"""Mobile automation API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.services.automation import AutomationService

router = APIRouter()
automation_service = AutomationService()


class AddItemRequest(BaseModel):
    """Request model for adding a single item with quantity (matches LLM format)."""
    item: str  # Matches LLM output format
    quantity: int = 1


class AddItemsRequest(BaseModel):
    """Request model for adding multiple items directly (no AI, no regex parsing)."""
    intent: str = "add_items"  # Explicit intent type
    items: List[AddItemRequest]


@router.post("/connect")
async def connect_device():
    """Connect to Android device."""
    try:
        result = await automation_service.connect_device()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect device: {str(e)}")


@router.get("/status")
async def get_automation_status():
    """Get automation service status."""
    try:
        status = await automation_service.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/open-walmart")
async def open_walmart_app():
    """Open Walmart app on connected device."""
    try:
        result = await automation_service.open_walmart_app()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open Walmart app: {str(e)}")


@router.post("/add-to-cart")
async def add_items_to_cart(items: list[str]):
    """
    Add items to cart in Walmart app.
    
    Args:
        items: List of item names to search and add
    """
    try:
        result = await automation_service.add_items_to_cart(items)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add items: {str(e)}")


@router.post("/search-item")
async def search_item(item_name: str):
    """Search for an item in Walmart app."""
    try:
        result = await automation_service.search_item(item_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search item: {str(e)}")


@router.post("/add-items-direct")
async def add_items_direct(request: AddItemsRequest):
    """
    Add items to cart directly without using AI or regex parsing.
    
    This endpoint bypasses AI processing and regex parsing. It accepts items
    in the exact format that the LLM would output and passes them directly
    to the automation service.
    
    Example request (matches LLM output format):
    {
        "intent": "add_items",
        "items": [
            {"item": "milk", "quantity": 2},
            {"item": "eggs", "quantity": 1}
        ]
    }
    """
    try:
        # Convert Pydantic models to dicts in LLM format
        items_structured = [{"item": item.item, "quantity": item.quantity} for item in request.items]
        
        # Execute automation directly (no AI calls, no regex parsing)
        result = await automation_service.add_items_to_cart_structured(items_structured)
        
        return {
            "intent": request.intent,
            "items": items_structured,
            "result": result,
            "note": "Direct endpoint - no AI processing or regex parsing used"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add items: {str(e)}")



