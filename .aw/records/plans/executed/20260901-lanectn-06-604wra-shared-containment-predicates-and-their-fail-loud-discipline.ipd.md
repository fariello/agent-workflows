# IPD: Shared containment predicates and their fail-loud discipline

- Date: 2026-09-01
- Kind: child
- Concern: The containment rules the earlier children implement risk being defined more than once, which is how two surfaces drift into disagreeing about the same rule. A dedicated module already exists to hold them as fail-loud stubs naming their owning phase, but it is imported by NO product module, so the intended single-definition discipline is declared and not yet real.
- Scope: Consolidate the containment rules this Set introduced into single definitions that every consumer calls, implement the predicate bodies this Set owns, and leave the ones it does not owns raising with their owner named. Implements spec `7ckptx` R6.1, R6.2, R6.3 and nothing else.
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/wtiso_gate.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_containment_predicates.py
- Item-Dependencies: executed:lhmrhx, executed:y5od1h
- From-Spec: 7ckptx
- Blocks-Release: next
- Status: executed
- Readiness: go-pending-approval
- Set: lanectn
- Order: 6
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 604wra

## Workflow history
- 2026-09-06 executed (aw oc run): aw oc run self-finalize: 604wra verified (set lanectn, attempt 1). [Scope reconciliation - out-of-scope tests/test_missing_input_repair.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_wtiso_adversarial.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_wtiso_taxonomy_freeze.py: changed by the plan's approved execution (auto-reconciled by aw oc run); in-scope-unmodified agent_workflows/agy_runipd.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified agent_workflows/oc_runipd.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-06 executed (opencode/its_direct/pt3-claude-opus-5-1m-us, run-20260905T211011Z-3780617 pos 11): all 4 E-items performed, all 4 V-items pass with pasted evidence and product-level sabotage for V-02/V-03/V-04. Prerequisites CHECKED not assumed: `y5od1h` and `lhmrhx` both in `executed/` and all 19 of their symbols verified present in this lane before editing. FOUR THINGS A REVIEWER SHOULD KNOW. (1) E-01 found NO forked function or class: the AST survey resolved all 32 rule symbols to exactly 1 definition each. The consolidation it DID make is a string-level one - the stable code `AW_MISSING_INPUT` was retyped inside `MISSING_INPUT_TOKEN_FORM`, so renaming the code would have left the worker's PROMPT publishing the old spelling and the escape hatch would have failed silently. (2) E-04's instruction was NOT followable as written and the divergence is recorded (D3): it asked each stale label to name the superseding `lanectn` child, but all three named owner phases (`qcqhj7`, `rchpms`, `2c122z`) are RETIRED and four of the five left-raising predicates have NO successor at all, so inventing one would have been fabricated provenance; each label now states its phase, retirement, what DID land, and plainly says when nothing supersedes it. (3) Three predicates were implemented as DELEGATIONS rather than new logic, per `y5od1h`'s handoff note and R6.1; only `check_permission_deadline` is new, and its docstring states the honest limit that it is a pure predicate over a recorded stream and NOT a live bound (`PERMISSION_TIMEOUT` still ships at 0). (4) The bare suite has 35 PRE-EXISTING failures at this lane's HEAD, not zero as the plan expected; I characterized all 35 before editing and the failing node-id set is IDENTICAL after (0 new, 0 fixed). 17 are caused by the driver exporting `AW_EXECUTION_ROLE=worker` into the turn, and 18 by lane-absent `.aw/records/runs/` plus a real `attention.duplicate-id` in committed backlog data (`2k42zu` in both `graduated/` and `done/`) - both worth a maintainer's attention and neither this plan's to fix.
- 2026-09-05 approved (aw set): status set to approved
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REVIEWED; round 2 is a DISCLOSED SELF-REVIEW (I authored this plan, so it is weaker evidence than round 1, which was independent and performed by codex/gpt-5). Round 1's PR-* findings were all resolved and moved to FIXED in the typed review record; round 2 then found 1 further findings, SR-002 (FIXED), of which four across the Set were defects I INTRODUCED while fixing round 1. Round 2 is appended to the plan-specific typed review record.
- 2026-09-01 reviewed (aw set): /aw plan-review round 1 complete; all findings ACCEPTED and resolved. Every one was verified against the artifact before fixing. Two were serious: (1) my orchestrator claimed a proven-complete dependency graph while two children's metadata omitted edges their own prose required, which is the same CLASS of defect that got the predecessor tch3bo rejected - the proof had checked acyclicity only and never metadata-vs-prose agreement; (2) the spec's secret vocabulary was derived from THIS repository's ignore file with no floor, which would admit secrets in a managed target repo, fixed by a maintainer-approved spec amendment adding a built-in floor, union-only composition, and fail-closed behavior. Also fixed: the right-sizing complaint that I complied on E-item count while hiding each second driver's whole implementation in one 'mirror' item (now host-neutral code plus thin adapters), stale hardcoded suite baselines (now measure-at-execution-time and compare failures by identity), a genuine data-model error where retention read the input manifest for OUTPUT collection state (now an attempt-keyed collection receipt owned by the plan that owns collection), and an unfollowable instruction to read docstring owner labels that name superseded phases (now a measured predicate ownership table).
- 2026-09-01 to-review (aw set): plan-review 06/PR-002: the prose required BOTH y5od1h and lhmrhx executed, but the metadata named only y5od1h. Consolidating the permission and deadline rules needs their call sites to exist.

- 2026-09-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): sixth and final child of Set `lanectn`. Requires `y5od1h` AND `lhmrhx` executed, because it consolidates the rules those plans introduce and needs their call sites to exist before it can prove every consumer shares one definition. Deliberately small: 4 E-items, and it deliberately does NOT implement predicates other phases own.
- 2026-09-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Every containment rule this Set introduced has exactly one definition that all its consumers call, and every predicate the module declares but this Set does not own still fails loudly with its owner named, so the skeleton never lies about its own state.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

