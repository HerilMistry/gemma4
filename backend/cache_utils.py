from collections import OrderedDict
from threading import RLock
from typing import Any, Callable


class LRUCache:
    """A simple thread-safe LRU cache.

    Not persistent across process restarts. Use Redis or a DB for persistence.
    """
    def __init__(self, capacity: int = 128):
        self.capacity = int(capacity)
        self.lock = RLock()
        self.cache = OrderedDict()

    def get(self, key: Any):
        with self.lock:
            if key not in self.cache:
                return None
            value = self.cache.pop(key)
            self.cache[key] = value
            return value

    def set(self, key: Any, value: Any):
        with self.lock:
            if key in self.cache:
                self.cache.pop(key)
            elif len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
            self.cache[key] = value

    def clear(self):
        with self.lock:
            self.cache.clear()


def lru_cache_decorator(cache: LRUCache):
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            key = (func.__name__, args, tuple(sorted(kwargs.items())))
            val = cache.get(key)
            if val is not None:
                return val
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        return wrapper

    return decorator
