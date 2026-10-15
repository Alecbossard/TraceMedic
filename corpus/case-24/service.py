def run(c, d):
    cache = {}
    out = []
    for row in d["requests"]:
        key = row["item"]
        if key not in cache:
            cache[key] = row["value"]
        out.append(cache[key])
    return out
