# Review findings: plan 9gy5jk

- Subject-Id: 9gy5jk
- Subject-Type: ipd
- Reviewed-At: 2026-11-13
- Reviewer: antigravity/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `01c564538` in a non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261109-metastore-129-9gy5jk-move-the-research-refs-move-and-set-assign-field-writers-ont.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 errors, 0 warnings, 2 `IPD-C802` info advisories for the em dashes in the validation preamble). The three pinned modules passed on unmodified code: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_research_rename_frontmatter.py tests/test_research_set_assign_date_containment.py tests/test_research_archive.py` printed `64 passed in 5.74s`. After revisions, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern, Scope | Named `run_mv` and `run_set_assign` as the writer sites | Names `research_refs._apply_renames` (the shared apply path) and the four-step scope | PR-001 |
| Scope-Paths | 4 paths | Adds `tests/test_research_meta_writer_characterization.py` | PR-003 |
| E-01, E-02 | One-line move statements with no event shape | E-01: one `set` event, key mapping, existing-key filter, `history=False`, failure path kept. E-02: one `transition` event, no `set` of `status`, write before `git mv` | PR-001, PR-002 |
| E-03, E-04 (new) | Absent | E-03 characterization module, pin-first; E-04 research YAML form gaps in `artifact_meta` | PR-003, PR-004 |
| Project conventions | Ledger writers omitted `research_refs` | Adds `research_refs._apply_renames`; adds the research legacy-append call shape | PR-001, PR-006 |
| Findings | F-01 named the wrong sites; F-02 per-item unit counts | F-01 corrected; F-02 marked context only; F-03 added (filled at execution by E-04) | PR-001, PR-004 |
| Behavior decisions | D-2 (bullet rule) only | D-2 marked not applicable to research YAML; adds D-4, D-5, D-6, D-7, D-8 | PR-003 |
| Proposed changes | Two lines | Four ordered steps plus a Mermaid `flowchart TD` (pin-first loop) | Technical writing requirement 12 |
| Validation preamble | Two em dashes (`IPD-C802`) | Commas | Proofreading |
| V-01, V-02 | V-01 `rg` check passed on unmodified code (tautological) | V-01/V-02 label hits by enclosing `def` and require the `artifact_meta.append(` call inside the real writer; V-03, V-04 added | PR-001, PR-003, PR-004 |
| Approval and execution gate | No stop for missing prerequisite symbols | Adds a narrow unsafe-condition stop | PR-006 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. E-04 extends the shared `artifact_meta` legacy writer's research YAML form, which other writer moves (`1hfmpb`, `fnu6kw`) also edit.
2. No. The plan does not touch leak sanitizing, commit, worktree-isolation, merge, or sandbox code.
3. No. Four `E-*` items in one task group across three production modules and one new test module.
4. Yes. `- Scope-Paths:` lists five explicit files.
5. Yes. A wrong rendering silently rewrites tracked research front matter (status position, `order` padding, a stray `## Workflow history`), recoverable from git but hard to notice.

AW-TIER: standard

### Step R1

- Checked: spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (4.1, section 7 field-name list); `agent_workflows/research_refs.py` (`_apply_renames`, `_planned_frontmatter_updates`, `run_mv`, `run_set_assign`); `agent_workflows/research_cmd.py::update_frontmatter_fields`; `agent_workflows/research_archive.py` (`apply_moves`, `_rewrite_status_in_text`, callers); `agent_workflows/artifact_meta.py` (`REGISTRY["research"]`, `_COMMON_FIELDS` `model`, `OP_PAYLOAD_SCHEMAS["transition"]`, `_check_owned_fields`, `_render_status`, `_render_history`, `render_legacy`, `append`, `append_legacy`, `LegacyRender`); sibling plans `7yr827`, `1hfmpb`, `fnu6kw`, `bsl45u`; the three pinned test modules.
- `run_mv` and `run_set_assign` write nothing themselves; both call `_apply_renames`, which holds the only `_rcmd.update_frontmatter_fields` plus `_atomic_write` pair (PR-001).
- `artifact_meta.write_legacy` and `render_legacy_text` do not exist at HEAD; `7yr827` E-01 adds them, and the plan correctly depends on `executed:7yr827`.

### Step R2

- Checked: E/V bijection (4/4 after the review), `Depends on:` chain E-03 -> E-04 -> E-01 -> E-02, `- Scope-Paths:` (now includes the new test module), `- Item-Dependencies:` (`tve77h`, `2xwb9b` executed; `7yr827`, `fnu6kw` pending, which the runner re-checks at dispatch; `1hfmpb` covered transitively through `fnu6kw`).
- The original V-01 demanded "none inside `run_mv` or `run_set_assign` writing front matter", which unmodified code already satisfies (PR-001). V-01 and V-02 now require the positive `artifact_meta.append(` hit inside the real writer.
- The V-04 probe is reachable through `artifact_meta.render_legacy_text`, which `7yr827` creates.

### Step R3

- Checked: `artifact_meta.validate_new_events` (string safety, leak sanitizer, path safety) now sees research values. A refusal in `_apply_renames` stays a warning note (D-8); a refusal in `apply_moves` raises before the `git mv` (D-8). No `path` key is emitted, so no new path-traversal surface. No secrets, identity, or authorization surface. No finding.

### Step R4

- Checked: correctness of the event shapes against `_check_owned_fields` (a `set` of `status` is refused, PR-002); kept-behavior gaps between today's writers and `render_legacy` (PR-003): `_render_status` inserts a missing fenced `status:` before the closing `---` where `_rewrite_status_in_text` inserts it after `kind:`; `render_legacy` writes a `## Workflow history` line unless `history=False`; `update_frontmatter_fields` never inserts a missing key. Research YAML key mapping gaps (PR-004): the `7yr827` research key list has no `model`; `1hfmpb` E-04 formats integer `order` with `str(value)`, which would drop the `01` padding that `tests/test_research_rename_frontmatter.py` pins.
- Right-sizing: each E-item is one concern in one file; `aw ipd lint` reported `IPD-Z603` (10 units) for an intermediate E-01 draft, which was trimmed to conform.
- Spec / documentation sync "None" is truthful: D-5 to D-8 keep today's behavior.

### Step S5

- Checked: no pre-existing open questions. Every question raised by PR-001 to PR-004 was answerable from repository evidence; all decisions are reversible plan edits. No human-owned question remains.

### Pass 2

- Re-reviewed after E-03/E-04 were added and `- Scope-Paths:` changed (S6 rule 1). Swept stale wording (`No new module`, `names 6 units`, `run_mv` as a writer site, em dashes): none left. Corrected one self-introduced misattribution (E-04 cited spec 4.1 for "only research carries `---`"; replaced by the measured fact that no tracked `.aw/records/**/*.md` outside `research/` starts with `---`). `aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R1 / R2 | `agent_workflows/research_refs.py::_apply_renames` "new_text = _rcmd.update_frontmatter_fields(old_text, updates)"; `research_refs.run_mv`, `research_refs.run_set_assign` call `_apply_renames` | E-01, Concern, F-01 named `run_mv`/`run_set_assign` as the writers; V-01's `rg` bar ("none inside `run_mv` or `run_set_assign`") was already true on unmodified code, so it could not detect a missed move. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Retargeted E-01, F-01, Concern and V-01 to `_apply_renames`; V-01 requires the `artifact_meta.append(` hit inside it (strong). |
| PR-002 | HIGH | IN-SCOPE | R4-A | `agent_workflows/artifact_meta.py::_check_owned_fields` "refuse generic set of identity/status field"; `artifact_meta.py::OP_PAYLOAD_SCHEMAS` `transition` (`from` optional, `to` required) | E-02 did not say which op carries the status change; the natural `set` of `status` is refused. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 emits one `transition` (`to`, `from` only when a `status:` line exists, no `path`) and V-02 checks it (strong). |
| PR-003 | HIGH | UNDER-SCOPE | R4-D | `agent_workflows/research_archive.py::_rewrite_status_in_text` (inserts after `kind:`); `agent_workflows/artifact_meta.py::_render_status` (inserts before closing `---`); `artifact_meta.py::render_legacy` (`if render.history:` writes `## Workflow history`); `agent_workflows/research_cmd.py::update_frontmatter_fields` "A field not present in the block is left absent" | Moving onto `render_legacy` changes kept behavior that no pinned test covers: status insertion position (common, since research docs usually lack `status:`), a new history section, and key insertion. D-2 (bullet rule) does not apply to YAML. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added D-4 to D-8, E-03/V-03 characterization module green on unmodified code, and wired it into the E-01/E-02 pins (strong). |
| PR-004 | MEDIUM | UNDER-SCOPE | R4-C | `7yr827` E-01 research YAML key list (no `model`); `1hfmpb` E-04 "`str(value)` formatting for integer `order`"; `tests/test_research_rename_frontmatter.py` `assert fm["order"] == "01"` | The declared `artifact_meta.py` scope had no item; the research YAML form cannot yet write `model`, pad `order`, or place `status` as research expects. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added E-04/V-04 (conditional, records what was already present in F-03) (strong). |
| PR-005 | LOW | IN-SCOPE | Proofreading | Plan validation preamble (`IPD-C802`) | Two em dashes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with commas (medium). |
| PR-006 | LOW | IN-SCOPE | S7 gate | Plan `## Approval and execution gate` | No narrow stop for an absent prerequisite symbol (`write_legacy`, `render_legacy_text`), and no call shape for a research legacy append. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the unsafe-condition stop and a Project conventions bullet with the `LegacyTarget`/`LegacyRender` shape (medium). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which op carries the archive status change? | One `transition` event, `from` only when a `status:` line exists | A `set` of `status` (refused by `_check_owned_fields`) | `agent_workflows/artifact_meta.py::_check_owned_fields`; `OP_PAYLOAD_SCHEMAS["transition"]` | yes |
| D-2 | Keep today's research front-matter behavior (status position, absent keys absent, no history line, `order` padding) or adopt the generic renderer's? | Keep today's (plan D-5 to D-8) | Adopt `_render_status`/`render_legacy` defaults (an unexplained behavior change in a pure writer move) | Plan Goal and spec `4sd62s` section 7 step 4 (move writers, keep behavior); `research_cmd.update_frontmatter_fields` docstring; `research_archive._rewrite_status_in_text` docstring | yes |
| D-3 | Pin the uncovered kept behavior with a new module or rely on existing pins? | New characterization module (E-03), green on unmodified code | Existing pins only (they do not cover status position or history creation) | `tests/test_research_archive.py` (no position assertion); R4-D characterization rule | yes |
| D-4 | Where do the `artifact_meta` research-form changes go? | Their own item E-04, conditional on what `7yr827`/`1hfmpb` already provide | Folding into E-01/E-02 (two files per item, against right-sizing guidance `IPD-Z603`) | `1hfmpb` precedent (its E-04); plan right-sizing rule | yes |
