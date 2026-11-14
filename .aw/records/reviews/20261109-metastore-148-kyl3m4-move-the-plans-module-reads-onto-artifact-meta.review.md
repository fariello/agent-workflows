# Review findings: plan kyl3m4

- Subject-Id: kyl3m4
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `7cf91a0fa` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-148-kyl3m4-move-the-plans-module-reads-onto-artifact-meta.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `0` advisories), and baseline test suites (`tests/test_plans_index.py`, `tests/test_plans_archive.py`, `tests/test_plans_archive_selectors.py`, `tests/test_ipd_set_plan.py`, `tests/test_completion.py`) passed (`111 passed in 4.52s`). During revision, `Approval and execution gate` was updated with the standard conditional runner/executor finalize ownership clause, explicit item-dependencies enumeration, scope fence declaration, and narrow unsafe-condition stop rule (`PR-001`), `mkdir -p .aw/state/t4gl15 .aw/state/kyl3m4` was added to the PIN-FIRST rule and E-01 (`PR-002`), `## Findings` was expanded to document `D-1` through `D-5` under `### Behavior decisions` (`PR-003`), a Mermaid `flowchart TD` diagram was added under `## Proposed changes` (`PR-004`), `OQ-01` owner was updated to `plan author` (`PR-005`), code citations in `Step 0` were converted to repo-relative `path::Symbol` identifiers, the authoring prompt was replaced with a declarative conformance note, and front matter gained `- Readiness: go-pending-approval` and `- Review-Depth: complex` (`PR-006`). Pass 2 re-checked the complete revised plan against `4sd62s`, `t4gl15`, `jd7874`, `cb5eda`, and `63ib9r`, and `aw ipd lint --phase review-finalize --agent` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted conditional runner/executor finalize clause, explicit dependencies list, scope fence boundary clarification, and narrow stop rule | Added conditional runner/executor finalize ownership clause, explicit dependency list, scope fence clarification, and narrow unsafe-condition stop rule | PR-001, `steps/r2-executability.md` and `steps/s7-finalize.md`. |
| PIN-FIRST rule & E-01 | Redirected baseline output into `.aw/state/t4gl15/` without ensuring directory existence | Added `mkdir -p .aw/state/t4gl15 .aw/state/kyl3m4` in the PIN-FIRST rule and in E-01 | PR-002, ensure isolated lane worktrees succeed without redirection failure. |
| Findings (Behavior decisions) | Listed only D-1 under DECISIONS, omitting D-2 through D-5 | Added full D-1 through D-5 documentation under `### Behavior decisions` matching `t4gl15` and `jd7874` | PR-003, ensure self-contained decision ledger. |
| Proposed changes | Two-step prose summary without diagram | Added Mermaid `flowchart TD` diagram showing the 2-step staged pipeline | PR-004, Technical Writing Standard Requirement 12(b). |
| Open questions (OQ-01) | `- Owner: none` recorded on resolved question | Set `- Owner: plan author` on resolved question | PR-005, `steps/s5-questions.md` owner attestation rule. |
| Front matter, Step 0, Authoring prompt | Imperative authoring prompt, bare symbols in Step 0, omitted review readiness and tier in front matter | Replaced authoring prompt with declarative conformance note, standardized citations to `path::Symbol`, added `- Readiness: go-pending-approval`, `- Review-Depth: complex`, and review history record | PR-006, Technical Writing Standard Requirement 7 and Step S7. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `kyl3m4` moves `plans_index`, `plans_archive`, `plans_refs` read side, `ipd_set_plan`, and `completion` onto `artifact_meta.query`, affecting index scanning, archive query behavior, and tab completion across agent-workflows.
2. No. Scope-paths are `plans_index.py`, `plans_archive.py`, `plans_refs.py`, `ipd_set_plan.py`, `completion.py`, test files, and the plan file itself.
3. No. Right-sized at 2 `E-*` items in 2 task groups across 5 work modules in the plans family (`agent_workflows/plans_index.py`, `agent_workflows/plans_archive.py`, `agent_workflows/plans_refs.py`, `agent_workflows/ipd_set_plan.py`, `agent_workflows/completion.py`).
4. Yes. `- Scope-Paths:` explicitly names the 7 work paths plus the plan file itself.
5. Yes. `plans_index` and `plans_archive` govern plan discovery, status inspection, archive sweeping, and completion across 111 baseline tests.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 4.4, C5, C5a, AC-9); split parent `jd7874` (Order 35); split parent `t4gl15` (Order 09); downstream plans `cb5eda` (Order 153) and `9o83cr` (Order 11); orchestrator `63ib9r` (Order 00, row 148); and prerequisite plans `ffceq0` (Order 08), `g5hpbb` (Order 14), `h58z9n` (Order 33), `tve77h` (Order 02), and `xexn45` (Order 07).
- Verified that all 12 referenced `id6` identifiers resolve cleanly via `aw find all --agent` and all declared modules exist on HEAD `7cf91a0fa`.
- Found owner violation in `OQ-01` (`- Owner: none` on resolved question, `PR-005`), bare `module.function` citations in `Step 0` (`PR-006`), and missing D-2 through D-5 documentation in `## Findings` (`PR-003`). Fixed all in place.

