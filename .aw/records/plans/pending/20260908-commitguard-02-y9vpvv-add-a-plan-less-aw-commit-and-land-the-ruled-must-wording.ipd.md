# IPD: Add a plan-less aw commit and land the ruled MUST wording

- Date: 2026-09-08
- Kind: child
- Concern: The maintainer ruled on 2026-09-01 that the commit contract must say agents MUST use the tooled path, not PREFER it, and supplied the exact replacement wording. That wording cannot land honestly yet for two reasons. FIRST, `aw commit` REQUIRES a plan selector, so every plan-less commit (a backlog item, a spec edit, a typo fix) has no tooled path to comply with, which would make non-compliance the COMMON case and trains agents to ignore the rule. SECOND, the ruled wording contains a DESCRIPTIVE sentence about a hook-rewrite retry that the code does not yet perform, so shipping it early would make the contract installed into every managed repo document behavior that does not exist.
- Scope: Close the gap, then land the wording. IN: a plan-less commit mode so the MUST is compliable, and the ruled replacement of the two `engine.py` paragraphs with the retry sentence gated on its prerequisite. OUT: the agent-context detector, any new guard, and gate wiring (sibling Order 01 owns that).
- Scope-Paths: agent_workflows/work_cmd.py, agent_workflows/cli.py, agent_workflows/engine.py, AGENTS.md, tests/test_work_commit.py
- Item-Dependencies: executed:lqly9m
- Status: to-review
- Set: commitguard
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: y9vpvv
- From-Backlog: wjl471

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `wjl471`. GATE NOTE: this item carries NO `- Blocks-Release:`, so this plan inherits none. THIS IS ORDER 02 of a two-child Set; sibling `kbqpkn` (Order 01) wires the four unwired gates and is independent. THE HARD ORDERING CONSTRAINT IS REAL, IS THE ITEM'S OWN, AND IS NOW SATISFIABLE: the item states that the retry sentence in the ruled wording is DESCRIPTIVE and "MUST NOT ship before `egqt32` layer 1 (the bounded single retry in `git_commit_helper.offer_commit`) lands, or the contract installed into every managed repo would document behavior the code does not have." `egqt32` has since been GRADUATED and its plan exists: `.aw/records/plans/pending/20260908-hookretry-01-lqly9m-...ipd.md`, carrying `From-Backlog: egqt32`, so this plan declares `Item-Dependencies: executed:lqly9m` to make that constraint machine-readable rather than prose. NOTE FOR THE EXECUTOR, because it changes where the retry lives: `lqly9m` found that the item's premise about WHERE the retry goes is obsolete. `offer_commit` no longer performs the commit itself; it delegates to `commit_lock.commit_isolated`, so the retry lands there. The ruled wording says "it re-stages that path and retries ONCE", which stays TRUE of the tooled path as a whole regardless of which layer performs it, so the sentence needs no change, but E-05 must VERIFY the shipped behavior matches the sentence rather than assuming. THE PLAN-LESS GAP IS CONFIRMED LIVE at HEAD `a2e0438a`: `work_cmd.py:138` returns "a <plan> selector is required", so `aw commit` without a plan exits before doing anything. THE ITEM'S EVIDENCE THAT THE HELPER NEVER NEEDED A PLAN ALSO VERIFIES: `offer_commit` takes no plan argument and there are 8 call sites of it across the package that pass none, and `run_commit` uses the plan for exactly two things, the `Scope-Paths` refusal (`work_cmd.py:436-452`) and the engine validation (`:459-465`). CRUCIALLY the graceful-degradation path the item points at is real and is the shape a plan-less mode should reuse: when a plan declares no `Scope-Paths`, `run_commit` prints "note - plan declares no Scope-Paths allowlist; committing the requested paths without scope enforcement" (`:454-458`) and PROCEEDS, so plan-less is that same path with a reworded notice rather than a new code path.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the ruled MUST compliable before making it mandatory. An agent told it MUST commit through `aw commit` needs a form of `aw commit` that fits every legitimate commit, and the contract must not describe a retry the code does not perform.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the MUST compliable

