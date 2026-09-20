# IPD: Enforce setid length bounds and dynamic cutover

- Date: 2026-09-20
- Kind: child
- Concern: Setids that exceed reasonable lengths degrade filename legibility, break terminal formatting, and obfuscate topic groupings.
- Scope: Establish an enforced setid length contract across the repository (strongly prefer <= 14 chars, warn on > 14, error on > 24), with dynamic per-repo cutover on install/update to grandfather historical artifacts, complete CLI authoring guards, and unified documentation.
- Scope-Paths: agent_workflows/config.py, agent_workflows/project_schema.py, agent_workflows/engine.py, agent_workflows/install_wizard.py, agent_workflows/check_engine.py, agent_workflows/cli.py, agent_workflows/ipd_schema.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_scaffold.py, agent_workflows/specs.py, agent_workflows/backlog.py, agent_workflows/research.py, agent_workflows/artifact_cli.py, .aw/config/project.json, AGENTS.md, .aw/records/plans/README.md, .aw/records/specs/20260910-2lcqno-01-2lcqno-setid-shared-topic-label-and-type-scoped-resolution.spec.md, .aw/records/specs/20260817-2147-01-uniform-artifact-naming-grammar.spec.md, .aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md, .aw/records/backlog/README.md, .aw/records/specs/README.md, .aw/records/research/README.md, .aw/records/walkthroughs/README.md, tests/test_config.py, tests/test_check_engine.py, tests/test_ipd_lint.py, tests/test_ipd_scaffold.py, tests/test_awnaming_grammar_and_producers.py
- Item-Dependencies: executed:ogs6a2
- Status: to-review
- Set: setidlen
- Order: 1
- Highest E allocated: 07
- Author: antigravity
- Id: x75obw

## Workflow history

- 2026-09-20 to-review (antigravity): authored complete review-ready IPD with dynamic cutover architecture and full test coverage.
- 2026-09-20 draft (antigravity): created via aw ipd scaffold.

## Goal

Enforce a clear, unified setid length contract: strongly prefer setids <= 14 characters, warn on > 14 characters, and fail with a hard error on > 24 characters. Ensure this applies forward-looking from the date agent-workflows is installed or updated in a repository by recording the dynamic cutover date in `.aw/config/project.json`, preventing historical breakages while stopping non-conforming setids across all tools and documentation.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Configuration & dynamic cutover storage

- [ ] E-01 Add setid policy schema and dynamic cutover reader/stamper in `agent_workflows/config.py` and `agent_workflows/project_schema.py`.
  - Depends on: none
  - Expected outcome: Add optional `setids` block to `ProjectPolicySchema`. Implement `get_setid_policy(repo_root)` reading `warn_length` (default 14), `max_length` (default 24), `cutover_date` (default None), and `strict` (default False) from `.aw/config/project.json`, integrating with the unified cutover resolver from `ogs6a2`. Pure helper `stamp_setid_cutover_if_missing(repo_root)` writes current ISO date when absent.
  - Execution state: pending
- [ ] E-02 Hook dynamic cutover stamping into framework install and update in `agent_workflows/engine.py` and `agent_workflows/install_wizard.py`.
  - Depends on: E-01
  - Expected outcome: When `install_into_repo` or `aw install` / `aw setup` runs, `setids.cutover_date` (or `cutovers.setid_length`) is stamped into the target repository's `.aw/config/project.json` if not already present, preserving any existing timestamp on subsequent updates.
  - Execution state: pending

### Task group 2: Policy engine & repository checks

- [ ] E-03 Register `check.setid-length-warn` and `check.setid-length-error` in `agent_workflows/check_engine.py`.
  - Depends on: none
  - Expected outcome: `RULE_REGISTRY` contains `check.setid-length-warn` (severity `warning`, catalog `I-16`, deterministic) and `check.setid-length-error` (severity `error`, catalog `I-16`, deterministic).
  - Execution state: pending
- [ ] E-04 Implement setid length validation in `agent_workflows/check_engine.py` and `agent_workflows/cli.py`.
  - Depends on: E-01, E-03
  - Expected outcome: `check_engine` inspects declared and filename setids across all tracked artifact types. Grandfathers artifacts dated prior to the repository's `cutover_date` unless `strict` is set. Wire `--strict-setid-length` CLI flag in `agent_workflows/cli.py`. Emits `check.setid-length-warn` for `14 < len(setid) <= 24` and `check.setid-length-error` for `len(setid) > 24` on post-cutover artifacts.
  - Execution state: pending

