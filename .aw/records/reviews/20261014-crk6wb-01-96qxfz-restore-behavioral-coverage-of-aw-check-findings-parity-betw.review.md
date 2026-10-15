# Review findings: plan 96qxfz

- Subject-Id: 96qxfz
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was already committed and unchanged, so no snapshot was needed.

Lint results:

- `aw ipd lint --phase author`: clean before review.
- `--phase pre-transition` before review: reported `check.ipd-uncarried-obligation` on all three Deferred rows.
- After the revisions, `--phase pre-transition` shows only the expected `IPD-S404` not-yet-performed items, and `--phase review-finalize` is clean.

Probes ran from a scratch script under the gitignored `tmp/`, deleted afterwards. They drove the CLI through `tests.support.run_cli` in both shapes. Results:

- Seeded parity, all four types: CI shape equals local shape, both exit 1.
  - `plans` (`badname.ipd.md`), `releases` (`bad.release.md`), and `backlog` (`bad.backlog.md`) all emit `check.name-nonconformant`.
  - A conforming backlog item with `Blocks-Release: zzzzzz` emits exactly `check.blocks-release-dangling` under `release-gates`.
- Clean tree: a repo with `.aw/records/` exits 0 in both shapes for all four types.
- Deleted recipe: `index plans --dir <bare repo>` raised `FileNotFoundError`, and `check` on a repo without `.aw/records/` exits 2 (`cannot-run`) in both shapes.
- Import resolution: an unpinned `import agent_workflows` from a temp cwd resolved to a different checkout's editable install.
- `rg` finds no `CI`/`GITHUB_ACTIONS` read anywhere in `agent_workflows/`.
- One `check` subprocess took about 0.55s.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Test validity / mutation reachability | E-01 old `_run` used bare `subprocess.run([sys.executable, "-m", "agent_workflows", ...])` with CI-shape cwd = temp repo; probe: unpinned import from a temp cwd resolved to an editable install outside this tree; `tests.support.run_cli` docstring (IPD `lhjsu0`, bug `ccbe60`) | In the CI shape the subprocess imports a different `agent_workflows` than the local shape, whose cwd is this checkout. The two shapes therefore run different code. A parity failure could come from version skew, and the E-04 scratch mutations would never reach the CI shape. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now routes both shapes through `tests.support.run_cli` (pinned `PYTHONPATH`), uses `support.init_repo` under a `TemporaryDirectory`, and parses the last JSON line. V-01 demands the excerpt showing this. |
| PR-002 | HIGH | IN-SCOPE | E. Testing feasibility | E-03 old recipe "empty temporary repo with ... `index plans --dir <repo>`"; probe: `FileNotFoundError` on AW_HOME `records/plans/INDEX.json`, then exit 2 `cannot-run` (`next: aw install .`) in both shapes | Following the clean-tree recipe as written cannot reach exit 0. Equal-exit parity would then pass vacuously on exit 2 while the stated exit-0 assertion fails. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now seeds an empty `.aw/records/` directory, which review measured at exit 0 in both shapes for all four types, and explicitly forbids the deleted recipe. V-03 demands the exit-0 assertion. |
| PR-003 | MEDIUM | IN-SCOPE | E. Seed precision / mutation feasibility | E-02 old release-gates seed "a backlog item carrying a `- Blocks-Release:`" (a nonconforming item also emits backlog-family findings); E-04 old mutations named no site | The release-gates seed did not say the item must otherwise conform. E-04's mutations named no code location, which leaves the executor to invent architecture. E-02 also did not rule out cannot-run-vs-cannot-run as a vacuous pass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now gives the exact conforming seed (reproduced at review) and per-type target rules, and excludes exit 2. E-04 places both mutations in `check_engine.check_type` before it returns, using `Drift._replace` for (b). |
| PR-004 | MEDIUM | UNDER-SCOPE | G. Lifecycle gate | `check_engine.evaluate_durable_carrier` via `aw ipd lint --phase pre-transition`: `check.ipd-uncarried-obligation ... deferred row 1, deferred row 2, deferred row 3` | None of the three Deferred rows had a carrier field, so the plan could never pass its own pre-transition gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a reasoned `Carrier-Declined` to each row. Pre-transition now reports only `IPD-S404`. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; OQ-01 `- Owner: none` | The gate lacked a scope fence, the honesty rule, the explicit commit paths, a check of the staged set, conditional finalize ownership, and the backlog handoff. OQ-01's owner was a placeholder. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the full contract, including mutation-revert-before-commit. Set the owner to `plan author`. Added F-6, recording that no code reads `CI` today. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What is the clean-tree fixture, given the deleted recipe no longer works? | A git repo with only an empty `.aw/records/` | `aw install <repo> --yes` (also exit 0 at review, but slower and drags in install behavior); the old `index plans` recipe (fails) | Review probe: `.aw/records/` alone gives exit 0 in both shapes for all four types | yes |
| D-2 | Keep the `CI`/`GITHUB_ACTIONS` env limb although no code reads it? | Keep it | Drop it (that would lose the guard against a future CI-conditional branch, which is exactly what mutation (a) models) | `rg` finds no reader today; the CI job sets these variables | yes |
