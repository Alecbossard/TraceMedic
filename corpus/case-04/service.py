class Encoder:
    def loads(self, value):
        return value

def run(c, d):
    return Encoder().decode_bytes(d["payload"])
