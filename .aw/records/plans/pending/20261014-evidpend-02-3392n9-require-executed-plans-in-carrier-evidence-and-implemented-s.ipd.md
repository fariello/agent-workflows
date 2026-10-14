# IPD: Require executed plans in Carrier-Evidence and implemented specs in evidence citations

- Date: 2026-10-14
- Kind: child
- Concern: Backlog `bkprhk` (follow-up from `7lfe87` / executed plan `ncmugb` / `D165`): `ncmugb` added `check_engine._evidence_plan_unshipped` only to `check_engine.evaluate_blocking_close`'s `SATISFIED` arm and left two non-terminal evidence gaps open. First, `check_engine.evaluate_carrier_obligation`'s `SATISFIED` arm (`- Carrier-Evidence:`) still calls `check_engine.resolve_evidence_artifact` without checking `_evidence_plan_unshipped`, so an IPD deferred row or open question can discharge an obligation as `SATISFIED` by citing a `pending/`, `draft`, `not-executed/`, `superseded/`, or `reusable/` plan. Second, neither `evaluate_blocking_close` (`- Close-Evidence:` / `--evidence`) nor `evaluate_carrier_obligation` (`- Carrier-Evidence:`) checks a cited spec's status, so both predicates accept a `draft`, `to-review`, `reviewed`, `approved`, `implementing`, `deferred`, `parked`, or `superseded` spec as `SATISFIED` evidence of finished work, even though `evaluate_blocking_close`'s `HANDOFF` arm (`_carrier_is_executed`) requires `- Status: implemented` for a `.spec.md` carrier and `evaluate_carrier_obligation`'s `HANDOFF` arm (`_CARRIER_TARGET_TYPES = ("backlog", "plans")`) forbids spec carriers altogether.
- Scope: In `agent_workflows/check_engine.py`, add `_evidence_spec_unshipped(repo_root, evidence) -> bool` (returning `True` when a citation resolves inside a specs tree and is not a file carrying `- Status: implemented` or lives in a non-`implemented` status subdirectory under that specs root), wire `_evidence_spec_unshipped` into `evaluate_blocking_close`'s `SATISFIED` arm alongside `_evidence_plan_unshipped`, and wire both `_evidence_plan_unshipped` and `_evidence_spec_unshipped` into `evaluate_carrier_obligation`'s `SATISFIED` arm with single-line refusal reasons that satisfy `attention_contract.is_safe_descriptive` and `attention_contract.MAX_DESCRIPTIVE_LEN` (`300`). Keep `resolve_evidence_artifact`'s return value unchanged, update its docstring and `agent_workflows/ipd_schema.py`'s `CARRIER_EVIDENCE_FIELD` comment, add behavioral tests in `tests/test_backlog_close_evidence_plan_disposition.py` and `tests/test_check_engine.py`, update repo-local `AGENTS.md`, `.aw/records/backlog/README.md`, and `CHANGELOG.md`, and record the decision and grandfathering analysis in `DECISIONS.md`.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/ipd_schema.py, tests/test_backlog_close_evidence_plan_disposition.py, tests/test_check_engine.py, AGENTS.md, .aw/records/backlog/README.md, CHANGELOG.md, DECISIONS.md
- Item-Dependencies: none
- Status: to-review
- From-Backlog: bkprhk
- Work-Kind: followup
- Priority: low
- Set: evidpend
- Order: 2
- Highest E allocated: 06
- Author: antigravity
- Id: 3392n9

## Workflow history
- 2026-10-14 to-review (aw set): authored review-ready child IPD 3392n9 graduating backlog bkprhk at HEAD bb28b833a

- 2026-10-14 draft (antigravity): created.

## Goal

Bring `- Carrier-Evidence:` (`check_engine.evaluate_carrier_obligation`) and spec citations in both `- Close-Evidence:` (`check_engine.evaluate_blocking_close`) and `- Carrier-Evidence:` into parity with the executed-plan rule from `ncmugb` (`D165`): citing a plan as `SATISFIED` evidence requires an `executed/` disposition directory, and citing a spec as `SATISFIED` evidence requires `- Status: implemented` (and an `implemented/` status directory when under a status-bucketed specs root), while every other in-tree records artifact and existing corpus row stays valid without a new cutover.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: pin the spec and carrier-evidence defects with outcome tests

