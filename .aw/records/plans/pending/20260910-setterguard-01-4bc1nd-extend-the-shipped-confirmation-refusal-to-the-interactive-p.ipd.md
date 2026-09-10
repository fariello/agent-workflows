# IPD: Extend the shipped confirmation refusal to the interactive path and refuse a backwards terminal transition

- Date: 2026-09-10
- Kind: child
- Concern: `aw ipd set` / `aw set` WRITE IMMEDIATELY from a human terminal, with no confirmation and no preview, and they will silently move a plan BACKWARDS out of a terminal disposition. MEASURED 2026-09-10 on this repository, by accident, while trying to REPRODUCE an unrelated error message: a bare `aw ipd set approved agentadhere` moved SEVEN plans out of `.aw/records/plans/executed/` into `pending/` and rewrote each `- Status: executed` to `approved`. It printed six `executed → approved` lines and exited 0. It was caught only by running `git status` out of caution, reverted with `git checkout`, and verified byte-identical to HEAD; nothing was committed. A less careful pass would have committed a fabricated regression of a completed six-phase plan Set.
  THE CONFIRMATION GATE ALREADY EXISTS AND IS UNREACHABLE FROM A TERMINAL, which is what makes this small to fix and embarrassing to leave. `status_set.py:1333` reads `if (ctx.is_agent or ctx.is_json) and not is_dry_run and not yes:` and then returns a structured refusal ("confirmation required (--yes needed to execute mutation)") complete with a change list and a `NextAction` naming the exact `--yes` command. So a MACHINE caller is protected and a HUMAN is not, which inverts the usual safety posture: the machine can parse a refusal and retry, while the human is the party who cannot undo a silent bulk write.
  AND THERE IS A GATE FOR ENTERING `executed` BUT NONE FOR LEAVING IT. `status_set.py:1312-1328` deliberately intercepts a PLAN moving TO `executed` and delegates into the gated `aw ipd finalize` transaction (begin receipt, scope reconciliation, three gates, attributed history, rollback). The reverse direction has no counterpart, so `executed -> approved` took the raw ungated path. `AGENTS.md` already forbids re-opening an executed plan in place and directs a corrective IPD instead, so the tool permits what the contract prohibits.
- Scope: The two missing speed bumps on the status setters. IN: extending the EXISTING confirmation refusal to the interactive (non-agent, non-json) path; refusing a backwards transition out of a terminal disposition (`executed`, `superseded`, `not-executed`) unless explicitly overridden, and naming the offending artifacts; a survey of in-repo callers that would newly be refused, with `--yes` added where the call is deliberate; regression fixtures for both. OUT: making `--dry-run` the DEFAULT for the setters (a larger behavior change deserving its own decision, recorded as deferred); anything about what a bare setid MEANS, since within-type fan-out is deliberate (`laykok` E-07) and correct; the history-message and durability defects (Order 02 of this Set).
- Scope-Paths: agent_workflows/status_set.py, tests/test_status_set.py
- Item-Dependencies: none
- Status: to-review
- Set: setterguard
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 4bc1nd
- From-Backlog: f5pttg

## Workflow history

- 2026-09-10 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `f5pttg`, which was filed after this defect fired ACCIDENTALLY during an unrelated cleanup. Every claim here was measured rather than reasoned: the unreachable-guard condition read at `status_set.py:1333`, the asymmetric forward-only `executed` gate at `:1312-1328`, and a MINIMAL ISOLATED REPRODUCTION in a scratch repo (two `executed` plans sharing a setid, one flagless command, both silently reverted and moved to `pending/`) so the fixture does not depend on this repository's corpus. ALSO SURVEYED, because it is the one real risk of fix 1 (F-4): the in-repo callers that would newly be refused. The runner drivers ALREADY pass `--yes` (`oc_runipd.py:763-772`, `:794-800`), and the only workflow-document mentions are PROSE about the forbidden `aw set executed` bypass rather than live invocations, so the blast radius is smaller than it first appears. That survey is the reason E-03 exists as its own item rather than as a footnote.
- 2026-09-10 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a destructive status mutation require one deliberate keystroke from a human, the way it already does from a machine, and make the setter refuse to walk a plan backwards out of a terminal state without being told to.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reach the guard that already exists

