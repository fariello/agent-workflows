# Review findings: ipd wknwwz

- Subject-Id: wknwwz
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: opencode/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at local HEAD `b85b57364` (the `p0hq1k` lane integration) in an isolated runner review-sweep lane worktree. The target plan `.aw/records/plans/pending/20261121-es4blt-01-wknwwz-read-the-lane-copy-of-an-orchestrator-plan-in-the-review-rea.ipd.md` was committed and clean at turn start, so no pre-review snapshot commit was needed. It is Order 1 of Set `es4blt`, graduated from backlog `es4blt` (`Work-Kind: bug`, `Status: graduated`), and carries `- Blocks-Release: next`. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 errors, 2 `IPD-C802` advisories in the template's validation-rule sentence).

The central result: the bug still reproduces at HEAD, but two commits that landed on 2026-11-24, after the plan was authored, changed the code it was written against. Commit `b77c6ef43` added a read-only helper, `ipd_lifecycle._resolve_staged_companion_lane_plan`, that does what the plan's new `map_companion_lane_path` was meant to do (F2). Commit `c8a130148` made `aw ipd set <id6> --dir <lane>` write the staged lane copy, so the plan's Finding F-04 is now false and its E-04 is unnecessary (F1). The review cut the plan to one production change: a call to the existing helper.

AW-TIER: standard

### Step T

- Checked: the five tier questions in `steps/t-tier.md`.

1. No: no flag, reason code, or spec text changes. One CHANGELOG bullet is added at review.
2. Yes, narrowly: the gate decides a review item's disposition in `aw oc run` / `aw agy run`. After review the change only adds a lane-copy lookup ahead of the existing fallback.
3. No: four E-items after review, three work Scope-Paths.
4. Yes: `- Scope-Paths:` is present; review removed `agent_workflows/lane_containment.py` and added `CHANGELOG.md`.
5. Low: one inserted step in one function, guarded so the shared-checkout and repository-backed paths are unchanged.

`AW-TIER: standard`

### Step R1

- Checked: `agent_workflows/runner_shared.py::handle_review_orchestrator_readiness` (the `plan_file` resolution block, the `review_readiness` loop, the demotion command under `# If plan reads reviewed, return it to to-review`, and the correction-turn path that reads `item["position"]`); both call sites in `execute_item_core`; the review dispatch that assigns `staged_review_plan`; `queue_artifact_path` and `resolve_plan_path`; `agent_workflows/lane_containment.py::resolve_companion_lane_path`, `stage_companion_lane_artifact`, `write_companion_staged_baseline`, and `companion_staged_records_root`; `agent_workflows/ipd_lifecycle.py::_resolve_staged_companion_lane_plan` and its call sites (`run_finalize` and the `runner_shared.py` finalize site that assigns `current_plan_for_finalize`); the `status_set.py` staged-lane handling added in `c8a130148`; `orchestrator_readiness.review_readiness`; spec `llbr2b` section 3.10 row A-4.
- Reproduced at HEAD with `tests/test_companion_runner_integration._provision_companion_repos` and `_add_lane_worktree`, and with the plan writers from `tests/test_production_correction_turn`. The lane copy was at `reviewed` with a passing coverage record, and the companion copy was at `to-review`. With `plan_path=<companion>` and `retry_budget` 0, the result was `disposition='fail-gate', refused=True` and the refusal said `is ready but status remains to-review`. With the default budget, the stub launcher was called, which is the correction turn the backlog item describes. With `plan_path=_resolve_staged_companion_lane_plan(lane, <companion>)`, the result was `disposition='reviewed', refused=False` with 0 retry attempts.
- Found F1: the plan's F-04 says `aw ipd set to-review <id6> --dir <lane>` writes the companion copy, and E-04 changes the selector to a path to fix that. At HEAD, with both copies at `reviewed`, the id6 selector and the path selector each set the lane copy to `to-review` and left the companion copy at `reviewed`. With no lane copy staged, the id6 selector wrote the companion copy. The change came with `c8a130148` (`status_set` honors `companion_staged_records_root`). Fixed: E-04 removed; F-04 rewritten with the new measurement; the demotion keeps `item["id6"]`, so spec `llbr2b` row A-4 stays accurate word for word.
- Found F2: E-02 adds `lane_containment.map_companion_lane_path`, but `ipd_lifecycle._resolve_staged_companion_lane_plan` (from `b77c6ef43`) already maps a companion plan to its staged lane copy without writing, and `runner_shared.py` already calls it across modules. The probe confirmed it returns the companion path before staging and the lane copy after staging. Fixed: E-02 removed; E-03 calls the existing helper; `lane_containment.py` dropped from Scope-Paths; F-08 records the evidence.
- Found F3: while the unfixed gate reads the companion copy, `review_readiness(..., ask=True)` writes `- Coverage: pass`, a fingerprint, and a history line straight into the companion copy (diff captured). The authored test (a) asserted only that the companion copy "still reads `Status: to-review`", which would pass even with that write. Fixed: F-09 added; tests (a) and (c) assert that the companion bytes are unchanged.
- Noted: the backlog's Expected fix names `queue_artifact_path(tree, item)` first. At HEAD that function still returns the companion path from inside the lane (re-measured), so mapping `plan_path` alone is enough, and mapping the `queue_artifact_path` result would be redundant. F-02 records this.

