# IPD: Preserve each plan Order in aw group the way aw rename already does

- Date: 2026-09-08
- Kind: child
- Concern: `aw group plans <id6> --set X --rename --apply` WITHOUT `--order` RENUMBERS EVERY NAMED PLAN FROM ZERO, so a `Kind: child` lands in the `00` filename slot the naming grammar reserves for an orchestrator. RE-REPRODUCED INDEPENDENTLY AT REVIEW at HEAD `72a8f6ad` in a fresh throwaway git repo (not inferred from the live tree, and not taken on the author's word): scaffold an orchestrator at Order 0 plus two children at Orders 1 and 2, then regroup ONE child with no `--order`, and `20260908-probeset-01-bbb222-probe-child-one.ipd.md` becomes `20260908-newset-00-bbb222-probe-child-one.ipd.md` carrying `- Order: 0`, exit 0, no warning.
  THE ROOT CAUSE IS ONE LINE AND ITS SENTINEL IS AMBIGUOUS. `plans_refs.run_set_assign` reads the flag and substitutes ZERO when absent: `start = getattr(args, "order", None)` then `start_order=start if start is not None else 0` (`plans_refs.py:420`, `:425`). `plan_set_assign` then assigns `order = start_order + i` per named plan (`:226`), so the first named plan always lands on 0 and the rest renumber from there. The signature default is `start_order: int = 0` (`:213`), which makes an ABSENT flag indistinguishable from a deliberate `--order 0`.
  THE DEFECT IS WIDER THAN THE `--rename` PATH THE PLAN SCOPED, AND THIS IS THE MOST IMPORTANT REVIEW CORRECTION (F-11). Measured: `aw group plans bbb222 --set metaset --apply` with NO `--rename` ALSO writes `- Order: 0`, because `plan_set_assign` computes `order = start_order + i` ABOVE the branch and emits a `RenamePlan(src, src, id6, order=order)` for the metadata-only case (`:239-241`). The result is strictly WORSE than the rename case: the filename still reads `-01-` while the front matter reads `- Order: 0`, so the file CONTRADICTS ITS OWN NAME. Verified in that exact state, `aw check plans` exits 0, `aw check` exits 0, and `aw ipd lint` reports `IPD-M104` but NO name-mismatch code, so nothing in the toolchain names the divergence. A fix that only guards the `--rename` branch would leave the worse half of the bug in place.
  AND THE IDENTICAL DEFECTIVE LINE EXISTS IN A SIBLING BACKEND (F-12). `research_refs.run_set_assign` carries `start_order=start if start is not None else 0` (`research_refs.py:326`) against a planner whose default is also `start_order: int = 0` (`:164`) and which formats `order=f"{start_order + i:02d}"` (`:181`). That is the same bug in `aw group research`. It stays OUT of scope, but it must be NAMED rather than gestured at, because a reader who fixes only `plans_refs` will believe the class is closed.
  THE SIBLING VERB ALREADY FIXED THIS EXACT BUG, WHICH IS THE STRONGEST EVIDENCE THAT THE FIX SHAPE IS RIGHT AND THAT THIS IS AN OVERSIGHT RATHER THAN A DESIGN CHOICE. `run_mv` (the `aw rename plans` backend) carries a comment in as many words: "Preserve the plan's existing Order unless `--order` is explicitly given (vf03z3: a bare rename must NOT clobber Order to 0)", and implements a three-tier fallback: the explicit flag, else the front-matter `- Order:`, else the current filename's `NN` (`plans_refs.py:453-462`). So the repository has already decided that a bare re-name must not clobber Order; `run_set_assign` simply never received the same treatment. That fix is even REGRESSION-TESTED for `rename` (`tests/test_awnaming_grammar_and_producers.py:312`, `PlansMvPreservesOrderAndDateTests`, docstring naming `vf03z3`) while `group` has no equivalent.
  AND A SECOND, CLEANER PRECEDENT EXISTS THAT THE PLAN DID NOT FIND, WHICH SHOULD BE THE ONE COPIED (F-10). `artifact_rename.run_group_generic` -- the `group` backend for every NON-plan artifact type -- already has this right, and it got there by a better route than `run_mv`'s: it does `order_val = (start_order + i) if start_order is not None else None` (`:682`) and passes that `Optional[int]` down, so `compute_target_name` falls back to the filename's own `NN` (`:142`, `order_num = new_order if new_order is not None else int(m_uni.group("nn"))`) and the metadata writer skips the `- Order:` line entirely when the value is `None` (`:237`, `if order is not None and _ORDER_LINE_RE.search(text)`). That is the SAME defect class solved with an `Optional` threaded through instead of a three-tier lookup re-done at one call site, and it means the fix has two in-repo shapes to choose between rather than one. E-02 must pick deliberately and say why.
  IT WRITES A STATE THE REPO-WIDE SWEEP CANNOT SEE, which is why it stayed invisible. Measured on the probe: `aw ipd lint` reports `error IPD-M104: Order: child Order must be an integer >= 1`, while `aw check plans` in the SAME tree reports `errors 0 warnings 0`. So the tool commits a state only a per-file verb detects. That reachability gap is separately owned by `k9awrq` (`lintreach-01`, from `q0h9ls`), and this defect is a concrete instance of why it matters: a repair verb can commit a lint violation.
  IT FIRES ON THE REPAIR PATH, which is what makes it worse than a cosmetic renumber. `aw group ... --set <new>` is exactly the recovery the setid-collision refusal RECOMMENDS (spec `4w7d6s` I4, and the refusal message planned in `setidhard` Order 03 `dw7i3m`). So an operator following the tool's own advice corrupts Orders while fixing a collision. OBSERVED LIVE TWICE while graduating: regrouping four `setiduniq` plans to `setidhard` put ALL FOUR at Order `00` including three children, and authoring THIS plan reproduced it again on its own file. Both were recovered by re-running with explicit `--order`, so no bad state was committed.
- Scope: Make `aw group plans` preserve each plan's existing Order when `--order` is absent, on BOTH its branches (the `--rename` clustering path AND the metadata-only path, which is the worse of the two, F-11), reusing one of the two shapes already shipped in this repository, and give `group` the regression test `rename` already has. EXCLUDES changing `run_mv` (it is correct), `artifact_rename.run_group_generic` (already correct, and the preferred model to copy), `research_refs.run_set_assign` (the same defect, named in F-12 and deferred with its owner unassigned), the lint-reachability gap (`k9awrq` owns it), and any refusal to place a child at Order 0 (recorded as a decision, not built).
- Scope-Paths: agent_workflows/plans_refs.py, agent_workflows/cli.py, tests/test_awnaming_grammar_and_producers.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: groupord
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: e3hzyc
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: s9p5x5
- Blocks-Release: next

## Workflow history
- 2026-09-20 executed (opencode its_direct/pt3-claude-opus-5-1m-us): FIXED ON BOTH BRANCHES, WITH THE FAILING-FIRST CONTRAST MEASURED AGAINST PRISTINE HEAD SOURCE. `plan_set_assign`'s `start_order` became `Optional[int] = None`, `run_set_assign` now passes the flag THROUGH instead of collapsing absent to 0, and an absent flag resolves PER PLAN above the `rename` split via a new `_preserved_order` (front-matter `- Order:`, else the filename's `NN`, else 0). SHAPE CHOSEN DELIBERATELY AND IT IS A HYBRID, not the reviewer's Shape B alone: Shape B's single `Optional` threading (so both branches are correct by construction) with Shape A's resolution tiers, because Shape B's mechanism does not transfer here - it relies on a metadata writer that SKIPS the `- Order:` line when the value is `None`, while the plans path writes through `_set_metadata`, which takes `order: int`, INSERTS the line when absent, and is shared with `run_mv` (out of scope). ONE SITE THE PLAN DID NOT NAME also needed it, found by reading: `apply_renames`'s PREVIEW printed the loop index, so a dry run advertised a renumber the apply no longer performs.
  EVIDENCE. Seven test cases in `PlansGroupPreservesOrderTests`, beside `rename`'s own regression in the same file. Against a `git archive HEAD` extraction carrying ONLY the new test file, FOUR fail and THREE pass (`4 failed, 3 passed`), so the four are real regressions for the defect and the three (orchestrator-at-zero, explicit-sequential, explicit `--order 0`) are must-not-break guards; all seven pass here. Bare suite BEFORE `1 failed, 7230 passed, 3 skipped, 2 xfailed`, AFTER `1 failed, 7237 passed, 3 skipped, 2 xfailed`: same single failure both times, so the delta is EMPTY and the +7 is exactly the new cases. THAT PRE-EXISTING FAILURE IS NOT THE ONE THE PLAN PREDICTED and the plan's note is stale, not wrong: `test_reporting_contract` passes here (no `opencode-recovery/` files in this lane) and the failure is `test_turn_bounds.py::...::test_the_permission_policy_by_contrast_IS_isolation_scoped`, which `env -u OPENCODE_CONFIG_CONTENT` makes pass, so it is this harness turn's own environment and not the code.
  A VALIDATION DEFECT HAD TO BE WORKED AROUND AND IS FILED (`ccbe60`, bug, release-gating): the editable install names an ABSOLUTE path to the MAIN checkout, so a `-m agent_workflows` subprocess from a lane imports the MAIN tree. Measured directly - the new CLI tests still failed after the fix was written here, because the CLI they invoked was the main checkout's unfixed module. The symmetric hazard is worse: a test can PASS while the tree under test is unfixed, which means any lane-isolated plan validated only through a subprocess CLI assertion may have been validated against the wrong source. This plan's test class pins `PYTHONPATH` to its own tree; the repo-wide fix is out of fence.
  DEFERRED WORK FILED WITH ITS MEASUREMENTS, not mentioned: `4y4xo5` (F-12, the byte-identical defect in `research_refs`, plus the `aw research set-assign --order` help string that documents it verbatim) and `j84jg3` (F-13, the `20260101` date fallback), both `bug` + `Blocks-Release: next`; `r30nnz` records the E-03 decision NOT to build the child-at-Order-0 refusal. Every Deferred row now carries a typed `- Carrier:` or an explicit `- Carrier-Declined:`, which surfaced one stale authored reference: `dw7i3m` is superseded because spec `2lcqno` REVERSED the setid-collision-prevention design, so that row's premise is dead and is declined rather than re-pointed.
  UNTOUCHED AS REQUIRED, with negative proof: `research_refs.py` and `artifact_rename.py` both have empty `git diff --stat`, no shared helper was extracted (no `research` token appears in the `plans_refs.py` diff at all), `run_mv` and `_set_metadata` are unchanged, the `+ i` arithmetic survives, the `MutationResult` shape is untouched (no `+/-` line mentions it; `test_selfcommit_adoption.py` 25 passed), and no real plan was regrouped (every case uses a tempfile fixture). `aw sanitize --agent` clean. begin/finalize were NOT run: `aw ipd begin` refused with `AW-LIFECYCLE-ROLE-001` because the runner owns the transition for a managed lane.
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-09 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-001..PR-007, ALL SEVEN FIXED, no open findings. `aw ipd lint --phase author` CONFORMING before semantic review and `--phase review-finalize` CONFORMING after every revision, so nothing here is structural. DISCLOSURE: same agent/model authored this plan, so this is a SELF-REVIEW, and its value rests on RE-RUNNING rather than re-reading: a fresh probe repo was built and SEVEN behaviors were executed against the real CLI (bare rename-regroup, bare metadata-only regroup, multi-plan explicit `--order`, date preservation with a divergent front-matter date, date fallback with no `- Date:` line, the same case through `rename` for contrast, and `aw ipd lint` versus `aw check` on the corrupted result).
  THE TWO FINDINGS THAT CHANGE WHAT GETS BUILT. (1) THE DEFECT ALSO FIRES WITH NO `--rename`, AND THAT CASE IS WORSE (PR-002, F-11). Measured: `aw group plans <id6> --set X --apply` writes `- Order: 0` while the filename keeps `-01-`, so the file CONTRADICTS ITS OWN NAME, and in that state `aw check plans`, bare `aw check`, and lint's name rules all report nothing. The cause is that `order = start_order + i` sits ABOVE the `if rename:` split and flows into the metadata-only `RenamePlan(src, src, id6, order=order)`. The authored Concern, Scope, E-01, E-02 and every test case named only the `--rename` path, so a conforming execution could have fixed the visible half and shipped the invisible one. (2) A SECOND AND BETTER PRECEDENT EXISTS THAT THE PLAN DID NOT FIND (PR-003, F-10): `artifact_rename.run_group_generic`, the `group` backend for every non-plan type, threads an `Optional[int]` (`order_val = (start_order + i) if start_order is not None else None`) so the name computer falls back to the filename's `NN` and the metadata writer OMITS the `- Order:` line when the value is `None`. That fixes both branches by construction where the `run_mv` three-tier port fixes one, so the plan's "the fix is a PORT" was true of the wrong shape. E-02 now presents both and requires a recorded choice.
  ALSO FIXED. The spec-sync section MANDATED a `--help` rewrite while `cli.py` was undeclared in `Scope-Paths`, so an executor doing as instructed would have gone out of fence (PR-005); `cli.py` is now declared, and the section distinguishes the shared `rename`/`group` string (`:3118`, in scope) from `aw research set-assign`'s own (`:2246`, deferred). The deferred date question is ANSWERABLE and the answer is that `group` DOES share a date defect (PR-004, F-13): it derives the name date from `_plan_date(text)` alone whose no-match fallback is the literal `20260101`, so a plan with no `- Date:` line is renamed to `20260101-...` where `rename` preserves `20260908-...`; measured, and now a filing obligation rather than a maybe. The identical defective line exists in `research_refs.run_set_assign` (PR-004, F-12), which the Deferred section had only gestured at; it is named, deferred, and a shared-helper refactor is explicitly forbidden. Every `plans_refs.py` citation was off by five to twelve lines (PR-001, F-14) and the baseline named the wrong failing test (PR-006, F-15: claimed `1 failed, 5648 passed` in `test_orchestrator_retirement`; measured `1 failed, 5919 passed, 3 skipped, 2 xfailed` in `test_reporting_contract`, environmental from 189 untracked files belonging to another party). Two test cases were missing: the metadata-only preserve and an explicit `--order 0` proving the new sentinel does not make zero unreachable (PR-007), so E-04 is now six cases; and the `IPD-M104` assertion needed narrowing to the CODE rather than a clean lint exit, which a probe file can never produce.
  CONFIRMED SOUND, AND THE DIAGNOSIS IS EXEMPLARY. Every authored claim that was re-run held: the clobber reproduces exactly as described, the root cause is that one line with that ambiguous sentinel, `run_mv` really has the fix with the `vf03z3` comment, `PlansMvPreservesOrderAndDateTests` really pins it for `rename` and nothing pins it for `group`, the sweep really cannot see the result (`aw ipd lint` exits 1 on `IPD-M104` while `aw check` exits 0 in the same tree), and the multi-plan explicit renumber really is a working feature that a preserve-always fix would break. The judgement that this is an oversight rather than a design choice is correct and is now supported by two independent precedents instead of one.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `s9p5x5`. NOTHING IN THE ITEM IS OBSOLETE; the root cause is unchanged at `plans_refs.py:432`/`:437` with the ambiguous default at `:212`. THE ITEM'S ONE OPEN QUESTION IS NOW ANSWERED, and the answer supplies the fix: it asks "DOES `aw rename` SHARE THE DEFECT? It goes through the same rename machinery and was NOT tested here." It does NOT. `run_mv` preserves Order with an explicit three-tier fallback and a comment citing `vf03z3` ("a bare rename must NOT clobber Order to 0"), and carries a regression test (`PlansMvPreservesOrderAndDateTests`) that `group` lacks. So this plan is a PORT of a shipped fix rather than a new design, which is why it is narrow and why OQ-01 is resolved rather than blocking. AUTHORING NOTE, recorded because it is the defect's own third live occurrence: scaffolding this plan into `Set: grouporder` collided with the backlog item `s9p5x5` (setid reuse, the `sjsoqq` defect), and regrouping it to `groupord` required passing `--order 1` explicitly precisely to avoid the bug this plan fixes. The Set setid is therefore `groupord`, not `grouporder`.

