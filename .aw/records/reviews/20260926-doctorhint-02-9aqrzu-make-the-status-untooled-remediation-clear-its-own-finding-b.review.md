# Review: Make the status-untooled remediation clear its own finding by writing a genuine transition record

- Subject-Id: 9aqrzu
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `25f790db` (the plan was authored at `61ef21d8`, an ancestor). The target plan was
committed and unchanged, so the pre-review snapshot was correctly skipped per Step 1. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE review and
`--phase review-finalize` reported `conforming` after the edits, including the added E-05/V-05.
`aw check plans --agent` reports 2 findings tree-wide and NONE against this plan;
`check_engine.evaluate_durable_carrier` returns `[]`.

THE DIAGNOSIS IS CORRECT AND I REPRODUCED ALL OF IT RATHER THAN READING IT. In fresh scratch repos:
a committed `to-review` plan hand-edited to `reviewed` and staged raises `check.status-untooled`;
`aw set reviewed <id6> --yes --no-commit` prints `unchanged` and writes NOTHING, leaving the finding
(F-1); with `--message fix` it writes `- <date> same-status (aw set): fix` and the finding persists
(F-2); a hand-edit to `approved` writes `- Approval: <date>, recorded via aw ipd set: status
unchanged (approved)` (F-3). I also proved the PREMISE the whole plan rests on, which is the thing
most worth checking in a plan like this: injecting a genuine `- <date> reviewed (aw set): status set
to reviewed` line into the staged plan makes `check_status_untooled` return `[]`. So option 2 does
clear the finding.

THE FINDING THAT MATTERS MOST IS PR-1101, AND IT WOULD HAVE SHIPPED A REGRESSION THE REPOSITORY
ALREADY PAID TO FIX. E-01 told the executor to set `is_same_status = False` immediately after it is
computed. Read against the function, that is the one change that must not be made:
`is_dup = same_status_message_is_duplicate(...) if is_same_status else False` is evaluated MUCH
later, and `should_write_history = not (is_same_status and is_dup)`. Flipping the flag at the top
therefore makes `is_dup` unconditionally `False` and the duplicate suppression UNREACHABLE on exactly
the new path. Measured: two runs of the fix path produce two byte-identical
`- 2026-09-27 reviewed (aw set): status set to reviewed` records. That is the accumulating-history
defect plans `1i300e` (E-02/E-03) and `vhbvwz` exist to prevent, and `same_status_message_is_duplicate`'s
own docstring names idempotent re-assertion as the case it protects. The remedy is small and I
verified it works: leave `is_same_status` TRUE, carry a separate `untooled_transition` flag, and widen
`_write_history_anyway` to `(bool(_explicit_message) or untooled_transition) and not is_dup`. Driven
at review, the first run then writes the real token (finding clears) and the second identical run is
suppressed (`same_status_message_is_duplicate(..., "reviewed", <today>, "status set to reviewed")` is
`True`), while a genuinely different message still records (`False`). The plan's own instruction to
neutralize the early return is also withdrawn for the same reason: `_write_history_anyway` is already
dedup-aware, so widening it keeps ONE dedup decision instead of adding a second escape hatch.

THE SECOND WOULD HAVE FAILED THE SUITE WITH THE CAUSE TWO ITEMS BEHIND. E-03 reworded
`doctor.build_remediation`'s `status-untooled` branch, and
`tests/test_doctor.py::DoctorRemediationTests::test_remediation_status_untooled` asserts
`assertIn("revert the hand edit", rem.detailed_fix)`. That file was NOT in `- Scope-Paths:`, so the
reword breaks a pinned test and the executor would meet it at E-04's bare run. The path is now
declared and E-03 carries the instruction, including that `assertIsNone(rem.command)` must be
RETAINED, because 6k7xot's decision to make the branch advisory is not being reversed here.

