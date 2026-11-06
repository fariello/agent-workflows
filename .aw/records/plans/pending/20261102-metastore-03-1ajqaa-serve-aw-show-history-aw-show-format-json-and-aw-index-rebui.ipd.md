# IPD: Serve aw show --history, aw show --format json and aw index rebuild through artifact_meta

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` 4.8 requires `--history` and `--format json` on the EXISTING `aw show` command, and 4.5 requires `aw index rebuild` with `aw index plans|research|prompts` kept as aliases; section 7 phase A step 2 serves all three through the new interface. None exists today: measured 2026-11-02, `aw show` (`cli._run_show`) accepts only `action_ref` and `--dir` and prints whole file text (it has no `--history` and no `--format`), and `aw index <type>` (`cli._run_noun_verb` through `artifact_types.TYPE_BACKENDS`) dispatches to `plans_index.run_index`, `research_index.run_index` and `prompts_index.run_index`, which write `INDEX.json`/`INDEX.md` files; there is no `rebuild` verb. Without `aw show --history` an operator has no command that shows an artifact's history once `## Workflow history` sections are removed at the cutover (4.1), and AC-2 (a `--depth 1` clone shows full state and history) has no command to demonstrate it with.
- Scope: Add `aw show <ref> --history` and `aw show <ref> --format json`, both answered by `artifact_meta.read`, `artifact_meta.history` and `artifact_meta.resolve`; add `aw index rebuild`, which rebuilds the cache through `artifact_meta`; keep the three typed `aw index` spellings working exactly as today in phase A while ALSO refreshing the cache, deferring their alias conversion to the plan that deletes INDEX files; prove AC-2 on a migrated-copy fixture. EXCLUDES changing the default (no-flag) `aw show` output, deleting INDEX files or their `--check` drift checks (Order 11), moving any other reader (Orders 08/09), and the migration itself (Order 04).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/artifact_types.py, agent_workflows/command_surface.py, agent_workflows/meta_cli.py, tests/conformance_matrix.py, tests/test_cli_show.py, tests/test_show_history.py, tests/test_index_rebuild.py, tests/test_show_history_clone.py, docs/cli-output-contract.md, CHANGELOG.md, .aw/records/plans/pending/20261102-metastore-03-1ajqaa-serve-aw-show-history-aw-show-format-json-and-aw-index-rebui.ipd.md
- Item-Dependencies: executed:tve77h
- Status: reviewed
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 3
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 1ajqaa
- Readiness: go-pending-approval
- Review-Depth: standard

## Workflow history
- 2026-11-06 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 FIXED
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 FIXED; review record .aw/records/reviews/20261102-metastore-03-1ajqaa-serve-aw-show-history-aw-show-format-json-and-aw-index-rebui.review.md
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Give operators and agents the read commands that replace inline history and INDEX files (`aw show --history`, `aw show --format json`, `aw index rebuild`), served only through `artifact_meta`, so later plans can delete the old surfaces without leaving a gap.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline

- [ ] E-01 Record the baseline: save the stdout and exit code of `aw show f36de0`, `aw show f36de0 --agent`, `aw show f36de0 --json`, `aw show nosuch1 --agent` and `aw index plans --check --agent` to `.aw/state/1ajqaa/before/` (gitignored and inside the workspace; a runner lane may refuse writes outside it), run `python3 -m pytest -o addopts="" -n auto tests/test_cli_show.py tests/test_index_write_agent_records.py tests/test_index_check_agent_records.py tests/test_plans_index.py` and save its summary line, and save `aw check --agent` to `.aw/state/1ajqaa/before/check.jsonl`.
  - Depends on: none
  - Expected outcome: five saved outputs, a passing named test run, and an `aw check` baseline.
  - Execution state: pending

### Task group 2: aw show

- [ ] E-02 Create `agent_workflows/meta_cli.py` with `show_history(repo_root, ref) -> CommandResult` and `show_json(repo_root, ref) -> CommandResult`. Both resolve `ref` with `artifact_meta.resolve` (an id6, a filename or a path; a selector that matches several records returns every match). `show_history` returns, per match, the `history(id6)` events in `seq` order with `seq`, `at` (or the legacy `observed_day`), `op`, `from`/`to` for a transition, the actor (`tool`, `model`, `by_human`) and `message`; an imported legacy line is rendered through `attention_contract.neutralize_control_characters` (4.2, SR-903: display paths never print imported text raw). Showing an old filename with its current name appended (AC-41 (4)) is NOT done here; it needs the cutover rename map and is deferred to `dcerjg` (see Deferred). `show_json` returns the replayed `State` (all registry fields, `status`, `path`, `set`, `order`, `short_description`, `valid`, `defect`) plus `history` when requested. An invalid record returns its `defect` and exit 2; an unknown selector keeps today's refusal (`cli.selector_tokens_naming_no_artifact` and `cli.emit_zero_match_selector_refusal`).
  - Depends on: E-01
  - Expected outcome: calling `show_history` on a fixture artifact returns its events in `seq` order; an imported line containing a control character is returned with U+FFFD in its place; an invalid fixture returns exit 2 naming the defect.
  - Execution state: pending

