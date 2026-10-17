# Review findings: plan 2jzld4

- Subject-Id: 2jzld4
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `e94d6f76d`. Plan committed and byte-identical to the lane input
(`cmp`), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase author`: `clean`; `--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review (scratch ledgers via `aw run init`, `AW_NO_REEXEC=1`):
- F-1/F-3 hold: `runs show|status|next|evidence|verify-ledger`, `run start|record|verify|cancel|finalize`
  under `--agent` print bare dicts with no `schema` key; `runs next` after `run start` exits 3 with
  `runnable_steps: []`; `run record --state failed` exits 3; `runs status` on a cancelled run exits 3 (F-4).
- `agent_schema.validate_agent_record` caps `exit` at (0, 1, 2) and forbids positive outcomes on exit 1
  (`agent_schema.py:261-319`), so `findings` for exit 1 is the only consistent choice (OQ-04).
- The eight `runs` leaves invoked with no target (as `test_agent_surface_conformance` will after the
  exemptions are removed) already emit valid `kind: "error"` records, exit 2, for both `--agent` and
  `--fields cmd`; `--json` parses as a dict. So E-07's universe expansion is satisfiable.
- `command_surface` declarations: all 13 leaves declare `agent_record_kind="result"`; `runs *` are
  `read`/`check`, `run *` are `mutation`, matching the universe computation in
  `tests/test_agent_surface_conformance.compute_conformance_universe`.
- `tests/conformance_matrix.EXEMPTION_REGISTRY` sanctioned_raw = 5 non-run + 8 `runs` = 13, so `(5)` is right.
- E-06 (e) fixture works: `RunLedgerStore.append` of a `tool_event` with a home-style `cwd` succeeds on a
  `seed_ledger_fixture` ledger and `runs evidence --agent` echoes the raw home path today (so the test is
  falsifiable); the writer sequence start/record/verify/finalize on that fixture exits 0 at each step.
- `run_viewer.py:986` is the only external caller of `_snapshot_payload` (plan claim correct).
- Plan `2t033b` (reviewed) E-01 adds `_emit_agent_record(args, rec)` and names `2jzld4` as a reuser;
  plan `u1ujw9` edits the same docstring, `command_surface` sentences and doc paragraphs and hands every
  success payload to this item (`- Carrier: nyvyb4`).
- `python3 -m pytest tests/test_live_conformance_sweep.py -o addopts="" -q -k mutation_leaves`: `1 passed`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric C (canonical mechanism, P8) | plan E-01 (old text) re-specified redact/`--fields`/render steps; `2t033b` E-01 `_emit_agent_record` "the ONE `--agent` record emitter that plans `2jzld4` E-01 and `u1ujw9` E-01 reuse instead of copying" | E-01 re-implemented the sanitize / project / guarded-render sequence that its dependency factors into one helper for this plan, creating two copies that would drift. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now builds the envelope and calls `_emit_agent_record`; Expected outcome and V-01 demand the delegation. |
| PR-002 | MEDIUM | UNDER-SCOPE | Rubric G (sequencing / cross-plan) | `u1ujw9` E-03, E-05 edit `_emit_error` docstring, `command_surface` `runs next`/`runs resume` comments, `docs/cli-output-contract.md` 3/3.1; both plans depend only on `2t033b` | Two sibling plans rewrite the same three prose surfaces with no ordering edge, and neither said how to merge with the other; whichever landed second would overwrite or contradict the first. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 and E-08 carry an explicit reconcile rule (keep the other plan's statement if landed, otherwise describe that class as pending `p7bvku`); F-7 records the overlap. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric G (stale claim) | plan E-05 prescribed sentence "only exit-0/1 answers and exit-2 refusals are records while codes 3, 5 and 7 stay bare" | If `u1ujw9` lands first, the prescribed sentence is false (exit-1 refusals are records too). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Folded into the E-05 reconcile rule: final text must be true of the code at this plan's commit. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric E (unsatisfiable check) | plan E-07 "assert the same for the agent mode of each step"; `tests/test_live_conformance_sweep.py` steps list `run finalize` expected rc 1; `run_cli._run_finalize` "Completion predicate gate" branch emits a bare `_emit_machine` refusal | The mutation sweep's `run finalize` step exits 1 through a REFUSAL this plan does not convert, so requiring `validate_agent_record == []` for every step would fail; it only passes if `u1ujw9` happens to land first. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 restricts record assertions to `run start`, `run record`, `run cancel`, keeps finalize's parse-as-dict check with a comment naming `u1ujw9`; Step 0 notes the refusal/answer distinction. |
| PR-005 | LOW | IN-SCOPE | Rubric G (traceability) | plan Deferred "Carrier: p7bvku" for exit-3 success answers; `u1ujw9` Deferred "`--agent` SUCCESS payloads ... `- Carrier: nyvyb4`" | Circular hand-off: each item names the other as owner of exit-3 success answers, so nobody owns the decision. | all Low | FIXED | Changed to `Carrier-Declined` with the reason; the boundary is decided here, documented by E-08 and pinned by E-06 (d). |
| PR-006 | LOW | UNDER-SCOPE | Rubric F (honest docs / Section 11.1) | `docs/cli-output-contract.md` Section 11.1 ("non-refused empty queries ... `outcome: "clean"`, `exit: 0`"); `run_cli._emit_projection` exit 1 on empty | `runs decisions` and `runs questions` with nothing recorded will emit `outcome: "findings"`, which disagrees with Section 11.1; the plan did not record the tension. | all Low | FIXED | Added a Deferred entry (`Carrier-Declined`) citing the declared exit contract and OQ-04. |
| PR-007 | LOW | UNDER-SCOPE | Rubric E (regression coverage) / AGENTS suite contract | plan Under-scope names `tests/test_records_root_accessor.py`; regression command omitted it; several commands passed `-q` on top of addopts-cleared runs | A named consumer was not in the regression run; an extra `-q` hides per-test detail the evidence needs. | all Low | FIXED | Added the file to the regression command; dropped `-q` from the `-n auto` commands. |
| PR-008 | LOW | UNDER-SCOPE | Rubric G (execution contract) | plan `## Approval and execution gate` lacked a lifecycle clause; COMMIT listed `<this plan>` placeholder | No conditional runner/executor ownership of `aw ipd finalize`, and the commit path list carried a placeholder. | all Low | FIXED | Added POST-GATE LIFECYCLE (runner owns under `aw oc run`/`aw agy run`, `aw ipd finalize 2jzld4 ... --apply` by hand, never `git mv`); spelled out the plan path. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Add an ordering edge between `2jzld4` and `u1ujw9` instead of a reconcile rule? | Reconcile rule, no new edge | `executed:u1ujw9` edge (serializes two independent low-priority plans and couples this one to a protocol decision it does not need) | Both plans touch only prose for the overlap; runner integrates lanes through merge-and-revalidate (AGENTS "The runners own ordering") | yes |
| D-2 | Should the mutation sweep assert `run finalize`'s exit-1 refusal shape here? | No; leave it to `u1ujw9` | Assert bare (breaks when `u1ujw9` lands); assert record (fails until it lands) | `run_cli._run_finalize` incomplete branch is a refusal; `u1ujw9` E-02 owns it | yes |
| D-3 | Who owns exit-3 success answers? | This plan, as Carrier-Declined with documented boundary | Leave `Carrier: p7bvku` (circular per `u1ujw9` Deferred) | `u1ujw9` Deferred `- Carrier: nyvyb4`; `agent_schema.validate_agent_record` exit bound | yes |
