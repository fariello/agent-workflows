# IPD: Shared containment predicates and their fail-loud discipline

- Date: 2026-09-01
- Kind: child
- Concern: The containment rules the earlier children implement risk being defined more than once, which is how two surfaces drift into disagreeing about the same rule. A dedicated module already exists to hold them as fail-loud stubs naming their owning phase, but it is imported by NO product module, so the intended single-definition discipline is declared and not yet real.
- Scope: Consolidate the containment rules this Set introduced into single definitions that every consumer calls, implement the predicate bodies this Set owns, and leave the ones it does not owns raising with their owner named. Implements spec `7ckptx` R6.1, R6.2, R6.3 and nothing else.
- Scope-Paths: agent_workflows/wtiso_gate.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_containment_predicates.py
- Item-Dependencies: executed:y5od1h
- From-Spec: 7ckptx
- Blocks-Release: next
- Status: to-review
- Set: lanectn
- Order: 6
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 604wra

## Workflow history

- 2026-09-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): sixth and final child of Set `lanectn`. Requires `y5od1h` AND `lhmrhx` executed, because it consolidates the rules those plans introduce and needs their call sites to exist before it can prove every consumer shares one definition. Deliberately small: 4 E-items, and it deliberately does NOT implement predicates other phases own.
- 2026-09-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Every containment rule this Set introduced has exactly one definition that all its consumers call, and every predicate the module declares but this Set does not own still fails loudly with its owner named, so the skeleton never lies about its own state.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

THE SUBTLE TRAP IN THIS PLAN, and the reason it is last: implementing a predicate BODY and WIRING its callers are separable deliverables that may belong to different owners (spec R6.3). One declared predicate assigns its pure body to this phase while explicitly reserving its wiring to a LATER phase. Implementing the body is in scope; wiring a caller to it is NOT, and doing so would take another phase's work and, worse, fork the very rule the split exists to keep single. When in doubt about a predicate, read its docstring for the owner before touching it.

### Task group 1: single definitions (R6.1)

- [ ] E-01 IMPLEMENTS R6.1. Audit the rules the earlier children of this Set introduced and establish that each has exactly ONE definition with every consumer importing it. Where a rule ended up defined twice, consolidate to one and repoint the callers. Do this by AST or the import graph over the package, repo-wide and NOT per file, because a per-file check passes while two copies exist in different files and a text grep is satisfied by the checking code itself.
  - Depends on: none
  - Expected outcome: for each containment rule this Set introduced, exactly one definition exists in the package and every consumer reaches it by import, established structurally rather than by text search.
  - Execution state: pending
- [ ] E-02 IMPLEMENTS R6.1, R6.3 (the body half). Implement the predicate bodies this Set owns in the dedicated module, so the rules the drivers now enforce live where every surface can call them. Give each a unit test. Read each predicate's docstring FIRST to confirm this phase owns it: implement only the bodies assigned here and leave the others untouched.
  - Depends on: E-01
  - Expected outcome: each predicate body this Set owns has a real implementation and unit tests, and no predicate assigned to another phase was modified.
  - Execution state: pending

### Task group 2: fail-loud discipline (R6.2, R6.3)

- [ ] E-03 IMPLEMENTS R6.2. Verify the fail-loud discipline still holds for every predicate this Set does NOT own: each must still raise, naming its owning phase, rather than returning a permissive default. This is the guard that prevents a half-built module from silently allowing what it cannot yet check. Confirm none was quietly given a default, a pass-through, or an empty return during this Set's work.
  - Depends on: E-02
  - Expected outcome: every predicate not owned by this Set still raises with its owning phase named, demonstrated by calling each one, and none returns a permissive value.
  - Execution state: pending
- [ ] E-04 IMPLEMENTS R6.3 (the wiring boundary), and updates the module's own docstring. Confirm that a predicate whose BODY this Set implemented but whose WIRING is reserved to a later phase has NO product caller: the body exists, the callers do not, and that is correct rather than incomplete. Then update the module docstring to state which predicates are real and which still raise, so the skeleton does not misdescribe itself to the next reader.
  - Depends on: E-03
  - Expected outcome: the body-implemented-but-not-wired predicate has zero product callers, shown structurally; and the module docstring accurately lists which predicates are real and which raise, with owners.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Measured at HEAD `59e68d5a`; anchor on symbol names.
