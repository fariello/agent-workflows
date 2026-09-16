# IPD: Split main into a shared core and a thin host hook

- Date: 2026-09-15
- Kind: child
- Concern: `main` is written twice (297 lines in `oc_runipd.py`, 205 in `agy_runipd.py`) for the same job. Measured at HEAD it carries 46 differing code lines of which only 8 bear a host token. CORRECTED AT REVIEW 2026-09-16: the sentence that followed ("so most of the divergence is DRIFT in shared logic") is the boilerplate Concern shared with the four sibling split children and it is FALSE for this symbol. Classified rather than counted, the 46 lines are 19 host CAPABILITY (oc's entire `as <profile>` grammar plus `--verify-with`/`--validate`/`--variant` resume handling, against agy's `--agy-executable`), 10 host LABEL (`runipd:`/`runagy:`, `opencode`/`antigravity`), and only 17 genuine drift, of which 12 are a two-line style difference repeated twice and a block-ordering difference that changes nothing. So the real drift is ~5 lines out of 133, and this plan's F-1 (which says the same thing) is the correct reading. See F-6.
- Scope: Extract the host-neutral core of `main` into `runner_shared.py`, leaving each host a thin hook supplying only what is genuinely its own. Logic resolves to the `oc_runipd` version per the maintainer's 2026-09-14 ruling except where a difference is a real capability, which is called out per difference below. RE-SCOPED AT REVIEW: this plan may not execute the split until the maintainer decides OQ-03. The split as described cannot be performed without either (a) breaking the four `inspect.getsource(mod.main)` pins F-8 enumerates, (b) breaking the 26 `mock.patch.object(<host>, "<name>")` seams F-9 enumerates, which a shared core makes structurally unpatchable, or (c) hardcoding one host's `EmptyStatusSelection` subclass in the shared core, which F-7 proves silently converts exit 0 into exit 2 on the other host. E-01 through E-06 are executable under every route.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_rununify_main.py, tests/test_runner_backlog_close.py, tests/test_run_flag_surface.py, tests/test_oc_runipd.py, tests/test_oc_runipd_cli.py, tests/test_interrupt_menu.py, tests/test_run_summary_table.py, tests/test_runner_stop_triggers.py
- Item-Dependencies: executed:ty3cj6
- Status: reviewed
- Readiness: no-go
- Set: rununify
- Order: 11
- Highest E allocated: 06
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: 3dki3o
- From-Backlog: alw22r

## Workflow history
- 2026-09-16 reviewed (aw set): Reviewed 2026-09-16 by /plan-review: REVIEWED - OPEN QUESTIONS, NO-GO. 12 findings (PR-001..PR-012), 9 FIXED, PR-001/PR-002/PR-003 OPEN and escalated as blocking OQ-03. The 46/8 line measurement reproduces exactly, but `main` is the MOST host-specific of the five by capability content, not the least: 19 of the 46 lines are oc's `as <profile>` grammar and its three profile-bound resume flags, which agy has no subsystem for. Two mechanisms a shared core cannot preserve were found and neither is in the plan: four source pins read `inspect.getsource(mod.main)`, and 26 `mock.patch.object` seams across four test files patch names `main` resolves at module level, which a shared core reading its own module globals cannot see. A third hazard was proven by construction: hardcoding one host's `EmptyStatusSelection` in the shared core turns exit 0 into exit 2 on the other host.

