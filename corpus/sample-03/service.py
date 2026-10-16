def run(c, d):
    expires_at = d["now_seconds"] + c["ttl_ms"]
    return expires_at
