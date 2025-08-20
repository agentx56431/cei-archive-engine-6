# cei6/cli.py
from __future__ import annotations

import argparse
from typing import Dict, List, Callable

from cei6.indexers import blogs_indexer, news_releases_indexer, op_eds_indexer, studies_indexer
from cei6.models import ListingItem

FETCHERS: Dict[str, Callable[[], List[ListingItem]]] = {
    "blogs": blogs_indexer.fetch_first_page,
    "news_releases": news_releases_indexer.fetch_first_page,
    "op_eds": op_eds_indexer.fetch_first_page,
    "studies": studies_indexer.fetch_first_page,
}


def main(argv: List[str] | None = None) -> int:
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
    args = parser.parse_args(argv)

    print("CEI6 v0.1.0")
    print(f"Types (requested): {', '.join(args.types)}")
    mode = "first-page" if args.first_page else "(no fetch yet in this mode)"
    print(f"Mode: {mode}")

    if not args.first_page:
        print("Note: Use --first-page to run the Stage R2 indexers.")
        return 0

    for t in args.types:
        fetch = FETCHERS.get(t)
        if not fetch:
            print(f"[warn] unsupported type: {t}")
            continue
        items = fetch()
        print(f"== {t} — {len(items)} item(s) ==")
        for i, it in enumerate(items, 1):
            # Use the new pretty line that includes authors when present
            print(f"{i:02d}. {it.pretty_line()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
