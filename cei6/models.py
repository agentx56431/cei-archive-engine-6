# cei6/models.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat(sep=" ") if dt else None


def parse_listing_datetime(text: str) -> Optional[str]:
    """
    Try multiple formats seen on CEI listings.
    Returns an ISO-like 'YYYY-MM-DD HH:MM:SS' (or date-only) string if possible.
    """
    text = (text or "").strip()
    if not text:
        return None

    # Common cases we’ve seen:
    # 1) Full datetime via <time datetime="2025-08-18T16:52:53-04:00">
    # 2) Date-only like "08/18/2025"
    fmts = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%m/%d/%Y",
        "%Y-%m-%d",
    ]
    for fmt in fmts:
        try:
            dt = datetime.strptime(text, fmt)
            # keep time if present; otherwise date only
            if "H" in fmt:
                return _to_iso(dt.replace(tzinfo=None))
            else:
                return dt.date().isoformat()
        except Exception:
            pass
    # Last resort: return original string; downstream can decide
    return text


@dataclass
class ListingItem:
    content_type: str                  # 'blogs', 'news_releases', 'op_eds', 'studies'
    title: str
    url: str
    date_published: Optional[str] = None  # ISO string where possible
    issue: Optional[str] = None
    authors: List[str] = field(default_factory=list)

    def pretty_line(self) -> str:
        parts = [self.title, self.url]
        if self.date_published or self.issue or self.authors:
            meta = []
            if self.date_published:
                meta.append(self.date_published)
            if self.issue:
                meta.append(self.issue)
            if self.authors:
                meta.append("By " + ", ".join(self.authors))
            parts[-1] = f"{parts[-1]} | " + " • ".join(meta)
        return " | ".join(parts)
