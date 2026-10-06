# Review findings: plan dalmk4

- Subject-Id: dalmk4
- Subject-Type: ipd
- Reviewed-At: 2026-10-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (HIGH, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in lane `review-sweep-run-20261006T040814Z-944` at HEAD `b9622119b`. The plan was committed and byte-identical
to the sealed lane input (rev-12); no snapshot needed. `- Kind: child`, so `IPD-S407` does not apply. `aw ipd lint --phase
author` clean before; `review-finalize` conforming after (one default-quiet `IPD-Z602` size-density advisory). Orders 00
to 07 and 13 are `reviewed`; none executed.

Re-measured: `runner_shared.build_backlog_production_prompt` / `build_spec_production_prompt` (seven-item Production
Contract then Prohibitions); `ipd_authoring._SECTION_BODY` (keyed by heading, read by `build_skeleton` for both kinds),
`_AUTHORING_PLACEHOLDERS`, `authoring_placeholders_resolved` (exact substrings); `tests/test_ipd_templates.py`
byte-parity of `.aw/system/workflows/assess/templates/orchestrator-ipd.md` with `build_skeleton`; `engine.py` managed
block (step (5), the coverage-gate paragraph, the "verdict is CACHED" sentence); `engine.merge_aw_block`,
`engine._apply_section_consent`, `manifest.load`/`save`; `aw install . --dry-run` (target delta spans `.aw/system/`,
`.aw/config/`, `.aw/state/`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G sequencing | `- Item-Dependencies: executed:26m1nb`; E-03 text describes `5etev3` (may RETIRE scope), `r2wa38` (graduation handoff gate), `sbiv1j` (`aw backlog set graduated` refuses) | The plan depends only on Order 05 but writes AGENTS.md sentences asserting Order 04, 06 and 10 behavior; executed earlier, the installed contract would state false facts. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `executed:5etev3, executed:r2wa38, executed:sbiv1j`; gate names them and a STOP if `aw ipd coverage` is absent. Orchestrator `1f4faf` table row/E-11 depends-on are recorded as a cross-plan note (no edit: `1f4faf` is reviewed; the runner reads this plan's `Item-Dependencies`). |
| PR-002 | HIGH | UNDER-SCOPE | A correctness | `.aw/system/managed-sections.json` pointer hash `b8a499df...` vs on-disk `258b6c16...`; `_apply_section_consent` case (3); simulated edit merge returned `refreshed` with old text and a "manual modifications" warning | E-03's "installer refresh" would silently keep the old managed section (or, without the manifest, leave the record stale so the next regeneration is refused). `aw install .` also writes far beyond scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now drives `merge_aw_block` with the manifest: a self-heal pass before the edit (demonstrated: case (1) re-records, second merge applies with no warning), explicit `warnings=` list, STOP on a warning; manifest added to Scope-Paths, diff limited to the pointer hash. |
| PR-003 | HIGH | UNDER-SCOPE | E regression | `tests/test_ipd_templates.py` `test_orchestrator_template_matches_generator` | Changing `_SECTION_BODY` without regenerating the orchestrator template fails the suite; the template was not in scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 regenerates the template with the test's exact arguments; path added to Scope-Paths; `test_ipd_templates.py` in the targeted run. |
| PR-004 | HIGH | IN-SCOPE | A correctness | `authoring_placeholders_resolved` matches listed substrings; probe: all listed markers replaced, three orchestrator placeholders left, returned True | E-02's "detectable by the `TODO:` prefix" is false; a stub orchestrator would be nudged/promoted by `check.ipd-draft-ready-to-review` and `action_for`. Also `_SECTION_BODY` has no per-kind entry, so "orchestrator kind only" had no mechanism. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 adds the three markers to `_AUTHORING_PLACEHOLDERS` and an `_ORCH_SECTION_BODY` override; E-05 adds a one-placeholder-left case and a second mutation. |
| PR-005 | MEDIUM | IN-SCOPE | F UX | E-01 item (4); `qs00nc` E-03; `r2wa38` E-02 | The prompt told the agent to run `aw ipd coverage` without saying it records into the plan or that the runner re-checks the Set after the turn; placement and drift between the two builders and Order 08's added section unspecified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Item (4) states both; one shared tuple; placed before `## Prohibitions`, located by heading. |
| PR-006 | MEDIUM | IN-SCOPE | A consistency | `8mabmu` Goal and `hm1h3l` A.4 (credit by id6 or Order number); `8mabmu` E-07 retires the cache | The named-child sentence credited id6 only, contradicting the probe's rule; the "verdict is CACHED" sentence becomes false once Order 02 lands and was untouched. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 sentence credits an Order number too; replaces the CACHED sentence with the recorded-answer sentence; both layouts. |
| PR-007 | LOW | IN-SCOPE | G executability | the three workflow files' headings | E-04 did not say where the subsection goes in each differently-structured file or reuse the 2-attempt budget. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Placement per file, exit-gate checkbox, budget, Readiness exception, parity. |
| PR-008 | LOW | IN-SCOPE | E/G | V-05, Required tests, gate | Single mutation; targeted run omitted template, authoring, lint, consent and marker-parity tests; gate lacked scope fence, paste-actual-output rule and finalize form. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How is `AGENTS.md` regenerated? | `merge_aw_block` with the manifest, self-heal pass first | `aw install .` (wide delta, same stale-hash refusal); merge without manifest (leaves record stale, next regen refused, measured) | `_apply_section_consent`; commit `91ba3d7c`; `3wofej` E-03 | yes |
| D-2 | Should `dalmk4` wait for Orders 04, 06, 10? | Yes, declared in Item-Dependencies | keep only `26m1nb` and soften the text | E-03 sentences describe those gates | yes |
| D-3 | How are the new orchestrator placeholders kept stubs? | List them in `_AUTHORING_PLACEHOLDERS` | prefix matching in the predicate (changes every consumer) | `authoring_placeholders_resolved` contract (anchored, OQ-02 of uisjns) | yes |
| D-4 | Edit `tests/fixtures/conforming-orchestrator.md`? | No | regenerate it | it is a static lint fixture, not a parity copy; still conforming | yes |
