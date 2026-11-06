# Review findings: plan e4n4p3

- Subject-Id: e4n4p3
- Subject-Type: ipd
- Reviewed-At: 2026-11-05
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `8ffe56222` in runner review-sweep lane `run-20261106T024139Z-372975` (non-interactive). The lane-input copy (revision 2) is byte-identical to the tracked plan (committed, unmodified), so no pre-review snapshot. `aw ipd lint --phase author` was clean (one info `IPD-Z602`) before revisions. After revisions `--phase review-finalize` is clean with zero findings.

Context: the round-4 review of Order 01 `g4719s` (merged as `8ffe56222`) recorded the maintainer's OQ-02 answer: keep the standard shipped by `0cbfcc706` at `.aw/system/workflows/technical-writing/technical-writing.md`, amend spec `ecmw83`, and re-review Orders 02 to 09 against the shipped path. This review applies that answer to Order 06.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern, Scope, Goal | Standard not yet referenced anywhere | States which bodies `0cbfcc706` already wired and which remain | PR-001. |
| Every E-item and gate | `.aw/system/workflows/standards/technical-artifact-writing.md` | Relative `../technical-writing/technical-writing.md` form | PR-002, PR-003. |
| Scope-Paths | `plan-review/steps/*.md` glob | The two step files actually edited, plus `research-prompt.md` | PR-004, PR-005. |
| E-07 | Asserts body "contains the standard's path" | Asserts every pointer resolves in an installed repo | PR-006. |
| Gate | Partial contract | Full execution contract | PR-008. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes: it edits shipped workflow bodies and amends approved spec `k3yx72`.
2. No.
3. Moderate: 8 E-items in 3 task groups, all prose edits to workflow bodies plus one test.
4. Yes: fourteen Scope-Paths, one `.spec.md`.
5. Low: text edits, reversible through git.

Tier: standard.

### Step R1

- Checked: `git show 0cbfcc706` (adds pointer lines to `spec/spec.md`, `spec-review/spec-review.md`, `plan-review/plan-review.md`, `plan-review-long/plan-review-long.md`, `research-prompt/research-prompt.md`); `grep technical-writing` finds no pointer in `ipd-lifecycle.md`, `advise/personas/spec-editor.md`, `plan-review/steps/*.md`, `plan-review-long/02-review-and-revise.md`, or `review-rubric.md`; `p-proofread.md` first two paragraphs apply `wcisgc` and its fallback summary; `spec.md` and `research-prompt.md` say "all eleven numbered requirements"; spec `k3yx72` N5, the Section 1 "Proofreading instructions" row, and the section-map row "(new) proofreading" name `wcisgc`; `3bwrfx` is in `executed/`; headings "## Execute" (`ipd-lifecycle.md`), "## Spec structure" (`spec.md`), "## Questioning style" (`spec-editor.md`), "## Spec rubric" (`spec-review.md`), "## Required context" (`02-review-and-revise.md`), "## H. Operations and documentation" as the last rubric section (`review-rubric.md`), "## Memory kernel" items 1 to 9 (`_kernel.md`).
- Probe: for each shipped body, extracted backticked refs ending `technical-writing/technical-writing.md` and resolved them relative to the body directory; all five resolved (`True`). This is the E-07 mechanism.

### Step R2

- Checked: E/V bijection 8/8; every V-item demands a pasted diff, grep, or test run; spec trace now cites `ecmw83` R-04, R-06; `Item-Dependencies: executed:g4719s, executed:3bwrfx` (3bwrfx satisfied; g4719s required because E-01, E-04 reference requirement 12 and the "Proofreading procedure" section it adds).

### Step R3

- Checked: no code, no trust boundary.

### Step R4

- Checked: E-07 asserts link integrity of delivered pointers in an installed repo (an outcome; precedent `tests/test_technical_writing_delivery.py` asserts the installed `AGENTS.md` names the standard). V-07 adds a mutation check (P16 "verify test sensitivity"). Spec sync for `k3yx72` declared.

### Step S5

- Checked: no open questions; the path and dash question was answered by the maintainer under `g4719s` OQ-02 (2026-11-05). D-1 to D-3 resolved from evidence.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | high | IN-SCOPE | R1 references | `0cbfcc706`; `.aw/system/workflows/spec/spec.md` "Write the spec to the technical writing standard" | Four of the bodies the plan would edit already carry a pointer; E-01, E-03, E-05 would duplicate them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-items now extend the existing lines and add only what is missing. |
| PR-002 | blocker | IN-SCOPE | D invariant | `g4719s` OQ-02 answer; `.aw/system/workflows/technical-writing/technical-writing.md` | Every E-item and the gate named `standards/technical-artifact-writing.md`, which will never exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | All references use the shipped path. |
| PR-003 | medium | IN-SCOPE | E compatibility | `engine.agents_pointer_prose` legacy layout `.agents/workflows`; shipped relative pointers | A hard-coded `.aw/system/...` path inside a body is wrong in the legacy install layout. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Plan mandates the relative form and gives both depths. |
| PR-004 | medium | UNDER-SCOPE | D invariant | `spec.md` and `research-prompt.md` "all eleven numbered requirements" | Once Order 01 adds requirement 12 these counts are wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-01 removes the count; `research-prompt.md` added to Scope-Paths. |
| PR-005 | low | IN-SCOPE | G executability | Scope-Paths `plan-review/steps/*.md` | A glob declares every step file; only two are edited, so finalize would demand `--scope-ack` for the rest. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Named `p-proofread.md` and `_kernel.md`. |
| PR-006 | medium | IN-SCOPE | E testing | E-07 "contains the standard's path" | A substring check is closer to a text pin than an outcome and passes for a broken relative path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-07 resolves each pointer in an installed repo; V-07 adds a mutation run. |
| PR-007 | low | UNDER-SCOPE | R1 references | `k3yx72` section-map row "(new) proofreading" | E-06 amended N5 and one `wcisgc` row but missed the section-map row. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-06 amends three locations. |
| PR-008 | medium | IN-SCOPE | G execution contract | plan gate | Gate lacked fence-as-declaration, paste-output MUST, finalize ownership, no `git add -A`, spec and Order 01 preconditions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Gate rewritten. |
| PR-009 | low | IN-SCOPE | G spec trace | E-items cited bare `R-06` | No qualified spec ids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-items cite `ecmw83` R-04, R-06. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which path should bodies name? | Shipped path, relative form | Old `standards/` path; absolute `.aw/system/...` | `g4719s` OQ-02 maintainer answer 2026-11-05; shipped pointers in `0cbfcc706` use the relative form | yes |
| D-2 | Add `research-prompt.md` although R-06 does not list it? | Yes, count fix only | Leave the stale count | Its "all eleven" becomes false after Order 01; one-line fix | yes |
| D-3 | Keep the new test given P16? | Yes, as a link-integrity test in an installed repo | Drop the test | Asserts a delivered outcome (each pointer resolves), not source shape; mirrors `tests/test_technical_writing_delivery.py` | yes |
