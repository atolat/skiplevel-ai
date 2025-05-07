"""
YouTube content source implementation.
"""

import json
import logging
import re
import time
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

from ...interfaces import ContentSource, ContentItem, ContentMetadata

logger = logging.getLogger(__name__)

class YouTubeSource(ContentSource):
    """Content source for YouTube videos."""
    
    def __init__(self, cache_dir: Path, output_dir: Path):
        super().__init__(cache_dir, output_dir)
        self.cache_file = self.cache_dir / "youtube_cache.json"
        self.cache = self._load_cache()
        
        # Load environment variables
        load_dotenv()
        
        # Initialize YouTube API client
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key:
            logger.warning("YOUTUBE_API_KEY not found in environment variables")
        self.youtube = build('youtube', 'v3', developerKey=api_key) if api_key else None

    def _load_cache(self) -> Dict:
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading YouTube cache: {str(e)}")
        return {}
    
    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving YouTube cache: {str(e)}")
    
    def discover(self, query: str, limit: int = 10) -> List[ContentItem]:
        """Discover content from YouTube based on search query."""
        discovered_items = []
        seen_ids = set()
        
        if not self.youtube:
            logger.error("YouTube API client not initialized - missing API key")
            return discovered_items

        try:
            # Search for videos related to the query
            search_query = f"{query} engineering career software development"
            search_response = self.youtube.search().list(
                q=search_query,
                part='id,snippet',
                type='video',
                videoCaption='closedCaption',  # Only videos with captions
                relevanceLanguage='en',
                maxResults=min(limit * 2, 50),  # Request more to account for filtering
                order='relevance'
            ).execute()

            # Process search results
            for item in search_response.get('items', []):
                if len(discovered_items) >= limit:
                    break

                video_id = item['id'].get('videoId')
                if not video_id or video_id in seen_ids:
                    continue

                try:
                    # Get detailed video information
                    video_response = self.youtube.videos().list(
                        part='snippet,statistics,contentDetails',
                        id=video_id
                    ).execute()
                    
                    if not video_response.get('items'):
                        continue
                    
                    video_info = video_response['items'][0]
                    
                    # Check if video has transcripts
                    content_item = self._process_video_id(video_id, video_info)
                    if content_item:
                        discovered_items.append(content_item)
                        seen_ids.add(video_id)
                
                except Exception as e:
                    logger.error(f"Error processing video {video_id}: {str(e)}")
                    continue

        except HttpError as e:
            logger.error(f"Error searching YouTube: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during YouTube discovery: {str(e)}")

        return discovered_items
    
    def process_url(self, url: str) -> Optional[ContentItem]:
        """Process a single YouTube URL."""
        if not self.youtube:
            logger.error("YouTube API client not initialized - missing API key")
            return None

        if not self.is_source_url(url):
            return None
            
        try:
            video_id = self._extract_video_id(url)
            if not video_id:
                return None
            
            # Get video information from API
            video_response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            ).execute()
            
            if not video_response.get('items'):
                return None
            
            return self._process_video_id(video_id, video_response['items'][0])
            
        except Exception as e:
            logger.error(f"Error processing YouTube URL {url}: {str(e)}")
            return None
    
    def is_source_url(self, url: str) -> bool:
        """Check if URL is from YouTube."""
        return bool(self._extract_video_id(url))
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from URL."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/oembed\?.*?url=.*?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/live/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _get_transcript(self, video_id: str, languages: List[str] = None) -> Optional[str]:
        """Get transcript for a video."""
        if languages is None:
            languages = ["en"]
            
        cache_key = f"transcript_{video_id}_{'-'.join(languages)}"
        if cache_key in self.cache:
            cache_time = self.cache[cache_key].get("timestamp", 0)
            if time.time() - cache_time < 30 * 24 * 60 * 60:  # 30 days
                return self.cache[cache_key].get("data")
        
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try preferred languages first
            transcript = None
            for lang in languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    break
                except NoTranscriptFound:
                    continue
            
            # Fall back to any available transcript
            if transcript is None:
                try:
                    transcript = next(iter(transcript_list))
                except StopIteration:
                    logger.warning(f"No transcript available for video {video_id}")
                    return None
            
            # Get transcript text
            transcript_data = transcript.fetch()
            text_parts = []
            for segment in transcript_data:
                # Access text attribute directly from the FetchedTranscriptSnippet object
                text_parts.append(segment.text)
            
            text_content = "\n".join(text_parts)
            
            # Cache the result
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "data": text_content
            }
            self._save_cache()
            
            return text_content
            
        except Exception as e:
            logger.error(f"Error getting transcript for video {video_id}: {str(e)}")
            return None
    
    def _process_video_id(self, video_id: str, video_info: Dict = None) -> Optional[ContentItem]:
        """Process a video by ID."""
        try:
            # Get transcript first - no point processing if we can't get transcript
            transcript = self._get_transcript(video_id)
            if not transcript:
                return None
            
            if not video_info and self.youtube:
                try:
                    video_response = self.youtube.videos().list(
                        part='snippet,statistics,contentDetails',
                        id=video_id
                    ).execute()
                    video_info = video_response['items'][0] if video_response.get('items') else None
                except Exception as e:
                    logger.error(f"Error getting video info from API: {str(e)}")
            
            if not video_info:
                video_info = {
                    'snippet': {
                        'title': f'YouTube Video {video_id}',
                        'description': '',
                        'channelTitle': 'Unknown',
                        'publishedAt': None
                    }
                }
            
            # Create unique filename
            filename = f"youtube_{video_id}.txt"
            text_path = self.output_dir / filename
            
            # Save transcript
            try:
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(transcript)
            except Exception as e:
                logger.error(f"Error saving transcript: {str(e)}")
                return None
            
            # Parse publish date
            try:
                date_str = video_info['snippet'].get('publishedAt')
                if date_str:
                    # YouTube API always returns UTC timestamps
                    publish_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
                    # Convert to naive UTC
                    publish_date = publish_date.replace(tzinfo=None)
                else:
                    publish_date = None
            except Exception as e:
                logger.warning(f"Error parsing publish date '{date_str}': {str(e)}")
                publish_date = None
            
            # Get video statistics
            stats = video_info.get('statistics', {})
            view_count = int(stats.get('viewCount', 0))
            like_count = int(stats.get('likeCount', 0))
            
            # Calculate source quality based on engagement metrics
            source_quality = 7.0  # Base quality
            if view_count > 10000:
                source_quality += 1.0
            if like_count > 1000:
                source_quality += 1.0
            
            # Create metadata
            metadata = ContentMetadata(
                source_type="youtube",
                content_type="video_transcript",
                source_quality=min(10.0, source_quality),
                is_curated=False,  # Now using dynamic discovery
                source_name=f"YouTube - {video_info['snippet']['channelTitle']}",
                additional_meta={
                    "video_id": video_id,
                    "channel": video_info['snippet']['channelTitle'],
                    "view_count": view_count,
                    "like_count": like_count,
                    "word_count": len(transcript.split())
                }
            )
            
            # Create content item
            return ContentItem(
                id=video_id,
                url=f"https://www.youtube.com/watch?v={video_id}",
                title=video_info['snippet']['title'],
                description=video_info['snippet']['description'],
                authors=[video_info['snippet']['channelTitle']],
                publish_date=publish_date,
                metadata=metadata,
                text_path=text_path,
                raw_data=video_info
            )
            
        except Exception as e:
            logger.error(f"Error processing video {video_id}: {str(e)}")
            return None 