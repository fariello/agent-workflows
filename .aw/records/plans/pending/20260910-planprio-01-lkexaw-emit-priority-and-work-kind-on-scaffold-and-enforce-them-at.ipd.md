# IPD: Emit Priority and Work-Kind on scaffold and enforce them at the ready-to-execute gate

- Date: 2026-09-10
- Kind: child
- Concern: A plan's `Priority` and `Work-Kind` are recognized but never emitted and never required, so adoption is zero (0 of 104 pending plans carry either) and the attention board's Priority column is empty for every plan. The scaffold omitting both is the root cause; nothing enforcing them is why nobody notices.
- Scope: Emit both fields in the scaffold skeleton, enforce them at the ready-to-execute lint gate with a `grandfathered` sentinel for the pre-cutoff corpus, register the `aw check` rule, and amend the governing IPD spec whose field enumeration currently omits both. Does NOT change the shared vocabulary, does NOT add a sort key, and does NOT touch specs, research or backlog items.
- Scope-Paths: agent_workflows/ipd_authoring.py, agent_workflows/ipd_schema.py, agent_workflows/ipd_lint.py, agent_workflows/check_engine.py, tests/test_plan_priority_required.py, .aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md
- Item-Dependencies: none
- Status: to-review
- Set: planprio
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: lkexaw

## Workflow history

- 2026-09-10 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from the maintainer's correction of 2026-09-10 that optionality was meant for LEGACY plans only, not going forward. This child owns the mechanism; siblings 02 and 03 own the backfill. THE PATTERN IS NOT NEW AND MUST BE REUSED RATHER THAN INVENTED: `Scope-Paths` already does exactly this, and its own review chose it explicitly (`3a195178`, 2026-08-23) "to avoid breaking every pending plan and the grandfather guarantee". MEASURED AT AUTHORING: `META_PRIORITY` and `META_WORK_KIND` are both in `META_RECOGNIZED` and neither is in `META_REQUIRED` (which holds exactly `Author`, `Concern`, `Date`, `Id`, `Kind`, `Scope`, `Status`); `ipd_authoring.py:170-185` emits `Item-Dependencies`, `Status`, `Set`, `Order`, `Highest E allocated`, `Author` and `Id` and NEITHER of these two; and the governing spec's field enumeration (`20260802-1904-01-ipd-structure-and-linting.spec.md:148-152`, `- Status: implemented`) lists required, optional and recognized-but-optional fields and never mentions `Priority` or `Work-Kind` at all, so the spec is SILENT rather than contradictory, which is a different amendment shape from `wfjsp4`'s.

## Goal

Make both fields required for a plan that is about to run, emitted for every new plan, and exempt for the terminal corpus, so the field stops being decorative without mass-failing 470 finished plans.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: close the root cause

- [ ] E-01 EMIT BOTH FIELDS IN THE SCAFFOLD SKELETON, in `ipd_authoring.py` where the metadata block is built (`:170-185`). This is the root cause of zero adoption and the cheapest half of the fix: a field the creating command never writes is a field nobody remembers.
  CHOOSE THE EMITTED VALUE DELIBERATELY AND STATE WHY. Do NOT emit a fabricated real value: the `xprio` orchestrator's OQ-01 already ruled that an ABSENT priority renders as unprioritized and that no value may be fabricated, and emitting `medium` by default would fabricate one at creation instead of at render. Emit the fields with a value the author must replace, following the `Item-Dependencies: unresolved` precedent in the same function (`:179`), whose own comment explains the reasoning: a reserved sentinel makes "a freshly scaffolded plan an HONEST not-ready draft". Mirror that: a scaffolded plan is honestly untriaged, and the gate in E-03 is what forces triage before it can run.
  POSITION THE FIELDS CONSISTENTLY, adjacent to each other and after `Order`, and record the chosen position, because `releases.set_item_dependencies_line` shows this repository pins canonical field position for write primitives and a later writer will need the same.
  - Depends on: none
  - Expected outcome: `aw ipd scaffold` writes both fields with a replace-me sentinel; a freshly scaffolded plan still passes `aw ipd lint --phase author`; the chosen sentinel and field position are recorded with their rationale.
  - Execution state: pending

