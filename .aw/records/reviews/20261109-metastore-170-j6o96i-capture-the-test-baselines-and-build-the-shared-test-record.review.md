# Review findings: plan j6o96i

- Subject-Id: j6o96i
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `dc4b370f7` in a non-interactive runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-170-j6o96i-capture-the-test-baselines-and-build-the-shared-test-record.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (`0` errors, `0` warnings, `0` info advisories). Live inspection against governing spec `4sd62s` (sections 6 and 7 step 6), research `nj8zdp`, sibling plans `7yr827`, `xexn45`, `g5hpbb`, `tve77h`, `ijpay0`, `59aiyh`, and `9rgn2w`, `tests/support.py`, and `agent_workflows/artifact_meta.py` uncovered one `HIGH`, three `MEDIUM`, and one `LOW` finding (`PR-001..PR-005`), all fixed in place. Pass 2 re-checked `E-13`, `E-01`, `E-15`, `E-16`, `E-17` and `V-13`, `V-01`, `V-15`, `V-16`, `V-17`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter, Item-Dependencies, Approval gate | Missing direct dependency on `7yr827` and cited only `xexn45`, `g5hpbb`, `tve77h` | Added `executed:7yr827` to `- Item-Dependencies:` and the gate prerequisite list | PR-001. |
| E-01, Step 0, OQ-01 | Cited `xexn45` E-01 and E-11 for `write_legacy` and `render_legacy_text` | Replaced stale citations with `7yr827` E-01 (and `xexn45` finishing part) | PR-001. |
| E-13 | Referenced unqualified "E-12 command" and stated golden fixture generating command is in E-02 docstring | Qualified full-suite command as `59aiyh` E-12 with explicit command, and specified documenting golden fixture generation in `tests/record_builder.py` module docstring | PR-002. |
| E-01 | PLACEMENT rule cited `artifact_types.TYPE_BACKENDS` for other types' default disposition directories | Cited layout model (`agent_workflows.layout.RecordClassDefinition`) default subpath and records root per type | PR-003. |
| Approval and execution gate | Lifecycle transition lacked conditional runner/executor ownership clause and explicit prohibition against hand `git mv` | Added standard conditional runner/executor ownership clause ("When `aw oc run` or `aw agy run` executes the plan...") and "never a hand `git mv`" | PR-004. |
| Proposed changes, Behavior decisions | Lacked Requirement 12 Mermaid diagram and recorded behavior decisions | Added a Mermaid `flowchart TD` diagram to `Proposed changes` and added `## Behavior decisions` documenting D-1..D-4 | Proofreading, PR-005. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `j6o96i` introduces `tests/record_builder.py` (`RecordBuilder`), the single test record builder for Phase B that all future test modules will use, supersedes `tests/support.py::ready_plan_text`, and establishes the tracked fixture `tests/fixtures/record_builder/ready_plan_text_golden.json` and baseline table `F-10` consumed by `ijpay0`, `59aiyh`, and subsequent plans in the metastore Set.
2. No. It only touches test infrastructure (`tests/record_builder.py`, `tests/support.py`, `tests/fixtures/...`) and the plan itself.
3. No, it is right-sized at 5 E-items across 2 task groups, modifying 2 python files (`tests/record_builder.py`, `tests/support.py`) and 1 fixture file.
4. Yes. `- Scope-Paths:` explicitly lists `tests/record_builder.py`, `tests/support.py`, `tests/fixtures/record_builder/ready_plan_text_golden.json`, and the plan file itself.
5. Yes. A mistake in `support.ready_plan_text` supersession (E-16) or builder bytes generation could break existing test callers across 15+ test modules, and flawed baseline capture in E-13/F-10 would invalidate the entire before/after regression verification in `59aiyh`.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (sections 6 and 7 step 6); research findings `.aw/records/research/20261108-plansize-01-nj8zdp-plan-size-calibration.findings.md`; sibling and prerequisite plans `7yr827` (`Order 21`), `xexn45` (`Order 07`), `tve77h` (`Order 02`), `g5hpbb` (`Order 14`), `ijpay0` (`Order 171`), `59aiyh` (`Order 10`), and `9rgn2w` (`Order 37`); and production/test modules `tests/support.py`, `agent_workflows/artifact_meta.py`, `agent_workflows/layout.py`, `agent_workflows/status_set.py`, `agent_workflows/review_findings.py`, `agent_workflows/ipd_authoring.py`, and `agent_workflows/artifact_naming.py`.
- Found stale citations to `xexn45` E-01 and E-11 in E-01, Step 0, and OQ-01 (`PR-001`): `xexn45` split its phase-B legacy renderer and in-memory text helpers to `7yr827` E-01 on 2026-11-07; citing `xexn45` directly without `7yr827` pointed to moved items and omitted the immediate provider of `write_legacy` and `render_legacy_text`. Fixed across front matter, E-01, Step 0, OQ-01, and Gate.
- Found cross-plan reference drift in E-13 (`PR-002`): E-13 cited "using the E-12 command" without naming `59aiyh` (no E-12 exists in `j6o96i`), and stated that the generating command for `ready_plan_text_golden.json` would be documented in "E-02's module docstring" (E-02 is in `ijpay0`, which runs after `j6o96i` and is excluded from `Scope-Paths:`). Fixed in E-13 and D-4.
- Found invalid module mapping in E-01 PLACEMENT rule (`PR-003`): E-01 cited `artifact_types.TYPE_BACKENDS` for other types' default disposition directories, whereas `TYPE_BACKENDS` maps CLI command handlers. Fixed by citing the layout model default subpaths and records root (`layout.RecordClassDefinition`).

