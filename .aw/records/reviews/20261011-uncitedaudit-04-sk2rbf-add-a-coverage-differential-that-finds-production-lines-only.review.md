# Review findings: plan sk2rbf

- Subject-Id: sk2rbf
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `c7234010c`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent`: `clean` before review;
`--phase review-finalize`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.
Sibling `nzzu8n` (Order 02) was reviewed earlier in this sweep and now replays each file in its own detached
worktree, exposing `replay_root`. This review reconciles against that revised interface.

Demonstrations used throwaway probe scripts under the gitignored `.aw/state/`, deleted afterwards; temp data lived in
`tempfile.mkdtemp()`:
- Fixture with `a()` called in-process, `b()` via `subprocess.run([sys.executable, "-c", ...])`, and the planned
  rcfile under `-n 2` and `-p no:xdist`. Both runs gave per-test context on `a`'s body, the empty context only on
  `b`'s body, and the empty context on every `def` line. No `.coverage*` was left in the repo.
- Unittest methods and a parametrized test gave context names `tests.test_m.T.test_a` and `tests.test_m.test_b`
  (no parameter suffix). A module-level call `VAL = m.c()` covered `c` under `''` only.
- Real tree, `tests/test_lost_guard_census.py tests/test_cli.py tests/test_agy_runipd_cli.py`, `-n auto`: plain
  run 9.8s, coverage run 17.6s, 58 data files combined in 1.2s, 193 measured files all in the repo, 55 contexts.
  By body lines: 735 functions in-process only, 242 mixed, 157 empty-context only, and 1,789 with only the header
  covered. `git status --porcelain --ignored` was unchanged.
- Baseline in root A and replay in root B: raw-path keying gave exclusive `[1, 2, 5, 6, 7]` (all lines).
  Root-relative keying gave exclusive `[6, 7]` and shared `[1, 2, 5]`. The replay data stayed readable after B was
  deleted.
- `python3 -m pytest -o addopts="" -p no:xdist -n auto ...` -> `unrecognized arguments: -n`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A correctness (exclusive vs shared) | E-04 original; `nzzu8n` E-01 Isolation (`<tmp>/wt`) and `replay_root`; review probe (F-06) | Baseline and replay run in different roots, so absolute paths never match. Every replayed line would read as `exclusive`, and Orders 05 to 07 would treat surviving guards as lost. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each measured file is now keyed relative to its own run root (`repo` for the baseline, `ReplayResult.replay_root` for the replay). E-02's main case fails if keying breaks, and V-02 adds a sensitivity check. |
| PR-002 | HIGH | IN-SCOPE | A correctness (reach / subprocess_only) | E-01 original mapper (`lineno..end_lineno`); review fixture and real-tree counts (F-05) | `def` lines execute at import under the empty context. With `lineno` included, every imported function counts as reached, and an uncalled one reads `subprocess_only: true`. On the real tree, 1,789 functions had only their header covered. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The mapper now owns only body lines (`body[0].lineno..end_lineno`). `subprocess_only` is defined over body lines. E-02 asserts that an uncalled `c()` is absent. |
| PR-003 | MEDIUM | IN-SCOPE | A data integrity (stale baseline) | E-04 original; nothing tied a baseline to a tree | Line numbers are comparable only on the same tree. A baseline from an older `HEAD` would silently misclassify lines. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `diff` refuses with exit 2 when `baseline.json` `head` differs from `HEAD`. E-02 tests this, and E-03 documents it. |
| PR-004 | MEDIUM | IN-SCOPE | G interface contract | E-01 `-n auto ... <args>` plus E-02 "pass `-p no:xdist`"; output shapes unspecified | Adding `-p no:xdist` after `-n auto` fails with "unrecognized arguments: -n" (measured). The `baseline.json` and diff output shapes, which Orders 05 and 07 consume, were only partly defined. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The serial mode is now an explicit selection rule. The `baseline.json` keys, the diff record keys, the context-name form and `--from-json`/`--format` behaviour are pinned. |
| PR-005 | LOW | UNDER-SCOPE | E evidence | V-01/V-04 `git status --short`; V-02 had no sensitivity check | `--short` hides ignored files, so a stray `.coverage*` that `.gitignore` matched would go unseen. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All runs now use `git status --porcelain --ignored`, plus `git worktree list` for `diff`. V-01 pastes a `baseline.json` excerpt, and V-02 adds a scratch sensitivity run. |
| PR-006 | LOW | UNDER-SCOPE | G execution contract | Gate paragraph; E-03; OQ-01 `Owner: none`; no execution-start baseline | The gate lacked a scope-fence declaration, honesty rule, prerequisite check and staged-set check. The README item lacked the no-dash rule, OQ-01 had no owner, and there was no baseline capture. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate itemized to match siblings `nzzu8n` and `g55j1e`. Baseline capture, no-dash rule and OQ-01 owner added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should paths from different run roots be reconciled? | Key each file relative to its own run root. | Coverage `[paths]` remapping, rejected because it needs one rcfile per root and adds config with no benefit. Running the baseline inside a worktree too, rejected because it is slower and still needs relativizing. | Review probe 4 (F-06); `nzzu8n` `replay_root`. | yes |
| D-2 | Which lines count as reach? | Body lines only; `def` lines are excluded. | Include `def` lines, rejected because import-time coverage would mark everything reached. Exclude all empty-context lines, rejected because that would erase genuine subprocess reach. | Review fixture plus real-tree counts (F-05). | yes |
| D-3 | What happens with a stale baseline? | Refuse with exit 2. | Warn and continue, rejected because the line comparison is meaningless across trees. | Rubric A; E-04. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
