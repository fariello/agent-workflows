# Walkthrough: `main` is an entry point, and the Set shared nothing (`rununify` Order 11, `3dki3o`)

- Date: 2026-09-17
- Id: zogmmg
- Target-Id: 3dki3o
- Plan: `.aw/records/plans/pending/20260915-rununify-11-3dki3o-split-main-into-a-shared-core-and-a-thin-host-hook.ipd.md`
- Base commit: `761edad3`
- Executed by: opencode/its_direct-pt3-claude-opus-5-1m-us, in lane `aw/lane/3dki3o`
- Set: mnclosure (this walkthrough's own Set; the plan it documents belongs to `rununify`, referenced above by `Target-Id`, because a walkthrough may not reuse the Set id of another artifact type)

## What this plan did, and what it did not

Plan `3dki3o` is named "split `main` into a shared core and a thin host hook". It did NOT perform that
split. As re-scoped at its own 2026-09-16 review it is a measure-pin-and-guard plan: E-01 measures
three populations, E-02 characterizes both hosts' behavior, E-03 pins the exit-code contract, E-04
delivers this analysis, and E-05/E-06 guard what was measured in both directions. All six were
performed.

This document is E-04's deliverable. It is a TRACKED record rather than a lane note, deliberately: the
lane submission tree is gitignored, which is a correction sibling `yrqyxb` had to make after the fact.

THE HEADLINE, stated first because it is the most useful sentence in this file and it is a Set-level
fact rather than a plan-level one:

> All five of the `rununify` split children (`yrqyxb` execute_item, `ty3cj6` run_queue, `orziju`
> initialize_run, `s16omw` build_parser, and this one) are now executed, and NOT ONE of them shared its
> symbol. Measured at this HEAD, none of `execute_item`, `run_queue`, `initialize_run`, `build_parser`
> or `main` exists in `runner_shared`, and for each the oc object and the agy object are still
> distinct. The Set's stated objective ("one code base shared by the two runners that contains 100% of
> the otherwise redundant code") is therefore NOT met by the Set as executed.

That is not a defect in any one child. Each was re-scoped to analysis at its own review, each executed
its re-scope faithfully, and each produced a measurement the eventual split needs. But a reader
scanning five `executed` plans would reasonably conclude the de-duplication happened, and it did not.
The five analyses are the input to a follow-on Set, not a substitute for it.

## (a) The eleven dependencies a shared core would take, and which the wrapper ruling governs

The plan's E-04(a) asks for "the eleven dependencies a shared core would have to take (the 9
double-defined plus the 2 host-wrapped)". RE-MEASURED AT THIS HEAD IT IS TEN, NOT ELEVEN, and the
reason is a genuine improvement rather than a counting difference.

`main` closes over 27 module-level names. The classification, re-derived by AST at HEAD `761edad3`:

| Closure class | Plan (2026-09-16) | HEAD (2026-09-17) | Members at HEAD |
|---|---|---|---|
| Resolves in `runner_shared`, SAME object | 8 | **9** | `DriverError`, `EmptyStatusSelection`, `Palette`, `json`, `load_state`, `render_run_summary_table`, `resolve_run_dir`, `should_color`, `sys` |
| Shared NAME, per-host wrapper object | 2 | 2 | `print_status`, `save_state` |
| One object, agy imports it from oc | 5 | 5 | `emit_shutdown_report`, `install_exit_signal_handler`, `render_runs_pointer`, `report_run_spec_edits`, `runner_shared` |
| STILL DEFINED TWICE | 9 | **8** | `build_parser`, `handle_stop_command`, `initialize_run`, `install_stop_triggers`, `locked_run`, `render_continuation_hint`, `run_queue`, `write_report` |
| oc-ONLY | 3 | 3 | `ProfileClauseError`, `extract_profile_clause`, `print_launch_identity` |
| **total** | 27 | **27** | |

THE ONE CLASS CHANGE: `EmptyStatusSelection` moved from STILL-DEFINED-TWICE to shared, because sibling
`i3d6ml` (commit `d26c1061`) lifted it into `runner_shared`. So the injection surface is 8 + 2 = **10**,
down from 11.

