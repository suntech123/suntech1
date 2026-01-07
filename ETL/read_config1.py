import logging
import yaml
from pathlib import Path
from typing import Optional, Tuple

# 1. Cryptography Imports (Required for the logic shown in your image)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# 2. Snowflake Imports
import snowflake.connector
from snowflake.snowpark import Session

# 3. Pydantic Imports
from pydantic import BaseModel, Field, FilePath, SecretStr, model_validator, ConfigDict

# Setup Logging (Standard practice over 'print')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SnowflakeConfig(BaseModel):
    """
    Validates configuration and prepares cryptographic keys automatically.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True) # Allow bytes/complex types

    user: str
    account: str
    warehouse: str
    database: str
    schema_: str = Field(alias="schema") 
    role: str
    
    # Ensures file exists on disk
    private_key_path: FilePath 
    passphrase: Optional[SecretStr] = None 

    # This field will hold the processed DER-formatted key required by Snowflake
    private_key_der: bytes = Field(default=b"", exclude=True)

    @model_validator(mode='after')
    def load_and_process_key(self):
        """
        Reads the PEM file, decrypts it using the passphrase (if any),
        and converts it to the DER format required by the Snowflake Driver.
        """
        try:
            # 1. Read raw bytes from file
            pem_data = self.private_key_path.read_bytes()
            
            # 2. Prepare password bytes if passphrase exists
            password_bytes = (
                self.passphrase.get_secret_value().encode() 
                if self.passphrase else None
            )

            # 3. Load the PEM Key (Cryptography logic from your image)
            p_key = serialization.load_pem_private_key(
                pem_data,
                password=password_bytes,
                backend=default_backend()
            )

            # 4. Serialize to DER (PKCS8) - Specific requirement for Snowflake driver
            self.private_key_der = p_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
        except ValueError as e:
            # Captures "Bad decrypt" errors if password is wrong
            raise ValueError(f"Invalid Private Key or Passphrase: {e}")
        except Exception as e:
            raise ValueError(f"Failed to process private key at {self.private_key_path}: {e}")
            
        return self

def get_snowflake_connection_and_session(
    config_path: Path
) -> Tuple[snowflake.connector.SnowflakeConnection, Session]:
    """
    Establishes Snowflake connection and Snowpark session using strict validation.
    
    Returns:
        Tuple containing (Connection, Session)
    """
    try:
        # 1. Load and Validate Config
        # The Pydantic model handles all file reading and crypto logic here.
        if not config_path.exists():
            raise FileNotFoundError(f"Config file missing at {config_path}")

        with config_path.open("r") as f:
            raw_config = yaml.safe_load(f)
            
        config = SnowflakeConfig(**raw_config)
        logger.info("Configuration loaded and private key processed successfully.")

        # 2. Define Connection Parameters
        # Notice we use config.private_key_der (processed bytes) directly
        conn_params = {
            "user": config.user,
            "account": config.account,
            "warehouse": config.warehouse,
            "database": config.database,
            "schema": config.schema_,
            "role": config.role,
            "private_key": config.private_key_der 
        }

        # 3. Create Connector Connection
        logger.info("Connecting to Snowflake via Connector...")
        connection = snowflake.connector.connect(**conn_params)
        
        # 4. Create Snowpark Session
        # We reuse the existing connection for efficiency
        logger.info("Creating Snowpark Session...")
        session = Session.builder.configs({"connection": connection}).create()

        logger.info(f"Successfully connected to Snowflake account: {config.account}")
        return connection, session

    except (ValueError, FileNotFoundError) as e:
        logger.error(f"Configuration/Validation Error: {e}")
        raise # Re-raise to let the caller handle the crash
    except snowflake.connector.errors.DatabaseError as e:
        logger.error(f"Snowflake Connectivity Error: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        raise

# --- Usage ---

if __name__ == "__main__":
    cfg_path = Path("snowflake_config.yaml")
    
    try:
        conn, sess = get_snowflake_connection_and_session(cfg_path)
        
        # Test logic
        print(f"Current Session Database: {sess.get_current_database()}")
        
        # Always close connection when done (or use context managers)
        # sess.close() 
    except Exception:
        print("Initialization failed.")