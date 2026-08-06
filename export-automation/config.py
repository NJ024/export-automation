"""
config.py — central configuration for the EXPORT Automation System.
Loads all settings from environment variables (.env file).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

# --- Run configuration ---
SEARCH_KEYWORD = os.getenv("SEARCH_KEYWORD", "Singing Bowls")
DAILY_SEND_LIMIT = int(os.getenv("DAILY_SEND_LIMIT", "100"))
SEND_DELAY_SECONDS = float(os.getenv("SEND_DELAY_SECONDS", "5"))
PRESENTATION_PATH = os.getenv("PRESENTATION_PATH", str(BASE_DIR / "assets" / "company_presentation.pdf"))

# --- Gmail (SMTP + App Password) ---
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
MONITOR_CC_EMAIL = os.getenv("MONITOR_CC_EMAIL", "")  # optional; leave blank to disable CC

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT_SSL = 465

# --- Google Custom Search (buyer discovery via Google) ---
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY", "")
GOOGLE_CSE_CX = os.getenv("GOOGLE_CSE_CX", "")

# --- AI Classification (Gemini) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# --- Data file paths ---
DATA_DIR = BASE_DIR / "data"
BUYERS_CSV = DATA_DIR / "buyers.csv"
SENT_LOG_CSV = DATA_DIR / "sent_log.csv"
BUSINESS_EMAILS_CSV = DATA_DIR / "business_emails.csv"
INDIVIDUAL_EMAILS_CSV = DATA_DIR / "individual_emails.csv"
SEED_WEBSITES_CSV = DATA_DIR / "seed_websites.csv"
SEED_DIRECTORIES_CSV = DATA_DIR / "seed_directories.csv"
MANUAL_LEADS_CSV = DATA_DIR / "manual_leads.csv"

# --- Enabled sources for a search run ---
# google      -> Google Custom Search API (needs GOOGLE_CSE_API_KEY + GOOGLE_CSE_CX)
# website     -> fetches public contact/about pages for URLs you supply
# directory   -> fetches directory listing pages for URLs you supply
# manual      -> imports leads you (or a teammate) manually collected from
#                LinkedIn/Facebook into a CSV (see search/linkedin_search.py
#                and search/facebook_search.py for why these aren't automated)
ENABLED_SOURCES = os.getenv("ENABLED_SOURCES", "google,website,directory,manual").split(",")
