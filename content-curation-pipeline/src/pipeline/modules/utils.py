"""
Utility functions for pipeline management.
"""

import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def clean_data(clean_pdfs=True, clean_texts=True, clean_cache=True, clean_medium=True):
    """
    Clean data directories by removing files
    
    Args:
        clean_pdfs: Whether to clean the PDFs directory
        clean_texts: Whether to clean the texts directory
        clean_cache: Whether to clean the cache directory
        clean_medium: Whether to clean the Medium texts directory
    
    Returns:
        dict: Count of files removed from each directory
    """
    base_dir = Path("./data")
    results = {'pdfs': 0, 'texts': 0, 'cache': 0, 'medium': 0}
    
    if clean_pdfs:
        pdf_dir = base_dir / "pdfs"
        if pdf_dir.exists():
            file_count = len(list(pdf_dir.glob("*")))
            for file_path in pdf_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            results['pdfs'] = file_count
            logger.info(f"Removed {file_count} files from {pdf_dir}")
    
    if clean_texts:
        text_dir = base_dir / "texts"
        if text_dir.exists():
            # Count and remove non-directory files in the texts directory
            file_count = 0
            for file_path in text_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
                    file_count += 1
            results['texts'] = file_count
            logger.info(f"Removed {file_count} files from {text_dir}")
    
    # Handle Medium files specifically
    if clean_medium:
        medium_dir = base_dir / "texts" / "medium"
        if medium_dir.exists():
            file_count = len(list(medium_dir.glob("*")))
            for file_path in medium_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            results['medium'] = file_count
            logger.info(f"Removed {file_count} Medium files from {medium_dir}")
    
    if clean_cache:
        cache_dir = base_dir / "cache"
        if cache_dir.exists():
            file_count = 0
            # Clean all cache files recursively
            for file_path in cache_dir.glob("**/*"):
                if file_path.is_file():
                    file_path.unlink()
                    file_count += 1
            
            # Also clean Medium discovery cache specifically
            medium_cache_dir = cache_dir / "medium_discovery"
            if medium_cache_dir.exists() and medium_cache_dir.is_dir():
                shutil.rmtree(medium_cache_dir)
                logger.info(f"Removed Medium discovery cache directory")
            
            results['cache'] = file_count
            logger.info(f"Removed {file_count} files from cache directories")
    
    return results 