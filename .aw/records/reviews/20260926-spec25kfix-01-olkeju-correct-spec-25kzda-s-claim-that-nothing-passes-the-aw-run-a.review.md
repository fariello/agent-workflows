# Review findings: plan olkeju

- Subject-Id: olkeju
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `46cb6af4`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(exit 0, `findings: 0`) before revision and `--phase review-finalize` conforms after. No pre-review
snapshot was needed: the plan was committed and unmodified, and the lane-input copy is byte-identical
to the tracked file.

THE PLAN'S CORE CLAIM IS TRUE AND WORTH FIXING. The clause is present and demonstrably false:

```text
spec:61  but NOTHING PASSES THEM: zero of 3764 commits across all refs carry an `AW-Run` trailer
git log --all --oneline --grep='^AW-Run:' | wc -l   ->  63
... | rg -c '^closed by aw'                         ->  62
```

The plan's diagnosis of WHO passes is right, its no-counts rule is exactly the right instinct, and its
E-03 target strings ("corrected twice (2026-08-30, then 2026-09-20)" and the paragraph header) are
present and unique as quoted. Its F-4 reading of backlog `sbh1o1` is accurate and careful, and its
decision to leave Section 4.2 alone is correct.

**THE PLAN WOULD HAVE LEFT ITS OWN TARGET SENTENCE SELF-CONTRADICTORY.** This is the finding that
matters most. The parenthetical it rewrites is a qualifier on a LIST, and the list is introduced by
"STILL NET-NEW and to be built:", with the trailers as its first item. Rewriting only the parenthetical
therefore produces:

```text
STILL NET-NEW and to be built: the hash-chained run ledger's `AW-Run:`/`AW-Item:` commit trailers
(the ledger AND the writer are built ... driver-side sites pass them ...)
```

which asserts and denies the same thing in one sentence, and still tells a graduating Set to build a
writer that already ships. The paragraph's own header names that exact failure mode: "Creating a
parallel capability module because this paragraph once called the descriptor net-new is the exact defect
that destroyed `a54m79`." So the plan would have half-corrected a falsehood in a way that preserved the
consequence it exists to prevent. E-02 now also moves the trailers out of that list.

