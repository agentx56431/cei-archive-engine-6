# cei6/cli.py
from __future__ import annotations

import argparse
from typing import List, Dict, Iterable

from .indexers import (
    fetch_blogs_first_page,
    fetch_news_releases_first_page,
    fetch_opeds_first_page,  # NOTE: name is "opeds", not "op_eds"
    fetch_studies_first_page,
)

from .details.blogs_details import fetch_blog_detail
from .models import ListingItem, DetailRecord, normalize_authors
from .storage import write_index_jsonl, write_details_jsonl


VERSION = "0.1.0"
DEFAULT_TYPES = ["blogs", "news_releases", "op_eds", "studies"]


def _print_header(types: List[str], first_page: bool) -> None:
    print(f"CEI6 v{VERSION}")
    print(f"Types (requested): {', '.join(types)}")
    print(f"Mode: {'first-page' if first_page else '(not set)'}")


def _format_item(idx: int, it: ListingItem) -> str:
    date_str = it.date_published.isoformat(sep=" ") if it.date_published else ""
    issue_str = f" • {it.issue}" if it.issue else ""
    authors = normalize_authors(it.authors or [])
    byline = f" • By {', '.join(authors)}" if authors else ""
    return f"{idx:02d}. {it.title} | {it.url} | {date_str}{issue_str}{byline}"


# Map of content_type -> callable that fetches the first page
FETCHERS: Dict[str, callable] = {
    "blogs": fetch_blogs_first_page,
    "news_releases": fetch_news_releases_first_page,
    "op_eds": fetch_opeds_first_page,  # keep the key "op_eds" for CLI, but function is fetch_opeds_first_page
    "studies": fetch_studies_first_page,
}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cei6",
        description="CEI Archive Engine 6 – fresh start (indexers per type).",
    )
    parser.add_argument(
        "--types",
        nargs="+",
        default=DEFAULT_TYPES,
        help="One or more source types to fetch (default: blogs news_releases op_eds studies).",
    )
    parser.add_argument(
        "--first-page",
        dest="first_page",
        action="store_true",
        help="Fetch only the first listing page for each type.",
    )
    parser.add_argument(
        "--write-jsonl",
        dest="write_jsonl",
        action="store_true",
        help="Append listings to outputs/index/{type}.jsonl (dedup by URL).",
    )
    parser.add_argument(
        "--details",
        dest="details",
        action="store_true",
        help="Fetch & write detail pages (blogs only in Stage R4).",
    )
    parser.add_argument(
        "--max-details",
        type=int,
        default=5,
        help="Cap the number of blog detail pages parsed/written in this run.",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Reduce console output.")

    args = parser.parse_args(argv)

    # Normalize type names from CLI
    types = [t.strip() for t in args.types]
    _print_header(types, args.first_page)

    # -------- First-page listings --------
    items_by_type: Dict[str, List[ListingItem]] = {}

    if args.first_page:
        for t in types:
            fetcher = FETCHERS.get(t)
            if not fetcher:
                print(f"[warn] unsupported type: {t}")
                continue

            items: List[ListingItem] = fetcher()
            items_by_type[t] = items

            print(f"== {t} — {len(items)} item(s) ==")
            for i, it in enumerate(items, start=1):
                print(_format_item(i, it))

            if args["write_jsonl"] if isinstance(args, dict) else args.write_jsonl:
                try:
                    wrote = write_index_jsonl(t, items)  # content_type FIRST, items SECOND
                    total_new += wrote
                    print(f"[wrote] {t}: {wrote} new line(s) to outputs/index/{t}.jsonl")
                except Exception as e:
                    print(f"[error] write_jsonl failed for {t}: {e}")

    # -------- Details (Stage R4: blogs only) --------
    if args.details:
        # Ensure we have blog listings to drive which details to fetch.
        blog_items = items_by_type.get("blogs")
        if blog_items is None:
            # If user didn’t pass --first-page, we still fetch the first page of blogs
            blog_items = FETCHERS["blogs"]()
            # print a small header so it’s clear why we fetched:
            print("== blogs — (fetched for details) ==")
            for i, it in enumerate(blog_items, start=1):
                print(_format_item(i, it))

        # Cap to max-details
        to_process = blog_items[: args.max_details] if args.max_details else blog_items

        detail_records: List[DetailRecord] = []
        for it in to_process:
            try:
                d = fetch_blog_detail(it.url)  # returns dict with paragraphs, pdf_links, maybe title
            except Exception as ex:
                print(f"[warn] fetch detail failed (blogs): {it.url} :: {ex}")
                continue

            detail_records.append(
                DetailRecord(
                    content_type="blogs",
                    url=it.url,
                    title=d.get("title") or it.title,
                    date_published=it.date_published,
                    issue=it.issue,
                    authors=tuple(it.authors),
                    pdf_links=tuple(d.get("pdf_links", [])),
                    paragraphs=tuple(d.get("paragraphs", [])),
                )
            )

        if detail_records:
            written = write_details_jsonl(detail_records, "blogs")
            print(f"[details] blogs: wrote {written} line(s) to outputs/details/blogs.jsonl")
        else:
            print("[details] nothing to write for blogs.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
