# IPD: Make aw doctor report how many files the leak sanitizer actually scanned

- Date: 2026-09-26
- Kind: child
- Concern: `doctor.SanitizerProbeResult.scanned_files` is declared (default 0), serialized by `to_dict()`, and published as the `sanitizer` Evidence value (`"scanned_files": report.sanitizer.scanned_files`), but nothing ever assigns it, so every consumer reads a hardcoded 0 even when the scan read thousands of files and found leaks. `leak_sanitizer.scan_working_tree` returns only findings, so `doctor.probe_sanitizer` has no count to set. NAME THE SURFACE PRECISELY, because the obvious phrasing is wrong and it decides how this plan is validated: the reachable surface is `aw doctor --json`, NOT `aw doctor --agent`. Measured at review on this repo: `--json` carries `evidence[sanitizer] == {"scanned_files": 0, "findings": 0}` and `data.report.sanitizer` carries `{"scanned_files": 0, ...}`, while the `--agent` COMPACT record carries `"evidence":["git","env","attention","sanitizer","artifacts"]` and the string `scanned_files` appears NOWHERE in it, because `agent_schema.sanitize_evidence_item` reduces a dict-valued Evidence to its KEY alone and `aw doctor` declares no `--verbose` to select the verbose branch (F-3).
- Scope: IN: a counted variant `leak_sanitizer.scan_working_tree_counted`; `scan_working_tree` delegates to it; `doctor.probe_sanitizer` sets `scanned_files`; one outcome test. OUT: the other scanners (`scan_staged`, `scan_history`); other callers of `scan_working_tree`; a `local_leaks` re-export of the NEW name (the shim preserves the HISTORICAL API and no consumer imports the new one; D-2); rpqv4q's drift/except changes; making the count visible in the `--agent` COMPACT record (F-3, carried); a human-render line for the count (F-4, carried).
- Scope-Paths: agent_workflows/leak_sanitizer.py, agent_workflows/doctor.py, tests/test_doctor.py
- Item-Dependencies: executed:rpqv4q
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: c0ppo0
- Blocks-Release: next
- Set: doctorleak
- Order: 2
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 3xdgg0

## Workflow history
- 2026-09-27 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 3xdgg0 verified (set doctorleak, attempt 1).
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; 8 findings PR-901..PR-908 all FIXED, 4 decisions D-1..D-4 recorded; review record written. PR-901: the count CANNOT reach aw doctor --agent (the compact record reduces a dict-valued Evidence to its key and doctor declares no --verbose), so V-02 demanded unproducible evidence; renamed to --json and recorded as F-3. PR-902: added E-04/V-04 pinning that 0 still means did-not-scan, the half of the Goal that was untested. PR-903: E-01's excluded branch is nearly unreachable (check=False does not raise), so the increment placement is now specified. Corrected two facts (the shared fixture tracks 3 files not many; rpqv4q is executed not approved). aw ipd lint --phase review-finalize conforming and aw check plans clean for this plan.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog c0ppo0: add leak_sanitizer.scan_working_tree_counted and set doctor's scanned_files from it, with a 2-file/1-leak outcome test.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`aw doctor`'s sanitizer evidence states the true number of tracked files the scan read, so a reader can tell a clean scan of N files from a scan that read nothing.

WHY THAT DISTINCTION IS WORTH A CHANGE AT ALL, since the field is cosmetic on a happy path and this plan should not oversell itself. The two states the count separates are NOT hypothetical and they are indistinguishable today. A probe whose scan RAISED reports `findings: 0` with `scanned_files: 0` plus a `doctor.probe-failed` drift (measured at review on a non-git directory: `drift=[('doctor.probe-failed', "Command '['git', '-C', ...")]`), and a genuinely clean repo reports `findings: 0` with `scanned_files: 0` and no drift. The drift entry is what distinguishes them today, so the count is a SECOND, positive signal rather than the only one; `leak_sanitizer`'s own `--agent` contract already treats exactly this distinction as load-bearing, in the words of the test that pins it, so that a consuming agent can tell "scanned, nothing found" from "did not scan" (`tests/test_leak_sanitizer.py`, the CLEAN ROW of `STATES` in `test_the_agent_envelope_is_identical_in_shape_for_both_tree_states`). This plan gives doctor's sanitizer evidence the same property the sanitizer's own CLI already has.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: count, wire, test

