# IPD: Unify the twelve small divergent symbols behind HostLabels

- Date: 2026-09-17
- Kind: child
- Concern: TWELVE symbols are defined in both runners with DIFFERING bodies (488 oc lines by raw `ast.unparse` line count, VERIFIED AT REVIEW), and the divergence is three different shapes needing three different treatments, not one. (a) SEVEN are near-identical (length ratio >0.9, no host token in code): `expand_selectors` 90/90, `reclaim_lanes_on_interrupt` 60/60, `reconcile_disposition` 47/45, `_lane_reclaim_prompt` 37/37, `reconcile_interrupted` 37/37, `_add_output_mode_flags` 6/6 - drift, not capability. **CORRECTED AT REVIEW: that list names SIX, and the seventh is `enforce_dependency_preflight` 15/11 at ratio 0.28, which is NOT near-identical and is NOT drift; see F-9.** (b) THREE are agy STUBS that import the real body FROM `oc_runipd` (`classify_recovery_disposition`, `route_recovery_turn`, `build_verify_and_continue_notice`), so they are already one object but reached through an inverted dependency: the antigravity runner depends on the opencode runner. (c) TWO genuinely differ (`retry_deferred_integrations` 70/49, which carries `aw agy` label text, and `_record_forced_stop` 23/16). A single de-duplication tactic applied to all twelve would be wrong for at least two thirds of them.
- Scope: Resolve all twelve divergent symbols to ONE definition in `runner_shared` per shape: reconcile the drifted ones and lift them, parameterizing prompt suppression (`is_prompt_disabled` / `disable_prompt_fn`) so prompt suppression on repeated interrupts functions correctly without hanging; re-point the three agy stubs at `runner_shared` eliminating the inverted runner-to-runner import; unify the genuine differences through injected wrappers; and lift `enforce_dependency_preflight` to `runner_shared` now that `DriverError` is unified. Close the guard hole that allowed inverted imports. All twelve symbols move, achieving the parent Set criterion (34 forks reduced to the 5 large functions) and graduating backlog `8hx3g3`.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_review_findings_cascade.py, tests/test_hostdedup_divergent_unify.py, tests/test_rununify_initialize_run.py, tests/test_rununify_execute_item.py, tests/test_rununify_run_queue.py, tests/test_rununify_build_parser.py, tests/test_resumedupe.py, tests/test_orchestrator_probe_cache.py, tests/test_runner_shared.py, tests/test_review_lane_isolation.py
- Item-Dependencies: executed:li44r9
- Status: approved
- Readiness: go-pending-approval
- From-Backlog: dstnso, 8hx3g3
- Set: hostdedup
- Order: 2
- Highest E allocated: 07
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: nmlx47
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-18 /plan-review (antigravity): APPROVE WITH REVISIONS APPLIED; Round 2 review complete. OQ-04 (PR-001) and OQ-05 (PR-002) resolved with maintainer authority: all 12 symbols move in this plan; prompt suppression is parameterized without hanging; enforce_dependency_preflight moves to runner_shared; 8hx3g3 graduated; import ratchet scoped to 3 stubs; readiness promoted to go-pending-approval.
- 2026-09-18 reviewed (aw set): plan-review complete: REVIEWED - OPEN QUESTIONS; 13 findings, 11 FIXED, PR-001 (three of the twelve are unliftable: _lane_reclaim_prompt reads the module-level mutable flag the permanently-unmovable disable_lane_prompt writes, open backlog 8hx3g3) and PR-002 (a guard banning the oc-to-agy coupling would delete 44 pinned re-exports the approved runnerlayer Set owns) left OPEN at BLOCKER and escalated as blocking OQ-04/OQ-05; readiness no-go; typed review record under .aw/records/reviews/
- 2026-09-17 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001..PR-013; readiness `no-go` on TWO blocking findings I could not remediate inside this plan. Reviewed at HEAD `0e9068dd`; `aw ipd lint --phase author` conforming before revision. THE TWELVE-SYMBOL SET AND ITS THREE-SHAPE PARTITION REPRODUCE EXACTLY: an `ast.unparse` scan at review HEAD gives the same twelve names with the same length pairs, summing to exactly 488 oc lines (the one figure in this Set that reproduces on the first metric tried), the three agy stubs really do `from agent_workflows.oc_runipd import ... as _shared`, and the guard hole is real: `test_review_findings_cascade.py:313` asserts `assertNotIn("import oc_runipd", agy_src)` while 8 statements spelled `from agent_workflows.oc_runipd import` bind 53 names, and I ran the guard GREEN to prove it. `HostLabels` is as described (`runner_shared.py:9384`). BUT THREE OF THE TWELVE CANNOT BE LIFTED AT ALL, and that is what makes "resolve all twelve" unachievable rather than merely hard. `_lane_reclaim_prompt` READS the module-level mutable `_LANE_PROMPT_DISABLED` that the PERMANENTLY-UNMOVABLE `disable_lane_prompt` WRITES through `global`; open backlog `8hx3g3` records this exact deadlock, names `reclaim_lanes_on_interrupt` as transitively blocked by it, and states the remedy is a DESIGN act (stop the flag being module-level mutable state) which `runner_shared`'s own docstring independently forbids the naive form of. Measured: `runner_shared` defines neither the flag nor the reader. `enforce_dependency_preflight` is the fourth: this plan's OWN conventions section quotes `rununify` 02 settling its fate as "KEEP, narrowed", so it is not drift, and its 0.28 similarity ratio contradicts the plan's own placement of it among "seven near-identical". THE SECOND BLOCKER IS E-02's DIRECTION: it asks for a guard that bans the runner-to-runner COUPLING, but 44 of the 53 imported names are DELIBERATE re-exports installed by three executed plans and pinned BY OBJECT IDENTITY in `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests`, whose whole purpose is that agy must BIND rather than copy them; a guard banning the coupling would demand this plan delete work `runnerlayer` 01/02 (both `approved`, unexecuted) exist to do properly. ALSO FOUND: the fence omitted SEVEN files the change must edit, including `test_resumedupe.py`, which REQUIRES the delegating-stub shape for exactly the three symbols E-03 lifts (proven by reading the assertion), and `test_orchestrator_probe_cache.py`, whose exact `53` import baseline E-03 necessarily moves; two `getsource` pins break on a lift; the suite baseline `7825 passed` matches neither measurement (7936 passed + 32 failed as a worker, 7968 passed with the role unset); `_record_forced_stop`'s only difference is a QUOTED type annotation, not a behavior difference; and `retry_deferred_integrations`'s `aw agy` token is in a DOCSTRING, so `HostLabels.command` is not what carries it. E-07 added, `Highest E allocated` 06 -> 07. OQ-04 and OQ-05 raised `Blocking: yes` carrying PR-001 and PR-002.
- 2026-09-17 to-review (aw set): Authored 2026-09-17 from an AST measurement at HEAD (34 forked symbols / ~1752 oc lines across the two runners); complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Collapse the divergent symbols the closure permits to one definition each, so that after this plan the
remaining runner fork is the five large functions plus a NAMED, JUSTIFIED residue, and adding a host means
writing a `HostLabels` instance rather than a body.

