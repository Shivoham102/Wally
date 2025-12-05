"""Mobile automation API endpoints."""
from fastapi import APIRouter, HTTPException
from app.services.automation import AutomationService

router = APIRouter()
automation_service = AutomationService()


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



