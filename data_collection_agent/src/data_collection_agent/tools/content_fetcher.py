"""Tool for fetching content from selected sources."""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from pydantic import Field
from .base import BasePipelineTool, ToolInput, ToolOutput
import re

class ContentFetcherInput(ToolInput):
    """Input model for content fetcher."""
    sources: List[Dict[str, Any]] = Field(..., description="List of sources to fetch from")

class ContentFetcherOutput(ToolOutput):
    """Output model for content fetcher."""
    fetched_content: List[Dict[str, Any]] = Field(..., description="List of fetched content")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors encountered")

class ContentFetcherTool(BasePipelineTool):
    """Tool for fetching content from selected sources."""
    
    name = "content_fetcher"
    description = "Fetches content from selected sources"
    input_model = ContentFetcherInput
    output_model = ContentFetcherOutput
    
    def _run(
        self,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Fetch content from the selected sources."""
        self._validate_input(kwargs)
        
        fetched_content = []
        errors = []
        
        for source in kwargs["sources"]:
            try:
                # Set headers to mimic a browser
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                # Fetch the content
                response = requests.get(source["url"], headers=headers, timeout=10)
                response.raise_for_status()
                
                # Parse the content based on source type
                if source["type"] == "html":
                    content = self._parse_html(response.text)
                else:
                    content = response.text
                
                # Skip if no meaningful content was extracted
                if not content.strip():
                    raise ValueError("No meaningful content could be extracted")
                
                fetched_content.append({
                    "source_id": source["source_id"],
                    "company": source["company"],
                    "content": content,
                    "url": source["url"]
                })
                
            except Exception as e:
                errors.append({
                    "source_id": source["source_id"],
                    "url": source["url"],
                    "error": str(e)
                })
        
        output = {
            "fetched_content": fetched_content,
            "errors": errors
        }
        
        self._validate_output(output)
        return output
    
    def _parse_html(self, html_content: str) -> str:
        """Parse HTML content to extract relevant text."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'meta', 'link', 'noscript', 'header', 'footer', 'nav', 'iframe', 'svg']):
            element.decompose()
            
        # Remove comments
        for comment in soup.find_all(text=lambda text: isinstance(text, str) and '<!--' in text):
            comment.extract()
        
        # Try to find the main content area
        content_areas = []
        
        # Look for common content containers
        for tag in ['main', 'article', 'div']:
            elements = soup.find_all(tag, class_=re.compile(r'(content|main|article|post|entry)', re.I))
            content_areas.extend(elements)
        
        # If we found content areas, use them
        if content_areas:
            text_parts = []
            for area in content_areas:
                # Get text from paragraphs and headers
                for element in area.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
                    text = element.get_text(strip=True)
                    if text:
                        text_parts.append(text)
            text = '\n\n'.join(text_parts)
        else:
            # Fallback to body content
            text_parts = []
            for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
                text = element.get_text(strip=True)
                if text:
                    text_parts.append(text)
            text = '\n\n'.join(text_parts)
        
        # Clean up the text
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove lines that are just special characters or very short
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if len(line) > 5 and not re.match(r'^[-_=*•]+$', line)]
        
        return '\n'.join(lines)
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """Validate the input data."""
        if "sources" not in input_data:
            raise ValueError("sources is required")
        if not isinstance(input_data["sources"], list):
            raise ValueError("sources must be a list")
    
    def _validate_output(self, output_data: Dict[str, Any]) -> None:
        """Validate the output data."""
        if "fetched_content" not in output_data:
            raise ValueError("fetched_content is required in output")
        if "errors" not in output_data:
            raise ValueError("errors is required in output") 