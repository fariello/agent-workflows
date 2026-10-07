# Review findings: plan 5eygjt

- Subject-Id: 5eygjt
- Subject-Type: ipd
- Reviewed-At: 2026-10-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `2cb41a769` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review, and `--phase review-finalize` was clean after revision.

Reproduced on scratch `git init` fixtures built with `tests/test_backlog_handoff_close.py`'s `_make_scratch_repo`,
`_write_backlog_item`, `_write_plan` and `_write_spec` (gitignored probes, no production edit):
- Executed plan + `approved` spec: `find_from_backlog_artifacts` returns both;
  `evaluate_backlog_close(repo, "item01", [plan])` -> `close=True, reason='every IPD carrier is executed and this run
  executed ...pln001...', rule='ipd'`. Same verdict with the spec `implemented`. Empty earned set -> `close=False`
  "this run executed none of its carriers". Spec-only `draft` -> `close=True, rule='other'`.
- Inner gate on the same item: `evaluate_blocking_close(repo, item, "done")` -> `False`, "handed off to From-Backlog
  carrier(s) (...pln001..., ...spc001...) but the work has not shipped"; with the outer citation -> `True SATISFIED`.
- Spec carriers at `superseded`, `deferred`, `parked` are all discovered by `find_from_backlog_artifacts`, and the
  inner gate refuses each without evidence.
- Cited code resolves: `runner_shared.evaluate_backlog_close` returns inside `if ipds:` with `others` unread
  (`agent_workflows/runner_shared.py:38008-38064`); `CARRIER_KIND_IPD` comment block and `BacklogCloseVerdict.rule`
  docstring (`:37848-37875`); `process_backlog_close` passes `verdict.evidence` to `close_backlog_item`
  (`:36607-36614`); `check_engine._carrier_is_executed` reads spec `- Status:` (`agent_workflows/check_engine.py:4729`);
  both hosts import `evaluate_backlog_close as evaluate_backlog_close` (`oc_runipd.py:501`, `agy_runipd.py:680`);
  no test calls `evaluate_backlog_close`; `tests/test_backlog_handoff_close.py::test_case_5_mixed_kind_carriers_plan_and_spec`
  exists.
- Live precedent: backlog `0k74my` closed by `aw oc run` (`528376446`, 2026-09-12) while spec `w15vzb` is `approved`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | D. Anti-regression | `tests/test_inlane_retirement_lands.py:554-556` asserts `"IPD carrier(s) not executed"` in the recorded close reason | E-02 told the executor to "widen the reason string", which could reword a prefix an existing test and `render_unclosed_report` depend on. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 keeps the prefix verbatim and adds a separate spec clause. The test is added to Required tests. |
| PR-002 | MEDIUM | UNDER-SCOPE | A. Correctness / UX (stranded state) | `process_backlog_close` is called only on plan execution; `agent_workflows/specs.py` has no backlog close path; retired-spec probes above | After the fix, nothing re-closes a refused mixed item when its spec later reaches `implemented`. A mixed item with a retired spec can never be closed by the runner. The plan did not state this cost. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-10, a Scope-check bound, and a Deferred row carried by new backlog `wfswdb` (followup, low). The behavior is intended because the inner gate already holds these items, and it is surfaced to the operator. |
| PR-003 | MEDIUM | IN-SCOPE | B/G. Shared-checkout safety | AGENTS.md "Never 'fix' a polluted index with a bare `git reset` or `git stash`"; E-04 "a stashed or reverted `runner_shared.py`" | The pre-fix evidence route told the executor to stash or revert a file in what may be a shared checkout. E-04 and the gate also cited `V-03` where the before/after evidence item is V-04. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with "run before E-02", with a `git show HEAD:` scratch import as the fallback. V-04 updated to match. References corrected. |
| PR-004 | LOW | IN-SCOPE | G. Live-artifact criterion | E-05 "the same three pre-existing failures and no others"; `CHANGELOG.md:7` `## 2.0.0 (pending)` | The success bar was a failure set measured at authoring, which goes stale, and it named an `Unreleased` heading that does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The baseline is now re-derived at execution HEAD before the edit and compared by node id. The CHANGELOG target is now the topmost pending heading. |
| PR-005 | LOW | IN-SCOPE | G. E/V bijection | V-01 (e) demands the F-06 census; E-01 did not perform it | The V-item demanded evidence its E-item never produces. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now re-runs the census, and its expected outcome includes it. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should a retired (`superseded`/`deferred`/`parked`) spec count as terminal for the mixed outer rule? | No. Use `_carrier_is_executed` unchanged (only `implemented` counts) | Treat retired specs as terminal in the outer predicate only | The inner gate refuses all three shapes (probe). A divergent outer rule recreates the two-predicate disagreement this plan removes | yes |
| D-2 | Should this plan add an automatic re-close when a spec reaches `implemented`? | No. Defer to backlog `wfswdb` | Hook `aw specs set implemented`; widen this plan's Scope-Paths to `specs.py` | It is a new behavior on a different command. The refusal is recorded and visible. A hand close is the documented route | yes |
| D-3 | How should the pre-fix test failure be produced? | Run the new tests before E-02, or import `git show HEAD:` output in gitignored scratch | `git stash` / revert (as authored) | AGENTS.md shared-checkout rules | yes |

