def run(c, d):
    return d["admin"] or d["active"] and d["has_scope"]
