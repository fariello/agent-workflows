# IPD: Give every dependency-block producer the recovery hint by threading it from the host descriptor

- Date: 2026-09-29
- Kind: child
- Concern: An operator whose item was blocked by `cascade_dependency_blocked` (or by an orchestrator TERMINATE) reads a `## Dependency blocks (why)` section with NO `- Recovery:` line, while a drain-blocked item in the same report gets one, even though BOTH need the identical `--retry-incomplete` flag to re-queue. The three producers of `unsatisfied_dependencies` agree on two keys and disagree on the third.
- Scope: IN: (a) a new `HostLabels` field carrying the dependency-block recovery hint, composed per host from the existing `command` so the two hosts' texts stop being two module-level constants; (b) an OPTIONAL `recovery_hint=` parameter on `runner_shared.cascade_dependency_blocked` and on `runner_shared.dispatch_orchestrator_item`, defaulting to `None` and preserving today's output byte-for-byte when unsupplied; (c) both hosts passing their descriptor's hint at the call sites they already own; (d) both drain arms reading the hint from the descriptor instead of the host-local constant, deleting the two divergent constants; (e) behavioral tests pinning that all three producers now write the key and that the report renders one `- Recovery:` line per blocked item naming the CORRECT host. OUT: deleting the `if d in why` conditionals in `derive_item_disposition` and `render_stream` (the backlog's suggested second half, measured in F-04 to be a REGRESSION against frozen records), changing the `dependency-blocked` event's key set, rewriting any frozen `state.json`, and the `not in this run` mislabel (`8mohre`/`zhqt51`) or the doubled-token verbosity (`csjq81`).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_dependency_block_reporting.py, tests/test_hostdedup_third_host.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: mjrac4
- Set: mjrac4
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 8eei5p
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (aw set): status set to reviewed

