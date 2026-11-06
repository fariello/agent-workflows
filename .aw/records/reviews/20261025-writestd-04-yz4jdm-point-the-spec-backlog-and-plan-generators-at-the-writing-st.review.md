# Review findings: plan yz4jdm

- Subject-Id: yz4jdm
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `dc65717f0` in runner review-sweep lane `run-20261106T024139Z-372975` (non-interactive). The lane-input copy (revision 5) is byte-identical to the tracked plan, which was committed and unmodified, so no pre-review snapshot was needed. `aw ipd lint --phase author` was clean before the revisions. After the revisions, `--phase review-finalize` is clean with zero findings.

Context: the round-4 review of Order 01 `g4719s` recorded the maintainer's OQ-02 answer (2026-11-05): keep the standard that `0cbfcc706` shipped at `.aw/system/workflows/technical-writing/technical-writing.md`, amend spec `ecmw83`, and re-review the other Orders against the shipped path. This review applies that answer to Order 04.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern, E-01 to E-03, gate | `.aw/system/workflows/standards/technical-artifact-writing.md` | Shipped path, naming both install layouts | PR-001, PR-004. |
| E-01 | Pointer bullet in "Project conventions discovered (Step 0)" | Pointer line after the metadata block, for both plan kinds | PR-002. |
| E-01 | "If a fixture is compared byte for byte, regenerate it" | The two `assess` templates must be regenerated, using the exact parity-test arguments | PR-003. |
| E-01 to E-03 | Three hand-copied wordings | One function, `artifact_core.writing_standard_pointer` | PR-005. |
| E-03 | "after the `## Workflow history` block and before any body" | Before `## Workflow history`, in the new-item branch only | PR-006. |
| E-04 | Asserts the path is present and the check passes | Also checks one occurrence, placement, a status transition, and a mutation run | PR-007. |
| Scope-Paths | `tests/fixtures/` | Removed; `agent_workflows/artifact_core.py` added | PR-008. |
| Gate | Partial contract | Full execution contract | PR-009. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes, but the change is small: new plans, specs, and backlog items gain one line, and the byte-pinned templates change. No CLI option or file-format change.
2. No.
3. Moderate: 5 E-items in 2 task groups across three generator modules.
4. Yes: eight Scope-Paths, none of them a `.spec.md` file.
5. Low: an additive line, reversible through git. The template parity test catches drift.

Tier: standard.

### Step R1

- Checked:
  - `ipd_authoring._SECTION_BODY` (the comment under `S.H_PROJECT_CONVENTIONS` on permanent guidance) and `ipd_authoring._AUTHORING_PLACEHOLDERS`.
  - `ipd_authoring.build_skeleton`, which writes the metadata block and then the H2 headings in `S.H2_ORDER_BY_KIND` order.
  - `ipd_schema.ORCHESTRATOR_H2_ORDER`, which has no Project-conventions heading.
  - `tests/test_ipd_templates.py::TemplateParityTests`, which compares both templates byte for byte with `build_skeleton` output.
  - `tests/test_ipd_schema.py` `CHILD_TEMPLATE` and `ORCH_IPD`, which use `tests/fixtures/conforming-orchestrator.md`, a static fixture that has no parity test.
  - `specs._render_new_spec`.
  - `backlog._render_item`: the new-item branch, the `source_text` branch that keeps header prose (rendrop `2yqt0a` E-07), and the `set_records` callers.
  - `.aw/system/workflows/standards/` does not exist.
- Probes, all run in temporary repositories:
  - A `>` pointer line after the metadata block lints `conforming` at `author`, `review-finalize`, and `pre-execution`, for both plan kinds (using `tests.support.ready_plan_text`).
  - The same line in a spec survives `aw specs set --status to-review`, and `validate_spec` returns `[]`.
  - The same line in a backlog item, placed before `## Workflow history`, survives `aw backlog set --status parked`, and `validate_item` returns `[]`.
  - `aw ipd set` and `aw ipd sync` keep the line in a plan.
  - `aw check all --agent` on an installed repository reports the same rule set with and without the line (delta: empty set).

### Step R2

