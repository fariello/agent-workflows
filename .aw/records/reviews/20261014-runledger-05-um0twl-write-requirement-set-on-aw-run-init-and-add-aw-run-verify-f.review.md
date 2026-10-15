# Review findings: plan um0twl

- Subject-Id: um0twl
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (LOW, fixed), PR-010 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `252e476c5`. The plan was committed and byte-identical to the
lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`, 0 findings. Not an
orchestrator.

`aw run init` (`v47z9u`, `reviewed`) and `aw run verify` do not exist. A probe under the lane's gitignored
`.aw/state/` (deleted afterwards) appended a header plus a `requirement_set` built by a simulated
R-NN-preserving freezer through `run_freeze.requirement_set_record` and `RunLedgerStore.append`, recorded a
verifier decision through `RunEngine.record_verifier_decision`, and drove the real CLI: the chain reached
`run finalize` exit 0 / `run_state: "complete"` and `runs status` exit 0 with and without `--workflow`
(plan F-07). The goal is feasible as designed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G (executability) | `agent_workflows/command_surface.py` `CommandDeclaration` (fields `command`..`canonical_command`) | E-04's declaration used `requires_apply`, `supports_check`, `supports_json`, `supports_agent`, `notes`: none exist, so the module would raise `TypeError` at import and break the whole CLI. It also named `command_surface._DECLARATIONS` (the tuple is `COMMAND_INVENTORY`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 gives the real-field declaration modeled on `run record`; F-10 added. |
| PR-002 | HIGH | IN-SCOPE | G (executability) | `agent_workflows/cli.py` `_register_run_leaf(group, name, help_text, desc)`, `_run_leaf_specs` | E-04 called `_register_run_leaf(run_sub, "verify", ..., _lazy(...))`: wrong arity and a handler argument the registrar does not take (routing is by `run_command` in `run_cli.run_cli`). The dispatcher edit was missing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 adds a `_run_leaf_specs` row, the flag blocks, and the `run_cli.run_cli` branch. |
| PR-003 | MEDIUM | IN-SCOPE | A (correctness) | probe: `record_verifier_decision("R-99", ...)` appended; on a cancelled run appended; invalid result raised `SchemaInvalidRecordError` (`LedgerCorruption`) | E-03 allowed ids from `--workflow` (inert for completion), did not refuse decisions on terminal runs, and an invalid `--result` reaching the engine would report exit 5 "corrupted" for a typo. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 checks ids against `requirement_set` only, refuses terminal runs (6), validates `--result` before the engine; OQ-03 added; F-08 added. |
| PR-004 | MEDIUM | IN-SCOPE | A (consistency) | `run_freeze._digest(category, normalized)`; `diff_requirements` | E-02 digested `(category, id, text)`, diverging from the module's semantic identity (a renumbered identical requirement would look redefined). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 reuses `_digest` and the existing set-digest rule; F-09 added. |
| PR-005 | MEDIUM | IN-SCOPE | A (correctness) | `run_engine._normalize_workflow`; probe `{"workflow": wf}.get("requirements") is None` | A compiled `{"workflow": {...}}` file would refuse at init as "missing requirements". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 unwraps first; E-10 tests both shapes. |
| PR-006 | MEDIUM | UNDER-SCOPE | A (atomicity) / D | `v47z9u` E-04 (reserve + cleanup); `RunLedgerStore.append_held` | Header and `requirement_set` were two independent appends: an interleaved writer or a failed second append leaves a ledger that can never complete. Refusing an empty `requirements` list at init is a behavior change vs `v47z9u` that was not declared. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New E-08 holds both under one `writer_lock`, extends cleanup, declares the behavior change (CHANGELOG via E-07); V-08 added. |
| PR-007 | MEDIUM | UNDER-SCOPE | D/E (regression) | `tests/test_completion.py` (`equals ["as", "cancel", "finalize", "ipd", "record", "start"]`); `tests/test_run_recovery_cli.py` `REFUSAL_LEAVES` prose ("Ten of them") | A new `aw run` leaf trips the pinned completion list, which was not in Scope-Paths; the `REFUSAL_LEAVES` count prose would become false; `REQUIRED_LEAVES` is also bumped by `v47z9u`, so a hard-coded target would be wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 adds the completion row and re-derives the count at HEAD; E-05 updates the prose; Scope-Paths extended. |
| PR-008 | MEDIUM | UNDER-SCOPE | E (coverage) | `grep run_freeze tests/` (only an unrelated match) | No test module covers `run_freeze`; the new freezer's refusals and the unchanged `M-NN` path had no unit home. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-10/V-10 creates `tests/test_run_freeze.py`; Scope-Paths extended. |
| PR-009 | LOW | IN-SCOPE | G (docs anchors) | `docs/cli-output-contract.md` headings (3.1 run vocabulary, 3.2 severity); `CHANGELOG.md` headings | E-07 cited a nonexistent Section 3.3 and an `Unreleased` heading. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 cites Section 3.1 parentheticals and the top pending release; split sanitize/suite into E-09. |
| PR-010 | LOW | IN-SCOPE | G (gate) | plan Approval gate | The gate told the executor to hand-move via `aw ipd move ... --to executed`, and lacked the scope fence, paste-output rule, never-push and conditional finalize ownership. `Concern` was a label, not a problem statement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten; Concern rewritten with the measured symptom. |

`IPD-Z602` (info) remains on E-03, E-04, E-05, E-06: each is one deliverable (one handler; one leaf
registration across parser, dispatcher and declaration; one CLI test sweep; one census sweep) and was not
split further.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which ids may `aw run verify` accept? | Only frozen `requirement_set` ids. | Also `--workflow` ids (REJECTED: inert for completion). | `run_evidence.evaluate_completion`; probe F-08. | yes |
| D-2 | Item digest shape? | Module `_digest(category, normalized_text)`. | `(category, id, text)` as authored (REJECTED: breaks semantic identity). | `run_freeze` docstring and `_digest`. | yes |
| D-3 | Require `R-NN` ids? | No; unique non-empty strings. | Enforce `workflow_schema` `R-NN` (REJECTED: `run_cli` accepts any JSON object as `--workflow`; enforcing here would refuse hand-written workflows the rest of the family accepts). | `workflow_schema._validate_requirements`; `run_cli._load_workflow_arg`. | yes |
| D-4 | Verify on a terminal run? | Refuse, exit 6. | Allow (REJECTED: changes nothing, misleads). | probe F-08; `run_state.TERMINAL_STATES`. | yes |
| D-5 | Refuse an empty `requirements` list at init? | Yes, declared as a behavior change. | Write an empty set (REJECTED: run can never complete). | `evaluate_completion` "no frozen requirements defined". | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
