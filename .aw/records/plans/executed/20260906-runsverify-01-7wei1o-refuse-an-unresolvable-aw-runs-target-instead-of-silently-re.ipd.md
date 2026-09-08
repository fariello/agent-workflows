# IPD: Refuse an unresolvable aw runs target instead of silently reporting success

- Date: 2026-09-06
- Kind: child
- Concern: `aw runs <token>` treats any first positional that is not a registered leaf name as a run-id/setid/substring TARGET. When that token resolves to nothing it is silently dropped and the command still exits 0, so a mistyped or not-yet-built subcommand reports success having done nothing. The measured case that matters: `aw runs verify <run-id>` renders an ordinary report and exits 0 while verifying nothing, and until 2026-09-05 the spec and seven shipped recovery messages told operators to run exactly that.
- Scope: Make an unresolvable target a nonzero refusal that names the registered leaves and the closest match, while preserving every currently-working invocation (a real run id, a setid, a bare `aw runs`, the viewer flags, the `--` escape hatch, and a legitimate leaf-name collision). Also narrow the OVER-MATCHING resolver that makes the refusal reachable in the first place: the `state.json` substring fallback matches any quoted JSON token anywhere in the file, so `status`, `run`, `main` and `clean` each "resolve" to 96-106 of 106 runs today and would be silently exempted from the refusal.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/run_viewer.py, tests/test_run_viewer.py, tests/test_run_noun_split.py, tests/test_cli_conformance_matrix.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: runsverify
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 7wei1o
- From-Backlog: 6kq1lj
- Blocks-Release: next

## Workflow history
- 2026-09-08 executed (opencode/its_direct/pt3-claude-opus-5-1m-us): Lane recovered and merged during the stranded-lane recovery; integration had been refused by the binary whole-repo suite gate (root cause tracked by 32ij2j/xtklpd) [Scope reconciliation - out-of-scope agent_workflows/artifact_refs.py: NOT THIS PLAN'S EDIT. Belongs to 674f2c68 refactor(records): stop committing the generated index manife, a concurrent lane or agent; verified absent from this plan's own commits (9c589d2d b5ea1802). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope agent_workflows/artifact_rename.py: NOT THIS PLAN'S EDIT. Belongs to 674f2c68 refactor(records): stop committing the generated index manife, a concurrent lane or agent; verified absent from this plan's own commits (9c589d2d b5ea1802). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope agent_workflows/attention.py: NOT THIS PLAN'S EDIT. Belongs to d099dc25 feat(att): add --id6-only, --active, --not-active, and --arci, a concurrent lane or agent; verified absent from this plan's own commits (9c589d2d b5ea1802). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope agent_workflows/git_commit_helper.py: NOT THIS PLAN'S EDIT. Belongs to 674f2c68 refactor(records): stop committing the generated index manife, a concurrent lane or agent; verified absent from this plan's own commits (9c589d2d b5ea1802). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope agent_workflows/ipd_lifecycle.py: NOT THIS PLAN'S EDIT. Belongs to 56802c81 merge lane h9cn0y: recover stranded validated work, a concurrent lane or agent; verified absent from this plan's own commits (9c589d2d b5ea1802). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope agent_workflows/plans_archive.py: NOT THIS PLAN'S EDIT. Belongs to 674f2c68 refactor(records): stop committing the generated index manife, a concurrent lane or agent; verified absent from this plan's own commits (9c589d2d b5ea1802). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope agent_workflows/plans_refs.py: NOT THIS PLAN'S EDIT. Belongs to 674f2c68 refactor(records): stop committing the generated index manife, a concurrent lane or agent; verified absent from this plan's own commits (9c589d2d b5ea1802). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope agent_workflows/research_archive.py: NOT THIS PLAN'S EDIT. Belongs to 674f2c68 refactor(records): stop committing the generated index manife, a concurrent lane or agent; verified absent from this plan's own commits (9c589d2d b5ea1802). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope agent_workflows/research_refs.py: NOT THIS PLAN'S EDIT. Belongs to 674f2c68 refactor(records): stop committing the generated index manife, a concurrent lane or agent; verified absent from this plan's own commits (9c589d2d b5ea1802). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope agent_workflows/status_set.py: NOT THIS PLAN'S EDIT. Belongs to 674f2c68 refactor(records): stop committing the generated index manife, a concurrent lane or agent; verified absent from this plan's own commits (9c589d2d b5ea1802). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope tests/test_attention.py: NOT THIS PLAN'S EDIT. Belongs to d099dc25 feat(att): add --id6-only, --active, --not-active, and --arci, a concurrent lane or agent; verified absent from this plan's own commits (9c589d2d b5ea1802). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope tests/test_orchestrator_retirement.py: NOT THIS PLAN'S EDIT. Belongs to 17112e19 merge lane 4r0qp1: recover stranded validated work, a concurrent lane or agent; verified absent from this plan's own commits (9c589d2d b5ea1802). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope tests/test_selfcommit_adoption.py: NOT THIS PLAN'S EDIT. Belongs to 674f2c68 refactor(records): stop committing the generated index manife, a concurrent lane or agent; verified absent from this plan's own commits (9c589d2d b5ea1802). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; in-scope-unmodified tests/test_cli_conformance_matrix.py: acknowledged]
- 2026-09-06 approved (aw set): status set to approved

- 2026-09-06 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review; APPROVE WITH REVISIONS APPLIED; PR-001..PR-008. Structural lint conformed at `--phase author` and `--phase review-finalize`. Re-measured every claim independently at HEAD `de26ef00`, unpiped: all seven of the plan's exit-code claims reproduce exactly. FOUR material additions. (1) PR-001, the one that would have broken the build: `tests/test_run_noun_split.py:280-284` ALREADY ASSERTS the behavior this plan removes (`runs -- no-such-target-xyz` -> rc 0 and the literal `no matching runs found`), and that module was NOT in `Scope-Paths`, so the executor would have hit a red suite outside its fence. Added to the fence with E-06. (2) PR-002: the resolver OVER-MATCHES via a raw `f'"{t_str}"' in content` substring test over the whole `state.json` (`run_viewer.py:1148`), so `status` resolves to 106/106 runs, `run`/`opencode` 106, `main` 96, `execute` 53, `clean` 105, `approved` 46, `verified` 13. Those are not setids; they are ordinary JSON values and keys. Any such token would be silently EXEMPTED from the refusal, which is the same fail-open shape one layer down, so E-07 narrows the fallback to the real setid field. (3) PR-003: `aw runs repair <bogus>` exits 0 having repaired nothing (measured, zero output), a second instance of the defect on the same surface and inside the fence; E-08 fixes it. (4) PR-004: `--agent`/`--json` return `{"runs": []}` at exit 0 (`run_viewer.py:2539-2541`), the path an automated consumer actually reads, so the refusal must be honored in all three renderers, not just the human one.
- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `6kq1lj`, inheriting its `Blocks-Release: next` gate. Every claim below was measured at HEAD `63107a76` WITHOUT a shell pipe, because a piped `$?` reports the last pipeline stage and that exact mistake produced a false sibling finding in `zrzfkw` (corrected in `63107a76`). Measured: `aw runs verify <run-id>` exits 0 and prints the normal report; `aw runs totalgibberish` exits 0 and prints `no matching runs found`; `aw runs totalgibberish <real-run-id>` exits 0 and prints the real run's report with the bogus token silently dropped, which is the worst variant because the operator sees plausible output. Confirmed still-correct behavior that must not regress: a real run id, a setid (`lanectn`), and `--last` all exit 0 today.

