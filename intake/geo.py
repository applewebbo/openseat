"""Province and comuni, read once from the vendored ISTAT dataset.

`intake/data/comuni.json` is refreshed by hand with `just update_comuni` — never
fetched live, so a visitor's browser never depends on ISTAT being reachable.
"""

import json
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "data" / "comuni.json"


@lru_cache
def _data():
    with DATA_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def province_choices():
    """(sigla, nome) pairs, alphabetical by name — the sigla is the stored
    value but never shown, so ordering follows what the visitor reads."""
    return [
        (p["sigla"], p["nome"])
        for p in sorted(_data()["province"], key=lambda p: p["nome"])
    ]


def comune_choices(sigla):
    """(nome, nome) pairs for one province, or empty for an unknown sigla."""
    return [(nome, nome) for nome in _data()["comuni"].get(sigla, [])]
