"""Interprets natural language test steps into structured ActionSpec objects."""
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import anthropic

from utilities.config_loader import config
from utilities.logger import get_logger

log = get_logger(test="StepInterpreter")

SUPPORTED_ACTIONS = [
    "login", "logout", "navigate", "click", "enter_text", "select_dropdown",
    "select_radio", "check_checkbox", "upload_file", "download_file",
    "search_records", "add_record", "edit_record", "delete_record",
    "save", "cancel", "validate_text", "validate_url", "validate_title",
    "validate_field_value", "validate_table", "validate_error_message",
    "validate_mandatory_fields", "validate_navigation", "handle_date_picker",
    "handle_rich_text",
]

_SYSTEM_PROMPT = f"""You are a test automation interpreter. Given a natural language test step, return ONLY a valid JSON object.

Supported actions: {', '.join(SUPPORTED_ACTIONS)}

JSON schema:
{{
  "action": "<one of the supported actions>",
  "target": "<UI element label, field name, button text, or page name>",
  "target_type": "<button|link|field|textbox|dropdown|checkbox|radio|table|page|message|any>",
  "context": "<parent container, form name, or section — empty string if not mentioned>",
  "value": "<value to enter, select, or validate — null if not applicable>"
}}

Rules:
- action must be exactly one of the supported actions
- Return ONLY the JSON object, no explanation, no markdown fences
- If the step mentions "click", use action=click
- If the step mentions entering/typing/filling text, use action=enter_text
- If the step mentions selecting from a dropdown/list, use action=select_dropdown
- If the step mentions validating/checking/verifying text or message, use action=validate_text
- If the step says "login" with credentials, use action=login
- If the step says "logout"/"log out"/"sign out", use action=logout
- If the step mentions saving, use action=save
- If the step mentions canceling, use action=cancel
"""

_KEYWORD_RULES = [
    (r"\b(login|log in|sign in)\b", "login", "button", None),
    (r"\b(logout|log out|sign out)\b", "logout", "link", None),
    (r"\bclick\s+(?:the\s+)?(.+?)(?:\s+button|\s+link|\s+menu)?\s*$", "click", "button", None),
    (r"\benter\s+(?:text\s+)?['\"]?(.+?)['\"]?\s+in(?:to)?\s+(?:the\s+)?(.+)", "enter_text", "textbox", None),
    (r"\btype\s+['\"]?(.+?)['\"]?\s+in(?:to)?\s+(?:the\s+)?(.+)", "enter_text", "textbox", None),
    (r"\bselect\s+['\"]?(.+?)['\"]?\s+(?:from|in)\s+(?:the\s+)?(.+)", "select_dropdown", "dropdown", None),
    (r"\bvalidate\s+(?:page\s+)?title", "validate_title", "page", None),
    (r"\bvalidate\s+(?:the\s+)?url", "validate_url", "page", None),
    (r"\bvalidate\s+(?:error|validation)\s+message", "validate_error_message", "message", None),
    (r"\bvalidate\s+mandatory\s+fields?", "validate_mandatory_fields", "any", None),
    (r"\bvalidate\s+(?:table|grid)", "validate_table", "table", None),
    (r"\bvalidate\s+navigation", "validate_navigation", "page", None),
    (r"\bsearch\b", "search_records", "textbox", None),
    (r"\badd\s+(?:new\s+)?(?:record|case|entry)", "add_record", "button", None),
    (r"\bedit\s+(?:record|case|entry)", "edit_record", "button", None),
    (r"\bdelete\s+(?:record|case|entry)", "delete_record", "button", None),
    (r"\bsave\b", "save", "button", None),
    (r"\bcancel\b", "cancel", "button", None),
    (r"\bupload\b", "upload_file", "any", None),
    (r"\bdownload\b", "download_file", "link", None),
]


@dataclass
class ActionSpec:
    action: str
    target: str
    target_type: str
    context: str
    value: Optional[str]
    raw_step: str


def _keyword_fallback(step: str) -> Optional[ActionSpec]:
    """Rule-based fallback when AI is unavailable."""
    lower = step.lower().strip()
    for pattern, action, t_type, _ in _KEYWORD_RULES:
        m = re.search(pattern, lower)
        if m:
            groups = m.groups()
            target = groups[-1].strip() if groups else ""
            value = groups[0].strip() if len(groups) > 1 else None
            if action == "enter_text" and len(groups) >= 2:
                value, target = groups[0].strip(), groups[1].strip()
            return ActionSpec(action=action, target=target, target_type=t_type,
                              context="", value=value, raw_step=step)
    # Generic click fallback
    return ActionSpec(action="click", target=step, target_type="any",
                      context="", value=None, raw_step=step)


class StepInterpreter:
    def __init__(self):
        self._client: Optional[anthropic.Anthropic] = None
        self._cache: dict[str, ActionSpec] = {}
        self._cache_file = Path(config.ai.cache_file)
        self._load_cache()

        api_key = config.ai.api_key
        if api_key:
            try:
                self._client = anthropic.Anthropic(api_key=api_key)
            except Exception as e:
                log.warning(f"AI client init failed: {e}. Using keyword fallback.")

    def _load_cache(self):
        if self._cache_file.exists():
            try:
                raw = json.loads(self._cache_file.read_text())
                self._cache = {k: ActionSpec(**v) for k, v in raw.items()}
                log.info(f"Step cache loaded: {len(self._cache)} entries")
            except Exception:
                pass

    def _save_cache(self):
        try:
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            raw = {k: vars(v) for k, v in self._cache.items()}
            self._cache_file.write_text(json.dumps(raw, indent=2))
        except Exception:
            pass

    def _hash(self, step: str) -> str:
        return hashlib.md5(step.strip().lower().encode()).hexdigest()

    def interpret(self, step: str) -> ActionSpec:
        key = self._hash(step)
        if key in self._cache:
            log.debug(f"Cache hit for step: {step!r}")
            return self._cache[key]

        result = self._call_ai(step) if self._client else _keyword_fallback(step)
        self._cache[key] = result
        self._save_cache()
        return result

    def _call_ai(self, step: str) -> ActionSpec:
        try:
            response = self._client.messages.create(
                model=config.ai.model,
                max_tokens=config.ai.max_tokens,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": step}],
            )
            raw = response.content[0].text.strip()
            # Strip any accidental markdown fences
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"```$", "", raw).strip()
            data = json.loads(raw)
            spec = ActionSpec(
                action=data.get("action", "click"),
                target=data.get("target", ""),
                target_type=data.get("target_type", "any"),
                context=data.get("context", ""),
                value=data.get("value"),
                raw_step=step,
            )
            log.info(f"AI interpreted: '{step}' → {spec.action}({spec.target!r})")
            return spec
        except Exception as e:
            log.warning(f"AI interpretation failed ({e}), using keyword fallback")
            return _keyword_fallback(step)