- [ ] E-01 EXTEND THE EXISTING CONFIRMATION REFUSAL TO THE INTERACTIVE PATH by removing the output-mode condition at `status_set.py:1333`, so the predicate becomes "not a dry run and not `--yes`" regardless of renderer. Do NOT write a new prompt or a new refusal: the refusal, its `exit_code=2`, its `Change` list and its `NextAction` hint are already built immediately below that line, and the human path should reach the SAME code so the two cannot drift. For the human renderer, the refusal must print the resolved artifact COUNT and the per-artifact `status: <old> -> <new>` detail before refusing, since the whole failure was not knowing the blast radius; the `changes` list already carries exactly that. KEEP `--dry-run` and `--yes` semantics unchanged. State in a comment WHY the condition was there and why it is wrong, so nobody restores it: a machine can parse a structured refusal and retry, a human cannot undo a silent bulk write, so gating on output mode protects the wrong party.
  - Depends on: none
  - Expected outcome: a flagless `aw ipd set approved <setid>` from a terminal REFUSES with exit 2, lists what it would change, and names the `--yes` form; with `--yes` it behaves exactly as before.
  - Execution state: pending

- [ ] E-02 REFUSE A BACKWARDS TRANSITION OUT OF A TERMINAL DISPOSITION unless explicitly overridden. Terminal for a plan is `executed`, `superseded`, `not-executed`. Mirror the SHAPE of the existing forward gate at `:1312-1328`, which keys on `record_type == "plans"` AND the NORMALIZED target status (deliberately not the raw token, because prompts share the `executed`/`done` tokens); key this one on the artifact's CURRENT status being terminal and the target being non-terminal. The refusal must NAME every offending artifact and its current status, and must point at the corrective-IPD route that `AGENTS.md` already prescribes for a post-execution gap rather than implying the transition is merely inconvenient. DECIDE AND RECORD the override's shape (a dedicated flag such as `--allow-terminal-reopen`, versus accepting `--force`): prefer a DEDICATED flag, because `--force` already means "act on an ambiguous multi-match" in this same code path (`:1250-1257`) and overloading it would make one flag mean two unrelated risks. Whatever you choose, state the reasoning in the code.
  - Depends on: E-01
  - Expected outcome: `aw ipd set approved <a setid whose plans are executed>` refuses even WITH `--yes`, names the executed plans, and cites the corrective-IPD route; the override performs it.
  - Execution state: pending

### Task group 2: do not break the callers

- [ ] E-03 SURVEY AND FIX THE IN-REPO CALLERS THAT WOULD NEWLY BE REFUSED, and treat this as the item that makes E-01 safe rather than as cleanup. A guard that starts refusing interactive calls will break any script, workflow document, hook or driver path that invokes a setter without `--yes`. MEASURED AT AUTHORING, so the executor is confirming rather than exploring (F-4): the runner drivers ALREADY pass `--yes` (`oc_runipd.py:763-772` and `:794-800` both include it), and the two `.aw/system/workflows/` hits are PROSE describing the forbidden `aw set executed` bypass, not live invocations. RE-RUN the survey rather than trusting that: grep `.aw/system/workflows/`, `agent_workflows/`, `tools/`, `Makefile` and any `.githooks`/`.pre-commit-config.yaml` for setter invocations, classify each as deliberate-automation (add `--yes`) or human-facing (leave it to refuse), and PASTE the classified list. If the survey finds a caller that CANNOT pass `--yes`, that is a finding to report, not a reason to weaken E-01.
  - Depends on: E-01
  - Expected outcome: a pasted, classified inventory of every in-repo setter call site; deliberate automation carries `--yes`; the full suite passes, proving no test depended on flagless interactive writes.
  - Execution state: pending

### Task group 3: pin both refusals

- [ ] E-04 PIN THE CONFIRMATION REFUSAL WITH THE MEASURED FIXTURE. Build the minimal isolated case from the reproduction: a scratch repo with two plans sharing one setid, then assert that a flagless interactive call WRITES NOTHING (statuses unchanged, files still in their original directory, exit 2) and that the same call with `--yes` performs the transition. ASSERT ON THE FILESYSTEM, not only the exit code: the original incident MOVED FILES between disposition directories, so a test that checks only the status bullet would miss half the damage. Include a `--dry-run` case proving it still previews without writing.
  - Depends on: E-01
  - Expected outcome: three cases (flagless refuses and writes nothing; `--yes` performs; `--dry-run` previews), each asserting both status text and file location.
  - Execution state: pending

- [ ] E-05 PIN THE TERMINAL-REOPEN REFUSAL, INCLUDING THE EXACT MEASURED INCIDENT. Assert that plans in `executed/` are NOT reverted by `aw ipd set approved <setid>` even with `--yes`, that the refusal names them, and that the override flag performs it. Then assert the transitions that MUST STILL WORK, because this guard is the one most likely to over-refuse: a nonterminal plan advancing (`to-review -> reviewed`, `reviewed -> approved`), a plan RETIRING (`reviewed -> superseded`, terminal but FORWARD, which this cleanup itself relied on three times), and a non-plan artifact's ordinary transition. A guard that blocks retirement would have blocked the very cleanup that found this bug.
  - Depends on: E-02
  - Expected outcome: the reopen is refused and named; advancing, retiring and non-plan transitions are all unaffected, each with its own assertion.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE REFUSAL MACHINERY IS ALREADY WRITTEN and returns a `CommandResult` with `changes`, `next_actions`, `verified=False` and `exit_code=2`. E-01 must route the human path INTO it, never duplicate it.
