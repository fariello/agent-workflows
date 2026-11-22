# Review findings: ipd rznd0q

- Subject-Id: rznd0q
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261122T000435Z-1280895`). The target plan `.aw/records/plans/pending/20261121-3z57rk-01-rznd0q-preserve-dry-run-and-non-interactive-invariants-in-legacy-aw.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` findings). Inspection of backlog item `3z57rk`, sibling plan `gftvh6`, `agent_workflows/install_wizard.py`, `agent_workflows/term.py`, `agent_workflows/cli.py`, `agent_workflows/engine.py`, and `tests/test_installer.py` surfaced two `HIGH`, one `MEDIUM`, and one `LOW` finding (`PR-001..PR-004`), all fixed in place. Pass 2 re-checked `Scope`, `Goal`, `E-01..E-05`, `Step 0`, `Findings`, `Proposed changes`, both Mermaid diagrams, `Scope check`, `Required tests / validation`, `V-01..V-05`, and `Approval and execution gate` for full internal consistency.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Scope`, `E-02`, `E-03`, `E-05`, `Step 0`, `Findings`, `Proposed changes`, `Required tests / validation`, `V-02`, `V-03` | Used `bool(getattr(args, "dry_run", False))` (truthy on unset `MagicMock` attributes) and updated only three assertions attributed to `test_migration_paths_thread_requested_disposition` | Switched all `cli.py` dry-run checks to `getattr(args, "dry_run", False) is True`, named all four `execute_migration.assert_called_once_with(..., dry_run=False)` assertions across `SplitBrainLayoutGuardTests` and `InstallLeftoverDispositionThreadingTests`, and added `guard_clean_shapes` to the targeted `tests/test_installer.py` `-k` filter | PR-001, `steps/r1-references.md`, `steps/r4-engineering.md` |
| `Scope`, `E-02` item 6, `E-04` item 4, `Findings`, `Proposed changes` + diagrams, `Scope check`, `V-02` | Left `_diagnostics_ok` unguarded under `dry_run`, allowing `engine.run_git_diagnostics` to run `git fetch`, prompt on dirty/behind interactive TTYs, or run `git pull --rebase` during `--dry-run` | Added `getattr(args, "dry_run", False) is True` short-circuit in `_diagnostics_ok`, synchronized diagrams, and added a tracked-dirty interactive-TTY `--dry-run --keep-legacy` test in `E-04` item 4 | PR-002, `steps/r3-security.md`, `steps/r4-engineering.md` |
| `E-04` items 3 and 5 | Did not clear `AW_NONINTERACTIVE`/`CI` in interactive-TTY tests and omitted direct `interactive=False`/`interactive=True` assertions for `gftvh6` compatibility | Required clearing `AW_NONINTERACTIVE`/`CI` in interactive-TTY test cases and added explicit `interactive=False` and `interactive=True` assertions in `E-04` item 5 | PR-003, `steps/r4-engineering.md` |
| `Approval and execution gate` (`COMMIT`) | Omitted shared-checkout safety clause | Added explicit shared-checkout clause forbidding altering, reverting, staging, or committing unrelated concurrent changes | PR-004, `steps/s7-finalize.md` |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes; updates `agent_workflows/install_wizard.py::collect_policy_interactive`'s signature (adding keyword-only `interactive` and `dry_run` parameters coordinated with pending sibling plan `gftvh6`) and enforces `aw install --dry-run` and `--no-interactive` contracts across single-repo and batch install paths.
2. Yes; `install_wizard.py` enforces D92 leak-containment git policies and `cli.py` install helpers gate working-tree, git-index, `.aw/.gitignore`, and user-config mutations.
3. No; focused bug fix (`5` E-items across `4` task groups in `2` production files and `2` test files).
4. Yes; `- Scope-Paths:` explicitly names `agent_workflows/cli.py`, `agent_workflows/install_wizard.py`, `tests/test_installer.py`, and `tests/test_install_dry_run_noninteractive.py`.
5. Yes; defects in dry-run or interactivity gating can execute live layout migrations (`git mv` + leftover removal) or `git pull --rebase` during `--dry-run`, block unattended automation on `input()`, or break split-brain/placement-switch safety guards.