- [x] E-01 In `agent_workflows/leak_sanitizer.py`, add `scan_working_tree_counted(repo_root: Path, *, include_warn: bool = False) -> tuple[list[Finding], int]` containing the current body of `scan_working_tree`, incrementing a counter each time a file's text is obtained and passed to `scan_text` (the on-disk read OR the `git show HEAD:<rel>` fallback). A path in `_ALLOWED_PATHS` is skipped and NOT counted; a path whose read and fallback both fail (`continue`) is NOT counted. Replace `scan_working_tree`'s body with `return scan_working_tree_counted(repo_root, include_warn=include_warn)[0]`, keeping its signature and return type, so its callers (`leak_sanitizer.run`, which calls `scan_working_tree(repo_root, include_warn=include_warn)` in its final `else` branch, `security_hardening.scan_artifact_for_leaks`, and the `local_leaks` re-export) are unchanged. State the counting rule in the new function's docstring: "files actually read and scanned; excludes `_ALLOWED_PATHS` and unreadable paths".
  - THE "READ AND FALLBACK BOTH FAIL" BRANCH IS NEARLY UNREACHABLE, AND KNOWING THAT PREVENTS A WRONG PLACEMENT OF THE INCREMENT. The fallback runs `subprocess.run(..., check=False)` inside its own `try`, so a git failure does NOT raise and does NOT reach the `continue`: it returns a nonzero exit with empty stdout, and `text` becomes `""`, which IS then passed to `scan_text`. Measured at review with a binary file staged but never committed: `git show HEAD:bin.dat` exits 128 with 0 bytes, `scan_text` is called with `''`, and the `except Exception: continue` is not taken. So the branch the docstring excludes is reached only if `subprocess.run` itself raises (a missing `git` binary, an OS-level spawn failure). PLACE THE INCREMENT IMMEDIATELY BEFORE THE `findings.extend(scan_text(...))` CALL, which makes the docstring true by construction rather than by reasoning about which `except` fires. Note the honest consequence: an unreadable file whose blob fetch yields empty IS counted, because it was scanned (of empty text). That is the correct reading of "files actually read and scanned" and it is why the docstring says "unreadable paths" rather than "binary files".
  - Depends on: none
  - Expected outcome: identical findings from both functions; the counted one also returns the read count.
  - Execution state: performed

- [x] E-02 In `doctor.probe_sanitizer`, call `leak_sanitizer.scan_working_tree_counted(repo_root)` and set `res.scanned_files` from its count and `res.findings` from its findings. rpqv4q restructures this function first (only the scan call inside the `try`); keep that structure: unpack the tuple inside the `try`, build drift outside it. If rpqv4q has not landed, stop (see gate).
  - LEAVE `res.scanned_files` AT ITS DEFAULT 0 ON THE FAILURE PATH, which is what the early `return res` in the `except` branch already does; do NOT set a partial count there. A probe that raised scanned an unknown number of files, and reporting a partial count as the coverage figure would assert coverage the scan does not have. 0 plus the `doctor.probe-failed` drift is the honest pair, and it is exactly the state E-04 pins.
  - Depends on: E-01
  - Expected outcome: `aw doctor --json` sanitizer evidence shows a nonzero `scanned_files` on any repo with tracked files (the `--agent` COMPACT record does not carry the value at all; see F-3).
  - Execution state: performed

