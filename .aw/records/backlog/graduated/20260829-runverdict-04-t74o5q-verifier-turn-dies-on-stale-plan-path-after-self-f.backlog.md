- Id: t74o5q
- Status: graduated
- Blocks-Release: next
- Set: runverdict
- Priority: high
- Work-Kind: bug
- Summary: 40% of verifier turns never ran: self-finalize moves the plan pending/ -> executed/ before the verifier launches, the verify prompt still cites the pending/ path, and opencode exits instantly with 'File not found' leaving verification silently skipped

## Workflow history
- 2026-09-08 graduated (aw set): PARTIALLY graduated to plan fzxfph (runverdict-06); see the PARTIAL OBSOLESCENCE section appended to this item. NOT graduated as ALREADY FIXED: fix (1) and tests (a), (c), (d), all delivered by commit 1549c018 (2026-08-28 02:42 UTC), two days BEFORE this item was filed, with its regression test shipping in the same commit and passing today. All 23 measured failures are in runs created before that fix and zero post-fix runs contain one. NOT graduated deliberately: fix (2) (reorder the turn), because 1549c018 solved the same problem by re-resolution. GRADUATED: fixes (3) and (4) and test (b), both re-verified live: unverified is written for three distinct facts at three sites per host, and the except DriverError fallback still silently substitutes a known-stale path. Inherits Blocks-Release: next.
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

ROOT CAUSE (in-tree, verified): the verifier turn is handed a plan path that a PRECEDING step in the
same turn already invalidated. `aw ipd finalize` moves the plan `pending/` -> `executed/`, but the
verify prompt written before/around that move still names the `pending/` path, and `opencode run --file
<prompt>` then dies on the first line because the cited plan no longer exists there. The turn exits
non-zero having done nothing, and the runner records `verify_disp = "unverified"`
(`oc_runipd.py:2288-2292`) rather than treating a never-executed verification as a hard failure.

MEASURED (whole recorded fleet):
  verify session logs present            : 57
  verification outcome files written     : 34
  verify turns with NO outcome file      : 23   (40% of all verifier turns)
  every one of those 23 logs is < 200 bytes and contains ONLY:
    "Error: File not found: /.../.aw/records/plans/pending/<plan>-<id6>-<slug>.ipd.md"
  affected runs: run-20260825T035151Z-1236581 (13), run-20260828T002915Z-3129108 (7),
                 run-20260825T105819Z-1469310 (3)

CONFIRMED MECHANISM (g69y23, run-20260828T002915Z-3129108): the written verify prompt
`prompts/07-g69y23-verify-attempt-1.md:3` says
`Plan: /.../.aw/records/plans/pending/20260827-ipddeps-01-g69y23-...ipd.md`, and `state.json`
`configured_file` is that same `pending/` path. The plan is NOW at
`.aw/records/plans/executed/20260827-ipddeps-01-g69y23-...ipd.md`. So the path was correct when the
queue was built and stale by the time the verifier launched.

NOT A RESOLUTION-LOGIC DEFECT: `resolve_plan_path` (`oc_runipd.py:1198-1225`) is correct and
disposition-agnostic -- it resolves by id6 through `selectors.resolve_selectors` first, then falls back
to an `rglob` over all plan roots. Verified live: `selectors.resolve_selectors(Path('.'),'plans',['g69y23'])`
today returns the `executed/` path. The runner also re-resolves before building the prompt
(`oc_runipd.py:2229-2235`). The defect is that the resolved value is not what reaches the CHILD PROCESS:
the prompt text (and the `--file` argument set) carry a path captured earlier, and on `DriverError` the
code silently falls back to the stale `plan_path` (`:2233`) instead of failing loudly.

CONSEQUENCE (worse than wyw936): this does not corrupt a verdict, it SKIPS VERIFICATION ENTIRELY for
40% of the turns that were supposed to be verified, and the run record shows a benign-looking
`unverified` rather than "the audit never ran". Combined with wyw936 the picture is: verification either
did not run (t74o5q) or could not record a rejection (wyw936). Note the mitigating fact that
self-finalize is gated on `verify_disp == "verified"` (`oc_runipd.py:2309-2314`), so an `unverified` turn
does NOT auto-merge; the 5 spot-checked plans reached `executed/` via SEPARATE human-driven
`aw ipd finalize` commits (e.g. `08e22b1` g69y23, `71724de` iw793a), not runner auto-merge.

ORDERING NOTE: this is arguably the FIRST item of this Set to fix. wyw936's fail-open mapping is latent
(all 34 recorded verdicts are exactly 'VERIFIED', so it has never fired), whereas this defect has fired
23 times.

FIX SKETCH: (1) pass the plan to the verifier by STABLE ID, not by captured path -- let the verifier
resolve `id6` itself, the same way `resolve_plan_path` does, so a lifecycle move cannot invalidate the
prompt; or re-resolve immediately before launch and rewrite the prompt/argv from that value. (2) Order
the turn so verification happens BEFORE the plan is moved, or make the mover publish the new path back
into the item so downstream steps see it. (3) Distinguish "verification did not run" from "verification
ran and was inconclusive": a verifier that exits non-zero without writing its outcome file must be a
recorded hard failure (retried or fail-closed), never a quiet `unverified` that a human may read as a
minor caveat. (4) Fail loudly instead of falling back to a known-stale `plan_path` at `:2233`.

