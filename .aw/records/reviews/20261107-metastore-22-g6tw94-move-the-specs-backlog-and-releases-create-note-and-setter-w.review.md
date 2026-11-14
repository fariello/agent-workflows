# Review findings: ipd g6tw94

- Subject-Id: g6tw94
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading

Checked `.aw/records/plans/pending/20261107-metastore-22-g6tw94-move-the-specs-backlog-and-releases-create-note-and-setter-w.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `steps/p-proofread.md`.

### Changes
| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Concern`, `Scope`, `Project conventions`, `Deferred` | Bare `id6` references and `module.func` symbols without descriptive labels or `path::Symbol` anchors | Added descriptive names on first mention of referenced records and standardized code citations to `path::Symbol` | `technical-writing.md` Requirement 1 and `steps/p-proofread.md` Section 11.1 |
| `Detailed Implementation Checklist (TODO)` | Stale `PIN-FIRST RULE for every "move" item` paragraph citing `.aw/state/g6tw94/` and nonexistent `D-1 to D-6` | Concise `Audit-only scope note` stating that `b3l7y6`, `jlwedt`, and `3466h8` own the pin-first moves while `g6tw94` runs the `E-03` audit | `technical-writing.md` Requirements 5, 8, and 11 (remove stale pre-split instructions) |
| `E-03`, `V-03`, `Findings`, `Behavior decisions` | Ambiguous `enclosing def` instruction on module/class hits and broken `(F-04)` blank-line cross-reference | Explicit `<module>` / class-scope labeling, `rg` exit `1` note on zero-match query, `D-3` value-delegate rule, and corrected `(xexn45 F-04)` citation | `technical-writing.md` Requirements 5, 6, and 11 |
| `Proposed changes (ordered, validatable)` | Two-line numbered list with no diagram | Added Mermaid `flowchart TD` showing `b3l7y6`, `jlwedt`, and `3466h8` feeding `E-03`, the moved-writer defect branch, `F-05` recording, and downstream unblocking | `technical-writing.md` Requirement 12 (three prerequisite records and a branched audit process) |
| `Validation and cross-check` | Two em dashes (`—as distinct from ...—`) on line 114 | Replaced both em dashes with commas | Resolve `IPD-C802` advisories |

### Issues
| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|

### Step T
- Checked: `- Scope-Paths:`, execution-item and task-group counts, spec/contract surface, and cross-plan dependency edges in Set `metastore`.
1. Yes: while `g6tw94` edits no `.spec.md` or Python source, it is the verification gate (`executed:g6tw94`) that 11 downstream `metastore` plans rely on for `spec 4sd62s` section 7 step 4 completion across `specs`, `backlog`, and `releases`.
2. No: `- Scope-Paths:` contains only `.aw/records/plans/pending/20261107-metastore-22-g6tw94-move-the-specs-backlog-and-releases-create-note-and-setter-w.ipd.md` and touches no leak-sanitizer, commit-helper, lock, containment, or sandbox code.
3. Cross-cutting across three production modules (`agent_workflows/specs.py`, `agent_workflows/backlog.py`, `agent_workflows/releases.py`) and six prerequisite plans, with 1 `E-*` item in 1 task group.
4. Yes: `- Scope-Paths:` explicitly lists `.aw/records/plans/pending/20261107-metastore-22-g6tw94-move-the-specs-backlog-and-releases-create-note-and-setter-w.ipd.md`.
5. Yes: an incomplete audit in `g6tw94` could clear an unmigrated metadata or history writer in `specs.py`, `backlog.py`, or `releases.py` and break downstream `fekdwv`, `xexn45`, or `9o83cr`.

AW-TIER: complex

