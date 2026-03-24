"""
Merged Web + RAG Agent
Routes queries intelligently:
- Web Search: for current events, general knowledge, live information
- RAG: for personal information from uploaded documents
"""

from typing import Dict, Any, Literal
from agent.retriver_service import Retriver
from agent.web_agent import get_service_information
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class QueryClassification(BaseModel):
    """Structured output for query classification"""
    query_type: Literal["web", "rag"] = Field(
        description="Classification of query: 'web' for general/current info, 'rag' for personal/document info"
    )


class MergedAgent:
    """Agent that intelligently routes between web search and RAG"""
    
    def __init__(self, groq_key: str = GROQ_API_KEY):
        """Initialize the merged agent with Groq LLM for routing"""
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            api_key=groq_key,
            max_retries=3
        )
    
    def _classify_query(self, query: str) -> str:
        """
        Classify if query needs web search or RAG using structured output
        Returns: 'web' or 'rag'
        """
        try:
            # Create structured LLM
            structured_llm = self.llm.with_structured_output(QueryClassification)
            
            system_msg = SystemMessage(content="""You are a query classifier. Analyze the user's query and determine if it requires:

1. WEB SEARCH - for:
   - Current events, news, latest information
   - General knowledge questions
   - Real-time data (weather, stock prices, etc.)
   - Questions about public figures, companies, products
   - "What is...", "How to...", "Latest...", "Current..." queries
   
2. RAG (Personal Documents) - for:
   - Personal information (my name, my address, my details)
   - Questions about uploaded documents
   - User-specific data
   - "My...", "I...", references to personal documents""")
            
            user_msg = HumanMessage(content=f"Classify this query: {query}")
            
            response = structured_llm.invoke([system_msg, user_msg])
            return response.query_type
                
        except Exception as e:
            print(f"Classification error: {e}")
            # Default to web search on error
            return 'web'
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main method: routes query to appropriate tool
        """
        print(f"\n{'='*60}")
        print(f"📝 Query: {query}")
        print(f"{'='*60}")
        
        # Classify the query
        query_type = self._classify_query(query)
        print(f"🎯 Routing to: {query_type.upper()}")
        
        try:
            if query_type == 'rag':
                # Use RAG for personal information
                print("📚 Searching in personal documents...")
                result = await Retriver(query)
                return {
                    "query": query,
                    "source": "rag",
                    "data": result.get("result", "No information found in documents"),
                    "status": "success"
                }
            else:
                # Use web search for general/current information
                print("🌐 Searching the web...")
                result = get_service_information(query)
                return {
                    "query": query,
                    "source": "web",
                    "data": result.get("data", "No information found"),
                    "status": result.get("status", "success")
                }
                
        except Exception as e:
            return {
                "query": query,
                "source": query_type,
                "data": f"Error: {str(e)}",
                "status": "error"
            }


# Main function to be called from API
async def merged_query(query: str) -> Dict[str, Any]:
    """
    Main entry point for merged web + RAG queries
    
    Args:
        query: User's question
    
    Returns:
        Dictionary with query results from appropriate source
    """
    agent = MergedAgent()
    result = await agent.process_query(query)
    return result
