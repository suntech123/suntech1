import time
import requests
import uuid
from typing import Any, List, Optional
from pydantic import PrivateAttr

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatResult, ChatGeneration

from google import genai
from google.genai import types
from config import settings

class UHGChatGemini(BaseChatModel):
    model_name: str = "gemini-2.5-flash"
    _access_token: str = PrivateAttr(default="")
    _token_expiry: float = PrivateAttr(default=0.0)

    def _fetch_hcp_token(self) -> str:
        data = {"grant_type": settings.hcp_grant_type, "client_id": settings.hcp_client_id, "client_secret": settings.hcp_client_secret, "scope": settings.hcp_scope}
        resp = requests.post(settings.hcp_auth_url, data=data, timeout=10)
        resp.raise_for_status()
        self._access_token = resp.json()["access_token"]
        self._token_expiry = time.time() + int(resp.json().get("expires_in", 3600))
        return self._access_token

    def _get_client(self) -> genai.Client:
        if not self._access_token or time.time() >= (self._token_expiry - 60):
            self._fetch_hcp_token()
        return genai.Client(
            api_key=self._access_token,
            http_options=types.HttpOptions(
                base_url=settings.uhg_base_url, api_version='v1beta',
                headers={"projectId": settings.uhg_project_id, "Authorization": f"Bearer {self._access_token}"}
            )
        )

    def bind_tools(self, tools: list, **kwargs):
        """Standard LangChain requirement. Attaches tools to the LLM."""
        # LangChain passes @tool objects. Google's SDK accepts raw python functions.
        # We extract the raw function (.func) so Google can auto-generate the JSON schema.
        extracted_tools = [getattr(t, "func", t) for t in tools]
        return super().bind(tools=extracted_tools, **kwargs)

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        contents = []
        system_instruction = None

        # 1. TRANSLATE LANGCHAIN MESSAGES -> GOOGLE FORMAT
        for m in messages:
            if isinstance(m, SystemMessage):
                system_instruction = m.content
            elif isinstance(m, HumanMessage):
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=m.content)]))
            elif isinstance(m, ToolMessage):
                # When passing tool results back to Google, role must be "user"
                parts = [types.Part.from_function_response(name=m.name, response={"result": m.content})]
                contents.append(types.Content(role="user", parts=parts))
            elif isinstance(m, AIMessage):
                if m.tool_calls:
                    # Previous AI message asked for a tool
                    parts = [types.Part.from_function_call(name=tc["name"], args=tc["args"]) for tc in m.tool_calls]
                    contents.append(types.Content(role="model", parts=parts))
                else:
                    # Standard AI text response
                    contents.append(types.Content(role="model", parts=[types.Part.from_text(text=m.content)]))

        # 2. CONFIGURE API CALL
        config_args = {"temperature": 0.0}
        if system_instruction:
            config_args["system_instruction"] = system_instruction
        if "tools" in kwargs:
            config_args["tools"] = kwargs["tools"] # Injected by bind_tools()

        # 3. CALL UHG GATEWAY
        response = self._get_client().models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(**config_args)
        )

        # 4. TRANSLATE GOOGLE RESPONSE -> LANGCHAIN FORMAT
        tool_calls = []
        text_content = ""
        
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    # LangChain requires a unique ID for every tool call
                    tool_calls.append({
                        "name": part.function_call.name,
                        "args": dict(part.function_call.args),
                        "id": f"call_{uuid.uuid4().hex[:8]}"
                    })
                elif part.text:
                    text_content += part.text

        # Return standard AIMessage (If tool_calls is populated, LangGraph takes over)
        message = AIMessage(content=text_content, tool_calls=tool_calls)
        return ChatResult(generations=[ChatGeneration(message=message)])

    @property
    def _llm_type(self) -> str:
        return "uhg_custom_gemini"