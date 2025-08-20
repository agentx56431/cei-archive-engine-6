from __future__ import annotations

import re
from typing import Iterable, List
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# Single place to tweak UA/timeout
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CEI6/1.0 (+https://github.com/agentx56431/cei-archive-engine-6)"
DEFAULT_TIMEOUT = 30

def _normalize_spaces(s: str) -> str:
    return " ".join(s.split())

def text(el) -> str:
    """Get normalized text from a BeautifulSoup element."""
    if not el:
        return ""
    return _normalize_spaces(el.get_text(" ", strip=True))

# Aliases some indexers might have used
def _text(el):  # alias
    return text(el)

def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

# More aliases so older code doesn't break
def fetch_soup(url: str) -> BeautifulSoup:  # alias
    return get_soup(url)

def request_soup(url: str) -> BeautifulSoup:  # alias
    return get_soup(url)

def coerce_datetime_str(s: str) -> str:
    """Try to parse a date string into ISO-8601. If parsing fails, return the original."""
    if not s:
        return ""
    s = s.strip()
    fmts = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.isoformat()
        except Exception:
            pass
    return s

# Alias used by some indexers
def parse_date_or_raw(s: str) -> str:
    return coerce_datetime_str(s)

def clean_authors(raw: Iterable[str] | str) -> List[str]:
    """Normalize authors list: strip 'By', split on commas/and, drop empties, dedupe."""
    if raw is None:
        return []
    parts = [raw] if isinstance(raw, str) else list(raw)

    names: List[str] = []
    for p in parts:
        if not p:
            continue
        p = re.sub(r"^\s*by\s+", "", p, flags=re.I)
        tokens = re.split(r",|\band\b", p)
        for t in tokens:
            name = _normalize_spaces(t.strip())
            if not name:
                continue
            if name not in names:
                names.append(name)
    return names

# Another alias some code might reference
def clean_authors_list(raw: Iterable[str] | str) -> List[str]:
    return clean_authors(raw)
