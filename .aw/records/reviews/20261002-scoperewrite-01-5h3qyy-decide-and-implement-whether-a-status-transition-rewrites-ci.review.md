# Review findings: plan 5h3qyy

- Subject-Id: 5h3qyy
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (BLOCKER, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `2dfa36ba7`. The plan was committed (`47218e46f`) and
unchanged, so no snapshot was taken. `aw ipd lint --phase author` was clean. After revision,
`--phase review-finalize` reports only `IPD-M107`, which clears when the review history line is
written, and an `info` `IPD-Z602` on E-09, accepted because that item covers one test file and one
surface. `- Kind: child`.

Re-verified: F-01 (a name-keyed map returns `[]`) and F-02 (a path-keyed map plans `full-name` and
`bare-stem` edits) were reproduced on a scratch repo. The `if old_name == new_name:` guard exists in
`artifact_refs.plan_reference_rewrites_with_warnings`. `widening_is_acceptable` requires
`not removed`. `.aw/state/ipd-lifecycle/` is absent in this lane. Carriers `23p80m` and `ho7qjb`
are open. Backlog `es7wdp` is graduated, `Work-Kind: chore`, with no `Blocks-Release` to inherit.
`DECISIONS.md` ends at D158. CHANGELOG has `## 2.0.0 (pending)`. All three named test files exist.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | C/D (single route claim) | `cli.py` backlog/specs `set` dispatch: `if getattr(args, "status", None) is None: ... status_set.run_set_command` else `backlog_mod.run_set(args)` / `sp.run_set(args)`; `backlog.run_set` `core.atomic_write(dest, rendered)` + `src.unlink()`; `specs.run_set` `core.git_mv(...)` | The plan treats `apply_status_change` as the only setter. The `--status` spellings of `aw backlog set` and `aw specs set` relocate records in their own functions, so the fix would fire for one spelling of a verb and not the other. | C:Medium; U:Low; S:Low; F:Low; Overall:Medium | FIXED | E-05 now wires one shared post-relocation step into all three paths. `backlog.py`, `specs.py` and `cli.py` added to Scope-Paths. F-09 added. Tests (g) and V-05 cover both spellings. |
| PR-002 | BLOCKER | IN-SCOPE | A (data integrity; executed-record rule) | Scratch probe: path-keyed `plan_reference_rewrites` planned edits in `plans/executed/e.ipd.md` and `tests/test_x.py`; `artifact_core.REFERENCE_SCAN_ROOTS = SCAN_ROOTS + (".aw/records/reviews", "tests")`; a three-path declaration probe produced a duplicate `implementing/` entry | Delegating to the bare rewriter would edit executed plans (AGENTS.md forbids this), test source and prose. It would also corrupt the exact F-07 forward declaration the plan says must not be touched. That contradicts F-07 and the plan's own reasoning. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now limits edits to the `Scope-Paths` line of PENDING plans and skips (with a reason) any plan already declaring the destination. F-10 added. Tests (a)-(d) and V-03 updated. |
| PR-003 | HIGH | IN-SCOPE | A/B (fail direction) | `check_engine._receipt_is_live` docstring: "FAIL SAFE ... when liveness cannot be determined ... the receipt is treated as NOT live and skipped"; returns False on an unreachable base | E-04 says to reuse `_receipt_is_live` and also to fail CLOSED (uncertain means skip). The helper fails in the opposite direction, so reusing it would rewrite exactly the uncertain cases the guard must skip. | all Low | FIXED | E-04 now keys on receipt-file presence (`receipt_path_for`), skips a missing `- Id:`, and has no liveness test. F-05 annotated. V-04 demands the fail-closed branches. |
| PR-004 | MEDIUM | UNDER-SCOPE | F (agent output contract) | `status_set.run_set_command` `if ctx.is_agent or ctx.is_json:` emits `CommandResult` with `changes` | E-06 writes free text to stdout unconditionally, which would corrupt the `aw.agent/v1` stream under `--agent`. | all Low | FIXED | E-06 reports through `Change` entries under `--agent`/`--json`. Test (i) and V-06 updated. |
| PR-005 | MEDIUM | UNDER-SCOPE | C (commit integration; flag reach) | `status_set._offer_self_commit(args, repo_root, touched_paths, ...)`; `specs._offer_specs_set_commit`; `ipd_lifecycle` calls `_ss.apply_status_change(wt_rec, "executed", ...)` | The plan does not name the flag, the parsers it goes on, or how rewritten files join `--commit`. It also does not say whether finalize's internal call rewrites. | all Low | FIXED | E-05 names `--rewrite-citations` on five parsers, uses `getattr` with default False so finalize stays off, skips dry runs, and adds the rewritten paths to `touched_paths`. Test (j) and V-05 updated. |
| PR-006 | MEDIUM | IN-SCOPE | G (execution contract) | Gate text; E-01 "stop and report" | There was no conditional runner/hand lifecycle ownership and no scope-fence declaration. E-01's halt was phrased as a stop rule. The gate claimed `Readiness` was absent. | all Low | FIXED | Gate now has conditional ownership and a declaration-style fence. E-01 marks the item `blocked` on disagreement and adds probe (f). Gate readiness text updated. |
| PR-007 | LOW | IN-SCOPE | G (accuracy) | `DECISIONS.md` bullet census: Context 115, Decision 114, Applied 102, Trade-off 8; D158 | E-02 prescribed a "Decision / Alternatives considered / Trade-off" shape that is not the house shape. E-07 bundled two test surfaces, and its (a) contradicted the prose-untouched rule. | all Low | FIXED | E-02 and V-02 use Context/Decision/Applied. E-07 split into helper tests (E-07) and setter tests (E-09, with V-09). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which files may the rewrite touch? | Only the `- Scope-Paths:` line of pending plans; skip plans already declaring the destination. | Every file the planner finds (edits executed plans/tests, corrupts the F-07 declaration); all text in pending plans (rewrites history prose). | Scratch probes (F-10); AGENTS.md executed-record rule; the plan's own F-07. | yes |
| D-2 | What counts as in flight? | A receipt file present for the id6 (parseable or not), or no `- Id:`. | Reuse `_receipt_is_live` (fails toward rewrite); a new liveness test (a second definition). | `check_engine._receipt_is_live` docstring; the plan's own fail-closed rationale. | yes |
| D-3 | Which setter paths are wired? | All three relocating paths through one shared step, with one flag on five parsers. | `apply_status_change` only (spelling-dependent behavior). | `cli.py` dispatch; `backlog.decide_gate_default` docstring on spelling parity. | yes |
| D-4 | Flag name? | `--rewrite-citations`, default off. | No name (left to the executor). | Default-off posture in the plan's Scope (d); OQ-01 leaves flipping the default to the maintainer. | yes |
