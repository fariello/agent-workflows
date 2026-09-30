# IPD: Stop spec 25kzda claiming commit-gateway enforcement nothing provides, and pin the claim to the descriptor

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `b7tlsh` asks the one question plan `4h7tt0` could not decide: whether ANY spec text should claim commit-gateway enforcement, given none exists. Measured at this lane's HEAD, `probe_runner_safety_capabilities()` returns `supports_commit_gateway` False, DECLARED AND NEVER PROBED (`host_sandbox_profile._DECLARED_UNENFORCED`), so the honest answer for every host is No. Section 7's worked example is now correctly framed as an ASSUMPTION, so the item's original defect is fixed; what remains is that the assumption is the ONLY site carrying its own measurement, while three sibling sites still read as live present-tense guarantees. The reader `b7tlsh` describes, auditing "what does the oc host guarantee", is misled by those three and not by the one already corrected.
- Scope: IN: amend spec `25kzda` at the TWO sites that still assert commit-gateway enforcement in the present tense (2.1's "the commit gateway rejects `--no-verify`" clause, whose dead "5.8 row 3" cross-reference is repaired in the same rewrite, and 5.2's guarantee-2 `Enforcement or proof` cell), add ONE behavioral regression test pinning the three-way agreement between the descriptor field, the finding-code binding, and the action-requirement map so the drift this item records cannot silently recur, and VERIFY the durable carrier (`ymlyqf`, filed at review) for the two sibling guarantee rows that carry the same overclaim and are measured to have no owner. OUT, each for a stated reason: REMOVING `supports_commit_gateway` (the sibling question, answered No here from repository evidence, see OQ-01); AMENDING 5.2 guarantee rows 1 and 3 (same defect class, deliberately carried by backlog `ymlyqf` rather than swept in, see F-11); the 5.2 host-requirement bullet, the 5.2 action table, and the 5.6 packet example's `"commit_gateway"` string, all of which state what a HOST must prove and were deliberately preserved by plan `01reg8`; Section 7's worked-example sentence, already corrected by `4h7tt0` and correct as it stands; BUILDING commit-gateway enforcement; and reintroducing or rebinding any finding code.
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, tests/test_host_capability_extension.py, .aw/records/backlog/open
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: b7tlsh
- Blocks-Release: next
- Set: b7tlsh
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 00pirb

## Workflow history
- 2026-09-30 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): status set to reviewed

- 2026-09-30 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-801 (HIGH, fixed), PR-802 (HIGH, fixed), PR-803, PR-804, PR-805 (MEDIUM, fixed), PR-806, PR-807 (LOW, fixed). Re-measured every claim in the Findings table at HEAD `4e7dd52c`; all verified. Two serious findings: E-04's exclusion of 5.2 guarantee rows 1 and 3 rested on an owner handoff that does not exist (no `denypush` plan mentions the guarantee table; `01reg8` E-09's DO-NOT-TOUCH list omits it), while both rows carry the identical overclaim, so E-06 now files the carrier; and E-03's instruction to keep "5.8 row 3" preserved a DEAD cross-reference (5.8 is the parity table; the hooks row is 5.2's), now retargeted and anchored on quoted text. Also resolved V-02's leg-2 falsification mechanism by demonstration rather than leaving it to the executor, recorded coverage overlap E-02 did not know about, and added the missing scope fence and tooled-finalize transition to the gate. Full findings and four recorded decisions: `.aw/records/reviews/20260929-b7tlsh-01-00pirb-stop-spec-25kzda-claiming-commit-gateway-enforcement-nothing.review.md`.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored review-ready while graduating backlog `b7tlsh`. Re-measured the descriptor, the finding-code binding, and the action-requirement map in this lane before scoping; answered the item's open question (keep the field, fix the prose) from repository evidence and recorded the derivation in OQ-01.
- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make spec `25kzda` state the same thing about commit-gateway enforcement everywhere: that it is a
REQUIREMENT on a host which no host meets today, and that the capability naming it is declared, never
probed, and therefore fails closed. After this plan a reader auditing the oc host's guarantees reaches
that answer from any of the four sites that mention the gateway, not only from the one Section 7
sentence that currently carries the measurement. One test then pins the agreement between the three
shipped artifacts, so the next drift fails a run instead of waiting for a reader to notice it.

Two things this plan does NOT claim, stated here because the whole subject is overclaim. It does not
make the 5.2 guarantee TABLE honest: rows 1 and 3 carry the same defect, review measured that nothing
owns them, and backlog `ymlyqf` (filed at review) carries them rather than this plan pretending the
table is finished, with E-06 verifying that carrier still holds. And it
changes no behavior at all; nothing in the package enforces a commit gateway before this plan or after
it, which is exactly the fact the records are being brought into line with.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure, and file the residual carrier, before editing any record

