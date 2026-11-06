# Review findings: plan ya4ee4

- Subject-Id: ya4ee4
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This round was reviewed at HEAD `3af87af7e` in a runner review-sweep lane worktree, a non-interactive run. The lane-input
copy (revision 9) is byte-identical to the tracked plan, which was committed and unmodified, so no
pre-review snapshot was needed. `aw ipd lint --phase author` reported clean before the edits, and `--phase review-finalize` reported clean after them.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| E-03 | The policy was verified only through the `tools` map. | The run requires the `tools` map to be all `false` and checks every permission rule after the last deny. Operator `external_directory` rules, which grant nothing once tools are disabled, are tolerated. | PR-001. |
| E-05, V-05 | Validation used the default sanitizer ruleset and refused on `fail` only. | Validation uses `include_warn`, refuses on any finding, and adds an absolute-path rule, so another machine's home path is also refused. | PR-002. |
| E-04 | The runner seam was described as "the `host_runner.RunnerFn` shape plus stdin", and the guard was described as "exactly as" `_assert_probe_spawn_is_permitted`. | The seam is a new `DescribeRunnerFn` with stated exit-code mapping. The run calls the shared guard itself. | PR-003. |
| E-04 | `tool_use` events were detected by a hand-written rule. | Detection reuses `verifier_corroboration.tool_call_from_event`. | PR-004. |
| E-10, V-10 | The clone went to `<tmpdir>`; the plan had no cost cap and no case for missing credentials. | The clone goes to `tmp/ya4ee4-clone` and code is committed first. Spending stops when the first 10 calls cost more than 0.50. Without credentials or network, E-10 is `blocked`, never faked. | PR-005. |
| E-01 | "listed in the sdist `include` list if ..." | The existing hatch targets already ship `agent_workflows/data/`, so no edit is needed. | R1. |
| E-01, E-11, V-11, gate | No baseline step; one commit; a partial gate. | A baseline is saved before E-01. There are two commits, one on each side of E-10. The gate states the full contract. | PR-006. |
| Findings | (none) | F-11 added with the review measurements. | Evidence. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. The plan adds options to `aw migrate metadata` and a shipped prompt file.
2. Yes. It spawns a model host whose permission posture is the safeguard; that safeguard is spec OQ-31.
3. Yes. It has 11 E-items in 5 task groups. The module is new and the wiring goes into `m0001`.
4. Yes. There are 9 Scope-Paths.
5. Yes. A permission leak lets injected record text run tools. A sanitizer gap leaks identifying text into tracked, public fields.

AW-TIER: complex

### Step R1

- Checked and present: `runner_shared.probe_argv`, `probe_reply_text` and `_assert_probe_spawn_is_permitted`; `lane_containment.build_permission_policy_env` and `OPENCODE_RUNTIME_CONFIG_ENV`; `oc_runipd.observe_opencode_policy`; `agy_runipd.run_agy_turn`; `agent_workflows/data/research-models.toml`; and the hatch wheel and sdist targets.
- The F-01 option list matches `opencode run --help` for 1.18.35. F-02 reproduced: 13 tools, all `false`.
- `host_runner.RunnerFn` is `(argv, cwd, timeout)` with no stdin (PR-003).
- The sanitizer does not flag a home path from another machine (PR-002, measured).

### Step R2

- Checked: the E-to-V bijection is 11/11.
- V-03's `opencode debug agent` demonstration is reachable through E-03's `describe_env`. V-10's real trial is reachable only with credentials; when they are absent, the outcome is now `blocked` (PR-005).
- `- Item-Dependencies: executed:dcerjg` is correct, because the seam, census and journal directory are `dcerjg`'s.

### Step R3

- Checked: the tool-less call has two layers. The first is the inline agent with every tool disabled, verified before use. The second is a read-only scratch working directory. The permission verification is now honest about the operator's merged rules (PR-001).
- Prompt text is sent on stdin, so it is not visible in the process list.
- The real spawn is guarded under pytest.
- Validation now matches `tve77h`'s writer rules, so a value cannot pass here and fail at the migration writer, and planted paths from any machine are refused (PR-002).
- Antigravity is refused as a host, as OQ-31 requires.
- Spending is capped, and the provider sentence is shown in the dry-run header (3c).

### Step R4

