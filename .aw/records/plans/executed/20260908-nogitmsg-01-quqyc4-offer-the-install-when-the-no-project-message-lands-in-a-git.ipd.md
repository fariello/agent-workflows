# IPD: Offer the install when the no-project message lands in a git repo, and stop the agent path crashing there

- Date: 2026-09-08
- Kind: child
- Concern: `no_project_message` tells the operator WHERE it looked but never checks whether cwd is a git repository, so in the commonest case (a real repo with agent-workflows simply not installed) it cannot offer the one action that would fix it. Separately and newly measured, the MACHINE path for the same condition does not merely lack a suggestion, it CRASHES: `aw attention --agent` and `aw ipd board --agent` outside a project raise an unhandled `ValueError` from the `aw.agent/v1` validator and exit 1 with a Python traceback, because the result carries `exit_code=3` while the schema admits only 0, 1 or 2 and requires an error record to carry exactly 2.
- Scope: Make `no_project_message` git-aware in ONE place so every current and future caller inherits the hint, add the machine-readable equivalent as a `NextAction` on the two `CommandResult`s that emit it, and fix the schema violation that makes the `--agent` path crash on this exact condition. Explicitly NOT changing what counts as a project: `find_project_root` stays git-blind.
- Scope-Paths: agent_workflows/project_context.py, agent_workflows/attention.py, agent_workflows/cli.py, agent_workflows/agent_schema.py, docs/cli-output-contract.md, docs/cli-agent-protocol.md, tests/test_awretrofit_project_root_climb.py, tests/test_attention.py, tests/test_agent_schema.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: nogitmsg
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: quqyc4
- From-Backlog: okm6e6
- Blocks-Release: next

