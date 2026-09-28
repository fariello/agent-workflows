# IPD: Pin the shared reaper's keyword contract with a Protocol so bound_expiry_reaper's injected reap type matches its own call

- Date: 2026-09-28
- Kind: child
- Concern: `lane_containment.bound_expiry_reaper` declares its injectable reaper as `reap: Callable[[Any, Path], Any] | None`, which means TWO POSITIONAL parameters, then calls it as `reaper(process, run_dir=run_dir)`. The declared type therefore contradicts the only call the function makes, and a type checker errors on that call line. It is runtime-harmless only by accident: the default `runner_shutdown.clean_shutdown` happens to name `run_dir` as a parameter, so the keyword binds. Nothing in the suite asserts that the annotation and the call agree, so the contradiction is invisible to every gate this repository actually runs.
- Scope: Replace the contradicted `Callable` with a `Protocol` whose `__call__` states the real contract (`(process, /, *, run_dir)`), and add a runtime test that binds the annotation against the call the product makes, so the class of defect is caught by the bare suite rather than only by a type checker nobody here runs. Change no runtime behavior: the default reaper, the call, and the expiry record stay byte-identical.
- Scope-Paths: agent_workflows/lane_containment.py, tests/test_reap_contract.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: jt01do
- Set: jt01do
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: 2o9osz
- Approval: 2026-09-28, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-28 approved (aw set): status set to approved

- 2026-09-28 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201..PR-205. This is an unusually well-evidenced plan: EVERY measured claim in Findings was independently re-measured at review and reproduced EXACTLY, including pyright's `errorCount` 1 -> 0 and its zero-based line 1244, the 627/383/5/69/1 histogram of F-12, the `missing a required argument: '__p1'` guard message, F-09's wrong-reason message `got an unexpected keyword argument 'run_dir'`, and both F-05 rejection messages verbatim. Review added a THIRD load-bearing conversion rule E-01 did not state and that I hit while prototyping its guard: the Protocol branch must be selected on `_is_protocol`, because EVERY class has a `__call__` attribute via its metaclass, so a `hasattr(member, "__call__")` dispatch silently routes a Protocol into the `Callable` branch and the guard then reports the wrong reason - the exact failure mode F-09 exists to prevent, in a second place (PR-201). Also corrected: the targeted regression set omitted `tests/test_prior_attempt_projection.py` while claiming to name every file importing `lane_containment` (PR-202), and V-01's second deliberate-failure demonstration mutates a file outside `- Scope-Paths:` in a shared checkout without saying how to restore it safely (PR-203). Record: `.aw/records/reviews/20260928-jt01do-01-2o9osz-pin-the-shared-reaper-s-keyword-contract-with-a-proto.review.md`.
- 2026-09-28 draft (opencode): created.
- 2026-09-28 to-review (opencode): authored from backlog item `jt01do`. Every claim in Findings was re-measured at this HEAD rather than carried from the item: the item cites `lane_containment.py:1208` and the error is now at the CALL line (F-01), the item's suggested `Callable[..., Any]` was tested and rejected on evidence (OQ-01), and the item's named test file `tests/test_turn_bounds.py` no longer exists (F-06), which changes where the guard must go.

## Goal

Make the declared type of `bound_expiry_reaper`'s `reap` parameter agree with the one call the function makes, by stating the contract the shared reaper actually has (a process positionally, `run_dir` by keyword) instead of a two-positional shape it does not have. Leave behind a test that FAILS on the contradiction, so the next author who widens or narrows this seam learns it from the bare suite. No runtime behavior changes: `runner_shutdown.clean_shutdown` remains the one reaper, it is still called exactly as it is called today, and the `turn_bound_expiry` record is unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the suite able to see the defect

- [x] E-01 Add `tests/test_reap_contract.py` with a RUNTIME guard that reproduces the type checker's finding without needing a type checker. It must resolve `typing.get_type_hints(lane_containment.bound_expiry_reaper)["reap"]`, strip the `| None`, convert the remaining member into an `inspect.Signature`, and assert that signature BINDS the call the product actually makes: `(process_sentinel, run_dir=Path(...))`. THREE conversion rules are load-bearing and all three were measured, so write them deliberately rather than discovering them.
  (a) DISPATCH ON `getattr(member, "_is_protocol", False)`, NOT on `hasattr(member, "__call__")`. This is the rule review added after hitting it while prototyping this very guard, and it is the most dangerous of the three because it fails SILENTLY IN THE GREEN DIRECTION on the post-fix tree: every class has a `__call__` attribute via its metaclass, so `hasattr(member, "__call__")` is True for the Protocol too, and a `hasattr`-first dispatch routes the Protocol into the `Callable` branch, where `typing.get_args` returns `()` and the guard synthesizes a two-positional signature from stale assumptions and reports `missing a required argument: '__p1'` AFTER E-02 has correctly fixed the code. Measured: with `hasattr` dispatch the guard reported MISMATCH on the PATCHED tree; with `_is_protocol` dispatch it reported `OK -> (process: 'Any', /, *, run_dir: 'Path') -> 'Any' accepts the product's call`. An executor who writes the `hasattr` form will conclude the Protocol did not work and may revert a correct fix.
  (b) FLATTEN THE `Callable` PARAMETER LIST. For a `collections.abc.Callable[[A, B], R]`, `typing.get_args` returns `([A, B], R)`, so the parameter list arrives as ONE LIST element that must be flattened before counting; unflattened, a two-arg `Callable` is misread as one-arg and the guard reports `got an unexpected keyword argument 'run_dir'` instead of the missing-positional reason (measured both ways).
  (c) BUILD THOSE PARAMETERS `POSITIONAL_ONLY`, because a bare `Callable[[...], R]` genuinely carries no parameter names and pretending it does would let the keyword bind and the guard pass.
  For a `Protocol`, inspect `member.__call__` and drop `self` (measured: the raw signature is `(self, process: 'Any', /, *, run_dir: 'Path') -> 'Any'`). ASSERT ALSO the other half of the contract, which is what makes this a guard and not a tautology: that `inspect.signature(runner_shutdown.clean_shutdown)` binds the same call, so the test fails if a future edit renames `run_dir` or makes it positional-only in the SHARED REAPER. MEASURED at this HEAD: the first assertion FAILS with `missing a required argument: '__p1'` and the second PASSES, so this test is red before E-02 and green after.
  - Depends on: none
  - Expected outcome: A new `tests/test_reap_contract.py` that FAILS at this HEAD naming the declared type and the call it refuses, PASSES on the post-E-02 tree (which rule (a) is what makes true), and would fail again for any future `reap` annotation whose shape the call site contradicts, or any change to `clean_shutdown`'s `run_dir` parameter.
  - Execution state: performed

