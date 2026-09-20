# IPD: Run the existing verifier prompt against an already executed plan without re-executing it

- Date: 2026-09-08
- Kind: child
- Concern: THE INDEPENDENT SKEPTICAL VERIFIER EXISTS AND CAN ONLY EVER RUN AS THE SECOND TURN OF AN EXECUTION, SO IT CANNOT BE ASKED FOR AFTERWARDS. Re-verified at review by symbol: `build_verifier_prompt` composes the fresh-session verification turn and has exactly ONE production caller per host, both inside the execute path (`oc_runipd.py:4913` defined, called at `:6586`; `agy_runipd.py:2456` defined, called at `:3642`). CORRECTED AT REVIEW: this plan's own four coordinates are ALREADY STALE TOO (it said `:4857`/`:6379` and `:2517`/`:3643`), which proves the plan's own point better than its prose does, and there are FOUR MORE callers in tests (`tests/test_oc_runipd.py:2004`, `:2074`, `tests/test_reporting_contract.py:517`, `:626`), so the honest claim is one PRODUCTION caller per host rather than one caller.
  THE GATE IS NOT THE SAME ON BOTH HOSTS, AND THIS PLAN'S COST ARGUMENT DEPENDS ON GETTING THAT RIGHT (review, F-12). This plan says the caller is "reached only when `validate` is on", which is true of oc and FALSE of agy. Measured: oc gates on `validate` whose parser default is `False`; agy has NO `--validate` flag at all and gates on `not (no_verify or no_audit)` whose default is `False`, so THE IN-RUN VERIFIER IS ON BY DEFAULT ON AGY and off by default on oc. `tm2cz8`'s own Concern states this in as many words ("the two shipped hosts want OPPOSITE defaults, deliberately and on measured grounds"). So "nobody currently passes `--validate`" describes oc only, and on agy the verifier already runs unasked.
  THE THREE SITUATIONS THAT COST SOMETHING ALL HAPPENED IN THIS REPOSITORY, and the item names them concretely: a run executed with validation OFF, which is the current OPENCODE default by the maintainer's measured 2026-08-31 ruling, so a later independent opinion requires re-executing an already-`executed` plan; an item that reached `substantially-complete` because finalize refused (`nna8yz` in run `run-20260905T211011Z-3780617`, 21.80 dollars of work, finalize refused for a missing begin receipt), where an independent verifier is exactly what a human wants before deciding whether to trust the lane; and six lanes integrated BY HAND during recovery on 2026-09-05, validated by the full suite but never by an independent verifier, with no way to add that signal after the fact. NOTE AT REVIEW: `nna8yz` is now `- Status: executed` in `executed/`, recovered and merged on 2026-09-08, so the motivating case is HISTORICAL rather than live. It remains a real example of the gap and it is now also an example of the alternative route (hand recovery) being taken instead, which is evidence about demand that OQ-01 must weigh.
  ITS VALUE IS CONDITIONAL ON WORK THAT IS NOT DONE, AND THE ITEM SAYS SO EXPLICITLY. The item's own sequencing recommendation is "do `h7qsje` first", reasoning that if per-model verification is wired and a weaker model runs with validation ON, "the in-run verifier covers most of the need and this verb becomes a recovery tool rather than the primary path. Building it first risks adding a surface nobody invokes, for the same reason nobody currently passes `--validate`." THE PRECONDITION HAS PARTLY LANDED SINCE AUTHORING (review, F-13): `tm2cz8` is now `- Status: executed` in `executed/` (this plan says `approved` in `pending/`), and `ybkmzp` is now `reviewed` with `- Readiness: go-pending-approval` (this plan says `to-review`). So the gate is closer than the plan states but STILL UNMET, since `ybkmzp` is the child that actually wires the resolved decision into both drivers and it awaits human approval, not review. The sibling plan agrees: `ybkmzp`'s own Deferred section names "A STANDALONE RE-VERIFY VERB for an already-executed plan. Backlog `7u9kbm`, deliberately sequenced after this and inheriting the same cost question."
  SO THIS PLAN IS AUTHORED AS A GATED DESIGN, NOT A BUILD, and its first deliverable is the answer to whether it should exist. The item lists four things to decide "none of which the repository can settle alone", and the fourth is whether the verb is wanted at all given the economics: the maintainer's measured finding is that on the strong executor the verifier added only nits for roughly 33 percent extra cost. A plan that built the verb without answering that would be spending money to add a surface whose in-run twin is already switched off by default.
  ONE CONSTRAINT IS ABSOLUTE AND MUST SHAPE ANY IMPLEMENTATION: reuse `build_verifier_prompt` and the existing outcome schema. The item states it and gives the reason: "It must NOT be a second implementation ... or the two verifiers will drift and neither can be trusted (the same argument `wlxkoz` makes about not building a second completion checker)."
  BUT THE EXISTING PROMPT CANNOT BE REUSED VERBATIM FOR AN EXECUTED PLAN, AND THIS IS THE CENTRAL DESIGN COLLISION THIS PLAN DID NOT SEE (review, F-14, BLOCKER). Read at review, the prompt's requirement 4 is titled "In-Scope Fixes" and instructs the agent: "If you discover safely correctable defects, regressions, or missing test cases within the approved scope, fix them, re-run validation, and commit path-scoped". Its requirement 1 instructs it to "Inspect the git commits and working tree diffs produced for this IPD". So the existing verifier is a FIX-AND-COMMIT turn against a live worktree, not a read-only opinion. Pointing it at an already-`executed` plan therefore authorizes exactly what this plan's own Scope excludes ("EXCLUDES ... any change to what an `executed` plan's record says") and what AGENTS.md forbids ("Do NOT add commits to a plan already in `.aw/records/plans/executed/`; close a post-execution gap with a new corrective IPD"). THE CONSTRAINT AND THE GOAL ARE THUS IN DIRECT TENSION: reuse the prompt unchanged and the verb can commit to history behind an immutable plan; change the prompt and it is no longer the same prompt. E-06 is added to resolve this FIRST, because every later decision depends on which way it goes, and OQ-05 escalates the part that is not the executor's to decide.
  THERE ARE ALREADY TWO PROMPTS, NOT ONE, WHICH MAKES "REUSE THE EXISTING PROMPT" AMBIGUOUS (review, F-15). `oc_runipd.build_verifier_prompt` and `agy_runipd.build_verifier_prompt` are SEPARATE 68-line functions that diff in 26 lines: the host name ("fresh OpenCode session" versus "fresh Antigravity session"), the test invocation (`python3 -m pytest` versus "using `run_command`"), and notably oc's fix instruction ends "Never push" while agy's OMITS that clause. So the drift the item warns about has already happened, and a standalone verb must say WHICH host's prompt it composes rather than treating "the existing prompt" as a single object.
- Scope: Decide whether a standalone re-verify verb should exist and, if so, exactly what it verifies against and what it may write; implement only what that decision authorizes, reusing the EXISTING verifier prompt and outcome schema rather than writing a second verifier. EXCLUDES changing the in-run verifier, changing the `validate` default, and any change to what an `executed` plan's record says.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/runner_shared.py, .aw/records/specs, tests/test_standalone_verify.py
- Item-Dependencies: executed:ybkmzp
- Status: executed
- Readiness: go-pending-approval
- Set: reverify
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: mp289j
- From-Backlog: 7u9kbm

