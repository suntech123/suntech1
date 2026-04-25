pip install google-generativeai

import google.generativeai as genai
import os

# 1. Setup your API Key (Replace 'YOUR_API_KEY' with your actual key)
genai.configure(api_key="YOUR_API_KEY")

# 2. Define the "Tool"
# This is a standard Python function. The docstring ("""...""") is VERY important.
# Gemini reads the docstring to understand WHEN and HOW to use this tool.
def multiply_numbers(a: float, b: float) -> float:
    """Multiplies two numbers together and returns the result."""
    print(f"\n[SYSTEM LOG] 👉 Gemini decided to use the tool: Multiplying {a} by {b}...\n")
    return a * b

# 3. Create the Agent
# We initialize the model and give it the tool we just created.
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    tools=[multiply_numbers] # This makes it an agent!
)

# 4. Start the Agentic Workflow
print("Starting the agent...")
chat = model.start_chat(enable_automatic_function_calling=True)

# We ask a question that requires exact math
user_prompt = "I have 1,452 boxes of apples. Each box contains 67 apples. How many apples do I have in total?"
print(f"User: {user_prompt}")

# Send the message to Gemini
response = chat.send_message(user_prompt)

# Print the final result
print(f"Gemini: {response.text}")