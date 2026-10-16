# Review findings: plan 7hvkk0

- Subject-Id: 7hvkk0
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `38d107d18`. The plan was committed and byte-identical to the lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean`. The plan is a child, not an orchestrator.

Verified (all probes ran in this lane, then were deleted):
- Both failures reproduced: `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py` -> `2 failed, 16 passed`; runner discovery `FileNotFoundError` on `.aw/records/plans/pending/20261015-cleantgt-01-kfnfji-...ipd.md`; kfnfji is in `executed/`.
- F-02 refusal on the unmodified `home_records_env`: `aw index prompts --dir <target> --agent` exit 2, stdout `{"kind":"error","outcome":"cannot-run",...,"diagnostics":[{"location":"records/prompts","rule":"records-dir-missing"}],"next":"aw install ."}`, empty stderr, no `target/.aw/records`, `AW_HOME` empty. Produced by `prompts_index.run_index` (`if not prompts_dir.is_dir():`, `agent_workflows/prompts_index.py:310`) -> `artifact_core.emit_index_missing_dir_refusal` (`agent_workflows/artifact_core.py:1129`). So E-05's assertions are satisfiable as written.
- E-04: pre-creating `project_context.project_records_dir(target, aw_home=aw_home) / "prompts"` makes `aw index prompts` exit 0 and write exactly one `aw_home/projects/<id>/records/prompts/INDEX.json`.
- F-01 author probe also reproduced: the `5acca6ce5` kfnfji text with ids renamed to `hrrun1`/`hrfix` passes `aw show` and `aw oc run start --prepare-only` (exit 0, `Run order (1 item(s)): 01 hrrun1`, row `hrfix 01 hrrun1`). Not needed after PR-001.
- Writing that frozen fixture under `tests/fixtures/` changes no `aw check all` output and `aw show hrrun1` from the repo finds nothing, so it would not leak into scanners. Not needed after PR-001.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | OVER-SCOPE | Rubric C (duplicate paths) / G (sequencing) | `.aw/records/plans/pending/20261016-g9kupi-01-4v8s0m-decouple-test-home-records-runner-discovery-from-the-live-re.ipd.md:9` `- Status: approved`, E-01 rewrites `test_home_records_runner_discovery` with fixture `zq9fx1`; this plan's E-02/E-03 rewrote the same test with a different fixture (`hrrun1`) | An approved plan from a separate backlog item (g9kupi) already owns the runner-discovery fix. Two plans rewrote the same test function with incompatible fixtures, so whichever ran second would fail its own E-01 premise or be overwritten. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed E-02/E-03/V-02/V-03 and the `tests/fixtures/` Scope-Path; carried the work with a `- Carrier: 4v8s0m` deferred row; F-01 marked owned by 4v8s0m. No ordering edge, so the plans stay independent. E-01/E-05/V-01/V-05 tolerate exactly the known runner-discovery failure while 4v8s0m is unexecuted. |
| PR-002 | MEDIUM | UNDER-SCOPE | Durable-carrier rule | `agent_workflows/check_engine.py:9814` `_deferred_section_obligations`; `aw ipd lint --phase pre-transition` reported `check.ipd-uncarried-obligation: 3 obligation(s) ... deferred row 1, deferred row 2, deferred row 3` | The deferred rows had no typed carrier field, so pre-transition lint would refuse the terminal transition. | all Low | FIXED | Added `Carrier-Declined` to the two rejected alternatives and `Carrier: 4v8s0m` and `Carrier: ki6t17, a48b4m` to the handoff rows. Pre-transition lint no longer reports the carrier rule. |
| PR-003 | MEDIUM | IN-SCOPE | Gate / execution contract (2026-09-01 scope-fence ruling) | plan gate: "if one seems to need changing, stop and record why" | The scope fence told the executor to STOP over an out-of-scope edit, which the ruling forbids. It also left out the resolved-OQ statement. | all Low | FIXED | Rewrote it as a declaration: make an out-of-scope edit, then justify it at finalize with `--scope-reason`. Stated that all OQs are resolved. |
| PR-004 | LOW | IN-SCOPE | Rubric G (re-derivation convention) | E-05 expected outcome "`19 passed`" | Used a collected test count as the pass bar. | all Low | FIXED | Changed the bar to zero failures and zero errors, with the count re-derived at execution. |
| PR-005 | LOW | IN-SCOPE | Rubric G (reachability) | V-05 | V-05 did not name the code path that produces the refusal observation. | all Low | FIXED | V-05 names `prompts_index.run_index` -> `artifact_core.emit_index_missing_dir_refusal` and requires the refusal JSON line to be pasted. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which plan should own the `test_home_records_runner_discovery` fix, 7hvkk0 or 4v8s0m? | 4v8s0m, which is already approved and reviewed; 7hvkk0 keeps the prompts index half. | Keep 7hvkk0's frozen-fixture approach and supersede 4v8s0m (REJECTED: discards an approved, demonstrated plan, which is a human-approval decision). Keep both (REJECTED: conflicting edits to one test function). | `.aw/records/plans/pending/20261016-g9kupi-01-4v8s0m-...ipd.md` Status `approved`, OQ-01 demonstrated; backlog g9kupi `Graduated-To: g9kupi`. | yes |
| D-2 | Should 7hvkk0 declare `executed:4v8s0m` as an Item-Dependency? | No. Leave them independent and tolerate the one known failure in the module-level bar. | Hard dependency (REJECTED: needless ordering coupling; the prompts index fix does not need runner discovery). | E-04/E-05 touch only the prompts index tests; the probe showed the prompts fix passes on its own. | yes |
| D-3 | Can backlog 5mnbaz close once only 7hvkk0 executes? | Yes for its gate. 5mnbaz's From-Backlog carrier is 7hvkk0; runner discovery is gated separately through g9kupi -> 4v8s0m (`Blocks-Release: next`). | Add `From-Backlog: 5mnbaz` to 4v8s0m (REJECTED: edits another approved plan; not needed because g9kupi already gates it). | 4v8s0m front matter `- From-Backlog: g9kupi`, `- Blocks-Release: next`. | yes |