- The dedicated predicate module exists as a fail-loud skeleton BY DESIGN: a stub raises rather than returning a permissive default so a premature caller breaks visibly. Its in-module rationale states this explicitly. Do not soften it.
- The module is currently imported by NO product module, so this plan is the first to make its discipline real.
- One declared predicate assigns its pure body to this phase and its WIRING to a later one. That split is deliberate and R6.3 protects it.
- "Exactly one of these exists" must be established by AST or the import graph, repo-wide, never by text grep, because the checking code contains the symbol.
- The suite must be run BARE and `make test-all` separately; a bare run deselects `slow` tests.

## Findings

| id | Finding | Evidence |
| --- | --- | --- |
| F-1 | The single-definition discipline is currently aspirational: the module is imported by NO product module, so nothing enforces it yet. This plan is what makes it real, which is why it runs last, after the rules exist to consolidate. | The module's import graph at authoring: zero product consumers. |
| F-2 | Fail-loud is a deliberate design choice with its reasoning recorded in the module itself: a stub raises rather than returning a permissive default so that a caller wired up before its owning phase lands breaks VISIBLY instead of silently allowing. Softening any stub to a default would convert a loud gap into a silent hole. | The module's own rationale comment; spec `7ckptx` R6.2. |
| F-3 | Body and wiring are separately owned for one predicate, and conflating them is the specific mistake available here. Implementing the body is this phase's job; wiring a caller is a later phase's, and doing it early both takes their work and risks forking the rule the split exists to keep single. | Spec `7ckptx` R6.3; the predicate's docstring naming a different phase for its wiring. |
| F-4 | A text grep cannot establish "exactly one definition", because the checking code itself contains the symbol, and a per-file check passes while duplicates live in different files. The precedent is this repository's own cross-Set verification, which used AST to prove one reaper existed while two byte-identical copies had previously passed a per-file check. | Spec `7ckptx` R6.1 and criterion A16; the AST method used in an earlier whole-Set verification. |

## Proposed changes (ordered, validatable)

1. Establish single definitions for the rules this Set introduced, structurally rather than by grep (E-01).
2. Implement the predicate bodies this Set owns, with unit tests (E-02).
3. Verify every predicate this Set does not own still fails loudly with its owner named (E-03).
4. Confirm the body-without-wiring boundary holds, and make the module docstring describe its real state (E-04).

## Deferred / out of scope (with reason)

- Every predicate assigned to a DIFFERENT phase: R6.2 requires they keep raising, and E-03 verifies exactly that. Implementing one would take another phase's work.
- WIRING the predicate whose body this Set implements but whose callers are reserved: R6.3 forbids it here.
- The rules themselves, as opposed to their consolidation: children `cqx5v7`, `nna8yz`, `lhmrhx`, `y5od1h`, and `xdr83v` own R1 through R5.
- Commit-scope enforcement at the git layer: spec Non-goal 5.

## Scope check

- Over-scope: none. Four declared files and the three requirements assigned.
- Under-scope: none for its assigned requirements. Consolidation adds no containment behavior; it makes the behavior the other five children added impossible to fork, which is the durability half of the guarantee.

## Required tests / validation

One new module: `tests/test_containment_predicates.py`, covering each implemented predicate body, the still-raising predicates with their owners named, the single-definition check by AST or import graph, and the zero-callers assertion for the body-without-wiring case.

Baselines at HEAD `59e68d5a`: bare `python3 -m pytest` -> `3996 passed, 3 skipped, 4 xfailed`; `make test-all` -> `4 failed, 4394 passed, 3 skipped, 4 xfailed`. State the expected count SEPARATELY per invocation: bare `failed == 0`; `make test-all` `failed == 4` with no NEW failure.

Because this is the LAST child, also paste the tripwire suite's result and its `xfailed` count with the delta from the Set's start explained per pin, since children of this Set may have satisfied pinned-absent guards that must now be converted rather than left pinned (CID-5).

## Spec / documentation sync

Spec `7ckptx` is normative; this plan cites requirement ids. E-04 updates the predicate module's docstring to state which predicates are real and which raise, which is the one documentation change this Set requires. No public command surface changes.

## Open questions

### OQ-01: If E-01 finds a rule defined twice, may this plan change a sibling child's code to consolidate it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, but only within this plan's declared Scope-Paths, which include both drivers precisely so consolidation is possible without a fence breach. Consolidating a duplicated rule is this plan's ASSIGNED work under R6.1, so repointing a caller in a driver is in scope. What is NOT in scope is changing a sibling's BEHAVIOR or its tests: if consolidation appears to require altering what a rule DOES rather than where it lives, that is a sign the two definitions disagreed, which is a finding to STOP and report rather than silently resolve by picking one. Recorded because "consolidate" can otherwise be read as licence to rewrite.

