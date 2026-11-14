# Review findings: plan xexn45

- Subject-Id: xexn45
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
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
| D-2 | Which root validates `out_of_scope_paths` and `widened_paths`? | The repository root (relative, no `..`, not absolute); spec 4.2 amended | Records root as written (refuses code paths); leave it to `tve77h` (already reviewed, and it would execute the wrong rule) | F-05; `runner_shared.compute_scope_reconciliation`; AGENTS.md "A plan may amend a spec"; no log carries these keys before the cutover | yes |
| D-3 | Split into 07a and 07b? | No | Split at the OQ-01 seam | Each E-item is one concern with a named pin set | yes |
| D-4 | Accept either outcome for the same-record merge? | No; pin the measured conflict | Accept either | Measured `merge=1` at review | yes |

## Round 2

This re-review ran at HEAD `921b5778d` in an isolated runner review-sweep lane worktree after the 2026-11-07 approval withdrawal, the 2026-11-07 six-part writer split (`7yr827`, `g6tw94`, `n5sxxk`, `6e93gt`, `bsl45u`, `8q27jt`), and the 2026-11-09 round-3 sub-split (`Orders 120..136`, including `b4y4ee` Order 133). Working tree was clean at turn start (`pre-review snapshot: skipped unchanged`). Pass 1 and Pass 2 verified the post-split plan against amended spec `4sd62s`, orchestrator `63ib9r`, and the reviewed writer parts.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Detailed Implementation Checklist`, `E-17`, `V-17`, `Required tests` | Demanded per-part diffs against gitignored cross-lane `-after.txt` files and `.aw/state/xexn45/check-before.jsonl` assumed pre-populated on disk; cited `g6tw94` E-02 for `test_specs_date_containment.py` | Runs the deduplicated union of existing `tests/test_*.py` files across `tve77h`, `2xwb9b`, `7yr827..8q27jt`, Orders `120..136`, `b4y4ee`, and `xexn45`; regenerates `check-before.jsonl` from `7yr827` `F-04` SHA in an isolated lane; cites `b3l7y6` E-05 | PR-201. |
| `E-13`, `V-13`, `Required tests` | Claimed `aw backlog set <id6> done` and `aw ipd finalize` both emit a scope bullet, and asked `V-13` to cite the plan's own final commit hash | States exact Phase-B `git diff` hunks for non-blocking `aw backlog set <id6> done`, within-scope `aw ipd finalize` (zero scope bullet per `D-3`, `- Approval:` unset), and out-of-scope `aw ipd finalize --scope-reason` (`- Scope-Exceeded:` added), and cites `E-13`'s immutable code commit SHA | PR-202. |
| `E-16`, `V-16`, `Spec / documentation sync` | Underspecified where `docs/cli-output-contract.md` documents `--summary` and omitted `test_cli_agent_protocol_doc.py` and the user-facing dash ban | Documents creation-time `--summary` (`aw ipd scaffold --summary`, `aw prompts new --summary`) beside `h06gs7` E-02's `aw describe` entry (leaving `## 6. Token Control` untouched), enforces zero em/en dashes, and runs `tests/test_cli_agent_protocol_doc.py` | PR-203. |
| `D-1`, `D-5`, `D-6` | Retained pre-split claims (`E-05` pin diff in `D-1`, `render_legacy_text` in `D-5`, `test_artifact_meta_registry.py` edits in `D-6`, `D-6` before `D-5`) | Reconciled in order `D-1..D-6` with `7yr827` (`restore_legacy_snapshot`), `b3l7y6` E-05 (`test_specs_date_containment.py`), and `9qhtrc` V-01 (`test_artifact_meta_registry.py` unmodified) | PR-204. |
| `Checklist` tail, `Step 0`, `F-07`, `F-09`, `Proposed changes`, `Validation`, `Approval gate` | Left `E-NEW` scaffold prompt, pre-split `Step 0`/`F-07` prose, two `IPD-C802` em dashes, no Mermaid diagram, and no stop-and-report clause | Removed `E-NEW` prompt, updated `Step 0`/`F-07`/`F-09` cross-references covering all 18 writer modules, added `flowchart TD` diagram, qualified `4sd62s` AC refs, removed em dashes, and added stop-and-report clause | PR-205. |
| `Deferred / out of scope`, `E-17`, `V-17` | `- Carrier: 2xwb9b` lacked `- Carrier-Evidence:` (`check.ipd-carrier-finished-unverified`), and `E-17` did not record `- Carrier-Evidence:` for finished split parts `7yr827..b4y4ee` | Recorded verified `- Carrier-Evidence:` for `executed/20261102-metastore-06-2xwb9b-...ipd.md` now and required `E-17` to record `- Carrier-Evidence:` on the seven finished split-part carrier rows before running `aw check --agent` | PR-206. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Partly. `xexn45` owns `4sd62s` AC-21 (Section 4.4a obligation closure) and reconciles `docs/cli-output-contract.md` and `CHANGELOG.md` for user-visible Phase-B `--summary` and `aw describe`.
2. Partly. It verifies `aw ipd finalize` scope and approval-unset transitions (`AC-6` phase-B form) and runs repository-wide `aw check`, `aw ipd lint --all`, and `aw sanitize` gates across the entire writer migration family.
3. No on raw item count after splitting (`5` E-items in `1` task group), yes on cross-plan integration fan-in (`9` direct `- Item-Dependencies:` covering `24` prerequisite writer plans and `109` pinned test modules).
4. No (`4` declared `Scope-Paths`), though `E-14`/`E-15` audit `10` production writer modules and cross-check `8` sibling-audited writer modules.
5. Yes. As the finishing gate of Phase B step 4 before reader moves (`ffceq0`, `t4gl15`) and test-data migration (`59aiyh`), any missed raw metadata write or false gate assumption here blocks or misleads downstream `Set: metastore` waves.

