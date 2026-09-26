# Review: Restore the outcome tests of the deleted executed-transition gate end-to-end suite

- Subject-Id: 6vozur
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `f375e650`. The target plan was committed and unchanged, so the pre-review
snapshot was correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent`
reported `conforming` (exit 0) before review and `--phase review-finalize` exit 0 after the revisions.

EVERY ONE OF THE PLAN'S FOUR FINDINGS HOLDS, and I reproduced each rather than reading them.
`19313eed` is real and deleted the file (1267 lines, 3 classes, 6 test methods, all where the plan says
they are). I recovered it from `19313eed^`, placed it under `tests/`, and got `6 passed in 4.98s`
against today's POST-kecxnb hook, confirming F-1. F-4 reproduced exactly: under a `pytest_runtest_setup`
re-assert plugin the suite reports `1 failed, 5 passed in 3.44s`, failing on
`test_real_finalize_own_commit_passes_via_installed_hook` with
`AssertionError: 2 != 0 : AW-LIFECYCLE-ROLE-001 ... a worker-role process must not run them`. I then
applied the plan's exact E-02 remedy and got `6 passed` both with and without the plugin, so the
prescribed fix is correct and sufficient. I also independently audited F-3: there is no `inspect`,
`getsource`, `__doc__` or source-file read anywhere in the file, and the only three `read_text` calls
operate on plan fixtures the tests themselves wrote, so the outcome-only claim is true. Both path
assumptions in E-01 hold (`parents[1]` resolves to the repo root from `tests/`, and
`.pre-commit-config.yaml` is there). kecxnb is `executed`, so `Item-Dependencies: executed:kecxnb` is
satisfied, and the two files share no class or method name (12 passed when run together). This is a
well-measured plan and its diagnosis is sound.

THE REVIEW TURNED ON A MISTAKE I MADE MYSELF, WHICH IS WHY PR-701 IS THE FINDING THAT MATTERS. I first
restored the file as `tests/_probe_e2e_restore.py` to keep it out of the way, then ran the bare suite: it
reported `2436 passed, 1 skipped, 3 warnings in 40.16s`, fully green and IDENTICAL to the baseline I had
measured minutes earlier. All 6 restored tests had been silently uncollected, because pytest's default
`python_files` is `test_*.py` and `pyproject.toml` sets no override. Renaming to the plan's real target
name produced `2442 passed` (exactly +6). The plan's success criteria were "the file exists and imports
cleanly" (E-01) and "6 passed in each run; bare suite green" (E-03), and EVERY ONE of those is satisfied
by a file that contributes nothing to the suite: a directly-named run collects it regardless of the
default pattern, and "bare suite green" is true when the count never moved. For a plan whose entire
deliverable is regained coverage, that is the one failure mode that must be impossible to report as
success, so E-04 now requires a COUNT with the arithmetic shown. I am reporting this as a real finding
rather than as my own slip because the plan's stated criteria genuinely do not distinguish the two
cases; a careful executor could land a typo'd filename and honestly paste evidence satisfying every V
item as written.

PR-702 is a convention question the plan answered against the wrong axis. Its Scope check declines the
`slow` marker with "the file ran 6 tests in under 5s", but `pyproject.toml` defines that marker by KIND:
"heavy subprocess/integration tests (spawn the CLI, install into temp repos)". This file is 13
`subprocess.run` call sites driving real `git init`/`merge`/`commit` plus an installed pre-commit hook
that shells `python3 -m agent_workflows ipd-executed-gate`, which is that definition almost verbatim,
and `tests/test_completion.py`'s marked class carries the comment "The only test here that SPAWNS the
CLI, so it carries the `slow` marker". I did NOT decide this for the plan. Both answers are genuinely
defensible: the measured bare-suite delta (38.12/40.64/44.54s without vs 46.75/43.65/38.59s with) is
inside run-to-run noise, the original file carried no `pytestmark` before deletion so leaving it
unmarked restores the prior state, and marking it would pull these 6 tests out of the default suite that
every lane runs, which for a coverage restoration is a real cost. So it is now E-03 with the criterion
and every measurement supplied, recorded as OQ-02, and flagged in the gate as the one open choice a
human may want to overrule at approval. Leaving a genuine judgement to the executor with the evidence in
hand is better here than my picking one and burying the alternative.

PR-703 is a reproducibility defect in the verification recipe, with a trap attached. E-03 hardcoded
`/tmp/opencode/roleplug`, a machine-local path outside the executing workspace that an isolated lane may
not be able to write (I hit exactly that: my own tooling refused the path and I had to relocate the
plugin into the workspace). The trap is what an executor would do next. The obvious simplification,
`AW_EXECUTION_ROLE=worker python3 -m pytest`, reports `6 passed in 3.71s` against the UNFIXED file,
because `conftest.py` pops that variable at import time with a long comment explaining why. An executor
who simplified the recipe would therefore conclude F-4 was wrong and skip E-02 entirely, shipping the
role-inheriting test. E-05 now names the trap, states why only a post-scrub re-assert can observe the
condition, and points at the canonical plugin shape rather than inventing one.

PR-704 is a stale cross-reference in shipped code that I found while looking for that canonical shape.
`conftest.py` twice directs the reader to `tests/test_role_declaration_guard.py` as the harness proving
role-independence, and the SAME trim `19313eed` deleted that file (222 lines). So the comment cites a
file that does not exist, and the `_REASSERT_PLUGIN` and `PROTECTED_FILES` it documents survive only in
git history. I recorded it as F-8 and deliberately did NOT fix it: it is a different deleted file with
its own restoration decision, `conftest.py` is outside this plan's fence, and widening the fence to
chase it would be exactly the scope creep the fence exists to prevent. It is worth a human's attention
as a follow-up, and it is directly relevant here because this plan's own verification needs that shape.

ON RIGHT-SIZING: three items to five. Both additions answer questions the restore itself cannot (does
this file belong in the default suite; is it actually collected), and each has its own evidence surface,
so neither is a split for its own sake. The original three items' substance is intact.

Two things I checked and found correct, recorded so a later reader does not re-derive them. PyYAML is in
the `test` extra, so the config test's `import yaml` is satisfied (and the test passes at this HEAD, with
all three of its rows matching the live config). And OQ-01's answer to keep that test is right, though I
added the honest limit it was missing: it is the only test in the file reading the LIVE repository
config rather than a fixture, so it is the only one a change to that file can turn red - which is the
point, not a defect, and is not the `livecorpus` case (that marker concerns the `.aw/records/` tree, and
no test in the suite carries it today). The plan carries `- Work-Kind: followup` with no
`- Blocks-Release:`, which is correct: the gating set is `bug` alone, so no release gate is owed.

Baseline established for the executor: bare `python3 -m pytest` at this HEAD is `2436 passed, 1 skipped,
3 warnings in 41.67s`. With the restored file correctly named it is `2442 passed, 1 skipped`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | UNDER-SCOPE | E. Testing and verification / D. Anti-regression | Restored as `tests/_probe_e2e_restore.py`: bare `python3 -m pytest` -> `2436 passed, 1 skipped, 3 warnings in 40.16s`, identical to the baseline `2436 passed ... in 41.67s`, with all 6 tests uncollected. Renamed to `tests/test_executed_transition_gate_e2e.py` -> `2442 passed, 1 skipped in 43.99s` (+6). pytest default `python_files = test_*.py`; `pyproject.toml` sets no override | THE PLAN'S SUCCESS CRITERIA CANNOT DISTINGUISH A COMPLETED RESTORATION FROM ONE THAT RESTORED NOTHING. E-01 asks that the file "exists and imports cleanly" and E-03 that the "bare suite [is] green"; both are satisfied by a file pytest never collects, because a directly-named run collects it regardless of the default pattern and "green" is true when the count never moved. Since the plan's whole deliverable is regained coverage, the criterion must be a test COUNT. I hit this myself with a non-conforming probe filename and the suite reported fully green. | C:Low; U:Low; S:Low; F:High if unfixed (the deliverable silently absent); Overall:Low (the fix is a count assertion) | FIXED | Added E-04 requiring the bare-suite total BEFORE and AFTER with the arithmetic shown and a delta of exactly +6 (or the 6 shown under `-m slow` if E-03 marks the file), plus a `--collect-only` check; added V-04 with the same demand and an explicit statement that a green summary does not satisfy it; added F-5; Scope and Scope check now name the collection criterion; the honesty rule and a stop condition both name the false-pass. |
| PR-702 | MEDIUM | IN-SCOPE | C. Architecture and operability / F. Principles | `pyproject.toml` marker definition: "slow: heavy subprocess/integration tests (spawn the CLI, install into temp repos)". The file: 13 `subprocess.run` sites, real `git init`/`merge`/`commit`, installed hook shelling `python3 -m agent_workflows ipd-executed-gate`. Shipped users: `tests/test_cli.py`, `tests/test_installer.py`, `tests/test_leak_sanitizer.py` (file-wide `pytestmark`), `tests/test_completion.py` ("The only test here that SPAWNS the CLI, so it carries the `slow` marker"). Measured: file alone 3.71-5.21s; bare suite 38.12/40.64/44.54s without vs 46.75/43.65/38.59s with; original at `19313eed^` unmarked | THE `slow` DECISION WAS DISMISSED ON DURATION WHEN THE PROJECT'S CRITERION IS KIND. The Scope check reads "The `slow` marker is not added: the file ran 6 tests in under 5s", which answers a question the convention does not ask; by the stated criterion this file is the marker's paradigm case. The right outcome may still be to leave it unmarked, but the reasoning offered does not reach it, and an unexamined convention divergence in a test file is how a suite's fast/slow split erodes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-03 requiring the decision be MADE against the kind-based criterion and RECORDED with its reason in the module docstring and the Scope check, with every measurement supplied for both sides; added V-03 requiring the recorded reason and, if unmarked, that the criterion was answered rather than skipped; added F-6; recorded as OQ-02 (open, owner the executor) and surfaced in the gate as the one choice a human may overrule. Deliberately NOT decided by review: both answers are defensible on the evidence. |
| PR-703 | MEDIUM | IN-SCOPE | E. Testing and verification / G. Plan executability | E-03 as authored hardcodes `/tmp/opencode/roleplug/reassert_worker.py`. Measured: `AW_EXECUTION_ROLE=worker python3 -m pytest -o addopts="" <unfixed file>` -> `6 passed in 3.71s`; the same unfixed file under a `pytest_runtest_setup` re-assert -> `1 failed, 5 passed in 3.44s`. `conftest.py`: `os.environ.pop("AW_EXECUTION_ROLE", None)` at import, with the rationale above it | THE VERIFICATION RECIPE IS NOT REPRODUCIBLE AND ITS OBVIOUS SIMPLIFICATION SILENTLY LIES. The hardcoded path is machine-local and outside the executing workspace (my own run was refused it and had to relocate the plugin). Worse, an executor simplifying to a plain env-var export gets `6 passed` against the UNFIXED file, because the root conftest scrubs the variable before collection, and would then conclude F-4 was wrong and skip E-02 - shipping exactly the role-inheriting test this plan exists to make robust. The plan warned against neither. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now requires the plugin be written INSIDE the workspace, names the env-var spelling as a measured false pass with the `conftest.py` mechanism that causes it, and points at the canonical `_REASSERT_PLUGIN` shape (recoverable at `19313eed^`) instead of an ad-hoc one. V-02 now also requires the plugin run against the file WITHOUT the declarations, showing `1 failed, 5 passed`, so E-02 is proven load-bearing. Added F-7 and a honesty-rule clause. |
| PR-704 | LOW | OVER-SCOPE (recorded, not fixed) | F. Honest documentation | `git show 19313eed --stat` lists `tests/test_role_declaration_guard.py` at 222 deleted lines; `ls tests/test_role_declaration_guard.py` -> No such file; `conftest.py` cites it at its "CROSS-REFERENCE:" line and in its honest-limits paragraph; `git show 19313eed^:tests/test_role_declaration_guard.py` recovers it with `PROTECTED_FILES` and `_REASSERT_PLUGIN` | SHIPPED CODE POINTS AT A FILE THE SAME TRIM DELETED. `conftest.py` twice directs a reader to that harness as the proof of role-independence under both roles, and it no longer exists, so the canonical re-assert shape this plan's own verification needs survives only in git history. Relevant to this plan (it is the shape E-05 should reuse) but not this plan's to fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | DEFERRED | Recorded as F-8 with the recovery command, and named in Scope as explicitly OUT with the reason. Not fixed because it is a different deleted file with its own restoration decision and `conftest.py` is outside this plan's Scope-Paths; widening the fence to chase it is the scope creep the fence prevents. Deferral does not meet the Fix Bar on risk (the fix would be Low risk) but on SCOPE: it is over-scope for this plan, for which the workflow's stated default is removal or explicit deferral. Worth a follow-up item. |
| PR-705 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: one stop condition (a restored test failing against the post-kecxnb hook); `- Cohesion rationale: not required`; OQ-01 answered without stating the live-config coupling | THE GATE UNDER-STATED BOTH THE OPEN CHOICE AND THE FAILURE MODES. It named no cohesion rationale while the item count grew, did not tell a human that the `slow` question is unresolved (OQ-02) even though the answer changes which suite runs these tests, and carried no stop condition for the two measured false passes or for the one test that reads the LIVE `.pre-commit-config.yaml` and would tempt an executor to relax it to match a changed config. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate gained a cohesion rationale, a paragraph naming OQ-02 as the executor's open choice with the human's option to overrule at approval, a kecxnb-is-executed confirmation, an honesty rule naming both measured false passes, and three stop conditions (hook regression; live-config test failure with an explicit instruction not to relax it; an unexplained bare-suite delta). OQ-01 gained the live-config honest limit and a note that this is not the `livecorpus` case. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan claims the recovered suite passes against today's hook and that its role remedy works. Accept from the plan's pasted numbers, or reproduce? | Reproduce all four findings end to end: recover the file, run it, run it under a re-assert plugin, apply the E-02 remedy, re-run. | (a) Accept the plan's numbers - rejected: the plan was authored at a different HEAD (`61ef21d8` vs `f375e650`) and kecxnb has since landed and CHANGED the hook these tests exercise, so "still passes" needed re-measuring against the current hook, not the one the author saw. (b) Read the recovered file and reason about it - rejected: the role failure is an ambient-environment interaction that no amount of reading reveals. | `6 passed in 4.98s` against the post-kecxnb hook; `1 failed, 5 passed in 3.44s` under the re-assert plugin with the `AW-LIFECYCLE-ROLE-001` message; `6 passed` with and without the plugin after applying E-02 verbatim; 12 passed beside kecxnb's file | yes |
| D-2 | Should review DECIDE the `slow` marker question, or hand it to the executor with the evidence? | Hand it to the executor as E-03 plus OQ-02, with the criterion and every measurement supplied, and surface it in the gate for the human. | (a) Decide to mark it - rejected: it would pull 6 restored tests out of the default suite every lane runs, which partly defeats a coverage restoration, and the measured cost of keeping them is inside run-to-run noise. (b) Decide NOT to mark it and close the question - rejected: that is the plan's current answer reached by the wrong reasoning, and endorsing it would launder a duration argument into a kind-based convention. (c) Leave the plan's Scope-check sentence alone - rejected: an unexamined convention divergence is how the fast/slow split erodes, and the sentence as written would be read as having considered the rule. | `pyproject.toml` marker definition (kind, not duration); the four shipped users and `test_completion.py`'s "because it SPAWNS the CLI" comment; measured 3.71-5.21s alone and a bare-suite delta inside noise; the original file unmarked at `19313eed^` | yes |
| D-3 | PR-704 (`conftest.py` citing the deleted `test_role_declaration_guard.py`) is a real documentation defect. Fix it here, or record it? | Record it as F-8 and name it OUT of scope, pointing E-05 at the recoverable shape. | (a) Fix the `conftest.py` comment in this plan - rejected: `conftest.py` is outside `- Scope-Paths:` and the honest fix depends on whether that guard file is itself restored, which is a separate decision this plan has no mandate to make. (b) Add restoring `test_role_declaration_guard.py` to this plan - rejected as clear over-scope: it is a different 222-line file with its own outcome audit, and this plan's concern is one file. (c) Say nothing - rejected: the plan's own verification needs that file's plugin shape, so a reader will go looking for it and find it missing. | `19313eed --stat`; `ls` -> absent; `conftest.py`'s two references; `git show 19313eed^:tests/test_role_declaration_guard.py` recovers `PROTECTED_FILES` and `_REASSERT_PLUGIN` | yes |