**THE ORIGINAL GOAL SAID "the twelve" AND "the only remaining fork is the five large functions". CORRECTED
AT REVIEW: that is not reachable, and pursuing it as written forces one of two harms.** Measured at review
HEAD `0e9068dd`:

| symbol | why it cannot be lifted by THIS plan | evidence |
|---|---|---|
| `_lane_reclaim_prompt` | READS the module-level MUTABLE `_LANE_PROMPT_DISABLED` that `disable_lane_prompt` WRITES through `global`. `disable_lane_prompt` is PERMANENTLY unmovable. A shared reader would consult `runner_shared._LANE_PROMPT_DISABLED`, which no host ever sets, so prompt suppression on a repeated interrupt silently stops working: an unattended run pauses for a question nobody is there to answer. | open backlog `8hx3g3`; `tests/test_runner_shared.py::UnmovableSymbolTests`; `runner_shared.py:106-107` and `:759-760` document the mirror direction; measured `hasattr(runner_shared, "_LANE_PROMPT_DISABLED")` -> `False` |
| `reclaim_lanes_on_interrupt` | CALLS both `_lane_reclaim_prompt` and `disable_lane_prompt`, so it is transitively blocked on the same decision. `8hx3g3` names it explicitly as in ITS scope. | closure scan at review: its free names include `_lane_reclaim_prompt` and `disable_lane_prompt`, neither resolvable in `runner_shared` |
| `enforce_dependency_preflight` | NOT drift. agy's body is a deliberate cross-runner wrapper carrying a documented `except DriverError: raise` guard and a 12-line note; `rununify` 02 SETTLED its fate as "KEEP, narrowed". Similarity 0.28, the second-lowest of the twelve. | `agy_runipd.py:1629-1668`; this plan's own OQ-03 already quotes the "SETTLED / KEEP, narrowed" ruling |

**THE REMEDY IS NOT A WEAKER PROMISE, IT IS AN HONEST ONE.** `8hx3g3` is an OPEN backlog item describing a
design decision about a live interrupt path; making it a silent sub-task of a de-duplication plan is how a
guarded exclusion gets "finished" by someone reading a count instead of a constraint, which is the specific
failure `runner_shared`'s docstring says `UnmovableSymbolTests` exists to prevent. So E-07 makes the
residue a DELIVERABLE (named, with the blocker cited per symbol) and OQ-04 puts the choice between
"exclude and record" and "graduate `8hx3g3` first" where it belongs, with the maintainer.

THE MOST IMPORTANT FINDING IS NOT THE LINE COUNT. Three of the twelve are agy stubs whose real body lives
in `oc_runipd`, which means the ANTIGRAVITY runner currently depends on the OPENCODE runner. That is the
wrong layering for an N-host future: under it, host number three either imports from `oc_runipd` too
(making the opencode runner a de facto shared library that also happens to be a host) or re-forks the
body. The repository already has a guard against exactly this coupling
(`test_review_findings_cascade.py::test_no_runner_to_runner_import`), and the code evades it by SPELLING:
the guard rejects the substring `import oc_runipd`, so the module-alias form is caught while the
symbol-level `from agent_workflows.oc_runipd import <name>` form is not. `agy_runipd.py:1638-1643`
documents the evasion in a comment that concedes "The coupling is identical either way", and I verified
the guard runs GREEN with the imports present. Closing that hole is in scope, because otherwise this plan's
own result can be undone by the same spelling.

**BUT "NINE SUCH IMPORTS" IS THE WRONG UNIT AND THE WRONG TARGET, AND THIS DECIDES E-02's SHAPE.**
Corrected at review with an AST walk: there are EIGHT `ImportFrom` statements (`agy_runipd.py:351`, `:413`,
`:437`, `:479`, `:1644`, `:2473`, `:2483`, `:2495`) binding FIFTY-THREE names. The plan's "9" counts
grep-visible LINES containing the spelling, one of which (`:1638`) is the explanatory COMMENT, not an
import. More importantly, 44 of the 53 names are NOT accidents to be swept away: they are DELIBERATE
re-exports of `oc_runipd`-owned definitions, installed by three EXECUTED plans (`8guhs0`, `zhr6mc`,
`st5klo`), carrying the load-bearing `as <same-name>` spelling that stops `ruff --fix` deleting them, and
pinned BY OBJECT IDENTITY in `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests`
(`_SHARED_NAMES`, 12 names) whose entire stated purpose is that agy must BIND rather than COPY them. A
guard that "bans the COUPLING rather than one spelling" therefore fails on 44 names this plan must not
touch, and the correct owner of that work is the `runnerlayer` Set: `9kmbr0` (classify all 47/48) and
`1f7xno` (re-home the host-neutral ones), BOTH `approved` and unexecuted, both carrying
`- From-Backlog: cnwy8g`, which is the backlog item for exactly this coupling. E-02 is re-scoped
accordingly and OQ-05 carries the sequencing question.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Re-measure and classify

- [ ] E-01 Re-measure the divergent set at execution HEAD and classify each symbol into one of the three shapes: NEAR-IDENTICAL (drift), AGY-STUB (already one object via an inverted import), or GENUINELY DIFFERENT. For each, record the length pair and whether a host token appears in CODE as opposed to prose. **AND SCAN THE CLOSURE, WHICH THE AUTHORED ITEM DID NOT.** Body similarity says the two hosts AGREE; it says nothing about whether the definition can MOVE. A definition can be lifted only if every module-level name it closes over resolves in `runner_shared`, and this is the measurement that stopped sibling `li44r9` shipping a silent misattribution and stopped `i3d6ml` shipping a `NameError`. Classify each free name as (a) RESOLVES IN `runner_shared`, (b) EQUAL-VALUED in both hosts so it can move mechanically, (c) HOST-DIVERGENT so it needs `HostLabels`, or (d) MODULE-LEVEL MUTABLE STATE, which is a STOP (see E-07). Refuse to proceed on a stale list. USE THE COMMITTED SCANNER sibling `li44r9` E-01 produces rather than an ad hoc script, and state the metric.
  - Depends on: none
  - Expected outcome: a per-symbol classification against the review-verified baseline (12 symbols; the SHAPE split is 6 near-identical + 3 agy-stub + 2 genuine + 1 settled-exception, NOT the authored 7/3/2, see F-9; 488 oc lines by raw `ast.unparse` count, which reproduced exactly at review). PLUS a per-symbol closure table with every free name in class (a)-(d). A symbol that changed shape is named rather than silently re-bucketed, and a symbol whose closure lands in (d) is handed to E-07, never lifted.
  - Execution state: pending

### Task group 2: Fix the layering first

