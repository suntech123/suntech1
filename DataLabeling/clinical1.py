'''
How to Interpret the Output
​The difflib Output: This gives you your hard metrics. You can easily modify the script to count the length of the additions and deletions arrays to calculate your Word Error Rate (WER). This is excellent for logging exactly which entities or clauses were injected by the business rules.
​The util.cos_sim Output: This acts as your safety net. If a human reviewer replaces the word "unexpected" with "unforeseen", difflib will flag a deletion and an addition. However, the SentenceTransformer will recognize the synonyms and still return a similarity score of ~98%, letting you know the edit was merely stylistic and didn't alter the business logic.
'''


import difflib
from sentence_transformers import SentenceTransformer, util

def evaluate_text_modifications(original_text, modified_text):
    """
    Compares an original and modified paragraph using word-level diffs 
    and contextual semantic embeddings.
    """
    
    # ---------------------------------------------------------
    # 1. Lexical Diff (What exact words changed?)
    # ---------------------------------------------------------
    print("### 1. Lexical Diff (Word-Level) ###")
    
    # Split paragraphs into words for a cleaner diff
    orig_words = original_text.split()
    mod_words = modified_text.split()
    
    # Calculate the differences
    diff = difflib.ndiff(orig_words, mod_words)
    
    additions = []
    deletions = []
    
    for token in diff:
        if token.startswith('- '):
            deletions.append(token[2:])
        elif token.startswith('+ '):
            additions.append(token[2:])
            
    print(f"Deletions (Removed by reviewer): {deletions}")
    print(f"Additions (Inserted by reviewer): {additions}\n")

    # ---------------------------------------------------------
    # 2. Semantic Similarity (Did the meaning change?)
    # ---------------------------------------------------------
    print("### 2. Semantic Similarity (Sentence Transformers) ###")
    
    # Load a fast, lightweight pre-trained model for sentence embeddings
    # Note: 'all-MiniLM-L6-v2' is standard for quick semantic similarity
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Convert paragraphs into dense vector embeddings
    embedding_orig = model.encode(original_text, convert_to_tensor=True)
    embedding_mod = model.encode(modified_text, convert_to_tensor=True)
    
    # Compute the cosine similarity between the two vectors
    cosine_score = util.cos_sim(embedding_orig, embedding_mod)
    
    # Extract the float value from the PyTorch tensor
    similarity_percentage = cosine_score[0][0].item() * 100
    
    print(f"Cosine Similarity Score: {similarity_percentage:.2f}%")
    
    if similarity_percentage > 90:
         print("Conclusion: The core meaning is highly preserved despite the edits.")
    elif similarity_percentage > 75:
         print("Conclusion: The meaning is mostly preserved, but notable semantic shifts occurred.")
    else:
         print("Conclusion: The business rules substantially altered the meaning of the paragraph.")

# --- Example Execution ---
if __name__ == "__main__":
    original_paragraph = "The policy covers unexpected damage to the vehicle."
    modified_paragraph = "The updated policy fully covers sudden and unexpected damage to the insured vehicle."
    
    evaluate_text_modifications(original_paragraph, modified_paragraph)