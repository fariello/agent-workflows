# IPD: Save the read_at split baseline and move the check_engine and hook git readers onto read_at

- Date: 2026-11-09
- Kind: child
- Concern: Split from `h58z9n` (Order 33) in round 3 of the metastore re-split, per research `nj8zdp` guidance (at most 5 E-items, 8 work Scope-Paths, about 8 named units per item): `h58z9n` declared 11 work Scope-Paths and its E-01 and E-04 named 9 and 11 units. Spec `4sd62s` 4.4 requires every reader of a HEAD, staged or branch revision to call `artifact_meta.read_at` instead of parsing git content, and C5a requires every gate and hook to read metadata through the cache. Measured 2026-11-07 at `ac76110f4`: `check_engine._blob_text` (`git show <ref>:<path>`, `:0:<path>`) has 12 call sites in 6 functions, `check_engine._status_meta` has 35 call sites in 13 functions, and `hooks/executed_transition_gate` reads blobs with its own `_blob_at`.
- Scope: (a) Save the split-wide `aw check all --agent` baseline that must precede every code edit of the `t4gl15` family (formerly part of `h58z9n` E-01) and record it as table F-10 here. (b) The 4.4 search rows for `check_engine` and the two blob-reading hooks (the rest of `h58z9n` E-01's file subset goes to `iqhzse`). (c) `h58z9n` E-02: the `check_engine` git-content readers. (d) `h58z9n` E-03: the four hooks. EXCLUDES: the setter, staleness, lifecycle and runner merge-path readers (`iqhzse`, Order 146); the residual audit (kept in `h58z9n`); everything else of `t4gl15`.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/hooks/executed_transition_gate.py, agent_workflows/hooks/ipd_dependency_statement_gate.py, agent_workflows/hooks/status_untooled_gate.py, agent_workflows/hooks/backlog_blocking_close_gate.py, tests/test_readers_read_at_gates.py, .aw/records/plans/pending/20261109-metastore-145-snh19k-save-the-read-at-split-baseline-and-move-the-check-engine-an.ipd.md
- Item-Dependencies: executed:ffceq0, executed:g5hpbb, executed:tve77h, executed:xexn45
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 145
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: snh19k

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from h58z9n (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The `check_engine` gates and the four hooks that read metadata out of a git revision read it through `artifact_meta.read_at`, with each verdict pinned by a behavioral test before and after the move, and the `aw check all` rule-id baseline of the whole `t4gl15` family is saved in a tracked table before any code edit.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

The pin-first rule of `ffceq0` applies to every move here (carried from `t4gl15` through `h58z9n`): BEFORE the edit, a behavioral test in the named module pins the reader's current observable behavior (the ledger in `## Findings`) and runs green on the unmodified code; AFTER the edit, the same test runs unchanged. A test that must change is a behavior change and must be one of the decisions copied below (D-1, D-2). For every existing module named as a baseline, save the per-test outcome list under the gitignored `.aw/state/t4gl15/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/t4gl15/<E>-before.txt`) before the move and the same command into `<E>-after.txt` after it, where `<E>` is the ORIGINAL `t4gl15` item id named in each item below; `diff` of the two prints nothing except lines a named decision explains. Run a new module's `-k` selection as its own command, never combined with baseline module paths. Every saved baseline goes under `.aw/state/t4gl15/`, never `/tmp`. New test modules set `pytestmark = pytest.mark.core` unless they need real `git` subprocesses across many commits, in which case they are marked `slow` and run in `make test-all`; none reads production source.

Commit through `aw commit snh19k -- <each changed path>`, one commit per item allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push.

### Task group 1: baseline and search rows

- [ ] E-01 (carried from `h58z9n` E-01, baseline half) Before any code edit of the `t4gl15` split (this plan is the first part; every other part of the family depends on it directly or through `h58z9n`), save the sorted rule-id counts of `aw check all --agent` (one `rule` per diagnostic) to `.aw/state/t4gl15/check-before.txt` and paste those counts into this plan as table F-10, so that the last part (`t4gl15` E-15) can compare against them even when this plan ran in an isolated lane worktree whose gitignored `.aw/state/` is not carried back.
  - Depends on: none
  - Expected outcome: `check-before.txt` is saved and F-10 holds its rule-id counts.
  - Execution state: pending

- [ ] E-02 (carried from `h58z9n` E-01, search half, gate-file subset) Re-run the 4.4 search for git-content readers over `agent_workflows/check_engine.py`, `agent_workflows/hooks/executed_transition_gate.py` and `agent_workflows/hooks/ipd_dependency_statement_gate.py` (21 of the 44 `h58z9n` hits at `ac76110f4`: `check_engine` 11, `hooks/executed_transition_gate` 8, `hooks/ipd_dependency_statement_gate` 2), with `rg -n -e '"show"' -e 'cat-file' -e '"ls-files", "-s"' -e '"--cached"' -e '":0:"' -e 'rev-parse' <those three files>`, and record the result as table F-03 here, classifying each hit as metadata reader (moves to `read_at`), path-only reader (no change), or not a metadata read. Any metadata reader not in the 4.4 list is added to E-03 or E-04. (`status_set.py` has no direct hit, because it reads through `check_engine._blob_text`; its row and the `plan_readiness`, `ipd_lifecycle` and `artifact_meta` rows are written by `iqhzse`.)
  - Depends on: E-01
  - Expected outcome: F-03 lists every hit in the three files with its class; every metadata-reader row names E-03 or E-04.
  - Execution state: pending

### Task group 2: read_at gates and hooks

- [ ] E-03 (carried from `h58z9n` E-02) Pin, then move, the `check_engine` git-content readers onto `artifact_meta.read_at`: `_blob_text` and `_status_meta` stop being called by `check_status_untooled`, `check_status_untooled_range`, `check_staged_illegal_backlog_transition`, `_lane_carrier_is_executed`, `_staged_backlog_done_items` and `check_release_gate_consistency`, which call `read_at(id6, ":0:")`, `read_at(id6, "HEAD")` or `read_at(id6, <commit>)` and compare the returned `State`s. The phase-B rule shapes stay (4.4 rewrites them only after the cutover): "status changed with no matching tool-authored history line" compares `read_at` states and their `history` rows; a renamed or moved record is resolved INSIDE each revision, so a staged rename compares the HEAD record at its old path with the staged record at its new path. Pin in `tests/test_readers_read_at_gates.py` (real `git init` fixtures: an untooled status flip refused, a tooled one accepted, a staged rename into `executed/`, an illegal backlog transition, a release-blocking `done` with and without a handoff), and run `tests/test_check_engine_status_meta.py`, `tests/test_check_engine_release_gate.py`, `tests/test_precommit_scope_gate_severity.py` and `tests/test_backlog_close_gate_prose.py` green before and after (outcome lists `E-02-before.txt`/`E-02-after.txt`).
  - Depends on: E-02
  - Expected outcome: every listed test passes before and after; `check_engine` no longer calls `_blob_text` from these six functions (the remaining callers, `hooks.ipd_dependency_statement_gate._staged_ipd_overlay` and `status_set._prepare_status_change`, move in E-04 and in `iqhzse`).
  - Execution state: pending

- [ ] E-04 (carried from `h58z9n` E-03) Move the four hooks onto `read_at`: `executed_transition_gate` (`_blob_at`, `_has_executed_status`, `_plan_id_of`, `_staged_plan_executed_transitions` call `read_at` for `HEAD` and `:0:`; "an executed transition" stays "the staged status is terminal and the HEAD status is not"); `ipd_dependency_statement_gate._staged_ipd_overlay` (staged status and Item-Dependencies from `read_at(id6, ":0:")`); `status_untooled_gate` and `backlog_blocking_close_gate` keep delegating to the moved `check_engine` rules. Pin in `tests/test_readers_read_at_gates.py` through the real CLI entry points (`aw ipd-executed-gate`, `aw ipd-status-untooled-gate`, `aw backlog-blocking-close-gate`, `aw ipd-dependency-statement-gate`) on staged fixture repositories, and run `tests/test_executed_transition_gate.py`, `tests/test_executed_transition_gate_e2e.py` and `tests/test_ipd_dependency_statement_gate.py` green before and after (outcome lists `E-03-before.txt`/`E-03-after.txt`).
  - Depends on: E-03
  - Expected outcome: each hook refuses and accepts the same fixtures before and after with the same exit codes; no hook module contains a `^-` metadata regex or a `git show` of a record.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

Carried from `h58z9n` Step 0:

- Interface names from Order 02 (`tve77h`), used exactly: `artifact_meta.read(id6) -> State`, `artifact_meta.history(id6)`, `artifact_meta.query(...)`, `artifact_meta.resolve(path_or_id6)`, and `artifact_meta.read_at(id6, rev)`, which runs git in the repository that owns the resolved records root, resolves the record's path inside that revision (`git ls-files -s` for the index, `git rev-parse <rev>:<path>` for a commit), caches by blob sha in `rev_log_states`/`rev_mirrors`, feeds a miss to the same loader, fails closed on a validation error, and returns distinct results for an absent record, an invalid revision and an unversioned placement.
- Today's git-content helpers: `check_engine._blob_text(repo_root, ref, path)` and `check_engine._status_meta(text)`; `hooks.executed_transition_gate._blob_at`.
- The hooks are thin: `hooks.status_untooled_gate.check` delegates to `check_engine.check_status_untooled`, and `hooks.backlog_blocking_close_gate.check` filters `check_engine.check_release_gate_consistency`; both are dispatched by `cli` and installed as optional pre-commit hooks from the `engine` template.
- Cite code by SYMBOL (`module.function`), never a bare line number (advisory `IPD-C801`).

## Findings

Measured 2026-11-07 at `ac76110f4` (the round-1 split measurement, carried from `h58z9n`).

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -n "_blob_text\(\|_status_meta\(" agent_workflows` prints 39 lines: the two definitions, 12 `_blob_text` calls (in `check_status_untooled`, `check_status_untooled_range`, `check_staged_illegal_backlog_transition` 8, `_lane_carrier_is_executed`, `check_release_gate_consistency`, `hooks.ipd_dependency_statement_gate._staged_ipd_overlay`, `status_set._prepare_status_change`) and `_status_meta` calls in 13 functions | E-03 moves 6 `check_engine` callers; E-04 the hook caller; `iqhzse` the setter caller. |
| F-03 | (written by E-02) the re-run 4.4 search over this plan's three files, each hit classified | 4.4 says the list is a minimum. |
| F-10 | (written by E-01) rule-id counts of `aw check all --agent` before any edit of the `t4gl15` split | Baseline for `t4gl15` E-15. |

Size (round 3): measured with `ipd_schema.count_named_units`, each item names at most 8 distinct units; 6 work Scope-Paths.

READER LEDGER (this part's rows, copied from `t4gl15` through `h58z9n`):

| Reader | Prior behavior | Pinning test | After |
|---|---|---|---|
| `check_engine.check_status_untooled` and `_range` | HEAD vs staged `- Status:` via `_blob_text` + `_status_meta`; refuse with no matching history line | E-03 fixtures; `tests/test_check_engine_status_meta.py`, `tests/test_precommit_scope_gate_severity.py` | same verdicts via `read_at` states and their history |
| `check_engine.check_staged_illegal_backlog_transition`, `_staged_backlog_done_items`, `check_release_gate_consistency`, `_lane_carrier_is_executed` | staged/HEAD backlog and carrier status via git blobs | E-03 fixtures; `tests/test_check_engine_release_gate.py`, `tests/test_backlog_close_gate_prose.py` | same via `read_at` |
| `hooks.executed_transition_gate` | case-insensitive region `status: executed\|done`, `- Id:` outside fences, finalize evidence | `tests/test_executed_transition_gate.py`, `tests/test_executed_transition_gate_e2e.py` | same via `read_at`; D-2 for case |
| `hooks.ipd_dependency_statement_gate` | staged `- Status:` and `Item-Dependencies` overlay | `tests/test_ipd_dependency_statement_gate.py` | same via `read_at(":0:")` |

DECISIONS that govern this part (copied from `t4gl15`, whose text is authoritative; `t4gl15` D-1 applies `ffceq0` D-1):

- D-1 (multi-word status). PLAN records return the canonical normalized status (`plans.normalize_status` of the first token); every other type keeps its raw single-token status, because `plans.normalize_status` maps `open`, `implemented`, `planned` and similar non-plan values to `legacy/unknown`.
- D-2 (status case in `executed_transition_gate`). The hook matches `status: executed|done` case-insensitively; the cached status is canonical lower-case (`EXECUTED`/`DONE` normalize to `executed`), so the hook's verdict is unchanged for every input the old regex accepted.

## Proposed changes (ordered, validatable)

1. Save the split-wide baseline (E-01) and the gate-file 4.4 rows (E-02).
2. Pin then move the `check_engine` git readers (E-03) and the hooks (E-04).

## Deferred / out of scope (with reason)

- The 4.4 search rows for `status_set`, `plan_readiness`, `ipd_lifecycle` and `artifact_meta`, and the setter, staleness, lifecycle and runner merge-path readers.
  - Carrier: iqhzse
- The residual audit of the hook, readiness and lifecycle modules.
  - Carrier: h58z9n
- Deleting `check_engine._blob_text` and `_status_meta`.
  - Carrier: 9o83cr

## Scope check

- Over-scope: none. `hooks/status_untooled_gate.py` and `hooks/backlog_blocking_close_gate.py` change only if their delegation needs an argument change; otherwise they are acknowledged unmodified at finalize.
- Under-scope: none known. This part carries the baseline and gate-file search half of `h58z9n` E-01, and `h58z9n` E-02 and E-03, unchanged.

## Required tests / validation

New test module `tests/test_readers_read_at_gates.py` (core unless real multi-commit git fixtures exceed the core budget, then `slow` with the reason in the module docstring); `iqhzse` adds one more case to it. CONTRIBUTES to `4sd62s` AC-16 and AC-33. Commands: every module named in E-03 and E-04, the bare core gate `python3 -m pytest`, `aw sanitize --agent`.

## Spec / documentation sync

No spec change. Implements the gate and hook part of `4sd62s` 4.4 and C5a.

## Open questions

### OQ-01: Where do the split-wide baselines live?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `.aw/state/` is gitignored, so a baseline saved inside an isolated lane worktree does not reach a later plan. E-01 therefore also pastes the `aw check all --agent` rule-id counts into this plan (F-10), which is tracked; `t4gl15` E-15 compares against F-10. Carried from `h58z9n` OQ-01. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff --stat agent_workflows/` empty at the time the baseline was taken, `ls -l .aw/state/t4gl15/check-before.txt`, and the F-10 table written into this plan (one row per rule id with its count).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the exact `rg` command of E-02 with its output line count, and the F-03 table with one row per hit and a class column (metadata reader / path-only / not a metadata read); every metadata-reader row names E-03 or E-04.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff --stat agent_workflows/check_engine.py` empty before the move, then `python3 -m pytest -o addopts="" -v tests/test_readers_read_at_gates.py -k check_engine` all PASSED (untooled flip refused, tooled flip accepted, staged rename into `executed/`, illegal backlog transition, release-blocking done with and without handoff) and `diff .aw/state/t4gl15/E-02-before.txt .aw/state/t4gl15/E-02-after.txt` (outcome lists of `tests/test_check_engine_status_meta.py tests/test_check_engine_release_gate.py tests/test_precommit_scope_gate_severity.py tests/test_backlog_close_gate_prose.py`) printing nothing; paste `rg -n "_blob_text\(" agent_workflows` with each remaining caller named (none of the six E-03 functions).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_read_at_gates.py -k hook` all PASSED, each test driving the real `aw ipd-executed-gate`, `aw ipd-status-untooled-gate`, `aw backlog-blocking-close-gate` or `aw ipd-dependency-statement-gate` leaf on a staged fixture and asserting the exit code; `diff .aw/state/t4gl15/E-03-before.txt .aw/state/t4gl15/E-03-after.txt` (outcome lists of `tests/test_executed_transition_gate.py tests/test_executed_transition_gate_e2e.py tests/test_ipd_dependency_statement_gate.py`) printing nothing; and `rg -n "\^-|\"show\"" agent_workflows/hooks/` showing no metadata regex or record `git show`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every `- Item-Dependencies:` edge is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every reader move is pin-first.

Honesty rule: run the named modules and `python3 -m pytest` (core gate), and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit snh19k -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
