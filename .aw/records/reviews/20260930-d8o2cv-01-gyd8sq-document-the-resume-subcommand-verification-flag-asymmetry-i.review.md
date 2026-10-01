# Review findings: plan gyd8sq

- Subject-Id: gyd8sq
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-701 (HIGH, fixed), PR-702 (MEDIUM, fixed), PR-703 (LOW, fixed)

## Round 1

Reviewed at HEAD `bda0fca16` in an isolated review lane. The plan file was committed and unmodified in the
lane (`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize --agent` reports `conforming` with zero findings after revision. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator checklist row check does not apply.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests on
RE-EXECUTING the measurements rather than re-reading them, and on checking the cross-plan facts the plan
reasoned about, which is where the one serious finding came from.

EVERY MEASUREMENT IN THE PLAN REPRODUCES EXACTLY, which for a documentation plan is most of the work. The
24-cell probe was re-driven over both parsers and both subcommands and matches the plan and spec `25kzda`
Section 2.1c cell for cell: opencode accepts all six spellings on BOTH `start` and `resume`
(`--validate`/`--verify`/`--audit` to `validate=True`, the three negations to `False`); antigravity `start`
takes `--validate`/`--no-validate` to `validate`, routes `--no-verify`/`--no-audit` to a separate
`no_verify=True` leaving `validate=None`, and exits 2 on `--verify` and `--audit`; antigravity `resume`
exits 2 on ALL SIX with `runagy: error: unrecognized arguments`. The contradictory-pair asymmetry reproduces:
oc `--no-verify --validate` yields `validate=True` and the reverse yields `validate=False`, with no refusal,
while `hasattr(oc_runipd,'verification_flag_tristate')` is `False` and the agy attribute is `True`.
`RUNNER_REGISTRY['agy'].validate_default` is `True` against `False` for oc, so F-05's "lands hardest on the
verify-by-default host" holds. The two sentences E-01 and E-02 target are present verbatim in
`docs/runner-profiles.md`, the file greps clean for `resume` outside the Durability section and the one
`--verify-with` row, F-07's precedent row is verbatim, the troubleshooting preamble is verbatim, and the
end-to-end CLI check confirms `aw agy run resume --no-verify` exits 2 creating no run directory, so the
preamble stays true of E-04's new row. `tests/test_runner_shared.py -k VerificationDestAsymmetryPerHost`
passes `4 passed`. The file contains zero em dashes and zero en dashes. F-04's provenance checks out:
executed plan `7dz3wv` records the identical measurement as its own F-14 and names `d8o2cv` as the carrier.

WHAT REVIEW FOUND was that the plan's central authoring DECISION rests on a fact that has since changed, in
the direction that makes the decision wrong. The plan reasoned carefully about a cross-plan coupling and
reached a defensible answer for the world as it stood; that world moved.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | IN-SCOPE | A (correctness), G (executability), F (honest documentation) | `zdgc6t`'s front matter at review HEAD: `- Status: approved`, `- Readiness: go-pending-approval`, `- Blocks-Release: next`; this plan's own `- Status: to-review`; plan DECISION-01 and E-02 | DECISION-01'S LOAD-BEARING PREMISE IS FALSE, AND E-02 AS WRITTEN WOULD LIKELY SHIP A NEW FALSEHOOD. DECISION-01 chose to correct the contradictory-pair sentence now, stating as its reason that "`zdgc6t` is `to-review`, not approved, so its execution is not guaranteed and may be revised". Measured: `zdgc6t` is APPROVED and release-gated, so it is dispatchable by `aw oc run` today while this plan is not, making the near-certain ordering the OPPOSITE of the one assumed. After `zdgc6t` lands, opencode REFUSES the pair and `25kzda` is amended to match, so writing "opencode resolves it by last-wins" would be a new affirmative falsehood of exactly the kind DECISION-01 exists to prevent. The plan's own gate already says to stop and report if behavior changed, so E-02 contradicted its own gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-10 with the measured statuses. Rewrote DECISION-01 to preserve the authored reasoning, record the inversion, and change the selection to an order-aware one. Rewrote E-02 as an explicit two-branch instruction: re-measure first, then host-qualify (last-wins branch) or confirm-and-leave-intact (refuses-too branch), recording which branch and the measurement that chose it. Corrected F-08's stale status. Re-resolved OQ-01 and gave it a real owner. Rewrote V-02's evidence requirement to demand the branch and its measurement instead of an unconditional stop. |
| PR-702 | MEDIUM | IN-SCOPE | A, F | `agy_runipd.build_parser().parse_args(...)` succeeding on both orders; `agy_runipd.verification_flag_tristate` raising `runner_shared.RunFlagRefusal`; that function's own docstring | THE ANTIGRAVITY REFUSAL IS POST-PARSE, NOT A PARSER REFUSAL, AND E-02 COULD EASILY MISDESCRIBE IT. F-04 says the pair "is refused" on antigravity without saying by what. Measured: the parser ACCEPTS it, yielding `validate=True, no_verify=True` in both orders, and the refusal comes from `verification_flag_tristate` raising `RunFlagRefusal`; its docstring records the same ("argparse accepts `--no-verify --validate` happily ... so this check is hand-written and not an argparse freebie"). This matters because the existing doc phrase "refused before the run starts" is therefore EXACT and must be preserved, while a reviewer or executor reaching for an `unrecognized arguments` framing would conflate it with the `resume` exit 2 that E-03 and E-04 document, which is a different mechanism an operator will be comparing the messages of. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-11 with the driven evidence and the docstring citation. Appended the distinction to F-04. Added a bullet to E-02 requiring the "before the run starts" phrase be kept and NOT downgraded to a usage error, with the reason (conflation with the resume exit 2). Extended V-02 to require the post-parse refusal shown explicitly for both orders. |
| PR-703 | LOW | IN-SCOPE | E (testing), G | bare `python3 -m pytest` at review; backlog `tl8qmc`, `2wae2x` | ONE PRE-EXISTING SUITE FAILURE, WHICH BITES HARDER ON A DOCUMENTATION-ONLY PLAN. Bare pytest reads `1 failed, 3431 passed, 2 skipped`; the failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a known local-versus-UTC history-date defect filed twice that fires only between local midnight and UTC midnight. The plan's validation correctly says a prose change "must not move" the baseline, but an executor who edits only prose and then sees a red suite may reasonably suspect their own change and start investigating, or worse, fix it; `tests/test_backlog.py` is not in `- Scope-Paths:`, so repairing it would be an undeclared edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12 with the summary line and both backlog citations. Added a note to the validation bullet naming it as pre-existing, explaining why a red suite is especially confusing on a documentation-only plan, and forbidding the repair as out of declared scope. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Given `zdgc6t` is approved and this plan is not (PR-701), should E-02 be dropped, deferred to `zdgc6t`, or made order-aware? | Make it order-aware: a two-branch instruction keyed on a re-measurement at execution time, with the branch and its evidence recorded. | (a) DROP E-02 entirely and let `zdgc6t` own the sentence. Genuinely defensible and the plan itself offers it as the fallback; rejected as the DEFAULT because if `zdgc6t` were revised, descoped, or long delayed the falsehood would persist in shipped operator docs, and the executed `7dz3wv` review already ranked a wrong statement worse than a silence. It remains available to the maintainer and the plan now says so. (b) Keep the authored single wording. Rejected outright: measurement says it would most likely ship a NEW falsehood, which is the exact harm the item exists to fix. (c) Write something vague enough to be true either way. Rejected for the plan's own stated reason, that vague prose about whether a command refuses is worse for an operator than either precise statement. | `zdgc6t`'s `- Status: approved` / `- Readiness: go-pending-approval` / `- Blocks-Release: next` versus this plan's `- Status: to-review`, which together determine dispatch order; the plan's own gate already requiring a re-measurement; and F-09's re-verified finding that E-01, E-03 and E-04 are independent of `zdgc6t`, so only this one sentence is coupled. | yes |
| D-2 | Should the review ALSO correct `zdgc6t`'s F-10 row, which asserts `docs/runner-profiles.md` "needs no change" and is made stale by this plan? | No; leave it, as the plan already decided. | Editing that row. Rejected on the plan's own correct reasoning, which this review re-verified rather than merely accepted: another plan's findings table is not this plan's to rewrite, and `zdgc6t` is `approved` so an edit to it now would touch an artifact already past review and awaiting execution. The coupling is visible from this side (F-08, F-10, OQ-01) and is where a reader of either plan will find it. | `zdgc6t`'s `- Status: approved`; the plan's existing Deferred row naming `zdgc6t` as carrier; `AGENTS.md`'s rule against rewriting what another plan records. | yes |
| D-3 | The plan ships NO test and says prose rot will be caught by nothing. Is that acceptable, or an under-scope gap to close? | Acceptable as argued; no test, and no carrier filed. | Filing a carrier or adding a prose-pinning assertion. Rejected because `AGENTS.md` prohibits asserting "that specific text, docstrings, or comment banners remain unchanged" and `GUIDING_PRINCIPLES` P16 governs, so such a test must never be written by anyone and a carrier would park a permanently undischargeable obligation, which is precisely what the plan's own `Carrier-Declined` reasoning says. Verified the compensating guard is real rather than asserted: `tests/test_runner_shared.py -k VerificationDestAsymmetryPerHost` passes `4 passed` at review, so the behavioral facts under the prose are pinned even though the prose is not. | `AGENTS.md`'s code-pinning prohibition; the passing 24-cell test run at review; the plan's existing Carrier-Declined row. | yes |

No `Reversible: no` decision was taken, so no escalation under the irreversible-decision rule is owed.

OQ-01 was `resolved` and has been RE-RESOLVED in substance rather than merely re-affirmed, because PR-701
falsified the evidence its original resolution cited. It remains `- Status: resolved` and `- Blocking: no`,
and the non-blocking judgement was re-verified rather than inherited: the branch E-02 now takes is decided
by a measurement any executor can make, not by a decision only a human could supply, and F-09's
independence claim was re-checked against `zdgc6t`'s E-03 and E-05. Its `- Owner:` read `none`, which is
mechanically accepted (`ipd_schema.open_question_error` consults the owner only on the `deferred` branch),
but since this review changed the resolution the owner is now recorded explicitly and points at D-1.

No finding was left OPEN or DEFERRED, so no finding requires escalation as a `- Blocking: yes` question
under the review-findings gate.