WHICH ARE GOVERNED BY THE `818uru` OQ-02 WRAPPER RULING: the two host-wrapped names, `print_status` and
`save_state`, exactly. That ruling establishes the form to use, and it is already in force for both:
`runner_shared` owns the real function taking the host dependency as an explicit parameter
(`print_status(run_dir, driver_label=...)`, `save_state(..., write_report=...)`) and each runner keeps a
one-line wrapper at the original name and signature. A shared `main` core would take these two as
parameters and each host's hook would pass its own wrapper, which is the sanctioned shape rather than a
violation of it.

The other eight are NOT governed by that ruling, and this is the part worth being precise about:
injecting a still-double-defined symbol DE-DUPLICATES NOTHING. It relocates the call while leaving two
implementations. A shared core taking `run_queue` as a parameter is a shared core that still has two
`run_queue`s behind it. That is why the sequencing below matters more than the mechanism.

## (b) The four source pins, with a verdict each

All four reproduce at this HEAD. Every one FAILS the moment `main`'s body moves, LOUDLY, at its own
assertion. Verdict for each: RE-BASEABLE, and the maintainer's 2026-09-16 ruling says how (re-base
deliberately onto the shared implementation, record what it now asserts, prove it still catches the
regression it was installed for; never weaken silently).

| # | Site | Test | Requires | Verdict |
|---|---|---|---|---|
| 1 | `tests/test_runner_backlog_close.py:923` | `test_json_output_suppresses_the_pointer` | walks the AST of `main`'s source for the `--json` branch; that branch must contain `json.dumps` and must NOT contain `render_runs_pointer`, on BOTH hosts | A thin caller contains neither. RE-BASE onto the shared core, and prefer the behavioral twin: this execution added `TheJsonStatusBranch`, which asserts the same contract as parseable OUTPUT, which a comment cannot satisfy. |
| 2 | `tests/test_runner_backlog_close.py:1073` | `test_the_sigterm_funnel_is_wired_in_both_drivers_main` | `main`'s source contains the literal `install_exit_signal_handler()` AND the literal `143` | The literal `143` is the weakest of the four (a comment satisfies it). Behavioral twin added: `test_exit_143_sigterm_is_marked_by_the_message_not_a_second_handler`, which drives a real SIGTERM-shaped interrupt and requires 143. |
| 3 | `tests/test_runner_backlog_close.py:1089` | `test_both_drivers_report_from_their_keyboardinterrupt_funnel` | an `except` handler naming `KeyboardInterrupt` whose body contains `emit_shutdown_report` | RE-BASE. Behavioral twin added: `test_exit_130_sigint_funnels_through_keyboardinterrupt`. |
| 4 | `tests/test_run_flag_surface.py:837` | `test_both_runners_refuse_and_apply_on_resume` | `main`'s source contains `refuse_frozen_flags_on_resume` and `apply_run_policy_flags_on_resume`, on BOTH hosts | RE-BASE. Behavioral twin added: `TheResumeFreezeContract`, which proves the refusal (exit 2) and the application (state actually written). |

WHY THE TWINS MATTER MORE THAN THE PINS. Each pin now has a behavioral counterpart asserting the same
property through observable output. That is what converts "re-basing these pins is risky" into "these
pins can be re-based, or replaced, without losing coverage", which is the trade the maintainer's ruling
explicitly invites. THE TWINS DO NOT AUTHORIZE DELETING THE PINS: `tests/test_rununify_main.py`
asserts all four are still present, and the pin census is asserted to be exactly four, so a fifth
cannot be added either (E-02 was forbidden from adding one, and did not).

## (c) The 26 patch seams, and which are LOST rather than merely BROKEN

Measured at this HEAD by AST across the whole test tree: **28** seams patch a name `main` resolves at
module level, of which **26** fall in the four files plan F-9 named. The plan's number reproduces
exactly.

