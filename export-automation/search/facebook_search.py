"""
search/facebook_search.py — Facebook source adapter.

Same reasoning as search/linkedin_search.py: Facebook's ToS prohibit automated
scraping of pages/groups and it actively detects and blocks bot traffic. This
adapter reads manually-researched leads from data/manual_leads.csv instead of
scraping Facebook directly.

Workflow:
    1. Browse relevant Facebook pages/groups yourself.
    2. Note contact/company info for promising leads.
    3. Add a row to data/manual_leads.csv with source_platform=Facebook.
    4. Run this adapter — it filters manual_leads.csv down to Facebook rows.
"""

import csv
from config import MANUAL_LEADS_CSV


def search(max_results=200):
    """Returns rows from manual_leads.csv tagged source_platform=Facebook."""
    if not MANUAL_LEADS_CSV.exists():
        print(f"  [facebook_search] No manual leads file at {MANUAL_LEADS_CSV} yet.")
        return []

    results = []
    with open(MANUAL_LEADS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("source_platform", "").strip().lower() == "facebook":
                results.append(dict(row))
            if len(results) >= max_results:
                break
    return results


if __name__ == "__main__":
    for r in search():
        print(r)