- [ ] E-01 Add a PLAN-LESS commit mode, so a backlog item, a spec edit or a typo fix has a tooled path. The item asks this be decided here and suggests a shape without prescribing it: `aw commit --no-plan -m <msg> -- <paths>`, or a sibling verb. IMPLEMENT `--no-plan` on the existing verb rather than a new verb, because the behavior is identical apart from two skipped checks and a second verb would duplicate the argument surface, the locking and the outcome reporting. Reuse the EXISTING graceful-degradation path rather than writing a new branch: when a plan declares no `Scope-Paths`, `run_commit` already prints a notice and proceeds without scope enforcement (`work_cmd.py:454-458`), so plan-less is that same flow with a reworded notice. The selector requirement to relax is at `work_cmd.py:138` ("a <plan> selector is required").
  - Depends on: none
  - Expected outcome: `aw commit --no-plan -m <msg> -- <paths>` commits the named paths through `offer_commit` with no plan, printing a notice that scope enforcement is skipped; omitting BOTH a plan and `--no-plan` still refuses as today.
  - Execution state: pending

- [ ] E-02 Keep the two plan-derived protections OFF only where they cannot apply, and say so out loud. `run_commit` uses the plan for exactly two things: the `Scope-Paths` refusal (`work_cmd.py:436-452`) and the engine validation of the plan itself (`:459-465`). Both are meaningless without a plan, so `--no-plan` skips both, and that is a REDUCTION in safety that must be visible rather than silent: print which protections were skipped, in the same spirit as the existing no-Scope-Paths notice. CRITICALLY, do NOT let `--no-plan` weaken the protection that has nothing to do with plans: `offer_commit`'s snapshot-then-intersect is what structurally prevents sweeping a concurrent agent's staged edits into your commit, and the item is explicit that this is "the ONLY mechanism in the repo that STRUCTURALLY prevents" that. Plan-less mode must still route through `offer_commit` with explicit paths, never through a raw `git commit`.
  - Depends on: E-01
  - Expected outcome: the skipped protections are named in the output; a co-worker's staged file is still excluded from a `--no-plan` commit, demonstrated.
  - Execution state: pending

- [ ] E-03 Refuse the AMBIGUOUS invocation rather than guessing. Decide and implement what happens when a plan selector AND `--no-plan` are both given: that is a contradiction, so it must be a usage error with exit 2, not a silent precedence rule, for the same reason the sibling `--color`/`--no-color` pair is mutually exclusive. Also decide the `-m` requirement: `aw commit <plan>` derives its message from the plan, so a plan-less commit has no message source and `-m` must be REQUIRED under `--no-plan`; refuse without it rather than committing with a placeholder.
  - Depends on: E-01
  - Expected outcome: plan plus `--no-plan` exits 2; `--no-plan` without `-m` exits 2; both refusals name the problem.
  - Execution state: pending

### Task group 2: land the ruled wording, in order

- [ ] E-04 Replace the `engine.py` paragraph with the maintainer's RULED WORDING VERBATIM, and treat it as dictated text rather than as a draft to improve. The target is the "PREFER THE TOOLED COMMIT PATH" paragraph (`agent_workflows/engine.py:1252-1256`, rendered at `AGENTS.md:60`), whose current "immune to this by construction" claim the item shows is true for index pollution and FALSE for auto-fix rejection. The ruled replacement is quoted in the backlog item and must be used as given: it opens "USE THE TOOLED COMMIT PATH. You MUST commit through `aw commit`, not raw `git commit`." and ends with the reporting obligation "If no form of `aw commit` fits your case, you MUST say so explicitly in your report, naming what you ran and why, and re-verify the staged set as above." PRESERVE THE ESCAPE HATCH AS A REPORTING OBLIGATION, NOT PERMISSION: the item is explicit that this is what makes it enforceable, because a silent raw `git commit` becomes a visible contract violation while a declared one is auditable. Regenerate `AGENTS.md` through `engine.py`; never hand-edit the managed block.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `engine.py` carries the ruled wording verbatim and `AGENTS.md`'s managed block renders it; the reporting-obligation sentence is present.
  - Execution state: pending

