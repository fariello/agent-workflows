# IPD: Isolate a review turn in a worktree too so no turn writes to the shared checkout

- Date: 2026-09-13
- Kind: child
- Concern: A review turn is explicitly excluded from worktree isolation by six separate `not is_review` guards, so it runs in the shared checkout and COMMITS there mid-run: an edit to the plan plus a new review record. That is the same mid-run write to main that Orders 03 and 04 remove for other actors, and it escaped the 2026-09-13 outage only because the pre-launch gate also exempts reviews, not because it is safe.
- Scope: Give a review turn the same worktree isolation an execute turn gets, so its plan edit and review record land via one merge. Excludes the review SESSION sharing (which must stay shared), the auto-approve step, and the validation/integration gates a review legitimately skips. Excludes Orders 01 to 04.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: none
- Status: to-review
- Set: dirtygates
- Order: 5
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: ajxr5d
- Priority: medium
- Work-Kind: bug

## Workflow history

- 2026-09-13 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-09-13 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored after the maintainer asked whether reviews should be isolated too. They should: a review commit in main was found in tonight's history (`a9510164`), proving a review is not read-only with respect to the tree.

## Goal

Make the answer to "does this turn write to the shared checkout?" the same for every action type: no. A review's two output files should arrive on main as one merge, exactly as an execute turn's commits do.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: separate the exclusions that are about the TREE from the ones that are not

- [ ] E-01 Classify all six `not is_review` guards before changing any of them, and record the classification in this plan. They are NOT one decision. `:6122` (pre-launch clean-base gate) and `:6279` / `:6519` (lane-relative plan and prompt paths) are about the TREE and are in scope. `:6151` (self-finalize: begin/finalize lifecycle transitions), `:6572` (post-turn validation of an executed disposition) and `:6665` (integration gate relevance) are about the LIFECYCLE and are correctly review-exempt, because a review produces no executed disposition to validate or integrate. Changing a lifecycle exclusion by mistake would make a review attempt a transition it must not perform.
  - Depends on: none
  - Expected outcome: a written table of the six sites, each marked tree-related (change) or lifecycle-related (leave), with its reason.
  - Execution state: pending
- [ ] E-02 Allocate a lane for a review turn and run the turn inside it, reusing the existing `wt_handle` / `work_dir` machinery rather than adding a second isolation path. `work_dir = str(wt_handle.path)` at `:6199` is the existing seam. The lane-relative plan resolution at `:6279` exists because of a MEASURED incident (run `run-20260831T153226Z-3424176`, plan `y6mfgo`): the prompt carried MAIN's absolute plan path and no statement of isolation, and the agent read `../../../DECISIONS.md` and committed 18 files into MAIN while the lane stayed at zero commits. A review turn must get the same lane-relative plan path and the same explicit statement that it is in a lane, or it will reproduce that incident.
  - Depends on: E-01
  - Expected outcome: a review turn's cwd, plan path and prompt all refer to the lane, and MAIN's `git status --porcelain` is unchanged for the whole turn.
  - Execution state: pending

### Task group 2: land the review output through the merge

- [ ] E-03 Integrate a review lane back to main as one merge, by WIDENING `integrate_lane_branch` to take an explicit action kind and SKIP the revalidation gate for a review (OQ-01, resolved). A review's output is two files, both scoped to one plan: the plan itself (revisions applied) and the review record, measured on commit `a9510164` which holds exactly `M .aw/records/plans/pending/...tgop8e...ipd.md` and `A .aw/records/reviews/...tgop8e...review.md`. Keep steps 3 and 4 of that function (`:1035-1063`) fully shared, because they carry the `--ff-only`-then-`--no-ff` sequence whose ff failure is the expected "main advanced" case, the capture-conflicted-paths-BEFORE-abort ordering, and the `host_label` merge subject. THE HARD CONSTRAINT: the action kind must be an EXPLICIT parameter and the docstring must state that a review is merged without revalidation because it produces nothing to revalidate. Do NOT pass a synthetic "validation passed" value into the gate; that is a forged attestation, not a skip.
  - Depends on: E-02
  - Expected outcome: a review's two files reach main via a single merge, or not at all, and the function declares rather than implies that revalidation was skipped.
  - Execution state: pending
- [ ] E-04 Preserve the SHARED REVIEW SESSION. Both the CLI help (`:7688`, `:7699`) and the sweep (`:7728`) state that every review in a run shares one OpenCode session "for continuity", and that is a deliberate property this plan must not break. Isolating the TREE must not isolate the SESSION. Note the interaction to verify explicitly: `run_opencode` drops the `--session` argument when a turn is isolated (`:5405`, `session = None if (fresh_session or isolated_turn or is_rotation)`), with a recorded incident (`lanesess xd9sll`) behind it. So isolating reviews naively would silently end session sharing for the whole review sweep. Resolve that conflict explicitly rather than accepting whichever behavior falls out.
  - Depends on: E-02
  - Expected outcome: reviews still share one session across the sweep, and the reason isolation does not break it is recorded.
  - Execution state: pending

