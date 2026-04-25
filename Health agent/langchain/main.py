# main.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# Import your custom wrapper
from uhg_gemini import UHGChatGemini
from config import settings 

def run_analysis(text_to_analyze: str, provider: str = "gemini"):
    # 1. Initialize the requested model
    if provider == "gemini":
        # Uses your custom UHG auth logic natively
        llm = UHGChatGemini(model_name="gemini-2.5-flash")
    elif provider == "openai":
        # Uses standard OpenAI logic
        llm = ChatOpenAI(model="gpt-4o", api_key=settings.openai_api_key)
    else:
        raise ValueError("Invalid provider")

    # 2. Create a standard LangChain Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful data analyst. Be concise."),
        ("human", "Please summarize the following text: {text}")
    ])

    # 3. Build the Chain using LCEL (LangChain Expression Language)
    # This chain works identically regardless of which LLM is plugged into it.
    chain = prompt | llm | StrOutputParser()

    # 4. Execute the chain
    result = chain.invoke({"text": text_to_analyze})
    return result

if __name__ == "__main__":
    sample_text = "The quick brown fox jumps over the lazy dog. It was a spectacular jump."
    
    print("--- Testing UHG Gemini ---")
    print(run_analysis(sample_text, provider="gemini"))
    
    print("\n--- Testing OpenAI ---")
    print(run_analysis(sample_text, provider="openai"))