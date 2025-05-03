# File: skiplevel/teams/reflection_team.py

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage

from core.agent_helpers import create_agent, create_team_supervisor, agent_node
from models.types import AgentState
from agents.reflection_evaluator.agent import create_reflection_evaluator_agent
from agents.reflection_evaluator.tools.rubric_retriever import rubric_retriever
from agents.reflection_evaluator.tools.reflection_evaluator import reflection_evaluator

# Create the reflection evaluator agent
reflection_evaluator_agent = create_reflection_evaluator_agent(ChatOpenAI(model="gpt-4-turbo-preview"))

def run_reflection_agent(state: AgentState) -> AgentState:
    """
    Run the reflection evaluator agent and update the state.
    
    Args:
        state: The current state of the DAG
        
    Returns:
        AgentState: Updated state with evaluation results
    """
    print("\n🧠 Entered run_reflection_agent node")
    print(f"📝 Initial state: {state}")
    
    result = agent_node(state, reflection_evaluator_agent, "reflection_evaluator")
    
    # Get the evaluation text from the result
    evaluation_text = result.get("reflection_evaluator")
    
    if evaluation_text:
        result["messages"].append(
            SystemMessage(content=f"✅ Reflection Evaluation Completed:\n{evaluation_text}")
        )
        result["next"] = "FINISH"  # 🛑 Tell supervisor that evaluation is done
    
    print(f"📝 Result from agent_node: {result}")

    # Create a new state with the evaluation properly set
    new_state = AgentState(
        messages=result.get("messages", []),
        reflection_text=result.get("reflection_text", ""),
        evaluation_result=evaluation_text,  # Set evaluation_result directly
        growth_advice=result.get("growth_advice"),
        next=result.get("next"),
        reflection_evaluator=evaluation_text  # Also keep it in reflection_evaluator for backward compatibility
    )
    
    print(f"📝 Updated state: {new_state}")
    return new_state

def create_reflection_team(llm: ChatOpenAI) -> StateGraph:
    """
    Creates a LangGraph team for evaluating engineer reflections.
    
    The team consists of:
    - A supervisor agent that coordinates the evaluation process
    - A reflection evaluator agent that analyzes the reflection against rubrics
    
    Args:
        llm: The language model to use for the agents
        
    Returns:
        StateGraph: The compiled team graph
    """
    # Create the supervisor agent
    supervisor = create_team_supervisor(
        llm=llm,
        system_prompt="""You are the Supervisor of the Reflection Team.

Your job is to review the engineer's self-reflection and coordinate the evaluation process by routing to the appropriate team member.

**Decision rules:**
- Always start by routing to "ReflectionEvaluator" to perform the reflection analysis.
- After "ReflectionEvaluator" completes, you must select "FINISH" and end the process. 
- Do not loop endlessly.
- Only use available choices exactly as listed: ["ReflectionEvaluator", "FINISH"].

Be decisive and minimize unnecessary steps.

After the ReflectionEvaluator completes its analysis, you should:
1. Review the evaluation result
2. If the evaluation looks complete and comprehensive, choose "FINISH"
3. If the evaluation seems incomplete or needs more analysis, choose "ReflectionEvaluator"

Remember: The goal is to get a complete evaluation in as few steps as possible.""",
        members=["ReflectionEvaluator"]
    )
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor)
    workflow.add_node("reflection_evaluator", run_reflection_agent)  # Use the new function
    
    # Set entry point
    workflow.set_entry_point("supervisor")
    
    # Add conditional edges
    # Add conditional edges based on the supervisor's decision
    # - If supervisor decides "ReflectionEvaluator", route to reflection_evaluator node
    # - If supervisor decides "FINISH", end the workflow
    # The decision is extracted from the state's "next" field which is set by the supervisor
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state.get("next"),
        {
            "ReflectionEvaluator": "reflection_evaluator",
            "FINISH": END
        }
    )
    
    # Add edge from reflection evaluator back to supervisor
    workflow.add_edge("reflection_evaluator", "supervisor")
    
    # Compile the graph
    return workflow.compile()

# Create the team graph
reflection_team_graph = create_reflection_team(ChatOpenAI(model="gpt-4-turbo-preview"))