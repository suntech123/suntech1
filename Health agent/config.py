# config.py
import os
from dataclasses import dataclass

@dataclass
class GeminiConfig:
    """Holds configuration for the UHG Gemini Gateway."""
    base_url: str = os.getenv("UHG_GEMINI_BASE_URL", "")
    project_id: str = os.getenv("UHG_PROJECT_ID", "")
    
    # Auth config
    client_id: str = os.getenv("HCP_CLIENT_ID", "")
    client_secret: str = os.getenv("HCP_CLIENT_SECRET", "")
    auth_url: str = os.getenv("HCP_AUTH_URL", "")
    scope: str = os.getenv("HCP_SCOPE", "")
    grant_type: str = os.getenv("HCP_GRANT_TYPE", "client_credentials")

    # Available Models
    MODEL_FLASH: str = "gemini-2.5-flash"
    MODEL_PRO: str = "gemini-2.5-pro" # Note: Assuming you meant pro here, your image had flash twice

    def validate(self):
        """Ensure critical environment variables are loaded."""
        missing = [k for k, v in self.__dict__.items() if not v and k != "MODEL_FLASH" and k != "MODEL_PRO"]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Instantiate a global config object to be imported elsewhere
settings = GeminiConfig()