E-03's CONDITIONAL WAS ALSO ALREADY DECIDABLE, AND LEAVING IT OPEN INVITED THE WRONG OUTCOME. It said
to edit the doctor text only "if" it implies reverting is required, else `--scope-ack` `doctor.py`.
Both strings make reverting required, verbatim: `summary_fix` is "revert the hand edit and apply
status change via '<cmd>' ...", and `detailed_fix` is "... revert the hand edit so the status returns
to its previous value, then apply the change via '<cmd>' ...". 6k7xot's own E-04 instructed exactly
that wording, so it is deliberate there and becomes false here. Left conditional, an executor could
have acked `doctor.py` and shipped a tool that tells operators to revert a hand edit they no longer
need to revert. I resolved it: the edit is required, and the gate now says `doctor.py` must not be
acked. Separately I checked the CHECKER's own drift detail and it needs no change, because it never
mentioned reverting ("apply it via `aw set <status> <id6>` ... so the transition is attributed") and
simply becomes true once E-01 lands.

THE PLAN CONTRADICTED ITSELF ABOUT BEING BLOCKED, WHICH IS A GATE DEFECT RATHER THAN A CODE ONE. The
approval gate opened with "THIS PLAN IS BLOCKED ON ONE HUMAN DECISION AND MUST NOT BE APPROVED OR
EXECUTED UNTIL IT IS ANSWERED" and cited "`OQ-01` (`- Blocking: yes`)", while OQ-01 carries
`- Blocking: no`, `- Status: resolved`, and a recorded maintainer answer choosing option 2. A human
reading the gate would refuse to approve a plan whose blocker is answered, and an automated consumer
reading the FIELD would proceed: the two disagree. I corrected the gate (the fields are right) and
retained the genuinely conditional half, that a reversal to (1) or (3) retires this plan.

ONE THING I SURFACED RATHER THAN RESOLVED, BECAUSE IT IS THE MAINTAINER'S TO CONFIRM. Backlog
`mpghjn` RECOMMENDED options (1) or (3) and described (2) as needing "a git read the setter does not
do". This plan implements (2), on the strength of a maintainer answer recorded only in OQ-01's prose.
I did not treat that as suspect (the plan says the maintainer was asked directly and confirmed), but I
also did not let it stay invisible: the gate now states the divergence and says that if the maintainer
does not recall making that choice, the plan should not be approved and the question should be
re-asked, because the entire plan IS that answer.

TWO SMALLER CORRECTIONS OF FACT. F-1's "writes NOTHING" is status-dependent in a way the plan did not
say: a hand-edit to a status whose DIRECTORY differs (measured with `not-executed`) makes
`path_changed` true, so a `same-status` record IS written even with no `--message` and the file
relocates, while the finding still persists. E-02 gained that as case (e), and it is worth a case
because it is the shape where the current behavior looks closest to working. And the plan asserted
nothing about the OTHER caller of `apply_status_change`: `ipd_lifecycle` calls it inside a COORDINATOR
WORKTREE, whose HEAD is not the caller's HEAD, so a `git show HEAD:` added to that function deserves an
explicit argument that it cannot fire there. It cannot (finalize's target is `executed` against a
pre-terminal on-disk status, so `is_same_status` is False; and a terminal status is refused earlier by
the pre-transition gate), but E-05 now requires that argument and a narrowed test run rather than
leaving it to be assumed.

