"""Tool for fetching content from various sources using Tavily."""

from typing import Dict, Any, TypedDict
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
import os
import time
from typing import Optional

class SourceInfo(TypedDict):
    """Type definition for source information."""
    url: str
    type: str
    company: str

def _validate_content(content: str, source_type: str) -> bool:
    """Validate content based on source type."""
    if not content:
        return False
    
    if source_type == "html":
        # Basic HTML validation
        return "<html" in content.lower() or "<body" in content.lower()
    elif source_type == "pdf":
        # Basic PDF validation (Tavily should handle this)
        return True
    else:
        # Unknown source type
        return False

@tool
def fetch_content(source_info: SourceInfo) -> str:
    """Fetch content from a source using Tavily.
    
    Args:
        source_info: Dictionary containing source information with keys:
            - url: The URL to fetch content from
            - type: The content type (html/pdf)
            - company: The company name (for context)
    
    Returns:
        str: The fetched content
    
    Raises:
        Exception: If content cannot be fetched or is invalid
    """
    # Initialize Tavily client inside the function
    tavily = TavilySearchResults(
        max_results=1,  # We only need the first result since we have a specific URL
        api_key=os.getenv("TAVILY_API_KEY")
    )
    
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            # Search for the specific URL
            results = tavily.invoke({"query": source_info["url"]})
            
            if not results:
                raise Exception(f"No content found for URL: {source_info['url']}")
            
            content = results[0]["content"]
            
            # Validate content
            if not _validate_content(content, source_info["type"]):
                raise Exception(f"Invalid content format for {source_info['type']} source")
            
            # Check content length
            if len(content) < 100:  # Minimum content length
                raise Exception("Content too short")
            
            return content
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"Failed to fetch content after {max_retries} attempts: {str(e)}")
            
            # Wait before retrying
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff 