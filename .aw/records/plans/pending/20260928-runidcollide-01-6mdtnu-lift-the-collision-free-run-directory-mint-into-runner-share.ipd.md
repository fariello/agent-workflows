# IPD: Lift the collision-free run-directory mint into runner_shared so every caller inherits it

- Date: 2026-09-28
- Kind: child
- Concern: `runner_shared.new_run_id` mints `run-<UTC SECONDS>-<pid>`, so two calls from one process inside one second return the IDENTICAL id; the audit verb works around this privately with a `-N` suffix loop, and that suffixed shape is REFUSED by two independent analytics validators, so an audit run is silently dropped from the analytics corpus and loses its telemetry correlation.
- Scope: Add a `mint_run_dir(repo, run_id=None)` helper to `runner_shared` that makes the collision-free guarantee STRUCTURAL for every caller by using `mkdir(exist_ok=False)` as the atomic test; repoint `oc_runipd._fresh_audit_run_dir` and `runner_shared.initialize_run_core` at it; widen the two analytics run-id patterns (`run_analytics_privacy._RUN_ID_RE`, `run_analytics_telemetry._SHAPED_ID_KEYS["run_id"]`) to admit the `-N` suffix so a suffixed run is analyzable rather than skipped; and add behavioral coverage for the mint, for the two validators, and for the end-to-end sweep. Out of scope: changing the id's TIMESTAMP granularity (sub-second), renaming any existing run directory, `run_ledger_schema`'s unrelated `run-<hex>` grammar, and `run_viewer`'s substring run-id matching.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/run_analytics_privacy.py, agent_workflows/run_analytics_telemetry.py, tests/test_run_id_collision.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 2jtsup
- Blocks-Release: next
- Set: runidcollide
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 6mdtnu

## Workflow history

- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `2jtsup`. Re-measured every claim the item makes at HEAD `f2cbe1dd` rather than quoting it. Two corrections to the item are recorded as findings rather than as edits to the item: its central "silently overwrites" claim is FALSE for the queued path, which has an explicit refusal guard (F-2), and the test it cites as evidence no longer exists (F-3). The real, measured harm is downstream of the workaround the item describes as safe (F-5, F-6), which is what makes this a bug rather than a latent hazard. Chose the item's own third candidate remedy and recorded WHY the other two are refused (F-7, OQ-01).
- 2026-09-28 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make "each run gets its own directory" a property of the shared helper instead of a property one verb re-implements, and make the resulting id acceptable to the analytics boundary that currently refuses it.

Two things are wrong today and they compound. The mint can return a duplicate id, which every caller must handle for itself; exactly one caller does. And the shape that caller invents to handle it (`run-<stamp>-<pid>-2`) is refused by both analytics validators, so the workaround that protects the audit verb's verdict is the same thing that removes its run from the analytics corpus. Fixing the helper fixes both: callers inherit the guarantee, and the one suffixed shape in existence becomes a shape the corpus admits.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one shared, collision-free mint

- [ ] E-01 Add `mint_run_dir(repo, run_id=None)` to `runner_shared`, beside `new_run_id` and `state_root`, returning `(run_id, run_dir)` with the directory ALREADY CREATED. Body: resolve the root with `state_root(repo)`; take `run_id` verbatim when the caller supplies one; otherwise derive a base from `new_run_id()` and try `base`, then `f"{base}-2"`, `f"{base}-3"` ... using `mkdir(parents=True, exist_ok=False)` as the test, returning the first that succeeds and catching only `FileExistsError`. Bound the loop (99 attempts, matching the existing helper) and raise `DriverError` naming the root when it is exhausted.

  KEEP `new_run_id` ITSELF UNCHANGED, which is the whole point of this shape. The item records that changing the id FORMAT alters run ids repository-wide (how they sort, how the analytics reader parses them, what an operator has in shell history) and calls the mkdir loop "the smallest behavioral change: the id format is unchanged for the common case and only a genuine collision produces a suffixed name". This E-item implements exactly that reading. Do NOT add a random suffix and do NOT widen the timestamp; F-7 and OQ-01 record why both are refused, and either would make every id in the repository a new shape.

  AN EXPLICIT `run_id` MUST NOT BE SUFFIXED. `--run-id` exists on both hosts (`oc_runipd`'s and `agy_runipd`'s `start` parsers both register it as "Explicit unique run ID") and an operator who names a run wants THAT name or an error, never a silently different one; suffixing it would also break a caller who reuses the name to find the directory afterwards. So when `run_id` is given, let the `FileExistsError` from `mkdir(exist_ok=False)` surface as the existing refusal (E-02), rather than renaming around it.
  - Depends on: none
  - Expected outcome: `mint_run_dir` called twice in one second from one process returns two DIFFERENT ids and two directories that both exist; called with an explicit `run_id` that is already taken, it refuses instead of inventing a name.
  - Execution state: pending

