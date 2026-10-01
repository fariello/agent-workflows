# Review: Correct the stale trailer-consumption claims in run_evidence and ipd_lifecycle

- Subject-Id: 2lxcwt
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims re-measured at HEAD `f801830f` rather than read. The target plan was committed and
unchanged with a clean tree, so the pre-review snapshot was correctly skipped per Step 1.
Structural preflight `aw ipd lint --phase author` reported `conforming` before review and
`--phase review-finalize` reported `conforming` after the revisions.

THE PLAN'S THESIS IS CORRECT AND NEARLY EVERY MEASUREMENT REPRODUCES. The trailer census is nonzero
and large (965 of 5685 at review, against the plan's 843 of 5551 at authoring). The reader exists
and is reachable: `ipd_lifecycle._commit_run_ownership` at line 2433, `_trailer_owned_committed_paths`
at 2465, and `evidence["trailer_attribution"]` assigned inside `finalize_precheck` at 2888.
`tests/test_finalize_trailer_attribution.py` is `6 passed`. `validate_finding_table()` is `ok=True`
with `{'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2}` over 12 codes. F-04 reproduces exactly (both cited
strings return zero). F-05 reproduces (exactly two `a8eufb` hits, both in `ChangedPathSources`, one
saying "remains the real fix" while the item is `done`). F-09, the finding the whole fence rests on,
reproduces by reading the consumer: `_commit_run_ownership` returns only `owned`/`foreign`/`unknown`,
and `finalize_precheck` uses `trailered.paths` for a demand-only ownership decision, never for a
tree-diff contents comparison, so the row stays correctly `UNBOUND_BY_DEPENDENCY`. The plan's choice
to re-derive its scope from disk rather than from the item's stale citations was right.

THE DOMINANT FINDING IS THAT THE PLAN WOULD HAVE LEFT A THIRD FALSEHOOD STANDING IN THE SAME SPEC
SENTENCE IT EDITS. That sentence reads: "the AGENT's own code commits are generally UNTRAILERED
(backlog `j2srcc`); and NOTHING READS A TRAILER BACK (backlog `am1g38`), so no commit's ownership is
yet decided by its trailer". E-06 addressed the second and third clauses and not the first, yet the
first is equally false: `j2srcc` closed 2026-09-27 via executed plan `a6xbso` ("stamp AW-Run and
AW-Item trailers on the agent's own aw commit"), and measured at review the agent's own `work(...)`
commits do carry `AW-Item`, with 178 of the last 202 non-merge commits trailered. The plan's own
F-10 already KNEW `j2srcc` was `done` and drew the conclusion for the code comments without carrying
it into the spec edit. Leaving it would have re-seeded, inside the corrected sentence, the exact rot
this plan exists to stop. That is PR-101.

THE PLAN'S OWN FINDINGS ROTTED DURING REVIEW, which is both a finding and the sharpest available
argument for its no-dated-counts rule. F-06 asserted that no test file references `RUN_FINDING_CODES`;
`tests/test_host_capability_extension.py` now does, added 2026-09-30 by commit `8b9d7945` (plan
`00pirb`) about fourteen hours AFTER this plan was authored. It is NOT the byte-equality test three
prior plans warn about, and it constrains nothing this plan edits: it pins only `RUN-COMMIT-GATEWAY`'s
`binding` and empty `predicates`. It is in fact a WELCOME tripwire against the OQ-02 overcorrection,
for one of the two rows. The census and the `run_item_trailers` call count had also moved. All three
are now recorded with both measurements and the structural restatement, and E-02 runs the new guard
explicitly so a green pass after the edit is positive proof the fence held.

TWO HAZARDS OF OMISSION, each one execution turn's cost. The spec contains the target phrase TWICE,
and the second occurrence is inside `olkeju`'s own 2026-09-26 `aw specs note` line, a historical
record that must stay byte-identical; an executor grepping to confirm removal would have found a
match with no instruction on what to do with it, and the plan had already settled this same hazard
shape for the `m73aet` quotation in OQ-01 without generalizing it (PR-103). And `aw specs note`
stages and commits nothing (`specs.py` module docstring: "NEVER stages, commits, or pushes git"),
which the plan nowhere stated, so the spec file must reach the commit through the plan's own
`aw commit` call (PR-105).

ONE QUESTION ANSWERED SO THE EXECUTOR NEED NOT RE-DERIVE IT. One other pending plan, `6uhtko`
(`approved`), quotes the very `waiting_on` string this plan rewrites, as the model for its own new
rows, and declares the same file. It does not EDIT that string, adds a separate table, and does not
touch the spec, so there is no same-sentence collision. File overlap alone is not a hazard here, per
the repository's own runner-isolation rule. Recorded as F-14.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | UNDER-SCOPE | D. Anti-regression; G. Plan executability | `.aw/records/specs/approved/20260826-25kzda-01-25kzda-...spec.md:65` the clause "the AGENT's own code commits are generally UNTRAILERED (backlog `j2srcc`)"; `.aw/records/backlog/done/20260922-trailread-01-j2srcc-...backlog.md` `- Status: done` | E-06 corrects two false clauses and leaves a THIRD standing in the same sentence. `j2srcc` closed 2026-09-27 via executed plan `a6xbso`, and the agent's own `work(...)` commits now carry `AW-Item` (178 of the last 202 non-merge commits trailered). The plan's own F-10 already knew `j2srcc` was done without carrying it into the spec edit. Leaving it re-seeds the exact rot this plan exists to stop, inside the sentence it corrects. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now names all three false clauses with the `j2srcc`/`a6xbso` evidence, requires both stale citations corrected, and forbids writing a count or share into the spec. Added F-11. E-01 gained measurement (e) confirming `j2srcc` is still `done` and the agent's commits still trailered, with a scoped stop condition that voids only E-06 clause (i) if it has regressed. V-06 and the Scope/Spec-sync sections reconciled. |
| PR-102 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy | `tests/test_host_capability_extension.py::test_commit_gateway_claim_consistency`; `git log -S RUN_FINDING_CODES -- tests/test_host_capability_extension.py` -> `8b9d7945 2026-09-30 19:45`; plan authored `889a643e 2026-09-30 05:23` | F-06's "no test file references `RUN_FINDING_CODES`" half has EXPIRED. A guard landed ~14 hours after authoring. It is not the byte-equality test the prior plans warn of and does not constrain this plan's edits, but E-02 would have re-measured, found it, and had no instruction on what it means. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-06 retained as the historical measurement and annotated as expired. Added F-13 with the commit and timing. E-02 rewritten to state exactly what the guard pins, to note it is a welcome tripwire against the OQ-02 overcorrection, and to run it explicitly before AND after. V-02 and the Required-tests section demand the green pass as positive proof the fence held. Deferred's finding-table-test entry revised from "ZERO coverage" to "narrowed, not closed". |
| PR-103 | MEDIUM | UNDER-SCOPE | A. Correctness; D. Anti-regression | `grep -n "nothing reads\|NOTHING READS"` on the spec -> two hits: line 65 and the 2026-09-26 `aw specs note` history line | The spec carries the target phrase twice; the second is inside `olkeju`'s own history record of a PRIOR amendment, true when written and not rewritable. An executor verifying removal by grep would hit it with no instruction, and the plan had already settled this identical hazard shape for the `m73aet` quotation (OQ-01) without generalizing it to the spec. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-12. E-06 now explicitly excludes the `## Workflow history` section and names the `olkeju` line. The `- Scope:` OUT list gained it. V-06 requires every surviving grep hit to be accounted for, with the history line shown unchanged. |
| PR-104 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy | census `843/5551` at `d77a4971` versus `965/5685` at `f801830f`; `run_item_trailers` occurs 9 times in `runner_shared.py`, not the claimed five | The plan forbids writing dated counts into the prose it produces, then hardcodes its own perishable figures into F-01, F-10 and E-01 as the bar. Two had already moved within a day, so an executor re-measuring would see a mismatch with no statement of whether that invalidates anything. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-01 and F-10 restated structurally with BOTH measurements recorded and the drift named as the evidence for the rule. E-01 now lists both figures per fact, states the four STRUCTURAL premises the argument actually rests on, and declares that a moved count is a PASS while a failed structural premise is not. V-01 updated to match. The Concern field reworded likewise. |
| PR-105 | LOW | UNDER-SCOPE | G. Plan executability | `agent_workflows/specs.py` module docstring: "NEVER stages, commits, or pushes git" | The plan prescribes `aw specs note` for the amendment record but nowhere states that it does not stage or commit, so an executor could reasonably assume the spec edit was committed by the verb and omit the spec path from its `aw commit` call, failing the finalize scope reconciliation it declared. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 and the Spec-sync section now state that `aw specs note` stages nothing and the spec file must reach the plan's own path-scoped `aw commit`. V-06 requires proof it did. |
| PR-106 | LOW | IN-SCOPE | 3.1 open-question ownership | plan OQ-01 and OQ-02, each `- Status: resolved` with `- Owner: none` | Both questions were resolved by the plan author on its own authority, and the workflow requires such a resolution to record the resolver as owner. `none` asserts nobody owns a decision somebody made. No mechanical check catches this: `ipd_schema.open_question_error` returns `None` for every non-blocking combination regardless of owner, verified by driving it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both set to `- Owner: plan author`, the spelling 18 other pending plans already use. |
| PR-107 | LOW | IN-SCOPE | G. Plan executability (scope fence) | plan Scope check, Under-scope clause | The under-scope clause enumerated no candidates checked-and-excluded and gave no instruction for a genuinely necessary out-of-fence edit, where the 2026-09-01 maintainer ruling is make-and-justify. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both clauses extended: over-scope now states what else is NOT in scope, under-scope names `tests/test_host_capability_extension.py` as checked and excluded with the F-13 reason, and adds the make-and-justify instruction with a `--scope-reason`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Does the `j2srcc` clause belong in this plan's scope, or is it a separate correction? | In scope, as part of E-06's single edit. | Filing a separate backlog item, rejected: it is the SAME SENTENCE this plan already opens and the same class of falsehood, so splitting would ship a sentence correcting two of its three false clauses, which is the rot this plan exists to stop. Leaving it silently, rejected as a known falsehood the plan's own F-10 had the evidence for. | `.aw/records/backlog/done/20260922-trailread-01-j2srcc-...backlog.md` closed by `a6xbso`; measured at review that agent `work(...)` commits carry `AW-Item`; the plan's own over-scope justification for touching the spec at all applies identically. | yes |
| D-2 | What should be done about F-06's expired "zero test files" claim: delete it, rewrite it, or annotate it? | Annotate: keep the authoring measurement verbatim as the historical record and add F-13 for the current state. | Rewriting F-06 in place, rejected because the authoring measurement was TRUE when made and overwriting it destroys the audit trail this plan's own OQ-01 reasoning protects for `m73aet`. Deleting it, rejected because the three prior plans' byte-equality claim still needs refuting. | `git log -S` dating the guard to `8b9d7945`, fourteen hours after the plan's own `889a643e`; the plan's OQ-01 precedent for historical-versus-present-tense. | yes |
| D-3 | Does the new `RUN_FINDING_CODES` guard block or constrain this plan's edits? | No. It pins only `RUN-COMMIT-GATEWAY`'s `binding` and empty `predicates`; E-02 runs it before and after as proof. | Treating it as the byte-equality fence and freezing the whole table, rejected after reading the test: it asserts two fields of one row and nothing about `waiting_on` or `RUN-COMMIT-CONTENTS`. Ignoring it, rejected because E-02's whole purpose is to re-measure the fence. | `tests/test_host_capability_extension.py::test_commit_gateway_claim_consistency` read in full; driven at review, `1 passed`. | yes |
| D-4 | Is the file overlap with pending plan `6uhtko` a hazard to raise? | No; recorded as F-14 and explicitly not raised as a risk. | Raising it as a collision needing a maintainer decision, rejected: `6uhtko` quotes the string as a model and does not edit it, adds a separate table, and does not touch the spec, so there is no same-sentence conflict; and the repository's own rule states file overlap is not a runtime hazard because each execute item runs in an isolated worktree behind a merge-and-revalidate gate. | `6uhtko`'s `- Scope-Paths:` and its single quoting reference read in full; AGENTS.md "The runners own ordering, isolation, and orchestrators". | yes |
| D-5 | What owner should the two author-resolved open questions carry? | `plan author`. | `maintainer`, rejected outright: the maintainer answered neither, and writing it would be the false attestation the workflow names explicitly (plan `vtkfq8` OQ-03 precedent). Leaving `none`, rejected as asserting nobody owns a decision somebody made. | plan-review 3.1 item 5; `ipd_schema.open_question_error` driven at review returns `None` for every non-blocking combination, so no mechanical check enforces this and the workflow rule is the only authority; 18 other pending plans use this spelling. | yes |
| D-6 | Should the two unbound `RUN-COMMIT-*` rows be bound now that a reader ships? | No, and the plan's refusal is upheld unchanged. | Binding `RUN-COMMIT-CONTENTS` on the reader's existence, rejected: the reader answers ownership, the row's `pass_criterion` demands a tree-diff contents equality, and binding on presence is the fail-open inference the module's own comment and backlog `d07nz2` reject by name. | `_commit_run_ownership` returns only `owned`/`foreign`/`unknown`; `finalize_precheck` uses `trailered.paths` for a demand decision only; `RUN-COMMIT-CONTENTS.pass_criterion`; backlog `d07nz2`. | yes |

No `Reversible: no` decisions were made, so no escalation was required under the
irreversible-decision rule. No finding was left `OPEN` or `DEFERRED` at or above the `HIGH` gate
threshold, so no `- Blocking: yes` escalation question was added to the plan.