- [ ] E-01 Re-measure the three artifacts this plan's edits describe, on the executing host, and retain the verbatim output: (a) `python3 -c` printing `host_sandbox_profile.probe_runner_safety_capabilities()` and `detect_host_capabilities('opencode').supports_commit_gateway` with its `probe_notes` entry; (b) the `RUN-COMMIT-GATEWAY` row's `binding` and `predicates` from `run_evidence.RUN_FINDING_CODES`; (c) `ACTION_CAPABILITY_REQUIREMENTS`, `ACTION_CLASSES`, and the list of actions whose `required` contains `CAP_COMMIT_GATEWAY`; plus (d) `python3 -m agent_workflows host capabilities opencode`. Do NOT trust this plan's authoring numbers: the spec's own preamble states every dated paragraph is a point-in-time snapshot that must be re-measured, and this plan is about a claim that rotted.
  - Depends on: none
  - Expected outcome: Four captured outputs establishing the premise every later item rests on: the capability is False and declared-not-probed, the finding code is `UNBOUND-BY-DEPENDENCY` with zero predicates, and NO action requires the capability. If any of the three has changed since authoring, STOP and report rather than editing: a capability that has since become probed would make E-03 and E-04 assert the opposite of the truth.
  - Execution state: pending

- [ ] E-06 VERIFY, do not re-file, the DURABLE CARRIER for guarantee rows 1 and 3 of the same 5.2 table, which review measured carry the identical overclaim this plan fixes in row 2 and which no other artifact owns. Backlog `ymlyqf` was FILED AT REVIEW (2026-09-30) rather than left to this item, deliberately: a carrier that only exists if this plan executes is the obligation-loss `sv9ce4` was filed at authoring time to avoid, and this plan's own Deferred row needs a resolvable id6 or `check.ipd-uncarried-obligation` fails. Confirm it is still `open`, still `Work-Kind: bug` with `- Blocks-Release: next`, and still carries BOTH measurements it was filed with: for row 1, that `supports_deny_push`/`CAP_DENY_PUSH` were removed by `01reg8` and `RUN-NO-PUSH` retired by `4h7tt0`; for row 3, that `hook_preserving_commit` sits in `UNREPRESENTED_SPEC_CAPABILITIES` with no field able to carry the proof. RE-MEASURE both claims on the executing host rather than trusting the item's text, and if either has moved, correct the item with `aw backlog set` and record what changed; if the item was closed or removed, re-file it with the same content and record why. Do NOT amend either spec row here.
  - Depends on: E-01
  - Expected outcome: `ymlyqf` is confirmed present, `open`, gated, and honestly worded, so the residual overclaim stays visible in `aw attention` regardless of what the rest of this plan does. VERIFYING rather than filing is the stronger arrangement: the obligation already exists on disk and cannot be lost by this plan failing.
  - Execution state: pending

### Task group 2: pin the agreement behaviorally, before changing prose

- [ ] E-02 Add a test class `CommitGatewayClaimConsistencyTests` to `tests/test_host_capability_extension.py` asserting the THREE-WAY agreement between shipped artifacts, by CALLING them and reading their outputs: (1) `detect_host_capabilities('opencode').supports_commit_gateway` is False and its `probe_notes` entry contains `DECLARED, NOT PROBED`; (2) the `RUN-COMMIT-GATEWAY` row of `run_evidence.RUN_FINDING_CODES` has `binding == run_evidence.UNBOUND_BY_DEPENDENCY` and empty `predicates`, i.e. no predicate decides it; (3) no member of `ACTION_CAPABILITY_REQUIREMENTS` lists `CAP_COMMIT_GATEWAY` in `required`, so the capability gates no production action. Write the class docstring to state the INVARIANT the three express jointly: nothing in this package enforces a commit gateway, so any artifact reporting otherwise is the fail-open drift backlog `b7tlsh` recorded. Assert on returned VALUES only; do not read source text, count callers, or grep for symbols (AGENTS.md's no-code-pinning rule, GUIDING_PRINCIPLES P16).
  KNOW WHAT ALREADY EXISTS, measured at review, so this class adds the missing leg rather than a third copy of an existing one: the SAME file already asserts leg (1) in three places (`test_the_unenforced_capability_is_declared_and_not_probed`, `test_a_forced_verdict_does_not_leak_out_of_the_context`, `test_the_production_path_is_unchanged_with_no_mock_supplied` all assert False plus `DECLARED, NOT PROBED`) and already asserts a form of leg (3) (`test_requirement_map_structure_and_coverage` asserts `ACTION_CAPABILITY_REQUIREMENTS[ACTION_READ_ONLY].required == ()` and `len(ACTION_CLASSES) == 1`). Leg (2) is asserted NOWHERE: `grep -rn RUN_FINDING_CODES tests/` returns no match, which is precisely the gap that let 4.2's binding and the spec's prose drift apart. So the class's VALUE is (2) plus the JOINT statement, and it must be written as such: keep all three legs so the invariant is readable in one place, and state in the docstring that legs (1) and (3) are deliberately restated here to make the three-way agreement checkable together, naming the existing tests so a later reader does not delete one as redundant. Do NOT weaken leg (3) to the existing test's form: assert that NO member of the map lists `CAP_COMMIT_GATEWAY` in `required`, which holds however many action classes exist, rather than pinning the map to one key.
  - Depends on: E-01
  - Expected outcome: The class passes at current HEAD (it encodes the measured state) and would FAIL if any one artifact drifted from the other two, which is the regression this plan adds. Run it alone first with `python3 -m pytest tests/test_host_capability_extension.py -o addopts="" -k CommitGatewayClaimConsistency` and keep that output.
  - Execution state: pending

### Task group 3: amend the two spec sites that still read as live guarantees

- [ ] E-03 Amend spec `25kzda` Section 2.1's flag paragraph, whose final clause currently reads "the commit gateway rejects `--no-verify` in its git sense (Sections 4.2 `RUN-COMMIT-GATEWAY` and 5.8 row 3)". As written this is a PRESENT-TENSE claim that a gateway exists and performs a rejection, inside a paragraph otherwise careful to say what is bound TODAY versus what is an unbound name (its own preceding sentence does exactly that for `IPD-EXEC-V-EVIDENCE`). Rewrite the clause so it states the PROHIBITION, which is real and unchanged, and separates it from the ENFORCEMENT, which does not exist: `--no-verify` in its git sense is forbidden and no flag on `run` offers it, AND the commit-gateway interception that would prove no bypass occurred is unbuilt, so `RUN-COMMIT-GATEWAY` is `UNBOUND-BY-DEPENDENCY` and `supports_commit_gateway` is declared-never-probed and fails closed. Do NOT weaken the prohibition itself: `git_commit_helper` never passes `--no-verify` (its module docstring states "never ``--no-verify``; never ``push``") and that is a real property of the driver-side helper.
  ALSO REPAIR THE CLAUSE'S SECOND CROSS-REFERENCE, which is DEAD, measured at review: "5.8 row 3" does not name the hooks guarantee. Section 5.8 is the interactive/unattended PARITY table and its row 3 is "Incomplete draft"; the hooks row is row 3 of the 5.2 GUARANTEE-CLASSIFICATION table. The reference was accurate when written (commit `844d195c`, 2026-09-06, whose own message cites "5.8 row 3" and whose tree has the hooks row inside the section then numbered 5.8) and rotted when later sections were inserted above it. So RETARGET it to "5.2 guarantee row 3" and cite it by its quoted text ("Hooks are not bypassed and a hook refusal remains a failure") rather than by a row ordinal, since an ordinal is the very thing that just rotted. Keep the `RUN-COMMIT-GATEWAY` reference, which resolves. Repairing this here rather than filing it is deliberate: the clause is being rewritten by this same item, so leaving a known-dead pointer inside text this plan authors would ship a defect knowingly.
  - Depends on: E-01, E-02
  - Expected outcome: 2.1 no longer asserts that a gateway rejects anything, while the prohibition it exists to state survives verbatim in force. The paragraph's own convention (name today's enforcer, name the unbound specifier) is now applied to this clause as it already was to its neighbor. Both cross-references now RESOLVE, and the surviving one is anchored on quoted text rather than a row ordinal.
  - Execution state: pending

