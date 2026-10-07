# Review findings: plan 5xq2ng

- Subject-Id: 5xq2ng
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
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

## Round 2

Re-reviewed 2026-10-07 at HEAD `fe2ee961c` in an isolated review lane. The plan was committed and byte-identical
to the lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent` was clean before semantic review
and `--phase review-finalize` was clean after revision.

Reproduced (gitignored probe under `.aw/state/`, replaying `check_lifecycle_transitions`' own loop over
`ipd_lifecycle._plan_status_event_groups`; no production edit):
- Live pending tree: 137 plans with history, 104 validated transitions, 62 multi-status zero-coverage plans (all 62
  contain an `ordered=False` group), 18 single-status zeros. The same <=1-day collapse: 104 -> 68 validated, 21 plans
  lose all coverage. Thesis holds.
- `check_lifecycle_transitions` live: 0 findings (round 1: 5).
- `aw check plans`: `errors 23 warnings 2 info 78`.
- One-date fixture groups to `[('2026-09-02', [approved, reviewed, to-review, draft], False)]`; two-date fixture
  to two `ordered=True` groups.
- `5ivkdh` and `9wcei0` are in `executed/`; `rfyrvp` is in `superseded/` (superseded by `9wcei0`, 2026-10-03);
  `ayhveg` and `qjm4bg` remain `to-review` in `pending/`. Spec `2vev8j` is `approved`; `record_history.py` has no `seq`.
- The existing call site lives in `check_engine.check_content`'s plans branch (`agent_workflows/check_engine.py:1494-1501`),
  which `check_type` composes (`:3971`), not in `check_type` itself.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | MEDIUM | IN-SCOPE | G. Evidence currency | `.aw/records/plans/executed/*5ivkdh*`, `executed/*9wcei0*`, `superseded/*rfyrvp*` | Deferred list, OQ-01 and spec-sync prose described the clock fix as in flight across five plans and `rfyrvp` as an owner. `5ivkdh` and `9wcei0` have executed and `rfyrvp` is superseded. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Deferred rows, OQ-01 and spec-sync now state the executed/superseded status, and say the window is open now rather than anticipated. |
| PR-102 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | Probe counts above | F-04/F-06/F-08 and E-01/E-02/E-03 prose carried round-1 counts (124/184, 5 findings). Live is 62/137 and 0 findings; the existing-rule set moves both ways. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Second-review measurements added as context. Every bar is still re-derived at execution, and F-08 notes that a zero set is the case only the new rule can distinguish. |
| PR-103 | LOW | IN-SCOPE | G. Executability / citation | `agent_workflows/check_engine.py:1494-1501` (`check_content`), `:3927` (`check_type`) | E-02 and Proposed change 2 said to wire the sibling into `check_type`. The neighbour call sits in `check_content`'s plans branch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both sites now name `check_content`'s plans branch by its anchor comment and note that `check_type` composes it. |
| PR-104 | MEDIUM | IN-SCOPE | E. Evidence feasibility | `artifact_core.drift_exit_code` (`agent_workflows/artifact_core.py:692-702`); `check_content` runs `check.ipd-lint-diagnostic` and other rules over every fixture plan | E-03, V-03 and Required tests demanded "a run whose only finding is the new rule exits 0". A fixture plan swept by `check_type` may trip other rules, so the demand is not reliably constructible. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with the canonical two-limb proof: `rule_spec(...).severity == "info"`, and `drift_exit_code` over the sibling's enriched findings returning 0 versus 1 with severity swapped to `error`. A whole-CLI exit 0 is optional. |
| PR-105 | LOW | UNDER-SCOPE | D. Anti-regression | `tests/test_check_engine.py:1738`, `tests/test_check_engine_from_spec_missing.py:548-585`, `tests/test_carrier_reverse_lookup.py:83-120`, `tests/test_work_gate_severity.py:150` | The new finding reaches every `check_content(repo, "plans")` caller, and the plan did not say so. The callers read at review filter by rule or by warning/error severity. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names the collateral surface. The bare-suite failure-set diff is the proof, and any moved undeclared test is reported by node id rather than edited. |
| PR-106 | MEDIUM | IN-SCOPE | G. Execution contract | Gate section; plan-review Step 4 scope-fence ruling of 2026-09-01 | Four problems in the gate. It said the plan "carries no Readiness" (now false). It had no paste-the-actual-output rule. Its scope fence and Scope check carried a STOP directive for the scope question. It told the executor to perform the terminal move unconditionally. OQ-01 recorded `Owner: none` on a resolved question. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now says Readiness belongs to the review. It adds the paste rule. The fence is a declaration reconciled via `--scope-reason`/`--scope-ack`, and an underivable signal marks E-02 `blocked`. Finalize ownership is conditional: the runner when one is in use, otherwise `aw ipd finalize`, and never `git mv`. OQ-01 owner is `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the exit-0 property be proven when a fixture cannot guarantee a single finding? | Use the canonical two-limb registry-severity + `drift_exit_code` contrast, with the CLI exit as an optional third limb | Keep the whole-CLI single-finding demand; drop the exit proof | plan-review rubric G "Canonical no-error-added proof shape"; `artifact_core.py:692-702` | yes |
| D-2 | What should an executor do if the signal cannot be derived without editing the classifier? | Mark E-02 `blocked` with the reason and do not edit `ipd_lifecycle.py` | STOP and report (prior wording); widen scope | plan-review Step 4 scope-fence ruling (stop directives reserved for unsafe conditions); producer already exposes date/members/ordered, verified by fixture replay | yes |
