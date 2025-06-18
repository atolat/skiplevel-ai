"""Configuration management for Agent Factory."""

import os
from pathlib import Path
from typing import Optional, Tuple, List

import yaml
from pydantic import BaseModel, Field, field_validator, ValidationError

from .traits import get_traits_registry
from .models import get_models_registry
from .memory_config import MemoryConfig


class LLMConfig(BaseModel):
    """Configuration for LLM provider."""
    
    provider: str = Field(default="openai", description="LLM provider name")
    model_name: str = Field(default="gpt-3.5-turbo", description="Model name to use")
    api_key: Optional[str] = Field(default=None, description="API key (from environment)")


class CognitiveCoreConfig(BaseModel):
    """Configuration for agent's cognitive core."""
    
    model: str = Field(..., description="The LLM model name like 'claude-3-sonnet', 'gpt-4', etc.")
    system_prompt: str = Field(..., description="The agent's core instructions")


class AgentConfig(BaseModel):
    """Configuration model for an AI agent."""
    
    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Human-readable name for the agent")
    description: Optional[str] = Field(None, description="Optional description of the agent")
    max_tokens: int = Field(default=1000, description="Maximum tokens per response")
    temperature: float = Field(default=0.7, description="LLM temperature setting")
    tools: List[str] = Field(default_factory=list, description="List of available tools")
    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM configuration")
    cognitive_core: Optional[CognitiveCoreConfig] = Field(None, description="Cognitive core configuration")
    traits: List[str] = Field(default_factory=list, description="List of personality trait names from the registry")
    memory: MemoryConfig = Field(default_factory=MemoryConfig, description="Memory system configuration")
    
    @field_validator("temperature")
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is between 0.0 and 2.0."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v


def validate_model_availability(model: str) -> Tuple[bool, str]:
    """Validate if a model is available (has API key) using the models registry.
    
    Args:
        model: The LLM model name (e.g., "claude-3-sonnet", "gpt-4", etc.)
        
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    try:
        models_registry = get_models_registry()
        return models_registry.validate_model(model)
    except Exception as e:
        return False, f"Error validating model: {e}"


def validate_traits(trait_names: List[str]) -> Tuple[bool, str]:
    """Validate that all specified traits exist in the traits registry.
    
    Args:
        trait_names: List of trait names to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not trait_names:
        return True, ""
    
    try:
        traits_registry = get_traits_registry()
        valid_traits, invalid_traits = traits_registry.validate_traits(trait_names)
        
        if invalid_traits:
            return False, f"Unknown traits: {', '.join(invalid_traits)}. Available traits: {', '.join(sorted(traits_registry.list_available_traits().keys()))}"
        
        return True, ""
        
    except Exception as e:
        return False, f"Error validating traits: {e}"


def load_config(yaml_path: str) -> Optional[AgentConfig]:
    """Load and validate agent configuration from YAML file.
    
    Args:
        yaml_path: Path to the YAML configuration file
        
    Returns:
        Validated AgentConfig object, or None if loading/validation fails
    """
    try:
        config_file = Path(yaml_path)
        
        if not config_file.exists():
            print(f"Error: Configuration file not found: {yaml_path}")
            return None
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        if not isinstance(config_data, dict):
            print("Error: YAML file must contain a configuration object")
            return None
        
        # Validate model availability if cognitive_core is specified
        if "cognitive_core" in config_data and "model" in config_data["cognitive_core"]:
            model = config_data["cognitive_core"]["model"]
            is_valid, error_message = validate_model_availability(model)
            if not is_valid:
                print(f"Error: Configuration validation failed: {error_message}")
                return None
        
        # Validate traits if specified
        if "traits" in config_data and config_data["traits"]:
            trait_names = config_data["traits"]
            if not isinstance(trait_names, list):
                print("Error: Configuration validation failed: 'traits' must be a list")
                return None
            
            is_valid, error_message = validate_traits(trait_names)
            if not is_valid:
                print(f"Error: Configuration validation failed: {error_message}")
                return None
        
        return AgentConfig(**config_data)
        
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {yaml_path}")
        return None
    
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML format: {e}")
        return None
    
    except ValidationError as e:
        print(f"Error: Configuration validation failed: {e}")
        return None
    
    except Exception as e:
        print(f"Error: Configuration validation failed: {e}")
        return None 