- [ ] E-04 Amend ONE table cell: spec `25kzda` 5.2's guarantee-classification row 2, `Enforcement or proof`, which currently reads "Commit interception and gateway capability; the gateway uses explicit argv/path lists." It names that mechanism as if it were in place, in a table whose OWN preamble distinguishes Host-dependent guarantees that "require controlled execution" from Host-independent ones re-derived afterwards. Reframe the cell so it reads as a specification rather than a description: keep the mechanism as what WOULD prove the guarantee, name `supports_commit_gateway` as the field that would carry the proof, and record that it is declared-never-probed on every host, so the guarantee is NOT in force and fails closed. Leave the `Bucket` column (`Host-dependent`) unchanged: the classification is correct and is precisely why the guarantee cannot be recovered by trusting the agent afterwards. Do NOT touch rows 1 or 3; they carry the SAME overclaim shape as row 2 and are deliberately left to backlog `ymlyqf`, for the reason recorded in Deferred (see `F-11`). Scope discipline is the reason, NOT an owner claim: review measured that NO artifact owns either row, so do not repeat this plan's authoring assertion that they "belong to the `denypush` Set and to E-03".
  - Depends on: E-01, E-02
  - Expected outcome: The highest-authority statement of guarantee 2 carries its own enforcement status, matching what `host_sandbox_profile`'s `_DECLARED_UNENFORCED` note has said since `mjx7ne`. A reader auditing guarantees from the classification table now gets the same answer as one reading the module docstring.
  - Execution state: pending

- [ ] E-05 Record provenance. Append a dated `## Workflow history` record to spec `25kzda` naming this plan, this backlog item, and what was amended, using `python3 -m agent_workflows specs note <spec path> --message "..."` rather than hand-editing the section. Do NOT change the spec's `- Status:` (it stays `approved`) or its `- Blocks-Release:`.
  - Depends on: E-03, E-04
  - Expected outcome: The spec's history gains one AMENDED line naming `00pirb` and `b7tlsh`, written by the owning tool, and its status and release gate are byte-unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A plan may amend a spec and MUST declare it (AGENTS.md). The spec is therefore in `Scope-Paths`, which is what makes both runners announce the declared spec edit before the run starts and reconcile it at finalize.
