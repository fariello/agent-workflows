# Review: Restore the packaging boundary coverage the wheel guard does not reach

- Subject-Id: d0lg63
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `1d7b5f1d4`:

- `tests/test_packaging.py` holds the wheel-only guard: `setUpClass` skips when `build` is missing and asserts on a build failure.
- `tests/` contains no hit for `run_analytics_assets`, `entry_points.txt` or `--sdist`.
- The sdist `include` allowlist matches the plan, and `REQUIRED_ASSETS == ("app.css", "app.js")`.
- `[project.scripts]` lists exactly three scripts.
- The wheel builds in 3.2s and the sdist in 4.0s, both into gitignored `.aw/state/` scratch.
- The wheel ships `app.css` (5235 bytes) and `app.js` (21944 bytes). `entry_points` parses to the three scripts, all mapped to `agent_workflows.cli:main`.
- The sdist's top-level entries are `.aw .gitignore LICENSE NOTICE PKG-INFO README.md agent_workflows hatch_build.py pyproject.toml`, with no `tests/`. It contains both assets and `.aw/system`.
- `layout_migration.py` and `layout_inventory.py` are present in both artifacts.
- I reproduced the `.gitignore` probe with hatchling 1.32.4: it exits 0 and the wheel contains `['pkg/assets/kept.css']` only.
- I removed the scratch afterwards and `git status --short` was clean.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Honesty of deferral (G) | plan Deferred row 3 "E-04's module list asserts exactly that"; E-04 listed only `run_analytics_spa.py`/`run_analytics_report.py` | The carrier-declined row says the durable half of the dropped import arms (`layout_migration`/`layout_inventory` ship) is covered. No item asserted it, so that claim was false and the coverage would have been lost silently. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 (wheel) and E-04 (sdist) now assert the four modules by name, all measured present. Deferred row corrected. |
| PR-002 | LOW | IN-SCOPE | Right-sizing (G) / validation | E-05 bundled the console-script arm with the full-suite run; V-05 likewise; "no newly failing test" bar | E-05 bundled two independent surfaces, and the suite bar was not stated as a set of test ids. | Low | FIXED | Split out E-06/V-06 for the bare suite, with an empty failure-set delta stated as test ids. E-05 now asserts mapping EQUALITY, which also catches a stray fourth script. |
| PR-003 | LOW | IN-SCOPE | Cost honesty / hygiene | OQ-02 "roughly 11 seconds"; OQ `Owner: none` | The cost statement omitted the third build, the E-03 probe, whose isolated build env resolves `hatchling` from the index. The resolved OQs named no owner. | Low | FIXED | OQ-02 now names all three builds and the network resolution. Owner set to `plan author`. E-04 notes the member-normalization rule and the re-measured sdist contents. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the layout modules be covered, or the deferral claim weakened? | Cover them by name in both artifacts | Rewrite the deferral to admit the loss (no reason to lose cheap coverage) | Both modules measured present in the wheel and sdist at review | yes |
| D-2 | Should E-03's probe stay in the default suite, given it resolves hatchling from the network? | Keep it, as authored, with its skip-on-probe-unavailable | Mark it `slow` (loses the gate, per `tests/test_packaging.py` docstring reasoning) | Probe reproduced at review; deleted test's `skipTest` on nonzero probe exit | yes |
