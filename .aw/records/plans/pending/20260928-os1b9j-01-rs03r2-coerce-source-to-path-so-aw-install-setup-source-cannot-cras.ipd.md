# IPD: Coerce --source to Path so aw install/setup --source cannot crash

- Date: 2026-09-28
- Kind: child
- Concern: `engine.resolve_source_root` does `provided.expanduser().resolve()`, assuming `provided` is a `pathlib.Path`. The `aw install` and `aw setup` argparse options both declare `--source` with `dest="source_root"` and NO `type=Path`, so the parsed value is a plain `str`. On the `cli._run_install` -> `cli._diagnostics_ok` -> `engine.build_install_plan` -> `engine.resolve_source_root` path that `str` is passed through UNCOERCED, and a real `aw install --source <path> <target>` dies with an unhandled `AttributeError: 'str' object has no attribute 'expanduser'` before performing any work. Two of the three `resolve_source_root` call sites in `cli.py` coerce defensively with `Path(args.source_root).expanduser()`; the fourth path through `build_install_plan` does not, and that asymmetry is the defect. No test anywhere in the tree passes `--source` through the CLI parser, so nothing catches it.
- Scope: Make a string `--source` work everywhere it is accepted, and add the CLI-level regression coverage whose absence let this ship. IN: coercing inside `engine.resolve_source_root` so every caller (CLI, library, future) is hardened at the boundary, widening its annotation to `Path | str | None` to match, adding `type=Path` to both `--source` argparse declarations (`install` and `setup`) so the namespace carries the declared type, and a new regression test driving `--source` as a string through the real CLI parser to a real target repo. OUT: any change to resolution ORDER or validation semantics inside `resolve_source_root`, any change to what `--source` accepts or means, the `--dry-run` early-return ordering that happens to mask this (see Deferred), and the redundant `Path(...)` coercions already at the three other call sites.
- Scope-Paths: agent_workflows/engine.py, agent_workflows/cli.py, tests/test_install_source_option.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: os1b9j
- Blocks-Release: next
- Set: os1b9j
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: rs03r2
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-901..PR-906 all FIXED; Readiness go-pending-approval

- 2026-09-28 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901..PR-906 all FIXED. Reviewed at HEAD `da816198`. THE PLAN'S DIAGNOSIS AND FIX ARE CORRECT AND WERE INDEPENDENTLY RE-MEASURED: the crash reproduces through exactly the named frame chain, `--dry-run` masks it, and with E-01's coercion staged in memory the crashing install completes and commits while the bare suite reports `3202 passed, 2 skipped` unchanged from baseline (F-13). Findings are all in the EVIDENCE the plan hands its executor. PR-901: F-10's three-flag reproducer prescription is overstated, `-y` alone reaches the crash because `--yes` auto-supplies the default preset, so the test need not couple to three unrelated policy surfaces (F-12). PR-902: both suite figures had drifted 93 tests (`3109` -> `3202`) while the plan instructed the executor to REPORT a differing count as a finding (F-14). PR-903: `test_doctor.py` passes `None` and never reaches the changed branch, so the plan's stated reason for running it is wrong (F-15). PR-904: a real `aw setup` run scans the user's filesystem and writes a user-level config, which is a stronger reason than cost to keep E-03's setup coverage at the parser level (F-16). PR-905: F-09's count of 18 is actually 13, and `engine.py` has zero such annotations rather than "already uses" them (F-17). PR-906: the gate carried no scope fence and no approval-summary paragraph; both added. No production code was modified by this review; every measurement was staged in memory or in throwaway repos, since removed.
- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `os1b9j`. GATE NOTE: item `os1b9j` carries `- Blocks-Release: next`, which this plan INHERITS; it is a `bug` and the every-live-bug-gates-the-release rule applies.
  THE ITEM'S CENTRAL CLAIM REPRODUCES EXACTLY, INCLUDING THE CALL CHAIN IT NAMES, and was re-measured at authoring HEAD `36904869` rather than taken on trust: `aw install --source <path> <target>` dies with the named `AttributeError` in `resolve_source_root`, reached through `_run_install` -> `_diagnostics_ok` -> `build_install_plan`. See F-01.
  THE ITEM IS INCOMPLETE IN ONE WAY THAT MATTERS TO A REPRODUCER AND TO THE TEST. `--dry-run` DOES NOT CRASH: `_run_install` returns at its dry-run `continue` BEFORE reaching `_diagnostics_ok`, so the first and most cautious thing anyone would try to verify the bug with passes cleanly and looks like a refutation. The crash needs a real install. This cost measurable time during authoring and is why E-03's test must not use `--dry-run`. See F-02.
  THE ITEM UNDERSTATES THE BLAST RADIUS BY ONE VERB: `aw setup --source` (cli.py:9016) reaches the same `_diagnostics_ok` and carries the same un-typed `--source`, so it crashes identically. `aw install all` (cli.py:7375) is a third entry. See F-04.
  BOTH OF THE ITEM'S PROPOSED FIXES WERE APPLIED AND MEASURED TOGETHER BEFORE PROPOSING THEM, not reasoned about: the end-to-end install then SUCCEEDS and commits, and a bare `python3 -m pytest` reports `3109 passed, 2 skipped`. The probe was reverted and this turn commits no source change. See F-06, F-07.

## Goal

Make `aw install --source <path>` and `aw setup --source <path>` work when the path is a string, which is the only thing argparse can produce for those options today, by coercing at the `resolve_source_root` boundary and declaring the argparse type. Close the coverage hole that let an unhandled `AttributeError` on a documented public flag ship, by testing `--source` through the actual CLI parser rather than around it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: fix the crash at the boundary

- [x] E-01 COERCE INSIDE `engine.resolve_source_root` and widen its annotation. Change the single line `candidate = provided.expanduser().resolve()` to construct a `Path` first (`Path(provided).expanduser().resolve()`), and change the signature from `provided: Path | None` to `provided: Path | str | None` so the annotation states what the function now accepts. `Path(p)` is a no-op for a `Path` (it returns an equal path) so the existing `Path`-passing callers are unaffected.
  DO THIS AT THE ENGINE RATHER THAN ONLY AT ARGPARSE, and do it FIRST, because it is the fix that actually closes the hole. The item offers `type=Path` on the option OR `Path(provided)` in the resolver and notes the latter "also hardens library callers"; F-05 measures why that matters concretely. `resolve_source_root` is reached from SEVEN call sites across four modules, and the three in `cli.py` that pass a user value each hand-roll their own `Path(args.source_root).expanduser()` coercion. The defect is precisely that the fourth path (through `build_install_plan`) forgot to, so a fix that adds a fifth hand-rolled coercion preserves the shape that produced the bug. One coercion at the callee makes every present and future caller correct.
  `Path | str` IS THE ESTABLISHED CONVENTION IN THIS PACKAGE for exactly this, not a new idea: F-09 counts 18 such annotations in `runner_stop.py` alone plus further use in `run_analytics_privacy.py` and `run_analytics_query.py`. Follow it rather than inventing `os.PathLike` or a `Union` spelling.
  DO NOT CHANGE THE RESOLUTION ORDER OR THE VALIDATION. The `.aw/system` / `.agents/workflows` descent, the bundled-package and checkout fallbacks, the `is_valid` `SystemExit` with its message, and the nested-bundle `workflows/` descent are all untouched. The ONLY behavior change is that a non-`Path` argument no longer raises `AttributeError`.
  - Depends on: none
  - Expected outcome: `engine.resolve_source_root("<path>")` returns the same `Path` as `engine.resolve_source_root(Path("<path>"))` instead of raising, the annotation reads `Path | str | None`, and no other line of the function changed.
  - Execution state: performed

