# Review: pin and stdin-deny the two nested aw launches in the release-readiness gates, child 5q924d (Set xzdudk)

- Subject-Id: 5q924d
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `735f2d5c`. `aw ipd lint --phase author --agent` reported `clean` BEFORE semantic review
and `--phase review-finalize --agent` after every revision. Every claim was re-measured by driving the
real `release_readiness` gates and the real pin helpers against temporary fixture trees, including a
scratch application of the proposed fix that was then reverted clean.

THE DIAGNOSIS IS CORRECT AND THE HEADLINE FINDING REPRODUCES EXACTLY. F-01: both launches are present
verbatim with `cwd=str(root)`, `capture_output`, `text`, `check=False` and nothing else. F-02: a
`subprocess.run` spy records `stdin` ABSENT and `env` ABSENT for both calls, with the trailing argv as
documented. F-03/F-04, the load-bearing pair: pointing the SHIPPED `gate_leak_scan` at a tree holding a
three-line decoy package returned `passed=True, detail='aw sanitize --agent exit 0',
evidence={'returncode': 0}` for a leak scan that never ran, and with the decoy exiting 42 both gates
returned `passed=False, evidence={'returncode': 42}`, so the verdict tracks the decoy in both directions.
That is a release gate reporting a clean scan it did not perform, and it fully justifies `Work-Kind: bug`
on its own merits rather than on the item's incidental-protection argument. F-06/F-07 hold: all three
named test files are gone and `grep` for `release_readiness` across `--include=*.py` returns nothing
outside the module itself, so the gates have zero coverage. F-08: no cycle, both import orders succeed,
`runner_shared` contains zero references to `release_readiness`. F-14 holds: no CLI verb reaches the
module and `docs/recovery.md:56` still tells a reader to run the deleted test. F-15 holds: five bare-argv
hits across three modules, and the `checkout_pin` exclusion is correct. The author's decision to upgrade
the item's own severity reasoning on measured evidence, and to refuse the item's unperformable third
instruction, are both exactly right.

FOUR FINDINGS CHANGE THE PLAN. Two are stale evidence that would send an executor chasing a failure that
no longer exists; one would make the plan's own headline test fail for the wrong reason; one is a
deterministic check the plan fails today.

FIRST, F-13'S BASELINE IS STALE IN BOTH DIRECTIONS AND WOULD ACTIVELY MISLEAD (PR-001). F-13 records
`1 failed, 2995 passed, 2 skipped` and names
`tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once` as an
expected pre-existing failure the executor must not attribute to this plan. Measured at this HEAD, 199
commits later: the bare suite is `3153 passed, 2 skipped` with ZERO failures, and that test file passes
`8 passed` on its own. The failure was fixed. This matters more than an ordinary stale number, because the
plan instructs the executor in three places (Required tests, V-03, and the execution gate) to EXPECT one
failure and not to stop for it. An executor following that instruction would treat a genuine new
regression as the known one. Fixed by de-pinning the count and inverting the instruction: measure your own
baseline, and treat ANY failure as yours to explain.

SECOND, E-01(a) AS WRITTEN CANNOT PASS AFTER E-02, FOR A REASON THE PLAN DID NOT MEASURE (PR-002). E-01(a)
requires asserting `evidence["returncode"] == 0` against a decoy tree built in `tmp_path`, on the premise
that a correct pin means "the REAL scanner ran" and therefore exits 0. I applied the exact E-02 change as
a scratch patch and ran it: `gate_leak_scan` returned `passed=False, evidence={'returncode': 2}`, because
the real scanner ran correctly and refused a non-git directory (`check-local-leaks: not a git repository or
git unavailable`). So the test would be RED both before AND after the fix, which is the one outcome that
makes a guard worthless, and the plan's own stated "MEASURED at this HEAD: this assertion FAILS with
`returncode == 42`, and after E-02 it passes" is false for `gate_leak_scan`. Adding `git init` to the
fixture makes it pass (measured: `passed=True, evidence={'returncode': 0}` for both gates). The cleaner
framing, which I also applied, is to assert the DECOY DID NOT RUN (`returncode != 42`) as the primary
property, since that is what the pin actually guarantees, with the exit-0 assertion kept only for the
git-initialised fixture. `gate_ipd_lint` happens to pass either way, which is precisely why the asymmetry
was easy to miss.

