#!/usr/bin/env python3
"""
Test script for Medium API integration.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from src.pipeline.modules import medium_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_medium_api(test_type="topic", topic="software-engineering", api_key=None, save=False):
    """
    Test the Medium API integration by fetching articles.
    
    Args:
        test_type: Type of test to run (user, topic, validation)
        topic: Topic to search for (if test_type is topic)
        api_key: API key to use (optional, will use environment variable if not provided)
        save: Whether to save results to file
    """
    # Set API key if provided
    if api_key:
        os.environ["MEDIUM_API_KEY"] = api_key
        
    # Check if API key is available
    if not os.environ.get("MEDIUM_API_KEY"):
        logger.error("MEDIUM_API_KEY not found in environment variables.")
        return
        
    if test_type == "validation":
        # Test URL validation
        test_urls = [
            # Valid article URLs
            "https://medium.com/@username/article-title-123456789abc",
            "https://medium.com/publication-name/article-title-123456789abc",
            "https://medium.com/p/123456789abc",
            
            # Invalid URLs - profiles and publications
            "https://medium.com/@username",
            "https://medium.com/publication-name",
            "https://medium.com/publication-name/tagged/technology",
            "https://medium.com/publication-name/archive",
            "https://medium.com/publication-name/latest",
            "https://medium.com/topics",
            "https://medium.com/membership",
        ]
        
        logger.info("Testing URL validation...")
        results = {}
        
        for url in test_urls:
            is_valid = medium_api.is_valid_article_url(url)
            results[url] = is_valid
            logger.info(f"URL: {url} - Valid: {is_valid}")
        
        if save:
            with open("medium_url_validation_results.json", "w") as f:
                json.dump(results, f, indent=2)
            logger.info("Saved validation results to medium_url_validation_results.json")
            
        return
    
    # List to store detailed articles
    detailed_articles = []
    headers = medium_api.get_medium_api_headers()
    
    if test_type == "user":
        # Test user endpoint
        user_id = "3a8aa3e9806d"  # Will Larson (StaffEng author)
        logger.info(f"Testing user endpoint with user_id: {user_id}")
        
        try:
            # Get user info
            user_info = medium_api.get_user_info(user_id)
            if user_info:
                logger.info(f"User found: {user_info.get('name')} (@{user_info.get('username')})")
                
                # Get user articles
                article_ids = medium_api.get_user_articles(user_id)
                logger.info(f"Found {len(article_ids)} articles from user {user_id}")
                
                for article_id in article_ids:
                    article_info = medium_api.get_article_info(article_id)
                    if article_info:
                        article_content = medium_api.get_article_content(article_id)
                        if article_content:
                            detailed_articles.append({
                                "id": article_id,
                                "title": article_info.get("title"),
                                "url": article_info.get("url"),
                                "content": article_content,
                                "text": medium_api.extract_text_from_html(article_content)
                            })
            else:
                logger.error(f"User {user_id} not found")
        except Exception as e:
            logger.error(f"Error testing user endpoint: {str(e)}")
    
    elif test_type == "topic":
        logger.info(f"Testing topic endpoints with topic: {topic}")
        
        # Try different modes for topfeeds
        for mode in ["hot", "new", "top_month"]:
            try:
                logger.info(f"Trying topfeeds/{topic}/{mode}")
                article_ids = medium_api.get_topfeeds_articles(topic, mode)
                if article_ids:
                    logger.info(f"Success! Found {len(article_ids)} articles with mode '{mode}'")
                    
                    # Get article info and content for the first few articles
                    for article_id in article_ids[:3]:
                        article_info = medium_api.get_article_info(article_id)
                        if article_info:
                            article_content = medium_api.get_article_content(article_id)
                            if article_content:
                                detailed_articles.append({
                                    "id": article_id,
                                    "title": article_info.get("title"),
                                    "url": article_info.get("url"),
                                    "content": article_content,
                                    "text": medium_api.extract_text_from_html(article_content)
                                })
                else:
                    logger.warning(f"No articles found for topfeeds/{topic}/{mode}")
            except Exception as e:
                logger.error(f"Error with topfeeds/{topic}/{mode}: {str(e)}")
        
        # If we didn't get articles from topfeeds, try recommended feed
        if not detailed_articles:
            try:
                logger.info(f"Trying recommended_feed/{topic}")
                article_ids = medium_api.get_recommended_feed_articles(topic)
                if article_ids:
                    logger.info(f"Success! Found {len(article_ids)} articles from recommended feed")
                    
                    # Get article info and content for the first few articles
                    for article_id in article_ids[:3]:
                        article_info = medium_api.get_article_info(article_id)
                        if article_info:
                            article_content = medium_api.get_article_content(article_id)
                            if article_content:
                                detailed_articles.append({
                                    "id": article_id,
                                    "title": article_info.get("title"),
                                    "url": article_info.get("url"),
                                    "content": article_content,
                                    "text": medium_api.extract_text_from_html(article_content)
                                })
            except Exception as e:
                logger.error(f"Error with recommended_feed/{topic}: {str(e)}")
        
        # If we still don't have articles, try search
        if not detailed_articles:
            try:
                logger.info(f"Trying search for '{topic}'")
                article_ids = medium_api.search_articles(topic)
                if article_ids:
                    logger.info(f"Success! Found {len(article_ids)} articles from search")
                    
                    # Get article info and content for the first few articles
                    for article_id in article_ids[:3]:
                        article_info = medium_api.get_article_info(article_id)
                        if article_info:
                            article_content = medium_api.get_article_content(article_id)
                            if article_content:
                                detailed_articles.append({
                                    "id": article_id,
                                    "title": article_info.get("title"),
                                    "url": article_info.get("url"),
                                    "content": article_content,
                                    "text": medium_api.extract_text_from_html(article_content)
                                })
            except Exception as e:
                logger.error(f"Error with search: {str(e)}")
    
    # Save results if requested
    if save and detailed_articles:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"medium_api_test_{test_type}_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(detailed_articles, f, indent=2)
        logger.info(f"Saved {len(detailed_articles)} articles to {filename}")
        
        # Save a sample of the first article's text
        if detailed_articles and "text" in detailed_articles[0]:
            sample_filename = f"medium_api_text_sample_{timestamp}.txt"
            with open(sample_filename, "w") as f:
                f.write(detailed_articles[0]["text"])
            logger.info(f"Saved text sample to {sample_filename}")

def main():
    parser = argparse.ArgumentParser(description="Test Medium API integration")
    parser.add_argument("--test-type", choices=["user", "topic", "validation"], default="topic", help="Type of test to run")
    parser.add_argument("--topic", default="software-engineering", help="Topic to search for (if test-type is topic)")
    parser.add_argument("--api-key", help="API key to use (optional)")
    parser.add_argument("--save", action="store_true", help="Save results to file")
    
    args = parser.parse_args()
    test_medium_api(args.test_type, args.topic, args.api_key, args.save)

if __name__ == "__main__":
    main() 