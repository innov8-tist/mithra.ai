"""
Live Agent - Screenshot + Query Analysis
Analyzes screenshot with user query and decides action
"""

from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
import google.generativeai as genai
import os
from dotenv import load_dotenv
import base64

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class LiveAgentResponse(BaseModel):
    """Structured output for live agent analysis"""
    text: str = Field(description="Answer to the user's question about the screenshot. Explain what you see and respond to their query.")
    decision: Literal["fill", "normal"] = Field(
        description="Decision: 'fill' if user wants to autofill the form with their data, 'normal' if they just want explanation/information"
    )


class FormFieldData(BaseModel):
    """Structured output for form field extraction"""
    label: str = Field(description="The label or name of the form field")
    value: str = Field(description="The value to fill in this field based on user's personal information")


class LiveAgent:
    """Agent that analyzes screenshots with user queries"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def analyze_screenshot(self, screenshot_b64: str, query: str) -> Dict[str, Any]:
        """
        Analyze screenshot with user query
        
        Args:
            screenshot_b64: Base64 encoded screenshot
            query: User's question about the screenshot
        
        Returns:
            Dictionary with text response and decision
        """
        try:
            print(f"\n{'='*60}")
            print(f"LIVE AGENT - ANALYZING SCREENSHOT")
            print(f"{'='*60}")
            print(f"Query: {query}")
            
            # Decode base64 image
            if ',' in screenshot_b64:
                screenshot_b64 = screenshot_b64.split(',')[1]
            
            image_data = base64.b64decode(screenshot_b64)
            print(f"Image size: {len(image_data)} bytes")
            
            # First, determine the decision
            decision_prompt = f"""You are a helpful assistant analyzing a screenshot with a user query.

User Query: "{query}"

Analyze the screenshot and decide if the user wants to:
- "fill": Autofill the form with their personal data (keywords: "fill", "autofill", "complete", "enter my details")
- "normal": Just explain or provide information (keywords: "what is", "explain", "tell me", "show me")

