"""
reports/report_generator.py — Reporting Module (spec section 8, /report route).

Builds the in-memory report_data structure the spec describes (total,
success_count, failed_count, successful[], failed[]) from sent_log.csv, prints
a summary, and exports a timestamped CSV snapshot. (PDF export is listed as a
possible format in the spec but not implemented here — see README for the
one-line addition needed if you want it, e.g. with fpdf2.)
"""

import csv
from datetime import datetime
from pathlib import Path

from config import DATA_DIR, BUYERS_CSV
from activity_logging.activity_logger import read_sent_log, read_buyers

REPORTS_DIR = DATA_DIR / "reports"


def build_report_data():
    sent_rows = read_sent_log()
    successful = [r["email"] for r in sent_rows if r["status"] == "sent" or r["status"] == "dry_run"]
    failed = [r["email"] for r in sent_rows if r["status"] == "failed"]
    return {
        "total": len(sent_rows),
        "success_count": len(successful),
        "failed_count": len(failed),
        "successful": successful,
        "failed": failed,
    }


def generate_report():
    report_data = build_report_data()
    buyers = read_buyers()

    print("=" * 50)
    print(f"EXPORT AUTOMATION — RUN SUMMARY ({datetime.now().date()})")
    print("=" * 50)
    print(f"Buyers discovered (total in {BUYERS_CSV.name}): {len(buyers)}")
    print(f"Outreach attempts logged:    {report_data['total']}")
    print(f"  Successful:                {report_data['success_count']}")
    print(f"  Failed:                    {report_data['failed_count']}")
    if report_data["total"]:
        rate = report_data["success_count"] / report_data["total"] * 100
        print(f"  Success rate:              {rate:.1f}%")
    print("=" * 50)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["buyers_discovered", len(buyers)])
        writer.writerow(["outreach_attempts", report_data["total"]])
        writer.writerow(["successful", report_data["success_count"]])
        writer.writerow(["failed", report_data["failed_count"]])
    print(f"Saved CSV snapshot to {out_path}")
    return report_data, out_path


if __name__ == "__main__":
    generate_report()
