"""Orchestrator: ties together routing, RAG retrieval, and agent dispatch."""

from typing import Any, Dict, Optional

from app.kb.retrieve import retrieve
from app.router import detect_intent
from app.agents import dev, research, curator


def handle(message: str, session_id: str) -> Dict[str, Any]:
    """Process a user message end-to-end and return a response dict.

    Flow:
    1. Detect intent, namespace and RAG flag via the router.
    2. If RAG is enabled, retrieve relevant KnowledgeCards.
    3. Dispatch to the appropriate agent.
    4. Build and return the response including trace metadata.

    Args:
        message: The user's raw message.
        session_id: The session identifier (passed through unchanged).

    Returns:
        A dict with keys: session_id, answer, trace.
    """
    intent, namespace, use_rag = detect_intent(message)

    context = []
    if use_rag:
        context = retrieve(namespace, top_k=5)

    stored_card_id: Optional[str] = None
    answer: str

    if intent == "curate":
        card, status = curator.run(message, namespace)
        answer = status
        if card:
            stored_card_id = card.id
    elif intent == "dev":
        answer = dev.run(message, context)
    else:
        answer = research.run(message, context)

    trace = {
        "intent": intent,
        "namespace": namespace,
        "use_rag": use_rag,
        "retrieved_count": len(context),
        "stored_card_id": stored_card_id,
    }

    return {
        "session_id": session_id,
        "answer": answer,
        "trace": trace,
    }
