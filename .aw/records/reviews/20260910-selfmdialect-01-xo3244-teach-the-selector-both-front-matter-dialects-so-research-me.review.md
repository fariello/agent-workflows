# Review: teach the selector both front-matter dialects so research metadata is matchable, child xo3244 (Set selfmdialect)

- Subject-Id: xo3244
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `d0b0acab`. Structural preflight `aw ipd lint --phase author` conformed (clean, 0 findings)
before semantic review. At `--phase review-finalize` the linter reports two `IPD-Q501` errors, which is the
escalation gate working: both are the blocking questions this review raised, and they are the mechanism by
which an unfixed BLOCKER stops execution rather than merely being reported.

DISCLOSURE: authored in the same repository by the same model family, so treat this as a near-self-review.
I reviewed `76w6mq` immediately before this plan, which is how the composition-order interaction surfaced;
that is a benefit of the sequence and also a reason to weigh my independence low.

THE APPROACH IS SOUND AND I RE-VERIFIED ITS FOUNDATIONS rather than trusting them. `aw find research
reference` returns exactly 5 lines while parsing front matter over the same tree gives `reference: 58,
archive: 31, todo: 20, active: 1` across 110 YAML-parsable docs of 118. The silent-fallthrough diagnosis is
right: the status rule does not error, it falls through to `MATCH_SUBSTRING` and returns a plausible short
list. Choosing option 1, reusing `research_contract.parse_frontmatter` instead of writing a second YAML
reader, keeping the public runner readers bullet-only (E-03), refusing to harmonize `_STATUS_RE`, and
honestly labelling E-04 a guard rather than a fix are all correct, and the bounded 4096-byte header genuinely
suffices (0 of 110 parsable docs differ between full-text and header parse). `tests/test_selector_zero_open.py`
is green today at 34 passed, so any failure there during execution belongs to the change.

WHAT REVIEW CHANGED, AND WHY TWO THINGS BLOCK. The plan's central safety claim is falsified: it asserts the
blast radius outside research is "provably ZERO" because no non-research record opens a `---` fence, and
calls that "the single strongest reason option 1 is safe". Two prompts ARE fenced. They happen to be safe,
but for a reason the plan never states and never implements, so the safety argument as written does not hold
and the correct implementation detail was left to chance. Separately, two questions genuinely require the
maintainer: the contract change reaches a DESTRUCTIVE verb (`aw archive`), which OQ-01 described only as a
query change; and this plan interacts with `76w6mq` as an ordering constraint that neither plan declares.
Five further findings are fixed in place, four of them measurement corrections that would each have misled
an executor. E-item and V-item counts are unchanged at seven each.

