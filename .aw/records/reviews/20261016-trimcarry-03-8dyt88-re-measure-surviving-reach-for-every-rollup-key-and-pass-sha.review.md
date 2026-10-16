# Review findings: plan 8dyt88

- Subject-Id: 8dyt88
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `a85608c0f`. Plan committed and byte-identical to the lane
input (sha256 `9e446caf...`), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`.
Not an orchestrator.

Verified:
- `hpjj44` `## Triaged not mutated` holds 747 unique `production-key` rows (709 `cost-cap`, 38 `budget-exhausted`, every row with "exclusive lines") and 17 `test-file` rows. All 17 exist at `19313eed^` and are absent at HEAD.
- 12 of the backlog body's pass-shared names never existed in git history.
- `aw research new ... --order 1 --slug rollup-reach` (dry run) mints `20261016-trimcarry-01-<id6>-rollup-reach.findings.md`, which `ipd_lifecycle._scope_match` accepts against the Scope-Paths glob.
- `records/research/INDEX.json` is gitignored.
- A narrowed `replay_coverage_diff.py baseline` run printed every summary field E-02 names. Contexts use the module-level form `tests.<module>.<test>`.
- `run_diff` refuses a head mismatch and records `verdict` and `tests_count` per file.
- `tools/deleted_test_replay.py` uses a detached HEAD worktree and `git show <commit>^:<path>`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric D (silent false negative) | plan E-04 "a file with 0 exclusive lines is `shared-confirmed`"; `tools/replay_coverage_diff.py` `run_diff` record `verdict`, `tests_count`; `tools/deleted_test_replay.py` verdicts `error`/`error-import`/`error-collect`/`no-tests`/`timeout` | A replay that errors or runs no tests also yields 0 exclusive lines. Classifying it `shared-confirmed` would let Order 06 decline a file that was never measured (precedent: `hpjj44` measured `test_run_evidence_completion.py` as `error-collect` with 0 exclusive lines). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a first-rule class `replay-unverified`, which Order 06 must carry as a gap. E-04 outcome and V-04 updated. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric G (executability) | plan E-03 "`tests.<module>.<Class>.<test>` -> `tests/<module>.py`"; review baseline contexts `tests.test_agent_aw_home_containment.test_fail_open_on_symlink_error` | The plan described a 3-segment context name only, but module-level tests produce the 2-segment form. A parser written to the described shape would mis-derive the file that Order 05 uses as its probe selection. | all Low | FIXED | Derivation is now first-two-segments, checked against HEAD, and unmapped contexts are counted rather than dropped. V-03 requires that count. |
| PR-003 | LOW | UNDER-SCOPE | Rubric E (honest measurement limit) | `tools/replay_coverage_diff.py` `_build_pytest_cmd` `-m "not slow and not livecorpus"`; 26 `mark.slow` and 18 `mark.livecorpus` uses in `tests/*.py` | `unreached` could be read downstream as "no test reaches it", while slow and livecorpus tests are excluded. | all Low | FIXED | `## Method` must state the selection limit; V-03 requires the sentence. |
| PR-004 | LOW | IN-SCOPE | Rubric G (verification strength) | plan V-03 "three sample rows ... cross-checked against `baseline.json`" | `key-gone` cannot be checked against `baseline.json`, and "three" did not match "one per non-empty class" (up to four classes). | all Low | FIXED | V-03 now requires one sample per non-empty class, with `extract_functions` (or file absence) used for `key-gone`. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to class a pass-shared replay that did not run its tests? | New class `replay-unverified`, carried as a gap by Order 06. | Treat as `shared-confirmed` (REJECTED: unmeasured); treat as `exclusive-now` (REJECTED: conflates two causes). | `deleted_test_replay.py` verdict set; `hpjj44` `error-collect` precedent. | yes |
| D-2 | Include slow/livecorpus tests in the baseline? | No; document the limit. | Run them (REJECTED: the tool hard-codes the marker filter, and changing tools is out of scope). | `_build_pytest_cmd`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`. Cross-plan note: Order 06
(`z2xs98`) Scope lists `exclusive-now` gaps only. The new `replay-unverified` class is declared here
as a gap Order 06 must carry; when `z2xs98` is reviewed, its Scope should name it.
