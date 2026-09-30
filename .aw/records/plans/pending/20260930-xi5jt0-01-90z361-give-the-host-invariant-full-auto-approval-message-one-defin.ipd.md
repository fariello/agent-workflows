# IPD: Give the host-invariant full-auto approval message one definition in runner_shared, with a guard that keeps it host-invariant

- Date: 2026-09-30
- Kind: child
- Concern: `oc_runipd.FULL_AUTO_APPROVAL_MESSAGE` and `agy_runipd.FULL_AUTO_APPROVAL_MESSAGE` are each an independent module-level LITERAL holding the identical string `"auto-approved by --full-auto: review readiness cleared (not human approval)"`, while the sibling `FULL_AUTO_ACTOR` beside each of them is a one-line REFERENCE to `runner_shared.OC_HOST_LABELS.full_auto_actor` / `runner_shared.AGY_HOST_LABELS.full_auto_actor`. So the two names sitting on adjacent lines in both hosts have OPPOSITE duplication properties, and the duplicated one is the one that reaches a plan's permanent `## Workflow history` as the `-m` message. The cost is the ordinary identical-copy hazard `runner_shared`'s own module docstring names: "Two identical copies have no behavioral disagreement TODAY, which is exactly why nothing signals when one is edited and the other is not".
- Scope: IN: (a) define the message ONCE in `runner_shared` as `FULL_AUTO_APPROVAL_MESSAGE`, in the reference-carrying shape the eight other host-invariant co-defined constants already use; (b) turn both hosts' literals into one-line references to it, leaving each host's `set_plan_approved` signature, its default, and the argv it builds byte-identical; (c) extend the shipped `gjni4c` E-01 sweep so a co-defined constant whose two HOST values DISAGREE also fails, which is the direction that sweep structurally cannot currently see and the property this plan must not silently give up. OUT, each with a reason recorded in "Deferred / out of scope": adding a `HostLabels` field (the fix direction the backlog item guesses at, REFUTED by measurement in F-04/F-05 because the value is host-INVARIANT and the descriptor is explicitly a carrier of host-VARYING strings); the ten other host-invariant literal-duplicated constants F-09 measures (a separate sweep, carried); and any change to the message's VALUE, the actor, or `set_plan_approved`'s signature.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: xi5jt0
- Set: xi5jt0
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 90z361

## Workflow history

- 2026-09-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `xi5jt0`. Every measurement in Findings taken against this lane's working tree at HEAD `56043a76`; suite baseline `3387 passed, 2 skipped` (F-10). The item's factual claim is CONFIRMED VERBATIM by AST probe: both hosts assign the message as an independent literal, both assign the actor as a descriptor reference (F-01). THE ITEM'S PROPOSED FIX DIRECTION IS REFUTED, and that is this plan's one substantive departure from the item it graduates. The item recommends "add a HostLabels field ... rather than a module-level shared constant". Measured, every one of the descriptor's 10 fields differs between the two hosts and the message does NOT (F-04), so a field would make a host-INVARIANT value into a per-host parameter and would force each host (plus the third-host test descriptor, which the no-defaults `NamedTuple` obliges) to re-spell the identical string - leaving the literal count at 2 and raising it to 3 in test code, i.e. the duplication the item asks to remove would survive the fix (F-05, F-06). The reference-carrying shared constant the item warns against is instead the ESTABLISHED shape for exactly this class: 8 of the 19 constants co-defined in both hosts already have it, and the shipped `gjni4c` guard PERMITS it by construction, failing only a shared value matching NEITHER host (F-07, F-08). A second correction: the item says `gjni4c` E-03's by-value argv assertion means "a future divergence of the two copies fails a test". Measured, that is TRUE and is why this stays `low`, but it is not the whole guarantee the item implies - the assertion pins each host against a literal spelled in the test, so it catches a host drifting from the EXPECTED value, and E-03 of this plan adds the complementary host-vs-host check the shipped sweep cannot make (F-03, F-08).

## Goal

