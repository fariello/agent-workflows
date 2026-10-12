# Review findings: plan 6iab2o

- Subject-Id: 6iab2o
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `a60a58038` in an isolated review lane. The plan was committed and unchanged (`63a948918`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` was re-run after revisions.

Re-verified:
- Consumers of `attention._history_section_lines` in production: the six `attention` `_*_record` builders (`A.last_history_at(_history_section_lines(text))`), `check_engine._item_close_date`, `_item_graduated_date`, `_spec_implementing_date`, `plan_readiness.extract_newest_history_entry`, `history_has_review_record`, `newest_verdict`, and `status_set.same_status_message_is_duplicate` (owned by `kgv213`). Matches F-01.
- Prerequisite: `kgv213` is `reviewed` in `plans/pending/` (not executed) and `attention_contract.history_block` does not exist at this HEAD. Its plan specifies `history_block(text) -> HistoryBlock(records, record_lines, body)` with records rstripped and at column zero, which is what this plan consumes.
- `plan_readiness` imports `_history_section_lines` from `attention`; no test patches `plan_readiness._history_section_lines`.
- Corpus: dropping indented lines from `plan_readiness`'s input changes 0 of the three readers' answers over 2516 tracked artifacts with a history heading.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | B. Security (attestation gate) / E. Testing | `plan_readiness.is_plan_review_approved` (`if not history_has_review_record(text): return False`); `plan_readiness.history_has_review_record` / `newest_verdict` iterate `line.strip()` over `_history_section_lines` | The plan treats the migration as answer-preserving tidy-up. It did not see that the loose rule lets a QUOTED indented review line ATTEST a hand-written `- Readiness:` field. Review probe: a plan whose only real record is `to-review`, with an indented quoted `/plan-review ... APPROVE` line after a prose paragraph, returns `history_has_review_record: True`, `newest_verdict: positive`, and `is_plan_review_approved: True`. That is the forged-attestation path the gate exists to refuse, and it gates `--full-auto` promotion. The planned tests (E-05 (a)) did not fence it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-04. E-05 (a) is now the gate case asserting all three refuse after migration and FAIL at the base sha. V-04 and V-05 demand that evidence. The CHANGELOG line names the effect. |
| PR-002 | MEDIUM | IN-SCOPE | Evidence / E. Testing | `check_engine._item_close_date` / `_item_graduated_date` / `_spec_implementing_date` match `^- ` on RAW lines | E-05 (b) asserted `_item_close_date` returns None for an indented-only item, which it ALREADY does at base, so that assertion proves nothing. The real change for these readers is a column-zero record after a column-zero prose line, which the heading bound keeps and the canonical rule drops. | all Low | FIXED | Added F-05. E-05 (b2) covers that shape for all three date readers and must fail at the base sha. |
| PR-003 | MEDIUM | IN-SCOPE | G. Prerequisite / evidence | `kgv213` `- Status: reviewed` in `pending/`; `history_block` absent | E-01's prerequisite check named only `history_block`, not where `kgv213` sits. "Mark blocked" carried no paste requirement. | all Low | FIXED | E-01 checks both, records the review-time state, and V-01 demands the pasted check. |
| PR-004 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | E-01 / V-04 "2489 tracked artifacts", "zero differing answers" | A live corpus count and an exact-zero diff were the bar. The plan's own F-03 allows that some artifacts could legitimately change. | all Low | FIXED | The artifact set is re-derived at execution. V-04's bar is now "every difference listed and justified", with zero noted as measured context. The attention JSON baseline is now saved in E-01 so V-02's before/after diff is producible. |
| PR-005 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Missing: OQ status, the scope-as-declaration wording, `aw ipd begin`, the staged-set check, the never-`--no-verify` rule, and the executor-must-not-finalize-under-a-runner rule. The text said "manually, run `aw ipd finalize ... --apply`" without the pre-transition condition. | all Low | FIXED | Gate rewritten. |
| PR-006 | LOW | IN-SCOPE | Open questions | OQ-01 `- Owner: none` | The resolved question named no owner. | all Low | FIXED | Owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does F-04 require reclassifying this plan as `Work-Kind: bug` (which would add a mandatory `Blocks-Release`)? | No; keep the backlog item's `chore` classification and record the hole in F-04 | Reclassify to `bug` + `Blocks-Release: next` (a release-scope decision the maintainer owns) | Zero tracked plans reach the hole (2516-artifact probe); the hole needs a hand-written Readiness field plus a crafted quotation; AGENTS.md: work-kind is the filer's recorded judgement; the maintainer is told in the review report | yes |
| D-2 | What is the bar for "answer-preserving"? | Every difference listed and justified (F-03/F-05 shapes), zero measured as context | Exact zero (would fail on a legitimately corrected artifact) | plan-review G live-artifact convention; F-03 | yes |
