def run(c, d):
    if d["response_ms"] > c["timeout_ms"]:
        raise TimeoutError(f"response={d["response_ms"]}ms exceeds timeout={c["timeout_ms"]}ms")
    return "ok"
