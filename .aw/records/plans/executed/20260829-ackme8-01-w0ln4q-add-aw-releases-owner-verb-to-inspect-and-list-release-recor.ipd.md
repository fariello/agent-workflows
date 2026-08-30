# IPD: Add 'aw releases' owner verb to inspect and list release records

- Date: 2026-08-29
- Kind: child
- Concern: Releases are a first-class record class (`.aw/records/releases/`, `releases.py`, `Blocks-Release` gating across every tree) but the ONE records tree with no owner-verb: backlog, specs, plans, and research all have `aw <type>`, whereas releases has none. Developers and agents cannot ask "what is the planned release, its id6/version, and everything gating it?" on demand via a dedicated CLI owner-verb.
- Scope: Add the `releases` (and `release` alias) owner verb to the `aw` CLI with subcommands: `list` (default bare `aw releases`), `show` (detailed view with aggregated release blockers), `new` (scaffold a release record via CLI with dry-run/apply), with full `--json` and `--agent` support, tab completion integration, and test coverage. A `releases check` subcommand is deliberately EXCLUDED: `aw check releases` already validates release records via `check_engine.py:489` -> `releases.validate_release` (verified working: `aw check releases` -> `CONFORMS 1 releases checked`), so adding a second validation entry point would duplicate a canonical path.
- Scope-Paths: agent_workflows/releases.py, agent_workflows/cli.py, agent_workflows/completion.py, .aw/records/releases/README.md, tests/test_releases.py, tests/test_releases_cli.py
- Item-Dependencies: none
- From-Backlog: ackme8
- Blocks-Release: next
- Priority: medium
- Status: executed
- Set: ackme8
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: w0ln4q

## Workflow history
- 2026-08-30 executed (opencode its_direct/pt3-claude-opus-5-1m-us): aw releases owner verb (list/show/new) added; V-01..V-05 verified with pasted evidence [Scope reconciliation - in-scope-unmodified .aw/records/releases/README.md: modified-and-committed-in-c5c7a27-before-receipt-refresh; in-scope-unmodified agent_workflows/cli.py: modified-and-committed-in-c5c7a27-before-receipt-refresh; in-scope-unmodified agent_workflows/completion.py: modified-and-committed-in-c5c7a27-before-receipt-refresh; in-scope-unmodified agent_workflows/releases.py: modified-and-committed-in-c5c7a27-before-receipt-refresh; in-scope-unmodified tests/test_releases.py: modified-and-committed-in-c5c7a27-before-receipt-refresh; in-scope-unmodified tests/test_releases_cli.py: created-and-committed-in-c5c7a27-before-receipt-refresh]
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 fixed; readiness GO - PENDING HUMAN APPROVAL. PR-001 get_release_blockers must REUSE attention.release_blockers (attention.py:582) not re-scan; PR-002 dropped the duplicate 'releases check' subcommand (aw check releases already validates via check_engine.py:489, verified CONFORMS) and added a test asserting it is not reintroduced; PR-003 replaced all five un-falsifiable V-items (which said only 'tests passing'/'100% verification') with exact commands plus required strings, set-equality and adversarial assertions; also hardened the execution gate with a scope fence, honesty rule, and reuse rule.

- 2026-08-29 to-review (Antigravity): graduated from backlog ackme8; fully authored plan with 5 E/V pairs covering 'aw releases' owner verb.
- 2026-08-29 draft (Antigravity): created.

## Goal

Provide a dedicated, first-class `aw releases` owner verb that brings parity to the `.aw/records/releases/` tree, enabling users and agents to list releases, inspect the active release and its blocking items, scaffold new release records, and validate release metadata.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: release query and blocker resolution primitives

- [x] E-01 In `agent_workflows/releases.py`, add release query/listing data structures and reader functions: define `ReleaseRecord` (holding `id6`, `version`, `status`, `summary`, `path`, and workflow history), implement `list_releases(repo_root: Path) -> List[ReleaseRecord]` discovering all `.release.md` records, `get_release(repo_root: Path, selector: str) -> Optional[ReleaseRecord]` resolving by id6, version, filename, or `next`, and `get_release_blockers(repo_root: Path, selector: str) -> List[dict]` which MUST REUSE the existing public `attention.release_blockers(items, repo_root)` (attention.py:582) over the attention item scan rather than re-implementing a second `- Blocks-Release:` walk. Re-implementing the scan would create a duplicate path that can drift from the board's answer (architecture rule: use existing canonical mechanisms).
  - Depends on: none
  - Expected outcome: `list_releases`, `get_release`, and `get_release_blockers` provide clean programmatic access; `get_release_blockers` returns the SAME blocker set as `aw attention` for the same release (single source of truth, no second scan). `get_release` resolves via the existing `resolve_release`/`describe_planned_release` (releases.py:134) for the `next` sentinel rather than a new resolver.
  - Execution state: performed

### Task group 2: release command runners (list, show, new, check)

- [x] E-02 In `agent_workflows/releases.py`, implement the command runners for the CLI verbs: `run_list(args)` (renders a formatted table of release records, supporting `--json` and `--agent`), `run_show(args)` (renders the full release record details along with all gating release-blocker items with status, priority, and path), `run_new(args)` (CLI wrapper around `create_release` with `--version`, `--summary`, `--status`, preview by default, `--apply` to write). No `run_check` is added (see Scope: `aw check releases` is the canonical validator).
  - Depends on: E-01
  - Expected outcome: all three release subcommands (list, show, new) are callable with standard `args`, supporting human terminal formatting, `--json`, and `--agent` JSONL modes with correct exit codes.
  - Execution state: performed

### Task group 3: CLI parser and dispatch integration

