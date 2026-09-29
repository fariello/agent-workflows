# Review findings: plan fx5op3

- Subject-Id: fx5op3
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `f927d5ff` in a lane worktree. No pre-review snapshot was needed: the plan was
committed and unmodified, and the lane-input copy is byte-identical to the tracked file (`diff`
reported no output). Structural preflight `aw ipd lint --phase author --agent` reported `clean` /
exit 0 with no advisories; `--phase review-finalize` still conforms after every revision below.

THE DECISION IS CORRECT AND I RE-DERIVED ITS ENTIRE BASIS RATHER THAN CHECKING THE PROSE. The plan's
base was `7c215fa7`; at review the corpus has grown by 55 files, which is a useful robustness test of
an invariant claim. Over all 1018 tracked `.ipd.md`:

```text
TOTAL tracked .ipd.md: 1018
   ('executed', False) 421      ('executed', True) 419
   ('not-executed', False) 4    ('not-executed', True) 1
   ('pending', False) 85        ('pending', True) 51
   ('superseded', False) 28     ('superseded', True) 9

PRE-REVIEW plans carrying the field (tree-wide): 0
```

And the pending tally has exactly TWO non-empty cells, which is a stronger statement than "the cross
cells are empty":

```text
PENDING count: 136
   ('reviewed', True) 51
   ('to-review', False) 85
```

The three refusal paths all reproduce, with the plan's quoted strings intact:

```text
ORIGINAL:   disposition=conforming  M107=0
BACKFILLED: disposition=error       M107=1
      IPD-M107 Readiness: 'go-pending-approval' is a REVIEW OUTPUT but no review verdict appears in '## Workflow history'.

recheck_conditions -> may_write=False
  refusals: ('the plan has NO `- Readiness:` field. A re-check RE-EVALUATES a recorded readiness; it
             does not mint one. Absence means no review recorded a signal, and writing a value here
             would assert a review that never happened.',)
```

F-01, F-02, F-03, F-05, F-06, F-08 and F-10 all verified as stated (F-01's counts have moved AGAIN,
to 51/85, which is why its own no-absolute-counts rule is right). Three findings needed correction.

PR-001 IS THE ONE THAT CHANGES WHAT GETS WRITTEN. F-09 claims a `reviewed` plan may legitimately lack
the field via the R6 orchestrator-exhaustion path. The workflow's `IPD-S407` section says otherwise,
in the same sentence that mandates the absent field:

```text
4. **Honest exhaustion (R6):** If the 2-attempt budget is exhausted with violations unresolved, the
   plan remains `- Status: to-review`, the findings are recorded in the review round, and
   `- Readiness:` is left ABSENT.
```

So R6 produces `(to-review, absent)`, the same cell as every other unreviewed plan, and is an
INSTANCE of the invariant rather than an exception to it. The authored finding read only the second
of the workflow's two R6 statements (the `## Step 4` field exception, which omits the status). I
checked for any other producing path: those two passages are the only readiness-absence instructions
in `plan-review.md`, `plan-review-long.md` contains no readiness text at all, and sweeping the
`pending/` tree of the last 12 commits finds ZERO `(reviewed, absent)` plans ever.

That error had three dependents, which is why it is HIGH rather than LOW. E-02's required element (4)
would have written the nonexistent carve-out into a tracked README. E-03's decision to assert the
partition one-directionally was justified by it ("or an R6 plan would break the suite"), which is
false; I kept the restraint but re-based it on the real reason, that the mirror is an open maintainer
decision (OQ-01), and measured that the mirror currently holds exactly (51 of 51), so a bidirectional
test would pass today and the restraint must be deliberate rather than accidental. OQ-01's deferral
rationale rested on it too, arguing a required-at-`reviewed` rule would need an R6 exemption; it
needs none. OQ-01 stays deferred on the policy ground alone, and I recorded the withdrawal explicitly
so whoever picks up `l0ixig` does not inherit a false technical obstacle.

PR-002 IS AN IMPLEMENTABILITY DEFECT. E-03 names three predicates and instructs "build the modified
text IN MEMORY or under `tmp_path`". In memory is impossible for three of the four properties:

