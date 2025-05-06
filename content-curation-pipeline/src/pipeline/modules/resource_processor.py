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
from .text_cleaning import preprocess_text_for_chunking
import time
import shutil
from bs4 import BeautifulSoup
import html2text
from . import medium_api

logger = logging.getLogger(__name__)

# Create directory for downloaded resources
RESOURCE_DIR = Path("./data/resources")
RESOURCE_DIR.mkdir(parents=True, exist_ok=True)

# Create directory for saved PDFs
PDF_DIR = Path("./data/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)

# Create directory for extracted text
TEXT_DIR = Path("./data/texts")
TEXT_DIR.mkdir(parents=True, exist_ok=True)

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

def save_text_content(text: str, resource_key: str, source_type: str = None) -> str:
    """
    Save text content to a file instead of storing it in JSON.
    
    Args:
        text: The text content to save
        resource_key: Unique identifier for the resource
        source_type: Type of source for text cleaning
        
    Returns:
        Path to the saved text file
    """
    # Clean the text before saving
    cleaned_text = preprocess_text_for_chunking(text, source_type)
    
    # Create a filename based on the resource key
    text_filename = f"{resource_key}.txt"
    text_path = TEXT_DIR / text_filename
    
    # Save the text to file
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_text)
    
    return str(text_path)

