"""Application configuration loaded from environment variables."""

from pathlib import Path
from pydantic_settings import BaseSettings

# Always load from hotel-agent-langfuse/.env regardless of working directory
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # LangSmith
    langsmith_api_key: str = "ADD_TOKEN"
    langsmith_project: str = "default"
    langsmith_tracing: bool = True

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    model_config = {
        "env_file": str(_ENV_FILE),
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # ignore extra keys from shared .env files
    }


settings = Settings()
