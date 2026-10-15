# IPD: Route every records reader and writer through one records-root accessor

- Date: 2026-10-15
- Kind: child
- Concern: Record readers and writers compose `<repo>/.aw/records/...` (and legacy `<repo>/.agents/...`) by hand instead of asking where the resolver placed the `records` class. When the STORED policy (`project_config_dir(repo)/project.json`) puts records under `AW_HOME/projects/<project_id>/records` (`records_backend: home`, which is what `completely-clean-target` and `local-only` store) or a companion, ordinary use writes into the target anyway. Measured at HEAD `57d5e8184` on a temp repo whose stored policy is `records_backend: home`: `aw backlog new --apply` wrote `.agents/backlog/open/<item>.backlog.md` AND `.aw/records/history.jsonl` INTO THE TARGET (`backlog._resolve_backlog_root`, `record_history.history_path`); `aw index prompts` crashed with `FileNotFoundError` on `<repo>/.aw/records/prompts/INDEX.json` (`prompts.prompts_root`); while `aw specs new --apply` correctly wrote under the home records root. Half the verbs follow the resolver and half do not.
- Scope: Add ONE pure accessor `project_context.project_records_dir(repo_root, aw_home=None) -> Path` that returns the in-tree `<repo>/.aw/records` for a repository-backed (or unconfigured) project and the resolver's `physical_classes["records"]` when a STORED policy places records elsewhere; then convert every records path construction in `agent_workflows/` that DECIDES A LOCATION (writers, directory readers, scan roots, iterators) to use it, grouped by subsystem, and leave the remaining literals that are only PATH CLASSIFIERS on repo-relative strings (prefix tests, glob vocabularies, docstrings, comments, messages) unchanged with a recorded reason. Repository-backed installs (including this repository) keep byte-identical behavior. Out of scope: `system` bundle routing (`4gn1ka`), project-root recognition with no in-repo `.aw` (`fnnwj3`), run state, receipts, locks and worktrees (`qk0ew6`), the installer's records scaffolding (`3m8aix`), and uninstall (`xoy5yg`).
- Scope-Paths: agent_workflows/project_context.py, agent_workflows/prompts.py, agent_workflows/prompts_index.py, agent_workflows/backlog.py, agent_workflows/record_history.py, agent_workflows/specs.py, agent_workflows/releases.py, agent_workflows/review_findings.py, agent_workflows/research_contract.py, agent_workflows/research_index.py, agent_workflows/plans_index.py, agent_workflows/plans_refs.py, agent_workflows/plans_archive.py, agent_workflows/plans.py, agent_workflows/record_placement.py, agent_workflows/set_records.py, agent_workflows/ipd_authoring.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_set_plan.py, agent_workflows/selectors.py, agent_workflows/status_set.py, agent_workflows/artifact_core.py, agent_workflows/artifact_refs.py, agent_workflows/artifact_audit.py, agent_workflows/attention.py, agent_workflows/check_engine.py, agent_workflows/completion.py, agent_workflows/readiness_recheck.py, agent_workflows/orchestrator_readiness.py, agent_workflows/production_checks.py, agent_workflows/comms_acks.py, agent_workflows/comms_broker.py, agent_workflows/doctor.py, agent_workflows/cli.py, agent_workflows/runner_shared.py, agent_workflows/agy_run.py, tests/test_records_root_accessor.py, .aw/records/plans/pending/20261015-cleantgt-01-kfnfji-route-every-records-reader-and-writer-through-one-records-ro.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: kvwwt0
- Blocks-Release: next
- Set: cleantgt
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: kfnfji

## Workflow history
- 2026-10-15 reviewed (aw set): plan-review: revisions applied (PR-001..PR-007)
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-15 to-review (aw set): authored review-ready child of Set cleantgt (orchestrator ucr3h8) from backlog kvwwt0

- 2026-10-15 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every agent-workflows command that reads or writes a typed record find the records root in ONE place, so a project whose stored policy puts records under `AW_HOME` (or a companion) never gets a records file written into the target by ordinary use, while a repository-backed project behaves exactly as it does today.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline and the accessor

- [ ] E-01 Re-measure at execution HEAD and capture the failing baseline: re-run the records-literal census (the two `rg` commands in Findings F-02) and the home-records reproduction from F-01 (temp repo, stored `.aw/config/project.json` with `records_backend: home`, temp `AW_HOME`/`HOME`; run `aw backlog new ... --apply`, `aw index prompts --dir .`, `aw specs new ... --apply`; then `git status --porcelain --ignored` and a `find` of the target), and add the failing subprocess test file `tests/test_records_root_accessor.py` that encodes the F-01 reproduction as assertions (target tree clean of agent-workflows records files; the new records land under `<AW_HOME>/projects/<project_id>/records/`).
  - Depends on: none
  - Expected outcome: Census counts and the reproduction output are recorded in V-01; the new test file exists and FAILS on the unmodified code for the backlog, history-sidecar and prompts-index cases, and passes for the specs case (proving the fixture is sound).
  - Execution state: pending

