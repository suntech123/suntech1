#!/bin/bash

# --- CONFIGURATION ---
FOLDER_A="/Users/yourname/path/to/folder_a"
FOLDER_B="/Users/yourname/path/to/folder_b"
DESTINATION="."

# ENTER THE TEXT YOU WANT TO SEARCH FOR HERE
# Example: "OBESITY" or "SG-IL" or "462b58d2"
SEARCH_TEXT="OBESITY"

# --- EXECUTION ---
echo "Looking for files containing: '$SEARCH_TEXT' ..."

# Function to move files safely
move_matching_files() {
    local source_folder="$1"
    
    # Check if any files match the pattern *TEXT*
    # 2>/dev/null hides errors if no files are found
    if ls "$source_folder"/*"$SEARCH_TEXT"* 1> /dev/null 2>&1; then
        echo "✅ Found matches in: $source_folder"
        
        # The quotes around the path handle files with spaces
        mv "$source_folder"/*"$SEARCH_TEXT"* "$DESTINATION"
        echo "   -> Moved to current folder."
    else
        echo "ℹ️  No files containing '$SEARCH_TEXT' found in $source_folder"
    fi
}

# Run for both folders
move_matching_files "$FOLDER_A"
move_matching_files "$FOLDER_B"

echo "--------------------------------"
echo "Done."