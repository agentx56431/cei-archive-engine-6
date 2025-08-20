import argparse
from typing import Dict, Iterable, List

from .models import ListingItem
from .indexers import (
    fetch_blogs_first_page,
    fetch_news_releases_first_page,
    fetch_opeds_first_page,
    fetch_studies_first_page,
)
from .storage import write_index_jsonl
from .details import fetch_blog_details_batch


def _print_items(label: str, items: Iterable[ListingItem]) -> None:
    items = list(items)
    print(f"== {label} — {len(items)} item(s) ==")
    for i, it in enumerate(items, 1):
        author_str = ""
        if it.authors:
            author_str = " • By " + ", ".join(it.authors)
        issue_str = f" • {it.issue}" if it.issue else ""
        print(f"{i:02d}. {it.title} | {it.url} | {it.date_published}{issue_str}{author_str}")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="cei6",
        description="CEI Archive Engine 6 – fresh start (indexers per type).",
    )
    parser.add_argument(
        "--types",
        nargs="+",
        default=["blogs", "news_releases", "op_eds", "studies"],
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
    parser.add_argument(
        "--details",
        action="store_true",
        help="Fetch detail pages (currently blogs only) using the first-page results.",
    )
    parser.add_argument(
        "--max-details",
        type=int,
        default=0,
        help="Cap number of detail pages to fetch (blogs only for now). 0 = no cap.",
    )

    args = parser.parse_args()

    types = args.types
    print("CEI6 v0.1.0")
    print(f"Types (requested): {', '.join(types)}")
    print("Mode: first-page" if args.first_page else "Mode: (listing fetch not specified)")

    # Map for indexers
    indexers: Dict[str, callable] = {
        "blogs": fetch_blogs_first_page,
        "news_releases": fetch_news_releases_first_page,
        "op_eds": fetch_opeds_first_page,
        "studies": fetch_studies_first_page,
    }

    listings_by_type: Dict[str, List[ListingItem]] = {}

    if args.first_page:
        for t in types:
            fetcher = indexers.get(t)
            if not fetcher:
                print(f"[warn] unknown type: {t}")
                continue
            items = fetcher()
            listings_by_type[t] = list(items)
            _print_items(t, listings_by_type[t])

        # write JSONL if requested
        if args.write_jsonl:
            total_new = 0  # <-- IMPORTANT: initialize before using it
            for t in types:
                items = listings_by_type.get(t, [])
                if not items:
                    continue
                try:
                    wrote = write_index_jsonl(t, items)  # content_type first, items second
                    total_new += wrote
                    print(f"[wrote] {t}: {wrote} new line(s) to outputs/index/{t}.jsonl")
                except Exception as e:
                    # Never reference total_new here; just show the error
                    print(f"[error] write_jsonl failed for {t}: {e}")
            print(f"[summary] total new lines written: {total_new}")

        # details (blogs only for now)
        if args.details:
            blogs = listings_by_type.get("blogs", [])
            if not blogs:
                print("[details] no blogs to fetch.")
                return 0
            cap = args.max_details if args.max_details and args.max_details > 0 else None
            try:
                wrote = fetch_blog_details_batch(blogs, cap=cap)
                if wrote:
                    print(f"[details] wrote {wrote} blog detail record(s).")
                else:
                    print("[details] nothing to write for blogs.")
            except Exception as e:
                print(f"[error] details failed (blogs): {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
