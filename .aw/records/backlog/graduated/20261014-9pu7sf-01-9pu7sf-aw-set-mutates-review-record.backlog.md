- Id: 9pu7sf
- Status: graduated
- Graduated-To: 9pu7sf
- Blocks-Release: next
- Set: 9pu7sf
- Priority: medium
- Work-Kind: bug
- Summary: aw set <status> on a .review.md record classifies it as type other and writes a Status line and workflow history into a review, which has no lifecycle

## Workflow history
- 2026-10-16 graduated (aw backlog): graduated by run run-20261016T145446Z-2140972: p4xo1u
- 2026-10-15 created (aw backlog): aw set <status> on a .review.md record classifies it as type other and writes a Status line and workflow history into a review, which has no lifecycle

MEASURED 2026-10-15 at /plan-review of ybf6za (lane HEAD c43b16f7c), in a temp git repo holding only .aw/records/reviews/20260929-demo-01-ab12cd-x.review.md (content '# Review: x', '- Subject-Id: ab12cd'): `aw set approved <that path> --dry-run` exits 0 and prints 'other 20260929-demo-01-ab12cd draft -> ? approved (dry-run)'; WITHOUT --dry-run (with --no-commit) it exits 0 and REWRITES the review, inserting '- Status: approved' and a '## Workflow history' line 'approved (aw set): status set to approved'. The agent_workflows/artifact_types.py module docstring says reviews has no status lifecycle and 'stays out of selectors.KNOWN_PRIMARY_TYPES and out of aw set', so the aw-set half of that claim is false today. Likely root: status_set.detect_artifact_type falls through to 'other' for a reviews-tree path. Expected: refuse at exit 2 naming reviews as a type with no status lifecycle, leaving the file byte-identical. Related: nrcvpg, ybf6za (which guards only the TYPE_BACKENDS and KNOWN_PRIMARY_TYPES halves).
