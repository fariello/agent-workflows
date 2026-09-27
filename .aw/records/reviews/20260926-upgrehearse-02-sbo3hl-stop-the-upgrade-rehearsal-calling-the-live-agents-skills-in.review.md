# Review findings: plan sbo3hl

- Subject-Id: sbo3hl
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated lane worktree. Structural preflight `aw ipd lint --phase author --detail`
returned `advisory` (exit 0) with ONE finding, `IPD-Z602` against E-05, which turned out to be
correct and is addressed below. No pre-review snapshot was needed: `git status --porcelain` was
empty and the lane input under `.aw/state/lane-inputs/rev-7/` is byte-identical to the tracked plan.

THE PREMISE IS CORRECT AND THE DEFECT IS REAL, RE-DRIVEN TWO WAYS. Through the state table:
`derive_observations({"baseline_layout":"legacy","layout":"aw+litter","legacy_files_remaining":92,
"legacy_breakdown":{"skills":92}})` returns `['empty-legacy-dirs', 'legacy-leftovers',
'orphaned-skills']`, exactly as the Concern claims. End to end: a real `create_sandbox` sandbox built
from a legacy source, then migrated by hand (drop `.agents/workflows`, stamp `.aw/system/VERSION`,
leave two files under `.agents/skills/x/`) probes to `['legacy-leftovers', 'orphaned-skills']`. And
the justification holds: `engine.resolve_skills_dir` returns `.agents/skills` for BOTH `"aw"` and
`"legacy"` (driven), so the observation's two clauses are false on every state, not merely
over-broad. The `orphaned-skills` note is the one the backlog item quotes, and it appears exactly
once in the module and once in the restored test row. This is a well-targeted bug fix with a correct
diagnosis.

**THE FIX'S ARITHMETIC REACHES TWO OTHER PINNED ROWS AND THE PLAN NAMED NEITHER.** E-03 changes the
leftover count for EVERY migrated state, so every existing row asserting `legacy-leftovers` behavior
is in its blast radius. I drove all of them. Both survive, and that is the good news, but they
survive for DIFFERENT reasons and neither was written down: the row "a MIGRATING run that left files
under `.agents/`" carries `legacy_files_remaining: 5` with NO `legacy_breakdown`, so the subtraction
is `5 - 0 = 5` and it still fires; the row "a run that deliberately KEPT the legacy layout" is NOT
migrated, so the leftover predicate never evaluates for it at all and its `331 - 92` is never
computed. The risk this closes is concrete: had either row been a skills-only migrated state it would
have gone SILENT, and the executor would have met an unexplained V-05 failure with no way to tell a
regression from the intended change. Both rows are now named in E-01 with their arithmetic, listed as
controls in Required tests, and called out in V-05.

**THE REAL-PROBE TEST WOULD HAVE PASSED VACUOUSLY.** This is the finding that justifies the review.
The authored E-05(3) asks for a test asserting that `orphaned-skills` and `legacy-leftovers` do NOT
appear. An absence assertion is only as good as the proof that the machinery was engaged, and here it
is not: `probe` reads `baseline_layout` from the `.aw-upgrade-test.json` marker via
`upgrade_rehearsal.read_marker`, and `create_sandbox` is what writes that marker from
`source.to_dict()`. Measured: a hand-built sandbox with `.aw/system/VERSION` and two files under
`.agents/skills/` probes to `baseline_layout=None`, which makes `migrated` False, which yields
`observations == []` BEFORE ANY FIX. So the test would pass against the unfixed module and be pasted
as evidence the defect was closed. The authored text did name `create_sandbox`, so the right
instrument was chosen, but it did not say the source must be LEGACY nor why the marker matters, and
that is precisely the detail an executor economizes away when a hand-built directory looks
equivalent. E-07 now states the dependency and the measured failure mode, and V-07 makes an
unproven fixture a FAILED validation by requiring the `baseline_layout`/`layout` pair to be pasted.

**ONE E-ITEM BUNDLED THREE TEST SURFACES.** The linter's `IPD-Z602` advisory against E-05 was right
and I investigated it by decomposition rather than dismissing it. The authored E-05 carried the
state-dict table edit, a live-sandbox `create_sandbox`+`probe` test, and a captured-stdout `report`
test: three different fixtures, three different failure modes, three different pieces of evidence.
Split into E-05 (table rows) and E-07 (the two live-behavior tests), with V-07 added and the E/V
bijection kept at 7/7. The linter now reports `conforming` with no advisory. The practical gain is
attribution: a failure in the live fixture can no longer be mistaken for a table regression.

