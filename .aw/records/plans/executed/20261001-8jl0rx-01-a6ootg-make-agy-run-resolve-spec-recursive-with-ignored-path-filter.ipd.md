# IPD: Make agy_run.resolve_spec recursive with ignored-path filtering

- Date: 2026-10-01
- Kind: child
- Concern: `agy_run.resolve_spec` enumerates candidate specifications with a NON-RECURSIVE `d.glob("*.md")` over `.agents/docs/specs` and `.aw/records/specs`, so after the `specdirs` migration moved every specification into a status subdirectory (`draft/`, `to-review/`, `reviewed/`, `approved/`, `implementing/`, `implemented/`, `deferred/`, `superseded/`) the glob sees only `README.md` at the specs root and resolves ZERO of this repository's 40 specifications. Measured in this lane at HEAD `e132c1f43`: `aw agy exec --spec pqsx96` exits 2 with `error: No specification matching 'pqsx96' found.`, and the in-process call fails identically for a bare id6 (`pqsx96`), for a bare filename (`20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md`), and for a flat-looking full path (`.aw/records/specs/<name>.spec.md`), which are the three forms the function's own matching branch exists to serve. Spec Mode is therefore unreachable by every selector except an EXACT existing path, which short-circuits at the `direct.is_file()` early return before the broken glob is consulted. `specs._spec_files` already fixed this exact defect on the other spec reader, and its docstring records that `rglob` ALONE is not the complete fix: non-recursion was masking the absence of an ignored-path filter, because a flat glob cannot descend into a gitignored subdirectory, so a recursive walk must also filter through `artifact_core.is_ignored_path` or it will start returning box-local specs that are never committed.
- Scope: Replace the non-recursive glob in `agy_run.resolve_spec` by DELEGATING enumeration to `specs._spec_files`, the single existing definition of "which files are this repository's specs", so the recursive walk, the ignored-path filter, the `README.md`/`INDEX.md`/`STATUS.md` skip, the legacy `.agents/docs/specs` read path and the resolved-path dedup all come from one place rather than being re-implemented a second time. Add the behavioral test coverage the symbol has never had (measured: zero tests reference `resolve_spec`'s subdirectory case, which is why this shipped broken), placing it under `tests/` because `pyproject.toml` sets `testpaths = ["tests"]` and CI runs `python -m pytest tests/`, so the existing `tools/test_agy_run.py` module is NOT collected by the default suite or by CI. Does NOT change the matching semantics (exact-name-or-substring), the ambiguity error, the `direct.is_file()` early return, the function signature, or any caller. Does NOT fix the same latent defect in the sibling `resolve_ipd` (measured and real, but it needs a different enumeration source and is handed off, see the deferred section).
- Scope-Paths: agent_workflows/agy_run.py, tests/test_agy_run_resolve_spec_recursive.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: 8jl0rx
- Blocks-Release: next
- Set: 8jl0rx
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: a6ootg

## Workflow history
- 2026-10-03 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: a6ootg verified (set 8jl0rx, attempt 1).
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006 (review record 20261002-8jl0rx-01-a6ootg-...review.md).
- 2026-10-02 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): plan-review revisions applied; see review record

- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `8jl0rx`, graduating it. Every claim the item makes was RE-MEASURED in this lane at HEAD `e132c1f43` rather than carried over, and all three of its reported failure forms reproduce exactly (bare id6, bare filename, flat-looking full path), plus the end-to-end `aw agy exec --spec pqsx96` exit 2 the item describes but does not paste. FIVE FACTS WERE MEASURED THAT THE ITEM DOES NOT STATE AND THAT CHANGE THE WORK. FIRST (F-03), the fix should DELEGATE to `specs._spec_files` rather than copy its `rglob`-plus-filter body: the item's "fix precedent" wording points at the right code but a second copy would be a second definition of the same set, and delegation was measured to produce a set differing from a naive recursive walk by exactly one file, `README.md`, whose exclusion is itself a fix (today `resolve_spec(root, "README")` RESOLVES THE SPECS README as if it were a specification). SECOND (F-04), `tools/test_agy_run.py` is NOT COLLECTED by the default suite or by CI (`testpaths = ["tests"]`, CI runs `pytest tests/`), so coverage added there would be invisible to every gate; this is a second, independent reason the defect went undetected and it decides where E-02 puts the new module. THIRD (F-05), the existing `tools/test_agy_run.py::test_resolve_spec_by_path_and_name` fixture plants a spec under the LEGACY `.agents/docs/specs` root, and `specs._spec_files` was driven against that exact fixture shape and returns it, so delegation keeps that test green rather than trading one broken root for another. FOURTH (F-06), the sibling `resolve_ipd` carries the SAME non-recursive defect via `_candidate_plans`, latent today only because no plan is sharded yet, and `aw archive plans` creates `YYYYMM/` shards by design; it is deliberately NOT fixed here and is handed off, because plans have no `_spec_files` equivalent to delegate to. FIFTH (F-07), delegation costs about 100ms warm on this repository's 40 specs, which is irrelevant inside a command that then spawns an interactive agent CLI, so no caching is warranted and none is added. THE ITEM LEFT NO BLOCKING QUESTION OPEN and this plan opens none: OQ-01 (delegate versus copy) and OQ-02 (is the `README.md` behavior change acceptable) are both resolved from repository evidence at authoring.

## Goal

Make Spec Mode reachable again. After this plan `aw agy exec --spec <id6>`, `--spec <bare-filename>` and the positional auto-detection path all resolve a specification that lives in a status subdirectory, which is where every specification in this repository now lives, and they do so through the ONE enumeration helper that already knows how to walk the specs tree safely, so the next migration that moves specs again cannot break this caller without breaking that helper too.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: establish the failing baseline before changing any byte

- [x] E-01 CAPTURE THE REPRODUCTION AT THE BASE COMMIT, before any edit, so the fix is demonstrated against a measured failure rather than asserted.

  NEVER LAUNCH A REAL AGENT FROM A PROBE. `agy` is on PATH on the authoring box, and `agy_run.run` calls `run_agy` as soon as `resolve_mode_and_target` returns, so a probe that RESOLVES (every after-fix probe, and the positional before-fix probe, which resolves to mode `prompt`) would start a real Antigravity turn. Every CLI probe in this plan therefore runs as `aw agy exec --agy <stub> --no-audit ...`, where `<stub>` is a throwaway executable created outside the repo (for example under the system temp dir) that prints its argv to stderr and exits 1; the `Executing [<mode> mode] <target> in Antigravity...` line `agy_run.run` prints before calling `run_agy` is the observation. Measured at review: `--spec pqsx96` exits 2 with the not-found error, and positional `pqsx96` prints `Executing [prompt mode] pqsx96 in Antigravity...` then reaches the stub. The stub run leaves a `tmp/antigravity/agy-*.jsonl` event log (gitignored `tmp/`); delete it afterwards.

  CAPTURE FOUR INVOCATIONS on the live tree and keep their verbatim output: (1) `aw agy exec --agy <stub> --no-audit --spec pqsx96` (expect exit 2 and `error: No specification matching 'pqsx96' found.`); (2) the in-process `agy_run.resolve_spec(Path(".").resolve(), "pqsx96")` raising (use a RESOLVED root, as production does via `agy_run.repository_root`; see F-10 for why a relative root is not a faithful probe after the fix) `ScriptError`; (3) the same for the bare filename `20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md`; (4) the same for the flat-looking path `.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md`. These are the three selector forms the item reports plus the end-to-end command, and they are the before half of V-01.

  ALSO CAPTURE THE TWO CASES THAT MUST KEEP WORKING, because they bound the blast radius: the EXACT existing path `.aw/records/specs/draft/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md` (which resolves today through the `direct.is_file()` early return, NOT through the glob) and the full `tools/test_agy_run.py` module (44 passed at authoring and at review; context only, the bar is "every collected test passes"). Re-derive the spec's real subdirectory at execution rather than trusting the path above: its status may have advanced, and a stale path would make this item appear to fail for the wrong reason.
  - Depends on: none
  - Expected outcome: four pasted failures and two pasted passes at the base commit, forming the discriminating baseline for V-01.
  - Execution state: performed

