"""
Utility functions for pipeline management.
"""

import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def clean_data(clean_pdfs=True, clean_texts=True, clean_cache=True, clean_medium=True, clean_substack=True, clean_youtube=True):
    """
    Clean data directories by removing files
    
    Args:
        clean_pdfs: Whether to clean the PDFs directory
        clean_texts: Whether to clean the texts directory
        clean_cache: Whether to clean the cache directory
        clean_medium: Whether to clean the Medium texts directory
        clean_substack: Whether to clean the Substack texts directory
        clean_youtube: Whether to clean the YouTube texts directory
    
    Returns:
        dict: Count of files removed from each directory
    """
    base_dir = Path("./data")
    results = {'pdfs': 0, 'texts': 0, 'cache': 0, 'medium': 0, 'substack': 0, 'youtube': 0}
    
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
    
    # Handle Substack files specifically
    if clean_substack:
        substack_dir = base_dir / "texts" / "substack"
        if substack_dir.exists():
            file_count = len(list(substack_dir.glob("*")))
            for file_path in substack_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            results['substack'] = file_count
            logger.info(f"Removed {file_count} Substack files from {substack_dir}")
    
    # Handle YouTube files specifically
    if clean_youtube:
        youtube_dir = base_dir / "texts" / "youtube"
        if youtube_dir.exists():
            file_count = len(list(youtube_dir.glob("*")))
            for file_path in youtube_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            results['youtube'] = file_count
            logger.info(f"Removed {file_count} YouTube files from {youtube_dir}")
    
    if clean_cache:
        cache_dir = base_dir / "cache"
        if cache_dir.exists():
            file_count = 0
            # Clean all cache files recursively
            for file_path in cache_dir.glob("**/*"):
                if file_path.is_file():
                    file_path.unlink()
                    file_count += 1
            
            # Clean specific cache directories
            directories_to_clean = []
            
            # Medium discovery cache
            if clean_medium:
                directories_to_clean.append("medium_discovery")
            
            # Substack cache
            if clean_substack:
                directories_to_clean.append("substack")
            
            # YouTube cache
            if clean_youtube:
                directories_to_clean.append("youtube")
            
            for dir_name in directories_to_clean:
                specific_cache_dir = cache_dir / dir_name
                if specific_cache_dir.exists() and specific_cache_dir.is_dir():
                    shutil.rmtree(specific_cache_dir)
                    logger.info(f"Removed {dir_name} cache directory")
            
            results['cache'] = file_count
            logger.info(f"Removed {file_count} files from cache directories")
    
    return results 