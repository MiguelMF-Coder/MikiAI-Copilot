"""Minimal tests for the /chat endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_research_intent():
    """A generic message should be routed to the research agent."""
    response = client.post("/chat", json={"message": "Tell me about neural networks."})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "answer" in data
    assert data["trace"]["intent"] == "research"
    assert data["trace"]["namespace"] == "PERSONAL"
    assert data["trace"]["use_rag"] is True


def test_chat_dev_intent():
    """A message containing 'debug' should route to the dev agent."""
    response = client.post("/chat", json={"message": "Help me debug this code."})
    assert response.status_code == 200
    data = response.json()
    assert data["trace"]["intent"] == "dev"
    assert "[Dev Agent]" in data["answer"]


def test_chat_curate_intent():
    """A /promote command should route to the curator agent."""
    response = client.post(
        "/chat",
        json={"message": '/promote title="Test Card" problem="A test problem" solution="A solution"'},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trace"]["intent"] == "curate"
    assert data["trace"]["stored_card_id"] is not None


def test_chat_namespace_bridge():
    """The BRIDGE namespace should be detected from the message."""
    response = client.post("/chat", json={"message": "Research topic in BRIDGE namespace."})
    assert response.status_code == 200
    data = response.json()
    assert data["trace"]["namespace"] == "BRIDGE"


def test_chat_session_id_passthrough():
    """A provided session_id must be echoed back in the response."""
    response = client.post("/chat", json={"session_id": "abc-123", "message": "Hello"})
    assert response.status_code == 200
    assert response.json()["session_id"] == "abc-123"


def test_policy_guardian_blocks_corporate_email():
    """Guardian should block a /promote that contains a corporate email."""
    response = client.post(
        "/chat",
        json={"message": '/promote title="Leak" problem="user@company.com" solution="x"'},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Blocked" in data["answer"]
    assert data["trace"]["stored_card_id"] is None


def test_policy_guardian_blocks_ticket():
    """Guardian should block a /promote containing a ticket-like pattern."""
    response = client.post(
        "/chat",
        json={"message": '/promote title="Ticket" problem="Ref: PROJ-1234" solution="fix it"'},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Blocked" in data["answer"]


def test_policy_guardian_blocks_file_path():
    """Guardian should block a /promote containing a sensitive file path."""
    response = client.post(
        "/chat",
        json={"message": '/promote title="Path" problem="see C:\\\\secret\\\\file" solution="x"'},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Blocked" in data["answer"]
