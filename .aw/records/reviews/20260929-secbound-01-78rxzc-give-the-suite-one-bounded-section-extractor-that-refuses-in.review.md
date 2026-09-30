# Review findings: plan 78rxzc

- Subject-Id: 78rxzc
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-301 (HIGH, fixed), PR-302, PR-303 (MEDIUM, fixed), PR-304 (LOW, fixed)

## Round 1

Reviewed at lane HEAD `91d6c88b` in an isolated review lane. The plan file was committed and unchanged,
so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0, zero findings) BEFORE semantic review; `--phase review-finalize --agent` reports
`conforming` after revision.

THIS PLAN'S EVIDENCE IS THE STRONGEST I HAVE REVIEWED IN THIS SWEEP, AND ALMOST ALL OF IT REPRODUCES TO
THE BYTE. I drove every measurement rather than reading it. F-01's live defect is real: building a
backlog item through the actual `backlog.run_new` with a `--body` carrying a `## Suggested work` list and
transitioning it with the actual `backlog.run_set` yields an unbounded count of 4 against the test's
asserted 2, with `- bound the guard` and `- add a control test` sitting in the list as though they were
history records. F-03's worked case gives exactly the quoted offsets, 463 unanchored against 2038
anchored. F-04's `## Sets` really is terminal in a real board render, and appending a section grows the
unbounded slice while the assertion keeps passing. F-05 is exact to the byte: 2170 bounded against 73887
to end of file, with `physical .aw/`, `durable` and `runtime` all satisfiable after D130 and only
`project.json` and `local.json` unique to it, so the test's correctness really does rest on two lucky
strings. F-07's numbers are exact (one `esac` at index 79, three non-comment lines after it, zero of the
script's 24 `COMPREPLY=` lines among them), and its refusal to call a safe site a bug is the right call.
F-08's site carries the quoted failure message and the `assertEqual` against `contract_text()`, so the
unboundedness genuinely is the assertion. The `plan_readiness` docstring and commit `2909713d`'s message
are verbatim as quoted.

I ALSO VERIFIED THE TWO MECHANISMS THE DESIGN RESTS ON, because both are one line to get wrong. Driven
through a real `unittest.TextTestRunner`, an `AssertionError` subclass lands in `result.failures` while a
`ValueError` lands in `result.errors`, so E-01's stated reason for the subclassing is correct. And
E-01's self-match warning is not defensive boilerplate: for `start="## Workflow history"` with
`end="## "`, searching the end marker from position 0 returns offset 0, inside the start marker, giving
an empty section over which every containment assertion passes vacuously.

WHAT REVIEW FOUND. One finding that changes an item's contract, and two accuracy corrections.

FIRST, THE ANCHORED DEFAULT HAS A THIRD OUTCOME THE PLAN DID NOT ACCOUNT FOR. E-02 describes exactly two
behaviors, anchored-lands-on-the-real-heading and `anchored=False`-reproduces-the-old-bug, and its
Expected outcome asserts a universal: anchoring "lands on the real heading for all 33 of the 33". That
universal is false. Re-measured over every tracked `.md`, 1891 contain the marker and 104 diverge under
anchoring, but only 38 are the shape the item describes. The other 66 contain the string ONLY in prose
and have no line-anchored occurrence at all: a quoted `>     ## Workflow history` in an archived comms
message, `.aw/records/plans/README.md` describing the record format in running text, three research
reports enumerating heading names in numbered lists. For every one of those, the anchored default makes
`section` RAISE on the start marker where the unbounded caller silently returned prose.

I did not change that behavior, and the distinction matters: refusing is CORRECT there, for precisely
the plan's own reason, since an unanchored match in such a document points at prose and returns
something that is not a section. What is wrong is that the plan does not say so, and the consequence is
concrete rather than stylistic. The refusal message E-01 specifies names the missing marker; in this case
the marker is demonstrably present in the text, just not at a line start, so a reader hitting it
concludes the input is malformed when the correct remedy is `anchored=False`. Order 02 will meet this
the first time it converts a site whose fixture is a README-shaped document, and it is the one refusal an
executor can most easily mistake for a bug in the helper.

SECOND, F-02 overstates its own blast radius. It says the unbounded `_records` helper "SERVES FIVE
ASSERTIONS"; `grep` returns three hits for `_records(`, one the definition and two the callers, which
between them make two length assertions and five positional ones. The direction is right and the finding
survives, but the number would send an Order 02 converter looking for three sites that do not exist.

