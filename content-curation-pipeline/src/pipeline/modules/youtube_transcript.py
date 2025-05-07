"""
YouTube transcript module for extracting transcripts from YouTube videos.

This module provides functions to extract and process transcripts from YouTube videos
using the youtube_transcript_api library.
"""

import os
import logging
import json
import time
import hashlib
import re
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

logger = logging.getLogger(__name__)

# Cache directory for YouTube transcript results
YOUTUBE_CACHE_DIR = Path("./data/cache/youtube")
YOUTUBE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
YOUTUBE_CACHE_FILE = YOUTUBE_CACHE_DIR / "youtube_transcript_cache.json"

# Text output directory
YOUTUBE_TEXTS_DIR = Path("./data/texts/youtube")
YOUTUBE_TEXTS_DIR.mkdir(parents=True, exist_ok=True)

# Load YouTube cache if exists
YOUTUBE_CACHE = {}
if YOUTUBE_CACHE_FILE.exists():
    try:
        with open(YOUTUBE_CACHE_FILE, 'r') as f:
            YOUTUBE_CACHE = json.load(f)
            logger.info(f"Loaded {len(YOUTUBE_CACHE)} YouTube transcript cache entries")
    except Exception as e:
        logger.error(f"Error loading YouTube transcript cache: {str(e)}")

def save_cache():
    """Save YouTube transcript cache to file."""
    try:
        with open(YOUTUBE_CACHE_FILE, 'w') as f:
            json.dump(YOUTUBE_CACHE, f, indent=2)
        logger.info(f"Saved {len(YOUTUBE_CACHE)} YouTube transcript cache entries")
    except Exception as e:
        logger.error(f"Error saving YouTube transcript cache: {str(e)}")

