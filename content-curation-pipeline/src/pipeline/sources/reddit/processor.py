"""
Reddit content processor implementation.
"""

import logging
from pathlib import Path
from typing import Dict, Any
from bs4 import BeautifulSoup

from ...interfaces import ContentProcessor, ContentItem

logger = logging.getLogger(__name__)

class RedditProcessor(ContentProcessor):
    """Processor for Reddit content."""
    
    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.processed_count = 0
        self.error_count = 0
        self.total_words = 0
        self.total_score = 0
        self.total_comments = 0
        self.subreddits = set()
    
    def process(self, content: ContentItem) -> bool:
        """Process a Reddit content item."""
        try:
            submission_data = content.raw_data
            if not submission_data:
                logger.warning(f"No data found for {content.url}")
                self.error_count += 1
                return False
            
            # Content should already be saved by the source
            # This processor mainly updates statistics
            
            # Update stats
            self.processed_count += 1
            self.total_words += content.metadata.additional_meta.get("word_count", 0)
            self.total_score += content.metadata.additional_meta.get("score", 0)
            self.total_comments += content.metadata.additional_meta.get("num_comments", 0)
            self.subreddits.add(content.metadata.additional_meta.get("subreddit", "unknown"))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Reddit content {content.url}: {str(e)}")
            self.error_count += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about processed content."""
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "total_words": self.total_words,
            "average_words": self.total_words / self.processed_count if self.processed_count > 0 else 0,
            "total_score": self.total_score,
            "average_score": self.total_score / self.processed_count if self.processed_count > 0 else 0,
            "total_comments": self.total_comments,
            "average_comments": self.total_comments / self.processed_count if self.processed_count > 0 else 0,
            "unique_subreddits": len(self.subreddits),
            "subreddits": list(self.subreddits)
        } 