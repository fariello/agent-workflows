# Review findings: ipd mx7azn

- Subject-Id: mx7azn
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran non-interactively in an isolated review-sweep lane worktree (run `run-20261124T195117Z-1319864`, HEAD `a98989734`). The target plan `.aw/records/plans/pending/20261121-517n5n-01-mx7azn-verify-aw-meta-repair-subparser-description-and-required-lea.ipd.md` was committed and unmodified (last commit `512763389`), so no pre-review snapshot commit was made. Before edits, `aw ipd lint --phase author --agent` returned `clean` with two `IPD-C802` info advisories (em dashes in the runtime-demonstration reachability rule sentence). After edits, it returned `clean` with zero findings.

The review read backlog item `517n5n` (graduated, `Work-Kind: bug`, `Blocks-Release: next`), `agent_workflows/cli.py::_build_parser` (`p_meta_repair`), `tests/test_cli.py::SubcommandDescriptionTests.test_every_subparser_has_fuller_description`, `tests/test_usage_refusal_agent_record.py::test_exclusion_set_size_and_members` and `_discover_required_arg_leaves`, and the markers on the four test modules the plan runs. Measured at review HEAD:

- `git merge-base --is-ancestor 0cb279ae0c1f2778e89b862ea80cb80f555ef733 HEAD` exits 0; `0cb279ae0` is dated `2026-11-21 00:11:45 -0500`, after `6de2e014d` (`2026-11-20 23:51:17 -0500`).
- `test_exclusion_set_size_and_members` asserts `len(REQUIRED_LEAVES) == 72`, not `70`. `git log -S'== 72'` names `6be40f11b` (`feat(724acb): add dormant aw reviews record and aw walkthrough new`). `REQUIRED_LEAVES` has 72 entries and contains `"meta repair"`.
- `meta repair` description is 280 characters against a 92-character help; `meta` is 201 against 62 (the plan said 278 and 206).
- `python3 -m pytest -o addopts="" -p no:randomly -n 0 tests/test_cli.py -k SubcommandDescriptionTests`: `2 passed, 63 deselected in 0.29s`.
- `python3 -m pytest -o addopts="" -p no:randomly -n 0 tests/test_usage_refusal_agent_record.py -k "test_exclusion_set_size_and_members or (test_required_arg_leaf_modes and meta)"`: `2 passed, 185 deselected in 0.23s`.
- `--collect-only` of the plan's `tests/test_shared_flag_honored.py -k "... and meta"` selector collects exactly 1 test.
- Only `tests/test_cli.py` is slow-marked; `tests/test_meta_repair_cli.py` is core-marked, and the other two carry no module marker, so the plan's plain `python3 -m pytest <paths>` commands run them.

`AW-TIER: simple`
`AW-REVIEW: DONE`

### Step T

1. No: the plan changes no spec, interface, or contract; it edits only itself.
2. No: it touches no guard module and writes no code.
3. No: 3 E-items in one task group, all verification commands.
4. Yes: `- Scope-Paths:` names only the plan file.
5. No: a mistake loses nothing; the plan stops and reports on any failure rather than editing code.

Tier: simple.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern | Implied the count stays `70` | Notes `6be40f11b` raised the pinned total to `72` with `meta repair` still a member | PR-001 |
| Short-Description | "REQUIRED_LEAVES=70" | "REQUIRED_LEAVES count" | PR-001 |
| Goal | "keeps `REQUIRED_LEAVES` at `70`" | Keeps `meta repair` counted; the pinned total is `72` | PR-001 |
| E-02 expected outcome | Silent on the total | A pass at a total other than `70` is expected, not drift | PR-001 |
| E-03 and V-03 | Ran pre-transition lint inside the item it gates; repo-wide `git status --short` | Lint moved to the gate; `git status --short -- agent_workflows tests` must be empty | PR-002, PR-003 |
| Project conventions, F-02, F-03 | 278/206 characters; count `70` | 280/201 measured; history through `72` | PR-001, PR-004 |
| Ordered changes 3, flowchart, Required tests | `aw ipd lint` among the E-03 gates | Lifecycle gate listed separately | PR-002 |
| Deferred row 1, OQ-01, Spec sync | Stated `== 70` as current | States it is now `== 72` | PR-001 |
| Validation rule sentence | Two em dashes | Commas and parentheses | `IPD-C802` |
| POST-GATE LIFECYCLE | Finalize without `aw ipd begin` | Runner owns begin and finalize; a standalone executor runs begin, then the evidence commit, then finalize | PR-002 |