AW-TIER: complex

### Step R1

- Checked: every file in `- Scope-Paths:` (`docs/cli-output-contract.md`, `CHANGELOG.md`, and `tests/test_writers_obligations.py` created by prerequisite `d4w53g`), all `10` production writer modules audited in `E-14` and `E-15` (`specs.py`, `backlog.py`, `releases.py`, `prompts.py`, `ipd_authoring.py`, `artifact_rename.py`, `plans_refs.py`, `plan_readiness.py`, `set_records.py`, `coverage_record.py`), all `5` existing obligation test modules in `E-13` (`tests/test_find_filters.py`, `tests/test_cli_find.py`, `tests/test_graduation_forward_links.py`, `tests/test_readiness_absence_invariant.py`, `tests/test_status_set_meta_writer.py`), `tests/test_cli_agent_protocol_doc.py`, and all `27` referenced artifact IDs across `.aw/records/`.
- Verified `rg -n "atomic_write\(|write_text\("` across the `10` `E-14`/`E-15` modules matches both `core.atomic_write(` and `ipd_authoring._atomic_write(`, with zero `.open(..., "w"|"a")` bypasses in those modules.
- Verified `agent_workflows/status_set.py::_prepare_status_change` and `1dvb08` E-01 for `E-13 (b)`: `aw backlog set <id6> done` never writes a scope bullet, and `aw ipd finalize` (`approved -> executed`) unsets `- Approval:` and writes `- Scope-Exceeded:` only when finalizing out-of-scope paths (`PR-202`).
- Verified `docs/cli-output-contract.md` (`## 6. Token Control` vs `## 13. Metadata Reads`) and `h06gs7` E-02 (`PR-203`).
- Verified `aw check plans --agent` on `HEAD`: `xexn45` had `check.ipd-carrier-finished-unverified` because `2xwb9b` is already in `.aw/records/plans/executed/` without `- Carrier-Evidence:` (`PR-206`).

### Step R2