| File | Seams | Symbols |
|---|---|---|
| `tests/test_interrupt_menu.py` | 12 | `run_queue`, `emit_shutdown_report`, `resolve_run_dir`, `load_state`, `locked_run`, `install_stop_triggers` (x2 hosts) |
| `tests/test_run_summary_table.py` | 8 | `run_queue` (4), `locked_run` (4) |
| `tests/test_oc_runipd.py` | 4 | `build_parser` (2), `initialize_run`, `resolve_run_dir` |
| `tests/test_oc_runipd_cli.py` | 2 | `run_queue`, `build_parser` |
| **subtotal (the four F-9 files)** | **26** | |
| `tests/test_rununify_run_queue_characterization.py` | 2 | `load_state`, `render_run_summary_table` |
| **total** | **28** | |

A MEASUREMENT WARNING WORTH RECORDING, because it nearly produced a wrong answer here. A scan that
matches only the DIRECT spelling `patch.object(oc_runipd, ...)` finds just 10 of the 28. The other 18
are INDIRECT: `patch.object(module, ...)` or `patch.object(driver, ...)` inside a both-hosts loop, where
the target is a variable holding the host module. Counting only the direct form undercounts by nearly
two thirds, and would have reported a reassuring 10 where the real exposure is 26. The scanner in
`tests/test_rununify_main.py::ThePatchSeamPopulation` counts both spellings for this reason.

LOST VERSUS BROKEN, which is the distinction E-04(c) demands and the most important paragraph here:

- A source pin BREAKS. It fails at its own assertion, in red, naming itself. You cannot miss it.
- A patch seam is LOST. A function living in `runner_shared` resolves its own module globals, so
  patching the HOST module has no effect on it. The `with patch.object(...)` block still executes, the
  mock is still installed, nothing raises, and the test still passes. What it now exercises is the
  REAL `run_queue`, the REAL `locked_run` and the REAL `initialize_run` against a temp repo.

ALL 26 ARE AT RISK OF BEING LOST, not broken. That is the whole finding. Whether a given seam survives
depends on a design detail the plan does not specify: a shared core that captures its dependency at
IMPORT time (a frozen default, a module-level descriptor) never sees the patch; one that reads it at
CALL time through an injected parameter does see it, provided the host hook passes the name rather
than a pre-bound object. Verified by construction during this execution: an import-time-frozen
reference returned the real object while a call-time reference honored the patch.

THE PRACTICAL CONSEQUENCE FOR WHOEVER SPLITS THIS. The 26 seams must be converted to patch the
INJECTED PARAMETER rather than the module name, and that conversion is a rewrite of four test files,
including `tests/test_oc_runipd.py:4123`'s `_parse_argv` helper, which patches `build_parser`,
`initialize_run` and `resolve_run_dir` to stop before side effects and which backs 12 launch-profile
grammar assertions. A split that skips this step will produce a GREEN suite that asserts materially
less than it claims, and no amount of characterization coverage detects that: the tests still pass.

## (d) Would re-ordering after siblings 04/07/08/09/10 reduce the ten? NO, and this is the finding

E-04(d) asks whether running this plan after its siblings would shrink the injection count, noting that
`run_queue` (child 08), `initialize_run` (child 09), `build_parser` (child 10) and
`render_continuation_hint`/`write_report` (child 04) are five of the double-defined names.

THE ANSWER IS NO, AND THE REASON IS DECISIVE. The question presumes those siblings will SHARE their
symbols. They executed without doing so. Measured at this HEAD:

| Symbol | Owning child | Child status | In `runner_shared`? | oc object is agy object? |
|---|---|---|---|---|
| `execute_item` | 07 `yrqyxb` | executed | NO | NO |
| `run_queue` | 08 `ty3cj6` | executed | NO | NO |
| `initialize_run` | 09 `orziju` | executed | NO | NO |
| `build_parser` | 10 `s16omw` | executed | NO | NO |

So re-ordering buys nothing: the plans ahead of this one have already run, and the symbols they own are
still double-defined. Three corrections to the plan's own text follow from this.

