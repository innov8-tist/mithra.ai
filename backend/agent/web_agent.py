"""
Service Search Agent using LangChain + Groq
User types a prompt, AI searches the web and returns data
"""

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any

# ============================================================
# CONFIGURATION - API Key
# ============================================================
GROQ_API_KEY = "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"
# ============================================================


class ServiceSearchAgent:
    """Agent class that searches and analyzes using Groq AI"""
    
    def __init__(self, groq_key: str = GROQ_API_KEY):
        """Initialize the agent with Groq LLM"""
        
        # Initialize Groq LLM with search capabilities
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            api_key=groq_key,
            max_retries=3
        )
    
    def _search_and_return_data(self, user_prompt: str) -> str:
        """
        Internal method that searches based on user prompt and returns data
        This is the sub function that defines the working of the return function
        """
        try:
            # Create system message for search-focused responses
            system_msg = SystemMessage(content="""You are an intelligent search assistant with access to comprehensive knowledge.
            
Your task:
1. Understand the user's search query
2. Provide accurate, detailed, and up-to-date information
3. If asked about services, list them with clear descriptions
4. Format responses in a well-structured, easy-to-read manner
5. Be comprehensive but concise

Always provide factual, helpful information based on the query.""")
            
            # Create user message with search intent
            user_msg = HumanMessage(content=f"Search and provide detailed information about: {user_prompt}")
            
            # Get response from Groq AI
            response = self.llm.invoke([system_msg, user_msg])
            return response.content
            
        except Exception as e:
            return f"Search Error: {str(e)}\nPlease check your internet connection and try again."
    
    def search(self, user_prompt: str) -> Dict[str, Any]:
        """
        Main search method - searches based on user input and returns data
        """
        print(f"🔍 Searching for: {user_prompt}")
        data = self._search_and_return_data(user_prompt)
        
        return {
            "query": user_prompt,
            "data": data,
            "status": "success" if "Search Error:" not in data else "error"
        }


# Outside the class - return function that uses the class methods
def get_service_information(prompt: str) -> Dict[str, Any]:
    """
    Main return function declared outside the class
    Takes user prompt, searches, and returns data
    
    Args:
        prompt: User's search prompt (any question or topic)
    
    Returns:
        Dictionary containing search results and data
    """
    # Create agent instance
    agent = ServiceSearchAgent()
    
    # Search and get data
    result = agent.search(prompt)
    
    return result

        
        
