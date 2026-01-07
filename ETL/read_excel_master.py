import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Tuple, List
from concurrent.futures import ProcessPoolExecutor

# Assuming these globals/helpers exist based on previous context
# REQUIRED_COLUMNS = [...]
# _normalise_cov_desc = ...
# _is_absent = ...
# read_single_excel = ...

def load_and_prepare_multiple_excels(folder_path: Union[str, Path]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Reads all Excel files, aligns them to a global superset schema, 
    validates, normalizes, and deduplicates efficiently.
    """
    folder = Path(folder_path)
    excel_files = list(folder.glob("*.xlsx"))

    if not excel_files:
        raise FileNotFoundError(f"No .xlsx files found in {folder}")

    print(f"📂 Found {len(excel_files)} files. Starting parallel read...")

    # 1. PARALLEL READ
    with ProcessPoolExecutor() as executor:
        dfs = list(executor.map(read_single_excel, excel_files))

    # Remove any empty DataFrames returned by read errors
    dfs = [d for d in dfs if not d.empty]

    if not dfs:
        raise ValueError("All Excel files were empty or failed to load.")

    # ---------------------------------------------------------
    # NEW LOGIC: Master Schema Alignment
    # ---------------------------------------------------------
    
    # 1. Create a Master List of unique columns from ALL dataframes
    all_unique_columns = set()
    for d in dfs:
        all_unique_columns.update(d.columns)

    # 2. Determine Final Column Order
    # Order: [Required Columns] + [Everything Else found in files]
    # We filter REQUIRED_COLUMNS to ensure we don't duplicate if they are in 'extras'
    # (Though logic below handles strict separation)
    
    extra_columns = [col for col in all_unique_columns if col not in REQUIRED_COLUMNS]
    
    # Sorting extras alphabetically ensures deterministic column order across runs
    master_column_order = REQUIRED_COLUMNS + sorted(extra_columns)

    print(f"🔄 Aligning {len(dfs)} files to master schema of {len(master_column_order)} columns...")

    # 3. Align every DataFrame to this Master List
    # .reindex() does exactly what is asked:
    #   - Reorders columns to match the list.
    #   - Inserts NaN for any column in the list that is missing in the DF.
    dfs = [d.reindex(columns=master_column_order) for d in dfs]

    # ---------------------------------------------------------
    # END NEW LOGIC
    # ---------------------------------------------------------

    # Combine all files (Now they have identical structure)
    df = pd.concat(dfs, ignore_index=True)

    # Keep a raw copy if strictly necessary
    df_raw_copy = df.copy()

    # 2. VALIDATION (Double check)
    # Since we forced reindex, these columns definitely exist, but might be all NaN.
    # This check ensures they are present in the structure.
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        # This shouldn't happen due to reindex, but good for sanity
        raise ValueError(f"Merged dataset structure error. Missing: {missing}")

    # 3. VECTORIZED CLEANING
    print("🧹 Starting vectorized cleaning...")
    
    # Optimize string operations
    df["PROC_CD"] = df["PROC_CD"].astype(str).str.strip().str.zfill(5)

    # Normalize coverage columns
    df["COV_DSCN_IND"] = df["COV_DSCN_IND"].map(_normalise_cov_desc)

    # Handle the condition: if absent -> NaN, else normalize
    mask_absent = df["Revised Coverage Indicator"].apply(_is_absent)
    
    # Using numpy where is often cleaner/faster for conditional updates
    df["Revised Coverage Indicator"] = np.where(
        mask_absent, 
        np.nan, 
        df["Revised Coverage Indicator"].map(_normalise_cov_desc)
    )

    # 4. VECTORIZED LOGIC FOR 'EFFECTIVE_COV_IND' & 'SOURCE_IN_EXCEL'
    df["EFFECTIVE_COV_IND"] = df["Revised Coverage Indicator"].combine_first(df["COV_DSCN_IND"])

    df["SOURCE_IN_EXCEL"] = np.where(
        df["Revised Coverage Indicator"].notna(), 
        "Revised Coverage Indicator", 
        "COV_DSCN_IND"
    )

    # 5. OPTIMIZED DEDUPLICATION
    print("⚡ Deduplicating records...")
    initial_count = len(df)

    # Priority logic: 1 = High Priority (Revised Present), 0 = Low
    df["_sort_priority"] = df["Revised Coverage Indicator"].notna().astype(int)

    # Sort: Group by PROC_CD, then Priority (asc), then Index (asc)
    # We want to keep LAST, so we want the "best" row at the bottom.
    df = df.sort_values(by=["PROC_CD", "_sort_priority"], kind="mergesort")

    # Drop duplicates, keeping the last one
    df_deduped = df.drop_duplicates(subset=["PROC_CD"], keep="last").copy()

    # Clean up temp column
    df_deduped.drop(columns=["_sort_priority"], inplace=True)

    # 6. LOGGING SUMMARY
    dropped_count = initial_count - len(df_deduped)
    if dropped_count > 0:
        print(f"⚠️ Deduplication Complete: Dropped {dropped_count} duplicate rows.")
    else:
        print("✅ No duplicates found.")
    
    print(f"✅ Final row count: {len(df_deduped)}")

    return df_deduped, df_raw_copy