### Step R1
- Checked: `agent_workflows/specs.py`, `agent_workflows/backlog.py`, `agent_workflows/releases.py`, `agent_workflows/artifact_meta.py`, `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md`, and sibling plans `xexn45`, `7yr827`, `b3l7y6`, `jlwedt`, `3466h8`, and `n5sxxk` at `HEAD` `01c564538`.
- Verified live hit counts across the three modules before the moves:
  - `agent_workflows/specs.py`: 15 `- Field:` bullet literals, 3 hand-built history lines (`run_migrate`, `run_note`, `_render_new_spec`), and 8 `Workflow history` occurrences (`_sidecar_append`, `_history_lines`, `validate_spec`, `_append_history` x3, `_render_new_spec` x2).
  - `agent_workflows/backlog.py`: 29 `- Field:` bullet literals (26 in `_render_item`/`_insert_absent_gate_fields` plus 3 in `set_release_exempt_kind_line`, `set_release_exempt_ref_line`, and `set_close_evidence_line`), 4 hand-built history lines (`_render_item` x2, `run_note`, `_reattach_history`), and 14 `Workflow history` occurrences (`<module>` x2, `validate_item`, `_render_item` x5, `run_new`, `run_note` x2, `_strip_metadata_and_history`, `_reattach_history` x4 — 16 lines total, 12 inside the 4 writers).
  - `agent_workflows/releases.py`: 11 `- Field:` bullet literals (`plan_release` x4 and 7 `set_*_line` helpers), 1 hand-built history line (`plan_release` line 94 using `{_core.utc_history_date()}`), and 4 `Workflow history` occurrences (`plan_release`, `ReleaseRecord` docstring, `_history_lines` x2).
- Identified that `E-03`'s original regex `f"- \{(date|today|hdate)\} "` missed `agent_workflows/releases.py:94` (`{_core.utc_history_date()}`), omitted `- Field:` bullet literals completely (`PR-001`), claimed `g6tw94` added `write_legacy` (owned by `7yr827`), and mis-cited `(F-04)` for blank-line insertion (`xexn45` `F-04`) (`PR-002`).

### Step R2
- Checked: `E-03`/`V-03` 1:1 bijection, `- Scope-Paths:`, `- Item-Dependencies:`, evidence verifiability, live-count framing, qualified `4sd62s` citations, and `Approval and execution gate`.
- Verified `E-03` maps 1:1 to `V-03`, `- Scope-Paths:` matches the single file `g6tw94` edits (its own IPD), and `- Item-Dependencies:` (`executed:tve77h, executed:2xwb9b, executed:7yr827, executed:b3l7y6, executed:jlwedt, executed:3466h8`) captures every prerequisite.
- Expanded `E-03` and `V-03` to cover all 18 writer functions moved by `b3l7y6` (4), `jlwedt` (4), and `3466h8` (10), added the `- Field:` bullet literal `rg` check and `python3 -m pytest` summary line (`4sd62s` AC-1b), framed historical `def test_` counts in `F-02`/`F-03` as non-binding split-sizing context, and aligned stop conditions in `Approval and execution gate` (`PR-001`, `PR-002`).

### Step R3
- Checked: command safety, file write scope, and trust boundaries in `E-03` and `V-03`.
- `g6tw94` executes three read-only `rg` queries on fixed repository paths plus `python3 -m pytest`, edits only its own tracked IPD (`F-05` and `V-03`), introduces no credentials, network calls, or privilege changes, and fails closed by stopping and reporting if any prerequisite writer still builds metadata by hand.

### Step R4
- Checked: correctness, domain invariants, anti-regression coverage, conceptual density, and `Spec / documentation sync`.
- Confirmed `agent_workflows/artifact_meta.py::_render_field` (`agent_workflows/artifact_meta.py:4041-4047`) delegates `release_exempt_kind`, `release_exempt_ref`, and `close_evidence` formatting to `backlog.set_release_exempt_kind_line`, `backlog.set_release_exempt_ref_line`, and `backlog.set_close_evidence_line` (`2xwb9b`, `jlwedt` F-01); added `D-3` so `E-03` classifies those three hits accurately in `F-05` instead of false-flagging `jlwedt`.
- Conceptual density check: `E-03` is a single read-only audit pass across three modules writing one findings cell (`F-05`) in one file. `Spec / documentation sync` ("None") is truthful because `g6tw94` changes no CLI flags, file formats, or user-facing behavior.

