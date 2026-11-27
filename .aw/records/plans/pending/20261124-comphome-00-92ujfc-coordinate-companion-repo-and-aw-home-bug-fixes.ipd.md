# IPD: Coordinate companion repo and AW_HOME bug fixes

- Date: 2026-11-24
- Kind: orchestrator
- Concern: A targeted `/assess-bugs` audit across `agent_workflows/` scoped strictly to companion `aw` repositories (`records_backend == "companion"`) and `~/.aw/` (`AW_HOME` / `records_backend == "home"` / `clean-delta`) identified 55 verified, open bugs (excluding issues already fixed in commits `b77c6ef43`, `70f911304`, and `c8a130148`, and excluding `emit_index_write_result` deleted in `snin8q`). These span six architectural layers: core storage/context/placement switching, installer and policy persistence, metadata/selectors/self-commit locking, CLI record verbs and attention/check engine, pre-commit hooks and run monitoring, and runner execution/question inbox/`~/.aw/` lanes.
- Scope: Coordinate six right-sized child IPDs (`ywl7uc`, `7gverp`, `mmuv3v`, `7eivm2`, `7hfx7r`, `4vnd36`) that remediate every confirmed companion and `~/.aw/` bug with behavioral regression coverage. This orchestrator performs no code edits of its own and retires once all six children reach `executed/`.
- Scope-Paths: .aw/records/plans/pending/20261124-comphome-00-92ujfc-coordinate-companion-repo-and-aw-home-bug-fixes.ipd.md
- Item-Dependencies: executed:4vnd36, executed:7eivm2, executed:7gverp, executed:7hfx7r, executed:mmuv3v, executed:ywl7uc
- Status: approved
- Readiness: go-pending-approval
- Review-Depth: orchestrator
- Coverage: pass
- Coverage-Fingerprint: 1be5a065843f436113fd840724350dcd9b0ec5dd1b8399baedd168d66657659f
- Coverage-Checked: 2026-11-25 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Set: comphome
- Order: 0
- Highest E allocated: 6
- Id: 92ujfc
- Approval: 2026-11-27, recorded via aw ipd set: status set to approved
- Author: antigravity

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-27 approved (aw set): status set to approved
- 2026-11-25 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003
- 2026-11-25 coverage pass (aw oc run): fingerprint 1be5a065843f, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-11-25 /plan-review (antigravity/Gemini 4 Neon (High)): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003
- 2026-11-25 coverage pass (aw oc run): fingerprint 78bb57faef4d, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-11-24 to-review (antigravity): authored orchestrator for `/assess-bugs` (companion repos and `~/.aw/` scope), coordinating six child IPDs (`ywl7uc`, `7gverp`, `mmuv3v`, `7eivm2`, `7hfx7r`, `4vnd36`).

## Goal

Remediate all 55 confirmed companion-repository and `~/.aw/` (`AW_HOME`) bugs found by `/assess-bugs` through six focused, parallelizable child IPDs with full behavioral test coverage.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Confirm all child IPDs reach executed

