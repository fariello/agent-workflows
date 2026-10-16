# Review findings: plan ppu39q

- Subject-Id: ppu39q
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `e1e49e8ac`. The plan was committed (`fa52d1582`) and byte-identical to the lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean` (one info `IPD-Z602`). The plan is a child, not an orchestrator.

Verified by scratch probes (`AW_HOME`/`HOME`/`XDG_CONFIG_HOME` under `/tmp/opencode`, `AW_NO_REEXEC=1`):
- Bypass (b) reproduces: `install --delivery-mode clean-delta --records-backend home -y --no-interactive` on a `private-target` repo exits `0`, writes `<AW_HOME>/projects/r-27d38e/config/project.json`, reader stays `<repo>/.aw/config` with `delivery_mode: tracked`.
- Bypass (a) reproduces END TO END through the CLI: `sys.stdin = io.StringIO("n\n4\nprivate\n\n\n\n\n")` then `cli.main(["--no-color","install",repo])` returns `rc 0` and writes `<AW_HOME>/projects/r-40d5aa/config/project.json`. `collect_policy_interactive` treats a StringIO stdin as interactive ("or isinstance(sys.stdin, io.StringIO)").
- A `PolicyError` raised inside `persist_project_policy` from `cli._run_install` propagates uncaught (`RAISED InvalidPolicyError`), confirming E-03's placement inside the existing `try` is needed for a clean `rc 1`.
- `persist_project_policy(` has one production call site, `cli._run_install`; `_install_all` goes through `_install_one` and writes no policy.
- Companion preset: `resolve_project_context(preset="public-target-private-companion", delivery_mode="tracked")` resolves `config_project` to `<repo>/.aw/config/project.json`, the same dir the reader returns, while today's `resolve_policy_noninteractive` refuses `private-target` -> companion.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric D (regression of a shipped refusal) | `agent_workflows/install_wizard.py:617` `resolve_policy_noninteractive` "if new_cfg_placement != existing_cfg_placement:"; `agent_workflows/project_context.py:1711` `resolve_project_context` "elif resolved_delivery_mode == DeliveryMode.TRACKED.value:" | Replacing the label check with a path-only detector would newly ALLOW `private-target` -> `public-target-private-companion` (writer and reader are both `<repo>/.aw/config`), contradicting spec 8.1 item 3 and backlog `n9vd2h`, and would break `test_resolve_policy_noninteractive_cross_placement_guard_refuses`, which has no config on disk. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 detector has two branches: `path` (always) and `label` (only when `existing_policy` is passed). `resolve_policy_noninteractive` and `cli._run_install` pass it; `persist_project_policy` does not. Added F-06, OQ-01 amendment, E-05 test (1) companion case, V-02 companion probe. |
| PR-002 | HIGH | UNDER-SCOPE | Rubric E (test reachability, mutation proof) | E-05 (3) "is not reachable without a TTY"; `install_wizard.collect_policy_interactive` "or isinstance(sys.stdin, io.StringIO)"; review probe `rc 0` | The interactive bypass (F-01) had no end-to-end test, and the mutation proof (delete E-03, expect (4)/(5) to fail) was unsatisfiable: (4)/(5) are noninteractive and refused earlier by `resolve_policy_noninteractive`, so they pass with E-03 deleted. E-03 was therefore unproven. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 (3) now drives `cli.main` with a StringIO stdin and asserts `rc 1` and no home write. Mutation proof split into M1 (E-03 -> test 3), M2 (E-03 plus wizard call -> test 5), M3 (`persist_project_policy` call -> test 2). V-03, V-05, Expected outcome and Required tests updated. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric A (detector predicate) | `agent_workflows/project_context.py:977` `project_config_dir` rule 1 lists `project.json`, `local.json`, `config.json`, `policy.json` | Gating the detector on `project.json` alone misses a `local.json`-only or legacy repo the reader still resolves in-tree (review probe: reader `<repo>/.aw/config`, `local-only` writer `<AW_HOME>/projects/r-a6fe62/config/project.json`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 gates on any of the four files; E-05 test (1) adds the `local.json`-only case; F-07 added. |
| PR-004 | MEDIUM | IN-SCOPE | Honest documentation / spec sync | spec `20260810-1447-01` front matter "- Status: implemented"; E-04 items (2), (4) to (6) | Section 8.1 specifies `--relocate` and a transaction that Orders 02 to 05 have not built, inside a spec marked implemented, with no statement of what is live. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires an implementation-status sentence opening 8.1 (refusal live via `ppu39q`; relocation pending Orders 02 to 05, refusal unconditional until then) and forbids touching the spec's Status. |
| PR-005 | LOW | IN-SCOPE | Rubric F (UX, error clarity) | Bypass (b) keeps `preset` constant | A message naming only preset names reads "from private-target to private-target" for a delivery-mode-only switch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 message must also name `current_dir` and `target_dir`; V-03 checks it. |
| PR-006 | LOW | UNDER-SCOPE | Rubric E (adjacent suites) / evidence | `tests/test_clean_target_config_home.py:653` calls `persist_project_policy` directly; V-02 `-k cross_placement` does not select `test_subprocess_reinstall_private_target_to_local_only_fails_closed` | The new `persist_project_policy` guard is not regression-checked against its other direct caller suite, and V-02's filter skipped one of the two `on0keo` tests it relies on. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `tests/test_clean_target_config_home.py` to E-05 and Required tests; V-02 runs the whole module with `-m ''`. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean` (info `IPD-Z602` only).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep the label comparison beside the path detector? | Yes, as a `label` branch used only when `existing_policy` is passed. | Path-only (REJECTED: allows companion switch, F-06). Label-only (REJECTED: misses delivery-mode switch, F-02). Label check inside `persist_project_policy` (REJECTED: would refuse `test_preserves_companion_dir_for_companion_backend`, a `local.json`-only fixture with a companion policy). | Review probes in Round 1 "Verified"; `tests/test_reinstall_preserves_config.py:242`. | yes |
| D-2 | How to prove E-03? | End-to-end `cli.main` with a StringIO stdin plus mutation M1. | Direct `collect_policy_interactive` call (REJECTED: never exercises `_run_install`). | `install_wizard.collect_policy_interactive` StringIO clause; review probe `rc 0`. | yes |
| D-3 | Change the spec's Status when adding unbuilt 8.1? | No; add an implementation-status sentence instead. | Set `implementing` (REJECTED: `aw specs` owns status and the refusal half does ship here). | `AGENTS.md` "Spec status + history is OWNED by `aw specs`". | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