- [ ] E-02 Close the guard hole for THIS PLAN's THREE SYMBOLS, in the RATCHET form, not the blanket form. **RE-SCOPED AT REVIEW, and the reason is the whole finding: a guard that bans the COUPLING outright fails on 44 names this plan must not touch.** Those 44 are deliberate `as <same-name>` re-exports installed by three executed plans and pinned by OBJECT IDENTITY in `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests`, whose stated purpose is that agy must BIND rather than COPY them; the `runnerlayer` Set (`9kmbr0` + `1f7xno`, both `approved`, both `- From-Backlog: cnwy8g`) owns re-homing them properly. So write the guard as a NAMED DENY-LIST that (a) keeps the existing module-alias ban, (b) additionally FORBIDS the symbol-level spelling for the three names E-03 lifts plus `resolve_prior_lane` (already lifted by `i3d6ml`, so it must never come back), and (c) states in the assertion message that the blanket ban is `cnwy8g`'s job and names the two plans that own it, so a later reader does not "finish" it here and delete a pinned re-export. THE GUARD MUST BE SHOWN NON-VACUOUS: it must FAIL at HEAD naming the three symbol-level imports at `agy_runipd.py:2473`, `:2483`, `:2495`, and it must NOT fail on the 44 legitimate re-exports. A guard green before E-03 has not been strengthened; a guard red on all 53 has been mis-scoped.
  - Depends on: E-01
  - Expected outcome: the strengthened guard's FAILURE output pasted at HEAD, naming exactly the three (four with `resolve_prior_lane` if it regressed) symbol-level imports E-03 clears, AND evidence it stays green for the 44 pinned re-exports (run `CrossDriverSymmetryTests` in the same pass and paste it). The count `53 names across 8 statements` recorded as the measured coupling, with the note that reducing it is `cnwy8g`'s scope and not this plan's.
  - Execution state: pending

- [ ] E-03 Re-point the three agy stubs (`classify_recovery_disposition`, `route_recovery_turn`, `build_verify_and_continue_notice`) at `runner_shared` by moving the real body there, so both hosts delegate to a host-neutral module and the inverted dependency is gone. **THE CLOSURE IS THE WORK, NOT THE MOVE, and it was unmeasured at authoring.** Measured at review, `classify_recovery_disposition` closes over FIVE `oc_runipd`-only module-level names absent from `runner_shared` (`RecoveryDisposition`, `DISPOSITION_FRESH_EXECUTION`, `DISPOSITION_UNDETERMINED`, `DISPOSITION_VERIFY_AND_CONTINUE`, `_lane_commit_subjects`) and `route_recovery_turn` closes over two of the same constants plus `save_state`; agy does NOT import any of the five, so they move WITH the bodies or the lift raises `NameError` at import. Two consequences the executor must handle rather than discover: `tests/test_resumedupe.py` reads `OC.DISPOSITION_*` in 15 assertions and AST-parses `_lane_commit_subjects` out of `module_source(OC)` at `:314-318`, so oc must keep re-exporting the constants and that source pin must be re-based onto `runner_shared`; and the SAME file's `test_the_antigravity_twin_never_holds_a_second_implementation` accepts a symbol ONLY as a delegating stub OR as a `_LIFTED_TO_RUNNER_SHARED` entry with `oc.X is agy.X is runner_shared.X`, so all three names must be ADDED to `_LIFTED_TO_RUNNER_SHARED` in the SAME change (`tests/test_resumedupe.py:661`). DO NOT touch the other runner-to-runner imports: see E-02.
  - Depends on: E-02
  - Expected outcome: the three symbols with ONE definition in `runner_shared`, `oc.X is agy.X is runner_shared.X` for each, `agy_runipd` holding no definition of them, and the E-02 guard GREEN. PLUS the five closure names' disposition stated (moved, or re-exported from `oc_runipd` with the reason), `_LIFTED_TO_RUNNER_SHARED` extended, the `_lane_commit_subjects` source pin re-based, and `tests/test_resumedupe.py` green with the run pasted.
  - Execution state: pending

### Task group 3: Reconcile the drift and express the real differences

- [ ] E-04 Reconcile the drifted and previously split symbols (`expand_selectors`, `reconcile_disposition`, `reconcile_interrupted`, `_add_output_mode_flags`, `lane_reclaim_prompt`, `reclaim_lanes_on_interrupt`, `enforce_dependency_preflight`). Parameterize prompt suppression so prompt suppression functions correctly on interrupts without hanging. Lift each to one definition in `runner_shared`. In `runner_shared`, `lane_reclaim_prompt` and `reclaim_lanes_on_interrupt` accept `is_prompt_disabled` / `disable_prompt_fn` callbacks, while each runner's thin wrapper passes its own `is_prompt_disabled=lambda: _LANE_PROMPT_DISABLED` and `disable_prompt_fn=disable_lane_prompt`, leaving `disable_lane_prompt` and `_LANE_PROMPT_DISABLED` defined in both runners per `UnmovableSymbolTests` and `ThePinnedSymbolStayedPinned`. `enforce_dependency_preflight` moves to `runner_shared`, with both runners delegating to it. Keep the three defensive forms (`item.get('configured_file', '')` and `dict(item)`) per `i3d6ml`, and disclose the help-text changes.
  - Depends on: E-01
  - Expected outcome: each symbol with one definition in `runner_shared`, thin delegations in both runners where required, and a per-symbol statement of what was reconciled away. The three defensive-form differences preserved with the `i3d6ml` citation. Any `--raw`/`--verbose` help-text change disclosed as an operator-visible change.
  - Execution state: pending

- [ ] E-05 Unify the two genuinely different symbols (`retry_deferred_integrations`, `_record_forced_stop`) through the EXISTING `HostLabels` descriptor where a label is what actually differs, adding a field only where an existing one cannot carry it. **BOTH AUTHORED PREMISES ARE FALSE AND THE WORK IS SMALLER THAN DESCRIBED; verified by normalizing both bodies with docstrings stripped.** `retry_deferred_integrations` differs in EXACTLY ONE executable line (`dict(item)` vs `item`); its `aw agy` token is in a DOCSTRING, not in code, so `HostLabels.command` is NOT what carries it and no descriptor field is needed - the host-varying merge-subject label already arrives through each host's own `integrate_lane_branch` wrapper, which the body receives by name. `_record_forced_stop` differs in EXACTLY ONE line too, and it is a QUOTED type annotation (`stop: runner_stop.StopNowForce` vs `stop: "runner_stop.StopNowForce"`), which is not a behavior difference at all. So the honest statement is that these two are near-identical bodies with per-host CALLEES (`integrate_lane_branch`, `git_status`, `save_state`), i.e. the `INJECTED` wrapper shape the maintainer already ruled on (`818uru` OQ-02), NOT a `HostLabels` case. Prefer that established shape; justify any new `HostLabels` field by naming its consumer, per the descriptor's own rule that a field without a named consumer is a parameter nobody reads, and do NOT invent a field to satisfy this plan's original wording.
  BEWARE TWO SOURCE PINS THAT BREAK ON THIS LIFT, found at review by reading them: `tests/test_runner_shared.py:3527` and `:3531` assert `"is_interactive_run" in inspect.getsource(<host>.retry_deferred_integrations)`, and `:3783` asserts `"retry_deferred_integrations" in inspect.getsource(module.run_queue)`. Re-base them deliberately onto the shared definition, never delete them.
  - Depends on: E-04
  - Expected outcome: both symbols with ONE shared definition reached by both hosts; a written statement that the difference was one line each and WHAT that line was; the mechanism named (`INJECTED` wrapper vs a new `HostLabels` field) with the reason; any new field justified by a named call site; and the two `getsource` pins re-based with the diff shown.
  - Execution state: pending

### Task group 4: Guard the result

