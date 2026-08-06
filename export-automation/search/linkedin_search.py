"""
search/linkedin_search.py — LinkedIn source adapter.

IMPORTANT: this does NOT scrape LinkedIn.

LinkedIn's Terms of Service explicitly prohibit automated scraping, and
LinkedIn actively fingerprints and bans accounts/IPs that attempt it —
including the account of whoever's cookies/session the scraper uses. That
risk (a banned account) is a bad trade for a lead-gen script.

Instead, this adapter reads leads that a human already found on LinkedIn and
saved into data/manual_leads.csv (with source_platform=LinkedIn). This keeps
the "adapter" structure the spec calls for — LinkedIn is still a lead
channel that feeds the same normalized pipeline — but the discovery step
itself stays manual and ToS-compliant.

Workflow:
    1. Search LinkedIn yourself (Sales Navigator, or regular search + Boolean
       operators — see leads_research_helper.py for ready-made query strings).
    2. For each promising contact, note name/company/email(if listed)/website/country.
    3. Add a row to data/manual_leads.csv with source_platform=LinkedIn.
    4. Run this adapter — it just filters manual_leads.csv down to LinkedIn rows.
"""

import csv
from config import MANUAL_LEADS_CSV


def search(max_results=200):
    """Returns rows from manual_leads.csv tagged source_platform=LinkedIn,
    already in the normalized buyer schema (so no further extraction needed)."""
    if not MANUAL_LEADS_CSV.exists():
        print(f"  [linkedin_search] No manual leads file at {MANUAL_LEADS_CSV} yet.")
        return []

    results = []
    with open(MANUAL_LEADS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("source_platform", "").strip().lower() == "linkedin":
                results.append(dict(row))
            if len(results) >= max_results:
                break
    return results


if __name__ == "__main__":
    for r in search():
        print(r)