- [ ] E-02 Repoint `runner_shared.initialize_run_core` at `mint_run_dir`, replacing its `run_id = getattr(args, "run_id", None) or new_run_id()` / `run_dir = state_root(repo) / run_id` / `if run_dir.exists(): raise DriverError(f"Run already exists: {run_id}")` trio. PRESERVE THAT REFUSAL MESSAGE VERBATIM for the explicit-`--run-id` case: it is the only user-visible string in this change, an operator may be matching on it, and F-2 records that this guard is the reason the item's "silently overwrites" claim does not hold for the queued path. The subsequent `for name in ("sessions", "outcomes", "prompts")` loop stays as it is (`mint_run_dir` creates the run directory, not its members).

  NOTE THE ORDERING CONSTRAINT rather than discovering it: this trio sits AFTER `enforce_freeze_time_refusal` and `enforce_orchestrator_shape_gate`, and a comment block immediately above it states that siting those gates before the run directory is a DECISION resting on "NO DURABLE WRITE: raising before `run_dir` is created ensures no run directory, events.jsonl, state.json, or prompt logs are created on a shape refusal". `mint_run_dir` CREATES a directory, so it must be called at exactly the point the current `mkdir` calls happen and not one line earlier.
  - Depends on: E-01
  - Expected outcome: a queued run start behaves identically for the common case and for an explicit duplicate `--run-id` (same refusal, same message), while two same-second automatic starts now get distinct directories instead of the second being refused.
  - Execution state: pending

- [ ] E-03 Replace the body of `oc_runipd._fresh_audit_run_dir` with a delegation to `runner_shared.mint_run_dir(repo)`, keeping the function and its name so the audit verb's call site is untouched. Rewrite its docstring: the current one is a 14-line argument for why the fix is DELIBERATELY NARROW and states that "the collision in the shared helper is reported as a finding with its own backlog carrier instead" - that carrier is `2jtsup`, this plan, so the docstring must now record that the guarantee moved into the shared helper rather than continuing to justify a local workaround. PRESERVE the measurement it carries (`{new_run_id(), new_run_id()}` had length 1) and the reason the guarantee must be structural rather than probabilistic; those are still true and still the rationale.

  DO NOT DELETE THE WRAPPER. It is a one-line delegation whose name documents the audit verb's requirement at the call site, and spec `i4gpto` R-7 is a requirement ABOUT this verb ("Each invocation MUST get its own directory, so a second opinion cannot erase the first"), so a named seam is worth keeping even when the body is shared.
  - Depends on: E-01
  - Expected outcome: exactly one implementation of the suffix loop exists in the package; `aw oc run audit <id6>` twice in one second still gets two directories, now via the shared helper.
  - Execution state: pending

### Task group 2: make the suffixed shape analyzable

- [ ] E-04 Widen `run_analytics_privacy._RUN_ID_RE` from `^run-\d{8}T\d{6}Z-\d+$` to admit an optional `-N` collision suffix (`^run-\d{8}T\d{6}Z-\d+(?:-\d+)?$`), and update the comment above it, which currently reads `A run id as the drivers mint it: ``run-<UTC stamp>-<pid>``` and is now incomplete. State in the comment that the optional trailing group is the collision suffix `mint_run_dir` appends, so a reader knows the alternative is not free text.

  THIS IS A PRIVACY BOUNDARY, so justify the widening on its own terms rather than on convenience. The pattern's job is to refuse a value that could carry identifying information; the added group admits only `-` followed by digits, which cannot express a path, a username, a hostname or a session id. The boundary is not loosened in kind, only in the count of trailing numeric components. `_PSEUDONYM_RE`, the alternative this key already accepts, is untouched.
  - Depends on: none
  - Expected outcome: `project_metric_facts({"run_id": "run-20260929T013453Z-1234-2"})` returns the value instead of raising `PrivacyRefusal`, while a non-numeric trailing component (`run-20260929T013453Z-good`) is still refused.
  - Execution state: pending

- [ ] E-05 Apply the same widening to `run_analytics_telemetry._SHAPED_ID_KEYS["run_id"]` and its `#:` comment (`A driver run id, exactly as the runners mint it: ``run-<UTC stamp>-<pid>```). These are two INDEPENDENT definitions of the same grammar in two modules, and both must move or the seam stays half-fixed: `runner_shared.telemetry_safe_context` pre-filters each correlation field through `validate_event`, so a run id this pattern refuses is DROPPED FROM THE EVENT rather than refused loudly (measured in F-6), leaving a telemetry stream that cannot be joined to its run.

  DO NOT UNIFY THE TWO PATTERNS INTO ONE SHARED CONSTANT. Each module's docstring states that it is a self-contained boundary (the telemetry one notes its sibling "carries the identical requirement, so the two agree"), and `run_analytics_privacy` imports only stdlib while `run_analytics_telemetry` imports `run_analytics_config`; introducing a cross-import to share a regex is a structural change neither module's contract asks for and is not what this bug needs. Keeping them separate and correct is the minimal fix; a third definition (`work_cmd._RUN_ID_RE`) ALREADY admits the suffix, which is the precedent that the grammar is duplicated deliberately (F-4).
  - Depends on: none
  - Expected outcome: `run_analytics_telemetry._validate_scalar("run_id", "run-20260929T013453Z-1234-2")` returns the value, so a suffixed run's telemetry events keep their `run_id` correlation field instead of having it silently dropped.
  - Execution state: pending

