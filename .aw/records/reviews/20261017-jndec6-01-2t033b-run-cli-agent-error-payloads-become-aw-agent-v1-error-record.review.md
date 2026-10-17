# Review findings: plan 2t033b

- Subject-Id: 2t033b
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the lane input and committed unchanged (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean` (one `info` `IPD-Z602`). Child plan; Set `jndec6`; dependents `2jzld4` (Set `nyvyb4`) and `u1ujw9` (Set `p7bvku`) declare `executed:2t033b` and reuse this plan's helper.

Verified:
- F-1 reproduced: `runs status totalgibberish --agent --fields cmd` and `run cancel ... --agent --fields cmd` print the full bare dict, exit 2.
- F-2: `run_cli._emit_error` docstring "DELIBERATELY NOT AN `aw.agent/v1` RECORD (F-16)"; exact key-set assertions in `tests/test_run_cli_error_payload_keys.py` and `tests/test_run_recovery_cli.py::test_an_unknown_target_keeps_the_bare_machine_shape`.
- F-3: `run_cli` imports `agent_schema` (top-level import) and uses it in `_run_init` and `_emit_projection`; `command_surface.py` `runs next` / `runs resume` comments still say "zero times".
- `agent_schema.validate_agent_record` caps `exit` at (0, 1, 2) and requires `kind: "error"` to carry exit 2 and `error`/`cannot-run`; `_PRESERVED_FIELDS` includes `next` but not `error`/`ok`/`exit_code`; `render_guarded_jsonl_record` is strict under pytest.
- Parser dests: `run cancel` sets `run_command`, `runs status` sets `runs_command`, neither sets the other attribute (measured with `cli._build_parser().parse_args`).
- `docs/cli-output-contract.md` Section 11.4 requires the agent-mode cannot-run record shape with a `next` recovery command; Section 3 bullet and Section 3.1 (`run init` sentence and opening paragraph) describe the bare shape.
- Two inline "failed to read ledger" sites bake `error: ` into the machine value (measured with an unreadable file; `_build_engine` emits the same condition unprefixed).
- `_emit_error` messages can embed absolute home paths (measured: `run init --workflow <home-style path> --agent`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Correctness (unstated contract change) | `agent_workflows/run_cli.py:628` and `:737` (`err_msg = f"error: failed to read ledger: {exc}"`); `run_cli._build_engine` (`f"failed to read ledger: {exc}"`); `run_cli._emit_ledger_not_found` docstring F-17 | E-02 routes the two inline payloads through `_emit_error`, which also changes the `--json` `error` value (prefix dropped), while the Scope said `--json` is unchanged and V-01 called `--json` "unchanged". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope and E-02 now state the deliberate `--json` prefix normalization and cite the F-17 convention; no test pins the prefixed value (searched). Deferred note updated. |
| PR-002 | MEDIUM | UNDER-SCOPE | Testing (E-02 untested) | V-02 (diff and grep only); `tests/` has no hit for `failed to read ledger` | The routed read-failure path had no behavioral test; V-02 was a diff/grep, which proves structure, not outcome. | all Low | FIXED | New E-07 (b) drives `runs show` / `runs evidence` with `RunLedgerStore.read_records` patched to raise `OSError` and asserts the record and the unprefixed value in both renderers; V-02 points at it. |
| PR-003 | MEDIUM | UNDER-SCOPE | Security (home-path leak, strict-render crash) | measured `run init --workflow <home-style path> --agent` error embeds the absolute path; `agent_schema.render_guarded_jsonl_record` strict under pytest | E-01 named home-path redaction but no test exercised it, and ANSI was not stripped although the validator rejects it; under pytest an unredacted record raises instead of printing. Redaction of nested `extra` lists (`suggested_commands`) was unspecified. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | E-01 now redacts and ANSI-strips recursively; E-07 (c) asserts a home-style path is absent from the record. |
| PR-004 | MEDIUM | IN-SCOPE | Architecture (duplication across dependent plans) | pending `2jzld4` E-01 ("reuse... add it exactly as `2t033b` E-01 specifies"); pending `u1ujw9` E-01 ("reuse its redact / `--fields` / `render_guarded_jsonl_record` sequence rather than copying it") | Two dependent plans reuse a sequence this plan wrote inline inside `_emit_error`, so reuse meant copying it. | all Low | FIXED | E-01 factors the sequence into one named `_emit_agent_record(args, rec)` helper; conventions note records the dependents. Envelope keys now override `extra` keys. |
| PR-005 | LOW | IN-SCOPE | Right-sizing | old E-04 (a)-(d) | E-04 bundled updating three existing tests with three new independent test surfaces (`--fields`, non-2 boundary, docstring). | all Low | FIXED | Split: E-04 updates the existing tests (renamed, since they no longer assert "exactly the three keys"); new E-07 adds the new tests; V-07 added with a demanded failing run against the pre-change code for the sensitive tests. |
| PR-006 | LOW | IN-SCOPE | Process (validation commands) | Required tests and V-05/V-06 used `-o addopts="" -q`; regression set omitted `test_run_evidence_completion.py` and `test_live_conformance_sweep.py`, which read `--agent` output | `-q` with `-o addopts=""` is harmless but the regression list was narrower than the Scope check's own under-scope list; `test_exit_contract_conformance.py` was in Required tests but in no V-item. | all Low | FIXED | Regression and conformance commands aligned across Required tests, V-05 and V-06; `-q` removed. |
| PR-007 | LOW | UNDER-SCOPE | Executability (lifecycle, doc sweep) | Gate lacked the POST-GATE LIFECYCLE clause present in sibling `tgfxin`; `docs/cli-output-contract.md` Section 3.1 opening paragraph "These commands emit bare JSON dictionaries ... rather than `aw.agent/v1` records" | The gate did not state who moves the plan to `executed/`; E-06 left one contradicting doc sentence. | all Low | FIXED | Gate gains the conditional runner/`aw ipd finalize` clause and notes the two dependents; E-06 also qualifies the Section 3.1 opening paragraph. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Accept that E-02 changes the `--json` `error` value at two sites? | Yes, and declare it. | Keep the `error: ` prefix by building the payload inline (REJECTED: preserves a split the repo already resolved against). | `run_cli._emit_ledger_not_found` docstring F-17; `_build_engine` already unprefixed; no test pins the value. | yes |
| D-2 | Where does the redact / `--fields` / render sequence live? | One helper `_emit_agent_record`. | Inline in `_emit_error` (REJECTED: two dependent plans would copy it). | `2jzld4` E-01; `u1ujw9` E-01. | yes |
| D-3 | How to test the unexpected-read-failure path portably? | Patch `RunLedgerStore.read_records` to raise `OSError`. | chmod-000 file (REJECTED: still readable as root, so the test would be environment-dependent). | measured: chmod-000 reproduces only as non-root. | yes |
| D-4 | Should `extra` be able to override envelope keys? | No; envelope and legacy keys are applied after `extra`. | Plan's original `**extra` last (REJECTED: an `extra` key named `exit` or `kind` would silently break the record). | `agent_schema.validate_agent_record`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