### Task group 3: IPD schema & linter integration

- [ ] E-05 Enforce setid length limits and advisories in `agent_workflows/ipd_schema.py` and `agent_workflows/ipd_lint.py`.
  - Depends on: E-01
  - Expected outcome: `ipd_schema.validate_metadata` checks `- Set:` length and produces `MetaError` if `len(setid) > 24` (driving diagnostic `IPD-M104` / `IPD-M110` with disposition `error`). `ipd_lint.lint_text` emits a non-blocking advisory if `14 < len(setid) <= 24` (disposition remains `conforming`), respecting grandfathering on terminal and pre-cutover plans.
  - Execution state: pending

### Task group 4: Authoring & scaffolding guards

- [ ] E-06 Add setid validation to creation and regrouping CLI verbs.
  - Depends on: none
  - Expected outcome: `aw ipd scaffold`, `aw specs new`, `aw backlog new`, `aw research new`, and `aw group` reject setids > 24 characters with an explicit error, and print an advisory warning when setids are between 15 and 24 characters advising that <= 14 characters is strongly preferred.
  - Execution state: pending

### Task group 5: Documentation & specification sync

- [ ] E-07 Synchronize documentation, guides, and specifications across the repository.
  - Depends on: none
  - Expected outcome: Update `AGENTS.md`, `.aw/records/plans/README.md`, spec `20260910-2lcqno-01`, spec `20260817-2147-01`, spec `20260802-1904-01`, and artifact READMEs (`backlog`, `specs`, `research`, `walkthroughs`) to document the length limits (<= 14 preferred, > 14 warning, > 24 disallowed) and eliminate all contradictory prose.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Single source of naming grammar: `agent_workflows/artifact_naming.py` handles regex parsing (`parse_clustered`) for artifact filenames.
- Cutover precedents: `SPEC_ID6_CUTOVER_DATE` (`check_engine.py:40`) and `CARRIER_CUTOVER_DATE` (`check_engine.py:4505`) were hardcoded in previous iterations, but `read_dependency_schema_cutover` in `config.py:1047` established the portable pattern of reading cutover markers from `.aw/config/project.json`.
- Policy registry: `check_engine.RULE_REGISTRY` maps rule IDs to `(severity, assurance, determinism, invariant)`. Invariant `I-16` is cataloged for setid semantics.
- Lint dispositions: In `ipd_lint.py`, `LintResult(disposition, diags, advisories)` distinguishes blocking errors (`diags`, causing disposition `error`) from non-blocking authoring nudges (`advisories`, allowing disposition `conforming`).

## Findings

- An audit of all 597 unique `(setid, len)` pairs currently across the repository showed 561 setids <= 14 chars, 36 setids between 15 and 24 chars, and 0 setids > 24 chars.
- Grandfathering historical records is required so that pre-existing valid records (like `artifact-org-adopters` and `research-prompt-pipeline`) do not turn CI red.
- Per maintainer directive, the cutover date must not be a hardcoded calendar date in the Python source code; it must be stamped into `.aw/config/project.json` dynamically when agent-workflows is installed or updated in a target repository for the first time.

## Proposed changes (ordered, validatable)

1. In `agent_workflows/config.py` and `agent_workflows/project_schema.py`: implement `get_setid_policy(repo_root)` and `stamp_setid_cutover_if_missing(repo_root)`. Support `warn_length`, `max_length`, `cutover_date`, and `strict`.
2. In `agent_workflows/engine.py` and `agent_workflows/install_wizard.py`: call `stamp_setid_cutover_if_missing` during repo installation and update flows.
3. In `agent_workflows/check_engine.py` and `agent_workflows/cli.py`: register `check.setid-length-warn` and `check.setid-length-error`. Implement length evaluation in setid check loops respecting `cutover_date` and `strict`. Add `--strict-setid-length` CLI flag.
4. In `agent_workflows/ipd_schema.py` and `agent_workflows/ipd_lint.py`: add setid length checks. Error on > 24 chars, emit advisory on 15-24 chars for post-cutover plans.
5. In `agent_workflows/ipd_scaffold.py`, `agent_workflows/specs.py`, `agent_workflows/backlog.py`, `agent_workflows/research.py`, and `agent_workflows/artifact_cli.py`: validate `--set` arguments at command invocation time.
6. In `AGENTS.md`, `.aw/records/plans/README.md`, specs, and READMEs: document the length constraints and remove ambiguities.

