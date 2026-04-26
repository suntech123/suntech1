from langchain_core.tools import tool

@tool
def multiply_numbers(a: int, b: int) -> int:
    """
    Multiply two numbers. Use this tool strictly when you need to find the product of two numbers.
    """
    return a * b

@tool
def add_numbers(a: int, b: int) -> int:
    """
    Add two numbers together. Use this tool strictly when you need to calculate a total sum.
    """
    return a + b