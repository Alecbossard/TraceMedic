def run(c, d):
    columns = list(filter(None, d["row"].split(",")))
    return {"name": columns[0], "email": columns[1]}
