# IPD: Make specs, releases, spec-link, search, and dep-gate log-aware in the cutover code patch

- Date: 2026-11-25
- Kind: child
- Concern: Backlog `ldfefd` (`psm9ac` F-05 and OQ-01, maintainer answer to `run-20261126T020242Z-3080634` question `05-psm9ac-a1-batch-b-production-log-aware-gaps`): in `.aw/system/cutover/metastore-code.cutover.patch`, writers already create post-cutover log-backed records whose `.md` file holds only the two-key YAML mirror (`id`, `status`) while all other fields and history live in `.aw/records/meta/<id6>.jsonl`. However, five non-backlog production areas were never made log-aware in the cutover code patch: (1) `agent_workflows/specs.py::validate_spec` and `run_check` (plus callers `agent_workflows/check_engine.py::check_content` and `agent_workflows/runner_shared.py::check_review_lane_artifacts`, `enforce_freeze_time_refusal`) fail on conformant log-format specs with `attention.history-missing`; (2) `agent_workflows/releases.py::validate_release`, `parse_release`, `check_from_backlog`, `check_graduated_to`, `get_release_blockers`, and `check_blocks_release` (plus `check_engine.py::check_content`) read inline text only (`validate_release` emits `release.version-missing`; `check_from_backlog` returns `[]` on log-format repos); (3) `agent_workflows/check_engine.py::parse_cited_spec_ids` and `check_plan_spec_link_missing` read only legacy `- Concern:`/`- Scope:`/`- Scope-Paths:` bullets instead of `## Concern`/`## Scope` body sections and log-stored `scope_paths`; (4) `agent_workflows/cli.py::_run_search` non-`--full` mode scans only YAML fence + H1 of `.md` files and misses log-stored `title`/`summary`/`short_description`; and (5) `agent_workflows/hooks/ipd_dependency_statement_gate.py::_staged_ipd_overlay` skips staged `meta/<id6>.jsonl` files where `item_dependencies` lives post-cutover. Together these five gaps block at least 6 batch B test modules (`psm9ac`) plus later test batches.
- Scope: In an isolated scratch worktree with both cutover patches applied (including `hdwqex`, `89mtbl`, `nv3upa`, `fljn9b`, and `cugg3w`), make `agent_workflows/specs.py` (and its `check_engine`/`runner_shared` callers), `agent_workflows/releases.py` (and its `check_engine` caller), `agent_workflows/check_engine.py::parse_cited_spec_ids`/`check_plan_spec_link_missing`, `agent_workflows/cli.py::_run_search`, and `agent_workflows/hooks/ipd_dependency_statement_gate.py::_staged_ipd_overlay` log-aware while preserving legacy bullet-format parity, add and pass core behavioral test module `tests/test_cutover_log_checkers.py` in the scratch worktree, and regenerate `.aw/system/cutover/metastore-code.cutover.patch`. No live code changes outside the cutover code patch.
- Scope-Paths: .aw/records/plans/pending/20261125-metastore-315-szykgd-make-specs-releases-spec-link-search-and-dep-gate-log-aware.ipd.md, .aw/system/cutover/metastore-code.cutover.patch
- Item-Dependencies: executed:cugg3w
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: bug
- Priority: high
- From-Backlog: ldfefd
- Blocks-Release: next
- Set: metastore
- Order: 315
- Highest E allocated: 05
- Author: antigravity/gemini
- Id: szykgd

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-26 to-review (antigravity/gemini): authored as Order 315 ahead of psm9ac per maintainer answer to run-20261126T020242Z-3080634 question 05-psm9ac-a1-batch-b-production-log-aware-gaps ("Fix backlog pointer in fljn9b and split 1 production-fix plan ahead of psm9ac (Recommended)").
- 2026-11-26 draft (antigravity/gemini): created.

## Goal

Make spec and release validation/link checkers, `check_plan_spec_link_missing`, default non-`--full` `aw search`, and the `ipd_dependency_statement_gate` pre-commit hook log-aware inside `.aw/system/cutover/metastore-code.cutover.patch`, unblocking `psm9ac` (batch B) and later test batches while keeping legacy text fallback intact.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: scratch worktree