- Checked:
  - The E/V bijection is 5 to 5.
  - Every V-item demands a pasted diff, file text, check result, or test run. V-04 adds a mutation run.
  - The spec trace cites `ecmw83` R-06 and AC-04.
  - `Item-Dependencies: executed:g4719s` is required, because the line names requirement 12, which `g4719s` E-02 adds.

### Step R3

- Checked: the change is generated text only. It touches no trust boundary and no secret.

### Step R4

- Checked:
  - One shared wording function. `artifact_core` is already imported by all three generators, so no new import edge is created.
  - The placement survives the transition writers, which was verified by probe.
  - The test drives the real CLI and asserts on the written files (P16).
  - The existing generator tests are named in E-05 and V-05.
  - The spec-sync section is truthful.

### Step S5

- Checked: there are no open questions. D-1 to D-4 were resolved from evidence.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | blocker | IN-SCOPE | D invariant | `g4719s` OQ-02; `.aw/system/workflows/technical-writing/technical-writing.md` | Every pointer and the gate named `standards/technical-artifact-writing.md`, which will never exist, so every new artifact would point at a missing file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | All references now use the shipped path. |
| PR-002 | high | IN-SCOPE | G executability | `ipd_schema.ORCHESTRATOR_H2_ORDER` | E-01 put the bullet in "Project conventions discovered (Step 0)", a heading orchestrator plans do not have, so the bullet could not reach `orchestrator-ipd.md` or a scaffolded orchestrator. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | The line now goes after the metadata block for both kinds. A probe showed it lints conforming. |
| PR-003 | high | UNDER-SCOPE | D invariant | `tests/test_ipd_templates.py::TemplateParityTests` | The templates are byte-pinned to `build_skeleton` output. Hand-adding a line to them, as E-01 said, fails parity. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-01 regenerates both templates using the parity test's exact arguments. |
| PR-004 | medium | IN-SCOPE | E compatibility | `engine.resolve_workflows_dir` (legacy `.agents/workflows`) | A single `.aw/system/...` path is wrong in a legacy-layout install, and a record cannot use a path relative to a workflow body. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | The line names both layouts (D-2). |
| PR-005 | low | IN-SCOPE | C architecture | E-01 to E-03 | Three hand-copied wordings would drift apart. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | One function: `artifact_core.writing_standard_pointer`. |
| PR-006 | medium | IN-SCOPE | A data integrity | `backlog._render_item` `source_text` branch | Placing the line "after the history block, before any body" makes it body text, and E-03 left open whether the transition re-render keeps it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | The line goes before `## Workflow history`, in the new-item branch only. A probe showed it survives `aw backlog set`. |
| PR-007 | medium | IN-SCOPE | E testing | E-04 | The test checked presence only. It would pass if the line were duplicated or lost on the first transition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | The test now asserts one occurrence, placement, survival of a transition, and a mutation run. |
| PR-008 | low | IN-SCOPE | G scope fence | Scope-Paths `tests/fixtures/` | `tests/fixtures/` holds no scaffold-parity fixture, so declaring it would force a `--scope-ack`. The shared function's module was not declared. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Removed `tests/fixtures/` and added `agent_workflows/artifact_core.py`. |
| PR-009 | medium | IN-SCOPE | G execution contract | plan gate | The gate was missing parts of the contract: the scope fence stated as a declaration, the paste-the-actual-output MUST, finalize ownership, the ban on `git add -A`, and the spec and Order 01 preconditions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Gate rewritten in the Set's contract form. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where does the line go? | After the metadata block, before `## Workflow history`, for all three artifact types | A Project-conventions bullet (child plans only); after the history block | `ipd_schema.ORCHESTRATOR_H2_ORDER`; probes showing conforming lint and survival of transitions | yes |
| D-2 | Which path form? | `.aw/system/...`, with the legacy path in parentheses | Layout-resolved at generation time (impossible for the byte-pinned templates); `.aw/system/...` only | `tests/test_ipd_templates.py` has no target repository; `engine.resolve_workflows_dir` | yes |
| D-3 | Regenerate the templates? | Yes, from `build_skeleton` | Hand-edit them | `TemplateParityTests` byte comparison | yes |
| D-4 | Add the line to existing artifacts? | No; the sweep Orders 07 to 09 handle them | Backfill here | Spec `ecmw83` R-08 assigns live artifacts to the sweep | yes |