```text
ipd_lint.check_readiness_attestation(doc: ParsedDoc)   -> AttributeError: 'str' object has no attribute 'meta_fields'
plan_readiness.is_plan_review_approved(plan_path: Path) -> AttributeError: 'str' object has no attribute 'read_text'
plan_readiness.recheck_conditions(repo_root, plan_path, plan_text=None)  -> needs the path pair
```

I found and verified the working shapes rather than only reporting the breakage: `ipd_lint.lint_text`
(a text entry point the plan never names) for property 2, and `tmp_path` plus, for property 4, a bare
`git init -q` temp repo root. All four arms were driven successfully at review.

PR-003 IS A CLAIM THAT IS TRUE BY ACCIDENT AND STATED AS A RULE. F-04 says the predicate "ALREADY
REFUSES EVERY FIELD-ABSENT PLAN". It refuses all 85, but not because the field is absent: the absent
branch falls through to a back-compat prose fallback for plans reviewed before the field existed.
Measured, adding one approving review record to a field-absent plan and changing nothing else:

```text
absent + NO review record : False
absent + approving review : True   <- the FALLBACK arm
```

This strengthens the decision rather than undermining it (absence is a meaningful, fully-supported
state with correct behavior of its own, not an inert one), but it obliges E-03's property 3 to pin
that arm, or a future deletion of the fallback would leave the test green.

RIGHT-SIZING: four E-items over two files, each one concern. E-01 is a measure-before-you-write item
and E-04 a verify-and-close item, both appropriate for a plan whose deliverable is a recorded
decision. No `IPD-Z602` fired. P16 compliance is a stated constraint of E-03 and the scope fence now
repeats it.

