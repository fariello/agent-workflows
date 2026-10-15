# Review findings: plan ztx39t

- Subject-Id: ztx39t
- Subject-Type: ipd
- Reviewed-At: 2026-10-14
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `6372c22ef`. The plan was committed and byte-identical to the
lane input (sha256 `803db566...`), so no pre-review snapshot. `aw ipd lint --phase author`: `conforming`.
Not an orchestrator. Backlog `s8eaay` is `Work-Kind: chore` with no `Blocks-Release`, so no gate to inherit.

Re-measured: `tests/test_id6_global_mint.py` is absent; `19313eed^` contained
`test_the_mint_set_over_collects_quoted_ids_and_that_is_deliberate` with the fixture described in E-01 (F-01
MATCH); only `tests/test_specs_date_containment.py` mentions the mint seam (F-02 MATCH); the docstring
sentence "deleted in ``19313eed``; no live guard currently asserts this" is present in `global_id6s` (F-04
MATCH). Driven: `global_id6s` on the E-01 tree -> `['own111', 'qut111']`; without the fenced quote ->
`['own111']` (F-03 MATCH). `mint_id6` with a per-character rng yielding `qut111` then `fre111` -> `fre111`
on the quoting tree, `qut111` on the non-quoting tree.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G executability | `artifact_core.generate_id6` (`"".join(rng(ID6_ALPHABET) for _ in range(ID6_LENGTH))`) | E-02 said "an `_rng` pinned to emit `qut111` on the first draw"; `_rng` is called once per CHARACTER, so a draw-per-call rng returning whole id6s yields a 36-char candidate and the test is wrong or vacuous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 specifies a per-character iterator and was demonstrated at review. |
| PR-002 | LOW | IN-SCOPE | E falsifiability | plan E-02; V-01 negative run is local-only | The mint test would also return `fre111` if the rng alone were broken; no committed control distinguishes the cause. | Overall:Low | FIXED | E-02 adds an in-test control: the same rng on a non-quoting tree must mint `qut111`. |
| PR-003 | LOW | IN-SCOPE | G execution contract / evidence | plan gate; "Required tests" ("2 tests") | The gate lacked the scope-fence, honesty and conditional-finalize clauses, and the bar was a collected count. | Overall:Low | FIXED | Gate rewritten; evidence is the named tests passing; the source-pin grep was tightened so a legitimate word like "inspects" cannot false-match. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Restore the other deleted tests from the module? | No (author's scope kept). | Restore all (REJECTED: owned by other backlog items; the signature pin violates P16). | Backlog `s8eaay` names only site S-01; AGENTS.md "TEST OUTCOMES". | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
