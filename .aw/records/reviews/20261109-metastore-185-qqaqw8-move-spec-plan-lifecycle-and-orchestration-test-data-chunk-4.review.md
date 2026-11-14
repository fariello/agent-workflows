# Review findings: plan qqaqw8

- Subject-Id: qqaqw8
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `43315c395` in the isolated runner lane worktree `review-sweep-run-20261114T042744Z-1314525`. The tracked plan `.aw/records/plans/pending/20261109-metastore-185-qqaqw8-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-4.ipd.md` was committed and clean, so the pre-review snapshot was skipped. Structural preflight `aw ipd lint --phase author --agent` returned `clean` (0 findings, exit 0). Reference baseline: `python3 -m pytest -m "" <the 7 Scope-Paths test modules>` printed `186 passed in 18.44s`. After revisions, `aw ipd lint --phase review-finalize --agent` returned `clean` (0 findings, exit 0). Re-measured at review HEAD: all 7 modules exist; F-01 `rg -c` counts match the plan's `3d0ddb845` column exactly (8, 7, 8, 8, 39, 16, 6); `7qxey9` F-41 assigns exactly these 7 modules to `qqaqw8`; the two pattern-matched helpers (`_write_plan` in `tests/test_ipd_set_executor.py` and `tests/test_ipd_set_plan.py`) are present.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Batch rule step 1 | Re-derive via the F-03 partition (pattern lists not in this plan); context commits `0cbfcc706`/`ac76110f4` | `mkdir -p`, then `rg -l` with the F-01 pattern over the named modules; context commit `3d0ddb845`; notes the `test_ipdrunner_runagy_shim` double match | PR-003 |
| Batch rule step 3 | `--apply --format json` only | Fallback to the default `--apply` report saved as `-codemod.txt` | PR-004 |
| Batch rule step 8 (new) | V-items cited an undefined "E-09 `rg` pattern" | Inlines the helper pattern and adds the other-named helper class | PR-001, PR-002 |
| E-01, E-02 | Helper lists covered only pattern-named helpers; E-02 said "no helper" | Names each other-named helper measured at review; notes `test_ipd_schema` subject and `_review`'s production writer | PR-002 |
| V-01, V-02 | "helper census of the E-09 `rg` pattern"; `-codemod.json` only | "helper census of batch rule step 8"; accepts `-codemod.txt` | PR-001, PR-004 |
| Project conventions | `module.function` citations | `path::Symbol` citations | PR-006 |
| Proposed changes | No diagram | Mermaid `flowchart TD` of the batch rule | PR-007 |
| OQ-01 | `- Owner: none` | `- Owner: plan author`; D-1 | PR-008 |
| Approval and execution gate | No hand `git mv` ban, conditional finalize ownership or narrow stop rule | All three added | PR-005 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No. Test modules only.
2. No.
3. No. 3 E-items, 2 task groups, 7 test modules.
4. Yes. `- Scope-Paths:` lists the 7 modules and the plan.
5. Yes, bounded: outcome lists must be identical before and after, and each change is a reversible test edit.

AW-TIER: standard

### Step R1

- Checked: plan ids `653ndz`, `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45`, `7qxey9`, `59aiyh`, `cxxmyv`, `y3uowx`, `j6o96i`, `1bshrb`; F-01 counts; F-40; `7qxey9` F-41; the codemod interface in `y3uowx` E-01 to E-03.
- "the E-09 `rg` pattern" does not resolve in this plan (PR-001). `y3uowx` promises `--format json` only for `--dry-run` (PR-004).

### Step R2

- Checked: E/V bijection (E-01..E-03 to V-01..V-03, `Highest E allocated: 03`); Scope-Paths; Item-Dependencies; executability of each batch-rule step; reachability (test runs and file contents only).
- Step 1 needed group pattern lists absent from this plan and lacked `mkdir -p` (PR-003).

### Step R3

- Checked: test modules only; scratch output under untracked `.aw/state/59aiyh/`; `aw commit qqaqw8`; no push. Not applicable beyond that.

### Step R4

- Checked: anti-regression (identical outcome lists, no weakened assertions), right-sizing (codemod runs over 3 to 4 modules with a 25-site hand stop), reuse, spec sync ("no spec change" is truthful).
- The census pattern misses 12 other-named record-text helpers and one module constant (PR-002).

### Step S5

- Checked: OQ-01 (resolved, non-blocking), supported by `7qxey9` F-41 and `59aiyh` E-09. No question needs the human. No finding is OPEN or DEFERRED.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | R1 references | plan V-01 "helper census of the E-09 `rg` pattern" | V-01 and V-02 cite an "E-09 `rg` pattern" this plan does not define (it is in `59aiyh` V-09 and `1bshrb` E-38). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Batch rule step 8 inlines it (recommendation strength: strong). |
| PR-002 | MEDIUM | UNDER-SCOPE | R4 D helpers | `tests/test_ipd_set_plan.py::_mk_set`, `tests/test_plan_readiness_recheck.py::_plan`, `tests/test_ipdrunner_runagy_shim.py::_CONFORMING_PLAN` | The census pattern misses record-text helpers and constants with other names; E-02 claimed no helper. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Step 8 adds the class; E-01 and E-02 name each one (recommendation strength: strong). |
| PR-003 | MEDIUM | IN-SCOPE | R2 executability | plan batch rule step 1 "re-derive its file list with the F-03 first-match partition" | Step 1 needed absent group pattern lists, lacked `mkdir -p`, and named non-matching context commits. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `mkdir -p` plus `rg -l` over the named modules (recommendation strength: strong). |
| PR-004 | LOW | IN-SCOPE | R2 cross-plan | `y3uowx` E-01 "`--dry-run [--format table\|json]`" | `--apply --format json` is not promised by the codemod plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fallback report; recommend `y3uowx` state it (recommendation strength: medium). |
| PR-005 | LOW | IN-SCOPE | G execution contract | plan gate "Lifecycle transition" | No hand `git mv` ban, conditional finalize ownership or narrow stop rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added (recommendation strength: strong). |
| PR-006 | LOW | IN-SCOPE | Proofreading requirement 7 | plan Step 0 "`artifact_meta.registry_fields(type)`" | `module.function` citations. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `path::Symbol` (recommendation strength: strong). |
| PR-007 | LOW | IN-SCOPE | Proofreading requirement 12(b) | plan batch rule | Branching process without a diagram. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Mermaid flowchart (recommendation strength: medium). |
| PR-008 | LOW | IN-SCOPE | S5 owner | plan OQ-01 "- Owner: none" | Resolved question with `Owner: none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `Owner: plan author` (recommendation strength: strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can this chunk run in any order relative to the other chunk plans? | Yes, as OQ-01 resolves. | Serialize them (rejected: disjoint modules). | `7qxey9` F-41; `59aiyh` E-09 | yes |
| D-2 | How does step 1 re-derive the file list? | `rg -l` with the F-01 pattern over the named modules. | Copy the group pattern lists (rejected: redundant). | plan batch rule; `7qxey9` F-41 | yes |
| D-3 | What if `--apply` refuses `--format json`? | Save the default report as `-codemod.txt`. | Stop the item (rejected: content, not format, is needed). | `y3uowx` E-01, E-03 | yes |
