# tools.py
from langchain_core.tools import tool

@tool
def multiply_numbers(a: float, b: float) -> float:
    """Multiplies two numbers together and returns the result."""
    print(f"\n[SYSTEM LOG] 👈 Gemini decided to use the tool: Multiplying {a} by {b}...\n")
    return a * b