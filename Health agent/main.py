'''
Now look at how clean and agnostic your main application code becomes. It doesn't know about tokens, headers, or specific SDKs.
'''

# main.py
# (Load your .env file here first using python-dotenv)

from llm.factory import get_llm

def process_document(text: str, use_provider: str = "gemini"):
    # 1. Get the requested LLM dynamically
    llm = get_llm(use_provider)
    
    prompt = f"Summarize this document: {text}"
    
    # 2. Call the standardized method. The application doesn't care 
    # if it's hitting OpenAI or the custom UHG Gemini Gateway.
    summary = llm.generate_text(prompt)
    
    return summary

if __name__ == "__main__":
    # Test with UHG Gemini
    print("Gemini Output:", process_document("Python is a great language.", "gemini"))
    
    # Test with ChatGPT
    print("OpenAI Output:", process_document("Python is a great language.", "openai"))