# Review findings: plan r3xk1f

- Subject-Id: r3xk1f
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `ccab69f1`. The plan on disk was byte-identical to the sealed lane input
(`source_sha256` `5dd953c872e772d927c438d684c0033d2b5286bc583d904cef4ce848bc882f86`, re-computed and
matched) and `git status --short` was empty, so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0; the watermark is unchanged at
04 (no E-item added; every finding was fixed by strengthening an existing item, correcting an
unsatisfiable evidence demand, or resolving the open question).

DISCLOSURE: same agent/model authored this plan AND applied the PR-007 corrections it already carries
from the orchestrator's review, so this is a SELF-REVIEW twice over. Its value therefore rests entirely
on EXECUTING claims rather than re-reading them, and this round did: it ran the parity suite, drove
`IPD-M107` both ways on a purpose-built fixture, ran three different `Kind`-scan shapes against the real
misclassifying plan, and grepped the long variant's step files for the two anchors E-01 depends on.

WHAT THIS PLAN GETS RIGHT, verified rather than accepted. The siting is correct and I confirmed the
split it prescribes: `aw ipd lint --phase review-finalize` appears ONLY in `03-resolve-and-finalize.md`
in the long variant, and `- Readiness:` appears only there too (zero occurrences in `02`), so putting
the revision half in `02` and the readiness/exhaustion half in `03` follows the existing structure
rather than imposing one. The PR-007 correction it inherits holds up: `plan-review-long.md` is indeed a
step index, the test that refuses instructions placed there is real, and its docstring does record the
mistake as "made twice". F-1's anchor is exact (`plan-review.md:121`). F-5's underlying hazard is real:
`m7gvuz` is `- Kind: child` and contains `Kind: orchestrator` eleven times. And R6's reasoning is sound
and important.

WHERE THIS REVIEW SPENT ITS EFFORT: the plan's product is PROSE, and it had not reckoned with what that
costs. Three of its four V-items demanded evidence no executor could produce, and its declared new test
file had no buildable content. Separately, the one shipped backstop E-03 leans on does not cover E-03's
own case.

**1. `IPD-M107` does not cover the case E-03 exists for (PR-202, HIGH).** This is the finding I would
most want a human to see. E-03 and the Concern both lean on `ipd_lint` refusing an unattested
`- Readiness:`, and I nearly recorded that as a clean backstop. Driving it showed otherwise:
`check_readiness_attestation` is EVIDENCE-BASED, not status-based, and fires only when the field is
present AND the plan's `## Workflow history` matches none of `/plan-review`, `APPROVE`, `NO-GO`,
`REJECT`. Its own comment says why it is deliberately not keyed on `Status`. So in this plan's exact
target scenario, a review that RAN and then exhausted its repair budget, the history already names a
review, and `IPD-M107` cannot distinguish a correct absence from a fabricated value. I verified both
directions on a minimal fixture: with a verdict-free history, injecting `go-pending-approval` yields
`IPD-M107`; removing it clears it. The consequence is that the workflow INSTRUCTION carries the entire
weight in the case that matters, which the plan had not stated. V-03 now requires the instruction be
quoted, requires the `IPD-M107` demonstration BOTH ways, and warns that a fixture whose history already
names a review makes that evidence vacuous, which is the mistake this review made first.

**2. Three of four V-items were unsatisfiable, all for the same root cause (PR-202, HIGH).** Nothing in
`agent_workflows/` executes a workflow body (the only references are docstrings and CLI help), so:
V-01's "paste three cases: an orchestrator checked, a child plan not checked" describes behaviour no
code exhibits; V-02's "paste the budget's resolution showing CLI-over-default" describes a resolver
reachable only from a CLI flag this deliverable does not have; and V-03's "confirm the code path
contains no write of `- Readiness:`, by grep" names a code path that does not exist. Left as written, an
executor either reports failure on correct work or, far more likely, writes something that LOOKS like
the demanded evidence. Each is now reworked into a demand that is both satisfiable and honest about its
own nature: a quotation of the instruction plus a demonstration against real fixtures, labelled as a
prose-correctness claim rather than a test.