- [ ] E-03 Wire two flags onto the existing `aw show` parser in `cli.py`, with no second `show` command (4.8). The flags are `--history` (store_true) and `--format {text,json}` with `default=None` (NOT `text`): `result_types.select_output` raises `ConflictingFlagsError` whenever `args.format` is non-None and not `json` beside `--agent` or `--json` (measured at review: `Namespace(agent=True, format='text')` raises), so a `text` default would break every existing `aw show <ref> --agent` and `--json` call; `None` and an explicit `--format text` both mean the human view. In `cli._run_show` the no-flag path stays unchanged, `--history` renders `meta_cli.show_history` (a human table, or the `aw.agent/v1` result under `--agent`/`--json`), and `--format json` emits `meta_cli.show_json` (including the history list when `--history` is also given). The `command_surface` `show` declaration's `legacy_flags` and the help epilog gain the two flags and two examples (`aw show <id6> --history`, `aw show <id6> --format json`). `tests/test_cli_show.py` keeps its six existing tests unchanged and gains one CLI case per flag.
  - Depends on: E-02
  - Expected outcome: `aw show <fixture-id6> --history` prints one row per event; `aw show <fixture-id6> --format json` parses with `json.loads` and has `status` and `fields`; the no-flag, `--agent` and `--json` outputs on the E-01 fixtures are byte-identical to the baseline; `aw show <id6> --agent --format json` exits 2 with the existing conflicting-flags refusal.
  - Execution state: pending

- [ ] E-04 Add `tests/test_show_history.py` (marked `core`) driving `cli.main` in temp repositories: (a) a legacy-format plan with tool-prepended and author-appended history lines shows them in file order with no inferred transition; (b) a synthetic log-format artifact (its `meta/<id6>.jsonl` written by the test from `artifact_meta.encode_event` lines plus a two-key front-matter mirror, NOT through `artifact_meta.create`/`append`, because `2xwb9b` later makes `append` write the legacy format while the repository is unmigrated, which would silently stop producing a log) shows events in `seq` order even when the log lines are shuffled on disk; (c) a review file's rounds appear as `review` events of the SUBJECT, not as a separate record; (d) `--format json` round-trips through `json.loads`; (e) a corrupted log makes `aw show --history` exit 2 and name the defect, never print stale events; (f) a missing cache (`.aw/state/index.db` deleted) gives the same output as a warm one; (g) a staged edit to the log appears on the next call with no rebuild.
  - Depends on: E-03
  - Expected outcome: a passing core module whose assertions are on CLI stdout, exit code and parsed JSON.
  - Execution state: pending

### Task group 3: aw index rebuild

- [ ] E-05 Add `meta_cli.index_rebuild(repo_root) -> CommandResult`, which deletes and rebuilds the cache through `artifact_meta` (a full freshness pass from empty) and reports the counts of artifacts, walkthroughs, review files, events, valid and invalid records, plus the cache path; it writes no tracked file. Register `rebuild` so `aw index rebuild` reaches it: the `aw index` parser takes `type` as its first positional, so `cli._run_noun_verb` routes the token `rebuild` to `meta_cli.index_rebuild` BEFORE type normalization (no record type is named `rebuild`; `artifact_types.ARTIFACT_TYPES` measured), and `artifact_types` gains no `rebuild` type. Update the `aw index` help text and the `command_surface` `index` declaration.
  - Depends on: E-01
  - Expected outcome: `aw index rebuild --agent` emits one `result` record with `outcome` `ok` and the counts; `git status --porcelain` is unchanged after it; `aw index rebuild` with a damaged `index.db` succeeds.
  - Execution state: pending

