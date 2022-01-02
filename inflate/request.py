from typing import Iterator, Optional, Set, Tuple

import requests

from inflate.utils import PRODUCTION

if not PRODUCTION:
    import requests_cache

    requests_cache.install_cache("inflate")


PROXY_BASE = "https://cagriari.com/fresh_proxy.txt"
TARGET_COUNTRY = "TR"
MAX_PROXY_TIMEOUT = 30
BLACKLISTED_PROXIES: Set[str] = set()

DEFAULT_COUNTER = 1 if PRODUCTION else 0


def make_call(*args, **kwargs) -> requests.Response:
    response = requests.get(*args, **kwargs)
    response.raise_for_status()
    return response


def check_proxy_health(proxy_addr: str, timeout: float) -> bool:
    try:
        response = requests.get(
            "https://httpbin.org/ip",
            timeout=timeout,
            proxies={"https": proxy_addr},
        )
    except requests.RequestException:
        return False
    else:
        return response.status_code == 200


def parse_proxies(data: str) -> Iterator[str]:
    viable_proxies = []

    for line in data.splitlines():
        line = line.strip()
        if line.startswith("# ") or not line:
            continue

        try:
            proxy_ip, country, raw_time = line.split("|")
        except ValueError:
            continue

        if country != TARGET_COUNTRY:
            continue

        try:
            timing = float(raw_time[:-1])
        except ValueError:
            timing = float("inf")

        viable_proxies.append(("http://" + proxy_ip, timing))

    for proxy_addr, timeout in sorted(viable_proxies):
        if proxy_addr in BLACKLISTED_PROXIES:
            continue

        if check_proxy_health(proxy_addr, timeout + 5):
            yield proxy_addr


def get_proxies() -> Iterator[str]:
    response = requests.get(PROXY_BASE)
    if response.status_code == 200:
        yield from parse_proxies(response.text)


def proxy_call(*args, **kwargs) -> Optional[requests.Response]:
    kwargs.setdefault("timeout", MAX_PROXY_TIMEOUT)
    for proxy in get_proxies():
        kwargs.setdefault("proxies", {"https": proxy})
        try:
            response = requests.get(*args, **kwargs)
        except requests.Timeout:
            BLACKLISTED_PROXIES.add(proxy)
            continue
        else:
            response.raise_for_status()
            return response
    else:
        return None
