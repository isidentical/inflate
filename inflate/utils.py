import logging
import os
from collections import deque
from functools import partial, wraps

from rich.progress import track

PRODUCTION = os.getenv("PRODUCTION")

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="[%(filename)s:%(lineno)s - %(funcName)20s()] %(message)s"
)
logger.setLevel(logging.DEBUG)


def robust(default):
    def outer(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception("Error while processing function")
                return default

        return wrapper

    return outer


def exhaust(iterable):
    return deque(iterable, maxlen=0)


progress = partial(track, transient=True, description="Scraping")
