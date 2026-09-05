# IPD: document the reviews selector and add the aw <host> review alias

- Date: 2026-09-04
- Kind: child
- Concern: The review sweep is the driver's most frequent invocation and it is INVISIBLE. `aw oc runipd reviews` has worked since the selector was added, routing every `to-review` plan through `/plan-review` in one shared session, and NOTHING advertises it: the `selectors` help on both hosts names only "id6, setid, plan filenames/paths" (oc `oc_runipd.py:6028`) and "ID6, Set ID, IPD filename, or 'all'" (`agy_runipd.py:3938`), neither EXAMPLES block shows the bare sweep, and agy's SELECTOR TYPES block documents `all` while omitting `reviews` entirely (`agy_runipd.py:3914-3918`). The measured consequence is a maintainer asking for a command that already exists. Worse than invisible, the spelling is a trap: `reviews` is a magic BAREWORD occupying the same positional slot as the `start|resume|status|report|stop` subcommands, so the operator must know both that the word exists and that it is not a subcommand. Spec `25kzda` 2.1 (amended 2026-09-04) resolves both halves: it specifies `aw <host> review [<selector>]` as a THIN ALIAS of `run --action review`, and its new Section 2.4a promotes `reviews` from bareword to specified status selector.
- Scope: Make the existing review sweep DISCOVERABLE and give it the spelled surface spec 2.1 declares. Four deliverables: (1) document the `reviews` selector in both hosts' selector help, SELECTOR TYPES prose, and EXAMPLES; (2) register `aw <host> review [<selector>]` as a thin alias, AT THE `aw` HOST-SUBCOMMAND SEAM where the spelling actually lives, that expands to the canonical run invocation; (3) register `--action` minimally with the legality REFUSAL spec 2.1 requires, so a review-spelled command can never execute a plan; (4) make the empty sweep the exit-0 success spec 2.4a property 3 declares, since the alias makes that the common path. Adds NO selection logic and NO new action: `determine_action` already routes `to-review` to review, and the alias must produce an invocation indistinguishable from the canonical one. EXCLUDES fixing the sweep's draft asymmetry and extracting the duplicated predicate (`6ypimw` owns both), excludes `--allow-drafts` and every other spec 2.1 flag (`uyeko5` owns the flag surface), excludes `--action`'s full per-type legality table (spec 2.6), and excludes any change to what the sweep SELECTS.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: revsweep
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 76gsmv
- Approval: 2026-09-05, recorded via aw ipd set: status set to approved
- Blocks-Release: next
- From-Spec: 25kzda

## Workflow history

- 2026-09-05 executed (aw oc run model=its_direct/pt3-claude-opus-5-1m-us): EXECUTED at HEAD `97d5ddf4` in an isolated lane worktree. All five E-items performed, all five V-items verified with pasted evidence, `aw ipd lint --phase pre-transition` conforming. THE SWEEP IS NOW DISCOVERABLE AND SPELLED: `reviews` is documented at six help sites across both hosts (the plan's five plus agy's own `selectors` positional, which is a distinct string), and `aw oc review` / `aw agy review` exist as thin aliases where before they died at `invalid choice: 'review'`. THREE THINGS WORTH A READER'S ATTENTION. (1) The alias is proven INDISTINGUISHABLE from `runipd <selector> --action review` by diffing the FROZEN RUN STATE of both spellings, not by both exiting 0, because a forked alias would also exit 0; the differing-key set is empty. One shared function `cli.expand_host_review_argv` implements it for both hosts and both dispatch routes, so there is no second copy to drift. (2) `--action` did not exist (re-measured: zero occurrences in both runners), so E-03 case (b) applied: registered minimally on both hosts with the FAIL-CLOSED refusal that is the real safety content. `aw oc review <approved-id6>` now REFUSES with exit 2 instead of executing the plan, and it refuses with `--full-auto` present too, proven not only by the exit code but by the plan file's `- Status: reviewed` being UNMUTATED, which is what distinguishes a gate placed before the auto-approval from one placed after it. `plan` and `execute` refuse honestly rather than being silently accepted. (3) The empty sweep now exits 0 with a plain report and creates no run directory, via a `DriverError` SUBCLASS raised only from the status-selector branch, so `all` and a misspelled id6 still exit 2 (asserted negatively, not just by inspection). TWO STALE PREMISES REPORTED RATHER THAN WORKED AROUND, recorded as DECISION 23-76gsmv-D1: F-5's "already red with 63 undeclared leaves" and F-12's "four new leaves" no longer describe the tree. Both `command_surface` tests PASS at HEAD, `discover_parser_leaves` now de-duplicates argparse aliases so `review` is TWO leaves and not four, and declaring the predicted four would have turned a green test red. Undeclared count measured 0 -> 2 -> 0. Also recorded: the 13 driver-suite failures visible inside this turn are caused by the turn's own `AW_EXECUTION_ROLE=worker`, reproduce identically on the unmodified tree, and vanish when the variable is cleared (161 passed); the 14 bare-suite failures are the pre-existing `dh0uno` worktree phantoms, identical before and after. Net: +48 tests, zero new failures. Scope fence respected: six declared paths, no change to what the sweep SELECTS, no `/plan-review` prompt prose, no per-type legality table. Not pushed.

- 2026-09-05 approved (aw set): status set to approved

- 2026-09-04 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review ROUND 2 (cursory) at HEAD `9bb47658`: APPROVE WITH REVISIONS APPLIED; R2-1 verified clean, no edits needed. OQ-01 resolved to the singular `aw <host> review`, which the plan already implemented, so no execution item, scope path or validation item changed. Spelling verified internally consistent (10 singular occurrences, 0 plural). Round 2 record appended.

- 2026-09-04 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): POST-REVIEW EDIT, minor and recorded for completeness. OQ-01 RESOLVED by the maintainer: the alias is SINGULAR `aw <host> review`, which is what spec `25kzda` 2.1 already declares and what this plan already implements, so NO execution item, scope path, or validation item changed. The deciding reason recorded in the question: keeping a clear gap from the existing `aw reviews` REPORTING noun matters more than matching the selector's plural spelling, because one of the two spellings launches agent sessions that edit files while the other only reads. `aw ipd lint` conforming.

- 2026-09-04 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1 at HEAD `800b6dc5`: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008, all FIXED in place, zero deferred, zero open. Target plan committed and unchanged at `0ee800f4`, so the pre-review snapshot was correctly skipped. `aw ipd lint` conforming at `--phase author` before review and again at `--phase review-finalize` after revisions. THE PLAN'S PREMISE HELD COMPLETELY: the sweep works and is undocumented, `--action` still greps to ZERO in both runners, and `command_surface` still carries no host-runner entries. THREE FINDINGS CHANGED WHAT THE PLAN WILL PRODUCE. PR-001 (BLOCKER): E-02 pointed the executor at the DRIVER's implicit-`start` shim, but `aw oc review` fails at the `cli` layer with `invalid choice: 'review'` before argv ever reaches `oc_runipd.main`, so a driver-side rewrite would make `aw oc runipd review` work (it already does, as the bare selector) and leave the spelled surface spec 2.1 declares unreachable; the plan could have passed its own V-02 without delivering its goal. Retargeted to `cli._dispatch`'s existing pre-`parse_args` forwarding block (`cli.py:9270-9283`), and V-02 gained a REACHABILITY half pinning the before/after. PR-002 (BLOCKER): `--action review` was treated as plumbing, but `action_for` returns `execute` for `approved` AND `reviewed`, the queue builder calls it unconditionally, and under `--full-auto` a `reviewed` plan with approving `- Readiness:` is auto-cleared and EXECUTED, so `aw oc review <approved-id6>` with the flag merely accepted would EXECUTE the plan while the operator typed "review" (spec 2.6 forbids exactly that). E-03 now requires a fail-closed refusal before any session and V-03 requires it proven with `--full-auto` present. PR-003 (HIGH, new E-04): an empty sweep exits 2 today (`DriverError` -> `return 2`), while spec 2.4a property 3 declares it a success that exits 0; before the alias that path needed a magic bareword, after it the advertised everyday command reports the HEALTHY state as a failure, so the plan itself creates the exposure and now owns the fix, narrowly for the status selectors only. Also: PR-004 a fifth undocumented help site (oc's own SELECTOR TYPES block omits BOTH `reviews` and `all`); PR-005 agy has no `epilog` at all, so "one example per host" was unexecutable as written; PR-006 every argparse alias is its own declared leaf, so `review` on both host groups is FOUR new leaves and an `alias` class additionally requires `empty_error_renderer="delegated"`; PR-007 the oc line citations had drifted ~38 lines (`818uru`) and a second `command_surface` test is independently red; PR-008 the plan's own validation instructions could not be followed safely, since a bare exploratory `aw oc runipd reviews` LAUNCHES REAL AGENT SESSIONS, measured the hard way when this review's own two exploratory invocations started live runs. Four decisions recorded (D-1..D-4), all reversible. Review record: `.aw/records/reviews/20260904-revsweep-01-76gsmv-document-the-reviews-selector-and-add-the-aw-host-review-alias.review.md`.