AW-TIER: standard

### Step R1

- Checked: backlog `.aw/records/backlog/graduated/20261121-3z57rk-01-3z57rk-install-dry-run-mutates-legacy-layout.backlog.md`, pending sibling plan `.aw/records/plans/pending/20261121-dogfood-bugs-01-gftvh6-honor-no-interactive-in-aw-install-policy-update-checkpoint.ipd.md`, `agent_workflows/install_wizard.py` (`resolve_existing_policy`, `resolve_policy_noninteractive`, `collect_policy_interactive`, `persist_project_policy`), `agent_workflows/term.py` (`set_interactive_override`, `get_interactive_override`, `is_forced_noninteractive`, `is_interactive`), `agent_workflows/cli.py` (`_confirm`, `_ask_policy`, `_confirm_install`, `_confirm_relocation`, `_exclude_guard`, `_report_leftover_removal`, `_install_leftover_disposition`, `_split_brain_guard`, `_diagnostics_ok`, `_install_one`, `_handle_legacy_migration`, `_run_install`, `_install_all`, `_configure_completion`), `agent_workflows/engine.py` (`is_interactive_session`, `run_git_diagnostics`, `prompt_and_run_commit`), and `tests/test_installer.py` (`SplitBrainLayoutGuardTests`, `InstallLeftoverDispositionThreadingTests`).
- Found that `tests/test_installer.py` has four (not three) exact-kwargs `execute_migration.assert_called_once_with(...)` call sites across three methods, including `SplitBrainLayoutGuardTests.test_guard_clean_shapes_description_and_migration` which passes an unset `mock.MagicMock()` `args` namespace (`PR-001`), and that `_diagnostics_ok` delegates to `engine.run_git_diagnostics` without guarding `dry_run` (`PR-002`). All other code references resolved accurately.

### Step R2

- Checked: `E-*`/`V-*` bijection (`5/5`: `E-01..E-05` <-> `V-01..V-05`, `- Highest E allocated: 05`), dependency chain (`E-01 -> E-02 -> E-03/E-04 -> E-05`), `- Scope-Paths:` completeness (`4` files), `- Item-Dependencies: none` (verified `E-01` signature compatibility with unapproved sibling plan `gftvh6` in either order), runtime reachability of `V-01..V-05` (all demand git diffs, pytest/CLI outputs, or `rg` checks reachable by construction), and `Approval and execution gate` (resolved OQ precondition, non-stopping scope fence with `--scope-reason`/`--scope-ack`, hard-MUST honesty rule, path-scoped `aw commit rznd0q`, conditional runner/executor `aw ipd finalize rznd0q` ownership).
- Added shared-checkout safety wording to `COMMIT` (`PR-004`).

### Step R3

- Checked: security and privacy lens (`steps/r3-security.md` full form). Closing the `--dry-run` mutation paths in `_handle_legacy_migration`, `_split_brain_guard`, `_diagnostics_ok`, `_install_one`, `_ask_policy`, and `_configure_completion` prevents unintended working-tree, git-index, `.git/FETCH_HEAD`, user-config, and shell-completion writes, while enforcing `term.py` Option A precedence (`--no-interactive` > `AW_NONINTERACTIVE`/`CI` > `--interactive` > stream detection) preserves fail-closed `IncompletePolicyError` on unattended first installs and blocks `io.StringIO` from overriding forced non-interactive mode.

### Step R4

