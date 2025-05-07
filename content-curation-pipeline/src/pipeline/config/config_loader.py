"""
Configuration loader for the content curation pipeline.

This module handles loading and validating configuration files, 
with support for JSON and YAML formats.
"""

import json
import logging
import copy
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

import yaml

from .schema import (
    ConfigSchema, 
    SourceConfig, 
    ProcessorConfig, 
    EvaluationConfig,
    ChunkingConfig,
    EmbeddingConfig
)

logger = logging.getLogger(__name__)


def get_default_config() -> ConfigSchema:
    """
    Return a default configuration with predefined sources and processors.
    
    Returns:
        ConfigSchema: Default configuration
    """
    # Default sources
    sources = {
        "substack": SourceConfig(
            type="substack",
            name="Substack Newsletters",
            enabled=True,
            limit=10,
            seed_queries=["engineering management", "tech leadership"],
            custom_urls=[],
            source_params={
                "curated_newsletters": [
                    "lethain",
                    "thegeneralist",
                    "alexanderjarvis",
                    "komoroske",
                    "highgrowthengineering",
                    "theengineeringmanager",
                    "managementmatters",
                ]
            }
        ),
        "medium": SourceConfig(
            type="medium",
            name="Medium Articles",
            enabled=True,
            limit=10,
            seed_queries=["software engineering", "engineering leadership"],
            custom_urls=[],
            source_params={
                "tags": [
                    "software-engineering",
                    "software-development",
                    "engineering-management",
                    "engineering-leadership",
                    "tech-leadership",
                ]
            }
        ),
        "youtube": SourceConfig(
            type="youtube",
            name="YouTube Videos",
            enabled=True,
            limit=10,
            seed_queries=["software engineering career", "engineering leadership"],
            custom_urls=[],
            source_params={}
        ),
        "papers": SourceConfig(
            type="papers",
            name="Technical Papers",
            enabled=True,
            limit=5,
            seed_queries=["software engineering methods", "software team productivity"],
            custom_urls=[],
            source_params={}
        ),
        "reddit": SourceConfig(
            type="reddit",
            name="Reddit Discussions",
            enabled=True,
            limit=10,
            seed_queries=["engineering career growth", "software engineering promotion"],
            custom_urls=[],
            source_params={
                "recommended_subreddits": [
                    "cscareerquestions",
                    "ExperiencedDevs", 
                    "AskEngineers",
                    "softwareengineering",
                    "engineeringmanagement",
                    "programming",
                    "datascience",
                    "devops",
                    "careeradvice"
                ]
            }
        )
    }
    
    # Default processors
    processors = {
        "substack": ProcessorConfig(
            type="substack",
            enabled=True,
            extract_metadata=True,
            extract_text=True,
            processor_params={}
        ),
        "medium": ProcessorConfig(
            type="medium",
            enabled=True,
            extract_metadata=True,
            extract_text=True,
            processor_params={}
        ),
        "youtube": ProcessorConfig(
            type="youtube",
            enabled=True,
            extract_metadata=True,
            extract_text=True,
            processor_params={}
        ),
        "papers": ProcessorConfig(
            type="papers",
            enabled=True,
            extract_metadata=True,
            extract_text=True,
            processor_params={}
        ),
        "reddit": ProcessorConfig(
            type="reddit",
            enabled=True,
            extract_metadata=True,
            extract_text=True,
            processor_params={}
        )
    }
    
    # Default evaluation
    evaluation = EvaluationConfig(
        enabled=True,
        method="standard",
        criteria={
            "relevance": 1.0,
            "quality": 1.0,
            "depth": 1.0,
            "practicality": 1.0
        },
        min_score=0.7,
        batch_size=10,
        model="gpt-4o",
        temperature=0.3,
        eval_params={}
    )
    
    # Default chunking
    chunking = ChunkingConfig(
        enabled=False,
        strategy="sliding_window",
        chunk_size=1000,
        chunk_overlap=100,
        extra_params={}
    )
    
    # Default embedding
    embedding = EmbeddingConfig(
        enabled=False,
        model="text-embedding-3-small",
        dimensions=1536,
        batch_size=100,
        extra_params={}
    )
    
    # Build default config
    return ConfigSchema(
        project_name="content-curation",
        data_dir="./data",
        output_dir=None,
        log_level="INFO",
        sources=sources,
        processors=processors,
        evaluation=evaluation,
        chunking=chunking,
        embedding=embedding,
        extra_params={}
    )