## Round 2

Re-reviewed 2026-10-06 at HEAD `fe2ee961c` in an isolated review-sweep lane. Plan committed and byte-identical to the
lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent` clean before semantic review and
`--phase review-finalize` clean after revision. Round 1's `- Readiness:` had been removed by `8c460a9a1` (the plan was
left at `to-review`); this round sets `reviewed`.

Re-verified (gitignored probe `.aw/state/review-probe-5eygjt-r2/probe.py`, scratch repos built with
`tests/test_backlog_handoff_close.py` helpers, no production edit):
- F-01: earned = executed plan, spec `approved`: carriers `[plan01 .ipd.md, spec01 .spec.md]`, outer `True ipd`, inner
  without evidence `False`. Spec `implemented`: outer `True ipd`, inner `True`.
- Empty earned set on the same mixed fixture: `False this run executed none of its carriers, so the close was not earned`.
- `evaluate_backlog_close` still returns inside `if ipds:` with `others` unread (`agent_workflows/runner_shared.py:39905-39961`);
  prefix `"IPD carrier(s) not executed: "` at `:39937`, asserted at `tests/test_inlane_retirement_lands.py:555`;
  `_carrier_is_executed` reads spec `- Status:` (`agent_workflows/check_engine.py:4838`); carrier `wfswdb` present in
  `backlog/open/`; `CHANGELOG.md:7` top heading `## 2.0.0 (pending)`.
- `tests/test_backlog_handoff_close.py tests/test_inlane_retirement_lands.py tests/test_carrier_scan_single_item_contract.py
  tests/test_runner_delegation_and_host_independence.py`: `73 passed in 19.63s`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | MEDIUM | IN-SCOPE | E. Testing (test guards the fix) | probe: empty earned set -> `False ... close was not earned`; `runner_shared.py:39945-39952` earned check | E-04 did not say what `earned_paths` cases (1)-(5) pass. With an empty or wrong earned set, the pre-fix predicate already refuses the mixed shape for the not-earned reason, so case (1) would pass before the fix and V-04's before/after contrast would be vacuous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires the executed plan's repo-relative path as earned in (1), (2), (3) and (5), and the spec's path in (4), and requires the reason to name the spec. The observed pre-fix verdict is recorded. |
| PR-102 | LOW | IN-SCOPE | G. Sequencing | E-02 `Depends on: E-01`; gate "E-04's tests are written and observed FAILING before E-02" | The mandated order (tests first) contradicted the machine-readable dependency, so a top-to-bottom executor would edit first and lose V-04's before-state. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now `Depends on: E-01, E-04`, with an explicit ORDERING note. |
| PR-103 | LOW | IN-SCOPE | G. Execution contract | plan `## Approval and execution gate` | Gate lacked scope-fence-as-declaration wording, an OQ status statement, and conditional finalize ownership, and its "only the files this plan names" excluded the plan file itself. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate amended. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which earned set should the mixed-case tests pass? | The executed plan's repo-relative path (the spec's for the spec-only case) | Empty set; the spec's path | Observed empty-earned refusal (probe) makes the empty set vacuous; `earned_ipds` is computed over IPD carriers only | yes |
