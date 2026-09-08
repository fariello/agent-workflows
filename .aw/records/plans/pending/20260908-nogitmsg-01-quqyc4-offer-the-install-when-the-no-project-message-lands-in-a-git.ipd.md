# IPD: Offer the install when the no-project message lands in a git repo, and stop the agent path crashing there

- Date: 2026-09-08
- Kind: child
- Concern: `no_project_message` tells the operator WHERE it looked but never checks whether cwd is a git repository, so in the commonest case (a real repo with agent-workflows simply not installed) it cannot offer the one action that would fix it. Separately and newly measured, the MACHINE path for the same condition does not merely lack a suggestion, it CRASHES: `aw attention --agent` and `aw ipd board --agent` outside a project raise an unhandled `ValueError` from the `aw.agent/v1` validator and exit 1 with a Python traceback, because the result carries `exit_code=3` while the schema admits only 0, 1 or 2 and requires an error record to carry exactly 2.
- Scope: Make `no_project_message` git-aware in ONE place so every current and future caller inherits the hint, add the machine-readable equivalent as a `NextAction` on the two `CommandResult`s that emit it, and fix the schema violation that makes the `--agent` path crash on this exact condition. Explicitly NOT changing what counts as a project: `find_project_root` stays git-blind.
- Scope-Paths: agent_workflows/project_context.py, agent_workflows/attention.py, agent_workflows/cli.py, tests/test_awretrofit_project_root_climb.py, tests/test_attention.py
- Item-Dependencies: none
- Status: to-review
- Set: nogitmsg
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: quqyc4
- From-Backlog: okm6e6
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `okm6e6`, inheriting its `Blocks-Release: next` gate. EVERY LINE NUMBER IN THE ITEM HAD MOVED and was re-located by SYMBOL at HEAD `44d4950d` rather than trusted: the item cites `attention.py:1008`/`:1011` for the two emit sites, which are now `:2200` and `:2203` (a ~1190-line drift), and `project_context.py:330-342` for the message, which is still correct. The item's other citations verify: `_find_git_root` at `:262-270`, `find_project_root` at `:273-292` with the git-blind rationale in its own docstring at `:279-281`, and the locking test `test_bare_git_ancestor_is_not_a_root` at `tests/test_awretrofit_project_root_climb.py:71-75`. ONE NEW DEFECT FOUND while reproducing the item, and it is more serious than the item's own concern: on the `--agent` path this condition CRASHES rather than degrading. Measured in a bare `git init` directory with no AW layout: `aw attention` (human) exits 3 correctly; `aw attention --json` exits 3 correctly; but `aw attention --agent` exits 1 with an unhandled `ValueError: Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2), got '3'; Error record must carry exit=2, got exit=3` and a full traceback. `aw ipd board --agent` reproduces it identically (exit 1). That is squarely inside this item's scope rather than a separate concern, because the item REQUIRES the new fact to be machine-readable on that same `CommandResult`, and there is no point adding a `NextAction` to a record that cannot be emitted. E-05 fixes it, and E-06 pins it. Also noted for the record: `aw plans --agent` is NOT reachable at all (`plans` is not a registered command; it exits 2 from argparse), so the item's `cli.py:6244`/`:6247` citation belongs to `aw ipd board`, whose emit sites are now `cli.py:7203`/`:7206`.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Turn a dead end into a next step. When `aw` cannot find a project but IS standing in a git repository, name that repository and offer `aw install <root>`; make the same fact available to an automated consumer; and make sure that consumer can actually receive it, which today it cannot because the record fails its own schema.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the human message actionable

- [ ] E-01 Teach `no_project_message(verb)` (`project_context.py:330-342`) to probe for a git ancestor when the AW climb has failed, and when one is found, name that root and offer the install. REUSE THE EXISTING HELPER: `_find_git_root(start_dir)` at `:262-270` already walks up looking for `.git` and is today called only by `resolve_project_context` (`:439`) to pick a default `target_repo`. Append lines in the shape the maintainer asked for: state that the directory IS a git repository but agent-workflows is not installed in it, and give the literal command `aw install <root>`. Keep the three existing lines unchanged and ordered as they are, since the item records the maintainer calling them genuinely helpful about WHERE it looked; this ADDS a fourth fact, it does not rewrite the first three.
  - Depends on: none
  - Expected outcome: run in a git repo with no AW layout, the message names the git root and offers `aw install <root>`; run in a directory that is not a git repo, the message is byte-for-byte what it is at HEAD `44d4950d`.
  - Execution state: pending