- [ ] E-01 Create the scratch worktree following the SCRATCH PROCEDURE of `2k5t16` (Step 0): run `git worktree add --detach .aw/state/szykgd/scratch HEAD`; inside `.aw/state/szykgd/scratch`, run `git apply --index .aw/system/cutover/metastore-docs.cutover.patch`, record `BASE=$(git write-tree)` in F-01, and then run `git apply --index .aw/system/cutover/metastore-code.cutover.patch`. If either patch rejects, stop and report.
  - Depends on: none
  - Expected outcome: `.aw/state/szykgd/scratch` holds HEAD plus both patches staged, and F-01 records the base tree id.
  - Execution state: pending

### Task group 2: log-aware checkers, search, and dep-gate (scratch worktree only)

- [ ] E-02 Make `agent_workflows/specs.py`, `agent_workflows/releases.py`, and their `check_engine.py` / `runner_shared.py` callers log-aware in `.aw/state/szykgd/scratch` while keeping legacy bullet-format parity intact:
  1. In `agent_workflows/specs.py`, extend `validate_spec(path, text, *, state=None, has_history=None, repo_root=None)` so when `state` is supplied or a companion `meta/<id6>.jsonl` exists under the resolved records root (`repo_root` or walked up from `path`), it validates via `validate_spec_state(path, state, has_history=has_history)` (also refusing a YAML mirror `id` or `status` in `text` that contradicts `state`, and keeping duplicate-bullet checks only when leading metadata bullets exist), falling back to legacy bullet validation when no log exists. Update `specs.run_check` to pass `repo_root=repo_root` (or resolved `state` and `has_history`), and update callers `agent_workflows/check_engine.py::check_content` (`record_type == "specs"`), `agent_workflows/runner_shared.py::check_review_lane_artifacts` (specs branch), and `agent_workflows/runner_shared.py::enforce_freeze_time_refusal` (specs branch, also including companion `meta/<id6>.jsonl` bytes in the `_FREEZE_GATE_CACHE` digest key).
  2. In `agent_workflows/releases.py`, add a log-aware release reader and validator (`validate_release_state` plus log-aware `validate_release(path, text, *, state=None, repo_root=None)` and `parse_release(path, text, *, state=None, repo_root=None)` reading `id6`, `version`, `status`, and `summary` from `meta/<id6>.jsonl` when present, falling back to `artifact_meta.read_text` for legacy text); update `check_from_backlog`, `check_graduated_to`, `get_release_blockers`, and `check_blocks_release` to read `from_backlog`, `graduated_to`, and `blocks_release` from `artifact_meta` state (`query(..., include_fields=True)` / `read`) rather than `_meta.read_text(text)` alone; and pass `repo_root=repo_root` (or `state`) from `agent_workflows/check_engine.py::check_content` (`record_type == "releases"`).
  - Depends on: E-01
  - Expected outcome: in a throwaway repository on `.aw/state/szykgd/scratch`, `aw specs new --apply` followed by `aw specs check` exits 0; `releases.create_release` followed by `releases.validate_release` and `check_engine.check_content(..., "releases")` returns `[]`; and `releases.check_from_backlog`, `releases.check_graduated_to`, and `releases.get_release_blockers` see log-stored links and gates.
  - Execution state: pending

