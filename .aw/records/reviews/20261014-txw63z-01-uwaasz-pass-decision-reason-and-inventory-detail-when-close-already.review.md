# Review findings: plan uwaasz

- Subject-Id: uwaasz
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `9e006dea9`. The plan was committed and unchanged (sha256 matched the sealed lane input `67ba1fa9...`), so no snapshot was needed. `aw ipd lint --phase author` was clean before review.

Re-measured with scratch probes under the gitignored `.aw/state/`, deleted afterwards:

- Direct call of `runner_shared._close_already_complete_backlog_item` with a real isolated lane and an untracked `untracked_residue.txt`: returned `True`, item `executed`, backlog in `done/`, lane kept, `preserved_reason` = `teardown refused: the lane holds content the driver cannot account for: 1 unknown UNTRACKED file(s): untracked_residue.txt`, `preserved_retention_reasons` = `['unknown-untracked-file']`. The current `worktree-preserved` event carries no `unknown_untracked` / `inventory_readable` keys, confirming F-03.
- Same with `runner_shared.teardown_isolation_worktree` patched to raise: `preserved_reason` = `teardown refused: teardown was authorized but failed: RuntimeError: simulated worktree teardown error`, codes `[]`.
- Isolated post-turn route via `run_queue` on `oc` and `agy`: both `executed`, `bklj01` in `done/`, `agent_scratch.txt` kept, `worktree-preserved` emitted with the expected reason and `['unknown-untracked-file']`. With `LaneTeardownDecision.reason` forced to raise the txw63z `AttributeError`, `run_queue` propagated it on both hosts, so sensitivity check (1) is reachable.
- `python3 -m pytest -o addopts="" -q tests/test_backlog_already_complete.py`: `11 passed`. `aw check release-gates` rc=0. `aw sanitize --agent` clean.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing / evidence accuracy | `agent_workflows/lane_containment.py:3256` `RETENTION_UNKNOWN_UNTRACKED = "unknown-untracked-file"` | E-02 told the executor to assert `retention_reasons == ["unknown-untracked"]` in both new tests. The real code is `unknown-untracked-file`, so both tests as specified would fail against correct code, and an executor might "fix" production to match. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced every `"unknown-untracked"` assertion with `"unknown-untracked-file"`, verified by probe. |
| PR-002 | MEDIUM | IN-SCOPE | G. Executability | `agent_workflows/lane_containment.py:131` `item_slug` reads `item['position']`; `agent_workflows/runner_shared.py:36871` `globals().get("integrate_review_lane_branch")` is `None` | The unit-test recipe left out harness details. Without them the direct call crashes for reasons unrelated to the branch under test (`KeyError: 'position'`, or a `None` integrator). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now lists the measured harness requirements: `.gitignore`, `run_dir` location, item shape, `comp` source, and explicit `run_checked` / `host_labels` / `save_state` / `integrate_review_lane_branch`. |
| PR-003 | MEDIUM | IN-SCOPE | E. Test robustness | `agent_workflows/lane_containment.py:4088` `"status": item.get("status")` snapshot; probe saw `fail-verify` | The case-j recipe did not require the plan move to happen in the lane, and it left the event `status` field open to assertion. That field is a pre-`executed` snapshot. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires `fake_agent` to work in `kwargs["work_dir"]` and forbids asserting the event `status`. It also records the measured reachability evidence. |
| PR-004 | LOW | IN-SCOPE | Evidence citation | `agent_workflows/runner_shared.py:36639` `def integrate_retired_lane(` encloses line 36759 | Concern/E-01/F-03 attributed the sibling call site at line 36763 to `def handle_in_lane_retired(`, which does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected to `integrate_retired_lane`. |
| PR-005 | MEDIUM | UNDER-SCOPE | E. Sensitivity hygiene / D | E-03 sensitivity checks temporarily mutate `runner_shared.py` | Nothing proved the mutants were reverted before commit. A leftover `decision.why` would reintroduce the bug. The V-02/V-03 bars were also keyed on test names, which are artifacts of test organization. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03/V-03 now demand a post-restoration `git diff` showing only E-01's change. Test names are now non-binding pointers, and V-02 states the behavioural bar. |
| PR-006 | LOW | UNDER-SCOPE | G. Execution contract | gate `**Execution contract**` | The gate lacked the hard-MUST paste-actual-output rule and a scope-fence declaration with justify-at-finalize semantics. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added both, with no stop-on-scope wording, plus scratch cleanup. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the plan also add `detail=` to the three other early-return `record_lane_preserved` calls in `_close_already_complete_backlog_item` (missing item, close refused, integration refused)? | No. They are not `teardown_lane_if_classified` refusals and have no inventory. | Add synthetic detail | `agent_workflows/runner_shared.py:36937`, `:37003`, `:37073` pass fixed reason codes with no decision object | yes |
| D-2 | Is a CHANGELOG entry needed? | No. The defect was introduced and patched within the unreleased 2.0.0 window, and no tag contains `c59ad329a`. | Add a Fixed line | `git tag --contains c59ad329a` is empty; `CHANGELOG.md:7` `## 2.0.0 (pending)` | yes |