### Step R5
- Checked: all eight reviewer personas against `.aw/system/workflows/release-review/00-run-protocol.md#Review mindset: the eight reviewer personas` (QA/QC, testing/regression, UI/UX, architect, software engineer, power user, novice, stakeholder).
- QA/QC and testing/regression caught the blind spot on `releases.plan_release`'s `{_core.utc_history_date()}` line and the missing `- Field:` bullet audit (`PR-001`); novice and software engineer caught the `rg` exit `1` behavior on zero-match queries, `<module>`/class-scope hits outside `def`, and stale `PIN-FIRST` move instructions (`PR-001`, `PR-002`).

### Step R6
- Checked: plan size and decomposition boundaries after the 2026-11-07 and 2026-11-09 splits.
- `g6tw94` already delegated all code and test moves to child plans `b3l7y6` (Order 120), `jlwedt` (Order 121), and `3466h8` (Order 134), retaining 1 `E-*` item in 1 task group with 0 code `Scope-Paths`. No further split is warranted.

### Step R7
- Checked: cross-plan consistency across orchestrator `63ib9r` (`E-22`, `E-62`, `E-63`, `E-76`), parent `xexn45`, prerequisites `tve77h`, `2xwb9b`, `7yr827`, `b3l7y6`, `jlwedt`, and `3466h8`, and downstream plans `n5sxxk`, `s95hj6`, `ernmom`, `x2dxvf`, `fekdwv`, `6e93gt`, `b4y4ee`, and `9o83cr`.
- Reconciled `g6tw94`'s writer inventory and `Deferred / out of scope` carriers with reviewed `b3l7y6`, `jlwedt` (`D-3` value delegates), `3466h8` (`run_new` and all 7 `set_*_line` adapters), `b4y4ee` (merge-independence test), and `xexn45` (`AC-21`, `F-09` raw-write audit, docs/changelog, and full-suite gates) (`PR-001`, `PR-002`).

### Step S5
- Checked: pre-existing open questions (none), review-raised questions, and remediation risk.
- All questions were resolved directly from repository code, `spec 4sd62s`, and reviewed sibling plans (`D-1` and `D-2` below, both `Reversible: yes`). Zero `OPEN` or `DEFERRED` findings remain.

