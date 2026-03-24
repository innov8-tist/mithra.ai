import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.structured_data_filling import extract_form_data


async def main():
    # Sample form fields to extract
    fields = [
        {"index": 0, "label": "Full Name"},
        {"index": 1, "label": "Date of Birth"},
        {"index": 2, "label": "Gender"},
        {"index": 3, "label": "Father's Name"},
        {"index": 4, "label": "Aadhaar Number"},
        {"index": 5, "label": "Address"},
        {"index": 6, "label": "District"},
        {"index": 7, "label": "State"},
        {"index": 8, "label": "Pincode"},
        {"index": 9, "label": "Educational Qualification"},
        {"index": 10, "label": "Occupation"},
        {"index": 11, "label": "Bank Account Number"},
        {"index": 12, "label": "IFSC Code"},
    ]
    
    print("Testing structured data filling with data from public folder...")
    print("=" * 60)
    
    # The script will read all .txt files from the public directory
    result = await extract_form_data(fields)
    
    print("\n" + "=" * 60)
    print("EXTRACTION RESULTS:")
    print("=" * 60)
    
    for field_result in result["fields"]:
        field = field_result["field"]
        value = field_result["value"]
        print(f"{field['label']}: {value}")
    
    print("\n" + "=" * 60)
    print("EXTRACTED DICTIONARY:")
    print("=" * 60)
    print(result["extracted"])


if __name__ == "__main__":
    asyncio.run(main())
