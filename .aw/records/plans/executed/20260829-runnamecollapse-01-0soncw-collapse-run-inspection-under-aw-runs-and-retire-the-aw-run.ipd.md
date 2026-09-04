# IPD: Split the run surface into two nouns: aw run writes, aw runs reads

- Date: 2026-08-29
- Kind: child
- Concern: `aw run list` and `aw runs` are byte-identical duplicates, and the noun `aw run` is misleading because most of what it holds only INSPECTS past runs rather than running anything. RE-SCOPED BY MAINTAINER RULING 2026-08-31 (OQ-03): rather than retiring `aw run`, split the surface BY DIRECTION into two nouns - `aw run` WRITES (`start`, `record`, `cancel`, `finalize`, and later the `runprofile` Set's `aw run as <profile>` dispatch), `aw runs` READS (the nine read-only viewers). The original "retire the noun" framing is preserved in the history below.
- Scope: The CLI naming surface only: the `run` parser group in `agent_workflows/cli.py`, the dispatch in `agent_workflows/run_cli.py`, the `command_surface` declarations, the tests that invoke the verb, and the one workflow doc that cites it. No change to ledger semantics, storage, or the run viewer's rendering.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/run_cli.py, agent_workflows/command_surface.py, agent_workflows/completion.py, .aw/system/workflows/exec-set/exec-set.md, tests/test_run_recovery_cli.py, tests/test_run_evidence_completion.py, tests/test_run_viewer.py, tests/test_completion.py
- Item-Dependencies: none
- Status: executed
- Set: runnamecollapse
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 0soncw
- From-Backlog: q5pdiy

## Workflow history
- 2026-09-04 executed (aw oc run): aw oc run self-finalize: 0soncw verified (set runnamecollapse, attempt 1). [Scope reconciliation - out-of-scope docs/evidence.md: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope docs/recovery.md: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope docs/troubleshooting.md: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope docs/verification.md: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope docs/walkthroughs/evidence-inspection.md: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope docs/walkthroughs/incomplete-run.md: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope docs/walkthroughs/recovery.md: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_exec_set_workflow.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_run_noun_split.py: changed by the plan's approved execution (auto-reconciled by aw oc run)]
- 2026-09-04 executed (opencode its_direct/pt3-claude-opus-5-1m-us): EXECUTED all 8 E-items; all 8 V-items carry pasted evidence; `aw ipd lint --phase pre-transition` conforming. SPLIT DELIVERED AS RULED: nine read-only leaves moved to `aw runs` (`show`, `status`, `list`, `next`, `resume`, `decisions`, `questions`, `evidence`, `verify-ledger`), four writers retained on `aw run` (`start`, `record`, `cancel`, `finalize`), duplicate `aw run list` deleted, old viewer spellings now rejected by normal argument parsing with no compatibility stub (per OQ-01). SUITE: my own pre-change baseline in this fresh lane was `tests=4136 failures=40` (NOT the plan's 4099/0 - 15 of those 40 are the machine-dependent `tests/test_run_viewer.py` set from backlog `agrlvw`, which fail in a lane with no local run records); after, `tests=4156 failures=32`, ZERO new failures, and the 8 red->green tests were proven ORDER-DEPENDENT flakes unrelated to this work (they pass at pre-change HEAD in isolation; three randomized post-change runs show a stable 32 with no new failures). Nothing in `tests/test_run_viewer.py` was fixed or adopted (its set is byte-identical, 15 before and after).
  FOUR THINGS THE PLAN GOT WRONG, all reported rather than absorbed. (1) THE MECHANISM: the ruling's claim that `aw runs` 'needs NO subparsers' is FALSE - the nine viewers each take a required single `target` plus leaf-specific flags while the bare viewer takes `targets nargs="*"` plus thirteen filter flags, so `aw runs` must carry BOTH shapes, which is exactly the combination PR-001 proved argparse cannot express (re-verified on CPython 3.14). Implemented an explicit `_ViewerOrLeafSubParsersAction` + `_RunsArgumentParser` + `_RunsTargetsPlaceholderAction`, chosen over positional routing because only REAL subparsers are visible to `discover_parser_leaves`, a hard precondition for E-06 (D1). (2) V-06's COUNT: delivered 9 `command="runs` declarations, not 10 - a family ROOT cannot be declared as a leaf (doing so broke the pinned drift test), and no other root (`ipd`, `specs`, `backlog`) is declared either; the viewer's contract is carried by the real `runs list` leaf (D4). (3) THE DOC SURFACE: `exec-set.md` is NOT the only doc citing the verb - seven `docs/` files carried 21 citations, 19 naming moved leaves; fixed the moved ones, preserved both `aw run finalize` (D3). (4) A TEST hard-coded the old spelling (`test_help_advertises_only_real_commands`), so E-07 broke it; retargeted AND strengthened to check the live parser (D2).
  THREE LATENT DEFECTS FOUND AND FIXED DURING EVIDENCE COLLECTION, each of which would have silently broken a surface: parser registration ORDER (a `targets` positional registered before the routing action swallowed the leaf name, so `aw runs show <t>` silently rendered the viewer); the placeholder action CLOBBERING resolved targets (`aw runs RUN1` reached the viewer with `targets=[]`, i.e. showing ALL runs); and `aw runs <TAB>` offering only targets, hiding every viewer leaf from completion. All three are now regression-tested. OUT-OF-SCOPE PATHS (2, both justified in the run's decisions register): `tests/test_exec_set_workflow.py` and seven `docs/*.md`.
- 2026-09-03 approved (opencode its_direct/pt3-claude-opus-5-1m-us): STALENESS AMENDMENT ONLY at the maintainer's direction; status UNCHANGED (`approved`), scope UNCHANGED, no E/V item added or removed. Two defects fixed before this plan is executed, both of which would have sent an executor after a wrong number or a reversed design. (1) THE SUITE BASELINE WAS STALE BY ~42 PERCENT. Review recorded 2883 tests / 1 failed / 7 skipped; re-measured at HEAD `34cefa8b` the suite is `4092 passed, 3 skipped, 4 xfailed` with `--junitxml` attributes `tests=4099 failures=0 errors=0 skipped=7`. Recorded as new finding F-9 and propagated to the Required-tests baseline, V-08's required evidence, and execution-contract items 3 and 5. F-8's named pre-existing failure `test_run_viewer_cli_issues_flag` is now GREEN (`2 passed, 40 deselected`), and the plan is corrected to NOT read that as a fix: backlog `agrlvw` (open, high) measures 15 tests in `tests/test_run_viewer.py` reading gitignored live run data under `.aw/records/runs/`, so that file's pass/fail set is a property of the MACHINE, not of this plan. The invariant is therefore restated as "the failure SET is unchanged against your own pre-change measurement", never a fixed count and never "zero failures". (2) THREE PLACES STILL DESCRIBED THE REVERSED DESIGN. The Cohesion rationale still said the plan retires the `aw run` noun, contradicting both the title and E-05 after the 2026-08-31 ruling; execution-contract item 1 still called OQ-03 BLOCKING although the maintainer resolved it that same day; item 4 still spoke of a single whole-noun stub instead of nine per-leaf deprecation responses. All three corrected in place with the correction marked, so the record shows what changed rather than reading as if it were always right. `aw ipd lint` conforming after the edit. `aw check plans` reports 13 errors both before and after (verified by stash-and-recheck), so the pre-existing `check.lifecycle-transition-invalid` finding on this plan is untouched by this amendment and is not introduced by it.
- 2026-08-31 approved (opencode/its_direct/pt3-claude-opus-5-1m-us): MAINTAINER RESOLVED OQ-03 AND OQ-02, and the plan is RE-SCOPED accordingly; this was the last blocking question, so the plan is now executable. RULING: TWO NOUNS SPLIT BY DIRECTION - `aw run` WRITES, `aw runs` READS. Close to the old option (c) but not identical: (c) parked the ledger leaves under a third noun `aw ledger`; the ruling keeps TWO words and leaves the writers under `aw run`. THE ARGPARSE BLOCKER DISSOLVES rather than being worked around: with only viewers under `aw runs`, that parser needs NO subparsers, so nothing competes with its `targets nargs="*"`, bare `aw runs <id>` keeps working, and the proven-unimplementable combination is simply never built. SPLIT decided from measured behavior, not names: MOVED (9 viewers) `show`, `status`, `list`, `next`, `resume`, `decisions`, `questions`, `evidence`, `verify-ledger` (`next`/`resume` sound like actions but only reconstruct state and report); RETAINED (4 writers) `start`, `record`, `cancel`, `finalize`. EDITS APPLIED: title and Concern re-scoped (the plan no longer 'retires the aw run noun'); Goal corrected; E-03 narrowed from 'every subcommand' to the nine viewers with the argparse rationale kept as the record of why the original design failed; E-05 REVERSED from 'retire the noun to a stub' to 'leave a per-leaf deprecation response for the nine moved leaves while `aw run start ...` keeps working'; V-03, V-04 and the command_surface count corrected (10 under `runs`, not 13). WHY E-05'S REVERSAL MATTERS BEYOND TIDINESS: retiring the whole noun would have installed a failing stub over the exact namespace the approved `runprofile` Set builds on, so `aw run as gem` would have started exiting nonzero. That collision was found in this session's review of that Set, and the maintainer settled the order as `0soncw` FIRST then `runprofile`, which is now encoded as `executed:0soncw` on that Set's chain head.
- 2026-08-30 approved (aw set): status set to approved
- 2026-08-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review: REVIEWED - OPEN QUESTIONS; PR-001..PR-006. BLOCKER: E-03's premise is unimplementable - argparse cannot combine targets nargs='*' with subparsers (verified: show/RUN1, RUN1, RUN1 RUN2 all exit 2), so routing needs pre-parse argv inspection plus a collision rule; raised as blocking OQ-03. Also corrected the suite baseline (2883/1 failed/7 skipped, not 2865 passed) and disclosed a pre-existing red test inside the plan's own Scope-Paths.

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `q5pdiy` per the maintainer's decision to collapse inspection under `aw runs`.

## Goal

Make one job have one name. Today `aw run list` and `aw runs` emit byte-identical output, and the
whole `aw run` noun is a read-only inspector holding a name that reads like "run an agent". This plan
moves the NINE READ-ONLY `aw run` subcommands under `aw runs`, deletes the duplicate `list`, and removes the old viewer leaves so normal argument parsing rejects them. RE-SCOPED 2026-08-31 (OQ-03): `aw run` itself is
NOT retired. It survives as the WRITING noun (`start`, `record`, `cancel`, `finalize`) and is the verb
the approved `runprofile` Set extends with `aw run as <profile>`, so this plan vacates only the
inspection leaves rather than the whole name. This plan still does NOT take on the default-host design
that the profile dispatch requires; that remains `runprofile`'s job, sequenced after this one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: characterize before moving anything

- [x] E-01 Add a characterization test that pins the CURRENT observable surface before any rename: for
      each of the twelve `run` leaves declared in `command_surface.py:759-880`
      (`show`, `evidence`, `verify-ledger`, `start`, `next`, `record`, `resume`, `cancel`, `status`,
      `finalize`, `decisions`, `questions`), assert the leaf parses and returns its documented exit
      class on a fixture ledger. This is the safety net that proves the move preserves behaviour, so
      it must be written and passing BEFORE E-03 changes any parser wiring.
  - Depends on: none
  - Expected outcome: a new test class fails if any leaf's parse or exit class changes, and passes at
    current HEAD unmodified.
  - Execution state: performed

- [x] E-02 Add an adversarial duplicate-detection test asserting that no two distinct CLI invocations
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
  - Execution state: performed

### Task group 2: move the surface

- [x] E-03 Register the NINE READ-ONLY `run` subcommands under the `runs` parser group in `cli.py`,
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
  - Execution state: performed

- [x] E-04 Delete the duplicate `list` registration (`cli.py:1548`, verified) and drop `list`/`summary`/
      `viewer` from the alias tuple in `run_cli.run_cli` (`run_cli.py:56`, verified - the plan's
      original `:49-52` was off), so exactly one spelling renders the viewer table. Note `summary` and
      `viewer` are NOT registered parser leaves (only `list` is), so removing them from the tuple is
      dead-branch cleanup rather than a user-visible removal; state that so the change is not
      mis-reported as retiring three commands.
  - Depends on: E-03
  - Expected outcome: `aw run list` no longer exists as a distinct rendering path; E-02's duplicate
    test passes.
  - Execution state: performed

- [x] E-05 Do NOT retire the `aw run` noun. REVERSED BY MAINTAINER RULING 2026-08-31 (see OQ-03).
      `aw run` SURVIVES as the WRITING verb, keeping `start`, `record`, `cancel` and `finalize`, and it
      is the noun the `runprofile` Set then extends with `aw run as <profile>`. For each of the NINE
      leaves MOVED to `aw runs` by E-03, remove its `aw run` parser registration entirely. RESOLVED BY
      MAINTAINER 2026-09-03 (OQ-01): do not retain a compatibility response; `aw run show X` must fail
      through normal argument parsing, while `aw run start ...` keeps WORKING unchanged. Do NOT silently
      forward, because silent aliases are how the duplicate in E-04 survived unnoticed.
      WHY THIS MATTERS BEYOND TIDINESS: retiring the whole noun would have installed a failing stub over
      the exact namespace the approved `runprofile` Set builds on, so `aw run as gem` would have begun
      exiting nonzero. That collision was found in this session's review of that Set and is the reason
      the ordering (`0soncw` first, then `runprofile`) was settled.
  - Depends on: E-03, E-04
  - Expected outcome: `aw run show X` is rejected by normal argument parsing with a nonzero exit and no
    ledger work is performed; `aw run start ...` remains unchanged.
  - Execution state: performed

### Task group 3: keep the declared surface honest

- [x] E-06 Update `command_surface.py` so the declarations track reality: rename the twelve
      `run <leaf>` declarations to `runs <leaf>` preserving each one's `command_class`,
      `human_recipe`, `mutation_gate`, and `exit_contract` verbatim, and ADD the missing top-level
      `runs` declaration. `aw runs` is currently undeclared entirely (`grep -n 'command="runs'
      agent_workflows/command_surface.py` returns nothing) while all twelve `run *` leaves are
      declared, so the invested surface is the undeclared one.
  - Depends on: E-03, E-05
  - Expected outcome: `tests/test_cli_conformance_matrix.py` passes and the declared set matches the
    parser leaves for this family.
  - Execution state: performed

- [x] E-07 Update the help/description text that names the old verb: the `"run"` and `"run <leaf>"`
      entries in the `cli.py:99` help dictionary, the `run_cli.py` module docstring and its usage
      string, and the three citations in `.aw/system/workflows/exec-set/exec-set.md:47-49`
      (`aw run status|decisions|questions <run-id>`). Note: the copies of that doc under
      `.aw/worktrees/*/` are other agents' lane checkouts and MUST NOT be touched.
  - Depends on: E-03, E-05
  - Expected outcome: no user-facing help or workflow doc instructs a reader to run `aw run <leaf>`.
  - Execution state: performed

- [x] E-08 Update the tests that invoke the verb to the new spelling: `tests/test_run_recovery_cli.py`
      (31 `"run"` invocations), `tests/test_run_evidence_completion.py` (12), `tests/test_run_viewer.py`
      (2), and the completion expectations in `tests/test_completion.py:269,297,381`. Retain at least
      one test asserting the E-05 normal-parser rejection and nonzero exit for a moved viewer leaf, so
      the removal stays covered. ALSO settle the COMPLETION surface (PR-005, F-7), which the plan did not mention:
      `completion.py:632` routes target completion for `words[1] in ("run", "runs")` as one surface, and
      `tests/test_completion.py` asserts `run` is among the offered subcommands. Decide explicitly
      whether the retired noun (a) still completes, so a user tab-completing `aw run ` is guided to the
      stub message, or (b) disappears from completion entirely. Either is defensible; leaving it
      undecided means the test expectations and the parser can disagree silently.
      DO NOT "fix" the pre-existing failure in `tests/test_run_viewer.py` (F-8) while editing that file.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: default suite shows the SAME failure SET as your own pre-change measurement and no
    new ones, with no reference to a live `aw run <leaf>` path; the completion decision is implemented and
    asserted. (Corrected 2026-09-03: this said "the SAME single pre-existing failure", which is no longer
    true - the set is machine-dependent and currently EMPTY here; see F-9 and backlog `agrlvw`.)
  - Execution state: performed

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
| F-8 | A pre-existing suite failure sits in a file this plan edits. SUPERSEDED BY F-9; retained for the record. | `tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_issues_flag` failed at the review HEAD (reproducible in isolation), introduced by `20caf1c`. Baseline as measured on 2026-08-29 was 2883 tests / 1 failed / 7 skipped, not the plan's original `2865 passed, 3 skipped, 4 xfailed`. |
| F-9 | **BASELINE RE-MEASURED 2026-09-03 AND BOTH EARLIER NUMBERS ARE STALE. Use this row, not F-8.** The suite has grown by roughly 42 percent since review and is now fully GREEN on this machine, and F-8's named failure is green too. Critically, the failure it describes is NOT a fixed bug but an ENVIRONMENT-DEPENDENT one, so the executor must not treat either result as the invariant. | Measured at HEAD `34cefa8b`: bare `python3 -m pytest` reports `4092 passed, 3 skipped, 4 xfailed in 36.07s`; `--junitxml` `testsuite` attributes are `tests=4099 failures=0 errors=0 skipped=7`, against review's 2883/1/7. `python3 -m pytest tests/test_run_viewer.py -o addopts="" -q -k issues_flag` -> `2 passed, 40 deselected`. THE REASON IT MOVED: backlog `agrlvw` (open, high, filed 2026-09-02) measures that 15 tests in `tests/test_run_viewer.py` read gitignored live run data under `.aw/records/runs/`, so they pass only on a machine that has actually run the driver and fail in every fresh clone and in CI. So this file's pass/fail set is a property of the machine, not of this plan. |
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
2. The full default suite with the actual counts pasted. BASELINE RE-MEASURED 2026-09-03 AT HEAD
   `34cefa8b` (F-9); BOTH earlier figures are stale and must not be used: **4099 tests, 0 failed,
   0 errors, 7 skipped** from the `--junitxml` `testsuite` attributes, which the bare run reports as
   `4092 passed, 3 skipped, 4 xfailed`. (Review's 2883/1/7 and the plan's original 2865 are both
   superseded.) Read the counts from `--junitxml`, because the repo's `addopts` uses `-q -n auto` and the
   xdist summary line is suppressed. RUN THE SUITE BARE, as `python3 -m pytest --junitxml=<f>`: do NOT
   add `-n0` (it disables xdist and makes the run several times slower here), do NOT add a second `-q`
   (it compounds into `-qq` and suppresses the summary), and do NOT add `-p no:randomly` (it switches off
   the order randomization that surfaces order-dependence bugs). RE-MEASURE THE BASELINE YOURSELF BEFORE
   STARTING rather than trusting this number: the suite grew about 42 percent between review and this
   re-measurement, and it will keep moving.
3. THE FAILURE SET IS MACHINE-DEPENDENT, WHICH IS THE HONEST INVARIANT (F-9, and the reason step 2's
   number is a snapshot rather than a contract). Do not encode "zero failures" as the expectation either:
   backlog `agrlvw` measures 15 tests in `tests/test_run_viewer.py` reading gitignored live run data under
   `.aw/records/runs/`, so they pass on a machine that has run the driver and fail in every fresh clone
   and in CI. `tests/test_run_viewer.py` is IN this plan's Scope-Paths (E-08), so the required discipline
   is unchanged even though the numbers moved: capture the failure set BEFORE starting, confirm it is
   IDENTICAL at the end, explain any difference rather than absorbing it, and do NOT adopt or "fix" a
   failure in that file - it belongs to `agrlvw`, not to this rename.
4. HISTORICAL, SUPERSEDED BY F-9, retained so the reasoning is auditable rather than silently rewritten.
   As measured at the review HEAD, the pre-existing failure had to be handled honestly:
   `tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_issues_flag` FAILS at HEAD
   (`AssertionError: 'Artifact & Status Discrepancies' not found in 'no artifact or status
   discrepancies found'`), reproducible in isolation, introduced by commit `20caf1c`
   (`feat(run_viewer): add discrepancy table, Issue column, and --issues/-i flag`) - i.e. it predates
   this plan. It matters here because `tests/test_run_viewer.py` is IN this plan's Scope-Paths (E-08),
   so the executor will be editing the very file that is red. Required: paste the failure BEFORE
   starting, do NOT fix it (out of scope, not this plan's bug), do NOT let it be mistaken for
   regression, and confirm at the end that the failure set is still exactly this one test. If it
   disappears or multiplies, STOP and report.
5. E-02's duplicate-output test demonstrated FAILING at pre-change HEAD and passing after, pasting
   both runs, plus evidence it is stable (run it twice). A guard never seen to fail is not evidence.
6. Manual confirmation that bare `aw runs`, `aw runs <run-id>`, and `aw runs <set-id>` still render the
   viewer table unchanged, by diffing against output captured before the change WITH volatile
   `runtime:`/elapsed fields masked (see E-02: raw output differs run-to-run for live processes).
7. The E-03 ambiguity rule exercised: a target whose name equals a leaf name routes as the documented
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
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-03: retain no compatibility responses. Once the nine read-only leaves move to `aw runs`, remove their old `aw run` parser registrations immediately, so old spellings fail through normal argument parsing. `aw run` remains the writing and dispatch noun; only the old viewer leaves disappear. This avoids silent forwarding and avoids an additional compatibility surface.

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

- [x] V-01 validates E-01
  - Required evidence: paste the characterization test run showing all twelve leaves asserted, plus
    the `git stash`-style demonstration that it passes at pre-change HEAD unmodified. List the twelve
    leaf names actually covered, so a missing leaf is visible.
  - Observed evidence: New file `tests/test_run_noun_split.py` (fixture-based, so its verdict is a
    property of the CODE, not the machine - deliberately NOT added to `tests/test_run_viewer.py`,
    which reads live gitignored run data per backlog `agrlvw`).

    `python3 -m pytest tests/test_run_noun_split.py -o addopts="" -v` ->
    ```
    tests/test_run_noun_split.py::DuplicateRenderingGuardTests::test_guard_is_stable_across_repeated_runs PASSED [  6%]
    tests/test_run_noun_split.py::DuplicateRenderingGuardTests::test_exactly_one_spelling_renders_the_viewer_table PASSED [ 12%]
    tests/test_run_noun_split.py::DuplicateRenderingGuardTests::test_runs_list_is_a_declared_alias_of_the_bare_viewer PASSED [ 18%]
    tests/test_run_noun_split.py::DuplicateRenderingGuardTests::test_no_two_spellings_render_identical_viewer_output PASSED [ 25%]
    tests/test_run_noun_split.py::LeafSurfaceCharacterizationTests::test_leaf_name_as_viewer_target_is_reachable_via_the_escape_hatch PASSED [ 31%]
    tests/test_run_noun_split.py::LeafSurfaceCharacterizationTests::test_viewer_leaves_parse_and_keep_their_exit_class_under_runs PASSED [ 37%]
    tests/test_run_noun_split.py::LeafSurfaceCharacterizationTests::test_writer_leaves_parse_and_keep_their_exit_class_under_run PASSED [ 43%]
    tests/test_run_noun_split.py::LeafSurfaceCharacterizationTests::test_runs_repair_verb_still_routes PASSED [ 50%]
    tests/test_run_noun_split.py::LeafSurfaceCharacterizationTests::test_leaf_specific_flags_still_bind PASSED [ 56%]
    tests/test_run_noun_split.py::LeafSurfaceCharacterizationTests::test_viewer_flags_bind_after_a_positional_target PASSED [ 62%]
    tests/test_run_noun_split.py::LeafSurfaceCharacterizationTests::test_bare_viewer_argv_shapes_all_render PASSED [ 68%]
    tests/test_run_noun_split.py::LeafSurfaceCharacterizationTests::test_all_twelve_leaves_are_covered_by_this_characterization PASSED [ 75%]
    tests/test_run_noun_split.py::MovedLeafRemovalTests::test_bare_run_help_advertises_only_the_writing_leaves PASSED [ 81%]
    tests/test_run_noun_split.py::MovedLeafRemovalTests::test_the_writing_noun_still_works PASSED [ 87%]
    tests/test_run_noun_split.py::MovedLeafRemovalTests::test_every_moved_leaf_is_rejected_under_the_old_noun PASSED [ 93%]
    tests/test_run_noun_split.py::MovedLeafRemovalTests::test_rejection_performs_no_ledger_write PASSED [100%]
    ============================== 16 passed in 1.96s ==============================
    ```

    THE TWELVE LEAVES COVERED, each with a PINNED EXIT CLASS on the fixture ledger
    (`LeafSurfaceCharacterizationTests.EXPECTED_EXIT`), so a missing leaf is visible and is itself a
    test failure (`test_all_twelve_leaves_are_covered_by_this_characterization` asserts the covered
    set EQUALS the declared split): `show`=1, `status`=1, `next`=3, `resume`=0, `evidence`=0,
    `verify-ledger`=1, `decisions`=2, `questions`=2, `start`=2, `record`=2, `cancel`=0, `finalize`=1.
    Plus `list` (the 13th parser leaf), whose class is the VIEWER's (exit 0) rather than the
    single-`target` leaf shape, asserted separately.

    PRE-CHANGE DEMONSTRATION (the point of a characterization test). The file was written and run
    FIRST against the pre-change spelling (`aw run <leaf>`), by copying it to
    `tests/test_prechange_char_tmp.py` with only the noun rewritten. Result at pre-change HEAD:
    `6 failed, 9 passed`. Every one of the 6 was an INTENDED post-split delta, not a defect in the
    net: the 2 duplicate-guard tests (`run list`/`runs` collision still present), the 2 removal tests
    (`aw run show` still worked), the leaf-name/escape-hatch test (`aw runs status` still routed to
    the viewer), and the twelve-leaf coverage assertion (`list` was a `run` leaf, not a `runs` one).
    The 9 that PASSED unmodified are the exit-class and flag-binding assertions, i.e. the actual
    behaviour-preservation net, which passed identically before and after the move. The temp file was
    then deleted; the surviving file asserts the post-split spelling.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste TWO runs of the duplicate-detection test: one at pre-change HEAD showing
    it FAIL and naming the `run list` / `runs` pair, and one after E-04 showing it pass. A guard that
    was never observed failing is not accepted as evidence. PLUS the STABILITY proof (PR-003): show the
    test uses a fixture ledger and/or masks volatile fields, and paste two consecutive passing runs.
    State explicitly which fields are normalized, citing the measured `runtime:`-only divergence
    (2 of 1031 lines) that makes a raw byte comparison flaky.
  - Observed evidence: RUN 1, AT PRE-CHANGE HEAD, FAILING AND NAMING THE PAIR
    (`python3 -m pytest tests/test_prechange_char_tmp.py -o addopts="" -q -k DuplicateRenderingGuard`):
    ```
    F.F                                                                      [100%]
    _ DuplicateRenderingGuardTests.test_no_two_spellings_render_identical_viewer_output _
    E               AssertionError: duplicate rendering: `aw runs` and `aw run list` produce identical output; one job must have one name
    _ DuplicateRenderingGuardTests.test_exactly_one_spelling_renders_the_viewer_table _
    E       AssertionError: Lists differ: [('runs',), ('run', 'list'), ('runs', 'list')] != [('runs',)]
    E       First extra element 1:
    E       ('run', 'list')
    ```
    So the guard was OBSERVED firing, and it named the exact historical pair.

    RUN 2, AFTER E-04, PASSING, run TWICE consecutively for the stability proof
    (`python3 -m pytest tests/test_run_noun_split.py -o addopts="" -q -k DuplicateRenderingGuard`):
    ```
    ....                                                                     [100%]
    4 passed, 12 deselected in 0.65s
    --- second consecutive run (stability) ---
    ....                                                                     [100%]
    4 passed, 12 deselected in 0.61s
    ```

    FLAKINESS CONSTRAINT SATISFIED TWO WAYS, as PR-003 requires. (1) FIXTURE, not live data: the test
    class extends `_LedgerFixture`, a `tempfile.TemporaryDirectory` repo holding one synthetic ledger
    and one `state.json` run dir with NO live pids, and every invocation passes `--dir <fixture>`.
    (2) NORMALIZATION on top of that, in `_normalize()`, masking exactly: `runtime:`/`elapsed:`
    values, absolute timestamps (`YYYY-MM-DDTHH:MM(:SS)Z`), `pid:` values, and bare duration tokens
    (`6d 5h 56m 28s`). This is required because the measured divergence between the two spellings was
    `runtime:`-only (2 of 1031 lines, `runtime: 31m 19s` vs `31m 21s`), i.e. a raw byte comparison of
    live output would have failed intermittently for a reason unrelated to the duplication.
    `test_guard_is_stable_across_repeated_runs` additionally asserts the normalized rendering is
    identical across two calls in one process.

    SCOPE NOTE on what the guard now watches: `("runs","list")` was REMOVED from the candidate set,
    because it is an INTENTIONAL alias of the bare viewer (one renderer, one registration, one shared
    flag parent) rather than the cross-noun duplicate this guard exists to catch. It is instead pinned
    EQUAL by the new `test_runs_list_is_a_declared_alias_of_the_bare_viewer`, so it cannot silently
    diverge either. The retired spellings (`run list`, `run runs`, `run summary`, `run viewer`) remain
    in the candidate set and are asserted to be REJECTED rather than rendering.
  - Result: pass

- [x] V-03 validates E-03
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
  - Observed evidence: EXIT CODES, NINE MOVED LEAVES, new spelling vs pre-change old spelling, same
    fixture ledger (`/tmp/.../fx/.aw/records/runs/run-abcdef1234/ledger.jsonl`). Pre-change column
    captured by stashing only the four source files and re-running:
    ```
    AFTER  (aw runs <leaf>)          BEFORE (aw run <leaf>)
    aw runs show           -> rc=1   aw run show            -> rc=1
    aw runs status         -> rc=1   aw run status          -> rc=1
    aw runs next           -> rc=3   aw run next            -> rc=3
    aw runs resume         -> rc=0   aw run resume          -> rc=0
    aw runs decisions      -> rc=2   aw run decisions       -> rc=2
    aw runs questions      -> rc=2   aw run questions       -> rc=2
    aw runs evidence       -> rc=0   aw run evidence        -> rc=0
    aw runs verify-ledger  -> rc=1   aw run verify-ledger   -> rc=1
    ```
    EQUAL for all eight ledger leaves. The ninth moved leaf, `list`, is the viewer and is covered by
    the zero-diff rendering comparison below plus `test_runs_list_is_a_declared_alias_of_the_bare_viewer`.

    FOUR RETAINED WRITERS still work UNCHANGED under `aw run` (pre-change run, same fixture):
    `aw run start -> rc=2`, `aw run record -> rc=2`, `aw run cancel -> rc=0`, `aw run finalize -> rc=1`;
    post-change they are asserted by `test_writer_leaves_parse_and_keep_their_exit_class_under_run`
    (start=2, record=2, cancel=0, finalize=1) and by `test_the_writing_noun_still_works`
    (`aw run cancel` prints `Cancelled run`). They were NOT moved: `discover_parser_leaves` reports
    `['run cancel', 'run finalize', 'run record', 'run start']` under `run`.

    PARSER LEAF INVENTORY after the split (from `command_surface.discover_parser_leaves`):
    ```
    ['run cancel', 'run finalize', 'run record', 'run start',
     'runs decisions', 'runs evidence', 'runs list', 'runs next', 'runs questions',
     'runs resume', 'runs show', 'runs status', 'runs verify-ledger']
    ```

    ON "CONFIRM `aw runs` HAS NO SUBPARSERS": THIS PART OF THE PLAN'S PREMISE IS FALSIFIED, and the
    plan is wrong on the mechanism though right on the split. `aw runs` DOES have subparsers - nine of
    them - and it must. The ruling's claim that "with only viewers under `aw runs`, that parser needs
    NO subparsers" does not hold, because the nine viewers are NOT flag-compatible with the bare
    viewer: each takes a REQUIRED single positional `target` plus leaf-specific flags
    (`--workflow`/`--actor`/`--step`/`--state`/`--reason`), whereas the bare viewer takes
    `targets nargs="*"` plus thirteen filter/format flags. So `aw runs` must carry BOTH shapes, which
    is exactly the combination PR-001 proved plain argparse cannot express. I RE-VERIFIED PR-001 at
    this HEAD on CPython 3.14: with `targets nargs="*"` plus a `show` subparser, `["RUN1"]`,
    `["RUN1","RUN2"]` and `["show","RUN1"]` all raise
    `argparse.ArgumentError: argument cmd: invalid choice: 'RUN1'`; only empty argv parses.

    ROUTING MECHANISM ACTUALLY IMPLEMENTED (named, as required): a custom
    `_ViewerOrLeafSubParsersAction(argparse._SubParsersAction)` in `cli.py`, paired with a
    `_RunsArgumentParser(_AwArgumentParser)` that suppresses `_check_value` for that action, and a
    `_RunsTargetsPlaceholderAction` for the `targets` positional. If the first positional exactly
    matches a registered leaf name it delegates to that leaf's subparser (native help, native usage
    errors, native flag validation); otherwise it hands the whole positional list to a sibling VIEWER
    parser owning `targets` + the shared viewer-flag parent. Chosen over positional routing (the route
    `aw runs repair` takes) because only a REAL subparser is visible to
    `command_surface.discover_parser_leaves`, which is a hard precondition for E-06 not to register as
    declaration/parser drift. Recorded with alternatives as DECISION 01-0soncw-D1.

    TWO ORDERING/OVERWRITE DEFECTS FOUND BY THIS EVIDENCE PASS AND FIXED (both would have silently
    broken a surface, and both are now regression-tested):
      1. REGISTRATION ORDER IS LOAD-BEARING. With `targets` registered BEFORE the routing action,
         argparse consumed positionals in registration order and the greedy `targets` swallowed the
         leaf name, so `aw runs show <t>` reached the action as `['<t>']` and silently rendered the
         VIEWER instead of dispatching `show`. The action is now registered first.
      2. THE PLACEHOLDER MUST NOT CLOBBER. Because the routing action has `nargs=PARSER`, the
         `targets` positional is always invoked afterwards with an empty list; assigning it blindly
         erased the targets the viewer parser had just resolved, so `aw runs RUN1` reached the viewer
         with `targets=[]` (i.e. "show ALL runs", silently ignoring the requested one).
         `_RunsTargetsPlaceholderAction` now writes only when it has values or the dest is unset.

    ALL FOUR ARGV SHAPES ROUTE CORRECTLY (parsed namespaces):
    ```
    ['runs', 'show', '/nope']                     cmd='show'      targets=[]               target='/nope'
    ['runs', 'RUN1']                              cmd=None        targets=['RUN1']         target=None
    ['runs']                                      cmd=None        targets=None             target=None
    ['runs', 'RUN1', 'RUN2']                      cmd=None        targets=['RUN1','RUN2']  target=None
    ['runs', 'list', 'X']                         cmd='list'      targets=['X']            target=None
    ['runs', 'decisions', 'R', '--workflow', 'w'] cmd='decisions' targets=[]               target='R'   (--workflow bound)
    ['runs', 'RUN1', '--dir', '/x', '--issues']   cmd=None        targets=['RUN1']         dir='/x' issues=True
    ```
    Set-id shape and flag-after-target binding are additionally asserted by
    `test_bare_viewer_argv_shapes_all_render` (bare / run-id / set-id / multi) and
    `test_viewer_flags_bind_after_a_positional_target`.

    NEGATIVE CASE + ESCAPE HATCH (`test_leaf_name_as_viewer_target_is_reachable_via_the_escape_hatch`):
    `aw runs status` (no target) routes to the LEAF and fails with the LEAF's usage
    (`agent-workflows runs status: error: the following arguments are required: target`), which is the
    documented ambiguity rule. `aw runs -- status` reaches the VIEWER. The hatch could NOT be
    implemented inside the action, because argparse STRIPS `--` while splitting argv, so the token is
    indistinguishable from a leaf name by then (measured: it reached the `status` leaf and demanded a
    target); it is therefore handled pre-parse in `_dispatch`, next to the existing
    `aw runs repair --help` interception. The PRE-EXISTING positionally-routed mutating verb still
    works: `aw runs repair <id>` -> `nothing to repair` (`test_runs_repair_verb_still_routes`).

    BARE-VIEWER RENDERING, before vs after, diffed against captures taken pre-change over the real
    95-run records dir with volatile fields masked. Both `aw runs` and `aw run list` produced 1544
    lines pre-change (confirming F-1's duplication). After masking `runtime:`/`elapsed:`/timestamps/
    pids, the only residual differences were the cost/token counters of THIS VERY RUNNING TURN; the
    changed row is `20260829-runnamecollapse-01-0soncw` (i.e. this turn's own live accounting, which
    advanced between the two captures). With those live counters ALSO masked the diff is empty:
    ```
    === bare viewer before vs after, with LIVE COUNTERS also masked ===
    ZERO DIFF (rendering identical; only this turn's own live cost/token counters moved)
    === proof the drift is THIS run: which run ids changed? ===
    20260829-runnamecollapse-01-0soncw
    ```
    `aw runs --last 3` behaves identically (same turn-local counter drift only), and post-change
    `aw runs list` is byte-identical to bare `aw runs` (`ZERO DIFF`).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the output of `aw run list` after the change (expect normal argument-parser
    rejection, not a table; `list` is one of the NINE moved leaves) and confirm exactly one spelling
    renders the viewer, by showing `grep -n` of the alias tuple in `run_cli.py` with
    `list`/`summary`/`viewer` gone.
  - Observed evidence: `aw run list` after the change - normal argument-parser rejection, NOT a table:
    ```
    usage: agent-workflows run [-h] [--no-color] [--agent] [--json]
                               {start,record,cancel,finalize} ...
    agent-workflows run: error: argument run_command: invalid choice: 'list' (choose from 'start', 'record', 'cancel', 'finalize')
    Next  aw run --help
    ```
    ALIAS TUPLE GONE. `grep -n '"list", "runs", "summary", "viewer"' agent_workflows/run_cli.py`
    returns only line 71, which is the explanatory COMMENT recording the removal, not code:
    ```
    71:    The `("list", "runs", "summary", "viewer")` viewer aliases that used to be handled here are GONE
    ```
    The dispatch branch `if sub in ("list", "runs", "summary", "viewer"): return run_viewer.run_viewer_cli(args)`
    no longer exists in `run_cli.run_cli`. As the plan requires this to be stated rather than
    mis-reported: only `list` was ever a REGISTERED parser leaf; `summary` and `viewer` were
    unreachable dead branches (verified pre-change: `aw run summary` was an argparse "invalid choice"),
    so removing them is dead-branch cleanup, NOT the retirement of three commands.

    EXACTLY ONE SPELLING RENDERS THE VIEWER. `grep -n 'run_viewer_cli' agent_workflows/cli.py
    agent_workflows/run_cli.py`:
    ```
    agent_workflows/cli.py:9162:        return run_viewer.run_viewer_cli(args_ns)   # the `--` escape-hatch path
    agent_workflows/cli.py:9373:        return run_viewer.run_viewer_cli(args)      # bare `aw runs` / `aw runs list`
    ```
    Zero call sites remain in `run_cli.py`. `test_exactly_one_spelling_renders_the_viewer_table`
    asserts that of the five historical spellings only bare `aw runs` renders, and E-02's guard passes.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `aw run show <target>; echo rc=$?` showing normal argument-parser rejection
    and a NONZERO rc. Additionally show that no ledger write occurred: paste the target dir listing
    before and after, identical.
  - Observed evidence: `aw run show <fixture-ledger> --dir <fixture>; echo rc=$?`:
    ```
    rc=2
    agent-workflows run: error: argument run_command: invalid choice: 'show' (choose from 'start', 'record', 'cancel', 'finalize')
    Next  aw run --help
    ```
    NONZERO (2), and the rejection comes from NORMAL argument parsing - it is argparse's own
    invalid-choice error, not a hand-written stub message and not a silent forward.

    NO LEDGER WRITE. Directory listing plus `sha256sum` of the ledger captured immediately before and
    after the rejected invocation; `diff` of the two captures:
    ```
    IDENTICAL - no write occurred
    ```
    Also covered by `test_rejection_performs_no_ledger_write` (compares ledger bytes AND the dir
    listing across the rejected call) and, for all nine leaves, by
    `test_every_moved_leaf_is_rejected_under_the_old_noun`, which asserts nonzero exit and the literal
    `invalid choice` for each.

    THE WRITING NOUN IS UNCHANGED: `aw run cancel <ledger>` -> rc=0, `Cancelled run run-abcdef1234`
    (`test_the_writing_noun_still_works`). `aw run` is NOT retired, so the namespace the approved
    `runprofile` Set extends with `aw run as <profile>` remains available.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_cli_conformance_matrix.py -q` green, plus
    `grep -c 'command="runs' agent_workflows/command_surface.py` showing the CORRECTED count of 10 (the
    NINE moved read-only leaves plus the bare viewer; not 13 - OQ-03's ruling keeps the four writing
    leaves under `aw run`, so their declarations stay `command="run ..."`). Also paste the count for
    `command="run` proving the four writers are still declared there. The original wording said 13 (twelve leaves plus the
    previously missing top-level `runs`) and `grep -c 'command="run '` showing 0.
  - Observed evidence: `python3 -m pytest tests/test_cli_conformance_matrix.py -o addopts="" -q` ->
    ```
    FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_no_undeclared_parser_leaves
    FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_every_declared_leaf_gets_a_full_scenario_row_set
    2 failed, 9 passed in 119.37s (0:01:59)
    ```
    NOT GREEN, and this is the PRE-EXISTING failure the plan itself documents (the 42-undeclared-leaf
    debt, explicitly out of scope). Both failures are present at the pre-change baseline and are
    UNCHANGED by this work. Crucially the run-family contribution to that debt went DOWN, not up: the
    undeclared-leaf set shrank from 65 to 63 because `run list` and `runs` both left it, and
    `find_undeclared_leaves` now reports ZERO run-family entries (`[]`). The third, related test
    `test_declared_absent_leaves_are_only_the_known_prompts_family` PASSES.

    COUNTS. `grep -c 'command="runs' agent_workflows/command_surface.py` -> **9**;
    `grep -c 'command="run ' agent_workflows/command_surface.py` -> **4**:
    ```
    command="runs list"        command="run start"
    command="runs show"        command="run record"
    command="runs evidence"    command="run cancel"
    command="runs verify-ledger"  command="run finalize"
    command="runs next"
    command="runs resume"
    command="runs status"
    command="runs decisions"
    command="runs questions"
    ```
    The `command="run ` count of 4 is EXACTLY as V-06 requires (the four writers still declared there).

    THE `runs` COUNT IS 9, NOT THE 10 THIS V-ITEM PREDICTED, and the difference is substantive rather
    than an oversight, so it is reported instead of massaged. V-06 expected "the NINE moved read-only
    leaves plus the bare viewer", and E-06 asked for "the missing top-level `runs` declaration". I DID
    add that root declaration first; it BROKE
    `test_declared_absent_leaves_are_only_the_known_prompts_family` with
    `declaration/parser drift changed: ['prompts set', 'runs']`. The mechanism: `discover_parser_leaves`
    (`command_surface.py:1262-1280`) yields a path only for a parser with NO subparsers, so a family
    ROOT is never a leaf, and `tests/conformance_matrix.py:346` files any declaration absent from the
    leaf set as drift against a set pinned to `{"prompts set"}`. The convention confirms it: NO family
    root is declared anywhere in the inventory - `aw ipd` (bare, renders the board), `aw specs` and
    `aw backlog` are all bare-invokable roots and none has a declaration (`command="ipd"` does not
    exist). So F-5's "aw runs is undeclared" is TRUE but is the normal state of a root, not a defect
    peculiar to `runs`. RESOLUTION: the viewer's contract is carried by `runs list`, a REAL leaf that is
    the bare viewer's exact alias (same renderer, same shared flag parent), carrying the full viewer
    flag set; the root is left undeclared per convention, with a comment at the declaration site
    recording why so a later reader does not "fix" it back. Recorded as DECISION 01-0soncw-D4.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `grep -rn 'aw run ' --include='*.md' .` filtered to TRACKED files
    (excluding `.aw/worktrees/`, `.aw/records/runs/`, `opencode-recovery/`, and other agents' lanes)
    showing zero live instructions to use `aw run <leaf>`; and `grep -n 'aw run' agent_workflows/run_cli.py`
    showing the docstring and usage string updated.
  - Observed evidence: `grep -rn 'aw run ' --include='*.md' .` over TRACKED files (excluding
    `.aw/worktrees/`, `.aw/records/runs/`, `opencode-recovery/`, and the historical records trees
    `.aw/records/{research,plans,backlog,specs,walkthroughs,reviews,comms}/`, which are immutable
    history and must not be rewritten):
    ```
    ./docs/verification.md:37:aw run finalize <run-id-or-path>
    ./docs/verification.md:40:`aw runs show` prints the completion predicates and their state. `aw run finalize` records
    ```
    ZERO live instructions to use `aw run <moved-leaf>`. The only two remaining `aw run ` hits both
    name `finalize`, a WRITER that CORRECTLY stays under `aw run`; each was executed and confirmed to
    dispatch.

    `grep -n 'aw run' agent_workflows/run_cli.py` - module docstring and usage string updated: the
    docstring now documents the split (`aw runs` READS: show/status/next/resume/evidence/
    verify-ledger/decisions/questions/list; `aw run` WRITES: start/record/cancel/finalize, with the
    note that `next`/`resume` only reconstruct state and report), and the fallback usage string is now
    two lines:
    ```
    102:        "usage: aw run {start|record|cancel|finalize} <run-id-or-path> "
    104:        "       aw runs {show|status|next|resume|evidence|verify-ledger|decisions|questions|list} "
    ```
    `cli.py`'s help dictionary was also corrected: the `"run"` entry now describes the writing verbs,
    a NEW `"runs"` entry describes the reading surface, and the three `"run show"`/`"run evidence"`/
    `"run verify-ledger"` keys became `"runs ..."`. The `run` parser's own help/description/epilog were
    rewritten (it previously still advertised 'show'/'evidence'/'verify-ledger' as its own commands),
    and `aw run --help` now prints only `{start,record,cancel,finalize}`. Asserted by
    `test_bare_run_help_advertises_only_the_writing_leaves`.

    TWO SCOPE FINDINGS, both reported rather than silently absorbed:
      1. THE PLAN'S DOC CLAIM WAS WRONG. It states `exec-set.md` is "the only tracked workflow doc
         citing `aw run <leaf>`". Measured: SEVEN files under `docs/` carried 21 such citations
         (`docs/evidence.md` 6, `docs/troubleshooting.md` 5, `docs/walkthroughs/incomplete-run.md` 3,
         `docs/recovery.md` 2, `docs/verification.md` 2, `docs/walkthroughs/evidence-inspection.md` 2,
         `docs/walkthroughs/recovery.md` 1), 19 naming a MOVED leaf. Leaving them would have shipped
         three step-by-step walkthroughs telling readers to run commands that now exit 2, and would
         have made this V-item unsatisfiable. An anchored regex rewrote ONLY the moved-leaf spellings,
         deliberately preserving both `aw run finalize` citations. `docs/` is outside Scope-Paths;
         recorded as DECISION 01-0soncw-D3.
      2. A TEST HARD-CODED THE OLD SPELLING. `tests/test_exec_set_workflow.py::ExecSetCliSurfaceV02::
         test_help_advertises_only_real_commands` asserted `exec-set.md` CONTAINS `aw run status|
         decisions|questions`, so the required E-07 edit broke it. Its stated purpose is that "every
         command the shipped help text names actually dispatches", so asserting the stale spelling
         would have inverted its meaning. Updated to the new spellings, PLUS strengthened: it now
         asserts the retired spellings are ABSENT and that each advertised leaf really exists on the
         live parser via `discover_parser_leaves`, so a future rename cannot leave the doc stale while
         the test stays green. Outside Scope-Paths; recorded as DECISION 01-0soncw-D2.
         `python3 -m pytest tests/test_exec_set_workflow.py -o addopts="" -q` -> `14 passed`.

    Every rewritten command was verified to DISPATCH rather than be rejected:
    ```
    aw runs show           dispatches ok
    aw runs status         dispatches ok
    aw runs evidence       dispatches ok
    aw runs verify-ledger  dispatches ok
    aw runs resume         dispatches ok
    aw run finalize        dispatches ok
    ```
    No `.aw/worktrees/*/` lane copy was touched.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the full default suite result with actual counts read from `--junitxml`
    (the `-q -n auto` addopts suppress the summary line). BASELINE RE-MEASURED 2026-09-03 AT HEAD
    `34cefa8b` (F-9): **4099 tests / 0 failed / 0 errors / 7 skipped**, reported by the bare run as
    `4092 passed, 3 skipped, 4 xfailed`. Review's 2883/1/7 is STALE and must not be compared against.
    RE-MEASURE THE BASELINE YOURSELF IMMEDIATELY BEFORE STARTING and paste that measurement too, because
    the suite grew about 42 percent between review and this re-measurement and will keep moving; compare
    your final run against YOUR OWN pre-change measurement, not against a number written here.
    DO NOT assert "zero failures" as the invariant either. The invariant is that the failure SET is
    UNCHANGED, because it is machine-dependent: backlog `agrlvw` measures 15 tests in
    `tests/test_run_viewer.py` reading gitignored live run data under `.aw/records/runs/`, so they pass on
    a machine that has run the driver and fail in every fresh clone and in CI. `test_run_viewer_cli_issues_flag`
    (F-8) is GREEN on this machine at this HEAD, which does NOT mean it was fixed. Paste the set before and
    after, state that nothing in that file was fixed or adopted, and explain any difference rather than
    absorbing it. Also paste the specific test asserting the deprecation stub's message and exit code, and
    the completion-surface assertion showing the E-08 decision (retired noun still completes, or does not)
    is implemented and tested.
  - Observed evidence: BASELINE RE-MEASURED MYSELF IMMEDIATELY BEFORE STARTING, as instructed, and the
    number written in this plan is STALE AGAIN. At my starting HEAD `6c8ea51a` in this lane, bare
    `python3 -m pytest --junitxml=<f>` reported `40 failed, 4089 passed, 3 skipped, 4 xfailed in 32.80s`
    with `--junitxml` `testsuite` attributes **`tests=4136 failures=40 errors=0 skipped=7`**. The plan's
    figure (4099 tests / 0 failed) does NOT reproduce here: this is a FRESH LANE WORKTREE with no
    `.aw/records/runs/` data of its own, which is exactly the machine-dependent condition F-9 and
    backlog `agrlvw` predict - 15 of the 40 failures are the `tests/test_run_viewer.py` set that reads
    gitignored live run data. So the plan's "currently EMPTY on this machine" is a property of the MAIN
    checkout, not of this lane.

    AFTER, same command, same lane: `32 failed, 4117 passed, 3 skipped, 4 xfailed in 29.23s`, junitxml
    **`tests=4156 failures=32 errors=0 skipped=7`** (+20 tests: 16 new in `tests/test_run_noun_split.py`
    plus 4 new completion assertions).

    FAILURE-SET COMPARISON, which is the honest invariant rather than a count:
    ```
    NEW FAILURES (my regressions) [0]:      <none>
    NEWLY PASSING [8]:
      - tests.test_awnaming_grammar_and_producers.* (7 tests)
      - tests.test_rename_ledger.CliEmissionTests::test_applied_plan_rename_appends_one_record
    ```
    ZERO regressions. The 8 that went red->green are EXPLAINED, not absorbed: none of those tests
    references the run surface at all (`grep -c 'aw run\|"run"\|"runs"'` -> 0 in both files), and they
    PASS AT PRE-CHANGE HEAD when run in isolation (verified by stashing my four source files:
    `25 passed`). They are ORDER-DEPENDENT flakes surfaced by `pytest-randomly`, which the repo enables
    deliberately. Confirmed by three consecutive randomized full runs AFTER my change:
    ```
    run1: 32 failures; new-vs-baseline: NONE
    run2: 32 failures; new-vs-baseline: NONE
    run3: 32 failures; new-vs-baseline: NONE
    UNION of new failures across 3 randomized runs: NONE
    FLAKY (differ between runs): <none>
    ```
    So the post-change set is stable at 32 and is a strict subset of the pre-change set.

    NOTHING IN `tests/test_run_viewer.py` WAS FIXED OR ADOPTED. Its failure set is byte-identical to my
    own pre-change measurement: baseline 15, after 15, `newly failing: none`, `newly passing: none`. I
    edited that file only to migrate 2 invocations to the new spelling (E-08) and did not touch the 15
    live-data tests, which belong to backlog `agrlvw`.

    IN-SCOPE FILES TOGETHER (`test_run_recovery_cli.py test_run_evidence_completion.py
    test_run_viewer.py test_completion.py test_cli_conformance_matrix.py test_run_noun_split.py
    test_exec_set_workflow.py`): `17 failed, 249 passed, 2 skipped`, and all 17 are the documented
    pre-existing failures - 15 in `tests/test_run_viewer.py` (`agrlvw`) and 2 in
    `tests/test_cli_conformance_matrix.py` (the undeclared-leaf debt). The four files whose spellings
    were migrated are fully green on their own: `tests/test_run_recovery_cli.py` +
    `tests/test_run_evidence_completion.py` -> `99 passed`; `tests/test_completion.py` ->
    `84 passed, 2 skipped`; `tests/test_exec_set_workflow.py` -> `14 passed`.

    E-05 REMOVAL COVERAGE (the plan asks for "the specific test asserting the deprecation stub's message
    and exit code"; per OQ-01's 2026-09-03 resolution there is NO stub, so the covering test asserts
    NORMAL-PARSER REJECTION instead): `MovedLeafRemovalTests::test_every_moved_leaf_is_rejected_under_the_old_noun`
    asserts nonzero exit + literal `invalid choice` for all nine moved leaves;
    `test_rejection_performs_no_ledger_write` asserts no durable effect.

    COMPLETION-SURFACE DECISION IMPLEMENTED AND TESTED (E-08's explicitly-required choice). DECIDED:
    the retired noun STILL COMPLETES, but completes its OWN real surface rather than targets it can no
    longer accept. Before, `completion.py:675` treated `run` and `runs` as ONE surface
    (`words[1] in ("run","runs")`), so `aw run <TAB>` offered Set ids and run ids - a shape `aw run` now
    rejects. Measured before/after:
    ```
    BEFORE: aw run <TAB>  -> ['apprvguard', 'ctlroot', 'hostcap', ...]      (targets - WRONG now)
    AFTER:  aw run <TAB>  -> ['cancel', 'finalize', 'record', 'start']      (its four writer leaves)
    AFTER:  aw runs <TAB> -> ['apprvguard', ..., 'decisions', 'evidence', 'list', 'next', ...] (leaves + targets)
    AFTER:  aw runs st<TAB> -> ['status']
    AFTER:  aw run start <TAB>  -> targets   (a real target slot)
    AFTER:  aw runs show <TAB>  -> targets   (a real target slot)
    ```
    A THIRD DEFECT WAS FOUND BY THE NEW TEST: `aw runs <TAB>` returned targets ONLY, hiding every
    viewer leaf name (`aw runs status` was untab-completable). Since that first slot is ambiguous by
    design, completion now offers BOTH leaf names and targets there. Asserted by four new tests in
    `tests/test_completion.py`: `test_run_noun_completes_its_writer_leaves_not_targets` (also asserts no
    retired leaf and no target leaks in), `test_run_writer_leaf_still_completes_targets_in_its_target_slot`,
    `test_runs_viewer_leaf_completes_targets_in_its_target_slot`, `test_runs_completes_its_viewer_leaves_too`.
    The pre-existing `test_set_id_from_front_matter_not_resolver` was retargeted from `aw run t` to
    `aw runs t`, since target completion now belongs to the reading noun.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (SPLIT the run surface by direction, moving the nine read-only
  inspection leaves onto `aw runs` while `aw run` survives as the WRITING noun). CORRECTED 2026-09-03: this
  line previously said the plan retires the `aw run` noun, which the maintainer ruling of 2026-08-31
  REVERSED (see OQ-03 and E-05); the stale wording contradicted both the title and E-05 and is fixed here
  rather than left to mislead an executor. The E-items are ordered sub-steps of that one split:
  characterize, move the viewers, de-duplicate, remove each old viewer leaf from `aw run`, then reconcile
  declarations/help/tests. No E-item changes ledger semantics or rendering.

This plan is `to-review` and requires explicit human approval before execution. It is a user-facing
CLI naming change: even though no production code shells `aw run <sub>` (F-4), a human's muscle memory
and any personal scripts do, which is why E-05 makes their failure explicit through normal command parsing rather than silently forwarding.

Execution contract:

1. Open questions: NO BLOCKING QUESTION REMAINS (corrected 2026-09-03; this item previously still called
   OQ-03 blocking). OQ-03 was RESOLVED by the maintainer on 2026-08-31, and its ruling is what dissolved
   the argparse blocker rather than working around it: because only viewers move to `aw runs`, that parser
   needs no subparsers, so nothing competes with its `targets nargs="*"`. OQ-02 was resolved by the same
   ruling. OQ-01 was resolved by the maintainer 2026-09-03: remove the old viewer leaves without a compatibility response.
2. Scope fence: touch ONLY the paths in `Scope-Paths`. Do NOT change ledger semantics, storage, or the
   viewer's rendering; do NOT fix any `tests/test_run_viewer.py` failure (F-8/F-9; that file's failures
   belong to backlog `agrlvw`, not to this rename) or the
   42 undeclared leaves; do NOT edit spec `25kzda`; do NOT touch `.aw/worktrees/*/` lane copies (other
   agents' checkouts). Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan or this orchestrator, and do NOT reimplement a rule another plan owns.
3. Honesty rule (HARD MUST): paste the ACTUAL runner output for every named command. A V-item whose
   command was not executed stays `Result: pending`. Report suite counts from `--junitxml` (the repo's
   `-q -n auto` addopts suppress the summary line). BASELINE RE-MEASURED 2026-09-03 AT HEAD `34cefa8b`
   (F-9): 4099 tests / 0 failed / 7 skipped. Review's 2883/1/7 is stale. Re-measure before starting and
   compare against your OWN pre-change measurement; run the suite BARE (`python3 -m pytest --junitxml=<f>`)
   without adding `-n0`, a second `-q`, or `-p no:randomly`.
4. NO SILENT FORWARDING: remove each of the NINE MOVED leaves from `aw run`; their old spellings must
   fail through normal command parsing with a nonzero exit. Do not make a moved leaf an invisible alias -
   silent aliasing is exactly how the E-04 duplicate survived unnoticed. `aw run` itself is NOT retired.
5. PRE-EXISTING FAILURE DISCIPLINE: capture the failure SET before starting and confirm it is IDENTICAL at
   the end. Do NOT expect a specific count: the set is machine-dependent (F-9, backlog `agrlvw`), and it is
   currently EMPTY on this machine at this HEAD while being 15-strong in a fresh clone. A newly green or
   newly red test in `tests/test_run_viewer.py` must be explained, not absorbed, and not fixed here.
6. Shared checkout: other agents work concurrently here. Commit only this plan's changed files,
   path-scoped (`git commit -m msg -- <path>`); verify with `git diff --cached --name-only` before each
   commit; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
7. Lifecycle move on completion: when every `V-*` item carries pasted evidence and
   `aw ipd lint --phase pre-transition` conforms, move this plan to `.aw/records/plans/executed/` via
   `aw ipd finalize`; do not hand-move it, and do not mark it executed on the strength of the execution
   checkmarks alone.
