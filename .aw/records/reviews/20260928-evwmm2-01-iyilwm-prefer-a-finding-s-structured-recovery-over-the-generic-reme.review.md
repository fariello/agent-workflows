# Review findings: plan iyilwm

- Subject-Id: iyilwm
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `0d11d122` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: the plan was
committed and unmodified, and its copy under `.aw/state/lane-inputs/rev-1/` is byte-identical to the
tracked file. No production code was modified by this review; every post-change measurement was taken
by rebinding `doctor.build_remediation` from a scratch script or a pytest plugin living OUTSIDE the
tree, with `git status --short` empty throughout.

**THE PLAN'S CORE DIAGNOSIS IS RIGHT AND ITS MEASUREMENT DISCIPLINE IS UNUSUALLY GOOD.** Every one of
its twelve authored findings reproduced at review HEAD. F-01: `rg recovery agent_workflows/doctor.py`
returns exactly one hit and it is a prose comment inside the `setid-collision` branch. F-02: 16
top-level `if` branches followed by an unguarded `return`. F-04: driving all 51 `RULE_REGISTRY` ids
through `build_remediation` yields `51 / 44 / 7` exactly as claimed, with the 7 branch owners being
`check.name-nonconformant`, `check.status-untooled`, `check.setid-collision`,
`check.id6-identity-slot`, `check.blocks-release-dangling`, `check.stale-index-missing` and
`check.stale-index-stale`. F-05 reproduces: `cli._run_check`'s `ce.enrich_drift(d, recovery=fix or "")`
overwrites the engine's value because `enrich_drift` resolves `recovery=recovery or drift.recovery`.
F-06's counts reproduce (34 `recovery=` kwargs, 22 with a literal-initial value, 8 of those containing
`<`), and `check_engine.py` is byte-identical between `4873a82a` and review HEAD so they could not have
drifted. F-08 reproduces: no test, fixture, golden or doc pins the generic string. F-09 reproduces
under a staged wrapper. F-12 reproduces: a `<collisions>` drift causes ZERO `rglob` calls because
`_categorize_drift` early-returns on the sentinel before the guard.

**REVIEW ALSO MEASURED SOMETHING THE PLAN DID NOT, AND IT IS THE STRONGEST EVIDENCE IN THE RECORD.**
Staging E-01's exact preference in memory through a pytest plugin and running the full bare suite
yields `3158 passed, 2 skipped, 3 warnings`, byte-identical in count to the unpatched baseline, with
`test_remediation_family_guard` and `test_resolve_next_actions_advisory_rules_return_no_action` both
green. The change is therefore verified safe against the shipped suite BEFORE approval rather than
after (added as F-21).

**WHAT REVIEW FOUND** is nine findings, none of which touch the code change itself. Three are
consequential: the plan asserts a safety property that does not hold on one of the two surfaces it
governs; its mandatory validation evidence directs the executor to commit a leak, on a witness that
may not exist in the executor's tree; and two of its baselines are stale while a validation item makes
a stale number the bar.

**THE PLAN ASSERTS A CONTAINMENT PROPERTY THAT IS FALSE ON THE `aw check` SURFACE (PR-601, HIGH).**
F-06 and OQ-02 conclude that keeping `command=None` avoids publishing a non-runnable string "in the
slot reserved for a runnable one, including into `resolve_next_actions`". That holds for `aw doctor`,
whose `resolve_next_actions` drops a `None`-command remediation. It is FALSE for `aw check`:
`cli._run_check` collects `_categorize_drift`'s 5th return value (the `detailed_fix`) into `seen_fixes`
and then emits `NextAction(command=f)` for each, so after E-01 a placeholder-bearing recovery lands in
a `command` field there. Measured with the preference staged and a `check.priority-invalid` Drift
carrying `recovery='aw ipd set abc123 --priority <low|medium|high>'`: the value reaching `seen_fixes` is
that exact string with `"<" in fix` True. This is NOT a regression in kind, because that slot already
carries non-runnable prose at review HEAD (`inspect .aw/system/layout.json frontmatter and schema
conformity.` and a 200-character `--slug <corrected-slug>` sentence), so the decision stands on its
red-guard reason. But a plan that overstates its own blast radius teaches the next reader the wrong
invariant, and the overstatement is precisely where an executor would look before deciding whether a
surface needs validating.

