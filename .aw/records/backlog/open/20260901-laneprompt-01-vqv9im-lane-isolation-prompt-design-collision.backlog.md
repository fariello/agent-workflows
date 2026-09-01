- Id: vqv9im
- Status: open
- Set: laneprompt
- Priority: high
- Work-Kind: bug
- Summary: Decide which lane-isolation prompt design survives: main's absolute-path exception vs qcqhj7's lane-relative contract, then re-scope or retire wtiso Phase 1

## Workflow history
- 2026-09-01 created (aw backlog): Filed after 6knsrx's E-01 stop condition FIRED during a phase-by-phase landing attempt: Phase 1's conflict surface differs from the plan's map AND one conflict is a competing design, not drift. Nothing was merged. Carries the maintainer's stated preference against absolute paths, the measured conflict counts, the y6mfgo evidence that the exception misleads agents in practice, and the five qyaime defenses main lacks that must be re-homed if Phase 1 is retired.

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
