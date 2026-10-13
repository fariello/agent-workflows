# IPD: Keep the staged git mv rename when aw set does not commit

- Date: 2026-10-12
- Kind: child
- Concern: `aw set` (every spelling: `aw backlog set`, `aw specs set`, `aw ipd set`, positional and `--status`) relocates a record with `git mv`, then its self-commit offer unconditionally runs `git reset --quiet HEAD -- <touched paths>` before deciding whether to commit. When it does NOT commit (`--no-commit`, or the non-interactive default without `--commit`), that reset unstages the rename and leaves ` D <src>` plus `?? <dest>`, the two-halves shape behind the measured 36-duplicate-id incident.
- Scope: Remove the redundant pre-reset from `status_set._offer_self_commit`, prove a relocation stays one staged rename on both spellings and all three relocating record types (backlog, specs, plans) under `--no-commit` and the non-interactive default, prove the committing path and the runner's `runner_shared.commit_backlog_close` consumer still record a single rename, flip the one pinned test that recorded the defect shape, and add a CHANGELOG line.
- Scope-Paths: agent_workflows/status_set.py, tests/test_set_dispatch_parity.py, CHANGELOG.md, .aw/records/plans/pending/20261012-r73v9i-01-a63epo-keep-the-staged-git-mv-rename-when-aw-set-does-not-commit.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: r73v9i
- Blocks-Release: next
- Set: r73v9i
- Order: 1
- Highest E allocated: 06
- Author: opencode
- Id: a63epo
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005
- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog r73v9i; root cause and fix measured in scratch repos (F-01..F-04).

## Goal

A status transition that relocates a record and does not commit leaves the relocation STAGED as a single `R` rename, so spec `wy9aru` AC-5 ("A relocation performed by either spelling appears in `git status --porcelain` as a single `R` rename") holds for both spellings, and nobody who later commits by hand can commit the addition without the deletion.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline

- [x] E-01 Record the BEFORE shape and the bare-suite baseline.
  In a scratch repo (`tests.test_set_dispatch_dedup._setup_test_repo` plus a commit of the fixture is sufficient, as F-01 did; put any probe script under the gitignored `.aw/state/`, never a tracked path), run `aw backlog set <item> --status done --message x` three ways: `--no-commit`, no flag (non-interactive), and `--commit`. Paste `git status --porcelain` after each and `git show --stat --find-renames --format=%s HEAD` after `--commit`. Then run the bare suite `python3 -m pytest` and save the failing-test SET by name.
  - Depends on: none
  - Expected outcome: ` D .../open/<item>` plus `?? .../done/` for the two non-committing modes, `{open => done}` for `--commit`, and a named baseline failure set.
  - Execution state: performed

### Task group 2: Fix (perform AFTER E-03, E-04 and E-06, which are written test-first)

- [x] E-02 Delete the pre-reset in `status_set._offer_self_commit`.
  Remove the `_gch._git(repo_root, ["reset", "--quiet", "HEAD", "--", *paths])` call and its "jgcm68 D2" comment, replacing the comment with a short note: the touched paths are passed to `git_commit_helper.offer_commit` already staged by `artifact_core.git_mv`; `offer_commit` drops a staged rename's source from its `git add` set via `_in_index` and stages the rest itself, so no pre-reset is needed, and a pre-reset would unstage the rename whenever the commit is skipped (backlog `r73v9i`). Change nothing else in the function (message, `assume_yes`, `no_commit`, `on_unrelated_staged="scope"` stay byte-identical).
  - Depends on: E-01, E-03, E-04, E-06
  - Expected outcome: a diff in `agent_workflows/status_set.py` confined to `_offer_self_commit` that removes exactly the reset call and rewrites its comment.
  - Execution state: performed

### Task group 3: Tests (written BEFORE E-02, so each failing-before claim is observed)