- [ ] E-06 Make the three typed spellings refresh the cache too, without changing what they print or write: after `aw index plans`, `aw index research` or `aw index prompts` (and `aw index all`) completes its existing INDEX work, call `artifact_meta`'s freshness pass so the cache is current. The call sits in `cli._run_noun_verb` after the per-type loop for `verb == "index"` without `--check` (so `plans_index.py`, `research_index.py` and `prompts_index.py` are not edited), and it is best effort: a cache or source error from the refresh is swallowed, so it changes neither the output nor the exit code of the typed spelling (`aw index rebuild` is the command that reports invalid records). Their `--check` drift checks, their INDEX files and their output stay byte-identical in phase A. Converting them into informational aliases of `aw index rebuild` and deleting INDEX files is deferred to the plan that deletes the INDEX code (C10a: `main` must keep one working behavior per commit, and `aw find`/`attention` still read INDEX-adjacent code until Orders 08/09).
  - Depends on: E-05
  - Expected outcome: the E-01 `aw index plans --check --agent` output is byte-identical after the change; the existing index test modules pass unchanged; in a fixture with one invalid log, `aw index plans --agent` output and exit code equal those of the same fixture without the log.
  - Execution state: pending

- [ ] E-07 Add `tests/test_index_rebuild.py` (marked `core`): (a) `aw index rebuild --agent` on a fixture repository reports the right counts and creates `<state>/index.db`; (b) it writes no tracked file (`git status --porcelain` before and after); (c) a garbage `index.db` is replaced and the command exits 0; (d) after `aw index plans`, an `artifact_meta.query()` reflects a plan added just before the call; (f) an invalid log does not change the output or exit code of `aw index plans`; (e) `aw index rebuild` in a repository with one invalid log reports `invalid: 1`, exits 1 (findings), and names the record.
  - Depends on: E-06
  - Expected outcome: a passing core module asserting on exit codes, parsed JSON and filesystem state.
  - Execution state: pending

### Task group 4: clone demonstration and contract

- [ ] E-08 Add `tests/test_show_history_clone.py` (marked `core`) for AC-2 on a migrated-copy fixture: build a temp repository, write one plan's metadata in the LOG format as four `artifact_meta.encode_event` lines in `meta/<id6>.jsonl` (a `create`, a transition to `to-review`, a `set` of `blocks_release`, a gate `review` event; written directly for the E-04 (b) reason), plus its two-key front matter mirror; commit; `git clone --depth 1 file://<repo> <clone>`; run `aw show <id6> --history --agent` in the clone with no `.aw/state/` directory; assert the four events, their `seq` order, and the replayed status. This uses Order 02's event encoder and loader directly; it does not depend on `aw migrate metadata` (Order 04) or on which format `append` writes. Order 13 re-demonstrates AC-2 on the real repository after the cutover.
  - Depends on: E-04
  - Expected outcome: the clone shows the full state and history with no cache present beforehand.
  - Execution state: pending

- [ ] E-09 Update `docs/cli-output-contract.md` (the `aw show` and `aw index` entries: the two new flags, `aw index rebuild`, exit codes 0/1/2), keep the conformance sweep green (no `RUNNABLE_ARGV` key is added: `RUNNABLE_ARGV` is keyed by parser LEAF and `index rebuild` and `show --history` are a positional value and a flag of the existing `index` and `show` leaves, so such keys would never be read; behavioral coverage is E-04 and E-07, and `tests/conformance_matrix.py` changes only if the sweep fails), and add one `CHANGELOG.md` entry, with no em or en dashes in user-facing prose.
  - Depends on: E-04, E-07
  - Expected outcome: `tests/test_agent_surface_conformance.py` and `tests/test_exit_contract_conformance.py` pass; the doc names both flags and the new verb.
  - Execution state: pending

### Task group 5: verification and commit

- [ ] E-10 Verify and commit: rerun the E-01 commands and diff the no-flag `aw show` and `aw index plans --check` outputs against the baseline (must be identical); run `python3 -m pytest -o addopts="" -n auto tests/test_show_history.py tests/test_index_rebuild.py tests/test_show_history_clone.py tests/test_cli_show.py tests/test_index_write_agent_records.py tests/test_index_check_agent_records.py tests/test_plans_index.py tests/test_exit_vocabulary_boundary.py tests/test_agent_surface_conformance.py tests/test_exit_contract_conformance.py`, the bare core gate `python3 -m pytest`, `aw check --agent` diffed by `(location, rule)` against `.aw/state/1ajqaa/before/check.jsonl`, and `aw sanitize --agent`; commit through `aw commit 1ajqaa -- <each changed path>`. Never push.
  - Depends on: E-09
  - Expected outcome: both pytest runs pass; outputs unchanged where required; no new `aw check` error or warning; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `aw show` is `cli._run_show`; its parser is built where `p_show` adds `action_ref` and `--dir`; its declaration is `command_surface.CommandDeclaration(command="show", command_class="read", ..., exit_contract=(0, 2))`. A selector naming no artifact exits 2 through `cli.selector_tokens_naming_no_artifact` and `cli.emit_zero_match_selector_refusal` (docs/cli-output-contract.md Section 11.1).
