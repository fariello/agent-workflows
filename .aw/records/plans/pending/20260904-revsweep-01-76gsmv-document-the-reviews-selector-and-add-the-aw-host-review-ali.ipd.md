# IPD: document the reviews selector and add the aw <host> review alias

- Date: 2026-09-04
- Kind: child
- Concern: The review sweep is the driver's most frequent invocation and it is INVISIBLE. `aw oc runipd reviews` has worked since the selector was added, routing every `to-review` plan through `/plan-review` in one shared session, and NOTHING advertises it: the `selectors` help on both hosts names only "id6, setid, plan filenames/paths" (oc `oc_runipd.py:5990`) and "ID6, Set ID, IPD filename, or 'all'" (`agy_runipd.py:3938`), neither EXAMPLES block shows the bare sweep, and agy's SELECTOR TYPES block documents `all` while omitting `reviews` entirely (`agy_runipd.py:3914-3917`). The measured consequence is a maintainer asking for a command that already exists. Worse than invisible, the spelling is a trap: `reviews` is a magic BAREWORD occupying the same positional slot as the `start|resume|status|report|stop` subcommands, so the operator must know both that the word exists and that it is not a subcommand. Spec `25kzda` 2.1 (amended 2026-09-04) resolves both halves: it specifies `aw <host> review [<selector>]` as a THIN ALIAS of `run --action review`, and its new Section 2.4a promotes `reviews` from bareword to specified status selector.
- Scope: Make the existing review sweep DISCOVERABLE and give it the spelled surface spec 2.1 declares. Two deliverables: (1) document the `reviews` selector in both hosts' selector help, SELECTOR TYPES prose, and EXAMPLES; (2) register `aw <host> review [<selector>]` as a thin alias that expands to the canonical run invocation. Adds NO selection logic, NO new action, and NO policy: `determine_action` already routes `to-review` to review, and the alias must produce an invocation indistinguishable from the canonical one. EXCLUDES fixing the sweep's draft asymmetry and extracting the duplicated predicate (`6ypimw` owns both), excludes `--allow-drafts` and every other spec 2.1 flag (`uyeko5` owns the flag surface), excludes `--action` itself, and excludes any change to what the sweep SELECTS.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: none
- Status: to-review
- Set: revsweep
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 76gsmv
- Blocks-Release: next
- From-Spec: 25kzda

## Workflow history

- 2026-09-04 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored with the `revsweep` Set after the maintainer asked for a command to review everything needing review, and research found the capability already shipped and merely undocumented. THIS PLAN IS THE DISCOVERABILITY HALF ONLY, deliberately separated from the three substantive gaps (`6ypimw` the shared predicate and draft gate, `eyh1fu` the artifact-neutral record, `5slbpi` spec review) so that a documentation-and-alias change carrying no behavior risk is not held hostage to the record migration. MEASURED AT `3d4e5414`: `reviews`/`review`/`to-review` are accepted at `oc_runipd.py:2244-2246` and `agy_runipd.py:1339-1341`; the oc `selectors` help at `:5990` omits them, agy's at `:3938` omits them while naming `all`, agy's SELECTOR TYPES prose at `:3914-3917` documents `all` and omits `reviews`, and oc's EXAMPLES block at `:5960-5976` shows only the session-scoped `runipd ipdrunner --session <id>` form, never the bare sweep. ONE RULING RECORDED RATHER THAN RE-LITIGATED: the alias must be a THIN ALIAS, never a second action, because `determine_action` (`oc_runipd.py:2409`) derives the action from STATUS and cannot review an item that is not reviewable, so a sibling verb would imply a capability the driver does not have. Spec 2.1 was amended to say exactly that, including the rule that an operator-visible difference between the two spellings is a DEFECT in the alias. ALSO MEASURED, and the reason E-04 exists: `command_surface.COMMAND_INVENTORY` contains NO `oc`/`agy` entries at all, so `tests/test_command_surface_declarations.py` is ALREADY RED with 63 undeclared leaves at HEAD; this plan declares its own leaf and must NOT be read as fixing that backlog.

## Goal

Make the review sweep findable and give it the spelling spec `25kzda` 2.1 declares, so an operator who wants to review everything awaiting review can discover the capability from `--help` and invoke it without knowing a magic bareword.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the existing selector visible