### Task group 2: state the real contract

- [x] E-02 In `agent_workflows/lane_containment.py`, replace `bound_expiry_reaper`'s `reap: Callable[[Any, Path], Any] | None = None` with a module-level `Protocol` whose `__call__` is `(self, process: Any, /, *, run_dir: Path) -> Any`, and add `Protocol` to the existing `from typing import Any, NamedTuple` import. THE POSITIONAL-ONLY MARKER ON `process` IS DELIBERATE AND MEASURED: without it, pyright rejects a test double whose first parameter is named anything other than `process` with `Parameter name mismatch`, which would make the annotation hostile to the injection seam whose ONLY purpose (per the function's own docstring) is letting a test observe the call. With it, a double may name its first parameter freely while `run_dir` stays pinned by keyword, which is the real contract. Keep the `Callable` import, which eight other annotations in this module still use. Change no executable line: the `reaper = reap if reap is not None else runner_shutdown.clean_shutdown` default, the `reaper(process, run_dir=run_dir)` call, and the `_expire` body are untouched, and the Protocol is typing-only so it adds no runtime work to a turn.
  - Depends on: E-01
  - Expected outcome: `npx pyright agent_workflows/lane_containment.py` reports 0 errors where it reported exactly 1; the E-01 guard passes; `python3 -m pytest` is green with no change to any expiry record or reaper call.
  - Execution state: performed