- `aw index <type>` is one of the noun-verb leaves (`check`, `find`, `search`, `index`, `rename`, `group`) dispatched by `cli._run_noun_verb`, which resolves `artifact_types.resolve_backend(type, verb)` from `artifact_types.TYPE_BACKENDS` (`plans_index.run_index`, `research_index.run_index`, `prompts_index.run_index`); its declaration has `exit_contract=(0, 1, 2)`.
- `--format json` is already recognized by the output selector (`cli` scans for `--format json` beside `--json`), and `aw attention` uses `--format {markdown,json}`, so the flag name is established.
- Display of untrusted text uses `attention_contract.neutralize_control_characters` (U+FFFD replacement).
- The conformance harness is `tests/conformance_matrix.py` (`RUNNABLE_ARGV` lists `"show": ["f36de0"]` and `"index": ["plans", "--check"]`).
- Results are `result_types.CommandResult` rendered by `renderers.get_renderer(ctx)`.
- Existing behavior tests for `aw show` live in `tests/test_cli_show.py` (six tests across human, `--agent` and `--json`).

## Findings

| Id | Evidence (measured 2026-11-02 at `0cbfcc706`) | Finding |
|---|---|---|
| F-01 | `aw show --help` lists only `action_ref` and `--dir`; `cli._run_show` prints `p.read_text()` per match | No history or JSON state view exists; the flags are new. |
| F-02 | `aw index --help`: "Rebuild and print the manifest/index for a given artifact TYPE"; `type` is required; `TYPE_BACKENDS` has `index` for plans, research and prompts only | `rebuild` must be routed before type normalization. |
| F-03 | `aw index plans --agent` reports `changes` for `.aw/records/plans/INDEX.json` and `INDEX.md` | The typed spellings write files today; changing that is Order 11's job (AC-9). |
| F-04 | 17 modules import `plans_index`, `research_index` or `prompts_index` (`rg -ln` count) | Turning the typed spellings into aliases now would break readers that still depend on those modules in phase A. |
| F-05 | `rg -n -- "--depth 1" tests` finds no clone test | AC-2 needs a new test. |

## Proposed changes (ordered, validatable)

1. E-01 baseline.
2. `aw show`: `meta_cli` functions, flags, tests (E-02 to E-04).
3. `aw index rebuild`, cache refresh on typed spellings, tests (E-05 to E-07).
4. Clone test, docs and conformance (E-08, E-09).
5. Verify and commit (E-10).

## Deferred / out of scope (with reason)

- Converting `aw index plans|research|prompts` into informational aliases of `aw index rebuild`, and deleting the INDEX files, their `--check` drift checks and `check.stale-index-*`: AC-9 and section 7 step 7.
  - Carrier: 9o83cr
- Moving `aw find`, `aw attention` and the board onto the cache: section 7 step 5.
  - Carrier: ffceq0
- Demonstrating AC-2 on the real migrated repository: section 7 step 9.
  - Carrier: cxxmyv
- `aw meta repair` and `aw check meta` verbs: readers plan.
  - Carrier: ffceq0
- Displaying an old filename resolved to the current one for records the cutover renames (AC-41 (4)): the rename map exists only after the migration.
  - Carrier: dcerjg

## Scope check

- Over-scope: none. `meta_cli.py` is a new module that only calls `artifact_meta`.
- Under-scope: none. Section 4.8 (flags on the existing `aw show`, no second command), 4.5 (`aw index rebuild` with the typed spellings kept), and section 7 step 2 are covered; the alias conversion is deliberately deferred with a carrier because C10a forbids changing the typed spellings' behavior before their readers move.

## Required tests / validation

New core modules: `tests/test_show_history.py`, `tests/test_index_rebuild.py`, `tests/test_show_history_clone.py`; extended: `tests/test_cli_show.py`, `tests/conformance_matrix.py`. All drive the real CLI and assert on stdout, exit codes, parsed JSON and filesystem state; none reads source.