### OQ-02: Which exact predicates does this Set own, and may consolidation begin before all declared producers are complete?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001, PR-002
- Resolution or deferral rationale: Round 1 review found that current docstrings name older owners while this plan names no predicates, and that `Item-Dependencies` omits `lhmrhx` despite the prose requiring it. Add an explicit predicate ownership table and the complete producer edges, then re-review before execution.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01 (proves R6.1; spec A16)
  - Required evidence: paste the AST or import-graph output over the package showing, for each containment rule this Set introduced, exactly ONE definition and every consumer reaching it by import. State the method used and why a text grep would not suffice here (the checking code contains the symbol; a per-file check passes while duplicates live in different files). If consolidation was needed, paste the before and after.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02 (proves R6.1, R6.3 body half; spec A16)
  - Required evidence: paste unit-test output for each predicate body this Set implemented. Paste evidence that NO predicate assigned to another phase was modified (a diff limited to the owned ones). SABOTAGE REQUIRED: break one implemented body, paste the FAILING unit test, restore, paste it passing plus `git status` proving the product is unmodified.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03 (proves R6.2; spec A16)
  - Required evidence: CALL every predicate this Set does not own and paste the raised error for each, showing it names the owning phase. Do not infer this from reading the source: an accidental default would still read plausibly. A predicate that returns any value instead of raising FAILS this item, and reporting it as fine is the silent-hole failure the fail-loud design exists to prevent. SABOTAGE REQUIRED: replace ONE not-owned predicate's raise with a permissive return, paste the FAILING check proving your verification actually notices a softened stub, restore, paste it passing plus `git status` proving the product is unmodified. Without this, a verification that merely calls each predicate and reports success cannot be distinguished from one that would accept a default.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04 (proves R6.3 wiring boundary; spec A16)
  - Required evidence: paste structural evidence that the body-implemented-but-not-wired predicate has ZERO product callers, and state in writing that this is CORRECT rather than incomplete, naming the phase that owns its wiring. Paste the updated module docstring and confirm it matches reality predicate by predicate. Then paste the tripwire suite result with its `xfailed` count and the delta from the Set's start explained per pin, and both whole-suite invocations with expected counts stated separately per invocation.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 4 E-leaves in 2 task groups, well under both thresholds. Single-definition and fail-loud are two halves of one property: a rule that exists once but can be silently defaulted is no better protected than one defined twice. The plan is last in the Set because it consolidates what the other five introduced, and it is small because it adds no behavior of its own.

Execution contract: this plan INHERITS the shared execution contract from orchestrator `h0zljh` verbatim, including its ten numbered rules. Restated here because these are the ones most likely to be skipped, and skipping them is how this work gets faked:

1. PROSE IS NEVER EVIDENCE. Paste real command output and exit codes, never a summary of them. A `V-*` whose command was not run stays `Result: pending`.
2. SABOTAGE the central assertions. Break the product behavior deliberately, paste the FAILING run, restore, paste the passing run plus `git status` proving the product is unmodified. This session already produced a test that passed while the product was broken; only sabotage exposed it.
3. ASSERT THE PROPERTY, NOT THE WORDING. Where the requirement states an absence, check the emitted output so a reworded violation still fails.
4. STRUCTURE, NOT GREP, for "only one of these exists". Use AST or the import graph, repo-wide; a text grep is satisfied by the checking code itself.
5. PREREQUISITE IS CHECKED, NOT ASSUMED: children `y5od1h` (Order 04) AND `lhmrhx` (Order 03) MUST both be in `executed/` before this plan starts, because it consolidates the rules they introduce and needs their call sites to exist to prove every consumer shares one definition. Verify those symbols exist. If they are absent, STOP and report; do not invent the rules yourself, which is precisely the forking this plan exists to prevent.
6. THE SCOPE FENCE IS A STOP CONDITION. Touch only the declared `Scope-Paths`. If the work seems to need a sibling's surface, STOP AND REPORT; do not broaden and do not reimplement it, which would fork the rule (CID-2).
7. STATE THE HONEST LIMIT. Where a mechanism is an accident guard rather than a boundary, say so in the code comment and in this plan. Overstating a guarantee is the failure.

Commits are path-scoped and never pushed. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed or hook-interrupted commit.

Post-gate lifecycle: run `aw ipd lint --phase pre-transition`, then `aw ipd finalize`, never a hand edit. If validation did not pass, record `substantially-complete` honestly rather than marking this executed.