- [ ] E-01 Add tests in `tests/test_backlog_close_evidence_plan_disposition.py` covering spec citations in `check_engine.evaluate_blocking_close`, `aw backlog set`, and `check_engine.check_release_gate_consistency`.
  - Write real `.spec.md` fixtures with `- Id:`, `- Status:`, and `## Workflow history` lines under `.aw/records/specs/<status>/` (and legacy `.agents/docs/specs/`).
  - Assert that citing an `approved` spec is refused on `aw backlog set <id> --status done --evidence ...`, `aw backlog set done <id> --evidence ...`, and `--dry-run` (exit code `1`, item remains in `open/` byte-identical, reason names the cited spec path and `names a spec that has not shipped (status is not implemented)`), and that `draft`, `to-review`, `reviewed`, `implementing`, `deferred`, `parked`, and `superseded` specs, `.aw/records/specs/README.md`, and a spec whose directory (`approved/`) and metadata (`- Status: implemented`) disagree all return `legitimate=False` from `evaluate_blocking_close`.
  - Assert that citing an `implemented` spec is accepted on both CLI spellings (`verdict.path == "SATISFIED"`, item moved to `done/` with `- Close-Evidence:` written), under sharded `.aw/records/specs/implemented/YYYYMM/`, and under flat legacy `.agents/docs/specs/`, and that at-rest `check_release_gate_consistency(repo, at_rest=True)` flags a `done/` gated item citing an `approved` spec with `check.blocking-item-closed-without-gate` while keeping an `implemented` spec citation clean.
  - Run `python3 -m pytest -o addopts="" tests/test_backlog_close_evidence_plan_disposition.py -v` before E-03 to confirm the new spec refusal cases fail at HEAD while acceptance cases pass, and run the bare full suite (`python3 -m pytest`) now to record the pre-change summary line and failing node-id set for E-06.
  - Depends on: none
  - Expected outcome: `tests/test_backlog_close_evidence_plan_disposition.py` has spec-citation coverage whose refusal cases fail at HEAD and whose acceptance cases pass at HEAD, and the pre-change bare `python3 -m pytest` baseline is captured.
  - Execution state: pending

- [ ] E-02 Add tests in `tests/test_check_engine.py` covering plan and spec citations in `check_engine.evaluate_carrier_obligation`, `check_engine.evaluate_durable_carrier`, `ipd_lint.lint_file(..., checkpoint="pre-transition")`, and `check_engine.check_durable_carrier`. Cover: `evaluate_carrier_obligation` refusing `- Carrier-Evidence:` on both a `## Deferred / out of scope` bullet and an `### OQ-01` block when the cited path is a plan in `plans/pending/` (`draft` or `to-review`), `plans/not-executed/`, `plans/superseded/`, or `plans/reusable/`, or the plans directory itself (`verdict.legitimate is False`, `verdict.rule == "check.ipd-uncarried-obligation"`, reason naming `names a plan that has not shipped (is not in \`executed/\`)`); `evaluate_carrier_obligation` refusing `- Carrier-Evidence:` when the cited path is a spec with status `draft`, `to-review`, `reviewed`, `approved`, `implementing`, `deferred`, `parked`, or `superseded`, or `.aw/records/specs/README.md`, or a spec with mismatched directory vs `- Status:` (`verdict.legitimate is False`, `verdict.rule == "check.ipd-uncarried-obligation"`, reason naming `names a spec that has not shipped (status is not \`implemented\`)`); `evaluate_carrier_obligation` accepting `- Carrier-Evidence:` when the cited path is a plan in `.aw/records/plans/executed/`, sharded `.aw/records/plans/executed/YYYYMM/`, or legacy `.agents/plans/executed/`, an `implemented` spec in `.aw/records/specs/implemented/`, sharded `.aw/records/specs/implemented/YYYYMM/`, or flat legacy `.agents/docs/specs/`, or a non-plan/non-spec records artifact (`backlog/done/`, `backlog/open/`, `research/`, `reviews/`, `releases/`); `evaluate_durable_carrier` and `ipd_lint.lint_file(..., checkpoint="pre-transition")` emitting `check.ipd-uncarried-obligation` (`IPD-S408`) whose `Drift.detail` satisfies `attention_contract.is_safe_descriptive(d.detail)` and `len(d.detail) <= attention_contract.MAX_DESCRIPTIVE_LEN` even when a long clustered path is cited across multiple obligations; and `check_durable_carrier` ignoring an `executed/` plan that carries a `pending/` or `approved`-spec `Carrier-Evidence:` line (proving pending-only sweep grandfathering). Run the new test class before E-03 to verify all refusal assertions fail at HEAD and all acceptance/grandfathering assertions pass.
  - Depends on: E-01
  - Expected outcome: `tests/test_check_engine.py` has behavioral tests for `Carrier-Evidence:` plan and spec disposition whose refusal assertions fail at HEAD and whose acceptance and grandfathering assertions pass at HEAD.
  - Execution state: pending

