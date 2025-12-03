import string

def clean_text_block(raw_text_block):
    # 1. Define standard special characters
    # This string contains: !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
    chars_to_remove = string.punctuation

    # 2. Create a translation table
    # The arguments are: (x, y, z)
    # x, y: characters to map (we leave empty)
    # z: characters to delete (our special characters list)
    translator = str.maketrans('', '', chars_to_remove)

    # 3. Apply the translation
    clean_text = raw_text_block.translate(translator)
    
    return clean_text

# --- Usage Example ---

# Assume this is your extracted text block
raw_text = "This is a test block... It contains: patterns, #IDs, and <tags>!"

cleaned_block = clean_text_block(raw_text)

print(f"Original: {raw_text}")
print(f"Cleaned:  {cleaned_block}")