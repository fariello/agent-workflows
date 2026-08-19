# .aw/records/releases/

Release records: thin ship-gate anchors. A release record (`<...>.release.md`) names a planned release
(Version or `next`), its Status (planned/blocked/shipped), and a Summary. Items declare they gate a
release via a `Blocks-Release:` field (see AGENTS.md). This is a COMMITTED ship gate, distinct from
roadmaps (possibilities).

Named by the uniform artifact-naming grammar with the release facet:
`YYYYMMDD-<setid>-NN-<id6>-<slug>.release.md` (a standalone release uses its id6 as the setid, NN=01).

Managed by `aw` (do not hand-edit status/history; use the aw verbs).
