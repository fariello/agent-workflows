# Review: make the auto-approve predicate require the review evidence IPD-M107 demands, child 8v5pwa (Set rdattest)

- Subject-Id: 8v5pwa
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `84258553`. Structural preflight `aw ipd lint --phase author` conformed (clean, 0 findings)
before semantic review, and `--phase review-finalize` conformed after the revisions. The plan carries no
`- Blocks-Release:`, correctly: backlog `754txs` carries none, and the plan says so explicitly rather than
inventing a gate for a `Work-Kind: security` `Priority: high` item.

DISCLOSURE: authored in the same repository and by the same model family as the plan, so treat this as a
near-self-review and worth less than an independent one.

THE PROBLEM IS REAL, THE DIRECTION IS RIGHT, AND I REPRODUCED THE DEFECT RATHER THAN TRUSTING IT. A plan
carrying `- Readiness: go` whose only history line is a `to-review` record with no review at all returns
True from `is_plan_review_approved`. The decision order the plan describes is intact, the four driver
consumers are real, and the security framing is correct: this predicate is what lets `--full-auto` move a
plan to an executable tier.

BUT THE PLAN'S CHOSEN MECHANISM DOES NOT FIX THE DEFECT, AND THAT IS THE FINDING THAT MATTERS. It reuses
`ipd_lint._REVIEW_EVIDENCE_RE`, which matches a bare MENTION anywhere in the history text. I ran three
forgeries through it: a `to-review` record saying "I mention plan-review in passing", a `draft` record
containing the word APPROVE, and a non-review record containing REJECT. All three PASS. Each is precisely
the forged field this plan exists to refuse, so the plan as authored would have shipped a gate that still
returned True, while its tests (which cover only the bare no-evidence case) went green. A security fix that
looks done and is not is worse than an open item, because it retires the backlog entry.

THE FIX WAS ALREADY SITTING IN THE FILE BEING EDITED. `plan_readiness.is_review_history_entry` parses a
record and requires a review token in the record's own status/workflow middle; it refuses all three
forgeries and accepts a real `/plan-review` record. It is already consumed by `newest_verdict` and
`approval_refusals`, so using it adds no second definition of "attested" and no import at all. The backlog
item framed this as a dilemma between duplicating the rule and importing the lint module; both horns
dissolve, because the item did not know this primitive existed. Its own docstring calls the discriminator
"THE CENTRAL CORRECTNESS REQUIREMENT of the approval gate".

THE PLAN'S IMPORT-SAFETY CLAIM IS FALSE, which matters independently because it would have been acted on.
F-5 asserts `ipd_lint` imports only stdlib plus `ipd_schema` and `term`. An AST walk shows it also imports
`attention`, `check_engine`, `ipd_authoring`, `record_producers`, `renderers` and `result_types`, function
scoped rather than at the header, reaching `engine`, `artifact_core`, `plans`, `selectors` and
`runner_shared` behind them. Both drivers import `plan_readiness` and the item's stated constraint is that
it stay stdlib-cheap, so the authored route would have put the CLI stack behind a hot predicate. Moot under
the corrected mechanism, and recorded so nobody restores the import believing F-5.

THREE ACCURACY CORRECTIONS, each of which would have misled the executor. The corpus numbers are stale and
their framing was backwards: 139 plans carry the field, not 65, and the "zero flips" that the plan and the
backlog item both present as the strongest safety argument is a SYMPTOM of the weak mechanism. Under the
corrected mechanism exactly one plan flips, and it is a true positive whose field says `go` while its own
review said REVIEWED - OPEN QUESTIONS. The drivers promote to `auto-approved`, not human `approved`, which
the plan's Concern and Goal both get wrong. And the suite baseline is wrong in both halves, with the real
failure caused by another party's gitignored directory that an executor had an incentive to delete.