- Spec status and history are OWNED by `aw specs`; history is appended with `aw specs note`, never hand-edited (AGENTS.md; `.aw/records/specs/README.md`). E-05 follows this and the plan changes no `- Status:`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This area is a case study: backlog `oq05nc` cites the anti-inference rule at `host_sandbox_profile.py:109-115` and plan `4h7tt0` cites the SAME rule at `:88-95`; both are stale. Every citation here names a symbol or quotes a string, and E-03/E-04 identify their edit sites by QUOTED TEXT for the same reason.
- Tests must assert observable behavior and outcomes, never code structure: no `inspect`/`ast`/regex reads of production source, no caller counts, no pinning of docstring or comment text (AGENTS.md; GUIDING_PRINCIPLES P16). E-02 is written to call the three artifacts and assert on their returned values. Note that `tests/test_host_capability_wiring.py` DOES parse `runner_shared` with `ast`; it is pre-existing and this plan neither extends nor imitates it.
- A capability may only be set True by code that executed a probe for it, and inferring support from a helper's PRESENCE is forbidden in writing (`host_sandbox_profile`'s module docstring and its `_DECLARED_UNENFORCED` rationale). This plan adds no probe and no capability, so it cannot violate the rule; it is named because it is the reason the honest answer here is prose rather than code.
- The `RUN_FINDING_CODES` table's size is itself contractual: `run_evidence.validate_finding_table` hard-fails on a count other than 12. This plan adds, removes, and rebinds NO row, so the invariant is untouched.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | The capability is False, declared, and never probed, exactly as the item records | `probe_runner_safety_capabilities()` returns `{'supports_commit_gateway': False, 'supports_fresh_verifier_session': True}`; the note begins `DECLARED, NOT PROBED: no commit-interception enforcement exists in this package to attempt`; `_RUNNER_SAFETY_PROBES[CAP_COMMIT_GATEWAY]` is `None` | The item's premise HOLDS. The honest answer to "should any spec text claim this enforcement" is No, which is what E-03 and E-04 implement. |
| F-2 | The item's OWN worked-example defect is already fixed, so this plan must not re-fix it | Section 7 now opens `ASSUME FOR THIS EXAMPLE that the `oc` capability descriptor positively proves ...` and states `THAT ASSUMPTION IS COUNTERFACTUAL TODAY`; backlog `hhr83h` is `done` with "fixed: 25kzda worked example reads ASSUME FOR THIS EXAMPLE; open question tracked by b7tlsh" | Section 7 is OUT of scope. Editing it again would churn text two records already settled. What this plan owes is the REMAINING question, which is the other sites. |
| F-3 | Three sibling sites still read as live present-tense guarantees | 2.1: "the commit gateway rejects `--no-verify` in its git sense"; 5.2 row 2 `Enforcement or proof`: "Commit interception and gateway capability; the gateway uses explicit argv/path lists."; and 5.2 guarantee 2 itself: "The agent cannot commit except through a path-scoped engine gateway" | These are the sites that mislead the reader `b7tlsh` describes. E-03 and E-04 amend the two that ASSERT a mechanism; the guarantee STATEMENT stays, because a guarantee row is a specification and its `Enforcement or proof` cell is where truth about enforcement belongs. |
| F-4 | The sibling `deny_push` question was answered by REMOVAL, but that precedent does not transfer | Backlog `aagh7v` is `done`; plan `01reg8` deleted the field, `CAP_DENY_PUSH`, and three action verdicts. Its stated ground was that the flag "only PRINTS a protection that does not exist" and had NO consumer | The item asks whether to follow that precedent. Measured answer: NO, and for a reason `01reg8` itself recorded, not a preference. See F-5. |
| F-5 | `supports_commit_gateway` is NOT dead code, unlike its removed sibling: it is the only capability by which the preflight refusal path can be exercised | `tests/test_host_capability_extension.synthetic_gated_action` requires `(CAP_COMMIT_GATEWAY, CAP_FRESH_VERIFIER_SESSION)` and its docstring states it "keeps the preflight REFUSES/PROCEEDS tests non-vacuous and two-sided (01reg8 E-06)"; `tests/test_host_capability_wiring.bound_contract_action` reuses it to drive `execute_item_core`'s live refusal; `01reg8`'s own OQ-01 records that after it, the capability "acquires a SECOND reason to exist ... it is what E-06's synthetic test action requires" | REMOVING the field would make the shipped preflight's refusal half untestable, converting a two-sided gate into a one-sided one. That is a strictly worse outcome than an honestly-labelled unprobed capability, so this plan KEEPS the field and fixes the PROSE. Recorded as OQ-01. |
| F-6 | The capability currently gates NO action, so nothing is refused on it | `ACTION_CLASSES == ('read_only',)`; `ACTION_CAPABILITY_REQUIREMENTS` has the single key `read_only` whose `required` is `()`; no member lists `CAP_COMMIT_GATEWAY` | This is why the defect is a RECORD defect and not a live hole: nothing fails open at runtime because nothing consults it. It is also what E-02's assertion (3) pins. |
| F-7 | The live preflight IS wired but its production action map is deliberately EMPTY | `runner_shared.execute_item_core` calls `_hsp.preflight_host_capabilities` on the dispatch path; `RUNNER_ACTION_TO_CONTRACT_ACTION` is `{}` and its comment says it "is deliberately empty of production rows: it serves as the extension seam that successor plans (b7tlsh/oq05nc) will populate when a mutating action acquires a real capability requirement" | THAT COMMENT NAMES THIS ITEM, and this plan deliberately does NOT populate the seam. Populating it would make `execute` require a capability that is permanently False, refusing EVERY execute item on every host. The comment describes a successor with a REAL requirement; none exists, so the seam stays empty and OQ-02 records the reasoning. |
| F-8 | The finding code is unbound and waiting on the same missing machinery | The `RUN-COMMIT-GATEWAY` row has `binding == 'UNBOUND-BY-DEPENDENCY'`, `predicates == ()`, and `waiting_on` naming "a captured commit-gateway RECEIPT ... `host_sandbox_profile` declares `supports_commit_gateway` False-by-default and NEVER PROBED for exactly that reason" | The code table is ALREADY honest, and its honesty is the third leg E-02 pins. It needs no edit; it is the model the spec prose should match. |
| F-9 | Plan `01reg8` deliberately preserved the host-requirement bullet, the action table, and the packet example | `01reg8` E-09: "DO NOT TOUCH the 5.2 host-requirement bullet ..., the 5.2 action TABLE's four rows, or the packet example's `"deny_push"` string: all three state what a HOST must prove" | Those three sites remain out of scope here for the same reason, which is why this plan's Scope names them explicitly rather than leaving the exclusion implicit. |
| F-10 | The spec asserts a test-enforced byte-equality guard on the 4.2 table that NO LONGER EXISTS | The spec states "`tests/test_run_evidence_completion.py` asserts byte equality, so editing a cell here is a code change"; that file is absent from `tests/`, was deleted in commit `19313eed` ("trim test suite from 9,136 to under 2,000 tests", 1722 deletions), and NO test references `RUN_FINDING_CODES` at all | A REAL defect and NOT this plan's: it concerns 4.2's table guard, not the commit-gateway claim, and fixing it means deciding whether to restore a guard. Filed as backlog `089bq4` AT AUTHORING TIME rather than promised for execution, so the obligation exists whether or not this plan ever runs. |
| F-11 | ADDED AT REVIEW. Guarantee rows 1 and 3 of the SAME 5.2 table carry the IDENTICAL overclaim as row 2, and NO artifact owns either | Row 1's `Enforcement or proof` reads "Tool/network/credential denial plus captured process policy. An actual push attempt aborts the run." while `hasattr(hsp, 'supports_deny_push')` and `CAP_DENY_PUSH` both fail to resolve (removed by `01reg8`) and `RUN-NO-PUSH` was retired by `4h7tt0`. Row 3's reads "Hook-preserving gateway and deny policy for `git commit --no-verify` or equivalent" while `hook_preserving_commit` is a member of `UNREPRESENTED_SPEC_CAPABILITIES` whose note reads "this contract has no field for it, so it cannot be gated here". Measured ownership: `01reg8` E-09's DO-NOT-TOUCH list names the 5.2 host-requirement bullet, the action table, and the packet example, and does NOT name the guarantee table; and grepping all four `denypush` Set plans for the guarantee table, its rows, or the `Enforcement or proof` column returns ZERO hits | This plan's authoring text asserted these rows "belong to the `denypush` Set and to E-03", and BOTH halves are false: `denypush` never mentions the table, and E-03 amends Section 2.1 rather than a table row. Left uncorrected, the exclusion would have read as an owner handoff and the two rows would have been silently orphaned in exactly the way this plan exists to stop. E-04's exclusion now cites SCOPE, and backlog `ymlyqf` carries them. |

