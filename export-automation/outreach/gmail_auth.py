"""
outreach/gmail_auth.py — Gmail Auth Handler (spec section 5.5 / 9.1-9.2).

Authenticates via SMTP_SSL using a Gmail App Password (not the primary account
password), per the spec's Gmail Integration section.

Setup required on the sending Gmail account:
    1. Enable 2-Step Verification.
    2. Google Account -> Security -> App Passwords -> generate one for "Mail".
    3. Put the 16-character password in .env as GMAIL_APP_PASSWORD.
"""

import smtplib
from config import GMAIL_EMAIL, GMAIL_APP_PASSWORD, SMTP_HOST, SMTP_PORT_SSL


def connect():
    """Returns an authenticated smtplib.SMTP_SSL connection."""
    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        raise RuntimeError(
            "GMAIL_EMAIL / GMAIL_APP_PASSWORD not set in .env. "
            "See outreach/gmail_auth.py docstring for setup steps."
        )
    smtp = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT_SSL, timeout=15)
    smtp.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
    return smtp


def reconnect(old_smtp=None):
    """Closes a stale connection (if any) and returns a fresh authenticated one."""
    if old_smtp is not None:
        try:
            old_smtp.quit()
        except Exception:
            pass
    return connect()


if __name__ == "__main__":
    smtp = connect()
    print(f"Authenticated successfully as {GMAIL_EMAIL}")
    smtp.quit()
