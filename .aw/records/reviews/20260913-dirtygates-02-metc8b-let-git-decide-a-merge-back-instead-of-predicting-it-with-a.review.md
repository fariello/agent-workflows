# Review: let git decide a merge-back instead of predicting it with a dirty-overlap heuristic, child metc8b (Set dirtygates)

- Subject-Id: metc8b
- Subject-Type: ipd
- Reviewed-At: 2026-09-13
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `c2e74824`. Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0
findings) before semantic review; at `--phase review-finalize` it reports one `IPD-Q501`, the escalation
gate working as designed on the blocking question this review added.

DISCLOSURE: same repository, same model family as the author, so this is a near-self-review worth less
than an independent one. Its value rests on what was DRIVEN. Measured here: every cited anchor opened
individually (`runner_shared.py:969-976`, `:984-990`, `:1001-1015`, `:1035-1063`, `:393-402`, `:421-472`);
the complete caller census of `dirty_tree_overlap` across `agent_workflows/` and `tests/` (excluding
worktree copies); the two stranded lanes' recorded `status` and `integration_deferral` read from run
`state.json`; and THREE scratch-repo git experiments covering the non-overlapping dirty case, the
overlapping dirty case, and the main-advanced-plus-overlapping-dirty case, in the last of which I checked
`MERGE_HEAD`, `--diff-filter=U`, and the exit code of `git merge --abort`.

THE PLAN'S TECHNICAL PREMISES ARE SOUND AND REVIEW CONFIRMED THEM INDEPENDENTLY. F-1, F-2 and F-3 all
reproduced: `git merge-tree --write-tree` returns rc=0 in BOTH the succeeding and the refusing case, so it
is genuinely not a predictor; a real merge with a NON-overlapping dirty path succeeds and preserves the
dirt; with an OVERLAPPING dirty path it refuses, names the file, aborts itself, and leaves both main and
the dirty content byte-intact. F-5's single-caller claim is exactly right (one non-test caller,
`runner_shared.py:1003`), and OQ-01's fallback protection is intact (`ipd_lifecycle.py:894-897`).

THE MOST USEFUL THING THIS REVIEW FOUND IS THAT THE PLAN CONTAINS TWO SEPARABLE CHANGES AND ONLY ONE IS
CONTESTED. E-02/E-03 reclassify a local-changes refusal from `merge-conflict` to `integration-blocked`;
that has a MEASURED witness (both 2026-09-13 stranded lanes are exactly this misclassification), needs no
spec motion, touches only the post-merge failure branch, and COMPLEMENTS approved plan `51vw4y`, whose
ladder defers the `integration-blocked` arm while leaving `merge-conflict` terminal. Under that ladder
today's misclassification is precisely what would convert a recoverable condition into permanent in-run
loss. E-01/E-04/E-05 delete the prediction, rest on F-1/F-5 plus simplicity with NO run record behind them,
and contradict two approved release blockers. So the plan was restructured: E-02's dependency dropped from
`E-01` to `none`, E-01/E-04/E-05 explicitly gated on the new blocking OQ-03, and the split recorded in the
scope check so a (b) ruling retires half the plan instead of stalling all of it.

A GENUINE CODE DEFECT WAS FOUND THAT THE PLAN WOULD HAVE INHERITED. On the local-changes path git never
STARTS the merge, so `.git/MERGE_HEAD` is absent and `git diff --diff-filter=U` is empty; the shipped code
nevertheless calls `git merge --abort` unconditionally, which exits 128 ("There is no merge to abort").
Today the return value is discarded so it is silent and harmless. E-02 makes that path a first-class
branch, so the abort must become conditional. Better, the same measurement supplies the ROBUST
discriminator E-02 needed: the plan proposed to recognize the case by git's English message
("error: Your local changes..."), which is localizable and version-dependent, where the `MERGE_HEAD`
presence plus empty `U` set is structural. E-02 and V-02 now require the structural test and forbid
relying on the text.

