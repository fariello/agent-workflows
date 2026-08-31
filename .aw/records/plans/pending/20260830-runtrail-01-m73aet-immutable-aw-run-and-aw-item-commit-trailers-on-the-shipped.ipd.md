# IPD: immutable AW-Run and AW-Item commit trailers on the shipped commit path

- Date: 2026-08-30
- Kind: child
- Concern: Nothing marks a commit as belonging to a particular run and work item, so no checker can tell which commits a run actually produced. Spec `25kzda` 4.6 is explicit that the deterministic checker "finds run-owned commits by required immutable trailers such as `AW-Run: <run-id>` and `AW-Item: <id6>`, then proves their tree diffs" and that it must NOT assume every commit between the baseline and the ending HEAD belongs to the run. Without the trailers, a concurrent commit by another session or a human is indistinguishable from run-owned work, which in a SHARED CHECKOUT like this one is the normal case rather than the edge case. Verified wholly unbuilt at HEAD `738980ec`: `AW-Run` and `AW-Item` together grep to ZERO hits across `agent_workflows/` and `tests/`.
- Scope: Add an optional `trailers` parameter to the SHIPPED `git_commit_helper.offer_commit`, append the trailers to the commit message per Git trailer convention, and thread the parameter through `aw commit` (`work_cmd.run_commit`). Excludes creating any new commit module, excludes wiring the trailers into either runner module (deferred, see OQ-01), excludes the quarantine and containment transaction, and excludes changing the default behavior of any existing caller.
- Scope-Paths: agent_workflows/git_commit_helper.py, agent_workflows/work_cmd.py, tests/test_git_commit_helper.py
- Item-Dependencies: none
- Status: to-review
- Set: runtrail
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: m73aet
- Blocks-Release: next
- From-Spec: 25kzda

## Workflow history
- 2026-08-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): SUPERSEDES `k7o7el` (detrun-04), inheriting ONLY the single residue its own second review left standing, and inheriting its `- Blocks-Release: next` gate so retiring `k7o7el` does not silently drop it. `k7o7el` was `REJECT - NEEDS REPLAN` twice: its worktree allocator, lease table, and scope assertion are shipped as `worktree_lease.py`, and its proposed `commit_gateway.py` would have forked `git_commit_helper.offer_commit`, the path AGENTS.md names as the one immune to index pollution by construction. Its review reduced the residue from three items to ONE, and named the correct shape for it: a `trailers` parameter on the shipped helper, not a new module. That is exactly what this plan does.
- 2026-08-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Let a commit say which run and which work item produced it, by adding an optional parameter to the one commit path the repository already uses, so a checker can identify run-owned commits instead of guessing from commit order.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: extend the shipped commit path

- [ ] E-01 Add an optional `trailers: Sequence[str] = ()` keyword parameter to the shipped `git_commit_helper.offer_commit`. MEASURED starting point so the executor does not rediscover it: the function is at `agent_workflows/git_commit_helper.py:133` and its current signature is `(repo_root, paths, *, message, assume_yes=False, no_commit=False, interactive=None, on_unrelated_staged="scope")`. The single git invocation that consumes the message is `_git(repo_root, ["commit", "-m", message, "--", *our_staged])` at `:245`. The parameter MUST default to empty so every existing caller is byte-for-byte unaffected; this module is a low-level LEAF reused by `aw archive`, `aw group`, `aw rename`, `aw research set-assign`/`mv`, the shared `set` engine, and `specs` (its own docstring, `:3-6`), so a behavior change here reaches all of them. Do NOT alter the path-scoping, the `--no-verify` prohibition, the no-push rule, or the index snapshot/rollback logic; the trailers are additive to the MESSAGE only.
  - Depends on: none
  - Expected outcome: `offer_commit` accepts `trailers` and defaults it empty; with no trailers passed, the composed message and the resulting commit are identical to today's; the parameter is keyword-only, consistent with the rest of the signature.
  - Execution state: pending