## Goal

Make a wrong `aw runs` invocation fail loudly instead of looking like it worked. The specific harm is that an operator (or an agent following a recovery message) asks for an integrity check, receives a normal-looking report and a success exit, and reasonably concludes nothing is wrong.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: detect the unresolvable case

- [x] E-01 In the `aw runs` viewer path, determine per-token whether each requested target RESOLVED to at least one run, and treat "one or more requested tokens resolved to nothing" as a distinct condition from "no targets were requested". `resolve_target_runs` (`run_viewer.py:1095`) currently returns only the union of matches, so an unmatched token is indistinguishable from an absent one by the time the caller sees the result. Return or expose the unresolved token list rather than re-deriving it in the caller, so one function owns the answer.
  - Depends on: none
  - Expected outcome: the caller can name exactly which requested tokens matched nothing, and a bare `aw runs` (no tokens) remains a distinct, non-error case.
  - Execution state: performed

- [x] E-02 Make the unresolvable case exit NONZERO with a message that names the unresolved token, the registered leaves, and the closest leaf match when there is one (`verify` -> `verify-ledger` is a one-edit suggestion and is the case that motivated this plan). Use the existing invalid-invocation exit code rather than inventing one: `run_cli.EXIT_INVALID_INVOCATION` is 2 (`run_cli.py:58`) and `aw runs verify-ledger <absent>` already exits 2 for the analogous "cannot do what you asked" case, so 2 keeps the surface coherent. HONOR THE REFUSAL IN ALL THREE RENDERERS. The empty-state at `run_viewer.py:2538-2543` has a machine branch that returns `{"runs": []}` and exit 0 for `--agent`/`--json` BEFORE the human `no matching runs found` line, and the machine branch is the one an automated consumer reads. A refusal implemented only on the human path leaves the fail-open exactly where it does the most damage. Emit the machine refusal as a conformant `aw.agent/v1` record (`agent_schema.py:21`) carrying the nonzero `exit`, not a bare `{"runs": []}`, because `tests/test_cli_conformance_matrix.py` asserts the agent summary `exit` agrees with the process return code (`tests/test_cli_conformance_matrix.py:9-10`).
  - Depends on: E-01
  - Expected outcome: `aw runs verify <run-id>` and `aw runs totalgibberish` both exit 2 with an actionable message; the human message goes to stderr so it does not pollute a parsed report on stdout, and `--agent`/`--json` emit a nonzero-carrying record instead of an empty success.
  - Execution state: performed

### Task group 2: do not break what works

- [x] E-03 Preserve every currently-working invocation, verified individually rather than assumed: a real run id; a setid (`lanectn` resolves today); a bare `aw runs` with no positionals (means "all runs", must stay exit 0 even when the repository has zero runs, since an empty repository is not an error); every viewer flag (`--last`, `--issues`, `--latest-only`, `--since`, ...); and the `--` escape hatch (`aw runs -- status` means the TARGET named `status`, handled pre-parse in `_dispatch` at `cli.py:10579`). Also preserve the documented AMBIGUITY RULE at `cli.py:652-657`: a first positional equal to a leaf name routes to the LEAF, and the escape hatch is the only way to reach a same-named target. Do NOT invert that precedence while adding the refusal.
  - Depends on: E-02
  - Expected outcome: each listed invocation behaves exactly as it does at `63107a76`, demonstrated case by case.
  - Execution state: performed
  - Re-measured independently at `de26ef00` (unpiped), all exit 0 and all MUST stay exit 0: a real run id; the setid `lanectn`; bare `aw runs`; `--last 1`; `aw runs -- status` (renders 106 runs, i.e. the escape hatch reaches the viewer, and note `aw runs status` WITHOUT the hatch exits 2 from the leaf demanding its target, which is the ambiguity rule working); `--since 2026-09-01`; `--since 7d`; `--since <run-id>`. Also confirmed already-correct and NOT to be changed: `--since bogusdate` exits 2, and the three mutually-exclusive flag pairs exit 2 (`run_viewer.py:2461-2482`).

- [x] E-04 Decide and implement the MIXED case deliberately, and state the choice in the message: `aw runs totalgibberish <real-run-id>` currently prints the real run and exits 0, silently dropping the bogus token. That is the most misleading variant. Refuse it (nonzero, naming the unresolved token) rather than rendering a partial result, because a partially-honored request that looks complete is the defect this plan exists to remove. If the executor concludes partial rendering plus a nonzero exit is better, that is acceptable ONLY if the unresolved token is named prominently on stderr; silently dropping it is not.
  - Depends on: E-02
  - Expected outcome: a mixed invocation cannot exit 0; the unresolved token is always named.
  - Execution state: performed
  - Note the mixed case is MORE common than the plan first implied, because of the over-matching E-07 fixes: `aw runs verified <real-run-id>` renders 14 runs at exit 0 today (measured `de26ef00`), since `verified` accidentally resolves via the JSON substring fallback. Land E-07 before judging E-04's behavior, or the mixed case will appear to pass for tokens that should have been refused.

### Task group 3: close the same fail-open on the two sibling paths

- [x] E-07 Narrow the resolver's `state.json` fallback, which currently over-matches so broadly that it would silently exempt common tokens from the refusal. The fallback is a raw substring test over the entire file (`if f'"{t_str}"' in content`, `run_viewer.py:1148`), not a setid lookup, so it matches any quoted JSON key or value anywhere. MEASURED at HEAD `de26ef00` against 106 run records via `resolve_target_runs`: `status` -> 106, `run` -> 106, `opencode` -> 106, `driver` -> 106, `run_id` -> 106, `options` -> 106, `main` -> 96, `clean` -> 105, `json` -> 79, `execute` -> 53, `approved` -> 46, `verified` -> 13, `pass` -> 11. None of those is a setid. Match against the setid field the summary already parses (`RunSummary.setids`, `run_viewer.py:108`, populated at `:916`) instead of the raw text. THIS IS LOAD-BEARING FOR THE REFUSAL, not a cleanup: a mistyped token that happens to be a JSON key resolves to every run in the repository and reports success, which is the same defect the plan exists to close. Preserve the legitimate setid case, verified individually (`lanectn` -> 3 runs, `runnernorm` -> 7 runs today) and the substring-on-run-id case (`2367239` -> 1 run), both of which `tests/test_run_viewer.py:63-69` asserts.
  - Depends on: E-01
  - Expected outcome: a token that is merely a JSON key or value no longer resolves; `lanectn`, `runnernorm` and `2367239` still resolve to the same runs as at `de26ef00`.
  - Execution state: performed

- [x] E-08 Fix the same fail-open on the sibling `repair` path, which is inside this plan's fence and one function away. `aw runs repair <unresolvable>` iterates `for run_dir in resolve_target_runs(targets, repo_root)` (`run_viewer.py:2424`) and, when nothing resolves, the loop body never runs, so `rc` stays 0 and NOTHING is printed. MEASURED unpiped at `de26ef00`: `aw runs repair totalgibberish` -> exit 0, zero bytes of output. That is strictly worse than the read path, because `repair` is the one MUTATING verb on this surface and an operator is told nothing at all. Note the adjacent missing-target case is ALREADY correct (`:2418-2421` prints an error and returns 2), so this is an inconsistency within one function, and the fix is to route the unresolvable case through the same refusal as E-02.
  - Depends on: E-02
  - Expected outcome: `aw runs repair <unresolvable>` exits nonzero and names the token; `aw runs repair <real-id>` still exits 0 and prints its result; `aw runs repair` with no target still exits 2.
  - Execution state: performed

