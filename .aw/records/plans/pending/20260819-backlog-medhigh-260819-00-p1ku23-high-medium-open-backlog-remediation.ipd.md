# IPD: high+medium open backlog remediation

- Date: 2026-08-19
- Concern: The open backlog carries 3 high + 7 medium items. This orchestrator drives the whole set through the IPD lifecycle. During scoping, one item (d3jkws /handoff) was found ALREADY EXECUTED and closed to done outside this Set; the remaining nine are the child Orders below. Two are human/process-owned (Orders 03, 08) and carry a `-human` slug facet on the human part.
- Scope: Drive child Orders 01..09 (author -> human approval -> execute -> verify -> transition), owning verification + path-scoped commits, never pushing. OUT: the d3jkws item (already done, closed separately); the release itself (Section 9).
- Kind: orchestrator
- Status: draft
- Set: backlog-medhigh-260819
- Order: 0
- Highest E allocated: 01
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: p1ku23

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created - one Set addressing all high+medium open backlog items; d3jkws was verified already-executed and closed to done, so it is not a child here.

## Goal

Remediate the actionable high+medium open backlog in one coherent Set: fix the pip-install packaging defect (revnjq), harden install (u298fd), the disclosure + HPC human/process items (2p6mgq, 3srje9), IPD-scaffold grammar enforcement (7vd36f), the single `/aw` slash namespace (q19z5t), the `/research` producer (6wlo04), a regression test for the already-implemented gitignore-honoring inventory walk (ith2xd), and the stale-`.agents/`-litter sweep (wxz7gg). Each child closes its backlog item on execution.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: drive the Set

- [ ] E-01 Drive child Orders 01..09 through the IPD lifecycle in dependency order (author -> `/plan-review` -> human approval -> execute -> verify -> transition to executed/), owning verification and path-scoped commits for each, never pushing; close each item's backlog entry to `done` as its Order executes.
  - Depends on: none
  - Expected outcome: all nine child Orders reach `executed` and their backlog items are `done`; the completion criteria below hold.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id) | Item | What it does | Depends on |
|---|---|---|---|---|
| 01 | m2h1z4 | revnjq (high) | ship `tools.awphysical` inside the package (or inline its inventory) so `aw migrate-layout` + install-time migration work when pip-installed | none |
| 02 | 0qj4on | u298fd (high) | install-time split-brain guard (detect `.aw` bookkeeping beside `.agents/workflows` content, refuse/repair) | 01 (shares migration path) |
| 03 | 38yl4s | 2p6mgq (high) | coordinated-disclosure PACKET + tracking record; the SEND is human-owned (`-human`) | none |
| 04 | v1rj3p | 7vd36f (med) | `aw ipd scaffold` enforces the clustering filename grammar + requires Set metadata | none |
| 05 | ckw2ze | q19z5t (med) | single `/aw <verb>` slash namespace over the workflows (+ per-host grammar verify + back-compat aliases) | none |
| 06 | 0drnpf | 6wlo04 (med) | `/research [topic]` producer workflow drafting a house-conformant handoff prompt into prompts/pending | none |
| 07 | m7e2g3 | ith2xd (med) | verify + add the missing regression test that `aw_layout_inventory._walk` prunes gitignored subtrees (code already implemented) | none |
| 08 | 0zxfic | 3srje9 (med) | HPC/shared-host: optional loud installer warning (CODE) + a circulation note the human owns (`-human` part) | none |
| 09 | plt26j | wxz7gg (med) | migration/uninstall detects + offers to sweep untracked stale-tool litter under a migrated `.agents/` | 01 (migration engine) |

## Completion criteria (the whole Set is done only when)

- All nine child Orders show `Status: executed` under `.aw/records/plans/executed/`.
- Each corresponding backlog item is `done`.
- The full serial suite is green after the final Order; `aw attention --check` / `aw sanitize --agent` clean.
- The pip-installability of migrate-layout (Order 01) is proven in an installed wheel.

## Cross-IPD validation

- Orders 01, 02, 09 all touch the migration/install path; verify no conflicting edits (execute 01 first, then 02 and 09 rebased on it).
- Orders 05 and 06 both add workflows; verify `index.md` + host shims stay consistent (no duplicate/omitted entries).

## Deferred / out of scope (with reason)

- d3jkws (/handoff): already executed (agentcont-03); closed to done during scoping, not a child.
- The human SEND of the disclosure (Order 03) and the human CIRCULATION of the HPC how-to (Order 08): human-owned, marked `-human`; the Orders deliver the agent-doable artifacts only.
- The 2.0.0 release: Section 9, human-gated.

## Scope check

- Over-scope: none - every child maps to an open high/medium backlog item.
- Under-scope: none - all ten items are addressed (nine Orders + one verified-and-closed).

## Required tests / validation

Each child carries its own tests/validation; the Set is validated by the completion criteria above (full suite green, backlog items done, installed-wheel proof for Order 01).

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Scope was resolved interactively with the maintainer (one IPD per item unless already fully executed; human-only work carries a `-human` slug). No open decision.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `ls .aw/records/plans/executed/*backlog-medhigh-260819-0[1-9]*` shows all nine child Orders with `Status: executed`; `aw backlog check` shows the nine items `done`; the final full serial suite tail + `aw attention --check`/`aw sanitize --agent` clean are pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: an orchestrator does not itself edit code; it drives the child Orders, each of which carries its own execution contract (path-scoped commits, never push, paste actual runner output, lifecycle move). This orchestrator transitions to executed only after all nine children are executed and their backlog items are done. Do not claim Set completion until V-01 is verified with concrete evidence.