- [ ] E-05 VERIFY THE DESCRIPTIVE SENTENCE IS TRUE BEFORE SHIPPING IT, which is the hard ordering constraint made concrete. The ruled wording asserts "When a MUTATING hook rewrites one of your own paths and rejects, it re-stages that path and retries ONCE, so whitespace or format churn costs you no round trip and no re-verify." That is DESCRIPTIVE, and the item forbids shipping it before the retry exists. This plan declares `Item-Dependencies: executed:lqly9m` for that reason. At execution time, PROVE the behavior rather than trusting the dependency: run the scratch reproduction (a hook that strips trailing whitespace and exits nonzero) through `aw commit` and show it succeeds on the retry with the rewritten path included. IF THE RETRY IS NOT PRESENT, DO NOT SHIP THE SENTENCE: land the MUST imperative (which the item says carries no such dependency) and hold the retry sentence, reporting why. Note `lqly9m` places the retry inside `commit_lock.commit_isolated` rather than `offer_commit`, so verify by BEHAVIOR through the tooled path, not by grepping one function.
  - Depends on: E-04
  - Expected outcome: either the retry is demonstrated and the full ruled wording ships, or the retry is absent and the descriptive sentence is withheld with the reason recorded.
  - Execution state: pending

- [ ] E-06 Apply the COMPANION NARROWING the ruling also specifies, to the paragraph immediately above. The target is "RE-VERIFY AFTER A FAILED HOOK" (`agent_workflows/engine.py:1246-1251`, rendered at `AGENTS.md:58`), which currently charges the re-verify after EVERY failed attempt including tooled ones, and never mentions that a mutating hook also REWROTE the file. Retitle it to "RE-VERIFY AFTER A FAILED RAW COMMIT", scope it to raw `git commit`, and add the one specified sentence: "A MUTATING hook (whitespace or eof fixer, formatter) also REWRITES your file and then rejects, so your retry must re-stage the rewritten path." KEEP THE `git reset`/`git stash` PROHIBITION VERBATIM: the ruling is explicit that it "stays VERBATIM; it is about a co-worker's work and is unrelated to this change." That prohibition protects a concurrent agent and must not be softened while narrowing the paragraph's scope.
  - Depends on: E-05
  - Expected outcome: the paragraph is retitled and scoped to raw commits with the specified sentence added, and the reset/stash prohibition is byte-identical.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `AGENTS.md` is GENERATED from `engine.py`'s managed block and must never be hand-edited; the block is installed into every managed repo, which is why a descriptive claim there is a claim about every consumer's tooling, not just this repo's.
- `offer_commit` takes NO plan argument and is already used plan-lessly at 8 call sites across the package, so a plan-less mode is a CLI-surface gap rather than a helper limitation.
- `run_commit` already degrades gracefully when a plan declares no `Scope-Paths`: it prints a notice and proceeds without scope enforcement. That is the precedent shape for `--no-plan`.
- `offer_commit`'s snapshot-then-intersect is the ONLY structural protection against sweeping a concurrent agent's staged edits into your commit, so no mode may bypass it.
- The maintainer's ruling distinguishes IMPERATIVE from DESCRIPTIVE text: a MUST is a command and its validity does not wait on the tooling being total, while a descriptive sentence must be true when it ships. That distinction drives the E-04/E-05 split.
- The ruling also states the truthfulness constraint applies ONLY to descriptive sentences, which is why the MUST may land even if the retry is delayed.
- `egqt32`'s retry moved layer since the ruling was written: `offer_commit` now delegates the commit to `commit_lock.commit_isolated`, so the retry lands there. Verify by behavior through the tooled path.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | THE PLAN-LESS GAP IS LIVE: `aw commit` refuses without a plan selector, so a plan-less commit has no tooled path. | `work_cmd.py:138` ("a <plan> selector is required") at `a2e0438a` |
| F-2 | The helper never needed a plan: `offer_commit` takes no plan argument and 8 call sites in the package use it plan-lessly. | measured at `a2e0438a` |
| F-3 | The plan is used for exactly TWO things, both meaningless without it: the `Scope-Paths` refusal and the plan's engine validation. | `work_cmd.py:436-452`, `:459-465` |
| F-4 | The graceful-degradation precedent exists and is the shape to reuse: a plan with no `Scope-Paths` prints a notice and proceeds. | `work_cmd.py:454-458` |
| F-5 | The paragraph to replace still carries the claim the item shows is half-false. | `engine.py:1252-1256`, rendered `AGENTS.md:60` |
| F-6 | The companion paragraph still charges the re-verify after EVERY failed attempt and never mentions the rewrite. | `engine.py:1246-1251`, rendered `AGENTS.md:58` |
| F-7 | THE ORDERING PREREQUISITE IS NOW GRADUATED, so the constraint is satisfiable: `egqt32` has plan `lqly9m` carrying `From-Backlog: egqt32`. | `.aw/records/plans/pending/20260908-hookretry-01-lqly9m-...ipd.md` |
| F-8 | The retry's LAYER moved since the ruling was drafted, so E-05 must verify by behavior: `offer_commit` delegates the commit to `commit_lock.commit_isolated`, and `lqly9m` places the retry there. | `lqly9m`'s Concern and workflow history |
| F-9 | The MUST imperative carries no dependency and could ship alone, which is the fallback if the retry is absent. | the ruling's own words: "The MUST IMPERATIVE itself carries no such dependency and could ship immediately" |
| F-10 | Making non-compliance the common case is a recorded harm, which is why E-01 precedes E-04: a rule that fires on correct behavior trains agents to ignore it. | the item's citation of `gjadwm:45-49` |

