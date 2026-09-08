# IPD: Guard the ungated dirty-base cases nna8yz leaves open: untracked dirt and shared-tree runs

- Date: 2026-09-07
- Kind: child
- Concern: A run that starts against a dirty main tree discovers the consequence hours and dollars later. Run `run-20260905T050043Z-639569` began at 05:00:43 with two tracked driver files already dirty, said nothing, spent ~3 hours and ~$40 executing `76gsmv`, and only at 08:06:32 refused to integrate for a reason fully knowable at startup; two more items hit the identical overlap over the following four hours. The condition was present and stable throughout. Only the discovery was late.
  MOST OF THAT IS ALREADY BEING FIXED, AND THIS PLAN MUST NOT REDO IT. Approved plan `nna8yz` (`lanectn` Order 02) E-05 adds a pre-launch guard that "refuses an unattended isolated turn when the target checkout has dirty TRACKED paths, naming them, before any worker process is spawned", in shared `agent_workflows/lane_containment.py` with both drivers wired. Verified 2026-09-08: the motivating run carried `options.isolate_worktree = true` and its dirt was `oc_runipd.py` plus `agy_runipd.py`, both TRACKED, so `nna8yz` E-05 would have refused it before the first spawn. This plan therefore does NOT re-implement the tracked-file check and does not restate that incident as unaddressed.
  THREE CASES SURVIVE, AND THEY ARE THE ONES `nna8yz` DELIBERATELY OR STRUCTURALLY EXCLUDES. (1) UNTRACKED DIRT: `nna8yz` E-05 excludes it by explicit reasoning ("a lane is made from a commit, so untracked content was never silently omitted the way an uncommitted tracked edit is, and refusing on it would make an unattended run unstartable in any working checkout"). That reasoning is correct FOR A LANE GUARD, and it is exactly the incident the maintainer recorded: a stray `aw install` wrote 130+ files into the working tree, uncommitted and largely UNTRACKED, and on at least two occasions an agent did not realize the pollution was its own. (2) SHARED-TREE RUNS: E-05 guards an unattended ISOLATED turn; a run started with `--no-isolate-worktree` shares the main tree and gets no guard at all. (3) NO CONSENT FLAG EXISTS: `--allow-dirty-base` greps to ZERO under `agent_workflows/` at HEAD, so there is currently no sanctioned way to proceed deliberately over known dirt.
- Scope: Close the dirty-base cases `nna8yz` E-05 leaves ungated, and add the consent surface that makes a deliberate override possible: report untracked dirt at run start with its consequence stated, guard the `--no-isolate-worktree` path, and add one explicit `--allow-dirty-base` consent flag. Reuse `nna8yz`'s guard and porcelain parser; add no second whole-tree dirty check. Resolve no dirt: report, refuse, and let a human decide.
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_lane_clean_base.py, tests/test_dirty_base_gate.py
- Item-Dependencies: executed:nna8yz
- Status: to-review
- Set: dirtybase
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 3i0aaz
- From-Backlog: p8ni63
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `p8ni63`, DELIBERATELY NARROWED. The item as written asks for a startup dirty-base gate in `runner_shared.py`; approved plan `nna8yz` E-05 already delivers that for the tracked+isolated case, including the item's entire motivating incident (verified by reading that run's `state.json` for `isolate_worktree`). Graduating the item as written would have duplicated E-05's check into a second module and re-litigated a solved case. Only the three genuinely ungated cases are carried forward, and the item's file now records which parts are dead.

## Goal

Make every dirty-base condition either GUARDED before cost is incurred or explicitly CONSENTED to, including the untracked and shared-tree cases a lane guard cannot reach.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish what nna8yz actually shipped

