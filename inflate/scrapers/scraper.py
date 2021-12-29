from __future__ import annotations

from typing import Any, Iterable, Iterator, Type

from inflate.format import Collection
from inflate.utils import logger

AVAILABLE_SCRAPERS = {}


class Scraper:
    """Scrape a source"""

    CONFIG: Any = {}

    def __init_subclass__(cls: Type[Scraper]) -> None:
        cls.CONFIG = cls.CONFIG.copy()
        AVAILABLE_SCRAPERS[cls.__name__.casefold()] = cls

    def scrape(self) -> Collection:
        ...


def run_scrapers(scrapers: Iterable[Type[Scraper]]) -> Iterator[Collection]:
    for scraper in scrapers:
        logger.debug(f"Running {scraper.CONFIG['name']}")
        try:
            yield scraper().scrape()
        except Exception:
            logger.exception(
                f"Exception when processing {scraper.CONFIG['name']!r}"
            )
