from typing import Iterator

from inflate.format import JSON, Collection, Item
from inflate.request import make_call, requests
from inflate.scrapers import Scraper
from inflate.utils import logger, robust

EMPTY_ITEM = {"metaData": {}, "pageCount": 0, "storeProductInfos": []}


class Migros(Scraper):

    BASE_URL = "https://www.migros.com.tr/rest/products/search"
    CONFIG = {"name": "migros", "categories": tuple(range(1, 11))}

    @robust(default=EMPTY_ITEM)
    def request(self, **kwargs) -> JSON:
        response = make_call(self.BASE_URL, **kwargs)

        data = response.json()
        assert data["successful"]
        return data["data"]

    def collect_category(self, category: int) -> Iterator[Item]:
        logger.debug(
            "  Collecting category %d/%d",
            category,
            max(self.CONFIG["categories"]),
        )

        meta = self.request(params={"category-id": category, "page": 0})
        category_name = meta["metaData"].get("title")
        if category_name is None:
            return None

        for page in range(meta["pageCount"] + 1):
            data = self.request(params={"category-id": category, "page": page})
            logger.debug("    Collecting page %d/%d", page, meta["pageCount"])

            for product in data["storeProductInfos"]:
                yield Item(
                    product["name"],
                    product["salePrice"] / 100,
                    category_name,
                    metadata={
                        "id": product["id"],
                        "sku": product["sku"],
                        "brand": product["brand"]["name"],
                        "sub_category": product["category"]["name"],
                    },
                )

    def scrape(self) -> Collection:
        logger.debug("Collecting %s", self.CONFIG["name"])
        return Collection(
            name=self.CONFIG["name"],
            items=[
                item
                for category in self.CONFIG["categories"]
                for item in self.collect_category(category)
            ],
        )
