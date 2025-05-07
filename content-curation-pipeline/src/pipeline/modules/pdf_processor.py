"""
PDF processor module for handling PDF resources.
"""

import os
import logging
import requests
import json
import time
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Create directory for saved PDFs
PDF_DIR = Path("./data/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)

# Cache for processed PDFs
CACHE_DIR = Path("./data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / "pdf_cache.json"
PDF_CACHE = {}

# Load cache if exists
if CACHE_FILE.exists():
    try:
        with open(CACHE_FILE, 'r') as f:
            PDF_CACHE = json.load(f)
            logger.info(f"Loaded {len(PDF_CACHE)} PDFs from cache")
    except Exception as e:
        logger.error(f"Error loading PDF cache: {str(e)}")

def save_cache():
    """Save PDF cache to file."""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(PDF_CACHE, f, indent=2)
        logger.info(f"Saved {len(PDF_CACHE)} PDFs to cache")
    except Exception as e:
        logger.error(f"Error saving PDF cache: {str(e)}")

def download_pdf(url: str, source: str = "unknown", title: str = None) -> Optional[Dict[str, Any]]:
    """
    Download a PDF from a URL and save it locally.
    
    Args:
        url: URL of the PDF
        source: Source of the PDF (e.g., arxiv, ieee)
        title: Title of the PDF (used for filename)
        
    Returns:
        Dictionary with PDF metadata if successful, None otherwise
    """
    # Generate cache key
    cache_key = f"pdf_{hashlib.md5(url.encode()).hexdigest()}"
    
    # Check cache
    if cache_key in PDF_CACHE:
        cache_time = PDF_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 30 * 24 * 60 * 60:  # 30 days
            pdf_data = PDF_CACHE[cache_key].get("data")
            if pdf_data and pdf_data.get("path") and os.path.exists(pdf_data["path"]):
                logger.info(f"Using cached PDF for {url}")
                return pdf_data
    
    # Normalize URL for specific sources
    try:
        if "arxiv.org" in url and not url.endswith(".pdf"):
            # Convert arxiv abstract URL to PDF URL if needed
            if "/abs/" in url:
                url = url.replace("/abs/", "/pdf/") + ".pdf"
            elif "/pdf/" in url and not url.endswith(".pdf"):
                url = url + ".pdf"
    except Exception as e:
        logger.warning(f"Error normalizing URL {url}: {str(e)}")
    
    # Download with retry logic
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading PDF from {url} (attempt {attempt + 1}/{max_retries})")
            
            # Set headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/pdf,*/*;q=0.9',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
            }
            
            # Download the PDF
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Check if we got HTML or JSON instead of PDF
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' in content_type or 'application/json' in content_type:
                if not response.content.startswith(b'%PDF-'):
                    # For arXiv, we might need to adjust the URL
                    if "arxiv.org" in url:
                        # Try alternative URL format
                        paper_id = url.split('/')[-1].replace(".pdf", "")
                        alt_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
                        if alt_url != url:
                            logger.info(f"Trying alternative arXiv URL: {alt_url}")
                            return download_pdf(alt_url, source, title)
                    
                    raise ValueError(f"Downloaded content is not a PDF (got {content_type})")
            
            # Validate PDF content
            content = response.content
            if not content.startswith(b'%PDF-'):
                raise ValueError("Downloaded content is not a valid PDF")
            
            # Create safe filename
            if title:
                safe_title = re.sub(r'[^\w\-_\. ]', '_', title)
                safe_title = safe_title[:100]  # Limit length
            else:
                # Extract filename from URL
                filename = url.split('/')[-1].split('?')[0]
                safe_title = re.sub(r'[^\w\-_\. ]', '_', filename)
                if not safe_title or len(safe_title) < 5:
                    safe_title = f"document_{hashlib.md5(url.encode()).hexdigest()[:8]}"
                
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d")
            pdf_filename = f"{source}_{timestamp}_{safe_title}"
            if not pdf_filename.endswith(".pdf"):
                pdf_filename += ".pdf"
                
            pdf_path = PDF_DIR / pdf_filename
            
            # Create directory if it doesn't exist
            PDF_DIR.mkdir(parents=True, exist_ok=True)
            
            # Save PDF
            with open(pdf_path, 'wb') as f:
                f.write(content)
            
            # Verify file saved successfully
            if not os.path.exists(pdf_path):
                raise IOError("PDF file was not saved successfully")
            
            # Extract text (if PyPDF2 is available)
            text_content = ""
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(pdf_path)
                for page_num in range(len(pdf_reader.pages)):
                    page_text = pdf_reader.pages[page_num].extract_text()
                    if page_text:
                        text_content += page_text + "\n\n"
            except ImportError:
                logger.warning("PyPDF2 not available, skipping text extraction")
            except Exception as e:
                logger.warning(f"Error extracting text from PDF: {str(e)}")
            
            # Create result
            result = {
                "url": url,
                "source": source,
                "title": title or safe_title,
                "path": str(pdf_path),
                "download_time": datetime.now().isoformat(),
                "text_content": text_content if text_content else None,
                "size_bytes": os.path.getsize(pdf_path)
            }
            
            # Cache result
            PDF_CACHE[cache_key] = {
                "timestamp": time.time(),
                "data": result
            }
            save_cache()
            
            logger.info(f"Successfully downloaded PDF from {url} to {pdf_path}")
            return result
            
        except IOError as e:
            # This is likely a file system error
            if "No such file or directory" in str(e):
                # Try creating parent directories
                try:
                    PDF_DIR.mkdir(parents=True, exist_ok=True)
                except Exception as mkdir_err:
                    logger.error(f"Failed to create PDF directory: {str(mkdir_err)}")
            
            if attempt == max_retries - 1:
                logger.error(f"Failed to download PDF after {max_retries} attempts: {str(e)}")
                logger.error(f"Failed to download PDF from {url}")
                return None
            else:
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay}s: {str(e)}")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
        
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to download PDF after {max_retries} attempts: {str(e)}")
                logger.error(f"Failed to download PDF from {url}")
                return None
            else:
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay}s: {str(e)}")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
    
    return None

