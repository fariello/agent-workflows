# Review findings: plan zosxj4

- Subject-Id: zosxj4
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-A01 (HIGH, fixed), PR-A02 (HIGH, fixed), PR-A03 (MEDIUM, fixed), PR-A04 (MEDIUM, fixed), PR-A05 (LOW, fixed)

## Round 1

Reviewed at HEAD `1d8fc76e` in an isolated review lane. The plan file was committed and byte-identical
to the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE
semantic review; `--phase review-finalize --agent` reports `conforming` after revision, including the
new `E-07`/`V-07` pair.

NOTE THE BASE MOVED: the plan's findings were taken at `b5a45362` and I measured at `1d8fc76e`, so
every claim below was RE-MEASURED rather than read. All six of the plan's original findings survive
that re-measurement intact, which is a good result for a plan whose own gate warns that its premise
could go stale.

WHAT I VERIFIED RATHER THAN ACCEPTED. F-01: `renderers.py` line 184 appends the literal, and
`python3 -m agent_workflows check plans | cat | tail -1` prints `Agent output: --agent (automatic when
piped)` under human prose, which is the self-refutation. F-06: `select_output`'s docstring does carry
"TTY-NESS OF STDOUT AFFECTS COLOR ONLY, NEVER THE MODE", so the resolver is right and this really is a
string defect. F-04 is the one I most expected to be wrong and it is exactly right: `19313eed` deleted
`tests/test_cli_quality_gates.py` (339 lines) and `tests/test_cli_conformance_matrix.py` (224), `git
grep GOLDEN_DIR` matches only the definition in `tests/conformance_matrix.py`, that module is imported
by no test, and `pytest --collect-only -q | grep -ci golden` returns 0. I then did the plan's own
empirical check independently: applied the E-02 fix, left the goldens untouched, ran the bare suite and
got `3246 passed, 2 skipped`, identical to the unpatched baseline, then reverted. F-05 also verifies
precisely: rendering `build_remediation` for the two rules shows the code now emits `--to-id6 --apply`
and `--rename --apply` text the golden does not have, so a wholesale regeneration really would smuggle
unrelated drift into this commit. F-03 verifies (`grep -rln HumanRenderer tests/*.py` returns only the
orphaned `conformance_matrix.py`), and F-02's fifth instance is at `docs/cli-human-guide.md:41`.

THE PLAN'S JUDGEMENT IS GOOD AND ITS SELF-CORRECTIONS ARE THE BEST PART OF IT: it caught that its own
backlog item's central scope claim was false, and it refused the tempting wholesale golden
regeneration for a stated reason. My two HIGH findings are both about things OUTSIDE the file it was
staring at.

PR-A01, and it is the one that would have shipped a false verification. THERE IS A SIXTH LIVE INSTANCE
of the claim, and the plan pre-classifies it as untouchable history. The CLI inventory survey's
"Conventions." paragraph says every command accepts "`--agent` (aw.agent/v1 JSONL, also automatic when
piped)". That is a PRESENT-TENSE normative statement about current behavior in a durable reference
artifact whose README calls the tree "kept for provenance and cold-start handoff"; it is not a
transcript of past output and not a quotation of the retracted policy, and no immutability rule of the
kind that protects `plans/executed/` reaches it. Yet V-06 pre-declares "the survey record" among hits
expected ONLY in "historical records that must not be rewritten". So the plan would have finished with
its Goal ("no ... the last user-facing doc instance is corrected") unmet while its own verification
declared success, which is the specific failure mode a review exists to catch. New E-07 corrects the
clause; new V-07 demands the diff and requires the executor to state WHY the file is live rather than
historical. I also declared the path rather than leaving it to a `--scope-reason`.

One detail worth keeping, because it nearly defeated me too: THE PHRASE WRAPS ACROSS A LINE in that
file (`... JSONL, also` / `automatic when piped), and ...`), so a single-line grep for the full phrase
finds nothing. E-07 says to search the short form. This also sharpened PR-A04.

PR-A02. A CONCURRENT PENDING PLAN DECLARES TWO OF THE SAME PATHS and the plan never mentions it.
`xs557y` (Set `ct1n04`, `to-review`) declares `renderers.py` and `docs/cli-human-guide.md`, scopes
itself to "all inside `renderers.HumanRenderer.render`'s Findings block", i.e. the same method E-02
edits, and its E-06 corrects the same guide E-03 edits; its F-09 even independently measured the same
orphaned-golden fact. I was deliberate about what this IS and IS NOT. It is NOT a runtime hazard and I
did not report it as one: the runners isolate each item in its own worktree and merge through the
revalidate gate, so declaring file overlap a danger would be a claim about code I would be
contradicting. What it actually costs is EVIDENTIARY: V-02 and V-03 demand "exactly one line changed",
and whichever plan lands second may honestly be unable to show that. Both V-items now carry the
exception, with an explicit instruction not to reshape the file to make the diff look smaller.

