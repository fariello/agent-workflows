# IPD: Gate the runner's in-lane backlog close against main with a verified lane-carrier override

- Date: 2026-09-30
- Kind: child
- Concern: The runner's in-lane backlog close evaluates the release gate against the LANE, where this run's own plan already sits in `executed/`, so a release-gated item can close `done` that main's view would refuse. `--gate-dir` shipped (`9vglxd` E-03/E-04) but has no caller, because a naive `--gate-dir <main>` refuses the ordinary single-carrier close.
- Scope: IN: (a) add a VERIFIED lane-carrier override to `check_engine.evaluate_blocking_close` so one named carrier may be judged against a git ref rather than against the gate tree's worktree, with the assertion CHECKED via `git ls-tree` and never trusted; (b) surface it on `aw backlog set` as `--lane-carrier-ref`/`--lane-carrier-path` and declare both in `command_surface`; (c) pass the split plus the override from `runner_shared.close_backlog_item`, `process_backlog_close` and BOTH host wrappers, so the in-lane close gates against `repo` while moving in `write_repo`; (d) correct the three docstrings this falsifies; (e) tests for the single-carrier allowance, the sibling refusal, the forged-assertion refusal, and the post-merge/non-isolated no-ops. OUT: the ANY-vs-ALL divergence (closed by `2o5wka`); the positional-spelling bypass (owned by pending `47ttnv`); the outer predicate's spec-carrier blind spot (F-09, filed as its own item by E-01); making the override reachable by a hand close with no lane.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/backlog.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_backlog_handoff_close.py, tests/test_check_engine_release_gate.py, docs/artifact-lifecycles.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: medium
- From-Backlog: qkl8fs
- Set: qkl8fs
- Order: 1
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 4nbvfr

## Workflow history

- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `qkl8fs`; every finding F-01..F-10 measured at HEAD `8163b62ad` on two-tree git-worktree fixtures, scripts under `tmp/qkl8fs/` (gitignored).

## Goal

Make the runner's in-lane backlog close ask MAIN whether a release-gated item may close, while still performing the move in the lane, WITHOUT refusing the ordinary single-carrier close that is the common shape. The route is a VERIFIED override: the runner names the one carrier it just finalized plus the git ref that proves it, and the predicate confirms the claim with `git ls-tree` against the shared object store rather than believing a flag.

WHAT THIS FIXES, stated as the observable change. Today an isolated turn runs `aw backlog set <item> --status done --dir <lane>` with no `--gate-dir`, so `check_engine.evaluate_blocking_close` scans the LANE for carriers. Measured (F-02): on a two-carrier item whose sibling is unexecuted, the lane-rooted gate returns `legitimate=True` via HANDOFF because the lane shows this run's plan in `executed/`. After this plan the same shape is decided against main and refuses. That is the defect, not a side effect.

WHAT THIS DELIBERATELY DOES NOT CLAIM. It does not change the three arms, their verdicts, or the predicate's existing signature semantics; HANDOFF, SATISFIED and DE-GATED are untouched for every caller that passes no override. It does not make a HAND close gate against another tree. And it does not close the outer predicate's spec-carrier blind spot (F-09), which is a genuinely separate defect that this plan MEASURES, FILES and leaves alone.

WHY NOT SIMPLY PASS `--gate-dir <main>`, which is what the backlog item's own route (a) first suggests: measured in F-03, that refuses the ordinary single-carrier close with `carrier is not executed/implemented`, exactly the outcome `9vglxd` E-06 recorded when it withdrew its E-05 and refiled this work. The override is what makes the split survivable.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the premises before changing a shipped gate

- [ ] E-01 RE-MEASURE F-02, F-03, F-05 AND F-09 AT EXECUTION HEAD and record the outputs, because this plan tightens a shipped release gate and every one of its premises is a dated measurement. Re-drive the two-tree fixture (a `git worktree` of main, the plan `git mv`d `pending/` to `executed/` and committed in the lane) and confirm: the lane-rooted gate still returns `legitimate=True` via HANDOFF on the two-carrier sibling-unexecuted shape (F-02); a main-rooted gate with the lane citation still refuses the single-carrier shape (F-03); `resolve_evidence_artifact` still gives the four-cell matrix in F-05; and the outer predicate still returns `close=True` on the mixed IPD-plus-unimplemented-spec shape (F-09). ALSO FILE F-09 as its own backlog item now, with `aw backlog new`, so the obligation exists whether or not this plan executes.
  - Depends on: none
  - Expected outcome: four pasted measurements agreeing with F-02/F-03/F-05/F-09, plus the new backlog item's id6 for the F-09 defect.
  - IF ANY PREMISE HAS EXPIRED, STOP AND RE-SCOPE rather than proceeding. The specific reversal to watch for: if a main-rooted gate now PASSES the single-carrier shape unaided, then the override this plan builds is unnecessary and the correct change is the one-line `--gate-dir` pass that `9vglxd` already wrote and withdrew. Say so and stop; do not build an override nothing needs.
  - DO NOT FILE F-09 AS A DUPLICATE. Measured at authoring: `lsbd32` (the ANY-vs-ALL divergence) is `done`, closed by `2o5wka`, and `d1ldvk` covers only prose. `2o5wka`'s F-06 records a DIFFERENT residual (a sibling with NO gate line, where the inner gate is the permissive one); F-09 is the OPPOSITE direction, the OUTER predicate ignoring a spec carrier because `if ipds:` returns before `others` is examined. Confirm with a fresh `aw find backlog` before writing.
  - Execution state: pending

### Task group 2: the verified override in the shared predicate

