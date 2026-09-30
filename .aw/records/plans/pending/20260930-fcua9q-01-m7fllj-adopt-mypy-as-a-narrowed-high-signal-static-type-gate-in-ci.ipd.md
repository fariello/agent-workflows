# IPD: Adopt mypy as a narrowed, high-signal static type gate in CI, with a measured baseline the repository can actually hold

- Date: 2026-09-30
- Kind: child
- Concern: Backlog `fcua9q` reports that nothing in the toolchain catches an annotation defect, so the wrong `Callable[[Any, Path], Any]` annotation `yifr0h` fixed by hand (backlog `g321ny`) could have sat in shipped code indefinitely. CONFIRMED, and the gate's value is no longer hypothetical: re-measured in this lane, mypy catches that exact defect shape (`error: Unexpected keyword argument "run_dir"  [call-arg]`, F-03), AND the same narrowed configuration this plan adopts finds a LIVE SHIPPED BUG the suite does not (F-06): `runner_shared.build_verify_and_continue_notice` is declared `-> str` and returns `None` on its main path, so the string `None` is interpolated into a recovery turn's prompt in place of the whole verify-and-continue instruction block. THE ITEM'S HEADLINE NUMBER IS UNDERSTATED (F-01): the 103 errors it cites are one file's; the package total is 321 across 46 files.
- Scope: Adopt `mypy` as a CI-only, fail-closed type gate over `agent_workflows/` with a NARROWED error-code selection, plus the test-extra/dev-group declaration and a `make typecheck` target. The narrowing is the whole design and it is measured, not guessed: disabling the ten `Any`-narrowing noise codes takes the package from 321 errors in 46 files to 23 in 12 (F-04), which is a baseline a human can read in one sitting rather than a 321-error wall that would have to be blanket-suppressed. This plan does NOT fix the 23 findings (F-05 triages every one of them and E-05 suppresses them per-line with a cited reason), does NOT touch pre-commit (OQ-02 hands that to the maintainer with the timing measurement it needs), and does NOT adopt strictness beyond the default. THE ONE EXCEPTION IS DELIBERATE: F-06's live bug is FIXED here rather than suppressed, because suppressing a real defect to turn a gate on would be the exact dishonesty the gate exists to prevent.
- Scope-Paths: pyproject.toml, Makefile, .github/workflows/tests.yml, agent_workflows/runner_shared.py, tests/test_typecheck_gate.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: fcua9q
- Set: fcua9q
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: m7fllj

## Workflow history

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `fcua9q`. Every measurement taken fresh in this lane at HEAD `69f341b7`; none carried over from the item or from `yifr0h`. The item's headline error count is CORRECTED (F-01). The item's premise that a checker would have caught `g321ny` is CONFIRMED by direct reproduction (F-03). A LIVE SHIPPED BUG the proposed gate finds is recorded (F-06) and is fixed by E-04 rather than suppressed. The item's four reserved maintainer decisions are resolved from repository evidence where the evidence is decisive (OQ-01 checker choice, OQ-03 baseline regime) and handed to the maintainer where it is genuinely a risk-appetite call (OQ-02 pre-commit).
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give this repository a static type gate that would have caught `g321ny` and that is worth keeping: CI-only, fail-closed, narrowed to the error codes that indicate defects rather than `Any`-narrowing noise, and standing on a baseline of 23 findings that were individually READ and triaged rather than a 321-error wall silenced wholesale. After this plan a wrong annotation of the `g321ny` shape fails CI on every push and pull request, the one live defect the gate already found is fixed, and each remaining known finding carries a per-line suppression naming WHY it is not a defect, so the next reader inherits a triaged baseline instead of an unexplained wall.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: declare the tool and its configuration

- [ ] E-01 Declare `mypy` in `pyproject.toml`'s `[project.optional-dependencies] test` extra and in the `[dependency-groups] dev` group, as a TEST/DEV-ONLY dependency with a floor of `mypy>=1.18`, and write the comment paragraph that justifies it in the register the neighbouring `filelock` and `PyYAML` paragraphs already use.

  IT IS NOT A RUNTIME DEPENDENCY AND MUST NOT BECOME ONE. `dependencies` stays exactly `["filelock>=3"]`. D138 governs the register: dependency MINIMIZATION is the principle, not a prohibition, so the comment must say what the tool buys (a gate for a defect class the suite provably does not catch, F-06) rather than apologising for existing.

  THE FLOOR IS `>=1.18` FOR A MEASURED REASON, NOT A GUESS. mypy dropped Python 3.9 support at `1.20.0` (F-07: `1.19.1` publishes `Requires-Python: >=3.9`, `1.20.0` publishes `>=3.10`), and this project's floor is `requires-python = ">=3.9"` with a CI leg on 3.9. A floor of `>=1.18` therefore RESOLVES on the 3.9 leg, where a bare `mypy` would not. E-03 is what keeps the 3.9 leg from running it at all, and this floor is the belt to that braces.
  - Depends on: none
  - Expected outcome: `pip install -e '.[test]'` and `pip install --group dev` both install mypy; `dependencies` is unchanged at one entry; the declaration carries a comment naming the caught-defect justification and the 3.9 floor constraint.
  - Execution state: pending

- [ ] E-02 Add a `[tool.mypy]` section to `pyproject.toml` carrying the NARROWED configuration, and a `typecheck` target to the `Makefile` that runs it the one canonical way.

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

  `ignore_missing_imports = true` BECAUSE THE ALTERNATIVE BUYS NOTHING HERE: measured, the package total is 321 errors WITH it and 321 WITHOUT it (F-02), so no finding in this baseline is a missing-stub artifact and the flag is insurance against a future optional import rather than a suppression of anything present.

  THE TEN DISABLED CODES ARE THE ENTIRE POINT AND MUST BE COMMENTED AS SUCH. They are not a taste choice: enabling them yields 321 findings in 46 files, and the backlog item itself predicts the consequence ("a gate turned on without a baseline would fail every commit"). Disabling them yields 23 in 12 (F-04). The comment must state both numbers, state that the disabled set is the `Any`-narrowing and annotation-completeness family rather than the wrong-call family, and state that re-enabling any of them is a deliberate future project with its own baseline, not a tightening someone should do casually. CRITICALLY, it must record the falsifiable proof that the narrowing did not narrow away the point: the `g321ny` defect shape is still caught under exactly this configuration (F-03).

  DO NOT SET `warn_unused_ignores`. Measured: it ADDS 33 findings (55 total, up from 22 at the same target), because the tree already carries 33 `type: ignore` comments written against no checker and many are unused under this configuration (F-09). Turning it on would make E-05's per-line suppressions fight the pre-existing ones. Recorded in OQ-05 as a follow-on, not done here.

  THE `make typecheck` TARGET runs `python3 -m mypy agent_workflows` and nothing else; it must be added to `.PHONY` and must NOT be wired into `make test` (OQ-02 explains why the gate is CI-only in this plan).
  - Depends on: E-01
  - Expected outcome: `make typecheck` runs the configured gate; `python3 -m mypy agent_workflows` picks the same configuration up from `pyproject.toml` with no flags; the configuration carries the 321-versus-23 justification, the 3.10-target reason, and the still-catches-`g321ny` proof.
  - Execution state: pending

### Task group 2: run it in CI, on the legs that can actually run it

- [ ] E-03 Add a `typecheck` job to `.github/workflows/tests.yml` as a NAMED, FAIL-CLOSED step, modelled on the existing `attention-check` job's shape (single Python, `pip install -e`, one named step per gate, no `continue-on-error`).

  ONE PYTHON VERSION, NOT THE MATRIX, and the reason is E-02's constraint rather than thrift: mypy does not install on the 3.9 leg (F-07) and does not accept a 3.9 target anywhere, so a matrix job would fail on its first leg for a reason that has nothing to do with this repository's types. Pin the job to `"3.12"`, which is inside mypy's supported range and is not the newest release, so the gate does not break when a new Python ships before mypy supports it.

  IT MUST NOT BE ADVISORY. No `continue-on-error`. The whole defect in `fcua9q` is that the check FAILS OPEN today; an advisory job would reproduce that failure in a new place and let the next `g321ny` land green. This follows the precedent set in this same file, where `aw check backlog` was explicitly flipped from advisory to fail-closed once its baseline measured clean, and its comment records that transition.

  INSTALL THE PROJECT, DO NOT HAND-LIST THE TOOL. Use `pip install -e ".[test]"`, exactly as the `unittest` and `output-conformance` jobs do, so the environment follows `pyproject.toml` instead of drifting from it. That file's own comment history records this specific drift happening before (CI once ran with a declared dependency missing, producing 155 failures), and hand-listing mypy here would reintroduce the same class of hole.
  - Depends on: E-02
  - Expected outcome: `tests.yml` carries a `typecheck` job that installs the project and runs the gate as a fail-closed named step on one pinned Python; no existing job is modified.
  - Execution state: pending

### Task group 3: fix the one real defect the gate found, then triage the rest

- [ ] E-04 FIX the live defect at `runner_shared.build_verify_and_continue_notice`: the function is declared `-> str`, builds its `lines` list, and then FALLS OFF THE END without returning it, so it returns `None` whenever `decision.verify_and_continue` is true. Add the missing `return "\n".join(lines)` (matching the joining convention its sibling notice builders in this module use) and a regression test in `tests/test_typecheck_gate.py`.

  THIS IS A USER-VISIBLE DEFECT, NOT A TYPE NIT, which is why it is fixed and not suppressed. Measured directly (F-06): the only caller interpolates the result into the execute-turn prompt as `{verify_notice}`, so a recovery turn that the driver routed to VERIFY AND CONTINUE prior work receives the literal string `None` where the entire instruction block should be. The block's own purpose is to stop a resumed agent re-authoring work that already exists on another branch, so the failure mode is the duplicated-work waste the block was written to prevent, occurring silently.

  THE FIX IS THE RETURN, NOT A SIGNATURE CHANGE. Do NOT "fix" this by widening the annotation to `-> str | None`: the caller's f-string interpolation means `None` renders as `None`, so a widened annotation would make the checker agree with a broken program. The early `return ""` on the `not decision.verify_and_continue` path already establishes the empty string as this function's no-op value, so `str` is the correct contract and the body is what is wrong.

  THE REGRESSION TEST MUST ASSERT BEHAVIOR, NOT THE ANNOTATION. Construct a `RecoveryDisposition` with `verify_and_continue` true and assert the returned value is a non-empty `str` containing the branch name and the commit subject, and separately that the false case returns `""`. Do NOT assert the return type by reading the source or by `inspect`; per the repository's testing contract (GUIDING_PRINCIPLES P16) a test that reads production source to check a structural property has no business existing.
  - Depends on: none
  - Expected outcome: `build_verify_and_continue_notice` returns the rendered notice string; a test pins both the populated and the empty case by behavior; the `[return]` finding for that symbol disappears from the gate's output.
  - Execution state: pending

