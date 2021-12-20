import logging
import os

PRODUCTION = os.getenv("PRODUCTION")

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="[%(filename)s:%(lineno)s - %(funcName)20s()] %(message)s"
)
logger.setLevel(logging.DEBUG)


def robust(default):
    def outer(func):
        if not PRODUCTION:
            return func

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception()
                return default_value

        return wrapper

    return outer
