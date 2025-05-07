"""
YouTube content processor implementation.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from ...interfaces import ContentProcessor, ContentItem

logger = logging.getLogger(__name__)

class YouTubeProcessor(ContentProcessor):
    """Processor for YouTube video transcripts."""
    
    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.processed_count = 0
        self.error_count = 0
        self.total_words = 0
        self.total_duration = 0
        self.unique_channels = set()
    
    def process(self, item: ContentItem) -> bool:
        """Process a YouTube content item."""
        try:
            # Verify we have a transcript file
            if not item.text_path or not item.text_path.exists():
                logger.error(f"Missing transcript file for video {item.id}")
                self.error_count += 1
                return False
            
            # Read and clean transcript
            try:
                with open(item.text_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            except Exception as e:
                logger.error(f"Error reading transcript file: {str(e)}")
                self.error_count += 1
                return False
            
            # Clean and format transcript
            cleaned_text = self._clean_transcript(text)
            
            # Save cleaned transcript
            try:
                with open(item.text_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_text)
            except Exception as e:
                logger.error(f"Error saving cleaned transcript: {str(e)}")
                self.error_count += 1
                return False
            
            # Update statistics
            self.processed_count += 1
            self.total_words += len(cleaned_text.split())
            if item.metadata and item.metadata.additional_meta:
                channel = item.metadata.additional_meta.get("channel")
                if channel:
                    self.unique_channels.add(channel)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing YouTube item {item.id}: {str(e)}")
            self.error_count += 1
            return False
    
    def get_stats(self) -> Dict:
        """Get processing statistics."""
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "total_words": self.total_words,
            "avg_words_per_video": self.total_words / max(1, self.processed_count),
            "unique_channels": len(self.unique_channels),
            "channels": sorted(list(self.unique_channels))
        }
    
    def _clean_transcript(self, text: str) -> str:
        """Clean and format transcript text."""
        if not text:
            return ""
            
        # Split into lines and clean
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            # Remove leading/trailing whitespace
            line = line.strip()
            
            if not line:
                continue
            
            # Remove common transcript artifacts
            line = line.replace("[Music]", "")
            line = line.replace("[Applause]", "")
            line = line.replace("[Laughter]", "")
            
            # Add to cleaned lines if not empty
            if line:
                cleaned_lines.append(line)
        
        # Join cleaned lines with proper spacing
        return "\n".join(cleaned_lines) 