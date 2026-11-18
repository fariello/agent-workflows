# Review findings: ipd 58isyp

- Subject-Id: 58isyp
- Subject-Type: ipd
- Reviewed-At: 2026-11-18
- Reviewer: antigravity/gemini-4-hydrogen-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `ab5973dcf` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261117-installmore-02-58isyp-add-aw-install-more-opt-in-companion-installer-and-discovery.ipd.md` was committed and clean at turn start, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`exit: 0`, `2` non-blocking `info` `IPD-C802` advisories on the boilerplate validation rule), while `aw ipd lint --phase review-finalize --agent --verbose` exited `1` with error `check.ipd-uncarried-obligation` on both rows of `## Deferred / out of scope (with reason)`. Inspection against `agent_workflows/cli.py`, `agent_workflows/command_surface.py`, `agent_workflows/completion.py`, `agent_workflows/agent_schema.py`, `agent_workflows/result_types.py`, `agent_workflows/check_engine.py`, `pyproject.toml`, `.pre-commit-config.yaml`, `conftest.py`, `tests/test_command_surface_declarations.py`, `tests/test_exit_contract_conformance.py`, `tests/test_agent_surface_conformance.py`, `tests/test_completion.py`, `tests/test_installer.py`, `tests/test_cli.py`, and sibling plans `5qqgfb` / `z403j4` produced findings PR-001..PR-005, all fixed in place.

### Proofreading

Checked `.aw/records/plans/pending/20261117-installmore-02-58isyp-add-aw-install-more-opt-in-companion-installer-and-discovery.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Front matter | `- Status: to-review`, missing `- Readiness:` / `- Review-Depth:`, `- Scope:` / `- Scope-Paths:` listed `tests/test_command_surface_declarations.py` as edited | Updated `- Status: reviewed` via `aw ipd set`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard`, and scoped `test_command_surface_declarations.py` to execution validation rather than file edits | Step S7 front-matter requirements and accurate `- Scope-Paths:`. |
| Workflow history | `to-review` and `draft` lines only | Prepended `reviewed (aw set)` and `/plan-review` lines citing `APPROVE WITH REVISIONS APPLIED; PR-001..PR-005` and review record path | Step S7 newest-first history requirement. |
| E-01, Project conventions | Omitted `from __future__ import annotations`, Windows `.cmd` / whitespace-safe POSIX wrappers, `INSTALL_SENTINEL`, atomic writes, and symlink refusal | Added Python 3.9+ typing rules, `INSTALL_SENTINEL`, atomic writes, symlink refusal, `force=True` backup rules, and POSIX + Windows launcher generation | PR-002, PR-004, Compatibility / Security / Atomicity. |
| E-02, E-03, V-02, V-03 | Referenced non-existent `--quiet` flag, omitted `OutputContext` wiring and `agent_schema.redact_home_paths`, left `--bin-dir` without `more` and foreign collisions ambiguous, and had `V-03` contradict `E-03` on `--dry-run` | Removed `--quiet`, wired `context: OutputContext` and `redact_home_paths` + `render_guarded_jsonl_record`, added exit-2 validation and interactive/non-interactive foreign-collision rules, updated `_DESCRIPTIONS["install"]` / `targets` help, and fixed `V-03` to use a non-dry-run temp-repo install | PR-003, PR-004, References / CLI Contract / Internal Consistency. |
| E-04, E-05, Required tests, V-04, V-05 | Omitted `pytestmark = pytest.mark.core`, sub-2s timing, and direct `mypy` / `ruff` checks | Required `pytestmark = pytest.mark.core`, fast in-process calls, `test_agent_surface_conformance.py`, and direct `mypy` / `ruff check` / `ruff format --check` commands | PR-002, Core-tier and static-gate coverage. |
| Proposed changes diagram | Omitted exit-2 target/flag check, separate `--yes` vs interactive prompt paths, and foreign-file collision branch | Added exit-2 validation branch, split `--yes` vs interactive `[y/N]`, added foreign-file collision branch, and aligned `K` with human non-dry-run tip conditions | PR-003, PR-004, Technical Writing Standard Requirement 12(d)/(e). |
| Deferred / out of scope | Two rows with no durable carriers | Added `- Carrier-Declined:` with explicit rationale to both rows | PR-001, `check.ipd-uncarried-obligation` compliance. |
| Approval and execution gate | Single sentence without execution contract | Replaced with full execution contract (open questions, scope fence, safety stop, evidence honesty, path-scoped `aw commit`, conditional runner/hand-executor finalize) | PR-005, `steps/s7-finalize.md` execution-contract rules. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |
| (none) | | | | | |

