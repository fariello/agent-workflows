# Review findings: ipd rulopj

- Subject-Id: rulopj
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261121T064614Z-2150223`). The target plan `.aw/records/plans/pending/20261119-r20qqe-01-rulopj-move-runner-shared-fail-incomplete-status-reset-onto-artifac.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `2` non-blocking `IPD-C802` info advisories on template prose). Inspection of backlog item `r20qqe`, `agent_workflows/runner_shared.py` (`run_review_sequence`, `_fail_incomplete`, `mark_plan_attended`, `rederive_front_matter`, `perform_coordinator_proposal_file`), `agent_workflows/artifact_meta.py` (`append`, `write_legacy`, `render_legacy`, `_render_status`, `_render_field`, `_check_owned_fields`, `legacy_context`, `restore_legacy_snapshot`), `agent_workflows/ipd_lifecycle.py` (`_LEGAL_BACKWARD_EDGES`), `agent_workflows/status_set.py`, `agent_workflows/review_sequence.py` (`restore_pre_s7_plan`), spec `4sd62s` Section 7 step 4, pending plans `y97k46`, `k3hb06`, and `9o83cr`, and `tests/test_review_sequence_runner.py` surfaced two `HIGH`, one `MEDIUM`, and one `LOW` finding (`PR-001..PR-004`), all fixed in place. Pass 2 re-checked `Scope`, `E-01..E-03`, `Step 0`, `Findings`, `Proposed changes`, the Mermaid flowchart, `Open questions`, `V-01..V-03`, and `Approval and execution gate` for full internal consistency.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `E-01`, `V-01` | Ran baseline pytest with `-p no:randomly -n 0` and hardcoded `(showing 10 passed)` as the V-01 bar | Removed `-p no:randomly -n 0` to keep order randomization enabled and replaced the hardcoded test count with re-derived baseline execution output (0 failures, 0 errors) | PR-001, `AGENTS.md`, `steps/r2-executability.md` |
| `Approval and execution gate` | Omitted resolved-OQ precondition, `--scope-reason`/`--scope-ack` scope-fence variance rule, shared-checkout safety, explicit hand-`git mv` prohibition, and clear conditional runner/standalone finalize ownership | Added all required execution-contract clauses including conditional runner/standalone `aw ipd finalize rulopj` ownership and explicit hand-`git mv` prohibition | PR-002, `steps/r2-executability.md`, `steps/s7-finalize.md` |
| `Scope`, `E-01`, `E-02`, `Step 0`, `Proposed changes`, `V-01`, `V-02` | Omitted local `artifact_core`/`artifact_meta` imports in `run_review_sequence`, hardcoded backward status tuple without `.lower()`, nested stale `Approval` cleanup inside backward branch, omitted `import pytest` in E-02, and offered exception-injection alternative to spy wrapping | Added local `artifact_core`/`artifact_meta` imports, lowercased `cur_status`, reused `ipd_lifecycle._LEGAL_BACKWARD_EDGES` for `readiness` unset and cleared `approval` whenever leaving `approved` or stale `Approval` exists, synchronized the Mermaid diagram, added `import pytest`, and standardized on `wraps=artifact_meta.append` | PR-003, `steps/r1-references.md`, `steps/r4-engineering.md`, technical writing standard Requirement 12(d)/(e) |
| `Scope`, `Step 0`, `Proposed changes` | Inaccurately stated `mark_plan_attended` passes `history=False`, and used unqualified symbol references | Corrected `Step 0` to distinguish `mark_plan_attended` (default `history=True` with `note`) from `rederive_front_matter` and `perform_coordinator_proposal_file` (`history=False`), and qualified code citations to `path::Symbol` | PR-004, `steps/p-proofread.md` Section 11.1, `steps/r1-references.md` |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No; internal bug fix in `agent_workflows/runner_shared.py::run_review_sequence._fail_incomplete` aligning it with the existing phase-B `artifact_meta` writer contract (spec `4sd62s` Section 7 step 4) without changing any CLI option, output format, file format, or spec contract.
2. No; touches only the incomplete-review status-reset path in `agent_workflows/runner_shared.py::run_review_sequence._fail_incomplete` and its tests in `tests/test_review_sequence_runner.py`, with no private-data, commit, worktree-isolation, merge-to-main, or sandbox code.
3. No; small and focused (`3` E-items in `1` task group across `1` production module and `1` test file).
4. Yes; `- Scope-Paths:` explicitly lists `agent_workflows/runner_shared.py`, `tests/test_review_sequence_runner.py`, and this IPD.
5. Yes; `run_review_sequence._fail_incomplete` is the rollback/cleanup path for failed multi-step reviews on both hosts, and a misconstructed `artifact_meta.append` event payload (such as missing backward-transition `unset` fields) raises `ValueError` during cleanup and leaves the plan in a stale status or readiness state.

AW-TIER: standard

### Step R1