## Proposed changes (ordered, validatable)

1. Re-measure the descriptor, the finding-code binding, and the requirement map on the executing host, and stop if any has moved (E-01). Nothing is edited before the premise is confirmed, because this plan exists because a record outlived its measurement.
2. VERIFY the carrier for the two sibling guarantee rows this plan does not amend (E-06), BEFORE any edit, so the residual obligation is confirmed intact rather than assumed. The carrier (`ymlyqf`) already exists on disk, filed at review, so it cannot be lost by this plan failing.
3. Add the three-way consistency test (E-02), so the invariant is pinned by something executable before any prose is rewritten to describe it. Test-only; no production code changes.
4. Amend 2.1 so it states the prohibition without asserting an enforcement, and repair its dead "5.8 row 3" cross-reference in the same rewrite (E-03).
5. Amend 5.2's guarantee-2 `Enforcement or proof` cell so it names a required mechanism and its absence (E-04).
6. Record the amendment through `aw specs note` (E-05).

## Deferred / out of scope (with reason)

- REMOVING `supports_commit_gateway`, `CAP_COMMIT_GATEWAY`, or the preflight machinery. Answered No from repository evidence (F-5): the field is the only capability that can drive the preflight's refusal path in tests, so removal would silently make a shipped two-sided gate one-sided. See OQ-01.
  - Carrier-Declined: NOT WANTED, which is a decision rather than a deferral. Filing a carrier would misrepresent a settled No as pending work. The evidence is recorded in F-5 and OQ-01 so a future reader can reopen it with the analysis rather than redo it.
- POPULATING `runner_shared.RUNNER_ACTION_TO_CONTRACT_ACTION`, even though its comment names `b7tlsh` as a successor that would. Declined on measured grounds (F-7): every candidate row would require a capability that is permanently False, so it would refuse every execute item on every host. The comment's own precondition, "when a mutating action acquires a real capability requirement", is not met.
  - Carrier-Declined: The precondition is stated in the code comment itself, so the condition for acting is discoverable without asserting that work is owed.
- BUILDING commit-gateway enforcement (commit interception the agent cannot evade). That is the OS-level boundary project, the same magnitude as the push-denial work, and it is explicitly not a prose fix.
  - Carrier: sv9ce4
- The spec's stale claim that `tests/test_run_evidence_completion.py` enforces byte equality on the 4.2 table (F-10). Out of scope: it concerns a different section and needs a decision this plan has no authority to make, namely whether to RESTORE a byte-equality guard (respecting the deliberate suite trim and the no-code-pinning rule) or to CORRECT the spec sentence to stop promising a guard that no longer exists.
  - Carrier: 089bq4
