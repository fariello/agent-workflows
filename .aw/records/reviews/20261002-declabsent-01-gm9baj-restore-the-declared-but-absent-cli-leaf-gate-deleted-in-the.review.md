# Review findings: plan gm9baj

- Subject-Id: gm9baj
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `0475ce787` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review and `--phase review-finalize` was clean after revision.

Re-verified (in-process probes, no production edit):
- `build_matrix(cli._build_parser())`: `declared_absent == ['prompts set', 'upgrade-test']`, `undeclared == []`.
- `get_declared_leaves()` has 162 entries; `COMMAND_INVENTORY` has 163 (plus `aw`).
- `prompts set --help` in-process exits 2 with `invalid choice: 'set' (choose from 'new')`.
- Only surviving references to the deleted test / "asserted elsewhere": `agent_workflows/command_surface.py` (the
  `runs` family comment) and `tests/conformance_matrix.py` (`build_matrix` `declared_absent` branch).
- `EXEMPTION_REGISTRY`: 27 entries (16 `not_runnable`, 7 `sanctioned_raw`, 4 `known_broken`); `upgrade-test` cites
  `lbbo9s`.
- `.github/workflows/tests.yml` `output-conformance` runs only `tests/test_command_surface_declarations.py`.
- `648597285` 2026-09-26 and `19313eed7` 2026-09-24 confirmed. `68sur3` is `graduated`, `Graduated-To: declabsent`.
  `7z3ovv` is `reviewed`, `From-Backlog: um8ikz`, and its E-07 already coordinates the stale allow-set entry with
  this plan.
- DETECTOR FALSE NEGATIVES (PR-001): phantom tokens `set phantom` (`--help` exit 0), `backlog set phantom` (exit 0),
  `runs phantom` (exit 2, `unrecognized arguments: --help`) produce NO `invalid choice`. A walk resolving each token
  through `_SubParsersAction.choices` flags all three, flags exactly `['prompts set']` over the 162 real declarations
  in 0.0009s, and resolves `upgrade-test`, `att`, `spec set`, `sanitize`, `agy exec`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Gate effectiveness | plan E-01 "treat the command as UNREACHABLE when the captured output contains an argparse `invalid choice` error"; probe above | The authored detector misses a phantom declaration nested under any parent that takes positionals or REMAINDER (`set`, `backlog set`, `runs`), so the restored gate would stay green on exactly the kind of drift it exists to catch. The "strictly stronger than the deleted test" claim was false. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now resolves tokens through the built parser's dispatch table (the same walk `discover_parser_leaves` performs) and uses the `--help` capture only for the message. F-03, OQ-02, V-01 (phantom probe required) and V-02 (injection under `set`) updated. |
| PR-002 | MEDIUM | IN-SCOPE | G. Live-artifact criterion | E-04/V-04/Required tests "zero failures", "against F-05's baseline" | The bar was an authoring-time snapshot, and the full suite is not guaranteed green. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Same-session pre-change baseline required, failures compared by name. |
| PR-003 | LOW | IN-SCOPE | G. Accuracy | E-04 "THE RUNNER SETS `graduated`"; `68sur3` front matter | The item is already `graduated` to `declabsent`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now states that, with the history line. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | Approval gate "move this plan ... through the tooled transition" | Finalize ownership (runner vs hand executor) was unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate names runner ownership under `aw oc run`/`aw agy run`, `aw ipd finalize` otherwise, never `git mv`. |
| PR-005 | LOW | IN-SCOPE | E. Evidence feasibility | V-01 "its only imports are `cli`/`command_surface`/the allow-set" | The mechanics E-01 prescribes need stdlib `argparse`/`contextlib`/`io`, so the demand was literally unsatisfiable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reworded to "only project imports", stdlib expected. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which detector should the gate use? | Resolve tokens through `_SubParsersAction.choices` (routing), `--help` capture for the message only | `--help` + `invalid choice` (authored; measured false negatives); `declared_absent` census (P16/`xvp5vx`); subprocess sweep (too slow, would be `slow`-deselected) | Review probe at HEAD `0475ce787`; `command_surface.discover_parser_leaves` already walks the same structure | yes |
| D-2 | Is the scope decision (gate only, registration left to `7z3ovv`) sound? | Yes, keep | Duplicate the registration here | `7z3ovv` is `reviewed`, declares `cli.py`/`status_set.py`/`prompts.py`, and its E-07 coordinates the stale entry with `gm9baj` | yes |
