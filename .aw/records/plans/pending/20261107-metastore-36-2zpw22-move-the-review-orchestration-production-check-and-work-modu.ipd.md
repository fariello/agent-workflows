# IPD: Move the review, orchestration, production-check and work module reads onto artifact_meta

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` C5a requires every record module to read metadata through the cache. Measured 2026-11-07 at `ac76110f4`: the review modules read front matter with their own patterns (`review_findings._META_RE`, `artifact_audit._STATUS_LINE_RE`), the review sequence and tier modules through `ParsedDoc.meta_fields` and `ipd_schema.read_readiness`, `orchestrator_readiness` through `_BATCH_META_RE`, `production_checks` through five module-level `^-` regexes and `backlog.parse_item`, `work_cmd` through `_plan_id6`/`_plan_status`, and `artifact_adopt` through `_BULLET_ID_RE`. Part 4 of the split of `t4gl15` (Order 09).
- Scope: `t4gl15` E-11 (review findings, audit, review subject lookups) and E-12 (review sequence, tier, re-review, orchestrator readiness, production checks, work, adoption), whole. EXCLUDES: the gate, runner and plans/research/prompts modules (Orders 33 `h58z9n`, 34 `y97k46`, 35 `jd7874`); the WRITE half of `review_sequence.restore_pre_s7_plan` (Order 07); the `->reviewed` gate-only attestation rule (`2xwb9b`); the residual audit of these modules (`t4gl15` E-15).
- Scope-Paths: agent_workflows/review_findings.py, agent_workflows/artifact_audit.py, agent_workflows/reviews.py, agent_workflows/review_sequence.py, agent_workflows/review_tier.py, agent_workflows/review_rereview.py, agent_workflows/orchestrator_readiness.py, agent_workflows/production_checks.py, agent_workflows/work_cmd.py, agent_workflows/artifact_adopt.py, tests/test_readers_review_modules.py, tests/test_artifact_audit_verdicts.py, .aw/records/plans/pending/20261107-metastore-36-2zpw22-move-the-review-orchestration-production-check-and-work-modu.ipd.md
- Item-Dependencies: executed:ffceq0, executed:g5hpbb, executed:h58z9n, executed:tve77h, executed:xexn45
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 36
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 2zpw22

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from t4gl15 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

The review, audit, orchestration, production-check, work and adoption modules read metadata only through `artifact_meta.read`/`query`/`history` (or `artifact_meta.read_text` for in-memory snapshots), with each move pinned by a behavioral test before and after.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

The pin-first rule of `ffceq0` applies to every move here (carried from `t4gl15`): BEFORE the edit, a behavioral test pins the reader's current observable behavior and runs green on the unmodified code; AFTER the edit, the same test runs unchanged except where decision D-1 (copied below) names it. For every existing module named as a baseline, save the per-test outcome list under the gitignored `.aw/state/t4gl15/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/t4gl15/<E>-before.txt`) before the move and into `<E>-after.txt` after it, where `<E>` is the ORIGINAL `t4gl15` item id named below. Run a new module's `-k` selection as its own command. New test modules set `pytestmark = pytest.mark.core`; none reads production source.

### Task group 1: review and audit modules

- [ ] E-01 (carried from `t4gl15` E-11) Pin, then move, `review_findings` (`_META_RE` front-matter read in `parse_review_text`; the review body grammar of rounds and findings stays, N3), `artifact_audit` (`_STATUS_LINE_RE` in `read_declared_status`, which serves every artifact type, so D-1 normalization applies only when the record is a plan), `reviews` subject resolution (`reviews._resolve_selector_paths` and `collect_decisions` subject lookups) and `review_findings.review_attestation_missing` lookups onto the cached `review_files` and `reviews` rows (`artifact_meta.query(latest_gate_review_of=...)`); the predicate's acceptance rule stays as it is (the gate-only change is Order 06's). Pin in `tests/test_readers_review_modules.py` and run `tests/test_review_findings_gate.py`, `tests/test_spec_review_attestation.py`, `tests/test_artifact_audit.py`, `tests/test_artifact_audit_verdicts.py` and `tests/test_artifact_audit_identity_staleness.py` green before and after. (Measured units at `ac76110f4`: 12 functions with a reader site, 5 baseline modules.)
  - Depends on: none
  - Expected outcome: all listed modules pass before and after; `aw check specs --agent` reports the same `check.spec-review-unattested` set as before.
  - Execution state: pending

### Task group 2: sequence, orchestration, production and work modules

- [ ] E-02 (carried from `t4gl15` E-12) Pin, then move, `review_sequence` (`count_verdict_bearing_entries`, `restore_pre_s7_plan` status and readiness reads, the snapshot verdict checks), `review_tier` and `review_rereview` (`meta_fields` reads, the `ipd_schema.read_readiness` call in `review_rereview`), `orchestrator_readiness` (`_BATCH_META_RE`, `meta_fields` reads), `production_checks` (`_PLAN_ID_RE`, `_ITEM_DEPS_RE`, `_SCOPE_PATHS_RE`, `_ITEM_FROM_BACKLOG_RE`, `_SET_RE`, `parse_item`, history clause), `work_cmd` (`_plan_id6`, `_plan_status`) and `artifact_adopt` (`_BULLET_ID_RE` in the adoption id inventory) onto `artifact_meta.read`/`query`/`history`, or `artifact_meta.read_text` for before/after snapshot strings that are not files. `restore_pre_s7_plan` still WRITES plan text and is a writer for Order 07; only its reads move here. Pin in `tests/test_readers_review_modules.py` and run `tests/test_review_sequence.py`, `tests/test_review_sequence_runner.py`, `tests/test_review_tier.py`, `tests/test_review_rereview.py`, `tests/test_orchestrator_readiness.py`, `tests/test_production_checks_trace.py`, `tests/test_backlog_production.py`, `tests/test_scope_match.py` and `tests/test_artifact_adopt.py` green before and after. (Measured units at `ac76110f4`: 36 functions with a reader site, of which `production_checks` 11 and `work_cmd` 11 read through two shared helpers each, so the distinct edits are about 20; 9 baseline modules. Over the 25-unit guideline by count of call sites, kept as one item because 22 of the 36 sites go through 4 helper functions and change with them.)
  - Depends on: E-01
  - Expected outcome: all listed modules pass before and after; none of the seven modules contains a `^-` metadata regex call.
  - Execution state: pending

- [ ] E-03 (carried from `t4gl15` E-15, this plan's module subset) Run `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-" <files>` and `rg -n "Workflow history" <files>` over the ten production modules in Scope-Paths (17 hits in 10 functions at `ac76110f4`, before this plan: `review_findings` 2, `artifact_audit` 1, `review_sequence` 3, `orchestrator_readiness` 1, `production_checks` 6, `work_cmd` 3, `artifact_adopt` 1) and write table F-04 in this plan listing every remaining hit with its owner: writer (Orders 06/07, named; for example the write half of `review_sequence.restore_pre_s7_plan`), body-prose bullet kept by N3 (named pattern), or a parser that Order 11 deletes. A reader hit with no such owner is a defect of this plan and is moved before finishing. Then run every module named in E-01 and E-02 and the bare core gate `python3 -m pytest`, and commit through `aw commit 2zpw22 -- <each changed path>`, never `git add -A`, a bare `git add` or `git commit -a`. Never push.
  - Depends on: E-02
  - Expected outcome: F-04 has no unowned reader hit; all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Interface names: `artifact_meta.read(id6) -> State`, `artifact_meta.history(id6)`, `artifact_meta.query(...)` including `latest_gate_review_of`, from `tve77h`; `artifact_meta.read_text(text, *, record_type=None)` and decision D-1 from `ffceq0`.
