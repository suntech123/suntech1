import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

# 1. Define the Failure Schema
class FailureRecordSchema(BaseModel):
    # Allows populating using snake_case names, but exporting as keys defined in alias=...
    model_config = ConfigDict(populate_by_name=True)

    # -- Required Fields --
    file_name: str = Field(alias="FILE_NAME")
    state_cd: str = Field(alias="STATE_CD")
    doc_guid: str = Field(alias="DOC_GUID")
    
    # You could use an Enum here if you want to restrict to specific error types
    failure_type: str = Field(alias="FAILURE_TYPE") 
    error_message: str = Field(alias="ERROR_MESSAGE")

    # -- Optional Fields (Default to None) --
    # These might be None if the failure happened early in the process
    proc_cd: Optional[str] = Field(default=None, alias="PROC_CD")
    load_mode: Optional[str] = Field(default=None, alias="LOAD_MODE")
    batch_id: Optional[str] = Field(default=None, alias="BATCH_ID")

    # -- Auto-Generated Fields --
    audit_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), 
        alias="AUDIT_ID"
    )
    audit_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        alias="AUDIT_TIMESTAMP"
    )

# 2. The Refactored Function
def create_failure_audit_record(data: dict) -> dict:
    """
    Creates a failure audit record dictionary.
    
    Args:
        data (dict): Dictionary containing error details. 
                     Required keys: file_name, state_cd, doc_guid, failure_type, error_message.
                     
    Returns:
        dict: A dictionary with UPPER_CASE keys ready for Snowflake insertion.
    """
    try:
        # Validate input data against the schema
        record = FailureRecordSchema(**data)
        
        # Convert to dictionary using aliases (UPPER_CASE)
        return record.model_dump(by_alias=True)
        
    except Exception as e:
        # Fallback logging if even the error recording fails
        # In production, use logger.error() here
        print(f"CRITICAL: Failed to generate failure record. Raw data: {data}")
        raise e

# --- Usage Example ---

# Scenario: A validation error occurred during processing
error_context = {
    "file_name": "claims_2025.csv",
    "state_cd": "TX",
    "doc_guid": "fail-999-xyz",
    "failure_type": "VALIDATION_ERROR",
    "error_message": "Invalid CPT Code format: 'XX99'",
    # proc_cd is missing because the code was invalid
    "batch_id": "BATCH_20260107" 
}

failure_record = create_failure_audit_record(error_context)

# Verify Output
import json
print(json.dumps(failure_record, indent=2, default=str))