THE SUBTLE TRAP IN THIS PLAN, and the reason it is last: implementing a predicate BODY and WIRING its callers are separable deliverables that may belong to different owners (spec R6.3). One declared predicate assigns its pure body to this phase while explicitly reserving its wiring to a LATER phase. Implementing the body is in scope; wiring a caller to it is NOT, and doing so would take another phase's work and, worse, fork the very rule the split exists to keep single. When in doubt about a predicate, read its docstring for the owner before touching it.

### Predicate ownership table (added after `/aw plan-review` finding PR-001)

THE ORIGINAL INSTRUCTION WAS UNFOLLOWABLE, and the review was right to refuse it. It told the executor to implement "the predicates this Set owns" after reading their docstrings, but those docstrings name the OLD phase ids (`qcqhj7`, `rchpms`, `2c122z`) and NONE of them names `lanectn` or any child of it. An executor could not determine which bodies to implement, which to leave raising, or which stale label had been superseded. Every predicate is therefore enumerated below by symbol, measured at authoring.

| Predicate | Current label in the module | This Set's disposition | Wire a caller? |
| --- | --- | --- | --- |
| `format_missing_input` | `qcqhj7` | IMPLEMENT here (superseded by `y5od1h`, which owns R3.1) | YES, from the missing-input path |
| `parse_missing_input` | `qcqhj7` | IMPLEMENT here (superseded by `y5od1h`, which owns R3.1) | YES, from the missing-input path |
| `check_permission_deadline` | `qcqhj7` | IMPLEMENT here (superseded by `lhmrhx`, which owns R4.4) | YES, from the turn-bounds path |
| `check_scope` | `qcqhj7` | IMPLEMENT THE BODY ONLY | NO. Its docstring reserves wiring to a later phase; wiring it here would take that phase's work and fork the rule |
| `check_lifecycle_role` | `rchpms` | LEAVE RAISING | NO |
| `check_hook_bypass` | `rchpms` | LEAVE RAISING | NO |
| `classify_retention` | `rchpms` | LEAVE RAISING. NOTE the near-miss: `xdr83v` implements retention CLASSIFICATION for this Set, but it is not chartered to fill this predicate, and doing so would be scope creep into another phase | NO |
| `check_receipt` | `rchpms` | LEAVE RAISING | NO |
| `check_protected_refs` | `2c122z` | LEAVE RAISING | NO |

FOUR implemented, FIVE left raising, and exactly ONE of the four (`check_scope`) is body-without-wiring. E-04 must UPDATE each stale label so the module stops naming a superseded owner, and must record which `lanectn` child superseded it. If the module's contents differ from this table at execution time, record the difference and proceed on the MEASURED contents rather than guessing: the table is measured, not assumed, and a difference means someone else moved first. Surface it; do not halt.

### Task group 1: single definitions (R6.1)

- [x] E-01 IMPLEMENTS R6.1. Audit the rules the earlier children of this Set introduced and establish that each has exactly ONE definition with every consumer importing it. Where a rule ended up defined twice, consolidate to one and repoint the callers. Do this by AST or the import graph over the package, repo-wide and NOT per file, because a per-file check passes while two copies exist in different files and a text grep is satisfied by the checking code itself.
  - Depends on: none
  - Expected outcome: for each containment rule this Set introduced, exactly one definition exists in the package and every consumer reaches it by import, established structurally rather than by text search.
  - Execution state: performed
  - Notes: AST survey over all of `agent_workflows/` covered the 32 symbols the Set's three shipped children introduced; every one resolved to exactly 1 top-level definition in `lane_containment.py`, and both drivers reach them by `from agent_workflows import lane_containment`. NO function or class was forked. One STRING-level fork WAS found and consolidated: `"AW_MISSING_INPUT"` was spelled as a literal in both `wtiso_gate.AW_MISSING_INPUT` (the declared stable error code) and inside `lane_containment.MISSING_INPUT_TOKEN_FORM` (the prompt text). The form now composes around the imported code, so the code, the prompt instruction, and the parser prefix all trace to one definition. Recorded as DECISION D1 with the concrete failure it prevents (renaming the code would have left the prompt publishing the old spelling, so a worker obeying instructions would emit a token no parser recognized). Import direction verified cycle-free in both orders.
