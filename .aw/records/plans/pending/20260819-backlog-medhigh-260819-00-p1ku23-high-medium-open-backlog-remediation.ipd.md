# IPD: high+medium open backlog remediation

- Date: 2026-08-19
- Concern: The open backlog carries 3 high + 7 medium items. This orchestrator drives the whole set through the IPD lifecycle. During scoping, one item (d3jkws /handoff) was found ALREADY EXECUTED and closed to done outside this Set; the remaining nine are the child Orders below. Two are human/process-owned (Orders 03, 08) and carry a `-human` slug facet on the human part.
- Scope: Drive child Orders 01..09 (author -> human approval -> execute -> verify -> transition), owning verification + path-scoped commits, never pushing. OUT: the d3jkws item (already done, closed separately); Order 03/2p6mgq (RETIRED to not-executed by maintainer decision - disclosure is human-owned end to end); the release itself (Section 9).
- Kind: orchestrator
- Status: reviewed
- Set: backlog-medhigh-260819
- Order: 0
- Highest E allocated: 01
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: p1ku23

## Workflow history

- 2026-08-19 revised (opencode, maintainer decision): Order 03 (2p6mgq disclosure) RETIRED to not-executed (human-owned end to end); the Set is now eight executable child Orders (01,02,04,05,06,07,08,09). Order 06 renamed to `/aw research` (namespaced under Order 05's dispatcher), so 06 now depends on 05.

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created - one Set addressing all high+medium open backlog items; d3jkws was verified already-executed and closed to done, so it is not a child here.
- 2026-08-19 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; PR-000-1..3 (status to-review, canonical serial-runner note, Order 02 dependency clarified as soft-after). GO - PENDING HUMAN APPROVAL. Set-level scope accounting (3 high + 7 medium = 10; eight child Orders + d3jkws already done) verified against the open backlog.

## Goal

Remediate the actionable high+medium open backlog in one coherent Set: fix the pip-install packaging defect (revnjq), harden install (u298fd), the HPC pointer (3srje9; the 2p6mgq disclosure Order was retired to not-executed - human-owned), IPD-scaffold grammar enforcement (7vd36f), the single `/aw` slash namespace (q19z5t), the `/research` producer (6wlo04), a regression test for the already-implemented gitignore-honoring inventory walk (ith2xd), and the stale-`.agents/`-litter sweep (wxz7gg). Each child closes its backlog item on execution.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: drive the Set

- [ ] E-01 Drive the eight child Orders (01, 02, 04, 05, 06, 07, 08, 09; Order 03 retired) through the IPD lifecycle SEQUENTIALLY, in this exact order: `01 -> 07 -> 04 -> 05 -> 08 -> 02 -> 09 -> 06`. NO PARALLELISM: although the pure dependency graph (02/09 depend on 01; 06 depends on 05; 04/07/08 free) would permit waves, the Orders have heavy SHARED-FILE contention - `agent_workflows/cli.py` (01,02,04,06,08,09), `engine.py` (02,05,06,09), `tests/test_installer.py` (02,05,07,08,09), `.aw/system/workflows/index.md` (02,05,06), and `layout_inventory.py`/`test_acceptance_matrix.py` (01,07) - so concurrent agy runs would clobber each other's edits and collide on the shared working tree + pre-commit stash. Run one Order fully (execute -> validate -> transition -> commit) before starting the next. The chosen sequence honors 01-before-{02,07,09} and 05-before-06 and otherwise spaces the cli.py/engine.py/test_installer.py writers. EXECUTION METHOD (maintainer decision): execute each Order with the Antigravity runner `python3 tools/agy_run.py <order-id6>` (the NEW unified runner; NOT the legacy `antigravity_execute_ipd.py`). BLOCK on it (run synchronously, wait for the result; never background it). `agy_run.py` runs the Gemini execution turn PLUS an automatic Turn-2 skeptical evidence-backed audit in-session (this is the anti-green-washing lever from the gemini-actually-validate playbook, `6zf5av`). Then, as the VALIDATE gate, opencode INDEPENDENTLY verifies every `V-*` item of that Order against real evidence (run the named tests/commands itself, paste ACTUAL runner output) BEFORE transitioning - never accept agy's "passed" without opencode's own proof (belt: agy Turn-2 audit; suspenders: opencode independent validation). Only after independent validation passes: mark E/V performed with the pasted evidence, transition the Order to executed/, and close its backlog item to `done`. Commit path-scoped, never push.
  - Depends on: none
  - Expected outcome: all eight child Orders reach `executed` (each executed via `tools/agy_run.py`, then independently validated by opencode with pasted evidence) and their backlog items are `done`; the completion criteria below hold.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id) | Item | What it does | Depends on |
