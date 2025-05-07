#!/usr/bin/env python
"""Check environment variables for the content curation pipeline."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    """Check for required API keys in environment variables."""
    # Try to load from different possible .env locations
    root_env = Path(".env")
    subdir_env = Path("content-curation-pipeline/.env")
    
    if subdir_env.exists():
        print(f"Loading environment from {subdir_env}")
        load_dotenv(subdir_env)
    elif root_env.exists():
        print(f"Loading environment from {root_env}")
        load_dotenv(root_env)
    else:
        print("No .env file found. Checking environment variables directly.")
    
    print("\n🔍 Checking environment variables for content curation pipeline...\n")
    
    # Required API keys
    required_keys = {
        "OPENAI_API_KEY": "Required for content evaluation and analysis",
        "TAVILY_API_KEY": "Required for content curation with Tavily"
    }
    
    # Optional API keys
    optional_keys = {
        "REDDIT_CLIENT_ID": "For Reddit content curation",
        "REDDIT_CLIENT_SECRET": "For Reddit content curation",
        "REDDIT_USER_AGENT": "For Reddit content curation",
        "MEDIUM_API_KEY": "For Medium article extraction via Medium API",
        "GITHUB_TOKEN": "For GitHub repository access",
        "YOUTUBE_API_KEY": "For YouTube video discovery and metadata"
    }
    
    # Check required keys
    missing_required = []
    for key, description in required_keys.items():
        value = os.getenv(key)
        if value:
            print(f"✅ {key}: Found")
        else:
            print(f"❌ {key}: Missing - {description}")
            missing_required.append(key)
    
    # Check optional keys
    print("\nOptional environment variables:")
    missing_reddit = []
    medium_missing = False
    github_missing = False
    youtube_missing = False
    
    for key, description in optional_keys.items():
        value = os.getenv(key)
        if value:
            print(f"✅ {key}: Found")
        else:
            print(f"⚠️ {key}: Missing - {description}")
            if key.startswith("REDDIT"):
                missing_reddit.append(key)
            elif key == "MEDIUM_API_KEY":
                medium_missing = True
            elif key == "GITHUB_TOKEN":
                github_missing = True
            elif key == "YOUTUBE_API_KEY":
                youtube_missing = True
    
    # Summary
    print("\nSummary:")
    if missing_required:
        print(f"❌ Missing required keys: {', '.join(missing_required)}")
        print("   These keys must be set for the pipeline to work properly.")
    else:
        print("✅ All required keys are set.")
        
    if len(missing_reddit) == 3:  # All Reddit keys are missing
        print("⚠️ All Reddit API credentials are missing. Reddit content curation will be disabled.")
    elif missing_reddit:
        print(f"⚠️ Some Reddit API credentials are missing: {', '.join(missing_reddit)}")
        print("   Reddit content curation may not work properly.")
    else:
        print("✅ Reddit API credentials are set - Reddit content curation is enabled.")
        
    if medium_missing:
        print("⚠️ Medium API key is missing. Medium article extraction will be limited.")
    else:
        print("✅ Medium API key is set - Enhanced Medium content extraction is enabled.")
        
    if github_missing:
        print("⚠️ GitHub token is missing. GitHub repository access may be rate-limited.")
    else:
        print("✅ GitHub token is set - Full GitHub repository access is enabled.")
        
    if youtube_missing:
        print("⚠️ YouTube API key is missing. YouTube video discovery will be disabled.")
    else:
        print("✅ YouTube API key is set - YouTube video discovery is enabled.")
    
    # Show instructions based on where the env file should be
    if subdir_env.exists():
        env_path = "content-curation-pipeline/.env"
    else:
        env_path = ".env"
        
    print(f"\nTo set these variables, edit the {env_path} file with the following format:")
    print("""
    OPENAI_API_KEY=your_openai_api_key
    TAVILY_API_KEY=your_tavily_api_key
    REDDIT_CLIENT_ID=your_reddit_client_id
    REDDIT_CLIENT_SECRET=your_reddit_client_secret
    REDDIT_USER_AGENT=python:content-curation-pipeline:v0.2.0 (by /u/your_username)
    MEDIUM_API_KEY=your_medium_api_key_from_rapidapi
    GITHUB_TOKEN=your_github_personal_access_token
    YOUTUBE_API_KEY=your_youtube_api_key
    """)
    
    # Exit with error code if required keys are missing
    if missing_required:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main()) 