- Review files: `review_findings.parse_review_text` (front matter via `review_findings._META_RE`, then rounds and findings), `review_findings.review_attestation_missing` (the one attestation predicate).
- Cite code by SYMBOL (`module.function`), never a bare line number (advisory `IPD-C801`).

## Findings

Measured 2026-11-07 at `ac76110f4`.

| Id | Evidence | Finding |
|---|---|---|
| F-01 | AST pass over `rg` hits of each module's reader symbols (`_META_RE`, `_STATUS_LINE_RE`, `meta_fields`, `read_readiness(`, `_BATCH_META_RE`, `_PLAN_ID_RE`, `_ITEM_DEPS_RE`, `_SCOPE_PATHS_RE`, `_ITEM_FROM_BACKLOG_RE`, `_SET_RE`, `parse_item(`, `_plan_id6(`, `_plan_status(`, `_BULLET_ID_RE`, `_resolve_selector_paths`, `collect_decisions`, `review_attestation_missing`, `read_declared_status`, plus the `^-` regex pattern): `review_findings` 8 sites in 5 functions, `artifact_audit` 7 in 4, `reviews` 5 in 3 | E-01: 12 functions. |
| F-04 | (written by E-03) residual hits with owners | Input to `t4gl15` E-15 and Order 11. |
| F-02 | Same pass: `review_sequence` 13 sites in 5 functions, `review_tier` 3 in 1, `review_rereview` 5 in 2, `orchestrator_readiness` 8 in 4, `production_checks` 28 in 11, `work_cmd` 16 in 11, `artifact_adopt` 5 in 2 | E-02: 36 functions. |

READER LEDGER (copied from `t4gl15`):

