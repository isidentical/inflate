import requests

from inflate.utils import PRODUCTION

if not PRODUCTION:
    import requests_cache

    requests_cache.install_cache("inflate")


DEFAULT_COUNTER = 1 if PRODUCTION else 0


def make_call(
    *args, counter: int = DEFAULT_COUNTER, **kwargs
) -> requests.Response:
    response = requests.get(*args, **kwargs)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        if counter <= 0:
            raise exc from None

        counter -= 1
        return make_call(*args, counter=counter, **kwargs)
    else:
        return response