### Task group 3: pin all three behaviors

- [ ] E-06 Add `tests/test_run_id_collision.py` covering the MINT, with three behavioral cases that drive the real helper against a real temporary directory tree and assert on observable outcomes (never on source text): (1) two `mint_run_dir` calls in immediate succession from one process return two distinct ids AND two extant directories, which is the item's measured defect stated as a passing assertion; (2) a caller-supplied `run_id` is returned VERBATIM and is not suffixed; (3) a caller-supplied `run_id` whose directory already exists RAISES rather than renaming. Add a fourth case pinning that the first automatic id is UNSUFFIXED when the path is free, because the whole argument for this shape over a format change is that the common case keeps today's id.

  FORCE THE COLLISION DETERMINISTICALLY rather than racing the clock. Two back-to-back calls are overwhelmingly likely to land in one second, but "overwhelmingly likely" is a flaky test; monkeypatch `new_run_id` to return a FIXED string for the duration of case (1) so the second call provably takes the suffix branch. Build every directory under `tempfile`, never under the checkout's gitignored `.aw/records/runs/`.
  - Depends on: E-03
  - Expected outcome: a test module that fails on the pre-fix tree (no `mint_run_dir` exists) and passes post-fix, pinning distinctness, verbatim-explicit-id, refusal, and the unsuffixed common case.
  - Execution state: pending

- [ ] E-07 Extend the same file with the ANALYTICS half, which is what proves the widening was the point rather than incidental. Two cases: (1) both validators ACCEPT a `-N` suffixed id and still REFUSE a non-numeric trailing component, driven through the public-facing entry points (`privacy.project_metric_facts` and `telemetry.validate_event`) rather than the private scalar helpers, so the test pins the boundary a producer actually crosses; (2) an END-TO-END case building two terminal run directories under `tempfile`, one with a plain id and one with a `-2` suffixed id, and calling `run_analytics_cache.update_cache(..., build_facts=...)` over both, asserting BOTH produce a `rebuild` decision. Pre-fix that second run yields `skip` / `build-refused` (the exact measurement in F-5), so this case is the one that demonstrates user-visible harm rather than a pattern mismatch.

  ASSERT ON THE DECISION, NOT ON THE MESSAGE TEXT. `update_cache` returns `CacheDecision` records carrying `verdict` and `reason`; assert `verdict == "rebuild"` and that no decision has `reason == "build-refused"`. Also assert through `runner_shared.telemetry_safe_context` that `run_id` SURVIVES the pre-filter for a suffixed id, since a dropped-but-not-refused field is the failure mode E-05 exists to fix and it is invisible to a validator-only test.
  - Depends on: E-05, E-06
  - Expected outcome: the analytics corpus admits a suffixed run (no `build-refused`), and a suffixed run's telemetry keeps its `run_id` correlation field; both fail pre-fix.
  - Execution state: pending

## Project conventions discovered (Step 0)

