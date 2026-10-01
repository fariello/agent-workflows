# IPD: Give the host-invariant full-auto approval message one definition in runner_shared, with a guard that keeps it host-invariant

- Date: 2026-09-30
- Kind: child
- Concern: `oc_runipd.FULL_AUTO_APPROVAL_MESSAGE` and `agy_runipd.FULL_AUTO_APPROVAL_MESSAGE` are each an independent module-level LITERAL holding the identical string `"auto-approved by --full-auto: review readiness cleared (not human approval)"`, while the sibling `FULL_AUTO_ACTOR` beside each of them is a one-line REFERENCE to `runner_shared.OC_HOST_LABELS.full_auto_actor` / `runner_shared.AGY_HOST_LABELS.full_auto_actor`. So the two names sitting on adjacent lines in both hosts have OPPOSITE duplication properties, and the duplicated one is the one that reaches a plan's permanent `## Workflow history` as the `-m` message. The cost is the ordinary identical-copy hazard `runner_shared`'s own module docstring names: "Two identical copies have no behavioral disagreement TODAY, which is exactly why nothing signals when one is edited and the other is not".
- Scope: IN: (a) define the message ONCE in `runner_shared` as `FULL_AUTO_APPROVAL_MESSAGE`, in the reference-carrying shape the eight other host-invariant co-defined constants already use; (b) turn both hosts' literals into one-line references to it, leaving each host's `set_plan_approved` signature, its default, and the argv it builds byte-identical; (c) extend the shipped `gjni4c` E-01 sweep so a co-defined constant whose two HOST values DISAGREE also fails, which is the direction that sweep structurally cannot currently see and the property this plan must not silently give up. OUT, each with a reason recorded in "Deferred / out of scope": adding a `HostLabels` field (the fix direction the backlog item guesses at, REFUTED by measurement in F-04/F-05 because the value is host-INVARIANT and the descriptor is explicitly a carrier of host-VARYING strings); the ten other host-invariant literal-duplicated constants F-09 measures (a separate sweep, carried); and any change to the message's VALUE, the actor, or `set_plan_approved`'s signature.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py
- Item-Dependencies: executed:b02ohu
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: xi5jt0
- Set: xi5jt0
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 90z361

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 90z361 verified (set xi5jt0, attempt 2).
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): plan-review complete; 7 findings all fixed; E-03 mechanism rewritten onto vars() and ordered behind approved sibling b02ohu

- 2026-10-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed). Reviewed in an isolated lane at HEAD `e4474af7`; the plan file was committed and byte-identical to the lane input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` reported `clean` before semantic review. THE DOMINANT FINDING IS A CROSS-PLAN COLLISION THE AUTHOR MISSED: E-03 instructed the executor to reuse the shipped `ast.parse` walk in `tests/test_runner_shared.py`, while APPROVED sibling `b02ohu` (Set `structpin` Order 01) is rewriting that very walk onto `vars()` and requires a pasted search showing ZERO `ast.parse`/`ast.walk`/`ast.unparse` remain in that file, and approved `76ic0k` ships a guard that REFUSES a new one; `GUIDING_PRINCIPLES.md` section 16 grants no enumeration-only carve-out and separately forbids inspecting "module dictionaries" for placement. The plan's own F-11 had dismissed both as "mentioning it only in prose", which reading their E-items refutes. Fixed by rewriting E-03 onto `vars()`, DEMONSTRATING the replacement green and red at review rather than describing it (F-13), and declaring `- Item-Dependencies: executed:b02ohu` (OQ-02). Four further corrections, each measured: E-01's comment cited E-03 as the guard against a drifting shared value when E-03 is structurally BLIND to that (both hosts follow the shared constant in lockstep) and E-04 is the guard that catches it; the suite baseline `3387 passed, 2 skipped` is stale and the tree carries one pre-existing unrelated failure (F-15), so V-04's bar was restated as re-derive-and-attribute; the `_ID_RE`/`_STATUS_RE` deferral reason implied compiled patterns cannot be compared, refuted on all four interpreters spanning the declared `>=3.9` matrix (F-16); and E-03's `vars()` enumeration reaches 57 names of which 48 are identical objects while `_close_process_streams` is not reached at all by `isupper()`, both now stated as bounds (F-14). Full findings and decisions: `.aw/records/reviews/20260930-xi5jt0-01-90z361-give-the-host-invariant-full-auto-approval-message-one-defin.review.md`.
- 2026-09-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `xi5jt0`. Every measurement in Findings taken against this lane's working tree at HEAD `56043a76`; suite baseline `3387 passed, 2 skipped` (F-10). The item's factual claim is CONFIRMED VERBATIM by AST probe: both hosts assign the message as an independent literal, both assign the actor as a descriptor reference (F-01). THE ITEM'S PROPOSED FIX DIRECTION IS REFUTED, and that is this plan's one substantive departure from the item it graduates. The item recommends "add a HostLabels field ... rather than a module-level shared constant". Measured, every one of the descriptor's 10 fields differs between the two hosts and the message does NOT (F-04), so a field would make a host-INVARIANT value into a per-host parameter and would force each host (plus the third-host test descriptor, which the no-defaults `NamedTuple` obliges) to re-spell the identical string - leaving the literal count at 2 and raising it to 3 in test code, i.e. the duplication the item asks to remove would survive the fix (F-05, F-06). The reference-carrying shared constant the item warns against is instead the ESTABLISHED shape for exactly this class: 8 of the 19 constants co-defined in both hosts already have it, and the shipped `gjni4c` guard PERMITS it by construction, failing only a shared value matching NEITHER host (F-07, F-08). A second correction: the item says `gjni4c` E-03's by-value argv assertion means "a future divergence of the two copies fails a test". Measured, that is TRUE and is why this stays `low`, but it is not the whole guarantee the item implies - the assertion pins each host against a literal spelled in the test, so it catches a host drifting from the EXPECTED value, and E-03 of this plan adds the complementary host-vs-host check the shipped sweep cannot make (F-03, F-08).
- 2026-09-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give the full-auto approval message ONE definition, so the string that lands in a plan's permanent
`## Workflow history` cannot be edited in one host and missed in the other, and leave behind a guard
that fails if the two hosts' co-defined constants ever disagree. No value changes: the message, the
actor, both `set_plan_approved` signatures and the argv each host builds are byte-identical before and
after.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one definition, two references

- [x] E-01 In `agent_workflows/runner_shared.py`, define `FULL_AUTO_APPROVAL_MESSAGE` as the single
  module-level constant holding `"auto-approved by --full-auto: review readiness cleared (not human
  approval)"`. Place it immediately BEFORE `runner_shared.set_plan_approved`, which is the function
  whose `message` parameter the value feeds and whose docstring already explains the value's history,
  rather than beside the `HostLabels` descriptors (it is not descriptor data; F-04).
  READ THE DELETED-CONSTANT HISTORY BEFORE WRITING THIS, because a name is being REINTRODUCED that
  plan `gjni4c` deliberately DELETED from this very module, and re-adding it carelessly re-creates the
  exact defect that plan fixed. The deleted constant held `"Auto-approved via --full-auto (review
  passed all gates)"`, a THIRD value matching NEITHER host, and `gjni4c`'s own out-of-scope row
  records why it did not do what this plan does: it was "deleting a shared constant as a durable-history
  hazard, so adding one in the same change would be self-contradictory". The hazard was the DIVERGENT
  VALUE, not the sharing: what makes this reintroduction safe is that the value is byte-identical to
  what both hosts already hold (F-01) and that E-04's by-value assertion fails if that ever stops
  being true. CITE E-04, NOT E-03, IN THAT COMMENT. E-03 is the host-vs-host sweep and it is
  structurally BLIND to a drifting SHARED value, because after E-02 both hosts follow the shared
  constant in lockstep and so continue to agree with each other; E-04 is the guard that pins the value
  itself, which is exactly why the plan carries both and why V-04 demands a mutation that is RED for
  E-04 while GREEN for E-03. Carry that reasoning in the constant's `#:` comment, naming `gjni4c` and
  stating that the value MUST equal both hosts' and is enforced by the E-04 assertion, so a future
  reader does not re-litigate the deletion or assume the name is forbidden.
  DO NOT give `runner_shared.set_plan_approved`'s `message` parameter a default of this new constant.
  Its no-default property is asserted by the shipped `test_set_plan_approved_durable_history_pin`
  (`inspect.Parameter.empty`), and the host wrappers' defaults are what actually decide the recorded
  message because both live call sites pass two arguments (F-02). Adding a default here would break a
  shipped assertion and would relocate a guarantee this plan is not entitled to move.
  - Depends on: none
  - Expected outcome: `runner_shared.FULL_AUTO_APPROVAL_MESSAGE` exists and equals the message string;
    `inspect.signature(runner_shared.set_plan_approved).parameters["message"].default` is still
    `inspect.Parameter.empty`; no other executable line in the module changes.
  - Execution state: performed

