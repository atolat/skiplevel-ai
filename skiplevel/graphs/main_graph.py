# File: skiplevel/graphs/main_graph.py

from langgraph.graph import StateGraph, END
from teams.reflection_team import reflection_team_graph
from core.agent_helpers import create_team_supervisor
from langchain_openai import ChatOpenAI
from models.types import AgentState
from langchain_core.messages import SystemMessage

# Create the supervisor
llm = ChatOpenAI(model="gpt-4-turbo-preview")
supervisor = create_team_supervisor(
    llm,
    system_prompt="""You are a team supervisor that coordinates the reflection evaluation process. Given the engineer's reflection and the evaluation results, decide the next step.

**Decision Rules:**
1. When you first receive a reflection, ALWAYS route to "ReflectionEvaluator"
2. After the ReflectionEvaluator completes its analysis, route to "FINISH"
3. Do not loop endlessly
4. Only use available choices exactly as listed: ["ReflectionEvaluator", "FINISH"]

Be decisive and minimize unnecessary steps.""",
    members=["ReflectionEvaluator"],
)

# ✨ Patch: Supervisor runner with evaluation injection
async def run_supervisor(state):
    # Always start with ReflectionEvaluator if no next step is set
    if not state.get("next"):
        state["next"] = "ReflectionEvaluator"
        return state

    evaluation_text = state.get("evaluation_result") or state.get("reflection_evaluator")

    if evaluation_text:
        # Inject evaluation into messages
        state["messages"].append(
            SystemMessage(content=f"✅ Reflection Evaluation Completed:\n{evaluation_text}")
        )
        print("✅ Injected evaluation into messages for supervisor")
        # After evaluation is complete, finish
        state["next"] = "FINISH"
    else:
        print("⚠️ No evaluation found to inject into supervisor messages")
        # If no evaluation yet, continue to ReflectionEvaluator
        state["next"] = "ReflectionEvaluator"

    return await supervisor.ainvoke(state)

# Build the full graph
graph = StateGraph(AgentState)

graph.add_node("supervisor", run_supervisor)
graph.add_node("reflection_evaluator", reflection_team_graph)

graph.set_entry_point("supervisor")

graph.add_conditional_edges(
    "supervisor",
    lambda x: x.get("next"),
    {
        "ReflectionEvaluator": "reflection_evaluator",
        "FINISH": END
    }
)

graph.add_edge("reflection_evaluator", "supervisor")

compiled_dag = graph.compile()