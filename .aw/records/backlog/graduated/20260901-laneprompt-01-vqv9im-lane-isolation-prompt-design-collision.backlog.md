- Id: vqv9im
- Status: graduated
- Blocks-Release: next
- Set: laneprompt
- Priority: high
- Work-Kind: bug
- Summary: Decide which lane-isolation prompt design survives: main's absolute-path exception vs qcqhj7's lane-relative contract, then re-scope or retire wtiso Phase 1

## Workflow history
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the fix is not on main, so the item now carries Blocks-Release: next explicitly rather than relying on a successor plan to carry it.

DECIDE which lane-isolation prompt design survives, then re-scope or retire wtiso Phase 1
(`qcqhj7`). This blocks landing the rest of the `wtiso` stack; it does NOT block `i452hf`, which was
fixed independently on main by `cdef9c90`.

MAINTAINER PREFERENCE ALREADY RECORDED (2026-09-01, verbatim intent): "I have a strong preference to
not allow absolute paths if having them has any chance of confusing agents (e.g., we ask them to work
in an isolated worktree)." That points at the LANE-SIDE design. It is recorded here as a preference,
not yet as a decision, because acting on it means changing shipped main-side behavior and re-testing
it, which is the work this item exists to scope.

## The collision, measured

Both designs solve the SAME problem (an isolated agent must not be handed paths that make it reach
outside its lane), and they contradict each other on the one question that matters.

MAIN's design (shipped, live). `build_isolation_notice` + a `lane_root` parameter on `build_prompt`
(`agent_workflows/oc_runipd.py:3765`, `:3803`). It emits a "Work here" block naming the lane, and
then DELIBERATELY keeps absolute main-repo control paths in the prompt body, telling the agent they
are legitimate exceptions: "When a path below is given as an absolute path outside the lane, it is a
DRIVER-OWNED control path (the run directory, the outcome JSON, the decisions register); those are
the only exceptions and you write them exactly as given." The prompt then emits
`External run directory:`, `Decisions/questions register:`, `Required JSON outcome:` and
`Driver report:` as absolute paths.

LANE's design (`aw/lane/qcqhj7`, reviewed, unmerged). `lane_paths` + `lane_contract_text`
(`git show aw/lane/qcqhj7:agent_workflows/oc_runipd.py`, around `:703` and `:721`). EVERY
worker-facing path is lane-RELATIVE, and the contract forbids absolute paths outright: "Do NOT inspect
parent directories, the original checkout, other worktrees, or any absolute path outside this
directory, and do NOT request external-directory access. Use relative paths." A genuinely missing
input goes through a bounded `AW_MISSING_INPUT` repair cycle instead of an external-directory ask.

WHY THIS IS A DECISION AND NOT A MERGE. The two are not two halves of one feature; they are opposite
answers to "may an isolated worker ever see an absolute path?". Resolving the merge means choosing,
and then re-validating the loser's dependents. The maintainer's preference above favors the lane side
precisely because a stated exception is still an absolute path an agent can misread.

## Evidence that the absolute-path exception is risky in practice

Main's own docstring records the failure that motivated its notice (run
`run-20260831T153226Z-3424176`, plan `y6mfgo`): the driver allocated a lane and launched with
`--dir <lane>`, and the agent nonetheless read `../../../DECISIONS.md` and committed 18 files into
MAIN while the lane branch stayed at zero commits. That is an agent leaving its lane while being told
to stay in it, which is the exact confusion the maintainer's preference is about.

## What main LACKS that the lane also carries

Phase 1 is not only the prompt design; it bundles the rest of the qyaime deadlock defenses, and main
has NONE of them (measured on main at `cdef9c90`):

  * `external_directory` deny policy: 0 occurrences (the lane denies it AND `question` via
    `OPENCODE_CONFIG_CONTENT`).
  * `TurnBounds` (permission deadline + absolute per-turn deadline): 0 occurrences.
  * `is_meaningful_event` (so spinner noise cannot reset the no-progress bound): 0 occurrences.
  * `detect_permission_request`: 0 occurrences.
  * lane input manifest / `AW_MISSING_INPUT` classifier / preserve-on-ambiguity teardown: absent.