def load_config(config_path: Union[str, Path]) -> ConfigSchema:
    """
    Load configuration from a file, supporting both YAML and JSON formats.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        ConfigSchema: The loaded and validated configuration
        
    Raises:
        ValueError: If the configuration file is invalid or cannot be loaded
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise ValueError(f"Configuration file does not exist: {config_path}")
    
    try:
        # Load configuration from file
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ('.yaml', '.yml'):
                config_data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                config_data = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
        
        # Validate and convert configuration
        return validate_config(config_data)
    
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {str(e)}")
        raise ValueError(f"Failed to load configuration: {str(e)}")


def validate_config(config_data: Dict[str, Any]) -> ConfigSchema:
    """
    Validate and convert a configuration dictionary to a ConfigSchema object.
    
    Args:
        config_data: Configuration data as a dictionary
        
    Returns:
        ConfigSchema: The validated configuration
        
    Raises:
        ValueError: If the configuration is invalid
    """
    try:
        # Validate required fields
        if 'project_name' not in config_data:
            raise ValueError("Configuration missing required field: project_name")
        
        # Process sources
        sources = {}
        if 'sources' in config_data:
            for source_id, source_data in config_data['sources'].items():
                # Ensure type is present
                if 'type' not in source_data:
                    raise ValueError(f"Source {source_id} is missing required field: type")
                
                # Convert to SourceConfig
                sources[source_id] = SourceConfig(
                    type=source_data['type'],
                    name=source_data.get('name', source_id),
                    enabled=source_data.get('enabled', True),
                    limit=source_data.get('limit', 10),
                    seed_queries=source_data.get('seed_queries', []),
                    custom_urls=source_data.get('custom_urls', []),
                    source_params=source_data.get('source_params', {})
                )
        
        # Process processors
        processors = {}
        if 'processors' in config_data:
            for processor_id, processor_data in config_data['processors'].items():
                # Ensure type is present
                if 'type' not in processor_data:
                    raise ValueError(f"Processor {processor_id} is missing required field: type")
                
                # Convert to ProcessorConfig
                processors[processor_id] = ProcessorConfig(
                    type=processor_data['type'],
                    enabled=processor_data.get('enabled', True),
                    extract_metadata=processor_data.get('extract_metadata', True),
                    extract_text=processor_data.get('extract_text', True),
                    processor_params=processor_data.get('processor_params', {})
                )
        
        # Process evaluation
        evaluation = EvaluationConfig()
        if 'evaluation' in config_data:
            eval_data = config_data['evaluation']
            evaluation = EvaluationConfig(
                enabled=eval_data.get('enabled', False),
                method=eval_data.get('method', 'standard'),
                criteria=eval_data.get('criteria', evaluation.criteria),
                min_score=eval_data.get('min_score', 0.7),
                batch_size=eval_data.get('batch_size', 10),
                model=eval_data.get('model', 'gpt-4o'),
                temperature=eval_data.get('temperature', 0.3),
                eval_params=eval_data.get('eval_params', {})
            )
        
        # Process chunking
        chunking = ChunkingConfig()
        if 'chunking' in config_data:
            chunk_data = config_data['chunking']
            chunking = ChunkingConfig(
                enabled=chunk_data.get('enabled', False),
                strategy=chunk_data.get('strategy', 'sliding_window'),
                chunk_size=chunk_data.get('chunk_size', 1000),
                chunk_overlap=chunk_data.get('chunk_overlap', 100),
                extra_params=chunk_data.get('extra_params', {})
            )
        
        # Process embedding
        embedding = EmbeddingConfig()
        if 'embedding' in config_data:
            embed_data = config_data['embedding']
            embedding = EmbeddingConfig(
                enabled=embed_data.get('enabled', False),
                model=embed_data.get('model', 'text-embedding-3-small'),
                dimensions=embed_data.get('dimensions', 1536),
                batch_size=embed_data.get('batch_size', 100),
                extra_params=embed_data.get('extra_params', {})
            )
        
        # Create ConfigSchema
        config = ConfigSchema(
            project_name=config_data['project_name'],
            data_dir=config_data.get('data_dir', './data'),
            output_dir=config_data.get('output_dir'),
            log_level=config_data.get('log_level', 'INFO'),
            sources=sources,
            processors=processors,
            evaluation=evaluation,
            chunking=chunking,
            embedding=embedding,
            extra_params=config_data.get('extra_params', {})
        )
        
        # Ensure all enabled sources have corresponding processors
        for source_id, source in config.sources.items():
            if source.enabled and source_id not in config.processors:
                logger.warning(f"Enabled source {source_id} has no corresponding processor")
        
        return config
        
    except Exception as e:
        logger.error(f"Error validating configuration: {str(e)}")
        raise ValueError(f"Invalid configuration: {str(e)}")


def merge_configs(base_config: ConfigSchema, override_config: ConfigSchema) -> ConfigSchema:
    """
    Merge two configurations, with override_config taking precedence.
    
    Args:
        base_config: Base configuration
        override_config: Override configuration with higher priority
        
    Returns:
        ConfigSchema: Merged configuration
    """
    # Create deep copy of base config to avoid modifications
    merged = copy.deepcopy(base_config)
    
    # Update core settings
    merged.project_name = override_config.project_name
    if override_config.data_dir != base_config.data_dir:
        merged.data_dir = override_config.data_dir
    if override_config.output_dir is not None:
        merged.output_dir = override_config.output_dir
    if override_config.log_level != base_config.log_level:
        merged.log_level = override_config.log_level
    
    # Merge sources
    for source_id, source in override_config.sources.items():
        merged.sources[source_id] = copy.deepcopy(source)
    
    # Merge processors
    for processor_id, processor in override_config.processors.items():
        merged.processors[processor_id] = copy.deepcopy(processor)
    
    # Update evaluation
    if override_config.evaluation.enabled != base_config.evaluation.enabled:
        merged.evaluation.enabled = override_config.evaluation.enabled
    if override_config.evaluation.method != base_config.evaluation.method:
        merged.evaluation.method = override_config.evaluation.method
    merged.evaluation.criteria.update(override_config.evaluation.criteria)
    merged.evaluation.min_score = override_config.evaluation.min_score
    merged.evaluation.batch_size = override_config.evaluation.batch_size
    merged.evaluation.model = override_config.evaluation.model
    merged.evaluation.temperature = override_config.evaluation.temperature
    merged.evaluation.eval_params.update(override_config.evaluation.eval_params)
    
    # Update chunking
    if override_config.chunking.enabled != base_config.chunking.enabled:
        merged.chunking.enabled = override_config.chunking.enabled
    if override_config.chunking.strategy != base_config.chunking.strategy:
        merged.chunking.strategy = override_config.chunking.strategy
    merged.chunking.chunk_size = override_config.chunking.chunk_size
    merged.chunking.chunk_overlap = override_config.chunking.chunk_overlap
    merged.chunking.extra_params.update(override_config.chunking.extra_params)
    
    # Update embedding
    if override_config.embedding.enabled != base_config.embedding.enabled:
        merged.embedding.enabled = override_config.embedding.enabled
    if override_config.embedding.model != base_config.embedding.model:
        merged.embedding.model = override_config.embedding.model
    merged.embedding.dimensions = override_config.embedding.dimensions
    merged.embedding.batch_size = override_config.embedding.batch_size
    merged.embedding.extra_params.update(override_config.embedding.extra_params)
    
    # Merge extra_params
    merged.extra_params.update(override_config.extra_params)
    
    return merged 