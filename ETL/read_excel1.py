import pandas as pd
import logging
from pathlib import Path
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. Define your standard/required schema
REQUIRED_COLUMNS = [
    "PROC_CD", 
    "PROC_CD_DESC", 
    "COV_DSCN_IND", 
    "Revised Coverage Indicator", 
    "COV_DSCN_RSN"
]

def read_single_excel(file_path: Path) -> pd.DataFrame:
    """
    Reads an Excel file and normalizes columns to match REQUIRED_COLUMNS.
    
    Logic:
    1. Standardize file headers (strip whitespace).
    2. Case-insensitive match against REQUIRED_COLUMNS.
    3. Create missing required columns (fill with None).
    4. Reorder: [Required Cols] + [Extra/Unknown Cols] + [Metadata].
    """
    try:
        # 1. Read the file
        # dtype=str ensures codes like '00123' don't become 123
        df = pd.read_excel(file_path, sheet_name=0, engine="openpyxl", dtype=str)
        
        # 2. Clean Headers: Remove accidental leading/trailing whitespace
        df.columns = df.columns.str.strip()

        # 3. Create a map for Case-Insensitive Matching
        # Logic: { 'proc_cd': 'PROC_CD', 'seq#': 'Seq#' } (Lower -> Original)
        file_col_map = {c.lower(): c for c in df.columns}
        
        # 4. Normalize Required Columns
        # We iterate through what we WANT (Required) and look for it in what we HAVE (File)
        found_cols = []
        
        for req_col in REQUIRED_COLUMNS:
            req_lower = req_col.lower()
            
            if req_lower in file_col_map:
                # Match found! Rename the file's specific casing to our Standard casing
                original_name = file_col_map[req_lower]
                if original_name != req_col:
                    df.rename(columns={original_name: req_col}, inplace=True)
                found_cols.append(req_col)
            else:
                # Match NOT found. Create the column with Null values
                df[req_col] = None
        
        # 5. Identify "Extra" columns
        # All columns currently in DF that are NOT in the Required list
        # Using list comprehension to preserve original order of extra columns
        extra_cols = [c for c in df.columns if c not in REQUIRED_COLUMNS]
        
        # 6. Define Final Column Order
        # Required first, then Extras
        final_order = REQUIRED_COLUMNS + extra_cols
        
        # 7. Reorder DataFrame
        df = df[final_order]

        # 8. Add Metadata (Last column)
        df["ORIGIN_FILE"] = file_path.name
        
        return df

    except Exception as e:
        logger.error(f"Failed to read/normalize {file_path.name}: {e}")
        return pd.DataFrame()

# --- Example Usage Logic ---
if __name__ == "__main__":
    # Simulating a file path
    f = Path("sample_data_v1.xlsx")
    
    # Run
    df_normalized = read_single_excel(f)
    
    # Verify
    if not df_normalized.empty:
        print("Columns:", df_normalized.columns.tolist())
        print(df_normalized.head())