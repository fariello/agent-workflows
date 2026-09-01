# IPD: immutable AW-Run and AW-Item commit trailers on the shipped commit path

- Date: 2026-08-30
- Kind: child
- Concern: Nothing marks a commit as belonging to a particular run and work item, so no checker can tell which commits a run actually produced. Spec `25kzda` 4.6 is explicit that the deterministic checker "finds run-owned commits by required immutable trailers such as `AW-Run: <run-id>` and `AW-Item: <id6>`, then proves their tree diffs" and that it must NOT assume every commit between the baseline and the ending HEAD belongs to the run. Without the trailers, a concurrent commit by another session or a human is indistinguishable from run-owned work, which in a SHARED CHECKOUT like this one is the normal case rather than the edge case. Verified wholly unbuilt at HEAD `738980ec`: `AW-Run` and `AW-Item` together grep to ZERO hits across `agent_workflows/` and `tests/`.
- Scope: Add an optional `trailers` parameter to the SHIPPED `git_commit_helper.offer_commit`, append the trailers to the commit message per Git trailer convention, and thread the parameter through `aw commit` (`work_cmd.run_commit`). Excludes creating any new commit module, excludes wiring the trailers into either runner module (deferred, see OQ-01), excludes the quarantine and containment transaction, and excludes changing the default behavior of any existing caller.
- Scope-Paths: agent_workflows/git_commit_helper.py, agent_workflows/work_cmd.py, tests/test_git_commit_helper.py
- Item-Dependencies: none
- Status: approved
- Set: runtrail
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: m73aet
- Approval: 2026-08-31, human ("approved"): Maintainer approved 2026-08-31 in session, after plan-review round 1 (m73aet APPROVE 0 findings; 6lu3rq and wlxkoz APPROVE WITH REVISIONS APPLIED, all findings FIXED in place, zero unresolved, no open questions).
- Blocks-Release: next
- From-Spec: 25kzda

## Workflow history
- 2026-09-01 executed (opencode/its_direct/pt3-claude-opus-5-1m-us): E-01..E-04 implemented in commit `81c67a6f`; V-01..V-04 verified with pasted evidence. Optional keyword-only `trailers=` on the shipped `offer_commit` (never a second commit path), a PURE `compose_message_with_trailers`, shape validation failing CLOSED, and threading through `aw commit` with NO new CLI flag. Tests 17 -> 48 in `tests/test_git_commit_helper.py`, asserted through GIT's own parser rather than string comparison. HONEST STATEMENTS THE PLAN REQUIRED: (1) nothing in the tree PASSES trailers yet, because the runner wiring is deferred, so this identifies no commits until a follow-up wires it - including this very commit, which carries none; (2) a trailer is a CLAIM in a commit message, not an enforced boundary - an agent committing by hand can omit or forge one, and `RUN-COMMIT-GATEWAY` (spec line 539) remains wholly unbuilt, so this is NOT progress on preventing an out-of-gateway commit; (3) `aw check plans` is RED and I do not claim otherwise - measured 5 findings before AND after at my own baselines (not the plan's remembered 901 at a different HEAD), all owned by other Sets; (4) the bare suite keeps 15 PRE-EXISTING `tests/test_run_viewer.py` failures, unchanged, outside this plan's scope. Beyond the plan: E-02's literal "trailing run of `Key: value` lines" test proved INSUFFICIENT, so the block predicate models git's ACTUAL documented rule (all-trailers, or git-generated + >=25%, preceded by a blank line, at end or before a `---` divider), cross-checked against `git interpret-trailers --parse` (decision D-1). Two of seven mutations initially SURVIVED, exposing genuine gaps that drove two extra tests. Decisions D-1/D-2/D-3 recorded in the run register.
- 2026-08-31 approved (aw set, --by-human): Maintainer approved 2026-08-31 in session, after plan-review round 1 (m73aet APPROVE 0 findings; 6lu3rq and wlxkoz APPROVE WITH REVISIONS APPLIED, all findings FIXED in place, zero unresolved, no open questions).
- 2026-08-31 reviewed (aw set): plan-review round 1 complete; revisions applied. See .aw/records/reviews/ for the typed findings and decisions.
- 2026-08-31 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): plan-review round 1: APPROVE; ZERO findings. Verified at HEAD 381dbd5c: offer_commit really is at git_commit_helper.py:133 with its single message-consuming git call at :245, work_cmd.run_commit at :360, and AW-Run:/AW-Item: really are ZERO-hit. Two claims verified BY EXECUTION rather than reading: (1) E-02's case-(b) hazard is REAL and reproducible - appending a trailer after a blank line to a body already ending in a trailer block makes git's own parser DROP the earlier trailers (a body ending 'Co-authored-by: x' yields ONLY 'AW-Run: r1' from --parse), so the plan's subtlest requirement is correctly diagnosed; (2) git interpret-trailers --parse is available here, so V-02's evidence is collectable. Endorsed three restraints: the blast radius is correctly handled (23 call sites across 10+ modules, parameter defaults empty), E-03's refusal to add a flag with no consumer is correct (verified work_cmd has no run-id access), and E-04 asserting through git's parser rather than string comparison is exactly why the malformed case is catchable. Findings table deliberately EMPTY rather than padded. Two reversible decisions recorded (D-1, D-2). Review artifact: .aw/records/reviews/20260831-runtrail-01-m73aet-immutable-aw-run-and-aw-item-commit-trailers.review.md
- 2026-08-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): SUPERSEDES `k7o7el` (detrun-04), inheriting ONLY the single residue its own second review left standing, and inheriting its `- Blocks-Release: next` gate so retiring `k7o7el` does not silently drop it. `k7o7el` was `REJECT - NEEDS REPLAN` twice: its worktree allocator, lease table, and scope assertion are shipped as `worktree_lease.py`, and its proposed `commit_gateway.py` would have forked `git_commit_helper.offer_commit`, the path AGENTS.md names as the one immune to index pollution by construction. Its review reduced the residue from three items to ONE, and named the correct shape for it: a `trailers` parameter on the shipped helper, not a new module. That is exactly what this plan does.
- 2026-08-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Let a commit say which run and which work item produced it, by adding an optional parameter to the one commit path the repository already uses, so a checker can identify run-owned commits instead of guessing from commit order.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: extend the shipped commit path

