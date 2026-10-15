def run(c, d):
    for attempt in range(c["max_attempts"]):
        if attempt >= d["transient_failures"]:
            return "ok"
    raise TimeoutError(f"retry exhausted: attempts={c["max_attempts"]}, failures before recovery={d["transient_failures"]}")