A NOTE ON THIS PLAN'S OWN FIELD, since it is the subject matter: while authored the plan correctly
carried NO `- Readiness:`, a live instance of the invariant it records; the field now present was
written by this review, which is the provenance rule the plan is about.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness; G. Plan executability | plan F-09; `.aw/system/workflows/plan-review/plan-review.md` `IPD-S407` section, quoted "the plan remains `- Status: to-review` ... and `- Readiness:` is left ABSENT" | F-09 is factually wrong: R6 leaves the plan at `to-review`, not `reviewed`, so "a `reviewed` plan may legitimately lack the field" describes a state that does not occur and never has (0 across 12 commits of pending trees; only two readiness-absence passages exist in the workflow and `plan-review-long` has none). The error had three dependents: E-02's element (4) would have written it into a tracked README, E-03's one-directional restraint was justified by it, and OQ-01's deferral rested on it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-09 corrected in place with the falsifying quotation and the searches ruling out another path; F-11 added to track the three dependents. E-02 element (4) rewritten as the PROVENANCE nuance that genuinely survives (absent means no verdict RECORDED, not no review ATTEMPTED) with an explicit prohibition on the false claim. E-03's restraint re-based on OQ-01 being an open maintainer decision, with the measurement that the mirror holds 51 of 51 today. OQ-01's rationale rewritten, withdrawing the false obstacle explicitly. Concern, Scope and V-02 corrected. |
| PR-002 | HIGH | IN-SCOPE | E. Testing; G. Plan executability | plan E-03 constraints (quoted "build the modified text IN MEMORY or under `tmp_path`"); measured signatures of `ipd_lint.check_readiness_attestation`, `plan_readiness.is_plan_review_approved`, `plan_readiness.recheck_conditions` | E-03 is partly unimplementable as written. None of the three named predicates accepts text: they take a `ParsedDoc`, a `Path`, and `(repo_root, plan_path)` respectively, each raising or refusing when handed a string, so the "IN MEMORY" option is unavailable for three of the four properties and an executor would discover this only mid-implementation. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03's constraint bullet now states the measured signatures with the exact errors, and names the working call shapes, each verified at review: `ipd_lint.lint_text(text, checkpoint=..., directory="pending")` for property 2, `tmp_path` for properties 3 and 4, plus a temp repo root for property 4. The never-write-a-tracked-plan requirement is preserved as the binding constraint. V-03 now requires stating which properties used `tmp_path` and why. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness; E. Testing | plan F-04 (quoted "ALREADY REFUSES EVERY FIELD-ABSENT PLAN"); `plan_readiness.is_plan_review_approved`'s third arm | F-04 states an accidental property as a rule. The predicate refuses all 85 because none carries an approving review record, not because the field is absent: the absent branch falls through to a back-compat prose fallback and CAN return True. Measured True after adding one approving review record and changing nothing else. Left as written, E-03's property 3 would pass while a deletion of the fallback went uncaught. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 corrected with the third-arm measurement and an explanation of why this strengthens rather than weakens the decision (absence is a supported state with its own correct behavior). E-03 property 3 now additionally requires driving a field-absent plan whose history DOES carry an approving record and asserting True. V-03 requires that value pasted and names False there as a signal to investigate. |
| PR-004 | LOW | IN-SCOPE | Evidence accuracy | plan F-07 (quoted "sweeps the real tree"); `tests/test_ipd_lint.py::ReadinessAttestationTests` | F-07 mischaracterizes the existing coverage: `ReadinessAttestationTests` does not sweep the real tree. It is entirely fixture-driven, one table-driven test over a synthetic `_conforming_child()` fed through `lint_text`, with no corpus walk in the module. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07 corrected, and the conclusion strengthened rather than weakened: the gap is not a live sweep checking only the converse, it is that NO live-corpus readiness assertion exists at all (re-verified: no test module references `_READINESS_FIELD_PRESENT_RE` or `read_readiness`), so the partition is unguarded in every direction. |
| PR-005 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | plan `## Approval and execution gate` as authored (lifecycle steps and commit rule present; no declared surface, no approval summary, no ownership conditional) | The gate lacked a SCOPE FENCE declaring the intended surface for post-hoc reconciliation, lacked a statement of what a human would be approving, and instructed `aw ipd finalize` unconditionally rather than naming the runner as owner in a managed lane. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a scope fence as a declaration with a "made and then JUSTIFIED" clause and no stop directive, enumerating eight negative constraints (no `- Readiness:` edit anywhere, no change to the six pinned symbols, no mirror rule, no `AGENTS.md` hand-edit, no spec edit, no wider `19313eed` restoration, no other record renamed, no source-reading assertions). Added a "what a human would be approving" paragraph naming all three review corrections. Added the runner/executor conditional citing `AW-LIFECYCLE-ROLE-001`. Annotated the pre-existing E-01 stop directive as the SANCTIONED unsafe-condition kind so a later reviewer does not flag it. |
| PR-006 | LOW | IN-SCOPE | A. Correctness (tooling contract) | plan E-04 (quoted "so the close needs evidence but no gate handoff"); `check_engine.evaluate_blocking_close` | E-04 implies `--evidence` is needed to satisfy the close gate. Driven directly, the shared predicate returns `legitimate=True`, `severity=ok`, `reason="no release gate to preserve"` for this ungated item, so no evidence is required by any gate and an executor could misread a silent gate as a broken one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now states the predicate's actual verdict, says `--evidence` is a deliberate provenance choice rather than a gate requirement, tells the executor not to report a refusal if it is omitted and not to conclude the machinery is broken when it stays silent, and notes the item already carries `- Graduated-To: rdyabsent` so the handoff is recorded independently. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | F-09, which three other sections depend on, is factually wrong. Correct it and its dependents, or send the plan back? | CORRECT IT IN PLACE, marking the finding withdrawn rather than deleting it, and repair all three dependents. | (a) `REJECT - NEEDS REPLAN`: rejected, the plan's CONCLUSION (do not backfill) is independently correct and I re-derived its whole basis; only one supporting finding and its three restatements were wrong, which is a bounded edit. (b) Delete F-09 silently: rejected, a future reader would re-derive the same misreading from the same `## Step 4` passage, and recording the correction inoculates them; the same reasoning the workflow gives for costlier-error on citations. (c) Leave F-09 and let the executor discover it: rejected, E-02 would by then have written a nonexistent state into a tracked README, which is the one artifact this plan exists to make authoritative. | The `IPD-S407` section's quoted status sentence; only two readiness-absence passages in `plan-review.md`; `plan-review-long.md` has none; 0 `(reviewed, absent)` plans across 12 commits of `pending/` trees. | yes |
| D-2 | With F-09 corrected, should E-03 now assert the partition BIDIRECTIONALLY, since the stated obstacle to doing so was false and the mirror measurably holds? | NO. Keep the one-directional assertion, and re-base its justification on OQ-01 rather than on R6. | (a) Assert both directions: rejected, and this is the substantive call. The mirror property is the subject of OQ-01, an open maintainer decision this plan was explicitly not asked to make; asserting it in a test would enact unapproved policy and make a deferred question into shipped behavior that fails the suite for anyone who disagreed. (b) Keep one-directional but leave the R6 justification: rejected, it is false and would mislead. (c) Assert the mirror as a non-failing informational check: rejected, a test that reports without asserting is noise, and the repository's own principle is to prevent silent failure rather than add advisory tests. | The mirror measured holding exactly today (51 of 51 `reviewed` pending plans carry the field), which is precisely why the restraint must be deliberate and recorded; OQ-01 `Status: deferred`, `Owner: maintainer`, carried by `l0ixig`. | yes |
| D-3 | E-03's three predicates reject in-memory text. Weaken the constraint to `tmp_path` only, or find text-accepting entry points? | BOTH, per property: name `ipd_lint.lint_text` for property 2 (text-accepting, verified) and mandate `tmp_path` for properties 3 and 4 where no text API exists. | (a) Mandate `tmp_path` for all four: rejected, property 2 has a genuine text entry point and using a temp file there adds I/O and a failure mode for nothing. (b) Leave the constraint as authored and let the executor improvise: rejected, "in memory" is stated as an allowed option for properties that cannot support it, so the item as written misinforms; an executor following it hits three AttributeErrors. (c) Change the production signatures to accept text: rejected outright as over-scope and as modifying symbols this plan exists to PIN rather than touch. | Measured signatures and the exact `AttributeError` messages; `ipd_lint.lint_text(text, checkpoint=..., directory="pending")` verified producing `conforming` -> `error` with one `IPD-M107`; `recheck_conditions` verified under a bare `git init -q` temp root. | yes |
| D-4 | F-04's absence-implies-refusal claim is true only accidentally. Does the discovery of the back-compat fallback weaken the no-backfill decision? | NO, it STRENGTHENS it. Record the fallback, and require the test to pin it. | (a) Treat it as a counter-argument (absence is not uniformly safe, so backfill for determinism): rejected, it shows the opposite. The fallback is the mechanism by which pre-field plans are still evaluated correctly, so absence is a supported state with defined behavior; a backfill would REPLACE that working path with an unattested field that `IPD-M107` then refuses. (b) Note it in the record only: rejected, E-03's property 3 would pass while a deletion of the fallback went uncaught, which is exactly the untested-safety-property gap this plan exists to close. (c) Add a test for the fallback in a separate module: rejected, it is one assertion on the same predicate the same test already drives. | `is_plan_review_approved`'s three documented arms; measured True for a field-absent plan with one approving review record added, False for the same plan without it, False for all 85 real field-absent plans, and False after a simulated backfill. | yes |
| D-5 | The plan's E-01 carries a "STOP AND REPORT" directive. The 2026-09-01 ruling requires flagging a stop directive for the out-of-scope-edit case. Flag it? | NO. Keep it, and annotate WHY it is the sanctioned kind. | (a) Flag and remove it: rejected, it would be a misapplication of the ruling, which explicitly preserves a stop for "a genuinely unsafe condition". An E-01 violation means the plan's central factual premise is false, so proceeding would commit a documented invariant the tree contradicts. (b) Keep it silently: rejected, a later reviewer applying the ruling mechanically would flag it, so the reasoning belongs in the plan. (c) Soften it to "note and continue": rejected, continuing past a falsified premise is the failure mode, and a live attestation forgery is exactly what the maintainer must see first. | The 2026-09-01 ruling's own carve-out wording; re-verified 0 of 1018 plans violate the invariant today, so the directive is a genuine tripwire rather than an expected path. | yes |

### Deferred and open

- (none). All six findings were FIXED in place, including both HIGH. No finding reached the
  repository's gate threshold (`review_findings_gate.block_at`, default `HIGH`) while unfixed, so no
  escalation to a `- Blocking: yes` open question was required.
- Pre-existing open question OQ-01 remains `Blocking: no` / `Status: deferred` /
  `Owner: maintainer` / `Carrier: l0ixig`, correctly: it is a policy decision the maintainer was not
  asked to make. Its rationale was corrected under PR-001 and D-1, withdrawing a false technical
  obstacle while leaving the genuine policy ground intact.
- No `Reversible: no` decision was taken. No backlog item was created (all three carriers the plan
  names, `l0ixig`, `xvp5vx` and `0z1b2s`, were verified to exist and to say what the plan claims).
