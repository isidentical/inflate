import gzip
import json
import sys
from pathlib import Path

with gzip.open(Path(sys.argv[1]), "rt") as stream:
    data = json.load(stream)

print(json.dumps(data, indent=4, ensure_ascii=False))
