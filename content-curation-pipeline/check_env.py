#!/usr/bin/env python
"""Check environment variables for the non-agentic pipeline."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    """Check for required API keys in environment variables."""
    # Try to load from different possible .env locations
    root_env = Path(".env")
    subdir_env = Path("non-agentic-pipeline/.env")
    
    if subdir_env.exists():
        print(f"Loading environment from {subdir_env}")
        load_dotenv(subdir_env)
    elif root_env.exists():
        print(f"Loading environment from {root_env}")
        load_dotenv(root_env)
    else:
        print("No .env file found. Checking environment variables directly.")
    
    print("\n🔍 Checking environment variables for non-agentic pipeline...\n")
    
    # Required API keys
    required_keys = {
        "OPENAI_API_KEY": "Required for content evaluation and analysis",
        "TAVILY_API_KEY": "Required for content curation with Tavily"
    }
    
    # Optional API keys
    optional_keys = {
        "REDDIT_CLIENT_ID": "For Reddit content curation",
        "REDDIT_CLIENT_SECRET": "For Reddit content curation",
        "REDDIT_USER_AGENT": "For Reddit content curation"
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
    for key, description in optional_keys.items():
        value = os.getenv(key)
        if value:
            print(f"✅ {key}: Found")
        else:
            print(f"⚠️ {key}: Missing - {description}")
            if key.startswith("REDDIT"):
                missing_reddit.append(key)
    
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
    
    # Show instructions based on where the env file should be
    if subdir_env.exists():
        env_path = "non-agentic-pipeline/.env"
    else:
        env_path = ".env"
        
    print(f"\nTo set these variables, edit the {env_path} file with the following format:")
    print("""
    OPENAI_API_KEY=your_openai_api_key
    TAVILY_API_KEY=your_tavily_api_key
    REDDIT_CLIENT_ID=your_reddit_client_id
    REDDIT_CLIENT_SECRET=your_reddit_client_secret
    REDDIT_USER_AGENT=python:non-agentic-pipeline:v0.1.0 (by /u/your_username)
    """)
    
    # Exit with error code if required keys are missing
    if missing_required:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main()) 