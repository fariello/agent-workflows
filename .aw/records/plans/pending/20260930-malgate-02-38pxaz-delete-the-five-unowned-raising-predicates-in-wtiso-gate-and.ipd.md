# IPD: Delete the five unowned raising predicates in wtiso_gate and the dangling test citations that claim they are pinned

- Date: 2026-09-30
- Kind: child
- Concern: `agent_workflows/wtiso_gate.py` is a 443-line module whose ENTIRE consumed surface is one string constant. Measured in this lane by AST-walking every `.py` file in the tree: the only import of the module anywhere is `from agent_workflows.wtiso_gate import AW_MISSING_INPUT as _AW_MISSING_INPUT` in `lane_containment`. Nine predicates, zero product callers. Five of them (`check_lifecycle_role`, `check_hook_bypass`, `classify_retention`, `check_receipt`, `check_protected_refs`) exist only to raise `NotImplementedError` naming an owner that spec-conforming prose admits is RETIRED with no successor, and their fail-loud discipline protects a caller that does not exist. Worse, the module cites `tests/test_containment_predicates.py` and `tests/test_wtiso_adversarial.py` as the tests that pin this state at three sites, and BOTH FILES WERE DELETED in commit `19313eed` (the 2026-09-24 suite trim), so the module asserts an enforcement that is absent. Under GUIDING_PRINCIPLES P15 these predicates are the clearest DELETE class in the tree: each was designed to catch an agent evading a gate (hook bypass, forged receipt, mutated protected ref), and P15 records that such defenses are futile by construction.
- Scope: Delete the five unowned raising predicates, the `_unimplemented` helper that exists only to serve them, and the four stable error codes no surviving surface names, then re-home the one constant `lane_containment` actually imports so the import does not dangle. Strike the three citations to the two deleted test files in the same change, since an edit that preserved them would carry forward a false claim. Amend spec `7ckptx`, which names this module as "the designated home for shared containment predicates" and whose R6.2 requires an unimplemented predicate keep raising, so the contract matches the tree. EXCLUDES the driver attestation token and `lane_worktree_active` (owned by backlog `dvonrn`), EXCLUDES every comment reworded by Order 03, and EXCLUDES the dangling citations elsewhere in the tree (owned by `ikxtkj` and `gia5i7`).
- Scope-Paths: agent_workflows/wtiso_gate.py, agent_workflows/lane_containment.py, .aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md, tests/test_lane_missing_input_token.py
- Item-Dependencies: executed:bec7ee
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: ariaau
- From-Spec: 7ckptx
- Set: malgate
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 38pxaz
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-301..PR-310. EVERY MEASUREMENT IN THIS PLAN WAS RE-DRIVEN RATHER THAN READ AND ALL TEN FINDINGS HOLD: an AST walk of every `.py` outside the module finds exactly ONE import of `wtiso_gate` in the whole tree (`AW_MISSING_INPUT` into `lane_containment`, line 62) against a 443-line module; calling all nine predicates confirms exactly the five named ones raise `NotImplementedError` naming a retired owner; both cited test files are absent and `git show --stat 19313eed` lists them at 731 and 704 deleted lines; the spec's three sites, R6.1's text and the 2026-09-28 maintainer ruling all quote verbatim; and `MISSING_INPUT_TOKEN_FORM` renders `AW_MISSING_INPUT:<repo-relative-path>:<why it is required>` from the single constant exactly as F-9 claims. THE PLAN IS SOUND AND ITS CENTRAL JUDGEMENT IS RIGHT. Four corrections matter. FIRST, THE CITATION COUNT IS SIX, NOT THREE, and the distribution is what makes it material: two sit in the MODULE DOCSTRING and one in `check_scope`'s docstring, both of which survive E-03 under the keep-the-file branch, so 'most will disappear with the deleted docstrings' is false for half of them. SECOND, E-03 SAYS 'four stable error codes' AND THEN LISTS FIVE, and separately leaves `AW_GATE_SCOPE` and `AW_PERMISSION_DEADLINE` with no disposition at all though both are measurably unreferenced outside the module; E-03 now covers all eight codes by rule. THIRD, A16 HAS A THIRD CLAUSE THE PLAN NEVER ADDRESSES ('each implemented shared predicate has unit tests'), which the delete-the-file branch falsifies for the four implemented bodies, so the amendment was incomplete in a way `aw specs check` would not catch. FOURTH, the plan amended a spec without `- From-Spec:`, which `aw check` reported as `check.plan-spec-link-missing`; the field is now set and the finding is cleared. BOTH OPEN QUESTIONS CARRIED `Owner: reviewer` AND ARE NOW RESOLVED: OQ-01 to DELETE the file (nothing imports it after E-02, and P6 plus the measured zero-caller state decide it), OQ-02 to the NO-SUBJECT framing with R6.3 explicitly preserved. Baseline re-measured: `3512 passed, 2 skipped, 3 warnings in 135.66s`, 208 deselected.
- 2026-09-30 same-status (aw set): status unchanged (to-review)

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored while graduating backlog `ariaau`. THREE measurements in this lane changed the plan's shape from what the backlog item describes. FIRST, the item says the predicates are "Pinned by tests/test_containment_predicates.py", so the obvious plan shape was 'retire the pin, then delete'. That file does not exist: nothing pins them, and the module cites it and `tests/test_wtiso_adversarial.py` as live enforcement at three sites, so the deletion is SMALLER and the citation strike is NEW work the item does not mention. SECOND, the item scopes the work to the five raising predicates and the zero-caller `check_scope` body; measured, ALL NINE predicates have zero product callers, including the four documented as REAL, so the honest subject is the module's whole disposition. THIRD, the module cannot simply be deleted, because `lane_containment` imports `AW_MISSING_INPUT` from it and that import is load-bearing (the constant composes `MISSING_INPUT_TOKEN_FORM`, which the worker prompt and the parser both derive from), so the constant must be re-homed rather than dropped. That single fact is why this plan keeps a file rather than removing one.
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Remove the anti-malice predicate skeleton from the shipped package, so that the one rule any surface
actually consumes lives in the module that consumes it and nothing in the tree claims an enforcement it
does not have.

Three separate defects are closed by one change, and they are worth naming separately because a partial fix
leaves the module in a WORSE state than before. (1) Five predicates exist solely to refuse an agent that
deliberately evades a gate, which P15 rules out by construction: "An agent runs as the same user with the
same access we have. It can edit the tool, the gate, the test, the instructions, or the record the gate
reads." (2) Their fail-loud discipline, correct in principle, is protecting a caller that does not exist, so
it buys nothing while costing every reader who must work out whether a stub is a to-do. (3) The module
asserts that tests pin this arrangement, and those tests were deleted, so a reader who checks finds nothing
and cannot tell whether the arrangement was abandoned or the citation rotted. That third one is the same
defect class this repository has already recorded twice (`ikxtkj`, `gia5i7`), both tracing to the same
commit.

