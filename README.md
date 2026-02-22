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

## LLM setup (.env)

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_openai_api_key_here
# Optional (defaults to gpt-4.1-mini)
MODEL=gpt-4.1-mini
```

## Switching LLM providers

### OpenAI provider

Set:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
# Optional
MODEL=gpt-4.1-mini
```

### Ollama provider (local)

Install and run Ollama, then pull a model and serve locally:

```bash
ollama pull llama3.1:8b
ollama serve
```

Set:

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
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

`/promote` accepts only a two-line format:

1. First line: metadata (`namespace`, `tags`)
2. Next line(s): JSON object with card fields

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "/promote namespace=PERSONAL tags=resilience,patterns\n{\"title\":\"Retry Pattern\",\"problem\":\"Transient failures\",\"solution_pattern\":\"Exponential back-off\",\"steps\":[\"detect transient error\",\"retry with backoff\"],\"constraints\":\"idempotent operation\",\"example\":\"HTTP 503 retry\",\"anti_pattern\":\"infinite retry loop\"}"
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
