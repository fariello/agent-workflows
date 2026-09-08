# IPD: Preserve each plan Order in aw group the way aw rename already does

- Date: 2026-09-08
- Kind: child
- Concern: `aw group plans <id6> --set X --rename --apply` WITHOUT `--order` RENUMBERS EVERY NAMED PLAN FROM ZERO, so a `Kind: child` lands in the `00` filename slot the naming grammar reserves for an orchestrator. REPRODUCED DETERMINISTICALLY in a throwaway git repo (not inferred from the live tree): scaffold an orchestrator at Order 0 plus two children at Orders 1 and 2, then regroup ONE child with no `--order`, and `20260908-probeset-01-6sqcqe-probe-child-one.ipd.md` becomes `20260908-newset-00-6sqcqe-probe-child-one.ipd.md` carrying `- Order: 0`, exit 0, no warning.
  THE ROOT CAUSE IS ONE LINE AND ITS SENTINEL IS AMBIGUOUS. `plans_refs.run_set_assign` reads the flag and substitutes ZERO when absent: `start = getattr(args, "order", None)` then `start_order=start if start is not None else 0` (`plans_refs.py:432`, `:437`). `plan_set_assign` then assigns `order = start_order + i` per named plan (`:225`), so the first named plan always lands on 0 and the rest renumber from there. The signature default is `start_order: int = 0` (`:212`), which makes an ABSENT flag indistinguishable from a deliberate `--order 0`.
  THE SIBLING VERB ALREADY FIXED THIS EXACT BUG, WHICH IS THE STRONGEST EVIDENCE THAT THE FIX SHAPE IS RIGHT AND THAT THIS IS AN OVERSIGHT RATHER THAN A DESIGN CHOICE. `run_mv` (the `aw rename plans` backend) carries a comment in as many words: "Preserve the plan's existing Order unless `--order` is explicitly given (vf03z3: a bare rename must NOT clobber Order to 0)", and implements a three-tier fallback: the explicit flag, else the front-matter `- Order:`, else the current filename's `NN` (`plans_refs.py:467-475`). So the repository has already decided that a bare re-name must not clobber Order; `run_set_assign` simply never received the same treatment. That fix is even REGRESSION-TESTED for `rename` (`tests/test_awnaming_grammar_and_producers.py:312`, `PlansMvPreservesOrderAndDateTests`, docstring naming `vf03z3`) while `group` has no equivalent.
  IT WRITES A STATE THE REPO-WIDE SWEEP CANNOT SEE, which is why it stayed invisible. Measured on the probe: `aw ipd lint` reports `error IPD-M104: Order: child Order must be an integer >= 1`, while `aw check plans` in the SAME tree reports `errors 0 warnings 0`. So the tool commits a state only a per-file verb detects. That reachability gap is separately owned by `k9awrq` (`lintreach-01`, from `q0h9ls`), and this defect is a concrete instance of why it matters: a repair verb can commit a lint violation.
  IT FIRES ON THE REPAIR PATH, which is what makes it worse than a cosmetic renumber. `aw group ... --set <new>` is exactly the recovery the setid-collision refusal RECOMMENDS (spec `4w7d6s` I4, and the refusal message planned in `setidhard` Order 03 `dw7i3m`). So an operator following the tool's own advice corrupts Orders while fixing a collision. OBSERVED LIVE TWICE while graduating: regrouping four `setiduniq` plans to `setidhard` put ALL FOUR at Order `00` including three children, and authoring THIS plan reproduced it again on its own file. Both were recovered by re-running with explicit `--order`, so no bad state was committed.
