# Review findings: plan mg8bag

- Subject-Id: mg8bag
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-201 (BLOCKER, fixed), PR-202 (HIGH, fixed), PR-203 (MEDIUM, fixed), PR-204 (MEDIUM, fixed), PR-205 (HIGH, fixed), PR-206 (HIGH, fixed), PR-207 (MEDIUM, fixed), PR-208 (LOW, fixed), PR-209 (LOW, fixed)

## Round 1

Reviewed at HEAD `c82c829d8` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review; `--phase review-finalize`
reports `conforming` after revision. The plan is `- Kind: child`, so the `IPD-S407` orchestrator row check
does not apply. No research doc was moved, no citation repaired, and no production file or test modified by
this review.

THE PLAN'S CENTRAL MEASUREMENT IS EXACT AND I RE-DERIVED ALL OF IT RATHER THAN SPOT-CHECKING. Driving
`research_contract.normalize_status` and `research_archive.plan_transition` over the tree reproduces every
figure: 126 docs under the research tree, 61 at the hot root, 35 of those cold, ALL 35 `reference` with
NONE `archive` (so F-02's correction of the backlog item holds and no `archive/` shard is created), targets
`reference/202607` (18) / `reference/202608` (14) / `reference/202609` (3), zero `plan_transition` errors,
zero hot-status docs inside a cold shard, and 11 of the 35 carrying a `created` month that diverges from
their filename month. E-01's 35-id list matches my own derivation character for character. F-08's
mechanism is right and matters: `_shard_subpath` passes `created` to `shard_for_date`, so a
`reference/202608` target for a `20260731-` file is correct and "fixing" it would mis-shard 11 docs.
F-03's quoted concession in `apply_moves` is verbatim ("if a full-path cite exists it is caught by the
dangling detector") and the claim it makes is indeed FALSE for a tier move, because the basename is
unchanged so id6 resolution still succeeds. F-10's three named examples all check out (`bu9yij`, `27rjro`,
`i5gj61` each live in a `reference/` shard while cited at root paths). F-11 holds exactly: zero pending or
reusable plans name a cohort doc in `- Scope-Paths:`.

THEN I CHECKED THE ONE THING A CORPUS-MIGRATION PLAN IS MOST EXPOSED TO, which is whether the world moved
under it between authoring and review. It did, and that is this review's central finding.

APPROVED PLAN `68hdic` HAS EXECUTED. It is now `- Status: executed` under `.aw/records/plans/executed/`
(finalize commit `a7f0ce4f1`), and it already performed its own E-05: `agent_workflows/comms.py` carries
ZERO occurrences of the retired `.agents/docs/research` form and instead names `j2000q`'s current ROOT
path, which resolves on disk today. Three of this plan's statements are false as a consequence, and the
worst of them is dangerous rather than merely stale. `- Scope-Paths:` declared `68hdic` at a
`.aw/records/plans/pending/...` path that NO LONGER EXISTS. E-06 instructed an executor to rewrite 3
occurrences inside it. And E-05 described a pre-existing dangling `.agents/` citation that is already
gone. So an executor following this plan unrevised would have gone looking for a file at a path that
cannot resolve and, on finding it in `executed/`, would have been instructed by its own plan to rewrite an
immutable record, which is the edit the execution contract most firmly forbids. The plan is explicit
elsewhere that this is forbidden (its own conventions section and two Carrier-Declined rows say so), so
this is a stale-fact defect rather than a judgement error, but the instruction was there to be followed.

