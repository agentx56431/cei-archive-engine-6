# cei6/indexers/studies_indexer.py
from __future__ import annotations

from typing import List

from bs4 import BeautifulSoup

from cei6.indexers.common import (
    get_soup,
    extract_issue,
    extract_title_and_url,
    extract_authors,
    extract_date,
    absolutize,
)
from cei6.models import ListingItem

LISTING_URL = "https://cei.org/studies/"


def fetch_first_page() -> List[ListingItem]:
    soup = get_soup(LISTING_URL)
    return _parse_listing(soup)


def _parse_listing(soup: BeautifulSoup) -> List[ListingItem]:
    cards = soup.select("article.default-card")
    items: List[ListingItem] = []
    for card in cards:
        title, href = extract_title_and_url(card, "/studies/")
        if not href:
            continue
        url = absolutize(LISTING_URL, href)
        issue = extract_issue(card)
        authors = extract_authors(card)
        date_iso = extract_date(card)

        items.append(
            ListingItem(
                content_type="studies",
                title=title or url,
                url=url,
                date_published=date_iso,
                issue=issue,
                authors=authors,
            )
        )
    return items
