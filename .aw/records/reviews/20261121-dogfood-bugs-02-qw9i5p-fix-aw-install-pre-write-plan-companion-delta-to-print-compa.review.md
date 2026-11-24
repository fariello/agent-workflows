# Review findings: ipd qw9i5p

- Subject-Id: qw9i5p
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: opencode/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at local HEAD `6c3c2c1b0` in an isolated runner review-sweep lane worktree. The target plan `.aw/records/plans/pending/20261121-dogfood-bugs-02-qw9i5p-fix-aw-install-pre-write-plan-companion-delta-to-print-compa.ipd.md` was committed and clean at turn start, so no pre-review snapshot commit was needed. It is Order 2 of Set `dogfood-bugs`, graduated from backlog `479wfb` (`Work-Kind: bug`), and carries `- Blocks-Release: next`. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings).

The defect is real and reproduces at HEAD. With `--companion-dir <TD>/priv`, the `records` row of the pre-write plan reads `<TD>/priv/records/` while `Companion Delta:` reads `<TD>/priv/.aw/records and config created/updated.` (`<TD>` is the temporary directory). The plan's one-line fix was right in direction, but its test recipe could not reach the companion branch, its test glob matched no file, and its "companion config" wording claimed a write the installer does not make.

AW-TIER: standard

### Step T

- Checked: the five tier questions in `steps/t-tier.md`.

1. No: no flag, reason code, or spec text changes; one CHANGELOG bullet is added at review.
2. No: preview text only; nothing the installer writes changes.
3. No: three E-items, three work Scope-Paths.
4. Yes: `- Scope-Paths:` is present; review added `CHANGELOG.md`.
5. Low: one formatted line in one function.

`AW-TIER: standard`

### Step R1

- Checked: `agent_workflows/install_wizard.py::render_pre_write_plan` (the `resolved_roots` build from `resolve_project_context(...).physical_classes`, the `records` row, and the `Expected Deltas` companion branch); both callers (`cli.py` dry-run preview and the wizard in `install_wizard.py`); `get_preset_defaults` and `ProjectPolicy` defaults; `storage.attach_companion` and the `cli.py` attach block; existing tests that call `render_pre_write_plan` (`tests/test_install_consent_truth.py`, `tests/test_records_untracked_backend.py`); sibling plan `gftvh6` and orchestrator `p2zmjs`.
- Reproduced at HEAD through `render_pre_write_plan` and through `aw install --dry-run` in a throwaway repository, with an explicit companion directory and with the default `<repo>.aw` companion. Both print `/.aw/records`; the default case prints `<TD>/t.aw/.aw/records ...`.
- Found F1: the plan's proposed text, `{comp_path}/records/ and companion config created/updated.`, names a "companion config" that is never written. Measured: with `--companion-dir`, the install writes `records/`, `.gitignore`, `.aw/companion_identity.json` and runs `git init`; with the default companion, only `records/`. No case writes a config file. It also re-derives the path by hand, so it can drift from the `records` row again. Fixed: E-01 takes the path from `resolved_roots["records"]` (the same value the row prints) with a `comp_path` fallback for a failed resolver, and drops "and config". DF-04a records the evidence.
- Noted F6 (not fixed in this plan): with the default companion, `<repo>.aw/` gets `records/` but no `git init`, identity file, or `.gitignore`, while the preview labels `records` as `companion-git`. This is a different code path from the preview text. It is recorded in Deferred and raised as a non-gating question for human triage, because filing a backlog item is outside this review's edit authority.

### Step R2

- Checked: the E/V bijection, `Depends on` edges, Scope-Paths, test placement and tier marker, fail-before proof, and whether each V-item demands concrete evidence.
- Found F2: a test built as `ProjectPolicy(preset="public-target-private-companion")` keeps `records_backend="repository"` and renders `Companion Delta:  None.` (measured), so a test following the authored wording could pass without reaching the bug. Fixed: E-02 builds each policy from `get_preset_defaults(preset)` and states why.
- Found F3: the required test command `tests/test_install_wizard*.py` matches no file at HEAD. Fixed: Required tests name the real neighbouring callers, plus `tests/test_install_no_interactive_tty.py` once `gftvh6` adds it.
- Found F4: no step proved the new test fails without the fix, and no tier marker was set. Fixed: E-01 records the base commit; E-02 adds `pytestmark = pytest.mark.core` and runs the module at the base commit in a `mktemp -d` worktree; E-02's expected outcome says (a) and (b) fail there and (c) passes.
- Found F5: no CHANGELOG entry for a user-visible preview fix, unlike sibling plans `gftvh6` and `p0hq1k`. Fixed: new E-03 and V-03; `CHANGELOG.md` in Scope-Paths.

