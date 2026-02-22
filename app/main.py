"""FastAPI application entry point."""

import uuid

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict, Optional

from app.orchestrator import handle

app = FastAPI(
    title="MikiAI Copilot",
    description="Personal multi-agent AI copilot MVP.",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    """Request body for the /chat endpoint."""

    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    """Response body returned by the /chat endpoint."""

    session_id: str
    answer: str
    trace: Dict[str, Any]


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Process a user message and return an agent response.

    - Routes to the appropriate agent (dev / research / curator).
    - Optionally retrieves context from the knowledge base (RAG).
    - Supports the ``/promote`` command to create KnowledgeCards.
    """
    session_id = request.session_id or str(uuid.uuid4())
    result = handle(request.message, session_id)
    return ChatResponse(**result)
