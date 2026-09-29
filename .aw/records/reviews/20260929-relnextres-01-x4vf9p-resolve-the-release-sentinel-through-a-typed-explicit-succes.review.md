# Review findings: plan x4vf9p

- Subject-Id: x4vf9p
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `364bacfe` in a lane worktree. Structural preflight `aw ipd lint --phase author`
reported `clean` with one ADVISORY, `IPD-Z602` on E-08, which E-08 itself anticipates and argues
against in its own text; `--phase review-finalize` reports the same single advisory and no errors after
the revision edits. No pre-review snapshot was owed: the plan was committed and unmodified
(`git status --porcelain` empty) and the lane-input copy under `.aw/state/lane-inputs/rev-28/` is
byte-identical. Bare suite at review HEAD: `3246 passed, 2 skipped, 3 warnings in 47.60s`. The scoped
surface is green: `tests/test_check_engine_release_gate.py tests/test_releases.py tests/test_doctor.py`
-> `83 passed in 2.68s`, matching F-12 exactly. NO PRODUCTION FILE OR TEST WAS MODIFIED by this review;
every measurement ran against a throwaway copy of `.aw/records` under the gitignored `tmp/` scratch,
never against the tracked tree, and the live tree still reports `check release-gates` exit 0 / 0 findings.

