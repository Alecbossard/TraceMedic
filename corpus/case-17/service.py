from datetime import date

def run(c, d):
    if date.fromisoformat(c["certificate_not_after"]) < date.fromisoformat(d["as_of"]):
        raise ConnectionError("TLS certificate has expired")
    return "connected"
