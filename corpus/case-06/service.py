def run(c, d):
    if c["driver"] not in d["installed_modules"]:
        raise ModuleNotFoundError(f"No module named {c["driver"]!r}; installed={d["installed_modules"]}")
    return "ready"
