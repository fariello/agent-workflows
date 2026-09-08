# IPD: Retry once inside the isolated commit when a hook rewrote our own paths, and normalize artifacts on write

- Date: 2026-09-08
- Kind: child
- Concern: Four pre-commit hooks REWRITE a staged file and then reject the commit, and their exclude regex does not cover `.aw/records/plans|backlog|specs`, which is where agents write most. The tooled commit path makes exactly one attempt and gives up, so routine whitespace churn costs a full commit round trip plus the contract-mandated index re-verify. The contract then compounds it by calling the tooled path "immune to this by construction", which is true for index pollution and false for auto-fix rejection, so an agent following the contract literally pays the full tax for a stripped trailing space.
- Scope: Add a BOUNDED SINGLE RETRY on a self-rewrite at the layer that now performs the commit, distinguishing a hook that REWROTE our own paths (retry once) from a hook that REFUSED without touching them (fail exactly as today). Report the rewritten paths so the fix is visible rather than silent. Separately, normalize per-line trailing whitespace in the single tool-authored artifact write path so most triggers disappear at the source. Close the test gap: today no test covers a hook-rejected commit at all.
- Scope-Paths: agent_workflows/commit_lock.py, agent_workflows/git_commit_helper.py, agent_workflows/artifact_core.py, tests/test_git_commit_helper.py, tests/test_commit_lock.py
- Item-Dependencies: none
- Status: to-review
- Set: hookretry
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: lqly9m
- From-Backlog: egqt32
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `egqt32`, inheriting its `Blocks-Release: next` gate. THE ITEM IS PARTLY OBSOLETE AND THE OBSOLETE PART IS ITS ENTIRE PRESCRIBED FIX LOCATION, so this plan is a deliberate narrowing rather than a transcription. The item's Fix Layer 1 says to add the retry in `offer_commit` "before the commit at `:245`", detecting a rewrite by re-hashing files on disk. That commit call NO LONGER EXISTS: three commits on 2026-09-06 (`3d239cfa` serialize on a shared writer lock, `798c5cb5` commit in an isolated worktree, `efc7a1a1` the same for finalize) moved the actual `git commit` out of `offer_commit` entirely. It now delegates to `commit_lock.commit_isolated` (`git_commit_helper.py:488`), which snapshots HEAD into a throwaway detached worktree, COPIES our paths in, and runs the real hooked commit THERE (`commit_lock.py:252`). The item's disk-re-hash detector would therefore never fire: a mutating hook now rewrites the file inside the private worktree, and the shared tree is untouched by design. I MEASURED THIS rather than inferring it. In a scratch repo with a hook that strips trailing whitespace and exits 1, `commit_isolated` returns `hook-rejected` while the shared-tree file still reads `'trailing space here   \n'` unchanged, and calling it three times in a row returns `hook-rejected` all three times with the commit log never advancing past `init`. So the defect is REAL and currently UNFIXABLE BY THE ITEM'S RECIPE, and the retry must move inside `commit_isolated` where the rewrite is observable. TWO FURTHER CORRECTIONS. The item's `offer_commit` line citations (`:245`, `:246`, `:247`, `:39-51`, `:233-234`) are all stale; re-located by symbol, the delegation is `:488`, the failure reset `:499`, the error return `:510`, `CommitOutcome` `:250-262`, and the our_staged intersection `:472-473`. And the item asserts the four mutating hooks fire on `.aw/records/...`: VERIFIED live by running `pre-commit run trailing-whitespace` against a scratch file under `.aw/records/backlog/open/`, which reported "Fixing ..." and exited 1.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop charging every agent a commit round trip for a stripped trailing space, without weakening any hook that legitimately refuses. Two independent levers: make a self-rewrite rejection recoverable in one bounded retry, and stop producing the whitespace the hook objects to.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: detect a self-rewrite where it is now observable

