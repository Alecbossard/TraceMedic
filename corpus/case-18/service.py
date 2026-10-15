def run(c, d):
    if "INSERT" not in c["permissions"]:
        raise PermissionError(f"connected as {c["role"]}; permission denied for INSERT; grants={c["permissions"]}")
    return "written"
