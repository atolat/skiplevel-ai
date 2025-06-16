"""Personality traits management for Agent Factory."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml


logger = logging.getLogger(__name__)


class TraitsRegistry:
    """Registry for managing agent personality traits."""
    
    def __init__(self, traits_file: str = "configs/traits_registry.yaml"):
        """Initialize the traits registry.
        
        Args:
            traits_file: Path to the traits registry YAML file
        """
        self.traits_file = traits_file
        self.traits_data: Dict[str, Dict[str, Dict[str, str]]] = {}
        self._load_traits()
    
    def _load_traits(self) -> None:
        """Load traits from the YAML file."""
        try:
            traits_path = Path(self.traits_file)
            
            if not traits_path.exists():
                logger.error(f"Traits registry file not found: {self.traits_file}")
                return
            
            with open(traits_path, 'r', encoding='utf-8') as f:
                self.traits_data = yaml.safe_load(f) or {}
            
            logger.info(f"Loaded traits registry from {self.traits_file}")
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing traits registry YAML: {e}")
            self.traits_data = {}
        except Exception as e:
            logger.error(f"Error loading traits registry: {e}")
            self.traits_data = {}
    
    def resolve_traits(self, trait_names: List[str]) -> List[str]:
        """Resolve trait names to their instruction strings.
        
        Args:
            trait_names: List of trait names to resolve
            
        Returns:
            List of instruction strings for valid traits
        """
        instructions = []
        
        if not self.traits_data:
            logger.warning("No traits data loaded, returning empty instructions")
            return instructions
        
        for trait_name in trait_names:
            instruction = self._find_trait_instruction(trait_name)
            if instruction:
                instructions.append(instruction)
            else:
                logger.warning(f"Trait '{trait_name}' not found in registry, skipping")
        
        return instructions
    
    def _find_trait_instruction(self, trait_name: str) -> Optional[str]:
        """Find the instruction for a specific trait.
        
        Args:
            trait_name: Name of the trait to find
            
        Returns:
            Instruction string if found, None otherwise
        """
        for category_name, category_traits in self.traits_data.items():
            if isinstance(category_traits, dict) and trait_name in category_traits:
                trait_data = category_traits[trait_name]
                if isinstance(trait_data, dict) and 'instruction' in trait_data:
                    return trait_data['instruction']
        
        return None
    
    def list_available_traits(self) -> Dict[str, str]:
        """Get all available traits with their descriptions.
        
        Returns:
            Dictionary mapping trait names to their descriptions
        """
        available_traits = {}
        
        for category_name, category_traits in self.traits_data.items():
            if isinstance(category_traits, dict):
                for trait_name, trait_data in category_traits.items():
                    if isinstance(trait_data, dict) and 'description' in trait_data:
                        available_traits[trait_name] = trait_data['description']
        
        return available_traits
    
    def get_traits_by_category(self) -> Dict[str, List[str]]:
        """Get traits organized by category.
        
        Returns:
            Dictionary mapping category names to lists of trait names
        """
        traits_by_category = {}
        
        for category_name, category_traits in self.traits_data.items():
            if isinstance(category_traits, dict):
                trait_names = [
                    trait_name for trait_name, trait_data in category_traits.items()
                    if isinstance(trait_data, dict) and 'instruction' in trait_data
                ]
                if trait_names:
                    traits_by_category[category_name] = trait_names
        
        return traits_by_category
    
    def validate_traits(self, trait_names: List[str]) -> tuple[List[str], List[str]]:
        """Validate a list of trait names.
        
        Args:
            trait_names: List of trait names to validate
            
        Returns:
            Tuple of (valid_traits, invalid_traits)
        """
        valid_traits = []
        invalid_traits = []
        
        for trait_name in trait_names:
            if self._find_trait_instruction(trait_name):
                valid_traits.append(trait_name)
            else:
                invalid_traits.append(trait_name)
        
        return valid_traits, invalid_traits


# Singleton instance
_traits_registry: Optional[TraitsRegistry] = None


def get_traits_registry() -> TraitsRegistry:
    """Get the singleton traits registry instance.
    
    Returns:
        TraitsRegistry instance
    """
    global _traits_registry
    
    if _traits_registry is None:
        _traits_registry = TraitsRegistry()
    
    return _traits_registry 