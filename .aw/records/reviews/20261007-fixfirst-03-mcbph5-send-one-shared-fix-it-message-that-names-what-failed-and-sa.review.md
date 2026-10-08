# Review findings: plan mcbph5

- Subject-Id: mcbph5
- Subject-Type: ipd
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `383ebc1ee`. The plan was committed and byte-identical to the lane
input, so there was no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review, and
`--phase review-finalize`: `clean` after revision. Not an orchestrator.

Verified: `build_correction_notice` ("Address ONLY the failed predicates"), `build_stale_receipt_notice` ("UNDO it
... KEEP it ... JUSTIFY it"), `build_verification_refusal_notice` ("you must FIX the cause rather than
re-implementing"; uses `render_stream._redact_absolute_paths`) all return `""` when `recovery` is False and are
called from exactly one site, `build_prompt`, which concatenates them. The execute prompt carries "Do not weaken
checks, fabricate evidence, broaden approved scope". `DEFAULT_RUNBOOK_TEXT` directive 3 says "Do not weaken checks
or fabricate evidence." `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` exists. The merge-conflict send-back prompt is
`merge_conflict_question`, and two further correction prompts exist (`build_production_set_correction_prompt`,
`build_review_orchestrator_correction_prompt`). Test-pinned phrases: `tests/test_finalize_sendback.py` "Change after
begin:"; `tests/test_verification_sendback.py` "## Verification failed on the prior attempt
(verifier-no-test-evidence)"; `tests/test_production_correction_turn.py` "never delete the checklist".

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric A (correctness of "once") | `build_prompt` `correction_notice = (build_correction_notice(...) + build_stale_receipt_notice(...) + build_verification_refusal_notice(...))` | E-02 required the rule "exactly once" per notice, but the notices are concatenated into one prompt and can co-occur, and E-03 adds a body copy too. The prompt would carry the rule up to four times, and the plan's own "rule once" test would contradict E-02's design. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `include_rule=False` on the three, one append at the assembly site, and E-03 states which copy is kept on recovery. V-02/V-03 count occurrences in a real `build_prompt` output with two notices. Added F-04. |
| PR-002 | MEDIUM | UNDER-SCOPE | Rubric G (coverage of fix-it texts) | `merge_conflict_question`; `build_production_set_correction_prompt`; `build_review_orchestrator_correction_prompt` | The Concern names the merge-conflict send-back as a fix-it text, but no E-item routes it, and two more correction prompts were not named. The rule would then be present on some fix-it turns and absent on others. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-05/V-05 appends the shared rule once to each, otherwise byte-identical. Added F-05. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric D (anti-regression) | Test-pinned phrases listed above | Routing through a new builder risked rewording phrases that existing tests match, which invites editing those tests. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and E-05 require the phrases to be preserved and the tests left unmodified, with re-derivation by grep. Required tests run the four modules, and V-04 shows `git diff --stat tests/`. |
| PR-004 | MEDIUM | IN-SCOPE | Security lens / P-convention | `build_verification_refusal_notice` uses `_redact_absolute_paths`; convention in plan Step 0 | E-01 put evidence (hook output, paths) verbatim into the prompt, and the elision "pointer" could have been an absolute run-dir path; redaction was only in prose conventions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 requires redaction, a named bound constant, and an in-lane pointer; redaction is tested. |
| PR-005 | LOW | IN-SCOPE | Consistency | `DEFAULT_RUNBOOK_TEXT` directive 3 | The attached runbook would still read as an absolute prohibition that the new rule relaxes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 aligns directive 3 with a pointer to the rule. |
| PR-006 | LOW | UNDER-SCOPE | Rubric G (execution contract) | Original gate | The scope fence, dependency reason, staged-set check and conditional finalize were missing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Execution contract added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where is the rule deduplicated? | One append at `build_prompt`'s assembly site; notices built with `include_rule=False` | Rule in each notice (repeats); rule only in the body (absent from E-05 standalone correction prompts) | `build_prompt` is the sole call site of the three notices | yes |
| D-2 | Should the standalone correction prompts and merge-conflict question carry the rule? | Yes, once each (E-05) | Leave them out (rule inconsistent across fix-it turns) | Plan Concern names the merge-conflict send-back; Goal "Every fix-it turn reads the same way" | yes |
