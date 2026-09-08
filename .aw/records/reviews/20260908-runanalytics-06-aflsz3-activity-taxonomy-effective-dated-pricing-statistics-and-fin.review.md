# Review: activity taxonomy, effective-dated pricing, statistics, and findings (child aflsz3, Set runanalytics)

- Subject-Id: aflsz3
- Subject-Type: ipd
- Reviewed-At: 2026-09-08
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `1f4c969b`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic review
(exit 0, `outcome: clean`), and `--phase review-finalize` conformed after the nine-item split and the rewritten
V-item bijection.

METHOD, AND IT DECIDED EVERY FINDING. This is an analytics plan, so it can be reviewed the way no other plan in
this Set could: by BUILDING the analyses it specifies and running them over the real corpus. That is what
happened. All 462 session files were parsed, all 32365 tool calls classified, all 29671 priced steps fitted, and
the resulting numbers compared against what the plan assumed. Three of its central premises did not survive, and
none of the three could have been caught by reading the document however carefully, because each is a claim about
what the data contains. The compensating discovery runs the other way: one thing the plan treated as hard turned
out to be exactly solvable, which is worth as much as the corrections.

WHAT THE PLAN GETS RIGHT, and it is the part most analytics work gets wrong. The insistence that association is
not causation, that a refusal is a legitimate output, and that "producing impressive charts is not evidence of a
valid conclusion" is the correct posture and it is stated plainly rather than as a disclaimer. Requiring effective
DATED pricing rather than a timeless price map is exactly right and, as it turns out, more achievable than the
plan knew. Requiring recorded cost be preserved separately from estimated cost is the discipline that keeps a
cost model auditable. And refusing to force overlapping activities to sum to elapsed time is the single most
important honesty property in a time-attribution system.

THE LARGEST FINDING IS THAT THE TAXONOMY IS THE WRONG SHAPE FOR THE DATA, AND THE MARGIN IS NOT CLOSE. The plan
asks for "a versioned deterministic taxonomy with precedence, overlap, uncertainty, and unclassified accounting",
which describes one winning class per event plus a note that overlap occurred. Measured over all 22787 real bash
tool calls: 84.7 percent contain more than one shell segment (45.3 percent carry a leading `cd X &&`), and when
each segment is classified independently, 41.9 percent of commands match TWO OR MORE classes, 49.4 percent match
exactly one, and 8.7 percent match none. So a precedence chain discards a genuine class in two of every five
commands, and which class it discards is determined by the ordering rather than by the work. `cd X && git status
&& python3 -m pytest` is simultaneously git and test; a `grep`-into-`sed` pipeline is simultaneously inspection
and editing. E-01 now requires a LABEL SET with per-label evidence, and precedence survives only as a display
convenience. A related constraint fell out of the same measurement: the only signal available for classifying a
bash action is the command TEXT, which the plan forbids persisting, so classification must happen at ingest with
only labels crossing into a fact. That is the one place in this Set where the privacy boundary and the core
algorithm touch, and the plan had not noticed.

THE FLAGSHIP ANALYSIS MEASURES ALMOST NOTHING, AND WOULD HAVE SHIPPED AS A FLAT LINE. Required analysis 1, listed
first, is instruction/spec/documentation-read TIME. Measured: all 2334 `read` tool calls in the entire corpus
total 183.2 seconds. That is 0.38 percent of the 48036 seconds of tool activity, and tool activity is itself 3.8
percent of the 1254107 seconds of run wall time, so instruction-read time is roughly 0.014 percent of elapsed.
The harm is specific: a chart of a quantity that is four ten-thousandths of the whole looks COMPLETE while
showing nothing, which is worse than omitting it. The burden is real, but it is injected rather than read: the
median session's FIRST step already carries 15067 input tokens before the agent reads anything (mean 25401, p90
44668), and `AGENTS.md` alone is 33101 bytes of always-loaded context. E-04 now measures the burden as tokens and
priced cost, demotes read time to a labeled footnote, and V-04 requires the 0.014 percent figure be PUBLISHED in
the output so no reader mistakes a flat chart for an absent cost.

