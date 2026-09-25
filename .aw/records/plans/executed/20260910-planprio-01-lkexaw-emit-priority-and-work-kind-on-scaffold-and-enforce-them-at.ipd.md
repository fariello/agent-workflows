# IPD: Emit Priority and Work-Kind on scaffold and enforce them at the ready-to-execute gate

- Date: 2026-09-10
- Kind: child
- Concern: A plan's `Priority` and `Work-Kind` are recognized but never emitted and never required, so almost no plan carries either and the attention board's Priority column is empty for almost every plan. The scaffold omitting both is the root cause; nothing enforcing them is why nobody notices. RE-MEASURED AT REVIEW (2026-09-13, HEAD `bf5bbe5a`), because the authored figures are stale and one was FALSE: 120 pending plans (authored 104), of which 11 ALREADY carry both fields, so "adoption is zero" is now wrong although the thesis survives (109 of 120 carry neither). 197 backlog items, all 197 carrying both (authored "180", the right shape, the wrong number). 470 `executed` + 34 `superseded` + 4 `not-executed` = 508 terminal. `aw att --type plan --format json` reports 628 items with 13 carrying a non-null `priority`. Do NOT re-quote any of these; the corpus moves daily and each E-item that needs a population re-derives its own.
- Scope: Emit both fields in the scaffold skeleton, enforce them at the ready-to-execute lint gate with a reserved sentinel for the pre-cutoff corpus, admit that sentinel in the two SHIPPED enum rules that currently reject it, register the `aw check` rule, regenerate the two IPD templates the scaffold change breaks, update the four `-`-clearing test callers E-07 breaks, and amend the governing IPD spec whose field enumeration currently omits both. Does NOT change the shared vocabulary, does NOT add a sort key, and does NOT touch specs, research or backlog items.
- Scope-Paths: agent_workflows/ipd_authoring.py, agent_workflows/ipd_schema.py, agent_workflows/ipd_lint.py, agent_workflows/check_engine.py, agent_workflows/cli.py, tests/test_plan_priority_required.py, tests/test_work_kind.py, tests/test_ipd_priority.py, .aw/system/workflows/assess/templates/ipd.md, .aw/system/workflows/assess/templates/orchestrator-ipd.md, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md, agent_workflows/backlog.py, agent_workflows/status_set.py, agent_workflows/runner_shared.py, tests/support.py, tests/test_status_set.py, tests/test_ipd_authoring.py, tests/test_ipd_lifecycle_cli.py, tests/test_ipd_lint.py, tests/test_orchestrator_retirement.py, tests/test_oc_runipd.py, tests/test_check_engine.py, tests/test_defect_report.py
- Item-Dependencies: executed:8u6770, executed:lc4unl
- Status: executed
- Work-Kind: feature
- Priority: medium
- Readiness: go-pending-approval
- Set: planprio
- Order: 1
- Highest E allocated: 12
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: lkexaw

## Workflow history
- 2026-09-25 executed (opencode/its_direct/pt3-claude-opus-5-1m-us): executed: E-01..E-12 performed, V-01..V-12 pass; merged c70e51ac; suite 1853 passed, 1 skipped [Scope reconciliation - in-scope-unmodified .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified .aw/system/workflows/assess/templates/ipd.md: changed in 9e3ed86e, merged before begin (receipt base c70e51ac); in-scope-unmodified .aw/system/workflows/assess/templates/orchestrator-ipd.md: changed in 9e3ed86e, merged before begin (receipt base c70e51ac); in-scope-unmodified agent_workflows/backlog.py: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified agent_workflows/check_engine.py: changed in 9e3ed86e, merged before begin (receipt base c70e51ac); in-scope-unmodified agent_workflows/cli.py: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified agent_workflows/ipd_authoring.py: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified agent_workflows/ipd_lint.py: changed in 9e3ed86e, merged before begin (receipt base c70e51ac); in-scope-unmodified agent_workflows/ipd_schema.py: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified agent_workflows/runner_shared.py: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified agent_workflows/status_set.py: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified tests/support.py: changed in 156e8414, merged before begin (receipt base c70e51ac); in-scope-unmodified tests/test_check_engine.py: changed in 156e8414, merged before begin (receipt base c70e51ac); in-scope-unmodified tests/test_defect_report.py: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified tests/test_ipd_authoring.py: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified tests/test_ipd_lifecycle_cli.py: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified tests/test_ipd_lint.py: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified tests/test_ipd_priority.py: changed in 9e3ed86e..c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified tests/test_oc_runipd.py: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified tests/test_orchestrator_retirement.py: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified tests/test_plan_priority_required.py: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified tests/test_status_set.py: changed in c70e51ac, merged before begin (receipt base c70e51ac); in-scope-unmodified tests/test_work_kind.py: changed in 9e3ed86e..c70e51ac, merged before begin (receipt base c70e51ac)]
- 2026-09-25 note (opencode/its_direct/pt3-claude-opus-5-1m-us): amended in place under the maintainer's 2026-09-24 ruling on 5h1lxs ('fix in place on the lane'): E-10..E-12 added, Scope-Paths widened, spec amended; approval unchanged. E-01..E-12 performed and V-01..V-12 verified on lane aw/lane/lkexaw_attempt4.
- 2026-09-24 approved (aw set): backfill: Priority/Work-Kind per planprio-03 lc4unl maintainer decision on OQ-05 (planprio: medium/feature)
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-13 reviewed (aw set): set Item-Dependencies to executed:8u6770, executed:lc4unl
- 2026-09-13 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review complete: REVIEWED - OPEN QUESTIONS; PR-001 BLOCKER open and escalated to blocking OQ-02 (the parent reversed this Set's order and this plan's Item-Dependencies still records the old one); PR-002..PR-013 FIXED. Readiness no-go.

- 2026-09-13 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 (BLOCKER, OPEN and escalated to blocking OQ-02), PR-002..PR-013 FIXED; readiness `no-go` because one blocking question remains. Record: `.aw/records/reviews/20260910-planprio-01-lkexaw-emit-priority-and-work-kind-on-scaffold-and-enforce-them-at.review.md`. `aw ipd lint --phase author --agent` CONFORMING (`outcome:clean, findings:0`) before semantic review. Suite measured bare at HEAD `bf5bbe5a`: `5971 passed, 3 skipped, 2 xfailed in 60.94s`. DISCLOSURE: the same agent and model family authored this Set, so treat this as a near-self-review worth less than an independent one; its value therefore rests on what was EXECUTED rather than re-read.
  SEVEN THINGS WERE MEASURED RATHER THAN REASONED, and each produced a finding. (1) E-01 was APPLIED to `ipd_authoring.build_skeleton` and the suite run: it FAILS `tests/test_ipd_templates.py` twice, because both IPD templates are asserted BYTE-EQUAL to the generator's output, and neither template nor that test file was in `Scope-Paths`. (2) E-07 was APPLIED to `cli.py` (removing `-` from `--priority`/`--work-kind` on `ipd set` only) and the suite run: it FAILS FOUR tests across `tests/test_work_kind.py` and `tests/test_ipd_priority.py`, neither declared. (3) The `grandfathered` sentinel was DRIVEN through `check_plan_priority`/`check_plan_work_kind`: BOTH flag it `error`, and so do `unresolved` and `TODO`, so the plan's chosen sentinel is rejected by two SHIPPED rules it does not declare a fix for. (4) `authoring_placeholders_resolved` was driven on a fully-authored plan carrying the sentinels: it returns True, so the sentinel does NOT participate in the placeholder predicate the plan cites as its precedent. (5) The FORBIDDEN change (both fields into `META_REQUIRED`) was applied and counted: 109 of 120 pending plans and 470 of 470 `executed` plans fail, confirming the plan's closing hazard note with numbers. (6) `set_priority_line`/`set_work_kind_line` were driven against a scaffold: they anchor after `- Status:`, NOT after `- Order:` where E-01 says to emit, so the setter MOVES the field E-01 positions. (7) The corpus was recounted: 120 pending / 11 already compliant / 197 backlog items all compliant / 508 terminal.
  THE PLAN'S DIAGNOSIS IS CORRECT AND ITS DESIGN IS RIGHT, which is why every finding is a correction rather than a rejection. The scaffold really never emits either field, nothing really enforces them, the `Scope-Paths` gate really is the right pattern to mirror, and the refusal to add either field to `META_REQUIRED` is not merely prudent but measurably load-bearing. What the plan got wrong is UNDER-DECLARED SCOPE: as authored it breaks six tests in three files that it does not list, and it picks a sentinel two shipped rules reject. The one BLOCKER is inherited: this plan is Order 01 in a Set whose maintainer ruling of 2026-09-12 REVERSED the order (02 and 03 run FIRST), and this plan still carries `- Item-Dependencies: none` while the parent's own resolution says Order 01 must now depend on both siblings. Escalated as blocking OQ-02.
- 2026-09-10 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from the maintainer's correction of 2026-09-10 that optionality was meant for LEGACY plans only, not going forward. This child owns the mechanism; siblings 02 and 03 own the backfill. THE PATTERN IS NOT NEW AND MUST BE REUSED RATHER THAN INVENTED: `Scope-Paths` already does exactly this, and its own review chose it explicitly (`3a195178`, 2026-08-23) "to avoid breaking every pending plan and the grandfather guarantee". MEASURED AT AUTHORING: `META_PRIORITY` and `META_WORK_KIND` are both in `META_RECOGNIZED` and neither is in `META_REQUIRED` (which holds exactly `Author`, `Concern`, `Date`, `Id`, `Kind`, `Scope`, `Status`); `ipd_authoring.py:170-185` emits `Item-Dependencies`, `Status`, `Set`, `Order`, `Highest E allocated`, `Author` and `Id` and NEITHER of these two; and the governing spec's field enumeration (`20260802-1904-01-ipd-structure-and-linting.spec.md:148-152`, `- Status: implemented`) lists required, optional and recognized-but-optional fields and never mentions `Priority` or `Work-Kind` at all, so the spec is SILENT rather than contradictory, which is a different amendment shape from `wfjsp4`'s.

