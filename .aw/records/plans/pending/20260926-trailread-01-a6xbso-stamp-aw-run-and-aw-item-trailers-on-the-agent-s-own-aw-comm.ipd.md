# IPD: Stamp AW-Run and AW-Item trailers on the agent's own aw commit calls inside a run

- Date: 2026-09-26
- Kind: child
- Concern: THE AGENT'S OWN CODE COMMITS CARRY NO RUN-OWNERSHIP TRAILER, SO NOTHING DOWNSTREAM CAN ATTRIBUTE THEM. Measured at HEAD `61ef21d8`: of 188 commits since 2026-09-22 touching `agent_workflows/` or `tests/`, exactly ONE carries an `AW-Run` trailer (`8aabf15a`, IPD `hv9gar`), and across all refs 39 commits carry one, 38 of which are driver-side `closed by aw oc run` backlog-close commits touching only `.backlog.md` files. Agents are already told to commit through `aw commit` (runbook `oc_runipd.DEFAULT_RUNBOOK_TEXT` directive 4, its `agy_runipd` twin, and the `runner_shared` prompt text, commit `12ecd491`), and `aw commit` can already format trailers (`work_cmd._trailers_from_args` -> `git_commit_helper.run_item_trailers`). The gap is the CHANNEL: `_trailers_from_args` reads only `args.trailers`/`args.run_id`/`args.item_id6`, which no CLI flag sets, and the agent turn's environment (built by `runner_shared.pinned_child_env` in `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn`) carries no run or item id. Measured: `AW_RUN_ID=run-20260926T000000Z-1 aw commit --no-plan -m x -- f` in a scratch repo commits a message of exactly `x` with no trailer.
- Scope: IN: (a) two env-var NAME constants beside the trailer keys in `git_commit_helper` (`RUN_ID_ENV = "AW_RUN_ID"`, `ITEM_ID6_ENV = "AW_ITEM_ID6"`); (b) `work_cmd._trailers_from_args` falls back to those env vars ONLY when the namespace supplies neither `trailers` nor `run_id`/`item_id6`, validating the run id against the `new_run_id` shape and the item id against `artifact_core.ID6_RE`, ignoring a malformed value with a one-line stderr warning; (c) both hosts' agent-turn env construction sets the two vars from the live `state["run_id"]` and `item["id6"]`, and REMOVES any inherited value when the live run has none, so a stale outer value can never be stamped; (d) `conftest.py` scrubs both vars at session start, exactly as it already scrubs `AW_EXECUTION_ROLE`, so a suite run INSIDE an agent turn does not stamp trailers onto its scratch commits; (e) docstring updates on `_trailers_from_args` and `run_item_trailers`; (f) behavioral tests. OUT: refusing raw `git commit` inside a run (Carrier-Declined, see Deferred); any trailer READER (Order 2 of this Set, `am1g38`); a public CLI flag (rejected by `_trailers_from_args`'s own docstring).
- Scope-Paths: agent_workflows/git_commit_helper.py, agent_workflows/work_cmd.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, conftest.py, tests/test_commit_run_trailers_env.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Backlog: j2srcc
- Set: trailread
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: a6xbso

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog j2srcc on the maintainer's batch-graduation instruction choosing route B (env channel into `aw commit`); raw-commit refusal declined. Every claim re-measured at HEAD 61ef21d8, including a scratch-repo `aw commit` with AW_RUN_ID set producing no trailer today.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every `aw commit` an agent makes inside an `aw oc run` / `aw agy run` turn carry `AW-Run: <run-id>` and `AW-Item: <id6>` trailers, so that finalize (Order 2, `am1g38`) has a real corpus to read, while leaving every commit made outside a run byte-identical to today.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE THE GAP at the executing HEAD. In a scratch git repo under `/tmp/` (one committed file `f`, then modified), run `AW_RUN_ID=run-20260926T000000Z-1 AW_ITEM_ID6=abc123 python3 -m agent_workflows commit --no-plan -m x -- f` with `PYTHONPATH` pointing at this checkout, then `git log -1 --format='%B|%(trailers:key=AW-Run,valueonly)|%(trailers:key=AW-Item,valueonly)|'`. Also paste `git log --since=2026-09-22 --format='%(trailers:key=AW-Run,valueonly)' -- agent_workflows tests | rg -c run-` and the matching total commit count. If the scratch commit ALREADY carries both trailers, STOP and report that the channel exists.
  - Depends on: none
  - Expected outcome: the scratch commit message is exactly `x` with both trailer fields empty; the in-repo count is at most a handful of trailered code commits out of well over a hundred.
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
  - Depends on: E-02
  - Expected outcome: the `env` kwarg `run_opencode` hands to `subprocess.Popen` carries `AW_RUN_ID=<state run_id>` and `AW_ITEM_ID6=<item id6>`, and carries neither when the state has no run id even if the parent process exported them.
  - Execution state: pending

