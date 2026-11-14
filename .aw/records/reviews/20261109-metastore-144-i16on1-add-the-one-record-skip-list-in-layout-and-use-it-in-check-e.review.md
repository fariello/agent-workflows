# Review findings: plan i16on1

- Subject-Id: i16on1
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `eab882ca9` in a non-interactive runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-144-i16on1-add-the-one-record-skip-list-in-layout-and-use-it-in-check-e.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (`0` errors, `0` warnings, `0` info advisories). Live inspection against governing spec `4sd62s` (section 4.4, exclusion list bullet), sibling plans `dbq57g` and `ebrc4t`, `agent_workflows/layout.py`, `agent_workflows/check_engine.py`, `agent_workflows/selectors.py`, `agent_workflows/artifact_refs.py`, and `agent_workflows/artifact_core.py` uncovered one `HIGH`, one `MEDIUM`, and one `LOW` finding (`PR-001..PR-003`), all fixed in place. Pass 2 re-checked `E-01`, `E-02` and `V-01`, `V-02`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted Scope fence declaration and conditional runner/executor finalize clause | Added standard Scope fence declaration and conditional runner/executor ownership clause ("When `aw oc run` or `aw agy run` executes the plan...") | PR-001. |
| Open questions (OQ-01) | `- Owner: none` recorded on resolved question | Updated to `- Owner: plan author` and recorded decision in `### Decisions` (D-1) | PR-002. |
| Proposed changes, Behavior decisions | Lacked Requirement 12 Mermaid diagram and formatted behavior decisions | Added a Mermaid `flowchart TD` diagram to `Proposed changes` and formatted `## Behavior decisions` with D-1..D-3 | Proofreading, PR-003. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `i16on1` introduces public constants in `agent_workflows.layout` (`RECORD_SCAN_SKIP_NAMES` and `RECORD_SCAN_EXCLUDED_DIRS`), establishes the single skip list across the entire toolkit per spec `4sd62s` 4.4, and changes record walker traversal rules across `check_engine`, `selectors`, `artifact_refs`, and `artifact_core`.
2. No. It touches framework layout and traversal modules, not sandbox, commit lock, or isolation code.
3. No, it is right-sized at 2 E-items in 1 task group across 5 related framework modules and 1 test module.
4. Yes. `- Scope-Paths:` explicitly lists all 5 modules, the test module, and the plan file itself.
5. Yes. A bug in `_SKIP_NAMES` or `RECORD_SCAN_EXCLUDED_DIRS` filtering in `selectors` or `check_engine` could cause record discovery (`aw find`, `aw check`, `aw attention`, `aw ipd`) to skip valid records or falsely process excluded directories, corrupting attention views and check gates repository-wide.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 4.4, exclusion list bullet); parent plan `ebrc4t` (Order 32); prerequisite plan `dbq57g` (Order 143, creating `tests/test_readers_check_engine.py`); and framework modules `agent_workflows/layout.py`, `agent_workflows/check_engine.py`, `agent_workflows/selectors.py`, `agent_workflows/artifact_refs.py`, and `agent_workflows/artifact_core.py`.
- Found owner violation in OQ-01 (`PR-002`): OQ-01 recorded `- Owner: none` despite being resolved. Fixed by setting `- Owner: plan author` and recording D-1 in `### Decisions`.

### Step R2

- Checked: `E-*`/`V-*` bijection (`2/2`: `E-01, E-02` <-> `V-01, V-02`, with `- Highest E allocated: 02` preserved), dependency chain (`E-01 -> E-02`), `- Scope-Paths:` completeness, and runtime reachability of all `V-*` checks.
- Found missing Scope fence and incomplete lifecycle transition in Approval and execution gate (`PR-001`): gate lacked a Scope fence declaration and omitted the conditional runner/executor finalize clause required by `steps/s7-finalize.md`. Fixed in Gate.

### Step R3

- Checked: path traversal and excluded directory handling. Verified that `RECORD_SCAN_EXCLUDED_DIRS` cleanly excludes `records/meta/` internal logs across all record scanners, preventing metadata logs from being treated as record files, with zero impact on citation scans over `README.md`.

### Step R4

- Checked: single shared skip list requirement (`4sd62s` 4.4), backward-compatibility aliases for `runner_shared` and `status_set` imports, tuple ordering determinism, right-sizing (`2` `E-*` items, `6` work Scope-Paths), and outcome-based testing (`AGENTS.md`).

### Step R5

