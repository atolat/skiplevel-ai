"""
Substack content source module.

This module provides functionality for discovering and processing content from Substack newsletters.
"""

from .source import SubstackSource
from .processor import SubstackProcessor

__all__ = ['SubstackSource', 'SubstackProcessor'] 