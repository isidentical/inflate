from typing import Any, Iterator

from inflate.format import JSON, Collection, Item
from inflate.request import make_call, requests
from inflate.scrapers.scraper import Scraper
from inflate.utils import progress, robust

EMPTY_ITEM = {"metaData": {}, "pageCount": 0, "storeProductInfos": []}


class Migros(Scraper):

    BASE_URL = "https://www.migros.com.tr/rest/products/search"
    CONFIG: Any = {"name": "migros", "categories": list(range(1, 11))}

    @robust(default=EMPTY_ITEM)
    def request(self, **kwargs) -> JSON:
        response = make_call(self.BASE_URL, **kwargs)

        data = response.json()
        assert data["successful"]
        return data["data"]

    def collect_category(self, category: int) -> Iterator[Item]:
        meta = self.request(params={"category-id": category, "page": 0})
        category_name = meta["metaData"].get("title")
        if category_name is None:
            return None

        for page in progress(
            range(meta["pageCount"] + 1),
            description=f"Scraping {category_name!r}",
        ):
            data = self.request(params={"category-id": category, "page": page})

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
        return Collection(
            name=self.CONFIG["name"],
            items=[
                item
                for category in self.CONFIG["categories"]
                for item in self.collect_category(category)
            ],
        )
