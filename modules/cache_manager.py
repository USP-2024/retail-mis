import time

_cache = {}

def get(key):
    entry = _cache.get(key)
    if entry:
        if time.time() - entry["ts"] < 300:  # 5 min TTL
            return entry["value"]
        else:
            del _cache[key]
    return None

def set(key, value):
    _cache[key] = {"value": value, "ts": time.time()}

def clear():
    _cache.clear()