THE REPAIR SET IS ALSO SMALLER THAN THE PLAN BELIEVES, AND I RE-MEASURED IT RATHER THAN SCALING THE
AUTHORED NUMBER. Searching the whole tracked tree outside the research directory for each cohort doc's
full path: 7 cohort docs are cited by full path (authoring said 14) across 12 files (said 11) holding 24
occurrences (said 16 immutable plus some). Of the 12, TEN are immutable (9 executed plans plus 1 review
record) and exactly TWO are live: `comms.py` (`j2000q`, 1 occurrence) and pending `h8e3sm` (`en5c8i`, 1
occurrence). So the live repair set is 2 occurrences in 2 files where the plan said 3 in 3. The authored
figures were correct when written; `68hdic`'s execution moved one file from the live set to the immutable
set and added its review record to the census. This is exactly the drift E-01 and E-02 were designed to
catch, which is why the fix is to harden their re-derivation rather than to substitute my numbers as a new
bar.

ONE VALIDATION BAR WAS A DRIFTING POPULATION PINNED AS A CONSTANT. E-07's design is the plan's single best
decision: it recognizes that `aw research index --check` already exits 1, so an exit code proves nothing,
and compares GROUPED per-rule counts instead. But it then quotes an authoring baseline (61
`dangling-citation`) as the figure to re-derive against. Re-measured, `dangling-citation` is 70, while
`adopted-without-consumer` (35) and `stale-state-to-promote` (17) reproduce exactly and
`check.stale-index-missing` no longer appears. A nine-finding drift in one day on an unrelated rule family
is precisely why the DELTA between the executor's own two measurements is the only meaningful quantity,
and a quoted before-count would have read as a STOP condition when it is just normal churn.