## Goal

Make both fields required for a plan that is about to run, emitted for every new plan, and exempt for the terminal corpus, so the field stops being decorative without mass-failing 470 finished plans.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: close the root cause

- [x] E-01 EMIT BOTH FIELDS IN THE SCAFFOLD SKELETON, in `ipd_authoring.py` where the metadata block is built (`:170-185`). This is the root cause of zero adoption and the cheapest half of the fix: a field the creating command never writes is a field nobody remembers.
  CHOOSE THE EMITTED VALUE DELIBERATELY AND STATE WHY. Do NOT emit a fabricated real value: the `xprio` orchestrator's OQ-01 already ruled that an ABSENT priority renders as unprioritized and that no value may be fabricated, and emitting `medium` by default would fabricate one at creation instead of at render. Emit the fields with a value the author must replace, following the `Item-Dependencies: unresolved` precedent in the same function (`:179`), whose own comment explains the reasoning: a reserved sentinel makes "a freshly scaffolded plan an HONEST not-ready draft". Mirror that: a scaffolded plan is honestly untriaged, and the gate in E-03 is what forces triage before it can run.
  POSITION THE FIELDS WHERE THE SHIPPED WRITERS ALREADY PUT THEM, WHICH IS NOT AFTER `Order` (review F-6). The authored instruction said "after `Order`", and that is measurably wrong: `releases.set_priority_line` (`releases.py:434-449`) and `set_work_kind_line` (`:455-474`) both insert after `- Status:`, falling back to after `- Id:`. MEASURED at review: scaffolding with the fields after `- Order:` and then running one `aw ipd set --priority high --work-kind bug` MOVES both lines up to just after `- Status:`, so the scaffold's position survives exactly until the first setter call. Emit them immediately after `- Status:` so the scaffold and the setter agree, and state that reason. Do NOT instead change the two writers' anchors: they are shared with `aw specs set` and the spec-side field is genuinely optional, so re-anchoring them is a wider change than this plan declares.
  - Depends on: none
  - Expected outcome: `aw ipd scaffold` writes both fields with a replace-me sentinel positioned after `- Status:`; a freshly scaffolded plan still passes `aw ipd lint --phase author` (measured at review: it does, at either position); one `aw ipd set --priority <v> --work-kind <v>` leaves the position UNCHANGED (the property that failed at the authored position); the chosen sentinel and field position are recorded with their rationale.
  - Execution state: performed

- [x] E-08 REGENERATE BOTH IPD TEMPLATES, WHICH E-01 BREAKS, and understand why before editing them. `tests/test_ipd_templates.py` asserts each template is BYTE-EQUAL to `build_skeleton`'s output (`:33-47` child, `:49-61` orchestrator), which is the mechanism that stops a template drifting from the generator. MEASURED AT REVIEW by applying E-01 and running the suite: `test_child_template_matches_generator` and `test_orchestrator_template_matches_generator` both FAIL, and nothing else in 5971 tests does. Neither template nor that test file was in the authored `Scope-Paths`, so E-01 as authored lands a two-test regression.
  REGENERATE, DO NOT HAND-EDIT, and do not touch the test. The test's own failure message says "regenerate it". The correct fix is to re-emit each template from the generator (the two placeholder arguments the test pins are child title `<short title of the change>` / orchestrator title `<short title of the coordinated change>`, author `<agent/model>`, date `<YYYY-MM-DD>`, set `<set-id>`, id6 `tmp1d6`), so the parity property is PRESERVED rather than weakened. If you find yourself editing `tests/test_ipd_templates.py`, stop: that would delete the guard instead of satisfying it, which is why that file is deliberately NOT in `Scope-Paths`.
  - Depends on: E-01
  - Expected outcome: both templates carry the two new fields, `python3 -m pytest tests/test_ipd_templates.py` passes with all 10 tests, and `tests/test_ipd_templates.py` is unmodified (proven by `git diff --stat`).
  - Execution state: performed

- [x] E-02 ADD THE `grandfathered` SENTINEL FOR BOTH FIELDS in `ipd_schema.py`, mirroring `SCOPE_PATHS_GRANDFATHERED` (`:157`) rather than inventing a second spelling. The sentinel is stored IN the plan's metadata so it travels with the plan, which is the property that makes the exemption auditable rather than a date computation.
  DO NOT ADD EITHER FIELD TO `META_REQUIRED`. That is the specific mistake the `Scope-Paths` review avoided and its comment warns against in place (`ipd_schema.py:149-152`): adding it there "would fail every existing pending plan at the always-on `author` metadata check and defeat the grandfather guarantee". Requirement is CONDITIONAL and belongs in the checkpoint layer only. MEASURED AT REVIEW by actually making the forbidden change and counting: 109 of 120 pending plans AND 470 of 470 `executed` plans go to `disposition: error`. So the hazard is quantified, not merely asserted.
  - Depends on: E-01
  - Expected outcome: a reserved sentinel recognized for both fields, both still absent from `META_REQUIRED`, and a validator that accepts either the sentinel or a value in the shared `low|medium|high` / `bug|feature|chore|security|followup` vocabularies.
  - Execution state: performed

- [x] E-09 ADMIT THE SENTINEL IN THE TWO SHIPPED ENUM RULES, WHICH CURRENTLY REJECT IT, in `check_engine.py`. THIS IS THE FINDING MOST LIKELY TO BE MISSED, because it fails on a DIFFERENT surface from the one E-03 exercises. `check_plan_priority` (`check_engine.py:2646-2693`) and `check_plan_work_kind` (`:2700-2755`) accept ONLY `backlog.PRIORITIES` / `backlog.KINDS` and treat ABSENT as fine. MEASURED AT REVIEW by driving both functions against a scratch plan: `grandfathered` is flagged `check.priority-invalid` AND `check.work-kind-invalid`, each `severity=error`; so are `unresolved` and `TODO`. So every sentinel this plan might choose is rejected by two rules that already ship, and the exemption the plan is built around would make `aw check plans` report two new errors per exempt plan.
  THE ASYMMETRY IS THE WHOLE POINT: those two rules treat an ABSENT field as silent and a NON-VOCABULARY value as an error, which is exactly inverted from what this Set needs (absent must become an error at the gate, and one specific non-vocabulary value must become acceptable). Both halves must land together or the Set produces a corpus that passes one surface and fails the other. Note this is the parent's Completion criterion 4 (`d0cbt3`), which says so explicitly.
  ADMIT ONLY THE SENTINEL, NOT ANY OUT-OF-VOCAB VALUE. `TODO`, `unknown`, `medium-high` and every other spelling must stay an error; widening the accepted set generally would delete the enum check. Derive the admitted token from the ONE constant E-02 defines, never a second literal, and prove it with a grep.
  - Depends on: E-02
  - Expected outcome: a plan carrying the sentinel in either field produces NO `check.priority-invalid` / `check.work-kind-invalid` finding, while `TODO` and any other out-of-vocab value still produces one; the admitted token is read from E-02's constant (proven by grep, not asserted).
  - Execution state: performed

### Task group 2: enforce it where it bites, and only there

- [x] E-03 ENFORCE BOTH FIELDS AT THE READY-TO-EXECUTE GATE in `ipd_lint.py`, mirroring the `Scope-Paths` gate exactly (`check_scope_paths`, `ipd_lint.py:916-957`) including its disposition guard. Reuse `_scope_paths_gate_applies`'s shape (`:904-913`), or factor a shared helper from it; do not copy the predicate.
  THE GATE FIRES ON THE STATUS AS WELL AS THE PHASE, AND THAT IS THE SET'S SHARPEST EDGE. `_scope_paths_gate_applies` returns `checkpoint == "pre-execution" or status in S.READY_TO_EXECUTE`, so mirroring it means the new refusal applies at EVERY phase, including `author`, to any plan whose persisted `- Status:` is `approved` or `auto-approved`. MEASURED AT REVIEW: 25 pending plans are at that tier and 18 of them carry neither field, so this E-item makes 18 plans unrunnable the instant it lands unless the backfills precede it. That is what OQ-02 and the parent's Ruling 1 are about; do not treat the status half of the predicate as incidental.
  THE GRANDFATHER BOUNDARY IS THE DISPOSITION, NOT THE DATE, which is why the existing gate returns early on status. VERIFIED AT REVIEW rather than assumed: `lint_text` short-circuits a terminal-dir file to `DISPOSITION_LEGACY` before any checkpoint check (`ipd_lint.py:1052-1053`, `_is_terminal_dir` at `:1028`), and an `executed/` plan carrying neither field was driven at all five phases: `legacy/not evaluated` with 0 diagnostics at `author`, `review-finalize`, `pre-execution` and `pre-transition`. THE ONE PHASE THAT IS NOT EXEMPT IS `post-transition`, which deliberately bypasses the short-circuit (`checkpoint != "post-transition"` in the same condition), so a plan is evaluated there. Baseline measured: 114 of 470 `executed` plans ALREADY report errors at `post-transition`, and E-06 must show that number does not grow.
  A SENTINEL VALUE IS ADVISORY-SATISFIED, NOT SILENT: the `Scope-Paths` gate emits an advisory saying a re-reviewed or new plan should declare a real value (`:946-953`). Mirror that, so a grandfathered plan is visibly exempt rather than invisibly compliant.
  - Depends on: E-02
  - Expected outcome: a plan at the ready-to-execute gate without either field is REFUSED with a message naming the fix; a plan carrying the sentinel passes with an advisory; a terminal plan is untouched at all four non-`post-transition` phases, and the `post-transition` error count over `executed/` is unchanged from the 114 baseline.
  - Execution state: performed