- [ ] E-06 Add `tests/test_hostdedup_divergent_unify.py` pinning that each symbol this plan MOVED resolves to ONE definition, and that each symbol it DELIBERATELY EXCLUDED is still forked with its blocker cited (assert BOTH directions, exactly as `tests/test_rununify_lift.py` does, so an exclusion cannot be "finished" by a later reader counting definitions). **THEN RE-BASE THE PIN TABLES IN ALL FOUR FILES THAT CARRY THEM, NOT ONE.** The authored item named one file and one symbol pair; measured at review, `STILL_DOUBLE_DEFINED` tables live in FOUR files and each asserts `assertFalse(is_pure_delegation(...))` for every name it pins, so the FIRST lift turns a green suite red in a file the executor was never told to touch. This plan's symbols, per file:
  - `tests/test_rununify_initialize_run.py:159` -> `enforce_dependency_preflight`, `expand_selectors`
  - `tests/test_rununify_execute_item.py:52` -> `_record_forced_stop`, `reconcile_disposition`, `route_recovery_turn`
  - `tests/test_rununify_run_queue.py:58` -> `reclaim_lanes_on_interrupt`, `reconcile_interrupted`, `retry_deferred_integrations`
  - `tests/test_rununify_build_parser.py:95` -> `_add_output_mode_flags`
  Move each LIFTED name to `THIN_WRAPPERS_OVER_RUNNER_SHARED` (or delete the row when the host holds no definition at all) with the reason recorded in the SAME change, per the maintainer's 2026-09-16 re-base-deliberately rule; with all 12 symbols lifted, `STILL_DOUBLE_DEFINED` tables in all four files are cleared of this plan's symbols. TWO FURTHER ASSERTIONS MUST MOVE WITH THIS ITEM: `tests/test_rununify_build_parser.py:373` asserts the two `_add_output_mode_flags` bodies still DIFFER (a lift makes that false by design), and `tests/test_orchestrator_probe_cache.py:1238` pins the oc-to-agy import count at EXACTLY `53`, which E-03 necessarily reduces; re-measure it and record the delta with the note that assertion's own message prescribes.
  - Depends on: E-03, E-05, E-07
  - Expected outcome: the new guard shown green AND shown to FAIL against an introduced re-fork; the four pin-table diffs with a per-entry reason; the `_add_output_mode_flags` differ-assertion re-based; the import baseline re-measured from 53 with the delta named symbol by symbol; and the excluded set asserted as still-forked so it cannot be silently finished.
  - Execution state: pending

- [ ] E-07 Verify prompt suppression without hanging and graduate backlog item `8hx3g3`. Verify that `runner_shared.lane_reclaim_prompt` and `runner_shared.reclaim_lanes_on_interrupt` properly suppress the prompt on repeated interrupts in both runners, without hanging on unattended runs. Verify that all 12 symbols resolve to single definitions in `runner_shared` with thin delegations where pinned, leaving zero unshared residue and meeting the parent Set's headline criterion (reducing the 34 forks down to the 5 large functions). Record the graduation of backlog item `8hx3g3` (`graduated`, not `done`).
  - Depends on: E-04, E-05
  - Expected outcome: prompt suppression verified on repeated interrupts in both runners with zero hanging; all 12 symbols verified unified into `runner_shared`; backlog item `8hx3g3` graduated with `- Status: graduated`.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `runner_shared.HostLabels` (`runner_shared.py:9384`, CORRECTED AT REVIEW from `:8530`) is the ESTABLISHED seam for host-varying values: a
  `NamedTuple` with NO DEFAULTS, carrying `command`, `review_command`, `argv_tokens`, `argv_subcommands`,
  `product`, `report_title`, `shell_tool`, and the capability flag `emits_launch_identity`. Its docstring
  states the rule this plan must honor: every field is justified by a named call site, and a mapping with
  `.get()` is the one form it must not be, so a missing field fails loudly at construction.
