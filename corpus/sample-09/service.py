class Adapter:
    def connect(self):
        return "connected"

def run(c, d):
    adapter = Adapter()
    adapter = c["endpoint"]
    return adapter.connect()