## Workflow history
- 2026-09-20 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: mp289j verified (set reverify, attempt 1). [Scope reconciliation - out-of-scope agent_workflows/agy_runipd.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_defect_report.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_oc_runipd.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_runner_stop_triggers.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_runner_telemetry_integration.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_rununify_build_parser.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_rununify_main.py: changed by the plan's approved execution (auto-reconciled by aw oc run)]
- 2026-09-20 executed (opencode its_direct/pt3-claude-opus-5-1m-us, run `run-20260920T035838Z-1819729` position 9): BUILD outcome per OQ-01. Added `aw oc run audit <id6>`, reusing the ONE shared `build_verifier_prompt` via a DEFAULTED `audit` mode (so the in-run prompt is byte-identical) and the existing verification outcome schema plus `diff_basis`/`findings_filed`. Spec `i4gpto` records the four reserved decisions. All six E-items performed, all six V-items verified with pasted evidence. Commit `807fdfd6`, 14 files, nothing pushed. BARE SUITE: before `1 failed, 7273 passed, 3 skipped, 2 xfailed`; after `1 failed, 7301 passed, 3 skipped, 2 xfailed`; FAILING NODE SET AFTER MINUS BEFORE IS EMPTY, and the one shared node is proven ENVIRONMENTAL (`43 passed` under `env -u OPENCODE_CONFIG_CONTENT`).
  THIS PLAN'S CENTRAL PREMISE WAS STALE AND A REVIEWER SHOULD KNOW IT FIRST. F-15 and the Concern assert TWO 68-line `build_verifier_prompt` bodies differing in 26 lines; `rununify` has since collapsed them into ONE definition (`runner_shared.py:12973`) with four-line host delegations. That resolves E-06's "which host's prompt" to the shared composer and makes route (a) far cheaper than priced, WITHOUT breaching the deliberate `agy_runipd.py` fence, since no driver prompt code changed. The plan's four line citations were stale for the fourth consecutive measurement, as its own F-2 predicted.
  BASE CENSUS RE-MEASURED on the current tree: 17 of 561 executed plans retain a `base_head` receipt, 544 do not, and `nna8yz`/`tm2cz8`/`ybkmzp` are all receipt-ABSENT, so `diff_basis: none` is the designed primary path exactly as the maintainer's OQ-01 withdrawal implies.
  THREE DEFECTS FOUND AND FILED WITH DURABLE CARRIERS, as OQ-01 requires: `2jtsup` (`new_run_id` collides within one second, so two audits shared a directory; worked around locally with an atomic `mkdir(exist_ok=False)` loop), `hblsqo` (`run_opencode` opens the attempt log without creating `sessions/`, killing a new caller at launch after a lane is allocated), and `5zyuc8` (nine tests pinned census COUNTS as proxies for invariants and so fired on a correctly-wired new call site; all nine restated as invariants, none relaxed). Also reported, not filed: backlog `kyb0v5` is now partly stale because agy DOES register `--validate`, left to its owner per OQ-01's "This plan may NOT absorb that fix".
  NOT FINALIZED BY THIS TURN, BY DESIGN: `aw ipd finalize` refused with `AW-LIFECYCLE-ROLE-001` because the runner owns begin/finalize for a managed lane. Left ready for the driver: pre-transition lint clean at exit 0, and the begin receipt's `frozen_region_digest` verified to MATCH the plan's current text. The finalize needs `--scope-reason` for the nine undeclared paths now enumerated in the Scope check above.
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-10 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: `plan_readiness.has_unresolved_blocking_question` -> False; `review_findings.subject_gating_blocks` -> empty; `plan_readiness.newest_verdict` polarity -> positive (not negative). Specifically, both blocking questions (OQ-01 build the audit, OQ-05 fix code but never the plan record) were answered on 2026-09-10, and its prose verdict is POSITIVE. Performed at HEAD `5692797e` at the maintainer's explicit instruction of 2026-09-10, who was shown that 12 of 15 `no-go` plans were held by stale bookkeeping and chose to have them fixed with evidence recorded rather than re-reviewed. This is the SECOND such cleanup in one session; the durable fix is plan `qhy3i3` E-07, authored and awaiting approval. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-09 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-801..PR-808; readiness `no-go`. Record: `.aw/records/reviews/20260908-reverify-01-mp289j-run-the-existing-verifier-prompt-against-an-already-executed.review.md`. `aw ipd lint --phase author` reported only the pre-existing blocking OQ-01 before semantic review, and after revision reports exactly two `IPD-Q501` (OQ-01 plus the new OQ-05), which is the gate working as designed. DISCLOSURE: same agent/model authored this plan, so this is a SELF-REVIEW, and its value rests on EXECUTING its claims rather than re-reading them. TEN things were run: the verifier prompt was READ IN FULL and both hosts' versions diffed; both gate expressions and both parser defaults were parsed; `build_verifier_prompt` was called with a synthetic item/state; every one of the 469 `executed/` plans was checked for a surviving `base_head` receipt and each survivor's base tested for ancestry; the receipt-consuming `unlink` was located; `git check-ignore`/`git ls-files` were run against the runs tree; `review_findings.SUBJECT_TYPES` was printed and the review corpus counted; `aw runs --help` was read; four sibling statuses were re-read; and the bare suite was run.
  THE HEADLINE DEFECT IS A CONSTRAINT COLLISION THE PLAN NEVER SAW (PR-801, BLOCKER). The prompt this plan is REQUIRED to reuse verbatim instructs the agent to "fix them, re-run validation, and commit path-scoped" and to inspect "working tree diffs". Pointed at an `executed` plan that authorizes commits behind an immutable artifact, which this plan's own Scope excludes and AGENTS.md forbids. So the item's no-second-implementation rule and the immutability rule cannot both be honored by naive reuse; a new E-06 resolves it first and blocking OQ-05 escalates the part that is not the executor's to decide. SECOND (PR-802, HIGH): the plan's cost argument rests on the verifier being off, but the two hosts have OPPOSITE defaults, and it is ON BY DEFAULT ON AGY, which registers no `--validate` at all. THIRD (PR-803, HIGH): the base the verb would verify against is GONE for 453 of 469 executed plans because clean finalize unlinks the receipt, including both of this plan's own motivating examples, so the reachability question this plan deferred is now answered and answered badly for the feature. Also fixed: the reviews tree cannot take a verdict without amending a CLOSED `Subject-Type` vocabulary (PR-804); the run surface has a documented read-only/writing split the verb fits neither half of (PR-805); "one caller per host" omits four test callers that usefully prove the prompt composes from synthetic inputs (PR-806); three sibling statuses and the suite baseline were stale, including this plan's own four line numbers going stale in one day (PR-807); and `nna8yz`, the named 21.80 dollar motivating case, has since been resolved by hand recovery without this verb (PR-808).
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `7u9kbm` as a GATED DESIGN plan, honoring the item's own sequencing recommendation rather than overriding it. Every citation re-verified by SYMBOL and found STALE in the item: `build_verifier_prompt` is at `oc_runipd.py:4857` (item said `:4725`) and `agy_runipd.py:2517` (item said `:2290`), with its single callers at `:6379` and `:3643` (item said `:6230`/`:3409`). The one-caller-per-host claim itself is TRUE and re-measured. THE SEQUENCING PRECONDITION IS UNMET, which is why this carries a dependency edge rather than being buildable now: the item says "do `h7qsje` first", and while `h7qsje` is `done` as an ITEM, the plans it graduated into are not finished (`tm2cz8` is `approved` in `pending/`; `ybkmzp`, the child that actually wires the decision into both drivers, is only `to-review`). Sibling plan `ybkmzp` independently agrees, naming this item as "deliberately sequenced after this and inheriting the same cost question". This plan therefore carries `Item-Dependencies: executed:ybkmzp` and a BLOCKING question on whether the verb is wanted at all, since the maintainer's measured finding is that the verifier added only nits for ~33 percent cost on the strong executor, and the in-run twin is currently off by default.

## Goal

Give a human a way to buy an independent opinion on work that is already done, or a recorded decision that this repository deliberately does not offer one, instead of leaving an expensive lane unverifiable and the question unanswered.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the gap and the precondition

- [x] E-01 RE-MEASURE THE GAP AND THE SEQUENCING PRECONDITION BY SYMBOL, and write both down before designing anything.
  THE GAP: locate `build_verifier_prompt` in BOTH drivers by NAME and count its callers, DISTINGUISHING production callers from test callers. Measured at review: ONE production caller per host (`oc_runipd.py:6586`, `agy_runipd.py:3642`) plus FOUR in tests (`tests/test_oc_runipd.py:2004`, `:2074`, `tests/test_reporting_contract.py:517`, `:626`). The test callers matter to the design rather than being noise: they prove the prompt composes from a SYNTHETIC `item`/`state`/`run_dir`, which is exactly what a standalone caller would have to supply. Do not trust this plan's line numbers OR the item's: measured at review, this plan's own four coordinates were already stale, and both files are under concurrent edit by live runs.
  MEASURE THE GATE PER HOST RATHER THAN ASSUMING ONE GATE. This plan said the caller is reached "only when `validate` is on", which holds for oc and NOT for agy. Read both gate expressions and both parser defaults yourself. Measured at review: oc gates on `validate` (parser default `False`, so the verifier is OFF by default) and agy has no `--validate` at all, gating on `not (no_verify or no_audit)` with default `False`, so the verifier is ON by default there. This asymmetry is the whole basis of the cost argument in OQ-01, so getting it wrong mis-answers the plan's blocking question.
  THE PRECONDITION: check whether `ybkmzp` has EXECUTED, since that is the child that wires the per-host verification decision into both drivers and is the thing the item's "do `h7qsje` first" recommendation actually depends on. `h7qsje` being `done` as a backlog ITEM is NOT the same as the work being landed, and confusing the two is exactly how a sequencing recommendation gets ignored. Measured at review the gate had PARTLY closed since authoring: `tm2cz8` is now `executed`, and `ybkmzp` is `reviewed` with `- Readiness: go-pending-approval`, awaiting human approval rather than review. Read both statuses again; they are moving.
  IF `ybkmzp` HAS NOT EXECUTED, STOP HERE AND REPORT. Task groups 2 and 3 must not be performed: the item's whole cost argument is that with per-model verification wired, a weaker model runs with validation ON and the in-run verifier covers most of the need, making this verb a recovery tool rather than a primary path. Building it before that lands risks "adding a surface nobody invokes". THE STOP IS ON `ybkmzp` REACHING `executed`, NOT ON IT BEING APPROVED OR MERELY REVIEWED; the declared `- Item-Dependencies: executed:ybkmzp` says the same thing and the runner enforces it, so a partly-closed gate is still a closed gate.
  - Depends on: none
  - Expected outcome: a symbol-cited statement of the PRODUCTION caller count per host, the per-host gate expression and parser default measured separately, and `ybkmzp`'s status read at execution time, with an explicit STOP if it is not `executed`.
  - Execution state: performed

### Task group 2: answer the four questions the item reserved

- [x] E-06 RESOLVE THE PROMPT-REUSE COLLISION BEFORE ANY OTHER DESIGN QUESTION, because every later answer depends on it and this plan was authored without seeing it (F-14, F-15).
  THE COLLISION, MEASURED: the prompt this plan is required to reuse verbatim instructs the agent to FIX AND COMMIT ("If you discover safely correctable defects ... fix them, re-run validation, and commit path-scoped") and to inspect "working tree diffs produced for this IPD". Pointing that at an `executed` plan authorizes commits behind an immutable artifact, which this plan's own Scope excludes and AGENTS.md forbids in as many words. So the item's "must NOT be a second implementation" and this plan's "must not change an executed plan" cannot BOTH be honored by naive reuse. READ THE PROMPT YOURSELF before deciding; do not take this paragraph's quotation on trust.
  THE THREE HONEST ROUTES, and each has a different cost. (a) PARAMETERIZE the existing prompt so the fix-and-commit and worktree-diff clauses are conditional on a mode, keeping ONE composer and no second verifier; this edits a function whose exact output is pinned by the reporting-contract parity tests, so it must keep those passing. (b) REUSE IT UNCHANGED and constrain the ENVIRONMENT instead, so a fix has nowhere to land (a detached read-only checkout, no push, changes discarded), accepting that the prompt still ASKS for something the run will not honor, which is the kind of instruction-versus-reality gap this repository treats as a defect. (c) DECIDE THE VERB CANNOT REUSE THIS PROMPT and therefore should not exist in this shape, which is a legitimate not-wanted outcome and feeds OQ-01.
  SAY WHICH HOST'S PROMPT, since there are TWO. Measured: the two `build_verifier_prompt` bodies diff in 26 lines including the host name, the test-invocation instruction, and the presence of "Never push" (oc has it, agy does not). Under route (a) state whether both are parameterized or only one; under any route, a claim of "reusing the existing prompt" that does not name the host is not checkable.
  DO NOT WEAKEN THE PARITY TESTS TO MAKE ROOM. `tests/test_reporting_contract.py` asserts both prompts carry the reporting contract byte-identically and that no third copy of that prose exists in the tree. If a chosen route would fail those, that is a finding to report, not a test to relax.
  - Depends on: E-01
  - Expected outcome: a written, evidence-cited choice among the three routes with the host named, the parity tests confirmed still passing under the chosen route (or the conflict reported), and no second verifier composer introduced.
  - Execution state: performed

- [x] E-02 ANSWER WHAT THE VERB VERIFIES AGAINST, which is the item's question 1 and the one that decides whether the verb is even coherent.
  THE PROBLEM STATED PRECISELY: the in-run verifier reads the execution outcome JSON for THAT attempt, in the worktree, immediately after the work. For a plan executed weeks ago on a different HEAD, "the work" is a historical diff, and verifying it against TODAY's tree answers a different question. The item's own lean is "probably needs an explicit base (the plan's recorded `base_head`) rather than an implicit one".
  THE REACHABILITY QUESTION IS NOW ANSWERED AND THE ANSWER IS THAT THE BASE IS USUALLY GONE (review, F-16). Measured across the whole tree at review: of 469 plans in `executed/`, exactly 16 still have a readable begin receipt carrying `base_head` and 453 do NOT. The mechanism is confirmed at `ipd_lifecycle.py:2832`, where the clean finalize path calls `receipt_path_for(...).unlink()` under the comment "Consume the begin receipt (the transaction is cleanly complete)". So the item's preferred base is unavailable for roughly 97 percent of executed plans, INCLUDING both of this plan's own motivating examples (`nna8yz` and `tm2cz8` both measured receipt-ABSENT). Of the 16 that remain, all 16 bases ARE still ancestors of HEAD, so when a receipt survives it is usable. RE-MEASURE THESE NUMBERS rather than quoting them; the population changes with every finalize.
  SO E-02'S REAL JOB IS TO CHOOSE AMONG BASES THAT ACTUALLY EXIST, not to confirm the preferred one. The honest candidates, each with a stated cost: the surviving receipt when there is one (correct but available for a small minority, and by construction only for plans whose finalize did NOT cleanly complete, which is a biased sample); an OPERATOR-SUPPLIED base, which works universally and moves the correctness burden to the human; the plan's own lifecycle commit, discoverable from tracked git history rather than gitignored state, which is durable but identifies the finalize rather than the execution baseline; or the plan's `Workflow history` executed line, which is tracked but prose. State which, and state plainly what a verdict MEANS when the base had to be guessed.
  BEWARE THE SIBLING MEASUREMENT: a plan's run record lives under `.aw/records/runs/`, which is gitignored (confirmed at review: `git check-ignore` resolves it to `.aw/.gitignore:14`, and `git ls-files` counts ZERO tracked files there against 143 local run directories) and absent from a lane worktree, and `h9cn0y`'s review measured that finalize receives no run id at all. Any design reading a run record must state where that record is guaranteed to exist. Note the verifier prompt EMBEDS two `run_dir`-relative outcome paths, so a standalone caller must decide what those paths point at when no run directory exists.
  - Depends on: E-06
  - Expected outcome: a written answer for what the verb compares against, CHOSEN from bases proven reachable at execution time with the 469-versus-16 measurement re-taken, plus an explicit statement of what a verdict means when the original base is unavailable.
  - Execution state: performed

- [x] E-03 ANSWER WHAT THE VERB MAY WRITE, which is the item's question 2, and treat the constraint as hard rather than negotiable.
  THE CONSTRAINT: an `executed` plan must NOT be edited in place (repository policy, stated in AGENTS.md), so a negative verdict cannot silently reopen it. The item's own answer is that it "should produce a corrective-IPD recommendation or a durable finding, not a status change".
  DECIDE WHERE THE VERDICT LANDS, since "a durable finding" needs an address. Candidates: a run record under `.aw/records/runs/` (gitignored, so invisible to a reviewer and absent from a clone), a review record under `.aw/records/reviews/`, or a new record type. State the trade: a gitignored verdict cannot be cited in a plan; a tracked one becomes permanent history for a machine-generated opinion.
  THE REVIEW-RECORD CANDIDATE IS MORE CONSTRAINED THAN THIS PLAN THOUGHT, AND THE CONSTRAINT IS ENFORCED (review, F-17). Two corrections. FIRST, "only `/plan-review` produces records today" is now FALSE: measured, 127 review records exist and several carry `Subject-Type: spec` (for example `20260906-77tr3o-01-77tr3o-...review.md`), so `spec-review` writes them too. SECOND and decisive, `Subject-Type` is a CLOSED vocabulary of exactly `('ipd','spec')`, verified live as `review_findings.SUBJECT_TYPES`, and the README states that an unrecognized value is a PARSE ERROR (`REV-M101`/`REV-M102`) and that a new type is added "by amending the vocabulary in `review_findings.SUBJECT_TYPES` and the checker's per-type resolution together, never by writing a novel value into a record". So a verification verdict filed there would either masquerade as an `ipd` REVIEW (a different kind of judgement, made by a different actor, at a different lifecycle point) or require amending a closed vocabulary plus its checker, which is work this plan has not scoped and whose path is NOT in `- Scope-Paths:`. Choose deliberately and price that amendment if you choose it.
  A THIRD CANDIDATE THE PLAN DID NOT LIST, worth considering because it needs no new vocabulary: the plan's own `## Workflow history` is tracked, append-only, and already the place a workflow records that it touched an artifact. Its cost is that appending to an `executed` plan's file is exactly the in-place edit the immutability policy forbids, so it is probably ruled out; say so explicitly rather than leaving it unconsidered, since a reader will otherwise ask.
  A NEGATIVE VERDICT MUST NOT BE SILENTLY DISCARDABLE EITHER. If the verb writes nowhere durable, an operator can run it, dislike the answer, and run it again; that is the shape of a check nobody can trust. Say what stops that, or record that nothing does.
  BE HONEST ABOUT WHAT IS ACHIEVABLE HERE, since an over-promise is worse than the gap. The verb is invoked BY the operator on demand, so nothing can prevent a human from simply not running it, and nothing can prevent them running it twice. The achievable property is narrower and worth stating precisely: that each run leaves a durable trace, so a SECOND run does not erase the first. Whatever destination E-03 picks, say whether it APPENDS or OVERWRITES, because that single property is the whole difference between "re-run until happy" being visible and being silent.
  - Depends on: E-02
  - Expected outcome: a decided, addressed destination for the verdict that respects the immutability policy, with the tracked-versus-gitignored trade stated, the closed `Subject-Type` vocabulary priced if the reviews tree is chosen, and an explicit append-versus-overwrite answer to the re-run hazard.
  - Execution state: performed

- [x] E-04 ANSWER WHETHER IT NEEDS A LANE, which is the item's question 3 and is a contention question with a measured history.
  THE ISSUE: the in-run verifier runs in the worktree. A standalone one has no lane, and running it against the primary checkout while other agents work there is the contention problem `p8ni63`/`5wdoze` exist for.
  NOTE THE LANDSCAPE HAS MOVED IN THIS PLAN'S FAVOUR: isolation is now the DEFAULT for execute turns (confirmed at review, `isolate_worktree` parses True on BOTH hosts), and `worktree_lease` already owns allocation and teardown. So allocating a lane for a standalone verification is the consistent choice rather than a novel one. CORRECTED: this plan says `3i0aaz` "graduated the remaining ungated dirty-base cases"; measured, `3i0aaz` is a PLAN at `- Status: to-review` in `pending/`, so those cases are identified and NOT yet guarded. Do not lean on it as landed work.
  BUT A VERIFIER IS READ-MOSTLY, so state whether a full lane is warranted or whether a read-only checkout of the recorded base is both cheaper and more correct. The verb's job is to form an opinion, not to change the tree, and a lane whose changes are then discarded is a lane that mainly costs time.
  THIS ANSWER IS NOW COUPLED TO E-06 AND MUST NOT BE DECIDED INDEPENDENTLY. If E-06 chose route (b) (reuse the prompt unchanged and constrain the environment), then the tree decision IS the enforcement mechanism for immutability, and a writable lane would defeat it; if route (a) (parameterize the prompt), a read-only checkout becomes a cheap belt-and-braces rather than the primary guard. Say which case you are in, because "what the verifier is permitted to write" has a different answer in each.
  - Depends on: E-03
  - Expected outcome: a decided answer on lane allocation with its reasoning, consistent with isolation being the default, cross-referenced to E-06's chosen route, and an explicit statement of what the verifier is permitted to write into whatever tree it gets.
  - Execution state: performed

### Task group 3: build only what the ruling authorizes

- [x] E-05 IMPLEMENT THE DECISION, REUSING THE EXISTING PROMPT AND SCHEMA, OR RECORD THAT THE VERB IS NOT WANTED. Both are real outcomes.
  UNDER A BUILD OUTCOME: add the verb calling the EXISTING `build_verifier_prompt` (as E-06 resolved it, for the host E-06 named) and writing the EXISTING outcome schema. Do NOT write a second verifier: the item is explicit and cites `wlxkoz`'s argument against a second completion checker. Prefer siting shared logic in `runner_shared.py`, since `rununify` (`5e4sb6`) exists to de-duplicate the two drivers and adding a host-specific copy would enlarge that backlog.
  DECIDE WHICH NOUN THE VERB HANGS OFF, AND MIND THE EXISTING READ/WRITE SPLIT (review, F-18). The CLI already partitions this surface deliberately: `aw runs` is documented in its own help as "the READING half of the run surface ... Read-only, except the opt-in 'repair' verb", while `aw run` is "the WRITING half". A verb that LAUNCHES A MODEL TURN and writes a verdict is not read-only, so filing it under `aw runs` would violate that stated contract, yet it is also not a run-ledger transaction like `start`/`record`/`cancel`/`finalize`. Name the noun and justify it against those two docstrings; note spec `25kzda` §1.3's "Audit only" row already routes audit to `aw runs verify-ledger` or `run resume`, so a third audit spelling needs a reason that row does not already cover.
  DO NOT WIRE THE AGY HOST unless the decision requires it. `agy_runipd.py` imports heavily from `oc_runipd.py` and the two are mid-unification; a second host surface doubles the review burden for a verb whose value is still conditional. If only one host gets it, SAY SO in the docs rather than letting a reader infer parity.
  UNDER A NOT-WANTED OUTCOME: write the decision into a spec, including the economics that decided it, so the next person who wants this finds the answer rather than re-deriving it. That is a genuine deliverable: the item's question 4 asks "Is it wanted at all, given the economics?", and a recorded no is more valuable than an unused verb.
  DO NOT CHANGE THE `validate` DEFAULT under either outcome. That default is a measured maintainer ruling from 2026-08-31, and `ybkmzp`/`tm2cz8` own the per-host decision surface.
  - Depends on: E-04
  - Expected outcome: either the verb, reusing prompt and schema with no second verifier and no unrequested second host, or a recorded spec decision that it is not wanted with the economics stated; the `validate` default untouched either way.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE VERIFIER IS REAL AND SINGLE-SITED IN PRODUCTION: `build_verifier_prompt` at `oc_runipd.py:4913` and `agy_runipd.py:2456`, each with exactly ONE production caller (`:6586`, `:3642`) inside the execute path, plus FOUR test callers. The test callers prove the prompt composes from a SYNTHETIC `item`/`state`/`run_dir`, which is what a standalone caller would supply.
- THE GATE DIFFERS BY HOST AND THE DEFAULTS ARE OPPOSITE: oc gates on `validate` (default `False`, verifier OFF); agy has no `--validate` and gates on `not (no_verify or no_audit)` (default `False`, verifier ON). `tm2cz8`'s Concern says so in as many words. "Nobody passes `--validate`" is an OPENCODE statement.
- THE EXISTING PROMPT IS A FIX-AND-COMMIT TURN, NOT A READ-ONLY OPINION: its requirement 4 says "fix them, re-run validation, and commit path-scoped" and its requirement 1 inspects "working tree diffs". That collides head-on with re-verifying an immutable `executed` plan.
- THERE ARE TWO PROMPTS, NOT ONE: the two `build_verifier_prompt` bodies diff in 26 lines (host name, test invocation, and oc's "Never push" which agy lacks). "Reuse the existing prompt" must name a host.
- LINE NUMBERS IN BOTH THE ITEM AND THIS PLAN GO STALE FAST: the item's four coordinates were stale at graduation and this plan's four were stale at review, one day later. Re-locate by symbol, always.
- THE SEQUENCING PRECONDITION IS STILL UNMET BUT HAS MOVED: `tm2cz8` is now `executed`; `ybkmzp` is `reviewed` with `- Readiness: go-pending-approval`, awaiting approval. The declared dependency is on `executed:ybkmzp`, so it remains closed. Item status is not landed work.
- THE SIBLING PLAN AGREES INDEPENDENTLY: `ybkmzp`'s Deferred section names this item as "deliberately sequenced after this and inheriting the same cost question".
- NO SECOND VERIFIER: reuse `build_verifier_prompt` and the existing outcome schema, per the item and per `wlxkoz`'s argument against a second completion checker.
- RUN RECORDS AND RECEIPTS ARE GITIGNORED: `.aw/records/runs/` resolves to `.aw/.gitignore:14` and has ZERO tracked files against 143 local run directories; `.aw/state/` resolves to `.gitignore:60`. Both are absent from a clone and from a lane worktree, and `h9cn0y`'s review measured that finalize receives no run id.
- THE RECORDED BASE IS GONE FOR ALMOST EVERY EXECUTED PLAN: 16 of 469 `executed/` plans still have a receipt carrying `base_head`; 453 do not, because clean finalize UNLINKS it (`ipd_lifecycle.py:2832`). Of the 16 survivors all 16 bases are still ancestors of HEAD. Both of this plan's motivating examples (`nna8yz`, `tm2cz8`) are receipt-ABSENT.
- AN `executed` PLAN IS IMMUTABLE: a negative verdict cannot reopen it; the honest route is a corrective IPD. AGENTS.md states it directly, which is what makes the prompt's fix-and-commit clause a collision rather than a nuance.
- ISOLATION IS THE DEFAULT for execute turns (`isolate_worktree` parses True on BOTH hosts), so allocating a lane is consistent rather than novel. NOTE `3i0aaz` is a `to-review` PLAN, not landed work.
- `Subject-Type` IS A CLOSED VOCABULARY, `('ipd','spec')`, verified live as `review_findings.SUBJECT_TYPES`; an unrecognized value is a parse error (`REV-M101`/`REV-M102`) and a new type requires amending the vocabulary AND the checker together. Also, 127 review records exist and some are `Subject-Type: spec`, so "only `/plan-review` writes records" is no longer true.
- THE RUN SURFACE IS SPLIT BY DESIGN: `aw runs` is "the READING half ... Read-only, except the opt-in 'repair' verb"; `aw run` is "the WRITING half". A model-launching verb fits neither cleanly, so the noun choice needs justifying.
- `rununify` (`5e4sb6`) EXISTS TO DE-DUPLICATE THE DRIVERS, so shared logic belongs in `runner_shared.py`.
- Both runner files are under concurrent edit. Suite runs BARE.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the gap is real and re-measured | `build_verifier_prompt` has exactly ONE PRODUCTION caller per host, inside the execute path, so verification is available only as the turn after an execution. CORRECTED at review: there are also FOUR test callers, and the gate is NOT `validate` on both hosts (see F-12). | `oc_runipd.py:4913`/`:6586`; `agy_runipd.py:2456`/`:3642`; four test call sites |
| F-2 | HIGH | citations go stale within a day | The item's four coordinates were stale at graduation, and THIS PLAN's four replacements were already stale at review one day later (`:4857`->`:4913`, `:6379`->`:6586`, `:2517`->`:2456`, `:3643`->`:3642`). | located by symbol at review |
| F-3 | HIGH | the precondition is UNMET but has MOVED | It says "do `h7qsje` first". Re-measured at review: `tm2cz8` is now `executed` (this plan said `approved` in `pending/`) and `ybkmzp` is `reviewed` with `- Readiness: go-pending-approval` (this plan said `to-review`). The declared dependency is `executed:ybkmzp`, so the gate is still closed. | statuses read at review |
| F-4 | HIGH | the sibling plan independently sequences it after itself | `ybkmzp`'s Deferred section: "A STANDALONE RE-VERIFY VERB ... Backlog `7u9kbm`, deliberately sequenced after this and inheriting the same cost question." | `ybkmzp`'s Deferred section |
| F-5 | HIGH | the economics question is genuinely open | The maintainer's measured finding is that on the strong executor the verifier added only nits for ~33 percent cost, and nobody currently passes `--validate`. A verb inherits that. | the item's question 4 |
| F-6 | HIGH (raised at review) | the recorded base is GONE for almost every executed plan | MEASURED rather than suspected: 16 of 469 `executed/` plans retain a receipt carrying `base_head`; 453 do NOT, because clean finalize UNLINKS it. So the item's preferred base is unavailable for ~97 percent of the corpus, including BOTH of this plan's motivating examples. Of the 16 survivors, all 16 bases remain ancestors of HEAD, so a surviving receipt is usable; but survivors are by construction plans whose finalize did not cleanly complete, a biased sample. | `ipd_lifecycle.py:2832` (`unlink` under "Consume the begin receipt"); `read_receipt` called for all 469 |
| F-7 | MEDIUM | run records are unreachable from a clone or lane | `.aw/records/runs/` is gitignored (`git check-ignore` -> `.aw/.gitignore:14`; ZERO tracked files against 143 local run dirs) and absent from a lane worktree, and finalize receives no run id. The verifier prompt EMBEDS two `run_dir`-relative outcome paths, so a standalone caller must decide what they point at. | `h9cn0y` F-13; `git check-ignore -v`; `git ls-files` |
| F-8 | MEDIUM | the verdict has nowhere obviously correct to go | A gitignored verdict cannot be cited; a tracked one makes a machine opinion permanent history. See F-17: the reviews tree is more constrained than this plan assumed. | `.aw/records/reviews/README.md` |
| F-9 | MEDIUM | the contention question has moved favourably | Isolation is now the DEFAULT for execute turns on BOTH hosts, so allocating a lane for a standalone verification is consistent rather than novel. CORRECTED: `3i0aaz` is a `to-review` PLAN, not landed work, so the ungated dirty-base cases are identified and not yet guarded. | `isolate_worktree` parses True on both hosts; `3i0aaz` status read |
| F-10 | MEDIUM | a second implementation is forbidden | The item requires reusing `build_verifier_prompt` and the outcome schema, citing `wlxkoz`'s argument against a second completion checker (`wlxkoz` confirmed `executed`). See F-14/F-15 for why naive reuse is nonetheless impossible. | the item's "WHAT DONE LOOKS LIKE" |
| F-11 | LOW | the three motivating situations were all real, and one has since resolved | Validation off by default ON OC ONLY (F-12); `nna8yz` at `substantially-complete` after a refused finalize (21.80 dollars, run `run-20260905T211011Z-3780617`); six lanes hand-integrated 2026-09-05 with no independent verification. RE-MEASURED: `nna8yz` is now `executed`, recovered and merged 2026-09-08, so the case was resolved by hand recovery instead. That is evidence about demand which OQ-01 must weigh. | the item's own record; `nna8yz` status and history line read at review |
| F-12 | HIGH (added at review) | the in-run verifier default is OPPOSITE on the two hosts | This plan says the caller is reached "only when `validate` is on", true of oc and FALSE of agy. Measured: oc gates on `validate` (parser default `False`, verifier OFF); agy registers NO `--validate` and gates on `not (no_verify or no_audit)` (default `False`, verifier ON BY DEFAULT). `tm2cz8`'s Concern states the hosts "want OPPOSITE defaults, deliberately and on measured grounds". This matters because OQ-01's whole cost case rests on the verifier being unwanted, which is an oc-only observation. | both gate expressions read; both parsers' defaults parsed; `tm2cz8` Concern |
| F-13 | MEDIUM (added at review) | two sibling statuses in this plan are stale | `tm2cz8` is `executed`, not `approved` in `pending/`; `ybkmzp` is `reviewed` + `go-pending-approval`, not `to-review`. The conclusion (gate unmet) SURVIVES because the dependency is on `executed:ybkmzp`, but an executor reading "to-review" would misjudge how close the gate is. | both plan files read at review |
| F-14 | BLOCKER (added at review) | the prompt this plan must reuse tells the agent to FIX AND COMMIT | The existing verifier prompt's requirement 4 is "In-Scope Fixes": "If you discover safely correctable defects ... fix them, re-run validation, and commit path-scoped", and requirement 1 inspects "working tree diffs produced for this IPD". Pointing that at an `executed` plan authorizes commits behind an immutable artifact, which this plan's own Scope excludes and AGENTS.md forbids. So "reuse the prompt verbatim" and "never touch an executed plan" cannot both hold, and the plan never reconciles them. | the prompt body read in full; AGENTS.md immutability rule |
| F-15 | MEDIUM (added at review) | there are TWO verifier prompts, so "the existing prompt" is ambiguous | The two `build_verifier_prompt` bodies are separate 68-line functions differing in 26 lines: host name, test invocation (`python3 -m pytest` versus `run_command`), and oc's "Never push" which agy OMITS. A standalone verb must name which host's prompt it composes. | both bodies diffed |
| F-16 | MEDIUM (added at review) | the prompt composes fine from synthetic inputs, which HELPS this plan | `build_verifier_prompt` reads only `item['id6']`, `item['position']`, `item['setid']`, `state['run_id']` and two `run_dir`-relative paths. Called at review with a synthetic dict it produced a 4646-character prompt. So a standalone caller does NOT need a real run; it needs to decide what the two embedded outcome paths mean. | called live with a synthetic item/state; keys extracted by regex over the body |
| F-17 | MEDIUM (added at review) | the reviews tree cannot take a verdict without amending a closed vocabulary | `review_findings.SUBJECT_TYPES` is exactly `('ipd','spec')`, verified live; the README says an unrecognized value is a parse error and that a new type requires amending the vocabulary AND the per-type resolution together. Also 127 records exist including `Subject-Type: spec` ones, so this plan's "only `/plan-review` writes records" is stale. Filing a verification verdict there means either masquerading as a review or paying for a vocabulary amendment this plan has not scoped. | `SUBJECT_TYPES` printed; README `:172-176`; records counted |
| F-18 | MEDIUM (added at review) | the run surface has a documented read/write split the verb must respect | `aw runs` self-describes as "the READING half of the run surface ... Read-only, except the opt-in 'repair' verb"; `aw run` is "the WRITING half". A verb that launches a model turn and writes a verdict is read-only under neither description, and spec `25kzda` §1.3's "Audit only" row already routes audit to `verify-ledger`/`run resume`. The noun choice needs an argument. | `aw runs --help`; `cli.py:114`, `:122`, `:1691`; spec §1.3 |

## Proposed changes (ordered, validatable)

1. Re-measure the production caller count and per-host gate by symbol, and `ybkmzp`'s status, stopping if the precondition is unmet (E-01).
2. Resolve the prompt-reuse collision (the prompt says fix-and-commit; an executed plan is immutable) and name which host's prompt (E-06).
3. Decide what the verb verifies against, choosing from bases proven reachable rather than the mostly-absent receipt (E-02).
4. Decide where a verdict lands, respecting plan immutability, pricing the closed `Subject-Type` vocabulary, and stating append-versus-overwrite (E-03).
5. Decide the lane question consistently with isolation being the default and with E-06's chosen route (E-04).
6. Build the verb reusing prompt and schema under a justified noun, or record that it is not wanted with the economics (E-05).

## Deferred / out of scope (with reason)

- CHANGING THE IN-RUN VERIFIER's BEHAVIOR in any way. It works, it is the thing being reused, and altering it would put two changes in one review. QUALIFIED AT REVIEW: this exclusion cannot be absolute, because E-06 route (a) modifies the shared prompt COMPOSER, which the in-run verifier also uses. The line to hold is that the in-run turn's EFFECTIVE PROMPT AND BEHAVIOR must be byte-identical before and after; a mode parameter that defaults to the current text preserves that, and the reporting-contract parity tests are what prove it. Anything that changes what the in-run verifier actually receives is out of scope.
- CHANGING EITHER HOST'S VERIFICATION DEFAULT. A measured maintainer ruling from 2026-08-31, and the per-host decision surface belongs to `tm2cz8` (now `executed`) and `ybkmzp` (`reviewed`, awaiting approval). Note the defaults are OPPOSITE per host (F-12), so "the `validate` default" is not one thing; leave both alone.
  HONORED AND RE-CONFIRMED AT EXECUTION, with no outstanding obligation: both defaults were measured live AFTER the change (oc `validate_default=False`, agy `True`, both `provenance='shipped-default'`) and neither `runner_profiles.py` nor either host's `--validate` registration is in this plan's diff. NOTE ALSO that `ybkmzp` has since REACHED `executed`, so both named carriers are complete and nothing here awaits them. SEPARATELY: backlog `kyb0v5` ("agy validate flag missing") is now PARTLY STALE, because agy DOES register `--validate` (bare, at `agy_runipd.py:3900`); left to its owner to re-measure and close rather than absorbed here, exactly as OQ-01 directs.
- PER-ROLE OR PER-ACTION MODEL SELECTION for the standalone verifier. `kgpptv` owns the verifier-specific profile and `btot17` (graduated from `0k74my`) owns the general question, which carries its own blocking decision. A standalone verb must use whatever model resolution exists when it lands.
- WIRING THE AGY HOST, unless the decision requires it. The drivers are mid-unification (`5e4sb6`), and a second host surface doubles the review burden for a verb whose value is conditional. If only one host gets it, that must be DOCUMENTED, not inferred.
  HONORED IN SUBSTANCE, WITH ONE DELIBERATE DEPARTURE THAT IS NOT A DEFERRAL. The agy host gets NO launch path, NO second prompt, and NO second resolver: its binding is a REFUSAL exiting 2 and naming the OpenCode spelling. It does get the shared SUBPARSER DECLARATION, because `tests/test_rununify_build_parser.py` pins the two hosts' subparser sets to be identical and a verb that parses on one host while reporting "unknown command" on the other (with `--help` documenting it) is a genuine surface fork. DOCUMENTED, not inferred: spec `i4gpto` R-10 states which host is implemented and why, and the refusal message itself says so to the operator. No obligation outstanding; implementing the agy launch path is a FUTURE option, not a debt, and needs no carrier because nothing is broken without it.
- ANY CHANGE TO AN `executed` PLAN'S RECORD. Immutable by policy; a negative verdict produces a corrective-IPD recommendation, never an in-place edit or a status change.
- FIXING THE MISSING-RECEIPT CASE that stranded `nna8yz`. That is `integearn`/`integpath` territory; this verb would make such a lane VERIFIABLE after the fact, not prevent the strand. STILL DEFERRED, and the named carriers remain the owners; `nna8yz` itself has since reached `executed` by hand recovery, so nothing is stranded today.
- RE-VERIFYING THE SIX HAND-INTEGRATED LANES from 2026-09-05. A use of the verb, not part of building or deciding it, and a maintainer's call about spending money on history. STILL DEFERRED BY DESIGN and deliberately CARRIER-FREE: this is an invitation to SPEND MONEY, not an obligation, so filing a backlog item would manufacture a debt the maintainer never incurred. The verb now exists, so the option is available on demand.

DEFECTS FOUND DURING EXECUTION, each with its own durable carrier as OQ-01 requires (three new backlog items, all filed with `aw backlog new`):

- `2jtsup` (bug, medium, blocks-release next): `runner_shared.new_run_id()` is second-granular (`run-<UTC seconds>-<pid>`), so two runs started within one second from one process SHARE a run directory and the second overwrites the first's state and outcomes. Measured directly. Worked around locally for this verb only, via an atomic `mkdir(exist_ok=False)` suffix loop; the shared helper is untouched because changing its format alters run ids repository-wide.
- `hblsqo` (bug, low, blocks-release next): `oc_runipd.run_opencode` opens the attempt log with `log_path.open("w")` without creating `sessions/`, so any caller that has not already built the full run-directory skeleton dies with `FileNotFoundError` AT LAUNCH, after the prompt is written and a lane allocated. Invisible until now because both pre-existing callers come from `initialize_run`. One-line fix available in the launcher; the agy twin should be checked for the same shape.
- `5zyuc8` (chore, medium): nine tests across five files asserted CENSUS COUNTS (launcher call sites, closure sizes, phase-declaration counts) as proxies for invariants, so adding ONE correctly-wired call site read as a regression while a badly-wired one would have produced the same number. All nine restated as the invariants they stood for; the general sweep is the carrier's work.

## Scope check

- AT EXECUTION (2026-09-20) THE SCOPE WAS EXCEEDED, DELIBERATELY AND IN THE WAY THIS SECTION ANTICIPATED. Recorded here before finalize rather than justified afterwards, per this section's own instruction. Declared paths, all used: `agent_workflows/runner_shared.py` (the shared composer's `audit` mode, `add_audit_parser`, `plan_audit_target`), `agent_workflows/oc_runipd.py` (the host binding), `.aw/records/specs` (new spec `i4gpto`), `tests/test_standalone_verify.py` (28 tests). UNDECLARED paths changed, each with its reason, and each needing a `--scope-reason` at finalize:
  1. `agent_workflows/agy_runipd.py` - the shared subparser declaration plus a REFUSING binding. This section says agy is undeclared BY DESIGN so that "a decision to parameterize BOTH hosts' prompts cannot be executed under this fence", and THAT FENCE WAS NOT BREACHED: no prompt code in either driver changed, because the composer is now shared and lives in a DECLARED file. What was added is a declaration and a refusal. The alternative (declaring on oc only) leaves two shipped tests red and creates a real one-host surface fork.
  2. `tests/test_rununify_build_parser.py`, `tests/test_runner_stop_triggers.py`, `tests/test_rununify_main.py` - PINNED TABLES updated to the new true surface (the subparser set, the flag partition, the shim set, the closure classification). These tables state in their own comments that a change must update them in the same commit and say why; that is what was done.
  3. `tests/test_oc_runipd.py`, `tests/test_defect_report.py`, `tests/test_runner_telemetry_integration.py` - five tests whose CENSUS COUNTS fired on a correctly-wired new call site, restated as the invariants they stood for. Nothing was relaxed; the general defect is filed as backlog `5zyuc8`.
  4. `.aw/records/backlog/open/` - three new items (`2jtsup`, `hblsqo`, `5zyuc8`), which OQ-01's resolution REQUIRES ("A FINDING MUST LAND IN A BACKLOG ITEM OR PLAN"), so this path is obligatory rather than optional.
  NOT TOUCHED, as promised: `agent_workflows/runner_profiles.py`, either host's `--validate` registration, `agent_workflows/review_findings.py`, and spec `25kzda` (whose Section 1.3 row is reconciled in the new spec's Section 6 rather than amended, so no approved spec was edited and no `Scope-Paths` spec declaration was needed).
