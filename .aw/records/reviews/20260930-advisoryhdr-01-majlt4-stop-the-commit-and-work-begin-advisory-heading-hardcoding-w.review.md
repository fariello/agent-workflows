# Review findings: plan majlt4

- Subject-Id: majlt4
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-101 (HIGH, fixed), PR-102 (HIGH, fixed), PR-103 (HIGH, fixed), PR-104 (MEDIUM, fixed), PR-105 (LOW, fixed), PR-106 (MEDIUM, fixed), PR-107 (LOW, fixed), PR-108 (LOW, fixed), PR-109 (HIGH, fixed), PR-110 (MEDIUM, fixed), PR-111 (LOW, fixed)

## Round 1

Reviewed at HEAD `65ea492f7` in an isolated review lane. The plan file was committed and byte-identical
to the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE
semantic review; `--phase review-finalize` reports `conforming` after revision, with the one transient
`IPD-Z602` advisory my own E-04 edit introduced resolved by tightening that prose. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator row check does not apply. No production file and no test
was modified by this review; `aw sanitize --agent` reports clean.

THE PLAN'S CENTRAL CASE IS CORRECT AND I RE-DROVE IT RATHER THAN READING IT. The end-to-end probe
reproduced F-01 verbatim: a temp git repo with the suite's own `_PLAN` fixture, `check_engine.check_type`
patched to return one `check.scope-drift` drift at the plan, then `cli.main(["commit","wk0001",...])`
prints `REGISTERED_SEVERITY = error`, `ENRICHED_SEVERITY = error`, `rc = 0`, and the heading
`aw commit: note - 1 advisory (warning) finding(s) on 20260828-wk-01-wk0001-demo.ipd.md (not blocking):`
followed by the untiered detail line. So an `error`-registered rule really is announced to a human as a
`warning`, and the heading really is the only severity signal in that output. F-04's three-rule probe
reproduced exactly (`check.scope-drift` -> `error`, `check.review-decision-unescalated` -> `warning`,
an invented rule -> `error` via `_DEFAULT_RULESPEC`), and I additionally confirmed its load-bearing
subtlety: a raw `artifact_core.Drift` carries `severity=''` while every `enrich_drift` result carries a
non-empty tier, so the plan's `or "unclassified"` fallback is correctly shaped and correctly described as
reachable only by an unenriched drift. F-06's routing comment reads as quoted, and
`test_scope_drift_registered_severity_is_error` exists where F-06 says, so the "do not fix this at the
registry" warning is backed by a real red test. F-03's baseline reproduced (`11 passed`), and I read all
four existing advisory tests: each asserts only `assertIn("advisory", out)` plus a rule id, so the
proposed heading preserves every one of them, which I verified by rendering it.

F-05 IS THE FINDING THAT DECIDES THE PLAN'S WHOLE SHAPE, AND IT WAS THE WEAKEST LINK IN THE EVIDENCE.
It argues the advisory batch can be genuinely MIXED, which is what rules out any single batch-level
parenthetical however worded, and which is why the plan narrows the backlog item's two options to one.
But it supported that by rendering candidate wording "in memory", which shows what the output WOULD look
like and not that the state is REACHABLE. Reachability is the entire claim. Driving both drifts through
the real `work_cmd._validate_plan_via_engine` on a temp repo returns `blocking = []` and
`advisory = [('check.scope-drift', 'error'), ('check.review-decision-unescalated', 'warning')]`, so one
heading really does introduce two tiers, by two independent branches of the router. The plan's conclusion
was right; it now rests on a measurement instead of a rendering.

THEN I RAN THE PLAN'S OWN VALIDATION INSTRUCTIONS AS WRITTEN, which is what produced the serious findings,
because a chore whose entire deliverable is four edited lines is worth reviewing mostly for whether its
gates can actually be satisfied and whether they can be satisfied falsely.

DEFECT ONE: TWO INSTRUCTIONS ARE UNSATISFIABLE, AND CHASING ONE OF THEM LEADS SOMEWHERE FORBIDDEN. F-02
asserts that searching `*.md` for the defective literal "returns nothing". It returns FIVE records: this
plan (7 hits), executed `ygb3nk` (3), executed `s7cu7n` (1), pending `9m4ujh` (1), and backlog `7gr0vr`
(1). E-02's Expected outcome and V-02's required evidence then both demand a WHOLE-REPO search returning
NO matches. That bar cannot be met, and the reason it cannot is that the records tree correctly QUOTES the
string it is describing, which must stay. Worse, two of the five live in `.aw/records/plans/executed/`,
which AGENTS.md forbids rewriting at all, so an executor working toward a green search is pointed at the
one edit the repository most firmly prohibits. The load-bearing half of F-02 does hold, and I verified it
separately: `grep -rn "(warning) finding" tests/ docs/` is empty, so no test, doc, spec, or golden pins
the parenthetical and `- Scope-Paths:` correctly needs no doc entry.

