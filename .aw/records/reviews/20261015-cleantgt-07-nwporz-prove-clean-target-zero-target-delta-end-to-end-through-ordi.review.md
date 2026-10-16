# Review findings: plan nwporz

- Subject-Id: nwporz
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `79f852afc`.

- The plan was committed and unchanged, so no snapshot was needed.
- `aw ipd lint --phase author` was clean before the edits.

### Evidence verified

- Spec `20260810-1447-01` Section 4: the `AMENDED 2026-10-12 (cleancfg p425hv)` paragraph ends "remain open as Phase 3 work (backlog kvwwt0, spec or061f)".
- Spec Section 5: the "Per-machine control state ... stays IN the target repository" paragraph, with its guard test `AwGitignoreLaneTests.test_git_ignores_every_per_machine_control_path` (`tests/test_installer.py`).
- `CHANGELOG.md` `## 2.0.0 (pending)` uses flat `- Fixed:` bullets.
- The repo-root `conftest.py` has the `@pytest.mark.timeout` remedy that OQ-01 relies on.
- `runner_shared.state_root` derives from `logical_roots["records"]`.
- These sibling plans name `Carrier: nwporz`:
  - `qk0ew6` (Deferred: e2e proof and Section 5; OQ-03);
  - `3m8aix` (Deferred: spec/CHANGELOG/e2e; OQ-03);
  - `xoy5yg` (Deferred: spec/CHANGELOG for uninstall).

### Probe

Setup: a temp repo with temp `HOME`/`AW_HOME`, a global git identity, and a `private-target` install. Clean-delta is not built at this HEAD, so the probe tests verb spellings and exit codes only.

Spellings as written:

- `aw backlog new <title> --summary ...` errors. The command takes no positional title, and refuses without `--priority`.
- `aw ipd scaffold ... --apply` reports "--author is required (or set AW_IPD_AUTHOR)". After that is fixed it reports "--priority and --work-kind required". It has no `--dir`.
- `aw oc run start <id6> --prepare-only` exits 2 on the fresh scaffold with `check.ipd-dependency-unresolved`.

After the fixes (`--priority low`, `AW_IPD_AUTHOR=e2e`, `aw ipd dependencies set <id6> none`):

- Scaffold wrote a `draft` plan.
- `aw work begin <id6>` exited 0 and allocated `.aw/worktrees/<id6>`.
- `--prepare-only` exited 0, minted `records/runs/run-*`, and listed the item as a `review` action.
- `--action execute` is refused for a draft.
- `aw doctor` exited 1 on the fresh install.
- `index prompts`, `attention`, `status`, `research new` and `uninstall --yes` each exited 0.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G. Executability | Probe above; `aw backlog new --help` (no positional, `--priority`); `aw ipd scaffold --help` (no `--dir`, author/priority/work-kind required) | Three of the fixed verb steps fail as written, and `--prepare-only` refuses the fresh scaffold. The acceptance test would fail for reasons unrelated to target deltas. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now uses the measured spellings, `cwd=<t>`, `AW_IPD_AUTHOR`, and the `ipd dependencies set <id6> none` step, and states the draft->review action. Recorded as F-06. |
| PR-002 | MEDIUM | UNDER-SCOPE | Set coverage / honest docs | `qk0ew6` OQ-03 and Deferred row (workflow-artifacts, Carrier nwporz); `3m8aix` OQ-03 (setup marker, Carrier nwporz) | Two obligations siblings carried to this plan were not mentioned. The Section 5 amendment would claim more than ships. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 records both as documented residuals, or records the answers if given. The E-06 CHANGELOG line names both limits. F-07 is added. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing | Probe: `aw doctor` exit 1 on a fresh install | `doctor` is a findings-reporting verb whose nonzero exit is normal. Asserting it as a writing verb (0) would make the lock brittle. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The test asserts the observed code plus zero delta, independently. |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness of assertion | `runner_shared.state_root` derives `records_dir / "runs"` from `logical_roots["records"]` | E-03/V-03 put the run directory under the "home state root". It actually lands under the records class root, so the assertion would fail on correct code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03/V-03 now assert `state_root(<t>)` = `<AW_HOME>/projects/<id>/records/runs`. Also added: `work begin` must validate a plan that lives only in home records (the case `qk0ew6` deferred here). |
| PR-005 | LOW | IN-SCOPE | E. Mutation proof | E-04 "in the installed copy under test"; the tests run with `PYTHONPATH` at the source tree | No separate installed copy exists, and lane allocation had no mutation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Mutations now target the source tree. Added mutation (c) for `worktrees_root`, with a clean-diff restore check. |
| PR-006 | LOW | IN-SCOPE | G. Traceability / gate | `Carrier: or061f` (spec id, `check.ipd-uncarried-obligation`, as in `3m8aix`/`xoy5yg` PR-009); gate "stop and report"; "Cohesion rationale: not required" | Invalid carrier, an unspecific stop clause, and no cohesion rationale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Carrier is now `kvwwt0`. A leaking verb now makes E-01 `blocked`, naming the owning sibling. Accessor checks are added to E-01. Cohesion rationale written. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should this plan fix the two carried residuals (workflow-artifacts, setup marker)? | No; record them as documented residuals in the spec and CHANGELOG | Fix them here (outside Scope-Paths, and needs maintainer answers to `qk0ew6` OQ-03 / `3m8aix` OQ-03) | Both OQs are `Owner: maintainer`, `Blocking: no`; this plan's Scope-Paths are test, spec and CHANGELOG | yes |
| D-2 | How should the doctor step be asserted? | Observed exit code plus the zero-delta bar | Require 0 | Probe: exit 1 on a fresh install with findings | yes |
