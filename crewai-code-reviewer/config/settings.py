"""
Configuration
==============
Central configuration for the Code Review Agent.
"""

import os
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    """LLM provider configuration."""

    # Supported: "openai", "anthropic", "ollama", "azure"
    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 4096
    api_key: str = ""

    def __post_init__(self):
        if not self.api_key:
            if self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY", "")
            elif self.provider == "anthropic":
                self.api_key = os.getenv("ANTHROPIC_API_KEY", "")


@dataclass
class ReviewConfig:
    """Review agent configuration."""

    max_files: int = 50
    max_file_size_kb: int = 500
    max_total_context_chars: int = 120_000
    focus_areas: list[str] = field(
        default_factory=lambda: [
            "frontend",
            "backend",
            "security",
            "performance",
            "quality",
        ]
    )
    verbose: bool = False


@dataclass
class GitHubConfig:
    """GitHub integration configuration."""

    token: str = ""
    auto_comment: bool = False  # Auto-post review to PR

    def __post_init__(self):
        if not self.token:
            self.token = os.getenv("GITHUB_TOKEN", "")


@dataclass
class AppConfig:
    """Top-level application configuration."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    review: ReviewConfig = field(default_factory=ReviewConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)
