import os

# Works with OpenAI python SDK >= 1.0
try:
    from openai import OpenAI
    _NEW_SDK = True
except Exception:
    _NEW_SDK = False

def complete_chat(messages, model=None, temperature=0.3, max_tokens=400):
    """
    messages = [{"role":"system"/"user"/"assistant", "content":"..."}]
    returns assistant text (str)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ OPENAI_API_KEY is not configured on the server."

    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if _NEW_SDK:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=messages,
        )
        return resp.choices[0].message.content.strip()
    else:
        # fallback for very old SDKs
        import openai
        openai.api_key = api_key
        resp = openai.ChatCompletion.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=messages,
        )
        return resp["choices"][0]["message"]["content"].strip()