- [ ] E-01 CONFIRM ywl7uc REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans ywl7uc` reports `ywl7uc` under `.aw/records/plans/executed/`.
  - Execution state: pending

- [ ] E-02 CONFIRM 7gverp REACHED executed
  - Depends on: E-01
  - Expected outcome: `aw find plans 7gverp` reports `7gverp` under `.aw/records/plans/executed/`.
  - Execution state: pending

- [ ] E-03 CONFIRM mmuv3v REACHED executed
  - Depends on: E-01
  - Expected outcome: `aw find plans mmuv3v` reports `mmuv3v` under `.aw/records/plans/executed/`.
  - Execution state: pending

- [ ] E-04 CONFIRM 7eivm2 REACHED executed
  - Depends on: E-01
  - Expected outcome: `aw find plans 7eivm2` reports `7eivm2` under `.aw/records/plans/executed/`.
  - Execution state: pending

- [ ] E-05 CONFIRM 7hfx7r REACHED executed
  - Depends on: E-01
  - Expected outcome: `aw find plans 7hfx7r` reports `7hfx7r` under `.aw/records/plans/executed/`.
  - Execution state: pending

- [ ] E-06 CONFIRM 4vnd36 REACHED executed
  - Depends on: E-01, E-03, E-05
  - Expected outcome: `aw find plans 4vnd36` reports `4vnd36` under `.aw/records/plans/executed/`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | ID | Filename | Summary | Depends on |
|---:|---|---|---|---|
| 01 | `ywl7uc` | `20261124-comphome-01-ywl7uc-fix-companion-and-aw-home-core-storage-context-placement-swi.ipd.md` | Fix core storage, `AW_HOME` unification, companion security/local.json sync, placement-switch rollback, `record_placement`, `artifact_core.git_mv`, and `project_layout`. | `none` |
| 02 | `7gverp` | `20261124-comphome-02-7gverp-fix-installer-clean-delta-hijack-companion-project-policy-di.ipd.md` | Fix `engine._clean_delta_home_trees` hijack, `public-target-private-companion` policy/attachment gaps (`install_wizard`, `project_context`, `project_schema`, `placement_switch`), `aw install --diff`, local-lane migration crash, and `leak_sanitizer` allowlist path. | `executed:ywl7uc` |
| 03 | `mmuv3v` | `20261124-comphome-03-mmuv3v-fix-metadata-selectors-self-commit-routing-companion-locking.ipd.md` | Fix `status_set` self-commit routing, `commit_lock` vs `ipd_lifecycle` companion locking, finalize staged-lane/worktree/runs fixes, `selectors` records-relative paths, and `artifact_meta` companion lookup bugs. | `executed:ywl7uc` |
| 04 | `7eivm2` | `20261124-comphome-04-7eivm2-fix-rename-archive-partition-attention-board-search-and-chec.ipd.md` | Fix `aw rename`, `aw group`, `aw archive`, `aw partition`, `aw ipd board`, `aw search`, `attention.scan` `.data/` and path-join bugs, `plan_readiness`, `artifact_refs`, `ipd_authoring`, and `check_engine` logical-path rules. | `executed:ywl7uc` |
| 05 | `7hfx7r` | `20261124-comphome-05-7hfx7r-fix-pre-commit-hooks-staged-gates-runners-monitor-run-viewer.ipd.md` | Fix companion pre-commit hooks (`executed_transition_gate`, `meta_log_append_gate`, `ipd_dependency_statement_gate`, staged `check_engine` gates), `runners_monitor`, `run_viewer`, `checkup`, `attention.inbox_waiting`, `set_records`, and clean-delta `aw adopt` inbox. | `executed:ywl7uc` |
| 06 | `4vnd36` | `20261124-comphome-06-4vnd36-fix-runner-question-inbox-untooled-finalize-gate-backlog-clo.ipd.md` | Fix `consume_answers` companion/home commit rollback, untooled `executed/` move gate bypass, `process_backlog_close`, `read_zero_work_evidence`, companion review/carrier helpers, and `~/.aw/` (`home`) lane staging/routing/merge guard. | `executed:ywl7uc`, `executed:mmuv3v`, `executed:7hfx7r` |

```mermaid
flowchart LR
  C01["01 ywl7uc: Core storage & context"]
  C02["02 7gverp: Installer & leak allowlist"]
  C03["03 mmuv3v: Metadata, commits & finalize"]
  C04["04 7eivm2: CLI verbs, attention & check_engine"]
  C05["05 7hfx7r: Hooks, staged gates & monitors"]
  C06["06 4vnd36: Runner, inbox, backlog close & home lanes"]
  C01 --> C02
  C01 --> C03
  C01 --> C04
  C01 --> C05
  C01 --> C06
  C03 --> C06
  C05 --> C06
```

## Completion criteria (the whole Set is done only when)

- Every child IPD in `## Child IPDs, sequence, and dependencies` (`ywl7uc`, `7gverp`, `mmuv3v`, `7eivm2`, `7hfx7r`, `4vnd36`) is in `.aw/records/plans/executed/` with `Status: executed` and all `V-*` checks passing.
- Each child IPD landed with behavioral regression coverage (zero code-pinning source-inspection tests), clean `mypy` on its modified modules, and clean `aw sanitize`.
- This orchestrator performs no code edits of its own and retires automatically once all six children are `executed`.

## Cross-IPD validation

- Order 01 (`ywl7uc`) establishes the unified `AW_HOME` resolver, companion `.gitignore`/`local.json` sync, and `git_mv` primitives required by Orders 02-06.
- Orders 02 (`7gverp`), 03 (`mmuv3v`), 04 (`7eivm2`), and 05 (`7hfx7r`) validate independently after `ywl7uc` lands.
- Order 06 (`4vnd36`) validates end-to-end companion and `~/.aw/` (`home`) runner execution, question inbox, backlog close, and lane containment after `ywl7uc`, `mmuv3v`, and `7hfx7r` land.

## Project conventions discovered (Step 0)

