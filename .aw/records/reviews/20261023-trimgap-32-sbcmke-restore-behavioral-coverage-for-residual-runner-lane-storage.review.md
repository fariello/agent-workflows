# Review findings: plan sbcmke

- Subject-Id: sbcmke
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `f76595a5a`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review by direct calls (every asserted value in E-01..E-05):
- `runner_shared.attributed_away_failure_ids` with the E-01 record ->
  `('FAILED tests/test_a.py::T::test_x', 'FAILED tests/test_b.py::test_y')`; `mine`, unusable, bare string,
  `{}` -> `()` each.
- `worktree_lease.lane_id_from_branch` -> `['ntf6sx', 'abc123_attempt2', None, None, None]`.
- `storage.get_git_common_dir`: main repo and linked worktree both equal `realpath(r/.git)`; non-git dir `None`.
- `TelemetryCollector.start()` (returns a dict): ok adapter -> `event_kind 'start'`, `tool_versions
  {'python': '3.14.0'}`; `ProbeOutcome("unavailable")` and a raising subclass -> no `tool_versions` key
  (`_observe_tool_versions` returns `{}` on exception, and the payload omits an empty dict).
- `hooks.prepush_authorization_gate.check`: unset -> exit 1 with one message containing
  `check.push-unauthorized` and `AW_PUSH_AUTHORIZED=1`; set `1` -> `(0, [])`. `check_push_authorization`
  `ack=False` -> one Drift, rule `check.push-unauthorized`, location `<push>`; `ack=True` -> `[]`.
- `apply_operator(..., "return-none")` changes source for all five keys (OQ-01 premise holds).
- F-04: `19313eed^` control files are 1290 and 675 lines; `tests/test_phase4_hooks.py` has
  `mock.patch.object(ce, "check_push_authorization", spy)`.
- Probes not re-run at review (they are E-07's work at execution HEAD).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Execution contract (rubric G) | plan `## Approval and execution gate` | Gate lacked the hard-MUST paste-actual-output wording, a declarative scope fence with `--scope-reason`, the no-production-change rule, and runner versus hand `aw ipd finalize` ownership; it implied a hand move to `executed/`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to the Set's standard contract (sibling `92tzo6`). |
| PR-002 | LOW | IN-SCOPE | Rubric E (evidence feasibility) | plan V-07, Required tests `<E-06 parent>` | `<E-06 parent>` was cited but recorded by no item. | all Low | FIXED | E-06 records `<E-06 commit>`/`<E-06 parent>`; V-07 demands both pasted. |
| PR-003 | LOW | IN-SCOPE | Rubric E (hermetic tests) | plan E-03; `tests/support.py` `"commit.gpgsign", "false"` | The E-03 throwaway repo commits without disabling signing, so a host with global `commit.gpgsign true` would fail the core test for reasons unrelated to the key. | all Low | FIXED | E-03 sets `commit.gpgsign false` locally, the `tests/support.py` pattern. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Re-run the five probes during review? | No; verify values, applicability and controls | Re-run probes | Probing after the module is committed is E-07; values the tests will assert were all reproduced | yes |
