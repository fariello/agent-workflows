# Review findings: plan 787hb4

- Subject-Id: 787hb4
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 02 of Set `statusvocab`, the independent child (`- Item-Dependencies: none`). Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE semantic review,
and `--phase review-finalize` conforms after the revisions, so nothing below is structural. The plan
file was committed and unchanged, so no pre-review snapshot was needed.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests on
RUNNING the claims against the shipped code rather than re-reading them, and that is precisely what
produced the blocker below: the plan's central mechanism was verified by CALLING it, and it does not
work as the plan assumed.

THE DIAGNOSIS IS CORRECT AND WELL EVIDENCED, and it is the strongest part of the plan. Independently
confirmed: `xdvglg` is in `executed/` (a human resolved it by hand after the run), `04vf1h` is in
`executed/` and `a5wdne` still in `pending/`, and the send-back machinery exists exactly as described
(`RETRYABLE_FINALIZE_FINDING_TEXTS`, `FINALIZE_RETRY_COUNT_KEY`, `frozen_retry_budget`,
`FINALIZE_RETRY_EXHAUSTED_STATUS = "failed-safely"`). The module's own comment states the reasoning the
plan quotes, including why the trigger is prose and not the `IPD-S404` code. F-02's stale-citation
claim is the kind of defect this repository has hit repeatedly and the plan is right to call the
refusal correct-but-disproportionate.

THE PLAN'S PROPOSED MECHANISM, HOWEVER, CANNOT WORK AS AUTHORED, and that is a BLOCKER rather than a
wording problem. This was found by calling the shipped predicate on the shipped test fixture:

```text
RETRYABLE_FINALIZE_SUMMARY                     = 'pre-transition gate did NOT conform'
STALE_RECEIPT_REFUSAL contains that summary?   = False
finding lines in STALE_RECEIPT_REFUSAL (IPD-*) = []          # the locator finds NOTHING
finalize_refusal_is_retryable(STALE_...)        = False       # and stays False after E-02 as authored
FINDING_RECEIPT_STALE                          = 'plan content digest no longer matches the receipt'
FINDING_RECEIPT_STALE.startswith('IPD-')        = False
```

