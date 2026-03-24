from typing import Dict, Any, List
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")


class ExtractIdMatching(BaseModel):
    """Structured output for service ID extraction"""
    id: int = Field(description="Extract the id of the matching service from the user query")


class NavigationAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            api_key=groq_key,
            max_retries=3
        )
        self.services = [
            {
                "id": 1,
                "title": "EDistrict",
                "description": "Apply for certificates like birth, death, income, and other district services online",
                "link": "https://edistrict.kerala.gov.in/registerPortalUser.do"
            },
            {
                "id": 2,
                "title": "GST Portal",
                "description": "GST registration, return filing, and tax payment services",
                "link": "https://reg.gst.gov.in/registration/"
            },
            {
                "id": 3,
                "title": "Kerala Concession",
                "description": "Fill the application form for KSRTC concession",
                "link": "https://concessionksrtc.com/school-register"
            },
            {
                "id": 4,
                "title": "College Admission Form",
                "description": "Fill the admission application form",
                "link": "https://admissions.cusat.ac.in/?tag=register&category=all"
            },
            {
                "id": 5,
                "title": "SIR Application Form",
                "description": "VOTERS' SERVICE PORTAL",
                "link": "https://voters.eci.gov.in/searchInSIR/S2UA4DPDF-JK4QWODSE"
            }
        ]
    
    def llm_invoke(self, query: str) -> Dict[str, Any]:
        """
        Match user query to a service and return the service details
        """
        try:
            # Create structured LLM
            structured_llm = self.llm.with_structured_output(ExtractIdMatching)
            
            # Build services list for context
            services_text = "\n".join([
                f"ID {s['id']}: {s['title']} - {s['description']}"
                for s in self.services
            ])
            
            system_msg = SystemMessage(content=f"""You are a service matching assistant. 
Match the user's query to the most appropriate service from this list:

{services_text}

Return the ID of the best matching service.""")
            
            user_msg = HumanMessage(content=f"Find the service for: {query}")
            
            response = structured_llm.invoke([system_msg, user_msg])
            service_id = response.id
            
            # Find the matching service
            matched_service = next(
                (s for s in self.services if s["id"] == service_id),
                None
            )
            
            if matched_service:
                return {
                    "success": True,
                    "link": matched_service["link"]
                }
            else:
                return {
                    "success": False,
                    "error": "No matching service found"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


async def navigate_to_service(query: str) -> Dict[str, Any]:
    """
    Main entry point for navigation agent
    
    Args:
        query: User's service request
    
    Returns:
        Dictionary with matched service details and link
    """
    agent = NavigationAgent()
    result = agent.llm_invoke(query)
    return result
