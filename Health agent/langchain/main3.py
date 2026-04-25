# main.py
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from tools import multiply_numbers
from uhg_gemini import UHGChatGemini  # Our custom wrapper

# 1. We define the ReAct prompt locally. 
# This tells the LLM exactly how to format its text so LangChain can parse it.
react_prompt_template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

def start_langchain_agent():
    # 2. Initialize our custom UHG LangChain model
    llm = UHGChatGemini(model_name='gemini-2.5-flash')

    # 3. Define the tools list
    tools = [multiply_numbers]

    # 4. Create the Prompt object from our string
    prompt = PromptTemplate.from_template(react_prompt_template)

    # 5. Create the LangChain Agent
    agent = create_react_agent(llm, tools, prompt)

    # 6. Create the Agent Executor
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, # Leave this True so you can watch it "think"
        handle_parsing_errors=True
    )

    print("Starting the agent...")
    
    user_prompt = "I have 1,452 boxes of apples. Each box contains 67 apples. How many apples do I have?"
    print(f"User: {user_prompt}")

    # 7. Execute the workflow
    response = agent_executor.invoke({"input": user_prompt})

    print(f"\nGemini: {response['output']}")

if __name__ == "__main__":
    start_langchain_agent()