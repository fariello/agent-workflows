# Review findings: plan wdyz5n

- Subject-Id: wdyz5n
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `9ccffaca3`. The plan was committed and byte-identical to the lane input, so no pre-review
snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and
`--phase review-finalize` was clean after revision.

Re-verified with a scratch probe driving `cli.main` over throwaway git repos (spec at `implementing`, no `--evidence`):
- `aw specs set implemented abc123` rc 0, file relocated; `aw set implemented abc123` rc 0, relocated;
  `aw set specs implemented abc123` rc 0, relocated; `aw specs set <path> --status implemented` rc 1 with
  `requires a resolvable --evidence citation (an existing .agents/plans/executed/ IPD path); refused.`. F-01/F-02 hold.
- Spec already at `implemented`: positional re-set rc 0 (`unchanged`); `--status` re-set rc 1 with the evidence refusal,
  because `specs.run_set`'s `if auth.get("evidence"):` is not guarded by `old != new`.
- `aw set --help` does not list `--evidence`; `p_specs_set` registers it with help "Resolvable implementation-evidence citation (for implemented)."
- `status_set.validate_transition_allowed` specs block binds `auth` and carries the `->reviewed` `_specs._review_attestation_refusal` precedent; no evidence branch.
- `specs._evidence_resolvable` accepts `.agents/plans/executed` or `.aw/records/plans/executed`; `TRANSITION_AUTHORITY["->implemented"]["evidence"]` is True.
- `run_set_command`'s backlog arm and `apply_status_change`'s Close-Evidence write both read `getattr(args, "evidence", None)`.
- No test in `tests/` asserts a declared-minus-accepted agreement for the `set` declaration; no test pins the legacy refusal wording.
- `h4fiwa` is `- Status: graduated` (`Graduated-To: setdispgate`), `- Blocks-Release: next`.
- Executed `47ttnv` E-03/E-06 precedent quote verified. Carriers `fv4b6s`, `fcnz1r`, `m94eht`, `6bolin` resolve.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | D. Anti-regression / E. Testing | `agent_workflows/specs.py` `run_set` `if auth.get("evidence"):` (no `old != new` guard) | E-04 required the no-op fence paired on both spellings with the same outcome, but the `--status` spelling already refuses an `implemented -> implemented` re-set (measured rc 1) while the positional one succeeds. The paired test was unsatisfiable without either changing `specs.run_set` out of scope or pinning a mismatch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now pins the no-op on the positional/untyped surfaces only, states why it is unpaired, and forbids asserting the `--status` no-op either way; V-04 checks it. |
| PR-002 | MEDIUM | IN-SCOPE | C. Duplicate path / UX | `specs.run_set` refusal text; plan F-03 | E-01 fixed the stale `.agents/` path only in the new message while V-01 demanded both spellings match; `specs.py` was in Scope-Paths with an edit that does not exist ("predicate is made reachable"). | all Low | FIXED | E-01 corrects both messages; Scope check names the real `specs.py` edit; V-01/V-06 verify both. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. Testing | `tests/test_backlog_handoff_close.py` etc. declared-minus-accepted asserts cover other verbs | V-02 asked to paste "the existing declared-minus-accepted agreement test(s) for the set family", which does not exist, so the evidence was unproducible. | all Low | FIXED | E-02/E-04 add one agreement assertion for `set`; V-02 demands it. |
| PR-004 | MEDIUM | UNDER-SCOPE | D. Anti-regression | `status_set.run_set_command` backlog arm `ev_arg = getattr(args, "evidence", None)` | Registering `--evidence` on `p_set` also activates the SATISFIED close route for backlog items on `aw set`; the plan did not mention this second effect. | all Low | FIXED | E-02 documents it as intended (parity with `aw backlog set`), requires help text and `dest="evidence"`; E-04/V-02 pin it. |
| PR-005 | MEDIUM | IN-SCOPE | G. Stale state | `.aw/records/backlog/graduated/...-h4fiwa-...backlog.md` `- Status: graduated` | E-06/V-06 required `h4fiwa` read back at `- Status: open`, already false; gate said the runner will set it graduated. V-06 was unsatisfiable. | all Low | FIXED | E-06, V-06 and the gate require the status unchanged from pre-execution (graduated at review). |
| PR-006 | MEDIUM | IN-SCOPE | G. Execution contract | Approval gate; V-04 `git stash` | No scope-fence declaration, no runner-vs-hand finalize ownership, the overlapping sibling unnamed (it is `m94eht`, draft, not to-review as claimed), and V-04 suggested `git stash`, unsafe in a shared checkout. | all Low | FIXED | Gate names `m94eht` with consume-not-duplicate ordering, adds scope fence and finalize ownership; V-04 uses a scratch worktree. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the `--status` no-op refusal be fixed here so the no-op fence can be paired? | No; leave it, fence positional only | Add `old != new` guard to `specs.run_set` in this plan | Plan Deferred section defers fork unification to `fcnz1r`/`m94eht`; the behavior is fail-closed, not a bypass | yes |
| D-2 | Is `--evidence` reaching the backlog close gate on `aw set` acceptable? | Yes, document and pin it | Register under a spec-only dest | `aw backlog set` already accepts `--evidence` for the SATISFIED route (`cli.py` `p_backlog_set` help); parity across spellings is the plan's goal | yes |
| D-3 | Fix the legacy path in the existing `specs.run_set` message too? | Yes | Fix only the new message | V-01 demands identical reasons; F-03 measured the wording stale; no test pins it | yes |
