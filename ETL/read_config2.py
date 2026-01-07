import uuid
from datetime import datetime, timezone
from typing import Optional, Literal
from pydantic import BaseModel, Field, computed_field, ConfigDict

# 1. Define the Schema
# This acts as a contract for your data. If data is missing or wrong type, it fails early.
class AuditRecordSchema(BaseModel):
    # Configuration to allow using field names when populating, but exporting aliases (UPPER_CASE)
    model_config = ConfigDict(populate_by_name=True)

    # -- Input Fields --
    file_name: str = Field(alias="FILE_NAME")
    state_cd: str = Field(alias="STATE_CD")
    doc_guid: str = Field(alias="DOC_GUID")
    proc_cd: str = Field(alias="PROC_CD")
    
    revised_decision: str = Field(alias="REVISED_DECISION")
    earlier_decision: str = Field(alias="EARLIER_DECISION")
    revised_reason: str = Field(alias="REVISED_COV_REASON")
    earlier_reason: str = Field(alias="EARLIER_COV_REASON")
    
    source_column: str = Field(alias="SOURCE_COLUMN")
    load_mode: str = Field(alias="LOAD_MODE")
    delta_file_row_count: int = Field(alias="ROW_COUNT_DELTA_FILE")

    # Optional Fields (Default to None)
    document_id: Optional[str] = Field(default=None, alias="DOCUMENTID")
    cpt_code_id: Optional[str] = Field(default=None, alias="CPTCODEID")
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

    # -- Business Logic (Computed Field) --
    @computed_field(alias="CHANGE_TYPE")
    def change_type(self) -> str:
        """
        Determines change type based on decision changes.
        ONLY tracks changes in COV_DSCN_IND.
        """
        if self.revised_decision != self.earlier_decision:
            return "Coverage_Update"
        return "No_Change"


# 2. The Simplified Function
def create_audit_record(data: dict) -> dict:
    """
    Creates a single audit record dictionary with tracking metadata.
    
    Args:
        data (dict): A dictionary containing the raw input fields.
        
    Returns:
        dict: A dictionary with UPPER_CASE keys ready for Snowflake insertion.
    """
    try:
        # Validate and create the object
        record = AuditRecordSchema(**data)
        
        # Convert back to dict, using the Aliases (UPPER_CASE keys)
        # mode='json' converts UUIDs and Datetimes to strings automatically if needed,
        # but for direct DB insertion, dict() is usually fine.
        return record.model_dump(by_alias=True)
        
    except Exception as e:
        # Log the specific record that failed
        raise ValueError(f"Failed to create audit record for Doc GUID {data.get('doc_guid')}: {e}")

# --- Usage Example ---

batch_input = {
    "file_name": "claims_2025.csv",
    "state_cd": "NY",
    "doc_guid": "abc-123-xyz",
    "proc_cd": "99213",
    "revised_decision": "PAID",
    "earlier_decision": "DENIED",  # This will trigger 'Coverage_Update'
    "revised_reason": "Medical Necessity",
    "earlier_reason": "Documentation Missing",
    "source_column": "COV_DSCN_IND",
    "load_mode": "DELTA",
    "delta_file_row_count": 1050,
    "batch_id": "BATCH_20260107"
}

final_record = create_audit_record(batch_input)

# Print cleanly to verify
import json
print(json.dumps(final_record, indent=2, default=str))