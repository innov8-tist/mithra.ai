from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict, Optional
import os
import json


class FieldValue(BaseModel):
    index: int = Field(description="The field index from input")
    label: str = Field(description="The field label from input")
    value: Optional[str] = Field(description="Extracted value from context, or null if not found")


class ExtractionOutput(BaseModel):
    fields: List[FieldValue]


def read_public2_content(profile_id: str | None = None) -> str:
    """Read all text file content from public directory."""
    server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Read from public directory
    public_dir = os.path.join(server_dir, "public")
    
    if not os.path.exists(public_dir):
        return "No context available - public directory not found."
    
    all_content = []
    # Recursively find all .txt files in public directory
    txt_files = list(Path(public_dir).rglob("*.txt"))
    
    if not txt_files:
        return "No text files found in public directory."
    
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            all_content.append(content)
        except Exception as e:
            print(f"Error reading {txt_file.name}: {e}")
    
    return "\n".join(all_content)


SYSTEM_PROMPT = """You are a form-filling extraction agent.

TASK:
- You receive a JSON array of form fields with index and label
- You receive user's personal data as context
- For EACH field, extract the matching value from context

RULES:
- Return the SAME index and label for each field
- Extract value from context if found, otherwise null
- For gender fields (Male/Female/Other), return the matching gender string if user matches
- For dates, keep original format from context
- Do NOT invent values - only extract what exists in context
- Phone/mobile numbers should be digits only"""


load_dotenv()


def get_structured_llm():
    """Initialize and return structured LLM."""
    groq_api_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(
        api_key=groq_api_key,
        model_name="llama-3.3-70b-versatile",
        temperature=0,
    )
    return llm.with_structured_output(ExtractionOutput)


async def extract_form_data(fields: List[Dict], profile_id: str | None = None) -> Dict[str, any]:
    """
    Extract form data using structured LLM output.
    
    Args:
        fields: List of form field dictionaries from Gemini vision response
        profile_id: Not used anymore, kept for backward compatibility
    
    Returns:
        Dictionary with extracted field values
    """
    # Build simple field list for LLM
    field_list = []
    for field in fields:
        label = field.get('label')
        if label:
            field_list.append({
                "index": field.get('index'),
                "label": label.replace(' *', '').strip()
            })
    
    if not field_list:
        return {"fields": [], "extracted": {}}
    
    # Read context from public directory
    context = read_public2_content()
    
    user_prompt = f"""Form fields to fill:
{json.dumps(field_list, indent=2)}

User's personal data:
{context}"""

    print(f"Sending {len(field_list)} fields to LLM...")
    
    # Get structured output from LLM
    structured_llm = get_structured_llm()
    
    try:
        result: ExtractionOutput = structured_llm.invoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ])
        
        print(f"LLM returned {len(result.fields)} fields")
        
        # Map results back to original fields
        extracted = {}
        field_results = []
        
        # Create lookup by index
        result_map = {f.index: f for f in result.fields}
        
        for field in fields:
            idx = field.get('index')
            label = (field.get('label') or '').replace(' *', '').strip()
            
            llm_field = result_map.get(idx)
            value = llm_field.value if llm_field else None
            
            field_results.append({
                "field": field,
                "value": value
            })
            
            if label and value:
                extracted[label] = value
        
        print(f"Extracted: {json.dumps(extracted, indent=2)}")
        
        return {
            "fields": field_results,
            "extracted": extracted
        }
        
    except Exception as e:
        print(f"LLM extraction error: {e}")
        raise