- [ ] E-02 Implement the trailer COMPOSITION per Git trailer convention: trailers form a block at the END of the message, separated from the body by ONE blank line. Handle the three cases that actually break naive string concatenation, all of which the retired plan's review named explicitly: (a) a MULTILINE body, (b) a body that ALREADY ends in a trailer block (the new trailers must join that block rather than starting a second one separated by a blank line, since a blank line inside the trailer block terminates it and makes the earlier trailers cease to parse as trailers), and (c) a body with NO trailing newline. Compose the message as data and keep the function pure so all three cases are testable without invoking git. Do NOT hand-roll a trailer PARSER: this item only needs to append correctly, and detecting case (b) requires recognizing a trailing run of `Key: value` lines, which is a bounded, well-defined check.
  - Depends on: E-01
  - Expected outcome: a single-line body, a multiline body, a body already ending in trailers, and a body without a trailing newline all produce a message whose trailer block parses as trailers (verifiable with `git interpret-trailers --parse` or `git log --format=%(trailers)`); no case produces two blank-line-separated trailer blocks; composition is a pure function testable without git.
  - Execution state: pending

- [ ] E-03 Thread the parameter through `aw commit` so a caller that knows its run and item can pass them. MEASURED: the verb is `work_cmd.run_commit` (`agent_workflows/work_cmd.py:360`), documented as committing in-scope paths "via the SHARED git_commit_helper (no forked commit path, no add -A, no push)". Pass the trailers through; do NOT invent a new CLI surface for them in this plan and do NOT make them required, because the values come from a live run and this plan deliberately does not touch the runners (see Deferred). If threading them requires a new CLI flag to be useful at all, STOP and report rather than adding a flag whose only caller does not exist yet: a flag with no consumer is a public contract taken on for nothing.
  - Depends on: E-02
  - Expected outcome: `run_commit` can pass trailers to `offer_commit`; `aw commit` behavior is unchanged when no trailers are supplied; no new required argument and no new public flag is added without reporting first.
  - Execution state: pending