### Task group 2: tighten the predicates and update schema/helper docstrings

- [ ] E-03 In `agent_workflows/check_engine.py`, add `_evidence_spec_unshipped` and wire plan and spec disposition checks into `evaluate_blocking_close` and `evaluate_carrier_obligation`.
  - Implement `_evidence_spec_unshipped(repo_root: Path, evidence: str) -> bool` directly below `_evidence_plan_unshipped`: resolve `repo_root = Path(repo_root).resolve()` and `candidate = (repo_root / evidence).resolve()`, compute `rel = candidate.relative_to(repo_root).parts` (returning `False` on `ValueError`), and match specs roots relative to `repo_root` (`rel[:3] == (".aw", "records", "specs")` with `prefix_len = 3`, `rel[:3] == (".agents", "docs", "specs")` with `prefix_len = 3`, or `rel[:2] == (".agents", "specs")` with `prefix_len = 2`). Return `False` when `prefix_len is None`. Inside a specs tree, return `True` if `not candidate.is_file()` or `len(rel) <= prefix_len`, return `True` when `len(rel) > prefix_len + 1` and `rel[prefix_len] != "implemented"`, and finally read `candidate` as UTF-8 (returning `True` on `OSError`) and return `_status_meta(text) != "implemented"`.
  - In `evaluate_blocking_close`'s `SATISFIED` arm, immediately after `_evidence_plan_unshipped`, check `_evidence_spec_unshipped(repo_root, effective_evidence)` and return `CloseVerdict(False, "error", f"cited evidence {effective_evidence!r} names a spec that has not shipped (status is not implemented)", ("cite the spec once it is implemented", "hand the gate to a plan: add `- From-Backlog: <this id6>` (and the same `- Blocks-Release`) to a plan via `aw ipd set ... --from-backlog <id6>`", "cite satisfying evidence: `aw backlog set done <item> --evidence <in-tree artifact path; a cited plan must be executed and a cited spec must be implemented>`", "explicitly release the gate first: `aw backlog set done <item> --blocks-release -`"), None)`. Update the `--evidence` hint string in the other three `evaluate_blocking_close` refusals to `<in-tree artifact path; a cited plan must be executed and a cited spec must be implemented>`.
  - In `evaluate_carrier_obligation`'s `SATISFIED` arm, when `resolve_evidence_artifact(repo_root, evidence)` is `True`, check `_evidence_plan_unshipped(repo_root, evidence)` (returning `CloseVerdict(False, "error", f"{obligation.locator}: `Carrier-Evidence: {evidence}` names a plan that has not shipped (is not in `executed/`)", ("cite the plan once it is executed, or hand off to a live plan with `- Carrier: <id6>`",) + fixes, None, rule=_CARRIER_RULE)`) and `_evidence_spec_unshipped(repo_root, evidence)` (returning `CloseVerdict(False, "error", f"{obligation.locator}: `Carrier-Evidence: {evidence}` names a spec that has not shipped (status is not `implemented`)", ("cite the spec once it is implemented, or hand off to an open backlog item or pending plan with `- Carrier: <id6>`",) + fixes, None, rule=_CARRIER_RULE)`), updating `evaluate_carrier_obligation`'s `fixes[1]` hint to `<in-tree artifact path; a cited plan must be executed and a cited spec must be implemented>`.
  - Update `resolve_evidence_artifact`'s docstring, `evaluate_carrier_obligation`'s docstring, `evaluate_durable_carrier`'s `required` string, and `agent_workflows/ipd_schema.py`'s `CARRIER_EVIDENCE_FIELD` comment so they state that `resolve_evidence_artifact` checks safety, containment, existence, and records-tree location only while `evaluate_blocking_close` and `evaluate_carrier_obligation` enforce the executed-plan and implemented-spec rules.
  - Depends on: E-02
  - Expected outcome: all tests in `tests/test_backlog_close_evidence_plan_disposition.py` and `tests/test_check_engine.py` pass, `tests/test_carrier_detail_descriptive_bound.py` passes, and `resolve_evidence_artifact` still returns `True` for existing in-tree pending plans and non-implemented specs.
  - Execution state: pending

### Task group 3: documentation and decision record

