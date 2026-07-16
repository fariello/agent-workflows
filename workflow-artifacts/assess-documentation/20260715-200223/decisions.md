# Assess documentation - decisions and assumptions

- Concern/scope: documentation lens, CHANGELOG + version-scoping PRIMARY, full authored-docs surface
  SECONDARY. The framework itself is the subject (maintainer instruction), so the repo's own docs are
  assessed as the product rather than excluded as "framework tooling".
- Method: two parallel read-only audit lanes (dogfooding D84 auto-parallel convention, first real use):
  lane 1 = CHANGELOG/versioning/DECISIONS reconciliation; lane 2 = broader docs accuracy. Coordinator
  synthesized, deduped, and independently re-verified the two HIGH findings (F1 CHANGELOG mis-scoping,
  F2 TODO "on trial") against source before writing the IPD.
- Version-scoping treated as a RECOMMENDATION (not a unilateral decision): the assess recommends the
  1.2.1(patch)/1.3.0(feature) split; the human confirms at approval, or defers to release-review Section 8
  which formally owns release scoping (maintainer's earlier choice).
- Intentionally NOT proposed: any versioning-mechanism change, any release cut/tag/push, building the
  `aw comms` helper, and the STATUS.md track-vs-ignore policy question (surfaced to the maintainer only).
  None of these were dropped on Remediation Risk; they are out of the documentation concern's scope.
- Assumption: STATUS.md and the AGENTS block are GENERATED artifacts; the IPD proposes REGENERATING them
  (`aw plans --write-index`, `aw install .`), never hand-editing.
- Open questions for the user: (1) accept the re-scope now vs defer to release-review; (2) F1c bucket-line
  bucket; (3) F5 pointer depth. Leans recorded in the IPD.
