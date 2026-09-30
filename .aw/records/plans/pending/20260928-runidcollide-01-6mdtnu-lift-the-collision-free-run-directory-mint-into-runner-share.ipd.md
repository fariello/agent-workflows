# IPD: Lift the collision-free run-directory mint into runner_shared so every caller inherits it

- Date: 2026-09-28
- Kind: child
- Concern: `runner_shared.new_run_id` mints `run-<UTC SECONDS>-<pid>`, so two calls from one process inside one second return the IDENTICAL id; the audit verb works around this privately with a `-N` suffix loop, and that suffixed shape is REFUSED by two independent analytics validators, so an audit run is silently dropped from the analytics corpus and loses its telemetry correlation.
- Scope: Add a `mint_run_dir(repo, run_id=None)` helper to `runner_shared` that makes the collision-free guarantee STRUCTURAL for every caller by using `mkdir(exist_ok=False)` as the atomic test; repoint `oc_runipd._fresh_audit_run_dir` and `runner_shared.initialize_run_core` at it; widen the two analytics run-id patterns (`run_analytics_privacy._RUN_ID_RE`, `run_analytics_telemetry._SHAPED_ID_KEYS["run_id"]`) to admit the `-N` suffix so a suffixed run is analyzable rather than skipped; and add behavioral coverage for the mint, for the two validators, and for the end-to-end sweep. Out of scope: changing the id's TIMESTAMP granularity (sub-second), renaming any existing run directory, `run_ledger_schema`'s unrelated `run-<hex>` grammar, and `run_viewer`'s substring run-id matching.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/run_analytics_privacy.py, agent_workflows/run_analytics_telemetry.py, tests/test_run_id_collision.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 2jtsup
- Blocks-Release: next
- Set: runidcollide
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 6mdtnu
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (aw set): plan-review: revisions applied; PR-901..PR-905 fixed

- 2026-09-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901 (high), PR-902 (medium), PR-903, PR-904, PR-905 (low), all FIXED. Findings recorded in `.aw/records/reviews/20260928-runidcollide-01-6mdtnu-...review.md`. This is an unusually well-measured plan: F-1, F-4, F-5, F-6, F-7, F-9 and F-10 all reproduced exactly, including the `skip`/`build-refused` decision with its verbatim refusal text and the 7-kept-versus-6-kept telemetry drop, and the PROPOSED widening was applied in memory and behaved exactly as predicted across eight shapes at both public boundaries while preserving the one refusal the shipped suite asserts (new F-15). The substantive finding is PR-901: E-01 and E-02 CONTRADICTED each other about the explicit-duplicate refusal, and E-01's literal reading ("let the `FileExistsError` surface") changes a user-visible error string, leaks an absolute path into it, and escapes the `except DriverError` handler that renders it; resolved to translate inside `mint_run_dir`, recorded as OQ-03. Also: the `exists()` -> `mkdir(exist_ok=False)` swap changes one predicate (a dangling symlink is now refused, an improvement) which V-02 must now paste; a second convention citation points at a file `19313eed` deleted, like F-3's; the gate gained the conditional runner/executor finalize ownership it lacked; and the suite baseline has already drifted from `3189` to `3246`, which vindicates the plan's own re-derive instruction.
- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `2jtsup`. Re-measured every claim the item makes at HEAD `f2cbe1dd` rather than quoting it. Two corrections to the item are recorded as findings rather than as edits to the item: its central "silently overwrites" claim is FALSE for the queued path, which has an explicit refusal guard (F-2), and the test it cites as evidence no longer exists (F-3). The real, measured harm is downstream of the workaround the item describes as safe (F-5, F-6), which is what makes this a bug rather than a latent hazard. Chose the item's own third candidate remedy and recorded WHY the other two are refused (F-7, OQ-01).
- 2026-09-28 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make "each run gets its own directory" a property of the shared helper instead of a property one verb re-implements, and make the resulting id acceptable to the analytics boundary that currently refuses it.

Two things are wrong today and they compound. The mint can return a duplicate id, which every caller must handle for itself; exactly one caller does. And the shape that caller invents to handle it (`run-<stamp>-<pid>-2`) is refused by both analytics validators, so the workaround that protects the audit verb's verdict is the same thing that removes its run from the analytics corpus. Fixing the helper fixes both: callers inherit the guarantee, and the one suffixed shape in existence becomes a shape the corpus admits.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one shared, collision-free mint

