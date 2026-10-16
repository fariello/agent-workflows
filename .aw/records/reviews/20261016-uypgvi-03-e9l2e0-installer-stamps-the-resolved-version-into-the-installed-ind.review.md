# Review findings: plan e9l2e0

- Subject-Id: e9l2e0
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `b551549b9`. The plan was committed and byte-identical to the lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean`. The plan is a child, not an orchestrator.

Verified:
- `engine._member_source_bytes` returns `source_path.read_bytes()` for every member except `VERSION_FILE`; both `engine.install_all` and `engine.show_install_diffs` call it (F-02 holds; E-03's "show_install_diffs needs no edit" holds).
- `git grep -n "WORKFLOWS-VERSION" -- agent_workflows tests` matches only `release_readiness.py` and `tests/test_release_readiness_producers.py` fixtures; no match under `.aw/records/specs/` (F-04, F-06, spec-sync hold).
- `git show v1.3.0-rc.1:.agents/workflows/VERSION` is `1.2.1` (F-05 counterexample holds).
- Reproduction in a gitignored scratch dir: installed VERSION `1.3.0rc2.dev11020+gb551549b9`, `index.md` lines 3-4 `1.2.1`, `gate_artifact_manifest` `False ['version stamp mismatch: ...']` (F-01 holds at HEAD).
- Fix sufficiency probe (synthetic `v7.3.0` source, `_member_source_bytes` patched by `mock` to rewrite both stamps): gate `True []`; a second install reported no `index.md` written. Recorded as F-07.
- Release-readiness test files named in E-05(1) exist. Backlog `7rs77x` carries no `Blocks-Release`; `followup` classification condition reasoned in F-05 matches the item text.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric E (unsatisfiable evidence) | `tests/test_installer.py:3673` `ResolvedVersionStampTests.MANIFEST_ROW` names `.agents/workflows/plan-review/plan-review.md`; `release_readiness.gate_artifact_manifest` "missing {field_name} file"; review probe printed `False ['plan-review: missing body file: ...', 'version stamp mismatch: ...']` | E-02 told the executor to model the fixture on `ResolvedVersionStampTests`, whose legacy body path makes `gate_artifact_manifest` fail regardless of the fix, so case (2) `passed is True` was unreachable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires the `.aw/system/workflows/...` body row, with the measured reason; V-02 requires (2)'s RED to show only the stamp mismatch. F-07 records the probe. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric E (RED expectation) | E-02 case (3) idempotence; `engine.write_file` `same_bytes` short-circuit "[already current]" | V-02 expected case (3) to fail on the unmodified engine, but a verbatim copy is already idempotent, so (3) passes pre-fix; an executor would be unable to produce the demanded RED. | all Low | FIXED | E-02 and V-02 now state only (1) and (2) are RED; (3)-(5) are regression guards that pass pre-fix. |
| PR-003 | LOW | IN-SCOPE | Rubric A (consumer parity) | `Makefile` `version-file` `r'<!-- WORKFLOWS-VERSION: [^>]*-->'`; `release_readiness.gate_artifact_manifest` `r"<!--\s*WORKFLOWS-VERSION:\s*([^\s>]+)\s*-->"` and `(?m)^Version:\s*` | E-03 prescribed the Makefile's single-space patterns, which miss stamp spellings the gate still reads, leaving a residual mismatch path. | all Low | FIXED | E-03 now matches with the gate's whitespace-tolerant patterns and writes the Makefile's canonical form (D-1). |
| PR-004 | LOW | IN-SCOPE | Rubric G (ambiguity) | `CHANGELOG.md:7` `## 2.0.0 (pending)` and `CHANGELOG.md:224` `## 1.3.0 (pending)`; existing `artifact_manifest` bullet at `CHANGELOG.md:40` | "the current pending section" is ambiguous with two pending sections. | all Low | FIXED | E-04 names `## 2.0.0 (pending)`; V-04 requires the hunk to land there. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which regex should the installer use to find the stamps? | Match with the consumer's whitespace-tolerant patterns; write the Makefile's canonical form. | Reuse the Makefile's exact patterns (REJECTED: a stamp the gate reads could escape the rewrite). | `agent_workflows/release_readiness.py:686-689` `gate_artifact_manifest` regexes; `Makefile` `version-file` target. | yes |