FIRST, the plan's F-12 says its declared edge `executed:ty3cj6` "points at a plan that cannot currently
execute". That is now WRONG in the letter and RIGHT in the spirit: `ty3cj6` IS executed, so the
dependency is MET, but because it executed as analysis-only, `run_queue` is still one of this plan's
injections. F-12's real point (the dependency is insufficient rather than wrong) stands.

SECOND, route (B) as the plan framed it ("re-order this plan LAST", noting it already IS Order 11) is
moot. What route (B) was really asking (can the siblings ahead be unblocked first) has been answered:
they were unblocked, they ran, and they chose not to split.

THIRD, and this is the recommendation: THE REMAINING WORK IS A FOLLOW-ON SET, not a re-run of these
five. It should be ordered by the dependency graph the five analyses now make explicit, callees before
callers, with `main` LAST because it is the only one of the five that closes over the other four. A
sensible ordering, from the closure data: the leaf helpers (`locked_run`, `render_continuation_hint`,
`write_report`, `install_stop_triggers`, `handle_stop_command`) first, then `initialize_run` and
`build_parser`, then `run_queue`, then `execute_item`, and `main` only once its injection surface has
fallen to the two ruled wrappers. Do not re-order plans by hand; declare `Item-Dependencies` and let
the runner sort by dependency depth.

## (e) Can oc's `as <profile>` grammar live in a shared core at all? NO

19 to 20 of the 46 differing AST-normalized lines are oc's launch-profile grammar, and agy has no
profile subsystem. Classified by cause at this HEAD, the 46 differing lines are:

| Class | Lines | What they are |
|---|---|---|
| host CAPABILITY | 20 | oc's `as <profile>` clause extraction and its refusal, the `--verify-with`/`--validate`/`--variant` resume handling, `print_launch_identity`; against agy's `--agy-executable` |
| host LABEL | 9 | `runipd:`/`runagy:` prefixes, `driver_label="opencode"`/`"antigravity"` |
| residual | 17 | of which 12 are ONE two-line style difference repeated twice (`print(render_continuation_hint(...))` versus `hint = ...; print(hint)`) plus a block-ordering difference (`stall_timeout` and `max_items_per_session` swapped) that changes nothing |

So the genuine drift is about **5 lines out of 133**. THE PLAN'S OWN CONCERN IS BACKWARDS AND ITS F-1
IS RIGHT: "most of the divergence is DRIFT in shared logic" is the boilerplate sentence shared with the
four sibling children, and for this symbol it is false. `main` is the most CAPABILITY-divergent of the
five, not the least. An executor trusting the Concern would hunt for drift to reconcile and would
instead find oc's entire launch-profile grammar.

THE ANSWER TO (e), stated mechanically rather than aesthetically, using this plan's own OQ-01 test (if
a candidate boundary requires the shared core to contain an `if host == ...` branch, the boundary is
wrong): the profile grammar CANNOT live in a shared core. It is not a difference in how the two hosts
do the same thing; it is a subsystem one host has and the other does not, and `extract_profile_clause`
and `ProfileClauseError` do not exist on agy at all. The only ways to place it in shared code are a host
branch (refused by OQ-01) or a caller-supplied hook (which is the host hook, i.e. leaving it where it
is). ADDING the grammar to agy is a FEATURE, and the parent Set forbids a child changing what a runner
does; the plan already defers agy's three missing resume capabilities for exactly this reason.

WHAT THIS MEANS FOR THE SHAPE OF AN EVENTUAL SPLIT. The shareable part of `main` is the ERROR-TRANSLATION
TAIL: the four `except` arms, in order, with the host prefix carried as a descriptor field. That is
where the two copies have genuinely drifted, it needs none of the eight double-defined symbols, and it
breaks no patch seam, because all 26 seams are on the parse/route head. The head itself is what an
entry point is for: binding one host's CLI to one host's behavior. A future Set can share the tail and
should say out loud that the head stayed per-host, with the measurement above as the reason.

## NO SPLIT WAS PERFORMED, and OQ-03's status stated precisely

