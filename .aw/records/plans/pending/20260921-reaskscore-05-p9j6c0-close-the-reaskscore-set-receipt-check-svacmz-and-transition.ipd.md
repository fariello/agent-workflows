# IPD: Close the reaskscore Set: receipt-check svacmz and transition both source backlog items honestly

- Date: 2026-09-21
- Kind: child
- Concern: The `reaskscore` Set's closing acts are owned by nobody who will perform them. They sit on the Order-0 orchestrator `s0gnha` as its E-02 (a receipt check over `svacmz`'s evidence) and E-03 (transitioning the two source backlog items), and the runner RETIRES an orchestrator once every child is `executed` while deliberately SKIPPING the pre-transition E/V checkpoint. E-03 IS THE SHARP CASE, because the parent's own text calls it "the one substantive act that belongs on this plan because it is a Set-level record change no child owns": two backlog items carrying `Blocks-Release: next` would be left untransitioned while the Set reported complete, so a release gate would silently survive a Set that claimed to have discharged it. MEASURED 2026-09-22 in run `run-20260922T003414Z-1020752`, where the orchestrator coverage probe refused a 34-set launch naming `s0gnha` among five uncovered parents (`events.jsonl`, event `orchestrator-probe-gate`).
- Scope: Perform `s0gnha`'s E-02 and E-03 as a real agent turn. IN: the receipt check over `svacmz`'s `V-01`..`V-04` evidence; the honest transition of backlog `yxfw4k` and `x7wfyx` through `aw backlog set`, respecting the close-legitimacy gate and each item's `Blocks-Release: next`; and a bare green suite on the merged result. OUT: `s0gnha` E-01's dispatch orchestration, which is the runner's act and not an agent's; any re-performance of `svacmz`'s verifications (it owns them, and duplicating them would put the same assertions in two places with no second observer); and any product code change.
- Scope-Paths: .aw/records/plans/pending, .aw/records/backlog/graduated, .aw/records/backlog/open, .aw/records/backlog/done
- Item-Dependencies: executed:svacmz
- Status: to-review
- Set: reaskscore
- Order: 5
- Highest E allocated: 03
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: p9j6c0

## Workflow history

- 2026-09-21 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.
- 2026-09-21 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored at the maintainer's direction after the orchestrator coverage gate refused run `run-20260922T003414Z-1020752`, naming `s0gnha` as carrying work no child covers. Content is lifted from the parent's E-02 and E-03 rather than invented, so the obligation is unchanged and only its owner moves; the parent's checklist stays in place. NOTE the parent's E-01 is deliberately NOT lifted: it is dispatch ordering, which a runner performs by construction and an agent cannot meaningfully "do".
- 2026-09-21 note (opencode/its_direct-pt3-claude-opus-5-1m-us): This Set was ALREADY partly self-aware of the retirement hazard: `svacmz` was authored to own the verifications "so it is performed and verified by an agent turn instead of being retired unperformed" (its child-table row says exactly that). What that fix missed is the BACKLOG TRANSITION, which no child took, and which is the release-gate-bearing half.

## Goal

Make the `reaskscore` Set's completion honest at its two weakest points: that `svacmz` actually pasted
evidence rather than asserting success, and that the two source backlog items reach the state the work
actually justifies. The second matters most: both carry `Blocks-Release: next`, so leaving them
untransitioned lets a Set report complete while a release gate it was meant to discharge quietly persists.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: receipt check, then the record transitions

- [ ] E-01 RECEIPT-CHECK `svacmz`'s FOUR VALIDATION ITEMS, by reading its executed plan file rather than by re-performing its work. This is deliberately a receipt check and NOT a second verification: `svacmz` owns the predicate-unweakened pins (its E-01/E-02) and both measured-shape reconstructions plus the collision case (its E-03/E-04), and duplicating them here would put the same assertions in two places with no second observer. CONFIRM SPECIFICALLY: `V-01` carries the five shared constants' ACTUAL VALUES and not a bare "unchanged"; `V-02` carries the pin output AND the `git diff` for both pin files; `V-03` and `V-04` carry the SHAPE A and SHAPE B reconstruction output and the collision case. An empty or hand-waved `Observed evidence` block on any of those four is a FAILURE of this item, and the Set is not complete - report it rather than compensating by running the checks here.
  - Depends on: none
  - Expected outcome: a per-item statement quoting the evidence line that satisfies each of `svacmz`'s `V-01`..`V-04`, or a named upstream failure identifying which block was empty.
  - Execution state: pending