- [ ] E-05 MIRROR E-04 IN `agy_runipd.run_agy_turn`, in its twin block (`child_env = pinned_child_env()` ... `popen_kwargs["env"] = child_env`), identical logic and a comment pointing at the oc twin, so the two hosts cannot drift on this rule (the same discipline that block already states for the role marker).
  - Depends on: E-02
  - Expected outcome: the same env facts as E-04 hold for the antigravity host.
  - Execution state: pending

- [ ] E-06 SCRUB BOTH VARS IN `conftest.py` at import time, immediately after the existing `os.environ.pop("AW_EXECUTION_ROLE", None)`, with a short comment: an agent turn now exports `AW_RUN_ID`/`AW_ITEM_ID6`, every plan tells that agent to run the suite, and without the scrub any test that commits through `aw commit` (for example the byte-identity assertions in `tests/test_git_commit_helper.py`) would stamp the outer run's trailers into its scratch commit and fail only inside a runner turn, the same evidence-corruption class the role scrub's comment documents. Tests that need the vars set them explicitly.
  - Depends on: E-04
  - Expected outcome: a test observing `os.environ` sees neither var even when pytest was launched with both exported (E-07 case (7), run as V-06 prescribes).
  - Execution state: pending

### Task group 4: prove it

- [ ] E-07 ADD `tests/test_commit_run_trailers_env.py`, all behavioral (no source-text or structure assertions, per the 2026-09-26 maintainer ruling). Cases: (1) SCRATCH-REPO END TO END: a temp git repo, a modified file `f`, run `python3 -m agent_workflows commit --no-plan -m x -- f` as a SUBPROCESS with `env` = a copy of `os.environ` plus `AW_RUN_ID=run-20260926T010203Z-4242`, `AW_ITEM_ID6=abc123`, and `PYTHONPATH` at the repo root; assert `git log -1 --format=%(trailers:key=AW-Run,valueonly)` stripped equals the run id and the `AW-Item` equivalent equals `abc123`. (2) BYTE-IDENTITY WITHOUT ENV: the same with both vars removed; assert `git cat-file commit HEAD` message body is exactly `x\n` (read the stored bytes, as `test_git_commit_helper._raw_commit_message` does). (3) MALFORMED VALUES: `AW_RUN_ID=../evil` with a valid `AW_ITEM_ID6`: the commit carries `AW-Item` only, no `AW-Run`, and the subprocess stderr names `AW_RUN_ID`; and a malformed id6 (`ABC!23`) with a valid run id carries `AW-Run` only. (4) NAMESPACE PRECEDENCE: in-process, with the env vars patched via `mock.patch.dict(os.environ, ...)`, `work_cmd._trailers_from_args(argparse.Namespace(run_id="run-20260101T000000Z-1", item_id6="zzz999"))` returns the namespace values, not the env ones. (5) OC STUB-AGENT ENV DUMP: call `oc_runipd.run_opencode` with `subprocess.Popen` patched (the harness shape `tests/test_driver_attestation_gate.py` `test_child_env_scrubs_driver_attest_for_both_hosts` already uses, including patching `observe_opencode_policy` and `lane_containment.record_host_posture`), a state carrying `run_id` and an item carrying `id6`; assert the captured `env` kwarg has both vars with those values; then repeat with `mock.patch.dict(os.environ, {"AW_RUN_ID": "run-19990101T000000Z-1"})` and a state WITHOUT `run_id`, asserting `AW_RUN_ID` is ABSENT from the captured env. (6) AGY STUB-AGENT ENV DUMP: the same two assertions through `agy_runipd.run_agy_turn`. (7) CONFTEST SCRUB: an in-process test asserting `os.environ` holds neither `AW_RUN_ID` nor `AW_ITEM_ID6`; it is made NON-VACUOUS by V-06, which launches it with both vars exported.
  - Depends on: E-03, E-04, E-05, E-06
  - Expected outcome: all cases pass after the change; cases (1), (3), (5) and (6) FAIL before it (no trailer, no env var), while (2) and (4) pass both before and after.
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

All measured at HEAD `61ef21d8` on 2026-09-26.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | agent code commits | Essentially no agent code commit carries a trailer. | `git log --since=2026-09-22 -- agent_workflows tests`: 188 commits, 1 with `AW-Run` (`8aabf15a`, whose body ends `AW-Run: run-20260924T171335Z-1981773` / `AW-Item: hv9gar`); all refs: 39 trailered, 38 of them subjects starting `closed by aw oc run` |
| F-2 | HIGH | `work_cmd._trailers_from_args` | Reads only namespace attributes no CLI flag sets, so a real `aw commit` never trailers. | scratch repo: `AW_RUN_ID=run-20260926T000000Z-1 aw commit --no-plan -m x -- f` -> `git log -1 --format='%B|%(trailers:key=AW-Run,valueonly)|'` -> `x` then `||` |
| F-3 | HIGH | `oc_runipd.run_opencode`, `agy_runipd.run_agy_turn` | The agent-turn env carries no run or item id. | both blocks set only `EXECUTION_ROLE_ENV` and pop `DRIVER_ATTEST_ENV` on top of `pinned_child_env()` |
| F-4 | INFO | prompts | The agent is already told to use `aw commit`, so no prompt change is needed. | `oc_runipd.DEFAULT_RUNBOOK_TEXT` directive 4 and its agy twin: "Commit only files you changed ... through `aw commit <plan> -- <paths>`"; `runner_shared` review-turn text says the same (commit `12ecd491`) |
| F-5 | MEDIUM | test isolation | Once the turn exports the ids, a suite run inside that turn would stamp them onto scratch commits unless scrubbed. | `conftest.py` already pops `AW_EXECUTION_ROLE` for the identical reason; `tests/test_git_commit_helper.py` asserts byte-identical messages |
| F-6 | LOW | overlap | Pending plan `8apjpp` (revcommit) adds trailers to `runner_shared.commit_review_lane_output`, a driver-side site. Different file and function from this plan's; no ordering dependency. | `8apjpp` E-05 |