def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from URL.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Video ID or None if not found
    """
    # Regular expressions for different YouTube URL formats
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

def get_transcript(video_id: str, languages: List[str] = None) -> Optional[List[Dict]]:
    """
    Get transcript for a YouTube video.
    
    Args:
        video_id: YouTube video ID
        languages: List of language codes to try, defaults to ["en"]
        
    Returns:
        List of transcript segments or None if not available
    """
    if languages is None:
        languages = ["en"]
    
    cache_key = f"transcript_{video_id}_{'-'.join(languages)}"
    if cache_key in YOUTUBE_CACHE:
        cache_time = YOUTUBE_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 30 * 24 * 60 * 60:  # 30 days in seconds
            logger.info(f"Using cached transcript for video {video_id}")
            return YOUTUBE_CACHE[cache_key].get("data")
    
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get transcript in preferred languages
        transcript = None
        for lang in languages:
            try:
                transcript = transcript_list.find_transcript([lang])
                break
            except NoTranscriptFound:
                continue
        
        # If no preferred language found, try to get any available transcript
        if transcript is None:
            try:
                # Get the first available transcript
                transcript = next(iter(transcript_list))
            except StopIteration:
                logger.warning(f"No transcript available for video {video_id}")
                return None
        
        # Fetch transcript data and convert to serializable format
        transcript_data = transcript.fetch()
        serializable_data = []
        for segment in transcript_data:
            serializable_data.append({
                "text": segment.text,
                "start": segment.start,
                "duration": segment.duration
            })
        
        # Cache the result
        YOUTUBE_CACHE[cache_key] = {
            "timestamp": time.time(),
            "data": serializable_data
        }
        save_cache()
        
        return serializable_data
    
    except (TranscriptsDisabled, NoTranscriptFound, Exception) as e:
        logger.warning(f"Failed to get transcript for video {video_id}: {str(e)}")
        return None

def transcript_to_text(transcript: List[Dict]) -> str:
    """
    Convert transcript segments to plain text.
    
    Args:
        transcript: List of transcript segments
        
    Returns:
        Plain text of the transcript
    """
    if not transcript:
        return ""
    
    text_parts = []
    for segment in transcript:
        text_parts.append(segment.get("text", ""))
    
    return "\n".join(text_parts)

def get_transcript_text(video_id: str, languages: List[str] = None) -> Optional[str]:
    """
    Get transcript text for a YouTube video.
    
    Args:
        video_id: YouTube video ID
        languages: List of language codes to try, defaults to ["en"]
        
    Returns:
        Plain text of the transcript or None if not available
    """
    transcript = get_transcript(video_id, languages)
    if transcript:
        return transcript_to_text(transcript)
    return None

def get_video_metadata(video_id: str) -> Optional[Dict]:
    """
    Get metadata for a YouTube video using the oEmbed API.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Dictionary with video metadata or None if not available
    """
    cache_key = f"metadata_{video_id}"
    if cache_key in YOUTUBE_CACHE:
        cache_time = YOUTUBE_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 7 * 24 * 60 * 60:  # 7 days in seconds
            logger.info(f"Using cached metadata for video {video_id}")
            return YOUTUBE_CACHE[cache_key].get("data")
    
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Cache the result
            YOUTUBE_CACHE[cache_key] = {
                "timestamp": time.time(),
                "data": data
            }
            save_cache()
            
            return data
        else:
            logger.warning(f"Failed to get metadata for video {video_id}: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error getting metadata for video {video_id}: {str(e)}")
        return None

def discover_youtube_transcripts(search_terms: List[str], limit_per_term: int = 5) -> List[Dict]:
    """
    Discover YouTube video transcripts based on search terms.
    
    Args:
        search_terms: List of search terms to find videos
        limit_per_term: Maximum number of videos per search term
        
    Returns:
        List of transcript resources
    """
    logger.info(f"Discovering YouTube transcripts for terms: {search_terms}")
    
    # Create a cache key for this discovery run
    terms_str = "_".join(sorted(search_terms))
    cache_key = f"youtube_discovery_{hashlib.md5(terms_str.encode()).hexdigest()}"
    
    # Check cache for recent results (< 1 day old)
    if cache_key in YOUTUBE_CACHE:
        cache_time = YOUTUBE_CACHE[cache_key].get("timestamp", 0)
        if time.time() - cache_time < 1 * 24 * 60 * 60:  # 1 day in seconds
            logger.info(f"Using cached YouTube discovery results for {search_terms}")
            return YOUTUBE_CACHE[cache_key].get("data", [])
    
    # List of manually curated video IDs for engineering career content
    engineering_videos = [
        "4LKJbVnsGuI",  # ENGINEERING JOB OUTLOOK & SALARIES 2024
        "5NEL9Rn4ITM",  # 3 Hard Lessons made me a better Engineer (in 2024)
        "zTf0MDAB8Pw",  # Is Software Engineering Still Worth It in 2024?
        "PSWUr5E_OKY",  # Become An AI Engineer in 2025
        "VpPPHDxR9aM",  # The software engineering industry in 2024
        "ZcpZjrwhg_Q",  # My Honest Thoughts On The Software Engineering Market In 2024
        "YQYJtR8Qd0Q",  # Software Engineering Career Path in 2024
        "uGRa6Cg6IgM",  # Career Growth Tips for Software Engineers
        "fzwUUMx9N6E",  # Tech Career Advice That Actually Works
        "Kv_LWjgcy4A",  # How to Grow Your Tech Career
    ]
    
    # Process each video
    results = []
    for video_id in engineering_videos:
        try:
            # Get transcript
            transcript = get_transcript(video_id)
            if not transcript:
                continue
            
            # Convert transcript to text
            text_content = transcript_to_text(transcript)
            if not text_content or len(text_content) < 500:  # Skip short content
                continue
            
            # Create unique filename
            file_name = f"youtube_{video_id}.txt"
            text_path = str(YOUTUBE_TEXTS_DIR / file_name)
            
            # Save text to file
            try:
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                logger.info(f"Saved YouTube transcript to {text_path}")
            except Exception as e:
                logger.error(f"Error saving transcript: {str(e)}")
                text_path = None
            
            # Create resource dictionary
            article_dict = {
                "title": f"YouTube Video {video_id}",  # We'll update this with metadata later
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "source": "youtube_transcript",
                "description": "",  # We'll update this with metadata later
                "authors": ["Unknown"],  # We'll update this with metadata later
                "meta": {
                    "content_type": "video_transcript",
                    "is_curated": True,
                    "source_quality": 7,
                    "video_id": video_id,
                    "word_count": len(text_content.split())
                },
                "text": text_content,
                "text_path": text_path,
                "is_processed": True
            }
            
            # Try to get metadata to enhance the resource
            try:
                metadata = get_video_metadata(video_id)
                if metadata:
                    article_dict["title"] = metadata.get("title", article_dict["title"])
                    article_dict["description"] = metadata.get("description", "")
                    article_dict["authors"] = [metadata.get("author_name", "Unknown")]
            except Exception as e:
                logger.warning(f"Failed to get metadata for video {video_id}: {str(e)}")
            
            results.append(article_dict)
            logger.info(f"Added YouTube transcript: {article_dict['title']}")
        except Exception as e:
            logger.error(f"Error processing video {video_id}: {str(e)}")
    
    # Cache the results
    YOUTUBE_CACHE[cache_key] = {
        "timestamp": time.time(),
        "data": results
    }
    save_cache()
    
    logger.info(f"Discovered {len(results)} YouTube transcripts")
    return results

def process_youtube_url(url: str) -> Optional[Dict]:
    """
    Process a YouTube URL to extract transcript and metadata.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Dictionary with processed transcript and metadata or None if processing failed
    """
    video_id = extract_video_id(url)
    if not video_id:
        logger.warning(f"Invalid YouTube URL: {url}")
        return None
    
    try:
        # Get transcript
        transcript = get_transcript(video_id)
        if not transcript:
            return None
        
        # Convert transcript to text
        text_content = transcript_to_text(transcript)
        if not text_content:
            return None
        
        # Get video metadata
        metadata = get_video_metadata(video_id)
        title = metadata.get("title", f"YouTube Video {video_id}") if metadata else f"YouTube Video {video_id}"
        author = metadata.get("author_name", "Unknown") if metadata else "Unknown"
        
        # Create unique filename
        title_slug = title[:30].lower().replace(" ", "_")
        title_slug = ''.join(c if c.isalnum() or c == '_' else '' for c in title_slug)
        file_name = f"youtube_{title_slug}_{video_id}.txt"
        text_path = str(YOUTUBE_TEXTS_DIR / file_name)
        
        # Save text to file
        try:
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            logger.info(f"Saved YouTube transcript to {text_path}")
        except Exception as e:
            logger.error(f"Error saving transcript: {str(e)}")
            text_path = None
        
        # Create resource dictionary
        result = {
            "title": title,
            "url": url,
            "source": "youtube_transcript",
            "description": metadata.get("description", "") if metadata else "",
            "authors": [author],
            "meta": {
                "content_type": "video_transcript",
                "is_curated": True,
                "source_quality": 7,
                "video_id": video_id,
                "word_count": len(text_content.split())
            },
            "text": text_content,
            "text_path": text_path,
            "is_processed": True
        }
        
        return result
    except Exception as e:
        logger.error(f"Error processing YouTube URL {url}: {str(e)}")
        return None

def is_youtube_url(url: str) -> bool:
    """
    Check if a URL is a YouTube video URL.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is a YouTube video URL, False otherwise
    """
    return extract_video_id(url) is not None 