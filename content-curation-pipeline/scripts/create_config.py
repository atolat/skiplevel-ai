#!/usr/bin/env python
"""
Create a configuration file for the content curation pipeline.

This script generates a new configuration file based on command line arguments
and saves it to the specified location.
"""

import argparse
import os
import sys
import yaml
from pathlib import Path

# Add the project root to the path so we can import the pipeline
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.pipeline.config import get_default_config


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Create a configuration file for the content curation pipeline")
    
    # Project settings
    parser.add_argument("--name", type=str, default="content-curation",
                        help="Project name")
    parser.add_argument("--data-dir", type=str, default="./data",
                        help="Data directory path")
    parser.add_argument("--output-dir", type=str,
                        help="Output directory path (defaults to data_dir/output)")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    
    # Source configuration
    parser.add_argument("--sources", type=str, default="substack,medium,youtube,papers,reddit",
                        help="Comma-separated list of sources to enable")
    
    # Output configuration
    parser.add_argument("--enable-evaluation", action="store_true",
                        help="Enable content evaluation")
    parser.add_argument("--enable-chunking", action="store_true",
                        help="Enable content chunking")
    parser.add_argument("--enable-embedding", action="store_true",
                        help="Enable content embedding")
    
    # Output file
    parser.add_argument("--output", "-o", type=str, default="config.yaml",
                        help="Output file path")
    
    return parser.parse_args()


def create_config(args):
    """
    Create a configuration file based on command line arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        Path to the created configuration file
    """
    # Get default configuration
    config = get_default_config()
    
    # Update configuration with command line arguments
    config.project_name = args.name
    config.data_dir = args.data_dir
    config.output_dir = args.output_dir
    config.log_level = args.log_level
    
    # Enable/disable sources
    enabled_sources = [s.strip() for s in args.sources.split(",")]
    for source_id in config.sources:
        if source_id in enabled_sources:
            config.sources[source_id].enabled = True
        else:
            config.sources[source_id].enabled = False
    
    # Enable/disable processors accordingly
    for processor_id in config.processors:
        if processor_id in enabled_sources:
            config.processors[processor_id].enabled = True
        else:
            config.processors[processor_id].enabled = False
    
    # Set evaluation, chunking, and embedding settings
    config.evaluation.enabled = args.enable_evaluation
    config.chunking.enabled = args.enable_chunking
    config.embedding.enabled = args.enable_embedding
    
    # Convert to dictionary for YAML export
    config_dict = {
        "project_name": config.project_name,
        "data_dir": config.data_dir,
        "output_dir": config.output_dir,
        "log_level": config.log_level,
        "sources": {},
        "processors": {},
        "evaluation": vars(config.evaluation),
        "chunking": vars(config.chunking),
        "embedding": vars(config.embedding),
        "extra_params": config.extra_params
    }
    
    # Convert source and processor configs
    for source_id, source in config.sources.items():
        config_dict["sources"][source_id] = vars(source)
    
    for processor_id, processor in config.processors.items():
        config_dict["processors"][processor_id] = vars(processor)
    
    # Clean up nested objects that don't serialize well
    for section in ["evaluation", "chunking", "embedding"]:
        if "extra_params" in config_dict[section] and isinstance(config_dict[section]["extra_params"], dict):
            config_dict[section]["extra_params"] = dict(config_dict[section]["extra_params"])
    
    # Create output directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write configuration to file
    with open(output_path, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    
    return output_path


def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        config_path = create_config(args)
        print(f"Configuration file created at: {config_path}")
        return 0
    except Exception as e:
        print(f"Error creating configuration file: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 