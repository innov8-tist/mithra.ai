# Live Query Response Logging

## Overview
Added comprehensive logging throughout the live query flow to help debug and monitor the voice-to-fill integration.

## Logging Locations

### 1. Frontend (ChromeSandbox.tsx)

#### Browser Console Output:
```
============================================================
SENDING TO LIVE QUERY ENDPOINT
============================================================
Query: fill my email address
Screenshot length: 123456 chars

============================================================
LIVE QUERY RESPONSE RECEIVED
============================================================
Full Response: {
  "success": true,
  "text": "I can see an email field on this form...",
  "decision": "fill",
  "fields": [
    {
      "label": "Email",
      "value": "user@example.com"
    }
  ]
}
============================================================
🤖 Live Agent Response: I can see an email field on this form...
📊 Decision: fill
🔄 Auto-filling form fields...
Fields to fill: [...]
Fill data: [...]
✅ Form filled successfully
```

### 2. Backend API (main.py)

#### Terminal Output:
```
============================================================
LIVE QUERY REQUEST
============================================================
Query: fill my email address
Screenshot length: 123456 chars

============================================================
LIVE QUERY RESPONSE
============================================================
Success: True
Decision: fill
Text: I can see an email field on this form...
Fields (1):
  - Email: user@example.com
============================================================
```

### 3. Live Agent (live_agent.py)

#### Terminal Output:
```
============================================================
LIVE AGENT - ANALYZING SCREENSHOT
============================================================
Query: fill my email address
Image size: 234567 bytes

Calling Gemini Vision API...

Gemini Raw Response:
{
  "text": "I can see an email field on this form...",
  "decision": "fill"
}

Parsed Decision: fill
Parsed Text: I can see an email field on this form...

============================================================
EXTRACTING FORM FIELDS (Decision: fill)
============================================================

============================================================
EXTRACTING FORM FIELDS
============================================================
Query: fill my email address

Calling Gemini Vision for field extraction...

Gemini Field Extraction Response:
[
  {
    "label": "Email",
    "field_type": "personal",
    "info_type": "email"
  }
]

Parsed 1 field(s):
  - Label: Email
    Type: personal
    Info: email

--- Processing field: Email ---
RAG Query: What is my email?
RAG Raw Result: Your email is user@example.com
Cleaned Value: user@example.com

============================================================
FIELD EXTRACTION COMPLETE
============================================================
Total fields: 1
  Email: user@example.com
============================================================
```

## What Gets Logged

### Request Phase:
- User's voice query (transcribed and translated)
- Screenshot size/length
- Request payload structure

### Processing Phase:
- Gemini Vision API calls
- Raw AI responses
- Parsed decisions and text
- Field extraction details
- RAG queries and results
- Value cleaning/formatting

### Response Phase:
- Complete response object (JSON)
- Success/error status
- Decision type (fill/normal)
- Field data with labels and values
- Fill operation results

## How to View Logs

### Frontend Logs:
1. Open browser DevTools (F12)
2. Go to Console tab
3. Trigger voice query
4. See formatted output with separators

### Backend Logs:
1. Run backend with: `cd backend && uv run uvicorn main:app --reload`
2. Terminal will show all processing steps
3. Look for `====` separator lines for easy reading

## Error Logging

If errors occur, you'll see:
```
============================================================
ERROR IN ANALYZE_SCREENSHOT
============================================================
Error: [error message]
[full stack trace]
============================================================
```

## Benefits

1. **Debug Issues**: See exactly where processing fails
2. **Monitor Performance**: Track API call times
3. **Verify Data**: Check RAG retrieval accuracy
4. **Understand Flow**: Follow request through entire pipeline
5. **Test Queries**: Validate different voice commands
