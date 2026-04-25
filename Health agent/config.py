# config.py
import os
from dataclasses import dataclass

@dataclass
class Config:
    # --- UHG Gemini Settings ---
    uhg_base_url: str = os.getenv("UHG_GEMINI_BASE_URL", "")
    uhg_project_id: str = os.getenv("UHG_PROJECT_ID", "")
    hcp_client_id: str = os.getenv("HCP_CLIENT_ID", "")
    hcp_client_secret: str = os.getenv("HCP_CLIENT_SECRET", "")
    hcp_auth_url: str = os.getenv("HCP_AUTH_URL", "")
    hcp_scope: str = os.getenv("HCP_SCOPE", "")
    hcp_grant_type: str = os.getenv("HCP_GRANT_TYPE", "client_credentials")
    gemini_model: str = "gemini-2.5-flash"

    # --- OpenAI Settings ---
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4o" # or gpt-3.5-turbo

settings = Config()