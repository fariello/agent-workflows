- Id: l90ejs
- Status: open
- Set: rk25gap
- Priority: medium
- Work-Kind: feature
- Summary: Bind or retire the unbound finding codes in spec 25kzda 4.2-4.12

## Workflow history
- 2026-10-25 created (aw backlog): Filed 2026-10-25 from the spec audit of 25kzda (maintainer ruling: ungate the spec, file the unbuilt pieces as items).

Spec 25kzda Section 4 names 58 deterministic finding codes. Audit 2026-10-25 at HEAD 5db4791c1: 17 appear in code. By family: RUN 10/12 (RUN-COMMIT-CONTENTS, RUN-COMMIT-GATEWAY unbound), BACKLOG 6/6, SPEC 6/14 (the implementing->implemented SPEC-LINKED-PLANS/SPEC-CHILD-OUTCOMES/SPEC-IMPLEMENTED-* checks are not built; the runner action for an implementing spec is 'undetermined'), IPD-EXEC 3/11 (comments only), IPD-REVIEW 1/7, and 0 for IPD-DEP, IPD-REUSE, PROMPT, NONRUN and the approval codes. Decide per family: bind the code to its shipped enforcer, build the missing check, or amend the spec to cite the enforcer instead. Also resolve the 7 open items in 25kzda 6.2 or move them to their owners.
