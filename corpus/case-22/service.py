def run(c, d):
    age_ms = d["now_ms"] - d["sample_ms"]
    return age_ms > c["max_age_seconds"]
