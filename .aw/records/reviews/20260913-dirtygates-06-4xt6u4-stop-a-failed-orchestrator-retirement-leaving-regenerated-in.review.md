# Review: stop a failed orchestrator retirement leaving regenerated index files, child 4xt6u4 (Set dirtygates)

- Subject-Id: 4xt6u4
- Subject-Type: ipd
- Reviewed-At: 2026-09-13
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `54b6f7ce`. Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0
findings) before semantic review, and `--phase review-finalize` conforms after the revisions, with no
`IPD-Q501`: this plan carries no blocking open question, which is the honest state for it.

DISCLOSURE: same repository and same model family as the author, so this is close to a self-review and
worth less than an independent one. Its value rests on what was DRIVEN. Measured here: F-1 reproduced
end to end in the repository's own fixture rather than inherited; the same fault driven a SECOND time
against a fixture whose manifests already existed, which is what relocated the defect; the two
prescribed journal keys traced through git history to the commit that deleted them and the comment that
forbids them; the plans-index gate's behavior with absent manifests measured; every point of the
`:1984` test's own sequence sampled; and the spec grepped for any requirement this change could touch.

THE PLAN IS SOUND AND ITS CENTRAL MEASUREMENT IS REAL. I re-drove `retire_orchestrator(apply=True,
fault_injection="after_move")` in the repo's own fixture and got F-1's values exactly: exit code 2,
message "fault-injected finalize failure (after_move); rolled back to pre-finalize state.", status
before `''` and after `?? .aw/records/plans/INDEX.json` plus `?? .aw/records/plans/INDEX.md`, plan
restored, destination gone, HEAD unmoved. F-2's citation is right (`:1961-1972` asserts restoration,
destination removal and HEAD, and never tree state). F-3 is right (step 4 regenerates rather than
restores). F-4's severity qualifier is right and I confirmed both manifests are gitignored at
`.aw/.gitignore:45-46` with `git check-ignore -v` returning rc=0. This is a well-scoped plan that fixes
a genuine defect and correctly refuses the architecture question its sibling carries; the four findings
below sharpen it rather than challenge it.

THE FINDING MOST LIKELY TO HAVE COST AN EXECUTOR REAL TIME IS PR-601. E-01 said to capture the
manifests' prior state "in the journal alongside the plan's `original_bytes`". Those exact keys already
existed and were removed ON PURPOSE, and there is a standing comment in the code saying so
(`:2642-2645`): the journal "deliberately carries no `index_json_before`/`index_md_before` content
snapshot ... they were dead weight describing a restore that never happened". I traced it to commit
`674f2c68` (2026-09-07), whose message lists the removal among nine deliberate contributor removals and
calls it "a content-restore no code performs". The plan's fix is RIGHT, and that is worth stating
plainly: the keys were dead weight then because nothing read them, and this plan makes something read
them. What was missing is the obligation to update the comment in the same change. Left alone it would
become false on landing and would actively instruct the next reader to undo the fix, and nothing would
catch it (neither key name appears in any test).

THE FINDING THAT CHANGES WHAT THE FIX MUST DO IS PR-603, AND I FOUND IT BY RUNNING THE FAULT TWICE.
The fixture starts with no manifests, which is why F-1 shows them as CREATED. A real repository has
them. So I pre-generated them and drove the same fault: `INDEX.json` came back BYTE-IDENTICAL, and both
copies correctly named the plan's `pending/` path. That means the corpus is already restored by the time
step 4 runs and the generator is deterministic, so regenerate-from-corpus and restore-from-journal AGREE
whenever the manifests already exist. The defect is therefore confined to create-where-absent. This is
not a reason to weaken the plan, it is a reason to aim it: the fix must make ABSENCE a restorable state
rather than merely snapshotting bytes, and the test must cover both prior states, because a test
covering only the broken one would not prove the fix left the working case alone. Restoring absence is
safe and I verified it: an absent manifest is `check.stale-index-missing` at severity `info`
(`check_engine.py:333-335`) and `aw index plans --check` returns rc=0 with both absent.

TWO SMALLER CORRECTIONS. PR-602: E-02 told the executor to add a `git status --porcelain` EMPTINESS
assertion to "the `before_commit` case at `:1984`". That test is
`test_a_stale_pre_commit_journal_is_ROLLED_BACK_before_a_fresh_attempt`, whose subject is crash RECOVERY
and whose last act is a SUCCESSFUL retirement asserted `EXIT_OK`. A successful retirement legitimately
regenerates the manifests, so the tree is not empty when it ends. Sampled at all three points of its own
sequence: `''`, then the two `??` entries after the failed attempt, then the SAME two after the
successful retry. The assertion would have failed even with E-01 correctly implemented, so an executor
would have spent time deciding whether their own fix was broken. PR-604: replacing step 4's
regeneration silently drops the fail-loud arm, because `_refresh_plans_index_fail_loud` both regenerates
AND verifies, raising on non-convergence, which the rollback turns into its "rollback index regeneration
failed" result. That arm is untested (the string appears only at `:1936`), so nothing would catch its
disappearance. E-01 now has to state its fate rather than leave it implicit.

