- Id: rsisop
- Status: graduated
- Graduated-To: quickpipe
- Set: revsteps
- Priority: medium
- Work-Kind: feature
- Summary: Shorter pipeline for small changes: go from plan to review to execution without the backlog draft/open/graduate steps

## Workflow history
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T175028Z-1384849: e41qgx
- 2026-10-19 created (aw backlog): Shorter pipeline for small changes: go from plan to review to execution without the backlog draft/open/graduate steps

Maintainer observation 2026-10-17: many plans are 1 to 4 line fixes or one new CLI option, yet each goes through backlog draft, open, graduate, plan draft, to-review, reviewed, approved, executed. Spec k3yx72 makes the review cheap for such plans (simple tier); this item covers the rest of the pipeline. Needs its own spec: which changes qualify, who decides, and which records are still written.
