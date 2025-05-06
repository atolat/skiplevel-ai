#!/usr/bin/env python
"""
Cleanup script for migrating existing resource cache to use file-based text storage.

This script will:
1. Read the existing processed resources from the JSON cache
2. For each resource with inline text content, move that content to separate text files
3. Update the cache with references to these files
"""

import logging
import os
import sys
import json
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('storage_cleanup')

# Import the resource processor functions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '')))
from src.pipeline.modules.resource_processor import (
    PROCESSED_CACHE_FILE, TEXT_DIR, save_text_content, get_resource_key
)

def clean_storage():
    """
    Migrate text content from JSON cache to separate text files.
    """
    logger.info("Starting storage cleanup process...")
    
    # Create text directory if needed
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load the existing cache
    if not PROCESSED_CACHE_FILE.exists():
        logger.warning(f"No cache file found at {PROCESSED_CACHE_FILE}")
        return
    
    try:
        with open(PROCESSED_CACHE_FILE, 'r') as f:
            cache = json.load(f)
        logger.info(f"Loaded {len(cache)} resources from cache")
    except Exception as e:
        logger.error(f"Error loading cache: {str(e)}")
        return
    
    # Track statistics
    migrated_count = 0
    already_migrated_count = 0
    error_count = 0
    
    # Process each resource
    for key, resource in cache.items():
        try:
            # Skip resources that already have a text_path
            if "text_path" in resource:
                if os.path.exists(resource["text_path"]):
                    logger.debug(f"Resource {key} already migrated to {resource['text_path']}")
                    already_migrated_count += 1
                    continue
                logger.warning(f"Resource {key} has text_path but file doesn't exist: {resource['text_path']}")
            
            # Skip resources that don't have text content
            if "text" not in resource:
                logger.debug(f"Resource {key} has no text content to migrate")
                continue
            
            # Extract the text and save to file
            text = resource.pop("text")  # Remove text from resource
            text_path = save_text_content(text, key)
            
            # Update the resource with the text path
            resource["text_path"] = text_path
            cache[key] = resource
            
            migrated_count += 1
            logger.debug(f"Migrated resource {key} text to {text_path}")
            
        except Exception as e:
            logger.error(f"Error migrating resource {key}: {str(e)}")
            error_count += 1
    
    # Save the updated cache
    try:
        with open(PROCESSED_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
        logger.info(f"Saved updated cache with {len(cache)} resources")
    except Exception as e:
        logger.error(f"Error saving updated cache: {str(e)}")
        return
    
    # Log summary
    logger.info(f"Storage cleanup complete:")
    logger.info(f"  - Migrated {migrated_count} resources to text files")
    logger.info(f"  - {already_migrated_count} resources were already migrated")
    logger.info(f"  - {error_count} errors encountered")
    logger.info(f"Text files are stored in {TEXT_DIR}")

if __name__ == "__main__":
    clean_storage() 