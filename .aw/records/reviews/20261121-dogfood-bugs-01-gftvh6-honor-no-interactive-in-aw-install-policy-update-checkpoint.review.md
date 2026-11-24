# Review findings: ipd gftvh6

- Subject-Id: gftvh6
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: opencode/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at local HEAD `005bd41ed` (the `d8b9rp` review commit, on top of `34792ea0b`), in an isolated runner review-sweep lane worktree. That commit touches no file this plan cites. The target plan `.aw/records/plans/pending/20261121-dogfood-bugs-01-gftvh6-honor-no-interactive-in-aw-install-policy-update-checkpoint.ipd.md` was committed and clean at turn start (last changed in `6efa5700e`), so no pre-review snapshot commit was needed. It is Order 1 of Set `dogfood-bugs` (orchestrator `p2zmjs`), graduated from backlog `n5tqib`, and carries `- Blocks-Release: next`. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings).

The central result: the fix this plan describes already landed in executed plan `rznd0q` (commit `90132cb4f`, 2026-11-21), which names this plan as its compatible sibling. The plan is rewritten as a regression lock that covers the two cases existing tests miss: `--no-interactive` without `--dry-run`, and a real PTY. This is the same shape the `c74ey2` review chose.

AW-TIER: standard

### Step T

1. Yes, minor: one CHANGELOG bullet. No flag, schema, or spec text changes.
2. No: the plan adds tests and changes production code only if a test fails.
3. No: four E-items, one new test module, one changelog line, and a conditional fix.
4. Yes: `- Scope-Paths:` is present. Review added the new test module and `CHANGELOG.md`, and kept the two production files for the conditional E-03.
5. Low: tests only, with a timeout on the child-process case.

`AW-TIER: standard`

### Step R1

- Checked: `agent_workflows/install_wizard.py::collect_policy_interactive` (987; parameters 1001-1002; `forced_noninteractive` 1008-1012; non-interactive return 1022); `agent_workflows/cli.py` install call (9709-9721), early-flag `interactive_override` (21199-21207), `term.set_interactive_override` (21330); `agent_workflows/term.py::set_interactive_override` / `get_interactive_override` (1953, 1959); executed plan `.aw/records/plans/executed/20261121-3z57rk-01-rznd0q-preserve-dry-run-and-non-interactive-invariants-in-legacy-aw.ipd.md` (E-01, line 111 sibling note); `tests/test_install_dry_run_noninteractive.py` (10 tests); `tests/test_agent_turn_noninteractive_pty.py` (PTY harness); `tests/test_stdin_interactive.py`; backlog `n5tqib`; siblings `qw9i5p`, `ippuby`; orchestrator `p2zmjs`.
- Found F1: E-01 asks to add `interactive: Optional[bool] = None` to `collect_policy_interactive`, which already has it (line 1001) and already honors it together with the process-wide override and `AW_NONINTERACTIVE` / `CI` (lines 1008-1012). `git log -L` attributes this to `90132cb4f` (`rznd0q`). Fixed: rewritten as regression tests with a conditional fix (E-01 to E-03).
- Found F2: E-02 asks to pass `interactive=ctx.interactive` from `cli.py`. There is no `ctx.interactive` in `cli.py` (`grep -c` returned 0). `--no-interactive` reaches the wizard through `term.set_interactive_override(False)` (line 21330). Step 0's claim that the CLI does not carry the decision was false. Fixed: Step 0 and the diagram describe the real path.

### Step R2

- Checked: the E/V bijection after revision (E-01..E-04 to V-01..V-04, `Highest E allocated: 04`), `Depends on` order, Scope-Paths completeness, and V-item evidence specificity.
- Found F3: E-03 and Required tests cited `tests/test_install_wizard_noninteractive.py tests/test_install_wizard*.py`. Neither the file nor the glob matches anything (`ls` failed on both), and `python3 -m pytest tests/test_install_wizard*.py` ran no tests. Bare `python3 -m pytest <file>` also hides per-test lines. Fixed: precise files with `-o addopts=""`.
- Found F4: the test module named in the plan would not be `core`-marked, so the bare routine gate would skip it. The existing `tests/test_install_dry_run_noninteractive.py` has the same gap (`--collect-only -m core` collected 0 of 10). Fixed: E-01 sets `pytestmark = pytest.mark.core`; marking the older module is declined in Deferred.

### Step R3

- Checked (short form): the tests run `aw install` against a temporary repository with an isolated `HOME`, `AW_HOME`, and XDG directories, so no user configuration is read or written. The PTY child is killed at a deadline. No credential, network, or shell interpolation.
- No security finding.

### Step R4

