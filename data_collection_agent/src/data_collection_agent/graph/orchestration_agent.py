"""Orchestration agent graph for coordinating between ingestion and reflection agents."""

from typing import Dict, Any, List, TypedDict, Annotated
from langchain.tools import Tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from ..toolbelt import orchestration_tools, get_tool
from .ingestion_agent import run_ingestion_agent
from .reflection_agent import run_reflection_agent

# Define the state type for the orchestration agent
class OrchestrationState(TypedDict):
    """State for the orchestration agent."""
    tool: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    error: str
    status: str
    ingestion_results: List[Dict[str, Any]]
    reflection_results: List[Dict[str, Any]]
    message: Dict[str, Any]

def create_orchestration_agent() -> StateGraph:
    """Create the orchestration agent graph."""
    # Create a new graph
    workflow = StateGraph(OrchestrationState)
    
    # Create a ToolNode that can use any of the orchestration tools
    tool_node = ToolNode(tools=orchestration_tools)
    
    # Add the tool node to the graph
    workflow.add_node("tool_node", tool_node)
    
    # Define the edges
    workflow.add_edge("tool_node", END)
    
    # Set the entry point
    workflow.set_entry_point("tool_node")
    
    # Compile the graph
    return workflow.compile()

def run_orchestration_agent(
    tool_name: str,
    input_data: Dict[str, Any],
    ingestion_results: List[Dict[str, Any]] = None,
    reflection_results: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Run the orchestration agent with the specified tool and input."""
    # Create the agent
    agent = create_orchestration_agent()
    
    # Prepare the initial state
    initial_state = {
        "tool": tool_name,
        "input": input_data,
        "output": {},
        "error": "",
        "status": "running",
        "ingestion_results": ingestion_results or [],
        "reflection_results": reflection_results or [],
        "message": {
            "content": f"Running {tool_name} with input: {input_data}",
            "function_call": {
                "name": tool_name,
                "arguments": input_data
            }
        }
    }
    
    # Run the agent
    result = agent.invoke(initial_state)
    
    # Return the result
    return result

def orchestrate_data_collection(
    sources: List[str],
    evaluation_criteria: Dict[str, Any]
) -> Dict[str, Any]:
    """Orchestrate the data collection process."""
    # Step 1: Run ingestion agent for each source
    ingestion_results = []
    for source in sources:
        result = run_ingestion_agent(
            tool_name="content_fetcher",
            input_data={"source": source}
        )
        ingestion_results.append(result)
    
    # Step 2: Run reflection agent for each ingestion result
    reflection_results = []
    for result in ingestion_results:
        reflection = run_reflection_agent(
            tool_name="content_evaluator",
            input_data={
                "content": result["output"],
                "criteria": evaluation_criteria
            }
        )
        reflection_results.append(reflection)
    
    # Step 3: Run orchestration agent to coordinate and summarize
    final_result = run_orchestration_agent(
        tool_name="data_collector",
        input_data={
            "sources": sources,
            "criteria": evaluation_criteria
        },
        ingestion_results=ingestion_results,
        reflection_results=reflection_results
    )
    
    return final_result 