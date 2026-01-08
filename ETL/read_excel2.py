import pandas as pd
import logging
import numpy as np
import re
from pathlib import Path
from typing import Union, List

# Setup logging
logger = logging.getLogger(__name__)

# Define constants
REQUIRED_COLUMNS = [
    "PROC_CD", 
    "PROC_CD_DESC", 
    "COV_DSCN_IND", 
    "Revised Coverage Indicator", 
    "COV_DSCN_RSN"
]

def load_full_data_sheet(xlsx_file: Union[str, Path]) -> pd.DataFrame:
    """
    Reads the FIRST sheet of an Excel file, reads ALL columns, 
    and applies standard normalization and stopping logic.
    
    Args:
        xlsx_file (str | Path): Path to the Excel file.
        
    Returns:
        pd.DataFrame: Cleaned data aligned to the master schema.
    """
    file_path = Path(xlsx_file)
    
    try:
        # 1. READ EXCEL (First Sheet, All Columns)
        # sheet_name=0 loads the first sheet. 
        # Removed usecols=range(...) so it reads everything.
        df = pd.read_excel(
            file_path, 
            sheet_name=0, 
            engine="openpyxl", 
            header=0,
            dtype=str 
        )

        # 2. CLEAN HEADERS (Strip whitespace)
        df.columns = df.columns.str.strip()

        # 3. CASE-INSENSITIVE MATCHING
        # Create a map: {'proc_cd': 'Proc_Cd', 'seq#': 'Seq#'}
        file_col_map = {c.lower(): c for c in df.columns}
        
        # Check specifically for PROC_CD first
        if "proc_cd" not in file_col_map:
             logger.warning(f"Skipping {file_path.name}: 'PROC_CD' column not found.")
             return pd.DataFrame()
             
        # Normalize the PROC_CD column name immediately
        actual_proc_col = file_col_map["proc_cd"]
        if actual_proc_col != "PROC_CD":
            df.rename(columns={actual_proc_col: "PROC_CD"}, inplace=True)

        # 4. STOP AT FIRST NULL PROC_CD
        proc_series = df["PROC_CD"].astype(str).str.strip()
        is_invalid = (proc_series == '') | (proc_series.str.lower() == 'nan') | (df["PROC_CD"].isna())

        if is_invalid.any():
            first_invalid_index = is_invalid.idxmax()
            df = df.iloc[:first_invalid_index].copy()
            logger.info(f"Stopped reading {file_path.name} at row {first_invalid_index + 2}")

        # 5. NORMALIZE PROC_CD
        df['PROC_CD'] = df['PROC_CD'].astype(str).str.strip().str.zfill(5)

        # 6. SCHEMA NORMALIZATION & REORDERING
        # Rename other required columns if they exist in different casing
        for req in REQUIRED_COLUMNS:
            if req == "PROC_CD": continue # Already handled
            if req.lower() in file_col_map:
                actual_name = file_col_map[req.lower()]
                if actual_name != req:
                    df.rename(columns={actual_name: req}, inplace=True)
            else:
                # Add missing required columns with NaN
                df[req] = None

        # Identify Extra Columns (Anything read that isn't required)
        extra_cols = [c for c in df.columns if c not in REQUIRED_COLUMNS]
        
        # Reorder: Required + Extras
        final_order = REQUIRED_COLUMNS + extra_cols
        df = df[final_order]

        # 7. ADD METADATA
        df["ORIGIN_FILE"] = file_path.name
        
        # Extract UUID from filename
        match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', file_path.name, re.I)
        df['DOC_GLOBAL_DOC_ID'] = match.group(0) if match else None

        logger.info(f"✅ Loaded {len(df)} rows from {file_path.name}")
        return df

    except Exception as e:
        logger.error(f"Failed to load full data from {file_path.name}: {e}")
        return pd.DataFrame()