- [x] E-02 In `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`, replace each
  module-level `FULL_AUTO_APPROVAL_MESSAGE = ( "auto-approved by ..." )` literal with the one-line
  reference `FULL_AUTO_APPROVAL_MESSAGE = runner_shared.FULL_AUTO_APPROVAL_MESSAGE`. Use exactly that
  form, which is the shape the eight already-shared co-defined constants use in both hosts
  (`ACTION_CHOICES = runner_shared.ACTION_CHOICES` and its seven peers; F-07), so this constant stops
  being the odd one out on its own two lines.
  KEEP THE NAME IN BOTH HOSTS. Do not delete it and point the wrappers at `runner_shared` directly:
  each host's `set_plan_approved` declares `message: str = FULL_AUTO_APPROVAL_MESSAGE` and the shipped
  `test_set_plan_approved_durable_history_pin` asserts that default EQUALS the literal per host, so the
  host-level name is load-bearing (F-02).
  AMEND THE ADJACENT COMMENT IN EACH HOST, which currently explains only why `FULL_AUTO_ACTOR` reads
  from the descriptor, to also state why the message reads from a shared constant instead: the actor
  is host-VARYING and so is descriptor data, the message is host-INVARIANT and so is a shared
  constant, and both are references for the same underlying reason (one place each value is written).
  That two-sentence contrast is the thing a future reader most needs, because the two names sit on
  adjacent lines with opposite mechanisms.
  - Depends on: E-01
  - Expected outcome: both hosts' `FULL_AUTO_APPROVAL_MESSAGE` still equal the message string and are
    now the SAME `str` object as `runner_shared.FULL_AUTO_APPROVAL_MESSAGE` (`is` identity, which the
    two independent literals do not satisfy today; F-01); neither host's `set_plan_approved` signature,
    default value, or built argv changes; `rg -c` finds ZERO remaining spellings of the message literal
    in `agent_workflows/`.
  - Execution state: performed

### Task group 2: the guard that keeps it invariant

- [x] E-03 Add a host-vs-host equality sweep to `tests/test_runner_shared.py`, beside
  `test_no_divergent_codefined_constants_in_runner_shared`, enumerating names with `vars()` AND NOT
  WITH `ast.parse`.
  THE GAP IS PRECISE, so do not conflate it with the shipped check. That sweep compares the SHARED
  value against each host and fails only when it "matches neither" (F-08), so it is blind to the case
  where the two HOSTS disagree with each other. Today that blindness is harmless for this constant
  because both hosts hold a literal that happens to agree; after E-02 the shared constant is what
  makes them agree, and the property worth pinning is the one the backlog item is actually about.
  USE `vars()`, NOT AN AST WALK, AND DO NOT REUSE THE SHIPPED HELPER. GUIDING_PRINCIPLES P16
  prohibits `ast.parse` against production code outright, with no enumeration-only carve-out, and the
  approved sibling plan `b02ohu` (Set `structpin`, Order 01, `- Status: approved`) is already
  REWRITING the very helper this item originally proposed reusing: its E-05 replaces
  `test_no_divergent_codefined_constants_in_runner_shared`'s AST walk with a `vars()`-plus-identity
  partition, and its E-04/E-06 require ZERO `ast.parse`/`ast.walk`/`ast.unparse` to remain anywhere in
  `tests/test_runner_shared.py` (verified by a pasted search, which a new AST walk added here would
  fail). This plan therefore declares `- Item-Dependencies: executed:b02ohu` (F-12).
  THE MECHANISM, demonstrated at review rather than described (F-13). Enumerate
  `sorted(k for k in vars(oc_runipd) if k.isupper() and k in vars(agy_runipd))`, which measures 57
  names; for each, assert `getattr(oc, n) == getattr(agy, n)` EXCEPT for the two names in an
  explicitly spelled `EXPECTED_HOST_VARYING = {"DEPENDENCY_BLOCK_RECOVERY_HINT", "FULL_AUTO_ACTOR"}`,
  which are measured host-VARYING and which the sweep must assert are STILL UNEQUAL (so the exemption
  cannot silently become vacuous if one collapses onto the other). Measured at review: the sweep is
  GREEN over 55 compared names, and it covers `FULL_AUTO_APPROVAL_MESSAGE` plus nine of the ten
  carried siblings.
  DO NOT HAND-WRITE THE COMPARED NAME LIST. The original instruction to name the F-09 set explicitly
  is WITHDRAWN as self-defeating: a hand list cannot see a constant added later, which is exactly the
  drift this guard exists to catch, and the `EXPECTED_HOST_VARYING` exemption set already supplies the
  independently-spelled expectation that keeps the test from deriving its whole verdict from the code
  it checks. State in the docstring that the exemption set is the authored expectation and that a
  newly co-defined constant is swept automatically.
  ASSERT OUTCOMES, NOT STRUCTURE, per `AGENTS.md` and GUIDING_PRINCIPLES P16. Reading module-level
  constant VALUES through `getattr` on imported modules is a value comparison and is legitimate. Do
  not assert that either host's line reads `runner_shared.FULL_AUTO_APPROVAL_MESSAGE`, which would be
  a code-structure pin on a refactor this plan itself performs.
  TWO BOUNDS TO STATE HONESTLY IN THE DOCSTRING rather than leave for a reader to discover (F-14).
  FIRST, `vars()` reaches 57 names where the AST walk reached 19, and 48 of the 57 are the SAME
  OBJECT in both hosts (re-exports, for which divergence is impossible), so the sweep is mostly
  vacuous by construction and its real subjects are the nine names that are NOT the same object; say
  so, and do NOT assert a count, which would be the census pin P16 forbids. SECOND,
  `_close_process_streams` is one of F-09's eleven but `"_close_process_streams".isupper()` is False,
  so an `isupper()` filter does NOT reach it; it needs no coverage (both hosts bind the identical
  `runner_shutdown` object, measured `is` True), but the docstring must name the exclusion so a
  future reader does not believe the sweep covers all eleven.
  - Depends on: E-02
  - Expected outcome: a new test in `tests/test_runner_shared.py` passes at the post-E-02 tree with
    NO `ast` use of its own; it FAILS with a message naming the constant and both host values when
    either host's constant is mutated to a different value; and a search for
    `ast.parse`/`ast.walk`/`ast.unparse` in `tests/test_runner_shared.py` returns no MORE hits than
    the post-`b02ohu` tree already had.
  - Execution state: performed

- [x] E-04 Add a by-value assertion that `runner_shared.FULL_AUTO_APPROVAL_MESSAGE` equals the message
  string, spelled out as a literal IN THE TEST rather than read from the module under test, and that it
  is neither the deleted `"Auto-approved via --full-auto (review passed all gates)"` nor any string
  containing `"passed all gates"`. This is the anti-regression for the specific defect `gjni4c`
  deleted: the danger of reintroducing this NAME is that some future edit gives it a third value again,
  and E-03's host-vs-host check would NOT catch that (it compares the two hosts, which would both
  follow the shared constant in lockstep). Put it in the same new test or an adjacent one, and comment
  that it exists because the name was previously deleted for holding a value no host held.
  PUT IT IN THE NEW E-03 TEST, NOT IN `test_set_plan_approved_durable_history_pin`. That shipped test
  is being edited by approved sibling `b02ohu` E-02 (which deletes its two `inspect.getsource` lines),
  so adding to it widens this plan's collision surface on a file both plans declare for no benefit
  (F-12).
  - Depends on: E-01
  - Expected outcome: the assertion passes at the post-E-01 tree and fails if the shared constant's
    value is edited to anything other than the message both hosts record.
  - Execution state: performed

## Project conventions discovered (Step 0)

- CODE IS CITED BY SYMBOL, NOT BY BARE LINE OFFSET, per spec `ipd-structure-and-linting` Section 10.2
  and advisory `IPD-C801`. This matters acutely for this plan's surface: `agent_workflows/runner_shared.py`
  is roughly 37.6k lines and absorbed the whole `rununify` tranche, and the immediately preceding plan
  on this exact code (`gjni4c`) records that EVERY line number in its own backlog item had gone stale
  by roughly fourteen thousand lines. This plan therefore cites `runner_shared.set_plan_approved`,
  `runner_shared.HostLabels`, `oc_runipd.FULL_AUTO_APPROVAL_MESSAGE` and
  `agy_runipd.FULL_AUTO_APPROVAL_MESSAGE` by name throughout, never by position.
