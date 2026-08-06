"""
app.py — Application Interface / Web Routes (spec section 8).

A minimal Flask UI so the pipeline can be run from a browser instead of the
command line: /, /upload, /classify, /send, /report, /settings, /download-report.

Run with:
    python app.py
Then open http://127.0.0.1:5000
"""

from flask import Flask, request, redirect, url_for, send_file, render_template_string
from pathlib import Path
import csv

from config import GMAIL_EMAIL, SEND_DELAY_SECONDS, DAILY_SEND_LIMIT, BUYERS_CSV
from activity_logging.activity_logger import (
    read_buyers, read_sent_log, append_buyers_bulk, read_emails_for_audience, write_classified_emails,
)
from classification.ai_classifier import classify_emails
from outreach.gmail_sender import send_campaign
from reports.report_generator import build_report_data, generate_report, REPORTS_DIR

app = Flask(__name__)

LAYOUT = """
<!doctype html><html><head><title>Export Automation</title>
<style>
body{font-family:system-ui,sans-serif;max-width:760px;margin:40px auto;color:#222}
nav a{margin-right:16px;text-decoration:none;color:#2563eb}
h1{font-size:1.4rem} table{border-collapse:collapse;width:100%;margin-top:12px}
td,th{border:1px solid #ddd;padding:6px 10px;text-align:left;font-size:0.9rem}
input,select,textarea{width:100%;padding:6px;margin:4px 0 12px;box-sizing:border-box}
button{background:#2563eb;color:#fff;border:none;padding:8px 16px;border-radius:4px;cursor:pointer}
.flash{background:#fef9c3;padding:8px;border-radius:4px;margin-bottom:12px}
</style></head><body>
<nav><a href="/">Home</a><a href="/upload">Upload</a><a href="/classify">Classify</a>
<a href="/send">Send</a><a href="/report">Report</a><a href="/settings">Settings</a></nav>
__CONTENT__
</body></html>
"""


def render(content):
    return render_template_string(LAYOUT.replace("__CONTENT__", content))


@app.route("/")
def home():
    buyers = read_buyers()
    sent = read_sent_log()
    content = f"""
    <h1>Dashboard</h1>
    <p>Buyers discovered: <b>{len(buyers)}</b></p>
    <p>Outreach attempts logged: <b>{len(sent)}</b></p>
    <p>Sending as: <b>{GMAIL_EMAIL or '(not configured — see Settings)'}</b></p>
    """
    return render(content)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    message = ""
    if request.method == "POST":
        file = request.files.get("csv_file")
        if file:
            rows = list(csv.DictReader(file.stream.read().decode("utf-8").splitlines()))
            added, skipped = append_buyers_bulk(rows)
            message = f'<div class="flash">Imported: {added} new, {skipped} duplicates skipped.</div>'

    buyers_path = Path(BUYERS_CSV)
    stats = f"{buyers_path.stat().st_size} bytes, last modified {buyers_path.stat().st_mtime}" \
        if buyers_path.exists() else "not created yet"
    content = f"""
    <h1>Upload Leads</h1>
    {message}
    <p>Upload a CSV with columns: buyer_name, company_name, email, website, country, source_platform</p>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="csv_file" accept=".csv">
        <button type="submit">Import</button>
    </form>
    <p>Current buyers.csv: {stats}</p>
    """
    return render(content)


@app.route("/classify", methods=["GET", "POST"])
def classify():
    message = ""
    if request.method == "POST":
        buyers = read_buyers()
        emails = [b["email"] for b in buyers if b.get("email")]
        labels = classify_emails(emails)
        business = [e for e, l in labels.items() if l == "business"]
        individual = [e for e, l in labels.items() if l == "individual"]
        write_classified_emails(business, individual)
        message = f'<div class="flash">Classified {len(labels)} emails: {len(business)} business, {len(individual)} individual.</div>'

    content = f"""
    <h1>Classify Contacts</h1>
    {message}
    <p>Runs AI classification (Gemini, with heuristic fallback) on all discovered buyers,
    splitting them into business vs. individual segments.</p>
    <form method="post"><button type="submit">Run Classification</button></form>
    """
    return render(content)


@app.route("/send", methods=["GET", "POST"])
def send():
    message = ""
    if request.method == "POST":
        audience = request.form.get("audience", "all")
        subject = request.form.get("subject", "")
        body = request.form.get("body", "")
        live = request.form.get("live") == "on"
        emails = read_emails_for_audience(audience)
        records = [{"email": e} for e in emails]
        report_data = send_campaign(records, subject, body, dry_run=not live)
        mode = "LIVE" if live else "DRY RUN"
        message = (f'<div class="flash">{mode} complete — sent: {report_data["success_count"]}, '
                    f'failed: {report_data["failed_count"]}, skipped (dup): {report_data["skipped_count"]}</div>')

    content = f"""
    <h1>Send Campaign</h1>
    {message}
    <form method="post">
        <label>Subject</label><input name="subject" required>
        <label>Body (use {{buyer_name}}, {{company_name}}, {{country}})</label>
        <textarea name="body" rows="8" required></textarea>
        <label>Audience</label>
        <select name="audience"><option value="all">All</option><option value="business">Business</option>
        <option value="individual">Individual</option></select>
        <label><input type="checkbox" name="live" style="width:auto;display:inline"> Actually send (unchecked = dry run)</label>
        <button type="submit">Launch Campaign</button>
    </form>
    <p>Send delay: {SEND_DELAY_SECONDS}s between emails. Daily limit: {DAILY_SEND_LIMIT}.</p>
    """
    return render(content)


@app.route("/report")
def report():
    report_data = build_report_data()
    rows = "".join(f"<tr><td>{e}</td><td>successful</td></tr>" for e in report_data["successful"][:50])
    content = f"""
    <h1>Campaign Report</h1>
    <p>Total attempts: {report_data['total']} |
       Successful: {report_data['success_count']} |
       Failed: {report_data['failed_count']}</p>
    <p><a href="/download-report">Download CSV</a></p>
    <table><tr><th>Email</th><th>Status</th></tr>{rows}</table>
    """
    return render(content)


@app.route("/download-report")
def download_report():
    _, csv_path = generate_report()
    return send_file(csv_path, as_attachment=True)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    content = f"""
    <h1>Settings</h1>
    <p>Settings are configured via the <code>.env</code> file (not editable from this page,
    to avoid storing credentials through the browser). Current values:</p>
    <table>
        <tr><td>Gmail account</td><td>{GMAIL_EMAIL or '(not set)'}</td></tr>
        <tr><td>Send delay</td><td>{SEND_DELAY_SECONDS}s</td></tr>
        <tr><td>Daily send limit</td><td>{DAILY_SEND_LIMIT}</td></tr>
    </table>
    <p>Edit <code>.env</code> and restart the app to change these.</p>
    """
    return render(content)


if __name__ == "__main__":
    import os
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