- [ ] E-01 Detect, inside `commit_isolated` (`commit_lock.py:150-292`), whether a rejected commit REWROTE any of OUR paths in the isolated worktree. This is the item's Fix Layer 1 relocated to the only layer that can still see the rewrite. Record a content hash per path in `rel` immediately after the isolated `git add` (`:240`) and before the real commit (`:252`); on `rc != 0` (`:253`), re-hash the same paths INSIDE THE WORKTREE (`wt / r`, not `repo_root / r`, which is the whole reason the item's recipe fails). Distinguish two cases and return them distinguishably: any of our paths changed on disk means a REWRITE, nothing changed means a genuine REFUSAL. Note the hash must be taken from the worktree copy after the `add`, because `shutil.copy2` (`:230`) is what put our content there and a pre-copy hash would compare against the wrong baseline.
  - Depends on: none
  - Expected outcome: a scratch hook that strips whitespace and exits 1 is classified REWRITE with the changed path named; a hook that prints an error and exits 1 without touching files is classified REFUSAL.
  - Execution state: pending

- [ ] E-02 Retry the commit EXACTLY ONCE on the rewrite case, never on the refusal case, and never in a loop. In the isolated worktree, re-`git add -- <rel>` to pick up the hook's own fix and re-run the same `git commit` (`:252`). A SECOND rejection fails, whatever its cause: one retry, never a loop. If the retry succeeds, continue into the existing success path unchanged, which resolves HEAD (`:261`) and advances the branch under the compare-and-swap (`:270`) whose staleness failure returns `ISO_RACED` (`:272-279`). MEASURED JUSTIFICATION for the exactly-once bound rather than a fixed-point loop: calling `commit_isolated` repeatedly today returns `hook-rejected` on every attempt with no progress, so an unbounded loop against a hook that rewrites nondeterministically would spin. One retry covers the whitespace/format case, which is the one the maintainer complained about.
  - Depends on: E-01
  - Expected outcome: the whitespace hook case commits on the retry with the hook's fix included; a refusing hook still returns `ISO_HOOK_REJECTED` after exactly one commit attempt, with the attempt count demonstrated.
  - Execution state: pending

- [ ] E-03 Make the fix VISIBLE rather than silent, end to end. A retry that silently absorbs a rewrite would hide the fact that the committed content differs from what the caller wrote, which is exactly the kind of invisible mutation the research README records as a past harm. Carry the rewritten path list out of `commit_isolated` on its `IsolatedCommitResult` (`commit_lock.py:124-133`, currently `status`/`commit`/`detail`) and then out of `offer_commit` on `CommitOutcome` (`git_commit_helper.py:250-262`, currently `status`/`commit`/`staged`/`message`) as the `hook_fixed` tuple the item names. BOTH ARE `NamedTuple`s, so ADD A FIELD WITH A DEFAULT rather than changing the positional contract: existing callers unpack by name and by position, and `work_cmd.run_commit` already reads the outcome. Surface the names in the human message too, so an operator sees "committed, after the hooks fixed <path>" rather than a bare success.
  - Depends on: E-02
  - Expected outcome: a rewrite-then-retry commit reports the rewritten paths on both result objects and in the human message; every existing caller still works unchanged.
  - Execution state: pending

- [ ] E-04 PRESERVE THE SHARED-CHECKOUT SAFETY PROPERTY, and prove it rather than asserting it. The retry must re-add ONLY `rel`, which is already the intersection of the caller's explicit paths with what the helper itself staged (`git_commit_helper.py:472-473`), so a co-worker's file restored into the index by pre-commit's stash/restore stays unreachable. Note the isolation makes this stronger than the item assumed: the retry happens in a private worktree that holds ONLY our copied paths (`commit_lock.py:225-234`), so there is nothing of a peer's to sweep in even by mistake. NEVER add `--no-verify`: the argv contract recorder in `tests/test_git_commit_helper.py:60-77` asserts it never appears (along with `-A`, `--all`, `-a`, `push`), and that test is correct. Re-run that recorder over the new retry path so the second commit attempt is covered by the same contract as the first.
  - Depends on: E-02
  - Expected outcome: the argv contract assertions pass across BOTH commit attempts, and a peer's dirty file is demonstrably absent from the retried commit.
  - Execution state: pending