- 2026-09-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-401, PR-402 (MEDIUM), PR-403 (LOW), all FIXED. Reviewed at lane HEAD `63c7da25`. Every material claim RE-MEASURED rather than read, and the plan's argument held throughout: F-01's staleness claim reproduces (the cascade writes a bare token plus a populated reasons map and no recovery key, so the backlog item's headline is indeed two thirds closed); F-02 reproduces end to end through the real `write_report`, a drain item rendering `- Recovery:` and an otherwise-identical cascade item rendering none; F-03's two host constants differ only in `aw oc` versus `aw agy` and compare unequal; F-04's blanket fallback reintroduces `executed:aaa111 (target reviewed) (unsatisfied)` and both shipped assertions it names exist; F-06's TERMINATE path writes the two dependency keys and no recovery key; F-07's `children-unfinished` remedy is verbatim; F-08's `fail-depend` is in the requeue set with both exclusions False for all three producers; F-10's single pinning assertion and the event-key equality are both present; F-13's ten-field literal `SCRIPTED_HOST_LABELS` and the `_fields`-derived construction that needs no edit are both as described; F-15 finds no spec mentioning the section; and all five cited carriers are in their stated states, including the RETRACTED, now-`parked` `phawyy`. TWO SUBSTANTIVE CORRECTIONS. (1) MEDIUM PR-401: E-03's prose said "Five test call sites" while F-11 in the same plan says NINE and E-03's own parenthetical lists seven files. The measured figure is nine invocations across six files; E-03 now carries the per-file breakdown and F-11 states its counting rule, so an executor cannot under-count what a required parameter would break. (2) MEDIUM PR-402: E-05 instructed the executor to "run the host's `retry_incomplete` requeue path" and V-05(c) required "naming the function called", and there is NO such callable - the branch is inline in each host's `run_queue` and the only requeue function in either host or `runner_shared` is `requeue_interrupted`, a different route. As written the two clauses could be satisfied only by fabricating a function name or by the re-implementation V-05 itself forbids. E-05 now names two acceptable routes (end-to-end `resume --retry-incomplete`, or predicate-level with the limitation declared) and V-05 requires the route be stated; review also measured the expected answer, so the executor confirms rather than derives it (new F-18). LOW PR-403 re-labelled the stale suite baseline after measuring `3284 passed, 2 skipped` against the authored `3246 passed, 2 skipped`. Review added F-18 through F-21 and F-08b, recording that the three-write-site census E-02 must re-home is where the plan says and its item 1 says exactly what E-02 claims, that all three descriptor guardrails hold as assumed, that the report section gates on the canonical status plus either dependency key so the additive write needs no consumer change, and that `write_report` requires `setid` on every probe item. Structural preflight `aw ipd lint` conforming at `author` and `review-finalize`.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `mjrac4`. THE ITEM'S HEADLINE CLAIM IS STALE AND THE PLAN SAYS SO RATHER THAN RESTATING IT (F-01): plan `5o1jye` already made the cascade write a bare token plus a reasons map, so the two-shape divergence the item describes is two thirds closed at HEAD `5d06997e`. What survives is narrower and is measured in F-02/F-03. THE ITEM'S SUGGESTED FIX IS ALSO HALF WRONG AND IS REJECTED WITH A MEASUREMENT (F-04): deleting the consumer conditionals, which the item proposes, reintroduces the double parenthetical on frozen records that `5o1jye` E-03 deliberately removed. The plan therefore delivers the item's STATED GOAL (one shape, no consumer special case owed) by finishing the producer side and explicitly declining the consumer side, and it resolves the item's open migration question from repository evidence (OQ-02).
- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

An operator reading `## Dependency blocks (why)` must be told HOW TO RECOVER for every blocked item,
not only for the ones the drain arm happened to label. Today the recovery line is attached by exactly
one of three producers, so the report's helpfulness depends on which internal code path blocked the
item - a distinction the operator cannot see and does not care about. The recovery action is the SAME
in all three cases (`--retry-incomplete`), so the omission is not a difference in truth but a gap in
reporting.

Close the gap at the only place it can be closed once: put the hint on the `HostLabels` descriptor,
which is the repository's established home for a string that legitimately differs per host, and let
every producer receive it as an argument. That simultaneously deletes the two divergent module-level
constants, which is the shape `test_no_divergent_codefined_constants_in_runner_shared` exists to
police and which `runner_shared.orchestrator_uncovered_work_remedy`'s docstring already names as the
pattern to follow.

WHAT THIS PLAN DOES NOT DO, stated here because the backlog item asks for it and the measurement says
no. It does NOT delete the `if d in why` conditionals in `derive_item_disposition` and
`render_stream`. F-04 measures that those conditionals are no longer special cases for a divergent
PRODUCER (no producer writes the embedded-reason shape at HEAD) but are the frozen-record repair
`5o1jye` E-03 landed deliberately, and deleting them re-creates the `(target reviewed) (unsatisfied)`
double parenthetical on run directories already on disk. So the item's goal "no consumer needs a
special case" is reached by a different route than the item guessed: after this plan there is no
PRODUCER divergence left for a consumer to special-case, and the surviving conditional is a
back-compatibility reader, which is a different and legitimate thing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: give the hint one home

- [ ] E-01 Add a `dependency_block_recovery` field to `runner_shared.HostLabels` carrying that host's
  dependency-block recovery hint, and populate it on `OC_HOST_LABELS` and `AGY_HOST_LABELS` with the
  two texts the hosts define today, verbatim, so no operator-facing string changes in this item.

  A FIELD RATHER THAN A DERIVATION FROM `command`, and the reason is already written down twice in
  this exact class: both `review_command` and `full_auto_actor` are fields whose comments state that
  deriving one operator-facing command from another by string surgery "re-introduces the implicit
  coupling this descriptor exists to delete, and it would break silently the day a host spells its
  command differently". Note the hints spell the command `aw oc runipd resume` while
  `HostLabels.command` is `aw oc run`, so the two are not even the same string today; a derivation
  would have to invent the `ipd`/`resume` surgery and would be wrong for a third host. Add NO DEFAULT,
  for the reason the class docstring gives: a `NamedTuple` field without a default raises `TypeError`
  at construction, which is what makes a new host declare the string rather than silently inherit an
  empty one.
  - Depends on: none
  - Expected outcome: `runner_shared.HostLabels._fields` contains `dependency_block_recovery`;
    `OC_HOST_LABELS.dependency_block_recovery` and `AGY_HOST_LABELS.dependency_block_recovery` equal
    the strings `oc_runipd.DEPENDENCY_BLOCK_RECOVERY_HINT` and
    `agy_runipd.DEPENDENCY_BLOCK_RECOVERY_HINT` hold at HEAD, byte for byte; constructing
    `HostLabels` without the new field raises `TypeError`.
  - Execution state: pending

- [ ] E-02 Point both hosts' drain arms at the descriptor field and DELETE the two module-level
  `DEPENDENCY_BLOCK_RECOVERY_HINT` constants from `oc_runipd` and `agy_runipd`. Each drain arm already
  has its host's labels available at that point in `run_queue`; read the hint from there for both the
  item key (`item["dependency_block_recovery"]`) and the event key (`"recovery"`).

  PRESERVE THE TWO CONSTANTS' EXPLANATORY COMMENTS by moving them, not deleting them. The `oc_runipd`
  comment above the constant is the repository's only written census of the THREE WRITE SITES FOR THIS
  STATUS and their permanence classifications, and the `agy_runipd` one cross-references it; that
  census is the reason this plan could be scoped, so losing it to a refactor would be a real cost.
  Re-home the census next to the new `HostLabels` field or beside `cascade_dependency_blocked`, and
  UPDATE its item 1, which currently says the cascade is "CORRECT AS WRITTEN; deliberately unchanged
  by `akzy45`" - true then, and this plan changes it.
  - Depends on: E-01
  - Expected outcome: `rg -n 'DEPENDENCY_BLOCK_RECOVERY_HINT' agent_workflows/` reports no
    module-level assignment in either host; a drain-blocked item's `dependency_block_recovery` and its
    event's `recovery` both still carry that host's exact text; the three-write-site census survives
    in the tree with item 1 corrected.
  - Execution state: pending

### Task group 2: give the other two producers the hint

- [ ] E-03 Add a keyword-only `recovery_hint: str | None = None` parameter to
  `runner_shared.cascade_dependency_blocked` and write `item["dependency_block_recovery"] =
  recovery_hint` ONLY when it is truthy. Pass the host's descriptor field at both call sites
  (`oc_runipd.run_queue` and `agy_runipd.run_queue`, each currently calling
  `cascade_dependency_blocked(state, run_dir)`).

  THE `None` DEFAULT IS LOAD-BEARING AND IS NOT TIDINESS. NINE test call sites invoke this function
  with no hint (review-corrected from "Five", which contradicted F-11 in the same plan and did not even
  match this item's own list of seven filenames - PR-401). Measured at review, the nine invocations are:
  `tests/test_dependency_block_reporting.py` (2), `tests/test_terminal_status_vocabulary.py` (2),
  `tests/test_runner_shared.py` (2), `tests/test_host_capability_wiring.py` (1),
  `tests/test_orchestrator_retirement.py` (1), and `tests/test_oc_runipd.py` (1);
  `tests/test_finalize_sendback.py` names the symbol in an object-identity pin and does NOT call it,
  which is why it is listed in F-11 but not counted here. One of the nine
  (`test_cascade_producer_output_shape`) ASSERTS `dependent.get("dependency_block_recovery") is None`.
  With a `None` default and a truthiness guard, that assertion keeps passing unchanged, which is what
  makes this item safe to land before E-06 updates the test.

  WRITE NO OTHER KEY. Specifically do NOT add `reasons`, `recovery`, `block_class` or `block_detail`
  to the `dependency-blocked` EVENT this function emits.
  `tests/test_dependency_block_reporting.py::test_cascade_producer_output_shape` asserts
  `set(ev.keys()) == {"at", "event", "id6", "dependencies", "reason"}` by EQUALITY, so an added event
  key turns it red; and the event's key set is not what the backlog item is about. The ITEM key is the
  one the report reads.
  - Depends on: E-01
  - Expected outcome: called with no `recovery_hint`, the function's output is byte-identical to HEAD's
    including the absent key; called with a hint, a cascade-blocked item carries
    `dependency_block_recovery` equal to that hint; the emitted event's key set is unchanged in both
    cases.
  - Execution state: pending

- [ ] E-04 Add the same keyword-only `recovery_hint: str | None = None` parameter to
  `runner_shared.dispatch_orchestrator_item` and write the key on the TERMINATE path only, beside the
  `unsatisfied_dependencies`/`unsatisfied_dependency_reasons` pair it already writes there. Pass the
  descriptor field from both hosts' call sites.

  THE RECONSIDER PATH MUST NOT RECEIVE IT, and this is the one place in the plan where a wrong edit
  would produce a false statement rather than a missing one. RECONSIDER deliberately writes NO status
  and leaves the item `queued`, which is the transient case; `TRANSIENT_DEPENDENCY_WAIT_HINT` records
  in terms an executor can check that such an item "needs no flag at all" and that saying
  "use --retry-incomplete" there "would send the operator to a flag they do not need". Only the
  TERMINATE path writes a terminal status, and only it is the case `--retry-incomplete` re-queues.
  - Depends on: E-01
  - Expected outcome: an orchestrator item the TERMINATE path blocked carries
    `dependency_block_recovery`; an item the RECONSIDER path left `queued` does NOT carry it and
    retains its `transient_dependency_wait` record with its own `recovery` text; both are byte-
    identical to HEAD when no hint is passed.
  - Execution state: pending

- [ ] E-05 Confirm BY MEASUREMENT, not by reading the source, that `--retry-incomplete` actually
  re-queues an item each of the three producers blocks, so the hint this plan attaches is TRUE for all
  three and not merely uniform. Build a run state for each producer's output and establish, for each,
  whether its item returns to `queued`.

  **THE REQUEUE LOGIC IS INLINE IN `run_queue` AND IS NOT A CALLABLE, SO SAY HOW YOU MEASURED IT (PR-402, F-18).**
  Review looked for an extractable helper and there is none: the `if retry_incomplete:` block lives in
  the body of each host's `run_queue`, and the only requeue FUNCTION in either host or in
  `runner_shared` is `requeue_interrupted`, which is the DIFFERENT (interrupted-prerequisite) route.
  So "run the host's `retry_incomplete` requeue path over it" is not directly executable as written,
  and V-05's demand that you drive the real branch while not re-implementing its status set cannot both
  be met by a unit probe. TWO ACCEPTABLE ROUTES, and you must name which you took. (1) END TO END:
  drive a real `aw <host> run ... resume --retry-incomplete` over a prepared run directory, so the
  shipped branch executes, and report the statuses before and after. (2) PREDICATE-LEVEL, which is
  weaker and must be labelled as such: evaluate the two exclusions (`runner_stop.is_indeterminate(item)`
  and `item.get("action") == "skip"`) against each producer's real item and read the status set from the
  shipped source rather than retyping it, stating explicitly that you did NOT execute the loop. Route
  (1) is preferred; route (2) is acceptable only with the limitation stated in the evidence.

  THIS ITEM EXISTS BECAUSE A UNIFORM LIE IS WORSE THAN AN HONEST GAP. The plan's whole premise is that
  the recovery action is identical across producers; if the requeue predicate excluded one of them,
  attaching the same hint would tell an operator to run a flag that will not help. The requeue branch
  gates on `item["status"] in {...}` plus the two exclusions above, and all three producers write
  `fail-depend`, so the expected answer is that all three requeue. Review measured the two exclusions
  returning False for all three producers' real item shapes and confirmed `fail-depend` is in the
  shipped status set (F-18), so the expected answer is now evidenced rather than predicted; your job is
  to confirm it at execution HEAD by whichever route you name.
  - Depends on: E-03, E-04
  - Expected outcome: a written record, in this plan's V-05 evidence, NAMING THE ROUTE TAKEN and showing
    for each of the three producers whether its blocked item returns to `queued`; if any does NOT, E-03
    or E-04 is revised to withhold the hint from that producer rather than shipping a false instruction.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-06 Update `tests/test_dependency_block_reporting.py::test_cascade_producer_output_shape`,
  whose `assert dependent.get("dependency_block_recovery") is None` is the shipped assertion that PINS
  the divergence this plan removes. Split it: keep a no-hint case asserting the key is absent (that is
  E-03's default-preservation property and is worth keeping), and add a with-hint case asserting the
  key equals the supplied string. Leave the event-key equality assertion untouched in both; it is what
  guards E-03's "write no other key" prohibition.

  Also add cases for the properties E-04 and E-02 establish: an orchestrator TERMINATE item carries the
  key, a RECONSIDER item does not, and `write_report` renders exactly ONE `- Recovery:` line per
  blocked item for each of the three producers. Assert the rendered REPORT TEXT and the returned
  values, never by reading production source.
  - Depends on: E-03, E-04
  - Expected outcome: the module covers all three producers for the recovery key in both the
    hint-supplied and hint-absent directions, plus the report rendering, and every new case fails when
    its corresponding E-item is reverted.
  - Execution state: pending

- [ ] E-07 Add the new field to `tests/test_hostdedup_third_host.py`'s `SCRIPTED_HOST_LABELS`, which
  constructs `HostLabels` by keyword and will raise `TypeError` at IMPORT TIME once E-01 lands a
  field with no default. Give it a `scripted`-flavored value consistent with the other fields in that
  descriptor.

  THIS IS NOT INCIDENTAL TEST MAINTENANCE: that module is the proof that a third host can exist as a
  descriptor alone, so the new field is precisely the kind of thing it is there to catch. An executor
  who discovers this as a collection error rather than as a planned edit is likely to reach for a
  default on the field instead, which would defeat E-01's `TypeError`-on-omission property. Note that
  `tests/test_runner_shared.py::test_set_plan_approved_durable_history_pin` builds a kwargs dict from
  `HostLabels._fields` programmatically and so needs NO edit; confirm that rather than assuming it.
  - Depends on: E-01
  - Expected outcome: `tests/test_hostdedup_third_host.py` imports and passes; the `TypeError`-on-
    omission assertion in `tests/test_runner_shared.py` still passes with no edit to that file.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A STRING THAT LEGITIMATELY DIFFERS PER HOST BELONGS ON `HostLabels`, NOT IN A PER-HOST CONSTANT, and
  this is written down rather than inferred. `runner_shared.orchestrator_uncovered_work_remedy`'s
  docstring states the rule with this very constant as its example: "The rendered strings legitimately
  DIFFER per host because each names its own host's command, exactly as
  `DEPENDENCY_BLOCK_RECOVERY_HINT` does; what must be ONE object is this function." So the repository
  has already classified this constant as belonging to that pattern; this plan applies the
  classification it was given.
- THE DIVERGENT-CONSTANT GUARD IS MECHANICAL AND THIS PLAN MUST NOT TRIP IT.
  `tests/test_runner_shared.py::test_no_divergent_codefined_constants_in_runner_shared` AST-collects
  every UPPER_CASE module-level assignment co-defined in all three of `runner_shared`, `oc_runipd` and
  `agy_runipd` and fails when the shared value matches neither host's. `HostLabels.full_auto_actor`'s
  comment records the measured incident behind it: a shared `FULL_AUTO_ACTOR` matching NEITHER host
  would have made every Antigravity auto-approval record that `aw oc run` did it. So E-01/E-02 must
  NOT introduce a `DEPENDENCY_BLOCK_RECOVERY_HINT` in `runner_shared`; the descriptor field is the
  correct shape and the constants are deleted rather than lifted.
- `HostLabels` FIELDS CARRY NO DEFAULTS BY DESIGN. Its class docstring states the reason ("A
  `NamedTuple` raises `TypeError` on a missing field at construction ... a plain mapping with `.get()`
  is the one form this must not be") and `tests/test_runner_shared.py` pins it by constructing the
  tuple with one field omitted inside `assertRaises(TypeError)`. E-01 follows this; E-07 is the
  consequence.
- ADDITIVE KEYS, NEVER RESHAPED ONES. Both drain arms carry the comment that
  `unsatisfied_dependencies` "keeps its exact shape and meaning, so every existing consumer is
  untouched; the reasons live alongside it", and `5o1jye` recorded a Carrier-Declined row stating that
  changing the key name or the event name is the wrong move and that the retained event name "is KEPT
  for continuity with the 28 already on disk". This plan adds one item key to two producers and
  changes no name, no shape and no event.
- A RUN RECORD IS NEVER REWRITTEN IN PLACE. `5o1jye`'s Deferred section states it as a committed
  contract with a Carrier-Declined rationale: legacy records stay READABLE and "a plan that mutated
  durable history would be the defect". OQ-02 applies it to this plan's own migration question.
- CITE BY SYMBOL. Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line
  number only appended to one of those and never alone: an offset expires before this plan executes
  (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | **THE BACKLOG ITEM'S HEADLINE CLAIM IS STALE AND MUST NOT BE REPEATED AS PRESENT-TENSE FACT.** The item says `cascade_dependency_blocked` "writes the reason INTO the token (`executed:aaa111 (target failed-safely)`) and writes NO `unsatisfied_dependency_reasons` map". Both halves are FALSE at HEAD `5d06997e`: plan `5o1jye` (executed 2026-09-28, `- From-Backlog: fvsyqk`) landed exactly the item's suggested producer fix in its E-01. Measured live by CALLING the function: `deps: ['executed:aaa111']`, `reasons: {'executed:aaa111': 'target aaa111 is failed-safely'}`. So two of the three keys already agree and the item is two thirds closed by work it did not know about. | Ran `cascade_dependency_blocked` against a two-item state with a `failed-safely` prerequisite and printed the resulting item keys; read of `5o1jye`'s E-01 ("make the dependency TOKEN bare") and of its `- Status: executed`. |
| F-02 | **WHAT SURVIVES IS EXACTLY ONE ITEM KEY, AND IT HAS A USER-VISIBLE CONSEQUENCE.** The drain arms write a third key, `item["dependency_block_recovery"]`, which the cascade and `dispatch_orchestrator_item` do not. `runner_shared.write_report`'s `## Dependency blocks (why)` section reads it (`hint = item.get("dependency_block_recovery")`, then `- Recovery: {hint}`) and is the ONLY reader of that key in the package. So the same report gives a drain-blocked item a recovery line and a cascade-blocked one none. Measured side by side: the cascade item renders two lines ending at its reason, the drain item renders a third `- Recovery: resolve the named cause, then re-queue with \`aw oc runipd resume ... --retry-incomplete ...\``. | Built both item shapes, called the real `write_report` with `labels=OC_HOST_LABELS` for each, and pasted both `## Dependency blocks (why)` sections; `RECOVERY LINE PRESENT: False` then `True`. `rg -n 'dependency_block_recovery' agent_workflows/` lists the two drain writes and this single read. |
| F-03 | **THE HINT IS NOT ONE OBJECT ACROSS HOSTS, WHICH IS WHY THE FIX IS A DESCRIPTOR FIELD AND NOT A SHARED CONSTANT.** `oc_runipd.DEPENDENCY_BLOCK_RECOVERY_HINT != agy_runipd.DEPENDENCY_BLOCK_RECOVERY_HINT` (measured `False` on equality): each names its own host's resume command (`aw oc runipd resume` versus `aw agy runipd resume`). `5o1jye`'s F-13 identified this as the blocker that stopped it unifying the third key and named THIS backlog item as the carrier. A shared constant is additionally forbidden by the divergent-constant guard (see Conventions). | `python3` comparison printing both strings and `equal: False`; read of `5o1jye` F-13 ("there is no single value the shared cascade could adopt without inventing a host-neutral wording ... Backlog `mjrac4` remains the carrier"). |
| F-04 | **THE ITEM'S SUGGESTED SECOND HALF IS A REGRESSION AND IS REJECTED ON MEASUREMENT.** The item says to "delete the special cases in `derive_item_disposition` and `render_stream`". Those conditionals are no longer producer special-cases: no producer writes the embedded-reason shape at HEAD (F-01), and `5o1jye` E-03 re-aimed the `render_stream` one at FROZEN RECORDS specifically, recording that its live effect is on "run directories already frozen on disk". Deleting them re-creates the double parenthetical on those records. Measured against a frozen-shape item: shipped `derive_item_disposition` yields `unmet: executed:aaa111 (target reviewed)` while the blanket fallback yields `executed:aaa111 (target reviewed) (unsatisfied)`; shipped `render_run_summary_table` yields `• eee555: dependency-blocked (executed:aaa111 (target reviewed))` while the deleted-conditional form yields the same with a trailing `(blocked)`. `tests/test_dependency_block_reporting.py::test_frozen_record_no_duplicate_parenthetical_or_blocked` asserts `"(blocked)" not in out` and `tests/test_run_selection_policy.py`'s inline-reason row forbids `(unsatisfied)`, so the deletion would also turn two shipped tests red. | Composed both expressions over `deps=['executed:aaa111 (target reviewed)']` with an empty reasons map and pasted both outputs; called the real `render_run_summary_table` on that item and pasted its diagnostic line; read of the two shipped assertions. |
| F-05 | **THE SURVIVING CONDITIONALS COST NOTHING ONCE THE PRODUCERS AGREE, so declining to delete them does not leave the item's goal unmet.** The item's stated goal is that "a consumer cannot render either shape generically" and "every consumer needs a special case". After this plan, every PRODUCER writes bare token + reasons map + recovery hint, so a consumer reading a live record needs no branch at all; the `if d in why` test is simply never false for such a record. What remains is a back-compat reader for frozen records, which is the same shape `TERMINAL_STATUS_ALIASES` uses for the retired `dependency-blocked` spelling and which the repository treats as correct rather than as a wart. The honest claim this plan may make is "no producer divergence remains", never "the conditionals were removed". | Read of `derive_item_disposition`'s dependency arm (the conditional is `if d in why`, i.e. a presence test that a complete map always satisfies); read of `TERMINAL_STATUS_ALIASES` and of `render_stream`/`write_report` each already accepting both status spellings. |
| F-06 | **THERE IS A THIRD PRODUCER THE ITEM DOES NOT MENTION, AND IT HAS THE SAME GAP.** `runner_shared.dispatch_orchestrator_item`'s TERMINATE path writes `unsatisfied_dependencies` (`f"executed:{child}"` per unfinished child) and `unsatisfied_dependency_reasons` (`f"child {child} is {st}"`) and no recovery key. Measured: its report section renders the per-child reason and no `- Recovery:` line. It is shared, so it reaches both hosts. This is why E-04 exists and why the plan's title says "every producer" rather than "the cascade". | Built the item exactly as that function writes it, called `write_report`, pasted the section, `RECOVERY PRESENT: False`; read of the function's TERMINATE block. |
| F-07 | **THE ORCHESTRATOR CASE ALREADY GETS A REMEDY BY A DIFFERENT ROUTE, WHICH BOUNDS E-04's VALUE HONESTLY.** That same TERMINATE path calls `record_refusal` with a `remedy` from `orchestrator_refusal_text`, and those remedies are substantial and specific (for `children-unfinished`: "let the run reach those children ... approve it with `aw ipd set approved <id6> --by-human` ..."). `render_stream`'s refusal branch precedes its dependency arm and renders that remedy, so the summary table already advises the operator for this producer. What E-04 adds is the `write_report` section's `- Recovery:` line, which is a DIFFERENT surface and is absent today. So E-04 closes a real gap on one surface and must not be described as rescuing an item that had no advice at all. | Called `orchestrator_refusal_text` for all three refusal codes and pasted the remedies; read of `render_stream`'s `elif refusal is not None` branch preceding the `elif st in ("fail-depend", "dependency-blocked")` arm; F-06's measurement that the REPORT section has no recovery line. |
| F-08 | **THE RECOVERY ADVICE IS GENUINELY THE SAME FOR ALL THREE PRODUCERS, which is the premise the whole plan rests on.** The `retry_incomplete` branch in each host's `run_queue` requeues on `item["status"] in {...}`, a set containing both `dependency-blocked` and `fail-depend`, minus two exclusions (`runner_stop.is_indeterminate(item)` and `action == "skip"`). All three producers write `fail-depend` (the cascade and the drain arm literally, `dispatch_orchestrator_item` via its `terminal_status: str = "fail-depend"` default). So the same flag recovers all three and a uniform hint is truthful. E-05 MEASURES this rather than resting on this read, because the premise is load-bearing. | Read of the `if retry_incomplete:` branch and its status set; read of the three write sites' status values; `canonical_terminal_status` mapping the legacy token to `fail-depend`. |
| F-09 | **THE FIX IS PROTOTYPED AND MEASURED TO WORK, INCLUDING ITS DEFAULT-PRESERVATION PROPERTY.** A scratch reimplementation of `cascade_dependency_blocked` taking `recovery_hint=` was run three ways and its report section pasted each time: with the oc hint the section gains `- Recovery: ... aw oc runipd resume ...`; with the agy hint it gains the `aw agy runipd resume` wording; with the default `None` the section is identical to HEAD's, with no recovery line. So E-03's "byte-identical when unsupplied" claim is measured before being prescribed, and the per-host correctness of the threading is measured too. | Scratch prototype under `tmp/prmjrac4/`, run over one state per host plus a `None` case, with all three `## Dependency blocks (why)` sections pasted from the real `write_report`. |
| F-10 | **EXACTLY ONE SHIPPED ASSERTION PINS THE DIVERGENCE THIS PLAN REMOVES, and an executor who does not know that will read a red test as their own bug.** `tests/test_dependency_block_reporting.py::test_cascade_producer_output_shape` asserts `dependent.get("dependency_block_recovery") is None`, with the docstring "cascade_dependency_blocked writes bare tokens, parallel reasons, and no recovery". It was written by `5o1jye` E-05 to pin the boundary that plan deliberately drew. Because E-03 defaults to `None` and guards on truthiness, that assertion keeps PASSING through E-03 and only changes when E-06 splits it, so the two items can land in either order without a spurious red. | Read of the test and its docstring; read of `5o1jye` E-01's prohibition ("Specifically do not add `dependency_block_recovery`") that the assertion enforces. |
| F-11 | **NINE TEST CALL SITES INVOKE `cascade_dependency_blocked` WITH NO HINT, so a required parameter would be a wide and needless break.** RE-MEASURED AT REVIEW AND CONFIRMED AT NINE, with the per-file breakdown now stated so the number is checkable rather than asserted: `tests/test_dependency_block_reporting.py` 2, `tests/test_terminal_status_vocabulary.py` 2, `tests/test_runner_shared.py` 2, `tests/test_host_capability_wiring.py` 1, `tests/test_orchestrator_retirement.py` 1, `tests/test_oc_runipd.py` 1. `tests/test_finalize_sendback.py` names the symbol in an object-identity pin and does NOT invoke it, so it is affected by F-12 rather than counted here. Keyword-only with a `None` default leaves every one of them untouched. NOTE E-03's prose said "Five" and is corrected (PR-401); this row was right. | A scripted count over `git ls-files 'tests/*.py'` matching `cascade_dependency_blocked\s*\(` and excluding `def ` lines, printing every hit with its file, line number and source line, totalling 9; the `test_finalize_sendback.py` reference read and classified as a non-call. |
| F-12 | **THE OBJECT-IDENTITY PIN BETWEEN THE TWO HOSTS' RE-EXPORTS MUST KEEP HOLDING, and E-03 preserves it for free.** `tests/test_finalize_sendback.py` asserts `oc_driver.cascade_dependency_blocked is agy_driver.cascade_dependency_blocked`; both hosts re-export the shared symbol rather than defining it. Adding a parameter to the one shared definition cannot break that; defining a per-host wrapper would. So E-03 must add the parameter to the shared function and must NOT introduce host wrappers around it. | Read of the assertion and of both hosts' re-export lines (`cascade_dependency_blocked as cascade_dependency_blocked`). |
| F-13 | **A THIRD TEST MODULE BREAKS AT IMPORT TIME FROM E-01 ALONE, and it is not obvious from the diff.** `tests/test_hostdedup_third_host.py` builds `SCRIPTED_HOST_LABELS = runner_shared.HostLabels(...)` at MODULE level with all ten current fields by keyword; a new field without a default makes that a `TypeError` during collection, failing the module wholesale rather than one test. By contrast `tests/test_runner_shared.py::test_set_plan_approved_durable_history_pin` derives its kwargs from `HostLabels._fields` and needs no edit. E-07 handles the first and verifies the second. | Read of both constructions: one literal keyword list, one `{f: f"val_{f}" for f in runner_shared.HostLabels._fields if f != "full_auto_actor"}`. |
| F-14 | **NO PENDING PLAN DECLARES `tests/test_dependency_block_reporting.py` AS A WRITE TARGET EXCEPT ONE, AND IT IS DISJOINT FROM THIS PLAN'S EDIT.** `jefifu` (`- Status: reviewed`, `- Scope-Paths: tests/test_dependency_block_reporting.py`) repoints `test_drain_and_cascade_mapped_reasons_rendered_once`'s dependency token at a synthesized repo root and adds negative-substring guards to THAT test. This plan edits `test_cascade_producer_output_shape` and adds new cases. Different test functions in the same file, and per AGENTS.md the runner isolates each item in its own worktree and merges through a revalidation gate, so the shared file is not a hazard; the honest statement is that the two edits touch different functions. `zhqt51` (`reviewed`) declares the same five production paths this plan touches but edits `derive_item_disposition`'s code SELECTION and `edge_satisfied`'s refusal WORDING, neither of which this plan reads or writes. | `rg -l` over `.aw/records/plans/pending/` for each of this plan's `- Scope-Paths:` entries, then read of each hit's `- Scope-Paths:` and E-items. |
| F-15 | **THE `## Dependency blocks (why)` SECTION IS NOT SPEC-GOVERNED, so no spec amendment is owed.** `rg` for `dependency_block_recovery` and for the section heading across `.aw/records/specs/` returns nothing. The section was introduced by `revgate` `7nkcgp` E-04 as a report improvement. So this plan declares no `.spec.md` path (see Spec sync). | `rg -rn 'dependency_block_recovery\|Dependency blocks \(why\)' .aw/records/specs/` returning no matches; read of the section's in-code provenance comment naming `7nkcgp` E-04. |
| F-16 | **NO RUN RECORD EXISTS IN THIS WORKTREE TO MIGRATE, and the per-item schema could not gate a migration anyway.** `.aw/records/runs` is absent here and `.aw/state/runs` is empty, so the pre-`5o1jye` inline-reason spelling occurs in-tree only in two hand-built test fixtures and in an orphaned AST fingerprint. Separately, `SCHEMA_VERSION` is a RUN-level key and queue items carry no version field; `run_analytics_sources` records that across a 135-run corpus `schema_version` was uniformly `1` while three different drivers had written them, so it "cannot discriminate generations". A version-dispatched migration is therefore not available, which is consistent with this plan owing none (OQ-02). | `ls .aw/records/runs` -> absent; `.aw/state/runs` empty; `rg` for the inline spelling across the tree returning only `tests/test_dependency_block_reporting.py`'s frozen-record fixture, `tests/test_run_selection_policy.py`'s inline-reason row, and `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json`; read of `run_analytics_sources`'s corpus measurement. |
| F-17 | THE BASELINE IS FULLY GREEN, so any failure after this plan is this plan's to explain. Bare `python3 -m pytest` at authoring HEAD `5d06997e` on this lane: `3246 passed, 2 skipped, 3 warnings in 52.68s`, with 207 deselected by the configured markers. **THESE DIGITS ARE CONTEXT, NOT THE BAR**: re-derive your own baseline at execution HEAD and state every delta against YOUR number. Review re-measured `3284 passed, 2 skipped` days later, which is a 38-test rise and is exactly why this row refuses to be an acceptance bar. | The bare run above; `git log --oneline -1` -> `5d06997e`; a second bare run at review HEAD reporting `3284 passed, 2 skipped, 3 warnings`. |
| F-18 | **THERE IS NO CALLABLE `retry_incomplete` REQUEUE PATH, SO E-05's INSTRUCTION AND V-05's ANTI-REIMPLEMENTATION CLAUSE COULD NOT BOTH BE SATISFIED AS WRITTEN (PR-402, review-added).** E-05 said to "run the host's `retry_incomplete` requeue path over it" and V-05(c) required confirming the measurement "drove the REAL requeue branch (naming the function called)". Measured: the `if retry_incomplete:` block is inline in the body of each host's `run_queue`, and the only requeue FUNCTION anywhere in either host or `runner_shared` is `requeue_interrupted(run_dir, state)`, which is the DIFFERENT interrupted-prerequisite route. So there is no function to name, and an executor following V-05(c) literally would either fabricate a function name or re-implement the status set, which the same clause forbids. E-05 now names two acceptable routes (end-to-end resume, or predicate-level with the limitation declared) and V-05 requires the route be stated. SEPARATELY, THE EXPECTED ANSWER IS NOW MEASURED rather than predicted, which is what E-05 asked for: `runner_stop.is_indeterminate(item)` returns False and `action == "skip"` is False for all three producers' real item shapes, and `fail-depend` is in the shipped status set alongside its legacy `dependency-blocked` spelling, so all three requeue. | `dir()` over both hosts and `runner_shared` for any `requeue`/`retry_incomplete` callable, returning only `requeue_interrupted`; `inspect.getsource(oc_runipd.run_queue)` confirming the `if retry_incomplete:` block is inside it; the two exclusion predicates evaluated against a cascade item, a drain item and an orchestrate-action TERMINATE item, all three printing False; the shipped status set read in place with `fail-depend` present. |
| F-19 | THE THREE-WRITE-SITE CENSUS E-02 MUST RE-HOME IS REAL, IS WHERE THE PLAN SAYS, AND ITS ITEM 1 SAYS EXACTLY WHAT E-02 CLAIMS, so the re-homing instruction is actionable rather than aspirational. Read at review above `oc_runipd.DEPENDENCY_BLOCK_RECOVERY_HINT`: the census enumerates (1) `cascade_dependency_blocked` - "PERMANENT by construction ... CORRECT AS WRITTEN; deliberately unchanged by `akzy45`", (2) the drain-time `if runnable is None:` arm, "the ONE site `akzy45` changed", and (3) `dispatch_orchestrator_item`'s `terminal_status` default, "ALREADY CORRECT". So item 1's "deliberately unchanged" IS the sentence this plan falsifies, exactly as E-02 states, and E-02's correction instruction targets the right text. ALSO VERIFIED: both hosts reach `runner_shared.OC_HOST_LABELS`/`AGY_HOST_LABELS` at module level and already pass `labels=` at many call sites, so E-02's "each drain arm already has its host's labels available" is true and needs no new plumbing. | The census read in full above the constant, with item 1 quoted; `grep` for `OC_HOST_LABELS` in `oc_runipd.py` showing module-level availability and existing `labels=` call sites; the drain write site read at `item["dependency_block_recovery"] = DEPENDENCY_BLOCK_RECOVERY_HINT` in both hosts. |
| F-20 | THE PLAN'S CENTRAL DESCRIPTOR CLAIM AND ITS TWO GUARDRAILS ALL HOLD, VERIFIED RATHER THAN READ. `HostLabels._fields` is exactly the ten fields F-13 assumes (`id`, `command`, `review_command`, `argv_tokens`, `argv_subcommands`, `product`, `report_title`, `shell_tool`, `emits_launch_identity`, `full_auto_actor`), so an eleventh with no default is what E-07 must absorb. `tests/test_hostdedup_third_host.py` builds `SCRIPTED_HOST_LABELS` with all ten by LITERAL keyword at module scope, so F-13's import-time `TypeError` prediction is correct. `tests/test_runner_shared.py::test_set_plan_approved_durable_history_pin` builds its kwargs as `{f: f"val_{f}" for f in runner_shared.HostLabels._fields if f != "full_auto_actor"}` inside `assertRaises(TypeError)`, so it needs no edit AND it keeps pinning the no-default property, exactly as E-07's final clause says to confirm. `test_no_divergent_codefined_constants_in_runner_shared` AST-collects UPPER_CASE module-level assignments co-defined in all three modules and compares resolved values, so it is the mechanical guard E-01/E-02 must avoid tripping by NOT lifting the constant into `runner_shared`. | `HostLabels._fields` printed; both test constructions read; the guard's docstring and AST-collection body read. |
| F-21 | THE FIX'S USER-VISIBLE EFFECT AND THE PER-HOST DIVERGENCE ARE BOTH REPRODUCED END TO END THROUGH THE REAL `write_report`, which is the measurement the whole plan turns on. Driving the shipped `write_report(run_dir, state, labels=OC_HOST_LABELS)` over two otherwise-identical items differing only in the presence of `dependency_block_recovery`: the cascade-shaped item renders `- \`executed:aaa111\`: target aaa111 is failed-safely` and NO recovery line, while the drain-shaped item renders the same plus `  - Recovery: resolve the named cause, then re-queue with \`aw oc runipd resume --repo <repo> --retry-incomplete <run-id>\`; a bare \`resume\` does NOT re-queue a dependency-blocked item`. The two hosts' constants differ only in `aw oc` versus `aw agy`, and compare unequal, which is F-03's basis for a descriptor field over a shared constant. One incidental note for the executor: `write_report` requires each queue item to carry `setid` (a bare probe without it raises `KeyError: 'setid'`), so build probe items with that key. | Both report sections pasted from the real `write_report`, with `RECOVERY LINE PRESENT: False` then `True`; both host constants printed with `equal: False`; the `KeyError` observed and the probe corrected. |
| F-08b | THE `## Dependency blocks (why)` GATE IS ON THE CANONICAL STATUS PLUS EITHER DEPENDENCY KEY, which is what makes E-03's and E-04's additive write sufficient to light up the section with no consumer change. Read at review: the section's comprehension selects an item when `canonical_terminal_status(item.get("status")) == "fail-depend"` AND (`unsatisfied_dependencies` OR `unsatisfied_dependency_reasons`) is truthy, then renders `- Recovery: {hint}` only `if hint`. All three producers already satisfy the gate (F-01, F-02, F-06 each show the section rendering for them today), so the only thing missing is the key, and the `if hint` guard is why an unsupplied hint leaves the section byte-identical. | The section's selection comprehension and its `hint = item.get("dependency_block_recovery")` / `if hint:` lines read in place; the three producers' sections rendered in F-01, F-02 and F-06's probes. |

## Proposed changes (ordered, validatable)

1. `runner_shared.HostLabels` gains a `dependency_block_recovery` field with no default, populated on
   `OC_HOST_LABELS` and `AGY_HOST_LABELS` with the two hosts' existing texts verbatim (E-01;
   descriptor shape justified by F-03 and the Conventions section, `TypeError`-on-omission per the
   class docstring).
2. Both hosts' drain arms read the hint from their labels and the two module-level
   `DEPENDENCY_BLOCK_RECOVERY_HINT` constants are deleted, with the three-write-site census re-homed
   and its item 1 corrected (E-02; guard rationale in Conventions).
3. `runner_shared.cascade_dependency_blocked` gains keyword-only `recovery_hint=None` and writes the
   key when truthy; both hosts pass their descriptor field (E-03; default-preservation measured in
   F-09, call-site safety in F-11, identity pin in F-12, shipped assertion in F-10).
4. `runner_shared.dispatch_orchestrator_item` gains the same parameter and writes the key on the
   TERMINATE path only, never on RECONSIDER (E-04; producer identified in F-06, value bounded by
   F-07, transient prohibition sourced from `TRANSIENT_DEPENDENCY_WAIT_HINT`).
5. The uniformity premise is measured across all three producers, by a DECLARED route since no requeue
   callable exists (F-18), and the plan is revised if any producer's item does not requeue (E-05;
   expected answer in F-08, now evidenced in F-18).
6. `tests/test_dependency_block_reporting.py` splits the recovery-key assertion into no-hint and
   with-hint cases and adds orchestrator TERMINATE/RECONSIDER and report-rendering cases (E-06).
7. `tests/test_hostdedup_third_host.py`'s `SCRIPTED_HOST_LABELS` gains the new field (E-07; import-
   time breakage measured in F-13).

## Deferred / out of scope (with reason)

- DELETING THE `if d in why` CONDITIONALS IN `derive_item_disposition` AND `render_stream` IS OUT OF
  SCOPE, EVEN THOUGH THE BACKLOG ITEM ASKS FOR IT. F-04 measures that they are no longer producer
  special-cases but the frozen-record repair `5o1jye` E-03 landed deliberately, that deleting them
  re-creates the `(unsatisfied)`/`(blocked)` double parenthetical on records already on disk, and that
  two shipped assertions would turn red. F-05 records why declining costs the item's goal nothing.
  - Carrier-Declined: Nothing is owed, and this row records a PROHIBITION rather than an outstanding
    defect. The conditionals are the CORRECT state: a presence test that a complete reasons map always
    satisfies, functioning as a back-compat reader for frozen records in exactly the way
    `TERMINAL_STATUS_ALIASES` does for the retired status spelling. A future plan deleting them would
    be re-introducing a defect, so naming a carrier would record an obligation that does not exist.
- REWRITING FROZEN `state.json` RECORDS TO THE NEW SHAPE IS OUT OF SCOPE. OQ-02 resolves this from
  repository evidence and F-16 measures that there is nothing in this worktree to rewrite and no
  per-item version field that could gate a dispatch.
  - Carrier-Declined: Nothing is owed. `5o1jye`'s Deferred section already states this as a committed
    contract with its own Carrier-Declined rationale ("a plan that mutated durable history would be
    the defect"), and the readers accept the older shape by construction. A carrier here would
    duplicate a settled decision.
- ADDING `reasons`, `recovery`, `block_class` OR `block_detail` TO THE CASCADE'S `dependency-blocked`
  EVENT IS OUT OF SCOPE AND IS PROHIBITED BY E-03. The backlog item is about the ITEM keys that
  `write_report` reads; the event key set is pinned by equality in a shipped test (F-10) and the
  retained event name is a deliberate continuity decision recorded by `5o1jye`.
  - Carrier-Declined: Nothing is owed. The cascade's event carries a single `reason` naming the class
    of cause, which is the right granularity for a producer that fires on exactly one condition; the
    drain arm's extra keys exist because it must record WHICH of several classifications it reached.
    Making the two event shapes identical would add keys with nothing to say.
- THE `not in this run` MISLABEL AND THE DOUBLED-TOKEN VERBOSITY ARE OUT OF SCOPE. Both are separately
  filed and this plan touches neither the disposition code selection nor the reason wording.
  - Carrier: 8mohre
- THE DRAIN PATH'S TOKEN-PREFIXED REASON STRINGS ARE OUT OF SCOPE for the same reason.
  - Carrier: csjq81
- MAKING `aw runs` SURFACE DEPENDENCY BLOCK REASONS IS OUT OF SCOPE. `run_viewer` reads none of these
  three keys, so a dependency-blocked item surfaces there only via a `Refusal` record. That is a
  VIEWER feature, not a producer-shape divergence, and this plan changes no viewer.
  - Carrier-Declined: There is no live carrier to name and this row deliberately does not invent one.
    The gap was filed as backlog `phawyy` and then RETRACTED: its `## Workflow history` records
    "RETRACTED: the premise is false ... What remains true is far narrower and not release-blocking:
    aw runs does not SURFACE the persisted reason in rendered output. Re-scope to the viewer or
    close", and the item now sits `parked`, i.e. abandoned, so pointing at it would assert that
    something revisits work that nothing revisits. Plan `03ie04` reached the same conclusion
    independently. Whether the viewer should render these keys is a PRODUCT decision for the
    maintainer rather than an obligation this plan incurs, and nothing this plan does makes it more
    or less needed: the keys it adds are read by `write_report`, which already renders them. A
    maintainer who wants it should file a fresh viewer-scoped item.

## Scope check

- Over-scope: none. `runner_shared.py` gains one `HostLabels` field, two values on the two existing
  descriptors, one keyword-only parameter on each of two functions with one guarded write apiece, and
  the re-homed census comment; no signature becomes incompatible, no key is renamed or reshaped, no
  event gains a key, and no import is added. `oc_runipd.py` and `agy_runipd.py` each lose one constant
  and gain a descriptor read at the sites they already have. The two test files receive additive cases
  plus one field. No `.spec.md` file is declared or touched (F-15), no frozen record is rewritten, and
  nothing in `run_selection_policy.py` or `render_stream.py` is edited, which is what keeps this plan
  off `zhqt51`'s expressions (F-14).
- Under-scope: the plan leaves the two consumer conditionals standing, so a reader who takes the
  backlog item's SUGGESTED FIX literally will find half of it declined; F-04/F-05 and the first
  Deferred row are where that is argued, and the item's Summary line ("every consumer needs a special
  case") is answered by removing the producer divergence rather than the reader. It also leaves the
  cascade's EVENT shape different from the drain arm's, which is deliberate and argued in a
  Carrier-Declined row. Finally, E-07 edits a test file this plan does not otherwise own; it is
  declared in `- Scope-Paths:` and F-13 measures why omitting it would fail collection.

## Required tests / validation

1. FULL BARE SUITE (`python3 -m pytest`, bare, no added flags) passes with zero failures and a count
   increased over your own re-derived baseline by exactly the cases E-06 adds. Paste the summary line.
2. TARGETED: `python3 -m pytest tests/test_dependency_block_reporting.py tests/test_hostdedup_third_host.py tests/test_runner_shared.py tests/test_host_capability_wiring.py tests/test_terminal_status_vocabulary.py tests/test_orchestrator_retirement.py tests/test_oc_runipd.py tests/test_finalize_sendback.py tests/test_run_selection_policy.py -o addopts=""` passes. These are every module that calls a changed symbol (F-11), the descriptor constructions (F-13), the identity pin (F-12), the divergent-constant guard, and the consumer whose conditional this plan deliberately does NOT change (F-04).
3. MEASURED, NOT ASSUMED: E-05's three-producer requeue measurement is recorded in V-05 with the
   actual statuses observed, NAMING THE ROUTE TAKEN. There is no callable requeue function to invoke
   (F-18), so either drive a real `resume --retry-incomplete` end to end, or evaluate the two exclusion
   predicates and read the status set from the shipped source, declaring that the loop was not executed.
   Do not claim a function call that does not exist.
4. MUTATION: each new test case in E-06 is shown to FAIL when its corresponding E-item is reverted, so
   a green case is evidence rather than decoration.

## Spec / documentation sync

N/A with reason. F-15 measures that no approved spec mentions `dependency_block_recovery` or the
`## Dependency blocks (why)` section; the section is a report improvement introduced by `revgate`
`7nkcgp` E-04 and its contents are not a specified contract. This plan adds no operator-facing string
(E-01 moves the two existing texts verbatim), changes no CLI surface, and alters no documented
behavior, so no `CHANGELOG.md` entry and no spec amendment is owed. Consequently this plan declares no
`.spec.md` path in `- Scope-Paths:`.

## Open questions

### OQ-01: Should the recovery hint be a `HostLabels` field or a parameter threaded from each host's existing constant?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, not from preference. A
  `HostLabels` FIELD, because `runner_shared.orchestrator_uncovered_work_remedy`'s docstring already
  classifies this exact constant as a per-host string whose implementation must be one object, and
  because `test_no_divergent_codefined_constants_in_runner_shared` mechanically forbids the shared-
  constant alternative. Keeping the two host constants and merely threading them would leave two
  UPPER_CASE strings that a third host must rediscover, which is precisely what
  `HostLabels.full_auto_actor`'s comment records as the measured trap (a shared value matching neither
  host silently misattributed every Antigravity auto-approval). REVERSIBLE: yes; the field could be
  replaced by a threaded constant without touching any producer signature.

### OQ-02: Does this plan owe a migration for run records already on disk carrying the pre-`5o1jye` inline-reason spelling, as the backlog item's closing sentence asks?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: NO MIGRATION IS OWED, AND NONE MAY BE ATTEMPTED. Three
  independent grounds, each checkable. FIRST, the contract: `5o1jye`'s Deferred section states with a
  Carrier-Declined rationale that legacy records stay READABLE and that "a plan that mutated durable
  history would be the defect". SECOND, the readers already handle it: both `render_stream`'s
  diagnostics arm and `write_report`'s gate accept the legacy `dependency-blocked` spelling alongside
  the canonical `fail-depend`, and the `if d in why` conditional this plan declines to delete (F-04)
  is exactly the reader that renders the old token shape correctly. THIRD, the mechanism is absent:
  F-16 measures that queue items carry no version field and that `SCHEMA_VERSION` cannot discriminate
  generations, so a version-dispatched migration is not available even if one were wanted. The
  practical consequence for an old record is narrow and acceptable: it keeps rendering its reason
  correctly and simply has no `- Recovery:` line, which is what it has today. REVERSIBLE: not
  applicable; nothing is changed.

### OQ-03: Should the RECONSIDER path of `dispatch_orchestrator_item` also receive the hint?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: NO, AND E-04 STATES IT AS A PROHIBITION because the
  wrong answer here ships a false instruction rather than a missing one. RECONSIDER writes no status
  and leaves the item `queued`; `TRANSIENT_DEPENDENCY_WAIT_HINT`'s own comment records that such an
  item "needs no flag at all, because `requeue_interrupted` re-queues an `interrupted` prerequisite on
  any `resume`" and that saying "use --retry-incomplete" there "would send the operator to a flag they
  do not need". The transient case additionally already carries its own recovery text inside
  `transient_dependency_wait`, rendered by `render_transient_dependency_waits`, so it is not
  advice-less. REVERSIBLE: yes, but reversing it would make the report misdirect the operator.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: (a) PASTE `runner_shared.HostLabels._fields` showing `dependency_block_recovery`
    present. (b) PASTE an equality check proving each host descriptor's new value equals the string
    that host's module defined at HEAD: capture both HEAD strings BEFORE E-02 deletes them (e.g. from
    `git show HEAD:agent_workflows/oc_runipd.py`) and compare, printing `True` for each; a
    hand-retyped comparison is not acceptable because the point is that no operator-facing text
    changed. (c) PASTE a `HostLabels(**kwargs)` construction omitting the new field raising
    `TypeError`, so the no-default property is measured and not assumed. (d) CONFIRM by quoting the
    diff that no `DEPENDENCY_BLOCK_RECOVERY_HINT` assignment was added to `runner_shared`, which the
    divergent-constant guard would flag.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: (a) PASTE `rg -n 'DEPENDENCY_BLOCK_RECOVERY_HINT' agent_workflows/ tests/`
    showing no module-level assignment remains in either host. (b) DRIVE a real drain block on each
    host (or call the arm's code path) and PASTE the resulting `item["dependency_block_recovery"]` and
    the event's `"recovery"` value for BOTH hosts, showing each still carries its OWN host's command
    (`aw oc runipd resume` for oc, `aw agy runipd resume` for agy). A test that only checks oc would
    miss the exact misattribution class `full_auto_actor`'s comment records. (c) PASTE the re-homed
    three-write-site census and confirm its item 1 no longer says the cascade is "deliberately
    unchanged by `akzy45`", since this plan changes it. (d) PASTE
    `python3 -m pytest tests/test_runner_shared.py -o addopts=""` passing, which is where the
    divergent-constant guard lives.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: (a) PASTE `inspect.signature(runner_shared.cascade_dependency_blocked)` showing
    the new parameter is KEYWORD-ONLY and defaults to `None`. (b) PASTE the function called with NO
    hint over a cascade-blocking state, showing the item's full key set and the resulting
    `## Dependency blocks (why)` section BYTE-IDENTICAL to HEAD's for the same input (obtain HEAD's by
    running the same probe against `git stash`ed or `git show`n HEAD code, not by retyping it). (c)
    PASTE it called WITH a hint, showing `dependency_block_recovery` equal to the supplied string and
    the report gaining exactly ONE `- Recovery:` line. (d) PASTE the emitted `dependency-blocked`
    event's key set in BOTH cases and confirm it equals `{"at","event","id6","dependencies","reason"}`,
    which is the prohibition E-03 carries and which a shipped test asserts by equality. (e) CONFIRM
    `oc_runipd.cascade_dependency_blocked is agy_runipd.cascade_dependency_blocked` still evaluates
    `True`, so no host wrapper was introduced (F-12).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: (a) PASTE `inspect.signature(runner_shared.dispatch_orchestrator_item)` showing
    the keyword-only `None`-defaulting parameter. (b) DRIVE the TERMINATE path with a hint and PASTE
    the item's `dependency_block_recovery` plus the rendered `## Dependency blocks (why)` section
    showing one `- Recovery:` line beside the existing per-child reasons. (c) DRIVE the RECONSIDER path
    with the SAME hint supplied and PASTE the item showing `dependency_block_recovery` ABSENT, its
    status still `queued`, and its `transient_dependency_wait` record still carrying its own
    `recovery` text. This is the item's one falsifying case: if RECONSIDER writes the key, V-04 fails
    outright. (d) PASTE the TERMINATE item's `Refusal` record showing its `remedy` unchanged, since
    F-07 establishes that surface already advised the operator and this plan must not alter it.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: (a) PASTE, for EACH of the three producers, the blocked item's status before and
    after running the host's `retry_incomplete` requeue over the state, naming which returned to
    `queued`. (b) STATE explicitly whether all three requeued. If any did not, PASTE the revised E-03
    or E-04 withholding the hint from that producer and explain in this evidence block why the hint
    would have been false for it; shipping a uniform hint that is wrong for one producer is the
    failure this item exists to prevent. (c) NAME THE ROUTE E-05 took and, if it was
    the weaker predicate-level route, SAY SO EXPLICITLY in this evidence block. Do NOT claim to have
    "called the requeue function": review established there is none to call, since the branch is inline
    in each host's `run_queue` and the only requeue callable is `requeue_interrupted`, a different route
    (F-18). If you drove it end to end, name the command and paste the before/after statuses; if you
    evaluated the predicate instead, paste the two exclusion results per producer AND the status set as
    READ FROM the shipped source rather than retyped, and state that the loop was not executed. A claim
    that the real branch ran when it did not is the failure this clause now exists to prevent.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: (a) PASTE `python3 -m pytest tests/test_dependency_block_reporting.py -o addopts=""`
    passing, with the per-test counts visible. (b) PASTE the no-hint case still asserting the key is
    ABSENT and the new with-hint case asserting it EQUALS the supplied string, and confirm the
    event-key equality assertion is present and UNEDITED in both. (c) FOR EACH new case, PASTE a
    mutation run showing it RED when its E-item is reverted (revert E-03's write for the cascade case,
    E-04's for the orchestrator cases, E-02's descriptor read for the host-attribution case), then
    green again after restoring. A case that cannot be made to fail is not evidence. (d) CONFIRM no new
    test reads production SOURCE text via `inspect`, `ast`, regex or substring search over a module
    file; every assertion must be on returned values or rendered output.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: (a) PASTE `python3 -m pytest tests/test_hostdedup_third_host.py -o addopts=""`
    passing, which proves the module now IMPORTS (F-13 measures that E-01 alone makes it a collection
    error). (b) PASTE the `SCRIPTED_HOST_LABELS` field added. (c) PASTE
    `tests/test_runner_shared.py::test_set_plan_approved_durable_history_pin` passing with NO edit to
    that file, confirming its `_fields`-derived kwargs construction still exercises the
    `TypeError`-on-omission property. (d) PASTE the full bare `python3 -m pytest` summary line and
    state the delta against your own re-derived baseline, accounting for it entirely by the cases E-06
    added.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Do not begin until this plan carries `- Status: approved` from an explicit human sign-off. Execution is
governed by the repository's execution contract: commit ONLY the paths named in `- Scope-Paths:`,
through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing. Run the suite BARE
(`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass you did not run.

Two order constraints an executor must respect. FIRST, E-01 and E-07 land TOGETHER or the suite cannot
even collect: F-13 measures that adding a no-default `HostLabels` field breaks
`tests/test_hostdedup_third_host.py` at import, and F-20 confirms the ten-field literal construction
that makes it so. SECOND, E-05 gates E-03 and E-04's shipping claim rather than merely following them:
if a producer's item does not requeue under `--retry-incomplete`, the correct response is to WITHHOLD
the hint from that producer and say so, not to ship a uniform instruction that is false for one path.

WHAT REVIEW CHANGED (2026-09-29), so the human approves the corrected plan rather than the authored one.
Every material claim was re-measured and the plan's argument held throughout. Reproduced: the cascade
writing a bare token plus a populated reasons map and NO recovery key (F-01, so the item's headline is
indeed stale); the report rendering a recovery line for a drain item and none for an otherwise-identical
cascade item, through the real `write_report` (F-02); the two host constants differing only in `aw oc`
versus `aw agy` and comparing unequal (F-03); the `(unsatisfied)` double parenthetical the blanket
fallback would reintroduce, plus both shipped assertions that would turn red (F-04); the orchestrator
TERMINATE path writing the two dependency keys and no recovery key (F-06); the `children-unfinished`
remedy verbatim (F-07); `fail-depend` in the requeue set with both exclusions False for all three
producers (F-08); the single shipped assertion pinning the divergence (F-10); the ten-field literal
`SCRIPTED_HOST_LABELS` construction and the `_fields`-derived one that needs no edit (F-13); no spec
mentioning the section (F-15); and all five cited backlog carriers in their stated states, including the
RETRACTED and now `parked` `phawyy`. TWO CORRECTIONS. FIRST (MEDIUM, PR-401), E-03's prose said "Five
test call sites" where F-11 in the same plan says NINE and E-03's own list names seven files; the
measured figure is nine invocations and E-03 now carries the per-file breakdown, so an executor cannot
under-count the blast radius of a required parameter. SECOND (MEDIUM, PR-402), E-05 told the executor to
"run the host's `retry_incomplete` requeue path" and V-05 required naming the function called, and there
is no such callable: the branch is inline in each host's `run_queue` and the only requeue function is
`requeue_interrupted`, a different route, so the two instructions together could only be satisfied by
fabricating a name or by the re-implementation the same clause forbids. E-05 now names two acceptable
routes and V-05 requires the route be declared (new F-18). Review also added F-19 through F-21 and F-08b
recording that the census E-02 must re-home is where the plan says and its item 1 says what E-02 claims,
that all three descriptor guardrails hold, that the report gate is on the canonical status plus either
dependency key (so the additive write is sufficient with no consumer change), and one practical note
that `write_report` requires `setid` on every probe item. The stale suite baseline is re-labelled after
measuring `3284 passed` against the authored `3246`.

Before the terminal transition, `aw ipd lint --phase pre-transition` must report conforming and every
`V-*` above must carry pasted evidence, not a recollection. Then move this plan to
`.aw/records/plans/executed/` through the tooled lifecycle transition.
