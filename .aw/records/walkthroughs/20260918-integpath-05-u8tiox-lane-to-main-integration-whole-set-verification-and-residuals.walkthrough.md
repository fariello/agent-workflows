# Walkthrough: `integpath` whole-Set verification and residuals

- Date: 2026-09-18
- Kind: whole-Set verification and residuals record
- Id: u8tiox
- Target-Id: 3v7wo6
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Verified at: HEAD `36129255`

No `- Set:` line is declared here deliberately, and the reason is mechanical rather than stylistic.
`check.setid-collision` treats a setid as owned by ONE record type, and it skips `executed/` plans as
retired, so while this Set's plan is still in `pending/` a walkthrough declaring `- Set: integpath`
is reported as a cross-type collision with it (measured 2026-09-18, and it is why the existing
walkthroughs that DO carry `- Set:` all document plans already filed to `executed/`). The Set is
carried by the filename's setid slot and by `Target-Id:` above. Recorded as a finding, backlog
`sovauj`.

This is the record child 05 (`3v7wo6`) E-02 requires, written here because
`.aw/records/walkthroughs/` is the path its `Scope-Paths` declares for exactly this output. No
product code was authored for it. Its own id6 is `u8tiox`, minted fresh; the plan it documents is
linked by `Target-Id: 3v7wo6` above, never by the filename identity slot (DECISIONS.md D140).

## Summary

The Set's central claim holds. All four implementing children are in
`.aw/records/plans/executed/` (`29wvmj`, `6sb3yu`, `51vw4y`, `rl67b0`), and both measured incidents
were reproduced end to end and survived on BOTH hosts, in throwaway repositories, against synthetic
id6s. Forty six assertions passed and none failed.

One thing changed between review and execution and is worth reading before the residuals: the
startup dirty-base gate, which this plan expected to record as ABSENT, has LANDED. So it was
exercised rather than recorded missing.

One defect was found, and it is not in the Set: the runner exports `AW_EXECUTION_ROLE=worker` into
an execution turn, which makes 31 suite tests fail for reasons that have nothing to do with the plan
being executed. It is filed as backlog `1uq1cu` and is described at the end.

## What was verified, and how

The four children each test their own mechanism. That is not what this child does, and the
distinction is the reason this child exists. The failure the Set exists to prevent is an
INTERACTION: a refusal that used to be terminal, times a recovery route the executed-transition hook
used to block, times a resume that used to orphan the lane. So the verification drives each HOST's
own adapter end to end rather than the shared functions the children's tests bind directly.

Concretely, the children's `MeasuredIncidentsAreSurvivedTests` calls `integrate_lane_branch` and
stubs the suite with a passing callable. This verification instead calls
`retry_deferred_integrations` and `_integrate_stranded_lanes` on each host, in repositories that
carry a real passing test so the gate's own `run_suite_check` runs an ACTUAL suite. That difference
was not cosmetic: with no test file present pytest exits 5, the gate fails closed, and the
reproduction would have proven only that the gate fails closed.

### Incident one, both hosts: transient dirt defers and later integrates

`run-20260905T050043Z-639569` lost seven of 34 items to transient dirt. Reproduced with a verified,
finalized lane and a co-worker's uncommitted TRACKED edit to an overlapping path in main:

- attempt one DEFERS rather than going terminal, reaching status `integration-deferred`, which is
  absent from both hosts' `TERMINAL_STATES`, so a re-attempt remains possible;
- the lane branch is preserved and main is untouched, so nothing integrated over the contaminated
  base;
- the dirt then clears, and attempt two INTEGRATES, with the lane's work and its finalized plan both
  on main;
- no additional agent turn was spent (the item still carries exactly the one attempt record it began
  with), and no `--no-verify` appears anywhere in the resulting history.

### Incident two, both hosts: a resume integrates the first lane

`mm6wuz` accumulated `_attempt2` and `_attempt3` across resumes and cost a hand recovery. The
pre-fix behavior was MEASURED in the same repository rather than asserted from memory:
`allocate_worktree` really does return `aw/lane/<id6>_attempt2` displacing the first lane. That probe
branch was then removed, and the resume path integrated the FIRST lane with no turn dispatched,
leaving no `_attempt2` behind.

Every lane assertion ran inside a throwaway repository against the synthetic id6s `aa0001` and
`bb0002`. It was NOT run against `mm6wuz` in the working checkout, and that is deliberate: three
`aw/lane/mm6wuz*` branches still exist here as another party's preserved work, so the assertion
would report failure for pre-existing history, and the only way to make it pass would be deleting
someone else's lanes.

