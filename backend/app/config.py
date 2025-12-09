"""Configuration management for the Wally application."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str
    anthropic_api_key: Optional[str] = None
    
    # Database
    database_url: str = "sqlite:///./wally.db"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Mobile Device
    android_device_id: Optional[str] = None
    appium_server_url: str = "http://localhost:4723"
    
    # Walmart App
    walmart_app_package: str = "com.walmart.android"
    walmart_app_activity: str = ".activity.MainActivity"
    
    # User Configuration
    customer_name: Optional[str] = "Soham Angal"  # Customer name for order matching
    customer_address: Optional[str] = "119 W Oakland Ave, Columbus, OH 43201" # Customer address for matching (e.g., "119 W Oakland Ave, Columbus, OH 43201")
    
    # AI Configuration
    ai_model: str = "gpt-4-turbo-preview"
    voice_model: str = "whisper-1"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


