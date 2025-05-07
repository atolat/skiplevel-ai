"""Content curation functions for fetching high-quality URLs."""
import os
import logging
from typing import List, Dict
from tavily import TavilyClient
import praw
import re
from . import medium_api

logger = logging.getLogger(__name__)


def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid for processing.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is valid, False otherwise
    """
    # Skip URLs that are empty or None
    if not url:
        return False
    
    # If it's a Medium URL, check if it's a valid article URL
    if "medium.com" in url:
        return medium_api.is_valid_article_url(url)
    
    # For non-Medium URLs, return True by default
    return True


def curate_urls(query: str) -> List[Dict]:
    """Use Tavily to fetch high-signal URLs."""
    try:
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            logger.error("TAVILY_API_KEY not found in environment variables")
            return []
            
        client = TavilyClient(api_key=tavily_api_key)
        
        search_results = client.search(
            query=query,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True,
            max_results=10,
        )
        
        urls = []
        for result in search_results.get("results", []):
            if result.get("url") and is_valid_url(result.get("url")):
                urls.append({
                    "url": result["url"],
                    "title": result.get("title", ""),
                    "source": "tavily_search",
                    "score": result.get("score", 0),
                })
            elif result.get("url") and "medium.com" in result.get("url"):
                logger.info(f"Filtered out invalid Medium URL from Tavily results: {result.get('url')}")
        
        return urls
    except Exception as e:
        logger.error(f"Error in Tavily search: {str(e)}")
        return []


def curate_urls_from_reddit(query: str, limit: int = 10) -> List[Dict]:
    """
    Get URLs from Reddit based on a search query.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
    
    Returns:
        List of URL dictionaries
    """
    try:
        # Check for the Reddit API keys
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "non_agentic_pipeline:v1.0.0 (by /u/your_username)")
        
        if not client_id or not client_secret:
            logger.warning("Reddit API keys missing. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env file")
            return []
            
        # Initialize the Reddit API client
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # Expanded list of relevant subreddits for engineering careers
        relevant_subreddits = [
            "engineering", 
            "cscareerquestions", 
            "ExperiencedDevs", 
            "AskEngineers",
            "softwareengineering",
            "programming",
            "engineeringmanagement",
            "datascience",
            "devops",
            "careeradvice",
            "leaddev"
        ]
        
        # Simplify the search query - use terms that are likely to be in career-related posts
        # Break down the query into parts and use OR between key terms
        query_parts = query.split()
        if len(query_parts) > 3:
            # If query is long, extract key terms
            key_terms = [term for term in query_parts if len(term) > 4 and term.lower() not in 
                         ("and", "the", "for", "that", "with", "this", "from")][:4]  # Take up to 4 significant terms
            specific_query = " OR ".join(key_terms)
        else:
            specific_query = query
            
        # Add career-related terms
        career_terms = "career OR growth OR framework OR evaluation OR promotion OR review OR feedback"
        full_query = f"({specific_query}) ({career_terms})"
        
        results = []
        logger.info(f"Searching Reddit for: {full_query}")
        
        for subreddit_name in relevant_subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                
                # Search within the subreddit, more posts per subreddit
                search_limit = max(5, limit // len(relevant_subreddits) + 2)  # At least 5 per subreddit
                
                # Search with more flexible parameters
                for submission in subreddit.search(full_query, sort="relevance", limit=search_limit):
                    # Accept more types of posts
                    if submission.num_comments > 0:  # Only require that the post has comments
                        # Get top comments
                        submission.comment_sort = "top"
                        submission.comment_limit = 10  # Get more comments
                        
                        # Expand comment forest to get top-level comments
                        submission.comments.replace_more(limit=2)
                        
                        # Extract top comments text
                        top_comments = []
                        for comment in submission.comments[:10]:  # Get more comments
                            # Lower the minimum length requirement
                            if comment.body and len(comment.body) > 50:
                                top_comments.append({
                                    "body": comment.body,
                                    "score": comment.score,
                                    "author": str(comment.author)
                                })
                        
                        # Include submissions even with fewer comments
                        if len(top_comments) > 0:
                            # Include submission data with top comments for better context
                            meta_data = {
                                "title": submission.title,
                                "score": submission.score,
                                "num_comments": submission.num_comments,
                                "created_utc": submission.created_utc,
                                "selftext": submission.selftext if hasattr(submission, "selftext") else "",
                                "top_comments": top_comments,
                                "is_reddit_post": True,  # Flag to identify Reddit content
                                "permalink": submission.permalink,  # Store permalink for direct access
                                "subreddit": subreddit_name  # Store subreddit name
                            }
                            
                            # Use proper permalink URL
                            full_url = f"https://www.reddit.com{submission.permalink}"
                            
                            # Check that the URL is valid before adding it to results
                            if is_valid_url(full_url):
                            results.append({
                                "url": full_url,
                                "title": submission.title,
                                "source": f"reddit_{subreddit_name}",
                                "meta": meta_data
                            })
                
                # Break if we have enough results
                if len(results) >= limit * 2:  # Get double the requested limit to allow for filtering
                    break
                    
            except Exception as subreddit_error:
                logger.warning(f"Error searching subreddit {subreddit_name}: {str(subreddit_error)}")
                continue
        
        # Filter for most relevant results if we have too many
        if len(results) > limit:
            # Sort by post score as a relevance indicator
            results.sort(key=lambda x: x.get("meta", {}).get("score", 0), reverse=True)
            results = results[:limit]
            
        logger.info(f"Found {len(results)} relevant Reddit posts")
        return results
        
    except Exception as e:
        logger.error(f"Error fetching from Reddit: {str(e)}")
        return [] 