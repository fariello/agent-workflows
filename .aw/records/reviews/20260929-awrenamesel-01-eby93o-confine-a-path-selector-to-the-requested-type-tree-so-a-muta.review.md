# Review findings: plan eby93o

- Subject-Id: eby93o
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `d6bf1b91` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after. No pre-review snapshot was owed: `git status --porcelain` was empty, so the plan was
committed and unmodified. No production file was modified at any point; the guard was prototyped as a
throwaway probe module that monkeypatched `selectors.resolve_for_mutation` in memory and was deleted,
with `git status --porcelain` empty again afterwards.

A DISCLOSURE THAT CHANGES HOW THIS REVIEW WAS CONDUCTED. This reviewer edited THIS FILE last turn,
while reviewing its Order-0 parent `95jk4s`, adding F-13 and F-14 and obligations on E-03, E-05, V-03
and V-05 under the cross-plan rule. Those additions are therefore NOT independent evidence for this
review, and every one was RE-MEASURED from the repository rather than trusted. Both hold: the
six-type reach of the cross-type rename reproduces, and `research_archive._resolve_research_for_mutation`
does confine by denying `MATCH_PATH` and then dropping out-of-root paths, refusing only `if paths and not
confined`, with its docstring citing IPD `me227c` E-04.

ALL TWELVE AUTHORED FINDINGS WERE INDEPENDENTLY REPRODUCED AND ALL TWELVE HOLD. F-01: a real
`cli.main(["--no-interactive","rename","specs",<a plan path>,"--slug","zzz","--apply","--dir",d])` in a
throwaway git repo exits 0, prints the rename, and the plan file is gone. F-02: `resolve`'s first
precedence rule is `path` and `run_rename_generic` takes `src = paths[0].resolve()` with no type
comparison. F-03: the `status_set` `Type mismatch` refusal and its comment exist as quoted. F-04:
approved spec `2lcqno` carries "type-safe for every selector kind EXCEPT a direct PATH" and "must be
PINNED, never retired as dead code" verbatim. F-05: `resolve_for_mutation(repo,'plans',<a spec path>)`
returns the SPEC with `err=None`, and `plans_refs._find_plan_by_id` iterates `plans_dir.rglob("*.md")`.
F-06 and OQ-01's decisive near-miss: `selectors.resolve(repo,'research','effzzi')` returns
`...effzzi...roadmap.md` with `kind='id6'` while `status_set.detect_artifact_type(<that file>, repo)`
returns `'roadmaps'`, so a type-equality predicate really would refuse a legitimate target. F-07: a
prototyped containment predicate sweeps the corpus with ZERO wrongly refused and refuses every foreign
path tested. F-08, F-09, F-12: confirmed by reading the code and the test corpus. F-10: passing `--yes`
exits 2 with `unrecognized arguments: --yes` and the file untouched, exactly as warned.

THIS IS A RIGOROUS, WELL-FENCED PLAN whose central design decision (containment over detected type) was
settled by measurement and is CORRECT; review re-derived that measurement and reached the same answer.
Its failing-first discipline, its in-process `cli.main` requirement with the cited `ccbe60` hazard, its
insistence on file-system assertions over exit codes, its refusal to merge with the `status_set` guard,
and its five carrier-backed deferrals are all sound. Review found no fault with the guard's placement,
its shape, or its scope. What it found is that ONE resolved open question answers a mechanism question
the WRONG WAY, and that error is sufficient on its own to make the whole plan land broken.

**OQ-02's `FAIL OPEN` RESOLUTION DEFEATS THE GUARD IN EXACTLY THE CASE THIS PLAN EXISTS TO CLOSE
(PR-601, BLOCKER).** OQ-02 asks what containment should do when `record_dirs` returns `[]`, and resolves
"FAIL OPEN (skip the check)". Review prototyped the guard exactly as E-03 specifies and ran one fixture
three ways. NO GUARD: `rc=0`, plan renamed, unrelated citation rewritten. FAIL-OPEN: `rc=0`, plan
renamed, citation rewritten, BYTE-IDENTICAL to no guard. FAIL-CLOSED: `rc=2`, `error: specs verb cannot
act on <path>: it is not inside the specs records tree`, plan present, citing record byte-unchanged.

