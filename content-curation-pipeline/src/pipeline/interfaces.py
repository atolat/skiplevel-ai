"""
Base interfaces for content curation pipeline.

This module defines the core interfaces that all content sources and processors must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

@dataclass
class ContentMetadata:
    """Metadata for a piece of content."""
    source_type: str  # e.g., "medium", "substack", "youtube"
    content_type: str  # e.g., "article", "video", "transcript"
    source_quality: float  # 0-10 rating of source quality
    is_curated: bool  # Whether this is from a curated source
    source_name: str  # Name of the source (e.g., blog name, channel name)
    additional_meta: Dict[str, Any]  # Any additional source-specific metadata

@dataclass
class ContentItem:
    """Represents a single piece of content."""
    id: str  # Unique identifier
    url: str  # Original URL
    title: str
    description: str
    authors: List[str]
    publish_date: Optional[datetime]
    metadata: ContentMetadata
    text_path: Optional[Path]  # Path to the text content file
    raw_data: Dict[str, Any]  # Raw data from the source

class ContentSource(ABC):
    """Abstract base class for content sources."""
    
    def __init__(self, cache_dir: Path, output_dir: Path):
        """
        Initialize the content source.
        
        Args:
            cache_dir: Directory for caching source-specific data
            output_dir: Directory for storing processed content
        """
        self.cache_dir = cache_dir
        self.output_dir = output_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def discover(self, query: str, limit: int = 10) -> List[ContentItem]:
        """
        Discover content based on a query.
        
        Args:
            query: Search query
            limit: Maximum number of items to return
            
        Returns:
            List of discovered content items
        """
        pass
    
    @abstractmethod
    def process_url(self, url: str) -> Optional[ContentItem]:
        """
        Process a single URL from this source.
        
        Args:
            url: URL to process
            
        Returns:
            Processed content item or None if processing failed
        """
        pass
    
    @abstractmethod
    def is_source_url(self, url: str) -> bool:
        """
        Check if a URL belongs to this source.
        
        Args:
            url: URL to check
            
        Returns:
            True if this source can handle the URL
        """
        pass

class ContentProcessor(ABC):
    """Abstract base class for content processors."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize the content processor.
        
        Args:
            output_dir: Directory for storing processed content
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def process(self, content: ContentItem) -> bool:
        """
        Process a content item.
        
        Args:
            content: Content item to process
            
        Returns:
            True if processing succeeded
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about processed content.
        
        Returns:
            Dictionary of statistics
        """
        pass

class ContentVisualizer(ABC):
    """Abstract base class for content visualization."""
    
    def __init__(self, data_dir: Path):
        """
        Initialize the content visualizer.
        
        Args:
            data_dir: Directory containing content data
        """
        self.data_dir = data_dir
    
    @abstractmethod
    def generate_table(self, items: List[ContentItem]) -> str:
        """
        Generate a table representation of content items.
        
        Args:
            items: List of content items to visualize
            
        Returns:
            String containing the table (e.g., markdown, CSV)
        """
        pass
    
    @abstractmethod
    def generate_stats(self, items: List[ContentItem]) -> Dict[str, Any]:
        """
        Generate statistics for content items.
        
        Args:
            items: List of content items to analyze
            
        Returns:
            Dictionary of statistics
        """
        pass 