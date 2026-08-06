"""
activity_logging/activity_logger.py — Logging Module (spec section 5.7).

NOTE ON NAMING: the spec's file tree calls this folder "logging/". That name
collides with Python's own built-in `logging` module — if this folder sat at
the top level of the project, `import logging` anywhere (including inside
requests, google-generativeai, or any other library) would resolve to THIS
folder instead of the standard library, silently breaking those libraries.
It's renamed to `activity_logging/` to avoid that; everything else matches
the spec's file responsibilities exactly (buyers.csv / sent_log.csv, single
point of truth for all CSV I/O).
"""

import csv
from datetime import datetime
from pathlib import Path

from config import BUYERS_CSV, SENT_LOG_CSV, BUSINESS_EMAILS_CSV, INDIVIDUAL_EMAILS_CSV

BUYER_FIELDS = ["buyer_name", "company_name", "email", "website", "country", "source_platform", "discovered_date"]
SENT_LOG_FIELDS = ["email", "status", "timestamp"]


def _ensure_csv(path, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=fields).writeheader()


def _read_all_rows(path):
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_known_emails():
    """All emails already in buyers.csv, lowercased, for duplicate checks at discovery time."""
    return {row["email"].strip().lower() for row in _read_all_rows(BUYERS_CSV) if row.get("email")}


def append_buyer(record):
    """Appends a buyer record to buyers.csv, skipping if the email is already present
    (buyers.csv treats email_address as the primary key, per spec section 7.1)."""
    _ensure_csv(BUYERS_CSV, BUYER_FIELDS)
    known = get_known_emails()
    email = record.get("email", "").strip()
    if not email or email.lower() in known:
        return False

    with open(BUYERS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=BUYER_FIELDS)
        writer.writerow({
            "buyer_name": record.get("buyer_name", ""),
            "company_name": record.get("company_name", ""),
            "email": email,
            "website": record.get("website", ""),
            "country": record.get("country", ""),
            "source_platform": record.get("source_platform", ""),
            "discovered_date": datetime.now().isoformat(timespec="seconds"),
        })
    return True


def append_buyers_bulk(records):
    added, skipped = 0, 0
    for r in records:
        if append_buyer(r):
            added += 1
        else:
            skipped += 1
    return added, skipped


def get_contacted_emails():
    """All emails with a 'sent' or 'dry_run' status in sent_log.csv, for duplicate prevention."""
    rows = _read_all_rows(SENT_LOG_CSV)
    return {r["email"].strip().lower() for r in rows if r.get("status") in ("sent", "dry_run")}


def is_already_contacted(email):
    return email.strip().lower() in get_contacted_emails()


def append_sent_log(email, status):
    """status: 'sent' | 'failed' | 'dry_run'"""
    _ensure_csv(SENT_LOG_CSV, SENT_LOG_FIELDS)
    with open(SENT_LOG_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SENT_LOG_FIELDS)
        writer.writerow({
            "email": email,
            "status": status,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })


def write_classified_emails(business_emails, individual_emails):
    _ensure_csv(BUSINESS_EMAILS_CSV, ["email"])
    _ensure_csv(INDIVIDUAL_EMAILS_CSV, ["email"])
    with open(BUSINESS_EMAILS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["email"])
        writer.writeheader()
        for e in business_emails:
            writer.writerow({"email": e})
    with open(INDIVIDUAL_EMAILS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["email"])
        writer.writeheader()
        for e in individual_emails:
            writer.writerow({"email": e})


def read_buyers():
    return _read_all_rows(BUYERS_CSV)


def read_sent_log():
    return _read_all_rows(SENT_LOG_CSV)


def read_emails_for_audience(audience):
    """audience: 'business' | 'individual' | 'all' -> list of email strings, de-duplicated."""
    emails = []
    if audience in ("business", "all"):
        emails += [r["email"] for r in _read_all_rows(BUSINESS_EMAILS_CSV) if r.get("email")]
    if audience in ("individual", "all"):
        emails += [r["email"] for r in _read_all_rows(INDIVIDUAL_EMAILS_CSV) if r.get("email")]
    return list(dict.fromkeys(emails))