**3. The declared new test file had no buildable content (PR-201, HIGH).** `Scope-Paths` declared
`tests/test_plan_review_orchestrator_repair.py`. The only assertion available over a prose deliverable
is a prose pin, and this repository has deleted that shape TWICE with the reason recorded in the very
files this plan cites: the parity test's docstring says descriptive wording "is rewritten legitimately
and often, and pinning it produced failures that told the author nothing except that they edited
prose", and `test_spec_review_attestation.py::WorkflowPackageTests` opens "ONE table replaces eleven
separate `assertIn` tests over the body and README. Those eleven were almost entirely PROSE PINS ... A
git repository already records when prose changes". Declaring the file invites an executor to
re-create exactly that in order to justify the declaration. The path is withdrawn; the existing parity
test is the whole test surface, and the Scope check now says a new test file becomes legitimate only if
a code-side helper is genuinely needed.

**4. The retry budget was described as configurable when it cannot be (PR-203, MEDIUM).** E-02 said to
follow `resolve_retry_budget`'s CLI-over-policy-over-default precedence. That resolver takes a CLI value
and is reached from `--retry-budget`; a markdown file an agent reads has no flag surface, so there is no
precedence to follow and V-02's demanded trace was unproducible. The in-tree precedent for this exact
decision is explicit and I applied it rather than inventing one: `enforce_orchestrator_probe_gate`'s
docstring records "THE RETRY BUDGET IS THE EXISTING FLAG, DECIDED AND RECORDED", reuses the flag,
ACCEPTS its default of 2 over a maintainer ruling that named 3, and gives the reason as "a second retry
knob is exactly the re-fork this Set spends an item preventing". E-02 now states 2 as a number in prose,
cites `resolve_retry_budget(None) == 2` as its source, forbids building a knob, and says a real knob
would be a code change to report rather than slip in.

**5. V-04 could be satisfied by a log that defeats its own purpose (PR-204, MEDIUM).** "Record what the
check reported and what changed" is satisfiable by a log reading "repaired" twice. Deletion and
relocation BOTH make the check pass, so unless the log carries a fact that differs between them it
cannot make the deletion failure mode auditable, which is its entire reason to exist. E-04 and V-04 now
require the row count before and after, or a stated alternative discriminator with its justification.

**6. F-5 named the wrong scan shape (PR-205, LOW).** The hazard is real but mis-attributed, and an
executor could satisfy the letter while leaving it undescribed. Measured three ways against `m7gvuz`:
`grep -l 'Kind: orchestrator'` MATCHES it and so misclassifies; a first-match regex `Kind:\s*(\S+)`
returns `child`; an anchored `^- Kind:` returns `child`; and `ipd_lint.parse` returns `child` because it
bounds the metadata region. So the failing shape is CONTAINMENT, not first-match, and the instruction
should name that specifically.

**7. OQ-01 was left open where the repository decides it (PR-206, MEDIUM).** Resolved to the review
round record. The authored rationale already proposed that and its reasoning holds, but two in-tree
facts settle it: `.aw/records/reviews/README.md` defines `## Round <n>` as append-only with the last
round current and already designates it for reviewer-authored judgement detail; and the workflow history
is one line per lifecycle TRANSITION, whose readers treat every row as one, so non-lifecycle attempt
rows would corrupt a log other tooling consumes. I also recorded why the question's own self-reporting
objection does not discriminate: the log is agent-authored in either location.

WHAT I DELIBERATELY DID NOT CHANGE. The four-item shape is right: the call, the loop, and the two halves
of what happens when the loop fails. The `Kind` guard keeping non-orchestrator review untouched is
correct. I did not weaken R6, and I did not soften the plan's prohibition on repairing a real
orchestrator while testing; I strengthened it, adding "use a fixture you author" to three separate
items. F-8 was RAISED from LOW to MEDIUM, because "prose has a lower assurance ceiling" turned out not
to be a footnote but the root cause of four other findings.

