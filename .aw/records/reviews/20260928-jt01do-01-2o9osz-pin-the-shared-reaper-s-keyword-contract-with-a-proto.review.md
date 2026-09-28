# Review findings: plan 2o9osz

- Subject-Id: 2o9osz
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `79b3b0d1` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize --agent`
conforms after revision with `findings: 0`, E/V bijection 3/3. No pre-review snapshot was owed: the
plan was committed and unmodified (`git status --short` clean) and the lane-input copy at
`.aw/state/lane-inputs/rev-3/` is byte-identical to the tracked file (`diff` reported no difference).

THIS IS THE BEST-EVIDENCED PLAN OF THIS SWEEP AND THAT IS WORTH STATING PLAINLY. I re-measured every
material claim in Findings independently rather than accepting any of them, and ALL FOURTEEN reproduced
EXACTLY, several to the digit: pyright's `errorCount: 1` with a single `reportCallIssue` at zero-based
line 1244 characters 41-48; `errorCount: 0` after the patch; the whole-tree histogram of F-12
(627 errors / 383 files / 5 `reportCallIssue` / `runner_shared.py` 69 / `lane_containment.py` exactly 1);
F-05's two rejection messages verbatim (`Parameter name mismatch: "process" versus "proc"` without the
marker, then `Missing keyword parameter "run_dir"` and `Extra parameter "token"` with it); F-09's
wrong-reason message `got an unexpected keyword argument 'run_dir'`; and F-08's
`missing a required argument: '__p1'`. The 3.9 parse holds, the suite is `2935 passed, 2 skipped` on
both trees, and F-06/F-07's census of zero test-tree references is exact across all seven symbols.

THE DESIGN JUDGEMENTS ARE ALSO RIGHT, and two deserve naming because they are the kind usually got
wrong. Choosing a `Protocol` over the item's suggested `Callable[..., Any]` is correct for the reason
OQ-01 gives and F-03 measures: `clean_shutdown`'s first four parameters are `process, lock, run_dir,
repo`, all optional, so the erased annotation would accept a positional call that binds the run
directory into `lock` - I verified that misbinding directly (`sig.bind(object(), Path("/run/dir"))`
yields `{'process': object, 'lock': PosixPath}`). And refusing to write a source-reading test, citing
commit `80db6750`'s deletion of 366 structure-pinning tests, is exactly the right instinct; I read that
commit message and it says what the plan says it says.

WHAT REVIEW FOUND IS A THIRD LOAD-BEARING CONVERSION RULE THE PLAN DOES NOT STATE, and I found it only
by actually prototyping E-01's guard rather than reading it.

**THE PROTOCOL BRANCH MUST DISPATCH ON `_is_protocol`, NOT ON `hasattr(member, "__call__")` (PR-201,
HIGH).** E-01 says "For a `Protocol`, inspect `member.__call__` and drop `self`" without saying how to
DETECT that case. The natural implementation tests `hasattr(member, "__call__")` - and that is True for
a Protocol CLASS as well as for a `Callable` alias, because every class inherits `__call__` from its
metaclass. So a `hasattr`-first guard routes the post-E-02 Protocol into the `Callable` branch, where
`typing.get_args(_ReapCallable)` returns `()`, and reports `missing a required argument: '__p1'` against
code that is now CORRECT. I hit this live: my first prototype used `hasattr` and reported MISMATCH on the
PATCHED tree, which briefly looked like a defect in the plan's fix; the same guard body with
`getattr(member, "_is_protocol", False)` reported
`OK -> (process: 'Any', /, *, run_dir: 'Path') -> 'Any' accepts the product's call`. This is the same
defect class as F-09 (a guard failing for the wrong reason) but strictly worse, because F-09's version
fails on the BROKEN tree where a failure is expected, while this one fails on the FIXED tree. The
executor's likely response to a red guard after a correct fix is to revert the fix or weaken the
annotation until the broken guard passes, which is how this plan could ship having made the code worse.