- Section 7's worked-example sentence, the 5.2 host-requirement bullet, the 5.2 action table, and the 5.6 packet example's `"commit_gateway"` string. Correct as they stand (F-2) or deliberately preserved (F-9).
  - Carrier-Declined: Nothing is owed; editing them would churn text that two prior records settled.
- AMENDING 5.2 guarantee rows 1 (push denial) and 3 (hooks), which review measured carry the identical overclaim as row 2 and which no artifact owns (F-11). Deferred rather than swept in for TWO reasons, neither of them effort. FIRST, each needs a judgement this plan has not made: row 1's "An actual push attempt aborts the run" is a claim about RUNTIME BEHAVIOR, not merely a mechanism, so correcting it means deciding what the row should say now that push denial was measured infeasible with the available mechanism (research `uq4y6q`), which is live territory for the `denypush` Set's own maintainer decision (`wcbpqf`). SECOND, row 3 cannot be corrected by naming a field that would carry the proof, the shape E-04 uses for row 2, because `hook_preserving_commit` has NO field at all; it is unrepresented by the contract, so the honest amendment has a different form and should be authored deliberately.
  - Carrier: ymlyqf
- CHANGING the spec's `- Status:` or `- Blocks-Release: next`. Content amendment only; status is owned by `aw specs`.
  - Carrier-Declined: Out of scope by construction.

## Scope check

- Over-scope: none. Every declared path is written by an E-item: the spec by E-03, E-04, and E-05; the test file by E-02; `.aw/records/backlog/open` by E-06 only in the CORRECTIVE case (the carrier `ymlyqf` already exists, so a conforming run writes nothing there; the path is declared because E-06 must be able to correct the item if a re-measurement contradicts it, and it is a directory because `aw backlog set` owns the filename). No production module is edited, which is deliberate and is what makes this reviewable as a record fix.
- Under-scope: none. E-01 writes nothing (measurement only). The one path a reader might expect and will NOT find is `agent_workflows/host_sandbox_profile.py`: its `_DECLARED_UNENFORCED` note and module docstring are ALREADY correct (F-1) and are the text the spec is being brought into line with, so editing them would be the wrong direction. `agent_workflows/run_evidence.py` is likewise absent because F-8 measured its row already honest.

## Required tests / validation

- Run the suite BARE as `python3 -m pytest` and paste the actual summary line. Expect the prior count plus E-02's new test. A bare run is already quiet, parallel, and fast-scoped; do not add `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md).
- Run `python3 -m pytest tests/test_host_capability_extension.py -o addopts=""` and paste the per-test summary, since E-02 edits that file and `addopts` must be cleared to get counts.
- `aw ipd lint` on this plan reports conforming.
- `aw check` reports no new violations, specifically none in the `release-gates` family: this plan and the spec both carry `- Blocks-Release: next`, neither gate moves, and E-06's new item carries its own gate correctly. Measured at review for comparison: `aw check release-gates` reports `errors 0   warnings 0` over 324 backlog, 20 specs, 151 plans, 1 release.
- `aw sanitize --agent` exits zero on the changed files: E-01's captured `host capabilities` output can carry host-identifying paths and is quoted into V-01.

## Spec / documentation sync

- Spec `25kzda` is AMENDED by E-03, E-04, and E-05, and is declared in `Scope-Paths`. WHY the amendment is warranted: the spec is the contract every other plan is reviewed against, and it currently answers "does the oc host enforce a commit gateway" differently depending on which of its sections a reader opens. Section 7 says the claim is counterfactual and carries the measurement; Section 2.1 says a gateway rejects `--no-verify`; Section 5.2's guarantee table names interception as the enforcement. One of those is true. Leaving the other two means every future reader of this area re-derives what `mjx7ne` already measured and `4h7tt0` already corrected once, which is the drift backlog `b7tlsh` was filed to end.
- CONCURRENT SPEC EDITORS, checked at review because this spec is contended: four pending plans in the `denypush` Set plus `cpi6p3`, `kcc71f`, `zdgc6t`, `yu47nf` and `entv1d` all declare this same spec in their `Scope-Paths`. Measured non-overlap with THIS plan's two edit sites: grepping all four `denypush` plans for the guarantee-classification table, its rows, or the `Enforcement or proof` column returns ZERO hits, and their declared 5.2 work is the push-denial REQUIREMENT BULLET and prose, not the guarantee table; `x2dwu5` E-03 explicitly says "the 5.2 action table, and the 5.6 packet example's `deny_push` string are all UNCHANGED". No pending plan declares Section 2.1's flag paragraph. So the two sites this plan edits are uncontended. Note the runner isolates each item in its own worktree and returns changes through merge-and-revalidate, so overlap would not be a hazard even if present; this note exists to record that the SEMANTIC edit sites do not collide, which isolation cannot decide.
- No change to `host_sandbox_profile`'s module docstring: it is already the correct statement (F-1), and this plan moves the spec toward it rather than the reverse.
- No `docs/` page changes: no user-facing page documents a commit-gateway guarantee (the term appears in this spec, in `host_sandbox_profile`, and in `run_evidence`, all internal contracts).
- CHANGELOG: no entry. Nothing user-visible changes; the amendment is to internal contracts and the new test pins existing behavior.

## Open questions