- CITE CODE BY SYMBOL. Per spec `ipd-structure-and-linting` Section 10.2 (advisory `IPD-C801`), code is cited by symbol or quoted string, never by a bare offset. This plan cites `runner_shared.new_run_id`, `runner_shared.initialize_run_core`, `oc_runipd._fresh_audit_run_dir`, `run_analytics_privacy._RUN_ID_RE`, `run_analytics_telemetry._SHAPED_ID_KEYS`, `runner_shared.telemetry_safe_context` and `run_analytics_cache.update_cache`; the backlog item's own citations are all symbol-shaped and all still resolve, except the test file it names (F-3).
- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE. `AGENTS.md` and GUIDING_PRINCIPLES P16 forbid tests that read production source with `inspect`/`ast`/regex, count callers, or pin docstrings. E-06 and E-07 therefore drive the real functions against real temporary trees and assert on returned values, raised exceptions and `CacheDecision` verdicts. This specifically rules out the tempting "assert the suffix loop exists in exactly one place" structural test; the single-definition property is delivered by E-03's delegation, not by a census.
- `runner_shared` KEEPS FIRST-PARTY IMPORTS FUNCTION-LOCAL. `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared` allows exactly `render_stream` and `runner_profiles` at module level, "because an import added here changes the import graph for BOTH host drivers". `mint_run_dir` (E-01) needs only `state_root` and `new_run_id` from its own module plus stdlib, so it adds no import at all; do not reach for one.
- THE RUNS ROOT IS RESOLVED, NEVER ASSUMED. `runner_shared.state_root` routes through `project_context.resolve_project_context` so a `records_backend` of repository / companion / home each resolves correctly. `mint_run_dir` must call `state_root`, not join `.aw/records/runs` by hand, or it breaks a non-repository-backed project.
- RUN IDS ARE ALREADY MATCHED BY SUBSTRING, WHICH THIS PLAN DOES NOT CHANGE. `run_viewer.resolve_target_runs_detailed` matches a token against a run directory name with `t_str in run_p.name`, so asking for the exact base id `run-<stamp>-<pid>` ALREADY resolves the base run and every `-N` sibling (measured: three runs returned for one exact id). That is pre-existing behavior of a deliberately fuzzy resolver, it predates this plan, and narrowing it would change what `aw runs <token>` selects everywhere. Recorded so the executor does not "fix" it here; see the Deferred section.
- THIS PACKAGE SHIPS MORE THAN ONE `run-` GRAMMAR AND THEY ARE NOT THE SAME THING. `run_ledger_schema._RUN_ID_RE` is `^run-[0-9a-f]{8,}$` (a hex ledger run id), which a driver run id does not match and never did (measured: `is_run_id("run-20260929T013453Z-1234")` is False). It is unrelated to this defect and is out of scope; do not "align" the two.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-1 | THE ITEM'S CORE DEFECT REPRODUCES EXACTLY, at today's HEAD. `new_run_id` is a two-line function returning `f"run-{stamp}-{os.getpid()}"` over a `"%Y%m%dT%H%M%SZ"` stamp, so it carries one-second resolution and a per-process constant. Three immediate calls collapse to one value. | `python3 -c "from agent_workflows import runner_shared as rs; print(len({rs.new_run_id(), rs.new_run_id(), rs.new_run_id()}))"` -> `1`, at HEAD `f2cbe1dd`. Source read of `runner_shared.new_run_id`. |
| F-2 | THE ITEM'S "SILENTLY OVERWRITES" CLAIM IS FALSE FOR THE QUEUED PATH, and the correction MATTERS because it changes what the fix must preserve. The item says "the second silently overwrites the first's state and outcomes". `initialize_run_core` in fact carries `if run_dir.exists(): raise DriverError(f"Run already exists: {run_id}")` immediately after resolving the path, so a colliding queued start is REFUSED, not overwritten. The item is right that the collision exists and right that it is a defect; it is wrong about the consequence, which is a refused run rather than lost data. The fix therefore must NOT be sold as "stops overwriting", and E-02 must keep that refusal for the explicit-`--run-id` case. | Source read of `runner_shared.initialize_run_core` (the `run_id = getattr(args, "run_id", None) or new_run_id()` trio); reproduced the guard against a pre-existing directory in a temporary runs root -> refusal, no overwrite. `grep -rn "Run already exists"` -> exactly one site, in `runner_shared`. |
| F-3 | THE TEST THE ITEM CITES AS EVIDENCE NO LONGER EXISTS. The item's EVIDENCE line names `tests/test_standalone_verify.py::TheVerdictDestination::test_two_invocations_cannot_collide_so_a_second_opinion_cannot_erase_the_first`. That FILE was deleted wholesale by `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"). So the `-N` suffix behavior the audit verb depends on is currently pinned by NOTHING, and `_fresh_audit_run_dir` has zero test references. This plan must ADD coverage (E-06) rather than update a row, and E-03's refactor of that function is currently unprotected by any test, which is itself a reason to write E-06 first. | `ls tests/test_standalone_verify.py` -> No such file; `git log --diff-filter=D --oneline -1 -- tests/test_standalone_verify.py` -> `19313eed`; `grep -rln "_fresh_audit_run_dir" tests/` -> no matches. |
| F-4 | THE RUN-ID GRAMMAR IS DUPLICATED FOUR TIMES AND THE FOUR DISAGREE ABOUT THE SUFFIX, which is the actual bug surface. `work_cmd._RUN_ID_RE` is `^run-\d{8}T\d{6}Z-\d+(-\d+)?$` and ALREADY admits the `-N` suffix, with a comment naming it ("plus the `-N` collision suffix `oc_runipd._fresh_audit_run_dir` appends"). `run_analytics_privacy._RUN_ID_RE` and `run_analytics_telemetry._SHAPED_ID_KEYS["run_id"]` are both `^run-\d{8}T\d{6}Z-\d+$` and REFUSE it. `run_ledger_schema._RUN_ID_RE` is an unrelated hex grammar. So one consumer was updated when the suffix was introduced and two were not; this plan brings those two into line with the one that is already right. | The four patterns read from source; `work_cmd`'s comment quoted; measured acceptance: `work_cmd` pattern accepts `run-20260929T013453Z-1234-2`, the two analytics patterns refuse it, `run_ledger_schema.is_run_id` refuses BOTH shapes. |
| F-5 | A SUFFIXED RUN IS SILENTLY DROPPED FROM THE ANALYTICS CORPUS. This is the user-visible harm and it is MEASURED, not inferred. Building two terminal run directories, identical but for the id, and sweeping them with `run_analytics_cache.update_cache`: the plain id yields `rebuild / no-entry / rebuilt and published`; the `-2` id yields `skip / build-refused / privacy refusal: key 'run_id' must be a driver run id or a pseudonym`. The sweep isolates the failure per run by design, so nothing fails loudly; `aw runs analyze` reports it only as a `skipped` count and exit 1. So the audit verb's own run is the one run the analytics surface cannot see. | Two-run `update_cache` sweep in a temporary repo with a stub `build_facts`, decisions pasted above; `run_analytics_cache.build_entry` refusal reproduced directly for the suffixed id and accepted for the plain one; `run_analytics_cli`'s `exit_code = EXIT_FINDINGS if skipped else EXIT_OK`. |
| F-6 | A SUFFIXED RUN ALSO LOSES ITS TELEMETRY CORRELATION, AND LOSES IT SILENTLY, which is a SECOND independent consumer and a worse failure mode than a refusal. `runner_shared.telemetry_safe_context` pre-filters each correlation field through the telemetry schema and OMITS a field the schema rejects, deliberately ("one out-of-shape correlation value would discard EVERY event for that invocation"). Measured: for a plain id the filter keeps all seven fields; for a `-2` id it keeps six and DROPS `run_id`. So the stream is written, looks healthy, and cannot be joined back to its run. The audit verb reaches this seam for real: `oc_runipd.handle_audit_command` puts the suffixed id in `state["run_id"]`, and `run_opencode` builds `telemetry_identity` from `state.get("run_id")`. | `telemetry_safe_context` called with both shapes, kept-key sets pasted; that function's own docstring quoted on the drop-not-refuse decision; the `state["run_id"] = run_id` assignment in `handle_audit_command` and the `run_id=str(state.get("run_id") or "")` read in `run_opencode`. |
| F-7 | THE ITEM'S THREE CANDIDATE REMEDIES ARE NOT EQUIVALENT, AND TWO ARE REFUSED ON MEASUREMENT. Candidate "sub-second precision in the stamp": a microsecond stamp is collision-free in practice (200,000 back-to-back stamps all distinct; 0 duplicates in 100,000 immediate pairs) but it changes EVERY id's shape, so both analytics patterns refuse every run (measured: `run-20260929T013453123456Z-1234` refused by both), and it does so for runs that have no collision at all. Candidate "a short random suffix": same objection, plus it discards the sortability the current stamp gives and makes an id un-typeable. Candidate "lift the `mkdir(exist_ok=False)` loop into the helper": the format is unchanged for the common case, only a genuine collision produces a new shape, and that new shape is one a consumer already accepts (F-4). The item itself names the third as "the smallest behavioral change"; this measurement confirms it rather than taking it on faith. | Microsecond-stamp distinctness measured over 200k draws and 100k immediate pairs; all three candidate shapes run through both analytics validators with the accept/refuse matrix pasted; the item's own text quoted. |
| F-8 | THE SUFFIX SHAPE IS NOT NEW AND IS ALREADY REACHABLE IN PRODUCTION, so E-04/E-05 are fixing a shipped inconsistency rather than pre-emptively widening a boundary for a shape this plan invents. `_fresh_audit_run_dir` has minted `-N` ids since `807fdfd6` ("feat(audit): add 'aw oc run audit <id6>'"), `work_cmd` was updated to accept them, and the two analytics modules predate that (`345ab09f` for privacy, `0c7ea8df` for telemetry) and were never revisited. | `git log --oneline -1 -S'must be a driver run id' -- agent_workflows/run_analytics_privacy.py` -> `345ab09f`; `git log --oneline -1 -S'_SHAPED_ID_KEYS' -- agent_workflows/run_analytics_telemetry.py` -> `0c7ea8df`; `git log --oneline -1 807fdfd6` for the audit verb; `work_cmd._RUN_ID_RE`'s comment naming the suffix. |
| F-9 | NO SPEC PINS THE ID FORMAT, AND THE ONE SPEC THAT DESCRIBES THE COLLISION IS `draft`. Spec `i4gpto` R-7 requires that each audit invocation get its own directory and states the mechanism ("suffixes until the path is free, using `mkdir(exist_ok=False)` as an atomic test"); its Status is `draft`. Its R-7 remains TRUE after this change, because the mechanism it names is the one being lifted, not replaced. Approved spec `25kzda` mentions `"run_id": "run-<id>"` in an example payload and pins no grammar. So this plan amends no spec and declares no `.spec.md` in `Scope-Paths`. | `grep -rn "run-<UTC"` across `.aw/records/specs/` -> one hit, in the `draft` `i4gpto`; its R-6/R-7 read in full; `grep -n "run_id" ` on `25kzda` -> the illustrative `run-<id>` line only. |
| F-10 | THE PACKAGE CARRIES TWO INDEPENDENT RUN-ID TIMESTAMP PARSERS AND NEITHER IS DISTURBED BY THE SUFFIX, which is what makes this change safe for the viewer. `run_viewer` recovers a start time with `re.search(r"(\d{8})T(\d{6})", run.run_id)`, which matches the same groups in a suffixed id. `workflow_artifacts_prune._parse_run_date` reads the FIRST 8 characters, which for any `run-`-prefixed id is `"run-2026"` and is not a date, so it returns None for a plain id and equally for a suffixed one - pre-existing behavior, unchanged, and not this plan's to fix. | Both parsers exercised against plain and suffixed ids: the viewer regex returns `('20260929','013453')` for both; `_parse_run_date("run-20260929T013453Z-1234")` -> `None`, identical for the suffixed form. |

