# Review findings: ipd x8id25

- Subject-Id: x8id25
- Subject-Type: ipd
- Reviewed-At: 2026-11-26
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Step T
1. No - the plan converts 18 test modules inside the prepared cutover code patch (`.aw/system/cutover/metastore-code.cutover.patch`) and does not change a spec or public contract.
2. Yes - it regenerates `.aw/system/cutover/metastore-code.cutover.patch`, which patches lifecycle, pre-commit hook, migration, and metadata-store code paths.
3. Yes - it converts 18 test modules across three grouped execution items (`E-02` to `E-04`) spanning `ipd_lifecycle`, `ipd_schema`, `ipd_set_executor`, lane rule-break detection, rename events, `m0001` migrations and gate markers, `meta repair`, `metadata_single_owner`, `migrate` CLI/chain, orchestrator probe payloads, `partition`, `plans_index`, `poll_for_deps`, prompt writing standard, and `prompts` set surface.
4. Yes - `- Scope-Paths:` lists the plan file and `.aw/system/cutover/metastore-code.cutover.patch`.
5. Yes - a mistake regenerating the cumulative code patch or retiring still-valid test coverage could silently break cutover validation or drop regression coverage across 18 test modules.
- Selected tier: `standard`

AW-TIER: standard

### Step R1: References, Scope, and Dependencies
- Checked: `.aw/records/plans/pending/20261125-metastore-310-x8id25-convert-test-batch-c-ipd-lifecycle-cli-through-prompts-set-s.ipd.md`, `.aw/records/plans/pending/20261125-metastore-305-hdwqex-make-ipd-lint-and-ipd-scaffold-log-aware-in-the-cutover-code.ipd.md`, `.aw/records/plans/pending/20261125-metastore-314-fljn9b-make-backlog-validation-and-readers-log-aware-in-the-cutover.ipd.md`, `.aw/records/plans/pending/20261125-metastore-315-szykgd-make-specs-releases-spec-link-search-and-dep-gate-log-aware.ipd.md`, `.aw/system/cutover/metastore-code.cutover.patch`, all 18 batch C test modules (`tests/test_ipd_lifecycle_cli.py` through `tests/test_prompts_set_surface.py`), `agent_workflows/ipd_lifecycle.py`, `agent_workflows/ipd_lint.py`, `agent_workflows/ipd_schema.py`, `agent_workflows/partition.py`, `agent_workflows/plans.py`, `agent_workflows/plans_index.py`, `agent_workflows/selectors.py`, `agent_workflows/check_engine.py`, `agent_workflows/hooks/executed_transition_gate.py`, `agent_workflows/hooks/backlog_blocking_close_gate.py`, `agent_workflows/meta_cli.py`, `agent_workflows/prompts.py`, `agent_workflows/artifact_rename.py`, and `agent_workflows/runner_shared.py`.
- Found five unpatched production cutover gaps in `.aw/system/cutover/metastore-code.cutover.patch` (none covered by `hdwqex`, `fljn9b`, or `szykgd`) blocking five batch C test modules and post-cutover runtime workflows (`PR-001`).
- Found gitignored attempt-1 lane provenance cited as live evidence in `Concern` and `F-04` (`PR-002`), stale Step 0 chain omitting `fljn9b` and `szykgd` and missing `cxxmyv` in `## Deferred / out of scope` (`PR-004`), and skipped numbering in `## Proposed changes` (`PR-006`).

