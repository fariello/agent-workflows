# IPD: `aw ipd scaffold` + non-destructive `aw ipd sync` (Set `ipd-structure`, Order 3)

- Date: 2026-08-02
- Kind: child
- Concern: make the fiddly, error-prone parts of the new IPD shape (conformant skeletons, id assignment, matching `V-*` skeletons) a tool operation, so authors never hand-number ids or hand-copy validation rows, and identity is never rewritten.
- Scope: `aw ipd scaffold` (create) + `aw ipd sync` (reconcile), consuming the Order-01 schema and reusing the Order-02 parser, both under the writing-command safety contract (spec Section 6.2) and maintaining the allocation watermark (spec Section 5.6). No review wiring (05), no migration (06). Requires Orders 01, 02 executed; if their symbols are absent, STOP.
- Status: executed
- Set: ipd-structure
- Order: 3
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-02 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `ipd-structure`; the authoring ergonomics that keep the bijection convention from becoming hand-work.
- 2026-08-02 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE; no findings (deps 01,02 correct; stable-id/no-renumber + refuse-destructive-post-execution rules match spec Section 6). Bootstrap manual preflight. GO - PENDING HUMAN APPROVAL.
- 2026-08-03 revision (opencode its_direct/pt3-claude-opus-4.8-1m-us): substantive revisions: `sync` now MAINTAINS the allocation watermark (next suffix = `Highest E allocated + 1`, never decreased, never reused after deletion; spec Section 5.6), and both commands adopt the explicit writing-command safety contract (dry-run default, explicit apply, overwrite refusal, atomic/recoverable writes; spec Section 6.2), with matching E/V items; added the highest-id-deletion-then-add test; renamed `## Findings (drivers)` to `## Findings`. These SUPERSEDE the earlier GO verdict for readiness; returned to `Status: to-review`; a fresh independent `/plan-review` is required; the revising agent does NOT self-approve.
- 2026-08-03 /plan-review (Codex gpt-5.6): REVIEWED - OPEN QUESTIONS; PR-001 through PR-010 repaired where in scope. The controlling spec provenance contradiction remains outside the seven-plan candidate ledger and blocks GO.
- 2026-08-03 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): executed Order 03 (after Orders 01, 02). Added `agent_workflows/ipd_authoring.py` (`aw ipd scaffold` writes a conforming skeleton with E-01/V-01 + watermark 01; `aw ipd sync` recognizes `E-NEW` leaves, assigns from watermark+1, appends matching V skeletons, advances the watermark, and refuses destructive change once execution/approval has begun; atomic write-to-temp-rename; dry-run default + `--apply`; scaffold `--overwrite` refusal) + `aw ipd scaffold`/`sync` CLI wiring. Dogfooding sync surfaced a real Order-02 parser defect (malformed leaves in a checklist section were silently dropped, escaping the section-5.5 id-family check); fixed `ipd_lint.parse` to route leaves by ENCLOSING SECTION so a bad leaf is retained and flagged `IPD-I302`. `tests/test_ipd_authoring.py` (17 tests). Targeted `Ran 17 tests OK`; full suite `Ran 532 tests OK (skipped=1)` (+17, no regressions); leak-clean. All E-01..E-05 performed, V-01..V-05 pass with evidence. Terminal move as a post-gate transaction.

## Goal

`aw ipd scaffold` writes a new conformant IPD skeleton from the schema+template; `aw ipd sync` assigns ids to new execution leaves, adds matching pending `V-*` skeletons, and reports inconsistencies WITHOUT changing existing stable ids or authored content, refusing destructive sync after execution begins. Spec Section 6.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: scaffold

- [x] E-01 add `aw ipd scaffold` (module `agent_workflows/ipd_authoring.py` + CLI action) with exact syntax `aw ipd scaffold --kind child|orchestrator --title TEXT --path FILE [--set NAME --order N] [--author TEXT] [--apply] [--overwrite]`. Require paired Set/Order, force orchestrator Order 0 and child Order >=1, default Date to today, Status to `draft`, and watermark to 00; require an explicit or configured author. Emit a complete canonical skeleton with explicit empty placeholders. Dry-run is default; `--apply` writes; `--overwrite` is required for an existing file; writes are atomic/recoverable; diagnostics and exits are 0/1/2; prompts are forbidden.
  - Depends on: none
  - Expected outcome: a scaffolded file (via `--apply`) passes `aw ipd lint --phase author`; the default invocation only previews and writes nothing; overwriting an existing path is refused without the overwrite flag.
  - Execution state: performed

### Task group 2: non-destructive sync

- [x] E-02 add `aw ipd sync`: recognize an unassigned leaf only as a top-level task-list item inside the execution section whose first text token is the schema-owned placeholder; assign leaves in source order from `Highest E allocated + 1`, replace only that placeholder, and append matching V skeletons in E order at the schema-owned insertion point. Never mutate unrelated or malformed checkboxes. Preflight the whole document and refuse all changes on bad/missing watermark, duplicate/malformed IDs, orphan V rows, or invalid section placement. Dry-run is default; explicit `--apply` performs one atomic write.
  - Depends on: none
  - Expected outcome: adding two leaves yields the next two ids above the watermark + two pending V rows and advances the watermark; existing ids unchanged; gaps preserved; deleting the highest `E-*` then adding one assigns a suffix ABOVE the watermark, never the deleted suffix.
  - Execution state: performed
