# IPD: Split the run surface into two nouns: aw run writes, aw runs reads

- Date: 2026-08-29
- Kind: child
- Concern: `aw run list` and `aw runs` are byte-identical duplicates, and the noun `aw run` is misleading because most of what it holds only INSPECTS past runs rather than running anything. RE-SCOPED BY MAINTAINER RULING 2026-08-31 (OQ-03): rather than retiring `aw run`, split the surface BY DIRECTION into two nouns - `aw run` WRITES (`start`, `record`, `cancel`, `finalize`, and later the `runprofile` Set's `aw run as <profile>` dispatch), `aw runs` READS (the nine read-only viewers). The original "retire the noun" framing is preserved in the history below.
- Scope: The CLI naming surface only: the `run` parser group in `agent_workflows/cli.py`, the dispatch in `agent_workflows/run_cli.py`, the `command_surface` declarations, the tests that invoke the verb, and the one workflow doc that cites it. No change to ledger semantics, storage, or the run viewer's rendering.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/run_cli.py, agent_workflows/command_surface.py, agent_workflows/completion.py, .aw/system/workflows/exec-set/exec-set.md, tests/test_run_recovery_cli.py, tests/test_run_evidence_completion.py, tests/test_run_viewer.py, tests/test_completion.py
- Item-Dependencies: none
- Status: approved
- Set: runnamecollapse
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 0soncw
- Approval: 2026-08-30, recorded via aw ipd set: status set to approved
- From-Backlog: q5pdiy

## Workflow history
- 2026-08-31 approved (opencode/its_direct/pt3-claude-opus-5-1m-us): MAINTAINER RESOLVED OQ-03 AND OQ-02, and the plan is RE-SCOPED accordingly; this was the last blocking question, so the plan is now executable. RULING: TWO NOUNS SPLIT BY DIRECTION - `aw run` WRITES, `aw runs` READS. Close to the old option (c) but not identical: (c) parked the ledger leaves under a third noun `aw ledger`; the ruling keeps TWO words and leaves the writers under `aw run`. THE ARGPARSE BLOCKER DISSOLVES rather than being worked around: with only viewers under `aw runs`, that parser needs NO subparsers, so nothing competes with its `targets nargs="*"`, bare `aw runs <id>` keeps working, and the proven-unimplementable combination is simply never built. SPLIT decided from measured behavior, not names: MOVED (9 viewers) `show`, `status`, `list`, `next`, `resume`, `decisions`, `questions`, `evidence`, `verify-ledger` (`next`/`resume` sound like actions but only reconstruct state and report); RETAINED (4 writers) `start`, `record`, `cancel`, `finalize`. EDITS APPLIED: title and Concern re-scoped (the plan no longer 'retires the aw run noun'); Goal corrected; E-03 narrowed from 'every subcommand' to the nine viewers with the argparse rationale kept as the record of why the original design failed; E-05 REVERSED from 'retire the noun to a stub' to 'leave a per-leaf deprecation response for the nine moved leaves while `aw run start ...` keeps working'; V-03, V-04 and the command_surface count corrected (10 under `runs`, not 13). WHY E-05'S REVERSAL MATTERS BEYOND TIDINESS: retiring the whole noun would have installed a failing stub over the exact namespace the approved `runprofile` Set builds on, so `aw run as gem` would have started exiting nonzero. That collision was found in this session's review of that Set, and the maintainer settled the order as `0soncw` FIRST then `runprofile`, which is now encoded as `executed:0soncw` on that Set's chain head.
- 2026-08-30 approved (aw set): status set to approved
- 2026-08-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review: REVIEWED - OPEN QUESTIONS; PR-001..PR-006. BLOCKER: E-03's premise is unimplementable - argparse cannot combine targets nargs='*' with subparsers (verified: show/RUN1, RUN1, RUN1 RUN2 all exit 2), so routing needs pre-parse argv inspection plus a collision rule; raised as blocking OQ-03. Also corrected the suite baseline (2883/1 failed/7 skipped, not 2865 passed) and disclosed a pre-existing red test inside the plan's own Scope-Paths.

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `q5pdiy` per the maintainer's decision to collapse inspection under `aw runs`.

## Goal

Make one job have one name. Today `aw run list` and `aw runs` emit byte-identical output, and the
whole `aw run` noun is a read-only inspector holding a name that reads like "run an agent". This plan
moves the NINE READ-ONLY `aw run` subcommands under `aw runs`, deletes the duplicate `list`, and leaves
a per-leaf deprecation response for each moved leaf. RE-SCOPED 2026-08-31 (OQ-03): `aw run` itself is
NOT retired. It survives as the WRITING noun (`start`, `record`, `cancel`, `finalize`) and is the verb
the approved `runprofile` Set extends with `aw run as <profile>`, so this plan vacates only the
inspection leaves rather than the whole name. This plan still does NOT take on the default-host design
that the profile dispatch requires; that remains `runprofile`'s job, sequenced after this one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: characterize before moving anything

- [ ] E-01 Add a characterization test that pins the CURRENT observable surface before any rename: for
      each of the twelve `run` leaves declared in `command_surface.py:759-880`
      (`show`, `evidence`, `verify-ledger`, `start`, `next`, `record`, `resume`, `cancel`, `status`,
      `finalize`, `decisions`, `questions`), assert the leaf parses and returns its documented exit
      class on a fixture ledger. This is the safety net that proves the move preserves behaviour, so
      it must be written and passing BEFORE E-03 changes any parser wiring.
  - Depends on: none
  - Expected outcome: a new test class fails if any leaf's parse or exit class changes, and passes at
    current HEAD unmodified.
  - Execution state: pending

- [ ] E-02 Add an adversarial duplicate-detection test asserting that no two distinct CLI invocations
      render the same output for the run family. Seed it with the known pair (`aw run list` vs
      `aw runs`) so it FAILS at current HEAD, proving the guard actually fires, and keep it as the
      standing regression once E-04 removes the duplicate. FLAKINESS CONSTRAINT (PR-003, measured):
      a literal BYTE comparison of live output is NOT stable. Verified: `run list` vs `runs` on this
      repo differ on 2 of 1031 lines purely because the viewer prints elapsed wall-clock for live
      processes (`runtime: 31m 19s` vs `31m 21s`); after masking `runtime:` values the two are
      identical. So the test MUST run against a FIXTURE ledger (no live pids) and/or normalize volatile
      fields (runtime, elapsed, timestamps) before comparing, and the plan must state which. A guard
      that compares raw bytes of live output would fail intermittently for reasons unrelated to the
      duplication it is meant to catch.
  - Depends on: none
  - Expected outcome: the test fails at HEAD naming the duplicate pair, passes after E-04, and is
    stable across repeated runs (assert by running it twice in the same session).
  - Execution state: pending

### Task group 2: move the surface

- [ ] E-03 Register the NINE READ-ONLY `run` subcommands under the `runs` parser group in `cli.py`,
      keeping each leaf's arguments, help text, and epilog identical.
      CORRECTED BY MAINTAINER RULING 2026-08-31 (see OQ-03, now resolved): do NOT move "every"
      subcommand. The surface splits BY DIRECTION into two nouns - `aw run` WRITES, `aw runs` READS.
      MOVE to `aw runs` (viewers): `show`, `status`, `list`, `next`, `resume`, `decisions`, `questions`,
      `evidence`, `verify-ledger`. `next` and `resume` sound like actions but only reconstruct state and
      report, so they are viewers.
      LEAVE under `aw run` (writers): `start`, `record`, `cancel`, `finalize`.
      THIS DISSOLVES THE ARGPARSE BLOCKER below rather than working around it: with only viewers under
      `aw runs`, that parser needs NO subparsers at all, so nothing competes with its `targets`
      `nargs="*"`, bare `aw runs <id>` keeps working, and no pre-parse argv routing is needed. The
      proven-unimplementable combination is simply never constructed. Keep the constraint text below as
      the RECORD of why the original design could not work, and do not reintroduce it. IMPLEMENTATION CONSTRAINT PROVEN IN REVIEW
      (PR-001): the plan's original instruction ("only treat the first positional as a subcommand when
      it exactly matches a registered leaf name") is NOT expressible declaratively in argparse, and
      the naive combination FAILS OUTRIGHT. `p_runs` has `targets` with `nargs="*"` (cli.py:1667-1672);
      adding `add_subparsers()` to that same parser is accepted at construction but every invocation
      then errors, because the greedy `nargs="*"` positional consumes the first token and argparse
      then rejects the remainder as an "invalid choice". VERIFIED: with `targets nargs="*"` plus a
      `show` subparser, `["show","RUN1"]`, `["RUN1"]`, and `["RUN1","RUN2"]` ALL exit 2; only the empty
      argv parses. So the routing MUST be done by inspecting `argv` BEFORE `parse_args` (dispatch the
      leaf parser when `argv[0]` is exactly a registered leaf name, else route to the viewer), or by
      some equivalent pre-parse hook. Choose ONE mechanism, implement it explicitly, and cite it in
      the code, rather than relying on argparse to disambiguate. ALSO resolve the resulting AMBIGUITY
      (PR-002): `aw runs` accepts SET IDS as targets and set ids are free-form (158 in this repo), so a
      future set id equal to a leaf name (e.g. a set literally named `status`) becomes unreachable as a
      viewer target. No collision exists today (verified: zero of 158 set ids and zero of 61 run ids
      match any leaf name), but the rule must be documented and given an escape hatch (e.g. honor `--`
      so `aw runs -- status` forces viewer interpretation).
  - Depends on: E-01
  - Expected outcome: every `aw runs <leaf> <target>` invocation behaves exactly as `aw run <leaf>
    <target>` did; bare `aw runs`/`aw runs <run-id>`/`aw runs <set-id>` still renders the viewer; and a
    target that collides with a leaf name is still reachable by the documented escape hatch.
  - Execution state: pending

- [ ] E-04 Delete the duplicate `list` registration (`cli.py:1548`, verified) and drop `list`/`summary`/
      `viewer` from the alias tuple in `run_cli.run_cli` (`run_cli.py:56`, verified - the plan's
      original `:49-52` was off), so exactly one spelling renders the viewer table. Note `summary` and
      `viewer` are NOT registered parser leaves (only `list` is), so removing them from the tuple is
      dead-branch cleanup rather than a user-visible removal; state that so the change is not
      mis-reported as retiring three commands.
  - Depends on: E-03
  - Expected outcome: `aw run list` no longer exists as a distinct rendering path; E-02's duplicate
    test passes.
  - Execution state: pending

- [ ] E-05 Do NOT retire the `aw run` noun. REVERSED BY MAINTAINER RULING 2026-08-31 (see OQ-03).
      `aw run` SURVIVES as the WRITING verb, keeping `start`, `record`, `cancel` and `finalize`, and it
      is the noun the `runprofile` Set then extends with `aw run as <profile>`. What this item must do
      instead is narrower: for each of the NINE leaves MOVED to `aw runs` by E-03, leave an actionable
      deprecation response under `aw run` naming the `aw runs` replacement and exiting nonzero, rather
      than argparse's bare "invalid choice". Do NOT silently forward, because silent aliases are how
      the duplicate in E-04 survived unnoticed. So `aw run show X` must say "use `aw runs show X`" and
      fail, while `aw run start ...` must keep WORKING unchanged.
      WHY THIS MATTERS BEYOND TIDINESS: retiring the whole noun would have installed a failing stub over
      the exact namespace the approved `runprofile` Set builds on, so `aw run as gem` would have begun
      exiting nonzero. That collision was found in this session's review of that Set and is the reason
      the ordering (`0soncw` first, then `runprofile`) was settled.
  - Depends on: E-03, E-04
  - Expected outcome: `aw run show X` prints a message naming `aw runs show X` and exits nonzero;
    no ledger work is performed.
  - Execution state: pending

### Task group 3: keep the declared surface honest

- [ ] E-06 Update `command_surface.py` so the declarations track reality: rename the twelve
      `run <leaf>` declarations to `runs <leaf>` preserving each one's `command_class`,
      `human_recipe`, `mutation_gate`, and `exit_contract` verbatim, and ADD the missing top-level
      `runs` declaration. `aw runs` is currently undeclared entirely (`grep -n 'command="runs'
      agent_workflows/command_surface.py` returns nothing) while all twelve `run *` leaves are
      declared, so the invested surface is the undeclared one.
  - Depends on: E-03, E-05
  - Expected outcome: `tests/test_cli_conformance_matrix.py` passes and the declared set matches the
    parser leaves for this family.
  - Execution state: pending

- [ ] E-07 Update the help/description text that names the old verb: the `"run"` and `"run <leaf>"`
      entries in the `cli.py:99` help dictionary, the `run_cli.py` module docstring and its usage
      string, and the three citations in `.aw/system/workflows/exec-set/exec-set.md:47-49`
      (`aw run status|decisions|questions <run-id>`). Note: the copies of that doc under
      `.aw/worktrees/*/` are other agents' lane checkouts and MUST NOT be touched.
  - Depends on: E-03, E-05
  - Expected outcome: no user-facing help or workflow doc instructs a reader to run `aw run <leaf>`.
  - Execution state: pending

- [ ] E-08 Update the tests that invoke the verb to the new spelling: `tests/test_run_recovery_cli.py`
      (31 `"run"` invocations), `tests/test_run_evidence_completion.py` (12), `tests/test_run_viewer.py`
      (2), and the completion expectations in `tests/test_completion.py:269,297,381`. Retain at least
      one test asserting the E-05 deprecation stub's message and exit code, so the retirement itself
      stays covered. ALSO settle the COMPLETION surface (PR-005, F-7), which the plan did not mention:
      `completion.py:632` routes target completion for `words[1] in ("run", "runs")` as one surface, and
      `tests/test_completion.py` asserts `run` is among the offered subcommands. Decide explicitly
      whether the retired noun (a) still completes, so a user tab-completing `aw run ` is guided to the
      stub message, or (b) disappears from completion entirely. Either is defensible; leaving it
      undecided means the test expectations and the parser can disagree silently.
      DO NOT "fix" the pre-existing failure in `tests/test_run_viewer.py` (F-8) while editing that file.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: default suite shows the SAME single pre-existing failure as the recorded baseline
    and no new ones, with no reference to a live `aw run <leaf>` path; the completion decision is
    implemented and asserted.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `aw runs` is the invested surface: it is the spelling the maintainer uses, and it reads
  `.aw/records/runs/<id>/events.jsonl`, the format the drivers actually write. The collapse direction
  is therefore "retire the duplicate and relocate the ledger surface", NOT "rename `runs` to `run`".
- The command surface is normatively declared in `command_surface.COMMAND_INVENTORY` and checked by
  `tests/test_cli_conformance_matrix.py` and `tests/test_command_surface_declarations.py`; a parser
  leaf added without a declaration is a test failure, so E-06 is mandatory, not cosmetic.
- `tests/test_command_surface_declarations.py` is `slow`-marked and EXCLUDED from the default run, and
  it carries a PRE-EXISTING failure (42 undeclared parser leaves, including `agy exec`, `completion`,
  `commit`, `finish`). That failure predates this plan. Do not adopt it and do not claim to fix it;
  just do not make it worse.
- The drivers' own verbs are `aw oc run` / `aw agy run` (`cli.py:2724,2786` register `run` as an alias
  inside those families). Retiring the top-level `aw run` noun does NOT touch them.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | `aw run list` and `aw runs` render the SAME table (one renderer), but their raw output is NOT byte-stable. | Re-verified in review: `diff` showed 2 differing lines of 1031 (not 967), both `runtime: 31m 19s` vs `31m 21s` for live pids; identical after masking `runtime:`. The duplication claim holds; the "byte-identical" wording does not, which is why E-02 must normalize or use a fixture (PR-003). |
