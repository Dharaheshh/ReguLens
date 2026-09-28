# ReguLens — Final Corrections

This file is an addendum to the 15 approved control-plane documents. It does
not replace them. Where this file specifies a provider, environment variable,
or implementation detail that differs from an older document, **this file
wins** — see Section 15.

## 0. Executive Summary

**What changed:** The architecture assumed Anthropic Claude as the LLM
provider and an unspecified embedding provider with `EMBEDDING_DIMENSION`
implied to be 1536 (OpenAI/Anthropic-scale). Research shows Anthropic has no
free tier suitable for hackathon iteration, while **Groq** and **Google
Gemini** both offer genuinely free, no-credit-card API access with
OpenAI-compatible endpoints — meaning one thin adapter, not three, can serve
both. Embeddings are moved to a **local, free, zero-network model**
(`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions) rather than any
paid or rate-limited API, which also removes embedding-API rate limits as a
risk during corpus ingestion (the highest-volume part of the workload).

**Why:** Cost and reliability under demo conditions matter more than model
sophistication for this system — every LLM call in `AI_RAG_DESIGN.md` is a
narrow, structured-output task (extraction, classification), not open-ended
generation, and mid-tier fast models handle these well.

**What the coding agent must do:** Build the small `LLMProvider` abstraction
in Section 5, wire `.env` per Section 4, and apply the numbered corrections
in Sections 6–13 before or during the relevant `TASKS.md` items. Do not
otherwise deviate from the approved architecture.

**On the "Memcode" router specifically: do not use it.** See Section 3 — it
could not be verified and the described behavior doesn't match anything
confirmable. This is a security-relevant decision, not just a preference.

---

## 1. LLM Provider Research

| Provider | Free Tier | Model(s) used here | API Type | Structured Output | Context | Rate Limits (free) | Cost (paid) | Hackathon Suitability |
|---|---|---|---|---|---|---|---|---|
| **Groq** | Yes, no card required | `llama-3.3-70b-versatile` | OpenAI-compatible (`/openai/v1`) | Yes — `response_format={"type":"json_object"}`, JSON mode | 131K tokens | 30 RPM / 1,000 RPD / 12K TPM (confirmed on `console.groq.com/docs/rate-limits`) | $0.59/$0.79 per M tokens in/out if ever exceeded | **Best fit — primary** |
| **Google Gemini** | Yes, no card required | `gemini-2.5-flash-lite` | Native + OpenAI-compatible (`/v1beta/openai/`) | Yes — JSON mode via `response_format` on the compat endpoint | 1M tokens | ~15–30 RPM, ~500–1,500 RPD depending on model (Google stopped publishing exact free-tier tables in docs as of Sept 2026 — verify live in AI Studio before the event) | ~$0.30/$2.50 per M tokens (Flash) if exceeded | **Strong fallback** |
| **OpenRouter** | Small free credit on signup + a rotating set of fully free models (`:free` suffix models, e.g. some Llama/Qwen variants) | varies | OpenAI-compatible | Varies by underlying model | Varies | Free-model rate limits scale with lifetime purchased credits — very low (reportedly ~50 req/day) with zero credits purchased | Pay-as-you-go across 300+ models | **Emergency only** — free-model quota too thin to rely on as primary |
| **Anthropic Claude** | None | `claude-sonnet-4-6` (original assumption) | Native Messages API | Yes | 200K tokens | N/A (paid) | Premium pricing | **Not usable as primary given the free-first priority** — keep only if the team already holds Anthropic credits from another source |
| **DeepSeek** | Limited low-cost tier, not genuinely free | `deepseek-chat` | OpenAI-compatible | Yes | 64K–128K | Not verified as sufficient for hackathon burst usage | Very cheap (~$0.14/M input) | Cheap fallback if both above are exhausted |
| **Cerebras** | Free tier exists but scope/limits not independently verified enough to rely on for a live demo | — | OpenAI-compatible | Yes | Varies | Unverified | — | Not recommended — insufficiently verified for demo-day reliability |
| **Together AI / Hugging Face Inference** | Both have shrunk or removed meaningful free tiers as of 2026 per current tracking | — | — | — | — | — | — | Not recommended |

**Sources consulted:** `console.groq.com/docs/rate-limits`, `ai.google.dev/gemini-api/docs/rate-limits`, `ai.google.dev/gemini-api/docs/openai`, `openrouter.ai/docs/faq`, `openrouter.ai/docs/api-reference/limits`, plus current community-maintained free-tier trackers cross-checked against the official docs above (community trackers alone are not treated as authoritative — every number above traces back to an official provider doc where one exists).

**Important verified caveat:** Gemini's free-tier numbers are volatile — Google removed the published RPM/RPD tables from its main docs in 2026 and now tells developers to check their live quota in AI Studio. Treat the Gemini figures above as approximate and **verify actual quota in AI Studio the morning of the hackathon**, not from this document alone.

---

## 2. Recommended LLM Strategy

### Primary: **Groq**, model `llama-3.3-70b-versatile`
Chosen because its free tier is the most concretely documented and generous
of the genuinely free options (1,000 requests/day, no credit card), it's
fast (low latency matters live in front of judges), and it natively supports
JSON mode for the structured-output contract every call in
`AI_RAG_DESIGN.md` requires.

### Fallback: **Google Gemini**, model `gemini-2.5-flash-lite`
Used automatically if Groq returns a rate-limit or outage error. Also free,
also OpenAI-compatible, and Flash-Lite specifically has the more generous
free-tier allowance among Gemini models — appropriate for the narrow,
short-output tasks this system needs (not long-form generation).

### Emergency: **OpenRouter** free-model router (`openrouter/free`)
Only reached if both of the above are exhausted mid-demo. Free-tier quota
here is thin and not something to plan the actual demo around — this exists
purely as a "the show can go on" backstop, not a tier the team should
expect to lean on.

**Engineering reasoning, not vibes:** all three are OpenAI-compatible, so
switching between them is an environment-variable change, not a code
change (Section 5). The system never needs to know which provider it's
talking to.

---

## 3. Memcode Assessment

**What it appears to be:** Public research shows a legitimate open-source
project at `memcode.ai` / `github.com/memcode-ai/memcode` — a terminal
coding agent (comparable to Claude Code) with an optional hosted gateway
(`memcode-api`) that proxies to multiple LLM vendors, billed either via a
shared credit balance or bring-your-own-key.

**What could NOT be verified:** The specific domain named in your email,
`router.memcode.in` (a `.in` domain, distinct from the verified `memcode.ai`
project), and the specific claim of "$10 OpenAI Credits" issued through it.
No independent source confirms this domain, this offer, or its relationship
to the legitimate `memcode.ai` project. The described mechanism — receiving
what's framed as "OpenAI credits" through a third-party router — is also
a pattern worth extra scrutiny on its own terms, independent of whether
`router.memcode.in` is affiliated with the real project: it is not something
you should assume means "you can plug this into `OPENAI_API_KEY` and call
OpenAI's actual API," since a router by definition sits in front of the real
provider and could point anywhere.

**Recommendation: do not use it, in primary, fallback, or emergency roles.**
Not because it's necessarily illegitimate, but because it is unverifiable
within the scope of this audit, and Groq + Gemini already give you two
genuinely verified, zero-cost, no-card-required options that fully cover
the workload. There's no reason to take on unverified risk when the
verified options are sufficient. If a teammate wants to investigate it
personally outside the hackathon's critical path, standard cautions apply:
never paste a real Anthropic/OpenAI API key into a third-party site's
"redemption" flow, and never wire an unverified base URL into
`LLM_BASE_URL` for anything that will touch real documents before someone
has manually confirmed what the endpoint actually is and does.

---

## 4. Required Environment Changes

Replace the LLM/embedding section of `ENVIRONMENT.md` with:

```
# LLM — provider-agnostic (see Section 5 for the adapter that consumes these)
LLM_PROVIDER=groq                # groq | gemini | openrouter — selects default base_url/model if not overridden
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=
LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE_DEFAULT=0.2

# LLM fallback — used automatically on rate-limit/outage from primary
LLM_FALLBACK_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_FALLBACK_API_KEY=
LLM_FALLBACK_MODEL=gemini-2.5-flash-lite

# Embeddings — local, free, no API key needed
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

**What each means:**
- `LLM_PROVIDER` is a label only, used for logging/debugging — the actual
  routing behavior comes entirely from `LLM_BASE_URL`/`LLM_MODEL`, since
  every provider here speaks the same OpenAI-compatible wire.
- `LLM_BASE_URL` + `LLM_API_KEY` + `LLM_MODEL` fully describe the primary
  provider; the fallback triple mirrors this for the automatic failover
  path (see Section 5).
- `EMBEDDING_PROVIDER=local` signals the embedder runs in-process (inside
  the backend container), not via an external API call — see Section 5.
- `EMBEDDING_DIMENSION=384` **replaces** the original assumption of 1536 —
  this is a breaking schema change, see CORRECTION-004.

**Removed from the original environment design:** any Anthropic-specific
variable naming (`ANTHROPIC_API_KEY`) as the sole/default path — Anthropic
remains usable only by pointing the same generic `LLM_*` variables at
`https://api.anthropic.com` if the team later obtains credits, but it is
not the default.

---

## 5. Required Architecture Corrections

### CORRECTION-001 — Introduce a minimal LLMProvider abstraction

**Problem:** `AI_RAG_DESIGN.md` and `ENVIRONMENT.md` implicitly assumed a
single hardcoded provider (Anthropic), with no abstraction layer. Scattering
`anthropic.Client(...)` calls across `generation/` and `validation/` would
make switching providers (now confirmed necessary) require touching every
call site.

**Change:** Add one thin interface and one concrete adapter — not three.
Because Groq, Gemini, and OpenRouter are all OpenAI-compatible, a single
`OpenAICompatibleAdapter` configured by `base_url`/`api_key`/`model` covers
all three. No `AnthropicAdapter` or `GeminiAdapter` needed at hackathon
scope — this is deliberately smaller than what `AGENTS.md`'s original
request anticipated, because the research findings make it unnecessary.

**Why:** Smallest abstraction that lets `LLM_BASE_URL`/`LLM_MODEL`/
`LLM_API_KEY` change without touching business logic — exactly what was
asked for, achieved with less code than a multi-adapter design because the
providers converge on one wire format.

**Files affected:** new `backend/app/generation/llm_provider.py` (or
`backend/app/llm/provider.py`); every existing/planned call site in
`generation/` and `validation/` that would otherwise call a provider SDK
directly.

**Implementation:**
```python
# backend/app/llm/provider.py
from openai import OpenAI  # the openai SDK works against any OpenAI-compatible base_url
from pydantic import BaseModel
from app.config import settings

class LLMProvider:
    def __init__(self, base_url: str, api_key: str, model: str):
        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._model = model

    def call(self, system_prompt: str, user_content: str,
              response_model: type[BaseModel], temperature: float) -> BaseModel:
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        raw = response.choices[0].message.content
        return response_model.model_validate_json(raw)  # raises on schema mismatch — caller handles retry


def get_provider(use_fallback: bool = False) -> LLMProvider:
    if use_fallback:
        return LLMProvider(settings.LLM_FALLBACK_BASE_URL, settings.LLM_FALLBACK_API_KEY, settings.LLM_FALLBACK_MODEL)
    return LLMProvider(settings.LLM_BASE_URL, settings.LLM_API_KEY, settings.LLM_MODEL)
```

Every one of the 4 LLM calls in `AI_RAG_DESIGN.md` goes through
`get_provider().call(...)`, never a provider SDK directly. On a schema
validation failure or an HTTP error indicating rate-limiting from the
primary, the calling code retries once against the primary (per existing
`RULES.md` rule #13), and if that also fails, falls back to
`get_provider(use_fallback=True)` for one additional attempt before
entering the defined failure state (`LLM_FAILED`/`VALIDATION_FAILED`) —
this fallback hop is new behavior this correction adds on top of the
existing retry rule.

**Acceptance criteria:** Changing `LLM_BASE_URL`/`LLM_MODEL`/`LLM_API_KEY`
in `.env` and restarting the backend changes which provider serves every
call, with zero code changes required.

---

### CORRECTION-002 — Local embeddings instead of an embedding API

**Problem:** The original design implied an embedding API call per chunk.
At ~40 documents and likely several thousand chunks, this creates two
risks: (a) burning through a free-tier embedding quota during ingestion
alone, before any query testing even starts, and (b) a network dependency
for a step that runs constantly during development.

**Change:** Generate embeddings locally, in-process, using
`sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, ~80MB model,
runs on CPU at hackathon scale in well under a second per chunk).

**Why:** Zero cost, zero rate limit, zero network dependency, and it
removes an entire class of "embedding API is down/rate-limited" failure
mode from the riskiest, highest-volume part of the pipeline. Retrieval
quality from a well-regarded small English sentence embedding model is
more than sufficient for a scoped synthetic corpus at this scale — this is
not a case where a bigger/API-hosted embedding model would materially
change the demo outcome.

**Files affected:** `backend/app/ingestion/embedder.py`,
`backend/requirements.txt` (add `sentence-transformers`), `ENVIRONMENT.md`
(Section 4 above), `DATABASE_SCHEMA.md` (see CORRECTION-004).

**Implementation:**
```python
# backend/app/ingestion/embedder.py
from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")  # loaded once at startup

def embed(text: str) -> list[float]:
    return _model.encode(text, normalize_embeddings=True).tolist()
```

Load the model once at backend startup (module-level, as shown), not per
request — first load takes a few seconds to download/cache the model
weights inside the container; bake this into the Docker image build step
if possible so the demo doesn't pay that cost on first ingestion.

**Acceptance criteria:** Ingesting a document produces 384-dimension
embeddings with no external network call, verified by running ingestion
with network access to the embedding provider deliberately blocked and
confirming it still succeeds.

---

### CORRECTION-003 — Automatic LLM provider failover on rate-limit

**Problem:** `RULES.md` rule #13 (one retry, then failure state) was
written under a single-provider assumption. With two free providers now
in play, a rate-limit on the primary shouldn't necessarily fail the whole
request if a fallback is available and healthy.

**Change:** Insert a fallback attempt between "primary retry failed" and
"enter failure state" — see the `get_provider(use_fallback=True)` call in
CORRECTION-001's implementation. This does not relax rule #13's spirit
(still bounded, still ends in an explicit failure state) — it just gives
the bounded retry one more real chance to succeed before giving up.

**Why:** Free-tier rate limits are the single most likely failure mode
during a live demo (multiple people testing/rehearsing back-to-back). A
same-shape fallback provider meaningfully improves demo reliability for
near-zero implementation cost, since both providers already speak the same
wire per CORRECTION-001.

**Files affected:** every LLM call site; `RULES.md` (update rule #13's
text to describe the fallback hop — a control-plane update, made in its
own commit per `GIT_WORKFLOW.md`).

**Acceptance criteria:** A test that mocks the primary provider returning
HTTP 429 confirms the fallback provider is called and its response is used.

---

### CORRECTION-004 — Update `chunks.embedding` dimension to 384

**Problem:** `DATABASE_SCHEMA.md`'s `chunks` table defines
`embedding VECTOR(1536)`, which assumed an OpenAI/Anthropic-scale embedding
model. Local `all-MiniLM-L6-v2` produces 384-dimension vectors — a direct
mismatch that will error on insert if not corrected before TASK-002 is
implemented.

**Change:**
```sql
-- in the initial migration (TASK-002), not a later migration, since no
-- data exists yet:
embedding VECTOR(384)
```

**Why:** Must match the actual embedding model's output dimension exactly
— this is a hard database constraint, not a style preference.

**Files affected:** `DATABASE_SCHEMA.md`, the initial Alembic migration
(TASK-002).

**Acceptance criteria:** Inserting a real embedding from
CORRECTION-002's `embed()` function succeeds against the migrated schema.

---

## 6. RAG Corrections

No corrections needed to chunking, hybrid retrieval, fusion, or reranking
design — these are provider-independent and remain exactly as specified in
`AI_RAG_DESIGN.md`. The only RAG-pipeline-adjacent change is embedding
generation moving in-process (CORRECTION-002), which changes *where*
embeddings are computed, not the retrieval algorithm itself.

One addition worth flagging: `all-MiniLM-L6-v2` is English-only and
optimized for shorter passages. Since chunks are already targeted at ~500
tokens per `RULES.md`'s chunking rule, this is well within the model's
effective range — no chunking size change needed.

---

## 7. LLM / Generation Corrections

- All 4 LLM calls in `AI_RAG_DESIGN.md` now route through
  `LLMProvider.call()` (CORRECTION-001) instead of a provider SDK directly.
- Structured JSON output changes from Anthropic's native structured-output
  mechanism to OpenAI-style `response_format={"type": "json_object"}` — the
  Pydantic validation step downstream is unchanged, since it was always
  provider-agnostic (parse-then-validate).
- Temperature values specified per call in `AI_RAG_DESIGN.md` (0.1–0.2)
  remain unchanged — both Groq and Gemini honor the same `temperature`
  parameter identically via the OpenAI-compatible wire.
- Retry-then-fallback-then-failure-state sequence per CORRECTION-003.

---

## 8. Contradiction Engine Corrections

No corrections to the underlying design — the deterministic pre-filter
(same `product_topic`, `approved` status, capped at 10 candidates) plus
scoped LLM comparison in `AI_RAG_DESIGN.md`/`ARCHITECTURE.md` already
correctly avoids treating semantic similarity as contradiction, and already
accounts for product/topic/date/version/threshold/unit factors via the
system prompt instruction to the comparison call. This audit found nothing
to change here — the design was already sound on this point.

---

## 9. Evidence Sufficiency Corrections

No corrections to the underlying algorithm. One clarification worth adding
to `AI_RAG_DESIGN.md` for whoever implements TASK-016: the
`THRESHOLD_HIGH`/`THRESHOLD_LOW` cosine-similarity cutoffs will need
recalibration against the actual score distribution `all-MiniLM-L6-v2`
produces on the real corpus (different embedding models produce different
absolute similarity score ranges) — the starting values of 0.75/0.55 in
`AI_RAG_DESIGN.md` were illustrative, not tied to any specific model, so
this isn't a new requirement, just a reminder that calibration must happen
against whichever model is actually running.

---

## 10. Security Corrections

- **New item:** never place a real API key (Groq, Gemini, or otherwise)
  into any third-party "router" or "credit redemption" site without
  independent verification of that site's legitimacy — see Section 3. Add
  this as an explicit line in `SECURITY.md`'s secrets section.
- The `<UNTRUSTED_EVIDENCE>` wrapping pattern in `SECURITY.md` is unchanged
  and applies identically regardless of which LLM provider is behind
  `LLM_BASE_URL` — this was always provider-agnostic by design.
- No other security corrections identified — the existing model (static
  bearer token, parameterized SQL, file validation, citation-spoofing
  defense) doesn't depend on provider choice.

---

## 11. Database Corrections

Only one: CORRECTION-004 (`embedding VECTOR(384)` instead of `VECTOR(1536)`)
in the initial migration. No other schema, index, or versioning changes are
needed — nothing else in `DATABASE_SCHEMA.md` was provider- or
embedding-model-dependent.

---

## 12. API Corrections

None required. `API_CONTRACT.md`'s endpoint shapes never exposed provider
or embedding-model details to the frontend — this was already correctly
encapsulated behind the backend, so no contract changes follow from any
correction in this document.

---

## 13. Testing Corrections

Add to `TESTING_STRATEGY.md`:

| Test | Expected |
|---|---|
| Provider failover | Mock primary returning HTTP 429 → fallback provider is called and its response used |
| Local embedding, no network | Ingestion succeeds with network access to any embedding API blocked |
| Embedding dimension | Inserting an embedding from the real `embed()` function succeeds against the migrated schema |
| Both providers, malformed JSON | Retry-then-fallback-then-failure-state path triggers correctly when both primary and fallback return unparseable output |

These are additions to the existing test matrix, not replacements for
anything already specified there.

---

## 14. 36-Hour Scope Corrections

### MUST BUILD
- CORRECTION-001 (LLM provider abstraction) — build this as part of
  TASK-011/012, not as a separate later task; it's foundational to every
  generation/validation task.
- CORRECTION-002 (local embeddings) — build as part of TASK-007.
- CORRECTION-004 (schema dimension fix) — must land in the initial
  migration, TASK-002, before any other task depends on it.

### SHOULD BUILD
- CORRECTION-003 (automatic fallback) — meaningfully improves demo
  reliability for low implementation cost, but the system is still
  functional (just less resilient to a single provider's rate limit)
  without it if the team is genuinely out of time.

### CUT IF BEHIND
- Do not build a third/fourth adapter for a provider not in Section 2's
  primary/fallback/emergency list — if OpenRouter's emergency path is
  never reached in practice, that's fine; it doesn't need dedicated code
  beyond the same generic adapter already handling Groq/Gemini.

---

## 15. Final Coding-Agent Instructions

- Read all 15 existing control-plane files first, per `AGENTS.md`.
- Read this file, `CORRECTIONS.md`, next.
- **`CORRECTIONS.md` overrides any conflicting provider, environment
  variable, or embedding-dimension assumption in the older 15 documents** —
  specifically: any mention of Anthropic as the default/sole provider, and
  any mention of `EMBEDDING_DIMENSION=1536` or `VECTOR(1536)`.
- Everything in the 15 original documents that this file does not
  explicitly correct remains fully in force, unchanged.
- Do not rewrite unrelated architecture on the strength of this document —
  it authorizes exactly the corrections numbered above, nothing broader.
- Do not introduce a fourth LLM adapter, a vector database change, or any
  other infrastructure beyond what's specified here.
- Do not hardcode `groq` or `gemini` anywhere outside `.env` and
  `config.py` — all provider specifics stay in configuration, never in
  business logic, per CORRECTION-001's entire point.
- Do not expose API keys in logs, error messages, or committed files.
- Do not weaken any existing test to accommodate a provider change — add
  the new tests in Section 13 alongside the existing suite.
- Stop after completing the assigned task, per `AGENTS.md`'s existing loop.

**Implementation order relative to `TASKS.md`:**
1. Apply CORRECTION-004 while implementing TASK-002 (initial migration).
2. Apply CORRECTION-002 while implementing TASK-007 (embeddings).
3. Apply CORRECTION-001 while implementing TASK-011 (first LLM call) — build
   the shared `LLMProvider` once here; TASK-012/015/017 (the other three
   LLM calls) reuse it directly, no rework needed.
4. Apply CORRECTION-003 opportunistically during TASK-011–017, or as a
   should-have pass afterward if time allows.
5. Add Section 13's tests alongside each corresponding task, not as a
   separate batch at the end.
