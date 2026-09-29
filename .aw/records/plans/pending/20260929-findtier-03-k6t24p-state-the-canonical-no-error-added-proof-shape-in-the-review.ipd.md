# IPD: State the canonical no-error-added proof shape in the review rubric so no plan asks for an unsatisfiable exit-0 demonstration

- Date: 2026-09-29
- Kind: child
- Concern: A PLAN AUTHOR CAN DEMAND AN EVIDENCE SHAPE THAT NO CORRECTLY-REGISTERED RULE CAN EVER PRODUCE, and when that happens the executor's only honest routes are to refuse the item or to ship the wrong severity. Measured in this lane: `artifact_core.drift_exit_code` is `return 1 if any(getattr(d, "severity", "") != "info" for d in drift) else 0`, so driving it with a synthetic single-finding list returns `warning -> 1`, `error -> 1`, `info -> 0`, empty `-> 0`. Executed plan `3i6rso`'s V-04 nonetheless requires "a synthetic-tree run whose only finding is the new code exiting 0" as the proof that a new ADVISORY rule adds no error. For its rule (`check.identity-absent-from-name`, registered `warning`, confirmed live via `check_engine.rule_spec`) that demand is unsatisfiable by construction, and the only way to satisfy the literal text is to register the rule `info`, which would ship a contract the plan itself rejected. Its executor did the right thing (refused, proved the impossibility, recorded DECISION 04-3i6rso-D1 asking for a wording fix) but the ask is unguarded, so the next author can repeat it.
- Scope: Record, ONCE, in the two plan-review rubric surfaces, the canonical two-limb no-error-added proof shape an author must demand instead (a registry severity assertion plus a behavioral gate-consequence measurement), and name the exit-0 form as the specific anti-pattern to flag. EXCLUDES any change to `artifact_core.drift_exit_code`, to `check_engine.RULE_REGISTRY`, or to any rule's registered severity: the code is correct and this is an authoring-contract defect. EXCLUDES editing executed plan `3i6rso` beyond nothing at all (its record is immutable and it already documents the refusal). EXCLUDES the suite-coverage half of this area, which sibling `y43g6q` owns. EXCLUDES adding a mechanical lint rule, for the reason the adjacent re-derivation convention states: distinguishing a satisfiable evidence demand from an unsatisfiable one requires semantic reading.
- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/review-rubric.md, tests/test_plan_review_feasibility_rule.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: hwhbc8
- Set: findtier
- Order: 3
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: k6t24p

