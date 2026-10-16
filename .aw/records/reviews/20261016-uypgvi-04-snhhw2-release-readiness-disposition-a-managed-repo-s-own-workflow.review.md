# Review findings: plan snhhw2

- Subject-Id: snhhw2
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `b551549b9`. The plan was committed and byte-identical to the lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean`. The plan is a child, not an orchestrator.

Verified:
- F-01 reproduced at `b551549b9`: fresh managed install, `gate_workflow_disposition` printed `True`, `engine.is_source_checkout(<scratch>)` `False`; after adding a `mycustomwf` copy of the `whatnext` row the gate printed `False {'undispositioned': ["manifest command 'mycustomwf' has no reviewed family assignment (silent omission)"]}`.
- F-02: `migration_inventory._command_disposition` raises on `_COMMAND_FAMILY.get(cmd) is None`; `build_inventory` calls it per command row; `check_completeness` emits "subject '<x>' has NO disposition (silent omission)".
- F-03: `engine.is_source_checkout(Path('.'))` is `True` here; a scratch tree with only `pyproject.toml` (`name = "agent-workflows"`) and `.aw/system/VERSION` also returns `True` (probe), so E-02 case 2 and E-05 fixtures are satisfiable without `source_root`.
- F-05: only `release_readiness.gate_workflow_disposition` calls `build_inventory`/`check_completeness` outside the module (plus `render_agent_report` inside it).
- F-06: `tests/test_release_readiness_producers.py` `26 passed in 0.99s`.
- No spec names the inventory or gate (`git grep` empty, rc=1).
- Dependency `4bw2u5` is `approved` (pending) and adds a not-applicable branch for absent `index.md` to the same function; E-01(e)/E-04 preserve it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric E (RED proof accuracy) | `agent_workflows/migration_inventory.py:599` `_add(_command_disposition(w))` raises before `check_completeness` at `:606`; plan E-02 "cases 1, 5 and 6 fail; 2, 3 and 4 may pass" | The stated RED set was wrong: case 4 necessarily fails on unmodified code (raise preempts the conformance finding) and case 3 fails on `KeyError: 'repo_local'`; "may pass or fail" is not a falsifiable expectation. | all Low | FIXED | E-02 now states the exact expected RED set with reasons (1,3,4,5,6 fail; 2 passes); V-02 demands `-v` per-case output matching it. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric E (masking gate) | `agent_workflows/release_readiness.py:658` `f"{w.command}: missing {field_name} file: {rel}"` in `gate_artifact_manifest` | E-02 case 6 (CLI GO) added "a custom manifest row" without requiring its body file; `artifact_manifest` would then fail and mask the result under the escape clause. | all Low | FIXED | Case 6 now specifies the row and requires the body file to exist. |
| PR-003 | LOW | IN-SCOPE | Rubric A (evidence shape) | `release_readiness.py:427-434` InventoryError branch evidence `{"undispositioned": undone}` | E-04 said `repo_local` is "always present on this path" without naming which of the five return branches; case 2 relies on `.get`. | all Low | FIXED | E-04 names the two post-inventory results that carry it and keeps the other branches unchanged. |
| PR-004 | LOW | UNDER-SCOPE | Rubric F / security lens (silent pass) | `migration_inventory.py:206` `_COMMAND_FAMILY` is the running CLI's catalog; managed `index.md` comes from the installed tree | In repo-local mode, a toolkit row unknown to an older `aw` (version skew) is indistinguishable from a repo-authored row and would pass as repo-local. Not stated anywhere. | all Low | FIXED | Recorded as accepted risk in OQ-02 and required in the E-06 `docs/recovery.md` paragraph (names surfaced, review the list). |
| PR-005 | LOW | IN-SCOPE | Evidence accuracy / docs | `agent_workflows/layout_inventory.py:48` `class InventoryError(Exception)`; `migration_inventory.py:580` "Raises :class:`InventoryError` only for a programmer error" | F-05's grep list omitted `layout_inventory.py` (unrelated same-named class); E-03 did not update the `build_inventory` docstring that the new mode contradicts. | all Low | FIXED | F-05 corrected and re-verified; E-03 requires the docstring update and keeps `render_agent_report` on the default. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should repo-local mode try to distinguish a repo-authored row from an uncatalogued toolkit row (version skew)? | No; name them all as repo-local and document that the list should be reviewed. | Compare against an installed toolkit manifest snapshot (REJECTED: new contract and state with no consumer; over-scope for this bug). | Plan OQ-02 (no fabricated dispositions, names surfaced); `migration_inventory._COMMAND_FAMILY` is the only catalog. | yes |
| D-2 | Is `engine.is_source_checkout` satisfiable by a tmp_path fixture without git? | Yes; no fixture change needed beyond `pyproject.toml` + `.aw/system/VERSION`. | Pass `role="source-checkout"` (REJECTED: not exposed by the gate). | Probe in this lane printed `True`; `engine.is_source_checkout` skips the git check when `source_root` is None. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
