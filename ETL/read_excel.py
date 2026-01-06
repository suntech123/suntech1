import pandas as pd
import numpy as np
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from typing import List, Tuple, Union

# Mocking external helpers referenced in your image for the code to run
# In production, ensure these are imported from your utils module
REQUIRED_COLUMNS = ["PROC_CD", "Revised Coverage Indicator", "COV_DSCN_IND"]

def _is_absent(val):
    return pd.isna(val) or val == ""

def _normalise_cov_desc(val):
    return str(val).strip().upper() if pd.notna(val) else None

def read_single_excel(file_path: Path) -> pd.DataFrame:
    """Helper function to read a single file, intended for parallel execution."""
    try:
        df = pd.read_excel(file_path, sheet_name="Sheet1", engine="openpyxl")
        # Add source file tracking immediately
        df["ORIGIN_FILE"] = file_path.name
        return df
    except Exception as e:
        print(f"❌ Error reading {file_path.name}: {e}")
        return pd.DataFrame()

def load_and_prepare_multiple_excels(folder_path: Union[str, Path]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Reads all Excel files in a folder in parallel, validates, normalizes, 
    calculates logic using vectorization, and deduplicates efficiently.
    """
    folder = Path(folder_path)
    excel_files = list(folder.glob("*.xlsx"))
    
    if not excel_files:
        raise FileNotFoundError(f"No .xlsx files found in {folder}")

    print(f"📂 Found {len(excel_files)} files. Starting parallel read...")

    # 1. PARALLEL READ: Speed up I/O
    with ProcessPoolExecutor() as executor:
        dfs = list(executor.map(read_single_excel, excel_files))
    
    # Combine all files
    df = pd.concat(dfs, ignore_index=True)
    
    if df.empty:
        raise ValueError("All Excel files were empty or failed to load.")

    # Keep a raw copy if strictly necessary (Warning: High Memory Usage)
    df_raw_copy = df.copy()

    # 2. VALIDATION
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Merged dataset missing required columns: {missing}")

    # 3. VECTORIZED CLEANING (No loops)
    # Optimize string operations
    df["PROC_CD"] = df["PROC_CD"].astype(str).str.strip().str.zfill(5)

    # Normalize coverage columns
    # applying function to Series is faster than apply(axis=1), but map/vectorize is best.
    # Assuming _normalise_cov_desc is simple, we map it.
    df["COV_DSCN_IND"] = df["COV_DSCN_IND"].map(_normalise_cov_desc)
    
    # Handle the condition: if absent -> NaN, else normalize
    # We do this by applying logic to the series, not the row
    mask_absent = df["Revised Coverage Indicator"].apply(_is_absent)
    df.loc[mask_absent, "Revised Coverage Indicator"] = np.nan
    df.loc[~mask_absent, "Revised Coverage Indicator"] = \
        df.loc[~mask_absent, "Revised Coverage Indicator"].map(_normalise_cov_desc)

    # 4. VECTORIZED LOGIC FOR 'EFFECTIVE_COV_IND' & 'SOURCE_IN_EXCEL'
    # Original logic: If Revised exists, use it. Else use COV_DSCN.
    # We use 'combine_first' which does exactly this efficiently.
    
    df["EFFECTIVE_COV_IND"] = df["Revised Coverage Indicator"].combine_first(df["COV_DSCN_IND"])
    
    # Logic: Source is "Revised..." if not NaN, else "COV..."
    df["SOURCE_IN_EXCEL"] = np.where(
        df["Revised Coverage Indicator"].notna(), 
        "Revised Coverage Indicator", 
        "COV_DSCN_IND"
    )

    # 5. OPTIMIZED DEDUPLICATION (Sort + Drop Duplicates)
    # Rules: 
    #   1. Prefer rows where 'Revised Coverage Indicator' is NOT Na/Null.
    #   2. If multiple exist, take the LAST occurrence.
    
    print("⚡ Deduplicating records...")
    initial_count = len(df)
    
    # Create a temporary priority column
    # 1 = High Priority (Revised is Present), 0 = Low Priority
    df["_sort_priority"] = df["Revised Coverage Indicator"].notna().astype(int)
    
    # Sort by: 
    #   1. PROC_CD (Grouping key)
    #   2. Priority (Put 1s at the bottom so 'keep=last' picks them)
    #   3. Index (Preserve original file/row order so 'last' works chronologically)
    df = df.sort_values(by=["PROC_CD", "_sort_priority"], kind="mergesort")
    
    # Drop duplicates, keeping the last one (which will be the highest priority or last loaded)
    df_deduped = df.drop_duplicates(subset=["PROC_CD"], keep="last").copy()
    
    # Clean up temp column
    df_deduped.drop(columns=["_sort_priority"], inplace=True)

    # 6. LOGGING SUMMARY
    # Calculating per-group logs is slow. Aggregate logging is standard for Big Data.
    dropped_count = initial_count - len(df_deduped)
    if dropped_count > 0:
        print(f"⚠️ Deduplication Complete: Dropped {dropped_count} duplicate rows.")
        print(f"✅ Final row count: {len(df_deduped)}")
    else:
        print("✅ No duplicates found.")

    return df_deduped, df_raw_copy

# Usage
# clean_df, raw_df = load_and_prepare_multiple_excels("./data_folder")