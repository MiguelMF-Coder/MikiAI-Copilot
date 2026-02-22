"""Pydantic schemas for the knowledge base."""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class KnowledgeCard(BaseModel):
    """Represents a structured unit of reusable knowledge."""

    id: str
    title: str
    problem: str
    solution_pattern: str
    steps: List[str]
    constraints: List[str]
    example: str
    anti_pattern: str
    tags: List[str]
    namespace: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