### Step R2

- Checked: the E/V bijection, `Depends on` edges, Scope-Paths, the right-sizing rule, test placement and tier marker, and whether each V-item demands concrete evidence.
- Found F4: the E-05 recipe as written could not run as intended. The `item` dictionary lacked `position`, so with the default budget the correction path raised `KeyError: 'position'` before it reached the launcher stub (measured). `retry_budget` 0 was set only for test (c), so test (a) at the base commit would raise instead of failing on an assertion. Test (d) tested `map_companion_lane_path`, which no longer exists. Fixed: E-05 gives the exact `item`, `state`, and keyword arguments for every test; budget 0 applies to all tests; test (d) is replaced by a shared-checkout case (`tree=target`, `work_dir=None`) that asserts no `<target>/.aw/records` is created.
- Found F5: the fail-before check covered only test (a). Test (c) also fails at the base commit (the lane copy stays `reviewed`), while (b) and (d) pass there by design. The scratch worktree also used a fixed `/tmp/opencode/...` path. Fixed: E-03 records the base commit; E-06 runs (a) and (c) at that commit in a `mktemp -d` worktree; E-05's expected outcome says which tests fail at base and why the others do not.
- Found F6: there was no CHANGELOG entry for a user-visible runner fix, unlike the sibling bug plans in Set `dogfood-bugs` (`gftvh6`, `p0hq1k`, `d8b9rp`). Fixed: new E-07 and V-07; `CHANGELOG.md` added to Scope-Paths.
- Found F7: the neighbouring-suite list omitted `tests/test_companion_ipd_lifecycle.py`, which is the module that exercises the reused helper. Fixed: added to E-06 and Required tests.
- Noted: the fixture provisions in about 0.06s, so the new module fits the core tier without a slow-allowlist entry.

### Step R3

- Checked (short form): no new input parsing, subprocess, network, or credential. The change narrows a write: after the fix the gate no longer writes coverage metadata into the companion repository outside `route_companion_lane_records` (F-09). `aw sanitize --agent` was run at finalize.
- No security finding.

### Step R4

- Checked: the two `execute_item_core` call sites. The isolated-lane site passes `tree=Path(wt_handle.path)`, where the staged-baseline marker exists whenever `staged_review_plan` was staged. The shared-checkout site passes `tree=repo`, where the new step is skipped by the `tree.resolve() != repo.resolve()` guard. The correction prompt and `resume_via_launcher` keep receiving the original `plan_path`; this is unchanged and outside the backlog's acceptance criteria. Backlog carriers `wdy3wg` and `82cles` exist, and their defects were re-measured at HEAD (`aw ipd board --no-color` still raises `ValueError`; `read_set_membership(lane, ...)` still omits a lane-only child).

### Step S5

- Checked: OQ-01 (resolved, non-blocking) still holds, and the reused helper keeps it true because it writes nothing. The two judgement calls this review made are recorded as D1 and D2 and are reversible. No question needs a human answer before approval.

### Pass 2

