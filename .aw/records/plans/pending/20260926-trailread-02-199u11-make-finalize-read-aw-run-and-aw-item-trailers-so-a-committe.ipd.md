# IPD: Make finalize read AW-Run and AW-Item trailers so a committed out-of-scope path this plan made always needs a reason

- Date: 2026-09-26
- Kind: child
- Concern: FINALIZE CANNOT TELL WHETHER A COMMITTED OUT-OF-SCOPE PATH BELONGS TO THIS EXECUTION, SO `h9cn0y`'S ACCEPTED COST WAIVES THE REASON REQUIREMENT FOR THE EXECUTOR'S OWN WORK. `ipd_lifecycle._working_tree_path_is_owned`'s docstring states the cost: "an executor's own COMMITTED out-of-scope path escapes the reason requirement when it rides in a commit containing no declared path", and names trailers as "the exact fix". `ipd_lifecycle._execution_cohesive_committed_paths` says trailers "would settle it exactly, but essentially no commit in history carries one yet". Nothing in the package reads a trailer back: `run_evidence.RUN_FINDING_CODES` records `RUN-COMMIT-CONTENTS`/`RUN-COMMIT-GATEWAY` `UNBOUND_BY_DEPENDENCY` "waiting on a trailer READ-BACK predicate". Reproduced at HEAD `61ef21d8` on a scratch repo: after `begin` on a plan declaring `agent_workflows/demo.py, tests/test_demo.py`, one in-scope commit plus one commit touching only `other.py` whose message carries `AW-Item: abc123` (the plan's own id6) gives `finalize_precheck` -> `attribution_source: commit-cohesion`, `out_of_scope_paths: []`, `disregarded_unowned_paths: ['other.py']`, i.e. the plan's own trailered commit is excused. Order 1 (`a6xbso`) makes the agent's `aw commit` calls carry these trailers, so the corpus this reader needs is about to exist.
- Scope: IN: (a) `ipd_lifecycle._commit_run_ownership(repo_root, sha, plan_id6) -> "owned" | "foreign" | "unknown"`, reading `AW-Item`/`AW-Run` via `git log -1 --format=%(trailers:key=...,valueonly)`; (b) a range helper `_trailer_owned_committed_paths(repo_root, base_head, plan_id6)` returning the paths of every non-merge commit in `base_head..HEAD` classified `owned`, plus per-class commit counts for evidence, using ONE `git log` call; (c) in `finalize_precheck`'s committed-half branch, a path in the trailer-owned set is ALWAYS owned (reason required), consulted BEFORE and independently of cohesion or the run record; `unknown` and `foreign` commits fall through to today's predicate unchanged; (d) a `trailer_attribution` evidence block; (e) updating the accepted-cost prose in `_working_tree_path_is_owned`, `_execution_cohesive_committed_paths`, `_run_record_committed_paths` and the `finalize_precheck` comment; (f) behavioral tests on scratch repos. OUT: binding `RUN-COMMIT-CONTENTS`/`RUN-COMMIT-GATEWAY` (Carrier-Declined); using a `foreign` trailer to EXCUSE a path (deferred, see OQ-02); any change to `check_engine.check_scope_drift`, which deliberately reads the unfiltered window.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_finalize_trailer_attribution.py
- Item-Dependencies: executed:a6xbso
- Status: to-review
- Work-Kind: followup
- Priority: medium
- From-Backlog: am1g38
- Set: trailread
- Order: 2
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 199u11

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog am1g38 on the maintainer's batch-graduation instruction; ordered after a6xbso (Order 1) so the reader has a corpus. The accepted cost was reproduced at HEAD 61ef21d8 on a scratch repo (a commit trailered with the plan's own AW-Item is disregarded as unowned).
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make finalize demand a `--scope-reason` for every committed out-of-scope path whose commit is trailered as this plan's own, removing `h9cn0y`'s accepted false-excuse cost for trailered commits, while an untrailered commit is judged exactly as today and is never inferred to be foreign.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE THE EXCUSE at the executing HEAD. Build a scratch repo exactly as the `tests/test_ipd_lifecycle_cli.py` `AdditiveScopeWideningTests.setUp` fixture does (`support.ready_plan_text(plan_id="abc123", ...)` marked performed/pass, `.gitignore` with `.aw/state/`, `agent_workflows/demo.py`, `tests/test_demo.py`, committed), run `ipd_lifecycle.begin`, commit an in-scope edit to `agent_workflows/demo.py`, then commit a new `other.py` alone with message `oos\n\nAW-Run: run-20260926T000000Z-1\nAW-Item: abc123`. Paste `finalize_precheck`'s `attribution_source`, `scope_audit.out_of_scope_paths` and `scope_audit.disregarded_unowned_paths`. Do this with `AW_EXECUTION_ROLE` unset. If `other.py` is already in `out_of_scope_paths`, STOP and report that trailers are already read.
  - Depends on: none
  - Expected outcome: `commit-cohesion`, `[]`, `['other.py']`.
  - Execution state: pending

