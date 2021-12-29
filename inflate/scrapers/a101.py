import json
import re
from typing import Any, Iterator

from inflate.format import JSON, Collection, Item
from inflate.request import make_call, requests
from inflate.scrapers.scraper import Scraper
from inflate.utils import progress, robust

RE_JSON = re.compile(
    r"<script type=\"application\/ld\+json\">(.*?)<\/script>\n",
    flags=re.MULTILINE | re.DOTALL,
)

EMPTY_ITEM: Any = {"@graph": {"itemListElement": []}}


class A101(Scraper):

    BASE_URL = "https://www.a101.com.tr/market"
    CONFIG: Any = {"name": "a101", "max_page_limit": 50}

    @robust(default=EMPTY_ITEM)
    def request(self, **kwargs) -> JSON:
        response = make_call(self.BASE_URL, **kwargs)

        if not (match := RE_JSON.search(response.text)):
            return EMPTY_ITEM

        return json.loads(match.group(1))

    def collect_page(self, page: int) -> Iterator[Item]:
        data = self.request(params={"page": page})

        for raw_item in data["@graph"]["itemListElement"]:
            item = raw_item["item"]
            if item["offers"]["availability"] != "https://schema.org/InStock":
                continue
            yield Item(
                item["name"],
                float(item["offers"]["price"]),
                item["category"]["name"],
                metadata={
                    "sku": item["sku"],
                    "brand": item["brand"],
                },
            )

    def scrape(self) -> Collection:
        page = 0
        collection = Collection(self.CONFIG["name"])
        for _ in progress(range(self.CONFIG["max_page_limit"])):
            items = list(self.collect_page(page))
            if not items:
                break
            collection.items.extend(items)
            page += 1

        return collection