### Task group 3: keep the review-only steps working, and parity

- [ ] E-05 Keep the auto-approve step correct. `:6926` clears a reviewed plan to `execute` under `--full-auto`, reading the plan via `resolve_plan_path(repo, ...)` against MAIN. After isolation the freshly reviewed plan is on the lane until the merge lands, so this must read the plan AFTER integration, or read it from the right tree. Getting this wrong makes auto-approve either read a stale plan or fail to find the review evidence, and the shared predicate is deliberately fail-closed, so the visible symptom would be reviews that never auto-approve.
  - Depends on: E-03
  - Expected outcome: `--full-auto` still promotes a cleanly reviewed plan, reading the post-merge state.
  - Execution state: pending
- [ ] E-06 Mirror on `agy_runipd.py` and add the regression: a review sweep of at least three plans, with a deliberately dirty unrelated tracked path in the shared checkout, where all three reviews complete, MAIN's `git status --porcelain` is empty at every item boundary, and each review's two files arrive in main. Assert the session was shared across the three.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: both hosts isolate reviews identically and the properties above are pinned.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A WORKER may commit facts about its own item; only the COORDINATOR may commit facts about a Set. A review is a fact about ONE plan, so a worker-side lane is the right home for it, exactly as Order 03 argues for the backlog close.
- `is_review` is overloaded: it currently gates both tree decisions and lifecycle decisions. E-01 exists because that overload is the main hazard in this change.
- Reviews are exempt from the pre-launch clean-base gate (`:6122`), which is why they kept running while 68 execute items were refused on 2026-09-13. The exemption is an accident of scope, not a safety argument.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | A review is NOT read-only with respect to the repository. It edits the plan and adds a review record, and commits both to main. | commit `a9510164`: `M .aw/records/plans/pending/...tgop8e...ipd.md`, `A .aw/records/reviews/...tgop8e...review.md` |
| F-2 | Reviews are excluded from isolation by six separate guards, mixing two unrelated concerns. | `oc_runipd.py:6122`, `:6151`, `:6279`, `:6519`, `:6572`, `:6665` |
| F-3 | Reviews escaped the 2026-09-13 outage by EXEMPTION, not by being safe. The pre-launch gate that refused 68 execute items also skips reviews, and the two large runs that night happened to contain zero review items (38 execute + 3 orchestrate; 36 execute + 7 orchestrate). | run `run-20260913T031148Z-1722898`, run `run-20260913T031521Z-1774617` |
| F-4 | Isolation is CHEAP to get wrong in a way that writes to main. A previously measured incident had an unisolated-looking prompt cause an agent to commit 18 files into MAIN while its lane stayed empty, which is why the lane-relative plan path and the explicit in-lane statement exist. | the comment at `oc_runipd.py:6275-6279`, citing run `run-20260831T153226Z-3424176` and plan `y6mfgo` |
| F-5 | Isolation currently FORCES a fresh session, so naive isolation would silently break the review sweep's shared-session property. | `oc_runipd.py:5405` drops `--session` when `isolated_turn`, with incident `lanesess xd9sll` recorded at `:5383-5390`; sharing is promised at `:7699` |
| F-6 | The reward here is smaller than for execute turns, and that is worth stating. A review is read-only against the CODE and cheap to re-run, so a failed merge costs one turn rather than lost work. The case for this plan is UNIFORMITY (one answer to "does a turn write to main?") plus removing a mid-run writer, not protecting expensive output. | judgement, recorded so review can weigh scope against benefit |

## Proposed changes (ordered, validatable)

1. Classify the six `not is_review` guards into tree-related and lifecycle-related (E-01).
2. Allocate a lane for a review and run the turn in it, with lane-relative plan path and prompt (E-02).
3. Land the review's two files via one merge, deciding honestly whether the execute integration path fits (E-03).
4. Preserve the shared review session against the isolation-forces-fresh-session rule (E-04).
5. Fix auto-approve to read the post-merge plan (E-05).
6. Mirror on agy and pin the properties with a three-review regression (E-06).

## Deferred / out of scope (with reason)

- The lifecycle exclusions at `:6151`, `:6572` and `:6665`. Correctly review-exempt: a review performs no begin/finalize transition, produces no executed disposition to validate, and has nothing to integrate under the execute gate. E-01 records this rather than changing it.
- Making isolation mandatory for all actions. That is the orchestrator's OQ-01 and a separate judgement; this plan changes the DEFAULT behavior for reviews only and leaves `--no-isolate-worktree` working.
- Changing what a review produces, or the review record format. Out of scope entirely.

## Scope check

- Over-scope: none. Two runner files and their tests.
- Under-scope: this plan does not remove the `is_review` overload itself (one flag still answering two questions). E-01 documents the split without refactoring it. Say so at review if the refactor is wanted; it would be a separate plan and a larger diff.

## Required tests / validation

