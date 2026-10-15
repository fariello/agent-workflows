# Review findings: plan 3392n9

- Subject-Id: 3392n9
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`d4cd4a6c2`), so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before the semantic review, and `--phase review-finalize` was conforming after the revisions.

Re-measured at review (the probes were placed under the gitignored `.aw/state/` and then deleted):
- `evaluate_carrier_obligation` returns `SATISFIED` for a live pending plan and for a live approved spec, and `evaluate_blocking_close` on `7lfe87` citing an approved spec returns `SATISFIED`. F-01 and F-02 hold.
- The `- Carrier-Evidence:` census found 241 bullets in `executed/`, 5 in `not-executed/`, 3 in `superseded/` and 5 in `pending/`. One pending row (`9380pe` deferred row 1) cites the PENDING plan `ww744p` alongside `- Carrier: ww744p`, and `carrier_severity_for_plan` for that plan is `error`.
- With the evidence field stripped, the same row returns `HANDOFF`.
- The `Close-Evidence:` census found 48 executed-plan rows and 4 other rows, with no spec citations.
- The current `aw check plans` count of `check.ipd-uncarried-obligation` is 31, not the authored 1.
- No spec on disk has a directory that disagrees with its `- Status:`.
- The longest live plan or spec path is 136 characters.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / D. Anti-regression | `.aw/records/plans/pending/20261014-uu4rfe-01-9380pe-...ipd.md` deferred row 1 (`- Carrier: ww744p` and `- Carrier-Evidence: .aw/records/plans/pending/20261011-x31lcm-01-ww744p-...`); `check_engine.evaluate_carrier_obligation` evidence arm returns before the `raw_carrier` arm | The census missed this live row. Under the plan as written, it would become a new error-severity `check.ipd-uncarried-obligation` on a plan whose handoff is legitimate. That contradicts F-05 ("zero new findings") and the E-06/E-07 bar. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added F-08. E-04 now falls through to the `HANDOFF` arm when `- Carrier:` is present, and refuses only when it is absent. E-02 tests both branches, and V-04 and V-07 demand the `9380pe` row resolves `HANDOFF`. OQ-01 point 4 and DECISIONS point 3 record the decision. |
| PR-002 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | F-05 and F-06 counts; `aw check plans --agent` at review reports `check.ipd-uncarried-obligation`: 31 | E-07 and V-06 compared against fixed authoring-time counts that had already drifted (1 became 31). The census itself was stale: 6 pending rows had become 5, and `6jp1ox` has since executed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now captures a per-rule count and `(plan path, rule)` baseline at execution, and E-07 and V-07 compare against that. F-05 and F-06 are relabeled as context and F-05 is corrected. |
| PR-003 | MEDIUM | UNDER-SCOPE | G. Right-sizing | old E-03 (two predicates, a helper, and four docstring sites); old E-02 (a single 2300-character line) | E-03 bundled two independent predicate changes, each with its own test surface. E-02 was unreadable as one line. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-03 (helper plus `evaluate_blocking_close`) and E-04 (`evaluate_carrier_obligation` plus prose), with V-03 and V-04 to match. E-02 and E-06 are broken into sub-bullets. Items renumbered to E-07 and V-07, and the bijection lints. |
| PR-004 | LOW | IN-SCOPE | E. Verification (bound) | `check_engine._deferred_section_obligations` locator `deferred row <n>`; F-07 cited the locator `Deferred / out of scope [1]:` | The locator format in F-07 was wrong, and the bound was argued from a 115-character path rather than the measured 136-character maximum, which leaves about 10 characters of headroom on the spec reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07 is corrected. E-02 pins the bound with a 136-character path for both reasons, and E-04 keeps the reason text exact. |
| PR-005 | LOW | IN-SCOPE | E. Verification feasibility | old V-04 `rg -c "[\u2013\u2014]"` | `rg` does not interpret `\u` escapes, so the command would not test for the dashes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 now uses `grep -c -P '[\x{2013}\x{2014}]'` and checks the hunk headers against the `<!-- /aw:block -->` line. |
| PR-006 | LOW | IN-SCOPE | E. Testing coverage | E-02 mismatch case | The directory-versus-status mismatch was tested in one direction only. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now tests both directions. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; `- Scope-Paths:` | The gate lacked the approval and `aw ipd begin` instruction, the hard-MUST honesty wording, never-tag, and the per-V `pass` precondition for finalize. Scope-Paths omitted the plan file itself. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All of these are added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What happens to an unshipped `Carrier-Evidence:` on a row that also names a valid `- Carrier:`? | Fall through to the `HANDOFF` arm and judge the row on its carrier | Refuse (creates a new error on `9380pe`); edit `9380pe` (out of scope, and another author's live plan) | Review probe: the stripped row returns `HANDOFF` (`handed off to carrier ww744p`); `check_engine.evaluate_carrier_obligation` arm order | yes |
| D-2 | Keep the authored F-06 counts as the E-07 bar? | No: re-capture the baseline in E-01 at execution | Use the authored counts (already stale) | plan-review rubric G live-artifact convention; measured 31 versus 1 | yes |
| D-3 | Accept OQ-01 points 1 to 3 (executed-plan rule, implemented-spec rule, no cutover) as resolved? | Yes, as authored, plus point 4 | Reopen as a maintainer question | `check_engine._carrier_is_executed`; `_CARRIER_TARGET_TYPES = ("backlog", "plans")`; `check_durable_carrier` pending-only sweep | yes |