- [x] E-04 REGISTER THE `aw check` RULE so the sweep and the checkpoint cannot drift apart, with a rule id in `RULE_REGISTRY`. This is the same single-predicate discipline `rnkqrc` E-04 states and that `subject_gating_blocks` already relies on: two surfaces reading one predicate, never two copies.
  STAGE THE SEVERITY, and treat that as a rollout mechanism rather than a softening: `warning` while the pending corpus still carries sentinels, `error` once it does not. Note the end state is `error`; nothing may leave the rule permanently at `warning`, which is the same obligation recorded on `rnkqrc` E-05.
  ALSO CHECK THE INVARIANT-CATALOG FIT BEFORE PICKING AN INVARIANT ID, AND THE ANSWER IS ALREADY DETERMINED: use the EMPTY invariant `""`, as both sibling rules do. Read at review, the catalog (`20260828-pqsx96-01-...spec.md:129-144`) holds I-01 through I-16 and NONE is about artifact triage metadata; the nearest, I-12, is specifically the draft-to-`to-review` authoring nudge. Both `check.priority-invalid` and `check.work-kind-invalid` are registered with `""` (`check_engine.py:247-259`), and `check.review-finding-unescalated`'s comment states the convention in place: an uncatalogued rule takes `""` and says why, because "claiming a neighbouring id would be a false trace". The `check.setid-collision` misfiling under I-09 is the counterexample this instruction exists to prevent; do not add a catalog entry either, since that is a spec amendment this plan does not declare.
  A `warning` DOES DRIVE A NONZERO EXIT, so do not read "advisory" into it. VERIFIED at review: `artifact_core.drift_exit_code` (`:405-415`) exempts ONLY `info`, so `warning` fails the gate exactly as `error` does; the sibling `lintreach` plan (`k9awrq`) records the same trap from its own review. If the intent is "reported but not gating", the severity is `info`, not `warning`. State which of the two you mean and why; the staged rollout is legitimate either way, but the word must match the mechanism.
  MEASURE THE `aw check plans` BASELINE FIRST AND DO NOT REQUIRE A CLEAN RUN. Measured bare at review: it exits 1 with `findings 140`, none attributable to this Set (124 `check.scope-drift` on two plans holding live begin receipts, 15 `check.lifecycle-transition-invalid`, 1 `check.review-decision-unescalated`). An executor told to make that clean would either stall or edit other agents' plans in a shared checkout, which the shared-checkout rule forbids. Compare against your own baseline and name any NEW rule id.
  - Depends on: E-03
  - Expected outcome: a registered rule reported by `aw check plans`, reading the SAME predicate as the lint gate (proven by grep, not asserted), with `invariant=""` and a recorded reason, at the chosen severity with its exit-code behavior measured unpiped and the end state `error` documented.
  - Execution state: performed

### Task group 3: make the contract say so

- [x] E-05 AMEND THE GOVERNING IPD SPEC, which is SILENT rather than wrong, and that distinction shapes the edit. `.aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md` is `- Status: implemented` and its field enumeration (`:148-152`) lists required fields (`Date`, `Kind`, `Concern`, `Scope`, `Status`, `Author`), one optional field, and `Scope-Paths` as recognized-but-optional with a CONDITIONAL requirement at the ready-to-execute gate. It never mentions `Priority` or `Work-Kind`. Add them alongside `Scope-Paths` as recognized fields whose requirement is conditional at that same gate, and state the grandfather sentinel.
  AMEND SECTION 9.2 TOO, NOT ONLY 4.4. The plan named only the field enumeration, but the checkpoint contract is a SECOND place the same rule is stated: the Section 9.2 table's `pre-execution` row spells out the `Scope-Paths` requirement in full, including that "This same `Scope-Paths` requirement also applies to any plan whose persisted `Status` is at the ready-to-execute tier" (`:449`). E-03 mirrors that predicate exactly, so leaving 9.2 silent would leave the shipped gate's status-tier behavior undocumented in the one table a reader consults for checkpoint rules. Add the two fields to that row in the same edit.
  DO NOT CLAIM `aw specs check` VALIDATES THE AMENDMENT'S CONTENT. Measured at review: `aw specs check` on this spec exits 0 BEFORE any edit, and `aw specs check` over all specs exits 0 too. It validates the status enum, required sections and gate typing, not whether a field enumeration is complete, so it can only show the edit did not BREAK the spec. Cite it for that and no more; the content evidence is the diff.
  THE PATH IS DECLARED IN `Scope-Paths` DELIBERATELY, so the runners announce the spec edit before the run and the finalize gate reconciles it. Do not widen the amendment beyond these two fields.
  - Depends on: E-04
  - Expected outcome: Section 4.4's enumeration AND Section 9.2's `pre-execution` row both name the two fields with their conditional requirement and sentinel; `aw specs check` still exits 0 (a no-break check, not a content check).
  - Execution state: performed

- [x] E-06 TEST THE GATE, THE SENTINEL, THE TERMINAL EXEMPTION AND THE SCAFFOLD in a new `tests/test_plan_priority_required.py`, with a falsification pass: every new assertion must be shown to FAIL against the pre-change code, since a test that passes before and after proves nothing. Falsify by REVERTING the change in the executing worktree, not by citing a historical HEAD.
  COVER THE CASE THAT WOULD MASS-FAIL THE CORPUS, because that is the failure this design exists to avoid: a plan in `executed/` with neither field must produce NO finding at the four non-`post-transition` phases. State `post-transition` honestly as the documented exception (E-03) rather than over-claiming "no finding at any phase", which review measured to be false.
  FOUR FURTHER CASES ARE REQUIRED, each corresponding to a defect review found by measurement, so each is a regression test for a real hole rather than a hypothetical:
  1. THE ENUM-RULE ADMISSION (E-09): a plan carrying the sentinel produces NO `check.priority-invalid` / `check.work-kind-invalid` finding, while `TODO` in either field still produces one. Without this, the exemption passes the lint gate and fails the sweep.
  2. THE SETTER-POSITION INVARIANT (E-01): scaffold, then run one `aw ipd set --priority <v> --work-kind <v>`, and assert the two lines are still adjacent and in the scaffold's chosen position. This is the property the authored "after `Order`" position failed.
  3. THE SCAFFOLD-IS-NOT-COMPLETE PROPERTY (F-11): `ipd_authoring.authoring_placeholders_resolved` must return False for a freshly scaffolded plan that still carries the new sentinel, which requires adding the sentinel line to `_AUTHORING_PLACEHOLDERS` (`ipd_authoring.py:105-119`, whose comment already requires lock-step with the scaffold). MEASURED at review WITHOUT that addition: a fully-authored plan still carrying the sentinels returns True, so `check.ipd-draft-ready-to-review` would nudge an untriaged plan toward `to-review`, which is the precedent's own reasoning inverted.
  4. THE TEMPLATE PARITY (E-08): `tests/test_ipd_templates.py` passes unmodified.
  - Depends on: E-05
  - Expected outcome: tests covering refusal, sentinel-advisory, terminal exemption at four phases, scaffold emission, enum-rule admission, setter-position stability and the placeholder property, each shown failing against pre-change code by reverting in the worktree.
  - Execution state: performed

- [x] E-07 REMOVE OR NARROW THE `-` CLEARING CHOICE ON `aw ipd set`, which this Set's own gate turns into a defect. `--priority` and `--work-kind` currently accept `-` meaning "clear this field" (documented in their help as "'-' clears it"). Once E-03 makes both fields required at the ready-to-execute gate, clearing either on a non-terminal plan produces a plan the gate REFUSES, so the flag becomes a way to manufacture a plan that cannot run.
  THE MAINTAINER AUTHORIZED THIS ON 2026-09-10 while answering `b5sfwm` OQ-02: they ruled NO `-` on either sibling verb and called the plan-side one "a defect to fix". That question was about `aw backlog set`, which will now ship WITHOUT `-`; this item is the plan-side half, so the two verbs end up symmetric rather than divergent.
  CHOOSE BETWEEN REMOVAL AND NARROWING AND SAY WHY. Removing the choice outright is simplest and matches the sibling. Narrowing it to a plan that is already grandfathered (or terminal) preserves a genuine use, editing an exempt plan's metadata, at the cost of a conditional flag. Either is acceptable; a silent third option, leaving it as-is, is not.
  THE FOUR BROKEN CALLERS ARE ALREADY IDENTIFIED, MEASURED, NOT PREDICTED. The authored instruction said to grep for callers; review did it by APPLYING the change (removing `-` from `--priority` and `--work-kind` on `ipd set` only) and running the suite. FOUR tests fail, in TWO files now declared in `Scope-Paths`:
  1. `tests/test_ipd_priority.py::PrioritySetterTests::test_set_writes_persists_on_noop_and_clears` (`:154-169`) drives `--priority -` through the real CLI and asserts the line is gone.
  2. `tests/test_work_kind.py::PlanSetterTests::test_set_writes_persists_on_noop_and_clears` (`:362-377`), the same shape for `--work-kind -`.
  3. `tests/test_work_kind.py::PlanSetterTests::test_writing_work_kind_does_not_disturb_the_structural_kind` (`:425-443`), which additionally asserts the structural `- Kind:` survives a Work-Kind clear; PRESERVE that assertion by clearing through another route rather than deleting the test, since it guards a genuine regression (`- Kind:` vs `- Work-Kind:` confusion).
  4. `tests/test_work_kind.py::SharedVocabularyTests::test_the_cli_choices_match_the_shared_vocab` (`:212-235`), which pins the argparse choices to `set(backlog.KINDS) | {"-"}` for BOTH `("ipd","set")` AND `("specs","set")` IN ONE ASSERTION. This is the load-bearing one: the two verbs share one assertion, so making them differ requires splitting it into two expectations. Do NOT resolve that by removing `-` from `aw specs set` as well: `Work-Kind` stays genuinely OPTIONAL on a spec, that verb is outside this plan's Scope and outside the maintainer's 2026-09-10 ruling, and the parent (`d0cbt3`) records the resulting asymmetry as a deliberate, reasoned cost.
  THE UNDERLYING WRITERS KEEP `-`, AND THAT IS CORRECT. `releases.set_priority_line` / `set_work_kind_line` treat `-`/None as "remove the line" and are shared with `aw specs set`; this item removes or narrows the PLAN VERB'S ARGPARSE CHOICE ONLY. `tests/test_work_kind.py:510` exercises the writer's `-` directly and must keep passing untouched.
  - Depends on: E-03
  - Expected outcome: `aw ipd set --priority -` either refuses with a message naming the gate, or is accepted only for a grandfathered/terminal plan; the choice and its reason are recorded; all four named tests updated to match the new contract with their guarding intent preserved; `aw specs set` unchanged; the full suite green.
  - Execution state: performed