### Pass 2
- Re-ran checks P, R1, R2, R4, R7, and S5 against the revised `.aw/records/plans/pending/20261107-metastore-22-g6tw94-move-the-specs-backlog-and-releases-create-note-and-setter-w.ipd.md`.
- Verified all three `E-03` `rg` commands against current `HEAD` `01c564538`, confirmed every reference across `E-03`, `V-03`, `F-01..F-05`, `D-1..D-3`, `Proposed changes`, `Deferred`, and `Approval and execution gate` is internally consistent, and verified zero em/en dashes, zero `TODO` placeholders, zero absolute paths, and zero `file://` URIs.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PR-001 | high | UNDER-SCOPE | R1 / R2 / R7 | `.aw/records/plans/pending/20261107-metastore-22-g6tw94-move-the-specs-backlog-and-releases-create-note-and-setter-w.ipd.md:40-43` (`E-03`), `agent_workflows/releases.py:94` (`plan_release`) | `E-03`, `V-03`, and `Deferred` checked only `"Workflow history"` and `f"- \{(date\|today\|hdate)\} "` (missing `releases.plan_release`'s `{_core.utc_history_date()}` line and all 55 `- Field:` bullet literals), named only 10 of the 18 writers moved by reviewed `b3l7y6`, `jlwedt`, and `3466h8` (omitting `releases.run_new` and 7 `releases.set_*_line` helpers), and omitted `<module>`/class-scope labeling and `rg` exit `1` zero-match semantics | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Expanded `E-03`, `V-03`, and `Deferred` to run all three `rg` audits (`Workflow history`, interpolated history builders including `_core.utc_history_date()`, and `- Field:` bullet literals), verify all 18 moved writers, document `<module>`/class scope and `rg` exit `1`, and reconcile `b4y4ee`/`xexn45` carriers (strength: very strong) |
| PR-002 | medium | IN-SCOPE | R1 / R2 / R4 | `.aw/records/plans/pending/20261107-metastore-22-g6tw94-move-the-specs-backlog-and-releases-create-note-and-setter-w.ipd.md:36,49-51,66-75,129-131` (`Detailed Implementation Checklist`, `Findings`, `Behavior decisions`, `Approval and execution gate`) | Stale pre-round-3 prose instructed PIN-FIRST move diffs under `.aw/state/g6tw94/` and cited nonexistent `D-1 to D-6`, falsely stated `g6tw94` adds `write_legacy` (owned by `7yr827`), mis-cited `(F-04)` for blank-line history insertion (`xexn45` `F-04`), left raw test counts unframed, omitted `D-3` for `backlog.py`'s three `artifact_meta._render_field` value delegates, and required `python3 -m pytest` in the gate without including it in `E-03`/`V-03` | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Replaced stale move boilerplate with an audit-only scope note, corrected `7yr827` and `xexn45` references, framed `F-02`/`F-03` counts as historical non-binding split context, added `D-3` for `backlog` value delegates, added `python3 -m pytest` (`4sd62s` AC-1b) to `E-03`/`V-03`, and added explicit prerequisite and audit-defect stop conditions in the gate (strength: strong) |
| PR-003 | low | IN-SCOPE | Proofreading | `.aw/records/plans/pending/20261107-metastore-22-g6tw94-move-the-specs-backlog-and-releases-create-note-and-setter-w.ipd.md:5-6,78-81,114` (`Concern`, `Scope`, `Proposed changes`, `Validation and cross-check`) | Line 114 contained two em dashes (`IPD-C802`), `Proposed changes` lacked a `technical-writing.md` Requirement 12 Mermaid diagram for the three-part prerequisite fan-in and audit defect branch, code references used bare `module.func` instead of `path::Symbol`, and first-mention `id6` tokens lacked descriptive labels | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Removed both em dashes (`IPD-C802`), added a Mermaid `flowchart TD` diagram in `Proposed changes`, standardized code citations to `path::Symbol`, and added descriptive labels on first mention of referenced records (strength: strong) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D-1 | Should `g6tw94` `E-03` audit `- Field:` bullet literals in addition to `Workflow history` lines, and how should it classify `backlog.py`'s three `set_*_line` helpers? | Add a third `rg` query for `- Field:` bullet literals alongside a broadened history-builder query, and record `backlog.set_release_exempt_kind_line`, `set_release_exempt_ref_line`, and `set_close_evidence_line` in `F-05` as expected `artifact_meta._render_field` value delegates (`D-3`) | Keep `E-03` limited to `Workflow history` strings (leaves field-setters unaudited despite `Goal`) or treat `backlog.set_*_line` as prerequisite defects (contradicts `2xwb9b` and `jlwedt` F-01) | `.aw/records/plans/pending/20261107-metastore-22-g6tw94-move-the-specs-backlog-and-releases-create-note-and-setter-w.ipd.md:30` (`Goal`), `agent_workflows/artifact_meta.py:4041-4047` (`_render_field`), and `.aw/records/plans/pending/20261109-metastore-121-jlwedt-move-the-backlog-create-and-note-writers-onto-artifact-meta.ipd.md:6,74,84` | yes |
| D-2 | Should `g6tw94` `E-03` and `V-03` run and paste bare `python3 -m pytest` even though `g6tw94` edits no Python files? | Require running bare `python3 -m pytest` and pasting its summary line in `V-03` | Drop `python3 -m pytest` from `Approval and execution gate` | `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:263` (`AC-1b` core-tier summary per child merge) and `g6tw94` `Approval and execution gate` honesty rule | yes |
