# Review findings: ipd 28k5h5

- Subject-Id: 28k5h5
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `bc96dcf69c1b72f4f560e59fb27354b7ad338636` in an isolated runner review-sweep lane worktree. The target plan `.aw/records/plans/pending/20261119-2i04so-01-28k5h5-wrap-check-engine-check-types-in-artifact-meta-scan-once-and.ipd.md` was committed and clean at turn start, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`exit: 0`, `error: 0`, `warning: 0`, `info: 2` on the boilerplate `IPD-C802` em-dashes). Inspection against backlog `2i04so`, `agent_workflows/check_engine.py`, `agent_workflows/artifact_meta.py`, `agent_workflows/cli.py`, git commit `5ca9a65a2af7441da5148c7f51b3fd9c77dba2fc` (2026-11-20), and `tests/` revealed that `@_with_scan_once` already landed on `check_type` and `check_types` in commit `5ca9a65a2` (one day after `28k5h5` was drafted), while zero behavioral regression tests pin the invariant and release-blocking backlog `2i04so` remains `graduated`. Live empirical probes confirmed `open_cache` (`call_count == 1`), `check_freshness` (`call_count == 1`), absent `.aw/state/index.db`, `Drift` parity, consecutive-call freshness, and nested `scan_once()` safety on repository-backed `tmp_path` fixtures, and uncovered an `AW_HOME` fixture pitfall. Findings `PR-001`..`PR-004` were fixed in place. Pass 2 re-checked every section after the `- Scope-Paths:` and `E-01`/`V-01` re-scope and confirmed clean `aw ipd lint --phase review-finalize --agent`.

### Proofreading

Checked `.aw/records/plans/pending/20261119-2i04so-01-28k5h5-wrap-check-engine-check-types-in-artifact-meta-scan-once-and.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Front matter | `- Status: to-review`, missing `- Readiness:` / `- Review-Depth:`, `- Scope-Paths:` included `agent_workflows/check_engine.py` and the plan's own path | Transitioned `- Status: reviewed` via `aw ipd set`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard`, narrowed `- Scope-Paths:` to `tests/test_check_engine_scan_once.py`, and aligned `- Concern:`/`- Scope:`/`- Short-Description:` with landed commit `5ca9a65a2` | PR-001, PR-004, Step S7 |
| Workflow history | `to-review` and `draft` lines only | Prepended `aw set` `reviewed` and `/plan-review` lines citing `APPROVE WITH REVISIONS APPLIED`, `PR-001..PR-004`, and this review record | Step S7 newest-first history contract |
| `Goal`, `E-01`, `V-01`, `Findings`, `Proposed changes`, Mermaid diagram, `Deferred / out of scope`, `Scope check`, `OQ-01` | Claimed `check_types` lacked an outer `scan_once()` / `ephemeral_if_uninitialized()` block, instructed adding an inner `with` block, excluded `check_type` and `selectors.scan_once()`, had `- Owner: none` on `OQ-01`, and left `Add further leaves as - [ ] E-NEW` boilerplate | Re-scoped `E-01`/`V-01` to verify already-landed `agent_workflows/check_engine.py::_with_scan_once` (`5ca9a65a2`) without adding redundant wrapping, updated `Findings`/diagram/`Deferred`/`OQ-01` (`- Owner: plan author`, `Carrier-Declined` citing `5ca9a65a2`), and removed `E-NEW` boilerplate | PR-001, PR-004, Step S5 |
| `E-02`, `V-02` | Used bare `tmp_path` without `.aw/config/project.json` and asserted `at most once` (`<= 1`) | Required repository-backed `.aw/config/project.json` (resisting `AW_HOME` redirection), multi-type fixture records, exact `call_count == 1`, single-type `check_type` reuse, and `check_types.__wrapped__` mutation-sensitivity proof | PR-003 |
| `Approval and execution gate` | Unconditionally instructed `aw ipd finalize 28k5h5` and omitted resolved-OQ precondition, `--scope-reason`/`--scope-ack`, paste-actual-output rule, and no-hand-`git mv` rule | Rewrote with all required execution-contract clauses including conditional runner (`AW_EXECUTION_ROLE=worker`) vs standalone executor finalize ownership | PR-002, Step R2, Step S7 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |

### Step T

1. No: no CLI option, output schema, or specification contract is changed; the `@_with_scan_once` decorator already landed in `5ca9a65a2` and this plan pins it with tests and closes release-blocking backlog `2i04so`.
2. No: after removing the redundant `agent_workflows/check_engine.py` edit, the sole code deliverable is `tests/test_check_engine_scan_once.py`. (Rated `standard` anyway because the plan carries `- Blocks-Release: next`, `- Priority: high`, and required a factual re-scope against landed commit `5ca9a65a2`.)
3. No: 3 `E-*` items in 1 task group, 1 declared `- Scope-Paths:` entry.
4. Yes: `- Scope-Paths:` explicitly lists `tests/test_check_engine_scan_once.py`.
5. Yes: executing the plan as originally authored would have added redundant dead wrapping inside an already-decorated `check_types` or risked removing `5ca9a65a2`'s `@_with_scan_once` / `_sel.scan_once()` decorator.

