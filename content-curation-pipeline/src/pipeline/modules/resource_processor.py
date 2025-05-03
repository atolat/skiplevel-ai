"""
Resource processor module for handling different types of discovered resources.

This module provides specialized functions for processing various content types
such as academic papers (PDFs), GitHub repositories, and engineering blog articles.
"""

import os
import logging
import requests
import tempfile
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import hashlib
import io
import re

logger = logging.getLogger(__name__)

# Create directory for downloaded resources
RESOURCE_DIR = Path("./data/resources")
RESOURCE_DIR.mkdir(parents=True, exist_ok=True)

# Create directory for saved PDFs
PDF_DIR = Path("./data/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)

# Cache for processed resources
PROCESSED_CACHE_FILE = Path("./data/cache/processed_resources.json")
PROCESSED_CACHE = {}

# Load processed resource cache if exists
if PROCESSED_CACHE_FILE.exists():
    try:
        with open(PROCESSED_CACHE_FILE, 'r') as f:
            PROCESSED_CACHE = json.load(f)
            logger.info(f"Loaded {len(PROCESSED_CACHE)} processed resources from cache")
    except Exception as e:
        logger.error(f"Error loading processed resource cache: {str(e)}")

def save_processed_cache():
    """Save processed resources to cache file."""
    PROCESSED_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(PROCESSED_CACHE_FILE, 'w') as f:
            json.dump(PROCESSED_CACHE, f, indent=2)
        logger.info(f"Saved {len(PROCESSED_CACHE)} processed resources to cache")
    except Exception as e:
        logger.error(f"Error saving processed resource cache: {str(e)}")

def get_resource_key(resource: Dict[str, Any]) -> str:
    """Generate a unique key for a resource."""
    if "url" in resource:
        return f"{resource['source']}_{hashlib.md5(resource['url'].encode()).hexdigest()}"
    elif "title" in resource:
        return f"{resource['source']}_{hashlib.md5(resource['title'].encode()).hexdigest()}"
    else:
        return f"unknown_{hashlib.md5(str(resource).encode()).hexdigest()}"

def process_arxiv_paper(resource: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an arXiv paper resource.
    
    Args:
        resource: The paper resource dictionary
        
    Returns:
        Processed resource with extracted content
    """
    logger.info(f"Processing arXiv paper: {resource.get('title')}")
    
    # Generate cache key
    resource_key = get_resource_key(resource)
    
    # Check cache
    if resource_key in PROCESSED_CACHE:
        logger.info(f"Using cached processed arXiv paper: {resource.get('title')}")
        return PROCESSED_CACHE[resource_key]
    
    try:
        # Download the PDF
        pdf_url = resource.get("url")
        if not pdf_url:
            logger.error(f"No PDF URL for arXiv paper: {resource.get('title')}")
            return resource
        
        # Process PDF content
        try:
            # Import PDF processing libraries here to avoid unnecessary dependencies
            import PyPDF2
            import io
            
            # Download PDF
            logger.info(f"Downloading PDF from {pdf_url}")
            response = requests.get(pdf_url)
            response.raise_for_status()
            
            # Create a safe filename from the title
            safe_title = re.sub(r'[^\w\-_\. ]', '_', resource.get('title', 'unknown'))
            safe_title = safe_title[:100]  # Limit filename length
            pdf_filename = f"{safe_title}_{resource_key[-8:]}.pdf"
            pdf_path = PDF_DIR / pdf_filename
            
            # Save the PDF to disk
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(response.content)
            logger.info(f"Saved PDF to {pdf_path}")
            
            # Extract text from PDF
            with io.BytesIO(response.content) as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                
                # Get text from first 10 pages (to keep it manageable)
                max_pages = min(10, len(pdf_reader.pages))
                for page_num in range(max_pages):
                    text += pdf_reader.pages[page_num].extract_text() + "\n\n"
            
            # Create a summary of the paper using the abstract/summary
            summary = resource.get("summary", "")
            if len(summary) > 1000:
                summary = summary[:1000] + "..."
            
            # Store processed information
            processed_resource = {
                **resource,
                "content_type": "academic_paper",
                "text": text,
                "summary": summary,
                "is_processed": True,
                "process_error": None,
                "content_length": len(text),
                "local_pdf_path": str(pdf_path)
            }
            
            # Cache the processed resource
            PROCESSED_CACHE[resource_key] = processed_resource
            save_processed_cache()
            
            return processed_resource
        
        except ImportError:
            logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
            resource["process_error"] = "PDF processing libraries not available"
            return resource
        
    except Exception as e:
        logger.error(f"Error processing arXiv paper {resource.get('title')}: {str(e)}")
        resource["process_error"] = str(e)
        return resource

def process_github_repository(resource: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a GitHub repository resource.
    
    Args:
        resource: The GitHub repository resource dictionary
        
    Returns:
        Processed resource with extracted content
    """
    logger.info(f"Processing GitHub repository: {resource.get('title')}")
    
    # Generate cache key
    resource_key = get_resource_key(resource)
    
    # Check cache
    if resource_key in PROCESSED_CACHE:
        logger.info(f"Using cached processed GitHub repository: {resource.get('title')}")
        return PROCESSED_CACHE[resource_key]
    
    try:
        # GitHub repositories already have README content from the discovery phase
        readme_content = resource.get("readme_content", "")
        description = resource.get("description", "")
        
        # Combine README and description
        full_text = f"# {resource.get('title', 'Untitled Repository')}\n\n"
        full_text += f"{description}\n\n" if description else ""
        full_text += readme_content
        
        # Clean up markdown syntax for better text processing
        # Remove code blocks
        full_text = re.sub(r'```[^`]*```', ' CODE_BLOCK ', full_text)
        # Remove URLs
        full_text = re.sub(r'https?://\S+', ' URL ', full_text)
        # Remove image references
        full_text = re.sub(r'!\[.*?\]\(.*?\)', ' IMAGE ', full_text)
        
        # Store processed information
        processed_resource = {
            **resource,
            "content_type": "github_repository",
            "text": full_text,
            "is_processed": True,
            "process_error": None,
            "content_length": len(full_text)
        }
        
        # Cache the processed resource
        PROCESSED_CACHE[resource_key] = processed_resource
        save_processed_cache()
        
        return processed_resource
        
    except Exception as e:
        logger.error(f"Error processing GitHub repository {resource.get('title')}: {str(e)}")
        resource["process_error"] = str(e)
        return resource

def process_blog_article(resource: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a blog article by fetching and extracting its content.
    
    Args:
        resource: The blog article resource dictionary
        
    Returns:
        Processed resource with extracted content
    """
    logger.info(f"Processing blog article: {resource.get('title')}")
    
    # Generate cache key
    resource_key = get_resource_key(resource)
    
    # Check cache
    if resource_key in PROCESSED_CACHE:
        logger.info(f"Using cached processed blog article: {resource.get('title')}")
        return PROCESSED_CACHE[resource_key]
    
    try:
        # Import necessary libraries
        from bs4 import BeautifulSoup
        import requests
        from newspaper import Article
        
        url = resource.get("url")
        if not url:
            logger.error(f"No URL for blog article: {resource.get('title')}")
            return resource
        
        # Use newspaper3k to extract the article content
        article = Article(url)
        article.download()
        article.parse()
        
        # Get the article text
        text = article.text
        
        # Get the article title if not already present
        title = resource.get("title") or article.title
        
        # Store processed information
        processed_resource = {
            **resource,
            "title": title,
            "content_type": "blog_article",
            "text": text,
            "authors": article.authors,
            "publish_date": str(article.publish_date) if article.publish_date else None,
            "is_processed": True,
            "process_error": None,
            "content_length": len(text)
        }
        
        # Cache the processed resource
        PROCESSED_CACHE[resource_key] = processed_resource
        save_processed_cache()
        
        return processed_resource
        
    except Exception as e:
        logger.error(f"Error processing blog article {resource.get('title')}: {str(e)}")
        resource["process_error"] = str(e)
        return resource

def process_resource(resource: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a resource based on its type.
    
    Args:
        resource: The resource dictionary
        
    Returns:
        Processed resource with extracted content
    """
    source = resource.get("source", "unknown")
    content_type = resource.get("meta", {}).get("content_type", "unknown")
    
    if source == "arxiv" or content_type == "academic_paper":
        return process_arxiv_paper(resource)
    elif source == "github" or content_type == "github_repository":
        return process_github_repository(resource)
    elif "blog" in source or content_type == "blog_article":
        return process_blog_article(resource)
    else:
        logger.warning(f"Unknown resource type: {source}/{content_type}")
        return resource

def process_resources(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of resources.
    
    Args:
        resources: List of resource dictionaries
        
    Returns:
        List of processed resources
    """
    logger.info(f"Processing {len(resources)} resources")
    
    processed_resources = []
    for resource in resources:
        try:
            processed_resource = process_resource(resource)
            processed_resources.append(processed_resource)
        except Exception as e:
            logger.error(f"Error processing resource {resource.get('title', 'Unknown')}: {str(e)}")
            resource["process_error"] = str(e)
            processed_resources.append(resource)
    
    logger.info(f"Processed {len(processed_resources)} resources")
    return processed_resources

def save_cached_pdfs():
    """
    Utility function to save PDFs from the existing cache.
    This can be called to retroactively save PDFs that were
    previously only stored in the cache.
    """
    if not PROCESSED_CACHE:
        logger.warning("No processed resources in cache to save PDFs from")
        return
    
    pdf_count = 0
    for key, resource in PROCESSED_CACHE.items():
        if resource.get("source") == "arxiv" and "url" in resource:
            try:
                # Only process if we don't already have a local path
                if "local_pdf_path" in resource and os.path.exists(resource["local_pdf_path"]):
                    logger.info(f"PDF already saved at {resource['local_pdf_path']}")
                    pdf_count += 1
                    continue
                
                pdf_url = resource.get("url")
                if not pdf_url:
                    continue
                
                # Create a safe filename from the title
                safe_title = re.sub(r'[^\w\-_\. ]', '_', resource.get('title', 'unknown'))
                safe_title = safe_title[:100]  # Limit filename length
                pdf_filename = f"{safe_title}_{key[-8:]}.pdf"
                pdf_path = PDF_DIR / pdf_filename
                
                # Download and save the PDF
                logger.info(f"Downloading PDF from {pdf_url}")
                response = requests.get(pdf_url)
                response.raise_for_status()
                
                with open(pdf_path, 'wb') as pdf_file:
                    pdf_file.write(response.content)
                
                # Update the cache entry with the local path
                resource["local_pdf_path"] = str(pdf_path)
                pdf_count += 1
                logger.info(f"Saved PDF to {pdf_path}")
                
            except Exception as e:
                logger.error(f"Error saving PDF for {resource.get('title')}: {str(e)}")
    
    # Save the updated cache
    save_processed_cache()
    logger.info(f"Saved {pdf_count} PDFs from cache")
    return pdf_count 