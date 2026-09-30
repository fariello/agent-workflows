# Review findings: plan nvsz19

- Subject-Id: nvsz19
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-801 (HIGH, fixed), PR-802 (HIGH, fixed), PR-803 (HIGH, fixed), PR-804 (MEDIUM, fixed), PR-805 (LOW, fixed)

## Round 1

Reviewed at HEAD `fd9e05db` in an isolated review lane. The plan file was already committed and identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming`, exit 0, with a single advisory `IPD-Z602` (size density) BEFORE semantic
review; `--phase review-finalize --agent` still reports `conforming` with the same single advisory after
revision. The plan is `- Kind: child`, so the `IPD-S407` orchestrator row check does not apply.

THE PLAN'S EVIDENCE IS EXCEPTIONALLY GOOD AND I VERIFIED ALL FIFTEEN AUTHORED FINDINGS, SO I RECORD THAT
FIRST. Every one holds. F-01 reproduces exactly (`executed -> reviewed` exits `2` with "refusing to move 1
plan(s) BACKWARDS out of a terminal disposition", nothing written). F-02 reproduces exactly on BOTH spellings:
all four illegal nonterminal edges returned exit `0` with the on-disk status rewritten, under `aw set` and
under `aw ipd set` alike. F-03 and F-09 verify by direct call (the four illegal edges all `ok=False` with
`missing predecessor: backwards transition ...`; the three enumerated edges all `ok=True`). F-04 holds: the
only production call is `check_engine.check_lifecycle_transitions`, and its body really does carry `if
"pending" not in p.parts: continue`. F-05 holds precisely (`reviewed -> superseded`, `approved ->
not-executed`, `draft -> reusable` all answer `unknown target status`). F-10 and F-11 quote their specs
accurately: `2vev8j` Section 4.8 point 2 reads "the transition table must ENUMERATE which backward edges are
legal instead of deriving legality from rank order" and point 3 says to treat an unenumerated edge as "illegal
(fail closed)", and the `ipd-spec` history bullet reads "every other backwards move fails closed" verbatim.
F-12's corpus sweep reproduces to the file (26 files: 19 `executed/`, 5 `superseded/`, 2 `pending/`). F-14 and
F-15 reproduce (dry-run printed `approved → draft (dry-run)` at exit `0`; the agent surface emitted
`"outcome":"clean","exit":0,"verified":true` with the status rewritten). F-07 reproduces EXACTLY, including
the count: with a probe installing the naive delegation, the bare suite returned `3 failed, 3365 passed, 2
skipped` and the three failures are precisely the three the plan names, with the `1 != 2`, `1 != 2`, `1 != 0`
shapes it predicted. All three deferred-row carriers resolve (`t1gbwg` and `4ynlcg` both `open`), and the
`From-Backlog: rrvrwv` item exists and is `graduated`. `aw check release-gates` CONFORMS.

I THEN BUILT THE PROPOSED GATE AND MEASURED IT, WHICH IS WHERE THE THREE SERIOUS FINDINGS COME FROM. All
three are cases where the plan's own instructions, followed literally, ship a regression; none is visible by
reading alone, and all three were found by implementing the design rather than by critiquing its prose. I
installed the gate by WRAPPING `status_set.validate_transition_allowed` in-process rather than patching
tracked source, so the call ordering is the real ordering and no production file was modified at any point.

PR-801 IS A CLAIM STATED BACKWARDS, AND IT MATTERS BECAUSE THE PLAN RELIES ON IT TO JUSTIFY AN OMISSION.
F-06 says plan `-> executed` "is already intercepted upstream and delegated to `aw ipd finalize`, so the gate
must not reintroduce the question", and E-03 refusal (2) rests on that: omit `actor=` and the terminal path is
safe. The interception is DOWNSTREAM. `run_set_command` calls `validate_transition_allowed` in its pre-flight
loop, and the `_plan_executed` comprehension that calls `_delegate_plan_executed_to_finalize` is built only
after that loop returns. I proved it by spying on the function during `aw ipd set executed <approved-plan>`:
the spy recorded `('plans','approved','executed')` BEFORE the finalize delegation emitted its actor refusal.
The consequence is concrete rather than theoretical, because the predicate's terminal-predecessor branch fires
with NO actor at all: with the naive gate installed, `draft -> executed` and `to-review -> executed` returned
exit `1` with a transition message, where HEAD returns exit `2` with the finalize actor message. So one
refusal is silently substituted for another at a different exit code, on the path that carries every plan
completion. I also measured a class the plan never enumerated: `superseded`, `not-executed` and `reusable ->
executed` each returned `1` from the new gate.

PR-802 IS THE MOST CONSEQUENTIAL FINDING, AND IT IS SUBTLE ENOUGH THAT THE PLAN'S OWN DISCRIMINATING TEST
WOULD HAVE CAUGHT IT ONLY BY FAILING. E-04 correctly diagnoses F-07 and then prescribes a remedy that does
not fix it: "when the ONLY reason the predicate refuses is that the SOURCE status is terminal and
`--allow-terminal-reopen` was passed, the new gate stands aside". Keying the carve-out on the FLAG fixes only
the override case. With no flag, the new gate still fires first, so the BARE terminal case refuses at exit `1`
from the new gate instead of exit `2` from the shipped guard, and the shipped guard's message never prints. I
implemented E-04 exactly as worded and measured `0` for the override case (correct) and `1` for the bare case
where E-04's own Expected outcome demands `2`. That is a silent reclassification of a `cannot-run` into a
`findings`, which is the exact change OQ-01 says the plan does not make, and it reddens two of the three tests
E-05 expects to pass unchanged - so the plan would have failed its own E-05 while an executor reasonably
believed they had followed E-04. The fix is to carve out the terminal SOURCE unconditionally and let the
existing guard own the whole class including its flag.

PR-803 IS A HOLE THE PLAN NEVER CONSIDERED, AND THE CORPUS PROVES IT IS LIVE. `read_artifact_record` captures
the `- Status:` token VERBATIM and `_status_rank` is a bare dict lookup, so `validate_transition('APPROVED',
'draft')` returns `ok=True` and an unfolded gate passes the exact edge it exists to refuse. I measured it end
to end: with the naive gate installed, a plan carrying `- Status: APPROVED` moved to `draft` at exit `0` with
the status rewritten, and the same for `REVIEWED` and `Approved`. This is not hypothetical - 25 plans in
`.aw/records/plans/executed/` carry an uppercase status today (18 `EXECUTED`, 7 `DONE`). The plan had the
evidence in hand and did not connect it: its own Project-conventions section quotes the terminal-reopen
guard's case-folding comment, and that comment states the reason and the same count ("25 of 479 plans"). The
guard beside the new gate solved this problem already and calls it "a CORRECTNESS requirement rather than
tidiness"; the new gate needed to copy that, and the plan did not say so.

PR-804 IS THE LIVE-COUNT CONVENTION, AND THIS PLAN IS A CLEAN INSTANCE OF WHY IT EXISTS. F-08 records a
`3246 passed, 2 skipped` baseline and both the Required-tests section and V-06 instruct the executor to compare
against it explicitly. At review HEAD the bare suite is `3368 passed, 2 skipped`, +122 from unrelated work in
one day. An executor comparing literally would have to account for a delta of +122 plus their own tests as
"exactly the tests added", which is impossible, and the cheapest escape from an impossible validation is to
fudge it. Converted to a re-derived property with the baseline captured in E-01. The same drift hit F-12's
check-rule identities: `qo9khm` has since reached `executed/` and left the rule's pending-only scope, so the
live pair is now `vnt9it` and `5poaqh`.

PR-805 is that E-06's eight cases left the two regressions above unfenced. Cases (i) and (j) were added
demanding the `-> executed` path keep its own exit `2` AND a distinguishing fragment of the finalize message
(since the failure mode is one refusal substituted for another), and demanding an uppercase-status plan be
gated identically.

I THEN BUILT THE CORRECTED DESIGN AND MEASURED IT END TO END, so E-04 is now a demonstrated mechanism rather
than a described one, which is what section 3.1's HOW-question standard requires. Skipping a terminal source
unconditionally, skipping a normalized `-> executed` target, and case-folding the source produced: bare
terminal `2` with the shipped message, override terminal `0` with the file relocated, all four illegal
nonterminal edges `1` with AND without `--allow-terminal-reopen`, uppercase `APPROVED`/`REVIEWED -> draft`
`1`, `-> executed` `2` from the finalize delegation, all three enumerated legal backward edges `0`, all three
retirements `0`, all three forward edges `0`, dry-run on an illegal edge `1`, and the agent surface
`"outcome":"findings","exit":1,"rule":"status.invalid_transition"`. Bare suite with that gate installed:
`3368 passed, 2 skipped, 3 warnings` - zero test edits, which confirms E-05's expectation is not merely
hopeful.

THINGS I CHECKED THAT PRODUCED NO FINDING. The `aw plan set` / `aw plans set` non-registration the plan
claims is real (argparse rejects both with `invalid choice`). OQ-01's exit-code split is sound and I left it
resolved: the pre-flight loop genuinely exits `1` and genuinely emits `status.invalid_transition`, and the
`1` versus `2` split maps onto `docs/cli-output-contract.md`'s own definitions. The spec-sync section's
no-amendment conclusion is right and I confirmed the contract is already written in both cited specs, so the
code moves toward the spec. `reusable` is correctly NOT in `_plans_mod.TERMINAL`, so the E-04 carve-out does
not accidentally exempt it, and I verified `reusable -> draft` answers `ok=True` so it stays gated by rank.
The gate's `record_type` keying is necessary as F-13 says: specs really do permit moves that would be
backwards for a plan, and `backlog` really has no transition table.

The plan's honesty about its own premise having moved is the reason this review had a clear target, and its
stop condition is well judged - though I note the (a) cases still measure exit `0` at review HEAD, so the
stop does not fire and the defect is live.

Bare suite at review HEAD: `3368 passed, 2 skipped, 3 warnings in 68.24s`. This review changed only the plan
and this review record; no production file was modified at any point, and all probes ran as in-process
wrappers plus a throwaway git repo under a gitignored `tmp/` path inside the lane.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | IN-SCOPE | Rubric A (correctness), D (anti-regression) | `status_set.run_set_command`: the `validate_transition_allowed` pre-flight loop precedes the `_plan_executed` comprehension calling `_delegate_plan_executed_to_finalize`. Spy measurement during `aw ipd set executed <approved-plan>` recorded `('plans','approved','executed')` before the delegation's actor refusal | THE FINALIZE DELEGATION IS DOWNSTREAM OF THE GATE SITE, NOT UPSTREAM, so F-06's justification for omitting `actor=` is inverted and insufficient. With no actor the predicate still refuses `draft -> executed` and `to-review -> executed` on its terminal-predecessor branch, so a naive gate converts the finalize path's exit `2` actor refusal into an exit `1` transition refusal - measured. Also measured: `superseded`/`not-executed`/`reusable -> executed` each refused at `1`, a class the plan never enumerated. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-06 corrected and split; added F-06b with the spy and probe measurements. E-03 gains refusal (4) requiring an explicit skip of a normalized `-> executed` target with the ordering reason; E-04 repeats it; E-02 must now record the `-> executed` target class and its owner separately; V-03 and V-04 demand the evidence, V-04 via a new variant (d); E-06 gains case (i). |
| PR-802 | HIGH | IN-SCOPE | Rubric A (correctness), E (verification), G (executability) | E-04 as authored: "the SOURCE status is terminal **and** `--allow-terminal-reopen` was passed". Probe implementing that literal condition measured bare terminal = exit `1` against E-04's own required `2`; override = `0` | E-04'S REMEDY DOES NOT FIX THE DEFECT IT DIAGNOSES. Keying the carve-out on the FLAG leaves the BARE terminal case refusing at `1` from the new gate instead of `2` from the shipped guard, whose message never prints - silently reclassifying a `cannot-run` as a `findings`, contradicting OQ-01's claim that the plan reclassifies neither, and reddening two of the three tests E-05 requires to pass UNCHANGED. An executor following E-04 exactly would fail E-05 while believing they had complied. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-04 rewritten: the condition is the terminal SOURCE unconditionally, with the measurement and the reason stated, and "terminal" computed case-folded from a set DERIVED from `_plans_mod.TERMINAL`; notes `reusable` is deliberately outside it. E-05 records that zero edits is measured achievable and names this as the first error to look for; V-04 (a) is flagged as the discriminating case and must assert the message fragment as well as the code. Added F-07b recording the corrected shape measured end to end. |
| PR-803 | HIGH | IN-SCOPE | Rubric A (correctness), B (default-deny), D | `validate_transition('APPROVED','draft')`, `('REVIEWED','draft')`, `('DONE','approved')` all return `ok=True` (`_status_rank` is a bare dict lookup; `read_artifact_record` stores the token verbatim). Probe with an unfolded gate: a plan at `- Status: APPROVED` moved to `draft` at exit `0`. Corpus: 18 `EXECUTED` + 7 `DONE` = 25 | AN UPPERCASE `- Status:` WALKS STRAIGHT THROUGH AN UNFOLDED GATE, so the gate fails OPEN on 25 live plans. The plan never mentions case, though its own conventions section quotes the neighbouring terminal-reopen guard's case-folding comment, which states both the reason and the same count and calls it "a CORRECTNESS requirement rather than tidiness". | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-06c with the measurements and the live count. E-03 gains refusal (5) requiring the source be case-folded through `normalize_target_status`; E-04 requires the same for its terminal classification; E-02 must record the uppercase class and count it; V-03 requires the uppercase refusal as the discriminating evidence; E-06 gains case (j). |
| PR-804 | MEDIUM | IN-SCOPE | Rubric G (live-artifact success criteria) | F-08's `3246 passed, 2 skipped`; re-measured at review HEAD `fd9e05db`: `3368 passed, 2 skipped` (+122 in one day). `aw check plans --json` now reports `vnt9it` and `5poaqh`, not `qo9khm` (since moved to `executed/`) | A LIVE COUNT IS PINNED AS AN ACCEPTANCE BAR. Required-tests and V-06 both instruct comparing the after-count against the pasted `3246`; the real baseline has already drifted +122, so a correct execution must account for an impossible delta and the cheapest escape from an impossible validation is to fudge it. F-12's check-rule identities drifted the same way. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 must now RE-DERIVE and paste the bare-suite baseline with its HEAD commit before changing anything; Required-tests and V-06 compare against THAT rather than any constant in the plan, and both state the number has drifted twice. F-08 carries both measurements; F-12 records that its identities and count are live context, not a bar. |
| PR-805 | LOW | UNDER-SCOPE | Rubric E (testing) | E-06 cases (a) through (h) as authored; the regressions measured in PR-801 and PR-802 fall outside all eight | THE TEST FENCE MISSES BOTH MEASURED REGRESSIONS. Nothing in the eight cases would catch the `-> executed` path's exit code changing from `2` to `1`, nor an uppercase-status plan passing at `0`, so both could ship green. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 gains case (i) (`-> executed` keeps exit `2` AND a distinguishing fragment of the finalize message, from all four nonterminal sources) and case (j) (uppercase `- Status:` gated identically, file byte-identical). Counts updated to ten in E-06, Required tests and V-06. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-802: should the terminal carve-out be keyed on the terminal SOURCE, or should the new gate own the terminal class and take over the `--allow-terminal-reopen` flag itself? | KEY IT ON THE TERMINAL SOURCE UNCONDITIONALLY and leave the entire class to the shipped guard. | Have the new gate own the terminal class and consult the flag itself: rejected. It would duplicate the flag check, the refusal message and the exit code in a second place, desyncing from `setterguard 4bc1nd`'s guard, and it changes the exit code of a shipped refusal that three tests pin - the precise harm PR-802 reports. Rejected also on the repository's stated no-second-copy principle, which the plan itself invokes for `_LEGAL_BACKWARD_EDGES`. | The existing guard in `run_set_command` already owns the class with its own exit `2`, its own message and its own flag recorded into the artifact; measured probe results `2` (bare) and `0` (override) with zero test edits under the chosen shape, versus `1` (bare) under the alternative | yes |
| D-2 | PR-801: should the gate skip a normalized `-> executed` target, or should the finalize delegation be MOVED above the pre-flight loop so the plan's original assumption becomes true? | SKIP THE TARGET in the new gate. | Reorder `run_set_command` to hoist the delegation above the pre-flight validation loop: rejected as out of scope and materially riskier. That loop is the "Refusing before making changes" all-or-nothing batch contract, so hoisting a branch above it changes when validation happens for every artifact type, not just plans, to fix one plan-only gate. The plan declares three Scope-Paths and a one-branch change; a control-flow reorder is a different plan. | `status_set.run_set_command`'s ordering (pre-flight loop, then `_plan_executed`, then the terminal guard, then `is_dry_run`); the plan's own Scope check committing to "one delegation branch in one function" | yes |
| D-3 | PR-803: case-fold inside the new gate, or fix `read_artifact_record` to normalize the status it stores? | CASE-FOLD AT THE GATE. | Normalize in `read_artifact_record`: rejected, that is a shared reader whose verbatim capture other consumers may depend on (the terminal-reopen guard explicitly folds at its own point of use rather than asking the reader to change), so altering it is a wide blast radius reached from a narrow bug. Rejected also because it would silently change what `rec.status` means for every artifact type. | The shipped terminal-reopen guard case-folds AT THE GUARD and records why, establishing the in-repo precedent; `read_artifact_record` stores `status_match.group(1)` unmodified | yes |
| D-4 | Should any of the three HIGH findings be escalated into the plan as a `- Blocking: yes` open question per Step 4's gate threshold? | NO ESCALATION NEEDED; all three are FIXED, not deferred or open. | Escalate anyway for visibility: rejected, the threshold rule governs a finding left OPEN or DEFERRED at or above `HIGH`, and each of these was repaired in place with its corrected instruction and its fence. Adding a blocking question for a fixed finding would refuse the plan at every lint checkpoint for a defect that no longer exists. | `review_findings_gate.block_at` default `HIGH` applies to OPEN/DEFERRED findings; all five findings carry Decision `FIXED`; `aw ipd lint --phase review-finalize` reports `conforming` after revision | yes |
| D-5 | OQ-01 is `- Status: resolved` with `- Owner: none` and was resolved by the author from evidence. Re-open it, given PR-802 showed a naive implementation WOULD have changed the exit contract? | LEAVE IT RESOLVED. | Re-open as blocking: rejected. The question asks which code the NEW refusal should use, and `1` remains correct and remains evidenced by the pre-flight loop's existing behavior. PR-802 is not a dispute about that answer; it is a defect in the mechanism that was supposed to preserve the OTHER class's `2`, and fixing E-04 restores exactly the split OQ-01 describes. Re-opening would block the plan over a decision that measurement confirms. | The pre-flight loop's existing exit `1` and `status.invalid_transition` rule; measured corrected shape yielding `1` for the new class and `2` for the terminal class simultaneously | yes |
