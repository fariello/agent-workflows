# IPD: Teach the executed-transition gate to recognize a legitimate lane merge

- Date: 2026-09-06
- Kind: child
- Concern: The `ipd-executed-transition-gate` pre-commit hook refuses EVERY integration of a lane on which `aw ipd finalize` genuinely ran, because its only proof of finalize is a journal under `.aw/state/runtime/transactions/ipd_finalize_<id6>.json` and `.aw/state/` is GITIGNORED box-local state. The journal therefore never travels with a lane branch, and the lane worktree that held it is torn down after integration, so the predicate is unsatisfiable by construction for a merge. The hook cannot distinguish the abuse it exists to catch (hand-editing a plan's `- Status:` or `git mv`-ing it into `executed/`) from the legitimate act of merging a finalized lane, and refuses both.
  REPRODUCED 2026-09-06, not inferred: in a throwaway clone, a lane branch was given a plan in `executed/` committed as `lifecycle(zzz999): finalize zzz999 -> executed`, then merged with `--no-ff --no-commit`. With `.git/MERGE_HEAD` present the hook exited 1 and printed "raw plan->executed transition (moved into executed/) with NO matching finalize evidence in .aw/state/". So the hook is blind to merge context.
  THE COST IS ALREADY PAID AND RECORDED. Recovering five lanes stranded by run `run-20260905T050043Z-639569` required `--no-verify` on four of five merges (`eyh1fu`, `txc9l1`, `uyeko5`, `eulhzt`), each with maintainer authorization, each documenting the bypass. Finalize had provably run on every one: commits `c9db21a3`, `43c87af5`, `251b7399`, `dd996d73`, each titled `lifecycle(<id6>): finalize <id6> -> executed`. A gate that must be bypassed as ROUTINE PRACTICE teaches operators and agents that `--no-verify` is normal, which is exactly how a real hand-edit would later pass unremarked. The hook's docstring is honest that it is local best-effort prevention; "skippable" was meant as a limitation, not as the expected workflow.
  THIS CHILD IS ORDER 01 BECAUSE IT UNBLOCKS THE REST OF THE SET. Children 03 and 04 make integration happen MORE often (a deferral ladder that re-attempts, and an `integrate` verb plus an automatic resume path), so every one of those integrations would trip this hook. Landing them first would multiply the `--no-verify` habit rather than reduce it.
- Scope: Add a MERGE-AWARE evidence path to the hook: during a merge, accept IN-TREE evidence (a `lifecycle(<id6>): finalize` commit reachable from the incoming side) as proof that finalize performed the transition, while keeping the hand-edit case refused exactly as today. Fix nothing else about the hook's behavior.
- Scope-Paths: agent_workflows/hooks/executed_transition_gate.py, tests/test_executed_transition_gate.py
- Item-Dependencies: none
- Status: to-review
- Set: integpath
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 29wvmj
- From-Backlog: rnl3b7

## Workflow history

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `rnl3b7` on a maintainer ruling to shape the `integdefer` items as one Set with the hook fix FIRST. Every claim in the item was re-verified at HEAD `a4279302` rather than trusted, because the item was filed 2026-09-05 and both runners churned heavily since. The core defect REPRODUCED exactly (see Concern). TWO CORRECTIONS TO THE ITEM, both material enough that a plan built on its text would have chased the wrong fix. FIRST, the item's headline evidence claim is WRONG: it says `76gsmv` passed the hook while the other four failed "because git recorded that plan file as a RENAME rather than an addition, so the hook's staged-change inspection did not classify it as a plan-to-executed transition", and concludes "a gate whose verdict depends on whether git chose rename detection is not gating the property it claims to gate". Measured: ALL FOUR of those commits are `R0xx` renames of identical shape (`443bbed4` R099, `c9db21a3` R099, `43c87af5` R099, `251b7399` R098), and the hook handles `R` EXPLICITLY (`code.startswith("R")` at `:118`, with `-M` passed at `:108`). So there is no rename-vs-add inconsistency to fix; the item's E-item-shaped instruction to "fix the rename-vs-add inconsistency regardless" would have been work against a non-defect. Why `76gsmv` passed is NOT established by this plan and is deliberately left as a non-blocking open question rather than guessed at. SECOND, the four lanes the item cites as live evidence are GONE: all four branches are deleted and all four plans now sit in `.aw/records/plans/executed/`, recovered by hand last session, so that evidence is HISTORICAL and this plan reproduces the defect synthetically instead of pointing at it. Also confirmed still true: the hook has zero references to `MERGE_HEAD` or merges, and `.aw/state/` remains gitignored.

## Goal

Stop refusing legitimate lane integrations, without weakening the hand-edit refusal the hook exists for. After this child, merging a finalized lane needs no `--no-verify`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: recognize a merge, and accept in-tree evidence

- [ ] E-01 Add a merge-context detector to `agent_workflows/hooks/executed_transition_gate.py`. A commit is a merge in progress when `.git/MERGE_HEAD` exists in the repository's git dir; RESOLVE THE GIT DIR PROPERLY rather than assuming `<root>/.git` is a directory, because in a WORKTREE `.git` is a FILE pointing elsewhere and this repository uses lane worktrees routinely (`git worktree list` shows them). Use `git rev-parse --git-dir` (the hook already shells out through its `_git` helper) so the check works from a worktree, a submodule, and a normal clone alike.
  RETURN THE INCOMING COMMIT, NOT JUST A BOOLEAN, because E-02 needs it: read `MERGE_HEAD`'s contents (a commit sha) rather than only testing existence. A detector that returns `bool` would force E-02 to re-read the same file, and the two could then disagree about which side is incoming.
  - Depends on: none
  - Expected outcome: a helper returns the incoming merge commit sha during a merge and `None` otherwise; it resolves the git dir via git rather than a hardcoded `.git/` path, so it is correct inside a lane worktree.
  - Execution state: pending

- [ ] E-02 Add the IN-TREE finalize-evidence predicate: for a plan arriving in `executed/` during a merge, accept the transition when a commit reachable from the INCOMING side (and NOT from `HEAD`) carries a `lifecycle(<id6>): finalize` subject naming THAT plan's id6. In-tree is the whole point: unlike the gitignored journal, a commit survives the branch, which is what makes the evidence portable (the item's own second option, "make the evidence portable", is the same insight arrived at from the other direction).
  BIND THE EVIDENCE TO THE SPECIFIC PLAN, exactly as `_finalize_evidence_ok` already binds the journal to the staged destination path (`:167-171`). A merge that carries a finalize commit for plan A must NOT authorize plan B arriving in `executed/` in the same merge. Match the id6 from the subject line and require it to equal the staged plan's `- Id:`.
  SCOPE THE SEARCH TO THE INCOMING SIDE ONLY, using the range `HEAD..<MERGE_HEAD>`, so a finalize commit that was already on main long ago cannot be replayed as evidence for a different plan arriving now.
  DO NOT REPLACE THE JOURNAL PATH. Keep `_finalize_evidence_ok` as-is and consult it FIRST; the new predicate is an additional accepting path used only when the journal is absent AND a merge is in progress. A non-merge commit therefore behaves byte-identically to today, which is what keeps the hand-edit case refused.
  - Depends on: E-01
  - Expected outcome: during a merge, a plan whose id6 has a `lifecycle(<id6>): finalize` commit on the incoming side passes; the same plan without such a commit still refuses; a finalize commit for a DIFFERENT id6 does not authorize it; outside a merge nothing changes.
  - Execution state: pending

