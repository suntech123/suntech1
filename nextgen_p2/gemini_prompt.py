prompt = """
    I have provided 1-bit black and white images of the first few pages of a document.
    These pages contain a Table of Contents (ToC).
    
    Your task is to extract the complete Table of Contents across all these pages 
    and reconstruct it into a single, unified hierarchical JSON structure.
    
    Output the result STRICTLY as a JSON Array of objects using the following schema:
    [
      {
        "title": "string (The name of the section)",
        "page": "string (The printed page number for this section)",
        "subsections": [
            // List of child section objects following this exact same schema. 
            // Leave empty [] if there are no sub-sections.
        ]
      }
    ]
    
    Important rules:
    1. Only include actual ToC items.
    2. Respect the hierarchical indentation/numbering shown in the images.
    3. Output pure JSON. No markdown formatting or explanations.
    """