- [ ] E-02 ADD THE `grandfathered` SENTINEL FOR BOTH FIELDS in `ipd_schema.py`, mirroring `SCOPE_PATHS_GRANDFATHERED` (`:157`) rather than inventing a second spelling. The sentinel is stored IN the plan's metadata so it travels with the plan, which is the property that makes the exemption auditable rather than a date computation.
  DO NOT ADD EITHER FIELD TO `META_REQUIRED`. That is the specific mistake the `Scope-Paths` review avoided and its comment warns against in place (`ipd_schema.py:149-152`): adding it there "would fail every existing pending plan at the always-on `author` metadata check and defeat the grandfather guarantee". Requirement is CONDITIONAL and belongs in the checkpoint layer only.
  - Depends on: E-01
  - Expected outcome: a reserved sentinel recognized for both fields, both still absent from `META_REQUIRED`, and a validator that accepts either the sentinel or a value in the shared `low|medium|high` / `bug|feature|chore|security|followup` vocabularies.
  - Execution state: pending

### Task group 2: enforce it where it bites, and only there

- [ ] E-03 ENFORCE BOTH FIELDS AT THE READY-TO-EXECUTE GATE in `ipd_lint.py`, mirroring the `Scope-Paths` gate exactly (`:925-957`) including its disposition guard. Reuse `_scope_paths_gate_applies`'s shape, or factor a shared helper from it; do not copy the predicate.
  THE GRANDFATHER BOUNDARY IS THE DISPOSITION, NOT THE DATE, which is why the existing gate returns early on status. A plan in `executed/`, `superseded/` or `not-executed/` must never be flagged, and `lint_text`'s `legacy` disposition already handles terminal plans; verify that rather than assuming it.
  A SENTINEL VALUE IS ADVISORY-SATISFIED, NOT SILENT: the `Scope-Paths` gate emits an advisory saying a re-reviewed or new plan should declare a real value (`:946-953`). Mirror that, so a grandfathered plan is visibly exempt rather than invisibly compliant.
  - Depends on: E-02
  - Expected outcome: a plan at the ready-to-execute gate without either field is REFUSED with a message naming the fix; a plan carrying the sentinel passes with an advisory; a terminal plan is untouched.
  - Execution state: pending

- [ ] E-04 REGISTER THE `aw check` RULE so the sweep and the checkpoint cannot drift apart, with a rule id in `RULE_REGISTRY`. This is the same single-predicate discipline `rnkqrc` E-04 states and that `subject_gating_blocks` already relies on: two surfaces reading one predicate, never two copies.
  STAGE THE SEVERITY, and treat that as a rollout mechanism rather than a softening: `warning` while the pending corpus still carries sentinels, `error` once it does not. Note the end state is `error`; nothing may leave the rule permanently at `warning`, which is the same obligation recorded on `rnkqrc` E-05.
  ALSO CHECK THE INVARIANT-CATALOG FIT BEFORE PICKING AN INVARIANT ID. A defect measured on 2026-09-10 has `check.setid-collision` filed under `I-09` ("filename-grammar conformance"), which does not describe it; do not repeat that by filing this rule under a convenient existing id. If no invariant fits, say so rather than mis-filing.
  - Depends on: E-03
  - Expected outcome: a registered rule reported by `aw check plans`, reading the SAME predicate as the lint gate (proven by grep, not asserted), at `warning` with the end state `error` documented.
  - Execution state: pending

### Task group 3: make the contract say so

