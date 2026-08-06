"""
outreach/attachment_handler.py — Presentation Attachment Module (spec section 5.6).

Loads the company presentation from PRESENTATION_PATH and attaches it to an
outbound MIME message with a consistent filename (avoids the "no name"
attachment issue mentioned in the spec).
"""

from pathlib import Path
from email.mime.application import MIMEApplication
from config import PRESENTATION_PATH


def attach_presentation(mime_message):
    """Attaches the configured presentation file to mime_message in place.
    Returns True if attached, False if the file is missing (caller decides
    whether that's fatal — per the spec, a missing presentation halts the run
    before any sends are attempted)."""
    path = Path(PRESENTATION_PATH)
    if not path.exists():
        return False

    with open(path, "rb") as f:
        part = MIMEApplication(f.read(), Name=path.name)
    part["Content-Disposition"] = f'attachment; filename="{path.name}"'
    mime_message.attach(part)
    return True


def presentation_exists():
    return Path(PRESENTATION_PATH).exists()