- Scope: Make `aw group` preserve each plan's existing Order when `--order` is absent, using the SAME three-tier fallback `run_mv` already implements, and give `group` the regression test `rename` already has. EXCLUDES changing `run_mv` (it is correct), the lint-reachability gap (`k9awrq` owns it), and any refusal to place a child at Order 0 (recorded as a decision, not built).
- Scope-Paths: agent_workflows/plans_refs.py, tests/test_awnaming_grammar_and_producers.py
- Item-Dependencies: none
- Status: to-review
- Set: groupord
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: e3hzyc
- From-Backlog: s9p5x5
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `s9p5x5`. NOTHING IN THE ITEM IS OBSOLETE; the root cause is unchanged at `plans_refs.py:432`/`:437` with the ambiguous default at `:212`. THE ITEM'S ONE OPEN QUESTION IS NOW ANSWERED, and the answer supplies the fix: it asks "DOES `aw rename` SHARE THE DEFECT? It goes through the same rename machinery and was NOT tested here." It does NOT. `run_mv` preserves Order with an explicit three-tier fallback and a comment citing `vf03z3` ("a bare rename must NOT clobber Order to 0"), and carries a regression test (`PlansMvPreservesOrderAndDateTests`) that `group` lacks. So this plan is a PORT of a shipped fix rather than a new design, which is why it is narrow and why OQ-01 is resolved rather than blocking. AUTHORING NOTE, recorded because it is the defect's own third live occurrence: scaffolding this plan into `Set: grouporder` collided with the backlog item `s9p5x5` (setid reuse, the `sjsoqq` defect), and regrouping it to `groupord` required passing `--order 1` explicitly precisely to avoid the bug this plan fixes. The Set setid is therefore `groupord`, not `grouporder`.

## Goal

Make a repair verb stop corrupting the thing it is repairing, by giving `aw group` the Order-preservation `aw rename` has had since `vf03z3`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the defect before changing it

- [ ] E-01 REPRODUCE THE DEFECT AS A FAILING TEST FIRST, in a throwaway repo, so the fix is demonstrated rather than asserted. Build a Set with an orchestrator at Order 0 and two children at Orders 1 and 2, regroup ONE child with `--set <new> --rename --apply` and NO `--order`, then assert the child's `- Order:` and its filename `NN` slot are UNCHANGED. That assertion must FAIL at HEAD.
  MIRROR THE EXISTING FIXTURE RATHER THAN INVENTING ONE. `tests/test_awnaming_grammar_and_producers.py:312` (`PlansMvPreservesOrderAndDateTests`) already builds exactly this shape for `rename`: a `_RepoBackendCLIFixture` repo, a seeded plan carrying `- Order: 3` and `- Id: zzz111`, a git commit, then a CLI invocation. Reuse that fixture class and seed pattern so the two verbs' regressions sit side by side and a reader can compare them.
  ASSERT THE FILENAME AND THE FRONT MATTER SEPARATELY. The bug corrupts BOTH (`- Order: 0` and the `-00-` slot), and a test checking only one would pass against a half fix.
  - Depends on: none
  - Expected outcome: a test that fails at HEAD proving a bare `aw group` clobbers a child's Order in both the front matter and the filename slot.
  - Execution state: pending

### Task group 2: port the shipped fix

- [ ] E-02 GIVE `run_set_assign` THE SAME THREE-TIER ORDER FALLBACK `run_mv` USES, and do not invent a different one. The mechanism to copy is at `plans_refs.py:467-475`: explicit `--order` wins; else the front-matter `- Order:` via `_ORDER_LINE_RE`; else the current filename's `NN` via `_CLUSTERED_RE`; else 0.
  THE SENTINEL MUST BECOME DISTINGUISHABLE. Today `start_order: int = 0` (`:212`) cannot tell an absent flag from `--order 0`. Change the parameter to accept `None` meaning "preserve per plan" and keep `0` meaning "the caller really said zero". Do NOT keep the `start if start is not None else 0` collapse at the call site (`:437`); that line is the defect.
  MIND THAT `plan_set_assign` IS A MULTI-PLAN LOOP, which is the one real difference from `run_mv`. It assigns `order = start_order + i` across all named plans (`:225`), and that sequential renumber is a LEGITIMATE use when a caller explicitly passes `--order` to assemble a Set from scattered plans. So preserve the sequential behavior WHEN the flag is given, and switch to per-plan preservation only when it is absent. Do not delete the `+ i` arithmetic.
  DO NOT TOUCH `run_mv`. It is correct, it is regression-tested, and changing it would put an unrelated risk inside a bug fix.
  DO NOT CHANGE THE DATE HANDLING. `run_mv` preserves the date for the same `vf03z3` reason; whether `run_set_assign` shares THAT defect is a separate question (see Deferred), and bundling it would make this fix unreviewable.
  - Depends on: E-01
  - Expected outcome: an absent `--order` preserves each plan's own Order via the same three-tier fallback; an explicit `--order` still renumbers sequentially from it; `run_mv` untouched; the ambiguous sentinel gone.
  - Execution state: pending

