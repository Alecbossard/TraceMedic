def run(c, d):
    attempts = 0
    for _ in range(c["attempts"]):
        try:
            attempts += 1
            if attempts <= d["transient_failures"]:
                raise TimeoutError("temporary failure")
            return "delivered"
        except TimeoutError:
            raise
