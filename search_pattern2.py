import pandas as pd
import numpy as np

def get_exclusions_from_df(df, table_name, search_pattern=None, suffix='(exclusion)'):
    # Default patterns if none provided (Matches Line 45)
    if search_pattern is None:
        search_pattern = ['*EXCLUSIONS*', '*NOT COVERED*', "*PLAN DOESN'T COVER*"]

    # 1. Clean Regex: Convert GLOB patterns (e.g., *TEXT*) to Regex (e.g., TEXT)
    # We join them with '|' for OR logic.
    # removing the asterisks for pandas .str.contains()
    clean_patterns = [p.replace('*', '').replace('?', '.') for p in search_pattern]
    regex_pattern = '|'.join(clean_patterns)

    # 2. Identify Columns (Matches Lines 50-51)
    # Find columns starting with 'heading'
    all_heading_cols = [c for c in df.columns if c.startswith('heading')]
    
    # Select only the last 5 heading columns (Matches Line 54 logic: columns[-5:])
    # Note: If you want ALL headings, remove the [-5:].
    selected_cols = all_heading_cols[-5:]

    # ---------------------------------------------------------
    # STEP 3: The Filter (Matches Line 52 & 62 WHERE clause)
    # ---------------------------------------------------------
    # Check if ANY of the selected columns contain the pattern (Case Insensitive)
    # We create a mask for headers
    header_mask = df[selected_cols].apply(
        lambda x: x.str.contains(regex_pattern, case=False, na=False)
    ).any(axis=1)

    # Check validity of 'text' column (Matches Line 62: text != 'None' and trim != '')
    text_mask = (df['text'].replace('None', np.nan).notna()) & (df['text'].str.strip() != '')

    # Apply Filter
    result_df = df[header_mask & text_mask].copy()

    if result_df.empty:
        return []

    # ---------------------------------------------------------
    # STEP 4: Calculate SECTION_HEADER (Matches Line 57 & 62)
    # Logic: Find the FIRST column (left-to-right) that matches the pattern.
    # ---------------------------------------------------------
    
    # Create a DataFrame of just the values that match the pattern
    # If a cell matches, keep value. If not, make it NaN.
    matches_only = result_df[selected_cols].apply(
        lambda x: np.where(x.str.contains(regex_pattern, case=False, na=False), x, np.nan)
    )
    
    # Backfill (bfill) axis=1 so the first non-null value moves to the first column
    # Then grab the first column. This simulates COALESCE from left-to-right on matches.
    result_df['SECTION_HEADER'] = matches_only.bfill(axis=1).iloc[:, 0]
    
    # Handle Fallback (Matches 'DUMMY_SECTION' in Line 61)
    result_df['SECTION_HEADER'] = result_df['SECTION_HEADER'].fillna('DUMMY_SECTION')

    # ---------------------------------------------------------
    # STEP 5: Calculate CATEGORY (Matches Line 58 & 62)
    # Logic: The deepest (right-most) non-null header, regardless of pattern.
    # ---------------------------------------------------------
    
    # Replace string "None" with actual NaN
    clean_headers = result_df[selected_cols].replace('None', np.nan)
    
    # Forward fill (ffill) propagates the last valid value to the right.
    # Taking the last column gives us the deepest header.
    result_df['CATEGORY'] = clean_headers.ffill(axis=1).iloc[:, -1]
    
    # Handle Fallback ('DUMMY')
    result_df['CATEGORY'] = result_df['CATEGORY'].fillna('DUMMY')

    # ---------------------------------------------------------
    # STEP 6: Final Clean Up (Matches Line 62 CASE statement)
    # Logic: If SECTION_HEADER == CATEGORY, then NULL. Else CATEGORY + suffix.
    # ---------------------------------------------------------
    
    # 1. Compare Header vs Category
    result_df['FINAL_CATEGORY'] = np.where(
        result_df['SECTION_HEADER'] == result_df['CATEGORY'], 
        None, 
        result_df['CATEGORY']
    )

    # 2. Add Suffix (only if not None)
    # We use a mask to add suffix only where FINAL_CATEGORY is not None
    not_none_mask = result_df['FINAL_CATEGORY'].notna()
    result_df.loc[not_none_mask, 'FINAL_CATEGORY'] = result_df.loc[not_none_mask, 'FINAL_CATEGORY'].astype(str) + suffix

    # 3. Add formatting columns
    result_df['TABLE_NAME'] = table_name
    result_df['SECTION'] = 'exclusions'

    # Select final columns to match output format
    final_output = result_df[[
        'TABLE_NAME', 
        'SECTION', 
        'SECTION_HEADER', 
        'FINAL_CATEGORY', 
        'text'
    ]]

    # distinct/drop_duplicates (Matches SELECT DISTINCT)
    return final_output.drop_duplicates()

# Example Usage:
# df_result = get_exclusions_from_df(df, "MyPolicyTable")
# print(df_result)