- [ ] E-04 Update the release-gate prose in `AGENTS.md`, `.aw/records/backlog/README.md`, and `CHANGELOG.md`.
  - In `AGENTS.md`'s repo-local `## Release gates (Blocks-Release)` section (below `<!-- /aw:block -->`), update `(2) SATISFIED, a resolvable in-tree artifact citation` so it states that a cited plan must be executed and a cited spec must be implemented.
  - In `.aw/records/backlog/README.md`, update item 1 of the "real controls on backlog transitions" list so the parenthetical states that a cited plan must be executed and a cited spec must be implemented.
  - In `CHANGELOG.md` under `## 2.0.0 (pending)`, update or add a `- Fixed:` bullet stating that `- Carrier-Evidence:` now refuses a cited plan that is not in `executed/` and both `--evidence` (`- Close-Evidence:`) and `- Carrier-Evidence:` now refuse a cited spec whose status is not `implemented`. Write user-facing prose in `AGENTS.md` and `CHANGELOG.md` with no em or en dashes.
  - Depends on: E-03
  - Expected outcome: `AGENTS.md` (below `<!-- /aw:block -->`), `.aw/records/backlog/README.md`, and `CHANGELOG.md` accurately describe both rules and introduce zero em or en dashes.
  - Execution state: pending

- [ ] E-05 Append a `DECISIONS.md` entry with the next free `D<n>` (`D167` is the last at authoring HEAD `bb28b833a`; re-check at execution) in the file's `Context` / `Decision` / `Applied` format, recording the `bkprhk` decision that extends `D165`: (1) `- Carrier-Evidence:` in `check_engine.evaluate_carrier_obligation` shares `_evidence_plan_unshipped` with `evaluate_blocking_close`, because a non-executed plan in `pending/` belongs on the `HANDOFF` route (`- Carrier: <id6>`, which tracks completion via `find_obligations_carried_by`, `check.ipd-carrier-ungated`, and `runner_shared.perform_carrier_verification`) while `not-executed/`, `superseded/`, and `reusable/` plans do not discharge an obligation; (2) both `evaluate_blocking_close` (`- Close-Evidence:`) and `evaluate_carrier_obligation` (`- Carrier-Evidence:`) refuse a cited spec unless `_evidence_spec_unshipped` is `False` (`- Status: implemented`, and in `implemented/` when under a status subdirectory), aligning `SATISFIED` with `evaluate_blocking_close`'s `HANDOFF` arm (`_carrier_is_executed`) and preventing an unimplemented spec from serving as a backdoor carrier in `evaluate_carrier_obligation` (where specs are excluded from `_CARRIER_TARGET_TYPES` per the 2026-09-10 maintainer ruling in `rnkqrc` OQ-01/OQ-05); (3) both checks live in the predicates rather than `resolve_evidence_artifact` so the predicates can distinguish an unshipped plan or spec from a missing path and emit specific refusal reasons and remedies; (4) NO new cutover or grandfathering mechanism is required because `check_durable_carrier` sweeps only `pending/` plans (and `ipd_lint._merge_durable_carrier` runs only at `pre-transition`), so terminal `executed/`, `not-executed/`, and `superseded/` plans are already grandfathered by scope, the motivating `wyk11f -> j7dsci` citation from `bkprhk` already moved to `executed/`, all 6 live `pending/` `Carrier-Evidence:` rows cite existing `executed/` plans (5) or `backlog/open/` alongside a live `- Carrier:` (1), and all 52 live `Close-Evidence:` rows in `backlog/done/` cite `executed/` plans (48) or a walkthrough (4) with zero citing specs; and (5) `backlog/` citations in `Carrier-Evidence:` are deliberately left unchanged because `bkprhk` scoped the question to plans and specs. Cite `3392n9`, `ncmugb`, `bkprhk`, `7lfe87`, and `D165`.
  - Depends on: E-04
  - Expected outcome: one new uniquely numbered `DECISIONS.md` entry recording all five points and citing `3392n9`, `ncmugb`, `bkprhk`, `7lfe87`, and `D165`.
  - Execution state: pending

### Task group 4: verify zero blast radius on the live corpus and full test suite

