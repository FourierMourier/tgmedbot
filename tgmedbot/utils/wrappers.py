import time
import functools

from .common import infoColorstr

from typing import Callable, Any


__all__ = ['async_time_counter']


def async_time_counter():
    def outer_wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs) -> Any:
            s0: float = time.time()
            result = await func(*args, **kwargs)
            s1: float = time.time()

            total = s1 - s0
            print(infoColorstr(f"{func.__name__} finished in {total:.4f} seconds"))

            return result

        return wrapped

    return outer_wrapper
