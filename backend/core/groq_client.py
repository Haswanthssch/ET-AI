"""
AURA-EPC Groq Client
Singleton wrapper around the official Groq Python SDK.
Strictly uses groq SDK — no OpenAI SDK dependency.
"""
from __future__ import annotations

import base64
import asyncio
from functools import lru_cache
from pathlib import Path
from typing import Any

from groq import AsyncGroq
from .config import settings


@lru_cache(maxsize=1)
def get_groq_client() -> AsyncGroq:
    """Return a cached singleton AsyncGroq client."""
    return AsyncGroq(api_key=settings.GROQ_API_KEY)


async def chat_complete(
    messages: list[dict[str, Any]],
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 2048,
) -> str:
    """
    Fire a chat completion via Groq SDK.
    Returns the text content of the first choice.
    """
    client = get_groq_client()
    model = model or settings.GROQ_TEXT_MODEL
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


async def vision_complete(
    prompt: str,
    image_bytes: bytes,
    image_mime: str = "image/png",
) -> str:
    """
    Send an image + prompt to Groq's vision model.
    Tries GROQ_VISION_MODEL first; falls back to GROQ_VISION_FALLBACK_MODEL.
    """
    client = get_groq_client()
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{image_mime};base64,{b64_image}"

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }
    ]

    for model in [settings.GROQ_VISION_MODEL, settings.GROQ_VISION_FALLBACK_MODEL]:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as exc:
            if model == settings.GROQ_VISION_MODEL:
                # Log fallback and retry
                print(f"[WARN] Vision model '{model}' failed ({exc}). Falling back to '{settings.GROQ_VISION_FALLBACK_MODEL}'.")
                continue
            raise RuntimeError(f"Both vision models failed. Last error: {exc}") from exc
    return ""  # unreachable but satisfies type checker

