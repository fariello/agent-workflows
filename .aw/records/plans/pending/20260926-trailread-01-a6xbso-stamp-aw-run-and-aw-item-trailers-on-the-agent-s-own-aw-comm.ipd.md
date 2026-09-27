# IPD: Stamp AW-Run and AW-Item trailers on the agent's own aw commit calls inside a run

- Date: 2026-09-26
- Kind: child
- Concern: THE AGENT'S OWN CODE COMMITS CARRY NO RUN-OWNERSHIP TRAILER, SO NOTHING DOWNSTREAM CAN ATTRIBUTE THEM. Measured at HEAD `61ef21d8`: of 188 commits since 2026-09-22 touching `agent_workflows/` or `tests/`, exactly ONE carries an `AW-Run` trailer (`8aabf15a`, IPD `hv9gar`), and across all refs 39 commits carry one, 38 of which are driver-side `closed by aw oc run` backlog-close commits touching only `.backlog.md` files. Agents are already told to commit through `aw commit` (runbook `oc_runipd.DEFAULT_RUNBOOK_TEXT` directive 4, its `agy_runipd` twin, and the `runner_shared` prompt text, commit `12ecd491`), and `aw commit` can already format trailers (`work_cmd._trailers_from_args` -> `git_commit_helper.run_item_trailers`). The gap is the CHANNEL: `_trailers_from_args` reads only `args.trailers`/`args.run_id`/`args.item_id6`, which no CLI flag sets, and the agent turn's environment (built by `runner_shared.pinned_child_env` in `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn`) carries no run or item id. Measured: `AW_RUN_ID=run-20260926T000000Z-1 aw commit --no-plan -m x -- f` in a scratch repo commits a message of exactly `x` with no trailer.
- Scope: IN: (a) two env-var NAME constants beside the trailer keys in `git_commit_helper` (`RUN_ID_ENV = "AW_RUN_ID"`, `ITEM_ID6_ENV = "AW_ITEM_ID6"`); (b) `work_cmd._trailers_from_args` falls back to those env vars ONLY when the namespace supplies neither `trailers` nor `run_id`/`item_id6`, validating the run id against the `new_run_id` shape and the item id against `artifact_core.ID6_RE`, ignoring a malformed value with a one-line stderr warning; (c) both hosts' agent-turn env construction sets the two vars from the live `state["run_id"]` and `item["id6"]`, and REMOVES any inherited value when the live run has none, so a stale outer value can never be stamped; (d) `conftest.py` scrubs both vars at session start, exactly as it already scrubs `AW_EXECUTION_ROLE`, so a suite run INSIDE an agent turn does not stamp trailers onto its scratch commits; (e) docstring updates on `_trailers_from_args` and `run_item_trailers`; (f) behavioral tests. OUT: refusing raw `git commit` inside a run (Carrier-Declined, see Deferred); any trailer READER (Order 2 of this Set, plan `199u11` from backlog `am1g38`); a public CLI flag (rejected by `_trailers_from_args`'s own docstring); validating the ids at the WRITE side (see E-04).
- Scope-Paths: agent_workflows/git_commit_helper.py, agent_workflows/work_cmd.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, conftest.py, tests/test_commit_run_trailers_env.py, tests/test_git_commit_helper.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Backlog: j2srcc
- Set: trailread
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: a6xbso
- Approval: 2026-09-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; 9 findings PR-1201..PR-1209 all FIXED (2 HIGH), 4 decisions D-1..D-4 recorded; review record written. Reproduced F-2 exactly (scratch aw commit yields 'x' with both trailers empty) and re-verified F-3/F-4 in code. PR-1201 (HIGH): F-5 named the wrong test; the assertion that actually breaks is test_aw_commit_threads_trailers_and_lifecycle_delegates's _trailers_from_args(Namespace()) == [], in an undeclared file, kept green only by the E-06 scrub; path declared and the coupling stated. PR-1202 (HIGH): nothing proved the writer's exported id is one the reader accepts (the two validate against two deliberate separate definitions of the run-id shape); added E-08/V-08 round trip. PR-1203: the reused harness exports run-test, which the reader rejects, so cases (5)/(6) prove export not usability. PR-1204: stated why validation lives at the reader only. Corrected the drifting corpus counts to a re-derived property, the Order-2 plan id (199u11, not backlog am1g38), and 8apjpp's status. aw ipd lint --phase review-finalize conforming.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog j2srcc on the maintainer's batch-graduation instruction choosing route B (env channel into `aw commit`); raw-commit refusal declined. Every claim re-measured at HEAD 61ef21d8, including a scratch-repo `aw commit` with AW_RUN_ID set producing no trailer today.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every `aw commit` an agent makes inside an `aw oc run` / `aw agy run` turn carry `AW-Run: <run-id>` and `AW-Item: <id6>` trailers, so that finalize (Order 2, plan `199u11`, graduated from backlog `am1g38`) has a real corpus to read, while leaving every commit made outside a run byte-identical to today.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE THE GAP at the executing HEAD. In a scratch git repo under `/tmp/` (one committed file `f`, then modified), run `AW_RUN_ID=run-20260926T000000Z-1 AW_ITEM_ID6=abc123 python3 -m agent_workflows commit --no-plan -m x -- f` with `PYTHONPATH` pointing at this checkout, then `git log -1 --format='%B|%(trailers:key=AW-Run,valueonly)|%(trailers:key=AW-Item,valueonly)|'`. Also paste `git log --since=2026-09-22 --format='%(trailers:key=AW-Run,valueonly)' -- agent_workflows tests | rg -c run-` and the matching total commit count. If the scratch commit ALREADY carries both trailers, STOP and report that the channel exists.
  - THE IN-REPO COUNTS ARE A LIVE POPULATION: RE-DERIVE THEM, DO NOT REPRODUCE THE NUMBERS. The required property is that essentially no AGENT CODE commit carries a trailer, and that whatever trailered commits exist are overwhelmingly DRIVER-SIDE (subject starting `closed by aw oc run`). The counts in the Concern and F-1 are authoring-time context and have already drifted: re-measured at review HEAD `fe9469d8`, the since-2026-09-22 population is 206 commits with 1 trailered (was 188 with 1), and the all-refs total is 71 (was 39). The SHAPE held at both measurements: of the 71, 77 subject-prefix occurrences group as `closed by aw oc run`, and the 9 `work(...)` commits, which ARE agent `aw commit` commits, carry NO trailers (verified individually). Report your own numbers and the grouping, not these.
  - THE STOP CONDITION IS THE SCRATCH COMMIT, NOT THE CORPUS. Do not read a trailered `work(...)` commit in the corpus as "the channel exists": it would mean some other plan landed the channel, which is worth reporting, but the authoritative test is the scratch-repo probe in this item.
  - Depends on: none
  - Expected outcome: the scratch commit message is exactly `x` with both trailer fields empty (measured at review: `git log -1` yields `'x\n|||\n'`, both trailer fields empty); the re-derived in-repo counts show the shape above.
  - Execution state: pending

