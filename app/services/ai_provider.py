from typing import Any

import httpx

from app.config import get_settings
from app.core.exceptions import AIProviderError, ProviderNotConfiguredError


def _provider_config() -> tuple[str, str | None, int]:
    settings = get_settings()
    if not settings.ai_base_url:
        raise ProviderNotConfiguredError(
            "Set AI_BASE_URL in .env to configure an OpenAI-compatible AI provider."
        )
    api_key = (
        settings.ai_api_key.get_secret_value()
        if settings.ai_api_key and settings.ai_api_key.get_secret_value()
        else None
    )
    return settings.ai_base_url.rstrip("/"), api_key, settings.ai_timeout_seconds


async def _post(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    base_url, api_key, timeout = _provider_config()
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{base_url}/{endpoint}", json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise AIProviderError(
            "The configured AI provider could not complete the request. Check provider settings and availability."
        ) from error
    if not isinstance(result, dict):
        raise AIProviderError("The configured AI provider returned an invalid response.")
    return result


async def embed_texts(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    response = await _post(
        "embeddings",
        {"model": settings.ai_embedding_model, "input": texts},
    )
    data = response.get("data")
    if not isinstance(data, list):
        raise AIProviderError("The embedding provider returned no embeddings.")
    try:
        ordered = sorted(data, key=lambda item: item["index"])
        embeddings = [[float(value) for value in item["embedding"]] for item in ordered]
    except (KeyError, TypeError, ValueError) as error:
        raise AIProviderError("The embedding provider returned invalid embedding data.") from error
    if len(embeddings) != len(texts) or any(not vector for vector in embeddings):
        raise AIProviderError("The embedding provider returned an unexpected number of embeddings.")
    dimensions = {len(vector) for vector in embeddings}
    if len(dimensions) != 1:
        raise AIProviderError("The embedding provider returned inconsistent vector dimensions.")
    return embeddings


async def generate_completion(messages: list[dict[str, str]]) -> str:
    settings = get_settings()
    response = await _post(
        "chat/completions",
        {"model": settings.ai_chat_model, "messages": messages, "temperature": 0.2},
    )
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise AIProviderError("The language model returned an invalid response.") from error
    if not isinstance(content, str) or not content.strip():
        raise AIProviderError("The language model returned an empty answer.")
    return content.strip()