**THE MANDATORY V-01(d) EVIDENCE DIRECTED THE EXECUTOR TO COMMIT A LEAK (PR-602, HIGH).**
`check_system_layout` builds its recovery as `"run 'aw install {0}' ...".format(root)` with `root` the
ABSOLUTE repo root, so after E-01 the `Fix:` line for `check.system-layout-missing` contains the full
checkout path. V-01(d) required pasting that line into the plan's `Observed evidence` and said "do not
omit it". Compiling `leak_sanitizer.build_ruleset` against the rendered string fires TWO `fail`-severity
rules, `home-path` and `handle`. Because every `V-*` evidence block is committed, the leak would enter
permanent git history. This is the finding most likely to cause real harm, because the plan's own
emphasis ("the only item of evidence a human can read as the defect being fixed") is what would push an
executor to paste it verbatim.

**THAT SAME WITNESS IS NOT GUARANTEED TO EXIST (PR-603, HIGH).** `check.system-layout-missing` fires
only while `.aw/system/layout.json` is ABSENT, and that file is GENERATED by `aw install` and
GITIGNORED (`.aw/.gitignore` `system/layout.json`, whose comment says it is "regenerated by every
install, and therefore never committed"). Authoring found it because a fresh worktree lacks it, but any
executor whose lane has run an install has no such finding and cannot perform the step the plan calls
mandatory. A deterministic, leak-free alternative needs no fixture: `aw check plans` always emits
`check.collisions-not-checked`, it reaches the fallback, its location is the `<collisions>` sentinel and
its engine recovery is the runnable `aw check all`. Measured: shipped `Fix: inspect <collisions>
frontmatter and schema conformity.` -> staged `Fix: aw check all`.

**TWO BASELINES ARE STALE AND V-01(c) MADE A STALE NUMBER THE BAR (PR-604, MEDIUM).** 102 commits
landed between authoring HEAD `4873a82a` and review HEAD `0d11d122`. Re-measured: the bare suite is
`3158 passed, 2 skipped`, not `3087 passed`; `aw check all` reports 2 findings, not 5. V-01(c) said
"state the delta against `3087 passed, 2 skipped`" and validation item 6 said "baseline: 5 pre-existing
findings", so an executor following the plan literally computes a nonsense delta of +71 plus their own
additions. The repository convention is explicit that a live-artifact count states the required PROPERTY
and re-derives the number; a suite total and a live finding set are both live populations.

**E-01's JUSTIFICATION FOR KEEPING THE GENERIC DEFAULT UNDERSTATES ITS OWN CASE BY ROUGHLY FIFTY-FOLD
(PR-605, MEDIUM).** E-01 said "three shipped producers construct bare 3-argument Drifts". Re-measured by
bracket-matching every `Drift(` call site in `agent_workflows/`: 152 constructions pass no `recovery`
kwarg, across 11 modules (`check_engine.py` 57, `doctor.py` 18, `attention.py` 17, `backlog.py` 13,
`research_index.py` 12, `specs.py` 11, `releases.py` 9, `plans_index.py` 7, `prompts_index.py` 4,
`artifact_core.py` 3, `result_types.py` 1). The conclusion is unchanged and far stronger, which is why
this matters: "three" invites an executor to read the else branch as a rare edge worth simplifying away,
when it is the majority path.

**THE `title` CONSTRAINT THE SCOPE FENCE CALLS LOAD-BEARING IS GUARDED BY NOTHING MECHANICAL
(PR-606, MEDIUM).** The fence forbids changing `title = detail if len(detail) < 60 else rule`, and the
dependency is real: `check_engine.check_collisions` carries a comment recording that it keeps
`check.collisions-not-checked`'s detail under 60 characters ("its generic fallback uses the detail AS
THE TITLE when it is short enough") and its emitted detail is 49 characters. Confirmed live: `aw check
plans` prints `Issue: cross-tree collisions NOT checked by a per-type run`. Yet no test in `tests/`
asserts the fallback's title at all, so the invariant rests entirely on a human reading V-01(a)'s diff.
The repository's anti-regression rule says to name each affected invariant and map it to a test.

**E-03's "16 BRANCH-OWNING RULES" CONFLATES THREE DIFFERENT COUNTS (PR-607, MEDIUM).** Re-measured:
`build_remediation` has 16 `if` BRANCHES; `REPRESENTATIVE_DRIFTS` has 21 ROWS over 19 distinct rule ids,
of which exactly 1 (`check.generic-fallback`) reaches the fallback and 20 hit a branch; and only 7 of
the 51 `RULE_REGISTRY` ids own a branch, because 9 of the 16 branches key on `doctor.*` prefixes that
are not registry rules. E-03's expected outcome named "all 16 branch-owning rules", which matches none
of the three. A test transcribing any of those numbers is a time bomb rather than a guard, and that
defeats the whole point of reusing the table.

**E-01 CHANGES THE `aw doctor` SUMMARY GROUPING AND NO ITEM NAMED IT (PR-608, MEDIUM).**
`render_doctor_report`'s "Summary of issues and proposed fixes" groups on `(rem.title,
rem.summary_fix)`. Today every fallback finding shares the loc-free generic `summary_fix`, so N findings
of one rule collapse into one `<title> (N files)` line. After E-01 a recovery interpolating a path or
id6 differs per finding and the group fragments: measured 1 line before, 4 after, on four synthetic
`check.priority-invalid` findings. The FINDINGS section is unaffected because it groups on
`detailed_fix`, which already interpolates the location. Review accepts the fragmentation as correct
(a per-file fix command genuinely differs per file, so collapsing them was hiding information) and
records it as a Decision, but an unnamed output change on a shipped surface is an executor surprise.

**F-03's OWN EVIDENCE IS NOW ITSELF STALE, WHICH VINDICATES ITS POINT (PR-609, LOW).** F-03 correctly
records that the backlog item's bare offset range landed in the `doctor.setup-needed` branch. At review
HEAD that range still lands inside `setup-needed`'s comment block, so the finding holds; but the actual
fallback has moved again, to `doctor.py:1233`. No action beyond confirming that E-01's
cite-by-content instruction is the right remedy, which it is; recorded so a later reader does not
"correct" F-03 with a fresh offset.

Every finding is FIXED. None was deferred, so no escalation to a `- Blocking: yes` question is owed and
none was written. Both authored open questions remain `resolved` and both survive review: OQ-01 is
upheld unchanged, and OQ-02 is upheld on its red-guard reason with its overstated containment clause
corrected in place per PR-601. Two new Deferred entries record the accepted knock-on effects (the
`aw check` `next_actions` slot, carried by `2cnvh1`; the `aw doctor` summary fragmentation, declined
with a reason).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | IN-SCOPE | A. Correctness / G. Plan executability | plan F-06 and OQ-02 ("including into `resolve_next_actions`"); `cli._run_check`'s `seen_fixes.add(fix)` loop and `for f in seen_fixes: next_actions.append(NextAction(command=f))`; `doctor.resolve_next_actions`'s `if rem.command` filter | THE PLAN ASSERTS A CONTAINMENT PROPERTY THAT IS FALSE ON THE `aw check` SURFACE. `command=None` fences `aw doctor` (a `None` command is dropped) but not `aw check`, whose `next_actions` are built from the `detailed_fix` text collected into `seen_fixes`. Measured with the preference staged: a `check.priority-invalid` Drift carrying `recovery='aw ipd set abc123 --priority <low\|medium\|high>'` puts that exact string, placeholders included, into a `NextAction.command`. Not a regression in kind (that slot already carries non-runnable prose at review HEAD), but the plan must not claim a property it lacks, and this is the paragraph an executor reads before deciding whether a surface needs validating. | C:Low; U:Low; S:Low; F:Low; Overall:Low (correct two prose claims and add one observation step; no code change) | FIXED | Added F-14 with both measurements. F-06 carries an explicit scope correction; OQ-02 revised in place, upheld on the red-guard reason with the false clause named and retracted. E-01 gained a "DO NOT BELIEVE `command=None` CONFINES THE CHANGE" paragraph; E-04 must name it in the comment; new validation item 7 and V-01(e) require observing it; new Deferred entry carried by `2cnvh1`; gate paragraph states it as something a human is approving. |
| PR-602 | HIGH | IN-SCOPE | B. Security and privacy / E. Testing | `check_system_layout`'s `recovery = "run 'aw install {0}' ...".format(root)`; the staged `aw check all` run printing the absolute checkout path in `Fix:` and `Next`; `leak_sanitizer.build_ruleset(cwd, include_warn=False)` matching that string -> `FAIL rule fires: home-path`, `FAIL rule fires: handle` | THE MANDATORY V-01(d) EVIDENCE DIRECTED THE EXECUTOR TO COMMIT A LEAK. After E-01 the `Fix:` line for `check.system-layout-missing` contains the ABSOLUTE repo root, and V-01(d) required pasting it into a committed `Observed evidence` block while saying "do not omit it". Two `fail`-severity sanitizer rules fire on the rendered string. Because the evidence block is committed, the leak becomes permanent git history. The plan's own emphasis on this step is what makes it likely to be pasted verbatim. | C:Low; U:Low; S:Low; F:Low; Overall:Low (swap the witness and add a redaction rule) | FIXED | Added F-19 with the sanitizer probe. V-01(d) now names the leak-free `check.collisions-not-checked` witness as primary and permits `system-layout-missing` only with the root redacted to `<repo-root>`. Added a LEAK RULE to Required tests and a "DO NOT PASTE AN ABSOLUTE CHECKOUT PATH" paragraph to the gate. V-01(f) now requires `aw sanitize --agent` clean, since (d) and (e) paste rendered CLI output into a committed artifact. |
| PR-603 | HIGH | IN-SCOPE | E. Testing and verification | `git check-ignore -v .aw/system/layout.json` -> `.aw/.gitignore:33:system/layout.json`; that file's comment ("regenerated by every install, and therefore never committed"); `ls .aw/system/layout.json` absent at review HEAD; `aw check plans` emitting `check.collisions-not-checked` unconditionally | THE PLAN'S ONLY END-TO-END WITNESS IS NOT GUARANTEED TO EXIST IN THE EXECUTOR'S TREE. `check.system-layout-missing` fires only while the GENERATED, GITIGNORED `.aw/system/layout.json` is absent, so an executor whose lane has run `aw install` cannot perform the step the plan calls mandatory and has no stated fallback. A deterministic alternative needs no fixture: `aw check plans` always emits `check.collisions-not-checked`, which reaches the fallback and whose engine recovery is the runnable `aw check all`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-20 with the before/after measurement on the alternative witness (`inspect <collisions> ...` -> `aw check all`) and the gitignore evidence. Validation item 5 and V-01(d) now name `check.collisions-not-checked` as the required witness and explain why, retaining `system-layout-missing` as an optional extra. |
| PR-604 | MEDIUM | IN-SCOPE | G. Plan executability (live-artifact convention) | plan F-07 (`3087 passed`) and validation item 6 ("baseline: 5 pre-existing findings"); bare `python3 -m pytest` at `0d11d122` -> `3158 passed, 2 skipped, 3 warnings in 45.52s`; `aw check all --json` -> `policy_findings: 2`; `git log --oneline 4873a82a..HEAD \| wc -l` -> `102` | TWO BASELINES ARE STALE AND A VALIDATION ITEM MADE A STALE NUMBER THE BAR. V-01(c) required the delta be stated against `3087 passed, 2 skipped`, which is 71 tests behind review HEAD, and item 6 named 5 pre-existing findings where there are now 2. Both are live populations, and the repository convention requires a criterion counting live artifacts to state the PROPERTY and re-derive the number at execution time. An executor following the text literally computes a meaningless delta. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-18 with all three re-measurements. F-07 and F-05 relabelled: their digits are authoring/review CONTEXT, the property is the bar. Required tests lead with "RE-DERIVE YOUR OWN BEFORE-BASELINE; DO NOT TRANSCRIBE THE DIGITS BELOW"; V-01(b)(c) and item 6 require re-derivation; the Step-0 conventions bullet carries both measurements and the re-derive instruction. |
| PR-605 | MEDIUM | IN-SCOPE | A. Correctness (evidence accuracy) | plan E-01 ("three shipped producers construct bare 3-argument Drifts"); scratch bracket-matching scan over `agent_workflows/**/*.py` counting 152 `Drift(` calls with no `recovery` kwarg, with the per-module breakdown | E-01's JUSTIFICATION FOR KEEPING THE GENERIC DEFAULT UNDERSTATES ITSELF BY ROUGHLY FIFTY-FOLD. 152 shipped `Drift` constructions across 11 modules pass no `recovery`, not three. The conclusion is unchanged and much stronger, which is exactly why the wrong number is worth fixing: "three producers" reads as a rare edge case an executor might simplify away, and deleting the else branch would break the majority path. V-01(a) also cited the wrong figure as its reason for failing a diff that deletes the default. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-13 with the count and per-module breakdown. E-01's paragraph now reads "the OVERWHELMING MAJORITY ... 152 across the package, 57 of them in `check_engine.py` alone" and states that deleting the default breaks the common case. V-01(a) and Proposed change 1 cite the corrected figure. |
| PR-606 | MEDIUM | UNDER-SCOPE | D. Anti-regression and domain invariants | `check_engine.check_collisions`' comment ("The DETAIL is kept under 60 characters deliberately ... its generic fallback uses the detail AS THE TITLE when it is short enough"); its 49-character detail; `aw check plans` printing `Issue: cross-tree collisions NOT checked by a per-type run`; `rg` over `tests/` finding no assertion on a fallback title | THE `title` CONSTRAINT THE SCOPE FENCE CALLS LOAD-BEARING IS GUARDED BY NOTHING MECHANICAL. The dependency is real and documented in `check_engine.py`, and the fence forbids touching `title = detail if len(detail) < 60 else rule`; but no test asserts the fallback's title, so the invariant rests on a human reading V-01(a)'s diff. E-01 edits the very `return` statement that computes it. The repository's anti-regression rule requires each affected invariant be mapped to a test, and the test is one assertion away. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-15 with the comment, the live title output and the absence of coverage. E-02 gained assertion (d) pinning `title` as identical across the recovery and empty-recovery cases, with a paragraph explaining it is the only machine guard on the fence. V-02(d) requires quoting that assertion. Scope check records the change from inspection-only to mechanical. |
| PR-607 | MEDIUM | IN-SCOPE | G. Plan executability (live-artifact convention) | plan E-03 and V-03(b) ("all 16 branch-owning rules", "21 rows covering 16 branches"); `awk` over the function counting 16 `^    if ` lines; import of `REPRESENTATIVE_DRIFTS` printing `rows: 21`, `distinct rules: 19`, `rows hitting the generic fallback: 1 ['check.generic-fallback']`; the `RULE_REGISTRY` sweep printing `51 / 44 / 7` | E-03's "16 BRANCH-OWNING RULES" CONFLATES THREE COUNTS AND MATCHES NONE OF THEM. There are 16 `if` branches, 21 table rows over 19 distinct ids (20 branch rows and 1 fallback row), and 7 registry ids with a branch, because 9 branches key on `doctor.*` prefixes that are not registry rules. A test asserting a transcribed count is a time bomb that breaks when a branch or row is added, which defeats the reuse E-03 exists for. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-16 naming all four measurements and the 7 branch-owning registry ids. E-03 gained a "COUNT BY ROW, NOT BY RULE, AND RE-DERIVE THE PARTITION" paragraph requiring the partition be computed at run time on the generic-string comparison; its Expected outcome no longer names a number. V-03(b) requires re-derivation and forbids hard-coding any of the four figures. |
| PR-608 | MEDIUM | IN-SCOPE | C. Architecture and operability / F. UX | `doctor.render_doctor_report`'s summary grouping `key = (rem.title, rem.summary_fix)` versus the findings grouping `key = (title, fix)` on `detailed_fix`; scratch probe over four enriched `check.priority-invalid` Drifts reproducing the summary grouping -> `SHIPPED lines: 1` / `PATCHED lines: 4` | E-01 CHANGES THE `aw doctor` SUMMARY GROUPING AND NO PLAN ITEM NAMED IT. Fallback findings currently share a loc-free `summary_fix` and collapse into one `<title> (N files)` line; after E-01 a recovery interpolating a path or id6 fragments the group into one line per finding. The findings section is unaffected. Review judges the fragmentation CORRECT rather than defective (a per-file fix command genuinely differs per file), but an unnamed output change on a shipped surface is an executor surprise, and the alternatives are both worse: keeping `summary_fix` generic leaves `aw doctor`'s summary showing the string this plan exists to remove, and changing the renderer is outside `- Scope-Paths:`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-17 with the 1 -> 4 measurement and the reason the findings section is unaffected. New Deferred entry accepting it with a `Carrier-Declined` reason; E-04 must name it in the comment; validation item 7 and V-01(e) require a before/after paste with an instruction to stop and report anything F-14/F-17 do not describe; recorded in Scope check under-scope and in the gate's approval paragraph. |
| PR-609 | LOW | IN-SCOPE | G. Plan executability (citation convention) | plan F-03; read of the item's cited range at review HEAD still landing in the `doctor.setup-needed` branch; `grep -n 'title = detail if len(detail) < 60 else rule'` -> `agent_workflows/doctor.py:1233` | F-03's OWN EVIDENCE HAS ITSELF DRIFTED, WHICH VINDICATES ITS POINT RATHER THAN WEAKENING IT. The finding correctly records that the backlog item's bare offset landed in an unrelated branch, and that still holds; but the actual fallback has since moved to line 1233, so any offset-based anchor in this area expires within weeks. Recorded so a later reader does not "correct" F-03 by substituting a fresh offset, which is the failure mode backlog `88manw` documents for review findings that reject a citation they merely failed to re-locate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | No change to F-03, which is accurate. E-01's cite-by-content instruction is confirmed as the correct remedy and was left exactly as authored; this row is the record that the drift was re-checked rather than assumed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `command=None` does not fence the `aw check` `next_actions` slot (PR-601). Does E-01 need to change, or is the prose the only defect? | THE PROSE ONLY. Keep E-01 exactly as specified, correct F-06 and OQ-02 in place, and add an observation step so the effect is seen rather than discovered. | (a) Narrow E-01 to `detailed_fix` and leave `summary_fix` generic - rejected: `aw doctor`'s summary reads `summary_fix`, so that leaves the useless string on the surface this plan exists to fix, and it splits one field's meaning across two renderers. (b) Fix `cli._run_check` in the same pass - rejected: `cli.py` is outside `- Scope-Paths:`, the residue is already carried by `2cnvh1`, and the fix requires deciding what `next_actions` should contain, which is a contract question. (c) Say nothing - rejected: the false clause is in the paragraph an executor reads before judging whether a surface needs validating. | `cli._run_check`'s `seen_fixes` -> `NextAction(command=f)` loop; the measured `"<" in fix` True under the staged preference; review-HEAD `aw check all --json` already carrying non-runnable prose in the same slot, so E-01 changes which prose and does not introduce the defect. | yes |
| D-2 | The `aw doctor` summary grouping fragments (PR-608). Preserve the collapse, or accept the fragmentation? | ACCEPT IT, as correct-if-noisier, and record it so it is not a surprise. | (a) Keep `summary_fix` generic and change only `detailed_fix` - rejected: leaves `aw doctor`'s summary printing the string the plan exists to remove, for no gain a reader would value. (b) Change the renderer to group on rule id instead - rejected: `doctor.render_doctor_report` is a shipped output surface, the change is not in `- Scope-Paths:`, and it would collapse genuinely different fix commands under one line, which is the information loss that makes the current behavior wrong. (c) File a carrier - rejected: there is no residual defect to carry; asserting one would claim the collapsed output was correct. | The two grouping keys read directly (`(rem.title, rem.summary_fix)` at the summary, `(title, fix)` on `detailed_fix` at the findings section); the measured 1 -> 4 fragmentation; the backlog item's own framing that the human is the audience least able to derive the fix. | yes |
| D-3 | V-01(d)'s witness leaks and may not exist (PR-602, PR-603). Swap the witness, drop the requirement, or ask the maintainer? | SWAP IT to `check.collisions-not-checked` and add a redaction rule, keeping the requirement mandatory. | (a) Drop the end-to-end requirement - rejected: it is the only evidence a human can read as the defect being fixed, and the plan is right to insist on it. (b) Keep `system-layout-missing` and just add a redaction instruction - rejected: redaction fixes the leak but not the existence problem; an executor whose lane ran `aw install` still has no finding to paste. (c) Build a fixture repo - rejected: unnecessary, since a guaranteed in-tree witness exists and needs no setup. (d) Ask the maintainer - rejected: the repository answers it by running one command. | `git check-ignore -v .aw/system/layout.json`; the sanitizer firing `home-path` and `handle` on the rendered string; `aw check plans` emitting `check.collisions-not-checked` unconditionally at review HEAD, with its recovery `aw check all` and its `<collisions>` sentinel location carrying nothing interpolated. | yes |
| D-4 | Should review mark this plan NO-GO for the HIGH findings PR-601..PR-603? | NO. All three were FIXED by in-place revision, so no unfixed HIGH remains and the correct readiness is `go-pending-approval`. | (a) NO-GO on severity - rejected: the workflow is explicit that severity is for reporting and the Fix Bar alone decides fixing; all three fixes are Low Remediation Risk prose-and-evidence edits touching no code. (b) Escalate one as a `- Blocking: yes` question - rejected: escalation is owed only for a finding left OPEN or DEFERRED at or above the gate threshold, and none was left unfixed. | The `plan-review` Fix Bar and the readiness vocabulary (a clean reviewed plan awaiting sign-off is `GO - PENDING HUMAN APPROVAL`, never a bare NO-GO); `aw ipd lint --phase review-finalize --agent` conforming after revision; `review_findings_gate` unset in `.aw/config/project.json`, so the default `HIGH` threshold applies and no finding sits at it. | yes |
