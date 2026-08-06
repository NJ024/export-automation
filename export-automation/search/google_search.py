"""
search/google_search.py — Google source adapter.

Uses the official Google Custom Search JSON API (not scraping google.com search
result pages, which violates Google's ToS and gets IPs blocked quickly). Needs a
free-tier API key + Custom Search Engine ID:
    https://developers.google.com/custom-search/v1/introduction

If credentials aren't configured, this adapter fails gracefully (per the spec's
error-handling table: "Source adapter fails gracefully; run proceeds with
remaining sources") and returns an empty list rather than raising.
"""

import requests
from config import GOOGLE_CSE_API_KEY, GOOGLE_CSE_CX, SEARCH_KEYWORD

SEARCH_ENDPOINT = "https://www.googleapis.com/customsearch/v1"

# Buyer-intent qualifiers appended to the base keyword to bias results toward
# people/companies who buy or distribute, not just make, the product.
BUYER_INTENT_QUALIFIERS = [
    "importer", "wholesale buyer", "distributor", "retailer contact email",
]


def search(keyword=None, max_results=20):
    """Returns a list of raw result dicts: {url, raw_text, source_platform}."""
    keyword = keyword or SEARCH_KEYWORD

    if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_CX:
        print("  [google_search] Skipped — GOOGLE_CSE_API_KEY / GOOGLE_CSE_CX not set in .env")
        return []

    results = []
    for qualifier in BUYER_INTENT_QUALIFIERS:
        query = f"{keyword} {qualifier}"
        try:
            resp = requests.get(SEARCH_ENDPOINT, params={
                "key": GOOGLE_CSE_API_KEY,
                "cx": GOOGLE_CSE_CX,
                "q": query,
                "num": min(10, max_results),
            }, timeout=10)
            resp.raise_for_status()
            items = resp.json().get("items", [])
        except Exception as e:
            print(f"  [google_search] Query failed for '{query}': {e}")
            continue

        for item in items:
            raw_text = " ".join(filter(None, [item.get("title"), item.get("snippet")]))
            results.append({
                "url": item.get("link", ""),
                "raw_text": raw_text,
                "source_platform": "Google",
            })

        if len(results) >= max_results:
            break

    return results[:max_results]


if __name__ == "__main__":
    for r in search(max_results=5):
        print(r)