So retiring Phase 1 wholesale would DROP real, reviewed defenses. Whatever is decided about the
prompt, these should be re-homed rather than discarded.

## Conflict surface, measured 2026-09-01 (read-only `git merge-tree`, nothing mutated)

  * `qcqhj7` (Phase 1) vs main: 4 files, 14 hunks
    (`agy_runipd.py` 7, `oc_runipd.py` 5, `tests/test_oc_runipd.py` 1, `tests/test_wtiso_adversarial.py` 1)
  * whole stack `2c122z` vs main: 11 files, 38 hunks

NOTE a scope problem for `6knsrx` (see below): `tests/test_oc_runipd.py` now conflicts and is NOT in
that plan's `Scope-Paths`, which its OQ-04 widened to exactly four enumerated extra paths. This is a
fifth, so `6knsrx` cannot legally resolve Phase 1 as written.

## Consequence for approved plan `6knsrx`

`6knsrx` E-01 says: "If the surface differs from F-7's re-verified 6 paths / 26 hunks, STOP and report
rather than proceeding on a stale map." It differs (composition, and the out-of-fence test file), and
the difference is a design collision rather than drift. That stop condition FIRED and was honored:
nothing was merged. `6knsrx` needs re-scoping (or its Phase-1 step re-pointing) before it can execute.

## Options, not a recommendation

  1. LANE WINS (aligns with the stated preference): take `qcqhj7`'s lane-relative paths + contract,
     retire main's absolute-path exception, and move the driver's control paths inside the lane with
     harvest-back (the lane already implements `harvest_lane_submissions` for exactly this).
     Cost: changes shipped behavior; needs the harvest loop verified end to end.
  2. MAIN WINS: keep the exception, retire Phase 1's prompt half only, and re-home the qyaime
     defenses (deny policy, TurnBounds, meaningful-event gating, manifest, teardown preservation) into
     a fresh plan. Cost: leaves the `../../../` confusion class open.
  3. HYBRID: lane-relative paths for everything a worker WRITES, keeping main's "Work here" wording as
     the human-readable notice. Needs checking that no absolute path survives in the body.

## Explicitly not in scope here

Not `dh0uno` (inner `aw` resolving state against the lane worktree), not `xvx8ez` (queue ordering),
and not the rest of the `wtiso` stack beyond Phase 1. Landing `rchpms`'s remaining E-items (the
five-way retention classification, verified harvest gate, and `aw lane status/note`) is also NOT
covered by `cdef9c90`, which took only the two commits that own `i452hf`.

## Decision (2026-09-01)

DECIDED 2026-09-01 BY THE MAINTAINER: the LANE-SIDE design wins. An isolated worker is handed NO
absolute path outside its lane. Main's "these specific absolute paths are legitimate exceptions"
framing is retired.

## The measurement that settles it

Both designs were exercised directly, building a real isolated prompt from each side:

    MAIN  (build_isolation_notice + lane_root):  5 absolute paths OUTSIDE the lane
              <repo>/.aw/records/plans/pending/x.ipd.md
              <repo>/.aw/records/runs/run-x
              <repo>/.aw/records/runs/run-x/decisions-and-questions.md
              <repo>/.aw/records/runs/run-x/execution-report.md
              <repo>/.aw/records/runs/run-x/outcomes/01-aaaaaa.json

    LANE  (lane_paths + lane_contract_text):     0 absolute paths, of any kind

So this is not a close call on the stated criterion. Main tells the agent, in prose, that five
out-of-lane absolute paths are exceptions it must use verbatim; the lane design emits none, because
every worker-facing path is lane-relative and the driver harvests the results afterwards.

Supporting evidence that the exception misleads real agents, from MAIN's OWN docstring
(`oc_runipd.py:3765`): in run `run-20260831T153226Z-3424176` (plan `y6mfgo`) the driver allocated a
lane and launched with `--dir <lane>`, and the agent nonetheless read `../../../DECISIONS.md` and
committed 18 files into MAIN while the lane branch stayed at zero commits.

## What the decision does NOT mean

