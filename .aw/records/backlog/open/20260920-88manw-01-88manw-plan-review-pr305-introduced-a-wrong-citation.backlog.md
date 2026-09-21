- Id: 88manw
- Status: open
- Blocks-Release: next
- Set: 88manw
- Priority: low
- Work-Kind: bug
- Summary: plan si24ia review finding PR-305 rejected a correct spec section citation and substituted a wrong one, and the 25kzda 0..10 retry bound is stated in four different sections

## Workflow history
- 2026-09-20 created (aw backlog): plan si24ia review finding PR-305 rejected a correct spec section citation and substituted a wrong one, and the 25kzda 0..10 retry bound is stated in four different sections

MEASURED 2026-09-20 at HEAD 96e93f8c by research survey vkub9o (plan si24ia), which had to adjudicate between its own plan and that plan review.

WHAT IS WRONG, IN TWO PARTS.

PART 1: THE REVIEW CORRECTION WAS ITSELF WRONG. Plan si24ia cited "25kzda 2.1 retry budget" four times. Its /plan-review finding PR-305 declared that citation wrong on the grounds that section 2.1 is "Command grammar", and named section 1.1 plus line 586 as the correct anchors. Measured:
    $ grep -nE "^#{2,4} " <25kzda> | awk -F: "\$1<=211" | tail -3
    162:### 1.4 Resolution of the required revisions
    172:## 2. Selector resolution and mixed-type policy
    174:### 2.1 Command grammar
    $ sed -n "211p" <25kzda>
    - `--retry-budget` is an integer from 0 through 10 inclusive. ...
Line 211 IS inside section 2.1. The PLAN was right and the REVIEW was wrong. Backlog f1sw71 own text also cites "25kzda section 2.1 (the retry budget)", agreeing with the plan.

PART 2: THE UNDERLYING SPEC STATES ONE BOUND IN FOUR PLACES, which is why all three parties could disagree in good faith. The 0..10 retry-budget bound appears at:
    line  167 -> ### 1.4 Resolution of the required revisions
    line  211 -> ### 2.1 Command grammar
    line  691 -> ### 4.1 Message and recovery conventions
    line 1088 -> ### 5.5 Retry policy
and agent_workflows/run_recovery.py:64 cites it as "spec 2.1 0..10 bound".

WHY THIS IS FILED AS A BUG RATHER THAN A CHORE. The user-perceptible impact is on a reader or agent who follows a citation: the plan review finding is DURABLE, tracked, and wrong, so the next reader who trusts it is sent to the wrong section and may propagate the error, which is precisely what happened once already in this chain. It is low priority because the blast radius is a documentation citation rather than behavior, and it is not a code defect. Per AGENTS.md every live bug gates the next release, so - Blocks-Release: next is set; if the maintainer judges this a `chore` instead, clear the gate with `--blocks-release -` and reclassify.

WHAT TO FIX. (a) Record in plan si24ia workflow history that PR-305 was itself incorrect (si24ia is already executed, so per AGENTS.md this needs a corrective note rather than an in-place edit of the findings table). (b) Decide which section of 25kzda is the CANONICAL home of the retry-budget bound and make the other three cross-reference it, so the code comment has one true anchor. (b) is the substantive half.

WORTH NOTING. Survey vkub9o treats this as its strongest single piece of evidence on the f1sw71 question, and it points at the CHEAP answer: a requirement PARSER would not have prevented it (the text carries no requirement id at any of the four sites), while a stable ADDRESSING CONVENTION would. It is an addressing failure, not a coverage-tracking failure.
