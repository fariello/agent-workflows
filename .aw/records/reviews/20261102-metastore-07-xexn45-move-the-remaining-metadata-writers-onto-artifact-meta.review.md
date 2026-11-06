# Review findings: plan xexn45

- Subject-Id: xexn45
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `00702a6db` in a non-interactive runner review-sweep lane worktree. The lane-input copy (revision 8) is byte-identical to the tracked plan. The tracked plan was committed and unmodified, so no pre-review snapshot was needed. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| PIN-FIRST rule, V-02, V-05 to V-08, V-10, V-11 | Outcome lists under `/tmp/opencode`; compared on PASSED lines only; `-q` repeated | Lists under the gitignored `.aw/state/xexn45/`; one deterministic command (`-m "" -p no:randomly -n 0`); the full sorted outcome lists are diffed | PR-001. |
| D-1 | "CHANGED" covered only the blank line; section-creation rules were unstated | Section-creation rules unified, byte tests added for each insertion rule, failing pins named | PR-002. |
| E-01 | `write_legacy` described as a new writer | `write_legacy` extracts and extends `2xwb9b`'s legacy branch, so there is one renderer; the `2xwb9b` test modules must stay green | PR-003. |
| E-12, V-12 | The same-record case accepted either outcome | The test pins the measured conflict | PR-004. |
| OQ-03, E-09, D-6, Scope-Paths, spec sync | "If `tve77h` enforces records-root containment" | It does; the writer rule and spec 4.2 are amended in this plan; the spec and `tests/test_artifact_meta_registry.py` are added to Scope-Paths | PR-005. |
| E-03, OQ-02 | "the other type checkers" register the field | Names the real checkers; research uses a YAML key; an `aw check` assertion is added | PR-006. |
| E-01, E-14, V-14, gate | No baseline item; one commit; partial gate | Baselines captured in E-01; one commit per task group allowed; full gate | PR-007. |
| E-07 | The recheck event "re-uses the newest verdict found by `newest_verdict`" | `newest_verdict` returns a polarity; the verdict token comes from `classify_verdict`, and the recheck refuses if there is none | PR-008. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. The plan adds `aw describe`, two `--summary` options and a `short_description` field, and amends spec `4sd62s` 4.2 (PR-005).
2. Partly. It moves finalize and retirement writes and the runner's merge-stage writer helpers. It edits no guard module.
3. Yes. It has 14 E-items in 5 task groups across about 20 modules.
4. Yes. It declares 33 Scope-Paths.
5. Yes. Every non-status metadata write passes through this code, so byte drift would corrupt records silently. The pin-first rule exists to guard against that.

AW-TIER: complex

### Step R1

- Checked: every symbol named in Scope and in E-01 to E-11 resolves in `agent_workflows/`. Every existing test module named exists. The five new modules are absent, as expected. `REDERIVABLE_FRONT_MATTER_KEYS` is `Work-Kind`, `Priority`. `RECHECK_TARGET_READINESS` is `go-pending-approval`. `aw describe` does not exist, as F-07 says.
- History insertion rules match the plan's Step 0 description:
  - `status_set._prepend_workflow_history_entry` inserts directly under the heading and creates a missing section before the first `##`.
  - `plan_readiness._prepend_history_entry` keeps a blank line.
  - `specs._append_history` normalizes to one blank line and creates a missing section at end of file.
  - The plan had missed the difference in section-creation rules (PR-002). A sample of 400 plans has 238 with a blank line under the heading and 162 without.
- `plan_readiness.newest_verdict` returns `(polarity, raw_entry)`, not a verdict string (PR-008).
- `tve77h` E-03 (c) requires `out_of_scope_paths` and `widened_paths` to resolve inside the records root, and spec 4.2 says they "are checked by the path rules (PATH HISTORY below)". OQ-03's conditional ("If `tve77h` enforces") is therefore met (PR-005).
- Only plans have an unknown-bullet lint (`IPD-M103`). `research_contract.validate_frontmatter` checks only for missing required keys (PR-006).

### Step R2

- Checked: the E/V bijection is 14/14. Each V item demands pinned diffs, named test runs or transcripts.
- Reachability:
  - V-04 is reachable through E-04.
  - V-12's same-record outcome is now pinned to the measured behavior (PR-004).
  - V-13 (b) depends on `2xwb9b`'s setter through `artifact_meta`, which `- Item-Dependencies` guarantees.
- Outcome-list paths were outside a lane workspace, and the PASSED-only comparison could miss a newly failing test (PR-001).
- `- Item-Dependencies: executed:tve77h, executed:2xwb9b` is correct.

### Step R3

- Checked: writer validation is unchanged, and refusals write nothing. The OQ-03 relaxation keeps "relative, no `..`, not absolute, sanitizer-scanned, inside the repository root" for finalize paths, so no path can escape the checkout (PR-005). The attestation refusals (E-07, E-08) are fail-closed. No secret or trust-boundary regression.

### Step R4

- A: atomic write, lock and freshness check are inherited from `2xwb9b` (PR-003). Batch validation runs before the first write (E-06).
- C: one renderer, not two (PR-003). Text mode reuses that same renderer (OQ-04).
- D: the pin-first rule is the anti-regression guard. It now catches regressions as well as lost passes (PR-001). Behavior changes are named in D-1 to D-6.
- E: each new behavior has a named test module.
- F: preview by default for `aw describe`.
- Spec sync: the section previously claimed "No spec change", which became false once OQ-03 was resolved. It now declares the amendment and its reason (PR-005).

### Step R5

