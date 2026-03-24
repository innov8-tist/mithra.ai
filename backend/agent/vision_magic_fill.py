import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


async def analyze_with_gemini_vision(screenshot_b64: str, fields: list[dict]) -> list[dict]:
    """
    Use Gemini Vision to identify form field labels from screenshot,
    then map them to DOM fields using coordinates.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")

    # Build field position info for the prompt
    field_positions = []
    for f in fields:
        field_positions.append(f"- Field #{f['index']}: {f['tag']} ({f['type']}) at position ({f['x']}, {f['y']})")
    
    positions_text = "\n".join(field_positions)

    prompt = f"""Analyze this government form screenshot and identify the label for each form field.

I have detected these form fields at these pixel coordinates:
{positions_text}

For EACH field listed above, find the corresponding label text visible in the screenshot.
Labels are usually:
- To the LEFT of the input field
- ABOVE the input field  
- Inside a table cell to the left
- Part of a <td> or table header

Return a JSON array with the label for each field index:
[
  {{"index": 0, "label": "Name of Applicant"}},
  {{"index": 1, "label": "Father's Name"}},
  {{"index": 2, "label": "District"}},
  ...
]

Rules:
- Match EVERY field index from the list above
- Copy label text EXACTLY as shown (including Hindi/regional text)
- If a field has no visible label, use null
- Order by index number"""

    response = model.generate_content([
        prompt,
        {"mime_type": "image/png", "data": screenshot_b64}
    ])

    gemini_text = response.text
    print(f"Gemini response:\n{gemini_text}")

    # Parse JSON from response
    try:
        start = gemini_text.find("[")
        end = gemini_text.rfind("]") + 1
        if start != -1 and end > start:
            json_str = gemini_text[start:end]
            labels = json.loads(json_str)
            return labels
    except json.JSONDecodeError:
        print("Failed to parse Gemini JSON")
    
    return []


async def extract_form_data_with_rag(fields: list[dict], retriver_func) -> dict:
    """Extract form data using RAG and LLM."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    from pydantic import BaseModel, Field
    
    # Define output schema
    class FormData(BaseModel):
        name: str | None = Field(None, description="Full name")
        email: str | None = Field(None, description="Email address")
        phone: str | None = Field(None, description="Phone number")
        address: str | None = Field(None, description="Full address")
        city: str | None = Field(None, description="City")
        state: str | None = Field(None, description="State")
        pincode: str | None = Field(None, description="Pincode/ZIP")
        dob: str | None = Field(None, description="Date of birth (DD/MM/YYYY)")
        gender: str | None = Field(None, description="Gender")
        aadhaar: str | None = Field(None, description="Aadhaar number")
        pan: str | None = Field(None, description="PAN number")
    
    # Build field descriptions
    field_descriptions = []
    for field in fields:
        label = field.get('label', '')
        field_type = field.get('type', 'text')
        placeholder = field.get('placeholder', '')
        field_id = field.get('id', '')
        
        desc = f"Field: {label or field_id or 'Unknown'}"
        if placeholder:
            desc += f" (placeholder: {placeholder})"
        desc += f" [type: {field_type}]"
        field_descriptions.append(desc)
    
    fields_text = "\n".join(field_descriptions)
    
    # Query RAG for user data
    rag_context = await retriver_func("user personal information name email phone address")
    
    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a form-filling assistant. Extract user data from the provided context and match it to form fields.

Context from user documents:
{context}

Form fields to fill:
{fields}

Extract and return the data in JSON format. Only include fields you can confidently fill from the context."""),
        ("human", "Extract the form data.")
    ])
    
    # Setup LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=GEMINI_API_KEY
    )
    
    parser = JsonOutputParser(pydantic_object=FormData)
    chain = prompt | llm | parser
    
    try:
        result = await chain.ainvoke({
            "context": rag_context,
            "fields": fields_text
        })
        
        # Map extracted data to fields
        field_results = []
        for field in fields:
            label = (field.get('label') or '').lower()
            field_id = (field.get('id') or '').lower()
            
            value = None
            # Simple matching logic
            if 'name' in label or 'name' in field_id:
                value = result.get('name')
            elif 'email' in label or 'email' in field_id:
                value = result.get('email')
            elif 'phone' in label or 'mobile' in label or 'phone' in field_id:
                value = result.get('phone')
            elif 'address' in label or 'address' in field_id:
                value = result.get('address')
            elif 'city' in label or 'city' in field_id:
                value = result.get('city')
            elif 'state' in label or 'state' in field_id:
                value = result.get('state')
            elif 'pin' in label or 'zip' in label or 'pin' in field_id:
                value = result.get('pincode')
            elif 'dob' in label or 'birth' in label or 'dob' in field_id:
                value = result.get('dob')
            elif 'gender' in label or 'sex' in label or 'gender' in field_id:
                value = result.get('gender')
            elif 'aadhaar' in label or 'aadhar' in label or 'uid' in field_id:
                value = result.get('aadhaar')
            elif 'pan' in label or 'pan' in field_id:
                value = result.get('pan')
            
            field_results.append({
                'field': field,
                'value': value
            })
        
        return {
            'extracted': result,
            'fields': field_results
        }
    except Exception as e:
        print(f"LLM extraction error: {e}")
        return {'extracted': {}, 'fields': []}
