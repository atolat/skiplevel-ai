"""
Substack API module for discovering and extracting content from Substack newsletters.

This module provides functions for interacting with Substack using their unofficial API,
allowing for discovery and extraction of content from their platform.
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
import re

logger = logging.getLogger(__name__)

# Cache directory for Substack API results
SUBSTACK_CACHE_DIR = Path("./data/cache/substack")
SUBSTACK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
SUBSTACK_CACHE_FILE = SUBSTACK_CACHE_DIR / "substack_api_cache.json"

# Text output directory
SUBSTACK_TEXTS_DIR = Path("./data/texts/substack")
SUBSTACK_TEXTS_DIR.mkdir(parents=True, exist_ok=True)

# Load Substack API cache if exists
SUBSTACK_CACHE = {}
if SUBSTACK_CACHE_FILE.exists():
    try:
        with open(SUBSTACK_CACHE_FILE, 'r') as f:
            SUBSTACK_CACHE = json.load(f)
            logger.info(f"Loaded {len(SUBSTACK_CACHE)} Substack API cache entries")
    except Exception as e:
        logger.error(f"Error loading Substack API cache: {str(e)}")

def save_cache():
    """Save Substack API cache to file."""
    try:
        with open(SUBSTACK_CACHE_FILE, 'w') as f:
            json.dump(SUBSTACK_CACHE, f, indent=2)
        logger.info(f"Saved {len(SUBSTACK_CACHE)} Substack API cache entries")
    except Exception as e:
        logger.error(f"Error saving Substack API cache: {str(e)}")

class SubstackNewsletter:
    """Class representing a Substack newsletter."""
    
    def __init__(self, url_or_name: str):
        """
        Initialize a newsletter by URL or name.
        
        Args:
            url_or_name: URL or subdomain name of the newsletter
        """
        if "substack.com" in url_or_name:
            # Extract subdomain from URL
            self.subdomain = url_or_name.split("//")[-1].split(".")[0]
        else:
            self.subdomain = url_or_name
            
        self.base_url = f"https://{self.subdomain}.substack.com"
        self.api_url = f"{self.base_url}/api"
    
    def get_newsletter_info(self) -> Optional[Dict]:
        """
        Get basic information about the newsletter.
        
        Returns:
            Dictionary with newsletter information or None if retrieval failed
        """
        cache_key = f"newsletter_info_{self.subdomain}"
        if cache_key in SUBSTACK_CACHE:
            cache_time = SUBSTACK_CACHE[cache_key].get("timestamp", 0)
            if time.time() - cache_time < 7 * 24 * 60 * 60:  # 7 days in seconds
                logger.info(f"Using cached newsletter info for {self.subdomain}")
                return SUBSTACK_CACHE[cache_key].get("data")
        
        try:
            url = f"{self.api_url}/v1/publication"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache the result
                SUBSTACK_CACHE[cache_key] = {
                    "timestamp": time.time(),
                    "data": data
                }
                save_cache()
                
                return data
            else:
                logger.warning(f"Failed to get newsletter info for {self.subdomain}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting newsletter info for {self.subdomain}: {str(e)}")
            return None
    
    def get_posts(self, subdomain: str) -> List[Dict]:
        """Get posts from a Substack newsletter."""
        cache_key = f"substack_posts_{subdomain}"
        if cache_key in SUBSTACK_CACHE:
            logger.info(f"Using cached posts for {subdomain}")
            return SUBSTACK_CACHE[cache_key]

        url = f"https://{subdomain}.substack.com/api/v1/posts"
        try:
            response = requests.get(url)
            response.raise_for_status()
            posts = response.json()  # API returns a list directly
            
            # Extract relevant fields from each post
            processed_posts = []
            for post in posts:
                if not post.get("is_published"):
                    continue
                    
                processed_post = {
                    "id": post.get("id"),
                    "title": post.get("title"),
                    "subtitle": post.get("subtitle"),
                    "description": post.get("description"),
                    "body_html": post.get("body_html"),
                    "post_date": post.get("post_date"),
                    "url": post.get("canonical_url"),
                    "meta": {
                        "content_type": "blog_article",
                        "is_curated": True,
                        "source_quality": 9.5,  # High quality Plato and other curated Substack newsletters
                        "blog_name": f"Substack - {subdomain}",
                        "newsletter": subdomain,
                    }
                }
                processed_posts.append(processed_post)

            SUBSTACK_CACHE[cache_key] = processed_posts
            save_cache()  # Save to disk after updating cache
            logger.info(f"Retrieved {len(processed_posts)} posts from {subdomain}")
            return processed_posts

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching posts from {subdomain}: {str(e)}")
            return []
    
    def search_posts(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for posts in the newsletter.
        
        Args:
            query: Search query
            limit: Maximum number of posts to retrieve
            
        Returns:
            List of matching post dictionaries
        """
        cache_key = f"search_{self.subdomain}_{hashlib.md5(query.encode()).hexdigest()}"
        if cache_key in SUBSTACK_CACHE:
            cache_time = SUBSTACK_CACHE[cache_key].get("timestamp", 0)
            if time.time() - cache_time < 1 * 24 * 60 * 60:  # 1 day in seconds
                logger.info(f"Using cached search results for {self.subdomain}")
                return SUBSTACK_CACHE[cache_key].get("data", [])
        
        try:
            url = f"{self.api_url}/v1/search/posts?query={query}&limit={limit}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get("results", [])
                
                # Cache the result
                SUBSTACK_CACHE[cache_key] = {
                    "timestamp": time.time(),
                    "data": posts
                }
                save_cache()
                
                return posts
            else:
                logger.warning(f"Failed to search posts for {self.subdomain}: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error searching posts for {self.subdomain}: {str(e)}")
            return []

