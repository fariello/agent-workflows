# Review findings: plan 5xq2ng

- Subject-Id: 5xq2ng
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `07a0dd8e1` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review, and `--phase review-finalize` was clean after revision.

Reproduced (a gitignored probe replaying `check_engine.check_lifecycle_transitions`' own loop over
`ipd_lifecycle._plan_status_event_groups`; no production edit):
- Live pending tree: 184 plans with history, 41 validated transitions, 124 plans with >=2 distinct statuses and 0
  validated (all 124 contain an `ordered=False` group), 31 single-status zeros. Collapsing adjacent <=1-day gaps:
  3 validated, 26 plans lose all coverage. Authoring said 123/30/79/22 -> 2/20, so the thesis holds and is larger.
- Fixture pair: two-date legal `draft..approved` -> groups `[('2026-09-01', True), ('2026-09-02', True)]`,
  3 validated; one-date -> `[('2026-09-02', False)]`, 0 validated.
- `check_lifecycle_transitions` live: 5 findings (`5poaqh`, `fv6kep`, `36sifo`, `1xthrh`, `1znlxy`). Authoring said 3.
- `aw check plans`: `errors 32 warnings 0 info 45`.
- Cited code resolves: `artifact_core.drift_exit_code` exempts only `info` (`agent_workflows/artifact_core.py:683`);
  `check.collisions-not-checked` `info` precedent and `check.lifecycle-transition-invalid` `error`
  (`agent_workflows/check_engine.py:572-585`); the producer's "none (single date / 1 record) -> unknown"
  (`agent_workflows/ipd_lifecycle.py:1147`); the plans-type call site (`check_engine.py:1418-1425`);
  `check_commit_invariants` does not compose the rule (`:3784-3788`); spec `2vev8j` 4.3/4.4 text
  (`.aw/records/specs/approved/20260908-2vev8j-...spec.md:169-189`, `- Status: approved`); siblings `5ivkdh`
  (reviewed), `ayhveg`/`9wcei0`/`rfyrvp`/`qjm4bg` (to-review), all in `pending/`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | D. Anti-regression | `tests/test_history_order.py:388-411` (fixture d `len(drift) == 1`; fixture e, a two-status single-date plan, `drift == []`), calling `check_lifecycle_transitions` directly | E-02 told the executor to emit the new rule from `check_lifecycle_transitions`. Fixture (e) is exactly the new rule's trigger, so a finding appended to that function's return breaks an existing test the plan does not declare. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now uses one private walk helper with two public callers. The existing function's return is unchanged, and a new sibling, wired into the `check_type` plans path, emits the rule. E-03 pins that `check_lifecycle_transitions` stays `[]` on the one-date fixture. Required tests and V-02 run `test_history_order.py` unmodified. |
| PR-002 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | Probe counts above | F-04/F-06 counts and E-01's "79 plans" drifted within a day (now 124 multi-status zeros and 31 single-status zeros). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-06 now carries the re-measurement. Prose treats the counts as context, and the bars require re-derivation at execution time. |
| PR-003 | MEDIUM | UNDER-SCOPE | F. UX / noise | `aw check plans` info 45; probe 124 | Day-one volume was not stated: about 124 new `info` findings, which would roughly triple the advisory count. That is a real readability cost the maintainer should see. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 states the volume and keeps it to one finding per plan with a bounded detail. V-04 demands before/after per-rule counts and shows the new rule is the only count that moved. |
| PR-004 | LOW | IN-SCOPE | B/G. Shared-checkout safety | V-03 "with E-01 and E-02 reverted"; AGENTS.md shared-checkout rules | The base-run route implied reverting the working tree. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The base run now comes from writing the test before the edit, or from a `git show HEAD:` scratch import. Stash or revert is explicitly forbidden. |
| PR-005 | LOW | IN-SCOPE | G. Live-artifact criteria | Live existing-rule set is 5, not 3; suite baseline was an authoring triple | V-02 diffed against the authoring list and E-01/V-01 against the authoring suite counts, both of which are stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three bars are now before/after re-derivations at execution HEAD. F-08 is annotated with the review value. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where should the new finding be emitted? | A sibling public function sharing one private walk helper, wired into `check_type`'s plans path | Append to `check_lifecycle_transitions` (as authored); edit `test_history_order.py` | `tests/test_history_order.py` fixture (e) equality; the plan's own Scope-Paths exclude that test; "same walk" preserved by the shared helper | yes |
| D-2 | Is about 124 day-one `info` findings acceptable? | Yes. Keep `info`, one finding per plan, and surface the volume in V-04 for the maintainer | Suppress below a threshold; aggregate into one repo-level finding | The volume is the measured blindness the plan exists to expose. `check.scope-drift`'s collapse precedent rejects unprincipled thresholds. Aggregating would lose the per-plan remedy | yes |
