# ai_mhbot/openai_utility.py
import os, random, time
from typing import List, Dict

# New SDK (>=1.0)
try:
    from openai import OpenAI
    from openai._exceptions import RateLimitError, APIStatusError
    _NEW_SDK = True
except Exception:
    _NEW_SDK = False
    RateLimitError = Exception
    APIStatusError = Exception


def _sleep_backoff(attempt: int, base: float = 0.4, cap: float = 8.0, retry_after: float | None = None):
    if retry_after is not None:
        time.sleep(min(max(retry_after, 0.0), cap))
        return
    delay = min(base * (2 ** (attempt - 1)), cap) + random.random() * 0.25
    time.sleep(delay)


def _retry_after_from(exc: Exception) -> float | None:
    # Best-effort extraction of Retry-After
    resp = getattr(exc, "response", None)
    headers = getattr(resp, "headers", None) if resp is not None else None
    if headers and hasattr(headers, "get"):
        ra = headers.get("Retry-After")
        try:
            return float(ra) if ra is not None else None
        except Exception:
            return None
    return None


def _call_openai(messages: List[Dict], model: str, temperature: float, max_tokens: int) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    if _NEW_SDK:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
    else:
        import openai
        openai.api_key = api_key
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp["choices"][0]["message"]["content"] or "").strip()


def complete_chat(
    messages: List[Dict],
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 400,
    max_retries: int = 4,
) -> str:
    """
    Main entry point used by views.py.
    Retries on true rate-limits; returns a friendly fallback for quota/billing errors.
    """
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            return _call_openai(messages, model, temperature, max_tokens)

        except RateLimitError as e:
            # Two cases:
            # A) real rate limit -> retry
            # B) insufficient_quota -> do NOT retry, return fallback
            text = str(e).lower()
            if "insufficient_quota" in text or "check your plan and billing" in text:
                return (
                    " I can’t reach the AI service because this project has no available credit. "
                    "I’m still here to listen and offer general support."
                )
            last_exc = e
            _sleep_backoff(attempt, retry_after=_retry_after_from(e))
            continue

        except APIStatusError as e:
            # Retry on 429/5xx; otherwise bubble up
            code = getattr(e, "status_code", None)
            if code == 429:
                # Might be rate-limit OR quota. Check body text too.
                text = (getattr(e, "message", "") or str(e)).lower()
                if "insufficient_quota" in text:
                    return (
                        " I can’t reach the AI service because this project has no available credit. "
                        "I’m still here to listen and offer general support."
                    )
                last_exc = e
                _sleep_backoff(attempt, retry_after=_retry_after_from(e))
                continue
            if code and 500 <= int(code) < 600:
                last_exc = e
                _sleep_backoff(attempt)
                continue
            raise

        except Exception as e:
            last_exc = e
            break

    return (
        " Im having trouble contacting the AI service right now. "
        "If youre in crisis, call 988 (Press 1). Otherwise, Im listening—"
        "tell me a bit more about whats going on."
    )