## Proposed changes (ordered, validatable)

1. `runner_shared.mint_run_dir(repo, run_id=None)`: one shared, atomic, collision-free run-directory mint returning `(run_id, run_dir)` (E-01).
2. `runner_shared.initialize_run_core`: use it, preserving the `Run already exists: <id>` refusal for an explicit `--run-id` (E-02).
3. `oc_runipd._fresh_audit_run_dir`: delegate to it; rewrite the docstring that currently argues for keeping the fix local (E-03).
4. `run_analytics_privacy._RUN_ID_RE`: admit the optional `-N` collision suffix (E-04).
5. `run_analytics_telemetry._SHAPED_ID_KEYS["run_id"]`: the same widening, for the second independent definition (E-05).
6. New `tests/test_run_id_collision.py`: the mint's four behaviors (E-06) plus the analytics acceptance and the end-to-end sweep (E-07).

WHAT CHANGES FOR A USER, STATED PLAINLY. In the common case, nothing: the id is byte-identical to today's. Two automatic runs starting in the same second, which today means the second is REFUSED with `Run already exists` (F-2), now both start, the second as `<id>-2`. A `-N` suffixed run, which today is dropped from `aw runs analyze` with a `skip / build-refused` and loses its telemetry `run_id` field (F-5, F-6), is now analyzed normally. An explicit `--run-id` behaves exactly as it does today, including its refusal.

