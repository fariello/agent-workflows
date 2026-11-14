# Review findings: plan n0li9v

- Subject-Id: n0li9v
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `527977905` in a non-interactive runner review-sweep lane worktree. The tracked plan was committed and unmodified, so the pre-review snapshot commit was skipped. `aw ipd lint --phase author --agent` returned `clean` (0 findings) before edits; `aw ipd lint --phase review-finalize --agent` returned `clean` (0 findings) after edits. All five `- Item-Dependencies:` exist; `j2xjtt` (Order 173, `reviewed`) depends on `y3uowx` (Order 172, `reviewed`, creates `tools/fixture_codemod.py`), so the tool dependency is transitive. Neither `tools/fixture_codemod.py`, `tests/test_fixture_codemod.py` nor `tests/fixtures/fixture_codemod/` exists yet, as expected.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Checklist preamble | "Item ids E-01 to E-04 ... New ids ... start at E-07" (this plan has E-11 to E-13) | States E-11..E-13 come from the split, points E-03/E-05 and F-01/F-03/F-06 at their owning plans | PR-004 |
| Checklist preamble (new) | Tool path, fixture naming, sites per fixture and byte comparison unstated | FIXTURE RULES (1) to (4) | PR-001, PR-002, PR-003 |
| E-11, E-12 | "Tests drive the tool as a subprocess ..." | Prefixed with "Follow the FIXTURE RULES above." | PR-001..PR-003 |
| E-13, V-13 | No duration check | `--durations=0`, the `j2xjtt` 10 s bound and its slow-module rule | PR-005 |
| V-11, V-12 | No naming check | Adds `git ls-files tests/fixtures/fixture_codemod` showing no `test_*.py` fixture | PR-001 |
| Approval and execution gate | Transition without "never a hand `git mv`" and runner/hand ownership | Both added | PR-005 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No. Tests only; no CLI, output or file-format contract changes.
2. No.
3. No. Three E-items, one test module and one fixture directory.
4. Yes. `tests/test_fixture_codemod.py`, `tests/fixtures/fixture_codemod/**`, the plan.
5. Mildly. Collectible fixture modules would leak into every `-m ""` run, and the batch plans size their hand work by these refusal codes.

AW-TIER: standard

### Step R1

- Checked: `y3uowx` E-01 CLI (`python3 tools/fixture_codemod.py --dry-run [--format table|json] <paths>` and `--apply`), the reason-code table (identical to `y3uowx`'s), `j2xjtt` E-04 `CODEMOD_PATH` convention, `pyproject.toml` `testpaths = ["tests"]` and `addopts` `-m 'not slow and not livecorpus'`, root `conftest.py::pytest_collection_modifyitems` (bare run selects only `core`), and the absence of any `test_*.py` under `tests/fixtures/`.
- Found the tool path unnamed (PR-002) and an id-carry paragraph describing ids not in this plan (PR-004).

### Step R2

- Checked: E/V bijection (3/3), dependency chain E-11 -> E-12 -> E-13, evidence concreteness, gate contract.
- A fixture stored as `tests/fixtures/fixture_codemod/test_*.py` is collected under `testpaths = ["tests"]`; a bare run deselects it (unmarked), but every `-m ""` run, including the `59aiyh` batch rule's full-suite comparison, would run deliberately legacy modules and may hit duplicate-basename import errors. The `legacy-format subject` code is decided by module NAME (`*legacy*`), so the name at tool time matters too (PR-001).
- "Exactly that reason code ... for the fixture's site" was ambiguous for a fixture with several sites (PR-003).
- Six new subprocess cases join `j2xjtt`'s module, whose E-10 sets a 10 s bound; this plan did not re-check it (PR-005).

### Step R3

- Checked: no production code, secrets, git operations beyond `aw commit n0li9v`; subprocesses run in `init_repo` temporary repositories. No security finding.

### Step R4

- Checked: behavior-not-structure (subprocess runs, JSON output, bytes on disk; `rg -n "inspect\.|getsource"` empty demanded); right-sizing (3 E-items, 3 codes per item).

### Step R7

- Checked: `j2xjtt` (cases (a)-(c), (e)-(h), 10 s bound), `y3uowx` (tool), `653ndz` (pilot, census; depends on `n0li9v`). Cross-plan note: `j2xjtt` E-04/E-08/E-09 also add fixture modules under `tests/fixtures/fixture_codemod/` without a naming rule; FIXTURE RULE (2) tells this plan's executor to keep its own fixtures non-collectible regardless. `j2xjtt` is outside this review's ledger and was not edited.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Test isolation | `pyproject.toml` "testpaths = [\"tests\"]"; n0li9v E-11 "one fixture module under `tests/fixtures/fixture_codemod/` per static refusal reason code"; reason-code table `legacy-format subject` "`*legacy*`" | Fixture modules named `test_*.py` would be collected by every `-m ""` run, and the name-based `legacy-format subject` code needs a specific module name at tool time | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | FIXTURE RULE (2): non-collected stored names, copied as `tests/test_<name>.py` (a `*legacy*` name for that code); V-11/V-12 check `git ls-files`. Strength: strong |
| PR-002 | LOW | UNDER-SCOPE | Executability | n0li9v E-11 "Tests drive the tool as a subprocess" with no path; `j2xjtt` E-04 defines `CODEMOD_PATH` | The tool path and interpreter were unstated | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | FIXTURE RULE (1). Strength: strong |
| PR-003 | LOW | IN-SCOPE | Validation precision | n0li9v E-11 "reports exactly that reason code with that disposition for the fixture's site" | Ambiguous when a fixture holds several sites; byte-identity scope unstated | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | FIXTURE RULES (3) one site per fixture, (4) whole-module byte comparison. Strength: strong |
| PR-004 | LOW | IN-SCOPE | Honest documentation | n0li9v preamble "Item ids E-01 to E-04 are the ids these items had in `653ndz`" | Describes ids this plan does not contain; F-01/F-03/F-06 and E-03/E-05 unanchored | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten with owners named. Strength: strong |
| PR-005 | LOW | UNDER-SCOPE | Execution contract / test budget | `j2xjtt` E-10 Expected outcome "total duration under 10 s or the moved slow module listed"; n0li9v gate "Lifecycle transition" | Adding six subprocess cases did not re-check the 10 s bound; transition lacked hand-`git mv` ban and finalize ownership | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-13/V-13 run `--durations=0` and apply `j2xjtt`'s slow rule; gate updated. Strength: strong |

### Step S5

- Checked: OQ-01 and OQ-02 (`Blocking: no`, `resolved`); both still accurate. No human-owned question arose.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should fixture modules avoid pytest collection? | Store under a non-collected name (for example `*.py.txt`) and copy to `tests/test_<name>.py` in the temporary repository | A `conftest.py` with `collect_ignore` under `tests/fixtures/fixture_codemod/` (rejected: adds a conftest where the repository has none under `tests/`, per this plan's carried conventions); `pytest.ini` `norecursedirs` change (rejected: global configuration change outside scope) | `pyproject.toml` `testpaths`; `conftest.py::pytest_collection_modifyitems` | yes |

### Step S6

- Re-read E-11..E-13, V-11..V-13 and the gate after edits; `grep` for "E-07" and the old id-carry wording found no stale sibling. No new finding.
- `AW-REVIEW: DONE`