### Task group 2: the reader

- [ ] E-02 ADD `ipd_lifecycle._commit_run_ownership(repo_root, sha, plan_id6)` returning `"owned"`, `"foreign"`, or `"unknown"`. Read the values with `_git(repo_root, ["log", "-1", "--format=%(trailers:key=AW-Item,valueonly,separator=%x2C)%x00%(trailers:key=AW-Run,valueonly,separator=%x2C)", sha])`, using the key names `git_commit_helper.TRAILER_KEY_ITEM`/`TRAILER_KEY_RUN` (imported lazily) rather than re-spelling them. Rules: no `AW-Item` value -> `unknown` (whatever `AW-Run` says, because an ownership claim without an item cannot name this plan); any `AW-Item` value equal to `plan_id6` -> `owned`; `AW-Item` present but none equal -> `foreign`; a git failure -> `unknown`. `AW-Run` is parsed and returned in evidence only: finalize is never handed a run id (the `_execution_cohesive_committed_paths` docstring: the run record is "never handed a run id by finalize"), so the ITEM is the key that names this execution; state that in the docstring. The docstring must also state the fail-closed rule verbatim in substance: `unknown` is NEVER treated as `foreign`, because the corpus permanently contains untrailered commits (backlog `j2srcc`, `wao266` OQ-03), and a trailer is a consistency record, not tamper-proof provenance (same honest limit `_run_record_committed_paths` states).
  - Depends on: E-01
  - Expected outcome: on a scratch repo, a commit trailered `AW-Item: abc123` -> `owned` for `abc123` and `foreign` for `zzz999`; an untrailered commit -> `unknown` for both.
  - Execution state: pending