### Step R2

- Checked: `E-*`/`V-*` bijection (`5/5`: `E-13, E-01, E-15, E-16, E-17` <-> `V-13, V-01, V-15, V-16, V-17`, with `- Highest E allocated: 17` preserved), dependency chain (`E-13 -> E-01 -> E-15 -> E-16 -> E-17`), `- Scope-Paths:` completeness, and runtime reachability of all `V-*` checks.
- Found lifecycle transition clause gap in Approval and execution gate (`PR-004`): the gate omitted the required conditional runner/executor ownership clause ("When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize j6o96i` itself") and "never a hand `git mv`", required by `steps/s7-finalize.md`. Fixed in Gate.

### Step R3

- Checked: `RecordBuilder` input validation, file permissions, and sandbox safety.
- Verified that all field names are validated against `artifact_meta.registry_fields`, values against event schemas, and `raw_fields` escape hatch is strictly confined to intentional defect testing (F-08) without bypassing default validations. Built test fixtures write to temporary fixture repositories (`tmp_path`) with no external network egress or sandbox escapes.

### Step R4

- Checked: `4sd62s` single shared builder requirement (section 6 and section 7 step 6), determinism (`when="2026-08-24"`, no clock reads), `text_only=True` in-memory rendering without disk I/O, `support.ready_plan_text` backward compatibility and byte parity against tracked golden fixture, right-sizing (`5` `E-*` items, `3` work Scope-Paths), and outcome-based testing (`AGENTS.md`).

### Step R5

- Checked: QA/QC (baseline and F-10 capture before code edits, core gate timing comparison), Testing and regression (golden file byte-for-byte check across all ~30 `ready_plan_text` call sites in 15 modules), Architect (`RecordBuilder` as the single Phase B switch point preparing for Order 13 cutover), Software Engineer (clean separation of class setup, method clusters, and supersession), and Modest Executor (five single-concern steps with explicit commands and evidence demands).

### Step R6

- Checked: `5` `E-*` items across `2` task groups and `3` work `- Scope-Paths:` entries (`- Size assessment: standard`; split from `9rgn2w` on 2026-11-09 per `nj8zdp`). Each item owns one cohesive concern inside `tests/record_builder.py`, `tests/support.py`, and `tests/fixtures/record_builder/ready_plan_text_golden.json`. No further split is required.

### Step R7

- Checked: `- Item-Dependencies: executed:g5hpbb, executed:tve77h, executed:7yr827, executed:xexn45` (`g5hpbb` verified under `.aw/records/plans/pending/`, `tve77h` verified executed, `7yr827` verified reviewed under `.aw/records/plans/pending/` providing `write_legacy` and `render_legacy_text`, `xexn45` verified under `.aw/records/plans/pending/`), downstream consumer `ijpay0` (`tests/test_record_builder.py`, Order 171), and batch migration plan `59aiyh` (`Order 10`). All method names, signatures, fixture paths, and baseline contracts align cleanly across the Set.

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`, carried from `59aiyh`), updated to incorporate `7yr827` alongside `xexn45`, `g5hpbb`, and `tve77h`; evaluated four engineering decisions surfaced by `PR-001..PR-004`.
- All four decisions (`D-1..D-4`) were established directly from repository evidence, `4sd62s` section 6 and section 7 step 6, `7yr827`, `xexn45`, `agent_workflows/layout.py`, and `tests/support.py`. Recorded in `### Decisions` (`D-1..D-4`), all `Reversible: yes`. Zero human-owned questions remain.

### Pass 2