## Proposed changes (ordered, validatable)

1. Add `--no-plan` reusing the existing no-Scope-Paths flow (E-01).
2. Name the skipped protections and keep the concurrency protection intact (E-02).
3. Refuse plan-plus-`--no-plan` and `--no-plan` without `-m` (E-03).
4. Replace the PREFER paragraph with the ruled MUST wording verbatim and regenerate AGENTS.md (E-04).
5. Prove the retry exists before shipping the descriptive sentence, or withhold it (E-05).
6. Apply the companion narrowing, keeping the reset/stash prohibition verbatim (E-06).

## Deferred / out of scope (with reason)

- THE AGENT-CONTEXT DETECTOR AND THE NEW GUARD (the item's Finding 1, OQ-1 through OQ-4). A separate design with four open questions about where the guard lives, what accident it catches, how it phrases refusal, and how an override is audited. This plan implements the maintainer's WORDING ruling and the gap that ruling exposed, nothing more.
- WIRING THE FOUR UNWIRED GATES. Sibling Order 01 (`kbqpkn`) owns that; it is independent and needs no contract change.
- `mjx7ne`'s `commit_gateway` / `deny_push` CAPABILITIES. Separate open item.
- ENFORCING the MUST mechanically (intercepting raw `git commit`). The ruling makes the escape hatch a REPORTING obligation deliberately, because that is enforceable where an absolute MUST with no exit is not. Building an interceptor is the guard question, deferred above.
- CHANGING THE `git reset`/`git stash` PROHIBITION. The ruling says it stays verbatim; E-06 preserves it.

## Scope check

- Over-scope: `AGENTS.md` is in `Scope-Paths` although it is GENERATED. It is listed because the regenerated file is committed with the change; the edit itself must be made in `engine.py` and the file regenerated, never hand-edited.
- Under-scope: the guard, the detector and the gate wiring are all out. This plan delivers the contract half plus the tooling gap it depends on.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_work_commit.py tests/test_git_commit_helper.py` for the focused surface.
- A real `aw commit --no-plan` against a fixture repository, committing a file with no plan, with the resulting commit and its file list pasted.
- The concurrency check from E-02: a co-worker's staged file present, a `--no-plan` commit of different paths, and proof the co-worker's file is not in the commit.
- The retry demonstration from E-05 through the tooled path, or the recorded reason the sentence was withheld.
- A diff of the regenerated `AGENTS.md` managed block showing both paragraphs changed as ruled.

## Spec / documentation sync

This plan's PRIMARY DELIVERABLE IS DOCUMENTATION, so the sync is the work rather than an afterthought. `agent_workflows/engine.py`'s managed block is the source of `AGENTS.md` and is installed into every managed repo, so both edits must be made there and the file regenerated; hand-editing `AGENTS.md` would be reverted by the next install and would also violate the repository's own rule that the block is generated. No `.spec.md` file governs the commit contract, so none is declared in `Scope-Paths`. TWO honesty obligations. FIRST, the wording is DICTATED by a recorded maintainer ruling: reproduce it verbatim and do not improve it, because a reworded ruling is no longer the ruling. SECOND, the descriptive retry sentence must be true at ship time (E-05); if it is not, ship the imperative alone and record the omission, since the whole reason the item states a hard ordering constraint is to stop the contract describing behavior the code lacks. `CONTRIBUTING.md` also describes the commit path and must be checked for consistency with the new MUST; if it says PREFER, it enters the fence.

## Open questions

### OQ-01: Should `--no-plan` be a flag on `aw commit` or a sibling verb?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: DECIDED IN THE PLAN as a flag, with the reasoning recorded so a reviewer can overrule cheaply. The item offers both shapes. A flag wins because the two paths differ only in skipping two plan-derived checks: everything else (path scoping, the writer lock, the isolated commit, the outcome reporting, the trailers) is identical, so a sibling verb would duplicate the whole argument surface and create two places for a future commit-path change to land. The counter-argument a reviewer may prefer: a distinct verb makes the reduced-safety mode impossible to reach by accident, whereas a flag can be added to a habitual command without thought. If that matters more, the implementation is equivalent work either way.

### OQ-02: Should a plan-less commit be RECORDED as an exception even after `--no-plan` exists?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED, leaning NO, and it decides how the ruled wording reads in practice. The ruling's escape hatch is a reporting obligation for when "no form of `aw commit` fits your case". Once `--no-plan` exists, a plan-less commit IS a form of `aw commit`, so it is compliant and needs no exception report; that is precisely the gap-closing the ruling asks for. The alternative view: plan-less mode skips scope enforcement, so a maintainer may want its use surfaced in reports anyway to see whether plan-less commits are becoming a habit. If that is wanted, it is a reporting convention rather than a code change, and it should be stated in the wording rather than left implicit.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a real `aw commit --no-plan -m <msg> -- <path>` run in a fixture repository, its UNPIPED exit code, the printed notice, and `git show --stat` of the resulting commit showing exactly the named path. Paste `aw commit` with NEITHER a plan nor `--no-plan` still refusing, so the relaxation is shown to be opt-in.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the output naming the skipped protections. Then paste the concurrency demonstration: a co-worker's file staged, a `--no-plan` commit of DIFFERENT paths, `git show --stat` proving the co-worker's file is absent, and `git status --porcelain` proving it is still staged/dirty afterwards.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste both refusals with their UNPIPED exit codes and messages: a plan selector together with `--no-plan`, and `--no-plan` without `-m`. Both must be 2.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `engine.py` diff and the regenerated `AGENTS.md` diff side by side, showing the ruled wording reproduced VERBATIM including the reporting-obligation sentence. Paste a character-level comparison (or a diff against the quoted text) proving it was not paraphrased. Confirm `AGENTS.md` was regenerated, not hand-edited.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the scratch reproduction through the TOOLED path: a hook that rewrites a staged file and exits nonzero, then `aw commit` succeeding on the retry with the rewritten content in the commit. If the retry is ABSENT, paste that finding instead and paste the shipped wording showing the descriptive sentence was WITHHELD while the imperative landed. State which outcome occurred.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the retitled paragraph as rendered in `AGENTS.md`, showing it is scoped to raw `git commit` and carries the specified mutating-hook sentence. Paste a byte-comparison of the `git reset`/`git stash` prohibition before and after proving it is UNCHANGED. Paste the bare `python3 -m pytest` summary line and compare it to the stated baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened.

It carries `Item-Dependencies: executed:lqly9m` deliberately, encoding the backlog item's own hard ordering constraint: the ruled wording's retry sentence is DESCRIPTIVE and must not ship before the retry exists. E-05 re-proves that at execution time rather than trusting the edge, and provides the documented fallback (ship the imperative, withhold the sentence) if the retry is absent.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE TWO HAZARDS. FIRST, `AGENTS.md` is GENERATED: edit `engine.py` and regenerate, never hand-edit, or the next install reverts it. SECOND, this plan edits the commit contract and the commit verb it will itself use, so verify with `git diff --cached --name-only` before each commit and never reach for `--no-verify` to land a change whose purpose is to make the tooled path mandatory. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