- [x] E-03 Flip `tests/test_set_dispatch_parity.py::test_backlog_relocation_porcelain_shape_agreement` to the canonical shape.
  It currently asserts ` D .aw/records/backlog/open/` and `?? .aw/records/backlog/done/` and its docstring records the defect. Make it assert, for BOTH spellings under `--no-commit`, that exactly one porcelain line starts with `R` and names `backlog/open/... -> backlog/done/...`, that no line starts with ` D ` for the source, and that no `?? .aw/records/backlog/done/` line exists. Rewrite the docstring to state the property and cite `wy9aru` AC-5 and backlog `r73v9i`.
  - Depends on: E-01
  - Expected outcome: run before E-02 the test FAILS (pasted); run after E-02 it passes. Never use `git stash`.
  - Execution state: performed

- [x] E-04 Add outcome tests for the remaining relocation surfaces in `tests/test_set_dispatch_parity.py`.
  (a) Backlog, both spellings, NO commit flag and NO `--yes`, with the environment forced non-interactive (set `AW_NONINTERACTIVE=1` via `mock.patch.dict(os.environ, ...)`, so `git_commit_helper._is_interactive` resolves False and `offer_commit` takes its "skipped: non-interactive" branch; `--yes` must be absent because `_offer_self_commit` maps a bare `--yes` to `assume_yes=True`): porcelain shows one `R` line for the item. (b) Spec relocation (`aw specs set <path> --status to-review --no-commit` and the positional `aw specs set to-review <id6> --no-commit`, fixture `_create_spec(repo, status="draft")`): porcelain shows one `R` line `specs/draft/... -> specs/to-review/...`. (c) Plan relocation (`aw ipd set superseded <plan> --message m --no-commit`, fixture `_write_conforming_plan`): porcelain shows one `R` line `plans/pending/... -> plans/superseded/...`. (d) Backlog `--commit` on both spellings: the new commit's `git show --name-status -M` has a single `R` line for the item, and `git status --porcelain` shows no tracked entry for either half (the gitignore-less fixture's untracked `.aw/records/history.jsonl` sidecar is expected and must be excluded from that assertion, not asserted absent). (e) An unrelated pre-staged file survives staged and uncommitted after a `--commit` relocation (guards that removing the reset did not widen the commit). Drive the CLI and assert on git output only (P16; no source reads).
  - Depends on: E-01
  - Expected outcome: run before E-02, (a), (b) and (c) FAIL and (d) and (e) pass (pasted); after E-02 all five pass.
  - Execution state: performed

- [x] E-06 Add one outcome test that the runner's non-isolated backlog close still commits a single rename after the fix.
  In `tests/test_set_dispatch_parity.py`, relocate a committed backlog item with `aw backlog set <path> --status done --message m --no-commit` (the exact argv shape `runner_shared.close_backlog_item` builds), then call `runner_shared.commit_backlog_close(repo, "<id6>", "close", run_checked=<subprocess wrapper returning stripped stdout and raising on nonzero>)`. Assert it returns a sha, the commit's `git show --name-status -M --format= HEAD` is exactly one `R` line `backlog/open/... -> backlog/done/...`, and no tracked entry for either half remains in porcelain. This guards the one in-repo consumer of the `--no-commit` porcelain shape the fix changes (it parses `old -> new` rename lines and fails closed on fewer than two paths).
  - Depends on: E-01
  - Expected outcome: passes both before and after E-02 (pasted both); a regression after E-02 would show as a None return or a non-`R` commit.
  - Execution state: performed

### Task group 4: Record

- [x] E-05 Add one `CHANGELOG.md` entry and run the full validation.
  Under the pending 2.0.0 section, add a `- Fixed:` line in user terms: when `aw backlog set`, `aw specs set` or `aw ipd set` moves a record to a new status directory without committing, the move now stays staged as a single file rename instead of a deleted file plus an untracked file. No em or en dashes (user-facing prose). Then run the bare suite and compare its failure set by name with E-01's.
  - Depends on: E-02, E-03, E-04, E-06
  - Expected outcome: one CHANGELOG line; bare-suite failure set equal to the baseline except for tests this plan edits or adds, all of which pass.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16): drive `cli.main` / `run_cli` in a temp git repo and assert on `git status --porcelain`, `git show`, exit codes. Never read source.