- [x] E-03 Record in the Protocol's own docstring WHY it exists, in the two terms a future author needs and cannot recover from the type alone: that `run_dir` is passed BY KEYWORD because the shared reaper `runner_shutdown.clean_shutdown` takes four optional leading parameters (`process, lock, run_dir, repo`) so a positional call would bind `run_dir` into `lock`; and that the first parameter is positional-only so an injected test double may name it freely, per the injection seam the function's existing docstring already describes as existing ONLY for tests. Cite `tests/test_reap_contract.py` as the enforcing guard. Do NOT restate spec `c4gd2h` R5's one-reaper rule, which the function docstring already carries; add nothing about behavior, since none changes.
  - Depends on: E-02
  - Expected outcome: The Protocol carries a docstring naming the keyword reason (the four-optional-leading-parameter hazard), the positional-only reason (the test-double seam), and the guard file; no other prose in the module is edited.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This bites immediately here: backlog item `jt01do` cites `lane_containment.py:1208`, and at this HEAD line 1208 is the function's RETURN annotation while the reported error is on the call at 1245. This plan cites `lane_containment.bound_expiry_reaper` and `runner_shutdown.clean_shutdown` by name throughout.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow'`; `python3 -m pytest` with no added flags is the contract, and a second `-q` would suppress the `N passed` line this plan's validation requires. Use `-o addopts=""` when per-test counts are genuinely needed.
- THIS REPOSITORY HAS NO TYPE-CHECK GATE, and that fact shapes the whole plan. There is no `pyrightconfig.json`, no `[tool.mypy]` or `[tool.pyright]` section in `pyproject.toml`, no type checker installed in the environment, and the three CI workflows are `tests.yml`, `local-leaks.yml` and `secret-scan.yml`. So a fix verified only by running pyright ad hoc is verified by a tool no later gate runs, which is why E-01 exists and why it is a RUNTIME test.
- A SOURCE-READING TEST IS THE WRONG SHAPE HERE, by explicit repository precedent. Commit `80db6750` deleted 366 tests "that pinned code structure instead of behaviour" because they "read production SOURCE - parsing it with ast, reading `__file__`, or substring-searching it" and "None of them exercises the code". A guard that grepped `lane_containment.py` for the string `Callable[[Any, Path], Any]` would be exactly that class. E-01's guard instead resolves the annotation object and binds a real `inspect.Signature`, so it exercises the contract.
- PYTHON 3.9 IS THE FLOOR (`requires-python = ">=3.9"`). `typing.Protocol` is 3.8+ and the positional-only `/` marker is 3.8+, so both are available; verified by parsing the patched module with `ast.parse(..., feature_version=(3, 9))`.
- `lane_containment` IS THE SANCTIONED HOME FOR HOST-NEUTRAL CODE, so the Protocol belongs there rather than in either driver or in `runner_shutdown`. Plan `lhmrhx` states it: "THE SHARED HOME IS NAMED, and is `agent_workflows/lane_containment.py`... Do NOT improvise a home by putting them in one driver and importing from the other: that makes one host the de-facto shared library, which is the opposite of host-neutral, and spec R2.6 forbids it."
- THE MODULE DEFERS ITS `runner_shutdown` IMPORT INTO THE FUNCTION BODY (`from agent_workflows import runner_shutdown` inside `bound_expiry_reaper`), which is why the Protocol must spell the contract structurally rather than reference `clean_shutdown`'s type: hoisting that import to module scope to get a type would change import-time behavior, which this plan does not authorize.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE DEFECT IS LIVE AND IS EXACTLY ONE ERROR, at the CALL rather than at the annotation the item cites. `npx pyright@1.1.403 --outputjson agent_workflows/lane_containment.py` returns `{'filesAnalyzed': 1, 'errorCount': 1}` with a single `reportCallIssue`, `"Expected 1 more positional argument"`, at zero-based line 1244 characters 41-48 (the `run_dir` keyword of `reaper(process, run_dir=run_dir)`), not at the `reap` annotation. So an executor navigating to the item's `:1208` lands on the function's return annotation instead. | `npx --yes pyright@1.1.403 --outputjson agent_workflows/lane_containment.py` at HEAD `40c6dcc3`, full diagnostic JSON. |
| F-02 | THE ITEM'S RUNTIME-HARMLESSNESS CLAIM IS CORRECT, and measurably so. `inspect.signature(runner_shutdown.clean_shutdown)` is `(process=None, lock=None, run_dir=None, repo=None, *, extra_processes=())`, and `sig.bind(object(), run_dir=Path("."))` succeeds. So the keyword binds at runtime; only the declared type disagrees. This is what makes the item `chore` rather than `bug`: no user-perceptible impact. | `inspect.signature` + `sig.bind` probe on the real `clean_shutdown`. |
| F-03 | THE KEYWORD IS NOT INCIDENTAL, it is REQUIRED for correctness, which raises the stakes of getting the annotation right. `clean_shutdown`'s first four parameters are `process, lock, run_dir, repo`, all optional. A caller "simplifying" to the two-positional shape the current annotation DESCRIBES would pass `run_dir` as `lock`, so the run directory would be treated as a lock handle and the real `run_dir` would stay `None`. The annotation therefore describes a call that would silently misbind. | Read of `runner_shutdown.clean_shutdown`'s signature and its `run_dir`-consuming invariants. |
| F-04 | THE PROPOSED PROTOCOL FIXES IT COMPLETELY. With `_ReapCallable(Protocol)` declaring `__call__(self, process: Any, /, *, run_dir: Path) -> Any` and `reap: _ReapCallable \| None`, pyright reports `{'errorCount': 0}` on the file, down from 1, with no new diagnostic introduced anywhere. | Patch applied in a scratch working tree, `npx pyright` re-run: `errorCount: 0`; patch then reverted with `git checkout --`. |
| F-05 | THE POSITIONAL-ONLY MARKER IS LOAD-BEARING, measured rather than assumed. A probe file declared the same Protocol WITHOUT `/` and assigned a double `def differently_named(proc, *, run_dir)`: pyright rejected it with `Parameter name mismatch: "process" versus "proc"`. With `/` added, the same double is accepted, a two-positional reaper is accepted, and the two shapes that MUST be refused still are: `def no_run_dir(process)` fails with `Missing keyword parameter "run_dir"` and `def extra_required(process, *, run_dir, token)` fails with `Extra parameter "token"`. So the marker widens exactly the freedom the test seam needs and nothing more. | Two scratch probe files type-checked in sequence, each pyright message recorded; both deleted. |
| F-06 | THE ITEM'S IMPLIED TEST HOME NO LONGER EXISTS, so the guard needs a new file. `tests/test_turn_bounds.py` was the Scope-Paths home for this code under plan `lhmrhx`, and it was DELETED by commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"). `ls tests/test_turn_bounds.py` and `ls tests/test_lane_permission_posture.py` both report no such file. | `git log --diff-filter=D --name-only -- tests/test_turn_bounds.py` naming `19313eed`; two `ls` probes. |
| F-07 | THE ENTIRE BOUND-EXPIRY SURFACE IS NOW UNTESTED, which is why a test is warranted at all and not merely a courtesy. Searching `tests/` and `tools/` for `bound_expiry_reaper`, `bound_expiry_record`, `driver_bound_for_host`, `BOUND_MAX_TURN`, `BOUND_PERMISSION`, `MAX_TURN_TIMEOUT` and `TurnBoundWatch` returns ZERO hits in either tree. The only test-tree references to these concepts are in `tests/test_backlog_duplicate_guard.py`, which quotes the deleted test file's NAME as corpus text and exercises none of this code. | Seven searches over `tests/` and `tools/`, all empty; read of the `test_backlog_duplicate_guard.py` fixtures that mention the name. |
| F-08 | A RUNTIME GUARD CAN REPRODUCE THE TYPE CHECKER'S EXACT FINDING, so the fix is verifiable by the gate this repo actually runs. A prototype resolving `get_type_hints(...)["reap"]`, flattening the `Callable` args, and binding `(sentinel, run_dir=Path("."))` printed `MISMATCH -> (__p0, __p1, /) REFUSES the product's call: missing a required argument: '__p1'` against the shipped annotation, and `OK -> (process, /, *, run_dir) accepts the product's call` against the patched one. Same defect, same reason, no pyright. | Prototype guard run twice, once per tree state; both outputs recorded; prototype deleted. |
| F-09 | THE FLATTENING RULE IS A REAL TRAP, not defensive prose. `typing.get_args(Callable[[Any, Path], Any])` returns `([typing.Any, <class 'pathlib.Path'>], typing.Any)`: the parameters arrive as a single LIST element. The prototype's first version omitted the flatten and reported the wrong reason (`got an unexpected keyword argument 'run_dir'`, i.e. a one-parameter signature) while still failing. A guard that fails for the wrong reason is how a later author concludes the guard is broken rather than the code. | `typing.get_args` probe; both prototype outputs, before and after the flatten fix. |
| F-09a | **ADDED AT REVIEW: THE PROTOCOL-BRANCH DISPATCH IS A SECOND TRAP OF THE SAME CLASS, AND IT IS WORSE, because it fails in the GREEN-LOOKING direction on the FIXED tree.** `hasattr(member, "__call__")` is True for a `Protocol` CLASS as well as for a `Callable` alias, because every class inherits `__call__` from its metaclass, so a guard that tests `hasattr` before `_is_protocol` routes the post-E-02 Protocol into the `Callable` branch. There `typing.get_args(_ReapCallable)` returns `()`, the synthesized signature is wrong, and the guard reports `missing a required argument: '__p1'` against code that is now CORRECT. Measured directly: identical guard bodies differing only in that dispatch test gave MISMATCH (hasattr-first) versus `OK -> (process: 'Any', /, *, run_dir: 'Path') -> 'Any' accepts the product's call` (`_is_protocol`-first) on the SAME patched tree. The correct raw Protocol signature is `(self, process: 'Any', /, *, run_dir: 'Path') -> 'Any'`, so dropping `self` is also required. The consequence for the executor is the reason this is a Finding and not a footnote: a red guard on a correct fix invites reverting the fix. | Two guard prototypes run against the same patched tree, differing only in the dispatch test, both outputs recorded; `getattr(_ReapCallable, "_is_protocol")` -> True; `typing.get_args(_ReapCallable)` -> `()`; `inspect.signature(_ReapCallable.__call__)` printed. |
| F-10 | THE FULL SUITE IS UNAFFECTED BY THE FIX. With the patch applied, bare `python3 -m pytest` reported `2935 passed, 2 skipped, 3 warnings in 45.03s`, with `201 tests deselected by -m/-k`. Nothing in the suite depends on the old annotation, consistent with F-07. | Bare `python3 -m pytest` on the patched tree, summary line recorded; tree then reverted. |
| F-11 | THE PATCH IS PYTHON 3.9-PARSEABLE, which matters because `requires-python` is `>=3.9` while this environment is 3.14.6. `ast.parse(source, feature_version=(3, 9))` on the patched module succeeded, and `from agent_workflows import lane_containment` then reported the annotation as `_ReapCallable \| None`. | `ast.parse` with `feature_version=(3, 9)`; import probe printing `bound_expiry_reaper.__annotations__["reap"]`. |
| F-12 | THE REPOSITORY IS NOT PYRIGHT-CLEAN OVERALL, so this plan must not be read as starting a type-check gate. A full run over `agent_workflows`, `tests` and `tools` reports `errorCount: 627` across 383 files, of which only 5 are `reportCallIssue` and exactly one is this defect; `lane_containment.py` contributes exactly 1 of the 627. | `npx pyright --outputjson agent_workflows tests tools`, summary plus per-rule and per-file histograms. |
| F-13 | ONE OTHER `reportCallIssue` IS A FALSE POSITIVE AND MUST NOT BE SWEPT IN. `platform_lock.py`'s `No parameter named "preserve_lock_file"` is raised on a line guarded by `_filelock_can_preserve()`, which exists precisely because filelock 4.0+ accepts that argument and older versions do not; `tests/test_platform_lock_preserve.py` asserts the call. So it is correct code the checker cannot see through, unlike this defect, which is a genuine self-contradiction. | Read of `platform_lock._new_lock` and `_filelock_can_preserve`; read of `tests/test_platform_lock_preserve.py`. |
| F-14 | THE INJECTION SEAM IS DOCUMENTED AS TEST-ONLY, which is the evidence that decides the positional-only question. `bound_expiry_reaper`'s docstring states the reaper "is injectable ONLY so a test can observe the call without spawning a real process; the default is the shared routine, and a caller that passes something else is introducing the second reaper the spec forbids." An annotation that rejects a differently-named double (F-05) would therefore obstruct the seam's only sanctioned use. | Read of `lane_containment.bound_expiry_reaper`'s docstring. |

