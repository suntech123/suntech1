# llm/openai.py
from openai import OpenAI
from .base import BaseLLMProvider
from config import settings

class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model_name = settings.openai_model

    def generate_text(self, prompt: str) -> str:
        """Implementation of the interface for OpenAI."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content