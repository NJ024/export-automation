"""
main.py — orchestrates search -> extract -> validate -> classify -> send -> report,
per the spec's Section 3 Workflow Narrative.

Usage:
    python main.py search              # run all enabled source adapters, extract, validate, save to buyers.csv
    python main.py classify            # AI-classify buyers.csv into business/individual segments
    python main.py send --subject "..." --body-file body.txt --audience business [--live]
    python main.py report              # print + save run summary

    python main.py search --sources google,website
"""

import argparse

from config import ENABLED_SOURCES
from search import google_search, website_search, directory_search, linkedin_search, facebook_search
from extraction.data_extractor import extract
from validation.email_validator import validate_batch
from classification.ai_classifier import classify_emails
from activity_logging.activity_logger import (
    append_buyers_bulk, read_buyers, write_classified_emails, read_emails_for_audience,
)
from outreach.gmail_sender import send_campaign
from reports.report_generator import generate_report

SOURCE_ADAPTERS = {
    "google": google_search.search,
    "website": website_search.search,
    "directory": directory_search.search,
    "manual": lambda: linkedin_search.search() + facebook_search.search(),
}


def cmd_search(sources):
    sources = sources or ENABLED_SOURCES
    all_raw = []
    for source in sources:
        source = source.strip()
        adapter = SOURCE_ADAPTERS.get(source)
        if not adapter:
            print(f"  Unknown source '{source}', skipping.")
            continue
        print(f"Querying source: {source}")
        try:
            raw = adapter()
            print(f"  -> {len(raw)} raw results")
            all_raw.extend(raw)
        except Exception as e:
            # Per spec: "Source adapter fails gracefully; run proceeds with remaining sources"
            print(f"  Source '{source}' failed ({e}), continuing with remaining sources.")

    records = extract(all_raw)
    print(f"\nExtracted {len(records)} candidate buyer records.")

    valid, invalid, flagged = validate_batch(records)
    print(f"Validation: {len(valid)} valid, {len(invalid)} invalid, {len(flagged)} flagged for review")

    added, skipped = append_buyers_bulk(valid)
    print(f"Saved to buyers.csv: {added} new, {skipped} duplicates skipped")


def cmd_classify():
    buyers = read_buyers()
    emails = [b["email"] for b in buyers if b.get("email")]
    if not emails:
        print("No buyers found in buyers.csv. Run `python main.py search` first.")
        return

    labels = classify_emails(emails)
    business = [e for e, label in labels.items() if label == "business"]
    individual = [e for e, label in labels.items() if label == "individual"]
    write_classified_emails(business, individual)
    print(f"Classified {len(labels)} emails -> {len(business)} business, {len(individual)} individual")


def cmd_send(args):
    emails = read_emails_for_audience(args.audience)
    if not emails:
        print(f"No emails found for audience '{args.audience}'. Run `classify` first.")
        return

    with open(args.body_file, encoding="utf-8") as f:
        body_template = f.read()

    records = [{"email": e} for e in emails]

    dry_run = not args.live
    if not dry_run:
        print(f"About to send LIVE to {len(records)} recipients.")
        confirm = input("Type SEND to confirm, anything else to cancel: ")
        if confirm.strip().upper() != "SEND":
            print("Cancelled. No emails sent.")
            return

    report_data = send_campaign(records, args.subject, body_template, dry_run=dry_run)
    print(f"\nDone. Sent: {report_data['success_count']}, "
          f"Failed: {report_data['failed_count']}, Skipped (dup): {report_data['skipped_count']}")


def main():
    parser = argparse.ArgumentParser(description="EXPORT Automation System")
    sub = parser.add_subparsers(dest="command")

    p_search = sub.add_parser("search")
    p_search.add_argument("--sources", help="comma-separated list, e.g. google,website")

    sub.add_parser("classify")

    p_send = sub.add_parser("send")
    p_send.add_argument("--subject", required=True)
    p_send.add_argument("--body-file", required=True, help="path to a text file with the email body")
    p_send.add_argument("--audience", choices=["business", "individual", "all"], default="all")
    p_send.add_argument("--live", action="store_true", help="actually send (default is dry run)")

    sub.add_parser("report")

    args = parser.parse_args()

    if args.command == "search":
        cmd_search(args.sources.split(",") if args.sources else None)
    elif args.command == "classify":
        cmd_classify()
    elif args.command == "send":
        cmd_send(args)
    elif args.command == "report":
        generate_report()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