PR-A03 is a shipped-check failure the plan would have hit before executing. Both `Carrier:
NEEDS-BACKLOG-ITEM (...)` placeholders are REFUSED by `check_engine.check_durable_carrier` as
"malformed `Carrier` reference(s) ... (expected a bare 6-char id6)", so `aw check` reported
`check.ipd-uncarried-obligation` against this plan as authored. The placeholder idiom appears in one
other pending plan too, so this is a pattern rather than a one-off slip. I converted both rows to
`Carrier-Declined` with the honest reason (the obligation is real; the id6 does not exist yet), which
is the shape the tooling accepts, and kept every mechanism that stops the obligation vanishing: OQ-01
still files the item during execution, and V-06 still fails without it. `check_durable_carrier` now
reports CLEAN for this plan and the repository-wide finding count dropped from 27 to 26.

PR-A04 records a limit on the verification rather than a defect in it, and it earns its place because
the repository has already paid for this lesson once. The whole of E-06 rests on grepping ONE literal
phrase. Plan `3rsdbj`'s review measured that its authored three-phrase pattern MISSED "This is
automatic and immediate" and "whenever stdout is not a terminal", the two most load-bearing sentences
in that plan, forcing a six-alternative rewrite. This plan's narrow pattern is defensible, since its
subject IS that exact literal, but a clean grep proves the literal is gone and nothing about a
paraphrase; and the survey's line-wrap shows even the full phrase can hide from a single-line search.
Stated as a fourth honest limit beside the three the plan already had.