### Step T

1. Yes. Adds `--bin-dir` to `aw install`, defines `aw install more` target dispatch with interactive/`--yes`/`--dry-run`/`--agent`/`--json` behavior, adds `_install_more_tip`, and updates `CommandDeclaration(command="install")` in `agent_workflows/command_surface.py`.
2. No. Does not touch code guarding private data, commits, worktree isolation, or sandboxes.
3. No. Compact child plan with 5 execution items in 1 task group and 6 scope paths.
4. Yes. `- Scope-Paths:` lists `agent_workflows/install_more.py`, `agent_workflows/cli.py`, `agent_workflows/command_surface.py`, `tests/test_install_more.py`, `README.md`, and this plan file.
5. Yes. Clobbering a user's existing non-AW binary in `~/.local/bin`, breaking `aw install` / `aw install all`, emitting raw `/home/` paths in `--agent` records, or breaking Python 3.9 / Windows / core-tier gates would harm users or CI.

AW-TIER: standard

### Step R1

- Checked: `agent_workflows/cli.py` (`_DESCRIPTIONS["install"]`, `p_install`, `_run_install`, `_install_all`, `_completion_tip`, `_configure_completion`, `_confirm`, `_dispatch`), `agent_workflows/command_surface.py` (`CommandDeclaration(command="install")`), `agent_workflows/completion.py` (`INSTALL_SENTINEL`, `install_shell_completion`, `uninstall_shell_completion`, `installed_completion_state`), `agent_workflows/agent_schema.py` (`validate_agent_record`, `redact_home_paths`), `agent_workflows/result_types.py` (`select_output`, `OutputMode`, `OutputContext`), `agent_workflows/check_engine.py` (`evaluate_carrier_obligation`), `pyproject.toml`, `.pre-commit-config.yaml`, `conftest.py`, `README.md`, `tests/test_command_surface_declarations.py`, `tests/test_exit_contract_conformance.py`, `tests/test_agent_surface_conformance.py`, `tests/test_completion.py`, `tests/test_installer.py`, `tests/test_cli.py`, and sibling plans `5qqgfb` and `z403j4`.
- Checked: Confirmed `p_install` and `common` in `agent_workflows/cli.py` define no `--quiet` flag, `_run_install` does not receive `context: OutputContext` in `_dispatch`, and `tests/test_command_surface_declarations.py` checks `find_undeclared_leaves` with no flag allowlist on `install`.

### Step R2

- Checked: 1:1 bijection between `E-01..E-05` and `V-01..V-05`; `- Scope-Paths:` completeness; `- Item-Dependencies: executed:z403j4`; concrete pasted evidence in `V-01..V-05` (resolved `V-03` `--dry-run` contradiction); runtime-demonstration reachability (`install_more.*`, `aw install more`, `aw install <tmp_repo> --yes`); durable carriers on `## Deferred / out of scope` (`PR-001`); and full execution contract in `## Approval and execution gate` (`PR-005`).

### Step R3

- Checked: Security and privacy across trust boundaries: `INSTALL_SENTINEL` ownership checks, symlink refusal, atomic temp-file writes, `extra.name` path-component validation, non-directory `--bin-dir` refusal, foreign-file non-clobbering and backup policy (`PR-004`), `shlex.quote` on printed `export PATH` guidance, zero dotfile edits, and `agent_schema.redact_home_paths` on `--agent` JSONL output (`PR-003`).

### Step R4