- [ ] E-06 Re-derive the live `Close-Evidence:` and `Carrier-Evidence:` corpus censuses, run `aw check release-gates --agent`, `aw check plans --agent`, and `aw check --agent` to compare per-rule counts against the authoring baseline in F-06 (confirming zero new `check.blocking-item-closed-without-gate` and zero new `check.ipd-uncarried-obligation` findings), re-run the three HEAD reproduction probes from F-01 and F-02 to confirm all three now return `legitimate=False` with the new refusal reasons, and run the bare full test suite (`python3 -m pytest`) to compare its summary line and failing node-id set against E-01.
  - Depends on: E-05
  - Expected outcome: zero new `check.blocking-item-closed-without-gate` or `check.ipd-uncarried-obligation` findings on the live corpus, all three F-01/F-02 probes refused with specific reasons, and no new failing pytest node ids compared to E-01.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `check_engine.evaluate_carrier_obligation` is the single per-row predicate behind both `check_engine.evaluate_durable_carrier` (called by `check_engine.check_durable_carrier` in `aw check` and by `ipd_lint._merge_durable_carrier` in `aw ipd lint --phase pre-transition`) and direct callers. `check_engine.evaluate_blocking_close` is the single predicate behind both `aw backlog set` CLI spellings, `set_records.close_on_answer`, and `check_engine.check_release_gate_consistency`.
- `evaluate_durable_carrier` strips the leading `f"{ob.locator}: "` prefix from `verdict.reason` and packs grouped clauses into `Drift.detail` under `attention_contract.MAX_DESCRIPTIVE_LEN` (`300`), with a single-locator floor when even one clause exceeds the budget. Every `evaluate_carrier_obligation` failure reason must therefore be single-line, `is_safe_descriptive`-clean, and concise enough that a single locator plus a long clustered path stays under 300 characters (`tests/test_carrier_detail_descriptive_bound.py`).
- Plan disposition is directory-derived (`executed/` under `.aw/records/plans/` or `.agents/plans/`), whereas spec lifecycle state is carried in `- Status: implemented` (and, in the status-bucketed layout under `.aw/records/specs/<status>/`, the `implemented/` subdirectory; see `check_engine._carrier_is_executed` and `specs.SPECS_ROOT`).
- Tests must exercise observable behavior through CLI commands and predicate calls, never inspecting source code (`AGENTS.md`, `GUIDING_PRINCIPLES` P16). The full test suite is run bare as `python3 -m pytest`.
- User-facing prose in `AGENTS.md` and `CHANGELOG.md` must contain no em or en dashes.

## Findings

