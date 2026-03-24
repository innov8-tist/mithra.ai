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