- [x] E-01 Add an optional `trailers: Sequence[str] = ()` keyword parameter to the shipped `git_commit_helper.offer_commit`. MEASURED starting point so the executor does not rediscover it: the function is at `agent_workflows/git_commit_helper.py:133` and its current signature is `(repo_root, paths, *, message, assume_yes=False, no_commit=False, interactive=None, on_unrelated_staged="scope")`. The single git invocation that consumes the message is `_git(repo_root, ["commit", "-m", message, "--", *our_staged])` at `:245`. The parameter MUST default to empty so every existing caller is byte-for-byte unaffected; this module is a low-level LEAF reused by `aw archive`, `aw group`, `aw rename`, `aw research set-assign`/`mv`, the shared `set` engine, and `specs` (its own docstring, `:3-6`), so a behavior change here reaches all of them. Do NOT alter the path-scoping, the `--no-verify` prohibition, the no-push rule, or the index snapshot/rollback logic; the trailers are additive to the MESSAGE only.
  - Depends on: none
  - Expected outcome: `offer_commit` accepts `trailers` and defaults it empty; with no trailers passed, the composed message and the resulting commit are identical to today's; the parameter is keyword-only, consistent with the rest of the signature.
  - Execution state: performed

- [x] E-02 Implement the trailer COMPOSITION per Git trailer convention: trailers form a block at the END of the message, separated from the body by ONE blank line. Handle the three cases that actually break naive string concatenation, all of which the retired plan's review named explicitly: (a) a MULTILINE body, (b) a body that ALREADY ends in a trailer block (the new trailers must join that block rather than starting a second one separated by a blank line, since a blank line inside the trailer block terminates it and makes the earlier trailers cease to parse as trailers), and (c) a body with NO trailing newline. Compose the message as data and keep the function pure so all three cases are testable without invoking git. Do NOT hand-roll a trailer PARSER: this item only needs to append correctly, and detecting case (b) requires recognizing a trailing run of `Key: value` lines, which is a bounded, well-defined check.
  - Depends on: E-01
  - Expected outcome: a single-line body, a multiline body, a body already ending in trailers, and a body without a trailing newline all produce a message whose trailer block parses as trailers (verifiable with `git interpret-trailers --parse` or `git log --format=%(trailers)`); no case produces two blank-line-separated trailer blocks; composition is a pure function testable without git.
  - Execution state: performed