### Step R2: Executability and Verification Rigor
- Checked: All 18 batch C test modules against post-cutover `artifact_meta`, `ipd_lifecycle`, `ipd_lint`, `ipd_schema`, `partition`, `plans`, `plans_index`, `check_engine`, `executed_transition_gate`, `backlog_blocking_close_gate`, `meta_cli`, `migrations/chain`, `migrations/m0001_*`, `prompts`, `artifact_rename`, and `runner_shared`.
- Verified five unpatched production cutover bugs (`PR-001`):
  1. `agent_workflows/ipd_lifecycle.py` (unpatched in `.aw/system/cutover/metastore-code.cutover.patch`): 10 bare `_lint.parse(...)` call sites without `state=` (`L166`, `L1053`, `L1101`, `L1887`, `L2110`, `L2278`, `L3567`, `L5447`, `L5540`, `L5780`) fail closed (`has no '- Id:' handle`) or read empty `Scope-Paths` on log-format plans, and `_finalize_transaction` (`L6065`, `L6123`, `L6155`, `L6185`, `L6274`, `L6317-L6328`) hardcodes `owned_paths = [tx_plan_rel, dest_rel]` without staging `.aw/records/meta/<plan_id>.jsonl`, losing the appended `executed` log event on worktree teardown.
  2. `agent_workflows/partition.py` (unpatched: `_is_orchestrator_plan` `L299-L315`, `_selectors._read_setid` `L207, L343`) and `agent_workflows/plans.py` (unpatched: `read_set` `L145-L166`, `scan` `L234`) call `artifact_meta.read_text` on file text instead of reading log-backed `State`, returning `None`/`False` for `plan_role`, `set`, and `order` on log-format plans.
  3. `agent_workflows/check_engine.py::check_status_untooled_range` (`_read_plan_state_at_checked` `L3620-L3650`, `_check_untooled_plan_transition` `L3667-L3764`) returns replayed log state via `read_at` and ignores the in-file YAML mirror status, failing to detect hand-edited mirror status flips across `base..head` in worker lanes.
  4. `agent_workflows/hooks/executed_transition_gate.py::check` (`L649` before `L656`) and `agent_workflows/hooks/backlog_blocking_close_gate.py::check` (`L54` before `L64`) read metadata via `read_at`/`check_release_gate_consistency` BEFORE checking `_migration_marker_accepts(root)`, raising `MetadataSchemaError` on unstamped legacy repos under `CURRENT_METADATA_SCHEMA == 2` before the `m0001` terminal-commit marker can short-circuit.
  5. `agent_workflows/meta_cli.py::_run_meta_repair` (`L1636`, unpatched) calls `_meta.resolve(tok, project_context=ctx)` without catching `MetadataSchemaError`, crashing with an uncaught exception on an unmigrated legacy repo instead of returning a structured exit-2 `CommandResult` naming `aw migrate metadata`.
- Confirmed `agent_workflows/artifact_rename.py` (`_apply_log_rename` at `L1072`) and `agent_workflows/plans_index.py` (`scan_plans` via `artifact_meta.query`) are already log-aware, and `agent_workflows/ipd_lint.py` / `ipd_schema.py` / `ipd_authoring.py` are already covered by Order 305 `hdwqex`.
- Identified per-module removed-API, Phase-B retirement, pre-migration schema-1 CLI baseline, YAML-mirror assertion, and duplicate-id6 fixture traps across all 18 batch C modules (`PR-003`), plus missing exact patch/plan paths, exact `rg -n` patterns with exit-1 expectations, and `git status --short` verification in `E-01`, `E-05`, and `V-01`..`V-05` (`PR-005`).

### Step R3: Security, Isolation, and Safety
- Checked: Scratch worktree isolation (`.aw/state/x8id25/scratch`), live-tree safety, `- Scope-Paths:` fence, `aw commit x8id25` path-scoped commit contract, never-push rule, and no assertion-weakening rule.
- Added explicit `git status --short` verification in `E-05`/`V-05` confirming no live code edits escape `- Scope-Paths:`.

### Step R4: Engineering Quality and Contract Conformance
- Checked: Technical writing standard (`.aw/system/workflows/technical-writing/technical-writing.md`), `IPD-Z603` sizing, `E-*`/`V-*` bijection, Mermaid diagram consistency, `check.review-finding-unescalated` / `MD-9` open-question rules, and `s7-finalize.md` managed-runner-lane vs. hand-run `aw ipd finalize` ownership (`PR-006`).
- Confirmed `PR-001` is properly escalated into `OQ-01` carrying `- Blocking: yes`, `- Status: open`, `- Owner: maintainer`, `- Finding: PR-001`, `- Carrier: ldfefd`, and a strength-labeled recommendation (`strength: strong`).

