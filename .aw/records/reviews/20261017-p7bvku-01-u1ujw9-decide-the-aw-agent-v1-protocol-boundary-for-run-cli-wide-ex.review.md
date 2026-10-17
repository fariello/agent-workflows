# Review findings: plan u1ujw9

- Subject-Id: u1ujw9
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `3160faff3`. Plan committed and byte-identical to the lane input
(`cmp`), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before and after revisions;
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review (scratch repo, `aw run init`, workflow with `S-02` depending on `S-01`, `AW_NO_REEXEC=1`):
- F-1: `run finalize <id> --agent` on a fresh run prints a bare dict, rc 1; `--json` keys are exactly
  `error, exit_code, ok, predicates, reasons` (E-04 (c) bar is correct).
- E-04 (d) fixtures all reach their codes today with bare dicts: `run start <id> --step S-02` rc 3; a second
  `run init --run-id <same>` rc 6; `runs status <path to {"x": 1} jsonl>` rc 7; rewriting the header
  `run_id` to `BAD` then `runs status` rc 5 (`RL-E015`); a `tool_event` with `exit_code: 1` makes
  `run finalize` rc 4 (`EV-FAILED-EXIT`).
- `EXIT_INCOMPLETE` refusal sites in `run_cli.py`: the predicate-gate `_emit_machine` payload and the
  `PredicateUnsatisfiedError` `_emit_error` call (F-3 correct); line 1661 is `_run_status`'s success tail.
- `agent_schema.validate_agent_record` (`agent_schema.py:261-319`): exit 1 with `outcome: "fail"` on a
  `result` is accepted; `error` requires exit 2 (OQ-02 correct).
- Spec `25kzda` Section 5.6 row 4 text "renumbering shipped codes was explicitly refused on evidence ...
  approved spec `6kwd2e` R7.3 forbids collapsing the run family into `{0,1,2}`" resolves verbatim;
  `docs/cli-output-contract.md` Section 8 "Any breaking modification to record schema" resolves.
- Plan `2t033b` (reviewed) E-01 adds `_emit_agent_record(args, rec)` and names `u1ujw9` as a reuser;
  plan `2jzld4` (reviewed this sweep) edits the same three prose surfaces and excludes `run finalize` from
  its sweep record assertions.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric C (one canonical mechanism, P8) | plan E-01 (old text) "reuse ... its redact / `--fields` / `render_guarded_jsonl_record` sequence"; `2t033b` E-01 `_emit_agent_record` | E-01 named the sequence but not the helper `2t033b` factors it into, leaving room for a second copy. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now hands the record to `_emit_agent_record`; Expected outcome and V-02 demand the delegation. |
| PR-002 | MEDIUM | UNDER-SCOPE | Rubric G (cross-plan sequencing) | `2jzld4` E-05, E-08 edit `_emit_error` docstring, `command_surface` `runs next`/`runs resume` comments, `docs/cli-output-contract.md` 3 and 3.1 | Sibling plan edits the same prose with no ordering edge; the prescribed text ignored success answers becoming records, so the second plan to land would contradict or overwrite the first. | all Low | FIXED | E-03 and E-05 carry the mirror reconcile rule of `2jzld4`; Step 0 records the overlap. |
| PR-003 | LOW | IN-SCOPE | Rubric A (key precedence) | plan E-01 (old text) record literal ending `**extra` | `extra` spread LAST let an extra key override an envelope or legacy key; `2t033b` E-01 deliberately spreads it first. | all Low | FIXED | E-01 spreads `extra` first; V-02 demands the ordering in the diff. |
| PR-004 | LOW | UNDER-SCOPE | Rubric E (coverage honesty) | `run_cli._run_finalize` `except run_state.PredicateUnsatisfiedError`; `run_engine.py:481` | The second exit-1 site also becomes a record through E-01 but no test drives it and the plan did not say so. | all Low | FIXED | Step 0 states it is converted by the same branch and why no CLI fixture reaches it deterministically. |
| PR-005 | LOW | IN-SCOPE | Rubric G (stale claim) | plan Under-scope "`run finalize` exemption stays valid because the success payload is still bare"; `tests/conformance_matrix.MUTATION_EXEMPTION_REGISTRY["run finalize"]` reason_kind `arg_fixture_needed` | The stated reason is wrong (the entry exists for a missing positional) and becomes false once `2jzld4` lands. | all Low | FIXED | Reworded to the real reason and noted that `2jzld4` owns its reason text. |
| PR-006 | LOW | UNDER-SCOPE | Rubric G (execution contract) / suite contract | plan gate COMMIT `<this plan>`; regression commands `-q -n auto` | Placeholder in the commit path, no conditional runner/executor finalize ownership, and an extra `-q` that hides per-test detail. | all Low | FIXED | Spelled out the plan path, added POST-GATE LIFECYCLE (runner owns under `aw oc run`/`aw agy run`, `aw ipd finalize u1ujw9 ... --apply` by hand, never `git mv`), dropped the extra `-q`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Confirm OQ-01 option B (convert exit 1 only; 3 to 7 stay bare) without asking the maintainer? | Confirmed | Escalate as blocking (unnecessary: B changes no published contract); C, D, E (each changes a published contract) | `agent_schema.py:261-319` exit bound; `25kzda` 5.6 row 4; `docs/cli-output-contract.md` Sections 4 and 8; the exit-1 record is additive and keeps legacy keys | yes |
| D-2 | Add an ordering edge to `2jzld4` instead of a reconcile rule? | Reconcile rule | `executed:2jzld4` edge (serializes two independent plans) | Overlap is prose only; runner merge-and-revalidate integrates lanes | yes |
