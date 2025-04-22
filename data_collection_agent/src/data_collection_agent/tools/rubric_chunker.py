"""Tool for chunking rubric content into meaningful segments."""

from typing import Dict, List, Any, Optional
from pydantic import Field
from .base import BasePipelineTool, ToolInput, ToolOutput
from langchain.text_splitter import RecursiveCharacterTextSplitter

class RubricChunkerInput(ToolInput):
    """Input model for rubric chunker."""
    content: List[Dict[str, Any]] = Field(..., description="List of content to chunk")
    chunk_size: int = Field(default=1000, description="Size of each chunk")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")

class RubricChunkerOutput(ToolOutput):
    """Output model for rubric chunker."""
    chunks: List[Dict[str, Any]] = Field(..., description="List of processed chunks")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the chunking process")

class RubricChunkerTool(BasePipelineTool):
    """Tool for chunking rubric content into meaningful segments."""
    
    name = "rubric_chunker"
    description = "Processes fetched content into meaningful chunks for vectorization"
    input_model = RubricChunkerInput
    output_model = RubricChunkerOutput
    
    def _run(
        self,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process the fetched content into chunks."""
        self._validate_input(kwargs)
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=kwargs.get("chunk_size", 1000),
            chunk_overlap=kwargs.get("chunk_overlap", 200),
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = []
        total_chunks = 0
        
        for item in kwargs["content"]:
            # Split the content into chunks
            content_chunks = text_splitter.split_text(item["content"])
            
            # Create chunk entries with metadata
            for i, chunk in enumerate(content_chunks):
                chunk_entry = {
                    "chunk_id": f"{item['source_id']}_{i}",
                    "content": chunk,
                    "source_id": item["source_id"],
                    "company": item["company"],
                    "url": item["url"],
                    "chunk_index": i,
                    "total_chunks": len(content_chunks)
                }
                chunks.append(chunk_entry)
                total_chunks += 1
        
        output = {
            "chunks": chunks,
            "metadata": {
                "total_chunks": total_chunks,
                "chunk_size": kwargs.get("chunk_size", 1000),
                "chunk_overlap": kwargs.get("chunk_overlap", 200)
            }
        }
        
        self._validate_output(output)
        return output
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """Validate the input data."""
        if "content" not in input_data:
            raise ValueError("content is required")
        if not isinstance(input_data["content"], list):
            raise ValueError("content must be a list")
        
        # Validate chunk parameters if provided
        if "chunk_size" in input_data and not isinstance(input_data["chunk_size"], int):
            raise ValueError("chunk_size must be an integer")
        if "chunk_overlap" in input_data and not isinstance(input_data["chunk_overlap"], int):
            raise ValueError("chunk_overlap must be an integer")
    
    def _validate_output(self, output_data: Dict[str, Any]) -> None:
        """Validate the output data."""
        if "chunks" not in output_data:
            raise ValueError("chunks is required in output")
        if "metadata" not in output_data:
            raise ValueError("metadata is required in output")
        if not isinstance(output_data["chunks"], list):
            raise ValueError("chunks must be a list")
        if not isinstance(output_data["metadata"], dict):
            raise ValueError("metadata must be a dictionary") 