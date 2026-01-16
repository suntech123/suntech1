import pandas as pd

# 1. Load the Excel files
df_tables = pd.read_excel('pdfs_with_table_page_numbers.xlsx')
df_output = pd.read_excel('pdf_output.xlsx')
df_count = pd.read_excel('pdf_count.xlsx')

# 2. Trim whitespaces around 'Filename'
df_tables['Filename'] = df_tables['Filename'].astype(str).str.strip()
df_output['Filename'] = df_output['Filename'].astype(str).str.strip()
df_count['Filename'] = df_count['Filename'].astype(str).str.strip()

# 3. Merge DataFrames
# Start with df_tables and left join the others.
# Any Filename not in df_tables will be dropped.
merged_df = pd.merge(df_tables, df_output, on='Filename', how='left')
merged_df = pd.merge(merged_df, df_count, on='Filename', how='left')

# 4. Select and reorder columns
# (Optional: Fill NaN values if a file in df_tables wasn't found in output/count)
final_df = merged_df[['Filename', 'Page_Count', 'Page_Content', 'page numbers with tables']]

# 5. Save to CSV
final_df.to_csv('filtered_pdf_data.csv', index=False)

print("Filtered CSV created successfully.")
