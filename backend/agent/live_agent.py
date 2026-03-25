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
    decision: Literal["inject", "normal"] = Field(
        description="Decision: 'inject' if user wants to autofill/fill the form with their data (use CDP injection), 'normal' if they just want explanation/information"
    )


class FormFieldData(BaseModel):
    """Structured output for form field extraction"""
    label: str = Field(description="The label or name of the form field")
    value: str = Field(description="The value to fill in this field based on user's personal information")


class LiveAgent:
    """Agent that analyzes screenshots with user queries"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def analyze_screenshot(self, screenshot_b64: str, query: str, fields: list = None) -> Dict[str, Any]:
        """
        Analyze screenshot with user query

        Args:
            screenshot_b64: Base64 encoded screenshot
            query: User's question about the screenshot
            fields: Optional list of extracted form fields from page

        Returns:
            Dictionary with text response and decision
        """
        try:
            print(f"\n{'='*60}")
            print(f"LIVE AGENT - ANALYZING SCREENSHOT")
            print(f"{'='*60}")
            print(f"Query: {query}")
            print(f"Extracted fields provided: {len(fields) if fields else 0}")

            # Decode base64 image
            if ',' in screenshot_b64:
                screenshot_b64 = screenshot_b64.split(',')[1]

            image_data = base64.b64decode(screenshot_b64)
            print(f"Image size: {len(image_data)} bytes")

            # First, determine the decision
            decision_prompt = f"""You are a helpful AI assistant analyzing a form screenshot with a user's voice query.

User Query: "{query}"

ANALYZE THE USER'S INTENT:

1. **INJECT Intent** (Form Filling):
   - User wants to fill/autofill form fields with data
   - Keywords: "fill", "autofill", "complete", "enter", "populate", "select", "my [field] is [value]"
   - Examples: "Fill my email", "Select Kottayam in District", "My name is Naveen"
   - Action: Extract field and value, then fill the form

2. **NORMAL Intent** (Information/Help):
   - User wants explanation, information, or help understanding the form
   - Keywords: "what is", "explain", "tell me", "show me", "describe", "help", "how to", "what does"
   - Examples: "What is this form?", "Explain the District field", "What documents are needed?"
   - Action: Provide helpful explanation as an assistant

DECISION RULES:
- If user mentions filling/entering/selecting ANY field → "inject"
- If user asks questions about the form/fields → "normal"
- If user provides explicit values (like "my name is X") → "inject"
- If unclear, default to "normal" (safer to explain than to fill incorrectly)

Response format (JSON):
{{
  "text": "Brief 2-3 sentence response to the user",
  "decision": "inject" or "normal"
}}

