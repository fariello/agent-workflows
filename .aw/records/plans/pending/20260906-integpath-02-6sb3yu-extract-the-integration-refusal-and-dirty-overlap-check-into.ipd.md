# IPD: Extract the integration refusal and dirty-overlap check into one shared module

- Date: 2026-09-06
- Kind: child
- Concern: `dirty_tree_overlap` and `integrate_lane_branch` are DUPLICATED in both host runners and have ALREADY DRIFTED, similarity 0.717 and 0.651, and neither appears in `runner_shared.py`. RE-VERIFIED AT REVIEW 2026-09-07 (HEAD `86581595`) with corrected anchors: `oc_runipd.py:1944` / `agy_runipd.py:1232`, and `oc_runipd.py:1976` / `agy_runipd.py:1259`. The agy line numbers moved between authoring and review, so RE-LOCATE BY SYMBOL rather than by any number in this plan. The three sibling children of this Set (03's deferral ladder, 04's `integrate` verb and resume path) all modify exactly this logic, so landing them against two copies would mean writing every change twice and would deepen a divergence the `rununify` Set already exists to close.
  THE EXTRACTION IS SAFE BECAUSE THE DRIFT IS ALMOST ENTIRELY COMMENTARY, and that is measured rather than hoped. An AST-level diff of the two `dirty_tree_overlap` bodies shows the ONLY differences are three added comment/docstring lines on the oc side; the executable statements are identical. For `integrate_lane_branch` the diff is 44 lines of which all but ONE are docstring or comment: the single behavioral difference is the merge commit subject, `integrate(aw agy run): merge verified lane {id6} to main` versus `integrate(aw oc run): ...`. So this is a de-duplication with one host-varying string, not a reconciliation of two designs.
  THIS CHILD IS ORDER 02 BECAUSE IT IS THE SEAM THE REST OF THE SET BUILDS ON. It changes NO behavior by itself; its whole value is that children 03 and 04 then write their changes once. Doing it after them would require redoing their work.