- [ ] E-03 ADD `ipd_lifecycle._trailer_owned_committed_paths(repo_root, base_head, plan_id6)` returning a small NamedTuple `(paths: frozenset, owned: int, foreign: int, unknown: int)`. Use ONE call, `git log --no-merges --format=<sentinel>%H%x00%(trailers:key=AW-Item,valueonly,separator=%x2C) --name-only base_head..HEAD`, and classify each commit by the SAME rule as E-02 (factor the classification of an already-read `AW-Item` value into one private function both call, so they cannot drift). Use an explicit sentinel prefix on the header line rather than a 40-hex heuristic, so a path can never be mistaken for a header. `paths` is the union of paths of `owned` commits. Empty `plan_id6`, no range, or a git failure returns an empty result with zero counts (no demand added, today's behavior).
  - Depends on: E-02
  - Expected outcome: on the E-01 repo, `paths == {"other.py"}` and `owned == 1`, `unknown == 1` (the in-scope commit).
  - Execution state: pending

### Task group 3: consult it

- [ ] E-04 CONSULT THE READER IN `finalize_precheck`'s committed-half branch. Compute `trailered = _trailer_owned_committed_paths(repo_root, base_head, plan_id)` once, beside the existing `exact`/`cohesive` computation. In the loop, inside `if p in committed_set:`, set `owned = True` when `p in trailered.paths`, BEFORE the existing cohesion/`anchored` expression, which is otherwise untouched; the working-tree branch is untouched. This only ever ADDS demands, never removes one, so every path owned today is still owned. Record `evidence["trailer_attribution"] = {"owned_commits": ..., "foreign_commits": ..., "unknown_commits": ..., "owned_paths": sorted(...)}`, and leave `attribution_source` unchanged in meaning (it still names the source that decided the non-trailered remainder). Update the block comment "ACCEPTED COST (the honest bound ...)" in `finalize_precheck` to say the cost now applies ONLY to untrailered commits.
  - Depends on: E-03
  - Expected outcome: on the E-01 repo, `out_of_scope_paths == ['other.py']`, `disregarded_unowned_paths == []`, and `trailer_attribution.owned_paths == ['other.py']`.
  - Execution state: pending

- [ ] E-05 UPDATE THE ACCEPTED-COST PROSE so no docstring still says trailers are unread: `_working_tree_path_is_owned` (the second accepted-cost bullet and the closing "The exact fix that would remove the second cost is commit trailers" sentence: now removed for trailered commits, remains for untrailered ones and for raw `git commit`, which is not refused per `a6xbso` OQ-02); `_execution_cohesive_committed_paths` (the "COMMIT TRAILERS ... essentially no commit in history carries one yet" bullet: now read, as a demand-only source ahead of cohesion); and `_run_record_committed_paths` (the "when those land they become a third and better source" sentence: they have landed, as an additive demand source rather than a replacement, and why: a trailer can only ADD a demand, so it composes with the run record instead of deciding alone). Do NOT rename `_working_tree_path_is_owned` (its docstring explains why).
  - Depends on: E-04
  - Expected outcome: `rg -n "essentially no commit in history carries one yet|when those land" agent_workflows/ipd_lifecycle.py` returns nothing.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-06 ADD `tests/test_finalize_trailer_attribution.py`, behavioral only (no source-text or structure assertions, maintainer ruling 2026-09-26), using `support.declare_execution_role(self)` in `setUp` so the coordinator role is declared rather than inherited, and the E-01 fixture shape. Cases: (1) OWN TRAILER DEMANDS: the E-01 shape -> `other.py` in `out_of_scope_paths`, not in `disregarded_unowned_paths`; and `finalize(..., apply=True)` WITHOUT a reason for `other.py` refuses, WITH `scope_reasons={"other.py": "..."}` succeeds. (2) UNTRAILERED FALLS BACK: identical but the `other.py` commit has no trailer -> `other.py` in `disregarded_unowned_paths`, exactly today's result (pins that `unknown` is not promoted either way). (3) FOREIGN FALLS BACK: `AW-Item: zzz999` -> same as (2), and `trailer_attribution.foreign_commits == 1`. (4) NO FALSE UNKNOWN->FOREIGN: a plan whose ONLY commit is an untrailered out-of-scope commit (the `p7dqwz` shape `_execution_cohesive_committed_paths` cites) still has that path in `out_of_scope_paths` (the `anchored=False` fail-closed path is unaffected). (5) `_commit_run_ownership` on three real commits returns `owned`/`foreign`/`unknown` as specified, including a commit with `AW-Run` but no `AW-Item` -> `unknown`. (6) END TO END WITH ORDER 1: the owned commit is produced by `python3 -m agent_workflows commit --no-plan -m oos -- other.py` run as a subprocess with `AW_RUN_ID`/`AW_ITEM_ID6=abc123` in its env (the writer `a6xbso` ships), proving the writer and reader agree on the format.
  - Depends on: E-04, E-05
  - Expected outcome: all pass; (1), (3)'s counter, (5) and (6) FAIL before the change (no reader), while (2) and (4) pass before and after.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `CommittedAttribution` exists so an empty set is never read as "nothing is owned"; the fail-closed switch is `anchored`. This plan's reader adds demands only, so it needs no such switch and cannot invert the gate.
- `_run_record_committed_paths` "decides alone rather than being unioned with cohesion" (`gys47u` OQ-01) because a union would re-admit foreign paths. That argument is about EXCUSING; a trailer here only adds DEMANDS, so composing it additively does not re-admit anything.
- The accepted cost and "trailers are the fix" are stated in three docstrings and one block comment in `ipd_lifecycle`; all must move together (E-05).
- `check_engine.check_scope_drift` reads the unfiltered union deliberately (`_paths_changed_by_this_execution` docstring) and is not touched.
- Trailer keys are single-sourced in `git_commit_helper` (`TRAILER_KEY_RUN`, `TRAILER_KEY_ITEM`).
- Test role: `support.declare_execution_role(self)` (conftest scrubs `AW_EXECUTION_ROLE`, but `tests/test_ipd_lifecycle_cli.py` is known to inherit, backlog `owi0no`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `61ef21d8` on 2026-09-26.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_lifecycle.finalize_precheck` | A commit trailered with the plan's own `AW-Item` is excused when it touches no declared path. | scratch repo: `0 commit-cohesion [] ['other.py']` (rc, attribution_source, out_of_scope_paths, disregarded_unowned_paths) |
| F-2 | MEDIUM | package | No code reads a trailer back. | `rg -n "trailers:key\|interpret-trailers" agent_workflows` finds only four comment/docstring lines in `git_commit_helper`; `run_evidence` `RUN-COMMIT-CONTENTS` `waiting_on` "a trailer READ-BACK predicate" |
| F-3 | INFO | finalize inputs | Finalize has the plan id (receipt `plan_id`) but no run id, so the item trailer is the usable key. | `begin` receipt keys: `plan_id`, `base_head`, `scope_paths`, ... (no `run_id`); `_execution_cohesive_committed_paths`: run record "never handed a run id by finalize" |
| F-4 | INFO | corpus | Today only one agent code commit is trailered, so this reader is inert until Order 1 lands. | `a6xbso` F-1 |

## Proposed changes (ordered, validatable)

1. E-01 reproduces the excuse.
2. E-02 adds the per-commit classifier.
3. E-03 adds the one-call range helper.
4. E-04 consults it in the committed half, demand-only.
5. E-05 updates the accepted-cost prose.
6. E-06 proves it, including an end-to-end run through Order 1's writer.

## Deferred / out of scope (with reason)

- Binding `RUN-COMMIT-CONTENTS` / `RUN-COMMIT-GATEWAY` in `run_evidence` and spec `25kzda` 4.2.
  - Carrier-Declined: binding them needs a tree-diff proof that a commit's paths equal the item-owned delta (spec `25kzda` 4.6), not just a reader; `run_evidence`'s own tally warns that binding on a writer or reader alone is the fail-open error. No carrier is filed because no plan is designing that proof.
- Using a `foreign` trailer to EXCUSE a committed path that cohesion would otherwise attribute.
  - Carrier-Declined: it would reduce false DEMANDS only (the fail-closed, merely annoying direction), and trusting a locally writable trailer to remove a demand is a weaker bet than trusting it to add one. See OQ-02.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/git_commit_helper.py` is READ (key constants) and not modified.
- Scope-Paths justification: `ipd_lifecycle.py` holds the reader and the precheck; the new test file holds E-06.

## Required tests / validation

- `tests/test_finalize_trailer_attribution.py` (new), cases (1)-(6); (1), (5), (6) shown FAILING before the change.
- `tests/test_ipd_lifecycle_cli.py` stays green (its `p7dqwz` counterexample and widening tests).
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A for specs: spec `25kzda` 4.6 already specifies trailer-based ownership; this plan implements a demand-only subset of it and binds no 4.2 code. No `.spec.md` is in `- Scope-Paths:`. The spec's preamble sentence "nothing reads trailers back" becomes stale when this executes; the Set `spec25kfix` amendment (`j0ag0u`) words that clause as a dated snapshot, and the spec's own convention says such snapshots must be re-measured.
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

- [ ] V-01 validates E-01
  - Required evidence: paste the three precheck values for the E-01 repo.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff adding `_commit_run_ownership`, and an in-process run printing its result for the trailered commit against `abc123` and `zzz999` and for the untrailered commit.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff adding `_trailer_owned_committed_paths` and its printed result on the E-01 repo (`paths`, and the three counts).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `finalize_precheck` diff and the three precheck values plus `trailer_attribution` on the E-01 repo after the change.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the docstring diffs and `rg -n "essentially no commit in history carries one yet|when those land" agent_workflows/ipd_lifecycle.py` returning nothing (exit 1).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_finalize_trailer_attribution.py tests/test_ipd_lifecycle_cli.py -o addopts="" -q` passing with counts; then the new file with the E-04 hunk temporarily reverted, showing (1) and (6) FAILING, (5) failing with an AttributeError if the E-02 hunk is also reverted, and (2), (4) passing; then passing after restoring. Paste the bare `python3 -m pytest` summary BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Finalize starts reading `AW-Item` trailers: a committed out-of-scope path in a commit trailered as THIS plan's always needs a `--scope-reason`. Untrailered and foreign-trailered commits are judged exactly as today, so the change can only add demands, never remove one. No `RUN-*` finding code is bound. It depends on Order 1 (`a6xbso`), which makes agent commits carry the trailer.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/ipd_lifecycle.py` and the new test file. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-06 must show the new tests FAILING before the change.

GENUINE STOP CONDITION: if E-01 finds `other.py` already demanded, stop and report.

Commit ONLY paths in `- Scope-Paths:` through `aw commit 199u11 -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `am1g38` `done` with `--evidence` citing the executed plan.
