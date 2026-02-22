"""Curator agent: builds structured KnowledgeCards from /promote commands."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from app.kb.guardian import check_policy
from app.kb.schemas import KnowledgeCard
from app.kb.store import store_card


def run(message: str, namespace: str) -> Tuple[Optional[KnowledgeCard], str]:
    """Parse a /promote command and create a KnowledgeCard.

    Expected format (minimal)::

        /promote title="..." problem="..." solution="..."

    Unrecognised fields are gracefully ignored.  All required fields that are
    not provided in the message are filled with placeholder values so the MVP
    remains functional without strict input validation.

    Args:
        message: The raw /promote message from the user.
        namespace: The target namespace for the card.

    Returns:
        A tuple of (KnowledgeCard | None, status_message).
        The card is None when the guardian blocks the operation.
    """
    # Run policy check on the full message before doing anything else
    allowed, reason = check_policy(message)
    if not allowed:
        return None, reason

    # Simple key="value" extraction
    def _extract(key: str, default: str = "") -> str:
        import re
        pattern = rf'{key}=["\']([^"\']+)["\']'
        match = re.search(pattern, message, re.IGNORECASE)
        return match.group(1) if match else default

    card = KnowledgeCard(
        id=str(uuid.uuid4()),
        title=_extract("title", "Untitled"),
        problem=_extract("problem", "No problem statement provided."),
        solution_pattern=_extract("solution", "No solution provided."),
        steps=_extract("steps", "").split(";") if _extract("steps") else [],
        constraints=_extract("constraints", "").split(";") if _extract("constraints") else [],
        example=_extract("example", ""),
        anti_pattern=_extract("anti_pattern", ""),
        tags=[t.strip() for t in _extract("tags", "").split(",") if t.strip()],
        namespace=namespace,
        created_at=datetime.now(timezone.utc),
    )

    store_card(card)
    return card, f"KnowledgeCard '{card.title}' stored with id={card.id}."