- [x] E-10 DECIDE PRIORITY AND WORK-KIND WHERE THE WORK IS FIRST RECORDED (maintainer ruling 2026-09-24, answering `5h1lxs`: "The refusal SHOULD NEVER HAPPEN. Priority and Work-Kind MUST be enforced WELL BEFORE getting approved. It should set at the backlog if one exists and at the first drafting otherwise."). (a) `aw backlog new` (`backlog.run_new`) REFUSES without `--priority` and `--work-kind` (alias `--kind`), dropping the silent `medium`/`chore` defaults, and the two runner prompts in `runner_shared.py` that instruct agents to file with `aw backlog new` name both flags. (b) `aw ipd scaffold` gains `--priority`, `--work-kind` and `--from-backlog <id6>`: `--from-backlog` records `From-Backlog` and inherits both values plus `Blocks-Release` from the item (via a new `backlog.find_item`), an explicit flag overrides the inherited value, and scaffold REFUSES when the values come from neither. `build_skeleton` keeps `unresolved` as its no-argument default so the byte-pinned templates are unchanged.
  - Expected outcome: both verbs refuse without the values and write nothing; `--from-backlog` inherits Priority, Work-Kind and Blocks-Release; each refusal has a test that fails when the refusal is reverted.
  - Execution state: performed

- [x] E-11 KEEP AN APPROVAL-TIME BACKSTOP in `status_set.validate_transition_allowed`: a plan moved to a ready-to-execute status with a missing or undecided Priority/Work-Kind is REFUSED before any write, counting a value passed in the same call, judged by the same `ipd_schema.parse_plan_priority`/`parse_plan_work_kind` the lint gate uses (`grandfathered` passes). This replaces the old silent outcome: an approved plan the pre-execution gate later refused in an unattended run.
  - Expected outcome: `aw ipd set approved` refuses an undecided plan with the file unchanged, accepts one carrying decided values or passing them in the same call; a test fails when the check is reverted.
  - Execution state: performed

- [x] E-12 REFUSE THE SCAFFOLD'S `Scope-Paths` PLACEHOLDER at the ready-to-execute gate. Found while verifying this plan: `parse_scope_paths` accepted `TODO (comma-separated repo-relative paths or pathspecs)` as one relative path, so a plan approved with the placeholder in place linted clean. A value whose first token is `TODO` is now a grammar error; spec Section 4.5 is amended to say so. Zero live plans carry the placeholder (measured with grep before the change).
  - Expected outcome: the placeholder is blocking at pre-execution on an approved plan; a real path list still parses; a new row in `ScopePathsCheckpointTests` covers it.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- A field is made conditionally mandatory in the CHECKPOINT layer, never by adding it to `META_REQUIRED`, because the always-on `author` metadata check would then fail the entire existing corpus. Stated in place at `ipd_schema.py:149-152`.
- The grandfather exemption is a reserved SENTINEL VALUE stored in the plan's own metadata "so it travels with the plan" (`ipd_schema.py:154-157`), not a cutoff date computed elsewhere.
- The scaffold's precedent for an untriaged field is a reserved sentinel that is neither blank nor a real value (`Item-Dependencies: unresolved`, `ipd_authoring.py:171-179`), justified there as making a fresh plan "an HONEST not-ready draft".
- An absent `Priority` renders as unprioritized and a value must NOT be fabricated (`xprio` orchestrator `u5vyye` OQ-01).
- A TEMPLATE IS BYTE-EQUAL TO ITS GENERATOR AND IS REGENERATED, NOT HAND-EDITED. `tests/test_ipd_templates.py:33-61` asserts both IPD templates equal `build_skeleton`'s output exactly, and the assertion message is "regenerate it". So any scaffold change is a THREE-file change (generator + two templates), and the pattern extends to any future metadata field.
- AN UNCATALOGUED CHECK RULE TAKES THE EMPTY INVARIANT `""` AND SAYS WHY. Stated in place at `check_engine.py:160-170` ("claiming a neighbouring id would be a false trace"), with both `Priority`/`Work-Kind` enum rules already registered that way (`:247-259`). The `check.setid-collision` misfiling under I-09 is the recorded counterexample.
- A `warning` SEVERITY IS NOT ADVISORY: `artifact_core.drift_exit_code:405-415` exempts only `info`, so `warning` drives a nonzero exit exactly as `error` does.
- THE SCAFFOLD-PLACEHOLDER TUPLE IS KEPT IN LOCK-STEP WITH THE SCAFFOLD BY HAND, and its own comment says so (`ipd_authoring.py:100-104`: "if a scaffold placeholder string changes, update it here"). A new sentinel that is not added there is invisible to the draft-readiness predicate.

## Findings

| Id | Severity | Finding |
|---|---|---|
| F-1 | HIGH | The scaffold never emits either field. `ipd_authoring.py:158-185` writes `Item-Dependencies`, `Status`, `Set`, `Order`, `Highest E allocated`, `Author` and `Id`, and neither `Priority` nor `Work-Kind`. This is the root cause of near-zero adoption. FIGURES CORRECTED AT REVIEW: 11 of 120 pending plans now carry both (not "0 of 104"), and 197 of 197 backlog items carry both (not "180"). The thesis survives; the numbers did not. |
| F-2 | HIGH | Nothing enforces either field at any checkpoint, so even a plan that carries them gains nothing and a plan that omits them is never told. Both are in `META_RECOGNIZED` (`ipd_schema.py:241-258`) and neither is in `META_REQUIRED` (`:129-137`). |
| F-3 | MEDIUM | The governing IPD spec is SILENT on both fields, not contradictory: its enumeration at `:146-150` covers required, optional and recognized-but-optional fields and never mentions them. So the amendment ADDS a row rather than correcting a false one, which is a smaller and safer edit than the `kw5y2s` case in the `specdirs` Set. Confirmed at review by grepping every `.spec.md`: the only `Priority`/`Work-Kind` occurrences are two specs' own front matter, so no spec anywhere asserts the optionality this Set changes. |
| F-4 | MEDIUM | "Recognized-but-optional" was inherited by analogy, not decided for these fields. The phrase originated for `Scope-Paths` (`3a195178`) with the stated reason of protecting the existing corpus. Nothing records a decision that these two should be permanently optional, and the only question ever put to the maintainer in the `xprio` Set was about RENDERING an absent value. |
| F-5 | LOW | The board already renders a Priority column for plans, so the benefit is immediate once values exist; no rendering work is needed in this Set. Note the column is COLOR-RENDERER ONLY: a piped `aw att --type plan` has no Priority column (`attention.py:2084-2101`), so evidence must come from `FORCE_COLOR=1` or `--format json` (measured: 628 items, 13 with a non-null `priority`). |
| F-6 | HIGH | **E-01 AS AUTHORED LANDS A TWO-TEST REGRESSION IT DOES NOT DECLARE.** `tests/test_ipd_templates.py:33-61` asserts both IPD templates are BYTE-EQUAL to `build_skeleton`'s output. MEASURED by applying E-01 and running the full suite: `test_child_template_matches_generator` and `test_orchestrator_template_matches_generator` FAIL (`2 failed, 5969 passed`), and neither template nor a regeneration step was in `Scope-Paths`. FIXED: new E-08 regenerates both templates, and both template paths are now declared. |
| F-7 | HIGH | **THE CHOSEN SENTINEL IS REJECTED BY TWO SHIPPED RULES.** `check_plan_priority` (`check_engine.py:2646-2693`) and `check_plan_work_kind` (`:2700-2755`) accept only the shared vocabularies and flag anything else `error`. MEASURED by driving both against a scratch plan: `grandfathered` yields `check.priority-invalid` AND `check.work-kind-invalid`; so do `unresolved` and `TODO`. So the exemption the plan is built around would add two errors per exempt plan on the sweep surface. This is the parent's Completion criterion 4. FIXED: new E-09 admits the sentinel in both rules, derived from E-02's single constant. |
| F-8 | HIGH | **E-07 AS AUTHORED BREAKS FOUR TESTS IN TWO UNDECLARED FILES.** MEASURED by applying it: `tests/test_ipd_priority.py::PrioritySetterTests::test_set_writes_persists_on_noop_and_clears`, and three in `tests/test_work_kind.py` (`test_set_writes_persists_on_noop_and_clears`, `test_writing_work_kind_does_not_disturb_the_structural_kind`, `test_the_cli_choices_match_the_shared_vocab`). The last pins the choices for `("ipd","set")` AND `("specs","set")` in ONE assertion, so the two verbs cannot diverge without splitting it. FIXED: both files declared, all four named with their guarding intent, and `aw specs set` explicitly out of scope. |
| F-9 | MEDIUM | **E-01's PRESCRIBED FIELD POSITION DOES NOT SURVIVE THE FIRST SETTER CALL.** The plan says to emit "after `Order`", but `releases.set_priority_line:434-449` and `set_work_kind_line:455-474` both anchor after `- Status:`. MEASURED: scaffolding at the authored position and running one `aw ipd set --priority high --work-kind bug` moves both lines. FIXED: E-01 now emits after `- Status:` to match the shipped writers, with re-anchoring the shared writers explicitly rejected. |
| F-10 | MEDIUM | **THE TERMINAL EXEMPTION IS NOT TOTAL, AND V-03 DEMANDED PROOF OF A FALSE CLAIM.** `lint_text:1052` short-circuits terminal dirs to `legacy` EXCEPT at `post-transition`. MEASURED: an `executed/` plan with neither field is `legacy` (0 diagnostics) at `author`/`review-finalize`/`pre-execution`/`pre-transition`, and IS evaluated at `post-transition`, where 114 of 470 `executed` plans already error. FIXED: E-03, E-06 and V-03 now state the four exempt phases and require the `post-transition` baseline be shown unchanged instead of claiming "no finding at any phase". |
| F-11 | MEDIUM | **THE SENTINEL WOULD BE INVISIBLE TO THE DRAFT-READINESS PREDICATE.** `_AUTHORING_PLACEHOLDERS` (`ipd_authoring.py:105-119`) is hand-maintained in lock-step with the scaffold, and its comment says so. MEASURED: a fully-authored plan carrying the new sentinels returns `authoring_placeholders_resolved == True`, so `check.ipd-draft-ready-to-review` would nudge an UNTRIAGED plan toward `to-review`, inverting the very `Item-Dependencies: unresolved` reasoning E-01 cites as its precedent. FIXED as E-06 case 3. |
| F-12 | LOW | E-04's `warning` severity is described as a softening but is not one: `artifact_core.drift_exit_code:405-415` exempts only `info`, so `warning` fails the gate exactly as `error` does. The sibling `lintreach` plan (`k9awrq`) recorded the identical trap from its own review. FIXED: E-04 now requires stating whether `info` or `warning` is meant and measuring the exit code unpiped. |
| F-13 | LOW | E-04's invariant-id instruction asks the executor to judge catalog fit, but the answer is already determined and citable: no catalog invariant (I-01..I-16, `pqsx96` spec `:129-144`) covers triage metadata, and both sibling enum rules are registered with `invariant=""` by the convention stated at `check_engine.py:160-170`. FIXED: E-04 now names `""` with the citation instead of deferring the judgement. |
| F-14 | LOW | E-05 named only the Section 4.4 field enumeration, but Section 9.2's checkpoint table states the same conditional requirement in full for `Scope-Paths` (`:449`), including the status-tier clause E-03 mirrors. Amending 4.4 alone would leave the shipped gate's status behavior undocumented where readers look for checkpoint rules. Also, `aw specs check` exits 0 on this spec BEFORE any edit (measured), so it cannot evidence the amendment's content. Both FIXED in E-05 and V-05. |