- A: the journal appends a line, calls `fsync`, and reads the last line per key; a test covers a truncated line. Reuse of entries is digest-gated on both the source and the prompt.
- C: the design reuses `probe_reply_text`, the spawn guard, `build_permission_policy_env` semantics and the tool-event parser (PR-004). It adds no runner mode.
- E: fake-host tests exercise the real argv, env and parsing path.
- Spec sync: no spec change, which is truthful; this is the prompt file that the spec names.

### Step R5

- Checked through the eight personas:
  - QA: there is a test for each refusal reason.
  - Security architect: two layers plus verification.
  - Power user: `--describe-limit` spreads the cost across runs.
  - Novice: refusal messages name OQ-31.
  - Stakeholder: real cost is measured before the cutover, and spending is capped.

### Step R6

- Checked: 11 E-items, each with one concern. No split is needed.

### Step R7

- Checked dependencies across the Set:
  - `dcerjg` provides the `describer` seam, the census rows for absences, and the m0001 journal directory under `state_durable`.
  - `dcerjg` E-13 refuses on sanitizer `fail` only for logs and mirrors, and this plan refuses on any finding for descriptions. These rules are consistent because the stricter rule applies first.
  - `tve77h` E-03 (b) refuses `warn` findings and absolute paths in written strings. This plan now matches that rule (PR-002).
  - `cxxmyv` OQ-02 chooses the model from E-10's table, so E-10 must not be faked (PR-005).
  - `xexn45` writes the `--summary` path for creating commands; that is a separate writer.

### Step S5

- Checked: OQ-01 to OQ-04 are resolved and non-blocking. OQ-02 carries `Owner: maintainer` and cites the maintainer's answer recorded in `cxxmyv` OQ-02. No new question for the human.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | R3 / R1 | Measured `opencode debug agent aw-describe`: the permission list ends `('*','deny','*')` twice, then an operator `external_directory` `allow` rule | Checking only `tools` ignored the merged permission list. A strict "nothing after deny" check would also refuse every run on this machine, because the operator's own config adds a later rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both checks apply. Later rules that grant nothing with tools disabled are tolerated, and any other later `allow` refuses. Both outcomes are tested. |
| PR-002 | HIGH | IN-SCOPE | R3 / R7 | Measured: `scan_text("see /home/alice/secret")` gives no finding with either ruleset; `tve77h` E-03 (b) refuses `warn` findings and absolute paths | Validation would accept a planted home path from another machine, which spec AC-36 case 7 requires to be refused. It would also accept values that `tve77h`'s writer then refuses. | Low | FIXED | `include_warn`, refusal on any finding, and the absolute-path rule. Six refusal tests. |
| PR-003 | LOW | IN-SCOPE | R1 | `host_runner.RunnerFn = Callable[[Sequence[str], str, float], ...]` | The seam was described as an existing type that has no stdin parameter. | Low | FIXED | `DescribeRunnerFn` with exit-code mapping, and a call to the shared guard. |
| PR-004 | LOW | IN-SCOPE | R4 C | `verifier_corroboration.tool_call_from_event`; `run_dashboard` "tool_use" | A second hand-written tool-event detector could drift from the shared one. | Low | FIXED | The shared parser is reused. |
| PR-005 | MEDIUM | IN-SCOPE | R2 G / R3 | E-10 `<tmpdir>/copy`, with no cost cap and no case for missing credentials; `cxxmyv` OQ-02 depends on its output | The trial could not run inside a lane workspace, could overspend, and could be faked when no credentials exist. | Low | FIXED | Clone in `tmp/`, code committed first, a 0.50 cap, and `blocked` when real calls are impossible. |
| PR-006 | MEDIUM | UNDER-SCOPE | S7 contract | V-11 asks for "totals before E-01" without a capture step; the gate | No baseline step existed. The commit order conflicted with E-10. The gate was partial. | Low | FIXED | Baseline captured in E-01, two commits, and the full gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How strict is the permission verification? | `tools` all false, and no later grant except operator `external_directory` rules | `tools` only (ignores permissions); nothing after deny (refuses every run here) | Measured F-11 | yes |
| D-2 | Which sanitizer threshold applies to descriptions? | Any finding, plus an absolute-path rule | `fail` only (misses other-machine paths and host names) | `tve77h` E-03 (b); AC-36 case 7; measured F-11 | yes |
| D-3 | What happens to E-10 without credentials? | `blocked`; never use the fake host | Run the fake host and report it | `cxxmyv` OQ-02 needs real outputs | yes |