## Proposed changes (ordered, validatable)

1. Add `tests/test_reap_contract.py` containing a runtime guard that binds `bound_expiry_reaper`'s declared `reap` type against the call the function makes, and separately binds `clean_shutdown`'s real signature against the same call (E-01). It is RED at this HEAD.
2. Replace the `Callable[[Any, Path], Any]` annotation with a module-level `Protocol` declaring `(process, /, *, run_dir)`, importing `Protocol` from `typing` (E-02). The guard turns green; pyright goes 1 error to 0; no executable line changes.
3. Document in the Protocol's docstring why `run_dir` is keyword-passed and why `process` is positional-only, citing the guard (E-03).

A NOTE ON ORDERING, since it is not the obvious one: E-01 lands a test that is RED, and E-02 turns it green. That is deliberate (a guard that was never red proves nothing) but it means the tree is transiently red between the two, so the executor must not treat a failing suite after E-01 as a defect. The bare suite is only expected green from E-02 onward.

## Deferred / out of scope (with reason)

- INSTALLING A TYPE-CHECK GATE (a `pyrightconfig.json`, a `[tool.pyright]` section, a `make typecheck`, or a CI step) is out of scope. It is the obvious generalization and it is a genuinely separate decision: the tree carries 627 pyright errors (F-12), so a gate would have to ship with a baseline or a large remediation, and at least one existing error is a false positive the checker cannot see through (F-13). Deciding whether this repository adopts static typing as a gate is a maintainer call about scope and risk appetite, not a `low`-priority `chore`. E-01's runtime guard is the part that can be delivered now without that decision.
  - Carrier-Declined: There is no outstanding DEFECT to carry, so naming a carrier would file an obligation the repository has not agreed to take on. This row records a scope boundary plus an explicit recommendation for the maintainer, and the concrete protection it would have bought for THIS seam is delivered inside this plan by E-01, which needs no type checker to run. If the maintainer wants the gate, that is new work to be filed as its own item with its own priority, not an obligation this plan may create on their behalf.
- FIXING THE OTHER 626 PYRIGHT ERRORS is out of scope and deliberately untouched. They are concentrated in `runner_shared.py` (69) and several test modules (F-12), span five rule families dominated by `reportArgumentType` and `reportOptionalMemberAccess`, and each needs its own judgement about whether the checker or the code is wrong. Sweeping them into a `low` `chore` would produce an unreviewable diff across 383 files.
  - Carrier-Declined: Nothing is owed here yet, because no defect among those 626 has been triaged, measured, or shown to have user-perceptible impact; a carrier would assert that an unexamined 626-item population is agreed work. The honest state is that they are UNTRIAGED, which is what F-12 records so a later reader can start from a number rather than a hunch. Filing them would itself require the gate decision deferred in the row above.
- `platform_lock.py`'s `preserve_lock_file` DIAGNOSTIC is explicitly NOT fixed. It is correct, version-guarded code (F-13) and `tests/test_platform_lock_preserve.py` asserts the call; silencing it would mean weakening working Windows compatibility code or adding an ignore comment to satisfy a tool this repository does not run.
  - Carrier-Declined: There is no defect to carry: the code is correct, the guard is correct, and the test asserting it is correct, so the only "fix" available would be a suppression for a non-gate. Recorded here so a future reader does not mistake this plan's silence for an oversight.
- BACKFILLING BEHAVIORAL TESTS FOR THE BOUND-EXPIRY SURFACE is out of scope. F-07 measures that `bound_expiry_reaper`, `bound_expiry_record`, `driver_bound_for_host` and `TurnBoundWatch` have ZERO test-tree references, and spec `7ckptx` criterion A10 requires a demonstration that an unanswered permission request terminates within the deadline with the bound named. That coverage was delivered by plan `lhmrhx` into `tests/test_turn_bounds.py` and lost when `19313eed` trimmed the suite (F-06). Restoring it means re-deriving a spec-acceptance demonstration with real subprocesses, which dwarfs this annotation fix and must not be smuggled into it.
  - Carrier: f15tne