- `runner_shared` MUST NOT IMPORT EITHER RUNNER, at module level or lazily, and
  `tests/test_runner_shared.py` asserts the absence by AST (module docstring, "WHAT MAY NEVER HAPPEN
  HERE"). This plan's direction of dependency is the legal one: the hosts read a constant FROM the
  shared module, which is how the eight already-shared co-defined constants work.
- NO MODULE-LEVEL MUTABLE STATE in `runner_shared` (same docstring section; a registration seam was
  considered and DECLINED by the maintainer). An immutable `str` constant is consistent with that
  prohibition, which concerns mutable state and import-order dependence.
- EVERY `HostLabels` FIELD MUST HAVE A NAMED CONSUMER AND CARRIES A HOST-VARYING STRING. The
  descriptor's preamble states "EVERY FIELD IS JUSTIFIED BY A CALL SITE" and its class docstring calls
  it "Every host-varying STRING the lifted runner symbols need". Both sentences bear directly on this
  plan's central decision (F-04). A pending sibling plan, `o55eli` (`gxsprh` Order 01), reads the same
  rule and declines to add a field for the same reason, recording "This plan therefore adds a FUNCTION
  beside the descriptors and no field".
- THE DESCRIPTOR IS A NO-DEFAULTS `NamedTuple` ON PURPOSE, so an omitted field raises `TypeError`
  rather than reading as empty. That is exactly why a field would force a third spelling of the message
  in `tests/test_hostdedup_third_host.py`'s `SCRIPTED_HOST_LABELS` (F-06), and pending plan `8eei5p`
  (`mjrac4` Order 01) confirms the mechanism by scheduling that very edit as its own E-07 for the field
  it adds.
- A STRING THAT LEGITIMATELY DIFFERS PER HOST BELONGS ON `HostLabels`. Pending plan `8eei5p` states
  this rule and correctly applies it to `DEPENDENCY_BLOCK_RECOVERY_HINT`, which is measured
  host-VARYING (`aw oc runipd` versus `aw agy runipd`; F-04). This plan is the converse case and the
  rule's contrapositive: the message does NOT differ per host, so it does not belong on the descriptor.
- A TEST MAY NOT READ PRODUCTION SOURCE, AND THE PROHIBITION HAS NO ENUMERATION-ONLY CARVE-OUT. This
  convention was MISSED at authoring and is the root of the review's dominant finding (F-12).
  `GUIDING_PRINCIPLES.md` section 16 forbids `inspect.getsource`, `ast.parse`, `read_text()` and
  substring or regex searches "against production code (`agent_workflows/*.py`)", and separately forbids
  "architectural placement pins" that "inspect ASTs or module dictionaries"; its one narrow exception is
  for text that "itself is the artifact under test", which a production module is not. The repository
  is actively CLOSING this route rather than tolerating it: approved plan `b02ohu` rewrites the shipped
  AST-walking guard in this very file onto `vars()` and requires zero `ast.*` calls to remain there, and
  approved plan `76ic0k` ships a test that REFUSES a new one. So the presence of an AST walk in
  `tests/test_runner_shared.py` today is a residue being removed, not a precedent to copy. E-03
  therefore enumerates with `vars()`.
- THE SUITE IS NOT GREEN AT THIS HEAD AND THAT IS NOT THIS PLAN'S DOING. One pre-existing unrelated
  failure exists (a date-rollover comparison in the backlog setter's test); see F-15. Re-derive the
  baseline before working rather than trusting any number written into a plan, which is the
  live-artifact re-derivation convention applied to a test count.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE DEFECT IS LIVE AT THIS HEAD, exactly as filed. An AST probe over module-level assignments in both hosts reports `FULL_AUTO_APPROVAL_MESSAGE` assigned as an independent string LITERAL in each (`'auto-approved by --full-auto: review readine...'` in both), while `FULL_AUTO_ACTOR` is assigned as a REFERENCE in each (`runner_shared.OC_HOST_LABELS.full_auto_actor` / `runner_shared.AGY_HOST_LABELS.full_auto_actor`). The two values compare EQUAL (`==` True) but are DISTINCT objects (`is` False, distinct `id()`), which is the signature of two independent literals rather than one shared value. | `ast.parse` walk over `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` module bodies, printing the unparsed RHS per `UPPER_CASE` target; `python3 -c` probe printing `==`, `is` and both `id()`s for the two hosts' constants. |
| F-02 | THE RECORDED MESSAGE COMES FROM EACH HOST'S WRAPPER DEFAULT, not from a caller and not from the shared function. `inspect.signature(runner_shared.set_plan_approved).parameters["message"].default` is `inspect._empty`, while each host's wrapper default IS that host's own constant (`is` identity True for both). Both live call sites pass two arguments (`set_plan_approved_fn(repo, id6)` in the queue-build arm, `set_plan_approved(repo, item["id6"])` in the dispatch arm). This is why E-02 must KEEP the host-level name rather than deleting it, and why E-01 must NOT add a shared default. | `inspect.signature` on all three functions; `is`-identity probe of each host default against that host's constant; both call sites read in `runner_shared` (the `is_plan_review_approved_fn` arm and the `is_plan_review_approved` arm). Corroborated by `gjni4c` F-03a, which measured the same and added E-05 because of it. |
| F-03 | THE ITEM'S STATED MITIGATION IS REAL AND GREEN, which is what keeps this `low`. `tests/test_runner_shared.py::test_set_plan_approved_durable_history_pin` drives each host's `set_plan_approved` with a faked `run_checked`, captures argv, and asserts `argv[argv.index("-m") + 1]` equals the message literal SPELLED IN THE TEST, per host. So a host drifting from the expected value already fails a test. Its limit is the one E-03 closes: it compares each host to a constant in the test, never the two hosts to each other. | `python3 -m pytest tests/test_runner_shared.py -k 'divergent or durable_history' -o addopts=""` -> `2 passed`; the test body read, showing `expected_msg` spelled as a literal and the per-host argv loop. |
| F-04 | THE BACKLOG ITEM'S PROPOSED FIX IS REFUTED BY THE DESCRIPTOR'S OWN CONTRACT AND BY MEASUREMENT. `HostLabels` is documented as "Every host-varying STRING the lifted runner symbols need"; measured, ALL 10 of its fields differ between `OC_HOST_LABELS` and `AGY_HOST_LABELS` (`id`, `command`, `review_command`, `argv_tokens`, `argv_subcommands`, `product`, `report_title`, `shell_tool`, `emits_launch_identity`, `full_auto_actor`), with ZERO fields equal across hosts. The message is EQUAL across hosts. So it is the only candidate that would violate the descriptor's stated invariant, and the `DEPENDENCY_BLOCK_RECOVERY_HINT` precedent pending plan `8eei5p` cites as justification for ITS field is measured host-VARYING, making it a disanalogy rather than a precedent. | Probe printing every `HostLabels._fields` entry with both hosts' values and an equality verdict: 0 equal, 10 differing; `oc.DEPENDENCY_BLOCK_RECOVERY_HINT == agy.DEPENDENCY_BLOCK_RECOVERY_HINT` -> False; `oc.FULL_AUTO_APPROVAL_MESSAGE == agy.FULL_AUTO_APPROVAL_MESSAGE` -> True; the class docstring's first line quoted. |
| F-05 | A `HostLabels` FIELD WOULD NOT REMOVE THE DUPLICATION IT IS MEANT TO REMOVE. The value would have to be written once per descriptor construction, so the production spelling count stays at 2 (`full_auto_actor=`'s two sibling kwargs demonstrate the shape), whereas a shared constant read by both hosts brings it to 1. The item's own fix direction therefore leaves the measured defect ("that string is genuinely duplicated") in place. | Count of production spellings per candidate: today 2 (two host literals); descriptor field 2 (one kwarg per descriptor); shared constant 1 (one definition, two references). Derived from the two `HostLabels(...)` construction sites in `runner_shared`, read in full. |
| F-06 | A FIELD WOULD ALSO ADD A THIRD SPELLING IN TEST CODE. `HostLabels` has no defaults (`_field_defaults` is empty and the shipped guard asserts `TypeError` when a field is omitted), and `tests/test_hostdedup_third_host.py` constructs `SCRIPTED_HOST_LABELS` with all ten fields by keyword. A new field must therefore be supplied there too. Pending plan `8eei5p` confirms this is not hypothetical: its E-07 exists solely to add its new field to that descriptor, warning that omitting it "will raise `TypeError` at IMPORT TIME". | `SCRIPTED_HOST_LABELS` read with its ten keyword arguments; the shipped no-defaults assertion read in `test_set_plan_approved_durable_history_pin` (constructing `HostLabels` with every field except `full_auto_actor` inside `assertRaises(TypeError)`); `8eei5p` E-07 read. |
| F-07 | THE REFERENCE-CARRYING SHARED CONSTANT IS THE ESTABLISHED SHAPE FOR THIS EXACT CLASS. Of 19 `UPPER_CASE`-or-underscore constants co-defined in both hosts (21 if the two non-`isupper()` names `_close_process_streams` and `canonical_terminal_status` are counted; re-verified at review), 8 are already `<NAME> = runner_shared.<NAME>` in BOTH hosts: `ACTION_CHOICES`, `ACTION_IMPLEMENTED`, `EXECUTION_SUCCESS_STATES`, `FULL_AUTO_ACTOR`, `SUCCESS_STATES`, `TERMINAL_STATES`, `TERMINAL_STATES_CANONICAL`, `TERMINAL_STATUS_ALIASES`. E-02 makes the message the ninth. | AST walk classifying each co-defined constant's RHS in both hosts as `runner_shared.`-prefixed or not: 8 reference-style, 11 not. |
| F-08 | THE SHIPPED `gjni4c` GUARD PERMITS THIS FIX BY CONSTRUCTION, and its predicate is also what proves E-03's gap. `test_no_divergent_codefined_constants_in_runner_shared` fails only `if v_shared != v_oc and v_shared != v_agy`, so a shared value EQUAL to both hosts passes; three of the already-shared constants (`ACTION_CHOICES`, `SUCCESS_STATES`, `TERMINAL_STATES`) satisfy `shared == oc == agy` and pass today. The same predicate is structurally blind to `v_oc != v_agy`, which is the host-vs-host direction E-03 adds. | The predicate line read verbatim from the test; probe confirming `shared == oc == agy` for the three named constants; the test's collection logic read (AST over module-level `ast.Assign`/`ast.AnnAssign` with `.isupper()` targets, intersected across the three modules). |
| F-09 | THE MESSAGE IS ONE OF ELEVEN, which bounds this plan and names the carried remainder. Probing constants co-defined in both hosts, host-invariant by value, and NOT reference-style yields 11: `DEFAULT_RUNBOOK_TEXT`, `DEFAULT_STALL_TIMEOUT`, `FULL_AUTO_APPROVAL_MESSAGE`, `LANE_PROMPT_TIMEOUT`, `OUTPUT_MODES`, `_ID_RE`, `_LANE_PROMPT_DISABLED`, `_SIGINT_GRACE_SECONDS`, `_SIGTERM_GRACE_SECONDS`, `_STATUS_RE`, `_close_process_streams`. Only `DEFAULT_STALL_TIMEOUT` is also defined in `runner_shared` (a three-way case the hosts ignore). This plan fixes the ONE its backlog item names, because that one reaches durable plan history and the others do not; the remaining ten are carried, not swept in, since each needs its own read of whether a shared home is correct. | Probe listing every co-defined host constant with an `also_in_shared` flag and a source-text-identity flag; 11 host-invariant literal-duplicated, `DEFAULT_STALL_TIMEOUT` the only one with `also_in_shared=True`. |
| F-10 | BASELINE AND SURFACE. Bare `python3 -m pytest` at the AUTHORING lane HEAD reported `3387 passed, 2 skipped, 3 warnings`; that figure is SUPERSEDED by F-15, which re-measured it at review HEAD `e4474af7` as `1 failed, 3414 passed, 2 skipped` with one pre-existing unrelated failure, so treat the number here as authoring context and re-derive at execution. The surface half still holds exactly: the message literal appears exactly 3 times in the tree's Python, once in each host and once in `tests/test_runner_shared.py` (the by-value assertion of F-03), re-verified at review. No `.md` outside `.aw/records/` mentions the constant, and no spec governs it. | `python3 -m pytest` tail (see F-15 for the current one); per-file occurrence count of the literal across `agent_workflows/`, `tests/` and `tools/` re-run at review -> `oc_runipd.py:1`, `agy_runipd.py:1`, `tests/test_runner_shared.py:1`; `rg` over `*.md` excluding the records trees returning no hits. |
| F-11 | NO PENDING PLAN CONFLICTS ON THIS SYMBOL, but two touch the same descriptor region and one shares two Scope-Paths. `8eei5p` (`mjrac4` 01) declares `runner_shared.py`, both hosts and `tests/test_hostdedup_third_host.py`, and ADDS a `HostLabels` field; `o55eli` (`gxsprh` 01) declares `runner_shared.py` plus the viewer and dashboard and adds a FUNCTION beside the descriptors. Neither touches `FULL_AUTO_APPROVAL_MESSAGE` nor `set_plan_approved`. This plan adds no field and touches neither the descriptors' values nor their field set, so the three are independent; the runner isolates each in its own worktree and merges through revalidation regardless. CORRECTED AT REVIEW: the row's dismissal of `b02ohu`/`76ic0k` as "mentioning it only in prose" is FALSE and is superseded by F-12. | `rg` over `.aw/records/plans/pending/` for `FULL_AUTO_APPROVAL_MESSAGE|full_auto_actor|set_plan_approved` returning three plans, each read: the two named above (descriptor-adjacent, neither touching this symbol) and `b02ohu`/`76ic0k` (whose actual E-items were read at review; see F-12). |
| F-12 | ADDED AT REVIEW, AND IT CHANGED E-03'S MECHANISM. The authored E-03 said to "reuse the existing helper rather than re-implementing the walk" (an `ast.parse` walk) and to extract it to a module-level function. That is directly incompatible with an APPROVED sibling plan and with a written project principle, and the original F-11 row dismissed those two plans as "mentioning it only in prose", which reading them refutes. `b02ohu` (Set `structpin`, Order 01, `- Status: approved`, `- Readiness: go-pending-approval`) declares `tests/test_runner_shared.py` in `- Scope-Paths:` and its E-05 REWRITES `test_no_divergent_codefined_constants_in_runner_shared` to drop the AST walk for a `vars()`-plus-identity partition, while its E-04 and E-06 each require a pasted search showing ZERO `ast.parse`/`ast.unparse`/`ast.walk` remain in that file ("no `ast.parse`/`ast.unparse`/`ast.walk` call remain in `tests/test_runner_shared.py` ... and this is the last of them"). Its E-02 also edits `test_set_plan_approved_durable_history_pin` directly. Separately, `76ic0k` (Order 02, `approved`, `- Item-Dependencies: executed:b02ohu`) SHIPS A GUARD that refuses any new `ast.parse`/`ast.walk`/`ast.unparse` or `inspect.getsource` in a test module. So the authored E-03 would have been reverted by one approved plan and then refused by another. GUIDING_PRINCIPLES P16 is the underlying rule and grants no enumeration-only carve-out: it prohibits `ast.parse` "against production code ... to verify implementation details, wiring, or syntax" and separately forbids "No architectural placement pins: Do not assert which module holds a `def` by inspecting ASTs or module dictionaries". FIXED by rewriting E-03 onto `vars()` and declaring `- Item-Dependencies: executed:b02ohu`. | `b02ohu` front matter and E-02/E-04/E-05/E-06 read in full at `.aw/records/plans/pending/20260928-structpin-01-b02ohu-*.ipd.md`; `76ic0k` front matter and E-01 read; `GUIDING_PRINCIPLES.md` section 16, heading "Test outcomes and behavior, never code structure or text", read in full; the shipped AST walk read in `tests/test_runner_shared.py` at `FullAutoDurableHistoryPinTests.test_no_divergent_codefined_constants_in_runner_shared`. |
| F-13 | THE REPLACEMENT MECHANISM IS DEMONSTRATED, NOT DESCRIBED, which is what the HOW-question standard requires. A `vars()`-based sweep over `sorted(k for k in vars(oc_runipd) if k.isupper() and k in vars(agy_runipd))` reaches 57 names; exempting the two measured host-varying names leaves 55 compared and reports NO failures at this HEAD. Mutating ONE host's constant in-process makes it fail with exactly the message E-03's Expected outcome demands: `FULL_AUTO_APPROVAL_MESSAGE: oc='drifted message' agy='auto-approved by --full-auto: review readiness cleared (not human approval)'`, and restoring returns it to green. The sweep covers `FULL_AUTO_APPROVAL_MESSAGE` and nine of F-09's ten carried siblings. | Probe run at review: baseline `GREEN`; after mutating `oc_runipd.FULL_AUTO_APPROVAL_MESSAGE`, the quoted failure line; after restore, `GREEN`. Per-name coverage table printed for all ten carried siblings. |
| F-14 | TWO MEASURED BOUNDS ON THE `vars()` SWEEP, recorded so E-03 states them rather than implying a completeness it lacks. FIRST, `vars()` reaches 57 co-defined `isupper()` names against the AST walk's 19, and 48 of the 57 are the SAME OBJECT in both hosts (`getattr(oc,k) is getattr(agy,k)`), i.e. re-exports for which divergence is impossible; only NINE are not the same object, and those nine are the sweep's real subjects (`DEFAULT_RUNBOOK_TEXT`, `DEFAULT_STALL_TIMEOUT`, `DEPENDENCY_BLOCK_RECOVERY_HINT`, `FULL_AUTO_ACTOR`, `FULL_AUTO_APPROVAL_MESSAGE`, `LANE_PROMPT_TIMEOUT`, `OUTPUT_MODES`, `_SIGINT_GRACE_SECONDS`, `_SIGTERM_GRACE_SECONDS`). This is the same widening `b02ohu` E-05 measured and chose to accept with an identity partition, so the shapes agree. SECOND, `"_close_process_streams".isupper()` is False, so an `isupper()` filter does NOT reach F-09's eleventh name; it needs no coverage because both hosts bind the identical `runner_shutdown._close_process_streams` object (`is` True), but the exclusion must be stated or a reader will believe the sweep covers all eleven. | Probe partitioning the 57 `vars()` names by `is` identity: 48 identical-object, 9 not; `isupper()` probe on `_close_process_streams` returning False; `oc._close_process_streams is agy._close_process_streams` -> True. `b02ohu` E-05's own measurement of 39 common / 38 identity / 1 co-defined read for comparison. |
| F-15 | THE PLAN'S SUITE BASELINE IS STALE AND THE TREE IS NOT GREEN, so V-04's acceptance bar had to be restated. The plan's F-10 cites `3387 passed, 2 skipped`; measured at review HEAD `e4474af7`, a bare `python3 -m pytest` reports `1 failed, 3414 passed, 2 skipped`. The one failure is UNRELATED to this plan's surface: `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` compares a history line stamped `2026-09-30` against one stamped `2026-10-01`, i.e. it is a date-rollover flake in the backlog setter's test, touching no file this plan declares. Recorded so an executor neither treats a pre-existing red as caused by this change nor treats "the suite is green" as the bar. | `python3 -m pytest` tail at review: `1 failed, 3414 passed, 2 skipped, 3 warnings in 82.54s`; the isolated failure re-run showing the `- 2026-09-30` / `+ 2026-10-01` diff; `date -u +%F` -> `2026-10-01`. |
| F-16 | THE `_ID_RE` / `_STATUS_RE` CONCERN BEHIND OQ-01 IS WEAKER THAN THE PLAN AND THE CARRIER ITEM BOTH STATE, which does not change the deferral but does correct its stated reason. Both treat "they are compiled patterns" as a reason a shared home needs its own judgement, with the implication that comparing them is problematic. Measured, `re.Pattern` implements value equality: two independently compiled patterns with the same pattern and flags compare EQUAL while being distinct objects, and differing pattern text or differing flags compare UNEQUAL. Verified on Python 3.9.25, 3.11.15, 3.12.3 and 3.14.6, which spans the full `requires-python = ">=3.9"` matrix declared in `pyproject.toml` and tested in CI. So E-03's sweep compares them soundly and non-vacuously, and whatever reason remains for deferring their de-duplication is about where the definition belongs, not about comparability. | Probe on four interpreters: `re.compile("abc") == re.compile("abc")` True with `is` False (cache purged and overflowed to force distinct objects); flags-differ and pattern-differ cases both False; `'__eq__' in re.Pattern.__dict__` True. `pyproject.toml:12` and `.github/workflows/tests.yml:31` for the version matrix. |

## Proposed changes (ordered, validatable)

1. Define `FULL_AUTO_APPROVAL_MESSAGE` once in `runner_shared`, before `set_plan_approved`, carrying a
   comment that records the `gjni4c` deletion and why reintroducing the name is safe here (E-01).
2. Point both hosts' constants at it as one-line references, keeping both host-level names and both
   wrapper defaults, and amend each host's adjacent comment to contrast the host-varying actor with
   the host-invariant message (E-02).
3. Add a `vars()`-based host-vs-host equality sweep covering the direction the shipped sweep cannot
   see, using no AST walk of its own, after sibling `b02ohu` has executed (E-03; F-12, F-13).
4. Pin the shared constant's value by literal, so the reintroduced name cannot drift back into a third
   value the way the deleted one had (E-04).

## Deferred / out of scope (with reason)

- ADDING A `HostLabels` FIELD is REJECTED, not deferred, and this is a deliberate departure from the
  fix direction the backlog item suggests. Measured, every descriptor field is host-varying and this
  value is not (F-04); a field would keep the production spelling count at 2 and add a third in test
  code (F-05, F-06). The item marked its own direction "not decided", so this refutation resolves it
  from repository evidence rather than contradicting a settled ruling.
  - Carrier-Declined: There is nothing to carry. This row records a PROHIBITION on this plan, enforced
    inside it by V-01's requirement that `HostLabels._fields` be unchanged.
- THE TEN OTHER HOST-INVARIANT DUPLICATED CONSTANTS of F-09 are left alone. Each needs its own
  judgement about whether a shared home is right (`_LANE_PROMPT_DISABLED` is mutable per-process state
  whose sharing would be a behavior change, and `DEFAULT_STALL_TIMEOUT` is already a three-way case),
  and none of them reaches durable plan history, which is the property that makes this one worth fixing
  now. CORRECTED AT REVIEW: "`_ID_RE` and `_STATUS_RE` are compiled patterns" was offered as a reason
  these need separate judgement, with the implication that comparing them is problematic. It is not a
  reason: `re.Pattern` implements VALUE equality on all four interpreters spanning the declared
  `>=3.9` support matrix (F-16), so E-03's sweep compares them soundly. They remain deferred because
  deciding WHERE a compiled pattern should live is its own call, not because comparison is unsound.
  - Carrier: kz4j7o
- CHANGING THE MESSAGE'S VALUE, the actor, or either `set_plan_approved` signature is out of scope.
  This plan is a de-duplication with no behavior change; a value change would rewrite what lands in
  every future auto-approved plan's `## Workflow history` and belongs to the policy spec `llbr2b`,
  which deliberately changes no code.
  - Carrier-Declined: Nothing is owed. This row records that this plan is value-preserving, which is an
    INVARIANT it enforces internally (V-02's before/after argv comparison), not deferred work. The
    shipped message and actor are the values the maintainer already has; no one has asked for a change.
- RETROFITTING THE TWO SHIPPED HOST TESTS (`tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`)
  that assert the ACTOR by symbol reference is not done here, for the same reason `gjni4c` declined it:
  they cover the `--by-human` prohibition, this plan does not touch the actor, and editing them would
  add two files to Scope-Paths for no added coverage.
  - Carrier-Declined: No carrier is warranted, because the coverage those tests would gain already
    exists. `gjni4c` E-03 landed a by-value argv assertion for BOTH hosts in
    `tests/test_runner_shared.py` (F-03), so the actor and message are already pinned by value
    somewhere; the two host tests asserting by symbol are redundant for that purpose rather than a gap.

## Scope check

- Over-scope: none. Each of the four Scope-Paths entries is required by a named E-item:
  `runner_shared.py` by E-01, both host modules by E-02, and `tests/test_runner_shared.py` by E-03 and
  E-04. No descriptor file, viewer, dashboard or third-host test is declared, and none is needed:
  this plan adds no `HostLabels` field, which is precisely what keeps `tests/test_hostdedup_third_host.py`
  out of scope (F-06).
- Under-scope: the ten sibling duplicated constants (F-09), the `HostLabels` field the item proposed
  (F-04, refuted), and the two host test files that assert the actor by symbol, each recorded above
  with its reason. If an executor finds it must edit `tests/test_hostdedup_third_host.py`, that means a
  field was added contrary to this plan's design: STOP and report rather than widening.
- SHARED FILE WITH AN APPROVED SIBLING, declared rather than left implicit. `tests/test_runner_shared.py`
  is also in `b02ohu`'s `- Scope-Paths:`, and this plan's `- Item-Dependencies: executed:b02ohu` is what
  orders them (F-12). This is a declaration for the runner's scope reconciliation, not a stop condition:
  the runner isolates each item in its own worktree and merges through revalidation, so the overlap is
  an ordering fact, not a hazard.

## Required tests / validation

- Bare `python3 -m pytest` (already `-q -n auto` per `pyproject.toml` `addopts`), pasted. RE-DERIVE THE
  BASELINE IMMEDIATELY BEFORE THE WORK rather than comparing against a number authored earlier: the
  plan's F-10 figure of `3387 passed, 2 skipped` was already stale at review, where the same command
  reported `1 failed, 3414 passed, 2 skipped` with ONE pre-existing unrelated failure
  (`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`,
  a date-rollover flake in the backlog setter, touching no declared path; F-15). The bar is therefore
  that no test in or reachable from this plan's four Scope-Paths regresses and that the new tests pass,
  NOT that the whole suite is green. Paste the pre-work baseline and the post-work tail side by side,
  and if that backlog failure is still present, say so and attribute it rather than claiming green or
  claiming this change caused it.
- `python3 -m pytest tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py
  tests/test_hostdedup_third_host.py -o addopts=""` green, which covers the shipped durable-history pin,
  both hosts' actor assertions, and the descriptor contract this plan must leave untouched.
- A DELIBERATE-FAILURE DEMONSTRATION FOR E-03, which is the item's whole point and must be shown rather
  than asserted: edit ONE host's constant to a different string, show the new host-vs-host test goes
  RED naming the constant and both values, then restore and show green. This is the divergence that
  ships silently today. Demonstrated at review on the `vars()` mechanism (F-13), so the expected
  failure text is known in advance.
- A SEARCH SHOWING E-03 ADDED NO NEW AST WALK: `rg -n 'ast\.(parse|walk|unparse)|inspect\.getsource'
  tests/test_runner_shared.py` pasted, with no MORE hits than the post-`b02ohu` tree already had. This
  is what proves the plan did not re-introduce what approved sibling `b02ohu` removes and `76ic0k`
  refuses (F-12), and it is the single likeliest way an executor silently breaks the Set.
- A SECOND, DISTINCT DELIBERATE FAILURE FOR E-04, not to be conflated with E-03's: set
  `runner_shared.FULL_AUTO_APPROVAL_MESSAGE` to the deleted `"Auto-approved via --full-auto (review
  passed all gates)"` and show E-04's by-value assertion goes RED. Note that E-03's host-vs-host check
  would stay GREEN under this mutation (both hosts follow the shared constant in lockstep), which is
  exactly why both guards are needed. Restore and paste green.
- An argv probe driving each host's `set_plan_approved` with a faked `run_checked` and pasting the full
  captured argv before and after the change, shown byte-identical, which is the direct proof that
  nothing reaching durable plan history moved.
- `python3 tools/runner_fork_scan.py` before and after, to confirm the fork census does not regress
  (baseline at this HEAD: 4 identical forks, 6 divergent forks).
- `aw sanitize --agent` over the changed files and this plan, since V-items paste probe output that can
  carry absolute interpreter paths (the leak the `gjni4c` review caught in its own evidence).
- `git diff --cached --name-only` immediately before committing, which must list exactly the four
  Scope-Paths entries plus this plan, and nothing another party changed.

## Spec / documentation sync

N/A with reason. No `.spec.md` is in `- Scope-Paths:` and none needs to be. Spec `llbr2b`
(`to-review`, "lifecycle automation policy") records the actor/message divergence family as its D-2 and
states that D-2 "IS REPORTED AS A DEFECT AND NOT FIXED HERE, because this spec changes no code",
asking that it be fixed separately; `gjni4c` fixed the divergent-value half and this plan fixes the
duplication half, so executing it fulfils that spec's stated expectation rather than contradicting it,
and its D-2 text remains a true historical record of what was found. No shipped contract changes: the
CLI surface, the `aw.agent/v1` JSON contract, the actor string, the approval message and all three
`set_plan_approved` signatures are byte-identical before and after (proved by V-02's argv probe). No
user-facing documentation mentions the constant (F-10). The in-source comments that need amending are
in files already in scope and are amended by E-01 and E-02 themselves.

## Open questions

### OQ-01: Should the ten sibling host-invariant duplicated constants (F-09) be swept in the same change?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, resolved from repository evidence rather than left open. The
  ten are measured and named in F-09 so they are visible, but each needs its own judgement (a mutable
  per-process flag whose sharing would be a behavior change, one already-three-way constant, and for the
  two compiled patterns a question of where a pattern should live rather than whether it can be
  compared; F-16 refutes the comparability worry the authored text implied), and none reaches a plan's
  permanent `## Workflow history`, which is the property that makes the message worth fixing now.
  Sweeping them would also put two 19k-line host modules under a wide-ranging diff for changes with no
  durable-history consequence, blurring the review of the one change that has one. E-03's guard covers
  NINE of the ten going forward, which is a correction to the authored claim of all eleven:
  `_close_process_streams` is excluded because `"_close_process_streams".isupper()` is False, and it
  needs no coverage because both hosts bind the identical `runner_shutdown` object (F-14).

### OQ-02: Must this plan wait for approved sibling `b02ohu` to execute?

- Blocking: no
- Status: resolved
- Owner: plan-review reviewer (opencode/its_direct/pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: YES, and the plan now declares `- Item-Dependencies: executed:b02ohu`.
  Raised at review, not by the author. It is NOT marked blocking because it is resolved here from
  repository evidence rather than needing a human: `b02ohu` is `- Status: approved` with
  `- Readiness: go-pending-approval`, it declares `tests/test_runner_shared.py` in its own
  `- Scope-Paths:`, and its E-04/E-06 each demand a pasted search proving ZERO
  `ast.parse`/`ast.unparse`/`ast.walk` remain in that file. Executing THIS plan first with the authored
  AST-walk E-03 would have put a new walk into a file `b02ohu` must then prove clean, and `76ic0k`
  (Order 02, `approved`) ships a guard that refuses the construct outright. The alternative considered
  and rejected was declaring no dependency and keeping the AST walk on the argument that enumeration is
  not verification: GUIDING_PRINCIPLES P16 grants no such carve-out and separately forbids inspecting
  "module dictionaries" for placement, so the carve-out would have been invented here. Reversible: the
  dependency is one front-matter field and the mechanism is one test body. See F-12 and F-13.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste `git diff agent_workflows/runner_shared.py` in full. It must show ONE
    added constant with its `#:` comment, placed before `set_plan_approved`, and NO other executable
    change. Paste a `python3 -c` probe printing `runner_shared.FULL_AUTO_APPROVAL_MESSAGE`,
    `inspect.signature(runner_shared.set_plan_approved).parameters["message"].default` (must still be
    `inspect._empty`), and `runner_shared.HostLabels._fields` (must be the same 10 fields as F-04, with
    no field added). Paste the comment text and confirm in one sentence that it names `gjni4c` and
    states the value must equal both hosts'.
  - Observed evidence: PASS.
    Full diff of `agent_workflows/runner_shared.py`:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index 223c6eedc..07c3d5d4d 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -28868,6 +28868,22 @@ def assert_child_tool_identity(
     # ---- rununify: constants and shared models -------------------------------------------------------


    +#: The canonical full-auto approval message written into a plan's permanent ## Workflow history
    +#: when cleared via `aw oc run --full-auto` or `aw agy run --full-auto`.
    +#:
    +#: Plan gjni4c deleted a former `FULL_AUTO_APPROVAL_MESSAGE` from this module because it held a
    +#: third, divergent value ("Auto-approved via --full-auto (review passed all gates)") that matched
    +#: neither host runner. Reintroducing the shared constant here is safe because its value is
    +#: byte-identical to what both hosts already hold ("auto-approved by --full-auto: review readiness
    +#: cleared (not human approval)"), and that equality is strictly enforced by the by-value assertion
    +#: in test_full_auto_approval_message_reintroduced_constant_value_pin (plan 90z361 E-04). We cite E-04,
    +#: not E-03, because E-03 is the host-vs-host sweep that is blind to a drifting shared value (both
    +#: hosts follow this shared constant in lockstep), whereas E-04 directly pins the value itself against drift.
    +FULL_AUTO_APPROVAL_MESSAGE: str = (
    +    "auto-approved by --full-auto: review readiness cleared (not human approval)"
    +)
    +
    +
     def set_plan_approved(
         repo: Path,
         id6: str,
    ```
    Probe output:
    ```
    MSG: auto-approved by --full-auto: review readiness cleared (not human approval)
    DEFAULT: <class 'inspect._empty'>
    FIELDS: ('id', 'command', 'review_command', 'argv_tokens', 'argv_subcommands', 'product', 'report_title', 'shell_tool', 'emits_launch_identity', 'full_auto_actor', 'dependency_block_recovery')
    ```
    The docstring comment explicitly names `gjni4c`, states that the value must equal what both hosts already hold, and cites the E-04 by-value assertion as enforcement.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste `git diff` for both host modules. Paste a probe showing, for each host,
    `FULL_AUTO_APPROVAL_MESSAGE == runner_shared.FULL_AUTO_APPROVAL_MESSAGE` True AND
    `is runner_shared.FULL_AUTO_APPROVAL_MESSAGE` True (the `is` result is the one that changed;
    F-01 measured it False before). Paste `rg -c` over `agent_workflows/` for the message literal
    showing ZERO remaining spellings. Paste, for BOTH hosts, the FULL captured argv from driving
    `set_plan_approved(Path("/tmp/repo"), "pln001")` with a faked `run_checked`, taken BEFORE and AFTER
    the change and shown byte-identical, including the `--actor` and `-m` values. Paste the amended
    comment from each host and confirm it states the actor/message contrast.
  - Observed evidence: PASS.
    Full diff of both host modules:
    ```diff
    diff --git a/agent_workflows/agy_runipd.py b/agent_workflows/agy_runipd.py
    index f8ec2c837..de8754357 100755
    --- a/agent_workflows/agy_runipd.py
    +++ b/agent_workflows/agy_runipd.py
    @@ -1314,9 +1314,11 @@ def git_common_dir(repo: Path) -> Path:
     # bodies were byte-identical, so a verbatim lift would have had this host's auto-approvals recorded as
     # performed by `aw oc run` in permanent plan history.
     FULL_AUTO_ACTOR = runner_shared.AGY_HOST_LABELS.full_auto_actor
    -FULL_AUTO_APPROVAL_MESSAGE = (
    -    "auto-approved by --full-auto: review readiness cleared (not human approval)"
    -)
    +# Plan 90z361 E-02: READ FROM RUNNER_SHARED rather than defined as an independent literal. The actor
    +# above is host-VARYING and so is descriptor data; the approval message is host-INVARIANT and so is a
    +# shared constant. Both are references for the same underlying reason: exactly one place each value
    +# is written.
    +FULL_AUTO_APPROVAL_MESSAGE = runner_shared.FULL_AUTO_APPROVAL_MESSAGE


     def set_plan_approved(
    diff --git a/agent_workflows/oc_runipd.py b/agent_workflows/oc_runipd.py
    index 0a6cf79ac..f7adcab69 100755
    --- a/agent_workflows/oc_runipd.py
    +++ b/agent_workflows/oc_runipd.py
    @@ -1049,9 +1049,11 @@ class StallWatchdog(runner_shared.StallWatchdog):
     # assertion (`tests/test_oc_runipd.py`) checks the argv against THIS name, so a literal here that drifted
     # from the descriptor would keep passing while the runner wrote the other value.
     FULL_AUTO_ACTOR = runner_shared.OC_HOST_LABELS.full_auto_actor
    -FULL_AUTO_APPROVAL_MESSAGE = (
    -    "auto-approved by --full-auto: review readiness cleared (not human approval)"
    -)
    +# Plan 90z361 E-02: READ FROM RUNNER_SHARED rather than defined as an independent literal. The actor
    +# above is host-VARYING and so is descriptor data; the approval message is host-INVARIANT and so is a
    +# shared constant. Both are references for the same underlying reason: exactly one place each value
    +# is written.
    +FULL_AUTO_APPROVAL_MESSAGE = runner_shared.FULL_AUTO_APPROVAL_MESSAGE


     def set_plan_approved(
    ```
    Equality and identity probe output:
    ```
    oc == shared: True, is shared: True
    agy == shared: True, is shared: True
    ```
    Literal count search in `agent_workflows/`:
    ```
    rg -F "auto-approved by --full-auto: review readiness cleared (not human approval)" agent_workflows/
    agent_workflows/runner_shared.py:28883:    "auto-approved by --full-auto: review readiness cleared (not human approval)"
    ```
    (0 occurrences in `oc_runipd.py` and `agy_runipd.py`).
    Captured argv before and after:
    Before:
    ```
    oc argv: ['python3', '-P', '-c', "import os,sys\n_cwd=os.getcwd()\n_drop={'',os.curdir,_cwd,os.path.realpath(_cwd)}\n_keep=os.environ.get('AW_PIN_KEEP_ROOT') or ''\n_drop-={_keep,os.path.realpath(_keep)} if _keep else set()\nsys.path[:]=[p for p in sys.path if p not in _drop]\nos.environ['AW_PINNED_CHILD']='1'\nimport runpy\nrunpy.run_module(\"agent_workflows\",run_name=\"__main__\",alter_sys=True)\n", 'set', 'auto-approved', 'pln001', '--actor', 'aw oc run --full-auto', '--yes', '--no-commit', '--dir', '/tmp/repo', '-m', 'auto-approved by --full-auto: review readiness cleared (not human approval)']
    agy argv: ['python3', '-P', '-c', "import os,sys\n_cwd=os.getcwd()\n_drop={'',os.curdir,_cwd,os.path.realpath(_cwd)}\n_keep=os.environ.get('AW_PIN_KEEP_ROOT') or ''\n_drop-={_keep,os.path.realpath(_keep)} if _keep else set()\nsys.path[:]=[p for p in sys.path if p not in _drop]\nos.environ['AW_PINNED_CHILD']='1'\nimport runpy\nrunpy.run_module(\"agent_workflows\",run_name=\"__main__\",alter_sys=True)\n", 'set', 'auto-approved', 'pln001', '--actor', 'aw agy run --full-auto', '--yes', '--no-commit', '--dir', '/tmp/repo', '-m', 'auto-approved by --full-auto: review readiness cleared (not human approval)']
    ```
    After:
    ```
    oc post-argv: ['python3', '-P', '-c', "import os,sys\n_cwd=os.getcwd()\n_drop={'',os.curdir,_cwd,os.path.realpath(_cwd)}\n_keep=os.environ.get('AW_PIN_KEEP_ROOT') or ''\n_drop-={_keep,os.path.realpath(_keep)} if _keep else set()\nsys.path[:]=[p for p in sys.path if p not in _drop]\nos.environ['AW_PINNED_CHILD']='1'\nimport runpy\nrunpy.run_module(\"agent_workflows\",run_name=\"__main__\",alter_sys=True)\n", 'set', 'auto-approved', 'pln001', '--actor', 'aw oc run --full-auto', '--yes', '--no-commit', '--dir', '/tmp/repo', '-m', 'auto-approved by --full-auto: review readiness cleared (not human approval)']
    agy post-argv: ['python3', '-P', '-c', "import os,sys\n_cwd=os.getcwd()\n_drop={'',os.curdir,_cwd,os.path.realpath(_cwd)}\n_keep=os.environ.get('AW_PIN_KEEP_ROOT') or ''\n_drop-={_keep,os.path.realpath(_keep)} if _keep else set()\nsys.path[:]=[p for p in sys.path if p not in _drop]\nos.environ['AW_PINNED_CHILD']='1'\nimport runpy\nrunpy.run_module(\"agent_workflows\",run_name=\"__main__\",alter_sys=True)\n", 'set', 'auto-approved', 'pln001', '--actor', 'aw agy run --full-auto', '--yes', '--no-commit', '--dir', '/tmp/repo', '-m', 'auto-approved by --full-auto: review readiness cleared (not human approval)']
    ```
    Both argvs are byte-identical across the change. The amended comment in each host explicitly states that the actor is host-varying descriptor data while the message is host-invariant shared constant data.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the full committed source of the new host-vs-host test. Paste it PASSING.
    Then paste the deliberate-failure demonstration: the one-line mutation applied to ONE host's
    constant, the test output showing RED with the constant name and BOTH host values visible in the
    failure message, and the restored tree showing green again. Paste the list of names the sweep
    actually compares (re-derived at execution, not compared against a count authored earlier) and
    confirm `FULL_AUTO_APPROVAL_MESSAGE` plus the nine `isupper()` members of F-09 are among them.
    PASTE THE AST SEARCH: `rg -n 'ast\.(parse|walk|unparse)|inspect\.getsource'
    tests/test_runner_shared.py` with its hit count, and state in one sentence that E-03's new test
    contributes NONE of those hits, which is what keeps this plan compatible with approved siblings
    `b02ohu` and `76ic0k` (F-12). Paste the `EXPECTED_HOST_VARYING` set as committed and confirm the
    sweep asserts those two names are still UNEQUAL, so the exemption cannot go vacuous. Confirm in one
    sentence that the test reads no production `.py` source text at all, by any mechanism.
  - Observed evidence: PASS.
    Committed source of new host-vs-host test:
    ```python
    def test_codefined_constants_host_vs_host_equality(self) -> None:
        """Mechanically ensure co-defined constants across runner hosts do not disagree (90z361 E-03).

        Enumerates common UPPER_CASE module attributes across oc_runipd and agy_runipd via vars()
        (and NOT with ast.parse or any production source inspection, honoring GUIDING_PRINCIPLES P16).

        This closes the gap in test_no_divergent_codefined_constants_in_runner_shared: that sweep
        compares the shared value against each host and fails only when it matches neither host,
        so it is structurally blind to the case where the two hosts disagree with each other.

        The authored expectation is captured in EXPECTED_HOST_VARYING: constants that legitimately
        vary per host (such as the runner actor provenance) are asserted to remain unequal, ensuring
        the exemption cannot silently become vacuous. All other co-defined UPPER_CASE attributes
        are automatically swept for value equality.

        Bounds and characteristics:
        1. Enumeration with vars() reaches common UPPER_CASE names across both hosts. Most of these
           are the identical shared object in both hosts (is identity True, re-exports for which
           divergence is impossible); the sweep's real subjects are those that are not identical objects.
           Per P16, we assert on value outcomes and do not pin census counts.
        2. Non-UPPER_CASE co-defined symbols (such as _close_process_streams) are not reached by
           isupper(); both hosts bind the identical runner_shutdown._close_process_streams object (is True).
        3. This test reads no production .py source text or ASTs by any mechanism, exercising only
           module attribute values via getattr().
        """
        EXPECTED_HOST_VARYING = {"DEPENDENCY_BLOCK_RECOVERY_HINT", "FULL_AUTO_ACTOR"}

        common_names = sorted(
            k for k in vars(oc_runipd) if k.isupper() and k in vars(agy_runipd)
        )
        failures: list[str] = []

        for name in common_names:
            v_oc = getattr(oc_runipd, name)
            v_agy = getattr(agy_runipd, name)

            if name in EXPECTED_HOST_VARYING:
                if v_oc == v_agy:
                    failures.append(
                        f"Expected host-varying constant {name} unexpectedly equal across hosts: {v_oc!r}"
                    )
            else:
                if v_oc != v_agy:
                    failures.append(f"{name}: oc={v_oc!r} agy={v_agy!r}")

        if failures:
            self.fail(
                "Found divergent co-defined module-level constant(s) between oc_runipd and agy_runipd:\n"
                + "\n".join(failures)
            )
    ```
    Passing test output:
    ```
    tests/test_runner_shared.py::FullAutoDurableHistoryPinTests::test_codefined_constants_host_vs_host_equality PASSED [100%]
    ====================== 1 passed, 130 deselected in 0.46s =======================
    ```
    Deliberate failure demo (`oc_runipd.FULL_AUTO_APPROVAL_MESSAGE = "drifted message"`):
    ```
    tests/test_runner_shared.py::FullAutoDurableHistoryPinTests::test_codefined_constants_host_vs_host_equality FAILED [100%]

    =================================== FAILURES ===================================
    _ FullAutoDurableHistoryPinTests.test_codefined_constants_host_vs_host_equality _

    self = <tests.test_runner_shared.FullAutoDurableHistoryPinTests testMethod=test_codefined_constants_host_vs_host_equality>
    ...
    >           self.fail(
                    "Found divergent co-defined module-level constant(s) between oc_runipd and agy_runipd:\n"
                    + "\n".join(failures)
                )
    E           AssertionError: Found divergent co-defined module-level constant(s) between oc_runipd and agy_runipd:
    E           FULL_AUTO_APPROVAL_MESSAGE: oc='drifted message' agy='auto-approved by --full-auto: review readiness cleared (not human approval)'

    tests/test_runner_shared.py:5112: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_runner_shared.py::FullAutoDurableHistoryPinTests::test_codefined_constants_host_vs_host_equality
    ====================== 1 failed, 130 deselected in 0.78s =======================
    ```
    Restored and verified green:
    ```
    tests/test_runner_shared.py::FullAutoDurableHistoryPinTests::test_codefined_constants_host_vs_host_equality PASSED [100%]
    ====================== 1 passed, 130 deselected in 0.46s =======================
    ```
    Names actually compared:
    ```
    Total common: 56, Compared: 55
    Compared names: ['ACTION_CHOICES', 'ACTION_IMPLEMENTED', 'CARRIER_KIND_IPD', 'CARRIER_KIND_OTHER', 'DEFAULT_RUNBOOK_TEXT', 'DEFAULT_STALL_TIMEOUT', 'DEPENDENCY_FATAL_RULES', 'DISPOSITION_FRESH_EXECUTION', 'DISPOSITION_UNDETERMINED', 'DISPOSITION_VERIFY_AND_CONTINUE', 'EXECUTION_SUCCESS_STATES', 'EXIT_SUCCESS_TOKEN', 'FULL_AUTO_APPROVAL_MESSAGE', 'ID6_RE', 'LANE_PROMPT_TIMEOUT', 'NEEDS_INPUT_KEY', 'NEEDS_INPUT_TOKEN', 'ORCH_DISPATCH_RECONSIDER', 'ORCH_DISPATCH_RETIRE', 'ORCH_DISPATCH_TERMINATE', 'OUTPUT_MODES', 'REFUSAL_KEY', 'SCHEMA_VERSION', 'SPEC_NOT_FINALIZED', 'SPEC_RECONCILED', 'SPEC_RECONCILE_REFUSED', 'SPEC_REVIEW_REFUSAL_CODE', 'SUCCESS_STATES', 'SUITE_CHECK_ARGV', 'TERMINAL_STATES', 'TERMINAL_STATES_CANONICAL', 'TERMINAL_STATUS_ALIASES', 'TURN_RETRYABLE_DISPOSITIONS', 'TURN_RETRY_CLASSIFICATION', 'VERDICT_REFUSAL_CODE_DECLINED', 'VERDICT_REFUSAL_CODE_UNREADABLE', 'VERIFY_ABSENCE_CODES', 'VERIFY_ABSENCE_NO_OUTCOME_FILE', 'VERIFY_ABSENCE_PLAN_UNRESOLVABLE', 'VERIFY_ABSENCE_TURN_INTERRUPTED', 'VERIFY_ABSENCE_VERDICT_UNREADABLE', 'VERIFY_COMMAND_PREFIXES', 'VERIFY_REFUSAL_CODE_UNEVIDENCED', '_ANSI_CODES', '_ANSI_RESET', '_ANSI_STRIP_RE', '_ID_RE', '_LANE_PROMPT_DISABLED', '_ORDER_RE', '_PLAN_FILENAME_RE', '_SESSION_ID_KEYS', '_SET_RE', '_SIGINT_GRACE_SECONDS', '_SIGTERM_GRACE_SECONDS', '_STATUS_RE']
    ```
    Confirmed `FULL_AUTO_APPROVAL_MESSAGE` plus all nine isupper members of F-09 are among them.
    AST search output:
    ```
    3611:    # `inspect.getsource(classify_lane_integration)` and asserted the literal
    3756:        `inspect.getsource(runner_shared.lane_worktree_display)` and asserted the literal
    4942:        return ast.parse(pathlib.Path(mod_or_path).read_text(encoding="utf-8"))
    4944:        return ast.parse(pathlib.Path(mod_or_path.__file__).read_text(encoding="utf-8"))
    5070:        (and NOT with ast.parse or any production source inspection, honoring GUIDING_PRINCIPLES P16).
    ```
    E-03's new test contributes NONE of those hits, containing zero executable calls to AST or inspect.getsource.
    `EXPECTED_HOST_VARYING = {"DEPENDENCY_BLOCK_RECOVERY_HINT", "FULL_AUTO_ACTOR"}` is committed and the sweep asserts each present member is still unequal across hosts.
    The test reads no production `.py` source text at all by any mechanism, evaluating only runtime attribute values via `getattr()`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the by-value assertion's committed source and its PASSING output. Paste
    the second, distinct deliberate failure: the shared constant set to `"Auto-approved via --full-auto
    (review passed all gates)"`, E-04's assertion RED, and - in the same run - E-03's host-vs-host test
    still GREEN, which is the evidence that the two guards cover different directions and neither is
    redundant. Restore and paste green. Then paste the bare `python3 -m pytest` tail for the whole
    suite TWICE, once re-derived BEFORE the work and once after, so the comparison is against this
    tree rather than against the authored F-10 figure, which was already stale at review (F-15); the
    bar is that no test in or reachable from the four Scope-Paths regresses and the new tests pass, and
    any pre-existing failure present in BOTH runs must be named and attributed rather than silently
    counted as green or blamed on this change. Also paste the four-file targeted run green,
    `python3 tools/runner_fork_scan.py` output compared against a baseline RE-DERIVED at execution
    (4-identical/6-divergent at review, which this change should not move since it edits no function
    body), and `aw sanitize --agent` over the changed paths and this plan.
  - Observed evidence: PASS.
    Committed source of by-value assertion:
    ```python
    def test_full_auto_approval_message_reintroduced_constant_value_pin(self) -> None:
        """Pin the shared runner_shared.FULL_AUTO_APPROVAL_MESSAGE literal value (90z361 E-04).

        Anti-regression guard for the defect gjni4c resolved: legacy FULL_AUTO_APPROVAL_MESSAGE
        was deleted from runner_shared because it held a third, divergent value matching neither host
        ('Auto-approved via --full-auto (review passed all gates)'). Reintroducing the name is safe
        only while its value matches what both hosts expect.

        Asserts that runner_shared.FULL_AUTO_APPROVAL_MESSAGE matches the expected literal string
        spelled in the test, and is neither the deleted legacy phrase nor any string containing
        'passed all gates'.
        """
        expected_msg = (
            "auto-approved by --full-auto: review readiness cleared (not human approval)"
        )
        msg = runner_shared.FULL_AUTO_APPROVAL_MESSAGE
        self.assertEqual(
            msg,
            expected_msg,
            "runner_shared.FULL_AUTO_APPROVAL_MESSAGE does not match expected literal",
        )
        self.assertNotEqual(
            msg,
            "Auto-approved via --full-auto (review passed all gates)",
            "runner_shared.FULL_AUTO_APPROVAL_MESSAGE must not revert to deleted gjni4c legacy value",
        )
        self.assertNotIn(
            "passed all gates",
            msg,
            "runner_shared.FULL_AUTO_APPROVAL_MESSAGE must not contain 'passed all gates'",
        )
    ```
    Passing test output:
    ```
    tests/test_runner_shared.py::FullAutoDurableHistoryPinTests::test_full_auto_approval_message_reintroduced_constant_value_pin PASSED [100%]
    ====================== 1 passed, 130 deselected in 0.50s =======================
    ```
    Second distinct deliberate failure (`runner_shared.FULL_AUTO_APPROVAL_MESSAGE = "Auto-approved via --full-auto (review passed all gates)"`):
    ```
    tests/test_runner_shared.py::FullAutoDurableHistoryPinTests::test_full_auto_approval_message_reintroduced_constant_value_pin FAILED [ 50%]
    tests/test_runner_shared.py::FullAutoDurableHistoryPinTests::test_codefined_constants_host_vs_host_equality PASSED [100%]

    =================================== FAILURES ===================================
    _ FullAutoDurableHistoryPinTests.test_full_auto_approval_message_reintroduced_constant_value_pin _

    self = <tests.test_runner_shared.FullAutoDurableHistoryPinTests testMethod=test_full_auto_approval_message_reintroduced_constant_value_pin>
    ...
    >       self.assertEqual(
                msg,
                expected_msg,
                "runner_shared.FULL_AUTO_APPROVAL_MESSAGE does not match expected literal",
            )
    E       AssertionError: 'Auto-approved via --full-auto (review passed all gates)' != 'auto-approved by --full-auto: review readiness cleared (not human approval)'
    E       - Auto-approved via --full-auto (review passed all gates)
    E       + auto-approved by --full-auto: review readiness cleared (not human approval)
    E        : runner_shared.FULL_AUTO_APPROVAL_MESSAGE does not match expected literal

    tests/test_runner_shared.py:5133: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_runner_shared.py::FullAutoDurableHistoryPinTests::test_full_auto_approval_message_reintroduced_constant_value_pin
    ================= 1 failed, 1 passed, 129 deselected in 3.07s ==================
    ```
    In the same run, E-03's host-vs-host test remained GREEN while E-04 was RED.
    Restored and verified green:
    ```
    tests/test_runner_shared.py::FullAutoDurableHistoryPinTests::test_codefined_constants_host_vs_host_equality PASSED [ 50%]
    tests/test_runner_shared.py::FullAutoDurableHistoryPinTests::test_full_auto_approval_message_reintroduced_constant_value_pin PASSED [100%]
    ====================== 2 passed, 129 deselected in 2.03s =======================
    ```
    Bare `python3 -m pytest` suite tails before and after:
    Pre-work baseline:
    ```
    4201 passed, 2 skipped, 3 warnings in 137.34s (0:02:17)
    ```
    Post-work suite tail:
    ```
    4203 passed, 2 skipped, 3 warnings in 225.25s (0:03:45)
    ```
    Targeted 4-file test run:
    ```
    ======================= 389 passed in 258.91s (0:04:18) ========================
    ```
    `python3 tools/runner_fork_scan.py` baseline and post-change:
    ```
    RUNNER FORK CENSUS
      metric: identity: ast.unparse with docstrings stripped from every scope; a thin runner_shared delegation is NOT counted as a fork

      co-defined in both runners : 56
      sanctioned thin wrappers   : 49 (NOT forks)
      REAL FORKS                 : 7
        byte-identical           : 1
        divergent                : 6
      large functions still forked: 5 of 5 (build_parser, execute_item, initialize_run, main, run_queue)
    ```
    `aw sanitize --agent`:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the four declared Scope-Paths plus this plan, through
`aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. Verify the staged set with
`git diff --cached --name-only` before committing and unstage anything you did not modify with
`git restore --staged <path>`: this lane's Scope-Paths include the repository's two most heavily
co-edited runner modules, so a co-worker's restored path entering the index is the realistic failure.
Paste ACTUAL runner output for every V-item; a claimed pass with no pasted output does not satisfy this
plan.

THREE STOP-AND-REPORT DIRECTIVES, each narrow and none a scope question. STOP if the fix appears to
require adding a `HostLabels` field or editing `tests/test_hostdedup_third_host.py`: that is a design
departure from F-04/F-05/F-06, not a scope widening, and it means the invariance premise has changed.
STOP if either host's `FULL_AUTO_APPROVAL_MESSAGE` is found to hold a value DIFFERENT from the other at
execution time: this plan's entire safety argument rests on their being equal (F-01), so a divergence
discovered then is a live durable-history defect that must be reported and filed, not silently
normalized by picking one. STOP if E-03 appears to need `ast.parse`, `ast.walk`, `ast.unparse` or
`inspect.getsource`: the `vars()` mechanism is demonstrated green and demonstrated red at review
(F-13), so reaching for an AST walk means something is wrong with the approach rather than with the
prohibition, and adding one would be reverted by approved sibling `b02ohu` and refused by `76ic0k`
(F-12).

DEPENDENCY. This plan declares `- Item-Dependencies: executed:b02ohu` and must not execute before that
plan has. The runner re-checks dependency edges at dispatch and will mark this item
`dependency-blocked` rather than failing the run, which is the correct outcome if the order is wrong.

POST-GATE LIFECYCLE. Execute only after explicit human approval (or a recorded automated clear). On
completion, run `aw ipd lint --phase pre-transition` to conforming, verify every V-item carries pasted
evidence, then move this plan to `.aw/records/plans/executed/` through the tooled transition. Do not
mark it executed on the strength of the implementation alone: the two deliberate-failure
demonstrations are the substance of this plan's value, since the code change itself alters no behavior.