class SubstackPost:
    """Class representing a Substack post."""
    
    def __init__(self, url: str):
        """
        Initialize a post by URL.
        
        Args:
            url: URL of the post
        """
        self.url = url
        
        # Extract info from URL
        match = re.match(r'https://([^\.]+)\.substack\.com/p/([^/]+)', url)
        if match:
            self.subdomain = match.group(1)
            self.slug = match.group(2)
        else:
            logger.warning(f"Invalid Substack post URL: {url}")
            self.subdomain = None
            self.slug = None
            
        self.base_url = f"https://{self.subdomain}.substack.com" if self.subdomain else None
        self.api_url = f"{self.base_url}/api" if self.base_url else None
    
    def get_post_data(self) -> Optional[Dict]:
        """
        Get metadata for the post.
        
        Returns:
            Dictionary with post data or None if retrieval failed
        """
        if not self.subdomain or not self.slug:
            logger.warning("Cannot get post data: missing subdomain or slug")
            return None
        
        cache_key = f"post_data_{self.subdomain}_{self.slug}"
        if cache_key in SUBSTACK_CACHE:
            cache_time = SUBSTACK_CACHE[cache_key].get("timestamp", 0)
            if time.time() - cache_time < 7 * 24 * 60 * 60:  # 7 days in seconds
                logger.info(f"Using cached post data for {self.slug}")
                return SUBSTACK_CACHE[cache_key].get("data")
        
        try:
            url = f"{self.api_url}/v1/posts/{self.slug}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache the result
                SUBSTACK_CACHE[cache_key] = {
                    "timestamp": time.time(),
                    "data": data
                }
                save_cache()
                
                return data
            else:
                logger.warning(f"Failed to get post data for {self.slug}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting post data for {self.slug}: {str(e)}")
            return None
    
    def get_content(self) -> Optional[str]:
        """
        Get the HTML content of the post.
        
        Returns:
            HTML content of the post or None if retrieval failed
        """
        post_data = self.get_post_data()
        if not post_data:
            return None
        
        return post_data.get("body_html", "")
    
    def get_text(self) -> Optional[str]:
        """
        Get the text content of the post.
        
        Returns:
            Text content of the post or None if retrieval failed
        """
        html_content = self.get_content()
        if not html_content:
            return None
        
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
            return None

def discover_substack_articles(topics: List[str], limit_per_topic: int = 5) -> List[Dict]:
    """
    Discover articles from high-quality Substack newsletters.
    
    Args:
        topics: List of topics to search for
        limit_per_topic: Maximum number of articles per topic
        
    Returns:
        List of discovered article dictionaries
    """
    # High-quality engineering management newsletters on Substack
    newsletters = [
        "platocommunity",  # Plato Community - Engineering Leadership Insights
        "pragmaticengineer",  # The Pragmatic Engineer by Gergely Orosz
        "theengineeringmanager", # The Engineering Manager by James Stanier
        "softwareleadweekly", # Software Lead Weekly by Oren Ellenbogen
        "lethain", # Irrational Exuberance by Will Larson
        "randsinrepose", # Rands in Repose by Michael Lopp
        "leaddev", # LeadDev by various authors
        "engineeringladders", # Engineering Ladders by Sarah Drasner
        "staffeng", # StaffEng by Will Larson
        "managersclub", # Manager's Club by Vidal Graupera
        "techlead", # TechLead Journal by Pat Kua
    ]
    
    seen_urls = set()
    discovered_articles = []
    
    for subdomain in newsletters:
        try:
            newsletter = SubstackNewsletter(subdomain)
            posts = newsletter.get_posts(subdomain)  # Get posts from the newsletter
            
            for post in posts:
                url = post.get("url") or f"https://{subdomain}.substack.com/p/{post.get('slug')}"
                if url in seen_urls:
                    continue
                    
                seen_urls.add(url)
                
                # Extract text content
                text = extract_text_from_substack_url(url)
                if not text:
                    continue
                
                # Save text to file
                filename = f"{subdomain}_{post.get('id')}.txt"
                text_path = SUBSTACK_TEXTS_DIR / filename
                try:
                    with open(text_path, 'w') as f:
                        f.write(text)
                except Exception as e:
                    logger.error(f"Error saving text for {url}: {str(e)}")
                    continue
                
                article = {
                    "url": url,
                    "title": post.get("title", ""),
                    "description": post.get("subtitle", ""),
                    "authors": [post.get("author", {}).get("name", "Unknown")],
                    "publish_date": post.get("post_date"),
                    "meta": {
                        "content_type": "blog_article",
                        "is_curated": True,
                        "source_quality": 9.5,  # High quality Substack newsletters
                        "blog_name": f"Substack - {subdomain}",
                        "newsletter": subdomain,
                        "text_file": str(text_path)
                    }
                }
                discovered_articles.append(article)
                
                if len(discovered_articles) >= limit_per_topic * len(topics):
                    break
                    
        except Exception as e:
            logger.error(f"Error processing newsletter {subdomain}: {str(e)}")
            continue
            
    logger.info(f"Discovered {len(discovered_articles)} Substack articles")
    return discovered_articles

def extract_text_from_substack_url(url: str) -> Optional[str]:
    """
    Extract text content from a Substack post URL.
    
    Args:
        url: URL of the Substack post
        
    Returns:
        Text content of the post or None if extraction failed
    """
    try:
        post = SubstackPost(url)
        return post.get_text()
    except Exception as e:
        logger.error(f"Error extracting text from Substack URL {url}: {str(e)}")
        return None

def is_substack_url(url: str) -> bool:
    """
    Check if a URL is a Substack post URL.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is a Substack post URL, False otherwise
    """
    return bool(re.match(r'https://[^\.]+\.substack\.com/p/[^/]+', url)) 