"""Central registry for all tools used in the SkipLevel project."""

from typing import Dict, List, Any, Optional, TypedDict, Callable
from langchain.tools import Tool
from .tools.source_selector import SourceSelectorTool
from .tools.content_fetcher import ContentFetcherTool
from .tools.rubric_chunker import RubricChunkerTool

# Define input/output types for tools
class ToolInput(TypedDict):
    """Base input type for tools."""
    pass

class ToolOutput(TypedDict):
    """Base output type for tools."""
    pass

# Source selector tool
def source_selector_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Select sources based on collection goals."""
    tool = SourceSelectorTool()
    return tool._run(**input_data)

# Content fetcher tool
def content_fetcher_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch content from selected sources."""
    tool = ContentFetcherTool()
    return tool._run(**input_data)

# Rubric chunker tool
def rubric_chunker_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process fetched content into meaningful chunks."""
    tool = RubricChunkerTool()
    return tool._run(**input_data)

# Define all tools
ingestion_tools = [
    Tool(
        name="source_selector",
        func=source_selector_tool,
        description="Selects appropriate data sources based on collection goals"
    ),
    Tool(
        name="content_fetcher",
        func=content_fetcher_tool,
        description="Fetches content from selected sources"
    ),
    Tool(
        name="rubric_chunker",
        func=rubric_chunker_tool,
        description="Processes fetched content into meaningful chunks for vectorization"
    ),
]

# Placeholder for evaluation tools (to be implemented)
evaluation_tools = [
    # Add evaluation tools here
]

# All tools combined
all_tools = ingestion_tools + evaluation_tools

# Tool registry for easy lookup
tool_registry: Dict[str, Tool] = {tool.name: tool for tool in all_tools}

def get_tool(tool_name: str) -> Optional[Tool]:
    """Get a tool by name."""
    return tool_registry.get(tool_name)

def get_tool_names() -> List[str]:
    """Get a list of all tool names."""
    return list(tool_registry.keys()) 