THIRD, the originating instance no longer exists, and the Concern narrates it as though it still stood.
There is no `bare_except` guard anywhere under `tests/` today; `git log -S` locates its removal in
`80db6750`, "test: delete 366 tests that pinned code structure instead of behaviour", whose criterion
(tests that "read production SOURCE ... and asserted on its shape. None of them exercises the code")
covers an AST walk over `runner_shared.py` squarely. So the deletion was correct and is not a regression
to repair. Two consequences the plan should state and did not: the live case now carries the entire
"this is live" claim, which it does carry; and the deletion is a standing warning that a bounding fix
must not itself be a source-reading fix, which this plan satisfies by construction and Order 02 must
keep true. I recorded it as a finding rather than a footnote because a reader who checks the Concern's
first example and finds nothing will discount the whole plan.

THE TWO DESIGN ARGUMENTS ARE SOUND AND I DID NOT DISTURB THEM. "Refuse, do not fall back" is argued from
four measured fallbacks rather than from taste, and F-05 prices one of them precisely. The
`tests/support.py`-not-`agent_workflows/` choice records its own honest counter-argument (a managed
target repo cannot import it), which is the right disposition for a helper encoding our record format's
conventions. Both open questions resolve from real censuses, and OQ-01's second reason is the decisive
one: a regex parameter would let a caller restore the exact fallback the plan exists to remove, through
the shared helper every future caller inherits.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | UNDER-SCOPE | A. Correctness / F. Prevent silent failure | Corpus sweep over `git ls-files '*.md'`: 1891 contain `## Workflow history`, 104 diverge between `text.find` and `(?m)^` anchored search, 38 have an anchored match on a real heading and 66 have NO anchored match at all; examples include `.aw/records/plans/README.md` and an archived comms message quoting `>     ## Workflow history` (plan E-02, its Expected outcome) | **E-02 accounts for two anchoring outcomes and there are three, and its Expected outcome asserts a universal that is false.** 66 tracked files contain the marker only in prose, so anchored search finds nothing and `section` refuses on the START marker where the unbounded caller silently returned prose. Refusing is CORRECT, but the plan does not say it happens, and the specified message ("naming the marker") is misleading in exactly this case: the marker IS present, just not line-anchored, so a reader concludes the input is malformed when the remedy is `anchored=False`. It is the refusal an Order 02 converter will hit first and the one most easily mistaken for a helper bug | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | New F-09 records the partitioned sweep (1891 / 104 / 38 / 66) with six of the no-anchored-match files printed in context. E-02 now enumerates all three outcomes explicitly, requires the docstring to state them, and requires the absent-start message to say the marker may exist UNANCHORED and point at the escape hatch; its Expected outcome replaces the false universal with the three-way requirement including the refusal case. V-02 now demands the corpus figure PARTITIONED into the three outcomes rather than as one number, and demands the no-anchored-match case be pasted specifically. The Goal gained a paragraph naming this as the refusal an Order 02 converter meets first; proposed-changes item 2 reconciled |
| PR-302 | MEDIUM | IN-SCOPE | Evidence accuracy | `grep -n "_records("` in `tests/test_backlog.py` returns three hits: the definition plus `test_note_appends_a_dated_record_without_moving_the_file` and `test_a_second_note_preserves_the_first`; those two carry two `assertEqual(len(recs), N)` calls and five positional assertions | **F-02 says the shared unbounded read "SERVES FIVE ASSERTIONS" and it serves two call sites carrying seven assertions.** The finding's direction and its corpus measurement survive, but the count is what Order 02 sequences against, so a converter reading it would search for three call sites that do not exist | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 corrected to two call sites with seven assertions, naming both callers, with the correction flagged and its relevance to Order 02 stated. Its corpus figure re-measured (42 of 1854 at review against 69 of 1751 at authoring) and relabelled live-tree state to re-derive. The Concern's matching "serves five assertions" phrase corrected too |
| PR-303 | MEDIUM | IN-SCOPE | Evidence accuracy (the plan's opening example) | `grep -rln "THE DEFECT REPORT" tests/` and `grep -rn "defect-report section" tests/*.py` both return nothing; `git log -S "a BARE except was added in the defect-report section" --all` returns `80db6750`, "test: delete 366 tests that pinned code structure instead of behaviour"; that commit's message states the criterion | **The ORIGINATING instance the Concern leads with no longer exists**, having been deleted as one of 366 code-structure pins, and the plan narrates it in the present tense as the class's exemplar. The deletion was correct (an AST walk over production source is exactly what P16 prohibits) and is not a regression to repair, but a reader who checks the first example and finds nothing will discount the rest, and the plan loses a lesson it should be claiming: a bounding fix must not itself read production source | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-10 records the absent guard, the deleting commit and its stated criterion, and draws the two consequences: the live case (F-01) now carries the whole "this is live" claim and does carry it, and the deletion is a standing constraint this plan satisfies by construction (every entry point takes `text` from its caller; `tests/support.py` reads no production source) which Order 02 must keep true. The Concern now states the deletion inline rather than leaving a reader to discover it |
| PR-304 | LOW | IN-SCOPE | Evidence accuracy (a status claim) | `aw find plans xvon5j` reports pending; its front matter reads `- Status: to-review`; its `- Scope-Paths:` names `status_set.py`, `check_engine.py`, `runner_shared.py` | **The production-readers deferral says touching them "would collide with an approved plan's scope" and that plan is `to-review`, so no approval exists.** The conclusion is unaffected, since a pending plan's declared fence is what the finalize scope gate reconciles against, but a deferral justified by an approval that has not happened is a claim a reviewer will check | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected to "another plan's declared scope" with the distinction stated and the reason the conclusion survives. New F-12 records all four cited carriers' measured states plus the Set's `- Item-Dependencies: executed:78rxzc` edge, which is what makes the Order 01 / Order 02 split safe rather than merely tidy. Two stale suite baselines (authored `3246 passed`, measured `3278 passed` at review) replaced with re-derive-from-your-own-measurement instructions in both Required tests and V-05 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-301: should the 66 no-anchored-match files be handled by refusing, by silently falling back to unanchored, or by a new outcome? | Keep the refusal, and require the plan to DOCUMENT it as a distinct third outcome with a message pointing at `anchored=False` | Falling back to unanchored search when anchored finds nothing; adding a separate `anchored="prefer"` mode; leaving E-02 as authored | A silent fallback to unanchored search is precisely the defect class this plan exists to remove, applied to the marker-location step instead of the terminator step, and it would reintroduce it in shared code every future caller inherits, so it is rejected on the plan's own argument. A third mode is unnecessary machinery for a case `anchored=False` already serves, and P6 directs against it. Leaving E-02 as authored is not viable because its Expected outcome states a measured falsehood that a validator would either propagate or trip over. Documenting the refusal costs one docstring clause and one message phrase and makes the one confusable refusal self-explaining | yes |
| D-2 | PR-303: does the originating instance's deletion undermine the plan enough to warrant REPLAN or a scope change? | No; record it as a finding and keep the plan as is | Marking REPLAN on the grounds that the motivating example evaporated; narrowing the plan to only the live sites; asking the maintainer whether the item is still wanted | The backlog item's own request is for "the other guards written the same way", so the originating guard's fate was never the justification; F-01 independently reproduces the class against real writers, and F-05 prices a second instance precisely, so the live evidence is sufficient on its own. Narrowing would change nothing, since the plan already adds only a helper and converts no site. Asking the maintainer would spend a turn on a question the repository answers: the deletion commit's own message explains why that test went, and it corroborates rather than contradicts this plan's approach | yes |
| D-3 | Should review verify the `AssertionError`-subclass claim and the self-match hazard, or accept them as stated? | Verify both by direct probe and record the results as a finding | Accepting them as plainly true; leaving verification to the executor via V-01 | Both are single-line implementation details on which the whole refusal design rests, and both are the kind of claim that reads as obviously true and is easy to implement backwards. The self-match case in particular produces an EMPTY section, over which every containment assertion passes vacuously, so getting it wrong yields a green suite and a useless helper. V-01 already demands the executor demonstrate them, so recording the measurement costs nothing and gives the executor a known-correct target instead of a claim to re-derive | yes |
| D-4 | The plan defers the author-time guard, all existing call-site conversions, the production readers, and one permanently-correct site. Should any be pulled in? | None; all four deferrals upheld | Pulling the author-time guard in; pulling the two `test_backlog.py` conversions in to prove the helper against the live defect | The author-time guard has a real unsolved detector-design problem the plan states honestly (`x[start:]` is indistinguishable from a legitimate tail slice without knowing the provenance of `start`), it would be red on arrival until Order 02 lands, and it has its own carrier (`ap839o`, verified open). Pulling conversions in is the one that tempts, because it would demonstrate the helper on the real defect, and the gate's own prohibition answers it correctly: E-05 already reproduces `1pgrii` end to end through the real writers, so the demonstration needs no existing site, and converting one here would put an unreviewed behavior change inside a plan reviewed as a pure addition. The Order 02 dependency edge (`executed:78rxzc`) makes the sequencing enforceable rather than advisory | yes |