- Checked: Engineering rubric, Python 3.9–3.14 and POSIX/Windows compatibility (`from __future__ import annotations`, POSIX whitespace-safe fallback, Windows `.cmd` wrapper), `@pytest.mark.core` tier selection in `tests/test_install_more.py` (`conftest.py::pytest_collection_modifyitems`), direct `mypy` / `ruff` checks in `E-05` / `V-05`, right-sizing (5 single-concern E-items, 6 Scope-Paths), and `README.md` dash-free prose rule.

### Step S5

- Checked: `58isyp` has no unresolved open questions (`OQ-*`) and all findings `PR-001..PR-005` are resolved cleanly from repository evidence with `Low` remediation risk and `Reversible: yes` decisions `D-1..D-5` recorded below.

### Pass 2

- Re-checked after Round 1 edits (Step S6 triggered by updating `- Scope-Paths:`, `E-01..E-05`, `V-01..V-05`, and the Mermaid flowchart): verified 1:1 `E-*`/`V-*` mapping, zero internal contradictions (`V-03` vs `E-03`, foreign-collision handling in `E-01`/`E-02`/`E-04`), Mermaid diagram alignment with `E-02`/`E-03`, and clean `aw ipd lint --phase review-finalize` disposition.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PR-001 | HIGH | IN-SCOPE | Governance / Durable Carriers | `.aw/records/plans/pending/20261117-installmore-02-58isyp-add-aw-install-more-opt-in-companion-installer-and-discovery.ipd.md:97-100` (`## Deferred / out of scope (with reason)`) | `aw ipd lint --phase review-finalize` exited `1` with `check.ipd-uncarried-obligation` because both deferred bullets lacked `- Carrier:`, `- Carrier-Evidence:`, or `- Carrier-Declined:`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Carrier-Declined:` with explicit rationale to both deferred rows. Recommendation strength: strong. |
| PR-002 | HIGH | IN-SCOPE | Compatibility / Python 3.9+, Cross-Platform Launchers & Core Tier | `pyproject.toml:12`; `conftest.py::pytest_collection_modifyitems:130-161`; `.pre-commit-config.yaml:120-125`; `.aw/records/plans/pending/20261117-installmore-02-58isyp-add-aw-install-more-opt-in-companion-installer-and-discovery.ipd.md:36,51,56,141-146` | `E-01` used `Path \| None` without requiring `from __future__ import annotations` and omitted Windows `.cmd` / whitespace-safe POSIX wrapper handling; `E-04` omitted `pytestmark = pytest.mark.core`; `E-05`/`V-05` omitted direct `mypy` and `ruff` checks (`static-type-gate-commit` skips unstaged `--files`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Python 3.9+ typing and POSIX/Windows launcher rules to `E-01`, `pytestmark = pytest.mark.core` to `E-04`, and direct `mypy`/`ruff` checks to `E-05`/`Required tests`/`V-05`. Recommendation strength: strong. |
| PR-003 | HIGH | IN-SCOPE | CLI Contract / `--quiet`, `--agent` Path Redaction & `V-03` Consistency | `agent_workflows/cli.py:1520-1543,1587-1691,20553`; `agent_workflows/agent_schema.py::validate_agent_record:358-375`; `.aw/records/plans/pending/20261117-installmore-02-58isyp-add-aw-install-more-opt-in-companion-installer-and-discovery.ipd.md:41,46,136` | `E-03` referenced a non-existent `--quiet` flag; `E-02` omitted wiring `OutputContext` into `_run_install` and redacting home paths via `agent_schema.redact_home_paths` in `--agent` records (which `validate_agent_record` rejects); `V-03` demanded `aw install --dry-run` tip output while `E-03` explicitly skips `--dry-run`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed `--quiet`, added `OutputContext` + `redact_home_paths` + `aw.agent/v1` outcome contract to `E-02`, added `_DESCRIPTIONS["install"]`/`targets` help updates to `E-03`, removed unneeded `test_command_surface_declarations.py` from `- Scope-Paths:`, and fixed `V-03` to use a non-dry-run temp-repo install. Recommendation strength: strong. |
| PR-004 | MEDIUM | IN-SCOPE | Security / Sentinel Ownership, Atomicity & Foreign-File Collisions | `agent_workflows/completion.py::install_shell_completion:1205-1283`; `.aw/records/plans/pending/20261117-installmore-02-58isyp-add-aw-install-more-opt-in-companion-installer-and-discovery.ipd.md:36,41,51` | `E-01` mentioned `force=False` and leaving foreign files untouched unless confirmed/forced, while `E-02` provided no foreign-file collision flow and `E-01` omitted `INSTALL_SENTINEL`, atomic temp-file writes, symlink refusal, `extra.name` validation, and `shlex.quote` on `PATH` output. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `INSTALL_SENTINEL`, atomic writes, symlink refusal, `extra.name`/dir validation, `shlex.quote` `PATH` tip, and interactive `[y/N]` backup vs non-interactive exit-1 collision handling across `E-01`, `E-02`, `E-04`, and the Mermaid flowchart. Recommendation strength: strong. |
| PR-005 | MEDIUM | IN-SCOPE | Governance / Execution Gate | `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46`; `.aw/records/plans/pending/20261117-installmore-02-58isyp-add-aw-install-more-opt-in-companion-installer-and-discovery.ipd.md:150-155` | `## Approval and execution gate` omitted the required execution-contract clauses and used an unconditional `aw ipd finalize` instruction. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced gate prose with the full execution contract and conditional runner/hand-executor `aw ipd finalize 58isyp` ownership. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D-1 | Which durable carrier subfield should the two deferred bullets in `58isyp` carry? | `- Carrier-Declined:` with explicit rationale on both bullets. | File new backlog items for programmatic-only `uninstall_extra` follow-up and dotfile editing (dotfile editing is intentionally excluded by design; CLI uninstall is explicitly deferred until more extras exist). | `agent_workflows/check_engine.py::evaluate_carrier_obligation:10074-10190`; `agent_workflows/completion.py` | yes |
| D-2 | Should `tests/test_command_surface_declarations.py` remain in `- Scope-Paths:`? | Remove `tests/test_command_surface_declarations.py` from `- Scope-Paths:` (keeping it in `E-05`/`V-02` validation) and place the `--bin-dir` `legacy_flags` assertion in `tests/test_install_more.py`. | Keep `tests/test_command_surface_declarations.py` in `- Scope-Paths:` even though it has no `install` flag allowlist to edit (requiring `--scope-ack` at finalize). | `tests/test_command_surface_declarations.py:1-150` | yes |
| D-3 | How should `E-03` handle the non-existent `--quiet` flag and `V-03` tip verification? | Remove `--quiet` and skip `_install_more_tip` when `OutputMode.HUMAN` is inactive (`--agent`/`--json`) or `--dry-run` is set; validate with a non-dry-run temp-repo `aw install <tmp_repo> --yes` run in `V-03`. | Add a brand-new global `--quiet` flag to `aw install` (over-scope) or keep the `--dry-run` contradiction in `V-03`. | `agent_workflows/cli.py:1488-1691,9583-9610`; `agent_workflows/result_types.py::select_output:66-150` | yes |
| D-4 | How should `install_more` handle foreign non-AW files at the target launcher path without adding a new `--force` CLI flag? | Embed `INSTALL_SENTINEL` in AW-managed launchers, refuse foreign files/symlinks by default in `install_extra` (`force=False`) and `uninstall_extra`, prompt `[y/N]` interactively in `aw install more` to back up (`*.bak`) and replace, and exit `1` without touching foreign files non-interactively. | Overwrite foreign files silently (data loss) or add an unrequested `--force` CLI flag to `p_install`. | `agent_workflows/completion.py::install_shell_completion:1205-1283`; `steps/r3-security.md` | yes |
| D-5 | How should `aw install more --agent` represent user bin and launcher paths in `aw.agent/v1` records? | Pass all home/user paths through `agent_schema.redact_home_paths` before emitting via `agent_schema.render_guarded_jsonl_record`. | Emit raw `Path.home()` strings (fails `agent_schema.validate_agent_record` with `Unsanitized absolute home path`). | `agent_workflows/agent_schema.py::validate_agent_record:358-375`, `redact_home_paths:168-188` | yes |