- Run the suite bare (`python3 -m pytest`), never `-n0`, extra `-q`, or `-p no:randomly` (`AGENTS.md`, repository development contract).
- Commit through `aw commit a63epo -- <Scope-Paths>`; never push.
- No em or en dashes in `CHANGELOG.md` (user-facing).
- Spec `wy9aru` 4.2 rules the single staged `git mv` rename canonical and records why (the 36-duplicate-id incident pinned by `tests/test_git_commit_helper.py::test_staged_rename_moves_and_duplicate_prevention`).

## Findings

| ID | Evidence | Consequence |
|---|---|---|
| F-01 | MEASURED 2026-10-12 in a scratch repo built by `tests.test_set_dispatch_dedup._setup_test_repo`: `aw backlog set <path> --status done --message x --no-commit` and the same with no commit flag both leave ` D .aw/records/backlog/open/20260930-bklung-...` plus `?? .aw/records/backlog/done/`; with `--commit` the commit is `.../{open => done}/20260930-bklung-... | 3 ++-`. | The bug reproduces in BOTH non-committing modes, not only `--no-commit`: the non-interactive default (no flag) is the more common path and is equally affected. The committing path is already correct. |
| F-02 | `status_set._offer_self_commit` calls `_gch._git(repo_root, ["reset", "--quiet", "HEAD", "--", *paths])` unconditionally, BEFORE `offer_commit`, under the comment "jgcm68 D2: unstage exactly these touched paths first (a no-op for in-place set rewrites)". `status_set.apply_status_change` relocates with `_core.git_mv(...)`, which stages the rename. | The reset undoes the staged rename; `offer_commit` then returns `skipped` (`no_commit`, or the non-interactive branch) BEFORE staging anything, so nothing re-stages it. Root cause of `r73v9i`. |
| F-03 | `git_commit_helper.offer_commit` builds `add_paths` filtered by `(repo_root / p).exists() or _in_index(repo_root, p)`; its comment records this was added 2026-09-13 precisely because `git add` on an already-staged rename's source fails "pathspec did not match any files". `_staged_paths` is rename-aware (both sides, fix of 2026-09-22). | The failure the jgcm68 D2 reset worked around is now handled inside `offer_commit`, so the reset is redundant on the commit path and harmful on the skip path. |
| F-04 | MEASURED 2026-10-12: same scratch repo, with only that reset call suppressed at runtime (monkeypatched `_gch._git` for calls from `_offer_self_commit`; no repo edit): `--no-commit` and no-flag both give `RM .aw/records/backlog/open/... -> .aw/records/backlog/done/...`; `--commit` still gives `.../{open => done}/... | 3 ++-` and a clean porcelain apart from the untracked `history.jsonl` sidecar. | Deleting the call is sufficient and does not regress the committing path. (`RM`: the rename is staged and the post-move `atomic_write` content edit is unstaged, which still begins with `R` as AC-5 requires.) |
| F-05 | `tests/test_set_dispatch_parity.py::test_backlog_relocation_porcelain_shape_agreement` asserts ` D .aw/records/backlog/open/` and `?? .aw/records/backlog/done/` and its docstring says neither spelling meets AC-5 today; plan `vhiqo6` (executed) E-06 filed `r73v9i` for exactly this. | That test pins the defect and must be flipped (E-03); it is the only test found asserting the defect shape for `aw set` (grep of `tests/` for ` D .aw` / `?? .aw/records` porcelain asserts: the others are `test_research_set_assign_date_containment.py`, a different verb pinning `shutil.move`, and `test_orchestrator_retirement.py`, INDEX files). |
| F-07 | MEASURED at review 2026-10-12 (scratch repos from `tests/test_set_dispatch_parity.py` `_setup_repo`/`_create_spec`/`_write_conforming_plan`, same runtime suppression as F-04): pre-fix, `aw specs set <path> --status to-review --no-commit`, `aw specs set to-review sp0001 --no-commit`, `aw ipd set superseded <plan> --no-commit` and `aw set not-executed <plan> --no-commit` all leave ` D <src>` plus `?? <dest dir>/`; with the reset suppressed each gives one `RM <src> -> <dest>` line. | Plans relocate through the same `status_set.apply_status_change` / `_offer_self_commit` path and are equally affected and equally fixed, so the CHANGELOG's `aw ipd set` claim needs its own test (E-04 (c)). |
| F-08 | `runner_shared.commit_backlog_close` (non-isolated runner path) runs `git status --porcelain -uall` after `close_backlog_item` (which passes `--no-commit`), splits `old -> new` rename lines into both paths, and returns None on fewer than two. MEASURED at review: pre-fix and with the reset suppressed it commits `R075 backlog/open/... backlog/done/...` and leaves only the untracked `history.jsonl`. The other `runner_shared` porcelain parsers (e.g. `commit_review_lane_output`) also split ` -> `. | The fix changes the porcelain shape this consumer sees from ` D`+`??` to `RM`, and the consumer handles it; E-06 pins that so a later refactor of either side cannot regress it silently. |
| F-06 | The same jgcm68 D2 pre-reset exists in `cli._offer_records_commit`, `plans_archive` and `research_archive`. | Different verbs (records rename/regroup, archive), not `aw set`; not measured here. Out of scope (see Deferred). |