| F-2 | The duplication is structural: one renderer, four spellings. | `run_cli.py:56` maps `list`, `runs`, `summary`, and `viewer` all to `run_viewer.run_viewer_cli` (the plan cited :49-52; the tuple is at :56). |
| F-3 | `aw run` runs nothing; it is inspection plus ledger transaction verbs. | `run_cli.py:53-89` dispatches only show/evidence/verify-ledger/start/next/record/resume/cancel/status/finalize/decisions/questions, then prints a usage string. |
| F-4 | The migration is cheap, contradicting an earlier assessment that called it a breaking migration needing its own spec. | One parser site (`cli.py:1389-1560`), the `run` dispatch at `cli.py:8273-8281` AND the separate `runs` dispatch immediately after at `cli.py:8282-8285` (the plan cited only one site - both must be reconciled), four test files invoking the verb, one workflow doc (`exec-set.md:47-49`), zero shims or hooks. Confirmed no production code shells `aw run <sub>`: every `agent_workflows/` hit is a docstring, help string, or the dispatch itself. |
| F-7 | `completion.py` treats `run` and `runs` as ONE completion surface, so retiring the noun must not silently break tab completion. | `completion.py:632` is `if cword >= 2 and words[1] in ("run", "runs")`, and `tests/test_completion.py` asserts both `run` and `runs` appear in subcommand candidates (`:269`, `:381`) and completes targets after `aw run` (`:297`). E-08 must decide whether the retired noun still completes. |
| F-8 | A pre-existing suite failure sits in a file this plan edits. | `tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_issues_flag` fails at HEAD (reproducible in isolation), introduced by `20caf1c`. Measured baseline is 2883 tests / 1 failed / 7 skipped, not the plan's original `2865 passed, 3 skipped, 4 xfailed`. |
| F-5 | `aw runs` is undeclared in the normative command surface while all twelve `run *` leaves are declared. | `grep -n 'command="runs' agent_workflows/command_surface.py` -> no matches; `grep -c 'command="run ' ...` -> 12. |
| F-6 | A real `aw run` meaning "run on the default host" is blocked on a concept that does not exist. | `project_schema.py` has `enabled_hosts` (default `["opencode","claude","antigravity"]`) but no default or preferred host field, and nothing in the pipeline defines one. |