- [x] E-02 WRITE `tests/test_agy_run_resolve_spec_recursive.py` AND SHOW IT RED BEFORE ANY PRODUCTION EDIT.

  PUT IT UNDER `tests/`, NOT IN `tools/test_agy_run.py`. This is the point of F-04 and it is not a style preference: `pyproject.toml` sets `testpaths = ["tests"]` and `.github/workflows/tests.yml` runs `python -m pytest tests/`, so a test added to the `tools/` module is run by NOBODY unless a human names the file. Measured at authoring: a bare `python3 -m pytest --collect-only` collects `tests/test_agy_runipd_cli.py` and does not collect `tools/test_agy_run.py` at all. Coverage that no gate runs is how this defect survived; do not reproduce that.

  DRIVE A FIXTURE REPOSITORY, NOT THE LIVE TREE, so every assertion is about a spec the test itself created and no count depends on this repository's drifting records. `tools/test_agy_run.py`'s `AgyRunTargetResolutionTests.setUp` has the fixture shape to copy (it builds a temp repo via its `init_repo` helper and plants plan, spec and prompt files); note the fixture must be a real git repo because `artifact_core.get_ignored_dirs` reads `.gitignore` and `.git/info/exclude`.

  ASSERT SIX THINGS, each one a measured failure or a measured invariant. (1) A spec planted in a STATUS SUBDIRECTORY (`.aw/records/specs/approved/`) resolves by bare id6; today this raises `ScriptError`. (2) The same spec resolves by bare filename. (3) A spec planted in the LEGACY root `.agents/docs/specs/` still resolves by bare filename, which is the `tools/test_agy_run.py` fixture shape and must not regress (F-05). (4) GITIGNORED specs are NOT returned, asserted TWICE because the two cases exercise different mechanisms (F-11): (4a) a spec under `.aw/records/specs/untracked/` (the shipped `.aw/.gitignore` pattern `records/*/untracked/`), which `artifact_core.is_ignored_path` rejects by its hardcoded `"untracked" in rel_parts` check whether or not any git rule exists; and (4b) a spec under a directory with NO `untracked` component (for example `.aw/records/specs/scratch/`) that is ignored ONLY by a real git rule written to the fixture's `.git/info/exclude`, which is the case that proves the `git ls-files --ignored` path of `get_ignored_dirs` is consulted. Both are the assertions a naive `rglob`-only fix fails. (5) `README.md` at the specs root is NOT resolvable as a specification, pinning OQ-02's decided behavior change. (6) A spec planted in the records backend's OUT-OF-REPO specs dir (obtain it from `record_producers.resolve_record_read_paths("specs", target_repo=str(root))[0]` under the pytest-sandboxed `AW_HOME`, and assert it lies outside `root` before planting) is NOT resolvable and the call raises `ScriptError`, not `ValueError` (F-10).

  ALSO ASSERT THE PRESERVED SEMANTICS so the delegation cannot quietly widen the contract: an ambiguous selector still raises with the `is ambiguous` message and lists its candidates, and an exact existing path still resolves through the early return.

  NO STATIC ANALYSIS. Do not read `agent_workflows/agy_run.py` from the test, do not assert that `rglob` appears in its source, do not count callers. GUIDING_PRINCIPLES P16 forbids code-pinning tests outright; every assertion here must call `resolve_spec` (or drive the CLI) and assert on its real return value or raised exception.
  - Depends on: E-01
  - Expected outcome: a new collected test module whose subdirectory assertions (1) and (2) FAIL at the base commit and whose legacy-root, gitignored (4a/4b), out-of-repo (6), ambiguity and exact-path assertions PASS there (the base glob cannot see subdirectories or out-of-repo dirs at all, so those exclusions hold vacuously before the fix and become meaningful only after it), and whose README assertion (5) FAILS at the base commit (`resolve_spec(root, "README")` returns the specs README today), with that red output captured verbatim.
  - Execution state: performed

### Task group 2: fix the enumeration at its one definition