| # | Finding | Evidence (measured at HEAD `bb28b833a`) | Consequence |
|---|---|---|---|
| F-01 | `evaluate_carrier_obligation` (`SATISFIED` arm) accepts a pending plan and an approved spec at HEAD. | `evaluate_carrier_obligation(repo, CarrierObligation("deferred", "p:Deferred[1]", 10, {"Carrier-Evidence": ".aw/records/plans/pending/20261014-2ohbkj-01-aka0li-...ipd.md"}))` returned `legitimate=True, path='SATISFIED'`, and the same call citing `.aw/records/specs/approved/20261001-89xjll-01-89xjll-...spec.md` also returned `legitimate=True, path='SATISFIED'`. | Both defects in `evaluate_carrier_obligation` reproduce at HEAD; E-02 pins them and E-03 fixes them. |
| F-02 | `evaluate_blocking_close` (`SATISFIED` arm) accepts a non-implemented spec at HEAD. | `evaluate_blocking_close(repo, Path(".aw/records/backlog/done/20261001-evidpend-01-7lfe87-...backlog.md"), "done", evidence=".aw/records/specs/approved/20261001-89xjll-01-89xjll-...spec.md", carrier_index={})` returned `legitimate=True, path='SATISFIED', reason="gate 'next' satisfied by resolvable evidence '...'"`, whereas the `HANDOFF` arm (`_carrier_is_executed`) requires `_status_meta(text) == "implemented"` for a `.spec.md` carrier. | The backlog close predicate's `SATISFIED` and `HANDOFF` arms disagree on specs; E-01 pins this and E-03 aligns them. |
| F-03 | Keeping the checks in the two predicates (rather than returning `False` from `resolve_evidence_artifact`) preserves specific refusal diagnostics. | `evaluate_blocking_close` (plan `ncmugb` E-02) calls `resolve_evidence_artifact` first and then `_evidence_plan_unshipped` so it can emit `names a plan that has not shipped (is not in executed/)` instead of falling through to the generic missing/unresolvable refusal (`tests/test_backlog_close_evidence_plan_disposition.py::test_case_h_refusal_reason_names_path_and_unshipped_preserves_bytes`). | E-03 adds `_evidence_spec_unshipped` as a sibling helper called in both predicates rather than mutating `resolve_evidence_artifact`'s boolean return. |
| F-04 | Terminal plans (`executed/`, `not-executed/`, `superseded/`) are already grandfathered by scope, and the motivating `wyk11f` citation no longer resolves to `pending/`. | `check_engine.check_durable_carrier` filters `if "pending" not in p.parts: continue` (`_iter_type_files` also skips retired buckets by default), and `ipd_lint._merge_durable_carrier` runs only at `_CARRIER_CHECKPOINTS = frozenset(("pre-transition",))` while `check_ipd_lint_reach` sweeps at `checkpoint="author"`. Moreover, in executed plan `wyk11f`, `- Carrier-Evidence: .aw/records/plans/pending/20261001-tf4jz5-01-j7dsci-...ipd.md` already has `exists() == False` because `j7dsci` executed and moved to `.aw/records/plans/executed/20261001-tf4jz5-01-j7dsci-...ipd.md`. | No new cutover key or per-plan exemption table is needed to grandfather historical `executed/` plans; E-02 tests this scope boundary and E-05 records it in `DECISIONS.md`. |
| F-05 | Live corpus census of `Carrier-Evidence:` and `Close-Evidence:` shows zero active violations under the new rules. | Across `.aw/records/plans/`, 242 `Carrier-Evidence:` rows exist (228 in `executed/`, 5 in `not-executed/`, 3 in `superseded/`, 6 in `pending/`). In `pending/` (the only directory swept by `check_durable_carrier`), 5 rows cite existing `.aw/records/plans/executed/*.ipd.md` files (`vzk1iw` row 4, `6jp1ox` rows 1/2/4, `k93w2g` row 2) and 1 cites `.aw/records/backlog/open/...` alongside `- Carrier: uu4rfe` (`ww744p` row 1); zero `pending/` rows cite a non-executed plan or any spec. Across `.aw/records/backlog/`, all 52 `Close-Evidence:` rows in `done/` cite existing `plans/executed/*.ipd.md` files (48) or walkthrough `04qifi` (4); zero cite a spec. | Tightening both predicates produces zero new findings on the live repository corpus. |
| F-06 | Baseline `aw check` counts at authoring HEAD `bb28b833a`. | `aw check release-gates --agent`: `outcome="conforms"`, `findings=0` (`check.blocking-item-closed-without-gate`: 0). `aw check plans --agent`: `findings=20` (`error`: 2, `warning`: 0, `info`: 18), with `check.ipd-uncarried-obligation`: 1 (`uiej2a`, missing carrier on deferred item) and `check.ipd-carrier-finished-unverified`: 1 (`z2ugxc`, finished carrier `x04bve`). | E-06 compares post-change `aw check` output against these exact baseline counts. |
| F-07 | `evaluate_durable_carrier` enforces `attention_contract.MAX_DESCRIPTIVE_LEN` (`300`) on `Drift.detail`. | `tests/test_carrier_detail_descriptive_bound.py` asserts `is_safe_descriptive(d.detail)` and `len(d.detail) <= 300` on every `Drift` returned by `evaluate_durable_carrier`. With a single long clustered path (~115 chars) and locator `Deferred / out of scope [1]: ` (29 chars) plus header `1 obligation(s) name no durable carrier: ` (41 chars), a reason suffix of ~75 chars keeps total `Drift.detail` around 260 chars (`<= 300`). | E-03 keeps the new `evaluate_carrier_obligation` refusal reasons concise and single-line, putting the longer remediation guidance in `fixes`. |

## Proposed changes (ordered, validatable)

1. E-01: extend `tests/test_backlog_close_evidence_plan_disposition.py` with spec-citation refusal and acceptance tests across `evaluate_blocking_close`, both `aw backlog set` CLI spellings, `--dry-run`, and at-rest `check_release_gate_consistency`, and capture the bare `python3 -m pytest` baseline.
2. E-02: add `TestCarrierEvidencePlanAndSpecDisposition` in `tests/test_check_engine.py` covering `evaluate_carrier_obligation`, `evaluate_durable_carrier`, `ipd_lint.lint_file(..., checkpoint="pre-transition")`, `MAX_DESCRIPTIVE_LEN`, and `check_durable_carrier`'s pending-only sweep.
3. E-03: implement `_evidence_spec_unshipped` in `agent_workflows/check_engine.py`, wire it into `evaluate_blocking_close` (`SATISFIED` arm), wire both `_evidence_plan_unshipped` and `_evidence_spec_unshipped` into `evaluate_carrier_obligation` (`SATISFIED` arm), and update docstrings/comments in `agent_workflows/check_engine.py` and `agent_workflows/ipd_schema.py`.
4. E-04: update repo-local `AGENTS.md`, `.aw/records/backlog/README.md`, and `CHANGELOG.md`.
5. E-05: record the decision and grandfathering rationale in `DECISIONS.md`.
6. E-06: re-verify the live corpus censuses, `aw check` rules, HEAD reproduction probes, and full `python3 -m pytest` suite.