### OQ-01: Should `supports_commit_gateway` be REMOVED, following the `supports_deny_push` precedent, rather than kept and honestly labelled?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: KEEP IT. This is the sibling question backlog `b7tlsh` names, and the precedent it points at does NOT transfer. `01reg8` removed `supports_deny_push` on the measured ground that it had no consumer and "only PRINTS a protection that does not exist". `supports_commit_gateway` has a consumer that the removed flag lacked: `synthetic_gated_action` requires it to keep the preflight's REFUSES/PROCEEDS coverage "non-vacuous and two-sided", and `tests/test_host_capability_wiring.bound_contract_action` reuses that seam to drive `execute_item_core`'s live refusal path. Since `01reg8` narrowed `ACTION_CLASSES` to `('read_only',)` with an empty `required`, it is the ONLY capability by which a refusal can be exercised at all, which `01reg8`'s own OQ-01 predicted in writing. So removal would convert a shipped two-sided gate into a one-sided one, and a gate that can never refuse in a test is the failure mode this whole area exists to refuse. The item's stated harm, a reader believing a protection is in force, is fully addressed by making the RECORDS honest (E-03, E-04) and pinning them (E-02), which costs no coverage. A maintainer preferring removal should say so at review; it would be a separate plan owing an answer to how the preflight keeps two-sided coverage afterwards.