## Goal

Make a repair verb stop corrupting the thing it is repairing, by giving `aw group` the Order-preservation `aw rename` has had since `vf03z3`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the defect before changing it

- [x] E-01 REPRODUCE THE DEFECT AS A FAILING TEST FIRST, in a throwaway repo, so the fix is demonstrated rather than asserted. Build a Set with an orchestrator at Order 0 and two children at Orders 1 and 2, regroup ONE child with `--set <new> --rename --apply` and NO `--order`, then assert the child's `- Order:` and its filename `NN` slot are UNCHANGED. That assertion must FAIL at HEAD.
  COVER THE METADATA-ONLY PATH IN THE SAME ITEM, because it is a SECOND failing case and the worse one (F-11). Regroup a child with `--set <new> --apply` and NO `--rename`: measured at review, the front matter becomes `- Order: 0` while the filename keeps `-01-`, so the file contradicts its own name. Both failing assertions belong here, so the fix in E-02 cannot pass one branch and silently leave the other.
  MIRROR THE EXISTING FIXTURE RATHER THAN INVENTING ONE. `tests/test_awnaming_grammar_and_producers.py:312` (`PlansMvPreservesOrderAndDateTests`) already builds exactly this shape for `rename`: a `_RepoBackendCLIFixture` repo, a seeded plan carrying `- Order: 3` and `- Id: zzz111`, a git commit, then a CLI invocation. Reuse that fixture class and seed pattern so the two verbs' regressions sit side by side and a reader can compare them.
  ASSERT THE FILENAME AND THE FRONT MATTER SEPARATELY. The bug corrupts BOTH in the rename case (`- Order: 0` and the `-00-` slot) and DIVERGES them in the metadata-only case, so a test checking only one would pass against a half fix and would miss the divergence entirely.
  - Depends on: none
  - Expected outcome: TWO tests failing at HEAD, one per `group` branch: a bare `--rename` regroup clobbering a child's Order in both the front matter and the filename slot, and a bare metadata-only regroup clobbering the front matter while leaving the filename, proving the divergence.
  - Execution state: performed

### Task group 2: port the shipped fix