- [ ] E-05 AMEND THE GOVERNING IPD SPEC, which is SILENT rather than wrong, and that distinction shapes the edit. `.aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md` is `- Status: implemented` and its field enumeration (`:148-152`) lists required fields (`Date`, `Kind`, `Concern`, `Scope`, `Status`, `Author`), one optional field, and `Scope-Paths` as recognized-but-optional with a CONDITIONAL requirement at the ready-to-execute gate. It never mentions `Priority` or `Work-Kind`. Add them alongside `Scope-Paths` as recognized fields whose requirement is conditional at that same gate, and state the grandfather sentinel.
  THE PATH IS DECLARED IN `Scope-Paths` DELIBERATELY, so the runners announce the spec edit before the run and the finalize gate reconciles it. Do not widen the amendment beyond these two fields.
  - Depends on: E-04
  - Expected outcome: the spec's field enumeration names both fields with their conditional requirement and sentinel, and `aw specs check` conforms.
  - Execution state: pending

- [ ] E-06 TEST THE GATE, THE SENTINEL, THE TERMINAL EXEMPTION AND THE SCAFFOLD in a new `tests/test_plan_priority_required.py`, with a falsification pass: every new assertion must be shown to FAIL against the pre-change code, since a test that passes before and after proves nothing.
  COVER THE CASE THAT WOULD MASS-FAIL THE CORPUS, because that is the failure this design exists to avoid: a plan in `executed/` with neither field must produce NO finding at any phase.
  - Depends on: E-05
  - Expected outcome: tests covering refusal, sentinel-advisory, terminal exemption and scaffold emission, each shown failing against pre-change code.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- A field is made conditionally mandatory in the CHECKPOINT layer, never by adding it to `META_REQUIRED`, because the always-on `author` metadata check would then fail the entire existing corpus. Stated in place at `ipd_schema.py:149-152`.
- The grandfather exemption is a reserved SENTINEL VALUE stored in the plan's own metadata "so it travels with the plan" (`ipd_schema.py:154-157`), not a cutoff date computed elsewhere.
- The scaffold's precedent for an untriaged field is a reserved sentinel that is neither blank nor a real value (`Item-Dependencies: unresolved`, `ipd_authoring.py:171-179`), justified there as making a fresh plan "an HONEST not-ready draft".
- An absent `Priority` renders as unprioritized and a value must NOT be fabricated (`xprio` orchestrator `u5vyye` OQ-01).

## Findings

| Id | Severity | Finding |
|---|---|---|
| F-1 | HIGH | The scaffold never emits either field. `ipd_authoring.py:170-185` writes `Item-Dependencies`, `Status`, `Set`, `Order`, `Highest E allocated`, `Author` and `Id`, and neither `Priority` nor `Work-Kind`. This is the root cause of zero adoption: 0 of 104 pending plans carry either field while all 180 backlog items carry both. |
| F-2 | HIGH | Nothing enforces either field at any checkpoint, so even a plan that carries them gains nothing and a plan that omits them is never told. Both are in `META_RECOGNIZED` and neither is in `META_REQUIRED`. |
| F-3 | MEDIUM | The governing IPD spec is SILENT on both fields, not contradictory: its enumeration at `:148-152` covers required, optional and recognized-but-optional fields and never mentions them. So the amendment ADDS a row rather than correcting a false one, which is a smaller and safer edit than the `kw5y2s` case in the `specdirs` Set. |
| F-4 | MEDIUM | "Recognized-but-optional" was inherited by analogy, not decided for these fields. The phrase originated for `Scope-Paths` (`3a195178`) with the stated reason of protecting the existing corpus. Nothing records a decision that these two should be permanently optional, and the only question ever put to the maintainer in the `xprio` Set was about RENDERING an absent value. |
| F-5 | LOW | The board already renders a Priority column for plans, so the benefit is immediate once values exist; no rendering work is needed in this Set. |

## Proposed changes (ordered, validatable)

1. Scaffold emits both fields with a replace-me sentinel (E-01).
2. A reserved `grandfathered` sentinel recognized for both, neither added to `META_REQUIRED` (E-02).
3. Conditional enforcement at the ready-to-execute gate, disposition-guarded (E-03).
4. A registered `aw check` rule reading the same predicate, staged severity (E-04).
5. The governing spec's field enumeration extended (E-05).
6. Tests with a falsification pass, including the terminal-exemption case (E-06).