The mechanism is a subtle asymmetry the authored reasoning missed. `record_dirs` is queried for the
type the OPERATOR NAMED, not for the file's own type. In a cross-type call the named type is precisely
the one whose tree may not exist, while the VICTIM's tree exists and is full: measured, a repo holding
`.aw/records/plans/` and no `.aw/records/specs/` gives `record_dirs(repo,'specs') == []` and
`record_dirs(repo,'plans') == ['.aw/records/plans']`. The authored justification ("a repository with no
records tree for the type has nothing to protect") silently reads the empty list as describing the
whole repository. Its second limb is worse than wrong, it is self-defeating: "with no directories,
`_iter_paths` yields nothing, so the only selector kind that can resolve at all is a direct path" is
TRUE, and a direct path is the ONLY kind that can escape (the plan's own F-08). So the one kind
fail-open admits is the only kind the guard exists for.

This would not have been caught during execution either, which is what makes it a BLOCKER rather than a
correctness nit. E-01's prescribed fixture seeds a PLAN and nothing else, so `record_dirs('specs')` is
empty there: under fail-open, E-01's test stays RED after a faithfully implemented E-03, and an executor
faces a correct-looking guard, a red failing-first test, and no explanation, in a plan whose own
evidence contract tells them to stop and report if the failing-first contrast does not resolve.

FIXED by re-resolving OQ-02 to FAIL CLOSED with the measurement recorded, adding F-15, and stating the
rule in the four places an executor reads: `- Scope:`, E-03 (with the reason and the required message
shape), V-03 (which now demands the empty-tree case be demonstrated in a repo where the requested type's
tree is ABSENT, since a both-trees-exist demonstration cannot distinguish the two behaviors), and the
execution contract. The authored worry that motivated fail-open was also MEASURED and is not a hazard:
`tests/test_group_verb_policy.py`'s bare-`git init` fixture produces byte-identical output under no
guard, fail-open and fail-closed alike, because its `zzzzzz` selector is an id6 that resolves to nothing
and never reaches containment. The plan had asked the executor to verify that claim; review verified it
and it is false.

**E-04 DEMANDED A `plans` PATH ROW THAT CANNOT PASS INSIDE THIS PLAN'S FENCE (PR-602, HIGH).** E-04
required, "for each of `plans`, `specs`, `backlog` and `research`", that the record resolve by its own
repo-relative path, its own absolute path, and its id6. For `plans` the two path rows are unsatisfiable
here: `plans` does not use the shared resolver, so measured at review both spellings exit 2 with `no
plan has Id '<path>'` while the id6 exits 0. That refusal IS the defect backlog `gyv9tf` filed and
`87m438` fixes. An executor following E-04 literally would write a row that fails for a reason this plan
does not own, then either burn a pass diagnosing it or "fix" it by taking Order 02's work and breaking
the fence, in a plan whose contract forbids exactly that. Fixed by rewriting E-04 to cover `plans` by
id6 plus the two path selectors asserted as the PRE-EXISTING refusal (which additionally pins that this
guard did not change that behavior and leaves a marker that flips when `87m438` lands), adding F-16, and
adding a sixth prohibition to the execution contract.

**THE CORPUS PAIR COUNT HAS DRIFTED (PR-603, LOW).** "1823 (type,file) pairs" appears in the
`- Concern:`, F-06, F-07, OQ-01 and the authoring history line. Re-measured, the sweep covers 1932
pairs, still with ZERO false refusals, so the conclusion is unchanged and slightly stronger. Fixed by
pairing every live citation with the re-measured figure and labelling it a figure to re-derive, adding
F-17, and having V-05 gate on the ZERO rather than the total. The authoring history line is left
intact, since it correctly records what was measured then.

NOT RAISED, each checked and let stand. OQ-01 (containment versus detected type) is correctly resolved
and its measurement reproduces; it is a HOW question and it cites a demonstration, so it meets the
demonstrate-do-not-describe bar. OQ-03 (`--force` must not override) is correct and its precedent
(`resolve_for_mutation`'s own "a data bug to fix, not overridable by --force") is real. The decision to
leave `resolve` untouched is right and the seventeen-importer figure in spec `z7nbn1` 2.1 is accurate.
The spec-sync section's reading of `2lcqno` N3 is fair, including its honest note that if a reviewer
reads `z7nbn1` 1.1 as covering mutating verbs then this plan makes it MORE true, not less. The
`Scope-Paths` exclusion of `artifact_rename.py` is correct and is what makes one guard cover six types.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. All three open questions are now resolved; OQ-02 carries the reviewer as its owner, since this
review overrode the author's answer.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | blocker | IN-SCOPE | A. Correctness and data integrity | plan OQ-02 (as authored); `agent_workflows/selectors.py` `record_dirs` ("Returns [] for an unknown/unresolvable type"); plan F-08; review prototype of the E-03 guard | OQ-02's `FAIL OPEN` answer makes the guard byte-identically as broken as no guard, because `record_dirs` is queried for the REQUESTED type, so in a cross-type call the empty list belongs to the ATTACKER while the victim's tree is full. Its second argument (only a direct path can resolve with no dirs) is true and self-defeating, since a direct path is the only kind that can escape. The plan's own E-01 fixture is an instance, so E-01 would stay red after a faithful E-03. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | OQ-02 re-resolved to FAIL CLOSED with the three-way measurement recorded; F-15 added; the rule stated in `- Scope:`, E-03 (with the required message shape), V-03 (empty-tree case must be demonstrated with the requested type's tree ABSENT) and the execution contract. The authored `test_group_verb_policy.py` worry was measured and is not a hazard. |
| PR-602 | high | IN-SCOPE | E. Testing and verification | plan E-04 (as authored); review probe over a temp repo holding one plan | E-04 demanded `plans` resolve by its own repo-relative and absolute path, which is unsatisfiable inside this fence: both exit 2 with `no plan has Id '<path>'` at HEAD because `plans` bypasses the shared resolver. An executor would write a failing row and either diagnose it or fix it by taking `87m438`'s work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-04 rewritten to cover `plans` by id6 plus the two path selectors asserted as the PRE-EXISTING refusal (a marker that flips when `87m438` lands); F-16 added; V-04 requires that shape and fails a `plans` path row asserted as success; a sixth execution-contract prohibition added. |
| PR-603 | low | IN-SCOPE | Evidence freshness | re-measured sweep: `pairs checked: 1932 wrongly refused: 0` against the plan's `1823` in `- Concern:`, F-06, F-07 and OQ-01 | The corpus pair count has drifted. No conclusion moves and the zero-false-refusals result is unchanged, but a reader could mistake the total for current, and V-05 gated on a count rather than on the property. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Every live citation now pairs 1823 with the re-measured 1932 and labels it a figure to re-derive; F-17 added; V-05 gates on the ZERO, not the total. The authoring history line is left intact as the record of what was measured then. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | OQ-02's resolved answer is wrong and it is a resolved, non-blocking question the author owns. Override it, or raise a new blocking question and leave the plan NO-GO for the maintainer? | Override it in place, re-resolve to FAIL CLOSED, record the measurement, and reassign OQ-02's owner to the reviewer. | (a) Raise `- Blocking: yes` and hand it to the maintainer: rejected because the repository answers it decisively; review ran the guard three ways over one fixture and the fail-open variant is measurably indistinguishable from no guard, so this is a fact rather than a judgement call, and the workflow's own rule is not to ask the human what the repository already answers. (b) Leave the answer and add a warning: rejected because E-03 is what an executor implements, so a warning elsewhere would lose to the resolved question's plain text. | Three-way prototype run over one fixture: no-guard `rc=0` plan renamed; fail-open `rc=0` plan renamed (identical); fail-closed `rc=2` plan present, citation byte-unchanged. `record_dirs(repo,'specs') == []` beside `record_dirs(repo,'plans') == ['.aw/records/plans']` in that repo. | yes |
| D-2 | E-04's `plans` path rows cannot pass. Drop the `plans` rows entirely, assert the pre-existing refusal, or let `87m438` become a dependency of this plan? | Assert the pre-existing refusal (`no plan has Id '<path>'`) for the two path spellings, and `plans` id6 for success. | (a) Drop the `plans` rows: rejected because `plans` is the type the whole Set is about and its absence from the matrix would read as an oversight; asserting the refusal also pins that this guard did not change that behavior. (b) Make this plan depend on `87m438`: rejected outright, as it would invert the Set's only required edge, which F-05 measures as forced in the other direction. | Measured: `aw rename plans <rel path>` and `<abs path>` both `rc=2` with `no plan has Id`; `ab12cd` `rc=0` with the preview. Parent `95jk4s`'s child table and `87m438`'s `- Item-Dependencies: executed:eby93o`. | yes |
| D-3 | F-13 and F-14 were added to this file by THIS reviewer last turn, so they are not independent evidence for this review. Re-measure them, or accept them? | Re-measure both from the repository before relying on either. | (a) Accept them as already-reviewed content: rejected because they were authored by the same agent in the same sweep, so accepting them would make this review partly a review of its own output, and the six-type claim in particular is load-bearing for E-05's new obligation. | Re-measured: the six-type rename matrix reproduces; `research_archive._resolve_research_for_mutation` carries `deny=frozenset({selectors.MATCH_PATH})`, the `relative_to(rroot_resolved)` drop loop, and the `if paths and not confined` refusal, with its docstring citing `me227c` E-04. | yes |
