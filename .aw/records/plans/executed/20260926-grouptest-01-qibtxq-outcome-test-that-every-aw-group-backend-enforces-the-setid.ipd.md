# IPD: Outcome test that every aw group backend enforces the setid length policy

- Date: 2026-09-26
- Kind: child
- Concern: `aw group` routes per type (`artifact_types.TYPE_BACKENDS`: plans -> `plans_refs.run_set_assign`, research -> `research_refs.run_set_assign`, everything else -> `artifact_rename.run_group_*` -> `run_group_generic`). The setid-length guard was added to all three backends by plan x75obw, but NO test covers it: `tests/test_artifact_group.py` was deleted in commit `19313eed` (test trim). The next verb-wide policy, or a regression that drops the guard from one backend, would go undetected, which is exactly how the original defect (guard on the generic backend only) happened.
- Scope: IN: one new outcome test file `tests/test_group_verb_policy.py`, parametrized over every type in `artifact_types.TYPE_BACKENDS` that has a `group` verb, asserting the refusal (over 24 chars) and the warning (15 to 24 chars). OUT: any production code change (the guards exist and work, measured); a shared pre-dispatch validation seam (the backlog's other suggested direction; a refactor this plan does not need); restoring the deleted `test_artifact_group.py`.
- Scope-Paths: tests/test_group_verb_policy.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 8gwpjy
- Blocks-Release: next
- Set: grouptest
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: qibtxq

## Workflow history
- 2026-09-27 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: qibtxq verified (set grouptest, attempt 1).
- 2026-09-27 approved (aw set): status set to approved

- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 all FIXED; review record `.aw/records/reviews/20260926-grouptest-01-qibtxq-outcome-test-that-every-aw-group-backend-enforces-the-setid.review.md`. Premise and F-1..F-5 re-verified at lane HEAD 2f0b4e9f: the registry yields 9 group types over 3 backends, all three carry the guard, `comms` is correctly excluded, no test drives `aw group`, and all 9 types were re-measured refusing 26 chars and warning at 16. THREE SUBSTANTIVE FIXES: the WARN assertion could not distinguish warn from refuse because BOTH messages contain `strongly preferred` (F-6), so it now keys on the `note:`/`error:` prefix plus refusal short-circuiting; two quiet-boundary cases added because only the firing side of each threshold was tested, which a guard firing on every setid would satisfy (F-7); and E-03's throwaway-worktree mutation was replaced by an in-process `verb=`-scoped patch after measuring that `git worktree add` from a lane registers in the SHARED `.git/worktrees/` (F-8/F-9, per-backend isolation verified). Also de-counted the live 9-type/36-case figures (F-11), corrected the F-3 test-file list (F-10), and made the finalize instruction conditional on runner ownership. `aw ipd lint --phase review-finalize` conforming (one IPD-Z602 advisory on E-03, assessed and kept by decision D-5).
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 8gwpjy: Registry-driven outcome test that every aw group backend enforces the setid length policy.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A regression test that fails if ANY `aw group` backend stops enforcing the setid-length policy, and that covers a newly registered type automatically because it iterates the routing registry rather than a hand-written list.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Confirm current behavior

- [x] E-01 Confirm the guard fires on every backend at HEAD: in a temp `git init` dir, for each type `t` in `[t for t, v in artifact_types.TYPE_BACKENDS.items() if "group" in v]`, run `aw group $t zzzzzz --set abcdefghijklmnopqrstuvwxyz` (26 chars) and `aw group $t zzzzzz --set abcdefghijklmnop` (16 chars) and record rc and output. ALSO capture `git worktree list` verbatim now, as the BEFORE baseline E-04 diffs against, and re-derive the guard's coverage gap (F-3) rather than trusting the authored file list.
  - Depends on: none
  - Expected outcome (re-derive the type set from the registry and report it; measured at authoring AND re-measured at review as the same 9: plans, research, specs, prompts, backlog, walkthroughs, roadmaps, releases, other - the COUNT is a live registry population, so the bar is "every type the registry enumerates", never the number 9): the 26-char case exits 2 with `error: aw group <t>: --set 'abc...z' is 26 characters, over the 24-character maximum`; the 16-char case prints `note: aw group <t>: --set 'abcdefghijklmnop' is 16 characters; a setid of <= 14 characters is strongly preferred` and then fails on the unmatched selector (`error: no ... zzzzzz`), exit 2. If any type does not, stop and report: that is a live bug, not a missing test.
  - Execution state: performed

### Task group 2: The test file

- [x] E-02 Create `tests/test_group_verb_policy.py`. Build the type list from the registry: `GROUP_TYPES = sorted(t for t, verbs in artifact_types.TYPE_BACKENDS.items() if "group" in verbs)`, plus a sanity assertion that it is non-empty and contains `plans` and `research` (so an accidental empty parametrization cannot pass vacuously). For each type, in a temp git repo, run the real CLI (`tests.support.run_cli("group", t, "zzzzzz", "--set", <setid>, "--dir", <tmp>)`, or in-process `cli.main` with captured stdout if subprocess cost is excessive; justify the choice in evidence) and assert:
    (a) REFUSAL: a 25-character setid (the smallest refused length, so the boundary is covered) exits `2` and the output contains `is 25 characters` and `24-character maximum` (so the refusal is the length guard, not the unmatched-selector error), and carries the `error:` prefix. ALSO assert the refusal SHORT-CIRCUITS: the output must NOT contain the unmatched-selector error (`no plan has Id`/`no ... zzzzzz`), because the guard runs BEFORE resolution and a refusal that also resolved would mean the guard moved. Measured at review: the 25-char run emits only the `error:` length line, while the 15-char run emits the `note:` line AND `error: no plan has Id 'zzzzzz'`, so this assertion distinguishes the two outcomes structurally rather than by wording;
    (b) WARNING: a 15-character setid (smallest warned length) prints a line containing `is 15 characters` and `strongly preferred`, and does NOT contain `24-character maximum`. USE THAT PHRASE, NOT `maximum for a setid`, AND DO NOT USE `strongly preferred` AS THE DISCRIMINATOR: measured at review, the REFUSAL message also contains `strongly preferred` (it reads "over the 24-character maximum for a setid (<= 14 is strongly preferred); choose a shorter Set id"), so `strongly preferred` is common to both outcomes and cannot tell them apart, and the authored negative `maximum for a setid` is a SUBSTRING of the refusal's `24-character maximum for a setid` - which means it would work, but only by accident of wording that the refusal owns. Assert positively on the `note:` PREFIX (the warning's own marker, verified absent from the refusal, which uses `error:`) and negatively on `24-character maximum`. The command still exits 2 because the selector matches nothing; assert the warning text and the prefix, not the rc, and say so in a comment, since the warning must be emitted before resolution fails.
    (c) THE TWO QUIET BOUNDARIES, added at review because without them (a) and (b) are satisfied by a guard that fires on EVERY setid: a 14-character setid emits NEITHER `note:` nor `error:` from the guard (measured: only `error: no plan has Id 'zzzzzz'`), and a 24-character setid WARNS but is NOT refused (measured: `note: ... is 24 characters`, no `24-character maximum`). These pin both thresholds from the permitted side, so an off-by-one in either direction fails: warn-at-15-not-14 and refuse-at-25-not-24. Four assertions per type, not two.
    Use `pytest.mark.parametrize` (or `subTest`) keyed by type name so a failure names the backend's type. Derive the four setids from `config.SETID_WARN_LENGTH_DEFAULT` and `config.SETID_MAX_LENGTH_DEFAULT` (`warn`, `warn+1`, `max`, `max+1`) rather than hardcoding 14/15/24/25, so a policy change moves the fixtures with the constants instead of silently testing the wrong boundary; assert the two constants' values once in the sanity check so a change is still visible rather than absorbed.
  - Depends on: E-01
  - Expected outcome: 4 assertions x every registry-enumerated type all pass at HEAD (9 types at review, so 36 cases; report what the registry actually yields rather than matching this figure), plus the sanity check (non-empty, contains `plans` and `research`, and the two policy constants are 14 and 24).
  - Execution state: performed