I ALSO ASSERTED THE PROPERTY THE PLAN ASKED ABOUT RATHER THAN LEAVING IT AS AN INSTRUCTION. The spec-sync
section said "VERIFY BEFORE EXECUTING by reading those requirements; if one speaks to rollback
completeness, amend it". I grepped spec `77tr3o` for `rollback` and `restore`: no hits. So no amendment
is expected, the spec file must NOT be added to `Scope-Paths`, and that is now recorded as a verified
negative rather than as homework.

ONE CROSS-PLAN HAZARD RECORDED, NOT WIDENED. The plan's own scope check asked whether review wants an
audit of `_rollback_precommit` for other paths it writes rather than restores, and said to state so
rather than widening. My answer: it should be its own plan and I did not widen this one. But one instance
matters immediately, because step 2 (`:1910-1920`) writes `original_bytes` over `original_path`
unconditionally while step 1 guards its destination, and sibling Order 04 (`u23gbn`) E-08 now owns making
that safe, since Order 04's relocation is what turns it into an overwrite of a peer's edit. Both plans
declare `agent_workflows/ipd_lifecycle.py`, so the scope check now records the division: this plan
touches step 4, Order 04 touches step 2.

WHAT I DELIBERATELY LEFT ALONE. OQ-01's resolution is correct and I confirmed its reasoning by
measurement rather than overturning it; I only replaced its hedge ("would usually produce the same
bytes, but only if...") with the measured fact that both conditions hold, which relocates the defect
without changing the decision. F-4's severity qualifier is honest and I strengthened nothing: this is a
correctness defect in a rollback that claims to restore, not an outage risk in this repository. And the
plan's refusal to take on Order 04's architecture question is right; carving it out was the correct call.

No product code was modified by this review. The full suite was run bare and is unchanged:
`6280 passed, 3 skipped, 2 xfailed`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | UNDER-SCOPE | C (architecture), G (honest documentation) | `ipd_lifecycle.py:2642-2645`; `git log -S index_json_before` -> `674f2c68` (2026-09-07) whose message calls it "a content-restore no code performs"; `grep -rn "index_json_before\|index_md_before" tests/` -> nothing | E-01's PRESCRIBED MECHANISM REINSTATES TWO JOURNAL KEYS THAT WERE DELIBERATELY DELETED, AND A STANDING COMMENT FORBIDS THEM. The comment states the journal "deliberately carries no `index_json_before`/`index_md_before` content snapshot ... dead weight describing a restore that never happened". The fix is right (the keys were dead weight because nothing read them; this makes something read them), but the plan never obliged the executor to update that comment, so it would become FALSE on landing and would instruct the next reader to undo the change. Nothing pins the journal key set, so no test would catch it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New E-01 bullet with the history, requiring the comment be updated in the same change and the ORIGINAL key names reused so the history reads as a reinstatement. Spec/doc-sync section gains the comment as a second, more dangerous stale-doc site than the docstring. V-01 requires the updated comment be pasted. New F-6. |
| PR-602 | HIGH | IN-SCOPE | E (testing) | `tests/test_orchestrator_retirement.py:1977` (`test_a_stale_pre_commit_journal_is_ROLLED_BACK_before_a_fresh_attempt`), which ends `second = self.retire(...)` asserted `EXIT_OK`; measured status at three points: `''`, then two `??`, then the SAME two | E-02's SECOND ASSERTION SITE WOULD PIN A FALSE PROPERTY. It told the executor to add a porcelain EMPTINESS assertion to "the `before_commit` case at `:1984`", but that test's subject is crash RECOVERY and its last act is a SUCCESSFUL retirement, which legitimately regenerates the manifests. The assertion would fail even with E-01 correctly implemented, sending the executor to debug a working fix. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 rewritten to target the ONE rollback-subject test, with the measurement recorded and the midpoint named as the only defensible place for a check in the recovery test. E-02 also now requires EQUALITY to the pre-attempt status rather than emptiness, since emptiness is the wrong property (it would pass if the test destroyed unrelated state). Required tests and V-02 corrected. New F-9. |
| PR-603 | MEDIUM | IN-SCOPE | A (correctness), G (honest documentation) | measured: pre-generated manifests + `fault_injection="after_move"` -> `INDEX.json` byte-identical before and after, both naming the `pending/` path; `check_engine.py:333-335`; `run_index(check=True)` rc=0 with both absent | THE DEFECT IS NARROWER THAN THE PLAN'S FRAMING, WHICH CHANGES WHAT THE FIX MUST DO. Regeneration is BYTE-EXACT when the manifests already exist, so regenerate and restore agree in that case and the entire defect is create-where-absent. The Concern, Goal and F-1 present the residue as the general shape of the bug. The fix must therefore make ABSENCE a first-class restorable state, and the test must cover BOTH prior states, since one covering only the broken case would not prove the working case was preserved. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Goal gains the measurement and its two practical consequences; new F-7; E-01 gains a three-state prior-value requirement with the safety of restoring absence verified; Required tests gains both prior-state cases plus `aw index plans --check` in each; V-01 requires both pasted and notes that a porcelain check alone cannot distinguish created-and-ignored from absent. OQ-01's hedge replaced with the measured fact. |
| PR-604 | MEDIUM | UNDER-SCOPE | A (correctness), E (testing) | `ipd_lifecycle.py:1932-1936` and `:1656-1695`; `grep -rn "rollback index regeneration failed" tests/` -> nothing | REPLACING STEP 4 SILENTLY DROPS AN UNTESTED FAIL-LOUD ARM. `_refresh_plans_index_fail_loud` both regenerates AND re-runs `--check`, raising on non-convergence, which the rollback converts into its "rollback index regeneration failed" result. Replace the regeneration with a restore and that verification has no subject, so the arm disappears. The plan does not mention it and no test would catch the removal. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New E-01 bullet requiring the fate of the arm be DECIDED and STATED (keep a post-restore check, or drop it and record that manifest trouble no longer fails a rollback), with the note that it is currently untested. Required tests demands whatever replaces it be exercised; V-01 demands the replacing code be quoted. New F-8. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-01 reinstates journal keys a standing comment forbids. Is that a REPLAN (the approach is wrong) or a fixable omission? | A fixable omission: keep the approach, add the obligation to update the comment and reuse the original key names. | Mark REPLAN and require a different mechanism that does not re-add the keys; or leave the comment alone as a historical note. | The comment's own stated reason for the removal is that "NOTHING ever read them", i.e. they described a restore no code performed. This plan makes the code perform that restore, so the condition the removal rested on no longer holds and the keys stop being dead weight. The approach is therefore correct and only the documentation obligation was missing. | yes |
| D-2 | Regeneration proved byte-exact when the manifests exist (F-7). Does that mean the plan is unnecessary? | No. Keep it, and narrow its aim to create-where-absent. | Retire the plan as fixing a non-defect; or leave the framing broad so the fix stays general. | The measured residue is real and reproduced twice: a tree with no manifests before the attempt has two afterwards, which is a rollback that claims to restore and does not. What the measurement changes is the AIM, not the validity: the fix must restore absence, and the test must cover the already-present case too so the fix cannot regress it. | yes |
| D-3 | Should review widen this plan to audit every path `_rollback_precommit` writes rather than restores? | No. Record the one instance that matters for a sibling plan and leave the audit to its own plan, as the plan's own scope check invited. | Widen this plan to cover step 2's unguarded write as well; or say nothing and let the two plans discover the overlap. | The plan explicitly asked review to state rather than widen, and step 2's unguarded write is already OWNED by Order 04 E-08, because Order 04's relocation is what makes it destructive. Widening here would put two unrelated properties in one commit and duplicate a sibling's item. Recording the division prevents both plans editing the function blindly. | yes |
| D-4 | The plan left "verify the spec before executing" as executor homework. Resolve it now, or leave it? | Resolve it now: grepped `77tr3o` for `rollback`/`restore`, no hits, so no amendment is expected and the spec file must not be declared. | Leave the instruction, since the executor would do it anyway. | It is a five-second check with a definite answer, and leaving it costs an executor a decision point where none exists; worse, an executor uncertain about it might declare the spec file in `Scope-Paths` defensively, which then costs a `--scope-ack` at finalize for a file that was never going to change. | yes |

No decision this round is `Reversible: no`, so none required escalation as a blocking question. That is
the honest state of this plan: it carries a measured defect, a bounded fix, and no architecture or
contract decision reserved to the maintainer. The one such decision in this area (shared versus forked
transaction code) belongs to sibling Order 04 and was correctly carved out of here before authoring.
