# Review findings: plan nrqo90

- Subject-Id: nrqo90
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated lane worktree at HEAD `74e672a2`. Structural preflight `aw ipd lint --phase
author --agent` CONFORMED (exit 0) before revision, and `--phase review-finalize --detail` conforms
after. No pre-review snapshot was needed: `git status --short` was empty, so the plan was committed
and unmodified. Suite baseline re-measured before touching anything: `2584 passed, 2 skipped, 3
warnings in 87.75s`.

THE PLAN'S DIAGNOSIS IS ACCURATE AND I RE-MEASURED EVERY CLAIM RATHER THAN ACCEPTING IT. F-1 holds
exactly: `releases.render_release` really does call `_core.mint_id6` and build
`f"{today}-{id6}-01-{id6}-{slug}.release.md"`, and the single tracked roadmap is clustered, so the
backlog's three-holdout framing is genuinely stale for two of three. F-2 holds: 24 walkthroughs, 11
legacy `YYYYMMDD-HHMM-NN-` names, 13 clustered. F-4 holds and matters: `write_walkthrough` takes a
caller-supplied `id6`, `promote_local_checkpoints` passes its own, and `git grep` finds no caller
outside `set_records.py`, so the signature change is safe. F-5 and F-6 hold verbatim, including the
shipped template's stale `YYYYMMDD-HHMM-NN-<slug>-walkthrough.md` line. The cutover mechanism the
plan proposes to copy works: I drove `check_names` against a simulated `walkthrough_id6` boundary and
a post-cutover legacy name yields one `check.name-nonconformant` while a pre-cutover one yields none,
and `aw rename walkthroughs <legacy> --to-id6` really does convert both legacy shapes and really is a
no-op on an already-clustered name, exactly as E-05 assumes.

**THE PLAN'S CENTRAL PROOF IS SATISFIED BY DOING HALF THE WORK, AND THAT IS THE FINDING THAT
JUSTIFIES THIS REVIEW.** E-09 (authored E-08) offered "ZERO `check.id6-identity-slot` findings" as the
evidence that the three D140 walkthroughs were repaired. I drove `_check_identity_slots` directly on
the post-rename record shape and it returns `[]` for a walkthrough that was RENAMED to a fresh id6 and
declares NO `- Id:` of its own. The reason is structural, not incidental: rule (a) only fires for a
file that DECLARES an Id, and rule (b) fires only when the slot id6 is owned by someone else, so a
freshly minted id6 that nobody declares satisfies neither branch. A rename alone therefore clears the
rule while leaving unmet the thing D140 and the walkthroughs README actually require, which the README
states as "a walkthrough MUST mint its own id6 there". The plan asked for the `- Id:` bullets in E-05
and in V-05's evidence list, but no assertion anywhere could FAIL if they were forgotten, and V-05 is a
paste-what-you-did item rather than a check. That is exactly the shape this repository has ruled
against before. I added E-06 as a real outcome test over the tracked tree, keyed on
`check_engine._identity_declared_values` so the test and the checker agree on what "declared in the
metadata region" means, and V-06 requires a three-run sequence including a deliberate bullet deletion
showing the test go RED.

**AND ONE ASSERTION WOULD HAVE FAILED ON A CORRECT OUTCOME.** E-09 asserted `aw find zpbx7o` (and
`y5od1h`, `4fodkt`) "returns only the plan". I ran all three. `zpbx7o` returns the plan and the
walkthrough. `y5od1h` and `4fodkt` return the plan, the walkthrough AND a same-named REVIEW record
under `.aw/records/reviews/`, because a review record is deliberately named after the plan it reviews
and legitimately shares that id6 handle. So after a correct fix, two of the three commands will still
return two artifacts, and an executor holding the authored assertion would either report a false
failure or, worse, "fix" it by renaming a review record. The honest assertion is that no WALKTHROUGH
appears and that the D140 collision warning `aw find` currently prints is gone, which is what E-09 now
says.

