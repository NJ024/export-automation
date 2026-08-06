"""
validation/email_validator.py — Email Validation Module (spec section 5.3).

Layer 1 (per spec): regex-based syntax validation (local-part@domain.tld).
Layer 2 (enhancement beyond the base spec, same free approach used in the
earlier prototype): DNS MX-record check, to catch domains that are syntactically
fine but don't actually have a mail server. No paid API required for either
layer.

Records with missing/unparseable emails are flagged for manual review rather
than silently discarded, per the spec's error-handling table.
"""

import re

try:
    import dns.resolver
    _DNS_AVAILABLE = True
except ImportError:
    _DNS_AVAILABLE = False

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_mx_cache = {}


def is_valid_format(email):
    return bool(email) and bool(EMAIL_REGEX.match(email.strip()))


def has_mx_record(domain):
    if not _DNS_AVAILABLE:
        return True  # skip this layer if dnspython isn't installed
    if domain in _mx_cache:
        return _mx_cache[domain]
    try:
        answers = dns.resolver.resolve(domain, "MX")
        result = len(answers) > 0
    except Exception:
        result = False
    _mx_cache[domain] = result
    return result


def validate(email):
    """Returns (status, reason) where status is 'valid', 'invalid', or 'flagged'."""
    if not email:
        return "flagged", "missing email — needs manual review"
    if not is_valid_format(email):
        return "invalid", "malformed email syntax"
    domain = email.split("@")[-1]
    if not has_mx_record(domain):
        return "invalid", "domain has no mail server (MX record)"
    return "valid", "ok"


def validate_batch(records):
    """
    records: list of buyer dicts with an 'email' key.
    Returns (valid_records, invalid_records, flagged_records) — same dicts,
    each with a 'validation_reason' key added.
    """
    valid, invalid, flagged = [], [], []
    for record in records:
        status, reason = validate(record.get("email", ""))
        record = {**record, "validation_reason": reason}
        if status == "valid":
            valid.append(record)
        elif status == "invalid":
            invalid.append(record)
        else:
            flagged.append(record)
    return valid, invalid, flagged


if __name__ == "__main__":
    for e in ["good@gmail.com", "not-an-email", "user@thisdomaindoesnotexist9999.com"]:
        print(e, "->", validate(e))
