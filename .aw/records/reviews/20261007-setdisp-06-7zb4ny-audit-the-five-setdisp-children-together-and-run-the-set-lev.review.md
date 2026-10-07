# Review findings: plan 7zb4ny

- Subject-Id: 7zb4ny
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `3a4f8b232`. The plan was committed and byte-identical to the
sealed lane input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent`: `clean`. After revision,
`--phase review-finalize --detail` reports `advisory` with one `IPD-Z602` on E-06. That advisory is judged
a false positive: E-06 has one concern (a failure-set comparison), and the two runs it names are the two
halves of that comparison. E-06's original release-gates clause was split out into a new E-07. Not an
orchestrator.

Measurements:

- Executed `c6f6sj`: `aw ipd lint --phase post-transition --detail` gives `conforming`. All five V-items
  are `Result: pass`. The file contains ZERO occurrences of the three parity file names. Its only suite
  baseline is the count `3512 passed, 2 skipped` at `ec857565a`, with no failure-id set. Its execution
  commit is `4d4966695` (trailer `AW-Item: c6f6sj`), integrated by merges `ce551c597` and `5041ef8bc`.
- All three retrospective parity files exist at `4d4966695~1`, and `TestGateFieldClearingOnStatusChange`
  is present there.
- `afdmn6` (`reviewed`, pending): its E-04 records "six at review: (a), (b), (d), (e), (f), (g)" DIFFER
  out of eight candidates. `tests/test_set_dispatch_parity.py` does not exist yet.
- `h4fiwa` and `fv4b6s` are both `graduated`, `Blocks-Release: next`, with carriers `wdyz5n` (approved,
  pending) and `ju3rhs` (executed).
- `m1jlwm`, `m94eht` and `vhiqo6` are all `reviewed` and pending. After their reviews none of them closes a
  carrier itself.
- `AW_NO_REEXEC=1 python3 -m agent_workflows check release-gates --agent` gives `conforms`, 0 findings.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (unreachable evidence) | E-05 "From each child's own pasted evidence"; executed `c6f6sj` names none of the three files | The per-child parity record cannot be quoted for at least one child, so V-05 could not be met honestly. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now measures each child at its own execution commit in a scratch worktree, quotes evidence where it exists, and uses two date-skewed zones for the current runs. |
| PR-002 | HIGH | IN-SCOPE | E (unreachable evidence) | E-06 "the baseline the first child recorded"; `c6f6sj` F-03 is a count only | No pre-Set failure set exists to compare against by id. | Overall:Low | FIXED | E-06 now re-derives the baseline with `-rf` at `4d4966695~1` in a scratch worktree, under the same `TZ` as the current run. |
| PR-003 | MEDIUM | IN-SCOPE | Evidence (stale premise) | E-02 "eight expected-difference assertions"; `afdmn6` E-04 "six at review" | The plan hardcoded eight flips, while the harness records six DIFFER axes plus two agreements. A fix may also come from outside the Set (`wdyz5n`). | Overall:Low | FIXED | E-02 now reads the classification from `afdmn6`'s V-04, allows a named non-Set flipping plan, and runs the final harness. The Concern wording is corrected. |
| PR-004 | MEDIUM | IN-SCOPE | Release-gate rules | E-03 "closed ... through the evidence route"; `h4fiwa`/`fv4b6s` graduated to `wdyz5n`/`ju3rhs` | The carriers close by HANDOFF, and `vhiqo6`/`m1jlwm` close nothing after review, so the check as written would report a false failure. | Overall:Low | FIXED | E-03 now discovers closes from git history across the Set window, accepts HANDOFF or SATISFIED, reports a still-`graduated` item without fixing it, and confirms the clock items were untouched. |
| PR-005 | LOW | IN-SCOPE | G (executability / contract) | E-04 grep for "reads of `agent_workflows/*.py`" with no file list; E-06 bundled release gates; gate lacked failure disposition and scope-fence wording | The source-read check had no way to enumerate "added tests", and the gate did not say what a failure does to the plan. | Overall:Low | FIXED | E-04 now enumerates added tests by `--diff-filter=A` and judges each hit. Release gates moved to new E-07/V-07. The gate now states a failure leaves the plan in `pending/` with `Result: failed`, uses declaration-style scope-fence wording, and forbids a hand `git mv`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where does the pre-Set baseline come from? | Re-derive at `4d4966695~1` in a scratch worktree. | Use `c6f6sj`'s count. Rejected because a count cannot be compared by id. | `c6f6sj` F-03; `63zo2f` E-06 cross-check. | yes |
| D-2 | Keep `IPD-Z602` on E-06 as advisory? | Keep it, as a single concern. | Split the baseline and current runs. Rejected because they are two halves of one comparison. | Linter advisory text; right-sizing rule. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