- Checked by probe at `005bd41ed`, with `AW_NO_REEXEC=1`, `CI` and `AW_NONINTERACTIVE` unset, and an isolated `HOME`. In process, simulated TTY, installed repository: `install --no-interactive` returned 0, printed no checkpoint, left `.aw/` unchanged, and left `git status` clean. With no flag, the first prompt was `Keep current policy and proceed? [Y/n/review] `. On a real PTY child process: `--no-interactive` exited 0 in 0.3 s (ending `aborted; nothing changed.`), and `--no-interactive --dry-run` exited 0 in 0.3 s (ending `[DRY RUN] No changes written ...`). With no flag, the run was still waiting at the checkpoint after 40 s. A fresh repository with `--no-interactive` failed closed with exit 1 and `Noninteractive first install requires complete policy choices`, without prompting. `tests/test_install_dry_run_noninteractive.py` ran 10 passed and `tests/test_stdin_interactive.py` ran 5 passed.
- Found F5: the existing tests cover only `--dry-run` spellings in the CLI and never run on a real PTY, which is the reported environment. The user-visible fix also had no CHANGELOG entry (`grep "Keep current" CHANGELOG.md` found none). Fixed: E-01 case (a) covers the non-dry-run spelling, with control case (b) proving the TTY simulation reaches the checkpoint; E-02 adds a real-PTY test; E-04 adds the bullet.
- Found F6: sibling `qw9i5p` depends on `executed:gftvh6` because "both plans edit `agent_workflows/install_wizard.py`", and its Required tests use the same empty glob. Outside this plan's Scope-Paths. Deferred to `qw9i5p` with a `Carrier:` line.
- Found F7: orchestrator `p2zmjs` describes this child as threading `ctx.interactive` (child table row 01, E-01 expected outcome). Outside Scope-Paths. Deferred to `p2zmjs` with a `Carrier:` line.

### Proofreading

Checked the plan against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Title, Short-Description | Thread `ctx.interactive` into the wizard | Lock in never-prompting with regression tests | F1, F2 |
| Concern, Scope, Scope-Paths | Code change in two files; nonexistent test file | Already fixed by `rznd0q`; new test module, conditional fix, changelog | F1, F3, F5 |
| Goal and diagram | Diagram of a proposed parameter | Two testable outcomes; diagram of the real override path | F2; requirement 12 |
| E-01..E-04 | Add parameter, pass `ctx.interactive`, vague tests | TTY tests with control, PTY tests, conditional fix, changelog | F1, F2, F4, F5 |
| Step 0 | Two false claims about current code | Measured code path, probes, existing coverage gaps | F1, F2, F3, F4 |
| Deferred | Two carriers | Plus declined core-marking and the `qw9i5p` and `p2zmjs` carriers | F4, F6, F7 |
| Scope check, Required tests, Spec sync | "none"; empty glob; "N/A" | Accurate scope; precise commands; changelog note | F3, F5 |
| V-01..V-04 | Diffs of code that already exists | Per-case evidence and fail conditions | F1, F4 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |

### Step S5

- Checked: the plan has no open questions. The judgement calls are recorded in Decisions D1 to D3 and are reversible. Every expected outcome was demonstrated by probe at HEAD. Nothing needs a human answer before approval.

### Pass 2

- Re-read the revised plan end to end. The case list (a) two parameters plus (b) one control, and the two PTY parameters, add up to the five cases named in E-03, and the same names appear in V-01 and V-02. The first `aw ipd lint --phase review-finalize` reported advisory `IPD-C801` on a bare line-range citation; the citation now names the test symbol. A second run returned `clean` (exit 0, 0 findings).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | HIGH | IN-SCOPE | R1 / Already fixed | agent_workflows/install_wizard.py:1001-1012; `git log -L` -> 90132cb4f (rznd0q) | The parameter and gating E-01 asks for already exist. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Rewritten as a regression lock with a conditional fix. |
| F2 | HIGH | IN-SCOPE | R1 / Nonexistent symbol | `grep -c "ctx.interactive" agent_workflows/cli.py` -> 0; cli.py:21330 | E-02 passes a value that does not exist; the real path is the process-wide override. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Step 0 and diagram describe the real path. |
| F3 | MEDIUM | IN-SCOPE | R2 / Test commands | `ls tests/test_install_wizard*.py` -> no match | Required tests named files that do not exist, so validation would run nothing. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Precise files with `-o addopts=""`. |
| F4 | MEDIUM | IN-SCOPE | R2 / Test tier | `pytest --collect-only -m core tests/test_install_dry_run_noninteractive.py` -> 0 collected | Without a `core` marker the routine gate skips the regression tests. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | New module sets `pytestmark = pytest.mark.core`. |
| F5 | MEDIUM | UNDER-SCOPE | R4 / Coverage and docs | tests/test_install_dry_run_noninteractive.py (only `--dry-run` CLI cases, no PTY); CHANGELOG.md | The reported environment (real PTY) and the non-dry-run spelling were untested, and the fix had no release note. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-01 (a)/(b), E-02, E-04. |
| F6 | LOW | OUT-OF-SCOPE | R4 / Sibling consistency | qw9i5p Item-Dependencies rationale and Required tests glob | Sibling cites an edit this plan no longer makes and the same empty glob. | C:Low;U:Low;S:Low;F:Low;Overall:Low | DEFERRED | Carrier `qw9i5p`. |
| F7 | LOW | OUT-OF-SCOPE | R4 / Orchestrator consistency | p2zmjs child table row 01, E-01 expected outcome | Orchestrator describes the old code change. | C:Low;U:Low;S:Low;F:Low;Overall:Low | DEFERRED | Carrier `p2zmjs`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D1 | What does a plan for an already-fixed bug do? | Regression lock with a conditional fix | Retire as not-executed; keep the code change | The release gate travels with the item; tests prove the fix holds, matching the `c74ey2` review | yes |
| D2 | Simulated TTY, real PTY, or both? | Both | Simulated only (fast, but not the reported setting) | The bug was reported on a PTY; the PTY probe ran in 0.3 s | yes |
| D3 | Mark the existing `rznd0q` tests `core`? | No; mark only the new module | Mark both | Tier membership for another plan's tests is a separate decision | yes |
