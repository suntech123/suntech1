# llm/factory.py
from .base import BaseLLMProvider
from .gemini import UHGGeminiProvider
from .openai import OpenAIProvider

def get_llm(provider_name: str) -> BaseLLMProvider:
    """Factory function to get the requested LLM provider."""
    
    provider_name = provider_name.lower()
    
    if provider_name == "gemini":
        return UHGGeminiProvider()
    elif provider_name == "openai":
        return OpenAIProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}. Choose 'gemini' or 'openai'.")