IT DOES NOT MEAN "merge `aw/lane/qcqhj7`". Measured: the lane was authored before a large amount of
main-side work and does not contain it. Reference counts in `oc_runipd.py`, main vs lane:

    runner_stop                 main 73   lane 0
    stall_progress              main  3   lane 0
    Statusline                  main  3   lane 0
    _apply_execution_profile    main  3   lane 0
    build_isolation_notice      main  2   lane 0
    build_recovery_lane_notice  main  2   lane 0

Taking the lane wholesale would destroy the entire `runstop` graceful-quit Set (six executed plans,
just verified in `zpbx7o`), the subagent progress poller, the statusline, and the hardened-profile
seam. That is not acceptable and is not what was decided.

THE RESOLUTION IS A PORT, NOT A MERGE: move the lane's PROMPT-ISOLATION design onto current main,
keeping every main-side mechanism intact.

## What must be ported (the lane's payload, measured)

The lane's Phase-1 section is ~516 lines and self-contained. Its parts, with reference counts on the
lane:

  * `LanePaths` / `lane_paths` (8 refs) - the lane-relative path set a worker is told to use, keyed by
    `run_id`/`id6` so a resumed run, a retry, and a co-resident lane never collide.
  * `lane_contract_text` (3 refs) - the prompt block stating this cwd is the COMPLETE authorized
    workspace, forbidding parent-directory and original-checkout access, and naming the one escape
    hatch.
  * `harvest_lane_submissions` (3 refs) - THE OTHER HALF OF THE LOOP, and the reason a naive port
    fails. A lane-relative INSTRUCTION alone is not enough: the worker writes
    `<lane>/.aw/lane/<run>/<id6>/submissions/outcome.json` while `reconcile_disposition` reads
    `<run_dir>/outcomes/<NN>-<id6>.json` in the main checkout. Both ends must move together, or a
    perfectly obedient worker's outcome is never found and the turn is scored from the empty-outcome
    fallback (the lane measured `reconcile_disposition -> ('partial', None)`), which then fails the
    `{executed, substantially-complete}` gate and silently never finalizes. The lane already wires the
    harvest immediately before `reconcile_disposition`, which is the correct seam.
  * `materialize_lane_inputs` + `input-manifest.json` (2 refs) - copy-only input materialization with a
    sealed digest manifest, never a symlink back to the original checkout.
  * `MISSING_INPUT_PREFIX` / `classify_missing_input` (3 + 1 refs) - the `AW_MISSING_INPUT` repair
    contract, resolved in COORDINATOR code, which never grants live original-checkout access. This is
    what makes "no absolute paths" survivable: a genuinely missing input becomes a bounded repair cycle
    instead of a permission deadlock.
  * `inventory_lane` (2 refs) - preserve-on-ambiguity before teardown.

## Also carried by the same lane, and NOT to be dropped

Main lacks all of these (each measured at 0 occurrences on main), and they are the rest of the qyaime
deadlock defense:

  * `external_directory: deny` + `question: deny` via `OPENCODE_CONFIG_CONTENT`, with an
    `observe_effective_permission_policy` read-back so the run cannot believe it is protected when a
    higher-precedence managed config overrode the deny.
  * `TurnBounds` - a seconds-scale permission deadline plus an absolute per-turn deadline.
  * `is_meaningful_event` - so spinner/heartbeat noise cannot reset the no-progress bound.
  * `detect_permission_request`.

Retiring Phase 1 without re-homing these would drop reviewed, tested work.

## Sequencing consequence for `6knsrx`

`6knsrx` (the landing plan) still cannot execute as written: its E-01 stop condition already fired
(surface differs, and `tests/test_oc_runipd.py` conflicts while sitting outside the `Scope-Paths` its
OQ-04 enumerated). This decision tells it WHAT to do but does not itself re-scope it. Phase 1 must be
re-authored as a port onto current main rather than a merge of the lane branch, and phases 3-5 then
rebase onto that.

## Honest limits of this decision

1. It is a DESIGN ruling plus a measurement, not an implementation. No code moved.
2. The port is real engineering, not conflict resolution: the lane's 516-line section must be
   reconciled with main's `Statusline`/poller/runstop turn loop, which is exactly where the 14-hunk
   phase-1 conflict lives.
3. Nothing here addresses `dh0uno` (inner `aw` resolving state against the lane worktree), which is a
   separate defect fixed by the unmerged `7p9n2v`.