- [x] E-03 PROVE EACH ASSERTION BITES PER BACKEND, IN-PROCESS, WITH NO GIT WORKTREE AND NO FILE EDIT. Disable the guard for ONE backend at a time by patching `config.validate_setid_length_for_authoring` with a wrapper that returns `(None, None)` only when its `verb=` kwarg equals that backend's own verb string (`aw group plans`, `aw group research`, `aw group <generic-type>`) and delegates to the real validator otherwise, then re-run the E-02 assertions and record which parametrized cases fail. THE `verb=` KWARG IS THE PER-BACKEND LEVER, verified at review: all three backends call the ONE validator and are distinguishable only by that argument (`plans_refs.run_set_assign` passes `verb="aw group plans"`, `research_refs.run_set_assign` passes `verb="aw group research"`, and `artifact_rename.run_group_generic` passes `verb=f"aw group {artifact_type}"`), and each module imports `config` LOCALLY inside the function, so there is no module-level `_config` attribute to patch per module. Measured at review with exactly this wrapper: disabling `aw group plans` stops the guard firing for `plans` ALONE, `aw group research` for `research` alone, and `aw group specs` for `specs` alone, across all nine types. THIS REPLACES THE AUTHORED THROWAWAY-WORKTREE PROCEDURE, which review rejected as unsafe: `git worktree add` from a lane writes its metadata into the SHARED `.git/worktrees/` (verified: `git rev-parse --git-common-dir` resolves to the main checkout's `.git`), so it mutates state every concurrent agent and human sees, it used a FIXED path that two runs of this plan would collide on, and a crash between `add` and `remove` strands a registration nobody owns - two such stale `/tmp/opencode` worktrees were already present at review. The in-process patch is scoped to the test process, needs no cleanup, and cannot leak. Keep it inside a `with mock.patch.object(...)` (or `monkeypatch`) so it unwinds even on failure, and do NOT commit any mutation.
  - Depends on: E-02
  - Expected outcome: disabling the `plans` verb fails exactly the four `plans` cases; the `research` verb exactly the four `research` cases; and a generic verb exactly that one generic type's four cases (the generic backend composes its verb per type, so it is proven type-by-type rather than for all seven at once - assert at least `specs` and one other generic type, and state that the composed verb is what makes the remaining generic types identical). No other case fails in any run, which is what proves each assertion is load-bearing for its own backend rather than passing on another's behalf.
  - Execution state: performed