## Proposed changes (ordered, validatable)

1. Scaffold emits both fields with a replace-me sentinel, positioned after `- Status:` to match the shipped writers (E-01).
2. Both IPD templates regenerated so the byte-parity guard keeps passing (E-08).
3. A reserved sentinel recognized for both, neither added to `META_REQUIRED` (E-02).
4. The sentinel admitted in the two shipped enum rules that currently reject it (E-09).
5. Conditional enforcement at the ready-to-execute gate, disposition-guarded (E-03).
6. A registered `aw check` rule reading the same predicate, `invariant=""`, staged severity with its exit code measured (E-04).
7. The governing spec's Section 4.4 enumeration AND Section 9.2 checkpoint row extended (E-05).
8. The `-` clearing choice removed or narrowed on the plan verb only, with its four measured callers updated (E-07).
9. Tests with a falsification pass, including the terminal-exemption case, the enum admission, the setter position and the placeholder property (E-06).

## Deferred / out of scope (with reason)

- BACKFILLING ANY PENDING PLAN. Owned by siblings 02 and 03 deliberately, so the mechanism is reviewable separately from the corpus edit.
- SPECS AND RESEARCH, which `xprio` gave the same optional field. Raised as the parent's OQ-01; out of scope here.
- A PRIORITY-BASED SORT KEY. Explicitly not introduced by `xprio` and not introduced here.
- CHANGING EITHER VOCABULARY. Shared with backlog items by decision recorded in source item `p9o1oo`.

## Scope check

- Over-scope: none. The eleven declared paths are the scaffold writer, the schema, the lint gate, the check registry, the plan verb's parser, one new test file, the two existing test files E-07 necessarily breaks, the two templates E-01 necessarily breaks, and the one spec whose contract must name the fields. FIVE OF THOSE WERE ADDED AT REVIEW because the authored six were measurably insufficient: applying E-01 and E-07 to the tree breaks six tests in three files that were not declared (F-6, F-8), and `aw ipd finalize` would refuse the run for each undeclared edited path.
- Under-scope: this child leaves every existing pending plan non-conformant-but-warned until siblings 02 and 03 run; whether that is intentional sequencing or a defect is now OQ-02, since the parent's maintainer ruling of 2026-09-12 REVERSED the order so 02 and 03 precede this plan. Until that is reflected in this plan's `- Item-Dependencies:`, this section's "intentional sequencing" claim is stale rather than reassuring.

## Required tests / validation

`tests/test_plan_priority_required.py`, plus falsification of every new assertion against pre-change code (revert in the worktree, not a historical HEAD). Establish the suite baseline by running `python3 -m pytest` bare BEFORE the first edit and paste that output.