### Task group 2: remove most triggers at the source

- [ ] E-05 Normalize per-line trailing whitespace in `artifact_core.atomic_write` (`:118-132`), the single write path for tool-authored artifacts. THE GAP IS REAL AND THE EXISTING RENDERERS DO NOT CLOSE IT, measured rather than assumed: `backlog._render_item` and its siblings do a WHOLE-FILE `.rstrip() + "\n"` (`backlog.py:337`, `plans.py:291`, `specs.py:891`, `set_records.py:83/113/134`), and I confirmed that leaves per-line trailing whitespace intact by rendering a body containing `'body line with trailing   '` and finding exactly one such line survives. Normalize by rstripping EACH line and ending with exactly one trailing newline. Callers inherit it automatically: `backlog.py:439/603`, `specs.py:677/834/850/967`, `releases.py:885`, `prompts.py:264`, `research_cmd.py:130`, `artifact_refs.py:158`, `artifact_rename.py:287/456`, `plans_refs.py:345`, `set_records.py:155/156/157/232/310/340`, `status_set.py:901`. NOTE the corpus is currently CLEAN (0 of 962 tracked `.aw/records` markdown files carry a trailing-whitespace line, measured at HEAD `44d4950d`), which means this item is PREVENTIVE: it stops the hook from ever having to fix a tool-written artifact, and there is no backlog of dirty files to migrate.
  - Depends on: none
  - Expected outcome: text written through `atomic_write` never contains a line with trailing whitespace and always ends in exactly one newline; the 962-file corpus check still reports 0 afterwards.
  - Execution state: pending

- [ ] E-06 Own the MARKDOWN HARD-LINE-BREAK tradeoff explicitly instead of discovering it later. Per-line rstrip destroys markdown's two-space hard line break. The honest framing, which the item states and this plan verified: the `trailing-whitespace` hook ALREADY destroys it on every non-excluded path, so this makes the writer agree with the hook rather than introducing a new loss, and measured at HEAD there are ZERO two-space hard breaks in the tracked artifact corpus, so nothing currently relies on it. ALSO RESOLVE THE EDITOR/HOOK DISAGREEMENT the item flags, because it is a live inconsistency and a one-line decision: `.editorconfig` sets `trim_trailing_whitespace = true` globally (`:8`) but EXEMPTS `*.md` (`:14-15`), while the hook does NOT exempt markdown. Pick one and make them agree; note that this plan's own change aligns the WRITER with the hook, so exempting markdown in the hook would contradict E-05 while removing the `.editorconfig` exemption would make all three agree. Record the decision in a comment.
  - Depends on: E-05
  - Expected outcome: the tradeoff is documented at the normalization site with its measured basis, and `.editorconfig` and the hook no longer disagree about markdown.
  - Execution state: pending

### Task group 3: close the test gap this defect hid behind

- [ ] E-07 Add the two fixtures the item requires, which do not exist today. THE GAP IS THE REASON THIS SHIPPED: `tests/test_git_commit_helper.py` has 16 `offer_commit` call sites and NO test for a hook-rejected commit, because its fixture `tests/support.init_repo` (`tests/support.py:92-100`) does a bare `git init` and installs NO hook (note the item cites `tests/support/__init__.py`, but the module is `tests/support.py`). Add both: (a) a hook that REWRITES a staged file and exits nonzero, asserting ONE retry, the commit succeeds, and `hook_fixed` names the path; (b) a hook that REFUSES without touching files, asserting NO retry, still an error outcome, and the index left as found. Cover BOTH layers, since E-01/E-02 changed the lower one: assert at `commit_isolated` (where the detection lives) and at `offer_commit` (where callers see it). Reuse the `_ArgvRecorder` fixture (`tests/test_git_commit_helper.py:60-85`) so the argv contract is asserted across the retry.
  - Depends on: E-03, E-04
  - Expected outcome: four tests (rewrite/refusal x both layers) that fail against HEAD `44d4950d` for the rewrite case and pass after; the refusal case passes both before and after, proving no behavior change there.
  - Execution state: pending

