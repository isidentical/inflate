from typing import Iterator

from requests import HTTPError

from inflate.format import JSON, Collection, Item
from inflate.request import make_call, requests
from inflate.scrapers.scraper import Scraper
from inflate.utils import logger, robust

EMPTY_ITEM = {"pagination": {"page_count": 0}, "payload": {"products": []}}


class Sok(Scraper):

    BASE_URL = "https://api.ceptesok.com/api/categories/{category}/products"
    CONFIG = {"name": "sok", "store-id": "2359"}

    @robust(default=EMPTY_ITEM)
    def request(self, category: int, **kwargs) -> JSON:
        kwargs.setdefault("headers", {}).setdefault(
            "store-id", self.CONFIG["store-id"]
        )
        try:
            response = make_call(
                self.BASE_URL.format(category=category), **kwargs
            )
        except HTTPError as exc:
            # Sometimes SOK API throws weird errors
            if exc.response.status_code == 400:
                return EMPTY_ITEM
            else:
                raise

        data = response.json()
        return data

    def scrape(self) -> Collection:
        logger.debug("Collecting %s", self.CONFIG["name"])

        meta = self.request(category=0, params={"stock": "true", "page": 0})

        items = []
        for page in range(1, meta["pagination"]["page_count"] + 1):
            data = self.request(
                category=0, params={"stock": "true", "page": page}
            )
            for product in data["payload"]["products"]:
                items.append(
                    Item(
                        product["product_name"],
                        product["price"]["original"],
                        product["category_breadcrumb"],
                        metadata={
                            "brand": product["brand"],
                            "serial": product["serial_id"],
                        },
                    )
                )

        return Collection(name=self.CONFIG["name"], items=items)
