# Review findings: plan ju3rhs

- Subject-Id: ju3rhs
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `f5671f1a2`. The plan was committed and byte-identical to the lane input, so no pre-review
snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and
`--phase review-finalize` was clean after revision.

Re-verified with a gitignored scratch probe (`.aw/state/`) driving `cli.main` over throwaway git repos:
- From `approved`/`open`, with `--gate-kind bogus-kind --gate-ref x`: `aw specs set deferred abc123` rc 0, wrote
  `bogus-kind`; `aw set backlog blocked def456` rc 0, wrote; `aw backlog set <path> --status blocked` rc 0, wrote;
  `aw specs set deferred abc123` with no gate rc 0, deferred with no gate fields. Plan F-01 to F-04 hold.
- From an already-gated record (valid `external` gate), no gate flags: `aw specs set deferred abc123 --message note`
  rc 0, gate preserved; `aw set deferred abc123 --blocks-release next` rc 0, gate preserved;
  `aw backlog set blocked def456 --message note` rc 1 ("Moving backlog item to blocked requires ...");
  `aw specs set <path> --status deferred --message n` rc 1; `aw backlog set <path> --status blocked --message n` rc 2.
- E-02 as written (monkeypatched `status_set.validate_transition_allowed`, in-process, call counter 3): the two
  positional specs same-status calls above flipped to rc 1.
- `specs.run_set` gate block, `backlog.run_set` `if not gk or not gr`, `status_set` backlog arm and
  `apply_status_change` `if gk and gr:` read and match the plan's citations.
- `fv4b6s` is `- Status: graduated` (`Graduated-To: setdispgate`), not `open`.
- `m1jlwm` (setdisp Order 3) E-02 targets the same deferred gate-pair validation in `status_set`.
- Carriers resolve: `h4fiwa`, `fcnz1r` (graduated), `go8ztx`, `6bolin` (open).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | D. Anti-regression | `agent_workflows/status_set.py` `validate_transition_allowed`; `apply_status_change` `if gk and gr:` | E-02 keys the refusal on `norm_status == gate_status` alone, so every same-status metadata re-set of an already-deferred spec or blocked item with no gate flags (`--message`, `--blocks-release next`) would start refusing; measured with a patch: two rc 0 calls became rc 1. E-05's fences did not cover it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 bounds the refusal to a real transition in, or any passed gate flag; E-03 aligns `backlog.run_set` and records which way; E-05 adds a same-status fence; V-02/V-05 demand it pasted. |
| PR-002 | MEDIUM | IN-SCOPE | G. Stale state | `.aw/records/backlog/graduated/...-fv4b6s-...backlog.md` `- Status: graduated` | E-06 and V-06 required reading `fv4b6s` back at `- Status: open`, which is already false, and said the runner will set it `graduated`. V-06 was unsatisfiable. | all Low | FIXED | E-06, V-06 and the gate now require the status unchanged from pre-execution (graduated at review). |
| PR-003 | LOW | IN-SCOPE | G. Executability | `status_set.validate_transition_allowed` signature; existing `validate_release_exempt_flags("aw set", ...)` call | `validate_transition_allowed` cannot know which of five surfaces invoked it, so "names the command the operator typed" is unachievable there. | all Low | FIXED | E-01 now says pass `"aw set"` in `status_set` as the shipped precedent does. |
| PR-004 | MEDIUM | IN-SCOPE | C. Duplicate path | `20261001-setdisp-03-m1jlwm-...ipd.md` E-02 | `m1jlwm` E-02 implements the same validation in the same function; the plan described it only as a carrier question, not an execution-order hazard of double implementation. | all Low | FIXED | The gate now tells whichever executes second to consume the first's validator rather than add a second copy. |
| PR-005 | MEDIUM | IN-SCOPE | G. Execution contract | Approval gate "Post-gate lifecycle" | No scope-fence declaration, no `--scope-ack` for the possibly-unmodified `specs.py`, and no runner-vs-hand finalize ownership. | all Low | FIXED | Gate paragraph added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should a same-status re-set with no gate flags refuse? | No; preserve the on-disk gate (today's positional specs behavior). | Refuse whenever the target is the gated status. | Measured rc 0 today for `aw set deferred <id6> --blocks-release next`; `apply_status_change` only writes gates `if gk and gr`. | yes |
| D-2 | Verb label in `status_set`? | `"aw set"`, matching the exempt-flags precedent. | Plumb the dispatch verb through. | `validate_transition_allowed` signature; existing call site. | yes |