FOR REFERENCE ONLY, measured bare at review (HEAD `bf5bbe5a`): `5971 passed, 3 skipped, 2 xfailed in 60.94s`, no failure. Do NOT quote that as your baseline; re-measure and judge on the delta, since an unverified count is what produced this Set. Run the suite BARE: the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`, and adding `-n0` or a second `-q` makes the run slower and suppresses the summary line the execution contract requires you to paste.

THREE PRE-EXISTING FIGURES THE EXECUTOR MUST NOT MISTAKE FOR ITS OWN REGRESSIONS, each measured at review: `aw check plans` exits 1 with `findings 140` before this plan touches anything; 114 of 470 `executed` plans already report errors at `--phase post-transition`; and `aw specs check` already exits 0, so it cannot evidence a spec amendment's content.

## Spec / documentation sync

`.aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md` is amended by E-05 (Section 4.4 AND Section 9.2) and is declared in `Scope-Paths`. WHY: that spec's field enumeration is the contract every plan is linted against, and adding a conditionally-required field without naming it there would leave the shipped gate unexplained by the document that defines the metadata block.

THE PARENT'S QUESTION "DOES ANY SPEC DESCRIBE THESE FIELDS AS OPTIONAL?" IS NOW ANSWERED, NOT LEFT TO EXECUTION. The parent (`d0cbt3`) required this child to measure it and warned it must not be assumed absent. MEASURED AT REVIEW by grepping every `.spec.md` for both field names: the ONLY occurrences are two specs' own front-matter values (`7ckptx` and `6kwd2e`, each carrying `- Work-Kind: feature` as metadata about itself). NO spec anywhere asserts that a plan's `Priority` or `Work-Kind` is optional. So this Set amends exactly ONE spec, the amendment ADDS rather than corrects (F-3), and no second `.spec.md` needs declaring.

NO OTHER DOCUMENTATION SURFACE CLAIMS THE OPTIONALITY EITHER, checked at review: the string "recognized-but-optional" appears in the tree only twice, both in this same spec and both about `Scope-Paths`. `AGENTS.md` does not describe either field, so it needs no edit and is deliberately not declared (a declared-but-unmodified path costs a `--scope-ack` at finalize).

## Open questions

### OQ-01: What sentinel should a freshly scaffolded plan carry, and should it differ from the grandfather sentinel?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: RESOLVED AT REVIEW AS **YES, TWO DISTINCT SENTINELS**, and the reasoning is now grounded in measurement rather than analogy. The repository already distinguishes the two states for `Item-Dependencies`: `unresolved` means "not yet triaged" (scaffold) while a real value or an explicit `none` means "decided"; `Scope-Paths` uses `grandfathered` for "predates the rule". Those are different CLAIMS with different gate behavior, so they need different words: a NEW plan carrying `unresolved` must be REFUSED at the gate (it must be triaged), while an OLD plan carrying `grandfathered` PASSES with an advisory (it is exempt). Collapsing them into one token would make an untriaged new plan indistinguishable from a deliberately exempt old one, which is precisely the audit property the sentinel exists to provide.
  TWO CONSEQUENCES THAT WERE NOT VISIBLE AT AUTHORING AND ARE NOW E-ITEMS. First, BOTH tokens must be admitted by the two shipped enum rules, not just one: measured, `grandfathered`, `unresolved` and `TODO` are each flagged `check.priority-invalid` and `check.work-kind-invalid` (F-7, now E-09). Second, `unresolved` must be added to `_AUTHORING_PLACEHOLDERS`, or a scaffolded plan carrying it reads as fully authored and gets nudged toward `to-review` (F-11, now E-06 case 3). Either choice was implementable, as the plan said; what the plan did not know is that both choices required these two extra edits, which is why resolving it here rather than at execution time changed the plan's scope.
  ONE CAVEAT FOR THE EXECUTOR: if the maintainer's answer to OQ-02 keeps the reversed order (02 and 03 first), NO pending plan ever needs `grandfathered` written onto it, because the corpus is real-valued before this gate exists. The token is still required in the SCHEMA and in E-09 for the terminal corpus and for any plan that reappears, but E-01 must not stamp it onto existing plans; that was option (a), which the maintainer declined.

### OQ-02: The parent reversed this Set's order, and this plan's `- Item-Dependencies: none` still records the old order. Confirm the reversal and the edge this plan must carry.

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: THE CONTRADICTION IS ON DISK RIGHT NOW AND IS NOT A JUDGEMENT CALL. The parent (`d0cbt3`) records a maintainer ruling dated 2026-09-12: "RULING 1, ORDERING: RUN ORDERS 02 AND 03 BEFORE ORDER 01", chosen over stamping a sentinel inside this plan and over staging the gate as advisory, and it states plainly that "Order 01's dependency edges must be rewritten to depend on 02 and 03 rather than the reverse". MEASURED at review: this plan still carries `- Item-Dependencies: none`, while siblings `8u6770` and `lc4unl` BOTH still carry `- Item-Dependencies: executed:lkexaw`, which is the ORIGINAL, now-rejected direction. So all three children currently encode the order the maintainer overturned, and the parent's own child table still lists this plan first.
  WHY IT BLOCKS RATHER THAN BEING A CLERICAL FIX, and this is the substance the maintainer already had put to them. The gate E-03 installs mirrors `_scope_paths_gate_applies` (`ipd_lint.py:904-913`), which fires when the checkpoint is `pre-execution` OR the plan's persisted `- Status:` is at the ready-to-execute tier. RE-MEASURED at review: 25 pending plans are `approved`/`auto-approved` and 18 of them carry neither field. So if this plan executes FIRST, those 18 plans fail `aw ipd lint` at EVERY phase and `aw ipd begin` refuses them, and they stay unrunnable until both backfills complete. The runner's dependency machinery cannot save the Set here, because the edges as written point the wrong way: `queue_sort_key` sorts on `dependency_depth` FIRST and re-checks edges at dispatch, so it would faithfully run this plan before the two siblings that declare it as their prerequisite.
  WHAT THE EXECUTOR MUST NOT DO. Do NOT silently rewrite the three `- Item-Dependencies:` lines as part of executing this plan: that is a cross-plan edit to two files this plan does not declare, in a shared checkout, and it would also require editing the parent's child table. Do NOT instead assume the authored order still stands because the front matter says `none`; the parent's resolved ruling is the newer statement. Do NOT relabel this question `Blocking: no` to get past the lint gate, which is the forged-clearance route the lint's own message warns about.
  WHAT AN ANSWER LOOKS LIKE. Either (a) CONFIRM the reversal, in which case one change brings all four files into agreement (this plan gains `- Item-Dependencies: executed:8u6770, executed:lc4unl`, both siblings drop to `none`, and the parent's child table and V-01 evidence are updated), and it should be made by whoever owns the Set rather than mid-execution by this child; or (b) REVERSE THE RULING back to gate-first, which requires accepting that 18 approved plans are unrunnable until the backfills land, and should then say so explicitly so nobody reports it as a regression. The parent's option (a) (stamp the sentinel inside this plan) was already declined and is not revived here, though note E-09 keeps the sentinel available in the schema either way.
  RECOMMENDATION (a), CONFIRM THE REVERSAL, because the maintainer already chose it on measured evidence and nothing found in this review weakens that choice. This review deliberately did NOT make the edit: only this one plan was in the review's scope ledger, three of the four files that must change belong to other plans, and a cross-plan reordering is the Set owner's act.
  CONFIRMED AND APPLIED 2026-09-12: OPTION (a), THE REVERSAL STANDS, and the four files are now in agreement. The maintainer confirmed their RULING 1 and chose to have the correction made as a RECORDS FIX by the Set's owner rather than as an execution step, exactly as this question recommended.
    THE CONTRADICTION THIS QUESTION IDENTIFIED WAS REAL AND WAS MINE. When RULING 1 was recorded on 2026-09-12 the parent's OQ-02 and both siblings' resolutions all SAID the `executed:lkexaw` edges were inverted and must be removed, but NO FILE'S DEPENDENCY DATA WAS ACTUALLY REWRITTEN. So the prose said one order and the machine-readable graph still encoded the other. This review caught precisely that gap, and its refusal to fix it mid-review was correct: four files across three plans is a cross-plan edit no child declares.
    WHAT WAS WRITTEN, through the tooled verb rather than by hand (`aw ipd dependencies set`, which canonicalizes and validates before writing): this plan gained `- Item-Dependencies: executed:8u6770, executed:lc4unl`; `8u6770` and `lc4unl` both dropped to `none`; and the parent's child table's `Depends on` column was inverted to match.
    VERIFIED BY THE RUNNER'S OWN SCHEDULER, not by inspection. `oc_runipd.dependency_depth` over the corrected edges returns `8u6770` 0, `lc4unl` 0, `lkexaw` 1, and `sorted(by depth)` yields `['8u6770','lc4unl','lkexaw']`. So the queue now executes the backfills first and this plan last, which is what RULING 1 requires and what the graph previously prevented.
    THE `Order` NUMBERS ARE DELIBERATELY NOT RENUMBERED, and the parent's table now says so explicitly, because that is the misreading this correction invites. `Order` is the authored numbering and is no longer the execution order; the `Depends on` column is authoritative and the runner sorts by dependency depth. Renumbering would rewrite three filenames and every cross-reference in the Set for a cosmetic gain, and the uniform naming grammar treats `NN` as a stable identifier rather than a promise about sequence.
    ONE OBLIGATION SURVIVES FOR THIS PLAN'S EXECUTOR: E-03 installs the gate, so it MUST NOT run until both backfills are `executed`. That is now enforced by the graph rather than by prose, which is the point of making the edit instead of only recording the ruling. If you find yourself able to execute this plan while either sibling is unexecuted, STOP: the edge has been lost again and the stranding described in the parent's OQ-02 is live.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a freshly scaffolded plan's full metadata block showing both fields with the chosen sentinel and their position, then paste `aw ipd lint --phase author --agent` on it showing `clean`. State the chosen sentinel and why it was chosen over a fabricated default, citing the `xprio` no-fabrication ruling. THEN PASTE THE POSITION-STABILITY PROOF, which is the half review found missing: run one `aw ipd set <status> <that plan> --priority <v> --work-kind <v>` and paste the metadata block AFTER it, showing both lines still in the scaffold's position. Measured at review, the authored "after `Order`" position FAILS this, so a V-01 that omits it would pass a plan with a defect.
  - Observed evidence: Chosen sentinel `unresolved` (the `xprio` no-fabrication ruling: a draft has not decided, so no default is invented); per the 2026-09-24 ruling `aw ipd scaffold` now writes the DECIDED values and `unresolved` survives only as `build_skeleton`'s no-argument default. Scratch repo, scaffold with `--priority high --work-kind bug`, lint at author, then one `aw ipd set draft <id> --priority low --work-kind chore`; both lines stay directly after `- Status:`:
    ## scaffold metadata
    - Date: 2026-09-24
    - Kind: child
    - Concern: TODO.
    - Scope: TODO.
    - Scope-Paths: TODO (comma-separated repo-relative paths or pathspecs)
    - Item-Dependencies: unresolved
    - Status: draft
    - Work-Kind: bug
    - Priority: high
    - Set: ev
    - Order: 1
    - Highest E allocated: 01
    - Author: t
    - Id: slg2wd

    ## lint author
    {"schema":"aw.agent/v1","kind":"result","cmd":"ipd lint","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":1,"evidence":["plans-lint"],"diagnostics":[{"location":".aw/records/plans/pending/20260924-ev-01-slg2wd-ev.ipd.md","rule":"check.ipd-dependency-unresolved"}],"next":null}
    rc=0
    ## after ipd set --priority low --work-kind chore
    - Date: 2026-09-24
    - Kind: child
    - Concern: TODO.
    - Scope: TODO.
    - Scope-Paths: TODO (comma-separated repo-relative paths or pathspecs)
    - Item-Dependencies: unresolved
    - Status: draft
    - Work-Kind: chore
    - Priority: low
    - Set: ev
    - Order: 1
    - Highest E allocated: 01
    - Author: t
    - Id: slg2wd
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the sentinel constant and a grep proving neither field was added to `META_REQUIRED`. Paste the validator accepting the sentinel and REJECTING a value outside the vocabulary, with the rejection message.
  - Observed evidence: Sentinel constants, META_REQUIRED membership (False False), and the validators accepting the sentinel and rejecting out-of-vocab values:
    ## V-02
    229:PLAN_PRIORITY_GRANDFATHERED = "grandfathered"
    230:PLAN_PRIORITY_UNRESOLVED = "unresolved"
    243:PLAN_WORK_KIND_GRANDFATHERED = "grandfathered"
    244:PLAN_WORK_KIND_UNRESOLVED = "unresolved"
    129:META_REQUIRED: Tuple[str, ...] = (
    130-    "Date",
    131-    "Kind",
    132-    "Concern",
    False False
    (None, True, None)
    (None, False, "priority not in ['high', 'low', 'medium']: 'urgent'")
    (None, True, None)
    (None, False, "work kind not in ['bug', 'chore', 'feature', 'followup', 'security']: 'epic'")
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste THREE gate runs with their unpiped exit codes: a pending plan missing both fields (REFUSED, message names the fix), a pending plan carrying the sentinel (passes, advisory emitted), and a plan copied from `executed/` carrying neither. FOR THE THIRD, show the FOUR non-`post-transition` phases producing NO finding, and state plainly that `post-transition` is the documented exception rather than claiming "no finding at any phase" (review measured that claim to be false). ALSO PASTE THE APPROVED-PLAN CASE, which the authored V-03 omitted and which is the Set's sharpest edge: a pending plan whose `- Status:` is `approved`, missing both fields, REFUSED at `--phase author` (not only at `pre-execution`), proving the status half of the predicate fires.
  - Observed evidence: Driven through `ipd_lint.lint_text`. The grandfathered row's disposition is `error` ONLY because of an unrelated `IPD-S404` (status `to-review` is incompatible with `pre-execution`); its M110/M111 findings are advisory, not blocking. The executed-dir rows are `legacy/not evaluated` at the four non-`post-transition` phases; `post-transition` is the documented exception and was not claimed:
    missing both (to-review) phase=pre-execution dir=pending: disposition=error blocking=["IPD-M110 Priority is required at the ready-to-execute gate: declare a priority (low|medium|high), or the sentinel 'grandfathered'", "IPD-M111 Work-Kind is required at the ready-to-execute gate: declare a work kind (bug|feature|chore|security|followup), or the sentinel 'grandfathered'"] advisory=[]
    grandfathered phase=pre-execution dir=pending: disposition=error blocking=[] advisory=['IPD-M110', 'IPD-M111']
    executed-dir, missing both phase=author dir=executed: disposition=legacy/not evaluated blocking=[] advisory=[]
    executed-dir, missing both phase=review-finalize dir=executed: disposition=legacy/not evaluated blocking=[] advisory=[]
    executed-dir, missing both phase=pre-execution dir=executed: disposition=legacy/not evaluated blocking=[] advisory=[]
    executed-dir, missing both phase=pre-transition dir=executed: disposition=legacy/not evaluated blocking=[] advisory=[]
    APPROVED, missing both phase=author dir=pending: disposition=error blocking=["IPD-M110 Priority is required at the ready-to-execute gate: declare a priority (low|medium|high), or the sentinel 'grandfathered'", "IPD-M111 Work-Kind is required at the ready-to-execute gate: declare a work kind (bug|feature|chore|security|followup), or the sentinel 'grandfathered'"] advisory=[]
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `aw check plans --agent` reporting the new rule id, plus the ANTI-FORK grep showing the check and the lint gate call the same predicate. Paste the registry entry showing `invariant=""` and the recorded reason it is uncatalogued, citing the `check_engine.py:160-170` convention. PASTE THE MEASURED UNPIPED EXIT CODE at the chosen severity and state whether `info` or `warning` was chosen, since `drift_exit_code` exempts only `info`. Compare the total `findings` count against your own pre-edit baseline (review measured 140 pre-existing) and name any NEW rule id; do NOT require a clean run and do NOT edit another party's plan to reduce the count.
  - Observed evidence: Rule ids `check.ipd-priority-required` / `check.ipd-work-kind-required`, severity `warning` (not `info`, so it drives exit 1 per `artifact_core.drift_exit_code`), `invariant=""` because no catalog invariant covers triage metadata (registry entries at `check_engine.py` beside `check.priority-invalid`). Anti-fork: `check_engine.check_plan_priority_required` calls `ipd_lint.check_plan_priority`/`check_plan_work_kind`, the same functions `lint_text` calls. Scratch repo with four approved plans:
    ## V-04/V-09 scratch repo: tst001 missing both, tst002 valid, tst003 TODO, tst004 grandfathered
    outcome findings exit 1 findings 13
      check.priority-invalid 20260924-testset-03-tst003-c.i
      check.work-kind-invalid 20260924-testset-03-tst003-c.i
      check.ipd-priority-required 20260924-testset-01-tst001-a.i
      check.ipd-work-kind-required 20260924-testset-01-tst001-a.i
      check.ipd-priority-required 20260924-testset-03-tst003-c.i
      check.ipd-work-kind-required 20260924-testset-03-tst003-c.i
    unpiped exit: 1
  Real tree, main's code vs the lane's code on the same tree (baseline comparison, no NEW rule id):
    ## main code on this tree:
    findings 8 exit 1
    [('check.collisions-not-checked', 1), ('check.ipd-uncarried-obligation', 6), ('check.lifecycle-transition-invalid', 1)]
    ## lane code on this tree:
    findings 8 exit 1
    [('check.collisions-not-checked', 1), ('check.ipd-uncarried-obligation', 6), ('check.lifecycle-transition-invalid', 1)]
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the amended Section 4.4 enumeration AND the amended Section 9.2 `pre-execution` row, plus a `git diff` of the spec, showing both fields named with their conditional requirement and the sentinel. State the diff line count; a near-empty diff means the edit did not land. Paste `aw specs check` exiting 0 AND state explicitly that this proves only the edit did not BREAK the spec, since it already exited 0 before the amendment (measured at review); the content evidence is the diff, not the checker.
  - Observed evidence: Spec diff (8 lines: 5 insertions, 3 deletions), including the 2026-09-24 amendments for E-10..E-12. `aw specs check` exit 0, which proves only that the edit did not BREAK the spec (it exited 0 before the amendment too); the content evidence is the diff:
    ## spec diff stat vs main
     .../20260802-1904-01-ipd-structure-and-linting.spec.md            | 8 +++++---
     1 file changed, 5 insertions(+), 3 deletions(-)
    -Recognized-but-optional field (all IPDs): `Scope-Paths` (Section 4.5) is a recognized field that is NOT in the always-required set; its requirement is CONDITIONAL at the ready-to-execute lint gate (S
    +Recognized-but-optional fields (all IPDs): `Scope-Paths` (Section 4.5), `Priority`, and `Work-Kind` are recognized fields that are NOT in the always-required set; their requirement is CONDITIONAL at
    -- `Scope-Paths` is REQUIRED at the `pre-execution` checkpoint and for any plan whose `Status` is at the ready-to-execute tier (`approved`/`auto-approved`); it is OPTIONAL at every earlier drafting/re
    +- `Scope-Paths`, `Priority`, and `Work-Kind` are REQUIRED at the `pre-execution` checkpoint and for any plan whose `Status` is at the ready-to-execute tier (`approved`/`auto-approved`); they are OPTI
    +- WHERE `Priority` AND `Work-Kind` ARE DECIDED (amended 2026-09-24, planprio `lkexaw`, maintainer ruling). Both are decided where the work is FIRST RECORDED, so that the ready-to-execute requirement
    +- The scaffold placeholder is NOT a path (amended 2026-09-24, planprio `lkexaw`): a value whose first token is `TODO` (what `aw ipd scaffold` writes) is an error, so a plan approved with the placehol
    -| `pre-execution` | `review-finalize` passes; no declared blocking question remains unresolved; the persisted lifecycle state authorizes execution; no action has an illegal pre-execution state; a `Sc
    +| `pre-execution` | `review-finalize` passes; no declared blocking question remains unresolved; the persisted lifecycle state authorizes execution; no action has an illegal pre-execution state; a `Sc
    ## aw specs check
    exit=0
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_plan_priority_required.py -o addopts=""` with per-test names, showing a case for EACH of the seven surfaces E-06 enumerates. Then the FALSIFICATION: the same file with the change REVERTED IN THIS WORKTREE showing the new cases FAIL (not a historical HEAD). Finally paste the bare `python3 -m pytest` summary line and compare it to the baseline established before the first edit, naming any failure as pre-existing or new.
  - Observed evidence: Per-test output for `tests/test_plan_priority_required.py` (27 cases covering every surface E-06 lists plus E-10..E-12). Falsification, each reverted IN THIS WORKTREE and restored: reverting E-03's `diags += prio_blocking/wk_blocking` fails the three gate tests; reverting E-01's emission fails the scaffold tests:
    ScaffoldRequiresDecidedValuesTests::test_scaffold_with_explicit_values_writes_them_not_the_sentinel PASSED [  3%]
    ScaffoldRequiresDecidedValuesTests::test_scaffold_refuses_an_out_of_vocabulary_value PASSED [  7%]
    ScaffoldRequiresDecidedValuesTests::test_from_backlog_inherits_priority_work_kind_and_records_the_link PASSED [ 11%]
    ScaffoldRequiresDecidedValuesTests::test_from_backlog_inherits_the_release_gate PASSED [ 14%]
    ScaffoldRequiresDecidedValuesTests::test_an_explicit_flag_overrides_the_inherited_value PASSED [ 18%]
    ScaffoldRequiresDecidedValuesTests::test_scaffold_without_values_or_backlog_is_refused_and_writes_nothing PASSED [ 22%]
    ScaffoldRequiresDecidedValuesTests::test_an_unknown_backlog_id_is_refused PASSED [ 25%]
    SetterPositionStabilityTests::test_setter_leaves_fields_adjacent_after_status PASSED [ 29%]
    ScopePathsPlaceholderTests::test_a_real_path_list_still_parses PASSED [ 33%]
    ScopePathsPlaceholderTests::test_the_placeholder_is_a_grammar_error PASSED [ 37%]
    BacklogNewRequiresBothTests::test_the_kind_alias_still_counts PASSED [ 40%]
    BacklogNewRequiresBothTests::test_each_missing_flag_is_refused_and_nothing_is_written PASSED [ 44%]
    BacklogNewRequiresBothTests::test_both_given_is_written_with_the_chosen_values PASSED [ 48%]
    ApprovalBackstopTests::test_unresolved_or_missing_values_refuse_approval_and_leave_the_file PASSED [ 51%]
    ApprovalBackstopTests::test_grandfathered_passes_the_backstop_as_it_passes_the_gate PASSED [ 55%]
    ApprovalBackstopTests::test_decided_values_approve PASSED [ 59%]
    ApprovalBackstopTests::test_values_passed_in_the_same_call_satisfy_the_backstop PASSED [ 62%]
    ReadyToExecuteGateTests::test_unresolved_sentinel_refused_at_pre_execution PASSED [ 66%]
    ReadyToExecuteGateTests::test_approved_plan_missing_fields_refused_at_author_phase PASSED [ 70%]
    ReadyToExecuteGateTests::test_missing_priority_or_work_kind_refused_at_pre_execution PASSED [ 74%]
    ReadyToExecuteGateTests::test_grandfathered_sentinel_advisory_satisfied PASSED [ 77%]
    ReadyToExecuteGateTests::test_valid_vocab_values_pass_silently PASSED [ 81%]
    ReadyToExecuteGateTests::test_draft_or_reviewed_plan_missing_fields_passes_at_author_phase PASSED [ 85%]
    ScaffoldEmissionTests::test_scaffold_emits_unresolved_sentinels_after_status PASSED [ 88%]
    ScaffoldEmissionTests::test_placeholder_property PASSED [ 92%]
    EnumRuleAdmissionTests::test_check_plan_priority_and_work_kind_admit_sentinel PASSED [ 96%]
    TerminalExemptionTests::test_terminal_plan_missing_fields_clean_at_four_phases PASSED [100%]
    ============================== 27 passed in 1.85s ==============================
    [revert E-03 lint gate]
    test_approved_plan_missing_fields_refused_at_author_phase test_missing_priority_or_work_kind_refused_at_pre_execution test_unresolved_sentinel_refused_at_pre_execution
    [revert E-01 scaffold emission]
    test_an_explicit_flag_overrides_the_inherited_value test_from_backlog_inherits_priority_work_kind_and_records_the_link test_scaffold_emits_unresolved_sentinels_after_status test_scaffold_with_explicit_values_writes_them_not_the_sentinel
    [restored]
  Bare suite: baseline after rebasing onto main `877545fc` was `4 failed, 1833 passed, 1 skipped` (all four the `5h1lxs` gap); now:
    1853 passed, 1 skipped, 3 warnings in 42.42s
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `aw ipd set --help` showing the `--priority`/`--work-kind` choice lists AFTER the change, and state which route was taken (removal or narrowing) with its reason. Then paste the behavioral proof with unpiped exit codes: `aw ipd set <status> <non-terminal-plan> --priority -` REFUSED with a message naming the gate; and, if narrowing was chosen, the same invocation ACCEPTED against a grandfathered or terminal plan. PASTE ALL FOUR NAMED TESTS PASSING (`tests/test_ipd_priority.py::PrioritySetterTests::test_set_writes_persists_on_noop_and_clears` and the three in `tests/test_work_kind.py`), plus a `git diff` of the two test files showing the `test_the_cli_choices_match_the_shared_vocab` assertion was SPLIT rather than deleted and that the `- Kind:` survival assertion is preserved. Paste `aw specs set --help` showing `-` is STILL accepted there, proving the asymmetry is deliberate and the shared assertion was split rather than resolved by changing both verbs. Finally confirm the sibling `aw backlog set` ships WITHOUT `-` by pasting its help.
  - Observed evidence: Route taken: REMOVAL, matching the sibling `aw backlog set` and the maintainer's 2026-09-10 ruling. The four named tests lived in `tests/test_work_kind.py` and `tests/test_ipd_priority.py`, which main's `19313eed` suite trim DELETED before this plan executed; there is nothing to split, and main has no replacement asserting the `-` choice. The writer-level behaviour they guarded is shown directly below (writers still clear on `-`, and a Work-Kind write leaves the structural `- Kind:` intact):
    ## aw ipd set --help (priority/work-kind)
                                   [--priority {low,medium,high}]
                                   [--work-kind {bug,feature,chore,security,followup}]
      --priority {low,medium,high}
      --work-kind {bug,feature,chore,security,followup}
    ## refusal of '-'
    exit=2
    invalid choice: '-' (choose from 'low', 'medium', 'high')
    ## aw specs set --help
                                     [--priority {low,medium,high,-}]
                                     [--work-kind {bug,feature,chore,security,followup,-}]
    ## aw backlog set --help
                                       [--work-kind {bug,chore,feature,followup,security}]
                                       [--priority {high,low,medium}] [--dry-run]
    '# IPD\n\n- Kind: child\n- Status: draft\n- Id: abc123\n'
    True True
  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: paste `python3 -m pytest tests/test_ipd_templates.py -o addopts=""` showing all 10 tests passing AFTER the scaffold change, and paste `git diff --stat` over `tests/test_ipd_templates.py` showing ZERO lines changed (the guard was satisfied, not weakened). Paste the metadata block of each regenerated template showing both new fields in the same position E-01 chose.
  - Observed evidence: Templates unchanged by the E-10 edit because `build_skeleton`'s no-argument default is still `unresolved`:
    10 passed in 0.12s
    ## diff stat tests/test_ipd_templates.py vs main:
    (empty = zero lines changed)
    ## .aw/system/workflows/assess/templates/ipd.md
    9:- Status: draft
    10:- Work-Kind: unresolved
    11:- Priority: unresolved
    12:- Set: <set-id>
    74:- Status: open
    ## .aw/system/workflows/assess/templates/orchestrator-ipd.md
    9:- Status: draft
    10:- Work-Kind: unresolved
    11:- Priority: unresolved
    12:- Set: <set-id>
    69:- Status: open
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste `check_plan_priority` and `check_plan_work_kind` driven against THREE scratch plans with their finding counts: one carrying the sentinel (ZERO findings from both), one carrying `TODO` (ONE finding from each, proving the enum check was not widened), and one carrying a valid vocabulary value (zero). Paste the grep proving the admitted token is read from E-02's single constant rather than a second literal.
  - Observed evidence: From the V-04 scratch repo: `tst004` (grandfathered) produces ZERO `priority-invalid`/`work-kind-invalid` findings, `tst003` (`TODO`) produces ONE of each, `tst002` (valid) zero. The admitted token is read from the constant: `check_engine.check_plan_priority` compares against `_schema.PLAN_PRIORITY_GRANDFATHERED` / `_schema.PLAN_PRIORITY_UNRESOLVED` (and the Work-Kind twin), not a literal:
    ## V-04/V-09 scratch repo: tst001 missing both, tst002 valid, tst003 TODO, tst004 grandfathered
    outcome findings exit 1 findings 13
      check.priority-invalid 20260924-testset-03-tst003-c.i
      check.work-kind-invalid 20260924-testset-03-tst003-c.i
      check.ipd-priority-required 20260924-testset-01-tst001-a.i
      check.ipd-work-kind-required 20260924-testset-01-tst001-a.i
      check.ipd-priority-required 20260924-testset-03-tst003-c.i
      check.ipd-work-kind-required 20260924-testset-03-tst003-c.i
    unpiped exit: 1
  - Result: pass