### Step R2

- Checked: 2-to-2 `E-*`/`V-*` 1:1 bijection (`E-01..E-02` <-> `V-01..V-02`), `- Highest E allocated: 02`, dependency chain (`E-01 -> E-02`), `- Scope-Paths:` completeness, and runtime reachability of all `V-*` checks.
- Found missing directory creation for `.aw/state/t4gl15/` (`PR-002`) and missing conditional runner vs. standalone executor finalize ownership clause, explicit dependencies list, scope fence declaration, and narrow unsafe-condition stop rule in `Approval and execution gate` (`PR-001`). Fixed both in place.

### Step R3

- Checked: access control, query safety, path traversal safety, and index drift verification. Verified that `artifact_meta.query` safely filters by type, status, and Set without shell execution, and plan indexing does not bypass leak-sanitizer constraints.

### Step R4

- Checked: behavioral decisions and invariant preservation:
  1. `D-1`: Multi-word plan status normalization (`executed` for `EXECUTED`/`DONE`, `legacy/unknown` otherwise); non-plan records retain exact single-token status.
  2. `D-2`: `plans_index.plan_entry` field extraction retains standard field dictionary (`Id`, `Status`, `Set`, `Order`, `Date`, etc.) and populates from `artifact_meta.query` without depending on regex patterns.
  3. `D-3`: `plans_index.check_drift` and `aw index plans --check` verify disk records against `INDEX.json` using `artifact_meta.query`; drift output matches baseline except for D-1 normalized statuses.
  4. `D-4`: `plans_archive` walker skips non-plan directories (`records/meta/`, `records/research/`, etc.) and legacy index markers (`README.md`, `INDEX.md`, `STATUS.md`).
  5. `D-5`: State directory initialization (`mkdir -p .aw/state/t4gl15 .aw/state/kyl3m4`).
- Verified test determinism (`-p no:randomly -n 0`), right-sizing (`2` `E-*` items, `7` work Scope-Paths), and Requirement 12(b) diagram coverage (`PR-004`).

### Step R5

- Checked: Architect (clean migration of plans modules onto `artifact_meta.query`, eliminating dependency on `INDEX.json` per AC-9), Security Reviewer (safe path traversal and regex elimination), QA/QC (baseline outcome list diffs, 111 verified baseline tests across 5 modules), Software Engineer (clean typing, preservation of `plan_entry` signature), and Modest Executor (2 bounded `E-*` items in 2 task groups).

### Step R6

- Checked: `2` `E-*` items in `2` task groups across `7` work `- Scope-Paths:` entries (`- Size assessment: standard`; split from `jd7874` on 2026-11-09 per research `nj8zdp` guidance). No further split is required.

### Step R7

- Checked: `- Item-Dependencies: executed:ffceq0, executed:g5hpbb, executed:h58z9n, executed:tve77h, executed:xexn45` (all verified in `metastore`), parent `jd7874` (which depends on `kyl3m4`), downstream child `cb5eda` (Order 153), Order 11 `9o83cr` (which deletes INDEX writers), split parent `t4gl15`, and orchestrator `63ib9r` (row 148). Contracts align coherently across all related artifacts.

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`), updated owner from `none` to `plan author`; recorded five engineering decisions (`D-1..D-5`) under `### Behavior decisions` and `### Decisions` below, all `Reversible: yes`. Zero human-owned questions remain (`questions: []`).

### Pass 2

