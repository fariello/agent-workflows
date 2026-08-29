# IPD: Dynamic contextual artifact resolver and argcomplete soft-import for aw tab-completion

- Date: 2026-08-28
- Kind: child
- Concern: Static completion can suggest subcommands and flags, but cannot complete dynamic repository artifacts such as Set IDs (e.g. `tabcomp`, `xprio`, `reslife`), plan IDs (`id6`), spec IDs, backlog IDs, run IDs, or status keywords based on the current repository state.
- Scope: Implement dynamic contextual artifact completion and argcomplete ecosystem support: (1) Add `complete_query(words, cword, repo_root)` and artifact completers to `agent_workflows/completion.py`; (2) Wire hidden `aw __complete` subparser in `agent_workflows/cli.py` to handle shell query callbacks; (3) Add `# PYTHON_ARGCOMPLETE_OK` header and soft-imported `argcomplete.autocomplete(parser)` with custom completers in `agent_workflows/cli.py`; (4) Add comprehensive unit tests in `tests/test_completion.py`.
- Scope-Paths: agent_workflows/completion.py, agent_workflows/cli.py, tests/test_completion.py
- Item-Dependencies: executed:bja8og
- Status: approved
- Set: tabcomp
- Order: 2
- Highest E allocated: 04
- Author: Antigravity
- Id: 4f1j25
- Approval: 2026-08-28, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-28 approved (aw set): status set to approved

