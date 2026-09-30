# Review findings: plan 121j2r

- Subject-Id: 121j2r
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-B01 (MEDIUM, fixed), PR-B02 (MEDIUM, fixed), PR-B03 (MEDIUM, fixed), PR-B04 (LOW, fixed), PR-B05 (LOW, fixed)

## Round 1

Reviewed at HEAD `376cd30b` in an isolated review lane. The plan file was committed and byte-identical to the
lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize --agent` reports `conforming` after revision. `aw check plans` reports no finding on
this plan.

BOTH OPEN QUESTIONS CARRIED `- Owner: reviewer`, SO ANSWERING THEM WAS THIS REVIEW'S JOB. That is worth stating
because the alternative reading (leave them open and recommend NO-GO) would have been wrong: the workflow says
to resolve from evidence rather than ask, and the author explicitly routed both decisions here with a stated
recommendation for each. Both are now `resolved` with the reviewer recorded as owner and a `### Decisions` row.

THE PLAN'S SUBSTITUTION IS HONEST AND I VERIFIED BOTH HALVES OF IT. The backlog item names two surfaces; the
plan implements only one and says so. F-1 is exact: `to_agent_record` reads
`self.data["checked"] if "checked" in self.data else self.data.get("total_checked")` guarded by
`if checked_count is not None`, commit `0a10a7b1` exists with the message quoted, and
`tests/test_agent_checked_count.py` passes `3 passed`. F-3, the live half, reproduced precisely:
`aw specs check` prints exactly `aw specs check: all specs conform.` at exit 0 while `--agent` on the same
tree prints `"checked":38`, and the human branch does hand-write two `sys.stdout.write` calls so the `summary`
computed above the agent branch is genuinely dead code on that path.

THE DECISIVE MEASUREMENT IS THE ZERO CASE, and I took it rather than trusting the argument. In a throwaway
repository with an empty `.aw/records/specs/`, `aw specs check` prints `aw specs check: all specs conform.` at
exit 0 while `--agent` reports `"checked":0`. So a human is told a tree conforms when nothing was examined,
which is the validated-nothing failure the item was filed for, on the surface a human uses. That is a real
defect against a real contract: `docs/cli-output-contract.md:155` reads verbatim "Both renderers expose
identical facts (counts, paths, evidence, exit code) with zero domain drift", and `docs/cli-human-guide.md`
documents the count layout (`X FINDINGS  2 findings across 41 checked`, then `Evidence` / `checked: 41`) which
`aw check specs` demonstrates live as `✓ CONFORMS  20 specs checked`. F-6's 38/20/38 is exact and its
explanation (the retired filter) is correct, so the plan is right to fence it off.

ONE CONTRACT CITATION IS WEAKER THAN THE PLAN IMPLIES, and I note it without making it a finding because it
does not change the verdict. Section 11.1's "zero count" requirement sits under a heading scoped to "Read and
List Verbs" and appears in the AGENT bullet, not the human one; the human bullet there mandates
`Term.empty_result(...)`. Section 2's identical-facts rule is the citation that actually carries this defect,
and it carries it unambiguously. The plan leans on 11.1 as a co-equal authority when it is really supporting
context.

WHAT REVIEW FOUND. Three MEDIUM findings, each a claim that was wrong or incomplete in a way that would have
misled the executor.

PR-B01: F-8 correctly identifies that adopting `HumanRenderer` would newly satisfy
`semantic_facts_from_human`'s `AW ` precondition, and I confirmed the flip by running it (`None` for
`specs check`'s current output, `'clean'` for `aw check specs`). But `tests/conformance_matrix.py` COLLECTS
ZERO TESTS and no test module imports it, so the risk is latent, not live. That matters twice: V-04 asked the
executor to "state whether any matrix-derived test changed status", which has no answerable form, and OQ-01's
tradeoff rested partly on a regression risk that cannot currently fire.

PR-B02 is the finding with the most practical bite. The plan says "nothing pins the current human string",
which is true of tests and FALSE of sibling plans. Two pending plans at `- Status: reviewed`, `h8e3sm` and
`xx5b7a`, each demand as their own `V-*` evidence that `aw specs check` print `all specs conform`, and neither
declares `agent_workflows/specs.py` in `- Scope-Paths:`, so neither would see this change coming. Replacing
the sentence would hand two approvable plans a false alarm. Appending the count instead satisfies both, costs
nothing, and is now an E-01 constraint.

