# cei6/indexers/common.py
from __future__ import annotations

import re
from typing import Iterable, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag


HEADERS = {
    "User-Agent": "CEI6/0.1 (+https://github.com/your/repo) Python requests",
}


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def norm_space(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def first_text(tag: Optional[Tag]) -> str:
    return norm_space(tag.get_text(" ", strip=True)) if tag else ""


def extract_issue(card: Tag) -> Optional[str]:
    """
    The colored issue pill in cards appears as a <p class="card-issue ...">...</p>
    """
    pill = card.select_one("p.card-issue")
    txt = first_text(pill)
    return txt or None


def extract_title_and_url(card: Tag, prefix: str) -> (str, str):
    """
    Titles are inside the card body as an <a> linking to the piece.
    We'll choose the first link that looks like it points at the type's prefix.
    """
    # Prefer a dedicated title node if present
    a = card.select_one("h2 a, h3 a, .card-title a")
    if not a:
        # Fallback: any anchor with an href that starts with the section prefix
        for cand in card.select("a[href]"):
            href = cand.get("href", "")
            if href.startswith(prefix) or href.startswith("/" + prefix.strip("/")):
                a = cand
                break
    title = first_text(a)
    url = a.get("href", "") if a else ""
    return title, url


def extract_authors(card: Tag) -> List[str]:
    """
    On CEI, listing cards show 'By: <a class="author-link">Name</a>' inside ul.card-meta li.by-line.
    """
    import re
    authors = []
    for a in card.select("ul.card-meta li.by-line a.author-link"):
        name = first_text(a)
        if name:
            # strip any trailing comma/space (some anchors include a comma)
            name = re.sub(r"[,\s]+$", "", name)
            authors.append(name)
    # De-dup while preserving order
    seen = set()
    uniq: List[str] = []
    for n in authors:
        if n not in seen:
            seen.add(n)
            uniq.append(n)
    return uniq


def extract_date(card: Tag) -> Optional[str]:
    """
    Dates appear in the 'li.posted-on' item, often as <time datetime="..."> or text like 08/18/2025.
    """
    from cei6.models import parse_listing_datetime

    li = card.select_one("ul.card-meta li.posted-on, ul.card-meta li.posted-on.with-author")
    if not li:
        return None
    # Prefer the machine-readable attribute if present
    time = li.find("time")
    if time:
        dt = time.get("datetime") or time.get("content") or first_text(time)
        return parse_listing_datetime(dt)
    # Else parse the text inside the li
    return parse_listing_datetime(first_text(li))


def absolutize(base: str, href: str) -> str:
    return urljoin(base, href or "")
