# 1. Merge, but RENAME the golden column on the fly to avoid conflicts
merged_df = pd.merge(
    clean_df,
    golden_data[['DOCUMENTID', 'PROC_CD', 'COV_DSCN_IND']].rename(columns={'COV_DSCN_IND': 'GOLDEN_COV_IND'}), 
    on=['DOCUMENTID', 'PROC_CD'],
    how='left',
    indicator=True
)

# 2. Define conditions
is_new = (merged_df['_merge'] == 'left_only')

# 3. Compare 'EFFECTIVE_COV_IND' (from clean) vs 'GOLDEN_COV_IND' (from golden)
is_changed = (merged_df['_merge'] == 'both') & \
             (merged_df['EFFECTIVE_COV_IND'] != merged_df['GOLDEN_COV_IND'])

# 4. Filter
changed_or_new_records = merged_df[is_new | is_changed].copy()

# Cleanup
changed_or_new_records.drop(columns=['_merge'], inplace=True)

# Output
print(changed_or_new_records)