### Task group 2: the reading side

- [ ] E-02 ADD THE ENV-NAME CONSTANTS to `git_commit_helper`, directly below `TRAILER_KEY_RUN`/`TRAILER_KEY_ITEM`: `RUN_ID_ENV = "AW_RUN_ID"` and `ITEM_ID6_ENV = "AW_ITEM_ID6"`, with a comment that these are the ONE channel by which a live run hands its ids to an agent's `aw commit`, that the runner writes them and `work_cmd` reads them, and that both sides import the names from here so the spelling is single-sourced exactly as the trailer keys are. Extend `run_item_trailers`' docstring paragraph "WHERE THE VALUES MUST COME FROM" with one sentence naming the env channel as the agent-commit route (still a live run's own state, written by the driver, never typed by a human), and an HONEST LIMIT sentence: like `AW_EXECUTION_ROLE`, an environment variable is a selector a same-user process can set, so a trailer is a consistency record, not tamper-proof provenance.
  - Depends on: E-01
  - Expected outcome: `git_commit_helper.RUN_ID_ENV == "AW_RUN_ID"` and `ITEM_ID6_ENV == "AW_ITEM_ID6"`; `run_item_trailers` behavior unchanged.
  - Execution state: pending

- [ ] E-03 TEACH `work_cmd._trailers_from_args` THE ENV FALLBACK. Keep today's precedence: explicit `args.trailers` wins; then `args.run_id`/`args.item_id6` if EITHER is set; only when the namespace supplies none of the three, read `os.environ.get(_gch.RUN_ID_ENV)` and `os.environ.get(_gch.ITEM_ID6_ENV)`. Validate each independently: the run id must fully match `^run-\d{8}T\d{6}Z-\d+(-\d+)?$` (the `runner_shared.new_run_id` shape, plus the `-N` collision suffix `oc_runipd._fresh_audit_run_dir` appends; define the pattern as a module-level constant in `work_cmd` with a comment citing both producers, rather than importing `runner_shared`, which would pull the whole runner into every `aw commit`), and the item must match `_core.ID6_RE` (`work_cmd` already imports `artifact_core as _core`). A value that fails is DROPPED with one stderr line `aw commit: warning - ignoring malformed <VAR> value <repr>; that trailer is omitted (unknown ownership)`; a valid one is passed to `_gch.run_item_trailers`. An empty or whitespace-only var is treated as unset, silently. Rewrite the docstring: keep the "no public flag" reasoning, replace the paragraph saying the agent-commit half "remains deferred" with a statement that the runner now exports the ids into the agent turn and this function reads them, and keep the rule that the plan's own id6 is NEVER auto-derived into `AW-Item` (the item id comes only from the run's env).
  - Depends on: E-02
  - Expected outcome: with both vars valid, `_trailers_from_args(argparse.Namespace())` returns `["AW-Run: <id>", "AW-Item: <id6>"]`; with neither set it returns `[]`; with a malformed run id and a valid id6 it returns only the `AW-Item` trailer and prints the warning.
  - Execution state: pending

### Task group 3: the writing side

- [ ] E-04 EXPORT THE IDS INTO THE OPENCODE AGENT TURN. In `oc_runipd.run_opencode`, in the ONE child-env construction (the block beginning `child_env = pinned_child_env()` that already pops `DRIVER_ATTEST_ENV` and sets or pops `EXECUTION_ROLE_ENV`), after the role handling: set `child_env[_gch.RUN_ID_ENV] = str(state["run_id"])` when `state.get("run_id")` is a non-empty string, else `child_env.pop(_gch.RUN_ID_ENV, None)`; likewise `ITEM_ID6_ENV` from `item.get("id6")`. Set them for isolated AND non-isolated turns (unlike the role marker, a trailer is truthful in both, because either way the commit is this turn's). Always overwrite or pop, never inherit: `pinned_child_env` copies `os.environ`, so a driver launched from inside another run's turn would otherwise stamp the OUTER run's id. Import `git_commit_helper` in the same local-import style the block already uses for `ipd_lifecycle`. Add a short comment citing `a6xbso` and the "overwrite or pop" reason.
  - DO NOT VALIDATE THE IDS HERE. Validation belongs at the READ side only (E-03), for a stated reason: the write side's job is to report what the live run actually calls itself, and a runner that silently dropped its own id would make a real run indistinguishable from no run. Export the value verbatim; if it is malformed, E-03's reader drops it and warns, which is the one place the judgement lives. THE CONSEQUENCE IS REAL AND MUST BE UNDERSTOOD BEFORE YOU WRITE E-07: `state["run_id"]` is exported unvalidated, so a test-shaped id like the existing harness's `run-test` IS exported and then REJECTED by the reader (measured at review: `run-test` fails the `new_run_id` pattern while all 283 real run dirs match it). That is correct behavior, not a bug, and E-07 case (5) must not be read as proving end-to-end usability. See E-08.
  - `state` and `item` ARE both in scope at this block (verified at review: they are the first and third parameters of `run_opencode`), so no plumbing is needed.
  - Depends on: E-02
  - Expected outcome: the `env` kwarg `run_opencode` hands to `subprocess.Popen` carries `AW_RUN_ID=<state run_id>` verbatim and `AW_ITEM_ID6=<item id6>`, and carries neither when the state has no run id even if the parent process exported them.
  - Execution state: pending

- [ ] E-05 MIRROR E-04 IN `agy_runipd.run_agy_turn`, in its twin block (`child_env = pinned_child_env()` ... `popen_kwargs["env"] = child_env`), identical logic and a comment pointing at the oc twin, so the two hosts cannot drift on this rule (the same discipline that block already states for the role marker).
  - Depends on: E-02
  - Expected outcome: the same env facts as E-04 hold for the antigravity host.
  - Execution state: pending

- [ ] E-06 SCRUB BOTH VARS IN `conftest.py` at import time, immediately after the existing `os.environ.pop("AW_EXECUTION_ROLE", None)`, with a short comment: an agent turn now exports `AW_RUN_ID`/`AW_ITEM_ID6`, every plan tells that agent to run the suite, and without the scrub a test reaching `work_cmd._trailers_from_args` would read the OUTER run's ids and fail only inside a runner turn, the same evidence-corruption class the role scrub's comment documents. Tests that need the vars set them explicitly.
  - NAME THE ACTUAL TEST THAT BREAKS, because the plan's original example was wrong and the right one is sharper. The example given was "the byte-identity assertions in `tests/test_git_commit_helper.py`"; those call `git_commit_helper.offer_commit` DIRECTLY with an explicit `trailers=` argument and never reach `_trailers_from_args`, so they are unaffected either way. The test that genuinely breaks is `tests/test_git_commit_helper.py::test_aw_commit_threads_trailers_and_lifecycle_delegates`, whose third assertion is literally `assert work_cmd._trailers_from_args(argparse.Namespace()) == []`. Driven at review with the env vars patched and the E-03 fallback prototyped, that call returns `['AW-Run: run-20260926T010203Z-4242', 'AW-Item: abc123']`, so the assertion FAILS. The conftest scrub is what keeps it passing; cite that test in the comment so the next reader can see what the scrub protects.
  - Depends on: E-04
  - Expected outcome: a test observing `os.environ` sees neither var even when pytest was launched with both exported (E-07 case (7), run as V-06 prescribes), and `test_aw_commit_threads_trailers_and_lifecycle_delegates` passes under a run launched with both vars set.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-07 ADD `tests/test_commit_run_trailers_env.py`, all behavioral (no source-text or structure assertions, per the 2026-09-26 maintainer ruling). Cases: (1) SCRATCH-REPO END TO END: a temp git repo, a modified file `f`, run `python3 -m agent_workflows commit --no-plan -m x -- f` as a SUBPROCESS with `env` = a copy of `os.environ` plus `AW_RUN_ID=run-20260926T010203Z-4242`, `AW_ITEM_ID6=abc123`, and `PYTHONPATH` at the repo root; assert `git log -1 --format=%(trailers:key=AW-Run,valueonly)` stripped equals the run id and the `AW-Item` equivalent equals `abc123`. (2) BYTE-IDENTITY WITHOUT ENV: the same with both vars removed; assert `git cat-file commit HEAD` message body is exactly `x\n` (read the stored bytes, as `test_git_commit_helper._raw_commit_message` does). (3) MALFORMED VALUES: `AW_RUN_ID=../evil` with a valid `AW_ITEM_ID6`: the commit carries `AW-Item` only, no `AW-Run`, and the subprocess stderr names `AW_RUN_ID`; and a malformed id6 (`ABC!23`) with a valid run id carries `AW-Run` only. (4) NAMESPACE PRECEDENCE: in-process, with the env vars patched via `mock.patch.dict(os.environ, ...)`, `work_cmd._trailers_from_args(argparse.Namespace(run_id="run-20260101T000000Z-1", item_id6="zzz999"))` returns the namespace values, not the env ones. (5) OC STUB-AGENT ENV DUMP: call `oc_runipd.run_opencode` with `subprocess.Popen` patched (the harness shape `tests/test_driver_attestation_gate.py` `test_child_env_scrubs_driver_attest_for_both_hosts` already uses, including patching `observe_opencode_policy` and `lane_containment.record_host_posture`), a state carrying `run_id` and an item carrying `id6`; assert the captured `env` kwarg has both vars with those values; then repeat with `mock.patch.dict(os.environ, {"AW_RUN_ID": "run-19990101T000000Z-1"})` and a state WITHOUT `run_id`, asserting `AW_RUN_ID` is ABSENT from the captured env. (6) AGY STUB-AGENT ENV DUMP: the same two assertions through `agy_runipd.run_agy_turn`. (7) CONFTEST SCRUB: an in-process test asserting `os.environ` holds neither `AW_RUN_ID` nor `AW_ITEM_ID6`; it is made NON-VACUOUS by V-06, which launches it with both vars exported.
  - THE HARNESS YOU ARE REUSING CARRIES `run_id: "run-test"`, WHICH THE READER REJECTS. `tests/test_driver_attestation_gate.py::test_child_env_scrubs_driver_attest_for_both_hosts` builds `state = {"run_id": "run-test", ...}` and `item = {"position": 1, "id6": "abc123", ...}`. `abc123` is a valid id6, but `run-test` FAILS the run-id pattern E-03 validates against (measured at review). Because E-04/E-05 do not validate at the write side, cases (5) and (6) will PASS while asserting `AW_RUN_ID=run-test`, which the reader would then drop. That is consistent behavior, not a contradiction, but it means (5)/(6) prove ONLY that the var is exported and NOT that it is usable end to end. Either keep `run-test` and say so in the test's own docstring, or use a pattern-valid id in YOUR copy of the harness state; do NOT "fix" it by adding validation to E-04/E-05, which is explicitly out of scope. Case (1) is the only end-to-end proof, which is why E-08 exists.
  - Depends on: E-03, E-04, E-05, E-06
  - Expected outcome: all cases pass after the change; cases (1), (3), (5) and (6) FAIL before it (no trailer, no env var), while (2) and (4) pass both before and after.
  - Execution state: pending

- [ ] E-08 ADD ONE JOINED CASE that proves the WRITE and READ halves agree on a REAL run id, which no other item does: take the exact run id shape `runner_shared.new_run_id` produces, feed it through the oc child-env construction (the E-07 case (5) harness, with a pattern-valid `run_id` in the state), capture the exported `AW_RUN_ID`, then pass that captured string through `work_cmd._trailers_from_args(argparse.Namespace())` with the env patched to the captured value, and assert the resulting trailer list carries it. Assert the SAME for the `-N` collision suffix `oc_runipd._fresh_audit_run_dir` appends. Behavioral only.
  - WHY THIS IS NOT REDUNDANT WITH CASES (1), (5) AND (6). Case (1) exercises the reader through a real `aw commit` but sets the env BY HAND, so it never touches the writer. Cases (5) and (6) exercise the writer but assert only on the env dict, and (as noted) do so with a value the reader rejects. So nothing in the plan as authored proves that what the WRITER exports is a value the READER accepts, which is the entire contract this plan delivers. One test closes that gap, and it is the test that would catch a future divergence between `new_run_id`'s shape and `work_cmd`'s pattern, which are deliberately two separate definitions (E-03 chose not to import `runner_shared`, for good reason).
  - Depends on: E-03, E-04
  - Expected outcome: the exported run id round-trips into a trailer for both the plain and `-N`-suffixed shapes; the test fails before E-03/E-04 land.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Trailer keys are single-sourced in `git_commit_helper` (`TRAILER_KEY_RUN`, `TRAILER_KEY_ITEM`) and formatted only by `run_item_trailers`; `compose_message_with_trailers` validates via `validate_trailer`. This plan adds the env NAMES beside them for the same reason.
- `run_item_trailers`' docstring: an absent value means UNKNOWN ownership and must stay absent; a fabricated trailer makes a false ownership claim permanent. The fallback therefore DROPS malformed values rather than repairing them.
- `_trailers_from_args`' docstring rejects a public CLI flag because the values come from a live run, never a human. The env channel respects that: only the driver writes it.
- The agent-turn env is built ONCE per host (`oc_runipd.run_opencode`, `agy_runipd.run_agy_turn`) from `runner_shared.pinned_child_env`, and both blocks already overwrite-or-pop an inherited marker (`DRIVER_ATTEST_ENV`, `EXECUTION_ROLE_ENV`) for the stated reason that `pinned_child_env` copies `os.environ`.
- `conftest.py` scrubs `AW_EXECUTION_ROLE` at import time so a suite launched inside a runner turn measures the code, not the environment (backlog `1uq1cu`). E-06 extends that.
- `runner_shared.new_run_id` mints `run-<YYYYmmddTHHMMSSZ>-<pid>`; `oc_runipd._fresh_audit_run_dir` may append `-N`. Measured: all 274 run directories under `.aw/records/runs/` match `^run-\d{8}T\d{6}Z-\d+$`.
- Tests are behavioral only (maintainer ruling 2026-09-26); run BARE `python3 -m pytest`, narrowed runs with `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1 through F-5 measured at HEAD `61ef21d8` on 2026-09-26. ALL RE-VERIFIED AT REVIEW HEAD `fe9469d8`, with the corpus counts drifting and the shape holding (see E-01): F-2 re-reproduced exactly in a scratch repo (`git log -1` -> `'x\n|||\n'`); F-3 re-read in both host blocks; F-4 re-read in the runbook. F-6 corrected. F-7 through F-12 added at review.

READ THE COUNTS IN F-1 AS AUTHORING CONTEXT, NOT AS THE BAR: the since-2026-09-22 population is now 206 commits (1 trailered) and the all-refs total is 71 (was 39). The PROPERTY is what matters and it held at both measurements: the trailered set is overwhelmingly driver-side `closed by aw oc run`, and the 9 agent `work(...)` commits carry no trailers.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | agent code commits | Essentially no agent code commit carries a trailer. | `git log --since=2026-09-22 -- agent_workflows tests`: 188 commits, 1 with `AW-Run` (`8aabf15a`, whose body ends `AW-Run: run-20260924T171335Z-1981773` / `AW-Item: hv9gar`); all refs: 39 trailered, 38 of them subjects starting `closed by aw oc run` |
| F-2 | HIGH | `work_cmd._trailers_from_args` | Reads only namespace attributes no CLI flag sets, so a real `aw commit` never trailers. | scratch repo: `AW_RUN_ID=run-20260926T000000Z-1 aw commit --no-plan -m x -- f` -> `git log -1 --format='%B|%(trailers:key=AW-Run,valueonly)|'` -> `x` then `||` |
| F-3 | HIGH | `oc_runipd.run_opencode`, `agy_runipd.run_agy_turn` | The agent-turn env carries no run or item id. | both blocks set only `EXECUTION_ROLE_ENV` and pop `DRIVER_ATTEST_ENV` on top of `pinned_child_env()` |
| F-4 | INFO | prompts | The agent is already told to use `aw commit`, so no prompt change is needed. | `oc_runipd.DEFAULT_RUNBOOK_TEXT` directive 4 and its agy twin: "Commit only files you changed ... through `aw commit <plan> -- <paths>`"; `runner_shared` review-turn text says the same (commit `12ecd491`) |
| F-5 | MEDIUM | test isolation | Once the turn exports the ids, a suite run inside that turn would stamp them onto scratch commits unless scrubbed. | `conftest.py` already pops `AW_EXECUTION_ROLE` for the identical reason; `tests/test_git_commit_helper.py` asserts byte-identical messages |
| F-6 | LOW | overlap | Pending plan `8apjpp` (revcommit) adds trailers to `runner_shared.commit_review_lane_output`, a driver-side site. Different file and function from this plan's; no ordering dependency. CORRECTED AT REVIEW: `8apjpp` is `executed`, not pending (the Deferred entry below already says so and cites it as evidence), and its trailers are in the tree: `runner_shared` builds `[*_gch.run_item_trailers(run_id, id6), "AW-Committed-By: driver"]` for the review-lane commit. So the overlap is settled, not prospective. | `8apjpp` E-05; the trailer list read in `runner_shared`; the plan file under `plans/executed/` |
| F-7 | HIGH | `tests/test_git_commit_helper.py::test_aw_commit_threads_trailers_and_lifecycle_delegates` | A SHIPPED ASSERTION BREAKS UNDER THE ENV FALLBACK, and F-5's example named the wrong test. That test asserts `work_cmd._trailers_from_args(argparse.Namespace()) == []`; with the vars set and the fallback prototyped it returns two trailers, so the assertion fails. The byte-identity tests F-5 cited are NOT affected (they call `offer_commit` with an explicit `trailers=`). The conftest scrub (E-06) is what keeps the suite green, so the two items are coupled and the coupling was unstated. | Driven at review with `mock.patch.dict(os.environ, {...})` and the prototyped fallback: returns `['AW-Run: run-20260926T010203Z-4242', 'AW-Item: abc123']` where the assertion demands `[]`; `grep -rln "_trailers_from_args" tests/` -> that file only |
| F-8 | MEDIUM | E-07 cases (5)/(6) versus E-03 | THE REUSED HARNESS'S RUN ID IS ONE THE READER REJECTS. `test_child_env_scrubs_driver_attest_for_both_hosts` uses `run_id: "run-test"`, which fails the `new_run_id` pattern E-03 validates against, while `id6: "abc123"` is valid. Since the write side does not validate, (5)/(6) pass asserting a value the reader would drop, so they prove export but not usability. Not a contradiction; an unstated limit, now stated, and E-08 closes the gap. | `run-test` vs the pattern (no match); all 283 real run dirs match; the harness state read verbatim |
| F-9 | MEDIUM | the plan as authored | NOTHING PROVED THAT THE WRITER'S VALUE IS ONE THE READER ACCEPTS. Case (1) sets the env by hand (reader only); (5)/(6) assert on the env dict (writer only). The two halves are validated against two SEPARATE definitions of the run-id shape by design (E-03 deliberately does not import `runner_shared`), which is exactly the pair that can silently diverge. Added E-08. | The case list read against what each case touches; E-03's stated reason for a local pattern constant |
| F-10 | LOW | `am1g38` versus `199u11` | THE PLAN NAMES THE ORDER-2 ARTIFACT BY ITS BACKLOG ID THROUGHOUT. `am1g38` is the backlog item; the Order 2 PLAN is `199u11` (`- Set: trailread`, `- Order: 2`, `- Item-Dependencies: executed:a6xbso`, `- From-Backlog: am1g38`). A reader following `am1g38` as a plan id finds no plan. Corrected in the Goal, Scope and Deferred. | `.aw/records/plans/pending/20260926-trailread-02-199u11-...ipd.md` front matter; `.aw/records/backlog/graduated/20260922-trailread-01-am1g38-...backlog.md` |
| F-11 | LOW | `work_cmd._trailers_from_args` docstring | ITS STATED PREMISE IS ALREADY STALE AND E-03 MUST NOT PRESERVE IT. The docstring says agent commits "are made by the agent running raw `git commit -m msg -- <path>` per the runbook directive, pass through no `offer_commit` call, and so cannot be reached by wiring one". The runbook now directs `aw commit` (directive 4, quoted in F-4), so that sentence describes a superseded instruction and is the reason the gap looks unreachable. E-03 already rewrites this paragraph; this records WHY it is wrong rather than merely out of date. | `oc_runipd.DEFAULT_RUNBOOK_TEXT` directive 4 read verbatim; the docstring paragraph read verbatim |
| F-12 | INFO | `conftest.py` | A PRE-EXISTING STALE CROSS-REFERENCE in the file E-06 edits: the comment cites `tests/test_role_declaration_guard.py` twice, and no such file exists anywhere in the tree. NOT this plan's to fix (it predates it and is unrelated to trailers); recorded so the executor does not copy the pattern of citing a nonexistent test in the comment they add. | `grep -rn "test_role_declaration_guard" --include=*.py .` -> two hits, both in `conftest.py`; `ls tests/ \| grep -i role` -> nothing |

## Proposed changes (ordered, validatable)

1. E-01 reproduces the untrailered scratch commit.
2. E-02 adds the env-name constants and the provenance note.
3. E-03 adds the validated env fallback to `_trailers_from_args`.
4. E-04 and E-05 export the ids into both hosts' agent turns, overwrite-or-pop, unvalidated at the write side.
5. E-06 scrubs the vars in `conftest.py` (which is what keeps the shipped assertion in F-7 green).
6. E-07 proves it with scratch-repo and stub-agent tests.
7. E-08 proves the writer's value round-trips through the reader, which no other item covers.

## Deferred / out of scope (with reason)

- Refusing a raw `git commit` inside a run (a hook or wrapper that makes an untrailered agent commit impossible).
  - Carrier-Declined: a risk-appetite decision the maintainer made on 2026-09-26 at batch graduation. Readers treat a missing trailer as UNKNOWN ownership, never as foreign (Order 2, `am1g38`), so an agent that bypasses `aw commit` loses attribution but cannot cause a false excuse; enforcement would also be local and skippable, the same limit AGENTS.md records for the integration lock.
- Reading trailers back in finalize.
  - Carrier: am1g38
  - Rationale: Order 2 of this Set is plan `199u11` (graduated from this backlog item `am1g38`), which carries `- Item-Dependencies: executed:a6xbso` so it does not read an empty corpus. The carrier field names the BACKLOG item deliberately (the carrier vocabulary resolves backlog and plans); the plan id is stated here so a reader can find it (F-10).
- Trailering driver-side review-lane commits.
  - Carrier-Evidence: .aw/records/plans/executed/20260925-revcommit-01-8apjpp-record-a-driver-side-review-output-commit-in-the-plan-s-own.ipd.md
  - Rationale: that plan owned `runner_shared.commit_review_lane_output` and has since executed, delivering the AW-Run/AW-Item/AW-Committed-By trailers on the driver review commit; re-pointed from the now-terminal carrier to its evidence on 2026-09-26.

## Scope check

- Over-scope: none.
- Under-scope: none remaining. Two gaps were found at review and are now in scope rather than at execution: `tests/test_git_commit_helper.py` (F-7, a shipped assertion the env fallback breaks) and E-08 (nothing proved the writer's value is one the reader accepts, F-9). `agent_workflows/runner_shared.py` is still deliberately NOT declared, and that reasoning was CHECKED at review and holds: `pinned_child_env` is bound as a generic `env_builder` by many driver-side call sites (`run_checked`, `driver_begin`, and others), where exporting a per-turn item id would be wrong, so the per-turn values belong in the two host blocks that already specialize it.
- Scope-Paths justification: `git_commit_helper.py` (constants, docstring), `work_cmd.py` (reader), `oc_runipd.py`/`agy_runipd.py` (writers), `conftest.py` (scrub), the new test file, and `tests/test_git_commit_helper.py` (the one assertion in F-7).

## Required tests / validation

- `tests/test_commit_run_trailers_env.py` (new), cases (1)-(7) as in E-07 plus E-08's round-trip case; (1), (3), (5), (6) and E-08's case shown FAILING before the change.
- Existing `tests/test_driver_attestation_gate.py` stays green UNCHANGED. `tests/test_git_commit_helper.py` stays green and is expected to need at most the F-7 assertion adjusted; state explicitly whether you changed it, because the conftest scrub (E-06) should make a change unnecessary and a change there is a signal the scrub is not doing its job.
- Bare `python3 -m pytest` before and after; compare failing node IDs. Also run the suite ONCE with both vars exported (V-06), which is the only way the F-7 hazard shows up.

## Spec / documentation sync

- N/A for specs: spec `25kzda` 4.6 already says the checker finds run-owned commits "by required immutable trailers such as `AW-Run: <run-id>` and `AW-Item: <id6>`"; this plan supplies such commits and changes no contract. The spec's preamble sentence about who passes trailers is corrected separately by plan Set `spec25kfix` (backlog `j0ag0u`), worded without counts so this plan does not re-stale it. No `.spec.md` is in `- Scope-Paths:`.
- No user-facing docs change: the trailers are machine-read and `aw commit`'s CLI surface is unchanged.

## Open questions

### OQ-01: Route A (prompt the agent to hand-write trailers) or route B (the env channel into `aw commit`)?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Route B, per the maintainer's instruction at batch graduation on 2026-09-26. Route A's compliance cannot be enforced by code and makes noncompliance indistinguishable from absence (backlog `j2srcc`); route B reuses `_trailers_from_args`, which "already accepts `run_id`/`item_id6`", and the prompts already direct `aw commit`.

### OQ-02: Should raw `git commit` be refused inside a run?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No, maintainer ruling 2026-09-26 (risk appetite). Carrier-Declined in Deferred; readers treat a missing trailer as unknown.

### OQ-03: Should `AW-Item` come from the plan argument of `aw commit <plan>` when no env is set?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: No, from repository evidence: `_trailers_from_args`' docstring already excludes auto-deriving the plan id6 because "that would change the default behavior of an existing caller", and the trailer's value is that it records a LIVE RUN's claim (`run_item_trailers` docstring). A human's `aw commit <plan>` outside a run stays untrailered, i.e. unknown.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the scratch-repo `aw commit` output and the `git log -1 --format=...` line showing an untrailered `x`, plus the two in-repo counts.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff adding `RUN_ID_ENV`/`ITEM_ID6_ENV` and the `run_item_trailers` docstring sentences; paste `python3 -c "from agent_workflows import git_commit_helper as g; print(g.RUN_ID_ENV, g.ITEM_ID6_ENV, g.run_item_trailers(None, None))"` printing `AW_RUN_ID AW_ITEM_ID6 []`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of `_trailers_from_args`; paste an in-process run printing the return value for (both valid env), (no env), and (malformed run id + valid id6), with the stderr warning line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the diff of the oc child-env block, and the passing output of E-07 case (5) naming the test.
  - The diff must show NO validation of either id at the write side, and must show the overwrite-or-pop shape for both vars. State in one line which run-id value case (5) asserts and whether the reader would accept it (F-8), so the record cannot be mistaken for end-to-end proof.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the diff of the agy child-env block, and the passing output of E-07 case (6) naming the test.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `conftest.py` diff; paste `AW_RUN_ID=run-20260926T000000Z-1 AW_ITEM_ID6=abc123 python3 -m pytest tests/test_commit_run_trailers_env.py tests/test_git_commit_helper.py -o addopts="" -q` passing, with case (7) among the passes; then the same with the `conftest.py` hunk temporarily reverted, showing case (7) FAILING; then passing again after restoring.
  - THE REVERTED RUN MUST ALSO SHOW `test_aw_commit_threads_trailers_and_lifecycle_delegates` FAILING, which is the shipped assertion the scrub protects (F-7). If it passes with the scrub reverted, either the env fallback is not wired or that test was edited; say which, because an edited assertion there means the scrub is not carrying its weight.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest tests/test_commit_run_trailers_env.py -o addopts="" -q` passing with the case count; then the same run with the E-03/E-04/E-05 hunks temporarily reverted, showing cases (1), (3), (5), (6) FAILING and (2), (4) passing; then passing again after restoring. Paste the bare `python3 -m pytest` summary line BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the round-trip test source's assertions and its passing run, for BOTH the plain `new_run_id` shape and the `-N` suffixed shape. State in one line that the run id asserted came from the CAPTURED env (the writer's output) and was not re-typed in the test body, since a re-typed literal would test the reader twice and prove nothing about agreement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. The runner exports its run id and the item id6 into each agent turn as `AW_RUN_ID`/`AW_ITEM_ID6`, and `aw commit` stamps them as `AW-Run`/`AW-Item` trailers when it finds them valid. Outside a run nothing changes: the commit message is byte-identical. Raw `git commit` is NOT refused (maintainer ruling 2026-09-26), so untrailered agent commits remain possible and are read as unknown ownership. No reader is built here; Order 2 of this Set (plan `199u11`, from backlog `am1g38`) consumes these trailers.

THE HONEST SECURITY PROPERTY, stated before approval because a trailer looks like provenance and is not. An environment variable is a selector any same-user process can set, exactly as `AW_EXECUTION_ROLE` is, so an `AW-Run` trailer is a CONSISTENCY RECORD and not tamper-proof attribution. E-02 requires that sentence in the code's own docstring. What the mechanism genuinely buys is that a commit made by a cooperating agent inside a run becomes attributable; it does not make a forged claim impossible, and no downstream reader should treat it as though it did.

WHERE VALIDATION LIVES, since the asymmetry is deliberate and would otherwise look like an oversight: the WRITE side exports `state["run_id"]` verbatim (a runner that silently dropped its own id would make a real run indistinguishable from no run), and the READ side validates and drops with a warning. A consequence measured at review: a test-shaped id such as the existing harness's `run-test` IS exported and then REJECTED, so the env-dump tests prove export, not usability. E-08 is the one item that proves the two halves agree on a real id.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the seven paths in `- Scope-Paths:`, which now include `tests/test_git_commit_helper.py` (F-7). Within `agent_workflows/work_cmd.py` only `_trailers_from_args` and one new module-level pattern constant; within each runner only the ONE `child_env = pinned_child_env()` block; within `conftest.py` only the scrub beside the existing role pop; within `tests/test_git_commit_helper.py` only the `_trailers_from_args(argparse.Namespace()) == []` assertion, and only if the conftest scrub proves insufficient. Expected to need NO edit, and named so reconciliation has something to check: `agent_workflows/runner_shared.py` (`pinned_child_env` stays generic; it is READ only), `git_commit_helper.run_item_trailers`' BEHAVIOR (docstring only), and `tests/test_driver_attestation_gate.py` (its harness is copied, not modified). If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-07 must show the new tests FAILING before the change. THE TWO CLAIMS EASIEST TO FAKE HERE: (a) the round-trip in E-08, which is worthless if the test re-types the run id instead of asserting on the CAPTURED env value, so V-08 requires you to say which you did; and (b) the conftest scrub's effect, which only ever shows up in a run launched WITH the vars exported, so V-06's reverted run must name the shipped assertion that fails.

GENUINE STOP CONDITIONS: (1) if E-01's scratch commit already carries both trailers, stop and report that the channel already exists (it does NOT today: re-measured at review, the message is exactly `x` with both trailer fields empty); (2) if the conftest scrub cannot keep `tests/test_git_commit_helper.py::test_aw_commit_threads_trailers_and_lifecycle_delegates` green under a run with both vars exported, stop and report rather than weakening that assertion to `!= None` or deleting it, because it is the one shipped test pinning the no-env default.

Commit ONLY paths in `- Scope-Paths:` through `aw commit a6xbso -- <paths>` (never `git add -A`, never push). NOTE THE PLEASING CONSEQUENCE, and check it: if this plan is executed by a runner turn, YOUR OWN commit should be the first agent code commit to carry `AW-Run`/`AW-Item`. Paste its trailers in V-07 as incidental end-to-end evidence; do NOT count it as a substitute for the tests, since a single observation cannot distinguish the fix from a coincidence. On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition to `executed/` is performed with `aw ipd finalize`, never a raw `git mv`; the RUNNER owns it when it executes this plan in a lane, and the executor otherwise performs it. Then close backlog `j2srcc` `done` with `--evidence` citing the executed plan. This plan carries NO `- Blocks-Release:` and `j2srcc` carries none either (verified at review), so no release gate is handed off and none needs de-gating.
