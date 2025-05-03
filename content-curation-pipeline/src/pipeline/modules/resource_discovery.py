"""
Resource discovery module for finding high-quality engineering management books and papers.

This module provides functions to automatically discover engineering leadership resources
from various sources including academic repositories, GitHub, and engineering blogs.
"""

import os
import logging
import requests
import json
import time
from typing import Dict, List, Any, Optional, Union
from bs4 import BeautifulSoup
from pathlib import Path
import arxiv
from datetime import datetime, timedelta
import re
import hashlib

logger = logging.getLogger(__name__)

# Create directory for downloaded resources
RESOURCE_DIR = Path("./data/resources")
RESOURCE_DIR.mkdir(parents=True, exist_ok=True)

# Cache for discovered resources
RESOURCE_CACHE_FILE = Path("./data/cache/discovered_resources.json")
RESOURCE_CACHE = {}

# Load resource cache if exists
if RESOURCE_CACHE_FILE.exists():
    try:
        with open(RESOURCE_CACHE_FILE, 'r') as f:
            RESOURCE_CACHE = json.load(f)
            logger.info(f"Loaded {len(RESOURCE_CACHE)} resources from cache")
    except Exception as e:
        logger.error(f"Error loading resource cache: {str(e)}")

def save_resource_cache():
    """Save discovered resources to cache file."""
    RESOURCE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(RESOURCE_CACHE_FILE, 'w') as f:
            json.dump(RESOURCE_CACHE, f, indent=2)
        logger.info(f"Saved {len(RESOURCE_CACHE)} resources to cache")
    except Exception as e:
        logger.error(f"Error saving resource cache: {str(e)}")

def discover_arxiv_papers(query: str, max_results: int = 50) -> List[Dict]:
    """
    Discover papers from arXiv based on query.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        List of paper dictionaries
    """
    logger.info(f"Searching arXiv for: {query}")
    
    # Create a cache key for this query
    cache_key = f"arxiv_{hashlib.md5(query.encode()).hexdigest()}"
    
    # Check cache for recent results (< 7 days old)
    if cache_key in RESOURCE_CACHE:
        cache_time = RESOURCE_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 7 * 24 * 60 * 60:  # 7 days in seconds
            logger.info(f"Using cached arXiv results for {query}")
            return RESOURCE_CACHE[cache_key].get("results", [])
    
    try:
        # Perform arXiv search
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = []
        for paper in search.results():
            # Filter for computer science and engineering papers
            if any(cat in ['cs.SE', 'cs.CY', 'cs.HC', 'cs.AI'] for cat in paper.categories):
                paper_dict = {
                    "title": paper.title,
                    "url": paper.pdf_url,
                    "source": "arxiv",
                    "authors": [author.name for author in paper.authors],
                    "published_date": paper.published.isoformat() if paper.published else None,
                    "summary": paper.summary,
                    "categories": paper.categories,
                    "entry_id": paper.entry_id,
                    "meta": {
                        "content_type": "academic_paper",
                        "is_curated": True,
                        "source_quality": 8  # arXiv papers are generally high quality
                    }
                }
                results.append(paper_dict)
        
        # Cache the results
        RESOURCE_CACHE[cache_key] = {
            "timestamp": time.time(),
            "results": results
        }
        save_resource_cache()
        
        logger.info(f"Found {len(results)} relevant arXiv papers")
        return results
    
    except Exception as e:
        logger.error(f"Error searching arXiv: {str(e)}")
        # Return cached results if available, even if old
        if cache_key in RESOURCE_CACHE:
            return RESOURCE_CACHE[cache_key].get("results", [])
        return []