OQ-03 is `resolved` ON DISK. The maintainer answered it on 2026-09-16 with a Set-wide directive (100%
de-duplication, route (A) as the objective, route (B)'s ordering permitted as a tactic). So this plan
did NOT withhold the split pending a decision that was already made. It withheld it for reasons of
AUTHORITY and SEQUENCING rather than difficulty:

1. THIS PLAN'S OWN APPROVED SCOPE. Its review re-scoped it to change NO product code, in four separate
   places (`Scope`, the SCOPE GATE above E-01, E-04's text, and `Scope check`), and its V-04 explicitly
   requires "an explicit statement that NO split was performed". Performing the relocation would
   exceed the scope the plan was approved with.
2. THE DEPENDENCY ORDER. `main` closes over eight still-double-defined symbols owned by sibling plans
   that have already executed WITHOUT sharing them. Splitting the caller before the callees inverts
   the order the maintainer's own sequencing note asks for, and would make this the only child of five
   to relocate its symbol, while being the child most dependent on the other four.

THE OMISSION CANNOT BE READ AS AN OVERSIGHT, because it is asserted mechanically:
`tests/test_rununify_main.py::TheSplitHasNotBeenPerformed` (4 tests) asserts both hosts still define
`main` themselves, the two are not the same object, `runner_shared` has no `main`, and neither host
delegates to its peer. Each carries the instruction to re-base it, in the same change, when the split
lands.

WHAT REMAINS FOR THE MAINTAINER is the Set-level sequencing judgment in part (d), not a route decision.
The route is settled; what is unsettled is that the Set which was supposed to achieve it produced five
analyses and zero de-duplication.

## Defects found during this execution

Three, each filed as a backlog item so it has a durable carrier rather than living in this prose:

- `pe7g6r` (bug, high): `test_the_terminal_rung_still_records_the_item_interrupted` fails
  deterministically (3 of 3) when selected, leaving an interrupted item `running` instead of
  `interrupted`, i.e. `main`'s exit-130 item bookkeeping is not preserved at the terminal rung. It is
  INVISIBLE to a bare `python3 -m pytest` because the class is `@pytest.mark.slow` and `addopts`
  supplies `-m 'not slow'`, so the bare suite is 7715 passed / 0 failed while this contract is broken.
- `yfbzqn` (chore, low): this plan's V-06(c) requires `test_no_call_site_was_rewritten` to expect
  "38/36" `save_state` call sites; the tables sum to 45/43 at this HEAD, because later plans added
  callers and named each one as the table's rule requires. The transcribed total is the defect.
- `18nlx8` (followup, medium): this plan's Goal table and its F-7 BLOCKER are stale, since `i3d6ml`
  lifted `EmptyStatusSelection` into `runner_shared`. F-7's mechanism was re-verified by deliberately
  re-forking the class (exit 0 for the matching class, exit 2 for the sibling, exactly as predicted)
  and then restored, so the finding was CORRECT when made and is now dissolved.

## What was landed

| File | What |
|---|---|
| `tests/test_rununify_main_characterization.py` | E-02 + E-03. 26 tests, behavior only, no source pin. Five exit codes per host, the implicit-start shim including the `stop` non-rewrite, the four `except` arms proven reachable and ORDERED by behavior, the `--json` suppression and its inverse, the report branch, the resume freeze/apply contract, oc's profile grammar and agy's absence of it, agy's `--agy-executable`, and E-03's empty-sweep contract with its structural half. |
| `tests/test_rununify_main.py` | E-05 + E-06. 20 tests. The 27-name closure classified from a NAMED TABLE with a bidirectional membership check and a histogram; the measured line counts and the 0.8115 similarity; the four source pins asserted still present with a census fixed at four; `main` asserted still per-host; and the 26 patch seams counted per file. |

Both suites were shown to FAIL when the thing they guard is broken, in both directions: a sabotaged
`143`-to-`130` return makes the characterization suite fail; a falsified table entry makes the closure
suite fail; a deleted source pin makes two E-06 guards fail; and a re-forked `EmptyStatusSelection`
makes E-03's structural assertion fail. Every sabotage was restored and verified byte-identical to
HEAD.
