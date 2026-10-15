def run(c, d):
    host = c["host"]
    if host not in d["hosts"]:
        raise ConnectionError(f"DNS lookup failed for {host}; registry={list(d["hosts"])}")
    return "connected"
