# IPD: Decide what RUN-NO-PUSH enforcement means before binding it, or keep it honestly unbound

- Date: 2026-09-08
- Kind: child
- Concern: `RUN-NO-PUSH` is the last remaining UNBOUND-UNBUILT finding code in spec `25kzda` 4.2: a name with no predicate behind it. It requires host push-denial ENFORCEMENT, and nothing in this repository implements one. The capability it would read, `supports_deny_push`, defaults `False` (`host_sandbox_profile.py:204`) and is "DECLARED AND NEVER PROBED, with the reason recorded in `probe_notes`" (`:88-95`), because it names host enforcement that "does not exist in this repository, so there is nothing to attempt". It therefore fails closed today, which is CORRECT and is not the defect. The defect is that the guarantee is owed and nothing records the design decision needed to either honor it or retire it.
  THE OBVIOUS IMPLEMENTATION IS EXPLICITLY FORBIDDEN, and that prohibition is the reason this is a spec-first plan rather than a coding plan. The same paragraph states: "Inferring support from the presence of the driver-side `git_commit_helper.offer_commit` helper is FORBIDDEN: a helper the driver chooses to call is not a boundary an agent cannot evade, and reporting it as one is the same fail-OPEN inference the sandbox probes above exist to refuse." So a plan may not bind `RUN-NO-PUSH` by detecting a helper, a hook, a config flag, or any other in-repo artifact's presence. Either a real boundary exists that an agent cannot evade, or the code must stay honestly unbound.
  THE BACKLOG ITEM ALSO SAYS SO, and its warning is inherited here verbatim in substance: `RUN-NO-PUSH` "is a security-boundary design of `1o4eif` magnitude and should not be picked up casually; treat it as needing a spec-level decision first, and do NOT let a future plan bind either code to a presence-based inference, which is the fail-open pattern already rejected once for the host capabilities."
  ITS SIBLING HALF IS ALREADY DEAD, which is why this plan covers one code and not two. The item was filed for `RUN-BASELINE-OWNERSHIP` and `RUN-NO-PUSH` together; the former is now BOUND, and the code says so: "`RUN-BASELINE-OWNERSHIP` is now BOUND, not UNBOUND-UNBUILT: the per-path lease overlap check F3 said nobody had built ships as `worktree_lease.LeaseTable.claim` (`m2wwns`), and `dirty_within` decides the pre-existing-dirty-path half" (`run_evidence.py:1221-1223`). Verified at HEAD: `LeaseTable.claim` exists (`worktree_lease.py:836`) and `run_evidence.dirty_within` exists (consumed at `ipd_lifecycle.py:892-895`). Do not build a second lease-overlap check.
- Scope: Produce the SPEC-LEVEL DECISION `RUN-NO-PUSH` needs, and implement only what that decision authorizes. Three outcomes are legitimate: a real enforcement boundary is specified and built; the guarantee is narrowed to what a host can actually prove; or the code is retired from 4.2 as unachievable here and the spec says so. This plan writes NO fail-open binding under any outcome.
- Scope-Paths: .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md, agent_workflows/run_evidence.py, agent_workflows/host_sandbox_profile.py, tests/test_run_no_push_boundary.py
- Item-Dependencies: none
- Status: to-review
- Set: nopush
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 4h7tt0
- From-Backlog: d07nz2
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `d07nz2`, HALVED. The item covers two finding codes; `RUN-BASELINE-OWNERSHIP` was BUILT after the item was written and is now BOUND (verified at HEAD by symbol: `worktree_lease.LeaseTable.claim`, `run_evidence.dirty_within`), so graduating the item as written would have commissioned a second lease-overlap check. Only `RUN-NO-PUSH` survives. Authored as a SPEC-FIRST plan because the item itself demands a spec-level decision first and forbids presence-based inference, and because the maintainer already ruled on the parallel case (`mjx7ne` OQ-03) that the capability may be declared `False` with a `probe_notes` entry rather than probed.

## Goal

