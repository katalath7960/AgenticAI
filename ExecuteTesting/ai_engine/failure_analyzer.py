"""Uses AI to analyze test failures and suggest probable causes."""
import json
from dataclasses import dataclass
from typing import Optional

import anthropic

from utilities.config_loader import config
from utilities.logger import get_logger

log = get_logger(test="FailureAnalyzer")

_SYSTEM_PROMPT = """You are a test automation failure analyst.
Given a failed test step's context, return ONLY a JSON object:
{
  "probable_cause": "<one-sentence explanation of why the step likely failed>",
  "suggested_fix": "<specific actionable suggestion to fix the test or application>",
  "retry_recommended": <true|false>
}
Return ONLY valid JSON. No explanation."""


@dataclass
class FailureAnalysis:
    probable_cause: str
    suggested_fix: str
    retry_recommended: bool

    def to_str(self) -> str:
        return f"Cause: {self.probable_cause} | Fix: {self.suggested_fix}"


class FailureAnalyzer:
    def __init__(self):
        self._client: Optional[anthropic.Anthropic] = None
        api_key = config.ai.api_key
        if api_key:
            try:
                self._client = anthropic.Anthropic(api_key=api_key)
            except Exception:
                pass

    def analyze(self, step: str, error: str, url: str, title: str) -> FailureAnalysis:
        if not self._client:
            return FailureAnalysis(
                probable_cause=f"Step '{step}' failed: {error[:200]}",
                suggested_fix="Check element existence and page state manually.",
                retry_recommended=False,
            )
        try:
            context = (
                f"Failed step: {step}\n"
                f"Error: {error}\n"
                f"Page URL: {url}\n"
                f"Page Title: {title}"
            )
            response = self._client.messages.create(
                model=config.ai.model,
                max_tokens=512,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": context}],
            )
            raw = response.content[0].text.strip()
            data = json.loads(raw)
            return FailureAnalysis(
                probable_cause=data.get("probable_cause", "Unknown"),
                suggested_fix=data.get("suggested_fix", ""),
                retry_recommended=data.get("retry_recommended", False),
            )
        except Exception as e:
            log.warning(f"Failure analysis error: {e}")
            return FailureAnalysis(
                probable_cause=error[:300],
                suggested_fix="Review manually.",
                retry_recommended=False,
            )
