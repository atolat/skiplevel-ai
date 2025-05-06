#!/usr/bin/env python3
"""
Clean script for removing cached data from the content curation pipeline.
"""

import argparse
import logging
from src.pipeline.modules.utils import clean_data

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Clean data directories for the content curation pipeline")
    parser.add_argument(
        "--pdfs-only",
        action="store_true",
        help="Clean only the PDFs directory"
    )
    parser.add_argument(
        "--texts-only",
        action="store_true",
        help="Clean only the texts directory"
    )
    parser.add_argument(
        "--cache-only",
        action="store_true",
        help="Clean only the cache directory"
    )
    parser.add_argument(
        "--medium-only",
        action="store_true",
        help="Clean only the Medium texts directory"
    )
    
    args = parser.parse_args()
    
    # If specific flags are set, clean only those directories
    if args.pdfs_only or args.texts_only or args.cache_only or args.medium_only:
        clean_pdfs = args.pdfs_only
        clean_texts = args.texts_only
        clean_cache = args.cache_only
        clean_medium = args.medium_only
    else:
        # Default: clean everything
        clean_pdfs = clean_texts = clean_cache = clean_medium = True
    
    results = clean_data(
        clean_pdfs=clean_pdfs,
        clean_texts=clean_texts,
        clean_cache=clean_cache,
        clean_medium=clean_medium
    )
    
    print(f"Cleaned data directories: ")
    print(f"- PDFs: {results['pdfs']} files")
    print(f"- Texts: {results['texts']} files") 
    print(f"- Cache: {results['cache']} files")
    print(f"- Medium: {results['medium']} files")

if __name__ == "__main__":
    main() 