- [ ] E-03 Make `check_plan_spec_link_missing`, default non-`--full` `aw search`, and `ipd_dependency_statement_gate` log-aware in `.aw/state/szykgd/scratch`:
  1. In `agent_workflows/check_engine.py`, extend `parse_cited_spec_ids(plan_text, known_spec_ids, *, state=None)` to scan `## Concern` and `## Scope` body sections (respecting fenced code blocks) and `state.fields.get("scope_paths")` when present, in addition to legacy `- Concern:`/`- Scope:`/`- Scope-Paths:` bullets; in `check_plan_spec_link_missing`, pass `state=st_obj` to `parse_cited_spec_ids` and read `scope_paths` from `st_obj.fields.get("scope_paths")` (falling back to `_declared_bullet_fields(text).get("scope_paths")`) for the spec-edit exemption.
  2. In `agent_workflows/cli.py::_run_search`, populate `cached_by_path` via `artifact_meta.query(project_context=search_ctx, include_fields=True)` whenever `search_has_tree` is true (not only when status filters are set), and when `full_search=False` match the pattern against log-stored header/descriptive metadata (`title`, `summary`, `short_description`, `set`, `status`, `id6`, and string metadata values from `st_row.fields`) in addition to the `.md` YAML mirror / H1 and filename, while still excluding Markdown body sections unless `-F`/`--full` is passed.
  3. In `agent_workflows/hooks/ipd_dependency_statement_gate.py::_staged_ipd_overlay`, in addition to staged `.ipd.md` paths, inspect staged `.aw/records/meta/<id6>.jsonl` (and `.agents/meta/<id6>.jsonl`) paths: resolve the staged state via `artifact_meta.read_at(id6, ":0:", project_context=ctx)`, and for any staged IPD (`res.state.type == "ipd"` with a resolved plan path) add it to `overlay_states` and `statuses` so staging a log-only `item_dependencies` edit triggers the same cycle, dangling, malformed, and advancing-unresolved gate as staging `.ipd.md`.
  4. Record the verified caller and behavior audit across all five areas in F-02.
  - Depends on: E-02
  - Expected outcome: `check_plan_spec_link_missing` detects spec citations in log-format plans and honors log-stored `scope_paths` exemptions; `aw search` without `-F` matches log-stored titles and summaries while excluding body-only tokens; and `ipd_dependency_statement_gate.check` catches staged `meta/<id6>.jsonl` dependency violations.
  - Execution state: pending

- [ ] E-04 Add and run behavioral test module `tests/test_cutover_log_checkers.py` in `.aw/state/szykgd/scratch` (asserting real outputs, exit codes, and side effects; no code-pinning tests):
  1. Cover `aw specs new --apply` -> `aw specs check` clean, negative `specs.validate_spec` log-format cases (deferred missing gate, invalid priority/work_kind, empty history, mirror/log mismatch), `check_engine.check_content(..., "specs")`, and `runner_shared.enforce_freeze_time_refusal` cache invalidation when `meta/<id6>.jsonl` changes.
  2. Cover `releases.create_release` -> `releases.validate_release`/`parse_release`/`check_engine.check_content(..., "releases")` clean and negative cases, plus `releases.check_from_backlog` (`malformed` and `dangling`), `releases.check_graduated_to`, and `releases.get_release_blockers` on log-format fixtures.
  3. Cover `check_engine.parse_cited_spec_ids` and `check_plan_spec_link_missing` on log-format plans citing a known spec in `## Concern` / `## Scope` / log-stored `scope_paths` (including spec-edit exemption via log-stored `scope_paths`).
  4. Cover `aw search` without `-F` matching log-stored `title`, `summary`, and `short_description` across plans, specs, backlog, research, and prompts while still excluding body-only tokens unless `-F`/`--full` is passed.
  5. Cover `ipd_dependency_statement_gate.check` refusing staged malformed, dangling, cyclic, and advancing-unresolved `item_dependencies` both when `.ipd.md` + `meta/<id6>.jsonl` are staged and when only `meta/<id6>.jsonl` is staged, while remaining a no-op on untouched files.
  6. Run `python3 -m pytest -o addopts="" -m '' -v tests/test_cutover_log_checkers.py` in `.aw/state/szykgd/scratch` and confirm every test passes.
  - Depends on: E-03
  - Expected outcome: `tests/test_cutover_log_checkers.py` passes every test in `.aw/state/szykgd/scratch`.
  - Execution state: pending

### Task group 3: package

- [ ] E-05 In `.aw/state/szykgd/scratch`, run `git add -A` and write `git diff --cached --binary $BASE` over `.aw/system/cutover/metastore-code.cutover.patch` in the executing checkout; remove the scratch worktree (`git worktree remove --force .aw/state/szykgd/scratch`); run `python3 -m pytest -o addopts="" tests/test_metastore_cutover_code_patch.py` in the executing checkout; verify `git status --short` shows only `- Scope-Paths:` modified; and commit through `aw commit szykgd -- .aw/records/plans/pending/20261125-metastore-315-szykgd-make-specs-releases-spec-link-search-and-dep-gate-log-aware.ipd.md .aw/system/cutover/metastore-code.cutover.patch`; never push.
  - Depends on: E-04
  - Expected outcome: `.aw/system/cutover/metastore-code.cutover.patch` contains all prior code-patch hunks plus this plan's changes; `tests/test_metastore_cutover_code_patch.py` passes; scratch worktree is removed; one path-scoped commit is created.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The scratch procedure and cumulative code patch are defined in executed plan `2k5t16` (Step 0, OQ-01); executed sibling `g45vyv`, reviewed sibling `hdwqex`, and Order 314 sibling `fljn9b` follow the same procedure.
