"""Tool for selecting appropriate sources based on collection goals."""

from typing import Dict, List, Type, Annotated
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from ..constants import RUBRIC_SOURCES, LEVEL_MAPPINGS, DIMENSION_MAPPINGS

class SourceSelectorInput(BaseModel):
    """Input model for the SourceSelectorTool."""
    level: str = Field(..., description="Target level (e.g., IC4, IC5)")
    dimension: str = Field(..., description="Target dimension (e.g., Execution, Leadership)")

@tool("source_selector", args_schema=SourceSelectorInput)
def select_sources(level: str, dimension: str) -> Dict[str, Dict[str, str]]:
    """Selects appropriate sources based on level and dimension requirements.
    
    Args:
        level: Target level (e.g., IC4, IC5)
        dimension: Target dimension (e.g., Execution, Leadership)
        
    Returns:
        Dictionary mapping source names to their metadata (url, type, company)
    """
    selected_sources = {}
    
    # Normalize level and dimension
    level_aliases = LEVEL_MAPPINGS.get(level, [level])
    dimension_aliases = DIMENSION_MAPPINGS.get(dimension, [dimension])
    
    for source_name, source_info in RUBRIC_SOURCES.items():
        # Check if source has the required dimension
        if any(dim in source_info["dimensions"] for dim in dimension_aliases):
            selected_sources[source_name] = {
                "url": source_info["url"],
                "type": source_info["type"],
                "company": source_info["company"]
            }
    
    return selected_sources 