## Deferred / out of scope (with reason)

- Restricting `backlog/` paths cited in `- Carrier-Evidence:` or `- Close-Evidence:` by backlog status (`open`/`graduated`/`done`). Out of scope because backlog `bkprhk` explicitly scopes the decision to plan citations (`executed/`) and spec citations (`implemented`), and an open backlog obligation should be linked via `- Carrier: <id6>` (though `ww744p` row 1 currently pairs `- Carrier: uu4rfe` with `- Carrier-Evidence: .aw/records/backlog/open/...`).
  - Carrier-Declined: backlog `bkprhk` scopes the parity rule to plans (`executed/`) and specs (`implemented`); no defect was filed for backlog path citations.
- Repairing historical `executed/` plans whose `- Carrier-Evidence:` rows cite vanished `pending/` or `specs/approved/` paths (F-04, F-05). `AGENTS.md` ("Agent execution contract") forbids editing plans already in `.aw/records/plans/executed/`, and `check_durable_carrier` intentionally sweeps only `pending/` plans.
  - Carrier-Declined: `executed/` plans are immutable records by repository contract and are outside `check_durable_carrier`'s pending-only sweep by design.

## Scope check

- Over-scope: none. Only `agent_workflows/check_engine.py`, `agent_workflows/ipd_schema.py`, the two existing test modules (`tests/test_backlog_close_evidence_plan_disposition.py` and `tests/test_check_engine.py`), `AGENTS.md`, `.aw/records/backlog/README.md`, `CHANGELOG.md`, and `DECISIONS.md` are modified.
- Under-scope: none. Backlog `bkprhk` asks whether `Carrier-Evidence` (`evaluate_carrier_obligation` `SATISFIED`) citing a plan should require `executed/`, whether a cited spec should require `implemented` across the evidence callers, and how existing rows are grandfathered. E-01 through E-06 answer and implement all three parts and record the decision in `DECISIONS.md`.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_backlog_close_evidence_plan_disposition.py tests/test_check_engine.py -k "Evidence or CarrierEvidence" -v` before E-03 (new refusal cases fail, acceptance/grandfathering cases pass) and after E-03 (all pass), pasted.
- `python3 -m pytest -o addopts="" tests/test_backlog_close_evidence_plan_disposition.py tests/test_check_engine.py tests/test_carrier_detail_descriptive_bound.py tests/test_carrier_finished_verification.py tests/test_backlog_handoff_close.py tests/test_backlog_positional_close_gate.py tests/test_specs_evidence_gate_parity.py tests/test_check_engine_release_gate.py tests/test_carrier_reverse_lookup.py -v` after E-03, pasted.
- Bare `python3 -m pytest` before E-03 (in E-01) and after E-05 (in E-06), summary lines pasted and failing node-id sets compared by name.
- `aw check release-gates --agent`, `aw check plans --agent`, and `aw check --agent` after E-03, compared to F-06.

## Spec / documentation sync

- No `.spec.md` is modified. Spec `llbr2b` (`to-review`) and draft spec `pqsx96` describe `SATISFIED` as resolvable in-tree evidence; requiring a cited plan to be `executed` and a cited spec to be `implemented` refines what qualifies as satisfying evidence of finished work without contradicting any spec clause.
- `agent_workflows/ipd_schema.py`, `AGENTS.md` (repo-local `## Release gates (Blocks-Release)` section), `.aw/records/backlog/README.md`, `CHANGELOG.md`, and `DECISIONS.md` are updated in E-03, E-04, and E-05.

## Open questions

