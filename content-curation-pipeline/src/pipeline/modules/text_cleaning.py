"""
Text cleaning module for preprocessing content before chunking.

This module provides functions to clean and normalize text from various sources
before it's processed further in the pipeline.
"""

import re
import logging
import html
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

def clean_html(text: str) -> str:
    """
    Clean HTML tags and entities from text.
    
    Args:
        text: HTML text to clean
        
    Returns:
        Cleaned text
    """
    # Decode HTML entities
    text = html.unescape(text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    return text

def clean_markdown(text: str) -> str:
    """
    Clean Markdown syntax from text.
    
    Args:
        text: Markdown text to clean
        
    Returns:
        Cleaned text
    """
    # Remove code blocks
    text = re.sub(r'```[^`]*```', ' ', text)
    text = re.sub(r'`[^`]*`', ' ', text)
    
    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove emphasis
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    
    # Remove images
    text = re.sub(r'!\[(.*?)\]\((.*?)\)', '', text)
    
    # Convert links to just their text
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', text)
    
    # Remove horizontal rules
    text = re.sub(r'^\s*[\*\-_]{3,}\s*$', '', text, flags=re.MULTILINE)
    
    return text

def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    # Replace all whitespace sequences with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace on each line
    text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)
    
    # Ensure paragraphs are separated by double newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def remove_urls(text: str) -> str:
    """
    Remove URLs from text.
    
    Args:
        text: Text to clean
        
    Returns:
        Text with URLs removed
    """
    return re.sub(r'https?://\S+', '', text)

def clean_pdf_artifacts(text: str) -> str:
    """
    Clean common PDF extraction artifacts.
    
    Args:
        text: Text from PDF to clean
        
    Returns:
        Cleaned text
    """
    # Remove page numbers
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    
    # Remove headers/footers that often appear on every page
    # This is a simplistic approach - may need to be customized per document
    text = re.sub(r'^\s*.{1,50}$', '', text, flags=re.MULTILINE)
    
    # Fix hyphenated words across line breaks
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    
    # Remove weird character sequences often found in PDFs
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    
    return text

def clean_special_chars(text: str) -> str:
    """
    Clean special characters that may cause issues.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Replace non-breaking spaces with regular spaces
    text = text.replace('\xa0', ' ')
    
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text

def clean_text(text: str, source_type: str = "general") -> str:
    """
    Clean text based on the source type.
    
    Args:
        text: Text to clean
        source_type: Type of source ("pdf", "html", "markdown", "general")
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
        
    # Apply common cleaning
    text = clean_special_chars(text)
    
    # Apply source-specific cleaning
    if source_type == "pdf":
        text = clean_pdf_artifacts(text)
    elif source_type == "html":
        text = clean_html(text)
    elif source_type == "markdown":
        text = clean_markdown(text)
    
    # Apply final normalization
    text = remove_urls(text)
    text = normalize_whitespace(text)
    
    return text

def auto_detect_source_type(text: str) -> str:
    """
    Automatically detect the source type based on content.
    
    Args:
        text: Text to analyze
        
    Returns:
        Detected source type ("pdf", "html", "markdown", "general")
    """
    # Check for HTML
    if re.search(r'<\/?[a-z]+[^>]*>', text):
        return "html"
    
    # Check for Markdown
    markdown_patterns = [
        r'^#{1,6}\s+',  # Headers
        r'\*\*(.*?)\*\*',  # Bold
        r'\[(.*?)\]\((.*?)\)',  # Links
        r'```',  # Code blocks
    ]
    
    if any(re.search(pattern, text) for pattern in markdown_patterns):
        return "markdown"
    
    # Check for PDF artifacts
    pdf_patterns = [
        r'\f',  # Form feed character often in PDFs
        r'\n\s*\d+\s*\n',  # Page numbers
    ]
    
    if any(re.search(pattern, text) for pattern in pdf_patterns):
        return "pdf"
    
    # Default to general
    return "general"

def preprocess_text_for_chunking(text: str, source_type: Optional[str] = None) -> str:
    """
    Preprocess text before chunking, including cleaning and normalization.
    
    Args:
        text: Text to preprocess
        source_type: Type of source, or None to auto-detect
        
    Returns:
        Preprocessed text ready for chunking
    """
    if not text:
        return ""
    
    # Auto-detect source type if not provided
    if source_type is None:
        source_type = auto_detect_source_type(text)
    
    # Clean the text based on source type
    cleaned_text = clean_text(text, source_type)
    
    # Preserve paragraphs but don't over-fragment
    # Instead of breaking at every sentence, maintain natural paragraph structure
    # Only ensure that there are proper paragraph breaks
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)  # Normalize multiple newlines
    
    # If there are very few paragraph breaks in a long text, add some breaks
    # at logical points (like after periods followed by spaces and a capital letter)
    if len(cleaned_text) > 1000 and cleaned_text.count('\n\n') < 3:
        cleaned_text = re.sub(r'([.!?])\s+([A-Z])', r'\1\n\n\2', cleaned_text)
    
    return cleaned_text 