- 2026-09-04 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored with the `revsweep` Set after the maintainer asked for a command to review everything needing review, and research found the capability already shipped and merely undocumented. THIS PLAN IS THE DISCOVERABILITY HALF ONLY, deliberately separated from the three substantive gaps (`6ypimw` the shared predicate and draft gate, `eyh1fu` the artifact-neutral record, `5slbpi` spec review) so that a documentation-and-alias change carrying no behavior risk is not held hostage to the record migration. MEASURED AT `3d4e5414`: `reviews`/`review`/`to-review` are accepted at `oc_runipd.py:2244-2246` and `agy_runipd.py:1339-1341`; the oc `selectors` help at `:5990` omits them, agy's at `:3938` omits them while naming `all`, agy's SELECTOR TYPES prose at `:3914-3917` documents `all` and omits `reviews`, and oc's EXAMPLES block at `:5960-5976` shows only the session-scoped `runipd ipdrunner --session <id>` form, never the bare sweep. ONE RULING RECORDED RATHER THAN RE-LITIGATED: the alias must be a THIN ALIAS, never a second action, because `determine_action` (`oc_runipd.py:2409`) derives the action from STATUS and cannot review an item that is not reviewable, so a sibling verb would imply a capability the driver does not have. Spec 2.1 was amended to say exactly that, including the rule that an operator-visible difference between the two spellings is a DEFECT in the alias. ALSO MEASURED, and the reason E-04 exists: `command_surface.COMMAND_INVENTORY` contains NO `oc`/`agy` entries at all, so `tests/test_command_surface_declarations.py` is ALREADY RED with 63 undeclared leaves at HEAD; this plan declares its own leaf and must NOT be read as fixing that backlog.

## Goal

Make the review sweep findable and give it the spelling spec `25kzda` 2.1 declares, so an operator who wants to review everything awaiting review can discover the capability from `--help` and invoke it without knowing a magic bareword.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the existing selector visible

- [x] E-01 Document the `reviews` selector everywhere a host's help enumerates selectors, on BOTH hosts. FIVE sites measured, and missing any one leaves the help self-contradictory: oc's `selectors` help string (`oc_runipd.py:6028`), oc's SELECTOR TYPES prose block (`:5987-5990`, which omits `reviews` AND omits `all`), oc's EXAMPLES epilog (`:5997-6015`), agy's `selectors` help string (`agy_runipd.py:3938`), and agy's SELECTOR TYPES prose block (`:3914-3918`, which documents `all` and omits `reviews`).
  RE-LOCATE EVERY SITE BY SYMBOL, NOT BY THESE LINE NUMBERS. They were re-measured at HEAD `800b6dc5` during review and had ALREADY drifted once (the oc citations moved by ~38 lines when `818uru` restructured the module). Anchor on `build_parser`, the `epilog="""EXAMPLES:` literal, and the `"selectors"` positional's `help=`.
  State the three accepted spellings (`reviews`, `review`, `to-review`), state that it selects items whose next legal action is review, and state the TYPE SCOPING spec 2.4a fixes: IPDs only, because that is what the runner can discover today. Do NOT document it as spanning specs; `5slbpi` makes that true and until then the help would be a false claim.
  Add ONE example per host showing the bare sweep (`runipd reviews`), which is the invocation the maintainer could not find. AGY HAS NO `epilog` AT ALL (greps to zero), so its example goes in the SELECTOR TYPES/description block rather than into an EXAMPLES epilog this plan must not invent.
  DESCRIBE THE MEMBERSHIP AS THE CONCEPT, NEVER AS `to-review`-ONLY. The current predicate is wrong (F-6) and `6ypimw` widens it; help text naming `status == to-review` would become false the day that lands, and help text naming "items whose next legal action is review" is true both before and after.
  - Depends on: none
  - Expected outcome: all five sites name the selector; `--help` on both hosts shows the sweep; no site claims cross-type coverage that does not exist yet; no site states the membership as the current buggy predicate.
  - Execution state: performed

### Task group 2: give it the spelled surface spec 2.1 declares

- [x] E-02 Register `aw <host> review [<selector>]` as a THIN ALIAS, on both hosts, expanding to exactly `run <selector> --action review` and, with the selector omitted, to exactly `run reviews --action review`.
  THE SPELLING IS `aw oc review`, SO THE ALIAS BELONGS AT THE `aw` HOST-SUBCOMMAND SEAM, NOT IN THE DRIVER'S `main()`. This was measured, and getting it wrong makes the plan's own goal unreachable: `python3 -m agent_workflows oc review` fails TODAY with `argument oc_command: invalid choice: 'review'`, because `review` must be a choice of the `oc_sub`/`agy_sub` subparsers (`cli.py:3186`, `:3248`) before any argv ever reaches `oc_runipd.main`. A rewrite placed only inside the driver's `main()` would make `aw oc runipd review` work (it ALREADY does, as the bare `reviews` selector) and would leave the spelled surface spec 2.1 declares still unreachable. So the rewrite goes in `cli._dispatch`, beside the EXISTING verbatim-forwarding block at `cli.py:9270-9283` that already special-cases `("oc","opencode") + ("runipd","run")` before `parse_args`, extended to accept `review` and to prepend the canonical tokens. The driver-side shim needs no change.
  THE ALIAS MUST CARRY NO LOGIC OF ITS OWN. Implement it as an argv rewrite ahead of the parser rather than as a second parser with its own flags: a duplicate parser is how the two hosts' flag surfaces diverged in the first place (measured by `uyeko5` F-5), and spec 2.1 states plainly that an operator-visible difference between `aw <host> review X` and `aw <host> run X --action review` is a DEFECT in the alias. `cli.py:3206-3211` records the same reasoning for the existing forwarding: re-declaring the driver's flags in `cli.py` "would drift and drop the implicit-start shim". PRESERVE THE VERBATIM TAIL, so `aw oc review --repo X --session Y` still reaches the driver's own parser unchanged.
  MIND THE ORDER OF THE TWO REWRITES: this alias and the driver's implicit-`start` shim (`oc_runipd.py:6305-6323`) both edit argv, and `review` must end up as `start <selector> --action review`. Since the alias emits a SELECTOR as the first token, the driver's shim then prepends `start` on its own; do not emit `start` yourself or the shim's `argv[0] not in subcommands` test produces `start start`. Test the composition, not just the alias alone.
  NOTE `--action` DOES NOT EXIST YET on either runner (re-measured at review: it greps to ZERO in both runner modules). So the rewrite's TARGET is unavailable, and E-03 resolves that rather than this item inventing the flag. Because of that ordering, DO NOT LAND E-02 WITHOUT E-03: an argv rewrite emitting an unregistered `--action` makes `aw oc review` a hard usage error, which is strictly worse than the undocumented-but-working state this plan starts from. If they land in one pass, say so; if E-02 is committed separately, it MUST NOT emit `--action` until E-03 registers it.
  - Depends on: E-01
  - Expected outcome: `aw oc review` and `aw agy review` both run the sweep; both accept an explicit selector; both preserve a verbatim flag tail; the alias is an argv rewrite at the `cli` host seam with no parser of its own; the composition with the driver's implicit-`start` shim is tested and produces exactly one `start`.
  - Execution state: performed

- [x] E-03 Resolve the `--action` dependency HONESTLY, and record which way you resolved it. Spec 2.1 defines `aw <host> review` as `run --action review`, and `--action` is unbuilt on both hosts (re-measured at review: zero occurrences in either runner).
  TWO ACCEPTABLE RESOLUTIONS, and the choice belongs to whoever executes this against the tree they find. (a) If `uyeko5` has landed and registered `--action`, the alias rewrites to it and this item is pure wiring. (b) If it has not, register `--action <review|plan|execute>` MINIMALLY here on BOTH hosts' `start` parser: accept the flag, honor `review`, and REFUSE `plan` and `execute` as not yet implemented rather than silently accepting them. Note `uyeko5` is `approved` and explicitly EXCLUDES `--action`, so case (b) is the expected one; case (a) applies only if some later plan claimed it.
  `--action review` MUST REFUSE A NON-REVIEWABLE ITEM, NOT SILENTLY EXECUTE IT. This is the item's real safety content, and it is the one place a thin alias can become dangerous. Measured: `action_for` returns `execute` for `approved` AND `reviewed` (`oc_runipd.py:2417-2430`, `determine_action:2409`), the queue builder calls it unconditionally at `:2630`, and under `--full-auto` a `reviewed` plan carrying an approving `- Readiness:` is cleared to `auto-approved` and EXECUTED at `:2611-2617`. So `aw oc review 5ahblp` on an approved plan, with the flag merely accepted and ignored, would EXECUTE that plan while the operator typed the word "review". Spec 2.6 says `--action review` permits re-review of a complete `reviewed` item and cannot "execute an unapproved item" or "turn a non-runnable record into a runnable one"; spec 2.1 adds that `--action` is legal only when "the requested action is legal from every item's current status". Therefore, under `--action review`, an item whose derived action is not `review` must be REFUSED (or skipped with an explicit finding) BEFORE any host session starts, and `--full-auto`'s auto-approval path must not run. Refusing before the queue is frozen is preferable, matching the existing fail-closed dependency preflight at `:2565`.
  Do NOT implement `--action`'s full per-type legality table (spec 2.6: `plan` legal only for an approved spec or open backlog item, `execute` only for approved/auto-approved/reusable IPDs); those need the per-type dispatch this Set has not built. The narrow rule above is not that table; it is the minimum that keeps the word "review" from executing code.
  A THIRD OPTION IS FORBIDDEN: do not make the alias a bespoke code path that bypasses `--action` entirely. That would be the second action this plan exists to avoid, and it would make the alias's behavior a separate thing to maintain.
  - Depends on: E-02
  - Expected outcome: `--action review` exists on both hosts and is what the alias uses; a non-reviewable item under `--action review` is refused BEFORE any session and is never executed, including under `--full-auto`; `plan`/`execute` refuse honestly if registered here; which resolution applied is stated; no bespoke alias-only code path exists.
  - Execution state: performed

