# Review: Scaffold plans that pass the durable-carrier gate, refuse walkthroughs as carrier evidence, and carry the new pending rows

- Subject-Id: vtkfq8
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `ba4a481a`. The target plan was committed and unchanged, so the pre-review
snapshot was correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent`
reported `conforming` (exit 0) BEFORE review and again at `--phase review-finalize` afterwards.

ALL THREE DEFECTS ARE REAL AND I REPRODUCED EACH ONE. F-1: scaffolding a plan into a fresh temp git
repo and running `check_engine.check_durable_carrier` gives exactly one `error` finding, on the
scaffold's own example `OQ-01`. F-2: `aw check plans` exits 1, with 29 of its 31 findings being this
rule, and the CI step is fail-closed (`run: python -m agent_workflows check plans --agent`, no
fallback). F-3: `resolve_evidence_artifact` returns True for a walkthrough path. The plan's
`24 plans / 37 rows` was EXACT at its cited HEAD, which I checked by adding a throwaway worktree at
`0c2e7970` and re-running the count there. This is a well-measured plan on a genuine, release-gating
bug, and its three-part structure matches the three causes.

THE DOMINANT FINDING IS PR-701, AND IT WOULD HAVE INVERTED THE PLAN'S OWN PURPOSE. E-01 emits
`- Carrier-Declined: TODO reason, or replace with - Carrier: <id6>` into every scaffold.
`evaluate_carrier_obligation`'s DECLINED branch returns SATISFIED on `if declined:` alone, and its
docstring says so deliberately: "The reason's MERIT is the reviewer's job ... requiring a human-judged
reason here would be a semantic claim this module cannot make." I drove it: adding any non-empty
`Carrier-Declined` to the scaffold's OQ-01 takes the finding count from 1 to 0. So shipping that string
in the skeleton makes EVERY plan pass this rule forever, whether or not an author ever reads the line.
The plan would then report success (CI green, zero findings) having converted a fail-closed error into a
rubber stamp, which is strictly worse than today's honest red, because a gate that always passes is
indistinguishable from a gate that was deleted. The remedy is the shape the source item `dtrect` itself
proposes first, a COMMENTED/inert placeholder, so I recorded it as OQ-03 with the measurement, required
E-02 to prove the chosen form is not accepted, and made "no inert form works" a stop condition rather
than something an executor resolves by shipping the bypass.

PR-702 removes half of E-01 as over-scope, on measurement. The item requires emitting the deferred
placeholder "as a bullet carrying the same carrier placeholder". `_deferred_section_obligations` reads
only lines beginning `- `, and the scaffold's deferred body is the PROSE line `TODO: deferred / out of
scope, with reason (or 'none').`, so it yields `[]` and contributes NO obligation today. Converting
prose to a bullet CREATES an obligation the scaffold does not have and then carries it: the gate outcome
is identical and the scaffold now implies deferred content it does not have. The single finding a fresh
scaffold produces is OQ-01's, and that is the whole of what E-01 needs to fix.

PR-703 is a false claim that would have shipped in a user-facing refusal. The plan's Concern and E-03
both say walkthroughs "are untracked", and E-03 asks the refusal message to say "a walkthrough is not
tracked". They are git-tracked: `git ls-files .aw/records/walkthroughs/` returns 26 files and
`git check-ignore` does not match the tree. The real property, which the SOURCE ITEM `3yr30q` states
correctly, is `tracked=False` in `attention_contract.TREE_POLICY`, meaning no lifecycle status and
filename-only checking, so nothing reads the contents and it never reaches `aw attention`. The
conclusion (refuse it) is right; the stated reason is wrong, and a refusal an author is meant to act on
must not assert something they can disprove in one command. I also found the check would have matched
only ONE of the two path generations: the `TreePolicy` root is `.agents/docs/walkthroughs` while the
live tree is `.aw/records/walkthroughs`, so a `.aw/`-only literal silently passes a legacy-layout repo,
and `attention._classify_tree` already normalizes both.

PR-704 is bigger than the plan treats it. E-04 says to document the walkthrough rule in the plans README
"next to the carrier fields". Those fields are not there: `Carrier`, `Carrier-Evidence` and
`Carrier-Declined` appear in NO README, in NO spec (the `ipd-structure-and-linting` spec contains the
string `Carrier` zero times), and nowhere in `AGENTS.md` or `CONTRIBUTING.md`. The only prose describing
them anywhere in the tree is inside review records. So an ERROR-severity, CI-fail-closed gate is
enforcing a field documented only in `ipd_schema.py` and `check_engine.py`, which is precisely the
discoverability failure the source item `dtrect` describes and which the plan's own spec-sync section
denies by claiming the fields are "already specified" by `rnkqrc`. That claim is false and I corrected
it. The documentation is now its own item, E-05, because writing a section that does not exist is a
different deliverable from adding a unit test.

PR-705 is the live-count problem the workflow's own convention names. E-05's (now E-06's) acceptance
criterion was "the 24 pending plans `aw check plans` flags" and V-05 asked for "before (24 findings)".
That population is LIVE and it has already moved: 24 plans / 37 rows at the cited HEAD, 29 plans / 36
rows at review, with the pending set itself growing from 31 to 51. It moves in both directions at once,
because concurrent review lanes are landing carriers as they go (three plans this very sweep hardened
are already absent from the flagged set) while the scaffold defect keeps minting new uncarried rows. A
count is therefore the wrong bar; the property is zero findings of that rule, re-derived at execution.
I also noted the practical ordering: while E-01 is unlanded the set refills behind a corpus pass, so
E-01 should land first even though the declared dependency is E-03.

PR-706 concerns the one item with real blast radius on other people's work. E-06 edits roughly thirty
plans this plan does not own, several in active review right now. The plan does say "edit only the
carrier subfield", which is the right instinct, but it gave no staged-set verification, no explicit list
of what must NOT be touched, and no instruction for the conflict case beyond a passing mention. Given
AGENTS.md's shared-checkout rules and the measured fact that lanes are landing concurrently, that
needed hardening rather than a clause.

Two smaller things. E-03 changes a predicate reached from TWO gate surfaces, not one:
`ipd_lint._merge_durable_carrier` calls the same evaluator at `--phase pre-transition`, so
`tests/test_ipd_lint.py` is a required run that the plan's test list omitted. And `check all` will not be
clean after this plan: `check plans` also reports a `check.ipd-lint-diagnostic` on plan `9npssm` for a
BLOCKING open question, which this plan neither owns nor may answer, so V-07 must name it as
pre-existing rather than claim a clean tree.

I confirmed the plan is right to leave `resolve_evidence_artifact` alone (OQ-02): it is the shared
resolver `aw backlog set done --evidence` uses, so widening the refusal there would change backlog close
legitimacy, a different contract with its own gate. Backlog items `dtrect` and `3yr30q` are both
`graduated` and carry no `- Blocks-Release:`; `rtyapw` is already `done` and its retirement note
correctly hands the live remainder here. The plan's own `- Blocks-Release: next` is appropriate: it is
`Work-Kind: bug`, CI is red, and the every-live-bug-gates-the-release rule applies.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | IN-SCOPE | A. Correctness / B. Gate integrity | `evaluate_carrier_obligation`'s DECLINED branch returns on `if declined:` with docstring "The reason's MERIT is the reviewer's job"; driven at review: adding `- Carrier-Declined: <any text>` to the scaffold's OQ-01 took `check_durable_carrier` from 1 finding to 0 | THE PROPOSED PLACEHOLDER TURNS A FAIL-CLOSED GATE INTO A RUBBER STAMP, inverting the plan's purpose. E-01 ships `- Carrier-Declined: TODO reason, ...` in every skeleton, and any non-empty value SATISFIES the rule by explicit design. Every future plan would therefore be born pre-satisfied on the one rule this plan exists to make satisfiable, and an author who never touches the line still passes. The plan would report success (CI green, zero findings) having removed the gate's information content entirely, which is worse than the current honest red: a gate that always passes cannot be told from a deleted one. | C:Low; U:Low; S:Medium (a gate silently stops gating); F:Medium; Overall:Low (choose an inert form and prove it) | FIXED | Added F-6 with the driven measurement. E-01 now states both constraints (the gate accepts any non-empty value; the string must also enter `_AUTHORING_PLACEHOLDERS`) and defers the form to OQ-03, which resolves to a COMMENTED/inert placeholder, the shape source item `dtrect` proposes first. E-02 gains a THIRD assertion that the emitted placeholder is NOT accepted as satisfied, driven rather than read. A stop condition covers "no inert form works". |
| PR-702 | MEDIUM | OVER-SCOPE | A. Correctness / F. KISS | `_deferred_section_obligations(fresh_scaffold_text)` -> `[]`; the scaffold's deferred body is the prose line `TODO: deferred / out of scope, with reason (or 'none').`; the single finding names `OQ-01` only | HALF OF E-01 CREATES THE OBLIGATION IT THEN CARRIES, for zero net effect. The item requires emitting the deferred placeholder as a BULLET with a carrier. Only `- `-prefixed lines are obligations, so a fresh scaffold's deferred section contributes none; turning prose into a bullet ADDS one, then satisfies it. The gate outcome is unchanged and the scaffold now implies deferred content it does not have. Traceable to no requirement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now carries an explicit DO NOT for the deferred half, with the measurement, so a later reader does not "finish" it. Added F-7; Scope and the Scope check's over-scope line record the removal. |
| PR-703 | MEDIUM | IN-SCOPE | A. Correctness / F. Honest documentation | `git ls-files .aw/records/walkthroughs/ \| wc -l` -> 26; `git check-ignore -v <walkthrough>` -> exit 1 (no match); `TreePolicy(name='walkthroughs', ..., tracked=False, reason='narrative records; no lifecycle status in v1 (OQ8)')`; item `3yr30q`'s own wording; `TreePolicy` root `.agents/docs/walkthroughs` versus the live `.aw/records/walkthroughs` | A FALSE CLAIM WOULD SHIP IN A USER-FACING REFUSAL, and the check would miss a layout. The plan says walkthroughs "are untracked" and asks the message to say so; they are git-tracked and not ignored. The true property, which the source item states correctly, is `tracked=False` in the attention contract: no lifecycle status, filename-only checking, never surfaced in `aw attention`. A refusal an author must act on may not assert something they can disprove in one command. Separately, E-03 names only the `.aw/` path, so a legacy-layout repo passes silently. | C:Low; U:Medium (a refusal that misstates its own reason); S:Low; F:Low; Overall:Low | FIXED | E-03 now requires the correct reason in BOTH the message and the code comment, with the measurement inline, and requires matching both path generations by routing through the existing `attention._classify_tree` normalization rather than a new path literal (P8). The plan's Concern is corrected too. V-03 requires the refusal message be pasted and confirmed not to claim untracked, plus a `git ls-files` count as the evidence the old reason was false, plus one refusal case per path generation. Added F-8. |
| PR-704 | MEDIUM | UNDER-SCOPE | F. Honest documentation / G. Plan executability | `grep -c Carrier` on `20260802-1904-01-ipd-structure-and-linting.spec.md` -> 0; a tree-wide `--include=*.md` grep for `Carrier-Declined` (excluding worktrees) hits only `.aw/records/reviews/*`; no hit in `AGENTS.md`, `CONTRIBUTING.md`, or any README | THE INSTRUCTION IS NOT ACTIONABLE AND THE PLAN'S SPEC-SYNC CLAIM IS FALSE. E-04 says to document the rule "next to the carrier fields" in the plans README; the fields are documented in NO README and NO spec, so there is no such place. The plan's spec-sync section asserts carriers "are already specified" in the IPD spec by `rnkqrc`; that spec contains the word zero times. So an ERROR-severity, CI-fail-closed gate enforces a field described only in code, which is exactly the discoverability failure source item `dtrect` filed, understated by the plan as a cross-reference. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Documentation split into its own item E-05 (writing the vocabulary and when each of the three escapes applies, not appending to a nonexistent section), with the measurement stated so the executor does not go looking for text to extend. The spec-sync section is corrected and records that amending the IPD spec is a larger, separate change left unlisted rather than silently declined. V-05 requires the diffs plus a grep proving the vocabulary is now findable. Added F-9. |
| PR-705 | MEDIUM | IN-SCOPE | A. Correctness (live-artifact success criteria) | 24 plans / 37 rows re-measured in a throwaway worktree at `0c2e7970`; 29 plans / 36 rows at review HEAD; pending population 31 -> 51; three plans hardened earlier in this sweep are already absent from the flagged set | THE ACCEPTANCE CRITERION COUNTS A LIVE, MOVING POPULATION, which the repository's own convention forbids. E-05 targets "the 24 pending plans" and V-05 demands "before (24 findings)". The set moves in both directions simultaneously: concurrent lanes land carriers while the unfixed scaffold mints new uncarried rows. An executor holding the number would either chase a stale set or report a mismatch as a failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06's expected outcome is now the PROPERTY (zero findings of that rule) RE-DERIVED at execution, with the counts moved into prose as dated context and both measurements recorded. V-06 forbids comparing against any number in the plan and requires the flagged set enumerated fresh before and after. Added F-5. Also added the practical ordering note: E-01 must land first or the set refills behind the pass. |
| PR-706 | MEDIUM | IN-SCOPE | B. Security-adjacent (other parties' work) / C. Operability | AGENTS.md shared-checkout rules; `git log` shows review lanes landing concurrently during this sweep; ~29 flagged plans, several under active review | THE ITEM WITH THE LARGEST BLAST RADIUS ON OTHER PEOPLE'S WORK HAD ONE SENTENCE OF PROTECTION. E-05 edits ~30 plans this plan does not own. It says "edit only the carrier subfield", which is right, but names nothing that must not be touched, gives no staged-set verification, and treats the concurrent-conflict case as an aside. In a checkout where other lanes are demonstrably landing changes to these same files, that is how a co-worker's edit gets overwritten or swept into this plan's commit. | C:Low; U:Low; S:Medium (another party's work); F:Low; Overall:Low | FIXED | E-06 now enumerates what must NOT change (question Status, answers, Owner, findings, history prose, surrounding reflow), requires `git diff --cached --name-only` verification before every commit with precise `git restore --staged` recovery, and makes the conflict case an explicit STOP-and-report per plan. The gate carries a dedicated shared-checkout-discipline paragraph and names the concurrent-conflict case as a genuine stop condition. V-06 requires naming any plan left unedited. |
| PR-707 | LOW | UNDER-SCOPE | E. Testing | `ipd_lint._merge_durable_carrier` calls `evaluate_carrier_obligation`; the plan's test list named only `test_ipd_authoring.py`, `test_ipd_templates.py`, `test_check_engine.py` | E-03 CHANGES A PREDICATE REACHED FROM TWO GATE SURFACES AND THE PLAN TESTS ONE. The same evaluator backs `aw check` and `aw ipd lint --phase pre-transition`, which is stated in its own docstring as the point of having one predicate. A regression in the lint surface would ship unnoticed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests now include `tests/test_ipd_lint.py` and `tests/test_ipd_schema.py`, marked REQUIRED with the reason; V-04 requires a passing `test_ipd_lint.py` run specifically. |
| PR-708 | LOW | IN-SCOPE | A. Correctness (an outcome claimed cleaner than it will be) | `check plans --agent` rule histogram at review: 29 `check.ipd-uncarried-obligation`, 1 `check.ipd-lint-diagnostic` (plan `9npssm`, OQ-03 blocking and open), 1 `check.collisions-not-checked` | E-06'S EXPECTED OUTCOME ("no carrier findings") READS AS A CLEAN TREE, WHICH IT WILL NOT BE. `check all` will still report a blocking-open-question lint diagnostic on plan `9npssm`, which this plan neither owns nor may answer, plus the informational collisions notice. An executor expecting clean would either report a false pass or treat another plan's finding as this plan's failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07's expected outcome names the pre-existing findings explicitly, and V-07 requires the `check all` output broken down BY RULE with every non-carrier finding named as pre-existing. |
| PR-709 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: three sentences; compare pending plan `afpmdu`'s gate | THE GATE UNDERSTATES AN APPROVAL WITH UNUSUAL REACH: E-05 edits ~30 other plans, E-01 changes what every future plan is born with, and the plan carries `- Blocks-Release: next` on a genuinely red CI. It had no what-a-human-is-approving paragraph, no scope fence, no stop conditions, and an UNCONDITIONAL finalize instruction. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate: an approval paragraph naming the three things (mass edits to others' plans, a corpus-wide scaffold change, a real release gate); a per-path scope fence as a DECLARATION noting `resolve_evidence_artifact` is excluded; the shared-checkout discipline paragraph; the honesty rule naming the two easiest-to-fake claims and forbidding a clean-tree claim; four genuine stop conditions; and conditional runner/executor finalize ownership plus the correct backlog closes (`dtrect`, `3yr30q`; `rtyapw` already done). |
| PR-710 | LOW | UNDER-SCOPE | G. Plan executability (right-sizing) | Original E-04 bundled a unit test and two README sections; original E-01 bundled two generator changes plus template regeneration; `aw ipd lint` passed on count | ITEMS BUNDLED DELIVERABLES WITH DIFFERENT EVIDENCE. E-04 held a test and documentation that does not exist anywhere (a writing task, not a test task); E-01 held an OQ change, a deferred change (removed by PR-702) and a template regeneration. A count-based size lint cannot see either. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Seven items with a 7:7 bijection: E-01 scaffold, E-02 scaffold test, E-03 refusal, E-04 refusal test, E-05 documentation, E-06 corpus, E-07 verification. Cohesion rationale states it is still the same three concerns and why E-05 split out. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the plan's three defect claims be accepted as measured, or independently reproduced? | Reproduce all three, including re-running the corpus count at the plan's own cited commit. | (a) Accept them, since the plan cites commands - rejected: F-2's count is of a LIVE population and the whole question of whether it is a usable target depends on how fast it moves, which only a second measurement at a second commit can show. (b) Reproduce only the scaffold defect - rejected: the walkthrough claim turned out to rest on a false premise about git tracking, which reading the plan alone would not have surfaced. | Scratch-repo scaffold -> 1 error finding; `check plans` -> exit 1, 29/31; throwaway worktree at `0c2e7970` -> 24/37; review HEAD -> 29/36 | yes |
| D-2 | E-01's placeholder would satisfy the gate by itself. Ship it, reject the item, or change the form? | Change the form to an inert/commented placeholder, recorded as OQ-03, and require E-02 to prove it is not accepted. | (a) Ship as written - rejected: it makes every future plan pass this rule unconditionally, which is worse than the current red because the gate stops carrying information. (b) Drop the scaffold change - rejected: that leaves F-1, the plan's primary defect, unfixed. (c) Teach the gate to judge a reason's merit - rejected: the evaluator explicitly declines to make that semantic claim, and overriding that is a bigger contract change than this plan should absorb. | `evaluate_carrier_obligation`'s DECLINED branch and its docstring; driven 1 -> 0 finding count; source item `dtrect`'s first candidate shape is "a commented carrier placeholder" | yes |
| D-3 | E-01 also requires a carrier on the deferred section. Keep it? | No. Remove that half with the measurement inline. | (a) Keep it - rejected: the scaffold's deferred body is prose, contributes no obligation, and bulletizing it creates the obligation it then carries for zero net effect. (b) Keep it but without the carrier - rejected: same objection, plus it would reintroduce a finding. | `_deferred_section_obligations(fresh scaffold)` -> `[]`; the single finding names `OQ-01` | yes |
| D-4 | The plan's stated reason for refusing walkthroughs ("untracked") is false. Drop the item or fix the reason? | Fix the reason. The conclusion is right; the justification is not. | (a) Drop the refusal - rejected: the maintainer ruled it and the true property (no lifecycle status, filename-only checking, never in `aw attention`) fully supports it. (b) Keep the wording - rejected: it lands in a refusal message an author is meant to act on, and they can disprove it with one `git ls-files`. | `git ls-files` -> 26 files; `git check-ignore` -> no match; `TreePolicy(... tracked=False, reason='... no lifecycle status ...')`; item `3yr30q`'s own correct wording | yes |
| D-5 | Should the walkthrough check match one path generation or both? | Both, via the existing `attention._classify_tree` normalization rather than a new path literal. | (a) `.aw/records/walkthroughs` only, as the plan says - rejected: silently passes a legacy-layout repo, and the `TreePolicy` root is the `.agents/` spelling. (b) Two hardcoded literals - rejected: a second "where do walkthroughs live" mechanism is the drift GUIDING_PRINCIPLES P8 forbids. | `TreePolicy` root `.agents/docs/walkthroughs` vs the live `.aw/records/walkthroughs`; `attention._classify_tree` already normalizes both | yes |
| D-6 | E-05's target set is a count of a live population. Keep the count as the bar? | No. The bar is the property (zero findings of that rule), re-derived at execution; the counts become dated context. | (a) Keep "the 24 plans" - rejected: already stale at review (29/36), and moving in both directions as lanes land and new plans arrive. (b) Freeze a list of id6s in the plan - rejected: same staleness with extra maintenance, and it would miss newly-arrived rows the item should also carry. | 24/37 at `0c2e7970` vs 29/36 at review; pending 31 -> 51; three sweep-hardened plans already absent from the flagged set | yes |
| D-7 | Is amending the IPD spec to specify the carrier vocabulary part of this plan? | No, but say so explicitly rather than leave it implied. | (a) Amend the spec here - rejected: the spec is `implemented` and governs the whole IPD contract, so specifying a new field family in it is a larger change than closing this concern requires. (b) Leave the plan's false "already specified" claim - rejected: it is measurably wrong and would tell a future reader the documentation exists. | `grep -c Carrier` on the spec -> 0; the vocabulary appears in no README, spec, AGENTS.md or CONTRIBUTING.md | yes |
