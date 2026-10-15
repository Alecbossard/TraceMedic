import threading

def run(c, d):
    lock = threading.Lock()
    lock.acquire()
    try:
        if not lock.acquire(timeout=0.01):
            raise TimeoutError("non-reentrant lock acquired twice by the same worker")
    finally:
        lock.release()
    return "ok"
