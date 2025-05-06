"""
Medium API module for interacting with the Medium platform.

This module provides functions to discover and retrieve content from Medium
using the unofficial Medium API.
"""

import os
import logging
import requests
import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)
    logger = logging.getLogger(__name__)
    logger.info(f"Loaded environment variables from {dotenv_path}")
else:
    logger = logging.getLogger(__name__)
    logger.warning("No .env file found")

# Medium API configuration
MEDIUM_API_KEY = os.environ.get("MEDIUM_API_KEY", "")
if MEDIUM_API_KEY:
    logger.info("MEDIUM_API_KEY found in environment variables")
else:
    logger.warning("MEDIUM_API_KEY not found in environment variables")
    
MEDIUM_API_HOST = "medium2.p.rapidapi.com"
MEDIUM_API_BASE_URL = "https://medium2.p.rapidapi.com"

# Cache directory for Medium API results
MEDIUM_CACHE_DIR = Path("./data/cache/medium")
MEDIUM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
MEDIUM_CACHE_FILE = MEDIUM_CACHE_DIR / "medium_api_cache.json"

# Load medium API cache if exists
MEDIUM_CACHE = {}
if MEDIUM_CACHE_FILE.exists():
    try:
        with open(MEDIUM_CACHE_FILE, 'r') as f:
            MEDIUM_CACHE = json.load(f)
            logger.info(f"Loaded {len(MEDIUM_CACHE)} Medium API cache entries")
    except Exception as e:
        logger.error(f"Error loading Medium API cache: {str(e)}")

def save_medium_cache():
    """Save Medium API cache to file."""
    try:
        with open(MEDIUM_CACHE_FILE, 'w') as f:
            json.dump(MEDIUM_CACHE, f, indent=2)
        logger.info(f"Saved {len(MEDIUM_CACHE)} Medium API cache entries")
    except Exception as e:
        logger.error(f"Error saving Medium API cache: {str(e)}")

def get_medium_api_headers():
    """Get headers for Medium API requests."""
    return {
        "X-RapidAPI-Key": MEDIUM_API_KEY,
        "X-RapidAPI-Host": MEDIUM_API_HOST
    }

def is_valid_article_url(url: str) -> bool:
    """
    Check if a URL is a valid Medium article URL.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is a valid Medium article URL, False for profile/publication URLs
    """
    # Filter out profile and publication links - they should have specific patterns
    if not url or "medium.com" not in url:
        return False
    
    # Parse the URL to analyze the path
    try:
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        # Direct profile URLs: medium.com/@username
        if len(path_parts) == 1 and path_parts[0].startswith('@'):
            return False
            
        # Publications: medium.com/publication-name with no further path
        if len(path_parts) == 1 and not path_parts[0].startswith('@'):
            return False
            
        # Publication tabs: medium.com/publication-name/tagged, medium.com/publication-name/archive
        if len(path_parts) == 2 and path_parts[1] in ['tagged', 'archive', 'latest', 'top']:
            return False
    except Exception:
        # If URL parsing fails, be conservative and say it's not valid
        return False
    
    # Skip URLs that are definitely not article URLs
    if any([
        "?source=topic_portal" in url,
        "/membership" in url,
        "/creators" in url,
        "/about" in url,
        "/contact" in url,
        "/privacy" in url,
        "/terms" in url,
        "/explore" in url,
        "/tags" in url,
        "/topics" in url,
        url.endswith("/"),
        url.endswith("/latest"),
        url.endswith("/top"),
        url.endswith("/archive"),
        "/tagged/" in url,
    ]):
        return False
    
    # Check for patterns that usually indicate an article URL
    has_article_indicators = any([
        "-" in url.split("/")[-1],  # Article slugs usually have hyphens
        len(url.split("/")[-1]) > 10,  # Article IDs are usually long
        "/p/" in url,  # Publication article pattern
    ])
    
    return has_article_indicators

