# Review findings: plan wa64wz

- Subject-Id: wa64wz
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `008c87f60` in an isolated review lane. The plan was committed and unchanged (identical to the lane input), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified by reading and driving the code:
- `release_readiness.gate_full_suite(suite_passed: bool, ...)` has only `full suite green` / `full suite RED` details; `gate_residual_risk` already fails closed on a missing signer (F-02 holds).
- `build_report`'s `suite_passed` is keyword-only with no default (E-02 premise holds).
- `releases.run_list` refusal block via `project_context.nonsurveyable_root_refusal` matches E-03's description.
- `cli.py` `p_releases` subparsers use `--dir` `default=argparse.SUPPRESS`; dispatch at `args.command in ("releases", "release")` falls back to `run_list`.
- `command_surface` releases-family block exists; `check` class with `(0, 1, 2)` precedent (`doctor`, `check`).
- HOW probe: a `CommandResult(command="releases readiness", status="findings", exit_code=1, diagnostics=[Diagnostic(location="residual_risk", rule="readiness.residual_risk", ...)], data=report.to_dict())` renders through `AgentRenderer` and `agent_schema.validate_agent_record` returns `[]`; `JsonRenderer` carries `data.verdict` and no temp path.
- Synthetic GO tree (git init, `.aw/records/plans/pending`, `docs/`, `CHANGELOG.md`, `.aw/system/VERSION`): `build_report(suite_passed=True, residual_risk_signed=True, residual_risk_signer="qa", repo_root=tree)` is GO in 1.0s with subprocess gates live; per-file SHA-1 snapshot (including `.git/`) unchanged.
- `tests/test_releases_cli.py` pins the `releases` subcommand set to exactly `{"list", "show", "new"}` in two tests; `tests/test_agent_surface_conformance.py` universe includes every `read`/`check` leaf with `agent_record_kind="result"`.
- `docs/recovery.md` "Release readiness (decision only)" still cites commit 19313eed / `3rmvik` (F-04 holds).
- Dependency `ttg9uz` is `reviewed`, not executed; the plan's `executed:ttg9uz` edge and E-01 stop condition handle that.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression | `tests/test_releases_cli.py` `test_subcommands_are_exactly_list_show_new` and `ReleasesCompletionTests.test_static_scripts_carry_the_subcommands` assert `{"list", "show", "new"}` | Adding the leaf turns two existing tests red, and the file was not in Scope-Paths, so the executor would either weaken scope or ship red. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `tests/test_releases_cli.py` to Scope and Scope-Paths, new F-06, E-04 updates both sets (and keeps `test_no_releases_check_subcommand`), V-04 demands the green run and diff. |
| PR-002 | MEDIUM | UNDER-SCOPE | G. Honest docs | `cli.py` comment above `p_releases`: "Subcommands are DELIBERATELY list/show/new only"; `p_releases` help/description/epilog | The leaf would make the family comment and help false, and the epilog exit line lacks the NO-GO exit 1. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now updates the comment (keeping the no-`releases check` rule and explaining why readiness is not a second validator), help, description and exit line. |
| PR-003 | MEDIUM | UNDER-SCOPE | F. UX (novice) | `gate_residual_risk` detail `residual-risk sign-off missing`; E-03 human mode prints only `render()` | A bare run is always NO-GO with no indication that two rows are unsupplied attestations rather than defects. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 adds one stderr hint line (stdout stays `render()`) only when those two rows are unsupplied; E-06 arm (b) asserts it. |
| PR-004 | MEDIUM | UNDER-SCOPE | E. Testing | E-03 "Any unexpected exception ... is a cannot-run (exit 2)" stated only for the record; E-06 had no `--dir` position arm and no direct `gate_full_suite(None)` arm | Human-mode cannot-run output was unspecified; the `SUPPRESS` parity rule E-04 relies on and the new gate state were not pinned directly. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 specifies human stderr + exit 2; E-06 adds arms (k) position parity and (l) direct gate; V-06 now lists (a) to (l). |
| PR-005 | LOW | IN-SCOPE | E. Testing (environment) | `tests/conformance_matrix.run_cli` pins `PYTHONPATH` to the repo root; E-06 subprocess arms run with `cwd` = synthetic tree | Without `PYTHONPATH`, `python3 -m agent_workflows` from a temp cwd may not import the lane's package. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 requires `PYTHONPATH` and `stdin=DEVNULL` for subprocess arms. |
| PR-006 | LOW | IN-SCOPE | E. Evidence feasibility | V-02 "`git diff tests/test_release_readiness.py` empty" | `ttg9uz` edits that file; the demand must be relative to the execution base, not the working tree of an earlier commit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 now diffs against `<execution-base>`. |
| PR-007 | LOW | UNDER-SCOPE | D. Anti-regression | `tests/test_agent_surface_conformance.py` `compute_conformance_universe` | The new leaf is auto-collected and run live at the repo root (NO-GO, both subprocess gates). E-05 did not say this, so an executor might misread a NO-GO exit 1 as a failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 states the expected live collection and that it passes on record validity and exit parity. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is `aw releases readiness` with exit 0 GO / 1 NO-GO / 2 cannot-run the right surface (OQ-01)? | Yes; OQ-01 marked resolved, ratified or amended by the maintainer at approval | New top-level `aw readiness`; `aw check release-readiness` (would conflate with `aw check releases` record validation) | `cli.py` `p_releases` (releases owns release records and `show` reports what gates the next release); `result_types.CommandResult.exit_code` comment `0 clean, 1 findings, 2 cannot-run`; `doctor`/`check` declarations `(0, 1, 2)` | yes |
| D-2 | Should the unsupplied-attestation hint go to stdout or stderr? | stderr, one line, only for the two attestation rows | stdout (would change `render()` output scripts parse); no hint (novice confusion) | `renderers.HumanRenderer` / `releases.run_list` write refusals to stderr; E-03 keeps stdout exactly `render()` | yes |
