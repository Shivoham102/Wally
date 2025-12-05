"""Order history and management API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.services.order_history import OrderHistoryService
from pydantic import BaseModel

router = APIRouter()
order_service = OrderHistoryService()


class OrderItem(BaseModel):
    """Order item model."""
    name: str
    quantity: int = 1
    price: Optional[float] = None


class Order(BaseModel):
    """Order model."""
    id: Optional[int] = None
    items: List[OrderItem]
    total: Optional[float] = None
    date: Optional[str] = None


@router.get("/history")
async def get_order_history(limit: int = 10):
    """Get order history."""
    try:
        orders = await order_service.get_order_history(limit)
        return {"orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch order history: {str(e)}")


@router.get("/history/{order_id}")
async def get_order(order_id: int):
    """Get a specific order by ID."""
    try:
        order = await order_service.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch order: {str(e)}")


@router.post("/history")
async def save_order(order: Order):
    """Save an order to history."""
    try:
        saved_order = await order_service.save_order(order)
        return saved_order
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save order: {str(e)}")


@router.post("/reorder/{order_id}")
async def reorder(order_id: int):
    """Reorder items from a previous order."""
    try:
        result = await order_service.reorder(order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reorder: {str(e)}")