def get_article_info(article_id: str) -> Optional[Dict]:
    """
    Get detailed information about a Medium article.
    
    Args:
        article_id: Medium article ID
        
    Returns:
        Dictionary with article information or None if retrieval failed
    """
    # Check cache first
    cache_key = f"article_info_{article_id}"
    if cache_key in MEDIUM_CACHE:
        cache_time = MEDIUM_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 7 * 24 * 60 * 60:  # 7 days in seconds
            logger.info(f"Using cached article info for {article_id}")
            return MEDIUM_CACHE[cache_key].get("data")
    
    if not MEDIUM_API_KEY:
        logger.warning("MEDIUM_API_KEY not found in environment variables.")
        return None
    
    try:
        headers = get_medium_api_headers()
        article_url = f"{MEDIUM_API_BASE_URL}/article/{article_id}"
        response = requests.get(article_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            article_info = response.json()
            
            # Cache the result
            MEDIUM_CACHE[cache_key] = {
                "timestamp": time.time(),
                "data": article_info
            }
            save_medium_cache()
            
            return article_info
        else:
            logger.warning(f"Failed to get article info for {article_id}: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error getting article info for {article_id}: {str(e)}")
        return None

def get_article_content(article_id: str) -> Optional[str]:
    """
    Get the content of a Medium article.
    
    Args:
        article_id: Medium article ID
        
    Returns:
        HTML content of the article or None if retrieval failed
    """
    # Check cache first
    cache_key = f"article_content_{article_id}"
    if cache_key in MEDIUM_CACHE:
        cache_time = MEDIUM_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 7 * 24 * 60 * 60:  # 7 days in seconds
            logger.info(f"Using cached article content for {article_id}")
            return MEDIUM_CACHE[cache_key].get("data")
    
    if not MEDIUM_API_KEY:
        logger.warning("MEDIUM_API_KEY not found in environment variables.")
        return None
    
    try:
        headers = get_medium_api_headers()
        content_url = f"{MEDIUM_API_BASE_URL}/article/{article_id}/content"
        response = requests.get(content_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            content_data = response.json()
            content = content_data.get("content", "")
            
            # Cache the result
            MEDIUM_CACHE[cache_key] = {
                "timestamp": time.time(),
                "data": content
            }
            save_medium_cache()
            
            return content
        else:
            logger.warning(f"Failed to get article content for {article_id}: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error getting article content for {article_id}: {str(e)}")
        return None

def get_topfeeds_articles(topic: str, mode: str = "top_month", limit: int = 5) -> List[str]:
    """
    Get article IDs from Medium topfeeds for a specific topic and mode.
    
    Args:
        topic: Topic to search for
        mode: Mode to use (hot, new, top_month, etc.)
        limit: Maximum number of article IDs to return
        
    Returns:
        List of article IDs
    """
    # Check cache first
    cache_key = f"topfeeds_{topic}_{mode}"
    if cache_key in MEDIUM_CACHE:
        cache_time = MEDIUM_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 1 * 24 * 60 * 60:  # 1 day in seconds
            logger.info(f"Using cached topfeeds results for {topic}, {mode}")
            return MEDIUM_CACHE[cache_key].get("data", [])[:limit]
    
    if not MEDIUM_API_KEY:
        logger.warning("MEDIUM_API_KEY not found in environment variables.")
        return []
    
    try:
        headers = get_medium_api_headers()
        url = f"{MEDIUM_API_BASE_URL}/topfeeds/{topic}/{mode}"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Handle different response formats
            if isinstance(response_data, dict) and "topfeeds" in response_data:
                # New format with topfeeds array
                article_ids = response_data.get("topfeeds", [])
            elif isinstance(response_data, list):
                # Old format - direct array of IDs
                article_ids = response_data
            else:
                # Unexpected format
                logger.warning(f"Unexpected response format from topfeeds endpoint: {response_data}")
                article_ids = []
            
            # Cache the result
            MEDIUM_CACHE[cache_key] = {
                "timestamp": time.time(),
                "data": article_ids
            }
            save_medium_cache()
            
            return article_ids[:limit]
        else:
            logger.warning(f"Failed to get topfeeds for {topic}, {mode}: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error getting topfeeds for {topic}, {mode}: {str(e)}")
        return []

def get_recommended_feed_articles(topic: str, page: int = 1, limit: int = 5) -> List[str]:
    """
    Get article IDs from Medium recommended feed for a specific topic.
    
    Args:
        topic: Topic to search for
        page: Page number to retrieve
        limit: Maximum number of article IDs to return
        
    Returns:
        List of article IDs
    """
    # Check cache first
    cache_key = f"recommended_feed_{topic}_page{page}"
    if cache_key in MEDIUM_CACHE:
        cache_time = MEDIUM_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 1 * 24 * 60 * 60:  # 1 day in seconds
            logger.info(f"Using cached recommended feed results for {topic}, page {page}")
            return MEDIUM_CACHE[cache_key].get("data", [])[:limit]
    
    if not MEDIUM_API_KEY:
        logger.warning("MEDIUM_API_KEY not found in environment variables.")
        return []
    
    try:
        headers = get_medium_api_headers()
        url = f"{MEDIUM_API_BASE_URL}/recommended_feed/{topic}?page={page}"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            article_ids = data.get("associated_articles", [])
            
            # Cache the result
            MEDIUM_CACHE[cache_key] = {
                "timestamp": time.time(),
                "data": article_ids
            }
            save_medium_cache()
            
            return article_ids[:limit]
        else:
            logger.warning(f"Failed to get recommended feed for {topic}, page {page}: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error getting recommended feed for {topic}, page {page}: {str(e)}")
        return []

def search_articles(query: str, limit: int = 5) -> List[str]:
    """
    Search for articles on Medium.
    
    Args:
        query: Search query
        limit: Maximum number of article IDs to return
        
    Returns:
        List of article IDs
    """
    # Check cache first
    cache_key = f"search_{hashlib.md5(query.encode()).hexdigest()}"
    if cache_key in MEDIUM_CACHE:
        cache_time = MEDIUM_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 1 * 24 * 60 * 60:  # 1 day in seconds
            logger.info(f"Using cached search results for '{query}'")
            return MEDIUM_CACHE[cache_key].get("data", [])[:limit]
    
    if not MEDIUM_API_KEY:
        logger.warning("MEDIUM_API_KEY not found in environment variables.")
        return []
    
    try:
        headers = get_medium_api_headers()
        search_url = f"{MEDIUM_API_BASE_URL}/search/articles?query={query}"
        response = requests.get(search_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            article_ids = data.get("associated_articles", [])
            
            # Cache the result
            MEDIUM_CACHE[cache_key] = {
                "timestamp": time.time(),
                "data": article_ids
            }
            save_medium_cache()
            
            return article_ids[:limit]
        else:
            logger.warning(f"Failed to search for '{query}': {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error searching for '{query}': {str(e)}")
        return []

def get_user_articles(user_id: str, limit: int = 5) -> List[str]:
    """
    Get article IDs from a specific Medium user.
    
    Args:
        user_id: Medium user ID
        limit: Maximum number of article IDs to return
        
    Returns:
        List of article IDs
    """
    # Check cache first
    cache_key = f"user_articles_{user_id}"
    if cache_key in MEDIUM_CACHE:
        cache_time = MEDIUM_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 3 * 24 * 60 * 60:  # 3 days in seconds
            logger.info(f"Using cached user articles for {user_id}")
            return MEDIUM_CACHE[cache_key].get("data", [])[:limit]
    
    if not MEDIUM_API_KEY:
        logger.warning("MEDIUM_API_KEY not found in environment variables.")
        return []
    
    try:
        headers = get_medium_api_headers()
        url = f"{MEDIUM_API_BASE_URL}/user/{user_id}/articles"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            article_ids = data.get("associated_articles", [])
            
            # Cache the result
            MEDIUM_CACHE[cache_key] = {
                "timestamp": time.time(),
                "data": article_ids
            }
            save_medium_cache()
            
            return article_ids[:limit]
        else:
            logger.warning(f"Failed to get articles for user {user_id}: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error getting articles for user {user_id}: {str(e)}")
        return []

def get_user_info(user_id: str) -> Optional[Dict]:
    """
    Get information about a Medium user.
    
    Args:
        user_id: Medium user ID
        
    Returns:
        Dictionary with user information or None if retrieval failed
    """
    # Check cache first
    cache_key = f"user_info_{user_id}"
    if cache_key in MEDIUM_CACHE:
        cache_time = MEDIUM_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 7 * 24 * 60 * 60:  # 7 days in seconds
            logger.info(f"Using cached user info for {user_id}")
            return MEDIUM_CACHE[cache_key].get("data")
    
    if not MEDIUM_API_KEY:
        logger.warning("MEDIUM_API_KEY not found in environment variables.")
        return None
    
    try:
        headers = get_medium_api_headers()
        url = f"{MEDIUM_API_BASE_URL}/user/{user_id}"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            user_info = response.json()
            
            # Cache the result
            MEDIUM_CACHE[cache_key] = {
                "timestamp": time.time(),
                "data": user_info
            }
            save_medium_cache()
            
            return user_info
        else:
            logger.warning(f"Failed to get user info for {user_id}: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error getting user info for {user_id}: {str(e)}")
        return None

def extract_text_from_html(html_content: str) -> str:
    """
    Extract clean text from HTML content.
    
    Args:
        html_content: HTML content
        
    Returns:
        Clean text extracted from HTML
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text
        text = soup.get_text(separator="\n\n")
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n\n".join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from HTML: {str(e)}")
        return ""

def discover_medium_articles(topics: List[str], limit: int = 5) -> List[Dict]:
    """
    Discover Medium articles based on topics.
    
    Args:
        topics: List of topics to search for
        limit: Maximum number of articles per topic
        
    Returns:
        List of article dictionaries
    """
    logger.info(f"Discovering Medium articles for topics: {topics}")
    
    if not MEDIUM_API_KEY:
        logger.warning("MEDIUM_API_KEY not found in environment variables. Skipping Medium API discovery.")
        return []
    
    # Create a cache key for all topics
    topics_str = "_".join(sorted(topics))
    cache_key = f"medium_discovery_{hashlib.md5(topics_str.encode()).hexdigest()}"
    
    # Check cache for recent results (< 1 day old)
    if cache_key in MEDIUM_CACHE:
        cache_time = MEDIUM_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 1 * 24 * 60 * 60:  # 1 day in seconds
            logger.info(f"Using cached Medium discovery results for {topics}")
            return MEDIUM_CACHE[cache_key].get("data", [])
    
    results = []
    seen_article_ids = set()
    
    # List of recommended users - we can add more as we find good ones
    recommended_users = [
        "3a8aa3e9806d", # Will Larson (StaffEng author, Lethain.com)
        "14d5c41e0264", # Random user with lots of articles
        "c542a6af0a0c", # First Round Review
    ]
    
    # Strategy 1: Topfeeds for each topic
    for topic in topics:
        # Try different modes
        for mode in ["hot", "top_month"]:
            article_ids = get_topfeeds_articles(topic, mode, limit)
            
            # Process articles
            for article_id in article_ids:
                if article_id in seen_article_ids:
                    continue
                
                seen_article_ids.add(article_id)
                article_info = get_article_info(article_id)
                
                if not article_info:
                    continue
                
                # Create resource dict
                article_dict = {
                    "title": article_info.get("title", "Untitled Medium Article"),
                    "url": article_info.get("url", ""),
                    "source": "blog_medium_topfeeds",
                    "description": article_info.get("subtitle", ""),
                    "authors": [article_info.get("author", {}).get("name", "Unknown")],
                    "publish_date": article_info.get("published_at"),
                    "claps": article_info.get("claps", 0),
                    "reading_time": article_info.get("reading_time", 0),
                    "medium_article_id": article_id,
                    "meta": {
                        "content_type": "blog_article",
                        "is_curated": True,
                        "source_quality": 8,
                        "blog_name": "Medium",
                        "topic": topic,
                        "medium_api": True,
                        "medium_mode": mode
                    }
                }
                
                # Get content
                content = get_article_content(article_id)
                if content:
                    article_dict["api_content"] = content
                
                results.append(article_dict)
                logger.info(f"Added Medium article from topfeeds: {article_dict['title']}")
    
    # Strategy 2: Recommended feed for each topic
    for topic in topics:
        # Try first 2 pages
        for page in range(1, 3):
            article_ids = get_recommended_feed_articles(topic, page, limit)
            
            # Process articles
            for article_id in article_ids:
                if article_id in seen_article_ids:
                    continue
                
                seen_article_ids.add(article_id)
                article_info = get_article_info(article_id)
                
                if not article_info:
                    continue
                
                # Create resource dict
                article_dict = {
                    "title": article_info.get("title", "Untitled Medium Article"),
                    "url": article_info.get("url", ""),
                    "source": "blog_medium_recommended",
                    "description": article_info.get("subtitle", ""),
                    "authors": [article_info.get("author", {}).get("name", "Unknown")],
                    "publish_date": article_info.get("published_at"),
                    "claps": article_info.get("claps", 0),
                    "reading_time": article_info.get("reading_time", 0),
                    "medium_article_id": article_id,
                    "meta": {
                        "content_type": "blog_article",
                        "is_curated": True,
                        "source_quality": 8,
                        "blog_name": "Medium",
                        "topic": topic,
                        "medium_api": True,
                        "medium_feed": "recommended",
                        "page": page
                    }
                }
                
                # Get content
                content = get_article_content(article_id)
                if content:
                    article_dict["api_content"] = content
                
                results.append(article_dict)
                logger.info(f"Added Medium article from recommended feed: {article_dict['title']}")
    
    # Strategy 3: Search for each topic
    for topic in topics:
        article_ids = search_articles(topic, limit)
        
        # Process articles
        for article_id in article_ids:
            if article_id in seen_article_ids:
                continue
            
            seen_article_ids.add(article_id)
            article_info = get_article_info(article_id)
            
            if not article_info:
                continue
            
            # Create resource dict
            article_dict = {
                "title": article_info.get("title", "Untitled Medium Article"),
                "url": article_info.get("url", ""),
                "source": "blog_medium_search",
                "description": article_info.get("subtitle", ""),
                "authors": [article_info.get("author", {}).get("name", "Unknown")],
                "publish_date": article_info.get("published_at"),
                "claps": article_info.get("claps", 0),
                "reading_time": article_info.get("reading_time", 0),
                "medium_article_id": article_id,
                "meta": {
                    "content_type": "blog_article",
                    "is_curated": True,
                    "source_quality": 7,
                    "blog_name": "Medium",
                    "topic": topic,
                    "medium_api": True,
                    "search_term": topic
                }
            }
            
            # Get content
            content = get_article_content(article_id)
            if content:
                article_dict["api_content"] = content
            
            results.append(article_dict)
            logger.info(f"Added Medium article from search: {article_dict['title']}")
    
    # Strategy 4: Articles from recommended users
    for user_id in recommended_users:
        # Get user info
        user_info = get_user_info(user_id)
        if not user_info:
            continue
        
        user_name = user_info.get("name", "Unknown Author")
        username = user_info.get("username", user_id)
        
        # Get user articles
        article_ids = get_user_articles(user_id, 3)  # Limit to 3 articles per user
        
        # Process articles
        for article_id in article_ids:
            if article_id in seen_article_ids:
                continue
            
            seen_article_ids.add(article_id)
            article_info = get_article_info(article_id)
            
            if not article_info:
                continue
            
            # Create resource dict
            article_dict = {
                "title": article_info.get("title", "Untitled Medium Article"),
                "url": article_info.get("url", ""),
                "source": f"blog_medium_user_{username}",
                "description": article_info.get("subtitle", ""),
                "authors": [user_name],
                "publish_date": article_info.get("published_at"),
                "claps": article_info.get("claps", 0),
                "reading_time": article_info.get("reading_time", 0),
                "medium_article_id": article_id,
                "meta": {
                    "content_type": "blog_article",
                    "is_curated": True,
                    "source_quality": 9,
                    "blog_name": f"Medium - {user_name}",
                    "medium_api": True,
                    "medium_user": user_name,
                    "medium_username": username
                }
            }
            
            # Get content
            content = get_article_content(article_id)
            if content:
                article_dict["api_content"] = content
            
            results.append(article_dict)
            logger.info(f"Added Medium article from user {user_name}: {article_dict['title']}")
    
    # Filter out articles with invalid URLs (shouldn't happen with API, but just in case)
    valid_results = [article for article in results if is_valid_article_url(article.get("url", ""))]
    
    # Cache the results
    MEDIUM_CACHE[cache_key] = {
        "timestamp": time.time(),
        "data": valid_results
    }
    save_medium_cache()
    
    logger.info(f"Discovered {len(valid_results)} Medium articles")
    return valid_results 