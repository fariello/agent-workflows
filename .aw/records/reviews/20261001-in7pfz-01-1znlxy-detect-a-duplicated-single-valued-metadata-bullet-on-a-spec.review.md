# Review: Detect a duplicated single-valued metadata bullet on a spec

- Subject-Id: 1znlxy
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean.

The following were re-verified in this lane:

- `specs._metadata_end` and `validate_spec` match the plan's description.
- The backlog twin `backlog.validate_item` emits `backlog.metadata-bullet-repeated` with the cited detail, and its RuleSpec is `error`.
- `_DEFAULT_RULESPEC` is `error`.
- A census over 40 specs, inside `_metadata_end`, found exactly one repeated key: `Constrained-by`, 4 times in `wy9aru` and 4 times in `llbr2b`. Every other key in the proposed allowlist appears at most once and has no tooling reader in `agent_workflows/`.

The design is sound. The defects were in how the evidence demands fit the live baseline, a blast radius the plan did not state, one under-specified fixture, and the execution contract.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Architecture / blast radius (C) | agent_workflows/specs.py:968 `residual = validate_spec(path, new_text)` (run_set) and :1208 (run_migrate); agent_workflows/attention.py:1264 `_spec_record`; agent_workflows/runner_shared.py:19576 RUN-STRUCTURE-PREFLIGHT | `validate_spec` is also the residual refusal gate for `aw specs set`/`migrate`, the attention view's spec reader, and the runner preflight. A new error therefore blocks every tooled transition of an affected spec. The plan treated the change as `aw specs check` only, and also left open whether to copy the backlog twin's `Kind`->`Work-Kind` canonicalization. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now names every consumer and states the intended fail-closed consequence, with zero cost today per F-03. It also forbids the Kind canonicalization (`_WORK_KIND_RE` accepts `Work-Kind` only). |
| PR-002 | LOW | IN-SCOPE | Execution guidance | tests/test_check_engine_spec_criteria.py:140 `test_rule_id_contains_neither_graduation_nor_duplicate`; check_engine.py comment above `backlog.metadata-bullet-repeated` | E-03 told the executor to put rationale in "the plan's own history", which is tool-written. It also did not mention the registry-wide ban on `duplicate` in rule ids, which a well-meaning rename would trip. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rationale now goes in the twin's existing code comment, and the substring constraint is stated. |
| PR-003 | HIGH | IN-SCOPE | Evidence feasibility (G) | `aw specs check --agent` at review: `findings:1` (`attention.unsafe-field` on 89xjll); `aw check --agent`: 97 findings | E-04/V-04 required "both commands report conformance". Neither conforms on the live baseline, for reasons unrelated to this plan, so V-04 could never pass as written. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The check is now before/after: zero `spec.metadata-bullet-repeated` findings and an equal `aw specs check` diagnostic set. Pre-existing findings are named as such, and live counts are re-derived. |
| PR-004 | MEDIUM | IN-SCOPE | Testing (E) | Review probe: `Gate-Kind: date` + `Gate-Kind: decision` + `Gate-Ref: 2027-01-01` -> `attention.gate-malformed` only | E-05(b) said the new rule "does NOT suppress or duplicate the existing gate findings" without saying which fixture. Whether gate findings exist depends on which Gate-Kind `_read_gate` keeps (the last one). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into (b1) same valid kind, where the new rule is the only finding, and (b2) a conflicting kind, where exactly one of each finding appears, with the measured shape given. |
| PR-005 | MEDIUM | IN-SCOPE | Validation honesty | Sibling lanes measured pre-existing bare-suite failures (e.g. plan 0obt4k F-7: 3 failed) | V-05 asked for "the bare summary line" with no baseline, so a pre-existing red suite would make it either unsatisfiable or falsely reported. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Before/after bare runs are now required, and the bar is no NEW failure. |
| PR-006 | MEDIUM | UNDER-SCOPE | Execution contract | Plan `## Approval and execution gate` | The gate was missing two things: the scope-fence declaration semantics (`--scope-reason`/`--scope-ack`) and conditional ownership of the terminal transition (runner vs executor `aw ipd finalize`; no hand `git mv`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Canonicalize legacy `Kind` to `Work-Kind` as the backlog twin does? | No | Copy the twin verbatim | agent_workflows/specs.py:213 `_WORK_KIND_RE` matches `- Work-Kind:` only; no spec carries `- Kind:` (review census) | yes |
| D-2 | Accept the author's widened allowlist (OQ-01)? | Accept | Minimal `{Constrained-by}` | Review census: each extra key appears at most once and has no reader in `agent_workflows/` | yes |
| D-3 | What is E-04's success bar on a non-clean baseline? | Zero new-rule findings plus an unchanged spec diagnostic set | Absolute conformance, which is unsatisfiable | Live `aw specs check`/`aw check` captures at review | yes |