- Run record lives locally (gitignored) under `.aw/workflow-artifacts/assess-bugs/20261124-213000/`.
- Each child IPD is reviewed at `complex` depth with behavioral regression tests only (no code-pinning source-inspection tests): Order 03 (`mmuv3v`) carries `- Size assessment: standard`, while Orders 01 (`ywl7uc`), 02 (`7gverp`), 04 (`7eivm2`), 05 (`7hfx7r`), and 06 (`4vnd36`) carry `- Size assessment: exception` with documented cohesion rationales under `IPD-Z603`.
- Runner retirement retires this orchestrator automatically once all six children in `## Child IPDs, sequence, and dependencies` are `executed` on disk.

## Findings

Summary of the 55 confirmed companion and `~/.aw/` bugs by child owner (full catalog in `.aw/workflow-artifacts/assess-bugs/20261124-213000/findings.csv`):
- `ywl7uc` (Order 01): 14 bugs in `agent_workflows/project_context.py`, `agent_workflows/config.py`, `agent_workflows/project_registry.py`, `agent_workflows/storage.py`, `agent_workflows/placement_switch.py`, `agent_workflows/record_placement.py`, `agent_workflows/artifact_core.py`, and `agent_workflows/project_layout.py`.
- `7gverp` (Order 02): 6 bugs in `agent_workflows/engine.py`, `agent_workflows/install_wizard.py`, `agent_workflows/cli.py`, `agent_workflows/project_context.py`, `agent_workflows/project_schema.py`, `agent_workflows/placement_switch.py`, and `agent_workflows/leak_sanitizer.py`.
- `mmuv3v` (Order 03): 9 bugs in `agent_workflows/status_set.py`, `agent_workflows/git_commit_helper.py`, `agent_workflows/commit_lock.py`, `agent_workflows/ipd_lifecycle.py`, `agent_workflows/selectors.py`, and `agent_workflows/artifact_meta.py`.
- `7eivm2` (Order 04): 9 bugs in `agent_workflows/artifact_rename.py`, `agent_workflows/research_refs.py`, `agent_workflows/plans_archive.py`, `agent_workflows/research_archive.py`, `agent_workflows/partition.py`, `agent_workflows/attention.py`, `agent_workflows/plan_readiness.py`, `agent_workflows/artifact_refs.py`, `agent_workflows/check_engine.py`, `agent_workflows/ipd_authoring.py`, and `agent_workflows/cli.py`.
- `7hfx7r` (Order 05): 8 bugs in `agent_workflows/hooks/executed_transition_gate.py`, `agent_workflows/hooks/meta_log_append_gate.py`, `agent_workflows/hooks/ipd_dependency_statement_gate.py`, `agent_workflows/check_engine.py`, `agent_workflows/runners_monitor.py`, `agent_workflows/run_viewer.py`, `agent_workflows/checkup.py`, `agent_workflows/artifact_adopt.py`, `agent_workflows/attention.py`, and `agent_workflows/set_records.py`.
- `4vnd36` (Order 06): 9 bugs in `agent_workflows/runner_shared.py`, `agent_workflows/question_inbox.py`, `agent_workflows/review_findings.py`, `agent_workflows/lane_containment.py`, and `agent_workflows/ipd_lifecycle.py`.

*(Note: 5 overlapping bugs reported across subagents were deduplicated; 5 companion lane production/staging bugs were already fixed in commit `c8a130148`; 1 deleted function `emit_index_write_result` was removed by `snin8q`.)*

## Proposed changes (ordered, validatable)

1. Execute Order 01 (`ywl7uc`) first to establish unified `AW_HOME`, companion `.gitignore`/`local.json`, and `git_mv` primitives.
2. Execute Orders 02 (`7gverp`), 03 (`mmuv3v`), 04 (`7eivm2`), and 05 (`7hfx7r`) in parallel once `ywl7uc` lands.
3. Execute Order 06 (`4vnd36`) once `ywl7uc`, `mmuv3v`, and `7hfx7r` land.
4. Retire `92ujfc` once all six children are `executed`.

## Deferred / out of scope (with reason)

- Backlog `vo0y6q` (`aw backlog new --apply` state lock in `tracked`+`home` fixture) is already carried by existing plan `rntx9a`.
  - Carrier: rntx9a
- Backend-agnostic `agent_workflows/artifact_meta.py::check_freshness` `ReleaseResolution` attribute mismatch (`rel_outcome.status`/`rel_outcome.candidates` at lines 4976-4984 vs `agent_workflows/releases.py::ReleaseResolution` fields `outcome`/`paths`) is outside the companion/`~/.aw/` scope of this assessment (and `ywl7uc` explicitly declined carrying it); tracked by open backlog item `f3qdqh`.
  - Carrier: f3qdqh

## Scope check