- [x] E-04 Make the EMPTY sweep an exit-0 success, per spec 2.4a property 3, on BOTH hosts. Measured: `expand_selectors` raises `DriverError("No items in 'to-review' state found in repository")` when the sweep matches nothing (`oc_runipd.py:2278-2280`, `agy_runipd.py:1372-1374`), and `main`'s `except DriverError` prints `runipd: <msg>` to stderr and returns 2 (`oc_runipd.py:6411-6431`). So "nothing needs review" currently reports as a FAILURE.
  THIS IS IN SCOPE BECAUSE THIS PLAN CREATES THE COMMON PATH FOR IT. Before the alias, reaching the empty sweep took a deliberate magic bareword; after it, `aw oc review` is the advertised everyday command and the healthy repository state is the one where it matches nothing. Shipping a documented verb whose success case exits 2 would make its FIRST user experience a spurious error. Spec 2.4a property 3 is explicit: an empty `reviews` result "is a success, not an error", it "reports that plainly and exits 0", and it is "the one deliberate exception to the Section 2.3 rule that zero matches exit 2".
  KEEP THE EXEMPTION NARROW, exactly as the spec bounds it: only the STATUS selectors (`reviews`/`review`/`to-review`). A misspelled id6 or an unmatched setid must STILL exit 2. Do not touch the `all` branch's behavior, and do not convert `DriverError` generally.
  Report plainly and start no run: no run directory, no session, no ledger entry for a queue that does not exist.
  - Depends on: E-03
  - Expected outcome: an empty `reviews` sweep prints a plain "nothing awaiting review" message and exits 0 on both hosts, creating no run state; a misspelled id6 still exits 2; the `all` branch is unchanged.
  - Execution state: performed

- [x] E-05 Declare the new leaf in `command_surface.COMMAND_INVENTORY` and register the alias in the same declaration shape the surface already uses for an alias (`command_class="alias"` plus `canonical_command` pointing at the canonical leaf, as `att`/`todo`/`sanitize` do at `command_surface.py:103`, `:113`, `:123`).
  AN ALIAS DECLARATION CARRIES TWO EXTRA OBLIGATIONS the inventory enforces, both measured: `test_empty_error_renderer_classification_consistency` requires `empty_error_renderer="delegated"` for any `command_class="alias"` (`tests/test_command_surface_declarations.py:120-125`), and `required_scenarios` in `tests/conformance_matrix.py:76-98` derives the matrix rows from the declared class. Declare it as an alias, not as a `read`, or the classification test fails on a NEW row that is this plan's fault rather than pre-existing.
  STATE THE PRE-EXISTING FAILURE HONESTLY: `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` is ALREADY RED at HEAD with 63 undeclared leaves, 22 of them in the `oc`/`agy`/`opencode`/`antigravity` families (the inventory contains no host-runner entries at all). Both that test and `tests/test_cli_conformance_matrix.py` are `pytest.mark.slow` (`test_command_surface_declarations.py:37`, `test_cli_conformance_matrix.py:46`), so a bare `python3 -m pytest` SKIPS them and a green bare suite proves nothing here. Run them explicitly, and BUDGET FOR IT: the two files together did not finish within 120s at review, so allow several minutes rather than reporting a timeout as a pass.
  ALSO MEASURED AND ALSO PRE-EXISTING: `test_empty_error_renderer_classification_consistency` is red at HEAD too (`runs list` declares `shared_empty_result` where the test demands `renderer_boundary`). Do NOT report that as caused by this plan, and do NOT fix it here.
  DECLARE EVERY ALIAS SPELLING YOU ACTUALLY ADD. `discover_parser_leaves` walks `sa.choices`, which contains every argparse alias as its own key (that is why `opencode runipd` and `antigravity runagy` each appear as separate undeclared leaves). So if `review` is registered on both host groups with their `opencode`/`antigravity` aliases, that is four new leaves, and declaring one of four would GROW the undeclared count while appearing to shrink it.
  So the bar for this item is NO-WORSENING plus the new declarations, not a green test. Do NOT declare the other 62 leaves to make the test pass: that is a separate sweep with its own review, and folding it in would hide this plan's own change inside a 63-entry diff.
  - Depends on: E-04
  - Expected outcome: every new leaf spelling and its alias are declared with `command_class="alias"` and `empty_error_renderer="delegated"`; the undeclared-leaves count does not grow; the two pre-existing red states are reported as pre-existing, with the explicit slow-test invocation shown.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE IMPLICIT-`start` SHIM IS THE PRECEDENT for argv rewriting on these runners (`oc_runipd.py:6267-6285`). It exists because `runipd` deliberately declares ZERO flags in `cli.py` (rationale comment at `cli.py:3174-3179`): re-declaring them there would drift from the driver's real parser and bypass the shim. An alias implemented in `cli.py` with its own flags would violate that reasoning; an argv rewrite honors it.
