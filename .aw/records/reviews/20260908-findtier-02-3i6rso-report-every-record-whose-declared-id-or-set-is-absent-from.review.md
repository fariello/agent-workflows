# Review: report every record whose declared Id or Set is absent from its filename, child 3i6rso (Set findtier)

- Subject-Id: 3i6rso
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 2

Reviewed at HEAD `985bc263`. Structural preflight `aw ipd lint --phase author` CONFORMED with zero findings
before semantic review, and `--phase review-finalize` CONFORMED after every revision. No open questions
remain. No product code was modified by this review.

PROVENANCE THIS ROUND MUST RECORD, because this file is a REPLACEMENT for a deleted one. A Round 1 review
was committed in `6cb837ad` (plan hardened, 111-line typed record written) and then REVERSED less than an
hour later in `77384e9c`, which rolled `Status: reviewed` back to `to-review`, stripped the `Readiness`
attestation, deleted the review record, and removed the review's history entry. That commit's own message
records it was made at the maintainer's explicit instruction, after the committing agent flagged that it
destroyed completed review work; the deleted record remains recoverable at `6cb837ad`. Round 1's findings
(F-12 through F-14) survive inside the plan body, so this round RE-VERIFIED them from the repository rather
than trusting them, and numbers this round is the first to state are labelled as such.

DISCLOSURE: the plan was authored by the same model family, so this is close to a self-review and is worth
less than an independent one. Its value rests on what was EXECUTED. Things run: a full-corpus scan for
declared-Id-absent-from-filename at BOTH a bounded 4096-byte window and full body, in BOTH front-matter
dialects; the same scan for `- Set:`; `check_engine.RULE_REGISTRY` read for the identity-slot rule's four
registration facets and for the severity census; `_is_real_id6` and `_check_identity_slots` read in full;
`_is_real_id6` evaluated directly on `assess` and on a real id6; `check_collisions` read to confirm it reads
whole files; `aw check all --agent` parsed per rule; `aw check all` exit code taken unpiped; `aw check specs`;
`aw rename --help` grepped for `--to-id6`; the bare suite; `tests/test_reporting_contract.py` alone;
`git check-ignore` on `opencode-recovery`; `25kzda` citations counted; the git history of both this plan and
its sibling; `76w6mq`'s current status; and a re-scan of every pending plan declaring `check_engine.py`.

THE PLAN'S CORE DESIGN IS SOUND AND IS THE STRONGER HALF OF THIS SET, which is worth saying plainly because
its sibling did not fare as well. Round 1's central insight re-verified in every particular:
`check.id6-identity-slot` is registered exactly as described, its rule (a) is already the comparator E-01/E-02
proposed to build, and its discriminator is a named shared helper rather than inline logic. The instruction to
REUSE that helper is now verified rather than argued, which is stronger than Round 1 left it:
`_is_real_id6('assess', declared_ids)` returns False (all letters, undeclared) while `_is_real_id6('826o13',
...)` returns True, so calling it genuinely fixes the F-13 mis-bucketing hazard instead of merely avoiding
duplication. The `- Id:` count of TEN reproduced exactly, and the warning-severity precedent reproduced
exactly: 6 warning, 24 error, 2 info, with all six named rules present. F-7's vacuity finding also stands,
since `aw check all` still exits 1 unpiped.

THE FINDING THAT MOST CHANGES THE PLAN IS A NEW ARTIFACT MEMBER THAT BREAKS THE BUCKET'S ASSUMED SHAPE. The
`- Set:` case is EIGHT, not the seven Round 1 measured, and the eighth is `aw-delivery`, declared at
`.aw/records/specs/20260730-2152-01-agents-artifact-organization.spec.md:198` INSIDE a fenced block captioned
"Frontmatter schema (authored/tool-written; the source of truth)". That is the same quoted-example class as
`uyeko5` and `runflags`, but reached through a SPEC and through the `set:` field rather than a research
document and `- Id:`. So the parser-artifact bucket has FIVE members spanning TWO fields and THREE record
types. This matters concretely rather than as a count correction: a classifier keyed on "research documents"
or on "the `- Id:` field", which both the plan's prose and its fixture list invite, would have caught the
`uyeko5` pair and MISSED this one, then emitted a rename suggestion against an `implemented` spec whose
filename is correct. The plan's own instruction to code bucket (b) as a CLASS was right; this measurement
shows the class test must be POSITIONAL (inside a fenced block / outside the metadata region), which is
exactly what `76w6mq` bounds.