- Checked: backlog `.aw/records/backlog/graduated/20261117-r20qqe-01-r20qqe-move-runner-shared-fail-incomplete-status-reset-on.backlog.md`, `agent_workflows/runner_shared.py` (`run_review_sequence`, `_fail_incomplete`, `mark_plan_attended`, `rederive_front_matter`, `perform_coordinator_proposal_file`), `agent_workflows/artifact_meta.py` (`append`, `write_legacy`, `render_legacy`, `_render_status`, `_render_field`, `_check_owned_fields`, `legacy_context`, `restore_legacy_snapshot`, `LegacyTarget`, `LegacyRender`), `agent_workflows/ipd_lifecycle.py` (`_LEGAL_BACKWARD_EDGES`), `agent_workflows/status_set.py` (lines 1090, 1572-1586, 1862-1873), `agent_workflows/review_sequence.py` (`restore_pre_s7_plan`), spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` Section 7 step 4, pending plans `y97k46`, `k3hb06`, and `9o83cr`, and `tests/test_review_sequence_runner.py` / `tests/test_runner_shared.py`.
- Found that `Step 0` misstated `mark_plan_attended` as passing `history=False` (`PR-004`), that `run_review_sequence` does not yet import `artifact_core` or `artifact_meta` (`PR-003`), and that `tests/test_review_sequence_runner.py` does not yet import `pytest` (`PR-003`). All fixed in place.

### Step R2

- Checked: `E-*`/`V-*` bijection (`3/3`: `E-01..E-03` <-> `V-01..V-03`, `- Highest E allocated: 03`), dependency chain (`E-01 -> E-02 -> E-03`), `- Scope-Paths:` completeness, `- Item-Dependencies: none`, runtime reachability of `V-01..V-03` (all demand git diffs, `rg`, pytest, or `aw` CLI outputs, reachable by construction), test-runner contract, re-derivation convention, and `Approval and execution gate`.
- Found forbidden pytest flags (`-p no:randomly -n 0`) and hardcoded collected test count `(showing 10 passed)` in `E-01`/`V-01` (`PR-001`), and incomplete execution contract in `Approval and execution gate` (`PR-002`). Both fixed in place.

### Step R3

- Checked: security and privacy lens (`steps/r3-security.md` full form). Replacing raw `re.sub` + `plan_file.write_text` with `artifact_meta.append` strengthens data-integrity and trust-boundary enforcement: `write_legacy` validates `LegacyRender.actor_label` and event payloads via `validate_new_events` (string safety, absolute-path check, leak sanitizer), enforces `_check_owned_fields` transition invariants, acquires `<state>/locks/meta-<key>.lock`, and writes via `artifact_core.atomic_write`. No secrets, external network calls, or privileged bypasses are introduced; an unmigrated metadata bypass is removed.

### Step R4

- Checked: correctness and data integrity (`PR-003` adds local `artifact_core`/`artifact_meta` imports, lowercases `cur_status`, reuses `ipd_lifecycle._LEGAL_BACKWARD_EDGES` for `readiness` unset, clears stale `approval` whenever leaving `approved` or an `Approval` bullet is present, and preserves body `- Status:` lines via `_render_status`), anti-regression and testing (`E-02` exercises `reviewed`, `approved`, and `draft` statuses, body prose preservation, and `wraps=artifact_meta.append` routing with `@pytest.mark.core` behavioral tests and zero source-inspection assertions), right-sizing (`3` E-items, `3` Scope-Paths, cohesive single bugfix), and `## Spec / documentation sync` (`N/A` verified truthful against spec `4sd62s` Section 7 step 4).

### Step S5

- Checked: `## Open questions` (`OQ-01`, `Blocking: no`, `Status: resolved`, `Owner: plan author`, verified against `agent_workflows/artifact_meta.py::restore_legacy_snapshot`). Every finding (`PR-001..PR-004`) has `Overall:Low` Remediation Risk and is settled directly by repository evidence. Recorded `D-1` (`Reversible: yes`) in `### Decisions`. Zero blocking or human-owned questions remain.

### Pass 2

