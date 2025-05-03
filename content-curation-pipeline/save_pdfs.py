#!/usr/bin/env python
"""
Helper script to save PDF files from the processed resource cache.
This is useful for retrieving PDFs that were processed in previous pipeline runs.
"""

import logging
import os
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pdf_saver')

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

# Import the function to save PDFs
from src.pipeline.modules.resource_processor import save_cached_pdfs

if __name__ == "__main__":
    logger.info("Starting PDF saving process...")
    count = save_cached_pdfs()
    logger.info(f"Saved {count} PDFs. Check the data/pdfs directory for the files.")
    logger.info("PDF saving process complete.") 