"""Curator agent: builds structured KnowledgeCards from /promote commands."""

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.kb.guardian import check_policy
from app.kb.schemas import KnowledgeCard
from app.kb.store import store_card


_FORMAT_ERROR = (
    "Invalid /promote format. Use two lines: first line '/promote namespace=... tags=...', "
    "then a JSON object on the next line(s) with KnowledgeCard fields."
)


def _parse_key_values(raw: str) -> Dict[str, str]:
    """Parse key=value pairs from promote metadata line."""
    pairs: Dict[str, str] = {}
    for match in re.finditer(
        r"(?P<key>\w+)\s*=\s*(?P<value>\"[^\"]*\"|'[^']*'|.+?)(?=\s+\w+\s*=|$)",
        raw,
    ):
        key = match.group("key").strip().lower()
        value = match.group("value").strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        pairs[key] = value.strip()
    return pairs


def _to_list(value: Any) -> List[str]:
    """Normalise list-like fields from JSON payload."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    return [str(value).strip()] if str(value).strip() else []


def run(message: str, namespace: str) -> Tuple[Optional[KnowledgeCard], str]:
    """Parse a strict /promote command and create a KnowledgeCard.

    Required format::

        /promote namespace=BRIDGE tags=router,rag
        {"title":"...", "problem":"...", ...}

    Args:
        message: The raw /promote message from the user.
        namespace: The target namespace for the card.

    Returns:
        A tuple of (KnowledgeCard | None, status_message).
        The card is None when validation fails or the operation is blocked.
    """
    stripped = message.strip()
    if "\n" not in stripped:
        return None, _FORMAT_ERROR

    first_line, json_blob = stripped.split("\n", 1)
    metadata_source = first_line
    if metadata_source.lower().startswith("/promote"):
        metadata_source = metadata_source[len("/promote") :].strip()
    metadata = _parse_key_values(metadata_source)

    raw_json_payload = json_blob.strip()
    if not raw_json_payload:
        return None, _FORMAT_ERROR

    # Run policy check on metadata + raw JSON payload before parsing/storing.
    allowed, reason = check_policy(f"{metadata_source}\n{raw_json_payload}")
    if not allowed:
        return None, reason

    try:
        loaded = json.loads(raw_json_payload)
    except json.JSONDecodeError:
        return None, _FORMAT_ERROR

    if not isinstance(loaded, dict):
        return None, _FORMAT_ERROR

    payload: Dict[str, Any] = {k.lower(): v for k, v in loaded.items()}

    title = str(payload.get("title", "")).strip()
    if not title:
        return None, "Invalid /promote payload: 'title' is required and cannot be empty."

    target_namespace = metadata.get("namespace", namespace).upper()

    tags_value = metadata.get("tags", "")
    tags = [t.strip() for t in str(tags_value).split(",") if t.strip()] if tags_value else []

    card = KnowledgeCard(
        id=str(uuid.uuid4()),
        title=title,
        problem=str(payload.get("problem", "No problem statement provided.")),
        solution_pattern=str(payload.get("solution_pattern", "No solution provided.")),
        steps=_to_list(payload.get("steps")),
        constraints=_to_list(payload.get("constraints")),
        example=str(payload.get("example", "")),
        anti_pattern=str(payload.get("anti_pattern", "")),
        tags=tags,
        namespace=target_namespace,
        created_at=datetime.now(timezone.utc),
    )

    store_card(card)
    return card, f"KnowledgeCard '{card.title}' stored with id={card.id}."
