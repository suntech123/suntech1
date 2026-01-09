import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 1. Setup Sample Data (For demonstration purposes)
# ---------------------------------------------------------
clean_df = pd.DataFrame({
    'DOCUMENT_ID': [101, 102, 103, 104],
    'PROC_CD': ['A1', 'A2', 'A3', 'A4'],
    'EFFECTIVE_COV_IND': ['Y', 'Y', 'N', 'Y'], 
    'OTHER_COL': ['Data', 'Data', 'Data', 'Data']
})

golden_data = pd.DataFrame({
    'DOCUMENT_ID': [101, 102, 103],
    'PROC_CD': ['A1', 'A2', 'A3'],
    'COV_DSCN_IND': ['Y', 'N', 'N'] # 101 matches, 102 differs, 103 matches
})

# ---------------------------------------------------------
# 2. The Solution
# ---------------------------------------------------------

# We merge clean_df (left) with golden_data (right).
# We only bring in the necessary comparison column from golden_data to keep it clean.
merged_df = pd.merge(
    clean_df,
    golden_data[['DOCUMENT_ID', 'PROC_CD', 'COV_DSCN_IND']], 
    on=['DOCUMENT_ID', 'PROC_CD'],
    how='left',
    indicator=True # Adds a column '_merge' telling us where the data came from
)

# Define conditions
# 1. New Record: The record exists in clean_df but not in golden_data (left_only)
is_new = (merged_df['_merge'] == 'left_only')

# 2. Changed Record: Exists in both, but the indicators are different
# Note: We use fillna to handle cases where one might be null, or rely on standard python logic
# where 'Value' != NaN is True.
is_changed = (merged_df['_merge'] == 'both') & \
             (merged_df['EFFECTIVE_COV_IND'] != merged_df['COV_DSCN_IND'])

# Apply Filter
changed_or_new_records = merged_df[is_new | is_changed].copy()

# Optional: Clean up the output by dropping the helper column
changed_or_new_records.drop(columns=['_merge'], inplace=True)

# ---------------------------------------------------------
# 3. Output
# ---------------------------------------------------------
print("Original Clean DF:")
print(clean_df)
print("\nGolden Data:")
print(golden_data)
print("\nRecords New or Changed:")
print(changed_or_new_records)
