# Review findings: plan vfv2db

- Subject-Id: vfv2db
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T032734Z-4093657` at HEAD `ebb42a70e`. The plan was
committed (`c365d968a`) and byte-identical to the sealed lane input (rev-9); no snapshot needed. `- Kind: child`, so
`IPD-S407`/`IPD-S408` do not apply. `aw ipd lint --phase author` clean before review.

Re-measured by driving the CLI in a fresh `aw install`-ed `/tmp` project with `HOME`/`XDG_CONFIG_HOME` pinned and
`PYTHONPATH` set to this worktree: all eleven F-03 leaves still emit prose with no record; the seven F-07 leaves still
exit 2 with empty stdout; `runs export` emits a `preview` record. Recorded in the plan as F-12..F-15.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A correctness / E testing | `tests/conformance_matrix.py::run_cli` `effective_cwd = str(REPO_ROOT) if cwd is None`; `checkout_pin.check_and_reexec` returns when `find_toolkit_checkout()` is None; measured `agent_workflows.__file__` from `/tmp` = main checkout editable install | With cwd in a temp project the subprocess imports the installed package, which in a worktree/lane is a different tree, so red/green would measure the wrong code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 pins `PYTHONPATH=REPO_ROOT` for the arm (and `scoped_repo_dir`); V-01 demands `__file__` proof; gate STOP extended. |
| PR-002 | HIGH | IN-SCOPE | A correctness | Measured: `aw install . --yes` without git identity -> "Error: git commit failed." / "Changes are STAGED but NOT committed", HEAD unborn | Plan asserted install commits; with HOME pinned empty there is no identity, so HEAD/status baseline would not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 sets a local identity and asserts committed baseline (`.aw/config/` untracked noted); F-14 added; V-01 demands it. |
| PR-003 | HIGH | IN-SCOPE | D anti-regression | `tests/test_command_surface_declarations.py::test_zero_unreachable_command_declarations` asserts `reason_kind in ("sanctioned_raw","known_broken","not_runnable")`; `compute_conformance_universe` subtracts all `EXEMPTION_REGISTRY` keys | New kinds in the shared registry would be outside the closed tested set, and the plan did not say where entries live. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 mandates a separate `MUTATION_EXEMPTION_REGISTRY` with its own contract test; read registry unchanged; V-02 demands proof. |
| PR-004 | MEDIUM | IN-SCOPE | A correctness | `agent_schema.validate_agent_record` "Error record must carry exit=2"; `storage reattach` exits 1 today (F-12) | E-04 mapped `storage reattach` to `kind: error`, impossible at exit 1 without changing the human exit code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Mapped to `kind: result`, `outcome: cannot-run`, `exit: 1` (validated `[]`, F-15); V-04 demands the record. |
| PR-005 | MEDIUM | IN-SCOPE | E testing | Measured: `ipd recheck-readiness`, `upgrade-test clean` emit valid `clean` records with no `applied` key | "an applied mutation carries `applied: true`" read as a presence requirement would turn conforming leaves red. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 checks are conditional; preview reachability cited (`runs export`); V-03 updated. |
| PR-006 | MEDIUM | IN-SCOPE | Carrier / traceability | `.aw/records/backlog/done/...lbbo9s...` Status done; `.aw/records/backlog/open/...91pjax...` "vfv2db E-06 SHOULD BE RE-POINTED at this item id" | E-06 and the Deferred carrier named a closed item; the real owner `91pjax` already exists. Backlog edits were outside Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Carrier -> `91pjax`; seven leaves exempted `owned_elsewhere` citing it; `aw backlog note` used; both backlog paths added to Scope-Paths; V-06 rewritten. |
| PR-007 | LOW | IN-SCOPE | Isolation design / gate | E-03 "the repository under test is untouched" in-suite; shared checkout + xdist | An in-suite whole-repo status assertion would flake on concurrent edits; gate also said "AMEND Scope-Paths before staging" rather than finalize justification, and lacked a lifecycle clause; counts stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Isolation re-tiered (per-leaf in suite, whole-repo as V-03 one-off); gate uses `--scope-reason`/`--scope-ack` and runner/`aw ipd finalize` ownership; counts marked as re-derived. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `storage reattach`'s exit-1 refusal be represented? | `kind: result`, `outcome: cannot-run`, `exit: 1` | `kind: error` at exit 2 (changes human exit); `kind: error` at exit 1 (schema rejects) | `agent_schema.validate_agent_record` probe (F-15); E-04 byte-identical requirement | yes |
| D-2 | Where do mutation exemptions live? | Separate `MUTATION_EXEMPTION_REGISTRY` | Widen the closed kind tuple in `test_command_surface_declarations.py` (out of scope, weakens a shipped check) | `test_zero_unreachable_command_declarations`; `compute_conformance_universe` | yes |
| D-3 | Who carries F-07? | Existing `91pjax`; seven leaves exempted citing it | Extend `lbbo9s` (done); file a new item (duplicate) | `91pjax` body; `lbbo9s` Status done | yes |
| D-4 | How to guarantee the arm runs this tree's code? | Pin `PYTHONPATH=REPO_ROOT` in the subprocess env | Rely on cwd (wrong outside checkout); `AW_NO_REEXEC` (irrelevant: no re-exec occurs) | Measured `agent_workflows.__file__` from `/tmp`; `checkout_pin.check_and_reexec` | yes |
| D-5 | Assert repository-under-test cleanliness in-suite? | No; per-leaf temp-root confinement in suite, whole-repo status as one-off V-03 evidence | In-suite `git status` of the repo (flakes in a shared checkout under xdist) | AGENTS.md shared-checkout section; `pyproject.toml` `addopts` `-n auto` | yes |