- [x] E-02 ADD `type=Path` TO BOTH `--source` ARGPARSE DECLARATIONS in `cli.py`, on the `install` subparser and on the `setup` subparser (the latter is `help=argparse.SUPPRESS` but fully functional and reaches the same crash, per F-04). This is the item's other suggested fix and it is complementary, not redundant: E-01 stops the crash, while this makes the namespace actually carry the type every downstream reader already assumes, matching `engine.parse_args`, which has declared `type=Path` on its own `--source` all along (F-03) and is why the deprecated `install-workflows.py` shim never hit this.
  DO NOT REMOVE THE THREE EXISTING `Path(args.source_root).expanduser()` COERCIONS at the other call sites (see Deferred). They become redundant once both E-01 and E-02 land, but they are correct, harmless, and deleting them would widen this plan into a refactor of code that is not broken.
  VERIFY THE `expanduser` SEMANTICS ARE PRESERVED, since this is the one place `type=Path` could change behavior: `type=Path` constructs a `Path` but does NOT expand `~`, so a `--source ~/x` that the shell did not expand still relies on the `.expanduser()` inside `resolve_source_root`. That call stays, so a tilde path keeps working through both verbs; V-02 requires this measured rather than assumed.
  - Depends on: E-01
  - Expected outcome: both `--source` declarations carry `type=Path`, a parsed `args.source_root` is a `Path` for both verbs, and an unexpanded `~` source still resolves.
  - Execution state: performed

### Task group 2: close the coverage hole

- [x] E-03 ADD A CLI-LEVEL REGRESSION TEST in a new `tests/test_install_source_option.py` that drives `--source` AS A STRING THROUGH THE REAL CLI PARSER into a real target repo and asserts the install succeeds. Without it this fix is one line that any future edit can silently undo, and the item's own root-cause analysis is that the absence of exactly this test is why the bug shipped: F-08 measures ZERO occurrences of `--source` anywhere under `tests/`, and `tests/support.run_installer` drives the deprecated `install-workflows.py` shim, which routes through `engine.parse_args` where `type=Path` already exists (F-03), so it can never exercise the broken path.
  GO THROUGH `cli.main`/`_dispatch` (or a subprocess `python3 -m agent_workflows install`), NEVER through `engine.install_into_repo` DIRECTLY. Driving the engine directly with a real `Path` is precisely what the three existing installer tests do (F-08 cites `tests/test_installer.py` `resolve_source_root(self.root)` sites passing `Path` objects), and it is why they all pass against the broken tree. The test must cross the argparse boundary or it tests nothing about this defect.
  DO NOT USE `--dry-run`, because it does not reach the defect: F-02 measures `_run_install` returning at its dry-run `continue` BEFORE `_diagnostics_ok`, so a dry-run install passes on the BROKEN tree and such a test would be permanently vacuous. Perform a real install into a throwaway git repo.
  COVER BOTH VERBS' PARSED TYPE, cheaply, with a parser-level assertion that `--source` yields a `Path` for `install` AND for `setup`. F-04 measures that a `setup`-parsed namespace handed to `_diagnostics_ok` raises the identical `AttributeError`, so the defect is real on that verb. DO NOT DRIVE THE REAL `setup` VERB END-TO-END, and the binding reason is stronger than cost: F-16 measures that a real `aw setup` run DISCOVERS REPOS ACROSS THE USER'S FILESYSTEM and WRITES `~/.config/agent-workflows/config.json`, i.e. it has side effects OUTSIDE the target repo and outside this workspace. A parser-level assertion plus the direct `_diagnostics_ok` probe below is the complete and safe coverage for that verb. Add a direct `resolve_source_root` unit assertion that a `str` and the equivalent `Path` return the same value, which is the tightest possible guard on E-01. OPTIONALLY add the `setup`-shaped `_diagnostics_ok` probe review used (parse `["setup", "--source", "<path>", "-y"]`, call `cli._diagnostics_ok(Path(target), args)`, assert no `AttributeError`); it is cheap, side-effect free, and covers the actual crash site on that verb rather than only the parsed type.
  MUTATION-CHECK THE TEST, since a regression test that cannot fail proves nothing: neutralize E-01's coercion and show the new test FAILING with the `AttributeError`, then restore and show it green. STAGE THE MUTATION IN MEMORY, NOT BY EDITING A TRACKED FILE (`mock.patch.object` on `engine.resolve_source_root`, or an out-of-tree pytest plugin): `agent_workflows/engine.py` is a shared-checkout file and a `git checkout` restore after a minute-long suite run silently discards a co-worker's concurrent edit. Review measured every fix-side claim in this plan that way, including the full suite, with `git status --short` empty before and after; the mechanism is verified to work because `build_install_plan` looks the name up on the module at call time.
  FOLLOW THIS REPOSITORY'S TARGET-REPO FIXTURE CONVENTIONS rather than inventing one. `tests/support.py` already provides the helpers (`init_repo`, `git`) the installer tests use to stand up a throwaway git repo; reuse them, or pytest's `tmp_path`. PASS THE MINIMUM POLICY SIGNAL, WHICH IS `-y` ALONE (F-12, correcting F-10): a wholly flagless non-interactive install refuses with `FAIL Noninteractive first install requires complete policy choices` and never reaches the defect, but `-y` by itself is enough, because `_run_install` auto-supplies `explicit_preset = Preset.PRIVATE_TARGET.value` when `--yes` is passed with no `--preset` and no `--delivery-mode`. Do NOT hardcode `--preset private-target --delivery-mode tracked --records-backend repository` unless the fixture genuinely needs them: that couples this regression test to three policy surfaces unrelated to the defect, each of which can change independently and break the test for the wrong reason.
  - Depends on: E-02
  - Expected outcome: a passing test module that fails on the pre-fix tree with the `AttributeError` and passes after, covering the end-to-end string `--source` install, the parsed type for both verbs, and str/`Path` equivalence at the resolver.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `Path | str` IS THE PACKAGE'S ESTABLISHED SPELLING for a path parameter that accepts either, used 13 times in `runner_stop.py` (count corrected at review, F-17; the plan originally said 18) and also in `run_analytics_privacy.salt_path`, `run_analytics_privacy.load_or_create_salt` and `run_analytics_query._cache_entries`. `run_cli.py` uses the older `Union[str, Path]`. Prefer the modern `Path | str`. NOTE `engine.py` has ZERO such annotations today, so E-01 introduces the first one in that module while matching the package convention; the plan's earlier claim that `engine.py` "already uses" it elsewhere is wrong and F-09 states the accurate version.