DEFECT TWO: A NEW TRAP NO PRIOR ARTIFACT RECORDS, and the one I judge most likely to have produced silent
over-reach. The loop body this plan rewrites, `print(f"  {d.rule}: {d.detail}")`, is BYTE-IDENTICAL in
FOUR places in `work_cmd.py` (lines 339, 345, 713, 719): the advisory loop AND the blocking loop in each
of the two verbs. E-01 says to change "the loop body" and locates the HEADING by a unique string, but the
loop body has no unique string at all. A search-and-replace satisfies the plan's letter while rewriting
the two refusal reports the plan's own Deferred section explicitly declines to touch, and no `V-*` would
have caught it: V-02 inspects the blocking HEADING, not its finding lines. So the plan's most explicit
non-goal was the thing its own instructions made easiest to violate.

DEFECT THREE: THE COVERAGE COULD HAVE PASSED VACUOUSLY, INCLUDING ITS NEGATIVE CONTROL. E-03 and V-01 ask
for an assertion that the captured output "contains" the real severity `error`. Measured: a PRE-FIX run
whose drift detail contains the word `error` satisfies `assertIn("error", out)` on the unfixed build. That
is not hypothetical, because the real `check.scope-drift` message is "1 changed path is outside the plan's
declared Scope-Paths" and the detail text is chosen by the test itself, so an executor writing a realistic
detail would hit it. The consequence is specific and bad: V-03 requires a negative control proving the new
tests go red on the pre-fix wording, and this shape makes the negative control go GREEN, which would be
read as the coverage being satisfied when it discriminates nothing.

DEFECT FOUR: AN IMPOSSIBLE SEQUENCE. E-04 instructs the executor to "Record a full-suite baseline BEFORE
applying E-01 and E-02", from inside an item declaring `- Depends on: E-03`. By the time E-04 runs, both
edits and the new tests exist, so the instruction cannot be followed where it is written. The same applies
to the negative control the Required-tests section demands. Both are pre-edit acts and now say so.

Three smaller corrections. The `addopts` marker expression is quoted as `-m 'not slow'` at two sites,
omitting `not livecorpus` (`pyproject.toml:171` reads `-q -n auto --dist=worksteal -m 'not slow and not
livecorpus'`). V-04 offers the touched file's `11 passed in 2.36s` as the base for a FULL-SUITE comparison
and compares counts rather than failing-node-id sets. And the authoring-commit citations read as though
`bb66aee9f` were current HEAD.

Two things the plan gets right that are worth recording. Its coordination analysis is exact and I checked
every part: `grep -ln "^- Scope-Paths:.*work_cmd"` returns precisely the two plans F-07 names, `9m4ujh`'s
`- Scope-Paths:` is quoted verbatim correctly, the four adjacent severity plans' paths are as stated with
none including `work_cmd.py`, and the line-disjointness claim holds concretely (`9m4ujh` owns `_in_scope`
at 451 and its callers at 680/685; this plan owns 336 and 710). Treating that as a coordination fact rather
than a runtime hazard, and therefore leaving `- Item-Dependencies: none`, is the correct reading of the
runner's isolation guarantees. And F-08's `chore` classification stands on the repository's own test:
`7gr0vr` carries no `- Blocks-Release:`, the gating work-kind set is `bug` alone, nothing parses the
heading, no user waits on it, and the adjacent line carries the accurate rule id. I specifically considered
whether this is the same class as a false CLI string I filed as `bug` earlier today and concluded it is
NOT: that one asserted a CAPABILITY a user would act on (that piping yields JSONL, which it does not),
while this one mislabels a tier on a line whose rule id is already correct and whose consequence
("not blocking") is already stated truthfully.

