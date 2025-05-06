from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import time

def discover_engineering_blog_articles() -> List[Dict]:
    """
    Discover articles from top engineering blogs focused on management and leadership.
    
    Returns:
        List of article dictionaries
    """
    import concurrent.futures
    from functools import partial
    
    logger.info("Discovering engineering blog articles")
    
    # List of high-quality engineering blogs with leadership content
    blogs = [
        # ... existing blog definitions ...
    ]
    
    # Create a cache key
    cache_key = "engineering_blogs"
    
    # Check cache for recent results (< 3 days old)
    if cache_key in RESOURCE_CACHE:
        cache_time = RESOURCE_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 3 * 24 * 60 * 60:  # 3 days in seconds
            logger.info("Using cached engineering blog results")
            return RESOURCE_CACHE[cache_key].get("results", [])
    
    # Function to process a single blog
    def process_blog(blog):
        try:
            logger.info(f"Fetching articles from {blog['name']}")
            
            response = requests.get(blog["url"], headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.select(blog["selector"])
            
            blog_results = []
            for article in articles[:5]:  # Limit to 5 most recent articles per blog
                try:
                    # Extract title
                    if blog["title_selector"]:
                        title_elem = article.select_one(blog["title_selector"])
                        title = title_elem.text.strip() if title_elem else "Untitled"
                    else:
                        # Use link text as title
                        link_elem = article.select_one(blog["link_selector"])
                        title = link_elem.text.strip() if link_elem else "Untitled"
                    
                    # Extract URL
                    link_elem = article.select_one(blog["link_selector"])
                    if not link_elem:
                        continue
                        
                    url = link_elem.get("href", "")
                    if not url:
                        continue
                        
                    # Handle relative URLs
                    if not blog.get("is_abs_url", True) and not url.startswith(("http://", "https://")):
                        base_url = blog.get("base_url", blog["url"])
                        # Remove trailing slash from base_url if present
                        if base_url.endswith("/") and url.startswith("/"):
                            base_url = base_url[:-1]
                        # Add slash to base_url if needed
                        elif not base_url.endswith("/") and not url.startswith("/"):
                            base_url = base_url + "/"
                        url = base_url + url
                    
                    # Extract description if available
                    description = ""
                    if blog.get("description_selector"):
                        desc_elem = article.select_one(blog["description_selector"])
                        if desc_elem:
                            description = desc_elem.text.strip()
                    
                    article_dict = {
                        "title": title,
                        "url": url,
                        "source": f"blog_{blog['name'].lower().replace(' ', '_')}",
                        "description": description,
                        "meta": {
                            "content_type": "blog_article",
                            "is_curated": True,
                            "source_quality": 8,  # Engineering blogs from top companies
                            "blog_name": blog['name']
                        }
                    }
                    blog_results.append(article_dict)
                    
                except Exception as e:
                    logger.warning(f"Error extracting article from {blog['name']}: {str(e)}")
                    continue
            
            return blog_results
        
        except Exception as e:
            logger.error(f"Error fetching articles from {blog['name']}: {str(e)}")
            return []
    
    # Use parallel processing to fetch from multiple blogs simultaneously
    results = []
    max_workers = min(len(blogs), 8)  # Cap at 8 concurrent requests
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all blogs for processing
        future_to_blog = {executor.submit(process_blog, blog): blog for blog in blogs}
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_blog):
            blog_results = future.result()
            results.extend(blog_results)
    
    # Cache the results
    RESOURCE_CACHE[cache_key] = {
        "timestamp": time.time(),
        "results": results
    }
    save_resource_cache()
    
    logger.info(f"Found {len(results)} engineering blog articles")
    return results 