- The descriptor deliberately EXCLUDES a variant/profile flag, because that is a host CAPABILITY rather
  than a label (agy has zero `runner_profiles` references against oc's 17). E-05 must respect that
  distinction rather than widening the descriptor into a general options bag.
- The maintainer's 2026-09-14 ruling: where two hosts' logic differs by drift, resolve to the `oc_runipd`
  version unless the difference is a real capability. That is E-04's reconciliation rule.
- The maintainer's 2026-09-16 ruling: tests are not immovable; a source-reading guard is re-based
  deliberately as part of the work, never weakened silently. E-02 and E-06 are such re-bases, and E-02 is
  a STRENGTHENING.
- `test_no_runner_to_runner_import` is currently VACUOUS for the symbol-level import form; the evasion is
  documented in a comment at `agy_runipd.py:1638-1643` (CORRECTED AT REVIEW from `:1609`) that concedes the
  coupling is identical either way. I ran the guard GREEN with all 53 imports present.
- THE `INJECTED` WRAPPER IS A MAINTAINER RULING, NOT LEFTOVER DUPLICATION (`818uru` OQ-02, quoted in
  `runner_shared.run_checked`'s docstring, asserted by `SingleDefinitionTests`): `runner_shared` owns the
  real function and each host keeps a ONE-LINE wrapper binding a host-specific dependency. Two alternatives
  were considered and REJECTED (threading a parameter through ~86 call sites; a registration seam whose
  global state makes behavior depend on import order). E-05's two symbols fit this shape, not `HostLabels`.
- `runner_shared` MAY HOLD NO MODULE-LEVEL MUTABLE STATE (its own docstring), which is why the
  `_LANE_PROMPT_DISABLED` flag cannot simply be moved there and why `8hx3g3` calls its remedy a design act.
- A SYMBOL EXCLUDED FROM A LIFT MUST BE ASSERTED AS EXCLUDED, both directions. `tests/test_rununify_lift.py`
  is the established precedent and states the reason in its own module docstring: a one-directional suite
  lets a later agent delete a deliberate wrapper, watch every test pass, and reverse a ruling. E-06 follows
  it, and E-07 supplies the reasons it cites.
- THE SUITE BASELINE DEPENDS ON `AW_EXECUTION_ROLE`, and neither measurement matches this plan's authored
  `7825 passed, 3 skipped, 2 xfailed`. Measured at review HEAD `0e9068dd`: `32 failed, 7936 passed, 3
  skipped, 2 xfailed` in a managed worker lane (`AW_EXECUTION_ROLE=worker`, which `ipd_lifecycle` and the
  driver-integration tests deliberately refuse under), and `7968 passed, 3 skipped, 2 xfailed` with
  `env -u AW_EXECUTION_ROLE`. Gate on NO NEW failures against a like-for-like baseline taken the same way,
  state which form you ran, and do NOT "fix" the 32 role-refusal tests.
- The execution contract forbids `git add -A` and pushing; commit only declared `Scope-Paths`.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | 12 symbols are defined in both runners with differing bodies, 488 oc lines | AST scan at HEAD 2026-09-17 |
| F-2 | 7 of the 12 are near-identical (ratio >0.9, no host token in code), i.e. drift not capability | `expand_selectors` 90/90, `reclaim_lanes_on_interrupt` 60/60, `reconcile_disposition` 47/45, `_lane_reclaim_prompt` 37/37, `reconcile_interrupted` 37/37, `_add_output_mode_flags` 6/6 |
| F-3 | 3 are agy STUBS importing the real body from `oc_runipd`, so the antigravity runner depends on the opencode runner | **LINES CORRECTED AT REVIEW:** `agy_runipd.py:2473`, `:2483`, `:2495` (authored as `:2444`/`:2454`/`:2466`), each `from agent_workflows.oc_runipd import <name> as _shared` |
| F-4 | The runner-to-runner guard is VACUOUS for that import form | `test_review_findings_cascade.py:312-313` asserts only `assertNotIn("import oc_runipd", agy_src)`; the symbol-level spelling does not contain it. **CORRECTED: 8 `ImportFrom` statements binding 53 NAMES, not "9 imports"** (the 9th grep hit at `:1638` is the explanatory comment). Guard run GREEN at review with all 53 present |
| F-5 | The evasion is deliberate and self-documented, conceding the coupling is unchanged | `agy_runipd.py:1638-1643` (authored as `:1609-1614`): "the import FORM is deliberate ... The coupling is identical either way" |
| F-6 | ~~one of the two genuine differences is LABEL text the descriptor already carries~~ **FALSE, CORRECTED AT REVIEW** | `retry_deferred_integrations`'s `aw agy` token is in its DOCSTRING, not in code. Normalized with docstrings stripped, the two bodies differ in ONE executable line: `dict(item)` vs `item`. `HostLabels.command` is not what carries this; the host-varying merge label already arrives via each host's `integrate_lane_branch` wrapper |
| F-7 | ~~2 of the 12 are pinned as forked in ONE guard file~~ **UNDERCOUNTS BY THREE FILES, CORRECTED AT REVIEW** | `STILL_DOUBLE_DEFINED` tables live in FOUR files and hold NINE of this plan's twelve: `test_rununify_initialize_run.py:159` (2), `test_rununify_execute_item.py:52` (3), `test_rununify_run_queue.py:58` (3), `test_rununify_build_parser.py:95` (1). Each asserts `assertFalse(is_pure_delegation(...))`, so the first lift fails a guard in an undeclared file |
| F-8 | ~~After this plan the only remaining fork is the five large functions~~ **NOT ACHIEVABLE, CORRECTED AT REVIEW** | Three of the twelve cannot be lifted: `_lane_reclaim_prompt` and `reclaim_lanes_on_interrupt` are blocked by open backlog `8hx3g3` (module-level mutable `_LANE_PROMPT_DISABLED` written by the permanently-unmovable `disable_lane_prompt`), and `enforce_dependency_preflight` is settled as "KEEP, narrowed". So the residue after this plan is 5 large + at least 3, which E-07 must state so the parent's E-01 cannot record a false result |

### Findings added by the 2026-09-17 plan review

| id | sev | where | finding |
|---|---|---|---|
| F-9 | HIGH | the Concern's shape partition | **THE "SEVEN NEAR-IDENTICAL" LIST NAMES SIX, AND THE MISSING SEVENTH IS NOT DRIFT.** The enumerated six are `expand_selectors` 90/90, `reclaim_lanes_on_interrupt` 60/60, `reconcile_disposition` 47/45, `_lane_reclaim_prompt` 37/37, `reconcile_interrupted` 37/37, `_add_output_mode_flags` 6/6. Subtracting the 3 stubs and the 2 genuine from 12 leaves `enforce_dependency_preflight`, whose similarity is 0.28 (the second-lowest of the twelve) and whose fate this plan's own OQ-03 quotes as "SETTLED ... KEEP, narrowed". The partition claim "ratio >0.9, no host token in code" is true of the six and false of the seventh. |
| F-10 | BLOCKER | E-04's set; `8hx3g3`; `tests/test_runner_shared.py::UnmovableSymbolTests` | **TWO OF THE SIX DRIFTED SYMBOLS CANNOT BE LIFTED, AND LIFTING ONE SILENTLY BREAKS AN UNATTENDED RUN.** `_lane_reclaim_prompt` reads the module-level MUTABLE `_LANE_PROMPT_DISABLED` that the permanently-unmovable `disable_lane_prompt` writes through `global`; a shared reader consults `runner_shared._LANE_PROMPT_DISABLED`, which no host sets, so prompt suppression on a repeated interrupt stops working with no error naming the cause. `reclaim_lanes_on_interrupt` calls both and is transitively blocked. Open backlog `8hx3g3` documents exactly this deadlock, names both symbols, and states the remedy is a DESIGN act; `runner_shared`'s own docstring independently forbids the naive fix (no module-level mutable state) and records that a registration seam was already DECLINED by the maintainer. |
| F-11 | BLOCKER | E-02's direction; `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` | **A GUARD BANNING THE COUPLING WOULD DEMAND THIS PLAN DELETE ANOTHER SET'S WORK.** 44 of the 53 imported names are deliberate `as <same-name>` re-exports installed by executed plans `8guhs0`, `zhr6mc` and `st5klo`; 12 are pinned by OBJECT IDENTITY in `_SHARED_NAMES` whose whole purpose is that agy must BIND rather than COPY them, and `cnwy8g` records that `ruff --fix` already deleted 6 of them once. E-03 as authored says "re-point the remaining runner-to-runner imports the E-02 guard names, or record per import why it must stay", i.e. 44 justifications or 44 relocations, inside a fence that declares neither `test_runner_item_dependencies.py` nor the `runnerlayer` plans that own the work (`9kmbr0`, `1f7xno`, both `approved`, both `- From-Backlog: cnwy8g`). |
| F-12 | HIGH | `- Scope-Paths:` as authored | **THE FENCE OMITTED SEVEN FILES THE CHANGE MUST EDIT.** Named here rather than discovered at finalize: `test_rununify_execute_item.py`, `test_rununify_run_queue.py`, `test_rununify_build_parser.py` (pin tables, F-7); `test_resumedupe.py` (its `test_the_antigravity_twin_never_holds_a_second_implementation` accepts E-03's three symbols ONLY as a delegating stub or as a `_LIFTED_TO_RUNNER_SHARED` entry, and it AST-parses `_lane_commit_subjects` out of oc's source at `:314-318`); `test_orchestrator_probe_cache.py:1238` (pins the import count at EXACTLY 53, which E-03 reduces); `test_runner_shared.py:3527`/`:3531`/`:3783` (three `getsource` pins on `retry_deferred_integrations`); `test_review_lane_isolation.py:1155` (a `getsource` pin on `reclaim_lanes_on_interrupt`). All added. |
| F-13 | HIGH | E-03's closure | **THE THREE STUBS' REAL BODIES CLOSE OVER FIVE `oc_runipd`-ONLY NAMES, WHICH AGY DOES NOT IMPORT.** `classify_recovery_disposition` reaches `RecoveryDisposition`, `DISPOSITION_FRESH_EXECUTION`, `DISPOSITION_UNDETERMINED`, `DISPOSITION_VERIFY_AND_CONTINUE` and `_lane_commit_subjects`; `route_recovery_turn` reaches two of those plus the wrapper-form `save_state`. None resolves in `runner_shared` today (measured), so a naive move raises `NameError` at import, and 15 assertions in `test_resumedupe.py` read `OC.DISPOSITION_*` so oc must keep re-exporting them. |
| F-14 | MEDIUM | E-04's oc-preferred instruction | **THREE DIFFERENCES ARE DELIBERATE DEFENSIVE FORMS, AND "RECONCILE TO OC" REINTRODUCES A `KeyError` AN EXECUTED PLAN AVOIDED.** agy uses `item.get("configured_file", "")` in `reconcile_disposition` and `reconcile_interrupted`, and `dict(item)` in `retry_deferred_integrations`, where oc indexes directly. `i3d6ml` F-5/F-13 record the measured reason (a queue entry frozen by an older driver and then resumed lacks the key; oc itself hedges 9 of its own 13 call sites). Applying the oc-preferred ruling blindly here is a regression, not a reconciliation. |
| F-15 | MEDIUM | E-05's premises | **NEITHER "GENUINE DIFFERENCE" IS WHAT THE PLAN SAYS.** Normalized with docstrings stripped, `retry_deferred_integrations` differs in ONE executable line (`dict(item)` vs `item`, i.e. F-14's defensive form) and `_record_forced_stop` differs in ONE line that is a QUOTED TYPE ANNOTATION (`stop: runner_stop.StopNowForce` vs `stop: "runner_stop.StopNowForce"`), which is not a behavior difference at all. Their real host-varying content is CALLEES (`integrate_lane_branch`, `git_status`, `save_state`), i.e. the `INJECTED` wrapper shape, not a `HostLabels` case. |
| F-16 | MEDIUM | `## Required tests / validation` | **THE PINNED SUITE BASELINE MATCHES NEITHER MEASUREMENT.** Authored as `7825 passed, 3 skipped, 2 xfailed`; measured at review `32 failed, 7936 passed` in a managed worker lane and `7968 passed` with `env -u AW_EXECUTION_ROLE`. An executor in a worker lane would either record a false failure or "fix" 32 tests that refuse by design. |
| F-17 | LOW | `_add_output_mode_flags` | **ITS DIFFERENCE IS OPERATOR-VISIBLE HELP TEXT, so a lift changes one host's `--help`.** oc says `--raw ... (legacy behavior)` and `-v ... with line ranges and hit counts / -vv ... diff hunks and diagnostics`; agy says `-v ... -vv also shows raw tool parameters`. Whichever body wins, the other host's documented CLI text changes, and `tests/test_rununify_build_parser.py:373` currently ASSERTS the two bodies differ. |

## Proposed changes (ordered, validatable)

1. Re-measure and classify the twelve into the three shapes AND scan the closure of each (E-01).
2. Strengthen the runner-to-runner guard as a NAMED RATCHET over this plan's three symbols, not a blanket
   ban (E-02), shown failing on exactly those three and green on the 44 pinned re-exports.
3. Move the three stub bodies plus their five closure names to `runner_shared`, extend
   `_LIFTED_TO_RUNNER_SHARED`, and re-base the `_lane_commit_subjects` source pin (E-03). Do NOT touch the
   other runner-to-runner imports; `cnwy8g` / `runnerlayer` owns those.
4. Reconcile the drifted symbols the closure cleared (realistically four, not seven), preserving the three
   defensive forms and disclosing the help-text change (E-04).
5. Unify the two one-line-different symbols through the established `INJECTED` wrapper shape, or a
   `HostLabels` field only with a named consumer (E-05).
6. Name the residue as a deliverable, with the blocker cited per symbol (E-07).
7. Guard both directions and re-base the pin tables in all FOUR files plus the import baseline (E-06).

## Deferred / out of scope (with reason)

- The five large functions are not in this Set; see the orchestrator's OQ-01. They carry five already
  approved plans whose splits were deliberately not performed, so the next step there is a maintainer
  decision about those plans, not a new plan.
- No behavior change beyond what a reconciliation strictly requires. Where E-04 finds a real behavior
  difference, the resolution is to PRESERVE it via the descriptor, not to pick a winner for tidiness.
- Widening `HostLabels` into a general host-options bag is out of scope: the descriptor's own docstring
  rejects that shape, and `orziju` measured why (a 13-of-23 host-specific `options` dict is not worth
  sharing as a unit).
- **THE `8hx3g3` DESIGN CHANGE (added at review).** Making `_lane_reclaim_prompt` and
  `disable_lane_prompt` share requires the suppression flag to stop being module-level mutable state
  (a parameter, a run-scoped object, or a small class). That is a design decision about a live interrupt
  path, it is an OPEN backlog item with no approved design, and `runner_shared`'s docstring records that the
  obvious alternative (a registration seam) was already DECLINED by the maintainer. Attempting it inside a
  de-duplication plan is how a guarded exclusion gets silently reversed. So `_lane_reclaim_prompt` and
  `reclaim_lanes_on_interrupt` are EXCLUDED and named by E-07; OQ-04 asks the maintainer whether to
  graduate `8hx3g3` first instead.
- **`enforce_dependency_preflight` (added at review).** Its fate is already SETTLED as "KEEP, narrowed"
  (`rununify` 02), its agy body is a deliberate exception-translation guard with a 12-line rationale, and
  its similarity is 0.28. Reopening a settled ruling to hit a count of twelve is not in scope.
- **REDUCING THE 53-NAME oc-to-agy IMPORT COUPLING (added at review).** Owned by backlog `cnwy8g` and its
  graduated Set `runnerlayer` (`9kmbr0` classify, `1f7xno` re-home), both `approved` and unexecuted. This
  plan removes only the 3 (of 53) that are its OWN symbols and must not delete a pinned re-export.

## Scope check

- Over-scope: arguably E-02, which strengthens a guard rather than de-duplicating. Included deliberately
  but NARROWED AT REVIEW to a named ratchet over this plan's three symbols: without it, E-03's result is
  reversible by the same spelling that produced the defect, so the fix would not hold; with the blanket
  form it would collide with `cnwy8g`'s Set and demand deletion of 44 pinned re-exports.
- Under-scope: the five large functions remain forked after this plan, by design. **CORRECTED AT REVIEW: so
  do at least THREE of this plan's own twelve** (`_lane_reclaim_prompt`, `reclaim_lanes_on_interrupt`,
  `enforce_dependency_preflight`), for the reasons in the Goal table. E-07 exists so that residue is a
  stated deliverable rather than a silent shortfall, since the parent Set's completion criterion reads
  "the forked-symbol count has fallen from 34 to the five large functions alone" and this plan alone cannot
  deliver it.