## Proposed changes (ordered, validatable)

1. Pin the current twelve-leaf surface with a characterization test (E-01) and make the duplicate
   detectable with a test that fails at HEAD (E-02).
2. Re-register the leaves under `runs`, preserving arguments and exit contracts (E-03).
3. Remove the duplicate `list` path (E-04).
4. Turn `aw run` into a loud deprecation stub, not a silent alias (E-05).
5. Reconcile `command_surface.py` and every help/doc citation (E-06, E-07).
6. Migrate the test spellings and keep the stub covered (E-08).

## Deferred / out of scope (with reason)

- **Making `aw run <selector>` actually run something.** Deferred: it requires a default-host
  resolution concept that does not exist (F-6). This plan only FREES the name; it deliberately does
  not claim it. Conflating the two would make a cheap rename depend on an undesigned feature.
- **Wiring the run ledger.** Deferred by explicit maintainer decision on 2026-08-29: it overlaps wtiso
  Phase 2 (`rchpms`) and spec `25kzda` is still `to-review`. This plan changes only the NAME of the
  inspection surface, not whether the ledger it inspects is ever populated.
- **The pre-existing 42 undeclared parser leaves** in the slow-marked declaration test. Out of scope:
  not caused by this work, and fixing it is a separate sweep.
- **The pre-existing failure `test_run_viewer_cli_issues_flag`** (F-8). Out of scope: introduced by
  `20caf1c`, unrelated to naming. Called out explicitly because it lives in a file this plan edits, so
  the executor must neither adopt it as their own regression nor quietly "fix" it mid-rename. Report it,
  leave it, and confirm the failure set is unchanged at the end.
