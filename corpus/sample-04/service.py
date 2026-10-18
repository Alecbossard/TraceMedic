def collect(item, bucket=[]):
    bucket.append(item)
    return list(bucket)

def run(c, d):
    collect(d["first"])
    return collect(d["second"])
