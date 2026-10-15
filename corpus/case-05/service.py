def run(c, d):
    installed = tuple(map(int, c["installed"].split(".")))
    required = tuple(map(int, c["minimum"].split(".")))
    if installed < required:
        raise RuntimeError(f"Dependency incompatible: installed={installed}, minimum={required}")
    return "ready"
