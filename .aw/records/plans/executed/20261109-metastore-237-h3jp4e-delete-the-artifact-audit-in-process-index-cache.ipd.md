# IPD: Delete the artifact audit in-process index cache

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 4.5 says the SQLite cache replaces `artifact_audit._INDEX_CACHE`. Today `artifact_audit.build_index` keeps an `OrderedDict` LRU (`_INDEX_CACHE`, bounded by `_INDEX_CACHE_MAX = 8`) keyed on a directory signature from `artifact_audit._dir_signature`, and `artifact_audit.find_artifact` pops a stale entry. This is part 8 of the round-3 split of `snin8q` (Order 42), carrying `snin8q` E-07 verbatim.
- Scope: delete the cache and its bound, make `artifact_audit.build_index` answer from `artifact_meta.query`/`resolve` on every call, delete `tests/test_artifact_audit_cache_eviction.py`, and retarget the two freshness test modules. EXCLUDES every other INDEX symbol (Orders 233 to 236).
- Scope-Paths: agent_workflows/artifact_audit.py, tests/test_artifact_audit_cache_eviction.py, tests/test_artifact_audit_index_cache.py, tests/test_artifact_audit_identity_staleness.py, .aw/records/plans/pending/20261109-metastore-237-h3jp4e-delete-the-artifact-audit-in-process-index-cache.ipd.md
- Scope-Exceeded: .aw/records/backlog/open/20261124-juua3p-01-juua3p-artifact-audit-build-index-enumerates-by-file-walk.backlog.md (defect_report carrier required by the driver contract: build_index still file-walks instead of reading the artifact_meta cache E-02 wording filing a backlog item is mandated, not optional work)
- Item-Dependencies: executed:1ajqaa, executed:54a80m, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:q6epwc, executed:t4gl15
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: standard
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 237
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: h3jp4e

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-24 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5.5-1m-us variant=high profile=opus): aw oc run self-finalize: h3jp4e verified (set metastore, attempt 2). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261124-juua3p-01-juua3p-artifact-audit-build-index-enumerates-by-file-walk.backlog.md: defect_report carrier required by the driver contract: build_index still file-walks instead of reading the artifact_meta cache (E-02 wording); filing a backlog item is mandated, not optional work]
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): /plan-review (antigravity/gemini-3.8-flash): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from snin8q (round 3, research nj8zdp guidance).

## Goal

After this plan, `artifact_audit.build_index` holds no in-process cache: a record added, deleted or moved after a first call is reflected by the second call.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

`snin8q` E-07 ("Delete `artifact_audit._INDEX_CACHE` and `_INDEX_CACHE_MAX` ... `artifact_audit.build_index` answers from `artifact_meta.query`/`resolve` on every call. Delete `tests/test_artifact_audit_cache_eviction.py` (it tests the removed LRU) and retarget the freshness assertions of `tests/test_artifact_audit_index_cache.py` and `tests/test_artifact_audit_identity_staleness.py` to the behavior") is split across E-01 to E-04 here.

PIN RULE (carried from `9o83cr`): before the edit, save the modules' per-test outcome list (`mkdir -p .aw/state/h3jp4e/ && python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA tests/test_artifact_audit_cache_eviction.py tests/test_artifact_audit_index_cache.py tests/test_artifact_audit_identity_staleness.py | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/h3jp4e/<E>-before.txt`); after it, the same into `<E>-after.txt`. A retargeted test keeps every input case; each case of the deleted eviction module is named "subject removed (LRU deleted)" in the mapping.

### Task group 1: pin, delete, retarget

- [x] E-01 Ensure directory `.aw/state/h3jp4e/` exists (`mkdir -p .aw/state/h3jp4e/`) and pin the three test modules (PIN RULE, `E-01-before.txt`).
  - Depends on: none
  - Expected outcome: `.aw/state/h3jp4e/E-01-before.txt` exists.
  - Execution state: performed