ON DELETING AN OBSERVATION, which deserved scrutiny because the codebase argues against it. The
restored table's failure message says "the fix for a spurious finding is to narrow the predicate,
never to delete the observation", and the plan's conventions section anticipated the objection. I
checked the reasoning rather than accepting it: a narrowed predicate needs at least one true-positive
state, and there is none, because the resolver returns the same path for both layouts and the
installer writes skills there on every run. So deletion is correct here and the useful half is
preserved as the inverse `skills-missing`. The gate now says this to the approver in those terms,
since "this plan deletes an observation" is the kind of thing a reviewer of the NEXT plan will cite as
precedent, and the precedent should carry its own limiting condition.

ON THE SHIM, verified rather than assumed because the mechanism could easily have been wrong. The
plan declares `tools/aw_upgrade_test.py` deliberately out of scope on the grounds that it re-exports.
It does so with a by-value loop over `vars(upgrade_rehearsal)` at import time, which COULD have bound
stale objects; driven, `uat.derive_observations is upgrade_rehearsal.derive_observations` and
`uat.probe is upgrade_rehearsal.probe` are both True, so the restored tests reach the same function
objects this plan edits. The under-scope claim is sound and now records the check.

ON THE RELEASE GATE, driven rather than trusted. Backlog `izfscm` is `Work-Kind: bug` with
`Blocks-Release: next`, and the plan correctly inherits both the gate and `From-Backlog`.
`evaluate_blocking_close(repo, <izfscm>, "done")` returns `legitimate=False`, severity `error`,
reason "gate 'next' is handed off to From-Backlog carrier(s) ... but the work has not shipped
(carrier is not executed/implemented)", which is exactly the fail-closed behavior the gate's ordering
depends on, and the plan's gate already states the correct order. `releases.check_from_backlog` and
`check_blocks_release` report no drift for `sbo3hl`.

