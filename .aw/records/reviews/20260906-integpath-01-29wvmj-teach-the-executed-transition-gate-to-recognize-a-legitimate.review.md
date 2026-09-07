# Review: teach the executed-transition gate to recognize a legitimate lane merge, child 29wvmj (Set integpath)

- Subject-Id: 29wvmj
- Subject-Type: ipd
- Reviewed-At: 2026-09-07
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `01b0b150`. `aw ipd lint --phase author` reported conforming BEFORE semantic review
and `--phase review-finalize` conforming after every revision, so nothing here is structural.

DISCLOSURE: the same agent/model authored this plan, so this is a SELF-REVIEW. What raises it above a
rubber stamp is that every load-bearing claim was RE-EXECUTED rather than read: the defect was
reproduced in a throwaway repository, the `HEAD..MERGE_HEAD` scoping was proven implementable, the
worktree hazard was confirmed (`.git` is a FILE, `rev-parse --git-dir` resolves it), and the
security-critical case (c) was shown to refuse today. That re-execution is what produced PR-101, a
measured falsification of the plan's own ordering rationale that no amount of reading would have found.

SCOPE: only this child was a candidate. The orchestrator `cczotj` and siblings `6sb3yu`, `51vw4y`,
`rl67b0` were read as evidence only and are not reviewed here.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | IN-SCOPE | A. Correctness; C. Architecture | throwaway repo 2026-09-07 with both hook types installed; `ls .git/hooks/`; `oc_runipd.py:2039`, `:2044-2052` | **THE PLAN TARGETS A HOOK GIT DOES NOT RUN FOR THE PATH IT NAMES.** The Concern's ordering rationale says children 03/04 make integration more frequent so "every one of those integrations would trip this hook". MEASURED FALSE: git runs `pre-merge-commit` (NOT `pre-commit`) for an automated merge and `MERGE_HEAD` is ABSENT when it runs; `merge --ff-only` creates no commit and fires nothing; only the HAND sequence (`--no-commit` then a separate `git commit`) fires `pre-commit` with `MERGE_HEAD` present. This repo installs ONLY `pre-commit`. So the runner's `integrate_lane_branch` never trips this gate, the stated urgency is wrong, and an executor trusting it would expect coverage the fix cannot deliver. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | The plan still does real work (all four measured bypasses were hand merges, which IS a `pre-commit` path), so the fix is honesty about which path is covered, not a redesign. Added F-14 with the measurement; rewrote the Concern's ordering rationale to the true one (this is the only runner-free child, so it can land while siblings contend over the drivers); added a mandatory pre-E-01 note; V-01 now requires pasting the hook-type evidence and proving the detector FAILS CLOSED. The residual automated-merge hole is raised as OQ-03 (non-blocking) rather than silently scope-crept. |
| PR-102 | MEDIUM | UNDER-SCOPE | C. Architecture; G. Plan executability | same as PR-101 | The automated-merge hole PR-101 exposes is pre-existing and WIDER than the bug this child fixes: any automated merge carrying a plan into `executed/` bypasses this gate entirely, today, with or without this plan. The plan had no place to record it, so it would have been lost. Closing it means `default_install_hook_types` plus a re-`pre-commit install` on every clone, i.e. an environment change outside this plan's two-file scope. | C:Medium; U:Medium; S:Low; F:Low; Overall:Medium | FIXED | Recorded as OQ-03, `Blocking: no`, owner maintainer, with three options and a recommendation (file it as its own backlog item, keeping this child's two-file scope so the environment change is reviewed on its own merits). Non-blocking is justified in the question itself: nothing in the plan depends on the answer, and the fix fails closed, so a later `pre-merge-commit` installation tightens the gate rather than breaking it. |
| PR-103 | MEDIUM | IN-SCOPE | E. Testing; honesty | measured `1 failed, 5613 passed` at HEAD `01b0b150`; plan's `Required tests / validation` pre-revision | The stated baseline (`5536 passed, 3 skipped, 2 xfailed` at HEAD `3d239cfa`) is stale by ~77 tests and, worse, asserts a GREEN suite when HEAD carries a pre-existing failure (`test_orchestrator_retirement::RealRepositorySets`). An executor comparing against it would either report a false regression or be tempted to claim green. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with the review-measured baseline, an explicit judge-on-the-DELTA instruction, and the named pre-existing failure (confirmed present with this plan's changes stashed) so it is not reported as this plan's. |
| PR-104 | MEDIUM | IN-SCOPE | E. Testing (a trap the reviewer hit) | `tests/test_plan_readiness.py:789-798`; `plan_readiness.py:406-421` | A REAL corpus test reads the live `pending/` tree and fails if any pending plan's newest review record classifies NEGATIVE. `newest_verdict` falls back to a negative-READINESS scan when a review record states no verdict token, so a history line saying `Readiness no-go` WITHOUT an explicit verdict token breaks the suite. The reviewer triggered exactly this while reviewing the orchestrator, turning a green-except-one baseline into two failures. The plan gave the executor no warning, and the executor will write history lines. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Documented the trap in `Required tests / validation` with the requirement to state a verdict token explicitly. The reviewer's own offending line on `cczotj` was corrected in the same pass and the suite verified back to the 1-pre-existing-failure baseline. |
| PR-105 | LOW | IN-SCOPE | G. Plan executability (stale self-reference) | plan gate line 193 pre-revision; OQ-01 `Status: resolved` | The gate said "OQ-01 is deferred and non-blocking with its rationale recorded", but OQ-01 was RESOLVED on 2026-09-07 by the plan's own preceding revision. A gate misstating its own question states cannot be relied on by a reader deciding whether the plan is approvable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now states OQ-01 and OQ-02 resolved, OQ-03 open and non-blocking, and that the plan is therefore approvable. |
| PR-106 | LOW | IN-SCOPE | Documentation sync | measured: no match for `executed_transition_gate` in `AGENTS.md`/`CONTRIBUTING.md`; `AGENTS.md:175` | The doc-sync section instructs correcting any doc that "tells a reader that a lane merge requires `--no-verify`". No such doc exists: neither file mentions this hook, and AGENTS.md's only `--no-verify` mention is the honest general statement that local hooks are skippable, which is CORRECT and must not be edited. As written the instruction invites an unnecessary doc edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded the measurement, flagged the expected no-op, added an instruction to re-grep and SAY SO if still a no-op rather than inventing a change, and explicitly protected `AGENTS.md:175`. |

