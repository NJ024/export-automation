"""
classification/ai_classifier.py — AI Email Classification Module (spec section 5.4).

Note: the spec's folder tree doesn't list a top-level "classification/" folder,
but section 5.4 describes this exact module, so it's added here to actually
implement what's specified.

Uses Google's Gemini API to classify each buyer email as "business" or
"individual" (zero/few-shot classification, per the spec's rationale). If
GEMINI_API_KEY isn't set, falls back to a free heuristic (free-mail providers
like gmail/yahoo/outlook => individual, everything else => business) so the
pipeline still runs end to end without an API key.
"""

from config import GEMINI_API_KEY, GEMINI_MODEL

FREE_MAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com",
    "aol.com", "protonmail.com", "live.com",
}

BATCH_SIZE = 20


def _heuristic_classify(email):
    domain = email.split("@")[-1].lower()
    return "individual" if domain in FREE_MAIL_DOMAINS else "business"


def _gemini_classify_batch(emails):
    """Calls Gemini to classify a batch of emails. Falls back to heuristic per-email on failure."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)

        prompt = (
            "Classify each email address below as exactly one word: "
            "'business' (company/organizational domain) or 'individual' "
            "(personal/free-mail address). Respond with one line per email, "
            "format exactly as 'email,label' with no extra text.\n\n"
            + "\n".join(emails)
        )
        response = model.generate_content(prompt)
        labels = {}
        for line in response.text.strip().splitlines():
            if "," not in line:
                continue
            email, label = line.rsplit(",", 1)
            label = label.strip().lower()
            labels[email.strip()] = label if label in ("business", "individual") else _heuristic_classify(email)

        # Make sure every input email got a label even if Gemini's response was incomplete
        for email in emails:
            labels.setdefault(email, _heuristic_classify(email))
        return labels
    except Exception as e:
        print(f"  [ai_classifier] Gemini call failed ({e}), using heuristic fallback for this batch.")
        return {email: _heuristic_classify(email) for email in emails}


def classify_emails(emails):
    """
    emails: list of unique email strings.
    Returns: dict {email: 'business' | 'individual'}
    """
    unique_emails = list(dict.fromkeys(emails))  # de-duplicate, preserve order
    results = {}

    if not GEMINI_API_KEY:
        print("  [ai_classifier] GEMINI_API_KEY not set — using heuristic classifier for all emails.")
        return {email: _heuristic_classify(email) for email in unique_emails}

    for i in range(0, len(unique_emails), BATCH_SIZE):
        batch = unique_emails[i:i + BATCH_SIZE]
        results.update(_gemini_classify_batch(batch))

    return results


if __name__ == "__main__":
    sample = ["buyer@somecompany.com", "person@gmail.com", "sales@bigcorp.co.uk"]
    print(classify_emails(sample))