- [ ] E-01 READ `nna8yz`'s LANDED E-05 AND RECORD ITS EXACT BOUNDARY before writing anything, because this plan's whole scope is defined by that boundary and the boundary is a fact about code, not about the plan's prose. Locate the guard by SYMBOL in `agent_workflows/lane_containment.py`, and record: which porcelain helper it reuses, whether it distinguishes tracked from untracked, what it does on a `--no-isolate-worktree` run, and whether it grew any override.
  IF E-05 ALREADY COVERS A CASE THIS PLAN CLAIMS, DROP THAT CASE AND SAY SO. `nna8yz` may have been reviewed or amended after this plan was authored; the executor's first duty is to re-measure rather than trust this plan's Concern. In particular, if E-05 landed WITH an `--allow-dirty-base` flag, E-04 below collapses to wiring rather than adding.
  - Depends on: none
  - Expected outcome: a written statement of E-05's shipped boundary by symbol, and an explicit list of which of this plan's three cases remain genuinely open.
  - Execution state: pending

### Task group 2: the three ungated cases

- [ ] E-02 REPORT UNTRACKED DIRT AT RUN START, with its consequence stated, and do NOT refuse on it by default. This is the `aw install` case: 130+ uncommitted, largely untracked files, which `nna8yz` E-05 excludes by design. The asymmetry is deliberate and must be preserved: refusing on untracked content "would make an unattended run unstartable in any working checkout", so this item REPORTS untracked dirt while E-05 REFUSES on tracked dirt.
  STATE THE CONSEQUENCE, NOT JUST THE FACT. A bare list of paths is what today's silence effectively is. The report must say plainly that any lane whose changed files overlap these paths WILL be refused at integration, which is the causal chain the motivating incident took three hours to reveal.
  REUSE THE PORCELAIN PARSER, and state in a comment how this question differs from the integration-time overlap check: that one asks whether an incoming lane's changed set intersects dirty paths; this one asks what is dirty before any lane exists. A third parser is forbidden (`cnwy8g`).
  - Depends on: E-01
  - Expected outcome: an untracked-dirt report at run start naming paths AND the integration consequence; the run still starts; no second porcelain parser.
  - Execution state: pending

- [ ] E-03 GUARD THE `--no-isolate-worktree` PATH, which `nna8yz` E-05 structurally cannot reach because it guards an unattended ISOLATED turn. A run sharing the main tree is the case where dirt is MOST dangerous, since the agent writes directly into the tree it is polluting, and today it is the least guarded. Extend the shared guard so a shared-tree run gets the same refusal a lane run gets, on BOTH hosts.
  DO NOT SILENTLY WIDEN E-05's TRACKED-ONLY RULE FOR THE ISOLATED CASE while doing this. The two paths may legitimately differ (a shared-tree run has more to lose), but any difference must be STATED in the code comment and asserted in a test, not left as an accident of where the check was inserted.
  - Depends on: E-02
  - Expected outcome: a `--no-isolate-worktree` run refuses on a dirty base with the paths named, on both hosts; the isolated path's behavior is unchanged unless deliberately altered and stated.
  - Execution state: pending