THIRD, F-05'S THIRD ROW IS WRONG, AND CORRECTING IT STRENGTHENS RATHER THAN WEAKENS THE TWO-PART PIN
ARGUMENT (PR-003). F-05 claims `-P` alone "ran the decoy (rc 42)". Measured: `-P` alone did NOT run the
decoy; it exited 0, because `-P` removes the cwd from `sys.path` and the import then resolved a DIFFERENT
`agent_workflows` entirely, the older pip-installed copy in site-packages
(`dev3925` against this lane's `dev5115`). So the accurate statement is worse for the naive fix and better
for the plan's conclusion: `-P` alone does not execute the decoy but it also does not execute the
RUNNER's own package, which is a silent wrong-version execution rather than a loud wrong-package one, and
is arguably harder to notice. Rows 1, 2 and 4 all reproduce exactly as written (plain `-m` -> decoy;
`PYTHONPATH` alone -> STILL the decoy, confirming the cwd entry precedes it; both helpers -> the real
lane copy). The plan's conclusion that BOTH halves are required is therefore correct and now rests on
correct evidence: `pinned_module_argv` supplies suppression, `pinned_child_env` supplies selection, and
each alone resolves the wrong code.

FOURTH, THE PLAN FAILS A DETERMINISTIC CHECK TODAY (PR-004). `check.ipd-carrier-finished-unverified` fires
against it: two deferred rows name `Carrier: 1bxw6o`, which reached `done`. The check's own recovery text
is explicit that `Carrier-Declined` is the WRONG repair here and that the row must cite
`- Carrier-Evidence:` instead. Worse than a bookkeeping nit: `1bxw6o` was closed with a maintainer ruling
that bears directly on this plan's OQ-01 ("retired by suite trim; we test outcomes and functionality,
never code structure or script text. Do not restore code-pinning guards."). That RULING strengthens OQ-01's
behavioral-only resolution from a reviewer's judgement to a maintainer's decision, and the plan should cite
it rather than treat the question as open policy. Both rows repaired with `Carrier-Evidence:` and OQ-01
now cites the ruling.

Things I checked and did NOT raise. The `-c` bootstrap claim in E-03 is correct (`pinned_module_argv`
contains `-c` and no `-m`), so the docstring correction E-03 mandates is genuinely required. E-01(b)'s
"ENDS with" phrasing is correct and necessary: after the pin, `argv[3:]` is no longer the trailing args
but `argv[-2:]` is, so a naive index-based assertion would have broken. `pinned_child_env` prepends the
runner root to `PYTHONPATH` and sets `AW_PIN_KEEP_ROOT`, matching the plan's description. The 3.9 floor
claim holds (`-P` is added only on 3.11+, inside the helper). `assert_child_tool_identity` in
`runner_shared` is an in-repo precedent using both helpers plus `stdin=subprocess.DEVNULL`, which the plan
could have cited but does not need to. F-09's import-cost reasoning and OQ-02's rejection of a lazy import
are both sound. The live gates returned byte-identical `GateResult`s under the scratch patch, confirming
F-12's no-semantic-change claim.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing; G. Executability | Measured `python3 -m pytest` bare -> `3153 passed, 2 skipped, 3 warnings`, zero failures; `python3 -m pytest tests/test_dependency_block_reporting.py -o addopts=""` -> `8 passed`; `git log --oneline d535ba56..HEAD \| wc -l` = 199 | F-13 pins `1 failed, 2995 passed, 2 skipped` and names a specific test as an expected pre-existing failure, and the plan instructs the executor in THREE places not to attribute it to this plan and not to stop for it. Both halves are stale: the count is wrong and the failure is FIXED. An executor following the instruction would misclassify a genuine new regression as the known one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-13 rewritten to record its numbers as a dated authoring snapshot with the re-measurement beside them; Required tests, V-03 and the execution gate now require the executor to measure their own baseline at execution HEAD and to treat ANY failure as theirs to explain rather than expecting a named one. The `1bxw6o` deferral row for that failure is withdrawn as discharged. |
| PR-002 | HIGH | IN-SCOPE | E. Testing; A. Correctness | Scratch-applied the exact E-02 change and ran E-01(a)'s assertion: `gate_leak_scan(<decoy tree>)` -> `passed=False, evidence={'returncode': 2}`, stderr `check-local-leaks: not a git repository or git unavailable`; with `git init` in the fixture -> `passed=True, evidence={'returncode': 0}` for both gates | E-01(a) asserts `evidence["returncode"] == 0` after the fix, and the plan states this was measured to pass. It does NOT for `gate_leak_scan`: the real scanner runs (so the pin works) and correctly exits 2 on a non-git `tmp_path`. The test would be RED before AND after E-02, the one outcome that makes a guard worthless. `gate_ipd_lint` passes either way, which is why the asymmetry was easy to miss. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01(a) now requires `git init` in the fixture AND makes the primary assertion "the decoy did NOT run" (`returncode != 42`), which is the property the pin actually guarantees, keeping the exit-0 assertion for the git-initialised tree. The false "measured ... after E-02 it passes" sentence is replaced with the actual measurement, and E-01's Expected outcome now says the guard must be red for the RIGHT reason. |
| PR-003 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy | Measured four-way probe at fixed cwd with a decoy present: plain `-m` -> DECOY (rc 42); `PYTHONPATH` only -> DECOY (rc 42); `-P` only -> rc 0 resolving an `agent_workflows/__init__.py` OUTSIDE this lane (the older pip-installed copy, version `dev3925`), i.e. NOT the decoy and NOT this lane's `dev5115`; both helpers -> the real lane copy | F-05 row 3 claims `-P` alone "ran the decoy (rc 42)". It did not: `-P` suppresses the cwd entry, so the decoy is avoided, but the import then resolves a DIFFERENT `agent_workflows` (site-packages). Rows 1, 2 and 4 reproduce exactly. The correction strengthens the plan's conclusion rather than weakening it, since a silent wrong-VERSION execution is harder to notice than a loud wrong-package one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 row 3 restated with the measured outcome and its implication; E-02's "BOTH HALVES ARE REQUIRED" paragraph and the execution gate's "DO NOT ADD ONLY `env=`" warning both updated so neither rests on the incorrect row; the four-way probe in Required tests now says what each variant must show. |
| PR-004 | MEDIUM | IN-SCOPE | G. Executability; project rule (`check.ipd-carrier-finished-unverified`) | `aw check` fires `check.ipd-carrier-finished-unverified` on this plan: "2 obligation(s) name a finished carrier needing verification: deferred row 1 ... deferred row 5 ... carrier 1bxw6o finished (done)"; the check's own recovery text forbids `Carrier-Declined` here; `1bxw6o`'s closing note is a maintainer ruling | Two deferred rows name `Carrier: 1bxw6o`, which is now `done`, so the plan fails a deterministic check. Beyond bookkeeping, `1bxw6o` closed with a maintainer ruling directly on OQ-01's subject ("we test outcomes and functionality, never code structure or script text. Do not restore code-pinning guards"), which the plan treats as an open policy question rather than a settled one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both rows now carry `- Carrier-Evidence:` citing the done item, as the check's recovery text prescribes; the structural-guard row keeps `Carrier: xvp5vx` for the audit half; the pre-existing-failure row is withdrawn entirely per PR-001. OQ-01 now cites the maintainer ruling, upgrading its resolution from reviewer judgement to settled policy. `aw check` re-run: zero findings for this plan. |

### Deferred and open

No finding is left `OPEN`, `DEFERRED`, or `REPLAN`, so `check.review-finding-unescalated` has nothing to
fire on and no `Blocking: yes` escalation is owed. The plan's own deferrals (the structural-guard rebuild,
the module's dead-code status, the other nine gates, the `docs/recovery.md` citation, the `checkout_pin`
prohibition, the gate-semantics prohibition) are the PLAN's and now carry conforming carrier fields.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-01(a) cannot assert exit 0 on a bare `tmp_path`. Fix the fixture, or change the assertion? | BOTH: `git init` the fixture AND make the primary assertion "the decoy did not run" (`returncode != 42`). | (a) Only `git init`, rejected as fragile: it makes the test depend on the leak scanner's git precondition, so an unrelated change to that precondition would break a test about pinning; (b) only changing the assertion, rejected because exit 0 is still worth pinning once the fixture is valid, and dropping it would let a future regression that breaks the scanner entirely pass; (c) asserting on the child's stdout marker, rejected because `capture_output` output is not surfaced through `GateResult`, so the test would have to re-implement the gate. | Measured under the scratch patch: non-git fixture -> `returncode 2` with `check-local-leaks: not a git repository or git unavailable`; `git init` fixture -> `returncode 0` for both gates; decoy-ran case -> `returncode 42`. | yes |
| D-2 | Is the two-part pin still justified once F-05 row 3 is corrected? | Yes, and more strongly. | Dropping to `-P` alone, rejected on the corrected measurement: it avoids the decoy but resolves the site-packages copy (`dev3925`) rather than the lane (`dev5115`), which is a silent wrong-version execution. Dropping to `PYTHONPATH` alone, rejected because it still runs the decoy (row 2 reproduced). | Four-way probe measured at review; `pinned_child_env` prepends the runner root and sets `AW_PIN_KEEP_ROOT`; `pinned_module_argv` adds `-P` on 3.11+ plus the `-c` bootstrap. | yes |
| D-3 | Does OQ-01's behavioral-only resolution survive review? | Yes, and it is upgraded from reviewer judgement to settled maintainer policy. | Re-opening it as a maintainer question, rejected because the maintainer already ruled, in the closing note of `1bxw6o`: "retired by suite trim; we test outcomes and functionality, never code structure or script text. Do not restore code-pinning guards." | `.aw/records/backlog/done/20260928-1bxw6o-...backlog.md` workflow history; `80db6750`'s deletion of 366 source-reading tests; AGENTS.md's own no-code-pinning-tests contract. | yes |
| D-4 | Should the stale `1bxw6o` pre-existing-failure deferral row be re-pointed or withdrawn? | Withdrawn. The obligation no longer exists. | Adding `Carrier-Evidence:` to it like the other row, rejected because the row's SUBJECT (a live suite failure to avoid misattributing) is measurably gone, so keeping the row in any form would preserve the misleading instruction PR-001 exists to remove. | Bare suite `3153 passed, 2 skipped`, zero failures; the named test passes `8 passed` standalone. | yes |
