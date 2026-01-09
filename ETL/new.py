# 1. Clean column names (remove hidden leading/trailing spaces)
clean_df.columns = clean_df.columns.str.strip()
golden_data.columns = golden_data.columns.str.strip()

# 2. DEBUG: Print the exact columns to verify 'COV_DSCN_IND' is actually there
print("Columns in golden_data:", golden_data.columns.tolist())

# 3. If the column exists now, run the merge
if 'COV_DSCN_IND' in golden_data.columns:
    merged_df = pd.merge(
        clean_df,
        golden_data[['DOCUMENTID', 'PROC_CD', 'COV_DSCN_IND']], 
        on=['DOCUMENTID', 'PROC_CD'],
        how='left',
        indicator=True
    )

    is_new = (merged_df['_merge'] == 'left_only')
    
    is_changed = (merged_df['_merge'] == 'both') & \
                 (merged_df['EFFECTIVE_COV_IND'] != merged_df['COV_DSCN_IND'])

    changed_or_new_records = merged_df[is_new | is_changed].copy()
    changed_or_new_records.drop(columns=['_merge'], inplace=True)
    
    print("\nSuccess! Found changed/new records.")
    print(changed_or_new_records)
else:
    print("\nERROR: 'COV_DSCN_IND' is still missing. Please check for typos or case sensitivity.")