ON OQ-01, WHICH IS ANSWERED AND WHICH THIS REVIEW DID NOT REOPEN. Every premise behind the maintainer's
DELETE ruling re-verified true. What the ruling did not have in view is that `fujm0y` is an approved,
reviewed design for KEEPING the guard usefully (widening its input to the merge-result diff), which is
precisely the option OQ-01's "if it cannot be kept usefully, delete it" logic assumed away. Worth noting
that widening would also make F-5's "narrower than git's precondition" objection false by construction.
So OQ-03 asks a narrow, answerable question, whether DELETE stands on complete information, rather than
re-litigating the reasoning.

No product code was modified by this review.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | BLOCKER | IN-SCOPE | C (architecture), G | `pending/20260907-mergedirty-01-fujm0y-...ipd.md:12` and its E-02; `20260906-integpath-03-51vw4y-...ipd.md:11`, `:122` ("THE REFUSAL ITSELF IS CORRECT AND MUST SURVIVE") | Two approved, `Blocks-Release: next` plans are signed off to KEEP and IMPROVE the symbol this plan deletes. The maintainer's OQ-01 DELETE ruling was given without them in view, and its own fallback logic ("if the gate cannot be kept usefully, delete it") assumed no such design existed; `fujm0y` is exactly that design, reviewed and approved. | C:High; U:Low; S:Low; F:Medium-High; Overall:High | OPEN | Escalated as blocking OQ-03 with three costed options and a recommendation of (b) KEEP AND IMPROVE. E-01/E-04/E-05 gated on the answer; the plan restructured so E-02/E-03 remain executable either way. |
| PR-202 | HIGH | UNDER-SCOPE | A (correctness), E | measured at review: main-advanced + overlapping dirty path -> rc=2, no `.git/MERGE_HEAD`, empty `git diff --diff-filter=U`, `git merge --abort` rc=128; `runner_shared.py:1055-1057` | E-02 proposed to recognize a local-changes refusal by git's English text, which is localizable and version-dependent, and inherits an unconditional `git merge --abort` that is invalid on that path (no merge in progress). The structural discriminator (`MERGE_HEAD` absent + empty `U` set) is available and exact. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | E-02 now requires the structural test, demotes any text match to a commented secondary hint, and makes the abort conditional. V-02 demands the discriminator itself be pasted, not just its outcome. New F-6 records the measurement. |
| PR-203 | HIGH | IN-SCOPE | C, G (executability) | this plan's E-02 vs E-01/E-04; `51vw4y` E-01 (ladder scoped to the `integration-blocked` arm only); F-4 | The plan bundled a contested deletion with an uncontested, measured reclassification and made the latter depend on the former (`E-02 Depends on: E-01`). A ruling against the deletion would therefore have stalled the one change with a measured witness, which also happens to be the change approved plan `51vw4y` needs. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02's dependency changed to `none`; E-01/E-04/E-05 gated on OQ-03 with explicit skip-and-record-not-performed instructions; the split documented in the scope check; new F-7 states the separability and why E-02 complements `51vw4y`. |
| PR-204 | MEDIUM | IN-SCOPE | E (testing) | `tests/test_oc_runipd.py:3176,:3181,:3185`; `tests/test_agy_runipd_cli.py:686,:690,:693`; `tests/test_lane_clean_base.py:267,:270,:272,:295`, `:216-247` | E-04 said "at least five test sites" pinned by identity. Measured: 10 CALL sites plus 5 identity pins across four modules, and `tests/test_lane_clean_base.py:216-247` is an ANTI-FORK regression (`test_dirty_tree_overlap_no_longer_forks_the_parser`) whose deletion silently removes the pin that stopped a per-host copy reappearing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 carries the verified census, names the anti-fork test explicitly, and requires the loss of that property be stated in the commit message rather than dropped silently. Scope check records that a (b) ruling removes essentially the whole diff. |
| PR-205 | MEDIUM | IN-SCOPE | G (honest documentation) | `run-20260913T032416Z-2009920` and `run-20260913T031521Z-1774617` `state.json`; commits `acde2496`, `51cb5d7a`, `50d71d05` | F-4 asserted the prediction stranded lanes `bzz5e6` and `f6idxs`; both are recorded `merge-conflict` carrying git's own "Your local changes" text, so the REAL merge refused them and the prediction passed them through. The plan's strongest-sounding evidence supported its opposite. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected during the orchestrator review pass and re-verified here per item; F-4 rewritten, F-4a added stating the honest narrower case, Concern block updated. |
| PR-206 | LOW | IN-SCOPE | G | this plan's Spec / documentation sync | The spec-sync section tells the executor to search for a requirement behind `driverfin-03 (7kbtkw)` before executing. Confirmed at review that no specs-tree requirement mandates the pre-merge prediction, so the instruction is correct as a verification step and needs no change; recorded so the executor knows it was already checked once. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | No edit required; verification recorded here as evidence rather than left for rediscovery. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the maintainer's answered OQ-01 (DELETE) settle the matter, so review should proceed as if the deletion is authorized? | No. Raise a NEW, narrow blocking question (OQ-03) asking whether DELETE stands on complete information, without reopening OQ-01's reasoning. | Treat OQ-01 as dispositive and review only the mechanics; or unilaterally rewrite the plan to KEEP the guard. | OQ-01's rationale contains its own fallback ("if it cannot be kept usefully, delete it") and `fujm0y:12` is an approved, reviewed design for keeping it usefully that the rationale never mentions. A ruling made without a material option in view is not a ruling on that option. | no |
| D-2 | Should E-02 be allowed to depend on E-01, as authored? | No. Decouple it: E-02 `Depends on: none`. | Leave the dependency and let a (b) ruling block the whole plan; or split E-02 into a separate IPD. | E-02 edits only the post-merge failure branch and needs no change to the guard call site (verified by reading `runner_shared.py:1001-1063`), and it is the only part with a measured witness (F-4). Decoupling inside the plan is the smaller change than a new IPD. | yes |
| D-3 | How should E-02 recognize a local-changes refusal? | By the structural test (`MERGE_HEAD` absent plus empty `--diff-filter=U`), with any text match demoted to a commented hint. | Match git's English "Your local changes to the following files would be overwritten by merge", as the plan proposed. | Measured at review: the structural signals are exact and already read by shipped code (`conflicted_paths` documents the empty-return case for "a refusal to start"), whereas git's message text is localizable and version-dependent, so a text match is a silent-breakage risk in a gate. | yes |
| D-4 | The unconditional `git merge --abort` exits 128 on the local-changes path. In scope to fix? | Yes, fold it into E-02. | Leave it (today it is silent) and file a separate item. | E-02 turns that path into a first-class branch, so the plan itself makes the defect reachable and meaningful; `plan-review.md:201` fixes by default at Low remediation risk, and splitting a two-line conditional into its own plan is not warranted. | yes |

