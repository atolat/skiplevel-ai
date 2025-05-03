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
    
    args = parser.parse_args()
    
    # Run the pipeline
    results = run_content_pipeline(args.query, args.evaluation_method)
    print(f"\nPipeline completed. Check data directory for results and pipeline.log for detailed logs.")

if __name__ == "__main__":
    main() 