### The startup dirty-base gate: PRESENT, not absent

The plan predicted this would be absent and told the executor to re-run the grep rather than trust
the prediction. The grep now returns matches: `runner_shared.py:5232` declares
`--allow-dirty-base`, and both drivers read the frozen option. The owing plan `3i0aaz`
(`dirtybase-01`) is now `- Status: executed`. So the gate was exercised: a dirty SHARED tracked base
REFUSES, `--allow-dirty-base` converts that refusal into recorded CONSENT whose own message says the
consent does not waive the integration-time refusal, a clean base PROCEEDS, and the ISOLATED path
REPORTS rather than refusing.

## Residuals: what this Set deliberately did NOT close

Each residual is named by a child. Statuses below were read at execution time, and two have moved
since the plan was written.

1. CONTENT-BASED NARROWING of the dirty-overlap false-positive rate, meaning skipping the refusal
   when main's dirty version of a path is byte-identical to what the merge would produce. DECLINED by
   the maintainer on 2026-09-05 as low-value relative to the ladder. Still declined; no owner, and
   that is intentional rather than an oversight.

2. PATH-CATEGORY ALLOWLISTS, of the "docs are safe" or "review records are harmless" kind. REJECTED,
   not deferred, and the distinction matters: they reason about who probably wrote a file rather than
   whether it can conflict, which is the fail-open inference `d07nz2` prohibits. If the false
   positive rate is ever narrowed, narrow on CONTENT, never on category. A future reader who mistakes
   this for a deferral will reintroduce a rejected design.

3. `h1ksy6`, which fixes the same function the ladder guards but WIDENS its input set, making refusal
   MORE reachable. It must be RECONCILED with the ladder rather than stacked on it. MOVED SINCE
   REVIEW: it is now `- Status: graduated` (2026-09-08) to plan `fujm0y` (`mergedirty-01`), which is
   `- Status: approved` in `pending/`. So the reconciliation now has an owner and is live work rather
   than an unowned note.

4. `a8eufb`, which would let the runner tell its own dirt from a co-worker's. NECESSARY BUT NOT
   SUFFICIENT here, by construction: trailers mark COMMITS, while the motivating incident's dirt was
   130+ UNCOMMITTED working-tree files carrying no trailer at all. MOVED SINCE REVIEW: it is now
   `- Status: graduated` (2026-09-08) to plan `wao266` (`runtrailwire-01`, `- Status: approved`),
   narrowed to step (1) only.

## `76gsmv` is an ANSWERED question, not an open one

Child 01 resolved this on 2026-09-07 (its OQ-01, `Status: resolved`) and this record does not
re-open it. The cause is the finalize journal's LIFETIME, and nothing about git.
`_clear_finalize_journal` deletes the journal on successful completion
(`ipd_lifecycle.py:3988`, and on every rollback path), so it exists only between finalize and its
consumption. `76gsmv` merged 22 minutes before its three siblings and still happened to have one.

The backlog item's rename explanation is conclusively ruled out, and it was re-measured here rather
than restated from the plan: `git diff --name-status -M <merge>^1 <merge>` gives `R061`, `R063`,
`R061` and `R060` for the four merges, so all four are identical in diff shape. Four identical
shapes with two different outcomes cannot be explained by the shape.

`76gsmv` itself is `- Status: executed`.

## Sibling Sets this one does NOT cover

- `integearn` covers a lane whose integration was never ATTEMPTED because the earned-integration gate
  refused, which is a different failure from the four here. Its live members are `daexj1`
  (`integearn-03`, `- Status: approved`), `ys1dor` (`integearn-04`, `- Status: approved`) and
  `9lyg5h` (`integearn-05`, `- Status: approved`). CITE THOSE, not `32ij2j` and `xtklpd`, which are
  both `- Status: superseded` and are history.
- `scopeattr` (`hyx1dg`) and `depreview` (`yf9fj9`) came out of the same recovery sessions but are
  unrelated mechanisms. Both are BACKLOG ITEMS, not plans: `hyx1dg` is `graduated`, `yf9fj9` is
  `done`.
- `phawyy` is NOT a live sibling concern. It was RETRACTED and parked on 2026-09-07 as
  false-premised, because both blocked paths already persist the reason, and it is
  `- Status: parked` today. Listing it as live work would propagate a withdrawn claim.