- **The `aw ledger start|next|record|...` split** floated in discussion (moving the transaction verbs
  to their own noun). Deferred: it is a second, larger taxonomy decision, and doing it inside this
  plan would mean two renames landing at once with no way to bisect a regression.

## Scope check

- Over-scope: none. Every E-item touches only the naming surface or its tests.
- Under-scope: the plan does not deliver a working `aw run` driver verb, by design (see Deferred). A
  reader expecting `aw run <thing>` to launch an agent after this lands will not get it; the name is
  merely freed and guarded by a deprecation stub.
- Under-scope found in review and now CLOSED: the plan did not name the second dispatch site
  (`cli.py:8282`, the `runs` branch beside the `run` branch), the completion surface that treats the two
  spellings as one (`completion.py:632`, F-7), or the pre-existing red test inside its own Scope-Paths
  (F-8). All three are now explicit. The routing mechanism gap (PR-001) is the one item review could NOT
  close by editing, because the fix requires a UX choice: it is raised as blocking OQ-03.

## Required tests / validation

1. `python3 -m pytest tests/test_run_recovery_cli.py tests/test_run_evidence_completion.py
   tests/test_run_viewer.py tests/test_completion.py tests/test_cli_conformance_matrix.py -q` green
   EXCEPT for the pre-existing failure named below, which must stay the only failure.