Response format:
{{
  "text": "Brief 2-3 sentence answer",
  "decision": "fill" or "normal"
}}"""

            print(f"\nCalling Gemini Vision API...")
            # Call Gemini Vision API for decision
            response = self.model.generate_content([
                decision_prompt,
                {"mime_type": "image/png", "data": image_data}
            ])
            
            response_text = response.text.strip()
            print(f"\nGemini Raw Response:\n{response_text}")
            
            # Try to extract JSON from response
            import json
            import re
            
            # Find JSON in response
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                text = result.get("text", response_text)
                decision = result.get("decision", "normal")
                print(f"\nParsed Decision: {decision}")
                print(f"Parsed Text: {text}")
            else:
                # Fallback: analyze text for decision
                query_lower = query.lower()
                decision = "fill" if any(kw in query_lower for kw in ["fill", "autofill", "complete", "enter my"]) else "normal"
                text = response_text
                print(f"\nFallback Decision: {decision}")
            
            # If decision is "fill", extract form fields and get values from RAG
            if decision == "fill":
                print(f"\n{'='*60}")
                print(f"EXTRACTING FORM FIELDS (Decision: fill)")
                print(f"{'='*60}")
                fields_data = await self._extract_form_fields(image_data, query)
                
                print(f"\nExtracted {len(fields_data)} fields:")
                for field in fields_data:
                    print(f"  - {field.get('label')}: {field.get('value')}")
                
                return {
                    "success": True,
                    "text": text,
                    "decision": decision,
                    "fields": fields_data
                }
            else:
                print(f"\nNo field extraction needed (Decision: normal)")
                return {
                    "success": True,
                    "text": text,
                    "decision": decision
                }
            
        except Exception as e:
            import traceback
            print(f"\n{'='*60}")
            print(f"ERROR IN ANALYZE_SCREENSHOT")
            print(f"{'='*60}")
            print(f"Error: {str(e)}")
            print(traceback.format_exc())
            print(f"{'='*60}\n")
            
            return {
                "success": False,
                "error": str(e),
                "text": "Failed to analyze screenshot",
                "decision": "normal"
            }
    
    async def _extract_form_fields(self, image_data: bytes, query: str) -> list:
        """
        Extract only the specific form field mentioned in the user's query
        and get values from RAG (user's documents) or AI generation
        """
        try:
            print(f"\n{'='*60}")
            print(f"EXTRACTING FORM FIELDS")
            print(f"{'='*60}")
            print(f"Query: {query}")
            
            # First, identify which fields the user is asking about
            extract_prompt = f"""Analyze this form screenshot based on the user's query.

User Query: "{query}"

The user is asking about a SPECIFIC field in the form. 

Your task:
1. Identify which field the user is referring to in their query
2. Extract ONLY that field's label
3. Determine the field type:
   - "personal": Personal data (name, email, phone, address, DOB, gender, etc.) - Get from user documents
   - "subjective": Opinion/preference fields (passion, hobbies, interests, why you want this, etc.) - AI generates

Return as JSON array with ONLY the field(s) mentioned in the query:
[
  {{"label": "Field Label", "field_type": "personal or subjective", "info_type": "what information is needed"}}
]

Examples:
- Query: "Can you fill the email field" → [{{"label": "Email", "field_type": "personal", "info_type": "email"}}]
- Query: "Fill my passion" → [{{"label": "Passion", "field_type": "subjective", "info_type": "passion"}}]
- Query: "What is my phone number" → [{{"label": "Phone", "field_type": "personal", "info_type": "phone"}}]
- Query: "Fill why I want this job" → [{{"label": "Why do you want this job", "field_type": "subjective", "info_type": "job motivation"}}]

IMPORTANT: Only return the specific field(s) mentioned in the user's query."""

            print(f"\nCalling Gemini Vision for field extraction...")
            response = self.model.generate_content([
                extract_prompt,
                {"mime_type": "image/png", "data": image_data}
            ])
            
            response_text = response.text.strip()
            print(f"\nGemini Field Extraction Response:\n{response_text}")
            
            # Extract JSON array
            import json
            import re
            
            # Find JSON array in response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                print("No JSON array found in response")
                return []
            
            fields_info = json.loads(json_match.group())
            print(f"\nParsed {len(fields_info)} field(s):")
            for field in fields_info:
                print(f"  - Label: {field.get('label')}")
                print(f"    Type: {field.get('field_type')}")
                print(f"    Info: {field.get('info_type')}")
            
            # Now get value for each field
            from agent.retriver_service import Retriver
            
            result_fields = []
            for field in fields_info:
                label = field.get("label", "")
                field_type = field.get("field_type", "personal")
                info_type = field.get("info_type", "")
                
                print(f"\n--- Processing field: {label} ---")
                
                if field_type == "personal":
                    # Query RAG for personal data
                    rag_query = f"What is my {info_type}?"
                    print(f"RAG Query: {rag_query}")
                    rag_result = await Retriver(rag_query)
                    
                    # Extract the value from RAG result
                    value = rag_result.get("result", "").strip()
                    print(f"RAG Raw Result: {value}")
                    
                    # Clean up the value
                    value = self._clean_rag_value(value, info_type)
                    print(f"Cleaned Value: {value}")
                else:
                    # Generate subjective/opinion content with AI
                    print(f"Generating subjective content for: {info_type}")
                    value = await self._generate_subjective_value(info_type, label)
                    print(f"Generated Value: {value}")
                
                result_fields.append({
                    "label": label,
                    "value": value
                })
            
            print(f"\n{'='*60}")
            print(f"FIELD EXTRACTION COMPLETE")
            print(f"{'='*60}")
            print(f"Total fields: {len(result_fields)}")
            for field in result_fields:
                print(f"  {field['label']}: {field['value']}")
            print(f"{'='*60}\n")
            
            return result_fields
                
        except Exception as e:
            import traceback
            print(f"\n{'='*60}")
            print(f"ERROR IN EXTRACT_FORM_FIELDS")
            print(f"{'='*60}")
            print(f"Error: {str(e)}")
            print(traceback.format_exc())
            print(f"{'='*60}\n")
            return []
    
    async def _generate_subjective_value(self, info_type: str, label: str) -> str:
        """
        Generate AI content for subjective/opinion fields
        """
        try:
            from agent.retriver_service import Retriver
            
            # First, try to get context from user's documents
            context_query = f"Tell me about the user's background, interests, and qualifications"
            context_result = await Retriver(context_query)
            user_context = context_result.get("result", "")
            
            # Generate appropriate response based on field type
            generation_prompt = f"""Based on the user's background information, generate a suitable response for this form field.

Field Label: "{label}"
Field Type: {info_type}

User Context:
{user_context}

Generate a brief, professional, and relevant response (2-3 sentences max) that would be appropriate for this field.
If the user context doesn't provide relevant information, generate a generic but professional response.

Response should be:
- Concise and to the point
- Professional tone
- Relevant to the field type
- Natural and human-like

Just provide the text value, nothing else."""

            response = self.model.generate_content(generation_prompt)
            value = response.text.strip()
            
            # Clean up any quotes or extra formatting
            value = value.strip('"\'')
            
            return value
            
        except Exception as e:
            print(f"Error generating subjective value: {e}")
            return "Not specified"
    
    def _clean_rag_value(self, rag_response: str, info_type: str) -> str:
        """
        Clean RAG response to extract just the value
        """
        # Remove common phrases
        rag_lower = rag_response.lower()
        
        # Common patterns to remove
        patterns = [
            f"your {info_type} is ",
            f"the {info_type} is ",
            f"my {info_type} is ",
            "according to the document, ",
            "based on the information, ",
        ]
        
        cleaned = rag_response
        for pattern in patterns:
            if pattern in rag_lower:
                # Find the pattern and extract what comes after
                idx = rag_lower.find(pattern)
                cleaned = rag_response[idx + len(pattern):].strip()
                break
        
        # Remove trailing punctuation
        cleaned = cleaned.rstrip('.!?')
        
        # If response is too long (more than 100 chars), it's probably not a clean value
        if len(cleaned) > 100:
            # Try to extract first sentence or line
            cleaned = cleaned.split('.')[0].split('\n')[0].strip()
        
        return cleaned


async def analyze_live_query(screenshot_b64: str, query: str) -> Dict[str, Any]:
    """
    Main entry point for live agent
    
    Args:
        screenshot_b64: Base64 encoded screenshot
        query: User's question
    
    Returns:
        Dictionary with analysis result
    """
    agent = LiveAgent()
    result = await agent.analyze_screenshot(screenshot_b64, query)
    return result