- [x] E-03 Thread the parameter through `aw commit` so a caller that knows its run and item can pass them. MEASURED: the verb is `work_cmd.run_commit` (`agent_workflows/work_cmd.py:360`), documented as committing in-scope paths "via the SHARED git_commit_helper (no forked commit path, no add -A, no push)". Pass the trailers through; do NOT invent a new CLI surface for them in this plan and do NOT make them required, because the values come from a live run and this plan deliberately does not touch the runners (see Deferred). If threading them requires a new CLI flag to be useful at all, STOP and report rather than adding a flag whose only caller does not exist yet: a flag with no consumer is a public contract taken on for nothing.
  - Depends on: E-02
  - Expected outcome: `run_commit` can pass trailers to `offer_commit`; `aw commit` behavior is unchanged when no trailers are supplied; no new required argument and no new public flag is added without reporting first.
  - Execution state: performed

- [x] E-04 Extend `tests/test_git_commit_helper.py` with the falsifiable cases. MUST cover: each of E-02's three body shapes producing a PARSEABLE trailer block, asserted by asking git to parse the trailers rather than by string comparison (a string assertion would pass on a malformed block that git does not recognize); the `AW-Run:`/`AW-Item:` shape specifically; a no-trailers call producing a commit identical to today's; and evidence that the surrounding contract still holds with trailers present (paths still scoped, nothing extra staged, no push). This file is SHIPPED and shared: add cases, and do NOT weaken, remove, or alter any existing assertion.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: every case above passes; the trailer assertions are made through git's own trailer parsing; the existing tests in the file pass unchanged; the new tests FAIL if the composition logic is reverted.
  - Execution state: performed

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