Six findings, all FIXED in place, no deferrals. One new open question (OQ-02) records the layer divergence
the corrected mechanism introduces, since the plan's original goal was one shared definition of attested
and it no longer delivers that. E-item and V-item counts are unchanged at five each.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | BLOCKER | IN-SCOPE | B. security; A. correctness | `ipd_lint.py:728-730` (`_REVIEW_EVIDENCE_RE`); `plan_readiness.py:355-375` (`is_review_history_entry`); all four cases run at review | **THE CHOSEN MECHANISM DOES NOT STOP A FORGED FIELD, so the plan as authored would have shipped a security fix that does not fix the defect and would have closed the backlog item.** `_REVIEW_EVIDENCE_RE` matches a MENTION anywhere in the history, so a `to-review` record mentioning `plan-review`, a `draft` record containing `APPROVE`, and a non-review record containing `REJECT` ALL pass; each is exactly the forgery in scope. The authored tests cover only the bare no-evidence case, so the suite would have gone green. The STRONGER discriminator is already defined in the same file, already consumed by `newest_verdict` and `approval_refusals`, and refuses all three while accepting a real review record: it needs no import and creates no second definition, dissolving both horns of the item's stated dilemma | C:Low; U:Low; S:High; F:High; Overall:Medium | FIXED | E-01 rewritten to use `is_review_history_entry` and to forbid the lint pattern, with all three measured forgeries recorded; E-04 gains the three mention-forgery assertions as the cases that prove the mechanism was necessary; E-03 gains the newest-versus-any-record decision that the discriminator raises; Scope, Concern, conventions and deferred list updated; V-01/V-04 require the forgeries pasted. New F-11, and OQ-02 records the resulting layer divergence |
| PR-702 | HIGH | IN-SCOPE | C. architecture; F. KISS | AST walk of `ipd_lint` at review; `plan_readiness` imported by both drivers plus `status_set`/`ipd_schema` | **F-5's import-safety claim is FALSE and was load-bearing for the authored design.** `ipd_lint` imports `attention`, `check_engine`, `ipd_authoring`, `record_producers`, `renderers`, `result_types` inside functions, reaching `engine`, `artifact_core`, `plans`, `selectors`, `runner_shared`. The plan cited the module header only. Adding that edge would put the CLI/renderer stack behind a predicate both drivers call in a loop, violating the item's own explicit stdlib-cheap-and-driver-agnostic constraint | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-5 rewritten with the measured import set; E-01 forbids the import explicitly; the fence repeats it; the conventions list corrects the "ipd_lint is stdlib-cheap" entry. Moot under the corrected mechanism, recorded so it is not restored |
| PR-703 | MEDIUM | IN-SCOPE | E. testing; Evidence accuracy | re-measured at `84258553`: 615 plan files, 139 carry `Readiness`, 127 True today, 1 flips under the corrected mechanism (`5e4sb6`) | **The corpus numbers are stale and their framing inverts the evidence.** The plan and the item both present "0 of 65 flip" as the strongest argument for safety; the real count is 139, and zero flips under the AUTHORED mechanism is a symptom of that mechanism being too weak to bite. Under the corrected mechanism exactly one flips, and it is a TRUE POSITIVE: `5e4sb6`'s newest record is an `approved` record rather than a review, and its actual review verdict was REVIEWED - OPEN QUESTIONS while its field says `go` | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-4 marked superseded with the re-measured figures and the corrected reading; E-03 carries the new numbers, the classified flip, and the newest-versus-any-record recommendation; OQ-01 re-grounded; the gate's cost argument rewritten so approval does not rest on the wrong version; V-03 requires a fresh measurement and the `5e4sb6` classification |
| PR-704 | MEDIUM | IN-SCOPE | Evidence accuracy; G. executability | `oc_runipd.py:735-759` (`set_plan_approved` docstring); `ipd_schema.py:265-267` (`READY_TO_EXECUTE`) | **The plan misdescribes the transition it hardens: the drivers promote to `auto-approved`, never to human `approved`.** All four sites call `set_plan_approved`, which deliberately avoids the human-approval attestation so the machine never claims a human approved something no human approved. The security defect is unchanged (an unreviewed plan reaches an executable tier) but the Concern and Goal overstate it, and an executor reading them would look for a transition that does not exist | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern corrected in place with the distinction and the note that the defect survives it; E-05 carries the correction and requires the executor to confirm it; V-05 requires it stated. New F-12 |
| PR-705 | MEDIUM | IN-SCOPE | E. testing; D. anti-regression | measured `2 failed, 5957 passed, 3 skipped, 2 xfailed`; `test_orchestrator_retirement` -> `112 passed`; `.gitignore:49` | **The suite baseline is wrong in both halves and the real failure invites destroying another party's work.** The plan cites `1 failed, 5648 passed` naming `test_orchestrator_retirement`, which PASSES. The actual failures are the reporting-contract parity test, which fails only because a GITIGNORED `opencode-recovery/` tree of another party's session transcripts quotes the contract prose, and a SIGINT test that passes in isolation and fails on a 30-second timeout under `-n auto` | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Required-tests carries the re-measured baseline with both node ids and the load-sensitivity note plus an explicit prohibition on touching `opencode-recovery/`; the fence repeats it; V-05 requires node-id comparison against the corrected figure |
| PR-706 | LOW | UNDER-SCOPE | G. executability; documentation | `plan_readiness.py` `newest_verdict` and `approval_refusals` docstrings; `ipd_schema.py:230`, `:317`; driver line numbers | **The in-code documentation obligation is wider than the plan states, and four cited line numbers had already drifted.** The plan names two docstrings to correct; the same field-is-authoritative ordering is asserted as shared house rule in `newest_verdict` and `approval_refusals` too, and both become false for the field-present case. The `ipd_schema` notes stay true (they concern absence). Separately the four driver line numbers are stale (`:2936`/`:6931`/`:1974`/`:3988`), and two of the four sites swallow a raise in `try/except Exception: pass` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync section enumerates every cross-reference to correct and which to leave alone, warning that `approval_refusals` is a different gate whose behavior does not change; E-05 carries the corrected line numbers and the swallowed-raise obligation. New F-13, F-14; F-15 records the stronger typed-record option and its 137-of-139 coverage |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The plan's chosen mechanism does not stop a forgery (PR-701). Reject the plan as unsound, or repair the mechanism in place? | REPAIR IN PLACE. The plan's goal, scope, sequencing and validation structure are all correct; only the mechanism choice is wrong, and the correct primitive is already in the file the plan already declares, so the repair is bounded and needs no new scope path | REJECT - NEEDS REPLAN (rejected: the defect is one substitution inside one E-item, not an unsound approach, and replanning would discard five sound E-items and a good validation plan); leave the mechanism and note the weakness (rejected outright: that ships a security fix that does not fix the defect and closes the backlog item, which is worse than leaving the item open) | `plan_readiness.is_review_history_entry` exists at `:355-375`, is already consumed by two functions in the module, and refuses all three measured forgeries | yes |
| D-2 | Should the discriminator scan the NEWEST history record only, or ANY record, for the attestation question? | RECOMMEND any-record, and hand the decision to the executor with both measured flip counts rather than fixing it myself. Any-record still refuses every forgery (a forged plan has no review record anywhere) and flips 0 plans; newest-only flips 1 | Newest-only (not chosen as the recommendation: it conflates "was this field ever attested" with "what is the newest verdict", which `newest_verdict`/`approval_refusals` already own, so it would duplicate a second gate's job); decide it silently in review (rejected: it is a genuine design choice with a measurable difference, and E-03's job is to measure it at execution time when the corpus is current) | Ran both variants over 139 Readiness-carrying plans; `newest_verdict` already owns the newest-verdict question | yes |
| D-3 | The corrected mechanism makes lint and predicate define "attested" differently, contradicting the plan's stated one-definition goal. Fix the divergence here, or record it? | RECORD IT as OQ-02 with three costed routes, and state the position that the divergence is CORRECT because a lint nudge should be permissive and a security gate must not be | Tighten `IPD-M107` to match (rejected for this plan: it changes a shipped lint contract, is covered by a corpus test with its own expectations, and could newly fail plans in the tree, so it needs its own measurement and justification); adopt the typed review record in both (rejected here as the largest change, though it is the strongest end state and is named in the deferred list with its 137-of-139 coverage) | The two layers have different failure costs: a lint false positive is friction on every plan, a gate false negative is an unreviewed plan reaching an executable tier | yes |
| D-4 | `5e4sb6` carries `- Readiness: go` that its own review's REVIEWED - OPEN QUESTIONS verdict does not support. Fix that plan, or leave it? | LEAVE IT, and record the classification in E-03 and under-scope so the executor does not treat the flip as a false positive. It is already human-`approved`, so nothing automated depends on the field | Correct the field (rejected: it is another party's plan, outside this fence, and editing a plan to make a measurement come out differently is exactly what the fence forbids); ignore it (rejected: an unclassified flip would leave the executor deciding fresh whether to weaken the check) | Its history shows a `2026-09-03 approved` newest record and a `2026-08-30 reviewed ... REVIEWED - OPEN QUESTIONS` verdict; `Status: approved` already set by a human | yes |
