def run(c, d):
    orders = {row["id"]: row for row in d["rows"]}
    return len(orders)
