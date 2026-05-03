"""Central configuration model for the automated testing pipeline."""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class OutputFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    HTML = "html"


class AIModel(str, Enum):
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"
    CLAUDE_SONNET = "claude-sonnet-4-20250514"


class LoginCredentials(BaseModel):
    username: str
    password: str
    login_url: Optional[str] = None


class Settings(BaseModel):
    target_url: str
    max_depth: int = Field(default=3, ge=1, le=10)
    rate_limit_rps: float = Field(default=2.0, ge=0.1, le=20.0)
    respect_robots_txt: bool = True
    login_credentials: Optional[LoginCredentials] = None
    output_format: OutputFormat = OutputFormat.JSON
    ai_model: AIModel = AIModel.GPT4O_MINI
    output_dir: Path = Path("output")
    headless: bool = True
    timeout_ms: int = 30_000
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    generate_scripts: bool = True
    run_security_tests: bool = False
