# IPD: Perform the Set-wide honesty comparison across both children's shipped output

- Date: 2026-09-20
- Kind: child
- Concern: Orchestrator `ao1rb7` carries E-03, a cross-child honesty comparison of Order 01's shipped gate disclosures against Order 02's shipped contract sentences, and NO CHILD COVERS IT. Its own OQ-02 raised this at review and named "ADD AN ORDER 03 CHILD" as option (b), leaving the choice to the maintainer. On 2026-09-21 the ORCHESTRATOR COVERAGE GATE refused `aw oc run` for exactly this parent, so the question is now answered by a run that will not start. Because `retire_orchestrator` deliberately skips the `pre-transition` E/V checkpoint (`ROLLUP_OMITTED_GATES["pre-transition-ev-checkpoint"]`), a runner would mark `ao1rb7` `executed` with the Set's own load-bearing honesty criterion never checked.
- Scope: Perform the cross-child comparison that neither sibling can perform from inside its own fence, and correct any sentence it finds untrue. IN: read every honest-limit disclosure shipped by Order 01 (`kbqpkn`) and every commit-contract sentence shipped or left standing by Order 02 (`y9vpvv`), judge each against what the code actually does, and run the parent's three cross-IPD checks. OUT: wiring any gate (that was `kbqpkn`'s decision and it resolved to wire none), changing what any gate DECIDES, and the agent-context detector the parent defers.
- Scope-Paths: agent_workflows/hooks/, agent_workflows/engine.py, AGENTS.md, .pre-commit-config.yaml, tests/test_gate_wiring.py
- Item-Dependencies: executed:kbqpkn, executed:y9vpvv
- Status: to-review
- Set: commitguard
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 2s0iym
- From-Backlog: wjl471

## Workflow history

- 2026-09-20 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored to own orchestrator `ao1rb7`'s E-03, which the ORCHESTRATOR COVERAGE GATE refused a run over on 2026-09-21. This plan exists because AGENTS.md prescribes adding a child for work found on a parent that no child covers, NOT deleting the parent's item: `ao1rb7`'s checklist stays exactly as it is, and this child is what makes its E-03 performable by an agent whose work passes the pre-transition E/V checkpoint. THE PARENT ALREADY ARGUED FOR THIS PLAN: its OQ-02 states option (b) verbatim ("ADD AN ORDER 03 CHILD that performs the cross-child read after both land, which AGENTS.md prescribes"), calls option (b) "more robust", and defers only because the choice depended on whether a runner would be used. A runner was used and refused, so option (b) is selected. MEASURED AT HEAD `41f6a45b` BEFORE AUTHORING, and two of the parent's stated premises are now STALE IN THE PLAN'S FAVOR. FIRST, `kbqpkn` is `executed` and it WIRED NOTHING: its OQ-01 resolved all four gates to "leave opt-in", so the comparison this plan performs is mostly a preservation check rather than a correction sweep, and the cheap outcome the parent's E-05 predicted ("every disclosure is unchanged and still true") is the likely one. Verified the partition the parent relies on still holds exactly: `grep -ci opt-in` over `agent_workflows/hooks/` gives 0 for both WIRED gates (`executed_transition_gate.py`, `status_untooled_gate.py`) and 3, 2, 3, 2 for the four opt-in ones (`ipd_dependency_statement_gate.py` 3, `precommit_scope_gate.py` 3, `backlog_blocking_close_gate.py` 2, `prepush_authorization_gate.py` 2). Also verified `.pre-commit-config.yaml` still registers only `ipd-executed-gate` (line 80) and `ipd-status-untooled-gate` (line 93), `default_install_hook_types: [pre-commit, pre-merge-commit]` (line 17) and `default_stages: [pre-commit]` (line 23) are unchanged, and the only installed hook in `.git/hooks` is still `pre-commit`, so `kbqpkn` genuinely added no stage. SECOND, THE PARENT'S E-02 BLOCKER HAS CLEARED: the parent says twice to "expect this edge to hold rather than to pass" because `lqly9m` was `to-review`, but `lqly9m` is now `- Status: executed` in `.aw/records/plans/executed/20260908-hookretry-01-lqly9m-...`, so `y9vpvv`'s `Item-Dependencies: executed:lqly9m` is SATISFIED and Order 02 can run. That is why this plan declares `executed:y9vpvv` as a real edge rather than as an aspiration. THE `immune to this by construction` SENTENCE THE SET IS ABOUT IS STILL LIVE at `engine.py:1320`, so Order 02's work is genuinely outstanding and this comparison has something to compare.
- 2026-09-20 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Perform the one check in the `commitguard` Set that spans both children, so the Set's completion criterion "no sentence shipped by either child describes a bypassable guard as an authority boundary" is verified by something that a pre-transition E/V checkpoint actually gates, rather than parked on a parent a runner retires without reading.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: read both halves and judge every sentence