- Checked: E/V bijection across `E-13..E-17` and `V-13..V-17` (`5/5`), `- Highest E allocated: 17`, `- Item-Dependencies:` (`executed:tve77h, executed:2xwb9b, executed:7yr827, executed:g6tw94, executed:n5sxxk, executed:6e93gt, executed:bsl45u, executed:8q27jt, executed:b4y4ee`), and isolated-lane reachability of every `V-*` demand.
- Found and fixed unreachable cross-lane `.aw/state/<part-id6>/*-after.txt` diff demands and unregenerated `.aw/state/xexn45/check-before.jsonl` assumptions in `E-17`/`V-17` (`PR-201`), self-referential commit-hash ordering and inaccurate diff hunks in `E-13`/`V-13` (`PR-202`), and post-prerequisite `check.ipd-carrier-finished-unverified` handling in `E-17`/`V-17` (`PR-206`).
- Every spec criterion reference in `E-13..E-17`, `Required tests / validation`, and `V-13..V-17` is qualified with `4sd62s`.

### Step R3

- Checked: `E-13..E-17` add tests, audit raw writes, update user-facing docs, and run verification gates without relaxing any validator, path-containment rule, descriptive-safety check, or attestation gate.
- Temporary baseline worktree regeneration in `E-17` uses a detached read-only checkout of the recorded `7yr827` `F-04` commit SHA and cleans up with `git worktree remove --force`. `aw sanitize --agent` runs before commit.

### Step R4

- Checked:
  - A (Atomicity and state): `E-13` commits `tests/test_writers_obligations.py` through `aw commit` before `V-13` cites its SHA; `E-14`/`E-15` fail closed (stop and report rather than patching production code out of scope) if any prerequisite writer module still bypasses `artifact_meta`.
  - C (Integration and seams): `E-17` exercises the full deduplicated union of existing `tests/test_*.py` modules across all `24` prerequisite writer plans (`109` modules measured on `HEAD`) plus `7yr827` `F-04`'s reproducible baseline SHA.
  - D and E (Regression and tests): `tests/test_writers_obligations.py` uses `pytestmark = pytest.mark.core`, isolated `tmp_path` git fixtures, and real CLI/function calls with zero source-code inspection; `E-16` runs `tests/test_cli_agent_protocol_doc.py`.
  - Spec and doc sync: `docs/cli-output-contract.md` and `CHANGELOG.md` are updated in `E-16` with zero em/en dashes; `4sd62s` 4.2 was already delegated to `9qhtrc`, and workflow body updates remain deferred to `90iqr1` per `4sd62s` C10a.

### Step R5

- Checked through the eight review personas:
  - QA and regression: `E-13 (b)` tests both within-scope and out-of-scope finalize diffs plus backlog `done`, and `E-17` runs all `109` writer-family test modules deterministically plus `python3 -m pytest` and `make test-all`.
  - Architect: all `18` writer modules (`10` in `F-02` audited in `E-14`/`E-15`, `8` in `F-03` cross-referenced to `7yr827`, `n5sxxk` E-03, `bsl45u` E-03, and `8q27jt`/`1dvb08`) are accounted for in `F-09` for `9o83cr` (`4sd62s` AC-1).
  - Engineer / isolated-lane executor: zero cross-lane gitignored state assumptions remain; baseline regeneration from `7yr827` `F-04` and `Carrier-Evidence` updates are explicit.
  - Power user and novice: `aw ipd scaffold --summary`, `aw prompts new --summary`, and `aw describe` are documented together in `docs/cli-output-contract.md` and `CHANGELOG.md`.
  - Stakeholder: `4sd62s` AC-21 row-by-row closure is verified and recorded in `V-13`.

### Step R6

- Checked: `5` E-items (`E-13..E-17`) in `1` task group across `3` non-plan `Scope-Paths` (`tests/test_writers_obligations.py`, `docs/cli-output-contract.md`, `CHANGELOG.md`), well inside `nj8zdp` right-sizing bounds after the 2026-11-07 and 2026-11-09 splits. Each E-item owns one cohesive deliverable and requires no further split.

### Step R7

