# Review findings: plan 32jpl1

- Subject-Id: 32jpl1
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `35f406d51`; the plan was committed and unchanged, so no
snapshot. `aw ipd lint --phase author` and `--phase review-finalize` both clean. `- Kind: child`.

Re-measured in-process: `run_state.ALL_STATES` has 11 states and `TRANSITION_RULES` 19 edges as the
plan states; `TERMINAL_STATES_CANONICAL` has 14 tokens and intersects `ALL_STATES` in `failed`
only; `runner_shutdown.KNOWN_ITEM_STATUSES` has 28 tokens (already including `queued` and
`running`) and intersects `ALL_STATES` in `blocked`, `running`, `failed`; `canonical_terminal_status`
maps `partial`/`failed-safely`/`dependency-blocked` as claimed; `run_state` imports only
`collections.abc` and `typing`; `validate_transition` is pure and `check_transition` raises; both
drivers grep zero for `run_state`/`verify_roles`/`run_recovery`; each host's `save_state` is a
two-line wrapper over `runner_shared.save_state`; backlog `ildjse`/`ye28s6` and plans `eow7p4`,
`i18yaz`, `1bfppy` exist.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A/D (correctness; inertness invariant) | `runner_shared.execute_item_core` writes `item["status"] = "running"` then `item["status"] = disposition`; probe: `run_state.validate_transition('running','complete','runtime')`, `('running','correction_required','runtime')`, `('runnable','blocked','runtime')` and `('running','running','runtime')` all return `ST-ILLEGAL-TRANSITION` | The driver writes a COARSE sequence and never writes `performed`/`verifying`/`verified`, so a strict single-edge check flags every successful item (`queued->running->executed`), every verifier rejection, every dispatch-time dependency block, and every unchanged re-save. That makes E-04's inertness property unsatisfiable and the report useless. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03: skip unchanged positions; check `runtime`-authorized REACHABILITY through `run_state`'s legal edges, confirming each hop with `validate_transition`, recording the collapsed path. Probe showed all normal sequences legal and only leaving `complete`, backward from `verified`, or entering `cancelled` illegal. E-04/V-03/V-04 illegal case moved to the unreachable set; F-09 added. |
| PR-002 | HIGH | UNDER-SCOPE | C (failure handling) | `runner_shared.save_state` body is three lines and is called on every driver write on both hosts; `_verdict_state` precedent "never kill a run over a label" | Plan did not require the new check to be exception-safe, to persist in the same write, or to keep earlier violations when a later legal save overwrites the verdict. A bug in report-only code would wedge every run; overwritten violations would destroy OQ-01's corpus. | all Low | FIXED | E-03 requires a wrapped never-raising check run before `atomic_write_json`, a per-item appended violation list; E-04/V-03/V-04 test both. |
| PR-003 | HIGH | IN-SCOPE | E / AGENTS.md test-outcomes rule | `git log -- tests/test_runner_refork_guard.py`: deleted in `19313eed`; `runner_shared.map_verdict` docstring "no live guard currently enforces this"; `80db6750c` "delete 366 tests that pinned code structure" | E-05 told the executor to extend a guard that no longer exists and that belonged to the source-inspecting class the maintainer deleted; the conventions section claimed an explicit exception to the no-source-reading rule. | all Low | FIXED | E-05/V-05 rewritten as a behavioral proof: drive `oc_runipd.save_state` and `agy_runipd.save_state`, assert identical records, mutation-check by monkeypatching the shared translation. Conventions note and F-10 updated. |
| PR-004 | MEDIUM | IN-SCOPE | A (mapping correctness) | `TERMINAL_STATUS_ALIASES['blocked'] == 'fail-gate'`; `KNOWN_ITEM_STATUSES & ALL_STATES == {blocked, running, failed}`; `*->cancelled` rules authorize only `coordinator`/`human` | Same-spelled tokens mean different things (`blocked` is a gate refusal alias), and nothing stopped a `cancelled` row that would yield a violation the runtime can never avoid. No rows were proposed, leaving the core decision to the executor. | all Low | FIXED | E-01: false-friend warning, recommended rows (confirmable/overridable), no `cancelled` row. |
| PR-005 | MEDIUM | IN-SCOPE | G (execution contract) | gate "If it looks like it wants a ledger, read the parent's OQ-01 and stop"; POST-GATE LIFECYCLE lacked runner/hand ownership | Scope fence phrased as a stop rule (2026-09-01 ruling) and lifecycle transition ownership unconditional/unstated. | all Low | FIXED | Fence restated as a declaration with `--scope-reason`; conditional lifecycle ownership added. |
| PR-006 | LOW | IN-SCOPE | G (accuracy) | `pyproject.toml` addopts `-m 'not slow and not livecorpus'`; `KNOWN_ITEM_STATUSES` contains `queued`/`running`; `oc_runipd` audit path calls `atomic_write_json` directly | Stale addopts quote, redundant enumeration in E-02, and F-03 overstated `save_state` as the funnel for every `state.json` write. | all Low | FIXED | Conventions, E-02 and F-03 corrected. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should a coarse driver transition be judged against a fine-grained table? | Legal iff the target is reachable from the source via `runtime`-authorized edges; unchanged positions skipped. | Strict single edge (flags every success, PR-001); mapping `executed` to `running`-adjacent states to dodge it (falsifies positions); editing `run_state` to add edges (out of Scope-Paths, changes a shipped contract). | Review probe over `run_state.get_legal_transitions` (F-09); E-04 inertness property. | yes |
| D-2 | How to prove no host carries a private copy without reading source? | Drive both hosts' `save_state` wrappers and mutation-check by monkeypatching the shared translation. | Recreate the deleted source-inspecting guard (forbidden by AGENTS.md, deleted by maintainer). | `19313eed`, `80db6750c`, AGENTS.md "NEVER write or restore tests that read production source". | yes |
| D-3 | Should rows be prescribed or left to the executor? | Recommended rows, executor confirms or overrides with a stated reason. | Leave entirely open (core decision invented at execution); hard-prescribe (no room for a measured correction). | Probe showing the recommended rows keep all normal sequences legal under D-1. | yes |
