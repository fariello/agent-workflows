# Review findings: plan 3nczai

- Subject-Id: 3nczai
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the lane input and committed unchanged (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan; Set `6i9viq`; `- Blocks-Release: next` inherited from backlog `6i9viq` (graduated).

Verified:
- `tests/test_clean_target_config_home.py` method `test_case_l_tracked_install_still_writes_target` at HEAD already carries the derived assertions (`commit_paths == tracked_paths`, non-empty, `AGENTS.md`, `.aw/.gitignore`, empty `git status --porcelain`) and no literal count. They were landed by commit 84cba788c ("fix(ci): derive test_case_l expectation and declare Carrier-Declined in pending plans"), an ancestor of HEAD, which also touched this plan file (adding the two `Carrier-Declined` lines) but did not execute it.
- `python3 -m pytest -o addopts="" -q tests/test_clean_target_config_home.py -k test_case_l`: `1 passed, 22 deselected in 3.50s`.
- `grep -rn "files changed" tests/` finds only `tests/test_status_set.py:695` (unrelated comment).
- Backlog `ioegmo` is graduated to pending plan `im4afa`, which targets the same already-fixed line.
- A mutation probe for the sensitivity claim was attempted at review and refused by the lane sandbox; it was not run. By reading: a stray untracked file leaves `commit_paths == tracked_paths` true, so only the porcelain assertion detects it, which is why E-02 now demands both variants.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Executability (stale premise) | `git show 84cba788c -- tests/test_clean_target_config_home.py`; method lines 566-595 at HEAD | E-01 instructed removing a `"358 files changed"` literal that no longer exists; V-01 demanded a `git diff` showing that removal, which is unsatisfiable, and an executor would either refuse or fabricate. | all Low | FIXED | Scope, E-01, F1/F3 (new F6) and V-01 rewritten: E-01 confirms the landed assertions match the specification and edits only on divergence; V-01 cites the landed commit. |
| PR-002 | MEDIUM | IN-SCOPE | Testing (sensitivity) | 84cba788c records no mutation run; old E-02 mutation targeted only a partial commit | The landed change was never shown to be non-vacuous, and the single proposed mutation does not exercise the clean-status assertion independently. | all Low | FIXED | E-02 now demands two mutations (partial commit -> set equality fails; stray file -> only porcelain fails) with exact insertions and revert command; V-02 demands each `AssertionError`. |
| PR-003 | LOW | IN-SCOPE | Executability (lifecycle and scope fence) | Gate "move the plan to `executed/` through the tooled lifecycle"; Scope-Paths declares a file likely left unmodified | Lifecycle ownership was unstated, and finalize would refuse a declared-but-unmodified path without `--scope-ack`. | all Low | FIXED | Gate states runner vs `aw ipd finalize 3nczai` ownership, the `--scope-ack` case, never hand `git mv`, and the inherited release gate; commit command names the plan id. |
| PR-004 | LOW | IN-SCOPE | Process | Required tests and V-items used `-o addopts="" -q`; Deferred note on `ioegmo` | Redundant `-q`; the duplicate plan `im4afa` is equally stale and was not mentioned. | all Low | FIXED | `-q` removed; Deferred note names `im4afa` as stale for the maintainer. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Retire the plan as superseded by 84cba788c, or keep it to verify? | Keep it, rescoped to verification plus the missing sensitivity proof. | Retire to `superseded/` (REJECTED: the release-gated item `6i9viq` would lose its carrier and the fix would ship unproven). | AGENTS.md close-legitimacy rule (HANDOFF needs an executed carrier); GUIDING_PRINCIPLES P16 mutation bullet. | yes |
| D-2 | Touch backlog `ioegmo` / plan `im4afa`? | No; flagged for the maintainer. | Retire `im4afa` here (REJECTED: outside this review's ledger). | plan-review Step 0.1 scope ledger. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
