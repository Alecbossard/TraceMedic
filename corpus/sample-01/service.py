def run(c, d):
    enabled = bool(c["notifications"])
    return {"sent": enabled}