| Reader | Prior behavior | Pinning test | After |
|---|---|---|---|
| `review_findings`, `artifact_audit`, `reviews` | review front matter by `_META_RE`; `_STATUS_LINE_RE` strict single-token status | `tests/test_review_findings_gate.py`, `tests/test_spec_review_attestation.py`, `tests/test_artifact_audit.py`, `tests/test_artifact_audit_verdicts.py`, `tests/test_artifact_audit_identity_staleness.py` | cached `review_files`/`reviews` rows; D-1 for status |
| `review_sequence`, `review_tier`, `review_rereview`, `orchestrator_readiness`, `production_checks`, `work_cmd`, `artifact_adopt` | `meta_fields`, `read_readiness` and module-local regex reads | `tests/test_review_sequence.py`, `tests/test_review_sequence_runner.py`, `tests/test_review_tier.py`, `tests/test_review_rereview.py`, `tests/test_orchestrator_readiness.py`, `tests/test_production_checks_trace.py`, `tests/test_backlog_production.py`, `tests/test_scope_match.py`, `tests/test_artifact_adopt.py` | cached fields or `read_text` for snapshots |

DECISIONS (copied from `t4gl15`, whose text is authoritative): D-1 PLAN records return the canonical normalized status; `artifact_audit._STATUS_LINE_RE` returned None for the 24 multi-word executed plans and now returns `executed`; `tests/test_artifact_audit_verdicts.py::test_multi_word_status_is_unreadable_by_design` may change only if the moved reader resolves its fixture as a plan (it is in Scope-Paths). D-3 the bullet `- Id:` inventory of `artifact_adopt` reads the cached `id` for plans, specs, backlog and releases.

## Proposed changes (ordered, validatable)

1. Pin then move the review and audit modules (E-01).
2. Pin then move the review sequence, tier, re-review, orchestration, production-check, work and adoption modules (E-02).
3. Residual audit, run and commit (E-03).

## Deferred / out of scope (with reason)

- The WRITE half of `review_sequence.restore_pre_s7_plan`.
  - Carrier: xexn45
- The `->reviewed` gate-only attestation rule (4.4 SR-601).
  - Carrier: 2xwb9b

## Scope check

- Over-scope: none. `tests/test_artifact_audit_verdicts.py` changes only in a D-1 assertion; `reviews.py` changes only for its subject-resolution reads.
- Under-scope: none known. Size: 3 E-items, 13 Scope-Paths (10 production modules that each change by a few reads, one new test module, one D-1 test, this plan). E-02 exceeds 25 units by raw call-site count; see its note.

## Required tests / validation

New test module: `tests/test_readers_review_modules.py` (core). CONTRIBUTES to `4sd62s` C5a. Commands: every module named in E-01 and E-02, the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change. Implements the review and orchestration module part of `4sd62s` C5a.

## Open questions

### OQ-01: Should E-02 be split further?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Its 36 call sites concentrate in shared helpers (`production_checks` module-level regexes and `_extract_plan_id`/`_read_from_backlog`; `work_cmd._plan_id6`/`_plan_status`), so the edit count is near 20 and every site shares one pinning module. If execution finds otherwise, split `production_checks` and `work_cmd` into a new plan. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_review_modules.py -k "review_findings or audit"` all PASSED, `diff .aw/state/t4gl15/E-11-before.txt .aw/state/t4gl15/E-11-after.txt` (outcome lists of `tests/test_review_findings_gate.py tests/test_spec_review_attestation.py tests/test_artifact_audit.py tests/test_artifact_audit_verdicts.py tests/test_artifact_audit_identity_staleness.py`) printing nothing or only D-1 lines, and the sorted `check.spec-review-unattested` locations from `aw check specs --agent` before and after with an empty diff.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `diff .aw/state/t4gl15/E-12-before.txt .aw/state/t4gl15/E-12-after.txt` (outcome lists of the nine modules named in E-02) printing nothing, `tests/test_readers_review_modules.py` all PASSED, and the empty output of `rg -n "re\.\w+\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/review_sequence.py agent_workflows/review_tier.py agent_workflows/review_rereview.py agent_workflows/orchestrator_readiness.py agent_workflows/production_checks.py agent_workflows/work_cmd.py agent_workflows/artifact_adopt.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the two `rg` commands of E-03 and the F-04 table (every remaining hit with its owner, none unowned); the bare `python3 -m pytest` summary line and wall time; and every `aw commit 2zpw22` output listing only Scope-Paths (or paths justified at finalize).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every `- Item-Dependencies:` edge is executed. OQ-01 is resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every reader move is pin-first.

Honesty rule: run the named modules and `python3 -m pytest` (core gate), and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit 2zpw22 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
