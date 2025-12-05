"""AI agent service for intent recognition and natural language understanding."""
from openai import OpenAI
from app.config import settings
import json

client = OpenAI(api_key=settings.openai_api_key)


class AIAgent:
    """AI agent for understanding user intents and commands."""
    
    SYSTEM_PROMPT = """You are a helpful voice assistant for ordering groceries from Walmart. 
Your job is to understand user commands and extract structured information.

User commands can be:
1. Adding items: "Add milk, eggs, and bread" or "I need milk and eggs"
2. Reordering: "Add my usual groceries" or "Reorder from last week"
3. Listing: "What's in my cart?" or "Show my previous orders"

Respond with a JSON object containing:
- type: One of "add_items", "reorder", "list_items", "unknown"
- items: List of item names (for add_items)
- order_id: Order ID if specified (for reorder)
- confidence: Confidence score 0-1

Example responses:
{"type": "add_items", "items": ["milk", "eggs", "bread"], "confidence": 0.95}
{"type": "reorder", "order_id": null, "confidence": 0.9}
{"type": "list_items", "confidence": 0.85}
"""
    
    def __init__(self):
        self.model = settings.ai_model
    
    async def understand_intent(self, command: str) -> dict:
        """
        Understand user intent from a text command.
        
        Args:
            command: User's text command
        
        Returns:
            Dictionary with intent type and parameters
        """
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": command}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            # Parse JSON response
            content = response.choices[0].message.content
            intent = json.loads(content)
            
            return intent
        
        except Exception as e:
            # Fallback to simple parsing if AI fails
            return self._fallback_intent_parsing(command)
    
    def _fallback_intent_parsing(self, command: str) -> dict:
        """
        Fallback intent parsing using simple keyword matching.
        
        Args:
            command: User's text command
        
        Returns:
            Dictionary with intent type and parameters
        """
        command_lower = command.lower()
        
        # Check for reorder keywords
        if any(keyword in command_lower for keyword in ["reorder", "usual", "last order", "previous order"]):
            return {
                "type": "reorder",
                "order_id": None,
                "confidence": 0.7
            }
        
        # Check for list keywords
        if any(keyword in command_lower for keyword in ["list", "show", "what", "cart"]):
            return {
                "type": "list_items",
                "confidence": 0.7
            }
        
        # Default to add_items and try to extract items
        # Simple extraction: look for common patterns
        items = []
        if "add" in command_lower or "need" in command_lower or "want" in command_lower:
            # Try to extract items after keywords
            parts = command_lower.split()
            for i, part in enumerate(parts):
                if part in ["add", "need", "want", "get"]:
                    # Take next few words as potential items
                    remaining = " ".join(parts[i+1:])
                    # Split by commas and "and"
                    items = [item.strip() for item in remaining.replace("and", ",").split(",")]
                    items = [item for item in items if item]
                    break
        
        return {
            "type": "add_items",
            "items": items if items else [command],  # Fallback to entire command
            "confidence": 0.6
        }
    
    async def extract_items(self, command: str) -> list[str]:
        """
        Extract item names from a command.
        
        Args:
            command: User's text command
        
        Returns:
            List of item names
        """
        intent = await self.understand_intent(command)
        
        if intent.get("type") == "add_items":
            return intent.get("items", [])
        
        return []



