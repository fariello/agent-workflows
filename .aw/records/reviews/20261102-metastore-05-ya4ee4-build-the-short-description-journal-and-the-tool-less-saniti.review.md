# Review findings: plan ya4ee4

- Subject-Id: ya4ee4
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-4-carbon
- Verdict: REVIEWED - OPEN QUESTIONS

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


## Round 2

Re-reviewed at `HEAD` `1f099cb9b` (`2026-11-14`) in isolated worktree lane `review-sweep-run-20261114T011656Z-594596` after the `2026-11-07` maintainer demotion (`approved -> to-review` for spec `4sd62s` C12 / 5.2a any-repository migration), the `2026-11-07` and `2026-11-09` splits of `ya4ee4` into `odeo9z` and `830wku`, and the `2026-11-12` OpenCode v2 (`v2.2.7`) host cutover (`a518d6863`, `05afdf32c`). Working tree was clean at review start (pre-review snapshot commit skipped unchanged). `aw ipd lint --phase author --agent` reported `clean` (`2` `IPD-C802` em-dash advisories) before edits and `clean` (`0` findings) after edits; `aw ipd lint --phase review-finalize --agent` reported `clean` (`0` findings).

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter (`Concern`, `Scope`, `Item-Dependencies`) | Cited only `odeo9z` and `dcerjg`, omitted `830wku` and `g5hpbb`, and assumed OpenCode v1 (`1.18.35`) and `.aw/records/` only. | Adds `executed:830wku, executed:g5hpbb`, updates `Scope` for `830wku` (`validate`), OpenCode v1/v2 compatibility (`F-12`), and `4sd62s` 5.2a C12 shapes (`g5hpbb` deferral). | PR-007, PR-009. |
| Callout, Checklist intro (`lines 40-44`), `Deferred` | Missing technical-writing callout; multi-line bullet block pasted inside single backticks on lines 40-44 while `Deferred` omitted `odeo9z` and `830wku`; claimed `.aw/state/ya4ee4/check-before.jsonl` comes from `odeo9z`. | Adds technical-writing callout; replaces broken inline-code paste with clean prose and adds `Carrier: odeo9z`, `Carrier: 830wku`, and `Carrier: g5hpbb` under `Deferred`; captures `check-before.jsonl` in `E-07`. | PR-011, PR-013. |
| `E-07`, `V-07`, `OQ-01`, `F-12` | OpenCode v1-only policy (`OPENCODE_CONFIG_CONTENT` and `debug agent`); no `PYTEST_CURRENT_TEST` handling in `describe_all`; no C12 unclassifiable-file exclusion or shape-c/layout key rule. | Adapts `m0001_describe.py` to OpenCode v1 and v2 (`opencode_cli.is_v2`, `adapt_run_argv`, `0o400` `<scratch_dir>/opencode.json` in `0o500` `scratch_dir`, `debug agents`); checks `_assert_probe_spawn_is_permitted` in `describe_all` as `could-not-ask` (`pytest-spawn-refused`) while `generate` raises `DriverError`; restricts description inputs to `m0001_discover`-classified convertible records across C12 shapes. | PR-007, PR-008, PR-009, PR-011. |
| `E-08`, `V-08` | Recorded default model "as reported by the `step_finish` event or the argv" and left CLI dispatch implicit. | Resolves omitted `--describe-model` via `oc_models.resolve_host_default_model` (`step_finish` carries no model id) and routes CLI options through `m0001_describe.Describer` into `chain.Migration.run(..., describer=describer)`. | PR-008, PR-010. |
| `E-09`, `V-09`, `E-10`, `V-10`, `E-11`, `V-11` | `fake_host.py` handled only `run`; `E-09` omitted OpenCode v2 and C12 corpus shapes; `V-10` checked only `"type":"tool_use"`; `E-11` ran 3 modules. | `fake_host.py` answers `--version`, `debug agent`, `debug agents`, and `run`; `E-09` tests v1/v2 policy, v2 `tool` (`shell`) events, `idless_prose` (with unclassifiable file), `legacy_agents_layout`, and `companion_backend`; `V-10` checks `tool(_use)?`; `E-11`/`V-11` add `test_m0001_any_repo.py`, `test_migrate_cli.py`, and the 3 CLI conformance suites. | PR-007, PR-008, PR-009. |
| `Step 0`, `Findings`, `Proposed changes`, `Spec / documentation sync`, `OQ-05`, `Validation`, `Gate` | Bare `module.func` citations, unescaped `\|` in `F-03`, two em dashes (`IPD-C802`), no flowchart, false claim that `ya4ee4` writes the prompt file and `90iqr1` documents `aw migrate metadata`, and no prerequisite stop rule. | Upgrades citations to `path::Symbol`, escapes `\|` in `F-03`, removes em dashes, adds Requirement 12 `flowchart TD`, attributes the prompt file to `odeo9z` E-01, raises non-blocking `OQ-05` (`PR-012`), and adds prerequisite/conflict stop rule. | PR-012, PR-013. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| ISSUE-01 | `Spec / documentation sync`, `OQ-05` | `ya4ee4` stated operator documentation lands with `90iqr1`, while neither `90iqr1` nor `qhay6a`, `a49djh`, `y1zihp`, or `ngc2a2` documents `aw migrate metadata` or `--describe-*`. | Which plan carries user-facing prose documentation for `aw migrate metadata` and its `--describe-*` / `--no-describe` options (aligned with `1vfqdu` `OQ-08`). | Add `aw migrate metadata` and its `--describe-*` / `--no-describe` options to the `y1zihp` cutover docs patch; `ya4ee4` ships `--help` and `CHANGELOG.md`. | medium |

