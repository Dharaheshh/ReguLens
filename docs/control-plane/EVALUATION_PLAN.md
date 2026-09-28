# EVALUATION_PLAN.md — AI Evaluation Harness

A small, credible evaluation harness — sized for a 36-hour hackathon, not a
production benchmark. 10–15 curated cases, chosen to directly exercise the
three killer demo capabilities, are sufficient. This is explicitly scoped down
from a 50-case ideal per the approved architecture contract.

## Golden dataset structure

Each case is a fixture: a query, the seeded corpus it runs against, and the
expected outcome. Stored as a JSON file per case under
`data/eval/golden_cases/`.

```json
{
  "case_id": "GC-01",
  "category": "answerable",
  "query_text": "Provide evidence supporting the microbiological safety of the cultivated-cell product.",
  "expected_evidence_codes": ["EVD-00012", "EVD-00034"],
  "expected_sufficiency": "SUFFICIENT",
  "expected_contradiction": null,
  "notes": "Baseline answerable case, no traps."
}
```

## Case categories and minimum counts (12 total for the hackathon)

| Category | Count | Purpose |
|---|---|---|
| Answerable | 3 | Baseline — confirms the pipeline works cleanly end to end |
| Insufficient evidence | 2 | Exercises demo scenario C — must include the long-term-toxicity case exactly as described in `PROJECT_CONTEXT.md` |
| Contradiction — true positive | 2 | Exercises demo scenario B — planted genuine conflicts |
| Contradiction — false positive check | 2 | Same product/topic, different threshold/units/version — must classify `COMPATIBLE`, proves the system doesn't over-trigger |
| Citation grounding | 2 | Confirms every citation in the response resolves to real, correct evidence |
| Overclaim | 1 | The worked "1 of 100 below threshold" vs. "no contamination detected" case |

## Metrics

| Metric | Definition | How measured |
|---|---|---|
| Recall@5 | Of the expected evidence codes for a case, fraction found in the top-5 retrieved chunks | Compare retrieved evidence codes against `expected_evidence_codes` per case |
| Recall@10 | Same, top-10 | Same |
| Citation validity | Fraction of citations in generated responses that resolve to a real `evidence` row | Automatic — count `citations.validated=true` / total proposed citations across the eval run |
| Unsupported claim rate | Fraction of claims with `validation_state = UNSUPPORTED` | Automatic from `claims` table after eval run |
| Overclaim detection | Does the overclaim case correctly classify as `OVERCLAIM`? | Pass/fail against `GC` overclaim case |
| Contradiction precision | Of cases classified non-`COMPATIBLE`, fraction that were true planted contradictions | Manual comparison against the 2 false-positive-check cases + 2 true-positive cases |
| Contradiction recall | Of the 2 true planted contradictions, fraction actually caught | Same |
| Sufficiency accuracy | Does each case's actual `sufficiency_status` match `expected_sufficiency`? | Pass/fail per case |

## What "success" looks like for the demo

- Recall@5 ≥ 0.8 across the answerable + citation-grounding cases (retrieval
  is finding the right evidence most of the time)
- Citation validity = 1.0 (no invalid citation should ever surface — this one
  is non-negotiable, since it's the core "we don't hallucinate citations"
  claim)
- The 2 true-positive contradiction cases are both caught (contradiction
  recall = 1.0 on this small set)
- The 2 false-positive-check cases are both classified `COMPATIBLE` (proves
  the system isn't just flagging everything that looks similar)
- Both insufficient-evidence cases correctly return `INSUFFICIENT`

These numbers, even from a 12-case set, are real, measured, and honestly
reportable to a judge — which is the entire point: a small measured result
beats an unmeasured claim of quality.

## Running the eval

A single script, `scripts/run_eval.py`, iterates the golden cases, calls
`POST /queries` for each, compares actual vs. expected fields, and prints a
summary table plus writes a JSON results file. This should be run at least
once before the hour-16 integration checkpoint (even with a subset of cases
seeded) and again before the final demo rehearsal block (hours 34–36) to
catch any regression introduced during late changes.

## What is explicitly not attempted here

Formal statistical significance testing, cross-validation, or any evaluation
methodology beyond "does the system get these specific, deliberately chosen
cases right" — appropriate honesty for a 36-hour prototype evaluation, and
worth stating plainly if a judge asks how rigorous the evaluation is.