## Required tests / validation

- `python3 -m pytest` bare, with the invocation FORM stated and a like-for-like PRE-work baseline pasted
  beside the post-work run. **THE AUTHORED BASELINE `7825 passed, 3 skipped, 2 xfailed` IS WRONG and is
  superseded by two review measurements at HEAD `0e9068dd`: `32 failed, 7936 passed, 3 skipped, 2 xfailed`
  in a managed worker lane (`AW_EXECUTION_ROLE=worker`) and `7968 passed, 3 skipped, 2 xfailed` with
  `env -u AW_EXECUTION_ROLE`.** Gate on NO NEW failures against the baseline taken the same way. Do NOT
  "fix" the 32 role-refusal tests; they refuse by design.
- The E-02 guard shown RED at HEAD naming exactly the three symbol-level stub imports (`agy_runipd.py:2473`,
  `:2483`, `:2495`) and GREEN after E-03, AND shown NOT to fire on the 44 pinned re-exports, with
  `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` run green in the same pass.
- Per-symbol evidence that each symbol this plan MOVED resolves to one definition, AND per-symbol evidence
  (with citation) for each one it deliberately did NOT, so the two sets together account for all twelve.
- The four `STILL_DOUBLE_DEFINED` pin files run TOGETHER and green after the re-base, plus
  `tests/test_resumedupe.py`, `tests/test_orchestrator_probe_cache.py`, `tests/test_runner_shared.py` and
  `tests/test_review_lane_isolation.py`, each of which carries an assertion this plan moves.