`finalize_refusal_is_retryable` is a two-part conjunction over ONE refusal class: it short-circuits
unless the pre-transition SUMMARY is present, and only then reads finding lines, which it locates by
the `IPD-` prefix. The stale branch's summary is a different sentence and neither of its findings
carries that prefix, so E-02's authored instruction ("extend the retryable set") would add entries the
function never reaches. The plan would have executed, passed its own E-02, and changed no behavior.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A (correctness) | `agent_workflows/runner_shared.py` `finalize_refusal_is_retryable`; `agent_workflows/ipd_lifecycle.py` `FINDING_RECEIPT_STALE` | THE PLAN'S CENTRAL MECHANISM CANNOT WORK AS AUTHORED. E-02 said to "extend the retryable set to include the stale-receipt finding and the scope-REDUCTION finding", and `Scope check` called it "a predicate that already exists". But `finalize_refusal_is_retryable` is a CONJUNCTION SCOPED TO ONE CLASS, not a list lookup: it returns False unless `RETRYABLE_FINALIZE_SUMMARY` ("pre-transition gate did NOT conform") is in the message, and only then collects finding lines by the `IPD-` prefix. The stale refusal's summary is "the begin receipt for <id> is STALE: ...", and its findings (`FINDING_RECEIPT_STALE`, plus the reduction sentence) carry NO `IPD-` prefix, so `finding_lines` is empty and the deliberate "refuse to guess" branch returns False. MEASURED by calling the shipped predicate on the shipped `STALE_RECEIPT_REFUSAL` fixture: False, and still False with the finding text appended to the allowlist, because control never reaches that comparison. An executor following E-02 literally would add two unreachable strings, pass its own expected outcome as worded, and ship ZERO behavior change while the plan claimed the defect fixed. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 rewritten as a per-class-arm restructuring: dispatch on SUMMARY first, then apply that class's own rule; keep the pre-transition arm byte-identical; add one arm per newly answerable class keyed on its own summary and the E-01 finding ids. The every-finding conjunction is explicitly PRESERVED WITHIN each arm so a mixed stale-plus-rewrite message still refuses. The measurement and both exclusion mechanisms are recorded in the item, and F-05 was added. |
| PR-002 | HIGH | IN-SCOPE | E (verification) | `tests/test_finalize_sendback.py` `TheRetryTriggerIsAPositiveAllowlist::test_a_STALE_begin_receipt_is_NOT_retryable` | V-01 REQUIRED EVIDENCE THAT CONTRADICTS THE PLAN'S OWN GOAL. It demanded "`tests/test_finalize_sendback.py` still passing unmodified in its `STALE_RECEIPT_REFUSAL` assertion". That assertion is `assertFalse(finalize_refusal_is_retryable(STALE_RECEIPT_REFUSAL))` with the docstring "spec 5.5's changed frozen requirements" - i.e. it pins the EXACT behavior E-02 exists to invert. Satisfying V-01 as written requires E-02 to have failed. An executor hitting the red test could plausibly read it as a regression and revert the change. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-01 now pins that the FIXTURE STRING is unchanged (which is what E-01's no-emitted-byte-change claim actually supports) and explicitly forbids citing that test as an unchanged pin, naming it as one E-02 must rewrite. The four sibling `assertFalse` tests that DO stay true were moved into V-02 as the over-admission pin, and the same list is named in the gate so a red test is not misread. F-06 was added. |
| PR-003 | MEDIUM | IN-SCOPE | A (correctness) | `agent_workflows/ipd_lifecycle.py` `finalize_precheck` stale branch | E-01 TREATED THE REDUCTION FINDING AS A FIXED STRING TO NAME, following the `FINDING_RECEIPT_STALE` precedent. But unlike that constant, the reduction finding is COMPOSED AT EMIT TIME with a singular/plural stem and the removed paths interpolated: `"Scope-Paths entr" + ("ies" if len(removed) > 1 else "y") + " REMOVED since begin (...): " + ", ".join(removed)`. So there is no single shipped string to name, and an id defined against the singular spelling silently fails to match a multi-path reduction - the case where a reviewer removed several stale citations at once. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now states the finding is composed rather than constant, requires the id to name the INVARIANT substring both spellings share, and requires both spellings pinned. Verified both renderings at review. |
| PR-004 | MEDIUM | UNDER-SCOPE | E (verification) | plan `V-02` | V-02 drove THREE refusals and omitted the two never-retry classes that share the stale branch's shape. Since PR-001's fix restructures the predicate's DISPATCH, an arm keyed on a too-loose summary could newly admit a MISSING receipt or a scope-reconciliation refusal - spec 5.5's FIRST never-retry entry - and nothing in the plan would catch it. The plan asserted the widening class stays terminal but never asked for the other two. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-02 now drives FIVE refusals (two send back, three stay terminal: widening, missing receipt, scope reconciliation) plus a MIXED stale-plus-rewrite message proven not retryable, and requires the three existing `assertFalse` sibling tests to pass UNMODIFIED. |
| PR-005 | MEDIUM | IN-SCOPE | G (executability) | plan `## Approval and execution gate` | The gate was ONE sentence ("Human approval required before execution") and carried no execution contract: no scope fence, no honesty rule, no commit discipline, no lifecycle transition, no statement of what a human is actually approving, and no disposition for OQ-01. It also failed to warn that this plan must REWRITE a currently-green test, which combined with PR-002 is how an executor reverts the change it was sent to make. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten with `Size assessment: standard`; a plain statement of the policy change being approved; OQ-01 dispositioned non-blocking with the spec-amendment boundary (this plan declares no spec path, Order 03 is the only spec-amending child); a declaration-style scope fence (make-then-justify, no stop-over-scope, with the `runner_shared.py` contention noted as NOT a hazard since items are isolated); the bare-`pytest` honesty rule with the re-derive requirement; the named list of tests to rewrite versus preserve; `aw commit` path-scoped and never-push; and the conditional lifecycle transition. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001 shows the authored mechanism cannot work. Is that a `REPLAN`, or repairable with bounded edits? | Repair in place; `APPROVE WITH REVISIONS APPLIED`. | `REJECT - NEEDS REPLAN`. Rejected: the plan's DIAGNOSIS, its answerability test, its class boundaries, and its three-item decomposition all survive intact; only the mechanism of one E-item changes, from "extend a list" to "restructure into per-class arms". The scope, the declared paths, and the E/V structure are unchanged. | `plan-review` Step 2.4: `REPLAN` is for an approach "fundamentally unsound and cannot be repaired with bounded edits". The repair here is one rewritten E-item plus its validation, inside the same files and the same scope. | yes |
| D-2 | Does admitting a stale receipt to the send-back need spec `25kzda` 5.5 amended before this plan may execute? | No. Proceed without a spec amendment, and record the boundary in the gate. | (a) Block the plan pending a spec amendment. (b) Declare `25kzda` in `Scope-Paths` and amend it here. Rejected: the plan does not declare a spec path, and AGENTS.md requires a spec edit to be DECLARED so the runners can announce and reconcile it; silently amending would be the exact drift that rule prevents. | The plan's own `Spec / documentation sync` section already states this correctly and pre-commits to the alternative ("if a reviewer judges that admitting a stale receipt contradicts 5.5 rather than refining it, that is a spec amendment and belongs to a plan that declares the spec path"). 5.5's never-retry list governs out-of-scope mutation, which stays terminal. OQ-01 is `Blocking: no` and carries the same recommendation, so no gate is bypassed. The judgement is the maintainer's to overturn at approval, which the rewritten gate now says explicitly. | yes |
| D-3 | `runner_shared.py` is declared by this plan AND by sibling Order 01, and is among the most contended files in the repo. Is that a finding? | Not a finding. Note it in the gate as NOT a hazard. | Raising it as a sequencing risk or adding an `Item-Dependencies` edge to Order 01. Rejected: it would serialize two genuinely independent changes and contradict the Set's own analysis. | The two touch disjoint surfaces (Order 01 the status vocabulary, this plan the finalize-retry predicate), and AGENTS.md is explicit that each execute item gets an ISOLATED WORKTREE by default whose changes return through the merge-and-revalidate gate, so file overlap is not a runtime hazard and reporting it as one wastes the maintainer's time. | yes |
| D-4 | The run directory `run-20260924T050407Z-3108751` underpinning every measurement is absent from this worktree. Does that block the review? | No. Corroborate by proxy and do not raise it. | Raising the missing evidence as a finding, or reading the main checkout. Rejected: the lane is the complete authorized workspace, and `.aw/records/runs/` is gitignored so no clone has it. | `.aw/records/runs/` does not exist anywhere in this worktree and is gitignored by construction, so its absence is expected. The claims resting on it were corroborated independently: `xdvglg`/`04vf1h` in `executed/`, `a5wdne` in `pending/`, and every code-side claim verified directly against the modules. Same decision as the `zngiya` review's D-1. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author          --agent 787hb4 -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize --agent 787hb4 -> {"outcome":"clean","exit":0,"findings":0}   (after revisions)