- Checked: QA/QC (dual verification of excluded meta dir across `aw find`, `aw check`, `aw attention` plus citation rewrite preservation in `README.md`), Architect (single canonical definition in `layout` eliminating 3 duplicated sets), Software Engineer (clean alias retention preventing breaking imports), and Modest Executor (two clear steps with exact regex and test commands).

### Step R6

- Checked: `2` `E-*` items in `1` task group across `6` work `- Scope-Paths:` entries (`- Size assessment: standard`; split from `ebrc4t` on 2026-11-09 per `nj8zdp`). No further split is required.

### Step R7

- Checked: `- Item-Dependencies: executed:g5hpbb, executed:tve77h, executed:xexn45, executed:w1cs3p, executed:na188y, executed:i3b5zu, executed:dbq57g` (all verified under `.aw/records/plans/pending/`), sibling plan `ebrc4t` (Order 32, retaining inline copies in `specs`, `releases`, `ipd_lint`), and retirement plan `9o83cr` (Order 11). All contracts align cleanly.

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`), updated owner from `none` to `plan author`; recorded three engineering decisions (`D-1..D-3`) in `### Decisions`, all `Reversible: yes`. Zero human-owned questions remain.

### Pass 2

- Re-reviewed `E-01`, `E-02` and `V-01`, `V-02` per `steps/s6-rereview.md` rule 1 after adding Scope fence, gate clauses, Mermaid diagram, and formatting decisions.
- Verified 2-to-2 `E-*`/`V-*` bijection, `- Highest E allocated: 02`, valid `- Scope-Paths:` and `- Item-Dependencies:`, zero em/en dashes, and `0` findings across all severities from `aw ipd lint --phase review-finalize --agent --verbose` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-144-i16on1-add-the-one-record-skip-list-in-layout-and-use-it-in-check-e.ipd.md:121 | Approval and execution gate omitted the required Scope fence declaration and conditional runner/executor finalize clause, required by steps/s7-finalize.md and rubric G. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added standard Scope fence declaration and conditional runner/executor ownership clause to Gate. Recommendation strength: strong. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / S5 / OQ-01 | .aw/records/plans/pending/20261109-metastore-144-i16on1-add-the-one-record-skip-list-in-layout-and-use-it-in-check-e.ipd.md:104 | OQ-01 recorded - Owner: none on a resolved question, violating the owner attestation standard in steps/s5-questions.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated - Owner: plan author in OQ-01 and recorded the decision in ### Decisions (D-1). Recommendation strength: strong. |
| PR-003 | LOW | IN-SCOPE | Proofreading / Technical writing standard Requirement 12 / R4 | .aw/records/plans/pending/20261109-metastore-144-i16on1-add-the-one-record-skip-list-in-layout-and-use-it-in-check-e.ipd.md:73, line 69 | Proposed changes lacked a Mermaid diagram required by requirement 12(b), and DECISIONS that govern this part was unformatted prose. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid flowchart TD diagram in Proposed changes and formatted ## Behavior decisions with D-1..D-3. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Why keep `_SKIP_NAMES` as aliases in `check_engine`, `selectors`, and `artifact_refs`? | Retain `_SKIP_NAMES` as module-level aliases of `layout.RECORD_SCAN_SKIP_NAMES` until Order 11 (`9o83cr`) retires them. | Delete immediately (rejected: breaks existing external imports in `runner_shared` and `status_set`). | `agent_workflows/runner_shared.py`, `agent_workflows/status_set.py`, spec `4sd62s` 4.4 | yes |
| D-2 | Where does the record skip list apply vs citation scans? | Record walkers skip `README.md`, `INDEX.md`, `STATUS.md`, and `records/meta/`; citation scans through `artifact_core.iter_scan_files` keep reading `README.md` while skipping `records/meta/`. | Exclude `README.md` from citation scans (rejected: breaks link tracking and citation rewrite); do not exclude `meta/` (rejected: treats logs as records). | `agent_workflows/artifact_refs.py:319`, spec `4sd62s` 4.4 | yes |
| D-3 | How should `RECORD_SCAN_SKIP_NAMES` and `RECORD_SCAN_EXCLUDED_DIRS` be structured? | Defined as immutable sorted tuples in `agent_workflows/layout.py` alongside `TRAVERSAL_EXCLUSIONS`. | Define as set or dict (rejected: tuples preserve deterministic traversal and serialization order). | `agent_workflows/layout.py:110` | yes |