### Task group 3: Full suite

- [x] E-04 Run the bare suite `python3 -m pytest` in the workspace and confirm E-03 left NOTHING behind: `git status --short` shows only `tests/test_group_verb_policy.py` as this plan's change, and `git worktree list` is byte-identical to a capture taken BEFORE E-03. CAPTURE THAT LIST FIRST, at E-01 time, and diff the two: the list legitimately holds a dozen-plus entries belonging to other agents and humans (14 at review), so "the throwaway worktree is absent" is unverifiable by eye and a bare listing proves nothing. With E-03 now in-process there should be no worktree change at all, which makes an identical diff the expected result rather than a cleanup check.
  - Depends on: E-03
  - Expected outcome: suite green; the before/after `git worktree list` diff is EMPTY; `git status --short` names only the new test file.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Setid policy: `config.SETID_WARN_LENGTH_DEFAULT = 14`, `config.SETID_MAX_LENGTH_DEFAULT = 24`; one validator `config.validate_setid_length_for_authoring` returns `(error, warning)` (AGENTS.md; plans README "KEEP A SETID SHORT").
- Tests run the CLI through `tests.support.run_cli`, pinned to the tree by `PYTHONPATH`.
- The shared checkout must not be used for mutation experiments. A `git worktree add` is NOT an escape from that rule: from a lane it registers in the SHARED `.git/worktrees/` (`git rev-parse --git-common-dir` resolves to the main checkout), so it mutates state other agents see and can strand a registration on a crash. An in-process `mock.patch`/`monkeypatch` of the validator is the isolation that actually holds, and it needs no cleanup.
- Commits via `aw commit qibtxq -- tests/test_group_verb_policy.py`; suite run bare.

## Findings

F-1 through F-5 are the author's, each re-verified at lane HEAD `2f0b4e9f` during review and each reproduced (with the one correction noted in F-10). F-6 through F-11 were added by `/plan-review` on 2026-09-26.

