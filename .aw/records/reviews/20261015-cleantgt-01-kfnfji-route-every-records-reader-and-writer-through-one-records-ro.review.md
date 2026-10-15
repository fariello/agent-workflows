# Review findings: plan kfnfji

- Subject-Id: kfnfji
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`23863c32a`), so no snapshot was needed. `aw ipd lint --phase author` was clean before the review, and `--phase review-finalize` is clean after it. All 90 cited symbols resolve in `agent_workflows/`. The F-02 census re-ran to the same totals: 432 occurrences in 65 files.

Probes ran with temp `HOME`/`AW_HOME` under `/tmp/opencode`:

- `resolve_project_context` on 8 fixtures. These were: `{"role":"target"}` -> home/builtin_defaults; `records_backend: home` -> home/project_durable_config; `repository` -> in-tree; `local.json` home -> machine_local_binding; companion preset -> `<repo>.aw/records`; `completely-clean-target` preset with no backend key -> home/builtin_defaults; `repository-untracked` -> in-tree; home-stored config -> project_durable_config.
- A prototype of the revised E-02 rule produced the intended root for all 8 fixtures.
- `aw specs new --apply` on a bare `git init` repo, and on a `{"role":"target"}` repo, both wrote under `<AW_HOME>/projects/<id>/records/specs/draft/`.
- `is_ignored_path` returned True for an external root under `/tmp/pytest-of-u/...`.
- `aw find all --format json` and `aw check all --format json` exit 2 with "unrecognized arguments: --format".
- Two identical runs of `aw check all --json` differed by 48 diff lines. The only differences were `data.elapsed_ms` and the order of `next_actions`; the sorted diagnostics were equal.
- `aw oc run --help` lists only subcommands, and `--prepare-only` is a `start` option.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | D. Anti-regression | `agent_workflows/project_context.py:1170` `resolve_project_context` else-branch "built-in default (home)"; `project_context.py:975` `is_configured` set by file presence | E-02 called the resolver whenever any config file existed. A `project.json` without a `records_backend` key, such as a test fixture `{"role":"target"}` (`tests/test_config_release_gate_kinds.py:30`) or a legacy install, resolves to `home` from `builtin_defaults`. That would have silently moved those repos' records out of tree, which breaks the plan's byte-identical promise and repeats the hazard OQ-01 had guarded against. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now treats a placement as stored only when the `records_backend` provenance is `project_durable_config` or `machine_local_binding`, or the mode is clean-delta; otherwise it returns in-tree. The prototype was correct on all 8 fixtures. Added unit cases; updated Proposed changes, OQ-01 and V-02; added F-07. |
| PR-002 | MEDIUM | IN-SCOPE | D. Anti-regression | `agent_workflows/record_placement.py:89` `resolve_type_dir` -> `resolve_record_path`; `agent_workflows/selectors.py:296` `_record_dirs_cached` -> `resolve_record_read_paths`; `agent_workflows/specs.py:117` | Several listed functions already fall through to `record_producers.resolve_record_path`, which always resolves. On unconfigured repos they therefore write to AW_HOME today. Routing them only through the in-tree-for-unconfigured accessor would change that behavior, the opposite of the parity claim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the E-03 parity guard (keep the existing fall-through when `has_stored_records_placement` is False), a bare-repo parity subprocess case, and OQ-04 recording the divergence, which is preserved and reported to the maintainer. |
| PR-003 | MEDIUM | UNDER-SCOPE | A. Correctness | `agent_workflows/artifact_core.py:704` `is_ignored_path` fallback `rel_path = Path(path.as_posix())`; 43 call sites in 14 modules | E-04 bypassed the ignore check only inside `iter_scan_files`. Other callers (`specs._spec_files`, `releases`, `research_index`, `plans_index`, `prompts_index`, `check_engine`) would still drop an external root whose ancestors include `tmp`, so `aw specs check` and the indexes would be blind under a temp AW_HOME and the E-04/E-05 tests could fail for the wrong reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now fixes `is_ignored_path` itself. A path under an external records root is re-based to `.aw/records/<rel>`, so the `untracked` and ignored-dir rules still apply. Added test cases and V-04 evidence. |
| PR-004 | MEDIUM | IN-SCOPE | E. Verification feasibility | `aw find all --format json` / `aw check all --format json` -> exit 2 "unrecognized arguments: --format"; two `check all --json` runs differ in `elapsed_ms` and `next_actions` order | E-08 asked for an empty before/after diff using flags those commands reject, and the corrected command is nondeterministic, so V-08 could not be satisfied. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Switched to `--json` for find/check. The diff now drops `elapsed_ms` and sorts `diagnostics`/`next_actions`, and a base-commit control diff is required. Updated Required tests, V-04 and V-08. |
| PR-005 | LOW | IN-SCOPE | E. Reachability | `aw oc run --help` lists `{start,resume,status,...}`; `--prepare-only` belongs to `start` | E-06/V-06 named `aw oc run --prepare-only <id6>`, a spelling that is not the documented one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now `aw oc run start --prepare-only <id6>` with cwd = the fixture; V-06 asks for the queue line naming the external path. |
| PR-006 | LOW | IN-SCOPE | C. Caching | E-02 cache key "stat-stamp of the stored config files"; `resolve_project_context` also reads `~/.config/agent-workflows/config.json` | The cache key left out the user config the resolver reads, did not say whether resolver errors are cached, and returned a mutable cached dict. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The key now includes the user config stat. `ProjectContextError` propagates and is not cached, and the helper returns a `MappingProxyType`. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | RIGHT-SIZING NOTE "STOP after committing ... ask for a follow-on child" | A stop-and-ask over a scope size question strands an unattended turn, which plan-review's scope-fence ruling forbids, and it named no durable carrier for the remainder. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The remainder is now filed as one release-gated backlog item and execution continues to E-08 (E-07, V-07, gate). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What counts as a STORED records placement for the accessor? | `records_backend` provenance `project_durable_config` or `machine_local_binding`, or delivery mode `clean-delta` | Any config file present (original plan; moves fixtures out of tree); explicit `records_backend` key only (misses stored companion and clean-target presets) | `project_context.py:1131-1175` provenance branches; review probe of 8 fixtures | yes |
| D-2 | Should unconfigured-repo writers that today resolve to AW_HOME (specs, research) be changed? | Preserve them (parity guard) and record the divergence as OQ-04 / Carrier-Declined | Unify on in-tree (moves existing users' specs); unify on AW_HOME (moves backlog) | Plan Scope "Repository-backed installs ... keep byte-identical behavior"; review probe `aw specs new` on bare repo | yes; maintainer told in this review report 2026-10-15 |
| D-3 | Fix the ignore filter in the scanner only, or in `is_ignored_path`? | In `is_ignored_path`, re-basing external-root paths | Scanner-only bypass (leaves 13 other modules blind) | `rg 'is_ignored_path\(' agent_workflows` = 43 sites / 14 files | yes |
| D-4 | How to prove repository-backed parity when `check all --json` is nondeterministic? | Normalize (drop `elapsed_ms`, sort lists) plus a base-commit control diff | Raw diff (unsatisfiable); drop `check all` from parity (weaker) | Two-run probe at `23863c32a` | yes |
| D-5 | What to do when the residual census exceeds the right-sizing threshold? | File one release-gated backlog item and continue | Stop and ask (strands unattended runs) | plan-review scope-fence wording ruling 2026-09-01 | yes |
