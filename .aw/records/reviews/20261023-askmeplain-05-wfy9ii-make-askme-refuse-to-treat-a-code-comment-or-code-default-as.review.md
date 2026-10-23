# Review findings: plan wfy9ii

- Subject-Id: wfy9ii
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane after `802615f7b` (the lf4j52 review commit). The plan was
committed and byte-identical to the sealed lane input, so no pre-review snapshot.
`aw ipd lint --phase author --agent`: `clean`; after revisions `--phase review-finalize --agent`:
`clean`, 0 findings. Not an orchestrator.

Verified at review:
- `run_analytics_cli.parse_date_window` docstring reads "Both accept what ``aw runs --since``
  accepts (dates, timestamps, relative specs like ``30d``), because one parser owns the grammar
  (``run_viewer.parse_since_timestamp``)." (F-4 correct).
- Findings `auwidn`: Claude Code T03 (OQ-02 closed from `parse_since_timestamp`'s `now`), T04
  ("I'm recording those without asking"), T11 (closed both blocking questions noninteractively),
  T09 attempt 1; the "Corrective plans" row for D-4 records "maintainer ruling 2026-10-23: keep
  the rule and enforce it" (F-6 now cites it).
- `askme.md` "Establish facts before asking" contains "Apply an existing decision rule when its
  conditions can be established.", "An author's preference is not the same as an approved decision
  rule." and the paragraph "Do not use this classification to ignore an explicit request to rewrite
  a question. If evidence already settles that question, explain the answer and its basis instead of
  asking the user to decide it again."
- Spec `6kwd2e` (approved) R2.5 delegates the sort to askme: "That sort is the single source for
  this decision and MUST NOT be restated here or in a prompt".

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric D (internal contradiction) | `.aw/system/workflows/askme/askme.md` "Establish facts before asking": "If evidence already settles that question, explain the answer and its basis instead of asking the user to decide it again." | E-01 added "if the user asked you to ask a specific question, ask it, even if you believe the evidence settles it" while leaving the existing paragraph that says the opposite. The body would carry two contradictory instructions, and the old one is what licensed the T09 attempt 1 failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now REPLACES that paragraph with one reconciled rule (approved rule: name it and ask whether to reopen; other evidence: ask and include it); F-7 added; E-03 test asserts the old sentence is gone. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric D (loophole in the definition) | plan E-01 source (c) "an earlier resolved open question"; `auwidn` T03/T04/T11 resolutions recorded "by evidence" | Source (c) would let an agent's own earlier "by evidence" resolution count as an approved rule, so one agent's guess becomes the next agent's rule. Source (a) did not exclude superseded `DECISIONS.md` entries, and nothing required the rule to address this question. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (c) limited to questions a HUMAN resolved; (a) to non-superseded entries; added "applies only when it addresses this question's choice and its conditions can be established". Scope line updated. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (validation reaches the test) | `tests/test_askme_command_delivery.py:88` `@pytest.mark.slow`; `tests/slow_allowlist.txt:22` | The installer test needs the slow marker and a run with the marker filter cleared; the bare run never collects this file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 marks it `slow`; E-04/V-04 run it with `-o addopts=""` and call the bare run a regression gate. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric G (right-sizing) | plan E-02 (askme sentence plus rationale paragraph), E-03 (test plus CHANGELOG) | Two E-items each bundled deliverables in different files with separate evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split out E-05 (rationale.md) and E-06 (CHANGELOG) with V-05/V-06. |
| PR-005 | MEDIUM | IN-SCOPE | Shared-checkout safety | AGENTS.md "Shared checkout"; V-03 asked for a pre-change failing run with no method | Unspecified method invites `git stash` in a shared checkout. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 gives a copy, `git show HEAD:` and restore sequence with `git diff --stat` proof. |
| PR-006 | LOW | UNDER-SCOPE | Rubric G (execution contract, provenance, side effects) | plan F-6 "in the `lkn1zt` session"; gate text; spec `6kwd2e` R2.5 | F-6 cited an unrecorded session instead of the durable `auwidn` ruling; the gate lacked the paste-actual-output rule, the declaration-only fence and conditional finalize ownership; the plan did not state the expected runner side effect (more blocking questions escalated to `questions[]`) or invariants. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 cites `auwidn`; gate rewritten; spec-sync states the side effect; invariants I-1 to I-3 and the honest test limit added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | When the user asks to be asked a question an approved rule already settles, what should askme do? | Name the rule and what it decides, and ask whether the user wants to reopen it | Always ask as if open (ignores recorded decisions, re-litigates them); explain and not ask (the old text, which T09 attempt 1 abused) | Maintainer ruling in `auwidn` D-4 row (keep the rule, enforce it); `askme.md` "Honor decisions and authorization already given in this session." | yes |
| D-2 | Does an agent-resolved earlier open question count as an approved rule? | No, only a human-resolved one | Count every resolved question | `auwidn` T03/T04/T11 show agents recording "by evidence" resolutions from docstrings; counting them would launder D-4 | yes |
| D-3 | Spec edit to `6kwd2e` needed? | No | Amend R2.5 | R2.5 says the askme sort "is the single source for this decision and MUST NOT be restated here" | yes |
| D-4 | Slow tier or core tier for the new test? | `@pytest.mark.slow`, run by path | Core tier | `tests/slow_allowlist.txt:22`; AGENTS.md repo-local suite contract | yes |
