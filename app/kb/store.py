"""JSON-based local persistence for KnowledgeCards."""

import json
import os
from typing import List

from app.kb.schemas import KnowledgeCard

# Directory where card files are stored (one JSON file per namespace)
_KB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "kb")


def _namespace_path(namespace: str) -> str:
    """Return the file path for a given namespace store."""
    safe = namespace.replace("/", "_").replace("\\", "_")
    return os.path.join(_KB_DIR, f"{safe}.json")


def _load_namespace(namespace: str) -> List[dict]:
    """Load all raw card dicts from the namespace file."""
    path = _namespace_path(namespace)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_namespace(namespace: str, cards: List[dict]) -> None:
    """Persist the list of raw card dicts to the namespace file."""
    os.makedirs(_KB_DIR, exist_ok=True)
    path = _namespace_path(namespace)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(cards, fh, indent=2, default=str)


def store_card(card: KnowledgeCard) -> None:
    """Append a KnowledgeCard to its namespace store.

    Args:
        card: The KnowledgeCard to persist.
    """
    cards = _load_namespace(card.namespace)
    cards.append(card.model_dump())
    _save_namespace(card.namespace, cards)
