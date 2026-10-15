from datetime import datetime

def run(c, d):
    event = datetime.fromisoformat(d["event"])
    clock = datetime.fromisoformat(d["clock"])
    return event < clock