- Over-scope: none as declared, but ONE PATH MAY BE MISSING and the executor must not discover it late. If E-06 chooses route (a) (parameterize the prompt), it edits `build_verifier_prompt`, whose byte-exact output is pinned by `tests/test_reporting_contract.py`; that file is NOT declared, so updating it costs a `--scope-reason` at finalize. If E-03 chooses the reviews tree and amends the closed `Subject-Type` vocabulary, that touches `agent_workflows/review_findings.py` plus the checker, also undeclared. Both are deliberately left undeclared because both are CONDITIONAL on a maintainer ruling this plan does not presume; if a ruling selects them, declare before editing rather than justifying afterwards.
- Note `agy_runipd.py` is undeclared BY DESIGN (see below), which under E-06 route (a) means a decision to parameterize BOTH hosts' prompts cannot be executed under this fence. That is intentional: it forces the one-host-or-both question to be answered explicitly rather than absorbed.
- Scope-Paths justification: `agent_workflows/oc_runipd.py` holds `build_verifier_prompt` and the single execute-path caller, so it is where a new entry point must attach under a build outcome (E-05); `agent_workflows/runner_shared.py` is the correct home for logic both hosts might share, since `rununify` exists to de-duplicate the drivers and a host-local copy would enlarge that backlog; `.aw/records/specs` is where the decision lands under EVERY outcome and is the whole deliverable under not-wanted; `tests/test_standalone_verify.py` is new and carries the build outcome's tests. `agy_runipd.py` is deliberately NOT declared: wiring the second host is excluded unless the decision requires it, and declaring it would invite a change this plan does not want. Under the not-wanted outcome the two `agent_workflows/` paths and the test file may finish UNCHANGED, which is the expected outcome and not an incomplete item.
- Under-scope, stated rather than left as `none`: this plan does not change the in-run verifier, the `validate` default, model routing, the agy host, any `executed` plan's record, the missing-receipt strand, or the six historical lanes. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. CORRECTED AT REVIEW: the `1 failed, 5648 passed` baseline is stale. Measured at review: `1 failed, 5929 passed, 3 skipped, 2 xfailed in 59.76s`, the single failure being `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which is ENVIRONMENTAL (a gitignored local `opencode-recovery/` dump in this checkout) and may be absent elsewhere. Measure your own baseline in the executing worktree and compare failing NODE IDS, never totals. Criterion: the failing node set AFTER minus BEFORE is EMPTY. Under the not-wanted outcome the suite should be untouched, which is the expected result rather than a missing test.
- NOTE THAT FAILING NODE IS IN THE FILE E-06 MAY TOUCH. `tests/test_reporting_contract.py` holds both the prompt-parity assertions and the environmental failure, so do not read a pre-existing environmental failure in that file as evidence your prompt change broke parity, and do not read a green parity assertion as evidence the environmental failure is fixed. Name the node ids.
- THE SYMBOL MEASUREMENTS (E-01): the PRODUCTION caller count per host located by NAME, both gate expressions with both parser defaults measured separately, and `ybkmzp`'s status, with the STOP if it is not `executed`.
- THE BASE-REACHABILITY CENSUS (E-02): the count of `executed/` plans with and without a surviving `base_head` receipt, measured across the whole tree rather than sampled.
- Under a build outcome: NEGATIVE PROOF that no second verifier prompt or outcome schema was written (show the searches), which is the item's hard constraint.
- Under a build outcome: a test that the standalone path composes the SAME prompt as the in-run path for equivalent inputs, since that identity is what makes the two verifiers trustworthy.
- Under a build outcome: proof the verb cannot change an `executed` plan's status or body, asserted rather than assumed.
- Under a build outcome: the verdict's destination demonstrated, and whether it is tracked or gitignored stated explicitly.
- Under the not-wanted outcome: the spec decision record, and `git status` over `agent_workflows/` proving no code changed.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

