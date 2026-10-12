# Review findings: plan df486j

- Subject-Id: df486j
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `772abdce9`. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` and `--phase review-finalize` both reported `clean`. `- Kind: child`.

Evidence verified: `runner_shared.manifest_entry_is_selectable` (`agent_workflows/runner_shared.py:15247`) refuses only `RETIRED_PLAN_STATUSES` (`:15239`) and `RETIRED_PLAN_DIRECTORY_SEGMENTS` (`:15244`), after lowercasing and stripping the status; its only caller is `expand_selectors` (`:14842`), which drops a retired Set member silently. The docstring cites the deleted `InRunExecutedDependencyTests` (`:15274`). `git show 19313eed^:tests/test_runner_item_dependencies.py` holds that class and the `_StartArgs`/`_plan_text` helpers. `tests/test_manifest_entry_selectable.py` does not exist. Every E-01 table row matches the predicate as written.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (test feasibility) | Review run of the deleted fixture shape: `DriverError: [RUN-STRUCTURE-PREFLIGHT] ipd bbbbbb ... violates IPD-M101: Concern: required field missing` (`agent_workflows/runner_shared.py:20634`) | E-02 modelled the fixture on the deleted `_StartArgs`/minimal-plan shape, which no longer reaches the queue, so the end-to-end test as specified fails on unmutated code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now reuses the conformant `_make_test_repo`/`_write_plan`/`_build_queue_for_selector` from `tests/test_typed_queue_entries.py` (real parser, `--prepare-only --unattended`) and forbids the stale shape. A prototype passed on both hosts. Added F5. |
| PR-002 | MEDIUM | IN-SCOPE | E (verification strength) | Review mutation runs on the prototype: admitting mutant `'cccccc' unexpectedly found`; executed-refusing mutant `KeyError: 'aaaaaa'` | E-03 said "monkeypatch" without a mechanism usable from the command line, and only asked that the module fail, which the predicate table alone would satisfy while the queue-path test stayed blind. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and V-03 now use scratch `-p` plugins kept out of the tree and require both the predicate test and the end-to-end test to fail for each mutant. V-01 now enumerates the table rows. |
| PR-003 | LOW | IN-SCOPE | G (execution contract) | Approval gate; OQ-01 `Owner: none`; V-04 `git show --stat HEAD` | The gate had no scope declaration, no paste-actual-output rule, and no conditional finalize ownership. V-04 assumed the test commit is `HEAD`, which a later lifecycle commit breaks. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate and pointed V-04 at the `aw commit df486j` commit. Set `Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Which fixture should the end-to-end test use? | The shipped conformant helpers in `tests/test_typed_queue_entries.py` (import the three helper names only). | Restore the deleted `_plan_text`/`_StartArgs` (fails preflight); copy a fixture into the new module (allowed as an alternative in E-02). | Review run of both shapes; `tests/test_typed_queue_entries.py` `_write_plan` and `_build_queue_for_selector`. | yes |
| D-2 | How should the mutation probe be applied? | Scratch pytest plugins rebinding the `runner_shared` attribute, run with `-p`. | Editing the source (forbidden by E-03); `mock.patch` inside the test file (would ship a mutant into the suite). | `expand_selectors` looks the predicate up as a module global (`agent_workflows/runner_shared.py:14842`); review runs killed both mutants. | yes |