## Deferred / out of scope (with reason)

- Mass-renaming historical setids > 14 chars (e.g. `artifact-org-adopters`): deferred to avoid breaking cross-tree citations and historical git hashes.
  - Carrier-Declined: Grandfathering handles historical artifacts safely without rewriting repository history.
- Modifying the core regex in `artifact_naming.py` to hard-limit setid length: deferred to maintain separation of concerns.
  - Carrier-Declined: Regex validation is binary and cannot distinguish warnings from errors or check dynamic cutover dates.

## Scope check

- Over-scope: none.
- Under-scope: avoided by checking both frontmatter `- Set:` and filename identity slots across all artifact types, guarding CLI authoring entrypoints, and syncing all documentation.

## Required tests / validation

- `tests/test_config.py`: unit tests for `get_setid_policy` (defaults, custom overrides, missing cutover) and `stamp_setid_cutover_if_missing`.
- `tests/test_check_engine.py`: tests verifying:
  - Pre-cutover record with 20-char setid passes with zero findings.
  - Post-cutover record with 16-char setid produces `check.setid-length-warn`.
  - Post-cutover record with 26-char setid produces `check.setid-length-error`.
  - Strict mode flags pre-cutover records.
- `tests/test_ipd_lint.py`: tests verifying IPD linting dispositions (conforming for <= 14, conforming with advisory for 15-24, error for > 24).
- `tests/test_ipd_scaffold.py`, `tests/test_awnaming_grammar_and_producers.py`, and CLI tests: tests asserting CLI tool abort on > 24 chars and warning on 15-24 chars.

## Spec / documentation sync

- `AGENTS.md`: lines 25 and 118 updated with setid length contract.
- `.aw/records/plans/README.md`: section on clustering grammar updated.
- `.aw/records/specs/20260910-2lcqno-01-2lcqno-setid-shared-topic-label-and-type-scoped-resolution.spec.md`: add normative rule N8.
- `.aw/records/specs/20260817-2147-01-uniform-artifact-naming-grammar.spec.md`: annotate `<setid>` segment definition.
- `.aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md`: update metadata schema definition.
- READMEs under `.aw/records/backlog/`, `.aw/records/specs/`, `.aw/records/research/`, and `.aw/records/walkthroughs/`.

## Open questions

### OQ-01: Should `--strict-setid-length` be available on the CLI in addition to project configuration?

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Yes. Support both `.aw/config/project.json` (`"strict": true`) and `--strict-setid-length` flag on `aw check` and `aw ipd lint` for local or CI enforcement.

### OQ-02: Should absent cutover date in `project.json` grandfather everything or enforce today?

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Absent cutover date fails open (grandfathers existing files) until `aw setup`, `aw install`, or `install_into_repo` writes the date into `project.json`. This prevents breaking un-migrated repositories unexpectedly.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `python3 -m pytest tests/test_config.py` passes, demonstrating correct loading of defaults, custom thresholds, strict mode, and cutover stamping into project.json.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Automated test proving that running `install_into_repo` stamps `setids.cutover_date` into `.aw/config/project.json` on a clean repo, and leaves an existing date unchanged on re-installation.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Assertion that `check.setid-length-warn` and `check.setid-length-error` exist in `RULE_REGISTRY` with expected severities and invariant `I-16`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `python3 -m pytest tests/test_check_engine.py` passes with test cases for pre-cutover files, warning-tier post-cutover files, error-tier post-cutover files, and strict mode.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `python3 -m pytest tests/test_ipd_lint.py` passes, verifying `IPD-M104`/`IPD-M110` error on > 24 chars and advisory on 15-24 chars.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: Tests demonstrating `aw ipd scaffold`, `aw specs new`, `aw backlog new`, and `aw group` abort when `--set` > 24 chars and output warning when 15-24 chars.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: Clean git diff across all specified documentation files and grep confirming all prose mentions `<= 14` preferred and `> 24` disallowed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: execute path-scoped commits for each task group without mutating unrelated files. All automated tests must run and pass. Upon completion, transition via `aw ipd finalize` in a managed lane or report results for maintainer review.