- [x] E-03 In `agent_workflows/cli.py`, register the `releases` subcommand (with alias `release`), add its subparsers (`list`, `show`, `new`, `check`), configure CLI arguments (`--version`, `--summary`, `--status`, `--apply`, selector), wire default bare `aw releases` to list releases, and route execution to `releases.run_*` handlers.
  - Depends on: E-02
  - Expected outcome: `aw releases`, `aw release`, `aw releases show next`, and `aw releases new --version ... --summary ... --apply` are fully discoverable via `aw --help` and execute cleanly.
  - Execution state: performed

### Task group 4: tab completion and doctor integration

- [x] E-04 In `agent_workflows/completion.py`, register `releases` and `release` commands in static shell completion tables for Bash, Zsh, and Fish, and implement dynamic completion in `aw __complete` for `aw releases show` resolving release id6s, versions, and `next`.
  - Depends on: E-03
  - Expected outcome: shell tab completion suggests `releases` and `release` subcommands and dynamically completes release selectors.
  - Execution state: performed

### Task group 5: documentation and test suite

- [x] E-05 Author a comprehensive test suite in `tests/test_releases_cli.py` covering all CLI subcommands (`list`, `show`, `new`, `--json`, `--agent`, error paths, and blocker resolution) and update `.aw/records/releases/README.md` and repo documentation to document the `aw releases` command family.
  - Depends on: E-03, E-04
  - Expected outcome: all new tests pass with 100% verification of CLI functionality and documentation reflects the new owner verb.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Owner verbs follow the `aw <type> [new|set|check|show|list]` pattern with aliases (e.g. `aw specs`/`spec`, `aw backlog`, `aw research`).
- CLI output contract: human-formatted colored output on TTY, `--agent` emits `aw.agent/v1` JSONL, `--json` emits full structured JSON, and exit codes are 0 (clean), 1 (findings), 2 (usage/error).
- Release records live under `.aw/records/releases/*.release.md` with `- Id:`, `- Status:`, `- Version:`, `- Summary:`.
- `Blocks-Release: <id6|next>` gates point to release records and are resolved via `releases.resolve_release`.
- Plan front-matter fields for graduation: `- From-Backlog: <id6>` pairs with `- Blocks-Release: <release>` so release-gating backlog items can safely transition to `done` via handoff.

## Findings

- `releases.py` already contains core record creation (`create_release`), validation (`validate_release`), and resolution (`resolve_release`, `describe_planned_release`, `load_active_release`), but lacked CLI entry points and owner verb commands.
- `aw attention` already aggregates release blockers, but there was no dedicated CLI verb to inspect release blockers on demand without running the full attention sweep.
- Adding `aw releases` completes owner-verb parity across all record classes (`plans`, `specs`, `backlog`, `research`, `releases`).

## Proposed changes (ordered, validatable)

1. `agent_workflows/releases.py`: add `ReleaseRecord`, `list_releases`, `get_release`, `get_release_blockers` (reusing `attention.release_blockers`), and runner functions `run_list`, `run_show`, `run_new`.
2. `agent_workflows/cli.py`: register `releases` / `release` parser, subparsers, argument definitions, and dispatch logic.
3. `agent_workflows/completion.py`: register completion schemas and dynamic resolver for release selectors.
4. `.aw/records/releases/README.md`: update documentation with CLI usage examples.
5. `tests/test_releases_cli.py`: add comprehensive test suite testing CLI subcommands, JSON/agent formatting, and blocker resolution.

## Deferred / out of scope (with reason)

- Modifying release record front-matter schema: out of scope, existing schema (`Id`, `Status`, `Version`, `Summary`) is stable and conformant.
- A `releases check` subcommand: EXCLUDED as a duplicate of the working `aw check releases` (check_engine.py:489). Validation stays single-sourced.
- Interactive release promotion workflow: out of scope, releases are ship-gate anchors; full release execution is handled by `release-review`.

## Scope check

- Over-scope: none.
- Under-scope: none; covers query primitives, CLI dispatch, tab completion, docs, and tests.

## Required tests / validation

- Unit tests for `list_releases`, `get_release`, `get_release_blockers`.
- CLI integration tests for `aw releases`, `aw releases list`, `aw releases show <id6|next>`, `aw releases new`.
- A test asserting NO `aw releases check` subcommand is registered (the canonical validator stays `aw check releases`), so the duplicate path cannot be reintroduced.
- Format tests verifying `--json` and `--agent` outputs.
- Tab completion tests for `releases` subcommands and release selectors.
- Regression tests ensuring `aw check` and `aw attention` continue to operate cleanly.

Validation command: `python3 -m pytest tests/test_releases.py tests/test_releases_cli.py -q`

## Spec / documentation sync

- Update `.aw/records/releases/README.md` to document the `aw releases` owner verb and subcommands.
- Update `AGENTS.md` or CLI help references if appropriate.

## Open questions

