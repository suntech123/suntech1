import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()  # Load OpenAI API key from .env file

class JSONSummarizerAgent:
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.llm = ChatOpenAI(model=model_name)
        self.summary_template = """
        Analyze the following JSON data and provide a comprehensive summary:
        {json_data}
        
        Structure your summary with:
        - Key statistics
        - Important fields
        - Notable patterns
        - Critical insights
        
        Use bullet points and keep it under 200 words.
        """

    def load_json_data(self, file_path: str) -> Dict[str, Any]:
        """Load and validate JSON data from file"""
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                if not isinstance(data, (dict, list)):
                    raise ValueError("JSON root should be object or array")
                return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Error loading JSON: {str(e)}")

    def summarize_data(self, json_data: Dict[str, Any], custom_prompt: str = None) -> str:
        """Generate AI-powered summary of JSON data"""
        prompt_template = ChatPromptTemplate.from_template(
            custom_prompt or self.summary_template
        )
        
        chain = prompt_template | self.llm
        return chain.invoke({"json_data": json.dumps(json_data, indent=2)}).content

# Example usage
if __name__ == "__main__":
    agent = JSONSummarizerAgent()
    
    try:
        # Load sample data
        data = agent.load_json_data("data/sales.json")
        
        # Generate summary
        summary = agent.summarize_data(data)
        print("📊 JSON Data Summary:")
        print(summary)
        
        # Custom summary example
        custom_prompt = """Extract key metrics from this sales data:
        {json_data}
        
        Focus on:
        - Total revenue
        - Best selling product
        - Monthly trends
        - Customer demographics
        """
        metrics_summary = agent.summarize_data(data, custom_prompt)
        print("\n🔍 Custom Metrics Summary:")
        print(metrics_summary)
        
    except Exception as e:
        print(f"Error: {str(e)}")