# IPD: Unify the repo-relative path renderers behind one name-only fallback policy

- Date: 2026-10-12
- Kind: child
- Concern: Four helpers render a path as repo-relative POSIX text, and they disagree on what to do when relativization fails. `artifact_rename._rel_to_repo` falls back to the RAW absolute posix path, `doctor._normalize_rel_path` also returns the absolute path (and does not resolve symlinks, so a symlink-spelled root leaks too), `specs.drift_location` truncates at a records segment and otherwise falls back to the FILE NAME, and `check_engine._finding_rel_path` (added by `2eubdn`) falls back to the file name. Two of the four therefore still emit an absolute path on exactly the inputs a fallback exists for, which is the defect class `2eubdn` fixed in the check engine (P8 duplication, filed as `qv0fi1` at `/plan-review` of `2eubdn`).
- Scope: IN: one shared renderer in `agent_workflows/artifact_core.py` whose fallback policy is "relativize against the root, else truncate at a records segment, else the bare file name, never an absolute path"; make the four named helpers delegate to it (keeping each helper's name and signature so no caller changes); and one behavioral test file pinning the policy and the four callers' agreement. OUT: the other repo-relative helpers grep finds (`ipd_lifecycle._repo_relative`, `attention._rel_posix`, `layout_inventory._repo_relative`, the inline relativization in `doctor.probe_artifacts`, `check_engine.finding_dict`'s `location` relativization), whose contracts differ on purpose and are filed separately as backlog `rd6ei9`; `agent_schema.normalize_repo_path` (executed scope of `9yd6tx`); any change to which findings fire or to any message structure beyond the path form.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/specs.py, agent_workflows/check_engine.py, agent_workflows/artifact_rename.py, agent_workflows/doctor.py, tests/test_repo_relative_posix.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: qv0fi1
- Set: qv0fi1
- Order: 1
- Highest E allocated: 06
- Author: OpenCode Claude Opus
- Id: amt9fs

## Workflow history

- 2026-10-12 draft (OpenCode Claude Opus): created.
- 2026-10-12 to-review (OpenCode Claude Opus): authored from backlog item `qv0fi1`. Measured all four helpers on the same inputs in the lane (F-01..F-04), chose the fallback policy from that evidence and from `docs/cli-output-contract.md`'s leak posture (OQ-01), and filed the out-of-scope sibling helpers as backlog `rd6ei9` so this plan's deferral has a live carrier.

## Goal

Make "render this path repo-relative" mean ONE thing in this codebase. Today the four helpers named by `qv0fi1` give four different answers on the same out-of-root or symlink-spelled input, and two of those answers are the absolute path, which `docs/cli-output-contract.md` ("Path Sanitization and Leak Posture") forbids on every machine-surface path field. One shared renderer in `artifact_core` with the leak-free fallback that `specs.drift_location` and `check_engine._finding_rel_path` already ship, plus thin delegating wrappers, removes the duplication and the two remaining absolute fallbacks at once.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the shared renderer

- [ ] E-01 Add a public function `repo_relative_posix(path, repo_root=None) -> str` to `agent_workflows/artifact_core.py` (stdlib-only, Python 3.9 compatible, so no `Path.is_relative_to`; use `relative_to` in a `try`). Policy, applied in order: (1) an empty value, or a `<...>` sentinel such as `<repo>`, is returned unchanged (the case `doctor._normalize_rel_path` guards today); (2) when `repo_root` is given, resolve the root and resolve the path (joining a relative path onto the root first), and if the result is inside the root return the relative POSIX string, without requiring the file to exist (as `_finding_rel_path`'s docstring requires, since `check_scope_path_target_stale` reasons about vanished paths); (3) otherwise, if the POSIX text contains a records segment (`.aw/records/` or `.agents/`, moving `specs._RECORDS_SEGMENTS` here as the single definition), return the text from that segment on; (4) otherwise, if the path is absolute, or is relative but escaped the root in step 2, return the bare file name; (5) otherwise return the path's POSIX text unchanged. Catch `ValueError`, `OSError` and `RuntimeError` around the resolution and fall through to steps 3-5. The docstring states the policy, why the fallback is name-only (cite `docs/cli-output-contract.md` "Path Sanitization and Leak Posture"), and that with `repo_root=None` the function is pure and cwd-independent (the `specs.drift_location` contract).
  - Depends on: none
  - Expected outcome: the function exists in `artifact_core`, nothing calls it yet, and the bare suite is unchanged.
  - Execution state: pending

### Task group 2: delegate the four helpers

- [ ] E-02 Make `specs.drift_location(path)` return `artifact_core.repo_relative_posix(path)` (no root), and have `specs` import the segment tuple from `artifact_core` instead of defining `_RECORDS_SEGMENTS` itself. Keep its docstring's rationale (pure, cwd-independent, why truncation instead of relativization) and add one line pointing at the shared renderer. `backlog.drift_location` already delegates to `specs.drift_location` and needs no edit.
  - Depends on: E-01
  - Expected outcome: `specs.drift_location` output is byte-identical to today on every input (the no-root path of E-01 is exactly its current algorithm), so `tests/test_attention.py::SpecDriftLocationIsRepoRelativeTests` stays green unmodified.
  - Execution state: pending

- [ ] E-03 Make `check_engine._finding_rel_path(repo_root, path)` return `_core.repo_relative_posix(path, repo_root)`, keeping its name, its argument order, and its docstring's statement of which fields it serves (shortened to point at the shared policy).
  - Depends on: E-01
  - Expected outcome: `tests/test_check_finding_path_relativity.py` stays green unmodified; the only observable delta is that an out-of-root path sitting under a records segment now renders from that segment rather than as the bare name, which is strictly more informative and still leak-free.
  - Execution state: pending

- [ ] E-04 Make `artifact_rename._rel_to_repo(path, repo_root)` return `_core.repo_relative_posix(path, repo_root)`, and update its one-line docstring, which today says "falls back to the raw posix path".
  - Depends on: E-01
  - Expected outcome: in-root paths render exactly as today (`tests/test_mutation_result_facts.py` stays green, it asserts `old_path == ".aw/records/plans/..."`); an out-of-root path no longer reaches `MutationTarget.old_path`/`new_path` or the touched-path list as an absolute path.
  - Execution state: pending

- [ ] E-05 Make `doctor._normalize_rel_path(loc, repo_root)` return `core.repo_relative_posix(loc, repo_root)`. Its sentinel and empty-string guard move into the shared renderer's step 1, so behavior on those inputs is unchanged; keep the broad `except Exception: return loc` only if the shared renderer can raise on a non-path string (it should not, since it catches the resolution errors), and otherwise drop it.
  - Depends on: E-01
  - Expected outcome: `doctor.build_remediation(...).file_path` for an absolute out-of-root `Drift.location` is the bare file name (today it is the absolute path, F-02), and for an in-root path reached through a symlinked root spelling it is the repo-relative path (today it is the absolute real path, F-03); `tests/test_doctor.py` and `tests/test_backlog_metadata_duplicate_and_gate_summary.py` stay green.
  - Execution state: pending

### Task group 3: pin the policy

- [ ] E-06 Add `tests/test_repo_relative_posix.py`, behavioral only (no `inspect`/`ast`/source reading, per the repo's no-code-pinning rule). Build every fixture under `tempfile.mkdtemp()` and assert by comparing against the derived temp root, never a literal home path (the `local-leaks` hook convention cited in `2eubdn`). Cases, each asserting the exact returned string: in-root absolute path; in-root relative path (including a `./` prefix); in-root path that does not exist; out-of-root absolute path with no records segment (bare name); out-of-root absolute path under a records segment (truncated); relative path escaping the root (bare name); root given as a symlink while the path uses the real spelling (relative); `<repo>` sentinel and empty string (unchanged); and, with `repo_root=None`, the three `specs.drift_location` cases (segment truncation of a relative and an absolute path, unchanged relative path). Then a PARITY test driving the four real callers on the same in-root, out-of-root and symlink inputs: `check_engine._finding_rel_path`, `artifact_rename._rel_to_repo`, `doctor.build_remediation(Drift(...)).file_path` (the public route to `_normalize_rel_path`), and, for the root-less inputs, `specs.validate_spec(...)[*].location`; assert they all agree and that no output contains the temp root string.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: the new file passes; the out-of-root and symlink cases for `artifact_rename` and `doctor` FAIL when E-04/E-05 are reverted (they witness F-01..F-03), so the test is not vacuous.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `agent_workflows/artifact_core.py` is the declared home for area-agnostic primitives ("This module OWNS the primitives that are common to EVERY growing `.agents/` artifact tree, so each area ... reuses ONE definition instead of forking"), is "pure and stdlib-only ... Python 3.9 compatible", and is ALREADY imported by all four modules (`specs` as `core`, `artifact_rename` as `_core`, `doctor` as `core`, `check_engine` as `_core`), so placing the renderer there adds no new import edge and no cycle.
- `pyproject.toml` declares `requires-python = ">=3.9"`, so `Path.is_relative_to` (3.9+ is fine, but `doctor` already uses it) is acceptable, while the shared renderer uses `relative_to` in a `try` to match the other three helpers.
- `docs/cli-output-contract.md` "Path Sanitization and Leak Posture": all path-valued envelope fields "MUST be repo-relative, normalized ... or home-path-redacted", and the producer is responsible for sanitizing "before the record is built, with the validator acting as a backstop". This is the contract that makes an absolute fallback a defect rather than a style choice.
- Run the suite BARE (`python3 -m pytest`), per the repo-local development contract in `AGENTS.md`.

## Findings

All measured in this lane by calling the real helpers (`AW_NO_REEXEC=1 python3 -c ...`).

| Id | Finding | Evidence |
|---|---|---|
| F-01 | `artifact_rename._rel_to_repo` returns the ABSOLUTE path for an out-of-root input. | Root `/tmp/opencode/repoX`, path `/tmp/opencode/elsewhere/x.spec.md`: `rename /tmp/opencode/elsewhere/x.spec.md`. Its docstring: "falls back to the raw posix path". |
| F-02 | `doctor._normalize_rel_path` returns the ABSOLUTE path for an out-of-root input, and it reaches `Remediation.file_path`. | Same inputs: `doctor /tmp/opencode/elsewhere/x.spec.md`; `doctor.build_remediation(core.Drift(o,'x.y','d'), r).file_path` printed `/tmp/opencode/elsewhere/x.spec.md`. |
| F-03 | `doctor._normalize_rel_path` does NOT resolve, so a symlink-spelled root leaks the real absolute path where the other two root-taking helpers relativize correctly. | Root `<T>/link -> <T>/real`, path `<T>/real/.aw/records/plans/pending/a.ipd.md`: `doctor <T>/real/.aw/records/plans/pending/a.ipd.md`, `rename .aw/records/plans/pending/a.ipd.md`, `engine .aw/records/plans/pending/a.ipd.md`. |
| F-04 | `specs.drift_location` and `check_engine._finding_rel_path` already use the leak-free name-only fallback, so two of four helpers already agree on the target policy. | Same out-of-root input: `specs x.spec.md`, `engine x.spec.md`. `_finding_rel_path`'s docstring: "The fallback to the bare file name is modeled on :func:`specs.drift_location` as the leak-free choice." |
| F-05 | In-root behavior already agrees across the three root-taking helpers, so unification changes only fallback cases. | `doctor-in a/b.md a/b.md a/b.md`; `doctor-rel a/b.md a/b.md`; `./a/b.md` -> `a/b.md` for both doctor and engine. |
| F-06 | One more divergence: a RELATIVE path escaping the root. `doctor` returns it unchanged, `check_engine` returns the name. Neither leaks; the plan picks the name for one rule. | `doctor ../x.md`, `engine x.md`. |
| F-07 | `specs.drift_location` takes no root and must stay pure (its docstring: "PURE AND CWD-INDEPENDENT BY CONSTRUCTION"), so the shared renderer must make the root OPTIONAL, with the no-root path being exactly the current truncate-else-name algorithm. | `specs.drift_location(Path('sub/.aw/records/specs/x.md'))` -> `.aw/records/specs/x.md`; `Path('../x.md')` -> `../x.md` (relative, no segment: unchanged). |
| F-08 | The relevant existing tests pass at HEAD and constrain the change. | `python3 -m pytest tests/test_check_finding_path_relativity.py tests/test_mutation_result_facts.py tests/test_doctor.py tests/test_backlog_metadata_duplicate_and_gate_summary.py tests/test_check_recovery_fidelity.py "tests/test_attention.py::SpecDriftLocationIsRepoRelativeTests"` -> `62 passed in 8.27s`. |
| F-09 | Other repo-relative helpers exist with deliberately different contracts and are NOT named by `qv0fi1`. | `ipd_lifecycle._repo_relative` ("or the resolved absolute path if outside", feeds receipts' `plan_path`), `attention._rel_posix` (raises `ValueError` outside the root), `layout_inventory._repo_relative` ("without resolving symlinks, or ``None``"), inline relativization in `doctor.probe_artifacts`. Filed as backlog `rd6ei9`. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/artifact_core.py`** gains `repo_relative_posix(path, repo_root=None)` and becomes the single home of the records-segment tuple (E-01).
2. **`specs.drift_location`** delegates with no root; byte-identical output (E-02).
3. **`check_engine._finding_rel_path`** delegates (E-03).
4. **`artifact_rename._rel_to_repo`** delegates; its absolute fallback is gone (E-04).
5. **`doctor._normalize_rel_path`** delegates; its absolute fallback and its symlink leak are gone (E-05).
6. **`tests/test_repo_relative_posix.py`** pins the policy and the four callers' parity (E-06).

## Deferred / out of scope (with reason)

- The sibling helpers in F-09 (`ipd_lifecycle._repo_relative`, `attention._rel_posix`, `layout_inventory._repo_relative`, `doctor.probe_artifacts`'s inline block) and `check_engine.finding_dict`'s `location` relativization: not named by `qv0fi1`, and each has a contract that a name-only fallback would change in a caller-visible way (a receipt field, a raised error used as a signal, a `None` signal, an `os.sep`-joined string). Carried by backlog `rd6ei9`, filed in this authoring turn so the deferral does not vanish (the exact failure that created `qv0fi1`).
- `agent_schema.normalize_repo_path`: a whole-path-value sanitizer with its own tail-keeping fallback, executed scope of `9yd6tx`; not a repo-relative renderer in this sense.

## Scope check

- Over-scope: none. Every path in `- Scope-Paths:` is one of the four helpers' modules, the shared home, or the new test.
- Under-scope: none. `backlog.drift_location` needs no edit because it already delegates to `specs.drift_location`; existing callers keep the same helper names and signatures, so no call site changes.

## Required tests / validation

- The new `tests/test_repo_relative_posix.py` passes, and its out-of-root and symlink cases for `artifact_rename` and `doctor` fail against the pre-change helpers (proves the test witnesses F-01..F-03).
- The constraining tests from F-08 stay green unmodified.
- The bare suite `python3 -m pytest` passes, with the summary line pasted.
- `aw check all` exit status and finding count on this repository are unchanged before and after (the change must not alter which findings fire).

## Spec / documentation sync

N/A: no spec describes these private helpers' fallback, and `docs/cli-output-contract.md` already states the leak posture this plan conforms the helpers to; the change brings code into line with the document rather than changing the contract. No user-facing doc or CHANGELOG entry: the change is not user-perceptible in normal operation (all inputs are under the root), which is why `qv0fi1` is a `chore`.

## Open questions

### OQ-01: Which fallback wins when the four helpers disagree?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RELATIVIZE, ELSE RECORDS-SEGMENT TRUNCATION, ELSE THE BARE FILE NAME; NEVER THE ABSOLUTE PATH. Evidence: `docs/cli-output-contract.md` requires path-valued envelope fields (`target`, `location`, `path`, ...) to be repo-relative and makes the producer responsible, so the two absolute fallbacks (F-01, F-02) are the defect, not an alternative. `qv0fi1`'s own summary records that `2eubdn` already adopted "specs.drift_location's name-only fallback as the leak-free choice", and two of four helpers already ship it (F-04). Segment truncation is kept as an intermediate step because it is what `specs.drift_location` does without a root and it is strictly more informative than the name while still leak-free (F-07). The information loss is bounded: in normal operation every input is under the root (F-05 shows all helpers already agree there), so the fallback runs only on symlinked, out-of-tree, or operator-supplied paths, where the file name identifies a file the operator just named. A relative path that escapes the root (F-06) also gets the name, for one rule rather than two.

### OQ-02: Does the doctor change alter its human output in a way a user would notice?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ONLY ON THE FALLBACK INPUTS, AND IN THE LEAK-FREE DIRECTION. `doctor._categorize_drift` uses `rem.file_path or d.location`; when the parent is `.` it already searches the repo with `repo_root.rglob(fname)` to recover a directory, so a bare-name fallback degrades to an in-repo lookup rather than to an absolute path. For the symlink case (F-03) the output becomes the correct relative path. In-root inputs are unchanged (F-05).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: The pasted diff of `agent_workflows/artifact_core.py` showing `repo_relative_posix` and the records-segment tuple, plus pasted output of a `python3 -c` call (observation produced by E-01's function) on these inputs with the printed results: in-root absolute, out-of-root absolute, out-of-root under `.aw/records/`, `../x.md` with a root, `<repo>`, and `sub/.aw/records/specs/x.md` with no root; expected respectively the relative path, the bare name, the truncated segment path, `x.md`, `<repo>`, `.aw/records/specs/x.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: The pasted diff of `agent_workflows/specs.py` showing `drift_location` delegating and `_RECORDS_SEGMENTS` no longer defined there, and the pasted runner output of `python3 -m pytest "tests/test_attention.py::SpecDriftLocationIsRepoRelativeTests" -o addopts=""` passing with the test file unmodified (`git diff --stat tests/test_attention.py` empty).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: The pasted diff of `check_engine._finding_rel_path` delegating, and the pasted runner output of `python3 -m pytest tests/test_check_finding_path_relativity.py tests/test_check_recovery_fidelity.py -o addopts=""` passing unmodified.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: The pasted diff of `artifact_rename._rel_to_repo` delegating with its docstring updated, the pasted `python3 -c` output (E-04's helper) showing `_rel_to_repo(<out-of-root abs>, root)` now returns the bare name where F-01 measured the absolute path, and the pasted runner output of `python3 -m pytest tests/test_mutation_result_facts.py -o addopts=""` passing unmodified.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: The pasted diff of `doctor._normalize_rel_path` delegating, the pasted `python3 -c` output (E-05's helper reached through `doctor.build_remediation`) showing `file_path` is the bare name for F-02's out-of-root input and `.aw/records/plans/pending/a.ipd.md` for F-03's symlinked-root input, and the pasted runner output of `python3 -m pytest tests/test_doctor.py tests/test_backlog_metadata_duplicate_and_gate_summary.py -o addopts=""` passing unmodified.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: The pasted runner output of `python3 -m pytest tests/test_repo_relative_posix.py -o addopts=""` passing; then, with ONLY `agent_workflows/artifact_rename.py` and `agent_workflows/doctor.py` temporarily reverted to HEAD (`git stash push -- <those two paths>`, then `git stash pop` after), the pasted output of the same command showing the out-of-root and symlink cases for those two callers FAILING, proving the test witnesses F-01..F-03. Then the pasted tail of the BARE `python3 -m pytest` run showing the `N passed` summary line with zero failures, and the `aw check all` exit status and finding count before and after the change (equal).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `- Status: to-review` and carries NO `- Readiness:` field: that field is an output of `/plan-review`. Execution requires explicit human approval recorded with `aw ipd set approved amt9fs --by-human`.

Execution contract: commit only the files named in `- Scope-Paths:`, through `aw commit amt9fs -- <paths>`, never `git add -A` and never `git push`. Run the suite BARE (`python3 -m pytest`) and paste the ACTUAL runner output. Do not mark any `V-*` item complete from the matching `E-*` checkmark.

STOP CONDITIONS. STOP if `specs.drift_location`'s output changes on ANY input: its no-root path must stay byte-identical (F-07), and `SpecDriftLocationIsRepoRelativeTests` going red means the policy order is wrong. STOP if any in-root rendering changes (F-05): unification is allowed to change fallback cases only. STOP if `aw check all`'s finding count or exit status changes. STOP and do NOT widen into the F-09 helpers; they are `rd6ei9`'s subject. STOP if the new test passes with E-04/E-05 reverted: the fixture is not exercising the fallback.

Post-gate lifecycle: when every `E-*` is performed and every `V-*` carries pasted evidence, run `aw ipd lint --phase pre-transition`, confirm it conforms, and only then move this plan to `.aw/records/plans/executed/` through the tooled transition. Backlog item `qv0fi1` carries no `- Blocks-Release:`, so none is inherited here.
