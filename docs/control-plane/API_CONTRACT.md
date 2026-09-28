# API_CONTRACT.md — Backend REST Contract

This is the single source of truth for every endpoint shape. Frontend and
backend both build against this file — neither invents a separate schema. If
an endpoint needs a change, update this file first, in its own commit (see
`RULES.md` Git rules).

All request/response bodies are JSON. All endpoints are versioned under `/api/v1`.

Auth: lightweight — a single `Authorization: Bearer <token>` header, validated
against one static demo token for the hackathon (see `SECURITY.md`). Every
endpoint below requires it unless marked `AUTH: none`.

## Standard error format

```json
{
  "error": {
    "code": "CITATION_NOT_FOUND",
    "message": "Human-readable description",
    "details": {}
  }
}
```

Validation errors (malformed request body) use FastAPI's default 422 format.
Business-logic outcomes (e.g., `INSUFFICIENT_EVIDENCE`) are **not** errors —
they are valid 200 responses; see `ARCHITECTURE.md` failure states table for
which states are errors vs. valid outcomes.

---

## Documents

### `POST /api/v1/documents`
Upload a new document (creates `documents` + first `document_versions` row).

**Request:** `multipart/form-data`
- `file`: the PDF
- `doc_type`: string (`scientific_paper` | `regulatory_guidance` | `internal_study` | `prior_response`)
- `jurisdiction`: string, optional
- `is_synthetic`: boolean, default `true`

**Response `201`:**
```json
{
  "document_id": "uuid",
  "version_id": "uuid",
  "version_number": 1,
  "status": "processing"
}
```
**Side effects:** triggers ingestion (parse → chunk → embed → store), runs
synchronously — request blocks until ingestion completes or fails.

**Errors:** `400 INVALID_FILE_TYPE`, `422` validation, `500 INGESTION_FAILED`

### `POST /api/v1/documents/{document_id}/versions`
Upload a new version of an existing document.

**Request:** same as above, minus `doc_type`/`jurisdiction` (inherited).
**Response `201`:** same shape, `version_number` incremented, previous version
marked `superseded`.

### `GET /api/v1/documents`
List documents.

**Query params:** `doc_type`, `jurisdiction` (optional filters)
**Response `200`:**
```json
{
  "documents": [
    {"document_id": "uuid", "filename": "...", "doc_type": "...", "jurisdiction": "...",
     "current_version_number": 2, "is_synthetic": true, "created_at": "iso8601"}
  ]
}
```

### `GET /api/v1/documents/{document_id}`
Get one document with its version history.

**Response `200`:**
```json
{
  "document_id": "uuid", "filename": "...", "doc_type": "...",
  "versions": [
    {"version_id": "uuid", "version_number": 1, "status": "superseded", "uploaded_at": "iso8601"},
    {"version_id": "uuid", "version_number": 2, "status": "current", "uploaded_at": "iso8601"}
  ]
}
```

---

## Regulatory Queries

### `POST /api/v1/queries`
Submit a regulator question and run the full pipeline (stages 1–11 of the
canonical lifecycle in `ARCHITECTURE.md`) synchronously.

**Request:**
```json
{ "query_text": "Provide evidence supporting the microbiological safety..." }
```

**Response `200`:**
```json
{
  "query_id": "uuid",
  "response_id": "uuid",
  "draft_text": "...",
  "sufficiency_status": "PARTIALLY_SUFFICIENT",
  "gap_summary": "REQ-02 (production controls) is only partially covered...",
  "requirements": [
    {"req_code": "REQ-01", "description": "...", "status": "COVERED"},
    {"req_code": "REQ-02", "description": "...", "status": "PARTIALLY_COVERED"}
  ],
  "claims": [
    {
      "claim_id": "uuid", "claim_code": "CLM-0042", "claim_text": "...",
      "validation_state": "SUPPORTED",
      "citations": [
        {"evidence_id": "uuid", "evidence_code": "EVD-01872", "document": "...",
         "page_start": 14, "page_end": 14, "section": "4.2"}
      ]
    }
  ],
  "contradictions": [
    {"contradiction_id": "uuid", "claim_a": {"...": "..."}, "claim_b": {"...": "..."},
     "classification": "POTENTIAL_CONTRADICTION", "reasoning": "..."}
  ],
  "status": "draft"
}
```

**Errors:** `500 LLM_FAILED`, `500 RETRIEVAL_FAILED` (per-requirement failures
are embedded in the `requirements` array as `NOT_COVERED`, not top-level
errors)

### `GET /api/v1/queries/{query_id}`
Retrieve a previously run query and its latest response, same shape as above.

---

## Responses (Review)

### `GET /api/v1/responses/{response_id}`
Full detail view for the review screen — same shape as the `POST /queries`
response body.

### `PATCH /api/v1/responses/{response_id}`
Edit the draft text before approval.

**Request:** `{ "draft_text": "edited text" }`
**Response `200`:** updated response object.

### `POST /api/v1/responses/{response_id}/approve`
Human approval action.

**Request:** `{ "reviewed_by": "reviewer name or id" }`
**Response `200`:**
```json
{ "response_id": "uuid", "status": "approved", "version": 1, "reviewed_at": "iso8601" }
```
**Side effects:** sets `status = 'approved'`, `reviewed_by`, `reviewed_at`;
writes an `audit_events` row with `event_type = 'response_approved'`; the
response's claims become eligible as future contradiction-check candidates.

### `POST /api/v1/responses/{response_id}/reject`
**Request:** `{ "reviewed_by": "...", "reason": "optional text" }`
**Response `200`:** `{ "response_id": "uuid", "status": "rejected" }`
**Side effects:** writes `audit_events` row `event_type = 'response_rejected'`.
No auto-resubmission is triggered.

---

## Evidence

### `GET /api/v1/evidence/{evidence_id}`
Full source detail for the citation viewer (click-through).

**Response `200`:**
```json
{
  "evidence_id": "uuid", "evidence_code": "EVD-01872",
  "document_id": "uuid", "document_filename": "...",
  "document_version_number": 2, "page_start": 14, "page_end": 14,
  "section": "4.2", "source_type": "internal_study",
  "content": "the full chunk text"
}
```

---

## Contradictions

### `GET /api/v1/contradictions?resolved=false`
List unresolved contradictions across all responses (for a dashboard/panel
view).

### `POST /api/v1/contradictions/{contradiction_id}/resolve`
Human marks a contradiction as reviewed/resolved (does not change the
underlying claims — purely a review-tracking action).

**Request:** `{ "reviewed_by": "...", "resolution_note": "optional text" }`
**Response `200`:** `{ "contradiction_id": "uuid", "resolved": true }`
**Side effects:** `audit_events` row `event_type = 'contradiction_resolved'`.

---

## Audit Trail

### `GET /api/v1/responses/{response_id}/audit`
**Response `200`:**
```json
{
  "events": [
    {"event_type": "response_approved", "actor": "...", "payload": {},
     "created_at": "iso8601"}
  ]
}
```

---

## Health

### `GET /api/v1/health`
`AUTH: none`. Returns `{"status": "ok"}`. Used for Docker healthcheck and
smoke testing.
