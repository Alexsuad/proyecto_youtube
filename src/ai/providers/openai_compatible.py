"""API-compatible adapter configurable per provider profile and without inline secrets."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from src.ai.contracts import ExecutionRequest


class OpenAICompatibleProvider:
    name = "openai_compatible"

    def execute(self, request: ExecutionRequest) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        api_key_env = str(request.config.get("api_key_env") or "AI_API_KEY")
        base_url_env = str(request.config.get("base_url_env") or "AI_BASE_URL")
        model_env = str(request.config.get("model_env") or "AI_MODEL")
        api_key = os.getenv(api_key_env, "")
        if not api_key:
            raise PermissionError("CREDENTIALS_MISSING")
        base_url = str(request.config.get("base_url") or os.getenv(base_url_env) or "").rstrip("/")
        model = request.model or os.getenv(model_env)
        if not base_url:
            raise RuntimeError("PROVIDER_UNAVAILABLE")
        if not model:
            raise ValueError("MODEL_UNAVAILABLE")
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": request.config.get("prompt", "")}],
            "response_format": {"type": "json_object"},
            **({"temperature": request.config["temperature"]} if request.config.get("temperature") is not None else {}),
            **({"max_tokens": request.config["max_tokens"]} if request.config.get("max_tokens") is not None else {}),
        }).encode()
        try:
            response = urllib.request.urlopen(
                urllib.request.Request(
                    base_url + "/chat/completions",
                    data=payload,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                ),
                timeout=request.timeout,
            )
            body = json.loads(response.read().decode("utf-8"))
        except TimeoutError as exc:
            raise RuntimeError("TIMEOUT") from exc
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, TimeoutError):
                raise RuntimeError("TIMEOUT") from exc
            raise RuntimeError("PROVIDER_UNAVAILABLE") from exc
        except OSError as exc:
            raise RuntimeError("PROVIDER_UNAVAILABLE") from exc
        try:
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("INVALID_RESPONSE") from exc
        usage = body.get("usage", {})
        usage.update({
            "provider_or_adapter": str(request.config.get("provider_label") or self.name),
            "model_or_evaluator": model,
        })
        return parsed, usage