- [ ] E-05 Bring the baseline to ZERO by adding a per-line `# type: ignore[<code>]` to each remaining known finding, EACH WITH A SHORT INLINE REASON, and add a test that pins the gate's clean exit.

  PER-LINE, NEVER PER-MODULE. A `[[tool.mypy.overrides]]` block silencing these codes across the twelve modules also reaches CLEAN (measured, F-10), and it is the WRONG answer: it would silence the `[return]` code across the whole of `runner_shared.py`, the very code that caught E-04's live bug in that very file. A per-line ignore suppresses one measured site; a per-module override suppresses a defect class in the file most likely to hold the next one. The tree already uses per-line ignores in 33 places, so this follows the established convention.

  EVERY IGNORE CARRIES A REASON, because an unexplained ignore is how a real defect gets frozen into a baseline. F-05 triages all 23 findings into three classes and the reason must name which: (a) CHECKER LIMITATION, where the code is correct and mypy is wrong (`run_selection_policy`'s two `Missing positional argument "WAIVES"` findings, which read a deliberately-unannotated NamedTuple class constant as a seventh field, a design choice that module's own comment already defends); (b) PLATFORM-CONDITIONAL, where the annotation is right for the platform the branch runs on (`private_file`'s two `ctypes`/`wintypes` Windows-only SID returns, `platform_lock`'s `preserve_lock_file` keyword which exists in `filelock` 4.0+ and not in the installed 3.29.7, a version skew that module's docstring already documents); (c) BENIGN RE-ANNOTATION, the seven `no-redef` findings where a local is re-annotated in a disjoint branch of the same function.

  DO NOT SUPPRESS A FINDING YOU HAVE NOT READ. If any of the 23 turns out on inspection to be a genuine defect like E-04's, STOP and report it rather than silencing it; that is a new plan's work, and F-05's triage is explicitly a starting point to be re-verified at execution time, not a conclusion to be trusted.
  - Depends on: E-04
  - Expected outcome: `python3 -m mypy agent_workflows` exits 0 with `Success: no issues found`; every added ignore names its code and its reason; no finding was suppressed without being read.
  - Execution state: pending

- [ ] E-06 Record the gate's contract and its HONEST LIMITS where the next reader will meet them: in `CONTRIBUTING.md`'s developer-workflow material if it documents the local check commands, otherwise in the `[tool.mypy]` comment block itself.

  STATE WHAT THE GATE DOES NOT CATCH, because a gate whose limits are unstated gets over-trusted. Four limits, each measured here: (1) the ten disabled codes mean whole families of annotation defect still pass, and the disabled set is far larger than the enabled one; (2) the target is 3.10, so a 3.9-only incompatibility is invisible to it even though 3.9 is the declared floor (OQ-04); (3) it runs in CI only, so a local commit is not gated and a developer sees the failure after pushing (OQ-02); (4) `tests/` is NOT checked, only `agent_workflows/`, so a type error in a test is not caught (OQ-06).

  SAY HOW TO RUN IT LOCALLY (`make typecheck`) and say that the baseline is triaged rather than clean-by-nature, pointing at E-05's per-line reasons so the next person to see an ignore understands it was a judgement and can revisit it.
  - Depends on: E-05
  - Expected outcome: the gate's command, its purpose, and its four stated limits are documented where a contributor will find them, with the local command named.
  - Execution state: pending

## Project conventions discovered (Step 0)

- CODE IS CITED BY SYMBOL OR QUOTED CONTENT, NOT BY BARE OFFSET (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan cites `runner_shared.build_verify_and_continue_notice`, `runner_shared.RecoveryDisposition`, `run_selection_policy.Verdict`, `run_selection_policy.DraftVerdict`, `private_file`'s SID helpers, `platform_lock._filelock_can_preserve`, `render_stream.render_event` and `_compat.packaged_source_root` by symbol, and locates each edited site by quoted content.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` plus the marker deselection. Measured on this lane's clean tree at HEAD `69f341b7`: `3387 passed, 2 skipped, 3 warnings in 62.43s`, 207 deselected. TREAT THAT AS CONTEXT AND RE-DERIVE YOUR OWN; sibling plans this month recorded `3217`, `3246`, `3322` and `3387`, so the total moves by tens of tests a day.
- CI GATES ARE NAMED, SINGLE-PURPOSE, AND FLIP FROM ADVISORY TO FAIL-CLOSED ONLY ON A MEASURED CLEAN BASELINE. `tests.yml` carries one named step per gate inside `attention-check`, and its `aw check backlog` step's comment records exactly that transition ("the baseline measures clean (exit 0)"). E-03 follows that precedent by arriving fail-closed only because E-05 brings the baseline to zero first.
- A NEW TOOL DEPENDENCY IS ARGUED IN A COMMENT, NOT ADDED SILENTLY. `pyproject.toml`'s `filelock` and `PyYAML` paragraphs each state what the dependency buys, why the stdlib does not do it, and which decision governs (D138: minimization is a principle, not a prohibition). E-01 writes its paragraph in that register.
- PER-LINE `type: ignore` IS ALREADY THIS TREE'S CONVENTION. Measured: 33 occurrences across `agent_workflows/*.py`, several already carrying explicit codes (`# type: ignore[assignment]`, `# type: ignore[override]`, `# type: ignore[arg-type]`). E-05 extends an existing practice rather than introducing one.
- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE (GUIDING_PRINCIPLES P16, restated in AGENTS.md). This directly shapes E-04's and E-05's tests: they must drive the code and assert real outputs, and must not use `inspect`, `ast`, regex or substring search over production source to assert a type property.
- THE `.mypy_cache/` DIRECTORY SELF-IGNORES. Measured: it is absent from `.gitignore`, yet `git status --porcelain --untracked-files=normal` is clean because mypy writes its own `.mypy_cache/.gitignore` containing `*`. So no `.gitignore` edit is needed and none is declared in `- Scope-Paths:`; V-02 pins this rather than assuming it holds in CI.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE BACKLOG ITEM'S HEADLINE ERROR COUNT IS UNDERSTATED BY AN ORDER OF MAGNITUDE, WHICH STRENGTHENS ITS OWN ARGUMENT.** `fcua9q` cites "103 errors in that one file" (`runner_shared.py`) as the reason a baseline regime must be chosen first. Re-measured across the whole package: `321 errors in 46 files (checked 184 source files)`. The 103 figure reproduces EXACTLY for `runner_shared.py` alone, so the item's number is correct but is a per-file number presented as the scale of the problem. The per-file distribution is long-tailed: `runner_shared.py` 103, `cli.py` 30, `private_file.py` 29, `record_producers.py` 14, `research_archive.py` 12, then a tail of 41 files at 11 or fewer. This makes the item's own conclusion ("a gate turned on without a baseline would fail every commit") more true, not less. | `python3 -m mypy agent_workflows --ignore-missing-imports` (mypy 2.3.1) at HEAD `69f341b7`, full output plus a per-file count via the error-line prefix, and the single-file run the item describes. |
| F-02 | **NO FINDING IN THIS BASELINE IS A MISSING-STUB ARTIFACT, SO `ignore_missing_imports` SUPPRESSES NOTHING THAT EXISTS TODAY.** Run WITH `--ignore-missing-imports`: 321 errors in 46 files. Run WITHOUT it: `321 errors in 46 files`, byte-identical totals, and a grep of the un-ignored run for `import`/`stub` diagnostics returns ZERO lines. The project has one runtime dependency (`filelock`, which ships `py.typed`) and is otherwise stdlib, so there is nothing for the flag to silence. E-02 still sets it, as insurance against a future untyped optional import rather than as a suppression. | Both runs at HEAD `69f341b7`, and `grep -E "import\|stub"` over the flagless run's full output. |
| F-03 | **THE ITEM'S CENTRAL PREMISE IS CONFIRMED BY DIRECT REPRODUCTION: MYPY CATCHES THE `g321ny` DEFECT SHAPE, AND STILL CATCHES IT UNDER THE NARROWED CONFIGURATION THIS PLAN ADOPTS.** Reconstructed the exact pre-`yifr0h` shape (a `reap` parameter annotated `Callable[[Any, Path], Any]`, i.e. two POSITIONAL parameters, whose body calls `reaper(process, run_dir=run_dir)` with a KEYWORD) in a standalone module. Result: `error: Unexpected keyword argument "run_dir"  [call-arg]`. Re-run under E-02's narrowed `disable_error_code` list: the SAME single error, because `call-arg` is not in the disabled set. This is the load-bearing finding for the whole plan: it proves both that the gate is worth having and that the narrowing did not narrow away the reason for having it. | Two mypy runs over a reconstructed probe module written under the gitignored `.aw/state/` (confirmed ignored by the `.gitignore` `.aw/state/` entry) and deleted afterwards: one with `--ignore-missing-imports`, one with the full narrowed config file. |
| F-04 | **THE NARROWING IS WHAT MAKES ADOPTION POSSIBLE, AND ITS EFFECT IS MEASURED, NOT ESTIMATED: 321 IN 46 FILES BECOMES 23 IN 12.** Classified all 321 findings by error code: `arg-type` 71, `attr-defined` 56, `assignment` 49, `misc` 44, `union-attr` 34, `index` 14, `var-annotated` 13, `dict-item` 9, `no-redef` 7, `list-item` 5, `operator` 4, `has-type` 4, `return-value` 3, `call-arg` 3, `return` 2, and one each of `override`, `func-returns-value`, `call-overload`. Disabling the ten highest-volume `Any`-narrowing and annotation-completeness codes leaves `Found 23 errors in 12 files`, whose composition is the wrong-call family the gate exists for: `no-redef` 7, `call-arg` 4, `operator` 4, `return-value` 3, `return` 2, `call-overload` 1, `override` 1, `func-returns-value` 1. | The per-code census over the full run, then a run with the exact ten-code `disable_error_code` list in a config file, at HEAD `69f341b7`. |
| F-05 | **ALL 23 SURVIVING FINDINGS WERE READ AND TRIAGE INTO THREE CLASSES, ONE OF WHICH TURNED OUT TO BE A LIVE BUG.** (a) CHECKER LIMITATION (2): `run_selection_policy.py`'s `Missing positional argument "WAIVES" in call to "Verdict"`/`"DraftVerdict"` - both NamedTuples carry a deliberately UNANNOTATED class constant `WAIVES = ("type-mixing",)` whose own comment says "Deliberately UNANNOTATED: an annotation would make it a seventh NamedTuple FIELD instead of a class constant"; mypy reads it as a field anyway, so the code is right and the checker is wrong. (b) PLATFORM/VERSION-CONDITIONAL (3): `private_file.py`'s two `ctypes`/`wintypes` `LPWSTR().value` returns on Windows-only SID paths, and `platform_lock.py`'s `preserve_lock_file` keyword, which the installed `filelock` 3.29.7 lacks and `filelock` 4.0+ has - a skew that function's own docstring already documents and guards with `_filelock_can_preserve()`. (c) BENIGN RE-ANNOTATION (7 `no-redef`): verified two directly - `ipd_lint.py` re-annotates `diags` in a disjoint early-return branch, `runner_shared.py` re-annotates `expanded`, `new_produced_paths`, `new_produced_plans` and `findings` in separate branches of the same function. (d) THE OUTLIER IS A REAL DEFECT: `runner_shared.py`'s `Missing return statement`, which F-06 measures. The remaining findings (`render_stream.render_event`'s 11-return `-> str | None`, `cli.py`'s `argparse.error` override, `backlog.py`/`ipd_authoring.py`'s `Path / Optional[str]` where `record_placement.target_subdir` returns `Optional[str]` but returns a non-None value for every type these call sites pass) are annotation-precision issues, not live defects. | Read of each cited site; `ast`-based confirmation of the two `Missing return statement` functions' return structure; `inspect.signature(filelock.SoftFileLock.__init__)` showing no `preserve_lock_file` in 3.29.7; read of `record_placement.target_subdir`'s `Optional[str]` signature and all four of its return paths. |
| F-06 | **THE PROPOSED GATE FINDS A LIVE SHIPPED BUG THAT THE 3387-TEST SUITE DOES NOT, AND IT IS USER-VISIBLE.** `runner_shared.build_verify_and_continue_notice(repo, decision)` is declared `-> str`. Its body early-returns `""` when `decision.verify_and_continue` is false, then builds a `lines` list through several branches and ENDS WITH `lines.extend([...])` - there is no `return` on that path. Called with a disposition whose `verify_and_continue` is true, it returns `None`: `RETURN VALUE: None / type: NoneType`. Its ONLY caller interpolates it into the execute-turn prompt as `Mode: {mode}{lane_notice}{verify_notice}{correction_notice}...`, so the rendered prompt contains the literal `Mode: recoveryNone` in place of the entire verify-and-continue instruction block. That block exists to stop a resumed agent re-authoring work that already exists on another branch (its own text: "Re-authoring work that is already correct produces a duplicate sibling commit and is the exact waste this routing exists to prevent"), so the defect silently causes the waste the block was written to prevent, on every recovery turn the driver routes this way. | `ast` walk confirming the function has exactly one `Return` (the early `""`) and does not end in a return; a direct call with a constructed `RecoveryDisposition` printing `None`; an f-string reproduction of the caller's interpolation printing `'Mode: recoveryNone'`; `grep` locating the single call site and the `{verify_notice}` interpolation in the prompt template. |
| F-07 | **MYPY NO LONGER INSTALLS ON THIS PROJECT'S DECLARED PYTHON FLOOR, WHICH DECIDES BOTH THE VERSION FLOOR AND THE CI JOB SHAPE.** Queried the PyPI metadata for every recent release: `1.18.1`, `1.18.2`, `1.19.0`, `1.19.1` all publish `Requires-Python: >=3.9`; `1.20.0` onward (through `2.3.1`) publish `>=3.10`. This project declares `requires-python = ">=3.9"` and runs a 3.9 CI leg. So a matrix `typecheck` job would fail at INSTALL on the 3.9 leg for a reason unrelated to this repository's types, which is why E-03 pins one Python and E-01 floors the dependency at `>=1.18`. | `urllib`/`json` query of `https://pypi.org/pypi/mypy/json` printing the `requires_python` of each release's files; `importlib.metadata` for the installed 2.3.1 showing `Requires-Python: >=3.10`. |
| F-08 | **A 3.9 TARGET IS REFUSED BY THE CLI AND SILENTLY IGNORED IN A CONFIG FILE, WHICH IS THE DANGEROUS SHAPE AND IS WHY THE TARGET IS 3.10.** `--python-version 3.9` exits with `mypy: error: argument --python-version: Python 3.9 is not supported (must be 3.10 or higher)`. The SAME value in a config file does NOT fail the run: it emits `[mypy]: python_version: Python 3.9 is not supported (must be 3.10 or higher)` and then proceeds, so a repository could carry `python_version = "3.9"` indefinitely while being checked at the default target. Measured targets: `3.9` -> 23 findings (i.e. identical to 3.10, confirming it was ignored), `3.10` -> 23, `3.11` -> 22, `3.14` -> 22. The single 3.10-versus-3.11 delta is `_compat.py`'s `Too many arguments for "joinpath" of "Traversable"`, reflecting the real 3.11 stdlib change to `Traversable.joinpath`'s arity. | Four config-file runs differing only in `python_version`, each tail-printed; the CLI refusal; a `comm` diff of the sorted 3.9-target and default-target finding sets isolating the one `_compat.py` line. |
| F-09 | **`warn_unused_ignores` MUST STAY OFF, BECAUSE THE TREE ALREADY CARRIES 33 CHECKER-LESS `type: ignore` COMMENTS.** With the narrowed config plus `warn_unused_ignores = true`: `Found 55 errors in 23 files`, up from 22 at the same target, the 33 additions being `Unused "type: ignore" comment` findings such as `lifecycle_fixtures.py:408: Unused "type: ignore[misc, assignment]"`. Those comments were written without a checker to validate them, so many do not correspond to a finding under this configuration. Enabling the flag would put E-05's new suppressions in tension with the pre-existing ones and would mean auditing 33 unrelated comments to turn a gate on. | The narrowed run with and without the flag; `grep -c "type: ignore" agent_workflows/*.py` totalling 33. |
| F-10 | **A PER-MODULE OVERRIDE ALSO REACHES A CLEAN BASELINE, AND IS THE WRONG TOOL: IT WOULD HAVE HIDDEN F-06's LIVE BUG.** Built the alternative baseline regime as a `[[tool.mypy.overrides]]` block listing the twelve affected modules and disabling the eight surviving codes across them: `Success: no issues found in 184 source files`. So both regimes are technically viable and the choice is about what they suppress. The override silences `return` across the ENTIRETY of `runner_shared.py` - 34,000+ lines including the exact function F-06 measures - so adopting it would have turned the gate on while blinding it to the one real defect it had just found, in the file most likely to hold the next one. This is the concrete evidence for E-05's per-line requirement and for resolving OQ-03 as it is resolved. | The per-module-override config run reaching `Success`; the module list it required; cross-reference to F-06's symbol living in one of those modules. |
| F-11 | **THE GATE IS CHEAP ENOUGH THAT COST IS NOT AN ARGUMENT AGAINST IT, IN CI OR LOCALLY.** Cold cache (fresh `--cache-dir`): `14.2s` for 184 files. Warm incremental: `0.23s`, twice consecutively. Single file with a warm cache: `3.5s`. So the CI job adds well under a minute including install, and a future local pre-commit hook would cost a fraction of a second on the common warm path - which is the measurement OQ-02 hands the maintainer, and it is the opposite of the "would fail every commit" friction the backlog item worried about (that worry was about the 321-error baseline, which E-05 removes, not about time). | `time` on three runs at HEAD `69f341b7`: cold with a scratch cache dir, warm repeat, and a single-file invocation. |
| F-12 | THE BASELINE IS FULLY GREEN, so any failure after this plan is this plan's to explain. Bare `python3 -m pytest` on this lane at HEAD `69f341b7`: `3387 passed, 2 skipped, 3 warnings in 62.43s`, 207 deselected by the configured markers. **TREAT THE DIGITS AS CONTEXT, NOT AS THE BAR**; sibling plans recorded `3217`, `3246` and `3322` within this month. The bar is zero failures and a count increased by exactly the tests E-04 and E-05 add, against a baseline re-derived at execution time. | The bare run at that HEAD; `git rev-parse --short HEAD`. |

## Proposed changes (ordered, validatable)

1. Declare `mypy>=1.18` in the `test` extra and the `dev` group as a test/dev-only dependency, with a D138-register comment naming what it buys and the 3.9-floor constraint (E-01, on the strength of F-06 and F-07).
2. Add the narrowed `[tool.mypy]` configuration and a `make typecheck` target, commented with the 321-versus-23 measurement, the 3.10-target reason, and the proof that `g321ny` is still caught (E-02, per F-03, F-04, F-08).
3. Add a fail-closed, single-Python `typecheck` job to `tests.yml` following the `attention-check` precedent (E-03, per F-07 and F-11).
4. Fix the live `build_verify_and_continue_notice` defect the gate found, with a behavioral regression test (E-04, closing F-06).
5. Drive the remaining 22 findings to zero with per-line, reasoned `type: ignore` comments, never a per-module override (E-05, per F-05 and F-10).
6. Document the gate's command and its four honest limits (E-06, per F-04, F-08 and OQ-02/OQ-04/OQ-06).

## Deferred / out of scope (with reason)

- **FIXING THE OTHER 22 FINDINGS IS NOT DONE HERE.** F-05 triages them as 2 checker limitations, 3 platform/version-conditional, 7 benign re-annotations, and a remainder of annotation-precision issues with no measured live defect. Fixing them would mean editing eleven modules to satisfy a checker that has not yet run once in CI, inverting the order that makes this reviewable: turn the gate on over a triaged baseline first, then tighten deliberately. Each suppression carries its reason, so the debt is readable rather than hidden.
  - Carrier: fcua9q
- **RE-ENABLING ANY OF THE TEN DISABLED ERROR CODES IS A SEPARATE PROJECT, NOT A TIGHTENING TO DO CASUALLY.** F-04 measures the cost: the disabled set accounts for 298 of the 321 findings, led by `arg-type` (71), `attr-defined` (56) and `assignment` (49). Each would need its own triage pass, and several are dominated by `Any`-narrowing noise in a codebase that uses `dict[str, Any]` state objects pervasively. None has been read, so no claim is made here about how many are real.
  - Carrier: fcua9q
- **CHECKING `tests/` IS NOT DONE HERE.** The gate covers `agent_workflows/` only. The tests are stdlib `unittest` and use fixtures and monkeypatching that generate large volumes of `Any`-shaped findings, and no measurement of that surface was taken, so including it would mean adopting an unmeasured baseline. Recorded as OQ-06 rather than silently omitted.
  - Carrier: fcua9q
- **A PRE-COMMIT HOOK IS NOT ADDED, AND THAT IS THE MAINTAINER'S CALL RATHER THAN AN OVERSIGHT.** The backlog item explicitly reserves "whether it gates pre-commit or only CI" to the maintainer. F-11 supplies the timing the decision needs (0.23s warm, 14.2s cold, 3.5s single-file) and OQ-02 states the real design tension: `pass_filenames: true` is fast but changes what is checked (a single-file invocation sees different findings than a whole-package one), while `pass_filenames: false` checks the package on every commit and pays the cold cost whenever the cache is stale.
  - Carrier: fcua9q
- **`warn_unused_ignores` AND OTHER STRICTNESS FLAGS ARE NOT ENABLED.** F-09 measures `warn_unused_ignores` alone at +33 findings from pre-existing checker-less `type: ignore` comments. Enabling it as part of turning the gate on would couple this plan to an audit of 33 unrelated comments. `disallow_untyped_defs`, `check_untyped_defs` and the rest were not measured at all and no claim is made about them.
  - Carrier: fcua9q
- **CHOOSING `pyright`/`basedpyright` INSTEAD IS RESOLVED, NOT DEFERRED.** OQ-01 records the resolution and its evidence. No obligation is left outstanding.
  - Carrier-Declined: No obligation is left outstanding. mypy is already installed and measured here, is pure-Python and pip-installable alongside the existing test extra, and needs no Node toolchain; adopting pyright would add a Node dependency to a project whose test extra is four pip packages, and no measurement of it was taken, so switching would trade a measured baseline for an unmeasured one.

## Scope check

- Over-scope: none. `pyproject.toml` receives two additive changes (the `test`/`dev` declarations and a new `[tool.mypy]` section); `dependencies` is NOT touched and must remain exactly `["filelock>=3"]`. `Makefile` gains one `typecheck` target and its `.PHONY` entry; `test`, `test-all`, `test-serial`, `version` and `version-file` are NOT modified. `.github/workflows/tests.yml` gains one `typecheck` job; the `unittest`, `wheel`, `attention-check` and `output-conformance` jobs are NOT modified. `agent_workflows/runner_shared.py` receives E-04's one-line `return` fix plus E-05's per-line ignores in that file; no other behavior in it changes. `tests/test_typecheck_gate.py` is new. E-05 also adds per-line ignores to the other eleven modules F-05 names - THESE ARE NOT IN `- Scope-Paths:` and this is deliberate: see under-scope.
- Under-scope: TWO THINGS A REVIEWER MUST DECIDE ON. FIRST, E-05's per-line ignores touch eleven modules beyond `runner_shared.py` (`private_file.py`, `platform_lock.py`, `run_packet.py`, `completion.py`, `cli.py`, `backlog.py`, `ipd_lint.py`, `run_selection_policy.py`, `ipd_authoring.py`, `render_stream.py`, `_compat.py`), and `- Scope-Paths:` deliberately does NOT declare them, because declaring eleven core modules as in-scope for a toolchain plan would license a far wider diff than this plan intends. The executor must either (a) add each file to `- Scope-Paths:` via `aw ipd set` before committing, naming it in the workflow history, or (b) if the maintainer prefers a tighter fence, stop after E-04 and carry E-05 in a follow-on plan. THE GATE CANNOT ARRIVE FAIL-CLOSED WITHOUT E-05, so option (b) means E-03 must land advisory and be flipped later, which contradicts this plan's own argument in E-03; raise it rather than choosing silently. SECOND, the four honest limits in E-06 mean this gate catches a minority of annotation defects: 23 of 321 findings are visible to it, `tests/` is unchecked, the 3.9 floor is unchecked, and nothing is gated locally. It closes `fcua9q`'s specific hole (the `g321ny` shape now fails CI, F-03) and does not make this a type-safe codebase.

## Required tests / validation

All validation runs BARE (`python3 -m pytest`), per the execution contract and the `addopts` already configured in `pyproject.toml`.

RE-DERIVE YOUR OWN BEFORE-BASELINE; DO NOT TRANSCRIBE THE DIGITS HERE. Authoring measured `3387 passed, 2 skipped, 3 warnings in 62.43s` at HEAD `69f341b7` (F-12). Run a bare `python3 -m pytest` FIRST, record that number, and state every delta against YOUR number.

1. GATE IS CLEAN: paste `python3 -m mypy agent_workflows` (no flags, configuration from `pyproject.toml`) showing `Success: no issues found in <N> source files` and exit 0, plus `make typecheck` showing the same.
2. FULL BARE SUITE: `python3 -m pytest` passes with ZERO failures and a count increased over YOUR baseline by exactly the tests E-04 and E-05 add.
3. THE LOAD-BEARING PROOF THAT THE GATE WORKS, without which this plan has shipped a gate that gates nothing: reintroduce the `g321ny` defect shape (annotate a callable parameter with positional-only parameters and call it with a keyword) in a scratch module under the gitignored `.aw/state/`, run the configured gate, and paste the `[call-arg]` error. Then delete the scratch file and show the gate clean again. A gate that does not go red here has been narrowed into uselessness.
4. E-04 BEHAVIORAL PROOF: paste the return value of `build_verify_and_continue_notice` with a `verify_and_continue` disposition BEFORE the fix (`None`) and AFTER (a non-empty string containing the branch and commit subject), plus the caller-shaped interpolation showing `Mode: recoveryNone` before and the rendered block after.
5. CI JOB PROOF: paste the added `typecheck` job from `tests.yml` and confirm by quotation that it carries no `continue-on-error`, installs with `pip install -e ".[test]"`, and pins a single Python inside mypy's supported range.
6. NO-RUNTIME-DEPENDENCY PROOF: paste `pyproject.toml`'s `dependencies` line showing it still reads exactly `["filelock>=3"]`, and paste `python -c "import agent_workflows"` succeeding in an environment WITHOUT mypy installed, proving the gate did not leak into the shipped package.
7. SUPPRESSION-HONESTY PROOF for E-05: paste the full list of added `type: ignore` comments with their inline reasons, and confirm the count equals the 22 findings remaining after E-04. Any finding suppressed WITHOUT a reason, or any count mismatch, fails this item.
8. CACHE-HYGIENE PROOF: paste `git status --porcelain` after a gate run showing NO `.mypy_cache` entry, confirming F-11's observation that mypy self-ignores its cache and that no `.gitignore` edit is needed.

## Spec / documentation sync

No `.spec.md` file is amended, and the reason is measured rather than assumed: a search of `.aw/records/specs/` and `DECISIONS.md` for `mypy`, `pyright` and `static type` returns ZERO matches, so no spec or decision describes a type-checking contract this plan could contradict or would need to extend. `- Scope-Paths:` therefore declares no spec file.

D138 (dependency minimization is a principle, not a prohibition) GOVERNS but is not amended: it already permits adding a dependency that earns its place, and E-01's comment cites it in the register the `filelock` and `PyYAML` paragraphs use. Adding a TEST-extra tool does not touch the shipped package's one runtime dependency, which validation step 6 proves.

E-06 documents the gate and its four limits in `CONTRIBUTING.md` if that file documents local check commands, otherwise in the `[tool.mypy]` comment block. `CONTRIBUTING.md` is NOT in `- Scope-Paths:`; if the executor determines it is the right home, add it via `aw ipd set` and record it in the workflow history rather than committing an undeclared path.

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
- Resolution or deferral rationale: NOT RESOLVED, and genuinely the maintainer's call: the backlog item names it explicitly ("whether it gates pre-commit or only CI"), and it trades local friction against feedback latency, which is risk appetite rather than fact. THIS PLAN SHIPS CI-ONLY, which is the reversible direction: adding a hook later is additive, while removing one people have built habits around is not. NON-BLOCKING because the CI gate closes `fcua9q`'s hole on its own (F-03: the `g321ny` shape fails CI), and a hook would only move the same failure earlier. WHAT THE MAINTAINER NOW HAS THAT THEY DID NOT: F-11 measures the cost (0.23s warm whole-package, 14.2s cold, 3.5s single-file), so the friction question has numbers. AND THE REAL DESIGN TENSION, which the timing alone does not settle: `pass_filenames: true` is the fast shape but CHANGES WHAT IS CHECKED, because a single-file invocation resolves imports differently than a whole-package one and can report a different finding set for the same code; `pass_filenames: false` checks the package every commit and pays the cold cost whenever the cache is stale (after a branch switch, for instance). A hook also cannot be the authority regardless: this repository's own guidance records that git hooks are local, not cloned by default, and skippable with `--no-verify`, which is why E-03 puts the authority in CI.

### OQ-03: should the existing findings be baselined-and-suppressed, or read and triaged?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: READ AND TRIAGED, and the plan does exactly that: F-05 reads all 23 surviving findings and classifies each. The item framed this as an open maintainer choice, and the measurement made the choice for itself: reading them found a LIVE SHIPPED BUG (F-06, a function returning `None` where a prompt block belongs), so a blanket baseline would have frozen a real defect into the repository's own record of "known acceptable". THE DECISIVE EVIDENCE IS F-10: the blanket regime (a per-module `[[tool.mypy.overrides]]` block) also reaches a clean `Success`, so it was a genuinely available option, and it would have disabled the `return` code across the whole of `runner_shared.py` - the exact code, in the exact file, that caught F-06's bug. That is the concrete cost of blanket suppression, not a stylistic preference. Hence E-05's per-line, reasoned ignores. NOTE the scale that makes this tractable at all is the narrowing, not diligence: triaging 321 findings would not have been feasible in one plan, and F-04's ten disabled codes are what reduced it to 23.

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

- [ ] V-01 validates E-01
  - Required evidence: (a) paste the added `test` extra and `dev` group lines showing `mypy>=1.18` in both; (b) paste `pyproject.toml`'s `dependencies` line proving it still reads exactly `["filelock>=3"]`, per validation step 6; (c) paste the comment paragraph and confirm by quotation that it names what the tool buys (citing F-06's caught defect) and the F-07 3.9-floor constraint, in the D138 register; (d) paste `pip install -e '.[test]'` output (or a `pip install --dry-run` equivalent) showing mypy resolving.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: (a) paste the full `[tool.mypy]` section; (b) paste `python3 -m mypy agent_workflows` with NO flags showing it picked the configuration up and reporting the finding count, and `make typecheck` showing the same, per validation step 1; (c) paste the comment block and confirm by quotation that it states BOTH the 321-in-46 and the post-narrowing counts, the 3.10-target reason from F-08, and the F-03 still-catches-`g321ny` proof; (d) confirm `warn_unused_ignores` is ABSENT; (e) paste `git status --porcelain` showing no `.mypy_cache` entry, per validation step 8.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: (a) paste the added `typecheck` job verbatim, per validation step 5; (b) confirm by quotation that it has NO `continue-on-error`, uses `pip install -e ".[test]"`, and pins one Python version inside mypy's supported range; (c) paste `git diff` for `.github/workflows/tests.yml` showing the four existing jobs UNCHANGED; (d) state which Python was pinned and why that version is inside mypy's support range per F-07.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: (a) the BEFORE/AFTER behavioral proof of validation step 4, pasting the actual `None` and then the rendered string, plus the `Mode: recoveryNone` interpolation before and the correct block after; (b) paste the new test passing, and confirm by quotation that it asserts on the RETURNED VALUE and does NOT use `inspect`, `ast`, regex or substring search over production source (a structure-pinning test fails this item under GUIDING_PRINCIPLES P16); (c) paste the gate output showing the `Missing return statement` finding for that symbol GONE; (d) confirm the fix was the added `return`, and that the annotation was NOT widened to `-> str | None`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: (a) the suppression-honesty proof of validation step 7: the full list of added ignores with inline reasons, and the count reconciled against the 22 post-E-04 findings; (b) paste the clean gate run, per validation step 1; (c) confirm NO `[[tool.mypy.overrides]]` block was added, which is the F-10 constraint that keeps `return` live in `runner_shared.py`; (d) THE MUTATION PROOF, which is what distinguishes a real gate from a silenced one: re-introduce F-06's bug (delete the `return` again), run the gate, and paste it going RED with `[return]`; then restore and show it green. A gate that stays green under that mutation has been suppressed too far; (e) state explicitly whether any of the 22 turned out on reading to be a genuine defect, and if so that it was REPORTED rather than silenced.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: (a) paste the added documentation; (b) confirm by quotation that it names all FOUR limits (the ten disabled codes, the 3.10-versus-3.9 target gap, CI-only with no local gate, and `tests/` unchecked) and the local `make typecheck` command; (c) state which file it landed in, and if `CONTRIBUTING.md`, paste the `aw ipd set` call that added it to `- Scope-Paths:` before it was committed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is a single cohesive toolchain change: it adopts one static type checker, narrows it to a baseline this repository can hold, runs it fail-closed in CI, and fixes the one live defect adopting it uncovered. It is `to-review` and requires `/plan-review` and then explicit human approval before execution; the executor must not self-approve it.

