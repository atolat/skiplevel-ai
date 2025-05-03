"""Content extraction and cleaning functions."""
import re
import time
import logging
import requests
from typing import List, Dict
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def scrape_url_content(url: str) -> Dict:
    """Scrape content from a URL using BeautifulSoup with improved error handling."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        }
        
        # Try with a longer timeout and retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add a small delay between retries
                if attempt > 0:
                    time.sleep(2 ** attempt)  # Exponential backoff
                
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=15,
                    allow_redirects=True
                )
                
                # Check if we got a 403 but with content (some sites return content with 403)
                if response.status_code == 403 and response.text:
                    print(f"Got 403 but content available for {url}")
                    break
                
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                print(f"Retry {attempt + 1}/{max_retries} for {url}")
                continue
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script, style, and other non-content elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            element.decompose()
            
        # Get title
        title = soup.title.string if soup.title else ""
        
        # Get main content - try to find the main article content
        main_content = (
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', class_=re.compile(r'content|article|post|main', re.I)) or
            soup.find('div', id=re.compile(r'content|article|post|main', re.I))
        )
        
        if main_content:
            text = ' '.join(main_content.stripped_strings)
        else:
            # If no main content found, try to get the body content
            body = soup.find('body')
            if body:
                text = ' '.join(body.stripped_strings)
            else:
                text = ' '.join(soup.stripped_strings)
        
        return {
            "title": title,
            "text": text,
            "error": None
        }
    except Exception as e:
        return {
            "title": "",
            "text": "",
            "error": str(e)
        }


def extract_reddit_content(reddit_data: Dict) -> Dict:
    """Extract content from Reddit post data."""
    title = reddit_data.get("title", "")
    selftext = reddit_data.get("selftext", "")
    comments = reddit_data.get("comments", [])
    
    # Combine post text and comments
    combined_text = f"{title}\n\n{selftext}\n\n"
    
    # Add comments
    if comments:
        combined_text += "Top comments:\n\n"
        for i, comment in enumerate(comments, 1):
            combined_text += f"Comment {i}:\n{comment}\n\n"
    
    return {
        "title": title,
        "text": combined_text,
        "error": None
    }


def extract_and_clean(urls: List[Dict]) -> List[Dict]:
    """Extract and clean content from URLs."""
    cleaned = []
    for entry in urls:
        # Handle Reddit posts differently
        if entry.get("source", "").startswith("reddit_"):
            if "reddit_data" in entry:
                content = extract_reddit_content(entry["reddit_data"])
            else:
                # Fallback to regular scraping if no Reddit data
                content = scrape_url_content(entry["url"])
        else:
            # Regular web scraping for non-Reddit URLs
            content = scrape_url_content(entry["url"])
            
        if content["error"]:
            logger.warning(f"Error processing {entry['url']}: {content['error']}")
            continue
            
        cleaned.append({
            "url": entry["url"],
            "title": content["title"],
            "text": content["text"][:3000],  # Truncated text for evaluation
            "full_text": content["text"],    # Full text for chunking and embedding
            "source": entry.get("source", "web")
        })
    return cleaned 