| # | Evidence (authored at HEAD 61ef21d8; re-measured at review) | Finding |
| --- | --- | --- |
| F-1 | `artifact_types.TYPE_BACKENDS` (~:74-118): plans `"group": "plans_refs.run_set_assign"`, research `"group": "research_refs.run_set_assign"`, seven others `"group": "artifact_rename.run_group_<type>"` | Routing confirmed; 9 types have a `group` verb. |
| F-2 | `artifact_rename.run_group_generic` "setidlen x75obw E-06 (catalog I-17): the ONE shared setid-length guard" (~:830-845); `plans_refs.run_set_assign` (~:450-470); `research_refs.run_set_assign` (~:310-330) | Guard present on all three backends, as the brief says. |
| F-3 | `git show --stat 19313eed` lists `tests/test_artifact_group.py | 270 --` | Deleted, confirmed at review. `git grep -l validate_setid_length_for_authoring -- 'tests/*.py'` hits `tests/test_config.py` ALONE (the authored claim also named `tests/test_check_engine.py`, which no longer matches; re-derive at execution rather than trusting either list). Independently confirmed the gap two further ways: no test drives `aw group` through the CLI, and the only test asserting the setid-length MESSAGES is `tests/test_prompts_new.py`, which covers `aw prompts new`, not `aw group`. No `aw group` coverage exists. |
| F-4 | re-measured at review across every registry type | Every type refuses 26 chars with rc 2 (`error: aw group <t>: ... is 26 characters, over the 24-character maximum`) and warns at 16 chars (`note: ... is 16 characters; ... strongly preferred`). The warn case also exits 2 (selector `zzzzzz` unmatched), so the test must assert the warning text, not rc 0; the brief's "15-24 chars warns" is correct but does not imply success exit. |
| F-5 | `aw group --help` lists `comms` as a type | `comms` is not in `TYPE_BACKENDS`, so it has no `group` backend; iterating the registry correctly excludes it. |
| F-6 | measured at review: `validate_setid_length_for_authoring(repo,'a'*25,verb='aw group plans')` -> error text "over the 24-character maximum for a setid (<= 14 is strongly preferred); choose a shorter Set id" | E-02(b)'s WARN assertion could not distinguish warn from refuse: BOTH messages contain `strongly preferred`, so it is not a discriminator, and the authored negative `maximum for a setid` only works as an accidental substring of the refusal's own wording. Corrected at review to assert the `note:` prefix positively and `24-character maximum` negatively, and E-02(a) now also asserts the refusal SHORT-CIRCUITS (no unmatched-selector error), which separates the two outcomes structurally. |
| F-7 | measured at review: 14 chars -> no guard output at all; 24 chars -> `note: ... is 24 characters` with no `24-character maximum` | Only the FIRING side of each threshold was tested, so a guard that warned or refused on EVERY setid would have satisfied both authored assertions. Added case (c): 14 chars is silent and 24 chars warns-but-is-not-refused, pinning both thresholds from the permitted side so an off-by-one in either direction fails. Setids are now derived from `config.SETID_WARN_LENGTH_DEFAULT`/`SETID_MAX_LENGTH_DEFAULT` rather than hardcoded. |
| F-8 | `git rev-parse --git-common-dir` from this lane -> the MAIN checkout's `.git`; `ls .git/worktrees/` -> 14 registrations, two of them stale `/tmp/opencode` entries | E-03's throwaway-worktree procedure was NOT the isolation it claimed: `git worktree add` from a lane registers in the SHARED `.git/worktrees/`, so it mutates state every concurrent agent and human sees, it used a FIXED path two runs would collide on, and a crash between `add` and `remove` strands a registration. Replaced at review with an in-process patch scoped to the test process. |
| F-9 | measured at review: patching the validator to return `(None,None)` only when `verb=='aw group plans'` stops the guard firing for `plans` ALONE across all nine types; likewise `aw group research` and `aw group specs` | The `verb=` kwarg IS a sufficient per-backend lever, which is what makes F-8's replacement possible. All three backends call the ONE validator and import `config` LOCALLY inside the function, so there is no module-level `_config` to patch per module; `verb=` is the only distinguishing argument. |
| F-10 | `git grep -l validate_setid_length_for_authoring -- 'tests/*.py'` -> `tests/test_config.py` only | F-3 also named `tests/test_check_engine.py`, which no longer matches. The coverage-gap CONCLUSION is unaffected and was independently re-confirmed two further ways (no test drives `aw group` via the CLI; the only test asserting the setid-length messages is `tests/test_prompts_new.py`, for `aw prompts new`). E-01 now re-derives this rather than trusting either list. |
| F-11 | the type count (9) appeared as a fixed figure in six places | The plan's whole premise is registry-driven coverage, so the type count is a LIVE population and must not be an acceptance bar. Restated as "every type the registry enumerates", with 9/36 kept as review-measured context. |

## Proposed changes (ordered, validatable)

1. E-01 confirm behavior.
2. E-02 the registry-driven test.
3. E-03 per-backend mutation proof in-process, via the validator's `verb=` kwarg.
4. E-04 suite.

## Deferred / out of scope (with reason)

- A single pre-dispatch validation seam for `aw group`: a refactor the backlog offered as an alternative; the test is the cheaper option the backlog itself recommends and closes the detection gap.
  - Carrier-Declined: not needed; the parametrized test covers every current and future backend through the registry, so no refactor is outstanding.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

The maintainer's standing rule is to test OUTCOMES only: the test drives the real `aw group` command and asserts its exit status and emitted message, never the guard's source or its presence in a file. One test file, two assertions per type, parametrized from the registry so a new type is covered with no edit. E-03 proves each assertion is load-bearing per backend.

## Spec / documentation sync

N/A: test-only; no spec or doc changes.

## Open questions

