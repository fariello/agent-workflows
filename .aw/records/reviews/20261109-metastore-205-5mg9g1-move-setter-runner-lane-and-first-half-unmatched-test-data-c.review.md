# Review findings: plan 5mg9g1

- Subject-Id: 5mg9g1
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-4-carbon-medium
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `537a13f3e` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-205-5mg9g1-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `0` advisories), the `F-40` `rg -c` counts matched HEAD (`12`, `9`, `2`, `92`, `61`, `31`, `1`; sum `208`), `42` slow tests in `tests/slow_allowlist.txt` mapped to these 7 modules, and the exact batch-rule baseline run (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0` over all 7 target modules) passed (`281 passed in 162.43s`). During review, code inspection revealed that `tests/test_oc_runipd.py` exports `_CONFORMING_PLAN` and `_init_repo_with_conforming_plan` to 25 other `tests/test_*.py` modules while missing the `59aiyh` E-09 helper prefix regex (`PR-001`); revisions added explicit export-preservation and cross-module importer verification (`E-01`, `E-03`, `V-01`, `V-03`, `F-40`, `D-2`), added the required lifecycle and stop-condition clauses to `Approval and execution gate` (`PR-002`), added `mkdir -p .aw/state/59aiyh` to batch rule step 1 and inlined the `59aiyh` E-09 helper regex in `V-01` and `V-02` (`PR-003`), updated `OQ-01` owner to `plan author` and documented `D-1..D-6` under `Behavior decisions` (`PR-004`), standardized `Step 0` citations to `path::Symbol` and added a Requirement 12(b) Mermaid `flowchart TD` diagram (`PR-005`), and recorded review readiness, tier, and status (`PR-006`). Pass 2 re-checked the complete revised plan against `4sd62s`, `63ib9r`, `1upea0`, `653ndz`, `9rgn2w`, `59aiyh`, and `cxxmyv`, and `aw ipd lint --phase review-finalize --agent` returned `clean` with `0` findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| E-01, E-03, F-40, V-01, V-03 | Listed `none` for `test_oc_runipd.py` helpers and omitted cross-module export guard | Documented `_CONFORMING_PLAN` and `_init_repo_with_conforming_plan` exports to 25 `tests/test_*.py` modules, preserved their call contracts, and added importer pytest verification in `E-03` and `V-03` | PR-001, prevent cross-module breakage across external callers. |
| Approval and execution gate | Omitted hand-mv prohibition, conditional runner/executor finalize ownership, and narrow unsafe-condition stop rule | Added explicit `never a hand git mv`, conditional runner/executor finalize clause, and narrow unsafe-condition stop rule | PR-002, `steps/r2-executability.md` and `steps/s7-finalize.md`. |
| Batch rule step 1, V-01, V-02 | Redirected into `.aw/state/59aiyh/` without creating the directory; cited "the E-09 `rg` pattern" without defining it in `5mg9g1` | Added `mkdir -p .aw/state/59aiyh` in step 1 and inlined the exact `59aiyh` E-09 helper-census `rg` command in `V-01` and `V-02` | PR-003, Technical Writing Standard Requirement 6 (self-contained commands). |
| Open questions (OQ-01), Findings | Recorded `- Owner: none` on resolved `OQ-01` and omitted `Behavior decisions` | Set `- Owner: plan author` on `OQ-01` and added `Behavior decisions` (`D-1..D-6`) | PR-004, `steps/s5-questions.md` owner attestation rule. |
| Authoring note, Step 0, Proposed changes | Imperative authoring prompt; bare `module.function` citations; two-step prose without diagram | Replaced prompt with declarative conformance note, standardized `Step 0` citations to `path::Symbol`, and added `flowchart TD` diagram | PR-005, Technical Writing Standard Requirements 7 and 12(b), `IPD-C801`. |
| Front matter, Workflow history | Carried `- Status: to-review` without `- Readiness:` or `- Review-Depth:` | Added `- Readiness: go-pending-approval`, `- Review-Depth: complex`, `/plan-review` history record, and `- Status: reviewed` | PR-006, `steps/s7-finalize.md` review output contract. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `5mg9g1` converts 7 runner, lane, merge, and analytics test modules (subset G5a, chunk 3 of 7 of `1upea0`, including `tests/test_oc_runipd.py` with 92 F-01 matches and cross-module exports) onto `tests/record_builder.py::RecordBuilder` via `tools/fixture_codemod.py`.
2. No. Test-data migration only; production code under `agent_workflows/` and `tools/` is excluded.
3. No. Right-sized at 3 `E-*` items (2 batch items of 4 and 3 modules, plus 1 finishing item) across 7 test modules.
4. Yes. `- Scope-Paths:` names all 7 target test modules plus the plan file itself.
5. Yes. Per-test outcome invariance across 281 tests (including 42 `slow` tests) and cross-module compatibility for 25 other `tests/test_*.py` modules importing `tests.test_oc_runipd`.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (sections 6, 7 step 6, C10a, N3, AC-1b), orchestrator `63ib9r` (`E-129`/`V-129`, Order 205 row), split parent `1upea0` (Order 50, `F-41`), codemod `653ndz` (`y3uowx`), builder `9rgn2w` (`j6o96i`), finishing plan `59aiyh`, cutover `cxxmyv`, research `nj8zdp`, and all 7 target test modules on HEAD `537a13f3e`.
- Verified all 16 referenced `id6` identifiers resolve cleanly via `aw find all --agent` and all `F-40` counts match HEAD (`208` lines total).
- Found `OQ-01` owner violation (`- Owner: none` on a resolved question, `PR-004`) and bare `module.function` citations in `Step 0` (`PR-005`). Fixed in place.

### Step R2

- Checked: 3-to-3 `E-*`/`V-*` bijection (`E-01..E-03` <-> `V-01..V-03`, `- Highest E allocated: 03`), DAG edges (`E-01, E-02 -> E-03`), `- Scope-Paths:` completeness, command flags in isolated lane worktrees, and execution-contract clauses in `Approval and execution gate`.
- Found missing cross-module export guard on `tests/test_oc_runipd.py::_CONFORMING_PLAN` and `tests/test_oc_runipd.py::_init_repo_with_conforming_plan` (`PR-001`), missing `never a hand git mv`, conditional finalize ownership, and unsafe-condition stop rule in `Approval and execution gate` (`PR-002`), and missing `mkdir -p .aw/state/59aiyh` plus uninlined `59aiyh` E-09 helper regex in `V-01`/`V-02` (`PR-003`). Fixed all three in place.

### Step R3

- Checked: test-isolation safety, gitignored `.aw/state/` containment, refusal ceiling (`at most 25` hand conversions before stopping), prohibition on weakening assertions or editing production code, and `raw_fields=` scoping to deliberate invalid-input tests only. No security or credential boundary is touched.

### Step R4

- Checked: alignment with `4sd62s` section 6 and C10a, deterministic outcome comparison (`-o addopts="" -m "" -p no:randomly -n 0`), behavioral-only testing (`AGENTS.md`), right-sizing (`3` `E-*` items, `7` work Scope-Paths), and Technical Writing Standard Requirement 12(b) diagram coverage (`PR-005`). Verified the exact step-2 pytest command passes all `281` collected items (`162.43s`) on unmodified HEAD.

### Step R5

- Checked: all eight viewpoints in `.aw/system/workflows/release-review/00-run-protocol.md#Review mindset: the eight reviewer personas` - QA/QC (byte-exact sorted per-test outcome diffs), Testing and regression (cross-module importer check for 25 callers of `tests.test_oc_runipd`, `PR-001`), UI/UX (not user-facing CLI output), Architect (single phase-B builder seam ahead of `cxxmyv`), Software engineer (inlined helper regex and `mkdir -p`, `PR-003`), Power user and Novice (self-contained modest-executor steps), and Stakeholder (`Blocks-Release: next` preserved with bounded hand-edit risk).

### Step R6

- Checked: `3` `E-*` items in `2` task groups across `7` test modules (`4` in `E-01`, `3` in `E-02`), already round-3 split from `1upea0` per research `nj8zdp` (`- Size assessment: standard`). No further split is warranted.

### Step R7

- Checked: consistency with orchestrator `63ib9r` (`E-129`/`V-129`), split parent `1upea0` (`F-41`), reviewed sibling chunk plans `9hk3rh` (Order 204, whose `tests/test_agy_runipd_cli.py` imports `_CONFORMING_PLAN` from `tests.test_oc_runipd`) and `1cgrgp` (Order 206, whose `tests/test_runner_bare_verb_shim.py` and `tests/test_runner_stop_triggers_e2e.py` import `_CONFORMING_PLAN` from `tests.test_oc_runipd`), finishing plan `59aiyh`, and `- Item-Dependencies: executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45`. Preserving `test_oc_runipd` exports (`D-2`) guarantees sibling chunks remain order-independent (`OQ-01`).

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`), updated `- Owner: plan author`, and recorded six engineering decisions (`D-1..D-6`) in `### Behavior decisions` and `### Decisions` below, all `Reversible: yes`. Zero human-owned questions remain (`questions: []`).

### Pass 2

- Re-read the complete revised plan (`.aw/records/plans/pending/20261109-metastore-205-5mg9g1-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md`) from line 1 to line 197 per `steps/s6-rereview.md` rule 1 after applying `PR-001..PR-006`.
- Verified 3-to-3 `E-*`/`V-*` bijection (`E-01..E-03` <-> `V-01..V-03`), `- Highest E allocated: 03`, unchanged `- Scope-Paths:` and `- Item-Dependencies:`, exact term consistency between text, tables, and the `flowchart TD` diagram, zero absolute paths or `file://` URIs, and `0` findings from `aw ipd lint --phase review-finalize --agent`.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / R4 / R7 / Cross-module exports | .aw/records/plans/pending/20261109-metastore-205-5mg9g1-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:49, .aw/records/plans/pending/20261109-metastore-205-5mg9g1-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:94 | `tests/test_oc_runipd.py` exports `_CONFORMING_PLAN` (line 2809) and `_init_repo_with_conforming_plan` (line 2906) to 25 other `tests/test_*.py` modules, which the `59aiyh` E-09 helper prefix regex misses; deleting or altering their `.format(id6=...)` / `(repo, id6)` contract during `E-01` would silently break external modules outside `5mg9g1`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Documented both exports in `F-40` and `D-2`, required preserving their exported contracts in `E-01`/`V-01`, and added `python3 -m pytest -m "" $(rg -l "tests\.test_oc_runipd" tests/)` in `E-03`/`V-03` (recommendation strength: very strong). |
| PR-002 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-205-5mg9g1-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:189, .aw/records/plans/pending/20261109-metastore-205-5mg9g1-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:197 | `Approval and execution gate` omitted the explicit `never a hand git mv` prohibition, conditional runner vs. standalone executor ownership of `aw ipd finalize`, and narrow unsafe-condition stop rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `never a hand git mv`, conditional `aw oc run`/`aw agy run` vs. standalone executor finalize ownership, and narrow unsafe-condition stop rule to `Approval and execution gate` (recommendation strength: very strong). |
| PR-003 | MEDIUM | IN-SCOPE | R2 / Batch rule step 1 & V-01..V-02 | .aw/records/plans/pending/20261109-metastore-205-5mg9g1-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:39, .aw/records/plans/pending/20261109-metastore-205-5mg9g1-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:170 | Batch rule step 1 wrote into gitignored `.aw/state/59aiyh/` without creating the directory first, and `V-01`/`V-02` referenced "the E-09 `rg` pattern" without defining that `59aiyh` regex inside `5mg9g1`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `mkdir -p .aw/state/59aiyh` in batch rule step 1 and inlined the exact `59aiyh` E-09 helper-census `rg` pattern in `V-01` and `V-02` (recommendation strength: strong). |
| PR-004 | MEDIUM | IN-SCOPE | R1 / S5 / OQ-01 & Behavior decisions | .aw/records/plans/pending/20261109-metastore-205-5mg9g1-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:162 | `OQ-01` recorded `- Owner: none` on a resolved question (`steps/s5-questions.md` violation), and settled execution choices lacked a `Behavior decisions` subsection under `Findings`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `OQ-01` to `- Owner: plan author`, added `Behavior decisions` (`D-1..D-6`) under `Findings`, and logged `D-1..D-6` in `### Decisions` (recommendation strength: strong). |
| PR-005 | LOW | IN-SCOPE | Proofreading / Req. 7 & Req. 12(b) | .aw/records/plans/pending/20261109-metastore-205-5mg9g1-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:22, .aw/records/plans/pending/20261109-metastore-205-5mg9g1-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:68, .aw/records/plans/pending/20261109-metastore-205-5mg9g1-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:108 | Plan retained an imperative authoring-prompt note at line 22, used unqualified `module.function` citations in `Step 0` (`IPD-C801`), and omitted a Mermaid `flowchart TD` diagram under `Proposed changes` (Technical Writing Standard Requirement 12(b)). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced the imperative authoring prompt with a declarative conformance note, converted `Step 0` citations to repo-relative `path::Symbol` identifiers, and added a `flowchart TD` diagram under `Proposed changes` (recommendation strength: strong). |
| PR-006 | LOW | IN-SCOPE | S7 / Front matter & Workflow history | .aw/records/plans/pending/20261109-metastore-205-5mg9g1-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:9, .aw/records/plans/pending/20261109-metastore-205-5mg9g1-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:25 | Pre-review front matter carried `- Status: to-review` without `- Readiness:` or `- Review-Depth:`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set `- Readiness: go-pending-approval`, `- Review-Depth: complex`, prepended the `/plan-review` workflow history entry, and transitioned `- Status: reviewed` via `aw ipd set` (recommendation strength: very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can Chunk 3 (`5mg9g1`) run in any order relative to sibling chunk plans? | Yes, once `653ndz`, `9rgn2w`, `g5hpbb`, `tve77h`, and `xexn45` are executed and `test_oc_runipd` exports are preserved (`D-2`). | Enforce strict serial ordering across all chunk plans of `1upea0` (rejected: serializes disjoint test module sets unnecessarily). | `OQ-01`, `1upea0` `F-41`, research `nj8zdp` | yes |
| D-2 | How should `tests/test_oc_runipd.py::_CONFORMING_PLAN` and `_init_repo_with_conforming_plan` be handled during `E-01`? | Keep both symbols exported with `.format(id6=...)` and `(repo: Path, id6: str = "slf001") -> Path` compatibility intact, and run pytest across all `rg -l "tests\.test_oc_runipd" tests/` importers in `E-03`. | Delete or rename them as private helpers (rejected: breaks 25 importing `tests/test_*.py` modules, including sibling chunks `9hk3rh` and `1cgrgp`); expand `- Scope-Paths:` to rewrite all 25 external callers here (rejected: blows past the 8-file right-sizing cap from `nj8zdp`). | `rg -l "tests\.test_oc_runipd" tests/`, `tests/test_oc_runipd.py` lines 2809 and 2906 | yes |
| D-3 | How should private record-building helpers be censused and cleaned up in `5mg9g1`? | Inline the exact `59aiyh` E-09 `rg` pattern in `V-01` and `V-02`, delete only unreferenced helpers, and list surviving helpers with their reason. | Leave the bare cross-reference "the E-09 `rg` pattern" (rejected: forces a modest executor to look up `59aiyh` to run `V-01`/`V-02`). | `59aiyh` V-09, `nj8zdp` modest-executor rule | yes |
| D-4 | What happens if an item's hand-conversion refusal count exceeds 25? | Stop hand conversion after codemod step 3, allow committing proved codemod rewrites, and report the subset for re-splitting. | Convert unbounded hand refusals in one turn (rejected: exceeds modest-executor error budget). | Batch rule step 4, `653ndz`, `nj8zdp` | yes |
| D-5 | How are deliberately invalid metadata values constructed in converted tests? | Pass invalid metadata through `tests/record_builder.py::RecordBuilder`'s `raw_fields=` escape and classify remaining matches as `invalid-input`. | Keep ad-hoc raw string literals for entire artifacts (rejected: bypasses phase-B builder centralization). | Batch rule step 4, `F-08`, spec `4sd62s` section 6 | yes |
| D-6 | How is `.aw/state/59aiyh/` initialized in isolated lane worktrees? | Run `mkdir -p .aw/state/59aiyh` in batch rule step 1 before writing `<batch>-files.txt` and `<batch>-before.txt`. | Assume `.aw/state/59aiyh/` already exists (rejected: `.aw/state/` is gitignored and absent in fresh lane worktrees). | Batch rule step 1, `.gitignore` | yes |
