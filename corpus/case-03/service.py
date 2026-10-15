def run(c, d):
    allowed = ["DEBUG", "INFO", "WARN", "ERROR"]
    if c["level"] not in allowed:
        raise ValueError(f"Invalid level {c["level"]!r}; accepted: {allowed}")
    return "ready"