- [ ] E-04 Extend `tests/test_git_commit_helper.py` with the falsifiable cases. MUST cover: each of E-02's three body shapes producing a PARSEABLE trailer block, asserted by asking git to parse the trailers rather than by string comparison (a string assertion would pass on a malformed block that git does not recognize); the `AW-Run:`/`AW-Item:` shape specifically; a no-trailers call producing a commit identical to today's; and evidence that the surrounding contract still holds with trailers present (paths still scoped, nothing extra staged, no push). This file is SHIPPED and shared: add cases, and do NOT weaken, remove, or alter any existing assertion.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: every case above passes; the trailer assertions are made through git's own trailer parsing; the existing tests in the file pass unchanged; the new tests FAIL if the composition logic is reverted.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THERE IS ONE COMMIT PATH AND IT IS THE THING TO EXTEND. `git_commit_helper.offer_commit` (`:133`) snapshots the index before staging, stages only the caller's explicit paths, commits only the intersection, and on failure resets only its own paths. AGENTS.md names this path as the one "immune by construction" to sweeping a co-worker's staged work into your commit. The retired `k7o7el` proposed `commit_gateway.py`, which would have forked exactly this. Extend, do not fork.
- IT IS A LEAF MODULE WITH MANY CALLERS. Its own docstring (`:3-6`) lists `aw archive`, `aw group`, `aw rename`, `aw research set-assign`/`mv`, the shared `set` engine, and `specs`. This is why the new parameter must default to empty and must not change composed messages for existing callers.
- THE GIT SUBPROCESS WRAPPER IS ALSO SINGLE-SOURCED. `_git` (`:57`) is documented as "the single canonical git-subprocess wrapper for the codebase", with `ipd_lifecycle._git` delegating to it. Do not add a second subprocess call site.
- THE WORKTREE MACHINERY THE RETIRED PLAN WANTED TO BUILD IS SHIPPED. `worktree_lease.py` owns allocation, the lease table, and scope assertion, and the worktrees constant is `worktree_lease.WORKTREES_SUBDIR = ".aw/worktrees"`, NOT the `.aw/state/worktrees/` path the retired plan proposed writing to. Nothing in this plan touches any of it.
- LANE TEARDOWN IS OWNED ELSEWHERE AND IS DANGEROUS TO TOUCH. The retired plan's review resolved that the approved `wtiso` orchestrator (`bl9q3d`) assigns teardown and retention to `rchpms`, and that an `unknown` untracked file must PREVENT teardown. Five `wtiso` lanes currently hold verified work reachable only from those branches. This plan touches no lane and no teardown path.
- `LANE_OUTCOMES` IS A CLOSED SET. `run_ledger_schema.LANE_OUTCOMES` is the existing outcome vocabulary and `worktree_lease.LeaseConflictError` is the existing conflict signal. The retired plan's proposed `ownership_conflict` reason code has zero hits; do not introduce a parallel vocabulary.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `agent_workflows/` (absence) | The trailers are WHOLLY unbuilt, so no checker can identify run-owned commits at all. In a shared checkout where concurrent commits by other sessions and the human are routine, "every commit since baseline" is not a usable proxy. | `rg -n 'AW-Run\|AW-Item' agent_workflows/ tests/ --include=*.py` returns ZERO hits at HEAD `738980ec` |
| F2 | HIGH | retired `k7o7el` E-01 vs `worktree_lease.py` | The retired plan's first review cited the WRONG module (`orchestrate_isolation.py`) as the canonical worktree lease manager, repeating the plan's own Step-0 bullet without checking it; its second review found `worktree_lease.py:4-16` states that module "never creates a git worktree or session" and holds "NO per-path exclusive-ownership lease". The corrected citation rejects the item MORE completely. Inheriting the pass-1 citation would resurrect a duplicate. | `k7o7el`'s own pass-2 gate text recording the self-correction |
| F3 | HIGH | retired `k7o7el` proposed `commit_gateway.py` | A second commit path is the highest-risk possible duplication in this repo, because the shipped one is the mechanism that prevents committing a co-worker's staged work. Two commit paths means one of them lacks that protection. | `offer_commit`'s snapshot/intersection/rollback logic at `:225-259`; AGENTS.md naming it immune by construction |
| F4 | MED | spec `25kzda` 4.6 | The trailers are load-bearing for a CORRECTNESS property, not bookkeeping: the checker "does not assume every commit between baseline and ending HEAD belongs to this run", which "permits unrelated concurrent commits while refusing any overlap with the item's lease or scope". That is precisely the shared-checkout hazard AGENTS.md warns about. | spec 4.6 closing paragraph |
| F5 | MED | Git trailer semantics | A blank line inside a trailer block TERMINATES it, so appending a second blank-line-separated block silently stops the earlier trailers from parsing as trailers. This is the case (b) in E-02 and is the reason a naive `message + "\n\n" + trailers` is wrong. It fails silently: the commit succeeds and the trailers are simply not there. | `git interpret-trailers` semantics; the retired plan's review named this case explicitly |
| F6 | LOW | `work_cmd.run_commit:360` | The natural consumer of the trailers is a live run, and this plan deliberately does not touch the runners. So `aw commit` gains the ABILITY to carry trailers with no in-tree caller passing them yet. Stated rather than hidden; see the Scope check. | `run_commit` docstring; Deferred section below |

## Proposed changes (ordered, validatable)

1. Add the optional keyword `trailers` to the shipped `offer_commit`, defaulting empty (E-01).
2. Compose the trailer block correctly for all three body shapes (E-02).
3. Thread it through `aw commit` without adding a consumer-less flag (E-03).
4. Cover it with tests that assert through git's own trailer parsing (E-04).

## Deferred / out of scope (with reason)