- [x] E-02 MAKE AN ABSENT `--order` PRESERVE EACH PLAN'S OWN ORDER, ON BOTH BRANCHES, REUSING ONE OF THE TWO SHAPES ALREADY SHIPPED HERE, AND SAY WHICH AND WHY. There are two in-repo precedents, not one, and the plan originally knew only the weaker:
  SHAPE A, `run_mv`'s THREE-TIER LOOKUP (`plans_refs.py:453-462`): explicit `--order` wins; else the front-matter `- Order:` via `_ORDER_LINE_RE`; else the current filename's `NN` via `_CLUSTERED_RE`; else 0. Local to one call site, easy to port, and already regression-tested in this file.
  SHAPE B, `artifact_rename.run_group_generic`'s THREADED `Optional[int]` (`:682`, `:142`, `:237`): compute `order_val = (start_order + i) if start_order is not None else None` and pass the `Optional` down, so the name computer falls back to the filename's own `NN` and the metadata writer SKIPS the `- Order:` line entirely when the value is `None`. This is the better fit for THIS defect, because it fixes both branches by construction (a `None` order writes no `- Order:` line at all, so the metadata-only path cannot diverge from the filename) and because it is the shape every non-plan `group` backend already uses. THE REVIEWER'S READING IS THAT SHAPE B IS RIGHT, but the choice is the executor's; make it deliberately and record the reason, because copying Shape A risks fixing only the rename branch.
  BOTH BRANCHES OF `plan_set_assign` MUST BE COVERED. `order = start_order + i` is computed ABOVE the `if rename:` split (`:226`) and flows into BOTH the clustering `RenamePlan` and the metadata-only `RenamePlan(src, src, id6, order=order)` (`:239-241`). Measured at review, the metadata-only path is the one that produces a file contradicting its own name, so a fix that guards only the rename branch leaves the worse half live.
  THE SENTINEL MUST BECOME DISTINGUISHABLE. Today `start_order: int = 0` (`:213`) cannot tell an absent flag from `--order 0`. Change the parameter to accept `None` meaning "preserve per plan" and keep `0` meaning "the caller really said zero". Do NOT keep the `start if start is not None else 0` collapse at the call site (`:425`); that line is the defect.
  MIND THAT `plan_set_assign` IS A MULTI-PLAN LOOP, which is the one real difference from `run_mv`. It assigns `order = start_order + i` across all named plans, and that sequential renumber is a LEGITIMATE use when a caller explicitly passes `--order` to assemble a Set from scattered plans: verified at review, `aw group plans bbb222 ccc333 --set asmset --order 1 --rename --apply` correctly produces `-01-`/`- Order: 1` and `-02-`/`- Order: 2`. So preserve the sequential behavior WHEN the flag is given, and switch to per-plan preservation only when it is absent. Do not delete the `+ i` arithmetic.
  DO NOT TOUCH `run_mv` OR `run_group_generic`. Both are correct and one is the model; changing either would put unrelated risk inside a bug fix.
  DO NOT CHANGE THE DATE HANDLING, even though review has now MEASURED that `group` does share a date defect (F-13: it uses `_plan_date(text)` alone, so a plan with no `- Date:` line is renamed to the literal `20260101` fallback, where `rename` would have preserved the filename's date). That is a real second bug with its own evidence, recorded in Deferred with a follow-up obligation, and bundling it would make the Order fix unreviewable.
  - Depends on: E-01
  - Expected outcome: an absent `--order` preserves each plan's own Order on BOTH branches; the chosen shape named with its reason; an explicit `--order` still renumbers sequentially from it; `run_mv` and `run_group_generic` untouched; the ambiguous sentinel gone.
  - Execution state: performed

- [x] E-03 DECIDE AND RECORD WHETHER `aw group` SHOULD REFUSE A CHILD AT ORDER 0 AT ALL, rather than leaving it implicit. This is the item's third open question and it is genuinely separable from the preservation fix.
  THE PREDICATE ALREADY EXISTS AND IS NOT CONSULTED AT THE WRITE SITE. `aw ipd lint` knows the rule (`IPD-M104`: "child Order must be an integer >= 1"), so this is the same shape as `sjsoqq`'s setid-collision-at-creation gap: a rule that exists in the checker and not at the moment of writing.
  THE HONEST DEFAULT IS TO RECORD, NOT TO BUILD. Once E-02 lands, the ACCIDENTAL path to a child at Order 0 is closed, so a refusal would only catch an EXPLICIT `--order 0` on a child, which is a much rarer mistake. Adding a refusal also changes a verb's contract, and this plan's value is a narrow bug fix. So the deliverable here is a written decision plus, if the answer is yes, a follow-up item rather than an in-scope build.
  IF YOU DO BUILD IT, it must not break the legitimate case: an ORCHESTRATOR at Order 0 is correct and common, so the refusal is conditional on `- Kind: child`.
  - Depends on: E-02
  - Expected outcome: a recorded decision on the refusal with its reasoning; either a follow-up item filed or a conditional `Kind: child` refusal implemented, never a refusal that blocks an orchestrator.
  - Execution state: performed

### Task group 3: prove it, including the case the fix must not break

- [x] E-04 PROVE BOTH DIRECTIONS, BOTH BRANCHES, AND THE MULTI-PLAN CASE, since a fix that only preserves would break Set assembly and a fix that only guards `--rename` would leave the worse half live.
  SIX ASSERTIONS MINIMUM: (a) a bare `--rename` regroup PRESERVES a child's Order in front matter AND filename (E-01's first test, now passing); (b) a bare METADATA-ONLY regroup preserves the front-matter Order and leaves the filename alone, so the two AGREE (E-01's second test, now passing) -- this is the assertion the plan originally lacked entirely; (c) an explicit `--order N` still renumbers sequentially across several named plans (`N`, `N+1`, `N+2`), which review verified works today and must keep working; (d) a bare regroup of a plan whose front matter has NO `- Order:` falls back to the filename slot; (e) an ORCHESTRATOR at Order 0 regrouped bare stays at 0 rather than being "preserved" into something else; (f) an explicit `--order 0` on a single plan still lands at 0, proving the new sentinel really distinguishes absent from zero rather than making zero unreachable.
  ASSERT (c) AND (f) SEPARATELY FROM THE REST. (c) is the behavior most likely to be lost by a careless fix and the one legitimate reason the `+ i` arithmetic exists; (f) is the direct test of the sentinel change and the one an executor is likeliest to skip, since it looks like a no-op.
  ALSO ASSERT THE LINT VERDICT FLIPS. Run `aw ipd lint` on the regrouped child before and after: `IPD-M104` present at HEAD (confirmed at review: `! IPD-M104: Order: child Order must be an integer >= 1`, exit 1), absent after. That is the end-to-end proof the defect is gone, not merely that a field kept its value. Note the probe file will also emit unrelated `IPD-H2xx` structural codes; assert on the ABSENCE OF `IPD-M104` specifically, not on a clean exit, or the assertion will never pass.
  - Depends on: E-03
  - Expected outcome: six assertions passing with the multi-plan explicit case and the explicit-zero case each standing alone, plus the `IPD-M104`-specific before/after contrast.
  - Execution state: performed

- [x] E-05 PROVE NOTHING ELSE MOVED, because `plans_refs` backs several verbs and this file is shared.
  ASSERT `aw rename`'s REGRESSION STILL PASSES: `PlansMvPreservesOrderAndDateTests` must be green, since both verbs live in the same module and share `_ORDER_LINE_RE`/`_CLUSTERED_RE`.
  ASSERT THE OTHER `plans_refs` SURFACES ARE UNCHANGED. `run_set_assign` returns a `MutationResult` consumed by the noun-verb router, which places the self-commit offer ONCE at the dispatch site (`cli.py:8642`, and `MutationResult`'s own docstring at `plans_refs.py:136-148` records the reason: "never inside a shared backend, or `aw group research` would double-fire"). A changed return shape would break that. Show the router's expectations still hold.
  DO NOT LET THE FIX LEAK INTO `research_refs`. That module has its own byte-identical defective line (F-12) and its own `plan_set_assign`; it is OUT of scope. If the executor is tempted to extract a shared helper, STOP: that is a refactor across two backends inside a bug fix, and it would drag `aw group research`'s behavior change into a plan whose fence is `plans_refs.py`. File it instead.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. Do NOT add flags: `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Baseline RE-MEASURED at review on `72a8f6ad`: `1 failed, 5919 passed, 3 skipped, 2 xfailed`, the single failure being `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, caused by 189 untracked `opencode-recovery/*.md` files belonging to another party in this shared checkout. It is ENVIRONMENTAL, it is NOT the `tests/test_orchestrator_retirement.py` case the plan originally named, and it must not be fixed. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
  DO NOT REGROUP ANY REAL PLAN AS A TEST. Measured at review, 104 plans are pending (18 `approved`, 25 `reviewed`, 61 `to-review`) and 45 run directories hold a `driver.lock`; a live regroup would rename artifacts other runs are reading. Fixtures only.
  - Depends on: E-04
  - Expected outcome: `rename`'s regression green, the `MutationResult` contract unchanged, `research_refs` untouched, bare-suite delta empty with counts stated, and no live plan regrouped.
  - Execution state: performed

## Project conventions discovered (Step 0)

All line numbers below were RE-MEASURED AT REVIEW at HEAD `72a8f6ad`; the authored plan's `plans_refs.py` citations were each off by five to twelve lines. Locate by SYMBOL.

- TWO CORRECT SHAPES ALREADY SHIP IN THIS REPOSITORY, and the plan knew only the weaker one. `run_mv` (`plans_refs.py:453-462`) does a three-tier lookup at one call site with a comment citing `vf03z3` ("a bare rename must NOT clobber Order to 0"). `artifact_rename.run_group_generic` (`:682`) instead threads an `Optional[int]` (`order_val = (start_order + i) if start_order is not None else None`) so that `compute_target_name` falls back to the filename's `NN` (`:142`) and the metadata writer omits the `- Order:` line entirely when the value is `None` (`:237`). The second is the shape every NON-plan `group` backend already uses and it fixes both branches by construction. Choose deliberately; do not invent a third.
- AND ONE IS REGRESSION-TESTED. `tests/test_awnaming_grammar_and_producers.py:312` `PlansMvPreservesOrderAndDateTests` pins Order and Date for `rename`. `group` has no equivalent, which is the coverage asymmetry this plan closes.
- THE DEFECT SPANS BOTH `group` BRANCHES, NOT JUST `--rename`. `order = start_order + i` is computed ABOVE the `if rename:` split (`:226`) and flows into the metadata-only `RenamePlan(src, src, id6, order=order)` too (`:239-241`). Measured: a metadata-only regroup writes `- Order: 0` while leaving the filename at `-01-`, so the file contradicts its own name, and nothing in the toolchain reports that divergence.
- THE SENTINEL IS THE DEFECT. `start_order: int = 0` (`:213`) plus `start if start is not None else 0` (`:425`) makes an absent flag indistinguishable from `--order 0`.
- THE SEQUENTIAL RENUMBER IS LEGITIMATE WHEN EXPLICIT AND VERIFIED WORKING. `order = start_order + i` (`:226`) is how a Set is assembled from scattered plans; measured at review, `--order 1` across two plans correctly yields `-01-`/`- Order: 1` and `-02-`/`- Order: 2`. Preserve it for the explicit case.
- `aw ipd lint` ALREADY KNOWS THE RULE (`IPD-M104`: "child Order must be an integer >= 1") and is not consulted at the write site, the same shape as `sjsoqq`'s creation-time setid gap. When asserting on it, match the CODE, not a clean exit: a probe file also emits unrelated `IPD-H2xx` structural codes.
- THE SWEEP CANNOT SEE THE RESULT, CONFIRMED BY RUNNING BOTH. On the corrupted probe, `aw ipd lint` exits 1 reporting `IPD-M104` while `aw check plans` AND bare `aw check` both exit 0. That gap is `k9awrq`'s subject, not this plan's.
- THE VERB IS THE RECOMMENDED REPAIR PATH for a setid collision (spec `4w7d6s` I4; `dw7i3m`'s planned refusal message), which is why the bug is worse than cosmetic.
- `group` ALSO DIVERGES FROM `rename` ON THE DATE, WHICH IS A SECOND REAL BUG. `plan_set_assign` derives the name date from `_plan_date(text)` alone (`:230`), whose no-match fallback is the literal `"20260101"` (`:113-118`); `run_mv` prefers the FILENAME's date and only then the front matter (`:466`). Measured: a plan with no `- Date:` line is renamed by `group` to `20260101-...` while `rename` preserves `20260908-...`. Out of scope here (see Deferred), but no longer an open question.
- `research_refs.run_set_assign` CARRIES THE BYTE-IDENTICAL DEFECTIVE LINE (`research_refs.py:326`, planner default `:164`, formatting `:181`). Out of scope; do NOT extract a shared helper to fix both, which would drag a second verb's behavior change into this fence.
- `run_set_assign` RETURNS A `MutationResult` and the noun-verb router places the self-commit offer ONCE at the dispatch site (`cli.py:8642`); the docstring at `plans_refs.py:136-148` records why ("never inside a shared backend, or `aw group research` would double-fire"). Do not change that shape.
- `--order`'s HELP TEXT IS SHARED ACROSS `rename` AND `group` in the noun-verb parser (`cli.py:3118`, "Order NN (rename/group)."), so any wording change lands on both verbs at once. The separate `aw research set-assign` parser has its own string (`:2246`, "Starting NN (default 0).") which is the one that literally documents the buggy default; it belongs to the deferred `research_refs` item, not here.
- Shared checkout, concurrent edits (104 pending plans, 45 `driver.lock` run dirs), suite runs BARE. Baseline at review: `1 failed, 5919 passed, 3 skipped, 2 xfailed`, the failure being the environmental `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` from 189 untracked `opencode-recovery/*.md` files belonging to another party. Re-locate every symbol by name.

## Findings

F-1..F-9 were authored 2026-09-08. F-10..F-15 were added at review at HEAD `72a8f6ad`, where every authored claim was RE-RUN in a fresh probe repo rather than re-read.

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | reproduced deterministically, TWICE INDEPENDENTLY | In a fresh throwaway repo at review, a child at Order 1 regrouped without `--order` became `20260908-newset-00-bbb222-probe-child-one.ipd.md` with `- Order: 0`, exit 0, no warning. CONFIRMED. | probe repo built and run at review |
| F-2 | HIGH | root cause is one line with an ambiguous sentinel | `start = getattr(args,"order",None)` then `start_order=start if start is not None else 0`; `plan_set_assign` does `order = start_order + i`; the signature default is `0`. CONFIRMED, citations corrected. | `plans_refs.py:420`, `:425`, `:226`, `:213` |
| F-3 | HIGH | **the sibling verb already fixed this exact bug** | `run_mv` preserves Order with a three-tier fallback and a comment citing `vf03z3` ("a bare rename must NOT clobber Order to 0"). So this is an oversight, not a design choice. CONFIRMED; but see F-10, which finds a SECOND and better precedent. | `plans_refs.py:453-462` |
| F-4 | HIGH | and the sibling has the test this verb lacks | `PlansMvPreservesOrderAndDateTests` pins Order/Date preservation for `rename`; nothing pins it for `group`. CONFIRMED, including the seeded `- Order: 3` / `- Id: zzz111` fixture shape. | `tests/test_awnaming_grammar_and_producers.py:312`, `:347` |
| F-5 | HIGH | it fires on the recommended repair path | `aw group ... --set <new>` is the recovery the setid-collision refusal prescribes, so following the tool's advice corrupts Orders while fixing a collision. | spec `4w7d6s` I4; `dw7i3m`'s refusal design |
| F-6 | MEDIUM | the corrupted state is invisible to the sweep | `aw ipd lint` exits 1 with `IPD-M104`; `aw check plans` AND bare `aw check` both exit 0 in the same tree. CONFIRMED by running all three on the probe. | probe at review |
| F-7 | MEDIUM | three live occurrences, all recovered | Four `setiduniq` plans all went to Order 00 (three of them children); authoring THIS plan reproduced it on its own file. All recovered with explicit `--order`, nothing bad committed. | graduation session record |
| F-8 | MEDIUM | the multi-plan renumber must survive, AND IT WORKS TODAY | `+ i` exists so an explicit `--order` can assemble a Set from scattered plans. VERIFIED at review: `aw group plans bbb222 ccc333 --set asmset --order 1 --rename --apply` yields `-01-`/`- Order: 1` and `-02-`/`- Order: 2`. A preserve-always fix would break this. | probe at review |
| F-9 | LOW | the item's open question is answered | It asks whether `aw rename` shares the defect. It does not (F-3), which both closes the question and supplies a fix shape. | `plans_refs.py:453-462` |
| F-10 | MEDIUM | **a SECOND and better precedent exists that the plan did not find** | `artifact_rename.run_group_generic` -- the `group` backend for every non-plan artifact type -- already solves this by threading an `Optional[int]`: `order_val = (start_order + i) if start_order is not None else None` (`:682`), so `compute_target_name` falls back to the filename's `NN` (`:142`) and the metadata writer SKIPS the `- Order:` line when the value is `None` (`:237`). That shape fixes BOTH `group` branches by construction, which the three-tier port does not, and it is what every sibling `group` backend already uses. The plan asserted "the fix is a PORT" of one shape; there are two, and the unfound one is the better fit. | read all three call paths |
| F-11 | HIGH | **the defect ALSO fires with NO `--rename`, and that case is WORSE** | Measured: `aw group plans bbb222 --set metaset --apply` (no `--rename`) writes `- Order: 0` while the filename stays `20260908-probeset-01-bbb222-...`, so the file CONTRADICTS ITS OWN NAME. The cause is that `order = start_order + i` sits ABOVE the `if rename:` split and flows into the metadata-only `RenamePlan(src, src, id6, order=order)` (`:226`, `:239-241`). In that state `aw check plans`, `aw check`, and lint's NAME rules all report nothing (only `IPD-M104` fires, on the Order value itself). The plan's Concern, Scope, E-01, E-02 and every test case named only the `--rename` path, so a conforming execution could have fixed the visible half and shipped the invisible one. | probe at review; both `RenamePlan` construction sites read |
| F-12 | MEDIUM | **the byte-identical defective line exists in `research_refs`** | `research_refs.run_set_assign` has `start_order=start if start is not None else 0` (`:326`) against a planner defaulting `start_order: int = 0` (`:164`) and formatting `order=f"{start_order + i:02d}"` (`:181`). So `aw group research` has the same bug. The plan's Deferred section said only "if another type's backend shares the shape, record it as a finding" without measuring; it does, and now it is named with an owner obligation. Also note `aw research set-assign`'s own `--order` help literally documents the buggy behavior ("Starting NN (default 0).", `cli.py:2246`). | read both call paths |
| F-13 | MEDIUM | **the deferred date question is ANSWERABLE and the answer is yes, `group` shares a date defect** | `plan_set_assign` derives the name date from `_plan_date(text)` alone (`:230`), whose no-match fallback is the literal `"20260101"` (`:113-118`); `run_mv` prefers the FILENAME's date, then the front matter (`:466`). Measured: a plan with no `- Date:` line is renamed by `group` to `20260101-nodate-01-...` while `rename` on the same file preserves `20260908-...`. The plan deferred this as "a real question this plan does NOT answer"; it is answered, and the deferral is now evidence-backed rather than speculative, with a follow-up obligation instead of an open unknown. | probe at review; both date derivations read |
| F-14 | LOW | every `plans_refs.py` citation had drifted | Off by five to twelve lines throughout: `start_order` default `:212` -> `:213`; the `+ i` loop `:225` -> `:226`; `run_set_assign`'s flag read `:432` -> `:420` and its collapse `:437` -> `:425`; `run_mv`'s fallback `:467-475` -> `:453-462`; `plan_set_assign` itself `:207` -> `:208`. Small, but the plan's own gate says to locate by name, and these are the lines a reader would jump to first. | re-located every symbol |
| F-15 | LOW | the recorded baseline was wrong | The plan cites `1 failed, 5648 passed` with the failure in `tests/test_orchestrator_retirement.py`. Measured at review: `1 failed, 5919 passed, 3 skipped, 2 xfailed`, and the failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, caused by 189 untracked `opencode-recovery/*.md` files belonging to another party. An executor expecting the wrong failure could chase a phantom regression or "fix" another party's files. | bare suite at review |

## Proposed changes (ordered, validatable)

1. Reproduce the clobber as TWO failing tests, one per `group` branch, mirroring the `rename` fixture (E-01).
2. Make an absent `--order` preserve on BOTH branches, choosing between `run_mv`'s three-tier lookup and `run_group_generic`'s threaded `Optional[int]` (the reviewer's reading favors the latter) and removing the ambiguous sentinel, while keeping the explicit sequential renumber (E-02).
3. Record a decision on refusing a `Kind: child` at Order 0, filing a follow-up rather than widening scope (E-03).
4. Prove six cases: both-branch preserve, explicit-sequential, filename fallback, orchestrator-at-0, and explicit `--order 0`, plus the `IPD-M104`-specific flip (E-04).
5. Prove `rename`'s regression and the `MutationResult` contract are unchanged, `research_refs` untouched, with an empty suite delta (E-05).

## Deferred / out of scope (with reason)

- CHANGING `run_mv`. It is correct and regression-tested; this plan ports FROM it. Editing it would put unrelated risk inside a bug fix.
  - Carrier-Declined: NO DEFECT IS BEING DEFERRED HERE. `run_mv` already holds the correct behavior (vf03z3) and is pinned by `PlansMvPreservesOrderAndDateTests`; this row records that it was deliberately NOT edited, so there is nothing for a carrier to carry onward. Verified byte-unchanged at execution (V-02).
- CHANGING `artifact_rename.run_group_generic`. It is ALREADY CORRECT (F-10) and is the preferred model for E-02 to copy. Reading it is in scope; editing it is not.
  - Carrier-Declined: NO DEFECT IS BEING DEFERRED HERE either. That backend already threads an `Optional[int]` correctly for every non-plan type; it was read as the model and left byte-unchanged (`git diff --stat` empty, V-02). Nothing outstanding.
- THE DATE DEFECT, WHICH IS NOW MEASURED RATHER THAN AN OPEN QUESTION (F-13). `group` derives the name date from `_plan_date(text)` alone, whose no-match fallback is the literal `"20260101"`, while `run_mv` prefers the filename's date first; verified, a plan with no `- Date:` line is renamed by `group` to `20260101-...` where `rename` preserves `20260908-...`. It stays out of scope because bundling a second field's behavior would make the Order fix unreviewable, but the deferral is now EVIDENCE-BACKED: the executor must FILE a backlog item for it with this measurement, not merely "record it if the fixture happens to show it". FILED at execution.
  - Carrier: j84jg3
- `research_refs.run_set_assign`'s IDENTICAL DEFECT (F-12), which is the same bug in `aw group research`, plus the `aw research set-assign --order` help string that documents the buggy default verbatim (`cli.py:2246`). File it; do NOT fix it here, and specifically do not extract a shared helper across the two backends, which would drag a second verb's behavior change inside this fence. FILED at execution (the help string now at `cli.py:2757`, folded into the same item).
  - Carrier: 4y4xo5
- THE LINT-REACHABILITY GAP. `k9awrq` (`lintreach-01`, from `q0h9ls`) owns making `aw check` run the `IPD-*` family. This plan's F-6 is a concrete instance of why that matters, not a licence to fix it here.
  - Carrier: k9awrq
- REFUSING A CHILD AT ORDER 0. E-03 records the decision; building it is conditional and probably a follow-up, because once E-02 lands the accidental path is closed and only an explicit `--order 0` remains. DECIDED at execution: not built, filed instead (see V-03).
  - Carrier: r30nnz
- THE SETID-COLLISION-AT-CREATION GAP. `dw7i3m` (`setidhard` Order 03) owns it. This plan reproduced that defect too while authoring (its own Set collided with the backlog item), which is reported, not fixed here.
  - Carrier-Declined: THE PREMISE OF THIS ROW WAS REVERSED AFTER IT WAS WRITTEN, checked at execution rather than assumed. `dw7i3m` is now `superseded` (retired 2026-09-10) precisely because the maintainer REVERSED the design it implemented: spec `2lcqno` (`.aw/records/specs/20260910-2lcqno-01-2lcqno-setid-shared-topic-label-and-type-scoped-resolution.spec.md`) N1 rules that a setid is a SHARED cross-type TOPIC label and that nothing may prevent or rename a cross-type setid used that way, and N6 that graduation PRESERVES the source's setid rather than minting a fresh one. So a plan Set sharing its setid with the backlog item it graduated from, the very thing this row calls a collision, is now the SPECIFIED behavior and not a defect. There is therefore no outstanding obligation to hand on, and naming the retired plan as a carrier would point a live gate at a dead design. A carrier is declined rather than re-pointed for that reason. (A genuinely separate live question about which population `check.setid-collision` reports already has its own carrier, backlog `lmjc8h`; it is not this plan's finding.)
- SWEEPING OR FIXING ANY PLAN ALREADY CARRYING A BAD ORDER. None exists: both live occurrences were recovered with explicit `--order` and nothing bad was committed. If the executor FINDS one, report it rather than regrouping another agent's plan.
  - Carrier-Declined: NOTHING TO CARRY, re-verified at execution rather than taken on the authored word: `git status --porcelain .aw/records/plans/` shows no rename in this tree, and no corrupted plan was found while executing. There is no outstanding defect, so a carrier would point at an empty set.
- `aw group` FOR NON-PLAN TYPES, WHICH REVIEW HAS NOW SPLIT IN TWO. The `artifact_rename.run_group_generic` backend serving `specs`/`backlog`/`prompts`/`walkthroughs`/`roadmaps`/`releases`/`other` is ALREADY CORRECT and needs nothing (F-10). The `research_refs` backend is NOT, and carries the byte-identical defective line (F-12). So "if another type's backend shares the shape" is answered: exactly one does, it is named, and it is deferred with a filing obligation rather than left as a maybe. That obligation is discharged by the same item the `research_refs` row names.
  - Carrier: 4y4xo5

## Scope check

- Over-scope: none. One parameter's semantics, one call site, both of its branches, one test class.
- Scope-Paths justification: `agent_workflows/cli.py` holds the SHARED `--order` help string the spec-sync section requires be rewritten (`:3118`); it was NOT declared in the authored plan even though that section mandated the edit, so an executor doing as instructed would have gone out of fence and owed a `--scope-reason` at finalize (PR-005). `agent_workflows/plans_refs.py` holds `plan_set_assign` (`:208`), its `start_order` default (`:213`), the `order = start_order + i` loop (`:226`) that feeds BOTH branches, the metadata-only `RenamePlan(src, src, ...)` (`:239-241`) that F-11 shows is the worse half, `run_set_assign`'s collapsing call site (`:420`, `:425`), and `run_mv`'s three-tier fallback (`:453-462`); `tests/test_awnaming_grammar_and_producers.py` holds `PlansMvPreservesOrderAndDateTests`, the fixture E-01 mirrors and the regression E-05 must keep green, so the two verbs' guarantees sit side by side. `agent_workflows/artifact_rename.py` is deliberately NOT declared: E-02 READS `run_group_generic` as its model (F-10) and must not edit it, and a declared-but-unmodified path would need a `--scope-ack` at finalize.
- Under-scope, stated rather than left as `none`: this plan does not touch `run_mv` or `run_group_generic`, does not fix the measured date defect (F-13, now a filing obligation), does not fix `research_refs`' identical defect (F-12, same), does not fix the lint-reachability gap, does not build the child-at-Order-0 refusal, does not touch setid collision prevention, and does not sweep any existing plan. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Do NOT add flags (`addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`). Baseline RE-MEASURED at review on `72a8f6ad`: `1 failed, 5919 passed, 3 skipped, 2 xfailed`, the failure being the environmental `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (189 untracked `opencode-recovery/*.md` files belonging to another party). Expect it in BOTH runs; it cancels in the delta and must not be fixed. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- THE TWO FAILING-FIRST TESTS (E-01) shown failing at HEAD and passing after, with all four outputs pasted. A test only ever run against the fixed code proves nothing about the defect.
- SIX CASES (E-04): `--rename` preserve, METADATA-ONLY preserve with filename and front matter AGREEING, explicit-sequential across several plans, filename fallback when front matter lacks `- Order:`, an orchestrator at Order 0 staying 0, and an explicit `--order 0` still landing at 0.
- THE `IPD-M104` BEFORE/AFTER on the regrouped child, pasted, as the end-to-end proof. Assert on the ABSENCE OF THAT CODE, not on a clean lint exit: a probe plan also emits unrelated `IPD-H2xx` structural codes, so an exit-0 assertion can never pass.
- `tests/test_awnaming_grammar_and_producers.py` re-run with ITS OWN summary line, showing `rename`'s regression still green.
- PROOF THE `MutationResult` SHAPE IS UNCHANGED, since the noun-verb router consumes it to place the self-commit offer once (`cli.py:8642`).
- PROOF `research_refs.py` IS BYTE-UNCHANGED (`git diff --stat` over it, empty), since its identical defect is deferred and a shared-helper refactor is forbidden.
- THE TWO DEFERRED DEFECTS FILED, not merely mentioned: paste the backlog item ids for the date defect (F-13) and the `research_refs` defect (F-12), each carrying its measurement.
- NEGATIVE PROOF that no real plan was regrouped: `git status --porcelain .aw/records/plans/` showing no unexpected renames.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`plan_set_assign`'s DOCSTRING currently says only "Plan a Set (re)assignment for the given plans; with `rename` also plan clustering renames." It must state what an ABSENT `--order` now means (preserve per plan, on BOTH branches) versus an EXPLICIT one (renumber sequentially from it), because that distinction is the whole fix and the next reader will otherwise reintroduce the collapse.

ADD THE `vf03z3` CROSS-REFERENCE at the new fallback, the way `run_mv` already does, AND name whichever sibling shape E-02 copied (`run_mv`'s three-tier lookup or `run_group_generic`'s threaded `Optional`). A future reader who changes one of the three should find the other two immediately; today two of them are correct and cross-reference nothing.

`--help` FOR `--order` IS SHARED BY `rename` AND `group` in the noun-verb parser (`cli.py:3118`, currently the bare "Order NN (rename/group)."), so one edit lands on both verbs. It should say that omitting it PRESERVES each artifact's existing Order, since today its absence silently means "renumber from zero" for `group` and nothing documents that. Do NOT edit the separate `aw research set-assign --order` string (`cli.py:2246`, "Starting NN (default 0).") even though it documents the buggy behavior verbatim: that parser belongs to the deferred `research_refs` item, and `cli.py` is not in `Scope-Paths`, so touching it needs a `--scope-reason`. Decide which of the two you are doing and say so. This is operator-facing prose: write no em or en dashes.

No spec change is expected. The naming grammar (`NN` with `00` reserved for an orchestrator) is defined by the uniform artifact-naming spec, which this plan HONORS rather than amends. If the executor finds spec text permitting a child at Order 0, that is a contradiction to report, not to edit here.

EXECUTED 2026-09-20, recording WHAT WAS DONE against each obligation above, since this section asked the executor to decide and say so.

THE DOCSTRING IS REWRITTEN. `plan_set_assign`'s docstring now states the two meanings explicitly (absent `--order` PRESERVES each plan's own Order per plan, resolved by `_preserved_order`; an integer, INCLUDING zero, renumbers sequentially from it via `start_order + i`) and says WHY it applies to both branches, namely that the Order is resolved ABOVE the `rename` split so the metadata-only branch can no longer write an `- Order:` its own filename contradicts.

THE `vf03z3` CROSS-REFERENCE IS PRESENT IN TWO PLACES and names the shape that was copied, as required: `_preserved_order`'s docstring ("The tier order matches ``run_mv``'s already-shipped fallback (vf03z3: \"a bare rename must NOT clobber Order to 0\")") and the `run_set_assign` call-site comment ("the same guarantee `run_mv` has carried since vf03z3"). Both also state that `run_mv` was deliberately left byte-unchanged rather than refactored into a shared helper, so the next reader is not tempted into the refactor this plan's gate forbids. NOTE THE SHAPE NAMED IS A HYBRID and V-02 says why: Shape B's threading with Shape A's tiers, because Shape B's `None`-skips-the-line mechanism cannot transfer to a writer (`_set_metadata`) that takes `order: int`, inserts the line when absent, and is shared with `run_mv`.

WHICH `--help` STRING: THE SHARED `rename`/`group` ONE, and ONLY that one. It now reads "Order NN (rename/group). Omit it to PRESERVE each artifact's existing Order; give it to renumber the named artifacts sequentially from NN." (verified through `aw group --help`). The separate `aw research set-assign --order` string was deliberately NOT touched; its literal "Starting NN (default 0)." still documents the buggy default, which is correct because that backend still HAS the bug, and it is folded into the filed carrier `4y4xo5` rather than left as a mismatch. Two drift notes for a future reader, both re-located by symbol as this plan's gate instructs: the shared string is now at `cli.py:3628` (cited `:3118`) and the research one at `cli.py:2757` (cited `:2246`). The wording contains no em or en dash.

`cli.py` WAS IN `Scope-Paths` for exactly this edit, so no `--scope-reason` is owed; the edit is the two-clause help string and nothing else in that file.

NO SPEC WAS CHANGED, and the expectation held on inspection: nothing in the naming grammar permits a `Kind: child` at Order 0, so there was no contradiction to report. `aw ipd lint`'s `IPD-M104` states the rule the same way the grammar does.

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
- Carrier: r30nnz
- Resolution or deferral rationale: DELIBERATELY OPEN AND SUBORDINATE TO E-02, because the fix changes what the refusal would be worth. Today the ACCIDENTAL path is the whole problem: nobody types `--order 0` on a child, they simply omit the flag. Once E-02 preserves by default, a refusal would only catch an explicit `--order 0`, a much rarer mistake, while adding a new failure mode to a verb that is the recommended recovery for a setid collision (so a refusal there could block a repair). The counter-argument is real: `aw ipd lint` already knows the rule (`IPD-M104`) and not consulting it at the write site is the same gap `sjsoqq` documents for setids. E-03 therefore requires a recorded decision and permits filing a follow-up instead of building, and this stays non-blocking because the plan delivers its fix either way.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste BOTH new tests and their ACTUAL FAILING output at HEAD, before any fix: the `--rename` case and the METADATA-ONLY case. For the rename case, quote the two assertions separately, one checking the front-matter `- Order:` and one the filename `NN` slot. For the metadata-only case, paste the DIVERGENCE explicitly (filename `-01-` beside front matter `- Order: 0`), since that contradiction is the finding the plan originally missed. Confirm in one sentence that the fixture mirrors `PlansMvPreservesOrderAndDateTests` rather than inventing a new repo shape.
  - Observed evidence: BOTH TESTS FAIL AT HEAD, MEASURED AGAINST PRISTINE HEAD SOURCE rather than against the working tree. HOW, because this matters and is a defect in its own right (see V-05 and the filed item `ccbe60`): the repository is installed EDITABLE and that install names an ABSOLUTE path to the MAIN checkout, so a `-m agent_workflows` subprocess launched from this lane imports the MAIN checkout's modules. The failing-first run was therefore done in a `git archive HEAD` extraction of this branch with ONLY the new test file copied in, so the source under test was unfixed by construction: `git archive HEAD | tar -x -C <tmp>` then `cp tests/test_awnaming_grammar_and_producers.py <tmp>/tests/`, verified by printing that tree's own lines (`start_order: int = 0,` / `order = start_order + i` / `start_order=start if start is not None else 0`) before running.

    THE TWO FAILURES, verbatim from `python3 -m pytest -o addopts="" -p no:randomly tests/test_awnaming_grammar_and_producers.py::PlansGroupPreservesOrderTests -v` in that HEAD tree:

    ```
    tests/...::PlansGroupPreservesOrderTests::test_bare_metadata_only_regroup_preserves_a_child_order FAILED [ 50%]
    tests/...::PlansGroupPreservesOrderTests::test_bare_rename_regroup_preserves_a_child_order FAILED [100%]
    ...
    >       self.assertIn("- Order: 1", text)
    E       AssertionError: '- Order: 1' not found in '# IPD: probe\n\n- Date: 20260908\n- Kind: child\n...\n- Set: metaset\n- Order: 0\n- Author: t\n- Id: bbb222\n\n## Goal\n\nx\n'
    tests/test_awnaming_grammar_and_producers.py:525: AssertionError
    ...
    >       self.assertIn("- Order: 1", moved.read_text(encoding="utf-8"))
    E       AssertionError: '- Order: 1' not found in '# IPD: probe\n\n- Date: 20260908\n- Kind: child\n...\n- Set: newset\n- Order: 0\n- Author: t\n- Id: bbb222\n\n## Goal\n\nx\n'
    tests/test_awnaming_grammar_and_producers.py:504: AssertionError
    ============================== 2 failed in 1.92s ===============================
    ```

    THE RENAME CASE'S TWO ASSERTIONS, QUOTED SEPARATELY as required. (1) the front matter: `self.assertIn("- Order: 1", moved.read_text(encoding="utf-8"))`. (2) the filename slot, asserted through the naming grammar's own parser so the `NN` field is read rather than string-matched: `m = refs._CLUSTERED_RE.match(moved.name)` then `self.assertEqual(m.group("nn"), "01", moved.name)`. At HEAD assertion (1) is what fails first; the direct CLI probe below shows (2) is equally violated, because the child is MOVED into the `00` slot: `renamed .aw/records/plans/pending/20260908-probeset-01-bbb222-probe-child-one.ipd.md -> .aw/records/plans/pending/20260908-newset-00-bbb222-probe-child-one.ipd.md`, exit 0, no warning, with the resulting `FRONT MATTER Order line: ['- Order: 0']`.

    THE METADATA-ONLY DIVERGENCE, printed side by side from the same probe at HEAD, which is the contradiction the authored plan did not scope:

    ```
    METADATA-ONLY DIVERGENCE AT HEAD:
      filename: 20260908-probeset-01-bbb222-probe-child-one.ipd.md
      front matter: ['- Order: 0']
    ```

    So the filename reads `-01-` while the front matter reads `- Order: 0`. The test pins that as a relation and not just a value, comparing the two fields directly (`self.assertEqual(int(order_line.group(1)), int(m.group("nn")), ...)`), so a future half fix that keeps one and clobbers the other still fails. And F-6 reproduced in the same tree: `aw ipd lint` on that file exits 1 reporting `! IPD-M104: Order: child Order must be an integer >= 1` while `aw check plans` in the SAME tree exits 0 with `✓ CONFORMS  3 plans checked / errors 0   warnings 0`.

    FIXTURE PROVENANCE, in one sentence as required: `PlansGroupPreservesOrderTests` subclasses the SAME `_RepoBackendCLIFixture` that `PlansMvPreservesOrderAndDateTests` uses and copies its seed-then-`git commit` pattern (a plan carrying `- Kind:`, `- Set:`, `- Order:` and `- Id:`, committed before the CLI runs), extended only by seeding a three-plan Set (orchestrator at 0, children at 1 and 2) because this defect is about renumbering ACROSS plans, so the two verbs' regressions now sit adjacently in one file.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the changed `run_set_assign` and `plan_set_assign` signature, showing the sentinel now distinguishes absent from `--order 0`. NAME WHICH SIBLING SHAPE YOU COPIED (`run_mv`'s three-tier lookup at `plans_refs.py:453-462`, or `run_group_generic`'s threaded `Optional[int]` at `artifact_rename.py:682`/`:142`/`:237`) AND WHY, and paste the `vf03z3` cross-reference comment. Paste the code path for BOTH branches, showing the metadata-only `RenamePlan` no longer writes an Order the filename contradicts. Paste NEGATIVE proof that `run_mv` and `run_group_generic` are byte-unchanged (`git diff` over each) and that the `+ i` arithmetic still exists.
  - Observed evidence: THE SENTINEL NOW DISTINGUISHES ABSENT FROM ZERO, in both the signature and the call site:

    ```python
    def plan_set_assign(
        plans_dir: Path,
        id6s: List[str],
        set_id: str,
        *,
        start_order: Optional[int] = None,     # was: start_order: int = 0
        rename: bool = False,
    ) -> Tuple[Optional[List[RenamePlan]], Optional[str]]:
    ```

    ```python
    # run_set_assign, replacing `start = getattr(args, "order", None)` +
    # `start_order=start if start is not None else 0`:
        plans, err = plan_set_assign(
            plans_dir,
            ids,
            getattr(args, "set", "") or "",
            start_order=getattr(args, "order", None),
            rename=getattr(args, "rename", False),
        )
    ```

    WHICH SHAPE, AND WHY: A HYBRID THAT TAKES SHAPE B'S THREADING AND SHAPE A'S TIER ORDER, chosen deliberately after reading both, and this deviates from the reviewer's "Shape B" reading in one respect that must be stated plainly. FROM SHAPE B (`artifact_rename.run_group_generic`) I took the `Optional[int]` threaded from the flag, computed ONCE above the `rename` split, which is what makes both branches correct by construction rather than by two guards. FROM SHAPE A (`run_mv`) I took the RESOLUTION TIERS, because Shape B's mechanism does not transfer: Shape B lets `None` flow to a metadata writer that SKIPS the `- Order:` line entirely (`if order is not None and _ORDER_LINE_RE.search(text)`), whereas the plans path writes through `_set_metadata`, which takes `order: int` and INSERTS a `- Set:`/`- Order:` pair when absent, and is shared with `run_mv`. Threading a bare `None` into it would either need `_set_metadata` changed (it is on `run_mv`'s path, and `run_mv` is explicitly out of scope) or would silently stop writing the Order on the metadata-only branch, which is that branch's whole job. So `None` is RESOLVED PER PLAN to a concrete int immediately, one function above the split, by `run_mv`'s tier order (front-matter `- Order:`, else the filename's `NN`, else 0):

    ```python
    def _preserved_order(name: str, text: str) -> int:
        """The Order a plan ALREADY has: its front-matter ``- Order:``, else its filename's ``NN``, else 0.

        e3hzyc: this is what a bare ``aw group plans ... --set X`` (no ``--order``) must write, so the
        verb stops renumbering every named plan from zero and parking a ``Kind: child`` in the ``00``
        slot the naming grammar reserves for an orchestrator. The tier order matches ``run_mv``'s
        already-shipped fallback (vf03z3: "a bare rename must NOT clobber Order to 0"), which is
        deliberately left byte-unchanged here rather than refactored into a shared helper.
        """

        om = _ORDER_LINE_RE.search(text)
        if om:
            return int(om.group(1))
        parsed = _CLUSTERED_RE.match(name)
        return int(parsed.group("nn")) if parsed else 0
    ```

    That docstring is the required `vf03z3` cross-reference, and it also names the shape it copied, as the spec-sync section demands. The `run_set_assign` call site carries the second cross-reference ("the same guarantee `run_mv` has carried since vf03z3").

    BOTH BRANCHES, from the one resolution ABOVE the split, which is the F-11 requirement:

    ```python
        for i, id6 in enumerate(id6s):
            src = _find_plan_by_id(plans_dir, id6)
            if src is None:
                return None, f"no plan has Id '{id6}'"
            text = src.read_text(encoding="utf-8")
            order = (
                (start_order + i)
                if start_order is not None
                else _preserved_order(src.name, text)
            )
            if rename:
                new_name = clustered_name(..., order=order, ...)
                plans.append(RenamePlan(src, src.parent / new_name, id6, order=order))
            else:
                plans.append(
                    RenamePlan(src, src, id6, order=order)
                )  # metadata-only (no rename)
    ```

    So the metadata-only `RenamePlan(src, src, id6, order=order)` now carries the plan's OWN Order, and the `--rename` branch feeds that same value into BOTH `clustered_name` (the filename `NN`) and the front matter, which is why the two can no longer diverge. Note `text = src.read_text(...)` MOVED up out of the `if rename:` block, since both branches need it now; nothing else in the loop changed.

    ONE MORE SITE NEEDED IT, found by reading rather than by a failing test: `apply_renames`'s PREVIEW path printed the loop index (`Order={i:02d}`) for the metadata-only case, so a dry run would have advertised a renumber the apply no longer performs. It now prints the Order that will actually be written: `shown = p.order if p.order is not None else i`. The `p.order is not None` guard is kept because `RenamePlan.order` defaults to `None` for other constructors.

    NEGATIVE PROOF, `run_mv` AND `run_group_generic` UNTOUCHED. `git diff --stat -- agent_workflows/artifact_rename.py` prints NOTHING (empty), so `run_group_generic`, `compute_target_name` and `_update_or_inject_set_metadata` are byte-unchanged. Within `plans_refs.py`, `git diff -U0 -- agent_workflows/plans_refs.py | grep -n run_mv` returns only two lines, both of them the new REFERENCES to it inside my added comments (`+    slot the naming grammar reserves ... matches ``run_mv``'s` and `+    # each plan's own Order", the same guarantee `run_mv` has carried since vf03z3.`); no hunk touches the `run_mv` body, and its three-tier fallback, its date handling and its `RenamePlan(...)` construction are unchanged. `_set_metadata` is likewise unmodified, which is what keeps `run_mv`'s write path identical.

    THE `+ i` ARITHMETIC STILL EXISTS: `grep -n "start_order + i" agent_workflows/plans_refs.py` reports `243:` (the docstring stating the rule) and `257:` (the live expression `(start_order + i)`), so explicit Set assembly is preserved. V-04(c) exercises it end to end.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: state the recorded decision on refusing a child at Order 0 and its reasoning. If a follow-up item was filed, paste its id and summary. If a refusal was implemented instead, paste the test proving an ORCHESTRATOR at Order 0 is still permitted, since that is the case a careless refusal breaks.
  - Observed evidence: THE DECISION IS: DO NOT BUILD THE REFUSAL IN THIS PLAN, and it is filed rather than left in prose. Reasoning, in order of weight. (1) E-02 CLOSED THE ACCIDENTAL PATH, which was the entire observed problem: nobody types `--order 0` on a child, they omit the flag and the verb substituted zero. With an absent flag now preserving, a refusal would only ever catch an EXPLICIT `--order 0` on a `Kind: child`. (2) A REFUSAL CHANGES A VERB'S CONTRACT on the RECOMMENDED REPAIR PATH for a setid collision (spec `4w7d6s` I4), so a new failure mode there can block a repair, which is the same class of harm the original defect had. (3) IT MUST BE CONDITIONAL ON `- Kind: child` because an orchestrator at 0 is correct and common, and that conditionality is exactly what a careless implementation gets wrong. The counter-argument is recorded in the item rather than dismissed: `aw ipd lint` already knows the rule (`IPD-M104`) and the write site does not consult it, the same shape `sjsoqq` documents for setid collisions at creation.

    FILED: `r30nnz`, `.aw/records/backlog/open/20260920-r30nnz-01-r30nnz-refuse-child-at-order-zero.backlog.md`, summary "Decide whether aw group/rename should refuse to place a Kind: child at Order 0 (consult IPD-M104 at the write site)", `- Work-Kind: followup`, `- Priority: low`, `- Status: open`. It carries the decision above plus the acceptance criteria if it is ever built (refuse only when `- Kind: child` AND the resolved Order is 0; permit an orchestrator at 0 unconditionally with a test pinning that case; name the rule in the refusal message). It is deliberately NOT release-gating, because it is a hardening followup and not a live defect: the defect this plan fixes is gone.

    NO REFUSAL WAS IMPLEMENTED, so the "if you build it" evidence does not apply. The orchestrator case is nonetheless PINNED, because "preserve" must not be read as "move off zero": `test_bare_regroup_keeps_an_orchestrator_at_zero` regroups the seeded `- Kind: orchestrator` plan bare and asserts it stays at `20260908-orchset-00-aaa000-` with `- Order: 0`. It PASSES both before and after the fix (see V-04), which is the honest reading: it is a must-not-break guard, not a demonstration of the bug.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the ACTUAL passing output of all SIX cases, QUOTING the explicit-sequential multi-plan assertion separately since it is the behavior a careless fix destroys, and QUOTING the explicit `--order 0` case separately since it is the direct test of the sentinel change and the one likeliest to be skipped as a no-op. Paste the METADATA-ONLY case showing the filename and the front matter now AGREE. Paste the `aw ipd lint` output for the regrouped child BEFORE (showing `IPD-M104`) and AFTER (showing that CODE absent, not a clean exit, since unrelated `IPD-H2xx` codes will still fire on a probe file), with unpiped exit codes.
  - Observed evidence: ALL SIX CASES PASS, plus a seventh pinning the lint flip. `python3 -m pytest -o addopts="" -p no:randomly tests/test_awnaming_grammar_and_producers.py::PlansGroupPreservesOrderTests -v`:

    ```
    collected 7 items

    tests/...::test_bare_metadata_only_regroup_preserves_a_child_order PASSED [ 14%]
    tests/...::test_bare_regroup_falls_back_to_the_filename_slot PASSED      [ 28%]
    tests/...::test_bare_regroup_keeps_an_orchestrator_at_zero PASSED        [ 42%]
    tests/...::test_bare_rename_regroup_preserves_a_child_order PASSED       [ 57%]
    tests/...::test_explicit_order_still_renumbers_sequentially PASSED       [ 71%]
    tests/...::test_explicit_order_zero_is_still_reachable PASSED            [ 85%]
    tests/...::test_lint_no_longer_reports_ipd_m104_after_a_bare_regroup PASSED [100%]

    ============================== 7 passed in 3.21s ===============================
    ```

    WHICH OF THOSE ACTUALLY DEMONSTRATE THE FIX, stated because "7 passed" alone does not distinguish a fixed defect from a guard. Run against PRISTINE HEAD source (the `git archive` tree described in V-01), FOUR fail and THREE pass: `test_bare_metadata_only_regroup_...`, `test_bare_regroup_falls_back_to_the_filename_slot`, `test_bare_rename_regroup_...` and `test_lint_no_longer_reports_ipd_m104_...` FAILED, while the orchestrator-at-zero, explicit-sequential and explicit-zero cases PASSED (`4 failed, 3 passed in 5.35s`). So the four are regressions for the defect and the three are must-not-break guards, which is exactly the split the plan asked for. The HEAD failure for case (d) is worth quoting because it is the tier the plan predicted: `AssertionError: False is not true : 20260908-fbset-00-ddd444-probe-no-order-line.ipd.md`, i.e. at HEAD a plan with no `- Order:` line went to the `00` slot instead of keeping its filename's `04`.

    (c) THE EXPLICIT-SEQUENTIAL MULTI-PLAN ASSERTION, QUOTED SEPARATELY as required, since it is the behavior a preserve-always fix destroys. Two plans are named in one call with `--order 1`:

    ```python
        r = self._run_cli(["group", "plans", "bbb222", "ccc333", "--set", "asmset",
                           "--order", "1", "--rename", "--apply"])
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        first = self._only("bbb222"); second = self._only("ccc333")
        self.assertTrue(first.name.startswith("20260908-asmset-01-bbb222-"), first.name)
        self.assertIn("- Order: 1", first.read_text(encoding="utf-8"))
        self.assertTrue(second.name.startswith("20260908-asmset-02-ccc333-"), second.name)
        self.assertIn("- Order: 2", second.read_text(encoding="utf-8"))
    ```

    Note the seeded Orders are 1 and 2 already, so this case is deliberately NOT self-satisfying by preservation: `ccc333` is asserted at `02` because `+ i` put it there from `--order 1`, and the assertion pins the filename `NN` and the front matter together.

    (f) THE EXPLICIT `--order 0` CASE, QUOTED SEPARATELY as the direct test of the sentinel change, which is the one an executor would skip as a no-op. It proves `None` meaning "preserve" did not make zero unreachable, and it is not satisfiable by preservation because the plan it moves (`ccc333`) is seeded at Order 2:

    ```python
        r = self._run_cli(["group", "plans", "ccc333", "--set", "zeroset",
                           "--order", "0", "--rename", "--apply"])
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        moved = self._only("ccc333")
        self.assertTrue(moved.name.startswith("20260908-zeroset-00-ccc333-"), moved.name)
        self.assertIn("- Order: 0", moved.read_text(encoding="utf-8"))
    ```

    (b) THE METADATA-ONLY CASE NOW AGREES WITH ITS OWN NAME, asserted as a RELATION and not merely as a value, which is what makes a future divergence fail rather than pass:

    ```python
        self.assertEqual(kept.name, "20260908-probeset-01-bbb222-probe-child-one.ipd.md", kept.name)
        self.assertIn("- Order: 1", text)
        m = refs._CLUSTERED_RE.match(kept.name)
        order_line = refs._ORDER_LINE_RE.search(text)
        self.assertEqual(int(order_line.group(1)), int(m.group("nn")),
                         f"filename NN {m.group('nn')} disagrees with front matter {order_line.group(1)}")
    ```

    THE `IPD-M104` BEFORE/AFTER, with exit codes read from the process itself (`subprocess.run(...).returncode`, never through a pipeline). BEFORE, at HEAD, regrouping the child produced the code, quoted from the HEAD-tree run of this very test: `AssertionError: 'IPD-M104: Order:' unexpectedly found in "-    approved     plan        20260908-lintset-00-bbb222  error\n     ! IPD-M104: Order: child Order must be an integer >= 1\n ..."`, so at HEAD the regrouped child lints with `IPD-M104: Order:` and lands in the `00` slot. AFTER the fix, the same probe run in this tree:

    ```
    === aw ipd lint BEFORE regroup (seeded child at Order 1), exit: 1
    -    approved     plan        20260908-probeset-01-bbb222  error
         ! IPD-M104: Approval: Approval is required when Status is approved
         ! IPD-H202: required H2 missing: Workflow history
         ... (12 more IPD-H202 rows) ...
         ! IPD-M106: Scope-Paths is required at the ready-to-execute gate: ...
    === regroup: renamed .aw/records/plans/pending/20260908-probeset-01-bbb222-probe-child-one.ipd.md -> .aw/records/plans/pending/20260908-lintset-01-bbb222-probe-child-one.ipd.md
    === aw ipd lint AFTER bare regroup, exit: 1
    -    approved     plan        20260908-lintset-01-bbb222  error
         ! IPD-M104: Approval: Approval is required when Status is approved
         ... same IPD-H202 / IPD-M106 rows, NO `IPD-M104: Order:` row ...
    ```

    Read it exactly as the plan instructed: the exit code is 1 BOTH times and always will be, because a minimal probe plan legitimately violates the structural rules, so the assertion is on the CODE. `IPD-M104: Order:` is absent after the regroup, and the destination is `-lintset-01-` rather than `-lintset-00-`. The test asserts the absence of `IPD-M104: Order:` AND the presence of `IPD-H202`, so it cannot pass on empty output (an assertion on a clean exit could never pass at all, exactly as the plan warned). One subtlety the narrowing had to respect: `IPD-M104` is a SHARED code that also carries the unrelated "Approval is required" finding, so the assertion matches the `IPD-M104: Order:` prefix rather than the bare code.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `tests/test_awnaming_grammar_and_producers.py`'s OWN summary line showing `rename`'s regression green. Paste proof the `MutationResult` shape is unchanged and that the router's self-commit offer still fires once (`cli.py:8642`). Paste `git diff --stat agent_workflows/research_refs.py` EMPTY, proving the deferred sibling defect was not opportunistically fixed and no shared helper was extracted. Paste the two filed backlog item ids (the date defect F-13 and the `research_refs` defect F-12) with their measurements. Paste `git status --porcelain .aw/records/plans/` proving no real plan was regrouped. THEN paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly, expecting the environmental `test_reporting_contract` failure in both.
  - Observed evidence: `rename`'s REGRESSION IS GREEN, with the file's own summary line. `python3 -m pytest -o addopts="" tests/test_awnaming_grammar_and_producers.py`: `20 passed in 5.44s` (13 pre-existing + 7 new), and named individually, `PlansMvPreservesOrderAndDateTests::test_mv_preserves_order_date_and_adds_facet PASSED`. That matters here because both verbs live in `plans_refs` and share `_ORDER_LINE_RE` and `_CLUSTERED_RE`, which `_preserved_order` now also reads. `tests/test_plans_refs.py` (the module's other suite, including `SetAssignTests` which calls `plan_set_assign` DIRECTLY with an explicit `start_order=`) is also green: `8 passed`, unmodified, so the changed keyword remains backward compatible for in-process callers.

    THE `MutationResult` SHAPE IS UNCHANGED, and this is negative proof plus a behavioral test. `git diff -- agent_workflows/plans_refs.py | grep -E "^[+-].*MutationResult"` prints NOTHING: neither the NamedTuple definition, nor its docstring, nor any of `run_set_assign`'s three `return MutationResult(...)` statements were touched. THE ROUTER STILL FIRES THE OFFER ONCE, asserted rather than asserted-by-reading: `python3 -m pytest -o addopts="" -p no:randomly tests/test_selfcommit_adoption.py -v` gives `25 passed in 1.88s`, including `BackendReturnShapeTests::test_plans_backend_returns_touched_paths PASSED`, `DispatchCoverageTests::test_group_plans_offers_once PASSED`, `DispatchCoverageTests::test_group_research_offers_once PASSED` and `DispatchCoverageTests::test_group_specs_offers_once_nonplans_coverage PASSED`. The dispatch site itself is unedited and still aggregates then offers once (`if isinstance(result, MutationResult): ... touched_all.extend(result.touched_paths)` then `if verb in ("group", "rename") and touched_all: ... _offer_records_commit(...)`); note the plan's citation `cli.py:8642` has drifted to `cli.py:9429`/`:9434`, located by symbol as the plan's own gate instructs.

    `research_refs` IS BYTE-UNCHANGED AND NO SHARED HELPER WAS EXTRACTED. `git diff --stat -- agent_workflows/research_refs.py` prints nothing (empty). Stronger, `git diff -- agent_workflows/plans_refs.py | grep -iE "^[+-].*research"` also prints nothing, so no import, no call, and no cross-backend coupling was introduced in either direction; `_preserved_order` is a private module-local function in `plans_refs` only. `git diff --stat -- agent_workflows/artifact_rename.py` is likewise empty, so the Shape B model was READ and not edited.

    THE DEFERRED DEFECTS ARE FILED, WITH THEIR MEASUREMENTS, not merely mentioned. F-12 -> `4y4xo5`, `.aw/records/backlog/open/20260920-4y4xo5-01-4y4xo5-group-research-clobbers-order.backlog.md`, `- Work-Kind: bug`, `- Blocks-Release: next`, carrying the measurement that `research_refs.run_set_assign` holds the byte-identical `start_order=start if start is not None else 0` against a planner defaulting `start_order: int = 0` and formatting `order=f"{start_order + i:02d}"`, and folding in the `aw research set-assign --order` help string that documents the buggy default verbatim ("Starting NN (default 0).", now at `cli.py:2757`). F-13 -> `j84jg3`, `.aw/records/backlog/open/20260920-j84jg3-01-j84jg3-group-plans-date-fallback.backlog.md`, `- Work-Kind: bug`, `- Blocks-Release: next`, carrying the measurement that `plan_set_assign` derives the name date from `_plan_date(text)` alone whose no-match fallback is the literal `"20260101"`, where `run_mv` prefers the filename's date, so a plan with no `- Date:` line is renamed by `group` to `20260101-...`. Both are release-gating under the all-bugs-block-release rule. TWO MORE ITEMS were filed beyond the plan's obligation: `r30nnz` (the E-03 decision record, `followup`, not gating) and `ccbe60` (`bug`, `Blocks-Release: next`, the editable-install/worktree test blind spot described below, found during this execution).

    NO REAL PLAN WAS REGROUPED. `git status --porcelain .aw/records/plans/` reports exactly one entry, ` M .aw/records/plans/pending/20260908-groupord-01-e3hzyc-...ipd.md`, which is THIS plan being filled in with execution evidence. There is no rename (no `R ` entry), no other plan touched, and every one of the seven test cases ran against a `tempfile` fixture repo. The verb was never pointed at `.aw/records/`.

    THE BARE SUITE, BEFORE AND AFTER, run as `python3 -m pytest` with no added flags. BEFORE: `1 failed, 7230 passed, 3 skipped, 2 xfailed, 3 warnings in 184.91s`. AFTER: `1 failed, 7237 passed, 3 skipped, 2 xfailed, 3 warnings in 168.03s`. DELTA: the failure SET is identical and therefore EMPTY after subtraction, the single failure being `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` in BOTH runs; passed count rises by exactly 7, which is the seven cases added here. THE PRE-EXISTING FAILURE IS NOT THE ONE THE PLAN PREDICTED, and the plan's prediction is now stale rather than wrong-at-the-time: it expected `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` caused by 189 untracked `opencode-recovery/*.md` files, and in this lane `ls opencode-recovery | wc -l` is 0 and that test PASSES. The failure actually present is ENVIRONMENTAL IN A DIFFERENT WAY, diagnosed rather than assumed: it asserts a non-isolated turn inherits NO permission policy, and it fails because THIS harness turn runs with `OPENCODE_CONFIG_CONTENT` already set in its own environment, which the test reads as a leaked policy. Proof it is the environment and not the code: `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest -o addopts="" "tests/test_turn_bounds.py::...::test_the_permission_policy_by_contrast_IS_isolation_scoped"` gives `1 passed in 0.47s`. It is unrelated to this change (nothing here touches turn bounds), it is present at HEAD, and it was correctly NOT fixed.

    TWO HONEST NOTES THAT BELONG IN THE RECORD. FIRST, `aw backlog check` exits 1 in this tree with 5 `backlog.id-duplicate` violations; that is PRE-EXISTING, verified by running the same check inside a pristine `git archive HEAD` extraction, which reports the identical 5 (`bplplj`, `gjadwm`, `f8m2z2`, `plbkp5`, `yw6759`) and exit 1. None of the four items filed here appears in it. SECOND, `aw sanitize --agent` is clean: `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,...}`.

    THE VALIDATION DEFECT THIS EXECUTION HAD TO WORK AROUND, recorded because it nearly invalidated this plan's own evidence and is now filed as `ccbe60`. The repository is installed EDITABLE with an ABSOLUTE path to the MAIN checkout, and `_RepoBackendCLIFixture._run_cli` shells out to `python3 -m agent_workflows` with no `PYTHONPATH`. Run from this lane, the in-process imports resolve HERE while the subprocess imports resolve to the MAIN checkout: measured, the two new tests still failed after the fix was written here, because the CLI they invoked was the main checkout's unfixed `plans_refs.py`. The symmetric hazard is worse, since a test can PASS while the tree under test is unfixed. This plan's own test class therefore overrides `_run_cli` (and adds `_lint`) to prepend the test file's own `REPO_ROOT` to the child's `PYTHONPATH`, a no-op when run from the main checkout; the repo-wide fix across every `-m agent_workflows` subprocess in `tests/` is out of this fence and is what `ccbe60` asks for.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION, deliberately: the one question the backlog item left open (does `aw rename` share the defect?) is answered NO by measurement, and that answer supplies a fix shape, so there is nothing for a maintainer to decide before execution. OQ-03 is genuinely open but subordinate, and E-03 permits recording a decision rather than building.

TWO REVIEW FINDINGS CHANGE WHAT MUST BE BUILT, not merely how it is described, and both should be read before starting. F-11: the defect ALSO fires with NO `--rename`, and that case is WORSE, because the front matter goes to `- Order: 0` while the filename keeps `-01-`, so the file contradicts its own name and nothing in the toolchain reports the divergence; the authored plan scoped only the `--rename` path, so a conforming execution could have fixed the visible half and shipped the invisible one. F-10: a SECOND and better precedent exists (`artifact_rename.run_group_generic` threads an `Optional[int]`), which fixes both branches by construction where the `run_mv` port fixes one, so "the fix is a PORT" was true of the wrong shape.

IT CARRIES `Blocks-Release: next`, inherited from the item under the all-bugs-block-release rule. The justification is not the cosmetic renumber: it is that the verb corrupts Orders on the RECOMMENDED REPAIR PATH for a setid collision, and that the resulting state is invisible to `aw check`.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Write the FAILING TESTS FIRST, both of them, and paste their failures; a fix demonstrated only against the fixed code is not demonstrated. Do NOT regroup, rename or edit any real plan as a test: measured at review, 104 plans are pending and 45 run directories hold a `driver.lock`, so use fixtures only. Do NOT touch `run_mv`, `artifact_rename.run_group_generic`, or `research_refs.py`, and do NOT extract a shared helper across the two defective backends. Do NOT touch the untracked `opencode-recovery/*.md` files, which belong to another party and cause the one known suite failure.

RE-LOCATE EVERY SYMBOL BY NAME, AND THE PROOF IS THIS PLAN'S OWN CITATIONS. Every `plans_refs.py` line number in the authored plan was off by five to twelve lines (F-14), and the corrected numbers above are themselves a snapshot. Find `plan_set_assign`, `run_set_assign`, `run_mv`, `_ORDER_LINE_RE`, `_CLUSTERED_RE`, `_plan_date`, `RenamePlan`, `MutationResult`, `artifact_rename.run_group_generic`, `compute_target_name`, and `research_refs.run_set_assign` BY NAME.

Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook, since `pre-commit` can leave another agent's paths in the index.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the failing-then-passing contrast and the `IPD-M104` before/after.
