# cei6/indexers/base.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List

@dataclass
class IndexRow:
    source_type: str
    url: str
    title: str
    date_published: str = ""   # ISO-like string if we can find it
    issue: str = ""            # “Energy and Environment”, etc., when available
    authors: List[str] = None  # best-effort from listing page (can be empty)
    outlet: str = ""           # op-eds only (usually needs detail page)
    outlet_url: str = ""       # op-eds only

    def to_dict(self) -> dict:
        d = asdict(self)
        if d["authors"] is None:
            d["authors"] = []
        return d
