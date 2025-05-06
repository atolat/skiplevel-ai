#!/usr/bin/env python3
"""
Medium content discovery runner script.

This script provides a command-line interface to discover and extract content from Medium
using multiple discovery strategies, with an emphasis on high-quality articles.
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
src_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(src_dir))

from src.pipeline.modules import medium_discovery


def main():
    """Main entry point for the Medium discovery script."""
    parser = argparse.ArgumentParser(description="Discover and extract content from Medium")
    parser.add_argument("query", help="The query to search for Medium articles")
    parser.add_argument("--max-articles", type=int, default=30, 
                        help="Maximum number of articles to retrieve (default: 30)")
    parser.add_argument("--strategies", nargs="+", 
                        choices=["topfeeds", "recommended", "search", "authors", "publications", "all"],
                        default=["all"],
                        help="Discovery strategies to use (default: all)")
    parser.add_argument("--no-cache", action="store_true", 
                        help="Disable cache for this run (fetch fresh content)")
    parser.add_argument("--output", help="Optional JSON output file for discovered articles")
    
    args = parser.parse_args()
    
    # Check for Medium API key
    if not os.environ.get("MEDIUM_API_KEY"):
        logger.error("MEDIUM_API_KEY not found in environment variables.")
        print("\nError: MEDIUM_API_KEY environment variable is required.")
        print("Please set it in your .env file or environment variables.")
        return 1
    
    print(f"\n🔍 Discovering Medium articles for: {args.query}")
    print(f"Max articles: {args.max_articles}")
    print(f"Strategies: {args.strategies}")
    print("Cache: " + ("Disabled" if args.no_cache else "Enabled"))
    
    # Prepare the strategies
    if "all" in args.strategies:
        strategies = None  # Use all available strategies
    else:
        strategies = args.strategies
    
    start_time = datetime.now()
    
    # Run the discovery process
    try:
        articles = medium_discovery.run_medium_discovery(
            query=args.query,
            max_articles=args.max_articles
        )
        
        # Calculate some stats
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ Discovery complete in {duration:.1f} seconds")
        print(f"Discovered {len(articles)} articles")
        
        if articles:
            # Show statistics
            total_words = sum(len(article.get("text", "").split()) for article in articles)
            avg_words = total_words / len(articles)
            
            print(f"\nTotal content: {total_words:,} words")
            print(f"Average article length: {avg_words:.1f} words")
            
            # Get top articles by engagement
            top_articles = sorted(
                articles, 
                key=lambda x: x.get("meta", {}).get("claps", 0),
                reverse=True
            )[:5]
            
            print("\n📊 Top articles by engagement:")
            for i, article in enumerate(top_articles):
                claps = article.get("meta", {}).get("claps", 0)
                title = article.get("title", "Untitled")
                url = article.get("url", "")
                print(f"{i+1}. {title}")
                print(f"   👏 {claps:,} claps")
                print(f"   🔗 {url}")
                print(f"   📄 {article.get('text_path', 'No text file')}")
                print()
            
            # Save to output file if requested
            if args.output:
                # Remove the large text and HTML content to make the output file smaller
                output_articles = []
                for article in articles:
                    article_copy = {**article}
                    # Keep a sample of the text but not the whole thing
                    if "text" in article_copy:
                        sample_text = article_copy["text"][:500] + "..." if len(article_copy["text"]) > 500 else article_copy["text"]
                        article_copy["text_sample"] = sample_text
                        del article_copy["text"]
                    
                    # Remove the HTML content
                    if "html_content" in article_copy:
                        del article_copy["html_content"]
                        
                    output_articles.append(article_copy)
                
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump({
                        "query": args.query,
                        "timestamp": datetime.now().isoformat(),
                        "article_count": len(articles),
                        "total_words": total_words,
                        "avg_words": avg_words,
                        "articles": output_articles
                    }, f, indent=2)
                
                print(f"\n💾 Saved article metadata to: {args.output}")
        
    except Exception as e:
        logger.exception("Error during Medium discovery")
        print(f"\n❌ Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 