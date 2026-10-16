def run(c, d):
    if c["version"] < c["minimum"]:
        raise RuntimeError("Plugin version rejected")
    return "loaded"
