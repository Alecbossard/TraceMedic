"""Native function calling. No deterministic fallback is allowed for real providers."""

import json
import time

import httpx

from tracemedic.models import ModelAction


class ProviderUnavailable(RuntimeError):
    pass


class MalformedResponse(ValueError):
    pass


class Provider:
    def __init__(self, settings):
        self.settings = settings

    async def decide(self, role, system, context, tools):
        s = self.settings
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ]
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=s.model_timeout) as client:
                if s.provider == "ollama":
                    response = await client.post(
                        s.model_url.rstrip("/") + "/api/chat",
                        json={
                            "model": s.model,
                            "messages": messages,
                            "tools": tools,
                            "stream": False,
                            "think": False,
                            "keep_alive": "30m",
                            "options": {
                                "temperature": s.temperature,
                                "seed": s.seed,
                                "num_ctx": s.context_tokens,
                                "num_predict": s.max_output_tokens,
                            },
                        },
                    )
                    response.raise_for_status()
                    body = response.json()
                    calls = body.get("message", {}).get("tool_calls", [])
                    input_tokens, output_tokens = (
                        body.get("prompt_eval_count"),
                        body.get("eval_count"),
                    )
                elif s.provider == "openai-compatible":
                    headers = {"Authorization": f"Bearer {s.api_key}"} if s.api_key else {}
                    response = await client.post(
                        s.model_url.rstrip("/") + "/chat/completions",
                        headers=headers,
                        json={
                            "model": s.model,
                            "messages": messages,
                            "tools": tools,
                            "tool_choice": "required",
                            "temperature": s.temperature,
                            "max_tokens": s.max_output_tokens,
                            "seed": s.seed,
                        },
                    )
                    response.raise_for_status()
                    body = response.json()
                    calls = body.get("choices", [{}])[0].get("message", {}).get("tool_calls", [])
                    usage = body.get("usage", {})
                    input_tokens, output_tokens = (
                        usage.get("prompt_tokens"),
                        usage.get("completion_tokens"),
                    )
                else:
                    raise ProviderUnavailable(f"Unknown real provider: {s.provider}")
        except (httpx.TransportError, httpx.HTTPStatusError) as exc:
            # Do not store request headers, credentials or arbitrary provider response bodies.
            status = (
                exc.response.status_code
                if isinstance(exc, httpx.HTTPStatusError)
                else type(exc).__name__
            )
            raise ProviderUnavailable(
                f"Model request failed ({status}); check model URL, availability and credentials"
            ) from exc
        if not calls:
            raise MalformedResponse(
                "Model returned no native function call; choose one advertised action"
            )
        function = calls[0].get("function", {})
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except ValueError as exc:
                raise MalformedResponse("Function arguments are not valid JSON") from exc
        return ModelAction(
            name=function.get("name", ""),
            arguments=arguments,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=round((time.perf_counter() - started) * 1000, 1),
        )
