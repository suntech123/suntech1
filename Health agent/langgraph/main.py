from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from tools import multiply_numbers
from uhg_gemini import UHGChatGemini

def main():
    print("Initializing LangGraph Agent...\n")

    # 1. Initialize our fully compliant wrapper
    llm = UHGChatGemini(model_name="gemini-2.5-flash")
    
    # 2. Define tools
    tools = [multiply_numbers]

    # 3. Create the LangGraph Agent
    # This pre-built function automatically wires up the StateGraph, ToolNodes, 
    # and conditional edges because our LLM wrapper now supports standard JSON tool calling.
    graph_app = create_react_agent(llm, tools)

    user_prompt = "I have 1,452 boxes of apples. Each box contains 67 apples. How many apples do I have?"
    print(f"User: {user_prompt}\n")

    # 4. Execute the Graph
    # We pass the input as a LangChain HumanMessage
    inputs = {"messages": [HumanMessage(content=user_prompt)]}
    
    # We stream the graph to see what it's doing behind the scenes
    for event in graph_app.stream(inputs, stream_mode="values"):
        last_message = event["messages"][-1]
        
        # If it's an AI message with a tool call request
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
             for call in last_message.tool_calls:
                 print(f"🧠 Agent requesting tool: {call['name']} with args {call['args']}")
                 
        # If it's an AI message with text (Final Answer)
        elif isinstance(last_message, AIMessage) and last_message.content:
            print(f"\n🤖 Gemini Final Answer: {last_message.content}")

if __name__ == "__main__":
    main()