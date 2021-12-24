from __future__ import annotations

import datetime
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from functools import cached_property
from typing import Any, Dict, List, Tuple, Union

JSON = Union[List[Any], Dict[str, Any]]
DatedCollections = Dict[datetime.date, "Collection"]

SEPARATOR = "@"
DAY_FMT = "%y%m%d"
DATE_FMT = f"{DAY_FMT}_%H%M%S"


class Node:
    def dump(self) -> JSON:
        return asdict(self)

    @classmethod
    def load(cls, data: JSON) -> Node:
        raise NotImplementedError


@dataclass
class Item(Node):
    """A single product."""

    name: str
    price: float
    category: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, data: JSON) -> Item:
        return cls(
            data["name"], data["price"], data["category"], data["metadata"]
        )


@dataclass
class Collection(Node):
    """A collection of items from a single source."""

    name: str
    items: List[Item] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.eliminate_duplicates()

    def eliminate_duplicates(self) -> None:
        item_map = {}
        for item in self.items:
            item_map[item.name] = item
        self.items = list(item_map.values())

    @classmethod
    def load(cls, data: JSON) -> Collection:
        return cls(data["name"], [Item.load(item) for item in data["items"]])


@dataclass
class MergedCollection(Node):
    """A unification of multiple collections from a single source."""

    name: str
    items: Dict[Tuple[str, str], List[float]] = field(default_factory=dict)
    collection_dates: List[datetime.date] = field(default_factory=list)

    @classmethod
    def from_collections(
        cls, name: str, dated_collections: DatedCollections
    ) -> MergedCollection:

        instance = MergedCollection(name)

        def fill_prices(key, target):
            items = instance.items.setdefault(key, [])
            while len(items) < target:
                items.append(None)
            return sum(filter(None, reversed(items)))

        index = 0
        for index, (date, collection) in enumerate(
            sorted(dated_collections.items(), key=lambda kv: kv[0])
        ):
            instance.collection_dates.append(date)
            for item in collection.items:
                key = (item.name, item.category)
                last_price = fill_prices(key, index)
                instance.items[key].append(item.price - last_price)

        for key in instance.items.keys():
            fill_prices(key, len(instance.collection_dates))

        return instance

    def dump(self) -> JSON:
        raw_data = asdict(self)
        raw_data["items"] = {
            SEPARATOR.join(key): value
            for key, value in raw_data["items"].items()
        }
        raw_data["collection_dates"] = [
            collection_date.strftime(DAY_FMT)
            for collection_date in raw_data["collection_dates"]
        ]
        return raw_data

    @classmethod
    def load(cls, data: JSON) -> Collection:
        return cls(
            data["name"],
            items={key: prices for key, prices in data["items"].items()},
            collection_dates=[
                datetime.datetime.strptime(raw_date, DAY_FMT)
                for raw_date in data["collection_dates"]
            ],
        )

    @cached_property
    def price_map(self) -> Dict[datetime.date, List[Tuple[str, float]]]:
        price_map = defaultdict(list)
        for name, price_deltas in self.items.items():
            price = None

            for date, price_delta in zip(self.collection_dates, price_deltas):
                if not price_delta:
                    continue

                if price is None:
                    price = 0.0

                price += price_delta
                price_map[name].append((date, price))
        return price_map