- [ ] E-08 Verify the interaction with the CONCURRENT-WRITER protection that `798c5cb5` bought, since the retry adds a second hook run inside the isolation window and that window's whole purpose is peer safety. `tests/test_commit_lock.py` (225 lines, 12 tests) pins the existing properties, including `test_offer_commit_holds_the_lock_during_its_commit` (`:178`) and the two documentation tests recording the honest residue (`:203`, `:214`). Confirm the retry happens INSIDE the same `writer_lock` window (`git_commit_helper.py:459`) and inside the SAME isolated worktree, so it neither takes the lock twice nor creates a second worktree, and confirm the `finally` cleanup (`commit_lock.py:288-292`) still removes exactly one worktree. Also confirm a peer write during a RETRIED commit still survives, which is the measured property `798c5cb5` was written for.
  - Depends on: E-07
  - Expected outcome: one lock acquisition and one worktree per `offer_commit` call even when a retry occurs, cleanup verified, and a peer write during a retried commit demonstrated to survive.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE COMMIT NO LONGER HAPPENS WHERE THE ITEM SAYS. `offer_commit` delegates to `commit_lock.commit_isolated` (`git_commit_helper.py:488`), which commits in a throwaway detached worktree so pre-commit's stash/restore cannot clobber a peer's in-flight edit. That relocation is the single most important fact for this plan.
