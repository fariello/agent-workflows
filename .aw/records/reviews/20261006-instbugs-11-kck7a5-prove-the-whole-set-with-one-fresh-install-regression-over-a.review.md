# Review findings: plan kck7a5

- Subject-Id: kck7a5
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `7da9f9719` in an isolated review-sweep lane. Child plan (own first `- Kind:` bullet reads
`child`); its six `Item-Dependencies` match the orchestrator `i99ykd` child table row (01, 04, 07, 08, 09, 10) and reach
the other four siblings transitively; all ten are `reviewed`, none executed. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent` clean before and after revisions;
`check_engine.check_durable_carrier` returns nothing for this plan.

Demonstrations (temp dirs, `AW_NO_REEXEC=1`, temp `HOME`, git identity in env, `umask 022` for research verbs):
- `-y` install 2.8 s, re-install 0.8 s, `doctor --json` 1.1 s (rc 1, `doctor.git-staged` etc.), `--version` 0.5 s,
  `research new` 0.5 s, `adopt ... --type research --kind research-report --set otherset --slug b --apply --yes` 0.6 s,
  `research index --check` 0.5 s (F-09).
- Open defects reproduce at HEAD: `?? .aw/config/`; `.aw/state/{install.json,history/installs.jsonl}` beside
  `durable/`; `installed_version` `2026.8.10`; both research files `-00-` and `0o600`; `index --check` clean (F-06).
- `-y` install output has no "Resolved Physical Classes"; `--dry-run -y` output does, with `.aw/config_project`,
  `.aw/state_durable` (F-05).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing (reachability) | `cli._run_install` prints `render_pre_write_plan` only under `dry_run`; F-05 | D04 asserted "every path the consent plan printed exists" on a `-y` run that prints no consent plan, so the assertion would pass vacuously. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fixture runs `--dry-run` first and captures the plan; E-01 does the same manually. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness | `gzsfqn` goal: `git status --porcelain` empty after `-y`; `xzlu9b` tracked README | D14 accepted "tracked or staged", which contradicts the D03 bar of an empty porcelain; the inbox drop needed an explicit ignore assertion. | Overall:Low | FIXED | D14 requires `git ls-files` and `git check-ignore` on a drop. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing | F-08; `aw doctor --help` | `aw doctor --format json` is not a flag, and "reports zero" over all diagnostics fails on unrelated drift. | Overall:Low | FIXED | `--json`, filter by the `ka0g86` rule id, do not assert exit code. |
| PR-004 | LOW | IN-SCOPE | G. Executability | orchestrator child table; E-01 | E-01 checked only the six direct edges while the module observes all ten children's fixes. | Overall:Low | FIXED | E-01 confirms all ten; edges unchanged to stay in parity with the orchestrator. |
| PR-005 | MEDIUM | IN-SCOPE | G. Executability | `aw adopt --help` (requires `--type`, exactly one path); D10 check half owned by `okw4ke` | `aw adopt --apply` lacked required arguments; the D10 mutation (hand-edit `order:`) needed a named expected output. | Overall:Low | FIXED | E-03 spells out both invocations and asserts the check output names `order`. |
| PR-006 | MEDIUM | IN-SCOPE | F. KISS / project rule | F-09; `tests/test_installer.py` `pytestmark = pytest.mark.slow` | A 15 s budget decided at execution invites a borderline default-suite module; measured cost and precedent already answer it. | Overall:Low | FIXED | OQ-01 resolved as `slow` with the measurement; E-03 records wall time only. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | gate "If any assertion fails ... STOP" | The stop was not framed as an unsafe-condition stop, and did not forbid weakening assertions. | Overall:Low | FIXED | Reframed with the no-weakening rule. |
| PR-008 | MEDIUM | UNDER-SCOPE | Release gates | `i99ykd` `- Blocks-Release: next`; completion criterion "One scratch-target regression test ... passes" owned by `kck7a5` | The Set's proof plan did not carry the Set's release gate. | Overall:Low | FIXED | Added `- Blocks-Release: next`. |
| PR-009 | LOW | IN-SCOPE | G. Execution contract | gate "move the plan to `executed/` with `aw ipd set executed kck7a5`" | Gate lacked resolved-OQ statement, honesty rule, scope fence as declaration, temp HOME, and conditional finalize ownership. | Overall:Low | FIXED | Gate rewritten to the Set's contract shape. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Default suite or `slow`? | `slow` | Decide at execution by a 15 s threshold | F-09 timings; `tests/test_installer.py` precedent; `pyproject.toml` addopts | yes |
| D-2 | Add the four transitive siblings as direct `Item-Dependencies`? | No, check them in E-01 | Add all ten edges | Orchestrator child table lists 01, 04, 07, 08, 09, 10; transitive edges already order them | yes |
| D-3 | Gate the release on this chore plan? | Yes, `next` | Leave ungated (chore is not in the gating set) | It owns a Set completion criterion of a release-gated orchestrator | yes |