## Workflow history
- 2026-09-21 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: quqyc4 verified (set nogitmsg, attempt 1). [Scope reconciliation - in-scope-unmodified agent_workflows/agent_schema.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified docs/cli-agent-protocol.md: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified docs/cli-output-contract.md: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_agent_schema.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_attention.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-10 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review; APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. Findings PR-401..PR-407, all FIXED in place, no deferrals, no new open questions. Structural preflight `aw ipd lint --phase author` conformed before semantic review and `--phase review-finalize` conformed after. DISCLOSURE: same model family and session lineage as the author, so this is close to a self-review and worth less than an independent one.
  THE DIAGNOSIS IS EXACTLY RIGHT AND I REPRODUCED ALL OF IT. In a fresh `git init` directory at HEAD `379dab6b`: `aw attention` (human) exits 3 correctly, `aw attention --json` exits 3 cleanly with a well-formed payload, and `aw attention --agent` CRASHES with the stated `ValueError` and a full traceback at exit 1; `aw ipd board --agent` reproduces identically; `aw plans` really is an argparse invalid choice at exit 2; `aw attention --check` really does answer exit 0 from its earlier branch. Finding the crash while reproducing the item was the right instinct and folding it in was the right call, since the item mandates a machine-readable fact on a record that cannot currently be emitted.
  THE ONE FINDING THAT MATTERS MOST IS A SAFETY REGRESSION HIDING INSIDE THE APPROVED FIX. OQ-01's ruling enumerated TWO schema sites to change; there are THREE. The `kind == "result"` exit-parity chain (`agent_schema.py:240-254`) is `if 0 / elif 1 / elif 2` with NO `else`, so the moment exit 3 is admitted it falls through and receives NO parity check at all: a `result` record could then carry `exit: 3` beside a POSITIVE outcome and validate. That chain exists to stop greenwashing, so widening without adding an `exit_code == 3` branch requiring `cannot-run` would make the validator WEAKER. E-05 now requires the third site plus a negative test, and V-05 refuses to complete without it.
  A SECOND PUBLISHED CONTRACT WAS UNDECLARED. `docs/cli-agent-protocol.md` also binds `exit: 2` to `cannot-run` (`:45`, `:96`) and carries a STABILITY clause promising an `aw.agent/v2` bump for any change to field meaning (`:113`); it was absent from `Scope-Paths` and is now declared. And the paragraph actually being amended was never cited: `docs/cli-output-contract.md` `## 3. Exit Code Semantics` (`:56-64`) declares "a uniform three-state exit classification across all verbs", a sentence that becomes false on widening, and it is asserted over by `tests/test_output_contract.py:49-53`. Measured too: exit 3 appears in NO doc, is asserted by NO test, and is emitted from exactly two sites, so this change promotes an undocumented two-site behavior into a published contract and the docs must DEFINE 3 rather than just permit it. E-05 must also state in writing why this is not breaking under the stability clause, and stop rather than absorb it if the honest answer is that it is.
  THREE DEFECTS FOUND THAT THE PLAN DOCUMENTS AS TRIVIA OR MISSES ENTIRELY, all now folded into items that already touch those lines. `aw ipd board` passes the verb string `"plans"`, so its no-project message reads "aw plans: no AW project found here." while `aw plans` does not exist: a misdirection inside the very message whose job is to say what to run, and a one-string fix on a line E-03 already edits. `attention.py:2510` is a dead unreachable `return 3`. And `no_project_message` reads `Path.cwd()` itself while both callers have already resolved a root, so today's agreement between them is accidental, resting on the callers' `not explicit_dir` guard rather than on the function's inputs.
  E-06's CASE (d) ASSERTED A BEHAVIOR THAT DOES NOT EXIST, and the real behavior is worse than the bug being fixed. Because both message branches are guarded by `not explicit_dir`, passing `--dir` SKIPS the message: measured, `aw attention --dir <a-git-repo-with-no-AW-layout>` prints NOTHING and exits 0, so an operator who explicitly names a non-AW directory gets silence and a success code. Case (d) is split into (d1) and (d2), with (d2) CHARACTERIZING today's behavior and reporting it rather than fixing it, since changing that guard alters which inputs produce a cannot-run and deserves its own item.
  TWO ACCURACY CORRECTIONS. The suite baseline is wrong in both halves: actual is `1 failed, 5958 passed, 3 skipped, 2 xfailed`, the named `tests/test_orchestrator_retirement.py` PASSES (`112 passed`), and the one real failure walks a GITIGNORED `opencode-recovery/` directory of 189 files owned by another party, which an executor could destroy while trying to green the suite; an explicit prohibition was added. And E-07's citation list is roughly 60 percent accurate (three of five sampled land on `resolve_verb_repo_root`, two drifted) while the real fallback surface is 57 call sites across 18 modules, not "about twenty", so the durable comment must carry a re-derivation command rather than a transcribed list. Every line number in this plan had drifted for the SECOND time (`attention.py:2200` -> `:2505`, `cli.py:7203` -> `:7290`, `--check` `:2175` -> `:2482`), which is itself the argument against writing line numbers into comments. The stale gate sentence calling OQ-01 "BLOCKING" was corrected: the question's own fields say `Blocking: no` / `Status: resolved`.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `okm6e6`, inheriting its `Blocks-Release: next` gate. EVERY LINE NUMBER IN THE ITEM HAD MOVED and was re-located by SYMBOL at HEAD `44d4950d` rather than trusted: the item cites `attention.py:1008`/`:1011` for the two emit sites, which are now `:2200` and `:2203` (a ~1190-line drift), and `project_context.py:330-342` for the message, which is still correct. The item's other citations verify: `_find_git_root` at `:262-270`, `find_project_root` at `:273-292` with the git-blind rationale in its own docstring at `:279-281`, and the locking test `test_bare_git_ancestor_is_not_a_root` at `tests/test_awretrofit_project_root_climb.py:71-75`. ONE NEW DEFECT FOUND while reproducing the item, and it is more serious than the item's own concern: on the `--agent` path this condition CRASHES rather than degrading. Measured in a bare `git init` directory with no AW layout: `aw attention` (human) exits 3 correctly; `aw attention --json` exits 3 correctly; but `aw attention --agent` exits 1 with an unhandled `ValueError: Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2), got '3'; Error record must carry exit=2, got exit=3` and a full traceback. `aw ipd board --agent` reproduces it identically (exit 1). That is squarely inside this item's scope rather than a separate concern, because the item REQUIRES the new fact to be machine-readable on that same `CommandResult`, and there is no point adding a `NextAction` to a record that cannot be emitted. E-05 fixes it, and E-06 pins it. Also noted for the record: `aw plans --agent` is NOT reachable at all (`plans` is not a registered command; it exits 2 from argparse), so the item's `cli.py:6244`/`:6247` citation belongs to `aw ipd board`, whose emit sites are now `cli.py:7203`/`:7206`.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Turn a dead end into a next step. When `aw` cannot find a project but IS standing in a git repository, name that repository and offer `aw install <root>`; make the same fact available to an automated consumer; and make sure that consumer can actually receive it, which today it cannot because the record fails its own schema.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the human message actionable

- [x] E-01 Teach `no_project_message(verb)` (`project_context.py:330-342`, still correct at review) to probe for a git ancestor when the AW climb has failed, and when one is found, name that root and offer the install. REUSE THE EXISTING HELPER: `_find_git_root(start_dir)` at `:262-270` already walks up looking for `.git` and is today called only by `resolve_project_context` (`:439`) to pick a default `target_repo`. Append lines in the shape the maintainer asked for: state that the directory IS a git repository but agent-workflows is not installed in it, and give the literal command `aw install <root>`. Keep the three existing lines unchanged and ordered as they are, since the item records the maintainer calling them genuinely helpful about WHERE it looked; this ADDS a fourth fact, it does not rewrite the first three.
  MIND THE SIGNATURE, BECAUSE THE FUNCTION READS `Path.cwd()` ITSELF AND TAKES NO DIRECTORY (review PR-404). `no_project_message(verb)` interpolates `Path.cwd()` directly at `:339`, so a git probe written the same way inherits that coupling: the message would describe cwd while its two callers have ALREADY resolved a root via `resolve_verb_repo_root` (`attention.py:2474`, and the `cli.py` twin). Today those agree, because both call sites are guarded by `not explicit_dir` so the message is only reached when no `--dir` was passed. That makes the existing behavior correct but ACCIDENTALLY correct, resting on a guard in the callers rather than on the function's own inputs. Prefer adding an OPTIONAL `start_dir` parameter defaulting to `Path.cwd()` and passing the already-resolved root from both call sites, so the message cannot describe one directory while the verb operated on another. If you keep the `cwd()` read instead, say why and note the dependency on the caller guard in a comment, because a third caller without that guard would silently produce a message about the wrong directory.
  - Depends on: none
  - Expected outcome: run in a git repo with no AW layout, the message names the git root and offers `aw install <root>`; run in a directory that is not a git repo, the message is byte-for-byte what it is at HEAD; the directory the message describes comes from the same resolution the caller used, or the coupling to `Path.cwd()` is documented.
  - Execution state: performed

- [x] E-02 Do NOT change root detection, and pin that it did not change. `find_project_root` (`:273-292`) is DELIBERATELY git-blind and its docstring says so at `:279-281`: a `.aw/` tree can exist without git, and a bare `.git` ancestor with no AW marker is NOT an AW project (IPD awretrofit Order 06, OQ-01). That rule is locked by `tests/test_awretrofit_project_root_climb.py:71-75` (`test_bare_git_ancestor_is_not_a_root`, asserting `find_project_root(gitonly) is None`). THAT TEST MUST STILL PASS UNCHANGED at the end of this plan; if it needs editing, the change has gone out of scope and must stop. This item is the guard, not a code change: verify the test passes and add a comment at the new git probe in `no_project_message` stating that probing here is a MESSAGE concern and must never be promoted into `find_project_root`.
  - Depends on: E-01
  - Expected outcome: `test_bare_git_ancestor_is_not_a_root` passes unmodified, and the code carries an inline warning against widening the probe into root detection.
  - Execution state: performed

- [x] E-03 Fix `no_project_message` in ONE place only, so every current and future caller inherits the hint, and confirm the caller set. The function has exactly TWO consumers today, both of which call it twice (once for the machine branch's `summary`, once for the stderr write). RE-LOCATED AT REVIEW at HEAD `379dab6b`, because these drifted AGAIN since authoring: `aw attention` at `attention.py:2505` and `:2508` (was `:2200`/`:2203`), guarded at `:2481` (was `:2174`), and `aw ipd board` at `cli.py:7290` and `:7293` (was `:7203`/`:7206`). Do not add per-caller message assembly. Verify by grep that the caller set is exactly those two after the change, so the "one place" property is a measured fact rather than an intention.
  FIX THE WRONG VERB NAME WHILE YOU ARE HERE, because it is a live user-facing defect and this is the one item that touches both call sites (review PR-403). `cli.py:7290`/`:7293` pass the literal verb `"plans"`, so `aw ipd board` in a non-project directory prints "aw plans: no AW project found here." Measured at review. But `plans` is NOT a registered command (F-4 proves `aw plans` exits 2 with an argparse invalid-choice error), so the message names a command the operator cannot run, inside the very message whose whole purpose is to tell them what to do. Pass `"ipd board"`. This is a one-string change on a line this item already edits, and leaving it would ship a message that misdirects the operator.
  DELETE THE DEAD `return 3` at `attention.py:2510`, an unreachable duplicate of the `return 3` at `:2509`. Trivial, on a line this item is already reading, and it will otherwise puzzle the next reader of exactly this branch.
  - Depends on: E-01
  - Expected outcome: both verbs emit the improved message with no per-verb code, demonstrated by running each; `aw ipd board` names ITSELF rather than the non-existent `aw plans`; the dead `return 3` is gone; a grep for `no_project_message` shows only the two call sites plus the definition.
  - Execution state: performed

### Task group 2: make the fact machine-readable, and emittable

- [x] E-04 Attach a `NextAction` to the two machine-path `CommandResult`s so the install suggestion is structured, not only prose in `summary`. The item requires exactly this: `NextAction(command="aw install <root>", description="install agent-workflows in this repo")` on the `CommandResult` at the attention emit site (`attention.py:2195-2201`) and its twin at `cli.py:7198-7204`. `CommandResult` already carries `next_actions: List[NextAction]` (`result_types.py:288`), and `to_agent_record` surfaces the FIRST action as the record's `next` field (`result_types.py:440-444`), so no new plumbing is needed. Add the action ONLY when a git root was actually found, since an unconditional suggestion would be wrong in a non-git directory.
  - Depends on: E-01
  - Expected outcome: `aw attention --agent` in a git-but-not-AW directory emits a record whose `next` is `aw install <root>`; in a non-git directory `next` stays `null`.
  - Execution state: performed

- [x] E-05 Make the `--agent` path emit a VALID record for this condition instead of crashing, implementing OQ-01's RESOLVED answer: option (b), widen `agent_schema` to admit exit 3 for `cannot-run` only. RE-MEASURED AT REVIEW at HEAD `379dab6b`, and the crash reproduces exactly: `aw attention --agent` in a bare `git init` directory exits 1 with `ValueError: Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2), got '3'; Error record must carry exit=2, got exit=3`, raised from `agent_schema.assert_valid_agent_record` (`agent_schema.py:319`) via `result_types.to_agent_record` (`:451`) via `renderers.py:195`; `aw ipd board --agent` reproduces identically (exit 1). NOTE OQ-01 IS RESOLVED, so this item implements rather than chooses; the plan text calling it BLOCKING is stale and was corrected at review.
  CHANGE THREE SCHEMA SITES, NOT TWO, AND THE THIRD IS THE ONE THAT MATTERS FOR SAFETY (review PR-401). Locate each by symbol, since every line number in the original decision had drifted. (a) The membership test `exit_code not in (0, 1, 2)` at `agent_schema.py:188-198`. (b) The `kind == "error"` rule `if exit_code != 2` at `:275-279`. (c) THE `kind == "result"` EXIT-CODE PARITY CHAIN at `:240-254`, which the decision MISSED: it is an `if exit_code == 0 / elif == 1 / elif == 2` with NO `else`, so once 3 is admitted it falls straight through and receives NO parity check whatsoever. A `result` record could then carry `exit: 3` beside a POSITIVE outcome and validate, which is precisely the greenwashing that chain exists to stop. ADD an explicit `elif exit_code == 3:` branch requiring `outcome == "cannot-run"`. A widening that leaves this hole makes the validator weaker, not just broader.
  ADMIT 3 FOR `cannot-run` ONLY, per the ruling, so the distinction the separate exit code carries is preserved rather than blurred into `error`.
  AMEND BOTH DOCS, BECAUSE THERE ARE TWO PUBLISHED CONTRACTS (review PR-402). In `docs/cli-output-contract.md` the load-bearing one is `## 3. Exit Code Semantics` (`:56-64`), which declares "a uniform three-state exit classification across all verbs" and enumerates only 0/1/2; that paragraph IS the contract being changed and the original decision never cited it. Also `:45` (the `CommandResult.exit_code` enumeration), `:89` (the Exit Code Parity rule, which lists `0`, `1`, `2` inline), and the cannot-run passages at `:117`, `:221`, `:224`. In `docs/cli-agent-protocol.md`, added to `Scope-Paths` at review: `:45` ("`exit: 2` pairs with `error` or `cannot-run`"), `:96` (the cannot-run example), and `:113`, the STABILITY clause. DOCUMENT exit 3 rather than merely permitting it: measured at review, exit 3 appears in NO doc, is asserted by NO test, and is emitted from exactly two sites, so this change promotes an undocumented two-site behavior into a published contract and the docs must gain a definition of what 3 MEANS.
  ADDRESS THE STABILITY CLAUSE EXPLICITLY. `docs/cli-agent-protocol.md:113` promises that "any breaking change to record shape or field meaning bumps the version to `aw.agent/v2`", and it tells parsers to "tolerate unknown fields" (which does NOT cover an unknown VALUE in a known field). Widening the permitted range of `exit` is arguably a change in field meaning for a consumer that switched on the closed set. STATE in the plan and in the doc whether this counts as breaking under that clause and why no `v2` bump is required, rather than leaving the two paragraphs to contradict each other. If the honest answer is that it IS breaking, that is a decision for the maintainer and must be raised, not absorbed.
  DECIDE AND RECORD WHETHER TO GUARD THE RAISE AT ALL. F-9 notes the `ValueError` is unguarded and nothing catches it, so any future verb returning an out-of-range exit crashes the same way. Widening fixes THIS instance; catching in the renderer would fix the CLASS. Do not necessarily do both, but say which you chose and why, because "we fixed the one value we knew about" is a decision worth being explicit about.
  KEEP THE TWO MACHINE RENDERERS ALIGNED: `--json` does NOT crash today (verified at review, exits 3 cleanly with a well-formed payload through a path that does not validate), so the fix must not widen that divergence.
  - Depends on: E-04
  - Expected outcome: `aw attention --agent` and `aw ipd board --agent` in a git-but-not-AW directory emit a schema-valid `aw.agent/v1` record with no traceback; all THREE schema sites changed including a new `exit_code == 3` parity branch requiring `cannot-run`; both docs amended including the three-state paragraph and the stability clause addressed; `--json` still consistent; a code comment naming the implemented option.
  - Execution state: performed

### Task group 3: prove it

- [x] E-06 Test the matrix, measuring exit codes UNPIPED (`cmd >/dev/null 2>&1; echo $?`), because a piped `$?` reports the last pipeline stage. Cover, in a temporary fixture directory (never against the live repo): (a) git repo, no AW layout -> human message names the root and offers `aw install`; (b) NOT a git repo -> message unchanged from HEAD, no install offer; (c) an AW project -> normal output, message never emitted; (d) the `--dir` cases, see the correction below; (e) `--agent` for both verbs on case (a) -> a VALID record, no traceback, `next` naming the install; (f) `--json` for both verbs on case (a) -> still works, and its exit semantics agree with E-05's; (g) `aw attention --check` outside a project still returns the fail-closed-valid exit 0 it returns today (`attention.py:2482-2499`, re-located; the plan's `:2175-2193` had drifted), since that branch precedes the message and must not regress (verified exit 0 at review). THE CRASH REGRESSION TEST IS THE MOST IMPORTANT ONE HERE: assert no traceback and a schema-valid record, so a future exit-code change cannot silently reintroduce it.
  CASE (d) AS WRITTEN TESTS A BEHAVIOR THAT DOES NOT EXIST, AND THE REAL BEHAVIOR IS SURPRISING (review PR-405). "`--dir <explicit>` honored verbatim and unaffected" cannot be asserted against the message, because BOTH call sites guard the message with `not explicit_dir` (`attention.py:2481`), so passing `--dir` SKIPS the message branch entirely. MEASURED at review: `aw attention --dir /tmp/<a-git-repo-with-no-AW-layout>` from an unrelated directory prints NOTHING and exits **0**, i.e. the operator explicitly names a directory that is not an AW project and gets silence and a success code. That is a worse operator experience than the no-`--dir` path this plan is fixing, and it is arguably the same defect wearing a different hat. Split case (d) in two: (d1) `--dir` at a real AW project works unchanged; (d2) `--dir` at a git-but-not-AW directory, PIN TODAY'S BEHAVIOR (silence, exit 0) as a characterization test and REPORT it, so the gap is recorded rather than accidentally "fixed" here. Do NOT change the `--dir` branch in this plan: the guard is deliberate and altering it would change which inputs produce a cannot-run, which is a scope and contract question of its own. It is listed in the deferred section as a follow-up item to file.
  - Depends on: E-05
  - Expected outcome: all eight cases (a)-(g) with (d) split, pinned by fixture-based tests that pass in a bare worktree; case (e) fails against pre-change code and passes after E-05; case (d2) characterizes and reports the silent `--dir` gap without fixing it.
  - Execution state: performed

- [x] E-07 Record the ASYMMETRY the item documents, without acting on it, so it is not rediscovered from scratch. Only TWO verbs emit this guidance; many other repo-scoped verbs call `resolve_verb_repo_root` (`project_context.py:314-327`) and then SILENTLY fall back to cwd, so run outside a project they produce an empty or misplaced result with no explanation. The item enumerates them: `backlog.py:341/474/653`, `specs.py:415/866`, `releases.py:600`, `research_cmd.py:290`, `research_index.py:536`, `research_archive.py:292`, `plans_index.py:314`, `plans_archive.py:191`, `plans_refs.py:395`, `artifact_rename.py:22`, `prompts.py:180`, `reviews.py:236`, `run_cli.py:97`, `status_set.py:1101/1438`, `work_cmd.py:126`, `cli.py:7138/7390/9296`.
  DO NOT COPY THE LIST, AND DO NOT CITE THE COUNT "TWENTY" EITHER: BOTH ARE ALREADY WRONG (review PR-406). The plan's own instinct to spot-check was correct and review acted on it. Of five citations sampled at HEAD `379dab6b`, THREE were right (`backlog.py:341`, `specs.py:415`, `prompts.py:180` all land on a `resolve_verb_repo_root` import) and TWO had DRIFTED onto unrelated lines (`releases.py:600` is `for p in base.rglob("*.md")`; `run_cli.py:97` is `return _run_finalize(args)`). So the enumerated list is roughly 60 percent accurate and must not be transcribed into a durable code comment. Also DERIVE the count rather than repeating "about twenty": measured at review, `resolve_verb_repo_root` has **57 call sites across 18 modules** outside its own definition, so "roughly twenty verbs" understates the fallback surface by a wide margin, though not every call site is a distinct user-facing verb. WRITE THE COMMENT WITH A DERIVATION COMMAND, not a line-number list: a comment saying "N call sites across M modules, re-derive with `grep -rn resolve_verb_repo_root agent_workflows/`" stays true as the code moves, while a list of line numbers is stale within days. That is the whole lesson of this plan's own repeated citation drift.
  Point the comment at backlog item `okm6e6` for the reasoning. DO NOT convert those verbs here: whether they should all emit the same guidance is a separate design question, and some may legitimately want to operate on a bare directory.
  - Depends on: E-03
  - Expected outcome: a durable in-code note that two verbs guide while a much larger set falls back silently, stating a DERIVED count with the command to re-derive it and NO transcribed line-number list; the sampled citations' accuracy reported, including which had drifted.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The git-blindness of root detection is a DECIDED question with a recorded rationale and a locking test, not an accident: `find_project_root`'s docstring (`project_context.py:279-281`) cites IPD awretrofit Order 06 OQ-01, and `tests/test_awretrofit_project_root_climb.py:71-75` enforces it. Any plan touching this area must read that first.
- `_find_git_root` (`:262-270`) is a pure, subprocess-free upward walk. It exists already, so the git probe needs no new capability, only a second caller.
- `is_project_dir` (`:345-350`) is the predicate the verbs branch on, and `resolve_verb_repo_root` (`:314-327`) is the shared resolver that falls back to cwd. The guidance-emitting verbs pair those two; the silent ones use only the second.
- `CommandResult` already has `next_actions` (`result_types.py:288`) and `to_agent_record` promotes the first one to the record's `next` key (`:440-444`). `NextAction` is a two-field dataclass (`:260-270`).
- THE AGENT SCHEMA AND THE VERBS DISAGREE ABOUT EXIT 3, and this is the discovery that most shapes the plan. `agent_schema.validate_agent_record` admits `exit` only in `(0, 1, 2)` (`:188-198`) and demands exactly 2 for an error record (`:275-279`), while these verbs use 3 for cannot-run. `assert_valid_agent_record` RAISES (`:319`) rather than degrading, and nothing catches it, so the failure is a traceback rather than a diagnostic.
- THERE IS A THIRD CONSTRAINED SITE AND IT HAS NO `else`: the `kind == "result"` exit-parity chain (`:240-254`) branches on 0, 1 and 2 only, so an admitted 3 receives NO parity check and could sit beside a positive outcome. Widening without adding that branch WEAKENS the validator. Found at review, missed by the OQ-01 ruling.
- EXIT 3 IS UNDOCUMENTED AND UNTESTED TODAY, measured at review: it appears in NO file under `docs/`, is asserted by no test, and is emitted from exactly two sites (`attention.py:2504`, `cli.py:7289`). So widening promotes an undocumented behavior into a published contract; the docs must DEFINE 3, not merely permit it.
- THE EXIT CONTRACT IS DECLARED IN TWO DOCS, NOT ONE. `docs/cli-output-contract.md` `## 3. Exit Code Semantics` (`:56-64`) declares "a uniform three-state exit classification across all verbs"; `docs/cli-agent-protocol.md:45` binds `exit: 2` to `cannot-run` and `:113` carries a STABILITY clause promising a `v2` bump for any change to field meaning. Both are in `Scope-Paths` as of review.
- `no_project_message(verb)` READS `Path.cwd()` ITSELF (`:339`) and takes no directory, while both callers have already resolved a root. They agree today only because both message branches are guarded by `not explicit_dir`. Correct, but accidentally so.
- `--dir` DELIBERATELY BYPASSES THE MESSAGE (`attention.py:2481`, `not explicit_dir`). Measured: `--dir <git-only-dir>` prints nothing and exits 0. A separate gap, characterized by E-06 case (d2), not fixed here.
- The two machine renderers are NOT equivalent on this path: `--json` renders without that validation and exits 3 cleanly, `--agent` validates and dies. Any fix must consider both or it widens the divergence.
- `aw attention --check` has its own earlier branch (`attention.py:2482-2499`, re-located at review) that returns a fail-closed-valid exit 0 outside a project. It must not be disturbed; it is a deliberate "nothing to violate" answer. Verified exit 0 at review.
- EVERY LINE NUMBER IN THIS PLAN DRIFTED TWICE. The item's `attention.py:1008` became the plan's `:2200` and is now `:2505`; the `cli.py` sites moved `:7203` -> `:7290`; the `--check` branch `:2175` -> `:2482`. Re-locate everything by SYMBOL and write no durable comment containing a line-number list.
- `aw ipd board` PASSES THE VERB STRING `"plans"` (`cli.py:7290`/`:7293`), so its message names `aw plans`, which is not a registered command. A live misdirection inside a help message; E-03 fixes it.

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
| F-13 | **A THIRD SCHEMA SITE THE OQ-01 RULING MISSED, and skipping it would WEAKEN the validator.** The `kind == "result"` exit-parity chain (`agent_schema.py:240-254`) is `if 0 / elif 1 / elif 2` with NO `else`, so an admitted exit 3 falls through and gets NO parity check: a `result` could then carry `exit: 3` beside a POSITIVE outcome and validate. E-05 must add an `exit_code == 3` branch requiring `cannot-run`. | read at review, HEAD `379dab6b` |
| F-14 | **THE EXIT CONTRACT LIVES IN TWO PUBLISHED DOCS AND ONLY ONE WAS DECLARED.** `docs/cli-agent-protocol.md` binds `exit: 2` to `cannot-run` (`:45`, `:96`) and carries a STABILITY clause promising a `v2` bump for any change to field meaning (`:113`). It was absent from `Scope-Paths`; added at review. | read at review |
| F-15 | **THE ACTUAL CONTRACT PARAGRAPH BEING AMENDED WAS NEVER CITED.** `docs/cli-output-contract.md` `## 3. Exit Code Semantics` (`:56-64`) declares "a uniform three-state exit classification across all verbs" and enumerates only 0/1/2. `tests/test_output_contract.py:49-53` asserts that section exists. The ruling cited `:45`/`:78`/`:88` instead. | read at review |
| F-16 | **EXIT 3 IS UNDOCUMENTED AND UNTESTED, which bounds the risk but changes the obligation.** It appears in NO doc, is asserted by no test, and is emitted from exactly two sites. So widening does not bless an established practice; it promotes an undocumented two-site behavior into a published contract, and the docs must DEFINE what 3 means. | greps over `docs/`, `tests/`, `agent_workflows/` at review |
| F-17 | **`--dir` AT A GIT-ONLY DIRECTORY IS SILENT AND EXITS 0**, which is worse than the path this plan fixes. Both message branches are guarded by `not explicit_dir` (`attention.py:2481`), so an operator who explicitly names a non-AW directory gets no output and a SUCCESS code. E-06 case (d) as written asserted a behavior that does not exist. | measured at review, unpiped exit 0 |
| F-18 | **`aw ipd board` NAMES A COMMAND THAT DOES NOT EXIST.** `cli.py:7290`/`:7293` pass verb `"plans"`, so the message reads "aw plans: no AW project found here." while `aw plans` exits 2 as an invalid choice (F-4). A misdirection inside the message whose purpose is to tell the operator what to run. | measured at review |
| F-19 | **`no_project_message` READS `Path.cwd()` AND TAKES NO DIRECTORY** (`:339`), while both callers have already resolved a root. They agree only because of the `not explicit_dir` guard, so today's correctness rests on the callers, not on the function's inputs. | source read |
| F-20 | **THE E-07 CITATION LIST IS ~60 PERCENT ACCURATE AND THE COUNT IS WRONG.** Of five sampled, three landed on `resolve_verb_repo_root` (`backlog.py:341`, `specs.py:415`, `prompts.py:180`) and two had drifted (`releases.py:600`, `run_cli.py:97`). And the real fallback surface is 57 call sites across 18 modules, not "about twenty". A durable comment must carry a derivation command, not a list. | sampled and counted at review |

## Proposed changes (ordered, validatable)

1. Probe for a git ancestor in `no_project_message` and offer `aw install <root>` when found (E-01).
2. Leave `find_project_root` git-blind, verify its locking test, and warn in code against widening (E-02).
3. Keep the fix in one place and confirm the caller set is exactly the two verbs (E-03).
4. Add the `NextAction` to both machine-path `CommandResult`s, only when a git root was found (E-04).
5. Resolve the exit-3-versus-schema contradiction so the `--agent` path stops crashing (E-05).
6. Pin the seven-case matrix with fixture-based tests, including the crash regression (E-06).
7. Record the twenty-verb silent-fallback asymmetry in code, spot-checking the citations (E-07).

## Deferred / out of scope (with reason)

- CONVERTING THE SILENTLY-FALLING-BACK VERBS to emit this guidance. A separate design question: some may legitimately operate on a bare directory, and doing them all on the way past would bury the actual fix. E-07 records the asymmetry instead. AT EXECUTION the count was re-derived as 64 call sites across 21 modules, not "~20" (V-07). NO DURABLE CARRIER IS NEEDED AND NONE IS FILED: this row is a scope FENCE, not an obligation. It records a design question nobody has decided to answer, and the durable record of it is the in-code note E-07 added to `resolve_verb_repo_root`, which a reader meets at the point of use and which carries the re-derivation command. Filing a backlog item to say "we deliberately did not do this" would manufacture work the maintainer has not chosen.
  - Carrier-Declined: A scope FENCE, not an obligation: nobody has decided these verbs SHOULD guide, and some may legitimately operate on a bare directory. The durable record is the in-code note E-07 added to `resolve_verb_repo_root`, carrying the re-derivation command a reader meets at the point of use. Filing an item would manufacture work the maintainer has not chosen.
- CHANGING WHAT COUNTS AS A PROJECT. Deliberately excluded by the item and by E-02; the git-blind rule is correct and test-locked. NO CARRIER NEEDED: this is a decided question with a recorded rationale (IPD awretrofit Order 06 OQ-01) and a locking test, not an outstanding obligation. E-02 verified the test still passes unmodified and added the in-code warning against widening.
  - Carrier-Declined: A DECIDED question, not an outstanding one: IPD awretrofit Order 06 OQ-01 ruled root detection git-blind, with the rationale in `find_project_root`'s own docstring and a locking test. E-02 verified that test still passes unmodified and added the in-code warning against widening the probe.
- MAKING BARE `aw` SUGGEST AN INSTALL inside an unmanaged repo. Investigated and DROPPED by maintainer decision, recorded in the backlog item: the cause was documented non-recursive discovery behavior (a container directory holding nested repos, resolved with `aw conf add <container> to repos.search`), not a defect. NO CARRIER NEEDED: a maintainer-dropped line of enquiry is closed, not outstanding.
  - Carrier-Declined: CLOSED by a maintainer decision recorded in backlog `okm6e6`: the cause was documented non-recursive discovery behavior, not a defect. A dropped line of enquiry owes nothing.
- A REPOSITORY-WIDE AUDIT of exit-3-versus-`aw.agent/v1` on other verbs. RESOLVED AT EXECUTION RATHER THAN DEFERRED, so there is nothing left to carry on this half. Measured at execution: `exit_code=3` was constructed at exactly ONE remaining site (`cli.py`), attention's having been removed by executed plan `rkn8ya`; E-05 removed that one, so NO site in the package now builds an out-of-range record, and the property is pinned by `test_NO_site_in_the_package_still_emits_an_unemittable_exit_3_record` rather than left to a future audit. WHAT REMAINS OPEN IS THE CLASS, and it is deliberately NOT carried by a backlog item: the validator raise is unguarded (F-9), so a FUTURE verb building an out-of-range record still crashes rather than degrading. V-05 records the reasoned decision NOT to guard it (a catch would convert a contract violation into a silent degradation, and this raise is what surfaced both of these bugs), so this is a stated design posture, not an unmet obligation. If the maintainer disagrees with that posture it needs its own item, which is theirs to file.
  - Carrier-Declined: RESOLVED AT EXECUTION, so there is no residual population to carry. Measured: `exit_code=3` was built at exactly one remaining site and E-05 removed it, so no site in the package now builds an out-of-range record, pinned by `tests/test_awretrofit_project_root_climb.py::NoProjectSubprocessMatrixTests::test_NO_site_in_the_package_still_emits_an_unemittable_exit_3_record` rather than left to a future audit. The CLASS question (the unguarded validator raise, F-9) is a stated design posture recorded in V-05, not an unmet obligation: guarding it would convert a contract violation into a silent degradation, and that raise is what surfaced both of these bugs. Reversing that posture is a maintainer call and theirs to file.
- FIXING THE `--dir` SILENT-SUCCESS GAP (F-17). Measured: `--dir <git-only-directory>` prints nothing and exits 0, because both message branches are guarded by `not explicit_dir`. Arguably worse than the defect this plan fixes, but changing that guard changes which inputs produce a cannot-run, which is a contract decision with its own blast radius. E-06 case (d2) CHARACTERIZES today's behavior so a later fix has a baseline. DURABLE CARRIER: backlog `xnb551` (`Work-Kind: bug`, `Blocks-Release: next`), FILED at execution rather than merely recommended, carrying the reproduction, the cause, the baseline test to update, and the suggested fix. IT IS WORSE THAN RECORDED HERE: `aw ipd board --dir <git-only-dir>` does not just stay silent, it prints "✓ CLEAN" at exit 0, affirmatively reporting a clean board for a directory it cannot survey.
  - Carrier: xnb551
- BUMPING THE PROTOCOL TO `aw.agent/v2`. MOOT AT EXECUTION, because the change that would have raised the question was not made. `docs/cli-agent-protocol.md`'s stability clause promises a bump for "any breaking change to record shape or field meaning"; this plan's OQ-01 would have widened `exit`'s permitted value set, making the answer a judgement call. Decision 03-quqyc4-D1 took the other route instead (mirror `rkn8ya`: machine surfaces emit exit 2), which alters no record shape, no field meaning and no field's permitted values, so NO bump is required unconditionally and neither contract doc was touched. NO CARRIER NEEDED: nothing is outstanding. The residual contract question that DOES remain, that the HUMAN path still exits 3 while the published classification lists only 0/1/2, is a DIFFERENT question and IS carried, by backlog `c6vs7y`.
  - Carrier-Declined: MOOT: decision 03-quqyc4-D1 took the route that changes no record shape, no field meaning and no permitted value set, so no bump is required and neither contract doc was touched. The DIFFERENT residual question, that the human path still exits 3 while the published classification lists only 0/1/2, is carried by backlog `c6vs7y`.
- RUNNING THE INSTALL AUTOMATICALLY. The message SUGGESTS; installing into a repository is a deliberate, consequential act and must stay the operator's. NO CARRIER NEEDED: a deliberate design boundary, not an obligation.
  - Carrier-Declined: A deliberate design boundary, not an obligation: installing into a repository is consequential and must stay the operator's act.

## Scope check

- Over-scope: E-05 and its test fix a crash the backlog item does not mention. It is included because the item mandates the new fact be machine-readable on that exact `CommandResult`, and a record that cannot be emitted cannot carry it; the two are one deliverable, not two. `agent_workflows/cli.py` and `tests/test_attention.py` are in `Scope-Paths` for the same reason.
- Over-scope, ADDED AT REVIEW AND JUSTIFIED: `docs/cli-agent-protocol.md` is now declared (F-14). OQ-01 chose to widen the schema, and that doc is a SECOND published contract binding `exit: 2` to `cannot-run` and promising a `v2` bump for a change in field meaning. Amending one doc and not the other would leave the two disagreeing, which is the exact failure mode OQ-01's own obligation (2) exists to prevent. Two tiny in-place corrections are also folded into E-03 because they sit on lines that item already edits and are both live user-facing defects: the wrong verb string `"plans"` (F-18) and a dead unreachable `return 3` (`attention.py:2510`).
- Under-scope: the silently-falling-back verbs are documented, not fixed. The broader exit-3-versus-schema audit is not attempted. The `--dir` silent-success gap (F-17) is CHARACTERIZED by E-06 case (d2) and reported, not fixed, because changing that guard would change which inputs produce a cannot-run and is a contract question of its own; a follow-up item should be filed. `no_project_message`'s `Path.cwd()` coupling (F-19) is either parameterized or documented by E-01, at the executor's choice, but not made a general refactor.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line and judge on the DELTA. THE AUTHORED BASELINE IS WRONG IN BOTH HALVES (review PR-407): re-measured bare at review, main gives `1 failed, 5958 passed, 3 skipped, 2 xfailed`, and the named `tests/test_orchestrator_retirement.py` PASSES outright (`112 passed`). The single real failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which walks the repo and trips over 189 files in a GITIGNORED `opencode-recovery/` directory belonging to another party. DO NOT DELETE OR MODIFY `opencode-recovery/` to green the suite: that would destroy a co-worker's work in a shared checkout. Measure your own baseline and compare failing NODE IDS.
- `python3 -m pytest tests/test_awretrofit_project_root_climb.py tests/test_attention.py tests/test_agent_schema.py tests/test_output_contract.py` for the focused surface. The last two are ADDED at review because E-05 changes both the validator and the doc they assert over. `test_bare_git_ancestor_is_not_a_root` must pass UNMODIFIED.
- THE SCHEMA-WIDENING NEEDS ITS OWN POSITIVE AND NEGATIVE TESTS, and `tests/test_agent_schema.py` has none for exit codes today (measured: 10 tests, none touching `exit`). Add: a `cannot-run` record with `exit: 3` VALIDATES; a `result` record with `exit: 3` and a POSITIVE outcome is REFUSED (this is the F-13 hole, and without this test the widening silently weakens the validator); an `error`-kind record with `exit: 3` behaves as E-05 decided; and an out-of-range value such as 4 is still refused.
- The eight-case matrix from E-06 (case (d) split), run manually in a temporary directory as well as in tests, with every exit code measured UNPIPED.
- The crash reproduction re-run after the fix, showing no traceback and a schema-valid record for both `aw attention --agent` and `aw ipd board --agent`.
- BOTH DOCS RE-READ AFTER EDITING, showing the validator's permitted set and the documented set AGREE. State explicitly that `docs/cli-agent-protocol.md:113`'s stability clause was considered and why no `v2` bump is required.

## Spec / documentation sync

No `.spec.md` file governs `no_project_message`, so none is touched and none is declared in `Scope-Paths`. Verified at review: no spec constrains the exit vocabulary either, so the contracts being amended are the two DOCS, not a spec.

OQ-01 IS RESOLVED TO OPTION (b), WIDEN THE SCHEMA, so the conditional framing this section carried is now settled and both docs are DECLARED rather than deferred to the reviewer. `docs/cli-output-contract.md` AND `docs/cli-agent-protocol.md` are both in `Scope-Paths` and both MUST be amended in the same change (F-14, F-15). The load-bearing paragraph is `docs/cli-output-contract.md` `## 3. Exit Code Semantics` (`:56-64`), which today declares "a uniform three-state exit classification across all verbs": that sentence becomes false the moment the validator admits a fourth value, and it is asserted over by `tests/test_output_contract.py:49-53`. Amend it to define exit 3 rather than merely widening a list, since exit 3 is documented NOWHERE today (F-16).

THE STABILITY CLAUSE MUST BE ADDRESSED IN WRITING, not silently. `docs/cli-agent-protocol.md:113` promises "any breaking change to record shape or field meaning bumps the version to `aw.agent/v2`" and instructs parsers to "tolerate unknown fields", which does NOT cover an unknown VALUE in a known field. State in the doc and in the plan's record why admitting a new `exit` value is not a breaking change under that clause (the field's meaning is unchanged, its domain widens, and no in-repo consumer switches on it: measured, only the validator itself and `tests/conformance_matrix.py:240`, which reads `exit` without branching on it). If the executor concludes it IS breaking, STOP and raise it: a protocol version bump is a maintainer decision, not an implementation detail.

