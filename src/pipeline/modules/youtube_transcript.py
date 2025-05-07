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
        
        # Fetch transcript data
        transcript_data = transcript.fetch()
        
        # Cache the result
        YOUTUBE_CACHE[cache_key] = {
            "timestamp": time.time(),
            "data": transcript_data
        }
        save_cache()
        
        return transcript_data
    
    except (TranscriptsDisabled, NoTranscriptFound, Exception) as e:
        logger.warning(f"Failed to get transcript for video {video_id}: {str(e)}")
        return None

# ... existing code ... 