"""Schema decoding for single control contracts; native calls for MCP/tool choices."""

import json
import time

import httpx

from tracemedic.models import ModelAction
from tracemedic.provider import MalformedResponse, ProviderUnavailable
from tracemedic.provider import Provider as NativeProvider

CONTROLS = {"delegate", "submit_findings", "submit_review", "finish"}


class Provider(NativeProvider):
    def structured_control(self, tools):
        return (
            self.settings.provider == "ollama"
            and len(tools) == 1
            and tools[0]["function"]["name"] in CONTROLS
        )

    async def decide(self, role, system, context, tools):
        if not self.structured_control(tools):
            return await super().decide(role, system, context, tools)
        s, function = self.settings, tools[0]["function"]
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=s.model_timeout) as client:
                response = await client.post(
                    s.model_url.rstrip("/") + "/api/chat",
                    json={
                        "model": s.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": system
                                + f"\nThis turn has one permitted control record: {function['name']}. Return ONLY its JSON arguments matching this schema. Do not wrap them in a function call or invent fields.\nJSON schema:\n"
                                + json.dumps(function["parameters"], ensure_ascii=False),
                            },
                            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
                        ],
                        "format": function["parameters"],
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
        except (httpx.TransportError, httpx.HTTPStatusError) as exc:
            status = (
                exc.response.status_code
                if isinstance(exc, httpx.HTTPStatusError)
                else type(exc).__name__
            )
            raise ProviderUnavailable(
                f"Model request failed ({status}); check configured endpoint"
            ) from exc
        try:
            arguments = json.loads(body.get("message", {}).get("content", ""))
        except ValueError as exc:
            raise MalformedResponse("Structured control response is not valid JSON") from exc
        return ModelAction(
            name=function["name"],
            arguments=arguments,
            input_tokens=body.get("prompt_eval_count"),
            output_tokens=body.get("eval_count"),
            latency_ms=round((time.perf_counter() - started) * 1000, 1),
        )
