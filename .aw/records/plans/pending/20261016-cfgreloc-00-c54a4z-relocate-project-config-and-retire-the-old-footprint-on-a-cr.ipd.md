# IPD: Relocate project config and retire the old footprint on a cross-placement preset switch

- Date: 2026-10-16
- Kind: orchestrator
- Concern: Backlog `ui1aln`: switching an installed repository between a preset whose config lives in the target (`private-target`, `<repo>/.aw/config/project.json`) and one whose config lives under `AW_HOME` (`completely-clean-target`, `local-only`, `<AW_HOME>/projects/<id>/config/project.json`) leaves the old `project.json` authoritative, because `project_context.project_config_dir` prefers the in-tree file whenever it exists while `install_wizard.persist_project_policy` writes to the NEW preset's `config_project` path. Plan `on0keo` stopped the noninteractive `--preset` path with an `InvalidPolicyError`; there is still no relocation, and authoring probes show two entry points the `on0keo` guard does not cover.
- Scope: Orchestration only: sequence the five children below and confirm each reaches `executed`. No code, test, spec or record work of its own.
- Scope-Paths: .aw/records/plans/pending/20261016-cfgreloc-00-c54a4z-relocate-project-config-and-retire-the-old-footprint-on-a-cr.ipd.md
- Item-Dependencies: none
- Status: to-review
- Coverage: pass
- Coverage-Fingerprint: b86a4c428cd6b72e2161ba7f23876aac6aa9ca80d88f8ace328579762a6ed797
- Coverage-Checked: 2026-10-16 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: bug
- Priority: medium
- From-Backlog: ui1aln
- Blocks-Release: next
- Set: cfgreloc
- Order: 0
- Highest E allocated: 05
- Author: opencode
- Id: c54a4z

## Workflow history

- 2026-10-16 coverage pass (aw oc run): fingerprint b86a4c428cd6, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready orchestrator graduating backlog ui1aln.

## Goal

`aw install <repo> --preset <p> --relocate` moves an installed repository between the target-placed and home-placed config layouts as one journaled move-verify-switch-retire transaction, so exactly one `project.json` is authoritative afterwards, every policy key, cutover date and record survives, and the old AW-owned footprint is removed (tracked deletions staged, never committed). Without `--relocate` every cross-placement write path refuses before writing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Children