FOUR RECORDED FACTS WENT STALE IN THE ~24 HOURS BETWEEN ROUNDS, AND ONE OF THEM WOULD HAVE INVERTED A TEST.
`check.id6-identity-slot` now emits ZERO findings, not 2; the two Round 1 saw have been resolved. E-05 and
V-04 instruct the executor to prove that count "MUST NOT CHANGE", so an executor holding a baseline of 2 would
read a correct 0 as a regression and chase it. Alongside it: `aw check` total 170 -> 169,
`check.setid-collision` 86 -> 38 with `check.scope-drift` now dominant at 110, and the suite `5929` -> `5958
passed`. The corrective is not to write newer numbers and stop, since these will drift again, so every
count-bearing instruction now tells the executor to measure its own and records that these figures have
already moved once. That is the durable fix.

THE SIBLING PARAGRAPH CITED NUMBERS NO REVIEW PRODUCED. It claimed Order 01's resolver is "12% of end-to-end
cost (54ms of 456ms)" and that its benchmark "times a filename search that returns ZERO results". Measured:
the resolver is ~42.5ms of ~450ms (~9%), of which only ~12.8ms is removable by its filter, about 3% of the
wait. And the benchmark criticism is sharper than stated: `find .aw/records -iname '*lus9ou*'` returns ZERO
files while `aw find plans lus9ou` correctly returns ONE, so it compares a MISS against a HIT rather than
merely returning nothing. The paragraph's CONCLUSION survives intact and is if anything reinforced, since
Order 01 now carries a blocking OQ-03 and `Readiness: no-go`; the independence claim is structural (disjoint
`Scope-Paths`, no dependency edge) and I verified it.