- Re-reviewed `E-13`, `E-01`, `E-15`, `E-16`, `E-17` and `V-13`, `V-01`, `V-15`, `V-16`, `V-17` per `steps/s6-rereview.md` rule 1 after updating dependencies, renderer citations, placement rules, gate ownership clauses, and adding Mermaid diagram.
- Verified 5-to-5 `E-*`/`V-*` bijection, `- Highest E allocated: 17`, valid `- Scope-Paths:` and `- Item-Dependencies:`, zero em/en dashes, and `0` findings across all severities from `aw ipd lint --phase review-finalize --agent --verbose` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R1 / R7 / E-01, Step 0, OQ-01, Gate | `.aw/records/plans/pending/20261109-metastore-170-j6o96i-capture-the-test-baselines-and-build-the-shared-test-record.ipd.md:52`, line 82, line 140, line 176 | Plan cited `xexn45` E-01 and E-11 for `write_legacy` and `render_legacy_text`, but those items were split to `7yr827` E-01 on 2026-11-07; `7yr827` was omitted from `- Item-Dependencies:` and Gate prerequisites. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated citations in E-01, Step 0, and OQ-01 to cite `7yr827` E-01 (and `xexn45` finishing part), added `executed:7yr827` to `- Item-Dependencies:`, and updated Gate prerequisite list. Recommendation strength: strong. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / R2 / E-13 | `.aw/records/plans/pending/20261109-metastore-170-j6o96i-capture-the-test-baselines-and-build-the-shared-test-record.ipd.md:40`, line 44 | E-13 cited unqualified "using the E-12 command" without naming `59aiyh` (no E-12 exists in `j6o96i`), and stated golden fixture generating command is in "E-02's module docstring" (E-02 is in `ijpay0`, which runs after `j6o96i` and is excluded from `Scope-Paths:`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Qualified full-suite command as `59aiyh` E-12 with explicit command syntax in E-13, and specified documenting golden fixture generation in `tests/record_builder.py` module docstring (`D-4`). Recommendation strength: strong. |
| PR-003 | MEDIUM | IN-SCOPE | R1 / R4 / E-01 | `.aw/records/plans/pending/20261109-metastore-170-j6o96i-capture-the-test-baselines-and-build-the-shared-test-record.ipd.md:53` | PLACEMENT rule in E-01 cited `artifact_types.TYPE_BACKENDS` for other types' default disposition directories, but `TYPE_BACKENDS` maps CLI command handlers rather than directory paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated PLACEMENT rule to cite layout model (`layout.RecordClassDefinition`) default subpaths and records root per type (`D-3`). Recommendation strength: strong. |
| PR-004 | MEDIUM | IN-SCOPE | R2 / S7 / Approval and execution gate | `.aw/records/plans/pending/20261109-metastore-170-j6o96i-capture-the-test-baselines-and-build-the-shared-test-record.ipd.md:184` | Lifecycle transition in Gate omitted the conditional runner/executor ownership clause ("When `aw oc run` or `aw agy run` executes the plan...") and explicit prohibition against hand `git mv`, required by `steps/s7-finalize.md`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the standard conditional runner/executor ownership clause and "never a hand `git mv`" to Gate lifecycle transition. Recommendation strength: strong. |
| PR-005 | LOW | IN-SCOPE | Proofreading / Technical writing standard Requirement 12 | `.aw/records/plans/pending/20261109-metastore-170-j6o96i-capture-the-test-baselines-and-build-the-shared-test-record.ipd.md:102` | Plan describes a 5-step implementation workflow but lacked a Mermaid flowchart required by technical writing standard requirement 12(b). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a Mermaid `flowchart TD` diagram in `## Proposed changes (ordered, validatable)`. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which plan provides `write_legacy` and `render_legacy_text` for the Phase B record builder? | Depend directly on `7yr827` E-01 (split from `xexn45` on 2026-11-07) and `xexn45` (finishing part). | Depend on `tve77h` only (rejected: requires builder to maintain duplicate renderer); keep obsolete `xexn45` E-01/E-11 citations (rejected: items moved to `7yr827`). | `7yr827` E-01, `xexn45` line 121, `4sd62s` section 7 step 4/6 | yes |
| D-2 | How should `RecordBuilder` support `text_only=True` when no repository root is provided (as in `support.ready_plan_text`)? | Allow `repo_root=None` (or `RecordBuilder.plan(..., text_only=True)`), rendering text via `artifact_meta.render_legacy_text` directly without disk I/O. | Require mandatory `repo_root` even for `text_only` (rejected: would force `support.ready_plan_text` to allocate temporary directories or change signature, breaking ~30 call sites). | `tests/support.py::ready_plan_text`, `j6o96i` E-01/E-16 | yes |
| D-3 | Where should `RecordBuilder` place records on disk across types? | Follow each type's layout definition (`agent_workflows.layout.RecordClassDefinition`), placing plans and prompts in `pending/`, specs in status subdirectories (`to-review` or `draft`), backlog in `open`, and research/releases/walkthroughs/reviews at records root, with override via `disposition=`. | Hardcode `artifact_types.TYPE_BACKENDS` (rejected: `TYPE_BACKENDS` is a command dispatcher mapping, not directory structure). | `agent_workflows/layout.py::LayoutModel.record_classes`, `agent_workflows/status_set.py::TYPE_STATUSES` | yes |
| D-4 | Where should the fixture generation command for `ready_plan_text_golden.json` be documented? | In `tests/record_builder.py` module docstring. | In `tests/test_record_builder.py` docstring (rejected: that module is created in `ijpay0`, which runs after `j6o96i` and is excluded from `Scope-Paths:`). | `j6o96i` Scope, `ijpay0` Item-Dependencies | yes |
