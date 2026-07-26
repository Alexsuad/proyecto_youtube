"""Adaptador de API compatible configurable exclusivamente por entorno/configuración."""
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
        api_key = os.getenv("AI_API_KEY")
        if not api_key:
            raise PermissionError("AI_API_KEY no configurada")
        base_url = str(request.config.get("base_url") or os.getenv("AI_BASE_URL") or "").rstrip("/")
        model = request.model or os.getenv("AI_MODEL")
        if not base_url or not model:
            raise ValueError("openai_compatible requiere AI_BASE_URL y modelo")
        payload = json.dumps({"model": model, "messages": [{"role": "user", "content": request.config.get("prompt", "")}], "response_format": {"type": "json_object"}}).encode()
        try:
            response = urllib.request.urlopen(urllib.request.Request(base_url + "/chat/completions", data=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}), timeout=request.timeout)
            body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(f"API compatible no disponible: {exc}") from exc
        usage = body.get("usage", {})
        usage.update({"provider_or_adapter": self.name, "model_or_evaluator": model})
        return json.loads(body["choices"][0]["message"]["content"]), usage
