# IPD: Doctor Actionable Remediation Commands and Targeted Fixes

- Date: 2026-08-23
- Kind: child
- Concern: Doctor CLI usability and actionable remediation output.
- Scope: agent_workflows/doctor.py, remediation generation, and doctor report tests.
- Status: reviewed
- Set: doctorremedy
- Order: 1
- Highest E allocated: 03
- Author: Antigravity
- Id: tdlspr

## Workflow history

- 2026-08-23 draft (Antigravity): initial plan draft for copy-pasteable doctor remediation commands.
- 2026-08-23 /plan-review (Antigravity): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003

## Goal

Upgrade `aw doctor` health reporting to synthesize exact, cut-and-pastable remediation commands in human output and structured next-action receipts in agent output, eliminating abstract placeholders (`<type>`, `<file>`) and providing direct copy-pasteable commands for all automated and path-bound issue categories.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Remediation engine and command synthesizer

- [ ] E-01 Implement a structured remediation synthesizer in `agent_workflows/doctor.py` that inspects drift findings, extracts resolved repository-relative POSIX file paths (sanitizing any absolute machine paths), derives artifact types and targets, and produces typed `Remediation` records with concrete CLI commands (e.g. `aw index`, `aw setup`, `aw migrate-layout`, `aw sanitize --fix`, `aw rename <type> <path>`, `aw group <type> <path> --set <new-set-id>`).
  - Depends on: none
  - Expected outcome: every drift rule maps to a concrete remediation record with pre-populated relative paths, types, and commands.
  - Execution state: pending

### Material change 2: Human report renderer upgrades

- [ ] E-02 Update `render_human_report` in `agent_workflows/doctor.py` to format concrete, cut-and-pastable remediation commands in both the per-issue breakdown and the bottom "Summary of issues and proposed fixes" table, displaying single-line copy-pasteable commands for automated fixes and target-populated commands for parameterized actions, while preserving terminal color, NO_COLOR, and plain width wrapping.
  - Depends on: E-01
  - Expected outcome: human terminal output shows immediate copy-pasteable commands without placeholder syntax.
  - Execution state: pending

### Material change 3: Structured next-actions and test suite

- [ ] E-03 Wire concrete remediation commands into `CommandResult.next` and `CommandResult.next_actions` for `--agent` and `--json` modes in `agent_workflows/doctor.py`, and write comprehensive tests in `tests/test_doctor_remediations.py` validating that every supported issue category produces the exact expected remediation command while existing doctor test suites (`tests/test_doctor.py`, `tests/test_term_severity.py`, `tests/test_cli_reads_and_checks.py`) remain 100% green.
  - Depends on: E-01, E-02
  - Expected outcome: machine and human outputs share fact parity, and all remediation commands are verified by automated tests.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `agent_workflows/doctor.py` categorizes drift findings using `_categorize_drift`, but currently returns hardcoded template strings containing generic placeholders like `<type>`, `<file>`, `<unique-setid>`.
- Drift objects (`core.Drift`) carry `location`, `rule`, and `detail`. For artifact findings, `location` contains the artifact path from which artifact type (`plans`, `specs`, `prompts`, `backlog`, `research`) can be deterministically inferred.
- For manifest indices, the exact command `aw index` or `aw index <type>` is 100% deterministic and requires zero arguments from the user.
- For setup, layout split-brain, and sanitizer findings, commands (`aw setup`, `aw migrate-layout`, `aw sanitize --fix`) are fully automated.

## Findings

Current doctor output produces generic guidance:
```text
Summary of issues and proposed fixes:
  1. Set ID collision across artifact records (10 files)
     Fix: run 'aw group <type> <file> --set <unique-setid>' to assign a unique Set ID.
  2. Filename does not match artifact naming grammar (4 files)
     Fix: run 'aw rename <type>' or rename to match 'YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md'.
```
Target doctor output with concrete, populated commands:
```text
Summary of issues and proposed fixes:
  1. Manifest index is missing or out of date (2 files)
     Fix: aw index
  2. Filename does not match artifact naming grammar (4 files)
     Fix: aw rename plans .aw/records/plans/pending/invalid_name.md
  3. Set ID collision across artifact records (2 files)
     Fix: aw group specs .aw/records/specs/20260822-auth-01-sp0001-spec.md --set <new-set-id>
```

## Proposed changes (ordered, validatable)

1. Define `Remediation` dataclass in `agent_workflows/doctor.py` holding `title`, `summary_fix`, `detailed_fix`, `command`, `file_path`, and `line_number`.
2. Enhance `_categorize_drift` to extract the artifact type from the location path or rule, and synthesize specific commands with sanitized repo-relative POSIX paths.
3. Establish a deterministic priority order for `CommandResult.next`:
   - Priority 1: `doctor.setup-needed` -> `"aw setup"`
   - Priority 2: `doctor.layout-split-brain` -> `"aw migrate-layout"`
   - Priority 3: `doctor.leak-*` -> `"aw sanitize --fix"`
   - Priority 4: `stale-index` / `doctor.index-*` -> `"aw index"`
   - Priority 5: First actionable artifact repair (`aw rename <type> <path>`, `aw group <type> <path> --set <new-set-id>`).
4. Update `render_human_report` to format per-file `-> Fix: <command>` lines in the detail breakdown and clean `Fix: <command>` lines in the summary table.
5. Populate `CommandResult.next_actions` with all synthesized commands.
6. Create `tests/test_doctor_remediations.py` to assert remediation commands across all rule types and priority ranking.

## Deferred / out of scope (with reason)

- In-place auto-fixing directly inside `aw doctor` (e.g. `aw doctor --fix`) is out of scope; `aw doctor` remains strictly read-only and emits actionable commands for the user/agent to run.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- Unit tests in `tests/test_doctor_remediations.py` verifying each drift rule category produces the expected concrete command.
- Deterministic priority tests proving `CommandResult.next` selects the highest-priority action.
- Existing doctor suites (`tests/test_doctor.py`, `tests/test_term_severity.py`, `tests/test_cli_reads_and_checks.py`) pass.
- Full regression suite via `make test`.

## Spec / documentation sync

- Update docstrings in `agent_workflows/doctor.py`.

## Open questions

### OQ-01: How should multi-file issue summaries format fixes when files belong to different types?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: For multi-file issues spanning different types, the summary line provides the general family command (e.g. `aw index` or `aw rename`), while the detailed per-issue breakdown provides the exact file-specific command.

### OQ-02: How is the primary next-action selected when multiple findings of different categories are present?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: A deterministic priority hierarchy (`setup` -> `migrate-layout` -> `sanitize --fix` -> `index` -> per-file repairs) selects the single most foundational next step for `CommandResult.next`, while `CommandResult.next_actions` contains the complete list.


## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: unit tests in `tests/test_doctor_remediations.py` verify `_categorize_drift` generates typed `Remediation` records with populated types and relative paths.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: CLI tests verify `render_human_report` outputs concrete copy-pasteable commands in both the detail section and summary table without placeholder syntax.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: tests verify `CommandResult.next_actions` contains synthesized remediation commands, and full test suite passes with `make test`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: focused entirely on doctor remediation synthesis and reporting.

### Execution contract

1. Open questions RESOLVED: OQ-01 is resolved. No open questions remain.
2. Scope fence: Modify `agent_workflows/doctor.py` and add `tests/test_doctor_remediations.py`. Do not refactor unrelated subsystems.
3. Honesty rule (hard MUST): When reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: On completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.