CONFIRMED SOUND, recorded because a review that only lists defects hides what it verified. The core
defect reproduces exactly as F-1 claims (exit 1, "NO matching finalize evidence in .aw/state/").
E-02's `HEAD..MERGE_HEAD` scoping works as specified (the range lists only the incoming finalize
commit). The worktree hazard E-01 exists for is real (`.git` is a FILE; `rev-parse --git-dir` resolves
correctly). The security-critical refusal case (c) refuses TODAY, so the plan's "must still refuse"
requirement is testable against real behavior. F-4 and F-13 are exact: all four commits are `R0xx`
renames (`R099`, `R099`, `R099`, `R098` as staged; `R061`/`R063`/`R061`/`R060` as merges) and the hook
handles `R` at `:118` with `-M` at `:108`. F-12 is exact: exactly ONE journal survives repo-wide, and
every cited `_clear_finalize_journal` line number is correct. OQ-01's timing explanation is
corroborated by the merge commit bodies themselves, which record `76gsmv` passing and the other three
being committed with `--no-verify` on maintainer authorization.

No finding was DEFERRED or left OPEN, so no `- Blocking: yes` escalation was required. OQ-03 is
`Blocking: no` by deliberate judgement (D-2), not to avoid a gate.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-101 shows the plan's premise is partly wrong. Is this a REPLAN, or repairable in place? | REPAIRABLE. Kept the plan and corrected what it claims: the fix is real and valuable for the HAND recovery path (where all four measured bypasses actually happened), only the frequency/urgency argument was false. | (a) `REJECT - NEEDS REPLAN`, rejected because the deliverable (in-tree evidence, plan-bound, incoming-side-only) is correct and unaffected; only prose about which path it covers was wrong. (b) Widen the plan to install `pre-merge-commit`, rejected as scope creep into contributor environment setup, and raised as OQ-03 instead. | `plan-review.md:227-229` (REPLAN only when unrepairable with bounded edits); measured hook behavior 2026-09-07 | yes |
| D-2 | Should OQ-03 (the automated-merge hole) be `Blocking: yes`? | NO, `Blocking: no`. | Making it blocking, rejected on evidence: the hole is PRE-EXISTING and this child does not widen it, nothing in the plan depends on the answer, and the detector fails CLOSED so a later `pre-merge-commit` install tightens rather than breaks the gate. Blocking a strict improvement on a pre-existing wider gap would be the false-refusal failure mode. | F-14; the plan's own fail-closed requirement; `plan_readiness.has_unresolved_blocking_question` semantics | yes |
| D-3 | My review of `cczotj` broke a real-corpus test. Fix my own prior artifact while reviewing a different plan? | YES, corrected the `cczotj` history line in this pass and verified the suite returned to the documented baseline. | Leaving it for a later pass, rejected because it is MY defect introduced minutes earlier, it fails a test in the shared checkout that any concurrent agent would then inherit, and the fix is one line that does not alter the review's verdict or readiness (`is_plan_review_approved` still False, the blocking question still stands). | `tests/test_plan_readiness.py:789-798`; verified `1 failed, 5613 passed` after the fix | yes |
