# Review findings: plan 6i8knl

- Subject-Id: 6i8knl
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `5077ad1c7`. The plan was committed and unchanged, so no
snapshot was taken. `aw ipd lint --phase author` was clean. `- Kind: child`.

Re-verified against the source: `plans_archive._plan_date` has its anchored regex and its
`return "20260101"`. Both `plan_shard_move` and `sweep_candidates` call it. The set branch uses
`min(set_ages[set_id])`. `_at_disposition_root` requires `len(rel_parts) == 2`. `plans_archive`
imports only `artifact_core` and `plans_index`. `plans_refs._preserved_date` is filename-first and
`plans_refs._plan_date` is a separate copy. `_CLUSTERED_RE` matches the plan's fixture names, and
`_LEGACY_TIMESTAMP_RE` returns `20260723` for the casualty's former name. The live casualty
`executed/20260101-instsafe-07-qrokie-...` exists. `tests/test_plans_archive.py` has 9 tests and
they pass (`9 passed in 0.40s`).

Corpus replay of the proposed tiers, re-measured at review: 1082 terminal plans and 1266 plan records
in total, 0 changed resolved dates. 11 terminal plans have no `- Set:`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | A (input validation) | `artifact_naming._CLUSTERED_RE` uses `(?P<date>\d{8})` and matches `20261399-grp-03-abc123-probe.ipd.md`; `artifact_core.shard_for_date('20261399')` returns `202613`; `is_valid_shard_dirname('202613')` is `True`; `plans_archive._age_days('20261399')` returns `0.0` | The new filename tiers trust any eight digits. An impossible filename date would shelve a plan into a nonexistent month permanently (F-04 stickiness), and its age would be 0, so it would never be swept. That is a new instance of the defect class the plan fixes. | all Low | FIXED | E-03 accepts a filename-tier date only if `strptime("%Y%m%d")` parses it, otherwise it falls through. The front-matter tier is left unchanged, which preserves the 0-changed replay. E-01 adds an impossible-date guard, and V-01/V-03 demand it. |
| PR-002 | LOW | IN-SCOPE | G (execution contract) | POST-GATE LIFECYCLE paragraph; gate "authored `to-review` with NO `- Readiness:`" | The lifecycle paragraph named only the runner case, not the by-hand ownership. The gate text described the pre-review state. | all Low | FIXED | Conditional ownership completed and gate text updated. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the filename tier validate calendar dates? | Yes, via `strptime`, falling through on failure; the front-matter tier is unchanged. | Trust the regex (creates `202613` shards); also tighten the front-matter tier (changes existing answers, breaking the plan's additive guarantee). | Review probe in PR-001; plan F-06 additivity claim. | yes |