**THE REGRESSION SET CLAIMS TO BE EXHAUSTIVE AND IS NOT (PR-202, MEDIUM).** Required tests names seven
files as "every test file that imports `lane_containment`"; `rg -l lane_containment tests/` returns
eight. `tests/test_prior_attempt_projection.py` is the omission, and it imports the module and calls
`lane_containment.prior_attempt_summary` three times. The gap is small in consequence (the change is
typing-only) but the claim was falsifiable and false, and the fix is one filename.

**V-01's SECOND DEMONSTRATION EDITS AN OUT-OF-FENCE FILE IN A SHARED CHECKOUT (PR-203, MEDIUM).** It
says to "temporarily rename `run_dir` in `runner_shutdown.clean_shutdown` ... and restore".
`agent_workflows/runner_shutdown.py` is not in `- Scope-Paths:`, the repository's own contract warns that
other agents may be editing concurrently, and the plan gives no restore mechanism - so an interrupted run
strands a broken shared reaper, and a careless restore (`git checkout --`) would discard a co-worker's
edit. The assertion under test needs no on-disk edit at all: `mock.patch.object` or a directly
constructed `inspect.Signature` exercises it exactly.

Two smaller items: the plan never says that E-01 deliberately lands a RED test so the tree is
transiently failing between E-01 and E-02, which invites an executor to treat that as a defect
(PR-204); and the gate's execution contract was complete except for the out-of-scope-edit disposition
(PR-205).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-201 | HIGH | UNDER-SCOPE | E. Testing / G. Plan executability | E-01 as authored ("For a `Protocol`, inspect `member.__call__` and drop `self`", with no detection rule); measured `getattr(_ReapCallable, "_is_protocol")` -> True, `hasattr(_ReapCallable, "__call__")` -> True, `typing.get_args(_ReapCallable)` -> `()`; two prototype guards differing ONLY in that dispatch test, run on the SAME patched tree: `hasattr`-first -> `MISMATCH ... missing a required argument: '__p1'`, `_is_protocol`-first -> `OK -> (process: 'Any', /, *, run_dir: 'Path') -> 'Any' accepts the product's call` | **THE GUARD'S PROTOCOL DETECTION IS UNSPECIFIED, AND THE NATURAL IMPLEMENTATION MAKES IT RED ON THE CORRECT FIX.** Every class has `__call__` via its metaclass, so a `hasattr`-first dispatch sends the post-E-02 Protocol down the `Callable` branch and the guard reports a missing positional argument against code that is now right. This is F-09's defect class in a second place and strictly worse: F-09 fails on the broken tree (where failure is expected), this fails on the FIXED tree. The executor's likely response is to revert the correct fix or weaken the annotation until the broken guard goes green, so the plan could ship having made the code worse while every gate stayed green. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | E-01 rewritten with THREE numbered conversion rules, (a) being the dispatch rule with its measurement and its named consequence; the raw Protocol signature recorded so `self`-dropping is concrete. New F-09a carries the two-prototype measurement. E-01's Expected outcome now states the post-fix PASS as an outcome rule (a) is what secures. V-01 requires the committed dispatch line QUOTED and confirmed, with the reason a passing V-02 cannot prove it. The gate names it as the second silent-failure mode and tells the executor to suspect the guard before the module. |
| PR-202 | MEDIUM | IN-SCOPE | E. Testing (completeness of a falsifiable claim) | Required tests naming seven files as "every test file that imports `lane_containment`"; `rg -l lane_containment tests/` returns EIGHT; `tests/test_prior_attempt_projection.py:15` imports it and calls `prior_attempt_summary` at `:38`, `:55`, `:64` | **AN EXHAUSTIVE CLAIM THAT IS NOT EXHAUSTIVE.** One importing test file was omitted from the targeted regression set. Low consequence for a typing-only change, but the claim was checkable and wrong, and a later reader reusing the list would inherit the gap. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The eighth file added; the correction noted inline; the executor told to RE-DERIVE the list with `rg -l lane_containment tests/` at execution time rather than trusting a list captured at authoring, since the population is live. |
| PR-203 | MEDIUM | UNDER-SCOPE | C. Operability / shared-checkout safety | V-01 and Required tests as authored ("temporarily rename `run_dir` in `runner_shutdown.clean_shutdown` ... and restore"); `- Scope-Paths:` contains only `lane_containment.py` and the new test; repository contract on concurrent work in a shared checkout | **THE DEMONSTRATION MUTATES A FILE OUTSIDE THE FENCE, IN A SHARED CHECKOUT, WITH NO RESTORE MECHANISM.** An interrupted run leaves a broken shared reaper for every other party, and the obvious restore (`git checkout --`) would discard a co-worker's concurrent edit to that file. The assertion needs no on-disk edit: the guard binds an `inspect.Signature`, so patching the attribute in process exercises it identically. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | Required tests now specifies the mutation IN PROCESS (`mock.patch.object`, or a directly constructed mutated `Signature`), states why (no window where a co-worker sees a broken reaper; no half-reverted edit if interrupted), and requires an explicit declaration plus clean before/after `git diff --exit-code` if an on-disk edit is judged unavoidable, with `git checkout --` forbidden on a co-worker-touchable path. V-01 points at that method. |
| PR-204 | LOW | UNDER-SCOPE | G. Plan executability | E-01 lands a deliberately RED test; E-02 turns it green; no statement anywhere that the tree is transiently red between them; Required tests asks for a bare suite run without saying from which item it must be green | The plan's own design (red guard first, so it is never a tautology) means the suite FAILS after E-01 by intent. Nothing says so, so an executor reaching a red suite mid-plan may treat it as a defect and debug or reorder the items. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A short ordering note added after Proposed changes stating the transient red is deliberate and that the bare suite is expected green only from E-02 onward. |
| PR-205 | LOW | IN-SCOPE | G. executability (scope fence) | Plan gate as authored: path-scoped commit, never-push, paste-actual-output and the lifecycle line all present; no out-of-scope-edit disposition; workflow Step 4 scope-fence ruling of 2026-09-01 | The gate carried every required execution-contract element except what to do about an out-of-scope edit. The correct wording is MAKE-AND-JUSTIFY (finalize refuses without a `--scope-reason`), not stop-and-report. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate states an out-of-scope edit is made then justified with `--scope-reason` and explicitly that it is not a reason to stop, with the V-01 in-process mutation named as the one deliberate exception. No "STOP and report" wording added. The commit clause now names this plan beside the two scope paths. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | PR-201 adds a third conversion rule to the guard. Fold it into E-01, or split the guard into a new E-item? | FOLD INTO E-01, as numbered rule (a). | (a) A new E-item for the dispatch rule: rejected, it is not a separate deliverable but a correctness constraint on the single test E-01 already writes, and splitting it would break the 3/3 E/V bijection for no gain in reviewability. (b) Leave it to the executor as an implementation detail: rejected on measurement - the natural implementation is the WRONG one, and its failure mode (red on the correct fix) is the single most likely way this plan damages the code. | The two-prototype measurement showing MISMATCH versus OK on the same patched tree from that one line; the plan's own precedent of stating measured conversion rules explicitly rather than letting them be discovered (F-09 exists for exactly that reason). | yes |
| D-2 | V-01's second demonstration mutates an out-of-fence shared file (PR-203). Widen `- Scope-Paths:` to include `runner_shutdown.py`, or specify an in-process mutation? | IN-PROCESS MUTATION; the fence stays two paths. | (a) Add `agent_workflows/runner_shutdown.py` to `- Scope-Paths:`: rejected, the plan does not and must not EDIT that file, and declaring it would make the finalize scope gate demand a `--scope-ack` for a path deliberately unmodified, plus it would mislead a reader about the blast radius. (b) Drop the second demonstration: rejected, it is what proves the guard watches the shared reaper and not only the annotation, which is the difference between a guard and a tautology. | The guard binds an `inspect.Signature`, so `mock.patch.object` exercises the identical assertion; the repository's shared-checkout contract forbids reverting another party's work and `git checkout --` cannot distinguish my edit from theirs. | yes |
| D-3 | Does any finding change the plan's `chore` classification or its absence of a release gate? | NO. `chore` and no `Blocks-Release:` are both correct. | Reclassify as `bug` and gate the release: rejected. The perceptibility test in the repository's release-gate policy asks for user-perceptible impact; F-02 measures the runtime behavior as correct (the keyword binds), and I re-verified that `sig.bind(object(), run_dir=Path("."))` succeeds against the real `clean_shutdown`. An annotation a non-gating tool disagrees with costs no user anything. | `inspect.signature` + `bind` probe on the shipped reaper; backlog `jt01do` carries `- Work-Kind: chore` and no `Blocks-Release:`; `.aw/config/project.json` sets no `release_gate_work_kinds`, so the default gating set is `bug` alone and `chore` is outside it. | yes |
| D-4 | OQ-01 and OQ-02 were resolved by the author from evidence. Do both hold on re-measurement? | BOTH HOLD; left resolved and non-blocking. | Re-open either for the maintainer: rejected, both are HOW questions with decisive in-repo answers, and I reproduced the measurements each rests on. | OQ-01: the `Callable[..., Any]` erasure versus the measured `lock` misbinding, plus F-05's marker measurement, all re-verified. OQ-02: `tests/test_turn_bounds.py`, `tests/test_lane_permission_posture.py` and `tests/test_lane_containment.py` all confirmed absent; `19313eed` confirmed as the deleting commit; `80db6750`'s message read in full and it says what the plan quotes. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is `FIXED`; none was deferred or left open, so no `- Blocking: yes` escalation under Step 4 is
owed either. Both pre-existing open questions remain `resolved` and non-blocking per D-4.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`
  after all edits; E/V counts confirmed 3 and 3.
- Lane input identity: `diff .aw/state/lane-inputs/rev-3/plan-20260928-jt01do-01-2o9osz-....ipd.md
  .aw/records/plans/pending/20260928-jt01do-01-2o9osz-....ipd.md` -> no difference; `git status --short`
  clean before editing, so no pre-review snapshot was owed.
- **F-01 reproduced exactly.** `npx --yes pyright@1.1.403 --outputjson agent_workflows/lane_containment.py`
  -> `filesAnalyzed: 1, errorCount: 1, warningCount: 0`; the single diagnostic is
  `error reportCallIssue | line 1244 chars 41 - 48 | Expected 1 more positional argument`. Confirmed by
  reading the source that `:1207` is the `reap` annotation and `:1245` (1-based) is
  `report = reaper(process, run_dir=run_dir)`, so the error is on the CALL as the plan says and the
  backlog item's `:1208` is the return annotation.
- **F-02 reproduced.** `inspect.signature(runner_shutdown.clean_shutdown)` is
  `(process=None, lock=None, run_dir=None, repo=None, *, extra_processes=())` with the first four
  `POSITIONAL_OR_KEYWORD`; `sig.bind(object(), run_dir=Path("."))` succeeds ->
  `{'process': <object>, 'run_dir': PosixPath('.')}`. So the keyword binds at runtime and the `chore`
  classification is right.
- **F-03 reproduced, and this is the measurement that justifies the Protocol.**
  `sig.bind(object(), Path("/run/dir"))` -> `{'process': 'object', 'lock': 'PosixPath'}`: a positional
  call binds the run directory into `lock`, exactly the silent misbinding the plan describes.
- **F-04 reproduced.** Patch applied in the working tree (Protocol added, annotation swapped, `Protocol`
  added to the `from typing import Any, NamedTuple` line): pyright -> `filesAnalyzed: 1, errorCount: 0,
  warningCount: 0`, no diagnostic anywhere in the file. Tree restored from a pre-edit copy under the
  gitignored `tmp/`; `git diff --stat agent_workflows/lane_containment.py` empty afterwards.
- **F-05 reproduced, both halves, with the messages verbatim.** Scratch probe WITHOUT the `/` marker:
  `errorCount: 1`, `Type "(proc: Any, *, run_dir: Path) -> Any" is not assignable to declared type
  "ReapNoSlash"`. Probe WITH `/` over four doubles: `errorCount: 2`, and the two errors are exactly
  `Missing keyword parameter "run_dir"` (for `def no_run_dir(process)`) and `Extra parameter "token"`
  (for `def extra_required(process, *, run_dir, token)`), while the differently-named double
  `def differently_named(proc, *, run_dir)` and the two-positional reaper are ACCEPTED. So the marker
  widens exactly the test-double freedom and refuses exactly the wrong shapes.
- **F-06 reproduced.** `ls` confirms `tests/test_turn_bounds.py`, `tests/test_lane_permission_posture.py`
  and `tests/test_lane_containment.py` all absent; `git log --diff-filter=D --name-only --
  tests/test_turn_bounds.py` names `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests").
