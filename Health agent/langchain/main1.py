# main.py
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent

from tools import multiply_numbers
from uhg_gemini import UHGChatGemini  # Our custom wrapper

def start_langchain_agent():
    # 1. Initialize our custom UHG LangChain model
    llm = UHGChatGemini(model_name='gemini-2.5-flash')

    # 2. Define the tools list
    tools = [multiply_numbers]

    # 3. Pull the standard LangChain ReAct prompt
    # This prompt tells the LLM *how* to output tool requests in text format
    prompt = hub.pull("hwchase17/react")

    # 4. Create the LangChain Agent (The Brain)
    agent = create_react_agent(llm, tools, prompt)

    # 5. Create the Agent Executor (The Engine)
    # verbose=True will print LangChain's thought process to the console
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=True # Good practice for custom LLMs
    )

    # 6. Execute the workflow exactly as shown in your image
    print("Starting the agent...")
    
    user_prompt = "I have 1,452 boxes of apples. Each box contains 67 apples. How many apples do I have?"
    print(f"User: {user_prompt}")

    # invoke() replaces chat.send_message()
    response = agent_executor.invoke({"input": user_prompt})

    # The final answer is stored in the 'output' key
    print(f"Gemini: {response['output']}")

if __name__ == "__main__":
    start_langchain_agent()