- 2026-09-16 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO; PR-001 through PR-012 (9 FIXED, PR-001/PR-002/PR-003 OPEN and escalated as the new blocking OQ-03). EVERY NUMBER REPRODUCED at HEAD `6a3a671c`: 297/205 source lines, 133/111 AST-normalized lines, exactly 46 differing, exactly 8 bearing a host token, similarity 0.8115. THE CONCERN'S INFERENCE IS BACKWARDS AND F-1 IS RIGHT. Classified, the 46 lines are 19 CAPABILITY, 10 LABEL and 17 drift, and 12 of the 17 are one two-line style difference repeated twice plus a block reordering; the genuine drift is about 5 lines out of 133. THE FIVE FINDINGS THAT DECIDE THE PLAN, none of them in it. (1) `main` closes over 27 module-level names of which only 10 resolve in `runner_shared`; 9 are STILL DEFINED TWICE (`EmptyStatusSelection`, `build_parser`, `handle_stop_command`, `initialize_run`, `install_stop_triggers`, `locked_run`, `render_continuation_hint`, `run_queue`, `write_report`), 5 are one-object-via-agy's-import-of-oc, and 3 are oc-only. (2) FOUR PINS read `inspect.getsource(mod.main)` and assert substrings a thin caller cannot contain: `tests/test_runner_backlog_close.py:923/1073/1089` (the `--json` branch AST, `install_exit_signal_handler()`, `143`, and the `KeyboardInterrupt` handler containing `emit_shutdown_report`) and `tests/test_run_flag_surface.py:837` (`refuse_frozen_flags_on_resume` and `apply_run_policy_flags_on_resume`). (3) THE FINDING NO SIBLING REVIEW LOOKED FOR: 26 `mock.patch.object(<host module>, "<name>")` seams across `tests/test_oc_runipd.py`, `tests/test_oc_runipd_cli.py`, `tests/test_interrupt_menu.py` and `tests/test_run_summary_table.py` patch `run_queue` (7x), `locked_run` (6x), `build_parser` (3x), `install_stop_triggers`, `initialize_run`, `emit_shutdown_report`, `load_state` and `resolve_run_dir`. A shared core resolving these as its OWN module globals sees NONE of those patches; proven by construction in a scratch probe, where an import-time-frozen descriptor returned the real object while a call-time reference honored the patch. `tests/test_oc_runipd.py:4123`'s `_parse_argv` helper, which backs 12 profile-grammar assertions, is built entirely on that seam. (4) HARDCODING `EmptyStatusSelection` SILENTLY BREAKS AN EXIT CODE: the two hosts' classes are DISTINCT subclasses of the shared `DriverError` and neither is a subclass of the other, so `except <oc's>` in a shared core lets agy's fall through to the `except DriverError` arm; measured in a scratch probe, exit 0 became exit 2, violating spec `25kzda` 2.4a property 3. The good news is that this one IS covered: `tests/test_run_flag_surface.py:1787` and `tests/test_agy_runipd_cli.py:1200` assert it through `main` on both hosts. (5) F-5's claim that oc resolves the `opencode` binary in `main` is FALSE: `main` contains no binary resolution on either host (`resolve_agy` is called at `agy_runipd.py:3010`, inside `execute_item`'s reach, not `main`), so the one difference the plan calls genuinely host-specific is not there. ALSO: `main` holds 6 of oc's 38 and 5 of agy's 36 pinned `save_state` call sites, which `test_no_call_site_was_rewritten` counts. Suite baseline taken at review HEAD with a clean tree: ONE PRE-EXISTING FAILURE, `tests/test_runner_stop_triggers.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted`, reproducible in isolation and NOT caused by this review. Re-scoped to five single-concern items, seven test files fenced, non-vacuity made bidirectional. Typed record at `.aw/records/reviews/20260916-rununify-11-3dki3o-split-main-into-a-shared-core-and-a-thin-host-hook.review.md` with 12 findings and 6 decisions.

- 2026-09-15 to-review (aw set): Authored 2026-09-15 from a fresh measurement at HEAD; resolves part of the rununify parent's placeholder child rows per the maintainer's 2026-09-14 oc-preferred ruling.

- 2026-09-15 draft (opencode/its_direct-pt3-claude-opus-5): created.
- 2026-09-15 authored (opencode/its_direct-pt3-claude-opus-5): authored from a per-symbol diff measured at HEAD; the differing lines were counted and classified rather than estimated.

## Goal

Give `main` ONE implementation of everything that is not host-specific, so a fix lands once and reaches
both hosts, without changing what either runner does.

RESTATED AT REVIEW 2026-09-16, because the original goal is not achievable as described and the reason is
measurable rather than aesthetic. `main` is an ENTRY POINT: it parses, routes, and translates errors, so
almost every line is a call to something else or a `getattr(args, ...)` on a flag one host owns. Three
independent measurements say the split cannot be a relocation.

FIRST, THE CLOSURE. `main` closes over 27 module-level names:

| Closure class | Count | Members | Consequence |
|---|---|---|---|
| Resolves in `runner_shared` today | 8 | `DriverError`, `Palette`, `json`, `load_state`, `render_run_summary_table`, `resolve_run_dir`, `should_color`, `sys` | moves for free |
| Name in `runner_shared` but host object DIFFERS (a per-host wrapper) | 2 | `print_status`, `save_state` | must be injected, or the host label is lost |
| Already ONE object, agy IMPORTS it from oc | 5 | `emit_shutdown_report`, `install_exit_signal_handler`, `render_runs_pointer`, `report_run_spec_edits`, `runner_shared` | needs relocation to `runner_shared`, not de-duplication |
| STILL DEFINED TWICE | 9 | `EmptyStatusSelection`, `build_parser`, `handle_stop_command`, `initialize_run`, `install_stop_triggers`, `locked_run`, `render_continuation_hint`, `run_queue`, `write_report` | each is an injected parameter, and injecting it is the opposite of sharing it |
| oc-ONLY (no agy counterpart exists) | 3 | `ProfileClauseError`, `extract_profile_clause`, `print_launch_identity` | host hook, permanently |

8 + 2 + 5 + 9 + 3 = 27. E-01 must re-derive this rather than trust it.

SECOND, AND THIS IS THE FINDING THAT MAKES `main` DIFFERENT FROM ITS FOUR SIBLINGS. `main` is not just
SOURCE-pinned (4 pins, F-8); it is MONKEYPATCH-pinned. 26 `mock.patch.object(<host module>, "<name>")`
sites across four test files replace names `main` resolves at module level, and a shared core in
`runner_shared` resolves its own globals, so it sees NONE of them (F-9). That is a different failure from
a source pin: a source pin fails LOUDLY at the assertion, while a lost patch seam makes a test exercise
REAL `run_queue`, real `locked_run`, real `initialize_run` against a temp repo. The 12 profile-grammar
assertions built on `tests/test_oc_runipd.py:4123`'s `_parse_argv` helper are all in that class.

THIRD, THE EXIT-CODE HAZARD IS REAL AND IS NOT THE ONE F-2 NAMES. F-2 warns not to renumber an exit code.
The actual mechanism is subtler and was proven by construction: the two hosts' `EmptyStatusSelection` are
DISTINCT classes, siblings under the shared `DriverError` and not subclasses of each other, so a shared
core writing `except EmptyStatusSelection` against one host's class lets the other host's instance fall
through to `except DriverError` and return 2 where the spec requires 0 (F-7).

So the honest goal for THIS plan, pending OQ-03, is: MEASURE the closure and the two pin populations,
PIN both hosts' current behavior including the exit-code contract, and DELIVER the analysis the Set needs,
rather than perform a split that would silently disarm 26 test seams.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

SCOPE GATE ADDED AT REVIEW 2026-09-16. E-01, E-02, E-03, E-05 and E-06 are authorized unconditionally:
they measure, they pin current behavior, and they guard what changed. THE SPLIT ITSELF IS GATED on OQ-03,
which is `Blocking: yes`, so the lint gate refuses execution until the maintainer answers; E-04's
deliverable is the ANALYSIS that decision needs, and it performs no relocation.

### Task group 1: measure before touching

- [ ] E-01 MEASURE THE THREE POPULATIONS at execution HEAD, and refuse to proceed to E-04 on a stale list. This is the method that reversed siblings `i3d6ml` and `ty3cj6`, and it is NOT the body-difference method this plan originally used. (a) THE CLOSURE: parse `oc_runipd.main`, collect every free name resolving at MODULE level, and classify each into the five classes of the Goal table; name any symbol whose class changed since 2026-09-16. (b) THE SOURCE PINS: find every `inspect.getsource(<host>.main)` in `tests/`, and for each record the substring or AST shape it requires and whether a thin caller can still satisfy it (F-8 lists four). (c) THE PATCH SEAMS: find every `mock.patch.object`/`monkeypatch.setattr` on a host module naming a symbol in the closure, and classify each by whether a shared core would still observe it (F-9 measured 26 across four files). This E-item writes NO runner logic.
  - Depends on: none
  - Expected outcome: three reproducible tables in the execution report, with the method stated and the HEAD named; the count of still-double-defined names stated; the source-pin and patch-seam counts stated with each file and line.
  - Execution state: pending

- [ ] E-02 PIN THE CURRENT BEHAVIOR OF BOTH HOSTS, per the parent's E-02 constraint that no child may reconcile a symbol the characterization baseline has not pinned. Write characterization tests for `main` on BOTH hosts covering every branch the split would move, following the precedent of `tests/test_wtiso_characterization.py`. Cover, by name and on BOTH hosts: the five exit codes `main` actually returns (0, 2, 130, 143, and the `print_help` 0), the implicit-start shim including the `stop` non-rewrite, the four `except` arms in order, and the `--json` status branch's suppression of the pointer line. PRIORITIZE the agy side, which the parent measured as the less covered one. Assert on OBSERVABLE BEHAVIOR (return code, stdout, stderr, on-disk state), NOT on source text: adding a fifth source pin would hand the next refactor a problem this plan is documenting. This E-item writes TESTS ONLY and changes no runner logic.
  - Depends on: E-01
  - Expected outcome: a committed characterization suite that passes against UNMODIFIED code and would fail if either host's observable behavior moved; the agy branches previously uncovered are named; no new `inspect.getsource(main)` pin introduced.
  - Execution state: pending

- [ ] E-03 PIN THE EXIT-CODE CONTRACT THAT F-7 SHOWS IS SILENTLY BREAKABLE, as its own item because it is the one hazard whose failure mode is invisible. Assert, on BOTH hosts, that an empty status sweep returns 0 with `Nothing awaiting review` and creates no run directory, AND assert the STRUCTURAL fact that makes the hazard possible: each host's `EmptyStatusSelection` is a subclass of the shared `runner_shared.DriverError` and is NOT a subclass of the other host's. Existing coverage is `tests/test_run_flag_surface.py:1787` and `tests/test_agy_runipd_cli.py:1200`; this item adds the structural half those two do not assert, so a shared core that hardcoded one class would fail HERE rather than in production.
  - Depends on: E-01
  - Expected outcome: a test that fails if either host's empty-sweep exit code moves off 0, plus a test that fails if the two `EmptyStatusSelection` classes are collapsed to one without proving both hosts still exit 0.
  - Execution state: pending

### Task group 2: the split, GATED

- [ ] E-04 DO NOT PERFORM THE SPLIT UNTIL OQ-03 IS ANSWERED, and record the analysis rather than silently skipping it. The deliverable is the disclosure, so an executor cannot mistake the omission for an oversight and "finish" it later. State, from E-01's tables: (a) the eleven dependencies a shared core would have to take (the 9 double-defined plus the 2 host-wrapped) and which of them the maintainer's `818uru` OQ-02 wrapper ruling already governs; (b) the four source pins with a verdict each; (c) the 26 patch seams, with an explicit statement of which are LOST rather than merely broken, since a lost seam degrades silently where a broken pin fails loudly; (d) whether re-ordering this plan AFTER siblings 07/08/09/10 would reduce the eleven, since `run_queue` (child 08), `initialize_run` (child 09), `build_parser` (child 10) and `render_continuation_hint`/`write_report` (child 04) are five of them, and note that sibling `ty3cj6`'s own review left child 08 NO-GO, so the declared `executed:ty3cj6` edge points at a plan that cannot currently execute; and (e) whether oc's `as <profile>` grammar (19 of the 46 differing lines) can live in a shared core at all, given agy has no profile subsystem.
  - Depends on: E-01
  - Expected outcome: a written analysis sufficient for the maintainer to answer OQ-03 without re-deriving the measurement; no runner logic changed by this item.
  - Execution state: pending

### Task group 3: proof

- [ ] E-05 Add `tests/test_rununify_main.py` and assert E-01's CLOSURE CLASSIFICATION mechanically, driven by a named table rather than by literals in the assertion bodies. A symbol that silently changes class must fail here. Do NOT write any assertion about a shared core: OQ-03 gates the split, and a test asserting a state the code is not in is a failing test rather than a guard.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: a suite that fails if any of the 27 closure names changes class, driven by one table.
  - Execution state: pending

- [ ] E-06 Add the two INVERSE assertions to `tests/test_rununify_main.py`, in their own item because they guard against a different actor than E-05 does. E-05 guards against the CODE drifting; these guard against a later AGENT quietly clearing the obstacles in order to make a split pass. Assert that the four F-8 source pins are STILL PRESENT (naming each `path:line` and its required substring or AST shape), and that `main` is STILL DEFINED in both runners, each with a comment naming OQ-03 as the reason it must stay.
  - Depends on: E-05
  - Expected outcome: a suite that fails if a source pin is deleted or if `main` is unilaterally moved into `runner_shared`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared.py` is the established home for host-neutral runner logic and imports no runner, so it
  can hold the core without a cycle. It already uses NAME/VALUE INJECTION for exactly this shape
  (`run_checked(..., env_builder=)`, `save_state(..., write_report=)`, `resume_via_launcher(launcher, ...)`),
  which is the pattern the hook should follow rather than a new mechanism.
- `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` forbids a runner-to-runner
  import, so the core must land in `runner_shared` and never be reached by importing the other host.
  CORRECTED AT REVIEW: that guard is a SUBSTRING check for `"import oc_runipd"` /
  `"import agy_runipd"` (`tests/test_review_findings_cascade.py:312-313`), and agy uses the
  `from agent_workflows.oc_runipd import (...)` form TEN times, which the substring does not match. So
  agy DOES import oc today, and FIVE of the names `main` closes over reach agy exactly that way. Do not
  cite this guard as evidence the coupling is absent; cite `runner_shared`'s own no-runner-import rule
  (`tests/test_runner_shared.py:955`), which IS AST-based and does hold.
- `tests/test_runner_stop_triggers.py:1001` and `:1055` REGEX `subcommands = \{(.*?)\}` out of BOTH
  runner SOURCE FILES and require the two sets to be identical, and both runners carry a
  KEEP-THIS-INLINE comment (`oc_runipd.py:9085-9089`, `agy_runipd.py:5533-5535`) recording that hoisting
  the set into a module constant makes the guard "silently unmatchable (measured: it fails with
  unexpectedly None)". So the implicit-start shim's subcommand set MUST STAY an inline literal in each
  host's own file. That is a hard constraint on the hook boundary: the shim cannot move into the core
  unless the guard is rewritten, and the guard is what stops `stop <run-id>` being rewritten to
  `start stop <run-id>` in one driver only.
- `tests/test_runner_shared.py:1148` (`test_no_call_site_was_rewritten`) counts `save_state` and
  `print_status` CALL SITES per runner via AST and currently expects 38/36 and 2/2 (verified passing at
  review). `main` holds SIX of oc's 38 `save_state` sites and FIVE of agy's 36, plus BOTH `print_status`
  sites on each host. Moving them into `runner_shared` drops those counts, and the test's own documented
  rule is that a moved count must be explained as a RELOCATION, in the file, not absorbed into a new
  literal.
- The parent Set forbids a child changing what a runner DOES, and forbids reconciling a symbol the
  characterization baseline has not pinned. E-02 exists to satisfy the second constraint.
- The execution contract forbids `git add -A`; commit only the declared `Scope-Paths`, path-scoped.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | measured at HEAD | `main` is the process entry point: argument dispatch, subcommand routing, and the top-level error translation. ~~Only 8 of 46 changed lines carry a host token, so most of the difference is drift.~~ **THE COUNT IS RIGHT AND THE CONCLUSION IS WRONG; CORRECTED AT REVIEW 2026-09-16.** Verified: 297/205 source lines, 133/111 AST-normalized, exactly 46 differing, exactly 8 host-token, similarity 0.8115. But a host TOKEN is the wrong discriminator for this symbol: classified by cause, 19 lines are host CAPABILITY (oc's `as <profile>` clause and its `--verify-with`/`--validate`/`--variant` resume handling, against agy's `--agy-executable`), 10 are host LABEL, and 17 are drift of which 12 are one style difference repeated twice plus a block reordering. Real drift: about 5 lines of 133. `main` is the most CAPABILITY-divergent of the five, not the least. |
| F-2 | HIGH | `main`, both hosts | THE HAZARD THIS SPLIT CARRIES: `main` owns EXIT CODES. Spec `25kzda` Section 5.6 pins them. **CORRECTED AT REVIEW: the spec's table is 0/1/2/3/4/130 and the row for 2 is "Invalid invocation, selector, or unknown type", not "cannot-run"; the spec ALSO records at `:1082` that "the drivers themselves return only `0`/`2`/`130`/`143` today (`oc_runipd.main`)", citing this very function. And `tests/test_exit_codes.py` DOES NOT EXIST** (the repository's exit-code file is `tests/test_json_and_exitcodes.py`, which tests `cli.main` and never touches either runner). So the hazard is real but the plan cites a nonexistent guard for it; the actual guards are F-7's two, plus `tests/test_run_summary_table.py:352/367` (143 and 130 through `oc_runipd.main`) and `tests/test_interrupt_menu.py:344/365` (130 on both hosts). |
| F-3 | MED | `main` | DIFFERENCE, subcommand routing: each host routes its own verbs; the ROUTING TABLE is host data, the dispatch loop is not. **CORRECTED AT REVIEW: the two hosts route the IDENTICAL five verbs** (`start`, `resume`, `status`, `report`, `stop`) and their implicit-start `subcommands` sets are asserted EQUAL by `tests/test_runner_stop_triggers.py:1041`. There is no per-host routing table to parameterize. What is host-specific is not the routing but what each branch DOES with `args`, which is F-1's capability difference. Also note the set must stay an INLINE LITERAL per the regex guard (see Project conventions). |
| F-4 | MED | `main` | DIFFERENCE, error translation: the `DriverError` to exit-code mapping is shared logic that has drifted; unify it and keep each host's message prefix from the descriptor. **VERIFIED AT REVIEW and it is the soundest finding in the original table.** The four `except` arms are in the same order on both hosts with the same return values; the only difference is the `runipd:` / `runagy:` prefix on 4 oc and 2 agy `print` calls. A descriptor field carries it. NOTE the prefix is NOT the parser `prog` (measured: `runipd`/`runagy`, which coincidentally match) and appears nowhere in `tests/` as an assertion, so nothing pins it today. |
| F-5 | MED | `main` | ~~DIFFERENCE, host binary resolution: oc resolves `opencode`, agy resolves via `resolve_agy`.~~ **FALSE, RETRACTED AT REVIEW 2026-09-16.** Neither host's `main` resolves a binary. `resolve_agy` is defined at `agy_runipd.py:1929` and its only call is `agy_runipd.py:3010`, inside the turn-launch path, not `main`; and `main`'s only two `opencode` occurrences on oc are the `driver_label="opencode"` argument to `render_run_summary_table`, which is F-6's label, not a resolution. So the ONE difference this plan called genuinely host-specific is not in the symbol. Its closure confirms it: no binary-resolution name appears among the 27. |
| F-6 | HIGH | the plan's own Concern | **THE CONCERN CONTRADICTS F-1 AND F-1 IS RIGHT.** "Most of the divergence is DRIFT in shared logic rather than genuine host specificity" is the boilerplate sentence shared verbatim with the four sibling split children, and for this symbol the classification refutes it (F-1). An executor trusting the Concern would hunt for drift to reconcile and instead find oc's entire launch-profile grammar, which agy has no subsystem to support. Concern corrected in place. |
| F-7 | BLOCKER | `oc_runipd.py:9338`, `agy_runipd.py:5690`; proven by construction at review | **HARDCODING ONE HOST'S `EmptyStatusSelection` IN A SHARED CORE SILENTLY TURNS EXIT 0 INTO EXIT 2 ON THE OTHER HOST.** Measured: `oc.EmptyStatusSelection` and `agy.EmptyStatusSelection` are DISTINCT classes, both direct subclasses of the SHARED `runner_shared.DriverError`, and NEITHER is a subclass of the other (`issubclass(agy.ESS, oc.ESS)` is False). Both hosts' `main` orders `except EmptyStatusSelection` BEFORE `except DriverError` precisely because the first is a subclass of the second. So a shared core writing `except EmptyStatusSelection` resolved against ONE host lets the other host's instance fall through to the `DriverError` arm and return 2. Reproduced in a scratch probe: the same core returned 0 for the matching class and 2 for the sibling class, printing `runX: empty` instead of `Nothing awaiting review`. That violates spec `25kzda` 2.4a property 3 (an empty status sweep is the healthy state and exits 0). THE GOOD NEWS: this one IS covered, by `tests/test_run_flag_surface.py:1787` (both hosts through `main`) and `tests/test_agy_runipd_cli.py:1200`, so the break would be caught, loudly. E-03 adds the structural half neither asserts. |
| F-8 | HIGH | four sites in two test files | **FOUR PINS READ `inspect.getsource(<host>.main)` AND A THIN CALLER SATISFIES NONE OF THEM.** (1) `tests/test_runner_backlog_close.py:923` parses the source to AST and requires the `--json` branch to contain `json.dumps` and NOT contain `render_runs_pointer`, for BOTH hosts. (2) `:1073` requires the source to contain the literal `install_exit_signal_handler()` and the literal `143`. (3) `:1089` requires an `except` handler naming `KeyboardInterrupt` whose body contains `emit_shutdown_report`. (4) `tests/test_run_flag_surface.py:837` requires the source to contain `refuse_frozen_flags_on_resume` and `apply_run_policy_flags_on_resume`, for BOTH hosts. Every one FAILS the moment the body moves. This is the same class of obstacle three sibling reviews found, and unlike sibling `s16omw` (zero pins on `build_parser`) `main` has them. All two files added to the fence. |
| F-9 | BLOCKER | four test files, 26 sites; mechanism proven by construction | **THE FINDING NO SIBLING REVIEW LOOKED FOR, AND IT IS WORSE THAN A SOURCE PIN BECAUSE IT FAILS SILENTLY. 26 `mock.patch.object(<host module>, "<name>")` SEAMS PATCH NAMES `main` RESOLVES AT MODULE LEVEL.** Measured: `run_queue` 7x, `locked_run` 6x, `build_parser` 3x, `install_stop_triggers` 2x, `emit_shutdown_report` 2x, `load_state` 2x, `resolve_run_dir` 3x, `initialize_run` 1x, across `tests/test_oc_runipd.py`, `tests/test_oc_runipd_cli.py`, `tests/test_interrupt_menu.py` and `tests/test_run_summary_table.py`. A function in `runner_shared` resolves these as ITS OWN globals, so patching the HOST module has no effect on it. Proven by construction in a scratch probe: an import-time-frozen descriptor returned the REAL object while a call-time reference honored the patch, so whether a seam survives depends on a design detail the plan does not specify. WHY THIS IS THE SHARPEST FINDING: a broken source pin fails loudly at its assertion, but a lost patch seam makes the test run the REAL `run_queue`, the REAL `locked_run` and the REAL `initialize_run` against a temp repo, which may still pass while asserting nothing it claims to. `tests/test_oc_runipd.py:4123`'s `_parse_argv` helper is built entirely on this seam (it patches `build_parser`, `initialize_run` and `resolve_run_dir` to stop before side effects) and backs 12 launch-profile grammar assertions. All four files added to the fence. |
| F-10 | MED | `tests/test_runner_shared.py:1148` | **THE SPLIT MOVES PART OF A PINNED CALL-SITE POPULATION.** `test_no_call_site_was_rewritten` counts call sites by AST per runner and currently expects 38/36 for `save_state` and 2/2 for `print_status` (verified passing at review). `main` holds SIX of oc's 38 and FIVE of agy's 36 `save_state` sites, and BOTH `print_status` sites on each host. Moving them drops those counts, and the test's own rule forbids fixing that by editing the literal: "If a count moves and you cannot name the new call site, the wrapper ruling has been undone". The correct treatment is a documented RELOCATION subtraction, exactly as `RELOCATED_RUN_CHECKED_CALLERS` does. The plan does not mention it. |
| F-11 | MED | E-02/E-03/E-04 right-sizing as authored | The original E-02 bundled the relocation of a 297-line entry point, its eleven dependency decisions, the exit-code contract, and the repair of six test files into ONE item, invisible to the count-based lint. The re-scoped items are one measurement, one test-only baseline, one exit-code pin, one written analysis and one guard suite: one focused pass each. |
| F-12 | LOW | `Item-Dependencies: executed:ty3cj6` | **THE DECLARED EDGE POINTS AT A PLAN THAT CANNOT CURRENTLY EXECUTE.** Sibling `ty3cj6` (child 08, `run_queue`) was reviewed 2026-09-16 to `reviewed`/`no-go` with its own blocking OQ-03, and its review RE-SCOPED it to explicitly NOT perform its split. So even when `ty3cj6` executes, `run_queue` will still be double-defined and will still be one of this plan's eleven injections. The same holds for children 09 and 10, both `no-go`. The dependency is not wrong, it is INSUFFICIENT, and that is part of OQ-03. |

## Proposed changes (ordered, validatable)

1. Measure the CLOSURE, the SOURCE PINS and the PATCH SEAMS at execution HEAD (E-01).
2. Characterize both hosts' current behavior for every branch a split would move, on observable
   behavior rather than source text (E-02).
3. Pin the exit-code contract F-7 shows is silently breakable, including its structural half (E-03).
4. Record the split analysis as a DELIVERABLE for OQ-03 rather than performing it (E-04).
5. Add the guard suite asserting E-01's closure classification mechanically (E-05).
6. Add the INVERSE assertions: the four source pins are still present, and `main` is still defined in
   both runners (E-06).

## Deferred / out of scope (with reason)

- The other four large functions of this Set, each owned by its own sibling child, because each is a
  distinct seam and the parent forbids a child exceeding one cohesive seam.
- The 48 no-disagreement symbols (child 03), the 8 host-string symbols (child 04), the two behavior
  conflicts (child 05), and the record type (child 06). All are ordered BEFORE this plan so their
  results are available rather than re-derived. NOTE at review: children 03 through 10 are ALL
  `reviewed`/`no-go` with open blocking questions, so none of their results is available yet (F-12).
- THE SPLIT ITSELF, deferred to OQ-03 rather than attempted. Reason stated plainly because a reader will
  otherwise assume it was forgotten: performing it today requires eleven injected dependencies, breaks
  four source pins, and silently disarms up to 26 monkeypatch seams. All three are decisions above this
  plan's authority.
- REPAIRING agy's THREE MISSING RESUME CAPABILITIES (`--validate`, `--variant`, `--verify-with`). They
  are absent because agy has no launch-profile subsystem, so adding them is a FEATURE, not a
  de-duplication, and the parent Set forbids a child changing what a runner does.
- Any behavior change, feature addition, or flag change.

## Scope check

- Over-scope: none. This plan now changes NO product code at all: E-01 measures, E-02 and E-03 write
  tests, E-04 writes analysis, E-05 and E-06 write a guard suite. The six existing test files added to the fence
  are declared so a pin repair is visible if one proves necessary; if they stay untouched, `--scope-ack`
  each at finalize.
- Under-scope: this plan does not perform the split it is named for. That is deliberate and gated
  (OQ-03), not an omission: E-04's deliverable is the analysis the maintainer needs to decide. It also
  does not attempt to shrink `main` itself, which remains a legitimate later refactor.

## Required tests / validation

1. E-01's three tables, reproducible: a reader must be able to re-run the stated method and obtain the
   stated classification. State the HEAD, because it will move.
2. The E-02 characterization suite, green against UNMODIFIED code. Both hosts' suites alone are NOT
   sufficient, because the parent measured them as asymmetric (95 oc tests versus 21 agy at the time),
   so an agy-side regression can hide behind green. Confirm explicitly that it introduced NO new
   `inspect.getsource(main)` pin.
3. E-03's exit-code pins green, and `tests/test_run_flag_surface.py` green with its 89-test baseline
   (verified at review: `89 passed`).
4. `tests/test_rununify_main.py` (new): the closure classification asserted mechanically; the four F-8
   source pins asserted STILL PRESENT; `main` asserted still defined in both runners.
5. NON-VACUITY, BIDIRECTIONAL. Two controls, both pasted. (a) Break the exit-code contract in the
   direction F-7 names, by making one host's `EmptyStatusSelection` inherit from the other's, and show
   E-03's structural assertion FAILS; restore. (b) Delete one of the four F-8 source pins and show
   E-06's inverse assertion FAILS; restore. A guard that only fails one way does not pin a boundary.
6. `tests/test_runner_shared.py::WrapperTests::test_no_call_site_was_rewritten` green, stated
   explicitly (F-10): it must still expect 38/36 for `save_state` and 2/2 for `print_status`, because
   this plan adds no call site.
7. THE SIX FENCED TEST FILES, each green by name and each named in the report:
   `tests/test_runner_backlog_close.py`, `tests/test_run_flag_surface.py`, `tests/test_oc_runipd.py`,
   `tests/test_oc_runipd_cli.py`, `tests/test_interrupt_menu.py`, `tests/test_run_summary_table.py`,
   plus `tests/test_runner_stop_triggers.py` for the inline-literal guard. If this plan leaves them all
   untouched, SAY SO with the passing output rather than editing them speculatively.
8. Bare `python3 -m pytest`, summary pasted, no new failure against the baseline at execution time.
   TAKE YOUR OWN BASELINE AT YOUR HEAD before changing anything. Measured at review HEAD `6a3a671c`
   with a clean tree, ONE test already fails:
   `tests/test_runner_stop_triggers.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted`
   (reproducible in isolation, and it exercises `main`'s exit-130 path, so do NOT attribute it to this
   plan and do NOT read a green run of it as evidence either).

## Spec / documentation sync

No `.spec.md` change expected while the split stays gated: E-01 through E-06 touch no operator-visible
contract. TWO THINGS WORTH CHECKING AT EXECUTION, added at review, because this symbol is more
spec-coupled than the boilerplate admits. FIRST, spec `25kzda` Section 5.6's exit-code table names
`oc_runipd.main` explicitly at `:1082` and records an UNRECONCILED CONFLICT between itself and the
`aw runs` table for codes 4 and above; do not "fix" that in passing, but if E-02's characterization finds
the drivers return a code the table does not list, say so. SECOND, `25kzda` 2.4a property 3 (an empty
status sweep exits 0) is exactly the contract F-7 shows a careless shared core would break, so E-03's
pins are spec conformance evidence and should be cited as such. IF execution finds a spec sentence
describing the divergence being removed, amend it in the SAME change and add the spec path to
`Scope-Paths`, per the repository's spec-amendment rule.

## Open questions

### OQ-01: Where exactly does the hook boundary belong?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: At the points Findings names as genuinely host-specific, and nowhere
  else. The test is mechanical rather than aesthetic: if a candidate boundary would require the shared
  core to contain an `if host == ...` branch, the boundary is in the wrong place, because that branch is
  the duplication this Set exists to remove wearing a different shape.

### OQ-02: What if the split cannot be done without changing behavior?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: STOP AND REPORT rather than proceeding. The parent's hard constraint
  is that a child may not change behavior, and E-02's characterization suite is what makes a violation
  visible instead of silent. A partial split that leaves a smaller shared core is an acceptable outcome
  and is strictly better than a complete split that moves behavior; say which branches were left behind
  and why. CONFIRMED AT REVIEW 2026-09-16, and the condition this question anticipated HAS OCCURRED:
  F-7, F-8 and F-9 are the report, and OQ-03 is the stop. This resolution is what makes the re-scope
  obedient to the plan rather than a departure from it.

### OQ-03: The split breaks four source pins and may silently disarm 26 patch seams. Which route does the Set take?

- Blocking: yes
- Finding: PR-001, PR-002, PR-003
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT DECIDED, deliberately, because every route restructures a Set
  with nine pending children and an approved orchestrator, and that is a scope-and-sequencing call the
  maintainer owns.
  THE MEASUREMENT, not an opinion. `main` closes over 27 module-level names: 8 resolve in
  `runner_shared`, 2 have a per-host wrapper there, 5 are one object agy imports from oc, 9 are STILL
  DEFINED TWICE, and 3 are oc-only. Separately, FOUR pins assert substrings or AST shapes of
  `inspect.getsource(<host>.main)` that a thin caller cannot contain (F-8), and 26 `mock.patch.object`
  seams across four test files patch names `main` resolves at module level, which a shared core would
  not observe (F-9). And hardcoding either host's `EmptyStatusSelection` in the core returns 2 where the
  spec requires 0 (F-7, proven by construction).
  FOUR ROUTES, with what each costs. (A) INJECT ALL ELEVEN now and repair the pins: gets one shared entry
  point, but the core takes eleven parameters, de-duplicates none of them, and the 26 patch seams must
  each be converted to patch the injected parameter instead of the module name, which is a rewrite of
  four test files including the `_parse_argv` helper that backs 12 launch-profile assertions; the
  maintainer already rejected uniform injection at smaller scale in `818uru` OQ-02. (B) RE-ORDER this
  plan LAST, after children 04/07/08/09/10, so `run_queue`, `initialize_run`, `build_parser`,
  `render_continuation_hint` and `write_report` are already shared and the injection count falls from
  eleven to about six; costs a Set re-ordering, and note this plan is ALREADY last (Order 11), so what
  route (B) really asks is whether the four `no-go` siblings ahead of it can be unblocked first. (C)
  SHARE ONLY THE ERROR-TRANSLATION TAIL, which is F-4's four `except` arms plus the two `print` prefixes:
  it is the one genuinely shared, genuinely drifted piece, it closes over far fewer names, and it is
  where a fix landing once actually helps; leaves the parse/route head duplicated. (D) DO NOT SPLIT
  `main` AT ALL: it is an ENTRY POINT, its job is to bind one host's CLI to one host's behavior, 19 of
  its 46 differing lines are a capability agy does not have, and the de-duplication payoff is roughly 5
  lines of real drift against the largest test-infrastructure cost in the Set.
  RECOMMENDATION: (C), then (D). (C) captures the actual benefit at a fraction of the risk: the error
  tail is the part where the two copies have genuinely drifted, it needs none of the nine
  double-defined symbols, and it breaks no patch seam because the seams are all on the parse/route head.
  (D) is a respectable outcome and should be said out loud rather than left as a silent failure, since a
  Set that unifies the shared machinery and documents why the ENTRY POINT stayed per-host is a better
  record than one that forces a shared `main` and leaves 26 tests asserting less than they claim.
  (A) is not recommended. (B) is not actionable while four siblings are `no-go`.
  THIS PLAN'S E-01 THROUGH E-06 ARE EXECUTABLE UNDER EVERY ROUTE and produce the analysis the decision
  needs; only E-04's split is gated.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: THREE pasted tables with the command or script that produced each, and the HEAD. (a) The closure, all 27 names classified into the five classes of the Goal table, explicitly stating the count STILL DEFINED TWICE. (b) The source pins, each with its `path:line`, the substring or AST shape it requires, and a verdict on whether a thin caller satisfies it. (c) The patch seams, each with its `path:line` and the symbol patched, plus an explicit count. A table that merely repeats this plan's numbers without re-deriving them at execution HEAD does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted green run of the characterization suite against UNMODIFIED code; the list of agy branches it newly covers, named; the five exit codes it pins per host, named; a sabotage of one pinned branch showing the suite FAILS (a characterization test that cannot fail pins nothing); and an explicit confirmation, with the grep result, that it added NO new `inspect.getsource(main)` pin.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: THREE parts, all pasted. (a) The empty-sweep assertions green on BOTH hosts (exit 0, `Nothing awaiting review`, no run directory created). (b) The STRUCTURAL assertion green: each host's `EmptyStatusSelection` subclasses `runner_shared.DriverError` and is NOT a subclass of the other host's, with the measured `issubclass` results shown. (c) `tests/test_run_flag_surface.py` green with its 89-test baseline.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the written analysis itself, covering all five parts (a) through (e) that E-04 enumerates, with the four pins of F-8 and the 26 seams of F-9 each given a verdict, and the LOST-versus-BROKEN distinction stated for the seams. Plus an explicit statement that NO split was performed and that OQ-03 remains the maintainer's, so the omission cannot be read as an oversight.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `python3 -m pytest tests/test_rununify_main.py -o addopts=""` green, pasted, plus the table the closure assertions are driven from, shown in the test source, plus a demonstration that changing one entry in that table makes the suite FAIL (a classification assertion that cannot fail pins nothing).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: FOUR parts, all pasted. (a) The two inverse assertions green, naming the four pins they check. (b) The BIDIRECTIONAL non-vacuity controls from Required tests item 5, both directions shown failing and then restored. (c) All SEVEN fenced test files green by name, plus `test_no_call_site_was_rewritten` with its 38/36 and 2/2 expectations unchanged. (d) Bare `python3 -m pytest` with no new failure against the baseline taken at execution HEAD, summary pasted, and the one pre-existing `test_the_terminal_rung_still_records_the_item_interrupted` failure either reproduced in the baseline or explained.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

OPEN QUESTION GATE. OQ-03 is `Blocking: yes` and OPEN. `aw ipd lint` refuses this plan at every
checkpoint until the maintainer answers it, which is intended: THE SPLIT is not executable on this plan's
own authority. E-01 through E-06 are all authorized unconditionally, because E-04 delivers the ANALYSIS
the decision needs rather than performing the relocation.

EXECUTION CONTRACT. Commit ONLY the declared `Scope-Paths`, path-scoped; never `git add -A` and never
push. Paste the ACTUAL runner output for every `V-*`. Run the suite BARE as `python3 -m pytest`. Do NOT
add `-n0`, a second `-q`, or `-p no:randomly`. The `Scope-Paths` fence is a DECLARATION: an out-of-scope
edit is made and then JUSTIFIED at finalize with a `--scope-reason`, and a declared-but-unmodified path
needs a `--scope-ack`, which is EXPECTED here for the six existing test files, since a plan that performs
no split should leave all of them untouched.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

REVIEWER'S HIGHEST-VALUE TARGETS, REWRITTEN 2026-09-16 because the original pointed at a guard that does
not exist (`tests/test_exit_codes.py`): F-9's 26 patch seams, because that is the only obstacle in this
Set whose failure mode is SILENT rather than a red test, and no amount of characterization coverage
detects it (a lost seam makes a test exercise real code that may still pass); F-7's exit-code mechanism,
which is the one hazard already covered and worth keeping that way; and F-5, retracted, as a reminder that
a plan asserting a difference is "genuinely host-specific" must cite the line, since this one could not.
