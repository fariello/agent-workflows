- Id: s6zc2f
- Status: open
- Set: specaudit
- Priority: medium
- Work-Kind: feature
- Summary: Amend spec w15vzb: verify role already routes a model, verdict store exists; finish R-6b and R-8

## Workflow history
- 2026-10-25 created (aw backlog): Filed 2026-10-25 from the spec audit (session report).

Audit 2026-10-25 at HEAD 5db4791c1. Drift: A-12 and Section 6 say a populated role map routes no model; false for verify (resolve() returns verify_with from roles.verify, provenance role-map, and oc_runipd.py ~1885 launches the verifier on it). Section 4.5 says the verdict store does not exist; coverage_record.py now provides it, and R-7 holds in practice (fingerprint is content-only, model recorded) but has no test for retention across a preference change. Open: R-6b (model unavailable at launch: warn, fall back, record; no code, plan 1u4olp declined A-8) and R-8 (schema bump to 3 with the first consumer; SCHEMA_VERSION is still 2, and docs/runner-profiles.md never mentions roles). OC-only; set_role has no CLI caller.