### Task group 2: keep the abuse refused

- [ ] E-03 Prove and preserve the refusals, which is the half of this change that must not regress. FOUR cases must still be refused, and each is a distinct way the fix could be made too permissive:
  (a) a hand-edited `- Status: executed` with NO merge in progress (today's behavior, unchanged);
  (b) a `git mv` into `executed/` with no merge in progress;
  (c) a plan staged into `executed/` DURING a merge with NO finalize commit anywhere on the incoming side. This is the case the item explicitly warns about: "a fix that simply exempts all merges would let someone stage a hand-edit inside a merge commit". A merge must not be a blanket exemption;
  (d) a plan with no readable `- Id:`, which the hook already refuses separately (`:186-191`) and which must keep refusing, since without an id6 the new predicate has nothing to bind to.
  DO NOT WEAKEN THE MESSAGE for the non-merge cases. Operators and agents have learned the current wording; keep it and ADD merge-specific wording only where a merge was detected.
  - Depends on: E-02
  - Expected outcome: all four refusal cases refuse, with (c) refusing specifically because no matching finalize commit exists on the incoming side rather than because a merge was detected.
  - Execution state: pending

- [ ] E-04 Make the refusal ACTIONABLE in the merge case, because a refusal an operator cannot act on becomes another `--no-verify`. When a merge is detected and the incoming side carries no matching finalize commit, say so explicitly: name the plan, state that the merge carries no `lifecycle(<id6>): finalize` commit for it, and point at the real remedy (finalize on the lane, or `aw ipd finalize` if the plan legitimately has not been finalized).
  DO NOT TELL THE OPERATOR TO COMMIT, STASH, RESET, OR CLEAN ANYTHING. Executed plan `z2isfg` is prior art for a begin-time dirty gate AND for the lesson that a refusal message must not instruct the operator to touch work `AGENTS.md` forbids them to touch; reuse that wording discipline. Do not suggest `--no-verify` either: naming the bypass in the refusal is how it becomes routine.
  - Depends on: E-03
  - Expected outcome: the merge-case refusal names the plan, the missing evidence, and a remedy that does not involve bypassing the hook or mutating a co-worker's tree.
  - Execution state: pending

### Task group 3: prove it end to end

- [ ] E-05 Test through a REAL GIT MERGE, not by mocking the detector, because the defect is precisely that real merge state was never consulted. Build the fixture the way this plan's reproduction did: a throwaway repository, a lane branch carrying a plan in `executed/` committed with a `lifecycle(<id6>): finalize <id6> -> executed` subject, then `git merge --no-ff --no-commit`, then invoke the hook's `check()`/`main()` with `MERGE_HEAD` genuinely present.
  COVER BOTH DIRECTIONS AND THE BINDING. Assert: the merge with matching finalize evidence now PASSES (exit 0); the same merge WITHOUT that commit still REFUSES (exit 1); a merge whose finalize commit names a DIFFERENT id6 still refuses for the plan in question; and each of E-03's four non-merge refusals still refuses.
  ASSERT THE WORKTREE CASE, since E-01 exists because of it: run the hook from a `git worktree` where `.git` is a FILE, and show the git-dir resolution finds `MERGE_HEAD`. A test that only ever runs in a normal clone would pass even if E-01 hardcoded `<root>/.git`, leaving the bug live in exactly the lane worktrees this Set is about.
  Run the suite BARE (`python3 -m pytest`) and state before/after counts.
  - Depends on: E-04
  - Expected outcome: a test that FAILS on today's hook and passes after; both merge directions, the id6 binding, the four non-merge refusals, and the worktree case all pinned; bare suite green with counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE HOOK ALREADY HANDLES RENAMES, contrary to the backlog item. `_staged_plan_executed_transitions` passes `-M` (`:108`) and branches on `code.startswith("R")` (`:118`), extracting both old and new paths. So the item's "fix the rename-vs-add inconsistency" instruction targets a non-defect and is deliberately NOT in this plan.
- THE JOURNAL PREDICATE IS ALREADY PLAN-BOUND, and that discipline is the model for E-02: `_finalize_evidence_ok` checks the journal's phase, its `plan_id`, AND that its `dest_path` matches the staged path (`:152-172`), so evidence for one plan cannot authorize another. The in-tree predicate must bind equally tightly.
- `.aw/state/` IS GITIGNORED BY DESIGN, which is why the fix is in-tree evidence rather than committing the journal. The item offered committing it as an alternative; that would trade a local-state-leak decision for a hook fix, so this plan takes the narrower path and leaves the journal untouched.
- THE HOOK IS HONEST ABOUT BEING LOCAL AND SKIPPABLE, with `aw check`/`aw doctor` as the deterministic backstop. This plan does not change that posture; it removes the reason to reach for the bypass.
- `.git` IS A FILE, NOT A DIRECTORY, INSIDE A WORKTREE, and this repository uses lane worktrees as the normal execution mode (`.aw/worktrees/<id6>`), so any merge-state check must resolve the git dir through git.
- Run the suite BARE: `python3 -m pytest`. The configured `addopts` already supply quiet, parallel, and the fast subset; do not add `-n0` (measurably several times slower here) or a second `-q` (compounds to `-qq` and suppresses the `N passed` line this plan requires pasted).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | **THE DEFECT, REPRODUCED SYNTHETICALLY.** A throwaway clone, a lane branch carrying a plan in `executed/` committed as `lifecycle(zzz999): finalize zzz999 -> executed`, merged with `--no-ff --no-commit`: with `.git/MERGE_HEAD` present the hook exited 1 and refused with "NO matching finalize evidence in .aw/state/". | live reproduction 2026-09-06 at HEAD `a4279302` |
| F-2 | The hook has ZERO merge awareness: `grep -n "MERGE_HEAD\|merge"` over `executed_transition_gate.py` returns nothing. | measured 2026-09-06 |
| F-3 | The evidence predicate is unsatisfiable across trees BY CONSTRUCTION: it reads a journal under `.aw/state/runtime/transactions/`, and `.aw/state/` is gitignored, so the journal cannot travel with a lane branch. | `executed_transition_gate.py:152-172`; `.gitignore` |
| F-4 | **THE ITEM'S RENAME EXPLANATION IS FALSE, and this correction is why the plan omits a whole instruction the item gave.** All four recovery commits are `R0xx` renames of identical shape (`443bbed4` R099, `c9db21a3` R099, `43c87af5` R099, `251b7399` R098), and the hook branches on `R` explicitly with `-M` enabled. There is no rename-vs-add inconsistency to fix. | `git log --diff-filter=R --name-status` per id6; `executed_transition_gate.py:108`, `:118` |
| F-5 | **THE ITEM'S LIVE EVIDENCE IS NOW HISTORICAL.** All four cited lane branches (`aw/lane/76gsmv`, `eyh1fu`, `txc9l1`, `uyeko5`) are DELETED and all four plans are in `.aw/records/plans/executed/`, recovered by hand last session. So the defect must be reproduced synthetically, which E-05 does. | `git rev-parse --verify` fails for all four; `ls .aw/records/plans/executed/` |
| F-6 | The bypass cost is documented in git history, so this is a measured habit rather than a hypothetical: four of five recovery merges used `--no-verify`, each with a real finalize commit on the lane (`c9db21a3`, `43c87af5`, `251b7399`, `dd996d73`). | backlog `rnl3b7`; those four commit subjects |
| F-7 | The journal predicate binds evidence to ONE plan via `plan_id` and `dest_path`, which is the discipline E-02 must match so a merge carrying finalize for plan A cannot authorize plan B. | `executed_transition_gate.py:167-171` |
| F-8 | A plan with no readable `- Id:` is already refused on its own branch (`:186-191`), which must keep refusing because the new in-tree predicate has no id6 to bind to. | `executed_transition_gate.py:186-191` |

## Proposed changes (ordered, validatable)

1. Add a merge detector that resolves the git dir through git and returns the incoming commit (E-01).
2. Add a plan-bound, incoming-side-only in-tree finalize-evidence predicate, consulted only when the journal is absent during a merge (E-02).
3. Prove the four refusal cases still refuse, including a hand-edit staged inside a merge (E-03).
4. Make the merge-case refusal actionable without naming the bypass or telling the operator to mutate a tree (E-04).
5. Test through a real git merge, both directions, the id6 binding, and from a worktree where `.git` is a file (E-05).

## Deferred / out of scope (with reason)

- COMMITTING THE FINALIZE JOURNAL (or a redacted attestation) to make the evidence portable. The item offers this as an alternative; it is rejected here as the wider change, because it turns a hook fix into a decision about why `.aw/state/` is gitignored and what may leave the box. In-tree commit evidence achieves the same portability with no new tracked state.
- THE "RENAME-VS-ADD INCONSISTENCY" the item instructs be fixed regardless. Measured non-existent (F-4). Fixing a non-defect would be change without cause.
- ESTABLISHING WHY `76gsmv` PASSED the hook when the other three did not. The item's explanation is disproved (F-4) and this plan does not substitute a guess; recorded as OQ-01, non-blocking, because the fix does not depend on the answer.
- WEAKENING OR REMOVING THE GATE. Explicitly counter to the goal: the point is to stop refusing legitimate merges, not to stop refusing hand-edits.
- THE OTHER THREE `integdefer` CONCERNS. Children 02, 03 and 04 of this Set own the shared extraction, the deferral ladder, and the `integrate` verb; this child deliberately stays inside one hook file so it can land and be verified first.

## Scope check

- Over-scope: none. One hook module plus its test file.
- Scope-Paths justification: `agent_workflows/hooks/executed_transition_gate.py` holds the detector, both predicates, and the refusal messages (E-01..E-04); `tests/test_executed_transition_gate.py` holds every new assertion (E-05). No runner module is touched, which is what lets this child land while the two high-contention driver files are being changed by the rest of the Set.
- Under-scope, stated rather than left as `none`: this child does not make the evidence portable by committing the journal, does not touch the `aw check`/`aw doctor` backstop, and does not address the three sibling concerns. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with the `N passed` summary line pasted and counts stated. Baseline at authoring: `5536 passed, 3 skipped, 2 xfailed` at HEAD `3d239cfa`; re-measure at execution time since the Set's siblings may land first.
- Targeted: `tests/test_executed_transition_gate.py`, plus any test module that exercises `aw ipd finalize` end to end.
- A REAL-MERGE demonstration in a throwaway repository, pasted before and after: the same merge refusing today and passing after the fix. A mocked `MERGE_HEAD` is NOT sufficient evidence, because the defect is that real merge state was never read.
- A WORKTREE demonstration: the hook invoked from a `git worktree` (where `.git` is a file), showing merge state is still found.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`). A pipe through `head` reports the pipe's status, which has already produced one false finding in this repository.
- `aw sanitize --agent` clean.

## Spec / documentation sync

The hook's MODULE DOCSTRING states the evidence rule ("a transaction JOURNAL under `.aw/state/runtime/transactions/ipd_finalize_<id6>.json`", `:18`) and must be updated to describe the second, in-tree accepting path and when it applies, since that docstring is the only prose statement of what the gate accepts.

If `CONTRIBUTING.md` or `AGENTS.md` documents this hook or tells a reader that a lane merge requires `--no-verify`, correct it in the same change and say so in the commit; a doc that still prescribes the bypass would keep the habit alive after the reason is gone. Verify by grep rather than assumption, and write no em or en dashes in user-facing prose.

No SPEC change is authorized here: the gate is local tooling, not a specified contract surface.

## Open questions

### OQ-01: Why did `76gsmv` pass the hook when the other three merges did not?

- Blocking: no
- Status: deferred
- Owner: this plan's executor, at E-05
- Trigger: E-05's real-merge fixture PASSING before the fix is applied, which would be this same mystery reproducing under controlled conditions; that is the only cheap occasion on which the answer becomes obtainable, and the executor must record it here rather than accept the pass.
- Resolution or deferral rationale: UNRESOLVED, and deliberately not guessed at. The backlog item attributes it to git rename detection, which this plan measured to be FALSE (F-4): all four commits are `R0xx` renames and the hook handles `R` explicitly. The real cause is not established. It is NON-BLOCKING because the fix does not depend on it: E-02 makes every legitimate merge pass on positive in-tree evidence, so a case that passed for an unknown reason will pass for a KNOWN reason afterwards. Deferred rather than open because pursuing it means archaeology on a five-commit sequence whose lanes are now deleted (F-5), and the answer would change nothing in this plan. If E-05's real-merge fixture unexpectedly PASSES before the fix, that is the same mystery reproducing and the executor MUST record it here rather than accept the pass.

### OQ-02: Should the in-tree predicate accept any commit subject naming the plan, or only the exact `lifecycle(<id6>): finalize` form?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ONLY THE EXACT FORM. That subject is written by `aw ipd finalize` itself, so requiring it keeps the evidence tied to the tool that ran the gates rather than to prose anyone can type; a looser match (any commit mentioning the id6) would let an ordinary work commit that happens to name the plan authorize the transition, which is the hand-edit case wearing a different hat. The narrow form is also what the four recorded recovery commits actually carry (`c9db21a3`, `43c87af5`, `251b7399`, `dd996d73`), so it is evidenced rather than invented. If a future finalize changes its subject format, this predicate must change with it, which is a coupling worth having because the alternative is a gate that accepts strings no tool emits.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the detector and show it returning the incoming commit sha during a real merge and `None` outside one. Paste the git-dir resolution line and confirm in one sentence that it does not hardcode `<root>/.git`. Paste output from inside a `git worktree` (where `.git` is a FILE, show that with `ls -la`) proving `MERGE_HEAD` is still found.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the predicate. Show FOUR probes during a real merge: matching finalize commit for the staged plan (accept); no finalize commit (refuse); a finalize commit naming a DIFFERENT id6 (refuse for the staged plan); and a finalize commit that exists on `HEAD` but not the incoming side (refuse, proving the `HEAD..MERGE_HEAD` scoping). Confirm the journal path is still consulted first and unmodified.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the exit code (UNPIPED) and message for each of the four refusal cases: hand-edited status outside a merge; `git mv` outside a merge; a plan staged into `executed/` DURING a merge with no finalize commit on the incoming side; and a plan with no readable `- Id:`. Case (c) is the one that matters most: confirm the message attributes the refusal to missing evidence, NOT to the presence of a merge, and state in one sentence why a blanket merge exemption would have been wrong.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the merge-case refusal text verbatim. Confirm it names the plan, names the missing `lifecycle(<id6>): finalize` evidence, and offers a remedy. Confirm by inspection that it does NOT mention `--no-verify` and does NOT instruct the operator to commit, stash, reset, or clean anything, citing the `z2isfg` wording discipline. Paste the non-merge refusal text and confirm it is unchanged from today.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new test and PROOF IT IS FALSIFIABLE: run it against the pre-fix hook (stash or revert E-01/E-02) and paste the FAILURE, then paste the pass after. A test never observed to fail is not evidence it detects the bug. Paste the real-merge before/after demonstration, the worktree case, and the BARE `python3 -m pytest` summary line with before/after counts. Confirm no test mocks `MERGE_HEAD` in place of performing a real merge.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). OQ-01 is deferred and non-blocking with its rationale recorded; OQ-02 is resolved. No blocking question remains.

Scope fence: touch ONLY the two paths in `Scope-Paths`. Do NOT modify `oc_runipd.py`, `agy_runipd.py`, or `runner_shared.py`; this child is deliberately runner-free so it can land while siblings 02 through 04 change those files. Do NOT commit the finalize journal or change `.gitignore`. Do NOT weaken any existing refusal. Do NOT change `_finalize_evidence_ok`'s journal logic. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since a rejected commit can leave another party's paths staged. THIS IS A SHARED CHECKOUT with concurrent agents: run `aw runs` before starting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

THE ITEM THAT MATTERS MOST IS V-03 CASE (c). The tempting fix is to exempt merges wholesale, which would pass every test about legitimate integration while opening the exact hole the gate exists to close: a hand-edited plan staged inside a merge commit. The refusal must come from ABSENT EVIDENCE, never from the absence of a merge. If you find yourself writing `if merging: return 0`, stop and reconsider.

YOU WILL BE TESTING A HOOK THAT GOVERNS YOUR OWN COMMITS. Expect to hit it while working, and do NOT reach for `--no-verify` to get your own work in; if it refuses something you believe is legitimate, that is either a finding or a bug in your change, and either way it is the information this plan exists to produce.

On completion, close backlog `rnl3b7`, which this plan carries as `- From-Backlog:`. That item carries NO release gate, so no `Blocks-Release` is inherited here; the three release-blocking siblings carry theirs on children 02 through 04.