Two things the plan gets right that deserve recording, because both are the kind of judgement that is
easy to get wrong in the opposite direction. First, its refusal to add an automated test is correct and
well-argued: a test asserting "this repository's corpus has zero stranded docs" is a corpus-census test,
which is the code-pinning shape AGENTS.md P16 forbids, and the durable guard genuinely does belong to
sibling `ucwlwt`'s fixture-tested checker rule. Second, its `- Work-Kind: chore` inheritance survives
scrutiny on the repository's own perceptibility test: readers key on frontmatter `status` rather than
path, so no answer a user receives is wrong, `zdsf35` carries no `- Blocks-Release:`, and the gating set
is `bug` alone. I specifically considered whether a mis-tiered corpus is user-perceptible and concluded it
is not, since nothing a user runs returns a different answer.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | BLOCKER | IN-SCOPE | D (invariants), G (executability) | `68hdic` is `- Status: executed` at `.aw/records/plans/executed/20260929-zftbta-01-68hdic-...ipd.md` (finalize commit `a7f0ce4f1`); the `plans/pending/` path in `- Scope-Paths:` does not resolve; `grep -c "\.agents/docs/research" agent_workflows/comms.py` -> 0 | E-06 instructs rewriting 3 occurrences in `68hdic`, which has EXECUTED and is immutable. `- Scope-Paths:` declares it at a nonexistent pending path, and E-05 describes an `.agents/` citation already removed. Unrevised, the plan directs an executor at the edit the execution contract most firmly forbids | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 rewritten to cover `h8e3sm` only, with an explicit prohibition on touching `68hdic`; E-05 recast as the settled "ran first" case and told the `.agents/` form is already gone; F-05 rewritten; the `68hdic` path removed from `- Scope-Paths:` (PR-206); V-05/V-06, Proposed-change 6, Scope check and the gate all swept |
| PR-202 | HIGH | IN-SCOPE | E (evidence accuracy) | Re-measured across the tracked tree: 7 cohort docs cited by full path, 12 citing files, 24 occurrences; 10 immutable (9 executed plans + 1 review), 2 live (`comms.py`, `h8e3sm`) | F-04 and E-02 record 14 docs / 11 files / 9 immutable / 2 live pending, and E-06 derives a 3-occurrence repair set from it. The true live set is 2 occurrences in 2 files | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 and E-02 carry both measurements with the reason they differ (`68hdic` executed); E-02 now explicitly refuses to reconcile to EITHER figure and must report what it measures; E-06 and V-06 corrected to one occurrence |
| PR-203 | MEDIUM | IN-SCOPE | F (recorded decisions) | Same as PR-201: `68hdic` executed at `a7f0ce4f1` | OQ-01 is phrased as "RESOLVED as EITHER ORDER", which told a reader an ordering choice still exists. It does not; the question is settled by event | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 now leads with the settled fact and names the two facts an executor must take as given, while retaining the original reasoning because making both orders safe is what kept the consequence cheap |
| PR-204 | MEDIUM | IN-SCOPE | A (correctness), G | E-02's LIVE list enumerates `plans/pending/`, `backlog/open/`, `specs/`, source; the backlog tree also has `graduated/`, `blocked/`, `parked/` states | The classification is two enumerated lists, so a citing file in an unanticipated location (for example `backlog/graduated/`) gets no disposition and an executor must guess, on a question where guessing LIVE risks falsifying a record | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 restated as a RULE: a named immutable set, everything else live, and a fail-safe instruction to classify IMMUTABLE and report when neither clause fits cleanly |
| PR-205 | HIGH | IN-SCOPE | E (validation), G (live-artifact criteria) | Re-measured `aw research index --check`: 70 `dangling-citation` (authoring: 61), 35 `adopted-without-consumer`, 17 `stale-state-to-promote`, no `check.stale-index-missing`; exit 1 | E-07 and F-06 quote authoring finding counts as the baseline to re-derive against. They are a LIVE population that drifted by 9 in one day, so a differing before-count would read as the STOP condition E-07 defines | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now requires the executor's OWN before/after pair captured in one session and compares the DELTA, with every quoted figure labelled orientation-only and a differing before-count explicitly NOT a stop; F-06 carries both measurements and the live-population warning |
| PR-206 | HIGH | IN-SCOPE | G (scope fence) | `- Scope-Paths:` names `.aw/records/plans/pending/20260929-zftbta-01-68hdic-...ipd.md`, which does not exist; `aw ipd finalize --scope-ack` exists for declared-but-unmodified paths | A declared path that cannot resolve and names a file the plan must NOT modify would force a `--scope-ack` at finalize for a file whose correct disposition is "never touch", muddling the fence that exists to catch real drift | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The entry REMOVED rather than repointed at `executed/`, since repointing would declare intent to edit an immutable record; E-05/E-06 state the prohibition in prose instead, and V-06 requires the executed plan to appear in the zero-diff immutable set |
| PR-207 | MEDIUM | IN-SCOPE | A (data integrity) | `research_archive.apply_moves` regenerates `INDEX.json`/`INDEX.md` on disk and omits them from `touched`; both gitignored; E-04 commits the broad path `.aw/records/research` | The manifests are a side effect of `--apply` while the commit path is a whole directory, so the no-staging rule needed an explicit pre-commit verification step rather than a note | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A dedicated gate paragraph requires `git diff --cached --name-only` before the commit completes, citing the 2477-line conflict the README records; V-04 already demanded the evidence and now has an instruction producing it |
| PR-208 | LOW | IN-SCOPE | E (evidence precision) | V-06 expects "3 occurrences in `68hdic`, 1 in `h8e3sm`" | Expected counts derived from the pre-`68hdic`-execution world; an executor finding 1 would have reported a divergence that is not one | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-06 expects ONE occurrence, names the correction, and requires the executed plan and its review in the zero-diff set |
| PR-209 | LOW | IN-SCOPE | E (citation hygiene) | Plan cites `HEAD 7000df73`; review HEAD is `c82c829d8` | Authoring commit written as though current | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-01, E-01 and the history line relabel it the authoring commit and name the review commit beside it, recording that every figure reproduced |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `68hdic` has executed, so E-06's instruction to edit it is now forbidden. Drop it from this plan, repoint it at the `executed/` path, or file a corrective plan? | Drop `68hdic` from E-06 and from `- Scope-Paths:` entirely, and state the prohibition in E-05/E-06 prose | (a) Repoint the citation at `.aw/records/plans/executed/...`: REJECTED, because declaring an executed plan in `- Scope-Paths:` asserts intent to modify an immutable record, which is the violation itself; the path's absence from the fence is what makes the attempt refuse. (b) File a corrective plan for `68hdic`'s now-stale internal citation: REJECTED, because nothing is broken that may be fixed; its citations were correct when written and AGENTS.md permits only an appended history line, which this plan has no reason to add. (c) Leave E-06 and trust the executor to notice: REJECTED, because the plan's own text would be instructing the violation | AGENTS.md "Never change what a plan already in `.aw/records/plans/executed/` RECORDS"; `68hdic` measured at `- Status: executed` with finalize commit `a7f0ce4f1`; the plan's own two Carrier-Declined rows already state the same prohibition as a positive contract | yes |
| D-2 | The authored citation census (14 docs / 11 files / 3 live) is stale. Substitute my re-measured numbers as the plan's figures, or harden the re-derivation? | Record BOTH measurements with the reason they differ, and make E-02 refuse to reconcile to either | (a) Replace the authored numbers with mine: REJECTED, because mine will be stale too; the population already moved once between authoring and review and the execution turn is a third moment. Pinning a fresh number repeats the defect with a newer value. (b) Delete the numbers entirely: REJECTED, because a census with no expectation gives the executor nothing to notice a surprise against; the value is in the DIVERGENCE being visible and explained | Measured 7 docs / 12 files / 24 occurrences / 10 immutable / 2 live against the authored 14 / 11 / 16 / 9 / 2, with `68hdic`'s finalize commit explaining the shift; the plan-review convention on live-artifact criteria requires a property plus re-derivation rather than a measured count as the bar | yes |
| D-3 | Does `68hdic` having executed invalidate the plan's approach, or only its records? | Only its records; the approach stands and the revisions are bounded | (a) REPLAN: REJECTED. The migration mechanism (tool-owned `promote --apply`), the ordering argument behind the two-child Set, the citation-classification design, and the grouped-count validation are all unaffected; what changed is which files are live. (b) Add an `Item-Dependencies` edge on `68hdic`: REJECTED as meaningless now, since it has already executed and an edge would be satisfied by construction while implying a constraint that no longer binds | OQ-01's own resolution anticipated this exact branch and made both orders safe, so the consequence is a records correction; the cohort census, `plan_transition` targets, and F-11's no-scope-collision finding all re-measured unchanged | yes |
| D-4 | Is the inherited `- Work-Kind: chore` right, given the tree's physical layout contradicts its own documented invariant? | Concur with `chore`; no release gate attaches and none is invented | (a) Reclassify `bug` with `- Blocks-Release: next`: REJECTED. The repository's perceptibility test asks whether a user notices, and every reader keys on frontmatter `status` rather than path, so no answer anyone receives is wrong; a mis-tiered corpus is untidy, not incorrect. (b) Raise it to the maintainer: NOT taken, because the item's author recorded the reasoning explicitly against the stated test and measurement confirms it | `zdsf35` carries no `- Blocks-Release:`; AGENTS.md gating set defaults to `bug` alone; `.aw/records/research/README.md` declares frontmatter status authoritative, which is what makes the layout cosmetic | yes |

### Verdict

APPROVE WITH REVISIONS APPLIED. Nine findings, all FIXED in place, none deferred, none left open. The
BLOCKER (PR-201) was a stale-fact defect that would have directed an executor to rewrite an immutable
executed plan; it is repaired by removing that plan from both the scope fence and the repair item. No
unfixed finding at or above the `HIGH` gate threshold remains, so no escalation to a `- Blocking: yes`
question is owed. The single pre-existing open question (OQ-01) stays `- Blocking: no` and `- Status:
resolved`, now recording a settled fact rather than an open ordering choice. `- Readiness:
go-pending-approval` written; `- Status:` to be set `reviewed` through `aw ipd set` so the transition is
tool-attributed. Human approval is still required before execution.