ON THE DEPENDENCY, checked because the plan is written as if it might not hold. `8ud1is` is ALREADY
EXECUTED and all three of its deliverables are present: the package module, the shim, and the
restored test file including the defect-pinning row with its `why` asserting the skills are "ORPHANED
SKILLS a host may still discover". So E-01's precondition is met and the stop condition is a
drift guard rather than an expected branch; the gate now says so, which keeps an executor from
reading a satisfied precondition as a surprise.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | HIGH | UNDER-SCOPE | E. verification (an absence assertion with an unproven fixture) | `upgrade_rehearsal.read_marker` reads `.aw-upgrade-test.json`; `create_sandbox` writes it from `source.to_dict()`; driven: hand-built sandbox -> `baseline_layout=None`, `migrated` False, `observations=[]` pre-fix; via `create_sandbox` from a legacy source -> `baseline_layout='legacy'`, `observations=['legacy-leftovers','orphaned-skills']` | **THE REAL-PROBE TEST WOULD HAVE PASSED AGAINST THE UNFIXED MODULE.** It asserts two observation kinds are ABSENT, and absence is trivially true when `migrated` is False, which is what a fixture lacking the sandbox marker produces. The plan named `create_sandbox` but did not state that the source must be LEGACY or why the marker is load-bearing, so the cheapest reading (build a directory by hand) yields a green test that proves nothing and would be pasted as proof the defect was closed. | C:Low; U:Low; S:Low; F:Medium (a fix reported as verified while unverified); Overall:Low | FIXED | Recorded as F-9. E-07(1) now states the marker dependency, requires a legacy source through `create_sandbox`, and carries the measured before/after pair. V-07 requires the probed `baseline_layout`/`layout` to be pasted and declares a `None` baseline a FAILED validation even when the assertions pass. The gate repeats it under the honesty rule. |
| PR-502 | MEDIUM | UNDER-SCOPE | A. correctness; E. verification | driven: `derive_observations({'baseline_layout':'legacy','layout':'aw','legacy_files_remaining':5})` -> `['legacy-leftovers']` (no breakdown, so `5-0=5`); legacy-kept row -> `['legacy-kept']` (not migrated, so `331-92` never computed) | **THE NEW SUBTRACTION REACHES TWO OTHER PINNED ROWS THE PLAN DID NOT NAME.** E-03 changes the leftover count for every migrated state, so both existing rows asserting leftover behavior are in its blast radius. Both survive, for two different and unstated reasons. Had either been a skills-only migrated row it would have gone silent, and the executor would have hit an unexplained V-05 failure unable to distinguish a regression from the intended change. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-7 added with both rows and their arithmetic. E-01 now measures both rows BEFORE the change and its expected outcome states they must read the same after. Required tests lists them as explicit controls; V-05 names them so a silenced true leftover fails loudly. |
| PR-503 | MEDIUM | UNDER-SCOPE | G. executability (right-sizing) | `aw ipd lint --phase author --detail` -> `IPD-Z602 (line 59): E-05: action text may bundle multiple concerns`; the item carried a table edit, a `create_sandbox` live test, and a captured-stdout `report` test | **ONE E-ITEM BUNDLED THREE INDEPENDENT TEST SURFACES.** Three fixtures, three failure modes, three evidence shapes in one item, which is the conceptual-density case the rubric asks a reviewer to judge and which the linter also flagged. Bundled, a live-fixture failure is indistinguishable from a table regression in the V-item's evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-8 added. Split into E-05 (state-dict table rows) and E-07 (the two live-behavior tests), V-07 added, `Highest E allocated` raised to 07, Proposed changes renumbered. E/V bijection stays 7/7 and the linter now reports `conforming` with no advisory. |
| PR-504 | LOW | IN-SCOPE | C. architecture (an out-of-scope claim resting on an unverified mechanism) | `tools/aw_upgrade_test.py` copies `vars(upgrade_rehearsal)` into its globals at import; driven: `uat.derive_observations is upgrade_rehearsal.derive_observations` and `uat.probe is upgrade_rehearsal.probe` are both True | **THE UNDER-SCOPE JUSTIFICATION RESTED ON A BY-VALUE RE-EXPORT NOBODY HAD CHECKED.** The plan correctly leaves the shim out of `Scope-Paths` because it re-exports, but a value-copy loop is exactly the shape that CAN bind stale objects, and the restored tests reach every internal through `uat.<name>`. If the identity did not hold, every new test would exercise a different function than the one edited. It holds. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Scope-check bullet now records the driven identity check and why it was worth making, so the out-of-scope decision is checkable instead of asserted. |
| PR-505 | LOW | IN-SCOPE | F. honest documentation (a precedent that needs its limiting condition) | restored table failure message: "the fix for a spurious finding is to narrow the predicate, never to delete the observation"; driven: `resolve_skills_dir('aw') == resolve_skills_dir('legacy') == '.agents/skills'` | **THE PLAN DELETES AN OBSERVATION AGAINST ITS OWN CODEBASE'S STATED RULE AND EXPLAINED THAT ONLY IN THE CONVENTIONS SECTION.** The reasoning is correct (no true-positive state exists, so there is nothing to narrow toward), but an approver reading the gate would not see it, and the next plan citing this one as precedent would inherit the conclusion without its limiting condition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate gained a paragraph stating that deletion is the EXCEPTION, why it applies here (no narrowable true positive, driven resolver equality), and that the useful half survives as `skills-missing`. The dependency state and a proven-versus-asserted paragraph were added alongside. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The real-probe test can pass vacuously (PR-501). Rewrite the fixture requirement, or drop the test for a state-dict row? | REQUIRE THE LIVE FIXTURE and make V-07 prove it engaged, stating the marker dependency in the item. | (a) Replace it with another state-dict row: rejected, the state table already covers the deriver and a hand-fed dict cannot catch a `probe` that populates `skills_files` wrongly, which is E-02's actual deliverable; the end-to-end path is the only place probe and deriver are tested together. (b) Keep the wording and trust the executor to use `create_sandbox` correctly: rejected, the failure is SILENT and green, which is the worst shape; the cheapest wrong fixture looks equivalent to the right one. (c) Assert on `migrated` directly: rejected, that tests the predicate rather than the observed behavior and would pin an internal. | Drove both fixtures: no marker -> `baseline_layout=None` and zero observations pre-fix (so the assertion passes wrongly); `create_sandbox` from a legacy source -> `baseline_layout='legacy'` and the two spurious kinds present (so the assertion is meaningful). `read_marker` and `create_sandbox`'s `write_marker` call are the mechanism. | yes |
| D-2 | `IPD-Z602` flagged E-05 (PR-503). Split it, or record the advisory as accepted? | SPLIT into E-05 and E-07. | (a) Accept the advisory with a rationale: rejected. The repository's own guidance is explicit that a sizing signal is "an actionable FINDING to investigate by decomposition, never a signal to dismiss because the size lint passed", and here the decomposition is clean along fixture lines rather than forced. (b) Split three ways (table / probe / report): rejected as over-split; the probe test and the report test are both live-behavior checks on the same post-fix module and share a verification shape, so one item with two parts keeps the evidence together without bundling unlike surfaces. | The three parts need a state dict, a real sandbox, and captured stdout respectively. After the split the linter reports `conforming` with no advisory and the E/V bijection stays 7/7. | yes |
| D-3 | Does the new leftover subtraction break any existing pinned row (PR-502)? | NO, and name the two rows with their arithmetic rather than leaving it implicit. | (a) Say nothing, since both rows pass: rejected, "it happens to pass" is not the same as "it is known to pass for a stated reason", and the executor needs the reason to distinguish a regression from an intended silence at V-05. (b) Add defensive test rows duplicating them: rejected, the rows already exist and are already pinned; duplicating them would grow the table without adding coverage. | Drove every existing row's arithmetic: the 5-file row has no `skills` key (`5-0=5`, fires); the legacy-kept row is not migrated (predicate never evaluates); the skills-only row goes to 0 and is INTENDED to fall silent. | yes |
| D-4 | The plan deletes an observation although the codebase says to narrow instead (PR-505). Is that legitimate, and where should it be justified? | LEGITIMATE; restate the justification in the GATE, not only in conventions. | (a) Narrow the predicate instead: rejected on evidence, there is no state in which files under the resolved skills dir are orphaned, since the resolver returns the same path for both layouts and the installer writes there on every run, so a narrowed predicate would have an empty true-positive set and would be dead code pretending to be a check. (b) Leave the justification in the conventions section only: rejected, the approver reads the gate, and a deletion precedent without its limiting condition invites the next plan to delete a genuinely narrowable observation. | Drove `resolve_skills_dir` for both layouts (same path). Backlog `izfscm`'s suggested fix names exactly this option ("Drop the `orphaned-skills` observation, or invert it"), and the inverse is added as `skills-missing`, so the useful half is not lost. | yes |

