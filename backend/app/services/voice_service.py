"""Voice processing service."""
import io
from openai import OpenAI
from app.config import settings
from app.services.ai_agent import AIAgent
from app.services.automation import AutomationService

client = OpenAI(api_key=settings.openai_api_key)


class VoiceService:
    """Service for handling voice transcription and command processing."""
    
    def __init__(self):
        self.ai_agent = AIAgent()
        self.automation_service = AutomationService()
    
    async def transcribe_audio(self, audio_data: bytes, filename: str) -> str:
        """
        Transcribe audio to text using OpenAI Whisper.
        
        Args:
            audio_data: Raw audio file bytes
            filename: Original filename (for format detection)
        
        Returns:
            Transcribed text
        """
        # Create a file-like object from bytes
        audio_file = io.BytesIO(audio_data)
        audio_file.name = filename
        
        # Transcribe using OpenAI Whisper
        transcript = client.audio.transcriptions.create(
            model=settings.voice_model,
            file=audio_file,
            language="en"
        )
        
        return transcript.text
    
    async def process_command(self, audio_data: bytes, filename: str) -> dict:
        """
        Process a voice command: transcribe and execute.
        
        Args:
            audio_data: Raw audio file bytes
            filename: Original filename
        
        Returns:
            Result dictionary with transcription and execution status
        """
        # Step 1: Transcribe audio
        transcription = await self.transcribe_audio(audio_data, filename)
        
        # Step 2: Process text command
        result = await self.process_text_command(transcription)
        result["transcription"] = transcription
        
        return result
    
    async def process_text_command(self, command: str) -> dict:
        """
        Process a text command using AI agent.
        
        Args:
            command: Text command from user
        
        Returns:
            Result dictionary with intent and execution status
        """
        # Use AI agent to understand intent
        intent = await self.ai_agent.understand_intent(command)
        
        # Execute the command based on intent
        execution_result = await self._execute_intent(intent, command)
        
        return {
            "command": command,
            "intent": intent,
            "result": execution_result
        }
    
    async def _execute_intent(self, intent: dict, original_command: str) -> dict:
        """
        Execute an intent returned by the AI agent.
        
        Args:
            intent: Intent dictionary with type and parameters
            original_command: Original user command
        
        Returns:
            Execution result
        """
        intent_type = intent.get("type")
        
        if intent_type == "add_items":
            items = intent.get("items", [])
            result = await self.automation_service.add_items_to_cart(items)
            return {"action": "add_items", "items": items, "status": result}
        
        elif intent_type == "reorder":
            order_id = intent.get("order_id")
            if order_id:
                from app.services.order_history import OrderHistoryService
                order_service = OrderHistoryService()
                result = await order_service.reorder(order_id)
                return {"action": "reorder", "order_id": order_id, "status": result}
            else:
                # Reorder from most recent order
                from app.services.order_history import OrderHistoryService
                order_service = OrderHistoryService()
                orders = await order_service.get_order_history(limit=1)
                if orders:
                    result = await order_service.reorder(orders[0]["id"])
                    return {"action": "reorder", "order_id": orders[0]["id"], "status": result}
                else:
                    return {"action": "reorder", "status": "no_orders_found"}
        
        elif intent_type == "list_items":
            # List items in cart or previous orders
            return {"action": "list_items", "message": "Feature coming soon"}
        
        else:
            return {"action": "unknown", "message": f"Unknown intent: {intent_type}"}