def load_text_content(text_path: str) -> str:
    """
    Load text content from a file.
    
    Args:
        text_path: Path to the text file
        
    Returns:
        The text content
    """
    try:
        with open(text_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading text content from {text_path}: {str(e)}")
        return ""

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
        cached_resource = PROCESSED_CACHE[resource_key]
        return cached_resource
    
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
            
            # For PDFs, we'll skip extracting text to text files
            # as we'll chunk directly from the PDF source later
            
            # Get a summary if available
            summary = resource.get("summary", "")
            if len(summary) > 1000:
                summary = summary[:1000] + "..."
            
            # Store processed information
            processed_resource = {
                **resource,
                "content_type": "academic_paper",
                "summary": summary,
                "is_processed": True,
                "process_error": None,
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
        cached_resource = PROCESSED_CACHE[resource_key]
        return cached_resource
    
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
        clean_text = re.sub(r'```[^`]*```', ' CODE_BLOCK ', full_text)
        # Remove URLs
        clean_text = re.sub(r'https?://\S+', ' URL ', clean_text)
        # Remove image references
        clean_text = re.sub(r'!\[.*?\]\(.*?\)', ' IMAGE ', clean_text)
        
        # Save text to separate file - preserve all text
        text_path = save_text_content(clean_text, resource_key, "markdown")
        
        # Store processed information
        processed_resource = {
            **resource,
            "content_type": "github_repository",
            "text_path": text_path,  # Store path instead of text
            "is_processed": True,
            "process_error": None,
            "content_length": len(clean_text)
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
    
    # Skip if the article is already fully processed (e.g., by the Medium API discovery)
    if resource.get("is_processed") and "text_path" in resource:
        logger.info(f"Using pre-processed blog article: {resource.get('title')}")
        return resource
    
    # Generate cache key
    resource_key = get_resource_key(resource)
    
    # Check cache
    if resource_key in PROCESSED_CACHE:
        logger.info(f"Using cached processed blog article: {resource.get('title')}")
        cached_resource = PROCESSED_CACHE[resource_key]
        return cached_resource
    
    # Special handling for Medium API content
    if resource.get("meta", {}).get("medium_api") and "api_content" in resource:
        try:
            logger.info(f"Processing Medium API content for: {resource.get('title')}")
            
            # Get the API content
            html_content = resource.get("api_content", "")
            
            # Extract text from HTML using our medium_api module
            text = medium_api.extract_text_from_html(html_content)
            
            # Get the article title
            title = resource.get("title") or "Untitled Medium Article"
            
            # Save text to separate file - preserve all content
            text_path = save_text_content(text, resource_key, "html")
            
            # Store processed information
            processed_resource = {
                **resource,
                "title": title,
                "content_type": "blog_article",
                "text_path": text_path,  # Store path instead of text
                "is_processed": True,
                "process_error": None,
                "content_length": len(text),
                "extract_method": "medium_api"
            }
            
            # Remove the large api_content field to save space in cache
            if "api_content" in processed_resource:
                del processed_resource["api_content"]
            
            # Cache the processed resource
            PROCESSED_CACHE[resource_key] = processed_resource
            save_processed_cache()
            
            return processed_resource
            
        except Exception as e:
            logger.error(f"Error processing Medium API content for {resource.get('title')}: {str(e)}")
            # Fall back to standard processing
    
    # Identify Medium URLs and skip them - they should be handled by the discovery function
    url = resource.get("url", "")
    if "medium.com" in url:
        logger.warning(f"Skipping Medium URL, should be handled by discovery: {url}")
        resource["process_error"] = "Medium URLs should be handled by the discovery function"
        return resource
    
    try:
        # Import necessary libraries
        from bs4 import BeautifulSoup
        import requests
        from newspaper import Article, Config
        
        if not url:
            logger.error(f"No URL for blog article: {resource.get('title')}")
            return resource
        
        # Check if URL is valid (must have scheme)
        if not url.startswith(('http://', 'https://')):
            # Try to fix common URL issues
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                # Try to extract domain from source
                source = resource.get('source', '')
                if 'blog_' in source and '_' in source:
                    domain_hint = source.split('blog_')[1].replace('_', '.')
                    if domain_hint:
                        url = f"https://{domain_hint}{url}"
                    else:
                        logger.error(f"Invalid URL format and cannot determine domain: {url}")
                        resource["process_error"] = f"Invalid URL format: {url}"
                        return resource
            elif url.startswith('@') and 'medium' in resource.get('source', ''):
                logger.warning(f"Skipping Medium profile URL, should be handled by discovery: {url}")
                resource["process_error"] = "Medium URLs should be handled by the discovery function"
                return resource
            else:
                logger.error(f"Invalid URL format: {url}")
                resource["process_error"] = f"Invalid URL format: {url}"
                return resource
        
        logger.info(f"Fetching content from: {url}")
        
        # Configure newspaper with longer timeout and browser user-agent
        config = Config()
        config.browser_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        config.request_timeout = 15
        
        # Use newspaper3k to extract the article content
        article = Article(url, config=config)
        
        # Initialize text variable
        text = ""
        extract_method = "failed"
        
        try:
            article.download()
            article.parse()
            text = article.text
            extract_method = "newspaper3k"
            
            # If article text is too short, try to get more content using requests and BeautifulSoup
            if len(text) < 500:
                logger.info(f"Article text is short ({len(text)} chars), trying direct HTML parsing")
                response = requests.get(url, headers={
                    'User-Agent': config.browser_user_agent
                }, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script, style, nav, and footer elements
                for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    element.decompose()
                
                # Try to find article content
                article_content = soup.find('article') or soup.find(class_=['content', 'article', 'post'])
                if article_content:
                    # Use content from article tag if found
                    backup_text = article_content.get_text(separator="\n\n")
                else:
                    # Fallback to main content or body
                    main_content = soup.find('main') or soup.find('body')
                    backup_text = main_content.get_text(separator="\n\n") if main_content else ""
                
                # Use the longer text
                if len(backup_text) > len(text):
                    logger.info(f"Using direct HTML parsing result ({len(backup_text)} chars)")
                    text = backup_text
                    extract_method = "direct_html"
        except Exception as e:
            logger.error(f"Error downloading article: {str(e)}")
            # Try direct request as fallback
            try:
                logger.info(f"Trying direct request as fallback for {url}")
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script, style, nav, and footer elements
                for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    element.decompose()
                    
                # Try to find article content
                article_content = soup.find('article') or soup.find(class_=['content', 'article', 'post'])
                if article_content:
                    text = article_content.get_text(separator="\n\n")
                else:
                    # Fallback to main content or body
                    main_content = soup.find('main') or soup.find('body')
                    text = main_content.get_text(separator="\n\n") if main_content else ""
                
                extract_method = "fallback_html"
                
                # Try to extract article title if not already present
                if not resource.get("title") or resource.get("title") == "Untitled":
                    title_elem = soup.find('h1') or soup.find('title')
                    if title_elem:
                        resource["title"] = title_elem.get_text().strip()
            except Exception as nested_error:
                logger.error(f"Error with fallback request: {str(nested_error)}")
                resource["process_error"] = f"Failed to extract content: {str(e)}, fallback error: {str(nested_error)}"
                return resource
        
        # Get the article title if not already present
        title = resource.get("title") or getattr(article, 'title', '') or "Untitled Article"
        
        # If still no meaningful text, return error
        if not text or len(text.strip()) < 100:
            logger.error(f"Failed to extract meaningful content from {url}")
            resource["process_error"] = "Failed to extract meaningful content"
            return resource
        
        # Save text to separate file - preserve all content
        text_path = save_text_content(text, resource_key, "html")
        
        # Store processed information
        processed_resource = {
            **resource,
            "title": title,
            "content_type": "blog_article",
            "text_path": text_path,  # Store path instead of text
            "authors": getattr(article, 'authors', []),
            "publish_date": str(article.publish_date) if hasattr(article, 'publish_date') and article.publish_date else None,
            "is_processed": True,
            "process_error": None,
            "content_length": len(text),
            "extract_method": extract_method
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

def get_resource_text(resource: Dict[str, Any]) -> str:
    """
    Get the text content of a resource.
    
    Args:
        resource: The resource dictionary
        
    Returns:
        Text content of the resource
    """
    # Check if resource has direct text
    if "text" in resource and resource["text"]:
        return resource["text"]
    
    # Check if resource has text path
    if "text_path" in resource and resource["text_path"]:
        text_path = Path(resource["text_path"])
        if text_path.exists():
            try:
                with open(text_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading text file {text_path}: {str(e)}")
    
    # Check if resource has Medium API content
    if "api_content" in resource and resource["api_content"]:
        try:
            # Extract text from HTML
            return medium_api.extract_text_from_html(resource["api_content"])
        except Exception as e:
            logger.error(f"Error extracting text from API content: {str(e)}")
    
    # Check if resource has a PDF
    if "local_pdf_path" in resource and resource["local_pdf_path"]:
        pdf_path = Path(resource["local_pdf_path"])
        if pdf_path.exists():
            try:
                # Extract text from PDF
                text = ""
                with open(pdf_path, "rb") as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text += page.extract_text() + "\n\n"
                return text
            except Exception as e:
                logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
    
    # No text available
    return ""

def process_resources(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of resources in parallel.
    
    Args:
        resources: List of resource dictionaries
        
    Returns:
        List of processed resources
    """
    import concurrent.futures
    from functools import partial
    
    logger.info(f"Processing {len(resources)} resources")
    
    if not resources:
        return []
    
    # Use parallel processing to handle multiple resources simultaneously
    max_workers = min(len(resources), 8)  # Cap at 8 concurrent workers
    
    processed_resources = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all resources for processing
        future_to_resource = {executor.submit(process_resource, resource): resource for resource in resources}
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_resource):
            try:
                processed_resource = future.result()
                processed_resources.append(processed_resource)
            except Exception as e:
                resource = future_to_resource[future]
                logger.error(f"Error processing resource {resource.get('title', 'Unknown')}: {str(e)}")
                resource["process_error"] = str(e)
                processed_resources.append(resource)
    
    logger.info(f"Processed {len(processed_resources)} resources in parallel with {max_workers} workers")
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