- [x] V-10 validates E-10
  - Required evidence: paste `python3 -m pytest tests/test_plan_priority_required.py -o addopts="" -k "BacklogNew or ScaffoldRequires" -v` with per-test names passing; then paste the falsification: with the `backlog.run_new` refusal reverted IN THIS WORKTREE `test_each_missing_flag_is_refused_and_nothing_is_written` FAILS, and with the `run_scaffold` refusal reverted `test_scaffold_without_values_or_backlog_is_refused_and_writes_nothing` FAILS. Paste `git diff --stat tests/test_ipd_templates.py` showing zero lines changed.
  - Observed evidence: `BacklogNewRequiresBothTests` and `ScaffoldRequiresDecidedValuesTests` pass (see V-06 listing). Falsification IN THIS WORKTREE: restoring the old `or "medium"`/`or "chore"` defaults fails `test_each_missing_flag_is_refused_and_nothing_is_written`; disabling the `run_scaffold` refusal fails `test_scaffold_without_values_or_backlog_is_refused_and_writes_nothing`. `git diff main --stat -- tests/test_ipd_templates.py` is empty (V-08).
  - Result: pass
- [x] V-11 validates E-11
  - Required evidence: paste the `ApprovalBackstopTests` cases passing, then the same class with the `validate_transition_allowed` check reverted IN THIS WORKTREE showing `test_unresolved_or_missing_values_refuse_approval_and_leave_the_file` FAILS.
  - Observed evidence: `ApprovalBackstopTests` (4 cases) pass (see V-06 listing). Falsification IN THIS WORKTREE: disabling the `validate_transition_allowed` check fails `test_unresolved_or_missing_values_refuse_approval_and_leave_the_file`.
  - Result: pass