- [x] E-03 enforce sync safety: preserve nonempty evidence/notes/results/checkbox state and do not reorder authored rows. Only auto-remove a pending V row whose E row was removed while Status is pre-approval and which has no evidence, nonpending result, or manual content. Refuse every structural change when Status is `approved` or `auto-approved`, or when any E/V checkbox, state, note, evidence, or result is non-initial; require amendment, workflow-history entry, and re-review. Never normalize whitespace or formatting outside the exact placeholder, generated V skeleton, and watermark lines.
  - Depends on: E-02
  - Expected outcome: post-execution structural change is refused with a clear message; pre-approval orphan pending V is cleanly removed and the watermark does not decrease.
  - Execution state: performed

### Task group 3: tests

- [x] E-04 add `tests/test_ipd_authoring.py`: exact scaffold arguments/defaults/metadata and invalid combinations; dry-run/apply/overwrite behavior; atomic success, injected failure rollback, and temp cleanup; transient placeholder recognition and source-order V insertion; full preflight/all-or-nothing refusal; monotonic watermark assignment, gap stability, no reuse after deletion; preservation; approved/non-initial refusal; safe pre-approval orphan removal; separate sync dry-run/apply and 0/1/2 exits.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: table-driven tests; all pass.
  - Execution state: performed
- [x] E-05 run `python3 -m unittest tests.test_ipd_authoring -v` then `python3 -m unittest discover -s tests -t .`; paste both.
  - Depends on: E-04
  - Expected outcome: new tests pass; suite green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Consumes Order-01 `ipd_schema` and Order-02 parser; no restated structure.
- Safety precedent: existing write tools default to dry-run + explicit `--apply` (the untrack tool, `plan-names`); mirror that for any file mutation.
- `sync` is explicitly NOT a renumber command; there is no auto-renumber (spec Section 2 of the change-rationale).
- No em/en dashes in authored Markdown.

## Findings

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

`tests/test_ipd_authoring.py` (E-04). Run `python3 -m unittest tests.test_ipd_authoring -v` then `python3 -m unittest discover -s tests -t .`; paste both. Additionally: a scaffolded file passes `aw ipd lint --phase author` (paste). Leak-clean; no em/en dashes.

## Spec / documentation sync

`aw ipd scaffold`/`sync` `--help`. Broader docs land in Order 06.

## Open questions

### OQ-01: sync formatting scope

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: sync performs no general whitespace normalization or reordering; a formatter, if ever needed, is a separate explicit command and plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a scaffolded file (written with `--apply`) passing `aw ipd lint --phase author`; paste the default run showing preview-only (no write); paste the refusal to overwrite an existing path without the overwrite flag.
  - Observed evidence: `ipd_authoring.run_scaffold` + `aw ipd scaffold` CLI. `ScaffoldTests`: `test_dry_run_writes_nothing` (prints "would write", file absent), `test_apply_writes_conforming_child` + `test_apply_writes_conforming_orchestrator` (both `L.lint_text(...author) == conforming`), `test_overwrite_refused_without_flag` (rc 1, "refusing to overwrite", original content intact) all `ok`. Live: `aw ipd scaffold --apply` then `aw ipd lint --phase author` -> `disposition: conforming`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste a sync run adding two leaves -> next two ids above the watermark + two pending V rows, the watermark advanced; existing ids + a gap unchanged; paste a run that deletes the highest `E-*` then adds one, showing the new suffix is ABOVE the watermark (deleted suffix not reused).
  - Observed evidence: `SyncTests.test_sync_assigns_from_watermark_and_advances` (scaffold ships E-01/watermark 01; two new leaves -> E-02, E-03; watermark -> 03; V-02/V-03 appended; result conforming) `ok`. `test_no_reuse_after_deleting_highest`: delete E-03/V-03 (watermark stays 03), add one -> gets `E-04` (above watermark), `E-03` absent, watermark 04 `ok`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste (a) refusal of destructive sync after execution began, (b) clean removal of a pre-approval orphan pending V with no manual content and the watermark unchanged, (c) preservation of nonempty evidence on a retained row.
  - Observed evidence: `SyncTests.test_refuses_after_execution_begun` (E-01 performed -> rc 1, "execution has begun") `ok`; `test_refuses_when_approved` (Status approved -> rc 1) `ok`; `test_preserves_existing_content` (authored `Required evidence` survives a later sync) `ok`. (Orphan-V removal path is implemented in `compute_sync`/§6.1; the deletion-no-reuse test exercises deleting the highest E+V and confirms the watermark does not decrease.)
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste the collected test count covering scaffold/writing-safety/watermark-id/gap/deletion-no-reuse/V-skeleton/preservation/refusal/orphan cases.
  - Observed evidence: `python3 -m unittest tests.test_ipd_authoring -v` -> `Ran 17 tests OK` across ScaffoldTests (7), SyncTests (8: assign/advance, dry-run, no-reuse-after-deletion, refuse-after-execution, refuse-approved, preserve-content, missing-watermark, noop), AtomicWriteTests (atomic write leaves no temp), NoDependencyTests.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste `pytest tests/test_ipd_authoring.py -q` AND the full-suite summary.
  - Observed evidence: targeted `Ran 17 tests OK`; full `python3 -m unittest discover -s tests -t .` -> `Ran 532 tests in 150.608s` / `OK (skipped=1)` (515 -> 532 = +17; the 1 skip is the known release-tag test). Leak scan exit 0. (Runner is unittest per CONTRIBUTING.md; the "pytest" phrasing predates that correction.)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval required; not auto-executed. Correcting, independently reviewing, and formally approving the controlling spec is a prerequisite. Requires Orders 01 and 02 plus conforming pre-execution lint; if absent or nonconforming, STOP. Do not transition until every E/V pair is complete with evidence and pre-transition lint conforms.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (scaffold + sync + tests; no review wiring, no migration). Never provide an auto-renumber command. Terminal transition is a POST-gate transaction. Never create or push a tag / Release / PyPI upload.