- **F-07 reproduced exactly.** All seven symbols (`bound_expiry_reaper`, `bound_expiry_record`,
  `driver_bound_for_host`, `BOUND_MAX_TURN`, `BOUND_PERMISSION`, `MAX_TURN_TIMEOUT`, `TurnBoundWatch`)
  return ZERO matching files in both `tests/` and `tools/`.
- **F-08 reproduced, red then green, with the exact message.** A prototype guard resolving
  `get_type_hints(...)["reap"]`, flattening the `Callable` args and binding `(sentinel, run_dir=Path("."))`
  printed `MISMATCH -> (__p0, __p1, /) REFUSES the product's call: missing a required argument: '__p1'`
  on the shipped tree and `OK -> (process: 'Any', /, *, run_dir: 'Path') -> 'Any' accepts the product's
  call` on the patched tree. The second assertion (`clean_shutdown` binds the same call) printed OK on
  both.
- **F-09 reproduced, including the wrong-reason message.**
  `typing.get_args(Callable[[Any, Path], Any])` -> `([typing.Any, <class 'pathlib.Path'>], typing.Any)`,
  `args[0]` is a `list` of length 2. Omitting the flatten yields a one-parameter signature whose bind
  error is `got an unexpected keyword argument 'run_dir'`, the wrong reason exactly as recorded.
