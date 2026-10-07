# Review findings: plan xvi55d

- Subject-Id: xvi55d
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T032734Z-4093657` at HEAD `bf28748b8`. The plan was
committed and byte-identical to the sealed lane input (rev-12); no snapshot needed. `- Kind: child`.
`aw ipd lint --phase author` clean before review. The dependency `qhcojn` is now `executed`, so the plan's
central unknown (OQ-01, Case A vs B) was resolvable from the landed code. The widened predicate was demonstrated
in-process against a scratch repo under `.aw/state/` by monkeypatching `plans_refs._validate_plan_order` (no
source edit). Corpus re-measured: 1313 plans, 85 orchestrators, 0 violating.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Evidence / executability | `plans_refs._validate_plan_order` "`if kind != ipd_schema.KIND_CHILD: return None`"; `tests/test_group_verb_policy.py::_seed_plan_record` signature with `kind=`, `item_dependencies=` | Plan premises were stale after `qhcojn` executed: it said `_seed_plan_record` writes no `- Kind:` (it now does) and that the five guards were absent (three already ship), so an executor would re-edit a shared helper and duplicate tests. Case B is now known. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 records Case B, uses helpers as-is, runs existing guards by node id, adds only the missing tests; F-14 added; conventions/proposed changes/V-01 reconciled. |
| PR-002 | MEDIUM | UNDER-SCOPE | Spec/doc sync / UX | `cli.py` `--order` help "(for plans, Order 0 is refused for a Kind: child; an orchestrator at 0 is permitted)"; `--allow-invalid-order` help "allow assigning Order 0 to a Kind: child plan" | After widening, both help strings misdescribe what the verbs refuse/override; the plan called the edit optional and kept `cli.py` out of scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both help strings and the stale docstrings/comment are required; `cli.py` added to Scope-Paths; V-02 demands `--help` excerpts. |
| PR-003 | MEDIUM | UNDER-SCOPE | E testing | In-process demo: orchestrator `--order 7 --allow-invalid-order` -> rc 0, writes `-07-` | The override now also applies to the orchestrator half; no test covered it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 adds the override arm; V-02 demands the `note: ... overridden rule:` line. |
| PR-004 | LOW | IN-SCOPE | G execution contract | Gate prose | Gate lacked runner/`aw ipd finalize` lifecycle ownership and the "resolved OQs" statement; dependency prose still described it as unmet; `bmhoxe` is now `graduated` to stub `yqv6b7`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Lifecycle clause added, dependency stated as met, V-01 carrier note updated. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Case A or Case B? | Case B: remove the `KIND_CHILD` narrowing | Case A (verify only) | landed `_validate_plan_order`; scratch demo of the widened form | yes |
| D-2 | Correct the help text in this plan? | Yes, required; declare `cli.py` | Leave optional (ships misleading help) | the two help strings quoted in F-14 | yes |
