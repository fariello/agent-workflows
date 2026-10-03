# Review findings: plan 2zvxhx

- Subject-Id: 2zvxhx
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `45529f342` (authoring HEAD `cb61fe319` is an
ancestor); the plan was committed (`eec81e2b6`) and the tree clean, so no snapshot.
`aw ipd lint --phase author` and `--phase review-finalize` both clean; no `IPD-Z602` density
advisory on any E-item after revision. `- Kind: child`.

Re-measured: `check plans --agent` and `--limit 1` both emit 76 of 76 diagnostics; `search plans
Blocks-Release --agent` reports `findings: 0` with or without `--limit 2` while `--json` reports
`hits: 603`; `_PRESERVED_FIELDS` contains `total`/`emitted`/`omitted`; `aw attention --help` has 0
`limit`; `--limit abc` exits 2 (argparse); `--limit 0` on check exits 1 with all findings and
`--limit -1` on search exits 0. Backlog `4izduy` (carrier) and `4uw9gy` (graduated) exist; the five
regression modules named exist.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A/B (crash; anti-greenwashing) | `agent_schema.validate_agent_record`: `outcome: clean` + `complete: false` -> "Greenwash violation: outcome cannot be 'clean' when complete=False"; `cli._run_search` agent branch `status = "clean" if hits`; `render_jsonl_record` asserts validity | The plan never says what `complete`/`outcome` a TRUNCATED record carries. For search, the current status is `clean`; flipping `complete` to false (as V-03 demanded) makes the record invalid and the command crash, while leaving `complete: true` on a partial view is the greenwashing Section 4 forbids. For check, `complete` handling was unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03: truncated search emits `outcome: partial`, `complete: false`, `exit: 0` (validated). E-04: truncated check keeps `findings`/exit 1, sets `complete: false` (validated, survives `--fields`). E-01 (4)(7), V-03, V-04 updated. |
| PR-002 | HIGH | IN-SCOPE | C (mechanism feasibility) | `result_types.CommandResult.to_agent_record` findings fallback `len(self.diagnostics)`; copies no other `data` payload key; `to_dict` serializes `diagnostics` and `data` for `--json`; review probes | No workable mechanism was named under the plan's own fence (no `result_types` edit, `--json` unchanged). Slicing diagnostics before the `CommandResult` makes `findings` the emitted count and truncates `--json`; putting counts or hits in `data` never reaches the compact record; adding `data["findings"]` changes `--json`. | all Low | FIXED | E-04 specifies an agent-path post-processing helper in `cli.py` (full record with fields cleared, slice, add counts, project, validate-emit), demonstrated to validate; E-02/Scope route search hits through it and keep `findings` on an agent-only copy. |
| PR-003 | MEDIUM | IN-SCOPE | E (coverage) | `cli._run_check` `--source-citations` and `--source-anchors` branches each `return get_renderer(ctx).emit(result, ctx)` | E-04 said the bound lands "where that record is built" and so covers every target, but two targets build and emit their own records earlier. | all Low | FIXED | E-04 names all three emit sites and requires the shared helper at each. |
| PR-004 | MEDIUM | UNDER-SCOPE | B (crash site) | probe: `matches[0].text` containing a home path -> "Unsanitized absolute home path in field 'matches[0].text'" | E-03 sanitized pattern and path but not the carried hit `text`, which is a matched record line and can hold a home path. | all Low | FIXED | E-03 requires redacting `text` too. |
| PR-005 | LOW | IN-SCOPE | G | `--limit abc` exits 2; V-02 "where `--json` reported 587" | Non-integer is already refused by argparse; a live count was framed as the bar. | all Low | FIXED | E-05 narrows to 0/negative with measured current behavior; V-02 bar is agent == `--json` at execution HEAD. |
| PR-006 | MEDIUM | IN-SCOPE | G (execution contract) | gate POST-GATE LIFECYCLE; "THREE BOUNDARIES AN EXECUTOR MUST NOT CROSS"; OQ-01..03 `Owner: none` | Unconditional tooled move with no runner/hand ownership split; boundary phrased as a stop rather than a declaration; self-resolved questions with no owner. | all Low | FIXED | Conditional lifecycle added; boundaries restated as declarations with `--scope-reason`; owners `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What outcome should a truncated `aw search --agent` record carry? | `partial`, `complete: false`, exit 0. | Keep `clean` + `complete: true` (greenwash); `clean` + `complete: false` (invalid, crashes); `findings` (exit-parity violation at exit 0). | `docs/cli-output-contract.md` Section 4 "If `complete=False` ... the outcome is `partial` or `skipped`"; validator probes. | yes |
| D-2 | Where should the bound be applied without editing `result_types`? | Agent-path post-processing helper in `cli.py`. | Slice before `CommandResult` (changes `findings` and `--json`); edit `to_agent_record` (plan fence). | Probes recorded in PR-002. | yes |
