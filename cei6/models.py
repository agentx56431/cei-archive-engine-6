# cei6/models.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import re

def _normalize_author(name: str) -> str:
    # collapse whitespace
    name = re.sub(r"\s+", " ", name).strip()
    # remove trailing commas/spaces
    name = re.sub(r"[,\s]+$", "", name)
    return name

def normalize_authors(authors: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for a in authors:
        if not isinstance(a, str):
            continue
        clean = _normalize_author(a)
        if not clean:
            continue
        if clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out

@dataclass
class ListingItem:
    content_type: str           # "blogs" | "news_releases" | "op_eds" | "studies"
    title: str
    url: str
    date_published: Optional[datetime] = None
    issue: Optional[str] = None
    authors: List[str] = None   # normalized at construction

    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        self.authors = normalize_authors(self.authors)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # serialize datetime -> ISO string
        if self.date_published and isinstance(self.date_published, datetime):
            d["date_published"] = self.date_published.isoformat()
        return d