### Step T

1. Yes. Adds four CLI flags (`--describe-host`, `--describe-model`, `--describe-limit`, `--no-describe`) to `aw migrate metadata` and extends `m0001_describe` and `m0001_metadata_v2.run`.
2. Yes. Spawns an external model host (`opencode`) whose tool-denial posture on both v1 and v2 enforces spec `4sd62s` OQ-31.
3. Yes. Five `E-*` items spanning `m0001_describe.py`, `m0001_metadata_v2.py`, `cli.py`, fake-host subprocess harnesses, C12 corpus integration, and a live clone trial.
4. Yes. Six work files in `- Scope-Paths:` plus cross-plan interfaces with `830wku`, `odeo9z`, `1vfqdu`, `dcerjg`, `g5hpbb`, and `cxxmyv`.
5. Yes. A permission regression allows prompt-injected record text to execute tools (`shell`, `write`, `edit`), an unhandled `DriverError` under `PYTEST_CURRENT_TEST` breaks core CLI conformance suites, and C12 discovery/key mismatches either strand prior-format repositories or send unclassifiable files to an external model.

AW-TIER: complex

### Step R1

- Verified live against `opencode v2.2.7` (`2026-11-14`): `opencode run` dropped `--dir` (`agent_workflows/opencode_cli.py::adapt_run_argv`), `opencode debug` dropped singular `agent` (leaving `agents`, `config`, `heap-dump`, `paths`), and `OPENCODE_CONFIG_CONTENT` is ignored (`PR-007`, `F-12`).
- Verified empirically in a `0o500` scratch directory holding a `0o400` `opencode.json` beneath an ancestor `opencode.json` with `shell: allow`: `opencode debug agents` (`cwd=scratch_dir`) resolves `aw-describe` (`keys: ['hidden', 'id', 'mode', 'name', 'permissions', 'request']`) with two `{"action": "*", "resource": "*", "effect": "deny"}` rules placed after the ancestor `shell: allow` rule, followed only by `effect: "deny"` rules (`PR-007`).
- Verified in `agent_workflows/runner_shared.py::COST_NOT_RECOMPUTED_HERE` comment: all 32,333 measured `step_finish` parts carry `{id, reason, snapshot, messageID, sessionID, type, tokens, cost}` and never a model id, while `agent_workflows/oc_models.py::resolve_host_default_model` resolves OpenCode's configured default model (`PR-010`).
- Verified all other Step 0 and `E-*` symbols exist: `runner_shared.probe_argv`, `probe_reply_text`, `_assert_probe_spawn_is_permitted`, `ask_orchestrator_probe`; `opencode_cli.is_v2`, `adapt_run_argv`, `normalize_event`; `verifier_corroboration.tool_call_from_event`; `lane_containment.OPENCODE_RUNTIME_CONFIG_ENV`, `build_permission_policy_env`, `antigravity_posture_record`; `oc_runipd.observe_opencode_policy`; `agy_runipd.run_agy_turn`; `tests/test_agy_skip_permissions_default.py`; `attention_contract.refuse_unsafe_descriptive`; `leak_sanitizer.scan_text`, `build_ruleset`; `model_vocab.load`; `project_context.resolve_project_context`; `platform_lock`; `cli._build_parser`; `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation`.

