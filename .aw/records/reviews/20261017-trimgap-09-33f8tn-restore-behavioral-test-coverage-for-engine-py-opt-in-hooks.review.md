# Review findings: plan 33f8tn

- Subject-Id: 33f8tn
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the lane input and committed unchanged (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 9), test-only, one declared path.

Verified by direct call at the lane HEAD (`AW_NO_REEXEC=1`, engine imported from the lane):
- All 12 keys exist in `agent_workflows/engine.py` with the cited signatures (`create_dependency_gate_hook`, `_wire_optin_precommit_hook`, `create_precommit_scope_gate_hook`, `create_prepush_authorization_gate_hook`, `_merge_tree`, `migrate_local_lanes_to_untracked`, `validate_shim_grammar`, `is_stale_shim_customized`, `is_shim_customized`, `is_shim_customized_vs_expected`, `_shim_is_user_modified`, `agents_pointer_block`, `agents_managed_block`).
- E-02 (a) to (f) reproduce for all three hooks, including the exact note texts, YAML `repos` list, the user's text as prefix, and flattened hook ids `['user-hook', <id>]`.
- E-03 reproduces: return `['.aw/records/comms/untracked']`; `a.md`, `deep/c.md` moved; `b.md` NEW kept; `local/inbox/b.md` OLD left; `local/inbox/deep` removed; no-collision case removes `local/`, second call returns `[]`.
- E-04: four dispatcher combinations validate True; 56 shim members (plan said 54; drift, see PR-006), zero non-README failures.
- E-05: dispatcher not customized, appended line customized, `""` False; `vs_expected` description-only difference False, added line True; `_shim_is_user_modified` three regimes as described. `InstallPlan` accepts `manifest=`.
- E-06: pointer block starts `AGENTS_BEGIN`, ends `AGENTS_END\n`, contains `UNTRUSTED` and the right inbox path per layout; managed block first/last lines, section order, no legacy marker, stable.
- `conftest.pytest_collection_modifyitems` selects only `core`-marked items on a bare run. `tests/test_installer.py` carries `pytestmark = pytest.mark.slow`. PyYAML and coverage 7.15 / pytest-cov are installed (test extra in `pyproject.toml`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Correctness (test would fail on correct code) | `agent_workflows/engine.py:6797` and `:6799` (`_DEPENDENCY_GATE_PRECOMMIT_BLOCK` "id: ipd-dependency-statement-gate" and "entry: python3 -m agent_workflows ipd-dependency-statement-gate") | E-02(e) demanded "the hook id now appears exactly once"; a raw count is 2 for the dependency gate even on a correct fresh create (measured), so a literal implementation fails one parametrized case on correct code. | all Low | FIXED | E-02(e) now asserts the flattened YAML hook-id list equals `["user-hook", <id>]`, and says why raw counting is wrong. |
| PR-002 | MEDIUM | IN-SCOPE | Testing (vacuous negative row) | `19313eed^:tests/test_command_shims.py:172` `valid_oc.replace("---\n", "", 1)`; `engine.validate_shim_grammar` closing-fence loop | E-04 said to restore deleted inputs verbatim; the deleted "missing closing fence" input removes the FIRST fence, so it fails via the opening-fence check and the closing-fence branch stays unguarded (measured: text starts `description:`). | all Low | FIXED | E-04 specifies removing the second `---` line and forbids that verbatim input. |
| PR-003 | MEDIUM | IN-SCOPE | Testing (row isolation) | old E-04 "asserting the corresponding unbroken control is True where a control exists" | The control requirement was undefined, so a row could carry two defects and pass for the wrong reason (which PR-002 is an instance of). | all Low | FIXED | E-04 defines four minimal valid fixtures (OC, CL, CL_HINT, OC_ARGS), each measured True, and requires one defect per row against one of them. |
| PR-004 | MEDIUM | IN-SCOPE | Testing (mutation would survive) | `engine._shim_is_user_modified` recorded-hash branch; old E-05(c) rows | The recorded-hash rows recorded the GENERATED shim, where hash and structural answers agree, so deleting the manifest branch would leave every row green. | all Low | FIXED | E-05(c) records foreign text so both rows disagree with the fallback (measured False/True vs fallback True/False); V-05 and Required tests add the branch-deletion mutation. |
| PR-005 | LOW | IN-SCOPE | Validation (non-reproducible evidence; contract) | old Required tests "--cov ... (or coverage run ...)"; old gate paragraph | Reach evidence named two alternative commands with no per-key reading rule; gate lacked the full execution contract (honesty rule, staged-set check, conditional finalize ownership, scope-fence wording). | all Low | FIXED | Reach is now one `coverage run` + `coverage json` command reading `functions[<name>].summary.percent_covered` (> 0 for each of 12), checked at review; gate rewritten as an execution contract. |
| PR-006 | LOW | IN-SCOPE | Evidence drift | F-01; F-04 "54 shim members"; `tests/test_plain_command_delivery.py:33` (added `7591a72cf`) | F-04 count is now 56; a new non-slow, non-core caller of `validate_shim_grammar` exists after baseline. Neither changes the premise (no core caller). Plan already treats the member count as context, not a bar. | all Low | FIXED | Drift note added to F-01. |

`aw ipd lint --phase review-finalize --agent`: `clean` (one `info` `IPD-Z602` clause-count advisory, kept: each E-item is one test surface over one function family).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should E-02 still assert "exactly once" given the dependency gate names its id twice? | Assert on the parsed YAML hook-id list | Raw count == 2 for that hook only; drop the once-check | `engine.py:6797`, `:6799`; measured counts | yes |
| D-2 | Restore the deleted closing-fence input verbatim as E-04 said? | No; remove the second fence instead | Restore verbatim (tests the wrong branch) | `19313eed^:tests/test_command_shims.py:172`; measured | yes |
| D-3 | Keep the existing E-item split (6 items, one file)? | Keep | Split hooks and shims into separate plans | each E-item is one function family and one V-item; one new file, fast | yes |
