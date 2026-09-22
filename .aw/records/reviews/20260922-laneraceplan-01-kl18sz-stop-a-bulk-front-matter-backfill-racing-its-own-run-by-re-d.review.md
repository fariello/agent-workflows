# Review findings: plan kl18sz

- Subject-Id: kl18sz
- Subject-Type: ipd
- Reviewed-At: 2026-09-22
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `fbf5f85c` in an isolated review lane. The plan was committed and unmodified, so no
pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author` exited `1` on `IPD-Q501`
because OQ-01 is `Blocking: yes` and open; that is CORRECT here and deliberately remains, so the plan still
reports that gate at `review-finalize`. `aw check` additionally reported `check.ipd-uncarried-obligation` at
`error`, which the IPD linter does not see; it is now clear and the tree total fell 57 -> 56.

THE DIAGNOSIS IS EXCELLENT AND THE PLAN'S SELF-CORRECTION IS EXEMPLARY, which is worth stating first because
the findings below are numerous and all of them are about implementability rather than about a wrong premise.
Verified: the orthogonality argument holds (the lane adds `- Work-Kind:`/`- Priority:` while `main` rewrote
`- Status:` and moved the file, so the two sides genuinely do not disagree); the archetype claim verifies with
`8u6770`, `lc4unl` and `lkexaw` all present in `pending/` and backlog `21fykf` `graduated` carrying the same
`Blocks-Release: next`, so the gate handoff is provable; the integration seam really is the shared
`runner_shared.integrate_lane_branch`, so declaring only `runner_shared.py` is right for E-01 to E-04; and the
plan RETRACTS its own earlier "silent merge revert" claim after the maintainer challenged it and measurement
disproved it, restating the hazard accurately as resolver ergonomics. That retraction is the kind of honesty
this repository's conventions ask for and it is rare enough to name.

TWO FINDINGS MAKE PARTS OF THE PLAN UNEXECUTABLE AS WRITTEN.

First (PR-001), the mandatory replay has no source. V-01 and the Required tests section demand reconstructing
`8u6770`'s 13-file conflict set on the stated ground that "the lane branch and the merge base are both still
resolvable". Measured:

```text
git branch -a | wc -l            -> 125 lane branches
git branch -a | grep 8u6770      -> (nothing)
git branch -a | grep lc4unl      -> aw/lane/lc4unl, aw/lane/lc4unl_attempt2
git log -1 aw/lane/lc4unl        -> b1223b4f records(lc4unl): apply Ruling 2 ...
git diff --name-only main...aw/lane/lc4unl -> 4 paths, all under .aw/records/
                                    (2 backlog/open/*.backlog.md, 2 plans/pending/*.ipd.md)
```

So the named lane is gone and the 13-file measurement cannot be reproduced from it. `lc4unl` is the sibling
F-6 already identifies as hitting the same class in the same run, so it is a legitimate substitute, but it is
4 paths and not 13 and it spans two record TYPES. The plan now re-points at it, requires the size difference
to be stated, and permits a clearly labelled synthetic fallback while failing V-01 for a synthetic fixture
presented as the real replay.

Second (PR-002), E-03 contradicts an approved spec, and the plan cited the wrong authority. Its spec-sync
section named "the spec text that assigns conflict resolution to a human/serial ordering", but that sentence
is a DOCSTRING in `runner_shared.integrate_lane_branch` ("conflict DETECTION is the gate's job; conflict
RESOLUTION is a human/serial ordering"). The governing rule is spec `25kzda` Section 2.1, and it is a flat
prohibition rather than an allocation of responsibility:

```text
"The ladder applies ONLY to that transient dirty-overlap refusal. It never applies to a genuine merge
 conflict, a stale base, a non-passing combined revalidation, or a scope violation, none of which
 repetition fixes. ... no rung integrates over a contaminated base, none stashes, resets, or cleans
 another writer's work, and none reclassifies a failure as a deferral."
```

Its 2026-09-21 amendment note repeats that scope and states "No rule changed". `8u6770` hit a genuine merge
conflict, so E-03 introduces automated handling of the one class the spec says gets none, and the plan
declared no spec path at all. The obligation is now stated with the quotes, three concrete requirements (declare
the path first, write a NARROW carve-out, keep `merge-refused`'s meaning), and V-03 fails without the diff
regardless of how well the code works. The argument FOR the carve-out is recorded too, because it is a good
one: the prohibition's own stated reason is that repetition does not fix these classes, and re-derivation is
not repetition.

THE CLASSIFIER'S SAFETY TEST WAS ALSO TOO WEAK (PR-004), and this is the finding with the worst failure mode.
"Front-matter keys ORTHOGONAL to `- Status:`" is a deny-list of exactly one key, so it admits every other
field, including several this repository treats as attestations or gates: `- Readiness:` (which the
conventions call a forged attestation when hand-written, and which the auto-approve predicate reads FIRST),
`- Approval:`, `- Blocks-Release:` (a release gate), `- Item-Dependencies:` (queue ordering) and
`- Id:`/`- Set:`/`- Order:` (identity). An integration able to write any of those automatically would be
strictly worse than the conflict it resolves. E-01 now requires an explicit ALLOW-list (the measured case
needs exactly `- Work-Kind:` and `- Priority:`) and E-05 gains a second control that fails if the list is ever
widened to a gate or attestation key.

TWO SMALLER CORRECTNESS POINTS. The shape was defined over all of `.aw/records/` although only plan front
matter was measured (PR-005), and `lc4unl`'s own diff proves the concern is live by including two
`.backlog.md` records beside two plans; backlog, spec, release and review records each carry a different
status enum and lifecycle layout, so the classifier must be type-aware and answer UNKNOWN for anything
unmeasured. And a re-derived integration had no distinct reported outcome (PR-006), so it would surface as an
ordinary `integrated`; `runner_shared.INTEGRATION_REFUSAL_CONFLICT` is `merge-refused`, documented in-code as
"the gate measured the work and REFUSED it" and deliberately renamed from `merge-conflict` because a conflict
is only one of four causes it collapses, so neither existing word may absorb the new behavior.

OQ-01 DELIBERATELY REMAINS `Blocking: yes` AND OPEN, and that is the correct disposition rather than an
oversight. It asks whether the runner may rewrite records content during integration, which changes a shipped
contract, is explicitly the maintainer's call, and cannot be resolved from repository evidence: the repository
states the OPPOSITE of what E-03 wants, so "resolve from evidence" would mean answering no. What review added
is the PRICE, so the question can be answered once with its cost visible: saying yes means amending an
approved spec's flat prohibition. The plan is therefore `NO-GO` until answered, while E-01/E-02 remain a
legitimate, contract-neutral partial landing that closes the measured resolver trap on their own. The gate now
says so explicitly.

NOT FLAGGED, checked and correct: `Work-Kind: bug` with `Blocks-Release: next` satisfies the live-bug rule;
`From-Backlog: 21fykf` resolves to a `graduated` item carrying the same gate; OQ-02's resolution (sequencing
is a complementary mitigation, not a substitute, and needs no code) is well-reasoned and its cross-run
limitation is honest; OQ-03 is correctly left to the maintainer rather than the executor deciding to edit a
terminal-directory plan; E-04's all-or-nothing rule is exactly the right shape for a mechanism that writes to
permanent records; and the five E-items are right-sized, one concern each, with a complete E/V bijection.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | E. Testing and verification | `git branch -a` lists 125 lane branches and NONE matching `8u6770`; `aw/lane/lc4unl` exists at `b1223b4f` with `git diff --name-only main...aw/lane/lc4unl` -> 4 paths, all under `.aw/records/` | THE MANDATORY REPLAY HAS NO SOURCE. The plan asserts "the lane branch and the merge base are both still resolvable" and V-01 demands the verdict for each of 13 files, but that lane is gone, so the item is unsatisfiable and an executor would either fail it or quietly substitute a synthetic fixture while claiming the real measurement. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Required tests and V-01 re-pointed at `aw/lane/lc4unl` as an explicitly-labelled 4-path substitute for the 13-path original, with a labelled synthetic fallback permitted and a synthetic-presented-as-real failing V-01. |
| PR-002 | BLOCKER | UNDER-SCOPE | C. Architecture / spec sync | Spec `25kzda` Section 2.1: the ladder "never applies to a genuine merge conflict ... none of which repetition fixes", "none reclassifies a failure as a deferral"; 2026-09-21 amendment note: "No rule changed". The plan cited only `runner_shared.integrate_lane_branch`'s docstring line | E-03 CONTRADICTS AN APPROVED SPEC, and the plan understated the obstacle as a convention about human resolution while declaring no spec path. `8u6770` hit exactly the prohibited class, so re-derivation cannot ship without a declared, narrow carve-out in the same change. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Spec-sync section rewritten with the real quotes and three obligations (declare the path first, write a narrow carve-out, preserve `merge-refused`'s meaning); E-03 and the gate carry the requirement; V-03 fails without the diff; OQ-01's rationale now records the cost so the maintainer decides with it visible. |
| PR-003 | LOW | IN-SCOPE | G. Executability (citation accuracy) | `oc_runipd.queue_sort_key` and `oc_runipd.dependency_depth`, with "DECLARED EDGES WIN" in the former's docstring; no agy-side definition of either; nothing of the sort in `runner_shared` | The Step-0 convention attributes both symbols to `runner_shared`, where they do not exist. The convention itself is accurate and asks for no code change, so the impact is a reader failing to find the cited evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Attribution corrected in place, with an explicit note that `Scope-Paths` needs no widening because no change is asked of those symbols. |
| PR-004 | HIGH | IN-SCOPE | B. Security lens / A. Correctness | E-01 as authored ("front-matter keys ORTHOGONAL to `- Status:`"); the repository's own treatment of `- Readiness:` as an attestation the auto-approve predicate reads first, plus `- Approval:`, `- Blocks-Release:`, `- Item-Dependencies:`, `- Id:`/`- Set:`/`- Order:` | THE SAFETY TEST IS A DENY-LIST OF ONE KEY, so the classifier would treat every gate, attestation and identity field as re-derivable and an integration could write one automatically. That is a strictly worse outcome than the conflict being resolved. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | E-01 now requires an explicit ALLOW-list stated in code (the measured case needs `- Work-Kind:` and `- Priority:` only), with every other key returning not-this-shape; E-05 gains an allow-list control that must FAIL if widened to a gate or attestation key; V-01 requires the list pasted and `- Readiness:` exercised as a negative case. |
| PR-005 | MEDIUM | IN-SCOPE | A. Correctness and data integrity | The shape as authored spans `.aw/records/`; `git diff --name-only main...aw/lane/lc4unl` includes two `backlog/open/*.backlog.md` beside two plans; backlog, spec, release and review records each carry their own status enum and lifecycle layout | THE SHAPE IS DEFINED OVER A BROADER TREE THAN WAS MEASURED. Only plan front matter was observed, yet the classifier would accept any `.aw/records/` path, so a backlog or spec record could be classified by a plan-shaped rule. The substitute replay lane itself contains such files, so this is live rather than theoretical. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 must classify the artifact TYPE and return UNKNOWN for any unmeasured type; E-05 pins that arm; V-01 requires a `.backlog.md` negative case. |
| PR-006 | MEDIUM | IN-SCOPE | C. Operability / honest reporting | `runner_shared.INTEGRATION_REFUSAL_CONFLICT = "merge-refused"`, documented as "the gate measured the work and REFUSED it" and deliberately renamed from `merge-conflict` because it collapses four causes | A RE-DERIVED INTEGRATION HAD NO DISTINCT REPORTED OUTCOME, so it would be reported as a plain `integrated`, hiding the single event an auditor most needs to see (that records content was RECOMPUTED rather than merged). Reusing `merge-refused` would be equally wrong in the other direction. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 must report a distinct outcome and say in the run record that content was recomputed; V-03 requires that line pasted; a Step-0 convention records that a refusal kind's meaning must not be stretched. |
| PR-007 | HIGH | UNDER-SCOPE | C. Architecture and operability | `aw check` rule `check.ipd-uncarried-obligation` (severity `error`): "2 obligation(s) name no durable carrier ... OQ-01 ... OQ-03" | BOTH OPEN QUESTIONS AND ALL FOUR DEFERRED ROWS NAMED NO DURABLE CARRIER, so each obligation would vanish from `aw attention` once the plan finalized. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Deferred rows carry `- Carrier: 8u6770` and `- Carrier: tgyfs2` where a real sibling owns the work, and reasoned `- Carrier-Declined:` where nothing is outstanding; OQ-01 and OQ-03 each carry a `- Carrier-Declined:` explaining why no honest carrier exists before the maintainer answers. `aw check` now reports no carrier finding for this plan; tree total 57 -> 56. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The replay source named by the plan no longer exists. Drop the real-replay requirement, or re-point it? | Re-point it at `aw/lane/lc4unl`, require the size difference to be stated, and permit a clearly labelled synthetic fallback. | (a) Drop the requirement and accept a synthetic fixture - rejected: F-5's claim (one mechanical rule resolved all 13 files) rests on real data, and a synthetic fixture built from the plan's own description cannot test that claim, only restate it. (b) Keep demanding the 13-file `8u6770` replay - rejected: measured, the branch is absent from all 125 lane branches, so the item would be unsatisfiable and an executor would be pushed toward quietly substituting. (c) Ask the maintainer to restore the lane - rejected: the lane was deliberately discarded and its work re-derived by hand, per the plan's own Under-scope note. | `git branch -a` (125 branches, no `8u6770`); `git diff --name-only main...aw/lane/lc4unl` -> 4 records paths; the plan's F-6 already names `lc4unl` as the same class | yes |
| D-2 | Should the reviewer resolve OQ-01, since the repository does answer the question? | No. Leave it `Blocking: yes` and open, and add the spec cost to its rationale. | (a) Resolve it NO from the spec prohibition - rejected: the prohibition is exactly what the maintainer may choose to amend, so reading it as the answer would pre-empt a contract decision that is explicitly theirs (the workflow forbids guessing a human decision). (b) Resolve it YES on the plan's own recommendation - rejected: that recommendation predates the spec finding, and approving it would authorize amending an approved spec on reviewer authority. (c) Set `Blocking: no` so the plan can proceed - rejected: it genuinely blocks E-03, and the flag exists to record exactly that. | Spec `25kzda` 2.1's prohibition; `AGENTS.md` on who may approve a spec change; the plan's own OQ-01 owner field (`maintainer`). ESCALATED: OQ-01 is raised in the reviewed plan as `- Blocking: yes` and remains open, so the lint gate refuses execution at every checkpoint until the maintainer answers, and `- Readiness:` is `no-go`. | no |
| D-3 | What defines a re-derivable ("orthogonal") front-matter key? | An explicit allow-list stated in code, seeded with exactly the two keys the measured case needs. | (a) Keep "any key that is not `- Status:`" - rejected: measured against this repository's own field set, that admits `- Readiness:`, `- Approval:`, `- Blocks-Release:` and `- Item-Dependencies:`, so an integration could forge an attestation or move a release gate. (b) Allow any key absent from the target file - rejected: `- Readiness:` is absent from a plan that has never been reviewed, which is precisely the case where writing it is worst. (c) Ask the maintainer for the list - rejected: the measured edit needs two keys and the conservative list is derivable from the incident, so this is an implementation decision, not a policy one; widening it later is a visible code edit with a failing test guarding it. | The plan's own F-2 (the lane adds `- Work-Kind:`/`- Priority:`); `AGENTS.md` on `- Readiness:` as an attestation the auto-approve predicate reads first | yes |