|---|---|---|---|---|
| 01 | m2h1z4 | revnjq (high) | ship `tools.awphysical` inside the package (or inline its inventory) so `aw migrate-layout` + install-time migration work when pip-installed | none |
| 02 | 0qj4on | u298fd (high) | install-time split-brain guard (detect `.aw` bookkeeping beside `.agents/workflows` content, refuse/repair) | soft-after 01 (shares migration path; no hard import dependency - see Order 02 gate) |
| 04 | v1rj3p | 7vd36f (med) | `aw ipd scaffold` enforces the clustering filename grammar + requires Set metadata | none |
| 05 | ckw2ze | q19z5t (med) | single `/aw <verb>` slash namespace over the workflows (+ per-host grammar verify + back-compat aliases) | none |
| 06 | 0drnpf | 6wlo04 (med) | `/research [topic]` producer workflow drafting a house-conformant handoff prompt into prompts/pending | none |
| 07 | m7e2g3 | ith2xd (med) | verify + add the missing regression test that `aw_layout_inventory._walk` prunes gitignored subtrees (code already implemented) | none |
| 08 | 0zxfic | 3srje9 (med) | HPC/shared-host: optional loud installer warning (CODE) + a circulation note the human owns (`-human` part) | none |
| 09 | plt26j | wxz7gg (med) | migration/uninstall detects + offers to sweep untracked stale-tool litter under a migrated `.agents/` | 01 (migration engine) |

## Completion criteria (the whole Set is done only when)

- All eight child Orders show `Status: executed` under `.aw/records/plans/executed/`.
- Each corresponding backlog item is `done`.
- The full serial suite is green after the final Order (the canonical serial runner is `make test-serial`, i.e. `python3 -m unittest discover -s tests -t .`; `python3 -m pytest -p no:xdist` is an equivalent serial run only when the `.[test]` extra is installed); `aw attention --check` / `aw sanitize --agent` clean.
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
  - Required evidence: `ls .aw/records/plans/executed/*backlog-medhigh-260819-0[124-9]*` (Order 03 retired to not-executed) shows all eight child Orders with `Status: executed`; `aw backlog check` shows the eight items `done`; the final full serial suite tail (`make test-serial` / `python3 -m unittest discover -s tests -t .`) + `aw attention --check`/`aw sanitize --agent` clean are pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution method + contract: each child Order is EXECUTED by the Antigravity runner `python3 tools/agy_run.py <id6>` (new unified runner, run BLOCKING/synchronously, never backgrounded; it does a Gemini execution turn + an automatic Turn-2 skeptical evidence audit). opencode then INDEPENDENTLY VALIDATES that Order's V-items with real, pasted runner output before transitioning it - agy's "passed" is never trusted without opencode's own evidence. Path-scoped commits, never push, lifecycle move per Order. This orchestrator transitions to executed only after all eight children are executed + independently validated and their backlog items are `done`. Do not claim Set completion until V-01 is verified with concrete evidence.

Backlog status handling (maintainer question resolved): the backlog vocabulary is `open | blocked | parked | done` - there is NO "in-progress" status, and we deliberately do NOT add one (the APPROVED IPD is itself the in-flight signal; a second status would be duplicate state, GUIDING_PRINCIPLES P8). Each item stays `open` until its Order transitions to executed, then flips to `done` (the Order's final E-item does this). The `2p6mgq` OpenCode-disclosure item is NOT touched by this Set at all - its Order 03 was retired to not-executed and the disclosure is human-owned; it stays `open` until the maintainer sends the disclosure and closes it.