def save_cached_pdfs(urls: List[str] = None):
    """
    Save PDFs from the cache or from a list of URLs.
    
    Args:
        urls: Optional list of URLs to download PDFs from
        
    Returns:
        Number of PDFs successfully saved
    """
    if urls:
        # Download PDFs from URLs
        stats = {
            "total": len(urls),
            "success": 0,
            "failed": 0
        }
        
        for url in urls:
            try:
                # Check if URL is likely a PDF or could be converted to a PDF URL
                pdf_url = url
                if "arxiv.org" in url and "/abs/" in url:
                    pdf_url = url.replace("/abs/", "/pdf/") + ".pdf"
                elif not url.lower().endswith('.pdf') and not any(domain in url for domain in ["arxiv.org", "ieee.org", "acm.org"]):
                    logger.warning(f"URL does not seem to be a PDF: {url}")
                    stats["failed"] += 1
                    continue
                
                # Determine source
                source = "unknown"
                if "arxiv.org" in url:
                    source = "arxiv"
                elif "ieee.org" in url:
                    source = "ieee"
                elif "acm.org" in url:
                    source = "acm"
                elif "springer.com" in url:
                    source = "springer"
                elif "sciencedirect.com" in url:
                    source = "sciencedirect"
                
                # Download PDF
                result = download_pdf(pdf_url, source)
                if result:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                    
            except Exception as e:
                logger.error(f"Error downloading PDF from {url}: {str(e)}")
                stats["failed"] += 1
        
        # Log summary
        logger.info("\nPDF Download Summary:")
        logger.info(f"Total URLs: {stats['total']}")
        logger.info(f"Successfully downloaded: {stats['success']}")
        logger.info(f"Failed: {stats['failed']}")
        
        return stats["success"]
        
    else:
        # Check for already cached URLs that haven't been downloaded
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0
        }
        
        for key, value in PDF_CACHE.items():
            if key.startswith("pdf_"):
                stats["total"] += 1
                pdf_data = value.get("data", {})
                
                # Check if PDF has been downloaded and the file exists
                if "path" in pdf_data and os.path.exists(pdf_data["path"]):
                    logger.info(f"PDF already saved at {pdf_data['path']}")
                    stats["success"] += 1
                    continue
                
                # Download if URL exists but file doesn't
                if "url" in pdf_data:
                    url = pdf_data["url"]
                    source = pdf_data.get("source", "unknown")
                    title = pdf_data.get("title")
                    
                    result = download_pdf(url, source, title)
                    if result:
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1
                else:
                    stats["failed"] += 1
        
        # Log summary
        logger.info("\nPDF Download Summary:")
        logger.info(f"Total cached PDFs: {stats['total']}")
        logger.info(f"Successfully downloaded/verified: {stats['success']}")
        logger.info(f"Failed: {stats['failed']}")
        
        return stats["success"]

def batch_download_pdfs(urls_with_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Download multiple PDFs with metadata.
    
    Args:
        urls_with_metadata: List of dictionaries with 'url', 'source', and 'title' keys
        
    Returns:
        List of results
    """
    results = []
    
    for item in urls_with_metadata:
        url = item.get("url")
        if not url:
            logger.warning("Missing URL in item")
            continue
            
        source = item.get("source", "unknown")
        title = item.get("title")
        
        result = download_pdf(url, source, title)
        if result:
            # Merge with original metadata
            merged_result = {**item, **result}
            results.append(merged_result)
        else:
            logger.warning(f"Failed to download PDF from {url}")
            item["error"] = "Failed to download PDF"
            results.append(item)
    
    return results 