WHAT MUST SURVIVE, stated first because it is the constraint that shapes every item below. `AW_MISSING_INPUT`
is REAL and CONSUMED. `lane_containment` imports it to build `MISSING_INPUT_TOKEN_FORM`, the constant from
which BOTH the worker's prompt text and the report parser derive their shape, so the prompt and the parser
provably cannot disagree. Spec `7ckptx` R3.1 depends on that single-definition property. Deleting or
duplicating that constant would fork the one rule in this module that matters, which is the precise hazard
research `x03wgn` Section 7 records and R6.1 forbids. So this plan RE-HOMES the constant into
`lane_containment`, the module that owns the token form and is its only consumer, and removes the reverse
dependency rather than the rule.

FIVE FACTS ESTABLISHED AT AUTHORING. The executor must re-measure rather than copy (E-01).

1. ZERO PRODUCT CALLERS, MEASURED BY AST. Walking every `.py` file in the tree outside the module itself for
   an `Import` or `ImportFrom` naming `wtiso_gate`, or an attribute access on a name bound to it, yields
   exactly one result: `lane_containment`'s import of `AW_MISSING_INPUT`. No caller reaches any of the nine
   predicates. A text grep is misleading here and must not be substituted: the module's own docstrings name
   every predicate dozens of times, so a grep reports hits that are all prose.

2. THE FIVE RAISE, AND NOTHING CAN REACH THEM. Calling each with placeholder arguments confirms
   `check_lifecycle_role`, `check_hook_bypass`, `classify_retention`, `check_receipt` and
   `check_protected_refs` raise `NotImplementedError`. Combined with fact 1, no shipped path can reach any
   raise, so R6.2's fail-loud requirement is satisfied vacuously.

