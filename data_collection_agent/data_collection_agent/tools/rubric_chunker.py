"""Tool for chunking and annotating rubric content."""

from typing import List, Dict, Any, TypedDict
from langchain.tools import tool
from langchain_openai import ChatOpenAI
import os

class ChunkInput(TypedDict):
    """Input type for chunk_rubric tool."""
    content: str
    level: str
    dimension: str
    company: str

@tool
def chunk_rubric(content: str, level: str, dimension: str, company: str) -> List[Dict[str, Any]]:
    """Extract and annotate rubric chunks from content.
    
    Args:
        content: Raw content to be chunked and annotated
        level: Target level (e.g., IC4, IC5)
        dimension: Target dimension (e.g., Execution, Leadership)
        company: Company name
    
    Returns:
        List of dictionaries containing chunked and annotated rubric fragments
    """
    # Initialize LLM inside the function
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.0,
        api_key=os.getenv("OPENAI_API_KEY")
    )

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

    response = llm.invoke(prompt)
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