- **F-09a, THE FINDING REVIEW ADDED.** `getattr(_ReapCallable, "_is_protocol")` -> True;
  `hasattr(_ReapCallable, "__call__")` -> True; `typing.get_args(_ReapCallable)` -> `()`;
  `inspect.signature(_ReapCallable.__call__)` -> `(self, process: 'Any', /, *, run_dir: 'Path') -> 'Any'`.
  Two guard bodies differing ONLY in the dispatch test, both run against the SAME patched tree:
  `hasattr`-first -> `MISMATCH -> (__p0, __p1, /) REFUSES the product's call: missing a required
  argument: '__p1'`; `_is_protocol`-first -> `OK -> (process: 'Any', /, *, run_dir: 'Path') -> 'Any'
  accepts the product's call`. (A note for the record: my first `_is_protocol` run ALSO reported
  MISMATCH, which I traced to my own harness - running the probe as a script from `tmp/rev3/` put that
  directory on `sys.path`, where a `lane_containment.py.orig` backup shadowed the package import.
  Re-run without that shadowing it reported OK. The finding is about the dispatch rule, not about
  `sys.path`; the harness artifact is recorded only so a later reader does not mistake it for evidence.)
- **F-10 reproduced.** Bare `python3 -m pytest` on the PATCHED tree and again on the restored tree both
  reported `2935 passed, 2 skipped, 3 warnings` (45.03s claimed at authoring; 41.39s and 42.52s
  measured here, the difference being machine load), with `201 tests deselected by -m/-k`.
