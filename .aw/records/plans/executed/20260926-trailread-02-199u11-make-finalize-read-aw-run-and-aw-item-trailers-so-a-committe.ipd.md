# IPD: Make finalize read AW-Run and AW-Item trailers so a committed out-of-scope path this plan made always needs a reason

- Date: 2026-09-26
- Kind: child
- Concern: FINALIZE CANNOT TELL WHETHER A COMMITTED OUT-OF-SCOPE PATH BELONGS TO THIS EXECUTION, SO `h9cn0y`'S ACCEPTED COST WAIVES THE REASON REQUIREMENT FOR THE EXECUTOR'S OWN WORK. `ipd_lifecycle._working_tree_path_is_owned`'s docstring states the cost: "an executor's own COMMITTED out-of-scope path escapes the reason requirement when it rides in a commit containing no declared path", and names trailers as "the exact fix". `ipd_lifecycle._execution_cohesive_committed_paths` says trailers "would settle it exactly, but essentially no commit in history carries one yet". Nothing in the package reads a trailer back: `run_evidence.RUN_FINDING_CODES` records `RUN-COMMIT-CONTENTS`/`RUN-COMMIT-GATEWAY` `UNBOUND_BY_DEPENDENCY` "waiting on a trailer READ-BACK predicate". Reproduced at HEAD `61ef21d8` on a scratch repo: after `begin` on a plan declaring `agent_workflows/demo.py, tests/test_demo.py`, one in-scope commit plus one commit touching only `other.py` whose message carries `AW-Item: abc123` (the plan's own id6) gives `finalize_precheck` -> `attribution_source: commit-cohesion`, `out_of_scope_paths: []`, `disregarded_unowned_paths: ['other.py']`, i.e. the plan's own trailered commit is excused. Order 1 (`a6xbso`) makes the agent's `aw commit` calls carry these trailers, so the corpus this reader needs is about to exist.
- Scope: IN: (a) `ipd_lifecycle._commit_run_ownership(repo_root, sha, plan_id6) -> "owned" | "foreign" | "unknown"`, reading `AW-Item`/`AW-Run` via `git log -1 --format=%(trailers:key=...,valueonly)`; (b) a range helper `_trailer_owned_committed_paths(repo_root, base_head, plan_id6)` returning the paths of every non-merge commit in `base_head..HEAD` classified `owned`, plus per-class commit counts for evidence, using ONE `git log` call; (c) in `finalize_precheck`'s committed-half branch, a path in the trailer-owned set is ALWAYS owned (reason required), consulted BEFORE and independently of cohesion or the run record; `unknown` and `foreign` commits fall through to today's predicate unchanged; (d) a `trailer_attribution` evidence block; (e) updating the accepted-cost prose in `_working_tree_path_is_owned`, `_execution_cohesive_committed_paths`, `_run_record_committed_paths` and the `finalize_precheck` comment; (f) behavioral tests on scratch repos. OUT: binding `RUN-COMMIT-CONTENTS`/`RUN-COMMIT-GATEWAY` (Carrier-Declined); using a `foreign` trailer to EXCUSE a path (deferred, see OQ-02); any change to `check_engine.check_scope_drift`, which deliberately reads the unfiltered window.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_finalize_trailer_attribution.py
- Item-Dependencies: executed:a6xbso
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: am1g38
- Set: trailread
- Order: 2
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 199u11

## Workflow history
- 2026-09-27 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 199u11 verified (set trailread, attempt 1).
- 2026-09-27 approved (aw set): status set to approved

- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; 8 findings PR-1301..PR-1308 all FIXED (3 HIGH), 4 decisions D-1..D-4 recorded; review record written. F-1 RE-REPRODUCED at review HEAD f94dc07f on three scratch repos (trailered-own, untrailered and foreign all yield commit-cohesion / out_of_scope=[] / disregarded=['other.py'], i.e. indistinguishable today). PR-1301 (HIGH): E-03's line-oriented one-call parse is unsound because a folded trailer value puts a newline INSIDE the field (measured), so a continuation line is indistinguishable from a path; replaced with a record-delimited \x1e/\x1f parse, verified. PR-1302 (HIGH): a trailers field is multi-valued AND multi-line (two AW-Item trailers -> 'aaa111,zzz999'), so E-02 must split on both axes before comparing. PR-1303 (HIGH): the runner auto-answers every demand this plan adds via compute_scope_reconciliation, so the gate's 'always needs a reason' does not describe the automated path; added E-07/V-07 (comment-only) and a gate paragraph. PR-1304: V-05's grep exits 1 on the UNMODIFIED file (the phrase wraps), so it would pass an unperformed E-05; replaced with three anchors each measured exiting 0 today. PR-1305: case (6) can pass having written no trailer. Also corrected the spec-sync claim (the spec has no 'nothing reads trailers back' sentence) and verified no shipped test is forced into scope. aw ipd lint --phase review-finalize conforming.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog am1g38 on the maintainer's batch-graduation instruction; ordered after a6xbso (Order 1) so the reader has a corpus. The accepted cost was reproduced at HEAD 61ef21d8 on a scratch repo (a commit trailered with the plan's own AW-Item is disregarded as unowned).
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make finalize demand a `--scope-reason` for every committed out-of-scope path whose commit is trailered as this plan's own, removing `h9cn0y`'s accepted false-excuse cost for trailered commits, while an untrailered commit is judged exactly as today and is never inferred to be foreign.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [x] E-01 RE-MEASURE THE EXCUSE at the executing HEAD. Build a scratch repo exactly as the `tests/test_ipd_lifecycle_cli.py` `AdditiveScopeWideningTests.setUp` fixture does (`support.ready_plan_text(plan_id="abc123", ...)` marked performed/pass, `.gitignore` with `.aw/state/`, `agent_workflows/demo.py`, `tests/test_demo.py`, committed), run `ipd_lifecycle.begin`, commit an in-scope edit to `agent_workflows/demo.py`, then commit a new `other.py` alone with message `oos\n\nAW-Run: run-20260926T000000Z-1\nAW-Item: abc123`. Paste `finalize_precheck`'s `attribution_source`, `scope_audit.out_of_scope_paths` and `scope_audit.disregarded_unowned_paths`. Do this with `AW_EXECUTION_ROLE` unset. If `other.py` is already in `out_of_scope_paths`, STOP and report that trailers are already read.
  - Depends on: none
  - Expected outcome: `commit-cohesion`, `[]`, `['other.py']`.
  - Execution state: performed

### Task group 2: the reader

- [x] E-02 ADD `ipd_lifecycle._commit_run_ownership(repo_root, sha, plan_id6)` returning `"owned"`, `"foreign"`, or `"unknown"`. Read the values with `_git(repo_root, ["log", "-1", "--format=%(trailers:key=AW-Item,valueonly,separator=%x2C)%x00%(trailers:key=AW-Run,valueonly,separator=%x2C)", sha])`, using the key names `git_commit_helper.TRAILER_KEY_ITEM`/`TRAILER_KEY_RUN` (imported lazily) rather than re-spelling them. Rules: no `AW-Item` value -> `unknown` (whatever `AW-Run` says, because an ownership claim without an item cannot name this plan); any `AW-Item` value equal to `plan_id6` -> `owned`; `AW-Item` present but none equal -> `foreign`; a git failure -> `unknown`. `AW-Run` is parsed and returned in evidence only: finalize is never handed a run id (the `_execution_cohesive_committed_paths` docstring: the run record is "never handed a run id by finalize"), so the ITEM is the key that names this execution; state that in the docstring. The docstring must also state the fail-closed rule verbatim in substance: `unknown` is NEVER treated as `foreign`, because the corpus permanently contains untrailered commits (backlog `j2srcc`, `wao266` OQ-03), and a trailer is a consistency record, not tamper-proof provenance (same honest limit `_run_record_committed_paths` states).
  - A TRAILER VALUE IS MULTI-LINE AND MULTI-VALUED, SO SPLIT ON BOTH AXES BEFORE COMPARING (review PR-1302, F-5). Verified with git 2.43.0 at review on a scratch repo: `separator=%x2C` joins SEVERAL `AW-Item` trailers into one comma-separated field (two `AW-Item` trailers yield `aaa111,zzz999`), and git's own trailer grammar lets a value CONTINUE on a following whitespace-indented line, so the field itself may contain a newline (measured: a folded continuation line came back inside the `AW-Item` value). So the parse is: take the field, split on `,`, then split each part on any newline, then `.strip()` each token and drop the empties. `owned` iff any surviving token equals `plan_id6` exactly. Comparing the raw field against `plan_id6` would miss the legitimate multi-value case and could be fooled by a folded line; do not do it.
  - Depends on: E-01
  - Expected outcome: on a scratch repo, a commit trailered `AW-Item: abc123` -> `owned` for `abc123` and `foreign` for `zzz999`; an untrailered commit -> `unknown` for both; a commit carrying BOTH `AW-Item: aaa111` and `AW-Item: zzz999` -> `owned` for each of those two and `foreign` for `abc123`.
  - Execution state: performed

- [x] E-03 ADD `ipd_lifecycle._trailer_owned_committed_paths(repo_root, base_head, plan_id6)` returning a small NamedTuple `(paths: frozenset, owned: int, foreign: int, unknown: int)`. Use ONE call and classify each commit by the SAME rule as E-02 (factor the classification of an already-read `AW-Item` value into one private function both call, so they cannot drift). `paths` is the union of paths of `owned` commits. Empty `plan_id6`, no range, or a git failure returns an empty result with zero counts (no demand added, today's behavior).
  - THE ONE-CALL GROUPING MUST NOT BE LINE-ORIENTED, AND THE AUTHORED SENTINEL DOES NOT FIX IT (review PR-1301, F-4). The authored form `--format=<sentinel>%H%x00<AW-Item field> --name-only` assumes one header line per commit, and the trailer field breaks that assumption for the same reason E-02 must split on newlines: a folded continuation line puts a NEWLINE inside the field, so the next line of output is neither a header nor a path. MEASURED at review with git 2.43.0: the trailered commit's output was `<sentinel><sha>\x00abc123\n  AWHDR1111...\n\ng\n`, i.e. the continuation line was indistinguishable from a path line, and a line-oriented reader attributes a nonexistent path to that commit. That is the FAIL-OPEN direction for the header case (a header misread as a path desynchronizes the grouping and can silently attribute a later commit's paths to an `owned` one). USE A RECORD-DELIMITED PARSE INSTEAD, which was verified at review: `git log --no-merges --format=%x1e%H%x00%(trailers:key=AW-Item,valueonly,separator=%x2C)%x1f --name-only base_head..HEAD`, then split the whole stdout on `\x1e` for records, and inside each record split once on `\x1f` to separate the header fields from the `--name-only` block; split the header on `\x00` for sha and item field, and split the block on newlines for paths. `\x1e`/`\x1f` cannot occur in a git path or in a trailer value, so the framing is exact rather than heuristic. If you prefer another framing, it MUST be record-delimited and you MUST paste the measurement in V-03 showing a folded trailer value parsed correctly.
  - Depends on: E-02
  - Expected outcome: on the E-01 repo, `paths == {"other.py"}` and `owned == 1`, `unknown == 1` (the in-scope commit); on a repo with an additional commit whose `AW-Item` value carries a folded continuation line, the continuation text does NOT appear in `paths`.
  - Execution state: performed

### Task group 3: consult it

- [x] E-04 CONSULT THE READER IN `finalize_precheck`'s committed-half branch. Compute `trailered = _trailer_owned_committed_paths(repo_root, base_head, plan_id)` once, beside the existing `exact`/`cohesive` computation. In the loop, inside `if p in committed_set:`, set `owned = True` when `p in trailered.paths`, BEFORE the existing cohesion/`anchored` expression, which is otherwise untouched; the working-tree branch is untouched. This only ever ADDS demands, never removes one, so every path owned today is still owned. Record `evidence["trailer_attribution"] = {"owned_commits": ..., "foreign_commits": ..., "unknown_commits": ..., "owned_paths": sorted(...)}`, and leave `attribution_source` unchanged in meaning (it still names the source that decided the non-trailered remainder). Update the block comment "ACCEPTED COST (the honest bound ...)" in `finalize_precheck` to say the cost now applies ONLY to untrailered commits.
  - Depends on: E-03
  - Expected outcome: on the E-01 repo, `out_of_scope_paths == ['other.py']`, `disregarded_unowned_paths == []`, and `trailer_attribution.owned_paths == ['other.py']`.
  - Execution state: performed

- [x] E-07 RECORD WHERE THE NEW DEMAND ACTUALLY LANDS UNDER THE RUNNER, IN THE `finalize_precheck` COMMENT BLOCK ONLY (review PR-1303, F-6; no behavior change, and deliberately so). The demand this plan adds is felt by a HUMAN finalizing by hand, and is AUTO-ANSWERED under a driver: `runner_shared.compute_scope_reconciliation` maps every path in `out_of_scope_paths` to the fixed string `"changed by the plan's approved execution (auto-reconciled by <host>)"` and hands it to finalize, so under `aw oc run` / `aw agy run` a newly-demanded path is satisfied without stopping the run. Add two or three sentences to the existing comment block stating (a) that the runner auto-reasons these, (b) that this is CORRECT rather than a hole, because a trailer-owned path IS this execution's own work and the auto-reason asserts exactly that (unlike the cohesion case, whose auto-reason can assert a co-worker's path and is the thing `gys47u`'s `attribution_source` note warns about), and (c) that the user-visible effect of this plan under a runner is therefore a TRUER PERMANENT RECORD (the path is recorded as reconciled rather than silently disregarded), not a new stop. Do NOT add a refusal, a warning, or any branch keyed on `trailer_attribution`: that would be a behavior change nobody approved and would strand runs.
  - WHY THIS IS AN ITEM AND NOT A FOOTNOTE: without it, the plan's own gate reads as though executors will now be asked for reasons they were not asked for before, which is false for the automated path that produces nearly all finalizes here, and a later maintainer measuring "did the demand fire?" through a runner log would conclude the reader is inert.
  - Depends on: E-04
  - Expected outcome: the comment block names `compute_scope_reconciliation` and states the auto-reason consequence; `rg -n "compute_scope_reconciliation" agent_workflows/ipd_lifecycle.py` returns at least one hit; no new conditional branch is introduced (the diff adds comment lines only).
  - Execution state: performed

- [x] E-05 UPDATE THE ACCEPTED-COST PROSE so no docstring still says trailers are unread: `_working_tree_path_is_owned` (the second accepted-cost bullet and the closing "The exact fix that would remove the second cost is commit trailers" sentence: now removed for trailered commits, remains for untrailered ones and for raw `git commit`, which is not refused per `a6xbso` OQ-02); `_execution_cohesive_committed_paths` (the "COMMIT TRAILERS ... essentially no commit in history carries one yet" bullet: now read, as a demand-only source ahead of cohesion); and `_run_record_committed_paths` (the "when those land they become a third and better source" sentence: they have landed, as an additive demand source rather than a replacement, and why: a trailer can only ADD a demand, so it composes with the run record instead of deciding alone). Do NOT rename `_working_tree_path_is_owned` (its docstring explains why).
  - THE AUTHORED GREP CANNOT SUCCEED OR FAIL HONESTLY, BECAUSE ONE PHRASE IS LINE-WRAPPED (review PR-1304, F-7). Measured at review: `rg -n "essentially no commit in history carries one yet" agent_workflows/ipd_lifecycle.py` exits 1 TODAY, on the unmodified file, because the sentence wraps mid-phrase ("... but essentially no commit in\n      history carries one yet ..."), and `rg` is line-oriented. So the authored expected outcome is already satisfied before any edit, which makes it a vacuous check that would pass a completely unperformed E-05. Use per-phrase anchors that each actually match today, verified at review to exit 0 on the unmodified file: `rg -n "essentially no commit in" agent_workflows/ipd_lifecycle.py` (line 2141), `rg -n "when those land" agent_workflows/ipd_lifecycle.py` (line 2052), and `rg -n "exact fix that would remove" agent_workflows/ipd_lifecycle.py` (line 2333). V-05 must paste each exiting 0 BEFORE the edit and exiting 1 after, which is what distinguishes a performed edit from an unperformed one.
  - Depends on: E-04
  - Expected outcome: each of the three anchors above exits 0 before the edit and 1 after.
  - Execution state: performed

### Task group 4: prove it

- [x] E-06 ADD `tests/test_finalize_trailer_attribution.py`, behavioral only (no source-text or structure assertions, maintainer ruling 2026-09-26), using `support.declare_execution_role(self)` in `setUp` so the coordinator role is declared rather than inherited, and the E-01 fixture shape. Cases: (1) OWN TRAILER DEMANDS: the E-01 shape -> `other.py` in `out_of_scope_paths`, not in `disregarded_unowned_paths`; and `finalize(..., apply=True)` WITHOUT a reason for `other.py` refuses, WITH `scope_reasons={"other.py": "..."}` succeeds. (2) UNTRAILERED FALLS BACK: identical but the `other.py` commit has no trailer -> `other.py` in `disregarded_unowned_paths`, exactly today's result (pins that `unknown` is not promoted either way). (3) FOREIGN FALLS BACK: `AW-Item: zzz999` -> same as (2), and `trailer_attribution.foreign_commits == 1`. (4) NO FALSE UNKNOWN->FOREIGN: a plan whose ONLY commit is an untrailered out-of-scope commit (the `p7dqwz` shape `_execution_cohesive_committed_paths` cites) still has that path in `out_of_scope_paths` (the `anchored=False` fail-closed path is unaffected). (5) `_commit_run_ownership` on three real commits returns `owned`/`foreign`/`unknown` as specified, including a commit with `AW-Run` but no `AW-Item` -> `unknown`. (6) END TO END WITH ORDER 1: the owned commit is produced by `python3 -m agent_workflows commit --no-plan -m oos -- other.py` run as a subprocess with `AW_RUN_ID`/`AW_ITEM_ID6=abc123` in its env (the writer `a6xbso` ships), proving the writer and reader agree on the format.
  - CASE (6)'S `AW_RUN_ID` MUST MATCH THE PATTERN ORDER 1'S READER VALIDATES AGAINST, OR NO TRAILER IS WRITTEN AND THE CASE PASSES VACUOUSLY (review PR-1305, F-8). `a6xbso` E-03 drops a malformed `AW_RUN_ID` with a warning, and its own review (PR-1203) measured that the test-shaped `run-test` FAILS that pattern. `AW_ITEM_ID6` is validated independently against `artifact_core.ID6_RE`, so `abc123` is fine, and a dropped run id alone would still leave `AW-Item` and case (6) would still exercise the reader. Do NOT rely on that: use a pattern-valid run id (the `runner_shared.new_run_id` shape, e.g. `run-20260926T000000Z-1`) so BOTH trailers land, and assert BOTH are present on the produced commit (`git log -1 --format=...` on each key) BEFORE asserting the precheck result. A case (6) that silently wrote no trailer at all would report the same `out_of_scope_paths` as case (2) and read as a reader failure when the writer never fired.
  - IF ORDER 1 HAS NOT EXECUTED, CASE (6) IS THE STOP, NOT A SKIP. `- Item-Dependencies: executed:a6xbso` already gates dispatch, but a hand-run executor can bypass it. If `aw commit` produces no trailers with the env set, STOP and report that Order 1's channel is absent rather than deleting case (6) or hand-writing the trailer to make the file pass; hand-writing it converts the only end-to-end proof in this plan into a second copy of case (1).
  - Depends on: E-04, E-05
  - Expected outcome: all pass; (1), (3)'s counter, (5) and (6) FAIL before the change (no reader), while (2) and (4) pass before and after; case (6) first asserts both trailers are present on the commit it produced.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `CommittedAttribution` exists so an empty set is never read as "nothing is owned"; the fail-closed switch is `anchored`. This plan's reader adds demands only, so it needs no such switch and cannot invert the gate.
- `_run_record_committed_paths` "decides alone rather than being unioned with cohesion" (`gys47u` OQ-01) because a union would re-admit foreign paths. That argument is about EXCUSING; a trailer here only adds DEMANDS, so composing it additively does not re-admit anything.
- The accepted cost and "trailers are the fix" are stated in three docstrings and one block comment in `ipd_lifecycle`; all must move together (E-05).
- `check_engine.check_scope_drift` reads the unfiltered union deliberately (`_paths_changed_by_this_execution` docstring) and is not touched.
- Trailer keys are single-sourced in `git_commit_helper` (`TRAILER_KEY_RUN`, `TRAILER_KEY_ITEM`).
- A trailer VALUE is not a scalar: git joins repeated keys under `separator=`, and its grammar folds a value across whitespace-indented continuation lines. Both shapes were measured at review with git 2.43.0 and both are why E-02 splits and E-03 uses a record-delimited parse rather than a line-oriented one.
- The runner ALREADY auto-answers every `out_of_scope_paths` demand (`runner_shared.compute_scope_reconciliation`), so adding a demand changes the permanent RECORD rather than stopping a run. Do not design a stop into a demand-only change.
- Test role: `support.declare_execution_role(self)` (conftest scrubs `AW_EXECUTION_ROLE`, but `tests/test_ipd_lifecycle_cli.py` is known to inherit, backlog `owi0no`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1 through F-4 were measured at HEAD `61ef21d8` on 2026-09-26 and RE-VERIFIED at review HEAD `f94dc07f` on 2026-09-27. F-5 through F-8 were added at review.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_lifecycle.finalize_precheck` | A commit trailered with the plan's own `AW-Item` is excused when it touches no declared path. | scratch repo: `0 commit-cohesion [] ['other.py']` (rc, attribution_source, out_of_scope_paths, disregarded_unowned_paths). RE-REPRODUCED at review on three scratch repos: the trailered-own, untrailered and `zzz999`-foreign variants ALL yield `commit-cohesion`, `out_of_scope=[]`, `disregarded=['other.py']`, i.e. the three cases are currently INDISTINGUISHABLE, which is exactly the gap. |
| F-2 | MEDIUM | package | No code reads a trailer back. | `rg -n "trailers:key\|interpret-trailers" agent_workflows` finds only four comment/docstring lines in `git_commit_helper`; `run_evidence` `RUN-COMMIT-CONTENTS` `waiting_on` "a trailer READ-BACK predicate". RE-VERIFIED at review: the same four `git_commit_helper` lines and nothing else. |
| F-3 | INFO | finalize inputs | Finalize has the plan id (receipt `plan_id`) but no run id, so the item trailer is the usable key. | `begin` receipt keys: `plan_id`, `base_head`, `scope_paths`, ... (no `run_id`); `_execution_cohesive_committed_paths`: run record "never handed a run id by finalize". RE-VERIFIED at review by reading the receipt literal in `ipd_lifecycle.begin`: no `run_id` key. |
| F-4 | INFO | corpus | Today only one agent code commit is trailered, so this reader is inert until Order 1 lands. | `a6xbso` F-1. NOTE `a6xbso`'s own review corrected these counts to a re-derived PROPERTY; the property, not a count, is what this row asserts. |
| F-5 | HIGH | E-02 as authored | A `%(trailers:key=...,valueonly)` FIELD IS NEITHER SINGLE-VALUED NOR SINGLE-LINE, so comparing it whole to `plan_id6` is wrong. | git 2.43.0, review scratch repo: two `AW-Item` trailers with `separator=%x2C` yield one field `aaa111,zzz999`; a whitespace-indented continuation line comes back INSIDE the value (`abc123\n  AWHDR1111...`). Fixed in E-02's split rule. |
| F-6 | HIGH | E-04 as authored versus `runner_shared.compute_scope_reconciliation` | UNDER A DRIVER, EVERY DEMAND THIS PLAN ADDS IS AUTO-ANSWERED, so the plan's stated user-visible effect ("always needs a reason") does not describe the automated path. | `compute_scope_reconciliation` maps each `out_of_scope_paths` entry to `"changed by the plan's approved execution (auto-reconciled by <host>)"` and hands it to finalize. Correct, but unstated; now E-07. |
| F-7 | MEDIUM | E-05 / V-05 as authored | THE VALIDATION GREP EXITS 1 ON THE UNMODIFIED FILE, so it would pass an entirely unperformed E-05. | `rg -n "essentially no commit in history carries one yet" agent_workflows/ipd_lifecycle.py` -> exit 1 today, because the sentence wraps after "no commit in". Replaced with three per-phrase anchors each measured exiting 0 today (lines 2141, 2052, 2333). |
| F-8 | MEDIUM | E-06 case (6) | CASE (6) CAN PASS HAVING WRITTEN NO TRAILER AT ALL, because Order 1's reader drops a malformed `AW_RUN_ID`. | `a6xbso` E-03 validates the run id against the `new_run_id` shape and its review PR-1203 measured `run-test` failing it. Case (6) now requires a pattern-valid id and a trailer read-back assertion first. |

## Proposed changes (ordered, validatable)

1. E-01 reproduces the excuse.
2. E-02 adds the per-commit classifier, splitting the trailer field on both `,` and newlines (F-5).
3. E-03 adds the one-call range helper with a record-delimited (`\x1e`/`\x1f`) parse (F-4/PR-1301).
4. E-04 consults it in the committed half, demand-only.
5. E-05 updates the accepted-cost prose, validated by three per-phrase anchors (F-7).
6. E-06 proves it, including an end-to-end run through Order 1's writer with a trailer read-back first (F-8).
7. E-07 records where the demand actually lands under a runner (F-6), comment-only.

## Deferred / out of scope (with reason)

- Binding `RUN-COMMIT-CONTENTS` / `RUN-COMMIT-GATEWAY` in `run_evidence` and spec `25kzda` 4.2.
  - Carrier-Declined: binding them needs a tree-diff proof that a commit's paths equal the item-owned delta (spec `25kzda` 4.6), not just a reader; `run_evidence`'s own tally warns that binding on a writer or reader alone is the fail-open error. No carrier is filed because no plan is designing that proof.
- Using a `foreign` trailer to EXCUSE a committed path that cohesion would otherwise attribute.
  - Carrier-Declined: it would reduce false DEMANDS only (the fail-closed, merely annoying direction), and trusting a locally writable trailer to remove a demand is a weaker bet than trusting it to add one. See OQ-02.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/git_commit_helper.py` is READ (key constants) and not modified.
- Scope-Paths justification: `ipd_lifecycle.py` holds the reader, the precheck, and E-07's comment; the new test file holds E-06.
- `agent_workflows/runner_shared.py` is READ at review and deliberately NOT declared (F-6): E-07 records the auto-reconciliation consequence in `ipd_lifecycle`'s own comment and changes no runner behavior. Declaring it would invite an executor to add a runner-side branch, which is out of scope and unapproved.
- CHECKED AT REVIEW AND CONFIRMED CLEAN: no test in the suite asserts on `attribution_source`, `disregarded_unowned_paths` membership beyond the one widening assertion in `tests/test_ipd_lifecycle_cli.py`, or on any symbol E-02/E-03 adds (`grep -rln "attribution_source" tests/` -> nothing; `grep -n "disregarded_unowned_paths" tests/test_ipd_lifecycle_cli.py` -> one line, asserting `tests/test_extra.py` IS disregarded in the UNTRAILERED widening fixture, which this change cannot affect because that fixture writes no trailer). So no undeclared test file is forced into scope, unlike Order 1's PR-1201 case.

## Required tests / validation

- `tests/test_finalize_trailer_attribution.py` (new), cases (1)-(6); (1), (5), (6) shown FAILING before the change.
- `tests/test_ipd_lifecycle_cli.py` stays green (its `p7dqwz` counterexample and widening tests). Its `AdditiveScopeWideningTests` assertion that `tests/test_extra.py` is in `disregarded_unowned_paths` is the one shipped pin in the blast radius and was verified at review to be UNAFFECTED (its `_commit_all` writes an untrailered message, so the path classifies `unknown` and falls through unchanged).
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A for specs: spec `25kzda` 4.6 already specifies trailer-based ownership; this plan implements a demand-only subset of it and binds no 4.2 code. No `.spec.md` is in `- Scope-Paths:`.
- THE CROSS-SET CLAIM ABOUT `spec25kfix` WAS CHECKED AT REVIEW AND IS CORRECTED HERE. The spec does NOT today contain a sentence reading "nothing reads trailers back" (`rg -n "nothing reads|read.back" <spec>` -> no match); what it contains is the `NOTHING PASSES THEM` clause about the WRITER, which is a different claim. Plan `olkeju` (Set `spec25kfix`, from backlog `j0ag0u`) owns rewriting that clause and its E-01 ALREADY instructs its executor to check whether `199u11` has executed and, if so, to word the reader half accordingly. So the ordering is handled on `olkeju`'s side and this plan needs no spec edit and declares none. If `olkeju` executes AFTER this plan, nothing is stale; if BEFORE, its own E-01 re-measures. Do NOT edit the spec from here.
- No user-facing docs change.

## Open questions

### OQ-01: Key ownership on `AW-Run` or on `AW-Item`?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: `AW-Item`, from repository evidence: finalize holds the plan id (begin receipt `plan_id`) and no run id (F-3), and a plan re-dispatched across runs is still the same plan's work. `AW-Run` is recorded in evidence for a human reader.

### OQ-02: Should a `foreign` trailer excuse a path?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: No. The maintainer's brief (2026-09-26) scopes the fix to "a path owned by THIS run always requires a reason" and "`unknown` ... falls back to today's predicate"; excusing on `foreign` is a separate trade (Deferred, Carrier-Declined). `foreign` therefore falls back to today's predicate too.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the three precheck values for the E-01 repo.
  - Observed evidence: PASS. Precheck values on scratch E-01 repo show other.py excused:
    exit_code: 0
    attribution_source: commit-cohesion
    out_of_scope_paths: []
    disregarded_unowned_paths: ['other.py']
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff adding `_commit_run_ownership`, and an in-process run printing its result for the trailered commit against `abc123` and `zzz999` and for the untrailered commit.
  - Observed evidence: PASS. _commit_run_ownership correctly classifies owned, foreign, unknown on scratch commits:
    Diff adding `_commit_run_ownership`:
    ```python
    def _commit_run_ownership(
        repo_root: Path, sha: str, plan_id6: str
    ) -> str:
        if not plan_id6 or not sha:
            return "unknown"
        from .git_commit_helper import TRAILER_KEY_ITEM, TRAILER_KEY_RUN

        fmt = f"%(trailers:key={TRAILER_KEY_ITEM},valueonly,separator=%x2C)%x00%(trailers:key={TRAILER_KEY_RUN},valueonly,separator=%x2C)"
        rc, out, _err = _git(repo_root, ["log", "-1", f"--format={fmt}", sha])
        if rc != 0:
            return "unknown"
        parts = out.split("\x00", 1)
        raw_item = parts[0]
        return _classify_item_trailer_value(raw_item, plan_id6)
    ```
    In-process run output:
    ```
    trailered vs abc123: owned
    trailered vs zzz999: foreign
    untrailered vs abc123: unknown
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the diff adding `_trailer_owned_committed_paths` and its printed result on the E-01 repo (`paths`, and the three counts).
  - Observed evidence: PASS. _trailer_owned_committed_paths single-call delimited parse returns paths=['other.py'], owned=1, foreign=0, unknown=1:
    Diff adding `_trailer_owned_committed_paths`:
    ```python
    def _trailer_owned_committed_paths(
        repo_root: Path, base_head: str, plan_id6: str
    ) -> TrailerAttribution:
        if not plan_id6 or not base_head or base_head == "unversioned":
            return TrailerAttribution(frozenset(), 0, 0, 0)
        from .git_commit_helper import TRAILER_KEY_ITEM

        fmt = f"%x1e%H%x00%(trailers:key={TRAILER_KEY_ITEM},valueonly,separator=%x2C)%x1f"
        rc, out, _err = _git(
            repo_root,
            ["log", "--no-merges", f"--format={fmt}", "--name-only", f"{base_head}..HEAD"],
        )
        if rc != 0:
            return TrailerAttribution(frozenset(), 0, 0, 0)

        owned_paths: Set[str] = set()
        owned_count = 0
        foreign_count = 0
        unknown_count = 0

        records = out.split("\x1e")
        for r in records:
            if not r.strip():
                continue
            parts = r.split("\x1f", 1)
            header = parts[0]
            body = parts[1] if len(parts) > 1 else ""
            h_parts = header.split("\x00", 1)
            raw_item = h_parts[1] if len(h_parts) > 1 else ""
            classification = _classify_item_trailer_value(raw_item, plan_id6)
            paths = [ln.strip() for ln in body.splitlines() if ln.strip()]

            if classification == "owned":
                owned_count += 1
                owned_paths.update(paths)
            elif classification == "foreign":
                foreign_count += 1
            else:
                unknown_count += 1

        return TrailerAttribution(
            frozenset(owned_paths), owned_count, foreign_count, unknown_count
        )
    ```
    Printed result on E-01 repo:
    ```
    paths: ['other.py']
    owned: 1
    foreign: 0
    unknown: 1
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `finalize_precheck` diff and the three precheck values plus `trailer_attribution` on the E-01 repo after the change.
  - Observed evidence: PASS. finalize_precheck populates trailer_attribution and demands other.py in out_of_scope_paths:
    `finalize_precheck` diff:
    ```diff
    @@ -2818,6 +2818,13 @@
                 if exact.anchored
                 else _execution_cohesive_committed_paths(repo_root, base_head, scope_paths)
             )
    +        trailered = _trailer_owned_committed_paths(repo_root, base_head, plan_id)
    +        evidence["trailer_attribution"] = {
    +            "owned_commits": trailered.owned,
    +            "foreign_commits": trailered.foreign,
    +            "unknown_commits": trailered.unknown,
    +            "owned_paths": sorted(trailered.paths),
    +        }
             evidence["attribution_source"] = (
                 "run-record-exact"
                 if exact.anchored
    @@ -2838,7 +2845,19 @@
                     # fix (owned, therefore reason required) rather than excusing it on absent evidence.
                     # This is what keeps a plan whose ONLY commit is out-of-scope refused.
                     owned = (
    -                    _working_tree_path_is_owned(
    +                    True
    +                    if p in trailered.paths
    +                    else (
    +                        _working_tree_path_is_owned(
    +                            p,
    +                            scope_paths=scope_paths,
    +                            committed=(),
    +                            plan_rel=plan_rel,
    +                            cohesive_committed=cohesive.paths,
    +                        )
    +                        if cohesive.anchored
    +                        else True
    +                    )
                     )
    ```
    Three precheck values plus `trailer_attribution` on E-01 repo:
    ```
    attribution_source: commit-cohesion
    out_of_scope_paths: ['other.py']
    disregarded_unowned_paths: []
    trailer_attribution: {'owned_commits': 1, 'foreign_commits': 0, 'unknown_commits': 1, 'owned_paths': ['other.py']}
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the docstring diffs; then each of the three per-phrase anchors E-05 names (`essentially no commit in`, `when those land`, `exact fix that would remove`) run against `agent_workflows/ipd_lifecycle.py` BEFORE the edit exiting 0 with its line number, and AFTER the edit exiting 1. Do NOT substitute the authored wrapped-phrase grep: it exits 1 on the unmodified file (measured at review) and so proves nothing.
  - Observed evidence: PASS. Three docstrings updated; each of the 3 anchors exits 0 before edit and 1 after:
    BEFORE the edit:
    ```
    $ rg -n "essentially no commit in" agent_workflows/ipd_lifecycle.py
    2267:    * COMMIT TRAILERS (``AW-Run:``/``AW-Item:``) would settle it exactly, but essentially no commit in
    (exit code: 0)

    $ rg -n "when those land" agent_workflows/ipd_lifecycle.py
    2178:    WRITER is plan ``wao266``; when those land they become a third and better source ahead of this one).
    (exit code: 0)

    $ rg -n "exact fix that would remove" agent_workflows/ipd_lifecycle.py
    2459:    exact fix that would remove the second cost is commit trailers (backlog ``a8eufb``); until those
    (exit code: 0)
    ```

    AFTER the edit:
    ```
    $ rg -n "essentially no commit in" agent_workflows/ipd_lifecycle.py
    (exit code: 1)

    $ rg -n "when those land" agent_workflows/ipd_lifecycle.py
    (exit code: 1)

    $ rg -n "exact fix that would remove" agent_workflows/ipd_lifecycle.py
    (exit code: 1)
    ```

    Docstring diffs:
    ```diff
    --- a/agent_workflows/ipd_lifecycle.py
    +++ b/agent_workflows/ipd_lifecycle.py
    @@ -2174,8 +2174,9 @@
         note above), and because the failure mode is ASYMMETRIC: a corrupted record can only cause a
         MISSING demand for a path the plan did commit, which is the same false EXCUSE cohesion already
         accepts and documents, never a false CLAIM written into permanent history. Non-forgeable
    -    attribution stays the deferred item it already is (commit trailers, backlog ``a8eufb``, whose
    -    WRITER is plan ``wao266``; when those land they become a third and better source ahead of this one).
    +    attribution is supplemented by commit trailers (stamped via ``a6xbso`` and read via ``199u11``),
    +    which land as an additive demand source ahead of cohesion; they compose with the run record
    +    instead of deciding alone because a trailer can only ADD a demand.
     @@ -2265,8 +2266,9 @@
           identity (measured: identical ``%an``/``%ae`` across the incident's own and foreign commits);
         * the RUN RECORD (``last_outcome.commits[].sha``) is unreachable, being gitignored, absent from a
           lane worktree, and never handed a run id by finalize; and
    -    * COMMIT TRAILERS (``AW-Run:``/``AW-Item:``) would settle it exactly, but essentially no commit in
    -      history carries one yet, so nothing can be consumed today (backlog ``a8eufb``).
    +    * COMMIT TRAILERS (``AW-Item:`` stamped by ``aw commit`` and read via
    +      :func:`_trailer_owned_committed_paths`) are now read ahead of cohesion as an additive
    +      demand-only source; untrailered and foreign commits still fall back to cohesion.
     @@ -2570,12 +2572,13 @@
         * (Order 01 OQ-01/F3) an executor's OWN uncommitted out-of-scope edit is byte-identical to a
           co-worker's, so it is disregarded too; and
         * (scopeattr `h9cn0y`) an executor's own COMMITTED out-of-scope path escapes the reason
    -      requirement when it rides in a commit containing no declared path.
    +      requirement when it rides in an UNTRAILERED commit containing no declared path.

         The mitigation for both is the execution contract's path-scoped commits, which keep a plan's real
         work in commits anchored by its declared paths, where the reason requirement still fires. The
    -    exact fix that would remove the second cost is commit trailers (backlog ``a8eufb``); until those
    -    exist, this is the strongest attribution available, and it is deliberately weaker than a proof.
    +    second cost is now removed for trailered commits (read via ``_trailer_owned_committed_paths``, Set
    +    ``trailread``, ``199u11``), but remains for untrailered commits and for raw ``git commit``; this
    +    is the strongest attribution available, and it is deliberately weaker than a proof.
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_finalize_trailer_attribution.py tests/test_ipd_lifecycle_cli.py -o addopts="" -q` passing with counts; then the new file with the E-04 hunk temporarily reverted, showing (1) and (6) FAILING, (5) failing with an AttributeError if the E-02 hunk is also reverted, and (2), (4) passing; then passing after restoring. Paste the bare `python3 -m pytest` summary BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty). ALSO paste case (6)'s trailer assertion output (both `AW-Run` and `AW-Item` read back off the commit `aw commit` produced), so a vacuously-passing case (6) that wrote no trailer is distinguishable from a real end-to-end pass.
  - Observed evidence: PASS. Full suite 2803 passed (0 failing delta); revert shows (1),(6) fail; Order 1 stamps and reads back both trailers:
    1. Combined test passing output:
    ```
    $ python3 -m pytest tests/test_finalize_trailer_attribution.py tests/test_ipd_lifecycle_cli.py -o addopts="" -q
    ...................................................                      [100%]
    51 passed in 20.09s
    ```

    2. Failure demonstration with E-04 hunk temporarily reverted:
    ```
    $ python3 -m pytest tests/test_finalize_trailer_attribution.py -o addopts="" -q
    .FF...                                                                   [100%]
    =================================== FAILURES ===================================
    _____ FinalizeTrailerAttributionTests.test_case_6_end_to_end_with_order_1 ______
    AssertionError: 'other.py' not found in []
    _______ FinalizeTrailerAttributionTests.test_case_1_own_trailer_demands ________
    AssertionError: 'other.py' not found in []
    =========================== short test summary info ============================
    FAILED tests/test_finalize_trailer_attribution.py::FinalizeTrailerAttributionTests::test_case_6_end_to_end_with_order_1
    FAILED tests/test_finalize_trailer_attribution.py::FinalizeTrailerAttributionTests::test_case_1_own_trailer_demands
    2 failed, 4 passed in 1.21s
    ```
    Prior to implementing E-02, case (5) also failed:
    `AttributeError: module 'agent_workflows.ipd_lifecycle' has no attribute '_commit_run_ownership'`
    After restoring E-04 hunk:
    ```
    $ python3 -m pytest tests/test_finalize_trailer_attribution.py -o addopts="" -q
    ......                                                                   [100%]
    6 passed in 1.33s
    ```

    3. Bare pytest summary:
    BEFORE:
    `2797 passed, 2 skipped, 3 warnings in 352.77s (0:05:52)`
    AFTER:
    `2803 passed, 2 skipped, 3 warnings in 130.60s (0:02:10)`
    After-minus-before failing node-ID set: empty set (0 failures).

    4. Case (6) trailer read-back assertion:
    ```
    AW-Run read back: 'run-20260926T000000Z-1'
    AW-Item read back: 'abc123'
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the comment-block diff and `rg -n "compute_scope_reconciliation" agent_workflows/ipd_lifecycle.py`; state explicitly that the diff adds comment lines only and introduces no conditional branch keyed on `trailer_attribution`.
  - Observed evidence: PASS. Comment-block diff adds documentation only; rg confirms compute_scope_reconciliation reference:
    Comment-block diff:
    ```diff
    @@ -2786,3 +2786,11 @@
     #     requirement when it rides in a commit containing no declared path. The mitigation is
     #     path-scoped commits; the real fix is commit trailers (backlog `a8eufb`).
    +#     requirement when it rides in an UNTRAILERED commit containing no declared path. With commit
    +#     trailers (Set `trailread`, `199u11`), this cost applies ONLY to untrailered commits.
    +#     Under a runner/driver, `runner_shared.compute_scope_reconciliation` maps every path in
    +#     `out_of_scope_paths` to a standard reconciliation reason and hands it to finalize, so under
    +#     `aw oc run` / `aw agy run` the newly-demanded path is satisfied without stopping the run.
    +#     This auto-reasoning is correct rather than a hole: a trailer-owned path IS this execution's
    +#     own work and the auto-reason asserts exactly that (unlike cohesion, where auto-reasoning could
    +#     assert a co-worker's path). The user-visible effect of this plan under a runner is therefore
    +#     a truer permanent record (the path is recorded as reconciled rather than silently disregarded),
    +#     not a new stop.
    ```
    Anchor grep output:
    ```
    $ rg -n "compute_scope_reconciliation" agent_workflows/ipd_lifecycle.py
    2789:    #     Under a runner/driver, `runner_shared.compute_scope_reconciliation` maps every path in
    2912:        # key to auto-reason the widening (`runner_shared.compute_scope_reconciliation`), because all
    ```
    The diff adds comment lines only and introduces no conditional branch keyed on `trailer_attribution`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Finalize starts reading `AW-Item` trailers: a committed out-of-scope path in a commit trailered as THIS plan's always needs a `--scope-reason`. Untrailered and foreign-trailered commits are judged exactly as today, so the change can only add demands, never remove one. No `RUN-*` finding code is bound. It depends on Order 1 (`a6xbso`), which makes agent commits carry the trailer.

WHO ACTUALLY FEELS THE NEW DEMAND, stated because the sentence above is easy to over-read (review F-6). A HUMAN finalizing by hand is asked for one more `--scope-reason`. Under `aw oc run` / `aw agy run` the demand is AUTO-ANSWERED by `runner_shared.compute_scope_reconciliation`, which already supplies a reason for every out-of-scope path, so no run stops and no lane is stranded by this change. The gain on the automated path is a TRUER PERMANENT RECORD: the plan's own out-of-scope commit is recorded as reconciled work instead of being silently disregarded. That auto-reason is honest here precisely because a trailer-owned path IS this execution's own work, which is not true of the cohesion case it sits beside. E-07 writes this into the code's own comment so the next reader does not have to re-derive it.

THE HONEST SECURITY PROPERTY. A trailer is a CONSISTENCY RECORD, not tamper-proof provenance: any process running as the same user can write one, exactly as it can set `AW_EXECUTION_ROLE`. This is acceptable here for a reason specific to the DIRECTION of the change: a trailer can only ADD a demand, so forging one costs an attacker an extra reason to write and can never manufacture a false EXCUSE. That asymmetry is why OQ-02 refuses to let a `foreign` trailer excuse a path, and it is the same discipline `_run_record_committed_paths` already documents for the locally-writable run record.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/ipd_lifecycle.py` (the two new helpers, the committed-half branch, the accepted-cost prose in three docstrings, and E-07's comment) and `tests/test_finalize_trailer_attribution.py` (new). EXPECTED TO BE READ AND NOT MODIFIED: `agent_workflows/git_commit_helper.py` (the two key constants), `agent_workflows/runner_shared.py` (`compute_scope_reconciliation`, quoted by E-07 and not changed), `agent_workflows/check_engine.py` (`check_scope_drift`, deliberately unfiltered), and `tests/test_ipd_lifecycle_cli.py` (its widening and `p7dqwz` assertions must stay green untouched). If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-06 must show the new tests FAILING before the change. THE TWO EASIEST CLAIMS TO FAKE HERE, both of which V-* items now demand real output for: V-05's greps (the authored form passes on an unmodified file, so paste the before-and-after exit status of each of the three anchors) and E-06 case (6)'s end-to-end run (paste the trailers read back off the commit `aw commit` produced, because a case that wrote no trailer passes while proving nothing).

GENUINE STOP CONDITIONS.
- If E-01 finds `other.py` already demanded, stop and report: trailers are already read and this plan's premise is spent.
- If E-06 case (6) finds `aw commit` producing no trailers with both env vars set, stop and report that Order 1's channel is absent. Do NOT hand-write the trailer to make the case pass, and do NOT delete the case.
- Do NOT weaken, skip, or delete the `tests/test_ipd_lifecycle_cli.py` assertion that `tests/test_extra.py` lands in `disregarded_unowned_paths`. It was verified at review to be unaffected (that fixture commits no trailer). If it nonetheless goes red, that means the reader is promoting an `unknown` commit to `owned`, which is the one inversion this design forbids: stop and report rather than adjusting the test.

Commit ONLY paths in `- Scope-Paths:` through `aw commit 199u11 -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence. The terminal transition is `aw ipd finalize`, which the RUNNER owns when this plan executes in a lane; run it yourself only if you are executing by hand outside a runner. Then close backlog `am1g38` `done` with `--evidence` citing the executed plan. NO RELEASE GATE IS IN PLAY: verified at review that neither this plan nor `am1g38` carries `- Blocks-Release:`, and `- Work-Kind: followup` is not in the repository's gating set.