THE DECISION IS THE PRIMARY DELIVERABLE UNDER EITHER OUTCOME and must live in a spec under `.aw/records/specs`, because the item's four questions will otherwise be re-derived by the next person who wants this. Record what the verb verifies against, what it may write and where, whether it takes a lane, and the economics that decided whether it exists at all. A recorded NO is a real answer: an unused verb costs more than a documented decision.

Under a build outcome the verb is operator-facing and needs documentation stating plainly that it forms an OPINION and cannot change an `executed` plan, that a negative verdict leads to a corrective IPD, and WHICH HOST it works on if only one is wired. Write no em or en dashes in that prose.

Spec `25kzda` governs the deterministic run-and-verify surface and enumerates the `aw runs` leaves in its Section 3 command table, so ADDING a verb to that surface may amend a table an approved spec fixes. If E-05 builds a verb that lands there, the spec file MUST be declared in `Scope-Paths` before editing, per the spec-amendment rule, and the reason stated here. That declaration is deliberately not made in advance, since the not-wanted outcome amends nothing.

If the executor finds spec or documentation text asserting that verification can already be requested for an executed plan, that is a false claim and must be corrected in the same change, with the spec declared first.

## Open questions

### OQ-01: Is a standalone re-verify verb wanted at all, given the measured economics?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): YES, BUILD IT, AND A FINDING MUST LAND IN A BACKLOG ITEM OR PLAN RATHER THAN ONLY IN A REPORT. Report-only was declined explicitly, on the maintainer's standing rule that "no defect, gap, or issue may be found, raised, or noted without a minimum of at least one IPD or one backlog item per issue". So filing a durable carrier is part of the deliverable, not a nicety.
  THE PLAN'S VALUE PROPOSITION WAS MISFRAMED BY BOTH THE PLAN AND THE REVIEW, AND THE MAINTAINER CORRECTED IT. Both argued the verb in terms of RECOVERING abandoned or stranded runs, and the review's strongest objection was that the base commit needed for a diff is gone for 454 of 470 executed plans (re-verified: only 16 surviving begin receipts). The maintainer rejected the premise: "I can ask an agent today 'another agent claims to have fully completed abc123. Please verify all of its claims and the completeness of execution'. It needs exactly no work to compare against." And: "this had almost nothing to do with the specific case of something left unfinished because of a terminated `aw oc|agy run` and everything to do with my wondering if a plan or similar was actually executed faithfully and completely." SO THE 96-PERCENT OBJECTION IS WITHDRAWN: it measured a stored-baseline comparison nobody asked for. The audit compares the PLAN'S OWN CLAIMS against the repository's present state, both of which are always available.
  TWO OTHER "AGAINST" MEASUREMENTS ALSO FALL. The `nna8yz` case was "recovered by hand", which the maintainer clarified means going into the host and asking an agent manually; that is precisely the friction the verb removes, so it argues FOR the verb rather than against it. And the agy-host default is not an argument at all: see below.
  THE GAP IS REAL AND WAS RE-VERIFIED, at HEAD `2cdc5fe5`: `build_verifier_prompt` has exactly ONE production caller per host, both inside the execute path (`oc_runipd.py` defined `:4913`, called `:6586`; `agy_runipd.py` defined `:2456`, called `:3642`), so the skeptical verifier cannot be asked for after the fact by any route.
  F-12 IS RECLASSIFIED FROM EVIDENCE TO A DEFECT WITH ITS OWN CARRIER, and this is a correction of this plan's own conduct. F-12 noted that the agy host "registers no `--validate` at all" and used it ONLY as evidence weakening this plan's cost argument. The maintainer ruled that unacceptable on the merits ("BOTH hosts need flags to turn on or off. Only the defaults were meant to change") and, by the carrier rule, unacceptable as process. Filed as backlog `kyb0v5` (high, bug). This plan may NOT absorb that fix: registering a flag on the other host is not re-verification.