- [ ] E-01 ENUMERATE AND QUOTE EVERY HONEST-LIMIT DISCLOSURE SHIPPED OR PRESERVED BY ORDER 01, then judge each against what the gate actually does. Order 01 wired nothing, so its deliverable was `tests/test_gate_wiring.py` plus the finding that all four gates stay opt-in; the disclosures it PRESERVED are therefore the subject. Quote each sentence with its `file:line`, and for each state whether it accurately describes a bypassable local check.
  THE SITES ARE THREE PER GATE, not one, and the parent's E-05 measured this: a gate's claim lives in (a) its module docstring, (b) its PRINTED refusal text, and (c) its `engine.create_*_hook` installer docstring. Read all three per gate for the four opt-in gates and the two wired ones. Do NOT grep for `opt-in` alone and call the enumeration done: a sentence can overclaim without using that phrase, which is exactly the failure mode (`"NOT an authority boundary"` is the honest form, and its absence is what matters).
  THE EXPECTED VERDICT IS "ALL ACCURATE, UNCHANGED", AND THAT IS A COMPLETE OUTCOME. Because `kbqpkn` wired nothing, every "OPT-IN" string remains true, and the parent's E-05 is explicit: "DO NOT 'FIX' THE DISCLOSURES IF YOU WIRE NOTHING ... editing them would create the very drift this item guards against." So a finding of zero corrections is the likely correct result and must be recorded as such, not padded with edits.
  - Depends on: none
  - Expected outcome: a table with one row per disclosure site (at least the three sites for each of the four opt-in gates), each row carrying the quoted sentence, its `file:line`, and an accurate/inaccurate verdict; plus an explicit count of corrections made, which may legitimately be zero.
  - Execution state: pending

- [ ] E-02 ENUMERATE AND QUOTE EVERY COMMIT-CONTRACT SENTENCE SHIPPED BY ORDER 02, then judge each the same way. Order 02 (`y9vpvv`) lands the ruled MUST wording plus `aw commit --no-plan`, and it rewrites the managed block installed into EVERY managed repo, so an overclaim here propagates further than a gate docstring.
  THE SPECIFIC SENTENCE THIS SET EXISTS TO GET RIGHT is at `engine.py:1320` and reads "PREFER THE TOOLED COMMIT PATH, which is immune to this by construction". Verified present at HEAD `41f6a45b`. "Immune by construction" is precisely the class of claim the Set forbids if a `--no-verify` or a hand-staged index can defeat it, so judge it against the code rather than against its own confidence, and check whether Order 02 replaced, narrowed, or left it.
  CHECK THE RENDERED COPY TOO, NOT ONLY THE SOURCE. `AGENTS.md` is GENERATED from `engine.py`, so a corrected sentence in the generator that was never regenerated leaves the false sentence in the file agents actually read. Compare both.
  IF ORDER 02's RETRY SENTENCE WAS WITHHELD, SAY SO AND WHY. Order 02's E-05 permits shipping the imperative while withholding the descriptive retry sentence if the retry is absent. `lqly9m` is now `executed`, so the retry SHOULD exist and the full wording should have shipped; if it did not, that is a finding, because a withheld sentence with a satisfied dependency means something else went wrong.
  - Depends on: none
  - Expected outcome: every contract sentence Order 02 shipped or left standing is quoted with its `file:line` and judged; the `engine.py:1320` claim is explicitly addressed; source and rendered `AGENTS.md` agree; and the retry sentence's presence or absence is stated with its reason.
  - Execution state: pending