## Proposed changes (ordered, validatable)

1. Baseline measurement and bare-suite failure set (E-01).
2. `tests/test_set_dispatch_parity.py`: flip the pinned defect test (E-03), add five outcome tests (E-04) observed failing first where applicable, and add the runner-consumer test (E-06).
3. `agent_workflows/status_set.py`: delete the pre-reset in `_offer_self_commit`, rewrite its comment (E-02).
4. `CHANGELOG.md`: one `Fixed:` line; bare suite compared to baseline (E-05).

## Deferred / out of scope (with reason)

- THE SAME PRE-RESET IN `cli._offer_records_commit`, `plans_archive` AND `research_archive` IS NOT CHANGED. Those back other verbs (`aw rename`/`aw group`/`aw archive`), the backlog item names `aw set` only, and their skip-path shape has not been measured. Changing them without a measurement would be opportunistic scope broadening.
  - Carrier-Declined: not measured as defective; a separate backlog item should be filed only if a measurement shows the same ` D` plus `??` shape for those verbs
- A HOOK-REJECTED SELF-COMMIT is not changed: `offer_commit`'s non-success path resets `our_staged`, which can also unstage a rename after a rejected commit. That is `offer_commit`'s failure-path contract, shared by every caller, and is not the `--no-commit`/non-interactive skip this item reports.
  - Carrier-Declined: different code path and contract, not the reported defect
- Spec `wy9aru` is not edited: AC-5 already states the property this plan makes true.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none. Every declared path is edited by a numbered item: `agent_workflows/status_set.py` (E-02), `tests/test_set_dispatch_parity.py` (E-03, E-04, E-06), `CHANGELOG.md` (E-05), this plan (evidence).
- Under-scope: none. Both non-committing modes (F-01), both spellings, all three relocating record types that route through `_offer_self_commit` (backlog, specs, plans; F-07), the committing path, and the runner's `commit_backlog_close` consumer (F-08) are covered by E-03/E-04/E-06.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_set_dispatch_parity.py tests/test_set_dispatch_dedup.py tests/test_git_commit_helper.py tests/test_backlog.py tests/test_backlog_set_adapter.py tests/test_backlog_close_host_label.py` passes after E-02..E-04 and E-06.
- E-03's flipped test and E-04 (a)/(b)/(c) are shown to FAIL against the pre-E-02 code and pass after; E-04 (d)/(e) and E-06 pass both before and after.
- Bare `python3 -m pytest`: failure set equal to E-01's baseline by name, except tests this plan edits or adds.
- `aw ipd lint` on this plan conforms; `aw check release-gates` exits 0.

## Spec / documentation sync

- Spec `wy9aru` AC-5: N/A, no edit. The spec already rules the single staged rename canonical (4.2); this plan makes the implementation meet it.
- `CHANGELOG.md`: one `Fixed:` line (E-05).