- [x] E-01 Add `mint_run_dir(repo, run_id=None)` to `runner_shared`, beside `new_run_id` and `state_root`, returning `(run_id, run_dir)` with the directory ALREADY CREATED. Body: resolve the root with `state_root(repo)`; take `run_id` verbatim when the caller supplies one; otherwise derive a base from `new_run_id()` and try `base`, then `f"{base}-2"`, `f"{base}-3"` ... using `mkdir(parents=True, exist_ok=False)` as the test, returning the first that succeeds and catching only `FileExistsError`. Bound the loop (99 attempts, matching the existing helper) and raise `DriverError` naming the root when it is exhausted.

  KEEP `new_run_id` ITSELF UNCHANGED, which is the whole point of this shape. The item records that changing the id FORMAT alters run ids repository-wide (how they sort, how the analytics reader parses them, what an operator has in shell history) and calls the mkdir loop "the smallest behavioral change: the id format is unchanged for the common case and only a genuine collision produces a suffixed name". This E-item implements exactly that reading. Do NOT add a random suffix and do NOT widen the timestamp; F-7 and OQ-01 record why both are refused, and either would make every id in the repository a new shape.

  AN EXPLICIT `run_id` MUST NOT BE SUFFIXED. `--run-id` exists on both hosts (`oc_runipd`'s and `agy_runipd`'s `start` parsers both register it as "Explicit unique run ID") and an operator who names a run wants THAT name or an error, never a silently different one; suffixing it would also break a caller who reuses the name to find the directory afterwards.

  TRANSLATE THE `FileExistsError` INTO `DriverError(f"Run already exists: {run_id}")` INSIDE `mint_run_dir`; DO NOT LET IT PROPAGATE. The authored wording ("let the `FileExistsError` ... surface as the existing refusal") is ambiguous and its literal reading is wrong on three counts, each measured at review. FIRST, the message changes: the literal reading produces `FileExistsError: [Errno 17] File exists: '/tmp/.../run-20260929T013453Z-1234'` where the shipped refusal is `DriverError: Run already exists: run-20260929T013453Z-1234`, which directly contradicts E-02's own "PRESERVE THAT REFUSAL MESSAGE VERBATIM". SECOND, it LEAKS AN ABSOLUTE PATH into a user-facing error, which is the class of string `aw sanitize` exists to keep out of shared output. THIRD, `DriverError` is a deliberately-shaped catchable class that both hosts handle (`agy_runipd`'s comments record that a non-`DriverError` "raised here could NOT be caught by `except DriverError`"), so a bare `FileExistsError` escapes the handler that is supposed to render this refusal. Verified at review that the translating form reproduces the shipped string byte-for-byte while the propagating form does not.

  ONE PREDICATE CHANGE IS UNAVOIDABLE AND IS AN IMPROVEMENT, recorded so it is not mistaken for a regression. The shipped guard is `run_dir.exists()`, which FOLLOWS a symlink; `mkdir(exist_ok=False)` does not. Measured: for a DANGLING SYMLINK at the run path, `exists()` returns `False` (so the shipped code proceeds and then fails later, deeper in the run) while `mkdir` raises `FileExistsError` (so the new code refuses cleanly up front). For an existing directory and for an existing plain FILE the two agree. State this in V-02 rather than claiming byte-identical predicate behavior.
  - Depends on: none
  - Expected outcome: `mint_run_dir` called twice in one second from one process returns two DIFFERENT ids and two directories that both exist; called with an explicit `run_id` that is already taken, it raises `DriverError` whose message is exactly `Run already exists: <run_id>` and contains no filesystem path.
  - Execution state: performed

