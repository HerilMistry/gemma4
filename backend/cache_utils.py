from collections import OrderedDict
from threading import RLock
from typing import Any, Callable
import numpy as np


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


class SemanticCache:
    """A semantic cache using cosine similarity for embeddings.
    
    Not persistent across process restarts.
    """
    def __init__(self, capacity: int = 128, threshold: float = 0.88):
        self.capacity = int(capacity)
        self.threshold = float(threshold)
        self.lock = RLock()
        # cache stores tuples: key -> (embedding, value)
        self.cache = OrderedDict()

    def get(self, query_embedding: list[float] | np.ndarray) -> Any | None:
        with self.lock:
            if not self.cache:
                return None
            
            q_emb = np.array(query_embedding)
            best_key = None
            best_score = -1.0
            
            for key, (emb, value) in self.cache.items():
                dot_product = np.dot(q_emb, emb)
                norm_q = np.linalg.norm(q_emb)
                norm_emb = np.linalg.norm(emb)
                
                if norm_q > 0 and norm_emb > 0:
                    sim = dot_product / (norm_q * norm_emb)
                else:
                    sim = 0.0
                    
                if sim > best_score:
                    best_score = sim
                    best_key = key
                    
            if best_score >= self.threshold and best_key is not None:
                # Move to end (mark as recently used)
                item = self.cache.pop(best_key)
                self.cache[best_key] = item
                return item[1]
            
            return None

    def set(self, key: Any, embedding: list[float] | np.ndarray, value: Any):
        with self.lock:
            if key in self.cache:
                self.cache.pop(key)
            elif len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
            self.cache[key] = (np.array(embedding), value)

    def clear(self):
        with self.lock:
            self.cache.clear()
