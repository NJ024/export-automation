"""
outreach/gmail_sender.py — Gmail Sender Module (spec section 5.5, Algorithm 12.3).

Composes and sends the campaign: reads audience list(s), attaches the
presentation, sends through Gmail SMTP with reconnect-on-drop and a
configurable delay, and returns report_data for the Reporting module.

Defaults to dry_run=True — nothing is actually sent unless explicitly disabled,
matching the "confirm before send" safeguard from the earlier prototype.
"""

import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import GMAIL_EMAIL, MONITOR_CC_EMAIL, SEND_DELAY_SECONDS, DAILY_SEND_LIMIT
from outreach import gmail_auth
from outreach.attachment_handler import attach_presentation, presentation_exists
from activity_logging.activity_logger import append_sent_log, is_already_contacted


def _build_message(to_email, subject, body):
    msg = MIMEMultipart()
    msg["From"] = GMAIL_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    if MONITOR_CC_EMAIL:
        msg["Cc"] = MONITOR_CC_EMAIL
    msg.attach(MIMEText(body, "plain"))
    attach_presentation(msg)  # missing presentation is checked separately before the run starts
    return msg


def _personalize_body(template_body, record):
    return template_body.format(
        buyer_name=record.get("buyer_name") or "there",
        company_name=record.get("company_name") or "your company",
        country=record.get("country") or "your region",
    )


def send_campaign(records, subject, body_template, dry_run=True, skip_duplicates=True):
    """
    records: list of buyer dicts (must have 'email'; buyer_name/company_name optional).
    Returns report_data: {total, success_count, failed_count, skipped_count, successful, failed}
    """
    if not dry_run and not presentation_exists():
        raise RuntimeError(
            "Presentation file not found at PRESENTATION_PATH. "
            "Run halted before any sends were attempted (per spec's error handling)."
        )

    successful, failed, skipped = [], [], []
    smtp = None
    sent_count_today = 0

    if not dry_run:
        smtp = gmail_auth.connect()

    for record in records:
        email = record.get("email", "").strip()
        if not email:
            continue

        if skip_duplicates and is_already_contacted(email):
            skipped.append(email)
            continue

        if sent_count_today >= DAILY_SEND_LIMIT:
            print(f"  [gmail_sender] Daily send limit ({DAILY_SEND_LIMIT}) reached, stopping.")
            break

        personalized_body = _personalize_body(body_template, record)

        if dry_run:
            print(f"[DRY RUN] Would send to {email}: \"{subject}\"")
            successful.append(email)
            append_sent_log(email, "dry_run")
            sent_count_today += 1
            continue

        msg = _build_message(email, subject, personalized_body)
        try:
            try:
                smtp.send_message(msg)
            except smtplib.SMTPServerDisconnected:
                smtp = gmail_auth.reconnect(smtp)
                smtp.send_message(msg)

            successful.append(email)
            append_sent_log(email, "sent")
        except Exception as e:
            print(f"  [gmail_sender] Failed to send to {email}: {e}")
            failed.append(email)
            append_sent_log(email, "failed")

        sent_count_today += 1
        time.sleep(SEND_DELAY_SECONDS)

    if smtp is not None:
        try:
            smtp.quit()
        except Exception:
            pass

    return {
        "total": len(records),
        "success_count": len(successful),
        "failed_count": len(failed),
        "skipped_count": len(skipped),
        "successful": successful,
        "failed": failed,
    }