- [ ] E-02 ADD A VERIFIED LANE-CARRIER OVERRIDE TO `check_engine.evaluate_blocking_close`, as a keyword-only parameter defaulting to None so every existing caller is bit-for-bit unchanged. It names ONE carrier path as the GATE TREE sees it, plus the git ref asserted to show that carrier terminal, and it is consumed ONLY inside the HANDOFF arm's `all(_carrier_is_executed(...))` fold, where the named carrier's state comes from the ref instead of from the worktree. VERIFY, DO NOT TRUST: resolve the claim with `git ls-tree -r --name-only <ref>` via the EXISTING `_git_capture` helper in this module, and treat the carrier as executed only when the ref's tree actually shows a path whose parts contain `executed` for that carrier's id6. A ref that does not exist, does not contain the carrier, or shows it still in `pending/` must leave the carrier judged exactly as the worktree judges it, which means the gate REFUSES.
  - Depends on: E-01
  - Expected outcome: with the override naming the single carrier and the lane branch ref, a main-rooted `evaluate_blocking_close` returns `legitimate=True` via HANDOFF with NO evidence citation; with a forged ref, or a ref whose tree still shows `pending/`, it returns `legitimate=False`.
  - THE OVERRIDE MUST NOT BE A SECOND CARRIER SCAN. Keep `find_from_backlog_artifacts(repo_root, item_id6)` as the one discovery call. The override changes how ONE discovered carrier is JUDGED; it must never add a carrier the gate tree did not find, because that would let a lane introduce a carrier main cannot see and is the permissive direction this plan exists to close.
  - SIBLINGS STAY UNOVERRIDDEN, which is the whole protective property. The override is singular by construction (one path, one ref). Measured at authoring on the live corpus by `2o5wka` F-07: 18 items carry a gate AND more than one carrier, with a tail of 9, so an override that generalized to "all carriers in the lane" would reopen precisely the hole `2o5wka` just closed.
  - `_carrier_is_executed` IS SHARED, so do NOT change its signature or behavior. It is called from `release_gate_warnings` too (the `check.orphaned-live-blocker` fold), and `2o5wka` E-05 just aligned that fold. Apply the override at the CALL SITE in the HANDOFF arm, leaving the helper a pure path/field predicate.
  - A SPEC CARRIER IS JUDGED BY A FIELD, NOT A PATH, so the ref lookup must read the blob for a `.spec.md` carrier rather than inspecting its directory. `_carrier_is_executed` reads `- Status: implemented` from spec TEXT and `"executed" in p.parts` from a plan PATH. `_blob_text(repo_root, ref, path)` already exists in this module for the text case. Handle both or the override silently never fires for a spec.
  - Execution state: pending

- [ ] E-03 SURFACE THE OVERRIDE ON `aw backlog set` as `--lane-carrier-ref` and `--lane-carrier-path`, wired through `backlog.run_set` into E-02's parameter, and DECLARE both in `command_surface.py`. Both flags must be supplied together: one without the other is a usage error (exit 2) with a message naming the missing flag, because a half-specified override would silently evaluate as no override at all and the operator would read a refusal as a gate verdict. Add the per-command flag-surface assertion to the existing `BacklogGateDirSplitTests` declaration test rather than relying on `find_undeclared_leaves`, which compares COMMAND PATHS and not flags.
  - Depends on: E-02
  - Expected outcome: `aw backlog set <item> --status done --dir <lane> --gate-dir <main> --lane-carrier-ref <branch> --lane-carrier-path <path>` exits 0 on the single-carrier shape; omitting either new flag exits 2 naming the missing one; the declaration test sees both flags.
  - REUSE `--gate-dir`'s VALIDATION SHAPE. That flag already resolves through `resolve_verb_repo_root` and refuses a non-project root with exit 2 before reading anything (`backlog.run_set`'s opening block, pinned by `test_case_5_gate_dir_non_project_root_refused`). Follow the same fail-before-write ordering so a bad override never half-moves an item.
  - DO NOT DEFAULT THE REF. There is no safe default: guessing `HEAD` would make the override fire against whatever the operator happens to have checked out, which is the trust-the-caller behavior E-02 exists to avoid.
  - THE EXISTING UNDECLARED DEBT IS NOT YOURS TO FIX. `command_surface.py`'s own comment records `--evidence`, `--yes` and `--commit/--no-commit` as accepted-but-undeclared, and the agreement test is one-directional. Declare the two NEW flags; do not opportunistically declare the three old ones, which would widen this plan's diff into a surface it does not otherwise touch.
  - Execution state: pending

### Task group 3: make the runner use it

- [ ] E-04 PASS THE GATE ROOT AND THE OVERRIDE FROM THE RUNNER, which is FOUR SYMBOLS IN THREE FILES and not the one the obvious reading suggests. `runner_shared.close_backlog_item` gains keyword-only parameters for the gate root plus the carrier ref/path and emits the three new argv flags; `runner_shared.process_backlog_close` passes `repo` as the gate root beside its existing `write_repo` move tree, and derives the carrier ref/path from the lane handle it already holds; and BOTH host wrappers (`oc_runipd.close_backlog_item`, `agy_runipd.close_backlog_item`) forward the new keywords IDENTICALLY.
  - Depends on: E-03
  - Expected outcome: an isolated turn's close emits `--dir <lane> --gate-dir <main> --lane-carrier-ref <lane-branch> --lane-carrier-path <main-relative carrier path>`; a non-isolated turn emits none of the three and its argv is unchanged.
  - WIDEN BOTH WRAPPERS OR NEITHER. `runner_shared`'s own module docstring warns that changing one runner's symbol "would silently give BOTH drivers that runner's behavior", because `agy_runipd` imports from `oc_runipd`. A one-sided edit gives one host a gated close and the other the status quo, with no test objecting. V-04 requires both wrappers pasted side by side.
  - `close_backlog_item` IS AN INJECTED PARAMETER AT THE CALL SITE, not the module function of the same name. `process_backlog_close` declares `close_backlog_item: Callable[..., tuple[int, str]]` keyword-only and invokes it with FIVE POSITIONAL arguments and no `run_checked`, while the module-level function REQUIRES `run_checked` keyword-only. This is the trap that made `9vglxd` E-05 unexecutable as scoped (its F-11/PR-701). Add the new parameters as KEYWORD-ONLY so the five-positional call site keeps working.
  - PASS THE OVERRIDE ONLY WHEN `isolated` IS TRUE. `process_backlog_close` already computes `isolated = write_repo.resolve() != repo.resolve()`, and the existing `lane_executed_carrier_override` is already gated on it. When the trees are the same there is nothing to override and nothing to split; measured in F-10, that path's verdict is unchanged either way, but passing a redundant override would make the argv lie about what the close depended on.
  - THE CARRIER PATH MUST BE MAIN'S SPELLING, NOT THE LANE'S. The override names the carrier as the GATE TREE sees it, which for a just-finalized plan is main's `pending/` path. `lane_executed_carrier_override` already computes exactly this mapping (`{main_rel: lane_rel}`) and is the function to read; do not re-derive the pair.
  - Execution state: pending

