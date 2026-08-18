- Id: 047ce9
- Status: blocked
- Set: awretrofit
- Priority: high
- Kind: chore
- Summary: RELEASE BLOCKER: uniform artifact-naming grammar (.type.md suffix, one grammar for all record types) before release
- Gate-Kind: artifact
- Gate-Ref: .aw/records/docs/specs/20260817-2147-01-uniform-artifact-naming-grammar.spec.md

## Workflow history
- 2026-08-17 created (aw backlog): RELEASE BLOCKER: uniform artifact-naming grammar (.type.md suffix, one grammar for all record types) before release

Pre-release naming-contract change; MUST block the release (spec 20260817-2147-01, maintainer-confirmed). Move the TYPE signal into filenames (.ipd.md/.prompt.md/.spec.md/.walkthrough.md/.roadmap.md/.backlog.md/.comms.md; research keeps .<model>.<kind>.md). Sequenced AFTER the directory-taxonomy Order 07. Folds vf03z3 tooling gaps. Gated on the spec approved+implemented.