ONE CROSS-SIBLING AMBIGUITY IS NOW EXPLAINED RATHER THAN LEFT LOOKING LIKE A DEFECT. This plan says TEN while
`826o13` says NINE, and a reader comparing them would reasonably try to "fix" one. Measured both ways: a
bounded 4096-byte header scan finds nine, a full-body scan finds ten, the tenth being the second `uyeko5`
quotation beyond the window. Nine is correct for a RESOLVER reading `_HEADER_BYTES` (`selectors.py:317`); ten
is correct for a REPORT, and `check_collisions` (which this plan extends) reads whole files with an unbounded
`p.read_text()`. Both plans now state their window when citing a count.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | UNDER-SCOPE | A. Correctness / G. Plan executability | `.aw/records/specs/20260730-2152-01-agents-artifact-organization.spec.md:198` | A FIFTH PARSER-ARTIFACT MEMBER BREAKS THE BUCKET'S ASSUMED SHAPE. The `- Set:` case is EIGHT, not seven; the eighth is `aw-delivery` declared inside a fenced "Frontmatter schema" block in a SPEC. So the artifact class spans two fields and three record types, not a research-only `- Id:` pair. A classifier keyed on type or field (which the plan's prose and fixture list invite) would miss it and suggest renaming an `implemented` spec whose name is correct. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Concern, E-01, E-02, F-3, F-8, new F-16, conventions, Required tests and the execution contract all updated: bucket (b) must be detected POSITIONALLY, the count is eight, the third file is named as a must-not-report, and the class is described as spanning both fields and three types. |
| PR-202 | MEDIUM | IN-SCOPE | E. Testing and verification | `aw check all --agent` parsed per rule; bare suite | FOUR CITED BASELINES WENT STALE IN 24 HOURS AND ONE WOULD INVERT A TEST. `check.id6-identity-slot` now emits ZERO findings, not 2, while E-05/V-04 demand proof the count "MUST NOT CHANGE", so a stale 2 makes a correct 0 look like a regression. Also: `aw check` total 170 -> 169, `check.setid-collision` 86 -> 38 (`check.scope-drift` now dominant at 110), suite `5929` -> `5958 passed`. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New F-15; Concern, E-06, E-05, conventions, Required tests and the execution contract now carry the re-measured figures AND an explicit instruction to measure your own and never assert against a count recorded in the plan, since these have already drifted once. |
| PR-203 | MEDIUM | IN-SCOPE | G. Plan executability | timed at review; `find`/`aw find` run | THE SIBLING PARAGRAPH CITES NUMBERS NO REVIEW PRODUCED: "12% of end-to-end cost (54ms of 456ms)" and a benchmark returning "ZERO results". Measured: ~42.5ms of ~450ms (~9%) with only ~12.8ms removable (~3% of the wait), and the benchmark compares a filename search returning ZERO files against an `aw find` correctly returning ONE, i.e. a miss against a hit. The paragraph's conclusion is correct but its evidence was not. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-17; the gate paragraph rewritten with the measured decomposition, the accurate miss-versus-hit statement, Order 01's current `no-go` and blocking OQ-03, and the structural basis for the independence claim. |
| PR-204 | LOW | IN-SCOPE | C. Architecture and operability | `Scope-Paths` re-scan | THE CONCURRENT-EDIT LIST IS STALE AND UNDERSTATED: the plan names four other pending plans editing `check_engine.py`; twelve declare it, `dw7i3m` is NOT among them, and `76w6mq` - whose bounded reader E-02 wants to consume - IS one of them, which the plan does not connect. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-18; the concurrent-edit note and the execution contract now list all twelve, drop `dw7i3m`, and flag that `76w6mq` edits the same file whose reader E-02 consumes. |
| PR-205 | LOW | IN-SCOPE | G. Plan executability | both scans run at review; `selectors.py:317` | THE TEN-VERSUS-SIBLING'S-NINE DIFFERENCE READS AS A DEFECT AND IS NOT ONE. A bounded 4096-byte header scan finds nine, a full-body scan finds ten. Unexplained, a reader "corrects" one plan to match the other and breaks whichever was right for its own reader. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now mandates full-body scanning WITH the window stated, F-2 records both numbers and why each sibling is right, and Required tests plus E-05 require the window be stated with every cited count. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Round 1's review was deleted at the maintainer's instruction. Redo the review from scratch, or treat Round 1's in-body findings as given? | Re-verify every Round 1 claim from the repository, write a Round 2 record, and label what this round measured first. | Trust the in-body findings and review only what changed (rejected: the record that attested them was deleted, so nothing external vouched for them; and re-verification found four stale counts and one new bucket member, which trusting would have missed); treat the plan as unreviewed and ignore the surviving findings (rejected: wasteful, and the findings proved largely correct). | `77384e9c`'s commit message recording the reversal and its instruction; `6cb837ad` holding the deleted record; workflow rule to verify claims from repository evidence. | yes |
| D-2 | Is the `- Set:` seven-versus-eight difference a scan error to reconcile, or a real new member? | A real new member (`aw-delivery`), and a fifth member of the artifact class. | Assume a scan-methodology difference and keep seven (rejected: I read the file and the declaration is at line 198 inside a fenced schema block, so it is genuinely present and genuinely an artifact); treat it as genuine drift needing a rename (rejected: that is precisely the damage bucket (b) exists to prevent, against an `implemented` spec). | The spec read directly at `:198` with its fenced-block caption; the same positional pattern as `uyeko5`/`runflags`. | yes |
| D-3 | Should this plan's TEN be reconciled with sibling `826o13`'s NINE? | No: document both windows and why each is right for its own reader. | Change this plan to nine (rejected: a report reads whole files, and `check_collisions` already does, so nine would undercount here); change the sibling to ten (rejected: out of scope for this review, and nine is correct for a resolver bounded to `_HEADER_BYTES`). | Both scans run at review; `selectors.py:317`; `check_collisions`'s unbounded `p.read_text()`. | yes |
| D-4 | Round 1 resolved OQ-01 to a sweep rule partly on the `- Set:` count being seven. Does eight reopen it? | No: re-confirm the same answer on the new number and record that it did not change the outcome. | Reopen OQ-01 as blocking (rejected: eighteen combined findings against an existing 169 is materially the same judgement as seventeen against 170, and the plan's own stated reopen threshold is "materially more"); silently update the number without re-testing the reasoning (rejected: the reasoning is what makes the resolution checkable). | Re-measured counts: 8 + 10 = 18 against 169 total, versus `check.scope-drift` 110 and `check.setid-collision` 38. | yes |
