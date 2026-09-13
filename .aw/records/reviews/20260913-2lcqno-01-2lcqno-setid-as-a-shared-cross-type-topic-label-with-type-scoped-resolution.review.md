# Review findings: spec 2lcqno

- Subject-Id: 2lcqno
- Subject-Type: spec
- Reviewed-At: 2026-09-13
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `9697856e`. Structural preflight `aw specs check` CONFORMED (exit 0) before semantic
review and again after every revision. No pre-review snapshot was needed: the spec was committed and
unmodified (`git status --porcelain` on it returned empty).

THE DESIGN IS RIGHT AND EVERY NUMBER IN IT HAS MOVED. The reversal this spec records is sound, the
maintainer's reasoning is preserved where it belongs, and the five measurements were honest when taken.
But the spec is written as though its counts were invariants, and four of the six acceptance criteria
were phrased as equality against them, so re-measurement falsifies the CRITERIA while confirming the
ARGUMENT. That gap is what this review closes.

THE ONE THAT CHANGES WHAT AN IMPLEMENTER WILL FIND. The 5 within-type descriptive conflicts that
justify keeping half the rule (N5) DO NOT EXIST ANY MORE. They were resolved by RENAME on 2026-09-11 in
commit `4f1ca199`, at the maintainer's own suggestion and chosen over widening the rule: six executed
plans sharing three setids became `relrev01`/`relrev02`/`relrev03`, `leaksan01`, `assessdoc01`,
`assessbug01`. Re-measured with the production predicate, the descriptive branch now returns ZERO on
every population. So criterion 2 as authored ("the 5 findings still report") is UNSATISFIABLE, and an
implementer meeting a zero would reasonably conclude they had broken something. The branch is now
LATENT BY DESIGN and must be pinned by a fixture, which is what criterion 2 now says.

