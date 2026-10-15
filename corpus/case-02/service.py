def run(c, d):
    key = c["connection_variable"]
    if key not in d["environment"]:
        raise RuntimeError(f"Missing environment variable: {key}; supplied keys: {list(d["environment"])}")
    return "ready"
