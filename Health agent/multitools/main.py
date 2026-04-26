from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage # Added missing AIMessage import

# Import multiple tools from the separate tools.py file
from tools import multiply_numbers, add_numbers
from uhg_gemini import UHGChatGemini

def main():
    print("Initializing LangGraph Agent...\n")

    # 1. Initialize the LLM wrapper
    llm = UHGChatGemini(model_name="gemini-2.5-flash")

    # 2. Define tools as a list of imported functions
    tools = [multiply_numbers, add_numbers]

    # 3. Create the LangGraph Agent
    # This pre-built function automatically wires up the StateGraph, ToolNodes, 
    # and conditional edges to handle multi-step reasoning and tool chaining.
    graph_app = create_react_agent(llm, tools)

    # Updated prompt to trigger sequential tool usage (Multiplication -> Addition)
    user_prompt = "I have 1,452 boxes of apples. Each box contains 67 apples. I also just received a separate shipment of 500 loose apples. How many apples do I have in total?"
    print(f"User: {user_prompt}\n")

    # 4. Execute the Graph
    inputs = {"messages": [HumanMessage(content=user_prompt)]}

    # Stream the graph to see what it's doing behind the scenes
    for event in graph_app.stream(inputs, stream_mode="values"):
        last_message = event["messages"][-1]

        # If it's an AI message with a tool call request
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
             for call in last_message.tool_calls:
                 print(f"🧠 Agent requesting tool: {call['name']} with args {call['args']}")

        # If it's an AI message with text (Final Answer)
        elif isinstance(last_message, AIMessage) and last_message.content:
            # We filter out intermediate "thought" blocks if they exist and only print the final answer
            if not last_message.tool_calls:
                print(f"\n🤖 Gemini Final Answer: {last_message.content}")

if __name__ == "__main__":
    main()