# cei6/cli.py
from __future__ import annotations

import argparse
from typing import List, Iterable, Dict

from .indexers.blogs_indexer import fetch_blogs_first_page
from .indexers.news_indexer import fetch_news_releases_first_page
from .indexers.opeds_indexer import fetch_op_eds_first_page
from .indexers.studies_indexer import fetch_studies_first_page
from .models import ListingItem, normalize_authors
from .storage import write_index_jsonl

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

FETCHERS: Dict[str, callable] = {
    "blogs": fetch_blogs_first_page,
    "news_releases": fetch_news_releases_first_page,
    "op_eds": fetch_op_eds_first_page,
    "studies": fetch_studies_first_page,
}

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cei6",
        description="CEI Archive Engine 6 – fresh start (indexers per type)."
    )
    parser.add_argument(
        "--types",
        nargs="+",
        default=DEFAULT_TYPES,
        help="One or more source types to fetch (default: blogs news_releases op_eds studies).",
    )
    parser.add_argument(
        "--first-page",
        action="store_true",
        help="Fetch only the first listing page for each type.",
    )
    parser.add_argument(
        "--write-jsonl",
        action="store_true",
        help="Append listings to outputs/index/{type}.jsonl (dedup by URL).",
    )

    args = parser.parse_args(argv)
    types = args.types
    first_page = args.first_page

    _print_header(types, first_page)

    if not first_page:
        print("Note: use --first-page to fetch one page of listings.")
        return 0

    total_new = 0

    for t in types:
        fetcher = FETCHERS.get(t)
        if not fetcher:
            print(f"[warn] unknown type: {t}")
            continue

        items: List[ListingItem] = fetcher()

        print(f"== {t} — {len(items)} item(s) ==")
        for i, it in enumerate(items, start=1):
            print(_format_item(i, it))

        if args["write_jsonl"] if isinstance(args, dict) else args.write_jsonl:
            try:
                wrote = write_index_jsonl(t, items)
                total_new += wrote
                print(f"[wrote] {t}: {wrote} new line(s) to outputs/index/{t}.jsonl")
            except Exception as e:
                print(f"[error] write_jsonl failed for {t}: {e}")

    if args["write_jsonl"] if isinstance(args, dict) else args.write_jsonl:
        print(f"[summary] total new lines written: {total_new}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