PR-B03: E-04 asserts "this repository has known pre-existing failures, so the suite is green is NOT the
expected result and must not be asserted". At review HEAD the bare suite is `3246 passed, 2 skipped` with an
EMPTY failure set. Left standing, that sentence licenses an executor to tolerate a red test they caused.

WHAT I DELIBERATELY DID NOT DO. I did not widen the plan to the four sibling commands, and OQ-02 now records
why on the release-gate argument rather than on effort. I did not implement the fix or touch any source file.
I did not fix the two sibling plans' V-items, because the additive form makes them correct as written. I did
not downgrade the plan for leaning on Section 11.1, because Section 2 alone establishes the defect.

Bare suite at review HEAD: `3246 passed, 2 skipped, 3 warnings`. `aw sanitize --agent`: clean.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-B01 | MEDIUM | IN-SCOPE | E. Testing / evidence accuracy | `python3 -m pytest --collect-only tests/conformance_matrix.py` -> `collected 0 items`; a repo-wide search for `conformance_matrix` outside that file finds only two prose comments in `command_surface.py`; `semantic_facts_from_human` returns `{'outcome_family': None}` for `specs check` and `'clean'` for `aw check specs` | **F-8's conformance-matrix risk is LATENT, not live: the matrix collects zero tests and has no consumers**, so no matrix-derived test can change status. V-04 nonetheless asked the executor to report whether any did, which has no answerable form, and OQ-01's tradeoff rested partly on a risk that cannot fire | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-10 records the zero-collection measurement AND the confirmed flip, so the risk is neither overstated nor dismissed. V-04 now requires the answer "no matrix-derived test exists" rather than a run, notes the question is moot under the resolved minimal form, and says where the measured flip becomes relevant if someone later departs to the renderer form. OQ-01's resolution is re-grounded on release scope rather than on the matrix risk |
| PR-B02 | MEDIUM | IN-SCOPE | D. Anti-regression / cross-plan coupling | Pending plans `h8e3sm` (`sklbrt`) and `xx5b7a` (`speckwfix`), both `- Status: reviewed`, neither declaring `agent_workflows/specs.py`: `h8e3sm` requires `aw specs check` report `all specs conform.` "both BEFORE (baseline, E-01) and AFTER"; `xx5b7a`'s V-item demands "the pre-edit `aw specs check` output (\"all specs conform\")" | **The "nothing pins the current human string" convention is true of TESTS and false of SIBLING PLANS.** Two approvable plans assert that substring as their own evidence and neither declares the file this plan edits, so replacing the sentence hands both a confusing false alarm | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-11 with both plans' statuses and the exact evidence each demands. E-01 gains a compatibility constraint: ADD the count, keep the existing sentence (an example spelling is given). V-01 requires pasted output showing `all specs conform` still present alongside the count. E-03's expected outcome is corrected to assert the COUNT's presence and NOT the sentence's absence, which would otherwise contradict E-01. The gate repeats it as a measured cross-plan constraint |
| PR-B03 | MEDIUM | IN-SCOPE | E. Testing (a premise that licenses tolerating a regression) | Bare `python3 -m pytest` at review HEAD: `3246 passed, 2 skipped, 3 warnings`, FAILED set EMPTY | **E-04's claim that "this repository has known pre-existing failures, so the suite is green is NOT the expected result and must not be asserted" is FALSE at this HEAD.** Left standing, it gives an executor a sanctioned reason to wave through a failure they caused | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-12 with the measurement. E-04 keeps its before/after requirement (the attribution reason is sound and unchanged) but the premise is corrected: expect an EMPTY failed set on both sides and treat any failure as this plan's until proven otherwise with named evidence. V-04 carries the same correction and forbids citing the original sentence as licence |
| PR-B04 | LOW | IN-SCOPE | G. Live-artifact re-derivation | `_spec_files` returns 38 today; the spec population is live and grows as specs are authored | **V-01 required the count "match the `--agent` `checked` value" but anchored the expectation to 38**, a live count that will drift | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now requires the count be RE-DERIVED on the tree under test and compared across surfaces, with 38 given as review's measurement rather than as the bar |
| PR-B05 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | The gate's execution-contract paragraph as authored | **Missing shared-checkout unstaging guidance and the never-tag prohibition.** The scope fence, paste-actual-output rule and conditional finalize ownership were all already present and correct | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `git diff --cached --name-only` verification before every commit, re-verification after a failed raw commit, precise `git restore --staged` unstaging with a prohibition on bare `git reset`/`git stash`, and never-create-a-tag. Noted for the record that this plan's gate was already stronger than most: it correctly states the fence as a declaration with `--scope-reason`, names its genuinely-unsafe stop cases, and already has conditional runner/executor finalize ownership |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01 (`Owner: reviewer`): minimal in-place count line, or full `HumanRenderer` adoption? | MINIMAL in-place form, matching the author's recommendation, now settled rather than left to the executor | Full `HumanRenderer` adoption now (delivers the documented banner and `Evidence` grid, and honors `human_recipe="check"`); leaving the choice to the executor as authored | This is a `bug` carrying `- Blocks-Release: next`, so the smallest change that closes the measured defect ships soonest with the least to review. Notably I did NOT rest this on the conformance-matrix risk, because I measured that risk to be latent (PR-B01: the matrix collects zero tests), and resting a decision on a risk that cannot fire would be dishonest reasoning even when the conclusion is right. The full layout is a real improvement that `human_recipe="check"` arguably promises, and it belongs with the F-7 sweep where five commands adopt the renderer together and the matrix interaction is measured once for all of them. Leaving it to the executor was the wrong third option: the question was routed to the reviewer on purpose, and an unresolved shape means the diff a maintainer approves is not the diff they see | yes |
| D-2 | OQ-02 (`Owner: reviewer`): fix the four sibling commands here, or file a sweep? | Keep this plan to one command and FILE the sweep, matching the author's recommendation | Sweeping all five commands in this plan; filing nothing and leaving F-7 as prose | The release gate decides it: only `specs check` is named by item `uwerb5`, and putting four unrelated surfaces plus their regression risk in front of a gating fix trades a shipped fix for a bigger one. The deferral is legitimate specifically because it is ENFORCED rather than trusted: the Deferred entry obliges `aw backlog new` and V-01 refuses without the resulting id6. I also removed the authoring turn's stated reason for not filing immediately, since D-1 now fixes the shape, so the executor can file with the sweep's shape named rather than filing a bare title. Verified the sibling claim in part myself (`aw backlog check` prints no count; `aw sanitize` prints none) rather than taking F-7 whole | yes |
| D-3 | PR-B02: should the existing `all specs conform` sentence be replaced by a count line, or kept with the count appended? | Keep the sentence and APPEND the count | Replacing it with a single count line (cleaner output); editing the two sibling plans' V-items instead; ignoring the coupling | Two plans at `- Status: reviewed` assert that substring as their own `V-*` evidence and neither declares `specs.py`, so replacement creates a false alarm for work another party is about to execute. Appending satisfies both plans AND delivers the fact this plan exists for, at zero cost. Editing the siblings' V-items was rejected as worse: they are another party's reviewed plans, this is a shared checkout, and rewriting their evidence requirements to accommodate my reading is exactly the kind of cross-plan edit the contract warns against. Ignoring it was rejected because the collision is measured, not hypothetical | yes |
| D-4 | Does Section 11.1's "zero count" clause support this defect as the plan claims? | Accept the plan's framing without a finding, while recording that Section 2 is the load-bearing citation | Raising it as a finding and requiring the 11.1 citation be softened | Read both sections. 11.1 is headed "Empty Result Convention (Read and List Verbs)" and its zero-count sentence is in the AGENT bullet; its human bullet mandates `Term.empty_result(...)`. So 11.1 is supporting context rather than a human-surface MUST for a check verb. But Section 2's "Both renderers expose identical facts (counts, ...) with zero domain drift" is verbatim and unambiguous, and it alone establishes the defect: the agent surface reports 38 and the human surface reports nothing. Raising a finding would have cost a revision round to change which of two citations leads, without changing the verdict, the scope, or any E-item. Recorded here so a later reader knows the weaker citation was noticed and weighed | yes |
| D-5 | Is `- Work-Kind: bug` with `- Blocks-Release: next` correct for a missing count in human output? | Yes, unchanged | Reclassifying as `chore` on the argument that no wrong answer is produced | The output is not merely terse, it is MISLEADING in the case that matters: measured, a human is told `all specs conform.` when ZERO specs were examined, which asserts a verdict over a population that was never read. That is user-perceptible and wrong, not slow or untidy, so it clears the repository's perceptibility test without needing a latency measurement. The gate is inherited from item `uwerb5` under the standing live-bug rule, and the item's own `Work-Kind: bug` was the maintainer-visible classification at filing | yes |