## Deferred / out of scope (with reason)

- BACKFILLING ANY PENDING PLAN. Owned by siblings 02 and 03 deliberately, so the mechanism is reviewable separately from the corpus edit.
- SPECS AND RESEARCH, which `xprio` gave the same optional field. Raised as the parent's OQ-01; out of scope here.
- A PRIORITY-BASED SORT KEY. Explicitly not introduced by `xprio` and not introduced here.
- CHANGING EITHER VOCABULARY. Shared with backlog items by decision recorded in source item `p9o1oo`.

## Scope check

- Over-scope: none. The six declared paths are the scaffold writer, the schema, the lint gate, the check registry, one new test file, and the one spec whose enumeration must name the fields.
- Under-scope: this child leaves every existing pending plan non-conformant-but-warned until siblings 02 and 03 run; that is intentional sequencing, not a gap, and the staged severity in E-04 is what keeps it honest meanwhile.

## Required tests / validation

`tests/test_plan_priority_required.py`, plus falsification of every new assertion against pre-change code. Establish the suite baseline by running `python3 -m pytest` bare BEFORE the first edit and paste that output; no baseline figure is stated here deliberately.

## Spec / documentation sync

`.aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md` is amended by E-05 and is declared in `Scope-Paths`. WHY: that spec's field enumeration is the contract every plan is linted against, and adding a conditionally-required field without naming it there would leave the shipped gate unexplained by the document that defines the metadata block.

## Open questions

### OQ-01: What sentinel should a freshly scaffolded plan carry, and should it differ from the grandfather sentinel?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: RESOLVE FROM THE EXISTING PRECEDENT AT EXECUTION TIME rather than asking. Two distinct states exist and the repository already distinguishes them for `Item-Dependencies`: `unresolved` means "not yet triaged" (scaffold) while a real value or an explicit `none` means "decided". `Scope-Paths` uses `grandfathered` for "predates the rule". Those are different claims and should probably keep different words, so a NEW plan carrying the scaffold sentinel is refused at the gate (it must be triaged) while an OLD plan carrying `grandfathered` passes with an advisory (it is exempt). Non-blocking because either choice is implementable and the executor has the precedent in front of them; record the decision and its reason in E-01's outcome.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a freshly scaffolded plan's full metadata block showing both fields with the chosen sentinel and their position, then paste `aw ipd lint --phase author --agent` on it showing `clean`. State the chosen sentinel and why it was chosen over a fabricated default, citing the `xprio` no-fabrication ruling.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the sentinel constant and a grep proving neither field was added to `META_REQUIRED`. Paste the validator accepting the sentinel and REJECTING a value outside the vocabulary, with the rejection message.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste THREE gate runs with their unpiped exit codes: a pending plan missing both fields (REFUSED, message names the fix), a pending plan carrying the sentinel (passes, advisory emitted), and a plan copied from `executed/` carrying neither (NO finding at any phase). The third is the mass-failure case and must be shown explicitly.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw check plans --agent` reporting the new rule id, plus the ANTI-FORK grep showing the check and the lint gate call the same predicate. Paste the registry entry showing the chosen invariant id, and justify that choice or state that no existing invariant fits.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the amended spec section and a `git diff` of it, showing both fields named with their conditional requirement and the sentinel. Paste `aw specs check` conforming. State the diff line count; a near-empty diff means the edit did not land.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_plan_priority_required.py -o addopts=""` with per-test names, then the FALSIFICATION: the same file against pre-change code showing the new cases FAIL. Finally paste the bare `python3 -m pytest` summary line and compare it to the baseline established before the first edit, naming any failure as pre-existing or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until it has been reviewed and a human sets it `approved`.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark.

NOTE THE HAZARD THAT DEFINES THIS PLAN: adding either field to `META_REQUIRED` would mass-fail 470 terminal plans and 104 pending ones at the always-on metadata check. The schema comment at `ipd_schema.py:149-152` warns against exactly that. If any change here would put either field in `META_REQUIRED`, it is wrong regardless of how clean it looks.
