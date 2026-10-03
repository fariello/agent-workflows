# Review: Emit a conformant agent record from the bare aw upgrade-test group

- Subject-Id: 7pnneh
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The plan was committed and unchanged, so I skipped the pre-review snapshot. `aw ipd lint --phase author` was clean before my edits and `--phase review-finalize` was clean after them. Review is plans-only, so I did not re-run the plan's code prototype.

Re-verified at lane HEAD `f035f874c`:

- `upgrade-test --agent` gives rc 2 with 2060 bytes / 39 lines of help on stdout.
- `get_declaration("upgrade-test")` is non-None.
- `len(EXEMPTION_REGISTRY)` is 27: 16 not_runnable, 7 sanctioned_raw, 4 known_broken.
- `compute_conformance_universe()` has 42 members and does not contain `upgrade-test`.
- `build_matrix` gives `declared_absent ['prompts set', 'upgrade-test']`, `undeclared []`, 1193 rows.
- `human_recipe == "help"` occurs 0 times across 163 declarations.
- `aw backlog --agent` emits the cannot-run record.
- `_show_family_help` signature and its `is_agent` branch match the plan's description.
- All five carrier backlog items exist in `open/`.
- `git tag --contains 648597285` returns nothing.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Evidence accuracy | agent_workflows/cli.py `_dispatch` (`if args.command == "upgrade-test":`; `context = select_output(args)`; `term = Term(color=context.color)`) | The plan put the handler arm and the `term`/`context` bindings in `cli.main`. They are in `cli._dispatch`, which `main` calls. An executor looking in `main` would not find them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Every `cli.main` site reference now points to `cli._dispatch`. |
| PR-002 | MEDIUM | UNDER-SCOPE | Anti-regression (D) | agent_workflows/cli.py `_show_family_help` branches on `is_agent` only; measured `aw backlog --json` rc 2 printing `usage:` | F-01 records that `--json` behaves the same as `--agent` today, but the plan never says what `--json` should do afterwards. The shared helper keeps printing help under `--json`. An executor could read that as an unfinished fix, or add a one-off special case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now says `--json` keeps parity with the 18 sibling roots (help at exit 2) and must not be special-cased. V-01 requires pasting the `--json` result beside `aw backlog --json`. |
| PR-003 | MEDIUM | IN-SCOPE | Live-artifact criteria (G) | plan E-03/V-03 "26 entries", "same 42"; pending `vfv2db` and `gm9baj` declare `tests/conformance_matrix.py` | The bars use absolute counts of a file that two sibling plans also edit. If either sibling lands first, a correct execution fails V-03. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bars are now relative to the pre-edit measurement: the registry shrinks by exactly one and the universe list is unchanged. The authoring values stay as context. |
| PR-004 | LOW | IN-SCOPE | Test design (E) | tests/test_aw_upgrade_test.py `CliTests.test_help_runs` drives `[sys.executable, str(TOOL), "--help"]` | E-04 says `test_help_runs` drives `-m agent_workflows`. It actually drives `tools/aw_upgrade_test.py`. The plan also gave no `cwd`, so `-m agent_workflows` could resolve a package other than the checkout's. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected the citation to `uat.default_aw_cmd()` and pinned `cwd=str(REPO_ROOT)`. |
| PR-005 | LOW | IN-SCOPE | Execution contract (G) | plan OQ-01..03 `- Owner: none`; gate "move this plan to executed/" | The questions I resolved recorded no owner. The gate did not say who runs the lifecycle transition, runner or executor. The CHANGELOG decision was left open to the reviewer. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owner is now `plan author`. The gate now names conditional finalize ownership. The CHANGELOG decision is confirmed: `git tag --contains 648597285` returns nothing, so the command is unreleased. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should `--json` on the bare group also emit a record? | No; keep parity with the 18 roots | Special-case `upgrade-test`; change `_show_family_help` (out of scope per plan) | measured `aw backlog --json` rc 2 help; `cli._show_family_help` `is_agent` branch | yes |
| D-2 | Should the plan add a CHANGELOG entry? | No | Add a `Fixed` line | `git tag --contains 648597285` empty; CHANGELOG head `2.0.0 (pending)` | yes |
| D-3 | Should the plan's choice to delete the declaration rather than correct it (OQ-01) stand? | Keep it | Correct the fields with a new `family`/`help` vocabulary | `command_surface.py` runs-family comment ("a family ROOT is never a leaf"); 0 of 163 declarations use `help` | yes |