## Open questions

### OQ-01: Is the jgcm68 D2 pre-reset still needed for an in-place rewrite or a pre-staged path?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Its own comment calls it "a no-op for in-place set rewrites". For a path the user had partially staged, `offer_commit` runs `git add -- <path>` before committing, so the committed content is the working tree either way; on the skip path NOT resetting leaves the user's staging untouched, which is strictly safer. E-04 (d) guards the unrelated-staged case. Evidence: F-03, F-04.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `git status --porcelain` for `--no-commit` and no-flag runs showing ` D` plus `??`, pasted `git show --stat --find-renames` for `--commit`, and the saved baseline failure set (names, or "none"). Produced by `status_set.apply_status_change` then `status_set._offer_self_commit` via `aw backlog set`.
  - Observed evidence:
    `--no-commit` porcelain:
    ```
    D .aw/records/backlog/open/20260930-bklung-01-bklung-ungated-item.backlog.md
    ?? .aw/records/backlog/done/
    ?? .aw/records/history.jsonl
    ```
    no-flag (non-interactive) porcelain:
    ```
    D .aw/records/backlog/open/20260930-bklung-01-bklung-ungated-item.backlog.md
    ?? .aw/records/backlog/done/
    ?? .aw/records/history.jsonl
    ```
    `--commit` git show:
    ```
    chore(backlog): set status done

     .../{open => done}/20260930-bklung-01-bklung-ungated-item.backlog.md   | 3 ++-
     1 file changed, 2 insertions(+), 1 deletion(-)
    ```
    Saved baseline bare-suite failure set: none (`7747 passed, 4 skipped, 3 warnings in 775.92s (0:12:55)`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `git diff -- agent_workflows/status_set.py` showing only the removed reset call and rewritten comment inside `_offer_self_commit`, plus the E-01 scratch measurement re-run after the change showing `R` (or `RM`) lines for `--no-commit` and no-flag, and `{open => done}` for `--commit`.
  - Observed evidence:
    `git diff -- agent_workflows/status_set.py`:
    ```diff
    diff --git a/agent_workflows/status_set.py b/agent_workflows/status_set.py
    index f5f9dc898..180e87e14 100644
    --- a/agent_workflows/status_set.py
    +++ b/agent_workflows/status_set.py
    @@ -2205,9 +2205,10 @@ def _offer_self_commit(

         paths = list(touched_paths)
         label = scoped_type_canonical or "records"
    -    # jgcm68 D2: unstage exactly these touched paths first (a no-op for in-place set rewrites) so the
    -    # helper cleanly re-stages them; scoped to the verb's own paths, never global.
    -    _gch._git(repo_root, ["reset", "--quiet", "HEAD", "--", *paths])
    +    # The touched paths are passed to git_commit_helper.offer_commit already staged by
    +    # artifact_core.git_mv; offer_commit drops a staged rename's source from its git add set
    +    # via _in_index and stages the rest itself, so no pre-reset is needed, and a pre-reset would
    +    # unstage the rename whenever the commit is skipped (backlog r73v9i).
         outcome = _gch.offer_commit(
             repo_root,
             paths,
    ```
    E-01 scratch measurement re-run after change:
    `--no-commit` porcelain:
    ```
    RM .aw/records/backlog/open/20260930-bklung-01-bklung-ungated-item.backlog.md -> .aw/records/backlog/done/20260930-bklung-01-bklung-ungated-item.backlog.md
    ?? .aw/records/history.jsonl
    ```
    no-flag porcelain:
    ```
    RM .aw/records/backlog/open/20260930-bklung-01-bklung-ungated-item.backlog.md -> .aw/records/backlog/done/20260930-bklung-01-bklung-ungated-item.backlog.md
    ?? .aw/records/history.jsonl
    ```
    `--commit` git show:
    ```
    chore(backlog): set status done

     .../{open => done}/20260930-bklung-01-bklung-ungated-item.backlog.md   | 3 ++-
     1 file changed, 2 insertions(+), 1 deletion(-)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted pytest output of `test_backlog_relocation_porcelain_shape_agreement` failing on pre-E-02 code and passing after, plus the test diff.
  - Observed evidence:
    Failing on pre-E-02 code:
    ```
    FAILED tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_relocation_porcelain_shape_agreement
    AssertionError: 0 != 1 : Expected 1 R rename line in porcelain:
     D .aw/records/backlog/open/20260928-testset-01-bk0001-test.backlog.md
    ?? .aw/records/backlog/done/
    ?? .aw/records/history.jsonl
    ```
    Passing after E-02:
    ```
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_relocation_porcelain_shape_agreement PASSED
    ```
    Test diff:
    ```python
    -        """Both spellings leave ' D <src>' plus '?? <dest>' in porcelain under --no-commit.
    -
    -        Reclassified from E-04 (c): measured at review that status_set._offer_self_commit
    -        runs 'git reset --quiet HEAD -- <paths>' after artifact_core.git_mv staged 'R',
    -        unstaging the rename. Neither spelling produces wy9aru AC-5's canonical staged 'R'
    -        rename today under --no-commit.
    -        """
    +        """Both spellings leave a single staged 'R' rename in porcelain under --no-commit.
    +
    +        Governed by spec wy9aru AC-5 ("A relocation performed by either spelling appears in
    +        git status --porcelain as a single R rename") and backlog r73v9i.
    +        """
    ...
    -                self.assertIn(" D .aw/records/backlog/open/", porcelain)
    -                self.assertIn("?? .aw/records/backlog/done/", porcelain)
    +                lines = [line.strip() for line in porcelain.splitlines() if line.strip()]
    +                r_lines = [
    +                    l
    +                    for l in lines
    +                    if l.startswith("R")
    +                    and "backlog/open/" in l
    +                    and " -> " in l
    +                    and "backlog/done/" in l
    +                ]
    +                self.assertEqual(
    +                    len(r_lines), 1, f"Expected 1 R rename line in porcelain:\n{porcelain}"
    +                )
    +                self.assertNotIn(" D .aw/records/backlog/open/", porcelain)
    +                self.assertNotIn("?? .aw/records/backlog/done/", porcelain)
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted pytest output for the five new tests (a)-(e) passing after E-02, and (a)/(b)/(c) failing on pre-E-02 code with the failure showing the ` D`/`??` shape; the test diff showing assertions on git output only, that (a) passes no `--yes` and forces `AW_NONINTERACTIVE=1`, and that (c) drives `aw ipd set`.
  - Observed evidence:
    Failing before E-02:
    (a) `test_backlog_relocation_noninteractive_default_porcelain_shape`:
    ```
    AssertionError: 0 != 1 : Expected 1 R rename line in porcelain:
     D .aw/records/backlog/open/20260928-testset-01-bk0001-test.backlog.md
    ?? .aw/records/backlog/done/
    ?? .aw/records/history.jsonl
    ```
    (b) `test_spec_relocation_porcelain_shape`:
    ```
    AssertionError: 0 != 1 : Expected 1 R rename line in porcelain:
     D .aw/records/specs/draft/20261001-testspec-01-sp0001-test.spec.md
    ?? .aw/records/history.jsonl
    ?? .aw/records/specs/to-review/
    ```
    (c) `test_plan_relocation_porcelain_shape`:
    ```
    AssertionError: 0 != 1 : Expected 1 R rename line in porcelain:
     D .aw/records/plans/pending/20260901-testset-01-pl0002-plan.ipd.md
    ?? .aw/records/plans/INDEX.json
    ?? .aw/records/plans/INDEX.md
    ?? .aw/records/plans/superseded/
    ```
    Passing after E-02:
    ```
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_relocation_noninteractive_default_porcelain_shape PASSED
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_spec_relocation_porcelain_shape PASSED
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_plan_relocation_porcelain_shape PASSED
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_relocation_commit_shape PASSED
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_backlog_relocation_commit_preserves_unrelated_staged PASSED
    ```
    Test diff verifies assertions inspect git output only, (a) forces `AW_NONINTERACTIVE=1` with no `--yes`, and (c) drives `aw ipd set`.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the test diff showing it drives `aw backlog set ... --no-commit` then `runner_shared.commit_backlog_close` and asserts on the returned sha and `git show --name-status -M` output; pasted pytest output passing on pre-E-02 code and again after E-02.
  - Observed evidence:
    Pre-E-02 execution:
    ```
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_runner_commit_backlog_close_consumes_relocation PASSED
    ```
    Post-E-02 execution:
    ```
    tests/test_set_dispatch_parity.py::TestBacklogSetDispatchParity::test_runner_commit_backlog_close_consumes_relocation PASSED
    ```
    Test diff drives `aw backlog set ... --no-commit` then `runner_shared.commit_backlog_close(repo, "bk0001", "close", run_checked=run_checked)` and verifies returned sha, `git show --name-status -M` has `R` rename line, and tracked porcelain is clean.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the `CHANGELOG.md` hunk; a grep of that hunk for em/en dashes returning nothing; the pasted targeted pytest run from Required tests; the pasted bare `python3 -m pytest` summary line and its failure set compared by name to V-01's baseline; pasted `aw ipd lint` and `aw check release-gates` output.
  - Observed evidence:
    `CHANGELOG.md` hunk:
    ```markdown
    - Fixed: aw specs set <status> <path> run from outside the repository now writes the same history-sidecar record as aw specs set <path> --status <status> (F-06).
    +- Fixed: when aw backlog set, aw specs set, or aw ipd set moves a record to a new status directory without committing, the move now stays staged as a single file rename instead of a deleted file plus an untracked file.
    ```
    Grep for em/en dashes in CHANGELOG.md diff returned nothing (0 matches).
    Targeted pytest run:
    ```
    139 passed in 28.08s (attempt 1)
    139 passed in 54.84s (attempt 2)
    ```
    Bare `python3 -m pytest` summary line:
    ```
    7753 passed, 4 skipped, 3 warnings in 943.04s (0:15:43) (attempt 1 baseline)
    7926 passed, 4 skipped, 18 xfailed, 3 warnings in 1198.03s (0:19:58) (attempt 2)
    ```
    Comparison to V-01 baseline failure set: baseline had 0 failures, post-fix has 0 failures; the 6 newly added tests all pass.
    `aw ipd lint`:
    ```
    - >  ◕  approved     plan        20261012-r73v9i-01-a63epo  [medium]  [blocking]  conforming
    ```
    `aw check release-gates`:
    ```
    AW check  release-gates                                                  5072 ms
    ✓ CONFORMS  231 release-gates checked

    Evidence
      backlog  116   specs  21   plans  93   releases  1
      errors  0   warnings  0   info  0
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Execution contract:

- Open questions: OQ-01 is resolved; no blocking question remains.
- Scope fence: the declared `- Scope-Paths:` are `agent_workflows/status_set.py`, `tests/test_set_dispatch_parity.py`, `CHANGELOG.md`, and this plan. This is a declaration, not a stop condition: an out-of-scope edit that proves necessary is made and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Do NOT touch the same pre-reset in `cli._offer_records_commit`, `plans_archive` or `research_archive` (Deferred).
- Honesty: every `Observed evidence` MUST paste the ACTUAL command output (pytest summary lines, `git status --porcelain`, `git show`, `git diff`); never claim a pass that was not run. Observe the failing-before state by writing E-03/E-04/E-06 BEFORE E-02, never with `git stash`.
- Commit: path-scoped via `aw commit a63epo -- agent_workflows/status_set.py tests/test_set_dispatch_parity.py CHANGELOG.md <this plan>`; never `git add -A`, never push.
- Lifecycle: start with `aw ipd begin a63epo --actor <you>`. The terminal transition to `executed/` happens only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence with `Result: pass`. Under `aw oc run`/`aw agy run` the runner performs that transition, so the executor must NOT run `aw ipd finalize` itself; when executing by hand, run `aw ipd finalize a63epo --actor <you> --message <msg> --apply` (never a hand `git mv` to `executed/`).