- `aw oc runipd` reaches its driver through `cli.py:9496-9503` forwarding `argparse.REMAINDER` verbatim, so the driver's own `build_parser` is the only place a selector or flag is really declared. Documentation must go there, not into `cli.py`'s help.
- BOTH RUNNERS ARE THE HIGHEST-CONTENTION FILES IN THE REPO (`uyeko5` F-8 measured 11 unexecuted plans declaring them). This plan touches only help strings and one argv rewrite per host, deliberately, so it can land without waiting on the `rununify` consolidation.
- A REVIEW TURN'S PROMPT IS LITERALLY `/plan-review <relpath>` AND NOTHING ELSE (`oc_runipd.py:3540-3562`, with a docstring warning never to append prose because the slash command absorbs extra text into `$ARGUMENTS`). Nothing in this plan may add prose to that prompt.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | THE SWEEP ALREADY WORKS AND IS UNDOCUMENTED, which is the whole reason this plan exists. `reviews`/`review`/`to-review` are accepted and expand to every `to-review` plan not in a terminal directory, sharing one session. | `oc_runipd.py:2244-2281` (accepted spellings at `:2244-2246`); `agy_runipd.py:1339-1374`; RE-VERIFIED LIVE at review: the bare selector resolved 5 items, all with action `review` |
| F-2 | FIVE HELP SITES OMIT IT, not four (CORRECTED AT REVIEW). The plan missed oc's OWN SELECTOR TYPES prose block, which enumerates id6/setid/filename and omits BOTH `reviews` and `all`. agy remains the worse case because it documents `all` in the same prose block while omitting `reviews`, which reads as a complete enumeration and is not. | oc SELECTOR TYPES prose `oc_runipd.py:5987-5990`, oc `selectors` help `:6028`, oc EXAMPLES `:5997-6015`; agy `selectors` help `agy_runipd.py:3938`, agy SELECTOR TYPES prose `:3914-3918` |
| F-3 | `--action` GREPS TO ZERO on both runners, so spec 2.1's definition of the alias targets a flag that does not exist. `uyeko5` is now `approved` and explicitly EXCLUDES `--action`, so nobody owns it; E-03 resolves that rather than assuming it. This also SEQUENCES E-02 behind E-03: an argv rewrite emitting an unregistered flag turns `aw oc review` into a usage error. | re-measured at review: `grep -c '\-\-action'` returns 0 in BOTH `oc_runipd.py` and `agy_runipd.py`; `uyeko5` Scope excludes `--action`; spec `25kzda` 2.1 grammar block |
| F-4 | THE ACTION IS DERIVED FROM STATUS, NEVER CHOSEN, which is why the alias must be thin. `determine_action` returns `review` for `to-review` and `draft` and `execute` otherwise; there is no parameter by which a caller selects an action. A sibling `review` verb would therefore imply the driver can review an item the driver cannot review. | `oc_runipd.py:2409-2415`; `action_for:2417-2430` adds only `orchestrate` |
| F-5 | `command_surface` IS ALREADY RED AND HAS NO HOST-RUNNER ENTRIES AT ALL, so this plan cannot be validated by a green declarations test and must not be read as fixing it. Both enforcing tests are `slow`, hence skipped by the configured bare run, and a SECOND test in the same file (`test_empty_error_renderer_classification_consistency`) is independently red at HEAD on `runs list`. | re-measured at review: `test_zero_undeclared_parser_leaves` fails with 63 undeclared leaves, 22 in the `oc`/`agy`/`opencode`/`antigravity` families; `tests/test_command_surface_declarations.py:37` and `tests/test_cli_conformance_matrix.py:46` both `pytestmark = pytest.mark.slow`; `pyproject.toml` `addopts` carries `-m 'not slow'` |
| F-8 | **THE ALIAS CANNOT LIVE IN THE DRIVER'S `main()`, WHICH THE PLAN AS WRITTEN GOT WRONG.** E-02 originally pointed the executor at the driver's implicit-`start` shim as the implementation site. But `review` must first be a CHOICE of the `aw oc`/`aw agy` subparsers, because `cli` resolves the host subcommand before any argv reaches the driver: `aw oc review` fails today with `invalid choice: 'review'`. A driver-side-only rewrite would make `aw oc runipd review` work (it already does, as the bare selector) and leave the spelled surface spec 2.1 declares unreachable, i.e. the plan could pass its own V-02 without delivering its goal. E-02 now targets `cli._dispatch`'s existing pre-`parse_args` forwarding block. | measured at review: `python3 -m agent_workflows oc review` -> `argument oc_command: invalid choice: 'review' (choose from 'runipd', 'run', 'update-models', 'sync-models')`; the host-group subparsers at `cli.py:3186` (`oc_sub`) and `:3248` (`agy_sub`); the verbatim-forwarding precedent at `cli.py:9270-9283` |
| F-9 | **`--action review` MUST REFUSE A NON-REVIEWABLE ITEM OR THE WORD "REVIEW" EXECUTES CODE.** The plan treated `--action` as mere plumbing. It is not: `action_for` returns `execute` for `approved` AND `reviewed`, the queue builder calls it unconditionally, and under `--full-auto` a `reviewed` plan with an approving `- Readiness:` is auto-cleared and EXECUTED. So `aw oc review <approved-id6>`, with the flag accepted and ignored, would execute that plan. Spec 2.6 forbids exactly that ("cannot force a status transition, execute an unapproved item"). E-03 now requires a fail-closed refusal before any session, and V-03 requires it proven under `--full-auto`. | `oc_runipd.py:2409-2415` (`determine_action`), `:2417-2430` (`action_for`), `:2630` (unconditional call), `:2611-2617` (the `reviewed` + `full_auto` -> `auto-approved` + execute path); spec `25kzda` 2.1 `--action` rule and 2.6 |
| F-10 | **AN EMPTY SWEEP EXITS 2 TODAY, AND THIS PLAN MAKES THAT THE COMMON PATH.** `expand_selectors` raises `DriverError("No items in 'to-review' state found in repository")` on an empty sweep and `main` maps `DriverError` to a stderr line plus exit 2. Spec 2.4a property 3 declares the opposite normatively: an empty `reviews` result is a success that exits 0, "the one deliberate exception to the Section 2.3 rule that zero matches exit 2". Before the alias this took a magic bareword; after it, the advertised everyday command reports the HEALTHY state as a failure. Added as E-04 rather than deferred, because the plan itself creates the exposure. | `oc_runipd.py:2278-2280`, `agy_runipd.py:1372-1374`, `oc_runipd.py:6411-6431` (`except DriverError` -> `return 2`); verified: `expand_selectors` on a manifest with one `approved` plan raises that `DriverError`; spec `25kzda` 2.4a property 3 |
| F-11 | AGY HAS NO `epilog` AND THEREFORE NO EXAMPLES BLOCK, so "add ONE example per host" was unexecutable as written for agy. Its example must go in the description/SELECTOR TYPES block; inventing an EXAMPLES epilog would be an unreviewed help-layout change. | `grep -n "epilog" agent_workflows/agy_runipd.py` returns nothing; oc's is at `:5997` |
| F-12 | EVERY ARGPARSE ALIAS IS ITS OWN LEAF in the declarations test, so registering `review` on both host groups (each with an `opencode`/`antigravity` alias) creates FOUR new leaves, not one. Declaring one of four would grow the undeclared count while appearing to shrink it. An `alias`-classed declaration also MUST carry `empty_error_renderer="delegated"` or a second (currently red) test gains a NEW failure attributable to this plan. | `command_surface.discover_parser_leaves:1334-1352` walks `sa.choices` (hence `opencode runipd`/`antigravity runagy` appear separately in the undeclared set); `tests/test_command_surface_declarations.py:120-125` |
| F-6 | THE SWEEP'S MEMBERSHIP IS WRONG TODAY (it filters `status == "to-review"` only, so a complete `draft` is reviewed when named and absent when swept), AND THIS PLAN DELIBERATELY DOES NOT FIX IT. Documenting a selector whose membership is about to change is acceptable only because E-01 documents the CONCEPT ("items whose next legal action is review") rather than the current buggy predicate. `6ypimw` fixes the predicate. | `oc_runipd.py:2252-2261` (`_needs_review`) versus `:2409` (`determine_action`); verified: `action_for(None,'draft')` -> `review` while `_needs_review` tests `st == "to-review"`; spec `25kzda` 2.4a property 2 |
| F-7 | THE PREDICATE IS DUPLICATED VERBATIM IN BOTH RUNNERS, differing only in one loop variable name (`setid` versus `_setid`), so any membership change must land in a shared module rather than twice. Out of scope here, owned by `6ypimw`, and the reason this plan touches only help text and argv. | verified by diff during research: oc `:2244-2282` versus agy `:1339-1375` produce one hunk, the loop variable; backlog `cnwy8g` tracks the broader duplication |

## Proposed changes (ordered, validatable)

1. Document `reviews` at all FIVE help sites on both hosts, including one bare-sweep example each (E-01).
2. Register `aw <host> review [<selector>]` as an argv rewrite AT THE `cli` HOST SEAM to the canonical run invocation, tested in composition with the driver's implicit-`start` shim (E-02).
3. Resolve the `--action` dependency, either by consuming `uyeko5`'s flag or by registering it minimally, WITH the fail-closed refusal that stops `--action review` from executing a non-reviewable item (E-03).
4. Make the empty sweep exit 0 with a plain report, narrowly for the status selectors only (E-04).
5. Declare every new leaf spelling and its alias in `command_surface`, reporting the two pre-existing red states as pre-existing (E-05).

## Deferred / out of scope (with reason)

- THE SWEEP'S DRAFT ASYMMETRY AND THE DUPLICATED PREDICATE: owned by `6ypimw` (`revsweep-02`). E-01 documents the concept rather than the current predicate precisely so the two plans do not conflict, and F-6 records the divergence rather than papering over it.
- `--allow-drafts` AND THE DRAFT ADMISSION GATE: spec `25kzda` 2.5a, owned by `6ypimw`.
- EVERY OTHER SPEC 2.1 FLAG, including `--type`, `--allow-mixed`, and the mixed-type gate wiring: owned by `uyeko5`, which is gated behind the `rununify` consolidation. This plan deliberately does not wait on that, because help text and an argv rewrite do not touch the structures `rununify` is moving.
- `--action`'s FULL PER-TYPE LEGALITY TABLE (spec 2.6). Registering the flag minimally is in scope, and so is the narrow fail-closed refusal that keeps `--action review` from executing a non-reviewable item (E-03, F-9), because without it the plan ships a verb named "review" that can execute code. What is EXCLUDED is the rest of the table: `plan` legal only for an approved spec or open backlog item, `execute` only for approved/auto-approved/reusable IPDs, per-type dispatch. Those need machinery this Set has not built.
- CROSS-TYPE SWEEP COVERAGE (reviewing specs): `5slbpi`, which depends on `eyh1fu`. E-01 must NOT document the selector as spanning specs until then, since the help would be a false claim.
- DECLARING THE OTHER 62 UNDECLARED COMMAND-SURFACE LEAVES (F-5), and the independently red `test_empty_error_renderer_classification_consistency` on `runs list`. A separate sweep with its own review; folding it in would bury this plan's own declarations in a 63-entry diff.

## Scope check

- Over-scope: none. Every edit either documents an existing selector, rewrites argv to an existing invocation, registers the flag that invocation names, corrects the exit code of the path the new verb makes common, or declares the resulting leaves.
- E-04 (the empty-sweep exit code) IS A DELIBERATE, JUSTIFIED WIDENING added at review, not scope creep. It changes an exit code, which is a behavior change this plan otherwise avoids. It is in scope because THIS plan creates the exposure: before the alias, the empty sweep was reachable only through a magic bareword; after it, `aw oc review` is the advertised everyday command and the healthy repository state (nothing awaiting review) reports as a failure. Shipping the documented verb without it would mean advertising a command whose success case exits 2. Spec 2.4a property 3 already decides the behavior, so no new policy is invented.
- Under-scope, DELIBERATE and stated plainly: after this plan the sweep is discoverable and spelled, and it still selects only IPDs and still misses complete drafts. Both limits are documented rather than fixed here, and both have named owners (`6ypimw`, `5slbpi`). Documenting a capability whose membership is about to widen is acceptable only because E-01 states the concept and the CURRENT type scoping, never a coverage claim that is false today.
- Under-scope: `--action` may land minimally (E-03 case b), with `plan` and `execute` refusing. Recorded rather than faked.

## Required tests / validation

