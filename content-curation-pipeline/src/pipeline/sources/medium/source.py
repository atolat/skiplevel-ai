"""
Medium content source implementation.
"""

import json
import logging
import re
import time
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests

from ...interfaces import ContentSource, ContentItem, ContentMetadata

logger = logging.getLogger(__name__)

class MediumSource(ContentSource):
    """Content source for Medium articles."""
    
    def __init__(self, cache_dir: Path, output_dir: Path):
        super().__init__(cache_dir, output_dir)
        self.cache_file = self.cache_dir / "medium_cache.json"
        self.cache = self._load_cache()
        
        # Get API key from environment
        self.api_key = os.getenv("MEDIUM_API_KEY")
        if not self.api_key:
            logger.warning("MEDIUM_API_KEY not found in environment variables")
        
        # RapidAPI configuration
        self.api_host = "medium2.p.rapidapi.com"
        self.api_base = "https://medium2.p.rapidapi.com"
        
        # Topics to search for engineering content
        self.topics = [
            "software-engineering",
            "engineering",
            "programming",
            "technology",
            "software-development"
        ]
        
        # High-quality engineering blogs on Medium
        self.curated_blogs = [
            "engineering.atspotify.com",  # Spotify Engineering
            "netflixtechblog.com",  # Netflix Technology Blog
            "medium.engineering",  # Medium Engineering
            "blog.discord.com",  # Discord Engineering
            "slack.engineering",  # Slack Engineering
            "medium.com/airbnb-engineering",  # Airbnb Engineering
            "medium.com/pinterest-engineering",  # Pinterest Engineering
            "medium.com/dropbox-engineering",  # Dropbox Engineering
            "medium.com/better-programming",  # Better Programming
            "medium.com/engineering-leadership",  # Engineering Leadership
        ]
    
    def _load_cache(self) -> Dict:
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading Medium cache: {str(e)}")
        return {}
    
    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving Medium cache: {str(e)}")
    
    def discover(self, query: str, limit: int = 10) -> List[ContentItem]:
        """Discover content from Medium."""
        if not self.api_key:
            logger.error("Cannot discover Medium content: MEDIUM_API_KEY not set")
            return []
        
        discovered_items = []
        seen_ids = set()
        
        # Search for articles
        try:
            url = f"{self.api_base}/search/articles"
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.api_host
            }
            params = {
                "query": query
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            article_ids = data.get("articles", [])
            
            # Get article info and content for each ID
            for article_id in article_ids[:limit]:
                if article_id in seen_ids:
                    continue
                
                seen_ids.add(article_id)
                
                # Get article info
                article_info = self._get_article_info(article_id)
                if not article_info:
                    continue
                
                # Get article content
                article_content = self._get_article_content(article_id)
                if not article_content:
                    continue
                
                # Add content to article info
                article_info["content"] = article_content
                
                # Convert to content item
                item = self._article_to_content_item(article_info)
                if item:
                    discovered_items.append(item)
                    
                if len(discovered_items) >= limit:
                    break
                    
        except Exception as e:
            logger.error(f"Error searching Medium articles: {str(e)}")
        
        return discovered_items
    
    def process_url(self, url: str) -> Optional[ContentItem]:
        """Process a single Medium URL."""
        if not self.is_source_url(url):
            return None
            
        try:
            article_data = self._get_article_info(url)
            if not article_data:
                return None
                
            return self._article_to_content_item(article_data)
            
        except Exception as e:
            logger.error(f"Error processing Medium URL {url}: {str(e)}")
            return None
    
    def is_source_url(self, url: str) -> bool:
        """Check if URL is from Medium."""
        return bool(re.search(r'medium\.com/|\.medium\.com', url))
    
    def _get_topic_articles(self, topic: str, mode: str = "hot", limit: int = 10) -> List[Dict]:
        """Get articles from a topic feed."""
        cache_key = f"topic_{topic}_{mode}"
        if cache_key in self.cache:
            cache_time = self.cache[cache_key].get("timestamp", 0)
            if time.time() - cache_time < 24 * 60 * 60:  # 24 hours
                return self.cache[cache_key].get("data", [])
        
        try:
            url = f"https://medium.com/topfeeds/{topic}/{mode}"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            # Extract article data from response
            articles = []
            # TODO: Parse the HTML response to extract article data
            # For now, return empty list as we need to implement HTML parsing
            
            # Cache the results
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "data": articles
            }
            self._save_cache()
            
            return articles[:limit]
            
        except Exception as e:
            logger.error(f"Error getting topic articles for {topic}: {str(e)}")
            return []
    
    def _get_article_info(self, article_id: str) -> Optional[Dict]:
        """Get information about a Medium article."""
        cache_key = f"article_{article_id}"
        if cache_key in self.cache:
            cache_time = self.cache[cache_key].get("timestamp", 0)
            if time.time() - cache_time < 7 * 24 * 60 * 60:  # 7 days
                return self.cache[cache_key].get("data")
        
        try:
            url = f"{self.api_base}/article/{article_id}"
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.api_host
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            article_data = response.json()
            
            # Cache the result
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "data": article_data
            }
            self._save_cache()
            
            return article_data
            
        except Exception as e:
            logger.error(f"Error getting article info for {article_id}: {str(e)}")
            return None
    
    def _get_article_content(self, article_id: str) -> Optional[str]:
        """Get article content from Medium."""
        cache_key = f"content_{article_id}"
        if cache_key in self.cache:
            cache_time = self.cache[cache_key].get("timestamp", 0)
            if time.time() - cache_time < 7 * 24 * 60 * 60:  # 7 days
                return self.cache[cache_key].get("data")
        
        try:
            url = f"{self.api_base}/article/{article_id}/content"
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.api_host
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            content = data.get("content", "")
            
            # Cache the result
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "data": content
            }
            self._save_cache()
            
            return content
            
        except Exception as e:
            logger.error(f"Error getting article content for {article_id}: {str(e)}")
            return None
    
    def _article_to_content_item(self, article: Dict) -> Optional[ContentItem]:
        """Convert a Medium article to a ContentItem."""
        try:
            article_id = article.get("id")
            if not article_id:
                return None
            
            # Get article content
            content = self._get_article_content(article_id)
            if not content:
                logger.warning(f"No content found for article {article_id}")
                return None
            
            # Create unique filename
            filename = f"medium_{article_id}.txt"
            text_path = self.output_dir / filename
            
            # Save article content
            try:
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error saving article content: {str(e)}")
                return None
            
            # Parse publish date
            try:
                date_str = article.get("published_at", "")
                if date_str:
                    # Try different date formats
                    for fmt in [
                        "%Y-%m-%d %H:%M:%S",       # Standard Medium format
                        "%Y-%m-%dT%H:%M:%S.%fZ",   # ISO format with microseconds
                        "%Y-%m-%dT%H:%M:%SZ",      # ISO format without microseconds
                        "%Y-%m-%d"                 # Simple date
                    ]:
                        try:
                            publish_date = datetime.strptime(date_str, fmt)
                            if fmt.endswith("Z"):
                                # Convert UTC to naive
                                publish_date = publish_date.replace(tzinfo=None)
                            else:
                                # Assume UTC and convert to naive
                                publish_date = publish_date.replace(tzinfo=timezone.utc).replace(tzinfo=None)
                            break
                        except ValueError:
                            continue
                else:
                    publish_date = None
            except Exception as e:
                logger.warning(f"Error parsing publish date '{date_str}': {str(e)}")
                publish_date = None
            
            # Create metadata
            metadata = ContentMetadata(
                source_type="medium",
                content_type="blog_article",
                source_quality=8.5,  # Medium articles generally have good quality
                is_curated=True,
                source_name=f"Medium - {article.get('publication_id', 'Unknown')}",
                additional_meta={
                    "publication": article.get("publication_id"),
                    "word_count": len(content.split()),  # Calculate word count from actual content
                    "claps": article.get("claps", 0),
                    "responses": article.get("responses_count", 0),
                    "reading_time": article.get("reading_time", 0),
                    "tags": article.get("tags", []),
                    "topics": article.get("topics", [])
                }
            )
            
            # Create content item
            return ContentItem(
                id=article_id,
                url=article.get("url", ""),
                title=article.get("title", ""),
                description=article.get("subtitle", ""),
                authors=[article.get("author", "Unknown")],
                publish_date=publish_date,
                metadata=metadata,
                text_path=text_path,
                raw_data=article
            )
            
        except Exception as e:
            logger.error(f"Error converting article to ContentItem: {str(e)}")
            return None

    def _search_articles(self, query: str, limit: int = 10) -> List[str]:
        """Search for Medium articles and return article IDs."""
        cache_key = f"search_{hashlib.md5(query.encode()).hexdigest()}"
        if cache_key in self.cache:
            cache_time = self.cache[cache_key].get("timestamp", 0)
            if time.time() - cache_time < 24 * 60 * 60:  # 24 hours
                return self.cache[cache_key].get("data", [])[:limit]
        
        try:
            url = f"{self.api_base}/search/articles"
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.api_host
            }
            params = {
                "query": query
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            article_ids = data.get("articles", [])
            
            # Cache the results
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "data": article_ids
            }
            self._save_cache()
            
            return article_ids[:limit]
            
        except Exception as e:
            logger.error(f"Error searching Medium articles: {str(e)}")
            return [] 