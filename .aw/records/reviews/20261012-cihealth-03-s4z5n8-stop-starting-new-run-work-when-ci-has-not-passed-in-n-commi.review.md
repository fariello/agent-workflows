# Review findings: plan s4z5n8

- Subject-Id: s4z5n8
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `7d8b0238c`. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` was clean after revisions (one advisory `IPD-Z602` on E-04, see D-3). No carrier findings at pre-transition.

Re-verified:
- `runner_shared.RunPolicyFlag` / `RUN_POLICY_FLAGS`: `--allow-uncovered-orchestrator-work`, `--allow-concurrent-driver`, `--ack-spec-edits` are `kind="str"` rows; the `--ack-spec-edits` row is `resume_rule=RESUME_REFUSE` because "`resume` does not call `initialize_run_core`".
- Row comments: spec `25kzda` 2.1 must declare every registered row in the same change.
- `runner_shared.initialize_run_core` calls `enforce_spec_edit_ack_gate` before the `prepare_only` early return and raises `DriverError` on refusal; `enforce_orchestrator_probe_gate` runs after it.
- Spec `25kzda` 2.1 grammar lists `[--ack-spec-edits <justification>]`; 2.5c defines the spec-edit gate with a durable refusal and `--prepare-only` siting; sections run to 2.5e.
- `tests/test_spec_edit_ack_gate.py` exercises the gate's events and justification directly.
- `.aw/config/project.json` has no CI keys yet; `config.release_gate_work_kinds` is the warn-and-fallback precedent.
- Orchestrator `cntxsm` cross-IPD rule "Order 03's always-allowed set includes this Set's plans" stays satisfied by `ci_red_exempt_sets = ["cihealth"]`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Gate bypass | `runner_shared.initialize_run_core` (spec-edit gate before the `prepare_only` return); `--ack-spec-edits` row `resume_rule=RESUME_REFUSE`; F-04 | E-02 did not say where the gate sits. Sited after `--prepare-only` it is bypassed by prepare-then-resume; and accepting the override "on `resume`" (as E-02 said) records consent that gates nothing, because resume never reaches the gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 sites `enforce_red_ci_gate` in `initialize_run_core` before the `--prepare-only` return, like the spec-edit gate; E-05 registers the flag with `RESUME_REFUSE`; E-03 adds (a2) and the resume refusal. |
| PR-002 | HIGH | IN-SCOPE | C. Canonical mechanism / spec | `RUN_POLICY_FLAGS` row comments; spec `25kzda` 2.1 grammar | The flag was to be added ad hoc to two parsers, and E-04 did not name spec 2.1, which must declare every registered flag in the same change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-05/V-05 registers a `RunPolicyFlag` row; E-04 names 2.1 grammar, its bullet, the `--full-auto` non-implication list, and a new 2.5f. |
| PR-003 | MEDIUM | IN-SCOPE | F. General-case | Scope (3), E-01 `- Set: cihealth` literal | A hard-coded Set id ships to every installing repository, where it means nothing, and stops exempting once a later CI repair lives in another Set. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Exemption is the setting `ci_red_exempt_sets` (default `[]`), set to `["cihealth"]` here; OQ-02 records it; `.aw/config/project.json` and `config.py` added to Scope-Paths. |
| PR-004 | MEDIUM | UNDER-SCOPE | C. Observability | spec `25kzda` 2.5c "Durable refusal record" | A refusal only printed and exited; `aw runs` would show nothing, unlike the sibling gates. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 records a durable refusal (code `red-ci`, event, state); V-02 demands the `aw runs` view. |
| PR-005 | MEDIUM | IN-SCOPE | A. Correctness | E-01 "a pure function" vs "Re-count commits ... against current main" | A pure predicate cannot run git; the re-count's owner and its failure case were unstated, and "main" ignored Order 02's `ci_checkup_branch` setting. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01: the caller re-counts against the configured branch and passes the count; an uncomputable count is UNKNOWN (warns). E-03 (g2) tests a stale record crossing N. |
| PR-006 | LOW | UNDER-SCOPE | E. Coverage | E-03 cases | Missing: a mixed queue (one exempt item, one not), `--full-auto` alone not overriding, `--prepare-only`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cases (a2), (d) mixed, (g2), (i) added; `tests/test_spec_edit_ack_gate.py` named as the neighbouring test that must stay green. |
| PR-007 | LOW | IN-SCOPE | G. Traceability | Proposed changes, Step 0, Findings | Sections did not reflect the new E-05 or the precedents the executor must follow. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Proposed changes reordered; Step 0 names `RUN_POLICY_FLAGS` and `initialize_run_core`; F-04, F-05 added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How are CI-repair plans exempted? | Project setting `ci_red_exempt_sets`, `["cihealth"]` here | Hard-coded `cihealth`; a new `- CI-Repair:` front-matter field (schema change for one gate) | AGENTS.md "General-case and configurable"; `config.release_gate_work_kinds` precedent | yes |
| D-2 | What does `--allow-red-ci` do on resume? | Refuse (`RESUME_REFUSE`) | Accept and freeze (`none-default`), which would record consent that gates nothing | `--ack-spec-edits` row comment; F-04 | yes |
| D-3 | Split E-04 for the `IPD-Z602` advisory? | Keep: the spec, README and CHANGELOG describe one change and are checked by one diff | Separate docs item | Advisory is `info`; V-04 demands each part | yes |
