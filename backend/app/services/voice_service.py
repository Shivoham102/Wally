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
        
        print("=" * 60)
        print("🎤 VOICE TRANSCRIPTION:")
        print(f"Audio file: {filename}")
        print(f"Transcription: {transcription}")
        print("=" * 60)
        
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
        
        # Log the LLM response for debugging
        print("=" * 60)
        print("🤖 LLM INTENT RECOGNITION RESPONSE:")
        print(f"Command: {command}")
        print(f"Intent: {intent}")
        print("=" * 60)
        
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
            items_data = intent.get("items", [])
            
            # Convert items to format expected by automation service
            # LLM returns: [{"item": "milk", "quantity": 3}, {"item": "eggs", "quantity": 2}]
            # Automation expects: ["3 milk", "2 eggs"] or will parse quantities itself
            items_for_automation = []
            
            for item_obj in items_data:
                # Handle both object format (from LLM) and string format (fallback)
                if isinstance(item_obj, dict):
                    item_name = item_obj.get("item", "")
                    quantity = item_obj.get("quantity", 1)
                    items_for_automation.append(f"{quantity} {item_name}")
                elif isinstance(item_obj, str):
                    # Fallback: already a string like "3 milk" or just "milk"
                    items_for_automation.append(item_obj)
            
            result = await self.automation_service.add_items_to_cart(items_for_automation)
            return {"action": "add_items", "items": items_data, "status": result}
        
        elif intent_type == "reorder":
            # Reorder from last order in Walmart app
            result = await self.automation_service.reorder_last_order()
            return {"action": "reorder", "status": result}
        
        elif intent_type == "reorder_with_items":
            # Reorder from last order, then add extra items
            items_data = intent.get("items", [])
            
            # First, reorder last order
            reorder_result = await self.automation_service.reorder_last_order()
            
            # Then add extra items
            if items_data and reorder_result.get("success"):
                items_for_automation = []
                for item_obj in items_data:
                    if isinstance(item_obj, dict):
                        item_name = item_obj.get("item", "")
                        quantity = item_obj.get("quantity", 1)
                        items_for_automation.append(f"{quantity} {item_name}")
                    elif isinstance(item_obj, str):
                        items_for_automation.append(item_obj)
                
                add_result = await self.automation_service.add_items_to_cart(items_for_automation)
                return {
                    "action": "reorder_with_items",
                    "reorder_status": reorder_result,
                    "extra_items": items_data,
                    "add_items_status": add_result
                }
            
            return {
                "action": "reorder_with_items",
                "reorder_status": reorder_result,
                "extra_items": items_data
            }
        
        elif intent_type == "list_items":
            # List items in cart or previous orders
            return {"action": "list_items", "message": "Feature coming soon"}
        
        else:
            return {"action": "unknown", "message": f"Unknown intent: {intent_type}"}