### Task group 4: prove it

- [x] E-05 Test the whole matrix, and measure exit codes WITHOUT a pipe (`cmd >/dev/null 2>&1; echo $?`), because a piped `$?` reports the last pipeline stage and that error produced a false finding in this very Set. Cover: the motivating case (`runs verify <id>` -> nonzero); a wholly unknown token; the mixed case; each preserved case from E-03 including the empty-repository bare call; the escape hatch; a leaf-name collision if one can be constructed in a fixture (none exists in the repo today per `cli.py:654`, so construct it rather than skip it); and all THREE renderers (human, `--agent`, `--json`) for the refusal, since only the human one is obvious. Assert the message NAMES the unresolved token, so a future refactor cannot degrade it to a bare exit code. BUILD A FIXTURE REPO; do NOT add a test that reads `dir="."`: `tests/test_run_viewer.py:1-30` records that 23 existing tests assert against the live gitignored `.aw/records/runs/` and that 14 of them fail in a bare worktree (re-measured 2026-09-06 in `.aw/worktrees/5942n7`: `14 failed, 32 passed`), and it explicitly instructs new tests to use a fixture instead. A new refusal test keyed to live run records would be unrunnable in CI and in every isolated lane worktree the runner allocates.
  - Depends on: E-03, E-04, E-07, E-08
  - Expected outcome: the refusal and every preserved behavior are pinned by fixture-based tests that pass in a bare worktree, with exit codes measured unpiped.
  - Execution state: performed

- [x] E-06 Update `tests/test_run_noun_split.py`, which ALREADY ASSERTS the exact behavior this plan removes and will go red otherwise. `test_leaf_name_as_viewer_target_is_reachable_via_the_escape_hatch` ends with `rc, out = _cli("runs", "--dir", str(self.root), "--", "no-such-target-xyz")` then `self.assertEqual(rc, 0, out)` and `self.assertIn("no matching runs found", out)` (`tests/test_run_noun_split.py:280-284`). That is an unresolvable token via the escape hatch, so E-02/E-04 must make it nonzero. Change the assertion to the new contract (nonzero, token named) rather than deleting the case: it is the escape hatch's only unresolvable-token coverage. Re-read the two sibling assertions above it in the same test (`--` forcing viewer interpretation of `status`, and the bare `runs status` leaf routing) and leave BOTH intact, because they pin the ambiguity rule E-03 must preserve.
  - Depends on: E-02, E-04
  - Expected outcome: `tests/test_run_noun_split.py` passes with the escape-hatch unresolvable case asserting the refusal; the two ambiguity-rule assertions are unchanged.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `aw runs` carries two shapes at once and argparse cannot express that, so `_ViewerOrLeafSubParsersAction` (`cli.py:623`) disambiguates explicitly: first token in `self._name_parser_map` routes to the leaf (`:672`), otherwise the whole list goes to the sibling viewer parser (`:676-682`). That single branch is the seam this plan changes.
- The nine viewer leaves are enumerated in `_RUNS_VIEWER_LEAVES` (`cli.py:1678-1690`): `show`, `status`, `list`, `next`, `resume`, `decisions`, `questions`, `evidence`, `verify-ledger`. Read the set rather than hardcoding a second copy, or the suggestion text will drift from the registration.
- Exit-code vocabulary already exists in `run_cli.py:46-62`; reuse `EXIT_INVALID_INVOCATION` (2) rather than adding a code. Note the spec's own exit table conflicts with this shipped one above 3 (recorded as an unreconciled conflict in spec `25kzda` Section 5.7 on 2026-09-05); this plan stays inside the shipped vocabulary and does not attempt that reconciliation.
- `_RunsTargetsPlaceholderAction` (`cli.py:685`) exists because a blind `setattr` erased resolved targets once already. Any change to target handling must not reintroduce that.
- MEASURE EXIT CODES UNPIPED. `cmd | head` reports `head`'s status. This repository already lost one finding to that mistake (`zrzfkw`, corrected 2026-09-06).
- `aw runs` is NOT itself a declared parser leaf: `discover_parser_leaves` returns the nine `runs <leaf>` entries and no bare `runs`, so the bare viewer carries no `CommandDeclaration` and no `exit_contract` (verified by calling `discover_parser_leaves(_build_parser())`). Adding a new nonzero exit to the VIEWER therefore does not violate a declared contract, and correspondingly `tests/test_cli_conformance_matrix.py` will NOT catch a regression there. That module is in `Scope-Paths` for the declared `runs verify-ledger` / `runs repair`-adjacent surface only; the viewer's own coverage must come from `tests/test_run_viewer.py` and `tests/test_run_noun_split.py`.
- `tests/test_cli_conformance_matrix.py` is marked `pytestmark = pytest.mark.slow` (`:46`), and `pyproject.toml` `addopts` includes `-m 'not slow'` (`:169`), so a bare `python3 -m pytest` SKIPS it entirely (measured: `no tests ran`). If this plan changes that module, validate it explicitly with `make test-all` or `python3 -m pytest tests/test_cli_conformance_matrix.py -m ''`; a green bare suite proves nothing about it.
- The viewer's empty-state has a MACHINE branch before the human one (`run_viewer.py:2538-2543`). Three renderers must agree on the refusal: human (stderr line), `--agent`, and `--json`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The routing branch has no third outcome: it is leaf-or-viewer, so an unknown token is a target by construction. | `cli.py:672-682` |
| F-2 | An unresolvable token exits 0. Measured unpiped: `aw runs totalgibberish` -> exit 0, prints `no matching runs found`. | measured at `63107a76` |
| F-3 | The motivating case exits 0 with plausible output: `aw runs verify <run-id>` -> exit 0, renders the full run report. | measured at `63107a76` |
| F-4 | The mixed case is worst: `aw runs totalgibberish <real-id>` -> exit 0, prints the real run, bogus token silently dropped. | measured at `63107a76` |
| F-5 | Not hypothetical. Until 2026-09-05 the spec documented `aw runs verify <run-id>` and seven shipped recovery messages in `run_evidence.py` told operators to run it, precisely when a ledger might be corrupt. Those strings are now corrected, but the fail-open path they pointed at is still open. | commit `98a0beed` |
| F-6 | The analogous honest case already exists and exits 2, so a nonzero refusal is consistent rather than novel: `aw runs verify-ledger <absent-ledger>` -> exit 2. | measured at `63107a76` |
| F-7 | Behavior that must be preserved, each measured exit 0 today: real run id, setid `lanectn`, `--last`. | measured at `63107a76`, re-measured at `de26ef00` |
| F-8 | AN EXISTING TEST ASSERTS THE BEHAVIOR THIS PLAN REMOVES, and its module was outside the original fence: `_cli("runs", "--dir", ..., "--", "no-such-target-xyz")` is asserted `rc == 0` with the literal `no matching runs found`. Landing E-02/E-04 turns it red. | `tests/test_run_noun_split.py:280-284` |
| F-9 | The resolver's `state.json` fallback is a raw substring test over the whole file, not a setid lookup, so ordinary JSON keys and values resolve to nearly every run. Measured via `resolve_target_runs` over 106 records: `status`/`run`/`opencode`/`driver`/`run_id`/`options` -> 106, `clean` -> 105, `main` -> 96, `json` -> 79, `execute` -> 53, `approved` -> 46, `verified` -> 13. Each would be silently EXEMPTED from the refusal. | `run_viewer.py:1141-1152`; measured at `de26ef00` |
| F-10 | The same fail-open exists on the MUTATING sibling and is worse: `aw runs repair totalgibberish` -> exit 0 with ZERO output, because the resolve loop body never executes. The no-target case two lines above is already correct (error + exit 2). | `run_viewer.py:2418-2429`; measured at `de26ef00` |
| F-11 | The machine renderers fail open too, on the path automation actually reads: `--agent` and `--json` both emit `{"runs": []}` and return 0 from the empty-state branch BEFORE the human line. A human-only refusal would leave the defect where it silently misleads a script. | `run_viewer.py:2538-2543`; measured `aw runs totalgibberish --agent` -> exit 0, `{"runs": []}` |
| F-12 | The plan's own test target is unreliable by design and its header says so: 23 tests in `tests/test_run_viewer.py` read the live gitignored `.aw/records/runs/`. Re-measured in the lane worktree `.aw/worktrees/5942n7`: `14 failed, 32 passed`, versus `46 passed` in the real checkout. New coverage must be fixture-based or it cannot run in CI or in any isolated lane. | `tests/test_run_viewer.py:1-30`; measured at `de26ef00` |