I did NOT run the bare full suite as a review baseline: this review modified no production file or test,
and E-04 as revised is what must establish the executing baseline.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | IN-SCOPE | E (evidence accuracy) | `grep -rln "advisory (warning)" --include="*.md" .` returns 5 records: this plan, `.aw/records/plans/executed/...ygb3nk...` (3 hits), `.aw/records/plans/executed/...s7cu7n...` (1), pending `9m4ujh` (1), backlog `7gr0vr` (1) | F-02 states "The same search across `*.md` returns nothing". False. The claim is load-bearing because E-02 and V-02 build a pass/fail gate on it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 rewritten with the re-measured counts, separating the half that HOLDS (no test/doc/fixture pins the literal) from the false absolute; notes that two of the five are executed plans which must not be rewritten |
| PR-102 | HIGH | IN-SCOPE | G (executability), D (invariants) | E-02 Expected outcome: "no occurrence ... survives anywhere in the repository"; V-02: `rg -n "advisory \(warning\)" .` returning "NO matches". AGENTS.md forbids changing what an executed plan records | The bar is UNSATISFIABLE, and the only way to approach it is to edit records that correctly quote the defect, two of them executed plans. An executor chasing a green search is pointed at a prohibited edit | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02, V-02, and Proposed-change 2 re-scoped to `--include="*.py"` (where zero IS reachable) plus the `tests/ docs/` check; an explicit prohibition on editing any record to clear a search; V-02 now also requires `git status --short` showing no record modified but this plan |
| PR-103 | HIGH | IN-SCOPE | E (testing rigor) | Pre-fix output with a realistic detail ("1 changed path is outside the plan's declared Scope-Paths (error-severity rule)") satisfies `assertIn("error", out)`: measured True | E-03 and V-01 ask the test to assert the output "contains" `error`. On the UNFIXED build that passes whenever the detail contains the word, so V-03's mandatory negative control would go GREEN and the coverage would discriminate nothing | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now forbids the bare whole-output assertion, requires a PER-LINE assertion (tier on the line carrying the rule id), and requires probe details free of tier words; V-03 requires stating which per-line assertion was used and that no bare `assertIn("error", out)` exists |
| PR-104 | MEDIUM | IN-SCOPE | E (evidence precision) | Same measurement as PR-103, applied to V-01's clause (c) "a finding line naming the tier `error` beside `check.scope-drift`" | V-01's evidence clause is satisfiable by the word appearing anywhere in the transcript, so the pasted proof would not establish the tier is on the finding's own line | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01(c) now requires quoting the SINGLE line carrying both the rule id and the tier, and requires the probe detail to contain no tier word |
| PR-105 | LOW | IN-SCOPE | E (validation commands) | `pyproject.toml:171` `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"` | E-04 and Required-tests both quote the configured marker expression as `-m 'not slow'`, omitting `not livecorpus` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both sites now quote the full expression |
| PR-106 | MEDIUM | IN-SCOPE | G (sequencing) | E-04 declares `- Depends on: E-03` while instructing "Record a full-suite baseline BEFORE applying E-01 and E-02" | The baseline and the negative control are pre-edit acts commanded from a post-edit item, so neither can be performed where the plan says. An executor either skips the baseline or reverts edits to manufacture one | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 recast as REPORTING a baseline captured as the first act of the execution turn, with an honest fallback (say so and compare against the tip; never invent a figure or revert to manufacture one); Required-tests carries the same note |
| PR-107 | LOW | IN-SCOPE | E (anti-regression) | V-04 cites "base run of the touched file recorded `11 passed in 2.36s`" as the comparison base for a BARE full-suite run; re-measured at review: `11 passed in 4.33s` for that file | A single file's count is offered where a full-suite baseline is needed, and the comparison is specified on counts rather than failing-node-id sets, so a swapped failure reads as no change | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 now requires the full-suite baseline from the start of the turn, comparison by failing-node-id SET, and explicitly labels `11 passed` as the touched file's own count and the wall time as machine-dependent context |
| PR-108 | LOW | IN-SCOPE | E (citation hygiene) | Plan cites `HEAD bb66aee9f` in the Concern, F-01, and the history line; actual review HEAD is `65ea492f7` | Authoring-time commits are written as though current, which a later reader resolves against the wrong tree | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three relabelled as the authoring commit, with the review re-measurement commit named beside them |
| PR-109 | HIGH | UNDER-SCOPE | A (correctness), G (scope fence) | `print(f"  {d.rule}: {d.detail}")` occurs at lines 339, 345, 713, 719 of `agent_workflows/work_cmd.py`: advisory and blocking loop in each of the two verbs | The loop body E-01/E-02 rewrite is BYTE-IDENTICAL to the blocking loop the plan forbids touching, and unlike the heading it has no unique locator. A search-and-replace satisfies the plan's letter while tiering both refusal reports, and NO `V-*` catches it because V-02 inspects the blocking HEADING only | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New F-09 records the four-occurrence measurement; E-01 requires locating the loop by its enclosing `if advisory:` block and editing exactly two of four; Proposed-change 1 and the Scope check state the four-line edit count; V-02 requires the blocking finding lines shown untiered and the remaining occurrence count stated as two; the Deferred row reframed as an ACTIVE constraint |
| PR-110 | MEDIUM | IN-SCOPE | E (evidence standard) | F-05's evidence is wording "rendered in memory"; driven instead through `work_cmd._validate_plan_via_engine`: `advisory = [('check.scope-drift','error'), ('check.review-decision-unescalated','warning')]`, `blocking = []` | The finding that decides the plan's entire shape (per-finding tiers over a batch parenthetical) rested on a rendering, which shows what output would look like but not that the MIXED state is reachable; reachability is the whole claim | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 upgraded with the driven measurement and an explicit note that the mixed case is real code behavior rather than a thought experiment; the conclusion is unchanged |
| PR-111 | LOW | IN-SCOPE | F (recorded decisions) | Sibling severity-truth plans: `xs557y` and `wm40yl` declare `CHANGELOG.md`; `tzjtg4` and `nwcf8j` do not | OQ-02 asserts "reasonable maintainers differ" without checking the repository's own practice, which is the claim a reviewer should test rather than repeat | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 now records the measured 2-2 split and why the two non-declaring plans are the closer analogues, so the balance is demonstrated rather than asserted; resolution (NO) unchanged and still non-blocking |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-02/V-02 demand a whole-repo search for the defective literal return zero, which five legitimate records prevent. Re-scope the search, exempt the records by name, or drop the check? | Re-scope to `--include="*.py"` and add an explicit prohibition on editing any record to clear a search | (a) Exempt the five records by name: REJECTED, because the exemption list would rot the moment another plan quotes the string, and a future reviewer would read a stale allowlist as authoritative. (b) Drop the confirming search: REJECTED, because it does real work; it is what proves no third EMITTING site was missed, which is the item's actual obligation. (c) Scrub the quotes from the records: REJECTED outright and now forbidden in the plan, since two are executed plans AGENTS.md protects and the quotes are the evidence trail the plan's findings rest on | Measured 5 `.md` hits including 2 under `plans/executed/`; AGENTS.md "Never change what a plan already in `.aw/records/plans/executed/` RECORDS"; `--include="*.py"` measured to return exactly the 2 emitting sites | yes |
| D-2 | The four identical loop bodies make over-reach easy and invisible. Add a locator instruction, add a V-item, or split the blocking-branch question into its own plan? | Add the locator instruction to E-01 AND the counter-evidence to V-02, keeping the blocking branch out of scope | (a) Instruction only: REJECTED, because the plan's existing non-goal was already explicit and still left the trap reachable; an instruction with no verification is what failed here. (b) Also tier the blocking lines, making the search-and-replace correct: REJECTED, because the plan's Deferred section reasons correctly that those headings misstate nothing, and widening a `chore` past its measured defect is exactly what the Fix Bar excludes. (c) A separate plan for the blocking branch: REJECTED, because there is no defect to carry; the Carrier-Declined row already explains why nobody owes that work | Counted 4 occurrences at 339/345/713/719; V-02 read and confirmed to assert only the blocking HEADING; the plan's own Deferred row and its Carrier-Declined reasoning | yes |
| D-3 | Is this defect genuinely `chore`, given that a near-identical false human-facing CLI string (`zdjhug`) is filed `bug` with `Blocks-Release: next`? | Concur with `chore` and carry no release gate | (a) Reclassify as `bug` and add `- Blocks-Release: next`: REJECTED. The plan must not invent a gate its backlog item does not carry, and the two cases differ on the repository's perceptibility test: `zdjhug`/`qdd6ey` assert a CAPABILITY a user acts on (that piping yields JSONL, which it does not), whereas this mislabels a tier on a line whose rule id is already correct and whose "not blocking" consequence is already true. (b) Raise it to the maintainer as an open question: NOT taken, because the item's author already recorded the `chore` reasoning explicitly against the stated test and nothing contradicts it | `7gr0vr` carries no `- Blocks-Release:` and `- Work-Kind: chore`; AGENTS.md gating set defaults to `bug` alone; AGENTS.md perceptibility test (user-perceptible impact, measured, not provable redundancy) | yes |
| D-4 | F-05 supported the plan's deciding conclusion with an in-memory rendering. Accept it, demand the executor prove it, or prove it at review? | Prove it at review and record the driven measurement in F-05 | (a) Accept the rendering: REJECTED, because reachability of the mixed state is the entire argument for the chosen shape, and a rendering cannot establish it; if the mixed batch were unreachable the batch parenthetical would be defensible and the plan's narrowing wrong. (b) Push it onto the executor as a spike: REJECTED as disproportionate, since the probe is three lines against a shipped function and a reviewer who can run it should not defer it | Drove `work_cmd._validate_plan_via_engine` with both drifts on a temp repo: `advisory` holds `('check.scope-drift','error')` and `('check.review-decision-unescalated','warning')`; the router's two independent append branches read in source | yes |

### Verdict

APPROVE WITH REVISIONS APPLIED. Eleven findings, all FIXED in place, none deferred, none left open. No
unfixed finding at or above the `HIGH` gate threshold, so no escalation to a `- Blocking: yes` question is
owed. Both pre-existing open questions remain `- Blocking: no` and `- Status: resolved`; OQ-02's rationale
was strengthened with measured precedent rather than reopened. `- Readiness: go-pending-approval` written;
`- Status:` to be set `reviewed` through `aw ipd set` so the transition is tool-attributed. Human approval
is still required before execution.
