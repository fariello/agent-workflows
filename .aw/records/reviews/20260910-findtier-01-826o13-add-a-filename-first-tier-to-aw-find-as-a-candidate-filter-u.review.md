# Review: add a filename-first tier to aw find as a candidate filter, child 826o13 (Set findtier)

- Subject-Id: 826o13
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `985bc263`. Structural preflight `aw ipd lint --phase author` CONFORMED with zero findings
before semantic review. At `--phase review-finalize` the linter reports ONE finding, `IPD-Q501`, because this
review ESCALATED OQ-03 to `Blocking: yes`; that refusal is the intended gate firing, not an unrepaired
structural defect, and it is why readiness is `no-go`. No product code was modified by this review.

DISCLOSURE: the plan was authored by the same model family, so this is close to a self-review and is worth
less than an independent one. Its value therefore rests on what was EXECUTED rather than reasoned. Things
run: `aw find` timed unpiped as a subprocess and warm in-process; `_iter_paths` timed with zero reads;
`_read_header` timed over all candidates and over the filtered subset; `Path.open` instrumented separately
for the resolver and for `plans_index.scan_plans`; `_read_header` instrumented per query kind for all five
kinds; a full-corpus scan for declared-Id-absent-from-filename at BOTH a bounded 4096-byte window and full
body, and in both front-matter dialects; the same scan for `- Set:`; `parse_clustered` and `ID6_RE` on three
legacy names; a SIMULATED quoting normalization with before/after resolution; `aw find` run for `lus9ou`,
`wtiso`, `y6mfgo`, `awoptimize` on two types; `find -iname` for `lus9ou`, `approved`, `wtiso`; the bare
suite; `tests/test_orchestrator_retirement.py` alone; `check.id6-identity-slot`'s registered severity; the
source backlog item's front matter; and a re-scan of pending `Scope-Paths` declaring `selectors.py`.

WHAT THE PLAN GOT RIGHT, and it is most of the hard part. Every one of its own guardrails re-verified true.
The mandatory fallback's two reasons hold exactly as filed: `-iname '*approved*'` returns 5 files of which 0
are approved against 17 real ones, and records genuinely carry a declared identity absent from their
filename including `25kzda`. The artifacts-not-references contract re-measured as claimed and is stronger
than filed: 17 filename hits for `wtiso` against 3 correctly resolved. `y6mfgo` resolves to one artifact
while 10 plans mention it. The inherited correction is real, `PrecedenceForcesFrontMatterReadsTests` says
what the plan says it says, and choosing a candidate FILTER over a precedence change is the right call for
the right reason. The plan's instinct to distrust its own predecessor's speed argument was also right; it
simply did not carry that distrust far enough to measure the decomposition before designing.

THE FINDING THAT RE-SCOPES THE PLAN IS THAT ITS PRIZE IS ~3% OF THE WAIT. The plan's Concern leads with a
"70x gap", which is true of the COMMAND but attributes to the resolver a cost that is mostly not the
resolver. Decomposed: of ~450ms for a subprocess `aw find plans <id6>`, interpreter start plus
`import agent_workflows.cli` is ~115ms, the resolver TOTAL is ~42.5ms, and the display layer's
`plans_index.scan_plans` is ~113.6ms, re-reading all 616 records the resolver just read (616 opens each,
1232 end to end, reproducing `e32j35`'s 938-across-469 at today's size). Inside the resolver, TRAVERSAL is
~29.5ms, 69% of it, and a filename filter cannot touch it; the header reads this plan removes are ~13.4ms,
and after the filter's own `parse_clustered` overhead the NET prize is ~12.8ms. The display layer alone is
8.9x the prize. OQ-03 asked precisely this and was authored `Blocking: no` on the premise that only a
measurement could decide; the measurement now exists and it argues against the plan's own stated rationale,
so the question is escalated rather than left for an executor to rediscover mid-run and resolve alone.