### OQ-02: What does the verb verify against for a plan executed weeks ago?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: THE REACHABILITY HALF IS NOW MEASURED AND ANSWERED; THE CHOICE-OF-BASE HALF REMAINS OPEN. This was left open because the obvious answer might be unavailable, and at review it was measured and IS unavailable for almost the whole corpus: 16 of 469 `executed/` plans retain a receipt carrying `base_head` and 453 do not, because clean finalize UNLINKS the receipt (`ipd_lifecycle.py:2832`), and both of this plan's motivating examples measured ABSENT (F-6). Of the 16 survivors all 16 bases are still ancestors of HEAD, so a surviving receipt is genuinely usable; but the survivors are precisely the plans whose finalize did NOT cleanly complete, so the base survives exactly when something went wrong, which is a biased and small sample.
  WHAT REMAINS FOR A HUMAN is which substitute the verb should use, because each changes what a verdict MEANS rather than merely how it is computed: an operator-supplied base (universal, but moves the correctness burden to the human and makes the verdict only as good as their input), the plan's tracked lifecycle commit (durable and clone-visible, but it identifies the finalize rather than the execution baseline), or a narrower verification that does not need a base at all (honest but answers a smaller question than "was this work done properly"). Still non-blocking, because E-02 must now CHOOSE among reachable bases and state the meaning consequence, and every branch leaves the plan completable; but note the answer interacts with OQ-01, since a verb that cannot reach a base for 97 percent of plans is worth less than one that can.

### OQ-03: Where does a verdict land, and what stops an operator re-running until they like it?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN BECAUSE BOTH DESTINATIONS HAVE A REAL COST and the choice is about what the repository wants permanently recorded. A gitignored run record cannot be cited in a plan or seen by a reviewer, so a negative verdict effectively evaporates. A tracked record makes a machine-generated opinion part of permanent history.
  ONE CANDIDATE IS NOW MEASURED AS MORE EXPENSIVE THAN THIS PLAN ASSUMED (F-17). The reviews tree is not simply "artifact-neutral and waiting": `review_findings.SUBJECT_TYPES` is the closed pair `('ipd','spec')`, an unrecognized value is a documented parse error (`REV-M101`/`REV-M102`), and the README states a new type is added "by amending the vocabulary ... and the checker's per-type resolution together, never by writing a novel value into a record". So filing there costs either an honesty compromise (a VERIFICATION verdict recorded as an `ipd` REVIEW, which is a different judgement by a different actor at a different lifecycle point) or a vocabulary-plus-checker amendment whose path this plan has not declared. Also corrected: 127 review records exist and some carry `Subject-Type: spec`, so "only `/plan-review` writes records" is stale and the tree has already widened once, which is precedent for how such a widening is done properly.
  THE SECOND HALF IS THE SHARPER ONE AND ITS SCOPE IS NOW NARROWED. If the verdict is discardable, an operator can re-run until satisfied, which makes the check untrustworthy in exactly the way `--no-verify` becoming routine was. But an operator-invoked verb can never force its own invocation, so "what stops re-running" cannot be answered by prevention. The achievable and checkable property is whether the destination APPENDS or OVERWRITES, since that alone decides whether a second opinion hides the first. E-03 must answer that specific question; an honest "nothing prevents re-running, and here is why that is acceptable given the trace is append-only" is a legitimate answer, but it must be written down rather than left implicit.

### OQ-04: Does the standalone verifier need its own lane?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES IF IT NEEDS A TREE AT ALL, and the landscape now makes that the consistent choice rather than a novel one: isolation is the DEFAULT for execute turns (re-confirmed at review, `isolate_worktree` parses True on BOTH hosts) and `worktree_lease` already owns allocation and teardown, so running a verification against the primary checkout while other agents work there would be the odd choice, not the safe one. The genuine sub-question E-04 must still answer is whether a full lane is warranted for a READ-MOSTLY turn, or whether a read-only checkout at the recorded base is cheaper and more correct, since the verifier's job is to form an opinion and a lane whose changes are discarded mainly costs time. What is settled is the direction: do NOT run it in the shared primary checkout. NOTE ONE SUPPORTING CITATION WAS WRONG: this plan credited `3i0aaz` with having "graduated the remaining ungated dirty-base cases"; it is a `to-review` PLAN, so those cases are identified and not yet guarded. The resolution stands on the isolation default, which was verified directly.
  A REVIEW ADDITION THAT CHANGES THIS ITEM'S WEIGHT: the tree decision is no longer merely a cost question, because under E-06 route (b) the read-only tree IS the mechanism preventing the reused prompt's fix-and-commit instruction from taking effect (F-14). So E-04 must state which route it is serving; "read-mostly, so a lease is probably overkill" is a defensible answer under route (a) and a dangerous one under route (b).