**THE CITATION CENSUS NAMED FIVE OF EIGHT FILES, AND ONE OMISSION WAS DANGEROUS.** E-07 (authored
E-06) instructed the executor to preview with `artifact_refs.plan_reference_rewrites` and classify each
hit, listing three REWRITE targets and two KEEP targets. I drove the preview: 36 edits across EIGHT
files. The three unlisted ones are executed plan `20260925-carrierauth-01-vtkfq8-...` (6 hits, a fenced
driven-evaluation transcript plus an embedded `aw check --agent` JSON payload) and this plan itself (6
hits, its own authored evidence). `vtkfq8` is the same recorded-transcript KEEP class as `t0jyb2`,
which the plan did name, so the omission is an incomplete sweep rather than a policy disagreement; but
because `plan_reference_rewrites` has no per-file exclusion, an executor who previewed and then called
`apply_reference_rewrites` on the returned list would have rewritten two recorded transcripts. E-07 now
names all eight, forbids the wholesale apply, and says to filter to the three documented plans. I also
checked the `y5od1h` facet fix, which changes the stem and so emits a `bare-stem` edit beside the
`full-name` one; `apply_reference_rewrites` sorts full-name first, so the pair composes correctly (I
drove it), but a hand edit must handle both forms, which E-07 now states.

TWO MEASUREMENT CORRECTIONS THAT WOULD HAVE MADE HONEST VALIDATION IMPOSSIBLE. V-09 (authored V-08)
told the executor to "compare the rule list to HEAD's 9 findings". HEAD has FIVE: the 3
`check.id6-identity-slot` plus one `check.scope-drift` and one `check.system-layout-missing`, both
pre-existing and unrelated. An executor comparing against 9 could not have produced a coherent
before/after, and might have read the two survivors as regressions. Separately, F-3 asserted that
`e2j5w4`'s detection defect "is already fixed (t0jyb2)". The CODE is fixed (I confirmed
`check_collisions(repo)` returns the 3 slot findings with default arguments, which is precisely what
`e2j5w4` reported as broken), but the ITEM is still `- Status: open`. Both halves are now stated, along
with the fact that this plan neither closes nor is blocked by it.