- Checked: correctness and data integrity (`PR-001` avoids truthy `MagicMock` `dry_run` regression in `SplitBrainLayoutGuardTests` via `getattr(args, "dry_run", False) is True` and updates all four exact-kwargs mock assertions; `PR-002` prevents `git fetch`, interactive prompts, and `git pull --rebase` via `_diagnostics_ok` dry-run short-circuit), anti-regression and testing (`PR-003` clears `AW_NONINTERACTIVE`/`CI` in interactive-TTY tests and tests `interactive=False`/`interactive=True` for `gftvh6` parity; verified `term.is_interactive()` already accommodates `_pytest.*` and `io.StringIO` stdout capture), right-sizing (`5` E-items, `4` Scope-Paths, cohesive single bug fix with one concern per E-item), and `## Spec / documentation sync` (`N/A` verified truthful).

### Step S5

- Checked: `## Open questions` (`OQ-01` and `OQ-02`, both `Status: resolved`, `Blocking: no`, `Owner: plan author`, grounded in verified code and direct reproduction `F-05`) and all `Deferred / out of scope` entries (all carry valid `Carrier-Declined` rationales). Every finding (`PR-001..PR-004`) has `Overall:Low` Remediation Risk and is settled from repository code. Recorded `D-1` (`getattr(args, "dry_run", False) is True` + four mock assertions) and `D-2` (`_diagnostics_ok` dry-run short-circuit inside `cli.py`) in `### Decisions`, both `Reversible: yes`. Zero blocking or human-owned questions remain.

### Pass 2