- Over-scope: none; orchestrator touches only its own plan file and delegates all code edits to Orders 01-06.
- Under-scope: none; all 55 confirmed companion and `~/.aw/` bugs are assigned to concrete child IPDs.

## Required tests / validation

Each child IPD (`ywl7uc`, `7gverp`, `mmuv3v`, `7eivm2`, `7hfx7r`, `4vnd36`) runs its own targeted `python3 -m pytest` suite, `mypy`, and `aw sanitize`. This orchestrator runs no tests of its own.

## Spec / documentation sync

No spec or user-doc edit is required for this orchestrator or its six reviewed children. During `/plan-review`, all six children (`ywl7uc`, `7gverp`, `mmuv3v`, `7eivm2`, `7hfx7r`, `4vnd36`) checked the governing specs and user docs (including `ARCHITECTURE.md:91` and `README.md:138` for `7gverp`'s resolved `OQ-02`, plus `docs/cli-output-contract.md` and specs `11037v`, `yfz5u9`, `4sd62s`, `25kzda`, `6kwd2e`, and `7ckptx`) and confirmed that the fixes restore documented behavior without changing public contracts.

## Open questions

### OQ-01: Canonical default for `AW_HOME` when `XDG_CONFIG_HOME` is set (`ywl7uc`)

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: `project_context.get_default_aw_home` currently uses `$XDG_CONFIG_HOME/agent-workflows` when `XDG_CONFIG_HOME` is set, whereas `config.get_aw_home` and `project_registry.find_project` always default to `~/.aw`. Order 01 (`ywl7uc`) should confirm during `/plan-review` whether to standardize on `~/.aw` (with legacy XDG fallback/warning if existing data is detected) or honor `XDG_CONFIG_HOME` across all three modules. RESOLVED 2026-11-24 by the user via /askme: Always default AW_HOME to ~/.aw, ignoring XDG_CONFIG_HOME (detect and warn if legacy project data already exists under $XDG_CONFIG_HOME/agent-workflows). No reason was given.

### OQ-02: Target-repo tracking policy for `.aw/config/project.json` in `public-target-private-companion` (`7gverp`)

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: `install_wizard.get_preset_defaults` sets `config_project="companion-git"`, `project_context` derives `IGNORED`, and `.aw/.gitignore` leaves `/config/project.json` unignored so fresh installs leave `.aw/config/project.json` untracked in the target repo. Order 02 (`7gverp`) should confirm during `/plan-review` whether `.aw/config/project.json` should be `target-git` (committed in target repo) or ignored/stored in the companion repo. RESOLVED 2026-11-24 by the user via /askme: Keep project.json at <target>/.aw/config/project.json and track it in the target repo (target-git). No reason was given.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw find plans ywl7uc` showing `ywl7uc` under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw find plans 7gverp` showing `7gverp` under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw find plans mmuv3v` showing `mmuv3v` under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw find plans 7eivm2` showing `7eivm2` under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw find plans 7hfx7r` showing `7hfx7r` under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `aw find plans 4vnd36` showing `4vnd36` under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:
1. **Approval & prerequisite gate:** This orchestrator retires only after human approval (`Status: approved`) and after all six children (`ywl7uc`, `7gverp`, `mmuv3v`, `7eivm2`, `7hfx7r`, `4vnd36`) reach `.aw/records/plans/executed/` with `Status: executed` and passing validation. Both `OQ-01` and `OQ-02` are resolved by the maintainer (`2026-11-24`).
2. **Scope fence:** `- Scope-Paths:` declares only `.aw/records/plans/pending/20261124-comphome-00-92ujfc-coordinate-companion-repo-and-aw-home-bug-fixes.ipd.md`; this orchestrator performs no source-code edits of its own. Any unexpected out-of-scope edit or omitted declared path in a standalone retirement must be justified via `--scope-reason` / `--scope-ack` at finalize time.
3. **Validation honesty (hard MUST):** In any standalone retirement, every `V-01..V-06` entry MUST paste the actual command output of `aw find plans <id6>` showing the child under `.aw/records/plans/executed/`. Never mark a `V-*` item `pass` from memory or without real output.
4. **Commit & push hygiene:** Any standalone commit MUST be path-scoped via `aw commit 92ujfc -- <paths>` (never `git add -A` or `-a`), and MUST NEVER push, tag, or release.
5. **Lifecycle transition (conditional ownership):** When run under a runner (`aw oc run` / `aw agy run`), the runner retires this orchestrator automatically to `.aw/records/plans/executed/` once all six children are `executed` on disk, spending no agent turn; do NOT hand-run `git mv` into `executed/`. In a standalone (non-runner) retirement after all six children are `executed`, run `aw ipd finalize 92ujfc` rather than hand-moving files.