## Deferred / out of scope (with reason)

- CHANGING THE TIMESTAMP GRANULARITY OR ADDING A RANDOM COMPONENT. Refused on measurement, not deferred: F-7 shows either would change every id's shape (and be refused by both analytics patterns for every run) to solve a problem only a colliding run has. The item itself names the mkdir loop as the smallest change.
  - Carrier-Declined: Nothing is owed. This is a DECISION recorded against two alternatives, not unfinished work: the chosen remedy fully closes the collision, so there is no residue for a carrier to own. Filing an item to "reconsider sub-second stamps" would invite re-litigating a settled choice with no new evidence.
- `run_viewer`'s SUBSTRING RUN-ID MATCHING. `resolve_target_runs_detailed` matches with `t_str in run_p.name`, so the exact base id already resolves the base run plus every `-N` sibling (measured: 3 for 1). This is pre-existing behavior of a deliberately fuzzy resolver that also matches setids and partial ids, it is not caused by this change, and narrowing it would alter what `aw runs <token>` selects for every token.
  - Carrier-Declined: This plan owes nothing here, and the behavior is arguably CORRECT rather than defective: an operator naming a base id plausibly wants that run and its collision siblings, which are by construction the same second's work. Nothing regresses, and naming a carrier would assert a defect this plan has not established.
- RENAMING OR MIGRATING EXISTING RUN DIRECTORIES. The runs root is gitignored, disposable local state; no historical directory needs to change for either the mint or the widened patterns to be correct.
  - Carrier-Declined: Nothing is owed. Both changes are forward-compatible with every id already on disk (F-10 measures that both timestamp parsers are indifferent to the suffix), so there is no migration to perform and no residue.
- UNIFYING THE FOUR `run-` GRAMMARS INTO ONE DEFINITION. `run_ledger_schema`'s is a genuinely different grammar for a different id (`run-<hex>`), and the three driver-id copies live in modules whose contracts state they are self-contained boundaries; `run_analytics_privacy` imports only stdlib today. A cross-module shared constant is a structural change this bug does not need.
  - Carrier-Declined: This plan owes nothing, and the duplication is DELIBERATE and documented at each site rather than being residue this plan leaves behind. `run_analytics_telemetry`'s docstring states the sibling "carries the identical requirement, so the two agree", which is the convention; after E-04/E-05 all three driver-id copies agree again, so the plan reduces divergence to zero rather than leaving any. Searched for an existing owner (`aw find backlog "run id"` -> no matching backlog) before declining.
- `run_ledger_schema.is_run_id` REFUSING DRIVER RUN IDS. Measured and real, and entirely separate: it validates ledger run ids (`run-<hex>`), a different identifier with a different producer. It refuses today's plain id as readily as a suffixed one, so this plan neither creates nor worsens it.
  - Carrier-Declined: Nothing is owed. These are two different identifiers that happen to share a `run-` prefix; a validator for one correctly refusing the other is not a defect, so there is no work for a carrier to hold.

## Scope check

- Over-scope: none. Every edit is inside one of the five declared `Scope-Paths`, and the five deferrals above are precisely the things a reader might expect to be swept in.
- Under-scope: the backlog item frames the fix as touching only the shared helper. This plan also widens the two analytics patterns, because F-5 and F-6 measure that the suffix the helper produces is refused by one consumer and silently dropped by another, so a helper-only change would move the collision guarantee into shared code while leaving the shape it produces unanalyzable - shipping the very half-fix the item describes as "worked around locally, not fixed". The item's requirements are not modified: its preferred third candidate is implemented as written, and its two corrections (F-2, F-3) are recorded here as findings rather than edited into it.

