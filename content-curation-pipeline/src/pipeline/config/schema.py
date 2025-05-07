"""
Configuration schema definitions for the content curation pipeline.

This module defines data models for pipeline configuration, including
source configuration, processor configuration, and evaluation options.
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SourceConfig:
    """Configuration for a content source."""
    
    # Core settings
    type: str
    name: str = field(default="")
    enabled: bool = True
    
    # Query settings
    seed_queries: List[str] = field(default_factory=list)
    custom_urls: List[str] = field(default_factory=list)
    
    # Collection settings
    limit: int = 10
    timeout: int = 30
    max_retries: int = 3
    cache_ttl: int = 86400
    
    # Source-specific settings
    source_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessorConfig:
    """Configuration for content processors."""
    
    # Core settings
    type: str
    enabled: bool = True
    
    # Processing settings
    extract_metadata: bool = True
    extract_text: bool = True
    max_content_length: int = 100000
    
    # Processor-specific settings
    processor_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationConfig:
    """Configuration for content evaluation."""
    
    # Core settings
    enabled: bool = False
    method: str = "standard"  # "standard", "web", "browsing", "dual_perspective"
    
    # Evaluation settings
    criteria: Dict[str, float] = field(default_factory=lambda: {
        "relevance": 1.0,
        "quality": 1.0,
        "depth": 1.0,
        "practicality": 1.0
    })
    min_score: float = 0.7
    batch_size: int = 10
    
    # LLM settings
    model: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int = 1000
    
    eval_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkingConfig:
    """Configuration for content chunking."""
    
    enabled: bool = False
    strategy: str = "sliding_window"
    chunk_size: int = 1000
    chunk_overlap: int = 100
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingConfig:
    """Configuration for content embedding."""
    
    enabled: bool = False
    model: str = "text-embedding-3-small"
    dimensions: int = 1536
    batch_size: int = 100
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigSchema:
    """Complete configuration schema for the content curation pipeline."""
    
    # Core settings
    project_name: str
    data_dir: str = "./data"
    output_dir: Optional[str] = None
    log_level: str = "INFO"
    
    # Source configurations
    sources: Dict[str, SourceConfig] = field(default_factory=dict)
    
    # Processor configurations
    processors: Dict[str, ProcessorConfig] = field(default_factory=dict)
    
    # Evaluation configuration
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    
    # Chunking configuration
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    
    # Embedding configuration
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def get_output_dir(self) -> Path:
        """Get the output directory path."""
        if self.output_dir:
            return Path(self.output_dir)
        return Path(self.data_dir) / "output" 