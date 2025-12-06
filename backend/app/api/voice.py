"""Voice processing API endpoints."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
from pydantic import BaseModel
from app.services.voice_service import VoiceService

router = APIRouter()
voice_service = VoiceService()


class TextCommandRequest(BaseModel):
    """Request model for text command."""
    command: str


@router.post("/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """
    Transcribe audio file to text using OpenAI Whisper.
    
    Accepts audio files in various formats (mp3, wav, m4a, etc.)
    """
    try:
        # Read audio file
        audio_data = await audio_file.read()
        
        # Transcribe
        transcription = await voice_service.transcribe_audio(audio_data, audio_file.filename)
        
        return {
            "text": transcription,
            "language": "en"  # Could be detected from transcription
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/process-command")
async def process_voice_command(audio_file: UploadFile = File(...)):
    """
    Process a voice command: transcribe and execute.
    
    This endpoint:
    1. Transcribes the audio
    2. Sends to AI agent for intent recognition
    3. Executes the command (e.g., add items to cart)
    """
    try:
        audio_data = await audio_file.read()
        
        # Process the command
        result = await voice_service.process_command(audio_data, audio_file.filename)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Command processing failed: {str(e)}")


@router.post("/text-command")
async def process_text_command(request: TextCommandRequest):
    """
    Process a text command directly (useful for testing).
    
    Example: {"command": "Add milk, eggs, and bread"}
    """
    try:
        result = await voice_service.process_text_command(request.command)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Command processing failed: {str(e)}")


class TestCommandRequest(BaseModel):
    """Request model for test command (direct items, no AI)."""
    items: list[str]


@router.post("/test-command")
async def test_command(request: TestCommandRequest):
    """
    Test endpoint that bypasses OpenAI API calls (no credits used).
    Directly accepts items list and executes automation.
    
    Example: {"items": ["great value whole milk", "18 count eggs"]}
    """
    try:
        # Execute automation directly (no AI calls)
        from app.services.automation import AutomationService
        automation_service = AutomationService()
        
        result = await automation_service.add_items_to_cart(request.items)
        
        return {
            "items": request.items,
            "status": result,
            "note": "Test endpoint - no OpenAI credits used"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test command failed: {str(e)}")

