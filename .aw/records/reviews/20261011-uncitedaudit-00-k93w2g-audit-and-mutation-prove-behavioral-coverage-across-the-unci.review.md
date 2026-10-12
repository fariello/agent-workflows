# Review findings: plan k93w2g

- Subject-Id: k93w2g
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (LOW, fixed), PR-002 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `7028b6f22`. Plan committed and byte-identical to the lane input; no
pre-review snapshot. Orchestrator (`- Kind: orchestrator`). `aw ipd lint --phase author` and `--phase review-finalize`:
`clean` before revision. `aw ipd coverage k93w2g`: "ready for review".

Verified: all eight children exist in `pending/` with `- Order:` 1..8, `- Id:` and `- From-Backlog: e486tz` matching the
`## Child IPDs` table; each child's `- Item-Dependencies:` equals the table's "Depends on" column, and E-01..E-08's
`Depends on` mirror those edges. Child statuses: `1ub8ex`, `nzzu8n`, `g55j1e` `reviewed`; `sk2rbf`, `8d0qsg`, `anzu8q`,
`rq3q7v`, `xmr5qj` `to-review`. Completion-criteria owners resolve: `8d0qsg` E-03 (verdicts), `anzu8q` E-01, `rq3q7v`
E-02, `xmr5qj` E-02 / E-03 (a)-(e) (E-03 (e) enumerates the eight instrument files plus `tools/README.md`). Cross-IPD
owners resolve: `8d0qsg` V-01 demands equality with a pasted `--summary` line; `sk2rbf` E-04 replays through
`deleted_test_replay`; `nzzu8n` mentions `python_prefix`. `python3 tools/lost_guard_census.py --summary` at
`7028b6f22`: "Uncited deleted files: 209 files holding 3585 removed functions", matching the Concern. Backlog `e486tz`
is `graduated` to all nine ids. No orchestrator item carries work of its own beyond confirming children.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | Rubric G (live-artifact bar) | Completion criterion 1; backlog `e486tz` says 207, Concern says 209 | The uncited population is a live count (it moves as docs cite deleted files); criterion 1 did not say the bar is equality with a same-HEAD census re-run rather than a fixed number. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Criterion 1 states the count is live and the bar is equality with `--summary` on the same HEAD. |
| PR-002 | LOW | IN-SCOPE | Rubric G (ownership, gate clarity) | OQ-01 `Owner: none`; gate "Requires explicit human approval of each child" | An author-made resolution recorded no owner; the gate did not state that five children are still `to-review` and need their own review, which this review does not supply. | all Low | FIXED | Owner set to `plan author`; gate names child review states. |

### Orchestrator gate attempts (IPD-S407 / IPD-S408)

- Attempt 1: after the PR-001/PR-002 edits, `aw ipd lint --phase review-finalize` reported `IPD-S408` (the recorded
  `- Coverage-Fingerprint:` no longer matched the edited text). `aw ipd coverage k93w2g` re-ran: "ready for review",
  recording fingerprint `d726a52ad65c`. Child-table rows: 8 -> 8 (no deletion). Re-lint: conforming. No `IPD-S407`
  violation at any point.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep OQ-01 (build three instruments rather than read by hand)? | Keep. | Narrower Set dropping Order 04 (rejected: every mutant would run the full ~200 s selection; the plan already offers that trade). | census line counts; plan OQ-01. | yes |
| D-2 | Is excluding removals from the 20 modified files correct? | Keep the Carrier-Declined exclusion. | Add them (rejected: outside backlog `e486tz`'s stated population). | `e486tz` body; census prints modified count. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