## Workflow history

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `hwhbc8`. THE ITEM'S PREMISE WAS VERIFIED RATHER THAN TRUSTED, and it holds exactly: `drift_exit_code`'s source reads as the item quotes it, and driving it returns 1 for a warning-only list. THE ITEM'S SUGGESTED FIX, HOWEVER, IS NOW PROHIBITED, which is the single most load-bearing finding here and the reason this plan does not implement what the item asked for. The item proposes "a severity assertion plus a lifecycle-gate SOURCE CENSUS" as the canonical shape, citing `3i6rso`'s `test_the_rule_gates_no_lifecycle_step`. That test READ `ipd_lint.py` and `ipd_lifecycle.py` as text and asserted the rule id was absent, and commit `80db6750` ("delete 366 tests that pinned code structure instead of behaviour") DELETED it by name. GUIDING_PRINCIPLES P16 now prohibits exactly that construction ("Never use ... `read_text()`, or substring/regex searches against production code"). So writing the item's literal suggestion into the rubric would canonize a test shape the repository deletes on sight. Limb (b) is therefore restated BEHAVIORALLY, as a gate-consequence measurement, which is both P16-conforming and strictly stronger. TWO OF THE ITEM'S THREE CITATIONS ARE ALSO STALE: `tests/test_review_findings.py` (cited for "an exit-code argument proves nothing") and `tests/test_name_identity_report.py` were BOTH deleted, by `80db6750` and `19313eed` respectively; neither exists at HEAD, so this plan cites the live sources instead (`check_engine.py`'s registration comments, which do survive, and `artifact_core.drift_exit_code` measured directly). The surviving `check.system-layout-*`, `check.stale-index-missing`, and `check.review-decision-unescalated` comments were each re-read and do state the fact. SIBLING BOUNDARY: `y43g6q` (`findtier` Order 01, `reviewed`) independently re-discovered the same test deletion and restores the lost `check_name_identity` COVERAGE; this plan touches no test of that rule and no `check_engine` code, so the two do not overlap.

## Goal

Make the no-error-added claim provable by an author who demands it, so an advisory rule's harmlessness is evidenced by a measurement that can actually be produced rather than by an exit code that only an `info` registration could ever yield.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: record the canonical proof shape where a plan author reads it

- [ ] E-01 ADD THE CANONICAL NO-ERROR-ADDED PROOF SHAPE to the single-file rubric's `## Engineering rubric` section G (`Plan executability`), as one bullet in the style of the `Live-artifact success criteria vs. stable code facts (re-derivation convention)` bullet that already sits there, and place it IMMEDIATELY AFTER that bullet, which is its closest sibling (both govern what an author may demand as evidence).
  STATE THE TWO LIMBS THE AUTHOR MUST DEMAND, and no more: (a) a REGISTRY SEVERITY assertion, that the rule id resolves through `check_engine.rule_spec` to the intended severity; and (b) a GATE-CONSEQUENCE MEASUREMENT, that `artifact_core.drift_exit_code` is DRIVEN with a finding at that severity and its actual return value pasted, so the rule's effect on the gate is measured rather than assumed.
  STATE THE ANTI-PATTERN BY NAME, since naming it is the whole point: a demand for "a synthetic tree whose only finding is the new rule, on which `aw check` exits 0" is UNSATISFIABLE for any severity other than `info`, because `drift_exit_code` exempts `info` alone. An author who writes it forces the executor to either refuse the item or mis-register the rule `info` to make the sentence true, and the second is a shipped contract defect. Reviewers must flag it as an IN-SCOPE finding on the plan.
  SAY WHAT `warning` DOES AND DOES NOT MEAN, because this is the misreading that generates the bad ask: `warning` does NOT mean "cannot fail anything". Behaviorally `error` and `warning` are equally loud (both exit 1); they differ in the CLASS of condition they report, not in gate consequence. `info` is the only advisory severity.
  DO NOT propose a source census, a caller count, or any `read_text`/`inspect`/regex read of `agent_workflows/*.py` as a limb. GUIDING_PRINCIPLES P16 prohibits it, and the specific census this backlog item suggested was deleted by commit `80db6750`; canonizing it would mint tests that are born condemned.
  - Depends on: none
  - Expected outcome: the single-file rubric carries the bullet, positioned directly after the re-derivation bullet in section G, naming both required limbs, naming the exit-0 ask as a reviewer-flaggable anti-pattern, stating that `info` is the only severity `drift_exit_code` exempts, and prohibiting a source-census limb.
  - Execution state: pending

- [ ] E-02 MIRROR THE SAME BULLET INTO THE LONG-FORM RUBRIC at `.aw/system/workflows/plan-review-long/review-rubric.md`, so the two review routes cannot give an author different contracts.
  PLACE IT BESIDE ITS EXISTING SIBLING, the `Right-sizing and conceptual density (per E-item)` bullet, which is present in BOTH files and is the anchor that shows where shared rubric bullets live. VERIFY BEFORE WRITING that the re-derivation bullet from E-01's anchor is ABSENT from this file, which is what makes the long-form rubric the drifted surface rather than a second copy: measured in this lane, `review-rubric.md` carries the right-sizing bullet but NOT the re-derivation one. If your own read disagrees, state what you observed and place the new bullet beside the right-sizing bullet regardless.
  KEEP THE TWO WORDINGS SUBSTANTIVELY IDENTICAL. Both files must demand the same two limbs and name the same anti-pattern; incidental section-numbering differences are fine, a different contract is not.
  - Depends on: E-01
  - Expected outcome: the long-form rubric carries a substantively identical bullet beside its right-sizing bullet, and the observed presence/absence of the re-derivation bullet in that file is stated.
  - Execution state: pending

### Task group 2: guard the wording against silent loss

- [ ] E-03 PIN BOTH BULLETS with anchor-phrase assertions in `tests/test_plan_review_feasibility_rule.py`, the module that ALREADY pins workflow-body prose in exactly this way and whose own docstring records why that is permitted.
  REUSE THAT MODULE RATHER THAN CREATING ONE, and reuse its established pattern: it defines `ANCHOR_PHRASES`, resolves `WORKFLOWS_DIR` from `Path(__file__).resolve().parent.parent`, and reads the workflow body with `read_text`. Add a test asserting a distinctive anchor phrase from the new bullet is present in BOTH `plan-review/plan-review.md` and `plan-review-long/review-rubric.md`, following the parity-pointer test already in that file.
  THIS IS INSIDE P16'S NARROW EXCEPTION AND YOU MUST SAY SO IN THE TEST'S OWN DOCSTRING, not merely assume it. P16 permits content verification "only where the text or file itself is the artifact under test", and a workflow body IS the artifact this plan changes; the test reads NO `agent_workflows/*.py`. The module's existing docstring already makes this argument for the same files and is the precedent to cite.
  CHOOSE ANCHORS THAT SURVIVE COPY-EDITING: pick short distinctive tokens tied to the CONTRACT (for example the rule symbol `drift_exit_code` and the phrase naming the exit-0 ask unsatisfiable) rather than a whole sentence, so a reworded-but-correct rubric does not fail.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_plan_review_feasibility_rule.py` passes with the new test present, the test's docstring records the P16 narrow-exception argument, and deleting either bullet makes it fail.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A REVIEW-RUBRIC CONVENTION HAS A TWO-FILE PARITY OBLIGATION. `.aw/system/workflows/plan-review/plan-review.md` (single-file route) and `.aw/system/workflows/plan-review-long/review-rubric.md` (long-form route) both carry the rubric, and the `Right-sizing and conceptual density (per E-item)` bullet appears VERBATIM in both, which is the pattern to follow. Measured drift: the `Live-artifact success criteria vs. stable code facts` bullet exists ONLY in the single-file copy, so parity is an obligation the repository does not always meet and this plan must not assume.
- WORKFLOW BODIES ARE TRACKED SOURCE HERE, NOT INSTALLED OUTPUT. `git ls-files` resolves `.aw/system/workflows/plan-review/plan-review.md`, `git check-ignore` does not match it, and 158 files under `.aw/system/workflows/` are tracked. `.opencode/commands/plan-review.md` and `.claude/commands/plan-review.md` are thin aliases that say "Read and execute @.aw/system/workflows/plan-review/plan-review.md", so editing the body is the correct single-source edit and the aliases need no change.
- THE PRECEDENT FOR EDITING A RUBRIC TO FIX AN AUTHORING DEFECT IS `tgop8e`, which added the re-derivation bullet this plan sits beside. Its own Scope states the shape: "record the convention where a future author will read it", treating the problem as "an authoring-contract defect and not a code defect". It also records that no gate reads a criterion, so such a convention "is enforced by REVIEW alone" - which is why this plan adds no lint rule.
- WORKFLOW-PROSE TESTS ARE PERMITTED BUT MUST ARGUE FOR THEMSELVES. `tests/test_plan_review_feasibility_rule.py` opens with an "Exemption from source-text-pin prohibition" docstring justifying itself against the concurrent deletion sweep, on the grounds that "a workflow body is a WORKFLOW BODY, the artifact under change" and the test reads no `agent_workflows/*` source. Cite it by SYMBOL and reuse it; do not create a parallel module.
- THE AUDITOR SIDE OF THIS PROBLEM IS ALREADY SOLVED, AND THIS PLAN IS THE AUTHOR SIDE. Commit `e6566341` added to `verify-execution/intent-audit.md` a three-part bar for classifying an item whose evidence reports the demand itself unsatisfiable (state why, prove impossibility empirically, evidence the satisfiable counterpart), and says such a demand "is a plan defect" the auditor must report. That tells a VERIFIER how to grade a refusal after the fact; nothing yet tells an AUTHOR not to write the demand. The same commit's `plan-review` addition is a revision-sweep obligation, not an evidence-shape rule.

## Findings

| Id | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | HIGH | THE ITEM'S PREMISE IS EXACTLY RIGHT AND REPRODUCES | `artifact_core.drift_exit_code` reads `return 1 if any(getattr(d, "severity", "") != "info" for d in drift) else 0`, and its docstring states an `info` finding "does NOT fail the gate". Driven with a single synthetic `Drift`: `warning -> 1`, `error -> 1`, `info -> 0`, empty `-> 0`. So a warning-only tree exits 1 by design and the exit-0 demand cannot be met. |
| F-02 | HIGH | THE ITEM'S SUGGESTED FIX IS NOW PROHIBITED, so this plan must NOT implement it literally | The item proposes a "lifecycle-gate source census" as a limb, citing `3i6rso`'s `test_the_rule_gates_no_lifecycle_step`. That test did `(pkg / module).read_text(...)` on `ipd_lint.py`/`ipd_lifecycle.py` and asserted `assertNotIn(RULE, text)`. Commit `80db6750` ("delete 366 tests that pinned code structure instead of behaviour") removed it. GUIDING_PRINCIPLES P16 prohibits "`read_text()`, or substring/regex searches against production code". Limb (b) is therefore a gate-consequence MEASUREMENT instead. |
| F-03 | MEDIUM | TWO OF THE ITEM'S THREE SUPPORTING CITATIONS NO LONGER EXIST | The item cites `tests/test_review_findings.py` for the "proves nothing" statement and `3i6rso` cites `tests/test_name_identity_report.py` for the replacement proof. Neither is at HEAD: `80db6750` deleted the first (-51 lines) and `19313eed` ("trim test suite from 9,136 to under 2,000 tests") deleted the second. Cite the LIVE sources instead. |
| F-04 | MEDIUM | THE SURVIVING IN-CODE PRECEDENTS DO STATE THE FACT, so the convention is a codification and not an invention | Re-read at HEAD: `check.system-layout-*` records "`artifact_core.drift_exit_code` fails the gate for anything that is not `info`, so either severity exits 1 and fails CI. The class is what differs." `check.stale-index-missing` records "`info` -> the ONLY non-failing severity". A third comment records the measurement `error -> 1, warning -> 1, info -> 0, empty -> 1`. Three independent registrations teach the same lesson in comments no plan author is obliged to read. |
| F-05 | MEDIUM | THE ANTI-PATTERN IS LIVE IN A PENDING PLAN, so this is not a historical cleanup | `.aw/records/plans/pending/20260928-1zknu7-01-0ykozn-...ipd.md` demands "the exit-code control proving a repository whose only finding is this rule exits 0". That plan is SATISFIABLE because its rule is registered `info` and its own text pins that (`- Exit-code control: ... pinning the `info` contract`), so it is a correct use of the form. It nonetheless shows the wording propagating, and it is the case that makes the distinction worth stating: the form is valid for `info` and unsatisfiable otherwise. |
| F-06 | LOW | THE REGISTRY MAKES THE BLAST RADIUS CONCRETE | `check_engine.RULE_REGISTRY` holds 52 rules: 33 `error`, 12 `warning`, 7 `info`. So 45 of 52 registered rules could not satisfy the exit-0 demand, and `check.identity-absent-from-name` resolves through `check_engine.rule_spec` to `RuleSpec(severity='warning', ...)`, confirming `3i6rso`'s rule is one of them. |
| F-07 | LOW | THE SIBLING PLAN IN THIS SET CORROBORATES F-02 INDEPENDENTLY AND DOES NOT OVERLAP | `y43g6q` (`findtier` Order 01, `reviewed`) records that `tests/test_name_identity_report.py` "was DELETED by a suite-trim commit, leaving `check_engine.check_name_identity`'s `drift` branch with zero coverage". Its `Scope-Paths` are `tests/test_check_engine.py, tests/test_find_filters.py`, disjoint from this plan's three paths. It restores lost coverage; this plan fixes the authoring contract. |

## Proposed changes (ordered, validatable)

1. Add the two-limb no-error-added proof-shape bullet to the single-file rubric's section G, beside the re-derivation bullet, naming the exit-0 ask as the anti-pattern and prohibiting a source-census limb (E-01).
2. Mirror the same bullet into the long-form rubric beside its right-sizing bullet, recording the observed parity state of the re-derivation bullet (E-02).
3. Pin both bullets with anchor-phrase assertions in the existing workflow-prose test module, with the P16 narrow-exception argument in the test's docstring (E-03).

## Deferred / out of scope (with reason)

- A MECHANICAL LINT RULE detecting an unsatisfiable evidence demand. Deliberately not attempted, for the reason the adjacent re-derivation bullet already records for itself: "Review is the only enforcement surface; no mechanical lint rule is attempted because distinguishing live artifact counts from stable code facts requires semantic reading." Recognizing that a `V-*` item's prose demands an impossible exit code is strictly harder. No durable carrier is needed: this is a decision not to build, not an outstanding obligation.
- ANY EDIT TO `3i6rso`. It is in `executed/` and its record is immutable by policy. It already documents the refusal and DECISION 04-3i6rso-D1 in its own `Observed evidence`, so a reader who reaches it finds the correction. No appended history note is proposed either, because the plan's own evidence block is already the fuller record.
- THE PENDING PLAN `0ykozn`'s WORDING (F-05). Not touched: its rule is registered `info`, so its exit-0 control is genuinely satisfiable and its own text pins that contract. Editing another pending plan to use different words for a correct demand is churn, and it is not this plan's `Scope-Paths`.
- RESTORING THE DELETED `check_name_identity` COVERAGE (F-02, F-07). Owned by sibling `y43g6q`, which is already `reviewed` with disjoint `Scope-Paths`. Duplicating it here would collide in `tests/test_check_engine.py`.
- ANY CHANGE TO `drift_exit_code`, to a registered severity, or to `RULE_REGISTRY`. The code is correct: an `info`-only exemption is the deliberate contract three separate registration comments defend. This is an authoring-contract defect.

## Scope check

- Over-scope: none. All three declared paths receive changes (the two rubric bodies in E-01/E-02, the test module in E-03) and nothing else is touched. `agent_workflows/` is deliberately absent from `- Scope-Paths:`, which is what keeps the "no code change" boundary mechanical rather than a promise.
- Under-scope: the deliberate non-goals are enumerated in `## Deferred / out of scope` with a reason each; the load-bearing one is that no mechanical lint rule is attempted, so this convention is enforced by review alone exactly as its sibling bullet is.

## Required tests / validation

- `python3 -m pytest tests/test_plan_review_feasibility_rule.py` passes with the new test present. Run the suite BARE as `python3 -m pytest` for the regression check; do NOT pass `-n0`, an extra `-q`, or `-p no:randomly` (`pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, and an extra `-q` suppresses the `N passed` line this plan requires you to paste).
- MUTATION SENSITIVITY IS REQUIRED, NOT OPTIONAL, because an anchor-phrase test that passes against a file missing the bullet is worthless. Delete the bullet from each rubric in turn IN A SCRATCH COPY OR AN IN-MEMORY PATCH, show the test FAILS, and restore. Do not commit a mutated rubric.
- `aw ipd lint --phase pre-transition --agent <this plan>` reports conforming before any terminal transition.
- NO PRODUCTION CODE CHANGE, proven mechanically: `git diff --name-only` at finalize must list no path under `agent_workflows/`.

## Spec / documentation sync

- NO SPEC IS AMENDED, and this is a deliberate placement decision rather than an omission. The backlog item offers a choice ("in the ipd-spec or a review checklist"); the REVIEW CHECKLIST is correct here because the `ipd-spec` doc consolidates by REFERENCE and explicitly delegates this class of convention outward - it already points at "`.aw/system/workflows/plan-review/plan-review.md` Rubric G for the live-artifact re-derivation convention and code-facts exemptions" rather than restating it. Adding a second evidence-shape convention to the rubric follows that established seam and keeps the single source of truth in one place. No `.spec.md` path appears in `- Scope-Paths:`, so the runners' spec-edit announcement correctly reports none.
- The precedent `tgop8e` DID touch the `ipd-spec` doc, but only to ADD the outward pointer that now exists; the pointer covers Rubric G generally, so no new pointer sentence is required for a second bullet in the same rubric section.

## Open questions

### OQ-01: Should the new convention also be mirrored into `spec-review`?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: NO, resolved from repository evidence rather than left open. The defect is a PLAN's `V-*` evidence demand, and `spec-review.md` reviews specs, which carry no `E-*`/`V-*` checklists at all; its severity vocabulary is about anchor resolution, not evidence shape. The two files this plan does touch are the two that carry the shared `Right-sizing and conceptual density` bullet, which is the repository's own demarcation of where a plan-authoring rubric convention belongs. Mirroring into `spec-review` would put a plan-only rule where no plan is reviewed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the committed diff hunk of `.aw/system/workflows/plan-review/plan-review.md` showing the new bullet and showing it sits IMMEDIATELY AFTER the `Live-artifact success criteria vs. stable code facts` bullet inside `## Engineering rubric` section G. QUOTE the added text and CONFIRM against it, clause by clause, that all four required elements are present: limb (a) the `check_engine.rule_spec` severity assertion, limb (b) the `artifact_core.drift_exit_code` gate-consequence measurement, the exit-0 ask named as a reviewer-flaggable anti-pattern, and the statement that `info` is the only severity `drift_exit_code` exempts. CONFIRM the bullet contains NO source-census, caller-count, or `read_text`/`inspect` limb; its presence FAILS this item under F-02. ALSO paste your OWN re-measurement of `drift_exit_code` driven with one synthetic finding at each of `error`, `warning`, `info`, and an empty list, and state the four return values you observed rather than repeating F-01's; if `info -> 0` does not reproduce, STOP, because the convention's premise has changed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the committed diff hunk of `.aw/system/workflows/plan-review-long/review-rubric.md` showing the mirrored bullet beside the `Right-sizing and conceptual density (per E-item)` bullet. PASTE a side-by-side or diff of the two added bullets from both files and CONFIRM they demand the same two limbs and name the same anti-pattern; a substantive divergence FAILS this item, while incidental numbering differences do not. STATE what you observed about the `Live-artifact success criteria` bullet's presence in `review-rubric.md` (this lane measured it ABSENT) and confirm your placement choice against what you actually found.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the ACTUAL output of `python3 -m pytest tests/test_plan_review_feasibility_rule.py` showing the new test passing, and the bare `python3 -m pytest` summary line with the `N passed` count you observed (do not assert any count recorded in this plan; measure your own). PASTE THE MUTATION PROOF, which is what makes the test worth having: remove the new bullet from EACH rubric in turn (scratch copy or in-memory patch) and paste the FAILING output for each, then confirm both files are restored byte-identical (`git diff` on both paths must be empty after the mutation runs, aside from the intended additions). PASTE the new test's docstring showing the P16 narrow-exception argument is recorded, and CONFIRM the test reads no path under `agent_workflows/`. FINALLY paste `git diff --name-only` at finalize and confirm no `agent_workflows/` path appears.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the three paths in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. This is a SHARED CHECKOUT: verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since `pre-commit` restores unstaged changes and can leave paths you never staged in the index; unstage precisely with `git restore --staged <path>` rather than a bare `git reset`.

`agent_workflows/` MUST END BYTE-UNCHANGED. The whole finding is that the CODE is correct and the AUTHORING CONTRACT is not, so a diff under `agent_workflows/` means the plan was misread. Specifically do not "fix" `drift_exit_code`, do not change any rule's registered severity, and do not add a rule to `RULE_REGISTRY`.

DO NOT WRITE THE BACKLOG ITEM'S SUGGESTION VERBATIM. It asks for a "lifecycle-gate source census", which commit `80db6750` deleted as a code-structure pin and GUIDING_PRINCIPLES P16 prohibits. Limb (b) is a BEHAVIORAL gate-consequence measurement. If you find yourself writing `read_text` against `agent_workflows/*.py`, stop and re-read F-02.

DO NOT EDIT `3i6rso` or any other plan under `.aw/records/plans/executed/`; its record is immutable and already documents the refusal. Do not edit pending plan `0ykozn` (F-05): its exit-0 control is satisfiable because its rule is `info`.

RE-LOCATE EVERY ANCHOR BY ITS QUOTED TEXT, not by any line number in this plan: both rubric files are edited by other work and an offset will have drifted. Re-read the other pending plans touching these paths before starting; measured at authoring, none declares them, but that can change.

POST-GATE LIFECYCLE TRANSITION (not an `E-*` item): after every `V-*` is verified with pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, append the `## Workflow history` line, set the terminal `- Status:`, and move this plan from `.aw/records/plans/pending/` to `.aw/records/plans/executed/` in a path-scoped lifecycle commit. Prefer `aw ipd finalize`; if an out-of-scope path was genuinely required, justify it with `--scope-reason` rather than widening the fence by hand.