- [ ] E-03 DECIDE AND RECORD WHETHER `aw group` SHOULD REFUSE A CHILD AT ORDER 0 AT ALL, rather than leaving it implicit. This is the item's third open question and it is genuinely separable from the preservation fix.
  THE PREDICATE ALREADY EXISTS AND IS NOT CONSULTED AT THE WRITE SITE. `aw ipd lint` knows the rule (`IPD-M104`: "child Order must be an integer >= 1"), so this is the same shape as `sjsoqq`'s setid-collision-at-creation gap: a rule that exists in the checker and not at the moment of writing.
  THE HONEST DEFAULT IS TO RECORD, NOT TO BUILD. Once E-02 lands, the ACCIDENTAL path to a child at Order 0 is closed, so a refusal would only catch an EXPLICIT `--order 0` on a child, which is a much rarer mistake. Adding a refusal also changes a verb's contract, and this plan's value is a narrow bug fix. So the deliverable here is a written decision plus, if the answer is yes, a follow-up item rather than an in-scope build.
  IF YOU DO BUILD IT, it must not break the legitimate case: an ORCHESTRATOR at Order 0 is correct and common, so the refusal is conditional on `- Kind: child`.
  - Depends on: E-02
  - Expected outcome: a recorded decision on the refusal with its reasoning; either a follow-up item filed or a conditional `Kind: child` refusal implemented, never a refusal that blocks an orchestrator.
  - Execution state: pending

### Task group 3: prove it, including the case the fix must not break

- [ ] E-04 PROVE BOTH DIRECTIONS AND THE MULTI-PLAN CASE, since a fix that only preserves would break Set assembly.
  FOUR ASSERTIONS MINIMUM: a bare regroup PRESERVES a child's Order in front matter and filename (E-01's test, now passing); an explicit `--order N` still renumbers sequentially across several named plans (`N`, `N+1`, `N+2`); a bare regroup of a plan whose front matter has NO `- Order:` falls back to the filename slot; and an ORCHESTRATOR at Order 0 regrouped bare stays at 0 rather than being "preserved" into something else.
  ASSERT THE MULTI-PLAN EXPLICIT CASE SEPARATELY, because it is the behavior most likely to be lost by a careless fix and the one legitimate reason the `+ i` arithmetic exists.
  ALSO ASSERT THE LINT VERDICT FLIPS. Run `aw ipd lint` on the regrouped child before and after: `IPD-M104` present at HEAD, absent after. That is the end-to-end proof the defect is gone, not merely that a field kept its value.
  - Depends on: E-03
  - Expected outcome: four assertions passing with the multi-plan explicit case standing alone, plus the `IPD-M104` before/after contrast.
  - Execution state: pending

- [ ] E-05 PROVE NOTHING ELSE MOVED, because `plans_refs` backs several verbs and this file is shared.
  ASSERT `aw rename`'s REGRESSION STILL PASSES: `PlansMvPreservesOrderAndDateTests` must be green, since both verbs now live in the same module and share `_ORDER_LINE_RE`/`_CLUSTERED_RE`.
  ASSERT THE OTHER `plans_refs` SURFACES ARE UNCHANGED. `run_set_assign` returns a `MutationResult` consumed by the noun-verb router, which places the self-commit offer ONCE at the dispatch site; a changed return shape would break that. Show the router's expectations still hold.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. Baseline measured on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py` case that asserts against sibling plans' live status. Inside a lane worktree roughly 32 further failures are environmental. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
  DO NOT REGROUP ANY REAL PLAN AS A TEST. Four agents are graduating concurrently and several Sets are approved or executing; a live regroup would rename artifacts other runs are reading. Fixtures only.
  - Depends on: E-04
  - Expected outcome: `rename`'s regression green, the `MutationResult` contract unchanged, bare-suite delta empty with counts stated, and no live plan regrouped.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE FIX ALREADY EXISTS FOR THE SIBLING VERB. `run_mv` (`plans_refs.py:467-475`) preserves Order with a three-tier fallback and a comment citing `vf03z3`: "a bare rename must NOT clobber Order to 0". Port it; do not design something new.
