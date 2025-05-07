"""
Processor implementation for technical papers.
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from ...interfaces import ContentProcessor, ContentItem

logger = logging.getLogger(__name__)

class PapersProcessor(ContentProcessor):
    """Processor for technical papers."""
    
    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.paper_stats_dir = self.output_dir / "stats"
        self.paper_stats_dir.mkdir(parents=True, exist_ok=True)
    
    def process(self, item: ContentItem) -> Dict[str, Any]:
        """
        Process a technical paper content item.
        
        Args:
            item: The content item to process
            
        Returns:
            Dictionary with processing stats and metadata
        """
        stats = {
            "id": item.id,
            "title": item.title,
            "url": item.url,
            "source": item.metadata.source_name,
            "word_count": 0,
            "author_count": len(item.authors),
            "pdf_path": item.text_path,
            "has_text_content": False
        }
        
        try:
            # Check if we have a PDF path
            if item.text_path and os.path.exists(item.text_path):
                stats["pdf_path"] = item.text_path
                
                # If we have extracted text content in the raw data, use it
                text_content = item.raw_data.get("text_content")
                if text_content:
                    stats["has_text_content"] = True
                    stats["word_count"] = len(text_content.split())
                    
                    # Try to extract technical terms and keywords
                    stats["keywords"] = self._extract_keywords(text_content)
                else:
                    # Try to extract text if not already done
                    try:
                        text = self._extract_text_from_pdf(item.text_path)
                        if text:
                            stats["has_text_content"] = True
                            stats["word_count"] = len(text.split())
                            stats["keywords"] = self._extract_keywords(text)
                    except Exception as e:
                        logger.warning(f"Error extracting text from PDF {item.text_path}: {str(e)}")
                        
                # Get PDF file size
                stats["file_size_bytes"] = os.path.getsize(item.text_path)
                stats["file_size_mb"] = stats["file_size_bytes"] / (1024 * 1024)
            
            # Extract additional metadata
            if item.metadata.additional_meta:
                stats["categories"] = item.metadata.additional_meta.get("categories", [])
                stats["source_type"] = item.metadata.additional_meta.get("source", "unknown")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error processing paper {item.id}: {str(e)}")
            stats["error"] = str(e)
            return stats
    
    def get_stats(self, items: List[ContentItem]) -> Dict[str, Any]:
        """
        Get aggregate statistics for a list of paper items.
        
        Args:
            items: List of paper content items
            
        Returns:
            Dictionary with aggregate statistics
        """
        stats = {
            "total_papers": len(items),
            "total_words": 0,
            "average_words": 0,
            "total_authors": 0,
            "average_authors": 0,
            "paper_types": {},
            "categories": {},
            "has_full_text": 0,
            "total_file_size_mb": 0
        }
        
        if not items:
            return stats
            
        # Process each item to get individual stats
        for item in items:
            try:
                item_stats = self.process(item)
                
                # Accumulate statistics
                stats["total_words"] += item_stats.get("word_count", 0)
                stats["total_authors"] += item_stats.get("author_count", 0)
                
                if item_stats.get("has_text_content", False):
                    stats["has_full_text"] += 1
                    
                stats["total_file_size_mb"] += item_stats.get("file_size_mb", 0)
                
                # Track paper types
                source_type = item_stats.get("source_type", "unknown")
                stats["paper_types"][source_type] = stats["paper_types"].get(source_type, 0) + 1
                
                # Track categories
                for category in item_stats.get("categories", []):
                    stats["categories"][category] = stats["categories"].get(category, 0) + 1
                    
            except Exception as e:
                logger.error(f"Error getting stats for item {item.id}: {str(e)}")
                
        # Calculate averages
        if stats["total_papers"] > 0:
            stats["average_words"] = stats["total_words"] / stats["total_papers"]
            stats["average_authors"] = stats["total_authors"] / stats["total_papers"]
        
        return stats
    
    def _extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """
        Extract technical keywords from paper text.
        Simple implementation that extracts capitalized phrases and common technical terms.
        
        Args:
            text: Text content to extract keywords from
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of extracted keywords
        """
        # Common technical terms pattern
        tech_patterns = [
            r'\b[A-Z][A-Za-z]+(Net|NN|ML|AI)\b',  # Neural Network terms
            r'\b(deep learning|machine learning|neural network|artificial intelligence)\b',
            r'\b[A-Z][A-Za-z]+ algorithm\b',  # Algorithm names
            r'\b[A-Z][A-Za-z]+ (framework|library|model)\b',  # Framework/library names
            r'\b[A-Z][A-Za-z]+ (method|approach|technique)\b',  # Method names
        ]
        
        keywords = set()
        
        # Find capitalized phrases (potential terms)
        cap_phrases = re.findall(r'\b[A-Z][A-Za-z0-9]+([-][A-Za-z0-9]+)?\b', text)
        for phrase in cap_phrases:
            if len(phrase) > 2:  # Filter out short abbreviations
                keywords.add(phrase)
        
        # Find technical terms
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Some regex patterns produce tuple matches
                    for m in match:
                        if m and len(m) > 3:
                            keywords.add(m)
                elif isinstance(match, str) and len(match) > 3:
                    keywords.add(match)
        
        # Limit to max_keywords
        return sorted(list(keywords))[:max_keywords]
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text from PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            import PyPDF2
            
            text = ""
            with open(pdf_path, 'rb') as file:  # Open in binary mode
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num in range(len(pdf_reader.pages)):
                        try:
                            page = pdf_reader.pages[page_num]
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n\n"
                        except Exception as e:
                            logger.warning(f"Error extracting text from page {page_num} in PDF {pdf_path}: {str(e)}")
                            continue
                except Exception as e:
                    logger.warning(f"Error reading PDF {pdf_path}: {str(e)}")
                    return ""
                    
            # If text is empty, log a warning
            if not text.strip():
                logger.warning(f"No text extracted from PDF: {pdf_path}")
                return ""
            
            return text
            
        except ImportError:
            logger.warning(f"Error extracting text from PDF {pdf_path}: No module named 'PyPDF2'")
            return ""
        except Exception as e:
            logger.warning(f"Error extracting text from PDF {pdf_path}: {str(e)}")
            return "" 