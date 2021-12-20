import gzip
import json
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from inflate.scrapers import AVAILABLE_SCRAPERS, run_scrapers


def main(argv: Optional[List[str]] = None) -> None:
    parser = ArgumentParser()
    parser.add_argument("datastore", type=Path)
    parser.add_argument("--scraper", type=str, default=None)
    parser.add_argument("--compress", action="store_true", default=False)

    options = parser.parse_args()

    if options.scraper:
        scrapers = [AVAILABLE_SCRAPERS[options.scraper.casefold()]]
    else:
        scrapers = AVAILABLE_SCRAPERS.values()

    collections = run_scrapers(scrapers=scrapers)

    for collection in collections:
        path = (
            options.datastore
            / collection.name
            / datetime.now().strftime("%y%m%d_%H%M%S")
        )
        path.parent.mkdir(parents=True, exist_ok=True)

        if options.compress:
            manager = gzip.open(path.with_suffix(".json.gz"), "wt")
        else:
            manager = open(path.with_suffix(".json"), "wt")

        with manager as file:
            json.dump(collection.dump(), file, ensure_ascii=False)


if __name__ == "__main__":
    main()
