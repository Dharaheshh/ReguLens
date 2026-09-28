# GIT_WORKFLOW.md — Branching, Commits, PRs for a 3-Person, 36-Hour Build

## Branch strategy

```
main                          — always deployable, demo-ready at every merge
├─ feat/ingestion              — Person A
├─ feat/retrieval               — Person A
├─ feat/generation                — Person B
├─ feat/validation                  — Person B
├─ feat/frontend-library              — Person C
├─ feat/frontend-workspace              — Person C
└─ feat/integration                       — Person C (late-stage, merges everything)
```

Branch per layer/feature, not per person for the whole hackathon — a person
moves to a new branch when they move to a new task from `TASKS.md`.

## Branch naming

`feat/<short-description>` for new functionality, `fix/<short-description>`
for bug fixes, `docs/<short-description>` for control-plane document changes
only (never mixed with application code — see `RULES.md` Git rules).

## Commit conventions

```
<type>(<scope>): <short description>

<optional body — what changed and why, if not obvious>

Refs: TASK-ID
```

Types: `feat`, `fix`, `test`, `docs`, `chore`, `refactor` (refactor commits
must stay within the current task's scope — no drive-by refactoring, per
`AGENTS.md`).

Examples:
```
feat(ingestion): implement PDF parsing with page preservation

Refs: TASK-003
```
```
fix(citation-validator): reject citation when evidence_code has no DB match

Refs: TASK-014
```

## PR conventions

- Every PR targets `main`, from a `feat/*` or `fix/*` branch.
- PR description includes: what changed, which `TASKS.md` ID(s) it closes,
  what was tested and how.
- A PR that touches a control-plane document (schema, API contract,
  architecture) must call this out explicitly in the description, even if
  it's a one-line schema addition — these changes affect all three people's
  work and must be visible.
- Self-review is acceptable given the 3-person/36-hour constraint, but the
  PR must still include a completed checklist (tests written, tests passing,
  acceptance criteria met) before merging — see `DEFINITION_OF_DONE.md`.

## Merge strategy

- Squash merge to `main` — keeps history readable given the volume of
  iterative commits expected from agent-assisted development.
- Merge frequently, in small increments. Do not let a branch diverge from
  `main` for more than a few hours during the 36-hour window — integration
  risk compounds with time.

## Avoiding merge conflicts across 3 people

- The layer split (ingestion+retrieval / generation+validation /
  frontend+integration) is chosen specifically so each person's primary
  files rarely overlap with another's.
- The one shared file every person edits is `DATABASE_SCHEMA.md` (via
  migrations) and `API_CONTRACT.md` — changes to these are called out in
  the team's channel immediately when made, not discovered via merge
  conflict. Treat these two files as requiring a quick heads-up before
  changing, even without formal review process.
- Migrations are additive wherever possible during the hackathon (add a
  column/table) rather than destructive (rename/drop), to minimize conflict
  surface between two people's migration files landing close together.

## Revert strategy

If a merge to `main` breaks the build or a demo-critical path: revert
immediately (`git revert`, not a manual undo), then re-diagnose on a fresh
branch. Do not leave `main` broken while debugging — the 36-hour clock means
someone else may need to build on `main` at any moment.

## Tags

Tag the commit used for the final demo as `demo-final` once the team commits
to not touching `main` further before presenting. This gives an unambiguous
fallback if last-minute changes destabilize anything.

## Checkpoint discipline

At the hour-16 mark (per `IMPLEMENTATION_PLAN.md`), all three branches
merge to `main` regardless of individual completeness, specifically to run
the full pipeline end-to-end at least once. This is a deliberate, planned
integration point — not an accident of convenience.
