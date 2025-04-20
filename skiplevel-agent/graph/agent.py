from typing import Dict, List, Tuple, Any, TypedDict
from langgraph.graph import Graph, StateGraph
from langgraph.prebuilt import ToolNode
from tools.rubric_retriever import RubricRetrieverTool
from tools.reflection_evaluator import ReflectionEvaluatorTool
from tools.growth_advisor import GrowthAdvisorTool
from langchain.callbacks.tracers import LangChainTracer
from langchain.callbacks.manager import CallbackManager
import os

def create_agent() -> Graph:
    """Create the LangGraph agent with the evaluation workflow."""
    
    # Set up LangSmith tracing
    tracer = LangChainTracer(
        project_name=os.getenv("LANGCHAIN_PROJECT", "skiplevel-agent")
    )
    callback_manager = CallbackManager([tracer])
    
    # Initialize tools with tracing
    rubric_tool = RubricRetrieverTool()
    evaluator_tool = ReflectionEvaluatorTool(callback_manager=callback_manager)
    advisor_tool = GrowthAdvisorTool(callback_manager=callback_manager)
    
    # Define the state type
    class AgentState(TypedDict):
        reflection: str
        rubrics: List[Dict]
        evaluation: Dict
        advice: Dict
    
    # Define the workflow functions
    def retrieve_rubrics(state: AgentState) -> AgentState:
        """Retrieve relevant rubric chunks."""
        result = rubric_tool._run(state["reflection"])
        return {"rubrics": result}
    
    def evaluate_reflection(state: AgentState) -> AgentState:
        """Evaluate reflection against rubrics."""
        result = evaluator_tool._run(state["reflection"], state["rubrics"])
        return {"evaluation": result}
    
    def get_growth_advice(state: AgentState) -> AgentState:
        """Generate growth advice based on evaluation."""
        result = advisor_tool._run(state["evaluation"])
        return {"advice": result}
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("retrieve_rubrics", retrieve_rubrics)
    workflow.add_node("evaluate_reflection", evaluate_reflection)
    workflow.add_node("get_growth_advice", get_growth_advice)
    
    # Add edges
    workflow.add_edge("retrieve_rubrics", "evaluate_reflection")
    workflow.add_edge("evaluate_reflection", "get_growth_advice")
    
    # Set entry point
    workflow.set_entry_point("retrieve_rubrics")
    
    # Compile
    return workflow.compile()

    # Visualization is moved to main.py since this function returns the workflow

