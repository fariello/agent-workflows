# Review findings: plan 0z7ds3

- Subject-Id: 0z7ds3
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `f52907adc` in an isolated review lane; plan committed and unchanged, no snapshot needed.
`aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize` clean after.

Re-verified:
- Census via `command_surface.discover_parser_leaves(cli._build_parser())`: 157 leaves, 67 with a required argument, 0 non-`_AwArgumentParser` parsers.
- All 67 driven bare as `python3 -m agent_workflows <leaf> --agent`: every one `rc=2`, 0 stdout bytes, stderr `the following arguments are required:`; about 66 s serial total (roughly 1 s per subprocess).
- The three handler leaves (`backlog new`, `specs new`, `prompts new`) refuse `rc=2`, 0 stdout bytes, with the quoted stderr text, both in the repo and in a non-repo temp dir.
- `cli._show_family_help` is the `cannot-run` precedent; `renderers.get_renderer` returns `JsonRenderer` for `is_json`.
- `MUTATION_UNIVERSE` is 24; all seven `91pjax` leaves are declared `mutation`/`result`, so removing the exemptions adds 7 (31).
- `tests/test_backlog_descriptive_safety.py` `test_empty_summary_refusal_unchanged` and `test_agent_mode_refusal_shape` are as the plan states.
- PROBE (per-parser capture, the authored E-03 mechanism), monkeypatching `parse_known_args` to record its `args` and `error` to print it: on Python 3.14, `--agent ipd scaffold` -> leaf saw `[]`; `--agent ipd set` -> `[]`; on Python 3.12, `ipd set --agent` -> `[]` and `config set --agent` -> `[]` (stdlib intermixed parse re-enters `parse_known_args` with positionals stripped).
- PROBE (dispatch-level capture prototype): on 3.14 and 3.12, `ipd set --agent`, `--agent ipd set`, `config set --agent`, `--agent ipd scaffold`, `nosuch --agent` each exit 2 with one record, `validate_agent_record` -> `[]`; `ipd scaffold -- --agent` and `ipd scaffold --agent --json` write nothing to stdout.
- In-process `cli.main` bare-leaf refusal costs about 0.23 s per call.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / OQ-01 HOW | plan E-03 "records the raw argv it was asked to parse (in `parse_known_args` ...)"; `cli._AwArgumentParser.parse_known_args`; probe above | A subparser only sees the argv suffix after its parent; `aw --agent ipd scaffold` is invisible to the leaf, and below Python 3.13 the intermixed re-entry records `[]` for `+`-positional leaves even with a trailing `--agent`. The authored mechanism would silently miss real invocations and break on the CI floor. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and OQ-01 now capture the full invocation argv once in `cli._dispatch` in a `ContextVar` (reset in `finally`) and read it in `error`; demonstrated on 3.14 and 3.12. E-05 adds case (8), the global-flag-before-leaf spelling; V-03 adds those runs. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing cost | E-05 (1)/(2) "runs `python3 -m agent_workflows <leaf> --agent`"; 67 leaves measured at about 66 s serial | Subprocess-parametrizing 134 cases would add minutes to the default fast suite, which `pyproject.toml` describes as the ~24 s subset. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now drives `cli.main` in-process (the `_capture_cli_separate` pattern), keeping subprocesses only for (5), (6) and one representative. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. Compatibility | `pyproject.toml` `requires-python = ">=3.9"`; `.github/workflows/tests.yml` OS matrix | The plan did not say the sweep must hold below Python 3.13, where argparse's intermixed parse behaves differently (the PR-001 failure mode). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 states the sweep must not depend on 3.13+ argparse behavior; V-05 names the interpreter used and also runs the sweep on a lower interpreter when one is available. |
| PR-004 | LOW | UNDER-SCOPE | E. Coverage | E-05 case list; `aw ipd nosuch --agent` measured (`argument ipd_command: invalid choice`) | `invalid choice` on a family was named in Scope but not tested, and the expected `cmd` for that case was unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 case (9): `aw ipd nosuch --agent` -> `cmd == "ipd"`, `next == "aw ipd --help"`. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | gate "Backlog item `91pjax` is set to `graduated` by the runner on verification"; item lives in `.aw/records/backlog/graduated/` | Wrong lifecycle claim: the item is already `graduated`, and it closes `done` via the handoff once the plan executes. The `Blocks-Release` inheritance was also not stated in the gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate corrected; it now states the inherited gate and the done-via-handoff close. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where to capture the argv the mode is sniffed from? | Once, in `cli._dispatch`, in a `ContextVar` reset in `finally` | Per parser in `parse_known_args` (authored; fails, see probe); a module global (stale across in-process calls); a two-pass parse (rejected in OQ-01) | Review probe on 3.14 and 3.12; `_consume_early_flags` precedent | yes |
| D-2 | Subprocess or in-process for the parametrized sweep? | In-process `cli.main`, a few subprocess cases kept | All subprocess (minutes added to the fast suite); mark the file `slow` (would hide the sweep from the default run) | Measured about 1 s per subprocess vs 0.23 s in-process; `pyproject.toml` fast-suite note | yes |
| D-3 | Expected `cmd` for an `invalid choice` on a family parser? | The family path from `self.prog` (`ipd`), `next` `aw ipd --help` | `aw` | E-03's `self.prog` rule applied as written; matches the stderr `Next` line | yes |