- [ ] E-05 CORRECT THE THREE DOCSTRINGS THIS CHANGE FALSIFIES, in the same change that falsifies them, so the tree never ships a guarantee this plan broke. (i) `runner_shared.close_backlog_item`'s paragraph asserting "THE TWO CANNOT BE SPLIT FROM HERE: one `--dir` is one tree for the move AND the gate" is now false twice over, since `--gate-dir` shipped in `9vglxd` and this plan passes it. (ii) The same docstring's explanation that the cited evidence "is a path that resolves in the lane" must say which tree the citation now resolves in. (iii) `runner_shared.evaluate_backlog_close`'s `executed_overrides` paragraph should note that the INNER gate now has its own verified override, so a reader does not conclude the two are the same mechanism.
  - Depends on: E-04
  - Expected outcome: no docstring in the changed files still claims the gate tree and move tree are inseparable; a `git diff` of the three sites reads correctly against the shipped behavior.
  - PRESERVE `close_backlog_item`'s FINAL WARNING about the permissive direction. Its closing sentences explain that a lane-side carrier scan "is MORE likely to find a satisfying carrier than main's, and the error direction is the permissive one". That is CORRECT, is the justification for this entire plan, and must survive. Measured in F-02, it understates the case: the permissive verdict is not merely likelier, it is what the gate actually returns today.
  - Execution state: pending

### Task group 4: prove the tightening without a regression

- [ ] E-06 ADD THE ALLOWANCE AND REFUSAL CASES to `tests/test_backlog_handoff_close.py`, in `BacklogGateDirSplitTests`, which already builds the two-tree `main_repo`/`lane_repo` fixture this needs. Three cases: (1) ORDINARY SINGLE CARRIER, gate tree main, override naming the lane branch and main's `pending/` path, exits 0 and the item lands in the lane's `done/`; (2) SIBLING UNEXECUTED, same override, exits 1 with `carrier is not executed/implemented`, and the item moves nowhere; (3) FORGED ASSERTION, the override naming a ref whose tree still shows the carrier in `pending/`, exits 1.
  - Depends on: E-05
  - Expected outcome: three new tests passing, with case (2) proving the tightening and case (3) proving the assertion is verified rather than trusted.
  - THE FIXTURE MUST MAKE THE LANE A REAL `git worktree` OF MAIN, because the override is verified through the SHARED OBJECT STORE and a merely-copied directory has no shared store to read. Measured in F-07: `git worktree add` gives both trees the same `--git-common-dir`, and `git ls-tree <lane-branch>` from MAIN already lists the carrier under `executed/`. The existing `BacklogGateDirSplitTests` builds two INDEPENDENT scratch repos via `_make_scratch_repo` twice, so this is a REAL fixture change and not a reuse; do not assume the existing setup suffices.
  - CASE (3) IS THE ONE THAT CANNOT BE FAKED BY A WEAKER IMPLEMENTATION. An override that trusts its caller passes (1) and (2) and fails only (3). Write it first if that helps.
  - Execution state: pending

- [ ] E-07 PROVE THE NO-OP SHAPES ARE UNCHANGED, which is where a tightening of a shipped gate most plausibly causes collateral damage. Add tests covering: a NON-ISOLATED turn (`--no-isolate-worktree`, where `write_repo == repo`) emitting no new flags and reaching the same verdict; and the POST-MERGE call sites, where main itself already shows the carrier `executed/` so the HANDOFF arm passes unaided. Put the predicate-level cases in `tests/test_check_engine_release_gate.py` beside the existing `evaluate_blocking_close` tests.
  - Depends on: E-06
  - Expected outcome: the non-isolated and post-merge shapes pass with an EMPTY override and with no evidence citation, demonstrating the change is inert for every caller that is not an isolated pre-merge turn.
  - MEASURED AT AUTHORING (F-10), so this is a confirmation rather than an experiment: post-merge, `lane_executed_carrier_override(main, coord, ...)` returns `{}` and a main-rooted gate returns `legitimate=True` via HANDOFF with no evidence at all. The three post-merge call sites (`integrate_retired_lane`, `finish_reintegrated_item`, `perform_coordinator_backlog_close`) are therefore unaffected. If any of them turns out to refuse, STOP: that is a regression in a path this plan believed inert.
  - DO NOT ASSERT ON CALLER COUNTS OR SOURCE TEXT. Drive the behavior and assert on verdicts, exit codes and where the item file ends up, per the repository's no-code-pinning rule.
  - Execution state: pending