ON E-03's CUTOVER RATIONALE, which was reasoning from the wrong quantity and reaching the right
answer. The plan justified its registry value as needing to be "strictly after the newest tracked
walkthrough date (`20260918`) so every existing walkthrough stays grandfathered". `KNOWN_FEATURE_CUTOVERS`
does not hold a boundary; its own block comment spends twenty lines saying so ("DATE 1 IS THE INPUT TO A
SEARCH, NOT THE BOUNDARY"), and the live proof is that `spec_id6`'s dict value is `2026-08-28` while
this repo's resolved boundary is `20260829`. The enforcement boundary is stamped per-repository by
`sync_cutovers_on_install`, from an `installs.jsonl` search that falls back to the install date. I
simulated the registration: on a fresh repo the boundary stamps to the install date, and a repo
installing in November gets a November boundary from the identical intro date. The grandfathering
conclusion is correct HERE (this repo has no `installs.jsonl`, so the boundary resolves to the install
date, later than `20260918`), but it was asserted from a false premise, so V-03 now MEASURES the
resolved boundary and the zero-nonconformant count rather than inferring them, and carries a stop
condition if the boundary lands early.

ON THE ONE JUDGEMENT I DID NOT MAKE ALONE. This plan renames three tracked records under
`.aw/records/`, and backlog `mw0s1y` says in capitals "DO NOT RENAME THESE RECORDS WITHOUT A MAINTAINER
DECISION". OQ-01 treats the brief's instruction ("re-id the 3 D140 walkthroughs") as that decision, and
I accepted that reading: the instruction is specific, it matches exactly what `mw0s1y` asks for, and
`mw0s1y`'s own text names re-identification as the remedy. I surfaced it in the gate rather than
blocking, because the plan is executable and correct as revised and the alternative is a maintainer
preference rather than a correctness question.

ON SCOPE, which I checked rather than assumed. `.aw/records/walkthroughs/README.md` is edited by E-08
and is covered by the directory entry `.aw/records/walkthroughs/`, since `ipd_lifecycle._scope_match`
treats a trailing-slash entry as directory-bounded; I confirmed that in the matcher rather than
trusting the shape. `vtkfq8` is deliberately NOT added to the fence, because E-07 leaves it
byte-identical. And I explicitly recorded that no edit is made to `_check_identity_slots` or
`_is_real_id6`: F-7 is a documented property of that rule whose docstring warns "DO NOT 'fix' this by
adding a declared-duplicate case here", so the right response is the new test, not a widened rule.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | UNDER-SCOPE | E. testing; D. anti-regression | `_check_identity_slots([(plan,'zpbx7o','zpbx7o'), (wt,None,'aaa111')])` -> `[]`; `_is_real_id6('aaa111', {'zpbx7o'})` -> `True`; rule (a) requires a declared Id, rule (b) requires another owner | **THE PLAN'S CENTRAL PROOF IS SATISFIED BY RENAMING ALONE.** A walkthrough renamed to a fresh id6 but declaring no `- Id:` yields zero `check.id6-identity-slot`, so the `- Id:` half of E-05 (what D140 rule (a) and the README require) had NO assertion that could fail. V-05 asks the executor to paste the bullets, which is self-report, not verification. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New E-06: an outcome test over the tracked tree asserting every clustered walkthrough declares a `- Id:` equal to its slot, read via `check_engine._identity_declared_values` so test and checker agree. V-06 requires three runs including a deliberate bullet deletion showing RED. E-05, E-09, Required tests and the gate all state that a clean `aw check` is not evidence of the `- Id:` half. |
| PR-602 | HIGH | IN-SCOPE | E. verification (an assertion that fails on a correct outcome) | `aw find y5od1h` -> plan + walkthrough + `.aw/records/reviews/20260901-lanectn-04-y5od1h-...review.md`; same for `4fodkt`; `zpbx7o` -> plan + walkthrough | **`find <plan id6>` RETURNS MORE THAN THE PLAN, BY DESIGN.** A review record is named after the plan it reviews and legitimately shares its id6 handle, so the authored "returns only the plan" assertion is false for two of three and would read a correct post-fix state as a failure, or invite an executor to "fix" it by renaming a review record. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-09 (4) now asserts the real property: no WALKTHROUGH appears, the D140 collision warning is gone, and the same-named review record is expected and correct. Recorded as F-8 with the measurement. |
| PR-603 | HIGH | UNDER-SCOPE | A. correctness; C. architecture | `plan_reference_rewrites` driven on the three renames: 36 edits across 8 files; unlisted are `20260925-carrierauth-01-vtkfq8-...` (6 hits: fenced driven-evaluation transcript + embedded `aw check --agent` JSON) and this plan (6 hits) | **THE CITATION CENSUS MISSED 2 OF 8 FILES, AND ONE IS A RECORDED TRANSCRIPT.** `vtkfq8` is the same KEEP class as the `t0jyb2` the plan did name. Because the preview API has no per-file exclusion, an executor who previewed and then applied the returned list wholesale would have rewritten two recorded transcripts, corrupting evidence of what `aw check` printed. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-07 names all eight files with a KEEP/REWRITE disposition each, forbids calling `apply_reference_rewrites` on the whole list, and instructs filtering to the three documented plans. V-07 requires the 8-file hit list and `git diff --quiet` proof for `vtkfq8` as well as `t0jyb2`, both backlog items and this plan. |
| PR-604 | MEDIUM | IN-SCOPE | E. verification (a baseline that does not exist) | `aw check all --agent` at HEAD: 5 findings (3 `check.id6-identity-slot`, 1 `check.scope-drift`, 1 `check.system-layout-missing`); authored V-08 said "compare the rule list to HEAD's 9 findings" | **THE STATED HEAD BASELINE IS WRONG (5, NOT 9),** so the before/after comparison the validation rests on could not have been performed as written, and an executor might have read the two unrelated survivors as regressions introduced by this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-3 corrected to record 5 with the per-rule breakdown; E-09 (1) and V-09 now name the baseline, the expected after-state (2), and that both survivors are pre-existing and unrelated. Suite baseline `2584 passed, 2 skipped` also recorded. |
| PR-605 | MEDIUM | IN-SCOPE | A. correctness; F. honest documentation | `KNOWN_FEATURE_CUTOVERS` block comment: "THE FEATURE INTRODUCTION DATE - the value in this dict ... DATE 1 IS THE INPUT TO A SEARCH, NOT THE BOUNDARY"; `spec_id6` dict value `2026-08-28` vs resolved boundary `20260829`; simulated registration stamps the install date | **E-03 JUSTIFIED THE REGISTRY VALUE AS IF IT WERE THE ENFORCEMENT BOUNDARY,** which the code explicitly says it is not. The grandfathering conclusion happens to hold here, but it was asserted from a false premise, so nothing would have caught a boundary that landed earlier than intended in this or any other repository. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 rewritten to state the two-date contract, cite the rejected option (b) of `x75obw` OQ-03, and require the grandfathering be VERIFIED not inferred. Its Expected outcome and V-03 now demand the resolved boundary and a zero-nonconformant count over all 24 walkthroughs; the gate adds a stop condition if the boundary is at or before `20260918`. Recorded as F-10. |
| PR-606 | MEDIUM | IN-SCOPE | A. correctness (a stale status claim) | `e2j5w4` is `- Status: open`; `check_collisions(Path('.'))` returns the 3 slot findings with DEFAULT arguments (the exact behavior `e2j5w4` reported missing) | F-3 asserted `e2j5w4`'s defect "is already fixed (t0jyb2)". True of the CODE, false of the RECORD. Left unqualified it invites an executor to close or ignore a live `Blocks-Release: next` bug item on this plan's authority. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-3 now states both halves with the measurement; the gate states explicitly that `e2j5w4` is NOT closed by this plan because its status is a separate record this plan has no authority over. |
| PR-607 | MEDIUM | IN-SCOPE | G. executability (an unverified close path) | `evaluate_blocking_close(repo, mw0s1y, 'done', evidence=<future executed plan path>)` -> `legitimate=False`, `error`, "closing it `done` would silently drop that release gate"; with an EXISTING artifact -> `legitimate=True`; the plan declares `- From-Backlog: f2u4l0`, not `mw0s1y`, and carries no `Blocks-Release` | The gate instructed closing `mw0s1y` via `--evidence` without stating that the HANDOFF escape does not apply (the plan's `From-Backlog` names a different item) or that the evidence path must already resolve, so the close FAILS CLOSED if attempted before finalize. Correct instruction, unstated preconditions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now records that HANDOFF does not apply, that SATISFIED via `--evidence` is therefore required, and that the close must happen AFTER finalize because the cited artifact must resolve, with the driven verdicts as evidence. |
| PR-608 | LOW | IN-SCOPE | G. executability (an ambiguous census input) | `git ls-files .aw/records/walkthroughs/` returns 26 paths; 24 are walkthroughs, the others `.gitkeep` and `README.md` | F-2's "24 walkthroughs" is correct but a naive `git ls-files` line count returns 26, and E-06's new tree-wide test iterates that directory, so the two non-records must be excluded deliberately rather than by accident. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-2 records the 26/24 distinction and warns the executor; E-06 keys on the shipped normalizer's parse of the identity slot rather than a bare directory listing, and exempts the 11 legacy names explicitly so the grandfathering is stated. |
| PR-609 | LOW | IN-SCOPE | C. architecture (an undeclared-but-correct scope boundary) | `ipd_lifecycle._scope_match`: a trailing-slash entry "matches any path beneath it"; `vtkfq8` appears in the citation preview but is left byte-identical; `_check_identity_slots` docstring: "DO NOT 'fix' this by adding a declared-duplicate case here" | Three scope facts were true but unstated: the README is covered by the directory entry (not a fence gap), `vtkfq8` must NOT be added to the fence despite appearing in the preview, and F-7 must not be "fixed" by widening the checker rule the plan works around. Each is a plausible wrong turn for an executor. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Three bullets added to the Scope check stating each, with the matcher behavior and the rule docstring's own prohibition cited. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `check.id6-identity-slot` cannot see the missing `- Id:` half (PR-601). Widen the checker rule, or add a test? | ADD A TEST (new E-06). Leave `_check_identity_slots` untouched. | (a) Widen rule (b) to flag a slot id6 whose file declares no Id at all: rejected, that would flag the 11 grandfathered legacy names' successors and, more importantly, the rule's own docstring forbids exactly this class of change ("DO NOT 'fix' this by adding a declared-duplicate case here ... handing an operator two findings and two remedies for a single problem"). (b) Rely on V-05's pasted bullets: rejected, self-report is not verification, and the whole defect is that nothing could fail. (c) File a follow-up backlog item for the rule gap: rejected, there is no rule gap; the rule is correct for what it checks, and the plan's own assertion was the weak link. | Driven `_check_identity_slots` on both post-rename shapes; the function's docstring; `.aw/records/walkthroughs/README.md`'s "MUST mint its own id6 there". | yes |
| D-2 | `aw find y5od1h` returns a review record too. Is that a defect to fix, or an expectation to correct? | CORRECT THE EXPECTATION. The shared handle is by design. | (a) Treat it as a D140 violation and re-id the review records: rejected and dangerous, it would expand this plan into renaming review artifacts on a reviewer's reading of a rule nobody applied to them, with no maintainer decision. (b) Keep the authored assertion and let the executor discover it: rejected, a validation that fails on a correct outcome is worse than no validation, because it pressures an executor toward an unsanctioned "fix". | `aw find` output for all three ids; review records are named after the plan they review (observed across `.aw/records/reviews/`). | yes |
| D-3 | The citation preview hits 8 files; 3 must be rewritten and 5 left alone. Filter in the plan, or add per-file exclusion to the tool? | FILTER IN THE PLAN (name all eight with dispositions; forbid the wholesale apply). | (a) Add an exclusion parameter to `plan_reference_rewrites`: rejected, that edits a shared reference-rewriting library outside this plan's fence and scope for a one-off classification the plan can state directly. (b) Rewrite everything including the transcripts: rejected, it destroys the record of what `aw check` printed, which is the evidence those plans exist to carry. | Driven preview: 36 edits, 8 files; `t0jyb2` already named as KEEP for exactly this reason; `apply_reference_rewrites` takes a flat edit list with no exclusion. | yes |
| D-4 | E-03's cutover rationale is wrong about what the registry value means. Correct the prose only, or change the value? | CORRECT THE PROSE and require the boundary be MEASURED. Keep the value shape (introduction date = execution date). | (a) Change the dict value to something "safely after 20260918": rejected, it would encode a boundary in the field the code says is not a boundary, which is the misreading this repository documents at length and which the block comment's own rejected option (b) warns against. (b) Leave the prose: rejected, the conclusion is right only by luck of this repo's install history, and another repo's boundary is computed differently. | `KNOWN_FEATURE_CUTOVERS` block comment; `spec_id6` dict `2026-08-28` vs resolved `20260829`; simulated `sync_cutovers_on_install` on a fresh repo and a November-installing repo. | yes |
| D-5 | May this plan rename three tracked records, given `mw0s1y`'s "DO NOT RENAME ... WITHOUT A MAINTAINER DECISION"? | YES, accepting OQ-01's reading, and SURFACE it in the gate rather than blocking. | (a) Raise it as a `Blocking: yes` question: rejected, the brief's instruction is specific ("re-id the 3 D140 walkthroughs") and matches the remedy `mw0s1y` itself names, so blocking would re-ask a question already answered. (b) Resolve it silently: rejected, a rename of tracked records is the highest-consequence act in this plan and a maintainer reading the gate should see it named. | `mw0s1y`'s own text naming re-identification as the remedy for all three files; OQ-01's citation of the 2026-09-26 brief. | yes |
| D-6 | Should this plan close backlog `e2j5w4`, whose code defect is fixed but whose status is `open`? | NO. State both halves and leave the item alone. | (a) Close it as done: rejected, this plan does no work on it and closing another item's record on a reviewer's measurement would be a status claim with no carrier; it also carries `Blocks-Release: next`, so a close must go through the close-legitimacy gate on its own evidence. (b) Leave F-3's "already fixed" unqualified: rejected, it reads as permission to ignore a live blocker. | `e2j5w4` is `- Status: open`; `check_collisions(Path('.'))` returns the 3 slot findings with default arguments, so the code half is genuinely fixed. | yes |

### Deferred and open

- (none). All nine findings were FIXED in place. None reached Medium-High or High Remediation Risk
  (every repair was a plan-text change verifiable by measurement, and the two HIGH-severity ones were
  fixed by ADDING a test and correcting an assertion rather than by reducing scope), so the Fix Bar
  permitted no deferral. Because nothing was left `OPEN` or `DEFERRED`, no escalation to a
  `- Blocking: yes` question was required.
- The authored OQ-01 was re-read rather than accepted: its premise (that `mw0s1y` demands a maintainer
  decision, and that the brief supplies one) is corroborated by `mw0s1y`'s own text, which names
  re-identification as the remedy for all three files. Retained as resolved, and surfaced in the gate
  as the one judgement a maintainer may want to overrule (D-5).
- The plan's three `Carrier`/`Carrier-Declined` rows were checked against the tooling rather than by
  eye: `check_engine.evaluate_durable_carrier` returns `[]` for this plan, so no obligation is
  uncarried.
- No `Reversible: no` decision was made. All six decisions are plan-text choices on an unexecuted
  plan; none renames anything yet, publishes an interface, or deletes data.

HONEST LIMITS, stated because they bound what this round proves. FIRST, I did not execute any part of
the plan: no walkthrough was renamed, no cutover was registered, and `tests/test_walkthrough_id6.py`
does not exist yet, so my confidence that E-01's three cases behave as stated rests on driving the
underlying functions (`check_names`, `check_collisions`, `resolve_cutover_date`, the normalizer)
against synthetic tmp repos, not on running the authored tests. SECOND, my grandfathering measurement
used a SIMULATED `20260927` boundary injected into `KNOWN_FEATURE_CUTOVERS` in-process; the real
stamped value depends on this repo's install history at execution time, which is why V-03 now measures
it rather than trusting my number. THIRD, the citation census is `plan_reference_rewrites`' own output
for three specific renames; a different minted id6 cannot change the hit SET, but a fourth file could
cite a walkthrough by a form the preview does not model (an id6 alone, which the function
deliberately never emits), and I did not hand-search for that. FOURTH, I verified that
`_check_identity_slots` clears on a rename alone using synthetic record tuples rather than by actually
renaming files on disk; the tuples are exactly the shape `check_collisions` builds, but the end-to-end
path is unproven until E-06 runs. FIFTH, I did not audit whether the 11 legacy walkthroughs SHOULD be
renamed; I accepted the plan's grandfathering policy because it matches the shipped precedent for
specs and prompts, and that is a policy inheritance rather than an independent judgement.
