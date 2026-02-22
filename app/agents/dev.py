"""Dev agent: handles coding, debugging and development-related queries."""

from typing import List

from app.kb.schemas import KnowledgeCard


def run(message: str, context: List[KnowledgeCard]) -> str:
    """Return a stub response for development-related queries.

    Args:
        message: The user's message.
        context: Retrieved KnowledgeCards from the knowledge base (may be empty).

    Returns:
        A plain-text answer string.
    """
    context_hint = (
        f" I found {len(context)} relevant knowledge card(s) in the knowledge base."
        if context
        else ""
    )
    return (
        f"[Dev Agent] I received your development query.{context_hint} "
        "This is a stub response — wire up your LLM here."
    )