Give the full-auto approval message ONE definition, so the string that lands in a plan's permanent
`## Workflow history` cannot be edited in one host and missed in the other, and leave behind a guard
that fails if the two hosts' co-defined constants ever disagree. No value changes: the message, the
actor, both `set_plan_approved` signatures and the argv each host builds are byte-identical before and
after.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one definition, two references

- [ ] E-01 In `agent_workflows/runner_shared.py`, define `FULL_AUTO_APPROVAL_MESSAGE` as the single
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
  what both hosts already hold (F-01) and that E-03's extended guard fails if that ever stops being
  true. Carry that reasoning in the constant's `#:` comment, naming `gjni4c` and stating that the
  value MUST equal both hosts' and is enforced by the E-03 guard, so a future reader does not
  re-litigate the deletion or assume the name is forbidden.
  DO NOT give `runner_shared.set_plan_approved`'s `message` parameter a default of this new constant.
  Its no-default property is asserted by the shipped `test_set_plan_approved_durable_history_pin`
  (`inspect.Parameter.empty`), and the host wrappers' defaults are what actually decide the recorded
  message because both live call sites pass two arguments (F-02). Adding a default here would break a
  shipped assertion and would relocate a guarantee this plan is not entitled to move.
  - Depends on: none
  - Expected outcome: `runner_shared.FULL_AUTO_APPROVAL_MESSAGE` exists and equals the message string;
    `inspect.signature(runner_shared.set_plan_approved).parameters["message"].default` is still
    `inspect.Parameter.empty`; no other executable line in the module changes.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`, replace each
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
  - Execution state: pending

### Task group 2: the guard that keeps it invariant

- [ ] E-03 Extend the shipped guard in `tests/test_runner_shared.py` so the host-vs-host direction is
  checked, in the same test module and beside
  `test_no_divergent_codefined_constants_in_runner_shared` whose collection logic it reuses.
  THE GAP IS PRECISE, so do not conflate it with the shipped check. That sweep compares the SHARED
  value against each host and fails only when it "matches neither" (F-08), so it is blind to the case
  where the two HOSTS disagree with each other. Today that blindness is harmless for this constant
  because both hosts hold a literal that happens to agree; after E-02 the shared constant is what
  makes them agree, and the property worth pinning is the one the backlog item is actually about.
  Add a test asserting that for every `UPPER_CASE` module-level name co-defined in BOTH hosts whose
  value is equal today, it is STILL equal - i.e. collect the co-defined set by AST (reuse the existing
  helper rather than re-implementing the walk; extract it to a module-level function if it is inline,
  and say so in the test's docstring) and assert `getattr(oc, n) == getattr(agy, n)` for the names
  measured host-invariant in F-09, naming them explicitly rather than computing the expectation from
  the same `getattr` calls the assertion makes (a test that derives its expectation from the code it
  checks cannot detect a change, which is the self-referential shape `gjni4c` F-07 measured).
  ASSERT OUTCOMES, NOT STRUCTURE, per `AGENTS.md` and GUIDING_PRINCIPLES P16. Reading module-level
  constant VALUES through `getattr` on imported modules is a value comparison, which is what the
  shipped sibling guard already does and is legitimate. The AST walk is used ONLY to enumerate which
  names to compare, never to assert that a particular source spelling is present; do not assert that
  either host's line reads `runner_shared.FULL_AUTO_APPROVAL_MESSAGE`, which would be a code-structure
  pin on a refactor this plan itself performs.
  - Depends on: E-02
  - Expected outcome: a new test in `tests/test_runner_shared.py` passes at the post-E-02 tree, and
    FAILS with a message naming the constant and both host values when either host's constant is
    mutated to a different value.
  - Execution state: pending

- [ ] E-04 Add a by-value assertion that `runner_shared.FULL_AUTO_APPROVAL_MESSAGE` equals the message
  string, spelled out as a literal IN THE TEST rather than read from the module under test, and that it
  is neither the deleted `"Auto-approved via --full-auto (review passed all gates)"` nor any string
  containing `"passed all gates"`. This is the anti-regression for the specific defect `gjni4c`
  deleted: the danger of reintroducing this NAME is that some future edit gives it a third value again,
  and E-03's host-vs-host check would NOT catch that (it compares the two hosts, which would both
  follow the shared constant in lockstep). Put it in the same new test or an adjacent one, and comment
  that it exists because the name was previously deleted for holding a value no host held.
  - Depends on: E-01
  - Expected outcome: the assertion passes at the post-E-01 tree and fails if the shared constant's
    value is edited to anything other than the message both hosts record.
  - Execution state: pending

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

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE DEFECT IS LIVE AT THIS HEAD, exactly as filed. An AST probe over module-level assignments in both hosts reports `FULL_AUTO_APPROVAL_MESSAGE` assigned as an independent string LITERAL in each (`'auto-approved by --full-auto: review readine...'` in both), while `FULL_AUTO_ACTOR` is assigned as a REFERENCE in each (`runner_shared.OC_HOST_LABELS.full_auto_actor` / `runner_shared.AGY_HOST_LABELS.full_auto_actor`). The two values compare EQUAL (`==` True) but are DISTINCT objects (`is` False, distinct `id()`), which is the signature of two independent literals rather than one shared value. | `ast.parse` walk over `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` module bodies, printing the unparsed RHS per `UPPER_CASE` target; `python3 -c` probe printing `==`, `is` and both `id()`s for the two hosts' constants. |
| F-02 | THE RECORDED MESSAGE COMES FROM EACH HOST'S WRAPPER DEFAULT, not from a caller and not from the shared function. `inspect.signature(runner_shared.set_plan_approved).parameters["message"].default` is `inspect._empty`, while each host's wrapper default IS that host's own constant (`is` identity True for both). Both live call sites pass two arguments (`set_plan_approved_fn(repo, id6)` in the queue-build arm, `set_plan_approved(repo, item["id6"])` in the dispatch arm). This is why E-02 must KEEP the host-level name rather than deleting it, and why E-01 must NOT add a shared default. | `inspect.signature` on all three functions; `is`-identity probe of each host default against that host's constant; both call sites read in `runner_shared` (the `is_plan_review_approved_fn` arm and the `is_plan_review_approved` arm). Corroborated by `gjni4c` F-03a, which measured the same and added E-05 because of it. |
| F-03 | THE ITEM'S STATED MITIGATION IS REAL AND GREEN, which is what keeps this `low`. `tests/test_runner_shared.py::test_set_plan_approved_durable_history_pin` drives each host's `set_plan_approved` with a faked `run_checked`, captures argv, and asserts `argv[argv.index("-m") + 1]` equals the message literal SPELLED IN THE TEST, per host. So a host drifting from the expected value already fails a test. Its limit is the one E-03 closes: it compares each host to a constant in the test, never the two hosts to each other. | `python3 -m pytest tests/test_runner_shared.py -k 'divergent or durable_history' -o addopts=""` -> `2 passed`; the test body read, showing `expected_msg` spelled as a literal and the per-host argv loop. |
| F-04 | THE BACKLOG ITEM'S PROPOSED FIX IS REFUTED BY THE DESCRIPTOR'S OWN CONTRACT AND BY MEASUREMENT. `HostLabels` is documented as "Every host-varying STRING the lifted runner symbols need"; measured, ALL 10 of its fields differ between `OC_HOST_LABELS` and `AGY_HOST_LABELS` (`id`, `command`, `review_command`, `argv_tokens`, `argv_subcommands`, `product`, `report_title`, `shell_tool`, `emits_launch_identity`, `full_auto_actor`), with ZERO fields equal across hosts. The message is EQUAL across hosts. So it is the only candidate that would violate the descriptor's stated invariant, and the `DEPENDENCY_BLOCK_RECOVERY_HINT` precedent pending plan `8eei5p` cites as justification for ITS field is measured host-VARYING, making it a disanalogy rather than a precedent. | Probe printing every `HostLabels._fields` entry with both hosts' values and an equality verdict: 0 equal, 10 differing; `oc.DEPENDENCY_BLOCK_RECOVERY_HINT == agy.DEPENDENCY_BLOCK_RECOVERY_HINT` -> False; `oc.FULL_AUTO_APPROVAL_MESSAGE == agy.FULL_AUTO_APPROVAL_MESSAGE` -> True; the class docstring's first line quoted. |
| F-05 | A `HostLabels` FIELD WOULD NOT REMOVE THE DUPLICATION IT IS MEANT TO REMOVE. The value would have to be written once per descriptor construction, so the production spelling count stays at 2 (`full_auto_actor=`'s two sibling kwargs demonstrate the shape), whereas a shared constant read by both hosts brings it to 1. The item's own fix direction therefore leaves the measured defect ("that string is genuinely duplicated") in place. | Count of production spellings per candidate: today 2 (two host literals); descriptor field 2 (one kwarg per descriptor); shared constant 1 (one definition, two references). Derived from the two `HostLabels(...)` construction sites in `runner_shared`, read in full. |
| F-06 | A FIELD WOULD ALSO ADD A THIRD SPELLING IN TEST CODE. `HostLabels` has no defaults (`_field_defaults` is empty and the shipped guard asserts `TypeError` when a field is omitted), and `tests/test_hostdedup_third_host.py` constructs `SCRIPTED_HOST_LABELS` with all ten fields by keyword. A new field must therefore be supplied there too. Pending plan `8eei5p` confirms this is not hypothetical: its E-07 exists solely to add its new field to that descriptor, warning that omitting it "will raise `TypeError` at IMPORT TIME". | `SCRIPTED_HOST_LABELS` read with its ten keyword arguments; the shipped no-defaults assertion read in `test_set_plan_approved_durable_history_pin` (constructing `HostLabels` with every field except `full_auto_actor` inside `assertRaises(TypeError)`); `8eei5p` E-07 read. |
| F-07 | THE REFERENCE-CARRYING SHARED CONSTANT IS THE ESTABLISHED SHAPE FOR THIS EXACT CLASS. Of 19 `UPPER_CASE`-or-underscore constants co-defined in both hosts, 8 are already `<NAME> = runner_shared.<NAME>` in BOTH hosts: `ACTION_CHOICES`, `ACTION_IMPLEMENTED`, `EXECUTION_SUCCESS_STATES`, `FULL_AUTO_ACTOR`, `SUCCESS_STATES`, `TERMINAL_STATES`, `TERMINAL_STATES_CANONICAL`, `TERMINAL_STATUS_ALIASES`. E-02 makes the message the ninth. | AST walk classifying each co-defined constant's RHS in both hosts as `runner_shared.`-prefixed or not: 8 reference-style, 11 not. |
| F-08 | THE SHIPPED `gjni4c` GUARD PERMITS THIS FIX BY CONSTRUCTION, and its predicate is also what proves E-03's gap. `test_no_divergent_codefined_constants_in_runner_shared` fails only `if v_shared != v_oc and v_shared != v_agy`, so a shared value EQUAL to both hosts passes; three of the already-shared constants (`ACTION_CHOICES`, `SUCCESS_STATES`, `TERMINAL_STATES`) satisfy `shared == oc == agy` and pass today. The same predicate is structurally blind to `v_oc != v_agy`, which is the host-vs-host direction E-03 adds. | The predicate line read verbatim from the test; probe confirming `shared == oc == agy` for the three named constants; the test's collection logic read (AST over module-level `ast.Assign`/`ast.AnnAssign` with `.isupper()` targets, intersected across the three modules). |
| F-09 | THE MESSAGE IS ONE OF ELEVEN, which bounds this plan and names the carried remainder. Probing constants co-defined in both hosts, host-invariant by value, and NOT reference-style yields 11: `DEFAULT_RUNBOOK_TEXT`, `DEFAULT_STALL_TIMEOUT`, `FULL_AUTO_APPROVAL_MESSAGE`, `LANE_PROMPT_TIMEOUT`, `OUTPUT_MODES`, `_ID_RE`, `_LANE_PROMPT_DISABLED`, `_SIGINT_GRACE_SECONDS`, `_SIGTERM_GRACE_SECONDS`, `_STATUS_RE`, `_close_process_streams`. Only `DEFAULT_STALL_TIMEOUT` is also defined in `runner_shared` (a three-way case the hosts ignore). This plan fixes the ONE its backlog item names, because that one reaches durable plan history and the others do not; the remaining ten are carried, not swept in, since each needs its own read of whether a shared home is correct. | Probe listing every co-defined host constant with an `also_in_shared` flag and a source-text-identity flag; 11 host-invariant literal-duplicated, `DEFAULT_STALL_TIMEOUT` the only one with `also_in_shared=True`. |
| F-10 | BASELINE AND SURFACE. Bare `python3 -m pytest` at this lane HEAD reports `3387 passed, 2 skipped, 3 warnings`. The message literal appears exactly 3 times in the tree's Python: once in each host and once in `tests/test_runner_shared.py` (the by-value assertion of F-03). No `.md` outside `.aw/records/` mentions the constant, and no spec governs it. | `python3 -m pytest` tail pasted in V-04; per-file occurrence count of the literal across `agent_workflows/`, `tests/` and `tools/`; `rg` over `*.md` excluding the records trees returning no hits. |
| F-11 | NO PENDING PLAN CONFLICTS ON THIS SYMBOL, but two touch the same descriptor region and one shares two Scope-Paths. `8eei5p` (`mjrac4` 01) declares `runner_shared.py`, both hosts and `tests/test_hostdedup_third_host.py`, and ADDS a `HostLabels` field; `o55eli` (`gxsprh` 01) declares `runner_shared.py` plus the viewer and dashboard and adds a FUNCTION beside the descriptors. Neither touches `FULL_AUTO_APPROVAL_MESSAGE` nor `set_plan_approved`. This plan adds no field and touches neither the descriptors' values nor their field set, so the three are independent; the runner isolates each in its own worktree and merges through revalidation regardless. | `rg` over `.aw/records/plans/pending/` for `FULL_AUTO_APPROVAL_MESSAGE|full_auto_actor|set_plan_approved` returning three plans, each read: the two named above (descriptor-adjacent, neither touching this symbol) and `b02ohu`/`76ic0k` (structure-pin plans mentioning it only in prose). |

## Proposed changes (ordered, validatable)

1. Define `FULL_AUTO_APPROVAL_MESSAGE` once in `runner_shared`, before `set_plan_approved`, carrying a
   comment that records the `gjni4c` deletion and why reintroducing the name is safe here (E-01).
2. Point both hosts' constants at it as one-line references, keeping both host-level names and both
   wrapper defaults, and amend each host's adjacent comment to contrast the host-varying actor with
   the host-invariant message (E-02).
3. Extend the guard with the host-vs-host direction the shipped sweep cannot see (E-03).
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
  judgement about whether a shared home is right (`_ID_RE` and `_STATUS_RE` are compiled patterns,
  `_LANE_PROMPT_DISABLED` is mutable per-process state whose sharing would be a behavior change, and
  `DEFAULT_STALL_TIMEOUT` is already a three-way case), and none of them reaches durable plan history,
  which is the property that makes this one worth fixing now.
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

## Required tests / validation

- Bare `python3 -m pytest` (already `-q -n auto` per `pyproject.toml` `addopts`), pasted, compared
  against the F-10 baseline of `3387 passed, 2 skipped`. Expect the same pass count plus the new tests.
- `python3 -m pytest tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py
  tests/test_hostdedup_third_host.py -o addopts=""` green, which covers the shipped durable-history pin,
  both hosts' actor assertions, and the descriptor contract this plan must leave untouched.
- A DELIBERATE-FAILURE DEMONSTRATION FOR E-03, which is the item's whole point and must be shown rather
  than asserted: edit ONE host's constant to a different string, show the new host-vs-host test goes
  RED naming the constant and both values, then restore and show green. This is the divergence that
  ships silently today.
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
  ten are measured and named in F-09 so they are visible, but each needs its own judgement (compiled
  regexes, a mutable per-process flag whose sharing would be a behavior change, and one already-three-way
  constant), and none reaches a plan's permanent `## Workflow history`, which is the property that makes
  the message worth fixing now. Sweeping them would also put two 19k-line host modules under a
  wide-ranging diff for changes with no durable-history consequence, blurring the review of the one
  change that has one. E-03's guard covers all eleven going forward regardless, since it compares every
  co-defined host-invariant constant, so the remainder is guarded even while unfixed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste `git diff agent_workflows/runner_shared.py` in full. It must show ONE
    added constant with its `#:` comment, placed before `set_plan_approved`, and NO other executable
    change. Paste a `python3 -c` probe printing `runner_shared.FULL_AUTO_APPROVAL_MESSAGE`,
    `inspect.signature(runner_shared.set_plan_approved).parameters["message"].default` (must still be
    `inspect._empty`), and `runner_shared.HostLabels._fields` (must be the same 10 fields as F-04, with
    no field added). Paste the comment text and confirm in one sentence that it names `gjni4c` and
    states the value must equal both hosts'.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `git diff` for both host modules. Paste a probe showing, for each host,
    `FULL_AUTO_APPROVAL_MESSAGE == runner_shared.FULL_AUTO_APPROVAL_MESSAGE` True AND
    `is runner_shared.FULL_AUTO_APPROVAL_MESSAGE` True (the `is` result is the one that changed;
    F-01 measured it False before). Paste `rg -c` over `agent_workflows/` for the message literal
    showing ZERO remaining spellings. Paste, for BOTH hosts, the FULL captured argv from driving
    `set_plan_approved(Path("/tmp/repo"), "pln001")` with a faked `run_checked`, taken BEFORE and AFTER
    the change and shown byte-identical, including the `--actor` and `-m` values. Paste the amended
    comment from each host and confirm it states the actor/message contrast.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the full committed source of the new host-vs-host test. Paste it PASSING.
    Then paste the deliberate-failure demonstration: the one-line mutation applied to ONE host's
    constant, the test output showing RED with the constant name and BOTH host values visible in the
    failure message, and the restored tree showing green again. Paste the list of co-defined names the
    test actually compares, which must be the F-09 set, so a reviewer can confirm it is a real sweep
    and not a single hand-written pair. Confirm in one sentence that the test asserts no source
    spelling and reads no production `.py` text to make an assertion (only to enumerate names).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the by-value assertion's committed source and its PASSING output. Paste
    the second, distinct deliberate failure: the shared constant set to `"Auto-approved via --full-auto
    (review passed all gates)"`, E-04's assertion RED, and - in the same run - E-03's host-vs-host test
    still GREEN, which is the evidence that the two guards cover different directions and neither is
    redundant. Restore and paste green. Then paste the bare `python3 -m pytest` tail for the whole
    suite (must be at least the F-10 baseline `3387 passed, 2 skipped` plus the new tests), the
    four-file targeted run green, `python3 tools/runner_fork_scan.py` output compared against the
    4-identical/6-divergent baseline, and `aw sanitize --agent` over the changed paths and this plan.
  - Observed evidence:
  - Result: pending

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

TWO STOP-AND-REPORT DIRECTIVES, both narrow and neither a scope question. STOP if the fix appears to
require adding a `HostLabels` field or editing `tests/test_hostdedup_third_host.py`: that is a design
departure from F-04/F-05/F-06, not a scope widening, and it means the invariance premise has changed.
STOP if either host's `FULL_AUTO_APPROVAL_MESSAGE` is found to hold a value DIFFERENT from the other at
execution time: this plan's entire safety argument rests on their being equal (F-01), so a divergence
discovered then is a live durable-history defect that must be reported and filed, not silently
normalized by picking one.

POST-GATE LIFECYCLE. Execute only after explicit human approval (or a recorded automated clear). On
completion, run `aw ipd lint --phase pre-transition` to conforming, verify every V-item carries pasted
evidence, then move this plan to `.aw/records/plans/executed/` through the tooled transition. Do not
mark it executed on the strength of the implementation alone: the two deliberate-failure
demonstrations are the substance of this plan's value, since the code change itself alters no behavior.
