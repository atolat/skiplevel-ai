"""
Content Curation Pipeline

This module provides a pipeline for discovering, curating, and evaluating content 
about engineering career development and performance feedback.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple, Union, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)

# Set up logger for this module
logger = logging.getLogger("pipeline")

# Import core components
from .pipeline import run_content_pipeline
from .modules.content_extraction import scrape_url_content
from .modules.web_evaluation import evaluate_url_with_browsing as evaluate_url, batch_evaluate_urls
from .modules.content_analysis import analyze_high_quality_content as analyze_content

# Make key functions available at package level
__all__ = [
    "run_content_pipeline",
    "scrape_url_content",
    "evaluate_url",
    "batch_evaluate_urls",
    "analyze_content"
]

# Version info
__version__ = "0.2.0"
__author__ = "Arpan Tolat"
__email__ = "arpan@skiplevel.ai"

# Global config
DEFAULT_QUERY = "engineering career growth frameworks AND technical evaluation criteria AND professional development"
DEFAULT_EVALUATION_METHOD = "openai_browsing"  # Can be: standard, openai_browsing, tavily_content
