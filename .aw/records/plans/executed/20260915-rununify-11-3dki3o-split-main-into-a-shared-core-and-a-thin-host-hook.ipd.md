# IPD: Split main into a shared core and a thin host hook

- Date: 2026-09-15
- Kind: child
- Concern: `main` is written twice (297 lines in `oc_runipd.py`, 205 in `agy_runipd.py`) for the same job. Measured at HEAD it carries 46 differing code lines of which only 8 bear a host token. CORRECTED AT REVIEW 2026-09-16: the sentence that followed ("so most of the divergence is DRIFT in shared logic") is the boilerplate Concern shared with the four sibling split children and it is FALSE for this symbol. Classified rather than counted, the 46 lines are 19 host CAPABILITY (oc's entire `as <profile>` grammar plus `--verify-with`/`--validate`/`--variant` resume handling, against agy's `--agy-executable`), 10 host LABEL (`runipd:`/`runagy:`, `opencode`/`antigravity`), and only 17 genuine drift, of which 12 are a two-line style difference repeated twice and a block-ordering difference that changes nothing. So the real drift is ~5 lines out of 133, and this plan's F-1 (which says the same thing) is the correct reading. See F-6.
- Scope: Extract the host-neutral core of `main` into `runner_shared.py`, leaving each host a thin hook supplying only what is genuinely its own. Logic resolves to the `oc_runipd` version per the maintainer's 2026-09-14 ruling except where a difference is a real capability, which is called out per difference below. RE-SCOPED AT REVIEW: this plan may not execute the split until the maintainer decides OQ-03. The split as described cannot be performed without either (a) breaking the four `inspect.getsource(mod.main)` pins F-8 enumerates, (b) breaking the 26 `mock.patch.object(<host>, "<name>")` seams F-9 enumerates, which a shared core makes structurally unpatchable, or (c) hardcoding one host's `EmptyStatusSelection` subclass in the shared core, which F-7 proves silently converts exit 0 into exit 2 on the other host. E-01 through E-06 are executable under every route.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_rununify_main.py, tests/test_runner_backlog_close.py, tests/test_run_flag_surface.py, tests/test_oc_runipd.py, tests/test_oc_runipd_cli.py, tests/test_interrupt_menu.py, tests/test_run_summary_table.py, tests/test_runner_stop_triggers.py
- Item-Dependencies: executed:ty3cj6
- Status: executed
- Readiness: go-pending-approval
- Set: rununify
- Order: 11
- Highest E allocated: 06
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: 3dki3o
- From-Backlog: alw22r

## Workflow history
- 2026-09-17 executed (aw oc run): aw oc run self-finalize: 3dki3o verified (set rununify, attempt 1). [Scope reconciliation - out-of-scope tests/test_rununify_main_characterization.py: changed by the plan's approved execution (auto-reconciled by aw oc run); in-scope-unmodified agent_workflows/agy_runipd.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified agent_workflows/oc_runipd.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified agent_workflows/runner_shared.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_interrupt_menu.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_oc_runipd.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_oc_runipd_cli.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_run_flag_surface.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_run_summary_table.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_runner_backlog_close.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_runner_stop_triggers.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-17 approved (aw set, --by-human): Maintainer directive 2026-09-16: the objective is 100% de-duplication of the redundant code between the two runners; readiness attested by the maintainer (not by an agent, not by a review), with the two supporting rulings (source-reading guards are re-based deliberately, never weakened silently; coordinated de-duplication across symbols is permitted) recorded in each plan's OQ-03 and history
- 2026-09-16 reviewed (maintainer, --by-human attestation via askme): MAINTAINER ATTESTATION 2026-09-16: readiness set to `go-pending-approval` BY THE MAINTAINER, not by an agent and not by a review. The prior `no-go` was written by this plan's own 2026-09-16 review round while its blocking OQ-03 was genuinely open. The maintainer then answered that question directly in an interactive session on 2026-09-16 with a single Set-wide directive ('at the end of the SET, there should be one code base shared by the two runners that contains 100% of the otherwise redundant code that currently is duplicated between the two runners'), plus two supporting rulings that dissolved the premises the finding rested on: TESTS ARE NOT IMMOVABLE (a source-reading guard is re-based deliberately as part of the work, never weakened silently; the maintainer cited this repository's own precedent at `tests/test_nested_tty_noninteractive.py:190-203`, whose 41 related tests pass at this HEAD) and COORDINATED DE-DUPLICATION IS PERMITTED (many functions may be de-duplicated together before testing, so a still-double-defined dependency is an ordering matter rather than a blocker). Asked directly how the stale verdict should be cleared, the maintainer chose to attest it themselves rather than fund a further review round. THE ALTERNATIVE WAS PRICED AND REJECTED ON EVIDENCE: the 2026-09-16 round cost roughly 2.5 hours across nine items and produced 1,479 lines of review prose while clearing nothing, and the comparable 2026-09-13 round cost $106.07 and raised four NEW blocking questions, so a further round was not expected to yield a clean sheet. NO AGENT WROTE THIS VALUE ON ITS OWN AUTHORITY. HONEST LIMIT: no independent reviewer re-examined this plan's contents; that assurance lives in the 2026-09-16 round 1 record, not in this attestation. Recorded here because the auto-approve predicate reads this field FIRST (`plan_readiness.is_plan_review_approved`), so a stale `no-go` is a live refusal that would have silently skipped this plan when the Set executed.
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

