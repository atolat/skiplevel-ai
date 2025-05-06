"""
Text utility functions for the pipeline.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def save_text_to_file(text: str, file_path: str, ensure_dir: bool = True) -> Optional[str]:
    """
    Save text content to a file.
    
    Args:
        text: The text content to save
        file_path: The path where the file should be saved
        ensure_dir: Whether to create the directory if it doesn't exist
    
    Returns:
        The file path if successful, None otherwise
    """
    try:
        if not text:
            logger.warning(f"No text content to save to {file_path}")
            return None
            
        # Create directory if it doesn't exist
        if ensure_dir:
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
        logger.info(f"Saved text content to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving text to {file_path}: {str(e)}")
        return None
        
def get_text_from_file(file_path: str) -> Optional[str]:
    """
    Read text content from a file.
    
    Args:
        file_path: The path to the file
    
    Returns:
        The file contents as a string, or None if there was an error
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File does not exist: {file_path}")
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        logger.info(f"Read text content from {file_path}")
        return content
    except Exception as e:
        logger.error(f"Error reading text from {file_path}: {str(e)}")
        return None 