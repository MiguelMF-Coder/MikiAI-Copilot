"""Namespace-filtered retrieval from the local knowledge base."""

from typing import List

from app.kb.schemas import KnowledgeCard
from app.kb.store import _load_namespace


def retrieve(namespace: str, top_k: int = 5) -> List[KnowledgeCard]:
    """Retrieve the most recent *top_k* KnowledgeCards for a namespace.

    Args:
        namespace: The namespace to filter by (e.g. "PERSONAL", "BRIDGE").
        top_k: Maximum number of cards to return.

    Returns:
        A list of KnowledgeCard instances, newest first.
    """
    raw_cards = _load_namespace(namespace)
    # Return the most recently stored cards first
    selected = raw_cards[-top_k:] if len(raw_cards) > top_k else raw_cards
    return [KnowledgeCard(**c) for c in reversed(selected)]
