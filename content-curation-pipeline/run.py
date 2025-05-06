#!/usr/bin/env python3
"""
Run the content curation pipeline with command-line arguments.
"""

import argparse
import json
import os
import sys
from dotenv import load_dotenv
from src.pipeline import run_content_pipeline, DEFAULT_QUERY, DEFAULT_EVALUATION_METHOD
from src.pipeline.modules.utils import clean_data

# Load environment variables from .env file
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Run the content curation pipeline")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Content query to search for")
    parser.add_argument(
        "--evaluation-method", 
        default=DEFAULT_EVALUATION_METHOD,
        choices=["standard", "openai_browsing", "tavily_content", "claude_browsing"],
        help="Method for evaluating content"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable URL and content caching (forces reprocessing of all URLs)"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Optional file to save results JSON (defaults to data/results_{timestamp}.json)"
    )
    parser.add_argument(
        "--no-books",
        action="store_true",
        help="Disable discovery of books, papers and other curated resources"
    )
    parser.add_argument(
        "--github-token",
        type=str,
        help="GitHub API token for accessing repositories (optional)"
    )
    parser.add_argument(
        "--medium-api-key",
        type=str,
        help="Medium API key from RapidAPI for accessing Medium content (optional)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean data directories (pdfs, texts, cache) before running the pipeline"
    )
    parser.add_argument(
        "--clean-pdfs",
        action="store_true",
        help="Clean only the PDFs directory before running"
    )
    parser.add_argument(
        "--clean-texts",
        action="store_true",
        help="Clean only the texts directory before running"
    )
    parser.add_argument(
        "--clean-cache",
        action="store_true",
        help="Clean only the cache directory before running"
    )
    parser.add_argument(
        "--clean-medium",
        action="store_true",
        help="Clean only the Medium texts directory before running"
    )
    
    args = parser.parse_args()
    
    # Set GitHub token if provided
    if args.github_token:
        os.environ["GITHUB_TOKEN"] = args.github_token
    
    # Set Medium API key if provided
    if args.medium_api_key:
        os.environ["MEDIUM_API_KEY"] = args.medium_api_key
    
    # Clean data directories if requested
    if args.clean or args.clean_pdfs or args.clean_texts or args.clean_cache or args.clean_medium:
        # If specific clean flags are set, use those
        if args.clean_pdfs or args.clean_texts or args.clean_cache or args.clean_medium:
            results = clean_data(
                clean_pdfs=args.clean_pdfs,
                clean_texts=args.clean_texts,
                clean_cache=args.clean_cache,
                clean_medium=args.clean_medium
            )
        # Otherwise clean everything
        else:
            results = clean_data()
            
        print(f"Cleaned data directories: PDFs: {results['pdfs']} files, " 
              f"Texts: {results['texts']} files, Cache: {results['cache']} files, "
              f"Medium: {results['medium']} files")
    
    # Run the pipeline with cache enabled by default (disabled if --no-cache flag is used)
    # and book discovery enabled by default (disabled if --no-books flag is used)
    results = run_content_pipeline(
        query=args.query, 
        evaluation_method=args.evaluation_method, 
        use_cache=not args.no_cache,
        include_books=not args.no_books
    )
    
    # Save results to file if specified
    if args.output_file:
        os.makedirs(os.path.dirname(os.path.abspath(args.output_file)), exist_ok=True)
        with open(args.output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output_file}")
    
    print(f"\nPipeline completed. Check data directory for results and pipeline.log for detailed logs.")
    print(f"Processed {results['total_urls']} URLs ({results['new_urls_processed']} new, {results['cached_urls_used']} from cache)")
    
    if not args.no_books:
        print(f"Discovered resources: {results['discovered_resources']}")
        
    print(f"Found {results['high_quality_count']}/{results['evaluated_urls']} high-quality results ({results['quality_ratio']:.2f}%)")
    print(f"Average score: {results['average_score']:.2f}")
    print(f"Total runtime: {results['runtime_seconds']:.1f} seconds")

if __name__ == "__main__":
    main() 