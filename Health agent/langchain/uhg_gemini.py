'''
We will create a class called UHGChatGemini that inherits from LangChain's BaseChatModel. LangChain only requires you to implement two things: the _llm_type property and the _generate method.
We will embed the token manager (from the first answer) directly inside this class using Pydantic's PrivateAttr so LangChain can manage it.
'''

# uhg_gemini.py
import time
import requests
from typing import Any, List, Optional
from pydantic import PrivateAttr

# Langchain core imports
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

# Your specific GenAI imports
from google import genai
from google.genai import types

from config import settings # Using the config.py from the previous answers

class UHGChatGemini(BaseChatModel):
    """A custom LangChain Chat Model for the UHG API Gateway."""
    
    model_name: str = "gemini-2.5-flash"
    
    # Private attributes (not parsed by Langchain's Pydantic validation)
    _access_token: str = PrivateAttr(default="")
    _token_expiry: float = PrivateAttr(default=0.0)

    def _fetch_hcp_token(self) -> str:
        """Fetches and caches the OAuth token."""
        data = {
            "grant_type": settings.hcp_grant_type,
            "client_id": settings.hcp_client_id,
            "client_secret": settings.hcp_client_secret,
            "scope": settings.hcp_scope
        }
        resp = requests.post(settings.hcp_auth_url, data=data, timeout=10)
        resp.raise_for_status()
        token_data = resp.json()
        
        self._access_token = token_data["access_token"]
        self._token_expiry = time.time() + int(token_data.get("expires_in", 3600))
        return self._access_token

    def _get_client(self) -> genai.Client:
        """Returns the authenticated Google GenAI client."""
        # Refresh token if missing or expiring within 60 seconds
        if not self._access_token or time.time() >= (self._token_expiry - 60):
            self._fetch_hcp_token()
            
        return genai.Client(
            api_key=self._access_token,
            http_options=types.HttpOptions(
                base_url=settings.uhg_base_url,
                api_version='v1beta',
                headers={
                    "projectId": settings.uhg_project_id, 
                    "Authorization": f"Bearer {self._access_token}"
                }
            )
        )

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """The core method LangChain calls to generate text."""
        
        # 1. Convert LangChain messages into a string prompt
        # (For advanced use, you can map SystemMessage/HumanMessage to Gemini roles)
        prompt = "\n".join([m.content for m in messages])
        
        # 2. Get the authenticated client
        client = self._get_client()
        
        # 3. Call the UHG API
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        
        # 4. Format the response back into LangChain standard objects
        message = AIMessage(content=response.text)
        generation = ChatGeneration(message=message)
        
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "uhg_custom_gemini"