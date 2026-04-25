# llm/base.py
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    
    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """Takes a prompt and returns the text response."""
        pass