### Task group 2: the cross-child comparison and the parent's cross-IPD checks

- [ ] E-03 COMPARE THE TWO HALVES AGAINST EACH OTHER, which is the work no sibling can do and the entire reason this plan exists. E-01 and E-02 each read ONE half; this item asks the question that spans them: does anything Order 01 shipped or preserved contradict anything Order 02 shipped?
  THE CONCRETE CONTRADICTION TO LOOK FOR, which the parent's cross-IPD section names: Order 01's half makes gates fire (or documents why they deliberately do not), while Order 02's wording tells agents the tooled path costs no round trip. If a gate REFUSES rather than rewrites, the retry claim does not cover it, and wording implying otherwise is the failure. Because Order 01 wired nothing, ALSO check the inverse asymmetry this creates: Order 02's wording must not imply a gate protects the commit path when that gate is opt-in and not installed here.
  STATE THE RESULT AS A CLAIM ABOUT THE SET, not as a per-file pass. The Set's completion criterion is a property of the whole shipped output, so the evidence must be a judgement over both halves together, naming any sentence corrected and in WHICH child's owning file.
  WHERE A CORRECTION BELONGS. The parent's scope check is explicit that a fix goes in the OWNING child's fence, but both siblings will be terminal when this runs, and AGENTS.md forbids adding commits to an executed plan. So this plan declares both halves' paths in its own `Scope-Paths` and makes the correction HERE, naming which child's territory it touched and why the correction could not be made there. If a correction turns out to be large enough to need its own review, file a corrective IPD instead and record that decision.
  - Depends on: E-01, E-02
  - Expected outcome: an explicit statement that no sentence shipped by this Set describes a bypassable guard as an authority boundary, or the offending sentences QUOTED and corrected with the owning child named; plus a statement of whether any correction was made here versus deferred to a corrective IPD.
  - Execution state: pending

