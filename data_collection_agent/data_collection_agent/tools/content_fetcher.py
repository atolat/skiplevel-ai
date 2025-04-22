"""Tool for fetching content from various sources."""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class ContentFetcherInput(BaseModel):
    """Input model for the ContentFetcherTool."""
    source_info: Dict[str, Any] = Field(..., description="Source information including URL and type")

class ContentFetcherTool(BaseTool):
    """Tool for fetching content from various sources."""
    
    name: str = "content_fetcher"
    description: str = "Fetches raw content from specified sources"
    args_schema: Type[BaseModel] = ContentFetcherInput

    def _run(self, source_info: Dict[str, Any]) -> str:
        """Fetch content from the specified source."""
        url = source_info["url"]
        source_type = source_info["type"]
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            if source_type == "html":
                soup = BeautifulSoup(response.text, 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                return soup.get_text(separator='\n', strip=True)
            elif source_type == "pdf":
                # TODO: Implement PDF parsing
                return response.content.decode('utf-8', errors='ignore')
            else:
                return response.text
                
        except requests.RequestException as e:
            return f"Error fetching content: {str(e)}"

    async def _arun(self, source_info: Dict[str, Any]) -> str:
        """Async implementation of content fetching."""
        return self._run(source_info) 