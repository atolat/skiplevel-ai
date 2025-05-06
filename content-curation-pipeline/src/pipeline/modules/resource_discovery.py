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
from . import medium_api
from . import medium_discovery

logger = logging.getLogger(__name__)

# Create directory for downloaded resources
RESOURCE_DIR = Path("./data/resources")
RESOURCE_DIR.mkdir(parents=True, exist_ok=True)

# Cache for discovered resources
RESOURCE_CACHE_FILE = Path("./data/cache/discovered_resources.json")
RESOURCE_CACHE = {}

# Medium API configuration
MEDIUM_API_KEY = os.environ.get("MEDIUM_API_KEY", "")
MEDIUM_API_HOST = "medium2.p.rapidapi.com"
MEDIUM_API_BASE_URL = "https://medium2.p.rapidapi.com"

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
            "url": "https://engineering.spotify.com/",
            "selector": "article.post",
            "title_selector": "h2.entry-title",
            "link_selector": "h2.entry-title a",
            "is_abs_url": True
        },
        {
            "name": "Netflix Tech Blog",
            "url": "https://netflixtechblog.com/",
            "selector": "div.postArticle",
            "title_selector": "h3.graf--title",
            "link_selector": "a.postArticle-content",
            "is_abs_url": True
        },
        {
            "name": "Slack Engineering",
            "url": "https://slack.engineering/",
            "selector": "article.post",
            "title_selector": "h2.post-title",
            "link_selector": "a.read-entire-post",
            "is_abs_url": True
        },
        {
            "name": "Dropbox Tech Blog",
            "url": "https://dropbox.tech/",
            "selector": "a.post-block",
            "title_selector": "h3",
            "link_selector": "a.post-block",
            "is_abs_url": True
        },
        {
            "name": "Stripe Engineering Blog",
            "url": "https://stripe.com/blog/engineering",
            "selector": "article.BlogIndex-item",
            "title_selector": "h2",
            "link_selector": "a.BlogIndex-link",
            "is_abs_url": False,
            "base_url": "https://stripe.com"
        },
        {
            "name": "Airbnb Engineering",
            "url": "https://medium.com/airbnb-engineering",
            "selector": "article",
            "title_selector": "h1",
            "link_selector": "a[href*='/airbnb-engineering/']",
            "is_abs_url": True
        },
        {
            "name": "Engineering Blog - Medium",
            "url": "https://medium.com/tag/engineering-management",
            "selector": "article",
            "title_selector": "h2",
            "link_selector": "a[href*='/']",
            "is_abs_url": False,
            "base_url": "https://medium.com"
        },
        {
            "name": "LeadDev",
            "url": "https://leaddev.com/leadership-skills",
            "selector": "div.views-row",
            "title_selector": "h3.article-title",
            "link_selector": "h3.article-title a",
            "is_abs_url": False,
            "base_url": "https://leaddev.com"
        },
        {
            "name": "Engineering Manager Resources",
            "url": "https://github.com/charlax/engineering-management",
            "selector": "#readme li",
            "title_selector": "a",
            "link_selector": "a",
            "is_abs_url": True
        },
        {
            "name": "Career Ladder Resources",
            "url": "https://career-ladders.dev/engineering/",
            "selector": "main a",
            "title_selector": None,  # Use link text as title
            "link_selector": "a",
            "is_abs_url": False,
            "base_url": "https://career-ladders.dev"
        },
        {
            "name": "Staff Engineer Resources",
            "url": "https://staffeng.com/guides/",
            "selector": "li",
            "title_selector": "a",
            "link_selector": "a",
            "is_abs_url": False,
            "base_url": "https://staffeng.com"
        },
        {
            "name": "Rands Leadership",
            "url": "https://randsinrepose.com/archives/category/management/",
            "selector": "article.post",
            "title_selector": "h2.entry-title",
            "link_selector": "h2.entry-title a",
            "is_abs_url": True
        },
        {
            "name": "Irrational Exuberance",
            "url": "https://lethain.com/",
            "selector": "div.post",
            "title_selector": "h1 a",
            "link_selector": "h1 a",
            "is_abs_url": True
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
                try:
                    # Extract title
                    if blog["title_selector"]:
                        title_elem = article.select_one(blog["title_selector"])
                        title = title_elem.text.strip() if title_elem else "Untitled"
                    else:
                        # Use link text as title
                        link_elem = article.select_one(blog["link_selector"])
                        title = link_elem.text.strip() if link_elem else "Untitled"
                    
                    # Extract URL
                    link_elem = article.select_one(blog["link_selector"])
                    if not link_elem:
                        continue
                        
                    url = link_elem.get("href", "")
                    if not url:
                        continue
                        
                    # Handle relative URLs
                    if not blog.get("is_abs_url", True) and not url.startswith(("http://", "https://")):
                        base_url = blog.get("base_url", blog["url"])
                        
                        # Special case for Medium to fix relative URLs
                        if "medium.com" in base_url and url.startswith("/@"):
                            url = f"{base_url}{url}"
                        # Regular handling for other relative URLs
                        else:
                            # Remove trailing slash from base_url if present
                            if base_url.endswith("/") and url.startswith("/"):
                                base_url = base_url[:-1]
                            # Add slash to base_url if needed
                            elif not base_url.endswith("/") and not url.startswith("/"):
                                base_url = base_url + "/"
                            url = base_url + url
                    
                    # Extract description if available
                    description = ""
                    if blog.get("description_selector"):
                        desc_elem = article.select_one(blog["description_selector"])
                        if desc_elem:
                            description = desc_elem.text.strip()
                    
                    article_dict = {
                        "title": title,
                        "url": url,
                        "source": f"blog_{blog['name'].lower().replace(' ', '_')}",
                        "description": description,
                        "meta": {
                            "content_type": "blog_article",
                            "is_curated": True,
                            "source_quality": 8,  # Engineering blogs from top companies
                            "blog_name": blog['name']
                        }
                    }
                    results.append(article_dict)
                    
                except Exception as e:
                    logger.warning(f"Error extracting article from {blog['name']}: {str(e)}")
                    continue
        
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

def discover_medium_articles(topics: List[str], limit: int = 5) -> List[Dict]:
    """
    Discover articles from Medium using ONLY the Unofficial Medium API.
    This function will handle both discovery and content extraction.
    
    Args:
        topics: List of topics to search for
        limit: Maximum number of articles per topic
        
    Returns:
        List of article dictionaries
    """
    logger.info(f"Discovering Medium articles for topics: {topics}")
    
    # Check if API key is available
    if not medium_api.MEDIUM_API_KEY:
        logger.warning("MEDIUM_API_KEY not found in environment variables. Skipping Medium API discovery.")
        return []
    
    # Use dedicated Medium API module for discovery
    articles = medium_api.discover_medium_articles(topics, limit)
    
    # Process the articles here directly to avoid going through web scraping later
    processed_articles = []
    for article in articles:
        try:
            # Only include articles with API content
            if "api_content" in article and article["api_content"]:
                # Extract text from HTML
                text = medium_api.extract_text_from_html(article["api_content"])
                
                # Only keep articles with substantial content
                if len(text) > 200:  # Minimum content length threshold
                    # Save text to separate file
                    text_path = TEXT_DIR / f"medium_{article['medium_article_id']}.txt"
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    
                    # Create fully processed article
                    processed_article = article.copy()
                    processed_article["text_path"] = str(text_path)
                    processed_article["is_processed"] = True
                    processed_article["extract_method"] = "medium_api_direct"
                    
                    # Remove api_content to save space but keep other metadata
                    if "api_content" in processed_article:
                        del processed_article["api_content"]
                    
                    processed_articles.append(processed_article)
                    logger.info(f"Processed Medium article: {article.get('title', 'Untitled')}")
                else:
                    logger.warning(f"Skipping Medium article with insufficient content: {article.get('title', 'Untitled')}")
            else:
                logger.warning(f"Skipping Medium article without API content: {article.get('title', 'Untitled')}")
                
        except Exception as e:
            logger.error(f"Error processing Medium article {article.get('title', 'Untitled')}: {str(e)}")
    
    logger.info(f"Discovered and processed {len(processed_articles)} Medium articles")
    return processed_articles

def discover_books(query: str) -> List[Dict]:
    """
    Discover relevant engineering and leadership books based on the query.
    
    Args:
        query: The search query
        
    Returns:
        List of book resource dictionaries
    """
    logger.info(f"Discovering books for: {query}")
    
    # Create a cache key for this query
    cache_key = f"books_{hashlib.md5(query.encode()).hexdigest()}"
    
    # Check cache for recent results (< 30 days old - books change less frequently)
    if cache_key in RESOURCE_CACHE:
        cache_time = RESOURCE_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 30 * 24 * 60 * 60:  # 30 days in seconds
            logger.info(f"Using cached book results for {query}")
            return RESOURCE_CACHE[cache_key].get("results", [])
    
    # For now, return a curated list of engineering leadership books
    # In the future, this could be expanded to use an API like Google Books or Open Library
    curated_books = [
        {
            "title": "The Manager's Path",
            "authors": ["Camille Fournier"],
            "url": "https://www.oreilly.com/library/view/the-managers-path/9781491973882/",
            "source": "curated_book",
            "description": "A guide for tech managers from individual contributor to CTO",
            "meta": {
                "content_type": "book",
                "is_curated": True,
                "source_quality": 9,
                "publication_year": 2017,
                "publisher": "O'Reilly Media"
            }
        },
        {
            "title": "Staff Engineer: Leadership Beyond the Management Track",
            "authors": ["Will Larson"],
            "url": "https://staffeng.com/book",
            "source": "curated_book",
            "description": "A guide to the Staff Engineer role in technology organizations",
            "meta": {
                "content_type": "book",
                "is_curated": True,
                "source_quality": 9,
                "publication_year": 2021,
                "publisher": "Self-published"
            }
        },
        {
            "title": "An Elegant Puzzle: Systems of Engineering Management",
            "authors": ["Will Larson"],
            "url": "https://lethain.com/elegant-puzzle/",
            "source": "curated_book",
            "description": "Systems thinking applied to engineering management",
            "meta": {
                "content_type": "book",
                "is_curated": True,
                "source_quality": 9,
                "publication_year": 2019,
                "publisher": "Stripe Press"
            }
        },
        {
            "title": "Accelerate: The Science of Lean Software and DevOps",
            "authors": ["Nicole Forsgren", "Jez Humble", "Gene Kim"],
            "url": "https://itrevolution.com/book/accelerate/",
            "source": "curated_book",
            "description": "Building and Scaling High Performing Technology Organizations",
            "meta": {
                "content_type": "book",
                "is_curated": True,
                "source_quality": 9,
                "publication_year": 2018,
                "publisher": "IT Revolution Press"
            }
        },
        {
            "title": "The Phoenix Project",
            "authors": ["Gene Kim", "Kevin Behr", "George Spafford"],
            "url": "https://itrevolution.com/book/the-phoenix-project/",
            "source": "curated_book",
            "description": "A Novel about IT, DevOps, and Helping Your Business Win",
            "meta": {
                "content_type": "book",
                "is_curated": True,
                "source_quality": 8,
                "publication_year": 2013,
                "publisher": "IT Revolution Press"
            }
        }
    ]
    
    # Select books relevant to the query
    # This is a simple keyword filtering approach - could be enhanced with NLP
    relevant_books = []
    query_terms = query.lower().split()
    
    for book in curated_books:
        # Check if any query term appears in the title or description
        if any(term in book["title"].lower() or 
               term in book.get("description", "").lower() 
               for term in query_terms):
            relevant_books.append(book)
        # If no direct match, include books that match broader engineering leadership terms
        elif ("engineering" in query.lower() or "leadership" in query.lower() or 
              "management" in query.lower() or "career" in query.lower()):
            relevant_books.append(book)
    
    # Cache the results
    RESOURCE_CACHE[cache_key] = {
        "timestamp": time.time(),
        "results": relevant_books
    }
    save_resource_cache()
    
    logger.info(f"Found {len(relevant_books)} relevant books")
    return relevant_books

def discover_resources(query: str) -> List[Dict]:
    """
    Discover relevant high-quality resources for a given query.
    
    This function orchestrates resource discovery from multiple sources
    including academic papers, books, repositories, and blogs.
    
    Args:
        query: The search query
        
    Returns:
        A list of discovered resources
    """
    logger.info(f"Discovering resources for: {query}")
    
    cache_key = f"discover_resources_{hashlib.md5(query.encode()).hexdigest()}"
    
    # Check cache for recent results
    if cache_key in RESOURCE_CACHE:
        cache_time = RESOURCE_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 24 * 60 * 60:  # 1 day in seconds
            logger.info(f"Using cached discover_resources results for {query}")
            return RESOURCE_CACHE[cache_key].get("data", [])
    
    # Resources will be a list of dictionaries with information about each resource
    discovered_resources = []
    
    # 1. Discover academic papers
    papers = discover_arxiv_papers(query, max_results=20)
    discovered_resources.extend(papers)
    logger.info(f"Added {len(papers)} academic papers")
    
    # 2. Discover GitHub repositories
    repos = discover_github_resources(query, min_stars=50)
    discovered_resources.extend(repos)
    logger.info(f"Added {len(repos)} GitHub repositories")
    
    # 3. Discover engineering blogs
    blogs = discover_engineering_blog_articles()
    discovered_resources.extend(blogs)
    logger.info(f"Added {len(blogs)} blog articles")
    
    # 4. Discover Medium articles using our specialized module
    try:
        medium_articles = medium_discovery.run_medium_discovery(query, max_articles=10)
        # These articles are already processed with content extracted, so we can add them directly
        discovered_resources.extend(medium_articles)
        logger.info(f"Added {len(medium_articles)} Medium articles")
    except Exception as e:
        logger.error(f"Error discovering Medium articles: {str(e)}")
    
    # 5. Discover books
    books = discover_books(query)
    discovered_resources.extend(books)
    logger.info(f"Added {len(books)} books")
    
    # Cache the results
    RESOURCE_CACHE[cache_key] = {
        "timestamp": time.time(),
        "data": discovered_resources
    }
    save_resource_cache()
    
    logger.info(f"Discovered {len(discovered_resources)} total resources")
    return discovered_resources 