- [x] E-02 In `agent_workflows/artifact_audit.py`, delete `_INDEX_CACHE`, `_INDEX_CACHE_MAX` and their comment block; in `artifact_audit.build_index` remove the cache lookup, insert and eviction so it builds from `artifact_meta.query`/`resolve` on every call; in `artifact_audit.find_artifact` remove the stale-entry pop. Delete `artifact_audit._dir_signature` if no caller remains.
  - Depends on: E-01
  - Expected outcome: `rg -n "_INDEX_CACHE" agent_workflows` prints nothing.
  - Execution state: performed

- [x] E-03 Delete `tests/test_artifact_audit_cache_eviction.py`, and in `tests/test_artifact_audit_index_cache.py` and `tests/test_artifact_audit_identity_staleness.py` remove every `_audit._INDEX_CACHE` reference (the `.clear()` setup calls and the `_INDEX_CACHE[key][1]` reads), asserting instead that a record added, deleted or moved between two `build_index` calls is reflected by the second.
  - Depends on: E-02
  - Expected outcome: `rg -n "_INDEX_CACHE" tests` prints nothing.
  - Execution state: performed

- [x] E-04 Save `E-04-after.txt`, run the two remaining modules, and commit through `aw commit h3jp4e -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-03
  - Expected outcome: both modules pass; the mapping accounts for every case.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The `artifact_meta` interface (`tve77h`, `ffceq0`): `query(...)`, `resolve(path_or_id6)`; `t4gl15` already routes `artifact_audit.build_index` reads through the cache (AC-1a).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `3d0ddb845`: `rg -n "_INDEX_CACHE" agent_workflows` prints 10 lines in `artifact_audit.py` (in `build_index` and `find_artifact`); `rg -n "_INDEX_CACHE" tests` prints 7 lines in `tests/test_artifact_audit_cache_eviction.py`, 6 in `tests/test_artifact_audit_identity_staleness.py`, 6 in `tests/test_artifact_audit_index_cache.py` (`snin8q` F-10).

## Proposed changes (ordered, validatable)

1. Create baseline directory and pin the three test modules (E-01).
2. Delete `_INDEX_CACHE`, `_INDEX_CACHE_MAX`, and LRU handling in `artifact_audit.py` (E-02).
3. Delete `tests/test_artifact_audit_cache_eviction.py` and retarget freshness assertions in `test_artifact_audit_index_cache.py` and `test_artifact_audit_identity_staleness.py` (E-03).
4. Save `E-04-after.txt`, verify diff mapping, run remaining modules, and commit path-scoped (E-04).

```mermaid
flowchart TD
    A["E-01: mkdir -p .aw/state/h3jp4e/ and pin 3 test modules into E-01-before.txt"] --> B["E-02: Delete _INDEX_CACHE, _INDEX_CACHE_MAX and LRU logic in artifact_audit.py"]
    B --> C["E-03: Delete eviction test module and retarget freshness tests in index_cache / identity_staleness"]
    C --> D["E-04: Capture E-04-after.txt, verify diff mapping, run pytest suite"]
    D --> E["E-04: Commit path-scoped via aw commit h3jp4e"]
