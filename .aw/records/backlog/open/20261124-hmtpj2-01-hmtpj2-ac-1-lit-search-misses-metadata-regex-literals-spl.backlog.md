- Id: hmtpj2
- Status: open
- Set: hmtpj2
- Work-Kind: followup
- Priority: medium
- Summary: AC-1 LIT search misses ^- metadata regex literals split across two lines or flagged (?mi)/(?i); no metastore deletion plan owns them and 9o83cr E-14 would not see them (found by 786w7r)
- Short-Description: AC-1 LIT search misses ^- metadata regex literals split across two lines or flagged (?mi)/(?i); no metastore deletion plan owns them and 9o83cr E-14 would not see them (found by 786w7r)

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-24 created (aw backlog): AC-1 LIT search misses ^- metadata regex literals split across two lines or flagged (?mi)/(?i); no metastore deletion plan owns them and 9o83cr E-14 would not see them (found by 786w7r)

Measured 2026-11-24 at 56e9d649f by 786w7r. Unowned literals the one-line LIT search misses: check_engine._REVIEW_SUBJECT_ID_RE, check_engine._GRADUATED_LINE_RE, check_engine._IMPLEMENTING_LINE_RE, coverage_record._FINGERPRINT_LINE_RE, coverage_record._CHECKED_LINE_RE, attention._FIELD_PATTERNS (Summary/Scope/Concern/Question/Title, flagged (?mi)), ipd_lint._HISTORY_ATTRIB_RE, ipd_lint._COVERAGE_HIST_RE, plan_readiness._HISTORY_RECORD_PARTS_RE, review_findings._OQ_FINDING_REF_RE. Some are history-record or OQ-row grammar (body prose, N3); _REVIEW_SUBJECT_ID_RE, the coverage fingerprint lines and attention._FIELD_PATTERNS read front-matter metadata. Fix: widen the AC-1 search (rg -U, any inline flag group) in 9o83cr E-14 and assign each hit an owner.
