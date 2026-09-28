# DEFINITION_OF_DONE.md — When a Feature Is Actually Complete

A feature is not done because it "works" in one manual click-through. Every
item below must be true before a task in `TASKS.md` is marked complete.

## The checklist

- [ ] **Implementation matches the control-plane contract.** The code does
  exactly what `ARCHITECTURE.md` / `DATABASE_SCHEMA.md` / `API_CONTRACT.md` /
  `AI_RAG_DESIGN.md` specify for this piece — no silent deviation, no
  "improvement" that wasn't asked for.
- [ ] **Tests exist and pass.** At minimum the test(s) named in the task's
  `TASKS.md` entry and in `TESTING_STRATEGY.md`. Tests were actually run, not
  assumed to pass.
- [ ] **Validation is real, not faked.** If the task involves an LLM call or
  any external input, the Pydantic schema validation, retry, and failure-state
  behavior from `AI_RAG_DESIGN.md`/`RULES.md` are actually implemented — not
  stubbed to always succeed.
- [ ] **Error handling is explicit.** No bare `except:`, no silently swallowed
  exception, no path that returns a misleading success on failure.
- [ ] **Logging is present** where `RULES.md` requires it (LLM call outcomes,
  `audit_events` writes on state transitions).
- [ ] **No secrets, no hardcoded config** that belongs in `ENVIRONMENT.md`'s
  environment variables.
- [ ] **Security requirements met** for this piece — e.g., if this task
  touches document content passed to an LLM, the `<UNTRUSTED_EVIDENCE>`
  wrapping pattern from `SECURITY.md` is actually used.
- [ ] **Integrated, not just isolated.** The feature works when called through
  the real pipeline/UI it belongs to, not only in isolation against a mock —
  confirmed at minimum by the hour-16 checkpoint or the Phase 10 integration
  pass, whichever applies.
- [ ] **Documentation reflects reality.** If this task changed a schema, API
  shape, or architectural detail, the relevant control-plane file was updated
  in the same PR, in its own commit (per `GIT_WORKFLOW.md`).
- [ ] **Acceptance criteria from `TASKS.md` are met, literally.** Not "close
  enough" — the exact stated criteria.

## What "done" explicitly does NOT mean

- It does not mean "I clicked through it once and it looked right."
- It does not mean "the happy path works" — the defined failure states for
  this component (from `ARCHITECTURE.md`'s failure states table) must also
  behave as specified, at least for the ones covered by this task's tests.
- It does not mean the code is optimized or production-hardened beyond what
  `ARCHITECTURE.md` and `SECURITY.md` actually require for this prototype.

## Task-type-specific additions

**LLM-call tasks** additionally require: a mocked-malformed-response test
proving the retry-then-failure-state path actually triggers, not just a
mocked-valid-response happy path.

**Deterministic validation tasks** (citation validator, sufficiency engine,
contradiction pre-filter) additionally require: at least one test proving the
*rejection* path works, not only the acceptance path — e.g., the citation
validator test suite must include an invalid-code case, not only a valid one.

**Frontend tasks** additionally require: the component renders correctly
against the exact response shape in `API_CONTRACT.md`, including at least one
non-happy-path state (e.g., `INSUFFICIENT` sufficiency, a non-`COMPATIBLE`
contradiction) — not only the cleanest-looking mock data.

**Database/migration tasks** additionally require: the migration was tested
applying to a genuinely empty database, not just a database that already had
a prior manual schema change applied by hand.

## Who checks this

Given the 3-person/36-hour constraint, self-review against this checklist is
acceptable — but it must actually happen, explicitly, before a `TASKS.md`
status is set to done. A task marked done that later turns out to violate
this checklist is treated as a bug, not a style nitpick — see `RULES.md` rule
#17 (no fake implementations left in place).