RETRYABLE_FINALIZE_FINDING_TEXTS   3 entries, all pre-transition E/V texts, as the plan states
RETRYABLE_FINALIZE_SUMMARY         'pre-transition gate did NOT conform'
FINALIZE_RETRY_COUNT_KEY           'finalize_retry_attempts'
FINALIZE_RETRY_EXHAUSTED_STATUS    'failed-safely'   (terminal, in no success bar -> E-03's claim holds)
FINDING_RECEIPT_STALE              'plan content digest no longer matches the receipt'  (a sentence,
                                   deliberately, so the stale branch emits identical bytes; E-01's
                                   precedent claim is correct)

finalize_refusal_is_retryable(STALE_RECEIPT_REFUSAL)  -> False   # PR-001: and unreachable by allowlist
  summary present in stale message                    -> False   #   first exclusion
  finding lines matching the IPD- locator             -> []      #   second exclusion

reduction finding renderings (PR-003):
  'Scope-Paths entry REMOVED since begin (a contract reduction, ...): a.py'
  'Scope-Paths entries REMOVED since begin (a contract reduction, ...): a.py, b.py'

existing tests pinning classes that MUST stay terminal (V-02's new pin):
  test_a_missing_begin_receipt_is_NOT_retryable
  test_a_scope_reconciliation_refusal_is_NOT_retryable
  test_a_MIXED_message_is_NOT_retryable
  test_an_empty_or_summary_only_message_is_NOT_retryable
existing test that MUST be rewritten (PR-002):
  test_a_STALE_begin_receipt_is_NOT_retryable
```

NOT RE-RUN AT REVIEW, and stated rather than implied: the suite. This review changed only planning
prose, so the authored baseline (`8850 passed, 5 skipped, 2 xfailed` on `main` `a631a1f6`) is neither
confirmed nor refuted here; the plan already requires re-deriving it at execution, which is the correct
treatment for a live figure.

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. PR-001..PR-005 all FIXED, none deferred, none open. OQ-01 remains open
at `Blocking: no` with a recorded recommendation, which under the 2026-09-10 maintainer ruling does not
make the plan `NO-GO`.

Readiness `go-pending-approval`. What a human should weigh at approval, none of it a finding: this is a
POLICY change (two classes become retryable, spending the existing budget), it rests on the judgement
that spec 5.5's "changed frozen requirements" category does not discriminate the cases the runner
actually meets, and if the maintainer reads that as contradicting 5.5 rather than refining it then the
work needs a plan that declares the spec path, since this one deliberately does not.
