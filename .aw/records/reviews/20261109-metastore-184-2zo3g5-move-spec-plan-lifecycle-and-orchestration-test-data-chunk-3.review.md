# Review findings: plan 2zo3g5

- Subject-Id: 2zo3g5
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `a78705a91` in the isolated runner lane worktree `review-sweep-run-20261114T042744Z-1314525`. The tracked plan `.aw/records/plans/pending/20261109-metastore-184-2zo3g5-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-3.ipd.md` was committed and clean, so the pre-review snapshot was skipped. Structural preflight `aw ipd lint --phase author --agent` returned `clean` (0 findings, exit 0). Reference baseline: `python3 -m pytest -m "" <the 8 Scope-Paths test modules>` printed `216 passed in 85.54s (0:01:25)`. After revisions, `aw ipd lint --phase review-finalize --agent` returned `clean` (0 findings, exit 0). Re-measured facts at review HEAD: all 8 modules exist; F-01 `rg -c` counts match the plan's `3d0ddb845` column exactly (23, 34, 18, 3, 39, 23, 24, 85); `tests/record_builder.py` and `tools/fixture_codemod.py` do not exist yet, as expected, because their plans (`j6o96i`/`9rgn2w`, `y3uowx`/`653ndz`) are pending and are prerequisites.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Batch rule step 1 | Re-derive via the F-03 partition (pattern lists not in this plan); context commits `0cbfcc706`/`ac76110f4` | `mkdir -p`, then `rg -l` with the F-01 pattern over the named modules; context commit `3d0ddb845` | PR-003 |
| Batch rule step 3 | `--apply --format json` only | Adds a fallback to the default `--apply` report saved as `-codemod.txt` | PR-004 |
| Batch rule step 8 (new) | V-items cited an undefined "E-09 `rg` pattern" | Inlines the helper pattern and adds the other-named record-text helper class | PR-001, PR-002 |
| E-01, E-02, E-03 | Helper lists covered only pattern-named helpers; E-01 said "no helper" | Names the other-named helpers measured at review; notes linter-subject text in `test_ipd_lint.py` | PR-002 |
| V-01, V-02, V-03 | "helper census of the E-09 `rg` pattern"; `-codemod.json` only | "helper census of batch rule step 8"; accepts `-codemod.txt` | PR-001, PR-004 |
| Project conventions | `module.function` citations | `path::Symbol` citations | PR-006 |
| Proposed changes | No diagram for the branching batch rule | Mermaid `flowchart TD` of the batch rule | PR-007 |
| OQ-01 | `- Owner: none` on a resolved question | `- Owner: plan author`; D-1 recorded | PR-008 |
| Approval and execution gate | No hand `git mv` ban, no conditional finalize ownership, no narrow stop rule | All three added | PR-005 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No. The plan edits test modules only; it changes no spec, CLI, file format or configuration key.
2. No. It touches no code that guards private data, commits, worktree isolation, merges or the sandbox.
3. No. 4 E-items, 2 task groups, 8 test modules in one family.
4. Yes. `- Scope-Paths:` lists the 8 test modules and the plan.
5. Yes, bounded: a wrong conversion could change test outcomes, but every item demands an identical before/after outcome list, and each change is a reversible test-file edit.

AW-TIER: standard

### Step R1

- Checked: every cited plan id (`653ndz`, `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45`, `7qxey9`, `59aiyh`, `cxxmyv`, `y3uowx`, `j6o96i`, `1bshrb`), the F-01 pattern and counts at HEAD, the F-40 helper table, `7qxey9` F-41 (subset and chunk assignment of the 8 modules), and the codemod interface in `y3uowx` E-01 to E-03.
- "the E-09 `rg` pattern" (V-01 to V-03) does not resolve in this plan; the pattern lives in `59aiyh` V-09 and `1bshrb` E-38 (PR-001).
- `y3uowx` E-01 specifies `--format table|json` for `--dry-run` only; this plan and 42 sibling plans run `--apply --format json` (PR-004).

### Step R2

- Checked: E/V bijection (E-01..E-04 to V-01..V-04, `Highest E allocated: 04`), Scope-Paths completeness, Item-Dependencies (all five exist; `tve77h` executed, others pending), executability of each batch-rule step, and reachability: no V-item demands an observed runtime behavior beyond test runs and file contents, which are reachable by construction.
- Batch rule step 1 depended on F-03 group pattern lists that this plan does not carry and omitted `mkdir -p` for the untracked state directory (PR-003).

### Step R3

- Checked: the plan edits only test modules, writes scratch output to untracked `.aw/state/59aiyh/`, commits through `aw commit 2zo3g5`, and never pushes. No secrets, authorization, or trust-boundary input is involved. Not applicable beyond that.

### Step R4

