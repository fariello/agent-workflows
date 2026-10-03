# Review: Widen the Section 8.8 control-character predicate to reject bidi overrides and isolates

- Subject-Id: 0obt4k
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before review.

The core thesis was re-verified in this lane. `attention_contract._CONTROL_CHAR_RE` is `[\x00-\x1f\x7f-\x9f]`. `is_safe_descriptive`, `validate_gate_ref("external", ...)`, `specs._refuse_unsafe_descriptive` and `backlog._refuse_unsafe_descriptive` all accept `"fix auth \u202ereversed\u202c now"`. Spec Section 8.8's bullet reads as quoted. The proposed widened class `[\x00-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]` matches exactly the nine intended code points within U+2000..U+20FF, matches U+2069, and does not match U+200B, U+2065 or U+2029. `tests/test_attention_contract.py::test_output_safety` carries the five assertions F-10 describes.

The defects were all in citations, in evidence feasibility, and in the execution contract. The design itself is sound.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Evidence citations | agent_workflows/releases.py:108 `def validate_release`; agent_workflows/backlog.py:409 `def validate_item` | F-5, F-6 and E-04 cite `releases._check_one` and `backlog._check_one`. Neither symbol exists. The real consumers are `releases.validate_release` and `backlog.validate_item`, and backlog emits `backlog.*-unsafe` rule ids, not `attention.unsafe-field`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Citations corrected and the backlog rule ids named. |
| PR-002 | MEDIUM | UNDER-SCOPE | Testing (D/E) | agent_workflows/releases.py:145 `A._CONTROL_CHAR_RE.search(prose_summary)` | F-6 identifies the release prose-summary consumer as the one place the widening could surprise, but E-02/V-02 had no behavioral test for it. The widening's effect on that consumer was therefore covered only by the corpus diff. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and V-02 now require a `releases.validate_release` test that expects an `attention.unsafe-field` drift for a bidi control in summary prose. |
| PR-003 | HIGH | IN-SCOPE | Evidence feasibility / live-artifact criteria (G) | /tmp capture: `aw check --agent` 97 findings across live rules (`check.scope-drift`, `check.lifecycle-transition-invalid`); `attention --check` includes `attention.lane-stranded` | E-04/V-04 demanded EQUALITY of the full unrestricted diagnostic sets. Those sets contain live rules unrelated to the predicate, and they can move between captures, so the demand could fail spuriously. It also pinned the authoring-time counts (three suite failures, one 89xjll finding) as the bar, which breaks the re-derivation convention. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The comparison is restricted to the four predicate-sensitive rule ids, with unrestricted captures pasted as context. The baseline and pre-existing failures are re-derived at execution through a before/after suite run, and the authoring counts are kept as context only. |
| PR-004 | MEDIUM | IN-SCOPE | Spec sync mechanism | spec `## Workflow history` lines 340-342 `note (aw specs): AMENDED by plan ...`; `aw specs note --help` | E-05 said to append "a dated amendment note in the body style the spec already uses" while forbidding Workflow-history changes. The spec's actual established amendment style is an `aw specs note` AMENDED record in `## Workflow history` (three precedents), so the instruction contradicted itself. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05/V-05 now mandate `aw specs note ... "AMENDED by plan 0obt4k ..."`, forbid `aw specs set` and hand edits to history, and require Status to remain `implemented`. |
| PR-005 | LOW | UNDER-SCOPE | Project rule (AGENTS.md execution contract) | AGENTS.md "write no em or en dashes in USER-FACING prose" | The CHANGELOG entry is user-facing prose, and the plan did not carry the no-dash rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 expected outcome and V-05 evidence now require a dash-free CHANGELOG entry. |
| PR-006 | MEDIUM | UNDER-SCOPE | Execution contract (G / Step 4) | plan `## Approval and execution gate` | The gate was missing three elements: the scope-fence declaration semantics (justify via `--scope-reason`/`--scope-ack`), the hard-MUST paste-actual-output rule, and the conditional lifecycle ownership (runner vs executor `aw ipd finalize`, no hand `git mv`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three were added to the gate paragraph. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which diagnostic set must stay equal across the E-01 edit? | The four rule ids whose verdict reads the widened predicate: `attention.unsafe-field`, `backlog.summary-unsafe`, `backlog.gate-descriptive-unsafe`, `backlog.close-evidence-unsafe` | Full unrestricted equality, which is spuriously fragile on live rules; `attention.unsafe-field` only, which misses backlog consumers | agent_workflows/backlog.py:486,542,589; agent_workflows/releases.py:133,145; agent_workflows/specs.py drift rule ids | yes |
| D-2 | How is the spec amendment recorded? | `aw specs note` AMENDED record, Status unchanged | Hand body note, which has no precedent on this spec; `aw specs set`, which would forge a lifecycle event | spec Workflow history lines 340-342; `aw specs note --help` | yes |
| D-3 | Is the targeted nine-code-point class (OQ-01) correct? | Accept the author's resolution | Whole `Cf` category | Demonstrated in this lane: the widened regex matches exactly U+202A..U+202E and U+2066..U+2069 within U+2000..U+20FF and does not match U+200B | yes |
