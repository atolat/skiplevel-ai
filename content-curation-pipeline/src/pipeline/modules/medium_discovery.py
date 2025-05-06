"""
Medium content discovery module.

This module provides specialized functions for discovering and processing content from Medium
using the Medium API, with multiple discovery strategies and thorough processing.
"""

import os
import logging
import time
import json
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
from . import medium_api

logger = logging.getLogger(__name__)

# Cache directory for Medium discovery results
MEDIUM_DISCOVERY_CACHE_DIR = Path("./data/cache/medium_discovery")
MEDIUM_DISCOVERY_CACHE_DIR.mkdir(parents=True, exist_ok=True)
MEDIUM_DISCOVERY_CACHE_FILE = MEDIUM_DISCOVERY_CACHE_DIR / "medium_discovery_cache.json"

# Text output directory
MEDIUM_TEXTS_DIR = Path("./data/texts/medium")
MEDIUM_TEXTS_DIR.mkdir(parents=True, exist_ok=True)

# Load medium discovery cache if exists
MEDIUM_DISCOVERY_CACHE = {}
if MEDIUM_DISCOVERY_CACHE_FILE.exists():
    try:
        with open(MEDIUM_DISCOVERY_CACHE_FILE, 'r') as f:
            MEDIUM_DISCOVERY_CACHE = json.load(f)
            logger.info(f"Loaded {len(MEDIUM_DISCOVERY_CACHE)} Medium discovery cache entries")
    except Exception as e:
        logger.error(f"Error loading Medium discovery cache: {str(e)}")

def save_discovery_cache():
    """Save Medium discovery cache to file."""
    try:
        with open(MEDIUM_DISCOVERY_CACHE_FILE, 'w') as f:
            json.dump(MEDIUM_DISCOVERY_CACHE, f, indent=2)
        logger.info(f"Saved {len(MEDIUM_DISCOVERY_CACHE)} Medium discovery cache entries")
    except Exception as e:
        logger.error(f"Error saving Medium discovery cache: {str(e)}")

def save_text_to_file(text: str, file_path: str) -> Optional[str]:
    """
    Save text content to a file.
    
    Args:
        text: The text content to save
        file_path: The path where the file should be saved
    
    Returns:
        The file path if successful, None otherwise
    """
    try:
        if not text:
            logger.warning(f"No text content to save to {file_path}")
            return None
            
        # Create directory if it doesn't exist
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
        logger.info(f"Saved text content to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving text to {file_path}: {str(e)}")
        return None