THE PATTERN WORTH NAMING, because it recurs across all three plans I reviewed in this session: each was
authored with careful, real measurements that have since drifted, and each drew a safety conclusion from a
count ("zero non-research records", "exactly one file", "zero collisions") rather than from a mechanism. A
count is a snapshot; a mechanism is a contract. Here the mechanism is case-sensitivity, and once stated it is
both stronger than the count and cheap to test.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | BLOCKER | UNDER-SCOPE | A. correctness; C. architecture | measured on `27rjro`: bullet-on-header `uyeko5`, bullet-on-region None, own YAML `id: 27rjro`; `76w6mq` metadata | **This plan and `76w6mq` compose correctly in ONE ORDER ONLY, and neither declares the edge.** `76w6mq` (`idcapture`, `reviewed`, `go-pending-approval`) bounds the SAME three readers to the metadata region; this plan adds a YAML fallback consulted only when the bullet regex MISSES. On the `27rjro` research doc, which quotes an IPD metadata block in its body, the bullet reader over the header returns the FOREIGN id6 `uyeko5` (belonging to an executed plan). So executing THIS PLAN ALONE does not fix that doc: the bullet path hits the quotation, the fallback never runs, the doc keeps asserting `uyeko5`, and `aw set reviewed uyeko5` keeps failing at exit 2. With `76w6mq` landed first the bullet path misses and this plan's fallback yields the correct `27rjro`. This plan never mentions the overlap at all, while `76w6mq` documents it; its gate says "re-read the file at execution time", which is good practice but is not an ordering guarantee | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium-High | OPEN | ESCALATED to OQ-03 (`Blocking: yes`, `Finding: PR-301`); lint refuses (verified, `IPD-Q501` line 160). New F-12 records the measurement both ways. Three costed options (declare `Item-Dependencies: executed:76w6mq`; sequence by hand; accept either order with a re-verification test), recommending the declared edge because it fails closed. DEFERRED-as-open under the Fix Bar on the functionality axis: the mechanical fix asserts an ordering between two independently-approvable release-gated plans and changes what a runner dispatches, which is a scheduling decision, not a reviewer's |
| PR-302 | HIGH | IN-SCOPE | A. correctness; G. executability | measured `prompts 2/34` fenced; `research_contract.py:568-575`; `parse_frontmatter(hdr)['Status']=='draft'` vs `.get('status') is None` | **The plan's central safety claim is false, and the thing that actually makes the change safe is never specified.** F-5 and E-06 assert that no non-research record opens a `---` fence, calling it "provably ZERO" and "the single strongest reason option 1 is safe". Re-measured: TWO prompts are fenced (`.aw/records/prompts/untracked/20260829-1422-01-session-handoff-run-ledger-defects.md` and `...-2250-01-session-handoff-wtiso-stranded-lanes.md`), both `Kind: session-handoff` written by the `handoff` workflow. They are saved ONLY by capitalization: `parse_frontmatter` preserves keys verbatim (no case folding), so `.get('Status')` is `draft` while `.get('status')` is None. E-01 says only "consults the YAML block" and never fixes the key lookup, so whether `aw find prompts draft` starts matching two handoff drafts depends on an unstated implementation choice. The next `handoff` run writes another such file, so this is a contract, not a corpus accident | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-5 marked FALSIFIED in place with the corrected per-type counts; new F-5b (case is what saves it, with the measurement) and F-5c (the lane is gitignored, so the fixture test not the corpus count is the durable guard). E-01 now mandates a case-SENSITIVE lookup of exactly `id`/`status`/`set` with an explicit code comment naming the reason, because it looks arbitrary and a future "robustness" edit would undo it. E-06 rewritten: the safety argument moves from "nothing else is fenced" to "the lookup is case-sensitive", and it must prove the NEW claim with a fixture test plus per-file assertions on the two prompts. V-06 requires both |
| PR-303 | BLOCKER | UNDER-SCOPE | B. security-adjacent (destructive action); F. UX | measured research selectors: `reference` 5->58, `todo` 0->20, `archive` 0->31; `aw archive --help` accepts a research `<set-id>/<id6>` | **The accepted contract change reaches a MUTATING verb, and OQ-01 presented it as a query change only.** `aw archive` takes a research target and MOVES files. Today the bare tokens resolve to 5, 0 and 0 files; after the change they become `MATCH_STATUS` at 58, 20 and 31. So a selector that today relocates at most 5 documents, usually none, would relocate twenty to fifty-eight, and `archive` is simultaneously a research status and a directory in that tree. A maintainer who accepts "my search returns more rows" has not thereby accepted "my archive verb moves thirty-one documents". E-06 does not cover this: it proves no non-research TYPE is perturbed, a true but different claim | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium-High | OPEN | ESCALATED: OQ-01 reclassified `Blocking: yes` with `Finding: PR-303` and rewritten to state the mutating-verb exposure, the corrected 5->58 figure, and three costed options (accept both with preview evidence as a condition; accept for read verbs only, noting that forking the resolver per verb is itself a contract change; decline and retire). New F-13. Required-tests gains a mutating-verb preview demonstration, which is the evidence OQ-01 needs and no other item produced. DEFERRED-as-open under the Fix Bar on the functionality axis: this is a risk-appetite call on a destructive verb, explicitly the human's, and it is not resolvable from the repository since nothing records the maintainer's preference |
| PR-304 | MEDIUM | IN-SCOPE | E. testing; G. executability | `tests/test_selector_zero_open.py:417-424`, `:426-440` | **E-07 names three tests in its target class where there are four, and misses a SECOND class that constrains its own docstring rewrite.** `ResearchStaysFilesystemResolvedTests` also holds `test_research_status_query_opens_zero_files_when_it_is_a_filename_miss`, which survives but belongs to the inverted class and would be silently dropped. `DialectDocumentationTests` asserts the module docstring contains BOTH `"YAML front matter"` and `"research"`, so E-07's rewrite can turn it red for a reason unrelated to correctness; its sibling asserts the `PARITY`/`plans_index.py` prose still sits within 1200 characters before `_STATUS_RE`, constraining edits near it. Discovered mid-execution, this reads as an unexplained failure | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-8b records both. E-07 now names the fourth test and requires it carried across, names `DialectDocumentationTests` with both asserted substrings and the adjacency constraint, and requires either keeping the phrases or updating that test deliberately with a stated reason. V-07 requires its result pasted |
| PR-305 | MEDIUM | IN-SCOPE | E. testing; evidence accuracy | measured `1 failed, 5958 passed, 3 skipped, 2 xfailed`; `test_orchestrator_retirement.py` `112 passed` | **The suite baseline is wrong in count AND in its named failing test, and the real failure invites a destructive fix.** The plan cites `1 failed, 5648 passed` with "the known `test_orchestrator_retirement` failure". Re-measured bare on main: `1 failed, 5958 passed, 3 skipped, 2 xfailed`, and that module passes outright. The real failure is `test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which walks the repo and trips over another party's untracked `opencode-recovery/` directory. An executor expecting a different failure could "clean up" that directory, destroying a co-worker's work in a shared checkout | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-8c. Required-tests carries the re-measurement, names the environmental failure and its mechanism, requires a self-measured baseline judged on delta, and prohibits deleting the untracked directory (repeated in the execution contract). Also records that the focused module is green at 34 passed, so a failure there is the executor's |
| PR-306 | MEDIUM | IN-SCOPE | Evidence accuracy | measured `reference: 58 ... 110 of 118`; `research_contract.py:576-577` | **The headline figure is stale in the one place it is most quoted.** The plan states 5 -> 52 in the Scope line, F-3, OQ-01, required-tests and V-07, and asks for a CHANGELOG entry carrying it. Re-measured: `reference: 58, archive: 31, todo: 20, active: 1` over 110 parsable docs of 118 (authored: 52 over 105 of 113). A changelog is a durable public artifact, so shipping a wrong count there is worse than in the plan | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-3 revised with the re-measurement and an instruction to re-count at execution rather than assert either figure. Scope line, E-02 (110 of 118), E-07, scope check, required-tests and V-07 updated; the changelog entry must carry the re-measured number. `parse_frontmatter`'s cited line range corrected to `:552-577` |
| PR-307 | LOW | UNDER-SCOPE | G. executability | `_PRECEDENCE` `selectors.py:71-78`, loop `:601`; measured `archive` -> `kind=None, paths=0` | OQ-02 asks what `archive` resolves to and assigns it to the executor, but the repository answers it and the plan-review contract says resolve rather than ask. It also mis-states the before value by implication: `archive` resolves to ZERO files today, not to a directory or a substring match, so this is a 0 -> 31 change rather than a re-ranking | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 RESOLVED: status (4th) beats stem and substring but loses to path (1st), so a bare `archive` resolves as a status to 31 records while an explicit path still wins. The measured before state (0) is recorded as the more surprising half and must be pinned alongside the after (31). Cross-referenced to OQ-01, since 0 -> 31 on a mutating verb is precisely what makes that question blocking |

PR-301 and PR-303 are DEFERRED-AS-OPEN under the Fix Bar, both at overall Remediation Risk Medium-High on the
FUNCTIONALITY axis, and every element the Bar demands is stated. PR-301: the axis is functionality (and
architecture, since option (b) would fork the resolver); the risk reaches the threshold because the remedy
asserts an execution ordering between two independently-approvable, release-gated plans and changes what a
runner dispatches; the required decision is the maintainer's choice among OQ-03's three options; the
consequence of leaving it unresolved is that the wrong order ships a research document whose id6 is read from
someone else's executed plan, with the collision that breaks `aw set` still live. PR-303: the axis is
functionality and usability, with a destructive-action edge; the risk reaches the threshold because the only
in-plan alternatives are to fork the resolver per verb (a contract change of its own) or to retire the plan;
the required decision is the maintainer's choice among OQ-01's three options; the consequence of leaving it
unresolved is that a selector which today moves at most five documents silently begins to move up to
fifty-eight on `aw archive`. Effort, time, cost and tokens play no part in either deferral.

Per the escalation rule both are raised in the plan as open questions carrying `- Blocking: yes` and
`- Finding: <ID>`, and the refusal was verified mechanically: `aw ipd lint --phase review-finalize` exits 1
with `IPD-Q501` on both, and the plan renders with a `[blocking]` marker, so it cannot reach `approved`
until the maintainer answers.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-302's fix looks like a one-word implementation note (use a case-sensitive lookup). Fix it in place, or escalate? | FIX IN PLACE, as a mandated implementation detail with a required code comment, and rewrite E-06 to prove the new safety claim. | (a) Escalating it, rejected because it is not a decision: there is exactly one correct behaviour (a case-sensitive lookup of the documented research keys) and no trade-off for a human to weigh. (b) Leaving E-06's "zero fenced records" claim and merely noting the two prompts, rejected because the claim is load-bearing for the whole change and a false safety proof is worse than none. (c) Excluding the `untracked/` lane from the resolver so the prompts cannot be reached, rejected as a much larger behaviour change that would hide records `aw find` legitimately resolves today. | measured `prompts 2/34` fenced; `research_contract.py:568-575` (verbatim keys); `parse_frontmatter(hdr)['Status']` vs `.get('status')`; `.aw/.gitignore:6` | yes |
| D-2 | PR-303: could I resolve the mutating-verb exposure myself by scoping the fallback to read verbs? | NO. Escalate to the maintainer with three costed options. | (a) Scoping the fallback to `find`/`show` on my own authority, rejected on two grounds: the module's own contract is that there is ONE resolver for every verb, so a per-verb dialect forks that contract and is a design change needing its own plan; and choosing it would silently deliver a different feature than the backlog item asked for. (b) Leaving OQ-01 advisory as authored, rejected because it fails OPEN: an executor would ship the widened selector onto a destructive verb with no one having agreed to it. (c) Adding a mitigation (refuse a status selector on `aw archive`), rejected as inventing policy the maintainer has not been asked about. | measured `reference`/`todo`/`archive` 5/0/0 -> 58/20/31; `aw archive --help` target grammar; `selectors.py:1-9` (one resolver for every verb) | no |
| D-3 | PR-301: should I just add `- Item-Dependencies: executed:76w6mq` to this plan? | NO. Escalate as OQ-03, recommending exactly that edit. | Writing the edge myself, rejected because it asserts an ordering between two independently-approvable plans, changes what a runner will dispatch, and `76w6mq` is not yet approved, so I would be scheduling the maintainer's queue. Saying nothing and relying on the existing "re-read the file at execution time" guidance, rejected because that is not an ordering guarantee and the wrong order is silently wrong rather than loudly broken. | measured `27rjro` three ways (bullet-on-header, bullet-on-region, own YAML); `76w6mq` `- Status: reviewed`; `ipd_schema` dependency grammar | yes |
| D-4 | OQ-02 is assigned to the executor. Leave it, or resolve it? | RESOLVE from the precedence table, and pin the measured before state (0) as well as the after (31). | Leaving it for the executor mid-implementation, rejected because the plan-review contract forbids asking a human (or deferring to an executor) what the code answers, and the answer is a four-line read of `_PRECEDENCE`. Resolving it without measuring the before state, rejected because the plan implies `archive` currently matches something, and its actually resolving to ZERO is what makes the change a 0 -> 31 jump worth escalating into OQ-01. | `_PRECEDENCE` `selectors.py:71-78`, loop `:601`; measured `resolve(repo,'research','archive')` -> `kind=None, paths=0` | yes |

Nothing in the plan's design was rejected. Option 1, the delegation to `parse_frontmatter`, the bullet-first
ordering, the bullet-only public readers, the honest labelling of E-04 as a guard, and the refusal to
harmonize `_STATUS_RE` are all correct and all re-verified. What review supplied was the falsification of the
central safety claim plus the mechanism that actually secures it, the destructive-verb exposure the
acceptance question omitted, the composition-order constraint with `76w6mq`, a second test class the docstring
rewrite would break, and corrected baselines.

## Round 2

Round 2 exists ONLY to close the finding(s) below, whose escalated question(s) the maintainer answered on
2026-09-10. It re-critiques nothing: every other round-1 finding was already `FIXED` and is superseded
unchanged.

WHY IT IS NEEDED: the escalation contract (`plan-review.md:335-341`) defines the path INTO a blocking
question and no path back, so an answered question leaves its finding reading `OPEN` forever while
`subject_gating_blocks` keeps refusing the plan on a decision that has been made. Appending a round is
the sanctioned mechanism, since `ReviewDocument.current_findings` reads only the LAST round
(`review_findings.py:236-243`). This is the SECOND such cleanup in one session; the durable fix is plan
`qhy3i3` E-07, which is authored and awaiting approval.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | IN-SCOPE | A. Correctness (composition order) | plan OQ-03 (`- Status: resolved`, `- Finding: PR-301`) | Carried forward from round 1 and now CLOSED BY THE MAINTAINER. Round 1 found the two plans compose in ONE order only and neither declared the edge: without `76w6mq` first, this plan's YAML fallback never fires on the affected document because the bullet reader still finds a quoted foreign id6. Ruling of 2026-09-10: DECLARE THE EDGE. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Closed on the maintainer's decision and ACTED ON: `- Item-Dependencies:` is now `executed:76w6mq`, set with `aw ipd dependencies set` rather than hand-edited, so a runner holds this item `dependency-blocked` and reports why. Re-verified the defect is live: the doc's first bullet `Id:` returns `uyeko5` (a real executed plan) against its own YAML `27rjro`, and `aw check all` reports `check.id6-collision` for it. |
| PR-303 | HIGH | IN-SCOPE | B. Contracts (a mutating verb widens) | plan OQ-01 (`- Status: resolved`, `- Finding: PR-303`) | Carried forward from round 1 and now CLOSED. Round 1 corrected the plan's framing twice: the figure is not 5-to-52, and the change is NOT confined to a query, because `aw archive` takes a research target and MOVES files. Ruling of 2026-09-10: ACCEPT BOTH surfaces, with a new obligation to PROVE the default preview lists the full widened set before any move. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Closed on the maintainer's decision. Re-measured: 118 research files, 110 with a parsable status (`reference` 58, `archive` 31, `todo` 20, `active` 1), so the accepted framing is an ORDER OF MAGNITUDE rather than a fixed figure. The recorded consent is explicitly the WIDER one and may not be cited as query-only. Bounding affordance confirmed: `aw archive` previews by default and requires `--apply`. |