- [ ] E-02 Add the pure accessor `project_context.project_records_dir(repo_root: str | Path, aw_home: Optional[str | Path] = None) -> Path` beside `project_context.project_config_dir`, with this rule: (1) let `cfg = project_config_dir(repo_root, aw_home=aw_home)`; if `cfg / "project.json"` (or legacy `config.json`/`policy.json`/`local.json`, the same files `resolve_project_context` treats as `is_configured`) does NOT exist, return `Path(repo_root) / ".aw" / "records"` (unconfigured repo: unchanged literal); (2) otherwise resolve `ctx = resolve_project_context(target_repo=str(repo_root), aw_home=...)` and treat the records placement as STORED only when `ctx.provenance["records_backend"]` has source `project_durable_config` or `machine_local_binding` (an explicit `records_backend` key, or one derived from a stored preset such as `public-target-private-companion`), OR the resolved `delivery_mode` is `clean-delta` (which the resolver forbids from using a repository backend); (3) when the placement is stored, return `Path(ctx.physical_classes[RootClass.RECORDS.value])`, except that a result equal to `_canonical_path(<repo>/.aw/records)` is returned as `Path(repo_root) / ".aw" / "records"` (caller spelling); (4) when a config file exists but the records placement is NOT stored (source `builtin_defaults`, `global_defaults` or `named_global_profile`, for example a `project.json` holding only `{"role": "target"}`), return `Path(repo_root) / ".aw" / "records"`, exactly as for an unconfigured repo (PR-001: the resolver's built-in default is `home`, so without this rule every fixture or legacy install whose config omits `records_backend` would silently move its records out of tree). Implement (2)-(3) through ONE private memoized helper `project_context._stored_physical_classes(repo_root, aw_home=None) -> Optional[Mapping[str, str]]` (returns `None` when no stored records placement exists per (1)/(4), else a read-only `types.MappingProxyType` of `physical_classes`, so a caller cannot mutate the cached value), so sibling child `4gn1ka` reuses it for `system` instead of adding a second cache, plus a public predicate `project_context.has_stored_records_placement(repo_root, aw_home=None) -> bool` (`_stored_physical_classes(...) is not None`) that E-03..E-06 use where a converted function must keep its current fallback. Memoize the helper per `(canonical repo, effective aw_home, (mtime_ns, size, ino) of each stored config file in cfg AND of the user config file `resolve_project_context` reads, `~/.config/agent-workflows/config.json` or the `user_config_dir` override)` with `functools.lru_cache`, mirroring `project_context._git_cached_entries`, so the cost stays at the measured `project_config_dir` level (about 21 microseconds per call) rather than `resolve_project_context` (about 5 milliseconds per call). A `ProjectContextError` from the resolver (conflicting config, clean-delta with a repository backend, path security) propagates unchanged and is NOT cached. No filesystem writes, no directory creation. Add unit tests to `tests/test_records_root_accessor.py` for: unconfigured repo, `repository`, `repository-untracked`, `home`, and `companion` stored backends, `local.json`-only `records_backend: home`, a stored `completely-clean-target` preset with no `records_backend` key, a stored `project.json` with NO `records_backend` and no preset (must stay in-tree), a home-stored config (`AW_HOME/projects/<id>/config/project.json`, no in-repo `.aw`), and the cache invalidating when `project.json` changes.
  - Depends on: E-01
  - Expected outcome: `project_records_dir` returns `<repo>/.aw/records` for unconfigured, config-without-stored-backend, `repository` and `repository-untracked` repos, `<AW_HOME>/projects/<id>/records` for stored `home`, `local.json` `home`, stored `completely-clean-target` and a home-stored config, and `<companion>/records` for `companion`; the unit tests pass; `project_context.py` still performs zero writes (spec 20260809-2211-01 invariant in the module docstring).
  - Execution state: pending

### Task group 2: Writers and per-type root resolvers

- [ ] E-03 Route the per-type ROOT RESOLVERS that writers and readers share through the accessor: `prompts.prompts_root`, `backlog._resolve_backlog_root` and `backlog._iter_items` (replace iteration over `backlog.BACKLOG_ROOTS` with the accessor-derived backlog root plus the legacy `<repo>/.agents/backlog` read fallback), `record_history.history_path`, `specs._specs_root` and `specs._spec_files` (the extra `local_specs` literal), `releases._releases_dir`, `review_findings.reviews_dir` and `review_findings.review_dirs`, `research_contract.resolve_research_root`, `research_index._roots`/`research_index.check_drift`, `plans_index._dirs`, `plans_refs._dirs`, `plans_archive._dirs`, `plans._resolve_area_dir`, `record_placement.resolve_type_dir`, `set_records.write_walkthrough`, `ipd_authoring.run_scaffold` (the `pending` mint dir), and `comms_acks._resolve_comms_dir` plus the three `comms_broker` CLI branches that build `repo_root / dirs["comms"]`. Each keeps its existing legacy `.agents/...` read fallback; only the MODERN root comes from `project_records_dir(repo_root) / <type subpath>`. PARITY GUARD (PR-002): where a converted function today falls through to `record_producers.resolve_record_path`/`resolve_record_read_paths` (`record_placement.resolve_type_dir`, `specs._spec_files`, and the E-04 `selectors._record_dirs_cached` resolver loop), keep that existing fall-through unchanged when `has_stored_records_placement(repo_root)` is False, so an unconfigured or config-without-backend repo resolves exactly as at HEAD (measured: `aw specs new --apply` on a bare `git init` repo and on a repo storing only `{"role":"target"}` both write under `<AW_HOME>/projects/<id>/records/specs/` today, while `aw backlog new` writes in-tree; unifying those is OQ-04, not this plan).
  - Depends on: E-02
  - Expected outcome: The E-01 subprocess test now passes for backlog, history sidecar, prompts index and specs; under `records_backend: home` no file appears under `<target>/.aw/records` or `<target>/.agents`; repository-backed fixtures resolve the same paths as before; an added subprocess case on a bare unconfigured repo shows `aw specs new --apply` and `aw backlog new --apply` land where they land at HEAD (recorded in V-01).
  - Execution state: pending

### Task group 3: Readers, scanners and iterators by subsystem

- [ ] E-04 Route the SHARED SCAN infrastructure: `artifact_core.iter_scan_files` resolves each `SCAN_ROOTS`/`REFERENCE_SCAN_ROOTS` entry beginning `.aw/records/` against `project_records_dir(repo_root)` (strip the `.aw/records/` prefix, join onto the accessor root) instead of `repo_root / rel`; fix `artifact_core.is_ignored_path` ITSELF (it has 43 call sites in 14 modules, including `specs._spec_files`, `releases`, `research_index`, `plans_index`, `prompts_index` and `check_engine`, so a scanner-only bypass would leave them blind, PR-003): in its outside-`repo_root` fallback, when the path lies under `project_records_dir(repo_root)` and that root is outside `repo_root`, compute `rel_path` as `.aw/records/<path relative to that root>` instead of the path's absolute parts, so the `tmp`/`.git`-style part filter no longer fires on the external root's ancestors while the `untracked` rule and `.aw/records/...` ignored-dir prefixes still apply (F-05); `selectors._record_dirs_cached` and `selectors._iter_paths` (the `.aw/records` literals, including the `other` sweep), and `status_set.detect_artifact_type` (the resolved records root it compares against).
  - Depends on: E-03
  - Expected outcome: `aw find`, `aw show`, `aw attention`, `aw check` and citation scans enumerate records under the external root on a home-backed fixture whose AW_HOME lives under the pytest temp dir (a path with a `tmp` component), a file under `<external>/prompts/untracked/` is still excluded, and they enumerate exactly the same file set as before on a repository-backed fixture (asserted by comparing the sorted path lists against the pre-change run in E-08).
  - Execution state: pending

- [ ] E-05 Route the CHECK, ATTENTION and DOCTOR readers: `check_engine._type_dirs`, `check_engine._iter_plan_ipds`, `check_engine._iter_spec_records`, `check_engine.stale_record_scope_paths` (the `records_dir` rglob), `attention.scan` (the uninventoried-tree `records_dir` and the `_TREE_TO_SCAN_ROOTS` roots it passes to `iter_scan_files`), `doctor.probe_installed_doc_references` (the records README glob), `artifact_refs.count_legacy_prefix_records` and `artifact_refs._index_records_facetless_stems`, `artifact_audit._dir_signature`, `completion.plan_id6_candidates` and `completion.set_id_candidates`, `readiness_recheck._sweep_paths`, `orchestrator_readiness.resolve_all_set_memberships`, `production_checks._find_executed_linked_plans`, and `ipd_lint._iter_plan_files`, `ipd_lint._default_pending_files`, `ipd_set_plan._repo_root_for_plans_dir` (accept an external plans dir by comparing against the accessor root).
  - Depends on: E-04
  - Expected outcome: On a home-backed fixture with a backlog item and a plan under the external root, `aw attention --format json` lists both, `aw check all` reports no `attention.uninventoried-tree` and no missing-tree error, and `aw ipd lint` on the external plan resolves its Set; repository-backed output is unchanged.
  - Execution state: pending

- [ ] E-06 Route the CLI and RUNNER plan/record discovery: `cli._run_search` (fallback bases), `cli._run_check` (the `plans_dir` evidence breakdown), `runner_shared.discover_plans`, `runner_shared.resolve_plan_path` (both `roots` lists), `runner_shared.review_has_positive_evidence`, `runner_shared.commit_backlog_close` (the `roots` list), `runner_shared.perform_coordinator_proposal_file` (the pending-plans and open-backlog dirs), `agy_run._candidate_plans` and `agy_run.resolve_ipd`. Do NOT touch the `runs` literals (`runner_shared.state_root`, `runner_shared.integrate_lane_branch` `runs_dir`, `runners_monitor.find_active_runners`, `run_analytics_cli._render_report_html`, `run_viewer.driver_holder_state`): run state is owned by `qk0ew6` (OQ-02).
  - Depends on: E-05
  - Expected outcome: `aw oc run start --prepare-only <id6>` (run with cwd = the fixture; `--prepare-only` is a `start` flag) and `aw show <id6>` resolve a plan that lives only under the external records root on a home-backed fixture; repository-backed resolution is unchanged.
  - Execution state: pending

### Task group 4: Residual audit and validation

- [ ] E-07 Re-run the F-02 census and classify EVERY remaining `.aw/records` occurrence in `agent_workflows/` into exactly one of: (a) routed through `project_records_dir` (should now be zero location-deciding constructions outside the accessor and the run-state/installer/uninstall sites owned by later children), (b) repo-relative PATH CLASSIFIER (prefix tests such as `check_engine._PLANS_PREFIX`, `runner_shared.RECORDS_TREE_PREFIX`, `hooks/executed_transition_gate._PLANS_PREFIX`, `attention._classify_tree`, `doctor._infer_artifact_type`, `ipd_schema` scope globs, `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS`, `artifact_core.RECORDS_SEGMENTS`), (c) docstring, comment or user message, (d) DEFERRED to a named sibling child (run state to `qk0ew6`; installer scaffolding `engine._record_scaffold_dirs`/`ensure_*_readmes`/`_DEEP_CLEANUP_ROOTS` to `3m8aix`/`xoy5yg`; `storage.materialize_companion_storage` companion tail; `layout_inventory`/`layout_migration` migration inventory to none, see Deferred). Write the classification as a table into this plan's V-07 evidence.
  - Depends on: E-06
  - Expected outcome: A complete table in which every occurrence has one class, class (a) constructions remain only inside `project_records_dir` itself (plus the PR-002 parity-guard fall-throughs, each listed), and every class (d) row names its carrier id6. If more than about 20 location-deciding sites remain unconverted (see the RIGHT-SIZING NOTE), they are filed as ONE follow-on backlog item via `aw backlog new --work-kind bug ... --apply` then `aw backlog set <id6> --blocks-release next`, and recorded as class (d) rows naming that id6.
  - Execution state: pending

- [ ] E-08 Prove byte-identical behavior for repository-backed installs and the clean-target fix together: run `aw find all --json`, `aw attention --format json`, `aw check all --json`, `aw index plans --check`, and `aw index prompts --check` in THIS repository before the change (E-01 baseline commit) and after, and diff the outputs after NORMALIZING the JSON (drop `data.elapsed_ms`; sort `diagnostics` and `next_actions` as `json.dumps(..., sort_keys=True)` strings) and comparing the two index commands by exit code plus stdout (PR-004: `find`/`check` reject `--format` with exit 2, and two identical `check all --json` runs at the same commit differ by 48 lines in `elapsed_ms` and `next_actions` order); first run each normalized command twice at the BASE commit to prove the normalization yields an empty control diff; run the narrowed tests (`python3 -m pytest -o addopts="" tests/test_records_root_accessor.py tests/test_record_producers.py tests/test_backlog.py tests/test_attention.py tests/test_plans_index.py tests/test_prompts_attention.py -q`), perform a mutation proof (temporarily make `project_records_dir` always return `<repo>/.aw/records`; the home-backed subprocess tests must fail; restore), and run the bare suite `python3 -m pytest`.
  - Depends on: E-07
  - Expected outcome: The base-commit control diffs and the before/after normalized diffs in this repository are empty; narrowed tests pass; the mutation turns the home-backed tests red and the restore turns them green; the bare suite shows no failure that does not also fail on the base commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `project_context.py` is PURE (module docstring: "PURE: ZERO filesystem writes, directory creation, or Git mutation."); the accessor must keep it so. Caching on a stat stamp is already the module's idiom (`project_context._git_cached_entries` keyed on `_git_index_stamp`).
- Every routing decision reads the STORED policy and `resolve_project_context(...).physical_classes`; never re-derive from preset names (irjoga PR-003/PR-004, maintainer decision 2026-10-15). Measured at HEAD `57d5e8184`: a repo with NO stored config resolves `physical_classes["records"]` to `AW_HOME/projects/<id>/records` (built-in default `records_backend: home`, provenance `builtin_defaults`), so the accessor MUST NOT call the resolver for an unconfigured repo, or every bare repo and every test fixture without config would silently move its records out of tree.
- Prior art for a per-type resolver that already follows the resolver: `record_producers.resolve_record_path` and `record_producers.resolve_record_read_paths` (used by `specs`, `plans_index`, `research_index`, `plans`, `selectors`, `record_placement`); `aw specs new` already lands under the home root (F-01). The new accessor is the root those resolvers' callers fall back from.
- Suite: bare `python3 -m pytest` (configured `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`); narrowed verbose runs use `-o addopts=""`. Tests assert outcomes through CLI subprocesses and return values (P16), never source text. Fixtures use temp `HOME`/`AW_HOME`, unset `XDG_CONFIG_HOME`/`AW_CONFIG_DIR`.
- Commit through `aw commit kfnfji -- <paths>`; never `git add -A`; never push.

## Findings

| # | Severity | Location | Finding |
| - | -------- | -------- | ------- |
| F-01 | High | `backlog._resolve_backlog_root`, `record_history.history_path`, `prompts.prompts_root` | Reproduced at HEAD `57d5e8184` (temp repo, stored `.aw/config/project.json` `{"preset":"private-target","delivery_mode":"tracked","records_backend":"home"}`, temp `AW_HOME`): `aw backlog new --summary x-thing --work-kind chore --priority low --slug x-thing --apply --dir .` printed `wrote <tmp>/t/.agents/backlog/open/20261015-mqeawt-01-mqeawt-x-thing.backlog.md` and `git status --porcelain --ignored` showed `?? .agents/` and `?? .aw/` with files `.aw/records/history.jsonl` and `.agents/backlog/open/...`; `aw index prompts --dir .` raised `FileNotFoundError: ... /t/.aw/records/prompts/INDEX.json`; `aw specs new --title Foo --slug foo --apply --dir .` wrote `<AW_HOME>/projects/t-e9be4b/records/specs/draft/20261015-ykvmo6-01-ykvmo6-foo.spec.md` (correct). The same backlog write into the target reproduces on a home-stored `completely-clean-target` config. |
| F-02 | High | 65 modules of `agent_workflows/` | Census at HEAD `57d5e8184`: `rg -o '\.aw/records\|"\.aw" / "records"\|"\.aw", "records"' agent_workflows --glob '*.py' \| wc -l` = 432 occurrences across 65 files. An AST classification of string constants matching `\.aw/records` gives 153 code literals, 106 docstrings, 72 comments; plus `"records"` path segments. Location-DECIDING constructions (`"\.aw" / "records"` chains and `Path(...".aw/records...")`) number 92 across 36 files (largest: `runner_shared.py` 9, `releases.py` 6, `check_engine.py` 6, `selectors.py` 4). The rest are repo-relative classifiers, messages and docs. Counts are context, re-derived in E-01/E-07. |
| F-03 | High | `artifact_core.SCAN_ROOTS`, `artifact_core.iter_scan_files` | The shared scanner joins each scan root onto `repo_root` (`p = repo_root / rel`), so every consumer (`attention.scan`, `artifact_refs`, `research_refs`, citation scans) is blind to an external records root. `attention._TREE_TO_SCAN_ROOTS` and `backlog.BACKLOG_ROOTS` are the same pattern as repo-relative tuples. |
| F-04 | Medium | `resolve_project_context` cost | Measured: 200 calls of `resolve_project_context(target_repo='.')` took about 1016 ms (about 5 ms each); 200 calls of `project_config_dir('.')` took about 4 ms. Readers such as `selectors._record_dirs_cached` run per type per command, so an uncached accessor that always resolved would add user-perceptible latency; E-02 memoizes on a config stat stamp. |
| F-05 | Medium | `artifact_core.is_ignored_path` | For a path outside `repo_root`, the function falls back to the path's own parts; measured: `is_ignored_path(Path('/tmp/pytest-1/aw/projects/x/records/plans/a.md'), Path('/srv/repo'), set())` returns `True` because the absolute path contains a `tmp` part, while the same file under `/home/u/.aw/...` returns `False`. An external records tree under a temp AW_HOME would therefore be silently skipped by every scanner. E-04 skips the target ignore check for an external records root. Note `untracked` parts are still honored by the explicit check, which is correct for `prompts/untracked`. |
| F-07 | High | `project_context.resolve_project_context` records-backend fallback | Plan-review measurement: with temp `HOME`/`AW_HOME`, a repo whose `.aw/config/project.json` is `{"role":"target"}` resolves `records_backend: home` with provenance `builtin_defaults`; a stored `{"preset":"completely-clean-target"}` also resolves `home` from `builtin_defaults` (clean-delta derived); `local.json` `{"records_backend":"home"}` resolves from `machine_local_binding`. File presence alone therefore does not prove a stored records placement; E-02 keys on provenance plus clean-delta. |
| F-06 | Low | `engine._record_scaffold_dirs` callers | `comms_acks._resolve_comms_dir` and the `comms_broker` CLI branches derive the comms dir from the INSTALLER's layout map (`engine.resolve_target_layout` plus `_record_scaffold_dirs`), which is a repo-relative literal; they are readers/writers of `comms/` at run time and belong here. The installer's own use of the map is `3m8aix`'s. |

## Proposed changes (ordered, validatable)

1. E-01: baseline census plus a failing subprocess test encoding F-01.
2. E-02: `project_context.project_records_dir(repo_root, aw_home=None)`. Design, chosen so repository-backed behavior is byte-identical by construction:
   - Unconfigured (no stored policy files in `project_config_dir`): return `<repo>/.aw/records` WITHOUT calling the resolver (F-04 and the built-in-home-default hazard in Step 0).
   - Configured but records placement NOT stored (provenance `builtin_defaults`/`global_defaults`/`named_global_profile` and delivery mode not `clean-delta`, e.g. `project.json` = `{"role":"target"}`): return `<repo>/.aw/records` (PR-001).
   - Configured with a STORED records placement (provenance `project_durable_config` or `machine_local_binding`, or `clean-delta`): return `physical_classes["records"]` from `resolve_project_context`; for `repository`/`repository-untracked` that is `_canonical_path(<repo>/.aw/records)`. To keep byte-identical paths (non-canonical spelling when `repo_root` is a symlink), when the resolved path equals the canonical form of `<repo>/.aw/records`, return `Path(repo_root) / ".aw" / "records"` as spelled by the caller.
   - Memoized on `(canonical repo, effective aw_home, (mtime_ns, size, ino) of each stored config file and of the user config file)`; resolver errors propagate uncached; returned mapping is read-only; pure.
   - Parity guard: where a converted function today falls through to `record_producers.resolve_record_path`, that fall-through is kept when `has_stored_records_placement` is False (PR-002, OQ-04).
3. E-03: per-type root resolvers (writers first, so F-01 is fixed earliest).
4. E-04: shared scanner, `is_ignored_path`'s external-root fallback, and selectors.
5. E-05: check, attention, doctor and lint readers.
6. E-06: CLI and runner discovery (not run state).
7. E-07: residual classification table.
8. E-08: in-repo before/after diff, mutation proof, bare suite.

## Deferred / out of scope (with reason)

- `system` bundle readers and writers (`manifest.resolve_manifest_path`, `engine.read_installed_version`, layout artifacts):
  - Carrier: 4gn1ka
- Recognizing a home-configured project with no in-repo `.aw` (`find_project_root`, `is_project_dir`, `doctor.probe_environment`, `cli._collect_repo_status_details`): this plan's tests pass `--dir` or keep a stored in-repo config so they do not depend on it.
  - Carrier: fnnwj3
- Run records, receipts, locks, journals and worktrees (`runner_shared.state_root`, `ipd_lifecycle.checkout_control_root`, `runners_monitor.find_active_runners`, `run_viewer.driver_holder_state`, `run_analytics_cli._render_report_html`, `runner_shared.integrate_lane_branch`, `worktree_lease`):
  - Carrier: qk0ew6
- Installer records scaffolding (`engine._record_scaffold_dirs`, `engine.ensure_plans_readmes`, `engine.ensure_prompts_readmes`, `engine.create_setup_artifacts`, `engine.migrate_local_lanes_to_untracked`, `engine._report_misplaced_run_records`):
  - Carrier: 3m8aix
- Uninstall and deep cleanup of records (`engine._DEEP_CLEANUP_ROOTS`, `cli._offer_deep_cleanup`):
  - Carrier: xoy5yg
- Layout migration and inventory (`layout_migration`, `layout_inventory`, `migration_compact`, `compat_migration`): these MOVE an in-tree legacy `.agents/` or `.aw/` layout and are defined over target-relative paths by design; a clean-target project has nothing in tree to migrate.
  - Carrier-Declined: migration operates on an existing in-repo layout, which a clean-target project does not have; routing it through the accessor would change what migration moves, a separate design decision outside backlog kvwwt0.
- Unconfigured-repo records-root divergence (OQ-04): `aw specs new`/`aw research new` resolve to `<AW_HOME>/projects/<id>/records` via the built-in `home` default while `aw backlog new` and the prompts/history writers stay in tree. Unifying them moves existing users' records, so this plan preserves today's split.
  - Carrier-Declined: pre-existing behavior on UNCONFIGURED repos, outside backlog kvwwt0 (stored clean-target policy) and outside this plan's byte-identical scope; surfaced to the maintainer by plan-review 2026-10-15 to file as a backlog item if they want one root.
- `storage.materialize_companion_storage` writes `<companion>/.aw/records`, a companion-container tail (spec 20260810-1447-01 Section 4 physical tail), not a target path.
  - Carrier-Declined: companion container layout is correct as is and unrelated to the target delta.

## Scope check

- Over-scope: none. Every listed module contains a location-deciding records construction (F-02) consumed by a verb in the `nwporz` ordinary-use list or by `aw check`/`aw attention`/`aw find`.
- Under-scope: the census is a lower bound until E-07 re-derives it at execution; any additional location-deciding site E-07 finds is converted in this plan (justified at finalize with `--scope-reason`) unless it belongs to a carrier above.

## Required tests / validation

- `tests/test_records_root_accessor.py` (new): unit tests of `project_records_dir` for each backend, `local.json`-only home, stored `completely-clean-target` without a `records_backend` key, a config with no stored backend (stays in-tree), a home-stored config, and the cache invalidation; a parity subprocess case on a bare unconfigured repo (PR-002); an `is_ignored_path` case for an external root under a `tmp` ancestor and for `<external>/prompts/untracked/` (PR-003); subprocess tests that run `aw backlog new --apply`, `aw index prompts`, `aw specs new --apply`, `aw research new`, `aw attention --format json` and `aw find all --json` against a home-backed fixture and assert (a) `git -C <target> status --porcelain --ignored` is empty apart from the stored in-repo config the fixture itself created, (b) the new records exist under `<AW_HOME>/projects/<id>/records/`, (c) attention/find list them.
- Repository-backed parity: normalized before/after JSON output diff of `aw find all --json`, `aw attention --format json`, `aw check all --json`, plus `aw index plans --check` and `aw index prompts --check`, in this repository, with a base-commit control diff proving the normalization (E-08, PR-004).
- Mutation proof on `project_records_dir` (E-08).
- Bare `python3 -m pytest` and narrowed `-o addopts=""` runs.

## Spec / documentation sync

- N/A for spec text in this child: spec 20260810-1447-01 already states the resolver returns each physical class separately (Section 4, "The resolver returns each physical class separately"); this plan makes readers obey that statement. The Section 4/5 clean-delta amendment is owned by `nwporz`.
- No CHANGELOG entry here; `nwporz` writes the single user-facing `- Fixed:` bullet for the Set.

## Open questions

### OQ-01: Should `project_records_dir` call the resolver for an unconfigured repository?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Measured at HEAD `57d5e8184`: `resolve_project_context` on a git repo with no stored config returns `records_backend: home` with provenance `builtin_defaults` and `physical_classes["records"] = <AW_HOME>/projects/<id>/records`. Routing an unconfigured repo there would relocate records for every bare repo and every existing test fixture. The maintainer rule is to read the STORED policy (brief, irjoga PR-003), so absence of stored policy means the in-tree literal, which is today's behavior. Plan-review PR-001 extended the same reasoning to a config file that EXISTS but does not store a records placement: measured at review, `resolve_project_context` on a repo whose `project.json` is `{"role":"target"}` also returns `home` with provenance `builtin_defaults`, so "a config file exists" is not the same as "the policy stores records elsewhere"; E-02 therefore keys on the `records_backend` provenance, not on file presence alone.

### OQ-02: Are `records/runs` readers part of this child?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The Set layout assigns run state, receipts, locks, journals and worktrees to `qk0ew6` (Order 04), and `runner_shared.state_root` already derives from `logical_roots["records"]`. Splitting run state across two children would make neither testable alone.

### OQ-03: Does this child need project-root recognition without an in-repo `.aw` to be testable?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. `fnnwj3` (Order 03) owns that. This child's fixtures keep the policy in a stored location the existing `project_config_dir` rule already finds and pass `--dir`, as the F-01 reproduction did, so every assertion here is reachable at HEAD plus this plan.

### OQ-04: Should an unconfigured repository's specs, research and plans keep landing under `AW_HOME` while its backlog lands in tree?

- Blocking: no
- Status: resolved
- Owner: plan author (plan-review)
- Resolution or deferral rationale: Preserve it here; out of scope. Pre-existing divergence measured at review on a bare `git init` repo with temp `HOME`/`AW_HOME`: `aw specs new --apply` wrote `<AW_HOME>/projects/<id>/records/specs/draft/...` (through `record_placement.resolve_type_dir` -> `record_producers.resolve_record_path`, which always resolves, so the built-in `home` default applies), while `aw backlog new` writes `<repo>/.agents/backlog/...`. This plan deliberately PRESERVES both (E-03 parity guard, PR-002) so repository-backed and unconfigured behavior stays byte-identical; choosing one root for an unconfigured repo changes where existing users' records land, which is the maintainer's call and is outside this plan's declared scope ("Repository-backed installs ... keep byte-identical behavior"). Recorded as a Deferred row; this child's clean-target fix is correct under either later answer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted census command output (both `rg` counts) and the pasted reproduction transcript showing the target-tree files and the `FileNotFoundError`, plus pasted `python3 -m pytest -o addopts="" tests/test_records_root_accessor.py -q` output with the expected failures on the unmodified code.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff -- agent_workflows/project_context.py` showing only the accessor, `_stored_physical_classes` and `has_stored_records_placement` (no write calls), and pasted narrowed pytest output of the accessor unit tests (all backends, `local.json` home, stored clean-target preset, config-without-stored-backend staying in-tree, home-stored config, cache invalidation) passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted subprocess-test output (reachable via `backlog.run_new` -> `backlog._resolve_backlog_root`, `record_history.append` -> `history_path`, `prompts_index.run_index` -> `prompts.prompts_root`) showing the backlog, history and prompts-index cases now pass, a pasted `git -C <target> status --porcelain --ignored` from the fixture showing no records files in the target, and the pasted bare-unconfigured-repo parity case output showing `aw specs new` and `aw backlog new` land at their HEAD locations.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `aw find all --json` output from the home-backed fixture (reachable via `selectors.record_dirs` -> `_record_dirs_cached`) listing the external records, and the pasted narrowed pytest run of the scanner tests, including the `is_ignored_path` cases (external root under a `tmp` ancestor enumerated; `<external>/prompts/untracked/` still excluded).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted `aw attention --format json` and `aw check all` output from the home-backed fixture (reachable via `attention.scan` and `check_engine._iter_plan_ipds`) showing both external artifacts and no uninventoried-tree or missing-tree finding.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted `aw show <id6>` and `aw oc run start --prepare-only <id6>` output (the queue line naming the external plan path) (reachable via `runner_shared.resolve_plan_path` and `runner_shared.discover_plans`) resolving a plan that exists only under the external records root.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: The pasted re-run census and the complete classification table (one row per remaining occurrence or per homogeneous group, each with class a/b/c/d and, for d, the carrier id6), plus, if the residual exceeded the RIGHT-SIZING threshold, the pasted `aw backlog new ... --apply` output naming the follow-on item's id6.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: The pasted normalization script, pasted empty base-commit control diffs, pasted empty normalized before/after diffs for the five in-repo commands, pasted narrowed pytest output, pasted mutation-red and restore-green output, and the pasted summary line of the bare `python3 -m pytest` (any failure shown to fail identically on the base commit).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

RIGHT-SIZING NOTE. This child touches about 36 modules but each E-item is one subsystem and one concern, and the accessor makes every conversion mechanical (replace a `repo_root / ".aw" / "records"` construction with `project_records_dir(repo_root)`). It fits one focused pass ONLY in that grouped order. If at E-07 the residual census shows more than about 20 location-deciding sites still unconverted, do not widen this pass: commit the completed groups, file the remainder as ONE release-gated follow-on backlog item (E-07), record it in V-07, and continue to E-08.

Execute only after human approval (`aw ipd set approved kfnfji --by-human`). Execute in an isolated worktree via `aw work begin kfnfji` (or under `aw oc run`, which isolates by default), then `aw ipd begin kfnfji`, and perform E-01..E-08 in order. Commit per task group through `aw commit kfnfji -- <paths>`, verifying `git diff --cached --name-only` first; never `git add -A`, never push, never tag. HONESTY: every `V-*` pastes ACTUAL output. Scope fence: `- Scope-Paths:` is a declaration; an out-of-scope edit is justified at finalize with `--scope-reason`. Post-gate: `aw ipd lint --phase pre-transition` must conform; under a runner the runner finalizes, by hand run `aw ipd finalize kfnfji`. Inherits `- Blocks-Release: next` from `kvwwt0`.