REPRO: run any `execute` item with `--self-finalize` (the default, `oc_runipd.py:1427`) through a
successful turn so the plan moves to `executed/`, then observe the verify turn's session log contain only
`Error: File not found: .../pending/<plan>.ipd.md`, no outcome file written, and
`verification_status: unverified` in `state.json`.

TEST: (a) a verifier turn launched after the plan moved to `executed/` still finds the plan and runs;
(b) a verifier that exits without writing its outcome file is recorded as a HARD failure, not
`unverified`; (c) the prompt/argv handed to the child cites a path that exists at launch time (assert on
the written prompt, not just the resolved variable); (d) a regression asserting the 23 historical cases
would now run: given a plan present only in `executed/`, prompt construction resolves it; (e) no silent
fallback to a stale `plan_path` -- an unresolvable plan refuses the verification.

RELATION: siblings wyw936 (verdict gate fails open), vlf75p (model/rate card unrecorded), rbftpl
(verifier evidence never consumed). Same class as y9lcem and the lanetruth Set: the runner's captured
model of the repo diverging from what the repo actually is. Here the divergence is a path the runner
itself invalidated mid-turn.

## PARTIAL OBSOLESCENCE, measured 2026-09-08 at HEAD 44d4950d during graduation

THIS ITEM'S HEADLINE DEFECT IS ALREADY FIXED AND ITS 23 MEASURED FAILURES CANNOT RECUR. The root
cause above (the verify prompt cites a `pending/` path that self-finalize already invalidated) was
fixed at commit `1549c018` "fix(runner): re-resolve current plan path before verification turn",
authored 2026-08-28 02:42 UTC. That commit re-resolves through `resolve_plan_path` immediately before
building the prompt AND passes the re-resolved value to the child launch, which is exactly what this
item says does not happen. Verified at HEAD: `oc_runipd.py:6373-6379` re-resolves and `:6396` passes
`current_plan_path` to `run_opencode`; the agy twin is `:3637-3643` and `:3660`.

THE FIX PREDATES THIS ITEM BY TWO DAYS. This item was filed 2026-08-30 02:02 UTC (commit `f4a1b5d8`).
All 23 failing turns are in three runs created 2026-08-25T03:51Z (13), 2026-08-25T10:58Z (3) and
2026-08-28T00:29Z (7), every one BEFORE the fix. Re-scanned all 135 run directories 2026-09-08: 57
verify session logs, 34 outcome files, 23 logs containing only the `File not found` error, and ZERO
such logs in any run created after `1549c018`.

CONSEQUENTLY NOT GRADUATED, because an existing commit already declares this work:
- FIX (1) (pass the plan by stable id / re-resolve before launch): delivered by `1549c018`.
- TEST (a) (a verifier launched after the plan moved still finds the plan): satisfied.
- TEST (c) (the prompt/argv cites a path that exists at launch): satisfied.
- TEST (d) (a regression proving the 23 historical cases would now run): ALREADY EXISTS and passes.
  It is `tests/test_oc_runipd.py::VerifierPromptTests::test_resolve_plan_path_handles_transition_to_executed`,
  shipped in the same commit as the fix; measured `1 passed` on 2026-09-08. Do NOT write a second one.

ALSO NOT GRADUATED, deliberately rather than as obsolete:
- FIX (2) (order the turn so verification precedes the plan move, or have the mover publish the new
  path back). `1549c018` solved the same problem by re-resolution, so reordering now would be a second
  solution to a solved problem and would reach into the `driver_begin`/`driver_finalize` transaction
  (`oc_runipd.py:894`, `:976`) with its own receipt and scope-reconciliation gates. If a future defect
  shows re-resolution is insufficient, reordering is the right response then.

WHAT WAS GRADUATED (plan `fzxfph`, runverdict-06): fixes (3) and (4) and test (b), each re-verified as
live at HEAD.
- FIX (3) survives: `verify_disp = "unverified"` is written for THREE materially different facts at
  three sites per host (`oc_runipd.py:6432` unparseable outcome JSON with nonzero exit, `:6434` no
  outcome file at all, `:6436` the turn raised KeyboardInterrupt/StallTimeout; agy `:3696`, `:3698`,
  `:3700`), with three different remedies and no way to tell them apart.
- FIX (4) survives verbatim: `except DriverError: current_plan_path = plan_path`
  (`oc_runipd.py:6376-6377`, agy `:3640-3641`) still SILENTLY substitutes a known-stale path when
  re-resolution fails. `1549c018` fixed the happy path and left the error path.

TWO OF THIS ITEM'S OWN STATEMENTS ARE NOW FALSE and are corrected here rather than left to mislead:
its "NOT A RESOLUTION-LOGIC DEFECT" paragraph claims "the resolved value is not what reaches the CHILD
PROCESS", which was true before `1549c018` and is false at HEAD; and its ORDERING NOTE advising that
this item be fixed first because it "fired 23 times" is obsolete, since it cannot fire again.
