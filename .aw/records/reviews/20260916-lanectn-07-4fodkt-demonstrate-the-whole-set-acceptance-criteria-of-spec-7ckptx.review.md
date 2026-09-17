# Review findings: plan 4fodkt

- Subject-Id: 4fodkt
- Subject-Type: ipd
- Reviewed-At: 2026-09-16
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval
- Set: lanectn
- Order: 7

## Round 1

DISCLOSED SELF-REVIEW, stated first because it bounds the value of everything below. I AUTHORED this
plan earlier in the same session, so this round is weaker evidence than an independent review and must
be read as such. Two consequences a later reader should hold onto: a defect rooted in an assumption I
made while authoring is one I am least likely to see here, and the one BLOCKER below was found only
because the plan's own instruction to measure rather than assume was applied to the plan itself. An
independent round would be worth funding before this plan's own conclusions are relied upon; it is not
required for the plan to be executable, because every claim it makes is re-derived at execution time by
its E-01.

Scope ledger: exactly one candidate, the plan named in the invocation. Nothing else was enumerated.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | G. plan executability (right-sizing / conceptual density) | the pre-revision `E-02`; spec `.aw/records/specs/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md:479` onward | **THIRTY-ONE ACCEPTANCE CRITERIA IN ONE E-ITEM, WHICH THE COUNT-BASED LINT CANNOT SEE.** The pre-revision plan demonstrated every live criterion in a single `E-02` and validated it with a single `V-02`. `aw ipd lint` reported `clean` because the structural thresholds are >18 leaves / >5 groups and the plan had 4 leaves in 3 groups, which is exactly the case the rubric warns a passing size lint does NOT clear. Measured, the criteria fall into SIX independent requirement families (R1 n=4, R2 n=5, R3 n=3, R4 n=10, R5 n=8, R6 n=1), each with its own evidence surface, so one item bundled six independent test-surfaces and could not be verified as one pass. The concrete harm is specific rather than aesthetic: a single `V-02` demanding evidence for 31 criteria is satisfiable by an executor that pastes evidence for the easy ones and asserts the rest, which is the precise greenwash this plan exists to prevent. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `E-02` split into six family items `E-02`..`E-07`, each carrying the family's own hazards, with a seventh closing reconciliation. `V-*` re-authored 1:1 as `V-02`..`V-07`, each demanding that family's specific evidence. Downstream items renumbered to `E-08`/`E-09`; `Highest E allocated` 04 -> 09. `Cohesion rationale` records why the count grew at review, so the split is not later "simplified" back. |
| PR-002 | MEDIUM | IN-SCOPE | A. correctness (a false premise in an open question) | `runner_shared.evaluate_set_retirement`; measured both ways, output pasted in the plan's resolved `OQ-01` | **`OQ-01` RESTED ON A WORRY THAT IS ALREADY PREVENTED, so it invited an unnecessary edit to an approved plan.** It asked whether `h0zljh` E-02 should be annotated as delegated, partly out of concern the parent might retire with the verification outstanding. Measured, `evaluate_set_retirement` requires EVERY child's on-disk `Status:` to be exactly `executed`: in this worktree it returns `eligible: False, reason: unfinished-children, detail: ... 1 child(ren) that are not 'executed': 4fodkt (to-review)`, and on `main` (without this plan) `eligible: True`. So AUTHORING the plan is itself the fix, and no edit to the parent is needed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `OQ-01` resolved from that evidence with both measurements pasted, `Status: open` -> `resolved`. The documentation nit is recorded as a maintainer PREFERENCE rather than a defect, and no edit is made to `h0zljh`. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. testing (a criterion's anti-cheat clause) | spec `:607` (`A14b`) | **`A14b`'s ANTI-CHEAT CLAUSE NEEDED TO BE BINDING, NOT MENTIONED.** The pre-revision plan named `A14b` as the criterion the parent omitted but did not make its self-defeating case an instruction. The criterion states that a test achieving the isolated behavior by making the rule report CLEAN FAILS the criterion, because that discards the dirty-path list the report exists to print and leaves the shared-tree refusal unreachable. Without an explicit instruction, an executor meeting that condition would most likely reinterpret the criterion as satisfied. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | `E-06` now instructs that if the implementation reports CLEAN, `A14b` is recorded **FAILED** rather than reinterpreted, and `V-06` makes recording FAILED the only satisfying evidence in that case. |
| PR-004 | MEDIUM | UNDER-SCOPE | A. correctness (idempotence half-proof) | spec `A4`, quoted at `:499` | **`A4` IS A TWO-HALF CRITERION AND ONLY ONE HALF IS THE OBVIOUS ONE.** It requires that re-running an attempt's collection leaves the lane's contribution exactly once AND that a sibling lane's contribution is still present. A test proving only the once-only half passes while silently losing a sibling's work, which is a data-loss shape. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `E-03` and `V-03` now require both halves shown separately, with the reason stated so the second is not dropped as redundant. |
| PR-005 | LOW | UNDER-SCOPE | E. testing (evidence reuse across criteria) | spec `A10`, `A10b`, `A10c`, `A10d`, `A10e` | **THE R4 FAMILY INVITES ONE OBSERVATION STANDING FOR FIVE CRITERIA.** Five `A10*` ids are adjacent and related, so a single run touching the area could plausibly be offered as evidence for all of them, which would report five demonstrations from one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `E-05` forbids collapsing the `A10*` group; `V-05` requires ten individual results and states that an observation reused across two criteria does not satisfy the item. |
| PR-006 | LOW | IN-SCOPE | D. anti-regression (a stale list becoming authoritative) | the plan's own `E-01`; `h0zljh` E-02's enumeration | **THE FAMILY SPLIT INTRODUCED A NEW WAY TO STRAND A CRITERION,** which the fix for PR-001 created and which must not be left implicit: once items are keyed to families, a criterion that MOVES family (or a new criterion added to the spec) could fall between items and be demonstrated by nobody, reproducing the exact failure this plan exists to fix, one level down. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `E-01`'s derivation is declared authoritative over the authoring-time counts, item BOUNDARIES are fixed while MEMBERSHIP follows E-01, and `E-07` adds a closing reconciliation asserting every live id appears in exactly one item with a verdict, neither missing nor double-counted. `V-07` requires that reconciliation be produced by comparing the two lists and pasted, not asserted. |
| PR-007 | LOW | IN-SCOPE | B. security / privacy (evidence artifacts leak local paths) | the plan's own `E-08` deliverable | NOT A DEFECT INTRODUCED HERE, recorded so it is not lost: a verification record whose whole purpose is pasting real command output is an unusually likely carrier of absolute local paths and machine identifiers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Already required, and confirmed retained after the split: `V-08` demands `aw sanitize --agent` output showing clean, with the reason stated. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Split the 31-criterion item, or leave it and rely on the executor's diligence? | SPLIT, by requirement family, into six demonstration items plus a closing reconciliation. | (a) Leave it as one item, rejected: the plan's entire reason for existing is that unverified work gets marked complete, so shipping it with a single unverifiable item would reproduce the defect it fixes. (b) One item per criterion (31 items), rejected: it would breach the 18-leaf structural threshold and fragment evidence that genuinely shares a fixture, buying no additional rigor. | The rubric's density diagnostics (multiple independent test-surfaces; verifiable as several independent passes) at `.aw/system/workflows/plan-review/plan-review.md:492`; the measured family clustering R1 n=4 / R2 n=5 / R3 n=3 / R4 n=10 / R5 n=8 / R6 n=1 derived from spec Section 4 | yes |
| D-2 | Where should the family boundaries fall? | The spec's own requirement families, with E-01's derivation governing MEMBERSHIP and the item boundaries held fixed. | (a) Split by test FILE, rejected: it would key the plan to the current test layout, so moving a test would silently re-scope an item. (b) Split by even count (roughly 5 criteria each), rejected: it would put unrelated criteria in one item and separate ones that share a fixture, which is arbitrary and would need re-deriving every time the spec changed. | The spec draws these boundaries itself: every criterion cites its requirement ids, so the families are the spec's structure rather than the reviewer's invention | yes |
| D-3 | Resolve `OQ-01` from evidence, or leave it for the maintainer? | RESOLVE the factual half from evidence (no parent edit needed) and leave only the cosmetic preference to the maintainer. | Leave the whole question open, rejected: the load-bearing half is a measurable fact about the retirement gate, and `plan-review` Step 3.1 forbids asking the human what the repository already answers. | `runner_shared.evaluate_set_retirement` executed against both trees; both results pasted into the plan's `OQ-01` | yes |
| D-4 | Should this plan edit `h0zljh` to annotate its E-02 as delegated? | NO. Leave the parent untouched. | Annotate it, rejected on two independent grounds: the retirement gate already prevents the harm (D-3's measurement), and editing an `approved` plan's checklist to make this plan's scope look complete is the move the convention forbids. | `AGENTS.md` on not editing another artifact's approved checklist; the measured gate behavior | yes |

HONEST LIMITS of this round, stated because a self-review's limits are the part most likely to be
skipped:

- IT IS A SELF-REVIEW. I authored the plan. An assumption baked in at authoring is the defect class
  this round is least able to detect.
- I DID NOT DEMONSTRATE ANY ACCEPTANCE CRITERION. This review verified that the plan's CLAIMS about
  the spec are true (36 total ids, 5 withdrawn by `R3.3a`, 31 live, `A14b` live and omitted by the
  parent, `A14b` citing `R5.4`/`R6.1`) and that the retirement mechanism is as described. Whether the
  31 criteria actually PASS is the plan's job, not this review's, and nothing here should be read as
  evidence that spec `7ckptx` is satisfied.
- I DID NOT RUN THE SUITE for this review. No product code is touched by the plan or by this review;
  the plan itself requires a bare `python3 -m pytest` as a regression fence at execution time.
- THE FAMILY COUNTS ARE FROM 2026-09-16 and will be stale if the spec changes. That is why they are
  written as an authoring-time measurement that `E-01` overrides rather than as fixed truth.