- [ ] E-01 CONFIRM ppu39q REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans ppu39q` shows it under `executed/`.
  - Execution state: pending

- [ ] E-02 CONFIRM xvlemm REACHED executed
  - Depends on: E-01
  - Expected outcome: `aw find plans xvlemm` shows it under `executed/`.
  - Execution state: pending

- [ ] E-03 CONFIRM gjylny REACHED executed
  - Depends on: E-02
  - Expected outcome: `aw find plans gjylny` shows it under `executed/`.
  - Execution state: pending

- [ ] E-04 CONFIRM 6u755v REACHED executed
  - Depends on: E-02, E-03
  - Expected outcome: `aw find plans 6u755v` shows it under `executed/`.
  - Execution state: pending

- [ ] E-05 CONFIRM ozr356 REACHED executed
  - Depends on: E-04
  - Expected outcome: `aw find plans ozr356` shows it under `executed/`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `ppu39q` | `20261016-cfgreloc-01-ppu39q-refuse-a-cross-placement-policy-write-at-every-entry-point-a.ipd.md` | Path-based cross-placement detection helper; refusal at `persist_project_policy` and in `cli._run_install` before any write (closes the interactive-wizard and `--delivery-mode` bypasses); spec Section 8.1 placement-switch contract. | none |
| 02 | `xvlemm` | `20261016-cfgreloc-02-xvlemm-pure-placement-switch-planner-with-blockers-and-per-item-mov.ipd.md` | New `agent_workflows/placement_switch.py` with a pure, read-only `plan_placement_switch` returning per-class moves, discards, retirements and blockers. | `executed:ppu39q` |
| 03 | `gjylny` | `20261016-cfgreloc-03-gjylny-retire-the-old-placement-s-aw-owned-footprint-after-a-placem.ipd.md` | Footprint retirement scoped to ONE explicit side (target or home), reusing `engine.uninstall_repo` for the target side without its AW_HOME auto-detection. | `executed:xvlemm` |
| 04 | `6u755v` | `20261016-cfgreloc-04-6u755v-journaled-placement-switch-executor-with-verify-authority-fl.ipd.md` | `execute_placement_switch`: lock, stage, verify, single-file authority flip, retire, receipt; resume and rollback from a journal that survives the flip; fault injection. | `executed:xvlemm`, `executed:gjylny` |
| 05 | `ozr356` | `20261016-cfgreloc-05-ozr356-wire-the-placement-switch-into-aw-install-behind-an-explicit.ipd.md` | `aw install --relocate` / `--relocate-rollback`, dry-run preview, refusal message update, end-to-end subprocess tests both directions, CHANGELOG and README. | `executed:6u755v` |

Orders run strictly in sequence: each consumes the previous child's module surface.

## Completion criteria (the whole Set is done only when)

1. No install entry point (noninteractive `--preset`, interactive wizard, `--delivery-mode`/`--records-backend` flags) writes a `project.json` at a path other than the currently authoritative one unless a relocation was requested. Owner: ppu39q (E-02, E-03).
2. The placement-switch contract (supported pairs, opt-in, what moves, what is discarded, staging-not-committing, blockers) is written into spec `20260810-1447-01` Section 8.1. Owner: ppu39q (E-04).
3. A pure planner reports every move, discard, retirement and blocker for a switch without writing. Owner: xvlemm (E-01..E-03).
4. The old placement's AW-owned footprint can be retired on one explicit side without touching the other side. Owner: gjylny (E-01..E-03).
5. A switch is a journaled transaction that ends with exactly one authoritative `project.json`, preserved keys and cutovers, moved records, and resumes or rolls back after an injected crash. Owner: 6u755v (E-01..E-06).
6. `aw install --relocate` performs the switch end-to-end in both directions and every user-facing surface describes it. Owner: ozr356 (E-01..E-05).

## Cross-IPD validation

- Order 02's planner uses Order 01's `install_wizard.config_placement_switch` for detection, so the refusal and the planner can never disagree about what is a cross-placement switch. Owner: xvlemm (V-01).
- Order 04's retire phase calls Order 03's `retire_footprint` with the side the Order 02 plan names. Owner: 6u755v (V-03).
- Order 05's end-to-end tests assert the same invariants Order 04's unit tests do, through the real CLI. Owner: ozr356 (V-04).

## Deferred / out of scope (with reason)

- Switches into or out of `public-target-private-companion` (a second git repository and a companion identity are involved). They keep refusing safely.
  - Carrier: n9vd2h
- A `--records-backend` change on an installed repo that keeps the config placement (records silently orphaned; found while authoring, distinct root cause).
  - Carrier: wbz75c

## Scope check

- Over-scope: none. This plan contributes no code, test or record of its own.
- Under-scope: none; refusal (01), design contract (01), plan (02), retirement (03), transaction (04) and user surface (05) together are the relocation the backlog item names ("move config, policy keys and cutovers to the new placement, remove or retire the old one").

## Required tests / validation

This plan runs no tests. Each child runs its own module and the bare suite; Order 05 (`ozr356`) runs the end-to-end subprocess tests that exercise the whole Set.

## Open questions

### OQ-01: Why five children rather than one plan?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The work has independently testable layers with different risk: an immediate safety fix (01, which also closes live split-brain paths today), a pure planner (02), a destructive retirement primitive (03), a crash-safe transaction (04) and the CLI contract (05). Order 01 is valuable alone if later children stall, and isolating 03 keeps the only deletion code in a reviewable unit.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `aw find plans ppu39q` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw find plans xvlemm` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `aw find plans gjylny` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `aw find plans 6u755v` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `aw find plans ozr356` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) of this plan and each child. EXECUTION CONTRACT: all open questions are resolved. This plan performs no work of its own; each child carries its own scope fence, test evidence and path-scoped `aw commit`. Paste ACTUAL output for every confirmation; never claim a child executed that `aw find plans` does not show under `executed/`. Never push. Under `aw oc run` / `aw agy run` the runner retires this orchestrator once every child is `executed`; by hand, finalize it through `aw ipd finalize` after every `V-*` is `pass`.
