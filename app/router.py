"""Rule-based intent detection and namespace routing."""

import re
from typing import Tuple

# Namespaces supported by the system
NAMESPACES = {"PERSONAL", "BRIDGE"}
DEFAULT_NAMESPACE = "PERSONAL"

# Keywords that map a message to the dev agent
_DEV_KEYWORDS = re.compile(r"\b(debug|code|error|bug|fix|compile|test|deploy)\b", re.IGNORECASE)

# Namespace tokens a user can include in their message
_NAMESPACE_RE = re.compile(r"\b(PERSONAL|BRIDGE)\b", re.IGNORECASE)


def detect_intent(message: str) -> Tuple[str, str, bool]:
    """Analyse *message* and return (intent, namespace, use_rag).

    Rules:
    - If the message starts with "/promote"  → intent = "curate"
    - If the message contains dev keywords   → intent = "dev"
    - Otherwise                              → intent = "research"

    Namespace is extracted from the message when present; defaults to PERSONAL.
    RAG is enabled for all intents except "curate".

    Args:
        message: The raw user message.

    Returns:
        A tuple of (intent, namespace, use_rag).
    """
    stripped = message.strip()

    # Namespace detection
    ns_match = _NAMESPACE_RE.search(stripped)
    namespace = ns_match.group(0).upper() if ns_match else DEFAULT_NAMESPACE

    # Intent detection
    if stripped.lower().startswith("/promote"):
        return "curate", namespace, False

    if _DEV_KEYWORDS.search(stripped):
        return "dev", namespace, True

    return "research", namespace, True
