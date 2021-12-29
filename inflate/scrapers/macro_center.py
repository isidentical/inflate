from typing import Any

from inflate.scrapers.migros import Migros


class MacroCenter(Migros):

    BASE_URL = "https://www.macrocenter.com.tr/rest/products/search"
    CONFIG: Any = {
        "name": "macrocenter",
        "categories": [
            71332,
            70760,
            71209,
            71625,
            71467,
            71280,
            70802,
            71219,
            70965,
            71351,
            71161,
            70871,
            71325,
            71422,
            71031,
        ],
    }
