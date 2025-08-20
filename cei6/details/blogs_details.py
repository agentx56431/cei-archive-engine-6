from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..common import get_soup
from ..models import ListingItem, DetailRecord
from ..storage import write_details_jsonl


PDF_RE = re.compile(r"\.pdf(\?.*)?$", re.I)


def _clean(text: str) -> str:
    """Trim and collapse whitespace."""
    return re.sub(r"\s+", " ", (text or "")).strip()


def _find_content_container(soup: BeautifulSoup) -> Optional[BeautifulSoup]:
    """
    Try several CEI-like selectors for the main article content.
    We keep this forgiving so minor site changes don't break us.
    """
    selectors = [
        "article .entry-content",
        "div.entry-content",
        "div.c-article__content",
        "div.article-content",
        "div.post-content",
        "article .post-content",
        "article",  # fallback: grab paragraphs from the article tag
    ]
    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            return node
    return None


def _extract_paragraphs(node: BeautifulSoup) -> List[str]:
    """Collect readable <p> texts from a container node."""
    paras = []
    for p in node.select("p"):
        txt = _clean(p.get_text(" "))
        if txt:
            paras.append(txt)
    # If selector returned the whole <article> and no <p> found, avoid empty
    if not paras:
        # Sometimes content is in <div> <li> etc.; last-resort
        for el in node.find_all(["p", "li"]):
            txt = _clean(el.get_text(" "))
            if txt:
                paras.append(txt)
    return paras


def _extract_pdf_links(node: BeautifulSoup, base_url: str) -> List[str]:
    """Return absolute URLs to any PDFs linked in the content."""
    links: List[str] = []
    for a in node.select("a[href]"):
        href = a.get("href") or ""
        if PDF_RE.search(href):
            links.append(urljoin(base_url, href))
    # de-dup while preserving order
    seen = set()
    uniq = []
    for u in links:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq


def _extract_published(soup: BeautifulSoup) -> Optional[str]:
    """
    Prefer ISO-ish datetime if present. Fallback to text of a <time> or meta.
    We keep this light because the index already captured the date reliably.
    """
    # <time datetime="...">
    t = soup.select_one("time[datetime]")
    if t and t.get("datetime"):
        return _clean(t.get("datetime"))

    # OpenGraph/SEO metas
    for sel in [
        'meta[property="article:published_time"]',
        'meta[name="article:published_time"]',
        'meta[name="pubdate"]',
        'meta[name="date"]',
    ]:
        m = soup.select_one(sel)
        if m and m.get("content"):
            return _clean(m["content"])

    # <time> text
    t2 = soup.select_one("time")
    if t2:
        return _clean(t2.get_text(" "))

    return None


def _extract_title(soup: BeautifulSoup) -> Optional[str]:
    """
    Try to read the on-page title; if missing we keep the index title.
    """
    for sel in ["h1.entry-title", "h1.c-article__title", "article h1", "h1"]:
        h = soup.select_one(sel)
        if h:
            txt = _clean(h.get_text(" "))
            if txt:
                return txt
    # meta og:title as a fallback
    og = soup.select_one('meta[property="og:title"]')
    if og and og.get("content"):
        return _clean(og["content"])
    return None


def _extract_authors(soup: BeautifulSoup) -> List[str]:
    """
    Light optional author extraction (we still trust index authors first).
    """
    names: List[str] = []
    # Common patterns: links with rel=author, or byline containers
    for a in soup.select('a[rel~="author"], .byline a, .c-article__byline a'):
        name = _clean(a.get_text(" "))
        if name:
            names.append(name)
    # De-dup
    seen = set()
    out: List[str] = []
    for n in names:
        if n and n not in seen:
            out.append(n)
            seen.add(n)
    return out


def parse_blog_detail(item: ListingItem) -> Optional[DetailRecord]:
    """
    Download and parse a single CEI blog post detail page.
    Returns a DetailRecord or None if parsing fails.
    """
    soup = get_soup(item.url)

    # Title/date: prefer page content, fall back to index values
    title = _extract_title(soup) or item.title
    date_published = _extract_published(soup) or item.date_published

    container = _find_content_container(soup) or soup
    paragraphs = _extract_paragraphs(container)
    pdf_links = _extract_pdf_links(container, item.url)

    # Authors: trust the index authors; if empty, use page authors
    authors = item.authors or _extract_authors(soup)

    return DetailRecord(
        content_type="blogs",
        url=item.url,
        title=title,
        date_published=date_published,
        issue=item.issue,
        authors=authors,
        outlet=None,         # not applicable to blogs
        outlet_url=None,     # not applicable to blogs
        pdf_links=pdf_links,
        content_paragraphs=paragraphs,
    )


def fetch_blog_details_batch(items: List[ListingItem], cap: Optional[int] = None) -> int:
    """
    Fetch details for the first `cap` items (or all if cap is None/0),
    then write to outputs/details/blogs.jsonl. Returns the number written.
    """
    if cap and cap > 0:
        items = items[:cap]

    details: List[DetailRecord] = []
    for it in items:
        try:
            rec = parse_blog_detail(it)
            if rec:
                details.append(rec)
        except Exception as e:
            print(f"[warn] fetch detail failed (blogs): {it.url} :: {e}")

    if not details:
        return 0

    wrote = write_details_jsonl("blogs", details)
    return wrote