TWO DESIGN DEFECTS SURFACED ONLY BY RUNNING THE CODE, and both would have failed mid-execution. FIRST, E-03
named three filterable kinds (`id6`, `stem`, `substring`); instrumenting `_read_header` shows all five kinds
read all 616 headers today, because `setid` and `status` are precedence 3 and 4 while the filename rules are
5 and 6, so by the time a `stem` or `substring` rule runs the full read is ALREADY PAID and filtering it
saves exactly zero while costing a parse per candidate. Only `id6`, at precedence 2, can benefit. The plan's
own cited proof implies this and the plan did not carry the implication into its design. SECOND, E-04 and
E-05 were mutually unsatisfiable: normalizing the backtick-quoted `` - Set: `awoptimize` `` makes that record
match the `setid` rule, and `setid` outranks `substring`, so `aw find research awoptimize` goes from FOUR
files to ONE. E-05 demands identical before/after resolution and the Scope forbids changing which record
wins, so an executor doing both would have had no correct move. E-04 is inverted to a characterization test
pinning today's behavior, with the normalization handed to Order 02 where it is report-only.

THREE SAFETY CORRECTIONS TO THE FILTER, each measured rather than argued. The exception set must be COMPUTED
at runtime via `parse_clustered` (4 of 616 candidates, 0.6%) and never written as a hardcoded list of nine,
or the first legacy record added afterwards is silently dropped, which is the exact correctness bug the
superset rule exists to forbid. The token must be matched against the WHOLE FILENAME and never the parsed
identity slot, because `parse_clustered` returns conformant with `id6='assess'` for
`20260817-1357-01-assess-bugs-...` whose real declared Id is `wvlk84`, and `ID6_RE.match('assess')` is True;
this is Order 02's own F-13 hazard reaching Order 01, which neither plan had connected. And E-05's
differential must span all ten record types, not plans, since `resolve` is the single resolver every verb
routes through, and must compare the winning KIND as well as the path set, because F-15 is precisely a case
where the kind flips.

