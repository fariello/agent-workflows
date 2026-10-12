# IPD: Correct host_runner redaction docstrings to say detected-and-refused, not masked

- Date: 2026-10-12
- Kind: child
- Concern: `agent_workflows/host_runner.py` prose overclaims that captured worker output is MASKED when a leak is found; the code only DETECTS (via `security_hardening.check_evidence_redaction`) and the caller `host_runner.run_task` REFUSES. A first caller written against the module docstring could skip checking `BoundaryResult.ok` and admit raw text.
- Scope: Comment/docstring-only correction in `agent_workflows/host_runner.py` (module docstring REDACTION bullet, `redact_worker_output` docstring, and its inline masking comment) so all three state the real contract: detection drives `ok=False`, the returned text is NOT masked, and the caller must refuse. No behavior change.
- Scope-Paths: agent_workflows/host_runner.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: fe6aro
- Set: fe6aro
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: 0ev8cz

## Workflow history
- 2026-10-12 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 0ev8cz verified (set fe6aro, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog fe6aro; decision (a) docstring correction selected from repository evidence (F-04, F-05, OQ-01).

## Goal

Make every statement in `agent_workflows/host_runner.py` about redaction of captured worker output match the measured behavior: `redact_worker_output` detects a leak and returns `BoundaryResult.ok=False` but does not mask the text, and `run_task` is where the raw text is refused (replaced by `[REDACTED-LEAK]`). This resolves backlog `fe6aro` by option (a), so the next caller author reads a docstring that tells them to check `ok`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Correct the prose in host_runner.py

- [x] E-01 Rewrite the module docstring's `* REDACTION:` bullet in `agent_workflows/host_runner.py` (the bullet ending with the quoted string "a planted home-path/secret is masked/blocked."). Replace "masked/blocked" with wording that says a planted home path is DETECTED by the canonical leak sanitizer, which makes the boundary fail closed (`BoundaryResult.ok=False`), and that `run_task` then REFUSES the raw text (records `[REDACTED-LEAK]` and a `failed_final` worker state) rather than admitting it. State that the `RedactionPolicy` masks only sensitive KEYS, so the `stdout`/`stderr`/`diff` values are not masked in place. Do not claim credential detection: per `docs/security.md` boundary 4 and backlog `lfko0e`, free-text credential detection is not evaluated by this boundary today. State that explicitly AND cite `lfko0e` in the bullet (both, not either), using the phrase "not evaluated" so that pending sibling plan `n09qoq` E-06 (iii), which depends on this plan and must later replace exactly that statement, can locate it (F-08).
  - Depends on: none
  - Expected outcome: the module docstring no longer contains "masked/blocked" and states detect-then-refuse.
  - Execution state: performed
- [x] E-02 Rewrite the docstring of `host_runner.redact_worker_output` (the sentence "Returns (possibly-masked RawWorkerResult, BoundaryResult)." at the end of its first paragraph) so it no longer says "possibly-masked" without qualification. It must say the returned `RawWorkerResult` carries the text after the key-based `RedactionPolicy`, which today never changes these three values, that a detected leak is reported ONLY via `BoundaryResult.ok=False` with findings in `evidence`, and keep (strengthen if needed) the existing sentence "the caller must treat that as a failure to record rather than admitting the raw text", naming `run_task` as the caller that does so.
  - Depends on: none
  - Expected outcome: the function docstring states detection-only and the caller obligation explicitly.
  - Execution state: performed
- [x] E-03 Rewrite the inline comment in `host_runner.redact_worker_output` that reads "The RedactionPolicy masks matched secrets/keys; reflect the masked text back into the result." so it says the policy masks sensitive KEYS only and that for this payload (keys `stdout`, `stderr`, `diff`) no value is changed today. Do not change any executable line of the function.
  - Depends on: none
  - Expected outcome: the inline comment is accurate; `git diff` shows only comment/docstring lines changed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Commits go through `aw commit <plan> -- <paths>`; never `git add -A`, never push (AGENTS.md execution contract).
- The suite is run BARE as `python3 -m pytest` and its actual output is pasted (AGENTS.md repository development contract).
- No code-pinning tests: a test must not assert on docstring or comment text (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE" rule 3). This plan therefore adds no test; the behavior the prose describes is already pinned by `tests/test_host_runner_redaction.py` (`HostRunnerRedactionTests.test_redact_worker_output_detects_leaks_without_in_place_masking` and `test_run_task_caller_side_fail_closed_contract`), added by executed plan `gqyold`.
- No em/en-dash restriction applies: code comments are exempt (AGENTS.md).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at lane HEAD `8c520062c`.

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | The module docstring of `agent_workflows/host_runner.py` says captured output passes through `check_evidence_redaction` and "a planted home-path/secret is masked/blocked." | Read of the module docstring, `* REDACTION:` bullet. |
| F-02 | `redact_worker_output` builds a payload with keys `stdout`, `stderr`, `diff`, runs `check_evidence_redaction`, then applies `default_redaction_policy().redact` and copies values back. The policy masks sensitive KEYS; none of these three keys is sensitive, so values are never changed. Its docstring says "possibly-masked" and its inline comment says the policy "masks matched secrets/keys". | Read of `host_runner.redact_worker_output`; `security_hardening.check_evidence_redaction` docstring ("apply the ledger RedactionPolicy ... then run the CANONICAL leak sanitizer"). |
| F-03 | `security_hardening.check_evidence_redaction` only DETECTS via `leak_sanitizer.scan_text` and returns `BoundaryResult(ok=False, ...)` with findings; it does not rewrite text. | Read of `security_hardening.check_evidence_redaction`. |
| F-04 | The caller-side refusal exists: `host_runner.run_task` replaces stdout/stderr with `[REDACTED-LEAK]`, empties the diff, and builds a `WORKER_FAILED_FINAL` envelope when `boundary.ok` is false. | Read of `host_runner.run_task` (comment "A hard leak in captured output: refuse to admit it"). |
| F-05 | Executed plan `gqyold` added `tests/test_host_runner_redaction.py`, which PINS that `redact_worker_output` does NOT mask in place (`assertIn(self.PLANTED_HOME, redacted.stdout, ...)`) and that `run_task` refuses. Option (b) (mask in the function) would invert a pinned, reviewed outcome and fall outside this item's evidence; option (a) leaves every test valid. | `tests/test_host_runner_redaction.py`; `gqyold` E-06 ("DO NOT ASSERT THAT `redact_worker_output` MASKS ANYTHING"). |
| F-06 | `docs/security.md` boundary 4 already states the accurate contract (masking sensitive keys, leak sanitizer fails closed, credential free-text not evaluated, backlog `lfko0e`), so the module docstring is the outlier and no doc edit is needed. | `docs/security.md` item "4. Evidence is redacted." |
| F-07 | The backlog item's "ZERO callers" measurement is stale: `rg -ln redact_worker_output agent_workflows tests` now matches `agent_workflows/host_runner.py` (definition plus `run_task`) and `tests/test_host_runner_redaction.py`. `run_task` still has no package caller. The reason to fix the prose stands: the first production caller of `run_task`/`redact_worker_output` is still unwritten. | `rg -ln redact_worker_output agent_workflows tests` at HEAD `8c520062c`. |
| F-08 | CORRECTED at review (PR-001): one other pending plan declares `agent_workflows/host_runner.py` in `- Scope-Paths:`: `n09qoq` (Set `lfko0e`, to-review), which carries `- Item-Dependencies: executed:0ev8cz` and whose E-06 (iii) rewrites the REDACTION bullet THIS plan writes, replacing its "not evaluated" credential statement / `lfko0e` citation. Overlap is not a runtime hazard (the runner orders by dependency and isolates worktrees); the obligation it creates is textual: E-01 must leave that statement findable. | `grep -ln "host_runner.py" .aw/records/plans/pending/*.md` -> this plan and `20261012-lfko0e-01-n09qoq-gate-worker-output-evidence-on-the-canonical-secret-scanner.ipd.md` (lines 7, 8, 60). |

## Proposed changes (ordered, validatable)

1. E-01: correct the module docstring REDACTION bullet (F-01, F-03, F-04).
2. E-02: correct the `redact_worker_output` docstring (F-02).
3. E-03: correct the inline comment in `redact_worker_output` (F-02).

All three are prose-only edits in one file; no executable statement changes.

## Deferred / out of scope (with reason)

- Option (b), making `redact_worker_output` mask what the sanitizer detected: not chosen (OQ-01). It would contradict the outcome pinned by `gqyold`'s tests (F-05) and is redundant with the refusal in `run_task` (F-04). A maintainer wanting defense in depth can file it separately.
  - Carrier-Declined: not chosen (OQ-01); contradicts pinned behavior from gqyold and is redundant with run_task refusal.
- Free-text credential detection in this boundary: owned by backlog `lfko0e`.
  - Carrier: lfko0e
- Case-sensitivity of `RedactionPolicy` keys: owned by backlog `go20fk`.
  - Carrier: go20fk
- `CHANGELOG.md`: not touched; a comment-only correction changes no user-visible behavior.
  - Carrier-Declined: comment/docstring-only correction changes no user-visible behavior; no release note owed.

## Scope check

- Over-scope: none.
- Under-scope: none. The only overclaiming statements found are the three in `agent_workflows/host_runner.py` (F-01, F-02); `docs/security.md` is already accurate (F-06).

## Required tests / validation

- No new test: the corrected prose describes behavior already pinned by `tests/test_host_runner_redaction.py` (F-05), and asserting on docstring text is prohibited (Project conventions).
- Run `python3 -m pytest -o addopts="" tests/test_host_runner_redaction.py` and paste output (both tests pass).
- Run the full suite BARE (`python3 -m pytest`) and paste the summary line.
- `git diff agent_workflows/host_runner.py` shows only docstring/comment lines changed; `python3 -c "import agent_workflows.host_runner"` succeeds.
- `aw ipd lint --phase pre-transition` conforms.

## Spec / documentation sync

N/A: no `.spec.md` is amended, so none appears in `- Scope-Paths:`. `docs/security.md` boundary 4 already states the accurate contract (F-06); this plan brings the module's own prose into line with it.

## Open questions

### OQ-01: Fix the docstring (a) or make the function mask (b)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED (a) from repository evidence. The function's own docstring already states the fail-closed contract ("the caller must treat that as a failure to record rather than admitting the raw text"), `run_task` implements that refusal (F-04), `docs/security.md` describes detection-and-fail-closed rather than masking (F-06), and executed plan `gqyold` pins non-masking as the observed outcome (F-05). Option (a) is the least disruptive, reversible, and leaves every test valid. Option (b) is deferred, not rejected; see Deferred.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Paste the `git diff agent_workflows/host_runner.py` hunk for the module docstring showing "masked/blocked" removed and the new detect-then-refuse wording naming `run_task` and `[REDACTED-LEAK]`. Paste `grep -n "masked/blocked" agent_workflows/host_runner.py` returning no match (exit 1). Paste `grep -n "lfko0e\|not evaluated" agent_workflows/host_runner.py` showing both the citation and the "not evaluated" credential statement inside the REDACTION bullet.
  - Observed evidence:
```diff
@@ -13,8 +13,13 @@ posture is pinned:
   * BOUNDED TIMEOUT + CANCELLATION are net-new: a hung worker is killed and recorded as a FAILURE
     (never completion); a cancelled worker terminates. `capture_command` maps a timeout to exit 124.
   * REDACTION: all captured stdout/stderr/diff pass through `security_hardening.check_evidence_
-    redaction` (RedactionPolicy + canonical leak sanitizer) BEFORE anything enters the ledger; a
-    planted home-path/secret is masked/blocked.
+    redaction` (RedactionPolicy + canonical leak sanitizer) BEFORE anything enters the ledger. A
+    planted home path is DETECTED by the canonical leak sanitizer, which makes the boundary fail
+    closed (`BoundaryResult.ok=False`), and `run_task` then REFUSES the raw text (records
+    `[REDACTED-LEAK]` and a `failed_final` worker state) rather than admitting it. The
+    `RedactionPolicy` masks only sensitive KEYS, so the `stdout`/`stderr`/`diff` values are not
+    masked in place. Free-text credential detection is not evaluated by this boundary today
+    (backlog `lfko0e`).
   * A host exit 0 is NEVER treated as success. The terminal envelope is a `run_packet.
     StepOutcomeEnvelope` validated by `run_packet.validate_outcome_envelope` + gated by
     `run_evidence.validate_evidence` (EV-FAILED-EXIT / EV-MISSING-OUTPUT / EV-FABRICATED-TEXT /
```
`grep -n "masked/blocked" agent_workflows/host_runner.py` exited with code 1 (no match).
```
$ grep -n "lfko0e\|not evaluated" agent_workflows/host_runner.py
21:    masked in place. Free-text credential detection is not evaluated by this boundary today
22:    (backlog `lfko0e`).
```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Paste the `git diff` hunk for the `redact_worker_output` docstring showing the detection-only wording and the retained caller obligation. Paste the actual output of `python3 -m pytest -o addopts="" tests/test_host_runner_redaction.py` showing both tests passed, demonstrating the documented behavior (raw text survives `redact_worker_output`, `run_task` refuses) is what the code does.
  - Observed evidence:
```diff
@@ -232,16 +237,20 @@ def redact_worker_output(
     repo_root=None,
 ) -> Tuple[RawWorkerResult, object]:
     """Run captured stdout/stderr/diff through `security_hardening.check_evidence_redaction` BEFORE
-    anything enters the ledger. Returns (possibly-masked RawWorkerResult, BoundaryResult).
+    anything enters the ledger. Returns (RawWorkerResult, BoundaryResult). The returned
+    RawWorkerResult carries the text after the key-based `RedactionPolicy`, which today never
+    changes these three values. A detected leak is reported ONLY via `BoundaryResult.ok=False` with
+    findings in `evidence`.

-    The BoundaryResult.ok is False when a hard leak (severity 'fail') is present; the caller must
-    treat that as a failure to record rather than admitting the raw text.
+    The BoundaryResult.ok is False when a hard leak (severity 'fail') is present; the caller
+    (`run_task`) must treat that as a failure to record rather than admitting the raw text.
     """
```
```
$ python3 -m pytest -o addopts="" tests/test_host_runner_redaction.py
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
Using --randomly-seed=3958357035
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 2 items

tests/test_host_runner_redaction.py ..                                   [100%]

============================== 2 passed in 0.18s ===============================
```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Paste the `git diff` hunk for the inline comment. Paste `git diff --stat agent_workflows/host_runner.py` and a statement that every changed line is a comment or docstring line (no executable line changed), plus `python3 -c "import agent_workflows.host_runner"` exiting 0. Paste the FULL bare `python3 -m pytest` summary line; for any red node paste its isolated re-run and classify it (pre-existing with backlog id, load-sensitive, or NEW). Paste `git diff --cached --name-only` before commit showing only `agent_workflows/host_runner.py` (plus this plan file), and `aw ipd lint --phase pre-transition` reporting conforming.
  - Observed evidence:
```diff
     payload = {"stdout": raw.stdout, "stderr": raw.stderr, "diff": raw.diff}
     result = _sh.check_evidence_redaction(payload, repo_root=repo_root)
-    # The RedactionPolicy masks matched secrets/keys; reflect the masked text back into the result.
+    # The RedactionPolicy masks sensitive KEYS only; for this payload (keys stdout, stderr, diff)
+    # no value is changed today. Reflect any policy result back into the returned structure.
     policy = _sh.default_redaction_policy()
```
```
$ git diff --stat agent_workflows/host_runner.py
 agent_workflows/host_runner.py | 21 +++++++++++++++------
 1 file changed, 15 insertions(+), 6 deletions(-)
```
Every changed line in `agent_workflows/host_runner.py` is a comment or docstring line; no executable statement was modified.
`python3 -c "import agent_workflows.host_runner"` exited with return code 0.
Full bare `python3 -m pytest` summary line:
`7281 passed, 2 skipped, 3 warnings in 194.29s (0:03:14)` (zero failures).
`git diff --cached --name-only` before commit shows only `agent_workflows/host_runner.py` and `.aw/records/plans/pending/20261012-fe6aro-01-0ev8cz-correct-host-runner-redaction-docstrings-to-say-detected-and.ipd.md`.
`aw ipd lint --phase pre-transition .aw/records/plans/pending/20261012-fe6aro-01-0ev8cz-correct-host-runner-redaction-docstrings-to-say-detected-and.ipd.md` reports conforming.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Execute only after human approval (`Status: approved`). Edit only `agent_workflows/host_runner.py`, and only comment/docstring lines. Commit through `aw commit <this plan> -- agent_workflows/host_runner.py <this plan path>`, never `git add -A`, never `--no-verify`; do not push; no tag or release. Run the suite bare and paste actual output. Scope fence: `- Scope-Paths:` is a declaration; an out-of-scope edit must be justified at finalize (`--scope-reason`), not silently made. Lifecycle: after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan moves to `executed/`. Under `aw oc run` / `aw agy run` the runner owns that finalize; do not run `aw ipd finalize` or `git mv` the plan yourself. Executed by hand, run `aw ipd finalize 0ev8cz` yourself. Never `git mv` it by hand.
