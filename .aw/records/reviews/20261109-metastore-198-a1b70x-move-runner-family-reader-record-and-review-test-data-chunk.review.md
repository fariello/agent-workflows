# Review findings: plan a1b70x

- Subject-Id: a1b70x
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `b5a492301` in the isolated runner lane worktree `review-sweep-run-20261114T042744Z-1314525`. The tracked plan `.aw/records/plans/pending/20261109-metastore-198-a1b70x-move-runner-family-reader-record-and-review-test-data-chunk.ipd.md` was committed and clean, so the pre-review snapshot was skipped. Structural preflight `aw ipd lint --phase author --agent` on the HEAD copy returned `clean` (0 findings, exit 0). Reference baseline: `python3 -m pytest -m "" <the 8 Scope-Paths test modules>` printed `106 passed in 4.17s`. After revisions, `aw ipd lint --phase review-finalize --agent` returned `clean` (0 findings, exit 0). Re-measured at review HEAD: all 8 modules exist; F-01 `rg -c` counts match the plan's `3d0ddb845` column exactly (18, 34, 10, 6, 14, 12, 23, 6); `nbfg7w` F-41 assigns exactly these 8 modules to `a1b70x`; `tests/record_builder.py` and `tools/fixture_codemod.py` do not exist yet, as expected, because their plans are pending prerequisites.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Batch rule step 1 | Re-derive via the F-03 partition (pattern lists not in this plan); context commits `0cbfcc706`/`ac76110f4` | `mkdir -p`, then `rg -l` with the F-01 pattern over the named modules; context commit `3d0ddb845` | PR-003 |
| Batch rule step 3 | `--apply --format json` only | Fallback to the default `--apply` report saved as `-codemod.txt` | PR-004 |
| Batch rule step 6 | No class for F-01 matches in comments or docstrings | Such a match gets `body prose` | PR-006 |
| Batch rule step 8 (new) | V-items cited an undefined "E-09 `rg` pattern" | Inlines the helper pattern and adds the other-named helper class | PR-001, PR-002 |
| E-01, E-02, E-03 | Each carried subset-level text about `aw-prompt` tests, `test_front_matter_loose_whitespace.py` and `test_history_block_bounding.py`, none of which this plan converts | Replaced with module-specific guidance (two-dialect subject, raw inbox drops, the deliberate `EXECUTED (approved by maintainer)` value) and named helpers | PR-005, PR-002 |
| V-01, V-02, V-03 | "helper census of the E-09 `rg` pattern"; `-codemod.json` only | "helper census of batch rule step 8"; accepts `-codemod.txt` | PR-001, PR-004 |
| Project conventions | `module.function` citations | `path::Symbol` citations | PR-008 |
| Proposed changes | No diagram for the branching batch rule | Mermaid `flowchart TD` | PR-009 |
| OQ-01 | `- Owner: none` on a resolved question | `- Owner: plan author`; D-1 | PR-010 |
| Approval and execution gate | No hand `git mv` ban, no conditional finalize ownership, no narrow stop rule | All three added | PR-007 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No. The plan edits test modules only; it changes no spec, CLI, file format or configuration key.
2. No. It touches no code that guards private data, commits, worktree isolation, merges or the sandbox (`tests/test_artifact_adopt.py` exercises the leak gate but only its test data changes).
3. No. 4 E-items, 2 task groups, 8 test modules.
4. Yes. `- Scope-Paths:` lists the 8 test modules and the plan.
5. Yes, bounded: a wrong conversion could change test outcomes, but every item demands an identical before/after outcome list, and each change is a reversible test-file edit.

AW-TIER: standard

### Step R1

- Checked: plan ids `653ndz`, `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45`, `nbfg7w`, `59aiyh`, `cxxmyv`, `y3uowx`, `j6o96i`, `1bshrb`; the F-01 pattern and counts at HEAD; F-40; `nbfg7w` F-41; the builder's `research(...)` method in `j6o96i` E-01; the codemod interface in `y3uowx` E-01 to E-03.
- "the E-09 `rg` pattern" (V-01 to V-03) does not resolve in this plan (PR-001). E-01 to E-03 named `test_front_matter_loose_whitespace.py`, `test_history_block_bounding.py` and `aw-prompt` comment tests that are not in this plan; `rg "aw-prompt|prompt\("` over the 8 modules finds nothing (PR-005).

### Step R2

- Checked: E/V bijection (E-01..E-04 to V-01..V-04, `Highest E allocated: 04`), Scope-Paths completeness, Item-Dependencies, executability of every batch-rule step, reachability (no V-item demands observed runtime behavior beyond test runs and file contents).
- Step 1 depended on group pattern lists this plan does not carry and omitted `mkdir -p` (PR-003); `--apply --format json` is not promised by `y3uowx` (PR-004).

### Step R3

- Checked: only test modules change; scratch output goes to untracked `.aw/state/59aiyh/`; commits go through `aw commit a1b70x`; no push. `tests/test_artifact_adopt.py` pins leak-gate refusal behavior; the plan keeps its drop texts literal (PR-005 fix), so the gate's test coverage is unchanged.

### Step R4

- Checked: anti-regression (identical outcome lists per item and for the union, no weakened assertions), right-sizing (each batch item is one codemod run over 2 to 4 modules with a 25-site hand stop), reuse, and spec sync ("no spec change" is truthful).
- The helper census pattern misses `make_bullet_plan` and `_seed_adopted_copy` (PR-002). Several F-01 matches sit in comments and docstrings (for example `tests/test_artifact_adopt.py` line 6, `tests/test_selector_two_dialect_readers.py` line 122), and step 6 offered no class for them (PR-006).

