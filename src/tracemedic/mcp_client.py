import json
import os
import sys
from contextlib import asynccontextmanager

from mcp import Client, StdioServerParameters

from tracemedic.config import Settings
from tracemedic.models import ToolResult
from tracemedic.store import Store, stable_id


class IncidentTools:
    def __init__(self, client, settings, store, run_id, schemas):
        self.client, self.settings, self.store, self.run_id = client, settings, store, run_id
        self.schemas = schemas

    async def call(self, name, arguments, role, step):
        if name not in {t["function"]["name"] for t in self.schemas}:
            raise ValueError(f"Tool not allowed: {name}")
        arguments = dict(arguments)
        # Model cannot choose another run's operation key. One pure fixture operation per run.
        if name == "run_check":
            arguments["operation_key"] = stable_id(self.run_id, "fixture-check")
        key = "mcp:" + stable_id(name, arguments)
        cached = self.store.cached(self.run_id, key)
        if cached and cached["status"] == "completed":
            self.store.event(
                self.run_id,
                f"reuse:{step}",
                role,
                "tool_reused",
                f"Reused saved {name}",
                {"tool": name, "operation_key": key},
            )
            return ToolResult.model_validate(json.loads(cached["result"]))
        if self.store.metrics(self.run_id)["tool_calls"] >= self.settings.max_tools:
            raise ValueError("MCP tool budget exhausted")
        self.store.event(
            self.run_id,
            f"tool-start:{step}",
            role,
            "tool_call",
            name,
            {"arguments": arguments, "operation_key": key},
        )
        result = await self.client.call_tool(
            name, arguments, read_timeout_seconds=self.settings.tool_timeout
        )
        payload = result.structured_content
        if payload is None:
            texts = [b.text for b in result.content if hasattr(b, "text")]
            if result.is_error:
                payload = {"ok": False, "error": " ".join(texts)[:1200]}
            else:
                payload = json.loads(texts[0])
        output = ToolResult.model_validate(payload)
        self.store.add_evidence(self.run_id, [e.model_dump() for e in output.evidence])
        self.store.complete(self.run_id, key, output.model_dump())
        self.store.event(
            self.run_id,
            f"tool-end:{step}",
            role,
            "tool_result",
            f"{name}: {'ok' if output.ok else 'error'}",
            {"tool": name, **output.model_dump(), "operation_key": key},
        )
        return output


@asynccontextmanager
async def connect_tools(settings: Settings, store: Store, run_id: str, incident_id: str):
    env = {
        k: v
        for k, v in os.environ.items()
        if k in ("SYSTEMROOT", "PATH", "TEMP", "TMP", "USERPROFILE")
    }
    env.update(
        TRACE_ROOT=str(settings.root),
        TRACE_INCIDENT=incident_id,
        TRACE_RUN=run_id,
        TRACE_AUDIT_DB=str(settings.audit_db),
        PYTHONUTF8="1",
    )
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "tracemedic.mcp_server"],
        env=env,
        cwd=str(settings.root),
    )
    async with Client(server, read_timeout_seconds=settings.tool_timeout) as client:
        discovered = await client.list_tools()
        schemas = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.input_schema,
                },
            }
            for t in discovered.tools
        ]
        # The operation key is owned by the adapter, hidden from the model's contract.
        for schema in schemas:
            if schema["function"]["name"] == "run_check":
                schema["function"]["parameters"] = {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                }
        store.event(
            run_id,
            "mcp-discovery",
            "system",
            "mcp_connected",
            "Discovered tools over MCP stdio in a separate process",
            {
                "client_pid": os.getpid(),
                "tools": [t["function"]["name"] for t in schemas],
                "transport": "stdio",
                "sdk": "mcp 2.3.0",
            },
        )
        yield IncidentTools(client, settings, store, run_id, schemas)
