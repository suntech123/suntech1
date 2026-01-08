import pandas as pd
import logging

# Setup logging
logger = logging.getLogger(__name__)

def load_to_temp(session, load_df: pd.DataFrame, baseline_state_dict: dict):
    """
    1. Maps EFFECTIVE_COV_IND to COV_DSCN_IND.
    2. Filters columns to match target Snowflake table exactly.
    3. Identifies changed records using vectorized operations.
    4. Loads only changed records to Snowflake.
    """
    # Constants
    DB_NAME = "EUZDS_DEV_PIMS_AI_DB"
    SCHEMA_NAME = "PIMS_AI_DEV"
    TARGET_TABLE = "POLDIG_WORKING_CPTCODE_T_TEMP_DELTA_TEST"
    
    # Target Schema (As per your requirement)
    TEMP_TABLE_COLUMNS = [
        'CPTCODEID', 'PROC_CD', 'PROC_CD_DESC', 'COV_DSCN_IND', 
        'COV_DSCN_RSN', 'COV_DSCN_REF', 'COV_DSCN_PSGS', 
        'COV_DSCN_PAGE', 'COV_DSCN_CAT', 'DOCUMENTID'
    ]

    # Set context
    session.use_database(DB_NAME)
    session.use_schema(SCHEMA_NAME)

    # ---------------------------------------------------------
    # STEP 1: LOGICAL MAPPING & COLUMN ALIGNMENT (Approach 2)
    # ---------------------------------------------------------
    
    # Work on a copy to avoid SettingWithCopy warnings on the original df
    df_processed = load_df.copy()

    # A. Map Effective Indicator -> Database Column
    if 'EFFECTIVE_COV_IND' in df_processed.columns:
        logger.info("ℹ️ Mapping EFFECTIVE_COV_IND to COV_DSCN_IND for DB Load")
        df_processed['COV_DSCN_IND'] = df_processed['EFFECTIVE_COV_IND']

    # B. Strict Schema Alignment
    # .reindex() keeps only the columns in TEMP_TABLE_COLUMNS.
    # It drops extra metadata like 'ORIGIN_FILE', 'ID_TYPE', etc.
    # It fills missing columns (like CPTCODEID if new) with NaN/None.
    df_clean = df_processed.reindex(columns=TEMP_TABLE_COLUMNS)

    # ---------------------------------------------------------
    # STEP 2: VECTORIZED CHANGE DETECTION
    # ---------------------------------------------------------

    # Flatten baseline dict for fast O(1) vectorized lookup
    # {proc_code: earlier_decision}
    baseline_lookup = {
        k: v.get('earlier_decision') 
        for k, v in baseline_state_dict.items() 
        if v
    }

    # Map earlier decisions to the dataframe based on PROC_CD
    earlier_decisions = df_clean['PROC_CD'].map(baseline_lookup)

    # Create Boolean Mask for Changes
    # Logic: 
    # 1. Current Value (COV_DSCN_IND) is NOT Empty
    # 2. Previous Value (earlier_decisions) is NOT Empty
    # 3. They are DIFFERENT
    # (Note: Rows not in baseline are usually New Inserts, not Changes, 
    # so we require earlier_decisions.notna() to capture strictly *updates* 
    # unless you want to load Insertions here too).
    mask_changed = (
        df_clean['COV_DSCN_IND'].notna() & 
        earlier_decisions.notna() & 
        (df_clean['COV_DSCN_IND'] != earlier_decisions)
    )

    # Filter to get only the rows that changed
    changed_records_df = df_clean[mask_changed].copy()

    # ---------------------------------------------------------
    # STEP 3: LOAD TO SNOWFLAKE
    # ---------------------------------------------------------
    
    if not changed_records_df.empty:
        count = len(changed_records_df)
        logger.info(f"🚀 Loading {count} changed records to {TARGET_TABLE}...")
        
        try:
            session.write_pandas(
                changed_records_df,
                TARGET_TABLE,
                auto_create_table=True, # Will match schema of df_clean
                overwrite=False,
                on_error='continue'
            )
            logger.info(f"✅ Successfully loaded {count} records.")
            
        except Exception as e:
            logger.error(f"❌ Failed to write to Snowflake: {e}")
            raise
    else:
        logger.info("ℹ️ No changes detected - nothing to load.")