- [ ] E-02 Do NOT change root detection, and pin that it did not change. `find_project_root` (`:273-292`) is DELIBERATELY git-blind and its docstring says so at `:279-281`: a `.aw/` tree can exist without git, and a bare `.git` ancestor with no AW marker is NOT an AW project (IPD awretrofit Order 06, OQ-01). That rule is locked by `tests/test_awretrofit_project_root_climb.py:71-75` (`test_bare_git_ancestor_is_not_a_root`, asserting `find_project_root(gitonly) is None`). THAT TEST MUST STILL PASS UNCHANGED at the end of this plan; if it needs editing, the change has gone out of scope and must stop. This item is the guard, not a code change: verify the test passes and add a comment at the new git probe in `no_project_message` stating that probing here is a MESSAGE concern and must never be promoted into `find_project_root`.
  - Depends on: E-01
  - Expected outcome: `test_bare_git_ancestor_is_not_a_root` passes unmodified, and the code carries an inline warning against widening the probe into root detection.
  - Execution state: pending

- [ ] E-03 Fix `no_project_message` in ONE place only, so every current and future caller inherits the hint, and confirm the caller set. The function has exactly TWO consumers today, both of which call it twice (once for the machine branch's `summary`, once for the stderr write): `aw attention` at `attention.py:2200` and `:2203`, guarded at `:2174`, and `aw ipd board`/`aw plans` at `cli.py:7203` and `:7206`. Do not add per-caller message assembly. Verify by grep that the caller set is exactly those two after the change, so the "one place" property is a measured fact rather than an intention.
  - Depends on: E-01
  - Expected outcome: both verbs emit the improved message with no per-verb code, demonstrated by running each; a grep for `no_project_message` shows only the two call sites plus the definition.
  - Execution state: pending

### Task group 2: make the fact machine-readable, and emittable

- [ ] E-04 Attach a `NextAction` to the two machine-path `CommandResult`s so the install suggestion is structured, not only prose in `summary`. The item requires exactly this: `NextAction(command="aw install <root>", description="install agent-workflows in this repo")` on the `CommandResult` at the attention emit site (`attention.py:2195-2201`) and its twin at `cli.py:7198-7204`. `CommandResult` already carries `next_actions: List[NextAction]` (`result_types.py:288`), and `to_agent_record` surfaces the FIRST action as the record's `next` field (`result_types.py:440-444`), so no new plumbing is needed. Add the action ONLY when a git root was actually found, since an unconditional suggestion would be wrong in a non-git directory.
  - Depends on: E-01
  - Expected outcome: `aw attention --agent` in a git-but-not-AW directory emits a record whose `next` is `aw install <root>`; in a non-git directory `next` stays `null`.
  - Execution state: pending

- [ ] E-05 Make the `--agent` path emit a VALID record for this condition instead of crashing, implementing whichever exit semantics OQ-01 resolves to. MEASURED at HEAD `44d4950d` in a bare `git init` directory: `aw attention --agent` exits 1 with an unhandled `ValueError: Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2), got '3'; Error record must carry exit=2, got exit=3`, raised from `agent_schema.assert_valid_agent_record` (`agent_schema.py:315-319`) via `result_types.to_agent_record` (`:451`) via `renderers.py:195`; `aw ipd board --agent` reproduces identically. The cause is a contradiction between two shipped contracts: the verbs use exit 3 for cannot-run (`attention.py:2199`/`:2204`, `cli.py:7202`/`:7207`) while the schema admits only `(0, 1, 2)` (`agent_schema.py:191-197`) and requires exactly 2 for an error record (`:275-279`). The two candidate directions and the evidence for each live in OQ-01, which is BLOCKING; do not choose one here. Record the chosen semantics in a code comment at the emit site, and keep the two machine renderers aligned: `--json` does NOT crash today (it exits 3 cleanly through a path that does not validate), so the fix must not widen that divergence.
  - Depends on: E-04
  - Expected outcome: `aw attention --agent` and `aw ipd board --agent` in a git-but-not-AW directory emit a schema-valid `aw.agent/v1` record with no traceback, `--json` behaves consistently with it, and a code comment names the OQ-01 option implemented.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-06 Test the matrix, measuring exit codes UNPIPED (`cmd >/dev/null 2>&1; echo $?`), because a piped `$?` reports the last pipeline stage. Cover, in a temporary fixture directory (never against the live repo): (a) git repo, no AW layout -> human message names the root and offers `aw install`; (b) NOT a git repo -> message unchanged from HEAD, no install offer; (c) an AW project -> normal output, message never emitted; (d) `--dir <explicit>` honored verbatim and unaffected; (e) `--agent` for both verbs on case (a) -> a VALID record, no traceback, `next` naming the install; (f) `--json` for both verbs on case (a) -> still works, and its exit semantics agree with whatever E-05 chose; (g) `aw attention --check` outside a project still returns the fail-closed-valid exit 0 it returns today (`attention.py:2175-2193`), since that branch precedes the message and must not regress. THE CRASH REGRESSION TEST IS THE MOST IMPORTANT ONE HERE: assert no traceback and a schema-valid record, so a future exit-code change cannot silently reintroduce it.
  - Depends on: E-05
  - Expected outcome: all seven cases pinned by fixture-based tests that pass in a bare worktree; case (e) fails against HEAD `44d4950d` and passes after E-05.
  - Execution state: pending

- [ ] E-07 Record the ASYMMETRY the item documents, without acting on it, so it is not rediscovered from scratch. Only TWO verbs emit this guidance; roughly twenty other repo-scoped verbs call `resolve_verb_repo_root` (`project_context.py:314-327`) and then SILENTLY fall back to cwd, so run outside a project they produce an empty or misplaced result with no explanation. The item enumerates them: `backlog.py:341/474/653`, `specs.py:415/866`, `releases.py:600`, `research_cmd.py:290`, `research_index.py:536`, `research_archive.py:292`, `plans_index.py:314`, `plans_archive.py:191`, `plans_refs.py:395`, `artifact_rename.py:22`, `prompts.py:180`, `reviews.py:236`, `run_cli.py:97`, `status_set.py:1101/1438`, `work_cmd.py:126`, `cli.py:7138/7390/9296`. SPOT-CHECK A SAMPLE of those citations rather than copying the list on faith (the item's own `attention.py` line numbers had drifted by ~1190 lines), then leave a comment at `no_project_message` naming the asymmetry and pointing at backlog item `okm6e6` for the reasoning. DO NOT convert those verbs here: whether they should all emit the same guidance is a separate design question, and some may legitimately want to operate on a bare directory.
  - Depends on: E-03
  - Expected outcome: a durable in-code note that two verbs guide and about twenty fall back silently, with a sample of the citations verified at HEAD rather than assumed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The git-blindness of root detection is a DECIDED question with a recorded rationale and a locking test, not an accident: `find_project_root`'s docstring (`project_context.py:279-281`) cites IPD awretrofit Order 06 OQ-01, and `tests/test_awretrofit_project_root_climb.py:71-75` enforces it. Any plan touching this area must read that first.
- `_find_git_root` (`:262-270`) is a pure, subprocess-free upward walk. It exists already, so the git probe needs no new capability, only a second caller.
- `is_project_dir` (`:345-350`) is the predicate the verbs branch on, and `resolve_verb_repo_root` (`:314-327`) is the shared resolver that falls back to cwd. The guidance-emitting verbs pair those two; the silent ones use only the second.
- `CommandResult` already has `next_actions` (`result_types.py:288`) and `to_agent_record` promotes the first one to the record's `next` key (`:440-444`). `NextAction` is a two-field dataclass (`:260-270`).
- THE AGENT SCHEMA AND THE VERBS DISAGREE ABOUT EXIT 3, and this is the discovery that most shapes the plan. `agent_schema.validate_agent_record` admits `exit` only in `(0, 1, 2)` (`:191-197`) and demands exactly 2 for an error record (`:275-279`), while these verbs use 3 for cannot-run. `assert_valid_agent_record` RAISES (`:315-319`) rather than degrading, and nothing catches it, so the failure is a traceback rather than a diagnostic.
- The two machine renderers are NOT equivalent on this path: `--json` renders without that validation and exits 3 cleanly, `--agent` validates and dies. Any fix must consider both or it widens the divergence.
- `aw attention --check` has its own earlier branch (`attention.py:2175-2193`) that returns a fail-closed-valid exit 0 outside a project. It must not be disturbed; it is a deliberate "nothing to violate" answer.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The message never probes for git, so it cannot offer the install. Reproduced verbatim in a bare `git init` directory. | `project_context.py:330-342`; measured at `44d4950d` |
| F-2 | The helper needed already exists and has exactly one caller today. | `_find_git_root` `:262-270`; sole call site `:439` |
| F-3 | THE ITEM'S EMIT-SITE CITATIONS HAD DRIFTED ~1190 LINES and were re-located by symbol: the item says `attention.py:1008`/`:1011`, actual sites are `:2200` and `:2203`, guarded at `:2174`. | read at `44d4950d` |
| F-4 | The second consumer is `aw ipd board`, at `cli.py:7203`/`:7206`. The item's `aw plans` spelling is not a registered command at all: `aw plans --agent` exits 2 from argparse with an invalid-choice error. | measured at `44d4950d` |
| F-5 | NEW DEFECT, worse than the item's own: `aw attention --agent` outside a project CRASHES. Unhandled `ValueError: Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2), got '3'; Error record must carry exit=2, got exit=3`, full traceback, exit 1. | measured unpiped at `44d4950d` in a bare `git init` dir |
| F-6 | `aw ipd board --agent` reproduces the same crash (exit 1). So it is the shared machine path, not one verb's bug. | measured at `44d4950d` |
| F-7 | The two machine renderers diverge on this condition: `--json` exits 3 cleanly with a well-formed payload; `--agent` dies. The human path also exits 3 correctly. | measured at `44d4950d`: human 3, `--json` 3, `--agent` 1 + traceback |
| F-8 | The contradiction is between two shipped contracts, so the fix is a contract decision rather than a bug fix: the verbs emit exit 3, the schema admits only 0/1/2 and requires 2 for an error record. | `attention.py:2199`, `:2204`; `agent_schema.py:191-197`, `:275-279` |
| F-9 | The raise is unguarded: `assert_valid_agent_record` raises and the renderer does not catch it. | `agent_schema.py:315-319`; `result_types.py:451`; `renderers.py:195` |
| F-10 | Root detection's git-blindness is deliberate, documented and test-locked, so the fix must stay in the message layer. | `project_context.py:279-281`; `tests/test_awretrofit_project_root_climb.py:71-75` |
| F-11 | `aw attention --check` outside a project already answers exit 0 "the view is valid" from a branch BEFORE the message, and must keep doing so. | `attention.py:2175-2193`; measured exit 0 |
| F-12 | The suggestion has a real target: `aw install` is a registered command with a full option surface, so `aw install <root>` is actionable advice rather than a guess. | `python3 -m agent_workflows install --help` at `44d4950d` |

## Proposed changes (ordered, validatable)

1. Probe for a git ancestor in `no_project_message` and offer `aw install <root>` when found (E-01).
2. Leave `find_project_root` git-blind, verify its locking test, and warn in code against widening (E-02).
3. Keep the fix in one place and confirm the caller set is exactly the two verbs (E-03).
4. Add the `NextAction` to both machine-path `CommandResult`s, only when a git root was found (E-04).
5. Resolve the exit-3-versus-schema contradiction so the `--agent` path stops crashing (E-05).
6. Pin the seven-case matrix with fixture-based tests, including the crash regression (E-06).
7. Record the twenty-verb silent-fallback asymmetry in code, spot-checking the citations (E-07).

## Deferred / out of scope (with reason)

- CONVERTING THE ~20 SILENTLY-FALLING-BACK VERBS to emit this guidance. A separate design question: some may legitimately operate on a bare directory, and doing twenty verbs on the way past would bury the actual fix. E-07 records the asymmetry instead.
- CHANGING WHAT COUNTS AS A PROJECT. Deliberately excluded by the item and by E-02; the git-blind rule is correct and test-locked.
- MAKING BARE `aw` SUGGEST AN INSTALL inside an unmanaged repo. Investigated and DROPPED by maintainer decision, recorded in the backlog item: the cause was documented non-recursive discovery behavior (a container directory holding nested repos, resolved with `aw conf add <container> to repos.search`), not a defect.
- A REPOSITORY-WIDE AUDIT of exit-3-versus-`aw.agent/v1` on other verbs. This plan fixes the two call sites on its own path; whether other verbs return 3 into an agent record is a real question and likely a separate item, but sweeping it here would make the fence unbounded. Worth filing after E-05 settles the semantics.
- RUNNING THE INSTALL AUTOMATICALLY. The message SUGGESTS; installing into a repository is a deliberate, consequential act and must stay the operator's.

## Scope check

- Over-scope: E-05 and its test fix a crash the backlog item does not mention. It is included because the item mandates the new fact be machine-readable on that exact `CommandResult`, and a record that cannot be emitted cannot carry it; the two are one deliverable, not two. `agent_workflows/cli.py` and `tests/test_attention.py` are in `Scope-Paths` for the same reason.
- Under-scope: the ~20 silent verbs are documented, not fixed. The broader exit-3-versus-schema audit is not attempted. If E-05's answer is to widen the schema, `docs/cli-output-contract.md` would also need an edit; that path is called out in OQ-01 rather than pre-declared, because the plan does not yet know which direction the reviewer will choose.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` at authoring time is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_awretrofit_project_root_climb.py tests/test_attention.py` for the focused surface. `test_bare_git_ancestor_is_not_a_root` must pass UNMODIFIED.
- The seven-case matrix from E-06, run manually in a temporary directory as well as in tests, with every exit code measured UNPIPED.
- The crash reproduction re-run after the fix, showing no traceback and a schema-valid record for both `aw attention --agent` and `aw ipd board --agent`.

## Spec / documentation sync

No `.spec.md` file governs `no_project_message`, so none is touched and none is declared in `Scope-Paths`. IF E-05 is resolved by WIDENING the agent schema to admit exit 3 (OQ-01 option b), then `docs/cli-output-contract.md` documents the `aw.agent/v1` payload contract and MUST be updated in the same change, and `Scope-Paths` must be extended before execution; that is stated here rather than pre-declared because the direction is the reviewer's to choose. If option (a) is chosen (record carries 2, process still exits 3), the divergence between the record's `exit` and `$?` must be documented in a comment at the emit site, since a consumer comparing them would otherwise reasonably call it a bug.

## Open questions

### OQ-01: For a cannot-run condition, should the agent record carry exit=2 while the process exits 3, or should the schema admit 3?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: BLOCKING, because the two options touch different files and one of them changes a published contract, so an executor cannot pick without authority. Option (a), record carries `exit=2` while the process still exits 3: preserves the human exit contract and the schema unchanged, cost is that the record's `exit` disagrees with `$?` for this condition, which a consumer could reasonably report as a bug. Option (b), widen `agent_schema` to admit 3 for `cannot-run`: makes the record honest and matches what the verbs already do, cost is a change to the published `aw.agent/v1` contract plus `docs/cli-output-contract.md` and a re-check of every consumer that switches on `exit`. EVIDENCE FOR (b): exit 3 for cannot-run is already the shipped behavior of the human and `--json` paths, so the schema is the outlier, and `--json` demonstrates a 3 flowing through a machine payload today without harm. EVIDENCE FOR (a): `(0, 1, 2)` is asserted in one place and may be relied on by consumers this plan cannot enumerate. Either way the crash must stop; the plan is blocked only on WHICH way.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the FULL stdout/stderr of `aw attention` run in a fresh `git init` directory with no AW layout, showing the four facts (verb, where it looked, the how-to-fix line, and the new "IS a git repository" line naming the root plus `aw install <root>`). Then paste the same command's output in a directory that is NOT a git repo and show it is byte-for-byte identical to the HEAD `44d4950d` output (paste both).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff -- tests/test_awretrofit_project_root_climb.py` showing NO change (empty diff), and paste the passing result of `python3 -m pytest tests/test_awretrofit_project_root_climb.py` naming `test_bare_git_ancestor_is_not_a_root`. Paste the inline comment added at the git probe warning against promoting it into `find_project_root`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `grep -rn "no_project_message" agent_workflows/` showing the definition plus exactly the two verbs' call sites and no new per-caller assembly, AND paste the improved message as emitted by BOTH verbs (`aw attention` and `aw ipd board`) in the same fixture directory, demonstrating the inheritance is real.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the raw `aw attention --agent` record from a git-but-not-AW directory showing `"next": "aw install <root>"`, and paste the record from a NON-git directory showing `next` is null. Both must be valid records (see V-05).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the BEFORE reproduction (the full `ValueError` traceback and unpiped exit 1) and the AFTER run for BOTH `aw attention --agent` and `aw ipd board --agent`, each showing no traceback, a valid record, and its unpiped exit code. State explicitly which OQ-01 option was implemented and paste the code comment recording that choice. Also paste `aw attention --json` before and after to show the two machine renderers did not diverge further.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste all seven cases (a)-(g) with commands, unpiped exit codes and output, plus the new tests' names and the `python3 -m pytest tests/test_awretrofit_project_root_climb.py tests/test_attention.py` summary line. For case (e) ALSO paste the test failing against pre-change code, proving the crash regression test bites.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the added comment, AND paste the spot-check: for at least four of the cited silent-fallback call sites, show the actual line at HEAD (for example `sed -n '341p' agent_workflows/backlog.py`) confirming a `resolve_verb_repo_root` call is really there, or report which citations had drifted. A comment copying the item's list unverified does not satisfy this item.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened. OQ-01 is BLOCKING and must be answered by the maintainer before execution, since it decides whether `docs/cli-output-contract.md` enters the fence.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