WHAT I DID NOT CHANGE. Option 2 as the approach, OQ-01's resolution and its `- Blocking: no` /
`- Status: resolved` fields (they were correct; the gate was wrong), the decision not to relax
`check_engine._has_matching_history_line`, the exclusion of non-plan record types, the `medium`
priority, the carrier on `mpghjn`, and the outcomes-only test posture. I also left
`check_status_untooled`'s docstring alone and said so in spec-sync: the accepted efficacy ceiling it
records is NOT moved by this change, which the plan's own conventions section already got right.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-1101 | HIGH | IN-SCOPE | A. Correctness / D. Anti-regression (re-opening a fixed defect) | `is_dup = same_status_message_is_duplicate(...) if is_same_status else False` and `should_write_history = not (is_same_status and is_dup)`, both evaluated far below where E-01 said to flip the flag. Driven at review: two fix-path runs produced two byte-identical `- 2026-09-27 reviewed (aw set): status set to reviewed` records. With the dedup reachable, the predicate returns `True` for the second identical write and `False` for a different message | **E-01's `is_same_status = False` MAKES THE DUPLICATE SUPPRESSION UNREACHABLE, re-opening the accumulating-history defect `1i300e` and `vhbvwz` fixed.** The flag is read much later as the gate on the dedup call, so setting it False at the top silently disables dedup on exactly the new path. Every re-run before the commit lands appends another identical record. The plan's companion instruction to neutralize the early return compounds it, since `_write_history_anyway` is ALREADY dedup-aware and a second escape hatch would bypass the one decision point. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 rewritten: keep `is_same_status` TRUE, carry a separate `untooled_transition` flag, set only `status_tag`/`default_message`, and widen `_write_history_anyway` to `(bool(_explicit_message) or untooled_transition) and not is_dup`. The rejected shape is named and forbidden, with the measurement. Added F-5, a new E-02 case (d) asserting the record COUNT after a second run, a V-01 requirement to prove `is_same_status` is never reassigned, and a second stop condition forbidding a fallback to the rejected shape. |
| PR-1102 | HIGH | UNDER-SCOPE | E. Testing / G (an undeclared path the change must touch) | `tests/test_doctor.py::DoctorRemediationTests::test_remediation_status_untooled` asserts `self.assertIn("revert the hand edit", rem.detailed_fix)`; `grep -rn "revert the hand edit" agent_workflows/ tests/` -> two `doctor.py` sites and that one test; the plan's `- Scope-Paths:` omitted `tests/test_doctor.py` | **E-03's REWORD BREAKS A PINNED TEST IN A FILE THE PLAN DID NOT DECLARE.** The executor would have reworded `doctor.py`, then met an unexplained failure at E-04's bare suite run, two items later, with no instruction covering it and no declared path permitting the fix. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `tests/test_doctor.py` added to `- Scope-Paths:` and to the fence (scoped to that one test). E-03 now instructs updating the wording assertion while RETAINING `assertIsNone(rem.command)` (6k7xot's advisory decision is not reversed) and touching no other test. V-03 requires the test diff, and states that a green run without it means the reword did not happen. Added F-6. |
| PR-1103 | MEDIUM | IN-SCOPE | A. Correctness (a decidable conditional left open) | `summary_fix` verbatim: "revert the hand edit and apply status change via '<cmd>' so an attributed history entry is appended"; `detailed_fix` verbatim: "... revert the hand edit so the status returns to its previous value, then apply the change via '<cmd>' ..."; 6k7xot E-04's own instruction to write that two-step recovery | **E-03's "EDIT ONLY IF IT IMPLIES REVERT IS REQUIRED" IS ALREADY ANSWERED, AND THE FALLBACK WAS TO SHIP A CONTRADICTION.** Both strings make reverting required. Left conditional, an executor could reasonably read them as "one valid option", `--scope-ack` `doctor.py`, and ship a tool instructing operators to revert a hand edit the fix makes unnecessary. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 states the conditional is resolved, quotes both strings, cites 6k7xot's E-04 as why the wording is deliberate there, and makes the edit mandatory. The gate says `doctor.py` must NOT be acked. V-03's "why no change was needed" alternative is removed. Also checked and recorded: the CHECKER's own drift detail never mentioned reverting and needs no edit. Added F-7. |
| PR-1104 | MEDIUM | IN-SCOPE | G. Plan executability (a gate contradicting its own plan) | The gate: "THIS PLAN IS BLOCKED ON ONE HUMAN DECISION AND MUST NOT BE APPROVED OR EXECUTED UNTIL IT IS ANSWERED. `OQ-01` (`- Blocking: yes`)". OQ-01: `- Blocking: no`, `- Status: resolved`, maintainer chose option 2 on 2026-09-26 | **THE GATE CLAIMS THE PLAN IS BLOCKED ON A QUESTION THAT IS ANSWERED, AND MISSTATES THAT QUESTION'S OWN FLAG.** A human reading the gate refuses to approve; an automated consumer reading the field proceeds. The two disagree about whether this plan may be executed, which is the most consequential thing a gate says. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The stale block notice is withdrawn and replaced with a note recording that it contradicted OQ-01's fields and why the fields are the correct side. The genuinely conditional half is retained: a reversal to (1) or (3) retires the plan as superseded. Added F-8. |
| PR-1105 | MEDIUM | UNDER-SCOPE | C. Architecture / D. Anti-regression (an unexamined second caller) | `ipd_lifecycle` calls `_ss.apply_status_change(wt_rec, "executed", coord.path, ns)` inside a coordinator worktree ("mutations happen in a coordinator worktree"); the pre-transition gate refuses a terminal status first ("carries Status ... which is already terminal; there is nothing to retire"); `status_set` and `check_engine` do not import each other at module level | **THE PLAN ADDS A `git show HEAD:` TO A FUNCTION FINALIZE CALLS IN A WORKTREE WHOSE HEAD IS NOT THE CALLER'S, AND SAYS NOTHING ABOUT IT.** The branch does not in fact fire there, but the plan asserted no argument for that, so an executor had no basis to be confident and a later reader had nothing to check. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added E-05/V-05 requiring the two-part argument with citations (finalize's target versus the on-disk status; the terminal refusal) plus a narrowed run of the setter and lifecycle test modules, and the module-level import check that also discharges the gate's import-cycle stop condition (measured: no cycle, and `status_set` already imports `check_engine` locally elsewhere). `Highest E allocated` 04 -> 05. |
| PR-1106 | LOW | IN-SCOPE | A. Correctness (an incomplete symptom description) | Scratch repo: hand-edit `to-review` -> `not-executed`, stage, `aw set not-executed <id6> --yes --no-commit` -> reports `unchanged`, file MOVED to `not-executed/`, history gained `- <date> same-status (aw set): status unchanged (not-executed)`, drift still `['check.status-untooled']`. `record_placement.target_subdir` maps every pre-terminal status to `pending` | **F-1's "WRITES NOTHING" IS TRUE ONLY WHEN THE TARGET DIRECTORY DOES NOT CHANGE.** For a terminal target, `path_changed` is true, so a `same-status` record IS written with no `--message` and the file relocates, while the finding still persists. An executor testing only the pending-to-pending shape would not cover the case where today's behavior looks closest to correct. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-9 with the measurement and E-02 case (e) (hand-edit to `not-executed`, assert the finding clears and the file lands in `not-executed/`), listed among the cases that must fail pre-change. V-02 requires the resulting path. |
| PR-1107 | LOW | IN-SCOPE | A. Correctness / F (a divergence from the source item, unstated) | `mpghjn`'s "Candidate fixes": "RECOMMENDATION: (1) or (3)", and of (2): "it needs a way to know the previous value, which is a git read the setter does not do". OQ-01 records the maintainer choosing (2) | **THE PLAN IMPLEMENTS THE OPTION ITS OWN SOURCE ITEM RECOMMENDED AGAINST, AND ONLY THE PLAN SAYS SO.** The maintainer answer is recorded in OQ-01 prose alone, so a human approving later cannot see that they are overriding the item's recommendation. Not a defect in the choice, which is well argued, but the approving human should be asked to confirm it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate gains a paragraph stating the divergence, the cost of (2) (exactly that git read, on the same-status plan path only), and the instruction NOT to approve but to re-ask if the maintainer does not recall the choice. A review note on OQ-01 records the same. Added F-10. |
| PR-1108 | LOW | IN-SCOPE | G. Plan executability (thin fence; stale-docstring silence) | Fence as authored: "the Scope-Paths above" with no per-file surface and no expected-unmodified list; `apply_status_change`'s docstring describes the same-status behavior with no untooled exception; `check_status_untooled`'s docstring records the efficacy ceiling | **THE FENCE NAMED NO SURFACES AND NO EXPECTED-UNMODIFIED PATHS, so finalize reconciliation had little to reconcile against, and two docstrings become stale-by-omission with no instruction either way.** The second matters because one of them (`check_status_untooled`'s ceiling) must NOT be edited, and a diligent executor might "helpfully" update it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fence now names the in-scope surface per file and four expected-unmodified surfaces (`_has_matching_history_line`, `check_status_untooled` including its drift detail, `same_status_message_is_duplicate` whose behavior is RELIED ON, and `ipd_lifecycle`). Spec sync states which docstring is in scope to update and which must be left alone, and that the efficacy ceiling is not moved. The honesty rule names idempotence as the easiest-to-fake claim. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-1101: how should the untooled path write history without disabling the dedup? | KEEP `is_same_status` TRUE, carry a separate flag, and widen `_write_history_anyway` to include it while retaining `and not is_dup`. | (a) `is_same_status = False` as authored: rejected on measurement, it makes `is_dup` unconditionally False and duplicates history on every re-run, re-opening `1i300e`/`vhbvwz`. (b) Flip the flag AND add a dedup call on the new path: rejected, two dedup decisions for one question is the drift the single-source principle forbids, and the existing call already handles it. (c) Neutralize the early return as the plan also said: rejected, `_write_history_anyway` is already dedup-aware, so a separate escape hatch would bypass the one decision point. | The `is_dup` / `should_write_history` expressions read in place; the duplicate records measured from the rejected shape; `same_status_message_is_duplicate` returning True for the repeat and False for a new message | yes |
| D-2 | PR-1103: E-03's conditional. Resolve it in review, or leave the executor to judge? | RESOLVE IT: the edit is required, and forbid acking `doctor.py`. | (a) Leave it conditional: rejected, both strings were read and both require reverting, so the condition is not genuinely open; leaving it invited an ack that ships a tool contradicting its own fixed behavior. (b) Also reword the checker's drift detail for symmetry: rejected, it never mentioned reverting and becomes true once E-01 lands, so editing it would be unnecessary scope in a file the plan excludes. | Both strings quoted verbatim from `build_remediation`; 6k7xot E-04's instruction; the checker's detail string read and found already correct | yes |
| D-3 | PR-1104: the gate says blocked, OQ-01 says resolved. Which is authoritative? | OQ-01's FIELDS; correct the gate. | (a) Trust the gate and set `- Blocking: yes`: rejected, that would re-block a plan whose question carries a recorded maintainer answer, and would forge a blocking state the author did not intend. (b) Leave both: rejected outright, the contradiction is about whether the plan may be executed and is read differently by humans and tooling. | OQ-01's `- Blocking: no` / `- Status: resolved` and its maintainer-answer text; the gate's own citation of a flag value the file does not contain | yes |
| D-4 | PR-1107: the plan implements the option `mpghjn` recommended against. Accept, or send it back? | ACCEPT, and surface the divergence in the gate with an instruction to re-ask if the maintainer does not recall the choice. | (a) Refuse and demand a fresh maintainer answer before review completes: rejected, the plan states the maintainer was asked directly and confirmed, and treating a recorded answer as suspect without evidence would be a reviewer overriding an attested decision. (b) Say nothing: rejected, the two documents disagree in the permanent record and the approving human is entitled to see that they are overriding the item's own recommendation. (c) Decide the merits myself: rejected, the choice among (1), (2) and (3) is a risk-appetite call about the checker's efficacy ceiling, which is the maintainer's. | `mpghjn`'s recommendation text; OQ-01's resolution; `_has_matching_history_line`'s docstring recording the ceiling option (1) would lower | yes |

### Deferred and open

- (none). All eight findings are FIXED in place. Two were HIGH and both were genuine execution
  hazards rather than polish: PR-1101 would have re-opened a defect the repository had already fixed,
  and PR-1102 would have failed the suite with its cause two items behind. No finding was left OPEN or
  DEFERRED, so no escalation to a `- Blocking: yes` question is owed. OQ-01 was already resolved and I
  deliberately did NOT re-open it: its fields were correct and the gate was wrong. The one thing I
  declined to decide is recorded as D-4, the choice among the three candidate fixes, which is the
  maintainer's risk-appetite call about the checker's efficacy ceiling; it is now stated in the
  approval gate so a human confirms the divergence from `mpghjn`'s recommendation before signing.
