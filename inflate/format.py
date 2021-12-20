from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, List, Tuple

JSON = List[Any]


class Node:
    def dump(self):
        return asdict(self)


@dataclass
class Item(Node):
    """A single product."""

    name: str
    price: float
    category: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Collection(Node):
    """A collection of items from a single source."""

    name: str
    items: List[Item] = field(default_factory=list)