## Required tests / validation

- `python3 -m pytest tests/test_run_id_collision.py` must pass post-fix, with the pasted `N passed` line.
- The same file must FAIL pre-fix. Capture that before applying E-01..E-05. The mint cases fail with `AttributeError` (no `mint_run_dir`), which is a weak red; the ANALYTICS cases (E-07) are the meaningful pre-fix proof because they fail on shipped behavior, so capture those specifically by writing and running E-07's cases against the unmodified `run_analytics_*` modules.
- Full bare suite `python3 -m pytest` must pass, with actual output pasted. Bare per AGENTS: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. RE-DERIVE YOUR OWN BEFORE-BASELINE AND STATE THE DELTA AGAINST IT: authoring measured `3189 passed, 2 skipped` on a clean tree at HEAD `f2cbe1dd`, and this tree moves by tens of tests a day, so a transcribed total is meaningless by the time this executes. Any delta beyond the cases E-06/E-07 add is this plan's to explain.
- `python3 -m pytest -o addopts="" -q tests/test_run_analytics.py tests/test_runner_shared.py tests/test_run_viewer.py tests/test_commit_run_trailers_env.py` as the targeted neighbour set: `test_run_analytics.py` asserts the privacy run-id boundary directly (it requires `run-20260908T100000Z-good` to be REFUSED and the plain id ACCEPTED, so E-04 must not break it), `test_runner_shared.py` is the guard harness over the module gaining `mint_run_dir`, and `test_commit_run_trailers_env.py` already exercises the `-N` suffixed shape through `work_cmd`.
- Direct end-to-end measurement, pasted: the two-run `update_cache` sweep from F-5 showing both decisions as `rebuild` post-fix, and `telemetry_safe_context` keeping `run_id` for a suffixed id (F-6).
- STAGE ANY PRE-FIX COMPARISON IN MEMORY, NOT BY MUTATING A TRACKED FILE. All four production files here are shared-checkout files, and a `git stash`/`git checkout` restore around a minute-long suite run can discard a co-worker's concurrent edit. Patch the patterns from a scratch script or a pytest plugin outside the tree, and paste `git status --short` before and after each proof.

## Spec / documentation sync

- NO SPEC AMENDMENT REQUIRED, verified rather than assumed (F-9). No spec pins the run-id grammar. `Scope-Paths` therefore declares no `.spec.md`, which is why the runners' spec-edit announcer will report none for this plan.
- SPEC `i4gpto` R-7 IS PRESERVED, NOT CONTRADICTED, and the distinction is worth stating because that spec names the mechanism. R-7 requires each audit invocation to get its own directory and describes the `mkdir(exist_ok=False)` suffix loop; E-03 moves that exact mechanism into a shared function and keeps the named wrapper, so the requirement holds by the same argument it always did. The spec is `draft` and this plan does not edit it; if a later plan promotes it, its R-7 prose may then be updated to say the mechanism is shared.
- THE IN-FILE DOCUMENTATION THAT MUST CHANGE is `oc_runipd._fresh_audit_run_dir`'s docstring (E-03), which currently argues for keeping the fix narrow and says the shared-helper collision "is reported as a finding with its own backlog carrier instead". That carrier is this plan, so leaving the docstring as-is would have it describing a decision this change reverses. The two `#:`/`#` comments above the widened patterns (E-04, E-05) likewise both currently state the grammar as `run-<UTC stamp>-<pid>` and must name the optional suffix.
- NO USER-FACING DOC CHANGE. `--run-id`'s help text ("Explicit unique run ID (default: auto-generated timestamped ID)") stays true: the default is still a timestamped id and an explicit one is still taken verbatim. No `docs/` page states the id grammar.

## Open questions

### OQ-01: Should this change the id FORMAT (sub-second stamp or random component) instead of suffixing on collision?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT AND FROM THE ITEM'S OWN PREFERENCE, so this is not a human decision. The item lists three candidates and names the third ("lifting the `mkdir(exist_ok=False)` loop into the helper") as "the smallest behavioral change: the id format is unchanged for the common case and only a genuine collision produces a suffixed name". F-7 tests that claim rather than trusting it: a microsecond stamp is indeed collision-free (0 duplicates in 100,000 immediate pairs) but is REFUSED by both analytics run-id patterns for EVERY run, so it converts a rare-collision defect into a universal one, and it changes what an operator has in shell history for no benefit to the 99.99 percent of runs that never collide. A random suffix shares that objection and additionally destroys the id's sortability. The suffix approach's one cost - that `-N` is a new shape - is already paid (F-8: the audit verb has minted them since `807fdfd6`) and is what E-04/E-05 close. Escalating would ask the maintainer to re-decide something the item already decided and the measurement confirms.

