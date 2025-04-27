from typing import Optional
import os
from tavily import TavilyClient
from langchain_core.tools import tool

# Initialize Tavily client
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

@tool
def rubric_searcher(query: str) -> str:
    """
    Search for relevant rubrics and evaluation criteria using the Tavily API.
    
    Args:
        query: The search query string
        
    Returns:
        str: A concatenated string of the top 5 search results, separated by double newlines
    """
    try:
        # Perform the search
        search_results = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5
        )
        
        # Extract and join the content from results
        if not search_results or not search_results.get("results"):
            return "No relevant rubrics or evaluation criteria found."
            
        # Join the content fields with double newlines
        content_snippets = [result.get("content", "") for result in search_results["results"]]
        return "\n\n".join(content_snippets)
        
    except Exception as e:
        return f"Error searching for rubrics: {str(e)}" 