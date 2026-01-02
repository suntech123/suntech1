import os
import pandas as pd

# 1. Setup
folder_path = './your_pdf_folder'  # Change this to your folder path
pdf_data = {}                      # Initialize empty dictionary

# 2. Loop through files
for filename in os.listdir(folder_path):
    if filename.endswith(".pdf"):
        file_path = os.path.join(folder_path, filename)
        
        # --- YOUR EXTRACTION LOGIC HERE ---
        # Assuming you have logic that returns a list of pages/content
        # For this example, let's pretend we get a list of strings
        # page_list = your_custom_function(file_path) 
        
        # Placeholder example list:
        page_list = [f"Content of page 1 for {filename}", f"Content of page 2 for {filename}"]
        
        # 3. Populate Dictionary
        # Key = Filename, Value = List of pages
        pdf_data[filename] = page_list

# 4. Create Pandas DataFrame
# We convert the dict items to a list of tuples to keep the structure clean
df = pd.DataFrame(list(pdf_data.items()), columns=['Filename', 'Page_Content'])

# 5. Write to CSV
df.to_csv('pdf_output.csv', index=False)

print("CSV created successfully!")