### OQ-05: May the verifier prompt be modified so it can be pointed at an immutable executed plan?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: F-14
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): THE AUDIT MAY FIX CODE IN PLACE AND COMMIT, BUT MUST NEVER EDIT THE FINISHED PLAN'S RECORD, and it must file a durable carrier naming what it fixed and why. Report-only-with-a-corrective-IPD-per-fix was declined on measured cost; fix-in-place-with-no-carrier was also declined, as it contradicts the maintainer's own rule that every defect needs a carrier.
  THE CONSTRAINT WAS NARROWER THAN THIS PLAN AND ITS REVIEW BOTH ASSUMED, and re-reading the rule is what dissolved the collision. `AGENTS.md:63` forbids adding commits to a plan already in `.aw/records/plans/executed/` and says to "close a post-execution gap with a new corrective IPD, not an in-place edit". THE IMMUTABLE THING IS THE PLAN DOCUMENT, NOT THE REPOSITORY. So the verifier prompt's "fix them, re-run validation, and commit path-scoped" clause is NOT in conflict with immutability when pointed at code; it conflicts only if aimed at the executed plan's own record. That distinction is what makes a compromise possible, and both the plan's F-14 and the review's PR-801 missed it by treating "executed plan" and "the repository at that point" as one object.
  THE MAINTAINER ASKED FOR EVIDENCE AND IT EXISTS, contrary to their expectation and mine ("I think not because ... we do not track tokens or $$ used"). MEASURED at HEAD `2cdc5fe5` from `.aw/records/runs/*/state.json`: 59 of 144 run records carry a numeric cost field, including 8 of the 12 most recent, so this is live data rather than a historical accident. PER-ATTEMPT MEDIANS: a `review`-action turn costs $11.10 (n=185) and an `execute`-action turn costs $18.50 (n=94). So a small fix through the full cycle costs about $29.60 (audit plus execute) against about $11.10 for a fix riding inside the audit turn, i.e. ~2.7x, or ~$18.50 extra per fix. The maintainer's stated concern that rigid rigor is tripling cost is therefore close to measured reality, and the project's >$12,000 spend gives it weight.
  HONEST BOUNDS ON THAT MEASUREMENT, stated so nobody over-trusts it: the figures are PER ATTEMPT, so a retried item costs more than shown; an audit turn may run longer than a plan review because it inspects finished work, making $11.10 a FLOOR rather than a point estimate; and 85 of 144 runs carry no cost field at all, so this is a sample rather than a census.
  WHAT THE PROMPT WORK NOW REQUIRES, which is less than option (a) as originally costed: the fix-and-commit clause may stay REUSED VERBATIM, because fixing code is now authorized. What must change is narrower: the "working tree diffs produced for this IPD" clause is wrong for a finished plan (there is no such working tree), and the prompt needs an instruction to file a durable carrier for each finding. Verified that this is affordable: `tests/test_reporting_contract.py:516-522` and `:620-632` assert both hosts' prompts CARRY THE CONTRACT, not that their bytes are frozen, so adding an audit mode does not fight a byte-exact pin as the plan feared.
  THE HARD PROHIBITION THE EXECUTOR MUST ENCODE: the audit may not add commits to, rewrite, or re-status the executed plan document, and it may not make finished work look as though it was always complete. That is the dishonesty the immutability rule protects against, and it is the one thing no cost argument may buy.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the ACTUAL location of `build_verifier_prompt` in BOTH drivers found by symbol, and the caller count for each SPLIT into production versus test callers, with the surrounding context showing each production caller sits inside the execute path. Paste BOTH hosts' gate expressions and BOTH parser defaults separately, stating explicitly which host has the verifier ON by default; a V-01 that reports a single shared `validate` gate is a FAILED validation (F-12). State the line-number drift against this plan's citations. Paste `ybkmzp`'s current `- Status:`, `- Readiness:` and directory, and if it has not reached `executed`, paste the STOP and confirm task groups 2 and 3 were not performed.
  - Observed evidence: PASS. The gap re-measured BY SYMBOL and the precondition MET. Headline correction: the two host prompts this plan describes NO LONGER EXIST as two; `rununify` collapsed them into ONE definition at `runner_shared.py:12973`, with four-line host delegations at `oc_runipd.py:5057` and `agy_runipd.py:2325`. ONE production caller (`runner_shared.py:15101`, inside `execute_item_core`), FIVE test callers (not four). Both defaults still OPPOSITE but now resolved from the runner-profile registry rather than a parser default: oc `validate_default=False` (verifier OFF), agy `True` (verifier ON). `ybkmzp` is in `executed/` with `- Status: executed`, so the gate is OPEN and task groups 2 and 3 were performed. Full measurements below.
    THE LANDSCAPE CHANGED MATERIALLY SINCE REVIEW, AND THIS IS THE HEADLINE OF V-01: THE TWO PROMPTS ARE NOW ONE. This plan's F-15 (and its Concern) assert two separate 68-line `build_verifier_prompt` bodies differing in 26 lines. Measured at HEAD `4b8f22b5`, that is NO LONGER TRUE: `rununify` collapsed them into a SINGLE definition in `runner_shared`, and each host now holds a four-line delegation. Located by symbol:

    ```
    $ grep -n "def build_verifier_prompt" agent_workflows/*.py
    agent_workflows/agy_runipd.py:2325:def build_verifier_prompt(
    agent_workflows/oc_runipd.py:5057:def build_verifier_prompt(
    agent_workflows/runner_shared.py:12973:def build_verifier_prompt(
    ```

    The two host functions are DELEGATIONS, not bodies (agy, verbatim before this plan's edit):

    ```
    agent_workflows/agy_runipd.py:2331:    return runner_shared.build_verifier_prompt(
    agent_workflows/agy_runipd.py:2332:        item, state, run_dir, plan_path, labels=runner_shared.AGY_HOST_LABELS
    ```

    PRODUCTION CALLERS, SPLIT FROM TEST CALLERS. There is now exactly ONE production caller of the shared composer for BOTH hosts, not one per host, because there is one composer:

    ```
    agent_workflows/runner_shared.py:15101:        v_prompt = build_verifier_prompt(
    ```

    Its enclosing function is `execute_item_core` (`runner_shared.py:13989 def execute_item_core(`), i.e. the execute path, and the call sits inside the `if not is_review and disposition in ("executed", "substantially-complete") and validate:` block measured below. Test callers: `tests/test_oc_runipd.py:2175`, `:2245`, `tests/test_reporting_contract.py:493`, `:614`, `tests/test_rununify_host_descriptor.py:424` - FIVE, not the four this plan recorded, the fifth being a host-descriptor parity test added since review. They compose from a SYNTHETIC `item`/`state`/`run_dir`, which is exactly what this plan's new standalone caller supplies.

    LINE-NUMBER DRIFT AGAINST THIS PLAN'S CITATIONS: total. The plan cites `oc_runipd.py:4913` defined / `:6586` called and `agy_runipd.py:2456` / `:3642`. Actual: the definition MOVED MODULE (`runner_shared.py:12973`), the host entries are at `oc_runipd.py:5057` and `agy_runipd.py:2325`, and the production call is at `runner_shared.py:15101`. This is the fourth consecutive measurement at which this plan's coordinates were stale, which is exactly what F-2 predicted.

    THE GATE, MEASURED PER HOST. The gate expression is now SHARED, and it reads BOTH keys rather than one per host (`runner_shared.py:15085-15088`, located by grep for the assignment rather than by a remembered line):

    ```
    opts = state.get("options", {})
    validate = opts.get("validate", False)
    if "validate" not in opts:
        validate = not (opts.get("no_verify") or opts.get("no_audit"))
    ```

    THE DEFAULTS ARE STILL OPPOSITE, WHICH IS WHAT F-12 CARES ABOUT, but the mechanism moved from a parser default to the runner-profile registry's bottom tier (`ybkmzp` E-01/E-03). Measured live:

    ```
    $ python3 -c "from agent_workflows import runner_profiles as rp, runner_shared as rs
    for h in ('oc','agy'):
        print(h, 'validate_default =', rp.RUNNER_REGISTRY[h].validate_default)
        print('  resolved (operator silent):', rs.resolve_verification_decision(runner=h, validate=None))"
    oc validate_default = False
      resolved (operator silent): VerificationDecision(validate=False, provenance='shipped-default')
    agy validate_default = True
      resolved (operator silent): VerificationDecision(validate=True, provenance='shipped-default')
    ```

    So THE VERIFIER IS OFF BY DEFAULT ON OPENCODE AND ON BY DEFAULT ON ANTIGRAVITY, stated explicitly as V-01 demands. Both parsers now register `--validate` as a TRI-STATE with `default=None` (oc at `oc_runipd.py:7361` with aliases `--verify`/`--audit`; agy at `agy_runipd.py:3900` registered BARE to avoid an argparse collision with its own `--no-verify`), measured:

    ```
    $ python3 -c "...build_parser().parse_args(['start','--repo','.','x'])..."
    oc validate= None no_verify= ABSENT
    agy validate= None no_verify= False
    ```

    NOTE THIS PARTLY RETIRES BACKLOG `kyb0v5` ("agy validate flag missing"): agy now DOES register `--validate`. That item is left for its owner to re-measure and close; this plan may not absorb it.

    THE PRECONDITION IS MET, so no STOP applies and task groups 2 and 3 were performed:

    ```
    $ find .aw/records/plans -name "*ybkmzp*"
    .aw/records/plans/executed/20260906-hostdefault-02-ybkmzp-wire-the-resolved-verification-decision-into-both-host-drive.ipd.md
    ```

    Directory: `executed/`. Its `- Status:` is `executed`. The declared `- Item-Dependencies: executed:ybkmzp` is therefore satisfied. `tm2cz8` is likewise `executed`.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the ACTUAL text of the existing prompt's requirement 1 and requirement 4, showing for yourself that it instructs worktree-diff inspection and fix-and-commit. State which of the three routes (parameterize / constrain the environment / do not reuse) was chosen and why, and name WHICH HOST's prompt the verb composes. Paste `python3 -m pytest tests/test_reporting_contract.py` passing under the chosen route, or, if the route conflicts with those tests, paste the conflict as a finding rather than a relaxed test. Confirm by grep that no second verifier composer was added.
  - Observed evidence: PASS. Route (a) PARAMETERIZE chosen, on the ONE shared composer, rendered with `OC_HOST_LABELS`. Requirement 4's fix-and-commit clause is REUSED VERBATIM because OQ-05 authorized fixing code; only requirement 1's working-tree premise is replaced, plus two ADDED requirements (the plan-document prohibition and the carrier obligation). The in-run rendering is byte-identical (asserted for both hosts' labels). Parity tests pass: 115 passed. Exactly three `def build_verifier_prompt` remain, two of them delegations. Full text and searches below.
    THE PROMPT'S ACTUAL TEXT, read in full from `runner_shared.build_verifier_prompt` before editing it. Requirement 1:

    ```
    1. **Inspect Concrete Diffs & Commits**:
       - Inspect the git commits and working tree diffs produced for this IPD.
       - Verify that real functional changes were made, not just cosmetic/vocabulary additions.
       - Ensure all referenced files and symbols in the plan's Scope-Paths actually exist and are wired correctly.
    ```

    Requirement 4:

    ```
    4. **In-Scope Fixes**:
       - If you discover safely correctable defects, regressions, or missing test cases within the approved scope, fix them, re-run validation, and commit path-scoped (`git commit -m msg -- <paths>`). Never push.
       - If any unresolvable defect or scope gap remains, report it clearly.
    ```

    Confirmed for myself: requirement 1 DOES instruct working-tree-diff inspection, and requirement 4 DOES instruct fix-and-commit.

    ROUTE CHOSEN: (a) PARAMETERIZE, recorded as DECISION 09-mp289j-D1. `build_verifier_prompt` gains a keyword-only `audit: bool = False` plus `diff_basis: str = ""`; under `audit=True` it delegates to `_build_audit_prompt`, which reuses the same clause constants. WHY: OQ-05's recorded maintainer resolution authorizes fixing CODE and forbids only editing the plan DOCUMENT, so requirement 4 is REUSED VERBATIM and the collision reduces to requirement 1's working-tree premise, which is simply false for a finished plan. Route (b) was rejected because the prompt would still ASK for a fix the environment silently refuses, which this repository treats as a defect; route (c) contradicts OQ-01's recorded "YES, BUILD IT".

    WHICH HOST'S PROMPT: the question has changed shape since review, and the honest answer is THE SHARED COMPOSER, rendered with `OC_HOST_LABELS`. F-15's premise (two 68-line bodies differing in 26 lines) no longer holds: there is ONE definition at `runner_shared.py:12973`, so parameterizing it reaches both hosts by construction. The VERB is wired on OpenCode only (see V-05).

    THE PARITY TESTS PASS UNDER THE CHOSEN ROUTE, and note the plan feared a byte-exact pin that does not exist: the assertions require the prompts to CARRY the contract prose, not to be frozen.

    ```
    $ python3 -m pytest tests/test_reporting_contract.py tests/test_rununify_build_parser.py tests/test_runner_stop_triggers.py
    115 passed in 6.53s
    ```

    NEGATIVE PROOF THAT NO SECOND COMPOSER WAS ADDED. Three definitions, of which two are the pre-existing host delegations:

    ```
    $ grep -n "def build_verifier_prompt" agent_workflows/*.py
    agent_workflows/agy_runipd.py:2325:def build_verifier_prompt(
    agent_workflows/oc_runipd.py:5057:def build_verifier_prompt(
    agent_workflows/runner_shared.py:12973:def build_verifier_prompt(
    ```

    That count is now ASSERTED rather than merely observed, by `tests/test_standalone_verify.py::TheAuditReusesTheOneVerifierComposer::test_no_second_composer_exists_in_the_package`, which regexes every `agent_workflows/*.py` for `def \w*verifier_prompt\w*(` and requires exactly that mapping. A stronger identity test accompanies it (`test_the_audit_prompt_comes_from_the_same_function_as_the_in_run_prompt`) which MONKEYPATCHES the shared composer and proves the audit output changes with it, so the audit has no private fallback path. `_build_audit_prompt` is a private RENDERER reached only from the `audit=True` branch of the one composer and is excluded from the count by name deliberately, which the test's own docstring states.

    THE IN-RUN PROMPT IS BYTE-IDENTICAL, which is the condition this plan's Deferred section attaches to touching the composer at all: `test_the_default_call_is_byte_identical_to_an_explicit_non_audit_call` asserts equality for BOTH hosts' labels, and `test_the_in_run_prompt_still_names_the_working_tree_and_the_execution_outcome` asserts the in-run rendering keeps the two clauses the audit rendering removes.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the written answer for what the verb verifies against. Paste YOUR OWN re-measurement of base reachability across the whole `executed/` tree (the count with a surviving `base_head` receipt versus without; it was 16 of 469 at review), not a spot check and not this plan's numbers. Paste the `ipd_lifecycle` line that consumes the receipt. Confirm whether the chosen base exists for this plan's own motivating examples (`nna8yz`, `tm2cz8`), both of which measured ABSENT at review. State plainly what a verdict MEANS when the original base is unavailable, and what the two `run_dir`-relative outcome paths in the prompt point at when no run directory exists.
  - Observed evidence: PASS. The verb audits the plan's OWN CLAIMS against present repository state (always available), with a historical base offered only as corroboration in precedence `operator` -> `receipt` -> `none`, and the basis RECORDED in the verdict. My own whole-tree re-measurement at HEAD `4b8f22b5`: 561 executed plans, 17 with a surviving `base_head` receipt, 544 without; `nna8yz`, `tm2cz8` and `ybkmzp` all receipt-ABSENT. Receipt consumed at `ipd_lifecycle.py:3989`. All three bases exercised live. The execution-outcome path is REMOVED from the audit prompt because no such file exists for a historical plan. Full measurements below.
    THE WRITTEN ANSWER (DECISION 09-mp289j-D2, and spec `i4gpto` R-3 through R-5): the verb's PRIMARY basis is the plan's OWN recorded claims versus the repository's present state, which is always available. A historical diff basis is offered as CORROBORATION when reachable, in precedence order `operator` (`--base <rev>`) -> `receipt` (a surviving `base_head`) -> `none`, and the verdict RECORDS which it had in a `diff_basis` field. This follows the maintainer's OQ-01 resolution, which withdrew the stored-baseline premise in as many words.

    MY OWN RE-MEASUREMENT ACROSS THE WHOLE TREE at HEAD `4b8f22b5` (not a spot check, not this plan's numbers; the population grew from 469 to 561 since review):

    ```
    $ python3 - <<'EOF'
    ... for every *.ipd.md in .aw/records/plans/executed/: read `- Id:`, call ipd_lifecycle.read_receipt ...
    EOF
    executed plans scanned: 561
    with surviving base_head receipt: 17
    without: 544
      nna8yz: receipt ABSENT
      tm2cz8: receipt ABSENT
      ybkmzp: receipt ABSENT
    ```

    So 17 of 561 (about 3 percent) retain the base, confirming F-6's finding on a larger corpus. THE THREE NAMED PLANS ARE ALL RECEIPT-ABSENT, including both of this plan's own motivating examples, so the chosen base does NOT exist for them and `diff_basis: none` is what they would get.

    THE CONSUMING LINE, located by grep for its comment rather than by a remembered number (the plan cites `:2832`, which has drifted):

    ```
    $ grep -n "Consume the begin receipt" agent_workflows/ipd_lifecycle.py
    3989:    # Consume the begin receipt (the transaction is cleanly complete).
    $ sed -n '3989,3993p' agent_workflows/ipd_lifecycle.py
        # Consume the begin receipt (the transaction is cleanly complete).
        try:
            receipt_path_for(repo_root, plan_id).unlink()
        except OSError:
            pass
    ```

    THE RESOLVER WAS EXERCISED AGAINST ALL THREE BASES, live:

    ```
    $ python3 -c "from pathlib import Path; from agent_workflows import runner_shared as rs
    for id6 in ('nna8yz','mp289j','ybkmzp'): ...; print(rs.plan_audit_target(Path('.'), id6))"
    nna8yz -> ok | basis= none | setid= lanectn
    mp289j -> REFUSAL:audit-plan-not-executed | basis= none | setid=
    ybkmzp -> ok | basis= none | setid= hostdefault
    with --base: operator | OPERATOR-SUPPLIED revision `HEAD~5`. You may diff against it for corroboration, but the co...
    bogus: audit-plan-not-found
    ```

    and the RECEIPT basis against two of the 17 survivors:

    ```
    v7e88a basis= receipt
        the plan's OWN surviving begin receipt, base_head `072f57f8dbc69cc4d0d06cac54991bd55efa2611`, so `git diff 072f57f8...
    qmt3yk basis= receipt
        the plan's OWN surviving begin receipt, base_head `cfab2d603812e92260d6346f7d7243e840551702`, so `git diff cfab2d60...
    ```

    WHAT A VERDICT MEANS WHEN THE ORIGINAL BASE IS UNAVAILABLE, stated plainly and also stated TO THE AUDITOR in the prompt itself: it means "the plan's claims are, or are not, borne out by the code, tests and artifacts that exist NOW". It does NOT mean "the diff at the time was correct". The prompt's audit rendering carries this explicitly ("Audit the claims against present state; say so in your verdict") and the schema carries a `diff_basis` field so a reader of the verdict cannot mistake one for the other. A surviving receipt also carries a BIAS warning, because a receipt survives precisely when finalize did NOT cleanly complete; `test_a_surviving_receipt_is_used_when_one_exists` asserts that warning is present.

    THE TWO `run_dir`-RELATIVE OUTCOME PATHS: the audit rendering carries only ONE of them. The EXECUTION outcome path is REMOVED, because for a historical plan no such file exists and naming one invites the auditor to report its absence as a defect (asserted by `test_the_audit_prompt_does_not_promise_an_execution_outcome_file`). The VERDICT path points inside the audit's OWN freshly-minted run directory (`<runs-root>/<audit-run-id>/outcomes/01-<id6>-verification.json`), so it always exists and is always writable; the end-to-end test proves the fake host can read that path out of the prompt and write to it.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the decided destination for a verdict and state explicitly whether it is TRACKED or GITIGNORED, with the consequence of that choice. If the reviews tree was chosen, paste `review_findings.SUBJECT_TYPES` as it actually is and state whether you are amending it (and its checker) or filing under an existing type, with the honesty cost of each; a V-03 that files a verification verdict as `Subject-Type: ipd` without addressing that it is not a review FAILS. Paste the APPEND-versus-OVERWRITE answer to the re-run hazard; if nothing prevents re-running, paste the written justification rather than omitting the question. Confirm in one sentence that no mechanism was proposed that edits an `executed` plan, including appending to its `## Workflow history`.
  - Observed evidence: PASS. Destination: a FRESH per-invocation run directory under the runs root, which is GITIGNORED (`.aw/.gitignore:14`), PLUS a MANDATORY tracked backlog item per finding. The reviews tree was NOT chosen and `SUBJECT_TYPES` was re-measured live as the closed pair `('ipd','spec')`; filing a verdict as `Subject-Type: ipd` is declined on honesty grounds and the vocabulary is not amended. APPEND, structurally. Validation found a REAL DEFECT here: `new_run_id` is second-granular so two same-second audits collided, filed as backlog `2jtsup` and worked around with an atomic `mkdir(exist_ok=False)` suffix loop. Nothing edits the plan document, including its `## Workflow history`. Full measurements below.
    THE DECIDED DESTINATION (DECISION 09-mp289j-D3, spec `i4gpto` R-6 through R-8): a FRESH run directory per invocation under the runs root, holding the machine verdict, PLUS a mandatory tracked backlog item for every finding.

    TRACKED OR GITIGNORED: the verdict is GITIGNORED. Measured, asked as a path INSIDE the directory because the pattern is directory-anchored:

    ```
    $ git check-ignore -v .aw/records/runs
    (rc=1, no output)
    $ git check-ignore -v .aw/records/runs/
    .aw/.gitignore:14:records/runs/	.aw/records/runs/
    $ git check-ignore -v .aw/records/runs/x/state.json
    .aw/.gitignore:14:records/runs/	.aw/records/runs/x/state.json
    ```

    THE CONSEQUENCE, stated rather than glossed: a gitignored verdict cannot be cited in a plan, is invisible to a reviewer, and is absent from a clone. That is ACCEPTED because the half a reviewer must be able to cite is forced into tracked history by R-8: the prompt REQUIRES `aw backlog new` for each finding, and the verdict schema carries a `findings_filed` list. So the prose is local and the findings are not. This is exactly what OQ-01's resolution demanded ("A FINDING MUST LAND IN A BACKLOG ITEM OR PLAN RATHER THAN ONLY IN A REPORT"); report-only was declined.

    THE REVIEWS TREE WAS NOT CHOSEN, and `SUBJECT_TYPES` was re-measured live to price it honestly:

    ```
    $ python3 -c "from agent_workflows import review_findings as rf; print('SUBJECT_TYPES =', rf.SUBJECT_TYPES)"
    SUBJECT_TYPES = ('ipd', 'spec')
    ```

    So F-17 holds: it is a CLOSED pair. I am NEITHER amending it NOR filing under an existing type. Filing under `ipd` would record a VERIFICATION verdict as a plan REVIEW, which is a different judgement by a different actor at a different lifecycle point, and that honesty cost is the reason for declining; amending the vocabulary plus its per-type checker resolution is undeclared work this plan did not scope (`agent_workflows/review_findings.py` is not in `- Scope-Paths:`). Both costs are recorded in spec `i4gpto` Section 5 so the next person does not re-derive them.

    APPEND OR OVERWRITE: APPEND, structurally, because each invocation mints its OWN directory. AND THIS IS WHERE THE VALIDATION FOUND A REAL DEFECT rather than confirming a design. Relying on `runner_shared.new_run_id()` would have made the claim FALSE: it returns `run-<UTC seconds>-<pid>`, so two invocations inside one second from one shell return the IDENTICAL id, measured as `{new_run_id(), new_run_id()}` having length 1. That is the most likely re-run pattern there is. The verb therefore mints through `oc_runipd._fresh_audit_run_dir`, which suffixes (`-2`, `-3` ...) using `mkdir(exist_ok=False)` as an atomic test. Demonstrated end to end, two audits in one second:

    ```
    Audit run: run-20260920T091548Z-1287758
    ...
    Audit run: run-20260920T091548Z-1287758-2
    second audit exit: 0 | run dirs now: 2
    ```

    The underlying collision in the SHARED helper is filed as backlog `2jtsup` (bug, medium, blocks-release next) rather than fixed here, because changing `new_run_id`'s format alters run ids repository-wide.

    WHAT NOTHING PREVENTS, written down rather than omitted as V-03 requires: nothing prevents an operator re-running the audit until they like the answer, and nothing can, because the verb is invoked on demand and cannot force or forbid its own invocation. The achievable property is narrower and is the one built: a later run cannot HIDE an earlier one (separate directories), and a finding the earlier run filed is a COMMITTED backlog item that a later run cannot unfile. That asymmetry is the whole reason R-8 exists.

    NO MECHANISM THAT EDITS AN `executed` PLAN WAS PROPOSED: the plan's own `## Workflow history` was considered and explicitly ruled out in spec `i4gpto` Section 5 as the in-place edit the immutability policy forbids, the prompt carries a HARD PROHIBITION against editing, re-statusing, moving or committing to the plan document or appending to its history, and `test_an_audit_records_a_verdict_and_leaves_the_plan_byte_identical` asserts byte-identity after a real audit turn.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the lane decision with its reasoning, and confirm it does not run in the shared primary checkout. State which E-06 route you are in and therefore whether the tree restriction is the PRIMARY immutability guard or a secondary one. If a read-only checkout was chosen over a full lane, paste the reasoning and state what the verifier may write into whatever tree it gets. If the chosen combination leaves any path by which the verifier could commit behind an `executed` plan, paste that as a finding.
  - Observed evidence: PASS. A FULL WRITABLE LANE through the EXISTING `worktree_lease` (`allocate_isolation_worktree`), default ON, `--no-isolate-worktree` to opt out; allocation failure REFUSES rather than falling back to the shared checkout. I am in E-06 route (a), so the tree restriction is a SECONDARY guard: the PRIMARY immutability guard is the prompt's hard prohibition, because OQ-05 authorizes code fixes and therefore requires a writable tree. The lane is never torn down (it may hold work) and never auto-integrated. The auditor MAY commit code in its lane, which is intentional per OQ-05 and stated rather than hidden; it may not touch the plan document. Full reasoning below.
    THE LANE DECISION (DECISION 09-mp289j-D4, spec `i4gpto` R-15 through R-17): a FULL WRITABLE LANE through the EXISTING `worktree_lease` machinery, default ON, with `--no-isolate-worktree` as a deliberate opt-out. The verb calls `runner_shared.allocate_isolation_worktree(repo, f"audit-{id6}")`, which is the same helper every execute turn uses, so no second isolation path was written.

    IT DOES NOT RUN IN THE SHARED PRIMARY CHECKOUT by default. `--isolate-worktree` is registered with `default=True`, and the help text names the risk of the opt-out ("runs it in the shared checkout, which other agents may be using"). If allocation FAILS the verb REFUSES rather than silently falling back to the shared tree:

    ```
    audit: could not allocate an isolated worktree (...); refusing rather than running in the shared
    checkout, which other agents may be using. Pass --no-isolate-worktree to override deliberately.
    ```

    That refusal direction is the load-bearing part: a fallback would have converted an allocation hiccup into a write in someone else's tree, which is precisely what OQ-04's recorded resolution forbids ("do NOT run it in the shared primary checkout").

    WHICH E-06 ROUTE, AND THEREFORE WHICH GUARD IS PRIMARY: I am in ROUTE (a) (parameterize), so the TREE RESTRICTION IS A SECONDARY GUARD. The PRIMARY immutability guard is the prompt's own explicit HARD PROHIBITION (requirements 6 and 7 of the audit rendering), because OQ-05 authorizes fixing code, which means the tree must be WRITABLE and therefore cannot be the mechanism that protects the plan document. A read-only checkout was CONSIDERED and rejected for exactly that reason: it would silently refuse the in-scope fix the prompt asks for, which is the instruction-versus-reality gap this repository treats as a defect. This is stated because OQ-04's own text warns that "read-mostly, so a lease is probably overkill" is defensible under route (a) and dangerous under route (b).

    WHAT THE AUDITOR MAY WRITE INTO THE TREE IT GETS: code, tests and documentation within the audited plan's scope, committed path-scoped, never pushed; plus backlog items for findings. What it may NOT write: the executed plan document, in any way.

    THE LANE IS NEVER TORN DOWN by the verb, even on an exception (the teardown call is deliberately absent and the `finally` block only REPORTS the branch and path). `teardown_isolation_worktree`'s own docstring says it "must only ever be called on a lane that holds NO work", and an audit that fixed code holds exactly that work. The verb also does NOT integrate its own lane, so a fix behind a finished plan is reviewed on its merits rather than auto-merged by the verb that asked for it.

    IS THERE A PATH BY WHICH THE VERIFIER COULD COMMIT BEHIND AN `executed` PLAN? YES, AND IT IS INTENTIONAL, SO IT IS STATED RATHER THAN HIDDEN: the auditor may commit CODE in its lane, because OQ-05 authorized exactly that. What no path permits is committing to, editing, re-statusing or moving THE PLAN DOCUMENT, which is the distinction OQ-05 drew ("THE IMMUTABLE THING IS THE PLAN DOCUMENT, NOT THE REPOSITORY") and which `test_an_audit_records_a_verdict_and_leaves_the_plan_byte_identical` asserts by measuring the file's bytes and the checkout's tracked dirt after a real turn. Reported here as a deliberate design property rather than as a finding, because the maintainer ruled on it directly.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: state which OQ-01 outcome the maintainer chose. Under a BUILD outcome: paste NEGATIVE proof that no second verifier prompt or outcome schema exists (show the searches), the test proving the standalone path composes the SAME prompt as the in-run path for equivalent inputs, the assertion that an `executed` plan's status and body cannot change, a statement of which host is wired, and the NOUN the verb hangs off with its justification against the documented `aw runs` read-only description and `aw run` writing description (F-18). Under a NOT-WANTED outcome: paste the spec decision record including the economics AND the per-host default asymmetry (F-12), and `git status` over `agent_workflows/` proving no code changed. UNDER EITHER: paste the BARE `python3 -m pytest` summary lines before and after with the failing NODE IDS compared rather than totals, and confirm BOTH hosts' verification defaults are untouched.
  - Observed evidence: PASS. BUILD outcome (OQ-01 resolved 2026-09-10). Verb: `aw oc run audit <id6>` on the host runner noun, justified against both `aw runs` (read-only) and `aw run` (ledger transactions, no agent turn) docstrings and asserted absent from the `runs` leaves. Implemented on OpenCode only; declared on both; the agy binding exits 2 naming the oc spelling. No second composer (3 defs, 2 delegations) and no second schema (9 keys, 7 reused). Plan byte-identity asserted through a real turn. BARE SUITE BEFORE `1 failed, 7273 passed, 3 skipped, 2 xfailed in 100.89s`; AFTER `1 failed, 7301 passed, 3 skipped, 2 xfailed in 99.67s`; FAILING NODE SET AFTER MINUS BEFORE IS EMPTY (same single node, proven ENVIRONMENTAL: green under `env -u OPENCODE_CONFIG_CONTENT`). Nine census-pinned tests were restated as invariants, none weakened; defect filed as `5zyuc8`. Both hosts' verification defaults re-confirmed untouched. Full evidence below.
    THE OQ-01 OUTCOME THE MAINTAINER CHOSE: **BUILD IT**, resolved 2026-09-10, with the added obligation that a finding must land in a backlog item or plan rather than only in a report. So this is a BUILD outcome, and the not-wanted branch does not apply.

    NEGATIVE PROOF, NO SECOND PROMPT COMPOSER. Searches shown:

    ```
    $ grep -n "def build_verifier_prompt" agent_workflows/*.py
    agent_workflows/agy_runipd.py:2325:def build_verifier_prompt(
    agent_workflows/oc_runipd.py:5057:def build_verifier_prompt(
    agent_workflows/runner_shared.py:12973:def build_verifier_prompt(
    ```

    The two host entries are four-line DELEGATIONS to the third; the third is the ONE body. Asserted, not merely observed, by `TheAuditReusesTheOneVerifierComposer::test_no_second_composer_exists_in_the_package`, which builds that mapping by regex over every `agent_workflows/*.py` and requires exactly it.

    NEGATIVE PROOF, NO SECOND OUTCOME SCHEMA. The audit writes the EXISTING verification schema, extended by two keys and replacing nothing: `schema_version`, `id6`, `verdict`, `summary`, `evidence`, `tests_run`, `corrections_made` are reused verbatim, plus `diff_basis` (E-02) and `findings_filed` (E-03/OQ-01). Asserted by `test_the_audit_writes_the_existing_outcome_schema`, which checks all nine keys. The `verdict` enum is unchanged (`VERIFIED|CORRECTION_REQUIRED|BLOCKED`), asserted by `test_the_audit_prompt_keeps_the_reused_requirements_verbatim`.

    THE SAME-PROMPT TEST, and it is stronger than a similarity check: `test_the_audit_prompt_comes_from_the_same_function_as_the_in_run_prompt` MONKEYPATCHES `runner_shared.build_verifier_prompt` with a spy returning `"SENTINEL"`, then calls the host entry with `audit=True`; it asserts the returned value is `"SENTINEL"` and that the spy saw `{"audit": True, "diff_basis": "a basis"}`. So the standalone path has NO private composer to fall back to. `test_the_audit_prompt_keeps_the_reused_requirements_verbatim` then pins seven clauses (including requirement 4's fix-and-commit sentence with "Never push") as present in BOTH renderings.

    THE ASSERTION THAT AN `executed` PLAN'S STATUS AND BODY CANNOT CHANGE, measured through a REAL audit turn against a fake host rather than asserted in prose: `TheVerbRunsEndToEnd::test_an_audit_records_a_verdict_and_leaves_the_plan_byte_identical` compares the plan file's full text before and after and requires `git status --porcelain` to show no tracked dirt outside the gitignored runs directory. Observed manually too:

    ```
    EXIT: 0
    state.kind: audit | action: audit | status: audited
    findings_filed: ['bk1234']
    PLAN BYTE-UNCHANGED: True
    WORKTREE CLEAN: ?? .aw/records/runs/
    ```

    A silent host is also not read as success: `test_a_turn_that_writes_no_verdict_exits_nonzero_rather_than_claiming_success` requires exit 1 and a `no-verdict` status.

    WHICH HOST IS WIRED: the verb is IMPLEMENTED on OPENCODE ONLY, and DECLARED on both. The Antigravity binding refuses, exiting 2 ("cannot run") rather than 1 ("refused after checking"):

    ```
    $ python3 -m agent_workflows agy runipd audit nna8yz
    audit is not implemented on the Antigravity host. The verb buys ONE independent opinion, so it is
    wired on one host deliberately (plan `mp289j`) rather than duplicated while the two drivers are
    still being unified.
    Run it on the OpenCode host instead:
      aw oc run audit nna8yz
    $ python3 -m agent_workflows agy runipd audit nna8yz >/dev/null 2>&1; echo $?
    2
    ```

    The DECLARATION is shared deliberately, because `tests/test_rununify_build_parser.py` pins the two hosts' subparser sets to be identical and a verb existing on one host only is a real surface fork; documented in the spec (R-10) rather than left to inference.

    THE NOUN, JUSTIFIED AGAINST BOTH DOCSTRINGS (F-18). Chosen: the HOST RUNNER's own parser, reached as `aw oc run audit <id6>`, alongside `stop` and `integrate`. Against `aw runs`, whose live help reads "Inspect driver execution runs and run ledgers (the READING half of the run surface) ... Read-only, with FOUR exceptions, named rather than counted": this verb launches a model turn and writes a verdict, so it is read-only under no reading of that sentence, and that description has already gone stale twice by COUNTING its exceptions. Against `aw run`, whose live help reads "The WRITING half of the run surface ... RUN LEDGER TRANSACTIONS are 'start' ... 'record' ... 'cancel' ... and 'finalize'": those are deterministic bookkeeping that spend no agent turn, and an audit is an agent turn. Asserted by `test_the_verb_is_not_on_the_read_only_runs_noun`, which walks the real `cli` parser and requires `audit` NOT to be a leaf of `runs`. Spec `25kzda` Section 1.3's "Audit only" row is addressed in spec `i4gpto` Section 6: that row routes auditing A RUN (its ledger hash chain, its resumable steps) and this verb audits A PLAN'S CLAIMS, needs no run id, and works when the run records are long gone, so the row is neither duplicated nor amended.

    BARE SUITE, BEFORE AND AFTER, WITH NODE IDS COMPARED RATHER THAN TOTALS.

    BEFORE (at `4b8f22b5`, before any edit):

    ```
    $ python3 -m pytest
    1 failed, 7273 passed, 3 skipped, 2 xfailed, 3 warnings in 100.89s (0:01:40)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    ```

    AFTER:

    ```
    $ python3 -m pytest
    1 failed, 7301 passed, 3 skipped, 2 xfailed, 3 warnings in 99.67s (0:01:39)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    ```

    FAILING NODE SET, AFTER MINUS BEFORE: **EMPTY** (identical single node). The criterion is met. That one node is ENVIRONMENTAL, not pre-existing breakage I am excusing, and I proved it rather than asserting it: it fails because `OPENCODE_CONFIG_CONTENT` is exported in this session (the driver sets it for lane turns), and the test asserts a non-isolated turn gets NO denial policy. Unset, the file is green:

    ```
    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py -o addopts="" -q
    43 passed in 4.81s
    ```

    NOTE THE PASS COUNT ROSE BY 28, WHICH IS THE NEW TEST FILE, and NINE pre-existing tests were REWRITTEN rather than deleted or relaxed. Each had pinned a CENSUS COUNT as a proxy for an invariant and so fired on a correctly-wired new call site: `test_one_argv_builder_serves_both_call_sites` (wanted one BUILDER, asserted two CALLERS), two telemetry wiring tests, `test_neither_host_gained_a_third_launcher_call_site` (whose own stated reason, "a third could inherit the wrong profile", is satisfied by the new caller because it declares `use_verifier_launch=True`), and five closure-classification tests in `test_rununify_main.py`. Every one was restated as the invariant it stood for (one builder by DEFINITION count; exactly one call site may take the default execute phase; exactly one may omit the launch-role keyword; closure counts read from the single table that documents them), with a comment naming the proxy. The genuine censuses (the flag partition, the subparser set, the closure table) were UPDATED with the new measurement and the reason, which is what those tables ask for. Nothing was weakened to pass: the general defect is filed as backlog `5zyuc8`.

    BOTH HOSTS' VERIFICATION DEFAULTS ARE UNTOUCHED, confirmed live AFTER the change:

    ```
    $ python3 -c "from agent_workflows import runner_profiles as rp, runner_shared as rs
    for h in ('oc','agy'): print(h, rp.RUNNER_REGISTRY[h].validate_default, rs.resolve_verification_decision(runner=h, validate=None))"
    oc False VerificationDecision(validate=False, provenance='shipped-default')
    agy True VerificationDecision(validate=True, provenance='shipped-default')
    ```

    Still opposite, still `shipped-default`, and `git diff` touches neither `runner_profiles.py` nor either host's `--validate` registration.

    THE SHIM MEMBERSHIP AND ITS CONSEQUENCE: `audit` is in both drivers' inline `subcommands` sets (asserted off `main`'s AST by `test_the_verb_is_in_both_implicit_start_shim_sets`), and the CONSEQUENCE is observed rather than inferred by `test_a_bare_audit_is_not_rewritten_into_a_run_launch`, which requires exit 1 and that NO run directory was created. Without it, `audit <id6>` would be rewritten to `start audit <id6>` and would pay for an execution attempt against an already-executed plan.

    REFUSALS, measured unpiped:

    ```
    $ python3 -m agent_workflows oc runipd audit mp289j >/dev/null 2>&1; echo $?
    1
    $ python3 -m agent_workflows oc runipd audit zzzzzz >/dev/null 2>&1; echo $?
    1
    $ python3 -m agent_workflows oc runipd audit mp289j
    audit refused (audit-plan-not-executed): mp289j is in pending/, not executed/, so there is no
    finished execution to audit. ...
    $ python3 -m agent_workflows oc runipd audit zzzzzz
    audit refused (audit-plan-not-found): Cannot locate IPD zzzzzz; configured path was
    ```

    `aw sanitize --agent` clean:

    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```

    `aw specs check`: `aw specs check: all specs conform.`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN IS NOW GATED THREE TIMES, AND TWO OF THE THREE GATES COME FROM THE ITEM ITSELF. It carries `- Item-Dependencies: executed:ybkmzp` because the item's own sequencing recommendation is "do `h7qsje` first" and `ybkmzp` is the child that actually wires the per-host verification decision into both drivers; `h7qsje` being `done` as a backlog item is NOT the same as that work landing, and `ybkmzp` is `reviewed` with `- Readiness: go-pending-approval` as measured at review, so it awaits human approval and then execution. It carries a BLOCKING OQ-01 because the item's fourth question is whether the verb is wanted at all given that the verifier added only nits for roughly 33 percent cost on the strong executor and nobody passes `--validate` on the OC host today. AND IT NOW CARRIES A BLOCKING OQ-05, added at review, because the prompt this plan is required to reuse verbatim instructs the agent to fix defects and commit, which cannot be pointed at an immutable `executed` plan; that conflict is between two constraints the plan and its item each treat as binding, so a human must say which yields.

E-01 IS SAFE TO PERFORM FIRST and is designed to enforce the first gate: it measures whether `ybkmzp` has reached `executed` and STOPS if not. Everything after E-01 is conditional, and E-06 must read OQ-05's recorded answer before E-02 through E-05 proceed, since the prompt-reuse route determines what the tree decision is FOR and whether the verb is coherent at all. A recorded decision that the verb is NOT wanted is a legitimate completed outcome and is more valuable than an unused surface.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Re-locate every symbol by NAME, never by the line numbers cited here: the item's four coordinates were stale at graduation and THIS PLAN's four replacements were stale one day later at review, and both runner files are under concurrent edit by live runs. Do NOT write a second verifier prompt or outcome schema. Do NOT change EITHER host's verification default (they are opposite: F-12), the in-run verifier's effective behavior, or any `executed` plan's record. Do NOT wire the agy host unless the decision requires it. Do NOT relax the reporting-contract parity tests to make room for a prompt change; if a chosen route conflicts with them, report the conflict. Do NOT write a novel `Subject-Type` value into a review record: the vocabulary is closed and a new type requires amending it and its checker together. If a verb is added to the `aw runs` surface, declare spec `25kzda` in `Scope-Paths` BEFORE editing it, and justify the noun against the documented read-only description of `aw runs` (F-18). Paste ACTUAL command output. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the reachability measurement for the verification base and the explicit tracked-versus-gitignored statement for the verdict's destination.