### Step R2

- Bijection: `E-07`..`E-11` <-> `V-07`..`V-11` (5/5, IDs `E-01`..`E-06` reserved for items moved to `odeo9z` and `830wku`).
- Dependencies: `- Item-Dependencies: executed:dcerjg, executed:830wku, executed:odeo9z, executed:g5hpbb` is acyclic (verified via `rg -n "executed:ya4ee4" .aw/records/plans/pending/`: every downstream plan depending on `ya4ee4` already depends on `g5hpbb`, and neither `g5hpbb` nor its parts depend on `ya4ee4`).
- Cross-lane baseline fix (`PR-011`): `.aw/state/` is gitignored and isolated worktree lanes do not share `.aw/state/ya4ee4/check-before.jsonl` written by `odeo9z`, so `E-07` captures its own pre-edit `aw check --agent` baseline.
- Runtime reachability: `V-07` and `V-08` reach `cli._build_parser` -> `chain.Migration.run` -> `m0001_metadata_v2.run` -> `m0001_describe.describe_all` against `fake_host.py` (which now answers `--version`, `debug agent`, `debug agents`, and `run`); `V-10` runs in `tmp/ya4ee4-clone` and records `blocked` with `could-not-ask` when credentials or network are absent.

### Step R3

- Dual-layer tool-less containment holds on both OpenCode v1 (`OPENCODE_CONFIG_CONTENT` + `debug agent`) and OpenCode v2 (`0o400` `<scratch_dir>/opencode.json` inside `0o500` `scratch_dir` + `debug agents` + `adapt_run_argv`), verified lazily before the first uncached model call (`PR-007`).
- Tool-event backstop covers both v1 `tool_use` and v2 `tool` (`shell`, `edit`, `write`, `read`, `execute`) events via `verifier_corroboration.tool_call_from_event` (`05afdf32c`) plus `event.get("type") in ("tool_use", "tool")`.
- Pytest token-spend guard (`PR-008`): `m0001_describe.generate(..., runner=None)` raises `runner_shared.DriverError` directly (`E-09(f)`), while `describe_all(..., runner=None)` checks `_assert_probe_spawn_is_permitted` before any `opencode debug` or `run` spawn and classifies `DriverError` as `could-not-ask` (`pytest-spawn-refused`), spawning zero subprocesses under `PYTEST_CURRENT_TEST` while keeping `--apply` refused if a test forgets to inject `runner`/`describer`.
- Unclassifiable `.md` files (`3g20ms` E-02) are excluded from `describe_all` so arbitrary unrecognized files in foreign repositories are never exfiltrated to a model provider (`PR-009`).

### Step R4