- [x] E-03 DELEGATE ENUMERATION TO `specs._spec_files` IN `agy_run.resolve_spec`.

  REPLACE the candidate-building block (the loop over `(root / ".agents" / "docs" / "specs", root / ".aw" / "records" / "specs")` calling `d.glob("*.md")`, followed by `candidates = sorted(set(candidates))`) with a call to `specs._spec_files(root)`. Import it the way this module already imports its one package sibling, LOCALLY inside the function rather than at module top level: `agy_run` imports `agy_sessions` locally inside a function and has no top-level `agent_workflows` import at all, so a module-level import here would be the first and would change this module's import graph for no benefit.

  DO NOT COPY `_spec_files`' BODY. That is the whole point: a second `rglob`-plus-`is_ignored_path` implementation would be a second definition of "which files are this repository's specs", and the next change to the specs layout would then have to find both. Delegation also inherits, for free and without re-deriving them, the four behaviors that helper's docstring records as COUPLED: the recursive walk, the `is_ignored_path`/`get_ignored_dirs` filter the recursion makes mandatory, the `README.md`/`INDEX.md`/`STATUS.md` skip, and the `resolve_record_read_paths` read-path resolution that keeps the legacy `.agents/docs/specs` root visible.

  LEAVE THE MATCHING BRANCH EXACTLY AS FOUND: `[p for p in candidates if p.name == supplied.name or value in p.name]`, both error messages, and the `direct.is_file()` early return above it. This plan fixes WHICH FILES are candidates and changes nothing about how a selector is matched against them. State that boundary in a comment, with the reason, so a later reader does not mistake the untouched substring matching for an oversight.

  WRITE A COMMENT THAT RECORDS WHY DELEGATION RATHER THAN RECURSION, citing backlog `8jl0rx` and naming the coupling: that `rglob` alone would start returning gitignored specs because non-recursion was masking the missing filter. A bare `rglob` swap with no comment is the fix a future reader would most plausibly "simplify" back into a one-liner.

  KEEP THE CANDIDATE SET INSIDE THE REPOSITORY ROOT (F-10). `specs._spec_files` resolves its primary root through `record_producers.resolve_record_read_paths`, which follows the configured records backend, so under a `home` or `companion` backend it returns specs OUTSIDE `root`. Every downstream consumer of `resolve_spec` assumes an in-repo path: the ambiguity branch renders `p.relative_to(root)`, both callers wrap the result in `agy_run.relative_posix`, and the Turn-1 prompt hands the agent a repo-relative path. Measured at review in a temp git repo with an isolated `AW_HOME`: a spec planted in the backend's specs dir IS returned by `_spec_files`, and `relative_posix(root, <it>)` raises `ValueError`, which is not a `ScriptError` and so escapes the positional caller's `except ScriptError` as a traceback. So after calling the helper, normalize and fence its output: `candidates = sorted({p.resolve() for p in specs._spec_files(root)})`, then keep only `p` with `p.is_relative_to(root.resolve())` (available on the repository's 3.9 floor), and render the ambiguity list relative to `root.resolve()`. This preserves today's scope (the old loop only ever looked inside `root`) and is the one deliberate narrowing of the helper's output; say so in the comment. The matching expression and both message texts are still left as found. Review prototype of exactly this shape, run over the fixture and the live tree: `abc123` and its bare filename resolve to `.aw/records/specs/approved/...`; `README`, the untracked-dir spec, the `.git/info/exclude`-ignored spec and the out-of-repo backend spec all raise `No specification matching ... found.`; `abc12` and `attention` raise `is ambiguous` listing two repo-relative candidates; live `pqsx96` and the flat-looking path both resolve to `.aw/records/specs/draft/20260828-pqsx96-...spec.md`.
  - Depends on: E-02
  - Expected outcome: `resolve_spec` resolves specs in status subdirectories, in the legacy root, by id6 and by bare filename; gitignored specs, `README.md` and specs outside the repository root are excluded; the matching expression and both error message texts are unchanged.
  - Execution state: performed

### Task group 3: prove nothing else moved

- [x] E-04 PROVE THE CALLERS AND THE EXISTING MODULE ARE UNAFFECTED.

  `resolve_spec` HAS EXACTLY TWO CALLERS, both in `resolve_mode_and_target`: the explicit `--spec` branch (`args.spec_target`) and the positional auto-detection fallback, which calls it inside a `try`/`except ScriptError` and falls through to treating the string as an INLINE PROMPT when it raises. That second path is why the defect is worse than a plain error: a mistyped-looking-but-valid spec selector is currently not reported as a missing spec, it is silently executed as a prompt. Exercise BOTH callers after the fix and paste the resolved mode for each, and confirm the auto-detection path now returns mode `spec` where it previously returned mode `prompt`. Do it two ways: in process, `agy_run.resolve_mode_and_target(<resolved root>, agy_run.parse_args([...]))` for `["--spec", "pqsx96"]` and `["pqsx96"]` (measured before the fix at review: `ERR No specification matching 'pqsx96' found.` and `('prompt', 'pqsx96', '')`); and end to end, `aw agy exec --agy <stub> --no-audit pqsx96` per E-01's stub rule, NEVER against the real `agy`, reading the `Executing [spec mode] ...` line.

  RUN `tools/test_agy_run.py` EXPLICITLY, by name, since the default suite does not collect it (F-04). Its `test_resolve_spec_by_path_and_name` is the legacy-root fixture this delegation must not break (F-05). Paste its full result; the bar is that it passes with zero failures at the count it has at E-01 (44 at authoring and at review, context only).
  - Depends on: E-03
  - Expected outcome: both callers exercised with pasted modes, the positional path demonstrably returning `spec` instead of `prompt`, no real agent launched, and `tools/test_agy_run.py` passing with zero failures at its E-01 count.
  - Execution state: performed

- [x] E-05 RUN THE FULL SUITE BARE AND REPORT THE FAILURE-SET DELTA AGAINST A BASELINE YOU ESTABLISH YOURSELF.

  Run `python3 -m pytest` with NO added flags. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; `AGENTS.md` names the three flags not to add and the measured reason for each (`-n0` makes the suite several times slower, a second `-q` compounds to `-qq` and suppresses the very summary line this item requires pasted, `-p no:randomly` disables the order randomization that surfaces order dependence). Capture the summary line at the BASE commit before any edit and again at the end.

  THE BAR IS AN EMPTY FAILURE-SET DELTA, not a green run, and it must be stated as a SET OF TEST IDS rather than a count comparison: this suite is large, a pre-existing environmental failure is not this plan's to fix, and a pre-existing failure plus a new regression can net to an unchanged count. A failure present AFTER and absent BEFORE blocks the transition.
  - Depends on: E-04
  - Expected outcome: two pasted bare-suite summary lines and an explicitly empty failure-set delta stated as test ids.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation here names a symbol or quotes the text it refers to.
- THE BARE SUITE IS THE CONTRACT. `AGENTS.md` requires `python3 -m pytest` with no added flags and names the three flags not to add. E-05 follows that literally.
- `testpaths = ["tests"]` MEANS `tools/` TESTS ARE NOT A GATE. `pyproject.toml` scopes collection to `tests/`, and `.github/workflows/tests.yml` runs `python -m pytest tests/`. A test outside `tests/` is documentation, not enforcement. This decided E-02's file placement and is recorded as F-04 because it is half the causal story of the defect.
- NO CODE-PINNING TESTS (GUIDING_PRINCIPLES P16). A test may not read production source, assert a symbol exists, or count callers; it must exercise the code and assert on real return values, exceptions, outputs and side effects. E-02 is therefore a direct-call and CLI-driving module over a fixture repo, not a source scan, and this plan deliberately does not pin the word `rglob` anywhere.
- ONE DEFINITION PER CONCEPT. `specs._spec_files`' docstring exists precisely to record that its recursion and its ignore filter are COUPLED and must not be separated. Re-implementing that pairing in a second module would be the drift this repository repeatedly pays for, which is why E-03 delegates.
- `agy_run` IMPORTS PACKAGE SIBLINGS LOCALLY. The module's only `agent_workflows` import is `from agent_workflows import agy_sessions` inside a function body; there is no top-level package import. E-03 matches that existing shape rather than introducing the module's first top-level sibling import.

## Findings

| id | finding | evidence |
| --- | --- | --- |
| F-01 | THE DEFECT REPRODUCES EXACTLY AS FILED, IN ALL THREE SELECTOR FORMS, AND END TO END. `aw agy exec --spec pqsx96` exits 2 printing `error: No specification matching 'pqsx96' found.`. In process, `resolve_spec` raises `ScriptError` for the bare id6 `pqsx96`, for the bare filename `20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md`, and for the flat-looking path `.aw/records/specs/<that name>`. The cause is mechanical: the candidate loop calls `d.glob("*.md")` on the two specs roots, and this repository's `.aw/records/specs/` root contains exactly one `.md` file, `README.md`, with all 40 specs one level down in eight status subdirectories (`approved/` 12, `implemented/` 15, `superseded/` 3, `to-review/` 3, `deferred/` 2, `draft/` 2, `implementing/` 2, `reviewed/` 1). | All four invocations run in this lane at HEAD `e132c1f43`; the subdirectory census taken by listing each `.aw/records/specs/*/`. |
| F-02 | ONLY AN EXACT EXISTING PATH WORKS TODAY, AND THE FAILURE MODE OF THE POSITIONAL FORM IS SILENT MISROUTING RATHER THAN AN ERROR. `resolve_spec(root, ".aw/records/specs/draft/20260828-pqsx96-...spec.md")` succeeds, because `direct.is_file()` returns before the broken glob is reached; every non-path form fails. `resolve_mode_and_target` calls `resolve_spec` in TWO places, and the positional auto-detection call is wrapped in `try: ... except ScriptError: pass` followed by `return "prompt", target_str, ""`. So `aw agy exec pqsx96` does not report a missing spec: it feeds the literal string `pqsx96` to the agent as an inline prompt. That is why this is filed `bug` and gates the release rather than being a cosmetic resolver gap. | The successful path call and the failing bare-id6 call run in process; `resolve_mode_and_target`'s two call sites and its `except ScriptError: pass` fallback read. |
| F-03 | DELEGATING TO `specs._spec_files` IS STRICTLY BETTER THAN COPYING ITS BODY, AND THE SET DIFFERENCE IS EXACTLY ONE FILE. Measured by set-comparing resolved paths: `specs._spec_files(root)` returns 40 files; a naive recursive walk of the same two roots returns 41; the difference is `README.md`, present only in the naive set. So delegation fixes a SECOND latent defect in the same breath, since today `resolve_spec(root, "README")` resolves `.aw/records/specs/README.md` as though it were a specification (verified: it returns that path). The helper also already resolves read paths through `record_producers.resolve_record_read_paths` and appends the legacy `.agents/docs/specs` root unconditionally, which is the compatibility the hand-rolled loop was approximating with a hardcoded tuple. | `specs._spec_files` driven and set-differenced against an inline `rglob` walk of both roots; `resolve_spec(root, "README")` driven and returning the specs README; the helper's body and docstring read. |
| F-04 | `tools/test_agy_run.py` IS NOT COLLECTED BY THE DEFAULT SUITE OR BY CI, WHICH IS THE SECOND HALF OF WHY THIS SHIPPED BROKEN. `pyproject.toml` sets `testpaths = ["tests"]`; `.github/workflows/tests.yml` runs `python -m pytest tests/ -n auto -rfEs` and `python -m pytest tests/ -n auto -m slow`; `Makefile`'s `test` target runs `python3 -m pytest tests/`. A bare `python3 -m pytest --collect-only` matching on `test_agy_run` returns only `tests/test_agy_runipd_cli.py`. The module passes when named explicitly (44 passed) but no gate names it. The item attributes the miss to an incomplete grep and to `resolve_spec` having zero coverage; BOTH are true, and this is the mechanism that would have let coverage-shaped-but-uncollected tests give false assurance. It is why E-02 writes under `tests/`. | `--collect-only` run and grepped; `pyproject.toml`, `tests.yml` and `Makefile` read; `python3 -m pytest tools/test_agy_run.py -o addopts="" -q` run (44 passed in 1.50s). |
| F-05 | THE EXISTING FIXTURE PLANTS ITS SPEC IN THE LEGACY ROOT, AND DELEGATION KEEPS IT GREEN. `tools/test_agy_run.py`'s `AgyRunTargetResolutionTests.setUp` creates `.agents/docs/specs/20260810-01-feature.spec.md`, and `test_resolve_spec_by_path_and_name` resolves it both by path and by bare filename. Driven directly against a temp git repo of that exact shape, `specs._spec_files` RETURNS that file, and with a second spec added under `.aw/records/specs/approved/` it returns both. So the fix does not trade the broken new layout for a broken legacy one, and the one existing test of this symbol survives unmodified. This also means the legacy root is exercised by a test that no gate runs, which E-02 corrects by asserting the legacy case under `tests/`. | The fixture's `setUp` and test read; `specs._spec_files` driven against a reconstructed temp-repo fixture with the legacy spec alone and then with both. |
| F-06 | THE SIBLING `resolve_ipd` CARRIES THE SAME DEFECT, LATENT ONLY BECAUSE NO PLAN IS SHARDED YET. `agy_run._candidate_plans` calls `plans_base.glob("*.md")` over `.agents/plans/<state>` and `.aw/records/plans/<state>`, non-recursively. Measured: in a temp repo with an executed plan at `.aw/records/plans/executed/202609/<name>.ipd.md`, `resolve_ipd(root, "ab12cd", ("executed",))` raises `No IPD matching 'ab12cd' found`, while the exact path resolves. This is not hypothetical: `plans_archive`'s module docstring states it creates `YYYYMM/` shards INSIDE each terminal dir and that "the INDEX (Order 03) is recursive, so sharded plans stay visible", a guarantee `_candidate_plans` does not share. Today all five plan dispositions have zero subdirectories in this repository, so nothing is broken yet; the first `aw archive plans --apply` makes it real. NOT FIXED HERE: plans have no `_spec_files` equivalent to delegate to, so the honest fix is a separate decision about which plan-enumeration helper becomes canonical, and folding it in would double this plan's scope and its blast radius. Handed off. | `_candidate_plans` read; the sharded-plan reproduction run in a temp repo; `plans_archive`'s docstring and `_shard_target` read; subdirectory count taken for all five disposition dirs (0 each). |
| F-07 | THE DELEGATION'S COST IS IRRELEVANT AT THIS CALL SITE, SO NO CACHING IS WARRANTED. `specs._spec_files` on this repository measured 333ms cold and 104ms warm for 40 specs, against a flat glob that reads one directory. `resolve_spec` is called at most twice per invocation, from `resolve_mode_and_target`, during argument resolution of a command whose next action is to spawn an interactive agent CLI turn. A sub-second one-time resolution cost inside a command that then waits on a model is not user-perceptible, which is the test `AGENTS.md` sets for whether inefficiency is a defect. Stated explicitly so a reviewer does not ask for a cache and so the executor does not add one speculatively. | `specs._spec_files` timed twice in process; the two call sites in `resolve_mode_and_target` read. |
| F-08 | NO SPECIFICATION GOVERNS THIS ENUMERATION, SO NO SPEC AMENDMENT IS DUE. A grep across `.aw/records/specs/` for `agy_run`, `agy exec` and `Spec Mode` returns seven specs, all of which mention the runner family for other reasons (orchestrator retirement, midrun question surfacing, per-action model selection, deterministic run and verify, worker lane containment, lifecycle automation policy, universal artifact dispatch); none specifies how a spec selector is resolved to a file. Checked rather than assumed, because this plan declares no `.spec.md` in `- Scope-Paths:` and the runner announces declared spec edits before a run, so an undeclared-but-needed amendment would surface as a scope refusal at finalize. | The grep run across `.aw/records/specs/`; the universal-artifact-dispatch spec searched for `resolve_spec`, `Spec Mode` and `--spec` (no match). |
| F-09 | SUBSTRING MATCHING IS UNCHANGED BY THIS PLAN AND IS NOT AMBIGUOUS FOR ANY CURRENT id6, BUT IT IS LOOSE FOR SHORT WORDS. The matching branch is `p.name == supplied.name or value in p.name`. Swept over the post-fix candidate set, every id6 appearing in a spec filename matches exactly one file (zero ambiguous), so the fix does not introduce an ambiguity regression for id6 selectors. But a short substring is greedy by construction: `spec` matches all 40 and would raise the ambiguity error, while `attention` matches 2. That is PRE-EXISTING behavior of a branch this plan leaves textually alone, and tightening it would change which selectors resolve, which is a separate contract decision. E-02 pins the ambiguity error so the delegation cannot alter it silently. | The id6 sweep run over the filtered candidate set; `spec`, `attention`, `ipd-spec` and `exit` driven through the same matching expression. |
| F-10 | (added at review, PR-001) `specs._spec_files` CAN RETURN PATHS OUTSIDE THE REPOSITORY, AND A NAIVE DELEGATION THEN CRASHES WITH A NON-`ScriptError`. Its primary root comes from `record_producers.resolve_record_read_paths("specs", target_repo=...)`, which follows the configured records backend; this repository is `records_backend: repository` (`.aw/config/project.json`), but an unconfigured temp repo resolves to `<AW_HOME>/projects/<slug>/records/specs`. With a spec planted there under an isolated `AW_HOME`, `_spec_files` returned it alongside the in-repo specs, and `agy_run.relative_posix(root, <it>)` raised `ValueError`. Separately, with a RELATIVE root (`Path(".")`) `_spec_files` returns absolute paths and `p.relative_to(Path("."))` raises `ValueError` too, so a probe must pass a resolved root, as production does (`agy_run.repository_root` returns `.resolve()`d paths). E-03 therefore resolves and fences the delegated set to `root`. | Temp git repo plus isolated `AW_HOME` reproduction run at review; `relative_posix` and the ambiguity renderer driven against the delegated output; `record_producers.resolve_record_path` and `agy_run.repository_root` read. |
| F-11 | (added at review, PR-002) THE `untracked/` FIXTURE ALONE DOES NOT PROVE A REAL GIT IGNORE RULE IS CONSULTED. `artifact_core.is_ignored_path` returns True for any path with an `untracked` component via a hardcoded `"untracked" in rel_parts` check, before it looks at `get_ignored_dirs`. A spec under `.aw/records/specs/scratch/` excluded only by `.git/info/exclude` was measured to be dropped by `_spec_files`, so that second fixture is the one that exercises the `git ls-files --ignored` path. | `artifact_core.is_ignored_path` and `_cached_ignored_dirs` read; temp-repo run with both fixtures, `_spec_files` returning neither. |

## Proposed changes (ordered, validatable)

1. E-01 captures the four-way reproduction and the two must-keep-working cases at the base commit.
2. E-02 writes the behavioral module under `tests/` (where a gate will actually run it) and shows its subdirectory, gitignored and README assertions red.
3. E-03 replaces the non-recursive candidate loop in `resolve_spec` with a delegation to `specs._spec_files`, imported locally, resolved and fenced to the repository root (F-10), leaving the matching expression and both error message texts unchanged and recording why delegation rather than a bare `rglob`.
4. E-04 exercises both callers, demonstrates the positional path returning `spec` instead of `prompt`, and runs the uncollected `tools/test_agy_run.py` explicitly.
5. E-05 runs the bare suite before and after and reports an empty failure-set delta.

## Deferred / out of scope (with reason)

- THE SAME NON-RECURSIVE DEFECT IN `agy_run._candidate_plans`/`resolve_ipd` (F-06), measured and reproduced, latent only until the first `aw archive plans --apply` creates a `YYYYMM/` shard. Not fixed here because plans have no single canonical enumeration helper to delegate to the way specs have `specs._spec_files`, so the fix requires choosing or creating that canonical source; doing it in this plan would double the scope and put plan resolution in the blast radius of a spec-resolution fix. Carrier filed at authoring with the sharded-plan reproduction and the `plans_archive` citation.
  - Carrier: mlcbk9
- TIGHTENING `resolve_spec`'s SUBSTRING MATCHING (F-09), which makes a short selector such as `spec` match all 40 candidates. Pre-existing behavior of a branch this plan leaves textually alone; changing which selectors resolve is a contract decision independent of which files are enumerated, and conflating the two would make this plan's regression surface much harder to reason about. E-02 pins the current ambiguity error so a later change to it is deliberate.
  - Carrier-Declined: the loose match is LOUD, not silent: it raises `Specification reference ... is ambiguous` and prints every candidate, so a caller is told exactly what happened and can disambiguate. Measured, it misresolves nothing today (zero ambiguous id6 across the whole candidate set), so there is no defect to carry, only a possible ergonomic preference. Filing an item for a correctly-erroring selector form would be speculative work.
- ADDING A CACHE TO THE DELEGATED ENUMERATION (F-07). Measured at 104ms warm inside a command that then spawns an interactive agent turn, so it is not user-perceptible and by `AGENTS.md`'s own test is not a defect. Recorded here so the executor does not add one speculatively and a reviewer does not read its absence as an oversight.
  - Carrier-Declined: nothing is deferred; this row records a measurement that says there is no work to do. Filing an item for an imperceptible 104ms would be exactly the over-filing `AGENTS.md` warns against when it says inefficiency users cannot notice is not a defect.
- MOVING OR DUPLICATING `tools/test_agy_run.py` INTO `tests/` so the whole module becomes a gate (F-04). This plan adds its OWN module under `tests/` and leaves the existing one where it is: relocating 44 tests is a records-and-collection change with its own regression surface (the module is run explicitly by name in at least one documented workflow path), and it is not needed for this fix to be gated. The honest statement is that `tools/test_agy_run.py`'s other 43 tests remain ungated after this plan.
  - Carrier: n8adhb

## Scope check

- Over-scope: none. `agent_workflows/agy_run.py` carries E-03's single enumeration change and its comment. `tests/test_agy_run_resolve_spec_recursive.py` is the new module from E-02. `agent_workflows/specs.py` is NOT edited: `_spec_files` already does what is needed and is called, not changed (F-03). `agent_workflows/artifact_core.py` is NOT edited: `is_ignored_path`/`get_ignored_dirs` are reached through the helper. `tools/test_agy_run.py` is NOT edited: F-05 measures that its one `resolve_spec` test survives delegation unmodified, and E-04 runs it as a check rather than touching it. No `.spec.md` is declared (F-08), so the run must announce no declared spec edits and none may be made.
- Under-scope: the risk is that `specs._spec_files` turns out to depend on repository state a bare temp fixture lacks, making E-02's fixture harder than expected. Partly measured already (F-05 drove it against a reconstructed temp git repo successfully, and the helper wraps its `resolve_record_read_paths` call in `try`/`except Exception` with a fallback to the local specs dir), so the residual risk is small; if it materializes, the correct move is to build the fixture as a real `git init` repo with the shipped `.aw/.gitignore` present rather than to monkeypatch the helper, since a patched helper would stop testing the coupling that matters.

## Required tests / validation

- THE NEW BEHAVIORAL MODULE `tests/test_agy_run_resolve_spec_recursive.py`, driving a temp git fixture repo and asserting: a spec in `.aw/records/specs/approved/` resolves by bare id6 and by bare filename; a spec in the legacy `.agents/docs/specs/` root still resolves by bare filename; a spec under `.aw/records/specs/untracked/` and a spec ignored only by a `.git/info/exclude` rule are NOT returned (the ignored-path filter, F-11); a spec in the out-of-repo records-backend dir is NOT returned and yields `ScriptError` (F-10); `README.md` is not resolvable as a spec; an ambiguous selector still raises the `is ambiguous` error listing its candidates; and an exact existing path still resolves through the early return.
- THE EXISTING `tools/test_agy_run.py`, run EXPLICITLY by name because no gate collects it (F-04), passing at its full count, with `test_resolve_spec_by_path_and_name` green (F-05).
- THE CALLER PROBE of E-04: both `resolve_mode_and_target` call sites exercised, including `aw agy exec --agy <stub> --no-audit pqsx96` positionally, with the resolved mode pasted and the `prompt`-to-`spec` correction shown.
- THE END-TO-END COMMAND from E-01 re-run after the fix, always against the stub `--agy`: `aw agy exec --agy <stub> --no-audit --spec pqsx96` must no longer exit 2 with `No specification matching` and must print `Executing [spec mode] ...`.
- THE BARE FULL SUITE of E-05: `python3 -m pytest` with no added flags, before and after, failure-set delta stated as a set of test ids and required to be empty.
- `aw ipd lint` conforming at `--phase author` before review and at `--phase pre-transition` before the terminal move. `aw check` to confirm no new drift.

## Spec / documentation sync

No spec amendment, and this was CHECKED rather than assumed (F-08). A grep across `.aw/records/specs/` for `agy_run`, `agy exec` and `Spec Mode` returns seven specs that mention the runner family for unrelated reasons; none specifies how a `--spec` selector is resolved to a file, and the `universal-artifact-dispatch` spec (`implementing`) contains no reference to `resolve_spec`, `Spec Mode` or `--spec`. This plan therefore declares no `.spec.md` in `- Scope-Paths:`, and the run must announce no declared spec edits.

`- From-Spec:` IS DELIBERATELY ABSENT, AND `aw check` ADVISES OTHERWISE. Measured at authoring, `aw check` raises the `info`-severity advisory `check.plan-spec-link-missing` against this plan with the fix hint `aw ipd set a6ootg --from-spec pqsx96`. THAT HINT MUST NOT BE FOLLOWED. The rule (`check_engine.check_plan_spec_link_missing`, via `parse_cited_spec_ids`) scans the `- Concern:`, `- Scope:` and `- Scope-Paths:` bullets for any 6-character token that resolves to a known spec id6, and `pqsx96` appears in this plan's Concern bullet only because it is the SELECTOR USED AS A TEST PROBE (`aw agy exec --spec pqsx96`) and part of the probe spec's filename. The spec `pqsx96` (`agent-adherence-invariant-catalog`, `draft`) does not govern, specify, or motivate this fix; it was chosen as a probe target because it exists and sits in a status subdirectory, which is precisely the condition that reproduces the bug. Writing `- From-Spec: pqsx96` would assert a graduation provenance that did not happen, which is the same class of error as hand-writing an attestation field. This plan's provenance is `- From-Backlog: 8jl0rx`, which is recorded. The advisory is `info` and does not gate; it is a known limitation of a token-matching heuristic that cannot distinguish a cited spec from a named probe target, and it is left standing rather than silenced.

No user-facing documentation change is due either. The defect is that a documented selector form did not work, not that the documentation described it wrongly: `aw agy exec --spec <selector>` is meant to accept an id6 and a bare filename, and after this plan it does. Nothing in `docs/` was found advertising the broken behavior (a search of `docs/` for `agy exec` returns no file), so there is no false claim to reconcile. The one place worth a note is `specs._spec_files`' docstring, which already records the recursion-plus-filter coupling this plan relies on; it needs no edit, and E-03 cites it from the call site instead of restating it.

## Open questions

### OQ-01: Should the fix delegate to `specs._spec_files` or re-implement a recursive walk in `agy_run`

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: DELEGATE, resolved from repository evidence at authoring. The backlog item's "fix precedent" section points at `specs._spec_files` and quotes its docstring's warning that `rglob` alone is incomplete, but it does not say whether to CALL that helper or to copy its approach, and the two choices have materially different consequences. Three measurements decide it. FIRST (F-03), the helper's result differs from a naive recursive walk of the same two roots by exactly one file, `README.md`, and excluding it is itself a fix, since `resolve_spec(root, "README")` today returns the specs README as though it were a specification; a hand-rolled `rglob` plus `is_ignored_path` would have to remember the skip-names set separately to get this right. SECOND, the helper resolves its roots through `record_producers.resolve_record_read_paths` and appends the legacy `.agents/docs/specs` root unconditionally with a comment explaining why, which is the compatibility the hardcoded two-tuple in `resolve_spec` was approximating; copying the walk but not that resolution would leave a second, less capable notion of where specs live. THIRD, the coupling the docstring records (recursion makes the ignore filter mandatory) is exactly the kind of invariant that survives in one place and rots in two, and this repository's standing preference is one definition per concept. The cost objection is answered by F-07: 104ms warm, inside a command that then spawns an interactive agent turn, is not user-perceptible. The private-name objection (`_spec_files` is underscore-prefixed) is answered by precedent: `spec_citations` and `check_engine` already call it across module boundaries, so this would be the third cross-module caller rather than a new pattern. Review addendum (PR-001, F-10): delegation is kept, but the helper's output follows the configured records backend and can include out-of-repo paths, so E-03 resolves and fences it to `root`; that fence was prototyped at review over a fixture and the live tree with the expected results.

### OQ-02: Is it acceptable that `README.md` stops resolving as a specification

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: YES, and it is a FIX rather than a regression, resolved at authoring. Measured: today `resolve_spec(root, "README")` returns `.aw/records/specs/README.md` and `resolve_spec(root, "README.md")` returns the repository root `README.md` through the `direct.is_file()` early return. After delegation the specs README is no longer a candidate, because `specs._spec_files` skips `README.md`, `INDEX.md` and `STATUS.md` in alignment with `check_engine._SKIP_NAMES`. This is correct on the merits: the specs README is a navigation document, not a specification, and feeding it to Spec Mode as the input to author an IPD from would produce an IPD based on an index. It is called out as an open question rather than buried because it is the ONE behavior this plan removes rather than adds, so a reviewer should see it stated and pinned rather than discover it later; E-02 asserts it explicitly. Note the root `README.md` case is untouched, since it resolves through the early return and not through the candidate set, which is a separate pre-existing oddity (any existing file path resolves as a spec) that this plan deliberately does not change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: Paste all four base-commit failures VERBATIM: the `aw agy exec --agy <stub> --no-audit --spec pqsx96` invocation (stub per E-01; name the stub path and paste its contents) with its exit code and the exact `error: No specification matching 'pqsx96' found.` line, and the three in-process `ScriptError` captures (bare id6, bare filename, flat-looking path). Paste the two must-keep-working captures: the exact existing path resolving, and `tools/test_agy_run.py` passing with zero failures (paste its summary line). State the base commit hash. Confirm no real `agy` was launched by any probe. State the spec's ACTUAL status subdirectory as re-derived at execution and confirm it is the one used in the probes, rather than reusing the authoring path, so an advanced spec status cannot make this item read as a failure for the wrong reason.
  - Observed evidence:
    1. Base commit hash:
    `eca89e1a65736f7621eac5c59f3678b2698fcf4d`

    2. Stub path and contents:
    Stub path: `/tmp/agy_stub_a6ootg.sh`
    ```bash
    #!/usr/bin/env bash
    echo "STUB agy invoked with argv: $@" >&2
    exit 1
    ```
    No real `agy` was launched; `--agy /tmp/agy_stub_a6ootg.sh --no-audit` was passed for all CLI invocations.

    3. Actual status subdirectory of `pqsx96`:
    Re-derived path on live tree: `.aw/records/specs/draft/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md` (status subdirectory is `draft/`).

    4. Verbatim output for the four base-commit failures:
    - CLI invocation:
    `python3 -m agent_workflows.cli agy exec --agy /tmp/agy_stub_a6ootg.sh --no-audit --spec pqsx96`
    Exit code: 2
    Output:
    ```
    error: No specification matching 'pqsx96' found.
    ```
    - In-process bare id6:
    `agy_run.resolve_spec(root, "pqsx96")`
    `ScriptError: No specification matching 'pqsx96' found.`
    - In-process bare filename:
    `agy_run.resolve_spec(root, "20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md")`
    `ScriptError: No specification matching '20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md' found.`
    - In-process flat-looking path:
    `agy_run.resolve_spec(root, ".aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md")`
    `ScriptError: No specification matching '.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md' found.`

    5. Verbatim output for the two must-keep-working captures:
    - Exact path resolving:
    `agy_run.resolve_spec(root, ".aw/records/specs/draft/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md")`
    Resolved to: `.aw/records/specs/draft/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md`
    - `python3 -m pytest tools/test_agy_run.py -o addopts=""` summary line:
    ```
    ============================== 44 passed in 2.56s ==============================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the new module's RED output at the base commit, before any production edit, with the individual assertion errors visible, and identify WHICH assertions failed and which passed. The expected split is that the status-subdirectory assertions (1)/(2) and the README assertion (5) FAIL, while the legacy-root (3), both gitignored (4a/4b), out-of-repo (6), ambiguity and exact-path assertions PASS (the exclusions pass vacuously at base because the flat glob cannot reach those dirs; they become discriminating only after E-03, which V-03 shows); if the split differs, explain why, because a module that fails wholesale is not a discriminating baseline. Confirm the module is COLLECTED by the default suite by pasting a bare `python3 -m pytest --collect-only` line showing the new file (this is the specific failure mode F-04 identifies, and a module under `tools/` would silently not appear). Confirm by inspection that the module reads no production source and asserts no symbol's existence (P16), and say in one sentence how each assertion obtains its facts. Paste the fixture construction for (4b) showing that spec sits under a path with NO `untracked` component and is ignored ONLY by a rule in the fixture's `.git/info/exclude` (or `.gitignore`), and paste `git -C <fixture> check-ignore -v <that path>` output naming the rule, since `is_ignored_path` rejects any `untracked` path by a hardcoded check (F-11). For (6), paste the assertion that the planted backend spec path is outside the fixture root.
  - Observed evidence:
    1. New module RED output at base commit:
    Command: `python3 -m pytest tests/test_agy_run_resolve_spec_recursive.py -o addopts=""`
    ```
    =================================== FAILURES ===================================
    __ TestAgyRunResolveSpecRecursive.test_05_specs_readme_not_resolvable_as_spec __

    self = <tests.test_agy_run_resolve_spec_recursive.TestAgyRunResolveSpecRecursive testMethod=test_05_specs_readme_not_resolvable_as_spec>

        def test_05_specs_readme_not_resolvable_as_spec(self) -> None:
            """(5) README.md at specs root is not resolvable as a specification."""
    >       with self.assertRaises(agy_run.ScriptError) as ctx:
    E       AssertionError: ScriptError not raised

    tests/test_agy_run_resolve_spec_recursive.py:168: AssertionError
    _ TestAgyRunResolveSpecRecursive.test_02_resolve_spec_in_status_subdirectory_by_bare_filename _

    self = <tests.test_agy_run_resolve_spec_recursive.TestAgyRunResolveSpecRecursive testMethod=test_02_resolve_spec_in_status_subdirectory_by_bare_filename>

        def test_02_resolve_spec_in_status_subdirectory_by_bare_filename(self) -> None:
            """(2) A spec planted in a status subdirectory resolves by bare filename."""
    >       resolved = agy_run.resolve_spec(
                self.root, "20261001-abc123-01-abc123-test-spec.spec.md"
            )

    tests/test_agy_run_resolve_spec_recursive.py:127:
    _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    root = PosixPath('/dev/shm/tmpkiqzju4t/repo')
    value = '20261001-abc123-01-abc123-test-spec.spec.md'

        def resolve_spec(root: Path, value: str) -> Path:
            ...
            if not matches:
    >           raise ScriptError(f"No specification matching {value!r} found.")
    E           agent_workflows.agy_run.ScriptError: No specification matching '20261001-abc123-01-abc123-test-spec.spec.md' found.

    agent_workflows/agy_run.py:406: ScriptError
    _ TestAgyRunResolveSpecRecursive.test_01_resolve_spec_in_status_subdirectory_by_bare_id6 _

    self = <tests.test_agy_run_resolve_spec_recursive.TestAgyRunResolveSpecRecursive testMethod=test_01_resolve_spec_in_status_subdirectory_by_bare_id6>

        def test_01_resolve_spec_in_status_subdirectory_by_bare_id6(self) -> None:
            """(1) A spec planted in a status subdirectory resolves by bare id6."""
    >       resolved = agy_run.resolve_spec(self.root, "abc123")

    tests/test_agy_run_resolve_spec_recursive.py:122:
    _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    root = PosixPath('/dev/shm/tmprbhcz5o3/repo'), value = 'abc123'

        def resolve_spec(root: Path, value: str) -> Path:
            ...
            if not matches:
    >           raise ScriptError(f"No specification matching {value!r} found.")
    E           agent_workflows.agy_run.ScriptError: No specification matching 'abc123' found.

    agent_workflows/agy_run.py:406: ScriptError
    =========================== short test summary info ============================
    FAILED tests/test_agy_run_resolve_spec_recursive.py::TestAgyRunResolveSpecRecursive::test_05_specs_readme_not_resolvable_as_spec
    FAILED tests/test_agy_run_resolve_spec_recursive.py::TestAgyRunResolveSpecRecursive::test_02_resolve_spec_in_status_subdirectory_by_bare_filename
    FAILED tests/test_agy_run_resolve_spec_recursive.py::TestAgyRunResolveSpecRecursive::test_01_resolve_spec_in_status_subdirectory_by_bare_id6
    ========================= 3 failed, 6 passed in 1.26s ==========================
    ```

    2. Failure/pass split breakdown:
    - FAILED (3):
      - `test_01_resolve_spec_in_status_subdirectory_by_bare_id6`
      - `test_02_resolve_spec_in_status_subdirectory_by_bare_filename`
      - `test_05_specs_readme_not_resolvable_as_spec`
    - PASSED (6):
      - `test_03_resolve_spec_in_legacy_root_by_bare_filename`
      - `test_04a_gitignored_spec_in_untracked_dir_not_resolved`
      - `test_04b_gitignored_spec_by_git_exclude_not_resolved`
      - `test_06_out_of_repo_backend_spec_not_resolved`
      - `test_07_ambiguous_selector_raises_with_candidates`
      - `test_08_exact_existing_path_resolves`

    3. Collection confirmation via bare `python3 -m pytest --collect-only`:
    ```
    tests/test_agy_run_resolve_spec_recursive.py::TestAgyRunResolveSpecRecursive::test_04b_gitignored_spec_by_git_exclude_not_resolved
    tests/test_agy_run_resolve_spec_recursive.py::TestAgyRunResolveSpecRecursive::test_07_ambiguous_selector_raises_with_candidates
    tests/test_agy_run_resolve_spec_recursive.py::TestAgyRunResolveSpecRecursive::test_02_resolve_spec_in_status_subdirectory_by_bare_filename
    tests/test_agy_run_resolve_spec_recursive.py::TestAgyRunResolveSpecRecursive::test_08_exact_existing_path_resolves
    tests/test_agy_run_resolve_spec_recursive.py::TestAgyRunResolveSpecRecursive::test_04a_gitignored_spec_in_untracked_dir_not_resolved
    tests/test_agy_run_resolve_spec_recursive.py::TestAgyRunResolveSpecRecursive::test_03_resolve_spec_in_legacy_root_by_bare_filename
    tests/test_agy_run_resolve_spec_recursive.py::TestAgyRunResolveSpecRecursive::test_01_resolve_spec_in_status_subdirectory_by_bare_id6
    tests/test_agy_run_resolve_spec_recursive.py::TestAgyRunResolveSpecRecursive::test_05_specs_readme_not_resolvable_as_spec
    tests/test_agy_run_resolve_spec_recursive.py::TestAgyRunResolveSpecRecursive::test_06_out_of_repo_backend_spec_not_resolved
    ```

    4. Inspection for P16 compliance:
    The module reads no production source code and asserts no symbol's existence; each assertion directly calls `agy_run.resolve_spec(self.root, ...)` against a real temporary git repository and asserts on returned Path values or raised ScriptError exceptions.

    5. Fixture construction for (4b) and check-ignore:
    ```python
    self.scratch_dir = self.root / ".aw" / "records" / "specs" / "scratch"
    self.scratch_dir.mkdir(parents=True, exist_ok=True)
    self.scratch_spec = self.scratch_dir / "20261001-scrt01-01-scrt01-scratch.spec.md"
    self.scratch_spec.write_text("# Scratch\n", encoding="utf-8")
    exclude_file = self.root / ".git" / "info" / "exclude"
    exclude_file.write_text(".aw/records/specs/scratch/\n", encoding="utf-8")
    ```
    `git -C <fixture> check-ignore -v <path>` output:
    `.git/info/exclude:1:.aw/records/specs/scratch/	.aw/records/specs/scratch/20261001-scrt01-01-scrt01-scratch.spec.md`

    6. Assertion that backend spec path is outside fixture root:
    `self.assertFalse(self.out_repo_spec.is_relative_to(self.root))`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the full diff of `agent_workflows/agy_run.py`. CONFIRM TEXTUALLY that the matching expression `p.name == supplied.name or value in p.name` and both error strings (`No specification matching ... found.` and `Specification reference ... is ambiguous:`) are UNCHANGED, by quoting them from the post-change file. Confirm the import of `specs` is LOCAL to the function and that no top-level `agent_workflows` import was added, quoting the surrounding lines. Confirm the comment records why delegation rather than a bare `rglob` and cites backlog `8jl0rx`. Paste the new module passing GREEN. Paste the four E-01 reproductions re-run and now succeeding, including the end-to-end `aw agy exec --spec pqsx96` no longer exiting 2 on resolution. Paste a set-comparison showing the post-fix candidate set equals the in-root subset of `specs._spec_files`' resolved output (on this repository, whose `records_backend` is `repository`, that subset is the whole output; state whether it was), so delegation is demonstrated rather than assumed. Quote the root-fence lines (resolve plus `is_relative_to(root.resolve())`) and the ambiguity renderer's `relative_to(root.resolve())` from the post-change file. Every CLI re-run uses the stub `--agy` and must show `Executing [spec mode] ...`.
  - Observed evidence:
    1. Full diff of `agent_workflows/agy_run.py`:
    ```diff
    diff --git a/agent_workflows/agy_run.py b/agent_workflows/agy_run.py
    index e4a9bd7bf..f7d8c7f20 100755
    --- a/agent_workflows/agy_run.py
    +++ b/agent_workflows/agy_run.py
    @@ -394,18 +394,31 @@ def resolve_spec(root: Path, value: str) -> Path:
         if direct.is_file():
             return direct.resolve()

    -    # Search common specs directories
    -    candidates: list[Path] = []
    -    for d in (root / ".agents" / "docs" / "specs", root / ".aw" / "records" / "specs"):
    -        if d.is_dir():
    -            candidates.extend(d.glob("*.md"))
    -    candidates = sorted(set(candidates))
    +    # Backlog 8jl0rx / IPD a6ootg: Delegate enumeration to specs._spec_files rather
    +    # than re-implementing a recursive walk. Non-recursion in the previous glob masked
    +    # the lack of an ignored-path filter; specs._spec_files couples the recursive walk,
    +    # the mandatory ignored-path filter (artifact_core.is_ignored_path), the exclusion
    +    # of non-spec files (README.md, INDEX.md, STATUS.md), and legacy root compatibility.
    +    # We import locally to avoid introducing top-level package imports in agy_run.
    +    from agent_workflows import specs
    +
    +    # specs._spec_files may return out-of-repo paths under non-repository backends;
    +    # downstream consumers (relative_posix, Turn-1 prompt) require in-repo paths.
    +    # Normalize and fence candidates to the repository root.
    +    resolved_root = root.resolve()
    +    candidates = sorted(
    +        {
    +            p.resolve()
    +            for p in specs._spec_files(root)
    +            if p.resolve().is_relative_to(resolved_root)
    +        }
    +    )

         matches = [p for p in candidates if p.name == supplied.name or value in p.name]
         if not matches:
             raise ScriptError(f"No specification matching {value!r} found.")
         if len(matches) > 1:
    -        rendered = "\n".join(f"  - {p.relative_to(root)}" for p in matches)
    +        rendered = "\n".join(f"  - {p.relative_to(resolved_root)}" for p in matches)
             raise ScriptError(
                 f"Specification reference {value!r} is ambiguous:\n{rendered}"
             )
    ```

    2. Textual confirmation of matching expression and error strings from post-change file:
    ```python
    matches = [p for p in candidates if p.name == supplied.name or value in p.name]
    if not matches:
        raise ScriptError(f"No specification matching {value!r} found.")
    if len(matches) > 1:
        rendered = "\n".join(f"  - {p.relative_to(resolved_root)}" for p in matches)
        raise ScriptError(
            f"Specification reference {value!r} is ambiguous:\n{rendered}"
        )
    ```

    3. Local import of `specs` and absence of top-level import:
    Surrounding lines (lines 402-404):
    ```python
        # We import locally to avoid introducing top-level package imports in agy_run.
        from agent_workflows import specs
    ```
    Grep for `from agent_workflows` in `agent_workflows/agy_run.py`:
    `403:    from agent_workflows import specs`
    `832:        from agent_workflows import agy_sessions`
    Confirmed: no top-level package imports exist.

    4. Comment citation:
    `# Backlog 8jl0rx / IPD a6ootg: Delegate enumeration to specs._spec_files rather than re-implementing a recursive walk. Non-recursion in the previous glob masked the lack of an ignored-path filter; specs._spec_files couples the recursive walk, the mandatory ignored-path filter (artifact_core.is_ignored_path), the exclusion of non-spec files (README.md, INDEX.md, STATUS.md), and legacy root compatibility.`

    5. New test module passing GREEN:
    `tests/test_agy_run_resolve_spec_recursive.py ......... [100%]`
    `9 passed in 1.21s`

    6. Four E-01 reproductions re-run and now succeeding:
    - CLI probe:
    `aw agy exec --agy /tmp/agy_stub_a6ootg.sh --no-audit --spec pqsx96`
    Output:
    `Executing [spec mode] .aw/records/specs/draft/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md in Antigravity...`
    - In-process `pqsx96`:
    Resolved to: `.aw/records/specs/draft/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md`
    - In-process bare filename:
    Resolved to: `.aw/records/specs/draft/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md`
    - In-process flat-looking path:
    Resolved to: `.aw/records/specs/draft/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md`

    7. Set-comparison of post-fix candidates against `specs._spec_files`:
    - Total `specs._spec_files(root)`: 40
    - Total in-root subset: 40
    - Is subset equal to whole output on this repo (`records_backend: repository`): True
    - Candidates set == in-root subset: True

    8. Root-fence lines and ambiguity renderer quote:
    ```python
    resolved_root = root.resolve()
    candidates = sorted(
        {
            p.resolve()
            for p in specs._spec_files(root)
            if p.resolve().is_relative_to(resolved_root)
        }
    )
    ...
    rendered = "\n".join(f"  - {p.relative_to(resolved_root)}" for p in matches)
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the resolved mode and target for BOTH callers: the explicit `--spec pqsx96` form and the POSITIONAL `pqsx96` form. Paste both the in-process `resolve_mode_and_target` tuples and the stub-`--agy` CLI `Executing [<mode> mode] ...` lines. For the positional form, paste the BEFORE result showing mode `prompt` (the silent misrouting F-02 measures) and the AFTER result showing mode `spec`, since that correction is the most consequential behavior change in this plan and must not be reported as a mere resolution fix. Paste the full output of `python3 -m pytest tools/test_agy_run.py -o addopts=""` showing zero failures and the same count as the V-01 capture (44 at authoring, context only), and confirm `test_resolve_spec_by_path_and_name` is among the passes. Confirm `git diff --name-only` does NOT list `tools/test_agy_run.py`.
  - Observed evidence:
    1. Caller 1 (explicit `--spec pqsx96`):
    - In-process `resolve_mode_and_target`:
      `('spec', '.aw/records/specs/draft/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md', '')`
    - CLI execution output:
      `Executing [spec mode] .aw/records/specs/draft/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md in Antigravity...`

    2. Caller 2 (positional `pqsx96`):
    - BEFORE result:
      In-process: `('prompt', 'pqsx96', '')`
      CLI execution: `Executing [prompt mode] pqsx96 in Antigravity...`
    - AFTER result:
      In-process: `('spec', '.aw/records/specs/draft/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md', '')`
      CLI execution: `Executing [spec mode] .aw/records/specs/draft/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md in Antigravity...`

    3. Full output of `python3 -m pytest tools/test_agy_run.py -o addopts=""`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=1611710850
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 44 items

    tools/test_agy_run.py ............................................       [100%]

    ============================== 44 passed in 0.64s ==============================
    ```
    Confirmed: 44 passed, zero failures, matching the baseline count.
    Confirmed: `tools/test_agy_run.py::AgyRunTargetResolutionTests::test_resolve_spec_by_path_and_name` is among the passes.

    4. `git diff --name-only` check:
    Outputs only `agent_workflows/agy_run.py` (and the plan file); `tools/test_agy_run.py` is NOT listed.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste both bare-suite summary lines (base commit and final) verbatim, and state the failure-set delta as an explicit SET of test ids. An empty delta is the bar; a count comparison is NOT acceptable evidence, because a pre-existing environmental failure and a new regression can net to the same count. Confirm the command was `python3 -m pytest` with no added flags, and if any flag was added, name it and justify it against `AGENTS.md`'s three named prohibitions.
  - Observed evidence:
    1. Base-commit summary line (command: `python3 -m pytest` with no added flags):
    `1 failed, 4879 passed, 2 skipped, 3 warnings in 781.31s (0:13:01)`
    Base failure set:
    `{'tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta'}`

    2. Final summary line (command: `python3 -m pytest` with no added flags):
    `1 failed, 4888 passed, 2 skipped, 3 warnings in 278.93s (0:04:38)`
    Final failure set:
    `{'tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta'}`

    3. Failure-set delta:
    `delta = final_failures - base_failures = set()` (EMPTY).
    No new failures were introduced. Exactly 9 new tests were added and passed (4879 -> 4888).

    4. Command confirmation:
    Both runs executed `python3 -m pytest` with no added flags; `pyproject.toml` `addopts` was honored with no prohibitions violated.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only the paths in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. Paste ACTUAL runner output for every test claim and never assert a pass that was not run. This plan declares no `.spec.md` file, so the run must announce no declared spec edits and none may be made.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop): `agent_workflows/agy_run.py` (E-03) and `tests/test_agy_run_resolve_spec_recursive.py` (E-02). Do NOT edit `agent_workflows/specs.py`, `artifact_core.py`, `record_producers.py` or `tools/test_agy_run.py`. An out-of-scope edit that turns out to be necessary is MADE and then JUSTIFIED to `aw ipd finalize` with `--scope-reason`; a declared path left unmodified needs `--scope-ack`.

