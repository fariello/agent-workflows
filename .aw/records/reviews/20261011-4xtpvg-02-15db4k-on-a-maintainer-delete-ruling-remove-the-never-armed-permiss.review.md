# Review findings: plan 15db4k

- Subject-Id: 15db4k
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `b1b2fab2b`. The plan was committed and byte-identical to the
lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review. Not an
orchestrator (`- Kind: child`), so S407/S408 do not apply. Baseline:
`python3 -m pytest -o addopts="" -q tests/test_turn_bounds.py tests/test_permission_bound_disabled.py`
-> `16 passed in 3.66s`.

Verified at HEAD: `note_permission_request` has one introducing commit (`git log -S` -> `8a491d4c1`,
2026-09-05) and no production caller; `note_progress` body only clears `_permission_pending_since`, called
once per stdout line in `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn`; `turn_bound_expiry` /
`turn-bound-expired` / `permission-timeout` are read by no module outside `lane_containment`;
`containment_layers` (which carries the `CONTAINMENT_LAYERS_WITHOUT_HOST_DENIAL` string) is asserted by no
test; `ipd_schema` "Approval iff Status is approved (auto-approved does NOT carry human Approval)" holds;
the spec's "WITHDRAWN by R3.3a. Formerly:" convention exists (A7b-1..A7b-3). E-09's mechanism was
DEMONSTRATED with a scratch script (real watch: rc -2 at 0.43s, bound max-turn-timeout, 33 lines read;
`_expired` stubbed: survived to 3.0s, 295 lines read, no record).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric B/G; backlog `e6zeta` ("must NOT be closed by an agent picking a side") | `agent_workflows/plan_readiness.py` `is_plan_review_approved` (`return readiness in _schema.READINESS_APPROVABLE`); `agent_workflows/runner_shared.py` queue build (`if status == "reviewed" and full_auto` ... `status = "auto-approved"`); plan gate ("A reviewer should set at most `go-pending-approval`") | The plan's only guard against `--full-auto` deciding the maintainer's ruling was an in-turn E-01 check. Measured: a copy of this plan at `reviewed` + `go-pending-approval` with a review record makes `is_plan_review_approved` return `True`, so `--full-auto` would auto-approve it and dispatch an execute turn whose correctness then rests on the executing agent honoring E-01. OQ-01 was `Blocking: no`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 is now `Blocking: yes` / `open`, Owner maintainer, with the DELETE and KEEP answer procedures. Demonstrated on a scratch copy: `IPD-Q501` exit 1 at `author`, `review-finalize`, `pre-execution`. Readiness `no-go`. E-01/V-01 also check OQ-01's resolution; gate, Concern, Scope, Goal, conventions updated. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric D; plan F-7 | `agent_workflows/lane_containment.py` `PERMISSION_TIMEOUT` `#:` block (`CONSEQUENCE, stated plainly:` and `RESIDUAL LIMITS:` paragraphs) | E-03 deleted "the `PERMISSION_TIMEOUT` constant and its whole `#:` comment block", which is the only code-side statement of the non-isolated and antigravity limits that F-7 says survive deletion. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now moves those paragraphs onto `MAX_TURN_TIMEOUT`'s block in their execution-time wording; E-03 outcome and V-03 demand it. |
| PR-003 | MEDIUM | UNDER-SCOPE | Spec sync; AGENTS.md "A PLAN MAY AMEND A SPEC" | spec `7ckptx` early host summary ("R4.4 driver bounds"), R4.1 / R4.1a ("driver-side bounds"), A8b ("R4.4 driver bounds"), A10c ("show the artifact stating that `MAX_TURN_TIMEOUT` is consequently the only bound covering a permission deadlock") | E-07's enumeration missed the plural-bound references outside R4.4/A10, and withdrawing A10c dropped its one surviving obligation. Scope line also omitted A10e. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now singularizes plural references found by a named grep (keeping R4.4d's host-plus-driver sense), moves A10c's surviving obligation into A10b; V-07 pastes and classifies the grep; Scope lists A10e. |
| PR-004 | LOW | IN-SCOPE | Rubric G (executability) | `TurnBoundWatch.__init__` (`self._lock = threading.Lock()`, used only by the permission accesses); `agy_runipd.run_agy_turn` construction comment (names no permission symbol); `test_reset_asymmetry_max_turn_survives_progress` (calls `note_progress`); scratch E-09 run printed a `KeyboardInterrupt` traceback | Four small precision gaps: `_lock` would be left dead; V-04 demanded a construction-comment change in `agy_runipd` that E-04 does not make; E-06's "every remaining test passes" is false until E-09 lands; E-09's child writes a traceback to stderr on reap and did not assert it was chatty. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 removes `_lock`; V-04 scoped to `oc_runipd` for the comment; E-06 outcome names the interim failure; E-09 adds `stderr=DEVNULL` and a line-count assertion, plus the recorded demonstration. |
| PR-005 | LOW | UNDER-SCOPE | Rubric G (cross-plan coupling) | pending plan `thzrpo` (Set `4xtpvg`, Order 2) E-04(b) rewrites the `RESIDUAL LIMITS:` paragraph of `PERMISSION_TIMEOUT`'s block; both declare `lane_containment.py` and the spec | Semantic coupling on one paragraph: whichever lands second must find it at its current home. Not a runner hazard (isolated worktrees, merge-and-revalidate gate). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate states the coupling and tells E-03 to move the paragraph in its execution-time wording and record its new home for `thzrpo`. No dependency edge added, since either order is valid. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the maintainer-only ruling be held away from `--full-auto`? | Make OQ-01 `Blocking: yes` / `open`, Readiness `no-go`. | Keep non-blocking and rely on E-01 (REJECTED: measured predicate returns True; E-01 relies on the executing agent). Add an `Item-Dependencies` gate (REJECTED: no edge kind expresses a human ruling). | `plan_readiness.is_plan_review_approved`; `runner_shared` full-auto queue build; backlog `e6zeta`; scratch lint demonstration. | yes |
| D-2 | Delete or relocate the residual-limits prose? | Relocate onto `MAX_TURN_TIMEOUT`. | Delete with the constant (REJECTED: loses F-7's only code-side statement). | plan F-7; `lane_containment` `PERMISSION_TIMEOUT` block. | yes |
| D-4 | Accept the `aw check` cost of a blocking question on a graduated item's plan? | Yes, documented in OQ-01. Measured at HEAD vs after this review: `check plans` 62 -> 65 findings (all three new are `info`), `check backlog` 3 -> 4 and `check specs` 1 -> 2 (each `+1` is `check.graduation-incomplete`, error, on `e6zeta` / `7ckptx`); `check specs` exit 0 -> 1. | Non-blocking OQ-01 plus `Readiness: no-go` (REJECTED: measured `recheck_conditions(...).may_write == True`, so any agent running `aw ipd recheck-readiness --apply` could lift it to `go-pending-approval`, after which `--full-auto` clears it; it also contradicts the review contract, under which a non-blocking question cannot justify `no-go`). | `plan_readiness.recheck_conditions`; plan-review "Verdict and readiness"; scratch-copy measurements. | yes; maintainer told in the review report 2026-10-12 |
| D-3 | Add a dependency edge between `15db4k` and `thzrpo`? | No; document the coupling. | Edge either way (REJECTED: both are valid in either order, and an edge would serialize a KEEP-retired plan against a live one). | AGENTS.md runner guarantees (isolated worktrees, merge-and-revalidate). | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`. OQ-01 is open by design: it is the maintainer's KEEP/DELETE ruling, not a review finding.
