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
            
            # Convert items to structured format expected by add_items_to_cart_structured
            # LLM returns: [{"item": "milk", "quantity": 3}, {"item": "eggs", "quantity": 2}]
            items_structured = []
            
            for item_obj in items_data:
                # Handle both object format (from LLM) and string format (fallback)
                if isinstance(item_obj, dict):
                    # Already in correct format: {"item": "milk", "quantity": 3}
                    items_structured.append({
                        "item": item_obj.get("item", ""),
                        "quantity": item_obj.get("quantity", 1)
                    })
                elif isinstance(item_obj, str):
                    # Fallback: parse string like "3 milk" or just "milk"
                    parts = item_obj.strip().split(None, 1)
                    if len(parts) == 2 and parts[0].isdigit():
                        quantity = int(parts[0])
                        item_name = parts[1]
                    else:
                        quantity = 1
                        item_name = item_obj.strip()
                    items_structured.append({"item": item_name, "quantity": quantity})
            
            # Use structured method for better reliability
            result = await self.automation_service.add_items_to_cart_structured(items_structured)
            return {"action": "add_items", "items": items_structured, "status": result}
        
        elif intent_type == "reorder":
            # Reorder from last order in Walmart app
            result = await self.automation_service.reorder_last_order()
            return {"action": "reorder", "status": result}
        
        elif intent_type == "reorder_with_items":
            # Reorder from last order, then add extra items
            items_data = intent.get("items", [])
            
            # First, reorder last order
            reorder_result = await self.automation_service.reorder_last_order()
            
            # Then add extra items using structured format
            if items_data and reorder_result.get("success"):
                # Convert items to structured format expected by add_items_to_cart_structured
                items_structured = []
                for item_obj in items_data:
                    if isinstance(item_obj, dict):
                        # Already in correct format: {"item": "milk", "quantity": 2}
                        items_structured.append({
                            "item": item_obj.get("item", ""),
                            "quantity": item_obj.get("quantity", 1)
                        })
                    elif isinstance(item_obj, str):
                        # Fallback: parse string like "3 milk" or just "milk"
                        parts = item_obj.strip().split(None, 1)
                        if len(parts) == 2 and parts[0].isdigit():
                            quantity = int(parts[0])
                            item_name = parts[1]
                        else:
                            quantity = 1
                            item_name = item_obj.strip()
                        items_structured.append({"item": item_name, "quantity": quantity})
                
                # Use structured method for better reliability
                add_result = await self.automation_service.add_items_to_cart_structured(items_structured)
                return {
                    "action": "reorder_with_items",
                    "reorder_status": reorder_result,
                    "extra_items": items_structured,
                    "add_items_status": add_result
                }
            
            return {
                "action": "reorder_with_items",
                "reorder_status": reorder_result,
                "extra_items": items_data,
                "message": "Reorder completed, but no extra items to add" if not items_data else "Reorder failed, skipping extra items"
            }
        
        elif intent_type == "place_order":
            # Place order with optional date and time preferences
            date_pref = intent.get("date_preference")
            time_pref = intent.get("time_preference")
            
            result = await self.automation_service.place_order(
                date_preference=date_pref,
                time_preference=time_pref
            )
            return {
                "action": "place_order",
                "date_preference": date_pref,
                "time_preference": time_pref,
                "status": result
            }
        
        elif intent_type == "list_items":
            # List items in cart or previous orders
            return {"action": "list_items", "message": "Feature coming soon"}
        
        else:
            return {"action": "unknown", "message": f"Unknown intent: {intent_type}"}



