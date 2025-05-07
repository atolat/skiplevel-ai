#!/usr/bin/env python
"""
Test script for content curation pipeline with dual perspective evaluation.

This script runs the pipeline with dual perspective evaluation enabled.
"""

import argparse
import logging
import json
from pathlib import Path

from src.pipeline.pipeline import ContentPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Test dual perspective evaluation in pipeline')
    
    # Arguments
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to configuration file')
    parser.add_argument('--url', type=str, help='Single URL to evaluate')
    parser.add_argument('--file', type=str, help='JSON file with URLs to evaluate')
    parser.add_argument('--output', type=str, default='pipeline_dual_eval_results.json', help='Output file for results')
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        # Initialize pipeline with dual perspective evaluation
        logger.info("Initializing pipeline with dual perspective evaluation...")
        pipeline = ContentPipeline(config_path=args.config)
        
        # Enable evaluation with dual perspective method
        pipeline.config.evaluation.enabled = True
        pipeline.config.evaluation.method = "dual_perspective"
        
        if args.url:
            # Evaluate a single URL
            logger.info(f"Evaluating single URL: {args.url}")
            
            # Create a minimal content item for evaluation
            from src.pipeline.interfaces import ContentItem, ContentMetadata
            
            item = ContentItem(
                id="manual_id",
                url=args.url,
                title="Manual URL Evaluation",
                description="",
                authors=[],
                publish_date=None,
                metadata=ContentMetadata(
                    source_type="web",
                    content_type="article",
                    source_quality=5.0,
                    is_curated=False,
                    source_name="Web",
                    additional_meta={}
                ),
                text_path=None,
                raw_data={}
            )
            
            # Evaluate the item
            results = pipeline.evaluate_content([item])
            
        elif args.file:
            # Evaluate URLs from file
            file_path = Path(args.file)
            if not file_path.exists():
                logger.error(f"File not found: {args.file}")
                return 1
                
            logger.info(f"Loading URLs from {args.file}")
            with open(file_path, 'r') as f:
                urls_data = json.load(f)
                
            # Create content items from URLs
            from src.pipeline.interfaces import ContentItem, ContentMetadata
            
            items = []
            for idx, data in enumerate(urls_data):
                url = data["url"]
                title = data.get("title", f"URL {idx+1}")
                source_type = data.get("source", "web")
                
                item = ContentItem(
                    id=f"file_id_{idx}",
                    url=url,
                    title=title,
                    description="",
                    authors=[],
                    publish_date=None,
                    metadata=ContentMetadata(
                        source_type=source_type,
                        content_type="article",
                        source_quality=5.0,
                        is_curated=False,
                        source_name=source_type.capitalize(),
                        additional_meta={}
                    ),
                    text_path=None,
                    raw_data={}
                )
                items.append(item)
                
            # Evaluate the items
            logger.info(f"Evaluating {len(items)} URLs...")
            results = pipeline.evaluate_content(items)
            
        else:
            logger.error("Please provide either a URL or a file with URLs to evaluate")
            return 1
            
        # Save results to file
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Results saved to {output_path}")
        
        # Print a summary
        logger.info("Evaluation Summary:")
        for idx, result in enumerate(results, 1):
            logger.info(f"{idx}. {result.get('title', 'Unknown')}")
            logger.info(f"   URL: {result.get('url', 'Unknown')}")
            logger.info(f"   Score: {result.get('evaluation', {}).get('score', 0):.1f}/10")
            logger.info(f"   Summary: {result.get('evaluation', {}).get('summary', 'N/A')}")
            logger.info(f"   Reasoning: {result.get('evaluation', {}).get('reasoning', 'N/A')}")
            logger.info("")
            
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main()) 