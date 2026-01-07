import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, FilePath, SecretStr, model_validator

class SnowflakeConfig(BaseModel):
    user: str
    account: str
    warehouse: str
    database: str
    schema_: str = Field(alias="schema") # Handles 'schema' key in YAML safely
    role: str
    
    # 1. Pydantic will automatically ensure this file exists
    private_key_path: FilePath 
    
    # Optional: If the key file is encrypted, you still need a passphrase
    passphrase: Optional[SecretStr] = None 

    # 2. This field is not in YAML, but we populate it automatically
    private_key_bytes: bytes = Field(default=b"", exclude=True)

    # 3. Validator to read the file content immediately upon loading
    @model_validator(mode='after')
    def load_key_content(self):
        try:
            # We read the file defined in the path
            content = self.private_key_path.read_bytes()
            self.private_key_bytes = content
        except Exception as e:
            raise ValueError(f"Could not read key file at {self.private_key_path}: {e}")
        return self

def get_snowflake_config(yaml_path: Path) -> SnowflakeConfig:
    """Loads and validates the Snowflake configuration."""
    
    if not yaml_path.exists():
        raise FileNotFoundError(f"Config file not found: {yaml_path}")

    with yaml_path.open('r') as f:
        # Load raw dict
        raw_config = yaml.safe_load(f)
        
    # Pydantic validates types, checks if ./pkey.pem exists, 
    # and reads the bytes into .private_key_bytes
    return SnowflakeConfig(**raw_config)

# --- Usage ---
try:
    config_file = Path("snowflake_config.yaml")
    config = get_snowflake_config(config_file)

    print("Configuration Validated.")
    print(f"Loaded Private Key: {len(config.private_key_bytes)} bytes")
    
    # Example usage in Snowflake connector:
    # conn = snowflake.connector.connect(
    #     user=config.user,
    #     private_key=config.private_key_bytes, 
    #     ...
    # )

except Exception as e:
    print(f"Configuration Error: {e}")