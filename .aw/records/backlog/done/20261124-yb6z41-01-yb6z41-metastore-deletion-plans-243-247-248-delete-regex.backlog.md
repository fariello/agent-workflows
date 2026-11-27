- Id: yb6z41
- Status: done
- Set: yb6z41
- Work-Kind: followup
- Priority: high
- Summary: Metastore deletion plans 243, 247, 248 delete regex symbols that callers outside their Scope-Paths still use, e.g. attention reads releases._VERSION_RE inside a try block, so deleting it silently drops the release version (found by 786w7r)
- Short-Description: Metastore deletion plans 243, 247, 248 delete regex symbols that callers outside their Scope-Paths still use, e.g. attention reads releases._VERSION_RE inside a try block, so deleting it silently drops the release version (found by 786w7r)

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 done (aw set): Obsolete: deletion plans kmf6w4 (243), akhrp5 (247), and tdhav3 (248) all executed cleanly.
- 2026-11-24 created (aw backlog): Metastore deletion plans 243, 247, 248 delete regex symbols that callers outside their Scope-Paths still use, e.g. attention reads releases._VERSION_RE inside a try block, so deleting it silently drops the release version (found by 786w7r)

Measured 2026-11-24 at 56e9d649f by 786w7r. (1) Order 243 kmf6w4 deletes releases._VERSION_RE; attention.py calls _releases._VERSION_RE.search inside try/except, and attention.py is not in kmf6w4 Scope-Paths, so the deletion would surface as a silent missing version instead of an error. (2) Order 248 tdhav3 deletes attention_contract.HISTORY_RECORD_RE, imported by plan_readiness.py and ipd_lifecycle.py (outside its Scope-Paths), and GATE_SUMMARY_RE, used by tests/test_attention_contract.py. (3) Order 247 akhrp5 deletes plan_readiness._READINESS_FIELD_PRESENT_RE and _READINESS_LINE_SUB_RE, used by tests/test_readiness_absence_invariant.py and tests/test_plan_readiness_recheck.py. Recorded in 786w7r F-26/F-27 notes. Fix: each executor retargets those callers with --scope-reason, or the plans gain the paths.