- Scope: Move `dirty_tree_overlap` and `integrate_lane_branch` into `runner_shared.py` as ONE implementation each, parameterizing the single host-varying value (the merge commit subject's host label) and injecting the driver-specific collaborators each already needs. Both runners bind the shared objects instead of defining their own. NO behavior change on either host: the refusal conditions, the gate call, the merge strategy, the abort path, and every returned `kind` stay exactly as they are.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: executed:29wvmj
- Status: approved
- Readiness: go-pending-approval
- Set: integpath
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 6sb3yu
- Approval: 2026-09-08, recorded via aw ipd set: status set to approved
- From-Backlog: 5wdoze
- Blocks-Release: next

## Workflow history
- 2026-09-08 approved (aw set): status set to approved
- 2026-09-07 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-201..PR-207 all FIXED, no unfixed BLOCKER/HIGH, no open questions; Readiness go-pending-approval

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored as the shared-code seam three of the four `integdefer` backlog items independently ask for ("The ladder belongs in shared code with both calling it, not copy-pasted twice" in `5wdoze`; "Put it in `runner_shared.py` with both runners calling it, NOT copy-pasted into two files" in `p8ni63`; both citing `cnwy8g` on the 40-symbol import coupling). Splitting it out as its own child is a deliberate decision rather than folding it into the ladder: a pure move with an identity assertion is verifiable in a way that a move-plus-behavior-change is not, and children 03 and 04 both edit this same logic, so extracting first means each writes its change ONCE. MEASURED AT HEAD `a4279302`, and the measurement is what makes the move safe rather than merely desirable: `dirty_tree_overlap` differs between hosts ONLY by three comment/docstring lines (executable statements byte-identical), and `integrate_lane_branch`'s 44-line diff is entirely docstring and comment EXCEPT one string, the merge subject's `aw agy run` versus `aw oc run` label. Also verified: neither symbol is in `runner_shared.py` today, and `agy_runipd.py` already imports 46 names from `oc_runipd.py`, so binding shared objects is the established pattern here, not a new one. Item-Dependencies declares `executed:29wvmj` because this child's own validation requires merging a lane, which child 01 must first make possible without `--no-verify`.

## Goal

One implementation of the integration refusal and the dirty-overlap check, so the three behavior changes this Set makes land once instead of twice and cannot drift apart afterwards.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: move the pure predicate first

- [x] E-01 Move `dirty_tree_overlap` into `runner_shared.py` as ONE implementation and have both runners bind it. This one is a genuinely PURE move: the measured diff between the two copies is three comment/docstring lines with byte-identical executable statements, so the shared version should be the oc copy (whose extra comments document the porcelain format and the rename `orig -> dest` handling) and the agy definition should be DELETED, not kept as a wrapper.
  BIND IT WITH THE `as <same-name>` RE-EXPORT FORM that `agy_runipd.py` already uses for 46 symbols from `oc_runipd.py`. That form is not cosmetic: the module records that `ruff` removed 6 such re-exports on a first commit attempt and only a cross-driver symmetry test caught it, so an unmarked import of a symbol this module does not itself call is at risk of being "cleaned up".
  PRESERVE THE RENAME HANDLING EXACTLY. The function treats BOTH endpoints of a `orig -> dest` porcelain entry as dirty. That is load-bearing for this Set: a rename is precisely how a plan moves into `executed/`, so dropping either endpoint would silently narrow the refusal and let an integration proceed over a path it should have refused.
  - Depends on: none
  - Expected outcome: one `dirty_tree_overlap` in `runner_shared.py`; both runners bind it; no runner defines its own; a test asserts OBJECT IDENTITY between the two runners' bound symbol, not merely equal behavior.
  - Execution state: performed

### Task group 2: move the integration function, parameterizing the one host-varying value

- [x] E-02 Move `integrate_lane_branch` into `runner_shared.py`, parameterizing the SINGLE host-varying value. The measured difference is one string: the merge commit subject is `integrate(aw agy run): merge verified lane {id6} to main` on one host and `integrate(aw oc run): ...` on the other. Pass the host label (or the full subject template) as an argument with NO default, so a caller cannot silently inherit the wrong host's label in its commit messages, which would misattribute integrations in git history.
  KEEP THE oc DOCSTRING as the shared one. It is the fuller of the two (it enumerates steps 0 through 3, the gate's detect-versus-resolve split, the `--ff-only` then controlled `--no-ff` fallback, the abort-leaves-main-clean guarantee, and all three returned `kind` values), and the agy copy is a compressed paraphrase of the same behavior. Losing the detail would remove the only prose statement of the integration contract.
  DO NOT CHANGE ANY BEHAVIOR: the pre-gate dirty refusal, the `execute_merge_and_revalidate_gate` call, `--ff-only` first, the controlled `--no-ff` fallback when main advanced, the abort on real conflict so main keeps no markers or partial merge, and the exact returned `kind` vocabulary (`integrated`, `integration-blocked`, `merge-conflict`) must all survive byte-for-byte in effect. This child's entire claim is that it changes nothing observable.
  - Depends on: E-01
  - Expected outcome: one `integrate_lane_branch` in `runner_shared.py` taking an explicit host label; both runners bind it and pass their own label; each host's merge commit subject is unchanged from today.
  - Execution state: performed

- [x] E-03 Resolve the COLLABORATOR question, which MEASUREMENT AT REVIEW (2026-09-07) shows is far smaller than this plan first claimed. The complete set of external names the two bodies call is FOUR: `_run_git`, `build_lane_outcome`, `conflicted_paths`, `format_merge_conflict_reason` (plus builtins and `Path`). THREE OF THE FOUR ARE ALREADY SHARED and already the SAME OBJECT in both drivers, verified at runtime: `oc._run_git is agy._run_git is runner_shared._run_git` is True, and the same holds for `conflicted_paths` and `format_merge_conflict_reason`. So for those three the move requires NOTHING: the shared function simply calls its own module-level names. NO INJECTION IS NEEDED FOR THEM, and adding a `run_checked=`-style parameter for them would be cargo-culting a precedent that exists for a different reason.
  THE ONLY REAL COLLABORATOR QUESTION IS `build_lane_outcome`, which this plan never named and which is DUPLICATED in both drivers (0.887 similarity) and ABSENT from `runner_shared.py`. Its EXECUTABLE AST is IDENTICAL across hosts (verified); the entire diff is docstring. So it is a pure move on the same evidence as `dirty_tree_overlap`, and the honest options are: (i) move it to `runner_shared.py` too, keeping the fuller oc docstring, which is the smallest change that lets the shared `integrate_lane_branch` call a module-level name; or (ii) inject it, following the `git_head(..., run_checked=)` precedent. PREFER (i) and record the choice: it removes a duplicate rather than parameterizing around one, and it is the same class of pure move this child already justifies. If you choose (ii), state why in `Observed evidence`.
  DO NOT INVENT THE `DriverError` PROBLEM: IT IS ALREADY FIXED. This plan's earlier text claimed "the two `DriverError` classes are distinct" and made OQ-02 turn on it. MEASURED FALSE at review: there is exactly ONE `DriverError` in the repository (`runner_shared.py:159`) and both drivers re-export it, so `oc.DriverError is agy.DriverError is runner_shared.DriverError` is True. Neither moved body raises or catches it anyway. The surviving `enforce_dependency_preflight` wrapper in `agy_runipd.py` and the stale comment at `:278` are historical residue of the already-completed fix, NOT a live trap; do not "restore" a translation layer, and do not treat that comment as current.
  CONFIRM NO IMPORT CYCLE IS CREATED, which remains a genuine requirement: `runner_shared.py` imports NEITHER driver today (verified by grep), and the shared function must keep it that way.
  - Depends on: E-02
  - Expected outcome: the shared function references NO name from either driver module; `build_lane_outcome` is resolved by option (i) or (ii) with the choice recorded; the three already-shared collaborators are used directly with no needless injection; `runner_shared` still imports neither driver.
  - Execution state: performed

### Task group 3: prove the move changed nothing

- [x] E-04 Add the SYMMETRY AND IDENTITY guard that keeps the two copies from reappearing. Assert at the AST or object level that neither `oc_runipd` nor `agy_runipd` DEFINES `dirty_tree_overlap` or `integrate_lane_branch` (and `build_lane_outcome` too, if E-03 took option (i)), and that the symbol each one exposes IS the same object as `runner_shared`'s.
  WRITE THE GUARD OVER A SYMBOL LIST, not as three copy-pasted assertions, so a future extraction extends it by adding one name. A guard whose shape discourages extension is how the next re-fork slips through.
  MAKE THE GUARD SYMMETRIC OVER BOTH RUNNERS. This is a recorded failure mode in this repository, not a hypothetical: `render_stream` was extracted a Set ago with a guard that checked only `oc_runipd`, and `agy_runipd` then re-forked four of its symbols with nothing noticing. A one-sided guard is how an extraction silently un-does itself.
  - Depends on: E-03
  - Expected outcome: a symmetric test fails if EITHER runner re-defines either symbol, and asserts object identity rather than behavioral equivalence.
  - Execution state: performed

- [x] E-05 Prove NO BEHAVIOR CHANGED, which is this child's whole contract and cannot rest on the suite alone. The runner suites are asymmetric enough that an agy-side regression can pass unnoticed, so exercise BOTH hosts explicitly:
  (a) a REAL INTEGRATION on each host in a throwaway repository: a lane that merges clean must still integrate, and its merge commit subject must still carry that host's own label (`aw oc run` / `aw agy run`), which is the one value E-02 parameterized and therefore the one most likely to be wired wrong;
  (b) the DIRTY REFUSAL on each host: an overlapping dirty path in main must still yield `integration-blocked` with main untouched and the lane branch preserved;
  (c) the RENAME endpoints: a porcelain `orig -> dest` entry must still make BOTH paths count as dirty (E-01);
  (d) the ABORT path: a real merge conflict must still leave main clean with no markers and return `merge-conflict`.
  Run the suite BARE (`python3 -m pytest`) and state before/after counts. Note that `tests/test_run_viewer.py` reads the gitignored `.aw/records/runs/`, so it fails in a bare worktree and passes in the real checkout: VALIDATE IN THE REAL CHECKOUT, because green elsewhere proves nothing.
  - Depends on: E-04
  - Expected outcome: both hosts integrate, refuse, and abort exactly as before; each host's commit subject is unchanged; the rename handling is intact; bare suite green with counts stated.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE DRIFT IS COMMENTARY, NOT DESIGN, and this is the measurement the plan rests on: `dirty_tree_overlap` differs by three comment/docstring lines with identical executable statements; `integrate_lane_branch`'s 44-line diff is all docstring and comment except the `aw agy run` / `aw oc run` label. Verified by AST extraction plus `difflib` at HEAD `a4279302`.
- BINDING, NOT COPYING, IS THE ESTABLISHED PATTERN HERE. `agy_runipd.py` already imports 46 names from `oc_runipd.py` with the `as <same-name>` re-export form, and its own comments give the reason: a duplicated copy "is how the deleted `_read_deps` pair came to be identically wrong in both drivers", and `ruff` stripped 6 re-exports until a symmetry test caught it.
- `runner_shared.py` INJECTS COLLABORATORS rather than importing driver internals: `git_head`, `git_status`, and `git_common_dir` all take `run_checked` as a keyword-only argument (`runner_shared.py:312`, `:327`, `:331`; the plan's earlier `:224/:239/:243` citations were stale). THE PRECEDENT EXISTS FOR A SPECIFIC REASON and does not apply blindly here: those three need injection because `run_checked` is HOST-SPECIFIC (it takes an `env_builder` that is opencode-only). Three of this child's four collaborators are already SHARED SINGLETONS, so injecting them would be cargo-culting; see E-03.
- THERE IS EXACTLY ONE `DriverError` AND IT IS ALREADY SHARED (`runner_shared.py:159`), re-exported by both drivers, so `oc.DriverError is agy.DriverError` is True. The two-class problem was FIXED by an earlier Set (`oc_runipd.py:106-110` records it). The comment at `agy_runipd.py:278` still describes the pre-fix world and is STALE; do not read it as current, and do not add a translation layer this child does not need.
- THREE OF THE FOUR COLLABORATORS ARE ALREADY SHARED OBJECTS: `_run_git`, `conflicted_paths`, and `format_merge_conflict_reason` are all `is`-identical across both drivers and `runner_shared`. The FOURTH, `build_lane_outcome`, is duplicated in both drivers and absent from the shared module, with an IDENTICAL executable AST (0.887 similarity, docstring-only diff), which makes it a pure move on the same evidence as `dirty_tree_overlap`.
- A ONE-SIDED EXTRACTION GUARD SILENTLY FAILS. `render_stream` was extracted with an oc-only guard and agy re-forked four symbols unnoticed. Every guard this child adds must assert over BOTH runners.
- THE `kind` VOCABULARY IS A CONTRACT read by callers and by run state: `integrated`, `integration-blocked`, `merge-conflict`. `integration-blocked` is currently in `TERMINAL_STATES` (`oc_runipd.py:301-313`); child 03 changes that, and this child must NOT.
- Run the suite BARE: `python3 -m pytest`. Validate `test_run_viewer.py` in the REAL checkout, since it reads gitignored run records.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | Both symbols are duplicated across the two runners and absent from the shared module. AGY LINE NUMBERS CORRECTED at review (the drivers churned since authoring); RE-LOCATE BY SYMBOL, never by these numbers. | `oc_runipd.py:1944` and `agy_runipd.py:1232` (`dirty_tree_overlap`); `oc_runipd.py:1976` and `agy_runipd.py:1259` (`integrate_lane_branch`); `runner_shared.py` defines neither (verified 2026-09-07; the plan's earlier agy citations `:1109`/`:1156` were stale) |
| F-2 | **They have already drifted**, which is why extraction is corrective rather than cosmetic: similarity 0.72 (`dirty_tree_overlap`, 30 vs 25 lines) and 0.65 (`integrate_lane_branch`, 92 vs 76 lines). | AST + `difflib` measurement 2026-09-06 |
| F-3 | **THE DRIFT IS SAFE TO COLLAPSE, MEASURED.** `dirty_tree_overlap`'s entire diff is three added comment/docstring lines on the oc side; executable statements are byte-identical. | unified diff of the two function bodies |
| F-4 | **`integrate_lane_branch` HAS EXACTLY ONE BEHAVIORAL DIFFERENCE**: the merge commit subject's host label (`integrate(aw agy run): ...` versus `integrate(aw oc run): ...`). The other 43 diff lines are docstring and comment. That single value is what E-02 parameterizes. | unified diff of the two function bodies |
| F-5 | Three of the four `integdefer` backlog items independently request shared placement, so this child is the seam they all assume: `5wdoze` ("belongs in shared code with both calling it, not copy-pasted twice"), `p8ni63` ("Put it in `runner_shared.py` ... NOT copy-pasted into two files"), both citing `cnwy8g`. | the three backlog items |
| F-6 | Binding shared objects is already this repository's pattern: `agy_runipd.py` imports 46 names from `oc_runipd.py`, 38 of them symbols oc alone defines. | AST import analysis 2026-09-06 |
| F-7 | Injection is the shared module's established way to avoid depending on a driver: `git_head`, `git_status`, `git_common_dir` all accept `run_checked` as a keyword-only parameter. LINE NUMBERS CORRECTED at review; the precedent exists because `run_checked` is host-specific (opencode-only `env_builder`), so it does NOT generalize to an already-shared collaborator. | `runner_shared.py:312`, `:327`, `:331` (the plan's earlier `:224/:239/:243` were stale); `runner_shared.py:55`, `:66-68` for the reason |
| F-9 | **THE COLLABORATOR SET IS FOUR NAMES, AND THREE ARE ALREADY SHARED SINGLETONS.** Measured: the two bodies' complete external-name set is `_run_git`, `build_lane_outcome`, `conflicted_paths`, `format_merge_conflict_reason` (plus builtins/`Path`). At runtime `oc._run_git is agy._run_git is runner_shared._run_git` is True, likewise `conflicted_paths` and `format_merge_conflict_reason`. So E-03's predicted injection work is mostly unnecessary, and NEITHER body references `run_checked` or `DriverError` at all. | AST external-name extraction + runtime `is` probes 2026-09-07 |
| F-10 | **`build_lane_outcome` IS A FOURTH DUPLICATED SYMBOL THIS PLAN NEVER NAMED**, and the shared `integrate_lane_branch` calls it. It is defined in BOTH drivers, absent from `runner_shared.py`, 0.887 similarity, and its EXECUTABLE AST is IDENTICAL (docstring-only diff). It is therefore a pure move on exactly the evidence this child already relies on, and leaving it behind would force an injection parameter for no benefit. | AST comparison 2026-09-07; `grep -c "^def build_lane_outcome"` returns 1 in each driver, 0 in `runner_shared.py` |
| F-11 | **THE ONE BEHAVIORAL DIFFERENCE IS CONFIRMED EXACTLY, at statement level rather than by line diff.** Both `integrate_lane_branch` bodies have 13 top-level statements with IDENTICAL signatures (`repo, handle, id6, validation_runner`); statement-by-statement AST comparison finds exactly ONE difference, the `--no-ff` merge subject's `aw oc run` versus `aw agy run` label. `dirty_tree_overlap`'s executable AST is byte-identical across hosts. This is the strongest available form of the plan's core safety claim. | per-statement `ast.dump` comparison 2026-09-07 |
| F-8 | A one-sided extraction guard has ALREADY failed once here: `render_stream` was extracted with a guard over `oc_runipd` only, and `agy_runipd` re-forked `Palette`, `_one_line`, `_strip_ansi` and `Heartbeat` with nothing noticing. | `rununify` orchestrator F10 |

## Proposed changes (ordered, validatable)

1. Move `dirty_tree_overlap` to `runner_shared.py` as a pure move, delete the agy copy, bind with the `as <same-name>` form (E-01).
2. Move `integrate_lane_branch`, parameterizing the host label with no default and keeping the fuller oc docstring (E-02).
3. Resolve collaborator injection and the two-`DriverError` trap without creating an import cycle (E-03).
4. Add a SYMMETRIC identity guard so neither runner can re-define either symbol (E-04).
5. Prove no behavior changed on EITHER host: integrate, refuse, rename endpoints, abort, plus each host's own commit subject (E-05).

## Deferred / out of scope (with reason)

- ANY BEHAVIOR CHANGE. This child is a pure de-duplication; its entire claim is that both hosts behave identically before and after. The deferral ladder is child 03 and the `integrate` verb is child 04, both of which build ON this seam. Mixing a move with a behavior change would make the identity assertion in E-04 unfalsifiable, which is the reason for the split.
- EXTRACTING THE OTHER DIVERGED SYMBOLS. The counts in this bullet were stale; `rununify`'s own executed E-01 inventory (research `tvnq50`, at HEAD `769989ce`) measured 88 shared symbols and 52 diverged, not 67 and 36. Unifying them is the `rununify` Set's job, and it is blocked on its own unauthored child rows plus its E-02 characterization baseline. This child takes ONLY the two symbols this Set must change, which is also why it does not need that baseline: a pure move with an object-identity assertion is self-verifying in a way a reconciliation is not.
- CHANGING `TERMINAL_STATES` or the `kind` vocabulary. Child 03 owns the `integration-deferred` status; touching it here would smuggle a behavior change into a move.
- MAKING THE COMMIT SUBJECT UNIFORM ACROSS HOSTS. Tempting while touching the string, but the per-host label is real information in git history (which driver integrated this lane) and collapsing it would lose attribution. Parameterize it; do not unify it.

## Scope check

- Over-scope: none. One shared module, both runners at the two symbols' definition and call sites, and the three corresponding test modules.
- Scope-Paths justification: `runner_shared.py` receives both symbols (E-01..E-03); `oc_runipd.py` and `agy_runipd.py` each lose a definition and gain a binding (unavoidable, since the whole point is that both hosts use one implementation); `tests/test_runner_shared.py` holds the symmetry and identity guards (E-04); each driver's suite holds its own behavior-preservation checks (E-05).
- BOTH DRIVER MODULES ARE THE HIGHEST-CONTENTION FILES IN THE REPOSITORY and other pending plans declare them. Expect drift, re-locate by symbol, and expect to rebase and re-run the full suite after any merge.
- Under-scope, stated rather than left as `none`: this child does not extract the other 36 diverged symbols, does not add the deferral ladder, does not add the `integrate` verb, and does not change either host's behavior. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with the `N passed` summary line pasted and counts stated. MEASURE YOUR OWN BEFORE-BASELINE and judge on the DELTA: the suite is NOT green at HEAD. Measured at review 2026-09-07 (HEAD `86581595`): `1 failed, 5613 passed, 3 skipped, 2 xfailed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`, confirmed present with unrelated changes stashed. Do NOT report it as yours. The authoring-time note of `5536 passed` at HEAD `3d239cfa` is stale and superseded.
- Targeted: `tests/test_runner_shared.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`.
- A REAL INTEGRATION ON EACH HOST in a throwaway repository, with the resulting merge commit subject pasted for both, since the host label is the single parameterized value.
- VALIDATE IN THE REAL CHECKOUT for `tests/test_run_viewer.py`, which reads the gitignored `.aw/records/runs/` and fails in a bare worktree while passing in the real checkout. Green elsewhere proves nothing.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

No spec change. This child moves code without changing behavior, and the integration contract it carries (the three `kind` values, the refusal semantics) is unchanged.

The MOVED DOCSTRING becomes the single prose statement of the integration contract, so it must arrive intact in `runner_shared.py` rather than being trimmed in transit (E-02 requires the fuller oc version). If either runner's module docstring or comments describe these functions as locally defined, correct that text in the same change.

Write no em or en dashes in user-facing prose. These are internal modules, so the constraint applies only if the executor touches user-facing text.

## Open questions

### OQ-01: Should the shared `integrate_lane_branch` take the host label, or the whole commit subject template?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE HOST LABEL, with the subject template living in the shared function. The label is the only thing that actually varies (F-4), and keeping the template shared means the subject's SHAPE stays uniform across hosts by construction, so a later change to the wording lands once. Passing the whole template would let the two hosts drift in format again, which is the failure this child exists to remove. It MUST have no default: a default label would let a new caller silently attribute its integrations to the wrong driver in git history, and that misattribution is invisible until someone audits the log.

### OQ-02: Should the shared function raise a neutral error type or accept the exception class as a parameter?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE QUESTION IS MOOT, and saying so is more useful than answering it. RE-MEASURED AT REVIEW 2026-09-07: the premise ("the two `DriverError` classes are distinct") is FALSE at HEAD. There is exactly ONE `DriverError`, defined at `runner_shared.py:159`, and both drivers re-export it with the `as <same-name>` form (`oc_runipd.py:169`, `agy_runipd.py:174`), so `oc.DriverError is agy.DriverError is runner_shared.DriverError` is True at runtime. The two-class problem was fixed by an earlier Set; `oc_runipd.py:106-110` records the fix ("There is now ONE class"), while the stale comment at `agy_runipd.py:278` still describes the old world and is what this plan's earlier text was reading.
  SO: raise `runner_shared.DriverError` if the function ever needs to raise, which is automatic because it is that module's own name, and add NO exception-class parameter. NEITHER MOVED BODY RAISES OR CATCHES `DriverError` AT ALL (verified: the external-name set is `_run_git`, `build_lane_outcome`, `conflicted_paths`, `format_merge_conflict_reason` and builtins), so no translation layer is needed at any boundary and none may be added. E-03 carries the corrected collaborator analysis; the real remaining question there is `build_lane_outcome`, not error types.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the shared `dirty_tree_overlap` and show BOTH runners' binding lines. Paste a probe proving OBJECT IDENTITY (`oc_runipd.dirty_tree_overlap is agy_runipd.dirty_tree_overlap is runner_shared.dirty_tree_overlap`), not merely equal output. Paste an AST check showing neither runner DEFINES it. Paste a rename case (`orig -> dest`) showing BOTH endpoints still count as dirty.
  - Observed evidence: PASS. `dirty_tree_overlap` is defined ONLY at `runner_shared.py:791`; `oc.dirty_tree_overlap is agy.dirty_tree_overlap is rs.dirty_tree_overlap` is True (same `id()`); both runners bind it with the `as <same-name>` re-export form (`oc_runipd.py:173`, `agy_runipd.py:176`); a real `R  orig.txt -> dest.txt` makes BOTH endpoints dirty on BOTH hosts; and the shared body's executable AST is byte-identical to both runners' PRE-MOVE bodies. Full pasted output below.

    THE SHARED DEFINITION (`agent_workflows/runner_shared.py:791`), which is the oc copy verbatim (its
    extra comments documenting the porcelain format and the rename handling are exactly why the plan
    chose it):

    ```python
    def dirty_tree_overlap(repo: Path, changed_files: Sequence[str]) -> list[str]:
        """driverfin-03 (7kbtkw) E-01: report the MAIN tree's un-owned dirty paths that overlap an
        incoming lane's ``changed_files``.
        ...
        The porcelain short format is `XY<space>path` (renames use `orig -> dest`); we take the last
        path token so both the origin and destination of a rename are considered dirty.
        """
        incoming = {p for p in changed_files if p.strip()}
        if not incoming:
            return []
        _rc, out, _err = _run_git(repo, ["status", "--short", "--untracked-files=all"])
        dirty: set[str] = set()
        for line in out.splitlines():
            if not line.strip():
                continue
            # Strip the two status columns and the following space: entries are `XY path` (min 3 chars).
            entry = line[3:] if len(line) > 3 else line.strip()
            # A rename/copy renders as `orig -> dest`; treat both endpoints as dirty.
            if " -> " in entry:
                orig, dest = entry.split(" -> ", 1)
                dirty.add(orig.strip())
                dirty.add(dest.strip())
            else:
                dirty.add(entry.strip())
        return sorted(incoming & dirty)
    ```

    BOTH RUNNERS' BINDING LINES, in the `as <same-name>` re-export form the plan requires:

    ```
    $ grep -n "dirty_tree_overlap as dirty_tree_overlap" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    agent_workflows/oc_runipd.py:173:    dirty_tree_overlap as dirty_tree_overlap,
    agent_workflows/agy_runipd.py:176:    dirty_tree_overlap as dirty_tree_overlap,
    ```

    THAT FORM PROVED LOAD-BEARING, not decorative, and it happened during this execution rather than
    being taken on faith: the `pre-commit` `ruff` hook DID run `--fix` over both drivers and DID
    remove a now-unused import (agy's `Sequence`, whose only use was the deleted definition's
    annotation) while leaving both `as <same-name>` re-exports untouched. Had the plain form been used
    for a symbol neither driver calls itself, that hook would have deleted the binding.

    OBJECT IDENTITY (not merely equal behavior):

    ```
    oc.dirty_tree_overlap is agy.dirty_tree_overlap is rs.dirty_tree_overlap -> True
    id(oc)= 134022037395536  id(agy)= 134022037395536  id(rs)= 134022037395536
    ```

    AST CHECK that neither runner DEFINES it (and that the other two are 1-statement wrappers, not
    second bodies):

    ```
    oc_runipd.py:1946  build_lane_outcome  (1 statement(s))
    oc_runipd.py:1955  integrate_lane_branch  (1 statement(s))
    agy_runipd.py:1217  build_lane_outcome  (1 statement(s))
    agy_runipd.py:1240  integrate_lane_branch  (1 statement(s))
    runner_shared.py:791  dirty_tree_overlap  (6 statement(s))
    runner_shared.py:823  build_lane_outcome  (7 statement(s))
    runner_shared.py:862  integrate_lane_branch  (13 statement(s))
    => dirty_tree_overlap is defined ONLY in runner_shared.py
    ```

    THE RENAME CASE, run against real git on BOTH hosts. `git status --short` renders
    `R  orig.txt -> dest.txt`, and the ORIGIN endpoint counts as dirty as well as the destination,
    which is the load-bearing property (a rename is how a plan moves into `executed/`):

    ```
    git status --short:
        R  orig.txt -> dest.txt
    [oc] overlap(['dest.txt'])            = ['dest.txt']
    [oc] overlap(['orig.txt'])            = ['orig.txt']   <- ORIGIN endpoint also dirty
    [oc] overlap(['orig.txt','dest.txt']) = ['dest.txt', 'orig.txt']
    [oc] overlap(['unrelated.txt'])       = []
    [oc] overlap([])                      = []
    [agy] overlap(['dest.txt'])            = ['dest.txt']
    [agy] overlap(['orig.txt'])            = ['orig.txt']   <- ORIGIN endpoint also dirty
    [agy] overlap(['orig.txt','dest.txt']) = ['dest.txt', 'orig.txt']
    [agy] overlap(['unrelated.txt'])       = []
    [agy] overlap([])                      = []
    ```

    PURITY, proven by subtraction rather than asserted: the shared body's executable AST (docstrings
    stripped) is byte-identical to BOTH runners' PRE-MOVE bodies at this lane's base `130d9cc7`:

    ```
      [oc_runipd] dirty_tree_overlap    == pre-move EXACTLY (pure move): True
      [agy_runipd] dirty_tree_overlap    == pre-move EXACTLY (pure move): True
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the shared `integrate_lane_branch` signature showing the host label parameter has NO default. Paste the merge commit subject produced by EACH host from a real integration, showing `aw oc run` and `aw agy run` respectively and unchanged from today (compare against a pre-change subject from git log). Confirm the fuller oc docstring arrived intact by quoting its steps 0 through 3 and all three `kind` values.
  - Observed evidence: PASS. The shared signature carries `host_label: str` keyword-only with NO default (machine-checked via `kw_defaults`, and proven falsifiable by adding one). A REAL integration on each host produced `integrate(aw oc run): merge verified lane aaa111 to main` and `integrate(aw agy run): merge verified lane bbb222 to main`, matching the shape in actual pre-change git history. The fuller oc docstring arrived intact (steps 0-3 and all three `kind` values present). Full pasted output below.

    THE SHARED SIGNATURE (`runner_shared.py:862`). `host_label` is keyword-only with NO DEFAULT, so a
    caller cannot silently inherit the wrong host's label:

    ```python
    def integrate_lane_branch(
        repo: Path,
        handle: Any,
        id6: str,
        validation_runner: Any,
        *,
        host_label: str,
        run_checked: Callable[..., str],
    ) -> tuple[bool, str, str]:
    ```

    Machine-checked rather than eyeballed, by
    `LaneIntegrationExtractionTests::test_the_host_label_has_NO_DEFAULT_in_the_shared_function`, which
    reads `node.args.kw_defaults` and asserts the slot is `None`. Proven FALSIFIABLE: adding
    `= "aw oc run"` makes exactly that test fail (pasted under V-04).

    EACH RUNNER'S WRAPPER keeps the ORIGINAL 4-argument signature, so no call site changed, and binds
    its own label (`oc_runipd.py:1955`, the agy twin at `agy_runipd.py:1240` differing only in the
    literal):

    ```python
    def integrate_lane_branch(
        repo: Path, handle: Any, id6: str, validation_runner: Any
    ) -> tuple[bool, str, str]:
        return runner_shared.integrate_lane_branch(
            repo, handle, id6, validation_runner,
            host_label="aw oc run", run_checked=run_checked,
        )
    ```

    THE MERGE SUBJECT FROM A REAL INTEGRATION ON EACH HOST, in a throwaway repo, taking the `--no-ff`
    path (main was advanced first so `--ff-only` fails, because the label appears ONLY on the
    `--no-ff` subject and a fast-forward would not have exercised it):

    ```
    [oc]  merge subject: integrate(aw oc run): merge verified lane aaa111 to main
    [agy] merge subject: integrate(aw agy run): merge verified lane bbb222 to main
    ```

    UNCHANGED FROM TODAY, compared against REAL pre-change history rather than against my own
    expectation (`git log --all --pretty=%s | grep -E "^integrate\(aw (oc|agy) run\):"`):

    ```
    integrate(aw oc run): merge verified lane 5942n7 to main
    integrate(aw oc run): merge verified lane 6ypimw to main
    integrate(aw oc run): merge verified lane wpu5zu to main
    ```

    The produced subject matches that shape character-for-character apart from the lane id. Each host's
    label is also asserted NEGATIVELY (the other host's label absent) in
    `test_a_clean_lane_still_integrates_and_carries_ITS_OWN_host_label`, since a swap would still
    satisfy "has a label"; that too is proven falsifiable under V-04.

    THE FULLER oc DOCSTRING ARRIVED INTACT. Steps 0 through 3 and all three `kind` values are present
    in the shared function's `__doc__`, checked programmatically:

    ```
      docstring contains '0. driverfin-03': True
      docstring contains '1. Build a LaneOutcome': True
      docstring contains '2. On': True
      docstring contains '3. driverfin-03': True
      docstring contains 'integrated': True
      docstring contains 'integration-blocked': True
      docstring contains 'merge-conflict': True
      docstring contains '--ff-only': True
      docstring contains '--no-ff': True
      docstring contains 'abort': True
    ```

    NO OTHER BEHAVIOR CHANGED, proven by subtraction: strip the two declared parameters and restore
    each host's label, and the shared body's executable AST equals BOTH runners' PRE-MOVE bodies:

    ```
      [oc_runipd] integrate_lane_branch == pre-move, modulo `host_label`+`run_checked`: True
      [agy_runipd] integrate_lane_branch == pre-move, modulo `host_label`+`run_checked`: True
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: enumerate every non-local name the two moved bodies call and state for each whether it moved, was already shared, or is injected. The expected set is FOUR (`_run_git`, `build_lane_outcome`, `conflicted_paths`, `format_merge_conflict_reason`); if you find a fifth, say so, since that would mean the drivers changed under this plan. Paste the runtime `is` probe showing the three already-shared collaborators are single objects across both drivers, and state that you therefore added NO injection parameter for them. STATE WHICH `build_lane_outcome` OPTION you took, (i) move or (ii) inject, and why. Paste proof of NO import cycle (`python3 -c "import agent_workflows.runner_shared"` succeeding standalone, and a check that `runner_shared` imports neither driver). DO NOT paste a `DriverError` translation demonstration: OQ-02 records that there is one shared class and neither body raises or catches it, so a translation layer here would be new unjustified code, not evidence.
  - Observed evidence: PASS, and it found a FIFTH name the plan did not predict. The four predicted collaborators resolved as expected (`_run_git`, `conflicted_paths`, `format_merge_conflict_reason` were ALREADY shared singletons needing NO injection; `build_lane_outcome` MOVED, option (i)). But `build_lane_outcome` itself calls `run_checked` three times, which is host-specific, so it is INJECTED following the existing `git_head`/`git_status`/`git_common_dir` precedent. No import cycle: `runner_shared` imports neither driver (AST-checked, covering lazy imports) and imports standalone with exit 0. No `DriverError` translation added or needed. Full pasted output below.

    THE `build_lane_outcome` CHOICE: OPTION (i), MOVE, as the plan prefers and as the scope fence
    explicitly authorizes. Recorded as decision `02-6sb3yu-D1`. Reason: option (ii) would have added a
    parameter whose ONLY purpose is to route around a duplicate, preserving the very defect this child
    exists to remove; and the move rests on the same evidence as `dirty_tree_overlap`'s (executable AST
    identical across hosts, docstring-only diff, re-verified at this lane's base `130d9cc7`).

    THERE IS A FIFTH NAME, AND THE PLAN ASKED ME TO SAY SO. The plan predicted the collaborator set
    would be FOUR. It is four for the two symbols the plan named, but `build_lane_outcome` (the fourth,
    which the plan discovered only at review) itself CALLS `run_checked` THREE TIMES, and neither the
    plan nor its review noticed. `run_checked` is host-specific (`oc.run_checked is agy.run_checked` is
    FALSE, unlike the other three collaborators), so the moved body cannot resolve it here and a naive
    lift raises `TypeError: run_checked() missing 1 required keyword-only argument`. This is the SAME
    intra-seam situation `runner_shared`'s own docstring records for `git_head`/`git_status`/
    `git_common_dir`, so I applied the SAME established remedy: INJECT it as a keyword-only parameter,
    with each runner's wrapper binding its own. Recorded as decision `02-6sb3yu-D2`, including why the
    tempting repair (rewriting the three calls onto `_run_git`) is worse here than for the git helpers:
    `_run_git` does not raise, so a failed `git rev-parse`/`git diff` would build a `LaneOutcome` from
    EMPTY STRINGS that the integration gate would revalidate as an empty change and merge.

    THE COMPLETE ENUMERATION, machine-derived from the shared module's AST (builtins and `Path`
    excluded), with each name's disposition:

    ```
    dirty_tree_overlap: external names called = ['_run_git']
        _run_git: MOVED/SHARED in runner_shared
    build_lane_outcome: external names called = ['run_checked']
        run_checked: PARAMETER (injected)
    integrate_lane_branch: external names called = ['_run_git', 'build_lane_outcome',
                                                    'conflicted_paths', 'dirty_tree_overlap',
                                                    'format_merge_conflict_reason']
        _run_git: MOVED/SHARED in runner_shared
        build_lane_outcome: MOVED/SHARED in runner_shared
        conflicted_paths: MOVED/SHARED in runner_shared
        dirty_tree_overlap: MOVED/SHARED in runner_shared
        format_merge_conflict_reason: MOVED/SHARED in runner_shared
    ```

    So: `_run_git`, `conflicted_paths` and `format_merge_conflict_reason` were ALREADY SHARED and
    needed NOTHING; `build_lane_outcome` and `dirty_tree_overlap` MOVED; `run_checked` is INJECTED.

    THE RUNTIME `is` PROBE for the already-shared collaborators, and I added NO INJECTION PARAMETER FOR
    ANY OF THE THREE (the shared bodies simply call their own module-level names). `DriverError` is
    included to confirm OQ-02's finding directly rather than by citation:

    ```
      oc._run_git is agy._run_git is rs._run_git: True
      oc.conflicted_paths is agy.conflicted_paths is rs.conflicted_paths: True
      oc.format_merge_conflict_reason is agy.format_merge_conflict_reason is rs.format_merge_conflict_reason: True
      oc.dirty_tree_overlap is agy.dirty_tree_overlap is rs.dirty_tree_overlap: True
      oc.DriverError is agy.DriverError is rs.DriverError: True
    ```

    No `DriverError` translation layer was added, and none is demonstrated here: neither moved body
    raises or catches it (visible in the enumeration above, which contains no such name), exactly as
    OQ-02 records.

    NO IMPORT CYCLE:

    ```
    $ python3 -c "import agent_workflows.runner_shared" >/dev/null 2>&1; echo $?
    0
    runner_shared imports of a runner: NONE
    ```

    The second line is an AST walk over every `Import`/`ImportFrom` in `runner_shared.py` looking for
    `runipd` in a module or alias name, so it covers a LAZY function-level import too, not only
    module-level ones. `tests/test_runner_shared.py::NoRunnerImportTests` (both tests) and my new
    `test_the_shared_bodies_reference_no_name_from_either_runner` (which checks the three bodies' free
    names resolve inside this module, its parameters, or builtins) also pass.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the guard test and its passing output. Then paste PROOF IT IS FALSIFIABLE IN BOTH DIRECTIONS: re-add a local definition to `oc_runipd` and show the guard failing, revert, then re-add one to `agy_runipd` and show it failing again. A guard only ever demonstrated against one runner is exactly the one-sided guard that let the `render_stream` re-fork through (F-8).
  - Observed evidence: PASS. The guard is `tests/test_runner_shared.py::LaneIntegrationExtractionTests`, 9 tests driven by a symbol LIST and iterating BOTH runners. Proven falsifiable FOUR ways, each reverted: a re-fork appended to `oc_runipd` fails 3 tests, the same re-fork in `agy_runipd` fails the SAME 3 (symmetry, the F-8 lesson), swapping agy's label fails both the static and the real-merge check, and adding a default to `host_label` fails the no-default check. Full pasted output below.

    THE GUARD is `tests/test_runner_shared.py::LaneIntegrationExtractionTests`, 9 tests driven by the
    module-level symbol list `LANE_INTEGRATION_MOVED` (so extending it is adding ONE name, not
    copy-pasting a block) and iterating `BOTH` runners in every assertion. It is a SEPARATE class
    rather than three more entries in the fixture-backed `INJECTED` machinery, for the reason recorded
    as decision `02-6sb3yu-D3`: that fixture is a capture of the PRE-MOVE source at HEAD `1ecc5891`,
    these three symbols are not in it, so there is no fingerprint to compare and adding them would
    raise `KeyError` rather than prove anything. The class asserts every property the fixture-backed
    one does, plus two it could not express (the label has no default; each runner binds its own).

    PASSING:

    ```
    tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_a_wrapped_symbol_is_a_single_delegating_statement PASSED
    tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_an_unwrapped_symbol_is_the_SAME_OBJECT_in_both_runners PASSED
    tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_each_runner_binds_its_OWN_host_label PASSED
    tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_each_wrapper_keeps_the_ORIGINAL_signature PASSED
    tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_exactly_one_definition_package_wide PASSED
    tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_neither_runner_redefines_an_unwrapped_symbol PASSED
    tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_the_host_label_has_NO_DEFAULT_in_the_shared_function PASSED
    tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_the_shared_bodies_reference_no_name_from_either_runner PASSED
    tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_the_shared_module_defines_all_three PASSED
    ```

    FALSIFIABLE IN BOTH DIRECTIONS. A local `dirty_tree_overlap` definition was appended to each
    runner IN TURN and reverted; the guard fails SYMMETRICALLY, with the same three tests, for each:

    ```
    --- RE-FORK injected into oc_runipd.py ---
    FAILED ...::test_an_unwrapped_symbol_is_the_SAME_OBJECT_in_both_runners
    FAILED ...::test_exactly_one_definition_package_wide
    FAILED ...::test_neither_runner_redefines_an_unwrapped_symbol
    3 failed, 6 passed in 1.87s
    --- RE-FORK injected into agy_runipd.py ---
    FAILED ...::test_an_unwrapped_symbol_is_the_SAME_OBJECT_in_both_runners
    FAILED ...::test_exactly_one_definition_package_wide
    FAILED ...::test_neither_runner_redefines_an_unwrapped_symbol
    3 failed, 6 passed in 1.86s
    ```

    That symmetry is the point: F-8 records that `render_stream` was extracted with an oc-only guard
    and `agy_runipd` then re-forked four symbols unnoticed, so a guard demonstrated against one runner
    only would be the same defect again.

    THE HOST-LABEL HALF IS ALSO FALSIFIABLE, in the two ways it could realistically be broken:

    ```
    --- agy host_label SWAPPED to oc's ---
    FAILED ...LaneIntegrationExtractionTests::test_each_runner_binds_its_OWN_host_label
    FAILED ...LaneIntegrationBehaviorTests::test_a_clean_lane_still_integrates_and_carries_ITS_OWN_host_label
    2 failed, 12 passed in 2.53s
    --- a DEFAULT added to host_label ---
    FAILED ...LaneIntegrationExtractionTests::test_the_host_label_has_NO_DEFAULT_in_the_shared_function
    1 failed, 8 passed in 1.76s
    ```

    Note the swap is caught BOTH statically (the binding) and dynamically (the real merge subject),
    which matters because a misattributed integration is otherwise invisible until someone audits
    main's log.

    ALL FOUR MUTATIONS REVERTED, and the guard is green again:

    ```
    --- ALL REVERTED; guard green ---
    tests/test_runner_shared.py ..............                               [100%]
    ============================== 14 passed in 2.36s ==============================
    ```

    THE GUARD ALSO COVERS `build_lane_outcome`, the third symbol, as the plan's scope fence asks: it is
    in `LANE_INTEGRATION_MOVED`, and because it keeps a host-binding wrapper it is checked by the
    wrapper-shape and original-signature tests rather than by object identity (asserting identity for a
    deliberately-wrapped symbol would be wrong, which is why `LANE_INTEGRATION_WRAPPED` exists).
    Symmetry for it is additionally covered in each driver's OWN suite by
    `test_the_integration_helpers_are_the_SHARED_ones`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste, FOR BOTH HOSTS: a clean integration succeeding; a dirty-overlap refusal returning `integration-blocked` with main untouched and the lane branch still present; and a real conflict returning `merge-conflict` with main carrying no markers (`git status` pasted). Paste the BARE `python3 -m pytest` summary line with before/after counts. State that `test_run_viewer.py` was validated in the REAL checkout and why that matters. Confirm no `kind` value and no `TERMINAL_STATES` entry changed.
  - Observed evidence: PASS. All four behaviors verified on BOTH hosts against real git: clean integration with each host's own subject, dirty-overlap refusal returning `integration-blocked` with main untouched and the lane preserved, rename endpoints (under V-01), and a real conflict returning `merge-conflict` with main clean, no `MERGE_HEAD`, no markers. Bare suite: BEFORE `16 failed, 5641 passed`, AFTER `16 failed, 5659 passed`, and the sorted FAILED lists DIFF EMPTY, so no test changed verdict and the +18 are exactly this child's new tests. No `kind` value and no `TERMINAL_STATES` entry changed. `test_run_viewer.py` could NOT be run in the real checkout (lane containment denies it); evidence that its failures are data-absence and not mine is below. Full pasted output below.

    ALL FOUR BEHAVIORS, ON BOTH HOSTS, against REAL GIT in throwaway repositories, each going through
    that runner's OWN wrapper so the host-specific bindings are exercised rather than bypassed:

    ```
    ================ HOST: oc ================
    (a) CLEAN INTEGRATION -> (True, 'controlled non-ff merge integrated to main', 'integrated')
        merge subject: integrate(aw oc run): merge verified lane aaa111 to main
        lane file on main: lane
    (b) DIRTY REFUSAL -> (False, 'integration refused: main tree has un-owned dirty paths overlapping the incoming change: src/x.py', 'integration-blocked')
        main HEAD unmoved: True
        un-owned edit intact: 'un-owned dirt\n'
        lane branch preserved: True
    (d) CONFLICT ABORT -> (False, kind='merge-conflict')
        reason: merge-back conflict in 1 file(s): clash.txt; Auto-merging clash.txt
        main HEAD unmoved: True
        git status --short: ''
        MERGE_HEAD exists: False
        conflict markers in file: False
        lane branch preserved: True
    ================ HOST: agy ================
    (a) CLEAN INTEGRATION -> (True, 'controlled non-ff merge integrated to main', 'integrated')
        merge subject: integrate(aw agy run): merge verified lane aaa111 to main
        lane file on main: lane
    (b) DIRTY REFUSAL -> (False, 'integration refused: main tree has un-owned dirty paths overlapping the incoming change: src/x.py', 'integration-blocked')
        main HEAD unmoved: True
        un-owned edit intact: 'un-owned dirt\n'
        lane branch preserved: True
    (d) CONFLICT ABORT -> (False, kind='merge-conflict')
        reason: merge-back conflict in 1 file(s): clash.txt; Auto-merging clash.txt
        main HEAD unmoved: True
        git status --short: ''
        MERGE_HEAD exists: False
        conflict markers in file: False
        lane branch preserved: True
    ```

    The two hosts' output is identical apart from the merge subject's label, which is the extraction's
    entire claim. `(c)` the rename endpoints is pasted under V-01. A REAL AGY INTEGRATION WAS
    DEMONSTRATED, not inferred from the oc result, as the plan's closing paragraph demands.

    THESE ARE COMMITTED AS TESTS, not merely run once ad hoc: `LaneIntegrationBehaviorTests` (5 tests,
    each looping over both runners) plus `test_this_hosts_merge_subject_still_says_aw_oc_run` and its
    agy twin, placed in each DRIVER'S OWN suite so a reader of either sees the host-specific proof.

    BARE SUITE, BEFORE AND AFTER (`python3 -m pytest`, no added flags):

    ```
    BEFORE (this lane's base, 130d9cc7):  16 failed, 5641 passed, 3 skipped, 2 xfailed in 112.87s
    AFTER  (this change):                 16 failed, 5659 passed, 3 skipped, 2 xfailed in  54.09s
    ```

    +18 passed, which is exactly the tests this child adds; and the FAILURE SETS ARE IDENTICAL, proven
    by diffing the sorted `FAILED` lists rather than by comparing counts (equal counts could hide one
    test breaking while another was fixed):

    ```
    $ diff f_before.txt f_after2.txt && echo "FAILURE SET IDENTICAL TO BASELINE"
    FAILURE SET IDENTICAL TO BASELINE
    ```

    ON THE BASELINE ITSELF, stated plainly because it does not match the plan's prediction. The plan
    expected `1 failed`. I measured 16, and none is mine: all 16 REPRODUCE with my changes stashed
    (`16 failed, 209 passed` over just those three modules). One is the pre-existing failure the plan
    names (`test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_
    NOT_for_unauthored_rows`). The other 15 accrued between that review and this lane's base: 14 in
    `tests/test_run_viewer.py` and one in `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests`
    (a NEGATIVE verdict on pending plan `32ij2j`, i.e. another plan's record, not code). Separately, a
    bare run in THIS lane initially showed 34 failures; 18 of those are caused by `AW_EXECUTION_ROLE=
    worker` being inherited from the worker process into test subprocesses, which makes `aw ipd begin`
    refuse with `AW-LIFECYCLE-ROLE-001`. They vanish under `env -u AW_EXECUTION_ROLE`, so both my
    before and after measurements were taken that way. Recorded as decision `02-6sb3yu-D4`.

    `test_run_viewer.py`: I could NOT validate it in the real checkout, and I am saying so rather than
    implying otherwise. This turn runs under lane containment, which denies reads outside the lane
    worktree, so I cannot execute anything against the main checkout. What I CAN show is that its
    failures are caused by the absent gitignored data and NOT by this change, which is what the plan's
    instruction was protecting against. Two pieces of evidence: (1) `agent_workflows/run_viewer.py`
    imports `platform_lock`, `attention`, `render_stream` and `term`, and NONE of `oc_runipd`,
    `agy_runipd` or `runner_shared`, so it cannot observe my edit; (2) creating one synthetic run
    record under `.aw/records/runs/` makes the representative failure pass immediately, with my change
    in place:

    ```
    $ # with a synthetic .aw/records/runs/run-.../state.json present
    tests/test_run_viewer.py .                                               [100%]
    ============================== 1 passed in 0.17s ==============================
    $ # (synthetic record then removed; the directory is gitignored and untracked)
    ```

    Pending plan `utwr6y` ("make the run viewer tests own their data instead of borrowing") exists to
    fix this class of failure and is not this child's work.

    NO `kind` VALUE AND NO `TERMINAL_STATES` ENTRY CHANGED:

    ```
    $ git diff HEAD -- agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py | grep -E "TERMINAL_STATES|integration-deferred"
      (no output: no diff line touches either)
    $ # `kind` literal occurrences, HEAD's oc copy vs the post-move shared+oc pair:
      kind occurrences identical
    ```

    `LaneIntegrationBehaviorTests::test_the_kind_vocabulary_is_UNCHANGED_by_the_extraction` pins the
    returned set to exactly `{"integrated", "integration-blocked", "merge-conflict"}` by AST, so a
    future edit that adds child 03's `integration-deferred` here (rather than in child 03) fails.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

DEPENDENCY: this child declares `- Item-Dependencies: executed:29wvmj`. KEEP THE EDGE, BUT NOT FOR THE REASON FIRST WRITTEN, which measurement at review 2026-09-07 showed to be false. The original rationale was that E-05's real lane integrations "today trip the executed-transition gate and would need `--no-verify`". They do not: E-05 performs its integrations in a THROWAWAY REPOSITORY, which has no `pre-commit` hook installed at all (verified: `ls .git/hooks/` in a fresh `git init` is empty of non-sample hooks, and the `--no-ff` merge succeeded with no bypass). Two further facts from child 01's review compound this: git runs `pre-merge-commit`, not `pre-commit`, for an automated merge, and this repository installs only `pre-commit`, so even in the real checkout the runner's merge path does not reach that gate.
  THE EDGE IS STILL CORRECT, on the honest grounds: both children edit code this Set then builds on, serializing them keeps the two highest-contention driver files from being rewritten under each other, and child 01 is the Set's declared first slice. If you need to run this child's validation before child 01 lands, nothing in E-05 is technically blocked; do NOT, however, reorder the Set on that basis without the maintainer, since the ordering is his ruling. The runner re-checks dependencies at dispatch, so a queued-together Set is safe.

Scope fence: touch ONLY the six paths in `Scope-Paths`. Do NOT change any behavior: not the refusal conditions, not the gate call, not `--ff-only` or the `--no-ff` fallback, not the abort path, not the `kind` vocabulary, not `TERMINAL_STATES`. Do NOT unify the per-host commit subject label. EXTRACT NO SYMBOL BEYOND THE TWO NAMED, WITH ONE EXPLICIT EXCEPTION: `build_lane_outcome` MAY move under E-03 option (i), because the shared `integrate_lane_branch` calls it, it is duplicated in both drivers with an IDENTICAL executable AST, and the alternative is an injection parameter that exists only to route around a duplicate. That exception is authorized HERE so the executor does not have to guess; it is deliberately narrow and covers no other symbol. Note this is a THIRD symbol, so E-04's symmetry guard and V-04's falsifiability proof should cover it too if you take option (i). Do NOT edit `agent_workflows/hooks/executed_transition_gate.py` (child 01 owns it). If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT and both driver modules are the highest-contention files in it: run `aw runs` before starting, and if a driver file is being changed under you and the two sets of changes cannot be safely combined, STOP and report rather than overwriting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find `dirty_tree_overlap`, `integrate_lane_branch`, their call sites, and `runner_shared`'s injection precedents by name.

THE CLAIM THIS CHILD MAKES IS "NOTHING CHANGED", so V-05 is what earns it. A green suite is NOT sufficient on its own: the two runner suites are asymmetric (the agy side has far fewer tests, and several of the largest diverged symbols have zero agy coverage), so an agy-side regression can leave both suites green. Exercise BOTH hosts explicitly and paste both. If you cannot demonstrate a real integration on the agy host, say so plainly rather than inferring from the oc result.

On completion, close backlog `5wdoze`? NO. That item's substance is the deferral ladder, which child 03 delivers; this child only builds the seam. `- From-Backlog: 5wdoze` records the provenance and `- Blocks-Release: next` is inherited from it, but the item stays open until child 03 executes. Do NOT close it here.
