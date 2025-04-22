"""Tool for selecting appropriate data sources based on collection goals."""

from typing import Dict, List, Any, Optional
from pydantic import Field
from .base import BasePipelineTool, ToolInput, ToolOutput
from ..constants import SOURCES, LEVEL_MAPPINGS

class SourceSelectorInput(ToolInput):
    """Input model for source selector."""
    collection_goal: str = Field(..., description="The goal for data collection")
    target_levels: Optional[List[str]] = Field(None, description="Target career levels")
    target_dimensions: Optional[List[str]] = Field(None, description="Target dimensions")

class SourceSelectorOutput(ToolOutput):
    """Output model for source selector."""
    selected_sources: List[Dict[str, Any]] = Field(..., description="List of selected sources")
    reasoning: str = Field(..., description="Reasoning for source selection")

class SourceSelectorTool(BasePipelineTool):
    """Tool for selecting appropriate data sources."""
    
    name = "source_selector"
    description = "Selects appropriate data sources based on collection goals"
    input_model = SourceSelectorInput
    output_model = SourceSelectorOutput
    
    def _run(
        self,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Select sources based on the collection goal."""
        self._validate_input(kwargs)
        
        # Parse the collection goal to extract target levels and dimensions
        goal = kwargs["collection_goal"].lower()
        
        # Extract target levels from the goal
        target_levels = []
        for company, mappings in LEVEL_MAPPINGS.items():
            for company_level, standard_level in mappings.items():
                if company_level.lower() in goal:
                    target_levels.append(standard_level)
        
        # Extract target dimensions from the goal
        target_dimensions = []
        for dimension in ["execution", "technical", "leadership", "communication"]:
            if dimension in goal:
                target_dimensions.append(dimension)
        
        # Select sources that match the criteria
        selected_sources = []
        for source_id, source_config in SOURCES.items():
            # For now, we'll select all sources as they all contain relevant data
            # In a real implementation, we would use more sophisticated matching
            selected_sources.append({
                "source_id": source_id,
                "url": source_config["url"],
                "company": source_config["company"],
                "type": source_config["type"]
            })
        
        output = {
            "selected_sources": selected_sources,
            "reasoning": f"Selected {len(selected_sources)} sources based on target levels {target_levels} and dimensions {target_dimensions}"
        }
        
        self._validate_output(output)
        return output
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """Validate the input data."""
        if "collection_goal" not in input_data:
            raise ValueError("collection_goal is required")
    
    def _validate_output(self, output_data: Dict[str, Any]) -> None:
        """Validate the output data."""
        if "selected_sources" not in output_data:
            raise ValueError("selected_sources is required in output")
        if "reasoning" not in output_data:
            raise ValueError("reasoning is required in output") 