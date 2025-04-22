"""Ingestion agent graph for scraping, chunking, and embedding rubric data."""

from typing import Dict, Any, List, TypedDict, Annotated
from langchain.tools import Tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from ..toolbelt import ingestion_tools, get_tool

# Define the state type for the ingestion agent
class IngestionState(TypedDict):
    """State for the ingestion agent."""
    tool: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    error: str
    status: str

def create_ingestion_agent() -> StateGraph:
    """Create the ingestion agent graph."""
    # Create a new graph
    workflow = StateGraph(IngestionState)
    
    # Create a ToolNode that can use any of the ingestion tools
    tool_node = ToolNode(tools=ingestion_tools)
    
    # Add the tool node to the graph
    workflow.add_node("tool_node", tool_node)
    
    # Define the edges
    workflow.add_edge("tool_node", END)
    
    # Set the entry point
    workflow.set_entry_point("tool_node")
    
    # Compile the graph
    return workflow.compile()

def run_ingestion_agent(
    tool_name: str,
    input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Run the ingestion agent with the specified tool and input."""
    # Create the agent
    agent = create_ingestion_agent()
    
    # Prepare the initial state
    initial_state = {
        "tool": tool_name,
        "input": input_data,
        "output": {},
        "error": "",
        "status": "running"
    }
    
    # Run the agent
    result = agent.invoke(initial_state)
    
    # Return the result
    return result 