- [ ] E-02 TRANSITION `yxfw4k` HONESTLY, RESPECTING ITS RELEASE GATE. Set it `done` ONLY IF its defect is fixed AND validated by `svacmz`'s evidence, as confirmed in E-01; if E-01 found that evidence absent, this item must NOT close it. It carries `Blocks-Release: next`, so `aw backlog set done` FAILS CLOSED unless the gate is provably preserved or released by one of the three documented fixes: a `From-Backlog` handoff on a plan carrying the same gate, a resolvable in-tree `--evidence` citation, or an explicit `--blocks-release -`. CHOOSE THE EVIDENCE ROUTE AND CITE `svacmz`'s EXECUTED PLAN, because that is the artifact that actually validated the fix; do NOT clear the gate with `--blocks-release -` merely to make the command succeed, which would discharge a release blocker by deleting it.
  - Depends on: E-01
  - Expected outcome: `yxfw4k` is `done` with a tool-written history entry citing `svacmz`'s evidence, and the close-legitimacy gate was satisfied by citation rather than by de-gating; pasted command output.
  - Execution state: pending

- [ ] E-03 TRANSITION `x7wfyx` TO `graduated`, NOT `done`, AND DO NOT CLEAR ITS `Blocks-Release`. The reason is substantive and is the parent's: only its item B is implemented, so `done` would assert delivery of work that was not delivered. `graduated` is the correct state - the design is handed off while code for the remainder is not written - and the release gate must SURVIVE the transition, because the undelivered half still gates the release. Use `aw backlog set` so the history entry is tool-written, and state in the message WHICH item (B) was implemented and which remains.
  - Depends on: E-01
  - Expected outcome: `x7wfyx` is `graduated` with its `- Blocks-Release: next` intact, and its history entry names the delivered and undelivered halves; pasted command output plus the item's front matter showing the gate still present.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN, and the remedy for a parent carrying uncovered work is to ADD A CHILD, never to delete the parent's items: that checklist is what makes a hand-run `execute <setid>` complete when no runner is involved (`AGENTS.md`). This plan adds coverage and changes nothing on `s0gnha` except its child table.
- THE CLOSE-LEGITIMACY GATE IS REAL AND FAILS CLOSED. `aw backlog set done` on an item carrying `- Blocks-Release:` refuses unless the gate is preserved via a `From-Backlog` handoff, released via a cited in-tree `--evidence`, or explicitly cleared with `--blocks-release -`. One shared predicate (`check_engine.evaluate_blocking_close`) backs the setter, the `aw check` rules and the opt-in hook, so they cannot diverge. `AGENTS.md` states this.
- `graduated` MEANS THE DESIGN IS HANDED OFF; `done` MEANS THE CODE IS WRITTEN AND VALIDATED. That distinction is why E-03 refuses `done` for a partly-implemented item.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH | `run-20260922T003414Z-1020752/events.jsonl`, event `orchestrator-probe-gate` | The coverage probe refused a 34-set launch naming `s0gnha` among five uncovered parents. Without this child, E-02 and E-03 are reported complete having never been performed. |
| F-02 | HIGH | `s0gnha` E-03, quoted; both items' front matter | E-03 is the release-gate-bearing half and the parent calls it "the one substantive act that belongs on this plan because it is a Set-level record change no child owns". Verified 2026-09-22: `yxfw4k` is `graduated` and `x7wfyx` is `open`, and BOTH carry `- Blocks-Release: next`. Retirement would leave both untransitioned while the Set claimed completion. |
| F-03 | MEDIUM | `svacmz`'s child-table row, quoted | This Set was already PARTLY aware of the hazard: `svacmz` exists expressly so the verifications are "performed and verified by an agent turn instead of being retired unperformed". The gap it missed is the backlog transition, which is exactly what F-02 names. |
| F-04 | MEDIUM | `s0gnha` E-01, quoted | The parent's E-01 is dispatch ordering, which a runner performs by construction. It is deliberately NOT lifted into this plan: an agent cannot meaningfully "perform" the queue order, and claiming to would be theatre. |

## Proposed changes (ordered, validatable)

