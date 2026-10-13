# Review findings: plan 6jp1ox

- Subject-Id: 6jp1ox
- Subject-Type: ipd
- Reviewed-At: 2026-10-13
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (LOW, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `95763c6cf`. The pending plan matched the sealed lane input byte for byte and was committed (`78d44e6f1`), so no snapshot commit was needed. `- Kind: orchestrator`. `aw ipd lint --phase author --agent` and `--phase review-finalize --agent` reported `clean` (no `IPD-S407`). `aw ipd coverage 6jp1ox` reported ready with no findings before and after revision (the revision changed coverage-relevant text, so the tool re-probed and re-recorded `Coverage: pass`, fingerprint `b2fb2458390b`).

Verified at review: all four children exist in `pending/` with `- Set: iosmvn`, Orders 1-4 matching the child table; `yuhl6o`, `9rthek`, `ev7t1w` are `reviewed` with `Item-Dependencies: none` and disjoint Scope-Paths; `ellenm` is `to-review` with `executed:yuhl6o, executed:9rthek, executed:ev7t1w`, matching the table. The Set measurement command (quoted in `yuhl6o` Project conventions) over `git ls-files 'agent_workflows/*.py' 'tools/*'` gives `UNRETIRED 88` with per-file counts exactly matching Concern (41 / 19 / 27 across 17 modules / 1 in `tools/lost_guard_census.py`). Sibling carriers: `dtelfb` and `65d5zf` are `approved`, `z2ugxc` (yf1p8y) is `approved` and cites `test_runner_layering` 8 times, `rcp8c4` is executed. Every E-item is pure orchestration (confirm a child executed); no parent-only work.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | G (carrier accuracy) | Plan Deferred row 1 `- Carrier: 3tov52`; Concern names five sibling owners (`dtelfb`, `65d5zf`, `z2ugxc` via `yf1p8y`, executed `rcp8c4`) | The sibling-owned row named a single carrier, `3tov52`, a backlog item already `graduated`, whose plan `65d5zf` owns only three of the excluded basenames. `test_runner_backlog_close.py`/`test_runner_layering.py` (owned by `z2ugxc`) and the `dtelfb` pin were not carried by the cited id. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into rows carrying `65d5zf`, `dtelfb`, `z2ugxc`, and `Carrier-Evidence` naming the executed `rcp8c4` plan. |
| PR-002 | LOW | IN-SCOPE | G (lifecycle accuracy) | Gate "Backlog `iosmvn` is set `graduated` by the runner when the Set is authored"; `.aw/records/backlog/open/...iosmvn...backlog.md` `- Status: open` | The gate stated as fact something that has not happened: the item is still `open`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now states the current status and the graduation and close conditions. |
| PR-003 | LOW | UNDER-SCOPE | G (execution contract) | Gate text | The gate lacked the paste-actual-output honesty rule and an explicit statement about open questions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added both. |
| PR-004 | LOW | IN-SCOPE | Plan-review 3.1 rule 5 | OQ-01 `- Owner: none` | A resolved question needs a real owner; this one was resolved by the author. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `Owner: plan author`. Re-measurement evidence was added to Scope check. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Cite the run-flag-surface cluster as a carrier or as evidence? | `Carrier-Evidence` pointing at the executed `rcp8c4` plan. | `Carrier-Declined`. | Its seven sites already carry `deleted in 19313eed` prose (`runner_shared.py` lines quoting `tests/test_run_flag_surface.py`), so the work is done, not declined. | yes |