Examples:
- Query: "Fill my email" → {{"text": "I'll fill your email address from your documents.", "decision": "inject"}}
- Query: "My name is Naveen" → {{"text": "I'll fill the name field with Naveen.", "decision": "inject"}}
- Query: "Select Kottayam in District" → {{"text": "I'll select Kottayam in the District dropdown.", "decision": "inject"}}
- Query: "What is this form about?" → {{"text": "This appears to be a registration form...", "decision": "normal"}}
- Query: "Explain the District field" → {{"text": "The District field is where you select...", "decision": "normal"}}"""

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
                decision = "inject" if any(kw in query_lower for kw in ["fill", "autofill", "complete", "enter my", "populate", "select"]) else "normal"
                text = response_text
                print(f"\nFallback Decision: {decision}")

            # If decision is "inject", extract form fields and get values from RAG
            if decision == "inject":
                print(f"\n{'='*60}")
                print(f"EXTRACTING FORM FIELDS (Decision: inject)")
                print(f"{'='*60}")
                fields_data = await self._extract_form_fields(image_data, query, fields)

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
    
    async def _extract_form_fields(self, image_data: bytes, query: str, fields: list = None) -> list:
        """
        Extract only the specific form field mentioned in the user's query
        and get values from RAG (user's documents) or AI generation

        Args:
            image_data: Screenshot image data
            query: User's query
            fields: Optional list of extracted form fields from page (with IDs, labels, types, options)
        """
        try:
            print(f"\n{'='*60}")
            print(f"EXTRACTING FORM FIELDS")
            print(f"{'='*60}")
            print(f"Query: {query}")
            print(f"Page fields provided: {len(fields) if fields else 0}")

            if fields:
                print(f"\nAvailable fields on page:")
                for field in fields[:10]:  # Show first 10
                    print(f"  - {field.get('label', 'N/A')} (id: {field.get('id', 'N/A')}, tag: {field.get('tag', 'N/A')})")

            # First, identify which fields the user is asking about
            extract_prompt = f"""You are analyzing a user's voice query to identify which form field they want to fill and what value to use.

User Query: "{query}"

YOUR TASK:
1. Identify which form field the user is referring to
2. Extract the field's label/name
3. Determine the VALUE SOURCE with PRIORITY:

VALUE PRIORITY (MOST IMPORTANT):
   **PRIORITY 1 - EXPLICIT VALUE** (Highest Priority):
   - User explicitly stated a value in their query
   - Examples: "My name is Naveen", "Select Kottayam in District", "Fill email as john@example.com"
   - Field type: "explicit"
   - ALWAYS use this value if provided - DO NOT query documents

   **PRIORITY 2 - PERSONAL DATA** (Use if no explicit value):
   - User asks to fill a field but doesn't provide the value
   - Examples: "Fill my email", "Enter my phone number", "Complete the name field"
   - Field type: "personal"
   - Get value from user's documents via RAG

   **PRIORITY 3 - SUBJECTIVE/AI GENERATED** (Use if not personal data):
   - Opinion/preference fields that need AI generation
   - Examples: "Fill my passion", "Why do you want this job", "Tell us about yourself"
   - Field type: "subjective"
   - AI generates appropriate content

RETURN FORMAT (JSON array):
[
  {{
    "label": "Field Label",
    "field_type": "explicit" or "personal" or "subjective",
    "info_type": "what information is needed",
    "explicit_value": "value if user stated it, otherwise null"
  }}
]

EXAMPLES:

Explicit Values (Priority 1):
- "My name is Naveen" → [{{"label": "Name", "field_type": "explicit", "info_type": "name", "explicit_value": "Naveen"}}]
- "Select Kottayam in District" → [{{"label": "District", "field_type": "explicit", "info_type": "district", "explicit_value": "Kottayam"}}]
- "Fill email as john@example.com" → [{{"label": "Email", "field_type": "explicit", "info_type": "email", "explicit_value": "john@example.com"}}]
- "Enter phone number 9876543210" → [{{"label": "Phone", "field_type": "explicit", "info_type": "phone", "explicit_value": "9876543210"}}]

Personal Data (Priority 2):
- "Fill my email" → [{{"label": "Email", "field_type": "personal", "info_type": "email", "explicit_value": null}}]
- "Enter my phone number" → [{{"label": "Phone", "field_type": "personal", "info_type": "phone", "explicit_value": null}}]
- "Complete the name field" → [{{"label": "Name", "field_type": "personal", "info_type": "name", "explicit_value": null}}]

Subjective (Priority 3):
- "Fill my passion" → [{{"label": "Passion", "field_type": "subjective", "info_type": "passion", "explicit_value": null}}]
- "Why do you want this job" → [{{"label": "Why do you want this job", "field_type": "subjective", "info_type": "job motivation", "explicit_value": null}}]

CRITICAL RULES:
1. If user says "my X is Y" or "select Y in X" → ALWAYS use explicit value Y
2. If user says "fill my X" without value → Use personal data from documents
3. Return ONLY the field(s) mentioned in the query
4. explicit_value must be the EXACT value user stated, not paraphrased"""

            print(f"\nCalling Gemini for field identification...")
            response = self.model.generate_content(extract_prompt)

            response_text = response.text.strip()
            print(f"\nGemini Field Identification Response:\n{response_text}")

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
                print(f"    Explicit Value: {field.get('explicit_value')}")

            # Now get value for each field and match to actual page fields
            from agent.retriver_service import Retriver

            result_fields = []
            for field_info in fields_info:
                label = field_info.get("label", "")
                field_type = field_info.get("field_type", "personal")
                info_type = field_info.get("info_type", "")
                explicit_value = field_info.get("explicit_value")

                print(f"\n--- Processing field: {label} ---")

                # Match to actual page field if fields provided
                matched_page_field = None
                if fields:
                    label_lower = label.lower()
                    for page_field in fields:
                        page_label = (page_field.get('label') or '').lower()
                        page_name = (page_field.get('name') or '').lower()
                        page_id = (page_field.get('id') or '').lower()

                        if (page_label == label_lower or 
                            label_lower in page_label or 
                            page_label in label_lower or
                            label_lower in page_name or
                            label_lower in page_id):
                            matched_page_field = page_field
                            print(f"Matched to page field: {page_field.get('label')} (id: {page_field.get('id')})")
                            break

                # Priority 1: Use explicit value if provided
                if explicit_value and field_type == "explicit":
                    value = explicit_value
                    print(f"Using Explicit Value: {value}")
                elif field_type == "personal":
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

                # Build result with matched page field info if available
                result_field = {
                    "label": label,
                    "value": value
                }

                if matched_page_field:
                    result_field["id"] = matched_page_field.get("id")
                    result_field["tag"] = matched_page_field.get("tag")
                    result_field["type"] = matched_page_field.get("type")
                    result_field["options"] = matched_page_field.get("options")

                result_fields.append(result_field)

            print(f"\n{'='*60}")
            print(f"FIELD EXTRACTION COMPLETE")
            print(f"{'='*60}")
            print(f"Total fields: {len(result_fields)}")
            for field in result_fields:
                print(f"  {field['label']}: {field['value']}")
                if 'id' in field:
                    print(f"    → Matched to ID: {field['id']}")
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


async def analyze_live_query(screenshot_b64: str, query: str, fields: list = None) -> Dict[str, Any]:
    """
    Main entry point for live agent
    
    Args:
        screenshot_b64: Base64 encoded screenshot
        query: User's question
        fields: Optional list of extracted form fields from page
    
    Returns:
        Dictionary with analysis result
    """
    agent = LiveAgent()
    result = await agent.analyze_screenshot(screenshot_b64, query, fields)
    return result