- [x] V-12 validates E-12
  - Required evidence: paste the `ScopePathsPlaceholderTests` cases and `ScopePathsCheckpointTests::test_every_phase_and_value_reaches_its_three_valued_outcome` passing, then both FAILING with the `parse_scope_paths` placeholder check reverted IN THIS WORKTREE; paste the grep showing no pending or reusable plan carries `- Scope-Paths: TODO`.
  - Observed evidence: `ScopePathsPlaceholderTests` and the new placeholder row in `ScopePathsCheckpointTests` pass. Falsification IN THIS WORKTREE: disabling the `parse_scope_paths` placeholder check fails `test_the_placeholder_is_a_grammar_error` AND `test_every_phase_and_value_reaches_its_three_valued_outcome` (`1 failed`). `grep -rln '^- Scope-Paths: TODO' .aw/records/plans` returned 0 before the change.
  - Result: pass






## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and carries `- Readiness: no-go`. It must NOT be executed: blocking OQ-02 is open, so `aw ipd lint` refuses this plan at every checkpoint until the maintainer answers it, and a human must then set it `approved`. Answer it with `/askme` (or an `aw ipd set ... --by-human`-attested approval AFTER the answer is recorded), not by an executor deciding it mid-run.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run, and compare failing NODE IDS against your own measured baseline rather than any figure quoted in this plan. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark.

When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.

NOTE THE HAZARD THAT DEFINES THIS PLAN: adding either field to `META_REQUIRED` would mass-fail the corpus at the always-on metadata check. The schema comment at `ipd_schema.py:149-152` warns against exactly that, and review QUANTIFIED it by making the change and counting: 109 of 120 pending plans and 470 of 470 `executed` plans go to `disposition: error`. If any change here would put either field in `META_REQUIRED`, it is wrong regardless of how clean it looks.

SIX CORRECTIONS FROM REVIEW THAT MUST NOT BE RE-INHERITED, because each was measured and each would otherwise send an executor down a wrong path:

1. `Scope-Paths` GREW FROM SIX PATHS TO ELEVEN, and the five additions are not optional tidying. Applying E-01 breaks two template-parity tests; applying E-07 breaks four setter tests. `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path, so an undeclared edit stalls the finalize gate.
2. THE SENTINEL IS REJECTED BY TWO SHIPPED RULES until E-09 lands. Do not write it onto any artifact before then and expect `aw check plans` to stay quiet.
3. EMIT THE FIELDS AFTER `- Status:`, NOT AFTER `- Order:`. The shipped writers anchor there and will move them on the first setter call.
4. THE TERMINAL EXEMPTION HAS EXACTLY ONE HOLE, `post-transition`, where 114 of 470 `executed` plans already error. Do not claim "no finding at any phase", and do not treat the 114 as your regression.
5. `warning` IS NOT ADVISORY: only `info` is exempt from the nonzero exit.
6. DO NOT REQUIRE `aw check plans` TO BE CLEAN. It carries 140 pre-existing findings this Set does not cause; compare against a baseline and never "fix" another party's plan in a shared checkout to reduce the count.