### OQ-02: Should the two analytics run-id patterns be unified into one shared constant while both are being edited?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AS "NO", FROM THE MODULES' OWN STATED CONTRACTS. Both modules document themselves as self-contained validation boundaries, and `run_analytics_telemetry`'s docstring explicitly records that the duplication is intentional agreement rather than drift ("The sibling privacy projector carries the identical requirement, so the two agree"). `run_analytics_privacy` imports only stdlib; introducing a cross-import (or a third module to hold the constant) to share an eight-token regex is a structural change neither contract asks for and would widen a four-line bug fix into an import-graph change across the analytics package. A fourth definition in `work_cmd` carries a comment explaining that it deliberately does NOT import `runner_shared` because that "would pull the whole runner into every `aw commit`", which is the established precedent that this grammar is duplicated on purpose. The residual risk - that a future third shape updates two of three copies again - is real and is exactly what E-07 pins behaviorally at both boundaries.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a transcript that calls `runner_shared.mint_run_dir` TWICE against a temporary runs root with `new_run_id` monkeypatched to a FIXED value, showing two distinct returned ids (`<base>` and `<base>-2`) and `is_dir()` True for both paths. Then paste a third call with an explicit `run_id` already on disk, showing the raised exception and its message. Also paste the function source once, to show it calls `state_root` (not a hand-joined `.aw/records/runs`) and catches only `FileExistsError`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `grep -n "Run already exists" agent_workflows/runner_shared.py` showing the refusal message is still present and still the only copy, plus the rewritten call site source showing `mint_run_dir` is called at the SAME point the old `mkdir` calls were (after `enforce_orchestrator_shape_gate`, before the `("sessions", "outcomes", "prompts")` loop), per the no-durable-write-before-the-gates constraint E-02 cites. Then paste an observed run start with a duplicate explicit `--run-id` showing the unchanged refusal.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new `_fresh_audit_run_dir` body showing it delegates to `runner_shared.mint_run_dir`, and the rewritten docstring, confirming it no longer claims the collision "is reported as a finding with its own backlog carrier instead" and that it still records the original measurement. Paste a transcript calling `_fresh_audit_run_dir` twice against a temporary repo, showing two distinct extant directories, so the delegation is proven to preserve spec `i4gpto` R-7 behaviorally and not just structurally.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste THREE measurements through the public entry point `run_analytics_privacy.project_metric_facts`: a suffixed id ACCEPTED (returned unchanged), a plain id still ACCEPTED, and `run-20260908T100000Z-good` still REFUSED with `PrivacyRefusal`. The third is required because `tests/test_run_analytics.py` asserts that exact refusal, so it is the shipped assertion E-04 must not break. Paste the updated comment beside the pattern showing it now names the collision suffix.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste a full `run_analytics_telemetry.validate_event` call (not the private scalar helper) on an event carrying a suffixed `run_id`, showing it validates, and the same for a malformed trailing component showing it still refuses. Then paste `runner_shared.telemetry_safe_context` called with the seven-field correlation context for BOTH a plain and a suffixed id, showing `run_id` is now KEPT in both; pre-fix the suffixed case kept six of seven and dropped `run_id` (F-6), so this before/after pair is the proof that the silent-drop path is closed.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the PRE-fix run of `python3 -m pytest tests/test_run_id_collision.py` and the POST-fix run showing `N passed`. State explicitly that the mint cases fail pre-fix only with `AttributeError` (a weak red, since the symbol does not exist) so the record is honest about what that red proves; V-07 carries the strong red. Also paste `git status --short` empty, proving no tracked file was mutated to stage a comparison.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: THREE pasted artifacts. (1) The STRONG PRE-FIX RED: E-07's analytics cases run against the UNMODIFIED `run_analytics_*` modules, showing the suffixed run decided `skip` / `build-refused` and the telemetry `run_id` dropped - this is the measurement of shipped behavior that gives the fix its meaning, and it must be captured before E-04/E-05 are applied (in memory, per the validation section). (2) The POST-fix two-run `update_cache` sweep showing BOTH decisions `rebuild` and no decision carrying `reason == "build-refused"`. (3) YOUR OWN re-derived clean-tree bare baseline, then the post-change bare `python3 -m pytest`, with the delta stated against your baseline and accounted for by the cases E-06/E-07 add; do not state a delta against the `3189 passed, 2 skipped` this plan records. Additionally paste the targeted neighbour run over `tests/test_run_analytics.py tests/test_runner_shared.py tests/test_run_viewer.py tests/test_commit_run_trailers_env.py`, since those four are the modules that already touch the run-id grammar or the changed module.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

This plan is `to-review` and has NOT been reviewed or approved; it must not execute until a human approves it. Per the execution contract: commit only the files changed, limited to the declared `Scope-Paths`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Paste actual runner output for every test claim; do not assert a passing suite that was not run.

Post-gate lifecycle: after every `E-*` is performed and every `V-*` carries real observed evidence, run `aw ipd lint --phase pre-transition` and confirm it reports conforming, then move this plan to `.aw/records/plans/executed/` via the tooled transition. Do not mark it executed while any `V-*` result is `pending`. The backlog item `2jtsup` carries `- Blocks-Release: next`, which this plan inherits; the item reaches `graduated` on handoff and may only close `done` once this plan is genuinely executed, which is what preserves the release gate.

- Size assessment: standard
- Cohesion rationale: not required
