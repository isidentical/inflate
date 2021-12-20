from __future__ import annotations

import gzip
import json
from argparse import ArgumentParser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Set, Tuple

from inflate.format import JSON

Product = Tuple[str, int]


@dataclass
class Database:
    products: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def load(cls, data: JSON) -> Database:
        instance = cls()
        for item in data["items"]:
            instance.products[item["name"]] = item["price"]
        return instance

    def compare(
        self, other: Database
    ) -> Tuple[Set[Product], Set[Product], Set[Tuple[Product, Product]]]:
        added, deleted, changed = [], [], []

        for key in self.products.keys() | other.products.keys():
            prod_1 = self.products.get(key)
            prod_2 = other.products.get(key)

            if prod_1 is None:
                added.append((key, prod_2))
            elif prod_2 is None:
                deleted.append((key, prod_1))
            elif prod_1 != prod_2:
                changed.append(((key, prod_1), (key, prod_2)))

        return added, deleted, changed


def read_file(file_1: Path) -> JSON:
    if file_1.suffix.endswith("gz"):
        manager = gzip.open(file_1, "rt")
    else:
        manager = open(file_1, "rt")

    with manager as file:
        return Database.load(json.load(file))


def compare_data(file_1: Path, file_2: Path, /) -> None:
    db_1 = read_file(file_1)
    db_2 = read_file(file_2)

    added, deleted, changed = db_1.compare(db_2)
    for label, items in [
        ("added", added),
        ("deleted", deleted),
        ("changed", changed),
    ]:
        print(label)
        for item in items:
            print("   ", item)


def main(argv: Optional[List[str]] = None) -> None:
    parser = ArgumentParser()
    parser.add_argument("file_1", type=Path)
    parser.add_argument("file_2", type=Path)

    options = parser.parse_args(argv)
    compare_data(options.file_1, options.file_2)


if __name__ == "__main__":
    main()
