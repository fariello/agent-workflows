# IPD: Gate worker-output evidence on the canonical secret scanner's credential rules

- Date: 2026-10-12
- Kind: child
- Concern: `security_hardening.check_evidence_redaction` (and therefore `host_runner.redact_worker_output` and `host_runner.run_task`) admits a credential in free-text worker output, because its stage 2 runs only the identifying-info leak sanitizer and never the canonical secret scanner; the module docstring promises "the canonical leak/secret scanners".
- Scope: Add a stage 3 to `check_evidence_redaction` that runs the canonical secret scanner's REGEX `secret`-category rules (no entropy heuristic, no PII rules) over the key-redacted text and fails closed (refuse, not mask) on any finding; fail closed when the scanner cannot be loaded; make the scanner loader also find the copy shipped in the wheel; add outcome tests; correct the boundary 4 prose in `docs/security.md`, the `security_hardening` module docstring, and the `host_runner` REDACTION bullet.
- Scope-Paths: agent_workflows/security_hardening.py, agent_workflows/host_runner.py, tests/test_security_hardening.py, tests/test_host_runner_redaction.py, docs/security.md
- Item-Dependencies: executed:0ev8cz
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: security
- Priority: medium
- From-Backlog: lfko0e
- Set: lfko0e
- Order: 1
- Highest E allocated: 06
- Author: opencode
- Id: n09qoq

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: n09qoq verified (set lfko0e, attempt 1).
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed. Re-verified at 548700461: run-path probes admit AWS-shaped and bearer stdout today; scanner regex-only flags them (generic-secret-env/aws-access-key-id/bearer-token), not sha digests or email+IPv4; baseline 11 passed; scan_secrets.py is git-tracked under the force-included .aw/system.
- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog lfko0e; scanner-rule scope and refuse-vs-mask resolved from repository evidence (OQ-01, OQ-02, OQ-03).

## Goal

Make boundary 4 true to its own docstring: worker output that carries a credential (an AWS-shaped key, a bearer token, a `*_TOKEN=` assignment, a private-key block) is REFUSED by `check_evidence_redaction`, so `host_runner.run_task` records `[REDACTED-LEAK]` and `failed_final` instead of admitting it verbatim. Keep the false-positive rate on ordinary output near zero by gating only on the scanner's specific regex credential rules, not on its entropy or PII heuristics.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Failing outcome tests first

- [x] E-01 In `tests/test_security_hardening.py` class `EvidenceRedactionTests`, extend the `PAYLOADS` table (same 7-tuple shape: case, payload, expect_flag, expect_ok, forbidden, rule, why) with: (a) the AWS-shaped assignment under the innocuous key `stdout`, built at runtime from char codes exactly as `CanonicalScannerReuseTests.PLANTED_SECRET` is (`"".join(chr(c) for c in (65, 75, 73, 65))`), expecting `ok=False` and rule `generic-secret-env`; (b) `{"stdout": "Authorization: Bearer " + <30 alphanumeric chars built at runtime>}` expecting `ok=False` and rule `bearer-token`; and three HOLDING rows that must stay `ok=True`: a 64-hex sha256 digest plus a 40-hex commit sha in `stdout` (high-entropy, must not trip because entropy is not consulted), `"contact someone@example.com from 10.0.0.1"` (PII, must not trip because PII rules are not consulted), and the existing bearer-under-SENSITIVE-KEY row (stage 1 masks it, so stage 3 sees `[REDACTED]`). Run the class against UNMODIFIED code and record that rows (a) and (b) fail (the boundary holds them today) while the holding rows pass.
  - Depends on: none
  - Expected outcome: two new refusal rows fail on unmodified code; every holding row passes.
  - Execution state: performed
- [x] E-02 In `tests/test_host_runner_redaction.py` class `HostRunnerRedactionTests`, add a test driving `hr.run_task` with a runner double whose stdout is the runtime-built AWS-shaped assignment, asserting worker state `hr.WORKER_FAILED_FINAL`, envelope `status` `failed`, `stdout == stderr == "[REDACTED-LEAK]"`, `diff == ""`, and that the planted value is absent from the returned `RawWorkerResult` and from `json.dumps(envelope)`. Add a second test calling `hr.redact_worker_output` with the same stdout and asserting `boundary.ok is False` with a finding starting `generic-secret-env@`. Run against UNMODIFIED code and record that both fail (today `run_task` returns `completed`/`performed`, measured at authoring). Leave the existing `test_redact_worker_output_detects_leaks_without_in_place_masking` unchanged: this plan keeps refuse-not-mask (OQ-02).
  - Depends on: none
  - Expected outcome: both new tests fail on unmodified code; the two existing tests still pass.
  - Execution state: performed

### Task group 2: The fix

