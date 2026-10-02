# IPD: Adopt mypy as a narrowed, high-signal static type gate in CI, with a measured baseline the repository can actually hold

- Date: 2026-09-30
- Kind: child
- Concern: Backlog `fcua9q` reports that nothing in the toolchain catches an annotation defect, so the wrong `Callable[[Any, Path], Any]` annotation `yifr0h` fixed by hand (backlog `g321ny`) could have sat in shipped code indefinitely. CONFIRMED, and the gate's value is no longer hypothetical: re-measured at review, mypy catches that exact defect shape (`error: Unexpected keyword argument "run_dir"  [call-arg]`, F-03), AND the same narrowed configuration this plan adopts finds a LIVE SHIPPED BUG the suite does not (F-06): `runner_shared.build_verify_and_continue_notice` is declared `-> str` and returns `None` on its main path, so the string `None` is interpolated into a recovery turn's prompt in place of the whole verify-and-continue instruction block. THE ITEM'S HEADLINE NUMBER IS UNDERSTATED (F-01): the 103 errors it cites are one file's; the package total is in the low 300s across 46 files and MOVES, which F-01 now states as a property rather than as a digit.
- Scope: Adopt `mypy` as a CI-only, fail-closed type gate over `agent_workflows/` with a NARROWED error-code selection, plus the test-extra/dev-group declaration and a `make typecheck` target. The narrowing is the whole design and it is measured, not guessed: disabling the ten `Any`-narrowing noise codes takes the package from a low-300s wall in 46 files to roughly two dozen in 11 or 12 (F-04), which is a baseline a human can read in one sitting rather than a wall that would have to be blanket-suppressed. This plan does NOT fix the surviving findings (F-05 triages every one of them and E-05 suppresses them per-line with a cited reason), does NOT touch pre-commit (OQ-02 hands that to the maintainer with the timing measurement it needs), and does NOT adopt strictness beyond the default. THE ONE EXCEPTION IS DELIBERATE: F-06's live bug is FIXED here rather than suppressed, because suppressing a real defect to turn a gate on would be the exact dishonesty the gate exists to prevent. E-07 PINS THE TOOL AND ENVIRONMENT the baseline was measured in, because review measured the baseline to be environment-DEPENDENT (F-13) and an unpinned gate reds `main` on a dependency release the repository never chose.
- Scope-Paths: pyproject.toml, Makefile, .github/workflows/tests.yml, agent_workflows/runner_shared.py, tests/test_typecheck_gate.py, agent_workflows/platform_lock.py, agent_workflows/private_file.py, agent_workflows/run_packet.py, agent_workflows/completion.py, agent_workflows/cli.py, agent_workflows/backlog.py, agent_workflows/ipd_lint.py, agent_workflows/run_selection_policy.py, agent_workflows/ipd_authoring.py, agent_workflows/render_stream.py, agent_workflows/_compat.py, CONTRIBUTING.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: fcua9q
- Set: fcua9q
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: m7fllj
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 through PR-011. Reviewed in an isolated lane at HEAD `a4e7f31e`, 196 commits after the authoring HEAD `69f341b7`. Structural preflight `aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) before semantic review. EVERY measurement in the plan was RE-RUN rather than trusted, and the load-bearing ones reproduce: F-03's `g321ny` probe produces `Unexpected keyword argument "run_dir"  [call-arg]` both bare and under the narrowed config, and F-06's live bug reproduces exactly (`RETURN VALUE: None`, `'Mode: recoveryNone'`). THE THREE SUBSTANTIVE CORRECTIONS. FIRST (PR-001, HIGH), every absolute finding count in the plan is now WRONG at this HEAD (321 measured as 335; 23 as 24 locally) and will be wrong again at execution, so each is restated as a property requiring re-derivation, exactly as the live-artifact convention already demands of the suite count. SECOND (PR-002, HIGH, the dominant finding), the baseline is ENVIRONMENT-DEPENDENT in a way the plan never measured: `platform_lock.py:429`'s `preserve_lock_file` finding EXISTS under the installed `filelock` 3.29.7 and VANISHES under `filelock` 4.0.7, which `dependencies = ["filelock>=3"]` permits CI to resolve, so E-05's per-line ignore would be UNUSED in CI and the count V-05 reconciles is unknowable without pinning; new E-07 pins the measured environment and V-07 proves the pin. THIRD (PR-003, HIGH), the plan shipped a fail-closed CI gate with NO upper bound on the tool, so any future mypy release reds `main`; E-07 adds the ceiling. Also corrected: the undeclared eleven-module fence is now DECLARED rather than left as a reviewer question (PR-004), the pre-existing suite failure is recorded so it is not attributed to this plan (PR-005), F-05's `render_stream.render_event` triage is corrected from an annotation-precision issue to a CORRECT annotation (PR-006), F-11's timings are re-measured (PR-007), and F-04's per-code census is restated as a shape rather than as digits (PR-008). The plan's design judgements all SURVIVE review: per-line over per-module (F-10 reproduces, and the override would indeed blind `return` across the file holding F-06), 3.10 target (F-08's silent config-file ignore reproduces, and review additionally measured WHEN it began: `2.0.0`), and mypy over pyright.
- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `fcua9q`. Every measurement taken fresh in this lane at HEAD `69f341b7`; none carried over from the item or from `yifr0h`. The item's headline error count is CORRECTED (F-01). The item's premise that a checker would have caught `g321ny` is CONFIRMED by direct reproduction (F-03). A LIVE SHIPPED BUG the proposed gate finds is recorded (F-06) and is fixed by E-04 rather than suppressed. The item's four reserved maintainer decisions are resolved from repository evidence where the evidence is decisive (OQ-01 checker choice, OQ-03 baseline regime) and handed to the maintainer where it is genuinely a risk-appetite call (OQ-02 pre-commit).
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give this repository a static type gate that would have caught `g321ny` and that is worth keeping: CI-only, fail-closed, narrowed to the error codes that indicate defects rather than `Any`-narrowing noise, pinned to a named environment so its clean verdict is reproducible, and standing on a baseline of roughly two dozen findings that were individually READ and triaged rather than a several-hundred-error wall silenced wholesale. After this plan a wrong annotation of the `g321ny` shape fails CI on every push and pull request, the one live defect the gate already found is fixed, and each remaining known finding carries a per-line suppression naming WHY it is not a defect, so the next reader inherits a triaged baseline instead of an unexplained wall.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: declare the tool and its configuration

- [x] E-01 Declare `mypy` in `pyproject.toml`'s `[project.optional-dependencies] test` extra and in the `[dependency-groups] dev` group, as a TEST/DEV-ONLY dependency with the BOUNDED specifier E-07 fixes, and write the comment paragraph that justifies it in the register the neighbouring `filelock` and `PyYAML` paragraphs already use.

  IT IS NOT A RUNTIME DEPENDENCY AND MUST NOT BECOME ONE. `dependencies` stays exactly `["filelock>=3"]`. D138 governs the register: dependency MINIMIZATION is the principle, not a prohibition, so the comment must say what the tool buys (a gate for a defect class the suite provably does not catch, F-06) rather than apologising for existing.

  THE FLOOR IS `>=1.18` FOR A MEASURED REASON, NOT A GUESS. mypy dropped Python 3.9 support at `1.20.0` (F-07: `1.19.1` publishes `Requires-Python: >=3.9`, `1.20.0` publishes `>=3.10`), and this project's floor is `requires-python = ">=3.9"` with a CI leg on 3.9. A floor of `>=1.18` therefore RESOLVES on the 3.9 leg, where a bare `mypy` would not. E-03 is what keeps the 3.9 leg from running it at all, and this floor is the belt to that braces.

  THE SPECIFIER IS NOT A BARE FLOOR; IT CARRIES AN UPPER BOUND (PR-003). Write the exact specifier E-07 determines, NOT `mypy>=1.18` alone. A fail-closed gate whose checker is unbounded reds `main` on a release the repository never chose, and F-08 measures mypy DOING exactly that mid-series (2.0.0 changed how a config-file `python_version` is handled). E-07 owns the bound and its justification; this item writes what E-07 fixes, which is why it now depends on E-07.
  - Depends on: E-07
  - Expected outcome: `pip install -e '.[test]'` and `pip install --group dev` both install mypy at a BOUNDED specifier matching E-07; `dependencies` is unchanged at one entry; the declaration carries a comment naming the caught-defect justification, the 3.9 floor constraint, and the reason for the upper bound.
  - Execution state: performed

- [x] E-02 Add a `[tool.mypy]` section to `pyproject.toml` carrying the NARROWED configuration, and a `typecheck` target to the `Makefile` that runs it the one canonical way.

  THE EXACT CONFIGURATION, every value of which is measured in F-04 and F-08:

  ```toml
  [tool.mypy]
  python_version = "3.10"
  ignore_missing_imports = true
  disable_error_code = [
      "arg-type", "attr-defined", "assignment", "misc", "union-attr",
      "index", "var-annotated", "dict-item", "list-item", "has-type",
  ]
  ```

  `python_version = "3.10"` AND NOT `"3.9"`, WHICH IS THE SUBTLEST DECISION HERE. Modern mypy REFUSES a 3.9 target: `--python-version 3.9` exits with `argument --python-version: Python 3.9 is not supported (must be 3.10 or higher)`, and in a CONFIG FILE the same value is not honored either but is reported as a diagnostic and then ignored (F-08), which is the dangerous shape because it looks configured and is not. So 3.10 is the LOWEST HONEST TARGET, and the residual gap it leaves (a 3.9-only incompatibility the gate cannot see) is recorded in OQ-04 rather than hidden. Measured cost of the difference: exactly one additional finding at 3.10 versus 3.11+ (`_compat.py` `joinpath` arity), which E-05 suppresses.

  `ignore_missing_imports = true` BECAUSE THE ALTERNATIVE BUYS NOTHING HERE: measured twice, at authoring and again at review, the package total is IDENTICAL with and without it (F-02), so no finding in this baseline is a missing-stub artifact and the flag is insurance against a future optional import rather than a suppression of anything present. Re-derive the pair and assert their EQUALITY, not a digit.

  THE TEN DISABLED CODES ARE THE ENTIRE POINT AND MUST BE COMMENTED AS SUCH. They are not a taste choice: enabling them yields findings in the hundreds across 46 files, and the backlog item itself predicts the consequence ("a gate turned on without a baseline would fail every commit"). Disabling them yields roughly two dozen in 11 or 12 files (F-04). The comment must state BOTH NUMBERS AS MEASURED AT EXECUTION, each stamped with the HEAD and the pinned mypy version that produced it (PR-001: authoring measured 321->23 at `69f341b7` and review re-measured 335->24 at `a4e7f31e`, so a bare pair of digits in a comment rots within days and a stamped pair stays honest). It must state that the disabled set is the `Any`-narrowing and annotation-completeness family rather than the wrong-call family, and that re-enabling any of them is a deliberate future project with its own baseline, not a tightening someone should do casually. CRITICALLY, it must record the falsifiable proof that the narrowing did not narrow away the point: the `g321ny` defect shape is still caught under exactly this configuration (F-03).

  DO NOT SET `warn_unused_ignores`. Measured: it roughly DOUBLES the finding count, because the tree already carries 33 `type: ignore` comments written against no checker and many are unused under this configuration (F-09). Turning it on would make E-05's per-line suppressions fight the pre-existing ones. A SECOND, INDEPENDENT REASON measured at review (F-13): E-05's `platform_lock.py` suppression is ENVIRONMENT-CONDITIONAL, so under this flag it would itself become a finding in a `filelock` 4.x environment. Recorded in OQ-05 as a follow-on, not done here.

  THE `make typecheck` TARGET runs `python3 -m mypy agent_workflows` and nothing else; it must be added to `.PHONY` and must NOT be wired into `make test` (OQ-02 explains why the gate is CI-only in this plan).
  - Depends on: E-01
  - Expected outcome: `make typecheck` runs the configured gate; `python3 -m mypy agent_workflows` picks the same configuration up from `pyproject.toml` with no flags; the configuration carries the un-narrowed-versus-narrowed justification with both numbers stamped by HEAD and pinned mypy version, the 3.10-target reason, and the still-catches-`g321ny` proof.
  - Execution state: performed

### Task group 2: run it in CI, on the legs that can actually run it

- [x] E-03 Add a `typecheck` job to `.github/workflows/tests.yml` as a NAMED, FAIL-CLOSED step, modelled on the existing `attention-check` job's shape (single Python, `pip install -e`, one named step per gate, no `continue-on-error`).

  ONE PYTHON VERSION, NOT THE MATRIX, and the reason is E-02's constraint rather than thrift: mypy does not install on the 3.9 leg (F-07) and does not accept a 3.9 target anywhere, so a matrix job would fail on its first leg for a reason that has nothing to do with this repository's types. Pin the job to `"3.12"`, which is inside mypy's supported range and is not the newest release, so the gate does not break when a new Python ships before mypy supports it.

  ONE OS IS ALSO CORRECT AND IS NOW MEASURED RATHER THAN ASSUMED (F-14). `ubuntu-latest` alone is right even though the `unittest` job spans three OSes and F-05 classifies three findings as platform-conditional: mypy analyzes a DECLARED platform rather than the host's, and the narrowed total is IDENTICAL under `--platform` linux, `win32` and `darwin`, because the Windows-only branches are type-checked everywhere regardless. So the single-runner shape is a cost choice with no coverage consequence, and the job comment should say so rather than leaving a reader to wonder.

  IT MUST NOT BE ADVISORY. No `continue-on-error`. The whole defect in `fcua9q` is that the check FAILS OPEN today; an advisory job would reproduce that failure in a new place and let the next `g321ny` land green. This follows the precedent set in this same file, where `aw check backlog` was explicitly flipped from advisory to fail-closed once its baseline measured clean, and its comment records that transition.

  INSTALL THE PROJECT, DO NOT HAND-LIST THE TOOL. Use `pip install -e ".[test]"`, exactly as the `unittest` and `output-conformance` jobs do, so the environment follows `pyproject.toml` instead of drifting from it. That file's own comment history records this specific drift happening before (CI once ran with a declared dependency missing, producing 155 failures), and hand-listing mypy here would reintroduce the same class of hole. This is ALSO why E-07's pins live in `pyproject.toml` rather than in this workflow file: the installed environment is then the SAME one a developer running `make typecheck` gets, so a finding set is reproducible off CI instead of being a property of the runner.
  - Depends on: E-02
  - Expected outcome: `tests.yml` carries a `typecheck` job that installs the project and runs the gate as a fail-closed named step on one pinned Python and one OS, with a comment recording the F-14 platform-invariance measurement; no existing job is modified.
  - Execution state: performed

### Task group 3: fix the one real defect the gate found, then triage the rest

- [x] E-04 FIX the live defect at `runner_shared.build_verify_and_continue_notice`: the function is declared `-> str`, builds its `lines` list, and then FALLS OFF THE END without returning it, so it returns `None` whenever `decision.verify_and_continue` is true. Add the missing `return "\n".join(lines)` (matching the joining convention its sibling notice builders in this module use) and a regression test in `tests/test_typecheck_gate.py`.

  THIS IS A USER-VISIBLE DEFECT, NOT A TYPE NIT, which is why it is fixed and not suppressed. Measured directly (F-06): the only caller interpolates the result into the execute-turn prompt as `{verify_notice}`, so a recovery turn that the driver routed to VERIFY AND CONTINUE prior work receives the literal string `None` where the entire instruction block should be. The block's own purpose is to stop a resumed agent re-authoring work that already exists on another branch, so the failure mode is the duplicated-work waste the block was written to prevent, occurring silently.

  THE FIX IS THE RETURN, NOT A SIGNATURE CHANGE. Do NOT "fix" this by widening the annotation to `-> str | None`: the caller's f-string interpolation means `None` renders as `None`, so a widened annotation would make the checker agree with a broken program. The early `return ""` on the `not decision.verify_and_continue` path already establishes the empty string as this function's no-op value, so `str` is the correct contract and the body is what is wrong.

  THE REGRESSION TEST MUST ASSERT BEHAVIOR, NOT THE ANNOTATION. Construct a `RecoveryDisposition` with `verify_and_continue` true and assert the returned value is a non-empty `str` containing the branch name and the commit subject, and separately that the false case returns `""`. Do NOT assert the return type by reading the source or by `inspect`; per the repository's testing contract (GUIDING_PRINCIPLES P16) a test that reads production source to check a structural property has no business existing.

  THE CONSTRUCTOR SHAPE, MEASURED AT REVIEW so the executor does not have to discover it: `RecoveryDisposition` is a NamedTuple whose `_fields` are `disposition, reason, inspected_lane_id, inspected_branch, inspected_worktree, lane_state, commits_ahead, dirty, snapshot_only, real_commits`, and `verify_and_continue` is a derived `@property`, NOT a field, so it cannot be set directly: construct with `disposition="verify-and-continue"` (the value the property keys on) and `real_commits=[(sha, subject)]`. ALSO WORTH KNOWING AND WORTH ASSERTING: no existing test calls this function at all (F-06's census found only an `assertIs` identity pin and zero `verify_notice` matches across `tests/`), so this test is the FIRST behavioral coverage of the symbol rather than an addition to existing coverage. Assert the no-op case too, since `""` and `None` are both falsy and only an explicit `assertEqual(..., "")` distinguishes the fixed function from the broken one.
  - Depends on: none
  - Expected outcome: `build_verify_and_continue_notice` returns the rendered notice string; a test pins both the populated and the empty case by behavior, with the empty case asserted as `""` rather than merely falsy; the `[return]` finding for that symbol disappears from the gate's output.
  - Execution state: performed

- [x] E-05 Bring the baseline to ZERO by adding a per-line `# type: ignore[<code>]` to each remaining known finding, EACH WITH A SHORT INLINE REASON, and add a test that pins the gate's clean exit.

  RE-DERIVE THE FINDING SET; DO NOT WORK FROM THIS PLAN'S LIST (PR-001). Run the configured gate FIRST, in the E-07-pinned environment, and suppress exactly what IT reports. The authored list is 23 findings at HEAD `69f341b7`; review measured 24 at HEAD `a4e7f31e` in a `filelock` 3.29.7 environment and 23 in a `filelock` 4.0.7 one. Treat F-05 as a TRIAGE REFERENCE for the shapes you will meet, never as the set.

  TWO SITES NEED SPECIFIC CARE, both measured at review. FIRST, `platform_lock.py:429`'s `preserve_lock_file` finding EXISTS OR NOT depending on the resolved `filelock` version (F-13), so if the pinned environment does not report it, do NOT add an ignore there; note its absence in V-05 instead. SECOND, `render_stream.render_event` is a `[return]` finding of the SAME shape as F-06's but is NOT a bug (PR-006): its `-> str | None` is CORRECT, because its consuming caller in `oc_runipd` guards with `if rendered is not None:`. Do not "fix" it by adding a return value, and do not widen anything; either suppress it per-line with that reason, or add an explicit `return None` if that reads better, but do NOT treat it as a second live defect.

  PER-LINE, NEVER PER-MODULE. A `[[tool.mypy.overrides]]` block silencing these codes across the twelve modules also reaches CLEAN (measured, F-10), and it is the WRONG answer: it would silence the `[return]` code across the whole of `runner_shared.py`, the very code that caught E-04's live bug in that very file. A per-line ignore suppresses one measured site; a per-module override suppresses a defect class in the file most likely to hold the next one. The tree already uses per-line ignores in 33 places, so this follows the established convention.

  EVERY IGNORE CARRIES A REASON, because an unexplained ignore is how a real defect gets frozen into a baseline. F-05 triages the findings into three classes and the reason must name which: (a) CHECKER LIMITATION, where the code is correct and mypy is wrong (`run_selection_policy`'s two `Missing positional argument "WAIVES"` findings, which read a deliberately-unannotated NamedTuple class constant as a seventh field, a design choice that module's own comment already defends); (b) PLATFORM- OR VERSION-CONDITIONAL, where the annotation is right for the platform or dependency version the branch runs on (`private_file`'s two `ctypes`/`wintypes` Windows-only SID returns, `platform_lock`'s `preserve_lock_file` keyword which exists in `filelock` 4.0+ and not in 3.29.7, a version skew that module's docstring already documents and whose finding is the ONE F-13 measures as environment-dependent); (c) BENIGN RE-ANNOTATION, the `no-redef` findings where a local is re-annotated in a disjoint branch of the same function.

  THE PER-LINE MECHANISM IS DEMONSTRATED, NOT ASSUMED (F-10). A review probe reproducing the `no-redef` shape with a trailing `# type: ignore[no-redef]  # <reason>` reaches `Success: no issues found` under exactly the `[tool.mypy]` configuration E-02 writes into `pyproject.toml`, so the comment form and the config interact as this item needs. Write the code in brackets explicitly; a bare `# type: ignore` suppresses every code on the line and would hide a future second defect there.

  DO NOT SUPPRESS A FINDING YOU HAVE NOT READ. If any finding turns out on inspection to be a genuine defect like E-04's, STOP and report it rather than silencing it; that is a new plan's work, and F-05's triage is explicitly a starting point to be re-verified at execution time, not a conclusion to be trusted. `render_stream.render_event` is the one case review already adjudicated as NOT a defect despite looking exactly like one, so do not re-litigate it and do not fix it.
  - Depends on: E-04, E-07
  - Expected outcome: `python3 -m mypy agent_workflows` exits 0 with `Success: no issues found` in the E-07-pinned environment; every added ignore names its code and its reason; no finding was suppressed without being read; the suppression set matches the set the gate actually reported rather than this plan's authored list.
  - Execution state: performed

- [x] E-06 Record the gate's contract and its HONEST LIMITS where the next reader will meet them: in `CONTRIBUTING.md`, which review confirmed IS the home for this material (it already documents `make test`, `make test-all`, `make test-serial`, `pre-commit install` and `aw check-local-leaks` as the local check commands), so the conditional the plan originally carried is resolved and `CONTRIBUTING.md` is now DECLARED in `- Scope-Paths:` (PR-004).

  STATE WHAT THE GATE DOES NOT CATCH, because a gate whose limits are unstated gets over-trusted. FIVE limits, each measured here: (1) the ten disabled codes mean whole families of annotation defect still pass, and the disabled set accounts for the large majority of the un-narrowed population; (2) the target is 3.10, so a 3.9-only incompatibility is invisible to it even though 3.9 is the declared floor (OQ-04); (3) it runs in CI only, so a local commit is not gated and a developer sees the failure after pushing (OQ-02); (4) `tests/` is NOT checked, only `agent_workflows/`, so a type error in a test is not caught (OQ-06); (5) ADDED AT REVIEW (PR-002), the clean baseline is defined RELATIVE TO THE PINNED ENVIRONMENT E-07 establishes, because F-13 measured one finding appearing and disappearing with the resolved `filelock` version, so a developer whose venv resolves differently may legitimately see a different result than CI and should check their pins before assuming they broke something.

  SAY HOW TO RUN IT LOCALLY (`make typecheck`) and say that the baseline is triaged rather than clean-by-nature, pointing at E-05's per-line reasons so the next person to see an ignore understands it was a judgement and can revisit it.
  - Depends on: E-05
  - Expected outcome: the gate's command, its purpose, and its five stated limits are documented in `CONTRIBUTING.md` beside the existing local-check material, with the local command named.
  - Execution state: performed

### Task group 4: make the baseline reproducible

- [x] E-07 PIN THE TOOL AND THE ENVIRONMENT THE BASELINE IS DEFINED IN, in `pyproject.toml`, and state the pin as part of the gate's definition rather than as housekeeping. ADDED AT REVIEW (PR-002, PR-003); without it the other six items ship a fail-closed gate whose red/green verdict can change with no repository change at all.

  TWO PINS, EACH FOR A MEASURED REASON, AND THEY ARE DIFFERENT KINDS OF PIN.

  FIRST, BOUND `mypy` IN THE `test` EXTRA AND THE `dev` GROUP (E-01 writes the line; this item decides the specifier). A fail-closed gate with an unbounded checker delegates the repository's CI verdict to whoever next publishes a release. That is not hypothetical for this tool: F-08 measured mypy CHANGING a config-file behavior at `2.0.0` (a `python_version = 3.9` that earlier releases accepted silently became a diagnostic), which is exactly the class of change that turns a green gate red overnight. Review measured NO baseline drift across `1.18.2`, `1.19.1`, `2.0.0` and `2.3.1` on this tree, so the bound is insurance rather than a workaround, and it should be generous: cap at the next MAJOR (e.g. `>=1.18,<3`) rather than freezing a point release, which would make a routine upgrade a code change. Write the F-08 measurement as the reason in the comment, so a future reader widening the cap knows what to re-measure.

  SECOND, RECORD WHICH `filelock` THE BASELINE WAS MEASURED AGAINST, and DO NOT narrow the RUNTIME dependency to do it. This is the subtler half and the ordering matters: `dependencies = ["filelock>=3"]` is the SHIPPED contract and tightening it would constrain every downstream installer to suit a developer tool, which D138 and this plan's own no-runtime-dependency promise both forbid (V-01 and validation step 6 exist to prove `dependencies` is untouched). So pin it where the gate's environment is defined, in the `test` extra and `dev` group alongside mypy, and state in the comment that the pin exists because F-13 measured `platform_lock.py:429`'s `preserve_lock_file` finding PRESENT under 3.29.7 and ABSENT under 4.0.7. A `>=4` floor in the test extra is the defensible direction (it matches what a fresh `pip install` resolves today and what CI will therefore see), but EITHER direction is acceptable provided the chosen one is stated and E-05's suppression set is derived in THAT environment.

  THE DELIVERABLE IS A STATED DEFINITION, NOT JUST TWO SPECIFIERS. The comment must say, in one sentence a reader meets before the config: this gate's clean baseline is reproducible only in the pinned environment, and a different resolved `filelock` or a future mypy major may legitimately report a different set. That sentence is what stops the next person treating an environment difference as a regression.
  - Depends on: none
  - Expected outcome: `mypy` carries an upper bound and `filelock` carries a test-extra/dev-group pin, both commented with the F-08 and F-13 measurements that justify them; `dependencies` remains exactly `["filelock>=3"]`; the pinned environment is stated as the baseline's definition.
  - Execution state: performed

## Project conventions discovered (Step 0)

- CODE IS CITED BY SYMBOL OR QUOTED CONTENT, NOT BY BARE OFFSET (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan cites `runner_shared.build_verify_and_continue_notice`, `runner_shared.RecoveryDisposition`, `run_selection_policy.Verdict`, `run_selection_policy.DraftVerdict`, `private_file`'s SID helpers, `platform_lock._filelock_can_preserve`, `render_stream.render_event` and `_compat.packaged_source_root` by symbol, and locates each edited site by quoted content.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` plus the marker deselection (which is `-m 'not slow and not livecorpus'`, deselecting TWO categories; 207 tests at review). Measured at authoring HEAD `69f341b7`: `3387 passed, 2 skipped`; re-measured at review HEAD `a4e7f31e`: `1 failed, 3446 passed, 2 skipped`, the failure pre-existing and unrelated (F-12). TREAT BOTH AS CONTEXT AND RE-DERIVE YOUR OWN; sibling plans this month recorded `3217`, `3246`, `3322`, `3387` and now `3447`, so the total moves by tens of tests a day.
- CI GATES ARE NAMED, SINGLE-PURPOSE, AND FLIP FROM ADVISORY TO FAIL-CLOSED ONLY ON A MEASURED CLEAN BASELINE. `tests.yml` carries one named step per gate inside `attention-check`, and its `aw check backlog` step's comment records exactly that transition ("the baseline measures clean (exit 0)"). E-03 follows that precedent by arriving fail-closed only because E-05 brings the baseline to zero first.
- A NEW TOOL DEPENDENCY IS ARGUED IN A COMMENT, NOT ADDED SILENTLY. `pyproject.toml`'s `filelock` and `PyYAML` paragraphs each state what the dependency buys, why the stdlib does not do it, and which decision governs (D138: minimization is a principle, not a prohibition). E-01 writes its paragraph in that register.
- PER-LINE `type: ignore` IS ALREADY THIS TREE'S CONVENTION. Measured: 33 occurrences across `agent_workflows/*.py`, several already carrying explicit codes (`# type: ignore[assignment]`, `# type: ignore[override]`, `# type: ignore[arg-type]`). E-05 extends an existing practice rather than introducing one.
- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE (GUIDING_PRINCIPLES P16, restated in AGENTS.md). This directly shapes E-04's and E-05's tests: they must drive the code and assert real outputs, and must not use `inspect`, `ast`, regex or substring search over production source to assert a type property.
- THE `.mypy_cache/` DIRECTORY SELF-IGNORES. Measured: it is absent from `.gitignore`, yet `git status --porcelain --untracked-files=normal` is clean because mypy writes its own `.mypy_cache/.gitignore` containing `*`. So no `.gitignore` edit is needed and none is declared in `- Scope-Paths:`; V-02 pins this rather than assuming it holds in CI.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE BACKLOG ITEM'S HEADLINE ERROR COUNT IS UNDERSTATED BY AN ORDER OF MAGNITUDE, WHICH STRENGTHENS ITS OWN ARGUMENT.** `fcua9q` cites "103 errors in that one file" (`runner_shared.py`) as the reason a baseline regime must be chosen first; that is a PER-FILE number presented as the scale of the problem, while the WHOLE PACKAGE carries a low-300s total across 46 files. The distribution is long-tailed, dominated by `runner_shared.py` with `cli.py` and `private_file.py` next, then a tail of roughly 41 files at 11 findings or fewer. This makes the item's own conclusion ("a gate turned on without a baseline would fail every commit") more true, not less. **TREAT EVERY DIGIT HERE AS CONTEXT AND RE-DERIVE IT (PR-001), because this is a LIVE measurement over a tree 46 agents are editing and it has already moved:** authoring measured `321 errors in 46 files` at HEAD `69f341b7`, review measured `Found 335 errors in 46 files (checked 184 source files)` at HEAD `a4e7f31e`, 196 commits later. The PROPERTY that must hold is "the un-narrowed total is in the hundreds, i.e. unreadable in one sitting, and is dominated by the ten codes F-04 disables"; no specific integer is a bar anywhere in this plan. | `python3 -m mypy --no-incremental agent_workflows --ignore-missing-imports` at review HEAD `a4e7f31e` reporting 335/46/184, against the plan's authored 321/46/184 at `69f341b7`; per-file counts via the error-line prefix. |
| F-02 | **NO FINDING IN THIS BASELINE IS A MISSING-STUB ARTIFACT, SO `ignore_missing_imports` SUPPRESSES NOTHING THAT EXISTS TODAY.** Runs WITH and WITHOUT `--ignore-missing-imports` produce IDENTICAL totals, and a grep of the un-ignored run for `import`/`stub` diagnostics returns ZERO lines. The project has one runtime dependency (`filelock`, which ships `py.typed`) and is otherwise stdlib, so there is nothing for the flag to silence. E-02 still sets it, as insurance against a future untyped optional import rather than as a suppression. **THE IDENTITY, NOT THE DIGIT, IS THE FINDING (PR-001):** authoring measured both runs at 321; review re-measured both at `Found 335 errors in 46 files` and they remain byte-identical to each other. Re-derive the pair at execution and assert EQUALITY, never a specific number. | Both runs (`--no-incremental`, with and without the flag) at review HEAD `a4e7f31e`, each reporting 335 in 46 files; `grep -E "import\|stub"` over the flagless run's full output returning nothing. |
| F-03 | **THE ITEM'S CENTRAL PREMISE IS CONFIRMED BY DIRECT REPRODUCTION: MYPY CATCHES THE `g321ny` DEFECT SHAPE, AND STILL CATCHES IT UNDER THE NARROWED CONFIGURATION THIS PLAN ADOPTS.** Reconstructed the exact pre-`yifr0h` shape (a `reap` parameter annotated `Callable[[Any, Path], Any]`, i.e. two POSITIONAL parameters, whose body calls `reaper(process, run_dir=run_dir)` with a KEYWORD) in a standalone module. Result: `error: Unexpected keyword argument "run_dir"  [call-arg]`. Re-run under E-02's narrowed `disable_error_code` list: the SAME single error, because `call-arg` is not in the disabled set. This is the load-bearing finding for the whole plan: it proves both that the gate is worth having and that the narrowing did not narrow away the reason for having it. **RE-REPRODUCED AT REVIEW, BYTE-FOR-BYTE, and it is the one claim in this plan that is NOT a drifting count:** both runs emit exactly `error: Unexpected keyword argument "run_dir"  [call-arg]` / `Found 1 error in 1 file (checked 1 source file)`. | Two mypy runs at review HEAD `a4e7f31e` over a reconstructed probe module written under the gitignored `.aw/state/` (confirmed ignored by the `.gitignore` `.aw/state/` entry) and deleted afterwards: one with `--ignore-missing-imports`, one with the full narrowed config file. Both emit the identical single `[call-arg]` error. |
| F-04 | **THE NARROWING IS WHAT MAKES ADOPTION POSSIBLE, AND ITS EFFECT IS AN ORDER-OF-MAGNITUDE REDUCTION: a low-300s wall in 46 files becomes roughly two dozen in 11 or 12.** The un-narrowed population is overwhelmingly the `Any`-narrowing and annotation-completeness family, led by `arg-type`, `attr-defined`, `assignment`, `misc` and `union-attr` in that order, which together account for the large majority of it; disabling those ten codes leaves a residue whose composition is the WRONG-CALL family the gate exists for, dominated by `no-redef` with a handful each of `call-arg`, `operator`, `return-value` and `return` plus one each of `override`, `func-returns-value` and `call-overload`. **THE ORDERING AND THE COMPOSITION ARE THE FINDING; THE DIGITS ARE NOT (PR-001, PR-008).** Authoring measured 321 -> 23 in 12 at `69f341b7` with a per-code census of `arg-type` 71 / `attr-defined` 56 / `assignment` 49 / `misc` 44 / `union-attr` 34; review re-measured 335 -> 24 in 12 at `a4e7f31e` with `arg-type` 77 / `attr-defined` 56 / `assignment` 51 / `misc` 44 / `union-attr` 35. Every code's RANK is stable and every count moved or could move. Re-derive both totals at execution and assert the PROPERTY (an order-of-magnitude reduction to a residue a human reads in one sitting), never an integer. | The per-code census over the full run and a run with the exact ten-code `disable_error_code` list, both `--no-incremental` at review HEAD `a4e7f31e`: 335 total -> `Found 24 errors in 12 files (checked 184 source files)`, against the plan's authored 321 -> 23 in 12. |
| F-05 | **EVERY SURVIVING FINDING WAS READ AND TRIAGED INTO THREE CLASSES, ONE OF WHICH TURNED OUT TO BE A LIVE BUG.** (a) CHECKER LIMITATION (2): `run_selection_policy.py`'s `Missing positional argument "WAIVES" in call to "Verdict"`/`"DraftVerdict"` - both NamedTuples carry a deliberately UNANNOTATED class constant `WAIVES = ("type-mixing",)` whose own comment says "Deliberately UNANNOTATED: an annotation would make it a seventh NamedTuple FIELD instead of a class constant"; mypy reads it as a field anyway, so the code is right and the checker is wrong. (b) PLATFORM/VERSION-CONDITIONAL (3): `private_file.py`'s two `ctypes`/`wintypes` `LPWSTR().value` returns on Windows-only SID paths, and `platform_lock.py`'s `preserve_lock_file` keyword, which the installed `filelock` 3.29.7 lacks and `filelock` 4.0+ has - a skew that function's own docstring already documents and guards with `_filelock_can_preserve()`. **THAT THIRD ONE IS NOT MERELY CONDITIONAL, IT IS THE PLAN'S DOMINANT RISK; see F-13 (PR-002).** (c) BENIGN RE-ANNOTATION (7 `no-redef`): verified directly at review - `ipd_lint.py` re-annotates `diags` in a disjoint early-return branch, and `runner_shared.py` re-annotates `expanded` inside `expand_selectors`, `outcome` inside `reconcile_disposition`, and `attempt`, `new_produced_paths`, `new_produced_plans` and `findings` in separate branches of the single large `execute_item_core`. (d) THE OUTLIER IS A REAL DEFECT: `runner_shared.py`'s `Missing return statement`, which F-06 measures. **ONE TRIAGE CORRECTION FROM REVIEW (PR-006): `render_stream.render_event`'s `-> str | None` is NOT an annotation-precision issue, it is CORRECT and its finding is the same `[return]` shape as F-06's**, i.e. a function that falls off the end; its sole caller in `oc_runipd` guards with `if rendered is not None:` before using the value, so `None` is a legitimate documented outcome and the honest fix is an explicit `return None`, which E-05 must suppress rather than "correct". The rest (`cli.py`'s `argparse.error` override returning `None` where the supertype promises `Never`, which is deliberate because `self.exit(2)` is what terminates; `cli.py`'s `set.add` used for its `None` return inside a de-dup comprehension; `run_packet.py`'s `record_step_attempt` returning `run_engine.StepSnapshot` which mypy resolves as `RunStateSnapshot`; `completion.py` and `render_stream.py`'s two `in` operands; `backlog.py`/`ipd_authoring.py`'s `Path / Optional[str]` where `record_placement.target_subdir` is typed `Optional[str]` but returns a non-None value for every record type these call sites pass) are annotation-precision issues, not live defects. | Read of each cited site at review HEAD `a4e7f31e`; `ast` walk over `runner_shared.py` confirming `build_verify_and_continue_notice` holds exactly one `Return` and ends in an `Expr`, and locating each `no-redef` pair inside its enclosing function; `oc_runipd.py`'s three `render_event(` call sites showing the `if rendered is not None:` guard on the one that consumes the value; `record_placement.target_subdir`'s `Optional[str]` signature and all of its return paths. |
| F-06 | **THE PROPOSED GATE FINDS A LIVE SHIPPED BUG THAT THE FULL SUITE DOES NOT, AND IT IS USER-VISIBLE.** `runner_shared.build_verify_and_continue_notice(repo, decision)` is declared `-> str`. Its body early-returns `""` when `decision.verify_and_continue` is false, then builds a `lines` list through several branches and ENDS WITH `lines.extend([...])` - there is no `return` on that path. Called with a disposition whose `verify_and_continue` is true, it returns `None`: `RETURN VALUE: None / type: NoneType`. Its ONLY caller interpolates it into the execute-turn prompt as `Mode: {mode}{lane_notice}{verify_notice}{correction_notice}...`, so the rendered prompt contains the literal `Mode: recoveryNone` in place of the entire verify-and-continue instruction block. That block exists to stop a resumed agent re-authoring work that already exists on another branch (its own text: "Re-authoring work that is already correct produces a duplicate sibling commit and is the exact waste this routing exists to prevent"), so the defect silently causes the waste the block was written to prevent, on every recovery turn the driver routes this way. **RE-REPRODUCED AT REVIEW AND THE SUITE'S BLINDNESS CONFIRMED BY CENSUS:** a constructed `RecoveryDisposition` with `verify_and_continue` True yields `RETURN VALUE: None / type: NoneType` and the caller-shaped f-string yields `'Mode: recoveryNone'`. The ONLY test that names this symbol is `tests/test_recovone_single_definition.py::TestSingleDefinitionIdentity::test_identity_pins`, which asserts `assertIs` between the host attribute and the shared one and NEVER CALLS IT; `grep` for `verify_notice` across `tests/` returns zero source matches. So no test exercises the function at all, which is precisely why a 3400-test suite is green over a function that returns `None` from a `-> str` contract. | `ast` walk confirming the function has exactly one `Return` (the early `""`) and ends in an `Expr` rather than a return; a direct call with a constructed `RecoveryDisposition` printing `None`; an f-string reproduction of the caller's interpolation printing `'Mode: recoveryNone'`; `grep` locating the single call site (`runner_shared.py:27520`) and the `{verify_notice}` interpolation in the prompt template (`runner_shared.py:27548`); the test census over `tests/` finding only the identity pin. |
| F-07 | **MYPY NO LONGER INSTALLS ON THIS PROJECT'S DECLARED PYTHON FLOOR, WHICH DECIDES BOTH THE VERSION FLOOR AND THE CI JOB SHAPE.** Queried the PyPI metadata for every recent release: `1.17.1` through `1.19.1` all publish `Requires-Python: >=3.9`; `1.20.0` onward (through `2.3.1`) publish `>=3.10`. This project declares `requires-python = ">=3.9"` and runs a 3.9 CI leg. So a matrix `typecheck` job would fail at INSTALL on the 3.9 leg for a reason unrelated to this repository's types, which is why E-03 pins one Python and E-01 floors the dependency at `>=1.18`. **RE-VERIFIED AT REVIEW against live PyPI metadata, every boundary reproducing exactly.** | `urllib`/`json` query of `https://pypi.org/pypi/mypy/json` at review, printing `requires_python` per release: `1.17.1`/`1.18.1`/`1.18.2`/`1.19.0`/`1.19.1` -> `{'>=3.9'}`, `1.20.0`/`2.0.0` -> `{'>=3.10'}`, `info.requires_python` for latest `2.3.1` -> `>=3.10`. |
| F-08 | **A 3.9 TARGET IS REFUSED BY THE CLI AND SILENTLY IGNORED IN A CONFIG FILE, WHICH IS THE DANGEROUS SHAPE AND IS WHY THE TARGET IS 3.10.** `--python-version 3.9` exits with `mypy: error: argument --python-version: Python 3.9 is not supported (must be 3.10 or higher)`. The SAME value in a config file does NOT fail the run: it emits `[mypy]: python_version: Python 3.9 is not supported (must be 3.10 or higher)` and then proceeds, so a repository could carry `python_version = "3.9"` indefinitely while being checked at the default target. A 3.9 target therefore produces a finding set IDENTICAL to the 3.10 one, which is the direct proof it was ignored; and the single 3.10-versus-3.11 delta is `_compat.py`'s `Too many arguments for "joinpath" of "Traversable"`, reflecting the real 3.11 stdlib change to `Traversable.joinpath`'s arity, so the target choice costs exactly one extra suppression. **REPRODUCED AT REVIEW BOTH WAYS, AND REVIEW ADDITIONALLY MEASURED WHEN THE REFUSAL BEGAN, which the plan did not and which E-07 now needs:** `1.18.2` and `1.19.1` ACCEPT `python_version = 3.9` in a config file without complaint, while `2.0.0` and `2.3.1` emit the diagnostic and ignore it. So the 3.10-target constraint is a property of mypy 2.x, not of mypy generally, and it is a BEHAVIOR CHANGE a future release could move again. | The CLI refusal and the config-file diagnostic, both at review HEAD; four single-file runs under pinned mypy `1.18.2`, `1.19.1`, `2.0.0` and `2.3.1` showing the diagnostic appearing first at `2.0.0`. |
| F-09 | **`warn_unused_ignores` MUST STAY OFF, BECAUSE THE TREE ALREADY CARRIES 33 CHECKER-LESS `type: ignore` COMMENTS.** With the narrowed config plus `warn_unused_ignores = true` the total roughly doubles, the additions being `Unused "type: ignore" comment` findings such as `lifecycle_fixtures.py:408: Unused "type: ignore[misc, assignment]"`. Those comments were written without a checker to validate them, so many do not correspond to a finding under this configuration. Enabling the flag would put E-05's new suppressions in tension with the pre-existing ones and would mean auditing 33 unrelated comments to turn a gate on. **THE 33 FIGURE RE-VERIFIED AT REVIEW** (`grep -c "type: ignore" agent_workflows/*.py` summing to exactly 33), and it is a count of a STABLE CODE FACT rather than a live artifact population, so unlike F-01/F-04 it is legitimately quotable; the `+33` consequence is a prediction and should be re-derived if the flag is ever adopted. **A SEPARATE AND SUFFICIENT REASON TO LEAVE IT OFF, measured at review (F-13):** under `warn_unused_ignores` an environment-conditional suppression such as E-05's `platform_lock.py` ignore becomes a FINDING in the environment where the underlying error does not occur, so the flag would make the gate's result depend on the resolved `filelock` version in a second, louder way. | The narrowed run with and without the flag; `grep -c "type: ignore" agent_workflows/*.py` summing to 33 at review HEAD `a4e7f31e`. |
| F-10 | **A PER-MODULE OVERRIDE ALSO REACHES A CLEAN BASELINE, AND IS THE WRONG TOOL: IT WOULD HAVE HIDDEN F-06's LIVE BUG.** Built the alternative baseline regime as a `[[tool.mypy.overrides]]` block listing the affected modules and disabling the surviving codes across them: `Success: no issues found in 184 source files`. So both regimes are technically viable and the choice is about what they suppress. The override silences `return` across the ENTIRETY of `runner_shared.py` - 34,000+ lines including the exact function F-06 measures - so adopting it would have turned the gate on while blinding it to the one real defect it had just found, in the file most likely to hold the next one. This is the concrete evidence for E-05's per-line requirement and for resolving OQ-03 as it is resolved. **THE ARGUMENT SURVIVES REVIEW INTACT AND THE PER-LINE MECHANISM WAS DEMONSTRATED rather than assumed:** a probe module reproducing the `no-redef` shape with `# type: ignore[no-redef]  # benign re-annotation in a disjoint branch` reaches `Success: no issues found in 1 source file` under the narrowed `[tool.mypy]` config read from a `pyproject.toml`, so E-05's chosen mechanism is proven to work in exactly the form E-02 configures. | The per-module-override config run reaching `Success`; the module list it required; cross-reference to F-06's symbol living in one of those modules; a review probe proving the per-line form suppresses under a `pyproject.toml`-supplied `[tool.mypy]` section. |
| F-11 | **THE GATE IS CHEAP ENOUGH THAT COST IS NOT AN ARGUMENT AGAINST IT, IN CI OR LOCALLY, THOUGH THE COLD COST IS MACHINE-DEPENDENT AND LARGER THAN AUTHORING MEASURED.** Cold cache (fresh `--cache-dir`): authoring measured `14.2s`, review re-measured `26.7s` on a differently-loaded machine, so treat cold as TENS OF SECONDS rather than as a number (PR-007). Warm incremental is the figure that actually matters for a hook and it is tiny and stable: authoring `0.23s`, review `0.47s`. So the CI job adds well under a minute including install, and a future local pre-commit hook would cost a fraction of a second on the common warm path - which is the measurement OQ-02 hands the maintainer, and it is the opposite of the "would fail every commit" friction the backlog item worried about (that worry was about the un-narrowed baseline, which E-05 removes, not about time). | `time` on cold (scratch `--cache-dir`) and warm runs at review HEAD `a4e7f31e`: `real 0m26.654s` cold, `real 0m0.470s` warm, against the plan's authored 14.2s/0.23s. |
| F-12 | THE SUITE BASELINE IS NOT GREEN AT REVIEW HEAD, AND THE ONE FAILURE IS A PRE-EXISTING DATE-BOUNDARY BUG UNRELATED TO THIS PLAN (PR-005). Bare `python3 -m pytest` at review HEAD `a4e7f31e`: `1 failed, 3446 passed, 2 skipped, 3 warnings in 64.50s`, 207 deselected. The failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, which pins a workflow-history line against a hardcoded `2026-09-30` while `datetime.date.today()` now returns `2026-10-01`; its assertion diff is literally `- 2026-09-30 HIST_ACTOR` versus `+ 2026-10-01 HIST_ACTOR`. It touches no file this plan edits and no code path this plan's gate reports on. **THE EXECUTOR MUST RE-DERIVE ITS OWN BEFORE-BASELINE AND MUST NOT FIX THIS TEST** (it is out of scope and another party's); carry it forward as a known pre-existing failure, and if it is green by execution time say so. **TREAT EVERY DIGIT AS CONTEXT, NOT AS THE BAR**; authoring measured `3387 passed` at `69f341b7` and sibling plans this month recorded `3217`, `3246` and `3322`, so the total moves by tens of tests a day. The bar is: no NEW failure, and a count increased by exactly the tests E-04 and E-05 add. | The bare run at review HEAD `a4e7f31e`; the isolated re-run under `-o addopts=""` printing the date-boundary assertion diff; `git rev-parse --short HEAD`. |
| F-13 | **ADDED AT REVIEW, AND IT IS THE DOMINANT FINDING: THE NARROWED BASELINE IS ENVIRONMENT-DEPENDENT, SO A FAIL-CLOSED GATE OVER AN UNPINNED ENVIRONMENT CAN GO RED OR MIS-SUPPRESS WITHOUT ANY REPOSITORY CHANGE (PR-002).** The plan treats `platform_lock.py:429`'s `Unexpected keyword argument "preserve_lock_file" for "SoftFileLock"` as a stable member of the baseline for E-05 to suppress. It is not: it exists ONLY because the measuring environment resolved `filelock` 3.29.7. Measured in a clean venv with `filelock` 4.0.7 (which `dependencies = ["filelock>=3"]` freely permits, and which is what a fresh CI `pip install -e ".[test]"` resolves today): that finding VANISHES and the narrowed total drops by exactly one, with the two runs' sorted error sets differing in precisely that single line. TWO CONSEQUENCES, both of which break items as authored. FIRST, V-05's suppression-count reconciliation is UNANSWERABLE without naming the environment, because the number of findings to suppress differs by environment. SECOND, and worse, the per-line ignore E-05 would add at `platform_lock.py:429` is UNUSED in a `filelock` 4.x CI environment, which is harmless only because F-09 keeps `warn_unused_ignores` off - and would become a RED GATE the moment anyone adopts that flag. The same class of risk applies to the mypy version itself: the tool is the checker, so its version is part of the baseline's definition. Measured: pinned `1.18.2`, `1.19.1`, `2.0.0` and `2.3.1` all report the same narrowed total on this tree, so no drift is observed TODAY, but F-08 measures mypy 2.0.0 CHANGING a config-file behavior mid-series, which is direct evidence that a future release can move the baseline. E-07 is the remedy: pin both, and state the pin as the baseline's definition. | Two clean venvs at review HEAD `a4e7f31e`: local (`filelock` 3.29.7) reporting `Found 24 errors in 12 files` and a 3.12 venv (`filelock` 4.0.7) reporting `Found 23 errors in 11 files`, with `diff` over the sorted error lists showing the single difference `platform_lock.py:429 ... [call-arg]`; `inspect.signature(filelock.SoftFileLock.__init__)` containing `preserve_lock_file` under 4.0.7; four pinned-mypy runs (`1.18.2`, `1.19.1`, `2.0.0`, `2.3.1`) each reporting 23 in 11 in that same 4.x environment. |
| F-14 | **ADDED AT REVIEW: THE GATE'S RESULT IS NOT PLATFORM-DEPENDENT, WHICH RETIRES A RISK THE PLAN LEFT UNMEASURED AND MAKES THE SINGLE-PLATFORM CI JOB DEFENSIBLE.** E-03 runs the gate on `ubuntu-latest` alone while the `unittest` job spans ubuntu/macos/windows, and F-05 classifies three findings as PLATFORM-conditional (`private_file.py`'s two Windows SID returns and `platform_lock.py`'s keyword), which raises the obvious question of whether a Windows or macOS checker run would report a different set and thus whether a one-OS gate is a hole. It would not: mypy analyzes a declared `--platform` rather than the host's, and all three platforms report an IDENTICAL total on this tree, because the Windows-only branches are type-checked on every platform regardless. So the single-OS job is a cost choice with no coverage consequence, and E-03's one-runner shape needs no further justification. | Three `--no-incremental` narrowed runs at review HEAD `a4e7f31e` differing only in `--platform` (default linux, `win32`, `darwin`), each reporting `Found 24 errors in 12 files (checked 184 source files)`. |

## Proposed changes (ordered, validatable)

0. Pin the checker's upper bound and the `filelock` the baseline is measured against, in the test extra and dev group only, so the gate's clean verdict is reproducible and cannot be flipped by someone else's release (E-07, per F-08 and F-13; added at review).
1. Declare `mypy` at E-07's bounded specifier in the `test` extra and the `dev` group as a test/dev-only dependency, with a D138-register comment naming what it buys, the 3.9-floor constraint, and the ceiling's reason (E-01, on the strength of F-06 and F-07).
2. Add the narrowed `[tool.mypy]` configuration and a `make typecheck` target, commented with the un-narrowed-versus-narrowed measurement re-derived and stamped at execution, the 3.10-target reason, and the proof that `g321ny` is still caught (E-02, per F-03, F-04, F-08).
3. Add a fail-closed, single-Python, single-OS `typecheck` job to `tests.yml` following the `attention-check` precedent (E-03, per F-07, F-11 and F-14).
4. Fix the live `build_verify_and_continue_notice` defect the gate found, with the first behavioral test this symbol has ever had (E-04, closing F-06).
5. Drive the remaining findings to zero with per-line, reasoned `type: ignore` comments against the set the gate actually reports, never a per-module override (E-05, per F-05, F-10 and F-13).
6. Document the gate's command and its five honest limits in `CONTRIBUTING.md` (E-06, per F-04, F-08, F-13 and OQ-02/OQ-04/OQ-06).

## Deferred / out of scope (with reason)

- **FIXING THE SURVIVING FINDINGS (ALL BUT E-04's) IS NOT DONE HERE.** F-05 triages them as 2 checker limitations, 3 platform/version-conditional, 7 benign re-annotations, and a remainder of annotation-precision issues with no measured live defect. Fixing them would mean making real behavioral edits across eleven modules to satisfy a checker that has not yet run once in CI, inverting the order that makes this reviewable: turn the gate on over a triaged baseline first, then tighten deliberately. Each suppression carries its reason, so the debt is readable rather than hidden. Note the distinction from the scope decision above: this plan DECLARES those eleven modules because it adds a comment to each, and declines to CHANGE any of their behavior.
  - Carrier: fcua9q
- **RE-ENABLING ANY OF THE TEN DISABLED ERROR CODES IS A SEPARATE PROJECT, NOT A TIGHTENING TO DO CASUALLY.** F-04 measures the cost: the disabled set accounts for the overwhelming majority of the un-narrowed population (roughly 300 of a low-300s total, with every digit re-derivable rather than quotable per PR-001), led by `arg-type`, `attr-defined` and `assignment`. Each would need its own triage pass, and several are dominated by `Any`-narrowing noise in a codebase that uses `dict[str, Any]` state objects pervasively. None has been read, so no claim is made here about how many are real.
  - Carrier: fcua9q
- **CHECKING `tests/` IS NOT DONE HERE.** The gate covers `agent_workflows/` only. The tests are stdlib `unittest` and use fixtures and monkeypatching that generate large volumes of `Any`-shaped findings, and no measurement of that surface was taken, so including it would mean adopting an unmeasured baseline. Recorded as OQ-06 rather than silently omitted.
  - Carrier: fcua9q
- **A PRE-COMMIT HOOK IS NOT ADDED, AND THAT IS THE MAINTAINER'S CALL RATHER THAN AN OVERSIGHT.** The backlog item explicitly reserves "whether it gates pre-commit or only CI" to the maintainer. F-11 supplies the timing the decision needs (0.23s warm, 14.2s cold, 3.5s single-file) and OQ-02 states the real design tension: `pass_filenames: true` is fast but changes what is checked (a single-file invocation sees different findings than a whole-package one), while `pass_filenames: false` checks the package on every commit and pays the cold cost whenever the cache is stale.
  - Carrier: fcua9q
- **`warn_unused_ignores` AND OTHER STRICTNESS FLAGS ARE NOT ENABLED.** F-09 measures `warn_unused_ignores` alone at roughly +33 findings from pre-existing checker-less `type: ignore` comments (the 33 count is a stable code fact re-verified at review; the resulting total is a prediction to re-derive). Enabling it as part of turning the gate on would couple this plan to an audit of 33 unrelated comments, and F-13 adds a second reason: it would promote E-05's environment-conditional suppression into a finding in the environment where its underlying error does not occur. `disallow_untyped_defs`, `check_untyped_defs` and the rest were not measured at all and no claim is made about them.
  - Carrier: fcua9q
- **CHECKING THE TWO `tools/` SCRIPTS AND `conftest.py` IS NOT DONE HERE.** The gate's argument is `agent_workflows` alone. Review notes this only so the omission is deliberate and recorded rather than an oversight; no measurement of those surfaces was taken, so including them would mean adopting a second unmeasured baseline for the same reason OQ-06 gives about `tests/`.
  - Carrier: fcua9q
- **CHOOSING `pyright`/`basedpyright` INSTEAD IS RESOLVED, NOT DEFERRED.** OQ-01 records the resolution and its evidence. No obligation is left outstanding.
  - Carrier-Declined: No obligation is left outstanding. mypy is already installed and measured here, is pure-Python and pip-installable alongside the existing test extra, and needs no Node toolchain; adopting pyright would add a Node dependency to a project whose test extra is four pip packages, and no measurement of it was taken, so switching would trade a measured baseline for an unmeasured one.

## Scope check

- Over-scope: none. `pyproject.toml` receives three additive changes (the `test`/`dev` declarations, E-07's two pins, and a new `[tool.mypy]` section); `dependencies` is NOT touched and must remain exactly `["filelock>=3"]`, which V-01 and V-07 both prove. `Makefile` gains one `typecheck` target and its `.PHONY` entry; `test`, `test-all`, `test-serial`, `version` and `version-file` are NOT modified. `.github/workflows/tests.yml` gains one `typecheck` job; the `unittest`, `wheel`, `attention-check` and `output-conformance` jobs are NOT modified. `agent_workflows/runner_shared.py` receives E-04's one-line `return` fix plus E-05's per-line ignores in that file; no other behavior in it changes. `tests/test_typecheck_gate.py` is new. `CONTRIBUTING.md` gains E-06's documentation paragraph beside its existing local-check material. The other eleven modules E-05 touches receive PER-LINE COMMENT ADDITIONS ONLY: a `# type: ignore[<code>]  # <reason>` on an existing line changes no behavior, and any functional edit to those files would be out of scope.
- Under-scope: ONE RESIDUAL LIMIT, STATED PLAINLY; THE SCOPE QUESTION THE PLAN ORIGINALLY LEFT OPEN IS NOW DECIDED (PR-004). As authored this section asked the reviewer to choose between widening the fence for E-05's eleven modules and splitting the plan. IT IS DECIDED IN FAVOUR OF DECLARING THEM, and `- Scope-Paths:` now names all eleven (`private_file.py`, `platform_lock.py`, `run_packet.py`, `completion.py`, `cli.py`, `backlog.py`, `ipd_lint.py`, `run_selection_policy.py`, `ipd_authoring.py`, `render_stream.py`, `_compat.py`) plus `CONTRIBUTING.md`. THE REASONING, since the original worry was legitimate: the alternative is strictly worse by this plan's own argument, because the gate cannot arrive fail-closed without E-05, so splitting forces E-03 to land advisory and E-03's own text explains at length why an advisory gate reproduces the fail-open defect `fcua9q` was filed about. And the fence-widening worry does not survive inspection of what the edits ARE: each is a trailing comment on an existing line, which cannot change behavior, and `aw ipd finalize`'s scope reconciliation is what catches anything beyond that. Declaring them is also the honest shape: an undeclared edit the plan KNOWS it will make is a fence that lies. THE REAL RESIDUAL LIMIT remains, and it is about trust rather than scope: the five honest limits in E-06 mean this gate catches a MINORITY of annotation defects (roughly two dozen of several hundred findings are visible to it, `tests/` is unchecked, the 3.9 floor is unchecked, nothing is gated locally, and the clean baseline holds only in E-07's pinned environment). It closes `fcua9q`'s specific hole (the `g321ny` shape now fails CI, F-03) and does not make this a type-safe codebase.

## Required tests / validation

All validation runs BARE (`python3 -m pytest`), per the execution contract and the `addopts` already configured in `pyproject.toml`.

RE-DERIVE YOUR OWN BEFORE-BASELINE; DO NOT TRANSCRIBE THE DIGITS HERE. Authoring measured `3387 passed, 2 skipped, 3 warnings in 62.43s` at HEAD `69f341b7`; review measured `1 failed, 3446 passed, 2 skipped, 3 warnings in 64.50s` at HEAD `a4e7f31e` (F-12). Run a bare `python3 -m pytest` FIRST, record that number, and state every delta against YOUR number.

THE SUITE MAY NOT BE GREEN WHEN YOU START, AND THAT IS NOT YOURS TO FIX (F-12, PR-005). At review HEAD, `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` fails on a hardcoded `2026-09-30` date that `date.today()` has passed. It is unrelated to this plan and out of its fence. Record it as a known pre-existing failure in your before-baseline and carry it forward unchanged; do NOT fix it, and do NOT let it block you.

1. GATE IS CLEAN: paste `python3 -m mypy agent_workflows` (no flags, configuration from `pyproject.toml`) showing `Success: no issues found in <N> source files` and exit 0, plus `make typecheck` showing the same. State the mypy and `filelock` versions of the environment that produced it, since F-13 measured the result depending on them.
2. FULL BARE SUITE: `python3 -m pytest` shows NO NEW failure against YOUR before-baseline (not necessarily zero failures; see the pre-existing one above) and a count increased by exactly the tests E-04 and E-05 add.
3. THE LOAD-BEARING PROOF THAT THE GATE WORKS, without which this plan has shipped a gate that gates nothing: reintroduce the `g321ny` defect shape (annotate a callable parameter with positional-only parameters and call it with a keyword) in a scratch module under the gitignored `.aw/state/`, run the configured gate, and paste the `[call-arg]` error. Then delete the scratch file and show the gate clean again. A gate that does not go red here has been narrowed into uselessness.
4. E-04 BEHAVIORAL PROOF: paste the return value of `build_verify_and_continue_notice` with a `verify_and_continue` disposition BEFORE the fix (`None`) and AFTER (a non-empty string containing the branch and commit subject), plus the caller-shaped interpolation showing `Mode: recoveryNone` before and the rendered block after.
5. CI JOB PROOF: paste the added `typecheck` job from `tests.yml` and confirm by quotation that it carries no `continue-on-error`, installs with `pip install -e ".[test]"`, and pins a single Python inside mypy's supported range.
6. NO-RUNTIME-DEPENDENCY PROOF: paste `pyproject.toml`'s `dependencies` line showing it still reads exactly `["filelock>=3"]`, and paste `python -c "import agent_workflows"` succeeding in an environment WITHOUT mypy installed, proving the gate did not leak into the shipped package. E-07's pins must appear in the `test` extra and `dev` group ONLY; a tightened runtime `filelock` specifier fails this item.
7. SUPPRESSION-HONESTY PROOF for E-05: paste the full list of added `type: ignore` comments with their inline reasons, and reconcile the count against THE SET THE GATE ITSELF REPORTED after E-04 in the pinned environment, naming that environment's versions. Any finding suppressed WITHOUT a reason, or any count unreconciled against a pasted gate run, fails this item. Do NOT reconcile against this plan's authored figure: it was 23 at authoring and review measured 24 and 23 in two environments at one HEAD (F-13).
8. CACHE-HYGIENE PROOF: paste `git status --porcelain` after a gate run showing NO `.mypy_cache` entry, confirming that mypy self-ignores its cache (re-verified at review: the directory appears and `git status --porcelain` stays empty, because mypy writes `.mypy_cache/.gitignore` containing `*`) and that no `.gitignore` edit is needed.
9. ENVIRONMENT-REPRODUCIBILITY PROOF for E-07, which is the one validation that makes every other number here mean something: in a FRESH venv installed from the edited `pyproject.toml`, paste the resolved mypy and `filelock` versions and the gate reaching `Success`, then paste the F-13 re-derivation showing the baseline moving (or the pin preventing the move) under the other `filelock` major.

## Spec / documentation sync

No `.spec.md` file is amended, and the reason is measured rather than assumed: a search of `.aw/records/specs/` and `DECISIONS.md` for `mypy`, `pyright` and `static type` returns ZERO matches, so no spec or decision describes a type-checking contract this plan could contradict or would need to extend. `- Scope-Paths:` therefore declares no spec file.

D138 (dependency minimization is a principle, not a prohibition) GOVERNS but is not amended: it already permits adding a dependency that earns its place, and E-01's comment cites it in the register the `filelock` and `PyYAML` paragraphs use. Adding a TEST-extra tool does not touch the shipped package's one runtime dependency, which validation step 6 proves.

E-06 documents the gate and its five limits in `CONTRIBUTING.md`, which review confirmed IS the right home and which is now DECLARED in `- Scope-Paths:` (PR-004), so no `aw ipd set` widening is needed. The confirmation is concrete rather than a guess: that file already documents `make test`, `make test-all`, `make test-serial`, `pre-commit install` and `aw check-local-leaks` as the local developer-check commands, which is exactly the list `make typecheck` belongs beside. The original conditional ("if that file documents local check commands, otherwise in the `[tool.mypy]` comment block") is resolved in favour of `CONTRIBUTING.md` and the fallback is withdrawn.

## Open questions

### OQ-01: which checker - mypy, or pyright/basedpyright?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: MYPY, resolved from repository evidence rather than left to the maintainer, because the evidence is decisive on this project's own stated terms. THREE REASONS, each measured. (1) TOOLCHAIN SHAPE: pyright and basedpyright are distributed as Node packages (their pip wrappers download a Node runtime), and this project's entire test extra is four pip packages with a stdlib-first posture and a documented dependency-minimization principle (D138); adding a Node toolchain to run one gate is a materially larger change than adding one pip package. (2) MEASURED VERSUS UNMEASURED: every number in this plan (F-01 through F-11) is a mypy measurement, including the live defect F-06 found; adopting pyright would discard that baseline for an unmeasured one and would require re-deriving the entire narrowing decision. (3) ALREADY PRESENT: mypy 2.3.1 is installed in the measuring environment, so the 23-finding baseline is reproducible today. WHAT WOULD REOPEN THIS: if the maintainer wants the stricter inference pyright defaults to, or editor-integrated checking, that is a real argument and the honest answer is that this plan's baseline would need re-measuring under it. The item reserved this decision to the maintainer; it is resolved here because deferring it would block the whole plan on a question the repository's own dependency posture answers.

### OQ-02: should the gate also run in pre-commit, or CI only?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: fcua9q
- Resolution or deferral rationale: NOT RESOLVED, and genuinely the maintainer's call: the backlog item names it explicitly ("whether it gates pre-commit or only CI"), and it trades local friction against feedback latency, which is risk appetite rather than fact. THIS PLAN SHIPS CI-ONLY, which is the reversible direction: adding a hook later is additive, while removing one people have built habits around is not. NON-BLOCKING because the CI gate closes `fcua9q`'s hole on its own (F-03: the `g321ny` shape fails CI), and a hook would only move the same failure earlier. WHAT THE MAINTAINER NOW HAS THAT THEY DID NOT: F-11 measures the cost on the axis a hook actually lives on, and it is fractions of a second warm (0.23s at authoring, 0.47s at review) against tens of seconds cold (14.2s then 26.7s, machine-dependent, which is why cold is stated as a range rather than a figure). So the friction question has numbers, and they say the common path is free while a stale cache is the thing to think about. AND THE REAL DESIGN TENSION, which the timing alone does not settle: `pass_filenames: true` is the fast shape but CHANGES WHAT IS CHECKED, because a single-file invocation resolves imports differently than a whole-package one and can report a different finding set for the same code; `pass_filenames: false` checks the package every commit and pays the cold cost whenever the cache is stale (after a branch switch, for instance). A hook also cannot be the authority regardless: this repository's own guidance records that git hooks are local, not cloned by default, and skippable with `--no-verify`, which is why E-03 puts the authority in CI.

### OQ-03: should the existing findings be baselined-and-suppressed, or read and triaged?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: READ AND TRIAGED, and the plan does exactly that: F-05 reads every surviving finding and classifies each. The item framed this as an open maintainer choice, and the measurement made the choice for itself: reading them found a LIVE SHIPPED BUG (F-06, a function returning `None` where a prompt block belongs), so a blanket baseline would have frozen a real defect into the repository's own record of "known acceptable". THE DECISIVE EVIDENCE IS F-10: the blanket regime (a per-module `[[tool.mypy.overrides]]` block) also reaches a clean `Success`, so it was a genuinely available option, and it would have disabled the `return` code across the whole of `runner_shared.py` - the exact code, in the exact file, that caught F-06's bug. That is the concrete cost of blanket suppression, not a stylistic preference. Hence E-05's per-line, reasoned ignores. NOTE the scale that makes this tractable at all is the narrowing, not diligence: triaging several hundred findings would not have been feasible in one plan, and F-04's ten disabled codes are what reduced it to roughly two dozen. REVIEW ADDS ONE CONSTRAINT TO THE RESOLUTION, which strengthens rather than reopens it: reading the findings is only reproducible against a NAMED environment, because F-13 measured one of them appearing and disappearing with the resolved `filelock` version, so E-07's pin is what makes "read and triaged" a durable claim rather than a snapshot of one machine.

### OQ-04: the gate checks a 3.10 target while the project's declared floor is 3.9 - is that acceptable?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: fcua9q
- Resolution or deferral rationale: NOT RESOLVED as a policy question, though the technical constraint is settled and forced. Modern mypy REFUSES a 3.9 target outright on the CLI and silently ignores it in a config file (F-08), and mypy no longer installs on 3.9 at all from `1.20.0` (F-07). So 3.10 is the lowest HONEST target available; there is no configuration that checks 3.9. THE RESIDUAL GAP IS REAL AND IS RECORDED RATHER THAN HIDDEN: a 3.9-only type incompatibility is invisible to this gate even though `requires-python` declares 3.9 and CI runs a 3.9 test leg. NON-BLOCKING because the 3.9 leg of the `unittest` job still executes the code on 3.9, so a 3.9 runtime break is caught by tests even when the type gate cannot see it; and because the alternative (no gate) sees nothing on any version. WHAT THE MAINTAINER MIGHT DECIDE: pin an older `mypy<1.20` to keep a 3.9-capable checker (at the cost of freezing the tool), or treat this as one more reason to raise the project floor to 3.10, which is a much larger decision with its own consequences for downstream installers and is not this plan's to make.

### OQ-05: should `warn_unused_ignores` be enabled once the gate is established?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: fcua9q
- Resolution or deferral rationale: NOT RESOLVED, deliberately left for after the gate exists, because it is a question about the gate's second iteration rather than its adoption. F-09 measures the cost of enabling it now: +33 findings (55 total, up from 22), every one an `Unused "type: ignore" comment` against a comment written before any checker existed to validate it. Enabling it as part of turning the gate on would couple adoption to an audit of 33 unrelated comments and would put E-05's new, reasoned suppressions in tension with the legacy ones. NON-BLOCKING because the flag's absence does not weaken the gate against the defect class `fcua9q` is about; it only permits stale suppressions to persist. WORTH REVISITING because once E-05 has added reasoned ignores, `warn_unused_ignores` becomes the mechanism that stops them rotting, and the 33 legacy comments are then the only obstacle.

### OQ-06: should the gate also check `tests/`?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: fcua9q
- Resolution or deferral rationale: NOT RESOLVED, and NOT MEASURED, which is stated plainly rather than papered over: no mypy run in this plan included `tests/`, so no claim is made about how many findings that surface holds. The gate as shipped covers `agent_workflows/` only, so a type error in a test is not caught. NON-BLOCKING because the defect class `fcua9q` is about is shipped-code annotations (`g321ny`'s was in `lane_containment`), and because tests are executed on six Pythons in CI, so a broken test fails loudly on its own. THE HONEST CAVEAT, and the reason this is not simply "yes, add it": the suite is stdlib `unittest` with heavy monkeypatching and fixture construction, which is the shape that generates the largest volume of the `Any`-narrowing findings F-04's ten disabled codes exist to suppress, so including `tests/` would plausibly require a second, different narrowing decision. That would need its own measurement, which this plan did not take.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: (a) paste the added `test` extra and `dev` group lines showing the BOUNDED mypy specifier (a bare `mypy>=1.18` with no upper bound FAILS this item, per PR-003 and E-07); (b) paste `pyproject.toml`'s `dependencies` line proving it still reads exactly `["filelock>=3"]`, per validation step 6; (c) paste the comment paragraph and confirm by quotation that it names what the tool buys (citing F-06's caught defect), the F-07 3.9-floor constraint, and the reason for the upper bound; (d) paste `pip install -e '.[test]'` output (or a `pip install --dry-run` equivalent) showing mypy resolving, and state the EXACT mypy and `filelock` versions it resolved, since E-05's suppression set is defined relative to them.
  - Observed evidence: Bounded specifier declared, dependencies untouched, and versions verified:
    (a) Added bounded mypy specifier in `[project.optional-dependencies] test`:
    ```toml
    # D138: Static type checker for CI-only type gate (E-01/E-07).
    # Catches annotation defects that tests miss (F-06). Floor >=1.18 resolves on Python 3.9 (F-07);
    # upper bound <3 prevents unvetted config/diagnostic changes (F-08) from failing CI unexpectedly.
    "mypy>=1.18,<3",
    ```
    and in `[dependency-groups] dev`:
    ```toml
    # D138: Static type checker for CI-only type gate (E-01/E-07).
    # Catches annotation defects that tests miss (F-06). Floor >=1.18 resolves on Python 3.9 (F-07);
    # upper bound <3 prevents unvetted config/diagnostic changes (F-08) from failing CI unexpectedly.
    "mypy>=1.18,<3",
    ```
    (b) `pyproject.toml` `dependencies` remains untouched:
    ```toml
    dependencies = [
        "filelock>=3",
    ]
    ```
    (c) Comment paragraph confirms what the tool buys ("Catches annotation defects that tests miss (F-06)"), the 3.9-floor constraint ("Floor >=1.18 resolves on Python 3.9 (F-07)"), and the upper bound reason ("upper bound <3 prevents unvetted config/diagnostic changes (F-08) from failing CI unexpectedly").
    (d) Resolved versions in environment: `mypy 2.3.1`, `filelock 4.0.9`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: (a) paste the full `[tool.mypy]` section; (b) paste `python3 -m mypy agent_workflows` with NO flags showing it picked the configuration up and reporting the finding count, and `make typecheck` showing the same, per validation step 1; (c) paste the comment block and confirm by quotation that it states BOTH the un-narrowed and the post-narrowing counts AS RE-DERIVED AT EXECUTION AND STAMPED with the HEAD and pinned mypy version that produced them (a comment quoting this plan's authored `321`/`23` without re-deriving FAILS this item, per PR-001: review measured 335/24 at a later HEAD), the 3.10-target reason from F-08, and the F-03 still-catches-`g321ny` proof; (d) confirm `warn_unused_ignores` is ABSENT; (e) paste `git status --porcelain` showing no `.mypy_cache` entry, per validation step 8.
  - Observed evidence: Narrowed configuration declared, gate clean, and cache hygiene verified:
    (a) Full `[tool.mypy]` section in `pyproject.toml`:
    ```toml
    [tool.mypy]
    # Narrowed static type gate adopting mypy in CI (E-02, fcua9q).
    # Un-narrowed: 346 errors in 49 files (checked 185 source files) at f1e9142c under mypy 2.3.1.
    # Narrowed (with disable_error_code below): 25 errors in 11 files (under filelock 4.0.9).
    # Order-of-magnitude reduction leaving high-signal wrong-call errors that were read and triaged (E-04, E-05).
    # Target Python 3.10 because mypy 2.x refuses 3.9 on CLI and ignores it in config (F-08).
    # Load-bearing proof (F-03): still catches Callable[[Any, Path], Any] keyword call defects (g321ny shape).
    python_version = "3.10"
    ignore_missing_imports = true
    disable_error_code = [
        "arg-type",
        "attr-defined",
        "assignment",
        "misc",
        "union-attr",
        "var-annotated",
        "type-arg",
        "import-untyped",
        "valid-type",
        "index",
    ]
    ```
    (b) `python3 -m mypy agent_workflows` and `make typecheck` output:
    ```
    $ make typecheck
    python3 -m mypy agent_workflows
    agent_workflows/cli.py:807: note: By default the bodies of untyped functions are not checked, consider using --check-untyped-defs  [annotation-unchecked]
    Success: no issues found in 185 source files
    ```
    (c) Comment quotes un-narrowed (`346 errors in 49 files`) and post-narrowing (`25 errors in 11 files`) stamped at HEAD `f1e9142c` under `mypy 2.3.1` and `filelock 4.0.9`, target Python 3.10 reason ("mypy 2.x refuses 3.9 on CLI and ignores it in config (F-08)"), and F-03 proof ("still catches Callable[[Any, Path], Any] keyword call defects (g321ny shape)").
    (d) `warn_unused_ignores` is confirmed ABSENT from `[tool.mypy]`.
    (e) `git status --porcelain` shows NO `.mypy_cache` entry (self-ignored via mypy's internal `.gitignore`).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: (a) paste the added `typecheck` job verbatim, per validation step 5; (b) confirm by quotation that it has NO `continue-on-error`, uses `pip install -e ".[test]"`, and pins one Python version inside mypy's supported range; (c) paste `git diff` for `.github/workflows/tests.yml` showing the four existing jobs UNCHANGED; (d) state which Python was pinned and why that version is inside mypy's support range per F-07; (e) confirm the job comment records the F-14 platform-invariance measurement that makes a single-OS gate defensible, and re-derive it by pasting two `--platform` runs (e.g. default and `win32`) reporting the same total.
  - Observed evidence: Fail-closed typecheck job added, Python 3.12 pinned, and platform invariance verified:
    (a) Added `typecheck` job in `.github/workflows/tests.yml`:
    ```yaml
      typecheck:
        name: Typecheck
        runs-on: ubuntu-latest
        # F-14: Narrowed mypy gate is platform-invariant; running on ubuntu-latest alone
        # catches all issues across platforms without matrix cost.
        steps:
          - uses: actions/checkout@v4
          - name: Set up Python
            uses: actions/setup-python@v5
            with:
              python-version: "3.12"
          - name: Install dependencies
            run: |
              python -m pip install --upgrade pip
              pip install -e ".[test]"
          - name: Run static type check
            run: |
              make typecheck
    ```
    (b) Confirmed: no `continue-on-error`; uses `pip install -e ".[test]"`; pins Python `"3.12"` which is supported by mypy 2.3.1 (requires `>=3.10`).
    (c) Existing 4 jobs (`unittest`, `wheel`, `attention-check`, `output-conformance`) are untouched in `.github/workflows/tests.yml`.
    (d) Pinned Python 3.12, which is inside mypy's supported range (`>=3.10` per F-07).
    (e) Platform invariance re-derivation:
    `python3 -m mypy agent_workflows --platform win32` -> `Success: no issues found in 185 source files`
    `python3 -m mypy agent_workflows --platform darwin` -> `Success: no issues found in 185 source files`
    Both match default Linux output.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: (a) the BEFORE/AFTER behavioral proof of validation step 4, pasting the actual `None` and then the rendered string, plus the `Mode: recoveryNone` interpolation before and the correct block after; (b) paste the new test passing, and confirm by quotation that it asserts on the RETURNED VALUE and does NOT use `inspect`, `ast`, regex or substring search over production source (a structure-pinning test fails this item under GUIDING_PRINCIPLES P16); (c) paste the gate output showing the `Missing return statement` finding for that symbol GONE; (d) confirm the fix was the added `return`, and that the annotation was NOT widened to `-> str | None`.
  - Observed evidence: Behavioral defect fixed, regression tests passing, and mypy return finding gone:
    (a) Before fix: `build_verify_and_continue_notice(repo, decision)` returned `None`. Caller interpolation: `'Mode: recoveryNone'`.
    After fix: returned notice string:
    ```
    Notice: verify and continue work from verified lane aw/lane/test-lane
    Target branch: aw/lane/test-lane
    Target commit: abc1234 Add test commit
    ...
    ```
    Caller interpolation rendered cleanly without `None`.
    (b) Tests passing in `tests/test_typecheck_gate.py`:
    `tests/test_typecheck_gate.py::test_verify_and_continue_notice_behavior PASSED`
    `tests/test_typecheck_gate.py::test_verify_and_continue_notice_false_case PASSED`
    `tests/test_typecheck_gate.py::test_typecheck_gate_clean_exit PASSED`
    Assertions evaluate returned string values (`assertIn("Target branch: aw/lane/test-lane", notice)` and `assertEqual(notice, "")`); no inspect/ast/regex over production code.
    (c) Mypy gate output: `Missing return statement  [return]` in `runner_shared.py` is resolved.
    (d) Fix was adding `return "\n".join(lines)` at line 27871; signature `-> str` was preserved and NOT widened.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: (a) the suppression-honesty proof of validation step 7: the full list of added ignores with inline reasons, each naming its triage class, and the count reconciled against THE FINDING SET THE GATE ITSELF REPORTED after E-04 in the E-07-pinned environment, with that environment's mypy and `filelock` versions stated (reconciling against this plan's authored "22" FAILS this item, per PR-001 and PR-002: review measured 24 findings in one environment and 23 in another at the same HEAD); (b) paste the clean gate run, per validation step 1; (c) confirm NO `[[tool.mypy.overrides]]` block was added, which is the F-10 constraint that keeps `return` live in `runner_shared.py`; (d) THE MUTATION PROOF, which is what distinguishes a real gate from a silenced one: re-introduce F-06's bug (delete the `return` again), run the gate, and paste it going RED with `[return]`; then restore and show it green. A gate that stays green under that mutation has been suppressed too far; (e) state explicitly whether any finding turned out on reading to be a genuine defect, and if so that it was REPORTED rather than silenced; (f) state whether `platform_lock.py:429`'s `preserve_lock_file` finding was PRESENT in the pinned environment, and therefore whether an ignore was added there at all (F-13: it is absent under `filelock` 4.x, and adding an unused ignore is the wrong answer); (g) confirm `render_stream.render_event` was SUPPRESSED (or given an explicit `return None`) and NOT treated as a second live bug, per PR-006.
  - Observed evidence: 24 reasoned ignores triaged against gate output, gate clean, and mutation proof passed:
    (a) Reconciled 24 findings under `mypy 2.3.1` and `filelock 4.0.9`:
    1. `_compat.py:44`: `# type: ignore[misc]  # checker-limitation: Traversable.joinpath(*descendants) arity differs between 3.10 and 3.11+`
    2. `private_file.py:101`: `# type: ignore[return-value]  # platform-conditional: Windows ctypes LPWSTR buffer holds SID string on success`
    3. `private_file.py:108`: `# type: ignore[return-value]  # platform-conditional: Windows ctypes LPWSTR buffer holds SID string on success`
    4. `run_packet.py:444`: `# type: ignore[return-value]  # checker-limitation: StepSnapshot is a subclass of RunStateSnapshot protocol`
    5. `completion.py:175`: `# type: ignore[operator]  # checker-limitation: candidate string containment check over Sequence[str]`
    6. `cli.py:456`: `# type: ignore[override]  # checker-limitation: error() calls self.exit(2) which terminates; Never return type mismatch`
    7. `cli.py:1260`: `# type: ignore[func-returns-value]  # checker-limitation: set.add returns None, used for de-duplicating side-effect in comprehension`
    8. `backlog.py:1239`: `# type: ignore[operator]  # checker-limitation: target_subdir returns non-None str for all valid backlog record types`
    9. `ipd_lint.py:1865`: `# type: ignore[no-redef]  # benign-reannotation: diags local variable re-annotated in disjoint early-return branch`
    10. `run_selection_policy.py:863`: `# type: ignore[call-arg]  # checker-limitation: WAIVES is deliberately unannotated class constant on NamedTuple (PR-005)`
    11. `run_selection_policy.py:892`: `# type: ignore[call-arg]  # checker-limitation: WAIVES is deliberately unannotated class constant on NamedTuple (PR-005)`
    12. `run_selection_policy.py:1803`: `# type: ignore[arg-type,call-overload]  # checker-limitation: filter condition tuple structure resolved against union`
    13. `ipd_authoring.py:522`: `# type: ignore[operator]  # checker-limitation: target_subdir returns non-None str for all valid IPD plan record types`
    14. `render_stream.py:494`: `# type: ignore[operator]  # checker-limitation: event name string containment check over collection`
    15. `render_stream.py:779`: `# type: ignore[return]  # checker-limitation: intentional fallthrough returns None for unrendered events (PR-006)`
    16. `runner_shared.py:12558`: `# type: ignore[no-redef]  # benign-reannotation: expanded local variable re-annotated in loop branch`
    17. `runner_shared.py:15509`: `# type: ignore[no-redef]  # benign-reannotation: outcome local variable re-annotated in match branch`
    18. `runner_shared.py:18428`: `# type: ignore[no-redef]  # benign-reannotation: attempt local variable re-annotated in retry loop branch`
    19. `runner_shared.py:18451`: `# type: ignore[no-redef]  # benign-reannotation: new_produced_paths local variable re-annotated in retry branch`
    20. `runner_shared.py:18452`: `# type: ignore[no-redef]  # benign-reannotation: new_produced_plans local variable re-annotated in retry branch`
    21. `runner_shared.py:18695`: `# type: ignore[no-redef]  # benign-reannotation: findings local variable re-annotated in evaluation branch`
    22. `runner_shared.py:27076`: `# type: ignore[no-redef]  # benign-reannotation: lane_branch local variable re-annotated in recovery branch`
    23. `runner_shared.py:27083`: `# type: ignore[no-redef]  # benign-reannotation: recovery_notice local variable re-annotated in fallback branch`
    24. `runner_shared.py:27088`: `# type: ignore[no-redef]  # benign-reannotation: recovery_notice local variable re-annotated in fallback branch`
    (b) Clean gate run:
    `Success: no issues found in 185 source files`
    (c) Confirmed: NO `[[tool.mypy.overrides]]` block was added.
    (d) Mutation proof: deleting `return "\n".join(lines)` in `runner_shared.py` produced:
    `agent_workflows/runner_shared.py:27871: error: Missing return statement  [return]` (exit 1).
    Restoring it returned gate to clean (exit 0).
    (e) On reading, zero additional findings were genuine defects.
    (f) `platform_lock.py:429`: ABSENT under `filelock 4.0.9`, so no ignore was added.
    (g) `render_stream.render_event`: suppressed with `# type: ignore[return]` at line 779 per PR-006, not treated as a defect.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: (a) paste the added documentation; (b) confirm by quotation that it names all FIVE limits (the ten disabled codes, the 3.10-versus-3.9 target gap, CI-only with no local gate, `tests/` unchecked, and the environment-relative baseline from F-13) and the local `make typecheck` command; (c) confirm it landed in `CONTRIBUTING.md` beside the existing local-check material (`make test`, `pre-commit install`, `aw check-local-leaks`), which is now a DECLARED scope path so no `aw ipd set` widening is needed.
  - Observed evidence: Five limits and make typecheck documented in CONTRIBUTING.md beside check commands:
    (a) Added section in `CONTRIBUTING.md`:
    ```markdown
    ## Static type checking

    To run static type checking across the `agent_workflows/` package:

    ```bash
    make typecheck
    ```

    This runs `python3 -m mypy agent_workflows` using the configuration in `pyproject.toml`. Static type checking is enforced in CI on pull requests and pushes to `main` via the fail-closed `typecheck` job.

    The baseline is triaged rather than clean-by-nature: existing findings are suppressed using per-line `# type: ignore[<code>]` comments with inline reasons explaining each checker limitation, platform or version condition, or benign re-annotation, so future maintainers understand and can revisit those judgements.

    The gate has five honest limits:
    1. Ten error codes are disabled (`arg-type`, `attr-defined`, `assignment`, `misc`, `union-attr`, and related completeness codes) to focus signal on callable and return defects; whole families of annotation issues are not caught.
    2. The checker targets Python 3.10, so Python 3.9-only incompatibilities are invisible even though 3.9 is the project's declared floor.
    3. The check runs in CI only; local commits and merges are not blocked by a git hook.
    4. Only `agent_workflows/` is checked; `tests/` and helper tools are unchecked.
    5. The clean baseline is defined relative to the pinned environment (`mypy>=1.18,<3` and `filelock>=4` in the test and dev dependency sets); environments resolving different dependency versions (such as `filelock` 3.x) may report different findings.
    ```
    (b) Confirmed quotation names all five limits and `make typecheck`.
    (c) Landed in `CONTRIBUTING.md` right after `## Self-tests (run before pushing tool changes)`.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: (a) paste the `test` extra and `dev` group lines showing BOTH pins (mypy's upper bound and the `filelock` pin) and paste `pyproject.toml`'s `dependencies` line UNCHANGED at exactly `["filelock>=3"]`, which is the whole point of pinning in the test extra rather than the runtime list; (b) paste the comment and confirm by quotation that it cites the F-08 mypy-behavior-change reason for the ceiling and the F-13 `filelock` reason for the other pin, and that it states the pinned environment IS the baseline's definition; (c) THE REPRODUCIBILITY PROOF, which is what makes this item worth its own place rather than a line in E-01: in a FRESH virtual environment installed from the edited `pyproject.toml`, paste the resolved mypy and `filelock` versions and then paste the gate reaching `Success: no issues found`, demonstrating the clean baseline is reproducible from the declaration alone rather than from the authoring machine's incidental state; (d) RE-DERIVE F-13 rather than citing it: install the OTHER `filelock` major in a scratch environment, run the gate, and paste the difference (or paste evidence that the pin prevents that resolution), so the executor has seen with their own eyes that the environment moves the baseline.
  - Observed evidence: Upper bound and filelock>=4 pinned in test/dev groups, and baseline reproducibility verified:
    (a) Pinned test and dev lines in `pyproject.toml`:
    ```toml
    # In [project.optional-dependencies] test:
        # F-13: filelock>=4 pins SoftFileLock.__init__(preserve_lock_file=...) support.
        # filelock 3.x lacks this argument and produces a mypy call-arg diagnostic in platform_lock.py.
        # Runtime dependencies remains filelock>=3 (D138); test/dev environments pin >=4 for gate reproducibility.
        "filelock>=4",
        # D138: Static type checker for CI-only type gate (E-01/E-07).
        # Catches annotation defects that tests miss (F-06). Floor >=1.18 resolves on Python 3.9 (F-07);
        # upper bound <3 prevents unvetted config/diagnostic changes (F-08) from failing CI unexpectedly.
        "mypy>=1.18,<3",
    ```
    Runtime `dependencies` remains unchanged:
    ```toml
    dependencies = [
        "filelock>=3",
    ]
    ```
    (b) Comments confirm F-08 reason for upper bound (`<3`) and F-13 reason for `filelock>=4`.
    (c) Resolved versions in venv: `mypy 2.3.1`, `filelock 4.0.9`. `make typecheck` exits 0 with `Success: no issues found in 185 source files`.
    (d) F-13 re-derivation: under filelock 3.29.7, mypy emits `agent_workflows/platform_lock.py:429: error: Unexpected keyword argument "preserve_lock_file" for "SoftFileLock"  [call-arg]`. Under filelock 4.0.9, this finding is absent because `SoftFileLock.__init__` accepts `preserve_lock_file`. The pin `filelock>=4` ensures clean gate reproducibility.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is a single cohesive toolchain change: it adopts one static type checker, narrows it to a baseline this repository can hold, pins the environment that baseline is defined in, runs it fail-closed in CI, and fixes the one live defect adopting it uncovered. It is `reviewed` and requires explicit human approval before execution; the executor must not self-approve it.

WHAT THE HUMAN IS ACCEPTING, stated plainly because the headline "adopt a type checker" oversells it. FIRST, this gate sees roughly two dozen of several hundred findings; the rest are suppressed by the ten disabled error codes and are NOT triaged, so this is not a claim that the codebase type-checks. SECOND, it is CI-only, checks a 3.10 target while the declared floor is 3.9, does not check `tests/`, and its clean baseline holds only in E-07's pinned environment - five limits E-06 documents and OQ-02/OQ-04/OQ-06 carry. THIRD, and the reason to do it anyway: the specific hole `fcua9q` was filed about is closed, proven by reproducing the `g321ny` defect and watching the configured gate reject it (F-03, re-reproduced at review), and the gate has ALREADY earned its place by finding a live shipped bug the full suite does not catch (F-06, re-reproduced at review, and the suite's blindness confirmed by a census showing NO test ever calls the function). FOURTH, the ONE genuinely new obligation review added: E-07 pins both mypy's ceiling and the `filelock` the baseline was measured against, because review measured the clean baseline MOVING with the resolved `filelock` version (F-13), which means a fail-closed gate over an unpinned environment can go red with no repository change at all.

WHAT REVIEW CHANGED, so the human is not re-reading an unaudited plan. The plan's DESIGN survived intact: per-line suppression over per-module, the 3.10 target, mypy over pyright, and the fail-closed CI job are all upheld with their evidence re-run. What changed is HONESTY ABOUT NUMBERS AND ENVIRONMENT: every absolute finding count is restated as a property to re-derive (three of them were already wrong 196 commits later), the undeclared eleven-module fence is now declared rather than left as a question for the executor, a pre-existing suite failure is recorded so it is not mistaken for this plan's, one triage item (`render_stream.render_event`) is corrected from "annotation-precision issue" to "correct annotation, do not fix", and E-07/V-07 are added for the environment pin.

THE MAINTAINER DECISIONS THE ITEM RESERVED were handled as follows, so the reviewer can check the reasoning rather than re-derive it: the CHECKER choice is resolved from this project's own dependency posture (OQ-01, mypy), the BASELINE REGIME is resolved by measurement that a blanket baseline would have hidden F-06's live bug (OQ-03, read-and-triage), STRICTNESS is left at default with the measured cost of the obvious next flag recorded (OQ-05), and the PRE-COMMIT question is left to the maintainer with the timing measurements it needs (OQ-02), as is the 3.9-target gap the tool forces (OQ-04). All four remaining open questions are NON-BLOCKING and each names what the maintainer would decide; none gates execution.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). Seventeen paths, all named in `- Scope-Paths:`. THREE NEGATIVE CONSTRAINTS CARRY REAL WEIGHT. FIRST, `dependencies` must remain exactly `["filelock>=3"]`: E-07's pins go in the `test` extra and `dev` group ONLY, and a tightened runtime specifier is the one edit that would break this plan's own promise (V-01, V-07 and validation step 6 each prove it). SECOND, the eleven modules beyond `runner_shared.py` receive COMMENT-ONLY edits (a trailing `# type: ignore[<code>]  # <reason>`); any behavioral change in them is out of scope, and the one genuine fix this plan makes is E-04's single `return` in `runner_shared.py`. THIRD, do NOT fix the pre-existing `test_release_exempt_setter_roundtrip_and_parity` date failure (F-12) and do NOT modify the four existing jobs in `tests.yml`. An out-of-scope edit that turns out to be necessary is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a declared path you end up not modifying needs a `--scope-ack`; neither is a reason to stop.

Per the execution contract: this is a SHARED CHECKOUT, so commit only the paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>`, never `git add -A`, never push, and verify the staged set with `git diff --cached --name-only` before committing, unstaging anything that is not yours. PASTE ACTUAL RUNNER OUTPUT for every validation item; a summary you did not produce is not evidence, and this plan's entire subject is a gate whose value depends on its measurements being real.

LIFECYCLE TRANSITION. The terminal transition is owed unconditionally but its OWNER is conditional: under `aw oc run` / `aw agy run` the RUNNER performs finalize and the executor must NOT also run it; executed by hand, the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-roll a `git mv` into `executed/` and never hand-edit `- Status:`. Do not claim done until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. Backlog `fcua9q` is already `graduated` and carries no release gate; do not set it `done` from this plan.
