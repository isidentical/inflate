import json
import re
from typing import Iterator

from inflate.format import JSON, Collection, Item
from inflate.request import make_call, requests
from inflate.scrapers import Scraper
from inflate.utils import logger, robust

RE_JSON = re.compile(
    r"<script type=\"application\/ld\+json\">(.*?)<\/script>\n",
    flags=re.MULTILINE | re.DOTALL,
)

EMPTY_ITEM = {"@graph": {"itemListElement": []}}


class A101(Scraper):

    BASE_URL = "https://www.a101.com.tr/market"
    CONFIG = {"name": "a101", "max_page_limit": 100}

    @robust(default=EMPTY_ITEM)
    def request(self, **kwargs) -> JSON:
        response = make_call(self.BASE_URL, **kwargs)

        assert (match := RE_JSON.search(response.text))
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
        logger.debug("Collecting %s", self.CONFIG["name"])

        page = 0
        collection = Collection(self.CONFIG["name"])
        while page < self.CONFIG["max_page_limit"]:
            logger.debug("     Collecting page %d", page)
            items = list(self.collect_page(page))
            if not items:
                break
            collection.items.extend(items)
            page += 1

        return collection
