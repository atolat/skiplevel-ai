"""Reflection evaluator agent graph for analyzing and evaluating content."""

from typing import Dict, Any, List, TypedDict, Annotated
from langchain.tools import Tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from ..toolbelt import evaluation_tools, get_tool

# Define the state type for the reflection agent
class ReflectionState(TypedDict):
    """State for the reflection agent."""
    tool: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    error: str
    status: str
    reflections: List[Dict[str, Any]]

def create_reflection_agent() -> StateGraph:
    """Create the reflection agent graph."""
    # Create a new graph
    workflow = StateGraph(ReflectionState)
    
    # Create a ToolNode that can use any of the evaluation tools
    tool_node = ToolNode(tools=evaluation_tools)
    
    # Add the tool node to the graph
    workflow.add_node("tool_node", tool_node)
    
    # Define the edges
    workflow.add_edge("tool_node", END)
    
    # Set the entry point
    workflow.set_entry_point("tool_node")
    
    # Compile the graph
    return workflow.compile()

def run_reflection_agent(
    tool_name: str,
    input_data: Dict[str, Any],
    reflections: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Run the reflection agent with the specified tool and input."""
    # Create the agent
    agent = create_reflection_agent()
    
    # Prepare the initial state
    initial_state = {
        "tool": tool_name,
        "input": input_data,
        "output": {},
        "error": "",
        "status": "running",
        "reflections": reflections or []
    }
    
    # Run the agent
    result = agent.invoke(initial_state)
    
    # Return the result
    return result 