- `commit_isolated`'s docstring (`commit_lock.py:157-183`) records four MEASURED properties, one of which directly constrains this work: "The hooks STILL RUN and STILL GATE: a deliberately failing hook rejected the commit and nothing landed. This is emphatically NOT `--no-verify` in disguise." A retry must preserve that for the refusal case.
- The branch advance is a COMPARE-AND-SWAP (`:270`), returning `ISO_RACED` (`:272-279`) when a peer commit landed meanwhile, because a blind `update-ref` was reproduced discarding a peer commit. A retry must not bypass it.
- `IsolatedCommitResult` (`:124-133`) and `CommitOutcome` (`git_commit_helper.py:250-262`) are both `NamedTuple`s with positional contracts, so new fields need defaults and must be appended.
- The status vocabularies are separate and both must be respected: `ISO_COMMITTED`/`ISO_NOTHING`/`ISO_HOOK_REJECTED`/`ISO_RACED`/`ISO_ERROR` (`commit_lock.py:136-140`) and `STATUS_COMMITTED`/`STATUS_SKIPPED`/`STATUS_DECLINED`/`STATUS_REFUSED_DIRTY`/`STATUS_NOTHING_TO_COMMIT`/`STATUS_ERROR` (`git_commit_helper.py:242-247`).
- Four hooks rewrite-and-reject; the read-only local hooks never rewrite. Mutating: `trailing-whitespace` (`.pre-commit-config.yaml:15-16`), `end-of-file-fixer` (`:17-18`), `ruff --fix` (`:31-33`), `ruff-format` (`:34-35`). Their shared exclude covers only `.agents/docs/research/`, `.aw/records/docs/research/` and `.aw/system/`. Read-only refusals: `local-leaks` (`:42-47`), `ipd-executed-transition-gate` (`:55-60`), `ipd-status-untooled-gate` (`:69-74`).
- The argv contract test is a real fence and should be leaned on, not worked around: it forbids `-A`, `--all`, `-a`, `push` and `--no-verify` across every recorded git call (`tests/test_git_commit_helper.py:60-77`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | THE ITEM'S PRESCRIBED FIX LOCATION IS OBSOLETE. Its Fix Layer 1 targets a `git commit` in `offer_commit` at `:245` that no longer exists; the commit now happens in `commit_lock.commit_isolated`. | `git_commit_helper.py:488` -> `commit_lock.py:252`; relocation landed in `3d239cfa`, `798c5cb5`, `efc7a1a1` (all 2026-09-06) |
| F-2 | The item's disk-re-hash detector would never fire, MEASURED not inferred: with a whitespace-stripping hook that exits 1, `commit_isolated` returns `hook-rejected` while the SHARED-tree file is still `'trailing space here   \n'` unchanged. | measured in a scratch repo against HEAD `44d4950d` |
| F-3 | The defect itself is REAL and there is no progress across attempts: three consecutive `commit_isolated` calls all return `hook-rejected` and the log never advances past `init`. | measured at `44d4950d` |
| F-4 | The mutating hooks DO fire on the agent-write paths: `pre-commit run trailing-whitespace` on a scratch file under `.aw/records/backlog/open/` printed "Fixing ..." and exited 1. | measured at `44d4950d`; exclude regex `.pre-commit-config.yaml:15-16` |
| F-5 | `offer_commit` still makes exactly ONE attempt: on failure it resets only our paths and returns an error, with no retry and no rewrite detection. | `git_commit_helper.py:488`, `:499`, `:510` |
| F-6 | The item's `offer_commit` citations are ALL stale and were re-located by symbol: `:245`/`:246`/`:247` -> `:488`/`:499`/`:510`; `CommitOutcome` `:39-51` -> `:250-262`; the our_staged intersection `:233-234` -> `:472-473`. | read at `44d4950d` |
| F-7 | THE TEST GAP IS EXACTLY AS DESCRIBED and is why this shipped: no test in `tests/test_git_commit_helper.py` covers a hook-rejected commit, because the shared fixture installs no hook. | `tests/support.py:92-100` (bare `git init`); 749-line test module with no hook fixture |
| F-8 | The whole-file rstrip in every renderer does NOT catch per-line trailing whitespace, verified by rendering a body containing a trailing-space line and finding it survives. | measured via `backlog._render_item` at `44d4950d`; `backlog.py:337`, `plans.py:291`, `specs.py:891`, `set_records.py:83/113/134` |
| F-9 | THE CORPUS IS CURRENTLY CLEAN, so E-05 is PREVENTIVE with no migration: 0 of 962 tracked `.aw/records` markdown files carry a trailing-whitespace line, and 0 carry a two-space markdown hard break. That also means the hard-break tradeoff costs nothing today. | measured over `git ls-files .aw/records` at `44d4950d` |
| F-10 | `atomic_write` is genuinely the single tool-authored write path, with ~20 call sites across 11 modules, so normalizing there reaches all of them. | `artifact_core.py:118-132`; call sites enumerated in E-05 |
| F-11 | The editor and the hook disagree about markdown, so one of them is wrong regardless of this plan: `.editorconfig` exempts `*.md` from trailing-whitespace trimming while the hook does not. | `.editorconfig:8`, `:14-15`; `.pre-commit-config.yaml:15-16` |
| F-12 | The contract's "immune to this by construction" claim is scoped to index pollution and does not cover auto-fix rejection, which is what makes an agent pay the full tax for a whitespace fix. | `engine.py:1246-1252`, rendered at `AGENTS.md:58`/`:60` |

## Proposed changes (ordered, validatable)

1. Detect a self-rewrite inside `commit_isolated`, hashing the WORKTREE copies (E-01).
2. Retry exactly once on a rewrite; never on a refusal; never loop (E-02).
3. Carry the rewritten paths out on both result types and into the human message (E-03).
4. Preserve and prove the shared-checkout and argv-contract properties across both attempts (E-04).
5. Normalize per-line trailing whitespace in `atomic_write` (E-05).
6. Document the hard-break tradeoff and reconcile `.editorconfig` with the hook (E-06).
7. Add the rewrite and refusal hook fixtures at both layers (E-07).
8. Verify one lock and one worktree per call even with a retry, and that a peer write survives (E-08).

## Deferred / out of scope (with reason)

- FIX LAYER 3 FROM THE ITEM, the contract rewording in `engine.py`. The item explicitly does not decide that wording, and the maintainer's MUST-versus-PREFER ruling is recorded on backlog item `wjl471` (commitguard, still `open` at HEAD), which owns the replacement text and its guard design. There is a HARD ORDERING CONSTRAINT here rather than a preference: the reworded paragraph DESCRIBES the retry, so it must not ship before this plan lands, or the contract installed into every managed repo would document behavior the code does not have. This plan is therefore a PREREQUISITE of `wjl471`'s answer, not a competitor to it.
- WIDENING THE HOOK EXCLUDE REGEX to cover `.aw/records/plans|backlog|specs`. That would stop the churn by stopping the checking, and the excluded trees would silently accumulate the whitespace the rest of the repo forbids. E-05 removes the trigger instead of the check.
- `--no-verify` IN ANY FORM. Forbidden by the argv contract test and correctly so; it would convert a churn annoyance into a gate bypass.
- AN UNBOUNDED RETRY LOOP or a fixed-point "commit until stable". One retry covers the deterministic whitespace/format case; a nondeterministic hook would spin, and measured behavior today is no progress across repeated attempts.
- MIGRATING EXISTING FILES to the normalized form. Unnecessary: the corpus already measures clean (F-9).

## Scope check

- Over-scope: `agent_workflows/commit_lock.py` and `tests/test_commit_lock.py` are in `Scope-Paths` although the backlog item names neither. They are unavoidable: the item's target code moved into that module on 2026-09-06, so the retry cannot be implemented anywhere else. `.editorconfig` is touched by E-06 and is NOT yet in `Scope-Paths` because the reconciliation direction is OQ-02's to settle; whichever file that decision lands in must be added to the fence before execution.
- Under-scope: the contract wording stays with `wjl471`. No existing artifact is re-normalized. The hook exclude regex is unchanged.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` at authoring time is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_git_commit_helper.py tests/test_commit_lock.py` for the focused surface.
- The scratch-repo reproduction from F-2/F-3 re-run after the change, showing the rewrite case now commits on the retry and the refusal case still does not.
- A peer-write-survives check during a RETRIED commit, following the method `tests/test_commit_lock.py` already uses for the single-attempt case.
- `aw sanitize --agent` before treating any pasted output as shareable, since the evidence includes filesystem paths.

## Spec / documentation sync

No `.spec.md` file governs the commit helper, so none is touched and none is declared in `Scope-Paths`. The authoritative documentation for this behavior is the `commit_isolated` docstring (`commit_lock.py:157-183`), which lists four measured properties and MUST be extended to describe the retry and to state that the refusal case is unchanged; leaving it as-is would make the code's own strongest claim ("a deliberately failing hook rejected the commit and nothing landed") ambiguous about which failing hooks. `AGENTS.md`/`engine.py:1246-1252` is DELIBERATELY NOT EDITED HERE: that wording belongs to backlog item `wjl471`, and the ordering constraint runs the other way, since the reworded paragraph may only ship AFTER this plan lands.

## Open questions

### OQ-01: Should the retry also cover `ipd_lifecycle`'s finalize commit path?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE FROM THE CODE and recorded so it is answered deliberately. `efc7a1a1` gave finalize the same isolated-commit treatment, so if finalize routes through `commit_lock.commit_isolated` it inherits E-01/E-02 for free and there is nothing to decide; if it carries its own commit call, it has the identical defect and either gets the same retry or is documented as deliberately excluded. Determine which by reading the finalize commit path, and if it needs a change, say so rather than silently extending the fence: `agent_workflows/ipd_lifecycle.py` is not in `Scope-Paths` and adding it is a scope decision.

### OQ-02: Which way should `.editorconfig` and the hook be reconciled for markdown?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: A ONE-LINE DECISION with a clear recommendation, deferred because it is a repository-style call rather than a correctness one. Removing the `*.md` exemption from `.editorconfig` (`:14-15`) makes editor, hook and this plan's writer all agree, and costs nothing measurable: there are ZERO two-space markdown hard breaks in the tracked artifact corpus (F-9). The opposite fix, exempting markdown in the hook, would directly contradict E-05 and re-open the churn this plan exists to close. E-05/E-06 do not depend on the answer; only the file that gets edited does, which is why `.editorconfig` is deliberately not yet in `Scope-Paths`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the output of a scratch-repo run showing BOTH classifications from the same code path: a whitespace-stripping hook classified REWRITE with the changed path named, and a file-untouching refusing hook classified REFUSAL. Paste the diff showing the re-hash reads `wt / r` and not `repo_root / r`, since hashing the shared tree is the specific mistake that makes this undetectable.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the scratch-repo BEFORE run (three consecutive `hook-rejected` results, log stuck at `init`) and the AFTER run (commit succeeds, log advanced, hook's fix present in the committed content). Paste an instrumented commit-attempt COUNT proving exactly two attempts on the rewrite case and exactly one on the refusal case; a passing test alone does not establish the count.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the retried commit's `IsolatedCommitResult` and `CommitOutcome` showing the rewritten path list populated, the human message naming the fixed path, and proof the positional contracts still hold (paste a positional unpack of each NamedTuple, or the test that does).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `_ArgvRecorder` assertion result covering BOTH commit attempts (showing no `-A`, `--all`, `-a`, `push`, `--no-verify`), and paste a demonstration that a peer's dirty file is absent from the retried commit (`git show --stat` of the retried commit alongside `git status --porcelain` showing the peer file still dirty).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste a snippet's output showing text containing a trailing-whitespace line and multiple trailing newlines, written through `atomic_write`, reads back with no trailing-whitespace line and exactly one final newline. Then paste the re-run of the 962-file corpus check reporting 0. Also paste the re-run of the `backlog._render_item` probe from F-8 showing the surviving trailing-space line is now gone through the write path.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the comment added at the normalization site including its measured basis, paste the `.editorconfig`/hook diff implementing the OQ-02 answer, and state which option was chosen. Paste a re-measured count of two-space hard breaks in the tracked corpus, so the "costs nothing today" claim is evidence rather than recollection.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste all four new tests' names and the `python3 -m pytest tests/test_git_commit_helper.py tests/test_commit_lock.py` summary line. ALSO paste the rewrite tests FAILING against pre-change code (stash the source change and re-run), proving they bite; and paste the refusal tests passing BOTH before and after, proving that path did not change.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste instrumented counts showing ONE `writer_lock` acquisition and ONE isolated worktree created per `offer_commit` call in the retry case, plus a post-run `git worktree list` and a directory listing of the repo parent showing no leftover `.aw-isocommit-` directory. Paste the peer-write-survives demonstration for a RETRIED commit. Paste the bare `python3 -m pytest` summary line and compare it to the stated baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened. A reviewer should note that this plan DELIBERATELY DEPARTS from its backlog item's prescribed fix location, with the measured reason recorded in the workflow history and in F-1/F-2; if that reasoning is wrong, the plan is wrong at its root rather than in detail.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. Take particular care that this plan edits the very commit path the executor will use to commit its own work: verify with `git diff --cached --name-only` before each commit and re-verify after any failed hook, and if the change under test breaks committing, fall back to a raw path-scoped `git commit` rather than working around the helper. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
