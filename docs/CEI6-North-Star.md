# CEI Archive Engine 6 — North Star

## Goal
Index and archive CEI content (blogs, news releases, op-eds, studies) into four JSON “databases”, each containing:
- content_type
- url
- title
- date_published
- author(s)
- issue
- outlet (and outlet_url) [op-eds only]
- documents/pdf links (if present)
- content (with paragraph boundaries when possible)

## Design principles
- Separate indexing (list pages) and details (article pages) per content type.
- Keep parsing rules tiny and type-specific.
- Use first-page tests before expanding scope.
- Everything printed should be deterministic and easy to inspect.
- Never ask for authors on detail pages if index already provides them.

## Phases (v1)
1. Scaffold repo + CLI + North Star (this doc).
2. Implement **indexers** for each type (one page).
3. Implement **details** for each type (one article).
4. Add JSON writers for four datasets.
5. Expand to “first page all details”.
6. Add date filters + dedupe.
7. Scale up safely (multiple pages).

## Output
- `data/cei6_blogs.jsonl`
- `data/cei6_news_releases.jsonl`
- `data/cei6_op_eds.jsonl`
- `data/cei6_studies.jsonl`

## CLI (initial)


## Notes
- Keep fetchers robust against pagination noise.
- Use strict URL filters for real posts vs. utility links.
- Log clearly; fail gracefully; prefer partial data over crashes.
- Store this doc in the repo for alignment.


## Notes
- Keep fetchers robust against pagination noise.
- Use strict URL filters for real posts vs. utility links.
- Log clearly; fail gracefully; prefer partial data over crashes.
- Store this doc in the repo for alignment.