"""LLM interface and implementations for Agent Factory."""

from abc import ABC, abstractmethod
from typing import Optional

import openai


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, model_name: str):
        """Initialize the LLM with a model name."""
        self._model_name = model_name
    
    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name
    
    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate a response from the LLM.
        
        Args:
            prompt: The input prompt
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        pass


class OpenAILLM(BaseLLM):
    """OpenAI LLM implementation."""
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        """Initialize OpenAI LLM.
        
        Args:
            api_key: OpenAI API key
            model_name: OpenAI model name to use
        """
        super().__init__(model_name)
        self.client = openai.OpenAI(api_key=api_key)
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate a response using OpenAI's API.
        
        Args:
            prompt: The input prompt
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text or error message
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content or "No response generated"
            
        except openai.AuthenticationError:
            return "Error: Invalid OpenAI API key"
        
        except openai.RateLimitError:
            return "Error: OpenAI API rate limit exceeded"
        
        except openai.APIError as e:
            return f"Error: OpenAI API error - {str(e)}"
        
        except Exception as e:
            return f"Error: Unexpected error - {str(e)}"


def get_llm(provider: str = "openai", **kwargs) -> Optional[BaseLLM]:
    """Factory function to create LLM instances.
    
    Args:
        provider: LLM provider name ("openai" for now)
        **kwargs: Arguments to pass to the LLM constructor
        
    Returns:
        BaseLLM instance or None if provider not supported
    """
    if provider.lower() == "openai":
        return OpenAILLM(**kwargs)
    else:
        print(f"Error: Unsupported LLM provider: {provider}")
        return None 