- Checked through the eight personas:
  - QA and regression: deterministic outcome diffs.
  - Architect: one legacy renderer, which Order 13 switches off.
  - Engineer: OQ-03 now states an executable rule instead of a conditional.
  - Power user: `aw describe` and `--summary` are documented in `docs/cli-output-contract.md`.
  - Novice: refusals name the field.
  - Stakeholder: AC-21 is owned here, with a row table.

### Step R6

- Checked: 14 E-items in 5 groups. OQ-01 records a 07a/07b seam. Each E-item is one concern with a named pin set. No split is recommended (D-3).

### Step R7

- Checked `2xwb9b` E-03 to E-09: its legacy branch, `LegacyRender`, `WritePreview` and the `_storage_format` per-target dispatch already exist when this plan runs. E-01 now extends that branch rather than duplicating it (PR-003).
- `tve77h` E-03 (c) conflicts with OQ-03, and this plan resolves the conflict in the writer and in the spec (PR-005). `tve77h` executes first, so its executor builds the records-root rule. This plan then narrows that rule for two keys and may change one `tve77h` test assertion (D-6).
- `59aiyh` now depends on this plan for `write_legacy` and `render_legacy_text`. Both names are kept.
- `dcerjg` maps a `- Short-Description:` bullet. Research uses a `short-description:` YAML key, which the `dcerjg` census lists among YAML keys.
- `cxxmyv` E-03 switches `write_legacy` off.
- `90iqr1` carries `aw reviews record` and `aw walkthrough new`.

### Step S5

- Checked: OQ-01, OQ-02 and OQ-04 are resolved and non-blocking. OQ-03 is re-resolved from evidence (D-2), with the reviewer recorded as `Owner`. No question needs the human. The spec amendment is reversible before the cutover, because no log carrying these keys exists until Order 13.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | R2 G / R4 D | PIN-FIRST rule `> /tmp/opencode/xexn45-<E>-before.txt`; V-items "restricted to PASSED lines"; `pyproject.toml` `addopts` | Outcome lists were written outside a lane workspace and lost on integration. The `-q` was redundant. Randomized order and PASSED-only comparison could hide a test that newly fails. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gitignored `.aw/state/xexn45/`; deterministic command; the full sorted outcome lists are diffed. |
| PR-002 | MEDIUM | IN-SCOPE | R4 D | `specs._append_history` creates a missing section at end of file; `status_set._prepend_workflow_history_entry` creates it before the first `##` | D-1 left the section-creation rule undecided, so one legacy writer could not reproduce both behaviors. | Low | FIXED | Rule unified (prompts keep end of file); a byte test for each insertion rule; failing pins are named. |
| PR-003 | HIGH | IN-SCOPE | R4 C / R7 | `2xwb9b` E-03 to E-05 build the legacy branch of `append`; this plan's E-01 "Add `artifact_meta.write_legacy`" | Two independent legacy renderers in `artifact_meta` would drift apart, and the cutover would have to switch off both. | Low | FIXED | `write_legacy` extracts and extends `2xwb9b`'s branch; `2xwb9b`'s test modules must pass unchanged. |
| PR-004 | LOW | IN-SCOPE | R2 reachability | E-12 "asserts git reports the conflict (or the merge succeeds ...)"; measured at review: two prepends under one heading give `merge=1` | The test accepted either outcome, so it pinned nothing. | Low | FIXED | The test asserts the conflict. |
| PR-005 | HIGH | IN-SCOPE | R1 / R7 / spec sync | `tve77h` E-03 (c) "every `path`, `out_of_scope_paths` and `widened_paths` value must ... resolve inside the resolved records root"; spec 4.2 "checked by the path rules"; F-05: 35 of 64 entries are code paths | The prerequisite plan's validator would refuse every out-of-scope code path that finalize records. OQ-03 noted the risk without resolving it. | Low | FIXED | The writer applies the repository root to these two keys; spec 4.2 is amended in this plan (declared in Scope-Paths and spec sync); D-6 is added. |
| PR-006 | MEDIUM | IN-SCOPE | R1 | E-03 "registered ... and the other type checkers"; only `ipd_schema.META_RECOGNIZED` rejects unknown bullets | Named checkers that do not exist; research has YAML front matter, not bullets. | Low | FIXED | Real checkers named; research uses a YAML key; an `aw check all --agent` assertion is added. |
| PR-007 | MEDIUM | UNDER-SCOPE | S7 contract / R2 | E-14 "rule-id multiset equal to a pre-E-01 baseline" with no capture; gate | No item captured the baseline. The gate lacked the honesty rule, the `git add -A` ban, the declaration wording of the fence and conditional finalize ownership. | Low | FIXED | Baselines in E-01; one commit per task group allowed; full gate. |
| PR-008 | MEDIUM | IN-SCOPE | R1 / 4.1a K2 | `plan_readiness.newest_verdict` returns `(polarity, raw_entry)` | The plan built the recheck `gate` event's `verdict` from a function that returns no verdict string. | Low | FIXED | The token comes from `classify_verdict` on the raw record; refuse when there is none. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | One legacy renderer or two? | Extract and extend `2xwb9b`'s | A separate `write_legacy` beside it | C1, C10a; `2xwb9b` E-03 to E-05 | yes |
| D-2 | Which root validates `out_of_scope_paths` and `widened_paths`? | The repository root (relative, no `..`, not absolute); spec 4.2 amended | Records root as written (refuses code paths); leave it to `tve77h` (already reviewed, and it would execute the wrong rule) | F-05; `runner_shared.compute_scope_reconciliation`; AGENTS.md "A plan may amend a spec" | yes (no log carries these keys before the cutover) |
| D-3 | Split into 07a and 07b? | No | Split at the OQ-01 seam | Each E-item is one concern with a named pin set | yes |
| D-4 | Accept either outcome for the same-record merge? | No; pin the measured conflict | Accept either | Measured `merge=1` at review | yes |
