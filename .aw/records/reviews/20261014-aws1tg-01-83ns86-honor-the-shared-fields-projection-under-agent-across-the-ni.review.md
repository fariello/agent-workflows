# Review findings: plan 83ns86

- Subject-Id: 83ns86
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`ef3c1c7e8`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize --agent` clean after revisions.

Re-verified at review HEAD:
- `tests/test_shared_flag_honored.py:54-75` `KNOWN_BROKEN`: 5 `jfdk7p`, 9 `aws1tg`, 4 `4y614a` entries exactly as the plan says; `test_known_broken_citations_resolve` asserts `seen_citations` non-empty (line 377).
- `orchestrator_readiness.run_coverage`: `ctx = context or select_output(args)` (line 727), five `if ctx.is_agent or ctx.is_json:` sites printing `_as.render_jsonl_record(rec)` unfiltered (738/757/818/850/894). `render_agent` (673) is NOT called by `run_coverage`; only caller is `tests/test_orchestrator_child_retired.py:281`.
- `partition.run_partition` (897) ignores `context`; two `if is_agent:` sites (1040 blocked_sets, 1179 ok). Probe: `aw partition -t plans -s approved --agent --fields cmd` emits `commands, cycles, shards, split_components`.
- `cli._dispatch` `oc update-models` builds `forwarded` without `--fields` and calls `oc_models.run(forwarded)` (line ~18096); `oc_models.run` resolves `ctx = select_output(args)`.
- `_StorageReattachResult.to_agent_record` (cli.py ~12373) lacks filtering; `if storage_cmd == "reattach": return _run_storage_reattach(args, term)` (17598). `_run_storage_reattach` already accepts `context` and falls back to `select_output(args)`, so the `--dry-run` branch ALREADY projects (probe: `--fields cmd` drops `findings`/`evidence`). Only the exit-1 branch is broken.
- `upgrade_rehearsal._emit_agent` (1260) builds a namespace without `fields`; call sites: 9 in `upgrade_rehearsal.py` (1296, 1340, 1439, 1465, 1500, 1518, 1527, 1544, 1728) plus 1 in `cli.py` (18217) = 10, not 8.
- `agent_schema.filter_record_fields` (506) and `_PRESERVED_FIELDS` (497) as described.

SAFETY INCIDENT DURING REVIEW: the reviewer's probe `aw oc update-models --agent --fields cmd` (no `--config`, no `--dry-run`) returned `applied:true` and rewrote the operator's `~/.config/opencode/opencode.json` (pricing changes and an added model) and wrote a `.bak`. The reviewer restored the file byte-identically from that `.bak` (`cmp` clean) and kept the rewritten copy beside it as `opencode.json.review-probe-applied.20261015T015607Z`. This is the hazard PR-001 fixes in the plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | B. Security / operability | `oc_models.build_parser` (`--dry-run` to preview, writes by default); `oc_models` config precedence docstring (~line 105); `tests/conformance_matrix._pinned_env` copies `os.environ`; review incident above | E-01, E-04, E-07 and V-04 demand running `oc update-models` / `oc_models.run(["--agent","--fields","cmd"])` with no `--config`, no `--dry-run`, no fetch stub. That writes the operator's real OpenCode config and hits the network, as observed at review. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SAFETY rule in E-01/E-04 and the gate: temp `--config` plus `--dry-run` or `fetch=` stub, isolated `HOME`/`XDG_CONFIG_HOME`; E-07(c) and V-04 rewritten, V-04 demands proof the real config is untouched. |
| PR-002 | MEDIUM | OVER-SCOPE | C. Architecture | `orchestrator_readiness.render_agent` (673); no call in `run_coverage` | E-02 added a `fields` parameter to `render_agent`, which is not on the CLI path, so it is unused surface; E-07(a) tested it instead of the reachable exit-0/1 completion branch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed the `render_agent` change; E-07(a)/V-02 now cover the completion branch via `cli.main` with `runner_shared.ask_orchestrator_probe` patched. |
| PR-003 | MEDIUM | IN-SCOPE | Evidence | `grep -n "_emit_agent("` -> 10 call sites | E-06/F-06/V-06 said "eight call sites" while listing ten; an executor counting to eight could miss two. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected to ten with a re-count command; V-06 demands the pasted count. |
| PR-004 | LOW | IN-SCOPE | Evidence / E. Testing | Probe of `storage reattach --dry-run --agent --fields cmd` | The `--dry-run` `CommandResult` branch already projects, and the exit-1 record carries no `evidence`; E-07(d)/V-05 implied both branches were broken and both drop `evidence`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05, E-07(d), V-05 corrected; the dry-run case kept as a regression guard. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` items 2 and 5 | Gate told the executor to run `aw ipd finalize` unconditionally and phrased the fence as "do not expand scope casually"; OQ-01 `Owner: none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fence restated as a declaration with `--scope-reason`; finalize made conditional on runner vs hand execution; OQ-01 owner `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep or drop the `render_agent(fields=...)` change? | Drop | Keep (unused API) | `run_coverage` never calls `render_agent` | yes |
| D-2 | How should tests reach the `ipd coverage` completion branch without a model call? | Patch `runner_shared.ask_orchestrator_probe` in-process | Live model probe; skip branch | `tests/test_coverage_not_written.py:175` pattern | yes |
| D-3 | How to keep `oc update-models` tests safe? | Temp `--config` plus `--dry-run` or `fetch=` stub, isolated HOME/XDG | Rely on `_pinned_env` (it copies `os.environ`, incl. real HOME) | `oc_models` config precedence; review incident | yes |
