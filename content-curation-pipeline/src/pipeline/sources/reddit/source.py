"""
Reddit content source implementation.
"""

import json
import logging
import re
import time
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import requests
import praw
from praw.models import Submission, Comment, MoreComments
from urllib.parse import urlparse, parse_qs

from ...interfaces import ContentSource, ContentItem, ContentMetadata

logger = logging.getLogger(__name__)

class RedditSource(ContentSource):
    """Content source for Reddit submissions and comments."""
    
    # Rate limiting
    MIN_REQUEST_INTERVAL = 2.0  # seconds between requests
    MAX_RETRIES = 3
    
    def __init__(self, cache_dir: Path, output_dir: Path):
        super().__init__(cache_dir, output_dir)
        self.cache_file = self.cache_dir / "reddit_cache.json"
        self.cache = self._load_cache()
        self.last_request_time = 0
        
        # Initialize Reddit API client
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "content_curation_pipeline:v1.0.0 (by /u/your_username)")
        
        if not client_id or not client_secret:
            logger.warning("REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET not set in environment variables")
            self.reddit = None
        else:
            try:
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent
                )
                logger.info("Reddit API client initialized")
            except Exception as e:
                logger.error(f"Error initializing Reddit API client: {str(e)}")
                self.reddit = None
        
        # High-quality career growth/engineering subreddits
        self.recommended_subreddits = [
            "cscareerquestions",
            "ExperiencedDevs", 
            "AskEngineers",
            "softwareengineering",
            "engineering",
            "programming",
            "engineeringmanagement",
            "techleadership",
            "datascience",
            "devops",
            "careeradvice",
            "learnprogramming"
        ]
    
    def _load_cache(self) -> Dict:
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading Reddit cache: {str(e)}")
        return {}
    
    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving Reddit cache: {str(e)}")
    
    def _rate_limit(self):
        """Apply rate limiting."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
        self.last_request_time = time.time()
    
    def discover(self, query: str, limit: int = 10) -> List[ContentItem]:
        """Discover content from Reddit."""
        if not self.reddit:
            logger.error("Cannot discover Reddit content: Reddit API client not initialized")
            return []
        
        discovered_items = []
        seen_ids = set()
        
        try:
            # Apply rate limiting
            self._rate_limit()
            
            # Search across multiple subreddits
            subreddits_to_search = self.recommended_subreddits
            subreddit_string = "+".join(subreddits_to_search)
            subreddit = self.reddit.subreddit(subreddit_string)
            
            logger.info(f"Searching Reddit for: {query} in {subreddit_string}")
            
            # Keep track of how many items we've processed per subreddit
            counts_per_subreddit = {sr: 0 for sr in subreddits_to_search}
            
            # Search for submissions
            search_results = subreddit.search(query, sort="relevance", limit=limit*3)
            
            for submission in search_results:
                # Skip if already seen
                if submission.id in seen_ids:
                    continue
                
                seen_ids.add(submission.id)
                
                # Check if submission is already cached
                cache_key = f"submission_{submission.id}"
                if cache_key in self.cache:
                    cache_time = self.cache[cache_key].get("timestamp", 0)
                    if time.time() - cache_time < 7 * 24 * 60 * 60:  # 7 days
                        item = self._submission_to_content_item(self.cache[cache_key].get("data"))
                        if item:
                            discovered_items.append(item)
                            if len(discovered_items) >= limit:
                                break
                        continue
                
                # Apply rate limiting
                self._rate_limit()
                
                # Process submission
                try:
                    # Get submission data
                    submission_data = self._get_submission_data(submission)
                    
                    # Cache submission data
                    self.cache[cache_key] = {
                        "timestamp": time.time(),
                        "data": submission_data
                    }
                    
                    # Convert to content item
                    item = self._submission_to_content_item(submission_data)
                    if item:
                        discovered_items.append(item)
                        
                    # Break if we have enough items
                    if len(discovered_items) >= limit:
                        break
                
                except Exception as e:
                    logger.error(f"Error processing submission {submission.id}: {str(e)}")
            
            # Save cache
            self._save_cache()
            
            logger.info(f"Discovered {len(discovered_items)} content items from Reddit")
            return discovered_items
            
        except Exception as e:
            logger.error(f"Error discovering Reddit content: {str(e)}")
            return []
    
    def process_url(self, url: str) -> Optional[ContentItem]:
        """Process a single Reddit URL."""
        if not self.reddit:
            logger.error("Cannot process Reddit URL: Reddit API client not initialized")
            return None
            
        if not self.is_source_url(url):
            return None
            
        try:
            # Apply rate limiting
            self._rate_limit()
            
            # Extract submission ID from URL
            submission_id = self._get_submission_id_from_url(url)
            if not submission_id:
                logger.warning(f"Could not extract submission ID from URL: {url}")
                return None
            
            # Check if submission is already cached
            cache_key = f"submission_{submission_id}"
            if cache_key in self.cache:
                cache_time = self.cache[cache_key].get("timestamp", 0)
                if time.time() - cache_time < 7 * 24 * 60 * 60:  # 7 days
                    return self._submission_to_content_item(self.cache[cache_key].get("data"))
            
            # Get submission
            submission = self.reddit.submission(id=submission_id)
            
            # Get submission data
            submission_data = self._get_submission_data(submission)
            
            # Cache submission data
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "data": submission_data
            }
            self._save_cache()
            
            # Convert to content item
            return self._submission_to_content_item(submission_data)
            
        except Exception as e:
            logger.error(f"Error processing Reddit URL {url}: {str(e)}")
            return None
    
    def is_source_url(self, url: str) -> bool:
        """Check if URL is from Reddit."""
        return bool(re.search(r'reddit\.com/r/|redd\.it/', url))
    
    def _get_submission_id_from_url(self, url: str) -> Optional[str]:
        """Extract submission ID from URL."""
        # Handle shortened URLs (e.g., https://redd.it/abcdef)
        if "redd.it" in url:
            match = re.search(r'redd\.it/([a-zA-Z0-9]+)', url)
            if match:
                return match.group(1)
        
        # Handle full URLs
        submission_id = None
        
        # Extract from path, e.g., /r/subreddit/comments/abcdef/title/
        match = re.search(r'/comments/([a-zA-Z0-9]+)(?:/|$)', url)
        if match:
            submission_id = match.group(1)
        
        # Extract from query, e.g., ?id=abcdef
        if not submission_id:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            if 'id' in query_params:
                submission_id = query_params['id'][0]
        
        return submission_id
    
    def _get_submission_data(self, submission: Submission) -> Dict:
        """Get data from a Reddit submission with comments."""
        # Parse submission
        submission_data = {
            "id": submission.id,
            "url": f"https://www.reddit.com{submission.permalink}",
            "title": submission.title,
            "selftext": submission.selftext,
            "author": str(submission.author) if submission.author else "[deleted]",
            "subreddit": submission.subreddit.display_name,
            "score": submission.score,
            "upvote_ratio": submission.upvote_ratio,
            "num_comments": submission.num_comments,
            "created_utc": submission.created_utc,
            "is_self": submission.is_self,
            "is_original_content": submission.is_original_content,
            "stickied": submission.stickied,
            "link_flair_text": submission.link_flair_text,
            "external_url": submission.url if not submission.is_self else None,
            "comments": []
        }
        
        # Get comments
        try:
            # Replace all MoreComments objects with actual Comment objects
            submission.comments.replace_more(limit=16)  # Limit to avoid excessive API calls
            
            # Get top-level comments
            top_comments = []
            for comment in submission.comments:
                if isinstance(comment, Comment):
                    comment_data = {
                        "id": comment.id,
                        "author": str(comment.author) if comment.author else "[deleted]",
                        "body": comment.body,
                        "score": comment.score,
                        "created_utc": comment.created_utc,
                        "replies": []
                    }
                    
                    # Get replies (just one level deep to avoid excessive API calls)
                    for reply in comment.replies:
                        if isinstance(reply, Comment):
                            reply_data = {
                                "id": reply.id,
                                "author": str(reply.author) if reply.author else "[deleted]",
                                "body": reply.body,
                                "score": reply.score,
                                "created_utc": reply.created_utc
                            }
                            comment_data["replies"].append(reply_data)
                    
                    top_comments.append(comment_data)
            
            submission_data["comments"] = top_comments
            
        except Exception as e:
            logger.warning(f"Error getting comments for submission {submission.id}: {str(e)}")
        
        return submission_data
    
    def _submission_to_content_item(self, submission_data: Dict) -> Optional[ContentItem]:
        """Convert a Reddit submission to a ContentItem."""
        try:
            if not submission_data:
                return None
            
            submission_id = submission_data.get("id")
            
            # Create unique filename
            filename = f"reddit_{submission_id}.txt"
            text_path = self.output_dir / filename
            
            # Prepare text content
            text_content = f"# {submission_data.get('title', '')}\n\n"
            
            # Add submission text if available
            selftext = submission_data.get("selftext", "")
            if selftext:
                text_content += f"{selftext}\n\n"
            
            # Add comments
            text_content += "## Comments\n\n"
            for i, comment in enumerate(submission_data.get("comments", []), 1):
                author = comment.get("author", "[deleted]")
                score = comment.get("score", 0)
                body = comment.get("body", "").strip()
                
                text_content += f"### Comment {i} by u/{author} ({score} points)\n\n{body}\n\n"
                
                # Add replies
                for j, reply in enumerate(comment.get("replies", []), 1):
                    reply_author = reply.get("author", "[deleted]")
                    reply_score = reply.get("score", 0)
                    reply_body = reply.get("body", "").strip()
                    
                    text_content += f"#### Reply {j} by u/{reply_author} ({reply_score} points)\n\n{reply_body}\n\n"
            
            # Save text content
            try:
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
            except Exception as e:
                logger.error(f"Error saving text content: {str(e)}")
                return None
            
            # Parse publish date
            created_utc = submission_data.get("created_utc")
            publish_date = None
            if created_utc:
                try:
                    publish_date = datetime.fromtimestamp(created_utc)
                except Exception as e:
                    logger.warning(f"Error parsing publish date: {str(e)}")
            
            # Create metadata
            metadata = ContentMetadata(
                source_type="reddit",
                content_type="discussion",
                source_quality=7.5,  # Reddit content quality varies
                is_curated=True,
                source_name=f"Reddit - r/{submission_data.get('subreddit', 'unknown')}",
                additional_meta={
                    "subreddit": submission_data.get("subreddit"),
                    "score": submission_data.get("score", 0),
                    "upvote_ratio": submission_data.get("upvote_ratio", 0),
                    "num_comments": submission_data.get("num_comments", 0),
                    "is_self": submission_data.get("is_self", True),
                    "is_original_content": submission_data.get("is_original_content", False),
                    "stickied": submission_data.get("stickied", False),
                    "flair": submission_data.get("link_flair_text"),
                    "external_url": submission_data.get("external_url"),
                    "comment_count": len(submission_data.get("comments", [])),
                    "word_count": len(text_content.split())
                }
            )
            
            # Get authors (submission author and top comment authors)
            authors = [submission_data.get("author", "[deleted]")]
            
            # Create content item
            return ContentItem(
                id=submission_id,
                url=submission_data.get("url", ""),
                title=submission_data.get("title", ""),
                description=submission_data.get("selftext", "")[:200] + "..." if len(submission_data.get("selftext", "")) > 200 else submission_data.get("selftext", ""),
                authors=authors,
                publish_date=publish_date,
                metadata=metadata,
                text_path=text_path,
                raw_data=submission_data
            )
            
        except Exception as e:
            logger.error(f"Error converting submission to ContentItem: {str(e)}")
            return None 