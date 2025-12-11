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
1. Adding items: "Add milk, eggs, and bread" or "I need 3 milks and 2 eggs"
2. Reordering: "Add my usual groceries" or "Reorder from last week"
3. Reordering with extra items: "Reorder my last order and add milk" or "Add my usual groceries plus eggs"
4. Placing order: "Place my order" or "Checkout" or "Place order for tomorrow at 6am" or "Order for Tuesday morning"
5. Listing: "What's in my cart?" or "Show my previous orders"

For quantities, users may say:
- "3 milks" or "three milks" → 3x milk
- "a dozen eggs" → 12x eggs
- "2 gallons of milk" → 2x milk
- Just "milk" → 1x milk (default)

Respond with a JSON object containing:
- type: One of "add_items", "reorder", "reorder_with_items", "place_order", "list_items", "unknown"
- items: List of objects with "item" and "quantity" fields (for add_items or extra items in reorder_with_items)
  - Always include quantity, even if user doesn't specify (default to 1)
  - Format: [{"item": "milk", "quantity": 3}, {"item": "eggs", "quantity": 2}]
- order_id: Order ID if specified (for reorder)
- date_preference: Date preference for place_order (e.g., "today", "tomorrow", "Tuesday", "12/9", "Tue 12/9", null if not specified)
- time_preference: Time preference for place_order (e.g., "6am-8am", "7am-9am", "morning", "afternoon", "evening", null if not specified)
- confidence: Confidence score 0-1

For date preferences, users may say:
- "today" → "today"
- "tomorrow" → "tomorrow"
- "Tuesday" or "Tue" → "Tuesday" or "Tue"
- "12/9" or "December 9" → "12/9"
- Relative dates like "next week" → extract the actual date if possible

For time preferences, users may say:
- "6am-8am" or "6am to 8am" → "6am-8am"
- "morning" → "morning" (first available morning slot)
- "afternoon" → "afternoon" (first available afternoon slot)
- "evening" → "evening" (first available evening slot)
- Specific times like "7am", "8am", "2pm" → pass through as-is (e.g., "8am", "2pm"). The system will find which time slot contains this time.

Example responses:
{"type": "add_items", "items": [{"item": "milk", "quantity": 1}, {"item": "eggs", "quantity": 1}], "confidence": 0.95}
{"type": "add_items", "items": [{"item": "milk", "quantity": 3}, {"item": "eggs", "quantity": 2}], "confidence": 0.95}
{"type": "reorder", "order_id": null, "confidence": 0.9}
{"type": "reorder_with_items", "items": [{"item": "milk", "quantity": 1}], "confidence": 0.9}
{"type": "place_order", "date_preference": null, "time_preference": null, "confidence": 0.9}
{"type": "place_order", "date_preference": "tomorrow", "time_preference": "morning", "confidence": 0.95}
{"type": "place_order", "date_preference": "Tuesday", "time_preference": "6am-8am", "confidence": 0.95}
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
        
        # Check for reorder with extra items keywords
        reorder_keywords = ["reorder", "usual", "last order", "previous order"]
        add_keywords = ["add", "plus", "and also", "also add"]
        
        has_reorder = any(keyword in command_lower for keyword in reorder_keywords)
        has_add = any(keyword in command_lower for keyword in add_keywords)
        
        if has_reorder and has_add:
            # Reorder with extra items - try to extract items after "add", "plus", etc.
            items = []
            for add_kw in add_keywords:
                if add_kw in command_lower:
                    parts = command_lower.split(add_kw)
                    if len(parts) > 1:
                        remaining = parts[1].strip()
                        # Split by commas and "and"
                        items = [item.strip() for item in remaining.replace("and", ",").split(",")]
                        items = [item for item in items if item]
                        break
            
            return {
                "type": "reorder_with_items",
                "items": items if items else [],
                "confidence": 0.7
            }
        
        # Check for reorder keywords (without extra items)
        if has_reorder:
            return {
                "type": "reorder",
                "order_id": None,
                "confidence": 0.7
            }
        
        # Check for place order keywords
        place_order_keywords = ["place order", "checkout", "order now", "complete order", "finalize order"]
        if any(keyword in command_lower for keyword in place_order_keywords):
            # Try to extract date and time preferences
            date_pref = None
            time_pref = None
            
            # Check for date mentions
            if "today" in command_lower:
                date_pref = "today"
            elif "tomorrow" in command_lower:
                date_pref = "tomorrow"
            elif any(day in command_lower for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
                # Extract day name
                for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                    if day in command_lower:
                        date_pref = day.capitalize()
                        break
            
            # Check for time mentions
            if "morning" in command_lower:
                time_pref = "morning"
            elif "afternoon" in command_lower:
                time_pref = "afternoon"
            elif "evening" in command_lower:
                time_pref = "evening"
            elif "am" in command_lower or "pm" in command_lower:
                # Try to extract time range first (e.g., "6am-8am", "6am to 8am")
                import re
                time_range_match = re.search(r'(\d+)\s*(am|pm)\s*(?:-|to)\s*(\d+)\s*(am|pm)?', command_lower)
                if time_range_match:
                    time_pref = f"{time_range_match.group(1)}{time_range_match.group(2)}-{time_range_match.group(3)}{time_range_match.group(4) if time_range_match.group(4) else time_range_match.group(2)}"
                else:
                    # Try to extract specific time (e.g., "8am", "2pm")
                    time_specific_match = re.search(r'(\d+)\s*(am|pm)\b', command_lower)
                    if time_specific_match:
                        time_pref = f"{time_specific_match.group(1)}{time_specific_match.group(2)}"
            
            return {
                "type": "place_order",
                "date_preference": date_pref,
                "time_preference": time_pref,
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



