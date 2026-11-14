# Review findings: plan i3b5zu

- Subject-Id: i3b5zu
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `bc7623d11` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261107-metastore-31-i3b5zu-move-the-check-engine-release-gate-and-from-backlog-readers.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `0` advisories), the baseline test suites (`tests/test_check_engine_release_gate.py` and `tests/test_from_backlog_cardinality.py`) passed (`60 passed in 2.19s`), and the related release-gate suites (`tests/test_carrier_ungated_rule.py`, `tests/test_release_gate_one_way_mismatch.py`, `tests/test_backlog_positional_close_gate.py`, and `tests/test_backlog_gate_follows_status.py`) passed (`52 passed in 3.06s`). During revision, the plan file itself was added to `- Scope-Paths:`, `mkdir -p .aw/state/ffceq0 .aw/state/i3b5zu` was added to the PIN-FIRST rule, code citations were converted to `path::Symbol` identifiers, Behavior decisions were expanded to document `D-1` through `D-6`, a Mermaid `flowchart TD` diagram was added under `## Proposed changes`, class-qualified pytest node IDs were specified in `V-01`, and a narrow unsafe-condition stop rule was added to `Approval and execution gate`. Pass 2 re-checked the complete revised plan against `4sd62s`, `ffceq0`, `w1cs3p`, `na188y`, and `ebrc4t`, and `aw ipd lint --phase review-finalize --agent` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Scope-Paths, Readiness, Review-Depth | Omitted the plan file from `- Scope-Paths:` and omitted review output fields | Adds the plan file to `- Scope-Paths:` and adds `- Readiness: go-pending-approval` and `- Review-Depth: complex` | PR-001, PR-004. |
| Detailed Implementation Checklist (PIN-FIRST RULE, E-01) | Assumed `.aw/state/ffceq0/` already existed without directory creation and lacked class-qualified test node IDs | Adds `mkdir -p .aw/state/ffceq0 .aw/state/i3b5zu` and specifies `TestCheckEngineReleaseGateReadersOrder31` in `tests/test_readers_check_engine.py` | PR-003, PR-004. |
| Project conventions discovered (Step 0) | Cited code with unqualified `module.function` references | Cites `path::Symbol` identifiers for `check_engine.py`, `artifact_meta.py`, `plans.py`, `selectors.py`, and `attention_contract.py` | Technical Writing Standard Requirement 7, PR-002. |
| Findings (F-01..F-04) and Behavior decisions (D-1..D-6) | Stated baseline test counts without non-binding framing and listed only D-1 and D-4, omitting release-gate and From-Backlog query semantics | Adds `F-09` non-binding baseline counts and documents `D-1` through `D-6` covering absent vs empty gates (`D-2`), terminal carrier skipping (`D-3`), From-Backlog query resolution (`D-5`), and close-date history reading (`D-6`) | PR-004, PR-005. |
| Proposed changes and Deferred / out of scope | Two-line list with no diagram and terse carrier entries | Two ordered steps with a Mermaid `flowchart TD` diagram and complete carrier attributions (`w1cs3p`, `na188y`, `ebrc4t`, `t4gl15`, `ffceq0`) | Technical Writing Standard Requirement 12(b), PR-002, PR-005. |
| Validation and cross-check (V-01, V-02) and Approval and execution gate | V-01 lacked exact class-qualified pytest node IDs and Approval and execution gate lacked an unsafe-condition stop rule | Specifies 10 exact class-qualified pytest node IDs in `V-01` across `TestCheckEngineReleaseGateReadersOrder31` and adds a narrow unsafe-condition stop rule in `Approval and execution gate` | PR-003, PR-006. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `i3b5zu` moves 24 working-tree metadata read sites across 13 core release-gate, close-legitimacy, and `From-Backlog` handoff functions in `agent_workflows/check_engine.py` onto `artifact_meta`.
2. Yes. Governs release-blocking backlog closure, handoff gate inheritance, and dangling decision reference detection; regressions could silently allow ungated or invalid backlog closes into release manifests.
3. No (`2` production files in `- Scope-Paths:`, `2` right-sized `E-*` items), though `agent_workflows/check_engine.py` (10,919 lines) is pinned against 60 existing baseline tests across two suites plus related gate tests.
4. No. `- Scope-Paths:` names concrete files, and `i3b5zu` modifies a strictly disjoint subset of 13 functions within `check_engine.py` separate from Orders 29, 30, and 32.
5. No. Read-only migration of working-tree metadata queries onto cached SQLite and replayed state.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (Sections 4.3, 4.5, and 7 step 5); parent plan `ffceq0` (Order 08); sibling plans `w1cs3p` (Order 29), `na188y` (Order 30), and `ebrc4t` (Order 32); prerequisite plans `tve77h` (Order 02), `g5hpbb` (Order 14), and `xexn45` (Order 07); and production modules `agent_workflows/check_engine.py`, `agent_workflows/artifact_meta.py`, `agent_workflows/plans.py`, and `agent_workflows/attention_contract.py`.
- Verified that the 13 functions named in `i3b5zu` (`_from_backlog_value`, `_evidence_spec_unshipped`, `find_from_backlog_plans`, `find_from_backlog_specs`, `_carrier_is_executed`, `evaluate_blocking_close`, `_from_backlog_carrier_index`, `_item_close_date`, `check_release_gate_consistency`, `check_live_bug_gate`, `release_gate_warnings`, `check_decision_ref_dangling`, `_iter_live_gate_carriers`) cover exactly 24 working-tree metadata read lines, disjoint from Orders 29, 30, and 32 (`PR-005`).

