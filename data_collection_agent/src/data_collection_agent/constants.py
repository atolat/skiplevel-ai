"""Constants and configurations for the agentic pipeline."""

from typing import Dict, List, TypedDict

class SourceConfig(TypedDict):
    """Configuration for a data source."""
    url: str
    type: str  # 'html' or 'markdown'
    company: str
    description: str

# Known sources for engineering career rubrics
SOURCES: Dict[str, SourceConfig] = {
    "dropbox": {
        "url": "https://dropbox.design/article/engineering-career-framework",
        "type": "html",
        "company": "Dropbox",
        "description": "Dropbox's engineering career framework"
    },
    "gitlab": {
        "url": "https://handbook.gitlab.com/job-families/engineering/development/",
        "type": "html",
        "company": "GitLab",
        "description": "GitLab's engineering career framework"
    },
    "monzo": {
        "url": "https://monzo.com/blog/2019/01/07/progression-framework",
        "type": "html",
        "company": "Monzo",
        "description": "Monzo's engineering career framework"
    },
    "buffer": {
        "url": "https://buffer.com/resources/engineering-career-framework/",
        "type": "html",
        "company": "Buffer",
        "description": "Buffer's engineering career framework"
    }
}

# Level mappings for different companies
LEVEL_MAPPINGS: Dict[str, Dict[str, str]] = {
    "dropbox": {
        "IC1": "L3",
        "IC2": "L4",
        "IC3": "L5",
        "IC4": "L6",
        "IC5": "L7"
    },
    "gitlab": {
        "Intermediate": "L4",
        "Senior": "L5",
        "Staff": "L6",
        "Principal": "L7"
    },
    "monzo": {
        "Engineer I": "L3",
        "Engineer II": "L4",
        "Senior": "L5",
        "Staff": "L6",
        "Principal": "L7"
    },
    "buffer": {
        "L3": "L3",
        "L4": "L4",
        "L5": "L5",
        "L6": "L6",
        "L7": "L7"
    }
}

# Common dimensions across companies
DIMENSIONS = [
    "execution",
    "technical_skills",
    "leadership",
    "communication",
    "impact",
    "problem_solving",
    "system_design",
    "collaboration"
]

# Qdrant collection configuration
QDANT_COLLECTION = "rubrics"
QDANT_VECTOR_SIZE = 1536  # OpenAI embedding dimension
