"""Dev agent: handles coding, debugging and development-related queries."""

from typing import List

from app.kb.schemas import KnowledgeCard
import app.llm as llm


def run(message: str, context: List[KnowledgeCard]) -> str:
    """Generate a development-focused response.

    Args:
        message: The user's message.
        context: Retrieved KnowledgeCards from the knowledge base (may be empty).

    Returns:
        A plain-text answer string.
    """
    context_lines = []
    for card in context:
        context_lines.append(
            f"- {card.title}: {card.problem} | pattern={card.solution_pattern}"
        )

    context_text = "\n".join(context_lines) if context_lines else "No KB context available."

    system_prompt = (
        "You are a senior software engineering assistant. "
        "Provide concise, actionable debugging guidance only. "
        "Output a maximum of 8 bullet points. "
        "Include exact shell commands when relevant. "
        "Avoid long explanations and keep each bullet short."
    )
    user_prompt = (
        f"User request:\n{message}\n\n"
        f"Knowledge base context:\n{context_text}"
    )

    return llm.call_llm(system_prompt=system_prompt, user_prompt=user_prompt)
