# EXPORT Automation System (API 3)

Implementation of the "API 3 — EXPORT Automation System" spec: discovers buyers,
validates and classifies their emails, sends personalized outreach with a
presentation attachment via Gmail, and logs everything for reporting — with a
CLI and a small web UI, matching the spec's module breakdown.

## Two deviations from the literal spec (and why)

1. **`logging/` → `activity_logging/`.** The spec names this folder `logging`,
   which collides with Python's own built-in `logging` module. If a folder
   named `logging` sits at the project root, `import logging` anywhere —
   including *inside* libraries like `requests` or `google-generativeai` —
   silently resolves to this folder instead of the standard library, breaking
   those libraries in confusing ways. Renamed to avoid that; the file
   responsibilities (single point of truth for `buyers.csv` / `sent_log.csv`)
   are unchanged.

2. **LinkedIn and Facebook adapters don't scrape.** Both platforms' Terms of
   Service prohibit automated scraping and both actively detect and ban
   accounts/IPs that try — a real risk to whatever account is used. Instead,
   `search/linkedin_search.py` and `search/facebook_search.py` read
   leads a human already researched from `data/manual_leads.csv`. This keeps
   the adapter-pattern architecture the spec calls for (LinkedIn/Facebook are
   still lead channels feeding the same pipeline) without the ban risk.
   `search/manual_research_helper.py` generates ready-to-use Boolean search
   strings to make that manual step faster.

   A `classification/` folder was also added (spec section 5.4 describes an
   AI Classification Module but the file tree omits a folder for it).

Everything else — file names, module responsibilities, CSV schema, Gmail
App-Password auth, the algorithms in section 12 — matches the spec directly.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- **Gmail**: enable 2-Step Verification on the sending account, then
  Google Account → Security → App Passwords → generate one for "Mail" →
  paste the 16-character password into `GMAIL_APP_PASSWORD`.
- **Google Custom Search** (optional, for the `google` source): get a free
  API key + Search Engine ID at https://developers.google.com/custom-search/v1/introduction
- **Gemini** (optional, for AI classification): get a key from
  https://aistudio.google.com/app/apikey — without one, classification falls
  back to a free heuristic (free-mail domains = individual, else = business).

Place your company presentation at `assets/company_presentation.pdf`.

## Running it — CLI

```bash
# 1. Discover buyers (writes to data/buyers.csv, dedupes automatically)
python main.py search --sources manual        # or: google,website,directory,manual

# 2. Classify into business / individual segments
python main.py classify

# 3. Draft + send (dry run by default — nothing sends without --live)
python main.py send --subject "Subject here" --body-file data/sample_email_body.txt --audience business
python main.py send --subject "Subject here" --body-file data/sample_email_body.txt --audience business --live

# 4. Report
python main.py report
```

For `google`/`website`/`directory` sources, fill in `data/seed_websites.csv`
and `data/seed_directories.csv` first. For LinkedIn/Facebook leads, research
manually (see `search/manual_research_helper.py` for search strings) and add
rows to `data/manual_leads.csv`.

## Running it — Web UI

```bash
python app.py
```

Open http://127.0.0.1:5000 — routes match the spec: `/` (dashboard),
`/upload` (import CSV), `/classify`, `/send`, `/report`, `/download-report`,
`/settings`.

## Project structure

```
export-automation/
├── main.py, config.py, app.py
├── search/            google, website, directory, linkedin, facebook adapters
├── extraction/        raw text -> normalized buyer records (Algorithm 12.1)
├── validation/        email format + MX record checks
├── classification/    Gemini-based business/individual classification (added, see above)
├── outreach/          Gmail auth, attachment handling, send loop (Algorithm 12.3)
├── activity_logging/  CSV read/write, duplicate prevention (renamed, see above)
├── reports/           run summary + CSV export
├── assets/            company_presentation.pdf goes here
└── data/              buyers.csv, sent_log.csv, seed lists, manual leads
```

## Known limitations (carried over from the spec)

- Country/company fields are inferred from unstructured text and may need
  manual correction.
- No consent tracking, unsubscribe links, or CAN-SPAM/GDPR compliance layer —
  the spec flags this as needed before any commercial-scale use.
- CSV storage doesn't scale to very large lists and has no concurrent-access
  safety — fine for single-operator use, per the spec.

---

## How to submit via Google Drive

1. **Zip the project folder:**
   ```bash
   cd export-automation
   zip -r ../export-automation.zip . -x "*.env" "*__pycache__*" "data/reports/*"
   ```
   (Excluding `.env` matters — never upload your real Gmail App Password or
   API keys. Leave `.env.example` in the zip so whoever reviews it knows what
   to configure.)

2. **Upload to Google Drive:**
   - Go to drive.google.com → New → File upload → select `export-automation.zip`.
   - Or create a folder first (New → Folder), open it, and upload the zip
     (or the unzipped project files) into that folder — whichever the
     internship's submission form asks for.

3. **Set sharing permissions:**
   - Right-click the file/folder → Share → under "General access," change
     from "Restricted" to **"Anyone with the link"** → set role to **Viewer**.
   - Click "Copy link."

4. **Paste that link into the submission form** (the same one from your
   earlier onboarding steps, or wherever this task's submission field is).

5. **Double check before submitting:** open the link in an incognito/private
   browser window to confirm it's actually viewable without needing to
   request access — links set to "Restricted" by default are the most common
   reason submissions get marked incomplete.

If the task also wants the screenshots (LinkedIn page + Google Calendar
session) bundled in the same submission, add those images into the same
Drive folder alongside the project zip before copying the share link.
