import pandas as pd
import logging

# Setup logging
logger = logging.getLogger(__name__)

def load_to_temp(session, load_df: pd.DataFrame):
    """
    1. Maps EFFECTIVE_COV_IND to COV_DSCN_IND.
    2. Filters columns to match target Snowflake table exactly.
    3. Loads the processed dataframe to the Snowflake temporary table.
    
    Args:
        session: Active Snowpark session.
        load_df (pd.DataFrame): The dataframe to prepare and load.
    """
    # Constants
    DB_NAME = "EUZDS_DEV_PIMS_AI_DB"
    SCHEMA_NAME = "PIMS_AI_DEV"
    TARGET_TABLE = "POLDIG_WORKING_CPTCODE_T_TEMP_DELTA_TEST"
    
    # Target Schema (Columns strictly required by the Temp Table)
    TEMP_TABLE_COLUMNS = [
        'CPTCODEID', 'PROC_CD', 'PROC_CD_DESC', 'COV_DSCN_IND', 
        'COV_DSCN_RSN', 'COV_DSCN_REF', 'COV_DSCN_PSGS', 
        'COV_DSCN_PAGE', 'COV_DSCN_CAT', 'DOCUMENTID'
    ]

    # Set context
    session.use_database(DB_NAME)
    session.use_schema(SCHEMA_NAME)

    # ---------------------------------------------------------
    # STEP 1: LOGICAL MAPPING & COLUMN ALIGNMENT
    # ---------------------------------------------------------
    
    # Work on a copy to avoid SettingWithCopy warnings
    df_processed = load_df.copy()

    # A. Map Effective Indicator -> Database Column
    # This ensures we load the "Final Truth" calculated earlier, not just the raw extraction
    if 'EFFECTIVE_COV_IND' in df_processed.columns:
        logger.info("ℹ️ Mapping EFFECTIVE_COV_IND to COV_DSCN_IND for DB Load")
        df_processed['COV_DSCN_IND'] = df_processed['EFFECTIVE_COV_IND']

    # B. Strict Schema Alignment
    # .reindex() keeps only the columns in TEMP_TABLE_COLUMNS.
    # It drops extra metadata like 'ORIGIN_FILE', 'ID_TYPE', 'EFFECTIVE_COV_IND'.
    # It fills missing columns (like CPTCODEID if new) with NaN/None.
    df_to_load = df_processed.reindex(columns=TEMP_TABLE_COLUMNS)

    # ---------------------------------------------------------
    # STEP 2: LOAD TO SNOWFLAKE
    # ---------------------------------------------------------
    
    if not df_to_load.empty:
        count = len(df_to_load)
        logger.info(f"🚀 Loading {count} records to {TARGET_TABLE}...")
        
        try:
            # write_pandas handles the chunking and upload efficiently
            session.write_pandas(
                df_to_load,
                TARGET_TABLE,
                auto_create_table=True, # Will match schema of df_to_load
                overwrite=False,        # Append mode
                on_error='continue'
            )
            logger.info(f"✅ Successfully loaded {count} records.")
            
        except Exception as e:
            logger.error(f"❌ Failed to write to Snowflake: {e}")
            raise
    else:
        logger.info("ℹ️ DataFrame is empty - nothing to load.")