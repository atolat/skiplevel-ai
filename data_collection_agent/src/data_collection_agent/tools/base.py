"""Base tool class for the agentic pipeline."""

from typing import Any, Dict, List, Optional, Type, ClassVar
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun

class ToolInput(BaseModel):
    """Base input model for tools."""
    pass

class ToolOutput(BaseModel):
    """Base output model for tools."""
    pass

class BasePipelineTool(BaseTool):
    """Base class for all pipeline tools."""
    
    name: ClassVar[str]
    description: ClassVar[str]
    input_model: ClassVar[Type[ToolInput]] = ToolInput
    output_model: ClassVar[Type[ToolOutput]] = ToolOutput
    
    def _run(
        self,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Run the tool with the given input."""
        raise NotImplementedError
    
    async def _arun(
        self,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Run the tool asynchronously."""
        raise NotImplementedError
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """Validate the input data."""
        self.input_model(**input_data)
    
    def _validate_output(self, output_data: Dict[str, Any]) -> None:
        """Validate the output data."""
        self.output_model(**output_data) 