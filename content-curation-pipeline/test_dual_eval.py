#!/usr/bin/env python
"""
Test script for dual perspective evaluation.

This script demonstrates the dual perspective evaluation on a few sample articles.
"""

import json
import argparse
import logging
from pathlib import Path
from src.pipeline.modules.dual_perspective_evaluation import dual_perspective_evaluation, batch_evaluate_urls

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Test dual perspective content evaluation')
    
    # Arguments
    parser.add_argument('--url', type=str, help='URL to evaluate (single mode)')
    parser.add_argument('--file', type=str, help='JSON file with URLs to evaluate (batch mode)')
    parser.add_argument('--output', type=str, default='dual_eval_results.json', help='Output file for results')
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Ensure we have either a URL or a file
    if not args.url and not args.file:
        logger.error("Please provide either a URL to evaluate or a file with URLs")
        return 1
    
    try:
        # Set up output file
        output_file = Path(args.output)
        
        if args.url:
            # Single URL evaluation
            logger.info(f"Evaluating single URL: {args.url}")
            result = dual_perspective_evaluation(args.url)
            results = [result]
            
        else:
            # Batch evaluation
            url_file = Path(args.file)
            if not url_file.exists():
                logger.error(f"File not found: {args.file}")
                return 1
                
            logger.info(f"Loading URLs from {args.file}")
            with open(url_file, 'r') as f:
                urls = json.load(f)
                
            # Ensure we have a valid list
            if not isinstance(urls, list):
                logger.error("File must contain a JSON array of URL objects")
                return 1
                
            logger.info(f"Evaluating {len(urls)} URLs...")
            results = batch_evaluate_urls(urls)
        
        # Save results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Results saved to {output_file}")
        
        # Print a summary
        logger.info("Evaluation Summary:")
        for i, result in enumerate(results, 1):
            logger.info(f"{i}. {result.get('title', 'Unknown')}")
            logger.info(f"   URL: {result.get('url', 'Unknown')}")
            logger.info(f"   Manager Score: {result.get('manager_score', 0):.1f}/10")
            logger.info(f"   Staff Score: {result.get('staff_score', 0):.1f}/10")
            logger.info(f"   Average Score: {result.get('avg_score', 0):.1f}/10")
            logger.info(f"   Manager Summary: {result.get('manager_evaluation', {}).get('summary', 'N/A')}")
            logger.info(f"   Staff Summary: {result.get('staff_evaluation', {}).get('summary', 'N/A')}")
            logger.info("")
            
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return 1

if __name__ == '__main__':
    exit(main()) 