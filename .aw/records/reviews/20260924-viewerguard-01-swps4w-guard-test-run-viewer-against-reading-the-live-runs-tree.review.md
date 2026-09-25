# Review: Guard test_run_viewer against reading the live runs tree

- Subject-Id: swps4w
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The plan was committed and unchanged, so the pre-review snapshot was correctly skipped per Step 1.
Structural preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) before review,
and `--phase review-finalize` reported `clean`, exit 0, ZERO findings after the revisions.

THIS IS A WELL-EVIDENCED PLAN AND ITS AUTHOR'S CLAIMS ALL HOLD. I re-derived each rather than trusting
the table, and every one reproduced. The module does zero live reads today: I synthesized a live
`.aw/records/runs/` tree in this checkout (the lane has none) and ran `tests/test_run_viewer.py` under an
audit-hook plugin recording any `open`/`os.scandir`/`os.listdir` under the guarded roots, getting `HITS 0`
and `26 passed` - which also confirms F-1's correction of the backlog item's stale "75 passed" figure.
F-2 is exact: `Path.is_dir`, `exists` and `stat` each emit NO audit event, `iterdir` emits `os.scandir`,
and a MISSING-path `open` or `iterdir` still emits its event, so the guard fires on real reads only while
still catching an attempt against an absent tree that gets past `is_dir`. F-3's rejection of
`monkeypatch.chdir` is sound. The audit-hook approach also has direct in-repo precedent the plan did not
claim: the root `conftest.py`'s own "Home isolation" defect was itself found with an audit hook, per its
comment block.

THE DOMINANT FINDING IS PR-601, AND IT IS THE ONE THING THAT WOULD HAVE MADE THIS GUARD DECORATIVE. The
plan's E-02 self-tests each CLEAR `_HITS` before returning - correctly, so the autouse fixture does not
fail the self-test - but the consequence is that the fixture never finds a hit, so `pytest.fail` never
runs, so the entire enforcement branch has no permanent test. I measured it rather than reasoning about
it: replacing `pytest.fail(...)` with `pass` in the prototype left both self-tests PASSING (`2 passed`),
and took the full prototype from `3 passed, 1 error` to `3 passed`. The only thing that caught the gutted
enforcement was the E-04 probe, which the plan deletes after one run by design. So as authored, the plan
ships a guard whose enforcement is proven once, locally, by an artifact that is then thrown away - and a
later refactor that breaks the failure path would be invisible to every future run. The fix has to use a
different mechanism, because an in-process test fundamentally cannot assert that its own teardown fixture
failed it; I prototyped a subprocess self-test that writes a throwaway module with a copy of the hook and
fixture, runs it under `pytest`, and asserts a nonzero exit plus the guard message. It passes, and when
the inner `pytest.fail` is replaced with `pass` it FAILS with `AssertionError` reporting the inner run's
`1 passed`. That is genuinely falsifiable, and it needs no live tree, so unlike E-04 it also protects the
guard in CI and in a lane worktree.

THE SECOND MATERIAL FINDING IS PR-602, and it is about honesty rather than correctness. The plan's Goal
says the guard makes a live-tree read "fail on the author's own machine", which is true, but the plan
elsewhere reads as though the guard closes the fresh-clone/CI hole its Concern describes. It does not. I
moved `.aw/records/runs/` aside and reran the real-read probe: `3 passed`, hook recorded nothing, because
`discover_run_dirs` gates every scan behind `r.is_dir()` and `is_dir` emits no audit event - directly,
`discover_run_dirs` returned `[]` with zero guarded hits. CI is a fresh `actions/checkout@v4` with no runs
tree, so the guard is inert there, as it is in every lane worktree. That is not a defect to repair: it is
the same condition that makes the underlying bug harmless in those environments, and the plan's Goal is
correctly aimed at the one box where the bug is both reproducible and invisible. But a reader who assumes
CI enforces this will stop looking for the regression, which is exactly the false-confidence failure this
plan exists to prevent. It is now stated in the Goal, in F-5, and in the E-01 comment block the plan
requires.