- [ ] E-08 RUN THE FULL SUITE AND RECONCILE IT AGAINST THE AUTHORED BASELINE, pasting the actual summary line. Run it BARE as `python3 -m pytest`.
  - Depends on: E-07
  - Expected outcome: a pasted summary whose pass count is at least the baseline's and whose only failure, if any, is the known pre-existing one named below.
  - BASELINE MEASURED AT AUTHORING on this lane at HEAD `8163b62ad`: `1 failed, 3419 passed, 2 skipped, 3 warnings in 67.82s`. THE ONE FAILURE IS PRE-EXISTING AND UNRELATED: `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a local-versus-UTC date-stamp skew already filed as backlog `fnb8pl` (and adjacent `2wae2x`, `o8l2y2`, `tl8qmc`). Its diff is purely `- 2026-09-30` versus `- 2026-10-01`. It is TIME-DEPENDENT, so it may be green when you run it; a green run is not evidence that you fixed it and a red one is not evidence that you broke it. Do NOT attempt to fix it here: it is outside `Scope-Paths` and owned elsewhere.
  - TREAT A SECOND FAILURE AS YOURS until proven otherwise, by re-running it at the pre-change commit in a clean worktree, and paste both results.
  - Execution state: pending

- [ ] E-09 UPDATE THE OPERATOR-FACING CLOSE DOCUMENTATION in `docs/artifact-lifecycles.md`, whose "Closing a release-blocking item" section is where an operator learns this rule and which `9vglxd` E-07 already amended for `--gate-dir`. State that the runner's in-lane close now evaluates the gate against the main checkout while moving the item in the lane, and that the two new flags exist for that caller. Add a `CHANGELOG.md` entry if and only if the file's current conventions call for one; verify the shape against the existing `aw backlog set` flag entries rather than trusting this sentence. WRITE NO EM OR EN DASHES in this user-facing prose.
  - Depends on: E-08
  - Expected outcome: an operator reading the section can tell which tree decides a close and which tree the item moves in; `git diff` shows no em or en dashes added to either file.
  - KEEP THE RUNNER'S INTERNALS OUT OF THE OPERATOR DOC. The verification mechanism, the injected-callable chain and the wrapper symmetry belong in the code comments E-05 corrects. The operator-visible fact is only which tree decides.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE GATE HAS TWO INDEPENDENT PREDICATES, and conflating them is the central hazard of this area. The OUTER one, `runner_shared.evaluate_backlog_close`, decides whether THIS RUN may close the item, filters carriers by KIND, requires ALL IPD carriers executed, and already carries a lane override (`executed_overrides`). The INNER one, `check_engine.evaluate_blocking_close`, is the shared authority behind the setter, `aw check` and the opt-in hook; it filters carriers by GATE and runs the three arms. This plan changes the INNER one's root and gives it its own override. Both are reached in a single close, outer first.
- A PLAN IS JUDGED BY ITS PATH AND A SPEC BY ITS FIELD, deliberately and asymmetrically. `check_engine._carrier_is_executed` tests `"executed" in p.parts` for `.ipd.md` and `- Status: implemented` for `.spec.md`. Any override must honor both or it silently never fires for one carrier kind.
- `--gate-dir` ALREADY EXISTS AND HAS NO CALLER. `backlog.run_set` resolves `gate_root` from it (defaulting to `repo_root`) and passes it as `evaluate_blocking_close`'s first argument, while the move still uses `repo_root`. It shipped in `9vglxd`, whose E-05 would have made the runner pass it and was WITHDRAWN under its own E-06 measurement, refiled as this plan's backlog item.
- THE GATE SITS BETWEEN THE METADATA WRITES AND THE MOVE, so a refusal writes nothing and moves nothing, and a `--dry-run` still refuses. `tests/test_backlog.py::test_backlog_set_status_done_dry_run_refuses_illegitimate_blocking_close_without_sidecar` pins this ordering and must stay green.
- `check_engine` ALREADY HAS GIT PLUMBING. `_git_capture(repo_root, args)` and `_blob_text(repo_root, ref, path)` exist in the module and back the commit-scoped `check.blocking-item-closed-without-gate` rule, so a ref-verified override needs no new subprocess helper.
- A LANE IS A REAL `git worktree`, sharing main's object store. So main can read the lane branch's tree with no filesystem access to the lane, which is what makes the override verifiable rather than merely asserted.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; adding `-n0` or a second `-q` is actively harmful.
- A CARRIER-SCAN AST GUARD CONSTRAINS THE HANDOFF LOOP'S SHAPE. `tests/test_carrier_scan_single_item_contract.py` refuses a loop-derived argument to `find_from_backlog_artifacts` and explicitly whitelists `evaluate_blocking_close`'s current `for p, br in find_from_backlog_artifacts(repo, item_id6)` shape. Restructuring that loop must stay inside a whitelisted shape.

## Findings

All measured at HEAD `8163b62ad` on this lane, on two-tree fixtures built with `git worktree add` so the lane genuinely shares main's object store. Reproduction scripts are under `tmp/qkl8fs/` (gitignored, not committed).

| # | Sev | Finding | Evidence | Consequence |
|---|---|---|---|---|
| F-01 | HIGH | THE GATE TREE AND THE MOVE TREE ARE THE SAME TREE FOR THE RUNNER TODAY, because `close_backlog_item` emits `--dir <repo>` and NO `--gate-dir`. Its argv is exactly `backlog set <id6> --status done --evidence <ev> --message <msg> --dir <repo> --no-commit`. | Read the `cmd = pinned_module_argv([...])` list in `runner_shared.close_backlog_item`; `--gate-dir` appears nowhere in `runner_shared.py`, and the module's only `gate_dir` variable is `backlog.run_set`'s `gate_root`. | This is the defect's mechanism. E-04 is the fix; E-05 corrects the docstring that still calls the split impossible. |
| F-02 | HIGH | THE LANE-ROOTED GATE RETURNS THE PERMISSIVE VERDICT ON A SHAPE MAIN WOULD REFUSE. Two same-gate IPD carriers, this run's executed in the lane, the sibling pending in both trees. Gate tree = LANE: `legitimate=True, path='HANDOFF'`, reason `gate 'next' handed off to a From-Backlog plan or spec`. Gate tree = MAIN: `legitimate=False`, reason naming BOTH carriers as not shipped. | Driven directly against `evaluate_blocking_close` on the two-tree fixture, both roots, same item text. | THE DEFECT, stated as a verdict rather than as a risk. E-06 case (2) pins the refusal. |
| F-03 | HIGH | A NAIVE `--gate-dir <main>` REFUSES THE ORDINARY SINGLE-CARRIER CLOSE, which is why this needs an override and not a one-line flag pass. Single carrier, lane shows `executed/`, main shows `pending/`. Gate=main with the LANE citation: `legitimate=False`, `gate 'next' is handed off to From-Backlog carrier(s) (...) but the work has not shipped (carrier is not executed/implemented)`. Gate=main with no evidence: identical refusal. | Same fixture, three gate-root/evidence combinations driven and pasted. | Confirms `9vglxd` E-06's withdrawal was correct and bounds this plan's design: the override in E-02 is load-bearing, not a convenience. |
| F-04 | HIGH | CITING MAIN'S `pending/` PATH WOULD "WORK", AND IS A FALSE CITATION. Gate=main with main's `pending/` path as `--evidence`: `legitimate=True, path='SATISFIED'`. The gate is satisfied by an UNEXECUTED plan, because `resolve_evidence_artifact` tests only that the path is safe, in-tree, existing and under a records tree; it never reads the carrier's state. | Driven as case D of the reproduction; verdict reason quotes the `pending/` path verbatim. | THE TRAP AN EXECUTOR MIGHT FALL INTO while making F-03 pass. E-02 therefore routes the fix through HANDOFF with a VERIFIED ref, never through a re-pointed citation. Also the reason the plan's own gate forbids "making E-06 pass" by changing the citation. |
| F-05 | MED | `resolve_evidence_artifact` IS STRICTLY PER-TREE, all four cells measured: (lane root, lane `executed/` path) True; (main root, lane `executed/` path) False; (main root, main `pending/` path) True; (lane root, main `pending/` path) False. | Four direct calls. | Exactly reproduces the item's claim 2 and `9vglxd` F-04. It is why the SATISFIED arm cannot rescue a main-rooted gate before the merge, and why E-02 works on HANDOFF instead. |
| F-06 | MED | THE CLOSE RUNS BEFORE THE MERGE, by 31 lines in one straight-line block of `execute_item_core`: finalize, carrier verification, `process_backlog_close(..., lane_repo=Path(work_dir))`, validation-runner construction, then `integrate_under_repository_lock`. Nothing between them merges anything. | Read `execute_item_core`'s isolated arm in source order; `process_backlog_close`'s own docstring states the split is deliberate and cites a 2026-09-13 measurement where a mid-run write to main left it dirty and a whole-tree gate then refused 27 of 42, 23 of 41 and 18 of 43 queue items. | Rules out the backlog item's route (c). Moving the close post-merge would reintroduce a measured production harm, so the plan keeps the write in the lane and moves only the DECISION. |
| F-07 | MED | THE LANE'S CARRIER STATE IS VERIFIABLE FROM MAIN WITH NO TRUST AND NO LANE FILESYSTEM ACCESS. `git worktree add` gives both trees the same `--git-common-dir`. From MAIN, `git ls-tree -r --name-only <lane-branch> -- .aw/records/plans/` lists exactly `.aw/records/plans/executed/<carrier>`; `git diff --name-status -M main..<lane-branch>` reports `R100 .../pending/<carrier> .../executed/<carrier>`. NEGATIVE CONTROL: a second lane that did NOT finalize lists the carrier under `pending/`. | Five git commands driven from main against two lane branches, one finalized and one not. | THE DESIGN BASIS FOR E-02. It is what makes this an override the predicate CHECKS rather than a `--trust-me` flag, and the negative control is what E-06 case (3) pins. |
| F-08 | MED | ROUTE (b) FROM THE BACKLOG ITEM IS UNNECESSARY, not merely harder. The item proposes bridging the EVIDENCE resolver to the move tree. But a resolver bridge would make F-04's false citation resolvable from main too, widening the SATISFIED arm for every caller of a shared predicate, while HANDOFF plus a verified ref needs no citation at all: measured, the overridden single-carrier case passes with `evidence=None`. | Compared the two routes on the same fixture; HANDOFF-with-override needs no evidence, whereas any resolver change necessarily touches the arm F-04 shows is already too permissive. | Records WHY the plan picks a HANDOFF-side override over the item's route (b). OQ-01 carries the decision. |
| F-09 | MED | A SEPARATE, PRE-EXISTING HOLE THIS PLAN DOES NOT CLOSE: the OUTER predicate ignores spec carriers entirely when any IPD carrier exists, because `if ipds:` returns before `others` is examined. Measured in ONE tree with NO lane: item with an executed IPD carrier plus a same-gate spec carrier still `approved`, outer returns `close=True`; the inner gate WOULD refuse (`...carrier is not executed/implemented`, naming both) but the outer's evidence citation fires SATISFIED and masks it. | Driven in a single scratch repo, no worktree, no `--dir` split; outer verdict, inner-with-evidence verdict and inner-without-evidence verdict all pasted. | DISTINCT FROM `lsbd32` (done, ANY-vs-ALL in the inner arm) and from `2o5wka` F-06 (a sibling with no gate line, inner permissive). This is the OUTER predicate dropping a carrier KIND. E-01 files it as its own item rather than folding it in: it needs no lane, so it is orthogonal, and fixing it would change which carriers the outer predicate considers. |
| F-10 | MED | THE NO-OP SHAPES ARE GENUINELY INERT. POST-MERGE: main shows the carrier `executed/`, `lane_executed_carrier_override(main, coord, ...)` returns `{}`, and a main-rooted gate returns `legitimate=True, path='HANDOFF'` with NO evidence. NON-ISOLATED: `override(repo, repo)` returns `{}` via the same-tree short-circuit and the verdict is unchanged. PRE-EXISTING SHARED-PATH SPEC CARRIER edited in the lane: passes against BOTH roots via SATISFIED, because the path is identical in the two trees. | Three fixtures driven: a merged lane plus a detached coordinator worktree, a single-tree repo, and a lane editing a spec that already existed in main. | BOUNDS THE BLAST RADIUS by measurement rather than by assertion. E-07 converts all three into tests. The third cell matters because it is the non-IPD shape that IS reachable from a lane, and it does not regress. |
| F-11 | MED | THE NON-IPD CARRIER CREATED IN THE LANE NEVER REACHES THE SETTER, so it needs no handling here. A spec the run creates in the lane does not exist in main at all: carriers visible from main `[]`, outer predicate `close=False` with `no plan or spec carries From-Backlog: <id6>, so no carrier proves the work`. | Driven on a lane that created a new spec carrier; outer verdict against main and against the lane both pasted. | Closes what would otherwise be an obvious gap in E-04's design. The OUTER predicate already refuses this shape when rooted at main, so the inner gate is never consulted. Worth recording so a reviewer does not read it as an unhandled case. |
| F-12 | LOW | THE SUITE HAS ONE PRE-EXISTING, TIME-DEPENDENT FAILURE. `1 failed, 3419 passed, 2 skipped` bare on this lane; the failure is `test_release_exempt_setter_roundtrip_and_parity`, whose diff is purely `- 2026-09-30` versus `- 2026-10-01` (local `date.today()` in `backlog.py` versus UTC in `status_set.py`). Already filed as `fnb8pl`, plus `2wae2x`, `o8l2y2`, `tl8qmc`. This lane's diff versus main touches none of `backlog.py`, `check_engine.py`, `runner_shared.py` or the host runners. | Bare `python3 -m pytest` summary plus the narrowed run's assertion diff; `git diff main --name-only` filtered for the gate files returns nothing. | E-08's baseline. Prevents an executor from either claiming credit for a green run or chasing a failure that is neither theirs nor in scope. |

## Proposed changes (ordered, validatable)

1. Re-measure the four dated premises and file the F-09 defect as its own item (E-01).
2. Add the verified lane-carrier override to the shared predicate, keyword-only and inert by default (E-02).
3. Surface it as two paired CLI flags and declare them (E-03).
4. Pass the gate root plus the override from the runner, across all four symbols in three files (E-04).
5. Correct the three docstrings this falsifies (E-05).
6. Pin the allowance, the tightening and the forged-assertion refusal (E-06).
7. Pin the no-op shapes so the blast radius is proven and not asserted (E-07).
8. Run the full suite and reconcile against the baseline (E-08).
9. Update the operator-facing close documentation (E-09).

ORDER IS LOAD-BEARING IN TWO PLACES. E-02 BEFORE E-03 BEFORE E-04 because each is the previous one's only consumer: the predicate parameter must exist before a flag can carry it, and the flag must exist before the runner can emit it. Shipping in this order also means that if E-04 has to be abandoned the override still exists and is tested, exactly the property that let `9vglxd` ship `--gate-dir` after withdrawing its runner adoption. E-06 BEFORE E-07 because E-06 proves the change works and E-07 proves it changed nothing else; running them in the other order invites an executor to treat the inert shapes as sufficient evidence.

## Deferred / out of scope (with reason)

- F-09, THE OUTER PREDICATE'S SPEC-CARRIER BLIND SPOT. Deferred because it is a DIFFERENT defect with a different cause: it is reachable in one tree with no lane and no `--dir` split, so nothing in this plan's fix touches it, and closing it changes which carrier KINDS the outer predicate considers, which has its own blast radius over the live multi-carrier population.
  - Carrier-Declined: NO CARRIER EXISTS YET BY CONSTRUCTION, because E-01 FILES ONE as its first action and the filed item's id6 cannot be known at authoring. This is the deliberate "file it rather than promise it" shape `d1ldvk` set as precedent, inverted only in timing: the obligation is an EXECUTION STEP of this plan (E-01), validated by V-01, which requires the new item's id6 plus `aw find backlog` output proving it is not a duplicate of `lsbd32` or `d1ldvk`. So the obligation cannot vanish silently when this plan reaches `executed`: a V-01 with no id6 pasted FAILS. If this plan is retired unexecuted, F-09's full measurement survives in the Findings table for whoever files it.
- THE POSITIONAL-SPELLING BYPASS. `aw backlog set done <sel>` (no `--status`) dispatches to `status_set.run_set_command`, which never calls the shared predicate at all. Out of scope here, and the runner is unaffected because it uses the `--status` spelling deliberately.
  - Carrier: 47ttnv
  - Carrier-Evidence: .aw/records/plans/executed/20260929-gatebypass-01-47ttnv-run-the-shared-release-gate-close-predicate-on-the-positiona.ipd.md
- THE ANY-VS-ALL DIVERGENCE, closed by `2o5wka` (executed), which tightened the HANDOFF arm from ANY-carrier to ALL-carrier semantics. This plan DEPENDS on that having landed: the `all(...)` fold is exactly what E-02's override plugs into.
  - Carrier-Declined: NOTHING IS OWED. This row records a SATISFIED PRECONDITION rather than an outstanding defect, so naming a carrier would assert pending work that does not exist. The fix shipped in plan `2o5wka` and its backlog item `lsbd32` is `done`; E-02's instruction to apply the override at the HANDOFF call site is what keeps this plan compatible with it.
- `2o5wka` F-06's UNGATED-SIBLING RESIDUAL, where a sibling carrier with no `- Blocks-Release:` line is dropped by the same-gate filter. Deferred because widening that FILTER changes which carriers the arm considers, a different decision from changing how ONE discovered carrier is judged.
  - Carrier-Declined: ALREADY OWNED AND DELIBERATELY UNFILED UPSTREAM. `2o5wka` OQ-02 defers this residue with an EXPLICIT TRIGGER (file a carrier only if `check.from-backlog-gate-mismatch` is ever weakened or made advisory, because that rule is what keeps the shape visible as an error today), and its own deferred row declines a carrier on that reasoning. Filing one here would duplicate a decision another plan already recorded, and would do so for a shape this plan does not touch.
- MAKING THE OVERRIDE AVAILABLE TO A HAND CLOSE WITH NO LANE.
  - Carrier-Declined: NOT AN OBLIGATION. A hand close has no second tree to name, so there is no deferred work here, only a boundary: the flags exist for the one caller that has a lane. Recording a carrier would misrepresent a scope fence as unfinished work.
- THE EXISTING UNDECLARED FLAG DEBT on `aw backlog set` (`--evidence`, `--yes`, `--commit/--no-commit` accepted but undeclared), which E-03 deliberately does not fix while declaring the two new flags.
  - Carrier-Declined: PRE-EXISTING AND DOCUMENTED AT THE SITE. `command_surface.py`'s own comment names all three flags as accepted-but-undeclared and records that the agreement test is one-directional, so the debt is already visible to the next reader of that file. It is not created, worsened or hidden by this plan, and folding it in would widen the diff into a surface this plan otherwise only appends to.
- THE `fnb8pl` DATE-CLOCK SUITE FAILURE, pre-existing and outside `Scope-Paths`, recorded as F-12 so an executor neither claims credit for a green run nor chases it.
  - Carrier: fnb8pl

## Scope check

- Over-scope: none. `agent_workflows/check_engine.py` carries E-02; `agent_workflows/backlog.py`, `agent_workflows/cli.py` and `agent_workflows/command_surface.py` carry E-03; `agent_workflows/runner_shared.py` plus `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` carry E-04 and E-05; `tests/test_backlog_handoff_close.py` carries E-03's declaration assertion and E-06; `tests/test_check_engine_release_gate.py` carries E-07; `docs/artifact-lifecycles.md` and `CHANGELOG.md` carry E-09. E-01 and E-08 write no tracked file beyond this plan's own execution notes, except the backlog item E-01 files, which is a new file under `.aw/records/backlog/open/` and is the normal product of `aw backlog new`.
- THE TWO HOST RUNNERS ARE IN SCOPE FOR EXACTLY TWO FORWARDED KEYWORDS and nothing else. This is a correction learned from `9vglxd`'s review (its F-11/PR-701), not an opportunistic widening: `process_backlog_close` calls an INJECTED `close_backlog_item`, and the callable is supplied by a thin wrapper defined in each host, so two of E-04's four edits necessarily live there. An executor changing anything else in either host runner has left this plan's fence.
- `agent_workflows/check_engine.py` IS IN SCOPE, and this differs from `9vglxd`, which deliberately kept it out. The reason is that the two plans do different things: `9vglxd` only let a CALLER choose the existing predicate's root, whereas this plan must change how the predicate JUDGES one carrier, and there is no way to do that from outside it. The change is bounded to one new keyword-only parameter and its use inside the HANDOFF arm; the three arms, their verdicts and every existing caller's behavior are untouched.
- Under-scope, DELIBERATE and stated plainly: this closes the gate-tree hole for the RUNNER'S ISOLATED PRE-MERGE CLOSE only. A hand close still gates against whatever tree `--dir` names unless the operator passes `--gate-dir`, and the F-09 blind spot in the outer predicate remains open under its own item. An operator reading "the in-lane close is now gated against main" must not conclude that every close is.

## Required tests / validation

- THE TIGHTENING MUST BE DEMONSTRATED, not asserted: the two-carrier sibling-unexecuted shape must exit 1 through the real CLI with the override in place, and the item must move nowhere (E-06 case 2). A plan that only shows the allowance case has not shown it fixed anything.
- THE ORDINARY CLOSE MUST STILL SUCCEED end to end, with the gate tree set to main and the override in place, exiting 0 and landing the item in the move tree's `done/` (E-06 case 1). If it cannot, paste the refusal and STOP rather than relaxing an arm to fit; a loosened gate is not an acceptable way to pass this.
- THE ASSERTION MUST BE PROVEN VERIFIED, by a case whose override names a ref that does not show the carrier executed and which therefore refuses (E-06 case 3). This is the test that distinguishes this plan's design from a `--trust-me` flag, and an implementation that trusts its caller passes every other case.
- THE INERT SHAPES MUST BE PROVEN INERT: non-isolated and post-merge, with an empty override and no evidence citation (E-07).
- BOTH HOST WRAPPERS MUST BE SHOWN WIDENED IDENTICALLY, pasted side by side (V-04), so a one-sided edit is visible rather than inferred.
- THE FULL SUITE, run bare, reconciled against the `1 failed, 3419 passed, 2 skipped` baseline with the single known pre-existing failure named (E-08).
- `tests/test_backlog.py::test_backlog_set_status_done_dry_run_refuses_illegitimate_blocking_close_without_sidecar` MUST STAY GREEN, since it pins the gate-before-write ordering that E-03's new usage error must not disturb.
- NO TEST MAY READ PRODUCTION SOURCE TEXT, count callers, or assert on docstrings. Drive the CLI and the predicates and assert on verdicts, exit codes, stderr strings and where the item file ends up.

## Spec / documentation sync

- `docs/artifact-lifecycles.md`: E-09 updates the "Closing a release-blocking item" section, which `9vglxd` E-07 already amended for `--gate-dir`, to say which tree decides a runner close.
- `CHANGELOG.md`: E-09 adds an entry for the two new flags if the file's conventions call for one, verified against the existing `aw backlog set` flag entries.
- NO `.spec.md` FILE IS AMENDED, and none is declared in `Scope-Paths`. Checked at authoring: the close-legitimacy contract lives in the repo-local `AGENTS.md` paragraph and `.aw/records/backlog/README.md`, both of which state the THREE ARMS and the ALL-carrier rule. This plan changes neither: it changes which TREE one caller evaluates the arms against, and adds an override that only makes a main-rooted evaluation see what the lane genuinely contains. If an executor finds themselves needing to edit a spec, that is a signal the change grew beyond this fence; stop and report.
- `AGENTS.md` IS DELIBERATELY NOT IN `Scope-Paths`, and this is a measured decision rather than an omission. Its "Close-legitimacy rule" paragraph describes the three fixes available to a HAND close and remains true verbatim. Two plans are already co-editing that paragraph (`2o5wka` E-06a landed the carrier-count wording, `47ttnv` owns the enforcement sentence); adding a third editor for a change that does not alter the rule would create a conflict for no gain.

## Open questions

### OQ-01: Should the override be verified against a git ref, or should the evidence resolver bridge to the move tree as the backlog item's route (b) proposes?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED BY MEASUREMENT AS THE VERIFIED REF (F-07, F-08), with the rejected alternative recorded because it is the item's own suggestion. THE CASE FOR THE REF. The lane is a real `git worktree` sharing main's object store, so main can confirm the carrier's lane-side bucket with `git ls-tree` and never has to believe the caller; the negative control in F-07 shows an unfinalized lane cannot pass. It also needs NO evidence citation at all, so it leaves the SATISFIED arm completely untouched. THE CASE AGAINST ROUTE (b), which is stronger than "harder": F-04 measures that citing main's `pending/` path ALREADY satisfies the gate, because `resolve_evidence_artifact` tests path safety and existence and never reads carrier state. Bridging that resolver across trees would widen an arm that is already too permissive, and it would do so for EVERY caller of a shared predicate that also backs `aw check` and the pre-commit hook. THE CASE A REVIEWER MIGHT MAKE FOR ROUTE (b), stated fairly: it is a smaller diff, confined to one helper, and it needs no new CLI surface. That is real, and it is why this is recorded rather than assumed. It is rejected because the smaller diff buys a permissive change to a shared gate, which is the opposite of this plan's purpose. REVERSIBLE: yes. The override is additive and inert by default, so it can be removed without changing any existing caller.

### OQ-02: Should the runner pass the override for every call site, or only for the isolated pre-merge turn?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED AS ISOLATED-ONLY, from F-10 rather than from caution. Measured post-merge, `lane_executed_carrier_override` returns `{}` and a main-rooted gate passes via HANDOFF with no evidence at all, so the three post-merge call sites (`integrate_retired_lane`, `finish_reintegrated_item`, `perform_coordinator_backlog_close`) need nothing: main genuinely sees the carrier executed. The non-isolated turn short-circuits on the same-tree check. So passing an override there would be inert at best and, worse, would make the emitted argv claim the close depended on a ref it did not need, which misleads anyone reading a run record. `process_backlog_close` already computes `isolated`, so the condition costs nothing. REVERSIBLE: yes, a one-line condition.

### OQ-03: Should E-04 be split into its own plan, given that `9vglxd` withdrew the equivalent item?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED AS ONE PLAN, with the opposite answer to `9vglxd`'s and for a stated reason. There, the runner adoption was withdrawn because the ordinary close could not be made to pass WITHOUT a mechanism that did not exist; the honest outcome was to ship the flag and refile. HERE the mechanism is E-02, and it is this plan's own deliverable, so splitting would separate the override from its only consumer and leave a tested-but-unused parameter with no caller to justify its shape. The ordering already provides the same safety the split would: E-02 and E-03 stand alone and remain valuable if E-04 is abandoned, which is precisely how `--gate-dir` survived `9vglxd`. REVERSIBLE: yes, E-04 and E-05 could be lifted into a follow-on plan at review with no rework to E-02 or E-03.

### OQ-04: Does tightening this gate need the live corpus grandfathered, as `lsbd32` asked for the ANY-vs-ALL fix?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED AS NO GRANDFATHERING NEEDED, on the mechanism `2o5wka` F-08 already measured rather than on a fresh corpus count. That plan tightened the same predicate and found `aw check release-gates` still reported `errors 0` afterwards, because `check_release_gate_consistency`'s Rule 1 is COMMIT-SCOPED by construction and its own comment states that historically closed `done/` items are never retroactively flagged. This plan's change is strictly narrower: it alters no arm and no verdict for any existing caller, and affects only a verdict computed live during an isolated runner turn. So no already-closed item can be re-judged, and there is nothing to grandfather. A REVIEWER SHOULD STILL CHECK ONE THING: that `aw check release-gates` is clean after the change, which E-08's suite run covers through the existing release-gate tests.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: four pasted measurements from execution HEAD, each naming the HEAD it ran at: (a) the two-carrier lane-rooted verdict, which must still read `legitimate=True` with `path='HANDOFF'`; (b) the single-carrier main-rooted refusal, quoting the reason string; (c) the four-cell `resolve_evidence_artifact` matrix; (d) the mixed IPD-plus-unimplemented-spec outer verdict reading `close=True`. PLUS the id6 of the newly filed F-09 backlog item and the `aw find backlog` output showing it is not a duplicate of `lsbd32` or `d1ldvk`. If any premise has reversed, the required evidence is instead a written STOP with the contradicting output.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted direct calls to `evaluate_blocking_close` on a two-tree fixture showing FOUR cells: (1) main-rooted, override naming the single carrier and the lane branch ref, NO evidence, returning `legitimate=True, path='HANDOFF'`; (2) main-rooted, same override, with an unexecuted SIBLING present, returning `legitimate=False`; (3) main-rooted, override naming a ref whose tree still shows the carrier in `pending/`, returning `legitimate=False`; (4) main-rooted with NO override, returning `legitimate=False`, proving the parameter defaults inert. Cell (3) must be pasted with the ref name so a reviewer can see the assertion was verified rather than trusted. Also paste a spec-carrier cell proving the override reads `- Status:` from the ref's BLOB rather than inspecting a directory.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: three pasted CLI runs with exit codes: the paired flags on the single-carrier shape exiting 0; `--lane-carrier-ref` without `--lane-carrier-path` exiting 2 with stderr naming the missing flag; and the same omission reversed, also exiting 2. PLUS the declaration-test output showing both new flags present in `command_surface.get_declaration("backlog set").legacy_flags`. The exit-2 cases must also show the item file UNMOVED, proving the usage error fires before any write.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the emitted argv for an isolated turn, pasted, showing `--dir <lane>`, `--gate-dir <main>` and both override flags with the carrier path in MAIN's spelling; the emitted argv for a NON-isolated turn, pasted, showing none of the three new flags; and BOTH host wrappers' post-change source pasted SIDE BY SIDE so a one-sided edit is visible. Capture the argv by driving the runner path and intercepting the command, not by reading the source and asserting it looks right.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `git diff` of the three docstring sites, pasted, showing that no text still claims the gate tree and move tree cannot be split, and showing that `close_backlog_item`'s closing warning about the permissive direction SURVIVES verbatim or strengthened. A diff that deletes that warning FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted test output for the three new cases, each identified by name, with the runner's own summary line. Case (2) must show exit 1 and the `carrier is not executed/implemented` string, plus an assertion that the item file stayed put. Case (3) must show exit 1 against a ref that does not show the carrier executed. Also paste evidence that the fixture builds the lane with `git worktree add` (for example the `git worktree list --porcelain` output or the fixture's own command), since a copied directory would make case (3) vacuous.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted test output for the non-isolated and post-merge cases, each showing the verdict reached with an EMPTY override and no evidence citation. Include the post-merge `lane_executed_carrier_override(...)` returning `{}`, since that is the fact that makes those call sites inert. State explicitly that no test added here reads production source text or counts callers.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: the ACTUAL bare `python3 -m pytest` summary line, pasted verbatim, with the pass count at or above 3419. If a failure other than `test_release_exempt_setter_roundtrip_and_parity` appears, paste BOTH that failure and a re-run of it at the pre-change commit in a clean worktree, and state which commit that was. A claim of success without the pasted summary line fails this item.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: `git diff` of `docs/artifact-lifecycles.md` and `CHANGELOG.md`, pasted, plus the output of a grep for em and en dashes over the changed lines showing none were added. If no `CHANGELOG.md` entry was added, state which existing entries were inspected and why the conventions did not call for one.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and has NOT been reviewed or approved. It requires `/plan-review` and then explicit human approval (`- Status:` must reach `approved`) before any execution. No `- Readiness:` field is present, deliberately: that field is an OUTPUT of `/plan-review` and writing it at authoring would forge a review that has not happened.

Execution follows the repository's execution contract: commit only the paths this plan declares, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`; paste ACTUAL runner output for every claim that a test passed; and run the suite BARE as `python3 -m pytest`.