- **F-11 reproduced.** `ast.parse(source, feature_version=(3, 9))` on the patched module succeeded, and
  importing it reported `bound_expiry_reaper.__annotations__["reap"]` as `_ReapCallable | None`.
  `requires-python` confirmed `>=3.9`.
- **F-12 reproduced to the digit.** `npx pyright --outputjson agent_workflows tests tools` ->
  `filesAnalyzed: 383, errorCount: 627`; rule histogram `reportArgumentType` 239,
  `reportOptionalMemberAccess` 144, `reportAttributeAccessIssue` 106, `reportOptionalSubscript` 56,
  `reportOptionalCall` 48, `reportPossiblyUnboundVariable` 8, `reportCallIssue` 5; file histogram
  `runner_shared.py` 69, `test_research_cmd_create.py` 59, `test_run_viewer.py` 32, `test_runagy.py` 32;
  `lane_containment.py` exactly 1. All five `reportCallIssue` diagnostics enumerated, and exactly one is
  this defect.
- **F-13 reproduced.** `platform_lock.py:428`'s `preserve_lock_file=True` call sits inside
  `if _filelock_can_preserve():`, whose body introspects `filelock.FileLock.__new__`/`__init__` for that
  parameter; `tests/test_platform_lock_preserve.py:124` asserts
  `fl.assert_called_once_with("x.lock", timeout=0.0, preserve_lock_file=True)`. So it is correct
  version-guarded code the checker cannot see through.
