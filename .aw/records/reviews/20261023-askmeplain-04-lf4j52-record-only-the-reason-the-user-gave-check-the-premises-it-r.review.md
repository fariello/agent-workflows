# Review findings: plan lf4j52

- Subject-Id: lf4j52
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane after `47faf0d6e` (the 9vttho review commit). The plan was
committed and byte-identical to the sealed lane input, so no pre-review snapshot.
`aw ipd lint --phase author --agent`: `clean`, 0 findings; after revisions
`--phase review-finalize --agent`: `clean`, 0 findings. Not an orchestrator.

Verified at review:
- Findings `auwidn` rows match the plan: D-5/D-6/D-7 table rows and the "Defects observed only in
  passing cells" paragraph (D-7); Claude Code T09 input "Creation date. And that question was way
  too long-winded." and record "Rationale supplied" (T08); OpenCode + opus "No reason was given"
  (T03 area, line "recording \"No reason was given beyond choosing the recommended option\"") and
  the measured "backlog 1104/1104 (100%)".
- `askme.md` "Record project decisions" bullet "Update `- Resolution or deferral rationale:` with
  the decision, its source (the user or evidence), the date, and any reason actually supplied." and
  "Ask and wait" "Do not invent a reason the user did not give." exist as quoted.
- `runner_shared.record_oq_answer` writes `RESOLVED {date} by {who} via {channel}: {answer}` and
  replaces the existing rationale line via `rationale_pattern.sub`; pinned by
  `tests/test_question_preflight.py` `test_a40_durable_artifact_write_back`.
- Spec `ipd-structure-and-linting` Section 7 only requires a nonempty rationale for `resolved`;
  spec `6kwd2e` R1.5 requires "a rationale naming the human and date". The append shape satisfies both.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric E (validation reaches the test) | `tests/test_askme_command_delivery.py:88` `@pytest.mark.slow`; `tests/slow_allowlist.txt:22` | The installer test needs the slow marker and a run with the marker filter cleared; E-05/V-05 relied on the bare run, which does not collect this file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 marks it `slow`; E-05/V-05 run it with `-o addopts=""` and call the bare run a regression gate. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric G (right-sizing) | plan E-03 (askme paragraph plus three rationale paragraphs), E-04 (test plus CHANGELOG) | E-03 and E-04 each bundled two deliverables in different files with separate evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split out E-06 (rationale.md) and E-07 (CHANGELOG) with V-06/V-07; E-05 now depends on them. |
| PR-003 | MEDIUM | UNDER-SCOPE | Rubric C (one canonical shape) | `agent_workflows/runner_shared.py` `record_oq_answer` "`RESOLVED {date} by {who} via {channel}: {answer}`" | The plan invented an append shape without the existing runner shape's `via <channel>`, giving two different resolution formats in records. The runner also REPLACES the rationale line, the same D-7 overwrite, which the plan did not mention. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Shape aligned (`... via /askme: ...`) plus the empty-field case; the runner overwrite is named in Scope check and raised as non-blocking OQ-01 for the maintainer. |
| PR-004 | MEDIUM | IN-SCOPE | Shared-checkout safety | AGENTS.md "Shared checkout"; plan V-04 asked for a pre-change failing run with no method | Without a stated method an executor would likely `git stash`, which can sweep a co-worker's change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 gives a copy, `git show HEAD:` and restore sequence with a `git diff --stat` proof. |
| PR-005 | LOW | UNDER-SCOPE | Rubric D (preserve behavior) | `askme.md` bullets "Preserve the original `- Blocking:` value." and "Record the answer before asking the next question."; sibling `pkz19w` E-01 Expected outcome | The plan did not say the section's other bullets stay; `pkz19w` depends on one of them. "Five points" were not named, so V-01 could not check them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 names the five points and the bullets to keep; invariants I-1 to I-3 added and mapped. |
| PR-006 | LOW | IN-SCOPE | Rubric D (D-6 coverage) | `auwidn` D-6 "repeated into the prompt or the resolution" | E-03's premise check covered prompts and options but not the resolution text written back, where D-6 was also observed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and V-03 now cover prompt, option and written resolution. |
| PR-007 | LOW | UNDER-SCOPE | Rubric G (execution contract) | plan "Approval and execution gate" | The gate lacked the paste-actual-output rule, the declaration-only scope fence and conditional finalize ownership; no honest limit on what a delivery test proves. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with the full contract; Required tests states the limit (research `y0vcm9`). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which resolution text shape should askme write? | `RESOLVED <date> by <the user or evidence> via /askme: <decision>. <reason or "No reason was given.">`, appended | The plan's shape without `via`; a new labelled block | `runner_shared.record_oq_answer` existing shape; spec `6kwd2e` R1.5 | yes |
| D-2 | Fix the runner's overwrite of the rationale line in this plan? | No; raise as non-blocking OQ-01 (owner maintainer) and name it under Scope check | Widen scope to `runner_shared.py` and `tests/test_question_preflight.py` | Plan Scope "OUT: ... any runtime validator of record text" and workflow-text-only scope; changing a pinned runner behavior is the maintainer's scope call | yes |
| D-3 | Split E-03/E-04 or keep them? | Split into E-06 and E-07 | Keep bundled | `plan-review.md` right-sizing rubric (a) multiple deliverables in different files | yes |
| D-4 | Slow tier or core tier for the new test? | `@pytest.mark.slow`, run by path | Core tier (about 5 s on a gate budgeted under 30 s) | `tests/slow_allowlist.txt:22`; AGENTS.md repo-local suite contract | yes |