I did NOT touch the plan's decision to edit the orphaned goldens as record-keeping, its refusal to
restore the deleted conformance gates, or its refusal to fix F-05's drift. All three are correctly
reasoned and correctly carried.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-A01 | HIGH | UNDER-SCOPE | F. honest documentation / E. verification | `.aw/records/research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md` "Conventions." paragraph: "`--agent` (aw.agent/v1 JSONL, also automatic when piped)"; `.aw/records/research/README.md` describes the tree as "Durable research ... kept for provenance and cold-start handoff" with no immutability rule; the plan's V-06 lists "the survey record" among hits expected only in "historical records that must not be rewritten" | A SIXTH LIVE instance of the false claim exists and the plan pre-classifies it as untouchable history. It is a present-tense normative statement, not a transcript, so the plan would have ended with its own Goal unmet while V-06 declared success | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-08. New E-07 corrects the clause (locating it by the short form, since the phrase WRAPS across a line and a full-phrase single-line grep misses it); new V-07 demands the one-line diff, an empty grep, and a stated reason the file is live not historical; the survey path DECLARED in `Scope-Paths`; E-06's disposition list corrected to remove the survey and its `Depends on` extended to E-07; Goal, Scope (b) and Scope check corrected from "five"/"last" to "every live instance" |
| PR-A02 | HIGH | IN-SCOPE | C. operability / G. executability | `.aw/records/plans/pending/20260929-ct1n04-01-xs557y-...ipd.md` declares `- Scope-Paths: agent_workflows/renderers.py, docs/cli-human-guide.md, ...`, scopes itself to "all inside `renderers.HumanRenderer.render`'s Findings block", and its E-06 corrects `docs/cli-human-guide.md`; its F-09 independently measures the same orphaned goldens | A concurrent pending plan rewrites the SAME renderer method and the SAME guide, unmentioned here. NOT a runtime hazard (the runners isolate per item and merge through the revalidate gate) but an EVIDENTIARY one: V-02 and V-03 demand "exactly one line changed", which the second plan to land may be unable to show | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-07 stating the overlap AND stating plainly that it is not a runtime risk. A Concurrency bullet added to Scope check; V-02 and V-03 each gained the exception, with an explicit instruction to report the larger diff rather than reshape the file; the approval gate names it so an approver is not surprised |
| PR-A03 | MEDIUM | IN-SCOPE | Repository rules | `check_engine.check_durable_carrier` on this plan: "2 obligation(s) name no durable carrier: deferred row 1: malformed `Carrier` reference(s) 'NEEDS-BACKLOG-ITEM (...)' (expected a bare 6-char id6)"; `aw check` reported `check.ipd-uncarried-obligation` against it | Both `Carrier: NEEDS-BACKLOG-ITEM` placeholders FAIL a shipped consistency check, so the plan was already red before executing. The idiom appears in another pending plan too, so it is a pattern, not a slip | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both rows converted to `Carrier-Declined` with the honest reason (the obligation is real; a `Carrier` must be a resolvable id6 and none exists yet), preserving every anti-loss mechanism: OQ-01 still files the item during execution and V-06 still fails without it. OQ-01's resolution records the tooling fact; V-06 now demands the id6, the `Work-Kind`, and a clean carrier check. `check_durable_carrier` reports CLEAN; repo findings 27 -> 26 |
| PR-A04 | MEDIUM | IN-SCOPE | E. verification honesty | Plan `3rsdbj`'s E-09 records that its authored three-phrase pattern MISSED `docs/cli-migration.md`'s "This is automatic and immediate" and `docs/cli-agent-protocol.md`'s "whenever stdout is not a terminal", forcing a six-alternative pattern; re-measured here, the survey's instance WRAPS across a line so a full-phrase single-line grep returns nothing | E-06's entire verification rests on grepping ONE literal phrase, and the repository has already measured that this class of pattern misses paraphrases. A clean grep proves the literal is gone and nothing more | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A fourth HONEST LIMIT added to "Required tests / validation", citing `3rsdbj`'s measured miss and the line-wrap, stating that the narrow pattern is defensible for this plan's exact-literal subject but proves nothing about a seventh instance in other words, and pointing anyone extending the work at `3rsdbj`'s wider pattern |
| PR-A05 | LOW | IN-SCOPE | Evidence accuracy | Re-measured at `1d8fc76e`: `python3 -m agent_workflows check plans \| cat` exits 0, not 1 as F-01 records; the bare suite reports `3246 passed, 2 skipped`, matching the plan | F-01 states the measured invocation exited 1. On the current tree it exits 0 (findings count and exit code both move with the live records tree) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Not corrected in F-01's prose, deliberately: the exit code is a LIVE ARTIFACT property of a shared tree, and V-01 already instructs the executor to "judge the SHAPE of the output only" and not to compare counts against numbers in the plan. Recorded here so a reader who re-measures a different exit code knows it is expected drift, not a contradiction |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is the CLI inventory survey a live surface to fix, or a historical record to leave alone? | Live: fix it (E-07) and declare the path | Leave it as history per the plan's own V-06 (rejected: it is a present-tense statement of current conventions, not a transcript, so leaving it would publish the retracted promise as fact and falsify this plan's Goal); append a correction note instead (rejected: the research tree has no append-only rule, unlike `plans/executed/`, so an in-place clause fix is the honest minimum) | `.aw/records/research/README.md`'s description of the tree; the paragraph's own present-tense wording; the absence of any immutability rule for research records | yes |
| D-2 | How should the overlap with pending plan `xs557y` be reported? | As a coordination and EVIDENTIARY fact, explicitly not a runtime hazard | Report it as a concurrency risk needing serialization (rejected: the runners isolate each item in its own worktree and merge through the revalidate gate, so that claim would contradict shipped behavior and waste a maintainer's time); say nothing (rejected: V-02/V-03 demand a one-line diff the second lander cannot show) | `AGENTS.md` "The runners own ordering, isolation, and orchestrators"; `xs557y`'s declared `Scope-Paths` and its stated `HumanRenderer.render` scope | yes |
| D-3 | The `Carrier: NEEDS-BACKLOG-ITEM` placeholders fail `check_durable_carrier`. Fix by filing the item now, or by declining? | Decline with the honest reason, keeping OQ-01's file-during-execution requirement and V-06's gate | File the backlog item during review (rejected: a review must not create tracked records; the plan-review workflow is explicit that editing a plan is not executing it); invent a plausible id6 (rejected outright, it would forge a reference); leave the placeholder (rejected: it fails a shipped check) | `check_engine.check_durable_carrier`'s refusal text; the `Carrier-Declined` idiom accepted by the same predicate; plan-review's "Review plans only" rule | yes |
| D-4 | Should F-01's stale exit code be corrected in the plan? | No: record it in the review record only | Rewrite F-01 to say exit 0 (rejected: the exit code is a live property of a shared records tree and will drift again by execution time, so pinning a new number repeats the defect); delete the exit code from F-01 (rejected: it is part of what the author actually measured) | V-01's own instruction to judge output SHAPE and not compare live counts; the re-measured exit 0 at `1d8fc76e` | yes |
| D-5 | Should review verify F-04's empirical claim independently, or accept the plan's pasted result? | Verify independently | Accept it (rejected: F-04 overturns the backlog item's central scope claim in the EASIER direction, which is exactly the kind of claim that most needs an independent check before an approver relies on it) | Applied E-02, left goldens untouched, ran the bare suite: `3246 passed, 2 skipped`, matching the unpatched baseline; then reverted. `19313eed`'s deletion stats and the zero `GOLDEN_DIR` consumers | yes |
