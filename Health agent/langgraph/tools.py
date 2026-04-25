from langchain_core.tools import tool

@tool
def multiply_numbers(a: float, b: float) -> float:
    """Multiplies two numbers together and returns the result."""
    print(f"\n[SYSTEM LOG] 👈 Tool Executed: Multiplying {a} by {b}...\n")
    return a * b