- This plan implements the trailer half of spec `25kzda` 4.6. It does not change the spec text. VERIFIED the spec says what the plan quotes: the spec is `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, and line 608 reads "The checker finds run-owned commits by required immutable trailers such as `AW-Run: <run-id>` and `AW-Item: <id6>`, then proves their tree diffs. It does not assume every commit between baseline and ending HEAD belongs to this run." Line 28 also names "the hash-chained run ledger with `AW-Run:`/`AW-Item:` commit trailers", so the key spellings implemented here match the spec exactly.
- `RUN-*` CODE STATUS AFTER THIS PLAN (recorded so a successor of `7f7782` does not re-derive it, and so two plans do not both believe a code is missing). Both relevant codes are at spec lines 538-539:
  - `RUN-COMMIT-CONTENTS` (line 538) - "Run-owned commits identified by immutable run/item trailers, commit parents, trees, and action-owned delta". Its trailer PREREQUISITE is now BUILT: a commit can carry `AW-Run`/`AW-Item`, and `git_commit_helper.TRAILER_KEY_RUN`/`TRAILER_KEY_ITEM` single-source the spelling a checker must match. The CODE ITSELF REMAINS UNBUILT: nothing yet emits it, and its "path union equals the action-owned delta" proof needs the tree-diff comparison, which is not in this scope. So: unblocked, not implemented.
  - `RUN-COMMIT-GATEWAY` (line 539) - "The engine, not the agent, invoked `git commit ... -- <explicit paths>`". STILL WHOLLY UNBUILT and deliberately NOT advanced here. It requires a captured gateway event and argv, i.e. ENFORCEMENT, which a trailer cannot supply. Do not treat this plan as progress on it (see the Scope check's second under-scope note).
  - NOT REACHABLE YET, because nothing passes trailers: until a runner supplies `AW-Run`/`AW-Item`, no real commit carries them, so a checker keying on them would find zero run-owned commits. The capability is available and tested; the wiring is the deferred follow-up.
- `git_commit_helper.py`'s module docstring DOES enumerate the contract it enforces, so it gained a bullet for the optional trailers (with the spec rationale and the honest "a trailer is a claim, not a boundary" limit) plus a pointer to `compose_message_with_trailers`. `work_cmd.py`'s docstring gained the matching note on its `aw commit` bullet. Neither reader now has to infer the feature from a signature.

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

- [x] V-01 validates E-01
  - Required evidence: paste the new signature showing `trailers` is keyword-only and defaults empty. Paste a no-trailers commit's full message and compare it against the same commit composed at the pre-change HEAD, proving byte-identical. Paste the list of callers you checked (the docstring names at least six) and evidence none passes a positional argument that this change would shift.
  - Observed evidence: PASS. `trailers: Sequence[str] = ()` is keyword-only (after the bare `*`) and defaults empty, asserted mechanically in `test_trailers_is_keyword_only_and_defaults_empty` (which also pins the positional set to `[repo_root, paths]`). No-trailers commits are BYTE-IDENTICAL to raw `git commit -m` across four body shapes, compared via stored bytes (`git cat-file commit`, not `%B`, which appends its own newline). All SEVEN `offer_commit` call sites checked BY AST: every one passes exactly 2 positional args, so no argument can shift. Detail below.

    SIGNATURE (`agent_workflows/git_commit_helper.py`), `trailers` after the bare `*` so it is keyword-only, defaulting to the empty tuple:

    ```
    def offer_commit(
        repo_root: Path,
        paths: Sequence[str],
        *,
        message: str,
        assume_yes: bool = False,
        no_commit: bool = False,
        interactive: Optional[bool] = None,
        on_unrelated_staged: str = "scope",
        trailers: Sequence[str] = (),
    ) -> CommitOutcome:
    ```

    Asserted mechanically rather than by eye, in `test_trailers_is_keyword_only_and_defaults_empty`, which also pins the positional set to `["repo_root", "paths"]` so no call site can shift.

    BYTE-IDENTICAL NO-TRAILERS BEHAVIOR. The pre-change code path was `git commit -m message` verbatim, so `test_no_trailers_commit_is_byte_identical_to_pre_change_behavior` commits the same content BOTH ways in one repo and compares the STORED message bytes (`git cat-file commit`, not `--format=%B`, which appends a newline of its own and so cannot support a byte claim). Four shapes: subject-only, subject+body, multiline, and a body already ending in `Co-authored-by:`. All identical. `test_compose_with_no_trailers_is_byte_identical` additionally asserts `compose_message_with_trailers(body, []) == body` for five shapes including the empty string.

    Live confirmation through `aw commit` with no trailers supplied (temp repo, HEAD `aab55714`):

    ```
    --- trailers (expect EMPTY) ---
    '\n'
    --- stored message bytes ---
    'feat: no trailers here\n\nbody\n'
    ```

    ALL CALL SITES CHECKED, by AST rather than by grep, so a multi-line call cannot hide. Every one passes exactly TWO positional arguments (`repo_root`, `paths`) and everything else by keyword, so adding a keyword-only parameter cannot shift any argument:

    ```
    agent_workflows/cli.py:3880 positional=2 keywords=['message', 'assume_yes', 'no_commit', 'on_unrelated_staged']
    agent_workflows/oc_runipd.py:1183 positional=2 keywords=['message', 'assume_yes', 'interactive']
    agent_workflows/plans_archive.py:296 positional=2 keywords=['message', 'assume_yes', 'no_commit', 'on_unrelated_staged']
    agent_workflows/research_archive.py:400 positional=2 keywords=['message', 'assume_yes', 'no_commit', 'on_unrelated_staged']
    agent_workflows/specs.py:650 positional=2 keywords=['message', 'assume_yes', 'no_commit', 'on_unrelated_staged']
    agent_workflows/status_set.py:1076 positional=2 keywords=['message', 'assume_yes', 'no_commit', 'on_unrelated_staged']
    agent_workflows/work_cmd.py:470 positional=2 keywords=['message', 'assume_yes', 'no_commit', 'on_unrelated_staged', 'trailers']
    ```

    That is SEVEN call sites (the docstring said "at least six"); `work_cmd.py` is the only one passing `trailers`. Across `tests/`, max positional args to `offer_commit` = 2.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: for EACH of the three body shapes (multiline; already ending in a trailer block; no trailing newline), paste the composed message AND the output of git parsing its trailers, proving the trailers are recognized. For the already-ending-in-trailers case, paste evidence the EARLIER trailers still parse (F5's silent failure), which a string comparison cannot show. Paste evidence the composition function is pure and was tested without invoking git.
  - Observed evidence: PASS. All EIGHT body shapes compose to trailers GIT parses (`git interpret-trailers --parse`, git 2.43.0), including the plan's three required shapes. F5's silent failure demonstrated side by side: the naive blank-line append LOSES a pre-existing `Co-authored-by` (git reports only AW-Run/AW-Item) while ours preserves it. Purity proven by monkeypatching both `subprocess.run` and `H._git` to raise, then composing successfully. Three shapes BEYOND the plan's three were found by probing git and are handled (mixed non-git-generated prose, sub-25% ratio, lone first paragraph); see decision D-1. Detail below.

    ALL EIGHT BODY SHAPES composed, then handed to GIT to parse (`git interpret-trailers --parse`, git 2.43.0). The three the plan required are the 2nd, 3rd, and 4th:

    ```
    OK  single-line body
       composed: 'fix: something\n\nAW-Run: run-20260901T042331Z-118022\nAW-Item: m73aet\n'
       parsed  : 'AW-Run: run-20260901T042331Z-118022\nAW-Item: m73aet'
    OK  multiline body
       composed: 'fix: something\n\nwhy this matters\nand more detail\n\nAW-Run: run-20260901T042331Z-118022\nAW-Item: m73aet\n'
       parsed  : 'AW-Run: run-20260901T042331Z-118022\nAW-Item: m73aet'
    OK  already ends in trailer block
       composed: 'fix: something\n\nbody\n\nCo-authored-by: x <x@e.com>\nAW-Run: run-20260901T042331Z-118022\nAW-Item: m73aet\n'
       parsed  : 'Co-authored-by: x <x@e.com>\nAW-Run: run-20260901T042331Z-118022\nAW-Item: m73aet'
    OK  no trailing newline
       composed: 'fix: something\n\nbody no newline\n\nAW-Run: run-20260901T042331Z-118022\nAW-Item: m73aet\n'
       parsed  : 'AW-Run: run-20260901T042331Z-118022\nAW-Item: m73aet'
    OK  body WITH trailing newline
    OK  single paragraph only
    OK  gitgen mixed block
    OK  --- divider
    ```

    Note the third case: the composed message has NO blank line before `AW-Run`, so the new trailers JOIN the existing block, and git consequently reports `Co-authored-by` ALONGSIDE them.

    F5's SILENT FAILURE, DEMONSTRATED RATHER THAN ASSERTED. The naive `message + "\n\n" + trailers` beside ours, same input, both parsed by git:

    ```
    NAIVE (message + '\n\n' + trailers):
    'AW-Run: r1\nAW-Item: m73aet'
    OURS:
    'Co-authored-by: x <x@e.com>\nAW-Run: r1\nAW-Item: m73aet'
    ```

    The naive form SILENTLY LOSES the co-author: the commit still succeeds, and only git's parser reveals it. `test_compose_preserves_preexisting_trailers_joining_the_block` asserts BOTH directions (that the naive form loses it and ours keeps it), so the test would fail if the hazard ever stopped being real. `test_trailers_join_existing_block_on_a_real_commit` repeats it end-to-end on an actual commit via `%(trailers)`.

    PURITY. `test_compose_is_pure_and_needs_no_git` monkeypatches BOTH `subprocess.run` and `H._git` to raise, then composes successfully, so the function provably invokes no subprocess. All composition tests call it directly; git is used only to CHECK the output.

    THREE EXTRA SHAPES BEYOND THE PLAN'S THREE, found by probing git rather than assuming. Git's real rule (`git-interpret-trailers(1)`) is that a group counts as trailers when it "is all trailers, or contains at least one Git-generated ... trailer and consists of at least 25% trailers", preceded by a blank line, at the end of input or just before a `---` divider. So a "looks like `Key: value`" heuristic is WRONG in three directions, each verified by asking git:

    - MIXED PROSE + non-git-generated trailer is NOT a block (`prose line` + `Key: value` -> git reports nothing), so joining it would yield a commit with NO parseable trailers;
    - a git-generated trailer UNDER 25% is not a block either (1 `Signed-off-by:` among 4 prose lines -> nothing; among 3 -> parses);
    - a LONE FIRST PARAGRAPH is never a block (git requires a preceding blank line), and that is the common case here, not an edge case: 910 of the last 2211 commit messages in this repo are single-paragraph.

    `test_is_trailer_block_matches_git_on_the_25_percent_rule` cross-checks the predicate against git's parser on eight boundary inputs including both sides of the 25% ratio, so the implementation is pinned to git's behavior and not to my reading of it. The `---` divider case is handled by inserting BEFORE the divider, which is what `git interpret-trailers` itself does with the same input (verified directly).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `aw commit` passing trailers through to a real commit and the resulting `git log` trailers. Paste an `aw commit` invocation WITHOUT trailers behaving exactly as before. State explicitly whether you added any new CLI flag; if you did, paste the report you were required to make first (E-03 forbids adding one silently).
  - Observed evidence: PASS. `aw commit` carried `AW-Run: run-20260901T042331Z-118022` + `AW-Item: zz9zz9` to real commit `7b8645c4`, confirmed via `git log --format=%(trailers)`. Without trailers (`aab55714`) the trailer output is empty and the stored bytes are exactly the caller's message. NO new CLI flag was added (verified against `aw commit --help`), so no E-03 report was owed; callers supply values via namespace attributes instead. Auto-deriving `AW-Item` from the resolved plan was deliberately REJECTED as an out-of-scope default-behavior change (decision D-3). Detail below.

    `aw commit` CARRYING TRAILERS to a real commit (throwaway repo `/tmp/opencode/awc` with a `Scope-Paths`-declaring plan, so the scope gate ran too):

    ```
    aw commit: committed 1 path(s): 7b8645c45058d4494d8639cfbbc62b29c66ef1cb
    exit: 0
    --- git-reported trailers ---
    AW-Run: run-20260901T042331Z-118022
    AW-Item: zz9zz9

    --- full message ---
    feat: demo change

    with a body paragraph

    AW-Run: run-20260901T042331Z-118022
    AW-Item: zz9zz9
    ```

    Those trailers come from `git log -1 --format=%(trailers)`, i.e. GIT's own parse of the stored commit, not from string inspection.

    `aw commit` WITHOUT trailers, same repo, unchanged behavior (empty trailer output, stored bytes exactly the caller's message):

    ```
    aw commit: committed 1 path(s): aab557146ecd1923434dc890a103ce8b78ff1a7e
    exit: 0
    --- trailers (expect EMPTY) ---
    '\n'
    --- stored message bytes ---
    'feat: no trailers here\n\nbody\n'
    ```

    NEW CLI FLAG: NONE ADDED. E-03 required stopping and reporting rather than adding a flag with no consumer, and no flag was needed, so no report was owed. Confirmed against the built parser:

    ```
    $ python3 -m agent_workflows commit --help | grep -i 'trailer|run-id|item'
    confirmed: no trailer/run-id/item flag on aw commit
    ```

    HOW A CALLER SUPPLIES THEM INSTEAD. `run_commit` already takes an `argparse.Namespace`, so the eventual runner passes either `trailers` (preformatted) or `run_id`/`item_id6` (raw ids, formatted through `git_commit_helper.run_item_trailers` so the key spelling is single-sourced and cannot drift). `_trailers_from_args` returns `[]` when neither is present. Asserted in `test_aw_commit_threads_trailers_through` for all three cases.

    DELIBERATELY NOT DONE: the plan's own id6 is NOT auto-derived into an `AW-Item` trailer. `aw commit` already knows its plan, so that was tempting and would have been WRONG here: it changes the default behavior of an existing caller, which this plan's scope explicitly excludes ("do not change the default behavior of any existing caller"). Recorded as decision D-3.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_git_commit_helper.py` with counts, and the BARE `python3 -m pytest` summary line with the `git rev-parse HEAD` it was measured at plus your own before-baseline at that HEAD. Paste a `git diff` of the test file proving no existing assertion was weakened, removed, or altered. Paste proof the new tests are NOT VACUOUS: with the composition logic stubbed, show them FAILING. Paste the no-worsening comparison for `aw check plans` (both counts measured, not remembered).
  - Observed evidence: PASS, with pre-existing failures honestly unchanged. Target file 17 -> 48 passing. BARE suite: 15 failed / 3872 passed at HEAD `26973ca6` (before) -> 15 failed / 3903 passed at HEAD `81c67a6f` (after), i.e. +31 passed and failures UNCHANGED at 15; all 15 are pre-existing `tests/test_run_viewer.py` failures outside this plan's Scope-Paths, and I do NOT claim the suite is green. Only ONE line was removed from the test file (a blank line); the 17 original tests were re-run by name and pass. Non-vacuity proven by SEVEN mutations, all caught - two initially SURVIVED and exposed real gaps in my own tests, which drove two additional tests. `aw check plans` 5 -> 5 (no worsening, all five owned by other Sets); `aw sanitize --agent` clean. Detail below.

    TARGET FILE, 17 -> 48 passing:

    ```
    $ python3 -m pytest tests/test_git_commit_helper.py     # BEFORE, at HEAD 26973ca6
    17 passed in 1.94s

    $ python3 -m pytest tests/test_git_commit_helper.py     # AFTER, at HEAD 81c67a6f
    48 passed in 1.99s
    ```

    BARE SUITE, both counts measured by me (not remembered), each with the HEAD it was taken at. Invoked bare per the contract, so `addopts` supplied `-q -n auto --dist=worksteal -m 'not slow'`:

    ```
    $ git rev-parse HEAD
    26973ca6a8ce3a26a4fae0dfaa44c3594446274a     # BEFORE
    $ python3 -m pytest
    15 failed, 3872 passed, 3 skipped, 4 xfailed in 36.25s

    $ git rev-parse HEAD
    81c67a6fe41e981db84673f42eae72b329a8ae63     # AFTER
    $ python3 -m pytest
    15 failed, 3903 passed, 3 skipped, 4 xfailed in 32.39s
    ```

    +31 passed, and the failure count is UNCHANGED at 15. Those 15 are PRE-EXISTING and NOT MINE: all are in `tests/test_run_viewer.py`, they fail identically at the pre-change HEAD `26973ca6`, and that file is outside this plan's Scope-Paths. Their mode is unrelated to this work (`AssertionError: 'Data from' not found in 'no matching runs found'`). I did NOT claim the suite is green.

    NO EXISTING ASSERTION WEAKENED, REMOVED, OR ALTERED. The complete set of removed lines in the test file diff is a single blank line (import-sort normalization):

    ```
    $ git diff HEAD~1 -- tests/test_git_commit_helper.py | grep '^-' | grep -v '^---'
    -
    ```

    Additive-only overall: `3 files changed, 683 insertions(+), 4 deletions(-)`, the 4 deletions being that blank line plus 3 reflowed docstring/signature lines. All 17 original tests were additionally re-run BY NAME to prove they still pass on their own: `17 passed, 31 deselected`.

    NON-VACUITY, PROVEN BY SEVEN MUTATIONS, each applied to the shipped module, suite re-run, then reverted (`diff` against a pristine copy confirmed byte-identical restoration afterward):

    | # | Mutation | Result |
    | --- | --- | --- |
    | 1 | Remove the join branch (naive blank-line append) | 2 failed |
    | 2 | Stub composition to return `message` unchanged | 12 failed |
    | 3 | Drop the `---` divider handling | 1 failed |
    | 4 | Remove the embedded-newline rejection | 3 failed |
    | 5 | Replace the git-generated + 25% gate with `return True` | 2 failed |
    | 6 | Remove the single-paragraph guard | 1 failed |
    | 7 | Widen the key charset to `[\w.-]` | 14 failed |

    Sample (mutation 1, the F5 case):

    ```
    E       AssertionError: pre-existing trailer lost: ['AW-Run: run-20260901T042331Z-118022', 'AW-Item: m73aet']
    FAILED tests/test_git_commit_helper.py::test_compose_preserves_preexisting_trailers_joining_the_block
    FAILED tests/test_git_commit_helper.py::test_trailers_join_existing_block_on_a_real_commit
    2 failed, 42 passed
    ```

    HONEST NOTE, because it changed the outcome. Mutations 5 and 6 initially SURVIVED (44 passed) - a real coverage gap in my own tests, not a formality. That is what prompted `test_compose_starts_a_new_block_when_git_would_not_see_one` and `test_is_trailer_block_matches_git_on_the_25_percent_rule`; both mutations now fail as shown. A further attempted mutation 4 appeared to survive but had silently FAILED TO APPLY (shell escaping); re-applied correctly via a Python heredoc and verified with `grep -n 'if False:'` before trusting the result. Had I trusted the first run, I would have reported false coverage.

    `aw check plans`, NO WORSENING, both counts measured:

    ```
    BEFORE (HEAD 26973ca6): findings: 5
    AFTER  (HEAD 81c67a6f): findings: 5
      check.ipd-dependency-findings-blocked  20260829-runprofile-03-3cm15q-...
      check.ipd-dependency-findings-blocked  20260829-runprofile-04-ygzq71-...
      check.ipd-dependency-findings-blocked  20260829-runprofile-05-p7xhhm-...
      check.lifecycle-transition-invalid     20260829-runnamecollapse-01-0soncw-...
      check.lifecycle-transition-invalid     20260830-runcodes-01-wlxkoz-...
    ```

    Identical before and after, and all five belong to OTHER Sets (`runprofile`, `runnamecollapse`, `runcodes`); none names this plan. It is RED, and I am NOT claiming it passes. The plan cited 901 findings at HEAD `7e5ba287`; my own fresh baseline at `26973ca6` is 5, so I used the measurement rather than the remembered number.

    `aw sanitize --agent`: clean (`"outcome":"clean","findings":0`). Formatting: `ruff-format` at the version the hook PINS (0.4.4) reports all three files formatted, and `pre-commit run ruff-format` passes on them. My locally installed ruff is 0.16.3 and disagrees with 0.4.4 on multi-line `assert` layout; the pinned version governs, since that is what the hook actually runs.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 4 E-leaves in one task group, well under the thresholds. One concern throughout: let a commit record which run and item produced it.