THIS IS AN UNUSUALLY WELL MEASURED PLAN AND EVERY ONE OF ITS THIRTEEN FINDINGS REPRODUCES. I rebuilt the
four-state experiment independently and got the same four outcomes: baseline (one planned) exit 0 / 0
findings; ship-only exit 1 with every finding `check.blocks-release-dangling`; a second planned record
added exit 1 with the same count, confirming absent and ambiguous are indistinguishable today; ship plus
successor exit 0 / 0. F-03 is verbatim, including `return planned[0] if len(planned) == 1 else None` and
the docstring's own admission. F-04 is exact (`RuleSpec("error", ASSURANCE_REPOSITORY,
DET_DETERMINISTIC, "I-07")`, five family members, and a CI step with no `continue-on-error` whose comment
already names carrier `cnn7au`). F-05's fail-safe precedent exists verbatim at the quoted comment. F-06,
the finding that justifies half the plan, reproduces exactly and is the sharpest thing in the document: a
bare `set shipped f33nrj` with NO `--apply` printed one preview-shaped line, exited 0, and the record read
`shipped` on disk, while `--apply` is genuinely rejected as an unrecognized argument, so there is no
preview-then-apply gap to hook. F-08 reproduces down to the same offending file (`5m43v9`), with the
remediation instructing `--blocks-release next` on a record whose field already reads `next`. F-09
reproduces end to end: a bug filed in the zero-planned state got NO gate line and then tripped
`check.live-bug-ungated`, so the sentinel reddens `main` through two independent error rules. F-10 (zero
workflow files mention release records), F-11 (the five-element equality census), F-12 and F-13 (eleven
call sites) all hold.

I ALSO VERIFIED THE PROPOSED DESIGN RATHER THAN ONLY THE DIAGNOSIS, because E-02 edits an error rule
inside a fail-closed family and the plan's own gate says that is the dangerous part. On a ship-only
scratch tree carrying one deliberately planted `- Blocks-Release: nonexist` record, today's code emits 776
`check.blocks-release-dangling` findings of which exactly 775 carry the `'next'` detail and exactly 1
carries the `'nonexist'` detail. So E-02's narrow suppression has a precise, checkable target: 2 findings
after the fix, not 1 and not 776. I also confirmed a concrete id6 still resolves in the AMBIGUOUS state,
which is what makes the narrow suppression safe, and that `get_release_blockers` reads `resolve_release`
and is therefore untouched by E-02. That arithmetic is now written into E-02 as a measured acceptance
criterion, which is the single most useful thing this review added, because it converts "do not
over-suppress" from an instruction into a number the executor can check.

Three real defects came out of driving the plan rather than reading it. Its E-05 needs `cli.py` to declare
a new flag and left that path conditional and undeclared. Its central count has now drifted twice (608 ->
697 -> 775 in about two hours) while two items still quote a literal. And E-06 turns out to be REQUIRED
rather than cosmetic: I measured that both new rule names fall through `doctor`'s substring match to a
generic fallback that is worse than the no-op it replaces. All three are fixed in place.

Both open questions are correctly non-blocking and I verified their premises rather than accepting them:
`pqsx96` is genuinely `- Status: draft` and its I-07 row is genuinely an incomplete enumeration of the
shipped family, so OQ-01's "this plan does not make it more wrong" is accurate; and F-09's measured
behavior supports OQ-02's recommendation of no change.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | UNDER-SCOPE | G. Executability (undeclared required path) | plan E-05 "Wire it through `agent_workflows/cli.py`'s `set` parser only if that is where the flag must be declared"; `--by-human` at `agent_workflows/cli.py:1590`, `--allow-open-questions` at `:1597`, `--allow-terminal-reopen` at `:1608` and `:4246` | **E-05's NEW FLAG CANNOT BE DECLARED WITHOUT `cli.py`, AND `cli.py` WAS NOT IN `Scope-Paths`.** The item made the path conditional on a question that has a definite answer: every existing `aw set` flag is added to the parser in `cli.py`, and `status_set` receives flags only through the already-parsed `args` namespace, so there is no route that adds a user-facing flag without touching `cli.py`. Leaving it conditional and undeclared invited either an undeclared commit or a mid-execution `Scope-Paths` amendment, which is exactly what the finalize scope gate refuses. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `agent_workflows/cli.py` ADDED to `- Scope-Paths:` at review so the executor finds it already declared. E-05 rewritten to state the path is required, with the measured flag-declaration sites cited, and to warn that `aw set` and `aw ipd set` build separate parser blocks so the executor must check which spellings reach the releases path rather than assuming one site. |
| PR-302 | MEDIUM | IN-SCOPE | Live-artifact counts vs stable facts | plan Concern, F-02, F-08, E-04, Deferred and conventions all quoting literals; item 608, authoring 697, review 775 | **THE CENTRAL COUNT IS A LIVE, MONOTONICALLY GROWING POPULATION THAT HAS NOW DRIFTED TWICE IN HOURS, AND TWO ITEMS STILL ASKED FOR A LITERAL.** The backlog item said 608, authoring measured 697, review measured 775 at a HEAD about two hours later. The plan already corrected the item's figure once and then froze its own, which is the same mistake one generation on. The specific risk is in E-04, whose refusal message must name "the count of records that would dangle": an executor could reasonably hardcode 697, or write a test asserting it, and both are stale before the plan executes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 rewritten to record all three measurements, to state that the figure is a live population no `E-*` or `V-*` may assert, and to name the SHAPE (one finding per gated record) as the invariant that actually held at all three measurements. The Concern, F-01, F-08, the conventions census and the Deferred entry all de-literalized while keeping the ratio (~99.7 percent sentinel-valued), which is the stable and load-bearing fact. E-04 gains an explicit instruction to compute the count at runtime and to assert against a fixture's own known number, never the live tree's. |
| PR-303 | MEDIUM | IN-SCOPE | C. Architecture (new rules get no remediation); F. Prevent silent failure | `agent_workflows/doctor.py:1067` (`if "blocks-release-dangling" in rule`); measured `build_remediation` on a `check.release-sentinel-absent` Drift -> `inspect artifact frontmatter and schema conformity.` | **E-06 IS REQUIRED, NOT COSMETIC, AND THE PLAN UNDERSTATED IT.** The existing branch matches by SUBSTRING, and neither new rule name contains `blocks-release-dangling`, so without E-06 both new rules fall through to `doctor`'s generic default. Measured at review, that default returns `inspect artifact frontmatter and schema conformity.`, which is WORSE than the no-op F-08 complains about because it does not even name the releases tree. The plan presented E-06 as correcting a no-op; it is also preventing a regression in which the new, more accurate finding arrives with less actionable advice than the inaccurate one it replaces. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 gains the measurement and two constraints: ADD DISTINCT BRANCHES rather than widening the existing substring test (a broadened match on `release` would swallow unrelated rules), and do not force the three-way `art_type` shape onto the new rules, whose location is the releases DIRECTORY rather than a typed record. |
| PR-304 | MEDIUM | IN-SCOPE | E. Testing (unverifiable acceptance criterion) | plan E-02 Expected outcome "returns exactly ONE finding"; measured 776 findings on a ship-only tree carrying one `nonexist` record, splitting 775 `'next'` + 1 `'nonexist'` | **E-02's ACCEPTANCE CRITERION WAS AMBIGUOUS IN THE ONE DIRECTION THAT MATTERS.** "Exactly ONE finding" is true only on a tree where every unresolvable value is the sentinel. On any tree that ALSO carries a genuinely dangling id6 or version, the correct answer is one sentinel finding PLUS one per-record finding for each such value, and the plan's own negative fence demands exactly that. As written, an executor testing on a mixed tree and seeing 2 findings could believe they had failed the criterion and then over-suppress to reach 1, which is precisely the gutting of an error rule the plan's gate forbids. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02's Expected outcome restated to name both components, and given the arithmetic MEASURED at review on a real scratch tree: 776 findings today (775 suppressible + 1 that must survive) becomes 2 after the fix, still exit 1, with an explicit reading that 1 means over-suppression and 776 means the suppression never fired. Also notes the separate `check.live-bug-ungated` finding present in that state is not part of the arithmetic, so it is not mistaken for a miscount. |
| PR-305 | LOW | IN-SCOPE | Evidence accuracy (measurement provenance) | plan F-01 and Concern citing only HEAD `ebd2da31` | **NO FINDING RECORDED AN INDEPENDENT RE-REPRODUCTION, so a reader could not tell whether the four-state experiment was ever repeated.** For a plan whose whole case rests on one experiment against a tree that demonstrably changes underneath it, that matters: the drift in PR-302 is itself evidence that a single-HEAD measurement ages. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-01 now records that review re-drove all four states in its own scratch copy at HEAD `364bacfe` and got the same four outcomes, with only the count differing, and points at F-02 for why. The Concern carries the same re-measurement note. This is a provenance improvement rather than a correction: nothing in the original claim was wrong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-08 trips the advisory `IPD-Z602` (action text bundles multiple concerns) and argues it should stay one item. Accept, or split it? | ACCEPT the plan's reasoning and leave E-08 as one item. | (a) Split by file into three items: REJECTED, the plan's own argument is correct that three near-identical actions whose main risk is divergence is worse than one, and a partial execution would leave the obligation in reference prose but missing from the checklist that actually cuts the release, which is the specific gap F-10 measured. (b) Split by audience (reference prose versus executable step): CONSIDERED and not imposed; the plan itself names this as the honest split if a reviewer disagrees, and I do not, so forcing it would add an item boundary for no measured benefit. | Verified F-10 independently: `grep -rln 'aw releases\|\.release\.md\|release record' .aw/system/workflows/` matches ZERO files, and `09-release-execution.md` (159 lines) never mentions a release record. So the three edits must agree with one another to be correct, which is the definition of one concern. `IPD-Z602` is ADVISORY, and the plan pre-argued it in the item text rather than ignoring it. | yes |
| D-2 | Should this review resolve OQ-01 (amend the draft spec `pqsx96`'s I-07 row) instead of leaving it to the maintainer? | Leave it OPEN and non-blocking, as authored. | Resolving it toward amending: REJECTED, editing a spec that is itself `draft` and still being authored risks colliding with its author, and the plan deliberately keeps the file out of `Scope-Paths`. Resolving it toward never amending: REJECTED, that is a judgement about another author's spec that neither the plan nor this review owns. | Verified both premises: the spec is `- Status: draft`, and its I-07 row names `check.blocking-item-closed-without-gate`, `check.from-backlog-gate-mismatch` and `check.orphaned-live-blocker` while omitting `check.blocks-release-dangling` and `check.from-backlog-dangling`, so it is already incomplete with respect to the shipped family and two more rules do not newly falsify it. The plan's reasoning is accurate and the question is genuinely the maintainer's. | yes |
| D-3 | F-09's second-order ungating (OQ-02) is measured and unfixed. Should this review require it be fixed here? | No. Endorse the plan's deferral with its recommendation of no change. | Requiring the fix here: REJECTED, it touches the creation path of every backlog item and would trade one error rule for another (writing a gate that points at nothing). Requiring a filed item now: REJECTED, the plan already records it as OQ-02 with an owner, and E-04 closes the tooled route that makes the state reachable. | Reproduced F-09 exactly: a bug filed in the zero-planned state got no `- Blocks-Release:` line and then produced one `check.live-bug-ungated` finding. That confirms the behavior AND confirms the plan's reasoning that the current behavior is defensible, since the alternative writes a gate at an unresolvable target. | yes |
| D-4 | E-02 changes attribution on an error rule in a fail-closed family. Is the narrow suppression actually safe, or should the review demand a different mechanism? | SAFE as specified; keep the mechanism and pin it with the measured arithmetic. | (a) Demand the fail-safe posture of `check_graduated_to` (report nothing on an empty corpus): REJECTED, and the plan already rejects it for the right reason, since reporting nothing would make a real release-cycle error silent and weaken I-07. (b) Demand the suppression be dropped and only the new rules added: REJECTED, that leaves the 775 inaccurate findings in place and fixes nothing. | Measured that a concrete id6 STILL resolves in the ambiguous state, so a non-`next` value is always distinguishable from the sentinel case; measured the exact split (775 `'next'` + 1 `'nonexist'`) that makes the narrow condition checkable; and confirmed `get_release_blockers` consumes `resolve_release` and so is untouched by E-02. The plan's two-condition guard (value is literally `next` AND the probe returned non-resolved) is exactly the right predicate. | yes |