TWO SMALLER CORRECTNESS ITEMS I would not have caught without running the thing. PR-603: the fixture must
clear `_HITS` BEFORE calling `pytest.fail`, not after, or the recorded hit survives into the next test in
the same xdist worker and fails it too, reporting the wrong test as the offender - a debugging detour on a
guard whose whole value is naming the culprit. PR-604: the plan says to add `import os, sys, pytest` "as
needed", which understates it - measured, the module imports NONE of the three today (it has `argparse`,
`io`, `json`, `tempfile`, `contextlib`, `datetime`, `pathlib`, `typing`, `unittest`), so all three are new;
`pytest` is already imported by sibling modules including `tests/test_cli.py` and `tests/test_installer.py`,
so it adds no dependency, but "as needed" invites an executor to check and find nothing and wonder.

PR-605 is a gap in the plan's own falsification story for the environment it will most likely execute in.
E-04 says a worktree with no live tree "cannot show the failure ... In that case also create
`_REPO/.aw/records/runs/run-probe/`", which is right, but it stops short of the cleanup evidence that
matters: the runs path is gitignored (verified: `.aw/.gitignore:14 records/runs/`), so a synthesized
directory left behind would NOT appear in `git status`, and the plan's stated outcome checks
`git status --short`. The item and V-04 now require a filesystem check.

PR-606 is right-sizing plus two assertions the plan inherited from a prototype rather than demonstrating.
E-02/E-04 both run with `-p no:randomly`, which deliberately disables the ordering randomization the real
suite uses, and the guard keeps module-level mutable state (`_HITS`, `_ARMED`) shared across every test in
a worker - the classic shape for an order-dependent flake. My prototype was stable across xdist and five
random seeds, and the hook's overhead was indistinguishable from zero (a disarmed hook cost 1.00x on a
3,000-file write-and-read loop: 320.5ms against 319.6ms), but the plan should show that on the real module.
Added as E-05.

ONE THING I CHECKED AND FOUND FINE, recorded so it is not re-litigated. `_LIVE_RUN_ROOTS` is computed at
module import from `runner_shared.state_root`, which resolves through `resolve_project_context`, so it
depends on the repo's records backend: `repository` gives `<repo>/.aw/records/runs`, `companion` gives
`<repo>.aw/records/runs`, and `home` gives a path under the developer's real `~/.aw/projects/<id>/`. The
root conftest sandboxes `AW_HOME` before test modules import, which I expected might redirect this - it
does not, because the backend comes from the repo's own `project.json` (verified: same in-repo path before
and after sandboxing). Guarding the external home path under a `home` backend is arguably more valuable
than guarding the in-repo one. Import cost is one-off at 23.1ms. Recorded as F-7.

