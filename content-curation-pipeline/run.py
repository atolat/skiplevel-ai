#!/usr/bin/env python
"""
Content Curation Pipeline Runner

This script runs the content curation pipeline with command-line arguments.
"""

import argparse
import logging
import sys
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
    parser = argparse.ArgumentParser(description='Run content curation pipeline')
    
    # Main arguments
    parser.add_argument('--query', type=str, help='Search query for content discovery')
    parser.add_argument('--limit', type=int, default=None, help='Limit per source (overrides config)')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--data-dir', type=str, help='Data directory (overrides config)')
    
    # Flags
    parser.add_argument('--clean', action='store_true', help='Clean cache before running')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--no-eval', action='store_true', help='Disable content evaluation')
    parser.add_argument('--parallel', action='store_true', help='Enable parallel processing of sources')
    parser.add_argument('--dual-eval', action='store_true', help='Use dual perspective evaluation (engineering manager and staff engineer)')
    parser.add_argument('--parallel-eval', action='store_true', help='Enable parallel processing for evaluations')
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Set up logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create data directory if specified
        data_dir = Path(args.data_dir) if args.data_dir else None
        
        # Initialize pipeline with configuration
        logger.info("Initializing content curation pipeline...")
        pipeline = ContentPipeline(
            config_path=args.config,
            data_dir=data_dir
        )
        
        # Configure evaluation settings
        if args.no_eval and pipeline.config.evaluation.enabled:
            logger.info("Disabling content evaluation as requested")
            pipeline.config.evaluation.enabled = False
        elif args.dual_eval and pipeline.config.evaluation.enabled:
            logger.info("Enabling dual perspective evaluation")
            pipeline.config.evaluation.method = "dual_perspective"
            
        # Track if we're using parallel evaluation
        parallel_eval = args.parallel_eval
        if parallel_eval:
            logger.info("Using parallel processing for evaluations")
            
        # Clean cache if requested
        if args.clean:
            logger.info("Cleaning cache...")
            for source_dir in pipeline.cache_dir.glob('*'):
                if source_dir.is_dir():
                    for cache_file in source_dir.glob('*.json'):
                        logger.debug(f"Removing cache file: {cache_file}")
                        cache_file.unlink()
        
        # Run pipeline
        logger.info(f"Running pipeline with query: {args.query or 'using config seed queries'}")
        if args.parallel:
            logger.info("Using parallel processing mode for discovery")
        results = pipeline.run(
            query=args.query,
            limit_per_source=args.limit,
            parallel=args.parallel,
            parallel_eval=args.parallel_eval
        )
        
        # Log results
        if "error" in results:
            logger.error(f"Pipeline error: {results['error']}")
            return 1
            
        logger.info(f"Pipeline completed in {results['runtime_seconds']:.2f} seconds")
        logger.info(f"Items discovered: {len(results['items'])}")
        logger.info(f"Items processed: {results['stats']['processed_items']}")
        logger.info(f"Failed items: {results['stats']['failed_items']}")
        
        # Log source-specific stats
        logger.info("Source statistics:")
        for source_id, stats in results['stats']['source_stats'].items():
            if stats.get('processed_count', 0) > 0:
                logger.info(f"- {source_id}: processed_count: {stats.get('processed_count', 0)}, "
                           f"error_count: {stats.get('error_count', 0)}, "
                           f"total_words: {stats.get('total_words', 0)}, "
                           f"average_words: {stats.get('average_words', 0):.1f}")
        
        # Print visualization path if available
        if "visualization_path" in results:
            logger.info(f"Visualization saved to: {results['visualization_path']}")
            
        # Print evaluation stats if available
        if "evaluations" in results and results["evaluations"]:
            eval_count = len(results["evaluations"])
            
            if pipeline.config.evaluation.method == "dual_perspective":
                # For dual perspective, we have manager and staff scores
                avg_manager_score = sum(e.get("raw_evaluation", {}).get("manager_score", 0) for e in results["evaluations"]) / eval_count if eval_count > 0 else 0
                avg_staff_score = sum(e.get("raw_evaluation", {}).get("staff_score", 0) for e in results["evaluations"]) / eval_count if eval_count > 0 else 0
                avg_score = sum(e.get("evaluation", {}).get("score", 0) for e in results["evaluations"]) / eval_count if eval_count > 0 else 0
                
                logger.info(f"Evaluated {eval_count} items with:")
                logger.info(f"  - Average Manager Score: {avg_manager_score:.2f}/10")
                logger.info(f"  - Average Staff Engineer Score: {avg_staff_score:.2f}/10")
                logger.info(f"  - Overall Average Score: {avg_score:.2f}/10")
            else:
                # Standard evaluation
                avg_score = sum(e.get("evaluation", {}).get("score", 0) for e in results["evaluations"]) / eval_count if eval_count > 0 else 0
                logger.info(f"Evaluated {eval_count} items with average score: {avg_score:.2f}/10")
            
        return 0
        
    except Exception as e:
        logger.error(f"Error running pipeline: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main()) 