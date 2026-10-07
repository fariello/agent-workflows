# Review findings: plan rtvdak

- Subject-Id: rtvdak
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Re-review in lane `review-sweep-run-20261007T165339Z-456282` at HEAD `ba977bc5e`. The plan was committed and byte-identical to the sealed lane input rev-3 (sha256 `b6983437...b4c3`), so no snapshot was needed. `- Kind: child`. `aw ipd lint --phase author` was conforming. The previous review round was on 2026-10-01. Since then, the contract this plan implements, spec `89xjll`, has been authored and spec-reviewed, and the landing site has changed.

Re-measured:
- Spec `89xjll` is at `.aw/records/specs/reviewed/...`, `- Status: reviewed`. Its history reads "REVIEWED - OPEN QUESTIONS; ... SR-002,SR-003 OPEN as blocking OQ-05,OQ-04". Its Section 3.1 says "Section 6 MUST NOT be implemented until OQ-04 is ratified".
- `89xjll` R-5 says TRACE "implements all three conjuncts of its pass criterion". Its 6.4 and AC-6 say "the result marks the pass as vacuous". Its 5.1 fixes the key as `spec_requirement_ids`. It also declares R-1..R-7 and AC-1..AC-8.
- `production_checks`: the siblings are `spec_plan_count`, `spec_plan_set` (`state`, `asker`, `runner`), `spec_plan_conformance` (now with `continued_ids`) and `spec_plan_gate_carry`.
- `runner_shared`: the SPEC cluster passes `all_verified_paths` (`existing_linked_plans` plus the new plans) and appears twice, once after production and once in the "# Production correction turn loop" (`while findings:`, `production_set_retry_decision`). The backlog cluster now includes `backlog_graduate_set`.
- `pyproject.toml` addopts end `-m 'not slow and not livecorpus'`. `.aw/config/project.json` `cutovers` holds 8 keys.
- `25kzda` 4.8 TRACE row: unchanged.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A correctness / contract | `89xjll` 1b R-5 "implements all three conjuncts"; 3.1 "Section 6 MUST NOT be implemented until OQ-04 is ratified"; OQ-04/OQ-05 OPEN, BLOCKING; plan E-01 "five things", E-05 "(b) DEFER it" | The plan predates its contract. It extracts five decisions where the spec now requires seven: the two open rulings (TRACE-mandatory forms, unknown-reference attribution) change E-03 and E-05. It also still offers deferral of the third conjunct, which R-5 now forbids except under an OQ-05 option-C ruling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now reads seven decisions, including OQ-04/OQ-05, and stops if either is open; it also records R-1..R-7 and AC-1..AC-8 with an AC-to-V map. E-05 makes the third conjunct mandatory per the OQ-05 ruling and applies the OQ-04 ruling. V-01/V-05 now require these as evidence. |
| PR-002 | HIGH | IN-SCOPE | A correctness / landing site | `runner_shared` "# Production correction turn loop (nnsa2o E-02)", `while findings:`, the second `_pc.spec_plan_conformance(` call; `all_verified_paths`; `production_checks.spec_plan_set` | The landing site changed since authoring. The SPEC verifier cluster now runs twice, the second time after each correction turn, and wiring TRACE only once would let a correction turn clear an uncovered requirement. Siblings receive `all_verified_paths`, not `new_produced_paths`. There are four siblings, not three, and the refusal now goes through a bounded retry. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02, E-07, V-02 and V-07 now name both clusters, `all_verified_paths`/`continued_ids`, the four siblings and the retry path. E-08 adds a persistence-across-correction case (v). |
| PR-003 | MEDIUM | UNDER-SCOPE | A correctness / honest docs | `89xjll` 6.4 "the verifier's result must make the vacuous case distinguishable from a real pass"; AC-6 | The `[(code, subject, message)]` return cannot distinguish a vacuous pass from a real one, and the plan had no surface for it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 requires an observable vacuity surface (recommended: a pure companion recorded as a run event). E-07 records it and E-08 case (vi) asserts it. |
| PR-004 | MEDIUM | IN-SCOPE | G gate accuracy | gate "the grammar has no such edge (F-10)", "cannot detect an unapproved spec for you"; front matter `state:spec:approved:89xjll` | The gate contradicted F-10 and the plan's own front matter: the runner does block on spec approval. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate is rewritten. The runner holds the plan on `state:spec:approved:89xjll` (measured: `reviewed`), and E-01 stays as the attestation layer. |
| PR-005 | LOW | IN-SCOPE | G execution contract | gate "POST-GATE LIFECYCLE MOVE ... (`aw ipd finalize` / the runner's self-finalize)" | The gate had no scope-fence declaration, and finalize ownership was ambiguous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the scope fence and conditional runner/executor finalize. |
| PR-006 | LOW | IN-SCOPE | Evidence drift | conventions "Six features ... five of them"; addopts "-m 'not slow'" | Stale facts. The feature key is now fixed by `89xjll` 5.1. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected: re-count at execution, the key is `spec_requirement_ids`, and addopts quoted as shipped. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should TRACE receive `all_verified_paths` or `new_produced_paths`? | `all_verified_paths`, matching `spec_plan_conformance`, with the choice recorded against `89xjll` 6.1's wording | `new_produced_paths` (spec 6.1's literal "newly produced"; it would ignore continued plans of the same production) | `runner_shared` SPEC cluster passes `all_verified_paths` to conformance and gate-carry | yes |
| D-2 | How should the vacuous pass be surfaced? | Recommend a pure companion recorded as a run event, leaving the executor free to choose another tested mechanism | Change the findings tuple shape (breaks the sibling contract and the shared refusal path) | `89xjll` 6.4, AC-6; `production_checks` module docstring contract | yes |
