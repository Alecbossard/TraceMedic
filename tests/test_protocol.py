import json
import os
import subprocess
import sys


def test_unknown_jsonrpc_method_returns_protocol_error(settings):
    env = dict(
        os.environ,
        TRACE_ROOT=str(settings.root),
        TRACE_INCIDENT="case-01",
        TRACE_RUN="protocol-test",
        TRACE_AUDIT_DB=str(settings.audit_db),
    )
    message = {"jsonrpc": "2.0", "id": 913, "method": "tracemedic/nonexistent", "params": {}}
    result = subprocess.run(
        [sys.executable, "-m", "tracemedic.mcp_server"],
        input=json.dumps(message) + "\n",
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    replies = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    error = next(reply for reply in replies if reply.get("id") == 913)
    assert error["error"]["code"] == -32601
