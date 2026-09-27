# Review findings: plan 7nghg8

- Subject-Id: 7nghg8
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `78a40cc9` in a lane worktree. Structural preflight `aw ipd lint --phase author`
CONFORMED with ONE advisory, `IPD-Z602` on E-04 ("names multiple independent deliverables ... 3
clauses"); that advisory is cleared by the E-04/E-06 split (PR-003), and `--phase review-finalize` now
conforms with no advisories. No pre-review snapshot was needed: the plan was committed and unmodified,
and the lane-input copy is byte-identical to the tracked file.

THIS REVIEW HELD ITSELF TO THE RULE THE PLAN IS INTRODUCING, which is the only honest way to review it.
Every mechanism I asserted, I ran.

THE PLAN'S CASE IS TRUE AND EVERY QUOTED PHRASE IS VERBATIM. I re-read plan `vtkfq8`'s OQ-03 rather
than trusting the brief. Its resolution contains, exactly as F-1 quotes: "Emit the carrier line as a
COMMENTED / inert placeholder that the gate does NOT read as a value", and "The executor must confirm
the chosen form empirically in E-02's third assertion rather than assuming a given spelling is inert;
if NO inert form can both suppress the obligation and stay unsatisfying, that is a genuine conflict to
put to the maintainer". So the plan's central claim, that the reviewer knew feasibility was unproven
and marked the question resolved anyway, is established from the artifact's own text. The maintainer's
re-ruling is real (`35d72343`, "record maintainer re-ruling of OQ-03 (gate skips the untouched scaffold
example question); re-scope E-01/E-02"), and the superseding text states the mechanism reason the plan
gives: "the obligation comes from the question's `- Status: open`, not from a missing carrier line".
F-2 is likewise supported: OQ-03 carries `- Owner: maintainer` while its own prose argues "it is the
ruled intent rather than a reviewer's invention", and the backlog it cites calls its list "candidate
shapes, not decided here". F-3 checks out: `rg 'HOW question|mechanism' plan-review.md` finds only
three unrelated rubric lines.

ALL THREE INSERTION POINTS EXIST, WITH THE QUOTED ANCHOR TEXT. `plan-review.md` `### 3.1 Build the
question set` contains "Resolve questions from authoritative evidence first. Cite the source.";
`plan-review-long/03-resolve-and-finalize.md` `## 1. Resolve open questions` contains "Resolve
questions already answered by authoritative evidence and cite it."; `spec-review.md` `### 3.1 Build the
question set` contains "Resolve from authoritative evidence first and cite the source". E-03's premise
that spec-review defers by reference is correct and is that file's stated law ("Anything else you find
duplicated here is a defect; fix it by deleting the copy"). The packaging claim is exact
(`pyproject.toml` `".aw/system" = "agent_workflows/_data/.aw/system"`), as is the `f9166bfb` precedent.

WHAT I FIXED. Five findings, and the two that matter most came from RUNNING things the plan reasoned
about. PR-001: E-02 left the executor a conditional ("by REFERENCE ... if the long form already defers
to it elsewhere") whose answer the plan had not measured. I measured it: that file has ONE cross-file
reference in 246 lines and none to `plan-review.md`, and it fully duplicates the sibling `### Decisions`
rule, so the conditional resolves to COPY and the plan now says so outright with the bundle's own
parity-pointer convention. PR-002 is the self-application one: E-01 point (3) tells a reviewer to fall
back on leaving the question `open` with `Blocking: yes`, and that instruction is only worth giving if
such a question actually holds the plan. I inserted one into this plan's own text and ran the real
linter: `conforming` -> `error` at ALL THREE checkpoints with `IPD-Q501`. Had that come back advisory,
the plan would have been prescribing a second undemonstrated mechanism in the very rule forbidding them.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. executability (an unresolved conditional handed to the executor) | Measured at review: `rg '\.\./\|\.md' .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md` -> ONE hit (line 231, `Read report-template.md in full and use it exactly.`); `rg 'plan-review/plan-review.md'` on that file -> no hits; it duplicates the `### Decisions` rule and the whole `### Reversible or not` section (lines 24, 27, 36, 45-65). Parity convention shown at `plan-review-long.md` line 93: "this is kept identical to the single-file `../plan-review/plan-review.md` per the parity note above" | **E-02 ASKED THE EXECUTOR TO DECIDE A QUESTION THE PLAN COULD HAVE MEASURED.** Its conditional ("by REFERENCE ... if the long form already defers to it elsewhere; otherwise copy the five points verbatim") is answerable in one command, and the answer is COPY: the long form defers to nothing and already duplicates the neighbouring shared rule. Leaving it open invited the reference branch, which would have made this the only bare cross-file reference in that file and would have read as an omission rather than a rule. Mildly ironic for a plan about resolving questions by measurement rather than description. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now mandates COPY, records the measurement that settles it, and requires the parity-pointer sentence in the shape `plan-review-long.md` already uses. Added as F-7. Raised and recorded as OQ-01 (resolved, non-blocking), and V-06 gains a negative control that FAILS if a bare reference is written there. |
| PR-002 | MEDIUM | IN-SCOPE | A. correctness / self-application (a prescribed fallback that was itself undemonstrated) | Executed at review against this plan's own text: inserting one `- Blocking: yes` / `- Status: open` question changed `ipd_lint.lint_file`'s disposition from `conforming` to `error` at `author`, `review-finalize` AND `pre-execution`, with `IPD-Q501: OQ-01: BLOCKING question is still 'open'. Ask the human and record the answer (run /askme ...)`. The `author`-onward reach is deliberate per the comment above that check: the `pre-execution`-only version was "measured insufficient on 2026-09-08" | **THE PLAN PRESCRIBED A FALLBACK WITHOUT DEMONSTRATING THAT THE FALLBACK BITES.** E-01 point (3) instructs a reviewer who cannot demonstrate a mechanism to leave the question `open` with `Blocking: yes`. If that were merely advisory, the rule would replace one hidden risk with another and a reviewer who believed it toothless would not use it. The plan asserted the route without evidence, which is precisely the failure mode it exists to eliminate; a rule that breaks its own standard invites exactly the dismissal it cannot afford. | C:Low; U:Low; S:Low; F:Medium (a fallback nobody trusts is not a fallback) but the FIX is Low (run it once, state it) | FIXED | Ran it. Goal gains a paragraph stating the escape route is demonstrated with the measured transition and diagnostic; E-01 point (3) now tells the reviewer WHY the branch bites (`IPD-Q501` at every checkpoint, so the plan cannot reach `approved`); recorded as F-4 with the measurement. |
| PR-003 | LOW | IN-SCOPE | G. executability / right-sizing | `aw ipd lint --phase author` advisory `IPD-Z602`: "E-04: action text may bundle multiple concerns (names multiple independent deliverables ... 3 clauses)". Reading E-04: one assertion set over `plan-review.md` (writable after E-01) bundled with two structurally different assertions over the long form and `spec-review.md` (writable only after E-02 and E-03) | **E-04 BUNDLED THREE FILES WITH DIFFERENT ASSERTION SHAPES AND DIFFERENT PREREQUISITES.** The single-file case asserts presence inside a section; the spec-review case must assert presence of a reference AND ABSENCE of a copy, an opposite-direction assertion; and its `Depends on` had to name all three edits, so the whole test waited on the last of them. Bundled, an executor can call E-04 done having written only the easy third. A maintainer's sizing signal is a finding to investigate, not to dismiss because the count lint passed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-04 (single-file, `Depends on: E-01`) and E-06 (the two siblings, `Depends on: E-02, E-03, E-04`), with the id assigned by `aw ipd sync --apply` (watermark 05 -> 06). E-04 gains a deterministic heading-boundary method instead of line numbers; E-06 requires the spec-review assertion in BOTH directions. The generated `TODO falsifiable evidence` in V-06 was replaced with two real negative controls. Advisory cleared at `review-finalize`. |
| PR-004 | LOW | UNDER-SCOPE | E. testing / C. architecture (two unstated risks around the new test) | (a) Concurrent plan `96xtmi` (srcguard-01, `- Status: to-review`) is deleting text-pinning tests under the maintainer's 2026-09-26 ruling; its `- Scope:` excludes "tests that read NON-production files (specs, workflow bodies, READMEs, the test module's own file) unless the census flags them as reading `agent_workflows/*`". (b) `rg 'question\|resolve' verify-execution.md` -> only its GO/NO-GO prose (line 154) and a corrective-plan clause (line 176); `rg 'Resolve.*question\|question set'` on `plan-review-long/01` and `/02` -> no matches, though `f9166bfb` touched all three | **TWO THINGS THE PLAN LEFT UNSTATED, ONE A RISK TO THE NEW TEST AND ONE A SCOPE DOUBT.** (a) E-04 creates a new test that reads shipped text at the same moment another plan is deleting tests that read shipped text; unless the exemption is written down, the next census could delete it or its author could re-litigate the question. (b) The plan asserts "Under-scope: none known" while the precedent it cites touched two files this plan omits, so a reviewer cannot tell whether they were considered or missed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (a) Added as F-8 with `96xtmi`'s scope line quoted; E-04 now requires the exemption in the test module's docstring; recorded as OQ-02 (resolved, non-blocking) INCLUDING the residual risk that `96xtmi` is not yet executed and its wording could change. (b) Added as F-6 with the measurements showing neither omitted file has a question-resolution step; the Scope check now says the completeness was CHECKED and names those files as deliberately out of the fence. |
| PR-005 | LOW | IN-SCOPE | B/F. honest documentation (a rule that could read as enforced) | `ipd_lint` computes `has_owner = bool(oq.get("Owner","").strip()) and oq.get("Owner","").strip().lower() != "none"`; `ipd_schema.open_question_error(blocking, status, has_rationale, has_owner)` receives only that BOOLEAN and never the owner VALUE; `ipd_authoring` seeds `- Owner: none`. So a false `Owner: maintainer` passes every mechanical check | **POINT (5) IS UNENFORCEABLE AND THE PLAN DID NOT SAY SO.** `Owner` is free text with no enum and no validation of who. A reviewer reading point (5) beside four other points, in a repository full of gates, may reasonably assume something checks it; F-2's measured violation on `vtkfq8` passed every gate precisely because nothing does. An instruction whose enforcement status is ambiguous is weaker than one that admits it is a human obligation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 point (5) now states plainly that NO GATE CHECKS IT, names the mechanism (`has_owner` as a bare boolean), and cites F-2 as the instance that survived because of it. Added as F-5, with the note that adding an `Owner` enum would be a schema change well outside this plan. Also surfaced in the approval gate's limits paragraph so a human approves knowing it. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-02 leaves "reference or copy" to the executor. Measure it, or let them decide? | MEASURE IT and mandate COPY plus a parity pointer. | (a) Leave the conditional: rejected, it is answerable in one command and the plan's own subject is resolving questions by measurement rather than description; leaving it would be a small instance of the defect under repair. (b) Mandate a bare REFERENCE for single-sourcing: rejected on evidence, that file references nothing else and already duplicates the neighbouring shared rule, so a lone reference would read as an omission and diverge from the bundle's demonstrated convention. (c) Copy with no pointer: rejected, the pointer is what makes a future divergence visible, which is the whole reason the two forms are "kept in deliberate parity". | `03-resolve-and-finalize.md`: one cross-file reference in 246 lines, none to `plan-review.md`; duplicated `### Decisions` + `### Reversible` sections; `plan-review-long.md` line 93's parity-pointer wording. | yes |
| D-2 | E-01 point (3) prescribes leaving a question `open` with `Blocking: yes`. Does that actually hold a plan, or is it advice? | RUN IT before shipping the instruction, and state the result inside the rule. | (a) Assert it from the workflow text: rejected outright, that is exactly the describe-instead-of-demonstrate move this plan forbids, and reviewing this plan any other way would be self-refuting. (b) Read `ipd_lint` and reason about it: rejected as insufficient, reading tells you a check exists while running tells you which checkpoints it reaches, and the `author`-vs-`pre-execution` distinction is the whole load-bearing part. (c) Soften point (3) to "consider leaving it open": rejected, weakening a fallback that measurably works would be the wrong correction. | Inserted a `Blocking: yes` question into this plan's own text: `conforming` -> `error` at `author`, `review-finalize`, `pre-execution`; diagnostic `IPD-Q501`; the comment above the check records the `pre-execution`-only version as "measured insufficient on 2026-09-08". | yes |
| D-3 | A new test reading shipped workflow text, while `96xtmi` deletes text-pinning tests. Proceed, drop E-04, or wait for that plan? | PROCEED, and write the exemption into the test's docstring plus an OQ recording the residual risk. | (a) Drop E-04: rejected, the rule then ships with nothing proving it is installed, and the plan's whole premise is that unverified claims rot. (b) Add an `Item-Dependencies` edge on `96xtmi`: rejected, there is no dependency in either direction (that plan's census excludes workflow-body readers by its own scope) and a false edge would delay this plan for nothing. (c) Claim the exemption silently: rejected, a future census reader would have to re-derive it; one docstring sentence removes that cost. | `96xtmi` `- Scope:` excludes "tests that read NON-production files (specs, workflow bodies, READMEs ...) unless the census flags them as reading `agent_workflows/*`"; E-04 reads a workflow body and no `agent_workflows/*`; `96xtmi` is `to-review`, hence the recorded residual risk. | yes |
| D-4 | The `citesym` precedent touched `verify-execution.md` and `plan-review-long/01`-`/02`, which this plan omits. Widen the scope? | NO. Verify they carry no question-resolution step, record the check, and name them as deliberately out of the fence. | (a) Widen to match the precedent file-for-file: rejected, a precedent is a list of files that needed THAT change, not a fixed set; adding a feasibility rule to a workflow with no question-resolution step would put an inapplicable instruction in front of a reader. (b) Say nothing and keep "Under-scope: none known": rejected, a reader comparing against the cited precedent cannot tell considered from missed, and "none known" is a weaker claim than "checked". | `rg 'question\|resolve' verify-execution.md` -> lines 154 and 176 only (GO/NO-GO prose, corrective-plan clause); `rg 'Resolve.*question\|question set' 01-discover-and-snapshot.md 02-review-and-revise.md` -> no matches; `git show f9166bfb --stat`. | yes |

### Deferred and open

- (none). All five findings were FIXED in place. No finding reached the repository's gate threshold
  (`HIGH`), so no escalated `- Blocking: yes` question is owed. The plan's two open questions (OQ-01 and
  OQ-02, both raised at review) are `resolved` and non-blocking. No `Reversible: no` decision was taken,
  so no escalation is owed. The plan's two `Carrier-Declined` deferrals were examined and both stand: the
  no-lint-rule decline cites spec `ipd-structure-and-linting` Section 7 accurately (verified: the quoted
  sentence "The linter checks the declared fields and their consistency. The semantic reviewer decides
  whether the author's `Blocking:` classification is credible." sits under `## 7. Blocking-question
  grammar`), and the no-retroactive-sweep decline is a scope decision with the one measured instance
  already re-ruled.

HONEST LIMITS, stated because they bound what this round proves. I verified the `vtkfq8` case verbatim,
all three insertion points, the packaging claim, the precedent, the spec citation, the `Owner`
non-enforcement, the scope completeness across the bundle, and (by running the linter) that the
prescribed fallback bites. I did NOT write any workflow text or the test, so that the five points are
well drafted, that the anchor phrases the test pins are the right ones, and that both negative controls
genuinely fail remain E-01..E-06's work and V-01..V-06's evidence. The deepest limit is one no review
can close: this plan changes an INSTRUCTION, and an instruction's effect depends on agents following it.
Nothing here measures compliance, and the plan is honest that no lint rule can judge whether a pasted
demonstration is real, so the mechanism of action is reviewer discipline plus the now-demonstrated
`IPD-Q501` stop on the fallback path. I ran the bare suite once for the `2501 passed, 2 skipped in
59.95s` baseline and did NOT run the slow set (`make test-all`); for a documentation change that is
proportionate but it is a hole, not a clearance. Finally, my `96xtmi` exemption reading is of a plan that
is `to-review` and could still change; that risk is recorded in OQ-02 rather than resolved.