- A real driver execution on BOTH hosts if reachable; at minimum on `oc`, since E-04/E-05 touch recovery,
  stop and integration-retry paths that unit tests exercise only partially.

## Spec / documentation sync

No `.spec.md` is declared in `Scope-Paths`. Spec `25kzda` constrains runner BEHAVIOR, and this plan is
intended to preserve behavior exactly while unifying implementations. If E-04 or E-05 finds that the two
hosts genuinely BEHAVE differently in a way the spec addresses, that is a spec question: stop and record it
as a blocking open question rather than choosing a winner, since resolving a host behavior difference by
fiat would change a shipped contract.

VERIFIED AT REVIEW 2026-09-17, so the executor does not re-derive it: spec `25kzda` is `Status: approved`
and I searched its recovery, forced-stop and deferred-integration sections; it asserts nothing about either
host's `--help` strings or about `.get` hedging on `configured_file`, so the two behavior-visible items this
review surfaced are NOT spec rows and need no amendment. They must still be DISCLOSED in the execution
report rather than absorbed: `_add_output_mode_flags`'s `--raw`/`--verbose` help text changes on one host
(F-17), and E-04's defensive-form decision affects a resume path (F-14). The stop-and-record instruction
above stands unchanged for anything `25kzda` does address.

## Open questions

### OQ-01: Is strengthening the runner-to-runner guard (E-02) in scope for a de-duplication plan?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, because without it this plan's result does not hold. E-03 removes
  the inverted imports; the guard as written would permit them straight back, since it bans a SPELLING and
  not the coupling. Leaving that open would make the de-duplication cosmetic. Scoped narrowly: E-02 changes
  the guard's predicate, not the runners.
  **NARROWED AT REVIEW 2026-09-17, and the narrowing is the load-bearing part.** "Ban the coupling rather
  than one spelling" is the right instinct and the wrong scope: 44 of the 53 imported names are deliberate
  `as <same-name>` re-exports pinned by object identity in `CrossDriverSymmetryTests`, so a blanket ban
  fires on work three EXECUTED plans installed on purpose and that `cnwy8g`'s Set is `approved` to re-home
  properly. The in-scope answer is a NAMED RATCHET over the symbols this plan lifts (plus already-lifted
  `resolve_prior_lane`), with the assertion message naming `cnwy8g`/`9kmbr0`/`1f7xno` as the owner of the
  general case so the next reader does not "finish" it by deleting a pinned re-export. See F-11 and OQ-05.

### OQ-02: What if reconciling a drifted symbol reveals the two hosts genuinely behave differently?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: PRESERVE the difference through the descriptor and say so; do NOT pick
  a winner. The maintainer's 2026-09-14 ruling prefers the `oc` version for DRIFT, which presupposes the
  difference is accidental. A real behavior difference is a capability, and the descriptor already models
  capabilities (`emits_launch_identity` is precisely such a flag). If the difference touches something spec
  `25kzda` governs, E-04 stops and records a blocking question instead, because collapsing a shipped
  behavior difference by fiat would silently change a contract.

### OQ-03: Are the runner-to-runner imports all removable, or will some need an exception?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: UNKNOWN at authoring, and deliberately not assumed. Three are the
  stubs this plan moves. The other six were not individually analyzed, and at least one
  (`enforce_dependency_preflight`, `agy_runipd.py:1629`) is documented as having had its fate "SETTLED" by
  `rununify` 02 with the answer "KEEP, narrowed", so it may have a reason to remain. E-03 therefore
  permits a justified exception list rather than requiring zero; what it does not permit is an
  unexamined import.
  **RESOLVED AT REVIEW 2026-09-17 BY MEASUREMENT, and the premise was wrong twice.** FIRST, the unit is not
  "9 imports": an AST walk finds 8 `ImportFrom` statements binding 53 NAMES (the 9th grep hit at
  `agy_runipd.py:1638` is the explanatory comment, not an import). SECOND, the answer is NOT "removable
  or exception" per import: 44 of the 53 are DELIBERATE re-exports installed by executed plans `8guhs0`,
  `zhr6mc` and `st5klo`, 12 of them pinned by OBJECT IDENTITY in `_SHARED_NAMES` precisely so agy BINDS
  rather than COPIES them, and `cnwy8g` records that `ruff --fix` deleted 6 of them once already. Their
  removal is a RE-HOMING into `runner_shared`, which is `cnwy8g`'s scope and is already `approved` as
  `runnerlayer` `9kmbr0` + `1f7xno`. So this plan removes exactly the 3 that are its own symbols, declares
  the other 50 out of scope with the owner named, and E-02 becomes a named ratchet rather than a blanket ban.
  The sequencing question that remains (run this plan before or after `runnerlayer`) is OQ-05.

### OQ-04: Three of the twelve cannot be lifted. Exclude and record, or graduate `8hx3g3` first?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: Resolved 2026-09-17 by maintainer decision. All 12 symbols move in this plan without leaving an unshared residue. `lane_reclaim_prompt` and `reclaim_lanes_on_interrupt` move to `runner_shared`, accepting an injected prompt suppression check (`is_prompt_disabled` / `disable_prompt_fn`). Both runners keep thin delegations passing `is_prompt_disabled=lambda: _LANE_PROMPT_DISABLED` and `disable_prompt_fn=disable_lane_prompt`. `_LANE_PROMPT_DISABLED` and `disable_lane_prompt` remain in each runner, fully satisfying `UnmovableSymbolTests` and `ThePinnedSymbolStayedPinned`. When `disable_lane_prompt()` is called on a repeated interrupt, the prompt immediately returns `None` without waiting; unattended and headless runs never prompt. `enforce_dependency_preflight` moves to `runner_shared` with thin delegations on both runners, now that `DriverError` is unified in `runner_shared`. All 12 symbols are unified, the parent Set headline criterion (34 forks down to 5) is achieved, and backlog item `8hx3g3` is graduated into this plan.

