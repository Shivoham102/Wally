"""Order history management service."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import settings


class Base(DeclarativeBase):
    """Base class for database models."""
    pass


class OrderModel(Base):
    """Database model for orders."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    items = Column(JSON)  # List of items with name, quantity, price
    total = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)


# Database setup
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


class OrderHistoryService:
    """Service for managing order history."""
    
    def __init__(self):
        self.db: Optional[Session] = None
    
    def get_db(self) -> Session:
        """Get database session."""
        if not self.db:
            self.db = SessionLocal()
        return self.db
    
    async def get_order_history(self, limit: int = 10) -> List[dict]:
        """
        Get order history.
        
        Args:
            limit: Maximum number of orders to return
        
        Returns:
            List of order dictionaries
        """
        db = self.get_db()
        try:
            orders = db.query(OrderModel).order_by(OrderModel.date.desc()).limit(limit).all()
            return [
                {
                    "id": order.id,
                    "items": order.items,
                    "total": order.total,
                    "date": order.date.isoformat() if order.date else None
                }
                for order in orders
            ]
        finally:
            pass  # Don't close session here, let it be managed
    
    async def get_order(self, order_id: int) -> Optional[dict]:
        """
        Get a specific order by ID.
        
        Args:
            order_id: Order ID
        
        Returns:
            Order dictionary or None
        """
        db = self.get_db()
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        
        if order:
            return {
                "id": order.id,
                "items": order.items,
                "total": order.total,
                "date": order.date.isoformat() if order.date else None
            }
        return None
    
    async def save_order(self, order_data: dict) -> dict:
        """
        Save an order to history.
        
        Args:
            order_data: Order data dictionary
        
        Returns:
            Saved order dictionary
        """
        db = self.get_db()
        try:
            order = OrderModel(
                items=order_data.get("items", []),
                total=order_data.get("total"),
                date=datetime.fromisoformat(order_data["date"]) if order_data.get("date") else datetime.utcnow()
            )
            db.add(order)
            db.commit()
            db.refresh(order)
            
            return {
                "id": order.id,
                "items": order.items,
                "total": order.total,
                "date": order.date.isoformat() if order.date else None
            }
        except Exception as e:
            db.rollback()
            raise
    
    async def reorder(self, order_id: int) -> dict:
        """
        Reorder items from a previous order.
        
        Args:
            order_id: ID of order to reorder
        
        Returns:
            Result dictionary with reorder status
        """
        order = await self.get_order(order_id)
        
        if not order:
            return {
                "success": False,
                "message": f"Order {order_id} not found"
            }
        
        # Extract item names from order
        items = [item["name"] for item in order.get("items", [])]
        
        # Add items to cart via automation
        from app.services.automation import AutomationService
        automation_service = AutomationService()
        
        result = await automation_service.add_items_to_cart(items)
        
        return {
            "success": result.get("success", False),
            "order_id": order_id,
            "items": items,
            "automation_result": result
        }

