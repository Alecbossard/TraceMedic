import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from tracemedic.provider import Provider, ProviderUnavailable


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
