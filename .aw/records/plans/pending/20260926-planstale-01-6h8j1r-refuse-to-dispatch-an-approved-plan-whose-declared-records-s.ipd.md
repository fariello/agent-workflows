# IPD: Refuse to dispatch an approved plan whose declared records scope path has moved or vanished

- Date: 2026-09-26
- Kind: child
- Concern: NOTHING VALIDATES THAT A PLAN'S DECLARED `Scope-Paths` TARGET STILL EXISTS BEFORE THE RUNNER SPENDS A TURN ON IT. Motivating case (backlog `mlc6mj`): plan `tgop8e`, approved 2026-09-12, declared `.aw/records/plans/pending/20260910-rdyrecheck-01-qhy3i3-...ipd.md` and existed to edit two success criteria inside `qhy3i3`; `qhy3i3` was finalized to `executed/` on 2026-09-21 (`fe120181 lifecycle(qhy3i3): finalize qhy3i3 -> executed`), and on 2026-09-23 the runner still dispatched `tgop8e` with queue action `execute`, for work that could not legally be done (AGENTS.md forbids adding commits to a plan already in `executed/`). Measured at HEAD `ea206c49`: `tgop8e`'s executed copy still declares that pending path, which does not exist. DESIGN CONSTRAINT, measured: of 24 approved pending plans, 13 legitimately declare 16 NOT-YET-EXISTING code/test paths (new files), so existence of an arbitrary scope path is NOT a valid gate; 0 approved pending plans declare a missing LITERAL path under `.aw/records/` (the one missing `.aw/records/` entry, `.aw/records/plans/pending/**` in `vtkfq8`, is a glob). A records path names an artifact that must already exist to be edited, so it is the only class that can be checked without false positives.
- Scope: IN: (a) one shared pure-ish predicate `check_engine.stale_record_scope_paths(repo_root, plan_text)` that returns, for each LITERAL (no `*`, `?`, `[`) `Scope-Paths` entry under `.aw/records/` that does not exist, a classification `moved-terminal` (the artifact's id6 now resolves to exactly one artifact that is retired), `moved` (resolves to exactly one non-retired artifact at a different path), or `vanished` (resolves to none); paths outside `.aw/records/`, globs, directory entries that exist, and grandfathered plans are ignored; (b) a new `aw check` rule `check.scope-path-target-stale` over approved (and reviewed/to-review) PENDING plans, riding the `aw check all` full-sweep seam beside `check.from-spec-dangling`; (c) a dispatch-time refusal in `runner_shared.execute_item_core` for an `execute` action, before any clean-base check, lane allocation, begin, or agent turn, that marks ONLY that item `fail-gate` with a recorded `scope_target_refusal` reason naming each stale path and its classification, emits a `scope-target-stale` event, and returns so the run continues (the item-local-refusal precedent of `clean_base_refusal`); (d) amend spec `25kzda` Section 5.7's failure taxonomy with one row for this refusal; (e) behavioral tests and a real-corpus zero-false-positive scan. OUT: checking non-records paths (new files are legitimate); checking glob entries; auto-rewriting a plan's scope to the moved path (a human decides whether the plan is still meaningful); review-action dispatch (a review of a stale plan is how a human finds out; the `aw check` rule covers it); retiring `tgop8e`-style plans already in terminal directories (they are history).
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/runner_shared.py, tests/test_scope_path_target_stale.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: mlc6mj
- Blocks-Release: next
- Set: planstale
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 6h8j1r

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog mlc6mj. Design constraint measured at HEAD ea206c49 (16 legitimate not-yet-existing code/test paths across 13 approved pending plans; 0 missing literal .aw/records paths), so only literal .aw/records entries are checked. Classification prototyped against every plan's Scope-Paths corpus-wide: 58 missing literal records entries, all in executed/superseded plans, 40 moved-terminal and 18 moved, 0 vanished.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Stop the runner spending an agent turn on an approved plan whose declared records target has moved (typically to a terminal directory) or vanished, and let `aw check all` flag the same condition before a run starts, with one shared predicate so the two can never disagree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline

- [ ] E-01 RE-MEASURE THE POPULATION at the executing HEAD with a throwaway script (not committed) that parses every `.aw/records/plans/pending/*.ipd.md`'s `- Scope-Paths:` with `ipd_schema.parse_scope_paths` and reports, per `- Status:`: (1) the count of missing non-glob entries OUTSIDE `.aw/records/`, (2) the list of missing non-glob entries UNDER `.aw/records/`. Also confirm `tgop8e`'s executed copy still declares the missing `qhy3i3` pending path. Paste both.
  - Depends on: none
  - Expected outcome: (1) non-zero for approved plans (new-file declarations, about 16 at authoring); (2) empty for approved pending plans. If (2) is non-empty, list each and say whether it is a genuine stale target (that is a finding to report, not a reason to stop).
  - Execution state: pending

### Task group 2: the predicate and the check

- [ ] E-02 ADD `check_engine.stale_record_scope_paths(repo_root, plan_text) -> list[StaleScopePath]` with a small `NamedTuple` `StaleScopePath(path, classification, resolved)` and three module constants `SCOPE_STALE_MOVED_TERMINAL = "moved-terminal"`, `SCOPE_STALE_MOVED = "moved"`, `SCOPE_STALE_VANISHED = "vanished"`. Algorithm: read the `- Scope-Paths:` value from the plan's metadata (use `ipd_schema.parse_scope_paths`; a grandfathered or unparseable value yields `[]`); for each entry, skip if it contains `*`, `?` or `[`, skip if it does not start with `.aw/records/`, skip if `(repo_root / entry).exists()`; otherwise derive the id6 from the filename's clustered identity slot (`artifact_naming.parse_clustered(Path(entry).name)`'s `id6` group) and the type from `status_set.detect_artifact_type(repo_root / entry, repo_root)`; resolve with `selectors.resolve(repo_root, type, id6, allow=frozenset({selectors.MATCH_ID6}))` (exact `- Id:` only). If that yields nothing (a legacy spec name has no id6 slot, measured 19 such entries corpus-wide), fall back to the SAME basename anywhere under `.aw/records/` (`rglob(name)`), which is exact and cheap because it runs only for already-missing entries. Exactly one hit: `moved-terminal` when `check_engine.is_retired(hit)` (the existing retired-path/status predicate: `executed`, `superseded`, `not-executed`, `parked`, `done`, `shipped` segments or those statuses plus `implemented`), else `moved`. Zero hits: `vanished`. More than one hit: `moved` with every hit listed in `resolved` (ambiguity is still "not where declared"). Do NOT use `run_selection_policy.is_in_terminal_directory` here: it counts `/reusable/` as terminal (see `ipd_lifecycle.plan_already_finalized`'s docstring) and misses backlog `done/` and spec `implemented/`; `is_retired` covers every records type. Pure except for filesystem reads; no git, no subprocess.
  - Depends on: E-01
  - Expected outcome: on `tgop8e`'s executed text the predicate returns one `moved-terminal` entry resolving to `qhy3i3`'s executed path; on every approved pending plan it returns `[]`.
  - Execution state: pending

- [ ] E-03 REGISTER AND WIRE `check.scope-path-target-stale`. Add `"check.scope-path-target-stale": RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")` to `RULE_REGISTRY` with a comment (invariant `""`: no catalog invariant in spec `pqsx96` covers scope-target freshness, and inventing one is out of scope; `error` because a stale target makes the plan unexecutable as written). Add `check_scope_path_target_stale(repo_root)` iterating `_iter_plan_ipds(repo_root)`, restricted to paths whose parent directory is `pending` (terminal plans are history and would be 58 permanent findings), calling E-02's predicate, and emitting one `enrich_drift(_core.Drift(str(path), rule, detail), observed=..., required=..., recovery=...)` per stale entry, whose recovery names the resolved path and says to either retire the plan (`aw ipd set superseded|not-executed ...`) or correct its `Scope-Paths` and re-review. Wire it into `check_types`' `collisions` full-sweep block with its OWN `try/except Exception: pass`, matching its neighbours.
  - Depends on: E-02
  - Expected outcome: `aw check all` on this repo reports zero `check.scope-path-target-stale` findings; on a fixture repo holding a pending approved plan whose declared records target moved to `executed/`, it reports exactly one.
  - Execution state: pending

### Task group 3: the dispatch refusal

- [ ] E-04 REFUSE AT DISPATCH, ITEM-LOCALLY. In `runner_shared.execute_item_core`, immediately after `plan_path = resolve_plan_path(...)` and the `attempt` record is appended, and BEFORE the `if self_finalize and not is_review:` clean-base block, when `action == "execute"`: read `plan_path`'s text and call E-02's predicate. If it returns any entry: set `attempt["ended_at"]`, `attempt["scope_target_refused"] = reason`, `attempt["disposition"] = "fail-gate"`, `item["status"] = "fail-gate"`, `item["scope_target_refusal"] = reason` (reason lists each `path -> classification (resolved: ...)`), `save_state`, append a `scope-target-stale` event to `events.jsonl` with `id6`, `paths`, and `detail`, print one red line naming the item and reason, and `return`. That is exactly the shape of the existing `clean-base-refused` arm, so the run continues with independent items and `cascade_dependency_blocked` marks dependents `fail-depend` on the next loop iteration with no new code. A predicate exception must NOT refuse (fail open to today's behavior, record `attempt["scope_target_check_error"]`), because this gate adds protection and must never block a run on its own bug. Reuse `fail-gate` (already in `TERMINAL_STATES_CANONICAL`); do not mint a new status token.
  - Depends on: E-02
  - Expected outcome: a queued approved plan with a moved-terminal records target ends `fail-gate` with `scope_target_refusal` set, no agent turn is spawned, no lane is allocated, and the next independent item still runs.
  - Execution state: pending

### Task group 4: spec, proof

- [ ] E-05 AMEND SPEC `25kzda` Section 5.7 "Failure taxonomy": add one row, placed after "Non-runnable state/type", reading `| Stale scope target | A literal Scope-Paths entry under .aw/records/ no longer exists and its artifact moved or vanished | Refuse the item before session start; cascade dependents; continue independent items | scope_target_stale |`, and one short paragraph below the table explaining why only literal records paths are checked (new code/test files are legitimately absent) and naming the shared predicate. Record the amendment with `aw specs note <spec> --message "..."` naming this plan's id6. The spec stays `approved`.
  - Depends on: E-04
  - Expected outcome: the table carries the row; the spec's history carries the note; `aw specs check` reports nothing new for the spec.
  - Execution state: pending

- [ ] E-06 ADD `tests/test_scope_path_target_stale.py` (behavioral only; no source-text or AST assertions). Predicate cases on a temp repo: (1) a declared pending plan path whose file now sits in `executed/` -> `moved-terminal`; (2) a declared backlog `open/` path now in `done/` -> `moved-terminal`; (3) a declared spec path now in `to-review/` (non-retired) -> `moved`; (4) a declared records path with no artifact anywhere -> `vanished`; (5) a missing NON-records path (`agent_workflows/new_module.py`, `tests/test_new.py`) -> ignored; (6) a glob (`.aw/records/plans/pending/**`) and an existing directory entry -> ignored; (7) a grandfathered `Scope-Paths` -> `[]`; (8) a legacy spec name with no id6 slot resolved via the basename fallback. `aw check` cases: (9) `check_scope_path_target_stale` reports one finding for a pending plan with case (1)'s scope and none for the same text under `executed/`. Dispatch cases, reusing `tests.test_oc_runipd._init_repo_with_conforming_plan` and `support.declare_execution_role(self)`: (10) OC host: a conforming approved plan whose `Scope-Paths` names a moved-terminal records path, run through `oc_runipd.execute_item` with `run_opencode` patched to a launcher that FAILS the test if called -> `item["status"] == "fail-gate"`, `scope_target_refusal` names the path, no `worktree` key on the attempt, a `scope-target-stale` event exists; (11) the same on the AGY host (`agy_runipd.execute_item`, `run_agy_turn` patched to fail); (12) a two-item queue through `oc_runipd.run_queue` where item 1 is stale and item 2 is independent and clean: item 1 `fail-gate`, item 2 reaches its launcher; (13) a plan whose only missing path is a new code file is NOT refused.
  - Depends on: E-03, E-04
  - Expected outcome: all pass; (1)-(4), (8)-(12) fail before the change.
  - Execution state: pending

- [ ] E-07 PROVE ZERO FALSE POSITIVES ON THE REAL CORPUS and run the bare suite. Run the E-02 predicate over every `.aw/records/plans/pending/*.ipd.md` whose status is `approved` and paste the per-plan count (must be all zero), then over every plan in every bucket and paste the classification histogram (authoring measurement: 58 entries, all in terminal-directory plans, 40 moved-terminal, 18 moved, 0 vanished). Run `python3 -m agent_workflows check all --agent` and paste the grep for `scope-path-target-stale` (must be empty). Run the bare `python3 -m pytest` before and after.
  - Depends on: E-06
  - Expected outcome: zero findings on approved pending plans; zero rule hits from `aw check all`; after-minus-before failing node set empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Item-local refusal precedent: `execute_item_core`'s clean-base arm writes `attempt["clean_base_refused"]`, `attempt["disposition"] = "fail-gate"`, `item["status"] = "fail-gate"`, `item["clean_base_refusal"]`, saves state, appends a `clean-base-refused` event, prints, and returns; the drivers' `run_queue` loops then continue and `cascade_dependency_blocked` marks dependents. Spec `25kzda` Section 5.7 states the same "Refuse the item before session start; cascade dependents; continue independent items" response for `host_capability_unavailable`.
- Dependency re-check at dispatch lives in each driver's `run_queue` (`dependency_status(item, state)` in the selection loop) and in `runner_shared.cascade_dependency_blocked`; this plan's refusal sits in the shared `execute_item_core` so both hosts get it once.
- Cross-tree reference rules ride the `aw check all` full-sweep seam in `check_engine.check_types` (`check_from_spec_dangling`, `releases.check_graduated_to`, `check_review_dangling`), each in its own `try/except`, iterating `_iter_plan_ipds`.
- Retired predicate: `check_engine.is_retired` (path segments `archive`, `executed`, `superseded`, `not-executed`, `parked`, `done`, `shipped`, or status in that set plus `implemented`). `run_selection_policy.is_in_terminal_directory` is plans-only and counts `/reusable/` (warned against in `ipd_lifecycle.plan_already_finalized`).
- Exact id6 resolution: `selectors.resolve(..., allow=frozenset({selectors.MATCH_ID6}))`; without `allow`, a substring filename match can win.
- Test policy (maintainer ruling 2026-09-26): behavior tests only. Suites run BARE; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `ea206c49` (2026-09-26).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | runner dispatch | No check between queue selection and agent turn reads a plan's `Scope-Paths` targets. | `execute_item_core` goes from `resolve_plan_path` to prompt build, clean-base, lane allocation, begin, spawn; no scope-target read |
| F-2 | HIGH | motivating case | `tgop8e` declares a pending path for `qhy3i3`, which moved to `executed/` nine days after approval. | `ls` of the declared path: absent; `git log --all -1 -- <declared path>` -> `fe120181`; executed copy's `- Scope-Paths:` still names it |
| F-3 | HIGH (design constraint) | approved pending plans | 13 of 24 approved pending plans declare 16 not-yet-existing non-records paths (new code/test files). A generic existence check would refuse them all. | authoring scan with `ipd_schema.parse_scope_paths` |
| F-4 | INFO | approved pending plans | 0 missing literal `.aw/records/` entries; the only missing records entry is the glob `.aw/records/plans/pending/**` (`vtkfq8`). | same scan |
| F-5 | INFO | whole corpus | 58 missing literal records entries, all in `executed/`/`superseded/` plans; classification prototype: 40 moved-terminal, 18 moved, 0 vanished (19 of them legacy spec names without an id6 slot, resolved by basename). | prototype over `.aw/records/plans/*/*.ipd.md` |
| F-6 | INFO | `run_selection_policy.is_in_terminal_directory` | Plans-only segment list including `/reusable/`; returns False for backlog `done/` and spec `implemented/`. | `TERMINAL_DIRECTORY_SEGMENTS` literal; direct call returned False for both |
| F-7 | INFO | spec `25kzda` Section 5.7 | The failure taxonomy enumerates item-local refusal classes with stable reasons; a new refusal class belongs there. | table rows "Host guarantee unavailable", "Non-runnable state/type" |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the population.
2. E-02 adds the shared predicate.
3. E-03 adds the `aw check` rule on the full-sweep seam.
4. E-04 adds the item-local dispatch refusal.
5. E-05 amends spec `25kzda` 5.7.
6. E-06 adds behavioral tests on both hosts.
7. E-07 proves zero false positives on the real corpus and runs the suite.

## Deferred / out of scope (with reason)

- Checking non-records scope paths.
  - Carrier-Declined: F-3; a new file is a legitimate declaration and there is no signal distinguishing it from a stale one.
- Refusing at queue BUILD as well as dispatch.
  - Carrier-Declined: dispatch is the later and therefore stricter moment (a target can move mid-run, as the motivating case's timeline shows); `aw check all` covers the pre-run view.
- Refusing review-action dispatch.
  - Carrier-Declined: a review is how a human learns the plan is stale, and it performs no edit on the target.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/oc_runipd.py` and `agy_runipd.py` are NOT declared: the refusal lives in the shared `execute_item_core`, and the existing `run_queue` loops already continue past a `fail-gate` item. `agent_workflows/run_selection_policy.py` is not touched (F-6 explains why its predicate is not used).
- Scope-Paths justification: `check_engine.py` holds the predicate and rule; `runner_shared.py` holds the dispatch refusal; the new test file holds E-06; the spec is amended by E-05.

## Required tests / validation

- `tests/test_scope_path_target_stale.py` (new): 13 cases over the predicate, the check rule, both hosts' dispatch, run continuation, and the new-file negative. Shown failing before the change.
- Real-corpus zero-false-positive scan and `aw check all` grep (E-07).
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- AMENDS spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`), declared in `- Scope-Paths:`. WHY: Section 5.7 is the spec's enumerated failure taxonomy, and each item-local refusal class there carries a detection, a response, and a stable reason. This plan adds a new item-local refusal with a new stable reason (`scope_target_stale`); leaving it out would make the shipped runner refuse on a class the governing contract does not name, which is the drift the "A PLAN MAY AMEND A SPEC" rule exists to prevent. The change is purely additive (one row, one paragraph); no existing row changes.
- No user-facing docs: the rule is discoverable through `aw check` output and its recovery text.

## Open questions

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

- [ ] V-01 validates E-01
  - Required evidence: paste the per-status counts of missing non-records entries and the (expected empty) list of missing literal records entries for approved pending plans, plus `tgop8e`'s executed `- Scope-Paths:` line and `ls` of its first entry.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the predicate's output on `tgop8e`'s executed text (one `moved-terminal` entry resolving to `qhy3i3`'s executed path) and on one approved pending plan that declares new code files (empty list).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `RULE_REGISTRY` diff and the `check_types` wiring diff; paste `check_scope_path_target_stale` output on a fixture repo (one finding) and on this repo (none).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `execute_item_core` diff showing the refusal placed before the clean-base block, and a reproduction's `item["status"]`, `item["scope_target_refusal"]`, and the `scope-target-stale` event line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the spec diff (one row, one paragraph) and the `aw specs note` output.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_scope_path_target_stale.py -q` passing with the count; then with the E-02..E-04 hunks temporarily reverted, the same command showing cases (1)-(4) and (8)-(12) FAILING; then passing again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the per-plan zero counts for approved pending plans, the corpus-wide classification histogram, the empty `scope-path-target-stale` grep of `python3 -m agent_workflows check all --agent`, and the bare `python3 -m pytest` summary line BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. One shared predicate that flags a plan whose literal `.aw/records/` scope target no longer exists, classified `moved-terminal`/`moved`/`vanished`; an `aw check all` rule `check.scope-path-target-stale` over pending plans; an item-local dispatch refusal (`fail-gate`, no agent turn, run continues) for execute actions; and a one-row amendment to spec `25kzda` Section 5.7. Non-records paths are never checked, because new files are legitimately absent. This graduates backlog `mlc6mj` and inherits its `- Blocks-Release: next`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/check_engine.py` (new predicate, registry entry, check function, full-sweep wiring), `agent_workflows/runner_shared.py` (`execute_item_core` refusal only), the new `tests/test_scope_path_target_stale.py`, and spec `25kzda` Section 5.7. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New tests must be shown FAILING against the pre-change code, and E-07's corpus scan must be pasted, not summarized.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `mlc6mj` `done` with `--evidence` citing the executed plan; its release gate is preserved by the `From-Backlog` handoff.