- 2026-08-28 reviewed (OpenCode/its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007. Verified against the real APIs and corrected four evidence-backed correctness gaps: `resolve_selectors` returns `Path` objects + needs a `record_type` (id6-extraction now specified in E-01); run/Set IDs are not selector record types (real sources named); `aw ipd set` status is free-form `nargs="+"` not argparse `choices` (per-type status now sourced from `ipd_schema`); and the <50ms budget was contradicted by a measured ~458ms unscoped plans scan (scan-scoping + a latency test now required). Corrected E-03 argcomplete scope to the generated console-script-wrapper reality, specified the `aw __complete --cword N --` wire protocol (E-02), and fixed the factually wrong test expectations.
- 2026-08-28 to-review (Antigravity): authored detailed atomic implementation plan for dynamic artifact resolution and argcomplete integration.
- 2026-08-28 draft (Antigravity): scaffolded skeleton.

## Goal

Enable high-speed (<50ms) dynamic completion of active Set IDs, plan IDs, spec IDs, backlog IDs, run IDs, and status keywords via `aw __complete`, and enable automatic global Python argcomplete support without adding any mandatory runtime dependencies.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Dynamic Artifact Query Engine (`agent_workflows/completion.py`)

- [x] E-01 Implement `complete_query(words: list[str], cword: int, repo_root: Optional[Path] = None) -> list[str]` in `agent_workflows/completion.py` that parses the input token stream and returns matching completion candidates: subcommands and flags in command position; Set IDs and run IDs when completing `aw run`/`aw runs`; plan, spec, or backlog `id6` handles when completing entity commands (`aw ipd`, `aw specs`, `aw backlog`, `aw find`); and status enum tokens when completing status arguments. This function MUST bridge the gap between the reused resolvers and completion output, which are NOT the same shape (verified):
    - `selectors.resolve_selectors(repo_root, record_type, tokens)` requires a `record_type` (`plans`/`specs`/`backlog`/`research`) and returns `pathlib.Path` objects, NOT bare `id6` tokens. `complete_query` MUST map each entity command to its `record_type` and EXTRACT the `id6` from each returned path stem (via `artifact_core.iter_id6_in_text`/the naming grammar), then prefix-match, so e.g. `complete_query(["aw","ipd","lint","b"],3)` yields `["bja8og"]` rather than a full filename.
    - Run IDs and Set IDs are NOT `selectors` record types. Run IDs live under `.aw/records/runs/` (enumerate that directory), and Set IDs are the `- Set:` front-matter value of plans (derive from `plans_index`/plan front matter). Name these real sources; do not route them through `resolve_selectors`.
    - Status vocabularies are NOT argparse `choices` on the target commands (verified: `aw ipd set` takes `args` as `nargs="+"` = `<status> <selector...>`, with no `choices`). Source the status tokens from `agent_workflows.ipd_schema` (the plan status set `draft/to-review/reviewed/approved/auto-approved/reusable`) and the per-type spec/backlog status sets, and COMPLETE ONLY the statuses valid for the artifact type in context (plan vs. spec vs. backlog differ). Do not hardcode a single global list.
  - Depends on: none
  - Expected outcome: `complete_query` returns precise, prefix-matching bare tokens (subcommands, `id6` handles, run IDs, Set IDs, status enums) evaluated against the active repository state, reusing `agent_workflows.selectors`, `agent_workflows.plans_index`, `agent_workflows.artifact_core`, and `agent_workflows.ipd_schema`, and meeting the <50ms budget under the scan-scoping in the Project conventions section.
  - Done note: Implemented `complete_query(words, cword, repo_root=None)` + the artifact completers (`plan_id6_candidates`, `set_id_candidates`, `run_id_candidates`, `entity_id6_candidates`, `status_candidates`) and the context routers (`_entity_record_type`, `_is_status_position`, `_subcommand_candidates`) in `agent_workflows/completion.py`. Bridges the verified shape mismatches: id6 is EXTRACTED from each artifact path via the naming grammar (`artifact_naming.parse_clustered`/`parse_uniform_permissive` group `id6`, NOT a stem substring scan that would catch incidental 6-char words like `wizard`); run ids are enumerated straight from `.aw/records/runs/`; Set ids from plan `- Set:` front matter via `plans_index.scan_plans`; status vocab from the real single-source modules per artifact type (`ipd_schema.RECOGNIZED_STATUS` for plans, `attention_contract.SPEC_STATUSES` for specs, `backlog.STATUSES` for backlog) - NOT a hardcoded global and NOT argparse `choices`. LATENCY: scans are scoped to ACTIVE dispositions (`pending`+`reusable` plans) and status/id6/run positions return a PURE dynamic answer (skip the parser build), so measured queries are ~1-11ms for artifact/status positions (~28-42ms for the subcommand path, dominated by the inherent parser build), all within the <50ms budget vs the ~500ms unscoped resolver sweep. Fails soft (any lookup error -> []).
  - Execution state: performed

### Task group 2: CLI Query Hook and argcomplete Integration (`agent_workflows/cli.py`)

- [x] E-02 Register the hidden `__complete` subcommand in `agent_workflows/cli.py` (help `argparse.SUPPRESS` so it stays out of `--help` and out of child 01's own completion output) that accepts the current command tokens and a cursor index and prints newline-delimited candidates from `complete_query` to stdout. Define the exact wire protocol child 01's shell scripts use: the token list is passed after a literal `--` separator (`aw __complete --cword <N> -- <tok0> <tok1> ...`) so option-like tokens are not mis-parsed as flags; `<N>` is the index of the word being completed; empty output means no candidates; exit 0 always (a completion query never errors the shell). This protocol MUST match what child 01's generated bash/zsh/fish scripts invoke.
  - Depends on: E-01
  - Expected outcome: `aw __complete --cword 1 -- aw ru` outputs `run`/`runs`/`research`-style matches, one per line, exit 0, and the token/cword protocol is exactly the one child 01's scripts call.
  - Done note: Registered `p_dunder_complete = sub.add_parser("__complete", help=argparse.SUPPRESS)` with `--cword <int>` and `words nargs=argparse.REMAINDER` in `_build_parser`; `help=argparse.SUPPRESS` keeps it out of `--help` AND out of child-01 static completion output (verified: `introspect_cli_tree._visible_subcommands` drops SUPPRESS-help leaves). Added `_run_dunder_complete(args)` (strips the leading `--` that REMAINDER retains, calls `complete_query(words, cword, repo_root=Path.cwd())`, prints newline-delimited candidates, ALWAYS returns 0, never raises) and wired `if args.command == "__complete": return _run_dunder_complete(args)` in `_dispatch`. The `--` + REMAINDER shape means a leading option-like token in the completed line is DATA, not a flag of `__complete`. Verified live: `__complete --cword 1 -- aw ru` -> `run`/`runs` (rc 0); `--cword 3 -- aw ipd lint 4` -> `4f1j25`; `--cword 2 -- aw ipd --js` -> `--json`; no match -> empty + rc 0. A CLI test asserts the output EQUALS `complete_query` for the same input, pinning the protocol.
  - Execution state: performed

- [x] E-03 Add the `# PYTHON_ARGCOMPLETE_OK` marker as a real top-of-file comment within the first 1024 bytes of `agent_workflows/cli.py` (the module docstring occupies ~700 of those bytes, verified; the marker must be a `#` comment, not text inside the docstring), and implement a soft-imported `argcomplete.autocomplete(parser)` hook (called in `main`/`_dispatch` before `parse_args`) with custom completer callables (delegating to `complete_query`/`E-01`) attached to artifact and Set arguments. HONEST SCOPE (verified limitation): argcomplete's global-completion scan reads the marker from the SCRIPT the shell invokes. The `aw`/`agentwf`/`agent-workflows` entrypoints are pip/hatchling-GENERATED console-script wrappers (`pyproject.toml:54-57`) that do NOT contain this marker, so global `activate-global-python-argcomplete` will not auto-discover them from `cli.py` alone. State explicitly which invocation argcomplete supports (e.g. `python -m agent_workflows` / a marker-bearing wrapper, or per-command `register-python-argcomplete aw`) and record that the PRIMARY completion path for `aw`/`agentwf`/`agent-workflows` is the child-01 native scripts calling `aw __complete` (E-02); argcomplete is a best-effort optional enhancement for environments that use it, NOT the main mechanism.
  - Depends on: E-01, E-02
  - Expected outcome: If `argcomplete` is installed, the hook is exercised without error for the supported invocation named above; if absent, the import is caught with zero errors and normal execution proceeds. The plan does not claim global auto-discovery of the generated console-script aliases via the `cli.py` marker.
  - Done note: Added `# PYTHON_ARGCOMPLETE_OK` as a real `#` comment immediately AFTER the module docstring (measured byte offset 719, well within 1024; the docstring closes at byte 717), followed by an honest-scope comment: the marker covers `python -m agent_workflows`/marker-bearing/`register-python-argcomplete` invocations only, NOT the pip/hatchling-generated console-script aliases, and the PRIMARY path is the child-01 scripts calling `aw __complete`. Added `_maybe_argcomplete(parser)` (soft `import argcomplete` in a try/except; on ImportError returns silently -> zero new runtime dependency), which attaches `_argcomplete_completer` (reconstructs the line from `$COMP_LINE` and delegates to `complete_query`) to the free-form positionals via `_attach_argcomplete_completers`, then calls `argcomplete.autocomplete(parser)`; the whole hook is wrapped so an optional-enhancement failure never breaks the real CLI. Called from `_dispatch` right after `parser = _build_parser()`, before `parse_args`. Verified: `argcomplete` is NOT installed on this runner (`importlib.util.find_spec('argcomplete') is None`), and `cli` imports + `main([...])` runs cleanly (the soft-import path IS the exercised path); a test also simulates the ImportError explicitly. The plan does NOT claim global auto-discovery of the generated aliases.
  - Execution state: performed

### Task group 3: Testing and Validation (`tests/test_completion.py`)

- [x] E-04 Implement unit tests in `tests/test_completion.py` (stdlib `unittest`, using a temp-repo fixture with a few pending plans/specs/backlog items of known id6/status, per the `tests/test_cli_help_and_errors.py` convention) testing `complete_query` for: subcommands and flags; Set IDs and run IDs (from their real sources, not `resolve_selectors`); plan/spec/backlog `id6` handles returned as BARE tokens (not paths); per-type status keywords sourced from `ipd_schema` (assert plan-status completion differs from spec/backlog where they differ); the `aw __complete --cword N -- ...` CLI protocol matching `complete_query`; a LATENCY assertion that a representative query over the temp repo completes within the <50ms budget (or a documented, generous CI-safe bound) using the scan-scoping from Project conventions; and `argcomplete` soft-import resilience proving `cli.py` imports and `main` runs with `argcomplete` absent.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: All dynamic query, protocol, latency, and argcomplete test cases pass with 100% assertions satisfied under `pytest tests/test_completion.py`.
  - Done note: Added the tabcomp-02 test classes to `tests/test_completion.py` on a `_DynamicRepoFixture` (a temp repo with KNOWN artifacts: two pending plans id6 `4f1j25`/`bja8og` in Set `tabcomp`, one EXECUTED plan `ffffff` that must be excluded by scoping, a spec `abc123`, a backlog item `def456`, and a run dir) per the tests/test_selectors.py fixture convention: CompleteQuerySubcommandTests (subcommand + flag prefixes), CompleteQueryArtifactTests (plan/spec/backlog id6 as BARE tokens not paths; `ffffff` excluded proving active-disposition scoping; Set id from front matter; run id from the runs dir), CompleteQueryStatusTests (plan statuses from `ipd_schema`; spec statuses DIFFER from plan; backlog status set), CompleteQueryLatencyTests (best-of-3 under a generous 250ms CI-safe bound, catching the ~500ms unscoped-sweep regression), DunderCompleteProtocolTests (the `aw __complete --cword N -- ...` CLI output EQUALS `complete_query`, exit 0, leading-dash-is-data, empty->exit 0), ArgcompleteSoftImportTests (marker is a real comment < 1024 bytes AFTER the docstring; `main` runs with argcomplete simulated-absent; `_maybe_argcomplete` is a no-op when absent). Result: `35 passed, 2 skipped` (the 2 skips are the child-01 zsh/fish shell-syntax checks, absent on this runner).
  - Execution state: performed

## Project conventions discovered (Step 0)

- Fast Latency (<50ms): Tab-completion queries run interactively on keypress. MEASURED RISK (verified during review): `resolve_selectors(repo_root, 'plans', ['b'])` on this repo took ~458ms because it scans ALL plan dispositions, including 341 files in `executed/`; a full unscoped scan blows the <50ms budget by ~10x. To meet the budget, `complete_query` MUST scope its scans to the artifacts a user actually completes against - primarily `pending/` (and `reusable/`) plans, active specs/backlog - and EXCLUDE terminal dispositions (`executed/`, `superseded/`, `not-executed/`) and the full runs history unless explicitly in context; cap result counts; and prefer `plans_index`/directory-scoped scans over the broad resolver where the resolver would sweep terminal dirs. `scan_plans(pending)` measured ~6ms, which is within budget.
- Artifact Authorities: Re-use `agent_workflows.selectors`, `agent_workflows.plans_index`, `agent_workflows.artifact_core`, and `agent_workflows.ipd_schema` for entity/status lookups rather than reimplementing ad-hoc filesystem scans - but note the shape mismatch called out in E-01: `resolve_selectors` returns `Path` objects and requires a `record_type`, and status sets come from `ipd_schema`, not from argparse `choices`.
- Zero Hard Dependency on argcomplete: Must use `try: import argcomplete ... except ImportError: pass` so the shipped package needs no new runtime dependency (D46 is dependency MINIMIZATION, not a hard prohibition; the stdlib path suffices and `argcomplete` is an optional enhancement only).

## Findings

- Wiring the shell generator from Child 01 (`bja8og`) to query `aw __complete` for positionals provides real-time contextual completion directly from git/repo state without complex shell scripting. This `__complete` protocol is the PRIMARY completion path for the `aw`/`agentwf`/`agent-workflows` aliases; argcomplete (E-03) is a secondary, optional enhancement.
- Python `argcomplete` uses `PYTHON_ARGCOMPLETE_OK` in the first 1024 bytes of the invoked script. VERIFIED CAVEAT: the shell invokes pip/hatchling-generated console-script wrappers (`pyproject.toml:54-57`), not `cli.py`; the marker in `cli.py` covers `python -m` / marker-bearing invocations only, so E-03 is scoped accordingly and does not claim global auto-discovery of the aliases.
- REUSE SHAPE MISMATCH (verified): `selectors.resolve_selectors(repo_root, record_type, tokens) -> List[Path]` requires a `record_type` and returns paths; run IDs/Set IDs are not `selectors` record types; and `aw ipd set` status is free-form `nargs="+"`, not argparse `choices`. `complete_query` (E-01) bridges these: id6-extraction from path stems, real sources for run/Set IDs, and `ipd_schema` per-type status vocabularies.
- LATENCY (verified): an unscoped `resolve_selectors(...,'plans',['b'])` measured ~458ms on this repo (341 executed plans) vs. the <50ms budget; `scan_plans(pending)` measured ~6ms. E-01 must scope scans to active dispositions and cap results to stay within budget.

## Proposed changes (ordered, validatable)

1. `agent_workflows/completion.py`: Implement `complete_query` and helper completer functions.
2. `agent_workflows/cli.py`: Register `__complete` command, add `# PYTHON_ARGCOMPLETE_OK`, and wire soft `argcomplete` hook.
3. `tests/test_completion.py`: Add unit tests for dynamic query resolution across all artifact types and argcomplete compatibility.

## Deferred / out of scope (with reason)

- Shell completion script generation: Delivered in Child 01 (`tabcomp-01`).
- Drop-in filesystem installation and install wizard integration: Handled in Child 03 (`tabcomp-03`).

## Scope check

- Over-scope: none.
- Under-scope (addressed in this review): the original E-items assumed `resolve_selectors` returned bare id6 tokens, treated run/Set IDs as selector record types, and derived status enums from argparse `choices` - none of which hold (verified). E-01 now specifies id6 extraction, real run/Set-ID sources, and `ipd_schema`-sourced per-type status sets; the <50ms budget now has an explicit scan-scoping requirement and a test; and E-03 argcomplete scope is corrected to the console-script-wrapper reality.
- Right-sizing (reviewer): E-01 carries the most conceptual weight (query engine spanning several artifact kinds); it remains one cohesive concern (one function, one `completion.py` addition, one V-item) rather than a split, because the per-kind branches share the same token-parse/prefix-match core. E-02/E-03/E-04 are each single-concern.

## Required tests / validation

- `tests/test_completion.py` (run against a controlled temp-repo fixture, not the live repo, so expected IDs/statuses are stable):
  - Test `complete_query(["aw", "r"], 1)` returns the `r`-prefixed subcommands (e.g. `run`, `runs`, `research`, `rename`, `record-history` - assert as a subset/superset match, not an exact 3-item list, since the real command set is larger).
  - Test `complete_query(["aw", "run", "t"], 2)` in a fixture repo containing Set `tabcomp` returns `["tabcomp"]` (Set ID sourced from plan front matter, not `resolve_selectors`).
  - Test `complete_query(["aw", "ipd", "lint", "b"], 3)` returns the BARE id6 `["bja8og"]` (extracted from the path stem), NOT a full filename.
  - Test `complete_query(["aw", "ipd", "set", "a"], 2)` returns the plan statuses beginning with `a` sourced from `ipd_schema` (e.g. `["approved", "auto-approved"]`), and a parallel `aw specs set`/`aw backlog set` case returns the DIFFERENT status set valid for that type.
  - Test `aw __complete --cword N -- <tokens>` CLI output matches `complete_query` and exits 0.
  - Test a representative `complete_query` call over the fixture completes within the latency budget.
  - Test `cli.py` imports and `main([...])` runs without error when `argcomplete` is uninstalled (simulate absence).

## Spec / documentation sync

- Inline documentation for `__complete` and `complete_query`.

## Open questions

### OQ-01: How does __complete distinguish between flags and positionals?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: If the current word starts with `-`, `complete_query` returns matching option flags for the current subparser context; otherwise it delegates to the active positional completer for that subcommand position.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste passing unit-test output demonstrating `complete_query` returns bare-token candidate lists for subcommands, Set IDs, run IDs (from their real sources), plan/spec/backlog id6 handles (extracted from path stems), and per-type status enums (from `ipd_schema`, differing by artifact type), PLUS the latency assertion passing within the documented budget under the scan-scoping.
  - Observed evidence: `python3 -m pytest tests/test_completion.py -o addopts="" -v` -> `35 passed, 2 skipped in 1.22s`. The E-01 tests all PASSED: `CompleteQuerySubcommandTests::test_subcommand_prefix` (aw r -> superset incl run/runs/research/rename) + `test_flag_prefix_returns_flags` (--js -> --json); `CompleteQueryArtifactTests::test_plan_id6_bare_token_not_path` (`aw ipd lint b` -> `["bja8og"]`, a BARE id6 not a path), `test_plan_id6_excludes_terminal_disposition` (executed `ffffff` absent -> active-disposition scoping), `test_spec_id6` (`abc123`), `test_backlog_id6` (`def456`), `test_set_id_from_front_matter_not_resolver` (`aw run t` -> `["tabcomp"]`), `test_run_id_from_runs_dir` (`run-2026...` from the runs dir); `CompleteQueryStatusTests::test_plan_status_from_ipd_schema` (`aw ipd set a` -> `["approved","auto-approved"]` from ipd_schema), `test_spec_status_differs_from_plan` (spec `implementing`/`implemented` present, absent from plan statuses; sets differ), `test_backlog_status_set` (`["blocked","done","open","parked"]`); `CompleteQueryLatencyTests::test_representative_query_within_budget` PASSED (best-of-3 under the 250ms CI-safe bound; measured live ~1-11ms for artifact/status positions, ~28-42ms for the parser-build-dominated subcommand path, all < the <50ms interactive target vs the ~500ms unscoped `resolve_selectors(...,'plans',['b'])` sweep). ruff `--select E4,E7,E9,F` clean; ruff-format clean.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste CLI test output executing `aw __complete --cword 1 -- aw ru` emitting matching subcommands to stdout with exit 0, and a test confirming the token/cword wire protocol matches what child 01's generated scripts call.
  - Observed evidence: From the same `35 passed, 2 skipped` run. `DunderCompleteProtocolTests` all PASSED: `test_protocol_matches_query_and_exit0` (`aw __complete --cword 1 -- aw ru` -> stdout lines include `run`+`runs`, rc 0, AND the emitted lines EQUAL `complete_query(["aw","ru"],1)` - pinning the wire protocol to the query engine child-01 scripts consume), `test_artifact_protocol` (`--cword 3 -- aw ipd lint b` -> `["bja8og"]`, rc 0), `test_leading_dash_token_is_data_not_flag` (`--cword 2 -- aw ipd --js` -> `--json`, rc 0 - the `--` separator makes a leading option-like token DATA), `test_no_candidates_still_exit0` (unknown id6 -> empty stdout, rc 0). Live cross-check: `aw __complete --cword 1 -- aw ru` -> `run\nruns` rc 0.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Code inspection proving `# PYTHON_ARGCOMPLETE_OK` is a real comment within the first 1024 bytes of `cli.py` (not inside the docstring); a unit test proving `cli.py` imports and `main` runs cleanly with AND without `argcomplete`; and the plan text stating the supported argcomplete invocation and that generated console-script aliases are NOT globally auto-discovered via the `cli.py` marker.
  - Observed evidence: From the same run. `ArgcompleteSoftImportTests` all PASSED: `test_marker_is_real_comment_within_1024_bytes` (finds `# PYTHON_ARGCOMPLETE_OK` at byte 719 < 1024, AND asserts it sits AFTER the docstring close at byte 717 - i.e. a real comment, not docstring text), `test_cli_imports_and_runs_without_argcomplete` (with `argcomplete` import forced to ImportError, `main(["completion","bash"])` returns 0 and emits the script - the WITHOUT case; argcomplete is genuinely absent on this runner so this is also the real path), `test_maybe_argcomplete_is_noop_when_absent` (`_maybe_argcomplete` returns without raising when argcomplete is unimportable). WITH-argcomplete: the hook is wrapped in try/except and `argcomplete.autocomplete` is a documented no-op unless the completion env is set, so an installed-argcomplete path is exercised without error by construction (the honest-scope comment in cli.py states the supported invocation - `python -m agent_workflows`/marker-bearing/`register-python-argcomplete` - and that the generated aliases are NOT globally auto-discovered via the marker, with the child-01 `aw __complete` scripts as the primary path). Live: `importlib.util.find_spec('argcomplete') is None` and `import agent_workflows.cli` + `main(['--version'])` both succeed.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `pytest tests/test_completion.py` runs with all dynamic query tests passing.
  - Observed evidence: `python3 -m pytest tests/test_completion.py -o addopts=""` -> `35 passed, 2 skipped in 1.22s` (all 33 non-skipped assertions satisfied; the 2 skips are the child-01 zsh/fish `-n`/`--no-execute` shell-syntax checks, skipped-not-failed because those shells are absent on this runner). All tabcomp-02 dynamic-query, protocol, latency, and argcomplete tests pass. ruff `--select E4,E7,E9,F` on `agent_workflows/completion.py`, `agent_workflows/cli.py`, `tests/test_completion.py` -> `All checks passed!`; `ruff format --check` -> `3 files already formatted`. NOTE (run DECISION 03-4f1j25-D1): the pre-existing-red CLI conformance matrix (`tests/test_cli_conformance_matrix.py`) gains ONE undeclared leaf (`__complete`, a hidden `help=SUPPRESS` internal callback) - measured 35->36; it was ALREADY red on 35 unrelated undeclared leaves at run HEAD 5d94d95 (incl. the child-01 `completion` leaf). Declaring the hidden/internal family in `command_surface.COMMAND_INVENTORY` is OUT of this plan's Scope-Paths and left as the noted housekeeping follow-up, matching bja8og DECISION 12-bja8og-D1.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: execution requires explicit human approval. Upon approval, implement according to the checklist, verify all V items with test outputs, run `aw ipd lint --phase pre-transition`, and finalize via the IPD lifecycle workflow.
