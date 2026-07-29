"""Adaptador local mínimo para la API de Ollama."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from src.ai.contracts import ExecutionRequest


class OllamaProvider:
    name = "ollama"

    def execute(self, request: ExecutionRequest) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        api_base_env = str(request.config.get("api_base_env") or "OLLAMA_API_BASE")
        model_env = str(request.config.get("model_env") or "OLLAMA_MODEL")
        base_url = str(request.config.get("base_url") or os.getenv(api_base_env) or "http://127.0.0.1:11434").rstrip("/")
        model = request.model or str(request.config.get("model", "") or os.getenv(model_env) or "")
        if not model:
            raise ValueError("MODEL_UNAVAILABLE")
        try:
            payload = json.dumps({"model": model, "prompt": request.config.get("prompt", ""), "stream": False, "format": "json"}).encode()
            response = urllib.request.urlopen(urllib.request.Request(base_url + "/api/generate", data=payload, headers={"Content-Type": "application/json"}), timeout=request.timeout)
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
            parsed = json.loads(body["response"])
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("INVALID_RESPONSE") from exc
        return parsed, {
            "prompt_eval_count": body.get("prompt_eval_count"),
            "eval_count": body.get("eval_count"),
            "provider_or_adapter": str(request.config.get("provider_label") or self.name),
            "model_or_evaluator": model,
        }