Replace an owed-but-undesigned guarantee with a recorded decision: either `RUN-NO-PUSH` names a boundary an agent cannot evade, or the spec states plainly that this repository does not provide one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish what is actually true, and what a boundary would have to be

- [ ] E-01 RECORD THE CURRENT STATE BY SYMBOL, and confirm the sibling half is dead before touching anything. Establish and write down: that `RUN-NO-PUSH` is the only remaining UNBOUND-UNBUILT code in 4.2 (the code's own tally is "10 BOUND, 2 UNBOUND-BY-DEPENDENCY, 1 UNBOUND-UNBUILT", `run_evidence.py:1231`); that `supports_deny_push` defaults `False` and is never probed with its reason in `probe_notes`; and that `RUN-BASELINE-OWNERSHIP` is BOUND.
  IF THE TALLY HAS MOVED, SAY SO AND RE-SCOPE. Codes have been re-bound twice already as their dependencies executed, which is exactly why this item's own sibling half died. Trust the tree, not this plan's Concern.
  - Depends on: none
  - Expected outcome: a written, symbol-cited statement of which codes are bound, that `RUN-NO-PUSH` alone is unbound-unbuilt, and that no second lease-overlap check is needed.
  - Execution state: pending

- [ ] E-02 ENUMERATE THE CANDIDATE ENFORCEMENT MECHANISMS AND WHAT EACH CAN AND CANNOT PROVE, without choosing one. This is the analysis the spec decision needs, and it must be honest about evadability rather than optimistic. At minimum consider: an OS/sandbox-level network or exec restriction; a git-level mechanism (a `pre-push` hook, a remote-less clone, a push-denying credential); a host-runtime restriction the adapter can attest; and the null option (no boundary is available here).
  FOR EACH, STATE THE EVASION. The prohibition this plan inherits is not "do not use a helper", it is "a boundary an agent cannot evade". A `pre-push` hook can be bypassed with `--no-verify`; a helper the driver chooses to call can be sidestepped by calling git directly; a config flag can be rewritten by the agent it constrains. Name the evasion for each candidate or the analysis is worthless.
  DO NOT PICK THE WINNER HERE. The choice is the maintainer's (OQ-01), because it is a security-boundary decision of `1o4eif` magnitude and because two of the three legitimate outcomes CHANGE AN APPROVED SPEC.
  - Depends on: E-01
  - Expected outcome: a candidate table with, per mechanism, what it proves, what it cannot prove, and its concrete evasion; no mechanism selected.
  - Execution state: pending

### Task group 2: implement only what the decision authorizes

- [ ] E-03 AMEND SPEC `25kzda` 4.2's `RUN-NO-PUSH` ROW TO MATCH THE DECISION, and amend nothing else. Exactly one of three edits, per OQ-01's answer: (a) the row states the specified boundary and the conditions under which a host may claim it; (b) the row is NARROWED to a guarantee a host can actually prove; or (c) the row is RETIRED from 4.2 with the reason recorded, i.e. the spec stops promising something this repository cannot deliver.
  THE SPEC FILE IS DECLARED IN `- Scope-Paths:` DELIBERATELY, so the amendment is announced before the run starts and reconciled by the finalize scope gate (`AGENTS.md:82`). Say WHY in the spec-sync section, since a 4.2 edit changes what every run is checked against.
  DO NOT TOUCH 4.2's TABLE STRUCTURE OR ANY OTHER ROW. The finding-code table is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` under a byte-equality test, so editing a neighbouring cell IS a code change and would fail the suite. Change the one row the decision names.
  - Depends on: E-02
  - Expected outcome: exactly one row amended to match the recorded decision, with the reason stated, and the byte-equality test still passing.
  - Execution state: pending

- [ ] E-04 MAKE THE CODE AND THE TEST MATCH THE AMENDED SPEC, AND PROVE NO FAIL-OPEN BINDING WAS INTRODUCED. Under outcome (a) build the specified boundary and bind the code to it; under (b) bind the narrowed guarantee; under (c) leave `supports_deny_push` `False` and make the honest-unbound state EXPLICIT rather than incidental, with the `probe_notes` entry citing the amended spec row.
  THE ANTI-FAIL-OPEN TEST IS REQUIRED UNDER ALL THREE OUTCOMES, because it is the one assertion that cannot become stale: assert that `supports_deny_push` is NOT set True by the mere presence of `git_commit_helper.offer_commit`, a hook file, or a config value. That inference is forbidden by `host_sandbox_profile.py:88-95` and was already rejected once for the host capabilities; a test pinning the refusal is what stops it being reintroduced by a future well-meaning change.
  - Depends on: E-03
  - Expected outcome: code state matches the amended spec row; a test pins the refusal of presence-based inference under every outcome; the byte-equality test between 4.2 and `RUN_FINDING_CODES` passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec 4.2's finding-code table is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so a spec cell edit IS a code change. Amend one row, deliberately.
- `mjx7ne` OQ-03 established the governing precedent: a capability naming enforcement that does not exist may be DECLARED `False` with a `probe_notes` reason rather than probed. Honest-unbound is a legitimate, already-sanctioned outcome, not a failure.
- Presence-based inference is FORBIDDEN for these capabilities, in writing, at `host_sandbox_profile.py:88-95`. Both `supports_commit_gateway` and `supports_deny_push` default `False` and fail closed.
- `wlxkoz`'s design rule, inherited: a code honestly reporting itself unbound is SAFE, while a code silently wired to a predicate that does not answer its question is a fail-OPEN checker. Retiring or narrowing beats binding-something-adjacent.
- Shared checkout; the suite runs BARE. Re-locate symbols before editing.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | half the item is dead | `RUN-BASELINE-OWNERSHIP` is BOUND, so the item's "nothing implements one" is false at HEAD and no second lease check may be built. | `run_evidence.py:1221-1223`; `worktree_lease.LeaseTable.claim` at `:836`; `run_evidence.dirty_within` consumed at `ipd_lifecycle.py:892-895` |
| F-2 | HIGH | the obvious fix is forbidden | Binding the code by detecting `git_commit_helper.offer_commit` (or any in-repo artifact's presence) is explicitly prohibited as fail-open. | `host_sandbox_profile.py:88-95` |
| F-3 | HIGH | it is a spec decision | Two of the three legitimate outcomes AMEND an approved spec, so an agent may not choose among them; the item itself says "needs a spec-level decision first". | item text; spec `25kzda` is `- Status: approved` |
| F-4 | MEDIUM | current state is safe | `supports_deny_push` defaults `False` and is never probed, so today's behavior fails closed. The defect is an undesigned obligation, not a live hole. | `host_sandbox_profile.py:204`, `:88-95` |
| F-5 | MEDIUM | precedent for honest-unbound | `mjx7ne` OQ-03 already ruled a non-existent enforcement may be declared `False` with a `probe_notes` reason rather than probed, so outcome (c) is sanctioned rather than a cop-out. | `mjx7ne` in `.aw/records/plans/executed/`; `probe_notes` at `host_sandbox_profile.py:212` |
| F-6 | MEDIUM | table is byte-pinned | 4.2's table is transcribed into `RUN_FINDING_CODES` under byte equality, so an incidental cell edit breaks the suite. | the byte-equality test over `RUN_FINDING_CODES` |
| F-7 | LOW | last one standing | `RUN-NO-PUSH` is the sole UNBOUND-UNBUILT code; the other unbound pair waits on `runtrail-01`'s trailers being READ, not written. | `run_evidence.py:1224-1231` |

## Proposed changes (ordered, validatable)

1. Record the current bound/unbound tally by symbol and confirm the sibling half is dead (E-01).
2. Enumerate candidate enforcement mechanisms with, for each, its concrete evasion (E-02).
3. Amend exactly one 4.2 row to match the maintainer's decision (E-03).
4. Make code and tests match, and pin the refusal of presence-based inference (E-04).

## Deferred / out of scope (with reason)

- `RUN-BASELINE-OWNERSHIP`: now BOUND (F-1). Removed from this plan's scope entirely; building a second lease-overlap check would duplicate `worktree_lease.LeaseTable.claim`.
- `RUN-COMMIT-CONTENTS` / `RUN-COMMIT-GATEWAY`: unbound but WAITING on something else. `runtrail-01` (`m73aet`) shipped the `AW-Run:`/`AW-Item:` trailers as WRITERS only; nothing reads a trailer back, and writing one is not proving a commit's tree diff equals the item-owned delta. Binding them now would be the same fail-open error. Not this plan.
- `RUN-HOST-CAPABILITY`: BOUND by `mjx7ne`. Not this plan.
- BUILDING A SANDBOX or network-restriction layer: if outcome (a) selects one, it is its own plan of `1o4eif` magnitude. This plan produces the decision and the spec row, not a sandbox.

## Scope check

- Over-scope: none, but note this plan DECLARES a spec file and may amend it, which is deliberate and announced.
- Under-scope: this plan does NOT build a sandbox, does NOT touch the other three unbound-or-recently-bound codes, and does NOT bind `RUN-NO-PUSH` to anything under outcome (c).

## Required tests / validation

The byte-equality test between spec 4.2 and `run_evidence.RUN_FINDING_CODES` must pass after the row edit. New `tests/test_run_no_push_boundary.py` pins that `supports_deny_push` is not inferred from any artifact's presence, under whichever outcome lands. Plus the bare suite on a self-measured delta.

## Spec / documentation sync

THIS PLAN AMENDS SPEC `25kzda` 4.2's `RUN-NO-PUSH` ROW, and the spec file is declared in `- Scope-Paths:` so the edit is announced before the run and reconciled afterwards. WHY: 4.2 currently promises a guarantee no code delivers and no host can prove, which is the fail-open shape `wlxkoz` was built to avoid; the amendment makes the spec say what is true, whichever of the three outcomes the maintainer chooses.

DO NOT EDIT ANY OTHER 4.2 ROW OR THE TABLE STRUCTURE: it is byte-equal to `RUN_FINDING_CODES` under test, so a neighbouring edit is a code change. If the decision turns out to require touching a second row, STOP and report rather than widening silently.

## Open questions

### OQ-01: Which of the three outcomes should `RUN-NO-PUSH` take: specify a real boundary, narrow the guarantee, or retire the code?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: BLOCKING AND NOT AGENT-RESOLVABLE, for two independent reasons, and the plan is deliberately unexecutable without the answer. FIRST, it is a SECURITY-BOUNDARY decision: the backlog item calls it "of `1o4eif` magnitude" and says it "should not be picked up casually" and needs "a spec-level decision first". SECOND, two of the three outcomes AMEND AN APPROVED SPEC, and an agent may not choose to weaken or retire a shipped guarantee on its own authority.
  THE THREE OPTIONS WITH THEIR REAL COSTS. (a) SPECIFY AND BUILD A BOUNDARY: honors the guarantee, but every candidate mechanism has a known evasion (a `pre-push` hook falls to `--no-verify`; a driver-side helper falls to calling git directly; a config value falls to the agent rewriting it), so a genuine boundary likely means OS/sandbox-level enforcement, which is a large separate plan. (b) NARROW THE GUARANTEE to what a host can actually prove (for example: no push is ATTEMPTED on the driver's own path, attested rather than enforced), which is honest and cheap but is strictly weaker than what 4.2 says today, so it is a documented reduction in a shipped promise. (c) RETIRE THE CODE from 4.2 with the reason recorded, which is the cheapest and arguably the most honest, is already sanctioned in shape by `mjx7ne` OQ-03 (declare `False` with a `probe_notes` reason rather than probe), and matches `wlxkoz`'s rule that an honestly-unbound code is safe while a silently-mis-bound one is fail-open; its cost is that the release ships with one fewer promised guarantee.
  MY READING, OFFERED AND NOT ADOPTED: (c) or (b), because the current state already fails closed, so the practical risk of retiring or narrowing is low, while (a) commissions a sandbox project. But this is exactly the "scope, priority, risk appetite, public contracts" class the workflow reserves for the human.
  WHAT MUST NOT HAPPEN, under any answer: binding the code to a presence-based inference. That is forbidden in writing at `host_sandbox_profile.py:88-95`, was already rejected once for the host capabilities, and would convert a safe fail-closed state into a fail-OPEN checker that reports a boundary nobody enforces.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the current bound/unbound tally with its source line, and paste `supports_deny_push`'s default plus its `probe_notes` reason. Paste the symbol-level proof that `RUN-BASELINE-OWNERSHIP` is BOUND (`worktree_lease.LeaseTable.claim` and `run_evidence.dirty_within` both located), and state explicitly that no second lease-overlap check will be built. If the tally has moved since authoring, paste the new one and state how this plan's scope changed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the candidate table. For EACH mechanism it must state what it proves, what it cannot prove, and a CONCRETE evasion; a row without a named evasion is an incomplete analysis and fails this item. Confirm in prose that no mechanism was selected, since selecting one is OQ-01's answer and not this item's job.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste OQ-01's recorded answer (quoting the maintainer's decision and its date), then paste the spec diff showing EXACTLY ONE row changed. Paste the byte-equality test between 4.2 and `RUN_FINDING_CODES` PASSING. Paste `git diff --stat` for the spec file showing the edit is confined to the `RUN-NO-PUSH` row, and quote the recorded reason from the spec-sync section.
    If OQ-01 is unanswered, this item must be UNSTARTED and that is the correct state: paste nothing and record that execution was refused pending the decision.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the code state matching the amended row, naming which outcome landed. Under (c), paste `supports_deny_push` still `False` with its `probe_notes` entry now citing the amended spec row.
    THE MANDATORY ASSERTION UNDER ALL THREE OUTCOMES: paste the test proving `supports_deny_push` is NOT set True by the presence of `git_commit_helper.offer_commit`, a hook file, or a config value, and paste it FAILING against a deliberately fail-open stub so the test is shown to have teeth. A test that passes against a fail-open implementation pins nothing.
    Paste the bare `python3 -m pytest` summary line with a self-measured BEFORE baseline and the AFTER-minus-BEFORE failure set EMPTY. Inside a lane worktree, ~14 `test_run_viewer.py` failures belong to the separate `agrlvw` defect (plan `utwr6y`); do not report them as this plan's.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`), AND OQ-01 must be answered first: it is `Blocking: yes`, so `aw ipd set approved` will refuse while it stands, which is deliberate. E-01 and E-02 are analysis and could technically run without the answer, but E-03 and E-04 cannot, so do not begin expecting to finish.

THE CURRENT STATE IS SAFE, WHICH CHANGES THE RISK CALCULUS. `supports_deny_push` already defaults `False` and fails closed, so there is no live hole to race. The wrong move here is not slowness; it is binding the code to something that does not enforce anything. Under every outcome, a fail-open binding is prohibited.

NEVER INFER SUPPORT FROM PRESENCE. Not from `git_commit_helper.offer_commit`, not from a hook file, not from a config flag. This is forbidden in writing at `host_sandbox_profile.py:88-95` and was already rejected once for the host capabilities; V-04 pins the refusal precisely so a future change cannot reintroduce it.

ONE SPEC ROW. 4.2's table is byte-equal to `RUN_FINDING_CODES` under test; editing a neighbouring cell is a code change that will fail the suite. If the decision seems to need a second row, STOP and report.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT: run `aw runs` before starting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

On completion, close backlog `d07nz2` (this plan carries `- From-Backlog: d07nz2` and inherits its `Blocks-Release: next`). The item's file records that its `RUN-BASELINE-OWNERSHIP` half was already dead; the close must not claim that half was built.
