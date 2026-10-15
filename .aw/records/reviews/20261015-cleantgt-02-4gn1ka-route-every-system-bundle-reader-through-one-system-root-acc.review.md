# Review findings: plan 4gn1ka

- Subject-Id: 4gn1ka
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged at `3d4772588`, so no pre-review snapshot was taken. `aw ipd lint` was clean at `author` before the review and at `review-finalize` after it. All 57 cited symbols resolve in `agent_workflows/`, and the F-01 census re-ran to the same 122 occurrences. Probes ran with a temp `HOME` and `AW_HOME`:

- I resolved 7 fixtures. Each line lists the inputs, then `delivery_mode` with its provenance, then the `system` root:
  - `{"role":"target"}`: tracked, builtin_defaults, in-tree.
  - `clean-delta` + `home`: home.
  - `tracked` + `home`: in-tree.
  - `completely-clean-target` preset: clean-delta, project_durable_config, home.
  - `local-only` preset with no `delivery_mode`: tracked, builtin_defaults, in-tree.
- A real `aw install --preset completely-clean-target -y --no-interactive` exited 0. It committed `a1bfc04` with 161 `.aw/system/` paths. AW_HOME held only `config` and `state`. The resolver's `system` root was `<AW_HOME>/projects/<id>/system`, and `engine.read_installed_version` read the in-tree VERSION.
- With an in-sandbox AW_HOME (`<sb>/.aw-upgrade-test/aw-home`) and a stored clean-delta policy, the resolver raised `PathSecurityError: Clean-delta security violation: system root ... is inside target repository`.
- `aw status --json` lists only repositories registered in the user config. An unregistered fixture shows `installed: null`, while `aw doctor --json` run with cwd = fixture reports `installed_version`. Two `aw status --json` runs at the same commit differed only in `git.ahead`.
- `clean_delta.resolve_system_provider` and `resolve_adapter_reference` have no caller in `agent_workflows/` or `tests/`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness | kfnfji E-02 `_stored_physical_classes` "returns `None` when no stored records placement exists"; `project_context.py:1106` clean-target derivation; probe fixtures `d` and `e` | E-02 built `project_system_dir` on a helper that kfnfji's review gated on records-backend provenance. A stored `completely-clean-target` preset has a records backend from `builtin_defaults`, so the system accessor would return in-tree for exactly the clean-target case and the fix would silently not apply. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now gates `system` on delivery-mode provenance or a `system_root` binding, and generalizes the shared helper per class. Added the unit cases and F-08. Added a cross-reference into kfnfji E-02 so the helper memoizes provenance alongside `physical_classes`. |
| PR-002 | LOW | IN-SCOPE | E. Testing | `rg resolve_system_provider` = definition only | E-03 routes `clean_delta.resolve_system_provider`, but nothing calls it, so no end-to-end test can observe the change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires a direct unit test and records that the function is uncalled. |
| PR-003 | MEDIUM | IN-SCOPE | E. Reachability | `cli._repos_for_report` reads `config.expanded_repos`; probe showed `installed: null` for an unregistered fixture | V-03 asked for `aw status --json` to show the fixture's version. That command reports only registered repos, so the evidence was unobservable as written. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 and E-03 now use `aw doctor --json` (cwd = fixture), `aw list-repos --json` on a registered fixture, and `aw check all --dir`. The bundle must exist only at home, and the unmodified code must show the contrasting result. |
| PR-004 | MEDIUM | UNDER-SCOPE | E. Feasibility | `upgrade_rehearsal.sandbox_env` AW_HOME = `<sandbox>/.aw-upgrade-test/aw-home`; probe gave `PathSecurityError` | E-05 told the probe to resolve through the sandbox AW_HOME. For clean-delta that AW_HOME is inside the sandbox repo, so the resolver raises and the rehearsal would crash, not report. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now catches `ProjectContextError`, falls back in-tree and records `system_root_error`, and tests both an external AW_HOME and the default one. Moving the sandbox AW_HOME is recorded as a Carrier-Declined deferral, and F-09 was added. |
| PR-005 | MEDIUM | IN-SCOPE | E. Verification feasibility | `aw check all --format json` exits 2; `aw status --json` `git.ahead` drifts; `check all --json` `elapsed_ms` and `next_actions` order drift | The E-07 in-repo "empty diff" demand could not be met. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now uses `--json`, normalizes the output (timing, ahead/behind, list order), and requires a base-commit control diff. V-07 and Required tests were updated to match. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract | RIGHT-SIZING NOTE "STOP after the completed groups and ask" | Stopping to ask on a scope-size question strands an unattended run and names no carrier for the leftover work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The remainder is now filed as one release-gated backlog item and execution continues (V-06 and the gate updated). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What makes the `system` placement "stored"? | `delivery_mode` provenance `project_durable_config`/`machine_local_binding`, or a `local.json` `system_root` binding | Reuse kfnfji's records gate (misses the clean-target preset); any config file present (moves `{"role":"target"}` fixtures, although the system resolves in-tree for them anyway) | `project_context.py:1085-1129`, `:1219-1225`; 7-fixture probe | yes |
| D-2 | How should E-05 handle the in-sandbox AW_HOME conflict? | Degrade honestly (`system_root_error`) and defer moving the AW_HOME | Move the sandbox AW_HOME outside the sandbox (changes the containment invariant); drop E-05 (leaves a crash path) | `upgrade_rehearsal.sandbox_env` docstring "keeps every `aw` call inside the sandbox (invariant 3)"; probe | yes |
| D-3 | Should 4gn1ka edit kfnfji's plan text? | Add one cross-reference sentence to kfnfji E-02 (pending, not executed) | Leave kfnfji as is (its executor would build a records-only cache that 4gn1ka must rework) | plan-review 2.4 "fix it in the owning plan and cross-reference it from dependent plans" | yes |