Acceptance criteria of `4sd62s`:
- OWNS AC-2, proven here on a log-format fixture committed and cloned with `--depth 1` (E-08); Order 13 re-demonstrates it on the real repository after the cutover, as the spec's evidence column names a migrated plan.
- CONTRIBUTES to AC-1a: `aw show <id6> --history` gives the same result with cold, warm, deleted and corrupt caches, and an external log edit appears on the next read (E-04 (e), (f), (g)); the owner is the reader plans.
- CONTRIBUTES to AC-8 and AC-23 through `aw index rebuild` exercising a full rebuild (E-07).

Commands: E-10's named pytest run, the bare core gate, `aw check`, `aw sanitize --agent`.

## Spec / documentation sync

No spec change; implements `4sd62s` 4.8 (`aw show --history`, `--format json`), 4.5 (`aw index rebuild`, the typed spellings retained) and section 7 phase A step 2. `docs/cli-output-contract.md` and `CHANGELOG.md` gain entries for the new flags and verb, because they describe commands that exist on `main` after this plan merges (C10a allows this; it forbids only documents describing post-cutover behavior).

## Open questions

### OQ-01: Should the typed `aw index <type>` spellings become aliases now?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. 4.5 makes them aliases that "print an information message", but in phase A they still produce the INDEX files that 17 modules' code paths sit beside (F-04), and C10a requires each merge to keep `main` working with one behavior. This plan makes them ALSO refresh the cache; Order 11, which deletes INDEX code (AC-9), converts them. Recommendation strength: strong.

### OQ-02: What does `aw show --history` print before the cutover?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: In phase B the legacy loader serves `history()` from the `## Workflow history` lines in file order with no inferred `seq` order or transitions (Order 02 E-12), and from logs when a log exists. The command's contract is the same in both formats; only the source differs, which 3c states. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls .aw/state/1ajqaa/before/` listing the five saved outputs with their exit codes, the summary line of the named baseline pytest run, and and `ls -l .aw/state/1ajqaa/before/check.jsonl`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_show_history.py -k meta_cli` with every selected test PASSED, and quote the assertion that an imported history line containing `\x07` is returned with `\ufffd` in its place.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw show --help` showing `--history` and `--format {text,json}`; `diff` of the no-flag `aw show f36de0`, `--agent` and `--json` outputs against the E-01 baseline (empty); `aw show f36de0 --agent --format json` exit code (2) and its refusal text; and `python3 -m pytest -o addopts="" -v tests/test_cli_show.py` with all tests PASSED, the original six included by name.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_show_history.py` with every test PASSED, one named test for each of cases (a) to (g) in E-04, and quote the case (b) fixture code that writes the log with `encode_event`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `aw index rebuild --agent` result record from a fixture repository (counts present, `outcome` ok), `git status --porcelain` before and after (identical), and the `aw index --help` line naming `rebuild`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `diff` of `aw index plans --check --agent` stdout against the E-01 baseline (empty) and `python3 -m pytest -o addopts="" tests/test_index_write_agent_records.py tests/test_index_check_agent_records.py tests/test_plans_index.py` summary line (all passed).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_index_rebuild.py` with every test PASSED, one named test for each of cases (a) to (f) in E-07, and quote the assertion on exit code 1 and `invalid: 1` for case (e).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_show_history_clone.py` with every test PASSED, and quote the assertions that the clone was made with `--depth 1`, that no `.aw/state` existed in the clone before the call, and that four events were returned in `seq` order.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the `git diff` of `docs/cli-output-contract.md` and `CHANGELOG.md`, `rg -n "[\u2013\u2014]"` over both diffs' added lines (no match), and the summary line of `python3 -m pytest -o addopts="" tests/test_exit_vocabulary_boundary.py tests/test_agent_surface_conformance.py tests/test_exit_contract_conformance.py` (all passed).
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste the summary line of the E-10 named pytest run; the bare `python3 -m pytest` summary line; the two empty baseline diffs (no-flag `aw show`, `aw index plans --check`); the `(location, rule)` diff of `aw check --agent` against `.aw/state/1ajqaa/before/check.jsonl` (no new error or warning, each other difference named with its cause); the `aw sanitize --agent` result record; and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `tve77h` is executed. All open questions are resolved. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified (for example `tests/conformance_matrix.py` or `agent_workflows/artifact_types.py` when no change is needed) is acknowledged (`--scope-ack`). Commit only through `aw commit 1ajqaa -- <paths>`; never `git add -A`, a bare `git add`, or `git commit -a`, and never push. Run the bare `python3 -m pytest` core gate and the E-10 named modules, and paste the ACTUAL summary lines; never claim a result you did not run. Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 1ajqaa` itself.
