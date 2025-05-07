"""
Configuration module for the content curation pipeline.

This module provides functionality for loading, validating, and using
configuration files to control the behavior of content sources and
processors in the pipeline.
"""

from .config_loader import (
    load_config,
    get_default_config,
    validate_config,
    merge_configs,
    ConfigSchema
)

__all__ = [
    'load_config',
    'get_default_config',
    'validate_config',
    'merge_configs',
    'ConfigSchema'
] 