- [x] E-03 In `agent_workflows/security_hardening.py`, add stage 3 to `check_evidence_redaction`: after the existing stage 2 leak-sanitizer check (keep stage 2 and its refusal reason unchanged), load the canonical scanner via `_load_scan_secrets()` and call its `scan_text(text, "evidence", "evidence", use_entropy=False, use_pii=False)` on the SAME key-redacted flattened text; keep only findings whose `category == "secret"` (all severities, including `low`, because the measured probe trips `generic-secret-env`, which is `low`). If any remain, return `BoundaryResult(boundary=BOUNDARY_EVIDENCE_REDACTION, ok=False, reason="redacted evidence still trips the canonical secret scanner", evidence={"findings": [_finding_repr(f) ...]})`. `_finding_repr` yields `<rule>@<where>`, which for this call is `<rule>@evidence` (it reads the Finding's `where` field, `"evidence"`, before `location`), and never the matched value, so no credential is copied into the evidence; the scanner's own `preview` field must NOT be put into evidence. Do not reimplement any rule (the module contract is "does not reimplement any rule"). Do not change `scan_text_for_secrets` (it stays entropy+PII for its existing callers and test). Update the function docstring to describe three stages.
  - Depends on: E-01
  - Expected outcome: E-01 rows (a) and (b) refuse naming their rule; holding rows hold.
  - Execution state: performed
- [x] E-04 Make the scanner dependency fail closed and wheel-safe. (i) In `security_hardening._load_scan_secrets`, keep the source-checkout path and, when it is absent, also try `_compat.packaged_source_root()` joined with `workflows/assess/tools/scan_secrets.py` (the wheel maps `.aw/system` to `agent_workflows/_data/.aw/system`, per `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]`), raising the existing `FileNotFoundError` only when neither exists. (ii) In `check_evidence_redaction`, wrap BOTH the load AND the `scan_text` call of stage 3 in one `try/except Exception`; on any exception return `ok=False` with reason "canonical secret scanner unavailable; evidence refused" and `evidence={"error": type(exc).__name__}` (never the exception text, which may echo input) rather than holding or raising, so a broken install can never silently admit output. (iii) In `_load_scan_secrets`, if `spec.loader.exec_module(mod)` raises, `sys.modules.pop(name, None)` before re-raising: today the module is registered BEFORE exec, so a failed exec leaves a half-initialized `aw_scan_secrets` cached and every later call returns it (review probe: a stub left in `sys.modules` makes the next `scan_text` access raise `AttributeError`), turning one transient failure into a permanent one. Add a test in `EvidenceRedactionTests` that patches `sh._load_scan_secrets` (via `unittest.mock.patch.object`) to raise `FileNotFoundError` and asserts a CLEAN payload is refused with that reason; add a second case patching it to return an object whose `scan_text` raises `RuntimeError`, asserting the same refusal (no exception escapes). These exercise the code path and assert its outcome. The wheel fallback is not unit-tested (the source path is derived from `__file__`); V-04 instead proves the scanner file ships in the wheel.
  - Depends on: E-03
  - Expected outcome: unavailable scanner yields refusal, not admission or traceback; source checkout and wheel layouts both resolve.
  - Execution state: performed
- [x] E-05 Run the E-01/E-02/E-04 tests on the modified code and confirm all pass, together with every pre-existing test in `tests/test_security_hardening.py` and `tests/test_host_runner_redaction.py` (in particular `CanonicalScannerReuseTests` and `test_redact_worker_output_detects_leaks_without_in_place_masking`, which must be untouched and green). Then run the full suite BARE as `python3 -m pytest`.
  - Depends on: E-04
  - Expected outcome: targeted tests green; full suite shows no new failure versus a baseline measured at the execution base.
  - Execution state: performed

### Task group 3: Prose

- [x] E-06 Correct the prose to match the new behavior. (i) `docs/security.md` boundary 4 ("4. Evidence is redacted."): replace the sentence ending "credential detection in free text is not evaluated by this boundary today (backlog lfko0e)." with a statement that the canonical secret scanner's credential rules are also run and a credential fails closed, that the entropy and PII heuristics are deliberately NOT part of this gate (they would refuse routine output such as commit hashes), and that an unavailable scanner also fails closed. This is user-facing prose: write no em or en dashes. (ii) The `security_hardening` module docstring item 4 already says "passes the canonical leak/secret scanners"; make it say which secret rules (regex credential rules, no entropy/PII). (iii) The `host_runner` module docstring `* REDACTION:` bullet, as rewritten by `0ev8cz` (the `- Item-Dependencies:` edge guarantees it has landed): replace any statement that free-text credential detection is not evaluated (or the `lfko0e` citation) with the true one, that a credential is now also detected and refused by `run_task`. Change no executable line of `host_runner.py`.
  - Depends on: E-03
  - Expected outcome: no document in scope still claims credentials are unevaluated; `grep -n "lfko0e" docs/security.md agent_workflows/host_runner.py` finds no "not evaluated" claim.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Commits go through `aw commit <plan> -- <paths>`; never `git add -A`, never `--no-verify`, never push (AGENTS.md execution contract).
- The suite is run BARE as `python3 -m pytest`; actual output is pasted (AGENTS.md repository development contract).
- No code-pinning tests: every new test calls `check_evidence_redaction`, `redact_worker_output` or `run_task` and asserts on the returned result (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Planted secrets and home paths are assembled at runtime from fragments so no literal sits in tracked source (existing convention: `CanonicalScannerReuseTests.PLANTED_SECRET`, `HostRunnerRedactionTests.PLANTED_HOME`).
- Reuse, never fork, the canonical scanners (`security_hardening` module docstring "It does NOT invent new scanners"; `docs/security.md` "There is no forked scanner").
- Stdlib only (D138); `tests/test_packaging.py` pins runtime dependencies to `{"filelock"}`. `scan_secrets.py` imports only stdlib (`argparse, json, math, re, subprocess, sys, dataclasses, pathlib`).
- No em/en dashes in user-facing prose (`docs/security.md`); code comments and this plan are exempt.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at lane HEAD `66401aeb1`.

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | `check_evidence_redaction` stage 2 calls only `leak_sanitizer.scan_text`; the secret scanner is never consulted. | Read of `security_hardening.check_evidence_redaction`. |
| F-02 | The backlog probe reproduces: `host_runner.run_task` with stdout = AWS-shaped assignment returns worker state `completed`, envelope status `performed`. | `python3 -c ...run_task(pk, runner=lambda a,c,t:(0,s,''), ...)` printed `completed performed`. |
| F-03 | The canonical scanner with entropy and PII OFF flags the probe as `generic-secret-env` (severity `low`), and `Authorization: Bearer <30 chars>` as `bearer-token` (severity `low`). So gating on `high`/`medium` only would miss the measured case; all severities of `category == "secret"` must count. | `scan_text(s,"h","x",False,False)` -> `[('generic-secret-env', 'low')]`; payload probe -> `['bearer-token']`. |
| F-04 | FALSE-POSITIVE MEASUREMENT. Over the text of `git log -p -300` (the last 300 commits' diffs, a large realistic body of tool output), the regex secret rules with entropy+PII OFF fire ONCE (`github-token`, a fake token inside a plan's test-fixture path). With entropy+PII ON they fire 3353 times (`high-entropy-string` 2909, `email` 331, `ipv4` 60, `credit-card-candidate` 33, `us-phone` 10). A sha256 digest plus commit sha, and an email plus IPv4, produce zero secret-category regex findings. | Python probe at authoring, outputs quoted. |
| F-05 | `_load_scan_secrets` resolves the scanner only at `<repo_root>/.aw/system/workflows/assess/tools/scan_secrets.py` relative to the module file; in an installed wheel the tree lives at `agent_workflows/_data/.aw/system` (`pyproject.toml` force-include `".aw/system" = "agent_workflows/_data/.aw/system"`, and `_compat.packaged_source_root()` resolves it). Without E-04, adding the scanner to the boundary would turn a wheel-installed `run_task` into a `FileNotFoundError`. | Read of `security_hardening._load_scan_secrets`, `_compat.packaged_source_root`, `pyproject.toml`. |
| F-06 | `_finding_repr` returns `rule@where` (reads `where` before `location`; e.g. `generic-secret-env@evidence`, not `...@evidence:2`) and never the matched value, so refusal evidence carries no credential. | Probe: `_finding_repr(finding)` -> `generic-secret-env@evidence`. |
| F-07 | `run_task` already refuses on `boundary.ok == False` (replaces with `[REDACTED-LEAK]`, `WORKER_FAILED_FINAL`); it needs no code change, only the boundary must report the credential. `redact_worker_output` cannot mask a value (payload keys `stdout/stderr/diff` are not sensitive keys), and executed plan `gqyold` pins that non-masking in `test_redact_worker_output_detects_leaks_without_in_place_masking`. | Read of `host_runner.run_task`, `host_runner.redact_worker_output`; `tests/test_host_runner_redaction.py`. |
| F-08 | `run_task` / `redact_worker_output` have no production caller (`grep "_hr\.\(run_task\|redact_worker_output\)" agent_workflows/*.py` returns nothing), so the false-positive blast radius today is the tests alone. | grep at authoring. |
| F-09 | Pending plan `0ev8cz` (Set `fe6aro`, to-review) rewrites the `host_runner` REDACTION bullet and is instructed to state free-text credential detection is not evaluated "or cite `lfko0e`". If this plan landed first, that text would be written false; hence the `executed:0ev8cz` edge and E-06 (iii). Pending plan `pbl020` (Set `go20fk`) case-folds `RedactionPolicy` keys; it composes with this plan (stage 1 vs stage 3) and touches no file here except reading the same tests. | `.aw/records/plans/pending/20261012-fe6aro-01-0ev8cz-...ipd.md` E-01; `.aw/records/plans/pending/20261012-go20fk-01-pbl020-...ipd.md`. |
| F-10 | Baseline: `python3 -m pytest -o addopts="" -q tests/test_security_hardening.py tests/test_host_runner_redaction.py` -> `11 passed in 0.35s`. | Run at authoring. |

## Proposed changes (ordered, validatable)

1. E-01, E-02: write the failing outcome tests and record their red state (F-02, F-03).
2. E-03: add stage 3 using the canonical scanner's regex secret rules (F-01, F-03, F-04, F-06).
3. E-04: wheel-safe loader plus fail-closed on an unavailable scanner (F-05).
4. E-05: targeted and full-suite runs (F-10).
5. E-06: correct `docs/security.md`, the `security_hardening` and `host_runner` docstrings (F-09).

## Deferred / out of scope (with reason)

- Masking credentials in place inside `redact_worker_output` instead of refusing: deferred. Refusal is the contract `run_task` already implements and `gqyold` pins non-masking (F-07); masking would need value-level redaction the `RedactionPolicy` does not have.
  - Carrier-Declined: NO OBLIGATION REMAINS. Refusal fully closes the admission gap the backlog item reports (a credential is no longer admitted), and masking is an alternative remedy for the same gap rather than additional outstanding work; filing it would invent scope no caller has asked for (F-08: no production caller).
- Gating on the scanner's entropy and PII heuristics: rejected for this boundary on measured false-positive evidence (F-04). `scan_text_for_secrets` keeps them for its own callers.
  - Carrier-Declined: A MEASURED REJECTION, NOT DEFERRED WORK. F-04 shows the heuristics would refuse routine output thousands of times per 300 commits, so there is no obligation to carry.
- `RedactionPolicy` key case-folding: owned by `pbl020` (Set `go20fk`).
  - Carrier: pbl020
- CHANGELOG entry: none; `run_task` has no production caller (F-08), so no shipped behavior a user observes changes. A release-review can add one if desired.
  - Carrier-Declined: NOTHING USER-VISIBLE SHIPS (F-08), so there is no changelog obligation; release-review owns changelog curation.

## Scope check

- Over-scope: none.
- Under-scope: none. The only consumers of `check_evidence_redaction` are `host_runner.redact_worker_output` and the tests (grep `check_evidence_redaction` across `agent_workflows/` and `tests/`); both are in Scope-Paths.

## Required tests / validation

- E-01, E-02, E-04 tests fail (rows/tests named) on unmodified code and pass after E-03/E-04 (V-01, V-02, V-03, V-04).
- `python3 -m pytest -o addopts="" tests/test_security_hardening.py tests/test_host_runner_redaction.py` all green (V-05).
- Full bare `python3 -m pytest` with no new failure against an execution-base baseline (V-05).
- `aw sanitize --agent` shows no new finding from the new test fixtures (V-05).
- Prose diffs (V-06); `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

No `.spec.md` is amended (none governs `security_hardening`; `grep -rln "check_evidence_redaction\|security_hardening" .aw/records/specs` returned nothing), so none appears in `- Scope-Paths:`. `docs/security.md` boundary 4 is updated in E-06 because its current sentence ("credential detection in free text is not evaluated by this boundary today (backlog lfko0e)") becomes false once this lands.

## Open questions

### OQ-01: Which scanner rules gate admission?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence: the regex rules of `category == "secret"`, every severity, with `use_entropy=False, use_pii=False`. F-04 measures one regex hit across 300 commits of diffs versus 3353 with the heuristics on, and F-03 shows a severity cutoff at `medium` would miss the backlog's own probe. Reversible: a single argument pair in E-03.

### OQ-02: Mask or refuse?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED refuse. `run_task` already implements refusal on `ok=False`, `docs/security.md` describes fail-closed, and the reviewed `gqyold` test pins that `redact_worker_output` does not mask (F-07). Masking is deferred (see Deferred).

### OQ-03: What if the scanner cannot be loaded?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED fail closed (E-04), consistent with `docs/security.md` "The tool enforces the boundaries deterministically and fails closed", plus a wheel-layout lookup so the closed path is not hit on a normal install (F-05).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Paste the actual output of `python3 -m pytest -o addopts="" tests/test_security_hardening.py -k EvidenceRedactionTests` run on UNMODIFIED production code (before E-03) showing the failure message naming the AWS-shaped row and the bearer row as "accepted as clean", and no holding row in the failure list. Paste the `git diff tests/test_security_hardening.py` hunk adding the rows, showing the secret is built at runtime (no literal `AKIA`).
  - Observed evidence:
    Pytest on unmodified production code:
    ```
    FAILED tests/test_security_hardening.py::EvidenceRedactionTests::test_each_stage_catches_the_leak_class_only_it_can_see - AssertionError: Lists differ: ["  an AWS-shaped assignment under an inno[801 chars]ey."] != []
    First list contains 2 additional elements.
    First extra element 0:
    "  an AWS-shaped assignment under an innocuous key:\n    - expected stage 2 to REFUSE this payload; it was accepted as clean: ok=True boundary='evidence_redaction' reason='evidence redacted and clean under the canonical leak sanitizer'\n    - the refusal must name the 'generic-secret-env' rule; findings were None\n    this row exists because: THE CONTROL ROW FOR STAGE 3: secret scanner detects credential under innocuous key."
    Diff is 937 characters long. Set self.maxDiff to None to see it. : check_evidence_redaction mishandled 2 of 7 payloads. THE PLANTED-LEAK CONTROL ROW IS AMONG THE FAILURES, so the canonical sanitizer stage is not looking.
      an AWS-shaped assignment under an innocuous key:
        - expected stage 2 to REFUSE this payload; it was accepted as clean: ok=True boundary='evidence_redaction' reason='evidence redacted and clean under the canonical leak sanitizer'
        - the refusal must name the 'generic-secret-env' rule; findings were None
        this row exists because: THE CONTROL ROW FOR STAGE 3: secret scanner detects credential under innocuous key.
      a bearer token under an innocuous key:
        - expected stage 2 to REFUSE this payload; it was accepted as clean: ok=True boundary='evidence_redaction' reason='evidence redacted and clean under the canonical leak sanitizer'
        - the refusal must name the 'bearer-token' rule; findings were None
        this row exists because: THE CONTROL ROW FOR STAGE 3: secret scanner detects bearer token under innocuous key.
    ======================= 1 failed, 8 deselected in 0.40s ========================
    ```
    Git diff hunk:
    ```diff
    @@ -504,6 +504,14 @@ class EvidenceRedactionTests(unittest.TestCase):

         #: The leak is assembled from fragments at runtime with a lowercase alphanumeric probe user.
         PLANTED_HOME_LEAK = "/home/" + "hardeningprobe" + "/proj/notes.md"
    +    _AWS_PREFIX = "".join(chr(c) for c in (65, 75, 73, 65))
    +    PLANTED_AWS_SECRET = (
    +        f"aws_secret_access_key = {_AWS_PREFIX}IOSFODNN7EXAMPLE{_AWS_PREFIX}IOSFODNN7"
    +    )
    +    PLANTED_BEARER_TOKEN = (
    +        "Authorization: Bearer "
    +        + "".join(chr(c) for c in (65 + (i % 26) for i in range(30)))
    +    )

         PAYLOADS = (
             (
    @@ -533,6 +541,42 @@ class EvidenceRedactionTests(unittest.TestCase):
                 "home-path",
                 "THE CONTROL ROW FOR STAGE 2: leak sanitizer detects home path under innocuous key.",
             ),
    +        (
    +            "a sha256 digest and commit sha under an innocuous key",
    +            {"stdout": "sha256: " + "a" * 64 + " commit: " + "b" * 40},
    +            False,
    +            True,
    +            "",
    +            "",
    +            "Entropy heuristic must not trip because entropy is not consulted.",
    +        ),
    +        (
    +            "contact email and IPv4 under an innocuous key",
    +            {"stdout": "contact someone@example.com from 10.0.0.1"},
    +            False,
    +            True,
    +            "",
    +            "",
    +            "PII rules must not trip because PII is not consulted.",
    +        ),
    +        (
    +            "an AWS-shaped assignment under an innocuous key",
    +            {"stdout": PLANTED_AWS_SECRET},
    +            False,
    +            False,
    +            "",
    +            "generic-secret-env",
    +            "THE CONTROL ROW FOR STAGE 3: secret scanner detects credential under innocuous key.",
    +        ),
    +        (
    +            "a bearer token under an innocuous key",
    +            {"stdout": PLANTED_BEARER_TOKEN},
    +            False,
    +            False,
    +            "",
    +            "bearer-token",
    +            "THE CONTROL ROW FOR STAGE 3: secret scanner detects bearer token under innocuous key.",
    +        ),
         )
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Paste the actual pytest output of the two new `tests/test_host_runner_redaction.py` tests on UNMODIFIED production code showing both FAIL (the `run_task` one with worker state `completed`), and the same run showing the two pre-existing tests passing.
  - Observed evidence:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <repo_root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 4 items

    tests/test_host_runner_redaction.py .FF.                                 [100%]

    =================================== FAILURES ===================================
    _ HostRunnerRedactionTests.test_run_task_refuses_worker_output_carrying_credential _
    ...
    >       self.assertEqual(ws, hr.WORKER_FAILED_FINAL)
    E       AssertionError: 'completed' != 'failed_final'
    E       - completed
    E       + failed_final
    tests/test_host_runner_redaction.py:157: AssertionError
    ____ HostRunnerRedactionTests.test_redact_worker_output_detects_credentials ____
    ...
    >       self.assertFalse(
                boundary.ok, "BoundaryResult must be ok=False for planted secret"
            )
    E       AssertionError: True is not false : BoundaryResult must be ok=False for planted secret
    tests/test_host_runner_redaction.py:181: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_host_runner_redaction.py::HostRunnerRedactionTests::test_run_task_refuses_worker_output_carrying_credential
    FAILED tests/test_host_runner_redaction.py::HostRunnerRedactionTests::test_redact_worker_output_detects_credentials
    ========================= 2 failed, 2 passed in 0.32s ==========================
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Paste `git diff agent_workflows/security_hardening.py` for `check_evidence_redaction` showing stage 2 untouched, stage 3 calling the loaded scanner's `scan_text` with `use_entropy=False, use_pii=False`, the `category == "secret"` filter, and evidence built from `_finding_repr` only. Paste the actual pytest output of `-k EvidenceRedactionTests` on the MODIFIED code, passing. Paste a one-line probe printing `check_evidence_redaction({'stdout': s}).evidence` for the runtime-built AWS string, showing `generic-secret-env@evidence` and no fragment of the value (assert in the probe that neither the `AKIA`-prefixed key nor its scanner `preview` appears in `repr(evidence)`).
  - Observed evidence:
    `git diff agent_workflows/security_hardening.py` for `check_evidence_redaction`:
    ```diff
    @@ -263,9 +264,12 @@ def check_evidence_redaction(
     ) -> BoundaryResult:
         """Evidence MUST be redacted before it lands AND MUST NOT leak secrets/identifiers.

    -    Two-stage: (1) apply the ledger RedactionPolicy to the payload, then (2) run the CANONICAL
    -    leak sanitizer (:func:`leak_sanitizer.scan_text`) over the redacted text. If the redacted
    -    evidence still trips a leak rule, the boundary fails closed.
    +    Three-stage: (1) apply the ledger RedactionPolicy to the payload, (2) run the CANONICAL
    +    leak sanitizer (:func:`leak_sanitizer.scan_text`) over the redacted text, and (3) run the
    +    canonical secret scanner's regex credential rules (no entropy/PII heuristics). If the redacted
    +    evidence trips a leak or secret rule, or the secret scanner cannot be loaded, the boundary
    +    fails closed.
         """
         pol = policy or default_redaction_policy()
         redacted, _ = pol.redact(payload)
    @@ -280,6 +284,28 @@ def check_evidence_redaction(
                 reason="redacted evidence still trips the canonical leak sanitizer",
                 evidence={"findings": [_finding_repr(f) for f in fail_findings]},
             )
    +    try:
    +        scanner = _load_scan_secrets()
    +        raw_secret_findings = scanner.scan_text(
    +            text, "evidence", "evidence", use_entropy=False, use_pii=False
    +        )
    +    except Exception as exc:
    +        return BoundaryResult(
    +            boundary=BOUNDARY_EVIDENCE_REDACTION,
    +            ok=False,
    +            reason="canonical secret scanner unavailable; evidence refused",
    +            evidence={"error": type(exc).__name__},
    +        )
    +    secret_findings = [
    +        f for f in raw_secret_findings if getattr(f, "category", "") == "secret"
    +    ]
    +    if secret_findings:
    +        return BoundaryResult(
    +            boundary=BOUNDARY_EVIDENCE_REDACTION,
    +            ok=False,
    +            reason="redacted evidence still trips the canonical secret scanner",
    +            evidence={"findings": [_finding_repr(f) for f in secret_findings]},
    +        )
         return BoundaryResult(
             boundary=BOUNDARY_EVIDENCE_REDACTION,
             ok=True,
    ```
    Pytest output on modified code:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <repo_root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 11 items / 8 deselected / 3 selected

    tests/test_security_hardening.py ...                                     [100%]

    NOTE: 8 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ======================= 3 passed, 8 deselected in 0.24s ========================
    ```
    One-line probe printing evidence:
    ```
    $ python3 -c "from agent_workflows import security_hardening as sh; s = 'aws_secret_access_key = ' + ''.join(chr(c) for c in (65, 75, 73, 65)) + 'IOSFODNN7EXAMPLE' + ''.join(chr(c) for c in (65, 75, 73, 65)) + 'IOSFODNN7'; ev = sh.check_evidence_redaction({'stdout': s}).evidence; print('evidence:', ev); assert 'generic-secret-env@evidence' in ev.get('findings', []); assert 'AKIA' not in repr(ev); assert 'preview' not in repr(ev); print('probe assertions passed!')"
    evidence: {'findings': ['generic-secret-env@evidence']}
    probe assertions passed!
    ```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: Paste the `git diff` of `_load_scan_secrets` showing the `packaged_source_root()` fallback and of the fail-closed branch. Paste the passing output of the two new patched-loader cases. Paste the `_load_scan_secrets` hunk showing the `sys.modules.pop` on exec failure. Paste the output of `python3 -c "from agent_workflows import security_hardening as sh; print(sh._load_scan_secrets().__file__)"` from the source checkout, printed repo-relative (do not paste an absolute home path). Paste `python3 -m build --wheel --outdir <tmp>` followed by `python3 -m zipfile -l <wheel> | grep assess/tools/scan_secrets.py` showing `agent_workflows/_data/.aw/system/workflows/assess/tools/scan_secrets.py` is in the wheel, which is the file the fallback resolves.
  - Observed evidence:
    `git diff` of `_load_scan_secrets` showing `packaged_source_root()` fallback, `sys.modules.pop` on exec error, and fail-closed branch:
    ```diff
    @@ -532,6 +558,12 @@ def _load_scan_secrets() -> Any:
             / "scan_secrets.py"
         )
         if not tool_path.is_file():
    +        pkg_root = _compat.packaged_source_root()
    +        if pkg_root is not None:
    +            candidate = pkg_root / "workflows" / "assess" / "tools" / "scan_secrets.py"
    +            if candidate.is_file():
    +                tool_path = candidate
    +    if not tool_path.is_file():
             raise FileNotFoundError(f"canonical secret scanner not found at {tool_path}")
         import sys

    @@ -542,7 +574,11 @@ def _load_scan_secrets() -> Any:
         mod = importlib.util.module_from_spec(spec)
         # Register BEFORE exec so @dataclass in the tool can resolve cls.__module__ (Py3.12+/3.14).
         sys.modules[name] = mod
    -    spec.loader.exec_module(mod)
    +    try:
    +        spec.loader.exec_module(mod)
    +    except Exception:
    +        sys.modules.pop(name, None)
    +        raise
         return mod
    ```
    Output of the two new patched-loader cases:
    ```
    $ python3 -m pytest -o addopts="" tests/test_security_hardening.py -k "test_scanner_unavailable"
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <repo_root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 11 items / 9 deselected / 2 selected

    tests/test_security_hardening.py ..                                      [100%]

    NOTE: 9 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ======================= 2 passed, 9 deselected in 0.22s ========================
    ```
    Scanner file path from source checkout (repo-relative):
    ```
    $ python3 -c "from pathlib import Path; from agent_workflows import security_hardening as sh; p = Path(sh._load_scan_secrets().__file__).resolve(); print(p.relative_to(Path.cwd()))"
    .aw/system/workflows/assess/tools/scan_secrets.py
    ```
    Wheel inspect showing `scan_secrets.py`:
    ```
    $ TMP_DIR=$(mktemp -d /tmp/aw-wheel-XXXXXX)
    $ python3 -m build --wheel --outdir "$TMP_DIR"
    * Creating isolated environment: venv+pip...
    * Installing packages in isolated environment:
      - hatchling
    * Getting build dependencies for wheel...
    * Installed build dependency versions:
      - hatchling==1.32.4
    * Building wheel...
    Successfully built agent_workflows-1.3.0rc2.dev9906+g1c323b0f9.d20261013-py3-none-any.whl
    $ python3 -m zipfile -l "$TMP_DIR"/*.whl | grep "assess/tools/scan_secrets.py"
    agent_workflows/_data/.aw/system/workflows/assess/tools/scan_secrets.py 2020-02-02 00:00:00        27610
    $ rm -rf "$TMP_DIR"
    ```
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: Paste the actual output of `python3 -m pytest -o addopts="" tests/test_security_hardening.py tests/test_host_runner_redaction.py` with its summary line showing zero failed (11 passed at authoring; this plan adds 4 test functions: the two E-02 tests and the two E-04 cases if written as separate methods. The E-01 rows are table rows inside an existing test, not new tests. Counts are context, not the bar). Paste your execution-base baseline of the FULL bare `python3 -m pytest` summary line measured BEFORE the change and the FULL bare run summary AFTER, compare the failure lists BY NAME; for every red node paste its isolated re-run and classify it (pre-existing with backlog id, load-sensitive, or NEW; NEW must be fixed, never accepted). Paste `aw sanitize --agent` output showing no finding located in the two test files.
  - Observed evidence:
    Targeted test run:
    ```
    $ python3 -m pytest -o addopts="" tests/test_security_hardening.py tests/test_host_runner_redaction.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <repo_root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 15 items

    tests/test_host_runner_redaction.py ....                                 [ 26%]
    tests/test_security_hardening.py ...........                             [100%]

    ============================== 15 passed in 0.33s ==============================
    ```
    Full suite execution baseline (BEFORE):
    `8023 passed, 4 skipped, 18 xfailed, 3 warnings in 548.97s (0:09:08)`
    Full suite post-change (AFTER):
    `8027 passed, 4 skipped, 18 xfailed, 3 warnings in 923.15s (0:15:23)`
    Comparison by name: zero failures before, zero failures after. Exactly 4 new tests passed (8027 - 8023 = 4).
    `aw sanitize --agent`:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":4936,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
    No findings located in the test files or working tree.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: Paste `git diff docs/security.md agent_workflows/host_runner.py` and the `security_hardening` module-docstring hunk, showing the corrected boundary 4 wording and that only docstring/comment lines changed in `host_runner.py`. Paste `grep -n "not evaluated" docs/security.md agent_workflows/host_runner.py agent_workflows/security_hardening.py` returning no credential-related match, and `grep -nP "[\x{2013}\x{2014}]" docs/security.md` returning nothing new. Paste `git diff --cached --name-only` before the commit showing only the five `- Scope-Paths:` entries plus this plan file, and `aw ipd lint --phase pre-transition` reporting conforming.
  - Observed evidence:
    `git diff docs/security.md agent_workflows/host_runner.py`:
    ```diff
    diff --git a/agent_workflows/host_runner.py b/agent_workflows/host_runner.py
    index 3b7f835d8..4f967d38b 100644
    --- a/agent_workflows/host_runner.py
    +++ b/agent_workflows/host_runner.py
    @@ -13,13 +13,12 @@ posture is pinned:
       * BOUNDED TIMEOUT + CANCELLATION are net-new: a hung worker is killed and recorded as a FAILURE
         (never completion); a cancelled worker terminates. `capture_command` maps a timeout to exit 124.
       * REDACTION: all captured stdout/stderr/diff pass through `security_hardening.check_evidence_
    -    redaction` (RedactionPolicy + canonical leak sanitizer) BEFORE anything enters the ledger. A
    -    planted home path is DETECTED by the canonical leak sanitizer, which makes the boundary fail
    +    redaction` (RedactionPolicy + canonical leak/secret scanners) BEFORE anything enters the ledger. A
    +    planted home path or credential is DETECTED by the canonical scanners, which makes the boundary fail
         closed (`BoundaryResult.ok=False`), and `run_task` then REFUSES the raw text (records
         `[REDACTED-LEAK]` and a `failed_final` worker state) rather than admitting it. The
         `RedactionPolicy` masks only sensitive KEYS, so the `stdout`/`stderr`/`diff` values are not
    -    masked in place. Free-text credential detection is not evaluated by this boundary today
    -    (backlog `lfko0e`).
    +    masked in place; a credential in free text is now also detected and refused by `run_task`.
       * A host exit 0 is NEVER treated as success. The terminal envelope is a `run_packet.
         StepOutcomeEnvelope` validated by `run_packet.validate_outcome_envelope` + gated by
         `run_evidence.validate_evidence` (EV-FAILED-EXIT / EV-MISSING-OUTPUT / EV-FABRICATED-TEXT /
    diff --git a/docs/security.md b/docs/security.md
    index de99ebf24..cbaee9be5 100644
    --- a/docs/security.md
    +++ b/docs/security.md
    @@ -24,9 +24,11 @@ Leak and secret checks REUSE the repository's canonical tooling. There is no for
     3. Skills are least privilege. `check_skill_least_privilege` refuses a skill entry point that
        inlines the canonical authoritative body or fails package validation.
     4. Evidence is redacted. `check_evidence_redaction` applies the ledger redaction policy (masking
    -   sensitive keys) and then runs the CANONICAL leak sanitizer over the payload; maintainer or machine
    -   identifying info (such as a home path) fails closed with findings in evidence, while credential
    -   detection in free text is not evaluated by this boundary today (backlog lfko0e).
    +   sensitive keys), runs the CANONICAL leak sanitizer over the payload, and runs the canonical
    +   secret scanner's credential rules. Maintainer or machine identifying info (such as a home path)
    +   and credentials fail closed with findings in evidence. The entropy and PII heuristics are
    +   deliberately not part of this gate because they would refuse routine output such as commit hashes.
    +   An unavailable secret scanner also fails closed.
     5. The real HOME is excluded from probes. `check_real_home_excluded` reuses
        `assert_isolated_base`, which refuses a base equal to or containing the real home.
     6. Untrusted text is isolated as data. `check_untrusted_text_isolated` refuses any path that
    ```
    Module docstring hunk in `agent_workflows/security_hardening.py`:
    ```diff
    @@ -18,7 +19,8 @@ that returns a :class:`BoundaryResult` (``ok`` plus a machine-readable ``reason
       3. ``check_skill_least_privilege`` - a skill entry point carries no inlined authority.
       4. ``check_evidence_redaction``    - evidence is redacted before it lands (reuses the
                                             run ledger RedactionPolicy) AND passes the
    -                                        canonical leak/secret scanners.
    +                                        canonical leak/secret scanners (regex credential
    +                                        rules, no entropy/PII).
       5. ``check_real_home_excluded``    - host probes refuse the real HOME (reuses the
                                             capability-registry isolation guard).
       6. ``check_untrusted_text_isolated`` - repository/tool/inter-agent text is treated as
    ```
    Prose verification:
    ```
    $ grep -n "not evaluated" docs/security.md agent_workflows/host_runner.py agent_workflows/security_hardening.py
    (exit code 1: 0 matches)
    $ grep -nP "[\x{2013}\x{2014}]" docs/security.md
    (exit code 1: 0 matches)
    ```
    Staged paths verification before commit:
    ```
    $ git diff --cached --name-only
    .aw/records/plans/pending/20261012-lfko0e-01-n09qoq-gate-worker-output-evidence-on-the-canonical-secret-scanner.ipd.md
    agent_workflows/host_runner.py
    agent_workflows/security_hardening.py
    docs/security.md
    tests/test_host_runner_redaction.py
    tests/test_security_hardening.py
    ```
    Lint pre-transition:
    ```
    $ aw ipd lint --phase pre-transition .aw/records/plans/pending/20261012-lfko0e-01-n09qoq-gate-worker-output-evidence-on-the-canonical-secret-scanner.ipd.md
    -    ◕  approved     plan        20261012-lfko0e-01-n09qoq  [medium]  conforming
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Execute only after human approval (`Status: approved`) and after `0ev8cz` has executed (`- Item-Dependencies:`). Edit only the five `- Scope-Paths:` files; in `agent_workflows/host_runner.py` change only docstring/comment lines. Commit through `aw commit <this plan> -- <paths>`, never `git add -A`, never `--no-verify`; do not push; no tag or release. Run the suite bare and paste actual output into each V-item. After every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan moves to `executed/`. Under `aw oc run` / `aw agy run` the runner owns begin and finalize, so do not run `aw ipd finalize` yourself; executed by hand, use `aw ipd begin n09qoq` and `aw ipd finalize n09qoq`. Never `git mv` it by hand.

All open questions (OQ-01, OQ-02, OQ-03) are resolved; none blocks. Scope fence: `- Scope-Paths:` is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), not silently made and not a reason to stop. You MUST paste the actual runner output for every test claim; never report a run that was not performed. Verify `git diff --cached --name-only` before every commit (shared checkout). DO NOT put a matched value, a scanner `preview`, or an exception message into any `BoundaryResult.evidence`, test failure message, or pasted V-item evidence.
