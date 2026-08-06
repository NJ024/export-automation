"""
search/website_search.py — Website source adapter.

Given a list of company website URLs (data/seed_websites.csv — you or a
teammate compile this from research), fetches each site's homepage plus
common contact/about page paths and returns the raw text for extraction.

This only requests pages that are already public and that you've explicitly
listed — it does not crawl the open web or bypass any access controls.
"""

import time
import requests
from bs4 import BeautifulSoup
from config import SEED_WEBSITES_CSV
import csv

COMMON_PATHS = ["", "/contact", "/contact-us", "/about", "/about-us"]
REQUEST_DELAY = 1.0  # be polite between requests to the same or different sites
TIMEOUT = 8
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ExportOutreachBot/1.0)"}


def _fetch(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None


def _load_seed_urls():
    if not SEED_WEBSITES_CSV.exists():
        print(f"  [website_search] No seed file at {SEED_WEBSITES_CSV} — nothing to do.")
        return []
    with open(SEED_WEBSITES_CSV, newline="", encoding="utf-8") as f:
        return [row["website"].strip() for row in csv.DictReader(f) if row.get("website")]


def search(max_results=100):
    """Returns a list of raw result dicts: {url, raw_text, source_platform}."""
    base_urls = _load_seed_urls()
    results = []

    for base_url in base_urls:
        base_url = base_url.rstrip("/")
        for path in COMMON_PATHS:
            full_url = base_url + path
            html = _fetch(full_url)
            time.sleep(REQUEST_DELAY)
            if not html:
                continue
            text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
            results.append({
                "url": full_url,
                "raw_text": text,
                "source_platform": "Website",
            })
            if len(results) >= max_results:
                return results

    return results


if __name__ == "__main__":
    for r in search()[:5]:
        print(r["url"], "->", r["raw_text"][:80])