`AW-TIER: standard`

### Step R1

- Checked: `.aw/records/backlog/graduated/20261118-2i04so-01-2i04so-wrap-check-engine-check-types-in-artifact-meta-sca.backlog.md`, `agent_workflows/check_engine.py` (`_with_scan_once:4866`, `check_type:4882`, `check_types:4940-5217`, `check_release_gates:7698`, `_meta_records_with_fields:5276`, `_meta_state_for_path:5335`, `_meta_state_map:5390`, `_item_close_date:6698`, `_item_graduated_date:7019`, `_spec_implementing_date:7081`), `agent_workflows/artifact_meta.py` (`_SCAN_ONCE_FRESH:4518`, `_SCAN_ONCE_CONNS:4521`, `_EPHEMERAL_IF_ABSENT:4524`, `ephemeral_if_uninitialized:4530`, `scan_once:4540`, `_open_for_read:4566`, `_maybe_check_freshness:4582`), `agent_workflows/cli.py` (`_run_find:16357`, `check_release_gates:18009`, `check_types:18035`), git commit `5ca9a65a2af7441da5148c7f51b3fd9c77dba2fc`, and all test files in `tests/`.
- Found `PR-001` (`_with_scan_once` already landed in `5ca9a65a2` on both `check_type` and `check_types` with `_sel.scan_once()`, while zero dedicated regression tests exist) and `PR-003` (bare `tmp_path` fixture redirects `records_root` to `$AW_HOME` unless `.aw/config/project.json` configures repository-backed records).

### Step R2

- Checked: `E-*`/`V-*` bijection (`3/3`: `E-01..E-03` <-> `V-01..V-03`, `- Highest E allocated: 03`), dependency chain (`E-01 -> E-02 -> E-03`), `- Scope-Paths:` accuracy, `- Item-Dependencies: none`, `- From-Backlog: 2i04so`, `- Blocks-Release: next`, carrier obligations on `Deferred / out of scope` (`Carrier-Declined`), runtime reachability of `V-01..V-03`, and `Approval and execution gate`.
- Found `PR-002` (incomplete execution contract and unconditional `aw ipd finalize` in `Approval and execution gate`) and `PR-004` (stale `agent_workflows/check_engine.py` and self-referential plan path in `- Scope-Paths:`, leftover `E-NEW` template line, and `- Owner: none` on `OQ-01`). Fixed both in place.

### Step R3

- Checked: security and privacy full form (`steps/r3-security.md`). No trust-boundary changes, credentials, outbound network calls, or shell interpolations; `@_with_scan_once` uses in-memory SQLite (`:memory:`) on uninitialized repositories via `ephemeral_if_uninitialized()` so read-only checks never create `.aw/state/index.db`, and tests run exclusively on isolated `tmp_path` directories.

### Step R4

- Checked: correctness and data integrity (empirically verified via live probes on uninitialized and initialized repository-backed `tmp_path` repos: `open_cache` `call_count == 1`, `check_freshness` `call_count == 1`, `index.db` absent on uninitialized repo, `Drift` parity `True`, consecutive-call new-defect detection `True`, nested `scan_once()` keeps outer connection open, `cli.main` returns valid `aw.agent/v1` without creating `index.db`), anti-regression and P16 behavioral testing (no `inspect`/`ast` pins; added `check_types.__wrapped__` mutation-sensitivity assertion and exact `call_count == 1`), right-sizing (3 focused E-items, 1 test file), and `## Spec / documentation sync` (`N/A` accurately justified).

### Step S5

- Checked: `OQ-01` (`Blocking: no`, `Status: resolved`). Updated `- Owner: plan author` and reconciled rationale with commit `5ca9a65a2`. Recorded autonomous review decisions `D-1`..`D-2` in `### Decisions` (both `Reversible: yes`). Zero blocking or human-owned open questions remain; all findings `PR-001`..`PR-004` are `FIXED` in place.

### Pass 2

