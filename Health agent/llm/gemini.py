# llm/gemini.py
import time
import requests
from google import genai
from google.genai import types
from .base import BaseLLMProvider
from config import settings

class UHGGeminiProvider(BaseLLMProvider):
    def __init__(self):
        self._access_token = None
        self._token_expiry = 0
        self.model_name = settings.gemini_model
        # Initialize client immediately or lazily
        self.client = self._get_client()

    def _fetch_hcp_token(self):
        # ... (Same token fetching logic as previous answer) ...
        data = {"grant_type": settings.hcp_grant_type, "client_id": settings.hcp_client_id, "client_secret": settings.hcp_client_secret, "scope": settings.hcp_scope}
        resp = requests.post(settings.hcp_auth_url, data=data)
        resp.raise_for_status()
        token_data = resp.json()
        self._access_token = token_data["access_token"]
        self._token_expiry = time.time() + int(token_data.get("expires_in", 3600))
        return self._access_token

    def _get_client(self) -> genai.Client:
        # Check token expiry and refresh if needed
        if not self._access_token or time.time() >= (self._token_expiry - 60):
            self._fetch_hcp_token()
            
        return genai.Client(
            api_key=self._access_token,
            http_options=types.HttpOptions(
                base_url=settings.uhg_base_url,
                api_version='v1beta',
                headers={"projectId": settings.uhg_project_id, "Authorization": f"Bearer {self._access_token}"}
            )
        )

    def generate_text(self, prompt: str) -> str:
        """Implementation of the interface for Gemini."""
        # Ensure we have a valid token before making the call
        if time.time() >= (self._token_expiry - 60):
            self.client = self._get_client() 
            
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        return response.text