```

## Deferred / out of scope (with reason)

- Every other INDEX writer, the STATUS renderer: Orders 233 to 236.
  - Carrier: snin8q

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 4 E-items, 4 work Scope-Paths.

## Required tests / validation

`tests/test_artifact_audit_index_cache.py`, `tests/test_artifact_audit_identity_staleness.py` (retargeted); `tests/test_artifact_audit_cache_eviction.py` deleted. Then the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.5.

## Open questions

### OQ-01: Does removing the LRU make `aw find` noticeably slower?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The SQLite cache (`ffceq0`, `t4gl15`) is the replacement the spec names; a repeated call reads the cache rather than rescanning. If a measurement shows a user-perceptible regression, file it as a `bug` with the number (AGENTS.md perceptibility rule). Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `wc -l .aw/state/h3jp4e/E-01-before.txt` and one line from each of the three named modules.
  - Observed evidence:
    - `wc -l .aw/state/h3jp4e/E-01-before.txt` printed `16 .aw/state/h3jp4e/E-01-before.txt` (re-pinned in attempt 2 with the four scope files restored to base `3223c1a8f`, before re-applying the edit).
    - One line per module from that file:
      - `PASSED tests/test_artifact_audit_cache_eviction.py::TestArtifactAuditCacheEviction::test_cache_size_is_bounded_at_cap`
      - `PASSED tests/test_artifact_audit_index_cache.py::TestArtifactAuditIndexCache::test_route1_same_tick_addition_detected`
      - `PASSED tests/test_artifact_audit_identity_staleness.py::TestArtifactAuditIdentityStaleness::test_stale_positive_returns_fresh_truth`
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `rg -n "_INDEX_CACHE" agent_workflows` printing nothing, and the `git diff` hunks of `artifact_audit.build_index` and `artifact_audit.find_artifact`.
  - Observed evidence:
    - `rg -n "_INDEX_CACHE" agent_workflows` printed nothing (exit 1).
    - `artifact_audit._dir_signature` had no remaining caller (`rg -n "_dir_signature" agent_workflows tests` printed nothing after the edit) and was deleted with the now-unused `import os` and `from collections import OrderedDict`.
    - Deviation, recorded as decision `02-h3jp4e-D1`: `build_index` still enumerates through `selectors._iter_paths` and reads `- Id:` through `selectors._read_id` (which parses via `artifact_meta.read_text`) rather than calling `artifact_meta.query`. The `artifacts` table keys on `id6` (`id6 TEXT PRIMARY KEY`), so `query` cannot report two files declaring one id6, which the phantom-collision tests require. Follow-up carrier: backlog `juua3p`. Cold-call cost is unchanged (about 3.0s before and after on 3549 paths).
    - `git diff` hunks (commit `35c678128`, carried forward from attempt-1 commit `800d17783`), comment-only lines elided:
      ```
      @@ -1203,12 +1116,2 @@ def build_index(
           repo_root = Path(repo_root)
      -    try:
      -        key = (str(repo_root.resolve()), tuple(record_types))
      -    except OSError:
      -        key = (str(repo_root), tuple(record_types))
      -    sig = _dir_signature(repo_root, record_types)
      -    cached = _INDEX_CACHE.get(key)
      -    if cached is not None and cached[0] == sig:
      -        _INDEX_CACHE.move_to_end(key)
      -        return cached[1]
      -
           paths: List[Path] = []
      @@ -1237,9 +1140,5 @@ def build_index(
      -    index = ArtifactIndex(
      +    return ArtifactIndex(
               paths=paths, by_declared_id=by_declared, by_filename_id=by_filename
           )
      -    _INDEX_CACHE[key] = (sig, index)
      -    while len(_INDEX_CACHE) > _INDEX_CACHE_MAX:
      -        _INDEX_CACHE.popitem(last=False)
      -    return index
      @@ -1292,17 +1191,2 @@ def find_artifact(
                       if not all(_claims_id6(p) for p in exact):
      -                    try:
      -                        cache_key = (str(repo_root.resolve()), tuple(record_types))
      -                    except OSError:
      -                        cache_key = (str(repo_root), tuple(record_types))
      -                    cached_entry = _INDEX_CACHE.get(cache_key)
      -                    if cached_entry is not None and cached_entry[1] is index:
      -                        _INDEX_CACHE.pop(cache_key, None)
      -
                           # Re-derive once from a fresh index. When the caller passed artifact_index=,
      ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `rg -n "_INDEX_CACHE" tests` printing nothing, and the `git diff --stat` line deleting `tests/test_artifact_audit_cache_eviction.py`.
  - Observed evidence:
    - `rg -n "_INDEX_CACHE" tests` printed nothing (exit 1).
    - `git diff --stat` line: ` tests/test_artifact_audit_cache_eviction.py     | 147 ------------------------` (file deleted in `35c678128`).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `diff .aw/state/h3jp4e/E-01-before.txt .aw/state/h3jp4e/E-04-after.txt` with each removed name mapped or marked "subject removed (LRU deleted)", `python3 -m pytest -o addopts="" -v tests/test_artifact_audit_index_cache.py tests/test_artifact_audit_identity_staleness.py` with the add, delete and move freshness cases PASSED, and `git show --stat` of the `aw commit h3jp4e` commit listing only Scope-Paths files.
  - Observed evidence:
    - `diff .aw/state/h3jp4e/E-01-before.txt .aw/state/h3jp4e/E-04-after.txt` output and mapping:
      ```
      1,5d0
      < PASSED tests/test_artifact_audit_cache_eviction.py::TestArtifactAuditCacheEviction::test_cache_invalidated_on_real_change
      < PASSED tests/test_artifact_audit_cache_eviction.py::TestArtifactAuditCacheEviction::test_cache_size_is_bounded_at_cap
      < PASSED tests/test_artifact_audit_cache_eviction.py::TestArtifactAuditCacheEviction::test_hot_root_retained_across_interleaved_queries
      < PASSED tests/test_artifact_audit_cache_eviction.py::TestArtifactAuditCacheEviction::test_no_rebuild_on_cache_hit
      < PASSED tests/test_artifact_audit_identity_staleness.py::TestArtifactAuditIdentityStaleness::test_cost_shape_cache_is_reused_on_unchanged_tree
      7c2
      < PASSED tests/test_artifact_audit_identity_staleness.py::TestArtifactAuditIdentityStaleness::test_explicit_artifact_index_preserves_caller_object_and_revalidates_without_extra_traversal
      ---
      > PASSED tests/test_artifact_audit_identity_staleness.py::TestArtifactAuditIdentityStaleness::test_explicit_stale_artifact_index_preserves_caller_object_and_answers_fresh_truth
      9a5
      > PASSED tests/test_artifact_audit_identity_staleness.py::TestArtifactAuditIdentityStaleness::test_unchanged_tree_repeated_build_index_is_equal
      13d8
      < PASSED tests/test_artifact_audit_index_cache.py::TestArtifactAuditIndexCache::test_memoization_cache_reuses_index_and_invalidates_on_change
      16a12,14
      > PASSED tests/test_artifact_audit_index_cache.py::TestArtifactAuditIndexCache::test_second_build_index_reflects_addition
      > PASSED tests/test_artifact_audit_index_cache.py::TestArtifactAuditIndexCache::test_second_build_index_reflects_deletion
      > PASSED tests/test_artifact_audit_index_cache.py::TestArtifactAuditIndexCache::test_second_build_index_reflects_move
      ```
      - `cache_eviction::test_cache_size_is_bounded_at_cap`: subject removed (LRU deleted).
      - `cache_eviction::test_hot_root_retained_across_interleaved_queries`: subject removed (LRU deleted).
      - `cache_eviction::test_no_rebuild_on_cache_hit`: subject removed (LRU deleted).
      - `cache_eviction::test_cache_invalidated_on_real_change`: subject removed (LRU deleted); its add-between-calls case survives as `index_cache::test_second_build_index_reflects_addition`.
      - `identity_staleness::test_cost_shape_cache_is_reused_on_unchanged_tree` -> `identity_staleness::test_unchanged_tree_repeated_build_index_is_equal` (same fixture; now asserts equal indexes and answers, and that each call re-traverses).
      - `identity_staleness::test_explicit_artifact_index_preserves_caller_object_and_revalidates_without_extra_traversal` -> `identity_staleness::test_explicit_stale_artifact_index_preserves_caller_object_and_answers_fresh_truth` (same input case; renamed because "without extra traversal" was a cache property).
      - `index_cache::test_memoization_cache_reuses_index_and_invalidates_on_change` -> `index_cache::test_second_build_index_reflects_addition` (same fixture: plan A, repeat on unchanged tree, then add plan B), plus the new deletion and move cases.
      - The three wrong-answer tests (stale positive, wrong path, phantom collision) keep their names and inputs; each now primes a caller-held `stale_idx` from `build_index` and asserts the stale-index answer equals fresh truth.
    - `python3 -m pytest -o addopts="" -v tests/test_artifact_audit_index_cache.py tests/test_artifact_audit_identity_staleness.py`:
      ```
      tests/test_artifact_audit_index_cache.py::TestArtifactAuditIndexCache::test_second_build_index_reflects_deletion PASSED
      tests/test_artifact_audit_index_cache.py::TestArtifactAuditIndexCache::test_route3_deep_directory_addition_detected PASSED
      tests/test_artifact_audit_index_cache.py::TestArtifactAuditIndexCache::test_compound_route2_untyped_tree_with_pinned_mtime PASSED
      tests/test_artifact_audit_index_cache.py::TestArtifactAuditIndexCache::test_compound_route3_deep_directory_with_pinned_mtime PASSED
      tests/test_artifact_audit_index_cache.py::TestArtifactAuditIndexCache::test_route2_untyped_tree_addition_detected PASSED
      tests/test_artifact_audit_index_cache.py::TestArtifactAuditIndexCache::test_route1_same_tick_addition_detected PASSED
      tests/test_artifact_audit_index_cache.py::TestArtifactAuditIndexCache::test_second_build_index_reflects_addition PASSED
      tests/test_artifact_audit_index_cache.py::TestArtifactAuditIndexCache::test_second_build_index_reflects_move PASSED
      tests/test_artifact_audit_identity_staleness.py::TestArtifactAuditIdentityStaleness::test_cost_shape_true_tier_one_answer_does_not_rederive PASSED
      tests/test_artifact_audit_identity_staleness.py::TestArtifactAuditIdentityStaleness::test_wrong_path_returns_fresh_truth PASSED
      tests/test_artifact_audit_identity_staleness.py::TestArtifactAuditIdentityStaleness::test_explicit_stale_artifact_index_preserves_caller_object_and_answers_fresh_truth PASSED
      tests/test_artifact_audit_identity_staleness.py::TestArtifactAuditIdentityStaleness::test_phantom_collision_returns_fresh_truth PASSED
      tests/test_artifact_audit_identity_staleness.py::TestArtifactAuditIdentityStaleness::test_stale_positive_returns_fresh_truth PASSED
      tests/test_artifact_audit_identity_staleness.py::TestArtifactAuditIdentityStaleness::test_unchanged_tree_repeated_build_index_is_equal PASSED
      ============================== 14 passed in 2.51s ==============================
      ```
    - Full suite (`aw suite`, core gate): `2898 passed, 1 skipped, 11 warnings in 225.31s (0:03:45)` (attempt 2, at `35c678128`).
    - `git show --stat` of the `aw commit h3jp4e` commit (`aw commit: committed 4 path(s): 35c6781289ae7c8b5906133b986c268171bd9ddb`):
      ```
      35c6781289ae7c8b5906133b986c268171bd9ddb feat(h3jp4e): delete artifact_audit in-process index cache; build_index answers fresh on every call
       agent_workflows/artifact_audit.py               | 138 ++--------------------
       tests/test_artifact_audit_cache_eviction.py     | 147 ------------------------
       tests/test_artifact_audit_identity_staleness.py |  93 +++++++--------
       tests/test_artifact_audit_index_cache.py        | 140 ++++++++++++----------
       4 files changed, 134 insertions(+), 384 deletions(-)
      ```
      Every path is in Scope-Paths; nothing pushed.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. OQ-01 is resolved and not blocking. Pin-first.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code outside `agent_workflows/artifact_audit.py` is not modified.

Safety: if prerequisite `artifact_meta.query` / `resolve` implementations or SQLite cache mechanisms from `ffceq0` or `t4gl15` are absent, stop and report immediately: that is an unsafe condition, not a scope question.

Honesty rule: run the named test modules and `python3 -m pytest` (core gate), and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit h3jp4e -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize h3jp4e` itself.