VALIDATION RUN AT REVIEW. `aw ipd lint --phase author` and `--phase review-finalize` conform. Carrier
rule CLEAN at `pre-transition` (OQ-01 now `resolved`, so it owes nothing).
`python3 -m pytest tests/test_plan_review_parity.py -o addopts="" -q` -> `5 passed`. Bare suite:
`1 failed, 7305 passed, 3 skipped, 2 xfailed`, the single failure being the corpus-pinned
`test_no_pending_plan_is_refused_on_a_verdict_today` naming three `reaskscore` plans another party is
editing, proven pre-existing during child 01's review by stashing all edits and re-running the node.
`aw check all` reports 0 findings against this plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | OVER-SCOPE | E (testing); prose-pin precedent | `tests/test_plan_review_parity.py` module docstring; `tests/test_spec_review_attestation.py::WorkflowPackageTests` docstring; no workflow-body executor in `agent_workflows/` | The declared `tests/test_plan_review_orchestrator_repair.py` had NO buildable content. Nothing executes a workflow body, so the only available assertion is a prose pin, and this repository has deleted that shape twice with the reason recorded ("fails on every legitimate reword and catches no defect"). Declaring the file invites an executor to re-create it to justify the declaration. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Path withdrawn from `Scope-Paths`; the existing parity test named as the whole test surface; the prose-pin prohibition quoted in the Scope check; a new test file made legitimate only if a code-side helper is genuinely required. Recorded as F-10. |
| PR-202 | HIGH | UNDER-SCOPE | E (verification); `ipd_lint.check_readiness_attestation` | `_REVIEW_EVIDENCE_RE` matches `/plan-review\|APPROVE\|NO-GO\|REJECT`; two lint runs on a minimal fixture; the checker's own "not keyed on Status" comment | TWO defects with one root cause. (a) `IPD-M107` is evidence-based, so in E-03's OWN case (a review that ran, then exhausted) the history already names a review and the rule CANNOT distinguish a correct absence from a fabricated value - the backstop does not cover the target case. (b) Three of four V-items demanded evidence no executor can produce: a call-site behaviour test, a budget resolution trace, and a code-path grep, none of which exist for a prose deliverable. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | V-01/V-02/V-03 reworked into satisfiable demands labelled as prose-correctness claims; V-03 requires the instruction quoted, the `IPD-M107` demonstration BOTH ways, and warns that a fixture whose history names a review makes the evidence vacuous; the residual hole recorded as F-9 so the plan does not overclaim its backstop. |
| PR-203 | MEDIUM | IN-SCOPE | C (architecture); retry budget | `resolve_retry_budget` signature (takes a CLI value); `--retry-budget` registration; `enforce_orchestrator_probe_gate` docstring "THE RETRY BUDGET IS THE EXISTING FLAG, DECIDED AND RECORDED"; `resolve_retry_budget(None) == 2` | E-02 described a configurable budget following a CLI-flag resolver's precedence, which a prose workflow cannot have; V-02 then demanded a resolution trace nobody could produce. The in-tree precedent for this exact call is explicit and was not cited. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 states 2 as a number in prose, cites the verified default as its source, follows the probe gate's recorded precedent by name, forbids building a knob, and routes a real knob to a reported code change. V-02's evidence changed to a quotation. Recorded as F-11. |
| PR-204 | MEDIUM | UNDER-SCOPE | E (verification) | V-04's stated purpose against its stated evidence | "Record what the check reported and what changed" is satisfiable by a log reading "repaired" twice, which cannot distinguish deletion from relocation - the single distinction the log exists to make, since both make the check pass. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 and V-04 now require the row count before and after, or a stated alternative discriminator with its justification. Recorded as F-12. |
| PR-205 | LOW | IN-SCOPE | A (correctness); the F-5 claim | `grep -l 'Kind: orchestrator'` matches `m7gvuz`; first-match regex and anchored read both return `child`; `ipd_lint.parse` returns `child` | F-5's hazard is real but mis-attributed: the shape that fails is a CONTAINMENT scan, not any first-match read. "Read the first bullet" is right but does not name the actual hazard, so an executor could satisfy the letter while leaving it undescribed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The convention and V-01 now name the containment shape with all three measurements, and record that `doc.meta_fields` is the safe read. Recorded as F-13. |
| PR-206 | MEDIUM | IN-SCOPE | G (executability); OQ resolution | `.aw/records/reviews/README.md` (append-only rounds, last round current, reviewer-authored detail); `aw ipd set` writes one line per lifecycle transition | OQ-01 was left open although the repository decides it: the round record is the designated home for reviewer-authored review detail, and the workflow history is a lifecycle log whose readers treat every row as a transition, so attempt rows would corrupt a log other tooling consumes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 resolved to the round record with both facts cited and the self-reporting objection addressed; E-04 carries the decision and the append-only constraint; `Carrier-Declined` restated. |
| PR-207 | MEDIUM | UNDER-SCOPE | E (verification); baseline honesty | run at review `1 failed, 7305 passed, 3 skipped, 2 xfailed`; the failing node id | The plan named no suite baseline, and one failure exists that is NOT this plan's: a corpus-pinned test naming three `reaskscore` plans another party is editing. Without the baseline an executor could chase a phantom regression or "fix" a co-worker's plans. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Baseline recorded with the failing NODE ID, its cause, the proof it is pre-existing, and an instruction not to touch those plans; criterion restated as AFTER-minus-BEFORE node ids being empty. Also added "use a fixture you author" to the three fixture-bearing items. |
| PR-208 | LOW | IN-SCOPE | F (honest documentation) | F-8 as authored at LOW | F-8 read as a footnote about assurance ceiling, when the prose nature of the deliverable is the ROOT CAUSE of PR-201 through PR-203. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-8 raised to MEDIUM with the consequence spelled out (it is what made three V-items unsatisfiable and the test file unbuildable) and this child's claim narrowed to "makes the violation repairable", with enforcement attributed to child 03. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Where should the attempt log live (the plan's own OQ-01)? | The current `## Round <n>` of the typed review record, append-only per round. | The plan's `## Workflow history` (rejected: `aw ipd set` writes one line per lifecycle TRANSITION and its readers - `aw attention`, the lifecycle-transition check, `last_history_at` - treat every row as one, so non-lifecycle attempt rows would corrupt a log other tooling consumes). A separate untracked scratch file (rejected: the reviews README states a decision surviving only in a transcript or scratch file "is not auditable"). | `.aw/records/reviews/README.md` defining append-only rounds, last-round-current, and a reviewer-authored decisions section; `aw ipd set`'s one-line-per-transition behavior | yes |
| D-2 | Should the declared new test file be kept, made optional, or withdrawn? | Withdrawn from `Scope-Paths`. | Keeping it and letting the executor decide (rejected: an undeclared-but-expected file is exactly what produces a prose pin written to justify a declaration). Keeping it with a `--scope-ack` note (rejected: reconciling a never-created file as unchanged is noise, and the honest statement is that no test belongs there). | the two module docstrings recording that this repository deleted prose-pin suites twice; no workflow-body executor exists in `agent_workflows/` | yes |
| D-3 | The budget cannot be configurable in prose. Adopt what, and on whose authority? | Adopt 2, stated as a number in the workflow, citing the shipped default; no knob. | Building a real knob (rejected: that is a code change with a declared path and a test, outside this plan's scope, and it forks a second retry surface). Leaving "configurable" in place (rejected: it describes a capability that does not exist, which is the dishonest-documentation failure the plan itself warns about for the policy tier). | `enforce_orchestrator_probe_gate`'s recorded decision to reuse the existing flag and accept 2 over a ruling naming 3, with its stated anti-refork reason; `resolve_retry_budget(None) == 2` verified in-process | yes |
| D-4 | `IPD-M107` does not cover E-03's own case. Fix the rule, or narrow the claim? | Narrow the claim: record the hole as F-9, put the weight on the instruction, and require the demonstration both ways. | Changing `check_readiness_attestation` to key on `Status` as well (rejected on the checker's OWN recorded reasoning: a review legitimately writes the field in the same pass that sets `reviewed`, and `plan-review-long` can leave a plan at `to-review` with a recorded NO-GO, so status-keying would refuse both legitimate shapes). Filing a backlog item (not taken: the rule is behaving as designed and the gap is a limit of what a deterministic check can see, not a defect). | `check_readiness_attestation` body and its "DELIBERATELY EVIDENCE-BASED, NOT AUTHORSHIP-BASED" comment; two lint runs proving both directions | yes |
