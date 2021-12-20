from __future__ import annotations

from typing import Iterable, Iterator

from inflate.format import Collection
from inflate.utils import logger

AVAILABLE_SCRAPERS = {}


class Scraper:
    """Scrape a source"""

    def __init_subclass__(cls: Scraper) -> None:
        AVAILABLE_SCRAPERS[cls.__name__.casefold()] = cls

    def scrape(self) -> Collection:
        ...


def run_scrapers(scrapers: Iterable[Scraper]) -> Iterator[Collection]:
    for scraper in scrapers:
        try:
            yield scraper().scrape()
        except Exception:
            logger.exception()