- Re-checked all sections after `- Scope-Paths:` and `E-01`/`V-01` re-scope: front matter, `## Workflow history`, `## Goal`, `E-01..E-03`, `Project conventions discovered`, `Findings`, Mermaid flowchart, `Proposed changes`, `Deferred / out of scope`, `Scope check`, `Required tests / validation`, `Spec / documentation sync`, `OQ-01`, `V-01..V-03`, and `Approval and execution gate`.
- Confirmed zero stale claims that `check_types` lacks an outer `scan_once()` wrapper, zero redundant `check_engine.py` edit instructions, `3/3` bijection, and clean `aw ipd lint --phase review-finalize --agent` disposition.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PR-001 | BLOCKER | IN-SCOPE | R1 / R4 / Stale premise against HEAD | agent_workflows/check_engine.py:4866 `_with_scan_once`; agent_workflows/check_engine.py:4940 `check_types`; commit `5ca9a65a2`; .aw/records/plans/pending/20261119-2i04so-01-28k5h5-wrap-check-engine-check-types-in-artifact-meta-scan-once-and.ipd.md:38 | Commit `5ca9a65a2` (2026-11-20) already wrapped both `check_type` and `check_types` in `@_with_scan_once` (`_meta.scan_once()`, `_meta.ephemeral_if_uninitialized()`, `_sel.scan_once()`), while shipping zero behavioral regression tests for the invariant. Executing `E-01` as authored would add redundant dead wrapping or risk removing `_sel.scan_once()` / `@_with_scan_once`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Re-scoped `E-01`/`V-01` to verify already-landed `@_with_scan_once` (commit `5ca9a65a2`) without modifying `agent_workflows/check_engine.py`, kept `E-02`/`E-03` to ship the missing behavioral regression suite and close backlog `2i04so`, and reconciled `Goal`, `Findings`, diagram, `Deferred`, and `OQ-01`. Recommendation strength: very strong. |
| PR-002 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261119-2i04so-01-28k5h5-wrap-check-engine-check-types-in-artifact-meta-scan-once-and.ipd.md:144 | `Approval and execution gate` unconditionally instructed `aw ipd finalize 28k5h5` and omitted the resolved-OQ precondition, `--scope-reason`/`--scope-ack` scope-fence clause, paste-actual-runner-output honesty rule, hand-`git mv` prohibition, and conditional runner/executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Approval and execution gate` with all required execution-contract clauses including conditional runner (`AW_EXECUTION_ROLE=worker`) vs standalone executor finalize ownership. Recommendation strength: very strong. |
| PR-003 | MEDIUM | IN-SCOPE | R1 / R4 / Test fixture correctness | Live probe in runner lane with `AW_HOME` exported; .aw/records/plans/pending/20261119-2i04so-01-28k5h5-wrap-check-engine-check-types-in-artifact-meta-scan-once-and.ipd.md:43 | A bare `tmp_path` repo without repository-backed `.aw/config/project.json` redirects `records_root` to `$AW_HOME`, and asserting `at most once` (`<= 1`) lets a vacuous `0`-call test pass; `E-02` also omitted `check_type` reuse and an explicit mutation-sensitivity check against `@_with_scan_once`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-02` and `V-02` to require repository-backed `.aw/config/project.json` with populated multi-type records, exact `call_count == 1`, single-type `check_type` reuse, and `check_types.__wrapped__` mutation-sensitivity assertion. Recommendation strength: strong. |
| PR-004 | MEDIUM | IN-SCOPE | R2 / S5 / Scope-Paths and hygiene | .aw/records/plans/pending/20261119-2i04so-01-28k5h5-wrap-check-engine-check-types-in-artifact-meta-scan-once-and.ipd.md:7, :53, :122 | `- Scope-Paths:` declared unmodified `agent_workflows/check_engine.py` and the plan's own path, line 53 retained `E-NEW` template boilerplate, and `OQ-01` recorded `- Owner: none` on a resolved question. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Narrowed `- Scope-Paths:` to `tests/test_check_engine_scan_once.py`, removed the `E-NEW` template line, and updated `OQ-01` to `- Owner: plan author`. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D-1 | Given that commit `5ca9a65a2` already landed `@_with_scan_once` on `check_type` and `check_types` without adding regression tests, should `28k5h5` be re-scoped in place to verify `5ca9a65a2` and ship `tests/test_check_engine_scan_once.py`, or rejected/retired? | Re-scope `28k5h5` in place to verify `@_with_scan_once` (no duplicate code edit) and ship the missing behavioral regression suite in `tests/test_check_engine_scan_once.py` to close release-blocking backlog `2i04so`. | Keep the duplicate `E-01` edit (adds dead code), or mark `REPLAN` / retire without shipping regression tests for `Blocks-Release: next` item `2i04so`. | Commit `5ca9a65a2`; `agent_workflows/check_engine.py:4866-4941`; `.aw/records/backlog/graduated/20261118-2i04so-01-2i04so-wrap-check-engine-check-types-in-artifact-meta-sca.backlog.md` | yes |
| D-2 | Should `tests/test_check_engine_scan_once.py` require repository-backed `.aw/config/project.json` and exact `call_count == 1` assertions? | Yes: require repository-backed `.aw/config/project.json`, multi-type records, exact `call_count == 1`, and a `check_types.__wrapped__` mutation-sensitivity check. | Leave `tmp_path` unconfigured and assert `<= 1` (can pass vacuously under runner-exported `AW_HOME`). | Live probe under `AW_HOME`; `GUIDING_PRINCIPLES.md` P16 ("Verify test sensitivity with mutation") | yes |