## Proposed changes (ordered, validatable)

1. E-01 reproduces the untrailered scratch commit.
2. E-02 adds the env-name constants and the provenance note.
3. E-03 adds the validated env fallback to `_trailers_from_args`.
4. E-04 and E-05 export the ids into both hosts' agent turns, overwrite-or-pop.
5. E-06 scrubs the vars in `conftest.py`.
6. E-07 proves it with scratch-repo and stub-agent tests.

## Deferred / out of scope (with reason)

- Refusing a raw `git commit` inside a run (a hook or wrapper that makes an untrailered agent commit impossible).
  - Carrier-Declined: a risk-appetite decision the maintainer made on 2026-09-26 at batch graduation. Readers treat a missing trailer as UNKNOWN ownership, never as foreign (Order 2, `am1g38`), so an agent that bypasses `aw commit` loses attribution but cannot cause a false excuse; enforcement would also be local and skippable, the same limit AGENTS.md records for the integration lock.
- Reading trailers back in finalize.
  - Carrier: am1g38
  - Rationale: Order 2 of this Set, which depends on this plan so it does not read an empty corpus.
- Trailering driver-side review-lane commits.
  - Carrier-Evidence: .aw/records/plans/executed/20260925-revcommit-01-8apjpp-record-a-driver-side-review-output-commit-in-the-plan-s-own.ipd.md
  - Rationale: that plan owned `runner_shared.commit_review_lane_output` and has since executed, delivering the AW-Run/AW-Item/AW-Committed-By trailers on the driver review commit; re-pointed from the now-terminal carrier to its evidence on 2026-09-26.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/runner_shared.py` is deliberately NOT declared: `pinned_child_env` is left generic (it also builds the driver's own subprocess envs, e.g. `driver_finalize`'s, where a run-id export would be wrong), and the per-turn values are applied in the two host blocks that already specialize it.
- Scope-Paths justification: `git_commit_helper.py` (constants, docstring), `work_cmd.py` (reader), `oc_runipd.py`/`agy_runipd.py` (writers), `conftest.py` (scrub), new test file.

## Required tests / validation

- `tests/test_commit_run_trailers_env.py` (new), cases (1)-(7) as in E-07; (1), (3), (5), (6) shown FAILING before the change.
- Existing `tests/test_git_commit_helper.py` and `tests/test_driver_attestation_gate.py` stay green.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

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
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the diff of the agy child-env block, and the passing output of E-07 case (6) naming the test.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `conftest.py` diff; paste `AW_RUN_ID=run-20260926T000000Z-1 AW_ITEM_ID6=abc123 python3 -m pytest tests/test_commit_run_trailers_env.py tests/test_git_commit_helper.py -o addopts="" -q` passing, with case (7) among the passes; then the same with the `conftest.py` hunk temporarily reverted, showing case (7) FAILING; then passing again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest tests/test_commit_run_trailers_env.py -o addopts="" -q` passing with the case count; then the same run with the E-03/E-04/E-05 hunks temporarily reverted, showing cases (1), (3), (5), (6) FAILING and (2), (4) passing; then passing again after restoring. Paste the bare `python3 -m pytest` summary line BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. The runner exports its run id and the item id6 into each agent turn as `AW_RUN_ID`/`AW_ITEM_ID6`, and `aw commit` stamps them as `AW-Run`/`AW-Item` trailers when it finds them valid. Outside a run nothing changes: the commit message is byte-identical. Raw `git commit` is NOT refused (maintainer ruling 2026-09-26), so untrailered agent commits remain possible and are read as unknown ownership. No reader is built here; Order 2 (`am1g38`) consumes these trailers.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the six paths in `- Scope-Paths:`. `runner_shared.py` is expected to be READ and not modified. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-07 must show the new tests FAILING before the change.

GENUINE STOP CONDITION: if E-01's scratch commit already carries both trailers, stop and report that the channel already exists.

Commit ONLY paths in `- Scope-Paths:` through `aw commit a6xbso -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `j2srcc` `done` with `--evidence` citing the executed plan.
