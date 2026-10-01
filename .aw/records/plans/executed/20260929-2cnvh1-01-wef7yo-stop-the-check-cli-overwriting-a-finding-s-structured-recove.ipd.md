# IPD: Stop the check CLI overwriting a finding's structured recovery with the human fix string

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `2cnvh1` reports that `cli._run_check` computes the HUMAN remediation string via `doctor._categorize_drift` and then writes it INTO every finding's structured `recovery` field (`enriched = ce.enrich_drift(d, recovery=fix or "")`), so the machine record `aw check --json` / `--agent` publishes is not the rule's authored recovery but doctor's prose. VERIFIED AT HEAD `9ebe260f` AND WIDER THAN THE ITEM STATES: the item frames the residue as only affecting a rule whose engine recovery is EMPTY, but measured over this repository's live findings the overwrite corrupts EVERY ONE of them - it replaces a POPULATED engine recovery on the large majority and FABRICATES one on the rest (F-01, F-02). THE COUNTS ARE A LIVE POPULATION AND DRIFT DAILY: authoring measured 17 findings (15 replaced, 2 fabricated) and review re-measured 32 (30 replaced, 2 fabricated) one day later, so re-derive them and treat only the PROPERTY as stable, namely that zero findings are faithful and both partitions are non-empty. The item's own suggested fix is confirmed correct and is one kwarg at one call site (F-06), measured to leave the full suite byte-identical (F-08) and to make all 17 records faithful (F-07).
- Scope: Remove the `recovery=fix or ""` kwarg from the single `ce.enrich_drift` call in `cli._run_check` so the machine finding carries the rule's own `recovery` verbatim instead of doctor's human `Fix:` prose, and pin the property with a hermetic regression test. The human `Fix:` line, the `Next` line, the `--agent` `next` field and `next_actions` are all deliberately UNCHANGED (F-05, F-09). This does NOT touch `doctor.build_remediation` (sibling `iyilwm` owns it), does NOT change `check_engine.enrich_drift`, and does NOT normalize the 22 placeholder-bearing recovery literals (the item's own second question, declined in Deferred).
- Scope-Paths: agent_workflows/cli.py, tests/test_check_recovery_fidelity.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 2cnvh1
- Blocks-Release: next
- Set: 2cnvh1
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: wef7yo

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: wef7yo verified (set 2cnvh1, attempt 1). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261001-mu4k1g-01-mu4k1g-test-box-renderer-invariants-across-swept-inputs-e.backlog.md: changed by the plan's approved execution (auto-reconciled by aw agy run)]
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-301 through PR-306, all FIXED in place. Reviewed at HEAD `c32a71ea` in an isolated lane; typed record at `.aw/records/reviews/20260929-2cnvh1-01-wef7yo-stop-the-check-cli-overwriting-a-finding-s-structured-recove.review.md` with six recorded Decisions (D-1..D-6), all reversible. `aw ipd lint --phase author` conformed with ZERO findings BEFORE semantic review and `--phase review-finalize` still conforms with zero findings, zero density advisories and zero carrier drifts.
  THE DIAGNOSIS IS EXACT AND MOST OF THE EVIDENCE RE-MEASURED CORRECT, by running it rather than reading it. Every link of F-01's chain verified in the shipped code. F-02's PROPERTY reproduced exactly (zero faithful findings, both partitions non-empty) while its COUNTS drifted 17/15/2 -> 32/30/2 in one day. F-03's hermetic witness drove end to end at rc 1 with exactly one finding and both strings byte-identical to its quotes, leak-free. F-05/F-06 reproduced on all three surfaces: the scoped fix makes the machine record faithful while the human `Fix:`, `Next` and agent `next` stay byte-identical. F-07's 4-way matrix reproduced in SHAPE (0/32, 30/32 with 2 still fabricated, 32/32, 32/32), confirming the two sibling plans are independent and order-free and that `iyilwm` alone does not close this item; both siblings confirmed `reviewed` with `doctor.py`-only scope. F-08 reproduced at `3246 passed`. F-09, F-11, F-12 verified. The LEAK RULE is verified and load-bearing: two rules really do interpolate the absolute repo root into the recovery this fix publishes.
  PR-301 (HIGH) INVERTS A LOAD-BEARING PREMISE. F-10 claimed the over-broad fix turns four named tests red at `4 failed, 3242 passed`, and FOUR places rested on it (E-01's prohibition, the Deferred row, V-01(b), V-03(f), validation item 4). Measured three ways - two monkeypatch formulations and a `sitecustomize` import hook staging the source change, with the inversion confirmed active behaviorally first - it is FALSE: the suite stays FULLY GREEN at `3246 passed, 2 skipped` and all four tests PASS under it. The consequence is worse than a wrong number: the scope fence the plan most depends on is not test-enforced at all, so an executor who generalizes the fix into the helper gets a green suite and silently inverts the contract for 40 correct callers. Fixed by rewriting F-10 with the falsification and the stronger conclusion, adding F-13's re-measured 47/40/7 census, and converting validation item 4, V-01(b) and V-03(f) from test runs to `git diff --name-only` inspections that explicitly FORBID citing those four tests.
  FIVE FURTHER FINDINGS. PR-302: F-04's and OQ-01's idiom argument names `plans_index` and `prompts_index` as bare-call precedents when both pass `recovery=` explicitly (7 no-recovery sites, not 8; 47 total, not 48), so the argument is withdrawn while the choice survives on drift resistance. PR-303: E-03's EMPTY-case clause is unsatisfiable against the single witness it mandates, since `check.live-bug-ungated` always carries a populated recovery; a measured second witness was added. PR-304: four sites stated the live counts as bare facts, including the paragraph describing what a human is approving. PR-305: F-09 cites the goldens at a path that does not exist (they are under `tests/fixtures/conformance_goldens/`), though its substantive claim verified in full. PR-306: the mutation-proof method note gives two pieces of wrong guidance, now replaced with a recipe re-verified at review.
  BASELINE MEASURED GREEN AT REVIEW HEAD, unchanged by this review (which edits only planning records): bare `python3 -m pytest` -> `3246 passed, 2 skipped, 3 warnings`; `aw check reviews` -> `CONFORMS`, 0 errors 0 warnings. Every probe ran in memory from the gitignored `tmp/`; `git status --short` was empty before and after each.
  READINESS `go-pending-approval`: verdict is APPROVE WITH REVISIONS APPLIED, no finding is left OPEN or DEFERRED, and both open questions are `resolved` with `Blocking: no`. Human approval is still required and this review does not grant it.

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `2cnvh1`. Every measurement re-taken in a lane worktree at HEAD `9ebe260f`; none carried over from the item. The item's core diagnosis HOLDS, its suggested fix is confirmed implementable and safe, and its BLAST RADIUS IS UNDERSTATED: the item reports the residue as the empty-recovery case only, but the overwrite corrupts EVERY live finding, the large majority of which have a populated engine recovery (F-01, F-02; authoring measured 17/15/2 and review re-measured 32/30/2, so the counts drift and only the property is stable). The relationship with sibling `iyilwm` was measured directly in a 4-way composition matrix rather than reasoned about (F-07): the two fixes are independent and order-free, and only THIS one makes the machine record faithful. OQ-01 records why the fix drops the kwarg rather than passing `recovery=d.recovery`; OQ-02 records why `next_actions` is deliberately left alone.
- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw check`'s machine-readable finding tell the truth about how to fix itself. A rule author who populates the documented `recovery` field should see that exact string in `data.policy_findings[*].recovery`, instead of having it silently replaced by a sentence telling the reader to inspect frontmatter. Equally, a rule that authors NO recovery should publish an empty one rather than a fabricated remedy it never wrote.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: stop the overwrite

- [x] E-01 In `cli._run_check`, drop the `recovery=` kwarg from the `enrich_drift` call so the finding keeps the recovery its rule authored. Locate it by CONTENT, not by line offset: it is the statement `enriched = ce.enrich_drift(d, recovery=fix or "")`, immediately below the comment `# Prefer any determinism/assurance/severity already stamped on the Drift, else the registry.` and inside the `for d in drift:` loop that unpacks `_doctor._categorize_drift(d, repo_root)`. It becomes `enriched = ce.enrich_drift(d)`.

  PASS NO RECOVERY AT ALL; do NOT write `recovery=d.recovery`. Both are behaviorally identical today because `enrich_drift` resolves `recovery=recovery or drift.recovery` (read the `_replace` call in `check_engine.enrich_drift`), so the explicit form is a no-op that re-states the default. OQ-01 records the choice, and its load-bearing reason is DRIFT RESISTANCE, not idiom: the bare call always inherits whatever precedence the helper defines, whereas an explicit `recovery=d.recovery` is a second, unguarded copy of that rule at the call site. (The authored idiom argument named `plans_index` and `prompts_index` as bare-call precedents; measured at review they both pass `recovery=` explicitly, so that argument is withdrawn - see F-14. The choice is unchanged.)

  DO NOT TOUCH `fix` OR ANY OTHER USE OF IT. The local `fix` variable stays exactly as it is and keeps feeding BOTH `Diagnostic(fix=fix or None)` and the `seen_fixes` set that builds `next_actions`. That is the whole reason this change is safe and narrow: the human surface reads `Diagnostic.fix`, never the finding's `recovery`, so removing the kwarg cannot alter what a human sees (F-05, F-09 measure this on both the human and the agent surface). An executor who also "tidies" `seen_fixes` or the `Diagnostic` has left the scope fence.

  DO NOT CHANGE `check_engine.enrich_drift`, AND NOTE THAT NO TEST WILL STOP YOU. It is used by 47 call sites, 40 of which pass a rule-authored `recovery=` that MUST keep winning (F-04, F-13). Inverting its precedence was re-measured at review and leaves the suite FULLY GREEN at `3246 passed` (F-10, corrected: the authored claim that it turns 4 tests red is FALSIFIED, and all four named tests pass under the inversion). So this constraint is enforced by REVIEW OF THE DIFF and by V-01(b), never by a test run: a green suite is NOT evidence you stayed scoped. The defect is the one CALLER, not the helper.
  - Depends on: none
  - Expected outcome: `aw check --json`'s `data.policy_findings[*].recovery` is byte-identical to the `Drift.recovery` the rule emitted, for every finding, including the empty string where the rule authored none. The human `Fix:`/`Next` lines, the `--agent` `next` field and `next_actions[*].command` are unchanged.
  - Execution state: performed

- [x] E-02 Update the comment above the changed call so it stops describing behavior the code no longer has, and records why the recovery is left alone. The existing comment reads `# Prefer any determinism/assurance/severity already stamped on the Drift, else the registry.`, which is accurate about the three metadata fields but silent on the fourth field the call used to overwrite, and that silence is what let the overwrite survive since `a08a4f50`.

  NAME THE DIRECTION OF TRAVEL: `recovery` is the RULE's authored fix and travels to the MACHINE record; `Remediation.detailed_fix` (the local `fix`) is the HUMAN prose and travels to `Diagnostic.fix` and `next_actions`. The two must not be crossed. Keep it to that distinction plus one clause on why `fix` is still computed here (it feeds the `Diagnostic` and `seen_fixes`), so the next reader does not "simplify" the loop by deleting `fix`.

  ALSO RECORD THE ONE THING THIS DOES NOT FIX, because it is the item's own open question and a reader will otherwise assume the surface is now fully honest: `next_actions` is still built from the human prose (`seen_fixes`), so a `NextAction.command` on this surface can still hold a non-runnable sentence. Declined in Deferred with a carrier; the comment must point at it rather than imply it was handled.
  - Depends on: E-01
  - Expected outcome: A comment at the changed call naming the recovery-versus-fix direction of travel, why `fix` is still computed, and the still-open `next_actions` prose question with its carrier.
  - Execution state: performed

### Task group 2: pin the property

- [x] E-03 Add `tests/test_check_recovery_fidelity.py` asserting the machine finding's `recovery` is byte-identical to the engine's, driven through the REAL `cli._run_check` on a hermetic fixture repo rather than by calling `enrich_drift` directly. A unit test on the helper would pass on the shipped code and prove nothing, because the helper is not the defect.

  USE THE MEASURED-HERMETIC WITNESS FOR THE POPULATED CASE: build a fixture repo with `tests/test_check_engine_release_gate._create_minimal_repo`, seed one `open`/`Work-Kind: bug` backlog item with no `Blocks-Release`, and run `cli._run_check` with `type="release-gates"` and `json=True`, capturing stdout via `contextlib.redirect_stdout`. That yields EXACTLY ONE finding, `check.live-bug-ungated`, whose engine recovery is populated and interpolates only the fixture's own id6 (F-03, re-verified at review: rc 1, 1 finding, both strings byte-identical to F-03's quotes, and no absolute temp path anywhere in the published recovery).

  THE EMPTY CASE NEEDS A SECOND WITNESS, BECAUSE THE FIRST ONE CANNOT PRODUCE IT (PR-303). `check.live-bug-ungated` ALWAYS carries a populated engine recovery, and the `release-gates` target reaches no rule whose recovery is empty, so clause (c) below is unsatisfiable against this fixture alone. Measured at review, the cheapest second witness is: on the SAME `_create_minimal_repo` fixture, write one backlog file whose NAME does not conform (for example `badly-named-file.backlog.md`, with valid front matter) and run `cli._run_check` with `type="backlog"`. That yields `check.name-nonconformant`, whose engine recovery is `''` and which is one of the two rules F-02 measures as FABRICATED, so it is exactly the partition the backlog item singles out. Use two small fixtures rather than forcing one to do both jobs, and keep each hermetic and leak-free.

  ASSERT, in one test file: (a) on the FIRST witness, the finding's `recovery` EQUALS the `recovery` on the corresponding `Drift` returned by `check_engine.check_release_gates(repo)` for the same rule, compared with `assertEqual` on the full string so a prefix match cannot pass; (b) that value does NOT equal the human `fix` string `doctor.build_remediation` produces for that same Drift, which is what makes the test fail on the shipped code; (c) on the SECOND witness, the EMPTY case: a rule whose Drift carries `recovery=""` publishes `""` and not a fabricated string, since that is the half the backlog item singles out and (a) alone does not cover it. Derive the empty expectation the same way, by asserting the published value equals the engine `Drift.recovery` for that rule and that it is falsy, rather than by transcribing `""` alone, so the test still means something if the rule ever gains a recovery; (d) the human surface is UNCHANGED, by asserting the `--agent` record's `next` field still equals the human prose string, which is the guard that stops a future "fix" from also emptying `Diagnostic.fix`.

  DERIVE BOTH SIDES AT RUN TIME. Do NOT transcribe either literal into the test: the engine recovery string interpolates a fixture id6 and the human string interpolates a path, and F-02 shows the live population is a moving target. Compute the expected value by calling the engine, and compute the human value by calling `build_remediation`; assert the RELATIONSHIP between them. A test carrying a hard-coded sentence is a time bomb, and the sibling plan `iyilwm` is about to CHANGE the human string, which would break a transcribed assertion for a reason unrelated to this defect.

  DO NOT ASSERT A TOTAL FINDING COUNT for the whole repository. The 17 findings F-02 measures are this checkout's live state at authoring and will differ in the executor's tree; the fixture repo's count of 1 is the only count safe to assert.
  - Depends on: E-01
  - Expected outcome: A test file that FAILS on the shipped code (because `recovery` equals the human prose there) and PASSES after E-01, covering the populated case, the empty case, and the human-surface-unchanged guard.
  - Execution state: performed

## Project conventions discovered (Step 0)

- CODE IS CITED BY SYMBOL OR QUOTED CONTENT, NOT BY BARE OFFSET (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This is not ceremony here: the sibling item `evwmm2` located its target by a bare offset and plan `iyilwm`'s F-03 measured that the offset had already expired onto an unrelated branch. The backlog item for THIS plan cites its target by the quoted statement text, which is why E-01 could locate it unambiguously; this plan keeps that discipline.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Every measurement here used a bare `python3 -m pytest`; the baseline at authoring HEAD `9ebe260f` was `3246 passed, 2 skipped, 3 warnings in 53.35s` with 207 deselected. TREAT THAT AS CONTEXT AND RE-DERIVE YOUR OWN: `iyilwm` recorded `3087` then `3158` at two HEADs days apart, so the number moves.
- A SHARED CHECKOUT MEANS NO SPECULATIVE FILE MUTATION. Every measurement in this plan that required altered behavior was staged IN MEMORY, via a pytest plugin in a gitignored `tmp/` directory inside the lane that rebinds `check_engine.enrich_drift` to a wrapper dropping the kwarg only when the calling frame is `_run_check`. `git status --short` was empty before and after every run. The same method is mandated for the E-03 mutation proof.
- `recovery` IS THE DOCUMENTED FIELD FOR THE RULE'S OWN FIX, which is what makes this a defect rather than a design choice. `artifact_core.Drift`'s docstring names it "the exact recovery command, when one exists" and says the trailing fields "are populated by `check_engine.enrich_drift` from the rule registry"; `check_engine.finding_dict`'s docstring repeats "the exact recovery command". Neither says "or whatever prose the human renderer computed".
- THE HUMAN AND MACHINE SURFACES READ DIFFERENT FIELDS, and that separation is what makes this fix narrow. `renderers.py` calls `_doctor._categorize_drift` itself and prints its `fix`; the `Diagnostic` carries `fix`; only `finding_dict` reads `Drift.recovery`. So the machine record can be corrected without touching a single character a human sees (measured in F-05 and F-09).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE ITEM'S CORE CLAIM IS VERIFIED.** `cli._run_check` computes the human string and writes it into the finding: the loop unpacks `title, dir_str, fname, extra, fix = _doctor._categorize_drift(d, repo_root)` and then executes `enriched = ce.enrich_drift(d, recovery=fix or "")`. `_categorize_drift`'s 5th return value is `rem.detailed_fix` from `build_remediation` (read the assignment `fix = rem.detailed_fix` at the top of that function). Because `enrich_drift` resolves `recovery=recovery or drift.recovery`, a non-empty `fix` WINS over the rule's own value, and `finding_dict` then serializes it as `recovery`. | Read of the `for d in drift:` loop in `cli._run_check`; read of `fix = rem.detailed_fix` in `doctor._categorize_drift`; read of the `recovery=recovery or drift.recovery` line in `check_engine.enrich_drift` and of `"recovery": drift.recovery` in `finding_dict`; `git log -1 -L` on the offending line dating it to `a08a4f50` (2026-08-28), i.e. pre-existing and older than the item. |
| F-02 | **THE ITEM UNDERSTATES THE BLAST RADIUS: THE OVERWRITE CORRUPTS EVERY LIVE FINDING, NOT ONLY THE EMPTY-RECOVERY ONES.** RE-MEASURED AT REVIEW HEAD `c32a71ea` and the PROPERTY reproduced exactly while the COUNTS drifted in one day: **32** findings, **0** faithful, **30** with a populated engine recovery REPLACED, **2** FABRICATED (both `check.name-nonconformant`, engine recovery `''`). Authoring measured 17/0/15/2. So the stable claim is "zero faithful, both partitions non-empty", and the digits below are a snapshot. The item's headline is the fabrication case ("a rule that populates no recovery gets a fabricated one"), and its own "WHY THIS IS SEPARATE" paragraph asserts `iyilwm` "incidentally repairs this path for every rule that POPULATES recovery". Measured on this repository's tree at HEAD `9ebe260f`: 17 findings, of which the overwrite REPLACES a populated engine recovery on 15 and FABRICATES one on 2 (both `check.name-nonconformant`, whose engine recovery is `''`). So the populated case is the MAJORITY, not the part already handled. THE COUNT IS A LIVE POPULATION AND MUST BE RE-DERIVED, NOT TRANSCRIBED; the PROPERTY this row asserts is that both partitions are non-empty and both are corrupted. | Scratch probe driving `check_engine.check_types(root, ["all"], collisions=True)` through the exact `_categorize_drift` -> `enrich_drift(recovery=fix)` -> `finding_dict` chain `cli._run_check` uses and classifying each finding: prints `overwrote a POPULATED engine recovery: 15` and `FABRICATED a recovery where engine had none: 2`. Per-rule dump showing e.g. `check.ipd-uncarried-obligation` engine `'hand it off: add `- Carrier: <id6>` ...'` versus published `'inspect .aw/records/plans/pending/<...>.ipd.md frontmatter and schema conformity.'`. |
| F-03 | **A HERMETIC, DETERMINISTIC WITNESS EXISTS AND WAS DRIVEN END TO END**, which is what lets E-03 be a real test instead of a snapshot of this checkout. Using `tests/test_check_engine_release_gate._create_minimal_repo` plus one seeded `open`/`Work-Kind: bug` item with no `Blocks-Release`, `cli._run_check(type="release-gates", json=True)` returns rc 1 and EXACTLY ONE finding, `check.live-bug-ungated`. Shipped, its published recovery is `'inspect .aw/records/backlog/open/20260920-bug001-01-bug001-test-defect.backlog.md frontmatter and schema conformity.'`; the engine's real value is `'aw backlog set open bug001 --blocks-release next  (or hand the gate to the plan/spec that graduated it, or file an explicit exemption if this bug genuinely does not gate the release)'`. With the fix staged in memory the published value is that engine string and an equality assertion against it returns `True`. It is also LEAK-FREE: the location is repo-relative and the recovery interpolates only the fixture's own `bug001`, never an absolute path. | The probe run on the fixture repo printing `rc: 1 policy_findings: 1` and the shipped recovery; the same probe under the staged plugin printing `ENGINE recovery`, `AFTER FIX` and `IDENTICAL : True`; read of `test_cli_check_release_gates_runner` confirming the `argparse.Namespace` shape reused. |
| F-04 | THE DEFECT IS THE CALLER, NOT THE HELPER, AND THE NUMBERS SAY SO LOUDLY. `enrich_drift` has **47** call sites across the package (authoring said 48; re-measured at review, see F-13), and **40** of them pass a `recovery=` kwarg carrying the RULE's authored string, which must keep winning. `cli._run_check` is the ONLY caller that passes a value derived from the human renderer. So the fix must be scoped to that one call; changing the helper's precedence would invert the contract for 40 correct callers. THE `8`-SITE / `plans_index` / `prompts_index` IDIOM SUB-CLAIM IS WITHDRAWN AS FALSE: there are **7** no-recovery sites and they are `check_engine.py` (six) plus `work_cmd.py` (one); `plans_index` and `prompts_index` both pass `recovery=` explicitly (F-14). | Scratch bracket-matching scanner over `agent_workflows/**/*.py` counting `enrich_drift(` calls and those whose argument text contains `recovery=`: prints `47` and `40`, with the 7 no-recovery sites listed. Read of the `cli._run_check` site confirming its value comes from `_categorize_drift`, and of a representative engine site (`check_engine.check_live_bug_gate`) confirming its value is a rule literal. |
| F-05 | **THE FIX CANNOT CHANGE WHAT A HUMAN SEES, MEASURED ON BOTH SURFACES RATHER THAN ARGUED.** The human renderer never reads `Drift.recovery`: `renderers.py` calls `_doctor._categorize_drift` itself and prints its `fix`, and the `Diagnostic` the CLI builds carries `fix=fix or None`. Running the F-03 fixture shipped and fixed, in both human and `--agent` mode, the `Fix:` line, the `Next` line and the agent `next` field are BYTE-IDENTICAL across the two, all three reading `inspect .aw/records/backlog/open/<...>.backlog.md frontmatter and schema conformity.`. Only `data.policy_findings[*].recovery` moves. | The fixture driven through `cli._run_check` in `agent=False` and `agent=True` modes, shipped and under the staged plugin, with the `Fix:`/`Next`/`next` lines printed for each: all four pairs identical. Read of `renderers.py`'s own `_categorize_drift` call and of the `Diagnostic(... fix=fix or None)` construction. |
| F-06 | **THE ITEM'S SUGGESTED FIX IS CORRECT AND THE TWO FORMS IT OFFERS ARE EQUIVALENT TODAY.** The item says "Either call `ce.enrich_drift(d)` with no recovery kwarg, or pass `recovery=d.recovery`". Both produce identical output, because `enrich_drift` computes `recovery=recovery or drift.recovery`, so passing `d.recovery` explicitly re-states the default. E-01 takes the bare form for idiom agreement (F-04 shows 8 of 48 sites already pass nothing, including `work_cmd`, `plans_index` and `prompts_index`), recorded as OQ-01 rather than left as an unexplained coin flip. | Read of the `_replace(... recovery=recovery or drift.recovery ...)` expression in `enrich_drift`; the staged-fix probe implementing the bare form and measuring output identity with the engine value (F-03); the call-site census from F-04. |
| F-07 | **THIS PLAN AND SIBLING `iyilwm` ARE INDEPENDENT AND ORDER-FREE, MEASURED IN A 4-WAY MATRIX, AND ONLY THIS ONE MAKES THE MACHINE RECORD FAITHFUL.** Staging both changes in memory over this repo's live findings: SHIPPED gives 0 faithful with 2 fabricated; `iyilwm` ALONE leaves the fabricated 2 STILL fabricated; THIS PLAN alone gives ALL faithful and 0 fabricated; BOTH gives the same. Authoring measured this as 0/17, 15/17, 17/17, 17/17; review RE-RAN the identical 4-way matrix at HEAD `c32a71ea` and got 0/32, 30/32, 32/32, 32/32, i.e. the same SHAPE on a drifted population, which is the result that matters. So neither plan blocks the other, either order works, and `iyilwm` alone does NOT close this item. This also CORRECTS the item's own framing (F-02): `iyilwm` repairs the populated case only as a side effect of changing the human string, and if `iyilwm` ever stopped doing so this defect would resurface, which is exactly why the machine record needs its own fix and its own test. | Scratch composition probe wrapping `doctor.build_remediation` with `iyilwm`'s E-01 preference and/or dropping the `cli` kwarg, tabulating faithful/fabricated counts over `check_types(root, ["all"])` for all four cells: prints the four rows quoted above. Read of `iyilwm`'s `- Scope-Paths:` (`agent_workflows/doctor.py, tests/test_doctor.py`) confirming zero file overlap with this plan's. |
| F-08 | **THE FIX BREAKS NOTHING IN THE SHIPPED SUITE, measured rather than predicted.** The scoped change staged in memory (a plugin rebinding `check_engine.enrich_drift` to drop the kwarg ONLY when the calling frame's `co_name` is `_run_check`) leaves a full bare run at `3246 passed, 2 skipped, 3 warnings`, byte-identical in count to the unpatched baseline, with `git status --short` empty before and after and no tracked file modified. | Bare `python3 -m pytest` unpatched: `3246 passed, 2 skipped, 3 warnings in 53.35s`. The same command with `PYTHONPATH=tmp/<scratch> -p <plugin>`: `3246 passed, 2 skipped, 3 warnings in 47.26s`. `git status --short` empty after both. |
| F-09 | **NOTHING PINS THE CURRENT (WRONG) VALUE, so E-01 cannot break a golden.** RE-VERIFIED AT REVIEW. No test in `tests/` reads `data.policy_findings`; a repo-wide search for that key finds hits only in `agent_workflows/cli.py` (the construction and its comment). The three `check_findings.*` goldens are hand-written fixtures that contain no `recovery` key at all and are not produced by `_run_check` (their real path is `tests/fixtures/conformance_goldens/`, not the bare `conformance_goldens/` cited here; corrected as F-16), and the `recovery` assertions that DO exist in `tests/` (three in `test_check_engine.py`, two in `test_check_engine_spec_criteria.py`) are engine-level, asserting on `Drift.recovery` before the CLI ever sees it - so they assert the value this plan RESTORES. | `rg -n policy_findings` over the repo returning only the two `cli.py` hits; read of all three `check_findings.*.golden` files confirming no `recovery` key; read of the `assertIn(..., d_p.recovery)` / `assertIn(expected_line, drifts[0].recovery)` assertions confirming they call the engine directly. |
| F-10 | **THE OVER-BROAD FIX IS STILL THE WRONG CHANGE, BUT IT IS NOT TEST-DETECTED, AND THE ORIGINAL FINDING'S CENTRAL CLAIM IS FALSIFIED.** CORRECTED AT REVIEW (PR-301). The authored claim was that inverting `enrich_drift`'s precedence so the drift's own recovery always wins turns the suite RED at `4 failed, 3242 passed`, naming four tests. RE-MEASURED at review HEAD `c32a71ea`, staging the inversion in memory via a `sitecustomize` import hook in the gitignored `tmp/` (behavior confirmed inverted first: a Drift carrying `recovery='DRIFT-OWN'` enriched with `recovery='CALLER-PASSED'` resolves to `DRIFT-OWN`), a bare full suite reports **`3246 passed, 2 skipped, 3 warnings`** - FULLY GREEN. All four named tests EXIST (each collects) and all four PASS under the inversion (`4 passed in 0.30s`). Two independent monkeypatch formulations reproduced the same green result. SO THE SUITE DOES NOT GUARD `enrich_drift`'s PRECEDENCE AT ALL, which is a WEAKER position than the plan assumed and makes the scope fence MORE important rather than less: an executor who "generalizes" E-01 into the helper gets a green suite and ships a silent contract inversion for F-04's 40 correct callers. The fence must therefore be held by REVIEW OF THE DIFF, not by a test run. | Inversion staged in memory (no tracked file edited; `git status --short` empty before and after): bare `python3 -m pytest` -> `3246 passed, 2 skipped, 3 warnings in 48.83s`. The four named tests under the inversion -> `4 passed in 0.30s`. Each of the four confirmed to exist via `--collect-only`. Unpatched baseline at the same HEAD -> `3246 passed, 2 skipped, 3 warnings`. |
| F-13 | **THE 40-CALLER CONTRACT IS REAL EVEN THOUGH NO TEST GUARDS IT, so F-10's conclusion survives its own correction.** Re-measured at review: `enrich_drift` has **47** call sites in `agent_workflows/` (not 48), of which **40** pass a `recovery=` kwarg and **7** pass none. A representative engine caller (`check_engine.check_live_bug_gate`) passes a rule literal; `cli._run_check` is the only caller passing a value derived from the human renderer. Inverting the helper would make an already-stamped `recovery` beat a fresh rule-authored one for all 40, which is a real behavior change that the suite simply fails to notice. | Bracket-matching census over `agent_workflows/**/*.py`: `47` call sites, `40` with `recovery=`, `7` without. Read of the `cli._run_check` site and of `check_live_bug_gate`'s literal. |
| F-15 | **THE MANDATED HERMETIC WITNESS CANNOT EXERCISE THE EMPTY CASE, so E-03's clause (c) was unsatisfiable as authored and needs a second fixture.** Found at review. `check.live-bug-ungated` always carries a populated engine recovery, and driving the `release-gates` target over the `_create_minimal_repo` fixture yields exactly that one finding, so no rule with `recovery=""` is reachable from it. A second, equally cheap and equally hermetic witness exists and was driven end to end: on the same fixture, one backlog file whose NAME does not conform (`badly-named-file.backlog.md`, valid front matter) driven through `type="backlog"` yields `check.name-nonconformant` with engine recovery `''`, which is one of the two FABRICATED findings F-02 measures. | The `release-gates` fixture probe printing `release-gates drifts: [('check.live-bug-ungated', ...)]` and `any with EMPTY engine recovery? False`. The second probe printing `rc 1 findings 2` with `check.name-nonconformant published='the slug in .aw/records/backlog/open/badly-named-fil...'`, i.e. fabricated prose over an empty engine value. |
| F-16 | **F-09's GOLDEN-FILE PATH IS WRONG, THOUGH ITS SUBSTANTIVE CLAIM HOLDS.** The finding cites "the three `conformance_goldens/check_findings.*` goldens"; no `conformance_goldens/` directory exists at the repository root. They live at `tests/fixtures/conformance_goldens/check_findings.{human,agent,json}.golden`. The claim ITSELF verified at review: all three contain ZERO `"recovery"` keys, they are hand-written fixtures consumed by `tests/conformance_matrix.py` rather than produced by `_run_check`, and nothing in `tests/` reads `policy_findings` (the only two repo-wide hits are the construction and its comment in `cli.py`). So E-01 cannot break a golden. | `find . -name "check_findings*"` returning the three `tests/fixtures/conformance_goldens/` paths and nothing at the cited location; `grep -c '"recovery"'` returning 0 on each; `grep -rn policy_findings` over the repo returning only `agent_workflows/cli.py:12714` and `:12717`. |
| F-14 | **F-04's IDIOM ARGUMENT FOR THE BARE CALL IS WRONG ON ITS FACTS, though its conclusion stands on a different ground.** F-04 and OQ-01 both claim "8 of the 48 call sites already pass no recovery, including `work_cmd.py`, `plans_index.py` and `prompts_index.py`". MEASURED: **7** sites pass no recovery, and they are `check_engine.py` at six places plus `work_cmd.py` at one. `plans_index.py` and `prompts_index.py` DO call `enrich_drift` but both pass `recovery=` explicitly (`recovery="aw index plans"`, `recovery="aw index prompts"`), so two of the three modules named as precedent are counter-examples. The bare form is still correct, on OQ-01's SECOND and stronger ground (drift resistance: an explicit `recovery=d.recovery` duplicates the helper's precedence rule at the call site and silently disagrees with it if that rule ever changes). | Bracket-matching census listing the 7 no-recovery sites; read of `plans_index.py`'s `_ce.enrich_drift(..., recovery="aw index plans")` and `prompts_index.py`'s `recovery="aw index prompts"`. |
| F-11 | NO SPEC GOVERNS THIS FIELD'S RENDERING, so no spec amendment is owed. A search over `.aw/records/specs/` for the finding shape finds: the `approved` spec `25kzda`'s "Exact recovery command" tables, which govern the `check.ipd-dependency-*` family's rule catalog and not `finding_dict`'s serialization; and the `draft` spec `pqsx96`, whose `I-09` row mentions "an exact rename recovery command" as a property of the naming check. Neither specifies where `aw check`'s machine `recovery` value comes from, and nothing references `finding_dict`, `policy_findings` or `POLICY_SCHEMA_VERSION`. The contract lives in CODE docstrings (`Drift`, `finding_dict`), which this plan makes the behavior MATCH rather than change. | `rg -n "recovery" .aw/records/specs/*/*.spec.md` with each hit classified; `rg -n "finding_dict\|policy_findings\|schema_version" .aw/records/specs/` returning no hit for the first two; read of the `25kzda` §2.10 table header and the `pqsx96` `I-09` row. |
| F-12 | THE `next_actions` PROSE PROBLEM IS REAL, IS UNCHANGED BY THIS PLAN, AND IS THE ITEM'S OWN SECOND QUESTION. `cli._run_check` builds `next_actions` from `seen_fixes`, which collects the human `fix` string, NOT from the finding's `recovery`. So this fix leaves that slot exactly as it is - measured on this tree, all 17 `next_actions[*].command` values are `inspect ... frontmatter` prose or a 200-character sentence containing `--slug <corrected-slug>`, i.e. 2 of the 17 distinct strings contain a `<` placeholder. The item explicitly parks this ("Then decide separately whether `next_actions` should carry a recovery string at all"), and it is declined here with a carrier rather than silently inherited. | Read of the `seen_fixes.add(fix)` loop and the `for f in seen_fixes: next_actions.append(NextAction(command=f))` block; `aw check all --json` at authoring HEAD printing all 17 `next_actions[*].command` values; the staged-fix run showing the same 17 unchanged. |

## Proposed changes (ordered, validatable)

1. Drop the `recovery=fix or ""` kwarg from the single `ce.enrich_drift` call in `cli._run_check`, leaving `fix` and every other use of it untouched (E-01, closing F-01/F-02, scoped by F-04, proven safe by F-08 and F-09, and deliberately NOT the global change F-10 measures as red).
2. Correct the comment above that call to name the recovery-versus-fix direction of travel, why `fix` is still computed, and the still-open `next_actions` question (E-02, per F-12).
3. Add `tests/test_check_recovery_fidelity.py` pinning machine-record fidelity through the real `cli._run_check` on the hermetic `check.live-bug-ungated` witness, covering the populated case, the empty case, and a human-surface-unchanged guard, with both sides derived at run time (E-03, per F-03/F-05, and necessary because F-09 shows nothing guards this today).

## Deferred / out of scope (with reason)

- `next_actions` KEEPS CARRYING NON-RUNNABLE HUMAN PROSE. F-12 measures that slot being built from `seen_fixes` (the human `fix`), so this plan neither improves nor worsens it: 2 of the 17 distinct strings on this tree contain a `<placeholder>` and none is runnable as printed. The backlog item explicitly parks this as a separate contract question ("decide separately whether `next_actions` should carry a recovery string at all"), and answering it means deciding whether a `NextAction.command` may hold prose at all, then normalizing 22 recovery literals in `check_engine.py` - a different file, a different contract, and a public output surface change that deserves its own review.
  - Carrier: 2cnvh1
- THE 22 PLACEHOLDER-BEARING RECOVERY LITERALS ARE NOT NORMALIZED. The item's closing sentence counts 8 of 22 `recovery` literals in `check_engine.py` containing `<placeholder>` segments. Making them runnable is a `check_engine.py` change this plan's `- Scope-Paths:` deliberately excludes, and it is only worth doing once the `next_actions` question above is answered, since that answer decides whether "runnable" is even the target shape. Note this plan makes the situation strictly more honest in the meantime: a placeholder-bearing recovery published verbatim is at least the rule's own documented guidance, whereas the shipped string is prose the rule never wrote.
  - Carrier: 2cnvh1
- `doctor.build_remediation` IS NOT TOUCHED. The generic `inspect ... frontmatter and schema conformity.` fallback that supplies the offending string is sibling plan `iyilwm`'s E-01 (item `evwmm2`), which is `reviewed` and awaiting approval, and `x19law`'s (item `cciw6g`) for the sentinel case. F-07 measures the two changes as independent and order-free, and both siblings' scope fences explicitly reserve `cli.py` for this plan. Editing `doctor.py` here would duplicate a reviewed plan and guarantee a conflict.
  - Carrier-Declined: No obligation is left outstanding. The human `Fix:` string is `iyilwm`'s and `x19law`'s declared deliverable, each with its own backlog item and release gate, so the work is carried - by those plans, not by a new carrier. Filing one would assert an uncovered gap that F-07 measures to be covered.
- `check_engine.enrich_drift`'s PRECEDENCE IS LEFT ALONE. 40 of its 47 callers legitimately pass a rule-authored `recovery=` that must win over an already-stamped value (F-04, F-13), so inverting the helper would silently change behavior for all of them. CORRECTED AT REVIEW: the authored claim that the global change turns 4 shipped tests red is FALSIFIED (F-10) - the inversion leaves the suite fully green at `3246 passed` and all four named tests pass under it. The contract is therefore real but UNGUARDED, which makes the fence a review-of-diff obligation rather than a test-detected one. The helper is not defective; one caller is.
  - Carrier-Declined: No obligation is left outstanding. After E-01 every caller passes a value consistent with the helper's documented `recovery or drift.recovery` precedence, so there is no residual defect to carry.
- NO HUMAN/AGENT SURFACE PARITY TEST IS ADDED. `iyilwm` records that no such test exists (`tests/test_ci_check_parity.py` was deleted in the suite trim `19313eed`) and defers it to this item. It is still declined, for a reason measured here rather than inherited: F-05 shows the two surfaces legitimately read DIFFERENT fields, so a naive parity test asserting they agree would be asserting a falsehood, and E-03(d) pins the honest property instead (the human surface does not change). A real parity test would first have to define which divergences are correct, which is the `next_actions` contract question above.
  - Carrier: 2cnvh1

## Scope check

- Over-scope: none. `agent_workflows/cli.py` receives ONE kwarg removal inside `cli._run_check` plus the E-02 comment; no other statement in the loop changes, `fix` keeps both its consumers (`Diagnostic(fix=...)` and `seen_fixes`), no signature changes, and no other function in the 12,000-line module is touched. `tests/test_check_recovery_fidelity.py` is a NEW file, so no existing test is edited, weakened or deleted; it IMPORTS `_create_minimal_repo` from `tests/test_check_engine_release_gate.py` and does not modify it, which is why that file is not in `- Scope-Paths:`. `agent_workflows/check_engine.py`, `agent_workflows/doctor.py` and `agent_workflows/renderers.py` are NOT in `- Scope-Paths:` and must not be committed. No spec is touched (F-11) and no `.aw/` record other than this plan changes.
- Under-scope: Four gaps are recorded as decisions above rather than closed. (1) `next_actions[*].command` still carries non-runnable human prose, which is the item's own parked second question (F-12). (2) The 22 recovery literals are not normalized into runnable commands. (3) The human `Fix:` string is still the generic frontmatter sentence for branchless rules, which is `iyilwm`'s and `x19law`'s deliverable, not this plan's (F-07 measures the boundary exactly). (4) No human/agent parity test is added, and F-05 explains why a naive one would assert a falsehood. After this plan, `aw check`'s machine record carries the recovery its rule authored, verbatim, and publishes no recovery it did not - which is the defect `2cnvh1` reports.

## Required tests / validation

All validation runs BARE (`python3 -m pytest`), per the execution contract and the `addopts` already configured in `pyproject.toml`.

RE-DERIVE YOUR OWN BEFORE-BASELINE; DO NOT TRANSCRIBE THE DIGITS BELOW. Authoring measured `3246 passed, 2 skipped, 3 warnings in 53.35s` at HEAD `9ebe260f` with 207 deselected. Sibling `iyilwm` recorded `3087` and then `3158` at two HEADs days apart, so this number moves by tens of tests a day. Run a bare `python3 -m pytest` on a clean tree FIRST, record it, and state every delta against YOUR number. THE TREE WAS FULLY GREEN at authoring, so the bar is zero failures and any failure is this plan's to explain.

1. TARGETED: `python3 -m pytest tests/test_check_recovery_fidelity.py -o addopts=""` passes, with every added test in the selected set and the count stated.
2. FULL BARE SUITE: `python3 -m pytest` passes with ZERO failures and a count increased over YOUR re-derived baseline by exactly the number of tests E-03 adds. Authoring measured the E-01 change staged in memory leaving the suite at the SAME count with zero failures (F-08), so a failure here is a defect in the executor's implementation, not an inherent consequence.
3. MUTATION PROOF, the load-bearing evidence: with E-01 in place, restore ONLY the overwrite (IN MEMORY, never by editing the file) so `recovery=fix or ""` is passed again, and show the E-03 test RED. A test that does not go red under this mutation has not closed F-01.
4. SCOPE PROOF FOR THE 40 ENGINE CALLERS, WHICH MUST BE A DIFF INSPECTION AND NOT A TEST RUN. Show, by pasting `git diff --name-only`, that `agent_workflows/check_engine.py` is NOT modified. DO NOT substitute a green run of the four tests the authored F-10 named: re-measured at review, the over-broad inversion leaves the ENTIRE suite green at `3246 passed` and all four of those tests PASS under it (`4 passed in 0.30s`), so their passing proves NOTHING about scope. That correction is the single most important one this review made, because the authored plan treated a test run as the fence. You may still run them as a cheap sanity check; you may NOT cite them as the scope proof. The 40-caller contract is real (F-13) and simply unguarded by the suite.
5. END-TO-END SURFACE PROOF: run `aw check all --json` before and after, and paste, for ONE finding whose rule populates a recovery, the `data.policy_findings[*].recovery` value changing from the `inspect ... frontmatter and schema conformity.` prose to the rule's own string. ALSO paste the human `Fix:` line and the `--agent` `next` field for that same finding before and after, confirming both are UNCHANGED (F-05). The second half is not padding: it is the only evidence that the fix did not disturb the human surface.
6. `aw ipd lint --phase pre-transition` conforms, and `aw check` reports no NEW drift. RE-DERIVE the pre-existing finding set rather than trusting a count: authoring saw 17 on this tree. The bar is that the SET you observe afterwards introduces nothing this plan caused.

METHOD RULE FOR THE MUTATION PROOF. Stage it IN MEMORY, not by editing a tracked file: patch or wrap from a scratch script or a pytest plugin in a gitignored `tmp/` directory, or use `mock.patch`. `agent_workflows/cli.py` is a shared-checkout file declared by several other pending plans, and a `git checkout` restore after a minute-long suite run silently discards whatever a co-worker wrote in the interval. Paste `git status --short` empty before and after each proof. Every measurement in this plan was taken that way, and every RE-measurement at review was too.

A WORKING RECIPE, SINCE THE AUTHORED ONE IS PARTLY WRONG. Gate the patch on the CALLING FRAME, which was re-verified at review: wrap `check_engine.enrich_drift` and pop the `recovery` kwarg only when `inspect.currentframe().f_back.f_code.co_name == "_run_check"`; loaded as a pytest plugin from a gitignored `tmp/` directory this leaves the suite at `3246 passed, 2 skipped` (F-08 confirmed). NOTE TWO CORRECTIONS to the authored note. FIRST, patching `enrich_drift` globally does NOT "show 4 unrelated failures": measured at review it shows ZERO, the suite stays green (F-10 corrected), so a green run cannot be used to distinguish the scoped patch from the global one. SECOND, a plain module-attribute monkeypatch reaches every caller including the engine's own internal ones, because they call the bare module-global name; if you need to stage a SOURCE-level change instead, note that a pytest `-p` plugin loads AFTER `agent_workflows` is imported, so the hook must be installed from a `sitecustomize.py` on `PYTHONPATH` to take effect (that is how the review staged it), and verify the stage took hold BEHAVIORALLY rather than with `inspect.getsource`, which reads the file and will show the unpatched text.

LEAK RULE FOR EVERY PASTED SURFACE PROOF. Some engine recovery strings interpolate the ABSOLUTE repo root: measured on this tree, `check.system-layout-missing` yields `run 'aw install <repo-root>' ...` and `check.ipd-lint-diagnostic` yields `aw ipd lint <repo-root>/.aw/records/plans/pending/<...>.ipd.md --phase author`. Since this fix PUBLISHES those strings verbatim, validation item 5 will surface them. Redact any absolute checkout path to `<repo-root>` BEFORE pasting into an `Observed evidence` block, prefer a finding whose recovery interpolates no path (`check.ipd-uncarried-obligation` and `check.lifecycle-transition-invalid` are both path-free on this tree), and run `aw sanitize --agent` before the final commit. The evidence block is committed, so a leak there is permanent.

## Spec / documentation sync

N/A with reason, and the reason is measured rather than assumed. F-11 searched `.aw/records/specs/` for anything governing the machine finding shape: the `approved` spec `25kzda` carries "Exact recovery command" columns, but they specify the `check.ipd-dependency-*` rule catalog's own recovery TEXT, not where `finding_dict` sources the field; the `draft` spec `pqsx96` mentions a "rename recovery command" only as an example inside its `I-09` row; and nothing in the tree references `finding_dict`, `policy_findings` or `POLICY_SCHEMA_VERSION`. The field's contract is documented in CODE (`artifact_core.Drift`'s docstring: "the exact recovery command, when one exists", and `check_engine.finding_dict`'s: "the exact recovery command"), and this plan makes the shipped behavior MATCH that docstring rather than changing it, so there is nothing to amend and `- Scope-Paths:` declares no `.spec.md` file. No user-facing documentation change either: no flag, command, or output KEY changes, only the value of an existing key becomes truthful. `POLICY_SCHEMA_VERSION` is deliberately NOT bumped, because the schema is unchanged; a field that was being populated from the wrong source starts being populated from the documented one, which is a defect fix and not a schema revision.

## Open questions

### OQ-01: Should the fixed call pass nothing, or explicitly pass `recovery=d.recovery`?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, no human input required: PASS NOTHING. The backlog item offers both forms and they are behaviorally IDENTICAL today, because `enrich_drift` resolves `recovery=recovery or drift.recovery`, so `recovery=d.recovery` is a no-op restating the helper's own default (F-06, re-verified at review). THE RESOLUTION STANDS BUT ITS FIRST GROUND IS WITHDRAWN (PR-302). The authored IDIOM argument claimed "8 of the 48 call sites already pass no recovery, including `work_cmd.py`, `plans_index.py` and `prompts_index.py`"; measured at review there are **7** such sites, and they are `check_engine.py` (six) plus `work_cmd.py` (one). `plans_index` and `prompts_index` both pass `recovery=` explicitly (`recovery="aw index plans"` / `recovery="aw index prompts"`), so two of the three cited precedents are COUNTER-examples and the idiom claim does not support the choice (F-14). THE SURVIVING AND SUFFICIENT GROUND IS DRIFT RESISTANCE: an explicit `recovery=d.recovery` duplicates the helper's precedence rule at the call site, so if that rule ever changes the caller silently disagrees with it, whereas the bare call always inherits whatever the helper defines. That argument is independent of how many callers do which, and it is strengthened by F-10's correction, since no test guards the helper's precedence, so a caller that restates it would be an unguarded second copy of an unguarded rule. REVERSIBLE: yes, trivially, and the two forms can be swapped with no behavior change while the current precedence holds.

### OQ-02: Should this plan also stop `next_actions` carrying human prose, since the item raises it in the same breath?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: RESOLVED: NO, and the item itself says so ("Then decide SEPARATELY whether `next_actions` should carry a recovery string at all"). Three measured reasons. FIRST, IT IS A DIFFERENT DATA PATH: `next_actions` is built from `seen_fixes`, which collects the human `fix`, so it is not reached by the recovery fix at all and would need its own edit (F-12). SECOND, IT IS A PUBLIC OUTPUT SURFACE with no obviously correct target shape: the item's own count (8 of 22 recovery literals carry `<placeholder>` segments) shows that swapping prose for recovery strings would put non-runnable text in a slot named `command`, trading one dishonesty for another, so the honest fix is to normalize the 22 literals FIRST - a `check_engine.py` change outside this scope. THIRD, SEQUENCING: fixing the machine record is a strict improvement that is independently testable and provably safe (F-08, F-09), whereas the `next_actions` contract needs a decision about whether a `command` field may hold prose. Bundling them would make a 1-line provable fix unreviewable. Carried by `2cnvh1` in Deferred. REVERSIBLE: yes; nothing here forecloses any option for that slot.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: (a) PASTE the `git diff -- agent_workflows/cli.py` hunk in full and confirm BY INSPECTION that the ONLY behavioral change is the removal of the `recovery=` kwarg from the `ce.enrich_drift(d, ...)` call, that the local `fix` variable is UNCHANGED and still feeds both `Diagnostic(fix=fix or None)` and `seen_fixes.add(fix)`, and that no other statement in the `for d in drift:` loop moved. A diff that also alters `fix`, the `Diagnostic`, or the `next_actions` construction FAILS V-01: F-12 records that slot as deliberately out of scope and OQ-02 refuses it explicitly. (b) CONFIRM the diff does NOT touch `agent_workflows/check_engine.py`, BY PASTING `git diff --name-only`. This is the one failure mode this plan most needs to exclude, and it is NOT test-detected: re-measured at review, inverting the helper's precedence leaves the suite fully green at `3246 passed` and all four tests the authored F-10 named pass under it, so a green suite is NOT evidence you stayed scoped (F-10 corrected, F-13). The only evidence is the file list. (c) PASTE YOUR OWN CLEAN-TREE BARE BASELINE FIRST, then PASTE the FULL BARE `python3 -m pytest` summary after the change and state the delta against YOUR baseline, accounted for per E-item. DO NOT state a delta against a number transcribed from this plan: authoring measured `3246 passed` and the sibling plan's own figure moved by 71 tests between two HEADs (F-08). (d) END-TO-END SURFACE PROOF: run `aw check all --json` BEFORE and AFTER and paste, for one finding whose rule populates a recovery, the `data.policy_findings[*].recovery` value changing from `inspect <path> frontmatter and schema conformity.` to the rule's own string. CHOOSE A PATH-FREE WITNESS and redact any absolute path to `<repo-root>`: `check.ipd-uncarried-obligation` (`hand it off: add `- Carrier: <id6>` ...`) and `check.lifecycle-transition-invalid` (`correct the plan history via ...`) were both path-free on this tree, whereas `check.system-layout-missing` and `check.ipd-lint-diagnostic` interpolate the ABSOLUTE repo root and would plant a permanent leak in this committed record. (e) HUMAN-SURFACE-UNCHANGED PROOF, which is half the point of the scoping: for that SAME finding, paste the human `Fix:` line and the `--agent` `next` field BEFORE and AFTER, and confirm both are byte-identical. F-05 measured all three surfaces unchanged on the fixture; if any of them moves in your tree, STOP and report it, because that is a consequence authoring did not measure.
  - Observed evidence: PASS. Verified diff inspection, check_engine untouched, bare suite green (4195 passed, +3 tests), end-to-end recovery restored to empty on 9uowl6, and human Fix / agent next byte-identical.
    (a) `git diff -- agent_workflows/cli.py` hunk:
    ```diff
    diff --git a/agent_workflows/cli.py b/agent_workflows/cli.py
    index 743b88847..cf5cead65 100644
    --- a/agent_workflows/cli.py
    +++ b/agent_workflows/cli.py
    @@ -12954,8 +12954,14 @@ def _run_check(
                 title, dir_str, fname, extra, fix = _doctor._categorize_drift(d, repo_root)
             except Exception:
                 fix = None
    -        # Prefer any determinism/assurance/severity already stamped on the Drift, else the registry.
    -        enriched = ce.enrich_drift(d, recovery=fix or "")
    +        # Direction of travel: `recovery` is the rule's authored fix and travels to the
    +        # machine record (policy_findings), while `Remediation.detailed_fix` (the local `fix`)
    +        # is human prose travelling to `Diagnostic.fix` and `next_actions`; the two must not be
    +        # crossed. `fix` is computed here because Diagnostic and seen_fixes need it.
    +        # Note this does NOT make `next_actions` fully runnable: next_actions is still built
    +        # from seen_fixes (human prose), carried separately by 2cnvh1.
    +        # Prefer any determinism/assurance/severity already stamped on the Drift, else registry.
    +        enriched = ce.enrich_drift(d)
             sev = enriched.severity or "error"
             # Tally findings by enriched severity (IPD tzjtg4). Unknown or out-of-enum
             # severities fall back to "errors" to remain conservative, matching
    ```
    Inspection confirms the only behavioral change in `cli.py` is dropping `recovery=fix or ""` from `ce.enrich_drift(d)`. `fix` is untouched and continues to feed `Diagnostic(fix=fix or None)` and `seen_fixes.add(fix)`.

    (b) `git diff --name-only`:
    ```
    agent_workflows/cli.py
    ```
    `agent_workflows/check_engine.py` is not modified.

    (c) Bare suite baseline:
    ```
    FAILED tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs
    1 failed, 4191 passed, 2 skipped, 3 warnings in 249.08s (0:04:09)
    ```
    (Note: the 1 timeout failure on `test_box_renderer_invariants_across_swept_inputs` passed in isolation at `1 passed in 15.23s`; filed as backlog defect `mu4k1g`).
    Full bare suite after change:
    ```
    4195 passed, 2 skipped, 3 warnings in 222.09s (0:03:42)
    ```
    Delta: +3 passed (added by E-03 `tests/test_check_recovery_fidelity.py`), 0 failures.

    (d) End-to-end surface proof:
    Finding for `check.name-nonconformant` at location `.aw/records/backlog/graduated/20260928-9uowl6-01-9uowl6-allow-options-anywhere-among-positional-arguments-.backlog.md`:
    BEFORE E-01 `data.policy_findings[*].recovery`:
    `"the slug in .aw/records/backlog/graduated/20260928-9uowl6-01-9uowl6-allow-options-anywhere-among-positional-arguments-.backlog.md is nonconformant; choosing a corrected slug is a human decision (cannot be derived mechanically). Run 'aw rename backlog 9uowl6 --slug <corrected-slug> --apply' or rename to match 'YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md'."`
    AFTER E-01 `data.policy_findings[*].recovery`:
    `""`
    (Rule-authored empty recovery preserved verbatim; human prose is no longer fabricated into the machine finding).

    (e) Human surface unchanged proof:
    For that same finding:
    Human `Fix:` line BEFORE and AFTER:
    `Fix: the slug in .aw/records/backlog/graduated/20260928-9uowl6-01-9uowl6-allow-options-anywhere-among-positional-arguments-.backlog.md is nonconformant; choosing a corrected slug is a human decision (cannot be derived mechanically). Run 'aw rename backlog 9uowl6 --slug <corrected-slug> --apply' or rename to match 'YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md'.`
    (byte-identical).
    `--agent` `next` field BEFORE and AFTER:
    `'aw check all'`
    (byte-identical).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: (a) PASTE the added or edited comment verbatim and confirm it names all THREE required points: that `recovery` is the RULE's authored fix travelling to the MACHINE record while the local `fix` is HUMAN prose travelling to `Diagnostic.fix` and `next_actions`, and that the two must not be crossed; that `fix` is still computed here BECAUSE those two consumers need it (so a later reader does not delete it); and that `next_actions` still carries human prose, with `2cnvh1` named as the carrier. A comment missing the `next_actions` pointer does NOT discharge this: without it a reader concludes the surface is now fully honest, which F-12 measures to be false. (b) CONFIRM the comment is AT the changed call and not at the top of the function, by pasting the surrounding lines, and confirm the stale claim is gone - the shipped comment mentions only `determinism/assurance/severity` and is silent on the fourth field, and that silence is what let the overwrite survive since `a08a4f50` (F-01). (c) PASTE the bare full-suite summary, which must be UNCHANGED from V-01(c), since a comment cannot change a test count.
  - Observed evidence: PASS. Verified added comment names rule recovery vs human fix direction of travel, why fix is still computed, and 2cnvh1 next_actions prose carrier; full suite passes unchanged.
    (a) Added comment verbatim:
    ```python
        # Direction of travel: `recovery` is the rule's authored fix and travels to the
        # machine record (policy_findings), while `Remediation.detailed_fix` (the local `fix`)
        # is human prose travelling to `Diagnostic.fix` and `next_actions`; the two must not be
        # crossed. `fix` is computed here because Diagnostic and seen_fixes need it.
        # Note this does NOT make `next_actions` fully runnable: next_actions is still built
        # from seen_fixes (human prose), carried separately by 2cnvh1.
        # Prefer any determinism/assurance/severity already stamped on the Drift, else registry.
    ```
    Confirms all three points:
    1. Names `recovery` (rule-authored fix -> machine record policy_findings) vs `fix` (human prose -> Diagnostic.fix and next_actions), forbidding crossing them.
    2. Explains `fix` is still computed here because `Diagnostic` and `seen_fixes` need it.
    3. Identifies that `next_actions` still carries human prose and names carrier `2cnvh1`.

    (b) Context lines confirming location directly above `enriched = ce.enrich_drift(d)`:
    ```python
        try:
            title, dir_str, fname, extra, fix = _doctor._categorize_drift(d, repo_root)
        except Exception:
            fix = None
        # Direction of travel: `recovery` is the rule's authored fix and travels to the
        # machine record (policy_findings), while `Remediation.detailed_fix` (the local `fix`)
        # is human prose travelling to `Diagnostic.fix` and `next_actions`; the two must not be
        # crossed. `fix` is computed here because Diagnostic and seen_fixes need it.
        # Note this does NOT make `next_actions` fully runnable: next_actions is still built
        # from seen_fixes (human prose), carried separately by 2cnvh1.
        # Prefer any determinism/assurance/severity already stamped on the Drift, else registry.
        enriched = ce.enrich_drift(d)
        sev = enriched.severity or "error"
    ```
    The stale comment silence on the 4th field is removed and replaced by the accurate description.

    (c) Full bare suite summary unchanged:
    ```
    4195 passed, 2 skipped, 3 warnings in 222.09s (0:03:42)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: (a) PASTE the new test file's source in full and PASTE it passing (`python3 -m pytest tests/test_check_recovery_fidelity.py -o addopts=""`). (b) CONFIRM IT DRIVES THE REAL CLI, by quoting the `cli._run_check` call and the `contextlib.redirect_stdout` capture; a test that calls `check_engine.enrich_drift` directly passes on the SHIPPED code and proves nothing, because the helper is not the defect (F-04). (c) CONFIRM BOTH SIDES ARE DERIVED AT RUN TIME, by quoting the line that computes the expected engine value (a call to `check_engine.check_release_gates`) and the line that computes the human value (a call to `doctor.build_remediation`), and confirm NEITHER string is transcribed as a literal. A hard-coded sentence is a time bomb: sibling `iyilwm` is about to change the human string, which would break a transcribed assertion for an unrelated reason (F-07). (d) CONFIRM ALL FOUR ASSERTIONS ARE PRESENT by quoting each: the populated case equal to the engine value, the inequality against the human prose, the EMPTY case publishing an empty recovery rather than a fabricated string, and the human-surface-unchanged guard. CONFIRM THE EMPTY CASE USES ITS OWN WITNESS (PR-303): the `release-gates` fixture reaches no rule with an empty engine recovery, so an empty-case assertion written against it is unsatisfiable; quote the second fixture (a non-conformant backlog filename driven through `type="backlog"`, yielding `check.name-nonconformant`, whose engine recovery is `''`) and show it is one of the FABRICATED partition F-02 measures. The empty case is the half the backlog item singles out and the populated assertion does not cover it; the human-surface guard is what stops a future change from "fixing" this by emptying `Diagnostic.fix`. (e) MUTATION PROOF, the load-bearing evidence: restore ONLY the overwrite IN MEMORY (patch or wrap; do NOT edit the file), PASTE the RED run naming this test and the failing assertion, PASTE `git status --short` empty to show no tracked file was mutated, then PASTE the GREEN re-run unpatched. A test that does not go red under this mutation has not closed F-01 and V-03 must be marked failed. (f) PROVE SCOPE BY FILE LIST, NOT BY TEST RUN: paste `git diff --name-only` showing `agent_workflows/check_engine.py` absent. DO NOT cite the four tests the authored F-10 named as a scope proof: re-measured at review, all four PASS under the over-broad inversion and the whole suite stays green at `3246 passed`, so their passing distinguishes nothing (F-10 corrected). Running them is a harmless sanity check and is not the evidence this item requires.
  - Observed evidence: PASS. Verified test_check_recovery_fidelity.py passing (3 passed), drives real CLI, run-time derivations, all 4 assertions, in-memory mutation proof red on empty case, and check_engine untouched.
    (a) Source of `tests/test_check_recovery_fidelity.py`:
    ```python
    """Tests for plan wef7yo: check CLI recovery fidelity.

    Pins the property that `aw check --json` machine findings preserve the rule-authored
    `Drift.recovery` verbatim, without being overwritten or fabricated by human remediation
    prose from `doctor.build_remediation`.

    Covers:
    - Populated engine recovery case (witness 1: check.live-bug-ungated)
    - Empty engine recovery case (witness 2: check.name-nonconformant)
    - Human/agent surface guard (agent record 'next' field preserves human remediation prose)
    """

    from __future__ import annotations

    import argparse
    import contextlib
    import io
    import json
    from pathlib import Path
    from tempfile import TemporaryDirectory
    import unittest

    from agent_workflows import check_engine as ce
    from agent_workflows import cli
    from agent_workflows import doctor as _doctor
    from agent_workflows.term import Term
    from tests.test_check_engine_release_gate import _create_minimal_repo


    class TestCheckRecoveryFidelity(unittest.TestCase):
        """Hermetic tests ensuring machine finding recovery fidelity via cli._run_check."""

        def test_machine_finding_recovery_fidelity_populated_case(self) -> None:
            """A rule with populated recovery publishes the engine's recovery verbatim."""
            with TemporaryDirectory() as tmp:
                repo = _create_minimal_repo(Path(tmp))
                bug_file = (
                    repo
                    / ".aw"
                    / "records"
                    / "backlog"
                    / "open"
                    / "20260920-bug001-01-bug001-test-defect.backlog.md"
                )
                bug_file.write_text(
                    "- Id: bug001\n"
                    "- Status: open\n"
                    "- Set: bug001\n"
                    "- Priority: medium\n"
                    "- Work-Kind: bug\n"
                    "- Summary: Live ungated bug\n",
                    encoding="utf-8",
                )

                # Derive engine drift at run time (never hard-code literals)
                engine_drifts = ce.check_release_gates(repo)
                self.assertEqual(len(engine_drifts), 1)
                expected_drift = engine_drifts[0]
                self.assertEqual(expected_drift.rule, "check.live-bug-ungated")
                self.assertTrue(expected_drift.recovery)

                # Drive real CLI through _run_check with json=True
                args = argparse.Namespace(
                    command="check",
                    type="release-gates",
                    dir=str(repo),
                    all=False,
                    agent=False,
                    json=True,
                    selector=[],
                    strict_setid_length=False,
                )
                term = Term(color=False)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = cli._run_check(args, term)

                self.assertEqual(rc, 1)
                output = json.loads(buf.getvalue())
                findings = output["data"]["policy_findings"]
                self.assertEqual(len(findings), 1)

                published_finding = findings[0]
                self.assertEqual(published_finding["rule"], "check.live-bug-ungated")

                # (a) published recovery equals the engine Drift.recovery verbatim
                self.assertEqual(published_finding["recovery"], expected_drift.recovery)

        def test_machine_finding_recovery_fidelity_empty_case(self) -> None:
            """A rule with empty recovery publishes empty string, not fabricated human prose."""
            with TemporaryDirectory() as tmp:
                repo = _create_minimal_repo(Path(tmp))
                bad_file = (
                    repo
                    / ".aw"
                    / "records"
                    / "backlog"
                    / "open"
                    / "badly-named-file.backlog.md"
                )
                bad_file.write_text(
                    "- Id: bad001\n"
                    "- Status: open\n"
                    "- Set: bad001\n"
                    "- Priority: medium\n"
                    "- Work-Kind: bug\n"
                    "- Summary: Bad file name\n",
                    encoding="utf-8",
                )

                # Derive engine drift and doctor human fix at run time
                engine_drifts = ce.check_types(repo, ["backlog"])
                drift_by_rule = {d.rule: d for d in engine_drifts}
                self.assertIn("check.name-nonconformant", drift_by_rule)
                expected_drift = drift_by_rule["check.name-nonconformant"]

                # Confirm engine recovery is empty for this rule
                self.assertEqual(expected_drift.recovery, "")

                # Compute human prose from doctor
                human_rem = _doctor.build_remediation(expected_drift, repo)
                self.assertTrue(human_rem.detailed_fix)

                # Drive real CLI through _run_check with json=True
                args = argparse.Namespace(
                    command="check",
                    type="backlog",
                    dir=str(repo),
                    all=False,
                    agent=False,
                    json=True,
                    selector=[],
                    strict_setid_length=False,
                )
                term = Term(color=False)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = cli._run_check(args, term)

                self.assertEqual(rc, 1)
                output = json.loads(buf.getvalue())
                findings = output["data"]["policy_findings"]
                finding_by_rule = {f["rule"]: f for f in findings}
                self.assertIn("check.name-nonconformant", finding_by_rule)

                published_finding = finding_by_rule["check.name-nonconformant"]

                # (c) published recovery equals engine Drift.recovery and is falsy (not fabricated)
                self.assertEqual(published_finding["recovery"], expected_drift.recovery)
                self.assertFalse(published_finding["recovery"])

                # (b) published recovery does NOT equal human remediation prose
                self.assertNotEqual(published_finding["recovery"], human_rem.detailed_fix)

        def test_human_and_agent_surface_fidelity_guard(self) -> None:
            """The human surface (--agent next field) still reflects human remediation prose."""
            with TemporaryDirectory() as tmp:
                repo = _create_minimal_repo(Path(tmp))
                bug_file = (
                    repo
                    / ".aw"
                    / "records"
                    / "backlog"
                    / "open"
                    / "20260920-bug001-01-bug001-test-defect.backlog.md"
                )
                bug_file.write_text(
                    "- Id: bug001\n"
                    "- Status: open\n"
                    "- Set: bug001\n"
                    "- Priority: medium\n"
                    "- Work-Kind: bug\n"
                    "- Summary: Live ungated bug\n",
                    encoding="utf-8",
                )

                engine_drifts = ce.check_release_gates(repo)
                self.assertEqual(len(engine_drifts), 1)
                expected_drift = engine_drifts[0]
                human_rem = _doctor.build_remediation(expected_drift, repo)

                # Drive real CLI through _run_check with agent=True
                args = argparse.Namespace(
                    command="check",
                    type="release-gates",
                    dir=str(repo),
                    all=False,
                    agent=True,
                    json=False,
                    selector=[],
                    strict_setid_length=False,
                )
                term = Term(color=False)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = cli._run_check(args, term)

                self.assertEqual(rc, 1)

                # Parse agent record
                agent_record = None
                for line in buf.getvalue().splitlines():
                    try:
                        parsed = json.loads(line)
                        if parsed.get("cmd") == "check":
                            agent_record = parsed
                            break
                    except Exception:
                        pass

                self.assertIsNotNone(agent_record)
                # (d) agent record 'next' still matches human prose string
                self.assertEqual(agent_record["next"], human_rem.detailed_fix)


    if __name__ == "__main__":
        unittest.main()
    ```
    Passing test execution:
    ```
    python3 -m pytest tests/test_check_recovery_fidelity.py -o addopts=""
    ============================= test session starts ==============================
    rootdir: <repo-root>
    collected 3 items

    tests/test_check_recovery_fidelity.py ...                                [100%]

    ============================== 3 passed in 0.98s ===============================
    ```

    (b) Real CLI driven:
    Lines 65-66, 137-138, 187-188:
    `with contextlib.redirect_stdout(buf):`
    `    rc = cli._run_check(args, term)`

    (c) Derived at run time (no literals):
    Lines 49: `engine_drifts = ce.check_release_gates(repo)`
    Lines 108: `engine_drifts = ce.check_types(repo, ["backlog"])`
    Lines 117, 172: `human_rem = _doctor.build_remediation(expected_drift, repo)`

    (d) All four assertions present and quoted:
    Populated case equal: line 75: `self.assertEqual(published_finding["recovery"], expected_drift.recovery)`
    Empty case equal & falsy: lines 145-146:
    `self.assertEqual(published_finding["recovery"], expected_drift.recovery)`
    `self.assertFalse(published_finding["recovery"])`
    Inequality against human prose: line 149: `self.assertNotEqual(published_finding["recovery"], human_rem.detailed_fix)`
    Human surface guard: line 203: `self.assertEqual(agent_record["next"], human_rem.detailed_fix)`
    Second witness quoted: lines 89-106 (seeds `badly-named-file.backlog.md`, yields `check.name-nonconformant` with engine recovery `''`).

    (e) Mutation proof in memory:
    Restored `recovery=fix or ""` in memory via temporary pytest hook in gitignored `tmp/`:
    `git status --short` before:
    ` M agent_workflows/cli.py`
    `?? tests/test_check_recovery_fidelity.py`
    RED run:
    ```
    FAILED tests/test_check_recovery_fidelity.py::TestCheckRecoveryFidelity::test_machine_finding_recovery_fidelity_empty_case
    AssertionError: "the slug in .aw/records/backlog/open/bad[246 chars]md'." != ''
    - the slug in .aw/records/backlog/open/badly-named-file.backlog.md is nonconformant; choosing a corrected slug is a human decision (cannot be derived mechanically). Run 'aw rename backlog bad001 --slug <corrected-slug> --apply' or rename to match 'YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md'.
    ========================= 1 failed, 2 passed in 0.79s ==========================
    ```
    `git status --short` after scratch cleanup: identical.
    Unpatched GREEN run:
    ```
    ============================== 3 passed in 0.98s ===============================
    ```

    (f) Scope proof:
    `git diff --name-only`:
    ```
    agent_workflows/cli.py
    ```
    `agent_workflows/check_engine.py` is absent.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and has NOT been reviewed or approved. It must not be executed until a `/plan-review` has run and a human has approved it. The executor must not self-approve, and must not write a `- Readiness:` field, which is an output of the review and not of authoring.

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. The removal of ONE keyword argument at ONE call site in `agent_workflows/cli.py`: `ce.enrich_drift(d, recovery=fix or "")` becomes `ce.enrich_drift(d)`, so `aw check`'s machine-readable finding carries the recovery its RULE authored instead of the prose the HUMAN renderer computed. Plus one corrected comment and one new test file. No rule changes, no new rule, no signature change, no schema change, nothing in `check_engine.py` or `doctor.py`. The user-visible effect is confined to `data.policy_findings[*].recovery` in `--json`/`--agent` output: measured on this repository's live findings, the large majority stop being overwritten and the rest stop being fabricated (F-02; 15 and 2 at authoring, 30 and 2 re-measured at review one day later, so the counts drift while the property does not). NOTHING A HUMAN READS CHANGES - the `Fix:` line, the `Next` line and the agent `next` field were measured byte-identical before and after on both surfaces (F-05), and `next_actions` is untouched by construction (F-12). The change was staged in memory and the full bare suite measured at `3246 passed, 2 skipped`, identical to baseline (F-08), so it is verified safe against the shipped suite before approval rather than after. TWO THINGS A HUMAN IS ALSO APPROVING BY OMISSION: `next_actions[*].command` will still carry non-runnable prose (OQ-02 refuses to fix it here, and the backlog item itself parks it), and a published recovery may now contain `<placeholder>` segments or an absolute repo root, because 8 of 22 recovery literals carry placeholders and two interpolate the root - that is the rule's own authored guidance rather than invented prose, which is the improvement, but it is not yet a runnable command. The remaining risk is concentrated in one place, named in F-10: if the executor "generalizes" the fix into `check_engine.enrich_drift`, four shipped tests go red. V-01(b) and V-03(f) both check for exactly that.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). Exactly two files plus this plan: `agent_workflows/cli.py` (E-01, E-02) and the new `tests/test_check_recovery_fidelity.py` (E-03). FOUR NEGATIVE CONSTRAINTS CARRY REAL WEIGHT. FIRST, `agent_workflows/check_engine.py` MUST NOT BE COMMITTED: changing `enrich_drift`'s precedence is the tempting general fix and F-10 measures it turning 4 shipped tests red, because 40 of 48 callers legitimately pass a rule-authored recovery that must win. SECOND, `agent_workflows/doctor.py` MUST NOT BE COMMITTED: the generic `inspect ... frontmatter` string is sibling `iyilwm`'s deliverable (and `x19law`'s for the sentinel case), both `to-review`/`reviewed` with their own gates, and both reserve `cli.py` for this plan; editing it here duplicates a reviewed plan and guarantees a conflict in the one statement they touch. THIRD, do NOT change the local `fix` variable, the `Diagnostic` construction, or the `seen_fixes`/`next_actions` block: OQ-02 refuses the `next_actions` question explicitly and V-01(a) fails a diff that touches it. FOURTH, do NOT edit `tests/test_check_engine_release_gate.py`; E-03 IMPORTS `_create_minimal_repo` from it and must not modify it, which is why it is absent from `- Scope-Paths:`. An out-of-scope edit that turns out to be necessary is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, and a declared path you end up not modifying needs a `--scope-ack`; neither is a reason to stop.

EXECUTION CONTRACT. Commit only the two files in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never with `--no-verify`. Do not push. `agent_workflows/cli.py` IS A HIGH-TRAFFIC SHARED FILE declared by several other pending plans, so the execution contract's "verify what you are actually about to commit" step is not optional: a co-worker's unstaged edit to `cli.py` must not be swept into this commit. THE MUTATION PROOF IS STAGED IN MEMORY, NOT BY EDITING A FILE, for the same reason - a `git checkout` restore after a minute-long suite run silently discards a co-worker's concurrent edit. Run `aw sanitize --agent` before the final commit, because this fix publishes recovery strings that can interpolate an absolute repo root (see the leak rule above).

LIFECYCLE TRANSITION. The terminal transition is owed unconditionally but its OWNER is conditional: under `aw oc run` / `aw agy run` the runner performs finalize and the executor must NOT also run it; executed by hand, the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-roll a `git mv` to `executed/`.

THE WAYS THIS PLAN CAN FAIL SILENTLY, stated for the executor. THREE shapes, all measured, and the third was added at review because the authored plan assumed a test would catch it.

FIRST, a test that would also pass if the fix were absent. A test that calls `check_engine.enrich_drift` or `finding_dict` DIRECTLY never exercises the defective caller and passes on shipped code (F-04: the helper is correct; the caller is not). SECOND, a test that transcribes either string as a literal will pass or fail for reasons unrelated to this defect, and will break outright when `iyilwm` changes the human string (F-07). For both, a green suite is NOT sufficient evidence; V-03(e)'s RED mutation run is, and it must be performed and pasted rather than reasoned about.

THIRD, AND THE ONE THE AUTHORED PLAN GOT WRONG: "generalizing" E-01 into `check_engine.enrich_drift`'s precedence. The authored F-10 claimed the suite would catch that by turning four tests red. RE-MEASURED AT REVIEW, IT DOES NOT: the inversion leaves the suite fully green at `3246 passed, 2 skipped` and all four named tests pass under it. So this failure mode is INVISIBLE to every test in the repository, and the only thing standing between it and `main` is a human or agent reading `git diff --name-only` and seeing `check_engine.py` where it does not belong. V-01(b) and V-03(f) now demand that file list explicitly and forbid citing a test run in its place. Treat a green suite after touching the helper as MEANINGLESS rather than as reassurance.

POST-GATE LIFECYCLE. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms AND all three `V-*` items carry pasted evidence with `Result: verified`, including the V-03(e) mutation proof and the V-01(d)/(e) surface proofs. On completion the runner sets backlog `2cnvh1` to `graduated`; this plan inherits its `- Blocks-Release: next` gate, so that gate is preserved rather than dropped.
