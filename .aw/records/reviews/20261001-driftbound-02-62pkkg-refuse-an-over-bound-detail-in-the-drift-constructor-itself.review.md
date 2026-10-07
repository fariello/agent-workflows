# Review findings: plan 62pkkg

- Subject-Id: 62pkkg
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-001 (HIGH, open), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (MEDIUM, open)

## Round 1

Reviewed in isolated lane `review-sweep-run-20261007T032752Z-4094028` at HEAD `baf4983ed`; plan committed and
byte-identical to the sealed lane input (rev-14), so no snapshot. `- Kind: child`; `IPD-S407`/`IPD-S408` do not apply.
`aw ipd lint --phase author` clean before review; `review-finalize` after review reports only `IPD-Q501` for the
deliberately escalated blocking OQ-06.

Measured at review (in-process; a scratch tree copy under /tmp was refused by the lane sandbox):
- Census: `check all --json` 2 unsafe of 226 (both the 329-char floor clause on `qtz0us`), `attention --check --json` 0 of 11, `doctor --json` 4 of 821 (same detail).
- Strict constructor patched into `artifact_core.Drift`: `check_engine.check_type(repo,"plans")` 96 -> 49 findings, all 26 `check.ipd-carrier-finished-unverified` and 21 `check.ipd-uncarried-obligation` lost; no exception surfaced.
- `ipd_lint.lint_file(<1u4olp>, checkpoint="pre-transition")`: blocking "6 obligation(s) name no durable carrier" present before, absent with the refusal simulated.
- `specs.validate_spec` with a 400-char `Gate-Ref`: 444-char `attention.gate-malformed` detail; under the strict constructor raised `ValueError`; `cli.main(["check","all","--agent"])` with that producer raising returned 2.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A correctness / D invariants | `check_engine.check_type` "`check_durable_carrier(...)` ... `except Exception: pass`"; `ipd_lint._merge_durable_carrier` "a repo-scan failure never masks the pure lint result"; `specs.validate_spec` `f"invalid Gate-Ref for {kind}: {ref!r}"` | F-05/F-06 premise wrong: a raising `Drift` is swallowed, silently dropping whole sweeps (96 -> 49) and a blocking pre-transition finding, or crashes `aw check all` (exit 2) where unisolated. Authored-echo details make the raise reachable by any author, so a clean population cannot make E-04 safe. | C:Medium-High; U:Medium; S:Low; F:High; Overall:High | OPEN | Escalated as blocking OQ-06 (`- Finding: PR-001`) with options normalize / test-only strict / raise plus widened scope; F-05, F-06 corrected, F-17 added, V-04 now demands per-rule counts unchanged. |
| PR-002 | MEDIUM | IN-SCOPE | G stale premise | `check_engine.evaluate_durable_carrier` "# Floor of one locator (OQ-01)"; executed plan `lxcexr` | Executed `lxcexr` already replaced `[:5]` with a budget; the only over-bound case is its deliberate one-locator floor (329 chars). E-02 described code that no longer exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now targets marked elision inside the floor clause; F-02/F-04 annotated. |
| PR-003 | LOW | IN-SCOPE | Carrier hygiene | `.aw/records/backlog/done/*7stpjm*`, `*3jez8u*` (both `done`) | Deferred rows named finished carriers without `Carrier-Evidence` (the plan itself raises `check.ipd-carrier-finished-unverified`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Carrier-Evidence for `lxcexr` and `0obt4k` added. |
| PR-004 | LOW | IN-SCOPE | Evidence currency | `ynhst5` in `executed/`; `_CONTROL_CHAR_RE` includes `\u202a-\u202e\u2066-\u2069` | F-14, OQ-05 and the bidi deferral describe superseded state. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Annotated as moot or shipped. |
| PR-005 | MEDIUM | UNDER-SCOPE | E testing | `pyproject.toml` addopts `-m 'not slow and not livecorpus'` | The E-05 census over live surfaces is either deselected (`livecorpus`) or flaky against a moving corpus, so it can't be the regression guard. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 requires a fixture tree that triggers the longest producers. |
| PR-006 | LOW | UNDER-SCOPE | Execution contract | Gate paragraph | Missing paste-output rule, scope-fence-as-declaration, and runner-vs-executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten. |
| PR-007 | MEDIUM | UNDER-SCOPE | Scope | F-17; `- Scope-Paths:` omits `specs.py`, `research_index.py`, `backlog.py`, `ipd_lint.py` | Under option (c) those producers and callers must change; under (a)/(b) they need not. The scope depends on OQ-06. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | OPEN | Resolved by OQ-06's answer; executor declares or `--scope-reason`s accordingly. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can review resolve the E-04 runtime mechanism itself? | No; escalated as blocking OQ-06 to the maintainer | Rewriting E-04 to normalize (changes the backlog item's "refuse" intent and a spec contract) | Measurements above; AGENTS.md "asking the human ONLY when ... the decision is theirs (... public contracts)" | yes |