D-1 is `Reversible: no` and is ESCALATED as required: raised in this plan as OQ-03 with `- Blocking: yes`
and `- Finding: PR-201`, so the lint gate refuses the plan at every checkpoint until the maintainer
answers. It is the child-level counterpart of the orchestrator's OQ-02, narrowed to this symbol.

## Round 2

Reviewed at HEAD `4f745afa`, as an INDIVIDUAL review of this child. It exists because the orchestrator's
round-2 review raised OQ-04: Orders 01, 02 and 04 carried a stale `Readiness: no-go` from their round-1
reviews although their blocking questions had since been resolved, and that field could not honestly be
rewritten by a review whose ledger was the parent. This is the review that earns the field for `metc8b`.

Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0 findings) before semantic review;
`--phase review-finalize` CONFORMING after revisions.

DISCLOSURE: same model family as the author and as the round-1 reviewer, so treat this as a near-self-review
worth less than an independent one. Its value rests on what was MEASURED at this HEAD.

ROUND 1'S BLOCKER IS GENUINELY DISCHARGED AND THE PLAN IS NOW SOUND. PR-201 escalated the collision with two
approved `Blocks-Release: next` plans over deleting `dirty_tree_overlap`; OQ-03 resolved to option (b) KEEP
AND IMPROVE, and the withdrawal genuinely landed: the checklist holds exactly E-02 and E-03, the "Proposed
changes" list marks 1, 4 and 5 WITHDRAWN, and no surviving item touches the symbol. Verified independently
rather than trusted: `dirty_tree_overlap` still has one definition (`runner_shared.py:888`) and one live
caller (`:1003`); the three `kind` values and their branch are exactly where the plan cites them (`:986-988`,
`oc_runipd.py:6753-6762`); the unconditional abort is at `:1055-1057`; and `conflicted_paths`' docstring
already documents the empty-return case for "a refusal to start" (`:393-402`). Every anchor resolved.

