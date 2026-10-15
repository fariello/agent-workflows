# Review findings: plan o34rb3

- Subject-Id: o34rb3
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `cd17d8b86`. The plan was committed and byte-identical to the
lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`, 0 findings. Not an
orchestrator. `aw check`: one `info` (`check.lifecycle-transition-unvalidated`, same-day history), no
finding on `From-Spec: none`.

`aw run init` (`v47z9u`, `reviewed`) has not landed. The E-03/E-04 check was simulated by wrapping
`run_cli._build_engine` in a pytest plugin under the lane's gitignored `.aw/state/` (deleted afterwards)
and run over every test file seeding a `kind: "run"` record: `2 failed, 99 passed`, both failures in
`tests/test_run_recovery_cli.py` from `_run_record`'s placeholder digest; with `_run_record` also simulated
to hash `_WORKFLOW`, that file went `52 passed`. `tests/test_run_cli_declarations.py` passed all six tests
unchanged under the check.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | A (partial failure) | `v47z9u` E-04 (atomic reserve + cleanup); authored E-02 ("after appending") | Writing `workflow.json` AFTER the header leaves a valid ledger with no workflow file if the write fails, and every later `--workflow`-less leaf silently falls back to the step-less skeleton. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 writes it first (atomic), inside the reserved dir so `v47z9u`'s cleanup covers it; a write failure exits 6; F-08 added. |
| PR-002 | MEDIUM | IN-SCOPE | A (correctness) | `agent_workflows/run_cli.py` `_load_workflow_arg` (`return data if isinstance(data, dict) else None`) | The authored E-03 raised for a non-object sibling file but left the explicit `--workflow` branch returning `None`, which silently bypasses the new digest check via the skeleton fallback. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 makes both branches raise; V-03 and E-06 (e) test it; F-06 added. |
| PR-003 | MEDIUM | IN-SCOPE | C (cross-plan contract) | `v47z9u` E-03 (`compute_record_hash(workflow)`); `run_engine._normalize_workflow` | The equality silently depends on `v47z9u` hashing the same mapping with the same function; a divergence would make every operator ledger refuse. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 verifies equality empirically and stops if it differs; E-04 hashes the mapping as loaded (wrapper included); F-07 added. |
| PR-004 | MEDIUM | UNDER-SCOPE | G (docs sync) | `agent_workflows/cli.py` `_register_run_leaf` (`--workflow` help); `docs/cli-output-contract.md` Section 3.1 | The `--workflow` help ("else derived from the ledger") and the Section 3.1 code-2 text become false or incomplete; the Spec/doc section claimed no change was needed, and no CHANGELOG line existed for a user-visible change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-08/V-08; Scope-Paths gains `cli.py`, the contract doc and CHANGELOG; Spec/doc sync rewritten; F-09 added. |
| PR-005 | MEDIUM | OVER-SCOPE | F (KISS) | review simulation: `tests/test_run_cli_declarations.py` 6 of 6 pass under the check | The authored E-05 edited `test_runs_resume_exit_3_is_reachable_and_declared`'s digest, which the check never reaches as a mismatch; churn in an undeclared-need file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Edit removed; file dropped from Scope-Paths; F-04 rewritten with the measurement. |
| PR-006 | LOW | IN-SCOPE | E (test strength) | authored E-06 | E-06 named topics, not assertions: nothing proved `depends_on` came from the persisted file (a step-less skeleton plus `--step` would also pass `start`), and the deleted-file fallback and failing-before demand were missing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 (a)-(f) with `runs next` listing `S-02` only after `S-01` performs; failing-before for (a)/(b). |
| PR-007 | LOW | IN-SCOPE | B (privacy) / UX | authored E-04 message | The mismatch message did not say which source mismatched, and paths there could carry an absolute home path (D92). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 names the source by the path as given or by filename; V-04 checks no absolute path. |
| PR-008 | LOW | IN-SCOPE | G (metadata) | `AGENTS.md` (From-Spec carries a spec id6) | `- From-Spec: none` is a non-id value in a field meant for an id6; absence is the documented way to say "no spec". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Field removed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Write `workflow.json` before or after the header? | Before, inside the reserved directory. | After (REJECTED: header-without-workflow failure mode, PR-001). | `v47z9u` E-04 cleanup-on-failure. | yes |
| D-2 | Should an explicit `--workflow` JSON array still fall back? | No; refuse exit 2 in both branches. | Keep returning `None` (REJECTED: silently bypasses the digest check). | `_build_engine` already maps `ValueError` to exit 2. | yes |
| D-3 | Edit `tests/test_run_cli_declarations.py`? | No. | Align its digests (REJECTED: measured unnecessary). | Review simulation, F-04. | yes |
| D-4 | Exit code for a mismatch? | 2 (`EXIT_INVALID_INVOCATION`), as authored. | 7 or a new code (REJECTED: 7 means "not a ledger"; a new code would change every `exit_contract`). | `docs/cli-output-contract.md` Section 3.1. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
