"""Decorators that add timing, call tracing and caching to functions."""

import time
from collections.abc import Callable
from functools import lru_cache, wraps


def timer(func: Callable) -> Callable:
    """Print how long each call to func takes."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f} seconds")
        return result

    return wrapper


def log_call(func: Callable) -> Callable:
    """Print when func is called, with its arguments, and when it finishes."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__} with args={args} kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"Finished {func.__name__}")
        return result

    return wrapper


def cache(func: Callable) -> Callable:
    """Remember func's results so repeated calls with the same arguments are instant.

    Uses functools.lru_cache. It keeps up to 1024 results; when full, it
    forgets the least recently used one, so memory use stays limited.
    """
    return lru_cache(maxsize=1024)(func)