<div align="center">

# 🌍 EXPORT Automation System

**API 3 — AI-Powered Export Outreach Automation**

*Discover international buyers → validate & classify contacts → send personalized outreach via Gmail → track & report — end to end.*

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/web%20UI-Flask-black)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

[Overview](#-overview) •
[Features](#-features) •
[Architecture](#-architecture) •
[Setup](#-setup) •
[Usage](#-usage) •
[Screenshots](#-screenshots) •
[Deviations](#-deviations-from-the-original-spec) •
[Limitations](#-known-limitations)

</div>

---

## 📋 Overview

This project implements a two-stage export marketing pipeline:

1. **Buyer Discovery** — searches multiple channels for prospective international buyers and extracts structured contact records into a normalized schema.
2. **Automated Outreach** — validates emails, classifies contacts (business vs. individual) using AI, attaches a company presentation, and dispatches personalized emails via Gmail — with duplicate prevention and full audit logging.

Built as a lightweight, script-driven pipeline with **both a CLI and a browser-based web UI**, so it can be run by developers and non-developers alike.

<details>
<summary><strong>📦 Why this exists / who it's for</strong></summary>
<br>

Built for a small export operation that needs to find and reach international buyers without manual, one-by-one prospecting. Every stage — discovery, validation, classification, sending, logging — is its own independently testable module, so pieces can be swapped out (a different search source, a different mail provider) without touching the rest of the pipeline.

</details>

---

## ✨ Features

| Module | What it does |
|---|---|
| 🔍 **Buyer Search** | Google Custom Search, website contact-page scanning, business directories, plus a manual-import path for LinkedIn/Facebook leads |
| 🧹 **Data Extraction** | Normalizes raw results into a consistent buyer schema (name, company, email, website, country, source) |
| ✅ **Email Validation** | Regex format check + DNS MX-record verification — filters junk before it reaches the send queue |
| 🤖 **AI Classification** | Gemini-powered business/individual segmentation, with a free heuristic fallback if no API key is set |
| 📧 **Gmail Outreach** | SMTP + App Password auth, presentation attachment, auto-reconnect on drop, configurable send delay |
| 🔁 **Duplicate Prevention** | Cross-checks every send against historical logs — no buyer gets emailed twice, ever |
| 📊 **Reporting** | Console summary + CSV export: total sent, success/failure counts, success rate |
| 🖥️ **Web UI** | Flask app — run the whole pipeline from a browser: upload, classify, send, report, settings |

---

## 🏗 Architecture

```
                 ┌─────────────────┐
                 │  Buyer Discovery │   Google · Website · Directory · Manual (LinkedIn/FB)
                 └────────┬─────────┘
                          ▼
                 ┌─────────────────┐
                 │  Data Extraction │   raw text/HTML → normalized buyer record
                 └────────┬─────────┘
                          ▼
                 ┌─────────────────┐
                 │ Email Validation │   regex + MX record check
                 └────────┬─────────┘
                          ▼
                 ┌─────────────────┐
                 │ AI Classification│   Gemini → business / individual
                 └────────┬─────────┘
                          ▼
                 ┌─────────────────┐
                 │  Gmail Outreach  │   compose → attach → send → log
                 └────────┬─────────┘
                          ▼
                 ┌─────────────────┐
                 │    Reporting     │   console + CSV summary
                 └─────────────────┘
```

<details>
<summary><strong>📁 Folder structure</strong></summary>
<br>

```
export-automation/
├── main.py                  # CLI entry point
├── app.py                   # Flask web UI
├── config.py                # Central configuration (.env-driven)
│
├── search/                  # Source adapters
│   ├── google_search.py
│   ├── website_search.py
│   ├── directory_search.py
│   ├── linkedin_search.py       # manual-import adapter (see Deviations below)
│   ├── facebook_search.py       # manual-import adapter (see Deviations below)
│   └── manual_research_helper.py
│
├── extraction/
│   └── data_extractor.py    # raw results → normalized buyer schema
│
├── validation/
│   └── email_validator.py   # format + MX record checks
│
├── classification/
│   └── ai_classifier.py     # Gemini-based business/individual classifier
│
├── outreach/
│   ├── gmail_auth.py        # SMTP App Password auth
│   ├── gmail_sender.py      # compose, send, retry, rate-limit
│   └── attachment_handler.py
│
├── activity_logging/        # renamed from spec's "logging/" — see Deviations
│   └── activity_logger.py   # single source of truth for all CSV I/O
│
├── reports/
│   └── report_generator.py
│
├── assets/
│   └── company_presentation.pdf   # (add your own — see Setup)
│
├── data/
│   ├── buyers.csv            # discovered leads (generated)
│   ├── sent_log.csv          # outreach history (generated)
│   ├── seed_websites.csv     # your research input for the website adapter
│   ├── seed_directories.csv  # your research input for the directory adapter
│   └── manual_leads.csv      # your LinkedIn/Facebook research input
│
├── .env.example
└── requirements.txt
```

</details>

---

## ⚙️ Setup

<details open>
<summary><strong>1. Install dependencies</strong></summary>
<br>

```bash
pip install -r requirements.txt
cp .env.example .env
```

</details>

<details>
<summary><strong>2. Configure Gmail (required to send)</strong></summary>
<br>

1. Enable **2-Step Verification** on the sending Gmail account.
2. Go to **Google Account → Security → App Passwords**.
3. Generate a password for "Mail" and paste it into `.env` as `GMAIL_APP_PASSWORD`.
4. Set `GMAIL_EMAIL` to the sending address.

</details>

<details>
<summary><strong>3. Configure optional integrations</strong></summary>
<br>

| Service | Needed for | Get a key |
|---|---|---|
| Google Custom Search | the `google` discovery source | [developers.google.com/custom-search](https://developers.google.com/custom-search/v1/introduction) |
| Gemini API | AI-based email classification | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |

Without these, the pipeline still runs fully — `google` source skips gracefully, and classification falls back to a free heuristic.

</details>

<details>
<summary><strong>4. Add your presentation file</strong></summary>
<br>

Place your company presentation at `assets/company_presentation.pdf` (this gets attached to every outreach email).

</details>

---

## 🚀 Usage

### CLI

```bash
# 1. Discover buyers (writes to data/buyers.csv, dedupes automatically)
python main.py search --sources manual

# 2. Classify into business / individual segments
python main.py classify

# 3. Draft + send — dry run by default, add --live to actually send
python main.py send --subject "Subject here" --body-file data/sample_email_body.txt --audience business
python main.py send --subject "Subject here" --body-file data/sample_email_body.txt --audience business --live

# 4. Report
python main.py report
```

### Web UI

```bash
python app.py
```

Open **http://127.0.0.1:5000** — dashboard, upload, classify, send, report, and settings, all from the browser.

---

## 🖼 Screenshots

<div align="center">

| CLI pipeline run | Web dashboard |
|---|---|
| ![CLI run](https://github.com/NJ024/export-automation/blob/main/01_cli_pipeline_run.png) | ![Dashboard](https://github.com/NJ024/export-automation/blob/main/02_web_dashboard.png) |

| Send campaign page | Report page |
|---|---|
| ![Send page](https://github.com/NJ024/export-automation/blob/main/03_web_send_page.png) | ![Report page](https://github.com/NJ024/export-automation/blob/main/04_web_report_page.png) |

</div>

---

## 🔀 Deviations from the original spec

<details>
<summary><strong>1. <code>logging/</code> → <code>activity_logging/</code></strong></summary>
<br>

The original spec names this folder `logging`. That collides with Python's own built-in `logging` module — if a folder named `logging` sits at the project root, `import logging` anywhere (including *inside* third-party libraries) silently resolves to this folder instead of the standard library, breaking those libraries in confusing ways. Renamed to avoid that; file responsibilities are unchanged.

</details>

<details>
<summary><strong>2. LinkedIn & Facebook adapters don't scrape</strong></summary>
<br>

Both platforms' Terms of Service prohibit automated scraping, and both actively detect and ban accounts/IPs that attempt it. Instead, `search/linkedin_search.py` and `search/facebook_search.py` read leads a human already researched from `data/manual_leads.csv` — preserving the adapter-pattern architecture the spec calls for, without the account-ban risk. `search/manual_research_helper.py` generates ready-to-use Boolean search strings to speed up that manual step.

</details>

<details>
<summary><strong>3. Added a <code>classification/</code> folder</strong></summary>
<br>

The spec's file tree omits a folder for the AI Email Classification Module even though section 5.4 describes it — added here to actually implement what's specified.

</details>

---

## ⚠️ Known limitations

- Country/company fields are inferred from unstructured text and may need manual correction.
- No consent tracking, unsubscribe links, or CAN-SPAM/GDPR compliance layer — needed before any commercial-scale use.
- CSV storage doesn't scale to very large lead lists and has no concurrent-access safety — fine for single-operator use.
- Search-source adapters depend on page structure and are fragile to markup changes.

---

## 📄 License

MIT — see [LICENSE](LICENSE).

<div align="center">

*Built as part of the API 3 — EXPORT Automation System internship project.*

</div>