def discover_github_resources(query: str, min_stars: int = 100) -> List[Dict]:
    """
    Discover high-quality resources from GitHub repositories.
    
    Args:
        query: The search query
        min_stars: Minimum number of stars a repository should have
        
    Returns:
        List of resource dictionaries
    """
    logger.info(f"Searching GitHub for: {query}")
    
    # Create a cache key for this query
    cache_key = f"github_{hashlib.md5(query.encode()).hexdigest()}"
    
    # Check cache for recent results (< 7 days old)
    if cache_key in RESOURCE_CACHE:
        cache_time = RESOURCE_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 7 * 24 * 60 * 60:  # 7 days in seconds
            logger.info(f"Using cached GitHub results for {query}")
            return RESOURCE_CACHE[cache_key].get("results", [])
    
    try:
        # GitHub search API requires authentication
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            logger.warning("GITHUB_TOKEN not found in environment variables. GitHub search will be rate-limited.")
            headers = {}
        else:
            headers = {"Authorization": f"token {github_token}"}
        
        # Perform GitHub search
        encoded_query = "+".join(query.split())
        url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for repo in data.get("items", []):
            # Filter by stars
            if repo.get("stargazers_count", 0) >= min_stars:
                # Get README content
                readme_url = f"https://api.github.com/repos/{repo['full_name']}/readme"
                readme_response = requests.get(readme_url, headers=headers)
                readme_content = ""
                
                if readme_response.status_code == 200:
                    readme_data = readme_response.json()
                    if readme_data.get("content"):
                        import base64
                        readme_content = base64.b64decode(readme_data["content"]).decode("utf-8")
                
                repo_dict = {
                    "title": repo["name"],
                    "url": repo["html_url"],
                    "source": "github",
                    "stars": repo["stargazers_count"],
                    "description": repo["description"],
                    "created_at": repo["created_at"],
                    "updated_at": repo["updated_at"],
                    "readme_content": readme_content[:5000] if readme_content else "",  # Limit content size
                    "meta": {
                        "content_type": "github_repository",
                        "is_curated": True,
                        "source_quality": min(9, 5 + (repo["stargazers_count"] // 1000))  # Quality based on stars
                    }
                }
                results.append(repo_dict)
        
        # Cache the results
        RESOURCE_CACHE[cache_key] = {
            "timestamp": time.time(),
            "results": results
        }
        save_resource_cache()
        
        logger.info(f"Found {len(results)} relevant GitHub repositories")
        return results
    
    except Exception as e:
        logger.error(f"Error searching GitHub: {str(e)}")
        # Return cached results if available, even if old
        if cache_key in RESOURCE_CACHE:
            return RESOURCE_CACHE[cache_key].get("results", [])
        return []

def discover_engineering_blog_articles() -> List[Dict]:
    """
    Discover articles from top engineering blogs focused on management and leadership.
    
    Returns:
        List of article dictionaries
    """
    logger.info("Discovering engineering blog articles")
    
    # List of high-quality engineering blogs with leadership content
    blogs = [
        {
            "name": "Spotify Engineering",
            "url": "https://engineering.atspotify.com/category/engineering-culture/",
            "selector": "article.post"
        },
        {
            "name": "Netflix Tech Blog",
            "url": "https://netflixtechblog.com/tagged/engineering-management",
            "selector": "div.postArticle"
        },
        {
            "name": "Slack Engineering",
            "url": "https://slack.engineering/",
            "selector": "article.post"
        },
        {
            "name": "Dropbox Tech Blog",
            "url": "https://dropbox.tech/",
            "selector": "a.post-block"
        }
    ]
    
    # Create a cache key
    cache_key = "engineering_blogs"
    
    # Check cache for recent results (< 3 days old)
    if cache_key in RESOURCE_CACHE:
        cache_time = RESOURCE_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 3 * 24 * 60 * 60:  # 3 days in seconds
            logger.info("Using cached engineering blog results")
            return RESOURCE_CACHE[cache_key].get("results", [])
    
    results = []
    for blog in blogs:
        try:
            logger.info(f"Fetching articles from {blog['name']}")
            
            response = requests.get(blog["url"], headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.select(blog["selector"])
            
            for article in articles[:5]:  # Limit to 5 most recent articles per blog
                # Extract article details based on blog structure
                if blog["name"] == "Spotify Engineering":
                    title_elem = article.select_one("h2.entry-title")
                    link_elem = title_elem.select_one("a") if title_elem else None
                    
                    if link_elem and title_elem:
                        article_dict = {
                            "title": title_elem.text.strip(),
                            "url": link_elem["href"],
                            "source": f"blog_{blog['name'].lower().replace(' ', '_')}",
                            "meta": {
                                "content_type": "blog_article",
                                "is_curated": True,
                                "source_quality": 8  # Engineering blogs from top companies
                            }
                        }
                        results.append(article_dict)
                
                # Add similar extraction for other blogs
                # (This would be expanded for each blog's unique structure)
        
        except Exception as e:
            logger.error(f"Error fetching articles from {blog['name']}: {str(e)}")
    
    # Cache the results
    RESOURCE_CACHE[cache_key] = {
        "timestamp": time.time(),
        "results": results
    }
    save_resource_cache()
    
    logger.info(f"Found {len(results)} engineering blog articles")
    return results

def discover_resources(query: str) -> List[Dict]:
    """
    Main function to discover high-quality engineering management resources.
    
    Args:
        query: The search query
        
    Returns:
        List of resource dictionaries
    """
    logger.info(f"Starting resource discovery for query: {query}")
    
    # Prepare search queries targeted to engineering management
    academic_query = f"{query} management leadership engineering"
    github_query = f"{query} engineering management handbook guide"
    
    # Discover resources from different sources
    arxiv_papers = discover_arxiv_papers(academic_query, max_results=20)
    github_resources = discover_github_resources(github_query, min_stars=50)
    blog_articles = discover_engineering_blog_articles()
    
    # Combine all resources
    all_resources = arxiv_papers + github_resources + blog_articles
    
    # Format resources for pipeline consumption
    formatted_resources = []
    for resource in all_resources:
        # Already formatted properly by the discovery functions
        formatted_resources.append(resource)
    
    logger.info(f"Discovered {len(formatted_resources)} total resources")
    return formatted_resources 