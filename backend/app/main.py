"""Main FastAPI application for Wally voice AI agent."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api import voice, orders, automation

app = FastAPI(
    title="Wally Voice AI Agent",
    description="Voice-powered AI agent for Walmart orders",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (voice.html interface)
app.mount("/voice", StaticFiles(directory="static", html=True), name="voice_static")

# Include routers
app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(automation.router, prefix="/api/v1/automation", tags=["automation"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Wally Voice AI Agent API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )



