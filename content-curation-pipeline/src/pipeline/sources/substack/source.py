"""
Substack content source implementation.
"""

import json
import logging
import re
import time
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from ...interfaces import ContentSource, ContentItem, ContentMetadata

logger = logging.getLogger(__name__)

class SubstackSource(ContentSource):
    """Content source for Substack newsletters."""
    
    # API endpoints
    API_ENDPOINTS = {
        "v1": "/api/v1/posts",
        "v2": "/api/v2/posts",
        "archive": "/archive",
        "feed": "/feed"
    }
    
    # Rate limiting
    MIN_REQUEST_INTERVAL = 1.0  # seconds between requests
    MAX_RETRIES = 3
    
    def __init__(self, cache_dir: Path, output_dir: Path):
        super().__init__(cache_dir, output_dir)
        self.cache_file = self.cache_dir / "substack_cache.json"
        self.cache = self._load_cache()
        self.last_request_time = 0
        
        # High-quality engineering management newsletters (verified active)
        self.curated_newsletters = [
            "pragmaticengineer",  # The Pragmatic Engineer by Gergely Orosz
            "theengineeringmanager",  # The Engineering Manager by James Stanier
            "platocommunity",  # Plato Community - Engineering Leadership Insights
            "bytesized",  # Bytesized by Zach Lloyd
            "techwriting",  # The Tech Writing Newsletter
            "engineeringorg",  # Engineering at Scale
            "techlead",  # TechLead Journal by Pat Kua
        ]
    
    def _load_cache(self) -> Dict:
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading Substack cache: {str(e)}")
        return {}
    
    def _save_cache(self):
        """Save cache to file."""
        try:
            # Convert datetime objects to ISO format strings before saving
            cache_copy = {}
            for key, value in self.cache.items():
                if isinstance(value, dict):
                    cache_copy[key] = {
                        "timestamp": value.get("timestamp"),
                        "data": self._prepare_for_cache(value.get("data", []))
                    }
                else:
                    cache_copy[key] = value
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_copy, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving Substack cache: {str(e)}")
    
    def _prepare_for_cache(self, data: Any) -> Any:
        """Prepare data for JSON serialization."""
        if isinstance(data, list):
            return [self._prepare_for_cache(item) for item in data]
        elif isinstance(data, dict):
            return {k: self._prepare_for_cache(v) for k, v in data.items()}
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data
    
    def _rate_limit(self):
        """Implement rate limiting between requests."""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, retries: int = MAX_RETRIES) -> Optional[requests.Response]:
        """Make a rate-limited request with retries."""
        if not url:
            logger.error("Cannot make request to None URL")
            return None
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        for attempt in range(retries):
            try:
                self._rate_limit()
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt == retries - 1:
                    logger.error(f"Failed to fetch {url} after {retries} attempts: {str(e)}")
                    return None
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
                time.sleep(wait_time)
        return None
    
    def discover(self, query: str, limit: int = 10) -> List[ContentItem]:
        """Discover content from curated Substack newsletters."""
        discovered_items = []
        seen_urls = set()
        
        for subdomain in self.curated_newsletters:
            try:
                posts = self._get_posts(subdomain)
                for post in posts:
                    if len(discovered_items) >= limit:
                        break
                        
                    url = post.get("url") or f"https://{subdomain}.substack.com/p/{post.get('slug')}"
                    if url in seen_urls:
                        continue
                    
                    seen_urls.add(url)
                    
                    # Convert post to ContentItem
                    try:
                        item = self._post_to_content_item(post, subdomain)
                        if item:
                            discovered_items.append(item)
                    except Exception as e:
                        logger.error(f"Error converting post to ContentItem: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error discovering posts from {subdomain}: {str(e)}")
                continue
        
        return discovered_items
    
    def process_url(self, url: str) -> Optional[ContentItem]:
        """Process a single Substack URL."""
        if not self.is_source_url(url):
            return None
            
        try:
            # Extract subdomain and slug from URL
            match = re.match(r'https://([^\.]+)\.substack\.com/p/([^/]+)', url)
            if not match:
                return None
                
            subdomain, slug = match.groups()
            
            # Try to get post data
            post = self._get_post_data(subdomain, slug)
            if not post:
                return None
                
            return self._post_to_content_item(post, subdomain)
            
        except Exception as e:
            logger.error(f"Error processing Substack URL {url}: {str(e)}")
            return None
    
    def is_source_url(self, url: str) -> bool:
        """Check if URL is from Substack."""
        if not url:
            return False
        return bool(re.match(r'https://[^\.]+\.substack\.com/p/[^/]+', url))
    
    def _get_posts(self, subdomain: str) -> List[Dict]:
        """Get posts from a Substack newsletter."""
        cache_key = f"posts_{subdomain}"
        if cache_key in self.cache:
            cache_time = self.cache[cache_key].get("timestamp", 0)
            if time.time() - cache_time < 24 * 60 * 60:  # 24 hours
                return self.cache[cache_key].get("data", [])
        
        posts = []
        base_url = f"https://{subdomain}.substack.com"
        
        # Try different API endpoints
        for endpoint_name, endpoint_path in self.API_ENDPOINTS.items():
            try:
                url = base_url + endpoint_path
                response = self._make_request(url)
                
                if not response:
                    continue
                
                if endpoint_name == "v1" or endpoint_name == "v2":
                    # API endpoints return JSON
                    data = response.json()
                    if isinstance(data, list):
                        posts = data
                        break
                    elif isinstance(data, dict) and "posts" in data:
                        posts = data["posts"]
                        break
                
                elif endpoint_name == "archive":
                    # Parse HTML archive page
                    soup = BeautifulSoup(response.text, "html.parser")
                    post_elements = soup.select("article.post-preview")
                    
                    for element in post_elements:
                        title_elem = element.select_one("h3.post-preview-title")
                        if not title_elem:
                            continue
                            
                        link = element.select_one("a.post-preview-title")
                        if not link:
                            continue
                            
                        url = link.get("href")
                        if not url:
                            continue
                        
                        # Check if the post is paywalled
                        is_paid = False
                        paid_marker = element.select_one(".locked-indicator")
                        if paid_marker:
                            is_paid = True
                            
                        # Create post data structure
                        post = {
                            "id": hashlib.md5(url.encode()).hexdigest(),  # Generate stable ID
                            "title": title_elem.text.strip(),
                            "url": url if url.startswith("http") else base_url + url,
                            "subtitle": element.select_one(".post-preview-description").text.strip() if element.select_one(".post-preview-description") else "",
                            "post_date": element.select_one("time").get("datetime") if element.select_one("time") else None,
                            "is_paid": is_paid
                        }
                        posts.append(post)
                    
                    if posts:
                        break
                
                elif endpoint_name == "feed":
                    # Parse RSS feed
                    feed_data = BeautifulSoup(response.text, "xml")
                    items = feed_data.find_all("item")
                    
                    for item in items:
                        url = item.link.text if item.link else ""
                        post = {
                            "id": hashlib.md5(url.encode()).hexdigest(),  # Generate stable ID
                            "title": item.title.text if item.title else "",
                            "url": url,
                            "subtitle": item.description.text if item.description else "",
                            "post_date": item.pubDate.text if item.pubDate else None
                        }
                        posts.append(post)
                    
                    if posts:
                        break
            
            except Exception as e:
                logger.error(f"Error fetching {endpoint_name} for {subdomain}: {str(e)}")
                continue
        
        if posts:
            # Ensure all posts have naive datetimes and valid IDs
            for post in posts:
                # Handle post_date
                if post.get("post_date"):
                    try:
                        # Parse and convert to naive UTC datetime
                        if isinstance(post["post_date"], str):
                            try:
                                dt = datetime.fromisoformat(post["post_date"].replace("Z", "+00:00"))
                            except ValueError:
                                try:
                                    dt = datetime.strptime(post["post_date"], "%a, %d %b %Y %H:%M:%S %z")
                                except ValueError:
                                    try:
                                        dt = datetime.strptime(post["post_date"], "%Y-%m-%d")
                                        dt = dt.replace(tzinfo=timezone.utc)  # Assume UTC for date-only
                                    except ValueError:
                                        dt = None
                            if dt:
                                post["post_date"] = dt.astimezone(timezone.utc).replace(tzinfo=None)
                            else:
                                post["post_date"] = None
                    except Exception as e:
                        logger.warning(f"Error parsing date {post['post_date']}: {str(e)}")
                        post["post_date"] = None
                
                # Ensure ID is a string
                if "id" not in post or not post["id"]:
                    post["id"] = hashlib.md5(post.get("url", "").encode()).hexdigest()
                post["id"] = str(post["id"])
                
                # Ensure URL is valid
                if "url" not in post or not post["url"]:
                    # Generate URL from slug if available
                    if "slug" in post and post["slug"]:
                        post["url"] = f"https://{subdomain}.substack.com/p/{post['slug']}"
            
            # Cache successful results
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "data": posts
            }
            self._save_cache()
        else:
            logger.warning(f"No posts found for {subdomain} after trying all endpoints")
        
        return posts
    
    def _check_for_paywall(self, soup: BeautifulSoup) -> bool:
        """Check if content is behind a paywall."""
        # Method 1: Look for paywall indicators
        paywall_indicators = [
            ".paywall-indicator", 
            ".locked-indicator", 
            ".locked-content",
            ".paid-content",
            ".subscriber-content",
            ".subscription-only"
        ]
        for indicator in paywall_indicators:
            if soup.select_one(indicator):
                return True
                
        # Method 2: Look for "paid" text or subscription notices
        subscription_patterns = [
            "Subscribe to continue reading",
            "This post is for paid subscribers",
            "This post is for paying subscribers",
            "Subscribe to read",
            "Paid subscribers only",
            "for subscribers only",
            "for paid subscribers"
        ]
        
        text = soup.get_text().lower()
        for pattern in subscription_patterns:
            if pattern.lower() in text:
                return True
                
        # Method 3: Check for "Subscribe to read" button
        subscribe_buttons = soup.select(".subscribe-button, .subscription-button")
        for button in subscribe_buttons:
            button_text = button.get_text().lower()
            if "subscribe" in button_text and ("read" in button_text or "continue" in button_text):
                return True
        
        return False
    
    def _extract_preview_content(self, soup: BeautifulSoup) -> str:
        """Extract preview content from a paywalled article."""
        preview_sections = [
            ".available-content",
            ".preview-content",
            ".public-content",
            ".free-content"
        ]
        
        for section in preview_sections:
            preview = soup.select_one(section)
            if preview:
                return str(preview)
        
        # If no specific preview section, try to get the first few paragraphs
        paragraphs = []
        for p in soup.select("article p"):
            # Skip paragraphs in specific sections
            if p.parent and any(
                p.parent.get("class") and cls in " ".join(p.parent.get("class"))
                for cls in ["subscribe", "paywall", "locked", "cta"]
            ):
                continue
            paragraphs.append(str(p))
            # Limit to first 3 paragraphs as preview
            if len(paragraphs) >= 3:
                break
        
        if paragraphs:
            return "\n".join(paragraphs)
        
        # Last resort: try to get article intro/header if it exists
        intro = soup.select_one("article .post-header, article .post-intro, article .intro")
        if intro:
            return str(intro)
            
        return ""
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata from a Substack article page."""
        metadata = {}
        
        # Title
        title_elem = soup.select_one("h1")
        if title_elem:
            metadata["title"] = title_elem.text.strip()
            
        # Subtitle
        subtitle_elem = soup.select_one(".subtitle")
        if subtitle_elem:
            metadata["subtitle"] = subtitle_elem.text.strip()
            
        # Date
        date_elem = soup.select_one("time")
        if date_elem:
            metadata["post_date"] = date_elem.get("datetime")
            
        # Author
        author_elem = soup.select_one(".author-name")
        if author_elem:
            metadata["author"] = {"name": author_elem.text.strip()}
            
        # Tags/categories
        tags = []
        tag_elems = soup.select(".tag, .post-tag, .post-tags a")
        for tag in tag_elems:
            tags.append(tag.text.strip())
        if tags:
            metadata["tags"] = tags
        
        return metadata
    
    def _get_post_data(self, subdomain: str, slug: str) -> Optional[Dict]:
        """Get data for a specific post."""
        cache_key = f"post_{subdomain}_{slug}"
        if cache_key in self.cache:
            cache_time = self.cache[cache_key].get("timestamp", 0)
            if time.time() - cache_time < 7 * 24 * 60 * 60:  # 7 days
                return self.cache[cache_key].get("data")
        
        # Try API endpoints first
        url = f"https://{subdomain}.substack.com/api/v1/posts/{slug}"
        response = self._make_request(url)
        
        if response:
            try:
                data = response.json()
                
                # Ensure the URL is included
                if "url" not in data or not data["url"]:
                    data["url"] = f"https://{subdomain}.substack.com/p/{slug}"
                
                # Cache the result
                self.cache[cache_key] = {
                    "timestamp": time.time(),
                    "data": data
                }
                self._save_cache()
                return data
            except Exception:
                pass
        
        # Fallback to scraping the post page
        url = f"https://{subdomain}.substack.com/p/{slug}"
        response = self._make_request(url)
        
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract post data from HTML
            article = soup.select_one("article")
            
            # Check if the article is behind a paywall
            is_paid = self._check_for_paywall(soup)
            if is_paid:
                logger.info(f"Detected paywalled content for {subdomain}/{slug}")
            
            # Extract metadata
            metadata = self._extract_metadata(soup)
            
            # Extract content based on paywall status
            content_html = ""
            
            if article:
                if is_paid:
                    # Get preview content only for paywalled articles
                    content_html = self._extract_preview_content(soup)
                else:
                    # Get full content for free articles
                    content_html = str(article)
            
            data = {
                "title": metadata.get("title", ""),
                "subtitle": metadata.get("subtitle", ""),
                "body_html": content_html,
                "post_date": metadata.get("post_date"),
                "author": metadata.get("author", {"name": "Unknown"}),
                "tags": metadata.get("tags", []),
                "is_paid": is_paid,
                "url": url
            }
            
            # Cache the result
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "data": data
            }
            self._save_cache()
            
            return data
            
        except Exception as e:
            logger.error(f"Error scraping post data for {subdomain}/{slug}: {str(e)}")
            return None
    
    def _post_to_content_item(self, post: Dict, subdomain: str) -> Optional[ContentItem]:
        """Convert a Substack post to a ContentItem."""
        try:
            url = post.get("url")
            if not url:
                # Try to construct URL from available data
                slug = post.get("slug")
                if slug:
                    url = f"https://{subdomain}.substack.com/p/{slug}"
                else:
                    # Generate an ID based on title if available, otherwise use a timestamp
                    title_id = hashlib.md5(post.get("title", str(time.time())).encode()).hexdigest()[:8]
                    url = f"https://{subdomain}.substack.com/p/post-{title_id}"
                post["url"] = url
            
            # Get HTML content
            html_content = post.get("body_html", "")
            is_paid = post.get("is_paid", False)
            
            # If no HTML content and we have a URL, try to fetch it
            if not html_content and url:
                response = self._make_request(url)
                if response:
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Check for paywall
                    is_paid = self._check_for_paywall(soup)
                    
                    if is_paid:
                        # Extract preview content for paywalled articles
                        html_content = self._extract_preview_content(soup)
                    else:
                        # Get full content for free articles
                        article = soup.select_one("article")
                        if article:
                            html_content = str(article)
            
            # Parse HTML content - safely handle None
            if html_content:
                try:
                    soup = BeautifulSoup(html_content, "html.parser")
                    text_content = soup.get_text(separator="\n\n")
                except Exception as e:
                    logger.error(f"Error parsing HTML content for {url}: {str(e)}")
                    text_content = "Error parsing content"
            else:
                # If we have no HTML content, use post description or create placeholder
                text_content = post.get("subtitle", "") or post.get("description", "") or "No content available"
                logger.warning(f"No HTML content found for {url}")
            
            if not text_content.strip():
                text_content = "No content available"
                logger.warning(f"Empty text content for post from {subdomain}, using placeholder")
            
            # Add paywall notice to beginning of text if applicable
            if is_paid:
                paywall_notice = (
                    "[This is a paid article - preview only]\n\n"
                    "This content requires a subscription to read in full.\n"
                    "Below is the preview content available without a subscription.\n\n"
                    "---\n\n"
                )
                text_content = paywall_notice + text_content
            
            # Create unique filename
            post_id = str(post.get("id", hashlib.md5(url.encode()).hexdigest()))
            filename = f"substack_{subdomain}_{post_id}.txt"
            text_path = self.output_dir / filename
            
            # Save text content
            try:
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
            except Exception as e:
                logger.error(f"Error saving text content for {url}: {str(e)}")
                return None
            
            # Parse publish date
            publish_date = None
            post_date = post.get("post_date") or post.get("publishedAt") or post.get("published_at")
            if post_date:
                try:
                    # Handle datetime object
                    if isinstance(post_date, datetime):
                        if post_date.tzinfo:
                            # Convert to UTC and make naive
                            publish_date = post_date.astimezone(timezone.utc).replace(tzinfo=None)
                        else:
                            # Already naive, assume UTC
                            publish_date = post_date
                    else:
                        # Handle string
                        for fmt in [
                            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with microseconds
                            "%Y-%m-%dT%H:%M:%SZ",      # ISO format without microseconds
                            "%Y-%m-%d %H:%M:%S",       # Simple datetime
                            "%Y-%m-%d"                 # Simple date
                        ]:
                            try:
                                publish_date = datetime.strptime(post_date, fmt)
                                if fmt.endswith("Z"):
                                    # Convert UTC to naive
                                    publish_date = publish_date.replace(tzinfo=None)
                                else:
                                    # Assume UTC and convert to naive
                                    publish_date = publish_date.replace(tzinfo=timezone.utc).replace(tzinfo=None)
                                break
                            except ValueError:
                                continue
                except Exception as e:
                    logger.warning(f"Error parsing publish date '{post_date}' for {url}: {str(e)}")
                    publish_date = None
            
            # Create metadata
            metadata = ContentMetadata(
                source_type="substack",
                content_type="blog_article",
                source_quality=9.5,  # High quality curated newsletters
                is_curated=True,
                source_name=f"Substack - {subdomain}",
                additional_meta={
                    "newsletter": subdomain,
                    "word_count": len(text_content.split()),
                    "is_paid": is_paid,
                    "tags": post.get("tags", [])
                }
            )
            
            # Create content item
            return ContentItem(
                id=post_id,
                url=url,
                title=post.get("title", ""),
                description=post.get("subtitle", ""),
                authors=[post.get("author", {}).get("name", "Unknown")],
                publish_date=publish_date,
                metadata=metadata,
                text_path=text_path,
                raw_data=post
            )
            
        except Exception as e:
            logger.error(f"Error converting post to ContentItem: {str(e)}")
            return None 