WHAT THE HUMAN IS ACCEPTING, stated plainly because the headline "adopt a type checker" oversells it. FIRST, this gate sees 23 of 321 findings; the other 298 are suppressed by the ten disabled error codes and are NOT triaged, so this is not a claim that the codebase type-checks. SECOND, it is CI-only, checks a 3.10 target while the declared floor is 3.9, and does not check `tests/` - four limits E-06 documents and OQ-02/OQ-04/OQ-06 carry. THIRD, and the reason to do it anyway: the specific hole `fcua9q` was filed about is closed, proven by reproducing the `g321ny` defect and watching the configured gate reject it (F-03), and the gate has ALREADY earned its place by finding a live shipped bug the 3387-test suite does not catch (F-06). FOURTH, a decision the reviewer should check rather than assume: E-05's per-line suppressions touch eleven modules that `- Scope-Paths:` deliberately does not declare, and the under-scope note sets out the two ways to handle that; the executor is instructed to raise it rather than widen the fence silently.

THE MAINTAINER DECISIONS THE ITEM RESERVED were handled as follows, so the reviewer can check the reasoning rather than re-derive it: the CHECKER choice is resolved from this project's own dependency posture (OQ-01, mypy), the BASELINE REGIME is resolved by measurement that a blanket baseline would have hidden F-06's live bug (OQ-03, read-and-triage), STRICTNESS is left at default with the measured cost of the obvious next flag recorded (OQ-05), and the PRE-COMMIT question is left to the maintainer with the timing measurements it needs (OQ-02), as is the 3.9-target gap the tool forces (OQ-04).

Per the execution contract: commit only the paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (extending it via `aw ipd set` first if E-05 or E-06 requires it), never push, and paste ACTUAL runner output for every validation item. After execution, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry pasted evidence before the plan moves to `.aw/records/plans/executed/`.