- [ ] E-04 RUN THE PARENT'S THREE CROSS-IPD CHECKS, which are part of its E-03 scope and which a retiring runner also skips. These are mechanical and independent of the sentence judgement, so they are separated from E-03 rather than bundled into it.
  CHECK 1, `.pre-commit-config.yaml` INTEGRITY: confirm `default_install_hook_types` contents, and confirm `29wvmj`'s `pre-merge-commit` key plus its explanatory comment block are BYTE-UNCHANGED. MEASURED AT HEAD `41f6a45b`: the file has `default_install_hook_types: [pre-commit, pre-merge-commit]` (line 17) and `default_stages: [pre-commit]` (line 23), and `pre-push` is ABSENT because `kbqpkn` wired nothing. So the parent's expectation that this list would contain three entries is STALE; the correct check is that the two original entries survived and that the absence of `pre-push` matches `kbqpkn`'s recorded decision rather than an omission.
  CHECK 2, WIRING-VERSUS-WORDING NON-CONTRADICTION: this is E-03's subject, so here just confirm the mechanical input to it, namely which gates are registered (`ipd-executed-gate` at line 80, `ipd-status-untooled-gate` at line 93, measured) and which are not.
  CHECK 3, `AGENTS.md` REGENERATES WITH NO DIFF: regenerate the managed block from `engine.py` and confirm the committed `AGENTS.md` matches, so the Set leaves no hand-edited block behind. Paste the no-diff proof.
  ALSO CONFIRM `tests/test_gate_wiring.py` STILL PASSES AND IS STILL NON-VACUOUS, since it is `kbqpkn`'s only shipped deliverable and it is the durable guard against a seventh gate being added unclassified. Run it and paste the summary line.
  - Depends on: E-03
  - Expected outcome: all three cross-IPD checks performed with pasted evidence; the `pre-push` absence explained against `kbqpkn`'s decision rather than reported as a defect; `AGENTS.md` regeneration showing no diff; `tests/test_gate_wiring.py` passing.
  - Execution state: pending

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, AND A PARENT'S UNCOVERED ITEM GETS A CHILD RATHER THAN A DELETION. AGENTS.md: "if you are authoring a Set and find yourself writing a STEP on the Order-0 plan that no child covers, do NOT delete it: ADD A CHILD for it." This plan IS that child. `ao1rb7`'s checklist is left exactly as authored.
- `retire_orchestrator` SKIPS THE PRE-TRANSITION E/V CHECKPOINT BY DESIGN, recorded in `ipd_lifecycle.ROLLUP_OMITTED_GATES["pre-transition-ev-checkpoint"]` on the premise that "an orchestrator's items are performed by NOBODY". That premise is what makes parked parent work dangerous, and it is the mechanism the coverage gate now checks before spending a turn.
- `kbqpkn` WIRED NOTHING, AND THAT WAS THE CORRECT OUTCOME. Its OQ-01 found all four gates deliberately opt-in by a resolved maintainer decision in executed plan `diundn` ("NEVER installed by default"), and two of the four additionally FAIL a safety check (`precommit-scope-gate` refuses a clean tree with `check.scope-drift` findings against other agents' in-flight plans; `prepush-authorization-gate` exits 1 by design without `AW_PUSH_AUTHORIZED=1`). Its shipped deliverable is `tests/test_gate_wiring.py`, which pins the wired/exempt partition so a NEW gate cannot be added unclassified.
- THE OPT-IN PARTITION IS MECHANICAL AND CURRENT. `grep -ci opt-in` over `agent_workflows/hooks/`: `executed_transition_gate.py` 0, `status_untooled_gate.py` 0, `ipd_dependency_statement_gate.py` 3, `precommit_scope_gate.py` 3, `backlog_blocking_close_gate.py` 2, `prepush_authorization_gate.py` 2. Re-measured at HEAD `41f6a45b`.
- `AGENTS.md` IS GENERATED FROM `engine.py`, so any prose correction must be made in the generator and regenerated, never hand-edited in the rendered file.
- A DISCLOSURE LIVES IN THREE PLACES PER GATE: module docstring, printed refusal text, and `engine.create_*_hook` installer docstring. A one-site fix leaves two false copies.

## Findings

| Id | Severity | Location (measured at HEAD `41f6a45b`) | Finding | Evidence |
|---|---|---|---|---|
| F-01 | info | `ao1rb7` OQ-02 | The parent itself proposed this plan as option (b) and called it "more robust", deferring only on whether a runner would be used. A runner was used and refused, so the deferral condition resolved. | Parent OQ-02 text: "ADD AN ORDER 03 CHILD that performs the cross-child read after both land". |
| F-02 | error | `ao1rb7` E-03 + `ipd_lifecycle.ROLLUP_OMITTED_GATES` | The parent's E-03 is covered by no child, and orchestrator retirement skips the E/V checkpoint, so a runner would report it complete unperformed. This is the defect this plan closes. | `ORCHESTRATOR COVERAGE GATE` refused `aw oc run` naming `ao1rb7` on 2026-09-21. |
| F-03 | info | `agent_workflows/hooks/` | The wired-versus-opt-in partition the parent relies on still holds exactly: 0/0 for the two wired gates, 3/2/3/2 for the four opt-in ones. | `grep -ci opt-in` per module, re-measured. |
| F-04 | warn | `ao1rb7` E-02 and its gate prose | The parent says twice to expect Order 02 to defer as `dependency-blocked` because `lqly9m` was `to-review`. STALE: `lqly9m` is now `executed`, so the edge is satisfied and Order 02 can run. Do not read the parent's prose as current. | `.aw/records/plans/executed/20260908-hookretry-01-lqly9m-...ipd.md` reads `- Status: executed`. |
| F-05 | warn | `ao1rb7` cross-IPD check 1 | The parent expects `default_install_hook_types` to contain `pre-push` after the Set. STALE: `kbqpkn` wired nothing, so the list is still `[pre-commit, pre-merge-commit]` and `pre-push` is correctly absent. E-04 checks preservation, not addition. | `.pre-commit-config.yaml:17`; only `pre-commit` in `.git/hooks`. |
| F-06 | info | `engine.py:1320` | The "immune to this by construction" claim the Set exists to judge is still live at HEAD, so E-02 has a real subject. | `grep -n "immune to this by construction" agent_workflows/engine.py` -> line 1320. |

## Proposed changes (ordered, validatable)

1. Enumerate and quote every Order 01 disclosure site across all three site classes, judging each against actual behavior (E-01).
2. Enumerate and quote every Order 02 contract sentence, including the `engine.py:1320` claim, in both generator and rendered form (E-02).
3. Compare the two halves against each other and correct any sentence that describes a bypassable guard as a boundary, naming the owning child (E-03).
4. Run the parent's three cross-IPD checks plus `tests/test_gate_wiring.py`, with the `pre-push` absence explained against `kbqpkn`'s decision (E-04).

Most likely shipped diff: NONE, with a recorded judgement that every sentence is accurate. That is a complete and correct outcome, and the plan must not manufacture an edit to look productive.

## Deferred / out of scope (with reason)

- WIRING ANY GATE. `kbqpkn` resolved all four to "leave opt-in" on a cited maintainer decision, and two additionally fail a safety check. Reversing that is not this plan's business.
  - Carrier-Declined: A RESOLVED MAINTAINER DECISION, not an outstanding obligation. Executed plan `kbqpkn`'s OQ-01 settled all four gates as deliberately opt-in, citing `diundn`'s "NEVER installed by default" ruling. There is no future state in which this Set should wire them, so a carrier would assert pending work that nobody owes.
- CHANGING WHAT ANY GATE DECIDES. The parent's E-03-versus-E-05 boundary applies here verbatim: a disclosure STRING may be corrected, a predicate may not. A `git diff` on any touched hook module must show only docstring and literal-text lines.
  - Carrier-Declined: A SCOPE BOUNDARY, not deferred work. Correcting a false disclosure string and changing a predicate are different acts, and this plan does only the former. Nothing is left undone for a carrier to hold.
- THE AGENT-CONTEXT DETECTOR AND THE NEW COMMIT GUARD (backlog `wjl471` FINDING 1, its OQ-1..OQ-4). The parent defers these explicitly and they need a maintainer ruling on shape.
  - Carrier-Declined: Already carried by an OPEN backlog item: `wjl471` remains open and holds FINDING 1 plus its four open questions. Naming a second carrier here would duplicate a live record.
- CLOSING BACKLOG `wjl471`. The parent's OQ-01 is open on whether the item survives this Set, and it recommends keeping it open for the guard design. This plan does not close it.
  - Carrier-Declined: The item itself is the record, and it stays OPEN by the parent's own OQ-01 recommendation. An obligation to keep something open needs no carrier; closing it prematurely is the risk, and that is the parent's question to settle.
- FIXING `check.scope-drift`'s STALE-FROZEN-BASE DEFECT, which is why `precommit-scope-gate` refuses a clean tree. Plan `wmnmei` (Set `rcptstale`) owns it.
  - Carrier-Declined: Already carried by plan `wmnmei` (Set `rcptstale`), which owns this defect. A second carrier would duplicate it.
- THE `Readiness:` FIELD. Deliberately ABSENT: it is `/plan-review`'s attested output, and hand-writing it would forge a review that never happened.
  - Carrier-Declined: The ABSENCE is the correct permanent state, not an omission to fix later. `/plan-review` writes that field; hand-writing one forges a review. There is nothing to hand off.

## Scope check

- Over-scope: none. This plan reads and judges prose that the Set already shipped, and corrects only a sentence found untrue.
- Scope-Paths justification: the declared paths are the UNION of both children's prose surfaces, because a cross-child comparison must be able to correct either half and both siblings will be terminal when this runs (AGENTS.md forbids adding commits to an executed plan). `agent_workflows/hooks/` and `.pre-commit-config.yaml` are Order 01's territory, `agent_workflows/engine.py` and `AGENTS.md` are Order 02's, and `tests/test_gate_wiring.py` is read to confirm it still passes. Declaring them is NOT a licence to re-decide either child's work: E-03 states the narrow rule (correct a false disclosure string, never a predicate).
- Under-scope: this plan wires no gate, writes no new guard, changes no gate's decision logic, closes no backlog item, and fixes no scope-drift defect. Each is excluded above with its reason.

## Required tests / validation

- `tests/test_gate_wiring.py` passes, and its non-vacuity is confirmed rather than assumed (the file is `kbqpkn`'s only shipped deliverable).
- `AGENTS.md` regenerates from `engine.py` with no diff.
- If any hook module is touched, `git diff` on it shows only docstring or literal-text lines and no predicate, exit code, or message-selection change.
- Bare suite `python3 -m pytest`, judged on the failing NODE ID delta against a baseline measured in the executing worktree, never on totals. AFTER minus BEFORE must be EMPTY. Do NOT copy a baseline from `ao1rb7` or `kbqpkn`: both cite figures that are now wrong, and `kbqpkn`'s own V-06 records that its predecessor's cited failure did not reproduce because the environmental cause (~189 untracked `opencode-recovery/*.md` files) is absent in a lane worktree. Measure your own.
- `pre-commit run --all-files`, with the known pre-existing `ruff-format` failure on `tests/test_cli_output_docs_rollout.py` identified by FILE IDENTITY rather than by count, and NOT fixed here (it belongs to another party's commit `6e6b9bd0`).

## Spec / documentation sync

- NO SPEC AMENDMENT IS INTENDED, so no `.spec.md` path is declared in `Scope-Paths`. If E-03 finds that a shipped sentence contradicts a spec rather than the code, STOP and record it: amending a spec is a contract change that must be declared in `Scope-Paths` before the run starts (both runners announce declared spec edits up front and reconcile them at finalize), so it needs a new plan rather than an undeclared edit here.
- `AGENTS.md` is documentation OUTPUT, not a source: any correction goes in `engine.py` and is regenerated (E-04 check 3).
- Spec `77tr3o` R-5 shape (b) governs the retirement skip this plan exists because of. This plan CONSUMES that spec and does not amend it.

## Open questions

### OQ-01: Does correcting a sentence inside a terminal sibling's territory need a corrective IPD instead?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: A POLICY QUESTION ABOUT AUTHORING RULES, not an obligation this plan incurs. It becomes moot in the expected case (zero corrections, because `kbqpkn` wired nothing), and in the unexpected case E-03 already prescribes the fallback (file a corrective IPD), so no work is left unrecorded either way. A carrier would assert a pending task where what exists is a convention a maintainer may tighten.
- Resolution or deferral rationale: NON-BLOCKING because the expected correction count is ZERO (`kbqpkn` wired nothing, so every "OPT-IN" string stays true) and because E-03 already states the fallback: if a correction is large enough to need its own review, file a corrective IPD and record that decision instead of making the edit here. The tension is real and worth a ruling eventually: `ao1rb7`'s scope check says a fix belongs "in the OWNING child's fence", but both children will be `executed` when this runs and AGENTS.md forbids adding commits to an executed plan, so the owning fence is closed by construction. This plan resolves that by declaring both halves' paths itself, which is the only route that does not either edit an executed plan or leave a false sentence shipped. A maintainer may prefer a stricter rule (always file a corrective IPD, never touch a terminal sibling's files from a later child); if so, E-03's fallback branch is the one to make mandatory.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the full disclosure table with one row per site, each row carrying the QUOTED sentence and its `file:line`. At minimum it must cover three sites for each of the four opt-in gates (module docstring, printed refusal text, `engine.create_*_hook` docstring) and state the verdict per row. ALSO paste the re-measured `grep -ci opt-in` counts per hook module and compare them to the 0/0/3/3/2/2 partition recorded in this plan's Findings, naming any difference. A blanket "the disclosures are fine" does NOT satisfy this item; the sentences must be quoted. State the correction count explicitly, and if it is zero, say so as a positive finding rather than leaving it implied.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste every Order 02 contract sentence with its `file:line`, including an explicit verdict on the `engine.py:1320` "immune to this by construction" claim (present at HEAD, so it must be addressed either as corrected, narrowed by Order 02, or judged accurate with the reason). Paste the comparison showing the generator prose and the rendered `AGENTS.md` prose agree. State whether Order 02's descriptive retry sentence shipped, and since `lqly9m` is now `executed`, justify any withholding as a finding rather than as the expected path.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the explicit cross-half judgement: a statement that no sentence shipped by this Set describes a bypassable guard as an authority boundary, OR each offending sentence quoted with its correction and the owning child named. The judgement must reference BOTH halves together (a per-file pass is not a Set-wide claim). If any sentence was corrected, paste the `git diff` for it and confirm no predicate, exit code, or message-selection logic changed. If a correction was deferred to a corrective IPD, name that IPD.
  - STATE WHO PERFORMED THIS ITEM AND IN WHAT MODE (agent-executed child, or human). This child exists precisely so that the answer is never "nobody"; recording the performer is what distinguishes this from the parent's unperformable E-03.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste (1) `.pre-commit-config.yaml`'s `default_install_hook_types` and `default_stages` lines plus `29wvmj`'s `pre-merge-commit` entry and comment block, with an explicit statement that they are byte-unchanged and that `pre-push`'s absence matches `kbqpkn`'s recorded decision; (2) the list of registered gate ids with line numbers; (3) the `AGENTS.md` regeneration no-diff proof; (4) the `tests/test_gate_wiring.py` run summary line. Also paste the bare-suite BEFORE and AFTER failing node id sets and show the delta is empty, using a baseline measured in this worktree rather than any figure cited in this Set's plans.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`. No `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened.

THIS PLAN RUNS LAST IN ITS SET, BY CONSTRUCTION. It declares `Item-Dependencies: executed:kbqpkn, executed:y9vpvv` because a comparison of two children's shipped output cannot run before both have shipped. `kbqpkn` is already `executed`; `y9vpvv` is `approved` with its own `executed:lqly9m` edge now SATISFIED (`lqly9m` is `executed`), so the remaining sequencing is `y9vpvv` then this plan. Under a runner, `dependency_depth` sorts this item last in the Set and the edge is re-checked AT DISPATCH, so if `y9vpvv` has not landed this item is marked `dependency-blocked` and the run continues rather than failing. That is correct behavior and is not a defect to report.

WHAT THIS PLAN DOES TO ITS PARENT, stated so nobody mistakes the intent: NOTHING is deleted from `ao1rb7`. Its E-01, E-02 and E-03 stay exactly as authored, because that checklist is what makes `execute commitguard` complete when a human drives the Set with no runner involved. This plan's row is ADDED to the parent's `## Child IPDs` table so the parent's Set is covered, which is what lets the ORCHESTRATOR COVERAGE GATE pass and lets the runner retire the parent honestly once every child is `executed`. The parent's E-03 is then discharged by CITING this child's pasted evidence, which is the correct discharge for an orchestration item.

Execution contract: commit ONLY files you changed, path-scoped (`git commit -m msg -- <path>`), never `git add -A`, never `-a`, and never push. THIS IS A SHARED CHECKOUT with other agents and humans working concurrently: verify the staged set with `git diff --cached --name-only` before every commit and `git restore --staged <path>` anything that is not yours, and re-verify after ANY failed hook, because `pre-commit` restores unstaged changes on rejection and can leave paths you never staged in the index. Do NOT reach for `--no-verify` anywhere in this Set: the Set's whole subject is the honesty of local guards, so bypassing one to land a change about them would be self-refuting. Do not delete or stage another party's untracked files (notably any `opencode-recovery/` dump), even to make a suite green. When every `E-*` is performed and every `V-*` carries pasted evidence, move this plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never by hand.
