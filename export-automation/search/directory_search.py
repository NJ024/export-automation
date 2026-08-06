"""
search/directory_search.py — Business directory source adapter.

Same pattern as website_search.py: given a list of directory *listing page*
URLs you've already identified (data/seed_directories.csv), fetches each page
and returns raw text for extraction. Directory HTML structure varies a lot
site to site, so this deliberately keeps parsing generic (full-page text)
rather than hard-coding selectors for one specific directory site — adjust
the CSS selector below if you're consistently using one particular directory.
"""

import time
import csv
import requests
from bs4 import BeautifulSoup
from config import SEED_DIRECTORIES_CSV

REQUEST_DELAY = 1.5
TIMEOUT = 8
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ExportOutreachBot/1.0)"}


def _load_seed_urls():
    if not SEED_DIRECTORIES_CSV.exists():
        print(f"  [directory_search] No seed file at {SEED_DIRECTORIES_CSV} — nothing to do.")
        return []
    with open(SEED_DIRECTORIES_CSV, newline="", encoding="utf-8") as f:
        return [row["url"].strip() for row in csv.DictReader(f) if row.get("url")]


def search(max_results=100):
    """Returns a list of raw result dicts: {url, raw_text, source_platform}."""
    urls = _load_seed_urls()
    results = []

    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
        except Exception as e:
            print(f"  [directory_search] Failed to fetch {url}: {e}")
            continue
        finally:
            time.sleep(REQUEST_DELAY)

        text = BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True)
        results.append({
            "url": url,
            "raw_text": text,
            "source_platform": "Directory",
        })
        if len(results) >= max_results:
            break

    return results


if __name__ == "__main__":
    for r in search()[:5]:
        print(r["url"], "->", r["raw_text"][:80])
