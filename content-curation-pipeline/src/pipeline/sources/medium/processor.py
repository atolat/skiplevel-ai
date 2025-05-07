"""
Medium content processor implementation.
"""

import logging
from pathlib import Path
from typing import Dict, Any
from bs4 import BeautifulSoup

from ...interfaces import ContentProcessor, ContentItem

logger = logging.getLogger(__name__)

class MediumProcessor(ContentProcessor):
    """Processor for Medium content."""
    
    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.processed_count = 0
        self.error_count = 0
        self.total_words = 0
        self.total_claps = 0
        self.publications = set()
    
    def process(self, content: ContentItem) -> bool:
        """Process a Medium content item."""
        try:
            if not content.raw_data.get("content"):
                logger.warning(f"No content found for {content.url}")
                self.error_count += 1
                return False
            
            # Clean and format content
            text_content = content.raw_data["content"]
            if isinstance(text_content, str):
                # Clean HTML if present
                if "<" in text_content and ">" in text_content:
                    soup = BeautifulSoup(text_content, "html.parser")
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
            self.total_words += content.metadata.additional_meta.get("word_count", 0)
            self.total_claps += content.metadata.additional_meta.get("claps", 0)
            self.publications.add(content.metadata.additional_meta.get("publication", "unknown"))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Medium content {content.url}: {str(e)}")
            self.error_count += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about processed content."""
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "total_words": self.total_words,
            "average_words": self.total_words / self.processed_count if self.processed_count > 0 else 0,
            "total_claps": self.total_claps,
            "average_claps": self.total_claps / self.processed_count if self.processed_count > 0 else 0,
            "unique_publications": len(self.publications),
            "publications": list(self.publications)
        } 