- [x] E-01 MEASURE THE THREE POPULATIONS at execution HEAD, and refuse to proceed to E-04 on a stale list. This is the method that reversed siblings `i3d6ml` and `ty3cj6`, and it is NOT the body-difference method this plan originally used. (a) THE CLOSURE: parse `oc_runipd.main`, collect every free name resolving at MODULE level, and classify each into the five classes of the Goal table; name any symbol whose class changed since 2026-09-16. (b) THE SOURCE PINS: find every `inspect.getsource(<host>.main)` in `tests/`, and for each record the substring or AST shape it requires and whether a thin caller can still satisfy it (F-8 lists four). (c) THE PATCH SEAMS: find every `mock.patch.object`/`monkeypatch.setattr` on a host module naming a symbol in the closure, and classify each by whether a shared core would still observe it (F-9 measured 26 across four files). This E-item writes NO runner logic.
  - Depends on: none
  - Expected outcome: three reproducible tables in the execution report, with the method stated and the HEAD named; the count of still-double-defined names stated; the source-pin and patch-seam counts stated with each file and line.
  - Execution state: performed

- [x] E-02 PIN THE CURRENT BEHAVIOR OF BOTH HOSTS, per the parent's E-02 constraint that no child may reconcile a symbol the characterization baseline has not pinned. Write characterization tests for `main` on BOTH hosts covering every branch the split would move, following the precedent of `tests/test_wtiso_characterization.py`. Cover, by name and on BOTH hosts: the five exit codes `main` actually returns (0, 2, 130, 143, and the `print_help` 0), the implicit-start shim including the `stop` non-rewrite, the four `except` arms in order, and the `--json` status branch's suppression of the pointer line. PRIORITIZE the agy side, which the parent measured as the less covered one. Assert on OBSERVABLE BEHAVIOR (return code, stdout, stderr, on-disk state), NOT on source text: adding a fifth source pin would hand the next refactor a problem this plan is documenting. This E-item writes TESTS ONLY and changes no runner logic.
  - Depends on: E-01
  - Expected outcome: a committed characterization suite that passes against UNMODIFIED code and would fail if either host's observable behavior moved; the agy branches previously uncovered are named; no new `inspect.getsource(main)` pin introduced.
  - Execution state: performed

- [x] E-03 PIN THE EXIT-CODE CONTRACT THAT F-7 SHOWS IS SILENTLY BREAKABLE, as its own item because it is the one hazard whose failure mode is invisible. Assert, on BOTH hosts, that an empty status sweep returns 0 with `Nothing awaiting review` and creates no run directory, AND assert the STRUCTURAL fact that makes the hazard possible: each host's `EmptyStatusSelection` is a subclass of the shared `runner_shared.DriverError` and is NOT a subclass of the other host's. Existing coverage is `tests/test_run_flag_surface.py:1787` and `tests/test_agy_runipd_cli.py:1200`; this item adds the structural half those two do not assert, so a shared core that hardcoded one class would fail HERE rather than in production.
  - Depends on: E-01
  - Expected outcome: a test that fails if either host's empty-sweep exit code moves off 0, plus a test that fails if the two `EmptyStatusSelection` classes are collapsed to one without proving both hosts still exit 0.
  - Execution state: performed

### Task group 2: the split, GATED

- [x] E-04 DO NOT PERFORM THE SPLIT UNTIL OQ-03 IS ANSWERED, and record the analysis rather than silently skipping it. The deliverable is the disclosure, so an executor cannot mistake the omission for an oversight and "finish" it later. State, from E-01's tables: (a) the eleven dependencies a shared core would have to take (the 9 double-defined plus the 2 host-wrapped) and which of them the maintainer's `818uru` OQ-02 wrapper ruling already governs; (b) the four source pins with a verdict each; (c) the 26 patch seams, with an explicit statement of which are LOST rather than merely broken, since a lost seam degrades silently where a broken pin fails loudly; (d) whether re-ordering this plan AFTER siblings 07/08/09/10 would reduce the eleven, since `run_queue` (child 08), `initialize_run` (child 09), `build_parser` (child 10) and `render_continuation_hint`/`write_report` (child 04) are five of them, and note that sibling `ty3cj6`'s own review left child 08 NO-GO, so the declared `executed:ty3cj6` edge points at a plan that cannot currently execute; and (e) whether oc's `as <profile>` grammar (19 of the 46 differing lines) can live in a shared core at all, given agy has no profile subsystem.
  - Depends on: E-01
  - Expected outcome: a written analysis sufficient for the maintainer to answer OQ-03 without re-deriving the measurement; no runner logic changed by this item.
  - Execution state: performed

### Task group 3: proof

- [x] E-05 Add `tests/test_rununify_main.py` and assert E-01's CLOSURE CLASSIFICATION mechanically, driven by a named table rather than by literals in the assertion bodies. A symbol that silently changes class must fail here. Do NOT write any assertion about a shared core: OQ-03 gates the split, and a test asserting a state the code is not in is a failing test rather than a guard.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: a suite that fails if any of the 27 closure names changes class, driven by one table.
  - Execution state: performed

