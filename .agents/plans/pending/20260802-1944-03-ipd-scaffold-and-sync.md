# IPD: `aw ipd scaffold` + non-destructive `aw ipd sync` (Set `ipd-structure`, Order 3)

- Date: 2026-08-02
- Kind: child
- Concern: make the fiddly, error-prone parts of the new IPD shape (conformant skeletons, id assignment, matching `V-*` skeletons) a tool operation, so authors never hand-number ids or hand-copy validation rows, and identity is never rewritten.
- Scope: `aw ipd scaffold` (create) + `aw ipd sync` (reconcile), consuming the Order-01 schema and reusing the Order-02 parser. No review wiring (05), no migration (06). Requires Orders 01, 02 executed; if their symbols are absent, STOP.
- Status: reviewed
- Set: ipd-structure
- Order: 3
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-02 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `ipd-structure`; the authoring ergonomics that keep the bijection convention from becoming hand-work.
- 2026-08-02 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE; no findings (deps 01,02 correct; stable-id/no-renumber + refuse-destructive-post-execution rules match spec Section 6). Bootstrap manual preflight. GO - PENDING HUMAN APPROVAL.

## Goal

`aw ipd scaffold` writes a new conformant IPD skeleton from the schema+template; `aw ipd sync` assigns ids to new execution leaves, adds matching pending `V-*` skeletons, and reports inconsistencies WITHOUT changing existing stable ids or authored content, refusing destructive sync after execution begins. Spec Section 6.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: scaffold

- [ ] E-01 add `aw ipd scaffold` (module `agent_workflows/ipd_authoring.py` + CLI action): create a new conformant skeleton (canonical headings in order for the chosen kind, empty checklists, size-assessment block, no-open-questions marker) from the Order-01 schema.
  - Depends on: none
  - Expected outcome: a scaffolded file passes `aw ipd lint --phase author`.
  - Execution state: pending

### Task group 2: non-destructive sync

- [ ] E-02 add `aw ipd sync`: assign the next unused suffix to each new execution leaf (monotonic, never renumber existing), generate a matching pending `V-NN` skeleton for each new `E-NN`, and report inconsistencies.
  - Depends on: none
  - Expected outcome: adding two leaves yields the next two ids + two pending V rows; existing ids unchanged; gaps preserved.
  - Execution state: pending
- [ ] E-03 enforce sync safety: preserve nonempty evidence/notes/results/checkbox state; do not reorder authored rows; only auto-remove a pending `V-*` whose matching `E-*` was removed BEFORE approval and which has no observed evidence/nonpending result/manual content; REFUSE destructive sync after execution began (require the amendment/re-review workflow + a workflow-history entry).
  - Depends on: E-02
  - Expected outcome: post-execution structural change is refused with a clear message; pre-approval orphan pending V is cleanly removed.
  - Execution state: pending

### Task group 3: tests

- [ ] E-04 add `tests/test_ipd_authoring.py`: scaffold conformance, monotonic id assignment, gap stability, V-skeleton generation, evidence/state preservation, refusal after execution, pre-approval orphan removal.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: table-driven tests; all pass.
  - Execution state: pending
- [ ] E-05 run `python -m pytest tests/test_ipd_authoring.py -q` then the full suite; paste both.
  - Depends on: E-04
  - Expected outcome: new tests pass; suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Consumes Order-01 `ipd_schema` and Order-02 parser; no restated structure.
- Safety precedent: existing write tools default to dry-run + explicit `--apply` (the untrack tool, `plan-names`); mirror that for any file mutation.
- `sync` is explicitly NOT a renumber command; there is no auto-renumber (spec Section 2 of the change-rationale).
- No em/en dashes in authored Markdown.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C3-1 | HIGH | Medium | maintainer | usability | Hand-numbering ids + hand-copying V rows is exactly the error-prone work the tool must absorb. | spec Section 6 |
| C3-2 | HIGH | Medium | integrity | correctness | Renumbering would invalidate `Depends on:`, `V-* validates E-*`, review comments, and in-flight state; ids must be stable. | change-rationale Section 2 |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | C3-1 | `scaffold` | `agent_workflows/ipd_authoring.py`, `agent_workflows/cli.py` | Medium | E-01 |
| 2 | C3-1, C3-2 | non-destructive `sync` | `agent_workflows/ipd_authoring.py` | Medium | E-02, E-03 |
| 3 | all | tests | `tests/test_ipd_authoring.py` | Low | E-04, E-05 |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | n/a | scope | A cosmetic-compaction/renumber migration is explicitly NOT provided (forbidden after review/execution). | Not planned |

## Scope check

- Over-scope: none - scaffold + sync + tests.
- Under-scope: MUST keep ids stable/monotonic, generate matching V skeletons, preserve authored content, and refuse destructive post-execution sync.

## Required tests / validation

`tests/test_ipd_authoring.py` (E-04). Run `python -m pytest tests/test_ipd_authoring.py -q` then `python -m pytest -q`; paste both. Additionally: a scaffolded file passes `aw ipd lint --phase author` (paste). Leak-clean; no em/en dashes.

## Spec / documentation sync

`aw ipd scaffold`/`sync` `--help`. Broader docs land in Order 06.

## Open questions

### OQ-01: sync formatting scope

- Blocking: no
- Status: deferred
- Owner: this child
- Resolution or deferral rationale: whether `sync` may perform any whitespace normalization is decided here; default is to touch only id/V-skeleton lines and never reorder authored rows.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a scaffolded file passing `aw ipd lint --phase author`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a sync run adding two leaves -> next two monotonic ids + two pending V rows; existing ids + a gap unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste (a) refusal of destructive sync after execution began, (b) clean removal of a pre-approval orphan pending V with no manual content, (c) preservation of nonempty evidence on a retained row.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the collected test count covering scaffold/id/gap/V-skeleton/preservation/refusal/orphan cases.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `pytest tests/test_ipd_authoring.py -q` AND the full-suite summary.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval required; not auto-executed. Requires Orders 01, 02; if absent, STOP. After Order 02, this file SHOULD be linted with the real `aw ipd lint`. Do NOT claim done or move to `executed/` until every `E-*` is `performed`+checked AND its matching `V-*` is `pass`+checked with nonempty observed evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (scaffold + sync + tests; no review wiring, no migration). Never provide an auto-renumber command. Terminal transition is a POST-gate transaction. Never create or push a tag / Release / PyPI upload.