THE MOTIVATING FAILURE NO LONGER REPRODUCES, AND THAT MOVES THE DELIVERABLE. Finding 3 quotes
`aw ipd set approved agentadhere` failing on a cross-type resolution. Measured: it SUCCEEDS, because
`match_selector` narrows `record_types` to the scoped type, and that landed in commit `91077905` on
2026-08-27, BEFORE this spec was authored. So N3's typed half needs PINNING, not building, and the live
defect is the UNTYPED path, which fails differently (it dies on a backlog item's status vocabulary).
The graduated child `w2y5ac` found this by executing rather than reading and its review says so; the
spec never absorbed the correction.

I REPRODUCED THE HAZARD THE CHILD PLAN WARNS ABOUT, ON MYSELF, WHICH IS WHY IT IS NOW IN THE SPEC.
Running `aw ipd set approved agentadhere` to verify the quoted failure WROTE: it reverted all seven
executed `agentadhere` plans out of `executed/` into `pending/` and rewrote their status. Reverted
immediately with `git restore --staged --worktree` plus removal of the seven untracked files, verified
byte-identical to HEAD, nothing committed. This is the second recorded occurrence (the first, during
`w2y5ac`'s authoring, is backlog `f5pttg`), so the warning is now in the SPEC rather than only in a
child plan, with `--dry-run` named.

TWO FURTHER CORRECTIONS. The `doctor`-versus-`check` split in Section 6 is THREE-way, not two-way:
doctor independently demotes findings under `executed/`, so reconciling `include_retired` alone cannot
make the surfaces agree (measured 81 / 81 / 35 across predicate, doctor and check). And keeping the
within-type branch requires a KEYING fix, not just a guard: `seen_sets` is keyed on the setid alone and
holds the first file seen with `plans` iterated first, so deleting the cross-type branch converts a
noisy miss into a SILENT one. Both facts came from the child plan's review and belong in the spec they
implement.

WHAT THE SPEC GOT RIGHT AND KEEPS UNCHANGED: the reversal itself, the maintainer's preserved reasoning,
the seven normative items' substance, the honest irony about the predecessor's own colliding setid, and
OQ-01's resolution, whose decision rule turns on an order of magnitude that has not changed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-001 | HIGH | IN-SCOPE | C. acceptance criteria cover the requirements | `4f1ca199` (2026-09-11); re-measured `check_collisions` descriptive count = 0 on every population | **ACCEPTANCE CRITERION 2 IS UNSATISFIABLE: the 5 within-type findings it requires to still report were renamed away.** The spec keeps half the collision rule (N5) because 5 genuine descriptive conflicts existed, and criterion 2 demands they still report. They were fixed by rename two days before this review, so the branch now returns ZERO on every population. An implementer would either fail the criterion for a reason unrelated to the change, or read the zero as having broken the branch they were told to preserve. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Section 1 finding 4 carries the re-measurement, the rename commit, and the consequence (the branch is LATENT BY DESIGN). N5 states that a zero count is the CORRECT result and requires a fixture plus a mutation check. Criterion 2 rewritten to demand the fixture and the mutation check rather than a live count. Cost 2 rewritten, since its old text asserted the 5 still need fixing. |
| SR-002 | HIGH | IN-SCOPE | A. the problem is real and current | `91077905` (2026-08-27); `match_selector('agentadhere', scoped_type='plans')` -> 7 matches, all plans; `w2y5ac` F-1/F-2 | **THE MOTIVATING FAILURE WAS ALREADY FIXED WHEN THE SPEC QUOTED IT AS LIVE, and the correction moves the primary deliverable.** Finding 3 calls the typed lookup defect 'this spec's primary deliverable' and quotes its error. The typed path was fixed a fortnight before authoring; the surviving defect is on the UNTYPED path with a different error. A plan written from the spec's prose alone would harden working code and leave the real failure in place, which is exactly what the graduated child nearly did. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | Finding 3 gains the correction with the fixing commit, the re-measurement, and the statement that N3's typed half needs PINNING rather than building. N3 says the same at the requirement. Criterion 5 rewritten to demand a regression test that fails when the narrowing is reverted, rather than a demonstration that the command works. |
| SR-003 | HIGH | UNDER-SCOPE | F. honest limits; D. irreversible commitments | the seven `executed -> approved` lines produced during this review; backlog `f5pttg`; `w2y5ac` F-5 | **THE SPEC INVITES A REPRODUCTION THAT DESTROYS RECORDS, AND SAYS NOTHING ABOUT IT.** Finding 3 presents a bare `aw ipd set approved agentadhere` as the evidence to check. That command WRITES with no confirmation: run during this review it reverted all 7 executed `agentadhere` plans out of `executed/`. It had already happened once during the child plan's authoring, so the spec's own suggested verification is a known record-destroying operation and the warning lived only in the child. | C:Low; U:High; S:Low; F:Medium; Overall:Medium | FIXED | Finding 3 now carries the warning by name, both occurrences, and the instruction to use `--dry-run` for every reproduction. Reverted with `git restore --staged --worktree` plus removal of the seven untracked copies; verified byte-identical to HEAD; nothing committed. Disclosed in this record rather than quietly repaired. |
| SR-004 | MEDIUM | IN-SCOPE | A. measured claims are current | re-measured at `9697856e`: 431 distinct setids / 130 cross-type (was 433/117); `aw check` 35 (was 38); `--all` 81 (was 86) | **EVERY HEADLINE COUNT HAS MOVED, AND THE SPEC PRESENTS THEM AS INVARIANTS.** Four of six acceptance criteria were phrased as equality against a literal count ('the 78 findings, the 2, the 1'), so ordinary corpus growth falsifies them. The direction of drift CONFIRMS the argument (cross-type sharing grew from 117 to 130 topics), which is precisely why the criteria should never have been written as equalities: they fail while the thesis strengthens. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Section 1 gains a standing note that every count is a dated snapshot of a growing corpus, with inline re-measurements where they moved. Section 5 rewritten in SHAPE terms with a stated rule that each criterion re-derives its number and reports the denominator, so a zero is corroborated. New cost 4 records the snapshot property. |
| SR-005 | MEDIUM | UNDER-SCOPE | A. correctness; the spec's own surviving deliverable | `216rgg` review's three-file fixture (one plan + two conflicting specs): HEAD emits 2 cross-type findings and never the spec-vs-spec conflict; cross-type branch removed emits 0 | **KEEPING THE WITHIN-TYPE BRANCH IS ILLUSORY WITHOUT A KEYING FIX, and N5 as authored asks only for the branch.** `seen_sets` is keyed on the setid ALONE and stores the FIRST file seen, with `plans` iterated first, so a foreign-type predecessor occupies the slot a within-type comparison needs. Deleting the cross-type emission therefore turns a noisy miss into a SILENT one, which is strictly worse for the one behavior the spec is preserving. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | N5 now requires the per-type keying fix alongside the guard, with the measured fixture and both failure modes named. New criterion 3 demands the shared-slot case report the genuine same-type conflict, which neither HEAD nor a guard-alone fix does. |
| SR-006 | MEDIUM | IN-SCOPE | F. honest limits; C. criteria are evaluable | measured: predicate 81 with retired included, `aw doctor --agent` 81, `aw check` 35; `doctor.py:519-528` demotes `executed/` findings independently of `include_retired` | **SECTION 6 STATES A TWO-WAY SPLIT WHERE THERE IS A THREE-WAY ONE, so its own criterion cannot be met as written.** Doctor demotes findings under `executed/` on an axis independent of `include_retired`, so reconciling that flag alone cannot make the surfaces agree. Criterion 3 ('the SAME population') was therefore unreachable by the route the spec describes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Section 6 gains the third axis, the three current numbers, the two historical ones, and an explicit statement that this spec does NOT decide which population wins (that is a wider `aw check` question, carried by plan `216rgg`) but requires only that the surfaces AGREE. Criterion 4 names both axes. Line citations refreshed (`doctor.py:538`, `check_engine.py:1763`). |
| SR-007 | MEDIUM | UNDER-SCOPE | F. security-adjacent honest limits | `w2y5ac` F-7: `match_selector(<plan path>, scoped_type='specs')` -> 1 match of type plans; with the mismatch branch deleted, `aw specs set approved <plan path> --by-human` SUCCEEDS and appends a forged human attestation to the plan; suite stays green | **N3 READS AS THOUGH TYPE SCOPING WERE COMPLETE, and one selector kind it does not cover is the only path to a forged cross-type write.** Scoped resolution is type-safe for id6/setid/status/stem/substring and NOT for a direct PATH, because path precedence matches an existing file regardless of the type requested. The `Type mismatch` refusal is the sole guard, nothing tests it, and the child plan's review measured that deleting it lets a spec verb rewrite a PLAN and forge a `--by-human` history line. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | N3 now names the path exception, the measured consequence, and the instruction that the refusal be PINNED and never retired as dead code. New criterion 6 requires the refusal to hold and to be tested, since nothing tests it today. |
| SR-008 | LOW | OVER-SCOPE | F. scope statement excludes what neighbours own | the non-goal 'Renaming any existing artifact' versus commit `4f1ca199`, which renamed six | **A NON-GOAL FORBIDS SOMETHING THE MAINTAINER THEN DID, with no distinction drawn.** 'Renaming any existing artifact' is correct for the CROSS-TYPE case (renaming to silence that rule would defeat the spec) and wrong as stated, since renaming to resolve a WITHIN-TYPE descriptive conflict is legitimate and is what N5 calls a genuine defect. Left as-is, the spec appears to prohibit the maintainer's own fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The non-goal narrowed to renaming TO SATISFY THE CROSS-TYPE RULE, with the within-type exception stated and the actual rename recorded as consistent with N5. A second non-goal added for the retired-population question, which Section 6 defers. |
| SR-009 | LOW | IN-SCOPE | C. criteria state refusable evidence | criterion 6 as authored: 'the full suite and `aw check all` are green' | **A CRITERION DEMANDS A GREEN `aw check all` THAT THE TREE CANNOT PRODUCE.** The repository carries 211 findings on the default scope, almost all unrelated to this rule (156 `check.scope-drift`, 14 lifecycle). An absolute-green criterion is unsatisfiable and invites satisfying it by editing a number rather than the code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Criterion 8 now requires NO WORSENING against a pasted pre-change baseline, with both counts shown, and states why absolute green is the wrong bar. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | The 5 within-type findings N5 exists to preserve no longer exist. Narrow the spec toward deleting the branch, or keep it as latent? | KEEP the branch and declare it LATENT BY DESIGN, pinned by a fixture plus a mutation check. | (a) Delete the branch as dead, rejected: the conflicts recur whenever two Sets in one type pick one setid, the maintainer chose renaming over widening precisely to keep the rule meaningful, and deleting it would discard a guard days after the maintainer acted to satisfy it. (b) Leave criterion 2 as a live count, rejected as knowingly unsatisfiable. (c) Ask the maintainer, rejected: the repository answers it, since their own rename commit states the intent ('after this the rule reports nothing because nothing is wrong'). | `4f1ca199`'s message; re-measured descriptive count 0 on every population; `216rgg` E-02's requirement that the branch survive | yes |
| D-2 | The spec's quoted motivating failure no longer reproduces. Retire the spec as stale, or correct it in place? | CORRECT IN PLACE, and re-point the deliverable from building type-scoped resolution to pinning it plus fixing the untyped path. | (a) Retire as superseded, rejected: only ONE of five measurements went stale, the reversal and the normative model are intact, and two approved plans already cite this spec as their `From-Spec`. (b) Leave the stale claim and note it in the review only, rejected because the spec is what an implementer reads and its prose would still direct them at working code. (c) Escalate to the maintainer, rejected: the correction is a measurement anyone can re-run, and the graduated child had already recorded it. | `91077905`; `match_selector` narrowing measured 7 plans scoped versus 13 unscoped; `w2y5ac` F-1/F-2 recording the same correction | yes |
| D-3 | Section 6 asks whoever implements to settle which population is authoritative. Should this spec decide it? | NO. Require only that the two surfaces AGREE, and record that the choice is a wider `aw check` question carried by plan `216rgg`. | (a) Decide it here (for example `include_retired=False` everywhere), rejected on measurement: that direction was the one plan `216rgg`'s review showed would make the rule emit nothing at all, and the decision governs every rule rather than this one. (b) Leave Section 6 silent about the boundary, rejected because the criterion then reads as this spec's obligation and an implementer would guess. | the three measured counts; `216rgg`'s own blocking question on the same choice; `check_engine.check_collisions`'s flags versus `doctor.py`'s hardcoding plus its independent `executed/` demotion | yes |
| D-4 | Reverting the seven plans my own verification moved: repair silently, or disclose? | DISCLOSE in this record AND put the warning in the spec, then revert precisely. | (a) Revert and say nothing, rejected: the execution contract forbids an unreported mutation of records, and the near-identical event during `w2y5ac`'s authoring shows the trap catches careful readers repeatedly. (b) Report only in this record, rejected as insufficient, because the SPEC is what invites the reproduction, so the warning belongs where the invitation is. (c) Use `git reset`/`git stash`, rejected: this is a shared checkout and both are indiscriminate; the fix was a path-scoped `git restore --staged --worktree` plus removal of exactly the seven untracked copies. | the seven `executed -> approved` lines; `git status --porcelain` empty afterwards; backlog `f5pttg` as the prior occurrence | yes |

### Deferred and open

None. Nine findings, all FIXED in place; none deferred, none REPLAN. OQ-01 remains `resolved` and its
decision rule is unaffected by the count drift (it turns on an order of magnitude, which did not change).

### Honest limits of this review

- IT DID NOT EXECUTE THE GRADUATED PLANS. `216rgg` and `w2y5ac` are `approved` and unexecuted, so the
  re-scope this spec authorizes is still unbuilt. This review verified the spec's CLAIMS against the code,
  not the plans' correctness.
- THE COUNTS I RECORDED WILL DRIFT TOO. That is the point of SR-004's fix: they are dated and the criteria
  no longer depend on them.
- I DID NOT SETTLE THE RETIRED-POPULATION QUESTION (D-3), so acceptance criterion 4 remains unevaluable
  until someone does. It is named rather than hidden.
