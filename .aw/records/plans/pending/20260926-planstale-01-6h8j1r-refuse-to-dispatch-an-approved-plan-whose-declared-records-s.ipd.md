# IPD: Refuse to dispatch an approved plan whose declared records scope path has moved or vanished

- Date: 2026-09-26
- Kind: child
- Concern: NOTHING VALIDATES THAT A PLAN'S DECLARED `Scope-Paths` TARGET STILL EXISTS BEFORE THE RUNNER SPENDS A TURN ON IT. Motivating case (backlog `mlc6mj`): plan `tgop8e`, approved 2026-09-12, declared `.aw/records/plans/pending/20260910-rdyrecheck-01-qhy3i3-...ipd.md` and existed to edit two success criteria inside `qhy3i3`; `qhy3i3` was finalized to `executed/` on 2026-09-21 (`fe120181 lifecycle(qhy3i3): finalize qhy3i3 -> executed`), and on 2026-09-23 the runner still dispatched `tgop8e` with queue action `execute`, for work that could not legally be done (AGENTS.md forbids adding commits to a plan already in `executed/`). Measured at HEAD `ea206c49`: `tgop8e`'s executed copy still declares that pending path, which does not exist. DESIGN CONSTRAINT, measured: of 24 approved pending plans, 13 legitimately declare 16 NOT-YET-EXISTING code/test paths (new files), so existence of an arbitrary scope path is NOT a valid gate; 0 approved pending plans declare a missing LITERAL path under `.aw/records/` (the one missing `.aw/records/` entry, `.aw/records/plans/pending/**` in `vtkfq8`, is a glob). A records path names an artifact that must already exist to be edited, so it is the only class that can be checked without false positives.
- Scope: IN: (a) one shared pure-ish predicate `check_engine.stale_record_scope_paths(repo_root, plan_text)` that returns, for each LITERAL (no `*`, `?`, `[`) `Scope-Paths` entry under `.aw/records/` that does not exist, a classification `moved-terminal` (the artifact's id6 now resolves to exactly one artifact that is retired), `moved` (resolves to exactly one non-retired artifact at a different path), or `vanished` (resolves to none); paths outside `.aw/records/`, globs, directory entries that exist, and grandfathered plans are ignored; (b) a new `aw check` rule `check.scope-path-target-stale` over approved (and reviewed/to-review) PENDING plans, riding the `aw check all` full-sweep seam beside `check.from-spec-dangling`, reporting ALL THREE classifications; (c) a dispatch-time refusal in `runner_shared.execute_item_core` for an `execute` action, before any clean-base check, lane allocation, begin, or agent turn, that marks ONLY that item `fail-gate` with a recorded `scope_target_refusal` reason naming each stale path and its classification, emits a `scope-target-stale` event, and returns so the run continues (the item-local-refusal precedent of `clean_base_refusal`) - BUT THE REFUSAL FIRES ON `moved-terminal` AND `vanished` ONLY, never on plain `moved` (corrected in review, F-8: a non-retired artifact that merely changed status directory is still fully editable, so refusing it would be a FALSE REFUSAL of a runnable plan; `aw check` still reports it so a human fixes the path); (d) amend spec `25kzda` Section 5.7's failure taxonomy with one row for this refusal; (e) behavioral tests and a real-corpus zero-false-positive scan. OUT: checking non-records paths (new files are legitimate); checking glob entries; auto-rewriting a plan's scope to the moved path (a human decides whether the plan is still meaningful); review-action dispatch (a review of a stale plan is how a human finds out; the `aw check` rule covers it); retiring `tgop8e`-style plans already in terminal directories (they are history); making the REFUSAL fire on `moved` (F-8).
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/runner_shared.py, tests/test_scope_path_target_stale.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: mlc6mj
- Blocks-Release: next
- Set: planstale
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 6h8j1r
- Approval: 2026-09-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-301..PR-307 FIXED, PR-308 OPEN as non-blocking OQ-04 (severity of a 'moved' finding is a maintainer call). Central fix: the refusal no longer fires on a non-retired 'moved' target, which would have fail-gated 7 live pending plans including this one when a cited spec advances status.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog mlc6mj. Design constraint measured at HEAD ea206c49 (16 legitimate not-yet-existing code/test paths across 13 approved pending plans; 0 missing literal .aw/records paths), so only literal .aw/records entries are checked. Classification prototyped against every plan's Scope-Paths corpus-wide: 58 missing literal records entries, all in executed/superseded plans, 40 moved-terminal and 18 moved, 0 vanished.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Stop the runner spending an agent turn on an approved plan whose declared records target has moved TO A TERMINAL DIRECTORY or vanished, and let `aw check all` flag that condition AND the weaker "merely moved" one before a run starts, with one shared predicate so the two can never disagree about the facts even though they act on different subsets of them.

THE TWO SURFACES DELIBERATELY DIFFER IN WHAT THEY ACT ON, and that asymmetry is the design (F-8). One predicate reports three classifications. `aw check` reports all three, because every one of them means a declared path is wrong and a human should fix it. The RUNNER refuses only `moved-terminal` and `vanished`, because only those mean the work cannot legally be done: a plan whose target merely moved from `specs/approved/` to `specs/implementing/` can still be executed, and refusing it would convert a stale string into a lost turn. Sharing the predicate while differing on the ACTION is what keeps them from disagreeing about facts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline

- [x] E-01 RE-MEASURE THE POPULATION at the executing HEAD with a throwaway script (not committed) that parses every `.aw/records/plans/pending/*.ipd.md`'s `- Scope-Paths:` with `ipd_schema.parse_scope_paths` and reports, per `- Status:`: (1) the count of missing non-glob entries OUTSIDE `.aw/records/`, (2) the list of missing non-glob entries UNDER `.aw/records/`. Also confirm `tgop8e`'s executed copy still declares the missing `qhy3i3` pending path. Paste both.
  - Depends on: none
  - Expected outcome: (1) non-zero (new-file declarations: about 16 at authoring, 30 across all pending statuses when re-measured in review); (2) empty for pending plans of EVERY status, not only approved (review widened this and confirmed 0 across all 49 pending plans carrying `Scope-Paths`). If (2) is non-empty, list each and say whether it is a genuine stale target (that is a finding to report, not a reason to stop). Report the integers you measure; do not treat a difference from these as a failure (see the RE-DERIVE rule in the gate).
  - Execution state: performed

### Task group 2: the predicate and the check

- [x] E-02 ADD `check_engine.stale_record_scope_paths(repo_root, plan_text) -> list[StaleScopePath]` with a small `NamedTuple` `StaleScopePath(path, classification, resolved)` and three module constants `SCOPE_STALE_MOVED_TERMINAL = "moved-terminal"`, `SCOPE_STALE_MOVED = "moved"`, `SCOPE_STALE_VANISHED = "vanished"`. Algorithm: read the `- Scope-Paths:` value from the plan's metadata (use `ipd_schema.parse_scope_paths`; a grandfathered or unparseable value yields `[]`); for each entry, skip if it contains `*`, `?` or `[`, skip if it does not start with `.aw/records/`, skip if `(repo_root / entry).exists()`; otherwise derive the id6 from the filename's clustered identity slot and the type from `status_set.detect_artifact_type(repo_root / entry, repo_root)` (verified in review: it works on a NONEXISTENT path, returning `plans`/`backlog`/`specs` from the path shape, and `other` for an unrecognized facet such as a `.review.md`); resolve with `selectors.resolve(repo_root, type, id6, allow=frozenset({selectors.MATCH_ID6}))` (exact `- Id:` only) and read the result's `.paths` LIST. THREE API DETAILS, EACH MEASURED IN REVIEW BECAUSE GETTING ONE WRONG SILENTLY DEGRADES THE PREDICATE TO ITS FALLBACK: (i) `artifact_naming.parse_clustered` returns a bare `re.Match` or `None`, NOT an object with an `.id6` attribute, so the id6 comes from `m.group("id6")` after a `None` check; an attribute access would raise or yield `None` on every entry and route everything through the fallback. (ii) `selectors.Resolution` has fields `(paths, kind, rejected_kind, selector)` and NO `path`/`ok`/`matches` member, so read `r.paths` and treat an empty list as no hit. (iii) `detect_artifact_type` can return `other`; skip the selector route in that case rather than calling `resolve` with a bogus record type. If the selector route yields nothing (a legacy spec name has no id6 slot, measured 13 such entries corpus-wide at this HEAD), fall back to the SAME basename anywhere under `.aw/records/` (`rglob(name)`). BOUND THE FALLBACK TO ARTIFACT FILENAMES: measured in review, two corpus entries name a GENERATED index file (`.aw/records/research/INDEX.json` and `INDEX.md`) whose basename is not unique, and the fallback resolved both to `.aw/records/plans/INDEX.*`, i.e. a DIFFERENT artifact's index, producing a confidently wrong `resolved` path. So run the fallback only when the basename carries a records artifact facet (`.ipd.md`, `.spec.md`, `.backlog.md`, `.review.md`, `.release.md`, `.walkthrough.md`, `.prompt.md`, `.research.md`); for any other basename classify `vanished` with `resolved` empty, which is honest (we cannot say where it went) instead of confidently wrong. Exactly one hit: `moved-terminal` when `check_engine.is_retired(hit)` (verified in review: `_RETIRED_PATH_SEGMENTS` is exactly `archive, done, executed, not-executed, parked, shipped, superseded` and `_RETIRED_STATUSES` adds `implemented`, so it covers every records type), else `moved`. Zero hits: `vanished`. More than one hit: `moved` with every hit listed in `resolved` (ambiguity is still "not where declared"; measured 0 such cases corpus-wide). Do NOT use `run_selection_policy.is_in_terminal_directory` here: it counts `/reusable/` as terminal (see `ipd_lifecycle.plan_already_finalized`'s docstring) and misses backlog `done/` and spec `implemented/`. Pure except for filesystem reads; no git, no subprocess.
  - Depends on: E-01
  - Expected outcome: on `tgop8e`'s executed text the predicate returns one `moved-terminal` entry resolving to `qhy3i3`'s executed path (verified in review: the declared pending path is absent and `selectors.resolve(root, 'plans', 'qhy3i3', allow={MATCH_ID6})` returns exactly the `executed/` path); on every pending plan of ANY status it returns `[]` (verified in review: 0 missing literal `.aw/records/` entries across all 49 pending plans carrying `Scope-Paths`, not only the approved ones).
  - Execution state: performed

- [x] E-03 REGISTER AND WIRE `check.scope-path-target-stale`. Add `"check.scope-path-target-stale": RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")` to `RULE_REGISTRY` with a comment (invariant `""`: no catalog invariant in spec `pqsx96` covers scope-target freshness, and inventing one is out of scope; `error` because a stale target makes the plan unexecutable as written). Add `check_scope_path_target_stale(repo_root)` iterating `_iter_plan_ipds(repo_root)`, restricted to paths whose parent directory is `pending` (terminal plans are history and would be 58 permanent findings), calling E-02's predicate, and emitting one `enrich_drift(_core.Drift(str(path), rule, detail), observed=..., required=..., recovery=...)` per stale entry, whose recovery names the resolved path and says to either retire the plan (`aw ipd set superseded|not-executed ...`) or correct its `Scope-Paths` and re-review. Wire it into `check_types`' `collisions` full-sweep block with its OWN `try/except Exception: pass`, matching its neighbours.
  - Depends on: E-02
  - Expected outcome: `aw check all` on this repo reports zero `check.scope-path-target-stale` findings (verified in review: 0 missing literal records entries across all 49 pending plans with `Scope-Paths`); on a fixture repo holding a pending approved plan whose declared records target moved to `executed/`, it reports exactly one. THE RULE REPORTS ALL THREE CLASSIFICATIONS, including plain `moved`, and its detail MUST name the classification: the check's job is "this declared path is wrong, fix it", which is true of all three, while only two of them stop a run (F-8). Say so in the rule's comment so a later reader does not "harmonize" the check down to the runner's subset.
  - Execution state: performed

### Task group 3: the dispatch refusal

- [x] E-04 REFUSE AT DISPATCH, ITEM-LOCALLY, ON `moved-terminal` AND `vanished` ONLY. In `runner_shared.execute_item_core`, when `action == "execute"`, read `plan_path`'s text, call E-02's predicate, and keep only entries whose classification is `moved-terminal` or `vanished` (a plain `moved` entry is NOT a refusal; see F-8 and the Goal). If any remain: set `attempt["ended_at"]`, `attempt["scope_target_refused"] = reason`, `attempt["disposition"] = "fail-gate"`, `item["status"] = "fail-gate"`, `item["scope_target_refusal"] = reason` (reason lists each `path -> classification (resolved: ...)`), `save_state`, append a `scope-target-stale` event to `events.jsonl` with `id6`, `paths`, and `detail`, print one red line naming the item and reason, and `return`. That is exactly the shape of the existing `clean-base-refused` arm (verified in review, symbol for symbol: it sets `attempt["ended_at"]`, `attempt["clean_base_refused"]`, `attempt["disposition"] = "fail-gate"`, `item["status"] = "fail-gate"`, `item["clean_base_refusal"]`, calls `save_state`, appends a `clean-base-refused` event, prints a red line to stderr, and returns), so the run continues with independent items and `cascade_dependency_blocked` marks dependents `fail-depend` on the next loop iteration with no new code. A predicate exception must NOT refuse (fail open to today's behavior, record `attempt["scope_target_check_error"]`), because this gate adds protection and must never block a run on its own bug. Reuse `fail-gate` (verified in review: it is in `TERMINAL_STATES_CANONICAL`); do not mint a new status token. WHERE, PRECISELY, corrected in review (F-9): the authored instruction said "immediately after `plan_path = resolve_plan_path(...)` and the `attempt` record is appended", but those two points are about forty lines apart and `build_prompt` + `write_prompt` run BETWEEN them, so "immediately after" is ambiguous and the later reading WRITES A PROMPT FILE and a `prompt_sha256` for a turn that will never happen. Put the check as early as the data allows: directly after `action`/`is_review` are computed and BEFORE `build_prompt`/`write_prompt`, refusing with a minimal attempt record (`number`, `started_at`, `ended_at`, `action`, the refusal fields) rather than the full prompt-bearing one. If placing it there proves to need state the prompt block builds, say so in V-04 and place it immediately before the clean-base block instead, but do NOT leave an orphan prompt file unexplained.
  - Depends on: E-02
  - Expected outcome: a queued approved plan with a moved-terminal records target ends `fail-gate` with `scope_target_refusal` set, no agent turn is spawned, no lane is allocated, no prompt file is left for the refused attempt, and the next independent item still runs. A plan whose only stale entry is plain `moved` is NOT refused and runs normally.
  - Execution state: performed

### Task group 4: spec, proof

- [x] E-05 AMEND SPEC `25kzda` Section 5.7 "Failure taxonomy": add one row, placed after "Non-runnable state/type" (verified in review: that row exists and reads `| Non-runnable state/type | Valid terminal/gated/narrative record | Skip without a session | type_or_status_not_runnable |`, and the neighbouring `Host guarantee unavailable` row carries exactly the "Refuse the item before session start; cascade dependents; continue independent items" response this refusal copies), reading `| Stale scope target | A literal Scope-Paths entry under .aw/records/ no longer exists and its artifact is RETIRED or unresolvable | Refuse the item before session start; cascade dependents; continue independent items | scope_target_stale |`. NOTE THE DETECTION WORDING IS NARROWER THAN THE AUTHORED DRAFT (corrected in review, F-8): the draft said "moved or vanished", which would commit the SPEC to refusing a merely-moved non-retired target, i.e. to the false refusal this review removed. The spec must describe the subset the runner actually refuses, or the contract and the code disagree on day one. Then add one short paragraph below the table stating (a) why only literal records paths are checked (new code/test files are legitimately absent), (b) that the shared predicate reports three classifications while the refusal acts on two, and why, and (c) the predicate's name. Record the amendment with `aw specs note <spec> --message "..."` naming this plan's id6. The spec stays `approved`.
  - Depends on: E-04
  - Expected outcome: the table carries the row with the narrowed detection wording; the paragraph states the report-three/refuse-two asymmetry; the spec's history carries the note; `aw specs check` reports nothing new for the spec.
  - Execution state: performed

- [x] E-06 ADD `tests/test_scope_path_target_stale.py` (behavioral only; no source-text or AST assertions). Predicate cases on a temp repo: (1) a declared pending plan path whose file now sits in `executed/` -> `moved-terminal`; (2) a declared backlog `open/` path now in `done/` -> `moved-terminal`; (3) a declared spec path now in `to-review/` (non-retired) -> `moved`; (4) a declared records path with no artifact anywhere -> `vanished`; (5) a missing NON-records path (`agent_workflows/new_module.py`, `tests/test_new.py`) -> ignored; (6) a glob (`.aw/records/plans/pending/**`) and an existing directory entry -> ignored; (7) a grandfathered `Scope-Paths` -> `[]`; (8) a legacy spec name with no id6 slot resolved via the basename fallback. `aw check` cases: (9) `check_scope_path_target_stale` reports one finding for a pending plan with case (1)'s scope and none for the same text under `executed/`. Dispatch cases, reusing `tests.test_oc_runipd._init_repo_with_conforming_plan` and `support.declare_execution_role(self)`: (10) OC host: a conforming approved plan whose `Scope-Paths` names a moved-terminal records path, run through `oc_runipd.execute_item` with `run_opencode` patched to a launcher that FAILS the test if called -> `item["status"] == "fail-gate"`, `scope_target_refusal` names the path, no `worktree` key on the attempt, a `scope-target-stale` event exists; (11) the same on the AGY host (`agy_runipd.execute_item`, `run_agy_turn` patched to fail); (12) a two-item queue through `oc_runipd.run_queue` where item 1 is stale and item 2 is independent and clean: item 1 `fail-gate`, item 2 reaches its launcher; (13) a plan whose only missing path is a new code file is NOT refused. THREE CASES ADDED IN REVIEW, each pinning a decision that is otherwise only prose: (14) THE `moved` NEGATIVE, which is the most important test in the file: a conforming approved plan whose only stale entry is a NON-RETIRED moved artifact (for example a declared `specs/approved/<f>.spec.md` whose file now sits in `specs/implementing/`) is NOT refused and REACHES its launcher, while `check_scope_path_target_stale` on the same repo DOES report it. Without this case, a later "simplification" that refuses on any stale entry passes the whole suite (F-8). (15) THE NON-ARTIFACT BASENAME: a declared missing `.aw/records/research/INDEX.json` classifies `vanished` with EMPTY `resolved`, and specifically does NOT resolve to `.aw/records/plans/INDEX.json`; assert the resolved path is empty rather than merely that a finding exists, since the defect is a confidently wrong answer and not a missing one (F-10). (16) NO ORPHAN PROMPT: on a refused item, assert the run's `prompts/` directory contains no file for that item and attempt, which pins the placement decision in E-04 (F-9).
  - Depends on: E-03, E-04
  - Expected outcome: all pass; (1)-(4), (8)-(12), (15) fail before the change; (14) and (16) are regression guards that must pass both before and after for the parts that describe today's behavior (an unrefused run) and fail against a naive implementation that refuses on any stale entry, which is what they exist to prevent. State which of the two they did.
  - Execution state: performed

- [x] E-07 PROVE ZERO FALSE POSITIVES ON THE REAL CORPUS and run the bare suite. Run the E-02 predicate over every `.aw/records/plans/pending/*.ipd.md` whose status is `approved` and paste the per-plan count (must be all zero), then over every plan in every bucket and paste the classification histogram (authoring measurement: 58 entries, all in terminal-directory plans, 40 moved-terminal, 18 moved, 0 vanished). Run `python3 -m agent_workflows check all --agent` and paste the grep for `scope-path-target-stale` (must be empty). Run the bare `python3 -m pytest` before and after.
  - Depends on: E-06
  - Expected outcome: zero findings on approved pending plans; zero rule hits from `aw check all`; after-minus-before failing node set empty.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Item-local refusal precedent: `execute_item_core`'s clean-base arm writes `attempt["clean_base_refused"]`, `attempt["disposition"] = "fail-gate"`, `item["status"] = "fail-gate"`, `item["clean_base_refusal"]`, saves state, appends a `clean-base-refused` event, prints, and returns; the drivers' `run_queue` loops then continue and `cascade_dependency_blocked` marks dependents. Spec `25kzda` Section 5.7 states the same "Refuse the item before session start; cascade dependents; continue independent items" response for `host_capability_unavailable`.
- Dependency re-check at dispatch lives in each driver's `run_queue` (`dependency_status(item, state)` in the selection loop) and in `runner_shared.cascade_dependency_blocked`; this plan's refusal sits in the shared `execute_item_core` so both hosts get it once.
- Cross-tree reference rules ride the `aw check all` full-sweep seam in `check_engine.check_types` (`check_from_spec_dangling`, `releases.check_graduated_to`, `check_review_dangling`), each in its own `try/except`, iterating `_iter_plan_ipds`.
- Retired predicate: `check_engine.is_retired` (path segments `archive`, `executed`, `superseded`, `not-executed`, `parked`, `done`, `shipped`, or status in that set plus `implemented`). `run_selection_policy.is_in_terminal_directory` is plans-only and counts `/reusable/` (warned against in `ipd_lifecycle.plan_already_finalized`).
- Exact id6 resolution: `selectors.resolve(..., allow=frozenset({selectors.MATCH_ID6}))`; without `allow`, a substring filename match can win.
- Test policy (maintainer ruling 2026-09-26): behavior tests only. Suites run BARE; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1..F-7 were measured by the author at HEAD `ea206c49` (2026-09-26). EVERY ONE WAS RE-DRIVEN IN REVIEW at this branch head by calling the shipped symbols and by running a faithful prototype of E-02's algorithm over the whole plans corpus; F-8..F-12 are review findings. Where a count changed, both readings are given, because the drift is itself the reason E-01 and E-07 re-derive rather than cite.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | runner dispatch | No check between queue selection and agent turn reads a plan's `Scope-Paths` targets. | `execute_item_core` goes from `resolve_plan_path` to prompt build, clean-base, lane allocation, begin, spawn; no scope-target read |
| F-2 | HIGH | motivating case | `tgop8e` declares a pending path for `qhy3i3`, which moved to `executed/` nine days after approval. | `ls` of the declared path: absent; `git log --all -1 -- <declared path>` -> `fe120181`; executed copy's `- Scope-Paths:` still names it |
| F-3 | HIGH (design constraint) | approved pending plans | 13 of 24 approved pending plans declare 16 not-yet-existing non-records paths (new code/test files). A generic existence check would refuse them all. | authoring scan with `ipd_schema.parse_scope_paths` |
| F-4 | INFO | approved pending plans | 0 missing literal `.aw/records/` entries; the only missing records entry is the glob `.aw/records/plans/pending/**` (`vtkfq8`). RE-MEASURED in review and CONFIRMED, and widened: 0 across ALL 49 pending plans carrying `Scope-Paths` (30 `to-review`, 11 `approved`, 8 `reviewed`), not only the approved ones, so the rule is safe on the whole pending lane rather than just the subset the runner dispatches. | same scan; review re-run with `ipd_schema.parse_scope_paths` over `.aw/records/plans/pending/*.ipd.md` |
| F-5 | INFO | whole corpus | 58 missing literal records entries, all in `executed/`/`superseded/` plans; classification prototype: 40 moved-terminal, 18 moved, 0 vanished. RE-MEASURED in review: now 65 entries (45 moved-terminal, 20 moved, 0 vanished), in plans under `executed/` (61), `not-executed/` (2) and `superseded/` (2); 13 resolved via the basename fallback and 52 via the id6 selector; 0 ambiguous multi-hit. The count moved by 7 in days, which is why E-07 re-derives it. The `pending`-only restriction remains load-bearing: without it the rule would report 65 permanent findings. | review prototype over `.aw/records/plans/**/*.ipd.md` |
| F-6 | INFO | `run_selection_policy.is_in_terminal_directory` | Plans-only segment list including `/reusable/`; returns False for backlog `done/` and spec `implemented/`. CONFIRMED in review from the other side: `check_engine._RETIRED_PATH_SEGMENTS` is exactly `{archive, done, executed, not-executed, parked, shipped, superseded}` and `_RETIRED_STATUSES` is that set plus `implemented`, so `is_retired` covers every records type and correctly does NOT count `reusable`. The plan's choice is right. | `TERMINAL_DIRECTORY_SEGMENTS` literal; the two constants printed in review |
| F-7 | INFO | spec `25kzda` Section 5.7 | The failure taxonomy enumerates item-local refusal classes with stable reasons; a new refusal class belongs there. CONFIRMED in review: the table exists at "### 5.7 Failure taxonomy", the `Non-runnable state/type` row the plan places after is present verbatim, and `Host guarantee unavailable` carries the exact response string this refusal copies. | the rendered table read in review |
| F-8 | HIGH | E-04 as authored; the `moved` classification | **REFUSING ON `moved` WOULD REFUSE PLANS THAT ARE PERFECTLY RUNNABLE, WHICH IS A WORSE FAILURE THAN THE ONE BEING FIXED.** The authored refusal fired on ANY returned entry, and `moved` means the artifact resolves to exactly one NON-RETIRED path. A non-retired artifact is fully editable, so the plan's work can still be done; the only thing wrong is a stale string in `Scope-Paths`. This is not hypothetical: a spec moves `approved/` -> `implementing/` -> `implemented/` over its life and NOTHING rewrites a citing plan's `Scope-Paths` when it does (`aw specs set` moves the file; only `aw rename` rewrites references, and a status change is not a rename). Measured in review, 20 of the 65 corpus entries are exactly this shape, 18 of them a spec that advanced status. So a plan declaring a spec at `approved/` is silently converted from runnable into a `fail-gate` the moment that spec starts being implemented, which is precisely when the plan is most likely to matter. FIXED: the refusal now fires on `moved-terminal` and `vanished` only; `aw check` still reports all three. | review prototype: 20 `moved` entries listed with declared and resolved paths, 18 being specs whose status dir advanced; `aw rename --help` "rewriting references to it across the repo" versus no reference rewriting in the status setters |
| F-9 | MEDIUM | E-04's placement instruction | **THE STATED INSERTION POINT IS AMBIGUOUS AND THE LATER READING LEAVES AN ORPHAN PROMPT FILE.** "immediately after `plan_path = resolve_plan_path(...)` and the `attempt` record is appended" names two points about forty lines apart in `execute_item_core`, and between them `build_prompt` and `write_prompt` run, the latter WRITING a prompt file to the run's `prompts/` directory and recording a `prompt_sha256` on the attempt. A refusal after that point leaves a prompt artifact for a turn that never happened, which pollutes the run directory and misleads anyone reading it. (`build_prompt` itself is cheap: measured, no subprocess, no model call, no git, so this is a correctness and tidiness defect, not a cost one.) FIXED: E-04 now specifies before `build_prompt`, with a minimal attempt record, and a fallback instruction that must be DISCLOSED in V-04 if taken. | `execute_item_core` read in review: `resolve_plan_path` at the top, then `build_prompt`/`write_prompt`, then the `attempt` dict with `prompt` and `prompt_sha256`, then `item.setdefault("attempts", []).append(attempt)` |
| F-10 | MEDIUM | E-02's basename fallback | **THE FALLBACK CAN RESOLVE TO A DIFFERENT ARTIFACT'S FILE AND REPORT IT CONFIDENTLY.** The fallback is `rglob(basename)` anywhere under `.aw/records/`, which is only safe for a basename that is unique by construction. Two corpus entries are not: `.aw/records/research/INDEX.json` and `.aw/records/research/INDEX.md` both resolve to `.aw/records/plans/INDEX.*`, a generated index belonging to a different type. The predicate would then report `moved` with a `resolved` path that is simply the wrong file, and the recovery text would tell a human to point their scope at it. FIXED: the fallback is bounded to basenames carrying a records artifact facet; anything else is `vanished` with empty `resolved`, which is honest rather than confidently wrong. | review prototype output naming both entries and their wrong resolutions |
| F-11 | MEDIUM | E-02's API usage | **TWO OF THE THREE NAMED APIs WOULD NOT HAVE WORKED AS WRITTEN.** `artifact_naming.parse_clustered` returns a bare `re.Match` (the id6 is `m.group("id6")`), so the authored "`parse_clustered(...)`'s `id6` group" read as attribute access yields nothing and silently routes EVERY entry through the basename fallback, taking F-10's risk on all 65 rather than 13. `selectors.Resolution` exposes `(paths, kind, rejected_kind, selector)` and no `path`/`ok`/`matches`, so a reader written against the wrong member sees no hits and classifies everything `vanished`. Both failures are SILENT: the predicate still returns a plausible-looking list. FIXED: E-02 names `m.group("id6")` after a None check, `r.paths` as a list, and the `other` record-type skip, each with the measurement. | driven in review: `parse_clustered(<name>).group("id6")` -> `'qhy3i3'`; `Resolution._fields` -> `('paths','kind','rejected_kind','selector')`; `detect_artifact_type` on a nonexistent `.review.md` -> `'other'` |
| F-12 | LOW | F-3's design-constraint denominator | The authored design constraint reads "13 of 24 approved pending plans declare 16 not-yet-existing non-records paths". Re-measured in review there are 11 approved pending plans carrying `Scope-Paths` and 30 missing literal non-records entries across all pending statuses. The CONCLUSION is unaffected and in fact strengthened (more legitimate absent code paths, not fewer), but the numbers are live-artifact counts on a shared tree and must not be read as fixed. | review scan; counts by status `{to-review: 30, approved: 11, reviewed: 8}` |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the population.
2. E-02 adds the shared predicate.
3. E-03 adds the `aw check` rule on the full-sweep seam.
4. E-04 adds the item-local dispatch refusal, on `moved-terminal`/`vanished` only (F-8).
5. E-05 amends spec `25kzda` 5.7 with the narrowed detection wording and the report-three/refuse-two paragraph.
6. E-06 adds behavioral tests on both hosts, including the `moved` non-refusal negative and the mutation that defends it.
7. E-07 proves zero false positives on the real corpus and runs the suite.

## Deferred / out of scope (with reason)

- Checking non-records scope paths.
  - Carrier-Declined: F-3; a new file is a legitimate declaration and there is no signal distinguishing it from a stale one.
- Refusing at queue BUILD as well as dispatch.
  - Carrier-Declined: dispatch is the later and therefore stricter moment (a target can move mid-run, as the motivating case's timeline shows); `aw check all` covers the pre-run view.
- Refusing review-action dispatch.
  - Carrier-Declined: a review is how a human learns the plan is stale, and it performs no edit on the target.
- REFUSING on a plain `moved` (non-retired) target (F-8).
  - Carrier-Declined: not deferred work but a DELIBERATE non-goal, and the reason is that doing it would be wrong rather than merely premature. A non-retired artifact is editable, so the plan is runnable and only its declared string is stale; refusing it would spend the plan's turn budget on a path-typo. `aw check` reports it, which is the right surface for "fix this string". If a future maintainer wants the runner to refuse here too, that needs its own decision and a migration story for the 20 corpus entries of this shape, not a quiet widening of this predicate's caller.
- AUTO-CORRECTING a `moved` entry to its resolved path.
  - Carrier-Declined: already out of scope in the plan's own Scope line, and F-8 sharpens why: the resolved path is where the artifact is NOW, which may change again, and a plan whose target became `implemented` may no longer be meaningful at all. A human decides; the recovery text points at the resolved path so the decision is cheap.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/oc_runipd.py` and `agy_runipd.py` are NOT declared: the refusal lives in the shared `execute_item_core`, and the existing `run_queue` loops already continue past a `fail-gate` item. `agent_workflows/run_selection_policy.py` is not touched (F-6 explains why its predicate is not used, and review confirmed the reason from the `is_retired` side).
- Scope-Paths justification: `check_engine.py` holds the predicate and rule; `runner_shared.py` holds the dispatch refusal; the new test file holds E-06; the spec is amended by E-05.
- A RISK THIS FENCE DOES NOT REMOVE, stated because the plan edits the shared dispatch path: `execute_item_core` is the single function BOTH hosts route every execute and review turn through, so a defect here does not fail one item, it fails or wrongly refuses every item of every run. That is why the refusal is specified to fail OPEN on a predicate exception, why it is restricted to `action == "execute"`, and why E-06 requires the un-refused paths (cases 13 and 14) to be proven and not assumed. Treat any change to this function's early return structure as higher risk than its line count suggests.

## Required tests / validation

- `tests/test_scope_path_target_stale.py` (new): 16 cases over the predicate, the check rule, both hosts' dispatch, run continuation, the new-file negative, the `moved` non-refusal (the load-bearing negative, F-8), the non-artifact basename (F-10), and the no-orphan-prompt placement pin (F-9). Each case that describes a CHANGE shown failing before it.
- Real-corpus zero-false-positive scan and `aw check all` grep (E-07).
- Bare `python3 -m pytest` before and after.
- TEST-DESIGN RULE FOR THIS PLAN: a gate that refuses is only as good as its negative cases. Most of this suite asserts that something IS refused, and the cheapest wrong implementation (refuse on any stale entry) satisfies all of those. Cases 13 and 14 are the ones that fail it, so they are not optional coverage padding; if they are dropped or weakened, the suite stops defending the design decision this review made.

## Spec / documentation sync

- AMENDS spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`), declared in `- Scope-Paths:`. WHY: Section 5.7 is the spec's enumerated failure taxonomy, and each item-local refusal class there carries a detection, a response, and a stable reason. This plan adds a new item-local refusal with a new stable reason (`scope_target_stale`); leaving it out would make the shipped runner refuse on a class the governing contract does not name, which is the drift the "A PLAN MAY AMEND A SPEC" rule exists to prevent. The change is purely additive (one row, one paragraph); no existing row changes.
- No user-facing docs: the rule is discoverable through `aw check` output and its recovery text.

## Open questions

### OQ-04: Should `check.scope-path-target-stale` be `error` severity for a plain `moved` entry, when a spec status advance creates one on an innocent plan?

- Blocking: no
- Status: open
- Owner: maintainer
- RAISED IN REVIEW (F-8's second half). The plan registers the rule at `error`, which is right for `moved-terminal` and `vanished`: the plan cannot be executed as written. For a plain `moved` it is less obvious, and the exposure is measurable rather than theoretical. SEVEN pending plans today cite a spec by its STATUS DIRECTORY (`specs/approved/<f>.spec.md`, `specs/implemented/...`, `specs/implementing/...`), and THIS PLAN IS ONE OF THEM: it declares `25kzda` at `specs/approved/`. Nothing rewrites a citing plan's `Scope-Paths` when a spec advances status, so the day `25kzda` moves to `implementing/` every one of those plans acquires an `error`-severity finding for a path-typo, and if the release-gate style fail-closed treatment is ever applied to this rule family, a routine spec transition reds the tree.
- Three shapes are available and the choice is the maintainer's risk call, not derivable from the repo: (a) `error` for all three, simplest and noisiest; (b) `error` for `moved-terminal`/`vanished` and `warning` for `moved`, which matches the runner's own two-tier treatment and is this reviewer's recommendation, since severity would then mean "does this stop the work"; (c) `error` for all three PLUS teaching the spec status setters to rewrite citing `Scope-Paths` the way `aw rename` already rewrites references, which removes the cause instead of grading the symptom but is materially more work and touches every status setter.
- NOT BLOCKING, and deliberately so: the plan is executable and correct under (a) as written, 0 pending entries are stale at this HEAD so nothing reds today, and the severity of one rule is a one-line change afterwards. It is recorded rather than resolved because picking (b) or (c) changes a published rule's severity and, in (c)'s case, the behavior of the status setters, which is beyond this plan's fence.
- If unanswered before execution, execute as authored ((a), `error`) and leave this question open for a follow-up; do NOT let an unanswered non-blocking question hold the plan.
- Carrier: 9xap30

### OQ-01: Must spec `25kzda`'s list of item-local refusal classes name this refusal?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: YES, from repository evidence. Section 5.7 enumerates item-local refusal classes with stable reasons (for example "Host guarantee unavailable ... Refuse the item before session start; cascade dependents; continue independent items | `host_capability_unavailable`"), and `run_selection_policy`'s skip-reason vocabulary cites 5.7 as its naming authority. A new refusal class therefore belongs in that table; E-05 adds it and the spec is declared in `- Scope-Paths:`.

### OQ-02: Which terminal predicate classifies `moved-terminal`?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: `check_engine.is_retired`, from repository evidence (F-6). The scope target may be any records type (the motivating case is a plan; the corpus includes specs and backlog items), and `is_retired` is the one existing predicate covering all of them, while `is_in_terminal_directory` is plans-only and wrongly counts `/reusable/`.

### OQ-03: Which status does a refused item get?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: `fail-gate`, from repository evidence: it is the canonical terminal token the clean-base refusal writes for the same "refused by a pre-turn gate" shape (`TERMINAL_STATUS_ALIASES` note: "WRITERS pick per producer (`clean_base_refusal` -> `fail-gate`"), so no new status token is minted and every reader of terminal states already handles it. The distinct `scope_target_refusal` field and event name the cause.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the per-status counts of missing non-records entries and the (expected empty) list of missing literal records entries for approved pending plans, plus `tgop8e`'s executed `- Scope-Paths:` line and `ls` of its first entry.
  - Observed evidence: Verified.
    Per-status counts of missing non-records entries across pending plans:
    ```
    {'approved': 11} (11 plans declaring 17 absent non-records entries; 0 absent records entries)
    ```
    List of missing literal records entries for approved pending plans: `[]` (empty).
    Motivating case `tgop8e` executed `- Scope-Paths:` line:
    ```
    - Scope-Paths: .aw/records/plans/pending/20260910-rdyrecheck-01-qhy3i3-re-evaluate-a-stale-no-go-readiness-whose-recorded-cause-is.ipd.md, agent_workflows/ipd_readiness.py, tests/test_ipd_readiness.py
    ```
    `ls` of its first entry:
    ```
    ls: cannot access '.aw/records/plans/pending/20260910-rdyrecheck-01-qhy3i3-re-evaluate-a-stale-no-go-readiness-whose-recorded-cause-is.ipd.md': No such file or directory (exit 2)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the predicate's output on `tgop8e`'s executed text (one `moved-terminal` entry resolving to `qhy3i3`'s executed path) and on one approved pending plan that declares new code files (empty list). ALSO paste three API-shape proofs, because each was measured wrong-as-written in review (F-11): `parse_clustered(<a real plan filename>).group("id6")` returning the id6, `selectors.Resolution._fields` showing `('paths','kind','rejected_kind','selector')`, and the predicate's output for a declared missing `.aw/records/research/INDEX.json` showing classification `vanished` with `resolved` EMPTY (not `.aw/records/plans/INDEX.json`, F-10).
  - Observed evidence: Verified.
    Predicate output on `tgop8e` executed text:
    ```python
    [StaleScopePath(path='.aw/records/plans/pending/20260910-rdyrecheck-01-qhy3i3-re-evaluate-a-stale-no-go-readiness-whose-recorded-cause-is.ipd.md', classification='moved-terminal', resolved=('.aw/records/plans/executed/20260910-rdyrecheck-01-qhy3i3-re-evaluate-a-stale-no-go-readiness-whose-recorded-cause-is.ipd.md',))]
    ```
    Predicate output on approved pending plan `6h8j1r` declaring new test files:
    ```python
    []
    ```
    Three API-shape proofs:
    1. `artifact_naming.parse_clustered('20260910-rdyrecheck-01-qhy3i3-re-evaluate-a-stale-no-go-readiness-whose-recorded-cause-is.ipd.md').group("id6")`:
    ```python
    'qhy3i3'
    ```
    2. `selectors.Resolution._fields`:
    ```python
    ('paths', 'kind', 'rejected_kind', 'selector')
    ```
    3. Predicate output for declared missing `.aw/records/research/INDEX.json` (where `.aw/records/plans/INDEX.json` exists in fixture):
    ```python
    [StaleScopePath(path='.aw/records/research/INDEX.json', classification='vanished', resolved=())]
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `RULE_REGISTRY` diff and the `check_types` wiring diff; paste `check_scope_path_target_stale` output on a fixture repo (one finding) and on this repo (none, re-derived at the executing HEAD, not cited from F-4). ALSO show the rule reports a plain `moved` entry (a fixture whose target advanced to a NON-retired status dir yields a finding naming classification `moved`), which is the half of F-8 the check keeps while the runner drops it.
  - Observed evidence: Verified.
    `RULE_REGISTRY` diff:
    ```diff
    @@ -1341,6 +1341,13 @@ RULE_REGISTRY: Dict[str, RuleSpec] = {
             DET_DETERMINISTIC,
             "I-17",
         ),
    +    # planstale 6h8j1r (backlog mlc6mj): literal Scope-Paths under .aw/records/ that
    +    # no longer exist. Reports moved-terminal, moved, and vanished on pending plans.
    +    "check.scope-path-target-stale": RuleSpec(
    +        "error",
    +        ASSURANCE_REPOSITORY,
    +        DET_DETERMINISTIC,
    +        "",
    +    ),
         # from-spec traceability (spec 004 Section 8)
         "check.from-spec-dangling": RuleSpec(
             "error",
    ```
    `check_types` wiring diff:
    ```diff
    @@ -5882,6 +5889,11 @@ def check_types(
         try:
             drift.extend(check_review_dangling(repo_root))
         except Exception:
             pass
    +    try:
    +        drift.extend(check_scope_path_target_stale(repo_root))
    +    except Exception:
    +        pass
         try:
             drift.extend(check_unreferenced_specs(repo_root))
         except Exception:
    ```
    `check_scope_path_target_stale(repo_root)` on this repo (executing HEAD):
    ```python
    []
    ```
    Fixture repo findings (moved-terminal):
    ```
    rule=check.scope-path-target-stale loc=.aw/records/plans/pending/20260902-test-01-def456-some-plan.ipd.md detail=Scope-Paths entry '.aw/records/plans/pending/20260901-test-01-abc123-some-target.ipd.md' is moved-terminal (resolved: .aw/records/plans/executed/20260901-test-01-abc123-some-target.ipd.md) obs=Scope-Paths: .aw/records/plans/pending/20260901-test-01-abc123-some-target.ipd.md (moved-terminal) rec=target exists at .aw/records/plans/executed/20260901-test-01-abc123-some-target.ipd.md; retire the plan (`aw ipd set superseded|not-executed ...`) or correct its Scope-Paths to .aw/records/plans/executed/20260901-test-01-abc123-some-target.ipd.md and re-review
    ```
    Fixture repo findings (plain moved):
    ```
    rule=check.scope-path-target-stale loc=.aw/records/plans/pending/20260902-test-01-def456-some-plan.ipd.md detail=Scope-Paths entry '.aw/records/specs/approved/20260901-spec1-01-abc123-my-spec.spec.md' is moved (resolved: .aw/records/specs/implementing/20260901-spec1-01-abc123-my-spec.spec.md) obs=Scope-Paths: .aw/records/specs/approved/20260901-spec1-01-abc123-my-spec.spec.md (moved) rec=target exists at .aw/records/specs/implementing/20260901-spec1-01-abc123-my-spec.spec.md; retire the plan (`aw ipd set superseded|not-executed ...`) or correct its Scope-Paths to .aw/records/specs/implementing/20260901-spec1-01-abc123-my-spec.spec.md and re-review
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `execute_item_core` diff showing WHERE the refusal landed relative to `build_prompt`/`write_prompt` and the clean-base block, and a reproduction's `item["status"]`, `item["scope_target_refusal"]`, and the `scope-target-stale` event line. THREE ADDITIONAL PROOFS, one per review finding: (a) the refused run's `prompts/` directory listing showing NO prompt file for that item and attempt (F-9); if the fallback placement was taken instead, say so explicitly and state why, rather than letting an orphan prompt pass unmentioned; (b) a reproduction with a plain `moved` target showing `item["status"]` is NOT `fail-gate` and the launcher WAS reached (F-8); (c) the predicate-raises path showing the run proceeds and `attempt["scope_target_check_error"]` is recorded, since a gate that fails closed on its own bug would break every run through this shared function.
  - Observed evidence: Verified.
    `execute_item_core` diff showing placement before `build_prompt`/`write_prompt` and clean-base block:
    ```diff
    @@ -28164,6 +28164,69 @@ def execute_item_core(
         attempt_no = len(item.get("attempts", [])) + 1
         is_review = action == "review"

    +    # planstale 6h8j1r E-04 (backlog mlc6mj): item-local dispatch refusal on moved-terminal or
    +    # vanished literal Scope-Paths under .aw/records/. Fails open on exception. Placed before
    +    # build_prompt/write_prompt to avoid orphan prompt files on refusal (F-9).
    +    scope_target_check_error: str | None = None
    +    if action == "execute":
    +        try:
    +            from agent_workflows import check_engine as _check
    +
    +            plan_text = plan_path.read_text(encoding="utf-8")
    +            stale_entries = _check.stale_record_scope_paths(repo, plan_text)
    +            stale_refused = [
    +                e
    +                for e in stale_entries
    +                if e.classification
    +                in (
    +                    _check.SCOPE_STALE_MOVED_TERMINAL,
    +                    _check.SCOPE_STALE_VANISHED,
    +                )
    +            ]
    +            if stale_refused:
    +                reason = "; ".join(
    +                    f"{e.path} -> {e.classification}"
    +                    + (
    +                        f" (resolved: {', '.join(e.resolved)})"
    +                        if e.resolved
    +                        else " (resolved: none)"
    +                    )
    +                    for e in stale_refused
    +                )
    +                ended = utc_now()
    +                attempt = {
    +                    "number": attempt_no,
    +                    "started_at": utc_now(),
    +                    "ended_at": ended,
    +                    "action": action,
    +                    "scope_target_refused": reason,
    +                    "disposition": "fail-gate",
    +                }
    +                item.setdefault("attempts", []).append(attempt)
    +                item["status"] = "fail-gate"
    +                item["scope_target_refusal"] = reason
    +                save_state(run_dir, state)
    +                append_jsonl(
    +                    run_dir / "events.jsonl",
    +                    {
    +                        "at": ended,
    +                        "event": "scope-target-stale",
    +                        "id6": item["id6"],
    +                        "paths": [e.path for e in stale_refused],
    +                        "detail": reason,
    +                    },
    +                )
    +                print(
    +                    pal(
    +                        f"\u2717 IPD {item.get('id6', '<unknown>')} scope target refused: {reason}",
    +                        "red",
    +                    ),
    +                    file=sys.stderr,
    +                )
    +                return
    +        except Exception as ex:
    +            scope_target_check_error = str(ex)
    +
         routing = None if is_review else route_recovery_turn(run_dir, state, item, recovery)
         if is_review:
             prompt_text = build_review_prompt(item, state, run_dir, plan_path, repo)
    ```
    Reproduction 1 (moved-terminal refusal):
    ```
    item["status"]: fail-gate
    item["scope_target_refusal"]: .aw/records/plans/pending/20260901-test-01-tst001-target.ipd.md -> moved-terminal (resolved: .aw/records/plans/executed/20260901-test-01-tst001-target.ipd.md)
    event line: {"at": "2026-09-27T18:11:00+00:00", "detail": ".aw/records/plans/pending/20260901-test-01-tst001-target.ipd.md -> moved-terminal (resolved: .aw/records/plans/executed/20260901-test-01-tst001-target.ipd.md)", "event": "scope-target-stale", "id6": "wir001", "paths": [".aw/records/plans/pending/20260901-test-01-tst001-target.ipd.md"]}
    prompts dir files: [] (no orphan prompt file created)
    ```
    Three additional proofs:
    (a) No orphan prompt: `prompts/` directory contains `[]` (empty list).
    (b) Plain `moved` target non-refusal:
    ```
    item["status"] != "fail-gate": True
    launcher reached: True
    ```
    (c) Predicate-raises fail-open path:
    ```
    item["status"] != "fail-gate": True
    launcher reached: True
    attempt recorded error: Simulated boom
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the spec diff (one row, one paragraph) and the `aw specs note` output. The row's Detection column must read the NARROWED wording (retired or unresolvable), not "moved or vanished", and the paragraph must state the report-three/refuse-two asymmetry; a spec row describing a refusal the code does not perform is a failed V-05 (F-8).
  - Observed evidence: Verified.
    `git diff .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`:
    ```diff
    @@ -1391,6 +1391,7 @@ Run exit codes:
     | Unknown external outcome | Non-idempotent action may have occurred but cannot be proved | Abort run; require human reconciliation | `unknown_outcome`, AS DEFINED BY SPEC `c4gd2h` Section 0.0, which OWNS this term. Cross-reference added 2026-09-05: `c4gd2h` 0.0 names this spec's source research (`ig9bai`) explicitly and requires that any adoption REFERENCE its definition rather than restate it, because two definitions of one token violate GUIDING_PRINCIPLES P8. This row previously restated it. The shipped code follows `c4gd2h` (`runner_stop.py:1038` reserves the term for level 4's indeterminate case; `:1277-1281` names `run_recovery` as the realization and forbids reimplementation). If the external-side-effect case needs a disposition distinct from level-4 indeterminacy, `c4gd2h` requires it be given a DISTINCT NAME. |
     | Human gate | Required human receipt absent | Persist and stop | `needs_human_approval` |
     | Non-runnable state/type | Valid terminal/gated/narrative record | Skip without a session | `type_or_status_not_runnable` |
    +| Stale scope target | A literal Scope-Paths entry under .aw/records/ no longer exists and its artifact is RETIRED or unresolvable | Refuse the item before session start; cascade dependents; continue independent items | `scope_target_stale` |
     | Unverifiable prompt | No valid run contract | Refuse, or explicitly run as `ran`/`unavailable`; aggregate non-success by default or neutral only under frozen `--unverifiable-ok` | `verification_unavailable` |
     | Push attempt | Tool policy sees push-capable action | Terminate worker and abort run | `push_attempt` |
     | Host guarantee unavailable | Capability descriptor lacks current positive proof for an action requirement | Refuse the item before session start; cascade dependents; continue independent items | `host_capability_unavailable` |
    @@ -1398,6 +1399,8 @@ Run exit codes:
     | Dependency cycle | Shared predicate returns a cyclic component | Fail cycle members; cascade dependents; continue disconnected components | `dependency_cycle` |
     | Dependency not met | Required edge's target failed, stopped, was unsatisfied, or could not be met in this run | Skip without session; record and propagate root chain | `dependency_not_met` |

    +Only literal `.aw/records/` scope paths are checked because non-records paths (new code or test files) are legitimately absent before execution. The shared predicate (`check_engine.stale_record_scope_paths`) reports three classifications (`moved-terminal`, `moved`, and `vanished`), but the runner refuses only `moved-terminal` and `vanished`. A plain `moved` target (an artifact that merely changed status directory, such as an approved spec advancing to implementing) remains fully editable; refusing it would cause false refusals on runnable plans. `aw check` reports all three classifications so a maintainer can correct the declared path.
    +
     ### 5.8 Interactive and unattended parity
    ```
    `aw specs note` output:
    ```
    aw specs note: appended a history record to .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    ```
    `aw specs check`: all specs conform.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_scope_path_target_stale.py -q` passing with the count; then with the E-02..E-04 hunks temporarily reverted, the same command showing cases (1)-(4), (8)-(12) and (15) FAILING; then passing again after restoring. ALSO run the MUTATION that proves the design decision is defended: change the refusal to fire on ANY stale classification (the naive implementation) and paste case (14) FAILING; revert. A suite that still passes under that mutation has not tested F-8 and V-06 is not satisfied.
  - Observed evidence: Verified.
    Passing test run:
    ```
    ................                                                         [100%]
    16 passed in 1.09s
    ```
    With E-02..E-04 temporarily reverted:
    10 failed, 6 passed in 0.94s:
    - FAILED `test_01_predicate_moved_terminal_plan`
    - FAILED `test_02_predicate_moved_terminal_backlog`
    - FAILED `test_03_predicate_moved_non_retired_spec`
    - FAILED `test_04_predicate_vanished_records_path`
    - FAILED `test_08_predicate_legacy_spec_basename_fallback`
    - FAILED `test_09_check_scope_path_target_stale`
    - FAILED `test_10_dispatch_oc_host_refusal_moved_terminal`
    - FAILED `test_11_dispatch_agy_host_refusal_moved_terminal`
    - FAILED `test_12_dispatch_two_item_queue_run_queue`
    - FAILED `test_15_predicate_non_artifact_basename_vanished_empty_resolved`
    (Cases 1-4, 8-12, and 15 all failed as predicted; 5, 6, 7, 13, 14, 16 passed).
    Restored: 16 passed in 1.09s.

    Under MUTATION (refusing on ANY stale classification, including plain `moved`):
    ```
    FAILED tests/test_scope_path_target_stale.py::TestScopePathTargetStale::test_14_dispatch_moved_negative_reaches_launcher_and_check_reports - AssertionError: [] is not true : Launcher must be reached for plain 'moved' artifact
    1 failed, 15 passed in 0.96s
    ```
    Mutation reverted and suite restored to 16 passing.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the per-plan zero counts for ALL pending plans (every status, not only approved: F-4 was widened in review and the rule scans the whole pending lane), the corpus-wide classification histogram RE-DERIVED at the executing HEAD, the empty `scope-path-target-stale` grep of `python3 -m agent_workflows check all --agent`, and the bare `python3 -m pytest` summary line BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty). DO NOT compare the histogram against the numbers in F-5: they are live-artifact counts that moved from 58 to 65 between authoring and review in a few days. Report what you measure and note the direction of drift; a mismatch is expected and is not a failure.
  - Observed evidence: Verified.
    Per-plan zero counts for ALL pending plans (every status):
    ```
    Total pending plans scanned: 11
    Plans by status: {'approved': 11}
    Stale findings across all pending plans: 0
    ```
    Corpus-wide classification histogram re-derived at executing HEAD:
    ```
    Total plans scanned across whole corpus: 836
    Classification histogram:
      moved: 18
      moved-terminal: 46
      vanished: 6
    Findings by directory:
      executed: 64
      not-executed: 2
      superseded: 4
    Total plans with findings: 46
    Total stale findings: 70
    (Drift observed: 58 at authoring -> 65 at review -> 70 at executing HEAD, all in terminal/superseded plans)
    ```
    Empty grep of `python3 -m agent_workflows check all --agent`:
    ```
    Matches count: 0 (exit 1 from grep)
    ```
    Bare `python3 -m pytest` summary line BEFORE and AFTER:
    BEFORE: `2797 passed, 2 skipped, 3 warnings in 315.42s`
    AFTER: `2813 passed, 2 skipped, 3 warnings in 136.95s (0:02:16)`
    After-minus-before failing node-ID set: empty (`set()`). Delta is exactly the 16 newly added passing tests.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. One shared predicate that flags a plan whose literal `.aw/records/` scope target no longer exists, classified `moved-terminal`/`moved`/`vanished`; an `aw check all` rule `check.scope-path-target-stale` over pending plans reporting ALL THREE; an item-local dispatch refusal (`fail-gate`, no agent turn, run continues) for execute actions on `moved-terminal` and `vanished` ONLY; and a one-row amendment to spec `25kzda` Section 5.7. Non-records paths are never checked, because new files are legitimately absent. This graduates backlog `mlc6mj` and inherits its `- Blocks-Release: next`.

THE ONE JUDGEMENT CALL WORTH A HUMAN'S ATTENTION, changed in review (F-8). The authored plan refused on ANY stale classification. That would have refused plans that are perfectly runnable: `moved` means the target resolves to a NON-RETIRED artifact, which is still editable, so only the declared string is stale. It is not a corner case. A spec advances `approved` -> `implementing` -> `implemented` over its life, NOTHING rewrites a citing plan's `Scope-Paths` when it does, 20 of the 65 stale entries in the corpus are exactly this, and 7 PENDING PLANS TODAY cite a spec by status directory (this plan among them, declaring `25kzda` at `specs/approved/`). Under the authored rule, each becomes a `fail-gate` the day its spec starts being implemented. So the refusal was narrowed and the reporting was not: `aw check` tells a human to fix the string, the runner spends no turn refusing over one. If you disagree and want the strict version, that is a deliberate choice to make here, not something to discover from a refused queue.

WHAT THIS TOUCHES, SO THE RISK IS NOT UNDERSTATED. `execute_item_core` is the single function through which BOTH hosts run every execute and review turn. A defect in this refusal does not cost one item; it can refuse or break every item of every run. That is why the gate fails OPEN on a predicate exception, is restricted to `action == "execute"`, and is covered by negative tests (a plain `moved` plan must still reach its launcher; the predicate raising must not refuse). Weigh it as a change to the runner's hot path, not as a small check.

ONE NON-BLOCKING QUESTION IS LEFT OPEN FOR YOU (OQ-04): whether a plain `moved` should be `error` severity in `aw check`, given that a routine spec status transition would then create an `error` finding on seven innocent pending plans. The plan is executable as authored (`error` for all three) and nothing is stale today, so this does not hold it; the reviewer's recommendation is `warning` for `moved` so severity tracks "does this stop the work".

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/check_engine.py` (new predicate, registry entry, check function, full-sweep wiring), `agent_workflows/runner_shared.py` (`execute_item_core` refusal only), the new `tests/test_scope_path_target_stale.py`, and spec `25kzda` Section 5.7. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New tests must be shown FAILING against the pre-change code, and E-07's corpus scan must be pasted, not summarized.

RE-DERIVE, DO NOT CITE, EVERY COUNT. The population numbers in this plan are live-artifact counts on a shared tree and they have already drifted once: F-5's corpus total read 58 at authoring and 65 in review, days apart, and F-3's "13 of 24 approved plans" re-measured as 11 approved plans with 30 missing non-records entries across all pending statuses. The CONCLUSIONS held both times, which is the point: E-01 and E-07 must measure at the executing HEAD and report what they see, and a number that differs from this plan's prose is expected rather than a failed check. What must hold is the PROPERTY (no missing literal records entry on a pending plan), never a specific integer.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `mlc6mj` `done` with `--evidence` citing the executed plan; its release gate is preserved by the `From-Backlog` handoff.
