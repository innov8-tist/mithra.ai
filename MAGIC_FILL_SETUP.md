# Magic Fill Setup Guide

Magic Fill uses AI to automatically fill web forms by analyzing screenshots and matching fields with your uploaded documents.

## How It Works

1. **Capture Screenshot** - Takes a screenshot of the current webpage via Chrome CDP
2. **Extract Form Fields** - Identifies all input fields, their positions, and types
3. **Gemini Vision Analysis** - Uses Gemini Vision API to read field labels from the screenshot
4. **RAG Lookup** - Queries your uploaded documents to find matching personal information
5. **Smart Matching** - Uses LLM to intelligently match your data to form fields
6. **Auto-Fill** - Fills the form automatically via Chrome CDP

## Setup Instructions

### 1. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the API key

### 2. Configure Backend

1. Navigate to `mithra.ai/backend/`
2. Create `.env` file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### 3. Install Dependencies

The required dependencies are already in `pyproject.toml`:
- `google-generativeai` - Gemini API
- `langchain-google-genai` - LangChain integration
- `faiss-cpu` - Vector database for RAG

### 4. Upload Your Documents

1. Start the backend server:
   ```bash
   cd mithra.ai/backend
   uv run uvicorn main:app --reload --port 8000
   ```

2. Upload your personal documents (PDFs, images with text):
   - ID cards (Aadhaar, PAN, Driver's License)
   - Resumes
   - Address proofs
   - Any documents containing your personal information

3. The system will automatically:
   - Extract text from documents
   - Create vector embeddings
   - Store in FAISS database for quick retrieval

### 5. Use Magic Fill

1. Start the desktop app
2. Click "Open Browser" to launch Chrome with CDP
3. Navigate to any form (government forms, job applications, etc.)
4. Click "Magic Fill"
5. Watch as the AI:
   - Analyzes the form
   - Finds your information
   - Fills everything automatically

## Supported Field Types

- Text inputs (name, email, address, etc.)
- Select dropdowns (automatically matches options)
- Radio buttons (gender, yes/no, etc.)
- Date fields (auto-converts formats)
- Number fields (phone, Aadhaar, PIN code)

## Smart Features

- **Format Detection**: Automatically formats phone numbers, Aadhaar (removes spaces), dates
- **Fuzzy Matching**: Matches field labels even if they're in different languages or formats
- **Context Aware**: Uses surrounding text and field positions to understand what data is needed
- **Skip Sensitive**: Automatically skips password, OTP, CAPTCHA fields

## Troubleshooting

### "GEMINI_API_KEY not set"
- Make sure you created `.env` file in `backend/` folder
- Check that the API key is correct
- Restart the backend server after adding the key

### "No matching data found"
- Upload more documents with your personal information
- Make sure documents are readable (clear scans, not handwritten)
- Check that the backend processed the documents successfully

### Fields not filling
- Some websites use dynamic IDs that change on reload
- Try refreshing the page and running Magic Fill again
- Check browser console for errors

## Privacy & Security

- All processing happens locally on your machine
- Documents are stored in `backend/user_details/`
- Only field labels are sent to Gemini Vision API (not your personal data)
- Your personal data never leaves your computer except for the final form filling

## Example Use Cases

- Government forms (passport, voter ID, etc.)
- Job applications
- University admissions
- Bank account opening
- Insurance forms
- Any repetitive form filling task