I RE-MEASURED THE PLAN'S CENTRAL MECHANISM AND IT HOLDS. In two scratch repos: a LOCAL-CHANGES refusal gives
rc=2, NO `.git/MERGE_HEAD`, EMPTY `git diff --diff-filter=U`, `git merge --abort` exiting 128 with "fatal:
There is no merge to abort (MERGE_HEAD missing)", the dirty content surviving verbatim and HEAD unmoved; a
REAL CONTENT CONFLICT gives `MERGE_HEAD` PRESENT, `U:f.txt`, and `git merge --abort` rc=0 leaving a clean
tree. So the structural discriminator genuinely discriminates, and keying on it rather than on git's English
is correct.

WHAT ROUND 2 FOUND ARE TWO GAPS IN HOW THE SURVIVING ITEM REACHES ITS GOAL, neither of which round 1 could
see because both live in code the deletion would have removed. FIRST (PR-207), the reason string is built by
`format_merge_conflict_reason`, which HARD-CODES the words "merge-back conflict" into every string it
produces (`:451`, `:468`) and whose entire contract is about conflicted paths read from the index. A
local-changes refusal has none, so reusing that helper reproduces today's misleading "merge-back conflict;
error: Your local changes..." wording under a new `kind`, defeating the item's purpose while passing a
`kind`-only assertion. Its test file was also undeclared. SECOND (PR-208), the refusal is reached by TWO
routes and the plan describes one: measured, when main has NOT advanced, `git merge --ff-only` ITSELF refuses
with the same "Your local changes" text (rc=1) and that output is deliberately DISCARDED at `:1036`, so
execution falls through to the `--no-ff` attempt. The discriminator still classifies it correctly, so the
outcome is right, but an executor reading "main advanced past the lane base" as the precondition could nest
the new branch under that assumption, or could "fix" the discarded ff-only output and surface an expected
non-error into the operator-facing reason, which is the exact defect the `mergemsg` work fixed.

I ALSO CLOSED THE SCOPE CONFLICT RATHER THAN FLAGGING IT AGAIN. The orchestrator's round 2 recorded PR-012
(two dead declared paths) as a reconciliation for the executor. Round 2 here found the stronger reason to act:
`tests/test_lane_clean_base.py` is a file approved plan `3i0aaz` requires byte-identical and deliberately
leaves undeclared, so declaring it was a live conflict with a release blocker, not merely a needless
`--scope-ack`. Both dead paths are now DROPPED from `Scope-Paths`.

NOTHING GATES THIS PLAN. Both blocking questions are resolved, the lint is conforming, and no finding was
left OPEN, so the readiness moves to `go-pending-approval`. That answers the orchestrator's OQ-04 for this
child: its `no-go` was genuinely stale and is now cleared on the evidence.