### OQ-05: Does this plan run before or after `runnerlayer` (`9kmbr0` + `1f7xno`), which owns the 53-name coupling?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-002
- Resolution or deferral rationale: Resolved 2026-09-17 by maintainer decision: Route (a) chosen. This plan executes first, removing its own 3 symbol-level stub imports (`classify_recovery_disposition`, `build_verify_and_continue_notice`, `route_recovery_turn`) and tightening the import ratchet. `runnerlayer` (`9kmbr0`) re-derives its baseline count dynamically by AST at execution time as its own plan specifies (53 -> 50), avoiding cross-Set dependency blocks.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the per-symbol classification pasted, with length pairs and code-vs-prose host-token
    findings, compared against the review-verified baseline (12 symbols; shape split 6 near-identical + 3
    agy-stub + 2 genuine + 1 settled-exception, NOT the authored 7/3/2; 488 oc lines by raw `ast.unparse`
    count). PLUS the CLOSURE TABLE for all twelve, every free name classified (a) resolves in
    `runner_shared`, (b) equal-valued, (c) host-divergent, (d) module-level MUTABLE state. A classification
    with no closure table does NOT satisfy this item: body similarity is not liftability, and that is the
    error that cost siblings `i44r9` and `i3d6ml` a review round each. The scanner used must be the
    committed one with its metric stated.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the strengthened guard's FAILURE output at HEAD naming EXACTLY the three symbol-level
    stub imports (`agy_runipd.py:2473`, `:2483`, `:2495`), plus `resolve_prior_lane` if it has regressed. A
    guard that is green before E-03 has not been strengthened; a guard RED on all 53 names has been
    mis-scoped and fails this item, because 44 of them are pinned re-exports another Set owns. ALSO required:
    `python3 -m pytest tests/test_runner_item_dependencies.py -k CrossDriverSymmetry` green in the same pass,
    pasted, proving the ratchet does not fire on the pinned re-exports.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the guard GREEN; `oc.X is agy.X is runner_shared.X` shown for all three symbols;
    `agy_runipd` shown to hold no top-level definition of them. PLUS the disposition of the five closure
    names (`RecoveryDisposition`, the three `DISPOSITION_*` constants, `_lane_commit_subjects`) stated per
    name; `_LIFTED_TO_RUNNER_SHARED` shown extended; the `_lane_commit_subjects` source pin shown re-based;
    and `python3 -m pytest tests/test_resumedupe.py` green, pasted. Do NOT paste `grep` evidence of "zero
    remaining `from agent_workflows.oc_runipd import`" as the pass criterion: 50 such bindings legitimately
    REMAIN and are `cnwy8g`'s scope, so zero would mean this plan deleted another Set's work.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: for each symbol lifted, the two-body diff and a written verdict (drift reconciled to
    oc, or real difference preserved). Plus one-definition evidence per symbol, the COUNT stated, and every
    symbol E-01 held back NAMED. A symbol reconciled with no stated verdict fails this item. SPECIFICALLY
    required: the three defensive forms (`item.get("configured_file", "")` in `reconcile_disposition` and
    `reconcile_interrupted`, `dict(item)` in `retry_deferred_integrations`) shown PRESERVED with the
    `i3d6ml` F-5/F-13 citation, since blindly applying the oc-preferred ruling here reintroduces a
    `KeyError` on a resume path; and the `--raw`/`--verbose` help-text change disclosed with BOTH hosts'
    strings before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: one-definition evidence for both symbols; the single differing line named for each
    (`dict(item)` vs `item`; the quoted vs unquoted `runner_stop.StopNowForce` annotation); the mechanism
    stated (`INJECTED` wrapper vs a new `HostLabels` field) with its reason. If a NEW `HostLabels` field was
    added, the named consumer that justifies it and BOTH hosts' bindings; if none was added, the explicit
    statement that none was needed and why. Do NOT satisfy this item by showing
    `retry_deferred_integrations` "producing the correct per-host command text": its `aw agy` token is in a
    DOCSTRING, so there is no such code path, and the authored wording asked for evidence of something that
    does not exist. Also required: the two `getsource` pins at `tests/test_runner_shared.py:3527`/`:3531`
    shown re-based, with `python3 -m pytest tests/test_runner_shared.py` green and pasted.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `python3 -m pytest tests/test_hostdedup_divergent_unify.py` green AND shown to fail
    against an introduced re-fork (paste the sabotage run too, since a guard never seen red is untested);
    the pin-table diffs for ALL FOUR files with a per-entry reason; the `_add_output_mode_flags`
    differ-assertion (`tests/test_rununify_build_parser.py:373`) re-based; the
    `tests/test_orchestrator_probe_cache.py:1238` import baseline re-measured from 53 with the removed names
    listed. The four pin files run TOGETHER and green. Then `python3 -m pytest` bare with the invocation FORM
    stated and a like-for-like PRE-work baseline beside it (see Required tests: the authored `7825` figure is
    wrong; use `32 failed, 7936 passed` for a worker lane or `7968 passed` with `env -u AW_EXECUTION_ROLE`),
    gating on NO NEW failures. Plus a real driver execution, since E-04/E-05 touch recovery, stop and
    integration-retry paths.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: verification that prompt suppression works on repeated interrupts without hanging in both runners; `test_lane_allocation_idempotent.py` green on both hosts; `UnmovableSymbolTests` green; evidence that all 12 symbols resolve to single definitions in `runner_shared` with thin delegations where pinned, leaving zero unshared residue and satisfying the parent Set's headline criterion (34 forks down to the 5 large functions); and backlog item `8hx3g3` updated to `graduated`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (7 E-items in 4 task groups, under the 18-leaf / 5-group thresholds).

This plan requires explicit human approval before execution. Unlike Order 01 it is NOT a pure move: E-04
and E-05 reconcile real differences, so the executor must state per symbol what was reconciled and must
stop rather than choose a winner where a difference looks like shipped behavior.

EXECUTION CONTRACT. All open questions (OQ-01 through OQ-05) are RESOLVED; execute their recorded answers and do not
re-litigate them. Specifically: E-02 is a NAMED RATCHET over this plan's own symbols, NOT a blanket ban, and
a guard that fires on the 44 pinned `as <same-name>` re-exports is mis-scoped, not strict. All 12 symbols
move to `runner_shared`, parameterizing prompt suppression so prompt suppression on repeated interrupts
functions correctly without hanging while preserving `disable_lane_prompt` and `_LANE_PROMPT_DISABLED` in
each runner per `UnmovableSymbolTests`. Backlog `8hx3g3` is graduated. Re-base `STILL_DOUBLE_DEFINED` pin
tables deliberately in the same change with the reasons recorded, per the maintainer's 2026-09-16 ruling.

SCOPE FENCE: this plan declares thirteen paths; an out-of-scope edit must be MADE if genuinely required and
then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a declared-but-unmodified path
needs a `--scope-ack`. Do not stop over a scope question. A genuinely unsafe condition (an unresolvable
concurrent-edit conflict, or `li44r9`'s symbols absent because Order 01 has not executed) IS a stop.

HARD-MUST HONESTY RULE: paste the ACTUAL runner output for every `V-*`; never claim a test passed that you
did not run. State the suite invocation FORM and paste a like-for-like PRE-work baseline beside the post-work
run, since the authored `7825 passed` figure matches neither measurement.

Work in an isolated worktree. Commit path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never
push. This is a SHARED CHECKOUT and roughly 33 other pending plans declare these same runner files: before
every commit run `git diff --cached --name-only` and unstage anything that is not yours with
`git restore --staged <path>`, and re-verify after any failed hook.

Post-gate lifecycle: the finalize obligation is unconditional, but its OWNER is conditional. Under
`aw oc run` / `aw agy run` the RUNNER owns `aw ipd begin` and `aw ipd finalize`; a hand-executed run means
the executor runs `aw ipd finalize` itself. Either way the plan reaches `.aw/records/plans/executed/` only
after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence. Never
hand-roll a `git mv` to `executed/`.
