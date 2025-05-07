#!/usr/bin/env python
"""
Clean the cache directories for the content curation pipeline.

This script removes all cached data from the cache directory,
all processed content, and exported visualizations,
allowing for a completely fresh run of the pipeline.
"""

import argparse
import logging
import sys
from pathlib import Path
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Clean cache and content directories for the content curation pipeline')
    
    parser.add_argument('--data-dir', type=str, default='./data',
                        help='Base data directory (default: ./data)')
    parser.add_argument('--keep-pdfs', action='store_true',
                        help='Keep downloaded PDF files')
    parser.add_argument('--keep-content', action='store_true',
                        help='Keep processed content files')
    parser.add_argument('--keep-exports', action='store_true',
                        help='Keep exported visualizations')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    return parser.parse_args()


def clean_cache_directories(data_dir: Path, keep_pdfs: bool = False, 
                           keep_content: bool = False, keep_exports: bool = False,
                           verbose: bool = False):
    """
    Clean all cache and content directories.
    
    Args:
        data_dir: Base data directory
        keep_pdfs: If True, keep downloaded PDF files
        keep_content: If True, keep processed content files
        keep_exports: If True, keep exported visualizations
        verbose: If True, log detailed information
    """
    # Make sure data directory exists
    if not data_dir.exists():
        logger.info(f"Data directory does not exist: {data_dir}")
        return
    
    # Clean the cache directory
    cache_dir = data_dir / "cache"
    if cache_dir.exists():
        logger.info(f"Cleaning cache directory: {cache_dir}")
        cache_count = 0
        
        for source_dir in cache_dir.glob('*'):
            if source_dir.is_dir():
                for cache_file in source_dir.glob('*.json'):
                    if verbose:
                        logger.info(f"Removing cache file: {cache_file}")
                    cache_file.unlink()
                    cache_count += 1
                    
        logger.info(f"Removed {cache_count} cache files")
    
    # Clean the PDF directory if requested
    if not keep_pdfs:
        pdf_dir = data_dir / "pdfs"
        if pdf_dir.exists():
            logger.info(f"Cleaning PDF directory: {pdf_dir}")
            pdf_count = 0
            
            for pdf_file in pdf_dir.glob('*.pdf'):
                if verbose:
                    logger.info(f"Removing PDF file: {pdf_file}")
                pdf_file.unlink()
                pdf_count += 1
                
            logger.info(f"Removed {pdf_count} PDF files")
    
    # Clean the content directory if requested
    if not keep_content:
        content_dir = data_dir / "content"
        if content_dir.exists():
            logger.info(f"Cleaning content directory: {content_dir}")
            
            try:
                # Instead of removing individual files, which could be numerous,
                # remove and recreate the entire directory
                shutil.rmtree(content_dir)
                content_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Cleaned content directory")
            except Exception as e:
                logger.error(f"Error cleaning content directory: {str(e)}")
    
    # Clean the exports directory if requested
    if not keep_exports:
        # Check both possible export directory names
        for export_dir_name in ["exports", "output"]:
            export_dir = data_dir / export_dir_name
            if export_dir.exists():
                logger.info(f"Cleaning {export_dir_name} directory: {export_dir}")
                
                try:
                    # Remove and recreate the entire directory
                    shutil.rmtree(export_dir)
                    export_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Cleaned {export_dir_name} directory")
                except Exception as e:
                    logger.error(f"Error cleaning {export_dir_name} directory: {str(e)}")
    
    # Clean the stats directory
    stats_dir = data_dir / "stats"
    if stats_dir.exists():
        logger.info(f"Cleaning stats directory: {stats_dir}")
        
        try:
            shutil.rmtree(stats_dir)
            stats_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Cleaned stats directory")
        except Exception as e:
            logger.error(f"Error cleaning stats directory: {str(e)}")
    
    logger.info("Cleaning completed successfully")


def main():
    """Main entry point."""
    args = parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        data_dir = Path(args.data_dir)
        clean_cache_directories(
            data_dir, 
            args.keep_pdfs,
            args.keep_content,
            args.keep_exports,
            args.verbose
        )
        return 0
        
    except Exception as e:
        logger.error(f"Error cleaning directories: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main()) 