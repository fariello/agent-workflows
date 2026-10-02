# Review findings: plan kxwpqf

- Subject-Id: kxwpqf
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `e094aa0c2` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review; `--phase review-finalize` was clean after revision.

Re-verified (read-only; no repository file outside the plan and this record was modified):
- Premise: `python3 -m pytest tests/test_verbose_flag_reach.py tests/test_fields_flag_reach.py -o addopts="" --durations=3`
  -> `30.92s call ...test_verbose_flag_end_to_end_observable_difference`, `15.38s call ...test_fields_flag_end_to_end_projection`,
  `7 passed in 47.22s`. Neither file imports `pytest` or carries a marker.
- `result_types.CommandResult.to_agent_record`: diagnostics block under the comment "Diagnostics (omitted in compact if clean)"
  branches `if is_verbose:` full `d.to_dict(repo_root)` vs the `{"location", "rule"}` literal; `--fields` applied via
  `if context is not None and context.fields: rec = _schema.filter_record_fields(...)`. Matches F-05/F-07.
- Synthetic probe (in memory, temp dirs): a temp repo with one `support.ready_plan_text(status="draft", approval=None)` plan
  yields compact `[['location','rule']]`, verbose `[['detail','fix','location','rule','severity']]`, `--fields findings` keys
  without `target`/`diagnostics`; 3 calls in 0.577s. An EMPTY temp dir still yields
  `[{'location': '<collisions>', 'rule': 'check.collisions-not-checked'}]`, so the twin's non-empty precondition is deterministic.
- `pyproject.toml` markers `slow`/`livecorpus` text and `addopts` match the plan; `conftest.py` `_DEFAULT_TEST_TIMEOUT = 90.0`.
  Method-level `@pytest.mark.livecorpus` precedents exist at `tests/test_ipd_lint.py` and `tests/test_review_record_classifier.py`.
- `-m livecorpus --collect-only` now reports `5/4875 tests collected (4870 deselected)` versus F-10's 4856: the deselected
  population has already drifted since authoring.
- Backlog `tf6x3a` is `graduated`, `Blocks-Release: next`, `Work-Kind: bug`; `wc5c5e` names the verbose node and the
  three filed failures; plan `mat9bt` exists in `pending/`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | E. Testing / mutation adequacy | `agent_workflows/result_types.py:463` "Diagnostics (omitted in compact if clean)"; plan E-02 | E-02 did not require the twin to assert non-empty diagnostics. Because the key is omitted when there are none, a twin iterating an empty list passes vacuously and M1/M2 would survive. The live test has this precondition; the twin spec dropped it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires `assertTrue` on both lists before iteration and explains why it is deterministic on a synthetic repo (always-on `check.collisions-not-checked`); V-02 demands written confirmation. |
| PR-002 | MEDIUM | UNDER-SCOPE | E. Testing / non-vacuous absence | plan E-03; same omission rule | The fields twin's `diagnostics`/`target` absence assertions could pass because the fixture never produced them, not because of projection. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 requires a contrastive unprojected run asserting both keys PRESENT; V-03 demands it. |
| PR-003 | MEDIUM | IN-SCOPE | G. Internal consistency | plan Required tests prose and Execution contract ("V-04's mutation study", "V-04 mutates it") | The mutation study lives in V-02/V-03, not V-04; the stale references could make an executor run mutations after E-04, inverting the "twins proven before withdrawal" ordering. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All references repointed to V-02 (M1, M2) and V-03 (M3). |
| PR-004 | MEDIUM | IN-SCOPE | G. Live-artifact criterion / unreachable baseline | V-04 (e) and gate "reconciled against the V-01 baseline"; measured 4870 deselected vs F-10 4856 | V-01 only runs two modules, so it has no bare-suite deselected count to compare against, and the authoring count has already drifted. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 (e), Required tests, and gate now demand a pre-E-04 bare `--collect-only` deselect notice re-derived at execution HEAD, pasted beside the post-change notice. |
| PR-005 | MEDIUM | IN-SCOPE | G. Execution contract (lifecycle ownership, scope fence) | plan gate "Run `aw ipd begin` ... and `aw ipd finalize`"; plan-review Step 4 | Gate unconditionally instructed the executor to run begin/finalize (refused in a runner lane) and lacked a declared scope fence with `--scope-reason`/`--scope-ack`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now states conditional runner/executor ownership, forbids `git mv`, adds the declaration-style scope fence, keeps the STOP only for a genuine production defect, and forbids closing `tf6x3a` from this plan. |
| PR-006 | LOW | IN-SCOPE | Evidence citation | plan E-03 "which F-07 records is unstable" | F-07 of this plan is the mutation study; the `next` instability is recorded in the existing test's docstring (its own plan's F-14). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Citation corrected. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is `livecorpus` (vs `slow` or a raised timeout) correct? (OQ-01) | Keep `livecorpus` | `slow`; per-test `@pytest.mark.timeout` | `pyproject.toml` marker text; live tests assert `assertTrue(compact_diags, ...)` on tree state; no subprocess spawned | yes |
| D-2 | Should the twin's non-empty precondition be added, given the live one is the corpus-dependent part? | Yes; it is deterministic on a synthetic repo | Leave it out (vacuous); assert a specific rule id (brittle) | Empty temp dir probe yields `check.collisions-not-checked` | yes |
| D-3 | Split the plan? | No; four focused E-items over two files, one concern | Separate plans per file | Each E-item is one deliverable with one V-item; lint clean | yes |