- Checked: anti-regression (identical per-test outcome lists per item and for the union, no weakened assertions), right-sizing (each batch item is one codemod run over 2 to 4 modules with a 25-site hand stop), reuse (shared builder and codemod, no new mechanism), spec sync (no spec change is truthful: the plan implements `4sd62s` section 6 and does not alter behavior).
- The helper census pattern misses record-text helpers named outside its prefix list, so an executor could leave dead record builders unlisted (PR-002).

### Step S5

- Checked: OQ-01 (resolved, non-blocking). Its resolution is supported by `7qxey9` F-41 (disjoint module lists) and `59aiyh` E-09 (sole editor of `tests/support.py`). No question needs the human. No finding is left OPEN or DEFERRED.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | R1 references | `.aw/records/plans/pending/20261109-metastore-184-2zo3g5-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-3.ipd.md` V-01 "helper census of the E-09 `rg` pattern" | V-01 to V-03 demand a census by "the E-09 `rg` pattern", but this plan has no E-09; the pattern is in `59aiyh` V-09 and `1bshrb` E-38. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added batch rule step 8 with the pattern inlined; V-items now cite step 8 (recommendation strength: strong). |
| PR-002 | MEDIUM | UNDER-SCOPE | R4 D anti-regression / helpers | `tests/test_specs_verbs.py::_spec`, `tests/test_ipd_dependency_check.py::_plan`, `tests/test_ipd_lint.py::_conforming_child` | The `def _?(make\|write\|build\|mk\|seed)_...` pattern misses 9 record-text helpers in these modules; E-01 claimed its modules held no helper. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Step 8 adds the other-named class; E-01 to E-03 name each helper measured at review (recommendation strength: strong). |
| PR-003 | MEDIUM | IN-SCOPE | R2 executability | plan batch rule step 1 "re-derive its file list with the F-03 first-match partition" | Step 1 needed F-03 group pattern lists absent from this plan, omitted creating the untracked state directory, and named context commits that do not match the items' `3d0ddb845` counts. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Step 1 is now `mkdir -p` plus `rg -l` with the F-01 pattern over the named modules (equivalent, because every named module is in its subset per `7qxey9` F-41) (recommendation strength: strong). |
| PR-004 | LOW | IN-SCOPE | R2 executability / cross-plan | `.aw/records/plans/pending/20261109-metastore-172-y3uowx-build-the-fixture-codemod-detector-rewriter-and-equivalence.ipd.md` E-01 "`--dry-run [--format table\|json]`" | This plan runs `--apply --format json`, but `y3uowx` specifies `--format` only for `--dry-run`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a fallback to the default `--apply` report (`-codemod.txt`) and V-items accept either. Recommend that the `y3uowx` owner state `--format json` for `--apply`, since 43 plans rely on it (recommendation strength: medium). |
| PR-005 | LOW | IN-SCOPE | G execution contract | plan `## Approval and execution gate` "Lifecycle transition" | The gate lacked a hand `git mv` ban, conditional runner/executor finalize ownership, and a narrow unsafe-condition stop rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all three (recommendation strength: strong). |
| PR-006 | LOW | IN-SCOPE | Proofreading, requirement 7 (`IPD-C801`) | plan `## Project conventions discovered (Step 0)` "`artifact_meta.registry_fields(type)`" | Code was cited as `module.function` instead of `path::Symbol`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Converted to `path::Symbol` (recommendation strength: strong). |
| PR-007 | LOW | IN-SCOPE | Proofreading, requirement 12(b) | plan batch rule steps 1 to 8 | An 8-step process with two stop branches had no diagram. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a Mermaid `flowchart TD` under `## Proposed changes` (recommendation strength: medium). |
| PR-008 | LOW | IN-SCOPE | S5 owner attestation | plan OQ-01 "- Owner: none" | A resolved question recorded `Owner: none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set `- Owner: plan author`; D-1 recorded (recommendation strength: strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can this chunk run in any order relative to the other chunk plans? | Yes, as OQ-01 resolves. | Serialize the chunk plans (rejected: module lists are disjoint). | `7qxey9` F-41; `59aiyh` E-09 | yes |
| D-2 | How does step 1 re-derive the file list without the F-03 pattern lists? | `rg -l` with the F-01 pattern over the item's named modules. | Copy the F-03 group pattern lists into this plan (rejected: the restriction to named modules makes them redundant). | plan batch rule ("restricted to the modules each batch item names"); `7qxey9` F-41 | yes |
| D-3 | What if `--apply` refuses `--format json`? | Save the default `--apply` report as `-codemod.txt` and read the same rows. | Stop the item (rejected: the report content, not its format, is what V-items need). | `y3uowx` E-01, E-03 | yes |
| D-4 | Which review tier applies? | `standard`. | `complex` (rejected: no contract change, single family, 4 items). | Step T answers | yes |