NEVER LAUNCH A REAL AGENT. Every `aw agy exec` probe passes `--agy <stub> --no-audit` (E-01); a probe against the real `agy` would start a paid, side-effecting Antigravity turn from inside a validation step. Verify the staged set with `git diff --cached --name-only` before committing and unstage anything another party changed with `git restore --staged <path>`, path by path.

DO NOT WIDEN THE FIX TO `resolve_ipd`. F-06 measures the identical defect there and it is handed off to its own carrier, because plans have no canonical enumeration helper to delegate to and choosing one is a separate decision. Report the breadth if execution learns more about it; do not absorb it.

DO NOT TIGHTEN THE MATCHING BRANCH. This plan changes WHICH FILES are candidates and nothing about how a selector matches them (F-09). An executor who also "improves" the substring match makes the regression surface of a release-gating bugfix much harder to reason about, and V-03 requires that expression quoted unchanged.

POST-GATE LIFECYCLE. After every `E-*` is performed and every `V-*` carries concrete pasted evidence, run `aw ipd lint --phase pre-transition` and require it conforming, then reach `.aw/records/plans/executed/` through `aw ipd finalize`. That transition is UNCONDITIONALLY OWED but its OWNER is CONDITIONAL: under `aw oc run` / `aw agy run` the RUNNER performs finalize and the executor must NOT also run it; executed by hand, the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-roll a `git mv` to `executed/` and never hand-edit `- Status: executed`. Backlog `8jl0rx` is already `graduated` (this plan is its carrier); do not set it `done` from this plan and do not clear its `Blocks-Release`. Do not claim done while any validation item lacks observed evidence.