3. THE CITED PINS DO NOT EXIST, AND THERE ARE SIX CITATIONS, NOT THREE (corrected at review; the authored
   count of three was low by half). `tests/test_containment_predicates.py` is cited THREE times: twice in
   the MODULE DOCSTRING (once as CALLING each raising predicate to prove it raises, once as asserting
   `check_scope`'s zero-caller state "structurally") and once inside `check_scope`'s OWN docstring.
   `tests/test_wtiso_adversarial.py` is cited THREE times: twice inside `check_hook_bypass` (once in its
   docstring, once inside the runtime `_unimplemented` message string) and once in `check_protected_refs`'s
   docstring. NEITHER FILE EXISTS; both were deleted in `19313eed`.
   THE DISTRIBUTION IS WHAT MAKES THE COUNT MATTER, which is why E-04 was rewritten around it. Three of the
   six (the two module-docstring citations and `check_scope`'s) sit in prose that SURVIVES E-03 under the
   keep-the-file branch, so the authored claim that "most will disappear with the deleted docstrings" is
   false for half of them and E-04 is doing real work rather than catching a remainder. Only the three
   inside `check_hook_bypass` and `check_protected_refs` vanish with their predicates.
   Note that the `check_scope` citation described an AST-based caller-census test, which is exactly the
   code-structure pin GUIDING_PRINCIPLES P16 and AGENTS.md now forbid, so it must NOT be restored.

4. THE FOUR REAL BODIES ARE ALSO UNCONSUMED, and two of them are pure indirection. `format_missing_input`
   and `parse_missing_input` are one-line delegations INTO `lane_containment`, the module that imports the
   constant back out, so the pair forms a dependency cycle in prose whose only purpose was to present a
   unified predicate surface to callers that never arrived. `check_scope` delegates to
   `ipd_lifecycle._scope_match` and its own docstring records that its zero-caller state is deliberate
   because the Phase-2 consumers "RETIRED unlanded". `check_permission_deadline` is a pure predicate whose
   own docstring says it "has NO product caller" and that the enforcing bound is `MAX_TURN_TIMEOUT` alone.
5. THE SPEC NAMES THIS MODULE EXPLICITLY, so the change requires an amendment and cannot be a silent
   deletion. Spec `7ckptx`'s constraints section says "`wtiso_gate.py` is the designated home for shared
   containment predicates. It exists as a fail-loud skeleton by design: a stub raises `NotImplementedError`
   naming its owning phase". R6.2 requires an unimplemented predicate fail loudly and name its owner, and
   acceptance A16 requires that "each unimplemented one still raises naming its owner". Deleting the stubs
   contradicts A16 as written, which is why this plan declares the spec file and amends it in the same
   change (AGENTS.md: a plan may amend a spec and must declare it).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the deletion is safe before deleting anything

- [ ] E-01 RE-DERIVE THE CALLER CENSUS AND THE RAISE CHECK IN YOUR OWN LANE, because the entire deletion rests on fact 1 and a deletion justified by a stale measurement is how a live guard gets lost. Walk the AST of every `.py` file in the tree except `wtiso_gate.py` itself and report every import of the module and every attribute access on it; do NOT substitute a text grep, for the reason fact 1 gives. Then call each of the nine predicates and record raise or return. Then confirm fact 3 by checking on disk for each cited test file and by `git log --diff-filter=D` for the commit that removed it.
  - Depends on: none
  - Expected outcome: the pasted AST census showing the sole import is `AW_MISSING_INPUT` into `lane_containment`, the pasted nine-predicate raise/return table, and the pasted existence check plus deletion commit for both cited test files. If ANY product caller of ANY predicate exists, STOP: say so explicitly and do not proceed, because the deletion's premise has failed.
  - Execution state: pending

### Task group 2: re-home the one rule that is consumed

- [ ] E-02 MOVE `AW_MISSING_INPUT` INTO `lane_containment` as the single definition, and remove the reverse import. The constant's value must not change: it is the leading token of the worker-facing report form and both the prompt and the parser derive from it, so a changed spelling would break the contract spec `7ckptx` R3.1 states. Define it in `lane_containment` beside `MISSING_INPUT_TOKEN_FORM`, which is its only consumer, and delete the `from agent_workflows.wtiso_gate import ...` line. Update the comments at that site that currently explain the import direction ("`wtiso_gate` declares the code vocabulary a hook prints and a driver matches on") so they describe the new arrangement rather than a module that no longer holds it; keep the still-true point that the prompt, the emitter and the parser all derive from ONE constant, since that is the property being preserved.
  - Depends on: E-01
  - Expected outcome: `lane_containment` defines the constant, imports nothing from `wtiso_gate`, and `MISSING_INPUT_TOKEN_FORM` renders the identical string as before; show the before and after values.
  - Execution state: pending

- [ ] E-03 DELETE THE FIVE UNOWNED RAISING PREDICATES (`check_lifecycle_role`, `check_hook_bypass`, `check_protected_refs`, `classify_retention`, `check_receipt`) and the `_unimplemented` helper that exists only to build their error. THEN RESOLVE THE ERROR-CODE SURFACE BY RULE RATHER THAN BY LIST, because the authored list was wrong twice (it said "four" while naming five, and it omitted two codes entirely). The module defines EIGHT codes: `AW_GATE_SCOPE`, `AW_LIFECYCLE_ROLE`, `AW_MISSING_INPUT`, `AW_GATE_HOOK_BYPASS`, `AW_GATE_PROTECTED_REF`, `AW_PERMISSION_DEADLINE`, `AW_RETENTION_UNKNOWN`, `AW_RECEIPT_INVALID`, plus the `ERROR_CODES` tuple enumerating all eight. Measured at review: `AW_MISSING_INPUT` is the ONLY one referenced anywhere outside the module (a repo-wide grep over `*.py` for the other seven returns nothing), and E-02 re-homes it. So THE RULE IS: `AW_MISSING_INPUT` moves (E-02), and every other code goes along with `ERROR_CODES`, unless the body that names it is kept, in which case keep that code too and say which body keeps it. Do not reproduce a hand-list; re-derive from the module and report the eight-way disposition.
  DECIDE AND RECORD the disposition of the four remaining bodies (`check_scope`, `check_permission_deadline`, `format_missing_input`, `parse_missing_input`) on this test: a body with no caller whose rule is ALREADY single-defined elsewhere is indirection, and the two `missing_input` delegations plainly are (fact 4). If deleting all four leaves the module with nothing, DELETE THE FILE and say so; if you keep any, state which surface is expected to consume it and why that is not a hypothetical need (GUIDING_PRINCIPLES P6). Do NOT preserve a stub to keep an import surface alive: fact 1 shows there is no importer left after E-02. OQ-01 is RESOLVED TO DELETE THE FILE and its reasoning is recorded there; follow it unless E-01's own measurement contradicts the premise, in which case stop and report rather than quietly taking the other branch.
  - Depends on: E-02
  - Expected outcome: the five predicates and the helper are gone; an explicit eight-way disposition of the error codes re-derived from the module rather than copied from this item, with `ERROR_CODES` resolved; a recorded decision for each of the four remaining bodies with its reason; and an explicit statement of whether `wtiso_gate.py` survives at all.
  - Execution state: pending

- [ ] E-04 STRIKE ALL SIX DANGLING CITATIONS to `tests/test_containment_predicates.py` and `tests/test_wtiso_adversarial.py` from whatever prose survives E-03, and add NO replacement citation. THE COUNT IS SIX AND THE SPLIT IS THREE-AND-THREE, corrected at review from the authored "three" (fact 3). THREE VANISH WITH THEIR PREDICATES under E-03: both inside `check_hook_bypass` (its docstring's "THE PREMISE IS PROVEN EVEN THOUGH THE GUARD IS ABSENT" sentence AND the citation embedded in its runtime `_unimplemented` message string, which is easy to miss because it is code rather than a docstring) and the one in `check_protected_refs`'s docstring. THREE DO NOT, and these are this item's real subject: TWO in the MODULE DOCSTRING (one asserting the test "CALLS each one to prove it does", one asserting it "asserts the zero-caller state structurally") and ONE inside `check_scope`'s own docstring. Under the delete-the-file branch all six go with the file and this item reduces to proving it; under any keep branch those three must be struck by hand. Do NOT rely on the authored claim that "most will disappear with the deleted docstrings": measured, exactly half do.
  DO NOT restore either test file, and specifically do not restore the caller-census assertion the module describes: an AST walk over production source to count callers is exactly the code-structure pin AGENTS.md and GUIDING_PRINCIPLES P16 forbid, and the maintainer has ruled such pins will not be restored (recorded on backlog `gia5i7`, citing the 2026-09-28 ruling on `pn7rw3`). Where a struck citation carried a still-true DESIGN point, keep the point and remove only the false claim that a test enforces it. The clearest instance is `check_scope`'s zero-caller rationale: the RETIRED-phase explanation is true and worth keeping; only "`tests/test_containment_predicates.py` asserts it structurally" is false.
  - Depends on: E-03
  - Expected outcome: zero references to either deleted test file anywhere in `agent_workflows/`, with the count struck reported and reconciled against E-01's measured six; no new citation to a nonexistent file or class introduced; and the search result pasted proving it.
  - Execution state: pending

### Task group 3: make the contract match the tree

- [ ] E-05 AMEND SPEC `7ckptx` so it no longer requires what this plan removed. Three sites, each re-verified at review: the constraints bullet naming `wtiso_gate.py` as "the designated home for shared containment predicates ... a fail-loud skeleton by design"; R6.2, "A predicate that is declared but not yet implemented MUST fail loudly rather than return a permissive default, and MUST name its owner"; and acceptance A16.
  A16 HAS THREE CLAUSES AND THE PLAN ORIGINALLY ADDRESSED ONLY ONE, which is the gap review found and the reason this item is longer than its first form. A16 reads in full: "Each implemented shared predicate has unit tests; each unimplemented one still raises naming its owner; and a predicate implemented but not chartered for wiring has no product caller. (R6.1, R6.2, R6.3)". Clause 2 is the one the authored plan named. CLAUSE 1 ("each implemented shared predicate has unit tests") is ALSO falsified by the delete-the-file branch, because the four implemented bodies cease to exist and their unit tests went with the 2026-09-24 trim; a reader after this plan would find a criterion asserting tests for predicates that are gone. CLAUSE 3 ("a predicate implemented but not chartered for wiring has no product caller") cites R6.3 and is the clause that MOTIVATED `check_scope`'s deliberate zero-caller state. Amend all three clauses, and say for each whether it is no-subject or still live.
  KEEP R6.1 UNTOUCHED (one predicate per rule, no forking): it is the requirement this plan HONORS by re-homing the constant rather than duplicating it, and it is independently correct. KEEP R6.3 UNTOUCHED TOO, and this is an addition from review: R6.3 ("Implementing a predicate body and wiring its callers are SEPARABLE deliverables") is the requirement whose only demonstration in the tree was `check_scope`, so deleting that body removes R6.3's example while leaving the rule correct. Say so in the amendment rather than editing R6.3, and do NOT let the loss of its example become an argument for weakening it.
  For R6.2 and A16's clauses 1 and 2, record that the requirement is NOT WITHDRAWN but has NO SUBJECT: a declared-not-implemented predicate no longer exists, and P15 (added 2026-09-26) rules out re-adding the class of predicate these stubs anticipated. State the P15 reasoning explicitly in the amendment, since a future author reading only R6.1 would otherwise re-create the skeleton. Append the amendment to the spec's `## Workflow history` naming this plan and the measurement it rests on.
  DO NOT TOUCH THE SPEC'S TRACEABILITY PROPERTY. Section 4's preamble states that "every requirement below is cited by at least one criterion, with TWO deliberate exceptions" and names them (R3.3a-1 and R4.1b). A16 is the ONLY criterion citing R6.2, so an amendment that deleted A16 outright would break that property and create a third, undocumented exception. Amend A16 in place and keep its `(R6.1, R6.2, R6.3)` citation list intact, so the traceability claim stays true by construction. Run `aw specs check` and paste it.
  - Depends on: E-04
  - Expected outcome: the `git diff` of the three spec sites plus the appended history line, with all three A16 clauses addressed, R6.1 and R6.3 and every other requirement unchanged, A16's requirement-citation list intact, and `aw specs check` conforming.
  - Execution state: pending

- [ ] E-06 ADD A BEHAVIORAL TEST FOR THE ONE PRESERVED PROPERTY, in `tests/test_lane_missing_input_token.py`. The property is the one that would silently break: the emitted report token, the token form published in the worker prompt, and the parser must all still agree after the constant moved. Drive the real functions (`lane_containment.format_missing_input_token`, `lane_containment.parse_missing_input_token`, and the prompt-building path that embeds `MISSING_INPUT_TOKEN_FORM`) and assert a round trip plus that the prompt's published form carries the same leading code the emitter produces. Assert on RETURNED VALUES and RENDERED TEXT ONLY; do not read module source, do not assert which module holds the definition, and do not census callers (AGENTS.md; GUIDING_PRINCIPLES P16). Give the file a docstring naming this plan and stating that it pins the round trip and not the constant's home.
  - Depends on: E-05
  - Expected outcome: a passing new test file, plus the mutation demonstration V-06 requires proving each assertion is sensitive.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation here is by symbol or quoted string; `19313eed` is a durable sha.
- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT (AGENTS.md). Spec `7ckptx` is declared in `- Scope-Paths:` so both runners announce the spec edit before the run starts and the finalize scope gate reconciles it. The amendment is E-05 and its reason is in Spec / documentation sync.
- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (AGENTS.md; GUIDING_PRINCIPLES P16). Doubly load-bearing here. The deleted `tests/test_containment_predicates.py` was itself a structure pin (it asserted a zero-caller state "structurally" and called stubs to prove they raise), so restoring it is forbidden twice over; and the obvious test for this plan ("assert `wtiso_gate` no longer defines X") would be the same violation. E-06 pins the surviving BEHAVIOR instead.
- A DELETION MUST SWEEP ITS REFERENCES (backlog `ariaau`'s own honest limit: "a deletion changes behavior other plans or specs may cite, so each removal must check for and update those references"). E-01 measures the references, E-04 strikes the dangling ones, E-05 amends the spec, and the Scope check states which referencing artifacts are deliberately left alone.
- AN EXECUTED PLAN'S RECORD IS IMMUTABLE (AGENTS.md). Executed plans `8zgybk` (which created this module) and `604wra` (which implemented four of its bodies) cite the deleted test files and describe the skeleton as current. They are NOT edited. A dated `## Workflow history` line pointing at this plan is the permitted addition, and the plan does not require one.
- RUN THE SUITE BARE (AGENTS.md). `pyproject.toml` `addopts` already supplies quiet, parallel and the fast subset; a second `-q` would suppress the `N passed` line this plan requires pasted. Use `-o addopts=""` when a per-test count from a narrowed run is needed.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | The module's entire consumed surface is one string constant | AST walk of every `.py` outside the module: sole result is `from agent_workflows.wtiso_gate import AW_MISSING_INPUT as _AW_MISSING_INPUT` in `lane_containment` | Establishes the deletion is safe and makes E-02 (re-home the constant) the pivot of the plan |
| F-2 | The five raising predicates cannot be reached by any shipped path | Each raises `NotImplementedError` when called; F-1 shows no caller exists | R6.2's fail-loud discipline is satisfied vacuously, so deleting the stubs removes no protection |
| F-3 | Both cited pinning test files were deleted in the suite trim | `tests/test_containment_predicates.py` and `tests/test_wtiso_adversarial.py` absent; `git show --stat 19313eed` lists both, at 731 and 704 deleted lines, and `git log --diff-filter=D` names that commit alone | The backlog item's "Pinned by" premise is false; E-04 strikes the citations and must not restore the files |
| F-3b | **ADDED AT REVIEW: THE CITATION COUNT IS SIX, NOT THREE, AND HALF OF THEM SURVIVE E-03.** The authored count was low by half, and the distribution is what matters: three citations sit in prose E-03 may KEEP (two in the module docstring, one in `check_scope`'s docstring), so the authored claim that "most will disappear with the deleted docstrings" is false for exactly half. One of the six is also inside a RUNTIME STRING rather than a docstring, which an executor sweeping docstrings would miss. | `grep -rn 'test_containment_predicates\|test_wtiso_adversarial' agent_workflows/` returns six lines, at 26, 33, 138, 260, 270 and 289. Mapped to enclosing scope by AST: 26 and 33 are MODULE docstring, 138 is `check_scope`, 260 and 270 are `check_hook_bypass` (270 being the `_unimplemented` message string, i.e. executable code), 289 is `check_protected_refs` | E-04 rewritten around the three-and-three split with the runtime-string instance named; V-04 reconciles the struck count against six |
| F-3c | **ADDED AT REVIEW: E-03'S ERROR-CODE LIST IS WRONG TWICE.** It says "the four stable error codes" and then names FIVE, and it leaves `AW_GATE_SCOPE` and `AW_PERMISSION_DEADLINE` with no disposition at all, though both are as unreferenced as the five it names. The module defines EIGHT codes plus the `ERROR_CODES` tuple over all eight, so an executor following the list literally would delete five, re-home one, and leave two orphans in a file the plan intends to delete. | The module's top-level assigns are `AW_GATE_SCOPE`, `AW_LIFECYCLE_ROLE`, `AW_MISSING_INPUT`, `AW_GATE_HOOK_BYPASS`, `AW_GATE_PROTECTED_REF`, `AW_PERMISSION_DEADLINE`, `AW_RETENTION_UNKNOWN`, `AW_RECEIPT_INVALID`, plus `ERROR_CODES` enumerating all eight. A repo-wide grep over `*.py` for the seven non-`AW_MISSING_INPUT` codes returns NOTHING outside the module | E-03 now resolves the surface BY RULE over all eight and requires the disposition re-derived from the module rather than copied |
| F-4 | The `check_scope` citation described a forbidden code-structure pin | The docstring says the test "asserts the zero-caller state structurally so a future wiring is a deliberate, reviewed act" | E-04 must NOT restore it; AGENTS.md and P16 forbid caller censuses as tests, and the maintainer has ruled such pins will not be restored |
| F-5 | Two of the four REAL bodies are pure indirection back into `lane_containment` | `format_missing_input` / `parse_missing_input` are one-line delegations to `lane_containment.format_missing_input_token` / `parse_missing_input_token` | Supports E-03's decision test: a callerless body whose rule is single-defined elsewhere adds nothing |
| F-6 | `check_permission_deadline`'s own docstring records it has no caller and enforces nothing | "This is a PURE PREDICATE OVER A RECORDED STREAM, not a bound ... it has NO product caller ... the enforcing bound today is `MAX_TURN_TIMEOUT` alone" | Its deletion removes no live guard; E-03 records the decision either way |
| F-7 | The spec names the module and requires the raising behavior | `7ckptx` constraints ("the designated home ... a fail-loud skeleton by design"), R6.2, and A16 ("each unimplemented one still raises naming its owner"); all three quote verbatim at review and `aw specs check` reports all 38 specs conforming today | E-05 exists; the deletion is non-conforming until the spec is amended in the same change |
| F-7b | **ADDED AT REVIEW: A16 HAS THREE CLAUSES AND THE PLAN ADDRESSED ONE.** A16 reads "Each implemented shared predicate has unit tests; each unimplemented one still raises naming its owner; and a predicate implemented but not chartered for wiring has no product caller." The plan names only clause 2. Clause 1 is ALSO falsified by deleting the file, because the four implemented bodies cease to exist while A16 still asserts they have unit tests (which they do not, since those went with the same trim). So the amendment as scoped would have left a criterion asserting tests for predicates that are gone, and `aw specs check` would not catch it because it validates structure rather than claims. | A16 verbatim at `7ckptx`, with its citation list `(R6.1, R6.2, R6.3)`; the four implemented bodies are `check_scope`, `check_permission_deadline`, `format_missing_input`, `parse_missing_input`; `tests/test_containment_predicates.py` (their unit tests) is absent | E-05 now amends all three clauses and states for each whether it is no-subject or still live |
| F-7c | **ADDED AT REVIEW: DELETING `check_scope` REMOVES R6.3'S ONLY DEMONSTRATION, AND R6.3 MUST NOT BE WEAKENED FOR IT.** R6.3 ("Implementing a predicate body and wiring its callers are SEPARABLE deliverables") is cited by A16's third clause, and `check_scope` is the one predicate in the tree that demonstrates the split; its own docstring says so ("the spec R6.3 split, and the one predicate here that demonstrates it"). Losing an example is not a reason to narrow the rule, but a later reader finding R6.3 with no instance might read it as dead. | `check_scope`'s docstring: "BODY IMPLEMENTED, CALLERS DELIBERATELY ABSENT - the spec R6.3 split, and the one predicate here that demonstrates it"; A16's trailing `(R6.1, R6.2, R6.3)` | E-05 now requires R6.3 left UNTOUCHED with the loss of its example stated rather than silently absorbed |
| F-7d | **ADDED AT REVIEW: THE SPEC CARRIES A TRACEABILITY PROPERTY THAT A CARELESS A16 EDIT WOULD BREAK.** Section 4's preamble asserts every requirement is cited by at least one criterion with exactly TWO documented exceptions (R3.3a-1, R4.1b). A16 is the ONLY criterion citing R6.2, so deleting A16 rather than amending it in place would create a third, undocumented exception and falsify the preamble. | Section 4 preamble: "every requirement below is cited by at least one criterion, with TWO deliberate exceptions"; `grep -n 'R6\.2'` over the spec returns exactly two hits, the requirement itself and A16 | E-05 now forbids deleting A16 and requires its citation list kept intact, with `aw specs check` pasted |
| F-7e | **ADDED AT REVIEW: THE PLAN AMENDS A SPEC WITHOUT DECLARING THE MACHINE-READABLE LINK.** `aw check` reported `check.plan-spec-link-missing` on this plan (severity `info`), whose remedy is exactly `aw ipd set 38pxaz --from-spec 7ckptx`. The plan correctly declares the spec in `- Scope-Paths:` and correctly argues the amendment in prose, so this was a missing field rather than a missing intent, but the field is what makes the spec handoff machine-readable. | `aw check` naming the rule, the plan, and the fix command; `check_engine.rule_spec('check.plan-spec-link-missing')` is `severity='info'` | `- From-Spec: 7ckptx` added to front matter; re-running `aw check` clears the finding |
| F-8 | R6.1 is HONORED by this plan rather than weakened | R6.1: "A containment rule consumed by more than one surface MUST live in one predicate that every surface calls. Forking the rule is non-conforming even when the copies agree" | E-02 re-homes the constant to a single definition rather than duplicating it; E-05 must leave R6.1 untouched |
| F-9 | The token form's single-definition property is load-bearing and must survive | `MISSING_INPUT_TOKEN_FORM` composes around the constant, and both the worker prompt text and the parser derive from it, so they "cannot disagree about the shape" | E-06 pins the round trip behaviorally; a careless deletion of the constant would break the prompt/parser agreement silently |
| F-10 | `docs/wtiso-state-taxonomy.md` cites two deleted tests (CORRECTED AT REVIEW: it does NOT cite the module, which strengthens the out-of-scope call rather than weakening it) | Its text names `tests/test_wtiso_taxonomy_freeze.py` and `tests/test_wtiso_characterization.py`, both measured absent. `grep -c 'wtiso_gate' docs/wtiso-state-taxonomy.md` returns `0`, so the authored "cites the module" clause was wrong: the doc shares a name prefix with the module and nothing more | OUT OF SCOPE, and now out of scope for a cleaner reason: those two citations are owned by backlog `ikxtkj`, which lists them by line, AND the doc holds no reference this plan's deletion could dangle. This plan strikes only the citations inside the code it deletes |

## Proposed changes (ordered, validatable)

1. Re-derive the AST caller census, the nine-predicate raise check, and the two deleted-test existence checks (E-01).
2. Re-home `AW_MISSING_INPUT` into `lane_containment` and remove the reverse import (E-02).
3. Delete the five raising predicates, the `_unimplemented` helper, and the unreferenced error codes; decide and record the four remaining bodies (E-03).
4. Strike the three dangling test citations, restoring nothing (E-04).
5. Amend spec `7ckptx`'s constraints bullet, R6.2 and A16, leaving R6.1 untouched (E-05).
6. Add a behavioral round-trip test for the preserved token-form property (E-06).

## Deferred / out of scope (with reason)

- THE DRIVER ATTESTATION TOKEN, `verify_driver_attestation`, `DRIVER_ATTEST_ENV`, and `lane_worktree_active`'s location guess. These are the largest anti-malice mechanism in the tree and backlog `ariaau` marks them ALREADY DECIDED and out of scope; their replacement is designed in backlog `dvonrn` D1/D2. Touching them here would collide with that design.
  - Carrier: dvonrn
- `agent_workflows/private_file.py`. It exists partly to protect the attestation token, so deleting the token might look like it orphans this module. It does NOT: its second consumer is `run_analytics_privacy.load_or_create_salt`, the analytics pseudonym salt, which protects the USER's privacy and is not an anti-malice mechanism at all. No change is owed here, and the token's own carrier will decide what remains.
  - Carrier-Declined: Nothing is owed because the module is not anti-malice machinery. Filing an item would assert a privacy mechanism is in P15's scope, which it is not.
- THE DANGLING CITATIONS IN `docs/wtiso-state-taxonomy.md` (F-10). Filed and itemized by line already.
  - Carrier: ikxtkj
- THE NINE DANGLING `NoRunnerImportTests` CITATIONS in `runner_shared` and `oc_runipd`, same root commit and same fix shape.
  - Carrier: gia5i7
- RESTORING ANY DELETED TEST FILE. Refused on a maintainer ruling rather than deferred: the 2026-09-28 ruling recorded on backlog `gia5i7` says code-pinning guards deleted in the trim "will not be restored" and stale comments should "simply remove references to them without seeking to restore code pins". F-4 shows the `wtiso_gate` pin was exactly such a guard.
  - Carrier-Declined: Nothing is owed because there is no latent work, only a constraint measured as withdrawn. Filing it would assert the repository intends to restore a pin its maintainer has ruled against.
- RE-IMPLEMENTING ANY DELETED PREDICATE AS A WORKING GATE. `check_hook_bypass`'s docstring calls the driver-side re-check "an open gap" and `check_protected_refs` names snapshot diffing as absent. This plan does NOT file carriers for them, and the reason is the point of the whole Set: under P15 these are not gaps but rejected designs. Each targets an agent that deliberately evades a gate (committing with `--no-verify`, mutating a protected ref), and P15 records that "any defense against a deliberately hostile agent is therefore futile by construction".
  - Carrier-Declined: Nothing is owed because filing a carrier would assert the repository intends to build a mechanism its own guiding principle forbids. The audit record (Order 01) captures the DELETE decision and its reasoning, which is the durable record of why no carrier exists.

## Scope check

- Over-scope: none. `agent_workflows/wtiso_gate.py` is the subject. `agent_workflows/lane_containment.py` is required because it holds the only import and is the new home for the constant (E-02), and because its comments describe the old import direction. The spec file is declared because E-05 amends what F-7 measures. `tests/test_lane_missing_input_token.py` is the one new test surface (E-06).
- Under-scope: `agent_workflows/ipd_lifecycle.py` is deliberately NOT declared even though `check_scope` delegates to its `_scope_match` and a comment there mentions the module's "receipt-vs-attempt narrative": deleting a caller does not require editing the callee, and that comment is Order 03's subject under its wording sweep. `docs/wtiso-state-taxonomy.md` is not declared (F-10, owned by `ikxtkj`). No runner file is declared: F-1 shows neither driver imports this module. If the executor concludes an edit outside these four paths is required, that is a scope change to stop and re-declare rather than absorb.

## Required tests / validation

- Bare `python3 -m pytest` with the `N passed` summary line pasted, against a pre-execution baseline captured the same way BEFORE any edit lands. A pre-existing failure must be shown pre-existing by that baseline rather than argued harmless. This is the primary safety evidence for a deletion: if a caller existed that the AST census missed, the suite is where it surfaces. RE-DERIVE THE BASELINE IN THE EXECUTING WORKTREE rather than reusing a figure from this plan: review measured `3512 passed, 2 skipped, 3 warnings in 135.66s` with `208 deselected` at HEAD `d4235e0b`, and that count moves with every merged lane, so it is CONTEXT and never the bar. The property to hold is green, plus exactly the tests E-06 adds.
- A MODULE-DOCSTRING CROSS-CHECK, added at review because the suite cannot catch it: the module's own docstring and `check_scope`'s describe the skeleton arrangement and the two deleted tests, and under any keep-the-file branch they survive E-03. Paste the surviving prose so a reviewer can see no sentence still claims a test enforces anything, which is the half of E-04's work the suite is blind to.
- A targeted run of the new `tests/test_lane_missing_input_token.py` with `-o addopts=""` for the per-test count.
- A MUTATION DEMONSTRATION for E-06: paste each assertion FAILING under a mutation that genuinely breaks the round trip (for example changing the emitted prefix without changing the published form), then PASSING after restore. A passing new test is not evidence it tests anything.
- AN IMPORT CHECK after E-02 and again after E-03: import `agent_workflows.lane_containment` and every module that transitively reaches it, and show `MISSING_INPUT_TOKEN_FORM` renders the identical string before and after the move. A `NameError` or a changed token would be the one way this plan breaks a live path.
- `aw ipd lint --phase pre-transition` conforming, `aw check` no worse than a pre-change baseline with both counts pasted, and `aw sanitize --agent` clean.
- NO TEST MAY ASSERT THAT A SYMBOL WAS DELETED, that a module no longer defines something, or that a caller count is zero. E-03 and E-04 are validated by their diffs and by the reference search (V-03, V-04). Such a test would be the structure pin P16 forbids and would itself become the next stale citation.

## Spec / documentation sync

- SPEC `7ckptx` IS AMENDED BY E-05, declared in `- Scope-Paths:` as AGENTS.md requires. WHY, since a spec edit changes the contract every other plan is reviewed against: the spec names this module by filename as "the designated home for shared containment predicates" and describes its fail-loud skeleton as intentional design, R6.2 REQUIRES a declared-not-implemented predicate to raise and name its owner, and A16 requires that each unimplemented one "still raises naming its owner". Deleting the stubs makes the tree non-conforming against A16 as literally written, so the amendment is not optional and must land in the same change as the deletion.
- WHAT THE AMENDMENT DOES AND DOES NOT DO. It records that R6.2 and A16 have NO SUBJECT rather than that they are withdrawn: the discipline is still right for any future declared-not-implemented predicate, and nothing here weakens it. It ADDS the P15 reason the class is not expected to return, so a later author reading R6.1 alone does not re-create the skeleton. It leaves R6.1 UNTOUCHED, because this plan honors it: the one consumed rule ends up with ONE definition in the module that consumes it, which is R6.1's requirement, and E-02 is careful to move rather than copy for exactly that reason.
- NO OTHER SPEC IS TOUCHED. `25kzda`'s begin-receipt rules, `c4gd2h`'s stop protocol, and `6kwd2e`'s reference to the `AW_MISSING_INPUT` token as "the carrier for its own distinct case" all remain true after E-02, because the token's VALUE and FORM do not change; only the module that defines the constant does. The executor must re-confirm that by searching every `.spec.md` for the constant and the module name, and report the result in V-05.
- NO CHANGELOG ENTRY. No user-visible behavior changes: the deleted predicates were unreachable and the surviving token form is byte-identical.
- HISTORICAL RECORDS ARE LEFT ALONE. Executed plans `8zgybk` (created the module) and `604wra` (implemented four bodies and asserted the stubs stay raising) describe the arrangement this plan removes, and the walkthrough `20260917-lanectn-07` records "Nine predicates in `wtiso_gate.py`, each with its state". Rewriting them would falsify history.

## Open questions

### OQ-01: Should `wtiso_gate.py` be deleted entirely, or kept holding only `AW_MISSING_INPUT`?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW, DELETE THE FILE, on measurement rather than preference. The question was addressed to the reviewer and is answered here so the executor has one branch to follow instead of a judgement call mid-deletion. THE DECIDING MEASUREMENTS, all re-driven at review HEAD: after E-02 the import count is ZERO (an AST walk over every `.py` in the tree finds exactly one import of the module today, `AW_MISSING_INPUT` into `lane_containment`, which E-02 removes); the seven error codes other than `AW_MISSING_INPUT` have NO reference anywhere outside the module; and of the four implemented bodies, two (`format_missing_input`, `parse_missing_input`) are one-line delegations INTO `lane_containment`, so keeping them would preserve a prose-level dependency cycle whose only purpose was a caller surface that never arrived. A module with zero importers, zero callers and zero externally-named constants is not a module anyone can reach. KEEPING IT WOULD BE THE HYPOTHETICAL-NEED CASE P6 FORBIDS: "do not add abstraction, features, or dependencies not traceable to a real need", and the need here is traceable only to retired phases (`qcqhj7`, `rchpms`, both RETIRED 2026-09-02 with no successor). THE COUNTER-ARGUMENT IS REAL AND IS ANSWERED, NOT DISMISSED: `check_scope` and `check_permission_deadline` are genuine working logic and deleting them discards work. But `check_scope`'s rule is NOT LOST, because its own docstring records that `ipd_lifecycle._scope_match` owns the grammar and `ipd_lifecycle.finalize_precheck` already enforces scope today, so the predicate is a context-free wrapper around a live rule rather than the rule itself; and `check_permission_deadline`'s own docstring states "the enforcing bound today is `MAX_TURN_TIMEOUT` alone", so it enforces nothing. Git history is the recovery route for both, and a re-proposal on merit is the conforming way back, which `check_lifecycle_role`'s own docstring already prescribes for its case. ONE OBLIGATION FOLLOWS FROM THIS ANSWER and is recorded in E-05: deleting the implemented bodies falsifies A16's FIRST clause ("each implemented shared predicate has unit tests") as well as its second, so the amendment must cover both.
- Carrier-Declined: No carrier is owed. The decision is implemented inside E-03 and leaves no work unbuilt; the audit record from Order 01 carries the reasoning durably, so a future author can find what was removed and why, and git history carries the deleted bodies verbatim.

### OQ-02: Should the amendment to R6.2 and A16 narrow them, or record them as having no subject?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW, USE THE NO-SUBJECT FRAMING, which is what E-05 already specified; this records the reviewer's assent plus the reason the alternative is actively worse. The discipline is CORRECT and this plan measured no fault in it: a declared-not-implemented predicate SHOULD fail loudly rather than return a permissive default, and the reason to delete these five is that they guard nothing and target malice, not that R6.2 is wrong. THE ALTERNATIVE (narrowing R6.2 to exclude anti-malice predicates) IS REJECTED ON A SPECIFIC HAZARD, not merely on verbosity: narrowing would write an ANTI-MALICE CARVE-OUT into a requirement about FAIL-LOUD DISCIPLINE, conflating two independent rules. R6.2 governs how any unimplemented predicate must behave; P15 governs which predicates are worth declaring at all. A reader who later wants a legitimate non-malice stub would find R6.2 narrowed by a reason that has nothing to do with their case, and the natural reading would be that fail-loud is now optional, which is the permissive default R6.2 exists to forbid. The no-subject framing keeps the two rules orthogonal and puts the P15 reasoning where it belongs, as the reason the CLASS is not expected to return. The honest cost is accepted and named: a requirement with no live subject is text a reader must still parse, which is why E-05 requires the no-subject status stated explicitly rather than left for the reader to infer from an empty tree.
- Carrier-Declined: No carrier is owed. The decision is implemented inside E-05 and leaves no spec requirement in an unreconciled state after this plan executes; R6.1 and R6.3 are preserved intact and A16's requirement-citation list keeps the spec's traceability property true.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted AST caller census, with the method shown to be AST-based (name the walk) and NOT a text grep, listing every import of and attribute access on `wtiso_gate` across the tree. The pasted nine-predicate raise/return table. The pasted existence check for `tests/test_containment_predicates.py` and `tests/test_wtiso_adversarial.py` plus the `git` evidence naming the deleting commit. Plus a `git status --short` showing the measurement modified no file. If any product caller was found, this item is satisfied ONLY by stating that plainly and stopping; proceeding would make every later item unsafe.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the `git diff` of both files for the constant's move, plus the BEFORE and AFTER rendered value of `MISSING_INPUT_TOKEN_FORM` shown to be byte-identical, obtained by importing and printing it rather than by reading the source. Plus proof that `lane_containment` imports nothing from `wtiso_gate` any more, and that the comment at the old import site was updated to describe the new arrangement rather than left describing a module that no longer holds the constant. A changed token value FAILS this item outright.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the `git diff` showing the five predicates and the `_unimplemented` helper removed, plus an EIGHT-WAY ERROR-CODE DISPOSITION TABLE re-derived from the module (not copied from E-03) naming each of `AW_GATE_SCOPE`, `AW_LIFECYCLE_ROLE`, `AW_MISSING_INPUT`, `AW_GATE_HOOK_BYPASS`, `AW_GATE_PROTECTED_REF`, `AW_PERMISSION_DEADLINE`, `AW_RETENTION_UNKNOWN`, `AW_RECEIPT_INVALID` and `ERROR_CODES` with its outcome. THE TABLE MUST ACCOUNT FOR ALL EIGHT: F-3c records that the authored list said "four" while naming five and omitted `AW_GATE_SCOPE` and `AW_PERMISSION_DEADLINE` entirely, so a disposition covering only the five named codes FAILS this item. Plus the recorded decision for each of the four remaining bodies with its reason, plus an explicit statement of whether the file survives. OQ-01 is resolved to DELETE THE FILE, so if the file survives this item is satisfied only by stating which measurement contradicted that resolution and why. If any body was KEPT, name the surface expected to consume it and why that is not a hypothetical need; if the file was deleted, show that no import of it remains anywhere. Do NOT satisfy this item with a test asserting the symbols are gone; the diff plus the full-suite result is the evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: a pasted search across `agent_workflows/` proving ZERO references to either deleted test file remain, WITH THE COUNT STRUCK RECONCILED AGAINST THE SIX E-01 MEASURED. F-3b records the authored count of three as low by half, so evidence that accounts for only three citations FAILS this item; state where each of the six went (vanished with its predicate, or struck by hand). Confirm the RUNTIME-STRING instance inside `check_hook_bypass`'s `_unimplemented` message was handled, since it is code rather than a docstring and a docstring-only sweep would miss it. Plus a statement that NO replacement citation was added and NO test file was restored. Where a citation was struck from surviving prose, show the still-true design point was kept and only the enforcement claim removed. Confirm explicitly that the caller-census assertion described in F-4 was not recreated in any form.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the `git diff` of the three amended spec sites plus the appended `## Workflow history` line, pasted. The diff must show R6.1 UNCHANGED, R6.3 UNCHANGED (F-7c: deleting `check_scope` removes R6.3's only demonstration, and losing an example is not a licence to narrow the rule), the P15 reasoning present in the amendment, and no change to any requirement outside the three sites.
  A16 MUST BE AMENDED IN PLACE WITH ALL THREE CLAUSES ADDRESSED AND ITS CITATION LIST INTACT. Quote the amended A16 in full and state for each of its three clauses ("each implemented shared predicate has unit tests", "each unimplemented one still raises naming its owner", "a predicate implemented but not chartered for wiring has no product caller") whether it is now no-subject or still live. An amendment addressing only clause 2 FAILS this item (F-7b). The trailing `(R6.1, R6.2, R6.3)` citation list must survive, because A16 is the ONLY criterion citing R6.2 and deleting it would create a third undocumented exception to the spec's own traceability claim (F-7d); paste `aw specs check` showing it conforming.
  Plus the result of searching every `.spec.md` for `AW_MISSING_INPUT` and for the module name, with a statement of whether any other spec needed amending and the reconciliation against `- Scope-Paths:` (an undeclared spec edit is reported by both runners at run end). Plus `aw check` showing no `check.plan-spec-link-missing` finding on this plan, which `- From-Spec: 7ckptx` now satisfies (F-7e).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted PASS of the new test file, AND a mutation demonstration for EACH assertion showing it FAILING under a mutation that genuinely breaks the property and PASSING after restore. At minimum, a mutation changing the emitted prefix without changing the published form must fail the agreement assertion. Plus confirmation, by reading the test file, that it asserts only on returned values and rendered text, reads no module source, and asserts nothing about which module defines the constant.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

OPEN QUESTIONS. BOTH are now `resolved` and neither is `Blocking: yes`, so nothing waits on a human before
execution. OQ-01 resolves to DELETE `wtiso_gate.py` and OQ-02 to the no-subject spec framing; both carried
`- Owner: reviewer` and were answered at review with their measurements recorded, so the executor follows one
branch rather than deciding mid-deletion. If E-01's own measurement contradicts OQ-01's premise (any surviving
importer), stop and report rather than quietly taking the other branch.

The executor must: perform E-01 through E-06 in order, respecting the declared `Depends on` edges; treat
E-01 as a HARD GATE, because a single real product caller makes the deletion unsafe and the correct response
is to stop and report, not to work around it; commit only the four paths in `- Scope-Paths:` via
`aw commit <plan> -- <paths>`; never push; paste ACTUAL runner output for every claim of a passing test,
INCLUDING the E-06 mutation demonstration; and verify each `V-*` in a separate pass from the `E-*` that
produced it. Do NOT mark this plan executed or move it to `.aw/records/plans/executed/` until every `V-*`
carries concrete pasted evidence and `aw ipd lint --phase pre-transition` conforms.

THE ONE WAY TO GET THIS PLAN WRONG is to delete `AW_MISSING_INPUT` along with the predicates, or to leave a
copy of it behind in both modules. That constant is the leading token of the report a worker emits when it
needs a file it does not have, and the worker's PROMPT and the driver's PARSER both derive their shape from
the single constant composed around it. Duplicate it and the two can drift, which is the exact fork spec
`7ckptx` R6.1 forbids and research `x03wgn` Section 7 names as a measured hazard; delete it and the
missing-input route breaks silently, because nothing raises until a worker actually needs it. MOVE it, prove
the rendered form is byte-identical, and pin the round trip.

A SECOND WAY TO GET IT WRONG is to be helpful about the pins. The module says two test files enforce this
arrangement and they do not exist; the instinct is to write them. Do not. One of them was an AST caller
census, which AGENTS.md and GUIDING_PRINCIPLES P16 forbid outright and which the maintainer has ruled will
not be restored. The other proved that a `--no-verify` commit is observable from git, which is a premise for
a gate this Set is deleting on principle. Writing either would re-import the defect this plan closes.

Backlog item `ariaau` is this plan's origin (`- From-Backlog: ariaau`). That item carries NO
`- Blocks-Release:` gate and none is invented here. The `chore` classification is inherited and CONFIRMED by
measurement rather than assumed: F-1 and F-2 show every deleted symbol is unreachable from any shipped path,
so no user-perceptible behavior changes and no operator waits on anything. The cost this closes falls on the
next reader who must work out whether a raising stub is a to-do and whether the tests it cites exist.
