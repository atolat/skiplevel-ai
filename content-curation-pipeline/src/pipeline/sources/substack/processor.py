"""
Substack content processor implementation.
"""

import logging
from pathlib import Path
from typing import Dict, Any
from bs4 import BeautifulSoup

from ...interfaces import ContentProcessor, ContentItem

logger = logging.getLogger(__name__)

class SubstackProcessor(ContentProcessor):
    """Processor for Substack content."""
    
    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.processed_count = 0
        self.error_count = 0
        self.total_words = 0
        self.newsletters = set()
    
    def process(self, content: ContentItem) -> bool:
        """Process a Substack content item."""
        try:
            if not content.raw_data.get("body_html"):
                logger.warning(f"No HTML content found for {content.url}")
                self.error_count += 1
                return False
            
            # Parse HTML content
            soup = BeautifulSoup(content.raw_data["body_html"], "html.parser")
            
            # Extract text content
            text_content = soup.get_text(separator="\n\n")
            
            # Save to file
            try:
                with open(content.text_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
            except Exception as e:
                logger.error(f"Error saving text content: {str(e)}")
                self.error_count += 1
                return False
            
            # Update stats
            self.processed_count += 1
            self.total_words += len(text_content.split())
            self.newsletters.add(content.metadata.additional_meta.get("newsletter", "unknown"))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Substack content {content.url}: {str(e)}")
            self.error_count += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about processed content."""
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "total_words": self.total_words,
            "average_words": self.total_words / self.processed_count if self.processed_count > 0 else 0,
            "unique_newsletters": len(self.newsletters),
            "newsletters": list(self.newsletters)
        } 