- Both hosts' `--help` showing the selector at every one of the five sites, and both bare-sweep examples.
- `aw oc review` and `aw agy review` producing an invocation INDISTINGUISHABLE from the canonical `run <selector> --action review`. This is the load-bearing evidence: the alias's whole contract is that it has no behavior of its own, so a test that merely proves it runs would pass even if it had forked.
- `aw oc review` REACHING THE DRIVER AT ALL, which is the regression the pre-change measurement pins: it fails today with `invalid choice: 'review'`, so paste the before and after.
- The argv-rewrite composition with the driver's implicit-`start` shim, proving exactly one `start` is prepended and a verbatim flag tail survives.
- Which E-03 resolution applied, stated, with `plan`/`execute` refusals shown if registered here, AND the fail-closed refusal of a non-reviewable item under `--action review` proven including with `--full-auto` present.
- The empty sweep exiting 0 with no run directory created, on both hosts, and a misspelled id6 still exiting 2.
- `command_surface` undeclared-leaf count NOT GROWN, measured with the slow tests invoked EXPLICITLY (a bare run skips them; budget minutes, since the two files did not finish in 120s at review).
- Both driver suites green: `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`.
- Full suite BARE (`python3 -m pytest`), compared against your own pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- USE `--prepare-only` FOR EVERY LIVE INVOCATION, or a fake/`--repo` fixture. Measured during this review: a bare `aw oc runipd review` LAUNCHES REAL AGENT SESSIONS against the repository's live `to-review` plans (it resolved 5 items and started a `/plan-review` turn). An exploratory "does the selector work" command is therefore a mutating action. Validate the resolution and exit codes without starting sessions.
- Measure in the PRIMARY checkout, not a scratch worktree (`tests/test_run_viewer.py` shows phantom failures in a detached worktree; backlog `dh0uno`).

## Spec / documentation sync

- Spec `25kzda` 2.1 and 2.4a were amended 2026-09-04 to declare the alias and specify the selector. This plan IMPLEMENTS that text and MUST NOT change it. If execution reveals the spec is wrong, amend it with `aw specs note` and say so; do not diverge silently.
- The help text this plan writes IS user-facing documentation, so it must state the CURRENT type scoping (IPDs only) rather than the eventual cross-type behavior.
- CHECKED AT REVIEW so the executor does not have to rediscover it: NO tracked user-facing doc enumerates the driver's selectors. `docs/` mentions `aw oc run` exactly once, in `docs/reporting-contract.md:47`, and only as the source of a prompt's reporting contract, not as a selector or subcommand list. `README.md`, `AGENTS.md`, and `CONTRIBUTING.md` do not enumerate either. So the help strings themselves are the only user-facing documentation to update, and the correct statement is N/A-with-paths for `docs/`, `README.md`, `AGENTS.md`, `CONTRIBUTING.md`. RE-CHECK rather than trusting this line, since a doc may land in between.
- `aw <host> review` is a NEW USER-FACING COMMAND, so its `help=` string is user-facing prose subject to the repository's no-em-dash rule, and it must say plainly what the bare form selects.

## Open questions

