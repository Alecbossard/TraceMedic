import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from tracemedic.provider import MalformedResponse, Provider, ProviderUnavailable


class SlowModel(BaseHTTPRequestHandler):
    def do_POST(self):
        time.sleep(0.4)
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


async def test_actual_http_timeout_is_reported_without_fallback(settings):
    server = ThreadingHTTPServer(("127.0.0.1", 0), SlowModel)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        provider = Provider(
            settings.model_copy(
                update={
                    "provider": "ollama",
                    "model_url": f"http://127.0.0.1:{server.server_port}",
                    "model_timeout": 0.1,
                }
            )
        )
        with pytest.raises(ProviderUnavailable, match="ReadTimeout"):
            await provider.decide("investigator", "Investigate", {}, [])
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.parametrize(
    "message",
    [
        {"content": "I would call a tool, but this is prose rather than a native call"},
        {"tool_calls": [{"function": {"name": "read_file", "arguments": "{invalid-json"}}]},
    ],
)
async def test_actual_http_malformed_decisions_never_become_success(settings, message):
    class MalformedModel(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.dumps({"message": message}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), MalformedModel)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        provider = Provider(
            settings.model_copy(
                update={"provider": "ollama", "model_url": f"http://127.0.0.1:{server.server_port}"}
            )
        )
        with pytest.raises(MalformedResponse):
            await provider.decide("investigator", "Investigate", {}, [])
    finally:
        server.shutdown()
        server.server_close()