- WIRING THE TRAILERS INTO `oc_runipd.py` / `agy_runipd.py`. Deferred so this plan touches neither runner, which removes the `rununify` (`5e4sb6`) sequencing conflict entirely rather than answering it. Same move that unblocked `hostcap-01` (`mjx7ne`). The honest consequence is in the Scope check.
- THE QUARANTINE EVIDENCE BUNDLE AND `contained: true` RECEIPT. The retired plan's review resolved that this may only be an EXTENSION of `wtiso-03`'s `lane_status.harvest_and_teardown_gate`, which is owned by an approved plan in a stack holding irreplaceable lane work. Not this plan.
- THE 6-CLASS ABORT TAXONOMY of spec 4.1. It must emit the shipped `run_ledger_schema.LANE_OUTCOMES` values, and it belongs with the containment work above.
- A NEW `commit_gateway.py` OR `worktree_containment.py`. Explicitly rejected (F2, F3); these were the retired plan's central defects.
- ENFORCING that the engine rather than the agent invoked the commit (spec's `RUN-COMMIT-GATEWAY`). That is host ENFORCEMENT, not a trailer, and it is the same class of unbuilt security boundary that `hostcap-01`'s OQ-03 escalated to the maintainer. Adding a trailer does not make a commit gateway; do not let the two be conflated.

## Scope check

- Over-scope: none. Two shipped files gain an additive optional parameter and its threading; one shipped test file gains cases. No new module.
- Under-scope, DELIBERATE and stated plainly: when this plan completes, nothing in the tree PASSES trailers yet, because the values come from a live run and the runner wiring is deferred. The capability lands tested and available; it identifies no commits until a follow-up wires it. That is the price of not touching the two runner modules `rununify` is chartered to unify.
- Under-scope, ACKNOWLEDGED: this plan makes commits IDENTIFIABLE, not GUARANTEED. A trailer is a claim in a commit message, not an enforced boundary; an agent committing by hand can omit or forge one. The spec's enforcement half (`RUN-COMMIT-GATEWAY`) is deferred above. Do not describe this work as preventing anything.
- CONTENTION: `git_commit_helper.py` and `work_cmd.py` are low-level shared modules in a checkout where several sessions commit concurrently. Re-read both immediately before editing and verify the staged set before every commit.

## Required tests / validation

- `tests/test_git_commit_helper.py` must pass with every case in E-04, and every PRE-EXISTING assertion in that file must pass unchanged. If a change to the shared helper breaks one, the extension is wrong, not the test.
- ASSERT THROUGH GIT, NOT THROUGH STRINGS (HARD): the trailer-block cases must be validated by having git parse the trailers (for example `git interpret-trailers --parse` or `git log --format=%(trailers)`). A string-equality assertion would pass on a block git does not recognize, which is exactly the silent failure F5 describes.
- FALSIFIABILITY: with the composition logic reverted or stubbed, the new tests must FAIL. Paste that failure, not just the pass.
- REGRESSION GUARD FOR EXISTING CALLERS: demonstrate that a no-trailers call produces the same commit message as today, since this leaf module has at least six callers.
- INVOKE THE SUITE BARE: `python3 -m pytest`. `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`.
- BASELINE IS A MEASUREMENT: take before/after counts yourself with the `git rev-parse HEAD` they were measured at. HEAD moves hourly here.
- `aw check plans` is RED on pre-existing findings owned by other Sets (measured 901 at HEAD `7e5ba287`). Do NOT claim it passes; the bar is NO-WORSENING against your own fresh baseline.
- `aw sanitize --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- This plan implements the trailer half of spec `25kzda` 4.6. It does not change the spec text.
- Record which of the spec's Section 4.2 `RUN-*` codes now becomes reachable, because `RUN-COMMIT-CONTENTS` and `RUN-COMMIT-GATEWAY` both depend on these trailers existing, and a successor of `7f7782` needs to know which of the 13 codes are still genuinely unbuilt. Leaving that unrecorded is how two plans both come to believe a code is missing.
- If `git_commit_helper.py`'s module docstring enumerates the contract it enforces, extend it to mention the optional trailers so the next reader does not have to infer them from the signature.

## Open questions

### OQ-01: Must the trailer wiring wait for `rununify`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE QUESTION IS DISSOLVED, not answered, which is what lets this plan proceed now. The retired `k7o7el` carried this as its BLOCKING OQ-03 (inherited from the parent Set) because its items edited both runner modules, doubling the surface `rununify` (`5e4sb6`) must reconcile; its own recommendation was to wait, which would have parked the work behind a Set whose child plans are still unwritten and whose sequencing is only partly authorized. This plan defers the runner wiring entirely and touches neither runner, so the conflict cannot arise. The precedent is `hostcap-01` (`mjx7ne`), which dissolved the identical question the identical way at the maintainer's direction. The honest cost is recorded in the Scope check rather than hidden.

### OQ-02: Should the trailer values be validated, and how strictly?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence: validate the SHAPE, refuse nothing else, and do it in this module. A trailer is `Key: value` with the key matching Git's trailer token rules, so a value containing a newline would silently break the block (F5) and must be rejected at composition time rather than producing a malformed commit. That is a structural check this module can make alone. Do NOT go further: verifying that an `AW-Item:` id6 resolves to a real artifact is a CROSS-TREE concern belonging to the `aw check` surface, which is where every other id6-resolution rule in this repo lives (`check.from-backlog-dangling`, `check.from-spec-dangling`), and duplicating that resolution inside a commit helper would fork it. So: reject a structurally impossible trailer, and leave referential validity to the checker.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new signature showing `trailers` is keyword-only and defaults empty. Paste a no-trailers commit's full message and compare it against the same commit composed at the pre-change HEAD, proving byte-identical. Paste the list of callers you checked (the docstring names at least six) and evidence none passes a positional argument that this change would shift.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for EACH of the three body shapes (multiline; already ending in a trailer block; no trailing newline), paste the composed message AND the output of git parsing its trailers, proving the trailers are recognized. For the already-ending-in-trailers case, paste evidence the EARLIER trailers still parse (F5's silent failure), which a string comparison cannot show. Paste evidence the composition function is pure and was tested without invoking git.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw commit` passing trailers through to a real commit and the resulting `git log` trailers. Paste an `aw commit` invocation WITHOUT trailers behaving exactly as before. State explicitly whether you added any new CLI flag; if you did, paste the report you were required to make first (E-03 forbids adding one silently).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_git_commit_helper.py` with counts, and the BARE `python3 -m pytest` summary line with the `git rev-parse HEAD` it was measured at plus your own before-baseline at that HEAD. Paste a `git diff` of the test file proving no existing assertion was weakened, removed, or altered. Paste proof the new tests are NOT VACUOUS: with the composition logic stubbed, show them FAILING. Paste the no-worsening comparison for `aw check plans` (both counts measured, not remembered).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 4 E-leaves in one task group, well under the thresholds. One concern throughout: let a commit record which run and item produced it.

Open questions: NEITHER is blocking and neither needs a maintainer decision. OQ-01 is DISSOLVED by deferring the runner wiring (the `hostcap-01` precedent), which is what lets this plan run without waiting on `rununify`. OQ-02 is resolved from repository evidence: validate trailer SHAPE here, and leave id6 referential validity to the `aw check` surface where every comparable rule already lives.

Scope fence: touch ONLY `agent_workflows/git_commit_helper.py`, `agent_workflows/work_cmd.py`, and `tests/test_git_commit_helper.py` (additive cases only; no existing assertion weakened, removed, or altered). Do NOT create `commit_gateway.py` or `worktree_containment.py`. Do NOT edit `worktree_lease.py`, `lane_status.py`, `run_ledger_schema.py`, `oc_runipd.py`, or `agy_runipd.py`. Do NOT write worktrees anywhere (the constant is `worktree_lease.WORKTREES_SUBDIR = ".aw/worktrees"`, not `.aw/state/worktrees/`). Do NOT delete or force-teardown any lane or its untracked files: five `wtiso` lanes hold verified work reachable only from those branches. Do NOT introduce the reason code `ownership_conflict` (`LANE_OUTCOMES` is closed; `LeaseConflictError` is the existing signal). Do NOT implement commit-gateway ENFORCEMENT. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): paste ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Do NOT claim `aw check plans` passes; it is RED on 901 pre-existing findings owned by other Sets (measured at HEAD `7e5ba287`), and the bar is no-worsening against your own fresh baseline. Do NOT describe this work as preventing an agent from committing outside the gateway: a trailer is a claim, not a boundary, and nothing passes these trailers until a follow-up wires the runners. Say both plainly in the terminal history.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never `-a`, and never push. Several sessions commit to this checkout CONCURRENTLY, and this plan edits two LOW-LEVEL SHARED modules: run `git diff --cached --name-only` before every commit and unstage anything you did not modify, with `git restore --staged <path>`. A pre-commit hook failure INVALIDATES that check, so re-run it after any failed commit attempt before retrying. Prefer `aw commit <plan> -- <paths>`, which is immune to index pollution by construction.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