### Step R2

- Checked: `E-*`/`V-*` 1:1 bijection (`E-01` <-> `V-01`, `E-02` <-> `V-02`), `- Highest E allocated: 02`, dependency order (`E-02` depends on `E-01`), `- Scope-Paths:` completeness (`5` paths, including the plan itself), and PIN-FIRST directory creation (`mkdir -p .aw/state/ffceq0 .aw/state/i3b5zu`).
- Replaced vague prose test descriptions with 10 exact class-qualified pytest node IDs under `TestCheckEngineReleaseGateReadersOrder31` in `V-01`, and verified the 60 baseline tests in `tests/test_check_engine_release_gate.py` (53 tests) and `tests/test_from_backlog_cardinality.py` (7 tests) (`PR-003`).

### Step R3

- Checked: Integrity and query safety. Ensured that `find_from_backlog_plans`, `find_from_backlog_specs`, and `_from_backlog_carrier_index` query `artifact_meta` for records declaring `from_backlog == item_id6` without whole-filesystem traversal, preserving exact `(path, blocks_release)` return types and distinguishing absent gates (`None`) from empty strings (`""`) (`D-2`, `D-5`).
- Verified that `_carrier_is_executed` and `check_release_gate_consistency` Rule 2 continue to skip terminal carriers (`executed`, `superseded`, `not-executed`) using cached metadata status (`D-3`).

### Step R4

- Checked: Behavioral decisions and invariant preservation:
  1. `D-1`: Multi-word plan status normalization (`executed` for `EXECUTED`/`DONE`, `legacy/unknown` otherwise).
  2. `D-2`: Preservation of distinct `None` vs `""` for `Blocks-Release` in `_from_backlog_carrier_index`.
  3. `D-3`: Narrowing `check_release_gate_consistency` Rule 2 to live carriers only.
  4. `D-4`: Region-bounded reading; status bullets outside metadata regions ignored.
  5. `D-5`: `From-Backlog` queries resolved via `artifact_meta` typed queries.
  6. `D-6`: Backlog item close-date reading derived from `artifact_meta.history` newest event dates.

### Step R5

- Checked: Architect (clean delegation of working-tree disk walks to indexed SQLite queries; clear boundary with git-content readers in `t4gl15`), Security/Integrity Reviewer (no bypass of release-blocking close gates; strict gate equality enforcement), QA/QC Engineer (10 exact class-qualified pytest node IDs in `TestCheckEngineReleaseGateReadersOrder31`; PIN-FIRST regression coverage with empty outcome diff), Software Engineer (defensive handling of missing records; identical return types across all 13 functions), and Modest Executor (two single-concern steps, each well within `IPD-Z603` bounds).

### Step R6

- Checked: `2` `E-*` items across `5` `- Scope-Paths:` entries (`4` work paths plus the plan file; `- Size assessment: standard`), satisfying `nj8zdp` and `IPD-Z603` bounds (`<=5` E-items, `<=8` work Scope-Paths, `0` advisories).