### Step R3

- Checked (short form): no input parsing, subprocess, network, or credential change. `aw sanitize --agent` was run at finalize.
- No security finding.

### Step R4

- Checked: both callers of `render_pre_write_plan` get the fix through the one function. `Item-Dependencies: executed:gftvh6` matches orchestrator `p2zmjs` ordering. Deferred carrier `ippuby` exists in `pending/`.

### Step S5

- Checked: the plan has no open questions. The one decision this review made (D1) is reversible. F6 is a separate observation for triage and does not gate this plan.

### Pass 2

- Re-read the revised plan end to end. E-01, E-02, E-03 map one-to-one to V-01, V-02, V-03, and `Highest E allocated: 03`. The flowchart uses decision shapes for both branches. `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings) after the edits.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | MEDIUM | IN-SCOPE | R1 / Wrong replacement text | Throwaway installs: companion receives no config file; `records` row path already in `resolved_roots` | The proposed "and companion config" names a write that does not happen, and the hand-built path can drift from the `records` row. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-01 uses `resolved_roots["records"]` with a `comp_path` fallback and drops "and config"; DF-04a added. |
| F2 | MEDIUM | IN-SCOPE | R2 / Test reaches the bug | `ProjectPolicy(preset=...)` renders `Companion Delta:  None.` | A test following the authored wording could pass without exercising the companion branch. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-02 builds policies from `get_preset_defaults`. |
| F3 | LOW | IN-SCOPE | R2 / Dead test glob | `ls tests/test_install_wizard*` finds nothing | The neighbouring-suite command ran no existing preview test. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Required tests and V-02 name the real modules. |
| F4 | LOW | IN-SCOPE | R2 / Fail-before proof and tier | No base-commit run; no marker | Nothing showed the test catches the bug, and the bare gate would skip it. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Core marker; base-commit run in a `mktemp -d` worktree. |
| F5 | LOW | IN-SCOPE | R2 / User docs | Sibling bug plans add `- Fixed:` bullets | A user-visible fix had no CHANGELOG entry. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | New E-03 and V-03; `CHANGELOG.md` in Scope-Paths. |
| F6 | LOW | OUT-OF-SCOPE | R1 / Adjacent behaviour | Default-companion install: `<repo>.aw/` has only `records/`, no `.git`; preview says `companion-git` | The default companion is not initialized as a git repository although the preview says its records are git-tracked. | C:Low;U:Low;S:Low;F:Low;Overall:Low | DEFERRED | Recorded in Deferred; raised as non-gating question `default-companion-git` for human triage. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D1 | Where should the delta line get its path? | `resolved_roots.get("records")`, falling back to `f"{comp_path}/records/"` | Hardcode `{comp_path}/records/` as authored | The row and the delta then cannot disagree, which is the defect itself; the fallback keeps output when the resolver fails | yes |

### Proofreading

Checked the plan against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Front matter | Two work Scope-Paths; `Highest E allocated: 02` | Adds `CHANGELOG.md`; `03` | F5 |
| Scope, Goal | Display `records/` | Same path as the `records` row; drop "and config" | F1 |
| E-01 | Format-string change to "and companion config" | Path from `resolved_roots`; records base commit | F1, F4 |
| E-02 | One sentence naming the module | Exact policy construction, three cases, base-commit run | F2, F4; requirement 4 |
| E-03 | (none) | CHANGELOG bullet | F5 |
| Conventions, Findings | Authoring observation only | Measured install writes, callers, real test modules; DF-04 reproduced, DF-04a added | F1, F3 |
| Proposed changes | Text list | Flowchart with decision shapes plus list | requirement 12 |
| Deferred, Scope check, Required tests, Spec sync, V-items | Dead glob; no fail-before evidence | Real modules; default-companion observation; V-01 to V-03 with concrete evidence | F3, F4, F6 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |
