"""Thin wrapper around google-genai.

The API key and model names come from the environment, Streamlit secrets or .streamlit/secrets.toml,
in that order. The key is never printed, logged or put in an error message.

`GEMINI_MODEL` may list several models separated by commas; the defaults are always appended as
fallbacks. A model that is retired (404), out of quota (429) or overloaded (503) is skipped for the next one, because
free-tier model names and capacity change without notice (plan §12).
"""
from __future__ import annotations

import os
import time
import tomllib
from pathlib import Path

DEFAULT_MODELS = ("gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash")
_SKIP_TO_NEXT_MODEL = {404, 429, 500, 503}  # free-tier quotas are per model
SECRETS_FILE = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"


class LLMError(Exception):
    def __init__(self, message: str, quota: bool = False):
        super().__init__(message)
        self.quota = quota


# Snapshot taken at import: reading st.secrets copies secrets.toml into os.environ and would
# otherwise silently override a value set in the environment.
_ENV = {k: os.environ[k] for k in ("GEMINI_API_KEY", "GEMINI_MODEL") if os.environ.get(k)}


def setting(name: str) -> str | None:
    value = _ENV.get(name)
    if value:
        return value
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:  # no Streamlit runtime or no secrets file
        pass
    if SECRETS_FILE.exists():
        try:
            return tomllib.loads(SECRETS_FILE.read_text(encoding="utf-8")).get(name)
        except (OSError, tomllib.TOMLDecodeError):
            return None
    return None


class GeminiLLM:
    def __init__(self, api_key: str, models: list[str], max_retries: int = 0, min_interval: float = 0.0):
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self.models = models
        self.model = models[0]  # the model that answered last
        self.max_retries = max_retries  # extra passes over all models; the app uses 0 and falls back instead
        self.min_interval = min_interval  # seconds between calls, to stay under free-tier RPM in batch runs
        self._last_call = 0.0

    def generate(self, system: str, prompt: str) -> str:
        from google.genai import errors, types

        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            temperature=0,
        )
        last_error = LLMError("Không có model Gemini nào khả dụng")
        for attempt in range(self.max_retries + 1):
            for model in self.models:
                wait = self.min_interval - (time.monotonic() - self._last_call)
                if wait > 0:
                    time.sleep(wait)
                self._last_call = time.monotonic()
                try:
                    response = self._client.models.generate_content(model=model, contents=prompt, config=config)
                    self.model = model
                    return response.text or ""
                except errors.APIError as e:
                    last_error = LLMError(f"Gemini API lỗi {e.code} ({e.status}) ở {model}", quota=e.code == 429)
                    if e.code in _SKIP_TO_NEXT_MODEL:
                        continue
                    raise last_error from None  # bad request or auth: another model will not help
                except Exception as e:  # network errors and the like
                    raise LLMError(f"Gemini lỗi kết nối ({type(e).__name__})") from None
            if attempt < self.max_retries:
                time.sleep(20 * (attempt + 1))
        raise last_error


def get_llm(max_retries: int = 0, min_interval: float = 0.0) -> GeminiLLM | None:
    """None when no usable key is configured; callers then use the extractive mode."""
    key = setting("GEMINI_API_KEY")
    if not key or key.startswith("paste-"):
        return None
    configured = [m.strip() for m in (setting("GEMINI_MODEL") or "").split(",") if m.strip()]
    models = list(dict.fromkeys(configured + list(DEFAULT_MODELS)))
    return GeminiLLM(key, models, max_retries, min_interval)
