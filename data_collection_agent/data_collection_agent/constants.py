"""Constants and configuration for the data collection agent."""

# Known structured sources for engineering career rubrics
RUBRIC_SOURCES = {
    "google": {
        "url": "https://rework.withgoogle.com/guides/managers-identify-and-remove-bias/steps/learn-about-googles-manager-rubric/",
        "type": "html",
        "company": "Google",
        "dimensions": ["Execution", "Leadership", "Strategy", "Collaboration"]
    },
    "microsoft": {
        "url": "https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/technical-career-framework.pdf",
        "type": "pdf",
        "company": "Microsoft",
        "dimensions": ["Technical Excellence", "Business Impact", "Leadership"]
    },
    # Add more sources as needed
}

# Level mappings for standardization
LEVEL_MAPPINGS = {
    "IC4": ["L4", "Senior", "Level 4"],
    "IC5": ["L5", "Staff", "Level 5"],
    "IC6": ["L6", "Senior Staff", "Level 6"],
    "IC7": ["L7", "Principal", "Level 7"]
}

# Dimension mappings for standardization
DIMENSION_MAPPINGS = {
    "Execution": ["Technical Execution", "Technical Skills", "Technical Excellence"],
    "Leadership": ["Team Leadership", "People Leadership", "Technical Leadership"],
    "Strategy": ["Technical Strategy", "Architecture", "System Design"],
    "Collaboration": ["Teamwork", "Communication", "Cross-functional Collaboration"]
}

# Qdrant collection configuration
QDRANT_CONFIG = {
    "collection_name": "rubrics",
    "vector_size": 1536,  # OpenAI embedding dimension
    "distance": "Cosine"
}

# OpenAI configuration
OPENAI_CONFIG = {
    "model": "gpt-4-turbo-preview",
    "temperature": 0.0,
    "max_tokens": 2000
} 