TWO RECORDED FACTS WERE STALE, both in ways that would have misled the executor. The suite baseline
`1 failed, 5648 passed` blames `tests/test_orchestrator_retirement.py`; measured, the suite is
`1 failed, 5958 passed, 3 skipped, 2 xfailed`, the failure is
`test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, it is an
ENVIRONMENTAL artifact of an untracked local `opencode-recovery/` tree of 1746 files in this shared checkout,
and `test_orchestrator_retirement.py` passes 112 tests. An executor comparing against the authored baseline
would have chased a code defect that does not exist while treating a real one as expected.

THE NINE-VERSUS-TEN DISCREPANCY WITH ORDER 02 IS NOT AN ERROR IN EITHER PLAN, which is worth recording
because it looks like one and would otherwise be "fixed" in the wrong direction. Measured both ways: a
bounded 4096-byte header scan finds NINE, a full-body scan finds TEN, the tenth being a second `uyeko5`
quoted example beyond the header window. Nine is exactly the population a resolver reading `_HEADER_BYTES`
can see, so Order 01 is right to say nine and Order 02 is right to say ten; the plans must state the WINDOW
when citing the count. Also corrected: five pending plans now declare `selectors.py`, not three.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | C. Architecture and operability / G. Plan executability | `agent_workflows/selectors.py:397`; `agent_workflows/cli.py:8683` | THE PLAN'S PRIZE IS ~3% OF WHAT AN OPERATOR WAITS FOR, and its Concern attributes to the resolver a cost that is mostly elsewhere. Measured: of ~450ms, interpreter+import ~115ms, resolver TOTAL ~42.5ms (traversal ~29.5ms IRREDUCIBLE by a filename filter, header reads ~13.4ms), display `scan_plans` ~113.6ms re-reading the same 616 records. Net prize ~12.8ms; display layer 8.9x larger. This answers OQ-03 against the plan's own performance rationale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | OPEN | Escalated OQ-03 to `Blocking: yes` with three named choices (execute as narrowed / re-scope onto the display layer / defer). Decomposition written into the Concern, conventions, F-12 and E-02, which now carries an explicit abort condition. The PRIORITY decision is the maintainer's, not the reviewer's. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness / G. Plan executability | `agent_workflows/selectors.py:71`, `:595-598` | E-03 CLAIMED THREE FILTERABLE KINDS BUT ONLY `id6` CAN BENEFIT. Instrumented header reads per query: `id6` 616, `setid` 616, `status` 616, `stem` 616, `substring` 616. `stem`/`substring` are precedence 5/6, so `setid`/`status` have already forced the full read; filtering them saves zero and costs a `parse_clustered` per candidate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 narrowed to the `id6` rule alone, with the measurement and the reason written in; E-06 now requires stating that only `id6` moved; spec-sync requires the reason be recorded at the precedence comment so the filter is not later extended into pure overhead. |
| PR-003 | HIGH | IN-SCOPE | A. Correctness and data integrity | `agent_workflows/selectors.py:304`, `:112-120` | E-04 CONTRADICTED E-05: normalizing `` - Set: `awoptimize` `` makes that record match `setid`, which OUTRANKS `substring`, so `aw find research awoptimize` goes from FOUR files to ONE. E-05 demands identical before/after resolution, so both items could not hold and an executor would have had no correct move. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 INVERTED: it now pins today's behavior with a characterization test (verbatim backtick value, four-file substring resolution) and forbids changing `_read_setid`, routing normalization to Order 02 where it changes no selector answer. Added to Deferred/out-of-scope, the execution contract, V-04 and spec-sync. |
| PR-004 | MEDIUM | UNDER-SCOPE | A. Correctness / D. Anti-regression | measured: 4 of 616 candidates non-conforming | THE SUPERSET FILTER'S EXCEPTION SET MUST BE COMPUTED, NOT HARDCODED. E-03 offered "union with a body-read pass over the exception set" while the plan elsewhere enumerates nine records; a hardcoded nine silently drops the next legacy record added, which is the correctness bug the superset rule exists to forbid. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now mandates a runtime `parse_clustered` union and explicitly forbids a hardcoded list; E-05 adds a synthetic-legacy-record regression test; V-03 requires showing the union is computed; the execution contract and spec-sync both carry it. |
| PR-005 | MEDIUM | UNDER-SCOPE | A. Correctness and data integrity | `artifact_naming.parse_clustered`; `artifact_core.ID6_RE` | THE PARSED FILENAME SLOT IS AN UNSAFE DISCRIMINATOR. `parse_clustered("20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md")` returns conformant with `id6='assess'` and `ID6_RE.match('assess')` is True, so a slot-comparing filter treats a legacy record (declared `wvlk84`) as modern and may drop it. Order 02 records this hazard as its own F-13; neither plan had connected it to Order 01's filter. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now requires matching the WHOLE FILENAME and explicitly forbids comparing against the parsed slot, citing the measurement; carried into V-03, the execution contract and spec-sync. |
| PR-006 | MEDIUM | UNDER-SCOPE | D. Anti-regression / E. Testing | `agent_workflows/selectors.py:5-9` | E-05's DIFFERENTIAL WAS TOO NARROW IN TWO WAYS: it covered plans while `resolve` is the ONE resolver for all ten types and every verb (`set`/`rename`/`show`), and it compared PATH SETS only while PR-003 is a case where the winning KIND flips. A paths-only, plans-only differential can pass while matching behavior has changed. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-05 now spans all record types, compares winning kinds as well as paths, verifies exception records through the CLI, and adds the synthetic-legacy regression test. V-05 makes a changed kind on an unchanged path set an explicit FAILURE. |
| PR-007 | MEDIUM | IN-SCOPE | E. Testing and verification | bare suite; `tests/test_orchestrator_retirement.py` | THE RECORDED SUITE BASELINE IS STALE AND NAMES THE WRONG FAILURE. Authored `1 failed, 5648 passed` blaming `test_orchestrator_retirement.py`; measured `1 failed, 5958 passed, 3 skipped, 2 xfailed` with the failure being an environmental `test_reporting_contract.py` case from an untracked local `opencode-recovery/` (1746 files), while `test_orchestrator_retirement.py` passes (112 passed). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 and Required tests now carry the measured baseline, name the real failure, label it environmental, and instruct the executor to measure its own BEFORE and compare failure SETS rather than counts. |
| PR-008 | LOW | IN-SCOPE | G. Plan executability | both scans run at review | THE NINE-VERSUS-ORDER-02's-TEN DISCREPANCY READS AS AN ERROR AND IS NOT ONE: bounded 4096-byte header scan finds nine, full-body scan finds ten. Left unexplained, a reader "fixes" one plan to match the other. Also stale: three pending plans declaring `selectors.py`, now five. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern, F-14 and the validation section now state the WINDOW with each count and explain why both plans are right; F-11 and the execution contract updated to five plans (`6ltz1y`, `lznpv6`, `paw8so`, `76w6mq`, `xo3244`). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Does OQ-03 stay `Blocking: no` now that review has measured the decomposition the plan wanted, or escalate? | ESCALATE to `Blocking: yes`, keeping it `open`, with three named choices for the maintainer. | Leave non-blocking and let the executor apply E-02's abort condition (rejected: the plan's entire rationale is performance, and at 3% the trade against changing the shared resolver is a priority call the maintainer owns, not an executor's); resolve it myself as "execute anyway for the correctness value" (rejected: that is choosing the maintainer's priorities); mark REPLAN (rejected: the plan is sound and safe, only its value is in question). | Measured decomposition (PR-001): resolver ~42.5ms of ~450ms, net prize ~12.8ms, display layer ~113.6ms. Workflow rule that a reviewer must never guess a human decision, plus `selectors.py:5-9` showing the blast radius is all ten types and every verb. | yes |
| D-2 | E-04 (normalize quoting) and E-05 (identical resolution) cannot both hold. Which yields? | E-04 yields: pin today's behavior with a characterization test, hand normalization to Order 02. | Drop E-05's identical-resolution bar (rejected: it is the plan's whole acceptance argument and the only proof a matching-engine change is safe); keep both and let the executor decide (rejected: guarantees a mid-run contradiction with no correct resolution); normalize and accept the changed answer (rejected: the Scope forbids changing which record wins, and this is the class of change `selectors.py:112-120` says requires owning a contract change). | Simulated normalization measured at review: `aw find research awoptimize` four files by substring becomes one by setid. `selectors.py:112-120` `_STATUS_RE` parity precedent. Order 02 already owns quote normalization at a report-only site. | yes |
| D-3 | Should the filter be narrowed to `id6`, or kept across `id6`/`stem`/`substring` as authored? | Narrow to `id6` alone. | Keep all three (rejected on measurement: `stem`/`substring` already pay the full read before their rules run, so filtering them saves zero and costs a parse per candidate); reorder precedence to make the filename rules filterable (rejected: explicitly forbidden by the plan, the item, and `PrecedenceForcesFrontMatterReadsTests`, and it changes which record wins). | Instrumented `_read_header` per kind at review: 616 reads for every kind including `stem` and `substring`. `_PRECEDENCE` (`selectors.py:71`) places `setid`/`status` at 3/4 and the filename rules at 5/6. | yes |
| D-4 | Is the nine-versus-ten count a defect in one of the two sibling plans? | Neither: it is a read-window difference, documented in both directions rather than "corrected". | Change this plan to ten to match Order 02 (rejected: nine is exactly what a resolver reading `_HEADER_BYTES` can see, so ten would be wrong HERE); change Order 02 to nine (rejected: out of scope for this review, and ten is right for a whole-file report). | Both scans run at review: bounded 4096-byte window finds 9, full body finds 10, the tenth beyond the window. `selectors.py:317` `_HEADER_BYTES = 4096`. | yes |

## Round 2

Opened 2026-09-11 to close PR-001, whose escalated question the maintainer ANSWERED. Round 1 is left
exactly as written: the findings gate reads only the CURRENT round, and the reviews README states rounds
are appended rather than edited, so silently flipping round 1's `OPEN` cell would hide that the question
was ever put. NO PLAN CONTENT WAS RE-CRITIQUED IN THIS ROUND and no new finding was derived; this round
records one disposition and nothing else. No product code was modified.

WHAT THE MAINTAINER DECIDED, and it was a FOURTH option none of the three PR-001 offered: KEEP THE TESTS,
DROP THE FILTER. Round 1 framed the choice as execute-as-narrowed / re-scope-onto-the-display-layer /
defer-to-not-executed. The maintainer instead re-scoped the plan IN PLACE, keeping E-01 and E-04 and
declining the filter outright. That is narrower than (A), which would still have shipped the filter, and
less wasteful than (C), which would have retired an authored plan to write a near-identical one. Stated
basis: at ~12.8ms net of a ~450ms wait the filter does not justify changing the ONE resolver every verb
and all ten record types route through, and the corpus-wide differential needed to prove it safe is
expensive precisely BECAUSE the change is dangerous.

THE FINDING IS THEREFORE `FIXED`, NOT `DEFERRED`. The distinction matters and is worth stating, because
`review_findings.Finding.is_resolved` treats `deferred` as UNRESOLVED and it would keep gating. PR-001's
substance was that the plan's rationale did not survive its own measurement; the remediation is that the
rationale and the work it justified are BOTH GONE from the plan. Nothing about PR-001 is outstanding or
awaiting a later pass, which is what `deferred` would assert.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | C. Architecture and operability / G. Plan executability | Round 1's measurement, unchanged: of ~450ms, interpreter+import ~115ms, resolver TOTAL ~42.5ms (traversal ~29.5ms irreducible, header reads ~13.4ms), display `scan_plans` ~113.6ms; net prize ~12.8ms. Maintainer ruling 2026-09-11. | Carried forward from round 1: THE PLAN'S PRIZE IS ~3% OF WHAT AN OPERATOR WAITS FOR, so its performance rationale did not justify a change to the shared resolver. Re-recorded here only to carry its disposition; the measurement is not re-derived. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | RESOLVED BY DESCOPE, on the maintainer's 2026-09-11 ruling. The filter is DECLINED, not deferred: E-02, E-03, E-05 and E-06 are REMOVED from the plan (they existed only to measure, build, prove and time it), the watermark advanced to 07 so their ids are retired rather than reused, `Work-Kind` moved `feature` -> `chore` since nothing user-visible changes, and the title, Concern, Scope and Goal were rewritten so the plan no longer claims a speedup. What remains is E-01 (contract pins), E-04 (quoting characterization) and a new E-07 recording the declined optimization, the id6-only limitation, the F-16 slot hazard and the frozen-precedence rationale in the comment block. The ~113.6ms display-layer double read is carried by its own backlog item so the real cost is not lost. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-5 | PR-001's question is answered. Amend round 1's cell, or open a round 2? | Open ROUND 2 and record the disposition here. | Edit round 1's `OPEN` cell to `FIXED` in place (rejected: the reviews README states rounds are appended rather than edited, and rewriting a completed round hides that the question was ever escalated, which is the audit trail PR-001 exists to leave); leave PR-001 `OPEN` and let the plan stay unapprovable (rejected: that is the exact one-directional escalation defect the maintainer's handoff names as recurring, and `qhy3i3` E-07 is authored to fix it durably). | `.aw/records/reviews/README.md` on appending `## Round <n>`; `review_findings.current_findings()` reads only the current round; precedent set by `wlxkoz`'s round 2 D-1. | yes |
| D-6 | Is a descoped finding `FIXED` or `DEFERRED`? | `FIXED`. | `DEFERRED` (rejected on mechanics AND on meaning: `Finding.is_resolved` treats `deferred` as unresolved so it would keep gating, and `deferred` asserts a deliberate decision not to fix something still outstanding, while here the finding's subject was removed from the plan entirely). | `agent_workflows/review_findings.py:176-181`, which documents `deferred` as UNRESOLVED and why. | yes |

## Round 3

Opened 2026-09-12 to review the plan AS RE-SCOPED, at the maintainer's instruction to clear the `no-go`.
Round 2 recorded a DISPOSITION (PR-001 closed by the maintainer's ruling) and explicitly re-critiqued
nothing; this round is the actual semantic review of the smaller plan, and it is separate because the
document round 1 read no longer exists in the same form. Four of its six E-items are gone.

WHY THIS ROUND EXISTS RATHER THAN A READINESS RE-CHECK. After round 2 all three refusal predicates
computed clear (`plan_readiness.has_unresolved_blocking_question` -> False, `review_findings.subject_gating_blocks`
-> empty, `newest_verdict` -> neutral), so `aw` would have advanced readiness on a re-check with no
reading required. That instrument was deliberately NOT used: a re-check may only recompute a stale
verdict WITHOUT re-critiquing content, and this plan's title, Concern, Scope, Goal, checklist and
validation set had all changed. PR-101..PR-105 below are the justification: five real defects that a
predicate sweep cannot see, four of them WORK ORPHANED WITH NO OWNER, which is the exact failure the
`AGENTS.md` orchestrator rule warns about (an obligation nobody performs is marked complete).

WHAT WAS RUN, since a review's worth is in what it executed rather than reasoned. `aw ipd lint --phase author`
(conforming) BEFORE semantic review and `--phase review-finalize` (conforming) after every revision.
`aw find plans wtiso` -> 3 records (`8zgybk`, `1o4eif`, `qcqhj7`) against `find -iname '*wtiso*'` -> 17
files. `aw find research awoptimize` -> `kind: substring`, 4 paths. `parse_clustered` on the `assess`
legacy name -> conformant with `id6='assess'`, `ID6_RE.match('assess')` -> True, and that record's real
declared `- Id:` -> `wvlk84`. `selectors.py` read at HEAD to confirm the comment block (`:52-58`), the six
numbered kinds, `UNIQUE_KINDS` (`:69`), `_PRECEDENCE` (`:71`) and `_HEADER_BYTES = 4096` (`:317`) are all
where the plan cites them. A re-scan of pending `Scope-Paths` declaring `selectors.py`. The display-layer
cost re-measured in-process. The bare suite.

EVERY ONE OF THE PLAN'S SURVIVING FACTUAL CLAIMS RE-VERIFIED TRUE. The three claims E-01, E-04 and E-07
must pin were each executed, not read: the artifacts-not-references contract, the backtick substring
resolution, and the F-16 slot hazard. That matters more than usual here, because a characterization test
whose asserted baseline is wrong is worse than no test.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | IN-SCOPE | D. Anti-regression / G. Plan executability | `Required tests / validation` as written after the descope | THE DESCOPE ORPHANED VALIDATION OBLIGATIONS THAT NO SURVIVING E-ITEM PERFORMS. The section still demanded a corpus-wide resolution differential across all record types, a synthetic-legacy regression test, the nine exception records verified through the CLI, before/after timings for four query kinds, and a four-part cost decomposition with E-02's abort-condition statement. E-02, E-03, E-05 and E-06 were all removed, so every one of those was work parked on the plan with no owner and no validation item. This is the failure mode `AGENTS.md` describes for orchestrators, reproduced inside a child by descoping. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Replaced with the bar that fits the actual scope: a diff proving `selectors.py` contains COMMENT CHANGES ONLY, which is a STRONGER proof than a differential (a differential shows a changed resolver still answers identically; a comment-only diff shows nothing could have changed). Kept and re-verified the two pins and the F-16 hazard, each now carrying its 2026-09-12 re-verification. Added an explicit statement that no timing claim is required OR PERMITTED, since a measurement would be evidence for a claim the plan no longer makes. |
| PR-102 | MEDIUM | IN-SCOPE | G. Plan executability | the `EXECUTION CONTRACT` paragraph as written after the descope | THE EXECUTION CONTRACT STILL INSTRUCTED THE EXECUTOR TO BUILD THE DECLINED FILTER. It forbade filtering any kind but `id6`, required computing the exception set rather than hardcoding it, required matching the whole filename, and required the corpus-wide differential as proof the filter removed nothing that could match. Read literally by an executor, those clauses AUTHORIZE the filter the maintainer declined, which is the most consequential possible misreading of this plan. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Rewritten around the actual central prohibition: change NO executable line in `selectors.py`, comment prose only, with the declined filter named as declined. ADDED a clause the plan lacked and needs: if a pin FAILS, that is a discovery and not a license to edit; fix the test or stop and report, never adjust `selectors.py` to make a characterization test pass, which would convert a pin into a silent contract change. |
| PR-103 | MEDIUM | IN-SCOPE | C. Architecture and operability | re-scan of pending `Scope-Paths` 2026-09-12 vs the plan's recorded five | THE CONTENTION COUNT WAS STALE AND OVERSTATED THE HAZARD. The plan recorded FIVE pending plans editing `selectors.py` (`6ltz1y`, `lznpv6`, `paw8so`, `76w6mq`, `xo3244`). Measured today: THREE (`paw8so`, `76w6mq`, `xo3244`). `6ltz1y` and `lznpv6` are both still pending but no longer declare the file, so this is a declaration change rather than plans having landed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected to three with the two dropped plans named and the reason stated, in both the conventions list and the execution contract. ALSO recorded that contention is now LOW BY CONSTRUCTION, since a comment-only edit conflicts textually at worst; the original warning was calibrated for a semantic change to the resolver. |
| PR-104 | MEDIUM | IN-SCOPE | F. KISS and honest documentation | the `Project conventions discovered` list and `Spec / documentation sync` after the descope | THREE CONVENTIONS LINES AND TWO SPEC-SYNC PARAGRAPHS DESCRIBED WORK THAT NO LONGER HAPPENS, in the imperative. Conventions told the executor to CONSUME `_iter_paths`, to COMPUTE the exception set at runtime, and cited a removed E-05 as the authority forbidding quote normalization; spec-sync required writing a superset-only invariant and a computed-exception-set rule AT THE CODE for a filter that will not exist. Documenting an invariant for absent code actively misleads: a later reader would conclude a filter is present. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conventions rewritten to say what is now true, each marked as no longer binding this plan and re-pointed at backlog `59t9x5` where the constraint actually applies. Spec-sync rewritten as prose to WRITE (it is now the plan's only non-test deliverable, performed by E-07) and states explicitly that the superset invariant and computed-exception rule are NOT written, with the reason, so their absence reads as deliberate. `_iter_paths`'s docstring is now explicitly left unchanged, because the sentence that was to be added would be false. |
| PR-105 | LOW | IN-SCOPE | D. Anti-regression / F. Honest documentation | `Findings` table; OQ-01; OQ-02; the OQ-03 option list | RECORDS OF SUPERSEDED REASONING WERE AMBIGUOUS BETWEEN "still binding" AND "historical", with no marking either way. F-7, F-9 and F-18 constrain absent work; OQ-01 and OQ-02 settle questions about a filter that will not be built; the OQ-03 option list offers three choices none of which was taken. Left unmarked, a reader either treats history as an instruction or deletes evidence to tidy the plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Nothing deleted, everything MARKED. Added a header telling the reader to read the findings table as measurement history and naming which rows still bind (F-13, F-15, F-16) versus which now bind only `59t9x5` (F-7, F-18) or nothing (F-9). OQ-01 and OQ-02 marked MOOT with their reasoning retained and the reason for retention stated (OQ-01's frozen-precedence derivation is exactly what E-07 must write; OQ-02's evidence is what `59t9x5` inherits). The OQ-03 option list is explicitly preserved verbatim, with a note not to tidy or renumber it, since a decision is only interpretable beside the alternatives it rejected. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-7 | Does the re-scoped plan still justify existing, or should it be retired now that the filter is gone? | EXISTS AND IS WORTH EXECUTING. Two test pins plus permanent comment prose. | Retire to `not-executed` and lose the pins (rejected: all three pinnable claims re-verified TRUE today and nothing currently pins them, so the contract is genuinely unprotected; `aw find plans wtiso` returning 3 where a glob returns 17 is exactly the property a future optimizer would break first); re-author as a fresh plan (rejected: the maintainer explicitly chose in-place re-scope over that on 2026-09-11, and it would discard this plan's measurement history). | The three verifications run this round; the maintainer's 2026-09-11 ruling. | yes |
| D-8 | `Work-Kind` is now `chore` while source item `f8m2z2` asks for a `feature`. Reconcile them? | LEAVE THE DIVERGENCE, and record why in the gate. | Change the plan back to `feature` (rejected: it ships nothing user-visible, so `feature` would be false); edit `f8m2z2` (rejected: out of scope for this review, and the item's request was legitimate when filed; what changed is the ANSWER to it, which OQ-03 records). | The item's own front matter, read at review round 1 and unchanged; the plan's current scope. | yes |
| D-9 | Is a comment-only diff an acceptable substitute for the removed corpus-wide differential? | YES, and it is STRICTLY STRONGER for this scope. | Keep a reduced differential anyway (rejected as theatre: a differential proves a CHANGED resolver still answers identically, but nothing here changes the resolver, so it would measure a change that does not exist and cost a corpus-wide run to do it); require no diff at all (rejected: then nothing mechanically prevents an executor from "fixing" `selectors.py` to make a red pin pass, which PR-102's new clause exists to forbid). | `Scope-Paths` limits the edit to comment-bearing sites; V-01 and V-07 both now demand the diff. | yes |