1. Receipt-check `svacmz`'s four validation items and report any empty evidence block (E-01).
2. Close `yxfw4k` with a cited-evidence route that preserves rather than deletes its release gate (E-02).
3. Graduate `x7wfyx` with its release gate intact, naming what was and was not delivered (E-03).

## Deferred / out of scope (with reason)

- `s0gnha` E-01, THE DISPATCH ORDERING. A runner enforces it by construction (dependency depth is the
  first sort key and edges are re-checked at dispatch), so there is no agent act to perform. See F-04.
- RE-PERFORMING `svacmz`'s VERIFICATIONS. It owns them; duplicating them here would place the same
  assertions in two files with no second observer, which is the parent's own stated reason for making
  E-02 a receipt check.
- ANY PRODUCT CODE CHANGE. The three children delivered the code; this plan closes the records.

## Scope check

- Over-scope: none.
- Under-scope: none, and the one apparent gap is deliberate: the parent carries three `E-*` items and this
  plan covers two. E-01 (dispatch order) is excluded with its reason stated in F-04 and in the deferral
  list, rather than silently dropped.

## Required tests / validation

No product code changes, so no new unit test. V-01 requires a bare `python3 -m pytest` on the merged result,
which is one of the Set's own completion criteria and must be pasted rather than asserted.

## Spec / documentation sync

N/A. This plan changes no contract. The only structural edit is the child-table row on `s0gnha`, which is
what the coverage gate reads.

## Open questions

### OQ-01: If `svacmz`'s evidence is absent, may this plan close `yxfw4k` anyway on its own reading of the code?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO - REPORT THE UPSTREAM FAILURE AND LEAVE THE ITEM OPEN. Resolved from the parent's own wording rather than deferred: `s0gnha` E-03 makes the close CONDITIONAL ("only if its defect is fixed AND validated by `svacmz`'s evidence"), so absent evidence means the precondition is unmet, not that a substitute is needed. Closing a release-blocking item on the verifier's own re-reading would defeat the point of having an independent validator and would discharge a `Blocks-Release: next` gate on weaker grounds than the gate demands. E-01's expected outcome already requires naming which evidence block was empty, which makes the refusal auditable.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: for each of `svacmz`'s `V-01`..`V-04`, quote the evidence line that satisfies it - specifically the five constants' actual VALUES for `V-01`, the pin output plus both `git diff`s for `V-02`, and the SHAPE A / SHAPE B / collision output for `V-03`/`V-04`. A statement that they "carry evidence" without quoting it FAILS this item. Plus the bare `python3 -m pytest` summary line on the merged result.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw backlog set done yxfw4k ...` output showing it SUCCEEDED, plus the `--evidence` citation used, plus the item's resulting front matter. An execution that reached success by passing `--blocks-release -` FAILS this item even though the command exited 0, because that discharges a release blocker by deleting the gate rather than by satisfying it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `aw backlog set graduated x7wfyx ...` output, plus the item's front matter AFTER the transition showing `- Blocks-Release: next` STILL PRESENT, plus the history message quoted showing it names item B as delivered and the remainder as not. A transition to `done`, or one that cleared the gate, FAILS this item.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY files this plan changed, path-scoped; never `git add -A`; never push.
When reporting tests passed, paste the ACTUAL runner output. Do NOT mark an `E-*` item performed for work
not done, and do NOT fill a `V-*` `Observed evidence` block with anything but observed output.

THE HONESTY RULE THAT MATTERS MOST HERE concerns the two backlog transitions, because both items carry
`Blocks-Release: next` and both are therefore easy to "finish" dishonestly. Two specific moves are
forbidden: closing `yxfw4k` by clearing its gate with `--blocks-release -` so the setter stops refusing
(that deletes a release blocker rather than discharging it), and recording `x7wfyx` as `done` when only its
item B was implemented (that asserts delivery of work nobody did). If `svacmz`'s evidence is absent, the
correct outcome is a reported upstream failure with both items left as they are.

SCOPE FENCE. Touch ONLY the paths in `- Scope-Paths:`. Change NO product code, and do not edit `s0gnha`
beyond the child-table row that already exists by the time this runs. If the work genuinely requires a path
outside the fence, make the edit and justify it, since `aw ipd finalize` refuses to complete until every
out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

POST-GATE LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item
must carry observed evidence before the plan moves to `.aw/records/plans/executed/`. The runner owns the
terminal transition; a worker-role process is refused by `AW-LIFECYCLE-ROLE-001`.