None. Review raised no new question: every finding was resolvable from repository evidence and was fixed in place, and the one judgement call (keeping E-03 as a single item despite its `IPD-Z602` density advisory, because its length is justification prose rather than bundled work) is recorded as a decision in the review record rather than left as an open question.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste, for every type the registry enumerates, rc and the first output line of the 26-char and 16-char runs (expected: rc 2 plus the `error:` length line; the `note:` warning line plus rc 2). Also paste the BEFORE `git worktree list` capture and the re-derived F-3 evidence (which tests, if any, reference the validator or drive `aw group`).
  - Observed evidence: PASS. Guard verified on every backend at HEAD; baseline worktrees captured; F-3 coverage gap re-derived.
    Enumerated 9 group types from `artifact_types.TYPE_BACKENDS`: `['backlog', 'other', 'plans', 'prompts', 'releases', 'research', 'roadmaps', 'specs', 'walkthroughs']`.

    26-char and 16-char run output for all 9 types:
    ```
    [backlog] 26-char rc=2
      stdout: error: aw group backlog: --set 'abcdefghijklmnopqrstuvwxyz' is 26 characters, over the 24-character maximum for a setid (<= 14 is strongly preferred); choose a shorter Set id
    [backlog] 16-char rc=2
      stdout: note: aw group backlog: --set 'abcdefghijklmnop' is 16 characters; a setid of <= 14 characters is strongly preferred (over 24 is refused)
    [other] 26-char rc=2
      stdout: error: aw group other: --set 'abcdefghijklmnopqrstuvwxyz' is 26 characters, over the 24-character maximum for a setid (<= 14 is strongly preferred); choose a shorter Set id
    [other] 16-char rc=2
      stdout: note: aw group other: --set 'abcdefghijklmnop' is 16 characters; a setid of <= 14 characters is strongly preferred (over 24 is refused)
    [plans] 26-char rc=2
      stdout: error: aw group plans: --set 'abcdefghijklmnopqrstuvwxyz' is 26 characters, over the 24-character maximum for a setid (<= 14 is strongly preferred); choose a shorter Set id
    [plans] 16-char rc=2
      stdout: note: aw group plans: --set 'abcdefghijklmnop' is 16 characters; a setid of <= 14 characters is strongly preferred (over 24 is refused)
    [prompts] 26-char rc=2
      stdout: error: aw group prompts: --set 'abcdefghijklmnopqrstuvwxyz' is 26 characters, over the 24-character maximum for a setid (<= 14 is strongly preferred); choose a shorter Set id
    [prompts] 16-char rc=2
      stdout: note: aw group prompts: --set 'abcdefghijklmnop' is 16 characters; a setid of <= 14 characters is strongly preferred (over 24 is refused)
    [releases] 26-char rc=2
      stdout: error: aw group releases: --set 'abcdefghijklmnopqrstuvwxyz' is 26 characters, over the 24-character maximum for a setid (<= 14 is strongly preferred); choose a shorter Set id
    [releases] 16-char rc=2
      stdout: note: aw group releases: --set 'abcdefghijklmnop' is 16 characters; a setid of <= 14 characters is strongly preferred (over 24 is refused)
    [research] 26-char rc=2
      stdout: error: aw group research: --set 'abcdefghijklmnopqrstuvwxyz' is 26 characters, over the 24-character maximum for a setid (<= 14 is strongly preferred); choose a shorter Set id
    [research] 16-char rc=2
      stdout: note: aw group research: --set 'abcdefghijklmnop' is 16 characters; a setid of <= 14 characters is strongly preferred (over 24 is refused)
    [roadmaps] 26-char rc=2
      stdout: error: aw group roadmaps: --set 'abcdefghijklmnopqrstuvwxyz' is 26 characters, over the 24-character maximum for a setid (<= 14 is strongly preferred); choose a shorter Set id
    [roadmaps] 16-char rc=2
      stdout: note: aw group roadmaps: --set 'abcdefghijklmnop' is 16 characters; a setid of <= 14 characters is strongly preferred (over 24 is refused)
    [specs] 26-char rc=2
      stdout: error: aw group specs: --set 'abcdefghijklmnopqrstuvwxyz' is 26 characters, over the 24-character maximum for a setid (<= 14 is strongly preferred); choose a shorter Set id
    [specs] 16-char rc=2
      stdout: note: aw group specs: --set 'abcdefghijklmnop' is 16 characters; a setid of <= 14 characters is strongly preferred (over 24 is refused)
    [walkthroughs] 26-char rc=2
      stdout: error: aw group walkthroughs: --set 'abcdefghijklmnopqrstuvwxyz' is 26 characters, over the 24-character maximum for a setid (<= 14 is strongly preferred); choose a shorter Set id
    [walkthroughs] 16-char rc=2
      stdout: note: aw group walkthroughs: --set 'abcdefghijklmnop' is 16 characters; a setid of <= 14 characters is strongly preferred (over 24 is refused)
    ```

    BEFORE `git worktree list` baseline:
    ```
    <repo-root>                                                          058713bc [main]
    <repo-root>/.aw/state/suite-baselines/qibtxq-attempt1                2cb0361a (detached HEAD)
    <repo-root>/.aw/state/suite-baselines/sbo3hl-attempt1                efd3cb42 (detached HEAD)
    <repo-root>/.aw/state/suite-baselines/y2vzit-attempt1                058713bc (detached HEAD)
    <repo-root>/.aw/worktrees/4eecvh                                     5573913b [aw/lane/4eecvh]
    <repo-root>/.aw/worktrees/7icz68                                     f2888ec7 [aw/lane/7icz68]
    <repo-root>/.aw/worktrees/btth0a                                     0ee2bcb3 [aw/lane/btth0a]
    <repo-root>/.aw/worktrees/feat-partition                             4e3a1f6d [feat/aw-partition]
    <repo-root>/.aw/worktrees/k4vi7z                                     8b93ab0c [aw/lane/k4vi7z]
    <repo-root>/.aw/worktrees/qibtxq                                     2cb0361a [aw/lane/qibtxq]
    <repo-root>/.aw/worktrees/review-sweep-run-20260926T143504Z-2574275  7a6ed035 [aw/lane/review-sweep-run-20260926T143504Z-2574275]
    <repo-root>/.aw/worktrees/review-sweep-run-20260926T143527Z-2574842  0cc68b8a [aw/lane/review-sweep-run-20260926T143527Z-2574842]
    <repo-root>/.aw/worktrees/sbo3hl                                     efd3cb42 [aw/lane/sbo3hl]
    <repo-root>/.aw/worktrees/y2vzit                                     058713bc [aw/lane/y2vzit]
    /tmp/opencode/iwt-gate                                               51bf997c [fix/gate-causes]
    ```

    Re-derived F-3 coverage gap evidence:
    - `git grep -l validate_setid_length_for_authoring -- 'tests/*.py'` -> `tests/test_config.py` only
    - `git grep -E 'run_cli\(.*"group"' tests/` -> empty (exit code 1; no CLI driver for `aw group` in tests)
    - `git grep -l "24-character maximum" tests/` -> `tests/test_prompts_new.py` only (`aw prompts new`, not `aw group`)
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_group_verb_policy.py` output listing every parametrized case by type name (4 assertions x however many types the registry enumerates, 36 at review, plus the sanity check) as PASSED. Do not reconcile the count to a number written here if the registry has grown; paste what the run reports and say how many types it enumerated.
  - Observed evidence: PASS. 37 tests passed (4 assertions x 9 registry types + 1 sanity check).
    Enumerated 9 types from the live registry. Run output (37 passed: 4 assertions x 9 types = 36 parametrized cases + 1 sanity check):
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=446630427
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 37 items

    tests/test_group_verb_policy.py::test_group_setid_refusal[backlog] PASSED [  2%]
    tests/test_group_verb_policy.py::test_group_setid_quiet_at_warn_limit[research] PASSED [  5%]
    tests/test_group_verb_policy.py::test_group_setid_warn_not_refused_at_max[other] PASSED [  8%]
    tests/test_group_verb_policy.py::test_group_setid_quiet_at_warn_limit[plans] PASSED [ 10%]
    tests/test_group_verb_policy.py::test_group_setid_warning[other] PASSED  [ 13%]
    tests/test_group_verb_policy.py::test_group_setid_refusal[specs] PASSED  [ 16%]
    tests/test_group_verb_policy.py::test_group_setid_quiet_at_warn_limit[backlog] PASSED [ 18%]
    tests/test_group_verb_policy.py::test_group_setid_warning[specs] PASSED  [ 21%]
    tests/test_group_verb_policy.py::test_group_setid_warn_not_refused_at_max[research] PASSED [ 24%]
    tests/test_group_verb_policy.py::test_group_setid_warning[backlog] PASSED [ 27%]
    tests/test_group_verb_policy.py::test_group_setid_refusal[other] PASSED  [ 29%]
    tests/test_group_verb_policy.py::test_group_setid_refusal[research] PASSED [ 32%]
    tests/test_group_verb_policy.py::test_group_setid_warn_not_refused_at_max[backlog] PASSED [ 35%]
    tests/test_group_verb_policy.py::test_group_setid_refusal[walkthroughs] PASSED [ 37%]
    tests/test_group_verb_policy.py::test_group_setid_warn_not_refused_at_max[specs] PASSED [ 40%]
    tests/test_group_verb_policy.py::test_group_setid_warning[research] PASSED [ 43%]
    tests/test_group_verb_policy.py::test_group_setid_quiet_at_warn_limit[prompts] PASSED [ 45%]
    tests/test_group_verb_policy.py::test_group_setid_quiet_at_warn_limit[specs] PASSED [ 48%]
    tests/test_group_verb_policy.py::test_group_setid_quiet_at_warn_limit[releases] PASSED [ 51%]
    tests/test_group_verb_policy.py::test_group_setid_refusal[plans] PASSED  [ 54%]
    tests/test_group_verb_policy.py::test_group_setid_quiet_at_warn_limit[roadmaps] PASSED [ 56%]
    tests/test_group_verb_policy.py::test_group_setid_refusal[prompts] PASSED [ 59%]
    tests/test_group_verb_policy.py::test_group_setid_quiet_at_warn_limit[walkthroughs] PASSED [ 62%]
    tests/test_group_verb_policy.py::test_group_setid_warn_not_refused_at_max[prompts] PASSED [ 64%]
    tests/test_group_verb_policy.py::test_group_setid_warn_not_refused_at_max[releases] PASSED [ 67%]
    tests/test_group_verb_policy.py::test_group_setid_warn_not_refused_at_max[roadmaps] PASSED [ 70%]
    tests/test_group_verb_policy.py::test_group_setid_warn_not_refused_at_max[plans] PASSED [ 72%]
    tests/test_group_verb_policy.py::test_group_setid_warn_not_refused_at_max[walkthroughs] PASSED [ 75%]
    tests/test_group_verb_policy.py::test_group_setid_warning[prompts] PASSED [ 78%]
    tests/test_group_verb_policy.py::test_group_setid_warning[roadmaps] PASSED [ 81%]
    tests/test_group_verb_policy.py::test_group_setid_warning[plans] PASSED  [ 83%]
    tests/test_group_verb_policy.py::test_group_setid_refusal[releases] PASSED [ 86%]
    tests/test_group_verb_policy.py::test_group_setid_quiet_at_warn_limit[other] PASSED [ 89%]
    tests/test_group_verb_policy.py::test_group_setid_warning[walkthroughs] PASSED [ 91%]
    tests/test_group_verb_policy.py::test_group_verb_policy_sanity PASSED    [ 94%]
    tests/test_group_verb_policy.py::test_group_setid_refusal[roadmaps] PASSED [ 97%]
    tests/test_group_verb_policy.py::test_group_setid_warning[releases] PASSED [100%]

    ============================== 37 passed in 3.17s ==============================
    ```
    Choice justification: in-process `cli.main` with captured stdout/stderr executes in ~3s across all 37 tests (compared to ~15-20s for subprocesses) and enables direct in-process mocking of `config.validate_setid_length_for_authoring` for E-03 without subprocess environment orchestration.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: for each backend probed, paste the patch wrapper's source (the `verb=` predicate) and the pytest output showing exactly which cases FAILED and that no others did (`plans` alone; `research` alone; each probed generic type alone). Then paste `git status --short` proving no tracked file under `agent_workflows/` was modified, and the before/after `git worktree list` diff proving E-03 created no worktree.
  - Observed evidence: PASS. Proved each backend assertion bites in-process with no worktrees created.
    Probe 1: `aw group plans`
    ```python
    def wrapper(repo_root, setid, *, verb=""):
        if verb == "aw group plans":
            return (None, None)
        return real_val(repo_root, setid, verb=verb)
    ```
    Pytest result:
    ```
    FAILED tests/test_group_verb_policy.py::test_group_setid_warning[plans]
    FAILED tests/test_group_verb_policy.py::test_group_setid_warn_not_refused_at_max[plans]
    FAILED tests/test_group_verb_policy.py::test_group_setid_refusal[plans]
    3 failed, 34 passed in 2.16s
    ```

    Probe 2: `aw group research`
    ```python
    def wrapper(repo_root, setid, *, verb=""):
        if verb == "aw group research":
            return (None, None)
        return real_val(repo_root, setid, verb=verb)
    ```
    Pytest result:
    ```
    FAILED tests/test_group_verb_policy.py::test_group_setid_warn_not_refused_at_max[research]
    FAILED tests/test_group_verb_policy.py::test_group_setid_refusal[research]
    FAILED tests/test_group_verb_policy.py::test_group_setid_warning[research]
    3 failed, 34 passed in 2.04s
    ```

    Probe 3: generic backend type `specs` (`aw group specs`)
    ```python
    def wrapper(repo_root, setid, *, verb=""):
        if verb == "aw group specs":
            return (None, None)
        return real_val(repo_root, setid, verb=verb)
    ```
    Pytest result:
    ```
    FAILED tests/test_group_verb_policy.py::test_group_setid_warning[specs]
    FAILED tests/test_group_verb_policy.py::test_group_setid_refusal[specs]
    FAILED tests/test_group_verb_policy.py::test_group_setid_warn_not_refused_at_max[specs]
    3 failed, 34 passed in 2.14s
    ```

    Probe 4: generic backend type `backlog` (`aw group backlog`)
    ```python
    def wrapper(repo_root, setid, *, verb=""):
        if verb == "aw group backlog":
            return (None, None)
        return real_val(repo_root, setid, verb=verb)
    ```
    Pytest result:
    ```
    FAILED tests/test_group_verb_policy.py::test_group_setid_warn_not_refused_at_max[backlog]
    FAILED tests/test_group_verb_policy.py::test_group_setid_warning[backlog]
    FAILED tests/test_group_verb_policy.py::test_group_setid_refusal[backlog]
    3 failed, 34 passed in 1.96s
    ```

    In each probed backend, exactly that backend's firing assertions failed and no other backend failed (34 passed). The remaining 5 generic types share identical dispatch code in `artifact_rename.run_group_generic` via composed `verb=f"aw group {artifact_type}"`. Furthermore, an over-eager guard simulation on `plans` returning a warning on `SETID_WARN_LENGTH_DEFAULT` (14 chars) confirmed `test_group_setid_quiet_at_warn_limit[plans]` fails (1 failed, 3 passed for plans).

    Tracked files check (`git status --short`):
    ```
    ?? tests/test_group_verb_policy.py
    ```
    No tracked file under `agent_workflows/` was modified.

    Worktree diff check: `diff(baseline_worktrees, current_worktrees)` is EMPTY (byte-identical); E-03 created no worktrees.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste the final summary line of bare `python3 -m pytest` (`N passed`, no failures), `git status --short` showing only `tests/test_group_verb_policy.py` as this plan's change, and the EMPTY diff between the `git worktree list` captured at E-01 and the one captured now.
  - Observed evidence: PASS. Full pytest suite green (2745 passed), clean git status, empty worktree diff.
    Final summary line of bare `python3 -m pytest`:
    ```
    2745 passed, 2 skipped, 3 warnings in 83.25s (0:01:23)
    ```

    `git status --short`:
    ```
    ?? tests/test_group_verb_policy.py
    ```

    Diff between `git worktree list` captured at E-01 and after full suite:
    ```
    DIFF IS EMPTY (byte-identical)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: one new test file; no production code. The bug being closed is the missing detection (8gwpjy), not a live guard failure: every backend was measured enforcing at authoring and RE-MEASURED enforcing at review, on all three code paths and all nine types.

WHAT REVIEW CHANGED. The plan's premise and all five of its findings hold, and the deliverable is still one test file with no production change. Three things moved. The WARN assertion could not actually distinguish a warning from a refusal, because both messages contain `strongly preferred` (F-6), so it now keys on the `note:`/`error:` prefix and on the refusal short-circuiting before selector resolution. Two boundary cases were added, since testing only the firing side of each threshold would be satisfied by a guard that fired on every setid (F-7): 14 characters must be silent and 24 must warn without refusing. And E-03's throwaway-worktree procedure was replaced by an in-process patch (F-8/F-9): `git worktree add` from a lane registers in the SHARED `.git/worktrees/`, so it was mutating state other agents see, and the validator's `verb=` argument gives the same per-backend isolation with nothing to clean up.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `tests/test_group_verb_policy.py` only. The E-03 mutations are IN-PROCESS patches that exist only inside the probing test process: no file is edited, nothing is committed, and no git worktree is created (review replaced the authored worktree procedure for exactly that reason). The shared checkout's `plans_refs.py`, `research_refs.py`, `artifact_rename.py` must not be edited. Do not expand scope casually; a genuinely required out-of-fence edit is made and JUSTIFIED at finalize with `--scope-reason`. Genuine stop condition: E-01 shows a backend NOT enforcing the policy (live bug; report before writing a test that would fail).

HONESTY RULE (hard MUST): paste the ACTUAL runner output; V-03 failures must be real runs.

Commit ONLY `tests/test_group_verb_policy.py` through `aw commit qibtxq -- tests/test_group_verb_policy.py`; never `git add -A`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition is `aw ipd finalize`: THE RUNNER OWNS IT when this plan executes in a lane, and only a hand execution outside a runner invokes it directly as `aw ipd finalize qibtxq --actor <agent/model> --message <summary> --apply`. Do not run it unconditionally, and never hand-roll a `git mv` to `executed/`. This plan inherits `- Blocks-Release: next` from backlog `8gwpjy`. CLOSING THAT ITEM IS ALREADY LEGITIMATE BY HANDOFF once this plan is `executed`, because it carries `- From-Backlog: 8gwpjy` and the SAME `- Blocks-Release: next`, which is the HANDOFF arm of `check_engine.evaluate_blocking_close`; passing `--evidence` citing the executed plan additionally satisfies the SATISFIED arm, so either suffices and the two together cannot strand the gate.
