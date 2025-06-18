"""Models registry management for Agent Factory."""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


logger = logging.getLogger(__name__)


class ModelsRegistry:
    """Registry for managing available AI models based on API key availability."""
    
    def __init__(self, models_file: str = "configs/models_registry.yaml"):
        """Initialize the models registry.
        
        Args:
            models_file: Path to the models registry YAML file
        """
        self.models_file = models_file
        self.models_data: Dict[str, Dict[str, Dict[str, any]]] = {}
        self.available_models: Dict[str, Dict[str, any]] = {}
        self._load_models()
    
    def _load_models(self) -> None:
        """Load models from the YAML file and filter by API key availability."""
        try:
            models_path = Path(self.models_file)
            
            if not models_path.exists():
                logger.error(f"Models registry file not found: {self.models_file}")
                return
            
            with open(models_path, 'r', encoding='utf-8') as f:
                self.models_data = yaml.safe_load(f) or {}
            
            # Filter models by API key availability
            self._filter_available_models()
            
            logger.info(f"Loaded models registry from {self.models_file}")
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing models registry YAML: {e}")
            self.models_data = {}
            self.available_models = {}
        except Exception as e:
            logger.error(f"Error loading models registry: {e}")
            self.models_data = {}
            self.available_models = {}
    
    def _filter_available_models(self) -> None:
        """Filter models based on API key availability."""
        self.available_models = {}
        
        for category_name, category_models in self.models_data.items():
            if isinstance(category_models, dict):
                for model_name, model_data in category_models.items():
                    if isinstance(model_data, dict) and 'api_key_env' in model_data:
                        api_key_env = model_data['api_key_env']
                        if os.getenv(api_key_env):
                            self.available_models[model_name] = model_data
    
    def get_available_models(self) -> Dict[str, Dict[str, any]]:
        """Get all available models (those with API keys present).
        
        Returns:
            Dictionary mapping model names to their configuration data
        """
        return self.available_models.copy()
    
    def get_models_by_provider(self) -> Dict[str, List[str]]:
        """Get available models organized by provider.
        
        Returns:
            Dictionary mapping provider names to lists of model names
        """
        models_by_provider = {}
        
        for model_name, model_data in self.available_models.items():
            provider = model_data.get('provider', 'unknown')
            if provider not in models_by_provider:
                models_by_provider[provider] = []
            models_by_provider[provider].append(model_name)
        
        return models_by_provider
    
    def get_models_by_cost_tier(self) -> Dict[str, List[str]]:
        """Get available models organized by cost tier.
        
        Returns:
            Dictionary mapping cost tiers to lists of model names
        """
        models_by_cost = {}
        
        for model_name, model_data in self.available_models.items():
            cost_tier = model_data.get('cost_tier', 'unknown')
            if cost_tier not in models_by_cost:
                models_by_cost[cost_tier] = []
            models_by_cost[cost_tier].append(model_name)
        
        return models_by_cost
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available (has API key).
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if model is available, False otherwise
        """
        return model_name in self.available_models
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, any]]:
        """Get detailed information about a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model configuration data or None if not available
        """
        return self.available_models.get(model_name)
    
    def validate_model(self, model_name: str) -> Tuple[bool, str]:
        """Validate if a model can be used.
        
        Args:
            model_name: Name of the model to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not model_name:
            return False, "Model name is required"
        
        if model_name not in self.available_models:
            available_models = list(self.available_models.keys())
            if available_models:
                return False, f"Model '{model_name}' is not available. Available models: {', '.join(sorted(available_models))}"
            else:
                return False, f"Model '{model_name}' is not available. No models are currently available (check API keys)"
        
        return True, ""
    
    def get_missing_api_keys(self) -> Dict[str, List[str]]:
        """Get models that are defined but missing API keys.
        
        Returns:
            Dictionary mapping API key environment variables to lists of unavailable models
        """
        missing_keys = {}
        
        for category_name, category_models in self.models_data.items():
            if isinstance(category_models, dict):
                for model_name, model_data in category_models.items():
                    if isinstance(model_data, dict) and 'api_key_env' in model_data:
                        api_key_env = model_data['api_key_env']
                        if not os.getenv(api_key_env):
                            if api_key_env not in missing_keys:
                                missing_keys[api_key_env] = []
                            missing_keys[api_key_env].append(model_name)
        
        return missing_keys


# Singleton instance
_models_registry: Optional[ModelsRegistry] = None


def get_models_registry() -> ModelsRegistry:
    """Get the singleton models registry instance.
    
    Returns:
        ModelsRegistry instance
    """
    global _models_registry
    
    if _models_registry is None:
        _models_registry = ModelsRegistry()
    
    return _models_registry 