- A & D (Interfaces & callers): `cli.py` constructs `m0001_describe.Describer` (validating `--describe-host` immediately so `agy` fails closed before preflight/scratch) and passes `describer=describer` through `chain.Migration.run` (`1vfqdu` E-01, `g8na48` E-01) without importing `m0001_metadata_v2`. Subprocess CLI preview runs under `test_agent_surface_conformance_mutation["migrate metadata"]` complete cleanly without exemptions (`PR-008`).
- C (Reuse): Reuses `opencode_cli.is_v2` and `adapt_run_argv`, `oc_models.resolve_host_default_model`, `verifier_corroboration.tool_call_from_event`, `runner_shared._assert_probe_spawn_is_permitted` and `probe_reply_text`, and `tests/migration_corpus.py`.
- Right-sizing: 5 `E-*` items and 6 work `- Scope-Paths:` files, within the followability guidance.
- Spec & documentation sync: Fixed false claim that `ya4ee4` writes `short-description-prompt.md` (`odeo9z` E-01 owns it) and escalated missing user-docs carrier as non-blocking `OQ-05` (`PR-012`).

### Step R5

- QA: `E-09` covers AC-36 cases 3, 4, 5, and 7, OpenCode v1 and v2 `debug` outputs and tool events, C12 corpus shapes (`idless_prose` with unclassifiable file, `legacy_agents_layout`, `companion_backend`), and the `generate` vs `describe_all` pytest guard; `E-11` runs 8 targeted suites plus bare `python3 -m pytest`.
- Security architect: `0o400` `<scratch_dir>/opencode.json` inside `0o500` `scratch_dir` overrides ancestor `opencode.json` `allow` rules on OpenCode v2 and is verified before calling; prompt stays on stdin; unclassifiable files are never sent.
- Operator / Stakeholder: `--describe-limit` and `descriptions.jsonl` spread cost across runs; `E-10` enforces a `0.50` cap on the first 10 calls and marks `blocked` honestly in credential-less lanes; `3c` provider notice names the resolved default model.

### Step R6

- Checked: 5 `E-*` items (`E-07`..`E-11`) and 6 work `- Scope-Paths:`; each item addresses one cohesive deliverable and needs no further split.

### Step R7

- Cross-plan contracts checked across `metastore`:
  - `g5hpbb` (`20261107-metastore-14-g5hpbb-...:87-88`) deferred short-description generation for other repositories to `Carrier: ya4ee4`; `E-07` and `E-09(e)` now fulfill that obligation across `3g20ms` (`m0001_discover`, shape `c` id-less prose, unclassifiable files) and `bv4kkj` (stage-1 `.agents/` layout scratch, companion/home `records_root`), ordered after `executed:g5hpbb` (`PR-009`).
  - `1vfqdu` E-01 (`cli.py`) dispatches `aw migrate metadata` through `chain.Migration.run(..., describer=...)` (`g8na48` E-01) and leaves `describer=None` on bare `aw migrate` (E-02) and `aw install --migrate` (E-03); `E-07` defaults `describer=None` to `Describer()` so post-cutover `aw install --migrate` and bare `aw migrate --apply` generate descriptions in production while recording `could-not-ask` under pytest unless a test injects `runner`/`describer` (`PR-008`).
  - **Upstream sibling alert (`odeo9z`):** `odeo9z` E-03 and V-03 (`20261107-metastore-20-odeo9z-...:50,146`) still hardcode the OpenCode v1 command `OPENCODE_CONFIG_CONTENT=... opencode debug agent aw-describe` and `--dir`, which fail on the installed `opencode v2.2.7` binary (`F-12`). `ya4ee4` E-07 adapts `m0001_describe.py` if `odeo9z` has not already done so, and `odeo9z` should be updated in its own `/plan-review` before `odeo9z` executes on an OpenCode v2 machine.
  - **Sibling carrier notes (`90iqr1`, `63ib9r`):** `90iqr1` line 83 still lists `Carrier: ya4ee4` for `short-description-prompt.md` (moved to `odeo9z` E-01), and `63ib9r` row 05's summary column lists `executed:dcerjg, executed:odeo9z` (informational; runner reads child front matter).

### Step S5