- The three-review regression of E-06: all three complete, MAIN clean at every boundary, each review's two files in main, session shared.
- A test proving a review's plan edit and review record arrive TOGETHER (one merge), and that a failed merge leaves neither in main and the plan unrevised.
- A test proving the lane-relative plan path and the in-lane statement are present in a review prompt, which is the direct regression for F-4.
- A test proving `--full-auto` still promotes a cleanly reviewed plan after isolation (E-05).
- A test proving the lifecycle exclusions still hold: a review performs no begin/finalize and triggers no integration gate.
- Both hosts. Full suite run bare, with the failure set diffed against a baseline from the same commit.

## Spec / documentation sync

- Update the CLI help text at `:7699` if the session behavior changes at all; it currently promises a shared session, and that promise must remain true or be corrected.
- No spec amendment is expected: isolation for execute turns came from `driverfin-02 (emus4n)` and no requirement found so far mandates that reviews stay unisolated. VERIFY BEFORE EXECUTING, and if a requirement does, amend that spec in this plan and add the spec file to `Scope-Paths` first.

## Open questions

### OQ-01: Does a review lane reuse `integrate_lane_branch`, or need a narrower merge path?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-13 by the maintainer: WIDEN `integrate_lane_branch` to know about reviews, so there is ONE integration function and a review skips only the revalidation step. E-03 takes that branch.

  THE AUTHOR INITIALLY LEANED THE OTHER WAY (a separate, clearly-named review merge path) and reading the function changed that view; the reversal is recorded so a later reader does not assume the alternative went unconsidered. The argument that decided it: `integrate_lane_branch` (`runner_shared.py:1000-1063`) is four steps, and only ONE is execute-specific. Step 1 is the dirty-overlap check, which Order 02 deletes outright. Step 2 is the merge-and-revalidate gate, the only part a review has no input for. Steps 3 and 4 are the actual merge and they are NOT thin: they carry three pieces of hard-won knowledge that a second implementation would have to duplicate or would get subtly wrong. First, `--ff-only` failing is the EXPECTED "main advanced" case and its output is deliberately discarded so it never reaches the operator-facing reason. Second, conflicted paths must be captured BEFORE `git merge --abort`, because the abort clears the index state they live in. Third, the merge subject carries `host_label` so history attributes to the right driver. That is genuine shared mechanism, and this repository's anti-re-fork discipline applies to it.

  THE LINE THAT MUST HOLD, and it is the whole reason this question was blocking: skip the gate EXPLICITLY, never satisfy it with a fake value. Passing a synthetic "validation passed" into the revalidation gate would be a forged attestation of the same family as a hand-written `- Readiness:`. Skipping revalidation for an action that produces nothing to revalidate is simply true, and it must be stated in the function's signature (an explicit action kind, not an inferred one) and in its docstring, so the contract is declared rather than quietly conditional. An implicit mode is how `dirty_tree_overlap` came to imply an authority its behavior did not have.

### OQ-02: Should a review lane be per-review or one lane for the whole sweep?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: per-review lanes give each review an independent merge, so one bad review cannot block the others, at the cost of N worktree allocations for N reviews. One lane for the sweep matches the shared-session model and costs one allocation, but couples the reviews: a merge failure would strand all of them. Non-blocking because either satisfies every V-item; the author leans per-review for independence, consistent with how execute items work, and because worktree allocation is cheap on this repository (though see the maintainer's separate question about very large repositories).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the six-site classification table, each marked tree or lifecycle with its reason, and confirm the three lifecycle sites are unchanged in the final diff.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste MAIN's `git status --porcelain` sampled DURING a review turn (not only after), showing it empty. Paste the review prompt showing the lane-relative plan path and the explicit in-lane statement, which is the F-4 regression.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the merge commit's `--name-status` showing both the plan edit and the review record in ONE merge. Paste a forced merge-failure case showing NEITHER file in main and the plan still unrevised. Paste the widened signature and docstring proving the action kind is an EXPLICIT parameter and that the skip is stated, then paste a `grep` of the review path showing NO synthetic validation value is constructed or passed to the gate. Also paste an execute-path test proving revalidation still runs for execute turns, so the widening did not weaken the gate it shares.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste evidence that three reviews in one sweep shared ONE session id, with isolation active. Paste the reasoning or code showing how this coexists with the isolation-drops-`--session` rule at `:5405`.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste a `--full-auto` run where a cleanly reviewed plan is promoted to `execute` after isolation, and the recorded `auto-approved` marker. A review that silently fails to auto-approve is the expected symptom of getting this wrong, so a negative case must also be shown to fail loudly rather than silently.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the three-review regression output for BOTH hosts, including the dirty-unrelated-path case, and paste the bare full-suite counts before and after with the FAILED-set diff.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files this plan changed, path-scoped, never `git add -A`, never push. Paste actual runner output for every test claim. OQ-01 is BLOCKING and must be answered before E-03 is written. Do not resolve OQ-01 by passing a synthetic validation result into the integration gate.

Post-gate lifecycle move: this plan reaches `executed/` only when every V-item above carries pasted evidence and `aw ipd lint --phase pre-transition` reports conforming.
