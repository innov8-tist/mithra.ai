"""
Voice Agent - Audio recording and speech-to-text using Sarvam AI
"""

import os
import base64
from typing import Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_API_URL = "https://api.sarvam.ai/speech-to-text"


async def transcribe_audio(audio_base64: str, language: str = "en-IN") -> Dict[str, Any]:
    """
    Transcribe audio using Sarvam AI
    
    Args:
        audio_base64: Base64 encoded audio data
        language: Language code (en-IN, hi-IN, etc.)
    
    Returns:
        Dictionary with transcription result
    """
    try:
        if not SARVAM_API_KEY:
            return {
                "success": False,
                "error": "SARVAM_API_KEY not set in .env file"
            }
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {SARVAM_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "audio": audio_base64,
            "language_code": language,
            "model": "saarika:v1"  # Sarvam's speech recognition model
        }
        
        # Call Sarvam AI API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                SARVAM_API_URL,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                transcript = data.get("transcript", "")
                
                return {
                    "success": True,
                    "transcript": transcript,
                    "language": language
                }
            else:
                return {
                    "success": False,
                    "error": f"Sarvam AI API error: {response.status_code} - {response.text}"
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
