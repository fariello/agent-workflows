# Review findings: plan jhdti8

- Subject-Id: jhdti8
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `4633d2627` in runner review-sweep lane `run-20261106T024139Z-372975` (non-interactive). The lane-input copy (revision 4) is byte-identical to the tracked plan (committed, unmodified), so no pre-review snapshot. `aw ipd lint --phase author` was clean before revisions; after revisions `--phase review-finalize` is clean with zero findings.

Context: the round-4 review of Order 01 `g4719s` recorded the maintainer's OQ-02 answer (2026-11-05): keep the standard shipped by `0cbfcc706` at `.aw/system/workflows/technical-writing/technical-writing.md`, amend spec `ecmw83`, and re-review the other Orders against the shipped path. This review applies that answer to Order 05.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern, E-01, gate | `.aw/system/workflows/standards/technical-artifact-writing.md` | Shipped path, resolved per target layout | PR-001, PR-002. |
| Concern, Scope | Review reached only through a bare slash command | Also names the steps-mode review (`review_sequence.render_prompt`) and the correction prompts, each with a reason | PR-005. |
| E-01 | "add to the contract section one line" | Exact helper, item numbers, position, and an "author or revise" wording | PR-003, PR-004. |
| E-02 | Byte comparison with a baseline commit; three builders | Three variants (both spec branches), layout cases, exact review-command assertion | PR-006. |
| Gate | Partial contract | Full execution contract | PR-007. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No: it adds one line to unattended authoring prompts; no CLI option, format, or spec changes.
2. No.
3. No: 3 E-items in one task group, one module plus one test.
4. Yes: three Scope-Paths, no `.spec.md`.
5. Low: additive prompt text, reversible through git.

Tier: standard (the runner prompt is shared by both hosts, so references and tests get full checks).

### Step R1

- Checked: `runner_shared.build_spec_production_prompt` (two branches on `spec_status == "implementing"`, contract lists end at item 8), `runner_shared.build_backlog_production_prompt` (ends at item 7), `runner_shared._append_continue_handoff_section` ("Production Contract items 1 and 2 apply to NEW plans only."), `runner_shared.build_review_prompt` (docstring: prose-free command line; returns `/plan-review <path>` when not isolated), `review_sequence.render_prompt`, `review_sequence.KERNEL_STEP_FILE`, `review_sequence.CHECK_STEP_FILES`, `runner_shared.build_production_set_correction_prompt` and `build_review_orchestrator_correction_prompt` (sent through `resume_via_launcher`), `engine.resolve_target_layout`, `engine.resolve_workflows_dir`; `.aw/system/workflows/standards/` does not exist; `0cbfcc706` shipped `technical-writing/technical-writing.md`; spec `ecmw83` R-06 and its Section 4 "Runner prompt" row.
- Probe: called the three builder variants on a temporary repository; first lines were `# Plan production from approved spec`, `# Plan production from implementing spec`, and `# Plan production from open backlog item`; `build_review_prompt` returned `'/plan-review .aw/records/plans/pending/x.ipd.md'`. Resolved the layout for an `aw`, a legacy, and an empty tree: `.aw/system/workflows/...`, `.agents/workflows/...`, `.aw/system/workflows/...`.

### Step R2

- Checked: E/V bijection 3/3; every V-item demands a pasted diff, output, or test run; V-02 adds a mutation run; spec trace cites `ecmw83` R-06 in E-01 and E-02; `Item-Dependencies: executed:g4719s` is required because the line names requirement 12, which `g4719s` E-02 adds.

### Step R3

- Checked: prompt text only; no trust boundary, secret, or command construction changes.

### Step R4

- Checked: the helper reuses `engine` layout resolution instead of a hard-coded path (C, KISS); appending keeps item-number references valid (D); the test calls the builders and asserts rendered output (E, P16); existing prompt-builder tests are named in E-03 and V-03; spec sync section is truthful.

### Step S5

- Checked: no open questions. D-1 to D-3 resolved from evidence.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | blocker | IN-SCOPE | D invariant | `g4719s` OQ-02 answer; `.aw/system/workflows/technical-writing/technical-writing.md` | E-01 and the gate named `standards/technical-artifact-writing.md`, which will never exist, so every prompt would point at a missing file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | All references use the shipped path. |
| PR-002 | medium | IN-SCOPE | E compatibility | `engine.resolve_target_layout`; `engine.resolve_workflows_dir` | A hard-coded `.aw/system/...` path is wrong for a legacy-layout target (`.agents/workflows/`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-01 resolves the path per target layout; E-02 tests both layouts. |
| PR-003 | medium | IN-SCOPE | G executability | E-01 "add to the contract section one line" | Position and numbering unspecified; renumbering would break "Production Contract items 1 and 2" in `_append_continue_handoff_section`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-01 appends as the last item (9, 9, 8) and forbids renumbering. |
| PR-004 | low | IN-SCOPE | D invariant | `runner_shared._append_continue_handoff_section` "Fix them in place" | "every plan you author" omits the continue-handoff case, where the agent revises existing plans. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Line says "author or revise". |
| PR-005 | medium | UNDER-SCOPE | R1 references | `review_sequence.render_prompt`; `runner_shared.build_production_set_correction_prompt` | Concern addressed only the slash-command review; the steps-mode review prompt and the correction prompts were not dispositioned. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Scope excludes each with its reason (step files via Order 06; corrections resume a session that holds the instruction). |
| PR-006 | medium | IN-SCOPE | E testing | E-02 "compare with its output ... at the baseline commit recorded before E-01" | The baseline comparison is not executable inside a test; the test also skipped the implementing-spec branch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-02 asserts the exact `/plan-review <path>` line and covers both spec branches; V-02 adds a mutation run. |
| PR-007 | medium | IN-SCOPE | G execution contract | plan gate | Gate lacked fence-as-declaration wording, the paste-output MUST, finalize ownership, no `git add -A`, and the spec and Order 01 preconditions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Gate rewritten to the Set's contract form. |
| PR-008 | low | UNDER-SCOPE | E testing | `tests/test_authoring_coverage_guidance.py`, `tests/test_production_resume_handoff.py`, `tests/test_spec_production.py` | Existing prompt-builder tests were not named for regression. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-03 and V-03 run them explicitly. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which path should the prompt name? | Shipped path, resolved per target layout | Old `standards/` path; fixed `.aw/system/...` string | `g4719s` OQ-02 maintainer answer 2026-11-05; `engine.resolve_target_layout` | yes |
| D-2 | Does R-06 require editing the review prompts? | No; they reach the standard through workflow bodies and step files (Order 06) | Append prose to `build_review_prompt` | `runner_shared.build_review_prompt` docstring (prose on the command line becomes path arguments); `review_sequence.render_prompt` lists the step files | yes |
| D-3 | Cover the correction prompts? | No | Add the line to both correction builders | They resume the session that received the authoring or review prompt (`resume_via_launcher` call sites) | yes |