### Step S5

- Checked: OQ-01 (resolved, non-blocking), supported by `nbfg7w` F-41 (disjoint module lists) and `59aiyh` E-09 (sole editor of `tests/support.py`). No question needs the human. No finding is left OPEN or DEFERRED.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | R1 references | plan V-01 "helper census of the E-09 `rg` pattern" | V-01 to V-03 cite an "E-09 `rg` pattern" this plan does not define; it lives in `59aiyh` V-09 and `1bshrb` E-38. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Batch rule step 8 inlines the pattern; V-items cite step 8 (recommendation strength: strong). |
| PR-002 | MEDIUM | UNDER-SCOPE | R4 D helpers | `tests/test_selector_two_dialect_readers.py::SelectorTwoDialectReadersBase.make_bullet_plan`, `tests/test_artifact_adopt.py::AlreadyAdoptedWarningTests._seed_adopted_copy` | The census pattern misses record-text helpers with other names; E-02 claimed no helper. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Step 8 adds the other-named class; E-01 to E-03 name each helper, and say why `_drop`, `_leaky_drop` and `_write_file` are not record builders (recommendation strength: strong). |
| PR-003 | MEDIUM | IN-SCOPE | R2 executability | plan batch rule step 1 "re-derive its file list with the F-03 first-match partition" | Step 1 needed group pattern lists absent from this plan, did not create the untracked state directory, and named context commits that do not match the items' `3d0ddb845` counts. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `mkdir -p` plus `rg -l` over the named modules, equivalent because `nbfg7w` F-41 places every named module in its subset (recommendation strength: strong). |
| PR-004 | LOW | IN-SCOPE | R2 cross-plan | `.aw/records/plans/pending/20261109-metastore-172-y3uowx-build-the-fixture-codemod-detector-rewriter-and-equivalence.ipd.md` E-01 "`--dry-run [--format table\|json]`" | `--format json` is promised only for `--dry-run`, but this plan runs `--apply --format json`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fallback to the default `--apply` report; recommend `y3uowx` state JSON output for `--apply` (recommendation strength: medium). |
| PR-005 | MEDIUM | IN-SCOPE | R2 executability / proofreading | plan E-02 "The `aw-prompt` comment tests use `prompt(...)`" | E-01 to E-03 repeated subset-level guidance that names modules and tests outside this plan, which could send an executor looking for work that is not here, while omitting the guidance these modules need (two-dialect subject, forged-id inbox drops, a deliberate invalid status). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with module-specific guidance (recommendation strength: strong). |
| PR-006 | LOW | UNDER-SCOPE | R4 classification | `tests/test_artifact_adopt.py` "1. a body carrying a BULLET `- Id: <id6>`" (module docstring) | F-01 matches in comments and docstrings had no F-06 reason class. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Step 6 classes them `body prose` (D-3) (recommendation strength: medium). |
| PR-007 | LOW | IN-SCOPE | G execution contract | plan `## Approval and execution gate` "Lifecycle transition" | No hand `git mv` ban, no conditional finalize ownership, no narrow stop rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all three (recommendation strength: strong). |
| PR-008 | LOW | IN-SCOPE | Proofreading, requirement 7 (`IPD-C801`) | plan `## Project conventions discovered (Step 0)` "`artifact_meta.registry_fields(type)`" | `module.function` citations. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Converted to `path::Symbol` (recommendation strength: strong). |
| PR-009 | LOW | IN-SCOPE | Proofreading, requirement 12(b) | plan batch rule steps 1 to 8 | A branching 8-step process had no diagram. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a Mermaid `flowchart TD` (recommendation strength: medium). |
| PR-010 | LOW | IN-SCOPE | S5 owner attestation | plan OQ-01 "- Owner: none" | A resolved question recorded `Owner: none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Owner: plan author`; D-1 (recommendation strength: strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can this chunk run in any order relative to the other chunk plans? | Yes, as OQ-01 resolves. | Serialize the chunk plans (rejected: module lists are disjoint). | `nbfg7w` F-41; `59aiyh` E-09 | yes |
| D-2 | How does step 1 re-derive the file list without the F-03 pattern lists? | `rg -l` with the F-01 pattern over the item's named modules. | Copy the group pattern lists into this plan (rejected: redundant under the named-module restriction). | plan batch rule; `nbfg7w` F-41 | yes |
| D-3 | Which reason class does an F-01 match in a comment or docstring get? | `body prose`. | Add a new class (rejected: F-06's class set is owned by `59aiyh`, and a comment is prose). | `59aiyh` F-06 class list | yes |
| D-4 | Are inbox drop texts in `tests/test_artifact_adopt.py` converted? | No; they are raw inbox material and stay literal as `legacy-format subject`. | Build them with the builder (rejected: a drop is not a record, and the forged `- Id:` is the test's subject). | AGENTS.md "The inbox: raw drops awaiting adoption"; `tests/test_artifact_adopt.py` module docstring | yes |
| D-5 | What if `--apply` refuses `--format json`? | Save the default report as `-codemod.txt`. | Stop the item (rejected: the report content is what V-items need). | `y3uowx` E-01, E-03 | yes |
