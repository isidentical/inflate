import datetime
import io
import json
import os
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Iterator

import requests
from rich.progress import track

from inflate.format import (
    DATE_FMT,
    JSON,
    Collection,
    DatedCollections,
    MergedCollection,
)
from inflate.utils import exhaust

GITHUB_USER = os.getenv("GITHUB_USER")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if GITHUB_USER is None or GITHUB_TOKEN is None:
    raise ValueError("Please set the GITHUB_TOKEN")

GITHUB_AUTH = (GITHUB_USER, GITHUB_TOKEN)

PRODUCTION = os.getenv("PRODUCTION")
if not PRODUCTION:
    import requests_cache

    requests_cache.install_cache("tmp_github")


DEFAULT_REPO = os.getenv("DEFAULT_REPO", "isidentical/inflate")
API_BASE = "https://api.github.com"


GroupedCollections = Dict[str, DatedCollections]
MergedCollections = Dict[str, MergedCollection]


def make_api_call(endpoint: str, **kwargs) -> JSON:
    kwargs.setdefault("auth", GITHUB_AUTH)
    response = requests.get(API_BASE + endpoint, **kwargs)
    response.raise_for_status()
    return response.json()


def iter_artifacts(repository: str = DEFAULT_REPO) -> Iterator[JSON]:
    page = 1
    while True:
        data = make_api_call(
            "/repos/isidentical/inflate/actions/artifacts",
            params={"page": page, "per_page": 100},
        )
        if len(artifacts := data["artifacts"]) == 0:
            return None

        yield from artifacts
        page += 1


def get_artifact(url: str) -> None:
    response = requests.get(url, auth=GITHUB_AUTH)
    response.raise_for_status()

    return io.BytesIO(response.content)


def collect_artifacts(path: Path, repository: str = DEFAULT_REPO) -> None:
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for artifact in iter_artifacts(repository):
            futures.append(
                executor.submit(
                    get_artifact,
                    artifact["archive_download_url"],
                )
            )

        for buffer in track(
            as_completed(futures), transient=True, total=len(futures)
        ):
            archive = zipfile.ZipFile(buffer.result())
            archive.extractall(path)


def deserialize_tree(path: Path) -> GroupedCollections:
    stores = defaultdict(dict)
    for store in path.iterdir():
        for collection in store.glob("*.json"):
            date = datetime.datetime.strptime(collection.stem, DATE_FMT).date()
            with open(collection) as stream:
                stores[store.stem][date] = Collection.load(json.load(stream))
    return stores


def fetch_collections() -> GroupedCollections:
    with TemporaryDirectory() as directory:
        path = Path(directory)
        collect_artifacts(path)
        return deserialize_tree(path)


def generate_collections() -> MergedCollections:
    grouped_collections = fetch_collections()

    stores = {}
    for store, dated_collections in grouped_collections.items():
        stores[store] = MergedCollection.from_collections(
            store, dated_collections
        )

    return stores


def find_most_volatile(
    collection: MergedCollections, *, volatility_threshold: int = 3
) -> None:
    groups = defaultdict(dict)
    for name, dated_prices in collection.price_map.items():
        groups[len(dated_prices)][name] = [
            dated_price[1] for dated_price in dated_prices
        ]

    for key, sub_map in sorted(groups.items()):
        if key <= volatility_threshold:
            continue

        print(key)
        print("=" * 50)
        for name, price in sub_map.items():
            print("  ", name, "=>", price)


def find_highest_price_gap(
    collection: MergedCollections, *, max_items: int = 20
) -> None:
    gaps = {}
    for name, dated_prices in collection.price_map.items():
        min_price = min(dated_prices, key=lambda kv: kv[1])
        max_price = max(dated_prices, key=lambda kv: kv[1])
        gap = abs(max_price[1] - min_price[1])
        gaps[gap] = (name, min_price, max_price)

    for index, (gap, _) in enumerate(sorted(gaps.items())[:max_items]):
        print(f"{index}.", name, gap, "TRY")


def best_sales(collection: MergedCollections, *, max_items: int = 50) -> None:
    gaps = {}
    for name, dated_prices in collection.price_map.items():
        if len(dated_prices) <= 1:
            continue
        current_price = dated_prices[-1]
        first_price = dated_prices[0]
        gaps[first_price[1] - current_price[1]] = (
            name,
            first_price,
            current_price,
        )

    for index, [
        gap,
        (name, (_, first_price), (_, last_price)),
    ] in enumerate(sorted(gaps.items(), reverse=True)[:max_items]):
        print(
            f"{index}.",
            name,
            f"{gap:5.3f}",
            "lira",
            f"({first_price} -> {last_price})",
        )