- CHANGING ANY RUNTIME BEHAVIOR is rejected rather than deferred. The reaper stays `runner_shutdown.clean_shutdown` (spec `c4gd2h` R5's one reaper), the call stays `reaper(process, run_dir=run_dir)`, the record-then-reap order stays (the docstring records that order as load-bearing), and the `turn_bound_expiry` record keeps its exact keys. If this plan changes an observable behavior, it has failed.
  - Carrier-Declined: This row is a PROHIBITION on this plan, not an outstanding defect, so no future work is owed and a carrier would name an obligation that does not exist. It is enforced inside this plan by V-02's byte-level diff review and by the bare suite in V-03.

## Scope check

- Over-scope: none. `agent_workflows/lane_containment.py` carries only the `typing` import addition, the new `Protocol` class with its docstring, and the one annotation change; `tests/test_reap_contract.py` is new and carries only the guard. No driver, no `runner_shutdown`, no spec, no CI config, and no `.aw/` record other than this plan changes. Notably `runner_shutdown.clean_shutdown` is NOT edited: the Protocol is written to match the reaper as it already is, not the reverse.
- Under-scope: The repository still has no type-check gate, the other 626 pyright errors remain, and the bound-expiry surface still has no BEHAVIORAL test (only the contract guard this plan adds). All three are recorded above with reasons, and the first two are the reason the third is bounded the way it is. After this plan, the one self-contradicting annotation backlog item `jt01do` reported is gone and a bare-suite test fails if it returns.

## Required tests / validation

- `python3 -m pytest` run BARE, with its `N passed` summary pasted and compared against the pre-change baseline. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `python3 -m pytest tests/test_reap_contract.py -o addopts=""` for per-test counts on the new file.
- A DELIBERATE-FAILURE DEMONSTRATION for E-01: the guard must be shown RED on the pre-E-02 tree, with the failure message naming the declared type and the bind error. A guard that was never red proves nothing.
- A SECOND DELIBERATE-FAILURE DEMONSTRATION for E-01's other half: temporarily rename `run_dir` in `runner_shutdown.clean_shutdown` (or make it positional-only), show the guard RED, and restore. This proves the guard watches the shared reaper too, not only the annotation. HOW TO DO THIS SAFELY, because `agent_workflows/runner_shutdown.py` is NOT in `- Scope-Paths:` and this is a shared checkout where another party may be editing it: do NOT edit the file on disk. Perform the mutation IN PROCESS with `unittest.mock.patch.object(runner_shutdown, "clean_shutdown", <a stub whose signature renames run_dir>)`, or by constructing the mutated `inspect.Signature` directly and binding against it. That exercises exactly the assertion under test, leaves no window in which a co-worker sees a broken shared reaper, and cannot strand a half-reverted edit if the run is interrupted. If you judge an on-disk edit unavoidable, say so explicitly in the V-01 evidence, snapshot the file first (`git diff --exit-code agent_workflows/runner_shutdown.py` before and after must both be clean), and never use `git checkout --` on a path a co-worker may have modified.
- `npx --yes pyright@1.1.403 --outputjson agent_workflows/lane_containment.py` before and after, showing `errorCount` 1 then 0. This is diagnostic evidence, not a gate (F-12); the gate is the bare suite.
- `python3 -c 'import ast; ast.parse(open("agent_workflows/lane_containment.py").read(), feature_version=(3,9))'` to hold the 3.9 floor.
- `python3 -m pytest tests/test_attempt_lane_facts.py tests/test_lane_input_manifest.py tests/test_lane_input_revision_scope.py tests/test_commit_run_trailers_env.py tests/test_driver_attestation_gate.py tests/test_finalize_sendback.py tests/test_defect_report.py tests/test_prior_attempt_projection.py -o addopts=""` as the targeted regression set: every test file that imports `lane_containment`. CORRECTED AT REVIEW: the authored list named seven files while claiming to be exhaustive; `rg -l lane_containment tests/` returns EIGHT, and `tests/test_prior_attempt_projection.py` was the omission. Re-derive the list with that command at execution time rather than trusting this one, since the population is live.
- `aw check` to confirm no new drift, and `aw ipd lint` conforming.
- `aw sanitize --agent` before commit, since this plan's evidence quotes local command output and absolute paths appear in pyright JSON.
- `git diff --cached --name-only` immediately before committing, which must list exactly the two paths in `- Scope-Paths:` and nothing another party changed.

## Spec / documentation sync

N/A with reason. No `.spec.md` is in `- Scope-Paths:` and none needs amending. Spec `c4gd2h` R5 ("The cleanup routine is ONE implementation shared by all four levels and by crash recovery") and spec `7ckptx` R4.4 (driver-side turn bounds) both govern this code, and this plan CONFORMS to both without changing either: the one reaper stays the one reaper, and the bounds' behavior is untouched. The Protocol makes R5's constraint more legible by pinning the shape a conforming reaper must have, which is a documentation effect inside the module, not a contract change. No user-facing documentation mentions `bound_expiry_reaper` or its `reap` parameter. Spec `7ckptx` criterion A10 remains UNDEMONSTRATED in the current suite, but that predates this plan (F-06, F-07) and is recorded as deferred above with a carrier rather than silently inherited.

## Open questions

### OQ-01: The backlog item suggests `Callable[..., Any]` OR a Protocol. Which, and does the choice need the maintainer?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT as the PROTOCOL, and it needs no maintainer ruling because this is a HOW question with a decisive in-repo answer, not a scope or risk-appetite question. Both candidates silence the error, so the tie is broken on what each one still guarantees. `Callable[..., Any]` erases the contract entirely: a probe confirmed it accepts ANY call shape, so it would equally accept a reaper that takes no `run_dir` at all, and F-03 measures what that costs - `clean_shutdown`'s first four parameters are `process, lock, run_dir, repo`, so a caller who believed the erased annotation and passed positionally would bind the run directory into `lock` and leave `run_dir` as `None`. That is a real misbinding, latent behind an annotation that had stopped saying anything. The Protocol instead states the contract and was measured to refuse exactly the two wrong shapes and accept the right ones (F-05). The item itself leans this way ("Callable[..., Any] replaced by a Protocol with (process, *, run_dir)"), and the one refinement measurement forced on the item's sketch is the positional-only marker: without it pyright rejects a test double whose first parameter is named `proc` with `Parameter name mismatch`, which would obstruct the very injection seam the function's docstring says exists ONLY for tests (F-14).

### OQ-02: Where does the guard live, given the test file this code used to be covered by no longer exists?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED as a NEW FILE, `tests/test_reap_contract.py`, on three measured grounds. FIRST, the historical home is gone: plan `lhmrhx` declared `tests/test_turn_bounds.py` in its Scope-Paths, and commit `19313eed` deleted it while trimming the suite from 9,136 tests; `ls` confirms neither it nor `tests/test_lane_permission_posture.py` exists (F-06). SECOND, there is no surviving `tests/test_lane_containment.py` to extend - that name appears only in a SUPERSEDED plan (`tch3bo`) that never executed - and the six `tests/test_lane_*.py` files that do exist each cover a different subject (attempt facts, import root, input manifest, revision scope, retirement, review output commit), so appending a reaper-contract test to any of them would mix concerns. THIRD, a new narrowly-named file makes the Scope-Paths fence exact, so the executor cannot incidentally edit another party's test file in a shared checkout. The guard is deliberately NOT written as a source-reading test, per commit `80db6750`'s deletion of 366 structure-pinning tests; it resolves the annotation object and binds a real `inspect.Signature` instead.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the full committed source of `tests/test_reap_contract.py`. Paste its output run on the tree BEFORE E-02's change (`python3 -m pytest tests/test_reap_contract.py -o addopts=""`), which must FAIL, and the failure message must show the declared type `collections.abc.Callable[[typing.Any, pathlib.Path], typing.Any] | None` and the bind error naming a MISSING SECOND POSITIONAL argument (expected `missing a required argument: '__p1'`). If the failure instead reports an unexpected keyword argument, the flatten of F-09 is missing and the guard is failing for the wrong reason: fix it before proceeding. QUOTE THE DISPATCH LINE of the committed guard and confirm in one sentence that it tests `getattr(member, "_is_protocol", False)` and NOT `hasattr(member, "__call__")`, per F-09a: that is the one rule whose violation makes the guard RED ON THE CORRECT POST-E-02 TREE, so a passing V-02 does not prove it and only reading the line does. Then paste the SECOND deliberate failure: mutate `clean_shutdown`'s `run_dir` IN PROCESS (per Required tests, not by editing the out-of-fence file), paste the guard RED on that mutation, and paste it back green. Confirm in one sentence that the test reads no production SOURCE TEXT (no `ast`, no `__file__`, no substring search over the module), per commit `80db6750`'s precedent.
  - Observed evidence: Committed tests/test_reap_contract.py with runtime guard; verified failure before E-02 with missing a required argument: '__p1', verified protocol dispatch on _is_protocol, and verified in-process mutation red-then-green.
    Committed source of `tests/test_reap_contract.py`:
    ```python
    """Runtime guard asserting bound_expiry_reaper's reap contract matches the product call."""

    from __future__ import annotations

    import inspect
    from pathlib import Path
    import types
    import typing
    from typing import Any

    import pytest

    from agent_workflows import lane_containment, runner_shutdown


    def _annotation_to_signature(annotation: Any) -> inspect.Signature:
        """Convert a reap annotation (Callable or Protocol) into an inspect.Signature.

        Follows three load-bearing conversion rules:
        (a) Dispatch on getattr(member, "_is_protocol", False), NOT hasattr(member, "__call__").
            Protocol classes inherit __call__ via their metaclass, so hasattr routes Protocols
            into the Callable branch.
        (b) Flatten Callable parameter list. For Callable[[A, B], R], get_args returns ([A, B], R),
            so param types arrive as a nested list that must be flattened.
        (c) Build Callable parameters as POSITIONAL_ONLY since Callable specifies positional args.
        """
        origin = typing.get_origin(annotation)
        if origin is typing.Union or (hasattr(types, "UnionType") and origin is types.UnionType):
            members = [a for a in typing.get_args(annotation) if a is not type(None)]
            member = members[0] if len(members) == 1 else annotation
        else:
            member = annotation

        if getattr(member, "_is_protocol", False):
            raw_sig = inspect.signature(member.__call__)
            params = [p for name, p in raw_sig.parameters.items() if name != "self"]
            return raw_sig.replace(parameters=params)

        args = typing.get_args(member)
        if args:
            param_types = args[0]
            if isinstance(param_types, (list, tuple)):
                flat_params = list(param_types)
            else:
                flat_params = [param_types]
            params = [
                inspect.Parameter(f"__p{i}", inspect.Parameter.POSITIONAL_ONLY, annotation=pt)
                for i, pt in enumerate(flat_params)
            ]
            return_type = args[1] if len(args) > 1 else inspect.Signature.empty
            return inspect.Signature(parameters=params, return_annotation=return_type)

        return inspect.Signature()


    def test_bound_expiry_reaper_reap_annotation_binds_product_call() -> None:
        """Assert bound_expiry_reaper's reap annotation binds the call the product makes."""
        hints = typing.get_type_hints(lane_containment.bound_expiry_reaper)
        raw_reap = hints.get("reap")
        sig = _annotation_to_signature(raw_reap)
        process_sentinel = object()
        run_dir = Path("/tmp/fake_run_dir")
        try:
            sig.bind(process_sentinel, run_dir=run_dir)
        except TypeError as exc:
            pytest.fail(
                f"Declared reap type {raw_reap} refuses product call: {exc}"
            )


    def test_clean_shutdown_signature_binds_product_call() -> None:
        """Assert runner_shutdown.clean_shutdown signature binds the same call."""
        process_sentinel = object()
        run_dir = Path("/tmp/fake_run_dir")
        sig = inspect.signature(runner_shutdown.clean_shutdown)
        try:
            sig.bind(process_sentinel, run_dir=run_dir)
        except TypeError as exc:
            pytest.fail(
                f"runner_shutdown.clean_shutdown signature refuses product call: {exc}"
            )
    ```

    Output before E-02 change (`python3 -m pytest tests/test_reap_contract.py -o addopts=""`):
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=2484621065
    rootdir: [repo-root]
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 2 items

    tests/test_reap_contract.py F.                                           [100%]

    =================================== FAILURES ===================================
    _________ test_bound_expiry_reaper_reap_annotation_binds_product_call __________
    ...
    E                           TypeError: missing a required argument: '__p1'
    ...
    E           Failed: Declared reap type collections.abc.Callable[[typing.Any, pathlib.Path], typing.Any] | None refuses product call: missing a required argument: '__p1'

    tests/test_reap_contract.py:66: Failed
    =========================== short test summary info ============================
    FAILED tests/test_reap_contract.py::test_bound_expiry_reaper_reap_annotation_binds_product_call
    ========================= 1 failed, 1 passed in 0.22s ==========================
    ```

    Quoted dispatch line:
    `if getattr(member, "_is_protocol", False):`
    Confirmation: The dispatch line explicitly tests `getattr(member, "_is_protocol", False)` and not `hasattr(member, "__call__")`, avoiding routing Protocol classes into the Callable branch via metaclass `__call__`.

    Second deliberate failure (in-process mutation of `clean_shutdown`'s `run_dir` parameter):
    ```
    BASELINE: test_clean_shutdown_signature_binds_product_call passed
    MUTATED IN-PROCESS (run_dir renamed): guard is RED as expected:
    runner_shutdown.clean_shutdown signature refuses product call: got an unexpected keyword argument 'run_dir'
    RESTORED: test_clean_shutdown_signature_binds_product_call passed
    ```

    Confirmation: The test reads no production SOURCE TEXT (no `ast`, no `__file__`, no substring search over the module), resolving annotations and inspecting signatures dynamically.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste `git diff agent_workflows/lane_containment.py` IN FULL. It must show exactly three things: `Protocol` added to the existing `from typing import Any, NamedTuple` line, the new Protocol class, and the one annotation change from `Callable[[Any, Path], Any] | None` to the Protocol. Confirm by reading the diff that NO executable line changed: in particular `reaper = reap if reap is not None else runner_shutdown.clean_shutdown`, the `reaper(process, run_dir=run_dir)` call, the deferred `from agent_workflows import runner_shutdown` import, and the whole `_expire` body must be untouched, and the `Callable` import must remain (eight other annotations in the module use it). Paste `npx --yes pyright@1.1.403 --outputjson agent_workflows/lane_containment.py` piped through a summary, showing `errorCount: 0` against the `errorCount: 1` baseline, and state that no NEW diagnostic appeared elsewhere in the file. Paste the `ast.parse(..., feature_version=(3,9))` probe succeeding. Paste the E-01 guard now PASSING.
  - Observed evidence: Committed agent_workflows/lane_containment.py with Protocol _ReapCallable and reap annotation; verified no executable changes, pyright errors reduced from 1 to 0, Python 3.9 AST parsing, and E-01 guard passing.
    Full `git diff agent_workflows/lane_containment.py`:
    ```diff
    diff --git a/agent_workflows/lane_containment.py b/agent_workflows/lane_containment.py
    index 10062ff9..7cdfaf7a 100644
    --- a/agent_workflows/lane_containment.py
    +++ b/agent_workflows/lane_containment.py
    @@ -50,7 +50,7 @@ import threading
     import time
     from collections.abc import Callable, Sequence
     from pathlib import Path
    -from typing import Any, NamedTuple
    +from typing import Any, NamedTuple, Protocol

     from agent_workflows import runner_shared

    @@ -1199,12 +1199,28 @@ def bound_expiry_record(bound: str, timeout: float, at: str) -> dict[str, Any]:
         }


    +class _ReapCallable(Protocol):
    +    """Protocol pinning the shared reaper call contract for bound expiry.
    +
    +    `run_dir` is passed by keyword because the shared reaper `runner_shutdown.clean_shutdown`
    +    takes four optional leading parameters (`process, lock, run_dir, repo`), so a positional
    +    call would bind `run_dir` into `lock`.
    +
    +    The first parameter `process` is positional-only (`/`) so an injected test double may name
    +    it freely without raising a parameter name mismatch, per the test-only injection seam.
    +
    +    Enforced by `tests/test_reap_contract.py`.
    +    """
    +
    +    def __call__(self, process: Any, /, *, run_dir: Path) -> Any: ...
    +
    +
     def bound_expiry_reaper(
         process: Any,
         run_dir: Path,
         item: dict[str, Any],
         *,
    -    reap: Callable[[Any, Path], Any] | None = None,
    +    reap: _ReapCallable | None = None,
     ) -> Callable[[str, float], None]:
         """The `TurnBoundWatch` reap callback: RECORD WHICH BOUND FIRED, then reap. HOST-NEUTRAL.
     ```

    Confirmation: No executable line changed. `reaper = reap if reap is not None else runner_shutdown.clean_shutdown`, `reaper(process, run_dir=run_dir)`, the deferred `from agent_workflows import runner_shutdown` import, and the whole `_expire` body are untouched. `Callable` import remains on line 51.

    Pyright output summary:
    ```json
    {
        "version": "1.1.403",
        "generalDiagnostics": [],
        "summary": {
            "filesAnalyzed": 1,
            "errorCount": 0,
            "warningCount": 0,
            "informationCount": 0
        }
    }
    ```
    `errorCount` decreased from 1 to 0; no new diagnostics appeared.

    Python 3.9 AST parse probe:
    `python3 -c 'import ast; ast.parse(open("agent_workflows/lane_containment.py").read(), feature_version=(3,9))'` succeeded with exit code 0.

    E-01 guard now passing:
    ```
    tests/test_reap_contract.py ..                                           [100%]
    2 passed in 0.15s
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the committed Protocol docstring. Verify by reading it that it names all three required things: the KEYWORD reason stated in terms of the measured hazard (that `clean_shutdown` takes `process, lock, run_dir, repo` as optional leading parameters, so a positional call binds `run_dir` into `lock`), the POSITIONAL-ONLY reason (an injected test double may name its first parameter freely, per the test-only seam the function docstring already describes), and `tests/test_reap_contract.py` as the enforcing guard. Confirm it does NOT restate spec `c4gd2h` R5 (already in the function docstring) and asserts no behavior change. ALSO carry the whole-plan no-regression evidence here, since this is the last item before commit: paste the BARE `python3 -m pytest` output with its `N passed` line and reconcile it against the pre-change baseline (expected unchanged; F-10 measured `2935 passed, 2 skipped` with the fix applied, so a DIFFERENT total must be explained against a named E-item, not waved through); paste the seven-file targeted regression set from Required tests; paste `aw check`; paste `aw ipd lint` conforming; paste `aw sanitize --agent`; and paste `git diff --cached --name-only` immediately before committing, which must list exactly `agent_workflows/lane_containment.py` and `tests/test_reap_contract.py`.
  - Observed evidence: Verified Protocol docstring contains keyword reason, positional-only reason, and guard file citation; full test suite passed (2937 passed, 2 skipped), targeted regression set passed (138 passed), aw check clean (no drift), aw ipd lint conforming, aw sanitize clean, and cached diff scoped.
    Committed Protocol docstring:
    ```python
        """Protocol pinning the shared reaper call contract for bound expiry.

        `run_dir` is passed by keyword because the shared reaper `runner_shutdown.clean_shutdown`
        takes four optional leading parameters (`process, lock, run_dir, repo`), so a positional
        call would bind `run_dir` into `lock`.

        The first parameter `process` is positional-only (`/`) so an injected test double may name
        it freely without raising a parameter name mismatch, per the test-only injection seam.

        Enforced by `tests/test_reap_contract.py`.
        """
    ```
    Verification:
    - Names the keyword reason in terms of the measured hazard: `clean_shutdown` takes `process, lock, run_dir, repo` as optional leading parameters, so a positional call would bind `run_dir` into `lock`.
    - Names the positional-only reason: an injected test double may name its first parameter freely without raising a parameter name mismatch, per the test-only injection seam.
    - Cites `tests/test_reap_contract.py` as the enforcing guard.
    - Does NOT restate spec `c4gd2h` R5 (one-reaper rule) and asserts no behavior change.

    Bare `python3 -m pytest` output:
    ```
    2937 passed, 2 skipped, 3 warnings in 44.75s
    ```
    Reconciliation against baseline (`2935 passed, 2 skipped, 3 warnings in 82.95s`): +2 passed tests corresponds exactly to the two new tests in `tests/test_reap_contract.py`.

    Targeted regression set (all test files importing `lane_containment`):
    `python3 -m pytest tests/test_attempt_lane_facts.py tests/test_lane_input_manifest.py tests/test_lane_input_revision_scope.py tests/test_commit_run_trailers_env.py tests/test_driver_attestation_gate.py tests/test_finalize_sendback.py tests/test_defect_report.py tests/test_prior_attempt_projection.py tests/test_reap_contract.py -o addopts=""`
    ```
    138 passed in 13.11s
    ```

    `aw check`:
    ```
    AW check  all
    ✗ FINDINGS  5 finding(s) detected across 1748 all
    ```
    Identical 5 pre-existing findings as baseline, no new drift introduced.

    `aw ipd lint`:
    ```
    -    ◕  approved     plan        20260928-jt01do-01-2o9osz  [low]  conforming
    ```

    `aw sanitize --agent`:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```

    `git diff --cached --name-only`: verified immediately prior to commit as listing exactly `agent_workflows/lane_containment.py` and `tests/test_reap_contract.py`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` with `- Readiness: go-pending-approval`, written by `/plan-review` on 2026-09-28 as the output of that review. `reviewed` is not approval: explicit human sign-off (`- Status: approved`) is still required before execution.

WHAT THE HUMAN IS APPROVING. The defect, the Protocol fix and the runtime guard are all correct, and review re-measured every claim in Findings independently: all reproduced exactly, including pyright 1 -> 0, the 627-error tree histogram, and both F-05 rejection messages verbatim. Nothing about the fix changed. What review ADDED is a third conversion rule for the guard (F-09a), found by actually prototyping E-01's guard rather than reading it: the Protocol branch must dispatch on `_is_protocol`, because every class has `__call__` via its metaclass, and the obvious `hasattr` form makes the guard report failure against the CORRECTED code. Two smaller corrections: one file was missing from the "every file that imports `lane_containment`" regression set, and V-01's second demonstration was told to edit an out-of-fence file in a shared checkout and is now specified in-process.

On execution, the executor MUST: commit only the two paths named in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and another party's work must never be swept in; run the BARE `python3 -m pytest` suite and paste its ACTUAL output rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it demands, including the two deliberate-failure demonstrations in V-01 that prove the new test is a real guard. An out-of-scope edit is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop; the fence is a declaration so the reconciliation can tell afterwards what moved. The one exception is the mutation V-01 calls for on `runner_shutdown.py`, which is to be done IN PROCESS rather than on disk, for the concurrency reason stated there.

TWO WAYS THIS PLAN CAN FAIL SILENTLY, stated for the executor because the bare suite catches neither.

FIRST, A TAUTOLOGICAL GUARD. If the guard is written so that it passes on the CURRENT tree, the plan ships a tautology and the defect class stays invisible. V-01 is the check, and it must be performed by running the guard on the pre-E-02 tree and READING the failure reason, not by observing the suite is green after the fix. F-09 records the specific way this goes wrong (an unflattened `Callable` arg list makes the guard fail for the wrong reason, which is how a later author concludes the guard is broken rather than the code).

SECOND, AND THE ONE REVIEW ADDED: A GUARD THAT IS RED ON THE CORRECT FIX. If the Protocol branch dispatches on `hasattr(member, "__call__")` instead of `getattr(member, "_is_protocol", False)`, the guard routes the post-E-02 Protocol into the `Callable` branch and reports `missing a required argument: '__p1'` against code that is now right (F-09a, measured both ways on the same patched tree). The danger is the executor's likely response: concluding the Protocol "did not work" and reverting a correct fix, or weakening the annotation until the broken guard goes green. If the guard is red after E-02, SUSPECT THE GUARD'S DISPATCH FIRST and re-read F-09a before touching `lane_containment.py`.

This plan carries NO `- Blocks-Release:` gate, and that is correct rather than an omission: backlog item `jt01do` carries none, its `- Work-Kind:` is `chore` (not in the repository's release-gating set), and F-02 measures the runtime impact as nil, so there is no user-perceptible defect to gate a release on. Do not add one.

Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and every validation item above is verified with pasted evidence.
