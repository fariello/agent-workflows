# Review findings: plan l5t4vx

- Subject-Id: l5t4vx
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `f371fbe11`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` (advisory `IPD-Z602`);
after revisions `--phase review-finalize`: `clean` (advisory `IPD-Z602` x3, justified in the gate).
Not an orchestrator.

Re-derived at review HEAD (all HELD):
- F-1: `parse_aw_block(AGENTS.md)` pointer `bc256612`, reporting `46970f75`, equal to
  `agents_managed_sections("aw")`; recorded `0fbbebcf` / `2ab6fbfb`. Only three `#` keys exist in the
  manifest (`.gitignore#aw:untracked`, the two `AGENTS.md#aw:*`); no decline tombstones.
- F-2: perturbing each section against the live manifest: `pointer False 1`, `reporting False 1`.
- F-4: `merge_aw_block` with the current generator on a temp copy of the manifest, then `manifest.save`:
  `diff` moves exactly the two `sha256` lines; result text equals `AGENTS.md`. `tests/test_section_consent.py`
  `12 passed in 4.57s`. `merge_aw_block(AGENTS.md, desired, manifest=None)` is byte-identical to disk.
- `engine.resolve_target_layout`, `resolve_agents_file`, `manifest.resolve_manifest_path` resolve to
  `aw`, `AGENTS.md`, `.aw/system/managed-sections.json` in the repo and in a synthesized temp repo.
- `b4bvas` Deferred row "A guard test that this repo's `AGENTS.md` pointer body equals ..." with
  Carrier-Declined citing F-7 exists as cited (F-5). `DECISIONS.md` highest is `D174`. `CONTRIBUTING.md`
  `### Regenerating Derivative Artifacts` and the `**Generated**` classification row exist; `tools/` has
  no `__init__.py` and `python3 -m tools.mutation_probe --help` works (namespace import).
- Backlog `q3ogs0` is `graduated` with `Blocks-Release: next`; the plan inherits it. Release `f33nrj` is
  `planned`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric A/D (data loss in the tool) | `engine.parse_aw_block` EOF-close branch (`drift = True`, `after` empty); `engine._apply_section_consent` iterates only `desired`; review probes: a block with no closer followed by foreign text -> `refreshed`, `"keep me" in out` False; a block with an extra `<!-- aw:extra -->` section -> `refreshed`, `"mine" in out` False | E-02's `manifest=None` rewrite refuses only `not found`/`ambiguous`. A missing closer silently deletes all foreign text after the block (in this repo, the whole repo-local section below `<!-- /aw:block -->`); an unknown on-disk section is silently dropped; a legacy marker converts/appends; a declined section would be resurrected. That is exactly the "changes `AGENTS.md` outside the markers" hazard stop condition 1 names, with no guard. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 refuses (exit 2, nothing written) on drift, legacy markers, unknown slugs, and declined keys; E-01 (d) gains one parametrized refusal case per condition. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric E (failing-first ordering) | E-01 expected outcome "(a) FAILS ... (b)-(d) fail with an import error" | A top-level `from tools.regen_agents_block import ...` fails collection of the whole module, so (a) would error at import rather than fail with the case-3 warning V-01 demands. | all Low | FIXED | E-01 requires the import inside the synthesized tests/fixture. |
| PR-003 | MEDIUM | UNDER-SCOPE | Rubric G/E (unspecified contract, untested CLI) | E-02 return shape `{"file","text_changed","records_changed"}`; E-01 (c) "returns a nonzero/'stale' result"; exit codes 0/1/2 in E-02 | The return dict had no `stale`/`refused` field for `check=True` to report, "nonzero/stale" was ambiguous, how to detect a changed record was unspecified, and the 0/1/2 exit codes E-03 relies on had no test. | all Low | FIXED | Return shape gains `stale` and `refused`; record change measured via `recorded_hash` before/after; `check=True` writes nothing (asserted by bytes); new case (e) drives `main` for 1, 0, 2; the tool prints slugs whose body it rewrote. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric E / P16 (code-pinning evidence) | V-02 "`grep -n \"update_agents_pointer\\|hash_content\\|\\.record(\" tools/regen_agents_block.py` returning nothing"; AGENTS.md "NEVER write or restore tests that read production source code using ... regex, or substring search" | V-02 proved a property by searching source text, which the repo's no-code-pinning rule forbids. The behavior it stood for is already observable. | all Low | FIXED | V-02 now demands the behavioral proof from case (b) and (d): `GEMINI.md` and the unrelated entry are unchanged, recorded hashes equal on-disk bodies, refusals write nothing. |
| PR-005 | LOW | IN-SCOPE | Rubric E (testability of guard mutation check / foreign-text assertion) | Required tests "show case (a)'s helper reports the failure"; E-01 (a) defined no helper; `merge_aw_block` rejoins pieces with `"\n\n"` | The mutation check named a helper E-01 never defined; case (c)'s "foreign text byte-identical" fails on the normalized blank-line separators. | all Low | FIXED | E-01 (a) defines `stale_section_keys(agents_text, manifest_obj)`; (c) compares `parse_aw_block(...).before/.after` stripped of separator newlines. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the tool refuse unsafe shapes, or call `merge_aw_block` with the real manifest so consent preserves them? | Refuse with exit 2 and write nothing | Pass the manifest to the rewrite (then a stale record holds the region back, which is the defect); silently proceed (data loss measured above) | `engine._apply_section_consent` case 3 warning; review probes in PR-001 | yes |
| D-2 | Keep OQ-01 (core tier for the live guard) as resolved by the author? | Keep core | `livecorpus` deselection | Author's rationale holds: only the lane editing the generator or managed region can turn it red, and the message names the one-command fix; `CONTRIBUTING.md` `### When tests depend on the live checkout or environment` | yes |