- Re-checked the complete revised plan across `Scope`, `Goal`, `E-01..E-03`, `Step 0`, `Findings`, `Proposed changes`, Mermaid flowchart, `Deferred / out of scope`, `Scope check`, `Required tests / validation`, `Spec / documentation sync`, `Open questions`, `V-01..V-03`, and `Approval and execution gate`.
- Verified `3/3` E/V bijection, `- Highest E allocated: 03`, zero unresolved questions, and clean `aw ipd lint --phase review-finalize --agent` disposition.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R2 / Test-runner contract and re-derivation convention | .aw/records/plans/pending/20261119-r20qqe-01-rulopj-move-runner-shared-fail-incomplete-status-reset-onto-artifac.ipd.md:38,134; AGENTS.md:307; .aw/system/workflows/plan-review/steps/r2-executability.md:65 | `E-01` and `V-01` instructed running pytest with `-p no:randomly -n 0` (forbidden by `AGENTS.md` / `GEMINI.md` because disabling order randomization hides bugs and `-n 0` disables xdist), and `V-01` hardcoded `(showing 10 passed)` as a collected test-count bar (forbidden by `steps/r2-executability.md` re-derivation convention). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-01` and `V-01` to run `python3 -m pytest -o addopts="" -v tests/test_review_sequence_runner.py` without `-p no:randomly` or `-n 0`, and replaced the hardcoded test count bar with re-derived baseline runner output showing 0 failures and 0 errors. Recommendation strength: very strong. |
| PR-002 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261119-r20qqe-01-rulopj-move-runner-shared-fail-incomplete-status-reset-onto-artifac.ipd.md:148-153; .aw/system/workflows/plan-review/steps/r2-executability.md:57-60; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | `Approval and execution gate` omitted the resolved-blocking-open-questions precondition, `--scope-reason`/`--scope-ack` scope-fence variance rule, shared-checkout safety clause, explicit prohibition on hand-rolled `git mv` to `executed/`, and clear conditional runner-versus-standalone `aw ipd finalize rulopj` ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Approval and execution gate` with all required execution-contract clauses, explicit prohibition of hand-`git mv` to `executed/`, and conditional runner/standalone finalize ownership. Recommendation strength: very strong. |
| PR-003 | MEDIUM | IN-SCOPE | R1 / R4 / Backward-edge source of truth, imports, and spy pattern | .aw/records/plans/pending/20261119-r20qqe-01-rulopj-move-runner-shared-fail-incomplete-status-reset-onto-artifac.ipd.md:38-50,88; agent_workflows/runner_shared.py::run_review_sequence:30583-30590,30861-30867; agent_workflows/ipd_lifecycle.py::_LEGAL_BACKWARD_EDGES:1167-1179; agent_workflows/status_set.py:1090,1862-1872; tests/test_review_sequence_runner.py:17-32 | `E-01` omitted adding `artifact_core` and `artifact_meta` to `run_review_sequence`'s local imports, re-listed backward statuses inline without `.lower()` normalization instead of consulting `ipd_lifecycle._LEGAL_BACKWARD_EDGES`, and nested stale `Approval` unsetting inside the backward branch; `E-02` omitted importing `pytest` in `tests/test_review_sequence_runner.py` and suggested exception injection as an alternative to spy wrapping even though `_fail_incomplete` does not catch exceptions from `artifact_meta.append`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `Scope`, `E-01`, `E-02`, `Step 0`, `Proposed changes` (including the Mermaid flowchart), `V-01`, and `V-02` to add the local imports, lowercase `cur_status`, consult `ipd_lifecycle._LEGAL_BACKWARD_EDGES`, clear `approval` whenever leaving `approved` or a stale `Approval` bullet exists (`D-1`), import `pytest`, and use `unittest.mock.patch.object(artifact_meta, "append", wraps=artifact_meta.append)`. Recommendation strength: very strong. |
| PR-004 | LOW | IN-SCOPE | R1 / Proofreading / Factual accuracy and citation form | .aw/records/plans/pending/20261119-r20qqe-01-rulopj-move-runner-shared-fail-incomplete-status-reset-onto-artifac.ipd.md:6,68,93-95; agent_workflows/runner_shared.py::mark_plan_attended:51768-51772; agent_workflows/runner_shared.py::rederive_front_matter:5485-5495; agent_workflows/runner_shared.py::perform_coordinator_proposal_file:51903-51914,52085-52096 | `Step 0` inaccurately stated that `mark_plan_attended` passes `history=False` (`mark_plan_attended` uses `LegacyRender`'s default `history=True` with a `note` event; only `rederive_front_matter` and `perform_coordinator_proposal_file` pass `history=False`), and `Scope` / `Proposed changes` used unqualified symbol references. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected `Step 0` to distinguish `mark_plan_attended` from `rederive_front_matter` and `perform_coordinator_proposal_file`, and qualified symbol citations to `path::Symbol`. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `run_review_sequence._fail_incomplete` classify backward transitions and stale `Approval` cleanup before calling `artifact_meta.append`? | Normalize `cur_status = (doc_c.meta_fields.get("Status") or "").strip().lower()`, consult `(cur_status, "to-review") in ipd_lifecycle._LEGAL_BACKWARD_EDGES` to unset `"readiness"`, and unset `"approval"` whenever `cur_status == "approved"` or `bool(doc_c.meta_fields.get("Approval"))`, importing `artifact_core` and `artifact_meta` inside `run_review_sequence`. | Hardcode `cur_status in ("reviewed", "approved", "auto-approved")` without `.lower()` and nest `Approval` cleanup inside that branch (rejected: duplicates `_LEGAL_BACKWARD_EDGES` against `status_set.py:1090`, misses mixed-case legacy values, and leaves stale `Approval` bullets on non-backward resets). | `agent_workflows/ipd_lifecycle.py::_LEGAL_BACKWARD_EDGES:1167-1179`, `agent_workflows/status_set.py:1090,1862-1872`, `agent_workflows/artifact_meta.py::_check_owned_fields:6088-6145` | yes |