THE PRICING FINDING IS THE PLEASANT ONE AND IT MAKES THE SCHEDULE TESTABLE. The plan treats price history as
something that must be asserted from an external source with citations, which is why it forbids automatic
scraping. Measured, the history is RECOVERABLE FROM THE CORPUS EXACTLY. Fitting cost against token components
yields two clean eras and nothing between them: through the step at 2026-08-29T01:30:43Z, input $5.00/Mtok,
output $25.00/Mtok, cache_read FREE, reproducing 7917 steps to floating-point exactness; from the step at
2026-08-29T05:38:43Z, $5.50 / $27.50 / $0.55, reproducing 21731. Zero Era A steps occur after the first Era B
step, so a single instant separates them. The residual 23 steps are exactly the 23 carrying `reasoning > 0`, all
in runs declaring `google/gemini-3.8-flash`, so the residual is a model-identity gap rather than a pricing bug.
Two schema consequences follow. `cache_write` must not be a rate column, because it is 0 in all 29611 steps that
report a cache object, so a write rate would be pure invention with no way to test it. And cache_read cannot be
omitted from any cost view: it is 98.62 percent of all tokens and least-squares apportions 72.1 percent of Era B
spend to it.

FOUR REQUIRED ANALYSES CANNOT BE COMPUTED, WHICH MAKES THE PLAN INTERNALLY CONTRADICTORY UNTIL FIXED. Of 733
queue items, only 6 have more than one attempt; only 6 attempts carry `recovery: true`; only 3 have disposition
`merge-conflict`. Required analyses 5, 8, 10 and 11 rest on those. A plan that mandates both those analyses and
statistical rigor with confidence warnings mandates a contradiction, and the resolution was already present in
the plan's own findings contract, which requires a refusal on insufficient evidence. E-06 now applies that rule
to the analyses themselves. Required analysis 12 fails for a different reason: model identity resolves for 2 of
179 attempts, 1.1 percent, because `options.model` is null in 130 of 135 runs, no attempt record carries a model
key, and the only `modelID` occurrences in 462 session files sit on a `task` sub-agent call and describe the
sub-agent's model rather than the main agent's. Price-era stratification is available; model stratification is
not, and inferring the model from the run date would conflate model with price era, manufacturing exactly the
confound described next.

A REAL SIMPSON'S-PARADOX INSTANCE IS ALREADY IN THIS DATA, so the plan's required warning has a genuine exemplar
instead of a synthetic one. Median blended cost per million tokens rises from $0.054 to $0.071 across the Era A
days to $0.635 to $0.737 across the Era B days, a more than nine-fold apparent jump. The rates rose only 10
percent. The jump is caused entirely by cache_read going from free to billable while being 98.62 percent of
tokens. Any cost-efficiency comparison that pools across 2026-08-29 will therefore attribute a pricing-policy
change to workflow behavior, which is precisely the error this plan exists to prevent. It now ships as E-09's
golden test.

TWO SMALLER MEASURED GAPS WORTH RECORDING. 13.0 percent of real spend is invisible at the attempt grain: session
logs total $3026.38 against $2568.12 of recorded attempts, with 215 files holding $394.19 that no attempt
accounts for; and all verifier spend ($64.08 across 57 logs) is recorded at NO attempt, since zero attempts carry
`verify_cost`. Reconciling per session id, 123 of 124 agree exactly and the single disagreement is a run with a
still-`running` item, so the GRAIN is sound and only the COVERAGE is not. Closing that gap is a runner change,
not an analytics change, so the plan now measures and reports it rather than claiming to fix it.

ONE ARCHITECTURAL CONTRADICTION THE PLAN NEVER RECONCILED. `benchmark_metrics` ships in this repository declaring
itself "time/token based, never dollar" and RAISES `MetricError` on any `cost`, `usd` or `price` key, with
`benchmark_manifest` rejecting the same in usage; the prohibition traces to a maintainer ruling recorded in
executed plan `9ihhzr` that dollar cost "is NOT capturable/enforceable". This plan centers dollar cost. They ARE
reconcilable, because that rule governs cross-model benchmark comparison where a per-model price is neither
knowable nor stable, while this cost is runner-recorded and reproduces exactly from a two-era schedule. But
unstated it reads as two modules in the same package contradicting each other, and the tempting wrong fix is to
relax the guard. OQ-04 records the distinction and the gate forbids that fix.

