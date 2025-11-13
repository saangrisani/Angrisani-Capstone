# ai_mhbot/openai_utility.py
# ChatGPT help – 2025-10-11: simplified to the current OpenAI Python SDK,
# added small exponential backoff + Retry-After support, and a friendly fallback message.
#
# SDK reference (official):
#   - Chat Completions: https://platform.openai.com/docs/api-reference/chat/create
#   - Error codes (429 / insufficient_quota / rate limits): https://platform.openai.com/docs/guides/error-codes
#   - Rate limits + backoff guidance: https://platform.openai.com/docs/guides/rate-limits
#   - Example backoff pattern (Abort/retry ideas): https://platform.openai.com/docs/guides/rate-limits/retrying-with-exponential-backoff
#   - Python SDK repo: https://github.com/openai/openai-python
# Note: this code uses OpenAI Python SDK v1.x conventions.
from __future__ import annotations
# --- imports -------------------------------------------------------------------
import os
import time
import random
from typing import List, Dict, Optional
# --- OpenAI SDK imports --------------------------------------------------------
from openai import OpenAI, RateLimitError, APIError  # SDK exceptions per 1.x

# --- small helpers ------------------------------------------------------------
# Try to read Retry-After header from exception (if any)
def _retry_after_from(exc: Exception) -> Optional[float]:
    """
    Try to read a Retry-After header (seconds) if the server provided one.
    If missing or unparsable, return None (we'll use backoff instead).
    """
    # --- IGNORE ---
    resp = getattr(exc, "response", None)
    headers = getattr(resp, "headers", None) if resp is not None else None
    # --- IGNORE ---
    if headers and hasattr(headers, "get"):
        val = headers.get("Retry-After")
        try:
            return float(val) if val is not None else None
        except Exception:
            return None
    return None

# Exponential backoff with jitter, capped
def _sleep_backoff(attempt: int, base: float = 0.4, cap: float = 8.0, retry_after: Optional[float] = None) -> None:
    """
    Exponential backoff with jitter, capped. If server says Retry-After, honor it.
    (Pattern based on OpenAI docs/guides – see links above.)
    """
    # --- IGNORE ---
    if retry_after is not None:
        time.sleep(min(max(retry_after, 0.0), cap))
        return
    delay = min(base * (2 ** (attempt - 1)), cap) + random.random() * 0.25
    time.sleep(delay)

# --- main API -----------------------------------------------------------------
# Make a chat completion request with retries and friendly fallback
def complete_chat(
    messages: List[Dict],
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 400,
    max_retries: int = 3,
) -> str:
    """
    Make a chat completion request with small, clear retry logic.

    What this does (simple & safe):
    - Uses the OpenAI Python SDK (1.x) for Chat Completions.
    - Retries a few times on 429 (rate limit) or transient 5xx errors,
      honoring Retry-After if present.
    - If the account has **insufficient_quota**, we do NOT keep retrying; we return
      a friendly message immediately (common 429 variant per docs).
    - On other errors, we stop and return a generic fallback once.

    ChatGPT help – 2025-10-11: kept this minimal so it’s easy to explain in class.
    """
    # --- IGNORE ---
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Be explicit; this helps students/instructors debug quickly.
        raise RuntimeError("OPENAI_API_KEY is not set in the environment.")
    # --- IGNORE ---
    client = OpenAI(api_key=api_key)
    use_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    #
    last_exc: Optional[Exception] = None
    # Retry loop
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=use_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return (resp.choices[0].message.content or "").strip()
        # --- IGNORE ---
        except RateLimitError as e:
            # 429 can mean "too many requests" (retry) or "insufficient_quota" (stop).
            txt = (str(e) or "").lower()
            if "insufficient_quota" in txt or "check your plan and billing" in txt:
                # Helpful resources to surface to users when API access is blocked
                return (
                    "⚠️ I can’t reach the AI service because this project has no available credit. "
                    "I’m still here to listen and offer general support.\n\n"
                    "If you need immediate help or resources, here are some options:\n"
                    "- Veterans Crisis Line: dial 988 then press 1, text 838255, or visit https://www.veteranscrisisline.net\n"
                    "- VA main site (search locations/services): https://www.va.gov\n"
                    "- Find Vet Centers: https://www.va.gov/find-locations\n"
                    "- National Suicide & Crisis Lifeline: dial 988\n"
                    "- Breathing exercise: /exercise/breathing/\n"
                    "- Grounding exercise: /exercise/grounding/\n"
                    "- Sleep exercise: /exercise/sleep/\n"
                )
            last_exc = e
            _sleep_backoff(attempt, retry_after=_retry_after_from(e))
            continue
        # --- IGNORE ---
        except APIError as e:
            # Transient server errors (5xx) → retry; other status codes → stop.
            code = getattr(e, "status_code", None)
            # Some SDKs surface 429 as APIError; handle same as above:
            if code == 429:
                txt = (getattr(e, "message", "") or str(e)).lower()
                if "insufficient_quota" in txt or "check your plan and billing" in txt:
                    return (
                        "⚠️ I can’t reach the AI service because this project has no available credit. "
                        "I’m still here to listen and offer general support.\n\n"
                        "If you need immediate help or resources, here are some options:\n"
                        "- Veterans Crisis Line: dial 988 then press 1, text 838255, or visit https://www.veteranscrisisline.net\n"
                        "- VA main site (search locations/services): https://www.va.gov\n"
                        "- Find Vet Centers: https://www.va.gov/find-locations\n"
                        "- National Suicide & Crisis Lifeline: dial 988\n"
                        "- Breathing exercise: /exercise/breathing/\n"
                        "- Grounding exercise: /exercise/grounding/\n"
                        "- Sleep exercise: /exercise/sleep/\n"
                    )
                last_exc = e
                _sleep_backoff(attempt, retry_after=_retry_after_from(e))
                continue
            if code and 500 <= int(code) < 600:
                last_exc = e
                _sleep_backoff(attempt)
                continue
            # Non-retryable API error; break to fallback.
            last_exc = e
            break

        except Exception as e:
            # Network issues, timeouts, etc. → bail to fallback after loop.
            last_exc = e
            break

    # Friendly fallback (don’t leak stack traces to users)
    return (
        "⚠️ I’m having trouble contacting the AI service right now. "
        "If you’re in crisis, call 988 (Press 1). Otherwise, I’m listening—"
        "tell me a bit more about what’s going on.\n\n"
        "Helpful resources while the AI is unavailable:\n"
        "- Veterans Crisis Line: dial 988 then press 1, text 838255, or visit https://www.veteranscrisisline.net\n"
        "- VA main site (search locations/services): https://www.va.gov\n"
        "- Find Vet Centers: https://www.va.gov/find-locations\n"
        "- National Suicide & Crisis Lifeline: dial 988\n"
        "- Breathing exercise: /exercise/breathing/\n"
        "- Grounding exercise: /exercise/grounding/\n"
        "- Sleep exercise: /exercise/sleep/\n"
    )
