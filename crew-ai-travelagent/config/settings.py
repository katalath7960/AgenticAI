import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OpenAI API Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY")

    # Travel Booking API Configuration (mock for now)
    travel_api_base_url: str = "https://api.travelbooking.com"
    travel_api_key: Optional[str] = os.getenv("TRAVEL_API_KEY")

    # CrewAI Configuration
    max_iterations: int = 10
    verbose: bool = True

    # Agent Configuration
    customer_service_temperature: float = 0.7
    travel_advisor_temperature: float = 0.8
    booking_agent_temperature: float = 0.3  # Lower temperature for booking accuracy

    class Config:
        env_file = ".env"

settings = Settings()