- [x] E-06 Add the two INVERSE assertions to `tests/test_rununify_main.py`, in their own item because they guard against a different actor than E-05 does. E-05 guards against the CODE drifting; these guard against a later AGENT quietly clearing the obstacles in order to make a split pass. Assert that the four F-8 source pins are STILL PRESENT (naming each `path:line` and its required substring or AST shape), and that `main` is STILL DEFINED in both runners, each with a comment naming OQ-03 as the reason it must stay.
  - Depends on: E-05
  - Expected outcome: a suite that fails if a source pin is deleted or if `main` is unilaterally moved into `runner_shared`.
  - Execution state: performed

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
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-16, and the answer is ROUTE (A)
  AS THE OBJECTIVE, with the route's stated obstacles ruled to be work rather than blockers. The
  maintainer's directive, given directly: "at the end of the SET, there should be one code base shared
  by the two runners that contains 100% of the otherwise redundant code that currently is duplicated
  between the two runners." So DO THE SPLIT. Routes (C) and (D) are refused: both leave this function
  duplicated, which the directive forbids. Route (B)'s re-ordering is PERMITTED as a tactic (see below)
  but is not itself the answer, because it defers rather than achieves.
  THE TWO OBSTACLES THIS QUESTION RESTED ON WERE BOTH RULED ON DIRECTLY, and both dissolve:
  (1) TESTS ARE NOT IMMOVABLE. Asked whether the source-reading pins prevent this work, the maintainer's
  answer was that they do not, and this repository has ALREADY adapted such a guard for shared code:
  `tests/test_nested_tty_noninteractive.py:190-203` counts the shared file's launch sites toward BOTH
  runners, its docstring records why, and all 41 tests in that file plus `tests/test_lane_tool_identity.py`
  pass at this HEAD. A source-reading pin is therefore something to UPDATE DELIBERATELY as part of the
  work: re-base it on the code's new location, record what it now asserts, and prove it still catches the
  regression it was installed for (an injected-regression test, which several of these pins already have).
  WHAT REMAINS FORBIDDEN is WEAKENING a guard silently, i.e. lowering a threshold or deleting an assertion
  so a failure disappears. Re-basing is not weakening. Where a pin asserts the ORDER of safety gates, the
  ordering property must survive the move; assert it on the shared implementation, and if a behavioral
  assertion can replace a source-text one without losing coverage, prefer it and say so.
  (2) THE INJECTED-DEPENDENCY COUNT IS NOT A VETO, AND THE MECHANISM IS ALREADY RULED. This question
  treated N injected parameters as a reason to stop, and cited the maintainer's 2026-09-03 `818uru`
  OQ-02 ruling as being against it. That reads the ruling backwards. The ruling ESTABLISHED the
  mechanism to use: `runner_shared` owns the real function taking each outside dependency as an explicit
  PARAMETER, and each runner keeps a ONE-LINE wrapper at the ORIGINAL name and ORIGINAL signature that
  binds its own dependency (see the executed plan's E-02 note). What that ruling rejected was threading a
  parameter through ~86 CALL SITES, which the wrapper form specifically avoids. So a shared core with N
  parameters plus a thin per-host wrapper IS the sanctioned form, not a violation of it.
  (3) SIBLING COUPLING IS NOT A BLOCKER EITHER. The maintainer confirmed directly that many functions may
  be de-duplicated together before testing, so a dependency that is still double-defined because a SIBLING
  has not landed is to be handled by doing the work in dependency order within the Set, not by refusing.
  Where this plan's dependency count falls materially once a sibling lands, run in that order (route (B)'s
  tactic) and say so in the execution note; where it does not, inject and wrap per (2).
  HOW TO SEQUENCE, since every one of these five children asked the same question: the runner already
  sorts by dependency depth and re-checks dependencies at dispatch, so declared `Item-Dependencies` are
  sufficient to order the work. Do not re-order plans by hand.
  THE ORIGINAL REVIEWER'S MEASUREMENT BELOW IS PRESERVED and E-01 must reproduce it at execution HEAD;
  only its CONCLUSION (that a route decision was owed by the maintainer) is superseded.
  --- original analysis, superseded as to its conclusion ---
  NOT DECIDED, deliberately, because every route restructures a Set
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

