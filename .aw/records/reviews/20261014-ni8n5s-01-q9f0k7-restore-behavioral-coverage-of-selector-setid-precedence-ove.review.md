# Review findings: plan q9f0k7

- Subject-Id: q9f0k7
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`fdea7b58c`), so no snapshot was needed. `aw ipd lint --phase author` was clean before review; `--phase review-finalize` conforms after the revisions, and `--phase pre-transition` no longer reports `check.ipd-uncarried-obligation`.

Claims verified:

- `selectors._PRECEDENCE` is `path, id6, setid, status, stem, substring`, and `selectors.resolve` iterates the module global at call time (`for kind in _PRECEDENCE:`).
- The `_PRECEDENCE IS FROZEN AS SEMANTICS` comment cites `tests/test_selector_zero_open.py::PrecedenceForcesFrontMatterReadsTests` with "no live guard currently asserts this".
- `rg -n MATCH_SUBSTRING tests/` is empty; `tests/test_selector_two_dialect_readers.py` is the cited precedent; the new module does not exist.
- Prototype on a temp plans tree: `"demo"` -> `setid`, two `Set: demo` plans, colliding `...-demo-shaped-name.ipd.md` excluded; `"approved"` -> `status`, filename-only `...-approved-looking.ipd.md` excluded; `"shaped"` -> `substring`, exactly that file. With `_PRECEDENCE` rebound in process to put `substring` before `setid`, the same setid test FAILED (`1 failed`) and passed (`1 passed`) unpatched. Probe ran under gitignored `.aw/state/` and was deleted.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Lifecycle gate | `aw ipd lint --phase pre-transition`: `check.ipd-uncarried-obligation: 3 obligation(s) name no durable carrier` | No Deferred row carried a carrier field, so the plan could not pass its own pre-transition gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a reasoned `Carrier-Declined` to each row. |
| PR-002 | MEDIUM | IN-SCOPE | E. Verification feasibility | E-03 "reorder `_PRECEDENCE` in a scratch copy (or monkeypatch ... in an ad-hoc `python3 -c` session)"; V-03 | A scratch copy is never imported by the test, so it cannot make it fail. A bare `python3 -c` monkeypatch does not reach a separate pytest process. Both options as worded were unsatisfiable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now prescribes an in-process rebind that then calls `pytest.main`, which was demonstrated at review. V-03 demands the command and an empty `selectors.py` diff before E-04. |
| PR-003 | LOW | IN-SCOPE | G. Re-derivation convention | Required tests "shows 3 passed"; V-02 "(3 passed total)"; V-04 "exactly the two Scope-Paths" | The collected test count was used as the bar. The commit-path check would also contradict the plan-path Scope-Paths fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bar now names the three behaviors. V-04 now requires both files and nothing outside Scope-Paths. |
| PR-004 | LOW | IN-SCOPE | E. Test robustness | E-02(a) status token; V-02 `rg "inspect"` | The status token was not required to be absent as a Set value, so setid could win instead and fail the test for the wrong reason. The `rg "inspect"` pattern also matches ordinary words. The fixture was unspecified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02(a) now requires the token to be no plan's Set. `rg` is narrowed to import forms. E-01 now names `unittest`, `TemporaryDirectory`, and no markers. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; `- Scope-Paths:`; OQ-01 `Owner: none` | The gate lacked the scope fence, `aw ipd begin`, conditional finalize ownership, and never-tag. The plan file was missing from Scope-Paths, and the owner was a placeholder. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the full contract and the plan path. Owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Carry the deferred rows as backlog items or decline them? | `Carrier-Declined` with reason | File new backlog items (scope expansion not requested) | Backlog `ni8n5s` property as quoted in OQ-01 | yes |
| D-2 | Falsifiability mechanism for E-03? | In-process rebind of `selectors._PRECEDENCE` then `pytest.main` | Edit `selectors.py` in place and revert (riskier, touches the E-04 file) | Demonstrated at review (`1 failed` reordered vs `1 passed`); `resolve` reads the global at call time | yes |
| D-3 | Accept OQ-01 (no `_PRECEDENCE` index pin)? | Yes, as authored | Restore it | GUIDING_PRINCIPLES P16; AGENTS.md no-code-pinning rule | yes |
