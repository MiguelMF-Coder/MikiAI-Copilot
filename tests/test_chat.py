"""Minimal tests for the /chat endpoint."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_llm_call(monkeypatch, request):
    """Prevent network LLM calls and return deterministic text."""

    if request.node.name == "test_llm_provider_env_selection":
        return

    class _FakeProvider:
        def generate(self, system_prompt: str, user_prompt: str, max_output_tokens: int) -> str:
            system = system_prompt.lower()
            if "software engineering" in system:
                return "MOCK_DEV_RESPONSE"
            if "research assistant" in system:
                return "MOCK_RESEARCH_RESPONSE"
            return "MOCK_GENERIC_RESPONSE"

    monkeypatch.setattr("app.llm._get_provider", lambda: _FakeProvider())


def test_llm_provider_env_selection(monkeypatch):
    """LLM_PROVIDER should switch provider selection logic without network calls."""
    import app.llm as llm

    monkeypatch.setenv("LLM_PROVIDER", "openai")
    openai_provider = llm._get_provider()
    assert openai_provider.__class__.__name__ == "OpenAIProvider"

    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    ollama_provider = llm._get_provider()
    assert ollama_provider.__class__.__name__ == "OllamaProvider"


def _count_cards(namespace: str) -> int:
    """Return the number of stored cards for a namespace."""
    path = Path(__file__).resolve().parents[1] / "kb" / f"{namespace}.json"
    if not path.exists():
        return 0
    return len(json.loads(path.read_text(encoding="utf-8")))


def test_root_health():
    """GET / should return a simple health payload."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "docs": "/docs"}


def test_chat_research_intent():
    """A generic message should be routed to the research agent."""
    response = client.post("/chat", json={"message": "Tell me about neural networks."})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["answer"] == "MOCK_RESEARCH_RESPONSE"
    assert data["trace"]["intent"] == "research"
    assert data["trace"]["namespace"] == "PERSONAL"
    assert data["trace"]["use_rag"] is False


def test_chat_research_with_explicit_kb_hint_enables_rag():
    """RAG should be enabled only when an explicit KB hint is present."""
    response = client.post(
        "/chat",
        json={"message": "Use knowledge base and explain retry patterns."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trace"]["intent"] == "research"
    assert data["trace"]["use_rag"] is True


def test_chat_dev_with_rag_flag_enables_rag():
    """An explicit rag=true flag should enable RAG for dev intent."""
    response = client.post(
        "/chat",
        json={"message": "debug import issues rag=true"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trace"]["intent"] == "dev"
    assert data["trace"]["use_rag"] is True


def test_chat_dev_intent():
    """A message containing 'debug' should route to the dev agent."""
    response = client.post("/chat", json={"message": "Help me debug this code."})
    assert response.status_code == 200
    data = response.json()
    assert data["trace"]["intent"] == "dev"
    assert data["trace"]["use_rag"] is False
    assert data["answer"] == "MOCK_DEV_RESPONSE"


def test_chat_dev_with_use_kb_enables_rag():
    """Explicit 'use kb' should enable RAG for dev intent."""
    response = client.post(
        "/chat",
        json={"message": "debug this import issue, use kb"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trace"]["intent"] == "dev"
    assert data["trace"]["use_rag"] is True


def test_chat_use_kb_from_bridge_sets_namespace_and_rag():
    """KB trigger + explicit namespace should route to BRIDGE with RAG on."""
    response = client.post(
        "/chat",
        json={"message": "use kb from BRIDGE for deployment troubleshooting"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trace"]["namespace"] == "BRIDGE"
    assert data["trace"]["use_rag"] is True


def test_chat_curate_intent():
    """A /promote command should route to the curator agent."""
    message = (
        "/promote namespace=PERSONAL tags=test\n"
        '{"title":"Test Card","problem":"A test problem","solution_pattern":"A solution"}'
    )
    response = client.post(
        "/chat",
        json={"message": message},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trace"]["intent"] == "curate"
    assert data["trace"]["stored_card_id"] is not None


def test_chat_curate_json_payload_bridge_namespace():
    """A /promote with metadata + JSON body should store fields correctly."""
    message = (
        "/promote namespace=BRIDGE tags=router,rag\n"
        '{"title":"Namespace RAG","problem":"Need namespace-aware retrieval",'
        '"solution_pattern":"Namespace filtered RAG","steps":["detect namespace","filter cards"],'
        '"constraints":"low latency","example":"query in BRIDGE",'
        '"anti_pattern":"global retrieval"}'
    )
    response = client.post("/chat", json={"message": message})
    assert response.status_code == 200
    data = response.json()
    assert data["trace"]["intent"] == "curate"
    assert data["trace"]["namespace"] == "BRIDGE"
    assert data["trace"]["stored_card_id"] is not None

    bridge_path = Path(__file__).resolve().parents[1] / "kb" / "BRIDGE.json"
    assert bridge_path.exists()

    cards = json.loads(bridge_path.read_text(encoding="utf-8"))
    stored = next(card for card in cards if card["id"] == data["trace"]["stored_card_id"])
    assert stored["title"] == "Namespace RAG"
    assert stored["namespace"] == "BRIDGE"


def test_chat_curate_legacy_key_value_rejected_and_not_stored():
    """Legacy one-line key=value /promote should be rejected and not stored."""
    before = _count_cards("BRIDGE")
    response = client.post(
        "/chat",
        json={"message": "/promote namespace=BRIDGE title=Bad Format problem=Wrong solution=Wrong"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trace"]["intent"] == "curate"
    assert data["trace"]["stored_card_id"] is None
    assert "Invalid /promote format" in data["answer"]
    after = _count_cards("BRIDGE")
    assert after == before


def test_chat_curate_missing_json_newline_rejected_and_not_stored():
    """A bare /promote command without JSON payload should be rejected."""
    before = _count_cards("PERSONAL")
    response = client.post("/chat", json={"message": "/promote"})
    assert response.status_code == 200
    data = response.json()
    assert data["trace"]["intent"] == "curate"
    assert data["trace"]["stored_card_id"] is None
    assert "Invalid /promote format" in data["answer"]
    after = _count_cards("PERSONAL")
    assert after == before


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
    message = (
        "/promote namespace=PERSONAL tags=security\n"
        '{"title":"Leak","problem":"user@company.com","solution_pattern":"x"}'
    )
    response = client.post(
        "/chat",
        json={"message": message},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Blocked" in data["answer"]
    assert data["trace"]["stored_card_id"] is None


def test_policy_guardian_blocks_ticket():
    """Guardian should block a /promote containing a ticket-like pattern."""
    message = (
        "/promote namespace=PERSONAL tags=security\n"
        '{"title":"Ticket","problem":"Ref: PROJ-1234","solution_pattern":"fix it"}'
    )
    response = client.post(
        "/chat",
        json={"message": message},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Blocked" in data["answer"]


def test_policy_guardian_blocks_file_path():
    """Guardian should block a /promote containing a sensitive file path."""
    message = (
        "/promote namespace=PERSONAL tags=security\n"
        '{"title":"Path","problem":"see C:\\\\secret\\\\file","solution_pattern":"x"}'
    )
    response = client.post(
        "/chat",
        json={"message": message},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Blocked" in data["answer"]