The plan's `Deferred` rows both carry `Carrier-Declined` reasons and `evaluate_durable_carrier` returns
zero findings for this plan, so nothing here starts from a dirty baseline. OQ-01 was already `resolved`
with a sound rationale and needed no change. Backlog `rcmbnb` is `graduated`, `Work-Kind: chore`, and
carries no `- Blocks-Release:`, so the every-live-bug-gates-the-release rule does not apply and no gate
handoff is owed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | UNDER-SCOPE | E. Testing and verification | Original E-02 clears `_HITS` before returning, by design; measured at review: replacing `pytest.fail(...)` with `pass` left both self-tests PASSING (`2 passed`) and took the full prototype from `3 passed, 1 error` to `3 passed`; the only artifact that caught it was E-04's probe, which the plan deletes after one run | THE GUARD'S ENFORCEMENT BRANCH HAS NO PERMANENT TEST, so the plan ships something that can silently become decorative. Because each self-test clears `_HITS`, the autouse fixture never finds a hit and `pytest.fail` never executes; nothing in the committed suite distinguishes a guard that fails a violating test from one whose failure path was refactored away. The plan's own Goal demands the guard "must be provably falsifiable", and after E-04's probe is deleted it no longer is. An in-process test CANNOT close this, because a test cannot assert that its own teardown fixture failed it - so this needs a different mechanism, not a tweak. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (the mechanism was prototyped at review and works; it is one self-contained test) | FIXED | Added F-6 with both measurements. Added E-03: a subprocess self-test that writes a throwaway module carrying a copy of the hook and fixture, runs it under `pytest` with `-o addopts=` and `cwd=td` (so the parent's `-n auto` does not nest and the inner run cannot pick up this repo's conftest), and asserts a nonzero returncode plus the guard message. Prototyped at review: passes as written, and FAILS (`AssertionError`, inner `1 passed`) when the copied `pytest.fail` is gutted. V-03 requires that falsification to be performed and pasted, and says a passing run alone does not satisfy the item. E-02 now states plainly what it does not prove, with the measurement, so the two items are not later merged. |
| PR-602 | MEDIUM | IN-SCOPE | F. Honest documentation / G. Plan executability | Measured at review: with `.aw/records/runs/` moved aside, a probe calling `run_viewer.discover_run_dirs(_REPO)` under the guard reported `3 passed` with zero recorded hits; `discover_run_dirs` returned `[]`; `run_viewer.discover_run_dirs` gates each scan behind `r.is_dir()` and `is_dir` emits no audit event (F-2); `.github/workflows/tests.yml` uses `actions/checkout@v4` | THE PLAN LETS A READER BELIEVE IT CLOSES A HOLE IT DOES NOT CLOSE. Its Concern is that a live-tree-reading test "fails in a fresh clone, in CI, and in a lane worktree", and it then builds a guard that is INERT in exactly those three environments, because an absent root is never scanned past `is_dir`. The Goal's own wording ("fail on the author's own machine") is correct and the design is the right one - the author's box is the only place the bug is both live and invisible - but nowhere did the plan state that CI gains nothing. That matters because false confidence in a guard is the same failure class the plan exists to prevent: a maintainer who believes CI enforces this stops watching for the regression. | C:Low; U:Low; S:Low; F:Low; Overall:Low (a stated limit, not a code change) | FIXED | Added F-5 with the measurement. Added an explicit HONEST REACH paragraph to the Goal stating that the guard buys author-side detection and not a CI gate, and that this is a property of the bug's own harmlessness where no tree exists rather than a defect. E-01(d) now requires the same limit in the committed comment block, and V-01 requires that sentence be quoted in the evidence so it cannot be dropped during execution. The gate's what-a-human-is-approving paragraph names it too. |
| PR-603 | MEDIUM | IN-SCOPE | A. Correctness | Original E-01(c): "clears the module list `_HITS`, arms, yields, disarms, and then calls `pytest.fail(...)` if anything was recorded" - no clear on the failing path; `_HITS` is module-level state shared by every test in an xdist worker | A RECORDED HIT LEAKS INTO THE NEXT TEST AND BLAMES THE WRONG ONE. The fixture clears `_HITS` on ENTRY, so if it fails a test without clearing on the way out, the surviving entry is still present when the next test's fixture runs - it clears at setup, so the immediate next test is fine, but any path that fails before that clear (or a future refactor moving the clear) reports a stale path. More concretely, the message is built from `_HITS[0]`, so a test that triggers several hits plus a later one that triggers none can produce a failure naming the earlier test's path. On a guard whose entire value is telling the author WHICH test reintroduced the dependency, naming the wrong one is a debugging detour that erodes trust in the guard itself. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01(c) now specifies clearing `_HITS` BEFORE calling `pytest.fail`, with the reason stated. V-01 requires the diff to show that ordering explicitly, so it is checked rather than assumed. |
| PR-604 | LOW | IN-SCOPE | G. Plan executability | Original E-01(c): "Add `import os, sys, pytest` as needed"; measured: `tests/test_run_viewer.py` imports `argparse`, `io`, `json`, `tempfile`, `contextlib`, `datetime`, `pathlib`, `typing`, `unittest` and none of `os`/`sys`/`pytest`; `pytest` is imported by `tests/test_cli.py`, `tests/test_installer.py`, `tests/test_completion.py` and others | "AS NEEDED" UNDERSTATES A FACT THE EXECUTOR WILL HAVE TO ESTABLISH ANYWAY. All three imports are new to this module, and one of them (`pytest`) is the first pytest import in a file that is otherwise pure `unittest.TestCase` - which looks like a design change worth questioning until you know sibling modules already do it. The vague phrasing costs a verification step and invites an executor to wonder whether introducing `pytest` here is intended. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01(c) now states all three are new, lists what the module currently imports, and records that `pytest` is already established in sibling test modules so it introduces no new dependency. |
| PR-605 | LOW | UNDER-SCOPE | E. Testing (evidence sufficiency) | Original E-04 expected outcome: "`git status --short tests/test_run_viewer.py` shows only the E-01/E-02 diff"; measured: `git check-ignore -v .aw/records/runs/.../state.json` -> `.aw/.gitignore:14 records/runs/`; this lane has NO live runs tree, so the synthesize-then-remove path is the one that will actually execute | THE CLEANUP CHECK CANNOT DETECT THE THING IT IS CHECKING FOR. E-04 tells an executor with no live tree to synthesize `.aw/records/runs/run-probe/`, and then verifies cleanliness with `git status`. The runs path is gitignored, so a synthesized directory left behind is invisible to git and the check passes over a dirty tree. This is the likely path rather than an edge case: any lane worktree, and this review's own lane, has no live tree. Leaving a stray run dir behind would then pollute later `aw runs` output on that checkout. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires the synthesized directory be removed and confirmed on the FILESYSTEM, stating that the path is gitignored so git would look clean either way. V-04 requires the filesystem check to be pasted and says `git status` alone is not sufficient evidence for this item. |
| PR-606 | MEDIUM | UNDER-SCOPE | G. Right-sizing / E. Testing | Original plan had 4 items; E-02 and E-04 both specify `-p no:randomly`, which disables the `pytest-randomly` the suite's configured `addopts` enables; `_HITS`/`_ARMED` are module-level mutable state shared across a worker's tests; review measured the prototype stable across xdist and 5 seeds, and a disarmed hook at 1.00x (320.5ms vs 319.6ms on a 3,000-file loop) | THE PLAN NEVER EXERCISES THE CONDITIONS THE SUITE ACTUALLY RUNS UNDER, and it keeps shared mutable state - the classic order-dependent-flake shape. Both targeted runs pin `-p no:randomly`, so nothing in the plan demonstrates behavior under the randomized ordering and `-n auto` worksteal that a bare `python3 -m pytest` uses; the only such run is E-06, where a flake would surface as an unexplained failure in a 2,000-test suite rather than as a diagnosed one. Separately, the plan inherited its stability and overhead expectations from a prototype without showing them on the real module. | C:Low; U:Low; S:Low; F:Low; Overall:Low (one added item running an existing command three times) | FIXED | Added E-05: three bare `python3 -m pytest tests/test_run_viewer.py` runs (so the configured `-n auto --dist=worksteal` and randomization both apply), requiring the same pass count with no order-dependent failure, and carrying the review's measured overhead figure so a large slowdown reads as a mistake rather than an inherent cost. V-05 requires all three summary lines and the explicit pass count (26 collected at review). Plan is now 6 items with a 6:6 E/V bijection; `Highest E allocated` corrected 04 -> 06; cohesion rationale rewritten to state that six items are still one concern. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The guard's enforcement branch has no permanent test (PR-601). What mechanism closes that, given an in-process test cannot assert its own fixture failed it? | A subprocess self-test that generates a throwaway module carrying a copy of the hook plus fixture, runs it under `pytest`, and asserts a nonzero exit and the guard message. Added as E-03. | (a) Assert inside the same process with `pytest`'s internal hooks or a `pytest_runtest_makereport` interception - rejected: it couples a test to pytest internals and would itself be untested; the failure is produced in teardown, which the failing test cannot observe. (b) Use `pytester`/`testdir` - considered and NOT chosen: it is the idiomatic tool, but it requires the `pytester` plugin be enabled and shifts the module from plain `unittest.TestCase` to a pytest-fixture-consuming style, a larger change to a 1,963-line file than a `subprocess.run` call; the subprocess form was prototyped working, so it is preferred on smallest-correct-change grounds. This is a judgement call another reviewer could reasonably decide the other way. (c) Accept E-04's one-shot probe as sufficient - rejected on the measurement: it is deleted after one run, so nothing protects the guard thereafter. | Measured: gutting `pytest.fail` left both E-02 self-tests green; the prototyped subprocess test passes and fails correctly when the inner `pytest.fail` is gutted | yes |
| D-2 | The guard is inert where no live runs tree exists, so it never fires in CI. Is that a defect to fix in this plan, or a limit to state? | A limit to state, in three places (Goal, F-5, and the committed comment block). The design is unchanged. | (a) Make the guard fail on any RESOLUTION of a live run root, not just a read (for example by wrapping `state_root` or asserting no test passes `_REPO` as a root) - rejected: it would fire on the six existing harmless `Path(".")` call sites and on legitimate path arithmetic, which is the noisy-grep-guard failure the backlog item explicitly warns will get the guard disabled. (b) Have the guard synthesize a run directory so a read always has something to hit - rejected: a test-time side effect that writes into the developer's real records tree, to make a guard fire, is worse than the gap. (c) Say nothing, since the Goal already scopes itself to the author's machine - rejected: the Concern section describes the CI failure mode at length, so silence reads as a claim. | Measured: `discover_run_dirs(_REPO)` with the tree absent returned `[]` with zero recorded hits; `is_dir` emits no audit event; backlog `rcmbnb` names noisiness as the thing that would get a guard disabled | yes |
| D-3 | Should the review widen the guard to the root `conftest.py` while it is here, given the technique's precedent there? | No. Left Deferred exactly as the plan has it. | (a) Widen now - rejected: other modules have not been audited for legitimate reads of the checkout's own `.aw/records/`, so a suite-wide hook risks false positives across a 2,000-test suite, and the backlog item explicitly scopes the ask to this module ("it protects this module, not every future test"). (b) File a new backlog item for the widening - not done: the plan's Deferred row already declines it with a condition ("file a backlog item only if a second module turns out to have the same hazard"), which is a reasonable trigger rather than an open obligation, and `evaluate_durable_carrier` accepts the declined row. | Backlog `rcmbnb` scope sentence; plan Deferred row with `Carrier-Declined`; `evaluate_durable_carrier` returns 0 findings for this plan | yes |
| D-4 | `_LIVE_RUN_ROOTS` resolves through `state_root`, so under a `home` backend it guards a path in the developer's real home rather than in the checkout. Constrain it to the repo? | No. Leave it resolving through `state_root`, and record the behavior. | (a) Restrict the guarded set to paths under `_REPO` - rejected: a test reading the developer's real `~/.aw/projects/<id>/records/runs` is at least as bad as one reading the in-repo tree, so narrowing would remove coverage the plan gets for free. (b) Drop `state_root` and hardcode the three in-repo paths - rejected: it would miss a non-`repository` backend entirely, which is the case the plan's E-01 deliberately covers. | Measured: `state_root` returns `<repo>/.aw/records/runs` for `repository`, `<repo>.aw/records/runs` for `companion`, and `~/.aw/projects/<id>/records/runs` for `home`; the root conftest's `AW_HOME` sandbox does not perturb it because the backend comes from the repo's `project.json` | yes |

## Round 1 escalation

No finding was left `OPEN` or `DEFERRED` - all six are `FIXED` - so no `- Blocking: yes` question was
owed under Step 4's escalation rule. No decision is recorded `Reversible: no`: each of D-1 through D-4 is
undoable by editing one test file or one plan section, and none publishes an interface, migrates data, or
deletes anything. D-1 is the closest call and is flagged in its own row as a judgement another reviewer
could decide the other way (`pytester` versus `subprocess`); it is recorded rather than escalated because
choosing the other mechanism later costs a rewrite of one self-test.
