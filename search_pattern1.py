import pandas as pd
import numpy as np

# 1. Setup: Define your search patterns
# Note: In Pandas, we don't need the '*' wildcards. 
# "contains" automatically looks everywhere in the string.
search_patterns = ['EXCLUSIONS', 'NOT COVERED']

# Join them with a pipe '|' to create a Regex "OR" condition
# Result: "EXCLUSIONS|NOT COVERED"
regex_pattern = '|'.join(search_patterns)

# 2. Identify Header Columns automatically
header_cols = [col for col in df.columns if col.startswith('header')]

# ---------------------------------------------------------
# LOGIC PART 1: The Filter (WHERE clause)
# ---------------------------------------------------------

# Create a mask initialized to False for all rows
mask = pd.Series(False, index=df.index)

for col in header_cols:
    # A. Clean: Treat string "None" as actual NaN (matches SQL logic)
    #    (Only needed if your CSV actually has the text "None")
    column_clean = df[col].replace('None', np.nan)
    
    # B. Check: Case-insensitive search
    #    case=False -> handles UPPER/lower
    #    na=False   -> ensures NaNs don't crash the code
    matches = column_clean.str.contains(regex_pattern, case=False, na=False, regex=True)
    
    # C. Combine: Update mask (Bitwise OR)
    #    If match found in header1 OR header2 OR header3...
    mask = mask | matches

# Apply the filter to get the resulting rows
result_df = df[mask].copy()

# ---------------------------------------------------------
# LOGIC PART 2: The Selection (COALESCE clause)
# ---------------------------------------------------------
# The SQL code reversed the columns and picked the first non-null.
# In Pandas, this means picking the "last valid value" in the header columns.

if not result_df.empty:
    # 1. Forward fill (propagate last valid value to the right)
    # 2. Select the last column
    result_df['selected_header'] = result_df[header_cols].replace('None', np.nan).ffill(axis=1).iloc[:, -1]

# Display result
print(result_df[['selected_header', 'text']])