### OQ-01: Should `Carrier-Evidence` require `executed/` for plans and should both evidence predicates require `implemented` for specs, and how are existing rows grandfathered?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED YES to both rules, with zero new grandfathering mechanism needed, from repository evidence. (1) In `evaluate_carrier_obligation`, `- Carrier-Evidence:` is the `SATISFIED` route ("discharged by finished work"), whereas `- Carrier: <id6>` is the `HANDOFF` route for a live `pending/` plan (which `find_obligations_carried_by`, `check.ipd-carrier-ungated`, and `runner_shared.perform_carrier_verification` track until execution). Accepting a non-executed plan in `Carrier-Evidence:` hides unexecuted or abandoned work from those gates. (2) For specs, `evaluate_blocking_close`'s `HANDOFF` arm (`_carrier_is_executed`) already requires `- Status: implemented` for a `.spec.md` carrier, and `evaluate_carrier_obligation` excludes specs from `_CARRIER_TARGET_TYPES` per the 2026-09-10 maintainer ruling (`rnkqrc` OQ-01/OQ-05: a spec is supporting material, never a handoff carrier); once a spec is `implemented` (which `specs._evidence_resolvable` gates on an executed IPD), its work has shipped. (3) Existing rows need no new cutover because `check_durable_carrier` sweeps only `pending/` plans (F-04), the motivating `wyk11f -> j7dsci` target in `bkprhk` has already executed and moved to `executed/` (F-04), and the live `pending/` `Carrier-Evidence:` and `done/` `Close-Evidence:` corpora have zero non-executed plan or non-implemented spec citations (F-05). Recorded in `DECISIONS.md` (E-05).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_backlog_close_evidence_plan_disposition.py -v` output from BEFORE E-03 showing every new spec-refusal test FAILING and every spec-acceptance and existing plan-disposition test PASSING, plus the pre-change bare `python3 -m pytest` summary line and sorted failing node ids.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_check_engine.py -k "CarrierEvidencePlanAndSpecDisposition" -v` output from BEFORE E-03 showing every unshipped-plan and unshipped-spec refusal test FAILING and every shipped-plan, shipped-spec, non-plan/spec artifact, and `executed/`-plan grandfathering test PASSING.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: (a) pasted `-v` output after E-03 for `tests/test_backlog_close_evidence_plan_disposition.py`, `tests/test_check_engine.py -k "CarrierEvidencePlanAndSpecDisposition"`, and the related test modules listed in `## Required tests / validation` with all tests passing; (b) pasted `python3 -c` output confirming `resolve_evidence_artifact` still returns `True` on an existing `pending/` plan and an existing `specs/approved/` spec while `_evidence_plan_unshipped` and `_evidence_spec_unshipped` return `True` on those paths and `False` on `plans/executed/` and `specs/implemented/` paths; and (c) quoted `git diff` hunks in `agent_workflows/check_engine.py` and `agent_workflows/ipd_schema.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: quoted changed lines from `AGENTS.md`, `.aw/records/backlog/README.md`, and `CHANGELOG.md`; pasted `git diff -U0 AGENTS.md` confirming all edits lie below line `<!-- /aw:block -->`; and pasted `git diff -U0 CHANGELOG.md AGENTS.md .aw/records/backlog/README.md | grep '^+' | rg -c "[\u2013\u2014]"` printing `0` (or no matches).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the new `DECISIONS.md` entry quoted in full and pasted `grep -c "^### D<n>\." DECISIONS.md` printing `1` for its number, showing the five points and citations to `3392n9`, `ncmugb`, `bkprhk`, `7lfe87`, and `D165`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: (a) pasted re-derived `Close-Evidence:` and `Carrier-Evidence:` corpus censuses and pasted outputs of `aw check release-gates --agent`, `aw check plans --agent`, and `aw check --agent` compared against F-06 with zero new `check.blocking-item-closed-without-gate` or `check.ipd-uncarried-obligation` findings; (b) pasted output of the three F-01/F-02 `python3 -c` reproduction probes after E-03 showing `legitimate=False` and the new refusal reasons; and (c) the post-change bare `python3 -m pytest` summary line and failing node-id set compared against V-01.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Reviewer focus: verify that `_evidence_spec_unshipped` handles both status-bucketed (`.aw/records/specs/<status>/`, including sharded `implemented/YYYYMM/`) and flat legacy (`.agents/docs/specs/`) spec paths relative to the repo root, that `evaluate_carrier_obligation`'s new refusal reasons fit within `attention_contract.MAX_DESCRIPTIVE_LEN` (`300`), and that existing `executed/` plans are unaffected because `check_durable_carrier` sweeps only `pending/` plans (F-04, F-05).

Execution contract: OQ-01 is resolved; no open questions remain. Scope fence (a declaration, not a stop rule): only the `Scope-Paths` files are expected to change; an out-of-scope edit that proves necessary is made and justified at finalize with `--scope-reason` (and `--scope-ack` for a declared path left unmodified). Commit only the `Scope-Paths` files through `aw commit 3392n9 -- <paths>`, never `git add -A`, never push. Edit only the repo-local `AGENTS.md` release-gates section (below `<!-- /aw:block -->`), never the managed block. Verify the staged set with `git diff --cached --name-only` before committing. Paste actual runner output for every test and check claim. Lifecycle: under `aw oc run` / `aw agy run` the runner performs finalize and the lifecycle move; by hand, run `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms; never hand-`git mv` or hand-edit `- Status:`. Do not set backlog `bkprhk` `done` from this plan (the runner's close step handles it after execution).