**THE SAME FALSE CLAIM LIVES IN TWO CODE COMMENTS, CARRIED BY NOBODY.** `run_evidence`'s
`RUN-COMMIT-CONTENTS` `waiting_on` says "`m73aet`'s own executed receipt records that nothing in the
tree passes trailers yet", and `ipd_lifecycle`'s attribution docstring says "essentially no commit in
history carries one yet, so nothing can be consumed today (backlog `a8eufb`)" - where `a8eufb` is
`done`, so that pointer is dead as well. Correcting only the spec leaves the next reader who greps the
CODEBASE with the original falsehood, which is a realistic path: this plan's own concern is that a false
sentence is "what reviewers read first". I did not fold the edits in (both files are outside the fence,
and `run_evidence`'s string belongs to the Section 4.2 transcription the plan deliberately preserves);
E-05 files one item so the obligation survives.

**THE MEASUREMENTS DRIFTED WITHIN HOURS, AND ONE "FUTURE" PLAN IS ALREADY PAST.** 39 -> 63 commits,
38 -> 62 backlog-close subjects, and F-5's "`8apjpp` will add a site" is spent: `8apjpp` is `executed`
and its review-output commit (`review(<host>): record the review of <id6>`, carrying `AW-Run`/`AW-Item`
plus `AW-Committed-By: driver`) is live with 3 such commits in history. `aw commit` also threads
trailers via `work_cmd` for a programmatic caller. None of this breaks the amendment, because the plan
wisely forbade counts; it does mean the SITE LIST must be categorical too, so E-02 now says "several
driver-side sites" with two named as examples, and E-01 tells the executor to re-check each named plan's
CURRENT status rather than trust this plan's snapshot.

**ONE INTERACTION THE PLAN SPOTTED BUT DID NOT GUARD.** F-4 correctly notes that `sbh1o1` cites the
sentence E-02 removes as "THE UNDERLYING FACT SURVIVES", quoting it verbatim. After E-02 that quotation
is dead, so `sbh1o1` becomes a fresh instance of the citation rot it was filed about. The plan says the
interaction is harmless because `sbh1o1`'s recommended fix is unaffected, which is true but incomplete.
E-02 now keeps the ids `sbh1o1` leans on findable, E-04's note records the interaction, and a Deferred
row assigns the quotation repair to `sbh1o1` itself.

**WHAT I CONFIRMED RATHER THAN CHANGED.** OQ-01 (do not fold `sbh1o1` in) is correctly resolved and I
re-read `sbh1o1` in full to check it: its citations really are in `i1hlgx` (executed), `zrzfkw` (done)
and `eh91an` (open), not in this paragraph. The spec-amendment declaration is correct and properly in
`- Scope-Paths:`. `aw specs note` works on an `approved` spec and prepends the record (tested on a
scratch COPY; the tracked spec was not touched), and three prior `AMENDED ...` records exist to match
its shape. `aw specs check` conforms BEFORE the edit, so a post-edit failure would be attributable. The
bare suite is green (`2458 passed, 2 skipped in 36.79s`). The Step 0 note that `RUN_FINDING_CODES` has
no guarding test is accurate. Right-sizing: 5 E-items on one file plus one filing, trivially one pass
each.

ONE SMALL CORRECTION: the plan's validation section says the suite matters because "the spec is read by
some tests' fixtures by path, e.g. `tests/test_run_selection_policy.py`". It is not: that file only
CITES the spec in prose, and no test opens this spec. The suite run is still worth doing as a cheap
regression check, but the stated reason was wrong and is now recorded as such.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A. correctness (a half-correction that preserves the harm) | the target sentence read in full: "STILL NET-NEW and to be built: the hash-chained run ledger's `AW-Run:`/`AW-Item:` commit trailers (the ledger AND the writer are built ...)"; the paragraph header's own warning that calling shipped machinery net-new "is the exact defect that destroyed `a54m79`" | **E-02 REWRITES ONLY THE PARENTHETICAL, LEAVING THE TRAILERS LISTED UNDER "STILL NET-NEW and to be built".** The result asserts and denies the same fact in one sentence and still instructs a graduating Set to rebuild a shipped writer, which is the consequence this plan exists to prevent and which the paragraph itself records as having destroyed a prior plan. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (one sentence, in a file the plan already owns) | FIXED | E-02 gains a second bullet requiring the trailers to move OUT of the "STILL NET-NEW" list (into the paragraph's existing already-shipped material, or an inline statement that the WRITER ships and only the READ-BACK is net-new), leaving the prompt `Run contract` block and `aw hooks install` as the genuine remainder, and authorizes the consequent punctuation fix. `- Scope:`, the Scope check and the approval paragraph updated. V-02 now requires the full rewritten sentence pasted. F-7 added. |
| PR-002 | MEDIUM | IN-SCOPE | A. correctness of the plan's own premises | `git log --all --oneline --grep='^AW-Run:' \| wc -l` -> `63` (plan says 39); `... \| rg -c '^closed by aw'` -> `62` (plan says 38); `.aw/records/plans/executed/20260925-revcommit-01-8apjpp-...ipd.md` is `- Status: executed`; `rg -n "run_item_trailers"` -> two sites in `runner_shared`, one in `work_cmd` | **THE COUNTS AND THE SITE LIST ARE ALREADY STALE, AND F-5 TREATS AN EXECUTED PLAN AS FUTURE.** `8apjpp` has landed, so a third driver-side site is live. The amendment survives (no counts are written), but E-02's wording named ONE site and E-01's expected outcome said "the driver-side sites" as if the set were fixed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 gains the re-measured numbers, an instruction to verify each named plan's CURRENT status with `find` rather than trust the snapshot, and an expected outcome of SEVERAL sites; E-02's wording says "several driver-side sites" naming two as examples and forbids enumeration; F-5 marked superseded in part; F-6 added. |
| PR-003 | MEDIUM | UNDER-SCOPE | A. correctness (this edit creates a new rotted citation) | `.aw/records/backlog/open/20260921-sbh1o1-...backlog.md` quotes "'STILL NET-NEW and to be built ... NOTHING PASSES THEM: zero of 3764 commits across all refs carry an AW-Run trailer', naming plan `wao266`" as the place the underlying fact survives | **E-02 DELETES THE SENTENCE BACKLOG `sbh1o1` CITES AS ITS SURVIVING-FACT EVIDENCE,** so an item filed ABOUT citation rot in this spec gains a rotted citation of its own. The plan noticed the interaction and judged it harmless on the narrow ground that `sbh1o1`'s recommended fix is unaffected, which is true but leaves the trail broken. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 must keep `wao266` and the trailer topic present in the rewritten clause and must NOT edit `sbh1o1` (out of fence, owns its own fix); E-04's amendment note now records the interaction so a reader of `sbh1o1` can follow it; a Deferred row assigns the quotation repair to `sbh1o1` with its carrier. |
| PR-004 | MEDIUM | UNDER-SCOPE | A. correctness / F. honest documentation (the correction is undone elsewhere) | `run_evidence.py` `RUN-COMMIT-CONTENTS` `waiting_on`: "`m73aet`'s own executed receipt records that nothing in the tree passes trailers yet"; `ipd_lifecycle.py`: "essentially no commit in history carries one yet, so nothing can be consumed today (backlog `a8eufb`)"; `a8eufb` is `- Status: done` | **THE SAME FALSE CLAIM EXISTS IN TWO CODE COMMENTS WITH NO CARRIER, AND ONE POINTS AT A CLOSED ITEM.** Correcting the spec alone leaves the falsehood reachable by anyone who greps the code, which is the same failure mode in a different file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-05: FILE one backlog item (`aw backlog new --work-kind chore`) naming both locations and the dead `a8eufb` pointer, and explicitly do NOT edit either file (out of fence; `run_evidence`'s string is part of the Section 4.2 transcription this plan preserves). V-05 requires the item plus a clean `git status` over `agent_workflows/`. A Carrier-Declined Deferred row records the reasoning. Watermark 04 -> 05. F-8 added. |
| PR-005 | LOW | IN-SCOPE | E. testing (a stated rationale that is false) | `rg -n "25kzda" tests/*.py` reviewed in full: prose citations and one deliberate Section 5.2 message transcription; no `read_text`/`open(`/`Path(` on the spec; `tests/test_run_selection_policy.py` only cites it in a docstring | **THE VALIDATION SECTION JUSTIFIES THE SUITE RUN WITH A COUPLING THAT DOES NOT EXIST** ("the spec is read by some tests' fixtures by path, e.g. `tests/test_run_selection_policy.py`"). Harmless in effect, but a false premise in a plan is what this plan is about, and it could lead an executor to over-attribute a suite failure to the spec edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The rationale is corrected in place and kept as a cheap regression check; F-9 records what was actually checked, including that `aw specs check` conforms BEFORE the edit and the green baseline. V-04 cites the baseline for comparison. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-02 rewrites a parenthetical. Review the parenthetical, or read the whole sentence it sits in? | READ THE WHOLE SENTENCE; the trailers are listed as "STILL NET-NEW" and must move too. | (a) Review the clause as scoped: rejected, the plan's own goal is that the paragraph say something TRUE, and a corrected parenthetical inside an uncorrected list is still false and still triggers the rebuild failure the header warns about. (b) Flag it and leave the fix to the executor's judgement: rejected, "adjust the surrounding sentence somehow" is exactly the instruction an executor gets wrong, and the plan explicitly told them to keep that phrase byte-identical. | The sentence read in full; the paragraph header's `a54m79` warning; the plan's E-02 instruction "Keep 'STILL NET-NEW and to be built:' ... byte-identical". | yes |
| D-2 | The same false claim is in two code comments. Fix them here, file an item, or say nothing? | FILE ONE ITEM (E-05), and do not edit either file. | (a) Fix them here: rejected, both are outside a deliberately spec-only fence, and `run_evidence`'s string is part of the Section 4.2 transcription this plan's own scope preserves byte-exact; editing it would put the plan at odds with itself. (b) Say nothing: rejected, the plan's premise is that a false sentence misleads whoever reads it first, and two code comments are read more often than a spec preamble. (c) Ask the maintainer: rejected, "file an item for a stale comment" needs no ruling. | The two quoted strings; `a8eufb` measured `done`; the plan's `- Scope:` OUT list naming Section 4.2. | yes |
| D-3 | `sbh1o1` quotes the sentence being deleted. Edit `sbh1o1`, or leave it? | LEAVE IT, but keep the ids findable and record the interaction in the amendment note; assign the repair to `sbh1o1` as its carrier. | (a) Edit `sbh1o1` here: rejected, out of fence and it is the item whose whole subject is this class of rot, so it is the right owner. (b) Leave it entirely unaddressed as the plan did: rejected, a deleted quotation with no forwarding trail is a new instance of the defect, and the fix costs one clause in a note. | `sbh1o1` read in full; its `POSSIBLE FIX` paragraph already prescribes citing stable sections over quoted strings. | yes |
| D-4 | The plan's counts are stale and one "future" plan has executed. Update the numbers, or change how the plan talks about them? | CHANGE HOW IT TALKS: categorical wording for the SITE LIST as well as for counts, plus an instruction to re-verify each named plan's status. | (a) Just refresh 39 -> 63 and 38 -> 62: rejected, it re-arms the trap; the values moved within hours and will move again. (b) Leave them, since the amendment writes no counts: rejected, E-02 named a single site and E-01's expected outcome implied a fixed set, so the staleness had somewhere to do damage even under a no-counts rule. | The re-measured values; `8apjpp` measured `executed` with 3 review-commits in history; three `run_item_trailers` call sites. | yes |

### Deferred and open

- (none). All five findings were FIXED in place. No question required the human: OQ-01 was already
  correctly resolved and I re-read its evidence to confirm, and every decision above rests on a
  measurement or on the plan's own declared scope.

HONEST LIMITS, stated because they bound what this round proves. I verified the DEFECTS and the target
strings; I did not write the replacement prose, so that the rewritten sentence is grammatical, correctly
wrapped, and truthful remains E-02's work and V-02's evidence. My `aw specs note` check ran on a scratch
COPY of the spec, not on the tracked file, so it proves the verb accepts an `approved` spec and prepends
a record but not that it composes correctly against this file's exact history block in place. I searched
for sibling copies of the false claim with targeted greps over `agent_workflows/` for trailer-related
strings; a differently-worded third copy could exist that I did not find, so F-8's two locations are a
floor and not a proven-complete set. I ran the bare suite once for a baseline and did not run
`make test-all`, which is appropriate for a prose-only edit but means I have not characterized the slow
set here. Finally, I did not attempt to determine whether `a6xbso` or `199u11` will land before this
plan executes; E-01 is instructed to check rather than assume, which is the durable answer.
