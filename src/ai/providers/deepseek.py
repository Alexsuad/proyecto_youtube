"""DeepSeek adapter using environment-only credentials."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from src.ai.contracts import ExecutionRequest


class DeepSeekProvider:
    name = "deepseek"

    def execute(self, request: ExecutionRequest) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise PermissionError("CREDENTIALS_MISSING")
        base_url = str(request.config.get("base_url") or os.getenv("DEEPSEEK_API_BASE") or "https://api.deepseek.com").rstrip("/")
        model = request.model or os.getenv("DEEPSEEK_MODEL")
        if not model:
            raise ValueError("MODEL_UNAVAILABLE")
        payload = json.dumps({"model": model, "messages": [{"role": "user", "content": request.config.get("prompt", "")}], "response_format": {"type": "json_object"}}).encode()
        try:
            response = urllib.request.urlopen(urllib.request.Request(base_url + "/chat/completions", data=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}), timeout=request.timeout)
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
        usage.update({"provider_or_adapter": self.name, "model_or_evaluator": model})
        return parsed, usage