- **F-14 reproduced.** `bound_expiry_reaper`'s docstring contains "It is injectable ONLY so a test can
  observe the call without spawning a real process", which is the evidence deciding the
  positional-only question.
- Conventions claims reproduced: no `pyrightconfig.json`, no `.mypy.ini`/`mypy.ini`, no `[tool.mypy]` or
  `[tool.pyright]` in `pyproject.toml`, no pyright or mypy on PATH, and the three CI workflows are
  exactly `tests.yml`, `local-leaks.yml`, `secret-scan.yml`. Commit `80db6750`'s message read in full and
  it states the structure-pinning rationale the plan quotes. Plan `lhmrhx`'s "THE SHARED HOME IS NAMED"
  paragraph read and it names `agent_workflows/lane_containment.py` as the plan says. The deferred
  `runner_shutdown` import confirmed inside the function body.
- `Callable` usage census: 8 annotation sites remain in the module after the one change, matching the
  plan's "eight other annotations" claim.
- PR-202's census: `rg -l lane_containment tests/` returns EIGHT files; the plan named seven; the
  omission is `tests/test_prior_attempt_projection.py`, which imports the module at `:15` and calls
  `prior_attempt_summary` at `:38`, `:55` and `:64`.
- Release-gate correctness: backlog `jt01do` is `- Status: graduated`, `- Work-Kind: chore`, and carries
  NO `- Blocks-Release:`; `.aw/config/project.json` sets no `release_gate_work_kinds`, so the default
  gating set is `bug` alone. The plan's gate paragraph explaining the absent gate is therefore correct.
  Carrier `f15tne` confirmed live (`- Status: open`, `- Work-Kind: followup`) and its summary matches the
  deferred row that names it.
- No code, test, or configuration file was modified by this review. The `lane_containment.py` patch used
  to verify F-04/F-05/F-08/F-11 was applied, measured, and REVERTED from a pre-edit copy; `git status
  --short` is clean and reports only this review's own two artifacts. All scratch probes and the guard
  prototypes were written under the gitignored `tmp/` tree and deleted afterwards.
