"""Tool for chunking and annotating rubric content."""

from typing import List, Dict, Any, Type
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, PrivateAttr

class RubricChunkerInput(BaseModel):
    """Input model for the RubricChunkerTool."""
    content: str = Field(..., description="Raw content to be chunked and annotated")
    level: str = Field(..., description="Target level (e.g., IC4, IC5)")
    dimension: str = Field(..., description="Target dimension (e.g., Execution, Leadership)")
    company: str = Field(..., description="Company name")

class RubricChunkerTool(BaseTool):
    """Tool for chunking and annotating rubric content."""
    
    name: str = "rubric_chunker"
    description: str = "Extracts and annotates rubric chunks using an LLM"
    args_schema: Type[BaseModel] = RubricChunkerInput
    
    _llm: ChatOpenAI = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.0
        )

    def _run(self, content: str, level: str, dimension: str, company: str) -> List[Dict[str, Any]]:
        """Extract and annotate rubric chunks from content."""
        prompt = f"""
        Extract and annotate rubric fragments from the following content that are relevant to:
        - Level: {level}
        - Dimension: {dimension}
        - Company: {company}

        For each relevant fragment:
        1. Extract the exact text
        2. Annotate it with:
           - level: {level}
           - dimension: {dimension}
           - company: {company}
           - rubric_type: "career_level"

        Content:
        {content}

        Return the fragments as a list of dictionaries with the following structure:
        {{
            "text": "exact fragment text",
            "metadata": {{
                "level": "{level}",
                "dimension": "{dimension}",
                "company": "{company}",
                "rubric_type": "career_level"
            }}
        }}
        """

        response = self._llm.invoke(prompt)
        # TODO: Parse the response into the correct format
        # For now, return a simple structure
        return [{
            "text": content[:500],  # Example: first 500 chars
            "metadata": {
                "level": level,
                "dimension": dimension,
                "company": company,
                "rubric_type": "career_level"
            }
        }]

    async def _arun(self, content: str, level: str, dimension: str, company: str) -> List[Dict[str, Any]]:
        """Async implementation of rubric chunking."""
        return self._run(content, level, dimension, company) 