ON SIZING, AND THIS ONE WAS ALREADY KNOWN TO THE SET. Three E-items, and the Set's own orchestrator (`5lxvl3`)
carries an OPEN blocking question naming this plan's E-02 explicitly as one of the four densest items in the Set:
"Order 06 E-02 bundles effective-dated pricing WITH every required statistical aggregation, which are separate
failure domains joined only by sequence". E-03 was worse, carrying the ranked-findings contract AND the selection
of four additional analyses AND the twenty analytics. All ten children carry exactly three items, the count-based
lint conforms at three by construction, and this is the sixth sibling split for the identical reason (`bzz5e6`
3->6, `lhccjf` 3->8, `5f2h8i` 3->7, `8hald1` 3->8). Split into nine across four groups. The sixth consecutive
sibling also carried no execution contract in its gate. Both patterns are in the authoring pipeline rather than
in any one plan, and the maintainer should hear that once rather than have it rediscovered in the four remaining
unreviewed siblings.

WHY APPROVE WITH REVISIONS RATHER THAN OPEN QUESTIONS. Nothing needed a human. The taxonomy shape, the
under-power policy and the model-comparison refusal were all settled by measurement; the dollar-cost
reconciliation was settled by reading the shipped code and the executed plan behind it. All four are recorded as
decisions with their bases and their rejected alternatives. No BLOCKER and no unfixed HIGH remains. The Set's own
sizing question (`5lxvl3` OQ-01) stays OPEN and blocking on the ORCHESTRATOR, which is correct: this review
applied the remedy that question recommends for this child, and the maintainer's answer still governs the other
three named children.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-073 | HIGH | IN-SCOPE | A. correctness; F. KISS (wrong model for the data) | segment-split and classified all 22787 real bash commands (104116 segments) across 462 session files: 84.7 percent multi-segment, 41.9 percent match 2+ classes, 49.4 percent exactly 1, 8.7 percent none | **ACTIVITY CLASSES OVERLAP IN 41.9 PERCENT OF COMMANDS, SO THE AUTHORED SINGLE-LABEL PRECEDENCE TAXONOMY DISCARDS REAL DATA IN TWO OF EVERY FIVE COMMANDS,** and which class it discards is an artifact of the precedence ordering rather than of the work. Overlap is the NORM here, not an exception a tiebreak handles. Separately, the only signal for classifying a bash action is the command TEXT the plan forbids persisting, which the plan never noticed | C:Medium; U:Low; S:Medium; F:High; Overall:Medium | FIXED | E-01 rewritten to require a LABEL SET per event with per-label rule evidence and no persisted command text, precedence demoted to display only; E-02 owns the measured unclassified/overlap accounting with a regression floor; V-01 requires the multi-class share re-measured and the ingest-only text rule proven; OQ-01 records the decision and rejects both the overlap-side-channel and the fixed primary/secondary pair. New F-1 |
| PR-074 | HIGH | IN-SCOPE | A. correctness; F. UX (a chart that looks complete and shows nothing) | summed `time.start`/`time.end` on all 32365 tool parts (100 percent coverage): `read` 183.2 s of 48036 s tool time; run wall 1254107 s; first-step input median 15067 tokens over 428 sessions; `AGENTS.md` 33101 bytes | **THE FLAGSHIP REQUIRED ANALYSIS MEASURES 0.014 PERCENT OF ELAPSED TIME.** Instruction-read TIME is 0.38 percent of tool time and tool time is 3.8 percent of wall time, so the plan's first-listed analysis renders as a flat line indistinguishable from zero. The burden is real but INJECTED: the median session's first step carries 15067 input tokens before any read. A chart of four ten-thousandths of the whole is worse than an omission because it looks complete | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | E-04 reshapes the analysis into injected-token and priced-cost terms with the standing-instruction byte inventory, demoting read time to a labeled footnote; V-04 REQUIRES the 0.014 percent figure and its derivation be published in the OUTPUT, not only in the plan; the Findings list annotates analysis 1 as reshaped. New F-2 |
| PR-075 | HIGH | IN-SCOPE | A. correctness and data integrity (pricing schema) | per-day least-squares fit plus exact-match test of both rate hypotheses against all 29671 priced steps; boundary located to the step; cache_write census | **PRICE IS RECOVERABLE EXACTLY IN TWO ERAS, WHICH MAKES THE SCHEDULE TESTABLE AND ALSO REFUTES THE PLAN'S COMPONENT LIST.** Era A through 2026-08-29T01:30:43Z ($5.00/$25.00, cache_read FREE) reproduces 7917 steps exactly; Era B from 2026-08-29T05:38:43Z ($5.50/$27.50/$0.55) reproduces 21731; zero interleaving; the 23 residuals are exactly the 23 `reasoning>0` steps from a different model. But `cache_write` is 0 in all 29611 steps, so a write-rate column is untestable invention, and cache_read is 98.62 percent of tokens and 72.1 percent of Era B spend | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-07 seeds the measured two eras with their boundary instants and requires the schedule VALIDATE against recorded cost, refusing rather than estimating for the 23 unpriced-model steps, with no cache_write rate column; V-07 requires per-era exact-match counts and a step priced on each side of the boundary; the conventions bullet records the correction in the plan's favor. New F-3 |
| PR-076 | HIGH | UNDER-SCOPE | A. correctness; E. testing (statistical validity) | attempt and disposition census over all 135 `state.json` files: 6 of 733 items multi-attempt, 6 recovery attempts, 3 merge-conflict; verifier spend $64.08 across 57 logs with 0 attempts carrying `verify_cost` | **FOUR REQUIRED ANALYSES REST ON n BETWEEN 3 AND 6, SO MANDATING THEM AND MANDATING RIGOR IS A CONTRADICTION.** Required analyses 5 (merge waste), 8 (conflict recurrence), 10 (retry loops) and 11 (burden versus retries) cannot be computed. The plan's own findings contract already requires a refusal on insufficient evidence but never applied that rule to the analyses themselves. Also, the verifier phase is derivable only from the session filename | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | New E-06 adds a shared under-power predicate returning `cannot-determine` with the observed n, applied to the four measured slices, and derives the verifier phase from the filename LABELED derived; V-06 requires each refusal pasted with its n and proof a chart cannot be produced; the Findings list annotates all 16 analyses with measured feasibility; OQ-02 rejects both the wide-interval chart and dropping the requirements. New F-4 |
| PR-077 | HIGH | IN-SCOPE | A. correctness; D. domain invariants | enumerated every model/provider key path across all state and session files: `options.model` null in 130 of 135; `launch_profile` absent in 102; 16 of 462 session files carry `modelID`, all at `part.state.metadata.model.modelID` on a `task` call; net 2 of 179 attempts | **MODEL IDENTITY RESOLVES FOR 1.1 PERCENT OF ATTEMPTS, SO REQUIRED ANALYSIS 12 CANNOT BE DRAWN.** The only `modelID` in the corpus identifies a `task` SUB-AGENT's model, not the measured agent's. Price-era stratification is available; model stratification is not. Order 04 fixes capture going forward only, so historical comparison stays unavailable | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-08 requires model comparison REFUSE with the measured coverage until identity exceeds a declared threshold, while price-era stratification proceeds; V-08 requires the coverage figure pasted with the refusal; OQ-03 rejects date-based model inference precisely because it conflates model with price era, manufacturing F-10's confound; a stop condition in the gate forbids it. New F-5 |
| PR-078 | MEDIUM | UNDER-SCOPE | A. data integrity; E. testing (coverage) | summed both sides for every run and matched files to attempts by name and by session id: logs $3026.38 versus attempts $2568.12; 215 files hold $394.19 unaccounted; 123 of 124 session ids reconcile exactly | **13.0 PERCENT OF REAL SPEND IS INVISIBLE AT THE ATTEMPT GRAIN AND ALL VERIFIER SPEND IS.** A per-IPD cost chart built only from attempt records understates by an eighth. The single reconciliation failure is a run with a still-`running` item, so the grain is sound and only coverage is not | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Missingness bias named as one of the four required additional analyses in E-05 with the $394.19 figure; E-06 derives and labels the verifier phase; the deferred section states plainly that closing the gap is a RUNNER change this plan measures rather than fixes; V-05 requires the figure re-measured. New F-6 |
| PR-079 | MEDIUM | UNDER-SCOPE | G. right-sizing and conceptual density | orchestrator `5lxvl3` OQ-01 read (names this plan's E-02 explicitly); all ten children at exactly 3 items; lint conforming both before and after the split | **THE E-ITEMS WERE MECHANICALLY SIZED, AND THE SET'S OWN BLOCKING OPEN QUESTION ALREADY NAMES THIS PLAN AS ONE OF THE FOUR DENSEST.** E-02 bundled pricing with every statistical aggregation, which `5lxvl3` calls "separate failure domains joined only by sequence"; E-03 carried the findings contract AND the four-analysis selection AND twenty analytics. Sixth sibling with this finding | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into NINE items across four groups (attribution / analytics and honesty limits / pricing and statistics / findings); `Highest E allocated` 03 -> 09; V-01..V-09 rewritten to bijection; a right-sizing note records the orchestrator's own citation; cohesion rationale restated to say it justifies one PLAN, not one ITEM |
| PR-080 | MEDIUM | UNDER-SCOPE | G. executability | plan gate as authored (two sentences); five sibling review records | **THE GATE CARRIED NO EXECUTION CONTRACT**: no scope fence, no path-scoped-commit / never-push rule, no paste-actual-output honesty rule, no lifecycle move, no re-measure warning, no stop conditions. Sixth consecutive sibling with the same omission | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Full contract added: approval requirement, the load-bearing `8hald1` dependency with WHY it matters, the three consuming Orders that make the taxonomy version and price schedule contracts; a fence naming seven measured prohibitions with the finalize `--scope-reason`/`--scope-ack` mechanics; the classify-at-ingest privacy rule stated as the one place the boundary meets the algorithm; path-scoped commit with re-verify-after-failed-hook; the honesty rule; re-measure-every-number; and FOUR stop conditions |
| PR-081 | MEDIUM | IN-SCOPE | C. architecture (duplicate/contradictory paths) | `benchmark_metrics.py:1` ("never dollar"), `:42-49` `_FORBIDDEN_COST_KEYS`, `:170` raise; `benchmark_manifest.py:215`; executed plan `9ihhzr` convention line | **A SHIPPED METRICS LAYER IN THIS REPOSITORY REJECTS DOLLAR COST OUTRIGHT AND THE PLAN NEVER RECONCILED WITH IT.** `benchmark_metrics` RAISES on a `cost`/`usd`/`price` key by maintainer ruling ("dollar `cost` is NOT capturable/enforceable"), while this plan centers dollar cost. They are reconcilable (that rule governs cross-model benchmark comparison; this cost is runner-recorded and exactly reproducible) but unstated it reads as two modules contradicting each other, and the tempting wrong fix is relaxing the guard | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | OQ-04 records the distinction with both rejected alternatives; a conventions bullet states it with citations; E-08 reuses the existing `MetricValue` uncertainty vocabulary (`:95`) and `wilson_score_interval` (`:59`) rather than inventing a second; the fence forbids relaxing `_FORBIDDEN_COST_KEYS` and a stop condition repeats it; Order 10 must document the distinction. New F-9 |
| PR-082 | LOW | IN-SCOPE | Honest documentation; E. testing | per-day blended rate over all 29671 steps: median $0.054-$0.071 in Era A days versus $0.635-$0.737 in Era B; cache_read 98.62 percent of tokens; rates rose 10 percent | Two gaps. "No open questions" was untrue (four decisions were unmade). And a REAL Simpson's-paradox instance is already in the data: a nine-fold apparent cost-per-token jump caused by cache_read becoming billable, not by the 10 percent rate change, so any comparison pooling across 2026-08-29 misattributes a pricing change to workflow behavior. The plan required a paradox warning with no exemplar | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Four open questions recorded resolved with bases and rejected alternatives (OQ-01..OQ-04); E-09 ships the price-era paradox as a golden test with the measured figures and requires stratification before any cost comparison; the within-session gradient is stated as association-only with its competing explanation; baseline recorded (`2 failed, 5655 passed, 3 skipped, 2 xfailed`) with both node ids attributed pre-existing; the two smart quotes removed and the escaped backtick cleared (0 remaining, after Order 01's six, 02's four, 03's ten, 04's eighteen and 05's sixteen). New F-10 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Is the activity taxonomy single-label with precedence, or multi-label? | MULTI-LABEL: a label SET per event with per-label evidence; precedence demoted to choosing a display label only | Single-label with an `overlap_time` side-channel, as authored, rejected because the side-channel records THAT overlap happened without recording WHAT overlapped, which is the question every activity analysis asks. A fixed "primary plus secondary" pair, rejected because 1.6 percent of commands match four or more classes and a fixed arity truncates them | classified all 22787 real bash commands (104116 segments): 84.7 percent multi-segment, 41.9 percent match 2+ classes, 8.7 percent none | yes |
| D-2 | What happens to a required analysis whose measured sample size is 3? | Return the plan's OWN `cannot-determine` verdict carrying the observed n, via a shared under-power predicate with a declared minimum | Rendering with a wide confidence interval, rejected because a chart drawn from n=3 is read as a result regardless of the interval, and this plan's stated purpose is to avoid impressive charts that are not evidence. Dropping the four requirements, rejected because their absence is indistinguishable from an oversight while a recorded refusal is a durable statement about the corpus | census over all 135 `state.json` files: 6 of 733 items multi-attempt, 6 recovery attempts, 3 merge-conflict attempts; the plan's own findings contract already mandates refusal on insufficient evidence | yes |
| D-3 | Can the model/provider/variant comparison be computed for historical runs? | NO. Refuse with the measured 1.1 percent coverage and let price-era stratification carry the analysis | Inferring the model from the run date, rejected because it conflates model identity with PRICE ERA and would make every cost difference look like a model difference, manufacturing exactly the Simpson's-paradox confound F-10 documents. Inferring it from a `task` sub-agent's `modelID`, rejected because that is a different model than the one being measured. Silently pooling all attempts as one model, rejected because the corpus provably contains at least two | `options.model` null in 130 of 135 runs; `launch_profile` absent in 102, `host-default` in 31 of 33 present; no attempt-level model key; 16 of 462 session files carry `modelID`, all on a `task` call; Order 04's own text requiring per-file capture going forward | yes |
| D-4 | How does this plan's dollar-cost analytics coexist with `benchmark_metrics`, which forbids dollar cost? | They are DIFFERENT measurement contracts and both stay as they are; the distinction is documented in Order 10's data dictionary | Relaxing `_FORBIDDEN_COST_KEYS` so one cost vocabulary serves both, rejected because it deletes a deliberate guard on the benchmark layer to suit an unrelated consumer. Dropping dollar cost from this plan, rejected because recorded cost is the primary signal the maintainer asked to analyze and it demonstrably exists and reproduces exactly. Saying nothing, rejected because an executor reading both modules sees a contradiction and the tempting fix is the first alternative | `benchmark_metrics.py:1,42-49,170`; `benchmark_manifest.py:215`; executed plan `9ihhzr`'s recorded maintainer ruling scoping the prohibition to cross-model benchmark comparison; the two-era fit reproducing 29648 of 29671 recorded costs exactly | yes |
| D-5 | Which four additional corpus-supported analyses does the plan adopt, given it deferred the choice to execution? | Named at review: cost concentration, the within-session cost gradient, price-era stratified efficiency, and missingness bias | Leaving the selection to execution as authored, rejected because the corpus was measured at review and deferring would repeat exactly the guesswork this review corrected, with no guarantee the executor measures before choosing. Choosing from the plan's suggested list without measuring (context-switching entropy, verifier disagreement), rejected because several of those rest on the same under-powered slices D-2 refuses | measured: top 10 percent of attempts hold 22.8 percent of spend; mean step cost $0.0781 to $0.1290 across position deciles over 345 sessions; the two exact price eras; $394.19 unaccounted across 215 session files | yes |