def discover_medium_content(topics: List[str], discovery_strategies: Optional[List[str]] = None, 
                            max_articles_per_strategy: int = 10, 
                            use_cache: bool = True,
                            save_content: bool = True) -> List[Dict]:
    """
    Discover Medium content using multiple strategies.
    
    Args:
        topics: List of topics to search for
        discovery_strategies: List of strategies to use (default: all)
            Available strategies: "topfeeds", "recommended", "search", "authors", "publications"
        max_articles_per_strategy: Maximum number of articles to get per strategy
        use_cache: Whether to use the cache
        save_content: Whether to save content to text files
        
    Returns:
        List of discovered resources with content already extracted
    """
    logger.info(f"Starting Medium content discovery for topics: {topics}")
    
    if not medium_api.MEDIUM_API_KEY:
        logger.warning("MEDIUM_API_KEY not found in environment variables. Skipping Medium discovery.")
        return []
    
    # Create a cache key for this discovery run
    topics_str = "_".join(sorted(topics))
    strategies_str = "_".join(sorted(discovery_strategies or ["all"]))
    cache_key = f"discovery_{hashlib.md5((topics_str + strategies_str).encode()).hexdigest()}"
    
    # Check cache if enabled
    if use_cache and cache_key in MEDIUM_DISCOVERY_CACHE:
        cache_time = MEDIUM_DISCOVERY_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 1 * 24 * 60 * 60:  # 1 day in seconds
            logger.info(f"Using cached Medium discovery results for {topics}")
            return MEDIUM_DISCOVERY_CACHE[cache_key].get("data", [])
    
    # Initialize discovery strategies
    if not discovery_strategies:
        discovery_strategies = ["topfeeds", "recommended", "search", "authors", "publications"]
    
    discovered_articles = []
    seen_article_ids = set()
    
    # Strategy 1: Topfeeds for each topic
    if "topfeeds" in discovery_strategies:
        logger.info("Using 'topfeeds' discovery strategy")
        for topic in topics:
            for mode in ["hot", "top_month"]:
                article_ids = medium_api.get_topfeeds_articles(topic, mode, max_articles_per_strategy)
                discovered_articles.extend(
                    process_article_ids(article_ids, seen_article_ids, 
                                       f"topfeeds_{topic}_{mode}", save_content)
                )
    
    # Strategy 2: Recommended feed for each topic
    if "recommended" in discovery_strategies:
        logger.info("Using 'recommended' discovery strategy")
        for topic in topics:
            # Try first 2 pages
            for page in range(1, 3):
                article_ids = medium_api.get_recommended_feed_articles(
                    topic, page, max_articles_per_strategy // 2)
                discovered_articles.extend(
                    process_article_ids(article_ids, seen_article_ids, 
                                       f"recommended_{topic}_page{page}", save_content)
                )
    
    # Strategy 3: Search for each topic
    if "search" in discovery_strategies:
        logger.info("Using 'search' discovery strategy")
        for topic in topics:
            article_ids = medium_api.search_articles(topic, max_articles_per_strategy)
            discovered_articles.extend(
                process_article_ids(article_ids, seen_article_ids, 
                                   f"search_{topic}", save_content)
            )
    
    # Strategy 4: Articles from curated authors
    if "authors" in discovery_strategies:
        logger.info("Using 'authors' discovery strategy")
        # List of recommended users - we can add more as we find good ones
        recommended_users = [
            "3a8aa3e9806d",  # Will Larson (StaffEng author, Lethain.com)
            "c542a6af0a0c",  # First Round Review
            "3ec794c4361f",  # Charity Majors
            "2dee8a25a224",  # Kent C. Dodds
            "ef4d6a91b7f6",  # Martin Fowler
            "2ff2ce6a97bc",  # Sarah Drasner
            "84ffa7e1f8ac",  # Camille Fournier
        ]
        
        for user_id in recommended_users:
            # Get user info
            user_info = medium_api.get_user_info(user_id)
            if not user_info:
                continue
            
            username = user_info.get("username", "")
            
            # Get user articles
            article_ids = medium_api.get_user_articles(user_id, max_articles_per_strategy // 2)
            discovered_articles.extend(
                process_article_ids(article_ids, seen_article_ids, 
                                   f"author_{username}", save_content)
            )
    
    # Strategy 5: Articles from curated publications
    if "publications" in discovery_strategies:
        logger.info("Using 'publications' discovery strategy")
        # This requires a different approach since we don't have direct API access
        # We could implement it in the future when/if Medium API supports it
    
    # Cache the results if enabled
    if use_cache:
        MEDIUM_DISCOVERY_CACHE[cache_key] = {
            "timestamp": time.time(),
            "data": discovered_articles
        }
        save_discovery_cache()
    
    logger.info(f"Discovered {len(discovered_articles)} Medium articles")
    return discovered_articles


def process_article_ids(article_ids: List[str], seen_article_ids: set, 
                       source_tag: str, save_content: bool) -> List[Dict]:
    """
    Process a list of article IDs to get their details and content.
    
    Args:
        article_ids: List of article IDs to process
        seen_article_ids: Set of already processed article IDs
        source_tag: Tag to identify the source of these articles
        save_content: Whether to save content to text files
        
    Returns:
        List of processed article resources
    """
    results = []
    
    for article_id in article_ids:
        # Skip already processed articles
        if article_id in seen_article_ids:
            continue
        
        seen_article_ids.add(article_id)
        
        # Get article info
        article_info = medium_api.get_article_info(article_id)
        if not article_info:
            continue
        
        # Get article URL and validate it
        article_url = article_info.get("url", "")
        if not article_url or not medium_api.is_valid_article_url(article_url):
            continue
        
        # Get content
        article_content = medium_api.get_article_content(article_id)
        if not article_content:
            continue
        
        # Extract text from HTML content
        article_text = medium_api.extract_text_from_html(article_content)
        if not article_text:
            continue
        
        # Save text to file if enabled
        text_path = None
        if save_content:
            # Create a unique file name based on the article ID and title
            title_slug = article_info.get("title", "")[:30].lower().replace(" ", "_")
            title_slug = ''.join(c if c.isalnum() or c == '_' else '' for c in title_slug)
            file_name = f"medium_{title_slug}_{article_id[:10]}.txt"
            text_path = str(MEDIUM_TEXTS_DIR / file_name)
            
            try:
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(article_text)
                logger.info(f"Saved Medium article text to {text_path}")
            except Exception as e:
                logger.error(f"Error saving article text: {str(e)}")
                text_path = None
        
        # Handle the author field which can be either a string or a dictionary
        author_name = "Unknown"
        author_field = article_info.get("author", {})
        if isinstance(author_field, dict):
            author_name = author_field.get("name", "Unknown")
        elif isinstance(author_field, str):
            author_name = author_field
            
        # Create resource dictionary
        article_resource = {
            "title": article_info.get("title", "Untitled Medium Article"),
            "url": article_url,
            "source": f"blog_medium_{source_tag}",
            "description": article_info.get("subtitle", ""),
            "authors": [author_name],
            "publish_date": article_info.get("published_at"),
            "meta": {
                "content_type": "blog_article",
                "is_curated": True,
                "source_quality": 8,  # High quality source
                "blog_name": "Medium",
                "medium_api": True,
                "medium_source": source_tag,
                "medium_article_id": article_id,
                "claps": article_info.get("claps", 0),
                "reading_time": article_info.get("reading_time", 0)
            },
            "text": article_text,
            "html_content": article_content,
            "is_processed": True
        }
        
        # Add text path if available
        if text_path:
            article_resource["text_path"] = text_path
        
        results.append(article_resource)
        logger.info(f"Processed Medium article: {article_resource['title']}")
    
    return results


def run_medium_discovery(query: str, max_articles: int = 30) -> List[Dict]:
    """
    Run a complete Medium discovery process for a query.
    
    Args:
        query: The query to search for (will be expanded to multiple topics)
        max_articles: Maximum number of articles to retrieve in total
        
    Returns:
        List of discovered article resources
    """
    # Expand the query into multiple topics
    # This is a simple approach - for production, consider using NLP to extract key topics
    topics = [query.lower()]
    
    # Add variations of the query for broader coverage
    query_terms = query.lower().split()
    if len(query_terms) > 1:
        # Add individual terms if the query has multiple words
        for term in query_terms:
            if len(term) > 3 and term not in ["the", "and", "for", "with", "that"]:
                topics.append(term)
    
    # Add related topics for engineering/career queries
    if any(term in query.lower() for term in ["engineer", "developer", "career", "tech"]):
        topics.extend([
            "software-engineering",
            "engineering-management",
            "career-development",
            "leadership"
        ])
    
    # Remove duplicates and limit topics
    topics = list(set(topics))[:5]  # Limit to 5 topics to avoid too many API calls
    
    logger.info(f"Expanded query '{query}' into topics: {topics}")
    
    # Calculate articles per strategy based on max_articles
    articles_per_strategy = max(5, max_articles // (len(topics) * 3))
    
    # Run the discovery process
    return discover_medium_content(
        topics=topics,
        discovery_strategies=["topfeeds", "recommended", "search", "authors"],
        max_articles_per_strategy=articles_per_strategy,
        use_cache=True,
        save_content=True
    )


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test the module
    import sys
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "engineering career growth"
    
    print(f"Running Medium discovery for query: {query}")
    articles = run_medium_discovery(query)
    print(f"Discovered {len(articles)} articles")
    
    # Print some stats
    if articles:
        total_words = sum(len(article.get("text", "").split()) for article in articles)
        avg_words = total_words / len(articles)
        print(f"Total words: {total_words}")
        print(f"Average words per article: {avg_words:.1f}")
        
        # Print top 5 articles by claps
        print("\nTop articles by engagement:")
        for i, article in enumerate(sorted(articles, 
                                          key=lambda x: x.get("meta", {}).get("claps", 0), 
                                          reverse=True)[:5]):
            claps = article.get("meta", {}).get("claps", 0)
            print(f"{i+1}. {article['title']} - {claps} claps") 