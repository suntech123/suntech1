import pandas as pd
import logging
from pathlib import Path
from typing import Union

# Setup logging
logger = logging.getLogger(__name__)

def load_full_data_sheet(
    xlsx_file: Union[str, Path], 
    sheet_name: str, 
    max_columns: int = 7
) -> pd.DataFrame:
    """
    Reads an Excel sheet efficiently using Pandas, keeping only rows 
    until the first missing/empty 'PROC_CD' is encountered.
    
    Args:
        xlsx_file (str | Path): Path to the Excel file.
        sheet_name (str): Name of the sheet to load.
        max_columns (int): Number of columns to read from the left (A to G = 7).
        
    Returns:
        pd.DataFrame: Cleaned data with normalized PROC_CD.
    """
    try:
        # 1. Read Excel efficiently (Engine=openpyxl is standard for .xlsx)
        # usecols=range(max_columns) ensures we only read the first N columns (A-G)
        # dtype=str ensures we don't lose leading zeros in codes immediately
        df = pd.read_excel(
            xlsx_file, 
            sheet_name=sheet_name, 
            engine="openpyxl", 
            header=0,
            usecols=range(max_columns), 
            dtype=str 
        )

        # 2. Clean Headers (Strip whitespace)
        df.columns = df.columns.str.strip()

        # 3. Validate Required Column
        if "PROC_CD" not in df.columns:
            raise ValueError(f"Column 'PROC_CD' not found in headers: {df.columns.tolist()}")

        # 4. Implement Logic: "Stop when we hit the first null PROC_CD"
        # The original code didn't just drop NAs, it stopped reading entirely.
        
        # Convert to string and strip whitespace
        proc_series = df["PROC_CD"].astype(str).str.strip()
        
        # Identify "Bad" rows (Null, None, 'nan', or empty string)
        # Note: 'nan' string check is needed because we read as dtype=str
        is_invalid = (proc_series == '') | (proc_series.str.lower() == 'nan') | (df["PROC_CD"].isna())

        if is_invalid.any():
            # Find the index of the FIRST True value (the first invalid row)
            first_invalid_index = is_invalid.idxmax()
            
            # Slice the dataframe to keep everything BEFORE that row
            df = df.iloc[:first_invalid_index].copy()
            
            logger.info(f"Stopped reading at row {first_invalid_index + 2} due to empty PROC_CD.")
        
        # 5. Normalize PROC_CD (Your specific business rule)
        # Strip and Pad with 5 zeros
        df['PROC_CD'] = df['PROC_CD'].astype(str).str.strip().str.zfill(5)

        logger.info(f"✅ Loaded {len(df)} rows with valid PROC_CD from {Path(xlsx_file).name}")
        return df

    except Exception as e:
        logger.error(f"Failed to load full data from {xlsx_file}: {e}")
        # Return empty DF on failure to prevent pipeline crash
        return pd.DataFrame()