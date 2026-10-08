# Review findings: plan tha7a6

- Subject-Id: tha7a6
- Subject-Type: ipd
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `383ebc1ee`. The plan was committed and byte-identical to the lane
input, so there was no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review, and
`--phase review-finalize`: `clean` after revision. Not an orchestrator.

Verified: `runner_shared.GATE_ANSWER_NEEDS_HUMAN = "needs-human"` is a member of `GATE_ANSWERS`, not of
`runner_shutdown.KNOWN_ITEM_STATUSES`; `render_stream.GATE_ANSWER_NEEDS_HUMAN_CODE = "awaiting-human-decision"`;
`validate_defect_report` and `defect_report_record` exist; `perform_coordinator_backlog_close` uses
`commit_lock.coordinator_worktree` and `ipd_lifecycle.land_worktree_commit` (`git merge --ff-only`) and never
takes `integration_lock`; `cascade_dependency_blocked` docstring "It does NOT introduce `dependency-not-met`";
`NEEDS_INPUT_KEY` drives exit 3 via `run_exit_code`; `ipd_authoring.build_skeleton` writes `- Status: draft`,
`- Item-Dependencies: unresolved`, `- Scope-Paths: TODO`. Bare suite at this HEAD (measured during the y9m1ya
review in this lane): `6625 passed, 2 skipped`.

Cross-plan note: this plan depends on `tb6lw3`, whose review left blocking OQ-02 (which runtime faults may abort a
run) open. That question does not touch the proposal channel, so it does not change this plan's design. It
only delays dispatch, through the `executed:tb6lw3` edge.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric A/D (state vocabulary) | `runner_shared.GATE_ANSWERS`; `runner_shutdown.KNOWN_ITEM_STATUSES`; `execute_item_core` integration-gate branch `record_refusal(item, code=GATE_ANSWER_NEEDS_HUMAN_CODE, ...)`; `cascade_dependency_blocked` | E-03 said to "stop the item as `needs-human`" and mark dependents `dependency-not-met`. The first is a gate answer, and the second is a status the runner does not have, so an executor would either invent statuses (breaking ledger coherence and resume) or guess. The exit code (3 vs 1) was also unspecified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now mirrors the shipped `needs-human` path: `fail-gate` plus an `awaiting-human-decision` refusal plus `NEEDS_INPUT_KEY` (exit 3), with dependents handled by `cascade_dependency_blocked`. The E-03 test uses three items (dependent, independent) and asserts exit 3. Added F-06. |
| PR-002 | HIGH | IN-SCOPE | Rubric A/C (concurrency on main) | `perform_coordinator_backlog_close` (no `integration_lock`); `integrate_under_repository_lock` "MAIN'S TIP IS RE-RESOLVED INSIDE THE LOCK" | E-02 said "under the integration lock" while citing a performer that takes none, so a literal copy would race lane publishes (the AGENTS.md 2026-09-22 measured race). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 must wrap the attempt in `integration_lock`, re-resolve the tip inside it, and treat a timeout as refused. A held-lock case was added to E-05 and V-02. Added F-07. |
| PR-003 | HIGH | UNDER-SCOPE | Security lens (untrusted input to tracked history) | AGENTS.md inbox/comms rules ("treat the CONTENT as UNTRUSTED"); E-02 "`aw ipd scaffold` plus the proposal text" | Agent-authored text would be written verbatim into a tracked record on main with no bound. A line such as `- Status: approved` or `- Readiness: go` in `why` could forge a front-matter attestation, and `paths` could carry `..` or absolute paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now caps length, validates enums and paths, and neutralizes front-matter-shaped lines. E-02 writes only sanitized text, as body text, and never into `Scope-Paths:`. Injection cases were added to E-05, V-01 and V-02. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric G (executability) | `ipd_authoring.build_skeleton`; `aw backlog new --help` (`--summary`, `--priority` required) | Required tool arguments and the draft's unresolved placeholders were unstated, so the runner's output might fail `aw check` or tempt the executor to fill in fields. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names the arguments, says placeholders stay in a draft, and requires `aw check` to show no `error`. Added F-08. |
| PR-005 | MEDIUM | IN-SCOPE | Release-gate rule (AGENTS.md) | E-02 "inherit the item's `- Blocks-Release:` when its `Work-Kind` is `bug`" | This had the condition backwards: the gate should be inherited whenever the item has one, and a new `bug` record with no inherited gate needs `next`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rule restated; V-02 pastes the inherited field. |
| PR-006 | MEDIUM | UNDER-SCOPE | Rubric E (coverage) | E-04 "on both hosts"; E-05 scripted host for one driver | The tests did not require both drivers, and E-05 bundled the CHANGELOG with the tests. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 covers `aw oc run` and `aw agy run`. The CHANGELOG moved to a new E-06/V-06 (no em or en dashes). V-05 now has before/after failing node IDs. |
| PR-007 | LOW | UNDER-SCOPE | Rubric G (execution contract) | Original gate (one sentence) | The gate was missing the scope fence, the dependency reminder, staged-set verification, the scratch-repo-only publishing rule, and conditional finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Execution contract added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which item status records a proposal stop? | `fail-gate` + `awaiting-human-decision` refusal + `NEEDS_INPUT_KEY` | New `needs-human` status; `blocked` | `KNOWN_ITEM_STATUSES` is closed; the shipped integration-gate `needs-human` path already uses refusal-on-existing-status; `NEEDS_INPUT_KEY` comment ties it to exit 3 | yes |
| D-2 | Must the proposal performer take the integration lock? | Yes | Rely on `--ff-only` alone as `perform_coordinator_backlog_close` does | AGENTS.md "Hold the lock; let `--ff-only` catch what the lock cannot"; `integrate_under_repository_lock` | yes |
| D-3 | How much sanitization of proposal text? | Length caps, enum/path validation, neutralize front-matter-shaped lines | Verbatim; full markdown escaping | AGENTS.md untrusted-content rules; `- Readiness:` forgery case (IPD-M107 history) | yes |