- Re-checked the complete revised plan across `Scope`, `Goal`, `E-01..E-05`, `Step 0`, `Findings`, `Proposed changes`, both Mermaid diagrams, `Scope check`, `Required tests / validation`, `Spec / documentation sync`, `Open questions`, `V-01..V-05`, and `Approval and execution gate`.
- Verified `5/5` E/V bijection, `- Highest E allocated: 05`, zero unresolved questions, and clean `aw ipd lint --phase review-finalize --agent` disposition with `0` diagnostics.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R1 / R4 / `MagicMock` `dry_run` hazard and missing 4th mock assertion | .aw/records/plans/pending/20261121-3z57rk-01-rznd0q-preserve-dry-run-and-non-interactive-invariants-in-legacy-aw.ipd.md:55-62,69-71,102; agent_workflows/cli.py::_split_brain_guard:8779; tests/test_installer.py::SplitBrainLayoutGuardTests.test_guard_clean_shapes_description_and_migration:4466-4485; tests/test_installer.py::InstallLeftoverDispositionThreadingTests:4635,4653,4752 | `E-02` used `bool(getattr(args, "dry_run", False))`, which evaluates to `True` on unset `mock.MagicMock()` attributes in `SplitBrainLayoutGuardTests.test_guard_clean_shapes_description_and_migration` (breaking its `"proceed"` return and mock call). `E-03` also missed that 4th exact-kwargs `execute_migration.assert_called_once_with(...)` assertion and mislocated the 3rd (line 4752 in `test_legacy_migration_fail_soft_on_preflight_gate_error`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Switched `E-02` to `getattr(args, "dry_run", False) is True` (matching `cli.py:8779`), updated `E-03`, `Scope`, `Step 0`, `Findings`, `Proposed changes`, `V-02`, and `V-03` to cover all four assertions across three test methods, and added `guard_clean_shapes` to `E-05` / `Required tests / validation` (`D-1`). Recommendation strength: very strong. |
| PR-002 | HIGH | UNDER-SCOPE | R3 / R4 / Dry-run git fetch, prompt, and rebase leak in `_diagnostics_ok` | .aw/records/plans/pending/20261121-3z57rk-01-rznd0q-preserve-dry-run-and-non-interactive-invariants-in-legacy-aw.ipd.md:58-63,79-80; agent_workflows/cli.py::_diagnostics_ok:8895-8924,_run_install:9437,_install_all:9688; agent_workflows/engine.py::is_interactive_session:2314-2320,run_git_diagnostics:4411-4510 | `_run_install` (on `kept_legacy=True`) and `_install_all` call `_diagnostics_ok(repo_root, args)` -> `engine.run_git_diagnostics(plan)`, which runs `git fetch --quiet` and (because neither `is_interactive_session` nor `run_git_diagnostics` checks `plan.dry_run`) blocks on `input()` or executes `git pull --rebase` on dirty/behind interactive `--dry-run`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a `getattr(args, "dry_run", False) is True` early return in `cli.py::_diagnostics_ok` (`E-02` item 6), synchronized `Scope`, `Findings`, `Proposed changes` + diagrams, `Scope check`, and `V-02`, and added a tracked-dirty interactive-TTY `--dry-run --keep-legacy` test in `E-04` item 4 (`D-2`). Recommendation strength: very strong. |
| PR-003 | MEDIUM | IN-SCOPE | R2 / R4 / Interactive-TTY CI isolation and `gftvh6` parity tests | .aw/records/plans/pending/20261121-3z57rk-01-rznd0q-preserve-dry-run-and-non-interactive-invariants-in-legacy-aw.ipd.md:38-47,79-81; agent_workflows/term.py::is_interactive:1972-2049 | `E-04` item 3 did not clear `AW_NONINTERACTIVE`/`CI` from `os.environ` (making interactive-TTY dry-run checks vacuous in CI), and `E-04` item 5 omitted direct `interactive=False` and `interactive=True` assertions for `E-01`'s `gftvh6` compatibility requirement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required clearing `AW_NONINTERACTIVE` and `CI` in interactive-TTY test cases in `E-04` items 3, 4, and 5, and added explicit `interactive=False` and `interactive=True` matrix checks to `E-04` item 5. Recommendation strength: strong. |
| PR-004 | LOW | IN-SCOPE | Proofreading / S7 / Shared-checkout gate wording | .aw/records/plans/pending/20261121-3z57rk-01-rznd0q-preserve-dry-run-and-non-interactive-invariants-in-legacy-aw.ipd.md:270 | `Approval and execution gate` (`COMMIT`) omitted the shared-checkout safety clause forbidding touching unrelated concurrent changes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the shared-checkout safety clause to `COMMIT` in `Approval and execution gate`. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `agent_workflows/cli.py` read `args.dry_run` without breaking existing `MagicMock`-based unit tests in `tests/test_installer.py`? | Use `getattr(args, "dry_run", False) is True` across install helpers (matching `_split_brain_guard`'s existing `getattr(args, "_split_brain_consented", None) is True` idiom) and update all four exact-kwargs `execute_migration` assertions across `SplitBrainLayoutGuardTests` and `InstallLeftoverDispositionThreadingTests`. | Keep `bool(getattr(args, "dry_run", False))` and also mutate `MagicMock` setups across unrelated test classes (rejected: fragile against any future `MagicMock` caller and inconsistent with `cli.py:8779`). | `agent_workflows/cli.py::_split_brain_guard:8779`, `tests/test_installer.py::SplitBrainLayoutGuardTests.test_guard_clean_shapes_description_and_migration:4466-4485`, `tests/test_installer.py::InstallLeftoverDispositionThreadingTests:4635,4653,4752` | yes |
| D-2 | Where should the `--dry-run` `git fetch` / `git pull --rebase` leak in `_diagnostics_ok` -> `engine.run_git_diagnostics` be closed? | Short-circuit `agent_workflows/cli.py::_diagnostics_ok` to return `True` when `getattr(args, "dry_run", False) is True`, keeping `agent_workflows/engine.py` out of scope. | Modify `agent_workflows/engine.py::run_git_diagnostics` or `is_interactive_session` (rejected: expands `- Scope-Paths:` into `engine.py` when the leak on `aw install` is cleanly closed at `cli.py::_diagnostics_ok`, which already owns CLI preflight gating). | `agent_workflows/cli.py::_diagnostics_ok:8895-8924`, `agent_workflows/engine.py::is_interactive_session:2314-2320`, `agent_workflows/engine.py::run_git_diagnostics:4411-4510` | yes |