FOUR GATES ARE SPECIFIC TO THIS PLAN and a reviewer should hold the executor to them.

FIRST, THIS TIGHTENS A SHIPPED RELEASE GATE, so E-01 is not a formality. Every premise is a dated measurement against a predicate that three other plans have recently changed (`2o5wka` tightened its HANDOFF arm, `9vglxd` added `--gate-dir`, `47ttnv` is pending against the adjacent spelling). If F-02 or F-03 has reversed, the correct outcome is to STOP and re-scope, and in particular: if a main-rooted gate now passes the single-carrier shape unaided, this plan should collapse to the one-line `--gate-dir` pass that `9vglxd` already wrote, not build an override nothing needs.

SECOND, DO NOT MAKE E-06 PASS BY CHANGING THE CITATION. F-04 measures that citing main's `pending/` path satisfies the gate via SATISFIED, because the evidence resolver never reads carrier state. That route makes the ordinary close pass while asserting a release gate was satisfied by an UNEXECUTED plan, which is strictly worse than the defect being fixed. If the only way an executor can get E-06 case (1) green is by re-pointing the citation, that is a signal to stop and report, not a solution.

THIRD, THE OVERRIDE MUST BE VERIFIED AND SINGULAR. An implementation that trusts a caller-supplied flag passes E-06 cases (1) and (2) and fails only case (3), so case (3) is the one that actually constrains the design. An override that generalizes from one carrier to "whatever the lane shows executed" would reopen the multi-carrier hole `2o5wka` just closed over 18 live gated items; siblings must still be read from the gate tree with no override.

FOURTH, WIDEN BOTH HOST WRAPPERS OR NEITHER. `agy_runipd` imports from `oc_runipd`, and `runner_shared`'s module docstring warns that changing one runner's symbol "would silently give BOTH drivers that runner's behavior". A one-sided edit gives one host a gated close and the other the status quo with no test objecting, which is why V-04 requires the two pasted side by side.