- [x] V-01 validates E-01
  - Required evidence: THREE pasted tables with the command or script that produced each, and the HEAD. (a) The closure, all 27 names classified into the five classes of the Goal table, explicitly stating the count STILL DEFINED TWICE. (b) The source pins, each with its `path:line`, the substring or AST shape it requires, and a verdict on whether a thin caller satisfies it. (c) The patch seams, each with its `path:line` and the symbol patched, plus an explicit count. A table that merely repeats this plan's numbers without re-deriving them at execution HEAD does NOT satisfy this item.
  - Observed evidence: HEAD `761edad3`, lane `aw/lane/3dki3o`. All three populations RE-DERIVED at
    execution HEAD by AST, not copied from the plan. The scripts are the ones the guard suite now
    embeds (`tests/test_rununify_main.py::module_level_free_names` / `classify` / `ThePatchSeamPopulation.seams`).

    **(a) THE CLOSURE. 27 module-level free names, and ONE HAS CHANGED CLASS SINCE 2026-09-16.**

    ```
    HEAD closure of oc_runipd.main: 27 module-level free names

    1-shared-same-object                  9  DriverError, EmptyStatusSelection, Palette, json, load_state, render_run_summary_table, resolve_run_dir, should_color, sys
    2-shared-name-host-wrapper            2  print_status, save_state
    3-one-object-agy-imports-from-oc      5  emit_shutdown_report, install_exit_signal_handler, render_runs_pointer, report_run_spec_edits, runner_shared
    4-still-defined-twice                 8  build_parser, handle_stop_command, initialize_run, install_stop_triggers, locked_run, render_continuation_hint, run_queue, write_report
    5-oc-only                             3  ProfileClauseError, extract_profile_clause, print_launch_identity
    TOTAL                                27

    agy main closure size: 24
    ```

    | Class | Plan (2026-09-16) | HEAD (2026-09-17) |
    |---|---|---|
    | shared, same object | 8 | **9** |
    | shared name, host wrapper | 2 | 2 |
    | one object, agy imports from oc | 5 | 5 |
    | **STILL DEFINED TWICE** | 9 | **8** |
    | oc-only | 3 | 3 |

    **THE COUNT STILL DEFINED TWICE IS 8**, stated explicitly as this item demands, down from the
    plan's 9. THE SYMBOL THAT CHANGED CLASS IS `EmptyStatusSelection`, named as E-01 requires:

    ```
    oc.ESS is agy.ESS : True
    oc.ESS is rs.ESS  : True
    mro: ['EmptyStatusSelection', 'DriverError', 'RuntimeError', 'Exception', 'BaseException', 'object']
    module: agent_workflows.runner_shared
    ```

    CAUSE: sibling `i3d6ml`, commit `d26c1061` ("lift the 9 closure-clean shared runner symbols into
    runner_shared"). CONSEQUENCE: the plan's F-7 BLOCKER can no longer fire, because its mechanism
    REQUIRED two distinct sibling classes. Recorded as backlog `18nlx8` and DECISION 12-3dki3o-D2
    rather than by editing F-7, whose measurement was correct when made and was re-verified during
    this execution (see V-03(b)).

    ALSO MEASURED, since F-1's conclusion depends on it and V-01 is where a stale claim would show:

    ```
    oc source lines : 297      agy source lines: 205
    oc AST-normalized : 133    agy AST-normalized: 111
    similarity: 0.8115         differing lines: 46
    ```

    Every headline number in the plan reproduces EXACTLY. Classified by cause: 20 host CAPABILITY,
    9 host LABEL, 17 residual, of which 12 are one two-line style difference repeated twice plus a
    block reordering. So the genuine drift is about 5 lines of 133, and F-1 (not the Concern) is
    right.

    **(b) THE FOUR SOURCE PINS. Every one reproduces; a thin caller satisfies NONE.**

    ```
    tests/test_runner_backlog_close.py:923:                src = inspect.getsource(mod.main)
    tests/test_runner_backlog_close.py:1073:                src = inspect.getsource(mod.main)
    tests/test_runner_backlog_close.py:1089:                src = inspect.getsource(mod.main)
    tests/test_run_flag_surface.py:837:            source = inspect.getsource(_MODULES[runner].main)
    ```

    | # | `path:line` | Requires | Thin caller satisfies it? |
    |---|---|---|---|
    | 1 | `test_runner_backlog_close.py:923` | AST of main's source: the `--json` branch must contain `json.dumps` and NOT `render_runs_pointer`, BOTH hosts | **NO.** A thin caller contains neither string. RE-BASEABLE; behavioral twin now exists (`TheJsonStatusBranch`). |
    | 2 | `test_runner_backlog_close.py:1073` | source contains literal `install_exit_signal_handler()` AND literal `143` | **NO.** Weakest of the four (a comment satisfies it). RE-BASEABLE; twin asserts 143 through real behavior. |
    | 3 | `test_runner_backlog_close.py:1089` | an `except` handler naming `KeyboardInterrupt` whose body contains `emit_shutdown_report` | **NO.** RE-BASEABLE; twin drives a real SIGINT-shaped interrupt. |
    | 4 | `test_run_flag_surface.py:837` | source contains `refuse_frozen_flags_on_resume` and `apply_run_policy_flags_on_resume`, BOTH hosts | **NO.** RE-BASEABLE; twin proves the refusal (exit 2) and the application (state written). |

    **(c) THE PATCH SEAMS. 28 total, of which 26 in the four files F-9 named, matching exactly.**

    ```
    TOTAL: 28  files: 5
    BY SYMBOL:
       run_queue                    7        locked_run                   6
       resolve_run_dir              3        load_state                   3
       build_parser                 3        emit_shutdown_report         2
       install_stop_triggers        2        initialize_run               1
       render_run_summary_table     1
    BY FILE:
       tests/test_interrupt_menu.py             12
       tests/test_run_summary_table.py           8
       tests/test_oc_runipd.py                   4
       tests/test_oc_runipd_cli.py               2
       tests/test_rununify_run_queue_characterization.py  2
    seams in the FOUR files the plan named: 26
    ```

    Per-site listing (28 lines, `path:line` + symbol) is in the lane artifact
    `e01-measurements.txt`; the same scan now runs as an assertion in
    `tests/test_rununify_main.py::ThePatchSeamPopulation`.

    A MEASUREMENT WARNING WORTH RECORDING: a scan matching only the DIRECT spelling
    `patch.object(oc_runipd, ...)` finds just **10** of the 28. The other 18 are INDIRECT
    (`patch.object(module, ...)` / `patch.object(driver, ...)` inside a both-hosts loop). My first
    scan made exactly that error and reported 10; counting both spellings gives F-9's 26. Recorded
    because it is how a scan can return a reassuring number and be wrong.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted green run of the characterization suite against UNMODIFIED code; the list of agy branches it newly covers, named; the five exit codes it pins per host, named; a sabotage of one pinned branch showing the suite FAILS (a characterization test that cannot fail pins nothing); and an explicit confirmation, with the grep result, that it added NO new `inspect.getsource(main)` pin.
  - Observed evidence: **GREEN AGAINST UNMODIFIED PRODUCT CODE.** `git diff agent_workflows/` was
    empty for this run; this plan changes no product code at all.

    ```
    $ python3 -m pytest tests/test_rununify_main_characterization.py -o addopts=""
    collected 26 items
    tests/test_rununify_main_characterization.py ..........................  [100%]
    ============================== 26 passed in 4.58s ==============================
    ```

    **THE FIVE EXIT CODES PINNED PER HOST, named** (class `TheFiveExitCodes`, every test looping
    BOTH hosts through `subTest`):

    | Code | Branch | Test |
    |---|---|---|
    | 0 | a completed command (`start --prepare-only`) | `test_exit_0_a_prepare_only_start_completes` |
    | 0 | the `parser.print_help()` path when no subcommand resolves | `test_exit_0_no_subcommand_prints_help_rather_than_failing` |
    | 2 | a `DriverError` translated to the host-prefixed stderr line | `test_exit_2_an_unresolvable_selector_is_translated_not_raised` |
    | 130 | SIGINT through the `KeyboardInterrupt` funnel | `test_exit_130_sigint_funnels_through_keyboardinterrupt` |
    | 143 | SIGTERM, distinguished ONLY by `"SIGTERM" in str(exc)` | `test_exit_143_sigterm_is_marked_by_the_message_not_a_second_handler` |

    **AGY BRANCHES NEWLY COVERED, named as this item demands.** agy was the under-covered host, so
    each of these is asserted on agy for the first time: its `print_help` return-0 path; its
    `DriverError` translation INCLUDING the `runagy:` prefix (measured as asserted NOWHERE in
    `tests/` before this file); its generic `except Exception` arm printing
    `runagy: unexpected failure:` and RE-RAISING rather than swallowing; its
    `just-terminate-no-cleanup` message variant; its `report` branch writing the file and printing
    the path; its `--json` status suppression AND the plain-status inverse; its resume freeze
    (`--retry-budget` refused) and apply (`--unattended` written to frozen options); its
    `--agy-executable` resume write; and the ABSENCE of oc's profile subsystem asserted as a fact
    (`extract_profile_clause`, `ProfileClauseError`, `print_launch_identity`, `--verify-with`).

    **SABOTAGE, showing the suite CAN fail.** One pinned branch broken (`return 143 if is_sigterm
    else 130` -> `return 130`) in `oc_runipd.main`:

    ```
    SABOTAGE APPLIED: oc main returns 130 for SIGTERM
    >               self.assertEqual(rc, 143, err)
    E               AssertionError: 130 != 143 : Terminated by SIGTERM; durable run state was preserved.
    FAILED tests/test_rununify_main_characterization.py::TheFiveExitCodes::test_exit_143_sigterm_is_marked_by_the_message_not_a_second_handler
    ========================= 1 failed, 25 passed in 4.61s =========================
    ```

    RESTORED and verified byte-identical (`git diff --stat -- agent_workflows/oc_runipd.py` empty),
    then green again at 26 passed.

    **NO NEW `inspect.getsource(main)` PIN, with the grep.** The only hit in the new file is PROSE
    in its module docstring explaining why it adds none:

    ```
    $ grep -rn "getsource" tests/ --include=*.py | grep -iE "\.main|\"main\"|'main'"
    tests/test_runner_backlog_close.py:923:                src = inspect.getsource(mod.main)
    tests/test_runner_backlog_close.py:1073:                src = inspect.getsource(mod.main)
    tests/test_runner_backlog_close.py:1089:                src = inspect.getsource(mod.main)
    tests/test_rununify_main_characterization.py:9:`inspect.getsource(<host>.main)` and assert substrings or AST shapes of its body (inventoried in
    tests/test_run_flag_surface.py:837:            source = inspect.getsource(_MODULES[runner].main)
    ```

    Four real pins, unchanged, and the census is now ASSERTED at exactly four by
    `TheSourcePinsAreStillPresent::test_the_pin_population_is_still_exactly_four`, so a fifth cannot
    be added silently either.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: THREE parts, all pasted. (a) The empty-sweep assertions green on BOTH hosts (exit 0, `Nothing awaiting review`, no run directory created). (b) The STRUCTURAL assertion green: each host's `EmptyStatusSelection` subclasses `runner_shared.DriverError` and is NOT a subclass of the other host's, with the measured `issubclass` results shown. (c) `tests/test_run_flag_surface.py` green with its 89-test baseline.
  - Observed evidence: **(a) THE EMPTY-SWEEP ASSERTIONS, BOTH HOSTS.**

    ```
    $ python3 -m pytest tests/test_rununify_main_characterization.py::TheEmptySweepExitCodeContract -o addopts=""
    ....                                                                     [100%]
    ============================== 4 passed in 0.40s ==============================
    ```

    `test_an_empty_review_sweep_exits_zero_on_both_hosts` asserts all three properties this item
    names, per host: `rc == 0`, `Nothing awaiting review` on stdout, and
    `(repo/".aw"/"records"/"runs").exists()` FALSE, i.e. no run directory created. A companion
    (`test_a_plain_driver_error_still_exits_2_so_the_zero_is_not_blanket`) proves the 0 is not
    blanket: a misspelled selector still exits 2.

    **(b) THE STRUCTURAL ASSERTION, AND A CORRECTION TO WHAT IT CAN ASSERT.** This item asks for
    "each host's `EmptyStatusSelection` subclasses `runner_shared.DriverError` and is NOT a subclass
    of the other host's". THE SECOND HALF IS NO LONGER ASSERTABLE, because there is no longer an
    "other host's" class to compare against: sibling `i3d6ml` (`d26c1061`) lifted the class into
    `runner_shared` and both hosts now resolve the SAME object. Measured:

    ```
    oc.ESS is agy.ESS : True
    oc.ESS is rs.ESS  : True
    issubclass(rs.EmptyStatusSelection, rs.DriverError): True   (and it is NOT DriverError itself)
    ```

    So the structural half was pinned in the form the CURRENT code allows, which is strictly
    stronger for the hazard's purpose: `test_empty_status_selection_is_ONE_shared_class_not_two_per_host`
    fails the moment anyone re-forks the class, and
    `test_the_shared_class_is_still_a_driver_error_subclass` keeps the subclass relation that makes
    the `except` ordering load-bearing.

    **F-7's MECHANISM WAS RE-VERIFIED BY CONSTRUCTION rather than taken on trust.** agy was
    deliberately re-forked to its own sibling class, reproducing the exact shape F-7 described:

    ```
    SABOTAGE APPLIED: agy re-forked EmptyStatusSelection into its own class
    E       AssertionError: <class 'agent_workflows.runner_shared.EmptyStatusSelection'> is not
            <class 'agent_workflows.agy_runipd.EmptyStatusSelection'> : the two hosts'
            EmptyStatusSelection must be the SAME object; two sibling classes let a shared `except`
            arm miss one host and return 2 instead of 0 (F-7)
    FAILED ...::test_empty_status_selection_is_ONE_shared_class_not_two_per_host
    ========================= 1 failed, 3 passed in 0.40s ==========================
    ```

    And the PRODUCTION consequence F-7 predicted, through a shared core written against
    `runner_shared`'s class exactly as a real split would be:

    ```
    agy.ESS is rs.ESS          : False
    issubclass(agy.ESS, rs.ESS): False
      -> Nothing awaiting review
    oc's instance through the shared core : 0
      -> runX: empty
    agy's instance through the shared core: 2
    ```

    Exit 0 for the matching class, exit 2 for the sibling, violating spec `25kzda` 2.4a property 3
    precisely as F-7 said. So F-7 was CORRECT when written and is now DISSOLVED by `i3d6ml`, which
    is why it is recorded as backlog `18nlx8` rather than deleted. Sabotage restored and verified
    byte-identical.

    **(c) `tests/test_run_flag_surface.py` GREEN AT ITS 89-TEST BASELINE, exactly as the plan
    predicted:**

    ```
    $ python3 -m pytest tests/test_run_flag_surface.py -o addopts=""
    tests/test_run_flag_surface.py ......................................... [ 46%]
    ................................................                         [100%]
    ============================== 89 passed in 5.45s ==============================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the written analysis itself, covering all five parts (a) through (e) that E-04 enumerates, with the four pins of F-8 and the 26 seams of F-9 each given a verdict, and the LOST-versus-BROKEN distinction stated for the seams. Plus an explicit statement that NO split was performed and that OQ-03 remains the maintainer's, so the omission cannot be read as an oversight.
  - Observed evidence: THE ANALYSIS IS THE TRACKED RECORD
    `.aw/records/walkthroughs/20260917-mnclosure-01-zogmmg-main-is-an-entry-point-and-the-set-shared-nothing.walkthrough.md`
    (committed at `1f57ae6c`). It is TRACKED rather than a lane note deliberately: the lane
    submission tree is gitignored, the correction sibling `yrqyxb` had to make after the fact.
    Summary of each of the five parts:

    **(a) THE INJECTION SURFACE IS TEN, NOT ELEVEN.** 8 still-double-defined plus 2 host-wrapped,
    because `EmptyStatusSelection` moved (V-01(a)). Of these, the maintainer's `818uru` OQ-02
    wrapper ruling governs EXACTLY TWO, `print_status` and `save_state`, and both are already IN
    that form: `runner_shared` owns the real function taking the host dependency as a parameter and
    each runner keeps a one-line wrapper at the original name and signature. The other eight are
    NOT governed by it, and the analysis states plainly why that matters: injecting a
    still-double-defined symbol DE-DUPLICATES NOTHING, it relocates the call while leaving two
    implementations behind it.

    **(b) THE FOUR PINS, A VERDICT EACH: all four RE-BASEABLE, none satisfiable by a thin caller.**
    Table in V-01(b) and in the walkthrough. Each now has a BEHAVIORAL TWIN added by E-02, which is
    what converts "re-basing these is risky" into the trade the maintainer's 2026-09-16 ruling
    invites (prefer a behavioral assertion where it loses no coverage). The twins do NOT authorize
    deleting the pins: E-06 asserts all four still present and the census fixed at four.

    **(c) THE 26 SEAMS, WITH THE LOST-VERSUS-BROKEN DISTINCTION STATED.** ALL 26 are at risk of
    being LOST, not broken, and the distinction is the finding: a source pin BREAKS (it fails at its
    own assertion, in red, naming itself) while a seam is LOST (the `with patch.object(...)` block
    still runs, nothing raises, the test still PASSES, and what it now exercises is the real
    `run_queue`, the real `locked_run` and the real `initialize_run` against a temp repo). Whether a
    given seam survives depends on a design detail the plan does not specify, and this was verified
    by construction: an import-time-frozen reference returned the real object while a call-time
    reference honored the patch. Practical consequence recorded: all 26 must be converted to patch
    the INJECTED PARAMETER, which is a rewrite of four test files including
    `tests/test_oc_runipd.py:4123`'s `_parse_argv` helper that backs 12 launch-profile assertions.

    **(d) RE-ORDERING AFTER THE SIBLINGS WOULD NOT REDUCE THE TEN, AND THIS IS THE SET-LEVEL
    FINDING.** The question presumes children 04/07/08/09/10 will SHARE their symbols. They
    executed WITHOUT doing so. Measured mechanically at this HEAD rather than read from their prose:

    | Symbol | Child | Status | In `runner_shared`? | oc object is agy object? |
    |---|---|---|---|---|
    | `execute_item` | 07 `yrqyxb` | executed | NO | NO |
    | `run_queue` | 08 `ty3cj6` | executed | NO | NO |
    | `initialize_run` | 09 `orziju` | executed | NO | NO |
    | `build_parser` | 10 `s16omw` | executed | NO | NO |

    So ALL FIVE split children are now executed and NOT ONE shared its symbol; the Set's stated
    objective (one shared code base holding 100% of the redundant code) is NOT met by the Set as
    executed, and the five analyses are the input to a follow-on Set rather than a substitute for
    one. THIS ALSO CORRECTS F-12 in the letter: `ty3cj6` IS executed, so the declared
    `Item-Dependencies: executed:ty3cj6` edge is MET, not dangling; F-12's substance (the dependency
    is insufficient rather than wrong) stands, since `run_queue` is still double-defined. The
    walkthrough recommends the ordering for the follow-on: leaf helpers first, then
    `initialize_run`/`build_parser`, then `run_queue`, then `execute_item`, and `main` LAST, since it
    is the only one of the five that closes over the other four.

    **(e) OC'S `as <profile>` GRAMMAR CANNOT LIVE IN A SHARED CORE.** 20 of the 46 differing lines
    are host CAPABILITY, and the answer is given against this plan's own OQ-01 mechanical test (if a
    boundary requires the shared core to contain an `if host == ...` branch, the boundary is wrong).
    `extract_profile_clause` and `ProfileClauseError` DO NOT EXIST on agy, so this is not two hosts
    doing the same thing differently; it is a subsystem one host has. The only placements are a host
    branch (refused by OQ-01) or a caller-supplied hook (which IS the host hook, i.e. leaving it
    where it is). ADDING it to agy is a FEATURE the parent Set forbids a child from making. The
    analysis concludes that the shareable part of `main` is the ERROR-TRANSLATION TAIL, which needs
    none of the eight double-defined symbols and breaks no patch seam, because all 26 seams sit on
    the parse/route head.

    **NO SPLIT WAS PERFORMED, and OQ-03's status stated precisely rather than left ambiguous.**
    OQ-03 is `resolved` ON DISK: the maintainer answered it on 2026-09-16 with a Set-wide directive
    (100% de-duplication, route (A) the objective). So this plan did NOT withhold the split pending a
    decision that was already made; the phrase "OQ-03 remains the maintainer's" in this V-item's
    required evidence is itself stale, and saying so is more useful than repeating it. The split was
    withheld for two reasons of AUTHORITY and SEQUENCING, both recorded in DECISION 12-3dki3o-D1:
    this plan's own approved scope changes NO product code (stated in four places, and V-04 itself
    demands a statement that no split was performed), and `main` is the child most dependent on the
    other four, so splitting the caller before the callees inverts the dependency order the
    maintainer's own sequencing note asks for. THE OMISSION CANNOT BE READ AS AN OVERSIGHT because
    it is asserted mechanically: `tests/test_rununify_main.py::TheSplitHasNotBeenPerformed` (4
    tests) asserts both hosts still define `main`, the two are not one object, `runner_shared` has
    no `main`, and neither host delegates to its peer, each with the instruction to re-base it in
    the same change as the split.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: `python3 -m pytest tests/test_rununify_main.py -o addopts=""` green, pasted, plus the table the closure assertions are driven from, shown in the test source, plus a demonstration that changing one entry in that table makes the suite FAIL (a classification assertion that cannot fail pins nothing).
  - Observed evidence: **THE SUITE GREEN:**

    ```
    $ python3 -m pytest tests/test_rununify_main.py -o addopts=""
    collected 20 items
    tests/test_rununify_main.py ....................                         [100%]
    ============================== 20 passed in 7.10s ==============================
    ```

    **THE TABLE THE ASSERTIONS ARE DRIVEN FROM**, in the test source as
    `EXPECTED_CLOSURE` (27 entries, one per closure name) plus `CLOSURE_CLASSES` (the five class
    definitions, each with the consequence for a split) and `EXPECTED_CLASS_COUNTS` (the histogram).
    Excerpt showing the shape and the one changed entry:

    ```python
    EXPECTED_CLOSURE = {
        # class 1: resolves in runner_shared, same object (9)
        "DriverError": "shared-same-object",
        "EmptyStatusSelection": "shared-same-object",
        ...
        # class 4: STILL DEFINED TWICE, i.e. the injection cost of a split (8)
        "build_parser": "still-defined-twice",
        ...
        # class 5: oc-only, no agy counterpart (3)
        "print_launch_identity": "oc-only",
    }
    EXPECTED_CLASS_COUNTS = {
        "shared-same-object": 9, "shared-host-wrapper": 2,
        "one-object-agy-imports-oc": 5, "still-defined-twice": 8, "oc-only": 3,
    }
    ```

    NO literal appears in an assertion body: every closure test iterates the table, and membership is
    checked BIDIRECTIONALLY (`test_every_name_is_in_the_table_and_the_table_has_no_extras`) so
    neither a new closure name nor a stale table entry can hide.

    **CHANGING ONE ENTRY MAKES THE SUITE FAIL** (a classification assertion that cannot fail pins
    nothing):

    ```
    table entry falsified: run_queue still-defined-twice -> shared-same-object
    E               - still-defined-twice
    E               + shared-same-object
    E                : run_queue changed closure class; a split's cost is a function of this
                       classification, so the plan that reads it is now stale
    FAILED tests/test_rununify_main.py::TheClosureClassification::test_each_name_is_still_in_its_expected_class
    ========================= 1 failed, 19 passed in 6.89s =========================
    ```

    Restored; suite green again at 20 passed.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: FOUR parts, all pasted. (a) The two inverse assertions green, naming the four pins they check. (b) The BIDIRECTIONAL non-vacuity controls from Required tests item 5, both directions shown failing and then restored. (c) All SEVEN fenced test files green by name, plus `test_no_call_site_was_rewritten` with its 38/36 and 2/2 expectations unchanged. (d) Bare `python3 -m pytest` with no new failure against the baseline taken at execution HEAD, summary pasted, and the one pre-existing `test_the_terminal_rung_still_records_the_item_interrupted` failure either reproduced in the baseline or explained.
  - Observed evidence: **(a) THE TWO INVERSE ASSERTIONS GREEN.**

    ```
    $ python3 -m pytest tests/test_rununify_main.py -o addopts=""
    ============================== 20 passed in 7.10s ==============================
    ```

    `TheSourcePinsAreStillPresent` (4 tests) checks the four pins NAMED in `SOURCE_PINS`:
    `test_runner_backlog_close.py:923` `test_json_output_suppresses_the_pointer`;
    `:1073` `test_the_sigterm_funnel_is_wired_in_both_drivers_main`;
    `:1089` `test_both_drivers_report_from_their_keyboardinterrupt_funnel`; and
    `test_run_flag_surface.py:837` `test_both_runners_refuse_and_apply_on_resume`. For each it
    asserts the file still calls `inspect.getsource(<mod>.main)`, the test still exists by name, and
    the required substrings are still required; plus the census is fixed at exactly FOUR, so a fifth
    cannot be added either. `TheSplitHasNotBeenPerformed` (4 tests) asserts `main` is still defined
    in both runners, the two are not one object, `runner_shared` has no `main`, and neither host
    delegates to its peer.

    **(b) THE BIDIRECTIONAL NON-VACUITY CONTROLS, both directions shown failing then restored.**

    DIRECTION 1, the exit-code contract broken in the direction F-7 names (agy's
    `EmptyStatusSelection` re-forked into its own sibling class), E-03's structural assertion FAILS:

    ```
    SABOTAGE APPLIED: agy re-forked EmptyStatusSelection into its own class
    E       AssertionError: <class 'agent_workflows.runner_shared.EmptyStatusSelection'> is not
            <class 'agent_workflows.agy_runipd.EmptyStatusSelection'>
    FAILED ...TheEmptySweepExitCodeContract::test_empty_status_selection_is_ONE_shared_class_not_two_per_host
    ========================= 1 failed, 3 passed in 0.40s ==========================
    ```

    NOTE ON FORM: this item's text says to break it "by making one host's `EmptyStatusSelection`
    inherit from the other's". That phrasing presumes two per-host classes, which no longer exist
    (V-03(b)). The control was therefore run in the shape that reproduces the SAME hazard against
    current code, a re-fork, and it also reproduced the production consequence (exit 0 for the
    matching class, exit 2 for the sibling; pasted in V-03(b)).

    DIRECTION 2, one of the four F-8 source pins DELETED, E-06's inverse assertions FAIL:

    ```
    DELETED pin: test_the_sigterm_funnel_is_wired_in_both_drivers_main
    FAILED tests/test_rununify_main.py::TheSourcePinsAreStillPresent::test_the_pin_population_is_still_exactly_four
    FAILED tests/test_rununify_main.py::TheSourcePinsAreStillPresent::test_each_pin_test_still_exists_by_name
    ========================= 2 failed, 18 passed in 7.29s =========================
    ```

    TWO guards catch it, not one. Both sabotages restored and verified byte-identical to HEAD
    (`git status --porcelain` showed only my own new files afterwards).

    **(c) THE SEVEN FENCED FILES, each green by name.**

    ```
    tests/test_runner_backlog_close.py   47 passed in 5.31s
    tests/test_run_flag_surface.py       89 passed in 8.61s
    tests/test_oc_runipd.py             185 passed in 51.33s
    tests/test_oc_runipd_cli.py          18 passed in 1.52s
    tests/test_interrupt_menu.py         15 passed in 0.37s
    tests/test_run_summary_table.py      10 passed in 0.37s
    tests/test_runner_stop_triggers.py    1 failed, 54 passed in 18.57s
    ```

    SIX of seven fully green. The seventh's single failure is the PRE-EXISTING
    `test_the_terminal_rung_still_records_the_item_interrupted`, addressed in (d). ALL SEVEN were
    left UNTOUCHED by this plan, as its scope check predicted, so each needs a `--scope-ack` at
    finalize rather than a `--scope-reason`.

    `test_no_call_site_was_rewritten` GREEN:

    ```
    $ python3 -m pytest "tests/test_runner_shared.py::WrapperTests::test_no_call_site_was_rewritten" -o addopts=""
    tests/test_runner_shared.py .                                            [100%]
    ============================== 1 passed in 1.09s ===============================
    ```

    THE `38/36` FIGURE THIS ITEM CITES IS STALE, and reporting that is more honest than transcribing
    it. The test holds NO such literal: a `PREMOVE_CALL_SITES` baseline of 32/30 plus five
    separately-named addition tables. Summed at this HEAD:

    ```
    ('oc_runipd', 'save_state'): 45      ('oc_runipd', 'print_status'): 2
    ('agy_runipd', 'save_state'): 43     ('agy_runipd', 'print_status'): 2
    ```

    So `print_status` is 2/2 EXACTLY as the item says, and `save_state` has moved to 45/43 because
    later plans added callers and NAMED each one, which is what that table's own rule requires. The
    numbers were NOT edited: the table's documented rule forbids fixing a moved count by editing a
    literal, and doing so would be the silent weakening the maintainer's 2026-09-16 ruling
    prohibits. The claim BEHIND this item is that this plan rewrote no call site, and that is proven
    directly and more strongly: `git diff agent_workflows/` is EMPTY for this execution. Filed as
    backlog `yfbzqn`; see DECISION 12-3dki3o-D3.

    **(d) BARE `python3 -m pytest`, NO NEW FAILURE AGAINST THE BASELINE TAKEN AT EXECUTION HEAD.**

    BASELINE at `761edad3` BEFORE any change:

    ```
    7715 passed, 3 skipped, 2 xfailed in 104.30s (0:01:44)
    ```

    AFTER my changes:

    ```
    7761 passed, 3 skipped, 2 xfailed in 109.21s (0:01:49)
    ```

    Zero failures both before and after; +46 passed, exactly the count of the two new files.

    TWO HONEST NOTES, because a bare-green report would otherwise be misleading.

    FIRST, `test_the_terminal_rung_still_records_the_item_interrupted` does NOT appear in either bare
    run, and the plan's Required tests item 8 expected it to fail. Both are true: the class carries
    `@pytest.mark.slow` (`tests/test_runner_stop_triggers.py:785`) and `addopts` supplies
    `-m 'not slow'`, so a BARE run DESELECTS it. Selected by node id it fails deterministically, 3 of
    3:

    ```
    E       AssertionError: 'running' != 'interrupted'
    E        : the interrupted item must be recorded `interrupted`, got {... 'status': 'running'}
    FAILED tests/test_runner_stop_triggers.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted
    ```

    NOT ATTRIBUTABLE TO THIS PLAN, shown three ways: it still fails with my two new files moved
    aside, with `AW_EXECUTION_ROLE` unset, and with `AW_PIN_KEEP_ROOT` unset; and this plan changes
    no product code. It exercises `main`'s exit-130 path, so it is squarely in this symbol's
    territory and is filed as backlog `pe7g6r` (high) WITH the invisibility mechanism, which is the
    more valuable half: the contract is broken right now and the mandated bare run cannot see it.

    SECOND, an INTERMEDIATE bare run showed one failure that the rerun did not:
    `test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`,
    a `subprocess.TimeoutExpired` after 30s rather than an assertion failure. It is load-related
    flakiness under `-n auto`, not a regression: it passes 3 of 3 in isolation, it appeared in a
    PRE-CHANGE baseline run as well, and the clean rerun above is fully green. Reported rather than
    quietly discarded.
  - Result: pass

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