- `agent_workflows/specs.py::validate_spec_state` and `agent_workflows/attention.py::_spec_record` establish the repository pattern for validating a log-backed artifact from `artifact_meta.State` plus a `has_history` boolean while preserving legacy text validation (`validate_spec`) for unmigrated or pure-text inputs.
- Tests exercise real behavior and assert on observable outcomes (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); no `inspect`, `ast`, regex, or substring code-pinning tests.
- Cite code by symbol (`path::Symbol`) or by a quoted content string, with a line number only appended as a hint and never alone (advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | (written by E-01) | Base tree id after applying `.aw/system/cutover/metastore-docs.cutover.patch`. |
| F-02 | (written by E-03) | Caller and behavior audit across `specs.py`, `releases.py`, `check_engine.py`, `cli.py`, `runner_shared.py`, and `hooks/ipd_dependency_statement_gate.py`. |
| F-03 | `psm9ac` F-05 and direct probes: `specs.validate_spec` on a log-format spec returned `[('attention.history-missing', ...)]`; `releases.validate_release` on a log-format release returned `[('release.version-missing', ...)]`; `releases.check_from_backlog` calls `_meta.read_text(text).fields.get("from_backlog")`; `check_engine.parse_cited_spec_ids` on a log-format plan with `## Concern` returned `[]`; `cli._run_search` non-`--full` mode scans only YAML fence + H1; `hooks/ipd_dependency_statement_gate.py::_staged_ipd_overlay` skips staged `meta/<id6>.jsonl`. | Five verified non-backlog production cutover gaps in `.aw/system/cutover/metastore-code.cutover.patch` block `psm9ac` (batch B) and later test batches. |

## Proposed changes (ordered, validatable)

1. E-01: Create scratch worktree `.aw/state/szykgd/scratch` with both cutover patches staged.
2. E-02: Make `agent_workflows/specs.py`, `agent_workflows/releases.py`, and their `check_engine`/`runner_shared` callers log-aware while keeping legacy parity.
3. E-03: Make `check_engine.parse_cited_spec_ids`/`check_plan_spec_link_missing`, `cli._run_search` non-`--full` metadata search, and `hooks/ipd_dependency_statement_gate.py::_staged_ipd_overlay` log-aware; record F-02.
4. E-04: Add and pass `tests/test_cutover_log_checkers.py` in `.aw/state/szykgd/scratch`.
5. E-05: Regenerate `.aw/system/cutover/metastore-code.cutover.patch`, remove the scratch worktree, pass `tests/test_metastore_cutover_code_patch.py`, and commit path-scoped.

```mermaid
flowchart TD
    E01["E-01: Create scratch worktree with both patches"] --> E02["E-02: Make specs.py, releases.py, and callers log-aware"]
    E02 --> E03["E-03: Make spec-link check, aw search, and dep-gate log-aware"]
    E03 --> E04["E-04: Add and run tests/test_cutover_log_checkers.py"]
    E04 --> E05["E-05: Regenerate code patch, run guard test, commit"]
```

## Deferred / out of scope (with reason)

- Making `agent_workflows/backlog.py` (including the `backlog.run_new` writing-standard pointer) log-aware: already owned by Order 314 ahead of `cugg3w`.
  - Carrier: fljn9b
- Converting batch B's 18 test modules (`test_backlog_handoff_close` through `test_ipd_dependency_statement_gate`): runs immediately after this plan executes.
  - Carrier: psm9ac
- Converting later test batches (batches C through F): later batch children.
  - Carrier: x8id25
- Applying the cutover patches on the real tree: attended cutover commit.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none. No live code or test files are modified outside `.aw/system/cutover/metastore-code.cutover.patch`.
- Under-scope: none. All five non-backlog production cutover gaps recorded in `psm9ac` F-05 map to E-02 through E-04 (while the `backlog.run_new` pointer gap is folded into `fljn9b`).

## Required tests / validation

- Throwaway-repository smoke checks on `.aw/state/szykgd/scratch` for `aw specs check`, `releases.validate_release`/`check_from_backlog`, `check_plan_spec_link_missing`, `aw search`, and `ipd_dependency_statement_gate` (V-02, V-03).
- Core behavioral test module `python3 -m pytest -o addopts="" -m '' -v tests/test_cutover_log_checkers.py` in `.aw/state/szykgd/scratch` (V-04).
- Cumulative patch guard test `python3 -m pytest -o addopts="" tests/test_metastore_cutover_code_patch.py` in the executing checkout (V-05).

## Spec / documentation sync

No spec or documentation change is needed in this plan. Spec `4sd62s` Sections 4.1 through 4.6 already define the post-cutover log format, and `.aw/system/cutover/metastore-docs.cutover.patch` already updates the documentation. This plan brings the five remaining production checker, search, and hook paths inside the cutover code patch into agreement with them.

## Open questions

None open.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition) - as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction - name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git worktree add --detach .aw/state/szykgd/scratch HEAD` command, both `git apply --index` commands (for `.aw/system/cutover/metastore-docs.cutover.patch` and `.aw/system/cutover/metastore-code.cutover.patch`) with exit status 0, and the base tree id recorded in F-01.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a throwaway-repository run on `.aw/state/szykgd/scratch` (code paths updated by E-02) showing `aw specs new --apply` followed by `aw specs check` exiting 0 with zero findings, `specs.validate_spec` catching a negative log-format spec case (for example deferred without gate or empty history), `releases.create_release` followed by `releases.validate_release` and `check_engine.check_content(..., "releases")` returning `[]`, and `releases.check_from_backlog` reporting `check.from-backlog-malformed` and `check.from-backlog-dangling` on log-format fixtures.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste F-02 (audit across all five areas) and observed outputs on `.aw/state/szykgd/scratch` (code paths updated by E-03) showing `check_engine.check_plan_spec_link_missing` flagging a log-format plan citing a known spec in `## Concern` (and exempting it when log-stored `scope_paths` lists that spec), `aw search` without `-F` matching a log-stored backlog/research summary while excluding a body-only token, and `ipd_dependency_statement_gate.check` returning exit 1 when only `meta/<id6>.jsonl` is staged with a cyclic or dangling dependency.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the full `python3 -m pytest -o addopts="" -m '' -v tests/test_cutover_log_checkers.py` output in `.aw/state/szykgd/scratch` showing every test PASSED across specs, releases, spec-link checks, `aw search`, and `ipd_dependency_statement_gate`.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `git apply --stat .aw/system/cutover/metastore-code.cutover.patch`, the `python3 -m pytest -o addopts="" tests/test_metastore_cutover_code_patch.py` run with all 3 tests PASSED, `git worktree list` showing `.aw/state/szykgd/scratch` removed, `git status --short` confirming no live edits outside `- Scope-Paths:`, and the `aw commit szykgd` output naming the commit hash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after `/plan-review`, human approval (`Status: approved`), and after every plan in `- Item-Dependencies:` (`cugg3w`) is executed; open questions: none open. Code and tests are edited ONLY inside `.aw/state/szykgd/scratch` and packaged into `.aw/system/cutover/metastore-code.cutover.patch`. Scope fence: `- Scope-Paths:` is a declaration; any needed edit outside it must be justified at finalize (`--scope-reason`), and any declared path left unmodified must be acknowledged (`--scope-ack`). Safety stop conditions: stop and report rather than editing live production code outside the scratch worktree or weakening test assertions if a patch hunk rejects, an unexpected failure occurs on unmodified code, or an unresolvable concurrent-edit conflict occurs. Honesty rule: you MUST paste the ACTUAL runner output of every command named in V-01 through V-05; never claim a result you did not run. Commits: commit only through `aw commit szykgd -- <paths>`; never push. Lifecycle transition: after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence, in a managed runner lane stop after committing the updated plan and let the runner run `aw ipd finalize`; in a hand-run session run `aw ipd finalize` to move the plan to `.aw/records/plans/executed/` (never use a raw `git mv` to `executed/`).
