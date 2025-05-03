"""
Content caching system to avoid reprocessing the same URLs.
"""
import os
import json
import logging
import hashlib
import time
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Default cache directory
CACHE_DIR = Path("./data/cache")
URL_CACHE_FILE = CACHE_DIR / "processed_urls.json"
CONTENT_CACHE_FILE = CACHE_DIR / "content_cache.json"

class ContentCache:
    """
    Cache manager for storing information about processed URLs and content.
    
    This allows the pipeline to:
    1. Skip URLs that have already been processed recently
    2. Reuse content extraction results
    3. Track evaluation scores and metadata
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the content cache.
        
        Args:
            cache_dir: Directory to store cache files (defaults to ./data/cache)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else CACHE_DIR
        self.url_cache_file = self.cache_dir / "processed_urls.json"
        self.content_cache_file = self.cache_dir / "content_cache.json"
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize caches
        self.urls: Dict[str, Dict[str, Any]] = self._load_cache(self.url_cache_file)
        self.content: Dict[str, Dict[str, Any]] = self._load_cache(self.content_cache_file)
        
        logger.info(f"Initialized content cache with {len(self.urls)} URLs and {len(self.content)} content entries")
    
    def _load_cache(self, cache_file: Path) -> Dict[str, Dict[str, Any]]:
        """Load cache from file or initialize an empty cache."""
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading cache from {cache_file}: {str(e)}")
                return {}
        return {}
    
    def _save_cache(self, cache_data: Dict[str, Dict[str, Any]], cache_file: Path) -> None:
        """Save cache to file."""
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving cache to {cache_file}: {str(e)}")
    
    def has_url(self, url: str, max_age_days: int = 7) -> bool:
        """
        Check if a URL has been processed recently.
        
        Args:
            url: The URL to check
            max_age_days: Consider cache entries older than this many days as expired
            
        Returns:
            True if the URL is in the cache and not expired
        """
        if url in self.urls:
            processed_time = self.urls[url].get("processed_time", 0)
            expiry_time = time.time() - (max_age_days * 24 * 60 * 60)  # Convert days to seconds
            return processed_time > expiry_time
        return False
    
    def add_url(self, url: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a URL to the cache.
        
        Args:
            url: The URL to add
            metadata: Optional metadata about the URL processing
        """
        self.urls[url] = {
            "processed_time": time.time(),
            "processed_date": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self._save_cache(self.urls, self.url_cache_file)
    
    def get_url_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a URL from the cache.
        
        Args:
            url: The URL to get metadata for
            
        Returns:
            Metadata dictionary or None if not found
        """
        if url in self.urls:
            return self.urls[url].get("metadata", {})
        return None
    
    def _get_content_hash(self, content: str) -> str:
        """Generate a hash for content to use as a cache key."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def has_content(self, content: str) -> bool:
        """Check if content has been processed before based on its hash."""
        content_hash = self._get_content_hash(content)
        return content_hash in self.content
    
    def add_content(self, content: str, processing_result: Dict[str, Any]) -> None:
        """
        Add processed content to the cache.
        
        Args:
            content: The raw content that was processed
            processing_result: The result of processing the content
        """
        content_hash = self._get_content_hash(content)
        self.content[content_hash] = {
            "processed_time": time.time(),
            "processed_date": datetime.now().isoformat(),
            "result": processing_result
        }
        self._save_cache(self.content, self.content_cache_file)
    
    def get_content_result(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Get processing result for content from the cache.
        
        Args:
            content: The raw content to get results for
            
        Returns:
            Processing result or None if not found
        """
        content_hash = self._get_content_hash(content)
        if content_hash in self.content:
            return self.content[content_hash].get("result")
        return None
    
    def get_all_urls(self) -> List[str]:
        """Get all URLs in the cache."""
        return list(self.urls.keys())
    
    def get_recent_urls(self, days: int = 7) -> List[str]:
        """Get URLs processed in the last N days."""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        return [
            url for url, data in self.urls.items()
            if data.get("processed_time", 0) > cutoff_time
        ]
    
    def clear_expired_entries(self, max_age_days: int = 30) -> None:
        """
        Remove entries older than max_age_days from both caches.
        
        Args:
            max_age_days: Remove entries older than this many days
        """
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        
        # Clear expired URLs
        expired_urls = [
            url for url, data in self.urls.items()
            if data.get("processed_time", 0) < cutoff_time
        ]
        for url in expired_urls:
            del self.urls[url]
        
        # Clear expired content
        expired_content = [
            content_hash for content_hash, data in self.content.items()
            if data.get("processed_time", 0) < cutoff_time
        ]
        for content_hash in expired_content:
            del self.content[content_hash]
        
        # Save updated caches
        self._save_cache(self.urls, self.url_cache_file)
        self._save_cache(self.content, self.content_cache_file)
        
        logger.info(f"Cleared {len(expired_urls)} expired URLs and {len(expired_content)} expired content entries")


# Global instance for easy access
content_cache = ContentCache() 