- [ ] E-04 ADD ONE `--allow-dirty-base` CONSENT FLAG, registered in the SHARED flag surface, so proceeding over known dirt is a recorded deliberate act rather than an accident. Verified at HEAD: the flag does not exist (`grep -rn "allow-dirty-base\|allow_dirty_base" agent_workflows/` returns nothing), so this is new surface on both hosts.
  IT MUST BE ONE FLAG WITH ONE DEFAULT ON BOTH HOSTS. The `--full-auto` divergence (default `False` on one host, `True` on the other) is the measured failure the shared `RUN_POLICY_FLAGS` table exists to prevent. Register it there rather than on each parser.
  CHECK THE SPEC BINDING BEFORE REGISTERING, because this is the trap sibling plan `51vw4y` hit: `tests/test_run_flag_surface.py` reads spec `25kzda` 2.1 in BOTH directions, so a flag registered in `RUN_POLICY_FLAGS` and NOT declared in 2.1 fails the suite, and one declared and not registered fails too. The spec amendment and the registration must therefore land in the SAME change; `.aw/records/specs/...aw-run-deterministic...spec.md` is NOT in this plan's `- Scope-Paths:`, so if that binding still holds, STOP and report rather than editing an undeclared spec file. Maintainer ruling 2026-09-08 on the parallel case: the two are atomic and the plan owning the flag owns the amendment.
  - Depends on: E-03
  - Expected outcome: `--allow-dirty-base` exists on both hosts with ONE default, frozen into run state like every other policy flag, and either the spec binding is satisfied in the same change or the executor stopped and reported.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 TEST ALL THREE CASES ON BOTH HOSTS in a new `tests/test_dirty_base_gate.py`, and leave `tests/test_lane_clean_base.py` (E-05's own file) green and UNEDITED so the two guards are provably independent. Cover: untracked dirt reported and the run STARTS; a `--no-isolate-worktree` run REFUSED on tracked dirt; the same refused run PROCEEDING with `--allow-dirty-base`; and the consent flag frozen in `state.json`'s options.
  ASSERT THE REFUSAL HAPPENS BEFORE ANY SPAWN, not merely that it happens. Patch the spawn and assert it was never called, or show the raised error precedes it. A guard that refuses after paying for a worker turn has not prevented the cost this item exists to prevent.
  ASSERT NO DIRT WAS TOUCHED. This repository's policy for un-owned dirty state is to leave it strictly alone. Show that after every refusal the working tree is byte-identical: no stash, no reset, no checkout, no clean.
  - Depends on: E-04
  - Expected outcome: a test failing against pre-change HEAD for all three cases, passing after; `tests/test_lane_clean_base.py` green with an EMPTY diff; refusal proven pre-spawn; tree proven untouched.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `nna8yz` E-05 is the sibling guard and its module is `agent_workflows/lane_containment.py`, host-neutral by design after that plan's own PR-001 review finding. Extend it; do not fork it.
- An existing porcelain-parsing helper already backs the integration-time dirty-overlap check, and `nna8yz` CID-2 forbids forking a rule. The two checks answer different questions and the comment must say so.
- NO DIRT RESOLUTION, EVER: report, refuse, and leave un-owned state alone (AGENTS.md shared-checkout rules). `z2isfg` is prior art for a begin-time dirty gate AND for the lesson that a refusal message must not tell an operator to commit or stash work they are forbidden to touch. Reuse that wording discipline.
- INFORMING IS NECESSARY AND NOT SUFFICIENT (`k1nity`, measured: byte-identical duplicate work on 3+ resumed runs despite an explicit prompt notice). So the tracked/shared-tree case must REFUSE by default, and only the explicit flag may bypass it.
- Shared checkout: both driver modules are being edited by concurrent runs. Re-locate every symbol before editing.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | overlap with nna8yz | E-05 already refuses an unattended ISOLATED turn on dirty TRACKED paths, in shared `lane_containment.py`, both drivers wired. This plan must not re-implement it. | `nna8yz` E-05 text; `agent_workflows/lane_containment.py` exists at HEAD |
| F-2 | HIGH | the item's incident is covered | The motivating run was ISOLATED and its dirt was TRACKED, so E-05 would have refused it ~3h and ~$40 before the integration refusal the item was filed about. | `run-20260905T050043Z-639569` `state.json` `options.isolate_worktree = true`; dirty paths were `oc_runipd.py`, `agy_runipd.py`, both `git ls-files`-tracked |
| F-3 | HIGH | untracked gap is real | E-05 excludes untracked content by explicit reasoning, and the `aw install` incident was 130+ largely-untracked files, so the maintainer-observed case is the one E-05 will not catch. | `nna8yz` E-05 ("Untracked files are deliberately EXCLUDED ..."); item's `aw install` note |
| F-4 | HIGH | shared-tree gap is real | E-05 guards an "unattended ISOLATED turn"; `--no-isolate-worktree` shares the main tree and is unguarded. | `oc_runipd.py` registers `--no-isolate-worktree`; isolation defaults True (`isolate_worktree` option) |
| F-5 | MEDIUM | no consent surface | `--allow-dirty-base` does not exist anywhere at HEAD, so there is no sanctioned deliberate override. | `grep -rn "allow-dirty-base\|allow_dirty_base" agent_workflows/` returns nothing |
| F-6 | MEDIUM | flag/spec binding trap | Registering a new flag in `RUN_POLICY_FLAGS` without declaring it in spec 2.1 FAILS the suite, and vice versa; the two are atomic. Sibling `51vw4y` was blocked on exactly this. | `tests/test_run_flag_surface.py` reads the spec file in both directions; `51vw4y` OQ-04 |
| F-7 | LOW | trailers do not help | `a8eufb`'s `AW-Run:`/`AW-Item:` trailers mark COMMITS; the motivating pollution was UNCOMMITTED, so ownership cannot be inferred that way. Do not close this by pointing at `a8eufb`. | item's own correction note; trailers are commit metadata |

## Proposed changes (ordered, validatable)

1. Re-measure `nna8yz` E-05's shipped boundary and drop any case it already covers (E-01).
2. Report untracked dirt at run start with its integration consequence, without refusing (E-02).
3. Refuse a dirty base on the `--no-isolate-worktree` path, both hosts (E-03).
4. Add one `--allow-dirty-base` consent flag in the shared surface, respecting the spec binding (E-04).
5. Test all three cases on both hosts, proving pre-spawn refusal and an untouched tree (E-05).

## Deferred / out of scope (with reason)

- THE TRACKED + ISOLATED CASE: owned by `nna8yz` E-05 and explicitly NOT re-implemented here. Duplicating it would put two whole-tree dirty checks in the same two drivers, which is the duplication `cnwy8g` exists to stop.
- OWNERSHIP DETECTION (telling the runner's own dirt from a co-worker's): `a8eufb`. Necessary-but-insufficient here, since trailers mark commits and the motivating dirt was uncommitted. It would improve the MESSAGE, not the gate.
- RESOLVING DIRT (stash, reset, clean): forbidden by repository policy, not merely out of scope.
- THE INTEGRATION-TIME overlap check and its deferral ladder: `h1ksy6` and `51vw4y`. Different question (an incoming lane's changed set versus dirty paths) at a different time.

## Scope check

- Over-scope: none. Two shared modules, two drivers, two test files.
- Under-scope: this plan does NOT touch the tracked+isolated guard, does NOT add ownership detection, and does NOT amend a spec (see E-04's stop-and-report condition if the flag binding requires one).

## Required tests / validation

New `tests/test_dirty_base_gate.py` covering the three cases on both hosts, with refusal proven pre-spawn and the tree proven untouched. `tests/test_lane_clean_base.py` must stay green with an EMPTY diff. Plus the bare suite on a self-measured delta.

## Spec / documentation sync

NO `.spec.md` is declared in `- Scope-Paths:`, deliberately. If E-04's flag registration turns out to require a spec 2.1 amendment (F-6), that is a STOP-AND-REPORT condition, not a silent edit: the maintainer ruled on 2026-09-08 that a flag's spec declaration and its registration are atomic and belong to one plan, so this plan must either gain the spec path by amendment to its own scope or hand the flag off. Do not edit an undeclared spec file.

`--help` text for `--allow-dirty-base` must state what proceeding means: that lanes overlapping the dirty paths will be refused at integration. Write no em or en dashes in user-facing prose.

## Open questions

### OQ-01: Should the `--no-isolate-worktree` guard refuse on UNTRACKED dirt too, not only tracked?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: RAISED AT AUTHORING and left OPEN because it is a risk-appetite judgement, not a fact. `nna8yz` E-05's tracked-only rule is reasoned for a LANE (built from a commit, so untracked content was never silently omitted, and refusing on it would make an unattended run unstartable in any working checkout). A SHARED-TREE run is different in kind: the agent writes directly into the polluted tree, so untracked files are not merely present, they are in the blast radius. THE ARGUMENT FOR REFUSING: this is the `aw install` case, and it is precisely where the maintainer observed an agent failing to recognize its own pollution. THE ARGUMENT AGAINST: nearly every working checkout carries some untracked file, so refusing would make `--no-isolate-worktree` nearly unusable and would train operators to pass `--allow-dirty-base` reflexively, which destroys the flag's signal value. E-02 and E-03 are written so the plan is executable either way (untracked REPORTED, tracked REFUSED), and the answer only widens E-03. NOT BLOCKING: the shared-tree tracked case is unguarded today and closing it is a strict improvement regardless.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the located guard from `agent_workflows/lane_containment.py` BY SYMBOL, and state in prose: which porcelain helper it reuses, whether it distinguishes tracked from untracked, what it does on a `--no-isolate-worktree` run, and whether it has an override. Then state explicitly which of this plan's three cases remain open AFTER that reading. If any case turned out to be already covered, name it and confirm this plan's corresponding E-item was dropped rather than executed anyway.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a run start in a tree with UNTRACKED dirt showing the report, the named paths, AND the sentence stating the integration consequence. Paste the exit status proving the run STARTED (untracked is reported, not refused). Paste the code comment distinguishing this question from the integration-time overlap check, and confirm by symbol that you reused the existing porcelain helper rather than adding a third parser.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a `--no-isolate-worktree` run REFUSED on a dirty tracked base with the paths named, on BOTH hosts. THE LOAD-BEARING PROOF IS THAT IT PRECEDES THE SPAWN: patch the spawn and paste the assertion it was never called, or paste the raised error with the ordering shown. A refusal after a paid turn does not prevent the cost this item exists to prevent.
    Paste evidence the ISOLATED path's behavior did NOT change unless you deliberately changed it: `tests/test_lane_clean_base.py` green with `git diff --stat` EMPTY for that file. If you did alter the isolated path, quote the comment stating why and paste the test asserting the difference.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `--allow-dirty-base` in BOTH hosts' `--help` with its default, and show ONE default across both (the `--full-auto` divergence is the failure being prevented). Paste the frozen value from a real `state.json` `options` block. Paste `python3 -m pytest tests/test_run_flag_surface.py` PASSING and UNMODIFIED.
    STATE HOW YOU SATISFIED F-6: either the flag is declared in spec 2.1 in this same change (and say how you obtained authority over a path not in `- Scope-Paths:`), or you registered it outside the spec-governed table and can show the single shared declaration keeping the hosts aligned, or you STOPPED and reported. A modified, skipped, or xfailed `test_run_flag_surface.py` is a FAILED validation.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste all three cases passing on BOTH hosts, and paste each one FAILING against pre-change HEAD. Paste proof the working tree was untouched after every refusal: `git status --porcelain` byte-identical before and after, with no stash entry created (`git stash list` unchanged). Paste the bare `python3 -m pytest` summary line with a self-measured BEFORE baseline and the AFTER-minus-BEFORE failure set EMPTY.
    Note that inside a lane worktree the pre-change baseline includes ~14 `test_run_viewer.py` failures from the separate `agrlvw` defect (plan `utwr6y`); do not report those as this plan's.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). OQ-01 is open but `Blocking: no`.

THIS PLAN IS DEFINED BY WHAT `nna8yz` DID NOT DO, so E-01 is not a formality. If E-01's reading shows E-05 already covers a case claimed here, DROP that case and say so in the report; executing a duplicate guard because this plan's Concern predicted a gap that closed would be the exact waste the narrowing exists to prevent.

DEPENDS ON `nna8yz` HAVING EXECUTED (`- Item-Dependencies: executed:nna8yz`). The runner re-checks dependencies at dispatch, so an unmet edge marks this item `dependency-blocked` and continues rather than failing the run. Do not hand-run this plan against a tree where E-05 has not landed: its whole scope is the complement of E-05.

NO DIRT RESOLUTION. Report, refuse, leave un-owned state strictly alone. If a test seems to need a clean tree, build a fixture; do not clean the repository's.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT: run `aw runs` before starting, and re-locate every cited symbol before editing.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

On completion, close backlog `p8ni63` (this plan carries `- From-Backlog: p8ni63` and inherits its `Blocks-Release: next`). Note the item's file records which of its parts were dead on arrival; the close should not claim those were built.