- [x] E-03 Add a test to `tests/test_doctor.py`: a fresh `tempfile.TemporaryDirectory` git repo (use the file's `_git` helper; do NOT reuse `DoctorTests.setUp`, which commits an installed fixture of its own) with exactly two committed files, one containing a home-directory path built at runtime from pieces (`"/home/" + "someuser" + "/x"`, never one literal, since `tests/test_doctor.py` is not in `_ALLOWED_PATHS` and a literal would itself be a leak finding; see rpqv4q E-02) and one clean. Assert `probe_sanitizer(repo).scanned_files == 2` and `len(probe_sanitizer(repo).findings) == 1`. Outcomes only.
  - USE A FRESH FIXTURE FOR THE REASON STATED HERE, NOT THE ONE THE PLAN FIRST GAVE. `DoctorTests.setUp` tracks THREE files, not "many" (measured at review by re-running its exact body: `['.aw/system/VERSION', '.aw/system/layout.json', '.aw/system/layout.schema.json']`), so the original justification was wrong on the number. The real reason stands and is stronger: `engine.emit_layout_artifacts` decides that count, so an exact-count assertion in a shared fixture would break the moment the installer emits one more file, which is a fixture-coupling defect rather than a size problem.
  - THE COUNT 2 IS AN AUTHORED STABLE FACT, NOT A LIVE-ARTIFACT COUNT: the test commits exactly two files into a throwaway repo it controls, so the number cannot drift and no re-derivation rule applies. Do NOT "generalize" it to a derived expression; a literal 2 against a two-file fixture is the whole assertion.
  - Depends on: E-02
  - Expected outcome: the test passes; against the pre-change doctor it fails with `0 != 2`.
  - Execution state: performed

- [x] E-04 In the SAME test method added by E-03 (one method, two assertions; do not add a second fixture), also pin the FAILURE pair: call `doctor.probe_sanitizer` on a path that is NOT a git repository (a second `tempfile.TemporaryDirectory`, never `git init`ed) and assert `res.scanned_files == 0` AND that `res.drift` contains a `doctor.probe-failed` rule. Outcomes only. Then run the bare suite.
  - WHY THIS PIN IS THE ONE THAT MAKES THE FIELD MEAN SOMETHING. E-03 alone proves a nonzero count appears; it does NOT prove 0 still means "did not scan", which is the distinction the Goal claims to deliver. Without this, a later refactor could make `scanned_files` nonzero on a failed probe and no test would notice, and the field would then be actively misleading rather than merely useless. Measured at review on a non-git temp dir at HEAD: `drift=[('doctor.probe-failed', ...)]` with `scanned_files: 0`, so the assertion passes BEFORE the change too. That is correct and expected: this is a CHARACTERIZATION pin protecting the invariant E-02's failure path relies on, not a regression test for the defect, and E-03 is the item that fails pre-change.
  - Depends on: E-02
  - Expected outcome: the failure pair is asserted; the bare suite passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- rpqv4q (doctorleak-01) changes the same function (`f.matched` -> `f.snippet`, narrow `try`); this plan depends on it to avoid a conflicting edit. CORRECTED AT REVIEW: rpqv4q is `executed`, not `approved` as this line originally said, so the dependency is already SATISFIED and the gate's stop condition is not expected to fire (verified: `.aw/records/plans/executed/20260925-doctorleak-01-rpqv4q-...ipd.md` carries `- Status: executed`, and `doctor.probe_sanitizer` reads `f.snippet` with the scan alone inside the `try`).
- `leak_sanitizer._ALLOWED_PATHS` exempts five self-referencing files from scanning; `tests/test_doctor.py` is not among them. Four of the five are tracked in this repo (`tests/test_packaging.py` is not), so on this tree the scan skips 4 and reads 2876 of 2880 tracked files.
- `aw sanitize --agent` must stay clean after the test is added.
- Tests assert OUTCOMES only (maintainer rule): no source-text or docstring pins.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The `aw.agent/v1` COMPACT record reduces a dict-valued `Evidence` to its key alone (`agent_schema.sanitize_evidence_item`); only the verbose branch or `--json` carries the value. `aw doctor` declares no `--verbose`, so `--json` is this plan's only reachable machine surface for the count (F-3).
- No CHANGELOG entry: the changed field is an internal evidence value that has never carried a true number, so there is no user-visible behavior to announce. Stated explicitly because a sibling plan in the pending set (`wd6npl`) does declare `CHANGELOG.md` in its Scope-Paths, and the difference is deliberate rather than an omission.

## Findings

Authored at HEAD `61ef21d8`; F-1 through F-6 re-measured at review HEAD `8b64b198` and all six hold.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | LOW | `doctor.SanitizerProbeResult.scanned_files` | Never assigned anywhere. | `grep -n scanned_files agent_workflows/*.py tests/*.py` -> only the dataclass default, `to_dict`, and the evidence emitter; re-run at review, same three sites and no test reference |
| F-2 | INFO | `leak_sanitizer.scan_working_tree` | Returns `list[Finding]` only; callers: `leak_sanitizer.run` (its final `else` branch, `findings = scan_working_tree(repo_root, include_warn=include_warn)`), `security_hardening.scan_artifact_for_leaks`, `doctor.probe_sanitizer`, and the `local_leaks` re-export. | grep; the plan's original wording called the first caller "the sanitizer entry point", which is `run`, now named |
| F-3 | MEDIUM | `agent_schema.sanitize_evidence_item`; `result_types.CommandResult.to_agent_record` | THE FIELD IS UNREACHABLE FROM `--agent`, WHICH IS THE SURFACE THIS PLAN ORIGINALLY CLAIMED TO FIX. The compact record reduces a dict-valued `Evidence` to its KEY alone, and the verbose branch is selected by `OutputContext.verbose`, which `select_output` reads from an `args.verbose` that `aw doctor` does not declare. So `scanned_files` cannot appear in `aw doctor --agent` output no matter what this plan assigns. `--json` and `data.report.sanitizer` do carry it. NOT FIXED HERE: exposing it would change the shared compact-record contract for every verb. | On this repo: `aw doctor --agent` first record is `"evidence":["git","env","attention","sanitizer","artifacts"]` and `'scanned_files' in json.dumps(record)` is `False`; `aw doctor --json` gives `evidence[sanitizer] == {"scanned_files": 0, "findings": 0}`. Driven with a NONZERO value (2876) through both branches: compact -> `["sanitizer"]`, verbose -> the full dict. `aw doctor --verbose` -> `error: unrecognized arguments: --verbose` |
| F-4 | LOW | `doctor.render_human_report` (the "Security & Local Leak Sanitizer" section) | THE HUMAN RENDER NEVER SHOWS THE COUNT, before or after this plan. Its clean branch prints the fixed string `"  Sanitizer:   Clean (0 maintainer/local leak findings)"`, so the human reader keeps the exact ambiguity the Goal describes. Out of scope: it is a copy change on a rendered line, with no test pinning that line today, and it belongs with whoever next revises that section. | `grep -rn "Clean (0 maintainer" --include=*.py .` -> one site, `agent_workflows/doctor.py`, and zero test references |
| F-5 | LOW | `leak_sanitizer.scan_working_tree` (the `except Exception: continue` fallback) | The "read and fallback both fail" case E-01 excludes from the count is NEARLY UNREACHABLE, because the fallback uses `check=False` and so does not raise on a git failure; it yields empty stdout and `scan_text` IS called with `""`. Folded into E-01 as a placement instruction rather than a scope change. | A binary file staged but never committed: `git show HEAD:bin.dat` exits 128 with 0 bytes, no exception, `scan_text` called with `''`, findings `[]` |
| F-6 | LOW | `tests/test_doctor.py` `DoctorTests.setUp` | E-03's original justification for a fresh fixture ("tracks many files") was factually wrong: the fixture tracks THREE files. The instruction is still right for a better reason (the count is owned by `engine.emit_layout_artifacts` and would drift), and E-03 now says that instead. | Re-ran the fixture body at review: tracked `['.aw/system/VERSION', '.aw/system/layout.json', '.aw/system/layout.schema.json']` |

## Proposed changes (ordered, validatable)

1. E-01: counted scanner; old one delegates.
2. E-02: doctor sets the count (and leaves 0 on the failure path).
3. E-03: the nonzero-count outcome test.
4. E-04: the failure-pair pin (`0` plus `doctor.probe-failed`); bare suite.

## Deferred / out of scope (with reason)

- Counts for `scan_staged` and `scan_history`: doctor does not use them and no surface reports a count for them.
  - Carrier-Declined: no consumer.
- F-3, exposing the count in the `--agent` COMPACT record: the compact record deliberately reduces a dict-valued `Evidence` to its key for EVERY verb, so changing it is a change to the shared output contract (`docs/cli-output-contract.md` Section 2) and not a doctor fix. The honest state after this plan is that `--json` carries a true count and `--agent` carries none, which is strictly better than today (where `--json` carries a false one), so nothing regresses.
  - Carrier-Declined: there is no work item here until someone decides the contract question, and filing one would record a decision the maintainer has not taken. The finding is recorded in this plan's Findings table with its measurement, and the approval gate states it, so a reader deciding to widen the contract later has the evidence. Stated plainly because the alternative reading is available: if the maintainer wants the count in `--agent`, that is a NEW request against the output contract, not an unfinished part of this plan.
- F-4, a human-render line stating the count: a copy change on `doctor.render_human_report`'s sanitizer section, unpinned by any test, and outside this plan's declared paths. Not needed for the machine-readable fix this plan delivers.
  - Carrier-Declined: not work anyone is waiting on; recorded in Findings so the next author of that section sees it.

## Scope check

- Over-scope: none. E-04 is new at review and is IN scope: it pins the failure half of the invariant the Goal claims, and it costs two assertions in the method E-03 already adds.
- Under-scope: none remaining. Two gaps were found at review and are recorded rather than absorbed, each with a stated reason: F-3 (the `--agent` compact record cannot carry the value) and F-4 (the human render does not show it). Both are Carrier-Declined above with the reasoning.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_doctor.py -v -k <the new method's name>`; `aw sanitize --agent`; a BARE `python3 -m pytest`. Test rule: outcomes only.
- NOTE THE SELECTOR, because the plan originally specified `-k scanned` and that matches nothing until the new method exists: measured at review, `-k scanned` on this file collects 27 items and deselects all 27. Use the method name actually added.

## Spec / documentation sync

No `.spec.md` is amended and none needs to be. No spec documents doctor's evidence FIELDS: the `aw doctor` references in the approved specs cover layout conformance (`kw5y2s` Section 6.2) and the doctor/check population split for setid conflicts (`2lcqno`), neither of which touches the sanitizer probe. `docs/cli-output-contract.md` Section 2 documents the `Evidence` SHAPE (`key`, `value`, `status`, `detail`), which this plan does not change; it only makes one value true. The field already exists and merely stops being a constant, so no documented contract changes and nothing declared in `- Scope-Paths:` is a spec.

## Open questions

### OQ-01: Count files read, or files listed by `git ls-files`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Files actually read and scanned. The field's purpose is to show what the scan covered; counting allowed or unreadable paths would overstate coverage. CONFIRMED AT REVIEW WITH THE NUMBERS, so a reader can see the choice is not cosmetic: on this repo the two answers differ, 2880 tracked versus 2876 read, because four of the five `_ALLOWED_PATHS` entries are tracked here and are deliberately never scanned. Reporting 2880 would claim coverage of four files the sanitizer is specifically configured not to look at.
- Carrier-Declined: resolved in place with a measurement; nothing outstanding after this plan executes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the diff; paste `python3 -c 'from pathlib import Path; from agent_workflows import leak_sanitizer as L; a=L.scan_working_tree(Path(".")); b,n=L.scan_working_tree_counted(Path(".")); print(len(a)==len(b), n, n==len([p for p in L._tracked_files(Path(".")) if p not in L._ALLOWED_PATHS]))'` on this repo showing `True <n> True` (or, if unreadable paths exist, the difference explained). At review this repo had 2880 tracked and 2876 eligible with zero on-disk read failures, so `True 2876 True` is the expected shape; RE-DERIVE it rather than pasting that number, since the tree grows.
  - ALSO show the delegation is real rather than a copied body, because the whole safety argument for E-01 is that `scan_working_tree` keeps one implementation: paste the `scan_working_tree` body from the diff showing it is a single `return scan_working_tree_counted(...)[0]` with its signature unchanged.
  - Observed evidence: verified diff, delegation, and counted scan re-derivation:
    1. Diff of `agent_workflows/leak_sanitizer.py`:
    ```diff
@@ -580,9 +580,17 @@ def _staged_files(repo_root: Path) -> list[str]:
     return [line for line in out.stdout.splitlines() if line]


-def scan_working_tree(repo_root: Path, *, include_warn: bool = False) -> list[Finding]:
+def scan_working_tree_counted(
+    repo_root: Path, *, include_warn: bool = False
+) -> tuple[list[Finding], int]:
+    """Scan tracked working tree for maintainer or machine identifying leaks.
+
+    Returns (findings, count). Count is files actually read and scanned; excludes
+    _ALLOWED_PATHS and unreadable paths.
+    """
     ruleset = build_ruleset(repo_root, include_warn=include_warn)
     findings: list[Finding] = []
+    scanned_count = 0
     for rel in _tracked_files(repo_root):
         if rel in _ALLOWED_PATHS:
             continue
@@ -599,8 +607,13 @@ def scan_working_tree(repo_root: Path, *, include_warn: bool = False) -> list[Fi
                 text = blob.stdout.decode("utf-8", "replace")
             except Exception:
                 continue
+        scanned_count += 1
         findings.extend(scan_text(text, rel, ruleset, include_warn=include_warn))
-    return findings
+    return findings, scanned_count
+
+
+def scan_working_tree(repo_root: Path, *, include_warn: bool = False) -> list[Finding]:
+    return scan_working_tree_counted(repo_root, include_warn=include_warn)[0]
    ```
    2. Re-derived validation command on this repository:
    ```
    $ python3 -c 'from pathlib import Path; from agent_workflows import leak_sanitizer as L; a=L.scan_working_tree(Path(".")); b,n=L.scan_working_tree_counted(Path(".")); print(len(a)==len(b), n, n==len([p for p in L._tracked_files(Path(".")) if p not in L._ALLOWED_PATHS]))'
    True 2930 True
    ```
    3. Delegation in `scan_working_tree`:
    ```python
    def scan_working_tree(repo_root: Path, *, include_warn: bool = False) -> list[Finding]:
        return scan_working_tree_counted(repo_root, include_warn=include_warn)[0]
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the doctor diff; paste the `sanitizer` evidence object from `python3 -m agent_workflows doctor --json` on this repo showing `scanned_files` nonzero. USE `--json`, NOT `--agent`: the compact `--agent` record does not carry the value at all (F-3), so an `--agent` paste cannot evidence this item and its absence there is expected, not a failure.
  - ALSO paste the `--agent` first record showing `evidence` as the bare key list, and state in one line that the value's absence there is F-3 and is deliberate. This is required so the executor cannot mistake F-3 for a bug they introduced, and so the record shows both surfaces were looked at.
  - Observed evidence: verified doctor diff, doctor --json evidence, and doctor --agent compact reduction:
    1. Diff of `agent_workflows/doctor.py`:
    ```diff
@@ -677,8 +677,9 @@ def probe_sanitizer(repo_root: Path) -> SanitizerProbeResult:
     """Scan tracked working tree for maintainer or machine identifying leaks."""
     res = SanitizerProbeResult()
     try:
-        findings = leak_sanitizer.scan_working_tree(repo_root)
+        findings, count = leak_sanitizer.scan_working_tree_counted(repo_root)
         res.findings = findings
+        res.scanned_files = count
     except Exception as exc:
         res.drift.append(
             core.Drift("<sanitizer>", "doctor.probe-failed", str(exc)[:120])
    ```
    2. Sanitizer evidence object from `python3 -m agent_workflows doctor --json` on this repo:
    ```json
    {
      "key": "sanitizer",
      "value": {
        "scanned_files": 2930,
        "findings": 0
      },
      "status": "clean",
      "detail": ""
    }
    ```
    `data.report.sanitizer`:
    ```json
    {
      "scanned_files": 2930,
      "findings": [],
      "drift": []
    }
    ```
    3. `python3 -m agent_workflows doctor --agent` first record evidence list:
    ```json
    "evidence": ["git", "env", "attention", "sanitizer", "artifacts"]
    ```
    The count's absence in the `aw doctor --agent` compact record is deliberate per F-3 (`agent_schema.sanitize_evidence_item` reduces dict-valued Evidence to key alone).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the test run passing (name the `-k` selector you actually used); revert the E-02 hunk IN THE WORKTREE and paste the test FAILING with `0 != 2`; restore. Paste `aw sanitize --agent` showing no finding in `tests/test_doctor.py`, and the final summary line of a BARE `python3 -m pytest` showing 0 failed.
  - Observed evidence: verified passing test, failure on reversion, clean sanitize, and bare pytest suite:
    1. Passing test run using selector `-k test_probe_sanitizer_scanned_files_count_and_failure_pin`:
    ```
    $ python3 -m pytest -o addopts="" tests/test_doctor.py -v -k test_probe_sanitizer_scanned_files_count_and_failure_pin
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=991819952
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 28 items / 27 deselected / 1 selected

    tests/test_doctor.py::DoctorTests::test_probe_sanitizer_scanned_files_count_and_failure_pin PASSED [100%]

    NOTE: 27 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    ======================= 1 passed, 27 deselected in 0.20s =======================
    ```
    2. Test failing when reverting E-02 hunk in worktree (`0 != 2`):
    ```
    =================================== FAILURES ===================================
    _____ DoctorTests.test_probe_sanitizer_scanned_files_count_and_failure_pin _____

    self = <tests.test_doctor.DoctorTests testMethod=test_probe_sanitizer_scanned_files_count_and_failure_pin>

        def test_probe_sanitizer_scanned_files_count_and_failure_pin(self) -> None:
            """E-03/E-04: probe_sanitizer reports scanned_files count and failure pin."""
            with tempfile.TemporaryDirectory() as tmp_git:
                repo = Path(tmp_git)
                _git(repo, "init", "-q")
                _git(repo, "config", "user.email", "t@e.com")
                _git(repo, "config", "user.name", "T")
                (repo / "clean.txt").write_text("clean\n", encoding="utf-8")
                planted = "/home/" + "someuser" + "/x"
                (repo / "leak.txt").write_text(planted + "\n", encoding="utf-8")
                _git(repo, "add", "clean.txt", "leak.txt")
                _git(repo, "commit", "-qm", "add two files")

                res = doctor.probe_sanitizer(repo)
    >           self.assertEqual(res.scanned_files, 2)
    E           AssertionError: 0 != 2

    tests/test_doctor.py:242: AssertionError
    NOTE: 27 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    =========================== short test summary info ============================
    FAILED tests/test_doctor.py::DoctorTests::test_probe_sanitizer_scanned_files_count_and_failure_pin
    ======================= 1 failed, 27 deselected in 0.28s =======================
    ```
    3. `aw sanitize --agent` (`python3 -m agent_workflows check-local-leaks . --agent`) on worktree showing clean findings:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
    4. Summary line of bare `python3 -m pytest`:
    ```
    2602 passed, 2 skipped, 3 warnings in 52.50s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the two failure-pair assertions from the diff, and paste the passing run. Then state explicitly that this assertion ALSO passes against the pre-change code and why that is correct (it is a characterization pin on the invariant `0` means "did not scan"; E-03 is the item that fails pre-change). Do NOT claim E-04 as evidence that the defect was fixed.
  - Observed evidence: verified two failure-pair assertions and characterized invariant:
    1. Two failure-pair assertions from the diff of `tests/test_doctor.py`:
    ```python
            self.assertEqual(res_fail.scanned_files, 0)
            self.assertTrue(any(d.rule == "doctor.probe-failed" for d in res_fail.drift))
    ```
    2. Passing test run output:
    ```
    tests/test_doctor.py::DoctorTests::test_probe_sanitizer_scanned_files_count_and_failure_pin PASSED [100%]
    ```
    3. Explicit statement: This assertion ALSO passes against the pre-change code, and that is correct: it is a characterization pin protecting the invariant that `0` means "did not scan" (on a path that is not a git repository where git ls-files fails, leaving `scanned_files` at default 0 with a `doctor.probe-failed` drift item), not evidence of the defect fix (E-03 is the item that fails pre-change with `0 != 2`).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. One new public function in `leak_sanitizer` (the old one keeps its exact contract and its single implementation), one assignment in doctor, and two assertions in one new test method. `aw doctor`'s sanitizer evidence value changes from a constant 0 to the real count.

WHAT IT DOES NOT DELIVER, STATED BEFORE APPROVAL BECAUSE THE PLAN ORIGINALLY IMPLIED OTHERWISE. The count becomes visible in `aw doctor --json` and in `data.report.sanitizer`. It does NOT become visible in `aw doctor --agent`: the compact `aw.agent/v1` record reduces a dict-valued `Evidence` to its key alone, and doctor declares no `--verbose` to select the branch that would carry the value, so the string `scanned_files` appears nowhere in `--agent` output before or after this change (F-3, measured both ways). Nor does it appear in the human render, whose clean sanitizer line is a fixed string (F-4). Neither is fixed here and both are recorded with their measurements. The exit code does not change; no finding count changes.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. Within `agent_workflows/leak_sanitizer.py` only the new `scan_working_tree_counted` and `scan_working_tree`'s one-line delegating body; within `agent_workflows/doctor.py` only `probe_sanitizer`; within `tests/test_doctor.py` only the one added method. `agent_workflows/local_leaks.py` is expected to need NO edit and is deliberately NOT declared: it re-exports the HISTORICAL surface and no consumer imports the new name (D-2). `agent_schema.sanitize_evidence_item`, `result_types.CommandResult.to_agent_record`, and `doctor.render_human_report` are deliberately NOT touched (F-3, F-4). `CHANGELOG.md` is deliberately not touched: no user-visible behavior changes. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. THE TWO CLAIMS EASIEST TO FAKE HERE, named so they are checked: (a) that the `--json` evidence shows a nonzero count, which requires the actual object and not a sentence saying it does; and (b) that E-04's failure-pair assertion is a characterization pin rather than proof of the fix, which V-04 requires you to state against yourself.

GENUINE STOP CONDITION: if rpqv4q has not executed (its `f.matched` defect still present in `doctor.probe_sanitizer`), stop. This is NOT expected to fire: rpqv4q is already `executed` as of review, and `doctor.probe_sanitizer` already reads `f.snippet` with only the scan call inside the `try`, so the dependency is satisfied and the restructuring E-02 must preserve is already in place.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition to `executed/` is performed with `aw ipd finalize`, never a raw `git mv`; the RUNNER owns it when it executes this plan in a lane, and the executor otherwise performs it. Then set backlog item `c0ppo0` `done` with `--evidence` citing the executed plan. The gate handoff is already provable: `c0ppo0` carries `- Blocks-Release: next` and this plan carries both `- From-Backlog: c0ppo0` and the same `- Blocks-Release: next`, and `check_engine.evaluate_blocking_close` on the item returns `legitimate=True`, `path='HANDOFF'`, so no de-gating is required.