- [x] E-02 IMPLEMENTS R6.1, R6.3 (the body half). Implement the predicate bodies this Set owns in the dedicated module, so the rules the drivers now enforce live where every surface can call them. Give each a unit test. Use the PREDICATE OWNERSHIP TABLE above, which enumerates every predicate by symbol; do NOT rely on the docstring labels, which name superseded phases and are what made the original instruction unfollowable.
  - Depends on: E-01
  - Expected outcome: each predicate body this Set owns has a real implementation and unit tests, and no predicate assigned to another phase was modified.
  - Execution state: performed
  - Notes: Four bodies implemented in `wtiso_gate.py`, three of them as DELEGATIONS to the existing single definition rather than new logic (DECISION D2): `format_missing_input` and `parse_missing_input` forward to `lane_containment.format_missing_input_token`/`parse_missing_input_token` (as `y5od1h`'s walkthrough explicitly instructed), and `check_scope` calls `ipd_lifecycle._scope_match` so the Scope-Paths grammar is not forked away from the rule finalize already enforces. Only `check_permission_deadline` is new logic, because no existing definition computes it (`TurnBoundWatch` enforces a LIVE wall-clock bound and cannot judge a recorded stream); it is session-agnostic so a NESTED child ask cannot be masked by root-session traffic. The wire-YES predicates needed no driver edit: their consumers reach the rules through `lane_containment`, which both drivers already import. 31 unit tests in `tests/test_containment_predicates.py`. No predicate assigned to another phase was modified (asserted structurally).
### Task group 2: fail-loud discipline (R6.2, R6.3)

- [x] E-03 IMPLEMENTS R6.2. Verify the fail-loud discipline still holds for every predicate this Set does NOT own: each must still raise, naming its owning phase, rather than returning a permissive default. This is the guard that prevents a half-built module from silently allowing what it cannot yet check. Confirm none was quietly given a default, a pass-through, or an empty return during this Set's work.
  - Depends on: E-02
  - Expected outcome: every predicate not owned by this Set still raises with its owning phase named, demonstrated by calling each one, and none returns a permissive value.
  - Execution state: performed
  - Notes: All five (`check_lifecycle_role`, `check_hook_bypass`, `classify_retention`, `check_receipt`, `check_protected_refs`) still raise `NotImplementedError`, demonstrated by CALLING each one rather than reading its source. Two of the five were live temptations to fill and were deliberately NOT filled (DECISION D4): the shipped worker-role rule and `xdr83v`'s retention classification are both a DIFFERENT SHAPE from their stub's signature, so wrapping either would mean inventing a contract no caller requested and, for retention, silently asserting two vocabularies are equivalent. Additionally asserted by AST that no body contains ANY value-returning path, which catches a conditional early return the representative arguments would miss.
- [x] E-04 IMPLEMENTS R6.3 (the wiring boundary), and updates the module's own docstring. Confirm that a predicate whose BODY this Set implemented but whose WIRING is reserved to a later phase has NO product caller: the body exists, the callers do not, and that is correct rather than incomplete. Then update the module docstring AND each stale per-predicate owner label to state which predicates are real, which still raise, and which `lanectn` child superseded each old label, so the skeleton stops naming a superseded owner.
  - Depends on: E-03
  - Expected outcome: the body-implemented-but-not-wired predicate has zero product callers, shown structurally; and the module docstring accurately lists which predicates are real and which raise, with owners.
  - Execution state: performed
  - Notes: `check_scope` has a real body and ZERO product callers, established by walking every consumer module's AST for both `name(...)` and `module.name(...)` call forms. Module docstring rewritten to list all nine predicates by symbol with their true state. THE PLAN'S OWN INSTRUCTION COULD NOT BE FOLLOWED AS WRITTEN, and the divergence is recorded as DECISION D3: it asked each stale label to name "which `lanectn` child superseded it", but I measured that ALL THREE named phases are RETIRED and that for FOUR of the five left-raising predicates NO `lanectn` child supersedes them. Writing a superseding child for those would have been a fabricated provenance claim, so each label instead names its phase, its retirement date and disposition, what DID land where that changes what is actually missing, and says plainly when there is no successor plan. The plan's escape clause ("record the difference and proceed on the MEASURED contents") authorizes exactly this.
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

BASELINES MUST BE MEASURED AT EXECUTION TIME, NOT COPIED FROM THIS PLAN. Corrected after `/aw plan-review` (PR-003 on every plan in this Set): the exact counts originally written here were already STALE before execution, because a co-worker's commit `8ced15ce` added two tests, moving the bare suite from `3996 passed` to `3998 passed`. A hardcoded count cannot distinguish an honest change from a regression, and treating it as an expectation would either raise a false alarm or, worse, mask a real failure behind an off-by-two rationalization.

SO DO THIS INSTEAD. Immediately before you start, run BOTH invocations and record their counts as YOUR baseline, pasting them. Then after your change, run both again and COMPARE FAILURES BY TEST IDENTITY, not by total: list the failing test node ids before and after and account for every difference by name. A count that changed with no new failing id is fine and must be explained (usually tests added); a new failing id is a STOP regardless of what the totals do.

TWO INVOCATIONS WITH DIFFERENT SEMANTICS, and the distinction is load-bearing: bare `python3 -m pytest` is expected to have ZERO failures, while `make test-all` carries a known set of PRE-EXISTING CLI-surface declaration failures that are not this plan's to fix. State the expected outcome separately per invocation; a single "failed == 0" claim across both is the contradiction that got the predecessor `tch3bo` flagged (PR-006). Identify the pre-existing set by NAME in your own measurement rather than trusting any number recorded here.

Because this is the LAST child, also paste the tripwire suite's result and its `xfailed` count with the delta from the Set's start explained per pin, since children of this Set may have satisfied pinned-absent guards that must now be converted rather than left pinned (CID-5).

## Spec / documentation sync

Spec `7ckptx` is normative; this plan cites requirement ids. E-04 updates the predicate module's docstring to state which predicates are real and which raise, which is the one documentation change this Set requires. No public command surface changes.

## Open questions

### OQ-01: If E-01 finds a rule defined twice, may this plan change a sibling child's code to consolidate it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, but only within this plan's declared Scope-Paths, which include both drivers precisely so consolidation is possible without a fence breach. Consolidating a duplicated rule is this plan's ASSIGNED work under R6.1, so repointing a caller in a driver is in scope. What is NOT in scope is changing a sibling's BEHAVIOR or its tests: if consolidation appears to require altering what a rule DOES rather than where it lives, that is a sign the two definitions disagreed, which is a FINDING to record and surface rather than silently resolve by picking one. Report it in the walkthrough and the finalize reconciliation; do not halt the run, and do not pick a winner without saying you did. Recorded because "consolidate" can otherwise be read as licence to rewrite.

### OQ-02: Which exact predicates does this Set own, and may consolidation begin before all declared producers are complete?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: PR-001, PR-002
- Resolution or deferral rationale: RESOLVED 2026-09-01, both halves. On ownership: a measured PREDICATE OWNERSHIP TABLE now enumerates all nine predicates by symbol with their current label, disposition (four implement, five leave raising), and whether to wire a caller. This was necessary because the docstring labels name superseded phases (`qcqhj7`, `rchpms`, `2c122z`) and NONE names `lanectn`, which made the original read-the-docstrings instruction unfollowable. On consolidation: it MAY repoint a caller inside this plan's declared `Scope-Paths`, since that is its assigned R6.1 work, but if consolidation appears to require changing what a rule DOES rather than where it lives, the two definitions disagreed and that is a FINDING to surface rather than resolve by picking a winner.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01 (proves R6.1; spec A16)
  - Required evidence: paste the AST or import-graph output over the package showing, for each containment rule this Set introduced, exactly ONE definition and every consumer reaching it by import. State the method used and why a text grep would not suffice here (the checking code contains the symbol; a per-file check passes while duplicates live in different files). If consolidation was needed, paste the before and after.
  - Observed evidence: PASS. AST over all of `agent_workflows/`: all 32 rule symbols this Set introduced resolve to exactly 1 top-level definition in `lane_containment.py`; 0 forks; both drivers reach them by import. One STRING fork found and consolidated (the `AW_MISSING_INPUT` code was retyped inside `MISSING_INPUT_TOKEN_FORM`); before/after and the cycle-free import check are pasted below.

    METHOD: `ast.parse` over every `agent_workflows/**/*.py`, collecting TOP-LEVEL `FunctionDef`,
    `AsyncFunctionDef`, `ClassDef`, `Assign` and `AnnAssign` names, then counting sites per rule
    symbol. Top level only, deliberately: a nested helper cannot be imported by another surface so it
    cannot BE the second definition of a shared rule, and counting nested defs would false-positive on
    ordinary closures.

    WHY NOT A TEXT GREP, demonstrated rather than asserted (`SabotageTests::test_a_text_grep_cannot_establish_single_definition`):
    the symbol `classify_missing_input_report` appears in the CHECKING CODE itself, so a text count
    over the package exceeds the definition count. And a per-file check passes while two byte-identical
    copies live in different files, which is how this repository's own earlier cross-Set verification
    was fooled before it switched to AST.

    ```
    == DEFINITION COUNT per rule (AST, package-wide, top level) ==
      OK   project_worker_paths: 1 -> ['agent_workflows/lane_containment.py:228']
      OK   isolation_notice: 1 -> ['agent_workflows/lane_containment.py:352']
      OK   prior_attempt_summary: 1 -> ['agent_workflows/lane_containment.py:206']
      OK   absolute_paths_outside_lane: 1 -> ['agent_workflows/lane_containment.py:308']
      OK   scrub_out_of_lane_paths: 1 -> ['agent_workflows/lane_containment.py:327']
      OK   collect_lane_submissions: 1 -> ['agent_workflows/lane_containment.py:541']
      OK   merge_decisions_block: 1 -> ['agent_workflows/lane_containment.py:505']
      OK   lane_submission_root: 1 -> ['agent_workflows/lane_containment.py:140']
      OK   collection_receipt_path: 1 -> ['agent_workflows/lane_containment.py:425']
      OK   read_collection_receipt: 1 -> ['agent_workflows/lane_containment.py:435']
      OK   prepare_lane_submission_dir: 1 -> ['agent_workflows/lane_containment.py:161']
      OK   attempt_key: 1 -> ['agent_workflows/lane_containment.py:123']
      OK   item_slug: 1 -> ['agent_workflows/lane_containment.py:135']
      OK   decisions_block_key: 1 -> ['agent_workflows/lane_containment.py:500']
      OK   build_permission_policy_env: 1 -> ['agent_workflows/lane_containment.py:778']
      OK   opencode_posture_record: 1 -> ['agent_workflows/lane_containment.py:916']
      OK   antigravity_posture_record: 1 -> ['agent_workflows/lane_containment.py:937']
      OK   evaluate_policy_observation: 1 -> ['agent_workflows/lane_containment.py:993']
      OK   TurnBoundWatch: 1 -> ['agent_workflows/lane_containment.py:1216']
      OK   driver_bound_for_host: 1 -> ['agent_workflows/lane_containment.py:1123']
      OK   bound_expiry_reaper: 1 -> ['agent_workflows/lane_containment.py:1165']
      OK   bound_expiry_record: 1 -> ['agent_workflows/lane_containment.py:1144']
      OK   record_host_posture: 1 -> ['agent_workflows/lane_containment.py:1353']
      OK   parse_host_ceiling_seconds: 1 -> ['agent_workflows/lane_containment.py:1408']
      OK   format_missing_input_token: 1 -> ['agent_workflows/lane_containment.py:1571']
      OK   parse_missing_input_token: 1 -> ['agent_workflows/lane_containment.py:1597']
      OK   classify_missing_input_report: 1 -> ['agent_workflows/lane_containment.py:1640']
      OK   classify_denied_permission_path: 1 -> ['agent_workflows/lane_containment.py:1819']
      OK   MissingInputDecision: 1 -> ['agent_workflows/lane_containment.py:1523']
      OK   MissingInputObserver: 1 -> ['agent_workflows/lane_containment.py:1846']
      OK   record_missing_input_refusal: 1 -> ['agent_workflows/lane_containment.py:1935']
      OK   lane_preserved_for_missing_input: 1 -> ['agent_workflows/lane_containment.py:1973']

    == FORKS ==
      none

    == product modules importing the home ==
      agent_workflows/agy_runipd.py: ['from agent_workflows import lane_containment']
      agent_workflows/oc_runipd.py: ['from agent_workflows import lane_containment']
      agent_workflows/wtiso_gate.py: ['from agent_workflows import lane_containment']
    ```

    CONSOLIDATION, BEFORE AND AFTER. No function was forked, but the stable error code was:

    ```
    BEFORE  agent_workflows/wtiso_gate.py:45        AW_MISSING_INPUT = "AW_MISSING_INPUT"
            agent_workflows/lane_containment.py:67  MISSING_INPUT_TOKEN_FORM = "AW_MISSING_INPUT:<repo-relative-path>:<why it is required>"
                                                    ^^^^^^^^^^^^^^^^ the same code, retyped

    AFTER   agent_workflows/lane_containment.py     from agent_workflows.wtiso_gate import AW_MISSING_INPUT as _AW_MISSING_INPUT
                                                    MISSING_INPUT_TOKEN_FORM = (
                                                        _AW_MISSING_INPUT + ":<repo-relative-path>:<why it is required>"
                                                    )
    ```

    ```
    $ python3 -c "from agent_workflows import lane_containment as lc, wtiso_gate as g; ..."
    TOKEN_FORM: AW_MISSING_INPUT:<repo-relative-path>:<why it is required>
    prefix == code: True
    roundtrip: ('a/b.txt', 'why')
    gate roundtrip: ('a/b.txt', 'why')
    ```

    Import direction is cycle-free, checked in both orders (`wtiso_gate` has no runtime module-level
    imports of its own, and its delegations to `lane_containment` are function-local for that reason):

    ```
    $ python3 -c "import agent_workflows.wtiso_gate; import agent_workflows.lane_containment; ..."
    both import OK, order A
    both import OK, order B
    drivers import OK
    ```
  - Result: pass
- [x] V-02 validates E-02 (proves R6.1, R6.3 body half; spec A16)
  - Required evidence: paste unit-test output for each predicate body this Set implemented. Paste evidence that NO predicate assigned to another phase was modified (a diff limited to the owned ones). SABOTAGE REQUIRED: break one implemented body, paste the FAILING unit test, restore, paste it passing plus `git status` proving the product is unmodified.
  - Observed evidence: PASS. 31 unit tests green (`31 passed in 27.05s`), covering all four implemented bodies. No predicate owned by another phase modified; both drivers byte-unmodified. SABOTAGE: replacing `format_missing_input`'s delegation with a local render was caught by 4 checks (`4 failed, 27 passed`), including the STRUCTURAL delegation check that a today-agreeing fork would otherwise pass; restored to `31 passed` with a `diff` proving identity.

    UNIT TESTS for the four implemented bodies (31 tests; `-o addopts=""` used ONLY to get per-test
    counts, per the repo contract's allowance):

    ```
    $ python3 -m pytest tests/test_containment_predicates.py -o addopts=""
    collected 31 items
    tests/test_containment_predicates.py ...............................     [100%]
    ============================= 31 passed in 27.05s ==============================
    ```

    Direct behavioral check of each implemented body:

    ```
    --- IMPLEMENTED ---
    format: 'AW_MISSING_INPUT:config/local.ini:absent from lane'
    parse : ('a/b.txt', 'why: with colons')
    parse non-token: None
    deadline: ['AW_PERMISSION_DEADLINE']
    scope   : ['AW_GATE_SCOPE'] []
    ```

    `check_permission_deadline` edge matrix (all as designed; note that a root-session answer does NOT
    clear a CHILD's ask, which is the nested-deadlock property, and that `0` disables the check):

    ```
    OK   answered on same session -> []
    OK   answered on OTHER session does not clear -> ['AW_PERMISSION_DEADLINE']
    OK   two asks one answer -> one violation -> ['AW_PERMISSION_DEADLINE']
    OK   within deadline -> []
    OK   deadline 0 disables -> []
    OK   no timestamp -> no violation -> []
    OK   empty -> []
    OK   non-dict tolerated -> ['AW_PERMISSION_DEADLINE']
    ```

    NO PREDICATE OWNED BY ANOTHER PHASE WAS MODIFIED. The five unowned bodies all still contain the
    `_unimplemented(...)` raise, asserted per predicate by
    `ImplementedPredicateTests::test_no_predicate_owned_by_another_phase_was_modified`, and the diff
    touches only the four owned bodies plus docstrings. Files changed in the product:
    `agent_workflows/wtiso_gate.py` and `agent_workflows/lane_containment.py` only; BOTH drivers are
    byte-unmodified (`git status --porcelain agent_workflows/oc_runipd.py` empty).

    SABOTAGE: replaced `format_missing_input`'s delegation with a locally rendered token
    (`return "SABOTAGE:{0}:{1}".format(path, why)`), i.e. a second implementation.

    ```
    $ python3 -m pytest tests/test_containment_predicates.py -o addopts=""
    tests/test_containment_predicates.py ....F...F.....F......F.........     [100%]
    FAILED tests/test_containment_predicates.py::SabotageTests::test_the_delegation_check_fails_on_a_second_implementation
    FAILED tests/test_containment_predicates.py::ImplementedPredicateTests::test_each_implemented_predicate_returns_its_documented_shape
    FAILED tests/test_containment_predicates.py::SingleDefinitionTests::test_both_token_surfaces_produce_identical_results
    FAILED tests/test_containment_predicates.py::SingleDefinitionTests::test_the_token_emitters_are_delegations_not_second_implementations
    ======================== 4 failed, 27 passed in 26.81s =========================
    ```

    Four independent checks caught it, INCLUDING the structural delegation check - which matters
    because a forked implementation that AGREES with the original today would pass a purely behavioral
    check. RESTORED:

    ```
    $ diff /tmp/.../wtiso_gate.py.pristine agent_workflows/wtiso_gate.py && echo IDENTICAL
    IDENTICAL
    $ python3 -m pytest tests/test_containment_predicates.py -o addopts=""
    ============================= 31 passed in 26.98s ==============================
    $ git status --porcelain agent_workflows/wtiso_gate.py
     M agent_workflows/wtiso_gate.py
    ```

    The `M` is THIS PLAN'S intended change, not sabotage residue; the `diff` against the pre-sabotage
    snapshot above proves the sabotage itself is fully gone.
  - Result: pass
- [x] V-03 validates E-03 (proves R6.2; spec A16)
  - Required evidence: CALL every predicate this Set does not own and paste the raised error for each, showing it names the owning phase. Do not infer this from reading the source: an accidental default would still read plausibly. A predicate that returns any value instead of raising FAILS this item, and reporting it as fine is the silent-hole failure the fail-loud design exists to prevent. SABOTAGE REQUIRED: replace ONE not-owned predicate's raise with a permissive return, paste the FAILING check proving your verification actually notices a softened stub, restore, paste it passing plus `git status` proving the product is unmodified. Without this, a verification that merely calls each predicate and reports success cannot be distinguished from one that would accept a default.
  - Observed evidence: PASS. All five unowned predicates CALLED (not read); each raised `NotImplementedError` naming its owner AND its retirement. SABOTAGE: softening `check_lifecycle_role` to `return []` was caught by 5 checks (`5 failed, 33 passed`) with the diagnostic naming the returned value; restored to `38 passed`. Full messages and the measured owner-retirement correction are below.

    ALL FIVE CALLED (not read). Each raised; none returned:

    ```
    --- STILL RAISING ---
    check_lifecycle_role raises OK
    check_hook_bypass raises OK
    classify_retention raises OK
    check_receipt raises OK
    check_protected_refs raises OK
    ```

    The raised message for each NAMES ITS OWNER and its disposition. Full text of one, as
    representative (the others follow the same shape and are asserted per predicate by
    `FailLoudTests::test_each_unowned_predicate_names_a_real_retired_owner`):

    ```
    NotImplementedError: wtiso_gate.check_lifecycle_role has no rule body; its owner is `rchpms`
    (Phase 2, RETIRED 2026-09-02, partly landed). The rule itself DOES ship, as
    `ipd_lifecycle.worker_role_active` + the AW-LIFECYCLE-ROLE-001 refusal, and both drivers already
    enforce it; this pure-predicate SHAPE has no caller, so no body is written here. It raises rather
    than returning a permissive default (spec 7ckptx R6.2), so a caller wired up before a body exists
    fails loudly instead of silently allowing. Do not soften this to a default: implement the body
    under a plan that owns it.
    ```

    IMPORTANT MEASURED CORRECTION, recorded as DECISION D3: every "owning phase" named in this module
    is RETIRED (`qcqhj7` superseded by this Set, `rchpms` partly-landed then retired, `2c122z` retired
    unlanded). So naming only the phase would send a reader to a plan that will never run. Each message
    now carries the phase AND its retirement AND, where relevant, what DID land instead.

    SABOTAGE, the critical one for this item: replaced `check_lifecycle_role`'s raise with
    `return []`, the exact permissive default a caller would read as "no violations".

    ```
    $ python3 -c "from agent_workflows import wtiso_gate as g; print(g.check_lifecycle_role('finalize','worker'))"
    softened stub returns: []
    ```

    ```
    $ python3 -m pytest tests/test_containment_predicates.py tests/test_wtiso_taxonomy_freeze.py -o addopts=""
    E  AssertionError: check_lifecycle_role RETURNED [] instead of raising. A permissive default
       converts a loud gap into a silent hole in a gate (spec R6.2).
    FAILED tests/test_wtiso_taxonomy_freeze.py::GateLibraryTests::test_gate_predicates_refuse_rather_than_silently_allow
    FAILED tests/test_containment_predicates.py::FailLoudTests::test_each_unowned_predicate_names_a_real_retired_owner
    FAILED tests/test_containment_predicates.py::FailLoudTests::test_each_unowned_predicate_raises_when_called
    FAILED tests/test_containment_predicates.py::FailLoudTests::test_no_unowned_predicate_returns_a_permissive_value
    FAILED tests/test_containment_predicates.py::SabotageTests::test_the_fail_loud_check_fails_on_a_softened_stub
    ======================== 5 failed, 33 passed in 26.90s =========================
    ```

    FIVE independent checks caught the softened stub, with the diagnostic naming the returned value.
    This is what distinguishes the verification from one that would accept a default. RESTORED:

    ```
    $ diff /tmp/.../wtiso_gate.py.pristine agent_workflows/wtiso_gate.py && echo RESTORED IDENTICAL
    RESTORED IDENTICAL
    $ python3 -m pytest tests/test_containment_predicates.py tests/test_wtiso_taxonomy_freeze.py -o addopts=""
    ============================= 38 passed in 26.59s ==============================
    ```
  - Result: pass
- [x] V-04 validates E-04 (proves R6.3 wiring boundary; spec A16)
  - Required evidence: paste structural evidence that the body-implemented-but-not-wired predicate has ZERO product callers, and state in writing that this is CORRECT rather than incomplete, naming the phase that owns its wiring. Paste the updated module docstring and confirm it matches reality predicate by predicate. Then paste the tripwire suite result with its `xfailed` count and the delta from the Set's start explained per pin, and both whole-suite invocations with expected counts stated separately per invocation.
  - Observed evidence: PASS. `check_scope` has a real body and ZERO product callers, proven structurally over both call forms; sabotage planting a real caller was located at `oc_runipd.py:894` and then restored. Docstring matches reality predicate by predicate. Tripwire `12 passed, 4 xfailed` -> `14 passed, 2 xfailed`, both conversions explained per pin. Whole suite: BARE `35 failed` before and after, `make test-all` `41 failed` before and after, failing node-id sets IDENTICAL (0 new, 0 fixed); all pre-existing failures are ENVIRONMENTAL and named below.

    ZERO PRODUCT CALLERS for `check_scope`, established structurally by walking each consumer module's
    AST for BOTH `check_scope(...)` and `<module>.check_scope(...)` call forms (a check that saw only
    one form would miss half the wirings it exists to detect):

    ```
    $ python3 -m pytest tests/test_containment_predicates.py -o addopts="" -k WiringBoundary
    ================== 5 passed, 26 deselected ==================
    (test_the_body_without_wiring_has_zero_product_callers -> call_sites('check_scope') == [])
    ```

    THIS IS CORRECT, NOT INCOMPLETE, and I state it in writing. `check_scope`'s wiring was assigned to
    wtiso Phase 2 (`rchpms`), which would have connected the pre-commit hook, `aw lane status`, the
    driver, finalize, and integration to it. `rchpms` was RETIRED on 2026-09-02 with that half recorded
    as NOT LANDED, and it has no successor plan. So there is no phase in flight that owns the wiring,
    the body is genuinely waiting for a consumer, and wiring it here would both take another phase's
    work and fork the scope rule that `ipd_lifecycle` already enforces. The scope rule ACTUALLY in
    force today runs through `ipd_lifecycle.finalize_precheck`, which this body delegates to, so the two
    cannot disagree.

    SABOTAGE for this item: planted a real product caller in `oc_runipd.py`.

    ```
    E  + [] : check_scope must have NO product caller: its wiring is unowned (spec R6.3).
             Found: ['oc_runipd.py:894']
    FAILED tests/test_containment_predicates.py::WiringBoundaryTests::test_the_body_without_wiring_has_zero_product_callers
    ================== 1 failed, 4 passed, 26 deselected in 0.95s ==================
    ```

    Located the planted wiring by file and line. RESTORED (`git status --porcelain
    agent_workflows/oc_runipd.py` empty, i.e. byte-identical to HEAD).

    MODULE DOCSTRING now matches reality predicate by predicate: it lists the four REAL bodies with the
    single definition each delegates to, the five STILL RAISING with the note that none has an owner in
    flight, the R6.3 body-without-wiring case and why its zero callers are correct, and a paragraph
    recording that all three original owner labels were retired. Asserted mechanically by
    `WiringBoundaryTests::test_the_module_docstring_describes_its_real_state`, which requires every one
    of the nine predicates to be named in it.

    TRIPWIRE SUITE, with the per-pin delta explained (CID-5). Measured at the Set's start vs now, for
    the two wtiso guard modules:

    ```
    BEFORE  $ python3 -m pytest tests/test_wtiso_adversarial.py tests/test_wtiso_taxonomy_freeze.py -o addopts=""
            ======================== 12 passed, 4 xfailed in 0.38s =========================

    AFTER   $ python3 -m pytest tests/test_wtiso_adversarial.py tests/test_wtiso_taxonomy_freeze.py -o addopts=""
            ======================== 14 passed, 2 xfailed in 0.40s =========================
    ```

    `xfailed` 4 -> 2, and BOTH conversions are accounted for by name (DECISION D5). Neither was deleted
    or weakened:

    1. `test_missing_input_driver_denial_pinned_absent` -> `test_missing_input_driver_denial_now_exists`.
       Its subject arrived: `y5od1h` shipped the report-and-refuse cycle and this plan re-pointed the
       gate stubs at it. The converted test asserts BOTH token surfaces agree and that a well-formed
       request for a real file is still REFUSED with nothing copied - strictly more than the pin.
       Deliberately does NOT assert a "resume" or a copy, because spec R3.3a withdrew that branch.
    2. `test_nested_permission_bounded_kill_pinned_absent` ->
       `test_nested_permission_detection_now_exists_but_is_not_armed`. As `strict=True` it reported
       `failed [XPASS(strict)]` the moment the body landed, which is its designed investigate-me signal;
       I confirmed the pass was legitimate before converting. Converted into a TWO-part assertion so the
       remaining gap stays visible: the detector catches a nested ask AND `PERMISSION_TIMEOUT` is still
       `0.0` (disabled per R4.4b, so `MAX_TURN_TIMEOUT` remains the only bound covering a permission
       deadlock). Asserting only the first half would have overstated what shipped.

    The 2 remaining pins (`forgetful_agent_driver_report`, `hook_bypass_driver_rejection`) are UNTOUCHED
    and still `xfailed`. The module's health signal (`failed == 0` AND `xfailed > 0`) holds.

    Two further pins outside those files were converted for the same mechanical reason:
    `test_missing_input_repair.py::TwinParityTests::test_the_wtiso_gate_stubs_are_left_raising_for_their_owner`
    (renamed to `..._now_delegate_to_this_single_definition`; `y5od1h`'s own walkthrough asked this
    executor to retire it in the same change) and
    `test_wtiso_taxonomy_freeze.py::test_gate_predicates_refuse_rather_than_silently_allow` (now asserts
    the property per CURRENT state rather than a fixed list, so it keeps catching a softened stub).

    BOTH WHOLE-SUITE INVOCATIONS, with expectations stated SEPARATELY per invocation. Baselines were
    MEASURED at this lane's HEAD `7e3deb92` immediately before editing, not copied from this plan:

    ```
    BARE (measured baseline)   35 failed, 5251 passed, 3 skipped, 4 xfailed in 103.97s
    BARE (after my change)     35 failed, 5284 passed, 3 skipped, 2 xfailed in 108.38s
      NEW failures (absent from baseline):  <none>
      FIXED (in baseline, now passing):     <none>

    make test-all (baseline)   41 failed, 5654 passed, 3 skipped, 4 xfailed in 162.84s
    make test-all (after)      41 failed, 5687 passed, 3 skipped, 2 xfailed in 164.27s
      NEW failures: <none>        FIXED: <none>
    ```

    COMPARED BY TEST IDENTITY, not by total: the failing node-id sets before and after are IDENTICAL
    for both invocations (`comm` over the sorted `FAILED` id lists returns empty in both directions).
    Passed counts rose by 33 = my 31 new tests + 2 converted xfails now counted as passes; `xfailed`
    fell by 2 for the same conversions.

    EXPECTATION PER INVOCATION, stated separately because a single "failed == 0" claim across both would
    be the contradiction that got predecessor `tch3bo` flagged. The plan expected BARE to have ZERO
    failures. IT DOES NOT, and I did not cause it: all 35 are PRE-EXISTING AND ENVIRONMENTAL, identified
    by name and split into two independent causes (see the decisions register NOTE-1):

    * 17 are caused by THE DRIVER'S OWN ENVIRONMENT. The runner exports `AW_EXECUTION_ROLE=worker`, and
      `ipd_lifecycle.worker_role_active` reads exactly that, so every test exercising `aw ipd
      begin`/`finalize` gets the legitimate `AW-LIFECYCLE-ROLE-001` refusal. Proven by re-running the
      same 35 under `env -u AW_EXECUTION_ROLE`: 17 pass, 18 remain.
    * 18 are repo-state dependent: `test_run_viewer.py` needs a non-empty `.aw/records/runs/`, which a
      lane worktree does not have (gitignored driver state), and `test_next_ordering.py` fails because
      `aw next` exits 1 on a real `attention.duplicate-id` in committed data (backlog id `2k42zu` is in
      BOTH `graduated/` and `done/`). That last one is a genuine repo defect but not this plan's to fix.

    The 6 additional `make test-all` failures are the known pre-existing CLI-surface declaration set
    (`test_command_surface_declarations`, `test_cli_conformance_matrix`, plus 3 installer/runner-stop
    tests), identified by name in my own measurement rather than trusted from a recorded number.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 4 E-leaves in 2 task groups, well under both thresholds. Single-definition and fail-loud are two halves of one property: a rule that exists once but can be silently defaulted is no better protected than one defined twice. The plan is last in the Set because it consolidates what the other five introduced, and it is small because it adds no behavior of its own.

Execution contract: this plan INHERITS the shared execution contract from orchestrator `h0zljh` verbatim, including its ten numbered rules. Restated here because these are the ones most likely to be skipped, and skipping them is how this work gets faked:

1. PROSE IS NEVER EVIDENCE. Paste real command output and exit codes, never a summary of them. A `V-*` whose command was not run stays `Result: pending`.
2. SABOTAGE the central assertions. Break the product behavior deliberately, paste the FAILING run, restore, paste the passing run plus `git status` proving the product is unmodified. This session already produced a test that passed while the product was broken; only sabotage exposed it.
3. ASSERT THE PROPERTY, NOT THE WORDING. Where the requirement states an absence, check the emitted output so a reworded violation still fails.
4. STRUCTURE, NOT GREP, for "only one of these exists". Use AST or the import graph, repo-wide; a text grep is satisfied by the checking code itself.
5. PREREQUISITE IS CHECKED, NOT ASSUMED: children `y5od1h` (Order 04) AND `lhmrhx` (Order 03) MUST both be in `executed/` before this plan starts, because it consolidates the rules they introduce and needs their call sites to exist to prove every consumer shares one definition. Verify those symbols exist. If they are absent, STOP and report; do not invent the rules yourself, which is precisely the forking this plan exists to prevent.
6. THE SCOPE FENCE IS A DECLARATION, NOT A HALT CONDITION. Touch only the declared `Scope-Paths` as a default, and never expand casually; if the work genuinely requires more, MAKE THE EDIT AND JUSTIFY IT in the finalize reconciliation (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path), which is where an unjustified widening is caught. Do NOT halt the run over a scope question. If the work genuinely requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` will refuse to complete until every out-of-scope path you touched carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT at the gate rather than prevented by halting a run. Do NOT halt the run over a scope question. What you must NOT do is REIMPLEMENT a sibling's rule, which would fork it (CID-2): that is a correctness problem, not a scope one, so if a needed rule is missing, say so in the reconciliation reason.
7. STATE THE HONEST LIMIT. Where a mechanism is an accident guard rather than a boundary, say so in the code comment and in this plan. Overstating a guarantee is the failure.

Commits are path-scoped and never pushed. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed or hook-interrupted commit.

Post-gate lifecycle: run `aw ipd lint --phase pre-transition`, then `aw ipd finalize`, never a hand edit. If validation did not pass, record `substantially-complete` honestly rather than marking this executed.