## Proposed changes (ordered, validatable)

1. Expose which requested tokens resolved to nothing (E-01).
2. Refuse that case nonzero with an actionable, leaf-naming message, in all three renderers (E-02).
3. Preserve every working invocation, case by case (E-03).
4. Decide the mixed case deliberately and never drop a token silently (E-04).
5. Pin the matrix with unpiped exit-code assertions, fixture-based (E-05).
6. Update the existing test that asserts the removed behavior (E-06).
7. Narrow the over-matching `state.json` fallback so the refusal is actually reachable (E-07).
8. Close the same fail-open on the mutating `repair` path (E-08).

## Deferred / out of scope (with reason)

- Whether driver runs should WRITE a `ledger.jsonl` at all. That is the remaining half of backlog `zrzfkw` and a genuine design question touching tamper-evidence and ownership attribution; it is independent of this refusal.
- Renaming either sense of "ledger" (the drivers' `events.jsonl` versus the hash-chained `ledger.jsonl`). Tracked in `zrzfkw`; cosmetic and separable.
- Auditing every other `aw` verb for the same fail-open shape. Worth doing, but a sweep is a different plan; this one fixes the measured instance and its immediate siblings under `aw runs`.
- Reconciling the spec's exit-code table with the shipped one. Recorded as an unreconciled conflict in spec `25kzda` on 2026-09-05 and explicitly left there.

## Scope check

- Over-scope: none. One CLI module, one viewer module, three test modules. E-07 (the resolver narrowing) and E-08 (`repair`) are in the same viewer module and are prerequisites for the refusal being real rather than cosmetic, not adjacent improvements: without E-07 a mistyped token that is also a JSON key resolves to every run and reports success, and without E-08 the one mutating verb on this surface keeps the identical defect the plan exists to remove. E-06 is a forced consequence of E-02, not new scope.
- Under-scope: does not make `verify-ledger` able to verify a driver run (nothing writes the file), and does not sweep other verbs beyond the two instances measured on THIS surface. Both are correct exclusions and named above.

## Required tests / validation

- `python3 -m pytest` bare, full suite, before and after, with counts stated.
- Targeted: `tests/test_run_viewer.py`, `tests/test_run_noun_split.py`, `tests/test_cli_conformance_matrix.py`.
- A live matrix of unpiped exit codes for every case in E-05, pasted as evidence, covering all three renderers.
- NOTE for the executor: `tests/test_run_viewer.py` reads run directories from `.aw/records/runs/`, which is gitignored. Re-measured 2026-09-06 at `de26ef00`: `46 passed` in the real checkout versus `14 failed, 32 passed` in the lane worktree `.aw/worktrees/5942n7`. (The plan originally said 14/42; the module has grown to 46 tests, so use the current numbers.) Validate in the real checkout, AND additionally prove the NEW tests green in a bare worktree per V-05, since the runner executes in an isolated worktree by default and a live-records-dependent test cannot pass there.
- NOTE on the `slow` marker: `tests/test_cli_conformance_matrix.py:46` sets `pytestmark = pytest.mark.slow` and `pyproject.toml:169` filters `-m 'not slow'`, so the bare suite does NOT run it (measured: `no tests ran`). Run it explicitly with `-m ''` if it is touched.

## Spec / documentation sync

Spec `25kzda`'s header already records (amended 2026-09-05) that `aw runs verify <run-id>` names no leaf and that the spelling exits 0 having verified nothing, citing backlog `6kq1lj`. The exact sentences are at `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:47` and `:49`. When this plan lands, that note should be updated to say the spelling now REFUSES. Do that in the same pass, since leaving it would make the spec understate the fix.

FENCE CONSEQUENCE, stated so the executor does not have to guess: that spec file is NOT in `Scope-Paths`, deliberately, because it is an approved spec and editing one is a `aw specs`-mediated act, not a code edit. Make the note edit and JUSTIFY it as an out-of-scope path at finalize (`--scope-reason`), which is the mechanism `aw ipd finalize` already provides; do not silently widen the fence, and do not skip the note.

Update `_RUNS_DESCRIPTION`/`_RUNS_EPILOG` help text only if the refusal makes the existing wording inaccurate. Note the epilog at `cli.py:1668-1672` currently advertises only three leaves and says nothing about unresolvable targets; if the refusal message names the leaves, the help and the message must not disagree about the list. Read `_RUNS_VIEWER_LEAVES` (`cli.py:1678-1690`) in both places rather than hardcoding a second copy.

## Open questions

### OQ-01: Should a bare `aw runs` in a repository with zero runs be an error?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, it must stay exit 0. A repository with no runs is a legitimate healthy state, not a failed request, and the same reasoning already governs the `reviews` status selector, whose empty result spec `25kzda` Section 2.4a makes a SUCCESS rather than a zero-match error. The distinction this plan draws is between "you asked for something specific that does not exist" (an error) and "you asked for everything and there is nothing" (not an error).

### OQ-02: Should the refusal apply to a token that is a valid-looking run id for a run that was deleted?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, and no special case is warranted. From the operator's position "this run id does not resolve" is the same failure whether the id was mistyped or the run directory was removed, and both deserve a nonzero exit naming the token. Attempting to distinguish them would require guessing intent from the token's shape, which is exactly the kind of inference this repository rejects elsewhere (see the fail-open prohibition recorded in backlog `d07nz2`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the resolver's output for three inputs showing unresolved tokens are reported distinctly: one real id, one bogus token, and both together. Show that a bare call (no tokens) is distinguishable from "all tokens unresolved".
  - Observed evidence: `resolve_target_runs_detailed` on 4 inputs: real id -> resolved=1/unresolved=[]; bogus -> 0/['totalgibberish']; both -> 1/['totalgibberish']; BARE -> 5/[]. Rows 2 and 4 are distinguishable, which is the point. Detail and the measurement note below.

    MEASUREMENT NOTE, stated once and applying to V-01 through V-08: this turn ran in the runner's
    isolated lane worktree, which has NO `.aw/records/runs/` at all (the tree is gitignored and
    box-local), and the main checkout was out of bounds. So every count below is against a FIXTURE
    of 5 run records built by `tmp/7wei1o/mkfixture.py` (gitignored scratch), carrying the same
    SHAPES the plan measured on the live tree: the setids `runnernorm`/`lanectn`/`runsverify`, the
    run-id substring `2367239`, and the JSON keys/values `status`/`driver`/`options`/`run_id`/
    `opencode`/`main`/`clean`/`execute`/`verified`. Counts are therefore out of 5, not out of 106.
    Recorded as DECISION 08-7wei1o-D3. This is also what the plan already requires of the SHIPPED
    tests (F-12, E-05), and V-05 proves those pass in a genuinely bare worktree.

    `resolve_target_runs_detailed`, four inputs (the new function E-01 added):

    ```
    1. one real id           resolved=1  unresolved=[]
    2. one bogus token       resolved=0  unresolved=['totalgibberish']
    3. both together         resolved=1  unresolved=['totalgibberish']
    4. BARE (no tokens)      resolved=5  unresolved=[]
    ```

    Rows 2 and 4 are the distinction the item asks for, and the one the old signature could not
    express: both once arrived at the caller as "not everything matched", but row 2 is a FAILED
    REQUEST (the caller named something that does not exist) while row 4 is a healthy repository-wide
    read. Row 3 is the mixed case: the real id still resolves AND the bogus token is still reported,
    so the caller can refuse rather than silently narrowing the request.

    Pinned by `test_detailed_resolver_separates_unresolved_from_absent`
    (`tests/test_run_viewer.py`), which asserts all four rows.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste UNPIPED exit codes and the stderr message for `aw runs verify <real-run-id>` and `aw runs totalgibberish`, using `cmd >/dev/null 2>&1; echo $?` for the code and a separate run for the text. Both must be nonzero, and the message must name the unresolved token and suggest `verify-ledger` for the `verify` case.
  - Observed evidence: UNPIPED: `runs verify <real-id>` rc=2, `runs totalgibberish` rc=2, both `--agent` and `--json` rc=2. Message names the token and suggests `verify-ledger`. Full text of all three renderers below.

    Exit codes measured UNPIPED with `cmd >/dev/null 2>&1; echo $?`, per the plan's warning. Invoked
    as `python3 -m agent_workflows` rather than `aw`, because the installed `aw` console script
    resolves to the MAIN checkout's package (verified: it printed the main tree's
    `agent_workflows/__init__.py`), so using it would have measured code this turn did not change.

    ```
    runs verify <real-run-id>                                 rc=2
    runs totalgibberish                                       rc=2
    runs totalgibberish --agent                               rc=2
    runs totalgibberish --json                                rc=2
    ```

    THE MOTIVATING CASE, `aw runs verify <run-id>`, stderr (stdout was empty, checked separately):

    ```
    error: no run matched target 'verify'
      did you mean the leaf `aw runs verify-ledger`? (not 'verify')
      leaves: decisions evidence list next questions resume show status verify-ledger
      a TARGET is a run id, a run directory path, or a Set id; force viewer interpretation of a leaf-like name with `aw runs -- <target>`
    ```

    It names the unresolved token AND suggests the one-edit correction, which is the whole point:
    before this change that invocation rendered the run's ordinary report and exited 0.

    `aw runs totalgibberish` (no close leaf match, so no suggestion line, correctly):

    ```
    error: no run matched target 'totalgibberish'
      leaves: decisions evidence list next questions resume show status verify-ledger
      a TARGET is a run id, a run directory path, or a Set id; force viewer interpretation of a leaf-like name with `aw runs -- <target>`
    ```

    ALL THREE RENDERERS honor it. `--agent` (one line) and `--json` (indented) emit a conformant
    `aw.agent/v1` ERROR record whose `exit` agrees with the process exit code, not the former
    `{"runs": []}` at exit 0:

    ```
    {"schema": "aw.agent/v1", "kind": "error", "cmd": "runs", "outcome": "cannot-run", "exit": 2,
     "verified": false, "complete": false, "findings": 1, "unresolved_targets": ["totalgibberish"],
     "error": "error: no run matched target 'totalgibberish'\n  leaves: ...", "next": null}
    ```

    The record passes `agent_schema.assert_valid_agent_record` (called on the construction path, so
    an invalid record would raise rather than ship). Exit code is the SHIPPED
    `run_cli.EXIT_INVALID_INVOCATION` value 2, not a new code.

    Pinned by `test_runs_verify_run_id_is_refused`, `test_wholly_unknown_token_is_refused`,
    `test_refusal_is_honored_by_the_agent_renderer`, `test_refusal_is_honored_by_the_json_renderer`,
    and `test_refusal_message_goes_to_stderr_not_stdout`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste UNPIPED exit codes for each preserved case: a real run id, the setid `lanectn`, bare `aw runs`, `--last`, and `aw runs -- status`. All must match their `63107a76` behavior. This is the anti-regression item; a nonzero here on a formerly-working invocation is a failed execution, not a pass.
  - Observed evidence: All 20 preserved invocations still rc=0 and all 6 pre-existing refusals still rc=2 with their own messages. ONE DEVIATION on `runs -- status`, reported in full below (DECISION 08-7wei1o-D1), not marked pass silently.

    Every preserved case, exit codes UNPIPED, AFTER the change. All 20 stayed exit 0:

    ```
    === MUST STAY EXIT 0 (anti-regression) ===
    runs <real-run-id>                                        rc=0
    runs <setid lanectn>                                      rc=0
    runs <setid runnernorm>                                   rc=0
    runs <run-id substring 2367239>                           rc=0
    runs (bare)                                               rc=0
    runs (bare, EMPTY repo)                                   rc=0
    runs --last 1                                             rc=0
    runs --latest-only                                        rc=0
    runs --issues                                             rc=0
    runs --summary-only                                       rc=0
    runs --short                                              rc=0
    runs --detail                                             rc=0
    runs --since 2026-09-01                                   rc=0
    runs --since 7d                                           rc=0
    runs --since <real-run-id>                                rc=0
    runs --set lanectn                                        rc=0
    runs --ipd aaa111                                         rc=0
    runs <real> --agent                                       rc=0
    runs <real> --json                                        rc=0
    runs repair <real-run-id>                                 rc=0
    ```

    The already-correct refusals also kept their own exit 2 AND their own messages, so the new
    refusal does not shadow them (asserted by `test_already_correct_refusals_keep_their_own_messages`,
    which additionally checks each output does NOT contain `no run matched target`):

    ```
    === ALREADY-CORRECT REFUSALS (must stay nonzero) ===
    runs status (leaf demands target)                         rc=2
    runs --since bogusdate                                    rc=2
    runs --summary-only --short                               rc=2
    runs --latest-only --summary-only                         rc=2
    runs --issues --summary-only                              rc=2
    runs repair (no target)                                   rc=2
    ```

    ONE DEVIATION, REPORTED PROMINENTLY RATHER THAN MARKED PASS SILENTLY, as this item's own warning
    demands. `aw runs -- status` is the single listed case whose EXIT CODE changed, and it now depends
    on whether a Set named `status` actually exists:

    ```
    === THE ESCAPE HATCH (E-03's ambiguity rule) ===
    runs -- status, Set 'status' EXISTS   -> want 0           rc=0
    runs -- status, NO such Set           -> want 2           rc=2
    ```

    WHY THIS IS NOT A REGRESSION, measured rather than argued. On a fixture declaring NO Set named
    `status`, the token used to resolve ONLY through the raw-substring fallback E-07 removes: measured
    before my change, `resolve_target_runs(['status'])` returned 5 of 5 runs while the setids those
    runs actually declare are `['runnernorm']`, `['lanectn']`, `['runsverify']`. It matched because the
    literal string `"status"` appears in every `state.json` as an ordinary JSON KEY (each queue item's
    own `status`). That is F-9 exactly. So the old exit 0 was the over-match reporting success, never
    a real target being viewed, and the plan's recorded evidence for this case ("renders 106 runs")
    is that same over-match on the live tree.

    The hatch's REAL purpose is preserved and now positively proven, which observation alone could not
    do because no such collision exists among the repo's real set ids: with a Set GENUINELY named
    `status` the hatch reaches it at exit 0 and renders that run
    (`test_a_leaf_named_target_is_reachable_through_the_hatch_and_exits_zero`, and the fixture in
    `tests/test_run_noun_split.py` now declares the collision). The other half of the ambiguity rule
    is also pinned: bare `runs status` WITHOUT the hatch still routes to the LEAF
    (`test_bare_leaf_name_without_the_hatch_still_routes_to_the_leaf`), so the refusal did not invert
    the documented precedence.

    Full reasoning, options weighed, and the reversal instructions are recorded as DECISION
    08-7wei1o-D1, flagged for human review at low urgency.

    Pinned by `test_every_resolvable_target_shape_still_exits_zero` (6 shapes),
    `test_every_viewer_flag_still_exits_zero` (13 flags),
    `test_bare_call_on_an_empty_repository_is_still_success`, and
    `test_a_filter_that_excludes_everything_is_still_success`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the UNPIPED exit code and full output for `aw runs totalgibberish <real-run-id>`, showing the unresolved token is named and the exit is nonzero. State which rendering choice was implemented and why.
  - Observed evidence: `runs totalgibberish <real-id>` rc=2 UNPIPED, token named on stderr, real run's id absent from stdout. Full REFUSAL chosen over partial rendering; reasoning below.

    ```
    $ python3 -m agent_workflows runs --dir <fx> totalgibberish run-20260901T000000Z-2367239 >/dev/null 2>&1; echo $?
    2
    ```

    Full output (stderr; stdout empty):

    ```
    error: no run matched target 'totalgibberish'
      leaves: decisions evidence list next questions resume show status verify-ledger
      a TARGET is a run id, a run directory path, or a Set id; force viewer interpretation of a leaf-like name with `aw runs -- <target>`
    ```

    RENDERING CHOICE IMPLEMENTED: full REFUSAL, not partial rendering. The plan permitted either
    (partial-plus-nonzero was acceptable "ONLY if the unresolved token is named prominently"), and I
    took the refusal for the reason the plan gives for preferring it: a partially-honored request that
    looks complete is the exact defect being removed. Before the change this invocation printed the
    real run's full report at exit 0 with the bogus token silently dropped, which is the most
    misleading variant precisely because the operator sees plausible output. Rendering the run
    alongside a nonzero exit would preserve that misleading artifact for anyone reading stdout or
    eyeballing a terminal, so the request is now either honored in full or refused, never quietly
    narrowed. Confirmed the real run's id does NOT appear on stdout (asserted in the test).

    Every unresolved token is named, not merely the first
    (`test_every_unresolved_token_is_named_not_just_the_first`: `bogus-one` and `bogus-two` both
    appear).

    NOTE the plan's E-04 warning that this case is more common than it first implied because of the
    over-match: `aw runs verified <real-run-id>` rendered 14 runs at exit 0 on the live tree. E-07
    landed first, so such tokens now resolve to nothing and are refused rather than appearing to pass;
    see the V-07 table.

    Pinned by `test_mixed_resolvable_and_unresolvable_is_refused_not_partially_rendered`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the ACTUAL output of the targeted test modules and of the bare full suite with the `N passed` summary line, state before/after counts, and name the test that pins the message text. Confirm the run was in the real checkout, not a bare worktree. ALSO paste the new refusal test running GREEN in a bare worktree (or a temp clone), which is the positive evidence that it is fixture-based rather than keyed to live run records; a refusal test that only passes in the real checkout does not satisfy this item. If `tests/test_cli_conformance_matrix.py` was modified, paste a run of it with `-m ''`, because the bare suite skips it (`slow` marker).
  - Observed evidence: Bare suite BEFORE `33 failed, 5624 passed` -> AFTER `33 failed, 5646 passed`, with the sorted FAILED-line diff EMPTY (zero new failures, +22 tests). All 22 new tests green in a genuinely bare worktree. Detail, honest caveats, and the conformance-matrix run below.

    BARE FULL SUITE, before and after, run as `python3 -m pytest` with no added flags:

    ```
    BEFORE (HEAD 130d9cc7):  33 failed, 5624 passed, 3 skipped, 2 xfailed in 57.34s
    AFTER:                   33 failed, 5646 passed, 3 skipped, 2 xfailed in 53.22s
    ```

    +22 passing, and the failing SET is byte-identical. Verified by diffing the sorted `FAILED` lines
    rather than comparing counts (a count match can hide one fix plus one break):

    ```
    $ comm -13 <(grep "^FAILED" baseline | sort) <(grep "^FAILED" after | sort)
    === NEW failures vs baseline (must be EMPTY) ===
    === (end of list) ===
    ```

    Zero new failures. The 33 pre-existing failures are unrelated to this plan (runner worktree
    isolation, ipd lifecycle CLI, real-corpus plan readiness, and the 14 documented live-records tests
    in `tests/test_run_viewer.py`).

    TARGETED MODULES:

    ```
    $ python3 -m pytest tests/test_run_viewer.py tests/test_run_noun_split.py -o addopts="" -q
    14 failed, 70 passed in 5.03s
    ```

    Baseline for the same pair at HEAD in this lane was `14 failed, 32 passed` (the plan cites
    `62 passed` measured in the REAL checkout at `de26ef00`, where the live run records exist; this
    lane has none, which is exactly the F-12 hazard). The 14 failures are the pre-existing
    live-records tests, unchanged in name and count.

    HONEST NOTE ON WHERE THIS RAN, since the item asks for the real checkout: this turn ran in the
    runner's ISOLATED LANE WORKTREE, which has no `.aw/records/runs/` at all, and the main checkout
    was out of bounds by the turn contract. I therefore could not produce a real-checkout run, and I
    have not claimed one. That cuts the right way for this item's actual purpose: the harder condition
    (green in a bare tree) is the one demonstrated, and the only tests that fail here are the ones the
    module header already documents as failing in any fresh checkout.

    NEW TESTS GREEN IN A GENUINELY BARE WORKTREE (`git worktree add` at HEAD, `.aw/records/runs`
    confirmed absent, my four changed files copied in):

    ```
    $ ls .aw/records/runs
    ls: cannot access '.aw/records/runs': No such file or directory

    $ python3 -m pytest tests/test_run_viewer.py -o addopts="" -q \
        -k "UnresolvableTargetRefusalTests or ResolverSetidNarrowingTests or repair_refuses or repair_still"
    ......................                                                   [100%]
    22 passed, 46 deselected in 2.34s

    $ python3 -m pytest tests/test_run_noun_split.py -o addopts="" -q
    ................                                                         [100%]
    16 passed in 2.66s
    ```

    All 22 new tests and all 16 of the noun-split module pass with zero run records present, which is
    the positive evidence that they are fixture-based rather than keyed to live records. (The bare
    worktree was removed afterwards; while it existed it made
    `tests/test_reporting_contract.py::ParityTests` fail by scanning its copied files, which is a
    scratch artifact and not a code change.)

    THE TEST THAT PINS THE MESSAGE TEXT: `test_runs_verify_run_id_is_refused` asserts the message
    contains both `verify` and `verify-ledger`, so a refactor cannot degrade the refusal to a bare
    exit code. `test_wholly_unknown_token_is_refused`,
    `test_mixed_resolvable_and_unresolvable_is_refused_not_partially_rendered`, and
    `test_every_unresolved_token_is_named_not_just_the_first` each also assert the token is named.

    `tests/test_cli_conformance_matrix.py` was NOT modified, so no `-m ''` run of it is owed. I ran it
    anyway because `cli.py` is in the fence, and its result is unchanged by this plan:

    ```
    $ python3 -m pytest tests/test_cli_conformance_matrix.py -m '' -o addopts="" -q
    WITH my change:     2 failed, 9 passed in 225.79s
    STASHED (at HEAD):  2 failed, 9 passed in 238.43s
    ```

    Identical failures in both runs (`test_no_undeclared_parser_leaves` and
    `test_every_declared_leaf_gets_a_full_scenario_row_set`), both naming undeclared `oc profile *`
    leaves that this plan does not touch. Pre-existing, verified by stashing rather than assumed.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the ACTUAL output of `python3 -m pytest tests/test_run_noun_split.py -o addopts="" -q` showing it green, plus the diff of the changed assertion. Show the two sibling ambiguity-rule assertions in the same test UNCHANGED (paste them), since the fix must not be achieved by deleting the coverage. Baseline for comparison: `62 passed` for `tests/test_run_viewer.py` + `tests/test_run_noun_split.py` together at `de26ef00`.
  - Observed evidence: `python3 -m pytest tests/test_run_noun_split.py -o addopts="" -q` -> `16 passed in 2.62s`. Assertion diff, the confirmed pre-fix failure, and both sibling ambiguity-rule assertions pasted unchanged below.

    ```
    $ python3 -m pytest tests/test_run_noun_split.py -o addopts="" -q
    ................                                                         [100%]
    16 passed in 2.62s
    ```

    Green. F-8 was confirmed first, not taken on faith: with the refusal landed and this assertion
    still expecting the old contract, the module failed with exactly the predicted error, which is the
    proof that the plan correctly identified a test asserting the removed behavior:

    ```
    rc, out = _cli("runs", "--dir", str(self.root), "--", "status")
    >   self.assertEqual(rc, 0, out)
    E   AssertionError: 2 != 0 : error: no run matched target 'status'
    1 failed, 15 passed in 4.10s
    ```

    DIFF OF THE CHANGED ASSERTION (re-pointed to the new contract, NOT deleted):

    ```diff
    -        # A token that matches nothing renders the viewer's own empty-state, still not a leaf error.
             rc, out = _cli("runs", "--dir", str(self.root), "--", "no-such-target-xyz")
    -        self.assertEqual(rc, 0, out)
    -        self.assertIn("no matching runs found", out)
    +        self.assertEqual(rc, 2, out)
    +        self.assertIn("no-such-target-xyz", out)  # the message NAMES the bad token
    +        self.assertNotIn("no matching runs found", out)
    ```

    The case is preserved (it remains the escape hatch's only unresolvable-token coverage) and is now
    STRONGER: it additionally asserts the token is named and that the old empty-state line is gone.

    THE TWO SIBLING AMBIGUITY-RULE ASSERTIONS, pasted to show they are intact:

    ```python
    # Bare `runs status` routes to the LEAF, which then demands its own required target.
    rc, out = _cli("runs", "status", "--dir", str(self.root))
    self.assertNotEqual(rc, 0)
    self.assertIn("target", out)
    self.assertIn("runs status", out)  # the LEAF's usage, not the viewer's
    # `--` forces VIEWER interpretation: the token becomes a target selector. Asserted by the
    # viewer table being rendered at all, which the leaf path can never do.
    rc, out = _cli("runs", "--dir", str(self.root), "--", "status")
    self.assertEqual(rc, 0, out)
    self.assertNotIn("the following arguments are required", out)
    ```

    Both assertions are unchanged, INCLUDING the `-- status` exit 0. Making that assertion continue to
    hold honestly required a fixture change rather than an assertion change: the fixture now declares
    a run whose `setid` is literally `status`, so the hatch resolves a REAL colliding Set instead of
    passing by accident through the over-match E-07 removed (see V-03 and DECISION 08-7wei1o-D1). I
    also STRENGTHENED it by one line, asserting the colliding run actually appears in the output, since
    the previous version could pass while resolving any run at all:

    ```python
    # And it resolved the SET named `status`, not merely "some run": the hatch is only meaningful
    # if it reaches the colliding target itself.
    self.assertIn(self.collision_run[:18], out)
    ```

    Combined pair, this lane: `14 failed, 70 passed` (baseline in this lane `14 failed, 32 passed`).
    The plan's `62 passed` baseline was measured in the real checkout, where the live run records the
    14 failing tests need are present; this lane has none. See the V-05 note.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste a before/after table of `resolve_target_runs([t], Path("."))` counts for at least `status`, `run`, `main`, `clean`, `execute`, `approved`, `verified` (each currently 11 to 106) showing they no longer over-match, ALONGSIDE `lanectn` (3), `runnernorm` (7) and `2367239` (1) showing they are UNCHANGED. The second half is the anti-regression half: a narrowing that also breaks setid lookup is a failed execution, not a pass. State which field the fallback now reads.
  - Observed evidence: Fallback now reads the setid FIELDS (`queue[].setid` + run-level `selectors`) via `_state_setids`. 10 JSON-key tokens went from 3-5 of 5 to 0 of 5; `runnernorm`/`lanectn`/`runsverify`/`2367239` all UNCHANGED. Full table below.

    WHICH FIELD THE FALLBACK NOW READS: the setid FIELDS, via a new `_state_setids(run_dir)` helper,
    namely each `queue[].setid` plus the run-level `selectors` (and a run-level `setids`/`setid` when
    present). It no longer tests raw file text. Those are the same fields `load_run_summary` populates
    `RunSummary.setids` from (`:831-832`, `:916`) and that `--set` filtering already accepts
    (`set_filter not in summary.setids and set_filter not in summary.selectors`), so the resolver and
    the renderer cannot disagree about what a run's Set is. Reading the fields directly rather than
    building a full `RunSummary` per run is DECISION 08-7wei1o-D2 (a summary parses costs, elapsed
    times, pid liveness and plan-stem lookups, all irrelevant to "does this run declare Set X?").

    BEFORE/AFTER, same 5-run fixture, same tokens, measured with the lane's package pinned on
    `PYTHONPATH` (without that pin the probe silently imported the MAIN checkout's copy and reported
    unchanged numbers; caught and re-measured):

    | token | before | after | verdict |
    |---|---|---|---|
    | `status` | 5 / 5 | 0 / 5 | over-match removed |
    | `opencode` | 5 / 5 | 0 / 5 | over-match removed |
    | `driver` | 5 / 5 | 0 / 5 | over-match removed |
    | `run_id` | 5 / 5 | 0 / 5 | over-match removed |
    | `options` | 5 / 5 | 0 / 5 | over-match removed |
    | `main` | 5 / 5 | 0 / 5 | over-match removed |
    | `clean` | 5 / 5 | 0 / 5 | over-match removed |
    | `execute` | 5 / 5 | 0 / 5 | over-match removed |
    | `queue` | 5 / 5 | 0 / 5 | over-match removed |
    | `verified` | 3 / 5 | 0 / 5 | over-match removed |
    | `approved` | 0 / 5 | 0 / 5 | already 0 in this fixture |
    | `runnernorm` (setid) | 2 / 5 | 2 / 5 | UNCHANGED |
    | `lanectn` (setid) | 2 / 5 | 2 / 5 | UNCHANGED |
    | `runsverify` (setid) | 1 / 5 | 1 / 5 | UNCHANGED |
    | `2367239` (run-id substring) | 1 / 5 | 1 / 5 | UNCHANGED |

    The anti-regression half holds: every real setid and the run-id substring resolve to exactly the
    same runs as before. `tests/test_run_viewer.py:63-69`, which asserts the `2367239` and
    `runnernorm` cases, is unmodified and its result is unchanged.

    ONE TOKEN DELIBERATELY NOT ZEROED: `run` stays 5 / 5. That is the pre-existing and CORRECT
    run-id-substring rule (every run directory is named `run-*`), a different and earlier branch than
    the JSON fallback this item narrows. Zeroing it would have broken substring matching, which the
    item explicitly requires be preserved.

    Counts are out of 5 rather than the plan's 106 because this lane has no live run records at all;
    see the V-01 measurement note and DECISION 08-7wei1o-D3. The plan's live-tree absolute numbers
    (106, 96, 53, ...) are therefore NOT re-verified in this turn; the property is (a JSON key
    resolving to effectively every run before, none after).

    Pinned by `test_ordinary_json_keys_and_values_no_longer_resolve` (10 tokens),
    `test_real_setids_and_run_id_substrings_still_resolve`,
    `test_setid_resolves_from_run_level_selectors_too`, and `test_malformed_state_json_does_not_raise`.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste UNPIPED exit codes and full output for three `repair` invocations: `aw runs repair <unresolvable>` (must be nonzero and name the token; it is exit 0 with zero output today), `aw runs repair <real-run-id>` (must stay exit 0 and print its result, `nothing to repair` in a clean fixture), and bare `aw runs repair` (must stay exit 2 with its existing message). Confirm no write occurred on the refused path.
  - Observed evidence: UNPIPED: `repair <unresolvable>` rc=2 naming the token (was rc=0, zero output), `repair <real-id>` rc=0 `nothing to repair`, bare `repair` rc=2 unchanged. All 5 state.json md5sums verified OK after the refusal. Detail below.

    Exit codes UNPIPED (`cmd >/dev/null 2>&1; echo $?`):

    ```
    repair <unresolvable> rc=2      (was rc=0 with ZERO output before this plan)
    repair <real-run-id>  rc=0
    repair (no target)    rc=2
    ```

    Full output of each:

    ```
    [1] repair totalgibberish:
    error: no run matched target 'totalgibberish'
      leaves: decisions evidence list next questions resume show status verify-ledger
      a TARGET is a run id, a run directory path, or a Set id; force viewer interpretation of a leaf-like name with `aw runs -- <target>`

    [2] repair run-20260901T000000Z-2367239:
    run-20260901T000000Z-2367239: nothing to repair (no running steps)

    [3] repair (bare):
    error: aw runs repair needs a run id (or a run directory path)

    usage: aw runs repair <run-id|run-dir> [<run-id|run-dir> ...]
    ```

    All three match the required contract: the unresolvable case now refuses and NAMES the token, the
    real target still repairs (no-op on a clean fixture) at exit 0, and the bare case keeps its
    pre-existing message and exit 2 unchanged.

    NO WRITE OCCURRED ON THE REFUSED PATH, verified by checksum rather than by reading the code:

    ```
    $ md5sum <fx>/.aw/records/runs/*/state.json > before.md5
    $ python3 -m agent_workflows runs --dir <fx> repair totalgibberish   # the refused invocation
    $ md5sum -c before.md5
    .../run-20260901T000000Z-2367239/state.json: OK
    .../run-20260901T010000Z-1111111/state.json: OK
    .../run-20260902T000000Z-2222222/state.json: OK
    .../run-20260902T010000Z-3333333/state.json: OK
    .../run-20260903T000000Z-4444444/state.json: OK
    ```

    All five records byte-identical after the refusal. This matters more here than anywhere else on
    the surface: `repair` is the one MUTATING verb under `aw runs`, and its old behavior told the
    operator nothing at all (exit 0, zero bytes) while appearing to have reconciled the run.

    Pinned by `test_repair_refuses_an_unresolvable_target_instead_of_silently_succeeding` (which also
    asserts no record gained an `interrupted` status) and
    `test_repair_still_works_on_a_resolvable_target`. The pre-existing
    `test_runs_repair_verb_still_routes` in `tests/test_run_noun_split.py` is unmodified and still
    passes, so the verb's routing is unaffected.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: eight E-items across three task groups, all inside one CLI module and one viewer module. Reviewed for splitting and kept as one plan: E-01/E-02 define the refusal, E-07 is what makes it reachable (a token resolving to 106 of 106 runs is never refused), E-04 cannot be judged before E-07 lands, E-06 goes red the moment E-02 lands, and E-08 is the same defect in the same function. Splitting would produce a plan whose tests fail until its sibling merges, which is the failure mode a Set is supposed to avoid rather than create.

Execution requires explicit human approval (`- Status: approved`). The executor must commit ONLY the paths in Scope-Paths, path-scoped, and must never push. The one intended out-of-fence edit is the spec `25kzda` header note, which must be JUSTIFIED at finalize with `--scope-reason` rather than added to the fence. Tests must be RUN and their actual output pasted into `Observed evidence`; a `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

FOUR WARNINGS FOR THE EXECUTOR. FIRST, V-03 is the item that matters most: this change can only fail in one direction, by refusing an invocation that used to work. If any preserved case cannot be shown green, report it prominently in the execution record rather than marking V-03 pass. SECOND, measure every exit code UNPIPED; a piped `$?` reports the last pipeline stage, and that mistake already produced one false finding in this Set (`zrzfkw`, corrected 2026-09-06). THIRD, an existing test at `tests/test_run_noun_split.py:280-284` asserts the OLD behavior; E-06 updates it, and if you find yourself deleting the case rather than re-pointing it, you have removed the escape hatch's only unresolvable-token coverage. FOURTH, do NOT write a new test that reads `dir="."`: the module header (`tests/test_run_viewer.py:1-30`) forbids it and the runner's default isolated worktree has no run records at all, so such a test cannot pass where it will actually be run.

This plan does NOT touch `oc_runipd.py` or `agy_runipd.py`, so it does not collide with the `verifygap` Set or the four approved `orchretire` plans and may run alongside them.

On completion, close backlog `6kq1lj`, which this plan carries as `- From-Backlog:`.