- AND IT IS REGRESSION-TESTED THERE. `tests/test_awnaming_grammar_and_producers.py:312` `PlansMvPreservesOrderAndDateTests` pins it for `rename`. `group` has no equivalent, which is the coverage asymmetry this plan closes.
- THE SENTINEL IS THE DEFECT. `start_order: int = 0` (`:212`) plus `start if start is not None else 0` (`:437`) makes an absent flag indistinguishable from `--order 0`.
- THE SEQUENTIAL RENUMBER IS LEGITIMATE WHEN EXPLICIT. `order = start_order + i` (`:225`) is how a Set is assembled from scattered plans; preserve it for the explicit case.
- `aw ipd lint` ALREADY KNOWS THE RULE (`IPD-M104`) and is not consulted at the write site, the same shape as `sjsoqq`'s creation-time setid gap.
- THE SWEEP CANNOT SEE THE RESULT: `aw ipd lint` errors on the corrupted child while `aw check plans` reports `errors 0` in the same tree. That gap is `k9awrq`'s subject, not this plan's.
- THE VERB IS THE RECOMMENDED REPAIR PATH for a setid collision (spec `4w7d6s` I4; `dw7i3m`'s planned refusal message), which is why the bug is worse than cosmetic.
- `run_set_assign` RETURNS A `MutationResult` and the noun-verb router places the self-commit offer ONCE at the dispatch site; do not change that shape.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | reproduced deterministically | In a throwaway repo, a child at Order 1 regrouped without `--order` became `...newset-00-6sqcqe-...` with `- Order: 0`, exit 0, no warning. | probe repo at HEAD |
| F-2 | HIGH | root cause is one line with an ambiguous sentinel | `start = getattr(args,"order",None)` then `start_order=start if start is not None else 0`; `plan_set_assign` does `order = start_order + i`; the signature default is `0`. | `plans_refs.py:432`, `:437`, `:225`, `:212` |
| F-3 | HIGH | **the sibling verb already fixed this exact bug** | `run_mv` preserves Order with a three-tier fallback and a comment citing `vf03z3` ("a bare rename must NOT clobber Order to 0"). So this is an oversight, not a design choice, and the fix is a PORT. | `plans_refs.py:467-475` |
| F-4 | HIGH | and the sibling has the test this verb lacks | `PlansMvPreservesOrderAndDateTests` pins Order/Date preservation for `rename`; nothing pins it for `group`. | `tests/test_awnaming_grammar_and_producers.py:312`, `:347` |
| F-5 | HIGH | it fires on the recommended repair path | `aw group ... --set <new>` is the recovery the setid-collision refusal prescribes, so following the tool's advice corrupts Orders while fixing a collision. | spec `4w7d6s` I4; `dw7i3m`'s refusal design |
| F-6 | MEDIUM | the corrupted state is invisible to the sweep | `aw ipd lint` -> `IPD-M104` error; `aw check plans` -> `errors 0` in the same tree. | both run on the probe |
| F-7 | MEDIUM | three live occurrences, all recovered | Four `setiduniq` plans all went to Order 00 (three of them children); authoring THIS plan reproduced it on its own file. Both recovered with explicit `--order`, nothing bad committed. | graduation session record |
| F-8 | MEDIUM | the multi-plan renumber must survive | `+ i` exists so an explicit `--order` can assemble a Set from scattered plans; a preserve-always fix would break that. | `plans_refs.py:225` |
| F-9 | LOW | the item's open question is answered | It asks whether `aw rename` shares the defect. It does not (F-3), which both closes the question and supplies the fix. | `plans_refs.py:467-475` |

## Proposed changes (ordered, validatable)

1. Reproduce the clobber as a failing test mirroring the `rename` fixture (E-01).
2. Port `run_mv`'s three-tier Order fallback into `run_set_assign` and remove the ambiguous sentinel, keeping the explicit sequential renumber (E-02).
3. Record a decision on refusing a `Kind: child` at Order 0, filing a follow-up rather than widening scope (E-03).
4. Prove preserve, explicit-sequential, filename-fallback and orchestrator cases, plus the `IPD-M104` flip (E-04).
5. Prove `rename`'s regression and the `MutationResult` contract are unchanged, with an empty suite delta (E-05).

## Deferred / out of scope (with reason)

- CHANGING `run_mv`. It is correct and regression-tested; this plan ports FROM it. Editing it would put unrelated risk inside a bug fix.
- THE DATE-PRESERVATION QUESTION. `run_mv` also preserves the `- Date:` for the same `vf03z3` reason, and whether `run_set_assign` shares that defect is a real question this plan does NOT answer, because bundling a second field's behavior would make the Order fix unreviewable. If E-01's fixture happens to show a date clobber, RECORD it as a finding and file it; do not fix it here.
- THE LINT-REACHABILITY GAP. `k9awrq` (`lintreach-01`, from `q0h9ls`) owns making `aw check` run the `IPD-*` family. This plan's F-6 is a concrete instance of why that matters, not a licence to fix it here.
- REFUSING A CHILD AT ORDER 0. E-03 records the decision; building it is conditional and probably a follow-up, because once E-02 lands the accidental path is closed and only an explicit `--order 0` remains.
- THE SETID-COLLISION-AT-CREATION GAP. `dw7i3m` (`setidhard` Order 03) owns it. This plan reproduced that defect too while authoring (its own Set collided with the backlog item), which is reported, not fixed here.
- SWEEPING OR FIXING ANY PLAN ALREADY CARRYING A BAD ORDER. None exists: both live occurrences were recovered with explicit `--order` and nothing bad was committed. If the executor FINDS one, report it rather than regrouping another agent's plan.
- `aw group` FOR NON-PLAN TYPES. The router dispatches `group` for several artifact types through their own backends; this plan fixes the PLANS backend, which is where the measured defect and the `run_mv` precedent both live. If another type's backend shares the shape, record it as a finding.

## Scope check

- Over-scope: none. One parameter's semantics, one call site, one test class.
- Scope-Paths justification: `agent_workflows/plans_refs.py` holds `plan_set_assign` (`:207`), its `start_order` default (`:212`), the `order = start_order + i` loop (`:225`), `run_set_assign`'s collapsing call site (`:432`, `:437`), and `run_mv`'s correct three-tier fallback (`:467-475`) that E-02 ports; `tests/test_awnaming_grammar_and_producers.py` holds `PlansMvPreservesOrderAndDateTests`, the fixture E-01 mirrors and the regression E-05 must keep green, so the two verbs' guarantees sit side by side.
- Under-scope, stated rather than left as `none`: this plan does not touch `run_mv`, does not address date preservation, does not fix the lint-reachability gap, does not build the child-at-Order-0 refusal, does not touch setid collision prevention, does not sweep any existing plan, and does not fix other types' `group` backends. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- THE FAILING-FIRST TEST (E-01) shown failing at HEAD and passing after, with both outputs pasted. A test only ever run against the fixed code proves nothing about the defect.
- FOUR CASES (E-04): bare-preserve, explicit-sequential across several plans, filename fallback when front matter lacks `- Order:`, and an orchestrator at Order 0 staying 0.
- THE `IPD-M104` BEFORE/AFTER on the regrouped child, pasted, as the end-to-end proof.
- `tests/test_awnaming_grammar_and_producers.py` re-run with ITS OWN summary line, showing `rename`'s regression still green.
- PROOF THE `MutationResult` SHAPE IS UNCHANGED, since the noun-verb router consumes it to place the self-commit offer once.
- NEGATIVE PROOF that no real plan was regrouped: `git status --porcelain .aw/records/plans/` showing no unexpected renames.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`plan_set_assign`'s DOCSTRING currently says only "Plan a Set (re)assignment for the given plans; with `rename` also plan clustering renames." It must state what an ABSENT `--order` now means (preserve per plan) versus an EXPLICIT one (renumber sequentially from it), because that distinction is the whole fix and the next reader will otherwise reintroduce the collapse.

ADD THE `vf03z3` CROSS-REFERENCE at the new fallback, the way `run_mv` already does. That comment is why the fix is a port rather than an invention, and a future reader who changes one verb should find the other immediately.

`aw group`'s `--help` for `--order` should say that omitting it PRESERVES each plan's Order, since today its absence silently means "renumber from zero" and nothing documents that. This is operator-facing prose: write no em or en dashes.

No spec change is expected. The naming grammar (`NN` with `00` reserved for an orchestrator) is defined by the uniform artifact-naming spec, which this plan HONORS rather than amends. If the executor finds spec text permitting a child at Order 0, that is a contradiction to report, not to edit here.

## Open questions

### OQ-01: Does `aw rename` share the defect?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, AND THAT IS THIS PLAN'S FIX. The backlog item raised this as untested ("It goes through the same rename machinery and was NOT tested here"). Measured: `run_mv` preserves Order with an explicit three-tier fallback (flag, front matter, filename slot) and carries a comment citing `vf03z3` that a bare rename "must NOT clobber Order to 0", plus a regression test (`PlansMvPreservesOrderAndDateTests`). So the two verbs DIVERGED: one received the fix and the other did not. That converts this plan from a design task into a port, which is why it is narrow, why the fix shape needs no debate, and why no blocking question remains.

### OQ-02: Should an absent `--order` preserve, or should a multi-plan call still renumber?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: PRESERVE WHEN ABSENT, RENUMBER WHEN EXPLICIT, which keeps both legitimate uses. The item left this open, offering a per-call-arity rule (single preserves, multi renumbers) as an alternative. That alternative is worse: arity is an accident of invocation, so `aw group a b --set X` would silently renumber while `aw group a --set X` preserved, which is a rule an operator cannot predict. Keying on the FLAG instead is predictable, matches `run_mv`'s already-shipped semantics, and preserves the sequential assembly case that `+ i` exists for. The cost is that assembling a Set now REQUIRES `--order`, which is the correct requirement: renumbering other plans is a deliberate act.

### OQ-03: Should `aw group` refuse to place a `Kind: child` at Order 0?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DELIBERATELY OPEN AND SUBORDINATE TO E-02, because the fix changes what the refusal would be worth. Today the ACCIDENTAL path is the whole problem: nobody types `--order 0` on a child, they simply omit the flag. Once E-02 preserves by default, a refusal would only catch an explicit `--order 0`, a much rarer mistake, while adding a new failure mode to a verb that is the recommended recovery for a setid collision (so a refusal there could block a repair). The counter-argument is real: `aw ipd lint` already knows the rule (`IPD-M104`) and not consulting it at the write site is the same gap `sjsoqq` documents for setids. E-03 therefore requires a recorded decision and permits filing a follow-up instead of building, and this stays non-blocking because the plan delivers its fix either way.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new test and its ACTUAL FAILING output at HEAD, before any fix. Quote the two assertions separately, showing one checks the front-matter `- Order:` and the other the filename `NN` slot. Confirm in one sentence that the fixture mirrors `PlansMvPreservesOrderAndDateTests` rather than inventing a new repo shape.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the changed `run_set_assign` and `plan_set_assign` signature, showing the sentinel now distinguishes absent from `--order 0`. Paste the three-tier fallback and confirm by inspection it matches `run_mv`'s at `plans_refs.py:467-475`, with the `vf03z3` cross-reference comment. Paste NEGATIVE proof that `run_mv` itself is byte-unchanged (`git diff` over that function) and that the `+ i` arithmetic still exists.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: state the recorded decision on refusing a child at Order 0 and its reasoning. If a follow-up item was filed, paste its id and summary. If a refusal was implemented instead, paste the test proving an ORCHESTRATOR at Order 0 is still permitted, since that is the case a careless refusal breaks.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the ACTUAL passing output of all four cases, QUOTING the explicit-sequential multi-plan assertion separately since it is the behavior a careless fix destroys. Paste the `aw ipd lint` output for the regrouped child BEFORE (showing `IPD-M104`) and AFTER (showing it absent), with unpiped exit codes.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `tests/test_awnaming_grammar_and_producers.py`'s OWN summary line showing `rename`'s regression green. Paste proof the `MutationResult` shape is unchanged and that the router's self-commit offer still fires once. Paste `git status --porcelain .aw/records/plans/` proving no real plan was regrouped. THEN paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION, deliberately: the one question the backlog item left open (does `aw rename` share the defect?) is answered NO by measurement, and that answer supplies the fix shape, so there is nothing for a maintainer to decide before execution. OQ-03 is genuinely open but subordinate, and E-03 permits recording a decision rather than building.

IT CARRIES `Blocks-Release: next`, inherited from the item under the all-bugs-block-release rule. The justification is not the cosmetic renumber: it is that the verb corrupts Orders on the RECOMMENDED REPAIR PATH for a setid collision, and that the resulting state is invisible to `aw check`.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Write the FAILING TEST FIRST and paste its failure; a fix demonstrated only against the fixed code is not demonstrated. Do NOT regroup, rename or edit any real plan as a test: four agents are graduating concurrently and several Sets are approved or executing, so use fixtures only. Do NOT touch `run_mv`. Re-locate every symbol by NAME rather than by the line numbers cited here. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook, since `pre-commit` can leave another agent's paths in the index.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the failing-then-passing contrast and the `IPD-M104` before/after.