### Step S5: Open Questions and Decisions
- Checked: Collected all 6 findings; resolved `PR-002` through `PR-006` from repository evidence (all `Overall:Low`, `Reversible: yes`, recorded in `### Decisions` `D-1..D-5`).
- Escalated `PR-001` (`Overall:Medium-High`) as blocking human-owned question `OQ-01` in `x8id25` and as `batch-c-production-log-aware-gaps` (`gates_verdict: true`) in `.aw/state/lane-submissions/run-20261126T020242Z-3080634/06-x8id25/attempt-1/outcomes/06-x8id25.json` because fixing five production subsystems (`ipd_lifecycle.py`, `partition.py`/`plans.py`, `check_engine.py`, `executed_transition_gate.py`/`backlog_blocking_close_gate.py`, and `meta_cli.py`) changes plan scope and sequencing across batch C and later batches.

### Pass 2: Verification of Edits
- Re-read the revised plan `.aw/records/plans/pending/20261125-metastore-310-x8id25-convert-test-batch-c-ipd-lifecycle-cli-through-prompts-set-s.ipd.md` from top to bottom.
- Verified `PR-002` through `PR-006` are fully applied, `PR-001` is escalated to `OQ-01` with `- Blocking: yes` and `- Finding: PR-001`, `- Status: reviewed`, `- Review-Depth: standard`, and `- Readiness: no-go` are written, `## Workflow history` leads with `REVIEWED - OPEN QUESTIONS`, `E-01..E-05` match `V-01..V-05` 1:1, and the Mermaid diagram matches the ordered steps.

