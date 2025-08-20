# cei6/indexers/op_eds.py
from __future__ import annotations
from typing import List, Set, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import re

from ..http import fetch_html
from .base import IndexRow

BASE = "https://cei.org"
LIST_URL = "https://cei.org/opeds_articles/"

def _clean(s: Optional[str]) -> str:
    return " ".join(s.split()) if s else ""

def _looks_like_post(href: str) -> bool:
    return (
        href.startswith("/opeds_articles/") and
        "/page/" not in href and
        "posts_per_page" not in href and
        href.count("/") >= 3
    )

def _find_issue(container) -> str:
    for a in container.select("a[href]"):
        href = a.get("href", "")
        if "/issues/" in href:
            t = _clean(a.get_text(strip=True))
            if t:
                return t
    return ""

def _find_authors(container) -> list[str]:
    names: list[str] = []
    for a in container.select('a[rel="author"], .author a, .byline a'):
        t = _clean(a.get_text(strip=True))
        if t and t not in names:
            names.append(t)
    if not names:
        for el in container.select(".author, .byline, .posted-by"):
            t = _clean(el.get_text(" ", strip=True))
            t = re.sub(r"^\s*by\s+", "", t, flags=re.I)
            if t and t.lower() != "by":
                for p in re.split(r",| and ", t):
                    p = _clean(p)
                    if p and p not in names:
                        names.append(p)
    return names

def fetch_first_page() -> List[IndexRow]:
    html, _ = fetch_html(LIST_URL)
    soup = BeautifulSoup(html, "lxml")
    rows: List[IndexRow] = []
    seen: Set[str] = set()

    for a in soup.select("a[href]"):
        href = a.get("href", "")
        abs_url = urljoin(BASE, href)
        if not abs_url.startswith(BASE):
            continue
        path = abs_url.replace(BASE, "", 1)
        if not _looks_like_post(path):
            continue
        if abs_url in seen:
            continue
        seen.add(abs_url)

        container = a.find_parent(["article", "li", "div"]) or soup
        title = _clean(a.get_text(strip=True))
        if not title:
            title = _clean(container.select_one("h2, h3, .entry-title").get_text(strip=True)) if container.select_one("h2, h3, .entry-title") else abs_url

        date = ""
        t = container.select_one("time[datetime]")
        if t and t.get("datetime"):
            date = _clean(t["datetime"])
        elif t:
            date = _clean(t.get_text(strip=True))

        issue = _find_issue(container)
        authors = _find_authors(container)

        rows.append(IndexRow(
            source_type="op_eds",
            url=abs_url,
            title=title,
            date_published=date,
            issue=issue,
            authors=authors or [],
            # outlet/outlet_url usually come from the detail page; blank for now
        ))

    return rows[:30]
