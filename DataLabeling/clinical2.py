import pandas as pd
from pathlib import Path

def load_excel_files(root_folder_path):
    # Define the root directory
    root_dir = Path(root_folder_path)
    
    # List to store each individual dataframe
    dataframes = []
    
    # rglob recursively searches through all subfolders
    # '*.xls*' ensures it catches both .xls and .xlsx files
    for file_path in root_dir.rglob('*.xls*'):
        try:
            # Read the Excel file into a temporary dataframe
            df = pd.read_excel(file_path)
            
            # Optional but recommended: Track which file the data came from
            df['source_file'] = file_path.name
            
            dataframes.append(df)
            print(f"Successfully loaded: {file_path.name}")
            
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")
            
    # Combine all dataframes into a single master dataframe
    if dataframes:
        master_df = pd.concat(dataframes, ignore_index=True)
        print(f"\nTotal files loaded: {len(dataframes)}")
        print(f"Total rows in combined dataframe: {len(master_df)}")
        return master_df
    else:
        print("\nNo Excel files were found in the specified directory.")
        return pd.DataFrame()

# --- Execution ---
# Replace this with the actual path to your main folder
folder_path = 'path/to/your/main/folder'
combined_dataframe = load_excel_files(folder_path)

# Display the first few rows
print(combined_dataframe.head())