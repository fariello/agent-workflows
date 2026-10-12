# Review findings: plan t76qdk

- Subject-Id: t76qdk
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `d695ef8fd` in an isolated review lane. The plan was committed and unchanged (`e05cead32`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified:
- `run_viewer.run_viewer_cli` empty-state branch (`if not summaries and not issues_only:` / `if is_agent or is_json:` / `payload: dict[str, Any] = {"runs": []}`) is as F-01 describes. Live: `runs list --agent`, `runs --agent`, `runs --agent --status zzz` on an empty tempdir each print `{"runs": []}` with rc 0.
- `cli.main` routes `if runs_cmd and runs_cmd != "list":` elsewhere, so both spellings reach `run_viewer_cli` (F-02).
- `command_surface` `command="runs list"` declares `agent_record_kind="summary"` (F-03); `tests/test_agent_surface_conformance.py` filters `agent_record_kind == "result"` (F-06).
- `agent_schema.validate_agent_record` `kind == "summary"` arm requires `total/emitted/omitted/complete`; a probe of the E-01 field set (with `filters`, `excluded_runs`, `next: "aw runs"`) returned `[]`.
- `agent_schema.render_jsonl_record` calls `assert_valid_agent_record` and appends `\n`.
- `tests/test_run_viewer.py::test_total_exclusion_distinguishable_from_empty_repo_across_all_surfaces` holds the two pinning assertions named in E-02 (F-05).
- `docs/cli-output-contract.md` Section 3.1 paragraph "Commands in the run-execution family" and Section 11.1 "a structured `result` (or `summary`) record" exist as cited.
- Backlog `4d3ynu` exists, open, `Blocks-Release: next`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A. Correctness / B. Privacy | `agent_schema.redact_home_paths` ("Non-string inputs are returned unchanged"); plan E-01 `filters` clause | E-01 said to pass `filters` values, including the `targets` list, through `redact_home_paths`. That function returns a list unchanged, so a home-path target would leak into the record. The plan also left the representation of `last` (`--latest` versus `--last N`) and the boolean flags undefined. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now redacts `targets` element by element (as `_unresolvable_target_refusal` already does), records `last` as the normalized `last_n` int, and includes `failed`/`active` only when True. |
| PR-002 | MEDIUM | IN-SCOPE | Evidence / Honest docs | `run_viewer.repair_run` `return 1, (`; plan F-04 and E-04 | F-04 and E-04 claimed the viewer "only ever returns exit `0` or `2`". The `aw runs repair` route returns `repair_run` codes, which include `1`. The doc sentence would therefore have been false. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04, E-04 and its expected outcome now say read paths return 0 or 2 and `repair` may also return 1, which is still inside the three-state vocabulary. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing (red-proof procedure) | plan Required tests, the `git show HEAD:... >` step | The red-proof step overwrote the fixed file with HEAD and then said "restore the fix" with no saved copy, because the fix is uncommitted at that point. Following it literally would lose the E-01 edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The fixed file is now copied to `/tmp/opencode` first and restored afterwards, and the diff is confirmed against V-01. |
| PR-004 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | plan V-05 "full suite bare ... summary line" | The full-suite evidence had no baseline comparison. A concurrent unrelated failure would block a correct execution, or would be waved through unexamined. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each failing node id must now be shown failing at the pre-change base commit and lie outside the touched files. A failure that passes at the base makes V-05 `failed`. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | plan `## Approval and execution gate` | The gate lacked the OQ status line, the scope-fence declaration, the MUST-paste honesty rule, and the conditional runner/executor ownership of begin/finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All four were added. |
| PR-006 | LOW | IN-SCOPE | Open-question hygiene | OQ-01..OQ-03 `- Owner: none` | The resolved questions were answered by the author but recorded the owner as `none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep `--json` empty payload bare (OQ-02)? | Yes, keep bare | Envelope `--json` empty case (makes shape depend on result count, breaks `data["runs"]` readers in `tests/test_run_viewer.py` and `tests/test_runs_subdir_root.py`) | contract Section 1 precedence; non-empty `--json` is bare `{"runs": [...]}` | yes |
| D-2 | Is stating the viewer's exit range a sufficient answer to the Section 3.1 reconciliation (F-04)? | Yes, with `repair`'s exit 1 named | Rewrite the whole family paragraph (other verbs genuinely use the wide tables; out of scope) | `run_viewer.EXIT_UNRESOLVABLE_TARGET`, `run_viewer.repair_run` returns | yes |
| D-3 | `summary` vs `result` kind (OQ-01)? | `summary` | `result` plus a declaration change (pulls the unfixed non-empty path into the result conformance sweep) | `command_surface` `runs list` `agent_record_kind="summary"`; Section 11.1 "(or `summary`)" | yes |