2. The full default suite with the actual counts pasted. CORRECTED BASELINE (PR-004, measured in review
   on 2026-08-29 at HEAD; the plan's `2865 passed, 3 skipped, 4 xfailed` was wrong): **2883 tests, 1
   failed, 0 errors, 7 skipped** (counts read from `--junitxml`, because the repo's `addopts` uses
   `-q -n auto` and the xdist summary line is suppressed - use
   `python3 -m pytest -p no:randomly -n0 --tb=no -q --junitxml=<f>` then read the `testsuite`
   attributes, and say so in the evidence).
3. THE PRE-EXISTING FAILURE MUST BE HANDLED HONESTLY, not adopted and not hidden:
   `tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_issues_flag` FAILS at HEAD
   (`AssertionError: 'Artifact & Status Discrepancies' not found in 'no artifact or status
   discrepancies found'`), reproducible in isolation, introduced by commit `20caf1c`
   (`feat(run_viewer): add discrepancy table, Issue column, and --issues/-i flag`) - i.e. it predates
   this plan. It matters here because `tests/test_run_viewer.py` is IN this plan's Scope-Paths (E-08),
   so the executor will be editing the very file that is red. Required: paste the failure BEFORE
   starting, do NOT fix it (out of scope, not this plan's bug), do NOT let it be mistaken for
   regression, and confirm at the end that the failure set is still exactly this one test. If it
   disappears or multiplies, STOP and report.
4. E-02's duplicate-output test demonstrated FAILING at pre-change HEAD and passing after, pasting
   both runs, plus evidence it is stable (run it twice). A guard never seen to fail is not evidence.
5. Manual confirmation that bare `aw runs`, `aw runs <run-id>`, and `aw runs <set-id>` still render the
   viewer table unchanged, by diffing against output captured before the change WITH volatile
   `runtime:`/elapsed fields masked (see E-02: raw output differs run-to-run for live processes).
6. The E-03 ambiguity rule exercised: a target whose name equals a leaf name routes as the documented
   rule says, and the escape hatch reaches the viewer.

## Spec / documentation sync

- `.aw/system/workflows/exec-set/exec-set.md:47-49` must be updated (E-07); it is the only tracked
  workflow doc citing `aw run <leaf>`.
- Spec `25kzda` describes `aw run` as the deterministic run-and-verify surface. It is `to-review` and
  NOT to be edited by this plan; if the maintainer approves this collapse, that spec's naming section
  should be reconciled when the spec itself is reviewed. Flagged, not silently changed.
- No README or CHANGELOG entry is required until the collapse actually ships, since the retirement is
  a stub rather than a removal. If a CHANGELOG line IS written, it must not claim three commands were
  retired: only `list` was a registered leaf; `summary`/`viewer` were unreachable dispatch branches
  (verified: `aw run summary` is an argparse "invalid choice" today).
- The shell completion surface is user-facing and must stay consistent with the parser: `completion.py:632`
  treats `run` and `runs` as one surface and the generated completion script offers both names. Whatever
  E-08 decides, the documented behavior and the tests must agree (F-7).

## Open questions

### OQ-01: Should the per-leaf `aw run` deprecation responses be permanent or time-boxed?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: LARGELY ANSWERED BY OQ-03's RULING (2026-08-31), and reframed: there is no whole-noun stub any more, because `aw run` SURVIVES as the writing verb. What remains is nine per-leaf deprecation responses (one for each moved viewer), and the original recommendation now describes reality rather than a future hope: it said keep the stub "until a real driver `aw run` exists", and a real driver `aw run` is exactly what the `runprofile` Set adds immediately after this plan. So the sensible answer is KEEP the nine per-leaf responses indefinitely (they cost nothing and prevent a stale `aw run show` from silently doing nothing), and revisit only if the help output becomes cluttered. Still non-blocking either way. ORIGINAL RATIONALE: E-05 ships a stub either way, so execution is not blocked. The
  question is only whether a later release deletes it. Recommendation: keep it until a real driver
  `aw run` exists, because the stub is exactly what prevents a stale `aw run show` from being read as
  the future "run something" verb.

### OQ-02: Do the twelve leaves belong under `aw runs`, or do the ten transaction verbs belong under a separate `aw ledger` noun?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ANSWERED BY THE SAME MAINTAINER RULING as OQ-03 (2026-08-31): the leaves do NOT all belong under `aw runs`, and they do not go to a separate `aw ledger` either. They split BY DIRECTION: the nine read-only viewers move to `aw runs`, and the four writers (`start`, `record`, `cancel`, `finalize`) stay under `aw run`, which becomes the doing verb. See OQ-03 for the full split and rationale. ORIGINAL RATIONALE: not blocking, because moving everything to `aw runs` first is a
  strict improvement and is reversible. Deliberately deferred rather than decided here (see Deferred);
  a second split can follow once this one is proven.

### OQ-03: How should `aw runs` disambiguate a subcommand from a viewer target, given argparse cannot?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-08-31: **TWO NOUNS, SPLIT BY WHAT THEY DO** - `aw run` for RUNNING (it writes), `aw runs` for VIEWING (it reads). This is close to option (c) but NOT identical: option (c) proposed parking the ledger leaves under a third noun (`aw ledger`), whereas the ruling keeps TWO words and puts the writing leaves under `aw run` alongside the new dispatch. THE ARGPARSE PROBLEM DISSOLVES rather than being worked around: if `aw runs` only ever views, it needs NO subparsers at all, so nothing competes with its `targets nargs="*"` and bare `aw runs <id>` keeps working with no hand-rolled routing and no latent ambiguity. THE SPLIT, decided from each leaf's measured behavior rather than its name: VIEWING (to `aw runs`) = `show`, `status`, `list`, `next`, `resume`, `decisions`, `questions`, `evidence`, `verify-ledger`; note `next` and `resume` SOUND like actions but only reconstruct state and report, so they are viewers. WRITING (stays under `aw run`) = `start` (takes the single-writer lease and moves a step to running), `record` (appends to the append-only ledger), `cancel` (records a terminal cancellation), `finalize` (runs the completion predicate and transitions). Rationale for keeping the four under `aw run` rather than a third noun: the rule stays teachable in one line ("`aw run` writes, `aw runs` reads") and there is no third command word to learn; the accepted cost is that `aw run` mixes one high-level verb typed daily with four low-level ones invoked by the machinery. CONSEQUENCE FOR THIS PLAN: E-03 must NO LONGER move every leaf to `runs`, and OQ-02 is answered at the same time (the leaves do NOT all belong under `aw runs`; they split by direction). CONSEQUENCE BEYOND IT: `aw run` is NOT retired to a bare stub after all, it becomes the doing verb, which is precisely what the `runprofile` Set (`3m0urk` and children) needs for `aw run as <profile>`; that Set now declares `executed:0soncw` and so lands after this plan.

  ORIGINAL FINDING AS RAISED: OPEN and BLOCKING E-03. The plan assumed `aw runs` could carry both
  its bare `targets` (`nargs="*"`) and a subcommand group, disambiguated by "first positional exactly
  matches a leaf name". Review PROVED that combination is unworkable in argparse: with `targets
  nargs="*"` plus a `show` subparser, `["show","RUN1"]`, `["RUN1"]` and `["RUN1","RUN2"]` all exit 2
  (the greedy positional eats the first token, then the subparser rejects the rest); only empty argv
  parses. A working design therefore needs an explicit mechanism plus a collision rule, and the choice
  is a UX decision the maintainer owns: (a) PRE-PARSE ARGV ROUTING - inspect `argv[0]`, dispatch the
  leaf parser on an exact leaf-name match, else route to the viewer; keeps `aw runs <id>` and
  `aw runs show <id>` both working, at the cost of a hand-rolled routing step and a latent ambiguity
  (a set id named `status` becomes unreachable without an escape hatch such as honoring `--`);
  (b) REQUIRE AN EXPLICIT SUBCOMMAND, making the viewer its own leaf (e.g. `aw runs list`/`aw runs
  show-all`) so argparse handles everything cleanly and there is no ambiguity - but this BREAKS the bare
  `aw runs <run-id>` spelling the maintainer actually uses, which the plan's own conventions call the
  invested surface; (c) KEEP TWO NOUNS - leave the viewer as bare `aw runs` and put the ledger leaves
  under a different noun (e.g. `aw ledger <leaf>`), which sidesteps the conflict entirely and overlaps
  OQ-02's split. Note (c) would change this plan's shape substantially, so it should be settled before
  execution rather than discovered during it. No collision exists in the repo today (zero of 158 set ids
  and zero of 61 run ids match a leaf name), so any option is safe to adopt now; the decision is about
  which surface the maintainer wants to live with.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the characterization test run showing all twelve leaves asserted, plus
    the `git stash`-style demonstration that it passes at pre-change HEAD unmodified. List the twelve
    leaf names actually covered, so a missing leaf is visible.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste TWO runs of the duplicate-detection test: one at pre-change HEAD showing
    it FAIL and naming the `run list` / `runs` pair, and one after E-04 showing it pass. A guard that
    was never observed failing is not accepted as evidence. PLUS the STABILITY proof (PR-003): show the
    test uses a fixture ledger and/or masks volatile fields, and paste two consecutive passing runs.
    State explicitly which fields are normalized, citing the measured `runtime:`-only divergence
    (2 of 1031 lines) that makes a raw byte comparison flaky.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: CORRECTED 2026-08-31 (OQ-03): for each of the NINE MOVED (read-only) leaves
    (`show`, `status`, `list`, `next`, `resume`, `decisions`, `questions`, `evidence`, `verify-ledger`),
    paste the exit code of `aw runs <leaf> <target>` alongside the pre-change exit code of
    `aw run <leaf> <target>` on the same fixture, showing them equal. SEPARATELY, for each of the FOUR
    RETAINED (writing) leaves (`start`, `record`, `cancel`, `finalize`), paste evidence they still work
    UNCHANGED under `aw run` and were NOT moved, since the ruling keeps them there. Also confirm
    `aw runs` has NO subparsers, which is what dissolves the argparse blocker. Also paste bare `aw runs` and `aw runs <run-id>` output diffed against captures taken
    before the change, with volatile `runtime:`/elapsed fields masked (expect zero diff after masking).
    PLUS the ROUTING evidence (PR-001/OQ-03): name the mechanism actually implemented and paste a test
    showing all four argv shapes route correctly - `runs <leaf> <target>`, `runs <run-id>`,
    `runs <set-id>`, and bare `runs`. Include the NEGATIVE case that proves the argparse trap was
    avoided: a target whose name equals a leaf name resolves per the documented rule, and the escape
    hatch (e.g. `aw runs -- status`) reaches the viewer.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the output of `aw run list` after the change (expect the per-leaf
    deprecation response from the corrected E-05, not a table; `list` is one of the NINE moved leaves) and confirm exactly one spelling renders the viewer, by showing `grep -n` of the alias
    tuple in `run_cli.py` with `list`/`summary`/`viewer` gone.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw run show <target>; echo rc=$?` showing the actionable message that
    names `aw runs show <target>` and a NONZERO rc. Additionally show that no ledger write occurred
    (the stub must not touch the store): paste the target dir listing before and after, identical.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_cli_conformance_matrix.py -q` green, plus
    `grep -c 'command="runs' agent_workflows/command_surface.py` showing the CORRECTED count of 10 (the
    NINE moved read-only leaves plus the bare viewer; not 13 - OQ-03's ruling keeps the four writing
    leaves under `aw run`, so their declarations stay `command="run ..."`). Also paste the count for
    `command="run` proving the four writers are still declared there. The original wording said 13 (twelve leaves plus the
    previously missing top-level `runs`) and `grep -c 'command="run '` showing 0.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `grep -rn 'aw run ' --include='*.md' .` filtered to TRACKED files
    (excluding `.aw/worktrees/`, `.aw/records/runs/`, `opencode-recovery/`, and other agents' lanes)
    showing zero live instructions to use `aw run <leaf>`; and `grep -n 'aw run' agent_workflows/run_cli.py`
    showing the docstring and usage string updated.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the full default suite result with actual counts read from `--junitxml`
    (the `-q -n auto` addopts suppress the summary line), compared against the CORRECTED baseline of
    **2883 tests / 1 failed / 0 errors / 7 skipped**. The failure set MUST still be exactly
    `test_run_viewer_cli_issues_flag` (F-8, pre-existing, introduced by `20caf1c`): paste it before and
    after and state that it was neither fixed nor adopted. Any other change in the failure set, or that
    test becoming green, must be explained rather than absorbed. Also paste the specific test asserting
    the deprecation stub's message and exit code, and the completion-surface assertion showing the
    E-08 decision (retired noun still completes, or does not) is implemented and tested.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (collapse the run-inspection naming surface onto `aw runs` and retire
  the `aw run` noun). The E-items are ordered sub-steps of that one rename: characterize, move,
  de-duplicate, retire, then reconcile declarations/help/tests. No E-item changes ledger semantics or
  rendering.

This plan is `to-review` and requires explicit human approval before execution. It is a user-facing
CLI naming change: even though no production code shells `aw run <sub>` (F-4), a human's muscle memory
and any personal scripts do, which is exactly why E-05 ships a loud stub instead of a silent removal.

Execution contract:

1. Open questions: OQ-01 and OQ-02 are non-blocking and may be executed around; OQ-03 is BLOCKING and
   must be answered before E-03 is implemented, because it fixes the routing mechanism and the
   collision rule that E-03 depends on.
2. Scope fence: touch ONLY the paths in `Scope-Paths`. Do NOT change ledger semantics, storage, or the
   viewer's rendering; do NOT fix the pre-existing `test_run_viewer_cli_issues_flag` failure (F-8) or the
   42 undeclared leaves; do NOT edit spec `25kzda`; do NOT touch `.aw/worktrees/*/` lane copies (other
   agents' checkouts). Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan or this orchestrator, and do NOT reimplement a rule another plan owns.
3. Honesty rule (HARD MUST): paste the ACTUAL runner output for every named command. A V-item whose
   command was not executed stays `Result: pending`. Report suite counts from `--junitxml` (the repo's
   `-q -n auto` addopts suppress the summary line) and compare against the corrected baseline of
   2883 tests / 1 pre-existing failure / 7 skipped.
4. NO SILENT FORWARDING: E-05 must be a loud, nonzero stub. Do not make `aw run` an invisible alias -
   silent aliasing is exactly how the E-04 duplicate survived unnoticed.
5. PRE-EXISTING FAILURE DISCIPLINE: record the single known failure before starting and confirm the
   failure set is IDENTICAL at the end. A newly green or newly red test in that file must be explained,
   not absorbed.
6. Shared checkout: other agents work concurrently here. Commit only this plan's changed files,
   path-scoped (`git commit -m msg -- <path>`); verify with `git diff --cached --name-only` before each
   commit; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
7. Lifecycle move on completion: when every `V-*` item carries pasted evidence and
   `aw ipd lint --phase pre-transition` conforms, move this plan to `.aw/records/plans/executed/` via
   `aw ipd finalize`; do not hand-move it, and do not mark it executed on the strength of the execution
   checkmarks alone.
