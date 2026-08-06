"""
extraction/data_extractor.py — Data Extraction Module (spec section 5.2).

Parses raw content returned by the search adapters into the normalized buyer
schema, implementing Algorithm 12.1 (Email Extraction & Validation) from the
spec: regex-extract candidate emails, discard obvious junk (image-extension
"emails" from filenames, absurdly long domains), and normalize into records.

Buyer schema fields: buyer_name, company_name, email, website, country, source_platform
"""

import re

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp")
MAX_DOMAIN_LENGTH = 50

# Very light country inference from common TLD patterns — best-effort only,
# per the spec's "Known Limitations": country is inferred from unstructured
# text/URLs and may need manual correction.
TLD_COUNTRY_HINTS = {
    ".de": "Germany", ".fr": "France", ".uk": "United Kingdom", ".in": "India",
    ".ae": "UAE", ".ca": "Canada", ".au": "Australia", ".jp": "Japan",
    ".it": "Italy", ".es": "Spain", ".nl": "Netherlands", ".br": "Brazil",
}


def _is_junk_candidate(email):
    domain = email.split("@")[-1].lower()
    if email.lower().endswith(IMAGE_EXTENSIONS):
        return True
    if len(domain) > MAX_DOMAIN_LENGTH:
        return True
    return False


def _infer_country(url, raw_text):
    haystack = (url or "") + " " + (raw_text or "")
    for tld, country in TLD_COUNTRY_HINTS.items():
        if tld in haystack.lower():
            return country
    return ""


def _infer_company_name(url):
    """Best-effort company name guess from a domain, e.g. abcimports.com -> Abcimports."""
    if not url:
        return ""
    try:
        domain = url.split("//")[-1].split("/")[0]
        domain = domain.replace("www.", "")
        name = domain.split(".")[0]
        return name.replace("-", " ").title()
    except Exception:
        return ""


def extract(raw_results):
    """
    raw_results: list of dicts, each either:
        - {"url", "raw_text", "source_platform"}  (needs email extraction), or
        - an already-normalized manual lead row (has "email" key directly)

    Returns: list of normalized buyer records (dicts).
    """
    records = []
    seen_in_batch = set()

    for item in raw_results:
        # Already-normalized manual leads (from linkedin_search / facebook_search)
        if "email" in item and item.get("email"):
            email = item["email"].strip()
            if email.lower() in seen_in_batch or _is_junk_candidate(email):
                continue
            seen_in_batch.add(email.lower())
            records.append({
                "buyer_name": item.get("buyer_name", "") or item.get("contact_name", ""),
                "company_name": item.get("company_name", "") or item.get("company", ""),
                "email": email,
                "website": item.get("website", ""),
                "country": item.get("country", ""),
                "source_platform": item.get("source_platform", "Manual"),
            })
            continue

        raw_text = item.get("raw_text", "")
        url = item.get("url", "")
        source_platform = item.get("source_platform", "Other")

        candidates = EMAIL_PATTERN.findall(raw_text)
        for email in candidates:
            email = email.strip().rstrip(".,;:")
            key = email.lower()
            if key in seen_in_batch or _is_junk_candidate(email):
                continue
            seen_in_batch.add(key)
            records.append({
                "buyer_name": "",
                "company_name": _infer_company_name(url),
                "email": email,
                "website": url,
                "country": _infer_country(url, raw_text),
                "source_platform": source_platform,
            })

    return records


if __name__ == "__main__":
    sample = [{
        "url": "https://abcimports.de/contact",
        "raw_text": "Contact us at sales@abcimports.de or see our logo.png file",
        "source_platform": "Website",
    }]
    for r in extract(sample):
        print(r)