- REPRODUCE A CLI DEFECT THROUGH THE CLI, NOT THROUGH THE ENGINE. The whole reason this bug survives a 3109-test suite is that `tests/support.run_installer` and the installer tests enter below the argparse boundary. A test that does not cross that boundary cannot see an argparse-typing defect.
- `--dry-run` IS NOT A SAFE PROXY FOR AN INSTALL in `_run_install`: it returns early, before the git-diagnostics pre-flight. Any evidence gathered with `--dry-run` may be describing a code path the real invocation never takes.
- A WHOLLY FLAGLESS NON-INTERACTIVE FIRST INSTALL REFUSES and reports `FAIL Noninteractive first install requires complete policy choices`. This is a clean refusal, not the crash, and an unwary reproducer will mistake one for the other. But the minimum to get past it is `-y` ALONE, not the three flags named in F-10 (corrected at review, F-12): `--yes` with no `--preset` and no `--delivery-mode` auto-supplies the default preset inside `_run_install`.
- A REAL `aw setup` RUN HAS SIDE EFFECTS OUTSIDE THE TARGET REPO (F-16): it discovers repos across the user's filesystem and writes `~/.config/agent-workflows/config.json`. Never drive it as evidence for a targeted defect; probe the parsed namespace or call `_diagnostics_ok` directly instead.
- RUN THE SUITE BARE (`python3 -m pytest`). `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; adding `-n0` makes it several times slower and a second `-q` suppresses the summary line this plan requires be pasted.
- THE `aw` CONSOLE SCRIPT MAY RESOLVE `agent_workflows` FROM THE MAIN CHECKOUT rather than this lane, and it announces the re-exec on stderr (observed during authoring: `aw: invoked in checkout <lane> but imported agent_workflows from <main>; re-running with <lane>'s package`). Any invocation used as evidence must state which interpreter and `PYTHONPATH` produced it, or it may be measuring the wrong code. Prefer `python3 -m agent_workflows`.
- WRITE THROWAWAY REPOS INSIDE THE LANE, not `/tmp`. Authoring was denied external-directory access and used `.aw/state/` scratch dirs, removed afterwards; tests should use pytest's `tmp_path` or the existing `tests/support` fixtures.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE DEFECT REPRODUCES END-TO-END THROUGH EXACTLY THE CHAIN THE ITEM NAMES, at authoring HEAD `36904869`.** A real `install --source <abs path> <target>` into a fresh git repo dies with an unhandled traceback, and every frame the item predicted is present in order: `cli.main` -> `cli._dispatch` -> `cli._run_install` -> `cli._diagnostics_ok` -> `engine.build_install_plan` -> `engine.resolve_source_root` -> `AttributeError: 'str' object has no attribute 'expanduser'` at `candidate = provided.expanduser().resolve()`. This is an unhandled crash with a traceback, not a `SystemExit` with a diagnostic, so the user sees a stack dump on a documented public flag. | `python3 -m agent_workflows install --source "$(pwd)" <throwaway-repo> --preset private-target --delivery-mode tracked --records-backend repository -y`; full traceback captured |
| F-02 | **`--dry-run` DOES NOT REPRODUCE THE CRASH, which makes the first thing any reproducer tries look like a refutation.** The identical command plus `--dry-run` completes cleanly and prints `OK [DRY RUN] No changes written`. Reading `_run_install`, the dry-run branch renders the pre-write plan and hits `continue` BEFORE the `if not _diagnostics_ok(repo_root, args):` pre-flight, so the only call site that passes the raw `str` is never reached. CONSEQUENCE FOR E-03: a regression test written with `--dry-run` would pass on the broken tree and be permanently vacuous. This is the single most useful thing authoring learned that the item does not say. | same invocation with `--dry-run` exiting clean; read of `_run_install`'s dry-run `continue` preceding the `_diagnostics_ok` call |
| F-03 | **`engine.parse_args` HAS DECLARED `type=Path` ON ITS OWN `--source` ALL ALONG, so the two entry points disagree and only the newer one is broken.** The engine's parser declares `--source` with `dest="source_root", type=Path`; both `cli.py` declarations omit it. This explains why the deprecated `install-workflows.py` shim (which calls `engine.main()` and so `engine.parse_args`) never hit this, while the modern `aw install` does. It also settles that `type=Path` is the intended contract here rather than a new convention this plan invents. | `engine.parse_args`'s `add_argument("--source", dest="source_root", type=Path, ...)` versus both `cli.py` sites lacking it; `install-workflows.py` delegating to `engine.main()` |
| F-04 | **THE ITEM UNDERSTATES THE SURFACE: `aw setup --source` CRASHES IDENTICALLY, and `aw install all` is a third entry.** `_diagnostics_ok` is called from THREE places in `cli.py`: `_run_install` (single target), the install-all path, and the `setup` path. `p_setup` declares `--source` with `dest="source_root"` and no `type=Path` (hidden behind `help=argparse.SUPPRESS` but fully functional), so it reaches the same `build_install_plan` with a `str`. So the fix must cover both argparse declarations, not just `install`'s. | three `_diagnostics_ok(` call sites in `cli.py`; `p_setup.add_argument("--source", dest="source_root", default=None, help=argparse.SUPPRESS)` |
| F-05 | **THE RESOLVER IS CALLED FROM SEVEN SITES ACROSS FOUR MODULES, AND THE THREE THAT PASS A USER VALUE EACH HAND-ROLL THE COERCION THE BROKEN PATH FORGOT.** The three `cli.py` sites that forward `args.source_root` all wrap it as `Path(args.source_root).expanduser()`; the four others (`doctor.py`, `check_engine.py`, `compat_migration.py`, `cli.py`'s workflow-root lookup) pass `None`. `engine.build_install_plan` passes `args.source_root` RAW. So the codebase already demonstrates that callers cannot be relied on to coerce, which is the argument for fixing the callee (E-01) rather than adding a fourth hand-rolled `Path(...)`. | `rg 'resolve_source_root\('` across `agent_workflows/` and `tests/`; the three `Path(args.source_root).expanduser()` wrappers versus `build_install_plan`'s `resolve_source_root(args.source_root)` |
| F-06 | **BOTH PROPOSED FIXES TOGETHER RESOLVE IT END-TO-END, MEASURED BEFORE BEING PROPOSED.** With `resolve_source_root` coerced and its annotation widened, the previously crashing real install runs to completion, writes the framework, and reports `Changes committed successfully.`; and `resolve_source_root('.')` and `resolve_source_root(Path('.'))` both return the identical resolved bundle path. The probe edit was then REVERTED (`git checkout -- agent_workflows/engine.py`, tree confirmed carrying only this plan file) and the `AttributeError` re-confirmed present, so this plan proposes a change already known to work rather than one hoped to. | patched-tree install completing and committing; str/`Path` parity probe; post-revert re-confirmation of the `AttributeError` |
| F-07 | **THE FIX IS CLEAN AGAINST THE WHOLE SUITE.** With the coercion applied, a bare `python3 -m pytest` reported `3109 passed, 2 skipped, 3 warnings in 47.36s` (205 deselected as `slow`/`livecorpus` by the configured `addopts`). So no existing test depends on `resolve_source_root` rejecting a `str`, and the one-line change carries no measured regression risk. | bare `python3 -m pytest` in this lane with the probe applied |
| F-08 | **THE COVERAGE HOLE IS TOTAL, WHICH CONFIRMS THE ITEM'S ROOT-CAUSE ANALYSIS AND CONSTRAINS E-03's DESIGN.** `--source` appears ZERO times anywhere under `tests/`. `tests/support.run_installer` invokes `[sys.executable, str(INSTALLER), "--repo", str(repo), *extra]` where `INSTALLER` is the deprecated `install-workflows.py`, so even if a test passed `--source` through that helper it would route via `engine.parse_args` and its existing `type=Path` (F-03), never touching the broken path. The three tests that do call the resolver with a value pass real `Path` objects (`INS.resolve_source_root(self.root)` in `tests/test_installer.py`). Hence E-03 must enter through `cli`, not through `support.run_installer` and not through the engine. | `rg '\-\-source' tests/` returning nothing; `tests/support.run_installer` and its `INSTALLER = REPO_ROOT / "install-workflows.py"`; the `Path`-passing resolver calls in `tests/test_installer.py` |
| F-09 | **`Path \| str` IS THE PACKAGE'S EXISTING CONVENTION for this exact widening, so E-01 follows precedent rather than setting one.** `runner_stop.py` uses `Path \| str` on 18 parameters (`stop_request_path`, `read_stop_request`, `poll_stop`, `run_liveness` among them); `run_analytics_privacy.py` and `run_analytics_query.py` use it too. The older `Union[str, Path]` spelling survives in `run_cli.py`. `engine.py` currently has no `Path \| str` annotation, so E-01 introduces the first one in that module, matching the package rather than the file. | `rg 'Path \| str\|str \| Path\|Union\[str, Path\]'` across `agent_workflows/` |
| F-10 | **A NON-INTERACTIVE FIRST INSTALL REFUSES CLEANLY WITHOUT POLICY FLAGS, and that refusal is easily mistaken for the defect being absent.** Omitting them yields `FAIL Noninteractive first install requires complete policy choices. Missing required fields: --preset ..., --delivery-mode ..., --records-backend ...` and never reaches `_diagnostics_ok`. Recorded because it, together with F-02, accounts for both false negatives encountered while confirming this item. **NARROWED AT REVIEW (PR-901, see F-12): the three-flag set is NOT required, and asserting that it is would send an executor past the smallest reproducer.** The refusal fires only when NO policy signal is present at all. `-y` ALONE is sufficient to reach the crash, because `_run_install` auto-supplies `explicit_preset = Preset.PRIVATE_TARGET.value` when `--yes` is passed with no `--preset` and no `--delivery-mode` (read at the `if getattr(args, "yes", False) and not explicit_preset and not getattr(args, "delivery_mode", None):` branch). `--preset private-target` alone is likewise sufficient. Measured: all three of `-y`, `--preset private-target`, and the full three-flag set reach the identical `AttributeError`; only a wholly flagless non-interactive invocation refuses. | the `FAIL` refusal from the truly flagless invocation (`< /dev/null`, no `-y`) versus the identical traceback from each of `-y` alone, `--preset private-target` alone, and the full three-flag set; read of `_run_install`'s `explicit_preset` auto-default branch |
| F-12 | **ADDED AT REVIEW (PR-901). THE MINIMAL REPRODUCER IS `--source <path> <target> -y`, AND F-10's THREE-FLAG PRESCRIPTION IS OVERSTATED.** Review re-measured the reproducer on a fresh throwaway repo per invocation, at HEAD `da816198`, and got the same `AttributeError` at `engine.py`'s `candidate = provided.expanduser().resolve()` from all of: the plan's full three-flag command, `-y` alone, and `--preset private-target` alone (non-interactive stdin). Only the wholly flagless non-interactive form refused with the `FAIL Noninteractive first install requires complete policy choices` message. THE CONSEQUENCE IS PRACTICAL RATHER THAN PEDANTIC: E-03's test and V-01's reproduction inherit F-10's prescription as a hard requirement, so an executor writes three flags where one suffices, and the test then couples itself to three policy surfaces (`--preset`, `--delivery-mode`, `--records-backend`) that have nothing to do with this defect and can each change independently. Prefer `-y` plus whatever the fixture already needs. | four invocations, each into its own fresh `git init` repo: full-flag set -> `AttributeError`; `-y` alone -> `AttributeError`; `--preset private-target` alone with `< /dev/null` -> `AttributeError`; no flags with `< /dev/null` -> the `FAIL` policy refusal; read of the `explicit_preset = Preset.PRIVATE_TARGET.value` auto-default in `_run_install` |
| F-11 | **THE BUG IS OLD AND PRE-DATES THE ITEM, consistent with the item's own "PRE-EXISTING at HEAD 6ff7a7ba" note.** The crashing line `candidate = provided.expanduser().resolve()` entered in `ccceb144` ("IPD-2 Batch A: package the install engine (no behavior change)", 2026-07-07), when the resolver was `Path`-only and the `cli.py` `--source` option that feeds it a `str` did not yet exist. So this is integration drift between the packaged engine and the newer CLI, not a regression from any recent change, and there is no recent commit to revert. | `git log -S'candidate = provided.expanduser().resolve()' -- agent_workflows/engine.py` -> `ccceb144` |
| F-13 | **ADDED AT REVIEW. EVERY CLAIM ABOUT THE EXISTING CODE REPRODUCED AT HEAD `da816198`, INCLUDING THE FULL FRAME CHAIN AND THE FIX'S SAFETY.** The traceback frames match F-01 in order (`cli.main` -> `_dispatch` -> `_run_install` -> `_diagnostics_ok` -> `engine.build_install_plan` -> `engine.resolve_source_root` -> `AttributeError`). `--dry-run` passes cleanly on the broken tree, confirming F-02, and reading `_run_install` shows the dry-run `continue` preceding the `_diagnostics_ok` call. F-03 holds (`engine.parse_args` declares `type=Path`; both `cli.py` sites omit it, `install` at the visible declaration and `setup` at the `help=argparse.SUPPRESS` one). F-05 holds exactly: three `cli.py` sites wrap as `Path(args.source_root).expanduser()` and `build_install_plan` passes raw. F-11's provenance holds (`git log -S` -> `ccceb144`). AND THE FIX WAS RE-MEASURED, not taken on trust: with E-01's coercion staged through an out-of-tree pytest plugin, the bare suite reports `3202 passed, 2 skipped, 3 warnings in 142.87s`, IDENTICAL to the unpatched baseline, and the previously crashing real install runs to completion and reports `Changes committed successfully.`. `resolve_source_root('.')` and `resolve_source_root(Path('.'))` return the same resolved bundle path. No tracked file was edited to measure any of this; `git status --short` was empty before and after. | the four reproductions above; the plugin-staged bare suite run; the end-to-end patched install; the parity probe; `git status --short` empty throughout |
| F-14 | **ADDED AT REVIEW (PR-902). BOTH SUITE FIGURES IN THIS PLAN HAVE DRIFTED, BY 93 TESTS.** F-07 and Required tests both cite `3109 passed, 2 skipped` as the post-fix figure, and Required tests says "a materially different count is itself a finding to report rather than to normalize". Review's clean-tree bare run at HEAD `da816198` reads `3202 passed, 2 skipped, 3 warnings in 71.88s`. An executor obeying that instruction literally would open a finding about a 93-test difference caused entirely by other work landing between authoring and execution. The count is a live, moving population and belongs in prose as context; the BAR is zero failures and a delta against the executor's own pre-work baseline. | review's clean-tree `python3 -m pytest` -> `3202 passed, 2 skipped, 3 warnings in 71.88s` at HEAD `da816198`, against F-07's `3109 passed, 2 skipped` at `36904869` |
| F-15 | **ADDED AT REVIEW (PR-903). `tests/test_doctor.py` DOES NOT CALL THE RESOLVER WITH A VALUE, so the plan's stated reason for running it is wrong.** Required tests names `test_installer.py` and `test_doctor.py` as "the modules that call `resolve_source_root` directly (F-05, F-08) and so are the likeliest to notice a mistake in E-01". Both of `test_doctor.py`'s calls are `engine.resolve_source_root(None)`, which takes the `provided is None` branch and never touches the line E-01 changes. `test_installer.py` DOES pass a value (`INS.resolve_source_root(self.root)` with a real `Path`), and so does exercise the changed branch. Running `test_doctor.py` is still cheap and harmless, but the stated rationale would mislead an executor about what their evidence proves. Two further modules call the resolver with `None` and go unmentioned: `tests/test_releases.py` and, in the package, `doctor.py`, `check_engine.py`, `compat_migration.py`. | `rg -n "resolve_source_root" tests/test_doctor.py` -> two `(None)` calls; `tests/test_installer.py`'s `resolve_source_root(self.root)` sites passing `Path` objects; `rg -n "resolve_source_root" tests/` for the full set |
| F-16 | **ADDED AT REVIEW (PR-904). `aw setup --source` CRASHES AT THE ARG SHAPE BUT IS NOT REACHED BY A PLAIN `aw setup` RUN, AND DRIVING THE REAL VERB HAS SIDE EFFECTS OUTSIDE THE TARGET.** F-04's claim is CORRECT at the level that matters: handing `_diagnostics_ok` a real `setup`-parsed namespace raises the identical `AttributeError` (measured directly). But the path there is guarded: `setup` resolves `source_root` at its own call site FIRST, with the defensive `Path(args.source_root).expanduser()` coercion, so that call succeeds, and `_diagnostics_ok` is reached only inside the `if found.targets and _confirm(...)` branch. Separately, and this is the operational warning: a real `aw setup` run DISCOVERS REPOS ACROSS THE USER'S FILESYSTEM and WRITES `~/.config/agent-workflows/config.json`. Review triggered exactly that while probing F-04 and it reached directories far outside this workspace. SO E-03 IS RIGHT to cover `setup` only at the parser level, and V-02 must NOT be satisfied by driving the real verb; the plan says the end-to-end setup is "expensive and interactive" and the stronger true reason is that it has side effects outside the target repo. | direct `_diagnostics_ok(Path("."), setup_args)` call raising `AttributeError: 'str' object has no attribute 'expanduser'`; read of `setup`'s own `resolve_source_root` call with its `Path(...)` wrapper preceding `_diagnostics_ok`; an observed real `aw setup` run enumerating unrelated directories and reporting `Saved config to <user config path>` |
| F-17 | **ADDED AT REVIEW (PR-905). F-09's COUNT IS WRONG, THOUGH ITS CONVENTION CLAIM IS RIGHT.** F-09 says `runner_stop.py` uses `Path | str` "on 18 parameters"; the actual count is 13 occurrences on 13 lines (`stop_request_path`, `stop_request_lock_path`, `read_stop_request`, `poll_stop`, `run_liveness` among them, plus two `Path | str | None`). The CONVENTION claim holds and is what E-01 relies on: the spelling is established here and also in `run_analytics_query.py` (7) and `run_analytics_privacy.py` (2), with the older `Union[str, Path]` surviving in `run_cli.py` (3). `engine.py` has zero today, so E-01 does introduce the first in that module, exactly as F-09 says. Corrected because a wrong number in a Findings row invites a reader to discount the row. | `rg -o "Path \| str\|str \| Path" agent_workflows/runner_stop.py \| wc -l` -> 13, with the 13 lines enumerated; per-file counts for `run_analytics_query.py`, `run_analytics_privacy.py`, `engine.py`, `run_cli.py` |

## Proposed changes (ordered, validatable)

1. Coerce with `Path(provided)` inside `engine.resolve_source_root` and widen its annotation to `Path | str | None`, leaving resolution order and validation untouched (E-01).
2. Add `type=Path` to the `--source` declarations on both the `install` and `setup` subparsers in `cli.py` (E-02).
3. Add `tests/test_install_source_option.py` covering a real string-`--source` install through the CLI, the parsed type for both verbs, and str/`Path` equivalence at the resolver, mutation-checked (E-03).

## Deferred / out of scope (with reason)

- REORDERING `_run_install` SO `--dry-run` ALSO RUNS THE GIT-DIAGNOSTICS PRE-FLIGHT. F-02 measures that the dry-run early `continue` is what hides this crash, so it is tempting to call the ordering itself a defect. It is out of scope on its own merits: a dry run deliberately writing and checking nothing is defensible, changing when the pre-flight runs would alter `--dry-run` behavior for every install (a far larger blast radius than this one-line bug fix), and the pre-flight can PROMPT, which a dry run should not. Fixing the crash makes the ordering harmless either way.
  - Carrier-Declined: no defect is identified in the ordering itself, only a reduced-fidelity dry run; nothing is left unresolved, and E-03 records the constraint so no future test is written against the masked path
- REMOVING THE THREE REDUNDANT `Path(args.source_root).expanduser()` COERCIONS at the other `cli.py` call sites (F-05) once E-01 makes them unnecessary. They are correct and harmless; deleting them is a cosmetic refactor of working code in the same file as a bug fix, which makes the fix harder to review and risks touching a path this plan has no test for. Defense in depth at a call site is not a defect.
  - Carrier-Declined: a decision not to widen scope onto correct code; nothing outstanding is created
- AUDITING EVERY OTHER `aw` OPTION THAT NAMES A PATH BUT LACKS `type=Path` (`--companion-dir` is visible in the same `install` parser). Potentially valuable but it is a different, open-ended piece of work with no measured defect behind it, and `cli.py` declares hundreds of options. This plan fixes the one measured crash on the flag the item filed.
  - Carrier-Declined: no defect measured in any other option; a speculative audit is not a gate on this fix
- HARDENING `engine.build_install_plan`'s SIBLING `args.repo_root.expanduser().resolve()`, which would crash the same way on a `str`. It is not reachable with a `str` today: every caller sets `repo_root` to a `Path` (`_diagnostics_ok` assigns the already-`Path` `repo_root` argument, and `engine.main` assigns from `repo_roots`, which `engine.parse_args` declares `type=Path`). No invocation reaches it with a string, so there is no user-visible defect to fix, and speculatively coercing it would be an unmeasured change.
  - Carrier-Declined: not reachable with a non-Path value from any current caller, so no defect exists to carry

## Scope check

- Over-scope: none. All three scope paths are required: `agent_workflows/engine.py` carries the crashing line and the annotation (E-01), `agent_workflows/cli.py` carries both un-typed `--source` declarations (E-02), and `tests/test_install_source_option.py` is the regression guard whose absence is the item's stated root cause (E-03).
- Under-scope: this plan changes only WHETHER a string `--source` is accepted. It does not change resolution order, what counts as a valid source directory, the `SystemExit` message on an invalid one, the nested-bundle `workflows/` descent, or any other install behavior. It deliberately leaves the `--dry-run` pre-flight ordering that masks the bug (Deferred, F-02), the three redundant call-site coercions (Deferred, F-05), and every other path-valued option in the CLI. The user-visible delta is exactly that `aw install --source` and `aw setup --source` stop crashing. VERIFIED AT REVIEW, not merely asserted (F-13): with E-01's coercion staged in memory the bare suite reports `3202 passed, 2 skipped`, byte-identical to the unpatched baseline, so no existing test depends on the resolver rejecting a `str` and the change carries no measured regression.

## Required tests / validation

- `python3 -m pytest` BARE, per the repository contract, pasting the ACTUAL summary line. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`. Establish the baseline on a CLEAN tree BEFORE editing and judge on the DELTA OF FAILING NODE IDS; prove any surviving failure pre-existing by reproducing it with this work stashed. THE BAR IS ZERO FAILURES AND A DELTA AGAINST YOUR OWN BASELINE; THE TOTAL IS CONTEXT, NOT A BAR. Two measurements, both clean and fully green: `3109 passed, 2 skipped` at authoring (HEAD `36904869`, F-07) and `3202 passed, 2 skipped, 3 warnings in 71.88s` at review (HEAD `da816198`, F-14). THE TREE MOVED BY 93 TESTS BETWEEN THEM, so do NOT treat a differing total as a finding (the earlier wording said to report one, which would open a finding about other people's work); expect only the new test module to raise YOUR count.
- `python3 -m pytest tests/test_install_source_option.py tests/test_installer.py tests/test_cli.py tests/test_doctor.py` for the focused surface. `test_installer.py` is the module that calls `resolve_source_root` WITH A VALUE (`resolve_source_root(self.root)`, a real `Path`) and so actually exercises the branch E-01 changes. CORRECTED AT REVIEW (F-15): `test_doctor.py`'s two calls are both `resolve_source_root(None)` and take the other branch entirely, so running it proves nothing about E-01; keep it in the list as cheap breadth, not as evidence. `tests/test_releases.py` is a third `None`-passing caller, unmentioned and equally uninformative here.
- THE BEFORE/AFTER REPRODUCTION, pasted in full: the real (NOT `--dry-run`) `install --source <path> <target> -y` into a throwaway git repo, showing the `AttributeError` traceback on the pre-fix tree and a successful install after. `-y` ALONE IS SUFFICIENT (F-12, correcting F-10): the three-flag set works too but is not required, because `--yes` with no `--preset`/`--delivery-mode` auto-supplies the default preset. A WHOLLY FLAGLESS non-interactive invocation does refuse before reaching the defect, so pass at least `-y`. State plainly that `--dry-run` is NOT a valid check here and why (F-02). USE A FRESH THROWAWAY REPO PER INVOCATION: a repo that a prior successful run already installed into is no longer a first install and may take a different policy path.
- THE MUTATION PROOF for E-03: neutralize E-01's coercion IN MEMORY (never by editing the tracked file, per E-03's method rule), paste the new test module FAILING with the `AttributeError`, restore, paste it green, and paste `git status --short` empty before and after. A regression test that passes on the broken tree is worthless and this is the only evidence that distinguishes the two.
- THE STR/PATH PARITY PROBE: paste `resolve_source_root('<path>')` and `resolve_source_root(Path('<path>'))` returning the SAME value, and confirm the existing `Path`-passing callers are unaffected.
- THE TILDE CASE, because it is the one semantic `type=Path` could plausibly break: paste a `--source ~/...`-shaped value (quoted so the shell does not expand it) resolving correctly through both `install` and `setup` parsing, proving the `.expanduser()` inside the resolver still does its job after E-02 (V-02).
- THE PARSED-TYPE CHECK FOR BOTH VERBS: paste the parsed `args.source_root` and its `type()` for `install --source` and for `setup --source`, showing `Path` in both cases after E-02 (F-04).
- MEASUREMENT DISCIPLINE: the `aw` console script may resolve `agent_workflows` from the MAIN checkout rather than this lane and announces the re-exec on stderr. Run evidence-producing invocations via `python3 -m agent_workflows` or with `PYTHONPATH=<lane>`, and STATE which was used; otherwise the measurement may describe the wrong code.
- CLEAN UP EVERY THROWAWAY REPO created for evidence, and confirm `git status --short` shows only this plan's intended paths. Authoring created and removed scratch dirs under `.aw/state/`; prefer pytest `tmp_path` in the test itself.
- `python3 -m agent_workflows check` must not gain a diagnostic.
- `aw sanitize --agent` clean, since this plan's evidence pastes absolute lane paths in install output and `PYTHONPATH`.

## Spec / documentation sync

NO `.spec.md` FILE IS EDITED AND NONE NEEDS TO BE, which is why `- Scope-Paths:` declares no spec. No approved spec governs `resolve_source_root`'s parameter type or the `--source` option's argparse declaration: this is an unhandled-exception bug fix restoring the behavior the flag's own `--help` text already promises ("Path to source .aw/system or legacy .agents/workflows (dev/override)"). Nothing about what `--source` MEANS, accepts, or resolves to changes, so no contract moves.

NO USER-FACING DOCUMENTATION CHANGES EITHER, for the same reason: the flag keeps its spelling, its `dest`, its help text and its semantics, and no flag is added or removed. The only observable difference is that a documented invocation stops dying with a traceback, which is the restoration of documented behavior rather than a change to it. A CHANGELOG entry under the bug-fix heading is appropriate at release time per this repository's normal practice, and needs no spec or doc edit here.

## Open questions

### OQ-01: Coerce in the resolver, declare `type=Path` at argparse, or both?

- Blocking: no
- Status: resolved
- Owner: executor
- Finding: F-03, F-05, F-09
- Resolution or deferral rationale: RESOLVED AS BOTH, WITH THE RESOLVER COERCION AS THE LOAD-BEARING FIX. The item offers the two options and states the tiebreaker itself, that coercing inside `resolve_source_root` "also hardens library callers". F-05 makes that concrete rather than abstract: the resolver has seven call sites across four modules, and the three that forward a user value each hand-roll `Path(args.source_root).expanduser()` while the fourth (`build_install_plan`) does not. The bug IS that asymmetry, so fixing only argparse would leave the callee still unable to accept what its own callers demonstrably pass inconsistently, and any future caller would have to remember the same coercion.
  `type=Path` IS STILL WORTH ADDING, on evidence rather than for tidiness: `engine.parse_args` has declared it on its own `--source` since before the CLI existed (F-03), so the two entry points currently disagree and the CLI is the outlier. Adding it makes the namespace carry the type every downstream reader assumes, and it is why the deprecated shim never hit this bug. Doing both costs two lines and removes both halves of the inconsistency.
  WHY THIS WAS NOT SENT TO THE MAINTAINER: the item already prescribes both candidate fixes and names the criterion for preferring one; the repository then answers which is load-bearing by measurement (F-05), and `Path | str` is the package's own established spelling for this widening (F-09). No scope, priority or public-contract judgement is involved, since neither option changes what `--source` accepts from a user.

### OQ-02: Should the `--dry-run` ordering that masks this crash be changed too?

- Blocking: no
- Status: resolved
- Owner: executor
- Finding: F-02
- Resolution or deferral rationale: RESOLVED AS NO, AND RECORDED BECAUSE THE DISCOVERY IS MORE IMPORTANT THAN THE DECISION. F-02 measures that `--dry-run` passes cleanly on the broken tree because `_run_install` hits its dry-run `continue` before the `_diagnostics_ok` pre-flight. That is a genuine fidelity gap: a dry run does not exercise a check the real run performs, so it can report success where the real command dies.
  IT IS STILL OUT OF SCOPE HERE, on three grounds. A dry run deliberately performing no checks that could prompt is defensible (the pre-flight can prompt on a dirty or behind repo, which a dry run should not). Changing when the pre-flight runs alters `--dry-run` for every install, a far larger blast radius than the one-line bug this plan fixes, and it would need its own evidence and tests. And once E-01 lands, the masked path no longer crashes, so the ordering stops hiding anything.
  THE PART THAT MUST NOT BE LOST IS THE TEST CONSTRAINT, and it is carried in E-03 rather than left in this question: a regression test using `--dry-run` would pass on the BROKEN tree and be permanently vacuous. That is the trap authoring actually fell into before measuring, and it is now a hard requirement on the test rather than a footnote. Nothing outstanding is created, which is why this carries no carrier.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the committed diff region of `engine.resolve_source_root` showing `Path(provided).expanduser().resolve()` and the signature reading `provided: Path | str | None`, and confirm by reading the diff that NO other line of the function changed (resolution order, the `.aw/system`/`.agents/workflows` descent, the `is_valid` check and its `SystemExit` message, and the nested-bundle `workflows/` descent all byte-identical). Paste the STR/PATH PARITY PROBE showing `resolve_source_root('<abs path>')` and `resolve_source_root(Path('<abs path>'))` returning the SAME resolved path. Paste the END-TO-END REPRODUCTION both ways: the real (NOT `--dry-run`) `install --source <path> <target> -y` into a FRESH throwaway git repo showing the `AttributeError` traceback BEFORE the fix and a successful completion AFTER; `-y` alone suffices for the policy gate (F-12) and a fresh repo per invocation is required because an already-installed repo is no longer a first install. Paste `python3 -m pytest tests/test_installer.py` green, which is the module that calls the resolver WITH A VALUE and therefore exercises the branch E-01 changes; `test_doctor.py` may be run for breadth but does NOT constitute evidence here, since both its calls pass `None` and take the other branch (F-15). Name the interpreter and `PYTHONPATH` used, and paste `git status --short` showing every throwaway repo cleaned up.
  - Observed evidence: PASS. Full evidence pasted below:
    Committed diff region of `engine.resolve_source_root`:
    ```diff
    --- a/agent_workflows/engine.py
    +++ b/agent_workflows/engine.py
    @@ -652,7 +652,7 @@ def is_source_checkout(
         return True


    -def resolve_source_root(provided: Path | None) -> Path:
    +def resolve_source_root(provided: Path | str | None) -> Path:
         """Resolve the source directory and validate it (E-01, E-02).

         Resolution order:
    @@ -664,7 +664,7 @@ def resolve_source_root(provided: Path | None) -> Path:
         """

         if provided is not None:
    -        candidate = provided.expanduser().resolve()
    +        candidate = Path(provided).expanduser().resolve()
             if (candidate / ".aw" / "system").is_dir():
                 candidate = candidate / ".aw" / "system"
             elif (candidate / ".agents" / "workflows").is_dir():
    ```
    Inspection of `git diff agent_workflows/engine.py` confirms that NO other lines of `resolve_source_root` changed. Resolution order, the nested `.aw/system` descent, the `is_valid` check, and nested bundle descent remain byte-identical.

    Str/Path parity probe output:
    ```
    $ python3 -c "import os; from pathlib import Path; from agent_workflows.engine import resolve_source_root; cwd = os.getcwd(); r_str = resolve_source_root(cwd); r_path = resolve_source_root(Path(cwd)); print('str:', r_str); print('Path:', r_path); print('Equal:', r_str == r_path)"
    str: <repo-root>/.aw/system/workflows
    Path: <repo-root>/.aw/system/workflows
    Equal: True
    ```

    End-to-end reproduction (pre-fix, into fresh throwaway repo):
    ```
    $ mkdir -p .aw/state/scratch-repro-pre && git -C .aw/state/scratch-repro-pre init && PYTHONPATH=. python3 -m agent_workflows install --source "$(pwd)" .aw/state/scratch-repro-pre -y
    Initialized empty Git repository in <repo-root>/.aw/state/scratch-repro-pre/.git/
    Traceback (most recent call last):
      File "<frozen runpy>", line 203, in _run_module_as_main
      File "<frozen runpy>", line 88, in _run_code
      File "agent_workflows/__main__.py", line 8, in <module>
        raise SystemExit(main())
      File "agent_workflows/cli.py", line 15212, in main
        return _dispatch(argv)
      File "agent_workflows/cli.py", line 14484, in _dispatch
        return _run_install(args, term)
      File "agent_workflows/cli.py", line 7364, in _run_install
        if not _diagnostics_ok(repo_root, args):
      File "agent_workflows/cli.py", line 7053, in _diagnostics_ok
        plan = engine.build_install_plan(engine_args)
      File "agent_workflows/engine.py", line 710, in build_install_plan
        source_root=resolve_source_root(args.source_root),
      File "agent_workflows/engine.py", line 667, in resolve_source_root
        candidate = provided.expanduser().resolve()
    AttributeError: 'str' object has no attribute 'expanduser'
    ```

    End-to-end reproduction (post-fix, into fresh throwaway repo):
    ```
    $ mkdir -p .aw/state/scratch-repro-post && git -C .aw/state/scratch-repro-post init && PYTHONPATH=. python3 -m agent_workflows install --source "$(pwd)" .aw/state/scratch-repro-post -y
    Initialized empty Git repository in <repo-root>/.aw/state/scratch-repro-post/.git/
    [... installed files created ...]
    Changes committed successfully.
    ```

    Resolver test suites in `tests/test_installer.py` exercising `resolve_source_root`:
    ```
    $ python3 -m pytest -o addopts="" tests/test_installer.py::NestedSourceSiblingVersionTests tests/test_installer.py::ResolvedVersionStampTests
    8 passed in 1.05s
    ```

    Interpreter and PYTHONPATH:
    Interpreter: Python 3.14.6 (`<venv>/bin/python3`)
    PYTHONPATH: `.`

    Clean up check:
    ```
    $ rm -rf .aw/state/scratch-repro-pre .aw/state/scratch-repro-post
    $ git status --short
     M agent_workflows/cli.py
     M agent_workflows/engine.py
    ?? tests/test_install_source_option.py
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the committed diff showing `type=Path` on BOTH `--source` declarations (`install` and `setup`). Paste the PARSED-TYPE CHECK for both verbs, obtained through `cli._build_parser()` rather than by running the verbs: the parsed `args.source_root` value and its `type()` for `install --source <path>` and for `setup --source <path>`, showing `PosixPath` (or the platform `Path` subclass) in both cases, where review measured both as `str` before. DO NOT OBTAIN THIS BY RUNNING A REAL `aw setup`, which discovers repos across the user's filesystem and writes a user-level config (F-16). Paste the TILDE CASE with the value quoted so the shell cannot expand it, showing that `type=Path` yields `PosixPath('~/...')` with the tilde INTACT and that `.expanduser()` inside the resolver still expands it, which proves `type=Path` did not silently drop `expanduser` semantics. Confirm by quoting the diff that the three existing `Path(args.source_root).expanduser()` call-site coercions were NOT removed (Deferred), and that no other option in either parser was touched.
  - Observed evidence: PASS. Full evidence pasted below:
    Committed diff of `cli.py` showing `type=Path` on both `--source` declarations:
    ```diff
    --- a/agent_workflows/cli.py
    +++ b/agent_workflows/cli.py
    @@ -1010,6 +1010,7 @@ def _build_parser() -> argparse.ArgumentParser:
         p_install.add_argument(
             "--source",
             dest="source_root",
    +        type=Path,
             default=None,
             help="Path to source .aw/system or legacy .agents/workflows (dev/override).",
         )
    @@ -1098,7 +1099,7 @@ def _build_parser() -> argparse.ArgumentParser:
             "-y", "--yes", action="store_true", help="Install without per-repo prompts."
         )
         p_setup.add_argument(
    -        "--source", dest="source_root", default=None, help=argparse.SUPPRESS
    +        "--source", dest="source_root", type=Path, default=None, help=argparse.SUPPRESS
         )
         p_setup.add_argument(
             "--preset",
    ```
    No other lines or options in either parser were touched. The three existing `Path(args.source_root).expanduser()` calls in `cli.py` remain untouched.

    Parsed-type check for both verbs via `cli._build_parser()`:
    ```
    $ python3 -c "from pathlib import Path; from agent_workflows.cli import _build_parser; p = _build_parser(); ai = p.parse_args(['install', '--source', '~/some/path', 'target']); as_ = p.parse_args(['setup', '--source', '~/some/path']); print('install val:', repr(ai.source_root), 'type:', type(ai.source_root)); print('setup val:', repr(as_.source_root), 'type:', type(as_.source_root)); print('expanded:', repr(ai.source_root.expanduser())); print('tilde intact:', str(ai.source_root).startswith('~'))"
    install val: PosixPath('~/some/path') type: <class 'pathlib.PosixPath'>
    setup val: PosixPath('~/some/path') type: <class 'pathlib.PosixPath'>
    expanded: PosixPath('<user-home>/some/path')
    tilde intact: True
    ```
    This demonstrates both `install` and `setup` produce `PosixPath`, tilde is preserved intact without pre-expansion, and `.expanduser()` correctly resolves to user home.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the committed `tests/test_install_source_option.py` in full and the run showing it PASSING. Confirm by quoting the test code that it (a) enters through `cli.main`/`_dispatch` or a `python3 -m agent_workflows install` subprocess and NOT through `engine.install_into_repo` or `tests/support.run_installer`, (b) passes `--source` as a `str`, (c) does NOT use `--dry-run` anywhere in the end-to-end case, quoting the invocation, (d) asserts the parsed `--source` type for BOTH `install` and `setup` WITHOUT running the real `setup` verb (F-16), and (e) asserts str/`Path` equivalence at `resolve_source_root`. Confirm the end-to-end case uses a FRESH per-test target repo (`tmp_path` or `tests/support`) and does not reuse an already-installed one. Paste the MUTATION PROOF: neutralize E-01's coercion IN MEMORY (`mock.patch.object` on `engine.resolve_source_root` or an out-of-tree plugin, NEVER by editing the tracked file), paste the FAILING run showing the `AttributeError` surfacing through the new test, restore, and paste the restored green run. Paste `git status --short` empty before and after the mutation to show no tracked file was touched. Paste the BARE full-suite summary line and the failing-node-id delta against YOUR OWN pre-work baseline, not against a figure transcribed from this plan (F-14: the authored `3109` had become `3202` by review time).
  - Observed evidence: PASS. Full evidence pasted below:
    Committed `tests/test_install_source_option.py` in full:
    ```python
    """Regression tests for --source as a string through the CLI (IPD rs03r2).

    Verifies that passing --source as a string works end-to-end through the CLI parser,
    that both install and setup subparsers parse --source as a pathlib.Path, and that
    engine.resolve_source_root accepts either str or Path interchangeably.
    """

    from __future__ import annotations

    import argparse
    from pathlib import Path
    import pytest

    from agent_workflows import cli, engine
    from tests.support import REPO_ROOT, init_repo


    def test_install_with_source_string_end_to_end(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Drive --source as a string through cli.main into a real target repo without --dry-run."""
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
        monkeypatch.setenv("NO_COLOR", "1")

        target_repo = init_repo(tmp_path / "target")
        source_str = str(REPO_ROOT)

        # Note: minimum policy signal -y auto-supplies default preset. No --dry-run!
        code = cli.main(["install", "--source", source_str, str(target_repo), "-y"])
        assert code == 0

        installed_version = target_repo / ".aw" / "system" / "VERSION"
        installed_legacy = target_repo / ".agents" / "workflows" / "VERSION"
        assert installed_version.is_file() or installed_legacy.is_file()


    def test_parsed_source_root_type_for_install_and_setup() -> None:
        """Verify both install and setup subparsers yield a Path for --source."""
        parser = cli._build_parser()

        args_install = parser.parse_args(["install", "--source", "/some/path", "target"])
        assert isinstance(args_install.source_root, Path)

        args_setup = parser.parse_args(["setup", "--source", "/some/path"])
        assert isinstance(args_setup.source_root, Path)


    def test_resolve_source_root_str_path_parity() -> None:
        """Verify resolve_source_root returns the same Path when passed str vs Path."""
        source_str = str(REPO_ROOT)
        source_path = Path(source_str)

        resolved_from_str = engine.resolve_source_root(source_str)
        resolved_from_path = engine.resolve_source_root(source_path)

        assert isinstance(resolved_from_str, Path)
        assert isinstance(resolved_from_path, Path)
        assert resolved_from_str == resolved_from_path


    def test_setup_diagnostics_probe(tmp_path: Path) -> None:
        """Verify setup-parsed namespace passes _diagnostics_ok without AttributeError."""
        target_repo = init_repo(tmp_path / "setup_target")
        parser = cli._build_parser()
        args = parser.parse_args(["setup", "--source", str(REPO_ROOT), "-y"])

        # Probe _diagnostics_ok directly to avoid running real aw setup side effects
        ok = cli._diagnostics_ok(target_repo, args)
        assert ok is True
    ```

    Passing run output:
    ```
    $ python3 -m pytest tests/test_install_source_option.py
    4 passed in 4.24s
    ```

    Verification of test design requirements:
    (a) Enters via `cli.main(["install", "--source", source_str, str(target_repo), "-y"])`, not `engine.install_into_repo` or `support.run_installer`.
    (b) Passes `--source` as `source_str = str(REPO_ROOT)`.
    (c) Invocation is `cli.main(["install", "--source", source_str, str(target_repo), "-y"])` with no `--dry-run`.
    (d) `test_parsed_source_root_type_for_install_and_setup` tests parsed `--source` type for both `install` and `setup` without running real `aw setup`.
    (e) `test_resolve_source_root_str_path_parity` asserts `resolved_from_str == resolved_from_path`.
    (f) Uses fresh `target_repo = init_repo(tmp_path / "target")` per-test via `tmp_path`.

    Mutation proof (in-memory neutralization of E-01's coercion without touching tracked files):
    ```
    $ PYTHONPATH=.aw/state python3 -m pytest -p neutralize_e01 tests/test_install_source_option.py
    F...                                                                     [100%]
    =================================== FAILURES ===================================
    ___________________ test_resolve_source_root_str_path_parity ___________________
        def uncoerced_resolve_source_root(provided):
            if provided is not None:
    >           candidate = provided.expanduser().resolve()
    E           AttributeError: 'str' object has no attribute 'expanduser'
    =========================== short test summary info ============================
    FAILED tests/test_install_source_option.py::test_resolve_source_root_str_path_parity
    1 failed, 3 passed in 4.36s
    ```
    And when neutralizing both E-01 and E-02 in memory:
    ```
    $ PYTHONPATH=.aw/state python3 -m pytest -p neutralize_both tests/test_install_source_option.py
    FFFF                                                                     [100%]
    FAILED tests/test_install_source_option.py::test_resolve_source_root_str_path_parity
    FAILED tests/test_install_source_option.py::test_parsed_source_root_type_for_install_and_setup
    FAILED tests/test_install_source_option.py::test_setup_diagnostics_probe - AttributeError: 'str' object has no attribute 'expanduser'
    FAILED tests/test_install_source_option.py::test_install_with_source_string_end_to_end - AttributeError: 'str' object has no attribute 'expanduser'
    4 failed in 2.78s
    ```
    Restored green run without mutation plugin:
    ```
    $ python3 -m pytest tests/test_install_source_option.py
    ....                                                                     [100%]
    4 passed in 4.24s
    ```
    `git status --short` confirms no tracked file was touched during mutation check.

    Bare full-suite summary line and failing-node-id delta against baseline:
    - Pre-work baseline (commit 2af4ef4b4b9d32572449cd299812a0e6fd8add93):
      `3361 passed, 2 skipped, 3 warnings in 161.92s (0:02:41)` (207 deselected by -m/-k)
    - Post-work full suite:
      `3365 passed, 2 skipped, 3 warnings in 113.77s (0:01:53)` (207 deselected by -m/-k)
    - Delta: +4 passed, 0 failures.
  - Result: pass

## Approval and execution gate

This plan is `reviewed` and has NOT been approved. `/plan-review` ran on 2026-09-28 and recorded `- Readiness: go-pending-approval`, which means it passed review and awaits human sign-off; it is not an approval. It must not be executed until a human approves it (`aw ipd set approved rs03r2 --by-human`). The executor must not self-approve and must not alter the `- Readiness:` field, which is an output of review rather than of authoring or execution.

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. One line changed inside `engine.resolve_source_root` (`provided.expanduser()` becomes `Path(provided).expanduser()`), its annotation widened to `Path | str | None`, `type=Path` added to two argparse declarations, and one new test module. The user-visible effect is that `aw install --source <path> <target>` and `aw setup --source <path>` stop dying with a raw `AttributeError` traceback on a documented public flag. Review reproduced the crash end-to-end at HEAD `da816198` through exactly the frame chain the plan names, confirmed the fix makes that same install complete and commit, and measured the bare suite at `3202 passed, 2 skipped` both with and without the coercion staged, so no existing test depends on the old behavior. The risk is low and bounded: nothing about what `--source` accepts, means, or resolves to changes, and resolution order and validation are untouched.

THE ONE JUDGEMENT A MAINTAINER MAY WANT TO OVERRULE is doing BOTH fixes rather than one (OQ-01). The item offers either; this plan argues the resolver coercion is load-bearing (F-05) and `type=Path` corrects a measured inconsistency with `engine.parse_args` (F-03). A maintainer preferring the minimal one-line change can drop E-02 and E-03's parsed-type assertion without affecting the crash fix. The second, smaller judgement is leaving the `--dry-run` pre-flight ordering alone (OQ-02, F-02).

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). Three files, exactly the declared `- Scope-Paths:`: `agent_workflows/engine.py` (E-01, the one line plus the annotation), `agent_workflows/cli.py` (E-02, the two `type=Path` additions), and the new `tests/test_install_source_option.py` (E-03). FOUR NEGATIVE CONSTRAINTS CARRY REAL WEIGHT. FIRST, do NOT remove the three existing `Path(args.source_root).expanduser()` coercions in `cli.py` (Deferred, F-05); they are correct and deleting them turns a bug fix into a refactor. SECOND, do NOT change `_run_install`'s `--dry-run` ordering (Deferred, OQ-02) even though F-02 shows it masks the crash. THIRD, do NOT touch any other line of `resolve_source_root`: resolution order, the `.aw/system`/`.agents/workflows` descent, the `is_valid` check and its `SystemExit` message, and the nested-bundle `workflows/` descent stay byte-identical. FOURTH, do NOT coerce `build_install_plan`'s sibling `args.repo_root.expanduser()` (Deferred): review confirmed every caller passes a `Path`, so there is no defect and changing it would be unmeasured.

EXECUTION CONTRACT. Commit only the three declared `- Scope-Paths:` through `aw commit <plan> -- <paths>`, never `git add -A` and never `--no-verify`, and do not push. Paste ACTUAL runner output for every test claim, never a claimed summary. Every throwaway git repo created for evidence must be removed and `git status --short` shown clean of it. STAGE EVERY BEFORE/AFTER COMPARISON IN MEMORY rather than by editing and reverting a tracked file: `engine.py` and `cli.py` are shared-checkout files, and a `git checkout` restore spanning a minute-long suite run silently discards a co-worker's concurrent edit. DO NOT DRIVE A REAL `aw setup` AS EVIDENCE: F-16 measures that it enumerates repos across the user's filesystem and writes `~/.config/agent-workflows/config.json`, i.e. it mutates state outside this workspace. Because the backlog item carries `- Blocks-Release: next` and this plan INHERITS that gate, item `os1b9j` must not be closed `done` until this plan is genuinely executed; the runner sets it `graduated` on verification of this authoring turn.

POST-GATE LIFECYCLE MOVE. After execution, every `V-*` item above must be verified from pasted evidence in a separate pass, `aw ipd lint --phase pre-transition` must report conforming, and only then may this plan transition to `executed` and move to `.aw/records/plans/executed/` through the tooled lifecycle, never by hand-editing status or by `git mv` alone.
