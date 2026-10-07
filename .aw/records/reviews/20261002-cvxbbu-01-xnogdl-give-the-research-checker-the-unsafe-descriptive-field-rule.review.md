# Review findings: plan xnogdl

- Subject-Id: xnogdl
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T032752Z-4094028` at HEAD `250466250`. The plan was
committed and byte-identical to the sealed lane input (rev-11, sha256 `c69852cc...`); no snapshot needed.
`- Kind: child`, so `IPD-S407`/`IPD-S408` do not apply. `aw ipd lint --phase author` clean before review;
`review-finalize` clean after.

Re-measured: census n=129 summaries, exactly the three named files over bound (395, 351, 320), no unsafe topic or
consumed-by token. `check_engine.rule_spec("attention.unsafe-field")` -> `RuleSpec(severity='error', ...)`.
`research_index._doc_entry` turns any `validate_frontmatter` error into `frontmatter-invalid` and no entry (F-06
holds). `check_engine.check_content` research branch is `if dirs and include_retired:` (F-07 holds). `check_drift`
has no `attention.unsafe-field` emitter and no module-level `attention_contract` import. `deftzy`, `jnpl08` and
`m5csyi` are executed; `llnvwj` (`qpw45x`) is reviewed/pending. Newline-injection fixture: `parse_frontmatter`
gives `status=reference`, `blocks-release=next`, `summary=legit`, `validate_frontmatter == []`; `check_drift` rule set
`['check.stale-index-missing', 'research.frontmatter-key-repeated']`, document still indexed.
`aw research index --check --agent` exit 1, rules `dangling-citation` 122, `adopted-without-consumer` 35,
`stale-state-to-promote` 19, `check.stale-index-missing` 2, `frontmatter-invalid` 1.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | D anti-regression / E testing | `research_index.check_drift` "Repeated frontmatter keys (Set jnpl08 / IPD 7d4bgs E-02)"; fixture drift includes `research.frontmatter-key-repeated` | E-05 LIMIT ONE and F-05 say no checker sees the newline vector; executed `jnpl08` now reports the duplicated `status`. A test written to "no checker sees it" would either be wrong or be unable to state the real residue (a non-duplicate injected key like `blocks-release`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05/V-05 now assert no `attention.unsafe-field`, exactly one `frontmatter-key-repeated` naming `status`, and nothing naming `blocks-release`. F-05, the deferred entry and under-scope (c) updated. |
| PR-002 | MEDIUM | IN-SCOPE | D "do not freeze accidental behavior" | E-05 LIMIT TWO "a value this rule now flags is still emitted raw by the renderer"; `.aw/records/plans/pending/20261001-llnvwj-01-qpw45x-...ipd.md` E-01 `neutralize_control_characters` | Pinning that `aw attention` emits raw bytes freezes a defect a reviewed plan is about to fix, so the test would go red when `qpw45x` lands. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | LIMIT TWO now asserts the stable property (the check leaves bytes and index values unchanged), and forbids asserting raw renderer output. |
| PR-003 | LOW | IN-SCOPE | G stale evidence | `deftzy` refuses `--summary` with a control char; `Carrier-Evidence` pointed at `plans/pending/`; index rule counts drifted (78 -> 122) | F-01's driver no longer reproduces through the CLI; the deftzy evidence path is stale; V-03 compared against authoring counts. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-01/F-08 annotated, Carrier-Evidence moved to `executed/`, V-03 compares to a pre-change rule set taken at execution, gate notes deftzy landed. |
| PR-004 | LOW | IN-SCOPE | Scope-fence wording | E-03 "state the gap and STOP rather than widening scope" | A stop over a scope question contradicts the 2026-09-01 scope-fence ruling; only "reaches no consumer" is a legitimate stop (the gate already says so). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now stops only on the no-consumer case; narrower gaps are fixed and justified with `--scope-reason`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep OQ-01 (repair the three summaries, no grandfather tier), including the `archive/` and `adopted` records? | Keep | grandfather tier | census n=129, same three offenders; edit touches only `summary:` | yes |
| D-2 | What should LIMIT TWO pin instead of raw renderer output? | Check-is-report-only (bytes and index value unchanged) | drop the limit; pin raw output (freezes a defect) | `qpw45x` reviewed, pending | yes |
