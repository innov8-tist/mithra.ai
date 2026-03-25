# Voice + Live Query Integration

## Overview
Integrated voice transcription with live query endpoint to enable voice-controlled form filling and page analysis.

## Flow

### 1. User Interaction
- User clicks the audio button overlay on the webpage
- Voice recording starts (indicated by purple status)

### 2. Audio Processing
- When recording stops, audio is captured as base64
- Sent to `/voice-transcribe` endpoint
- Sarvam AI transcribes audio (auto-detects Malayalam/English)
- Translates to English if needed

### 3. Screenshot Capture
- After successful transcription, screenshot is captured via CDP
- Screenshot shows current page state

### 4. Live Query Analysis
- Both transcribed text and screenshot sent to `/live-query` endpoint
- Gemini Vision analyzes the screenshot with the user's query
- Returns:
  - `text`: AI response explaining what it sees
  - `decision`: "fill" or "normal"
  - `fields`: Array of field data (if decision is "fill")

### 5. Auto-Fill (if applicable)
- If decision is "fill" and fields are provided:
  - Converts fields to fill_data format
  - Calls `fill_form_fields` Tauri command
  - Fills the form automatically

### 6. Visual Feedback
- Status updates shown in real-time:
  - 🎤 Recording...
  - 🔄 Transcribing audio...
  - 📝 Transcribed text
  - 📸 Analyzing page...
  - 🔄 Filling X fields...
  - ✅ Success or ℹ️ Information response

## API Endpoints

### POST /voice-transcribe
```json
{
  "audio_base64": "base64_encoded_audio",
  "language_code": "auto"
}
```

Response:
```json
{
  "success": true,
  "transcribed_text": "original text",
  "translated_text": "english translation",
  "language": "ml-IN"
}
```

### POST /live-query
```json
{
  "screenshot_b64": "base64_encoded_screenshot",
  "query": "user query text"
}
```

Response:
```json
{
  "success": true,
  "text": "AI response",
  "decision": "fill",
  "fields": [
    {"label": "Email", "value": "user@example.com"},
    {"label": "Phone", "value": "1234567890"}
  ]
}
```

## Files Modified

### Frontend
- `desktop/src/components/ChromeSandbox.tsx`
  - Added live query integration after transcription
  - Added visual status feedback
  - Auto-fill form if decision is "fill"

### Backend
- `backend/main.py`
  - Updated `/live-query` to accept JSON instead of form-data
  - Simplified request handling

## Usage Example

1. Open Chrome Sandbox
2. Navigate to a form page
3. Click the voice button overlay
4. Say: "Fill my email address"
5. System will:
   - Transcribe your voice
   - Analyze the page
   - Find the email field
   - Fill it with your email from documents

## Supported Queries

### Fill Queries (decision: "fill")
- "Fill my email"
- "Enter my phone number"
- "Complete the name field"
- "Autofill my address"

### Information Queries (decision: "normal")
- "What is this page about?"
- "Explain this form"
- "What information is required?"
- "Tell me about this field"