### Step R7

- Checked: `- Item-Dependencies: executed:g5hpbb, executed:tve77h, executed:xexn45` (`tve77h` verified executed; `g5hpbb` and `xexn45` verified in `metastore`), parent `ffceq0` (Order 08), sibling check_engine plans `w1cs3p` (Order 29), `na188y` (Order 30), and `ebrc4t` (Order 32), and downstream git-content reader plan `t4gl15` (Order 09).

### Step S5

- Checked: `OQ-01` (step-complexity limits satisfied at 14 and 24 units) and six technical decisions (`D-1`..`D-6` in `### Decisions` below, all `Reversible: yes`).
- Resolved all from repository code, `check_engine.py`, and approved spec `4sd62s`. Zero questions belong to the human under the `askme` three-way sort.

### Pass 2

- Re-reviewed the complete revised plan per `steps/s6-rereview.md` rules 1 and 2 because the plan file was added to `- Scope-Paths:`, `mkdir -p .aw/state/ffceq0 .aw/state/i3b5zu` was added to `PIN-FIRST RULE`, `D-2`, `D-3`, `D-5`, `D-6` were documented, and `V-01` gained exact test node IDs.
- Verified `E-01..E-02` <-> `V-01..V-02` 1:1 bijection, `- Highest E allocated: 02`, dependency order (`E-01` -> `E-02`), `- Scope-Paths:` (`5` files), compliance with all 12 requirements of `.aw/system/workflows/technical-writing/technical-writing.md`, and `aw ipd lint --phase review-finalize --agent` (`outcome: clean`, `findings: 0`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Scope-Paths | `.aw/records/plans/pending/20261107-metastore-31-i3b5zu-move-the-check-engine-release-gate-and-from-backlog-readers.ipd.md:7` | The plan file itself was omitted from `- Scope-Paths:`, which would prevent committing plan updates under `aw commit i3b5zu`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `.aw/records/plans/pending/20261107-metastore-31-i3b5zu-move-the-check-engine-release-gate-and-from-backlog-readers.ipd.md` to `- Scope-Paths:` (recommendation strength: very strong). |
| PR-002 | LOW | IN-SCOPE | Proofreading / Step 0, Proposed changes | `.aw/records/plans/pending/20261107-metastore-31-i3b5zu-move-the-check-engine-release-gate-and-from-backlog-readers.ipd.md:57`, `.aw/records/plans/pending/20261107-metastore-31-i3b5zu-move-the-check-engine-release-gate-and-from-backlog-readers.ipd.md:96` | `Proposed changes` lacked the Mermaid diagram required by Technical Writing Standard Requirement 12(b), and `Step 0` cited code using unqualified `module.function` symbols instead of repo-relative `path::Symbol` identifiers (`IPD-C801`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a Mermaid `flowchart TD` diagram under `Proposed changes` and converted code citations to `path::Symbol` identifiers (recommendation strength: strong). |
| PR-003 | MEDIUM | IN-SCOPE | R2 / R4 / E-01, V-01 | `.aw/records/plans/pending/20261107-metastore-31-i3b5zu-move-the-check-engine-release-gate-and-from-backlog-readers.ipd.md:41`, `.aw/records/plans/pending/20261107-metastore-31-i3b5zu-move-the-check-engine-release-gate-and-from-backlog-readers.ipd.md:135` | `V-01` did not name the specific test class or test methods in `tests/test_readers_check_engine.py`, leaving expected verification node IDs ambiguous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Named `TestCheckEngineReleaseGateReadersOrder31` in `E-01` and specified 10 exact class-qualified pytest node IDs in `V-01` covering all 10 reader methods (recommendation strength: very strong). |
| PR-004 | LOW | IN-SCOPE | R2 / PIN-FIRST | `.aw/records/plans/pending/20261107-metastore-31-i3b5zu-move-the-check-engine-release-gate-and-from-backlog-readers.ipd.md:35` | `PIN-FIRST RULE` redirected output to `.aw/state/ffceq0/` without explicitly running `mkdir -p .aw/state/ffceq0 .aw/state/i3b5zu`, which would fail on fresh worktrees where the directory has not yet been created. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `mkdir -p .aw/state/ffceq0 .aw/state/i3b5zu` to `PIN-FIRST RULE` (recommendation strength: very strong). |
| PR-005 | MEDIUM | IN-SCOPE | R1 / R4 / Behavior decisions | `.aw/records/plans/pending/20261107-metastore-31-i3b5zu-move-the-check-engine-release-gate-and-from-backlog-readers.ipd.md:91` | `## Behavior decisions` copied only generic decisions D-1 and D-4 from `ffceq0`, omitting explicit decisions governing absent vs empty gates (`D-2`), terminal carrier skipping (`D-3`), From-Backlog query resolution (`D-5`), and close-date history reading (`D-6`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Expanded `## Behavior decisions` to document `D-1` through `D-6` with precise query and field mapping contracts (recommendation strength: very strong). |
| PR-006 | LOW | IN-SCOPE | R7 / S7 / Approval and execution gate | `.aw/records/plans/pending/20261107-metastore-31-i3b5zu-move-the-check-engine-release-gate-and-from-backlog-readers.ipd.md:150` | `Approval and execution gate` lacked a narrow stop directive if prerequisite symbols from `xexn45` or `tve77h` (`artifact_meta.read`, `artifact_meta.query`, `artifact_meta.history`) are absent on HEAD, or if baseline test suites fail before the move. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a narrow unsafe-condition stop rule in `Approval and execution gate` while keeping `- Scope-Paths:` declaration-only (recommendation strength: strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should plan status be normalized when reading from `artifact_meta`? | For PLAN records only, match `plans.normalize_status` of the FIRST token of the cached raw value (`executed` for `EXECUTED`/`DONE`, `legacy/unknown` otherwise); all other record types use exact single-token matching. | Use raw un-normalized status across all readers (preserves 24 multi-word plan disagreement); normalize all types through `plans.normalize_status` (corrupts non-plan vocabulary). | `agent_workflows/plans.py:normalize_status`, `ffceq0` D-1, `4sd62s` Section 4.3 | yes |
| D-2 | How should `_from_backlog_carrier_index` distinguish between an absent gate and an empty gate? | Return `None` when an artifact has no `- Blocks-Release:` gate, and `""` when the gate is explicitly empty or malformed, preserving identical parity in `check_release_gate_consistency` Rule 2. | Coalesce missing gates to empty string `""` (breaks "no gate" vs "malformed gate" diagnostic distinction). | `agent_workflows/check_engine.py:6139`, `tests/test_check_engine_release_gate.py:1971` | yes |
| D-3 | How should `check_release_gate_consistency` Rule 2 determine whether a carrier is live versus terminal? | Check whether the carrier's cached `artifact_meta` status is in a terminal disposition (`executed`, `superseded`, `not-executed`); if terminal, skip the carrier. | Check filesystem path parts only (fails on in-memory or alternative backend records); check `is_retired` (improperly conflates live work with retired orchestrators). | `agent_workflows/check_engine.py:6586`, maintainer ruling 2026-09-12 (parent `qmgn12` OQ-03) | yes |
| D-4 | How should status bullets outside the metadata region be handled? | Region-bounded reading: bullets outside the metadata region are ignored. | Search entire file text for `- Status:` bullets (misidentifies quotes in review and walkthrough bodies). | `agent_workflows/selectors.py:metadata_region`, `ffceq0` D-4 | yes |
| D-5 | How should `find_from_backlog_plans`, `find_from_backlog_specs`, and `_from_backlog_carrier_index` locate carriers? | Query `artifact_meta` for records declaring `from_backlog == item_id6` via indexed SQLite tables, eliminating O(corpus) filesystem walks while returning identical `(path, blocks_release)` tuples. | Continue walking the disk with `_iter_plan_ipds` and `_iter_spec_records` (wastes hundreds of milliseconds per check run). | `agent_workflows/check_engine.py:5230`, `agent_workflows/check_engine.py:6125`, `4sd62s` Section 4.5 | yes |
| D-6 | How should `_item_close_date` extract the close date from backlog items? | Read `artifact_meta.history(item_id6)` events and extract the date of the newest record, formatting compact `YYYYMMDD`. | Run regex parsing over raw file text using `attention_contract.history_block` (bypasses structured event history). | `agent_workflows/check_engine.py:6152`, `4sd62s` Section 4.2a | yes |