- Checked orchestrator `63ib9r` (row `07` dependencies match `xexn45` `- Item-Dependencies:` exactly; all round-3 children `Orders 120..136` are transitive dependencies of `7yr827..8q27jt`), `7yr827` (`E-01`, `F-04`, `D-5`), `g6tw94` (`F-03`, `E-03`), `b3l7y6` (`E-05`), `n5sxxk` (`E-03`), `6e93gt` (`E-03`), `py2vu9`, `h06gs7` (`E-02` `docs/cli-output-contract.md` contract for `aw describe`), `bsl45u` (`E-03`), `8q27jt`, `d4w53g` (`E-02`, `E-03` creating `tests/test_writers_obligations.py`), `9qhtrc` (`V-01` keeping `tests/test_artifact_meta_registry.py` unmodified), `1dvb08` (`E-01` Phase-B scope fields), and `b4y4ee` (`E-01` `tests/test_writers_merge_independence.py`).
- Reconciled `D-1`, `D-5`, and `D-6` (`PR-204`), `h06gs7`/`py2vu9` doc alignment (`PR-203`), and `2xwb9b` + split-part `Carrier-Evidence` (`PR-206`).

### Step S5

- Checked: `OQ-01` is resolved and non-blocking; `OQ-02`, `OQ-03`, and `OQ-04` moved to `6e93gt`, `8q27jt`/`9qhtrc`, and `7yr827` where they are resolved. All six Round-2 findings (`PR-201..PR-206`) are technical execution-accuracy and cross-plan alignment defects resolved directly from repository code, amended spec `4sd62s`, and reviewed sibling plans. Zero questions belong to the human (`questions: []`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | IN-SCOPE | R2 reachability / R4 C / R7 | `xexn45` `E-17`, `V-17`, `Required tests`; `7yr827` `E-01` and `F-04`; `g6tw94` and `n5sxxk` `V-*` (`0` test modules after round-3 split to Orders `120..123`, `127..129`) | `V-17` demanded diffing against per-part `.aw/state/<part>/*-after.txt` files and reading `.aw/state/xexn45/check-before.jsonl` across isolated lane worktrees where gitignored `.aw/state/` does not persist, missed test modules moved into round-3 children of `g6tw94`/`n5sxxk`, and cited `g6tw94` E-02 instead of `b3l7y6` E-05 for `test_specs_date_containment.py`. | Low | FIXED | `E-17`/`V-17` now run the deduplicated union of existing `tests/test_*.py` files across `tve77h`, `2xwb9b`, `7yr827..8q27jt`, Orders `120..136`, `b4y4ee`, and `xexn45`, regenerate `check-before.jsonl` from `7yr827` `F-04`'s baseline SHA when absent, and cite `b3l7y6` E-05. |
| PR-202 | HIGH | IN-SCOPE | R1 / R2 / R4 A | `xexn45` `E-13 (a)-(b)`, `V-13`, `D-3`; `agent_workflows/status_set.py::_prepare_status_change`; `1dvb08` `E-01`; `4sd62s` `AC-6` and `4.4a` | `E-13 (b)` asserted that `aw backlog set <id6> done` and `aw ipd finalize` both emit a scope bullet, whereas `backlog` `done` never emits a scope bullet and `finalize` unsets `- Approval:` while emitting `- Scope-Exceeded:` only on out-of-scope finalize (`D-3`); `V-13` also created a self-hash loop by demanding the plan's own final commit SHA. | Low | FIXED | Specified exact Phase-B `git diff` hunks for non-blocking `aw backlog set <id6> done`, within-scope `aw ipd finalize`, and out-of-scope `aw ipd finalize --scope-reason`, and committed `tests/test_writers_obligations.py` in `E-13` so `V-13` cites an immutable code SHA. |
| PR-203 | MEDIUM | IN-SCOPE | R1 / R4 Spec-doc sync | `xexn45` `E-16`, `V-16`; `docs/cli-output-contract.md`; `h06gs7` `E-02`; `tests/test_cli_agent_protocol_doc.py` | `E-16` did not align its `docs/cli-output-contract.md` edit with `h06gs7` `E-02`'s `aw describe` contract entry or guard `## 6. Token Control` via `tests/test_cli_agent_protocol_doc.py`, and omitted the user-facing no-em/en-dash rule for `docs/cli-output-contract.md` and `CHANGELOG.md`. | Low | FIXED | Scoped `E-16`/`V-16` beside `h06gs7` `E-02`'s `aw describe` entry (leaving `## 6. Token Control` untouched), enforced zero em/en dashes, and added `tests/test_cli_agent_protocol_doc.py` to `V-16`. |
| PR-204 | MEDIUM | IN-SCOPE | R7 Cross-plan alignment | `xexn45` `D-1`, `D-5`, `D-6`; `7yr827` `D-5`; `9qhtrc` `V-01`; `b3l7y6` `E-05` | `D-1`, `D-5`, and `D-6` retained pre-split claims contradicting reviewed child plans (`render_legacy_text` instead of `restore_legacy_snapshot` in `D-5`, nonexistent `test_artifact_meta_registry.py` edits in `D-6`, deleted `E-05` in `D-1`, and `D-6` ordered before `D-5`). | Low | FIXED | Reconciled `D-1..D-6` in numerical order with `7yr827`, `b3l7y6`, and `9qhtrc`. |
| PR-205 | LOW | IN-SCOPE | Proofreading / S7 contract / R4 | `xexn45` `Checklist`, `Step 0`, `F-07`, `F-09`, `Proposed changes`, `Validation`, `Approval gate` | Retained leftover `E-NEW` scaffold text, pre-split `Step 0`/`F-07` wording, incomplete `F-09` cross-references for the eight `F-03` modules, two `IPD-C802` em dashes, no Mermaid diagram, and no stop-and-report clause. | Low | FIXED | Removed `E-NEW` text and em dashes, updated `Step 0`/`F-07`/`F-09` cross-references across all 18 writer modules, qualified `4sd62s` AC refs, added `flowchart TD` diagram, and added the stop-and-report clause. |
| PR-206 | MEDIUM | IN-SCOPE | R1 / R2 / R7 | `xexn45` `Deferred / out of scope` (`- Carrier: 2xwb9b`, `7yr827..b4y4ee`); `aw check plans --agent` (`check.ipd-carrier-finished-unverified`) | `xexn45` triggered `check.ipd-carrier-finished-unverified` because `2xwb9b` is already `executed` without `- Carrier-Evidence:`, and `E-17` would trigger the same diagnostic on `xexn45` once `7yr827..b4y4ee` execute unless `- Carrier-Evidence:` is recorded. | Low | FIXED | Added verified `- Carrier-Evidence:` for `2xwb9b` now and instructed `E-17`/`V-17` to record `- Carrier-Evidence:` for the seven finished split-part carriers before running `aw check --agent`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-201 | How should `E-17` verify writer test suites and `aw check` baselines in an isolated lane worktree? | Run the deduplicated union of existing `tests/test_*.py` modules across all prerequisite writer parts and regenerate `check-before.jsonl` from `7yr827` `F-04`'s recorded baseline SHA when absent | Require cross-lane `.aw/state/<part>/*-after.txt` files (unreachable because `.aw/state/` is gitignored); skip baseline comparison | `7yr827` `F-04` design intent; `.aw/.gitignore`; `109` real test modules across Orders `02`, `06`, `21..26`, `120..136`, and `07` | yes |
| D-202 | How should `E-13 (b)` pin `4sd62s` `AC-6` in Phase B? | Pin exact `git diff` metadata hunks across three fixtures: non-blocking `aw backlog set <id6> done`, within-scope `aw ipd finalize` (`- Approval:` unset, zero scope bullet per `D-3`), and out-of-scope `aw ipd finalize --scope-reason` (`- Scope-Exceeded:` added) | Assert a scope bullet on backlog `done` and within-scope finalize (contradicts `status_set.py` and `D-3`) | `agent_workflows/status_set.py::_prepare_status_change`; `1dvb08` `E-01`; `xexn45` `D-3` | yes |
| D-203 | How should finished split-part carriers in `xexn45` `## Deferred` be handled for `aw check`? | Record `- Carrier-Evidence:` for already-executed `2xwb9b` now and record `- Carrier-Evidence:` for `7yr827..8q27jt` and `b4y4ee` in `E-17` before running `aw check --agent` | Leave `- Carrier:` rows without `- Carrier-Evidence:` (causes `check.ipd-carrier-finished-unverified` on `xexn45` in `E-17`) | `agent_workflows/check_engine.py::evaluate_durable_carrier` (`check.ipd-carrier-finished-unverified`) | yes |
