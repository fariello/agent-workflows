# IPD: Make resolve_plan_path fail closed on a non-plan path, a mentioned id6, and lane or baseline copies

- Date: 2026-09-26
- Kind: child
- Concern: `runner_shared.resolve_plan_path(repo, configured, id6)` IS THE SHARED "LOCATE THIS IPD" AUTHORITY (28 real call sites, ALL of them in `runner_shared`; counted by AST at review, correcting the authored "29 ... one each in `oc_runipd` and `agy_runipd`" - both hosts only RE-EXPORT the symbol (`resolve_plan_path as resolve_plan_path`) and neither calls it, which the plan's own Scope check already says) AND IT FAILS OPEN IN THREE MEASURED WAYS. (1) Its `configured` branch returns ANY existing file: measured at HEAD `ea206c49`, `resolve_plan_path(repo, ".aw/records/plans/README.md", "zzzzzz")` returns the README and `resolve_plan_path(repo, <4sd62s .spec.md>, "4sd62s")` returns the spec. That is reachable in production: a scratch repo holding only a spec, run as `aw oc run start <spec path> --prepare-only --unattended`, produced a queue item with `configured_file` set to the spec path (the file-candidate branch of `runner_shared.expand_selectors` accepts it through `parse_plan_file`); the derived action follows the spec's own `- Status:`, measured `review` for a `to-review` spec and `execute` for an `approved` one, and `resolve_plan_path` is reached either way because `execute_item_core` calls it BEFORE it branches on `is_review`. (2) Its id6 branch calls `selectors.resolve_selectors(repo, "plans", [id6])`, whose precedence ends in a FILENAME SUBSTRING match, so a SPEC id6 resolves to a plan that merely mentions it: `resolve_plan_path(repo, "", "77tr3o")` returns `executed/20260906-orchretire-00-84j8d7-...-adopt-spec-77tr3o.ipd.md` (`selectors.resolve` reports kind `substring`). (3) Its last-resort glob roots include `repo` itself, so `rglob("*-<id6>-*.ipd.md")` walks `.aw/worktrees/*` and `.aw/state/suite-baselines/*`: `resolve_plan_path(repo, "", "25kzda")` raises `Ambiguous IPD` over a set of paths dominated by lane and baseline copies, and a miss costs roughly half a second against about 0.004s for the plans trees alone. THE PATH COUNT IS A LIVE POPULATION, NOT A BAR: authored as 24 (22 lane or baseline, 2 mention-only) and re-measured at review in a lane checkout as 3, ALL lane or baseline, because the number depends on how many worktrees and suite baselines exist at that moment. E-01 re-derives it; the REQUIRED PROPERTY is that the set is non-empty and contains at least one path that is either under `.aw/worktrees/`/`.aw/state/` or does not claim the id6, which is what makes the pre-change behavior wrong. Re-measured timing at review: 0.46s for the `25kzda` miss.
- Scope: IN: (a) restrict the id6 branch to an exact `- Id:` match (`selectors.resolve(repo, "plans", id6, allow=frozenset({selectors.MATCH_ID6}))`); (b) make the `configured` branch accept a file only when it is a plan by the same membership rule `runner_shared.discover_plans` uses (under the repo's `.aw/records/plans` or `.agents/plans` tree, not an index file `README.md`/`INDEX.md`/`STATUS.md`) AND `status_set.detect_artifact_type` reports `plans`, else raise `DriverError` naming the detected type; (c) limit the glob fallback's roots to the two plans trees and keep only hits that CLAIM the id6 (`selectors.id6_ownership` in `selectors.CLAIMING_OWNERSHIPS`); (d) record the supersession in `tests/test_runner_shared.py`'s `SUPERSEDED_SINCE_MOVE`; (e) behavioral tests for each measured case plus the existing lane and executed-transition behaviors. OUT: `runner_shared.expand_selectors`' file-candidate branch admitting a non-plan path into the manifest (with this fix the item is refused loudly at dispatch; refusing earlier is spec `z7nbn1`'s typed-dispatch work); `selectors.resolve`'s precedence (a shared contract for every verb); editing spec `z7nbn1` (under maintainer review); any new source-pinning test (maintainer ruling 2026-09-26).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_resolve_plan_path_typed.py, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: m10mrs
- Blocks-Release: next
- Set: planpathtype
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: mxzogk

## Workflow history

- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 all FIXED; review record `.aw/records/reviews/20260926-planpathtype-01-mxzogk-make-resolve-plan-path-fail-closed-on-a-non-plan-path-a-ment.review.md`. All three fail-open modes and F-1..F-8 re-verified at lane HEAD ec5c6c12 and every one reproduced; the three code changes stand as authored, and the narrowing was verified not to break the executed-transition case, the lane case, `.agents/plans`, an absolute configured path, or any discovered plan (836 measured, 0 non-`.ipd.md`, 0 non-`declared`). CORRECTED THE EVIDENCE: E-06 case (6)'s fixture was unreachable by the glob it targeted and would have passed vacuously (F-9); case (5) bundled an already-passing guard with the real fail-before (F-10); F-2 named `execute` for a `to-review` spec that actually yields `review`, so the dispatch test now covers both actions (F-11); the 29-call-site census was a grep artifact contradicting the plan's own scope note, 28 by AST all in `runner_shared` (F-12); three drifting live counts became re-derived properties (F-13). Split the dispatch case into E-07 (different harness). `aw ipd lint --phase review-finalize` conforming; baseline `pytest tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py` 316 passed.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog m10mrs. All three fail-open modes re-measured at HEAD ea206c49; a production path from a spec-path selector to a plan-shaped queue item reproduced on a scratch repo; detect_artifact_type measured to report `plans` for the plans README, so the configured-branch check is strengthened with discover_plans' membership rule; the strict fingerprint test is measured ABSENT since 19313eed, so the SUPERSEDED_SINCE_MOVE entry is a record, not a gate.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `resolve_plan_path` return an IPD or raise: never a README, a spec, a plan that only mentions the id6, or a lane or baseline copy, and stop a miss from walking the whole checkout.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce and audit callers

- [ ] E-01 REPRODUCE AND AUDIT at the executing HEAD. (1) Paste the results of `resolve_plan_path(repo, ".aw/records/plans/README.md", "zzzzzz")`, `resolve_plan_path(repo, <the 4sd62s .spec.md path>, "4sd62s")`, `resolve_plan_path(repo, "", "77tr3o")`, and `resolve_plan_path(repo, "", "25kzda")` (the exception text's path count, and how many contain `/.aw/worktrees/` or `/.aw/state/`), each timed. (2) Enumerate every `resolve_plan_path` call site BY AST rather than by grep (a text grep counts the `def`, the two host re-export lines, and prose mentions; measured at review, grep says 29/1/0 across the three modules while AST says 28/0/0) and, for each, paste the ORIGIN of its `configured` argument. At review there were 28, all in `runner_shared`, and every origin was one of: `item["configured_file"]` (copied from the manifest entry's `file` when the queue is built), a manifest entry's `.get("file", "")`, a lane record's `configured_file`, or the literal `""`. The manifest `file` is `rec.rel_path` from `discover_plans` or from `expand_selectors`' file-candidate branch. Record that NO call site deliberately passes a non-plan: `refuse_unrunnable_selected_types` refuses a non-`ipd` `--type` selection before the queue is built, and `resolve_selected_artifact_paths` routes specs through `discover_specs`. The one non-deliberate origin is the file-candidate branch (measured: a spec path selector yields `configured_file` = the spec). (3) On a scratch repo holding only a spec, run `python3 -m agent_workflows oc run start <spec path> --prepare-only --unattended` with `AW_HOME` isolated, and paste the queue item's `configured_file` and `action` from the run's `state.json`. DO THIS FOR BOTH a `to-review` and an `approved` spec, because the derived action differs (`review` and `execute` respectively, re-measured at review) and the plan must not claim one when it measured the other.
  - Depends on: none
  - Expected outcome: all four fail-open results reproduce; every call-site origin is accounted for; the scratch runs queue the spec with `configured_file` set to the `.spec.md` path, action `review` for a `to-review` spec and `execute` for an `approved` one.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-02 RESTRICT THE ID6 BRANCH to an exact declaration. Replace `selectors.resolve_selectors(repo, "plans", [id6])` with `selectors.resolve(repo, "plans", id6, allow=frozenset({selectors.MATCH_ID6}))` and accept only `len(res.paths) == 1 and res.paths[0].is_file()`. A match through any other kind (substring, stem, setid, status) then comes back with `rejected_kind` set and no paths, and falls through exactly as a no-match does today. Keep the surrounding `try/except Exception: pass` unchanged.
  - Depends on: E-01
  - Expected outcome: `resolve_plan_path(repo, "", "77tr3o")` no longer returns the orchretire plan; a plan declaring `- Id: <id6>` still resolves from `pending/` and, after a move, from `executed/`.
  - Execution state: pending

- [ ] E-03 TYPE-CHECK THE CONFIGURED BRANCH. When `direct = (repo / configured).resolve()` is a file, accept it only if (i) it sits under `(repo / ".aw" / "records" / "plans").resolve()` or `(repo / ".agents" / "plans").resolve()`, (ii) its name is not `README.md`, `INDEX.md` or `STATUS.md` (the skip set `discover_plans` uses), and (iii) `status_set.detect_artifact_type(direct, repo)` returns `"plans"`. Otherwise raise `DriverError(f"Refusing {configured!r} for IPD {id6}: it is {what}, not an IPD plan")`, where `what` is `a <type>` from `detect_artifact_type`, `a plans index file`, or `outside the plans trees`. WHY ALL THREE AND NOT (iii) ALONE, measured at authoring: `detect_artifact_type` returns `plans` for `.aw/records/plans/README.md` (location rule) and for a root `AGENTS.md` (content fallback on `- Kind: child`), so a type check alone would still pass the README, which is one of the measured fail-open cases. Import `status_set` lazily inside the function, as `selectors` already is. A file that does not exist still falls through to the glob exactly as today (the executed-transition case needs that).
  - Depends on: E-01
  - Expected outcome: the README and spec inputs raise `DriverError` naming `a plans index file` and `a specs` (or the detected type's wording) respectively; a real pending plan path is still returned.
  - Execution state: pending

- [ ] E-04 NARROW THE GLOB FALLBACK. Drop `repo` from `roots`, leaving `repo / ".aw" / "records" / "plans"` and `repo / ".agents" / "plans"`, and keep a hit only if `selectors.id6_ownership(path, id6) in selectors.CLAIMING_OWNERSHIPS` (declared, or the id6 sits in the filename identity slot with no foreign `- Id:`). That keeps the fallback's one legitimate job, finding a plan whose declaration the bounded header read cannot see or a legacy slot-only plan, while dropping plans that merely mention the id6 in the slug. Keep both existing error messages (`Cannot locate IPD ...` and `Ambiguous IPD ...`) byte-identical, since `tests/test_agy_runipd_cli.py::AgyVerificationAbsenceTests::test_plan_path_resolution` asserts the first.
  - Depends on: E-02
  - Expected outcome: `resolve_plan_path(repo, "", "25kzda")` raises `Cannot locate IPD 25kzda` (no plan declares it) instead of `Ambiguous` over the lane/baseline set E-01 measured, whatever its size at execution, and a miss takes milliseconds rather than tenths of a second. Assert the MESSAGE and an order-of-magnitude timing improvement, never the path count.
  - Execution state: pending

- [ ] E-05 RECORD THE SUPERSESSION in `tests/test_runner_shared.py`: add `"resolve_plan_path"` to `SUPERSEDED_SINCE_MOVE`, with a comment paragraph in that block's existing style saying why (the three measured fail-open modes, the fixed behavior, and where the replacement coverage lives: `tests/test_resolve_plan_path_typed.py`). MEASURED AT AUTHORING and to be re-checked at execution: the STRICT fingerprint test (`test_every_clean_symbol_is_a_STRICT_fingerprint_match`) and the fixture loader were removed by commit `19313eed` (test trim, 2026-09-24), so today nothing reads `tests/fixtures/runner_shared_premove_fingerprints.json` and the tuple is an enumerated record, not a gate. It is still updated so the record matches the code if the harness is ever restored. This adds NO new source-pinning assertion. If the strict test has been RESTORED by execution time, this entry is what keeps it green, and V-05's run proves it.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: `resolve_plan_path` is listed with its reason; `tests/test_runner_shared.py` passes.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-06 ADD `tests/test_resolve_plan_path_typed.py` (behavioral only; build temp repos; no source-text or AST assertions). Cases: (1) `configured` = a plans-tree `README.md` raises `DriverError` naming a plans index file; (2) `configured` = a `.spec.md` path raises `DriverError` naming the spec type; (3) `configured` = a root `AGENTS.md` containing `- Kind: child` raises (outside the plans trees); (4) an id6 that only appears in another plan's filename slug (`...-adopt-spec-abc123.ipd.md` with `- Id: zzz999`) raises `Cannot locate IPD abc123` instead of returning that plan. THIS CASE EXERCISES THE ID6 BRANCH (E-02), NOT THE GLOB, and the fixture shape is load-bearing: measured, the pre-change function RETURNS that plan through `selectors.resolve_selectors`' substring precedence, while the glob pattern `*-abc123-*.ipd.md` does NOT match a TRAILING id6, so this fixture never reaches the fallback at all; (5) a plan copy under `.aw/worktrees/<lane>/.aw/records/plans/...` and one under `.aw/state/suite-baselines/<x>/...` do NOT make `resolve_plan_path(repo, "", id6)` ambiguous when the real plan exists in `repo`'s plans tree (5a), and do not resolve at all when it does not (5b). SPLIT INTO TWO SUB-CASES BECAUSE ONLY ONE IS A REGRESSION TEST: measured, 5a ALREADY PASSES pre-change (the id6 branch resolves the real plan before the glob is ever reached), so it is a GUARD that E-02/E-04 must not break, while 5b is the genuine fail-before (pre-change it raises `Ambiguous IPD` over the lane and baseline copies; after E-04 it raises `Cannot locate`). Assert 5b's MESSAGE, not merely that it raises, or the case cannot tell the two errors apart; (6) two plans that each MENTION `abc123` MID-SLUG (so the fallback pattern actually matches: `...-zzz999-adopt-abc123-spec.ipd.md` and `...-yyy888-revisit-abc123-again.ipd.md`, each declaring a FOREIGN `- Id:`) do not produce `Ambiguous IPD`. MID-SLUG IS REQUIRED, NOT COSMETIC: measured, a TRAILING `-abc123.ipd.md` is not matched by `*-abc123-*.ipd.md`, so the pre-change function already raises `Cannot locate` for the trailing shape and this case would PASS VACUOUSLY (asserting nothing about the glob narrowing it exists to prove). With the mid-slug shape the pre-change function raises `Ambiguous IPD abc123` over both paths (`id6_ownership` -> `foreign-id` for each), which is the behavior E-04 removes; (7) REGRESSION: a pending plan declaring `- Id:` resolves, and after `rename` to `executed/` still resolves with the stale configured path (mirrors `tests/test_oc_runipd.py::...test_resolve_plan_path_handles_transition_to_executed`); (8) REGRESSION: `resolve_plan_path(lane, rel, id6)` returns the LANE copy when the lane holds one (mirrors `TestIsolatedTurnPromptPointsAtTheLane`); (9) a legacy slot-only plan (no `- Id:`, id6 in the filename slot) is still found by the glob fallback;
  - Depends on: E-05
  - Expected outcome: all nine pass. FAIL against the pre-change function: (1), (2), (3), (4), (5b), (6). PASS both before and after (guards, not proofs): (5a), (7), (8), (9). State that split in the test module's docstring; a case in the second group that FAILS pre-change means the fixture is wrong, not that the fix works.
  - Execution state: pending

- [ ] E-07 ADD THE DISPATCH-REFUSAL CASE to `tests/test_resolve_plan_path_typed.py`. (10) DISPATCH: a queue item whose `configured_file` is a spec path, run through `oc_runipd.execute_item` with `run_opencode` patched to FAIL the test if called, raises `DriverError` before any turn (and through `run_queue`, the item ends in the driver-error status with `driver_error` naming the spec type while an independent second item still runs). COVER BOTH ACTIONS, `review` AND `execute`, since a spec-path item can carry either (F-2) and the review turn takes a different prompt builder; both are still refused because `execute_item_core` resolves the plan path BEFORE computing `is_review`, which is the property that makes one guard cover both and is worth asserting rather than assuming. Patch whichever spawn each action would reach so neither can run. Split from E-06 at review because this case needs a DIFFERENT harness from (1)-(9): a real `run_queue` driver with a patched spawn and a second independent item, not a direct `resolve_plan_path` call, so bundling the two made one item span two test shapes. Use `support.declare_execution_role(self)` where the lifecycle verbs run.
  - Depends on: E-06
  - Expected outcome: the spec-path item is refused with `DriverError` before any spawn for BOTH the `review` and the `execute` action; through `run_queue` it ends in the driver-error status with `driver_error` naming the spec type, an independent second item still runs, and the patched spawn records zero calls for the refused item. Fails against the pre-change function (which resolves the spec and spends a turn).
  - Execution state: pending

- [ ] E-08 RE-RUN E-01's four probes and the scratch-repo spec run after the change, and run the bare suite. The scratch spec run should now leave the item refused with a `driver_error` naming the spec type, and no agent turn (with `--prepare-only` nothing is spawned either way, so drive one real `start` with `AW_OPENCODE` or the opencode binary option pointed at `/bin/false` to show the refusal comes BEFORE the spawn, or cite E-07 if that option is unavailable). Run `python3 -m pytest` BARE before and after.
  - Depends on: E-07
  - Expected outcome: all four probes refuse (or `Cannot locate`); the miss timing is in milliseconds; the after-minus-before failing node set is empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `selectors.resolve` precedence is path, id6, setid, status, stem, substring, and `allow=` makes a match through a non-allowed kind an explicit rejection rather than a silent skip. `selectors.resolve_one` and `resolve_selectors` DROP that verdict (their docstring: "Do NOT reuse this shim for a NEW read path").
- Ownership versus mention: `selectors.id6_ownership` and `CLAIMING_OWNERSHIPS` (declared, slot-only) are the D140 identity-versus-reference predicate; `Resolution.kind == substring` means "not proven to declare", not "is a reference".
- Plan membership: `runner_shared.discover_plans` walks `.aw/records/plans` and `.agents/plans` and skips `README.md`, `INDEX.md`, `STATUS.md`; measured, every discovered plan ends `.ipd.md` and every one declares `- Id:` (`id6_ownership` -> `declared`), so E-02's narrowing excludes none of them. The POPULATION SIZE is live and is not a bar: authored as 804, re-measured at review as 836; re-derive it and assert the PROPERTY (zero non-`.ipd.md`, zero non-`declared`), not the total.
- `status_set.detect_artifact_type` checks the facet first (`.spec.md` -> `specs`), then LOCATION (anything under `records/plans/` -> `plans`, including README), then content (`# IPD:` or `- Kind: child|orchestrator` -> `plans`).
- Driver errors at dispatch are item-local: both hosts' `run_queue` wrap `execute_item` in `except DriverError as exc:`, record `driver_error`, emit `ipd-driver-error`, and continue.
- Test policy (maintainer ruling 2026-09-26): behavior tests only, no new source or AST pins. Suites run BARE; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `ea206c49` (2026-09-26). F-1 through F-8 are the author's; every one was re-verified at lane HEAD `ec5c6c12` during review and reproduced. F-9 through F-13 were added by `/plan-review` on 2026-09-26.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `resolve_plan_path`, `configured` branch | Any existing file is returned. | README -> returned; `4sd62s` `.spec.md` -> returned |
| F-2 | HIGH | production path | A spec-path selector queues the spec with `configured_file` = the spec. THE ACTION FOLLOWS THE SPEC'S OWN `- Status:`, corrected at review: a `to-review` spec yields action `review`, and only an `approved` one yields `execute`. Either way the item is queued and `resolve_plan_path` is reached, so the fix applies to both. | re-measured on two scratch repos: `Status: to-review` -> `(action review, initial_status to-review, queued)`; `Status: approved` -> `(action execute, initial_status approved, queued)`; `configured_file` is the `.spec.md` path in both. `action_for(None,'to-review')` -> `review` |
| F-3 | HIGH | id6 branch | Substring precedence resolves a spec id6 to a plan mentioning it. | `resolve_plan_path(repo, "", "77tr3o")` -> `executed/20260906-orchretire-00-84j8d7-...-adopt-spec-77tr3o.ipd.md`; `selectors.resolve(...)` kind `substring` |
| F-4 | MEDIUM | glob fallback | Root `rglob` sees lane and baseline copies and mention-only slugs. THE COUNT IS A LIVE POPULATION (see the Concern): re-derive at execution, do not assert the authored number. | authored: `25kzda` -> `Ambiguous IPD` over 24 paths, 22 under `.aw/worktrees/` or `.aw/state/`, 2 mention-only (`id6_ownership` -> `foreign-id`). Re-measured at review in a lane checkout: 3 paths, all 3 under `.aw/worktrees/`/`.aw/state/`. Property holds in both: every path is a copy or a non-claimer |
| F-5 | MEDIUM | glob fallback | A miss walks the whole checkout. | root `rglob` about 0.54s; plans tree only about 0.004s; the full `resolve_plan_path` miss about 0.45s |
| F-6 | HIGH (design) | `status_set.detect_artifact_type` | Returns `plans` for `.aw/records/plans/README.md` and for a root `AGENTS.md`, so the type check alone cannot refuse F-1's README case. | direct calls |
| F-7 | INFO | callers | 28 real call sites, ALL in `runner_shared` (re-measured by AST at review; the authored 29/27/1/1 split was a grep artifact - both hosts only re-export). No deliberate non-plan `configured`; the only non-plan origin is F-2. | AST call census: runner_shared 28, oc_runipd 0, agy_runipd 0. Distinct `configured` expressions: 13x `item.get('configured_file','')`, 3x `''`, 3x `configured`, 2x `str(item.get('configured_file') or '')`, and one each of `str(lane.get('configured_file') or '')`, `item.get('configured_file') or ''`, `plan.get('file','')`, `manifest['plans'][id6].get('file','')`, `cfg`, `plan_info.get('file','')`, `f`; `refuse_unrunnable_selected_types`, `resolve_selected_artifact_paths` |
| F-8 | INFO | fingerprint harness | The strict fingerprint test and the fixture loader were removed in `19313eed`; `SUPERSEDED_SINCE_MOVE` survives as data that no test reads. The current `resolve_plan_path` still fingerprints equal to both pre-move captures. | `git show 19313eed -- tests/test_runner_shared.py` removes `test_every_clean_symbol_is_a_STRICT_fingerprint_match`; `git grep premove_fingerprints -- 'tests/*.py'` -> comments only |
| F-9 | MEDIUM | E-06 case (6) as authored | The fixture put the id6 TRAILING (`...-adopt-spec-abc123.ipd.md`), which the fallback pattern `*-<id6>-*.ipd.md` never matches, so the case would have PASSED VACUOUSLY against the pre-change code and proved nothing about E-04. Found at review; fixture corrected to MID-SLUG. | trailing shape pre-change -> `Cannot locate IPD abc123` (already the post-fix answer) and `glob *-abc123-* hits: []`; mid-slug shape pre-change -> `Ambiguous IPD abc123` over both paths, each `id6_ownership` -> `foreign-id` |
| F-10 | MEDIUM | E-06 case (5) as authored | Case (5) bundled a GUARD with a PROOF: 5a (real plan present) already passes pre-change because the id6 branch resolves before the glob is reached, while only 5b (real plan absent) is a genuine fail-before. E-06's expected outcome listed all of (1)-(6) as failing pre-change, which is false for 5a. Found at review; split into 5a/5b with the fail-before set restated. | 5a pre-change -> returns the real `pending/` plan; 5b pre-change -> `Ambiguous IPD abc123` over the lane and baseline copies |
| F-11 | MEDIUM | F-2 as authored | The production-path claim said the spec queues as an `execute` item. Re-measured: the action follows the SPEC'S OWN `- Status:`, so a `to-review` spec yields `review` and only an `approved` one yields `execute`. The fix is unaffected (`execute_item_core` resolves the plan path BEFORE branching on `is_review`), but E-07's dispatch test must cover BOTH actions or it tests only half the reachable states. | two scratch runs: `to-review` -> `(review, to-review, queued)`; `approved` -> `(execute, approved, queued)`; `action_for(None,'to-review')` -> `review`; `execute_item_core` calls `resolve_plan_path` on the line before `is_review = action == "review"` |
| F-12 | LOW | F-7 / Concern as authored | The call-site census ("29 code call sites: 27 in `runner_shared`, one each in `oc_runipd` and `agy_runipd`") was a grep artifact counting the `def`, both host RE-EXPORT lines and prose. By AST there are 28 real calls, ALL in `runner_shared`, and neither host calls it - which the plan's own Scope check already stated, so the plan contradicted itself. Found at review; corrected and E-01 switched to an AST census. | AST: runner_shared 28, oc_runipd 0, agy_runipd 0. grep: 29/1/0. `oc_runipd.py` and `agy_runipd.py` contain only `resolve_plan_path as resolve_plan_path` plus comments |
| F-13 | LOW | live-artifact counts | Three counts were written as bars rather than as re-derived properties, and two have already drifted: the `25kzda` ambiguity set (authored 24 paths / 22 lane-or-baseline / 2 mention-only; re-measured in a lane checkout as 3, all lane-or-baseline) and the discovered-plan total (authored 804; re-measured 836). Per the plan-review live-artifact convention these belong in prose as context with the PROPERTY as the bar. Found at review; all three restated. | `resolve_plan_path(repo,"","25kzda")` -> Ambiguous over 3 paths at review; `discover_plans` -> 836, of which 0 non-`.ipd.md` and 0 non-`declared` |

## Proposed changes (ordered, validatable)

1. E-01 reproduces the fail-open modes and audits every caller.
2. E-02 restricts the id6 branch to an exact `- Id:` match.
3. E-03 type-checks the configured branch using discover_plans' membership rule plus `detect_artifact_type`.
4. E-04 narrows the glob fallback to the plans trees and to claiming hits.
5. E-05 records the supersession.
6. E-06 adds the nine behavioral resolver cases.
7. E-07 adds the dispatch-refusal case (both actions).
8. E-08 re-probes and runs the suite.

## Deferred / out of scope (with reason)

- Refusing a non-plan path in `expand_selectors`' file-candidate branch at selection time.
  - Carrier-Declined: owned by spec z7nbn1 (typed selection-to-dispatch, its Sections 4.1/4.2), under maintainer review; a spec is not an accepted carrier type, and backlog oc3mhb is blocked on that spec's approval.
  - Rationale: typed selection-to-dispatch is that spec's subject (its Section 4.1/4.2), and it is under maintainer review; after this plan such an item is refused loudly at dispatch instead of running silently.
- Changing `selectors.resolve`'s precedence or `resolve_selectors`.
  - Carrier-Declined: shared by every verb; this plan narrows only its own call.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/oc_runipd.py` and `agy_runipd.py` re-export the shared function (`resolve_plan_path as resolve_plan_path`) and need no edit. `agent_workflows/selectors.py` and `status_set.py` are called, not changed. `tests/fixtures/runner_shared_premove_fingerprints.json` is deliberately NOT re-baselined (the harness rejects re-baselining; F-8).
- Scope-Paths justification: `runner_shared.py` holds the function; the new test file holds E-06 and E-07; `tests/test_runner_shared.py` receives E-05's tuple entry.

## Required tests / validation

- `tests/test_resolve_plan_path_typed.py` (new): nine resolver cases (E-06) covering each fail-open mode plus the preserved lane, executed-transition and legacy-slot behaviors, and the dispatch-refusal case (E-07) for both the `review` and the `execute` action. The fail-before set is (1), (2), (3), (4), (5b), (6) and the dispatch case; (5a), (7), (8), (9) are guards that pass both before and after.
- `tests/test_runner_shared.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py` pass unchanged apart from E-05's tuple entry.
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- N/A: no `.spec.md` in `- Scope-Paths:`. Spec `z7nbn1` Section 4.2 DESCRIBES this fail-open behavior as a measured prerequisite for universal dispatch; after execution that paragraph becomes historical. It is not edited here because `z7nbn1` is under maintainer review, and the dispatch work that graduates from it (backlog `oc3mhb`) is where its prerequisite list should be updated to "satisfied by mxzogk". Spec `25kzda` Section 2.3's "shared precedence ... then filename substring" governs OPERATOR selector resolution, which this plan does not change.
- No user-facing docs.

## Open questions

### OQ-01: Does any caller deliberately pass a non-plan as `configured`?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO, from repository evidence (F-7). Every one of the 28 origins (re-counted by AST at review) is a manifest/queue `file`/`configured_file` or `""`; `refuse_unrunnable_selected_types` refuses non-`ipd` `--type` selections before the queue is built and `resolve_selected_artifact_paths` routes specs through `discover_specs` precisely because this resolver fails open. The single non-plan origin, F-2, is accidental, and refusing it is the fix. E-01 re-audits at execution.

### OQ-02: Is `detect_artifact_type == "plans"` a sufficient configured-branch check?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO, measured (F-6): it reports `plans` for the plans `README.md` that is one of the measured fail-open inputs. E-03 therefore also requires discover_plans' own membership rule (under a plans tree, not an index file), so the resolver and the discoverer agree on what a plan is.

### OQ-03: How is the strict AST fingerprint pin handled?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: through the existing `SUPERSEDED_SINCE_MOVE` enumeration (E-05), per the documented pattern and not by re-baselining the fixture. Measured (F-8), the strict test itself was removed in `19313eed`, so today the entry records a supersession rather than unblocking a failing test. No new source-pinning test is added.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the four probe results with timings; the AST call-site origin table (one row per real call, whatever the count is at execution - do NOT reconcile it to a number written here) with each `configured` origin; the measured non-`.ipd.md` and non-`declared` plan counts (both must be 0) beside the discovered total; and BOTH scratch runs' `configured_file`/`action` (the `to-review` and the `approved` spec).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of the id6 branch; `resolve_plan_path(repo, "", "77tr3o")` no longer returning the orchretire plan (paste the new error text); and the `selectors.resolve(..., allow={MATCH_ID6})` verdict for a control id6 that DOES declare itself, showing `kind=id6` and one path, so the narrowing is shown to reject without also breaking the positive case.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of the configured branch, the `DriverError` text for the README and the spec inputs, and a positive control: a real pending plan path still returned, plus the same for a `.agents/plans` path and for an ABSOLUTE configured path inside the repo (both measured working pre-change at review, so both are regressions if they break).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the diff of the glob fallback, the new `25kzda` result (`Cannot locate IPD 25kzda`) with its timing beside E-01's pre-change timing, and the preserved byte-identical text of BOTH error messages, evidenced by `python3 -m pytest -o addopts="" tests/test_agy_runipd_cli.py -q` passing (it asserts `Cannot locate IPD agy404`).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `SUPERSEDED_SINCE_MOVE` diff, `git grep -n premove_fingerprints -- 'tests/*.py'` at execution (showing whether any test loads the fixture), and `python3 -m pytest -o addopts="" tests/test_runner_shared.py -q` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_resolve_plan_path_typed.py -q` passing with the count; then with the E-02..E-04 hunks temporarily reverted, the same command showing cases (1), (2), (3), (4), (5b), (6) and (10) FAILING and (5a), (7), (8), (9) still PASSING; then passing again after restoring. A case in the second group that fails pre-change means its fixture is wrong (it is a guard, not a proof) and must be corrected before this V item may be marked verified.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the dispatch-refusal test output for BOTH the `review` and the `execute` action, each showing the `DriverError` text naming the spec type and the patched spawn's recorded call count of ZERO for the refused item; plus the `run_queue` case showing the item's driver-error status, its `driver_error` field, and the independent second item still completing. Then the same test FAILING against the pre-change function.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the four post-change probe results with timings beside E-01's pre-change timings, both scratch-run refusals (the `to-review` and the `approved` spec) or the E-07 citation if the binary option is unavailable, and the bare `python3 -m pytest` summary line BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A behavior change to the shared plan resolver: it now returns only a real IPD (exact `- Id:` match, or a configured path that is a plan by discover_plans' own rule, or a plans-tree file that claims the id6) and otherwise raises `DriverError`. A caller that silently got a README, a spec, or a merely-mentioning plan now gets a loud, item-local refusal; a miss no longer walks lane worktrees or suite baselines. That is the point, and it is also a prerequisite named by spec `z7nbn1` Section 4.2. This graduates backlog `m10mrs` and inherits its `- Blocks-Release: next`.

WHAT REVIEW CHANGED, since none of it alters the FIX and all of it alters what the tests PROVE. The three code changes (E-02, E-03, E-04) were each re-measured and stand as authored; the narrowing was verified not to break the executed-transition case, the lane case, the `.agents/plans` tree, an absolute configured path, or any of the discovered plans (every one declares `- Id:`). What moved is the EVIDENCE: two test fixtures would have proved nothing as written (one unreachable by the glob it targeted, one already passing pre-change), the production-path finding named the wrong action for a `to-review` spec so the dispatch test now covers both, the call-site census was a grep artifact that contradicted this plan's own scope note, and three drifting counts became re-derived properties. The dispatch case was also split into its own item because it needs a `run_queue` harness the other nine do not.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/runner_shared.py` (`resolve_plan_path` only - the id6 branch, the configured branch, and the glob roots plus its ownership filter; both error-message strings stay byte-identical), the new `tests/test_resolve_plan_path_typed.py` (E-06's nine cases and E-07's dispatch case), and `tests/test_runner_shared.py` (`SUPERSEDED_SINCE_MOVE` only). If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New tests must be shown FAILING against the pre-change function.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `m10mrs` `done` with `--evidence` citing the executed plan; its release gate is preserved by the `From-Backlog` handoff.