No product code was modified by this review.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | BLOCKER | IN-SCOPE | G, C | `fujm0y:12`, `51vw4y:11`; this plan's E-list | CARRIED FROM ROUND 1 AND NOW DISCHARGED. The deletion collided with two approved release blockers. Verified the withdrawal landed in the executable text: E-02/E-03 only, changes 1/4/5 marked WITHDRAWN, `dirty_tree_overlap` untouched with its definition and sole call site intact. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-03 resolved to (b) by the maintainer; the plan's shape matches. |
| PR-207 | HIGH | UNDER-SCOPE | A (correctness), E, G | `runner_shared.format_merge_conflict_reason:421-478`, literal "merge-back conflict" at `:451`, `:468`; called at `:1058-1062`; `tests/test_merge_conflict_reason.py:112,135,147,158,182` | THE REASON STRING IS BUILT BY A HELPER THAT HARD-CODES THE WRONG WORDS, and its test file was undeclared. Reusing it for the new class reproduces the exact misleading "merge-back conflict; error: Your local changes..." text the two stranded lanes recorded, so the item could pass a `kind`-only assertion while shipping the defect it exists to fix. The helper's contract is conflicted-paths-from-the-index, and a local-changes refusal has none. | C:Medium; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | New F-8. E-02 now decides the route explicitly (preferred: a separate reason builder, helper untouched), requires preserving the measured `mergemsg` stdout contract if the helper is taught a second class, and requires declaring `tests/test_merge_conflict_reason.py` in that case. V-02 requires pasting the reason string and showing it does not say "merge-back conflict". |
| PR-208 | HIGH | IN-SCOPE | A (correctness), E | measured at review: main NOT advanced, dirty path also changed by the lane -> `git merge --ff-only` rc=1 "Your local changes..."; `git merge-base --is-ancestor HEAD lane` confirms ff was possible; the discard is `runner_shared.py:1036` | THE REFUSAL HAS TWO ROUTES AND THE PLAN DESCRIBES ONE. E-02 and F-6 both frame it as the `--no-ff` attempt failing "after main advanced". Measured, it also occurs with main unadvanced, via the ff-only attempt whose output is deliberately discarded. The discriminator still classifies correctly so the outcome is right, but the stated precondition invites nesting the branch under a main-advanced condition, or "fixing" the ff-only discard and surfacing a benign expected failure into the operator-facing reason. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Low | FIXED | New F-9. E-02 gains an explicit "do not assume main advanced" instruction and "leave the ff-only discard alone"; V-03 and the test section require the case proven via BOTH routes, since a single main-advanced case passes even for a wrongly nested branch. |
| PR-209 | MEDIUM | UNDER-SCOPE | E (testing) | E-03's own wording ("both failure kinds") versus V-03's evidence list | V-03 COVERED ONLY ONE OF THE TWO KINDS E-03 CLAIMS. E-03 asserts non-destructiveness "on both failure kinds", while V-03 asked only for the local-changes case's before/after. Nothing required proof that a content conflict still leaves a clean tree, and nothing required proof that the abort became CONDITIONAL, which is the one new way this item can regress (F-6). | C:Low; U:Low; S:Low; F:Medium-High; Overall:Low | FIXED | V-03 gains the content-conflict tree-cleanliness case, the both-kinds abort evidence (issued for the conflict, NOT issued for local changes), and the both-routes requirement. |
| PR-210 | MEDIUM | IN-SCOPE | G (honest documentation) | plan Goal and Concern versus the shipped scope | THE GOAL AND CONCERN STILL DESCRIBED THE WITHDRAWN DELETION. The Goal read "Stop guessing what `git merge` will do. Attempt it, and treat its own refusal as the answer", and the Concern opened on the prediction being wrong and closed with "Do NOT execute this plan until the orchestrator's blocking OQ-02 is answered". Both are false: the prediction is retained by the OQ-03 ruling, and that question is resolved. An executor reading the Goal would believe the prediction is meant to go, which is the one thing this plan must not do. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Goal rewritten to the classification objective; Concern rewritten to lead with the misclassification and its measured witness, state plainly what the plan no longer does, and record that the gate is discharged. |
| PR-211 | MEDIUM | OVER-SCOPE | G, D | `Scope-Paths` (pre-edit); `3i0aaz` E-06 `:91`, V-06 `:212-214`, fence `:252` | TWO DECLARED PATHS WERE DEAD AND ONE WAS CONTESTED. `lane_containment.py` and `tests/test_lane_clean_base.py` were needed only by the withdrawn items. Beyond costing a needless `--scope-ack`, declaring the test file conflicted with approved release-blocker `3i0aaz`, which requires it byte-identical and deliberately leaves it undeclared so any edit is a scope violation. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Both DROPPED from `Scope-Paths` (not `--scope-ack`ed, which would leave the false claim that this plan has business in those files). The gate paragraph records the closure and forbids re-adding them. |
| PR-212 | LOW | IN-SCOPE | G (executability) | F-7, E-02, the scope-check split note, the `merge-tree` deferral (pre-edit) | FOUR PASSAGES STILL SPOKE OF THE WITHDRAWN ITEMS AS PENDING A RULING ("survives any ruling", "if OQ-03 rules (b), execute the first pair and retire the second"), and the `merge-tree` deferral could be misread as opposing approved plan `fujm0y`, which is signed off to use `merge-tree --write-tree` as the retained check's INPUT. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All four rewritten to past tense with the ruling stated; the `merge-tree` deferral now distinguishes rejecting it as a PREDICTOR (F-1) from `fujm0y`'s approved use of it as an INPUT. |
| PR-213 | LOW | IN-SCOPE | G, E | `tests/test_oc_runipd.py:3251`, `tests/test_agy_runipd_cli.py:756`, `tests/test_runner_shared.py:1685`, `:1715`, `:1775` | POSITIVE RESULT, recorded rather than left implicit. The plan warned that identity-pinning tests "fail first if a symbol is removed", which no longer applies since nothing is removed. Located the five test call sites that unpack `(integrated, reason, kind)`: E-02 adds no parameter, so none needs a signature change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The call sites are enumerated in the test section with an instruction to confirm rather than assume no signature change is needed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-5 | PR-207: should E-02 reuse `format_merge_conflict_reason` for the new class, or build the local-changes reason separately? | Record a PREFERENCE for a separate builder, and permit teaching the helper a second class provided the `mergemsg` stdout contract is preserved and the test file is declared. | Mandate the separate builder outright; or leave the choice unstated as the plan did. | The helper's own docstring scopes it to "a lane merge-back that failed on a real git conflict" and builds its message from conflicted paths read from the index, which a local-changes refusal does not have; but the helper also carries a measured incident contract (`run-20260906T162533Z-1552446`) that a competent executor may prefer to extend in one place. `plan-review.md:214-222` requires replacing ambiguity, which a stated preference plus a conditional obligation does, without over-constraining an implementation detail. | yes |
| D-6 | PR-211: drop the two dead declared paths, or leave them for the executor to `--scope-ack`? | Drop them from `Scope-Paths`. | Leave them and record the `--scope-ack` obligation, as the orchestrator's round 2 did. | `plan-review.md:211` makes removal the default fix for over-scope and rates it Low risk. The stronger reason is D-specific: `3i0aaz` (approved, `Blocks-Release: next`) requires `tests/test_lane_clean_base.py` byte-identical and leaves it undeclared, so a declaration here is a standing conflict with a release blocker rather than a tidiness issue. Editing the declaration is a plan-text change, which is within a reviewer's authority. | yes |
| D-7 | The title still says "Let git decide a merge-back instead of predicting it", which the plan no longer does. Rename? | No. Record the discrepancy in the Concern. | `aw rename plans` to match the reduced scope. | A rename changes the `<slug>` in the uniform artifact name and every cross-reference (the orchestrator's child table, this review record, sibling plans). Cost of a stale-but-explained title is one paragraph. Same reasoning applied to the orchestrator (round 2 D-3) and to `d7qoxv` (round 2 D-7), so the three are consistent. | yes |
| D-8 | Which readiness does this plan carry? | `go-pending-approval`, verdict APPROVE WITH REVISIONS APPLIED. | `no-go`, carried over from round 1; `go`, which would require `Status: approved`. | `plan-review.md:536-542`: GO - PENDING HUMAN APPROVAL is the correct positive state when the verdict is APPROVE WITH REVISIONS APPLIED, no open question remains, and no BLOCKER/HIGH is left unfixed. Both OQs are resolved, all seven round-2 findings are FIXED, and `aw ipd lint --phase review-finalize` reports CONFORMING. The round-1 `no-go` was genuinely stale. | yes |

No `Reversible: no` decision was taken in this round, so no escalation is required under
`plan-review.md:279-292`. Round 1's blocker was escalated as OQ-03 and the maintainer has answered it,
which is what discharged PR-201.

NOTE ON THE ORCHESTRATOR'S OQ-04: for `metc8b` the stale `no-go` is now CLEARED to
`go-pending-approval` on the evidence of this round. `u23gbn` still carries an unverified `no-go`.