#### Issues

- None remaining. Lint reports zero findings after revision; the plan contains no em or en dashes.

### Step Q

- Checked: what the change could break and what depends on it. The plan edits no code, so it can break nothing at runtime; the risk is a false verdict. Two paths led there. First, the plan pinned `REQUIRED_LEAVES` at `70` in its Goal and Short-Description while HEAD pins `72`, so an executor reading the Goal literally could report a regression on a passing test, or "fix" it back to `70` (PR-001). Second, E-03 required `aw ipd lint --phase pre-transition` to report `conforming` while E-03 itself is still `pending`, which that lint refuses, so the item could never be marked performed in order (PR-002). E-03's repo-wide `git status --short` would also show the plan file the executor is required to edit, plus lane-runner state, so "zero edits" was not checkable as written (PR-003). The character counts were off by a few characters (PR-004); the test's `len(desc) > len(hlp)` condition holds either way.
- Checked: the `0cb279ae0` ancestry and timeline claims, the test selectors (each collects the tests the plan names), the `-o addopts=""` requirement for slow-marked `tests/test_cli.py`, and backlog `rryabb` (exists) for the deferred thorough-suite row. All hold.

### Step S5

- Checked: no question needs a human. OQ-01 stays resolved (verify only); its rationale now cites the current count.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | MEDIUM | IN-SCOPE | Correctness of the verification target | `tests/test_usage_refusal_agent_record.py::test_exclusion_set_size_and_members` asserts `== 72`; `git log -S'== 72'` names `6be40f11b` (`724acb`); `REQUIRED_LEAVES` has 72 entries including `meta repair` | The Goal and Short-Description say the count stays `70`, which is false at HEAD and invites a false regression report or a wrong edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Goal, Concern, Short-Description, E-02, F-03, Deferred, and OQ-01 verify membership of `meta repair` and accept the pinned total. |
| PR-002 | MEDIUM | IN-SCOPE | Lifecycle | Pre-transition lint refuses a `pending` E-item; `aw ipd finalize --help` validates a matching `aw ipd begin` receipt | E-03 ran the lint that gates E-03 itself, and the gate ordered finalize without begin. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Lint moved to the gate's POST-GATE LIFECYCLE clause, with runner-owned begin/finalize or begin, evidence commit, finalize by hand. |
| PR-003 | LOW | IN-SCOPE | V reachability | The executor must edit the plan file (in Scope-Paths); a lane also writes runner state | "`git status --short` shows zero edits to Python source or test files" was not checkable from repo-wide output. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and V-03 use `git status --short -- agent_workflows tests`, which must print nothing. |
| PR-004 | LOW | IN-SCOPE | Reference accuracy | In-process measurement: `meta repair` description 280, `meta` description 201 | The plan cited 278 and 206 characters. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conventions and F-02 carry the measured values. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | What should the plan verify about `REQUIRED_LEAVES`? | That `meta repair` is a member and the pinned assertion passes | Require the total to equal `70` (rejected: false at HEAD after `6be40f11b`) | PR-001 measurement | yes |
| D-2 | Review tier | simple | standard (rejected: every Step T answer except 4 is no, and the plan edits no code) | Step T answers | yes |

### Plans reviewed and not reviewed

- ELIGIBLE: mx7azn (reviewed; APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 FIXED)
- NOT REVIEWED: (none)
