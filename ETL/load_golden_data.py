import pandas as pd
from typing import List
import logging

# Setup logger
logger = logging.getLogger(__name__)

def load_golden_data_batch(guids: List[str], cursor) -> pd.DataFrame:
    """
    Fetches CPT code data for a batch of Document GUIDs in a single query.
    
    Args:
        guids (List[str]): A list of DOC_GLOBAL_DOC_ID strings.
        cursor: Active Snowflake cursor object.
        
    Returns:
        pd.DataFrame: DataFrame containing CPT codes for all requested GUIDs.
    """
    # 1. Handle Edge Case: Empty List
    if not guids:
        logger.warning("No GUIDs provided to load_golden_data_batch.")
        return pd.DataFrame() # Return empty DF with expected columns if needed

    # 2. Generate SQL Placeholders dynamically (%s, %s, %s...)
    # This is the standard safe way to bind lists in Snowflake Python Connector
    placeholders = ", ".join(["%s"] * len(guids))

    # 3. Construct Query
    # Note: Using IN (...) with the generated placeholders
    query = f"""
        SELECT 
            CPT.* 
        FROM 
            EUZDS_DEV_PIMS_DB.PIMS_DEV.POLDIG_DOCUMENT_T DOC 
        JOIN 
            EUZDS_DEV_PIMS_DB.PIMS_DEV.POLDIG_CPTCODE_T CPT
            ON CPT.documentid = DOC.documentid
        WHERE 
            DOC.DOC_GLOBAL_DOC_ID IN ({placeholders})
    """

    try:
        # 4. Execute with Binding (Pass 'guids' as the second argument)
        # Snowflake replaces %s with the actual values safely
        cursor.execute(query, guids)
        
        # 5. Fetch Results
        cpt_df = cursor.fetch_pandas_all()

        # 6. Data Cleaning (Vectorized)
        if not cpt_df.empty:
            # Ensure proper string formatting (Strip whitespace, pad with zeros)
            cpt_df['PROC_CD'] = (
                cpt_df['PROC_CD']
                .astype(str)
                .str.strip()
                .str.zfill(5)
            )

        return cpt_df

    except Exception as e:
        logger.error(f"Failed to load golden data batch: {e}")
        raise