- [x] E-02 Repoint `runner_shared.initialize_run_core` at `mint_run_dir`, replacing its `run_id = getattr(args, "run_id", None) or new_run_id()` / `run_dir = state_root(repo) / run_id` / `if run_dir.exists(): raise DriverError(f"Run already exists: {run_id}")` trio. PRESERVE THAT REFUSAL MESSAGE VERBATIM for the explicit-`--run-id` case: it is the only user-visible string in this change, an operator may be matching on it, and F-2 records that this guard is the reason the item's "silently overwrites" claim does not hold for the queued path. E-01 owns the translation that makes this possible; verified at review that the message survives byte-for-byte only if `mint_run_dir` raises `DriverError` itself rather than letting `FileExistsError` propagate (F-11). The subsequent `for name in ("sessions", "outcomes", "prompts")` loop stays as it is (`mint_run_dir` creates the run directory, not its members).

  NOTE WHAT ACTUALLY CHANGES ON DISK, which the authored item glossed. The shipped code NEVER creates `run_dir` itself: it checks `exists()` and then mkdirs only the three MEMBER directories with `parents=True, exist_ok=True`, so the run directory comes into being as a side effect of the first member. After this change `mint_run_dir` creates `run_dir` explicitly with `exist_ok=False` and the member loop then fills it. That is the intended atomicity (the directory's creation IS the lock), and it is why no caller can be relying on the old tolerance: the shipped guard already refused any pre-existing path, so by construction no caller ever passed one.

  NOTE THE ORDERING CONSTRAINT rather than discovering it: this trio sits AFTER `enforce_freeze_time_refusal` and `enforce_orchestrator_shape_gate`, and a comment block immediately above it states that siting those gates before the run directory is a DECISION resting on "NO DURABLE WRITE: raising before `run_dir` is created ensures no run directory, events.jsonl, state.json, or prompt logs are created on a shape refusal". `mint_run_dir` CREATES a directory, so it must be called at exactly the point the current `mkdir` calls happen and not one line earlier.
  - Depends on: E-01
  - Expected outcome: a queued run start behaves identically for the common case and for an explicit duplicate `--run-id` (same refusal, same message), while two same-second automatic starts now get distinct directories instead of the second being refused.
  - Execution state: performed

- [x] E-03 Replace the body of `oc_runipd._fresh_audit_run_dir` with a delegation to `runner_shared.mint_run_dir(repo)`, keeping the function and its name so the audit verb's call site is untouched. Rewrite its docstring: the current one is a 14-line argument for why the fix is DELIBERATELY NARROW and states that "the collision in the shared helper is reported as a finding with its own backlog carrier instead" - that carrier is `2jtsup`, this plan, so the docstring must now record that the guarantee moved into the shared helper rather than continuing to justify a local workaround. PRESERVE the measurement it carries (`{new_run_id(), new_run_id()}` had length 1) and the reason the guarantee must be structural rather than probabilistic; those are still true and still the rationale.

  DO NOT DELETE THE WRAPPER. It is a one-line delegation whose name documents the audit verb's requirement at the call site, and spec `i4gpto` R-7 is a requirement ABOUT this verb ("Each invocation MUST get its own directory, so a second opinion cannot erase the first"), so a named seam is worth keeping even when the body is shared.
  - Depends on: E-01
  - Expected outcome: exactly one implementation of the suffix loop exists in the package; `aw oc run audit <id6>` twice in one second still gets two directories, now via the shared helper.
  - Execution state: performed

### Task group 2: make the suffixed shape analyzable

- [x] E-04 Widen `run_analytics_privacy._RUN_ID_RE` from `^run-\d{8}T\d{6}Z-\d+$` to admit an optional `-N` collision suffix (`^run-\d{8}T\d{6}Z-\d+(?:-\d+)?$`), and update the comment above it, which currently reads `A run id as the drivers mint it: ``run-<UTC stamp>-<pid>``` and is now incomplete. State in the comment that the optional trailing group is the collision suffix `mint_run_dir` appends, so a reader knows the alternative is not free text.

  THIS IS A PRIVACY BOUNDARY, so justify the widening on its own terms rather than on convenience. The pattern's job is to refuse a value that could carry identifying information; the added group admits only `-` followed by digits, which cannot express a path, a username, a hostname or a session id. The boundary is not loosened in kind, only in the count of trailing numeric components. `_PSEUDONYM_RE`, the alternative this key already accepts, is untouched.
  - Depends on: none
  - Expected outcome: `project_metric_facts({"run_id": "run-20260929T013453Z-1234-2"})` returns the value instead of raising `PrivacyRefusal`, while a non-numeric trailing component (`run-20260929T013453Z-good`) is still refused.
  - Execution state: performed

- [x] E-05 Apply the same widening to `run_analytics_telemetry._SHAPED_ID_KEYS["run_id"]` and its `#:` comment (`A driver run id, exactly as the runners mint it: ``run-<UTC stamp>-<pid>```). These are two INDEPENDENT definitions of the same grammar in two modules, and both must move or the seam stays half-fixed: `runner_shared.telemetry_safe_context` pre-filters each correlation field through `validate_event`, so a run id this pattern refuses is DROPPED FROM THE EVENT rather than refused loudly (measured in F-6), leaving a telemetry stream that cannot be joined to its run.

  DO NOT UNIFY THE TWO PATTERNS INTO ONE SHARED CONSTANT. Each module's docstring states that it is a self-contained boundary (the telemetry one notes its sibling "carries the identical requirement, so the two agree"), and `run_analytics_privacy` imports only stdlib while `run_analytics_telemetry` imports `run_analytics_config`; introducing a cross-import to share a regex is a structural change neither module's contract asks for and is not what this bug needs. Keeping them separate and correct is the minimal fix; a third definition (`work_cmd._RUN_ID_RE`) ALREADY admits the suffix, which is the precedent that the grammar is duplicated deliberately (F-4).
  - Depends on: none
  - Expected outcome: `run_analytics_telemetry._validate_scalar("run_id", "run-20260929T013453Z-1234-2")` returns the value, so a suffixed run's telemetry events keep their `run_id` correlation field instead of having it silently dropped.
  - Execution state: performed

### Task group 3: pin all three behaviors

- [x] E-06 Add `tests/test_run_id_collision.py` covering the MINT, with three behavioral cases that drive the real helper against a real temporary directory tree and assert on observable outcomes (never on source text): (1) two `mint_run_dir` calls in immediate succession from one process return two distinct ids AND two extant directories, which is the item's measured defect stated as a passing assertion; (2) a caller-supplied `run_id` is returned VERBATIM and is not suffixed; (3) a caller-supplied `run_id` whose directory already exists RAISES rather than renaming. Add a fourth case pinning that the first automatic id is UNSUFFIXED when the path is free, because the whole argument for this shape over a format change is that the common case keeps today's id.

  FORCE THE COLLISION DETERMINISTICALLY rather than racing the clock. Two back-to-back calls are overwhelmingly likely to land in one second, but "overwhelmingly likely" is a flaky test; monkeypatch `new_run_id` to return a FIXED string for the duration of case (1) so the second call provably takes the suffix branch. Build every directory under `tempfile`, never under the checkout's gitignored `.aw/records/runs/`.
  - Depends on: E-03
  - Expected outcome: a test module that fails on the pre-fix tree (no `mint_run_dir` exists) and passes post-fix, pinning distinctness, verbatim-explicit-id, refusal, and the unsuffixed common case.
  - Execution state: performed

- [x] E-07 Extend the same file with the ANALYTICS half, which is what proves the widening was the point rather than incidental. Two cases: (1) both validators ACCEPT a `-N` suffixed id and still REFUSE a non-numeric trailing component, driven through the public-facing entry points (`privacy.project_metric_facts` and `telemetry.validate_event`) rather than the private scalar helpers, so the test pins the boundary a producer actually crosses; (2) an END-TO-END case building two terminal run directories under `tempfile`, one with a plain id and one with a `-2` suffixed id, and calling `run_analytics_cache.update_cache(..., build_facts=...)` over both, asserting BOTH produce a `rebuild` decision. Pre-fix that second run yields `skip` / `build-refused` (the exact measurement in F-5), so this case is the one that demonstrates user-visible harm rather than a pattern mismatch.

  ASSERT ON THE DECISION, NOT ON THE MESSAGE TEXT. `update_cache` returns `CacheDecision` records carrying `verdict` and `reason`; assert `verdict == "rebuild"` and that no decision has `reason == "build-refused"`. Also assert through `runner_shared.telemetry_safe_context` that `run_id` SURVIVES the pre-filter for a suffixed id, since a dropped-but-not-refused field is the failure mode E-05 exists to fix and it is invisible to a validator-only test.
  - Depends on: E-05, E-06
  - Expected outcome: the analytics corpus admits a suffixed run (no `build-refused`), and a suffixed run's telemetry keeps its `run_id` correlation field; both fail pre-fix.
  - Execution state: performed

## Project conventions discovered (Step 0)

- CITE CODE BY SYMBOL. Per spec `ipd-structure-and-linting` Section 10.2 (advisory `IPD-C801`), code is cited by symbol or quoted string, never by a bare offset. This plan cites `runner_shared.new_run_id`, `runner_shared.initialize_run_core`, `oc_runipd._fresh_audit_run_dir`, `run_analytics_privacy._RUN_ID_RE`, `run_analytics_telemetry._SHAPED_ID_KEYS`, `runner_shared.telemetry_safe_context` and `run_analytics_cache.update_cache`; the backlog item's own citations are all symbol-shaped and all still resolve, except the test file it names (F-3).
- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE. `AGENTS.md` and GUIDING_PRINCIPLES P16 forbid tests that read production source with `inspect`/`ast`/regex, count callers, or pin docstrings. E-06 and E-07 therefore drive the real functions against real temporary trees and assert on returned values, raised exceptions and `CacheDecision` verdicts. This specifically rules out the tempting "assert the suffix loop exists in exactly one place" structural test; the single-definition property is delivered by E-03's delegation, not by a census.
- `runner_shared` KEEPS FIRST-PARTY IMPORTS FUNCTION-LOCAL, and the RULE STILL HOLDS even though the test that enforced it is gone (F-13). Measured at review, the module's module-level first-party imports are exactly `runner_profiles` and `render_stream`, matching the documented allowance "because an import added here changes the import graph for BOTH host drivers". The citation this plan originally gave (`tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`) was DELETED by `19313eed`, the same trim commit F-3 names, so nothing mechanically enforces it now. `mint_run_dir` (E-01) needs only `state_root` and `new_run_id` from its own module plus stdlib, so it adds no import at all; do not reach for one, and note that the suite will NOT catch you if you do.
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
| F-10 | THE PACKAGE CARRIES TWO INDEPENDENT RUN-ID TIMESTAMP PARSERS AND NEITHER IS DISTURBED BY THE SUFFIX, which is what makes this change safe for the viewer. `run_viewer` recovers a start time with `re.search(r"(\d{8})T(\d{6})", run.run_id)`, which matches the same groups in a suffixed id. `workflow_artifacts_prune._parse_run_date` reads the FIRST 8 characters, which for any `run-`-prefixed id is `"run-2026"` and is not a date, so it returns None for a plain id and equally for a suffixed one - pre-existing behavior, unchanged, and not this plan's to fix. | Both parsers exercised against plain and suffixed ids: the viewer regex returns `('20260929','013453')` for both; `_parse_run_date("run-20260929T013453Z-1234")` -> `None`, identical for the suffixed form. Re-verified at review, both rows reproduce. |
| F-11 | REVIEW FINDING (new, HIGH): E-01's instruction to "let the `FileExistsError` ... surface as the existing refusal" CONTRADICTS E-02's "PRESERVE THAT REFUSAL MESSAGE VERBATIM", and its literal reading is wrong three ways, so the two items had to be made unambiguous. | Measured both readings against a pre-taken path. Propagating: `FileExistsError: [Errno 17] File exists: '/tmp/.../run-20260929T013453Z-1234'` (different class, different text, and it LEAKS AN ABSOLUTE PATH into a user-facing error). Translating: `DriverError: Run already exists: run-20260929T013453Z-1234`, `matches the shipped user-visible string: True`. Third count: `DriverError` is the catchable class both hosts handle, and `agy_runipd`'s own comments record that a non-`DriverError` "raised here could NOT be caught by `except DriverError`", so a bare `FileExistsError` escapes the handler meant to render this refusal. E-01 and E-02 corrected; V-01/V-02 now demand the exact string and the absence of a path. |
| F-12 | REVIEW FINDING (new, LOW): the swap from `exists()` to `mkdir(exist_ok=False)` changes the predicate in exactly ONE case, so "behaves identically" needed narrowing. It is an improvement, not a regression. | Four paths tested: existing DIR -> `exists()=True`, mkdir raises (agree); existing FILE -> `exists()=True`, mkdir raises (agree); FREE path -> `exists()=False`, mkdir creates (agree); DANGLING SYMLINK -> `exists()=False` but mkdir raises `FileExistsError`. So for a dangling symlink the shipped code proceeds and fails later inside the run, while the new code refuses cleanly up front. Recorded in E-01 and required in V-02 instead of an unqualified identity claim. |
| F-13 | REVIEW FINDING (new, LOW): a SECOND convention citation in this plan points at a file deleted by the same commit as F-3's, so the plan cites a guard that no longer runs. The convention itself is still true in the code, which is why this is LOW and the instruction stands. | The Step-0 bullet cites `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`. `ls` -> No such file; `git log --diff-filter=D --oneline -1` -> `19313eed`, the same trim commit F-3 names; `grep -rln "no_new_module_level_first_party_import" tests/` -> no matches. The PROPERTY still holds: `runner_shared`'s module-level first-party imports are exactly `runner_profiles` and `render_stream`. So E-01's "add no import" instruction remains correct but is now unenforced by any test. |
| F-14 | REVIEW FINDING (new, LOW): the plan's own suite baseline has drifted, exactly as the plan itself predicts it would, and one `CacheDecision` reason it quotes is path-dependent. | Bare `python3 -m pytest` at review: `3246 passed, 2 skipped, 3 warnings in 48.89s` against the plan's recorded `3189 passed, 2 skipped`. The plan already instructs the executor to re-derive rather than trust that digit, which is the right instruction and is now additionally justified. Separately, F-5's `no-entry` reason appears only for a TERMINAL run; a non-terminal one yields `rebuild / run-not-terminal`. Both are `rebuild`, so E-07's "assert on the DECISION, not the message" instruction already covers it, but V-07 now says so explicitly. |
| F-15 | REVIEW FINDING (new, reassuring): the PROPOSED widening was applied in memory and behaves EXACTLY as E-04/E-05 predict at both public boundaries, including preserving the one shipped refusal the suite asserts. No plan change was needed; recorded so the executor knows the design is pre-validated. | Patched both patterns to `^run-\d{8}T\d{6}Z-\d+(?:-\d+)?$` in memory and drove `privacy.project_metric_facts` and `telemetry.validate_event` over eight shapes: plain ACCEPT, `-2` ACCEPT, `-99` ACCEPT, `-good` REFUSE, `run-20260908T100000Z-good` (the shipped assertion) REFUSE, microsecond stamp REFUSE, `-1234-/etc` REFUSE, `-1234-2-3` REFUSE; all eight matched the prediction at BOTH boundaries. `telemetry_safe_context` then kept 7/7 fields for the suffixed id where it had kept 6/7 and dropped `run_id`. |

## Proposed changes (ordered, validatable)

1. `runner_shared.mint_run_dir(repo, run_id=None)`: one shared, atomic, collision-free run-directory mint returning `(run_id, run_dir)`, raising `DriverError("Run already exists: <id>")` itself for a taken explicit id (E-01).
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
- Full bare suite `python3 -m pytest` must pass, with actual output pasted. Bare per AGENTS: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. RE-DERIVE YOUR OWN BEFORE-BASELINE AND STATE THE DELTA AGAINST IT: authoring measured `3189 passed, 2 skipped` on a clean tree at HEAD `f2cbe1dd`, review re-measured `3246 passed, 2 skipped` a day later (F-14), and this tree moves by tens of tests a day, so a transcribed total is meaningless by the time this executes. That drift is the argument for the instruction, not an exception to it: re-derive rather than comparing against either figure. Any delta beyond the cases E-06/E-07 add is this plan's to explain.
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

### OQ-03: When an explicit `--run-id` is already taken, should `mint_run_dir` raise `DriverError` itself or let `FileExistsError` propagate?

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode its_direct/pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: RESOLVED AT REVIEW BY DEMONSTRATION: raise `DriverError(f"Run already exists: {run_id}")` inside `mint_run_dir`. It is recorded as a question rather than folded silently into E-01 because the two authored items disagreed with each other about it (E-01 said "let the `FileExistsError` ... surface"; E-02 said "PRESERVE THAT REFUSAL MESSAGE VERBATIM"), and the answer decides a USER-VISIBLE error contract an operator may be matching on. The propagating reading was measured and fails on three counts: the text becomes `FileExistsError: [Errno 17] File exists: '/tmp/.../run-...'` instead of `DriverError: Run already exists: run-...`; it LEAKS AN ABSOLUTE PATH into a user-facing error, which is the exact class of string the leak-sanitizer exists to keep out of shared output; and `DriverError` is the catchable class both hosts handle, with `agy_runipd`'s own comments recording that a non-`DriverError` raised in this region "could NOT be caught by `except DriverError`", so the bare OS error escapes the handler meant to render the refusal. The translating form reproduced the shipped string byte-for-byte at review. The ALTERNATIVE of raising a NEW, more specific error class (say `RunDirTaken(DriverError)`) was considered and rejected as scope this bug does not need: the shipped message is what an operator has today and preserving it exactly is the stated requirement. One consequence is accepted and recorded in F-12 rather than hidden: swapping `exists()` for `mkdir(exist_ok=False)` makes a DANGLING SYMLINK at the run path newly refused, which is an improvement (it previously failed later, deeper in the run) but is a behavior change, so V-02 must paste it. Reversible: yes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a transcript that calls `runner_shared.mint_run_dir` TWICE against a temporary runs root with `new_run_id` monkeypatched to a FIXED value, showing two distinct returned ids (`<base>` and `<base>-2`) and `is_dir()` True for both paths. Then paste a third call with an explicit `run_id` already on disk, showing the raised exception's CLASS and MESSAGE and asserting all three of: it is `DriverError` (not `FileExistsError`), the message is exactly `Run already exists: <run_id>`, and the message contains NO filesystem path (F-11: the propagating form leaks an absolute path and escapes `except DriverError`). Also paste the function source once, to show it calls `state_root` (not a hand-joined `.aw/records/runs`) and catches only `FileExistsError` internally.
  - Observed evidence: PASS. Distinct collision IDs returned, DriverError with exact message and no filesystem path raised on taken ID, state_root called, only FileExistsError caught internally. Detail:
    ```python
    >>> # 1. Two calls with monkeypatched new_run_id
    >>> id1, dir1 = rs.mint_run_dir(repo)
    >>> id2, dir2 = rs.mint_run_dir(repo)
    Call 1 id: run-20260928T120000Z-99999 is_dir: True
    Call 2 id: run-20260928T120000Z-99999-2 is_dir: True
    Distinct IDs: True
    Distinct Dirs: True

    >>> # 2. Explicit run_id already on disk
    >>> rs.mint_run_dir(repo, run_id=id1)
    Exception class: DriverError
    Exception message: Run already exists: run-20260928T120000Z-99999
    Is DriverError not FileExistsError: True
    Exact message match: True
    No filesystem path in message: True

    >>> # 3. Function source
    def mint_run_dir(
        repo: Path | str | None = None,
        run_id: str | None = None,
    ) -> tuple[str, Path]:
        root = state_root(repo)
        if run_id:
            target = root / run_id
            try:
                target.mkdir(parents=True, exist_ok=False)
                return run_id, target
            except FileExistsError:
                raise DriverError(f"Run already exists: {run_id}")

        base = new_run_id()
        for suffix in range(1, 100):
            candidate_id = base if suffix == 1 else f"{base}-{suffix}"
            candidate = root / candidate_id
            try:
                candidate.mkdir(parents=True, exist_ok=False)
                return candidate_id, candidate
            except FileExistsError:
                continue
        raise DriverError(
            f"could not mint a free run directory under {root} after 99 attempts; something is "
            f"creating run directories faster than this process can name them"
        )
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `grep -n "Run already exists" agent_workflows/runner_shared.py` showing the refusal message is still present and still the only copy, plus the rewritten call site source showing `mint_run_dir` is called at the SAME point the old path resolution was (after `enforce_orchestrator_shape_gate`, before the `("sessions", "outcomes", "prompts")` loop), per the no-durable-write-before-the-gates constraint E-02 cites. Then paste an observed run start with a duplicate explicit `--run-id` showing the unchanged refusal, and confirm the two shape gates still refuse BEFORE any directory is created (the whole point of the ordering constraint is now sharper, because `mint_run_dir` creates `run_dir` explicitly where the shipped code only created its members). STATE THE ONE PREDICATE CHANGE rather than claiming byte-identical behavior: per F-12, a DANGLING SYMLINK at the run path was previously NOT refused by `exists()` and now IS refused by `mkdir(exist_ok=False)`; paste that case and note it as an intentional improvement.
  - Observed evidence: PASS. Only one code copy of 'Run already exists' in runner_shared.py, mint_run_dir called at correct ordering site in initialize_run_core, duplicate explicit ID refused, shape gates refuse before run directory minted, dangling symlink refused cleanly. Detail:
    ```sh
    $ grep -n "Run already exists" agent_workflows/runner_shared.py
    388:    :class:`DriverError("Run already exists: <run_id>")`.
    401:            raise DriverError(f"Run already exists: {run_id}")
    ```

    Call site in `runner_shared.initialize_run_core`:
    ```python
        enforce_orchestrator_shape_gate({"queue": queue}, repo=repo)

        run_id, run_dir = mint_run_dir(repo, getattr(args, "run_id", None))
        for name in ("sessions", "outcomes", "prompts"):
            (run_dir / name).mkdir(parents=True, exist_ok=True)
    ```

    Observed duplicate explicit `--run-id` refusal through `oc_runipd.initialize_run`:
    `Duplicate explicit --run-id refusal: Run already exists: run-20260930T000000Z-55555`

    Shape gate preflight refusal before directory is created:
    `[RUN-STRUCTURE-PREFLIGHT] ... No work started, and nothing durable was created.`
    Target runs directory check: `bad_dir.exists()` is False.

    Predicate change on dangling symlink (intentional improvement per F-12):
    ```python
    dangling_path.symlink_to(runs_dir / "non-existent-target")
    # Shipped exists() returned False; new code refuses cleanly up front:
    dangling_path.exists() -> False
    mint_run_dir(repo, run_id=dangling_id) -> DriverError: Run already exists: run-20260930T000000Z-dangling
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the new `_fresh_audit_run_dir` body showing it delegates to `runner_shared.mint_run_dir`, and the rewritten docstring, confirming it no longer claims the collision "is reported as a finding with its own backlog carrier instead" and that it still records the original measurement. Paste a transcript calling `_fresh_audit_run_dir` twice against a temporary repo, showing two distinct extant directories, so the delegation is proven to preserve spec `i4gpto` R-7 behaviorally and not just structurally.
  - Observed evidence: PASS. _fresh_audit_run_dir delegates to runner_shared.mint_run_dir, rewritten docstring preserves measurement and drops stale local-fix rationale, two distinct extant directories returned across two calls. Detail:
    ```python
    def _fresh_audit_run_dir(repo: Path) -> tuple[str, Path]:
        """A run directory that does NOT already exist, returned as ``(run_id, path)``.

        reverify-01 (`mp289j`) E-03, runidcollide (`6mdtnu`) E-03. THIS SEAM EXISTS BECAUSE
        `new_run_id` ALONE IS NOT ENOUGH, which was measured while writing this verb's own tests: the id
        is `run-<UTC seconds>-<pid>`, so two invocations from ONE shell inside the SAME second produce the
        IDENTICAL id (`{new_run_id(), new_run_id()}` had length 1). A second opinion cannot erase the
        first, and two verdicts sharing a directory would overwrite each other.

        THE GUARANTEE IS STRUCTURAL rather than probabilistic: the base id is suffixed `-2`, `-3` ...
        until the path is free, using `mkdir` itself via `exist_ok=False` as the atomic reservation test.
        Lifted into :func:`runner_shared.mint_run_dir` so every runner and queued execution inherits it;
        this wrapper delegates to the shared helper while preserving the named seam spec `i4gpto` R-7
        requires.
        """
        return runner_shared.mint_run_dir(repo)
    ```

    Transcript calling `_fresh_audit_run_dir` twice in temporary repo:
    `Call 1: run-20260928T120000Z-99999 exists: True`
    `Call 2: run-20260928T120000Z-99999-2 exists: True`
    `Distinct IDs: True`
    `Distinct Dirs: True`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste THREE measurements through the public entry point `run_analytics_privacy.project_metric_facts`: a suffixed id ACCEPTED (returned unchanged), a plain id still ACCEPTED, and `run-20260908T100000Z-good` still REFUSED with `PrivacyRefusal`. The third is required because `tests/test_run_analytics.py` asserts that exact refusal, so it is the shipped assertion E-04 must not break. Paste the updated comment beside the pattern showing it now names the collision suffix.
  - Observed evidence: PASS. project_metric_facts accepts suffixed ID, accepts plain ID, and preserves PrivacyRefusal on malformed suffix. Detail:
    ```python
    >>> rap.project_metric_facts({"run_id": "run-20260929T013453Z-1234-2"})
    {'run_id': 'run-20260929T013453Z-1234-2'}
    >>> rap.project_metric_facts({"run_id": "run-20260929T013453Z-1234"})
    {'run_id': 'run-20260929T013453Z-1234'}
    >>> rap.project_metric_facts({"run_id": "run-20260908T100000Z-good"})
    PrivacyRefusal: privacy refusal: key 'run_id' must be a driver run id or a pseudonym
    ```

    Updated comment and pattern in `agent_workflows/run_analytics_privacy.py`:
    ```python
    #: A run id as the drivers mint it: ``run-<UTC stamp>-<pid>``, plus the optional trailing
    #: numeric ``-N`` collision suffix that :func:`runner_shared.mint_run_dir` appends on collision.
    _RUN_ID_RE = re.compile(r"^run-\d{8}T\d{6}Z-\d+(?:-\d+)?$")
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste a full `run_analytics_telemetry.validate_event` call (not the private scalar helper) on an event carrying a suffixed `run_id`, showing it validates, and the same for a malformed trailing component showing it still refuses. Then paste `runner_shared.telemetry_safe_context` called with the seven-field correlation context for BOTH a plain and a suffixed id, showing `run_id` is now KEPT in both; pre-fix the suffixed case kept six of seven and dropped `run_id` (F-6), so this before/after pair is the proof that the silent-drop path is closed.
  - Observed evidence: PASS. validate_event accepts suffixed ID and refuses malformed suffix; telemetry_safe_context retains all 7 fields including run_id for both plain and suffixed IDs. Detail:
    ```python
    >>> rat.validate_event(event_suffixed)["run_id"]
    'run-20260929T013453Z-1234-2'
    >>> rat.validate_event(event_bad)
    SchemaRefusal: telemetry schema refusal: 'run_id' does not match this identifier's required shape (^run-\d{8}T\d{6}Z-\d+(?:-\d+)?$); a value that is merely 'a short label' is REFUSED here
    ```

    telemetry_safe_context retention:
    Plain kept count: 7 has run_id: True
    Suffixed kept count: 7 has run_id: True value: run-20260929T013453Z-1234-2
    (Pre-fix, suffixed kept 6 of 7 and dropped run_id; now 7 of 7 preserved).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the PRE-fix run of `python3 -m pytest tests/test_run_id_collision.py` and the POST-fix run showing `N passed`. State explicitly that the mint cases fail pre-fix only with `AttributeError` (a weak red, since the symbol does not exist) so the record is honest about what that red proves; V-07 carries the strong red. Also paste `git status --short` empty, proving no tracked file was mutated to stage a comparison.
  - Observed evidence: PASS. Pre-fix run 7 failed (weak red on mint, strong red on analytics), post-fix run 7 passed; clean git status before staging. Detail:
    PRE-fix run (unmodified code, weak red on mint cases due to missing `mint_run_dir` symbol, strong red on analytics):
    ```
    FAILED tests/test_run_id_collision.py::RunIdCollisionTests::test_two_mint_calls_on_collision_return_distinct_ids_and_extant_dirs - AttributeError: module 'agent_workflows.runner_shared' has no attribute 'mint_run_dir'
    FAILED tests/test_run_id_collision.py::RunIdCollisionTests::test_first_automatic_id_is_unsuffixed_when_path_is_free - AttributeError: module 'agent_workflows.runner_shared' has no attribute 'mint_run_dir'
    FAILED tests/test_run_id_collision.py::RunIdCollisionTests::test_caller_supplied_run_id_is_returned_verbatim_not_suffixed - AttributeError: module 'agent_workflows.runner_shared' has no attribute 'mint_run_dir'
    FAILED tests/test_run_id_collision.py::RunIdCollisionTests::test_caller_supplied_run_id_whose_directory_already_exists_raises - AttributeError: module 'agent_workflows.runner_shared' has no attribute 'mint_run_dir'
    FAILED tests/test_run_id_collision.py::RunIdCollisionTests::test_analytics_validators_accept_suffixed_id_and_refuse_malformed - PrivacyRefusal: privacy refusal: key 'run_id' must be a driver run id or a pseudonym
    FAILED tests/test_run_id_collision.py::RunIdCollisionTests::test_telemetry_safe_context_preserves_suffixed_run_id - AssertionError: 'run_id' not found in {'execution_id': 'exec-1', ...}
    FAILED tests/test_run_id_collision.py::RunIdCollisionTests::test_analytics_cache_update_sweep_admits_suffixed_run_end_to_end - AssertionError: 'skip' != 'rebuild'
    7 failed in 4.73s
    ```

    POST-fix run:
    ```
    7 passed in 4.45s
    ```

    No tracked file mutated prior to staging: `git status --short` showed only untracked `?? tests/test_run_id_collision.py`.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: THREE pasted artifacts. (1) The STRONG PRE-FIX RED: E-07's analytics cases run against the UNMODIFIED `run_analytics_*` modules, showing the suffixed run decided `skip` / `build-refused` and the telemetry `run_id` dropped - this is the measurement of shipped behavior that gives the fix its meaning, and it must be captured before E-04/E-05 are applied (in memory, per the validation section). (2) The POST-fix two-run `update_cache` sweep showing BOTH decisions `rebuild` and no decision carrying `reason == "build-refused"`. ASSERT ON `verdict`, NOT ON `reason`: per F-14 the passing `reason` is `no-entry` for a TERMINAL run and `run-not-terminal` for a live one, so pinning `no-entry` would make the test depend on how the fixture builds its runs rather than on the behavior under test. (3) YOUR OWN re-derived clean-tree bare baseline, then the post-change bare `python3 -m pytest`, with the delta stated against your baseline and accounted for by the cases E-06/E-07 add; do not state a delta against the `3189 passed, 2 skipped` this plan records, which review re-measured at `3246 passed, 2 skipped` (F-14), nor against that figure either. Additionally paste the targeted neighbour run over `tests/test_run_analytics.py tests/test_runner_shared.py tests/test_run_viewer.py tests/test_commit_run_trailers_env.py`, since those four are the modules that already touch the run-id grammar or the changed module; review measured them green at `194 passed`, so a failure there is this plan's to explain.
  - Observed evidence: PASS. Strong pre-fix red reproduced; update_cache rebuilds both runs with no build-refused; post-change bare pytest 3285 passed, 2 skipped (+7 delta from 3278 baseline); neighbour suite 194 passed. Detail:
    1. Strong pre-fix red:
    ```
    run-20260901T000000Z-1111111 verdict: rebuild reason: no-entry
    run-20260901T000000Z-1111111-2 verdict: skip reason: build-refused
    F-6 safe keys count: 6 has run_id: False
    ```

    2. Post-fix two-run update_cache sweep:
    ```
    run-20260901T000000Z-1111111 verdict: rebuild reason: no-entry
    run-20260901T000000Z-1111111-2 verdict: rebuild reason: no-entry
    ```
    Both verdicts are rebuild; neither has reason == "build-refused".

    3. Re-derived clean-tree bare baseline:
    `3278 passed, 2 skipped, 3 warnings in 94.01s (0:01:34)`

    Post-change bare pytest:
    `3285 passed, 2 skipped, 3 warnings in 84.16s (0:01:24)`
    Delta: exactly +7 passed, matching the 7 tests added in `tests/test_run_id_collision.py`.

    Targeted neighbour suite:
    `194 passed in 24.64s`
  - Result: pass

## Approval and execution gate

This plan is `to-review` and has NOT been reviewed or approved; it must not execute until a human approves it. Per the execution contract: commit only the files changed, limited to the declared `Scope-Paths`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Paste actual runner output for every test claim; do not assert a passing suite that was not run.

Post-gate lifecycle: after every `E-*` is performed and every `V-*` carries real observed evidence, run `aw ipd lint --phase pre-transition` and confirm it reports conforming, then reach `.aw/records/plans/executed/` via `aw ipd finalize`. THAT TRANSITION IS UNCONDITIONALLY OWED BUT ITS OWNER IS CONDITIONAL: under `aw oc run` / `aw agy run` the RUNNER owns it, so do not invoke `aw ipd finalize` yourself in a runner-driven execution; a HAND execution invokes it. Never hand-roll a `git mv` to `executed/`. Do not mark it executed while any `V-*` result is `pending`. The backlog item `2jtsup` carries `- Blocks-Release: next`, which this plan inherits; the item reaches `graduated` on handoff and may only close `done` once this plan is genuinely executed, which is what preserves the release gate.

BEFORE IMPLEMENTING, re-run the F-1, F-5 and F-6 reproductions: if the mint no longer collides, or a suffixed run is no longer refused by the analytics boundary, or its telemetry `run_id` is no longer dropped, STOP and report rather than building a fix for a defect that has moved. All three reproduced at review on 2026-09-29 (`len({new_run_id(), new_run_id(), new_run_id()}) == 1`; the suffixed run decided `skip` / `build-refused` with `privacy refusal: key 'run_id' must be a driver run id or a pseudonym`; `telemetry_safe_context` kept 6 of 7 fields and dropped `run_id`), so the defects had NOT moved as of then.

READ F-11 BEFORE WRITING `mint_run_dir`. E-01 and E-02 as authored contradicted each other about the explicit-duplicate refusal, and the literal reading of E-01 changes a user-visible error, leaks an absolute path, and escapes the `except DriverError` handler that renders it. OQ-03 records the resolution and E-01 now states it directly.

- Size assessment: standard
- Cohesion rationale: not required