### Deferred and open

- (none). All five findings were FIXED. Nothing reached Medium-High or High Remediation Risk, so the
  Fix Bar took no deferral. PR-501 is HIGH severity and still `FIXED` rather than escalated: the fix
  was available and bounded (state the fixture requirement, make V-07 prove it), so no
  `- Blocking: yes` question was owed. Worth being precise about what `FIXED` means there: the plan
  now cannot report a vacuous pass as a verified fix, but the guarantee is a VALIDATION REQUIREMENT an
  executor must honor, not a mechanical gate.
- Both pre-existing open questions were already resolved and I verified rather than accepted both.
  OQ-01 (delete vs narrow) is correct on driven resolver evidence. OQ-02 (`skills-missing` must not
  fire on a state that omits `skills_files`) is correct and I confirmed the concrete consequence:
  every existing restored row omits the key, so a presence-insensitive predicate would have broken the
  clean row whose whole purpose is proving a good upgrade is silent.
- No `Reversible: no` decision was made. All four are plan-text or test-design choices on an
  unexecuted plan.
- The release gate is intact and was driven: backlog `izfscm` (`Work-Kind: bug`,
  `Blocks-Release: next`) hands off to this plan through `From-Backlog`, and
  `evaluate_blocking_close` currently REFUSES a `done` close with severity `error` because the carrier
  has not shipped, which is the ordering the plan's gate already states.

HONEST LIMITS, stated because they bound what this round proves. FIRST, I verified the DEFECT and the
plan's diagnosis by driving the real functions, and I checked the new arithmetic against every
existing pinned row; I did NOT write the fix, so the claim that E-03's subtraction is correctly
implemented remains the executor's to demonstrate. SECOND, I did not run the suite: this review
changed no code. I did confirm that `orphaned-skills` appears in exactly two places (the module and
the one restored row), so the blast radius of its deletion is bounded, but a test asserting the string
indirectly could still exist and would surface in E-06's bare run. THIRD, my end-to-end probe used a
minimal legacy source of my own construction rather than the repository's own
`make_source_repo` helper, so it proves the marker/`migrated` mechanism but not that the plan's
eventual fixture will match the file's established conventions. FOURTH, on the deletion question I
established that no true-positive state exists for the CURRENT resolver; if `resolve_skills_dir` ever
became layout-dependent, the deleted observation would become meaningful again, which is a reason the
plan's instruction to read the resolver rather than hardcode the path matters more than the deletion
itself.
