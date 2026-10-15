import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from tracemedic.v2.prompts import FINISH
from tracemedic.v2.provider import Provider


async def test_structured_control_schema_is_visible_to_model_and_mcp_stays_native(settings):
    requests = []
    result = {
        "outcome": "insufficient",
        "hypothesis_ids": [],
        "next_actions": ["Collect a captured request and its source."],
    }

    class Model(BaseHTTPRequestHandler):
        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(request)
            message = (
                {"content": json.dumps(result)}
                if "format" in request
                else {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "read_bundle",
                                "arguments": {"paths": ["service.py"]},
                            }
                        }
                    ]
                }
            )
            body = json.dumps(
                {"message": message, "prompt_eval_count": 20, "eval_count": 8}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Model)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        provider = Provider(
            settings.model_copy(
                update={"provider": "ollama", "model_url": f"http://127.0.0.1:{server.server_port}"}
            )
        )
        action = await provider.decide("coordinator", "Investigate", {}, [FINISH])
        assert action.arguments == result and action.name == "finish"
        assert action.input_tokens == 20
        action = await provider.decide(
            "investigator",
            "Investigate",
            {},
            [
                {
                    "type": "function",
                    "function": {
                        "name": "read_bundle",
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            ],
        )
        assert action.name == "read_bundle" and action.arguments == {"paths": ["service.py"]}
        assert "next_actions" in requests[0]["messages"][0]["content"]
        assert "tools" not in requests[0] and "format" not in requests[1]
        assert requests[1]["tools"][0]["function"]["name"] == "read_bundle"
    finally:
        server.shutdown()
        server.server_close()