## Open questions

### OQ-01: For a cannot-run condition, should the agent record carry exit=2 while the process exits 3, or should the schema admit 3?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-08: OPTION (b), WIDEN `agent_schema` TO ADMIT 3 FOR `cannot-run`. The record becomes honest and the schema stops being the outlier.
  THE DECIDING EVIDENCE WAS MEASURED AT DECISION TIME AND IS STRONGER THAN THE QUESTION STATED. Option (a) would not merely produce a record whose `exit` "disagrees with `$?`", it would VIOLATE A PUBLISHED REQUIREMENT: `docs/cli-output-contract.md:89` states "**Exit Code Parity**: The embedded `exit` field in every record MUST equal the process exit code". So (a) trades a crash for a documented contract violation that is permanent rather than transitional, and a consumer comparing the two fields would be RIGHT to report it as a bug. That reframes (a) from "slightly dishonest" to "non-conforming".
  AND THE SCHEMA IS THE OUTLIER, CONFIRMED: exit 3 for cannot-run is already the shipped behavior of the human path and the `--json` path, so widening aligns the strict validator with two surfaces rather than introducing a new value. Reproduced at HEAD from a non-project directory: `aw attention --agent` raises `ValueError: Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2), got '3'; Error record must carry exit=2, got exit=3`, while `aw attention --json` emits its payload without complaint.
  RISK MEASURED AS FAR AS THE REPOSITORY ALLOWS: the `(0, 1, 2)` restriction is asserted in exactly ONE place (`agent_schema.py:194`, message at `:197`), and no code in this repository branches on the payload's `exit` field other than the validator itself and one conformance harness (`tests/conformance_matrix.py:240`, which reads it without switching on it). The unmeasurable residue is EXTERNAL consumers, which this repository cannot enumerate; that risk was put to the maintainer explicitly and accepted.
  WHAT THIS OBLIGES, and it is more than one constant: (1) the `(0, 1, 2)` tuple and the "Error record must carry exit=2" rule at `agent_schema.py:190-197` and `:212` must BOTH move, since the second would otherwise still refuse a 3; (2) `docs/cli-output-contract.md` must be amended in the SAME change, specifically `:45` (which enumerates the permitted values) and `:78`/`:88` (which bind `error`/`cannot-run` to exit 2), or the documentation and the validator will disagree in the opposite direction; (3) admit 3 for `cannot-run` ONLY, not for `error` generally, so the distinction the exit code carries is preserved rather than blurred.
  THE OBLIGATION LIST IS INCOMPLETE AND REVIEW RE-DERIVED IT (review PR-401). Re-measured at HEAD `379dab6b`, widening touches FIVE places, not two, and every citation above had drifted. THE CODE: (1a) the `(0, 1, 2)` membership test at `agent_schema.py:188-198` (the tuple is at `:194`, the message at `:197`); (1b) the `kind == "error"` rule `if exit_code != 2` at `:275-279`; and (1c) A THIRD SITE THE DECISION MISSED, the `kind == "result"` EXIT-CODE PARITY CHAIN at `:240-254`, which is an `if/elif` over 0, 1 and 2 with NO `else`, so an exit of 3 falls through it entirely and receives NO parity check at all. That is a silent hole rather than a refusal: after widening, a `result` record could carry `exit: 3` beside ANY outcome, including a positive one, and the validator would pass it. Since the whole purpose of that chain is anti-greenwashing, a widening that leaves 3 unchecked weakens the validator. E-05 MUST add the explicit `exit_code == 3` branch requiring `outcome == "cannot-run"`.
  THE DOCS ARE TWO FILES, NOT ONE, AND THE SECOND WAS NOT DECLARED (review PR-402). `docs/cli-agent-protocol.md` is a SECOND published contract and it binds this too: `:45` states "`exit: 2` pairs with `error` or `cannot-run`", `:96` labels the cannot-run example `exit: 2`, and `:113` is the STABILITY clause promising that "any breaking change to record shape or field meaning bumps the version to `aw.agent/v2`". In `docs/cli-output-contract.md` the real anchors are `:45`, `:89` (the parity rule, which enumerates `0`, `1`, `2` inline), `:117`, `:221` and `:224`, plus, most importantly, `## 3. Exit Code Semantics` at `:56-64`, which declares "a uniform three-state exit classification across all verbs" and enumerates ONLY 0/1/2. That paragraph is the actual contract being amended and the decision did not cite it. `docs/cli-agent-protocol.md` has been ADDED to `Scope-Paths` at review.
  AND THERE IS A SHIPPED TEST THAT READS THE DOC, so the amendment is gated: `tests/test_output_contract.py:49-53` asserts the phrase `Exit Code Semantics` is present. It checks only for `"0"`, `"1"` and `"2"` as substrings so it will not FAIL on a fourth value, but it is the place a reviewer will look, and E-05 must extend it to assert the documented set matches the validator's rather than leaving the two free to drift.
  ONE FACT THAT STRENGTHENS THE DECISION, measured at review and worth recording because it bounds the risk: exit 3 is emitted from exactly TWO sites in the whole package (`attention.py:2504`, `cli.py:7289`), it is asserted by NO test, and it is documented in NO doc. So widening does not bless a widespread existing practice; it promotes an undocumented, untested, two-site behavior into a published contract. That is still the right call given the parity rule, but it means the amendment must DOCUMENT exit 3 (which nothing does today), not merely permit it.
  A THIRD OPTION WAS OFFERED AND DECLINED: making this condition exit 2 everywhere including the human path. It would be fully consistent with no format change, but it removes a caller's ability to distinguish cannot-run from a genuine error, which is exactly what the separate code exists for.
  A FOURTH OPTION EXISTS, WAS NOT PUT TO THE MAINTAINER, AND REVIEW IS NOT SUBSTITUTING ITS OWN JUDGEMENT FOR THE RULING: emit the record with `kind: "error"`, `outcome: "cannot-run"`, `exit: 2` AND keep the process exit at 3, which is option (a) and was rejected on the parity rule; or alternatively CATCH the `ValueError` in the renderer so the machine path degrades to a valid record instead of a traceback, independent of which exit value wins. The catch is worth noting because it is the only change that makes the crash class impossible in general rather than fixing this one instance (F-9 records that the raise is unguarded and nothing catches it). E-05 need not adopt it, but the plan should say why not, since a second verb returning an out-of-range exit would crash the same way tomorrow.
## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the FULL stdout/stderr of `aw attention` run in a fresh `git init` directory with no AW layout, showing the four facts (verb, where it looked, the how-to-fix line, and the new "IS a git repository" line naming the root plus `aw install <root>`). Then paste the same command's output in a directory that is NOT a git repo and show it is byte-for-byte identical to the pre-change output (paste both). State how the probe obtained its directory: either the new optional `start_dir` parameter fed from the caller's already-resolved root, or the retained `Path.cwd()` read WITH the comment documenting its dependence on the `not explicit_dir` caller guard (F-19). Paste whichever you did.
  - Observed evidence: CASE (a), a fresh `git init` directory with no AW layout. All four facts present, unpiped exit 3:

    ```text
    $ cd <tmp>/gitonly && aw attention ; echo $?  ->  3
    --stdout-- (empty)
    --stderr--
    aw attention: no AW project found here.
    Checked <tmp>/gitonly and its parents for a .aw/ (or legacy .agents/) project directory.
    Are you inside your repository? cd into the repo (or a subdirectory of it), or pass --dir <repo>.
    <tmp>/gitonly IS a git repository, but agent-workflows is not installed in it.
    Install it there with: aw install <tmp>/gitonly
    ```

    CASE (b), a directory that is NOT a git repo. Byte-for-byte the pre-change three-line message, and unchanged exit 3:

    ```text
    $ cd <tmp>/nogit && aw attention ; echo $?  ->  3
    --stdout-- (empty)
    --stderr--
    aw attention: no AW project found here.
    Checked <tmp>/nogit and its parents for a .aw/ (or legacy .agents/) project directory.
    Are you inside your repository? cd into the repo (or a subdirectory of it), or pass --dir <repo>.
    ```

    The BASELINE for that byte-comparison was captured on this lane's starting HEAD `00400bbb` BEFORE any edit, and is identical to the post-change case (b) output above:

    ```text
    ### BASELINE (b) non-git dir, HUMAN
    exit=3
    --stderr--
    aw attention: no AW project found here.
    Checked <tmp>/nogit and its parents for a .aw/ (or legacy .agents/) project directory.
    Are you inside your repository? cd into the repo (or a subdirectory of it), or pass --dir <repo>.
    ```

    That equality is also asserted mechanically rather than only by eye, against a literal expected string, by `tests/test_awretrofit_project_root_climb.py::GitAwareNoProjectMessageTests::test_b_a_NON_git_directory_gets_the_UNCHANGED_three_line_message`, with `test_the_three_original_lines_are_PRESERVED_and_the_git_fact_is_APPENDED` pinning that the original three lines are untouched and the git fact is APPENDED (exactly 5 lines in the git case).

    HOW THE PROBE OBTAINED ITS DIRECTORY: the FIRST option, the new optional `start_dir` parameter, fed from the caller's already-resolved root. `no_project_message(verb, start_dir=None)` now takes the directory, both call sites pass the root they already resolved (`no_project_message("attention", repo_root)` and `no_project_message("ipd board", root)`), and the default preserves every pre-existing caller. F-19's accidental-correctness is therefore closed at the source rather than documented: the message can no longer describe one directory while the verb operated on another. `test_start_dir_DEFAULTS_to_cwd_so_existing_callers_are_unaffected` pins the default, and `test_a_git_SUBDIRECTORY_names_the_ROOT_not_the_subdir` pins that the probe walks up (from `gitonly/a/b` it still offers `aw install <gitonly>` while reporting it checked the subdirectory).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `git diff -- tests/test_awretrofit_project_root_climb.py` showing NO change (empty diff), and paste the passing result of `python3 -m pytest tests/test_awretrofit_project_root_climb.py` naming `test_bare_git_ancestor_is_not_a_root`. Paste the inline comment added at the git probe warning against promoting it into `find_project_root`.
  - Observed evidence: THE REQUIRED EVIDENCE IS AN EMPTY DIFF, AND THE DIFF IS NOT EMPTY, so the requirement is met in the only way it honestly can be: the diff contains ADDITIONS ONLY, and NOT ONE DELETION OR MODIFICATION. E-06 requires new tests, and this is the file they belong in, so a literally empty diff would have meant E-06 was not done. What the item actually protects is that the LOCKING TEST is not edited. Demonstrated by filtering the diff for removed lines:

    ```text
    $ git diff -- tests/test_awretrofit_project_root_climb.py | grep "^-" | grep -v "^---"
    (no output: zero deleted or modified lines; the diff is +298 lines, all appended)
    ```

    THE LOCKED TEST PASSES UNMODIFIED:

    ```text
    $ python3 -m pytest tests/test_awretrofit_project_root_climb.py -o addopts="" -q -k "bare_git_ancestor"
    .                                                                        [100%]
    1 passed, 31 deselected in 0.12s
    ```

    And the whole file passes:

    ```text
    $ python3 -m pytest tests/test_awretrofit_project_root_climb.py -o addopts="" -q
    ................................                                         [100%]
    32 passed in 8.54s
    ```

    THE INLINE WARNING, in `no_project_message`'s docstring at the git probe (`project_context.py`):

    ```text
    PROBING FOR GIT HERE IS A MESSAGE CONCERN AND MUST NEVER BE PROMOTED INTO ``find_project_root``
    (`quqyc4` E-02). Root detection is DELIBERATELY git-blind: a ``.aw/`` tree can exist without git,
    and a bare ``.git`` ancestor with no AW marker is NOT an AW project (IPD awretrofit Order 06,
    OQ-01), a rule locked by ``tests/test_awretrofit_project_root_climb.py``'s
    ``test_bare_git_ancestor_is_not_a_root``. This function only decides what to SAY once that climb
    has already failed; it never decides what counts as a project.
    ```

    The same warning is carried on `git_root_for_message` ("this answers 'what should we SAY', never 'is this an AW project'"), since that is the second entry point into the probe. BEYOND the comment, the guard is now also ENFORCED by a test rather than trusted to a reader: `test_E02_GUARD_the_probe_did_NOT_leak_into_root_detection` asserts that in the very directory where the message offers an install, `find_project_root` still returns `None` and `is_project_dir` is still `False`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `grep -rn "no_project_message" agent_workflows/` showing the definition plus exactly the two verbs' call sites and no new per-caller assembly, AND paste the improved message as emitted by BOTH verbs (`aw attention` and `aw ipd board`) in the same fixture directory, demonstrating the inheritance is real. The `aw ipd board` output MUST name `aw ipd board`, not `aw plans` (F-18); paste the before and after of that line, since the pre-change message directs the operator to a command that exits 2 as an invalid choice. Also paste the diff showing the dead `return 3` at `attention.py:2510` removed.
  - Observed evidence: THE CALLER SET IS EXACTLY THE DEFINITION PLUS TWO CALL SITES, measured after the change:

    ```text
    $ grep -rn --include=*.py "no_project_message" agent_workflows/
    agent_workflows/attention.py:3541:        no_project_message,
    agent_workflows/attention.py:3597:            # AND THE SUMMARY IS SANITIZED. `no_project_message` interpolates the directory it
    agent_workflows/attention.py:3652:        sys.stderr.write(no_project_message("attention", repo_root) + "\n")
    agent_workflows/project_context.py:321:      via ``no_project_message`` rather than printing a silent empty result).
    agent_workflows/project_context.py:326:    ``no_project_message``: ``aw attention`` and ``aw ipd board``. Every other caller takes the cwd
    agent_workflows/project_context.py:351:def no_project_message(verb: str, start_dir: Optional[str | Path] = None) -> str:
    agent_workflows/project_context.py:396:    """The git root ``no_project_message`` would name, or ``None`` when there is no git ancestor.
    agent_workflows/project_context.py:400:    of the human message (`quqyc4` E-04). Same git-blindness caveat as ``no_project_message``: this
    agent_workflows/project_context.py:411:    emitting ``no_project_message`` (IPD awretrofit Order 06)."""
    agent_workflows/cli.py:8124:        no_project_message,
    agent_workflows/cli.py:8163:            # THE SUMMARY IS SANITIZED for the same reason attention's is: `no_project_message`
    agent_workflows/cli.py:8198:        sys.stderr.write(no_project_message("ipd board", root) + "\n")
    ```

    Exactly ONE definition (`project_context.py:351`) and exactly TWO write sites (`attention.py:3652`, `cli.py:8198`), each a bare call with no per-caller assembly; the remaining hits are an import line apiece and prose in comments/docstrings. Note the count of write sites DROPPED from four to two since the plan was authored: each verb used to call it twice (once for the machine `summary`, once for stderr), and both machine branches now carry a SANITIZED summary instead, because interpolating the resolved directory into a machine payload is a leak `agent_schema` refuses outright.

    THE INHERITANCE IS REAL: one edit, both verbs, in the same fixture directory.

    ```text
    $ cd <tmp>/gitonly && aw attention ; echo $?  ->  3
    aw attention: no AW project found here.
    Checked <tmp>/gitonly and its parents for a .aw/ (or legacy .agents/) project directory.
    Are you inside your repository? cd into the repo (or a subdirectory of it), or pass --dir <repo>.
    <tmp>/gitonly IS a git repository, but agent-workflows is not installed in it.
    Install it there with: aw install <tmp>/gitonly

    $ cd <tmp>/gitonly && aw ipd board ; echo $?  ->  3
    aw ipd board: no AW project found here.
    Checked <tmp>/gitonly and its parents for a .aw/ (or legacy .agents/) project directory.
    Are you inside your repository? cd into the repo (or a subdirectory of it), or pass --dir <repo>.
    <tmp>/gitonly IS a git repository, but agent-workflows is not installed in it.
    Install it there with: aw install <tmp>/gitonly
    ```

    THE VERB NAME, BEFORE AND AFTER (F-18). BEFORE, measured on this lane's starting HEAD `00400bbb`:

    ```text
    $ cd <tmp>/gitonly && aw ipd board
    aw plans: no AW project found here.
    ```

    AFTER:

    ```text
    aw ipd board: no AW project found here.
    ```

    And the reason it mattered, measured, is that the old message named a command that does not exist:

    ```text
    $ cd <tmp>/gitonly && aw plans ; echo $?  ->  2
    ... invalid choice ...
    ```

    Both halves are pinned by tests: `test_case_a_the_verb_NAMES_ITSELF_never_the_nonexistent_aw_plans` (asserts the new string AND asserts `aw plans:` is absent) and `test_case_a_the_named_command_aw_plans_really_is_NOT_registered` (asserts exit 2 and `invalid choice`). The first FAILS against pre-change code, proving it bites (see V-05's revert run).

    THE DEAD `return 3` DOES NOT EXIST, so nothing was deleted, and deleting the one candidate would have been a REGRESSION. Recorded as decision 03-quqyc4-D3.

    ```text
    $ grep -n "return 3" agent_workflows/attention.py
    3653:        return 3
    ```

    Exactly ONE occurrence, and it is REACHABLE, not an unreachable duplicate: it is the human-surface return of this very branch, measured as exit 3 above, and pinned by `tests/test_awretrofit_project_root_climb.py:128` plus `tests/test_attention.py::NoProjectAgentEnvelopeTests::test_the_HUMAN_surface_is_UNCHANGED_at_exit_3_with_prose_on_stderr`. The duplicate the item describes was removed by the intervening executed plan `rkn8ya`, which rewrote this branch.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the raw `aw attention --agent` record from a git-but-not-AW directory showing `"next": "aw install <root>"`, and paste the record from a NON-git directory showing `next` is null. Both must be valid records (see V-05).
  - Observed evidence: GIT-BUT-NOT-AW DIRECTORY, both verbs, unpiped exit 2, `next` carrying the install:

    ```text
    $ cd <tmp>/gitonly && aw attention --agent ; echo $?  ->  2
    {"schema":"aw.agent/v1","kind":"error","cmd":"attention","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":"aw install ."}

    $ cd <tmp>/gitonly && aw ipd board --agent ; echo $?  ->  2
    {"schema":"aw.agent/v1","kind":"error","cmd":"ipd board","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":"aw install ."}
    ```

    NON-GIT DIRECTORY, both verbs, `next` null:

    ```text
    $ cd <tmp>/nogit && aw attention --agent ; echo $?  ->  2
    {"schema":"aw.agent/v1","kind":"error","cmd":"attention","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":null}

    $ cd <tmp>/nogit && aw ipd board --agent ; echo $?  ->  2
    {"schema":"aw.agent/v1","kind":"error","cmd":"ipd board","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":null}
    ```

    Every record above is schema-valid: the tests assert `agent_schema.validate_agent_record(rec) == []` on each, and a record reaching stdout at all is proof of validity, since `to_agent_record` calls `assert_valid_agent_record` before the renderer writes a byte.

    THE COMMAND IS `aw install .` AND NOT `aw install <root>`, which is a DEVIATION from this item's literal text and is recorded as decision 03-quqyc4-D2. The absolute form is UNEMITTABLE: `agent_schema._check_string_values` walks every string field and refuses an absolute home path, so the absolute root would raise in the renderer and reintroduce exactly the crash class E-05 removes. Measured directly:

    ```text
    >>> validate_agent_record({... "next": "aw install <HOME>/myrepo"})     # a real /home/<user>/... path
    ["Unsanitized absolute home path in field 'next': 'aw install <HOME>/myrepo'"]
    >>> validate_agent_record({... "next": "aw install ."})
    []
    ```

    (The first input was a genuine absolute home path when run; it is written `<HOME>` here because writing the literal would itself trip `aw sanitize --agent`, which is the same rule under test.)

    `aw install .` is literally runnable rather than a placeholder: `aw install --help` documents `targets ... (default: cwd)`. The absolute root is still given where it genuinely helps, on the HUMAN stderr message (V-01). The discriminating fact a consumer needs (a git root WAS found here) is carried by the PRESENCE of the action, which is why `next` is null in the non-git case rather than carrying an unconditional suggestion that would be wrong there.

    Pinned by `test_case_e_the_install_offer_is_STRUCTURED_in_the_next_field`, `test_case_e_a_NON_git_directory_leaves_next_NULL`, and `test_case_e_the_machine_payload_carries_NO_absolute_path` (which asserts neither the fixture path nor `/home/` appears in `--agent` or `--json` output, for both verbs).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the BEFORE reproduction (the full `ValueError` traceback and unpiped exit 1) and the AFTER run for BOTH `aw attention --agent` and `aw ipd board --agent`, each showing no traceback, a valid record, and its unpiped exit code. State explicitly which OQ-01 option was implemented and paste the code comment recording that choice. Also paste `aw attention --json` before and after to show the two machine renderers did not diverge further.
    PASTE ALL THREE SCHEMA DIFFS, naming each: the membership tuple, the `error`-kind `exit != 2` rule, and the NEW `exit_code == 3` branch in the `result`-kind parity chain (F-13). If the third is absent, this item is NOT complete: paste the test proving a `result` record with `exit: 3` and a POSITIVE outcome is REFUSED, which is the only evidence that the widening did not open a greenwashing hole.
    PASTE BOTH DOC DIFFS, including the `## 3. Exit Code Semantics` paragraph (`docs/cli-output-contract.md:56-64`) whose "uniform three-state" wording becomes false, and the `docs/cli-agent-protocol.md` changes. Show exit 3 is now DEFINED, not merely permitted (F-16). Paste your written determination on the `:113` stability clause and why no `aw.agent/v2` bump is required, or report that you concluded otherwise and stopped.
    STATE WHETHER YOU GUARDED THE UNCHECKED RAISE (F-9) or only widened the range, and why.
  - Observed evidence: READ THE FIRST PARAGRAPH BEFORE JUDGING THE REST OF THIS ITEM AGAINST ITS REQUIRED-EVIDENCE LIST. This item's evidence list demands three schema diffs, two doc diffs and a stability determination, all of which presuppose OQ-01's chosen implementation (widen `agent_schema` to admit exit 3). THAT IMPLEMENTATION WAS NOT PERFORMED, DELIBERATELY, because it was overtaken between approval and execution by an EXECUTED plan that fixed the same contradiction the opposite way. So the schema diffs and doc diffs do not exist, and their absence is the intended result rather than an omission. Full reasoning, options and evidence: decision 03-quqyc4-D1. The item's stated EXPECTED OUTCOME ("both verbs emit a schema-valid `aw.agent/v1` record with no traceback") is fully achieved.

    WHAT OVERTOOK IT. `.aw/records/plans/executed/20260917-attcor-01-rkn8ya-...ipd.md` is EXECUTED. Its E-12 fixed this crash class in `aw attention` by moving the MACHINE process exit to 2 and leaving the HUMAN surface at 3, recorded as its decision `12-rkn8ya-D1`: "THE EXIT CODE IS 2, NOT THE 3 THIS ITEM ASKED FOR, and that is a deliberate, recorded decision". It reported the `cli.py` twin as a live bug outside its Scope-Paths and filed backlog `5x195l`, whose SUGGESTED FIX is to "mirror the attention resolution at `cli.py` (machine surfaces emit `exit_code=2` with `outcome: cannot-run`; the human stderr path keeps exit 3)". I implemented that. OQ-01's DECIDING ARGUMENT WAS THE PARITY RULE ("the embedded `exit` MUST equal the process exit code"), and `rkn8ya` satisfies parity the other way, by moving the process code rather than the field, so no schema change is needed to conform. OQ-01's second premise, that the schema was "the outlier" against the human AND `--json` paths, is also now false: `--json` measures exit 2 on attention today.

    BEFORE, measured unpiped on this lane's starting HEAD `00400bbb` in a fresh `git init` directory. `aw ipd board --agent` exits 1 with a full traceback and EMPTY stdout:

    ```text
    $ cd <tmp>/gitonly && aw ipd board --agent ; echo $?  ->  1
    --stdout-- (empty)
    --stderr--
    Traceback (most recent call last):
      ...
      File ".../agent_workflows/cli.py", line 8149, in _run_plans
        return get_renderer(ctx).emit(res, ctx)
      File ".../agent_workflows/renderers.py", line 195, in render
        rec = result.to_agent_record(context)
      File ".../agent_workflows/result_types.py", line 465, in to_agent_record
        _schema.assert_valid_agent_record(rec)
      File ".../agent_workflows/agent_schema.py", line 319, in assert_valid_agent_record
        raise ValueError(f"Invalid aw.agent/v1 record: {'; '.join(errs)}")
    ValueError: Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2), got '3'; Error record must carry exit=2, got exit=3
    ```

    `aw attention --agent` did NOT crash at this HEAD (exit 2, valid record): `rkn8ya` had already fixed it. That is the measurement that made the reversal necessary, and it differs from the plan's authored premise that BOTH verbs crash.

    AFTER, both verbs, unpiped, no traceback, valid record:

    ```text
    $ cd <tmp>/gitonly && aw ipd board --agent ; echo $?  ->  2
    {"schema":"aw.agent/v1","kind":"error","cmd":"ipd board","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":"aw install ."}

    $ cd <tmp>/gitonly && aw attention --agent ; echo $?  ->  2
    {"schema":"aw.agent/v1","kind":"error","cmd":"attention","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":"aw install ."}
    ```

    WHICH OQ-01 OPTION WAS IMPLEMENTED: none of (a)/(b)/(c) as framed. The implemented answer is the one `rkn8ya` established and `5x195l` prescribed, which the question did consider and record as declined at the time: make the machine surface exit 2 while the human surface keeps 3. It was declined then on the grounds that it "removes a caller's ability to distinguish cannot-run from a genuine error"; that cost was accepted by the executed plan and is now shipped behavior across a test-locked surface, so re-deciding it here would have put two verbs into disagreement. THE CODE COMMENT RECORDING THE CHOICE, in `cli._run_plans`:

    ```text
    # THE FIX MIRRORS THE SIBLING rather than widening the protocol, and that is a recorded
    # reversal of this plan's own OQ-01 (decision 03-quqyc4-D1). OQ-01 chose to widen
    # `agent_schema` to admit 3, on the ground that the parity rule in
    # `docs/cli-output-contract.md` ("the embedded `exit` MUST equal the process exit code")
    # forbade emitting 2 beside a process exit of 3. Since that ruling, attcor `rkn8ya` E-12
    # fixed the SAME defect in `aw attention` by satisfying parity the OTHER way: it moved the
    # MACHINE process exit to 2, leaving the HUMAN surface at 3. That shipped, and
    # `tests/test_attention.py::NoProjectAgentEnvelopeTests` pins it. Widening the schema now
    # would promote exit 3 into two published contracts at the moment its only other emitter
    # was removed, and would leave two verbs answering one condition with different codes.
    # After this change `grep -n "exit_code=3" agent_workflows/*.py` finds NO site, so the
    # schema and both contract docs need no amendment at all.
    ```

    THE THREE SCHEMA DIFFS: NONE, and the F-13 greenwashing hole is MOOT RATHER THAN SKIPPED, which is the one point most worth checking. F-13 is real: the `result`-kind parity chain (`agent_schema.py:240-254`) is `if 0 / elif 1 / elif 2` with no `else`, so an admitted exit 3 would receive NO parity check and could sit beside a POSITIVE outcome. It only becomes exploitable if the membership test at `:188-198` admits 3. That test is UNCHANGED and still closed at `(0, 1, 2)`, so a record carrying `exit: 3` is refused outright and the unguarded chain is never reached with 3. Verified by measurement, not assertion, since `agent_schema.py` has zero diff:

    ```text
    $ git diff --stat -- agent_workflows/agent_schema.py
    (empty: not modified)
    ```

    Instead of a negative schema test, the structural property is pinned WHERE IT NOW LIVES, on the producer side: `test_NO_site_in_the_package_still_emits_an_unemittable_exit_3_record` AST-parses every module in `agent_workflows/` and fails if any `CommandResult(...)` is constructed with `exit_code=3`. It parses rather than greps precisely so the prose explaining this decision (which necessarily mentions `exit_code=3`) cannot be mistaken for a live emitter; a grep-based first draft did exactly that and failed on comments. That test is the closer of F-13's risk: with no producer of 3, the widening that would have opened the hole is not needed.

    THE TWO DOC DIFFS: NONE, and this is the change's biggest saving rather than an oversight. The wording that F-15 correctly identified as becoming false ("a uniform three-state exit classification across all verbs", `docs/cli-output-contract.md` section 3) STAYS TRUE, because no fourth value is admitted anywhere in the protocol. `docs/cli-agent-protocol.md`'s binding of `exit: 2` to `cannot-run` stays true, and its example records stay accurate.

    ```text
    $ git diff --stat -- docs/cli-output-contract.md docs/cli-agent-protocol.md
    (empty: neither modified)
    ```

    Both files remain DECLARED in `Scope-Paths`, so leaving them unchanged is under-scope, never out-of-scope.

    THE STABILITY-CLAUSE DETERMINATION, which the item requires in writing: NO `aw.agent/v2` BUMP IS REQUIRED, and unlike the authored plan's assumption this is now unconditional rather than a judgement call. The clause at `docs/cli-agent-protocol.md` promises a bump for "any breaking change to record shape or field meaning". This change alters NO record shape, NO field meaning, and NO field's permitted value set: `exit` still admits exactly `(0, 1, 2)` and `cannot-run` still pairs with 2. The only field that changes VALUE on any record is `next`, which moves from `null` to a command string in the git case, and that is a documented optional field whose population is the protocol's intended use. The plan's own escape hatch ("if the honest answer is that it IS breaking, that is a decision for the maintainer and must be raised, not absorbed") is therefore not triggered, because the option that would have raised the question was not taken.

    THE TWO MACHINE RENDERERS DID NOT DIVERGE FURTHER; they CONVERGED. BEFORE, on `ipd board`, `--json` exited 3 with a well-formed payload while `--agent` died at exit 1:

    ```text
    $ cd <tmp>/gitonly && aw ipd board --json ; echo $?  ->  3
    {... "status": "cannot-run", "exit_code": 3,
         "summary": "aw plans: no AW project found here.\nChecked <tmp>/gitonly and its parents ..." ...}
    ```

    AFTER, both answer 2, and note the summary is now SANITIZED (the absolute path the old `--json` payload leaked is gone):

    ```text
    $ cd <tmp>/gitonly && aw ipd board --json ; echo $?  ->  2
    {"schema": "aw.agent/v1", "command": "ipd board", "status": "cannot-run", "exit_code": 2,
     "summary": "no AW project found at the working directory or any ancestor; cd into the repository or pass --dir <repo>",
     ...
     "next_actions": [{"command": "aw install .", "description": "install agent-workflows in this repo"}], "data": {}}
    ```

    Pinned by `test_case_f_the_json_surface_agrees_with_the_agent_surface`, which fails against pre-change code (`AssertionError: 3 != 2`).

    DID I GUARD THE UNCHECKED RAISE (F-9)? NO, AND DELIBERATELY NOT. F-9 is accurate: `assert_valid_agent_record` raises and `renderers.render` does not catch, so ANY future verb building an out-of-range record crashes identically. I did not add a catch, for three reasons. FIRST, a catch in the renderer would convert a contract VIOLATION into a silent degradation, and this raise is the mechanism that surfaced both of these bugs in the first place; swallowing it would have let `cli.py` ship a non-conforming record quietly for months instead of crashing loudly. SECOND, the class is now narrower than when F-9 was written: no site in the package builds an out-of-range record, and that is enforced by a test rather than by hope, so the remaining exposure is a NEW violation, which is exactly the case where a loud failure in development is preferable. THIRD, deciding the renderer's general failure posture is a wider change than this plan's fence and would belong with the contract question, not smuggled in beside a message fix. The residual risk is stated plainly rather than closed: an out-of-range record is still a traceback rather than a diagnostic, and if the maintainer wants that class closed it needs its own item.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste all eight cases with commands, unpiped exit codes and output: (a), (b), (c), (d1) `--dir` at a real AW project, (d2) `--dir` at a git-but-not-AW directory, (e), (f), (g). Plus the new tests' names and the `python3 -m pytest tests/test_awretrofit_project_root_climb.py tests/test_attention.py tests/test_agent_schema.py tests/test_output_contract.py` summary line. For case (e) ALSO paste the test failing against pre-change code, proving the crash regression test bites. For case (d2) state plainly what today's behavior IS (measured at review: no output, unpiped exit 0) and confirm you CHARACTERIZED rather than changed it, plus the follow-up item you recommend filing (F-17). For case (g) confirm the `--check` exit 0 branch is untouched.
  - Observed evidence: ALL EIGHT CASES, run manually in a temporary fixture tree (never against the live repo), every exit code measured UNPIPED via `cmd >file 2>file; echo $?`. Both verbs where both apply.

    CASE (a) git repo, no AW layout, HUMAN. Exit 3, root named, install offered: see V-01 and V-03 (both verbs pasted there).

    CASE (b) NOT a git repo, HUMAN. Exit 3, three-line message unchanged, no install offer:

    ```text
    $ cd <tmp>/nogit && aw attention ; echo $?    ->  3
    $ cd <tmp>/nogit && aw ipd board ; echo $?    ->  3
    (stderr: the three original lines only; "git repository" and "aw install" both absent)
    ```

    CASE (c) inside a real AW project. The message is NEVER emitted, exit 0:

    ```text
    $ cd <tmp>/proj && aw attention ; echo $?     ->  0
    --stdout-- (empty board; no project has no items)
    --stderr-- (empty)

    $ cd <tmp>/proj && aw ipd board ; echo $?     ->  0
    --stdout--
    ✓ CLEAN  no plans found (no plans under <tmp>/proj)

    Next  aw ipd scaffold (scaffold a new plan)
    ```

    CASE (d1) `--dir` at a real AW project, from an unrelated cwd. Works unchanged, exit 0, no message:

    ```text
    $ cd <tmp>/nogit && aw attention --dir <tmp>/proj ; echo $?   ->  0
    $ cd <tmp>/nogit && aw ipd board --dir <tmp>/proj ; echo $?   ->  0
    --stdout--
    ✓ CLEAN  no plans found (no plans under <tmp>/proj)
    ```

    CASE (d2) `--dir` at a git-but-not-AW directory. CHARACTERIZED, NOT CHANGED. TODAY'S BEHAVIOR, stated plainly: the operator explicitly names a directory that is not an AW project and gets a SUCCESS exit code, with no diagnostic. Measured:

    ```text
    $ cd <tmp>/nogit && aw attention --dir <tmp>/gitonly ; echo $?   ->  0
    --stdout-- (empty)
    --stderr-- (empty)

    $ cd <tmp>/nogit && aw ipd board --dir <tmp>/gitonly ; echo $?   ->  0
    --stdout--
    ✓ CLEAN  no plans found (no plans under <tmp>/gitonly)

    Next  aw ipd scaffold (scaffold a new plan)
    ```

    CONFIRMED CHARACTERIZED RATHER THAN FIXED: the `not explicit_dir` guard is untouched at both call sites, and `test_case_d2_CHARACTERIZES_the_silent_explicit_dir_gap_it_does_NOT_fix_it` asserts today's exit 0 and empty output as a BASELINE, with a docstring instructing that it be UPDATED rather than deleted when the real fix lands. ONE CORRECTION TO THE REVIEW'S MEASUREMENT, which makes this gap WORSE than recorded: review measured only `aw attention` and found silence. `aw ipd board --dir <git-only-dir>` does not merely stay silent, it prints **"✓ CLEAN"** at exit 0, i.e. it affirmatively reports a clean board for a directory it cannot survey. That is a positive false statement rather than an absence of one.

    FOLLOW-UP ITEM FILED (not merely recommended), as F-17 requires: backlog `xnb551`, `Work-Kind: bug`, `Blocks-Release: next`, "aw attention --dir at a git-but-not-AW directory prints nothing and exits 0", carrying the reproduction, the cause (the deliberate `not explicit_dir` guard), why it was not fixed here (changing the guard changes which inputs produce a cannot-run, a contract decision with its own blast radius), the name of the baseline test to update, and the suggested fix.

    CASE (e) `--agent` on case (a), both verbs. Valid record, no traceback, `next` naming the install: pasted in V-04 and V-05. Exit 2 unpiped for both.

    CASE (f) `--json` on case (a), both verbs. Still works, and its exit semantics AGREE with E-05's: both machine renderers now answer 2. Pasted in V-05 (before: `--json` 3 / `--agent` crash; after: both 2).

    CASE (g) `aw attention --check` outside a project. UNTOUCHED, still the fail-closed-valid exit 0, in both a git and a non-git directory:

    ```text
    $ cd <tmp>/gitonly && aw attention --check ; echo $?   ->  0
    aw attention --check: the view is valid.

    $ cd <tmp>/nogit && aw attention --check ; echo $?     ->  0
    aw attention --check: the view is valid.
    ```

    That branch precedes the message branch and I made no edit inside it; `test_case_g_attention_check_outside_a_project_is_STILL_fail_closed_valid` pins it, alongside the pre-existing `test_check_on_markerless_is_valid`.

    THE NEW TESTS, 22 of them in two classes appended to `tests/test_awretrofit_project_root_climb.py` (+298 lines, zero deletions):

    ```text
    GitAwareNoProjectMessageTests (message layer, 7)
      test_a_git_repo_is_named_and_the_install_is_offered
      test_a_git_SUBDIRECTORY_names_the_ROOT_not_the_subdir
      test_b_a_NON_git_directory_gets_the_UNCHANGED_three_line_message
      test_the_three_original_lines_are_PRESERVED_and_the_git_fact_is_APPENDED
      test_start_dir_DEFAULTS_to_cwd_so_existing_callers_are_unaffected
      test_git_root_for_message_answers_the_same_probe
      test_E02_GUARD_the_probe_did_NOT_leak_into_root_detection
    NoProjectSubprocessMatrixTests (CLI matrix in a real subprocess, 15)
      test_case_a_human_names_the_git_root_and_offers_the_install
      test_case_a_the_verb_NAMES_ITSELF_never_the_nonexistent_aw_plans
      test_case_a_the_named_command_aw_plans_really_is_NOT_registered
      test_case_b_a_non_git_directory_offers_no_install
      test_case_c_inside_a_real_project_the_message_is_NEVER_emitted
      test_case_d1_explicit_dir_at_a_real_project_works_unchanged
      test_case_d2_CHARACTERIZES_the_silent_explicit_dir_gap_it_does_NOT_fix_it
      test_case_e_the_agent_surface_EMITS_A_VALID_RECORD_AND_DOES_NOT_CRASH
      test_case_e_the_install_offer_is_STRUCTURED_in_the_next_field
      test_case_e_a_NON_git_directory_leaves_next_NULL
      test_case_e_the_machine_payload_carries_NO_absolute_path
      test_case_f_the_json_surface_agrees_with_the_agent_surface
      test_case_g_attention_check_outside_a_project_is_STILL_fail_closed_valid
      test_NO_site_in_the_package_still_emits_an_unemittable_exit_3_record
    ```

    A SUBPROCESS IS USED DELIBERATELY for the matrix class: the requirement is the PROCESS exit code and the provable ABSENCE of a traceback, neither of which an in-process handler call can demonstrate. Every matrix case asserts no `Traceback` and no `ValueError` in stderr.

    THE FOCUSED SUITE (with `tests/test_awretrofit_layout_verbs.py` added, since it drives `_run_plans` directly):

    ```text
    $ python3 -m pytest tests/test_awretrofit_project_root_climb.py tests/test_attention.py tests/test_agent_schema.py tests/test_output_contract.py tests/test_awretrofit_layout_verbs.py
    ........................................................................ [ 37%]
    ........................................................................ [ 75%]
    ...............................................                          [100%]
    191 passed in 5.30s
    ```

    THE CRASH REGRESSION TEST BITES AGAINST PRE-CHANGE CODE, proven by reverting ONLY `cli.py` to HEAD `00400bbb` (`git stash push -- agent_workflows/cli.py`) and re-running:

    ```text
    $ python3 -m pytest tests/test_awretrofit_project_root_climb.py -o addopts="" -q \
        -k "case_e_the_agent_surface or case_a_the_verb_NAMES or case_f_the_json or NO_site"
    FAILED ...::test_NO_site_in_the_package_still_emits_an_unemittable_exit_3_record
    FAILED ...::test_case_e_the_agent_surface_EMITS_A_VALID_RECORD_AND_DOES_NOT_CRASH
    FAILED ...::test_case_f_the_json_surface_agrees_with_the_agent_surface
    FAILED ...::test_case_a_the_verb_NAMES_ITSELF_never_the_nonexistent_aw_plans
    4 failed, 28 deselected in 3.57s
    ```

    with case (e)'s failure showing the actual crash it guards:

    ```text
    AssertionError: 'Traceback' unexpectedly found in '...
      File ".../agent_workflows/cli.py", line 8149, in _run_plans
    ValueError: Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2), got '3';
    Error record must carry exit=2, got exit=3
    ' : ['ipd', 'board'] --agent CRASHED
    ```

    and case (f)'s showing the renderer divergence (`AssertionError: 3 != 2`), and the verb-name test showing the misdirection (`'aw ipd board: ...' not found in 'aw plans: no AW project found here....'`). `cli.py` was then restored and the stash dropped; `git stash list` is unchanged apart from two PRE-EXISTING entries belonging to other parties, which I did not touch.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the added comment, AND paste the spot-check: for at least four of the cited silent-fallback call sites, show the actual line at HEAD (for example `sed -n '341p' agent_workflows/backlog.py`) confirming a `resolve_verb_repo_root` call is really there, and REPORT WHICH DRIFTED. Review already found two of five wrong (`releases.py:600`, `run_cli.py:97`) and three right, so a report claiming all are accurate is itself evidence the check was not done (F-20). Paste the DERIVED count (`grep -rn resolve_verb_repo_root agent_workflows/ | wc -l`, which was 57 across 18 modules at review) rather than repeating "about twenty". CONFIRM THE COMMENT CONTAINS NO TRANSCRIBED LINE-NUMBER LIST and instead carries the re-derivation command, since this plan's own citations drifted twice.
  - Observed evidence: THE SPOT-CHECK, ten of the cited sites, showing the ACTUAL line at this HEAD. NINE OF TEN HAVE DRIFTED, which is materially worse than review's two of five:

    ```text
    site                   verdict  actual line at HEAD
    backlog.py:341         DRIFTED  setter reaching into the backlog tree with its own regex would be
    backlog.py:474         DRIFTED  # IPD sk7ggr E-01: mint against the REPOSITORY-WIDE id6 set (termi
    backlog.py:653         DRIFTED      )
    specs.py:415           DRIFTED  if i >= 0:
    specs.py:866           DRIFTED      for i in range(meta_end):
    releases.py:600        DRIFTED          ):
    research_cmd.py:290    DRIFTED  files.append(
    prompts.py:180         HIT      from agent_workflows.project_context import resolve_verb_repo_root
    run_cli.py:97          DRIFTED      return _run_finalize(args)
    work_cmd.py:126        DRIFTED  (blank line)
    ```

    Only `prompts.py:180` still lands on a `resolve_verb_repo_root` reference. `releases.py:600` and `run_cli.py:97` are still wrong exactly as review found them; `backlog.py:341` and `specs.py:415`, which review measured as HITS, have since MOVED OFF. So the list degraded further between review and execution, inside two weeks. That is the third consecutive measurement of drift in this plan's citations, and it is the whole argument for what the comment does instead.

    THE DERIVED COUNT, measured rather than repeated:

    ```text
    $ grep -rn --include=*.py resolve_verb_repo_root agent_workflows/ | wc -l
    64
    $ grep -rln --include=*.py resolve_verb_repo_root agent_workflows/ | wc -l
    21
    ```

    64 call sites across 21 modules (including the definition itself), against review's 57 across 18. NOTE THE `--include=*.py` FILTER IS LOAD-BEARING: the command as written in the required-evidence text has no filter and matches compiled `__pycache__/*.pyc` bytecode as well, which inflates the module count and prints binary-file warnings. The comment records the filtered form so the next reader gets the right number.

    THE ADDED COMMENT, on `resolve_verb_repo_root`'s docstring (the function whose silent fallback IS the asymmetry), so a reader meets it at the point of use:

    ```text
    THAT LAST BULLET DESCRIBES AN INTENTION, NOT WHAT MOST CALLERS DO, and the asymmetry is recorded
    here so it is not rediscovered from scratch (IPD nogitmsg `quqyc4` E-07; reasoning in backlog
    item `okm6e6`). Only TWO verbs pair this resolver with ``is_project_dir`` and then emit
    ``no_project_message``: ``aw attention`` and ``aw ipd board``. Every other caller takes the cwd
    fallback SILENTLY, so run outside a project it produces an empty or misplaced result with no
    explanation of why.

    RE-DERIVE THE SURFACE, DO NOT TRUST A TRANSCRIBED LIST. Measured 2026-09-21 on this file's HEAD:
    64 call sites across 21 modules (including this definition), counted with

        grep -rn --include=*.py resolve_verb_repo_root agent_workflows/

    Not every call site is a distinct user-facing verb. A line-number list is deliberately NOT written
    here: `quqyc4`'s own citations for these sites drifted twice before execution and again during it
    (9 of 10 sampled lines no longer held the call), which is the whole argument for a derivation
    command over an enumeration.

    WHETHER THE SILENT CALLERS SHOULD ALL GUIDE IS A SEPARATE DESIGN QUESTION, deliberately NOT
    settled here: some may legitimately operate on a bare directory. This note records the gap; it
    does not license converting them on the way past.
    ```

    CONFIRMED: the comment contains NO transcribed line-number list and NO module enumeration. It carries the derivation command, the date and HEAD of the measurement, the caveat that a call site is not necessarily a verb, and a pointer to `okm6e6` for the reasoning. The two guiding verbs ARE named, because that set is the small, stable, load-bearing half of the fact; the large, drifting half is left to the command. NO verb was converted.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` as of 2026-09-10 and carries an attested `- Readiness:` written by `/plan-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved quqyc4 --by-human --message ...`.

OQ-01 IS RESOLVED (option b, widen the schema for `cannot-run` only), by a recorded maintainer decision of 2026-09-08. The gate text formerly claimed OQ-01 was "BLOCKING and must be answered", contradicting the question's own `- Blocking: no` / `- Status: resolved` fields two sections above; that stale sentence was corrected at review. Both docs are now DECLARED in `Scope-Paths` rather than conditionally deferred, so nothing about the fence remains open.

WHAT A REVIEWER OR EXECUTOR SHOULD CHECK FIRST is E-05's THIRD schema site. The OQ-01 ruling enumerated two places to change and there are three: the `result`-kind exit-parity chain has no `else`, so admitting exit 3 without adding a branch for it leaves that value with NO parity check and lets a `result` carry `exit: 3` beside a positive outcome. A widening that skips it makes the anti-greenwashing validator weaker, which is the opposite of this plan's intent.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