Open questions: NEITHER is blocking and neither needs a maintainer decision. OQ-01 is DISSOLVED by deferring the runner wiring (the `hostcap-01` precedent), which is what lets this plan run without waiting on `rununify`. OQ-02 is resolved from repository evidence: validate trailer SHAPE here, and leave id6 referential validity to the `aw check` surface where every comparable rule already lives.

Scope fence: touch ONLY `agent_workflows/git_commit_helper.py`, `agent_workflows/work_cmd.py`, and `tests/test_git_commit_helper.py` (additive cases only; no existing assertion weakened, removed, or altered). Do NOT create `commit_gateway.py` or `worktree_containment.py`. Do NOT edit `worktree_lease.py`, `lane_status.py`, `run_ledger_schema.py`, `oc_runipd.py`, or `agy_runipd.py`. Do NOT write worktrees anywhere (the constant is `worktree_lease.WORKTREES_SUBDIR = ".aw/worktrees"`, not `.aw/state/worktrees/`). Do NOT delete or force-teardown any lane or its untracked files: five `wtiso` lanes hold verified work reachable only from those branches. Do NOT introduce the reason code `ownership_conflict` (`LANE_OUTCOMES` is closed; `LeaseConflictError` is the existing signal). Do NOT implement commit-gateway ENFORCEMENT. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): paste ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Do NOT claim `aw check plans` passes; it is RED on 901 pre-existing findings owned by other Sets (measured at HEAD `7e5ba287`), and the bar is no-worsening against your own fresh baseline. Do NOT describe this work as preventing an agent from committing outside the gateway: a trailer is a claim, not a boundary, and nothing passes these trailers until a follow-up wires the runners. Say both plainly in the terminal history.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never `-a`, and never push. Several sessions commit to this checkout CONCURRENTLY, and this plan edits two LOW-LEVEL SHARED modules: run `git diff --cached --name-only` before every commit and unstage anything you did not modify, with `git restore --staged <path>`. A pre-commit hook failure INVALIDATES that check, so re-run it after any failed commit attempt before retrying. Prefer `aw commit <plan> -- <paths>`, which is immune to index pollution by construction.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
