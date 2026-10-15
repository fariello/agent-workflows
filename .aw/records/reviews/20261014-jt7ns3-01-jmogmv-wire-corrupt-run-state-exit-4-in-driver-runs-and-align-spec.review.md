# Review findings: plan jmogmv

- Subject-Id: jmogmv
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed in an isolated review lane, with no human channel. The plan was committed and unchanged (`046aabcbf`), so no snapshot was needed. `aw ipd lint --phase author` was clean before the review; after it, lint reports only `IPD-Q501` for the newly escalated blocking OQ-01, which is intended. The pre-transition carrier rule was already satisfied (`Carrier: 9epp40`, `Carrier: 6g08rp`; both plans exist in `pending/`).

Two throwaway probes ran under the gitignored `.aw/state/` and were deleted:

- `main(["resume", <run_dir>, "--repo", ...])` on both hosts. A missing `state.json` gives rc 2 and `Run not found` (`runner_shared.resolve_run_dir` refuses before `load_state` runs). An unparseable `state.json` gives rc 2 and `Invalid JSON`. With `--agent`, stdout carries an `aw.agent/v1` result with `"exit":2,"outcome":"cannot-run"`.
- The real `run_queue` on both hosts with a stubbed turn that corrupts `state.json` after its own `save_state`. Unparseable state raised `DriverError: Invalid JSON ...` out of `run_queue` with 1 turn dispatched. `{"queue": "x"}` raised `AttributeError: 'str' object has no attribute 'get'`.
- `agent_schema.render_jsonl_record` on a result with `exit: 3` raised `ValueError: Field 'exit' must be an integer in (0, 1, 2)`.
- `run_evidence.aggregate_run_exit((), run_wide_abort_class="Corrupt run ledger").exit_code == 4`, and `ABORT_CLASSES == ("Corrupt run ledger",)`, so the plan's constant value is a member.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | B/C. Public contract (agent surface) | `oc_runipd.py:5765` `if runner_shared.is_agent_mode(args):` -> `emit_agent_run_refusal_record` (`"exit": 2`); `agent_schema.py:264` `exit_code not in (0, 1, 2)`; `docs/cli-output-contract.md:173` and `:177` | The plan's new `main` handler returns 4 but does not say what `--agent` mode does. Emitting an agent record with exit 4 raises, while emitting none or keeping 2 breaks either exit parity or the same-code-on-every-surface rule. That is a public CLI contract choice. | C:Medium; U:Medium-High; S:Low; F:Medium; Overall:Medium-High | OPEN | Raised as plan OQ-01 (`Blocking: yes`, `Finding: PR-001`) with options and a recommendation (a). E-02, E-03, E-04 and V-04 now defer to it. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness of premise (F-02/E-02) | `oc_runipd.py:4295` `try: execute_item(...)` is the only body of the item-local `try`; `load_state` reloads at `oc_runipd.py:4036` sit outside it; review probe: mid-run corruption raised out of `run_queue` on both hosts | F-02 claimed a mid-run `load_state` failure would be swallowed as item-local `failed-safely`, and E-02 added `except CorruptRunStateError: raise` to `run_queue`. No `load_state` is reachable inside that `try`, so the handler is dead code built on a false finding. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected F-02 and removed the `run_queue` handler from Scope, E-02, Proposed changes and V-02. E-04 keeps the mid-run test, which now injects corruption from a stubbed turn. |
| PR-003 | MEDIUM | IN-SCOPE | P16 / test design | old E-04(2) `oc_runipd.CorruptRunStateError is agy_runipd.CorruptRunStateError is runner_shared.CorruptRunStateError`; old E-04(3) `decl.exit_contract == (0, 1, 2, 3, 4)` | Both assertions pin structure (class identity, a literal declaration tuple) rather than behavior. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with behavior: `load_state` raises on the three corruption shapes, and each driver's OBSERVED corrupt-state exit is a member of its declared `exit_contract`. |
| PR-004 | MEDIUM | IN-SCOPE | Evidence / anchors | spec `25kzda` line 1427 `(c) Failures that abort the run (1 member):` / line 1429 `- corrupt run ledger only.`; `docs/cli-output-contract.md:205` | E-03 quoted a group (c) anchor (`* **(c) Run-wide abort: ...** —`) that does not exist. It also cited a Section 3.1 "summary table row" for the runipd exit set, when the text that needs to change is the table-2 bullet saying 4 is "not returned by current driver `run_queue` dispatch". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote both anchors to the real text and required single-line edits to preserve line offsets. |
| PR-005 | MEDIUM | UNDER-SCOPE | Doc sync / D | `command_surface.py:1960` `# Neither \`4\` nor \`130\` is reachable through \`run_queue\`` | The in-code rationale above the `oc runipd` declaration would become false once 4 is returned, and the plan did not update it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the comment update to E-02. |
| PR-006 | MEDIUM | UNDER-SCOPE | E. Sensitivity | old V-04 | Nothing proved the new tests fail without the fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 now demands a pasted run with `main`'s handler removed, where the tests fail with rc 2, plus an empty diff after the revert. The narrowed pytest uses `-o addopts=""`. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | old gate "transition the plan to `executed` via `aw ipd set executed jmogmv`"; `- Scope-Paths:` | The gate instructed the executor to transition the plan itself (which is the runner's job under `aw oc run`). It also lacked a scope fence, the honesty rule, the never-push/never-tag rules and a staged-set check. The plan file was not in Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced the gate with the full contract, including runner-versus-hand finalize ownership and the Section 4.2 transcription lock. Added the plan path to Scope-Paths. |
| PR-008 | LOW | IN-SCOPE | E. Test precision | probe: missing `state.json` -> `Run not found` from `resolve_run_dir` | The missing-file case never reaches `load_state` through `resume`, so it cannot test `load_state`'s missing-file branch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 asserts only rc 2 there and states why. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep the `run_queue` handler as defense in depth? | Remove it | Keep it (dead code with a false rationale) | `oc_runipd.py:4295` item-local `try` body; review probe | yes |
| D-2 | How should the declaration change be tested without a literal pin? | Observed exit is a member of `get_declaration(...).exit_contract` | Literal tuple equality (P16 pin) | AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; `command_surface.get_declaration` at `command_surface.py:2496` | yes |
| D-3 | Resolve the agent-surface question myself? | No: escalated as blocking OQ-01 | Pick (a) silently | It is a public CLI contract (plan-review 3.1: never guess a human decision) | n/a (escalated) |