- Re-reviewed `E-01..E-02` and `V-01..V-02` per `steps/s6-rereview.md` rule 1 after adding gate clauses, state directory initialization, behavior decisions, and Mermaid process diagram.
- Verified 2-to-2 `E-*`/`V-*` bijection, `- Highest E allocated: 02`, valid `- Scope-Paths:` and `- Item-Dependencies:`, zero em/en dashes in user-facing text, and `0` findings across all severities from `aw ipd lint --phase review-finalize --agent` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-148-kyl3m4-move-the-plans-module-reads-onto-artifact-meta.ipd.md:154 | `Approval and execution gate` omitted conditional runner vs. standalone executor ownership of `aw ipd finalize`, explicit dependency list, scope fence boundary clarification, and narrow unsafe-condition stop rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional runner vs. executor ownership clause, explicit dependency list, scope fence clarification, and narrow stop rule to Gate (recommendation strength: very strong). |
| PR-002 | MEDIUM | IN-SCOPE | R2 / R4 / PIN-FIRST rule & E-01 | .aw/records/plans/pending/20261109-metastore-148-kyl3m4-move-the-plans-module-reads-onto-artifact-meta.ipd.md:38, .aw/records/plans/pending/20261109-metastore-148-kyl3m4-move-the-plans-module-reads-onto-artifact-meta.ipd.md:44 | PIN-FIRST rule and E-01 redirected baseline dumps into `.aw/state/t4gl15/` without directory initialization (`mkdir -p .aw/state/t4gl15 .aw/state/kyl3m4`), which fails in fresh isolated lane worktrees where `.aw/state/` does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `mkdir -p .aw/state/t4gl15 .aw/state/kyl3m4` in the PIN-FIRST rule and in E-01 (recommendation strength: strong). |
| PR-003 | MEDIUM | IN-SCOPE | R1 / R4 / Findings & Behavior decisions | .aw/records/plans/pending/20261109-metastore-148-kyl3m4-move-the-plans-module-reads-onto-artifact-meta.ipd.md:83 | `## Findings` stated decisions were copied from `t4gl15`, but omitted D-2 through D-5 covering `plan_entry` field preservation, drift verification, non-plan exclusion, and directory initialization. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Expanded `## Findings` to document D-1 through D-5 under `### Behavior decisions` matching `t4gl15` and `jd7874` (recommendation strength: strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Requirement 12(b) | .aw/records/plans/pending/20261109-metastore-148-kyl3m4-move-the-plans-module-reads-onto-artifact-meta.ipd.md:93 | `Proposed changes` lacked a Mermaid `flowchart TD` diagram required by Technical Writing Standard Requirement 12(b) for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram under `Proposed changes` showing the 2-step staged pipeline (recommendation strength: strong). |
| PR-005 | LOW | IN-SCOPE | R1 / S5 / OQ-01 | .aw/records/plans/pending/20261109-metastore-148-kyl3m4-move-the-plans-module-reads-onto-artifact-meta.ipd.md:132 | `OQ-01` recorded `- Owner: none` on a resolved question, violating the owner attestation standard in `steps/s5-questions.md`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set `- Owner: plan author` on OQ-01 and logged the decision in `### Decisions` (recommendation strength: strong). |
| PR-006 | LOW | IN-SCOPE | Proofreading / Requirement 7 / S7 | .aw/records/plans/pending/20261109-metastore-148-kyl3m4-move-the-plans-module-reads-onto-artifact-meta.ipd.md:9, .aw/records/plans/pending/20261109-metastore-148-kyl3m4-move-the-plans-module-reads-onto-artifact-meta.ipd.md:20, .aw/records/plans/pending/20261109-metastore-148-kyl3m4-move-the-plans-module-reads-onto-artifact-meta.ipd.md:62 | Plan retained an imperative authoring-prompt note, used unqualified `module.function` citations in `Step 0`, and omitted review readiness and tier in front matter. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced authoring prompt with declarative conformance note, converted `Step 0` citations to repo-relative `path::Symbol` identifiers, added `- Readiness: go-pending-approval` and `- Review-Depth: complex` to front matter, and transitioned `- Status: reviewed` via `aw ipd set` (recommendation strength: very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `artifact_meta.query` match plan status for `plans_index`? | For PLAN records only, match `plans.normalize_status` of the FIRST token of the cached raw value (`executed` for `EXECUTED`/`DONE`, `legacy/unknown` otherwise); all other record types use exact single-token matching. | Keep raw unnormalized status across all readers; normalize non-plan vocabularies (rejected: corrupts non-plan statuses). | `t4gl15` D-1, `4sd62s` Section 4.3 | yes |
| D-2 | How should `plans_index.plan_entry` fields be preserved? | `plans_index.plan_entry` retains its standard field dictionary (`Id`, `Status`, `Set`, `Order`, `Date`, etc.) and populates them from `artifact_meta.query` without depending on regex patterns. | Alter field keys or drop legacy fields (rejected: breaks external consumers of plan index). | `agent_workflows/plans_index.py::plan_entry`, `jd7874` E-02 | yes |
| D-3 | How should `INDEX.json` drift check verify plan records? | `plans_index.check_drift` and `aw index plans --check` compare metadata against disk records using `artifact_meta.query`; drift output matches baseline except for D-1 status normalization. | Skip drift checking during transition; retain regex scanning (rejected: leaves drift checking unmigrated). | `agent_workflows/plans_index.py::check_drift`, `4sd62s` Section 4.4 | yes |
| D-4 | How should non-plan artifacts and meta directories be handled in `plans_archive`? | `plans_archive` walker skips non-plan directories (`records/meta/`, `records/research/`, etc.) and legacy index markers (`README.md`, `INDEX.md`, `STATUS.md`), matching core registry rules. | Walk all directories unconditionally (rejected: causes crash on JSONL event logs or non-plan markdown files). | `agent_workflows/plans_archive.py`, `4sd62s` Section 4.2 | yes |
| D-5 | Where should baseline test outcome lists be preserved across isolated lane worktrees? | Preserve `.aw/state/t4gl15/` as the baseline directory with explicit initialization (`mkdir -p .aw/state/t4gl15 .aw/state/kyl3m4`). | Use plan-specific `.aw/state/kyl3m4/` only (rejected: breaks finishing parent `jd7874`'s residual audit comparison). | `jd7874` E-01, `t4gl15` Task group 3 | yes |
