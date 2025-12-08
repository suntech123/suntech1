#!/bin/bash

# --- CONFIGURATION ---
FOLDER_A="/Users/yourname/path/to/folder_a"
FOLDER_B="/Users/yourname/path/to/folder_b"
DESTINATION="."

# --- YOUR LIST OF STRINGS ---
# You can put full filenames, ID codes, or words like "OBESITY" here.
# Ensure each item is inside double quotes.
search_list=(
    "349c561c"
    "WITH OBESITY"
    "SG-KY-8f591"
    "SG-NM"
    "4182-a662"
)

# --- EXECUTION ---
echo "Starting move operation based on list..."
echo "---------------------------------------"

for search_term in "${search_list[@]}"; do
    # Remove any accidental spaces around the search term
    term=$(echo "$search_term" | xargs)
    
    echo "🔍 Looking for files containing: '$term'"
    
    # --- CHECK FOLDER A ---
    # We use ls to check if a file exists before trying to move it
    # The pattern is: *term* (matches anything before and after the term)
    if ls "$FOLDER_A"/*"$term"* 1> /dev/null 2>&1; then
        echo "   ✅ Found matching file(s) in Folder A. Moving..."
        mv "$FOLDER_A"/*"$term"* "$DESTINATION"
    fi

    # --- CHECK FOLDER B ---
    if ls "$FOLDER_B"/*"$term"* 1> /dev/null 2>&1; then
        echo "   ✅ Found matching file(s) in Folder B. Moving..."
        mv "$FOLDER_B"/*"$term"* "$DESTINATION"
    fi
done

echo "---------------------------------------"
echo "Operation complete."