### OQ-01: Should bare `aw releases` default to `list` or show `show next`?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Default to `list` (matching `aw backlog` and other owner verbs), while `aw releases show` defaults to `next` when no selector is given.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Pasted `python3 -m pytest tests/test_releases.py -q` output showing named unit tests pass for: `list_releases` discovering every `.release.md` under `.aw/records/releases/` (assert the returned count equals the on-disk count from `ls .aw/records/releases/*.release.md | wc -l`); `get_release` resolving BY id6, BY version string, BY filename, and BY the `next` sentinel (4 separate assertions), and returning None for an unknown selector; and `get_release_blockers` returning EXACTLY the same id6 set as `attention.release_blockers` for the same release - assert set equality against the existing function, proving no second scan was written. ALSO paste `grep -n "attention.release_blockers\|from agent_workflows.attention import" agent_workflows/releases.py` showing the reuse is real.
  - Observed evidence: ALL FOUR required proofs run and pasted below - `pytest tests/test_releases.py` 22 passed (named tests shown); live on-disk count 1 == `list_releases` 1; the four `get_release` resolutions + the None case each a separate named test; SET EQUALITY vs `attention.release_blockers` asserted in test AND confirmed live (58 == 58, sets equal); plus the required reuse grep showing the delegating call at releases.py:346.
    `python3 -m pytest tests/test_releases.py -p no:randomly -n0 --no-header --verbosity=2` (the -q form emits only the progress line under this repo's xdist addopts, so -v is used to show the NAMED tests the evidence requires):
    ```
    ============================= test session starts ==============================
    collecting ... collected 22 items

    tests/test_releases.py::ReleasesClassTests::test_attention_release_reader PASSED [  4%]
    tests/test_releases.py::ReleasesClassTests::test_class_resolves PASSED   [  9%]
    tests/test_releases.py::ReleasesClassTests::test_create_and_validate PASSED [ 13%]
    tests/test_releases.py::ReleasesClassTests::test_deep_cleanup_includes_releases PASSED [ 18%]
    tests/test_releases.py::ReleasesClassTests::test_describe_planned_release PASSED [ 22%]
    tests/test_releases.py::ReleasesClassTests::test_facet_recognized PASSED [ 27%]
    tests/test_releases.py::ReleasesClassTests::test_load_active_release PASSED [ 31%]
    tests/test_releases.py::ReleasesClassTests::test_resolve_next PASSED     [ 36%]
    tests/test_releases.py::ReleaseQueryPrimitiveTests::test_get_release_blockers_carries_render_fields PASSED [ 40%]
    tests/test_releases.py::ReleaseQueryPrimitiveTests::test_get_release_blockers_equals_attention_release_blockers PASSED [ 45%]
    tests/test_releases.py::ReleaseQueryPrimitiveTests::test_get_release_blockers_reuse_is_wired_in_source PASSED [ 50%]
    tests/test_releases.py::ReleaseQueryPrimitiveTests::test_get_release_blockers_scoped_to_the_named_release PASSED [ 54%]
    tests/test_releases.py::ReleaseQueryPrimitiveTests::test_get_release_by_filename PASSED [ 59%]
    tests/test_releases.py::ReleaseQueryPrimitiveTests::test_get_release_by_id6 PASSED [ 63%]
    tests/test_releases.py::ReleaseQueryPrimitiveTests::test_get_release_by_next_sentinel PASSED [ 68%]
    tests/test_releases.py::ReleaseQueryPrimitiveTests::test_get_release_by_version PASSED [ 72%]
    tests/test_releases.py::ReleaseQueryPrimitiveTests::test_get_release_unknown_selector_is_none PASSED [ 77%]
    tests/test_releases.py::ReleaseQueryPrimitiveTests::test_list_releases_empty_tree PASSED [ 81%]
    tests/test_releases.py::ReleaseQueryPrimitiveTests::test_list_releases_matches_on_disk_count PASSED [ 86%]
    tests/test_releases.py::ReleaseQueryPrimitiveTests::test_parse_release_reads_prose_summary_section PASSED [ 90%]
    tests/test_releases.py::ReleaseQueryPrimitiveTests::test_parse_release_tolerates_a_malformed_record PASSED [ 95%]
    tests/test_releases.py::ReleaseQueryPrimitiveTests::test_plan_release_previews_exactly_what_create_writes PASSED [100%]

    ============================== 22 passed in 0.17s ==============================
    ```
    Mapping to the four required assertions: (1) on-disk count - `test_list_releases_matches_on_disk_count` asserts `len(list_releases(root)) == len(sorted(glob("*.release.md")))` AND that the returned path set equals the globbed set; independently confirmed against the LIVE tree:
    ```
    $ ls .aw/records/releases/*.release.md | wc -l
    1
    $ python3 -c "from pathlib import Path; from agent_workflows import releases; print('list_releases count:', len(releases.list_releases(Path('.'))))"
    list_releases count: 1
    ```
    (2) the FOUR separate `get_release` resolutions are four separate named tests - `test_get_release_by_id6`, `test_get_release_by_version`, `test_get_release_by_filename` (also asserts the bare stem), `test_get_release_by_next_sentinel` (also asserts the returned path IS `resolve_release(root,"next")`, i.e. delegation not reimplementation); the unknown-selector None case is `test_get_release_unknown_selector_is_none` (asserts None for `nosuch`, `""`, and a well-formed-but-absent id6 `zzzzzz`).
    (3) SET EQUALITY vs `attention.release_blockers` is `test_get_release_blockers_equals_attention_release_blockers` (`assertEqual` on the two sets, plus an explicit id-set assertion that the non-gating control item `free01` is excluded). Also verified against the LIVE repo, which has 58 real blockers:
    ```
    $ python3 -c "
    from pathlib import Path
    from agent_workflows import attention, releases
    root = Path('.')
    items, _ = attention.scan(root)
    a = {it.path for it in attention.release_blockers(items, root)}
    b = {d['path'] for d in releases.get_release_blockers(root, 'next')}
    print('attention:', len(a), 'verb:', len(b)); print('equal:', a == b)
    print('only-attention:', sorted(a-b)[:5]); print('only-verb:', sorted(b-a)[:5])"
    attention: 58 verb: 58
    equal: True
    only-attention: []
    only-verb: []
    ```
    (4) the reuse grep (required verbatim):
    ```
    $ grep -n "attention.release_blockers\|from agent_workflows.attention import\|from agent_workflows import attention as _attention" agent_workflows/releases.py
    7:`attention.release_blockers` rather than re-walking `- Blocks-Release:` a second time), and the three
    202:# `attention.release_blockers` (the function `aw attention` and `aw doctor` already consume), so the
    331:    REUSES `attention.scan` + `attention.release_blockers` verbatim: this function does NOT
    343:    from agent_workflows import attention as _attention
    346:    blockers = _attention.release_blockers(items, repo_root)
    378:    `attention.release_blockers` probes (repo-relative, then `.aw/records/`-relative)."""
    671:    from `attention.release_blockers`, so it is the SAME set the board shows. Exit 2 when the selector
    ```
    The import is `from agent_workflows import attention as _attention` (line 343), the repo's local-import idiom for avoiding an import cycle, rather than the `from agent_workflows.attention import` form the grep pattern also allowed; line 346 is the actual delegating call. `test_get_release_blockers_reuse_is_wired_in_source` asserts both strings are present in the source so a future refactor cannot silently reintroduce a second scan. Per-release narrowing is documented in DECISION 04-w0ln4q-D3.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted `python3 -m pytest tests/test_releases_cli.py -q` output for named tests asserting: `run_list` human output contains the planned release's id6 AND version; `run_list` with `--json` emits parseable JSON whose record count matches `list_releases`; `run_list` with `--agent` emits `aw.agent/v1` JSONL (assert the `schema` key equals `aw.agent/v1`); `run_show next` output names the release AND lists each blocker's id6 with its status; `run_new` WITHOUT `--apply` writes NO file (assert the releases dir listing is byte-identical before/after) and WITH `--apply` creates a conformant record that `aw check releases` then passes. Exit codes asserted explicitly: 0 clean, 2 on a bad selector.
  - Observed evidence: `pytest tests/test_releases_cli.py` 37 passed (named tests pasted below), covering every required assertion: id6+version in human output; `--json` record count == `list_releases`; `--agent` `schema` == `aw.agent/v1`; `show next` naming the release and each blocker's id6 + status; `new` without `--apply` leaving the releases dir BYTE-identical (content-level compare) and with `--apply` producing a record the canonical `check_engine`/`validate_release` path accepts; exit codes 0 clean and 2 on a bad selector / bad flag asserted explicitly.
    `python3 -m pytest tests/test_releases_cli.py -p no:randomly -n0 --no-header --verbosity=2` (-v rather than -q so the NAMED tests this item requires are visible):
    ```
    ============================= test session starts ==============================
    collecting ... collected 37 items

    tests/test_releases_cli.py::RunListTests::test_agent_emits_aw_agent_v1_jsonl PASSED [  2%]
    tests/test_releases_cli.py::RunListTests::test_empty_tree_is_clean_with_guidance PASSED [  5%]
    tests/test_releases_cli.py::RunListTests::test_human_output_names_id6_and_version PASSED [  8%]
    tests/test_releases_cli.py::RunListTests::test_json_record_count_matches_list_releases PASSED [ 10%]
    tests/test_releases_cli.py::RunShowTests::test_show_bad_selector_agent_mode_exits_2 PASSED [ 13%]
    tests/test_releases_cli.py::RunShowTests::test_show_bad_selector_exits_2 PASSED [ 16%]
    tests/test_releases_cli.py::RunShowTests::test_show_blockers_match_get_release_blockers PASSED [ 18%]
    tests/test_releases_cli.py::RunShowTests::test_show_defaults_to_next_when_no_selector PASSED [ 21%]
    tests/test_releases_cli.py::RunShowTests::test_show_next_names_release_and_lists_blockers PASSED [ 24%]
    tests/test_releases_cli.py::RunShowTests::test_show_renders_history PASSED [ 27%]
    tests/test_releases_cli.py::RunNewTests::test_apply_creates_a_record_that_check_releases_passes PASSED [ 29%]
    tests/test_releases_cli.py::RunNewTests::test_bad_status_exits_2_and_writes_nothing PASSED [ 32%]
    tests/test_releases_cli.py::RunNewTests::test_json_preview_reports_applied_false PASSED [ 35%]
    tests/test_releases_cli.py::RunNewTests::test_missing_summary_exits_2 PASSED [ 37%]
    tests/test_releases_cli.py::RunNewTests::test_missing_version_exits_2 PASSED [ 40%]
    tests/test_releases_cli.py::RunNewTests::test_preview_writes_nothing_and_leaves_dir_identical PASSED [ 43%]
    tests/test_releases_cli.py::ReleasesParserTests::test_bare_releases_parses_with_no_subcommand PASSED [ 45%]
    tests/test_releases_cli.py::ReleasesParserTests::test_new_flags_registered PASSED [ 48%]
    tests/test_releases_cli.py::ReleasesParserTests::test_no_releases_check_subcommand PASSED [ 51%]
    tests/test_releases_cli.py::ReleasesParserTests::test_releases_and_release_alias_registered PASSED [ 54%]
    tests/test_releases_cli.py::ReleasesParserTests::test_show_selector_is_optional PASSED [ 56%]
    tests/test_releases_cli.py::ReleasesParserTests::test_subcommands_are_exactly_list_show_new PASSED [ 59%]
    tests/test_releases_cli.py::ReleasesDispatchTests::test_bare_releases_lists PASSED [ 62%]
    tests/test_releases_cli.py::ReleasesDispatchTests::test_explicit_list PASSED [ 64%]
    tests/test_releases_cli.py::ReleasesDispatchTests::test_new_preview_via_cli_writes_nothing PASSED [ 67%]
    tests/test_releases_cli.py::ReleasesDispatchTests::test_release_alias_lists PASSED [ 70%]
    tests/test_releases_cli.py::ReleasesDispatchTests::test_show_next_via_cli PASSED [ 72%]
    tests/test_releases_cli.py::ReleasesDispatchTests::test_unknown_selector_via_cli_exits_2 PASSED [ 75%]
    tests/test_releases_cli.py::ReleasesCompletionTests::test_dunder_complete_wire_protocol PASSED [ 78%]
    tests/test_releases_cli.py::ReleasesCompletionTests::test_dynamic_show_selector_honors_the_alias PASSED [ 81%]
    tests/test_releases_cli.py::ReleasesCompletionTests::test_dynamic_show_selector_prefix_filters PASSED [ 83%]
    tests/test_releases_cli.py::ReleasesCompletionTests::test_dynamic_show_selector_resolves_id6_version_and_next PASSED [ 86%]
    tests/test_releases_cli.py::ReleasesCompletionTests::test_next_absent_when_no_single_planned_release PASSED [ 89%]
    tests/test_releases_cli.py::ReleasesCompletionTests::test_release_selector_candidates_reuses_list_releases PASSED [ 91%]
    tests/test_releases_cli.py::ReleasesCompletionTests::test_static_scripts_carry_the_subcommands PASSED [ 94%]
    tests/test_releases_cli.py::ReleasesCompletionTests::test_static_scripts_carry_the_verb PASSED [ 97%]
    tests/test_releases_cli.py::ReleasesDocsTests::test_releases_readme_documents_the_owner_verb PASSED [100%]

    ============================== 37 passed in 0.79s ==============================
    ```
    Mapping to each required assertion:
    - `run_list` human output contains the id6 AND version: `RunListTests::test_human_output_names_id6_and_version` (asserts `aaaaaa`, `2.0.0`, `planned`, and the `next -> 2.0.0 (aaaaaa)` line).
    - `--json` record count matches `list_releases`: `test_json_record_count_matches_list_releases` (`len(payload["data"]["releases"]) == len(list_releases(root))`, plus `count == 1`, the resolved `next`, and `exit_code == 0`).
    - `--agent` emits `aw.agent/v1` JSONL with `schema` equal to that value: `test_agent_emits_aw_agent_v1_jsonl` (`assertEqual(rec["schema"], "aw.agent/v1")`, plus `cmd == "releases list"` and `exit == 0`).
    - `run_show next` names the release AND lists each blocker's id6 with its status: `test_show_next_names_release_and_lists_blockers` (asserts `2.0.0`, `aaaaaa`, `release-blockers (2)`, blocker `gate01` + status `open`, blocker `gate03` + status `approved`, and that the non-gating `free01` is ABSENT). `test_show_blockers_match_get_release_blockers` additionally asserts the rendered blocker id set equals `get_release_blockers`.
    - `run_new` WITHOUT `--apply` writes NO file, asserted as a byte-identical directory listing: `test_preview_writes_nothing_and_leaves_dir_identical` compares `{name: p.read_bytes()}` for the releases dir before and after (`assertEqual`), which is a content-level, not merely name-level, identity check. The CLI-level equivalent is `ReleasesDispatchTests::test_new_preview_via_cli_writes_nothing`.
    - WITH `--apply` creates a conformant record that `aw check releases` passes: `test_apply_creates_a_record_that_check_releases_passes` asserts the file exists with the right Version/Status, that `releases.validate_release` returns [] (the exact function `aw check releases` calls), and that `check_engine.check_type(root, "releases")` reports no drift for it - i.e. the canonical validator path, not a restatement.
    - exit codes explicitly: 0 clean is asserted in every success test; 2 on a bad selector in `test_show_bad_selector_exits_2` (human, message on stderr) and `test_show_bad_selector_agent_mode_exits_2` (agent mode, `exit == 2` and `kind == "error"`); 2 on missing/invalid flags in `test_missing_version_exits_2`, `test_missing_summary_exits_2`, and `test_bad_status_exits_2_and_writes_nothing` (which also asserts nothing was written).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted terminal output of each real invocation: `aw releases` (bare, defaults to list), `aw release` (alias), `aw releases list`, `aw releases show next`, and `aw releases new --version 9.9.9 --summary "probe"` (preview, no `--apply`) - each exiting 0 with the expected content. PLUS `aw releases --help` showing exactly the subcommands `list`, `show`, `new` and NOT `check`. PLUS the adversarial assertion: `aw releases check` MUST fail as an unknown subcommand (paste the nonzero exit / usage error), proving the duplicate validator was not reintroduced.
  - Observed evidence: Every required invocation run and pasted below with its exit code - bare `releases` (lists), the `release` alias, `releases list`, `releases show next`, and `releases new --version 9.9.9 --summary probe` (preview; dir unchanged) all EXIT=0; `releases --help` shows exactly {list,show,new} and no `check`; and the ADVERSARIAL check passes - `releases check` fails as an invalid choice (EXIT=2) while `check releases` still CONFORMS (EXIT=0). Run via `python3 -m agent_workflows` because the lane's `aw` shim loads the main checkout (known defect af7i6p); rationale below.
    NOTE ON THE ENTRY POINT: these were run as `python3 -m agent_workflows <args>`, not the `aw` console script. In this lane worktree the installed `aw` shim resolves `agent_workflows` to the MAIN checkout (`<main-checkout>/agent_workflows/__init__.py`, i.e. the repo root rather than this lane worktree), so `aw releases` there exits 2 with "invalid choice: 'releases'" - it is executing code that does not contain this change. That is the known nested-`aw`-in-a-lane defect already tracked by pending plan `af7i6p` ("make a nested aw in a lane run the driver's own tooling"), NOT a defect in this work. `agent_workflows/__main__.py` calls the identical `cli.main`, and `python3 -c "import agent_workflows; print(agent_workflows.__file__)"` confirms it loads this worktree's source, so `python3 -m agent_workflows` is the faithful invocation of the code under test.
    ```
    $ python3 -m agent_workflows releases          # bare, defaults to list
    ID      STATUS   VERSION  SUMMARY
    f33nrj  planned  2.0.0    First release since v1.3.0-rc.1, gating the breaking `.aw/`

    next -> 2.0.0 (f33nrj)
    EXIT=0

    $ python3 -m agent_workflows release           # the alias
    ID      STATUS   VERSION  SUMMARY
    f33nrj  planned  2.0.0    First release since v1.3.0-rc.1, gating the breaking `.aw/`

    next -> 2.0.0 (f33nrj)
    EXIT=0

    $ python3 -m agent_workflows releases list
    ID      STATUS   VERSION  SUMMARY
    f33nrj  planned  2.0.0    First release since v1.3.0-rc.1, gating the breaking `.aw/`

    next -> 2.0.0 (f33nrj)
    EXIT=0

    $ python3 -m agent_workflows releases show next | head -12
    release 2.0.0 (f33nrj)
      Status:  planned
      Version: 2.0.0
      Id:      f33nrj
      Path:    .aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md
      Summary: First release since v1.3.0-rc.1, gating the breaking `.aw/` namespace migration (`.agents/` -> `.aw/`) and the `awcmdsurf` command-surface hard cutover, plus the pre-release UX batch. Because nothing has shipped since before the `.aw/` migration, this is a major (2.0.0) release. The concrete version is stamped at release time under the RELEASING.md Section 9 human GO gate; this record is the ship-gate anchor that `Blocks-Release: next` resolves against.

    release-blockers (58)
    ID      TREE     STATUS     PRIORITY  PATH
    kjzlgw  backlog  graduated  high      .aw/records/backlog/graduated/20260827-runnerstop-01-kjzlgw-graceful-quit-protocol-for-aw-oc-agy-run-4-stop-le.backlog.md
    dhuape  backlog  graduated  medium    .aw/records/backlog/graduated/20260828-dhuape-01-dhuape-unify-runners.backlog.md
    i97baj  backlog  graduated  high      .aw/records/backlog/graduated/20260828-promptmint-01-i97baj-aw-verb-to-mint-prompts-staging-file.backlog.md
    EXIT=0
    (truncated by `head -12`; the full listing renders all 58 blockers, matching the set-equality check in V-01)

    $ python3 -m agent_workflows releases new --version 9.9.9 --summary "probe"   # PREVIEW, no --apply
    --- would write <lane-worktree>/.aw/records/releases/20260830-qwmcv4-01-qwmcv4-9-9-9.release.md ---
    # Release: 9.9.9

    - Id: qwmcv4
    - Status: planned
    - Version: 9.9.9
    - Summary: probe

    ## Workflow history

    - 2026-08-30 created (aw releases): probe
    EXIT=0
    $ ls .aw/records/releases/
    20260820-f33nrj-01-f33nrj-2-0-0.release.md
    README.md
    (the preview wrote nothing: only the pre-existing record and README remain. The absolute path the command really printed is abbreviated to `<lane-worktree>` here to satisfy the repo's leak sanitizer, which rejects home-style paths in tracked files; nothing else in the output is altered.)
    ```
    `--help` showing EXACTLY list/show/new and NOT check:
    ```
    $ python3 -m agent_workflows releases --help
    usage: agent-workflows releases [-h] [--no-color] [--agent] [--json] [--dir DIR]
                                    {list,show,new} ...

    Owner verbs for the release records in .aw/records/releases/ (the ship-gate anchors that 'Blocks-Release: <id6|next>' resolves against): 'list' tabulates every release record, 'show' details one release plus the LIVE items gating it (the same blocker set 'aw attention' reports), and 'new' scaffolds a conformant record (preview by default). Validate release records with 'aw check releases'.

    positional arguments:
      {list,show,new}
        list           List every release record (the default for a bare 'aw
                       releases').
        new            Create a release record (dry-run by default; --apply to
                       write).
        show           Show one release + its release-blockers (selector defaults to
                       'next').

    options:
      -h, --help       show this help message and exit
      --no-color       Disable ANSI color (also honored via NO_COLOR).
      --agent          Machine-readable output (aw.agent/v1 JSONL).
      --json           Emit full structured JSON representation.
      --dir DIR        Repo root (default: current directory).

    EXAMPLES
      aw releases                  # list every release record (default)
      aw releases show next        # the planned release + everything gating it
      aw releases new --version 2.1.0 --summary "why" --apply

    SAFETY & DEFAULTS
      'new' is dry-run by default; pass --apply to write.
      Bare 'aw releases' lists; 'show' defaults to the 'next' (single planned) release.
      Validation lives in 'aw check releases' - there is no 'releases check'.

    OUTPUT & EXITS
      Exit codes: 0 clean, 2 cannot-run/usage error (e.g. an unresolvable selector).
      Agent mode: --agent or non-TTY piped emits aw.agent/v1 JSONL.
    EXIT=0
    ```
    THE ADVERSARIAL ASSERTION - `releases check` must be an unknown subcommand, and the canonical validator must still work:
    ```
    $ python3 -m agent_workflows releases check
    usage: agent-workflows releases [-h] [--no-color] [--agent] [--json] [--dir DIR]
                                    {list,show,new} ...
    agent-workflows releases: error: argument releases_command: invalid choice: 'check' (choose from 'list', 'show', 'new')
    Next  aw releases --help
    EXIT=2

    $ python3 -m agent_workflows check releases
    AW check  releases                                                         43 ms
    CONFORMS  1 releases checked

    Evidence
      checked  1
      errors  0   warnings  0
    EXIT=0
    ```
    The duplicate validator was NOT reintroduced: `aw releases check` fails as an unknown subcommand (exit 2) while `aw check releases` remains the single working validator (exit 0). `ReleasesParserTests::test_no_releases_check_subcommand` locks this in three ways - `check` is absent from the subparser choices, `parse_args(["releases","check"])` raises SystemExit(2), and `releases` has no `run_check` attribute at all. An unresolvable SELECTOR (as opposed to subcommand) also exits 2: `python3 -m agent_workflows releases show nosuchthing` printed "aw releases show: 'nosuchthing' does not resolve to a release record (try an id6, a version, a filename, or 'next')" with EXIT=2.
    Also note the `--dir` placement fix recorded in DECISION 04-w0ln4q-D2: because bare `aw releases` is a real leaf (OQ-01), `--dir` is declared on the family parser and the subparsers use `argparse.SUPPRESS`, so both `aw releases --dir X` and `aw releases list --dir X` resolve the same root.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted `aw completion bash | grep -c releases` (nonzero) and the same for zsh and fish, showing all three generated scripts carry the verb. PLUS pasted dynamic completion output proving real resolution, not a static list: `aw __complete --cword 3 -- aw releases show` MUST emit the actual planned release id6 (`f33nrj`) and the `next` sentinel - assert those exact tokens appear. PLUS a test in `tests/test_completion.py` asserting the same, so a future refactor cannot silently drop it.
  - Observed evidence: All three generated scripts carry the verb (bash 3, zsh 2, fish 12 - nonzero, pasted below); `__complete --cword 3 -- aw releases show` emits the exact required tokens `f33nrj` and `next` (plus the version `2.0.0`) against the live repo, and the alias resolves identically; and two new tests in `tests/test_completion.py` (`test_release_selector_id6_version_and_next`, `test_release_selector_prefix_filters`) lock it against a controlled fixture so a refactor cannot drop it.
    Generated-script grep counts (all three nonzero), via `python3 -m agent_workflows` for the entry-point reason given in V-03:
    ```
    $ python3 -m agent_workflows completion bash | grep -c releases
    3
    $ python3 -m agent_workflows completion zsh | grep -c releases
    2
    $ python3 -m agent_workflows completion fish | grep -c releases
    12
    ```
    Dynamic resolution against the LIVE repo, proving real resolution rather than a static list - the required tokens `f33nrj` (the actual planned release id6) and `next` both appear, alongside the record's Version:
    ```
    $ python3 -m agent_workflows __complete --cword 3 -- aw releases show
    2.0.0
    f33nrj
    next
    EXIT=0
    $ python3 -m agent_workflows __complete --cword 3 -- aw release show     # the alias resolves identically
    2.0.0
    f33nrj
    next
    ```
    That these are RESOLVED, not hardcoded, is further evidenced by `ReleasesCompletionTests::test_next_absent_when_no_single_planned_release`: flipping the only planned release to `shipped` in a temp repo makes `next` STOP being offered while the id6 is still offered - a static list could not do that.
    A test in `tests/test_completion.py` asserting the same, so a future refactor cannot silently drop it (the item's third requirement):
    ```
    $ python3 -m pytest tests/test_completion.py -p no:randomly -n0 --no-header --verbosity=2 2>&1 | grep -E "release_selector|passed"
    tests/test_completion.py::CompleteQueryArtifactTests::test_release_selector_id6_version_and_next PASSED [ 29%]
    tests/test_completion.py::CompleteQueryArtifactTests::test_release_selector_prefix_filters PASSED [ 30%]
    ================= 79 passed, 2 skipped, 1 deselected in 4.68s ==================
    ```
    Those two tests live in the shared `_DynamicRepoFixture` (a controlled temp repo, never the live tree), whose fixture now seeds one planned release `rel111`/`7.0.0`; they assert the id6, the version, and `next` are all offered, that the `release` alias returns an identical candidate set, and that a `rel` prefix narrows to exactly `["rel111"]`.
    SCOPE NOTE (DECISION 04-w0ln4q-D4): E-04 also says to "register `releases` and `release` in static shell completion tables". No change was needed there and none was made: `completion.introspect_cli_tree` derives all three generators' command lists from the REAL argparse tree, so registering the verb in E-03 made it appear in every generated script automatically (hence the nonzero counts above, with zero edits to the generators). Adding a hardcoded per-shell table would have duplicated the introspected tree - the same anti-duplication rule this plan applies to `releases check`. `ReleasesCompletionTests::test_static_scripts_carry_the_verb` and `test_static_scripts_carry_the_subcommands` assert the generated scripts and the introspected tree carry `releases` with exactly `{list, show, new}`. The only genuinely new completion code is `completion.release_selector_candidates` plus one `complete_query` branch, and that function sources its candidates from `releases.list_releases` - the same reader the verb uses - so completion can never offer a token the verb would reject.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Pasted `python3 -m pytest tests/test_releases.py tests/test_releases_cli.py -q` summary line AND a full default-suite run `python3 -m pytest -p no:randomly` summary line, both green with the counts shown (a bare "all tests passing" claim is NOT acceptable evidence). PLUS pasted `grep -n "aw releases" .aw/records/releases/README.md` showing the documented usage, and `aw check releases` still exiting 0 (regression: the new verb did not break the canonical validator). Any V-item whose command was not actually run stays `pending`.
  - Observed evidence: `tests/test_releases.py tests/test_releases_cli.py` -> 59 passed. Full suite is NOT all-green and the honest reason is measured, not asserted: a PRISTINE clone at the base HEAD d4d265b gives `15 failed, 2912 passed` and this tree gives `15 failed, 2965 passed`, with a byte-identical FAILED set (diff empty) - so +53 tests, ZERO new failures, all 15 pre-existing and all in the unrelated `tests/test_run_viewer.py`. Plus the README `aw releases` grep, `check releases` still EXIT=0, and both enforced pre-commit hooks (ruff, ruff-format) Passed on the six changed files. One known gap reported below, not hidden.
    The two suites this plan owns (summary line, with counts):
    ```
    $ python3 -m pytest tests/test_releases.py tests/test_releases_cli.py -p no:randomly -n0 --no-header
    ...........................................................              [100%]
    59 passed in 1.47s
    ```
    The full default suite. THIS IS NOT ALL-GREEN, and the honest reason is stated rather than hidden (see DECISION 04-w0ln4q-D5): the suite carries 15 PRE-EXISTING failures at this plan's base commit, all in `tests/test_run_viewer.py`, which is unrelated to releases and outside this plan's Scope-Paths. To prove those are not mine, the baseline was measured on a PRISTINE clone checked out at the exact base HEAD `d4d265b67a12e89893ff77b7ff093b0abd5a45f9` (from the begin receipt), with no changes from this plan applied:
    ```
    $ cd /tmp/opencode/baseclone && git log --oneline -1
    d4d265b plan-review: harden ng2blv (second pass, revisions applied)
    $ python3 -m pytest -p no:randomly            # BASELINE, no w0ln4q changes
    15 failed, 2912 passed, 3 skipped, 4 xfailed in 29.35s

    $ cd <this worktree> && python3 -m pytest -p no:randomly     # AFTER all w0ln4q changes
    15 failed, 2965 passed, 3 skipped, 4 xfailed in 26.67s

    $ diff <(grep -E "^FAILED" baseline.txt | sort) <(grep -E "^FAILED" final.txt | sort) && echo "(EMPTY - identical failure set)"
    (EMPTY - identical failure set)
    ```
    So: passed rose 2912 -> 2965 (+53, this plan's new tests), and the failure SET is byte-identical (same 15 `tests/test_run_viewer.py::RunViewerTests::*` items) - zero new failures, zero newly-broken tests. All 15 pre-existing failures are listed identically in both runs; none is in a file this plan touched.
    Documentation grep (required verbatim):
    ```
    $ grep -n "aw releases" .aw/records/releases/README.md
    13:## The `aw releases` owner verb
    18:aw releases                     # list every release record (bare = list)
    19:aw releases list                # the same, explicitly
    20:aw releases show                # the planned release + everything gating it (defaults to 'next')
    21:aw releases show f33nrj         # a specific release, by id6, version, or filename
    22:aw releases new --version 2.1.0 --summary "why this release exists"          # preview only
    23:aw releases new --version 2.1.0 --summary "why this release exists" --apply  # write it
    26:`aw releases show` lists the LIVE items declaring `Blocks-Release` against that release. That blocker
    ```
    The README also states that validation is `aw check releases` and that there is deliberately no `releases check`; `ReleasesDocsTests::test_releases_readme_documents_the_owner_verb` asserts the documented commands are present, that `aw check releases` is named, and that the string `aw releases check` does NOT appear, so the docs cannot drift into advertising the excluded duplicate.
    Regression - the canonical validator still exits 0 (pasted in full in V-03):
    ```
    $ python3 -m agent_workflows check releases
    CONFORMS  1 releases checked
    EXIT=0
    ```
    Enforced pre-commit hooks on exactly the changed files (the repo enforces ruff lint + ruff-format at the pinned v0.4.4, not a type checker):
    ```
    $ pre-commit run ruff --files agent_workflows/releases.py agent_workflows/cli.py agent_workflows/completion.py tests/test_releases.py tests/test_releases_cli.py tests/test_completion.py
    ruff.....................................................................Passed
    $ pre-commit run ruff-format --files <same six files>
    ruff-format..............................................................Passed
    ```
    KNOWN GAP, reported not hidden: `find_undeclared_leaves` reports this plan's 6 new parser leaves (`releases|release` x `list|show|new`) as undeclared in `command_surface.COMMAND_INVENTORY`, joining 59 leaves that were ALREADY undeclared at the base commit (`completion`, `commit`, `runs`, `spec new`, `test`, `finish`, and the whole `oc`/`agy`/`conf`/`config` families). `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` and two `tests/test_cli_conformance_matrix.py` guards are therefore red for that systemic reason - they are `slow`-marked and so excluded from the default suite above, and they were red before this plan. `agent_workflows/command_surface.py` is NOT in this plan's Scope-Paths, so the scope fence forbade editing it; this is flagged for maintainer follow-up in DECISION 04-w0ln4q-D5 rather than silently absorbed.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (add the missing `releases` owner verb); E-items are ordered sub-steps of that single deliverable (primitives -> runners -> CLI wiring -> completion -> docs/tests).

Execution contract:

1. Open questions: OQ-01 resolved; execution requires explicit human approval.
2. Scope fence: touch ONLY the declared Scope-Paths. Do NOT add a `releases check` subcommand (`aw check releases` is the canonical validator, check_engine.py:489) and do NOT re-implement the blocker scan (reuse `attention.release_blockers`, attention.py:582). If the work seems to need more, STOP and report.
3. Honesty rule (HARD MUST): every V-item's Observed evidence is the ACTUAL pasted stdout/exit code of the named command. "All tests passing", "verified", or a summarized result is NOT evidence; a V-item whose command was not run stays `Result: pending`.
4. Reuse rule: prefer extending the existing surfaces (`resolve_release`, `describe_planned_release`, `validate_release`, `attention.release_blockers`, the existing `completion.py` tables and `__complete`) over new parallel implementations. A second path that answers the same question as the board is a defect, not a feature.
5. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push; never `--no-verify`.
6. Lifecycle move on completion: verify all V items with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed.
