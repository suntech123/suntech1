import pandas as pd
import numpy as np
import logging
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURATION: Hardcoded Values Moved Here ---
# Maps the Decision (Key) to the Description (Value)
COV_REASON_CONFIG = {
    "Conditionally-Covered": "This service/equipment/drug requires additional review based on the member's current benefit plan.",
    "Covered": "This procedure is a covered benefit per the member's policy.",
    "Non-Covered": "This procedure is not a covered benefit per the member's policy."
}

# Pipeline Config
DELTA_SOURCE_DIR = Path("./snowflake_data_load/revised_files_load")
LOAD_MODE = "full"
FALLBACK_TO_FULL = True
BATCH_ID = str(uuid.uuid4())

# --- ASSUMED EXTERNAL FUNCTIONS (From your previous context) ---
# Ensuring imports match your previous setup
from your_module import (
    load_delta_data_sheet, 
    load_golden_data, 
    extract_metadata, 
    create_audit_record, 
    create_failure_audit_record,
    _normalise_cov_desc
)


#######

def process_single_delta_file(xlsx_file: Path):
    """
    Processes a single Excel file: Validates, Merges with Golden, 
    Calculates Updates, and Generates Audit records using Vectorization.
    """
    file_name = xlsx_file.name
    logger.info(f"Processing: {file_name}")

    # 1. Load Delta Data
    df_delta = load_delta_data_sheet(
        xlsx_file, 
        sheet_name='Sheet1', 
        highlight_col='C', 
        mode=LOAD_MODE, 
        fallback_to_full=FALLBACK_TO_FULL
    )
    
    if df_delta.empty:
        logger.warning(f"Skipping empty file: {file_name}")
        return [], []

    # 2. Metadata & Golden Data Load
    state_cd, doc_guid = extract_metadata(file_name)
    df_golden = load_golden_data(doc_guid)

    # 3. Pre-Calculation: Effective Coverage Indicator (Vectorized)
    # Logic: Use Revised if available, else COV_DSCN_IND
    df_delta['EFFECTIVE_COV_IND'] = df_delta['Revised Coverage Indicator'].combine_first(df_delta['COV_DSCN_IND'])
    
    # Determine source column name for auditing
    df_delta['AUDIT_SOURCE_COL'] = np.where(
        df_delta['Revised Coverage Indicator'].notna(), 
        'Revised Coverage Indicator', 
        'COV_DSCN_IND'
    )

    # 4. VALIDATION: Check PROC_CD existence (Vectorized 'isin')
    # Standardize types to string for safe comparison
    delta_procs = df_delta['PROC_CD'].astype(str)
    golden_procs = df_golden['PROC_CD'].astype(str)
    
    valid_mask = delta_procs.isin(golden_procs)
    
    # -- Handle Failures --
    df_failed = df_delta[~valid_mask].copy()
    failure_records = []
    
    if not df_failed.empty:
        # Bulk create failure records
        for _, row in df_failed.iterrows():
            # We use iterrows here only for failures (usually small volume)
            # or map the create_failure function if strictly necessary
            rec = create_failure_audit_record({
                "file_name": file_name,
                "state_cd": state_cd,
                "doc_guid": doc_guid,
                "failure_type": "PROC_CD_NOT_FOUND",
                "error_message": f"PROC_CD {row['PROC_CD']} not found in golden data",
                "proc_cd": row['PROC_CD'],
                "load_mode": LOAD_MODE,
                "batch_id": BATCH_ID
            })
            failure_records.append(rec)

    # -- Keep Valid Rows --
    df_valid = df_delta[valid_mask].copy()
    if df_valid.empty:
        return [], failure_records

    # 5. CORE LOGIC: Merge Delta with Golden (The "Baseline" Step)
    # This replaces the slow manual lookup loop
    df_merged = pd.merge(
        df_valid,
        df_golden[['PROC_CD', 'COV_DSCN_IND', 'COV_DSCN_RSN', 'DOCUMENTID', 'CPTCODEID']],
        on='PROC_CD',
        how='left',
        suffixes=('_new', '_old')
    )

    # 6. DETECT CHANGES (Vectorized)
    # Condition: 
    #   1. New Decision is NOT Null 
    #   2. Old Decision is NOT Null (Existing record)
    #   3. Values are DIFFERENT
    change_mask = (
        df_merged['EFFECTIVE_COV_IND'].notna() &
        df_merged['COV_DSCN_IND_old'].notna() &
        (df_merged['EFFECTIVE_COV_IND'] != df_merged['COV_DSCN_IND_old'])
    )

    df_changes = df_merged[change_mask].copy()

    # 7. GENERATE AUDIT RECORDS (Vectorized Preparation)
    audit_records = []
    
    if not df_changes.empty:
        # Map the reason description based on configuration
        # This replaces the hardcoded "if/else" block in image 3
        df_changes['new_reason_desc'] = df_changes['EFFECTIVE_COV_IND'].map(COV_REASON_CONFIG)

        # Iterate only the CHANGED rows to create audit dicts
        # (Much faster than iterating ALL rows)
        for _, row in df_changes.iterrows():
            audit_rec = create_audit_record({
                "file_name": file_name,
                "state_cd": state_cd,
                "doc_guid": doc_guid,
                "proc_cd": row['PROC_CD'],
                "revised_decision": row['EFFECTIVE_COV_IND'], # New Value
                "earlier_decision": row['COV_DSCN_IND_old'],  # Old Value
                "revised_reason": row['new_reason_desc'],     # Mapped Description
                "earlier_reason": row['COV_DSCN_RSN_old'],    # Old Reason from DB
                "source_column": row['AUDIT_SOURCE_COL'],
                "load_mode": LOAD_MODE,
                "delta_file_row_count": len(df_delta),
                "documentid": row['DOCUMENTID'],
                "cptcodeid": row['CPTCODEID'],
                "batch_id": BATCH_ID
            })
            audit_records.append(audit_rec)

    logger.info(f"File Summary: {len(df_valid)} valid rows, {len(df_changes)} changes, {len(df_failed)} failures.")
    
    return audit_records, failure_records

#######

def main():
    logger.info(f"Starting Batch Run: {BATCH_ID}")
    
    all_audit_changes = []
    all_audit_failures = []
    processed_files_count = 0

    # Get list of files
    xlsx_files = list(DELTA_SOURCE_DIR.glob("*.xlsx"))
    
    if not xlsx_files:
        logger.warning("No files found to process.")
        return

    # Process files
    for src in xlsx_files:
        try:
            changes, failures = process_single_delta_file(src)
            all_audit_changes.extend(changes)
            all_audit_failures.extend(failures)
            processed_files_count += 1
        except Exception as e:
            logger.error(f"CRITICAL ERROR processing file {src.name}: {e}")
            # Capture file-level failure if needed
            
    # --- Final DataFrames ---
    audit_changes_df = pd.DataFrame(all_audit_changes)
    audit_failures_df = pd.DataFrame(all_audit_failures)

    # --- Summary Report ---
    print("\n" + "="*80)
    print(f"📊 BATCH SUMMARY : {BATCH_ID}")
    print("="*80)
    print(f"✅ Files Processed  : {processed_files_count}")
    print(f"📝 Changes Tracked  : {len(audit_changes_df)}")
    print(f"❌ Failures Tracked : {len(audit_failures_df)}")
    print("="*80)

    # (Optional) Save or Push to Snowflake here
    # session.write_pandas(audit_changes_df, "AUDIT_TABLE", ...)

if __name__ == "__main__":
    main()