- Re-read the revised plan end to end. E-03, E-05, E-06, and E-07 map one-to-one to V-03, V-05, V-06, and V-07, and `Highest E allocated: 07`. No text still refers to E-02, E-04, or `map_companion_lane_path` except the Scope check's record of their removal. The flowchart uses decision shapes for every branch and marks the one new step. `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 errors) after the edits.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | HIGH | IN-SCOPE | R1 / Stale premise | Probe at `b85b57364`: id6 selector demoted the lane copy, companion stayed `reviewed`; commit `c8a130148` | F-04 and E-04 rest on demotion behaviour that changed after authoring; E-04 would change the spec-cited command for nothing. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-04 removed; F-04 rewritten; test (c) guards the demotion target. |
| F2 | MEDIUM | IN-SCOPE | R1 / Duplicate helper | `agent_workflows/ipd_lifecycle.py::_resolve_staged_companion_lane_plan` (commit `b77c6ef43`); existing call in `runner_shared.py` | E-02 would add a second read-only companion-to-lane mapper. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-02 removed; E-03 reuses the helper; `lane_containment.py` out of Scope-Paths. |
| F3 | MEDIUM | IN-SCOPE | R1 / Hidden companion write | Diff of companion copy after unfixed gate: `+- Coverage: pass` and a history line | The unfixed gate writes coverage into the companion copy, and the authored assertion (status only) could not see it. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | F-09 added; tests (a) and (c) assert companion bytes unchanged. |
| F4 | MEDIUM | IN-SCOPE | R2 / Test executability | `KeyError: 'position'` with default budget; budget 0 only in (c); test (d) targeted a removed function | The test recipe would error rather than fail at base, and one test tested code no longer planned. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-05 specifies every argument, budget 0 for all tests, and a shared-checkout test (d). |
| F5 | LOW | IN-SCOPE | R2 / Fail-before proof | Probe: (c) lane copy stays `reviewed` at base | Only (a) was proven to fail without the fix; scratch path was fixed. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-06 runs (a) and (c) at the recorded base in a `mktemp -d` worktree. |
| F6 | LOW | IN-SCOPE | R2 / User docs | Sibling bug plans add `- Fixed:` bullets | A user-visible runner fix had no CHANGELOG entry. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | New E-07 and V-07; `CHANGELOG.md` in Scope-Paths. |
| F7 | LOW | IN-SCOPE | R2 / Neighbour coverage | `tests/test_companion_ipd_lifecycle.py` calls `_resolve_staged_companion_lane_plan` | The suite covering the reused helper was not run. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Added to E-06 and Required tests. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D1 | Reuse the private `ipd_lifecycle._resolve_staged_companion_lane_plan` or add a public mapper? | Reuse it, imported inside the function | New `lane_containment.map_companion_lane_path`; rename the helper public | `runner_shared.py` already calls it at the finalize site; a rename touches `ipd_lifecycle.py` and its tests with no behaviour change (recorded as Carrier-Declined) | yes |
| D2 | Keep the demotion's id6 selector or switch to a path? | Keep `item["id6"]` | `str(plan_file)` | Measured: the id6 selector writes the staged lane copy at HEAD; keeping it leaves spec `llbr2b` row A-4 exact | yes |

### Proofreading

Checked the plan against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Front matter | Four Scope-Paths including `lane_containment.py`; `Highest E allocated: 06`; "read and demote" | `runner_shared.py`, test module, `CHANGELOG.md`; `07`; "read" | F1, F2, F6 |
| Scope, Goal, terms | New mapper and selector change | Reuse of existing helper; defines the staged-baseline marker | F1, F2; requirement 1 |
| E-02, E-04 | New mapper; selector change | Removed | F1, F2 |
| E-03 | Five-step reorder using the new mapper | One inserted step using the existing helper; records the base commit | F2, F5 |
| E-05 | Single dense paragraph; missing `position`; budget only in (c) | Setup, call arguments, staging, and cases as separate parts; shared-checkout test (d) | F3, F4; requirement 4 |
| E-06, new E-07 | Fail-before for (a) only; no CHANGELOG | (a) and (c) at base in `mktemp -d`; CHANGELOG bullet | F5, F6, F7 |
| Conventions, Findings | Authoring-time measurements only | Helper and status_set conventions; F-02 to F-07 re-measured; F-08, F-09 added | F1, F2, F3 |
| Flowchart | Decisions drawn as rectangles; redundant mapping branch | Decision shapes; one marked new step | requirement 12 |
| Scope check, Spec sync, Deferred | Selector change justified against A-4 | Records removed items; A-4 unchanged; rename declined | D1, D2 |
| V-02 to V-06 | Evidence for removed items | V-03, V-05, V-06, V-07 for the remaining items | F1, F2, F6 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |
