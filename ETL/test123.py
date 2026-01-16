import pandas as pd

# 1. Load the Excel files into Pandas DataFrames
df_tables = pd.read_excel('pdfs_with_table_page_numbers.xlsx')
df_output = pd.read_excel('pdf_output.xlsx')
df_count = pd.read_excel('pdf_count.xlsx')

# 2. Trim whitespaces around 'Filename' text for safety
# We convert to string first to handle cases where Filename might be interpreted as a number
df_tables['Filename'] = df_tables['Filename'].astype(str).str.strip()
df_output['Filename'] = df_output['Filename'].astype(str).str.strip()
df_count['Filename'] = df_count['Filename'].astype(str).str.strip()

# 3. Join the DataFrames on the 'Filename' column
# We use 'outer' join to ensure we don't lose a file if it is missing from one of the sheets. 
# You can change how='outer' to how='inner' if you only want files present in ALL sheets.
merged_df = pd.merge(df_output, df_count, on='Filename', how='outer')
merged_df = pd.merge(merged_df, df_tables, on='Filename', how='outer')

# 4. Select and reorder the columns as requested
final_df = merged_df[['Filename', 'Page_Count', 'Page_Content', 'page numbers with tables']]

# 5. Save the final DataFrame to a CSV file
final_df.to_csv('merged_pdf_data.csv', index=False)

print("CSV file 'merged_pdf_data.csv' created successfully.")