## The rollup defect this child's existence is evidence of, still open

This child exists because an orchestrator cannot carry verification work. The runner-owned rollup
deliberately omits the `pre-transition` E/V checkpoint for an orchestrator, on the premise that an
orchestrator's items are performed by nobody, so work parked on a parent is marked complete having
never been performed or verified.

That is MEASURED, not predicted, and it is still true at this HEAD: orchestrator `84j8d7` sits in
`.aw/records/plans/executed/` with `- Status: executed` while carrying `Execution state: pending` on
its E-01 and `Result: pending` on its V-01. It was rollup-retired despite carrying an explicit
forceful warning against exactly that, which is the point: a warning addressed to a human does not
constrain a code path.

The GENERAL fix is still owed, as a separate backlog item against spec `77tr3o` R-5. Moving the two
items onto this child was the per-Set WORKAROUND, not that fix. Whether `84j8d7` needs a corrective
IPD for its unperformed E-01 and V-01 is a maintainer decision and is recorded here rather than acted
on.

## The defect this verification found: backlog `1uq1cu`

A bare `python3 -m pytest` inside a runner-launched execution turn reports 32 failures. The same
suite with one environment variable unset reports `1 failed, 7906 passed`, with no code change at
all. The runner exports `AW_EXECUTION_ROLE=worker` into the turn, and
`tests/test_worker_role_refusal.py:225` asserts that variable is not `worker`, with the docstring
"The DRIVER's own environment must never be worker-marked, or `driver_begin` would refuse". Tests
that spawn a driver subprocess inherit the marking, so `driver_begin` refuses inside the fixture; the
affected families are begin/finalize, worktree isolation, fail-closed integration and
backlog-close-in-lane, across five test files.

Why it matters beyond one turn: every plan's validation section tells its executor to run the bare
suite and judge the delta against a self-measured baseline. Inside a runner turn both measurements
carry the same 31 phantom failures, so the delta cancels and the check still passes; but an executor
who reads the 32 as real is misled into either excusing a genuine regression or reporting one that
does not exist.

It must NOT be fixed by relaxing `tests/test_worker_role_refusal.py`, which exists to catch a
worker-marked driver process and is correct as written.

The remaining single failure in the clean baseline
(`tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`)
is a `subprocess.TimeoutExpired` under parallel load and passes in isolation, so it is a
load-dependent flake rather than a code defect.

## A third defect, and it penalizes pasting real evidence: backlog `vnzm27`

This one refused the commit that carries this Set's verification, so it is worth stating plainly. The
`executed_transition_gate` pre-commit hook refused with "raw plan->executed transition (gained
`- Status: executed`) with NO matching finalize evidence", while the plan's own status was `approved`
throughout. What tripped it was PASTED EVIDENCE inside a fenced code block, quoting the four child
plans' real status output.

The cause is that `_has_executed_status` strips each line's indentation before comparing it to the
whole metadata line, and knows nothing about fenced blocks, so a quoted status line is
indistinguishable from a real one. That penalizes exactly the behavior the execution contract
demands, since a whole-Set verification plan's evidence is largely other artifacts' status lines.

The workaround was to reformat the evidence so the id6 and status print on one line, which is lossy:
the pasted output no longer matches the command a reader would re-run. The gate itself is correct and
was NOT bypassed; no `--no-verify` was used anywhere in this execution.

## A second, smaller defect: backlog `sovauj`

Writing this record surfaced one more, described in full in the item and summarized here because it
shaped this file's own front matter. `check.setid-collision` treats a setid as owned by exactly one
record type, and it skips `executed/` plans as retired. So a walkthrough that declares the Set of a
plan still sitting in `pending/` is reported as a cross-type collision, while the same declaration is
clean once that plan reaches `executed/`. The verdict depends on the subject plan's lifecycle
position rather than on anything about the walkthrough, which is why the existing walkthroughs that
carry a `- Set:` line do not trip it. The workaround here was to omit the field, which is lossy.

## Test results

Bare suite, measured the same way before and after (this child changes no product code, so the
after-minus-before failure set is empty by construction and was confirmed so by node id):
`1 failed, 7906 passed, 3 skipped, 2 xfailed`.

The two `slow` declaration suites, which a bare run cannot see, were run separately under `-m ''`:
`3 failed, 22 passed`. All three failures name exactly the same five pre-existing undeclared leaves
(`oc profile add`, `default`, `list`, `remove`, `show`), so the undeclared set did not grow. This
child adds no cli leaf.
