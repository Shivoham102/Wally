"""Mobile automation API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
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


@router.post("/reorder-last-order")
async def reorder_last_order():
    """
    Reorder items from the last order for the configured customer.
    
    This endpoint finds the last order for the customer (based on CUSTOMER_NAME env var)
    and reorders all items from that order. It searches through purchase history
    to find the matching order.
    
    Example request:
    POST /api/v1/automation/reorder-last-order
    """
    try:
        result = await automation_service.reorder_last_order()
        return {
            "intent": "reorder",
            "result": result,
            "note": "Direct endpoint - finds last order for configured customer and reorders all items"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reorder last order: {str(e)}")


class ReorderWithItemsRequest(BaseModel):
    """Request model for reorder with additional items (test endpoint, no AI)."""
    items: List[AddItemRequest]  # Format: [{"item": "coffee", "quantity": 1}]


@router.post("/reorder-with-items")
async def reorder_with_items(request: ReorderWithItemsRequest):
    """
    Test endpoint: Reorder last order and add additional items (bypasses AI, no credits used).
    
    This endpoint sequences:
    1. Reorders the last order
    2. Adds additional items
    
    Example request:
    {
        "items": [
            {"item": "coffee", "quantity": 1}
        ]
    }
    """
    try:
        # Step 1: Reorder last order
        reorder_result = await automation_service.reorder_last_order()
        
        # Step 2: Add additional items if reorder succeeded
        add_items_result = None
        if reorder_result.get("success") and request.items:
            # Convert to structured format
            items_structured = [{"item": item.item, "quantity": item.quantity} for item in request.items]
            add_items_result = await automation_service.add_items_to_cart_structured(items_structured)
        
        return {
            "reorder_status": reorder_result,
            "add_items_status": add_items_result,
            "items": [{"item": item.item, "quantity": item.quantity} for item in request.items],
            "note": "Test endpoint - no OpenAI credits used, uses existing automation methods"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reorder with items: {str(e)}")


class PlaceOrderRequest(BaseModel):
    """Request model for placing an order with optional date and time preferences."""
    date_preference: Optional[str] = None  # e.g., "today", "tomorrow", "Tuesday", "12/9"
    time_preference: Optional[str] = None  # e.g., "6am-8am", "7am-9am", "morning", "afternoon"


@router.post("/place-order")
async def place_order(request: Optional[PlaceOrderRequest] = None):
    """
    Place an order in Walmart app.
    
    This endpoint:
    1. Clicks cart button
    2. Clicks on third card inside delivery_options LinearLayout
    3. Clicks cart_view_address_and_delivery_time_button
    4. Sets correct address by:
       - Clicking cart_view_change_address_button
       - Finding address matching customer name in address_recycler_view
       - Clicking the matching address radio button
    5. Selects delivery date (if date_preference provided)
    6. Selects delivery time slot (if time_preference provided)
    7. Confirms reservation
    
    Example request:
    POST /api/v1/automation/place-order
    {
        "date_preference": "tomorrow",
        "time_preference": "morning"
    }
    """
    try:
        date_pref = request.date_preference if request else None
        time_pref = request.time_preference if request else None
        
        result = await automation_service.place_order(
            date_preference=date_pref,
            time_preference=time_pref
        )
        return {
            "intent": "place_order",
            "result": result,
            "date_preference": date_pref,
            "time_preference": time_pref,
            "note": "Places order with address matching configured customer name"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to place order: {str(e)}")