### Findings
| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | repo-wide | Production cutover readiness (`ipd_lifecycle.py`, `partition.py`, `plans.py`, `check_engine.py`, `executed_transition_gate.py`, `backlog_blocking_close_gate.py`, `meta_cli.py`) | `.aw/system/cutover/metastore-code.cutover.patch`; `agent_workflows/ipd_lifecycle.py:166,1053,1101,1887,2110,2278,3567,5447,5540,5780,6155,6317`; `agent_workflows/partition.py:207,299-315,343`; `agent_workflows/plans.py:145-166,234`; `agent_workflows/check_engine.py:3620-3650,3667-3764`; `agent_workflows/hooks/executed_transition_gate.py:649-657`; `agent_workflows/hooks/backlog_blocking_close_gate.py:54-65`; `agent_workflows/meta_cli.py:1636` | Five unpatched production cutover gaps in `.aw/system/cutover/metastore-code.cutover.patch` (not covered by `hdwqex`, `fljn9b`, or `szykgd`) directly block five batch C test modules (`test_ipd_lifecycle_cli.py`, `test_partition.py`, `test_lane_rule_break_detection.py`, `test_m0001_gate_marker.py`, `test_meta_repair_cli.py`) and post-cutover execution: `ipd_lifecycle.py` fails closed on log-format plans at 10 bare `_lint.parse` sites and drops `meta/<plan_id>.jsonl` from `_finalize_transaction` `owned_paths`; `partition.py` and `plans.py::read_set` read inline text instead of log state; `check_status_untooled_range` ignores hand-edited YAML mirror status flips; both pre-commit gates read metadata before `_migration_marker_accepts`; and `meta_cli._run_meta_repair` raises uncaught `MetadataSchemaError` on unmigrated legacy repos. | C:Medium-High; U:Medium; S:Low; F:High; Overall:Medium-High | OPEN | Escalated to maintainer as `OQ-01` (`- Blocking: yes`, `- Finding: PR-001`) and parked in outcome JSON (`gates_verdict: true`) to decide between splitting 1 dedicated production-fix child plan ahead of `x8id25` (Recommended, `strong`), splitting into 2 plans (`ipd_lifecycle.py` alone + the other 4 fixes), or expanding `x8id25`. |
| PR-002 | HIGH | plan-local | Provenance (`Concern`, `F-04`) | `.aw/records/plans/pending/20261125-metastore-310-x8id25-convert-test-batch-c-ipd-lifecycle-cli-through-prompts-set-s.ipd.md:5,82` | `Concern` and `F-04` cited gitignored `.aw/state/lane-submissions/run-20261125T162650Z-1337442/06-x1mmdp/attempt-1/evidence/failing-modules.txt` as live evidence, which does not exist in fresh execution lanes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Attributed the 55-failure count as historical `x1mmdp` attempt-1 pre-split provenance and anchored execution to the authoritative `89mtbl` F-04 post-builder census (`D-1`). |
| PR-003 | HIGH | plan-local | Per-module conversion & rule-4 retirement rules (`E-02`, `E-03`, `E-04`, `F-05`) | `tests/test_log_rename_events.py`; `tests/test_m0001_any_repo.py:251-265`; `tests/test_m0001_review_conversion.py:351,427-451,1181`; `tests/test_meta_repair_cli.py:324`; `tests/test_metadata_single_owner.py:382`; `tests/test_migrate_cli.py:239`; `tests/test_migrations_chain.py:272,350`; `tests/test_orchestrator_probe_payload.py:31,132`; `tests/test_production_prompt_writing_standard.py`; `tests/test_prompts_set_surface.py:81,204` | Bare module lists in `E-02`..`E-04` hid non-mechanical per-module traps: removed Phase-B legacy tests needing rule-4 retirement (`test_log_rename_events.py`, `test_meta_repair_cli.py`, `test_migrations_chain.py`, `test_prompts_set_surface.py`), pre-migration schema-1 CLI baselines (`test_m0001_any_repo.py`, `test_m0001_review_conversion.py`), post-cutover `<!-- aw-managed-prompt: ... -->` mirrors and `hdwqex` H2 orders, duplicate `demo01` id6s in `test_production_prompt_writing_standard.py`, and `text_only=True` fixtures. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified concrete per-module conversion and rule-4 retirement rules across all 18 batch C modules in `E-02`, `E-03`, and `E-04`, and recorded the production-gap audit in `F-05` (`D-2`). |
| PR-004 | MEDIUM | plan-local | Set chain & deferred carriers (`Step 0`, `## Deferred / out of scope`) | `.aw/records/plans/pending/20261125-metastore-310-x8id25-convert-test-batch-c-ipd-lifecycle-cli-through-prompts-set-s.ipd.md:69,98-103` | Step 0 omitted prerequisite production-fix children `hdwqex`, `fljn9b`, and `szykgd` from the cumulative patch chain, and `## Deferred / out of scope` omitted `cxxmyv` (the attended cutover commit) and `hdwqex`/`fljn9b`/`szykgd`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated Step 0 with the full current chain (`hdwqex`, `89mtbl`, `nv3upa`, `fljn9b`, `cugg3w`, `szykgd`, `psm9ac`, `x8id25`, `e0g2gt`, `qi0kl6`, `x3mig6`, `x1mmdp`) and added `hdwqex`, `fljn9b`/`szykgd`, and `cxxmyv` carriers to `## Deferred / out of scope` (`D-3`). |
| PR-005 | MEDIUM | plan-local | Execution & validation specificity (`E-01`, `E-05`, `V-01`..`V-05`) | `.aw/records/plans/pending/20261125-metastore-310-x8id25-convert-test-batch-c-ipd-lifecycle-cli-through-prompts-set-s.ipd.md:38,62,126-145` | `E-01`/`E-05`/`V-01` used placeholders (`"the docs patch"`, `"<this plan>"`) instead of exact repo-relative paths; `E-05`/`V-05` omitted `git status --short` clean-tree verification; `V-02`..`V-04` lacked the exact removed-symbol `rg -n` regex and exit-1 expectation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Named exact patch and plan paths in `E-01`, `E-05`, `V-01`, and `V-05`, added `git status --short` verification in `E-05`/`V-05`, and specified exact `rg -n` commands expecting exit 1 in `V-02`..`V-04` (`D-4`). |
| PR-006 | LOW | plan-local | List hygiene & finalize ownership (`## Proposed changes`, `## Approval and execution gate`) | `.aw/records/plans/pending/20261125-metastore-310-x8id25-convert-test-batch-c-ipd-lifecycle-cli-through-prompts-set-s.ipd.md:86-88,152` | `## Proposed changes` skipped step 3 (`1.`, `2.`, `4.`), and `## Approval and execution gate` unconditionally directed `aw ipd finalize` instead of distinguishing managed runner lanes from hand-run sessions (`s7-finalize.md:31-36`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Restored sequential `1.`..`5.` numbering in `## Proposed changes` matching the Mermaid diagram and updated `## Approval and execution gate` to distinguish managed runner lanes from hand-run sessions and reflect `OQ-01` gating (`D-5`). |

### Proofreading
#### Changes
| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Concern` & `F-04` | Cited gitignored `.aw/state/lane-submissions/.../failing-modules.txt` as live evidence | Attributed 55-failure count as historical `x1mmdp` attempt-1 provenance; anchored execution to `89mtbl` F-04 | Accuracy & self-contained provenance |
| `## Proposed changes` | Numbered `1.`, `2.`, `4.` | Numbered `1.` through `5.` matching `E-01`..`E-05` and the Mermaid diagram | List hygiene & diagram parity |
| `E-01`, `E-05`, `V-01`..`V-05` | Generic `"the docs patch"`, `"<this plan>"`, `"rg for the removed symbols"` | Named exact repo-relative patch/plan paths, exact `rg -n '...' <modules>` commands with exit 1, and `git status --short` | Precision & verifiable evidence |
| `## Approval and execution gate` | Unconditional `aw ipd finalize` instruction | Distinguished managed runner lanes (runner finalizes) from hand-run sessions and gated execution on `OQ-01` resolution | Runner-lane contract conformance |

#### Issues
| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| PR-001 | `## Open questions` (`OQ-01`) | Sequencing of five unpatched production cutover gaps (`ipd_lifecycle.py`, `partition.py`/`plans.py`, `check_engine.py::check_status_untooled_range`, `executed_transition_gate.py`/`backlog_blocking_close_gate.py` marker order, and `meta_cli.py::_run_meta_repair`) blocking batch C (`x8id25`) | Maintainer decision on splitting one prerequisite production-fix child plan ahead of `x8id25`, splitting into two prerequisite plans (`ipd_lifecycle.py` alone + the other four), or expanding `x8id25` | Split out one dedicated production-fix child plan ahead of `x8id25` covering all five gaps and keep `x8id25` strictly test-only | strong |

### Decisions
| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `Concern` and `F-04` cite the pre-split batch C failure count without referencing gitignored lane artifacts? | Attribute the 55-failure count to the historical `x1mmdp` attempt-1 pre-split census and anchor execution to `89mtbl` F-04. | Keep the `.aw/state/lane-submissions/...` path (rejected: gitignored and absent in fresh execution lanes). | `x8id25` lines 5 and 82; `cugg3w` / `psm9ac` review precedent. | yes |
| D-2 | How should `E-02`..`E-04` guide conversion and Phase-B retirement across all 18 batch C modules? | Add concrete per-module rules for every module, citing spec `4sd62s` clauses for rule-4 retirements (`test_log_rename_events.py`, `test_meta_repair_cli.py`, `test_migrations_chain.py`, `test_prompts_set_surface.py`) and naming fixture/baseline traps (`test_m0001_any_repo.py`, `test_m0001_review_conversion.py`, `test_production_prompt_writing_standard.py`). | Leave bare filename lists (rejected: hides non-mechanical retirements and pre-migration schema-1 baseline traps). | Static audit of all 18 batch C test modules against `.aw/system/cutover/metastore-code.cutover.patch`. | yes |
| D-3 | How should `Step 0` and `## Deferred / out of scope` reflect the current `metastore` Set chain? | List `hdwqex`, `89mtbl`, `nv3upa`, `fljn9b`, `cugg3w`, `szykgd`, `psm9ac`, `x8id25`, `e0g2gt`, `qi0kl6`, `x3mig6`, `x1mmdp` in Step 0 and add `hdwqex`, `fljn9b`/`szykgd`, and `cxxmyv` to `## Deferred / out of scope`. | Keep the pre-split chain omitting `fljn9b`, `szykgd`, and `cxxmyv` (rejected: stale relative to `.aw/records/plans/pending/`). | `.aw/records/plans/pending/20261125-metastore-314-fljn9b-*.ipd.md`, `20261125-metastore-315-szykgd-*.ipd.md`, `20261102-metastore-13-cxxmyv-*.ipd.md`. | yes |
| D-4 | How should `E-01`, `E-05`, and `V-01`..`V-05` specify paths, removed-symbol checks, and live-tree safety? | Use exact repo-relative patch and plan paths, exact `rg -n` patterns expecting exit 1, and `git status --short` verification in `E-05`/`V-05`. | Keep placeholders and generic `rg` wording (rejected: ambiguous and weakens verification). | `x8id25` `E-01`, `E-05`, `V-01`..`V-05`; `psm9ac` review precedent. | yes |
| D-5 | How should `## Proposed changes` and `## Approval and execution gate` align with list hygiene and runner-lane finalize ownership? | Restore sequential `1.`..`5.` numbering matching the Mermaid diagram, distinguish managed runner lanes from hand-run sessions for `aw ipd finalize`, and gate execution on `OQ-01` resolution. | Keep skipped numbering and unconditional `aw ipd finalize` (rejected: numbering defect and conflicts with `s7-finalize.md:31-36`). | `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-36`. | yes |

## Round 2

### Step T
1. No - `x8id25` converts 18 test modules inside `.aw/system/cutover/metastore-code.cutover.patch`.
2. Yes - it regenerates `.aw/system/cutover/metastore-code.cutover.patch`.
3. Yes - it covers 18 test modules across `E-02`..`E-04`.
4. Yes - `- Scope-Paths:` lists the plan and `.aw/system/cutover/metastore-code.cutover.patch`.
5. Yes - regenerating the cumulative cutover code patch affects downstream batches.
- Selected tier: `standard`

AW-TIER: standard

### Step R1: References, Scope, and Dependencies
- Checked: `.aw/records/plans/pending/20261125-metastore-310-x8id25-convert-test-batch-c-ipd-lifecycle-cli-through-prompts-set-s.ipd.md`, `.aw/records/plans/pending/20261126-metastore-316-otin36-make-ipd-lifecycle-partition-plans-untooled-range-hooks-and.ipd.md`, `.aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md`, and `.aw/records/plans/pending/20261109-metastore-257-x1mmdp-add-the-log-format-test-builder-switch-to-the-cutover-code-p.ipd.md`.
- Verified Order 316 `otin36` chains directly after `psm9ac` (`- Item-Dependencies: executed:psm9ac`) and ahead of `x8id25` (`- Item-Dependencies: executed:otin36`).
- Verified `otin36` is wired into orchestrator `63ib9r` (`Highest E allocated: 228`, `E-228`/`V-228`, `## Child IPDs` Order 316, `E-222`/`E-179`/`E-13` dependencies) and `x1mmdp` (`- Item-Dependencies:` and `## Deferred / out of scope`).
- Swept every stale open-`OQ-01`/`PR-001` reference across `x8id25` and corrected the `meta_cli.py::meta_repair` symbol name.

### Step R2: Executability and Verification Rigor
- Checked: `E-01`..`E-05` and `V-01`..`V-05` in `x8id25` and `otin36`.
- Verified `x8id25` requires zero production edits outside the scratch worktree because `otin36` lands all five production cutover fixes before `x8id25` executes.

### Step R3: Security, Isolation, and Safety
- Checked: Scratch worktree isolation, `- Scope-Paths:` fences, `aw commit` path-scoped commit contracts, and never-push clauses in `x8id25` and `otin36`.

### Step R4: Engineering Quality and Contract Conformance
- Checked: Technical writing standard (`.aw/system/workflows/technical-writing/technical-writing.md`), `IPD-Z603` sizing, `E-*`/`V-*` bijection, Mermaid diagrams, and `check.review-finding-unescalated` / `IPD-Q501` gates.
- Verified `PR-001` is cleared (`FIXED`), `OQ-01` carries `- Status: resolved` and `- Owner: maintainer`, `- Readiness: go-pending-approval` is written in `x8id25`, and `otin36` is authored review-ready (`Status: to-review`) with zero `TODO` placeholders.

### Step S5: Open Questions and Decisions
- Checked: `OQ-01` (`PR-001`) resolved via Option 1 recovery from parked `run-20261126T020242Z-3080634` branch `aw/parked/run-20261126T020242Z-3080634/x8id25`; recorded chaining decision `D-1` below (`Reversible: yes`).

### Pass 2: Verification of Edits
- Re-read `x8id25` and `otin36` in full; verified `aw ipd lint --phase review-finalize` on `x8id25` and `aw ipd lint --phase author` on `otin36`, `63ib9r`, and `x1mmdp`.

### Findings
| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | repo-wide | Production cutover readiness (`ipd_lifecycle.py`, `partition.py`, `plans.py`, `check_engine.py`, `executed_transition_gate.py`, `backlog_blocking_close_gate.py`, `meta_cli.py`) | `.aw/records/plans/pending/20261125-metastore-310-x8id25-convert-test-batch-c-ipd-lifecycle-cli-through-prompts-set-s.ipd.md` (`OQ-01`, `F-05`); `.aw/records/plans/pending/20261126-metastore-316-otin36-make-ipd-lifecycle-partition-plans-untooled-range-hooks-and.ipd.md` | Five unpatched production cutover log-awareness gaps blocking five batch C test modules and downstream execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolved `OQ-01` (2026-11-26) under Option 1 (Recommended, matching `fljn9b` and `szykgd`). Authored Order 316 child plan `otin36` chained after `psm9ac`, wired `otin36` into `63ib9r` and `x1mmdp`, updated `x8id25`'s `- Item-Dependencies:` to `executed:otin36`, marked `OQ-01` resolved, set `- Readiness: go-pending-approval`, and swept stale references across `x8id25`. |

### Proofreading
#### Changes
| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `x8id25` (`Concern`, `Scope`, `E-02`..`E-04`, `Step 0`, `F-05`, `Scope check`, `Approval and execution gate`) | Described `OQ-01`/`PR-001` as open and gating batch C modules; cited `meta_cli.py::_run_meta_repair` | Updated all references to resolved `OQ-01`, prerequisite Order 316 (`otin36`) in `- Item-Dependencies:`, and exact symbol `meta_cli.py::meta_repair` | Consistency, symbol accuracy, and stale-wording sweep |
| `x8id25` (`## Deferred / out of scope`) | Did not list `otin36` | Added `otin36` carrier for the five production log-awareness fixes | Explicit scope boundary |

#### Issues
| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | (none) | No unresolved proofreading issues remain. | None | None | very strong |

### Decisions
| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Where in the serial cutover code-patch chain should Order 316 (`otin36`) sit? | Chain `otin36` immediately after `psm9ac` (`- Item-Dependencies: executed:psm9ac`) and set `x8id25` to `- Item-Dependencies: executed:otin36` (wiring `otin36` into `63ib9r` and `x1mmdp`). | Chain `otin36` earlier ahead of `psm9ac` (rejected: would require editing already-reviewed `psm9ac`, which does not need any of `otin36`'s five fixes). | `x8id25` OQ-01 Option 1 (Recommended); `fljn9b`/`szykgd` precedent; `.aw/records/plans/pending/20261125-metastore-309-psm9ac-convert-test-batch-b-backlog-handoff-close-through-ipd-depen.ipd.md`; `.aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md`. | yes |