- [ ] E-01 Document the `reviews` selector everywhere a host's help enumerates selectors, on BOTH hosts. Four sites measured, and missing any one leaves the help self-contradictory: oc's `selectors` help string (`oc_runipd.py:5990`), oc's EXAMPLES epilog (`:5960-5976`), agy's `selectors` help string (`agy_runipd.py:3938`), and agy's SELECTOR TYPES prose block (`:3914-3917`, which documents `all` and omits `reviews`).
  State the three accepted spellings (`reviews`, `review`, `to-review`), state that it selects items whose next legal action is review, and state the TYPE SCOPING spec 2.4a fixes: IPDs only, because that is what the runner can discover today. Do NOT document it as spanning specs; `5slbpi` makes that true and until then the help would be a false claim.
  Add ONE example per host showing the bare sweep (`runipd reviews`), which is the invocation the maintainer could not find.
  - Depends on: none
  - Expected outcome: all four sites name the selector; `--help` on both hosts shows the sweep; no site claims cross-type coverage that does not exist yet.
  - Execution state: pending

### Task group 2: give it the spelled surface spec 2.1 declares

- [ ] E-02 Register `aw <host> review [<selector>]` as a THIN ALIAS, on both hosts, expanding to exactly `run <selector> --action review` and, with the selector omitted, to exactly `run reviews --action review`.
  THE ALIAS MUST CARRY NO LOGIC OF ITS OWN. Implement it as an argv rewrite ahead of the existing parser, in the same place `oc_runipd.py:6267-6285` already rewrites an implicit `start`, rather than as a second parser with its own flags: a duplicate parser is how the two hosts' flag surfaces diverged in the first place (measured by `uyeko5` F-5), and spec 2.1 states plainly that an operator-visible difference between `aw <host> review X` and `aw <host> run X --action review` is a DEFECT in the alias.
  MIND THE ORDER OF THE TWO REWRITES: the implicit-`start` shim and this alias both edit argv, and `review` must resolve to `start ... --action review`, so composing them in the wrong order yields `review start` or a lost flag. Add a test for the composition, not just for the alias alone.
  NOTE `--action` DOES NOT EXIST YET on either runner (it greps to zero; `uyeko5` records it as one of spec 2.1's unbuilt entries and explicitly excludes it). So the rewrite's TARGET is unavailable, and E-03 resolves that rather than this item inventing the flag.
  - Depends on: E-01
  - Expected outcome: `aw oc review` and `aw agy review` both run the sweep; both accept an explicit selector; the alias is an argv rewrite with no parser of its own; the composition with the implicit-`start` shim is tested.
  - Execution state: pending

- [ ] E-03 Resolve the `--action` dependency HONESTLY, and record which way you resolved it. Spec 2.1 defines `aw <host> review` as `run --action review`, and `--action` is unbuilt on both hosts.
  TWO ACCEPTABLE RESOLUTIONS, and the choice belongs to whoever executes this against the tree they find. (a) If `uyeko5` has landed and registered `--action`, the alias rewrites to it and this item is pure wiring. (b) If it has not, register `--action <review|plan|execute>` MINIMALLY here: accept the flag, honor `review` by the routing that already exists (`determine_action` gives `to-review` and complete `draft` a review action), and REFUSE `plan` and `execute` as not yet implemented rather than silently accepting them. Do NOT implement `--action`'s full legality rules (spec 2.6: `plan` legal only for an approved spec or open backlog item, `execute` only for approved/auto-approved/reusable IPDs); those need the per-type dispatch this Set has not built.
  A THIRD OPTION IS FORBIDDEN: do not make the alias a bespoke code path that bypasses `--action` entirely. That would be the second action this plan exists to avoid, and it would make the alias's behavior a separate thing to maintain.
  - Depends on: E-02
  - Expected outcome: `--action review` exists and is what the alias uses; `plan`/`execute` refuse honestly if registered here; which resolution applied is stated; no bespoke alias-only code path exists.
  - Execution state: pending

- [ ] E-04 Declare the new leaf in `command_surface.COMMAND_INVENTORY` and register the alias in the same declaration shape the surface already uses for an alias (`canonical_command` pointing at the canonical leaf).
  STATE THE PRE-EXISTING FAILURE HONESTLY: `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` is ALREADY RED at HEAD with 63 undeclared leaves, none of them `oc`/`agy` (the inventory contains no host-runner entries at all). Both that test and `tests/test_cli_conformance_matrix.py` are `pytest.mark.slow`, so a bare `python3 -m pytest` SKIPS them and a green bare suite proves nothing here. Run them explicitly.
  So the bar for this item is NO-WORSENING plus one new declaration, not a green test. Do NOT declare the other 62 leaves to make the test pass: that is a separate sweep with its own review, and folding it in would hide this plan's own change inside a 63-entry diff.
  - Depends on: E-03
  - Expected outcome: the new leaf and its alias are declared; the undeclared-leaves count does not grow; the pre-existing red state is reported as pre-existing, with the explicit slow-test invocation shown.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE IMPLICIT-`start` SHIM IS THE PRECEDENT for argv rewriting on these runners (`oc_runipd.py:6267-6285`). It exists because `runipd` deliberately declares ZERO flags in `cli.py` (rationale comment at `cli.py:3174-3179`): re-declaring them there would drift from the driver's real parser and bypass the shim. An alias implemented in `cli.py` with its own flags would violate that reasoning; an argv rewrite honors it.
- `aw oc runipd` reaches its driver through `cli.py:9496-9503` forwarding `argparse.REMAINDER` verbatim, so the driver's own `build_parser` is the only place a selector or flag is really declared. Documentation must go there, not into `cli.py`'s help.
- BOTH RUNNERS ARE THE HIGHEST-CONTENTION FILES IN THE REPO (`uyeko5` F-8 measured 11 unexecuted plans declaring them). This plan touches only help strings and one argv rewrite per host, deliberately, so it can land without waiting on the `rununify` consolidation.
- A REVIEW TURN'S PROMPT IS LITERALLY `/plan-review <relpath>` AND NOTHING ELSE (`oc_runipd.py:3540-3562`, with a docstring warning never to append prose because the slash command absorbs extra text into `$ARGUMENTS`). Nothing in this plan may add prose to that prompt.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | THE SWEEP ALREADY WORKS AND IS UNDOCUMENTED, which is the whole reason this plan exists. `reviews`/`review`/`to-review` are accepted and expand to every `to-review` plan not in a terminal directory, sharing one session. | `oc_runipd.py:2244-2281` (accepted spellings at `:2244-2246`); `agy_runipd.py:1339-1374`; verified live during research: the selector resolved 1 item with action `review` |
| F-2 | FOUR HELP SITES OMIT IT, not one. agy is the worse case because it documents `all` in the same prose block while omitting `reviews`, which reads as a complete enumeration and is not. | oc `selectors` help `oc_runipd.py:5990`, oc EXAMPLES `:5960-5976`; agy `selectors` help `agy_runipd.py:3938`, agy SELECTOR TYPES prose `:3914-3917` |
| F-3 | `--action` GREPS TO ZERO on both runners, so spec 2.1's definition of the alias targets a flag that does not exist. `uyeko5` records it among spec 2.1's unbuilt grammar entries and explicitly excludes it from its own scope, so nobody owns it; E-03 resolves that rather than assuming it. | `uyeko5` "Deferred / out of scope": "`--action` greps to zero in both runners"; spec `25kzda` 2.1 grammar block |
| F-4 | THE ACTION IS DERIVED FROM STATUS, NEVER CHOSEN, which is why the alias must be thin. `determine_action` returns `review` for `to-review` and `draft` and `execute` otherwise; there is no parameter by which a caller selects an action. A sibling `review` verb would therefore imply the driver can review an item the driver cannot review. | `oc_runipd.py:2409-2415`; `action_for:2417` adds only `orchestrate` |
| F-5 | `command_surface` IS ALREADY RED AND HAS NO HOST-RUNNER ENTRIES AT ALL, so this plan cannot be validated by a green declarations test and must not be read as fixing it. Both enforcing tests are `slow`, hence skipped by the configured bare run. | measured during research: `test_zero_undeclared_parser_leaves` fails with 63 undeclared leaves including `oc run`, `oc runipd`, `agy exec`; `tests/test_command_surface_declarations.py:37` `pytestmark = pytest.mark.slow`; `pyproject.toml` `addopts` carries `-m 'not slow'` |
| F-6 | THE SWEEP'S MEMBERSHIP IS WRONG TODAY (it filters `status == "to-review"` only, so a complete `draft` is reviewed when named and absent when swept), AND THIS PLAN DELIBERATELY DOES NOT FIX IT. Documenting a selector whose membership is about to change is acceptable only because E-01 documents the CONCEPT ("items whose next legal action is review") rather than the current buggy predicate. `6ypimw` fixes the predicate. | `oc_runipd.py:2252-2261` (`_needs_review`) versus `:2409` (`determine_action`); spec `25kzda` 2.4a property 2 |
| F-7 | THE PREDICATE IS DUPLICATED VERBATIM IN BOTH RUNNERS, differing only in one loop variable name (`setid` versus `_setid`), so any membership change must land in a shared module rather than twice. Out of scope here, owned by `6ypimw`, and the reason this plan touches only help text and argv. | verified by diff during research: oc `:2244-2282` versus agy `:1339-1375` produce one hunk, the loop variable; backlog `cnwy8g` tracks the broader duplication |

## Proposed changes (ordered, validatable)

1. Document `reviews` at all four help sites on both hosts, including one bare-sweep example each (E-01).
2. Register `aw <host> review [<selector>]` as an argv rewrite to the canonical run invocation, tested in composition with the implicit-`start` shim (E-02).
3. Resolve the `--action` dependency, either by consuming `uyeko5`'s flag or by registering it minimally with honest refusals for `plan`/`execute` (E-03).
4. Declare the new leaf and its alias in `command_surface`, reporting the pre-existing red state as pre-existing (E-04).

## Deferred / out of scope (with reason)

- THE SWEEP'S DRAFT ASYMMETRY AND THE DUPLICATED PREDICATE: owned by `6ypimw` (`revsweep-02`). E-01 documents the concept rather than the current predicate precisely so the two plans do not conflict, and F-6 records the divergence rather than papering over it.
- `--allow-drafts` AND THE DRAFT ADMISSION GATE: spec `25kzda` 2.5a, owned by `6ypimw`.
- EVERY OTHER SPEC 2.1 FLAG, including `--type`, `--allow-mixed`, and the mixed-type gate wiring: owned by `uyeko5`, which is gated behind the `rununify` consolidation. This plan deliberately does not wait on that, because help text and an argv rewrite do not touch the structures `rununify` is moving.
- `--action`'s FULL LEGALITY RULES (spec 2.6). Registering the flag minimally is in scope; implementing `plan` and `execute` legality requires the per-type dispatch table this Set has not built. E-03 refuses them rather than accepting them silently.
- CROSS-TYPE SWEEP COVERAGE (reviewing specs): `5slbpi`, which depends on `eyh1fu`. E-01 must NOT document the selector as spanning specs until then, since the help would be a false claim.
- DECLARING THE OTHER 62 UNDECLARED COMMAND-SURFACE LEAVES (F-5). A separate sweep with its own review; folding it in would bury this plan's one-line declaration in a 63-entry diff.

## Scope check

- Over-scope: none. Every edit either documents an existing selector, rewrites argv to an existing invocation, or declares the resulting leaf.
- Under-scope, DELIBERATE and stated plainly: after this plan the sweep is discoverable and spelled, and it still selects only IPDs and still misses complete drafts. Both limits are documented rather than fixed here, and both have named owners (`6ypimw`, `5slbpi`). Documenting a capability whose membership is about to widen is acceptable only because E-01 states the concept and the CURRENT type scoping, never a coverage claim that is false today.
- Under-scope: `--action` may land minimally (E-03 case b), with `plan` and `execute` refusing. Recorded rather than faked.

## Required tests / validation

- Both hosts' `--help` showing the selector at every site, and both bare-sweep examples.
- `aw oc review` and `aw agy review` producing an invocation INDISTINGUISHABLE from the canonical `run <selector> --action review`. This is the load-bearing evidence: the alias's whole contract is that it has no behavior of its own, so a test that merely proves it runs would pass even if it had forked.
- The argv-rewrite composition with the implicit-`start` shim, both orders exercised.
- Which E-03 resolution applied, stated, with `plan`/`execute` refusals shown if registered here.
- `command_surface` undeclared-leaf count NOT GROWN, measured with the slow tests invoked EXPLICITLY (a bare run skips them).
- Both driver suites green: `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`.
- Full suite BARE (`python3 -m pytest`), compared against your own pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree (`tests/test_run_viewer.py` shows phantom failures in a detached worktree; backlog `dh0uno`).

## Spec / documentation sync

- Spec `25kzda` 2.1 and 2.4a were amended 2026-09-04 to declare the alias and specify the selector. This plan IMPLEMENTS that text and MUST NOT change it. If execution reveals the spec is wrong, amend it with `aw specs note` and say so; do not diverge silently.
- The help text this plan writes IS user-facing documentation, so it must state the CURRENT type scoping (IPDs only) rather than the eventual cross-type behavior.
- If any user-facing doc enumerates driver selectors or `aw oc` subcommands, update it; otherwise state N/A with the paths checked.

## Open questions

### OQ-01: Should the alias be spelled `review` or `reviews` as a verb?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT BLOCKING; spec 2.1 says `review` and this plan implements `review`, so either answer is a one-line change. The case for `review` (chosen): it reads as an imperative verb, matching every other command in the surface (`run`, `check`, `find`), and the plural would read as a noun naming records, which is what `aw reviews` already means for the review-record tooling. The case for `reviews`: it matches the selector's own spelling exactly, so the operator learns one word. Chosen `review` because the collision with `aw reviews` (the record-reporting noun) is the more expensive confusion: two commands one letter apart, one reporting records and one launching agent sessions, is a mistake waiting to happen.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `--help` output from BOTH hosts showing the `reviews` selector documented, and paste all four sites' new text (oc selectors help, oc EXAMPLES, agy selectors help, agy SELECTOR TYPES prose). Paste the bare-sweep example from each host. CONFIRM EXPLICITLY that no site claims the selector spans specs, since it does not yet and a help string is user-facing documentation that would be a false claim.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: THE LOAD-BEARING EVIDENCE FOR THIS PLAN. Paste `aw oc review` and `aw agy review` resolving to the SAME invocation as the canonical `run <selector> --action review`, demonstrated by comparing the parsed namespace or the frozen run options, not merely by both commands exiting 0. A test proving the alias runs would also pass if the alias had forked, which is the one failure mode spec 2.1 names as a defect. Paste the argv rewrite showing it is a rewrite and not a second parser. Paste the composition test with the implicit-`start` shim, exercised in both orders.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: state plainly WHICH resolution applied (`uyeko5` landed, or minimal registration here). If minimal: paste `--action review` working, and paste `--action plan` and `--action execute` REFUSING with a not-implemented message naming what is missing. A silent accept does NOT satisfy this item. Paste evidence that no bespoke alias-only code path exists, that is, the alias reaches the same `--action` handling any operator would.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new `CommandDeclaration` entries (leaf plus alias with `canonical_command`). Paste the undeclared-leaf count BEFORE and AFTER, obtained by invoking the slow tests EXPLICITLY (show the invocation, since a bare `python3 -m pytest` skips them and would prove nothing). The count must not grow. State plainly that the test was already failing with 63 undeclared leaves at HEAD and that this plan does not fix that. Then both driver suites and the bare full suite with counts, compared against your own pre-change measurement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 4 E-leaves, one concern: make an existing capability discoverable and give it the declared spelling. E-01 is the documentation pass, E-02 the alias, E-03 its one real dependency, E-04 the surface declaration the repo's own CI check requires. E-02 and E-03 are separate because the alias's target flag does not exist, and conflating them would let a green "alias works" hide a bespoke code path that bypassed `--action` entirely.

Open questions: OQ-01 (verb spelling) is non-blocking with a recorded default and a stated reason. No blocking question remains.

This plan is `to-review` and requires explicit human approval before execution. It has NO plan dependencies (`- Item-Dependencies: none`) and deliberately does not wait on `rununify`: it touches help strings and one argv rewrite per host, not the structures that consolidation is moving. It must not run CONCURRENTLY with `uyeko5` or `ki6tom`, which edit the same parser functions.

Scope fence: touch ONLY `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/cli.py`, `agent_workflows/command_surface.py`, `tests/test_oc_runipd.py`, and `tests/test_agy_runipd_cli.py`. Do NOT change what the sweep SELECTS (`6ypimw` owns the predicate). Do NOT extract or edit the duplicated `_needs_review` closures. Do NOT add prose to the `/plan-review` prompt, which must remain the bare slash command and its path. Do NOT implement `--action`'s full legality rules. Do NOT declare the other 62 undeclared command-surface leaves. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. The load-bearing evidence is V-02's proof that the alias is INDISTINGUISHABLE from the canonical invocation, because "the alias works" is exactly what a forked alias would also demonstrate. Do NOT report the command-surface declarations test as passing: it is already red with 63 undeclared leaves and both enforcing tests are `slow`, so a green bare suite says nothing about them. Do NOT claim the sweep covers specs or complete drafts; it covers neither after this plan.

Execution contract: RE-READ both runner modules immediately before editing and locate every site BY SYMBOL, never by the line numbers in this plan: these are the highest-contention files in the repo and 11 other unexecuted plans declare them. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption, since a failed hook invalidates the check. If a co-worker's in-flight change cannot be safely combined with an edit, STOP and report rather than overwriting.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