- `OQ-01`..`OQ-04` remain resolved (`OQ-01` updated with measured OpenCode v2 `F-12` facts).
- One new question (`OQ-05`, `- Blocking: no`, `- Status: open`, `- Owner: maintainer`, `- Finding: PR-012`) is recorded for human scope/timing decision on which plan carries prose user documentation for `aw migrate metadata` and its `--describe-*` / `--no-describe` options (matching `1vfqdu` `OQ-08`; recommended `y1zihp` cutover docs patch, strength `medium`).

### Pass 2

- Re-read modified `ya4ee4` end to end after edits (`HEAD` `1f099cb9b` working tree) against `.aw/system/workflows/technical-writing/technical-writing.md` and R1-R7: `aw ipd lint --phase author --agent` returned `clean` (`0` findings), all citations resolve, Mermaid diagram quotes special-character node labels, table pipes are escaped, and no regression or new finding appeared.
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-007 | BLOCKER | IN-SCOPE | R3, R4-A, R1 / E-07, E-09, OQ-01, F-12 | Measured on `opencode v2.2.7` (`2026-11-14`) and `agent_workflows/opencode_cli.py`: `opencode run` dropped `--dir`, `opencode debug` dropped singular `agent` (leaving `agents`, `config`, `heap-dump`, `paths`), and `OPENCODE_CONFIG_CONTENT` is ignored; empirically verified that a `0o400` `<scratch_dir>/opencode.json` inside `0o500` `scratch_dir` makes `opencode debug agents` (`cwd=scratch_dir`) resolve `aw-describe` with two wildcard `deny` rules after any ancestor `allow` rule | Without OpenCode v2 support in `agent_workflows/migrations/m0001_describe.py`, every call on the installed `opencode v2.2.7` host fails policy verification (`could-not-ask`) or fails on `--dir`, blocking `E-10` and `cxxmyv`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `E-07` adapts `m0001_describe.py` to OpenCode v1 and v2 via `opencode_cli.is_v2` and `adapt_run_argv`, `<scratch_dir>/opencode.json` (`0o400` in `0o500` `scratch_dir`), `opencode debug agents`, and `verifier_corroboration.tool_call_from_event` + `type in ("tool_use", "tool")`; `E-09` tests both generations; `F-12` and `OQ-01` updated; `odeo9z` V-03 flagged in R7. Recommendation strength: very strong. |
| PR-008 | HIGH | IN-SCOPE | R4-D, R7 / E-07, E-08, E-09, E-11 | `agent_workflows/runner_shared.py::_assert_probe_spawn_is_permitted` raises `DriverError` under `PYTEST_CURRENT_TEST`; `tests/test_agent_surface_conformance.py::test_agent_surface_conformance_mutation` runs `aw migrate metadata --agent` under `PYTEST_CURRENT_TEST`; `1vfqdu` E-01 dispatches `cli.py` via `chain.Migration.run` without importing `m0001_metadata_v2`; `V-07` drives `aw migrate metadata` with `fake_host.py` | Letting `DriverError` escape `describe_all` crashes subprocess CLI dry runs in `test_agent_surface_conformance_mutation` and `test_m0001_roundtrip.py`; `cli.py` dispatch through `Migration.run` was unspecified; `fake_host.py` lacked `--version` and `debug` handlers needed by `V-07`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `generate(..., runner=None)` still raises `DriverError` (`E-09(f)`), while `describe_all(..., runner=None)` checks `_assert_probe_spawn_is_permitted` before the lazy policy probe and classifies `DriverError` as `could-not-ask` (`pytest-spawn-refused`) with zero spawns; `E-08` routes `Describer` through `chain.Migration.run`; `fake_host.py` handles `--version`, `debug agent`, `debug agents`, and `run`; `E-11` runs `test_migrate_cli.py` and the 3 CLI conformance suites. Recommendation strength: very strong. |
| PR-009 | HIGH | IN-SCOPE | R7, R2 / Front matter, Scope, E-07, E-09, E-11 | `ya4ee4` history `2026-11-07` (re-review against `4sd62s` C12 / 5.2a); `g5hpbb` lines 87-88 (`Carrier: ya4ee4` for other repositories); `3g20ms` E-01/E-02 (`m0001_discover`, shape `c` id-less prose, unclassifiable files); `bv4kkj` E-01 (stage-1 layout scratch, companion/home `records_root`); `830wku` (`validate` split) | `ya4ee4` omitted `executed:830wku` and `executed:g5hpbb`, did not exclude `3g20ms` unclassifiable `.md` files from `describe_all` or missing-description refusals, and specified pre-rename keys only for Order 04 mints rather than C12 shapes (a)-(e). | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added `executed:830wku, executed:g5hpbb`; `E-07` restricts `describe_all` to `m0001_discover`-classified convertible records under the resolved `records_root` after stage-1 layout scratch and keys all minted-id records by pre-rename resolved-records-root-relative path; `E-09(e)` tests `idless_prose` (with unclassifiable file), `legacy_agents_layout`, and `companion_backend`; `E-11` runs `test_m0001_any_repo.py`. Recommendation strength: strong. |
| PR-010 | MEDIUM | IN-SCOPE | R1, R4-C / E-08 | `agent_workflows/runner_shared.py::COST_NOT_RECOMPUTED_HERE` comment (32,333 `step_finish` parts carry `{id, reason, snapshot, messageID, sessionID, type, tokens, cost}` and never a model id); `agent_workflows/oc_models.py::resolve_host_default_model` | When `--describe-model` is omitted, neither `argv` nor `step_finish` carries a model id, so `E-08` could not name the model in the `3c` dry-run header or `descriptions.jsonl`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `E-08` resolves omitted `--describe-model` via `oc_models.resolve_host_default_model(env=child_env, cwd=repo, agent="aw-describe")` (`default.model` when resolved, else `"host-default"`). Recommendation strength: strong. |
| PR-011 | MEDIUM | IN-SCOPE | R2, R4-A / E-07, E-11, V-11 | `.aw/.gitignore` (`state/` is gitignored); isolated lane execution (`odeo9z` and `ya4ee4` run in separate worktrees); `g8na48` E-01 precedent | `.aw/state/ya4ee4/check-before.jsonl` written in `odeo9z`'s lane is absent in `ya4ee4`'s worktree, causing `E-11`/`V-11` to fail with `FileNotFoundError`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `E-07` captures `.aw/state/ya4ee4/check-before.jsonl` before `ya4ee4`'s first edit. Recommendation strength: very strong. |
| PR-012 | MEDIUM | UNDER-SCOPE | R4 Spec and documentation sync | `odeo9z` E-01 (owns `short-description-prompt.md`); `rg -n "migrat\|describe"` across `90iqr1`, `qhay6a`, `a49djh`, `y1zihp`, `ngc2a2` (no `aw migrate metadata` or `--describe-*` user docs); `1vfqdu` `OQ-08` | `Spec / documentation sync` falsely stated `ya4ee4` writes `short-description-prompt.md` and `90iqr1` documents `aw migrate metadata`; no plan carries prose user docs for `aw migrate metadata` and `--describe-*`. | C:Low; U:Medium; S:Low; F:Low; Overall:Medium | OPEN | Corrected prompt-file owner citation to `odeo9z` E-01 and raised non-blocking `OQ-05` (`Owner: maintainer`, aligned with `1vfqdu` `OQ-08`). Documenting `aw migrate metadata` before the cutover invites users to convert repositories into a format phase-A readers cannot read, so carrier and timing belong to the maintainer; recommended `y1zihp` cutover docs patch (strength: medium). |
| PR-013 | LOW | IN-SCOPE | Proofreading, R1, S7 / Checklist intro, Deferred, Gate, Validation, Proposed changes | `ya4ee4` lines 40-44 (multi-line block inside single backticks; `Deferred` missing `odeo9z` and `830wku`); `aw ipd lint` (`2` `IPD-C802` em dashes); `technical-writing.md` Req 12 (b) | Malformed inline-code block, missing `odeo9z`/`830wku` carrier rows, missing prerequisite stop clause, bare `module.func` citations, unescaped `\|` in `F-03`, two em dashes, and no flowchart. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Repaired prose and `Deferred` carriers, added technical-writing callout, `flowchart TD`, `path::Symbol` citations, escaped `\|`, plain punctuation, and prerequisite/conflict stop rule. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-4 | How does `m0001_describe` enforce a verified tool-less agent on OpenCode v2 (`v2.2.7`), which ignores `OPENCODE_CONFIG_CONTENT` and dropped `run --dir` and `debug agent`? | Detect v2 via `opencode_cli.is_v2`, adapt argv via `opencode_cli.adapt_run_argv`, write a `0o400` `<scratch_dir>/opencode.json` inside the `0o500` `scratch_dir` with v2 wildcard `deny` rules, and verify via `opencode debug agents` (`cwd=scratch_dir`) while keeping v1 `OPENCODE_CONFIG_CONTENT` + `debug agent` | Keep `OPENCODE_CONFIG_CONTENT` only (rejected: ignored on `v2.2.7`, every call becomes `could-not-ask`); drop v1 support (rejected: breaks OpenCode 1.18.x installs) | Measured live on `opencode v2.2.7` (`F-12`) and `agent_workflows/opencode_cli.py` | yes |
| D-5 | How do `generate` and `describe_all` behave when `runner is None` under `PYTEST_CURRENT_TEST`? | `generate(..., runner=None)` raises `runner_shared.DriverError` directly (`E-09(f)`), while `describe_all(..., runner=None)` checks `_assert_probe_spawn_is_permitted` before the lazy policy probe and classifies `DriverError` as `could-not-ask` (`pytest-spawn-refused`) | Let `DriverError` escape `describe_all` (rejected: crashes `test_agent_surface_conformance_mutation["migrate metadata"]` and `test_m0001_roundtrip.py` subprocess dry runs); remove `_assert_probe_spawn_is_permitted` (rejected: violates `E-09(f)` and risks paid model calls in tests) | `runner_shared._assert_probe_spawn_is_permitted`; `tests/test_agent_surface_conformance.py`; `4sd62s` 4.2 (`could-not-ask` still refuses `--apply`) | yes |
| D-6 | Should `ya4ee4` depend on `executed:g5hpbb` (`3g20ms`, `bv4kkj`, `9vf2iv`) as well as `executed:830wku`? | Yes: add `executed:830wku, executed:g5hpbb` to `- Item-Dependencies:` | Leave `ya4ee4` unordered relative to `g5hpbb` (rejected: `3g20ms` and `bv4kkj` rewrite `m0001_metadata_v2.py` and `cli.py`, and `g5hpbb` line 88 defers C12 description generation to `Carrier: ya4ee4`) | `g5hpbb` lines 87-88; `2026-11-07` maintainer demotion note; `rg -n "executed:ya4ee4"` shows zero cycle | yes |
| D-7 | How is the default model name obtained when `--describe-model` is omitted? | `oc_models.resolve_host_default_model(env=child_env, cwd=repo, agent="aw-describe")` (`default.model` when resolved, else `"host-default"`) | Read from `step_finish` or `argv` (rejected: `step_finish` never carries a model id and `argv` has no `--model` when omitted) | `runner_shared.py::COST_NOT_RECOMPUTED_HERE` comment and `cost_attribution_record` | yes |
| D-8 | How does `cli.py` pass `--describe-*` / `--no-describe` into `m0001`? | Construct `m0001_describe.Describer` in `cli.py` and pass `describer=describer` to `chain.Migration.run` (`describer=None` defaults to `Describer()` in `m0001_metadata_v2.run`) | Import `m0001_metadata_v2` directly in `cli.py` (rejected: forbidden by `1vfqdu` E-01); keep `describer=None` meaning "skip" (rejected: post-cutover `aw install --migrate` and bare `aw migrate --apply` pass `describer=None` and would refuse `--apply`) | `1vfqdu` E-01..E-03; `g8na48` E-01 `Migration.run` signature | yes |
