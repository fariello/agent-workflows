# Review findings: plan d7jpo3

- Subject-Id: d7jpo3
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `3199f621` in a lane worktree. Structural preflight `aw ipd lint --phase author`
CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` conforms after
revision. No pre-review snapshot was owed: the plan was committed and unmodified (`git status
--short` empty at review start). Bare suite at review HEAD: `3246 passed, 2 skipped, 3 warnings in
49.98s`, 207 deselected.

DISCLOSURE, RECORDED FIRST BECAUSE IT IS AN INCIDENT AND NOT A FINDING. While verifying E-03's claim
that `aw backlog note` accepts an id6, this reviewer ran the verb for real against `59t9x5` instead
of against a throwaway copy, appending one history line reading `PROBE (dry)`. A review must not
modify records, and this did. It was caught immediately, the diff inspected (a single added line,
nothing else touched), and reverted with `git restore` on that one path; `git status --short` is
empty and `grep -c 'PROBE (dry)'` on the file returns 0. No other party's work was in the file and
nothing was committed. The probe DID establish two facts the plan needed (the verb accepts a bare
id6, and it appends without transitioning or moving), and those are recorded in E-04 - but the right
way to get them was a temp-dir repo, which is what should have been done.

THE PLAN'S CORE REASONING IS CORRECT AND WELL-EVIDENCED, and its central judgement is the right one.
Every load-bearing measurement reproduces: `aw find plans wtiso` returns 8, the exclusion contract
holds at 0, the causal offset table matches the source item byte for byte (2507/2954/3894 visible
against 4177/4241/5153/5581/7281 not), `ecdd348f` is present with the quoted message, the executed
plan `826o13` already self-corrects in its own E-01 execution note naming eight and the offsets and
this very backlog item, no test pins the count, and the `2iye0e` OQ-02 precedent says exactly what
the plan says it says. The LIVE-GUIDANCE-versus-DATED-ACCOUNT distinction that reduces a four-record
sweep to one correction plus three reasoned refusals is sound, is grounded in three separate README
contracts plus `AGENTS.md`, and has in-repo precedent. Refusing to rewrite dated history is the
correct call and the plan argues it well.

WHAT REVIEW FOUND IS THAT THE PLAN'S OWN PRESCRIPTION REPRODUCES THE DEFECT CLASS IT EXISTS TO
REMOVE. The glob figure E-01(b) measures and E-02 writes is SELF-REFERENTIAL: this plan's filename
contains `wtiso`, so the plan is counted by its own measurement. The number moved from 15 to 16
between authoring and review for that reason alone, and this review record makes 17. An executor
following the plan as authored would have written a fresh stale integer into the very bullet being
corrected for carrying a stale integer. That is PR-001 and it is the finding that justifies this
review.

A SECOND OMISSION COMPOUNDS IT: the bullet directly beneath the one being corrected is stale from
the SAME commit, in three respects, and the plan does not touch it. Correcting one and leaving the
other would make the block self-contradictory on a single screen.

VERDICT AND READINESS, INCLUDING A CONTRACT TENSION WORTH RECORDING. OQ-02 is left `open`
(non-blocking, `Owner: maintainer`) per D-3, which puts two clauses of the plan-review workflow in
tension: the verdict list reserves `APPROVE WITH REVISIONS APPLIED` for a plan with "no open
questions", while the readiness rules, as amended by the maintainer's ruling of 2026-09-10 on plan
`qhy3i3` OQ-01, make only an unresolved BLOCKING question a `NO-GO` and state that "A NON-BLOCKING
open question does NOT make a plan `NO-GO`". Resolved toward the newer and more specific rule, for
two reasons. First, the ruling's stated reasoning generalizes: treating blocking and non-blocking
questions alike "discards the distinction the field was created to carry". Second, and decisive here,
OQ-02 asks whether the maintainer wants this work done at all, which IS the approval decision rather
than a prerequisite to it; answering it and approving the plan are the same act, so holding the plan
`NO-GO` pending an answer would deadlock on a question only approval can close. Verdict therefore
`APPROVE WITH REVISIONS APPLIED` with `- Readiness: go-pending-approval`, and the open question is
declared plainly in the final report rather than treated as closed. A maintainer who reads OQ-02 and
declines should retire the plan `not-executed` citing it, which the plan's gate already instructs.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric A (correctness); Rubric G (live-artifact re-derivation convention) | `.aw/records/plans/pending/20260929-kx9md1-01-d7jpo3-correct-the-stale-aw-find-wtiso-count-in-the-one-live-guidance-site.ipd.md` filename; plan E-01(b), E-02, V-01 | THE PLAN'S PRESCRIBED CORRECTION RE-CREATES THE DEFECT IT CORRECTS. The glob count `find .aw/records -iname '*wtiso*'` is self-referential: this plan's own filename contains `wtiso`, so the plan counts itself. Measured 15 at authoring, 16 at review HEAD (the sixteenth file IS this plan, added by `d42f31e0`), and 17 once this review's record lands. E-02 as authored told the executor to write the measured integer into the guardrail bullet, which would commit a figure already stale at commit time, in the exact line being corrected for staleness. V-01's "state any divergence" instruction also mislabels a guaranteed self-inflicted change as possible corpus drift. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-09 records the self-reference with the measurements and the causing commit. E-01(b) now requires BOTH the raw count and the count net of this work's artifacts, with a statement of which is used. E-02 now FORBIDS a bare integer and requires the property (a glob returns strictly more, including other Sets and unrelated docs), with any figure marked as a dated sample. V-02 now FAILS a diff that merely swaps `12` for `16`. A dedicated gate paragraph warns the executor. Scope and Concern updated. |
| PR-002 | HIGH | UNDER-SCOPE | Rubric D (anti-regression: do not leave an adjacent falsehood); Rubric F (prevent silent failure) | `.aw/records/backlog/done/20260912-59t9x5-01-59t9x5-find-display-layer-double-read.backlog.md` `## Guardrails any implementation inherits from 826o13`, second bullet; `agent_workflows/selectors.py` symbols `_HEADER_CHUNK_BYTES`, `_HEADER_MAX_BYTES`, `_METADATA_END_RE` | The bullet immediately below the one E-02 corrects is stale from the SAME commit and the plan does not mention it. It reads "Nine records carry a declared identity ABSENT from their bounded 4096-byte header, including `25kzda`". Three parts are now false: there is no 4096-byte header BOUND (`ecdd348f` made 4096 a read quantum under a structural bound, as `selectors.py`'s own comment states: "THE CHUNK IS A READ QUANTUM, NOT A CAP, AND THAT DISTINCTION IS THE WHOLE BUG FIX"); the count is 291 not nine (worst offset 39224); and `25kzda` carries `- Id:` at byte 209 so is no longer an instance. Correcting one bullet and leaving its neighbour makes the block internally inconsistent on one screen and leaves the next optimizer misled by the adjacent line. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-10 with all three measurements. New E-03 corrects the bullet while PRESERVING its surviving requirement (a declared identity must be findable wherever it sits; no fixed cap may return) and inherits E-02's anti-rot rule. New V-03 requires the supporting evidence pasted and requires `selectors.py` to be read-only. `- Highest E allocated:` 03 -> 04; old E-03 renumbered E-04; Proposed changes and Scope check updated with the declared widening. |
| PR-003 | MEDIUM | IN-SCOPE | plan-review Step 1 (evidence verification) | plan F-04(ii) vs `.aw/records/reviews/20260910-findtier-01-826o13-...review.md` | F-04 states the review's stale count "sits in round 3's `WHAT WAS RUN` ledger" and attributes a `WHAT THE PLAN GOT RIGHT` re-measurement to the same round. Measured: the review has FOUR `wtiso` count statements across TWO rounds. The two the plan quotes are in ROUND 1 (lines 25 and 33, against `## Round` headings at 10/111/147); round 3 carries a separate ledger line (165) and a `D-7` DECISIONS row (192) arguing the property. The refusal is unaffected and arguably stronger (a Decisions row is an even more clearly dated account), but an executor checking the refusal against the file would not find what the plan describes where it says it is. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04(ii) rewritten with the corrected enumeration, the line/round measurement, and an explicit statement that the refusal is unchanged. The Deferred bullet is retitled from "ROUND-3 LEDGER" to the four statements across both rounds and now also argues why rewriting a `Basis` cell would be worse than rewriting a count. A gate paragraph states that finding more history is not a licence to rewrite it. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric G (executability) | plan E-03 (now E-04) vs `aw backlog note --help` | E-03 prescribed `aw backlog note 59t9x5 --message "<why>"`, but the verb's documented positional is a PATH (`positional arguments: path`). An executor reading the help would see a mismatch with the plan and could reasonably stall or guess. Verified by running it: the bare id6 DOES resolve and append, so both spellings work and the plan's invocation is not wrong, merely undocumented-looking. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now states that the documented positional is a path, that a bare id6 also works, that review verified this, and that the executor should prefer the declared path. The verified append-without-transition property is recorded there too. The gate paragraph carries the same note. |
| PR-005 | MEDIUM | IN-SCOPE | Rubric E (validation completeness) | plan E-02/V-02 `Expected outcome` wording | E-02's outcome required "the two numbers changed to the E-01 measurements", which after PR-001 is the WRONG bar: writing the measured glob integer is now a failure rather than the goal. Left as written, V-02 would have certified the defect PR-001 identifies. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02's `Expected outcome` re-specified around the non-rotting property, and V-02 given an explicit failure condition ("a diff that simply replaces `12` with `16` FAILS V-02"). |
| PR-006 | LOW | IN-SCOPE | plan-review Step 1 (live-population re-derivation) | plan F-06 ("10 plans mention it") | F-06's `y6mfgo` mention count was 10 at authoring and is 12 at review. The finding's CLAIM (the resolver returns 1 while many plans mention it, so the property holds) is unaffected, and the plan correctly flags this figure as not-a-contract, so this is drift rather than a wrong claim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-06 updated to 12 with a parenthetical noting the authoring figure and that the growth is itself a small illustration of why a mention count does not belong in a pin. Also records the independent re-measurement of the 8 rows and the 0 exclusion count at review HEAD. |
| PR-007 | LOW | IN-SCOPE | Rubric G (traceability) | plan F-03 ("15"), Concern/Scope prose | F-03 and the Scope field carried the authoring glob figure 15 as a present-tense measurement; at review it is 16, for the self-referential reason PR-001 establishes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03 updated to 16 with a pointer to F-09; Concern and Scope rewritten to state the self-reference and the property-not-integer remedy rather than quoting a figure as the target. |
| PR-008 | LOW | IN-SCOPE | Rubric G (plan hygiene) | plan `- Highest E allocated: 03`; E-item cross-references | Adding E-03 required renumbering the history item to E-04, updating `- Highest E allocated:`, and sweeping every cross-reference that named the old numbering (E-02's closing sentence pointed at "E-03 owns the history record", V-02 pointed at "E-03's appended record"). A stale cross-reference after a renumber is the exact class the workflow's revision-sweep rule names. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Highest E allocated:` set to 04; history item renumbered E-04 with `Depends on: E-02, E-03`; every cross-reference swept (E-02 body, V-02 body, Proposed changes, Scope check, gate). `aw ipd lint --phase review-finalize` conforms, confirming the `E-*`/`V-*` bijection survived. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | PR-001 shows the glob count cannot be written as a durable integer. Replace it with a property, drop the glob clause entirely, or write the integer with a date? | Replace with a PROPERTY (a glob returns strictly more, naming the other Sets and unrelated docs), permitting a figure only if explicitly marked a dated sample. | Dropping the glob clause (rejected: the contrast IS the artifacts-not-references contract the bullet exists to state, so deleting it would remove the guidance rather than fix it); writing a dated integer alone (rejected as the primary form: a reader skims the number, not the caveat, which is how the original 12 misled). | The repository's own live-artifact convention, stated in the plan-review workflow's Rubric G: a criterion counting live artifacts "MUST state the required property and require re-derivation at execution time; a count measured at authoring belongs in the item's prose as context, never as the bar". Measured self-reference: `find .aw/records -iname '*wtiso*'` = 16 including this plan, 15 excluding it. | yes |
| D-2 | PR-002's stale second bullet is outside the source item's literal scope ("the stale `wtiso` count"). Widen this plan to fix it, or file a separate carrier? | Widen this plan (new E-03), and DECLARE the widening in Scope check. | Filing a new backlog item (rejected: it would leave a known falsehood sitting one line below a line this very plan corrects, for an unbounded interval, and the fix needs the same file, the same block and the same `ecdd348f` attribution already being written); leaving it silently (rejected: makes the block self-contradictory). | Same root cause and same commit: `ecdd348f` is what invalidated both bullets, verified by `grep -n 4096 agent_workflows/selectors.py` showing `_HEADER_CHUNK_BYTES` with the quantum-not-cap comment. No new `- Scope-Paths:` entry is needed because it edits the one already-declared file, so the finalize scope reconciliation is unaffected. | yes |
| D-3 | OQ-02 asks whether this correction earns a plan at all, and is `Owner: maintainer`, `Status: open`, non-blocking. Resolve it from evidence, or leave it open? | Leave it OPEN, unanswered, and add a dated note recording that review changed its inputs. | Resolving it `yes` on the ground that review doubled the deliverable (rejected: substitutes reviewer judgement for the maintainer's on cost-versus-value); resolving it `no` (rejected for the same reason, and it would contradict the plan being otherwise sound). | The plan-review workflow reserves this class to the human: "Never guess a human decision", and a non-blocking open question does not make a plan `NO-GO` per the 2026-09-10 maintainer ruling. No repository evidence decides whether a low-priority chore is worth a run; that is scope and priority, explicitly the maintainer's call per `AGENTS.md`. | yes |
