# MikiAI-Copilot

Personal multi-agent AI copilot — FastAPI MVP.

## Project Structure

```
personal-ai-copilot/
│
├── app/
│   ├── main.py          # FastAPI app & /chat endpoint
│   ├── orchestrator.py  # Ties routing, RAG and agents together
│   ├── router.py        # Rule-based intent / namespace detection
│   ├── agents/
│   │   ├── dev.py       # Dev agent stub
│   │   ├── research.py  # Research agent stub
│   │   └── curator.py   # Curator: builds KnowledgeCards
│   └── kb/
│       ├── schemas.py   # KnowledgeCard Pydantic model
│       ├── store.py     # JSON-based local persistence
│       ├── retrieve.py  # Namespace-filtered retrieval
│       └── guardian.py  # Policy guardian (blocks sensitive data)
│
├── kb/                  # Runtime storage for KnowledgeCards (JSON files)
├── tests/
│   └── test_chat.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation

```bash
pip install -r requirements.txt
```

## Running the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
Interactive docs: `http://127.0.0.1:8000/docs`

## Example requests

### General research query

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about transformer models."}'
```

### Dev query (triggers Dev Agent)

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Help me debug this Python error."}'
```

### Promote a Knowledge Card

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "/promote title=\"Retry Pattern\" problem=\"Transient failures\" solution=\"Exponential back-off\" tags=\"resilience,patterns\" namespace=\"PERSONAL\""
  }'
```

### Example response

```json
{
  "session_id": "a1b2c3d4-...",
  "answer": "[Research Agent] I received your research query. This is a stub response — wire up your LLM here.",
  "trace": {
    "intent": "research",
    "namespace": "PERSONAL",
    "use_rag": true,
    "retrieved_count": 0,
    "stored_card_id": null
  }
}
```

## Running tests

```bash
pytest tests/
```

## Namespaces

| Namespace  | Description                      |
|------------|----------------------------------|
| `PERSONAL` | Default personal knowledge space |
| `BRIDGE`   | Shared / bridge knowledge space  |

## Policy Guardian

Before any KnowledgeCard is stored, the guardian blocks content that contains:

- Corporate email addresses
- Ticket-like patterns (e.g. `ABC-1234`)
- Sensitive file paths (`C:\` or `/mnt/`)