- THE FORWARD `executed` GATE IS THE SHAPE TO COPY (`:1312-1328`): it keys on `record_type == "plans"` plus the NORMALIZED target status, with an explicit comment that keying on the raw token would misfire because prompts share `executed`/`done`. E-02 inherits that care.
- `--force` IS ALREADY TAKEN in this code path, meaning "act on all of an ambiguous multi-match" (`:1250-1257`), which is why E-02 prefers a dedicated override flag.
- A BARE SETID LEGITIMATELY MEANS THE WHOLE SET for a mutating setter (`laykok` E-07 distinguishes setid fan-out from a unique-id collision from a substring match). This plan must NOT weaken that; it adds a speed bump, not a narrowing.
- `status_set.py` DOES NOT WRITE TO THE GLOBAL HISTORY SIDECAR (`grep -c record_history` -> 0), unlike `specs.py` and `backlog.py`. Relevant here only as a caution: do not assume a discarded or refused transition is recorded anywhere else. Order 02 of this Set owns that gap.
- SUITE BARE: `python3 -m pytest`. Compare failing NODE IDS, never totals. Known environmental failure in the primary checkout only: `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (a gitignored local `opencode-recovery/` dump); it passes in a clean worktree.

## Findings

| Id | Severity | Location (measured at HEAD) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `status_set.py:1333` | The confirmation gate is conditioned on `ctx.is_agent or ctx.is_json`, so it protects machine callers and not humans. The refusal it guards is fully built. | source read |
| F-2 | HIGH | `status_set.py:1312-1328` | There is a gate for moving INTO `executed` (delegating to `aw ipd finalize`) and NONE for moving out of it, so a terminal plan can be silently reverted. | source read |
| F-3 | HIGH | measured incident, 2026-09-10 | A flagless `aw ipd set approved agentadhere` moved 7 plans from `executed/` to `pending/` and rewrote their status; caught by `git status`, reverted, nothing committed. Reproduced minimally in a scratch repo (2 plans, same outcome). | the seven `executed → approved` lines; the scratch-repo BEFORE/AFTER showing `executed executed` -> `approved approved` and a new `pending/` dir |
| F-4 | MEDIUM | `oc_runipd.py:763-772`, `:794-800`; `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md:109,144` | The blast radius of E-01 is SMALL: the drivers already pass `--yes`, and the workflow-document hits are prose about the forbidden bypass, not invocations. This must be re-surveyed, not trusted. | grep of drivers and workflows |
| F-5 | MEDIUM | `AGENTS.md` execution contract | The contract already forbids re-opening an executed plan in place and directs a corrective IPD, so E-02 enforces a stated rule rather than inventing policy. | contract text |
| F-6 | LOW | `status_set.py:1250-1257` | `--force` already means "act on an ambiguous multi-match", so E-02 must not overload it for terminal reopen. | source read |

## Proposed changes (ordered, validatable)

1. E-01 routes the human path into the existing refusal and explains why the old condition was wrong.
2. E-02 adds the missing backwards-terminal guard, mirroring the forward gate's keying discipline.
3. E-03 surveys and fixes the callers, which is what makes E-01 safe to land.
4. E-04 pins the confirmation refusal on the filesystem, not just the exit code.
5. E-05 pins the reopen refusal AND the transitions that must keep working, including retirement.

## Deferred / out of scope (with reason)

- MAKING `--dry-run` THE DEFAULT for the setters: a bigger behavior change than either fix here, affecting every caller and every muscle memory, and it deserves its own decision. Fixes E-01 and E-02 remove the sharp edge without it. Recorded in backlog `f5pttg` as its third suggested fix.
- THE HISTORY-MESSAGE AND DURABILITY DEFECTS (`x6tk1u`, `hg2oop`): Order 02 of this Set. They touch the same setters but are a different failure (provenance loss, not unguarded mutation) and have different tests.
- WHAT A BARE SETID MEANS: deliberate (`laykok` E-07) and preserved.
- THE `aw backlog note` GAP: recorded in `hg2oop`; belongs with Order 02 if it is done at all.

## Scope check

- Over-scope: none. Both declared paths are touched by named items: `status_set.py` (E-01, E-02, and E-03's `--yes` additions if any land there) and `tests/test_status_set.py` (E-04, E-05).
- Under-scope: none remaining. E-03 was added because a guard that changes refusal behavior is not safe without a caller survey, and E-05's must-still-work assertions were added because an over-broad terminal guard would have blocked this very cleanup's three retirements.

## Required tests / validation

`python3 -m pytest` bare, in an isolated worktree, baseline measured there and pasted, compared by failing NODE ID rather than by total. Beyond the suite: the measured incident re-run in a SCRATCH repo before and after (never against real records, which is how this defect was discovered), with `git status --porcelain` pasted after each run proving what was and was not written; plus the E-03 classified caller inventory.

## Spec / documentation sync

NO SPEC IS AMENDED and none is declared in `- Scope-Paths:`. No spec governs setter confirmation behavior; the relevant rule is the `AGENTS.md` execution contract's prohibition on re-opening an executed plan, which E-02 ENFORCES rather than changes.

ONE DOCUMENTATION QUESTION FOR THE REVIEWER, raised rather than decided: if E-01 lands, `--yes` becomes required for any interactive mutation, which changes the documented ergonomics of a verb operators use constantly. Whether `.aw/records/plans/README.md`'s setter examples should be updated to show `--yes` is a judgement about how prominent the change should be; it is NOT in `- Scope-Paths:` and should be decided at review. If the answer is yes, that edit belongs in this plan's scope and the path must be declared before execution.

## Open questions

### OQ-01: Should the terminal-reopen override be a dedicated flag or should the transition be refused outright with no override?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because E-02 delivers the REFUSAL either way and the only variable is whether an escape hatch exists. Recorded because it is a policy judgement rather than a mechanism one, and because the two answers age differently. A DEDICATED FLAG treats reopening as legitimate-but-rare and keeps a documented path for a genuine mistake (a plan marked executed in error). NO OVERRIDE makes the `AGENTS.md` rule absolute and forces the corrective-IPD route always, which is stricter and matches how `aw ipd finalize` refuses rather than offering a bypass; the cost is that a genuinely mis-filed plan then needs a hand edit, which is exactly the untooled write the repository's own hooks discourage. RECOMMENDATION: a dedicated flag (`--allow-terminal-reopen`), on the grounds that a refusal with no escape tends to be routed around by hand editing, which is less auditable than a named flag whose use appears in the shell history and can be pinned by a test. Not resolved unilaterally because it is a contract-shaped decision about how strict the lifecycle is.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the flagless interactive call REFUSING (exit code shown) with its listed changes, and the same call with `--yes` SUCCEEDING, both from a scratch repo. Paste `git status --porcelain` after the refusal proving nothing was written. Paste the code comment explaining why gating on output mode protected the wrong party. Confirm the human path reaches the SAME refusal construction rather than a duplicate (show the single call site).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the refusal for `executed -> approved` INCLUDING with `--yes` (proving it is a second, independent guard), showing the offending plans named and the corrective-IPD route cited. Paste the override performing it. State which override shape you implemented and why, and confirm `--force` was NOT overloaded.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the CLASSIFIED caller inventory (every in-repo setter invocation, each marked deliberate-automation or human-facing) and the diff of any `--yes` additions. Paste the full bare suite result showing no test depended on flagless interactive writes. If any caller could not pass `--yes`, say so explicitly rather than omitting it.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste all three cases passing (flagless refuses; `--yes` performs; `--dry-run` previews), each asserting BOTH the status bullet and the file's directory. Plus a MUTATION CHECK: restore the old output-mode condition, show the flagless-refusal test FAILS, revert, show it passes.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the reopen-refused assertion, AND the must-still-work assertions for a nonterminal advance, a RETIREMENT to `superseded` (forward into a terminal state, which must remain allowed), and a non-plan artifact transition. State plainly that retirement still works, since an over-broad guard would have blocked the three retirements performed during the cleanup that found this bug.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Size note: 5 E-leaves in 3 groups. Two are the fixes, one is the caller survey that makes the first fix safe, and two are the test surfaces.
- Cohesion rationale: E-01 and E-02 are two guards on the same function and are grouped because a reviewer should judge the setter's overall safety posture once rather than twice, but they are SEPARATE items because they have different triggers, different overrides and different over-refusal risks. E-03 exists only to de-risk E-01. E-04 and E-05 are split to match their subjects, since E-05 carries the must-still-work assertions that E-04 does not need.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. When reporting tests passed, paste the ACTUAL runner output. REPRODUCE ONLY IN A SCRATCH REPO: this defect was discovered by accidentally mutating seven real records, so every exploratory setter run belongs in a throwaway tree, and use `--dry-run` where a real tree is unavoidable. This is a SHARED CHECKOUT: never revert or commit a file you did not change.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved 4bc1nd --by-human --message ...`) before execution. On completion, transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
