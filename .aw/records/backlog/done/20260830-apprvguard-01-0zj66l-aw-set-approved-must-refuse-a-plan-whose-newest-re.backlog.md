- Id: 0zj66l
- Status: done
- Blocks-Release: next
- Set: apprvguard
- Priority: high
- Work-Kind: bug
- Summary: aw set approved must refuse a plan whose newest review verdict is negative or that has unanswered blocking open questions, with an explicit override arg for the OQ case only

## Workflow history
- 2026-09-04 set (aw backlog): closed by aw oc run: IPD d7bnhc executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260831-apprvguard-01-d7bnhc-aw-set-approved-must-refuse-a-plan-whose-newest-review-verdi.ipd.md); evidence .aw/records/plans/executed/20260831-apprvguard-01-d7bnhc-aw-set-approved-must-refuse-a-plan-whose-newest-review-verdi.ipd.md

OBSERVED 2026-08-30, and it caused real damage rather than being theoretical.

WHAT HAPPENED. The maintainer gave a standing instruction, "I APPROVE all the reviewed IPDs", before
stepping away. The orchestrating agent applied it by selecting on STATUS alone and ran `aw ipd set
approved` on every plan reading `reviewed`. FIVE of those plans (`r4mbcw`, `bmh754`, `kaygwo`,
`k7o7el`, `7f7782`, the whole `detrun` Set) had a NEWEST `/plan-review` verdict of
`REJECT - NEEDS REPLAN`, with their `E-*` items marked `Execution state: blocked` and per-item
DO-NOT-BUILD notes. One of them, `bmh754`, opened its own Goal section with `REPLAN - DO NOT EXECUTE`.

The `--by-human` attestation was truthful (a human really did instruct it) and the tooling accepted it
without complaint, because NOTHING in the approval path reads the review verdict. Verified:
`grep -rn "NO-GO\|REJECT" agent_workflows/status_set.py` returns ZERO matches, so the setter has no
verdict awareness whatsoever.

CONSEQUENCE. `approved` is the EXECUTABLE state. All five became selectable by the runner. A sibling
in the same Set, `a54m79`, was launched, refused at pre-execution on its unresolved blocking open
questions, and cascaded four dependents to `dependency-blocked` (run-20260830T202022Z-3475919). Had
those plans instead refused for the OTHER reason (no blocking OQ but a REJECT verdict), they would
have EXECUTED and rebuilt machinery that already ships: `parse_item_dependencies`,
`evaluate_ipd_dependencies`, the six `check.ipd-dependency-*` rules, `dependency_cutover_date`, the
`aw ipd dependencies set` verb, and the statement-gate hook are all present in main today.

So the pre-execution OQ gate caught the accident by luck, not by design: it fires on unanswered
questions, not on a negative verdict. A REJECTed plan with all its questions answered has NOTHING
stopping it.

WHAT TO BUILD (maintainer-specified 2026-08-30).

1. REFUSE ON A NEGATIVE NEWEST VERDICT. `aw set approved` / `aw ipd set approved` must read the
   plan's newest review verdict and refuse when it is negative. NO OVERRIDE for this case: the
   maintainer was explicit. If a review says do not build it, approving it is always a mistake, and
   the correct action is to re-scope or retire the plan, not to force it through.

2. REFUSE ON UNANSWERED BLOCKING OPEN QUESTIONS, WITH AN OVERRIDE. A plan carrying an `OQ` with
   `Blocking: yes` and `Status: open` must also be refused, but here an explicit argument MAY
   override, because a maintainer legitimately sometimes approves authority-to-run ahead of a
   question they intend to answer before execution. That already happens in this repo: `zhr6mc` was
   approved with a history note recording "approval here records authority to run, not readiness to
   start". The override must be a named flag, must be recorded in the history entry, and must NOT be
   implied by `--by-human`.

DESIGN QUESTIONS TO RESOLVE, not prescribed here.

- WHERE does the verdict live, and is it reliably machine-readable? `is_plan_review_approved`
  (`oc_runipd.py`) already parses the newest history entry for `GO - PENDING HUMAN APPROVAL` and
  rejects `NO-GO`/`CONDITIONAL-GO`, so a predicate exists and should be REUSED rather than forked.
  Check whether the `revgate` Set's typed review-findings artifact (now in main) supersedes prose
  parsing; if it does, read the typed artifact and treat prose as the legacy path.
- IS PROSE PARSING SOUND ENOUGH TO GATE ON? A verdict stated in free text is fragile. Note the
  measured counterexample in this very session: the `IPD-S406` actor regex broke on a parenthesized
  actor, so prose-shaped contracts in this repo have already bitten once (backlog `wwdm4g`).
- WHAT ABOUT A PLAN WITH NO REVIEW AT ALL? Refusing those would block the legitimate
  author-then-approve path. Probably out of scope, but decide explicitly rather than by omission.
- SHOULD THE SAME GATE APPLY TO `aw specs set approved`? Specs carry an approval attestation too. If
  the answer is yes, the predicate belongs in one shared place, not two.
- DOES THE RUNNER'S `--full-auto` AUTO-APPROVAL PATH NEED THE SAME GUARD? It calls
  `set_plan_approved` after checking `is_plan_review_approved`, so it may already be safe; verify
  rather than assume, and make both paths consume ONE predicate.

WHY THIS IS A RELEASE BLOCKER. The failure is silent, it produces an EXECUTABLE artifact, and the
damage is unbounded: an agent acting on a blanket approval can rebuild shipped subsystems, and the
only thing that stopped it this time was an unrelated gate firing for an unrelated reason.

RELATED. Backlog `gjadwm` (executed-transition gate cannot see a consumed finalize journal),
`wwdm4g` (a parenthesized actor breaks the history-attribution regex), `v880xk` (a stale frozen base
floods scope-drift). Together with this item that is FOUR defects in the lifecycle-gate layer found in
one session, which argues for one coherent review of the gate model rather than four patches.

DISCOVERED by a peer agent auditing plan states (comms fyi `20260831-0126-01`), which reported
`bmh754`; the orchestrator verified independently and found all five.
