def run(c, d):
    assert c["port"] == d["listening_port"], f"ConnectionRefused: target port {c[chr(112)+chr(111)+chr(114)+chr(116)]}; probe listener {d[chr(108)+chr(105)+chr(115)+chr(116)+chr(101)+chr(110)+chr(105)+chr(110)+chr(103)+chr(95)+chr(112)+chr(111)+chr(114)+chr(116)]}"
    return "connected"