### OQ-01: Should the alias be spelled `review` or `reviews` as a verb?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-04 by the maintainer, asked interactively: SINGULAR `aw <host> review`, which is what spec 2.1 already declares and what this plan already implements, so no E-item changes. The deciding reason was the one recorded below: keeping a clear gap from the existing `aw reviews` REPORTING noun matters more than matching the selector's spelling, because one of the two spellings launches agent sessions that edit files while the other only reads. Recorded as resolved rather than left open so a later reader does not reopen a settled naming question. ORIGINAL ANALYSIS: NOT BLOCKING; spec 2.1 says `review` and this plan implements `review`, so either answer is a one-line change. The case for `review` (chosen): it reads as an imperative verb, matching every other command in the surface (`run`, `check`, `find`), and the plural would read as a noun naming records, which is what `aw reviews` already means for the review-record tooling. The case for `reviews`: it matches the selector's own spelling exactly, so the operator learns one word. Chosen `review` because the collision with `aw reviews` (the record-reporting noun) is the more expensive confusion: two commands one letter apart, one reporting records and one launching agent sessions, is a mistake waiting to happen.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `--help` output from BOTH hosts showing the `reviews` selector documented, and paste all FIVE sites' new text (oc SELECTOR TYPES prose, oc selectors help, oc EXAMPLES, agy selectors help, agy SELECTOR TYPES prose). Paste the bare-sweep example from each host, and state where agy's went given it has no `epilog` (F-11). CONFIRM EXPLICITLY that no site claims the selector spans specs, since it does not yet and a help string is user-facing documentation that would be a false claim. CONFIRM ALSO that no site describes membership as `status == to-review`, which `6ypimw` is about to make false.
  - Observed evidence: All measured at HEAD `97d5ddf4` in the assigned lane worktree.

    SITE 1, oc SELECTOR TYPES prose (`python3 -m agent_workflows.oc_runipd --help`), which omitted BOTH `reviews` and `all` before (F-2):

    ```text
    SELECTOR TYPES:
      - id6:      6-character unique ID (e.g. 'pr2nd0', '5ahblp')
      - setid:    IPD Set identifier (e.g. 'ipdrunner', 'execset')
      - filename: Path or filename of an IPD file (e.g. '.aw/records/plans/pending/...ipd.md')
      - reviews:  Every IPD whose next legal action is review, swept in one shared session.
                  Spelled 'reviews', 'review', or 'to-review'. Selects IPDs only; specs and
                  backlog items are not reachable by any selector yet. Matching nothing is a
                  success and exits 0, because a repository with nothing awaiting review is
                  the healthy state. 'aw oc review' is the spelled form of this sweep.
      - all:      Every actionable pending IPD in the repository
    ```

    SITE 2, oc EXAMPLES epilog, first entry so the sweep is the first thing read:

    ```text
    EXAMPLES:
      # Review EVERYTHING awaiting review, in one shared session (the review sweep).
      # Spelled 'reviews', 'review', or 'to-review'; 'aw oc review' is the same command:
      runipd reviews
    ```

    SITE 3, oc `selectors` positional help (`oc_runipd start --help`):

    ```text
    positional arguments:
      selectors             One or more target selectors: id6 (e.g. 5ahblp), setid
                           (e.g. execset), plan filenames/paths, 'reviews' (alias
                           'review'/'to-review'; every IPD whose next legal
                           action is review, IPDs only), or 'all'
    ```

    SITE 4 and 5, agy SELECTOR TYPES prose AND agy's bare-sweep example (`python3 -m agent_workflows.agy_runipd --help`). AGY'S EXAMPLE WENT IN THE DESCRIPTION BLOCK, not an EXAMPLES epilog, exactly as F-11 requires: `parser.epilog` is `None` on this host and inventing an epilog would be an unreviewed help-layout change. A test asserts `epilog is None` so a future epilog forces this decision to be revisited rather than silently leaving the example orphaned.

    ```text
    SELECTOR TYPES:
      - id6:      6-character unique ID (e.g. 'pr2nd0', '5ahblp')
      - setid:    IPD Set identifier (e.g. 'ipdrunner', 'execset')
      - filename: Path or filename of an IPD file (e.g. '.aw/records/plans/pending/...ipd.md')
      - reviews:  Every IPD whose next legal action is review, swept in one shared session.
                  Spelled 'reviews', 'review', or 'to-review'. Selects IPDs only; specs and
                  backlog items are not reachable by any selector yet. Matching nothing is a
                  success and exits 0, because a repository with nothing awaiting review is
                  the healthy state. 'aw agy review' is the spelled form of this sweep.
      - all:      All actionable pending IPDs in the repository

    EXAMPLE, the review sweep (the most frequent invocation):
      runagy reviews
    ```

    SITE 6 (agy `selectors` positional help, `agy_runipd start --help`), which the plan counted inside site 4/5 but is a distinct string:

    ```text
    positional arguments:
      selectors             Target plan selectors: ID6, Set ID, IPD filename,
                           'reviews' (alias 'review'/'to-review'; every IPD whose
                           next legal action is review, IPDs only), or 'all'
    ```

    NO CROSS-TYPE CLAIM, CONFIRMED EXPLICITLY. Every site says "Selects IPDs only; specs and backlog items are not reachable by any selector yet", which is true today and does not pre-announce `5slbpi`. Asserted by `test_help_does_not_claim_cross_type_coverage` (oc) and `test_help_states_the_current_type_scoping_and_not_the_buggy_predicate` (agy).

    NO `status == to-review` MEMBERSHIP CLAIM, CONFIRMED EXPLICITLY. Every site states the CONCEPT, "every IPD whose next legal action is review", which stays true after `6ypimw` widens the predicate to include complete drafts. Asserted negatively as well as positively by `test_help_does_not_state_membership_as_the_current_buggy_predicate`, which fails if the literal string `status == to-review` ever appears.

    ```text
    $ python3 -m pytest tests/test_oc_runipd.py -o addopts="" -q -k ReviewsSelectorDocumented
    ......                                                                   [100%]
    6 passed, 116 deselected

    $ python3 -m pytest tests/test_agy_runipd_cli.py -o addopts="" -q -k AgyReviewsSelectorDocumented
    .....                                                                    [100%]
    5 passed, 34 deselected
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: THE LOAD-BEARING EVIDENCE FOR THIS PLAN, and it has two halves.
    (a) REACHABILITY, the regression the plan exists to remove: paste `python3 -m agent_workflows oc review` failing BEFORE with `invalid choice: 'review'` and succeeding AFTER, on both hosts. Without this half, the plan could pass (b) while `aw oc review` still did not exist.
    (b) INDISTINGUISHABILITY: paste `aw oc review` and `aw agy review` resolving to the SAME invocation as the canonical `run <selector> --action review`, demonstrated by comparing the parsed namespace or the frozen run options, not merely by both commands exiting 0. A test proving the alias runs would also pass if the alias had forked, which is the one failure mode spec 2.1 names as a defect.
    Paste the argv rewrite itself showing it is a rewrite at the `cli` host seam and not a second parser. Paste the composition evidence: exactly ONE `start` reaches the driver's parser (not `start start`), and a verbatim flag tail such as `--repo`/`--session` survives to the driver unchanged.
    USE `--prepare-only` OR A FIXTURE REPO. A bare live invocation starts real agent sessions.
  - Observed evidence: All at HEAD `97d5ddf4`. Every live invocation used `--prepare-only` against a FIXTURE repo under `/tmp`, never the live tree, so no agent session was started at any point.

    (a) REACHABILITY, the regression this plan exists to remove. BEFORE, measured on the unmodified tree, both hosts:

    ```text
    $ python3 -m agent_workflows oc review
    agent-workflows oc: error: argument oc_command: invalid choice: 'review' (choose from 'runipd', 'run', 'update-models', 'sync-models')

    $ python3 -m agent_workflows agy review
    agent-workflows agy: error: argument agy_command: invalid choice: 'review' (choose from 'runipd', 'run', 'runagy', 'sessions', 'view', 'view-antigravity-jsonl', 'exec')
    ```

    AFTER, all FOUR host spellings reach the driver (fixture repo with no `to-review` plan, so the E-04 success path is what they reach):

    ```text
    $ python3 -m agent_workflows oc review --repo <fixture> --prepare-only
    Nothing awaiting review; no run started.
    EXIT=0
    $ python3 -m agent_workflows agy review --repo <fixture> --prepare-only
    Nothing awaiting review; no run started.
    EXIT=0
    $ python3 -m agent_workflows opencode review --repo <fixture> --prepare-only
    Nothing awaiting review; no run started.
    EXIT=0
    $ python3 -m agent_workflows antigravity review --repo <fixture> --prepare-only
    Nothing awaiting review; no run started.
    EXIT=0
    ```

    The verb is also now visible in `aw oc --help`, which is the discoverability the plan exists for:

    ```text
    positional arguments:
      {runipd,run,review,update-models,sync-models}
        runipd (run)        Restartable non-interactive OpenCode driver for
                            reviewing/executing IPDs.
        review              Review IPDs awaiting review (thin alias of 'aw oc
                            runipd <selector> --action review'; with no selector
                            it sweeps every IPD whose next legal action is
                            review).
    ```

    (b) INDISTINGUISHABILITY, compared by FROZEN RUN STATE rather than by exit code, because both a faithful and a forked alias would exit 0. Fixture repo with one `to-review` plan, two `--prepare-only` runs with pinned run ids, then the two `state.json` files diffed with only identity/timestamp keys removed:

    ```text
    alias  options: {"action": "review", "agent": null, "auto": true, "full_auto": false, "isolate_worktree": true, "max_items_per_session": 4, "model": null, "no_audit": true, "opencode": "opencode", "output_mode": "clean", "self_finalize": true, "session": null, "stall_timeout": 600.0, "validate": false, "variant": null}
    canon  options: {"action": "review", "agent": null, "auto": true, "full_auto": false, "isolate_worktree": true, "max_items_per_session": 4, "model": null, "no_audit": true, "opencode": "opencode", "output_mode": "clean", "self_finalize": true, "session": null, "stall_timeout": 600.0, "validate": false, "variant": null}
    alias  selectors: ['reviews'] queue: [('torv01', 'review', 'to-review')]
    canon  selectors: ['reviews'] queue: [('torv01', 'review', 'to-review')]

    DIFFERING KEYS: NONE -> the alias is INDISTINGUISHABLE from the canonical invocation
    ```

    Pinned as a test by `test_alias_freezes_the_same_run_state_as_the_canonical_invocation`, which asserts `options`, `selectors`, `queue`, and then the WHOLE state dict are equal.

    THE REWRITE IS A REWRITE, NOT A SECOND PARSER. The implementation is `cli.expand_host_review_argv`, a pure argv function, called from the SAME pre-`parse_args` forwarding block in `cli._dispatch` that already special-cases `("oc","opencode") + ("runipd","run")`. It declares none of the driver's flags; the `review` subparser itself captures `argparse.REMAINDER` exactly as `runipd` does. Both hosts and both dispatch routes (the fast path and the parsed-namespace fallback) call that ONE function, so there is no second implementation that could drift. Observed expansions:

    ```text
    bare sweep               tail=[]                          -> ['reviews', '--action', 'review']
    explicit selector        tail=['torv01']                   -> ['torv01', '--action', 'review']
    verbatim flag tail       tail=['--repo','/tmp/x','--session','sess-1']
                                                              -> ['reviews', '--repo', '/tmp/x', '--session', 'sess-1', '--action', 'review']
    selector + flag tail     tail=['torv01','--repo','/tmp/x','--session','sess-1']
                                                              -> ['torv01', '--repo', '/tmp/x', '--session', 'sess-1', '--action', 'review']
    help passthrough         tail=['--help']                   -> ['--help']
    ```

    COMPOSITION WITH THE IMPLICIT-`start` SHIM, the plan's named hazard, showing EXACTLY ONE `start` in every case and a surviving verbatim flag tail:

    ```text
    bare sweep               after shim: ['start', 'reviews', '--action', 'review']   start count = 1
    explicit selector        after shim: ['start', 'torv01', '--action', 'review']   start count = 1
    verbatim flag tail       after shim: ['start', 'reviews', '--repo', '/tmp/x', '--session', 'sess-1', '--action', 'review']   start count = 1
    selector + flag tail     after shim: ['start', 'torv01', '--repo', '/tmp/x', '--session', 'sess-1', '--action', 'review']   start count = 1
    help passthrough         after shim: ['--help']   start count = 0
    ```

    The verbatim tail is proven end to end on the agy host as well, by mocking `agy_runipd.main` and asserting the exact argv it received: `['5ahblp', '--repo', '/tmp/x', '--session', 's1', '--action', 'review']`.

    ```text
    $ python3 -m pytest tests/test_oc_runipd.py -o addopts="" -q -k HostReviewAliasExpansion
    .......                                                                  [100%]
    7 passed, 115 deselected

    $ python3 -m pytest tests/test_agy_runipd_cli.py -o addopts="" -q -k AgyReviewAlias
    ...                                                                      [100%]
    3 passed, 36 deselected
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: state plainly WHICH resolution applied (`uyeko5` landed, or minimal registration here). If minimal: paste `--action review` working, and paste `--action plan` and `--action execute` REFUSING with a not-implemented message naming what is missing. A silent accept does NOT satisfy this item.
    THE SAFETY HALF IS MANDATORY AND IS THE POINT OF THIS ITEM (F-9): paste `--action review` REFUSING a non-reviewable item, using a plan whose status derives `execute` (an `approved` one), and paste it refusing WITH `--full-auto` ALSO PRESENT, since that is the path that auto-clears a `reviewed` plan to `auto-approved` and executes it. Show the refusal happens BEFORE any host session or run directory exists. An `--action review` that accepts an approved id6 and executes it FAILS this item, however green the rest is.
    Paste evidence that no bespoke alias-only code path exists, that is, the alias reaches the same `--action` handling any operator would.
  - Observed evidence: All at HEAD `97d5ddf4`, every invocation `--prepare-only` against a `/tmp` fixture.

    WHICH RESOLUTION APPLIED: CASE (b), MINIMAL REGISTRATION HERE. Re-measured before writing any code: `grep -c -- "--action"` returns `0` for BOTH `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`, so `uyeko5` had not landed the flag and nobody owned it. Registered `--action {review,plan,execute}` on both hosts' `start` parser, `default=None`.

    ```text
    $ python3 -m agent_workflows.oc_runipd start --help
      --action {review,plan,execute}
                            Require a specific action for every selected item.
                            Only 'review' is implemented: it refuses the run if
                            any selected plan's next legal action is not review,
                            so it can never execute a plan. 'plan' and 'execute'
                            are accepted by the grammar and refused as not yet
                            implemented. This is what 'aw oc review' expands to.
    ```

    `plan` AND `execute` REFUSE HONESTLY, they are not silently accepted:

    ```text
    $ python3 -m agent_workflows oc runipd torv01 --action plan --repo <fixture> --prepare-only
    runipd: --action plan is not implemented yet. Only --action review is available; plan's per-type legality table (spec 25kzda 2.6) needs the per-type dispatch this runner does not have. No run was started. To review instead, run: aw oc review <selector>
    EXIT=2

    $ python3 -m agent_workflows oc runipd torv01 --action execute --repo <fixture> --prepare-only
    runipd: --action execute is not implemented yet. Only --action review is available; execute's per-type legality table (spec 25kzda 2.6) needs the per-type dispatch this runner does not have. No run was started. To review instead, run: aw oc review <selector>
    EXIT=2

    $ python3 -m agent_workflows agy runipd torv01 --action plan --repo <fixture> --prepare-only
    runagy: --action plan is not implemented yet. Only --action review is available; plan's per-type legality table (spec 25kzda 2.6) needs the per-type dispatch this runner does not have. No run was started. To review instead, run: aw agy review <selector>
    EXIT=2

    $ python3 -m agent_workflows oc runipd torv01 --action bogus --repo <fixture> --prepare-only
    runipd start: error: argument --action: invalid choice: 'bogus' (choose from 'review', 'plan', 'execute')
    EXIT=2
    ```

    THE SAFETY HALF (F-9), WHICH IS THE POINT OF THIS ITEM. Fixture repo carrying three conforming plans: `appr01` (`Status: approved`), `revw01` (`Status: reviewed` plus an approving `- Readiness: go`, i.e. the exact shape `--full-auto` auto-clears), and `torv01` (`Status: to-review`).

    Refusing an APPROVED item, whose derived action is `execute`:

    ```text
    $ python3 -m agent_workflows oc review appr01 --repo <fixture> --prepare-only
    runipd: --action review is illegal for 1 selected item(s): appr01 (status 'approved' -> action 'execute'). Review is the next legal action only for a to-review or draft plan; an approved or reviewed plan would EXECUTE, which is not what 'review' asks for. No run was started and no session launched. To sweep only what actually awaits review, run: aw oc review
    EXIT=2
    ```

    Refusing WITH `--full-auto` ALSO PRESENT, the path that clears `reviewed` to `auto-approved` and executes:

    ```text
    $ python3 -m agent_workflows oc review revw01 --repo <fixture> --prepare-only --full-auto
    runipd: --action review is illegal for 1 selected item(s): revw01 (status 'reviewed' -> action 'execute'). Review is the next legal action only for a to-review or draft plan; an approved or reviewed plan would EXECUTE, which is not what 'review' asks for. No run was started and no session launched. To sweep only what actually awaits review, run: aw oc review
    EXIT=2
    ```

    REFUSED BEFORE ANY SESSION OR RUN DIRECTORY, proven two ways. First, no run directory was created by either refusal:

    ```text
    $ ls <fixture>/.aw/records/runs/
    ls: cannot access '<fixture>/.aw/records/runs/': No such file or directory
    ```

    Second, and more decisive for the `--full-auto` case, THE PLAN FILE WAS NOT MUTATED. If the gate had run after the auto-approval it would have written `auto-approved` into the file on its way to executing:

    ```text
    $ grep -n "^- Status:" <fixture>/.aw/records/plans/pending/20260828-demo-02-revw01-demo.ipd.md
    9:- Status: reviewed
    ```

    Both facts are pinned as tests (`test_alias_refuses_an_approved_plan_before_any_run_directory_exists`, `test_alias_refuses_a_reviewed_plan_even_with_full_auto_present`, the latter asserting the unchanged `- Status: reviewed`). Structurally, `enforce_requested_action` is called in `initialize_run` immediately after `enforce_dependency_preflight` and BEFORE both the `run_dir.mkdir` and the `status == "reviewed" and full_auto` auto-approval loop, which is why the ordering holds rather than happening to hold. The LEGAL case still works: `aw oc review torv01` exits 0 and queues one item with action `review`.

    NO BESPOKE ALIAS-ONLY CODE PATH. `expand_host_review_argv` emits the literal tokens `--action review` into the driver's argv, so the alias goes through the driver's OWN `--action` registration and the same `enforce_requested_action` any operator typing `--action review` by hand reaches. There is no alias-only branch in either runner: the runners contain no reference to `review` as a subcommand at all, and V-02(b) shows the frozen state carries `"action": "review"` identically for both spellings, which is only possible if the alias went through the flag. Both hosts' vocabularies are asserted EQUAL by `test_action_vocabulary_matches_the_oc_host`, so the two cannot drift.

    ```text
    $ python3 -m pytest tests/test_oc_runipd.py -o addopts="" -q -k ActionLegality
    ...........                                                              [100%]
    11 passed, 111 deselected

    $ python3 -m pytest tests/test_agy_runipd_cli.py -o addopts="" -q -k AgyActionLegality
    ......                                                                   [100%]
    6 passed, 33 deselected
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste an empty sweep on BOTH hosts printing a plain "nothing awaiting review" report and exiting 0, with the exit code shown explicitly (`echo EXIT=$?` or the equivalent), plus evidence that NO run directory was created. Construct the empty case with a fixture repo or `--repo`; do not wait for the live repository to be clean. Paste a misspelled id6 STILL exiting 2, which proves the exemption stayed narrow to the status selectors, and confirm the `all` branch was not touched. Quote spec 2.4a property 3 beside the observed behavior.
  - Observed evidence: All at HEAD `97d5ddf4`, against a `/tmp` fixture repo, never the live tree.

    SPEC 2.4a PROPERTY 3, quoted verbatim as the normative bar: "**An empty result is a success, not an error.** `reviews` matching nothing means the repository has nothing awaiting review, which is the healthy state and the common one. It reports that plainly and exits 0. This is the one deliberate exception to the Section 2.3 rule that zero matches exit 2, and it is justified because `reviews` is a standing question about repository state rather than an assertion that a named item exists. A misspelled id6 still exits 2; only the status selectors are exempt."

    BEFORE, on the unmodified tree, the empty sweep was a FAILURE: `expand_selectors` raised `DriverError("No items in 'to-review' state found in repository")` and `main` printed `runipd: <msg>` to stderr and returned 2.

    AFTER, empty sweep on BOTH hosts and all four host spellings, exiting 0 with a plain stdout report:

    ```text
    $ python3 -m agent_workflows oc review --repo <empty-fixture> --prepare-only
    Nothing awaiting review; no run started.
    EXIT=0

    $ python3 -m agent_workflows agy review --repo <empty-fixture> --prepare-only
    Nothing awaiting review; no run started.
    EXIT=0

    $ python3 -m agent_workflows opencode review --repo <empty-fixture> --prepare-only
    Nothing awaiting review; no run started.
    EXIT=0

    $ python3 -m agent_workflows antigravity review --repo <empty-fixture> --prepare-only
    Nothing awaiting review; no run started.
    EXIT=0
    ```

    NO RUN DIRECTORY CREATED. The fixture's records tree after all four invocations contains only `plans`, no `runs`:

    ```text
    $ ls -la <empty-fixture>/.aw/records/
    drwxr-xr-x . / drwxr-xr-x .. / drwxr-xr-x plans
    ```

    Asserted structurally by `test_end_to_end_empty_sweep_exits_zero_and_creates_no_run_directory` (oc) and `test_main_exits_zero_on_an_empty_sweep_and_creates_no_run_state` (agy), both `assertFalse((repo / ".aw" / "records" / "runs").is_dir())`. This holds by construction rather than by care: the signal is raised from `expand_selectors`, which `initialize_run` calls before it creates the run directory.

    THE EXEMPTION STAYED NARROW, three ways. (1) A misspelled id6 still exits 2 on both hosts:

    ```text
    $ python3 -m agent_workflows oc review zzzz99 --repo <fixture> --prepare-only
    runipd: No IPD plan found with id6 'zzzz99' under .aw/records/plans/.
    EXIT=2

    $ python3 -m agent_workflows agy review zzzz99 --repo <fixture> --prepare-only
    runagy: No IPD plan found with id6 'zzzz99' under .aw/records/plans/.
    EXIT=2
    ```

    (2) THE `all` BRANCH IS UNTOUCHED, confirmed by reading and by test. Its `raise DriverError("No actionable pending IPDs found in repository")` was not edited on either host; `test_the_all_selector_still_raises_a_plain_driver_error` (oc) and `test_all_selector_zero_match_is_untouched` (agy) assert `assertNotIsInstance(ctx.exception, EmptyStatusSelection)`, so `all` keeps exit 2 and a future refactor cannot silently widen the exemption to it.

    (3) Only the three status spellings raise the success type, asserted per spelling for `reviews`/`review`/`to-review`, and the new class SUBCLASSES `DriverError` (`test_the_success_subclass_is_still_a_driver_error`) so every other `except DriverError` in the package, including agy's cross-runner preflight translation, keeps catching it unchanged.

    ```text
    $ python3 -m pytest tests/test_oc_runipd.py -o addopts="" -q -k EmptyReviewSweep
    .....                                                                    [100%]
    5 passed, 117 deselected

    $ python3 -m pytest tests/test_agy_runipd_cli.py -o addopts="" -q -k AgyEmptyReviewSweep
    .....                                                                    [100%]
    5 passed, 34 deselected
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new `CommandDeclaration` entries, one per NEW LEAF SPELLING (F-12: `oc review`, `opencode review`, `agy review`, `antigravity review` if all four are registered), each with `command_class="alias"`, `empty_error_renderer="delegated"`, and `canonical_command` naming the canonical leaf. Paste the undeclared-leaf count BEFORE and AFTER, obtained by invoking the slow tests EXPLICITLY (show the invocation, since a bare `python3 -m pytest` skips them and would prove nothing). The count must not grow, and the new spellings must not appear in it. State plainly that `test_zero_undeclared_parser_leaves` was ALREADY failing with 63 undeclared leaves at HEAD, that `test_empty_error_renderer_classification_consistency` was ALREADY failing on `runs list`, and that this plan fixes neither. Then both driver suites and the bare full suite with counts, compared against your own pre-change measurement.
  - Observed evidence: All at HEAD `97d5ddf4`.

    THREE OF THIS ITEM'S PREMISES WERE STALE AT EXECUTION TIME, AND THE HONEST ANSWER IS THAT THEY NO LONGER HOLD. Recorded as DECISION 23-76gsmv-D1 rather than quietly worked around, and the item is reported against the tree as MEASURED, not as written. This is a report that the plan's baseline was BETTER than it feared, not a claim to have fixed anything the plan excluded.

    1. `test_zero_undeclared_parser_leaves` was NOT already failing. It PASSES at HEAD, before any edit of mine, and `find_undeclared_leaves(_build_parser())` returns 0, not 63.
    2. `test_empty_error_renderer_classification_consistency` was NOT already failing on `runs list`. It PASSES at HEAD.
    3. F-12's FOUR new leaves are TWO. `command_surface.discover_parser_leaves` now SKIPS a choice name that is an argparse alias of an already-seen subparser (identity test), and its own docstring documents that change as the fix for exactly the 63-leaf failure this plan cites. So `opencode review` and `antigravity review` are not separate leaves. Declaring four would have declared two phantoms, which `test_declared_absent_leaves_are_only_the_known_prompts_family` PINS as a failure, i.e. following the plan literally here would have turned a green test red.

    Also stale: "the inventory contains no host-runner entries at all". It already declares `oc runipd`, `oc update-models`, `agy runipd`, `agy exec`, `agy sessions`, and `agy view`.

    UNDECLARED-LEAF COUNT, measured three times to isolate my own contribution:

    ```text
    BEFORE any change:                    undeclared count: 0   []
    AFTER E-02, before E-05:              undeclared count: 2   ['agy review', 'oc review']
    AFTER E-05:                           undeclared count: 0   []
    ```

    So the count did NOT grow, the new spellings do NOT appear in it, and the two leaves my E-02 created are exactly the two I declared. The parser surfaces precisely those two review leaves: `['agy review', 'oc review']`.

    THE NEW DECLARATIONS, both `command_class="alias"` with the REQUIRED `empty_error_renderer="delegated"` and a `canonical_command` naming the host's canonical driver leaf:

    ```python
    CommandDeclaration(
        command="oc review",
        command_class="alias",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="delegated",
        legacy_flags=(),
        exit_contract=(0, 1, 2),
        canonical_command="oc runipd",
    ),
    CommandDeclaration(
        command="agy review",
        command_class="alias",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="delegated",
        legacy_flags=(),
        exit_contract=(0, 1, 2),
        canonical_command="agy runipd",
    ),
    ```

    THE SLOW ENFORCING TESTS, INVOKED EXPLICITLY with `-m ""` since the configured `addopts` carries `-m 'not slow'` and a bare run would skip them and prove nothing. Budgeted for minutes as the plan instructed; it took 2m18s:

    ```text
    $ python3 -m pytest tests/test_command_surface_declarations.py tests/test_cli_conformance_matrix.py -o addopts="" -q -m ""
    .........................                                                [100%]
    25 passed in 138.20s (0:02:18)
    ```

    BOTH DRIVER SUITES, green:

    ```text
    $ python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -o addopts="" -q
    ........................................................................ [ 44%]
    ........................................................................ [ 89%]
    .................                                                        [100%]
    161 passed in 19.85s
    ```

    ONE MEASUREMENT CAVEAT, STATED RATHER THAN HIDDEN. Run naively inside this driver turn, those same two suites report `13 failed, 148 passed`, every failure carrying `AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role process must not run them`. The cause is the turn's own environment, `AW_EXECUTION_ROLE=worker`, not my change: on the UNMODIFIED tree in the same shell the identical 13 fail (`13 failed, 100 passed`), and clearing that one variable makes both trees green. So the honest comparison is 100 -> 148 passed with the same 13 environment-induced failures, or 161 passed with the variable cleared. I did not modify any lifecycle-role code.

    BARE FULL SUITE, compared against my OWN pre-change measurement at the HEAD I started from, taken by stashing only my six files and re-running:

    ```text
    BEFORE (stashed):  14 failed, 4436 passed, 3 skipped, 4 xfailed in 32.94s
    AFTER:             14 failed, 4484 passed, 3 skipped, 4 xfailed in 40.35s
    ```

    The 14 failures are IDENTICAL before and after and are all in `tests/test_run_viewer.py`, the known detached-worktree phantom failures the plan itself warned about (backlog `dh0uno`); this turn runs in an isolated lane worktree, which is the documented trigger. Net effect of my change: +48 passing tests, zero new failures. Run BARE as the contract requires, with no `-n0`, no second `-q`, and no `-p no:randomly`.

    WHAT THIS PLAN DID NOT FIX, stated plainly: it declared only its own two leaves. It did not touch the `runs list` renderer classification, did not sweep other declarations, and did not change what the sweep SELECTS. After this plan the sweep still covers IPDs only and still misses complete drafts (`6ypimw` and `5slbpi` own those).

    Lint and leak gates on the changed files:

    ```text
    $ python3 -m ruff check --select E4,E7,E9,F <the six changed files>
    All checks passed!
    $ python3 -m ruff format --check <the six changed files>
    6 files already formatted
    $ python3 -m agent_workflows check-local-leaks . --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 5 E-leaves, one concern: make an existing capability discoverable, give it the declared spelling, and make that spelling honest. E-01 is the documentation pass, E-02 the alias, E-03 its one real dependency plus the refusal that keeps a review verb from executing code, E-04 the exit code of the path the new verb makes common, E-05 the surface declaration the repo's own CI check requires. E-02 and E-03 are separate because the alias's target flag does not exist, and conflating them would let a green "alias works" hide a bespoke code path that bypassed `--action` entirely. E-04 is separate because it is the one behavior change in the plan and must be independently provable.
- Right-sizing re-checked at review: each E-item is one deliverable with one test surface. E-01 is help text across five sites but one deliverable (the same sentence, five places) with one V-item. E-03 carries two clauses (register the flag, refuse an illegal action) that cannot be split because the refusal is meaningless without the flag and the flag is unsafe without the refusal.

Open questions: OQ-01 (verb spelling) is non-blocking with a recorded default and a stated reason. No blocking question remains.

This plan is `to-review` and requires explicit human approval before execution. It has NO plan dependencies (`- Item-Dependencies: none`) and deliberately does not wait on `rununify`: it touches help strings, one argv rewrite at the `cli` host seam, one flag registration, and one exit-code branch, not the structures that consolidation is moving. It must not run CONCURRENTLY with `uyeko5` or `ki6tom`, which edit the same parser functions. NOTE THE SEQUENCING RISK WITH `uyeko5`, which is already `approved`: if it lands first it may itself register `--action` (it says it will not), so E-03 must LOOK before it declares, and if `--action` already exists E-03 becomes pure wiring plus the refusal.

Scope fence: touch ONLY `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/cli.py`, `agent_workflows/command_surface.py`, `tests/test_oc_runipd.py`, and `tests/test_agy_runipd_cli.py`. Do NOT change what the sweep SELECTS (`6ypimw` owns the predicate). Do NOT extract or edit the duplicated `_needs_review` closures; E-04 changes only what happens when their result is EMPTY, not who is in the set. Do NOT add prose to the `/plan-review` prompt, which must remain the bare slash command and its path. Do NOT implement `--action`'s full per-type legality table. Do NOT change the `all` selector's zero-match behavior. Do NOT declare the other 62 undeclared command-surface leaves or fix the red `runs list` renderer classification. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. The load-bearing evidence is V-02's TWO halves (the verb is REACHABLE, and it is INDISTINGUISHABLE from the canonical invocation) plus V-03's refusal proof, because "the alias works" is exactly what both a forked alias and an unsafe one would also demonstrate. Do NOT report the command-surface declarations test as passing: two of its tests are already red and both enforcing files are `slow`, so a green bare suite says nothing about them. Do NOT claim the sweep covers specs or complete drafts; it covers neither after this plan.

Execution contract: RE-READ both runner modules and `cli.py` immediately before editing and locate every site BY SYMBOL, never by the line numbers in this plan: these are the highest-contention files in the repo, 11 other unexecuted plans declare them, and the oc citations in this plan ALREADY drifted once by roughly 38 lines when `818uru` restructured the module (they were refreshed at review to HEAD `800b6dc5` and will drift again). NEVER run a bare live sweep to "check" something: `aw oc runipd reviews` starts real agent sessions against the repository's live `to-review` plans (measured during this review, which started two unintended runs). Use `--prepare-only` or a fixture repo for every exploratory invocation. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption, since a failed hook invalidates the check. If a co-worker's in-flight change cannot be safely combined with an edit, STOP and report rather than overwriting.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