### OQ-02: Should this plan populate `RUNNER_ACTION_TO_CONTRACT_ACTION`, which names `b7tlsh` as the successor that would?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: NO. The comment's own precondition is "when a mutating action acquires a real capability requirement", and no such requirement exists: `ACTION_CLASSES` is `('read_only',)` and its `required` is empty (F-6). The only capability available to require is permanently False, so mapping `execute` onto any gated action would refuse EVERY execute item on EVERY host, which is not a fix but an outage. `iot7hc` also recorded two measured reasons against mapping `execute -> read_only` specifically: `read_only`'s own `spec_basis` says "no agent session for a skip", and `format_host_capability_finding` interpolates the action name verbatim into the spec's byte-exact operator message. The seam is correctly left empty, and this plan's E-02 assertion (3) pins that no production action requires the capability, so a later plan that populates it must confront this invariant deliberately rather than by accident.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: All four captured outputs pasted verbatim. (a) must show `supports_commit_gateway` False AND its note containing `DECLARED, NOT PROBED`. (b) must show `binding` `UNBOUND-BY-DEPENDENCY` and an EMPTY `predicates` tuple; a non-empty tuple means a predicate now decides the code and E-03/E-04 must be re-authored, so this item FAILS rather than proceeding. (c) must show the list of actions requiring `CAP_COMMIT_GATEWAY` is EMPTY and `ACTION_CLASSES` is `('read_only',)`. (d) must show the `NO   supports_commit_gateway (runner-safety)` line and `0 (host, action) pair(s) refused`. State explicitly whether each matches this plan's authoring measurement.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: The new test's code pasted, plus `python3 -m pytest tests/test_host_capability_extension.py -o addopts="" -k CommitGatewayClaimConsistency` output showing it PASSES. Then prove it is NON-VACUOUS by making each of the three assertions fail once and pasting the failure: use the shipped `hsp.forced_runner_safety_verdicts({CAP_COMMIT_GATEWAY: (True, 'forced')})` seam for (1), and the shipped `synthetic_gated_action()` seam for (3), which registers an action requiring the capability. For (2) there is no shipped seam, and REVIEW DEMONSTRATED the mechanism to use rather than leaving the executor to invent one: `run_evidence.RunFindingCode` is a NamedTuple (`type(row).__mro__` contains `tuple`; `hasattr(row, '_replace')` is True), so substitute a mutated row and restore it in a `finally`, measured working at review:
    `row._replace(binding='BOUND', predicates=('fake_pred',))`, rebind `re_.RUN_FINDING_CODES` to the tuple with that row swapped in, assert the test FAILS, then restore the saved tuple. Observed: `MUTATED -> BOUND ('fake_pred',)` then `RESTORED -> UNBOUND-BY-DEPENDENCY`. Do this in the FALSIFICATION step only; do NOT ship a test that mutates the module-level table, because the rebind is process-global and a leak would corrupt later tests (the same hazard `forced_runner_safety_verdicts`'s own leak test exists to catch). An assertion that cannot be made to fail proves nothing. Also confirm by inspection of the pasted test code that it reads NO production source text and counts NO callers (AGENTS.md no-code-pinning rule); a test using `inspect`, `ast`, or a source grep FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff` of the spec showing the 2.1 clause rewritten, plus a grep proving the string "the commit gateway rejects `--no-verify` in its git sense" no longer appears. The replacement text must state BOTH halves: that git-sense `--no-verify` remains prohibited with no flag offering it, AND that the interception proving no bypass is unbuilt (`RUN-COMMIT-GATEWAY` unbound, `supports_commit_gateway` declared-never-probed, fail-closed). A diff that DELETES the prohibition FAILS this item: the prohibition is real and only the enforcement claim is at issue. ALSO prove the cross-references RESOLVE, by command and not by assertion: paste a grep showing the string "5.8 row 3" no longer appears anywhere in the spec, and paste the replacement reference beside a grep locating the text it names ("Hooks are not bypassed and a hook refusal remains a failure") together with the `### 5.2`/`#### Guarantee classification` heading that encloses it, demonstrating the target is inside 5.2 and not 5.8. A replacement that cites a row by ORDINAL alone, without the quoted text, FAILS this item, since an ordinal is what rotted.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff` of the spec showing ONLY row 2's `Enforcement or proof` cell changed in the guarantee-classification table. Paste greps proving four things are BYTE-UNCHANGED: the guarantee-2 statement "The agent cannot commit except through a path-scoped engine gateway", its `Host-dependent` bucket, row 1 (push denial), and row 3 (hooks). Also paste greps proving the three sites `01reg8` preserved are unchanged: the 5.2 bullet "prevent the agent from committing except through the engine's commit gateway", the 5.2 action-table row containing "commit gateway, hook-preserving commit", and the packet example line containing `"commit_gateway"`. A diff touching any of those FAILS this item (F-9).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: The tail of the spec's `## Workflow history` showing the new dated record naming `00pirb` and `b7tlsh`, plus the `aw specs note` command output. Paste a grep proving the spec's `- Status: approved` and `- Blocks-Release: next` lines are unchanged. Also paste: the BARE `python3 -m pytest` summary line; `aw ipd lint` on this plan reporting conforming; `aw check` showing no new violations; and `aw sanitize --agent` exiting zero. F-10's carrier (`089bq4`) was filed at authoring time, so confirm it still resolves rather than filing it here: paste `aw find backlog 089bq4` (or the equivalent) showing the item exists.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `aw find backlog ymlyqf` output showing it resolves and is `open`, plus its pasted front matter showing `- Status: open`, `- Work-Kind: bug`, and `- Blocks-Release: next`. Paste the item's body showing BOTH measurements are present: for row 1, the quoted cell text plus the names `supports_deny_push`/`CAP_DENY_PUSH` (removed by `01reg8`), `RUN-NO-PUSH` (retired by `4h7tt0`), and `sv9ce4`; for row 3, the quoted cell text plus `hook_preserving_commit` and `UNREPRESENTED_SPEC_CAPABILITIES`. Then RE-MEASURE both, pasting command output rather than restating the item: `python3 -c` printing `'hook_preserving_commit' in hsp.UNREPRESENTED_SPEC_CAPABILITIES` as True with the note text beside it, and `python3 -c` printing `hasattr(hsp, 'supports_deny_push')` and `hasattr(hsp, 'CAP_DENY_PUSH')` as False for each. If a re-measurement CONTRADICTS the item, this item is satisfied by CORRECTING the item and recording the change, not by leaving it stale. Also paste `aw check` showing no `check.ipd-uncarried-obligation` violation on this plan, which is what proves the `Carrier: ymlyqf` reference resolves, and no new `release-gates` violation from the gated item.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is a RECORD fix plus one regression test, and that shape is deliberate. The defect backlog
`b7tlsh` records is a spec claiming an enforcement that does not exist, so the two ways to close it are
to build the enforcement or to make the record honest. Building is the OS-level boundary project
(`sv9ce4`). Making the record honest costs nothing and removes the fail-open reading. The test is what
distinguishes this from the previous two attempts at the same area: `mjx7ne` measured the truth into a
`probe_notes` string and `4h7tt0` corrected one sentence, and the claim still drifted in three other
places, because nothing executable held the three artifacts in agreement. E-02 adds that.

The plan deliberately does NOT remove the capability (OQ-01) or populate the runner's empty action map
(OQ-02), and both refusals rest on measured evidence rather than caution: the first would make a
shipped gate untestable, and the second would refuse every execute item on every host.

SCOPE DECLARATION (a declaration the runner reconciles afterwards, not a gate to clear): within the
declared paths the intended surface is the spec's Section 2.1 flag clause and its 5.2 guarantee-row-2
`Enforcement or proof` cell plus one `aw specs note` history record; one new test class in
`tests/test_host_capability_extension.py`; and one new item under `.aw/records/backlog/open`. Everything
else in the spec is OUT, specifically guarantee rows 1 and 3, the 5.2 host-requirement bullet, the 5.2
action table, the 5.6 packet example, Section 7, and the 4.2 table. No production module is in scope. If
execution requires touching a path not declared here, MAKE the edit and then JUSTIFY it through
`aw ipd finalize --scope-reason`; do not silently widen and do not stop to ask. The one genuinely
unsafe condition that SHOULD stop this plan is named in E-01: if the descriptor, the finding-code
binding, or the requirement map has moved since authoring, stop and report, because the amendments would
then assert the opposite of the truth.

EXECUTION CONTRACT: commit ONLY the paths named in `- Scope-Paths:`, through
`aw commit 00pirb -- <paths>`; never `git add -A`, never bare or `-a`, and never push. Paste the ACTUAL
runner output rather than claiming success. When every `V-*` carries real pasted evidence and
`aw ipd lint --phase pre-transition` conforms, perform the terminal transition with
`aw ipd finalize 00pirb --actor <agent/model> --message <summary> --apply`; the RUNNER owns that
transition when it executes this plan in a lane, and `aw ipd begin` refuses with
`AW-LIFECYCLE-ROLE-001` in that case, so record the refusal and let the runner finalize rather than
hand-editing or hand-`git mv`-ing anything. This plan inherits `- Blocks-Release: next` from backlog
`b7tlsh`; AFTER EXECUTION, and not before, that item may be set `done` with `--evidence` citing this
executed plan. The ORDER is load-bearing: while this plan sits in `pending/`, closing `b7tlsh` fails
closed because the gate is handed to a carrier that has not shipped, so the item stays `graduated`.
Note backlog `ymlyqf` is a SEPARATE gated item, filed at review and only VERIFIED by E-06; it must not be closed by this plan.
