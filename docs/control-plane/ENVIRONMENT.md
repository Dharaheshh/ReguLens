# ENVIRONMENT.md — Environment, Configuration, Local Development

## Required environment variables

Defined in `.env.example` (committed) and `.env` (never committed):

```
# Database
DATABASE_URL=postgresql://postgres:devpass@db:5432/regulens

# LLM
ANTHROPIC_API_KEY=
LLM_MODEL=claude-sonnet-4-6
LLM_TEMPERATURE_DEFAULT=0.2

# Embeddings
EMBEDDING_MODEL=<provider-specific model name>
EMBEDDING_DIMENSION=1536

# Auth (hackathon demo only — see SECURITY.md)
DEMO_BEARER_TOKEN=

# App
BACKEND_PORT=8000
FRONTEND_PORT=5173
ENVIRONMENT=development   # development | test
```

**Rule:** `EMBEDDING_DIMENSION` here must exactly match the `VECTOR(n)`
dimension in `chunks.embedding` (`DATABASE_SCHEMA.md`). If the embedding model
changes, both must be updated together, in the same commit, with a new
migration if the column dimension changes.

## Docker Compose

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: regulens
      POSTGRES_PASSWORD: devpass
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on:
      db:
        condition: service_healthy
    env_file: .env
    volumes: ["./backend:/app"]   # dev only — live reload

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    depends_on: [backend]
    env_file: .env
    volumes: ["./frontend:/app"]

volumes:
  pgdata:
```

## Local development

```bash
cp .env.example .env    # fill in ANTHROPIC_API_KEY and DEMO_BEARER_TOKEN
docker compose up --build
```

Backend runs migrations automatically on startup in development (Alembic
`upgrade head` as a startup step) — this is acceptable for the hackathon
timeline; a production setup would run migrations as a separate deploy step.

## Test environment

- Tests run against a separate Postgres database (`regulens_test`), created
  fresh per test run, migrated, seeded with fixture data, torn down after.
- LLM calls in tests are mocked by default (fixed fake responses matching
  each call's Pydantic schema) — no tests depend on live API calls unless
  explicitly marked as an integration test requiring `ANTHROPIC_API_KEY` to
  be set, and those are skipped in CI-less local runs if the key is absent.

## LLM configuration

- Provider: Anthropic Claude, via the official SDK.
- Model: set via `LLM_MODEL` — do not hardcode the model string anywhere in
  application code; read it from `Settings`.
- Every call sets `temperature` explicitly per `AI_RAG_DESIGN.md`'s per-call
  values — never relies on a provider default.

## Embedding configuration

- Model and dimension are set via `EMBEDDING_MODEL` / `EMBEDDING_DIMENSION`,
  read from `Settings`, never hardcoded.
- If switching embedding providers mid-hackathon (should be avoided), every
  existing chunk's embedding must be regenerated — there is no mixed-dimension
  support in a single `chunks` table.

## What must never appear in the repository

- Real API keys, even temporarily, even in a branch, even in a test file.
- A real `.env` file (only `.env.example` with placeholders is committed).
- Any credential printed in a log file that gets committed.
