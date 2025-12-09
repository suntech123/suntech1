dict1 = {
    'folder_A': [1, 2, 3, 4, 5],
    'folder_B': [10, 20, 30, 40]
}

dict2 = {
    'folder_A': [4, 5, 6, 7, 8],
    'folder_B': [30, 40, 50, 60]
}

# The Solution: Dictionary Comprehension + Set Intersection (& operator)
dict3 = {k: list(set(dict1[k]) & set(dict2[k])) for k in dict1}

print(dict3)



_------------+-


import os
import shutil

# --- CONFIGURATION ---
SOURCE_FOLDER = '/path/to/folder_A'
DEST_FOLDER = '/path/to/folder_B'

# Ensure destination exists
os.makedirs(DEST_FOLDER, exist_ok=True)

# --- THE LOOP ---
for pdf_basename, intersection_list in final_dict.items():
    
    # 1. Check if the list is NON-EMPTY
    # In Python, an empty list evaluates to False, a populated list to True.
    if intersection_list:
        
        # 2. Handle File Extension
        # If your keys are just "file1" but files are "file1.pdf", add the extension
        filename = pdf_basename if pdf_basename.lower().endswith('.pdf') else f"{pdf_basename}.pdf"
        
        # 3. Define Full Paths
        source_path = os.path.join(SOURCE_FOLDER, filename)
        dest_path = os.path.join(DEST_FOLDER, filename)
        
        # 4. Move the File
        try:
            if os.path.exists(source_path):
                shutil.move(source_path, dest_path)
                print(f"✅ Moved: {filename}")
            else:
                print(f"⚠️  File not found in source: {filename}")
                
        except Exception as e:
            print(f"❌ Error moving {filename}: {e}")

print("-------------------")
print("Operation Complete.")