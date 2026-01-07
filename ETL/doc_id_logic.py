import uuid
import re
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

UUID_REGEX_CANONICAL = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

def get_or_create_doc_id(file_path: Path) -> str:
    """
    1. Tries to extract UUID from filename.
    2. If missing, generates a DETERMINISTIC UUID based on the filename.
    """
    filename = file_path.name
    
    # 1. Try to find real UUID
    match = re.search(UUID_REGEX_CANONICAL, filename, flags=re.IGNORECASE)
    
    if match:
        return match.group(0)
    
    # 2. Generate Deterministic Dummy
    # uuid5 creates a UUID by hashing a namespace + a name (the filename).
    # This guarantees that 'Alabama.xlsx' ALWAYS produces the same UUID.
    dummy_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, filename))
    
    logger.warning(
        f"⚠️ ID missing in '{filename}'. Generated deterministic dummy: {dummy_uuid}"
    )
    
    return dummy_uuid

# --- How to use it in your read function ---

def read_single_excel(file_path: Path) -> pd.DataFrame:
    try:
        # ... (Read logic) ...
        df = pd.read_excel(file_path, sheet_name=0, engine="openpyxl", dtype=str)
        
        # ... (Normalization logic) ...
        
        # ---------------------------------------------------------
        # APPLY THE ID LOGIC
        # ---------------------------------------------------------
        final_doc_id = get_or_create_doc_id(file_path)
        
        df['DOC_GLOBAL_DOC_ID'] = final_doc_id
        
        # Optional: Add a flag so you know which ones are dummies
        # Check if the ID was actually in the filename to set the status
        if final_doc_id in file_path.name:
            df['ID_TYPE'] = 'ORIGINAL'
        else:
            df['ID_TYPE'] = 'GENERATED_DUMMY'
            
        return df

    except Exception as e:
        logger.error(f"Error: {e}")
        return pd.DataFrame()