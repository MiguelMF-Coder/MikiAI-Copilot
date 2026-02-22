"""Policy guardian: blocks sensitive data before it is stored."""

import re
from typing import Tuple

# Patterns considered sensitive
_CORPORATE_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@(?!gmail\.com|yahoo\.com|hotmail\.com|outlook\.com)[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)
_TICKET_RE = re.compile(r"\b[A-Z]{2,10}-\d{3,6}\b")
_FILE_PATH_RE = re.compile(r"(C:\\|/mnt/)", re.IGNORECASE)


def check_policy(text: str) -> Tuple[bool, str]:
    """Check whether *text* violates storage policy.

    Returns:
        (allowed, reason) – *allowed* is True when the text is safe to store;
        False when it must be blocked, with *reason* explaining why.
    """
    if _CORPORATE_EMAIL_RE.search(text):
        return False, "Blocked: corporate email address detected."
    if _TICKET_RE.search(text):
        return False, "Blocked: ticket-like pattern detected (e.g. ABC-1234)."
    if _FILE_PATH_RE.search(text):
        return False, "Blocked: sensitive file path detected (C:\\ or /mnt/)."
    return True, ""
