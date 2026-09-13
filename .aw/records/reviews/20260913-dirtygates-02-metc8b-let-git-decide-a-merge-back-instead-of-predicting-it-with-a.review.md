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
