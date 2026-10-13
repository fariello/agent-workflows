# IPD: Case-fold RedactionPolicy sensitive-key matching

- Date: 2026-10-12
- Kind: child
- Concern: `RedactionPolicy` sensitive-key matching is case-sensitive, so a secret under `TOKEN` or `Authorization` reaches the run ledger unmasked.
- Scope: Fold key case on both sides of the sensitive-key comparison in `run_ledger_store.RedactionPolicy`, add outcome tests for mixed-case keys, and record the behavior change in CHANGELOG and docs/evidence.md.
- Scope-Paths: agent_workflows/run_ledger_store.py, tests/test_redaction_key_casefold.py, CHANGELOG.md, docs/evidence.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: security
- Priority: medium
- From-Backlog: go20fk
- Set: go20fk
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: pbl020

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: pbl020 verified (set go20fk, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog go20fk; review-ready.

## Goal

Make `RedactionPolicy` match sensitive keys case-insensitively, so that every spelling of a configured secret-bearing key (`token`, `TOKEN`, `Token`, `Authorization`) is masked before a record lands in the run ledger or in redacted worker output. Folding is chosen over widening the key list because it cannot be forgotten when a new spelling appears (backlog go20fk open question).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Reproduce, then fix

- [x] E-01 Add `tests/test_redaction_key_casefold.py` with outcome tests that call `RedactionPolicy.redact` (and `security_hardening.default_redaction_policy().redact`) on payloads keyed `TOKEN`, `Authorization`, `Api_Key`, nested `{'outer': {'PASSWORD': ...}}`, and list `{'items': [{'Secret': ...}]}`, asserting the secret value is replaced by the mask, `was_redacted` is True, the ORIGINAL key spelling is preserved in the output, a non-sensitive key (`stdout`) is untouched, a policy constructed with an uppercase configured key (`sensitive_keys=['X-Api-Key']`) masks a lowercase payload key `x-api-key`, a payload with an int key (`{3: 'v'}`) is returned unchanged without raising, and a list value under a mixed-case sensitive key (`{'Token': ['a', 'b']}`) is masked whole. Run it against unmodified code and record the failures.
  - Depends on: none
  - Expected outcome: new test file exists; the mixed-case cases fail on unmodified code (reproducing the defect) while the lowercase control, the non-sensitive-key case and the int-key case pass.
  - Execution state: performed

- [x] E-05 In the same test module, add one END-TO-END ledger test: a `run_ledger_store.RunLedgerStore` in `tmp_path` constructed with `security_hardening.default_redaction_policy()`, append a schema-valid `kind: run` seed record (the shape `tests/test_capture_command_contract.py::test_capture_command_persistence_clean_in_real_store` uses: `schema_version`, `kind`, `run_id`, `actor`, `parent`, `workflow_digest`, `requirement_digest`, `repo`, `head`) with an extra top-level key `'Authorization': 'Bearer s3cr3t'` (an extra top-level key passes schema validation; measured at review), then assert the ledger FILE text does not contain `s3cr3t` and `read_records()` shows the mask. Run it against unmodified code and record the failure.
  - Depends on: E-01
  - Expected outcome: the ledger test fails on unmodified code (the ledger file contains `s3cr3t`, F-7) and passes after E-02.
  - Execution state: performed

- [x] E-02 In `agent_workflows/run_ledger_store.py`, change `RedactionPolicy.__init__` to store `self.sensitive_keys = frozenset(k.casefold() for k in sensitive_keys)` (configured keys are typed `Sequence[str]`; a non-string configured key now raises `AttributeError` at construction, which is the correct loud failure for a misconfigured policy, and every in-tree constructor passes strings: `security_hardening.default_redaction_policy` and tests only) and change `RedactionPolicy._redact_value` so the check reads `isinstance(parent_key, str) and parent_key.casefold() in self.sensitive_keys`. Do not rename payload keys and do not alter pattern, list, dict, or custom-hook handling.
  - Depends on: E-01, E-05
  - Expected outcome: the E-01 and E-05 tests pass; output dicts keep their original key spellings; a non-string PAYLOAD key (e.g. int `3`) is still not matched and does not raise (the `isinstance` guard is what keeps the new `.casefold()` call from raising on it; the old membership test never raised either). Probe at review applying exactly these two edits: `{'TOKEN','Authorization','outer':{'PASSWORD'},'items':[{'Secret'}]}` all masked, `stdout` and `3` untouched, `X-Api-Key` configured masks `x-api-key`.
  - Execution state: performed

### Task group 2: Regression and documentation

- [x] E-03 Run the existing redaction-adjacent suites (`tests/test_security_hardening.py`, `tests/test_host_runner_redaction.py`, `tests/test_host_capability_registry.py`, plus every test module that exercises `RunLedgerStore`, found at execution time with `grep -ln RunLedgerStore tests/`) and then the full fast suite bare (`python3 -m pytest`).
  - Depends on: E-02
  - Expected outcome: the named suites pass; the bare suite shows no failure by test name that is absent from a same-session baseline taken on the base commit before E-02.
  - Execution state: performed

- [x] E-04 Document the behavior: add a CHANGELOG.md entry under the top `## 2.0.0 (pending)` section stating sensitive-key matching is now case-insensitive (security fix, backlog go20fk), and amend the `## Redaction` paragraph of `docs/evidence.md` to say sensitive keys are matched case-insensitively. No em or en dashes in this user-facing prose.
  - Depends on: E-02
  - Expected outcome: both files carry the new sentence; `aw sanitize --agent` reports no new leak finding.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Suite is run bare as `python3 -m pytest` (AGENTS.md repo-local development contract); narrowed runs use `python3 -m pytest -o addopts="" <files>` when per-test counts are needed.
- Tests must exercise behavior, not pin source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): the new tests call `redact` and assert on returned dicts and flags.
- `security_hardening.default_redaction_policy` reuses `run_ledger_store.RedactionPolicy` rather than forking it (its docstring: "Reuses the run ledger :class:`RedactionPolicy` (Order 03/04); does not fork it."), so the fix belongs in `RedactionPolicy` alone and automatically covers `host_runner.redact_worker_output` (which calls `_sh.default_redaction_policy()`) and `host_capability_registry` (which accepts a `redaction_policy`).
- Commits go through `aw commit <plan> -- <paths>`; never push.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | Key match is an exact frozenset membership test with no folding. | `run_ledger_store.RedactionPolicy._redact_value`: `if parent_key in self.sensitive_keys:`; `__init__`: `self.sensitive_keys = frozenset(sensitive_keys)` |
| F-2 | The default key list is all lowercase. | `security_hardening.default_redaction_policy`: `"authorization", "auth_token", "token", "api_key", "apikey", "secret", "password", "bearer"` |
| F-3 | Probe in backlog go20fk: `{'TOKEN': 's3cr3t'}` returns unmasked; nested dicts and lists are already handled. | backlog go20fk body, measured at HEAD 4fbbc8386 |
| F-4 | `sensitive_keys` is read only inside `_redact_value`; no other caller reads the attribute, so folding the stored set is safe. | `grep -rn "\.sensitive_keys" agent_workflows tests` returns only the `_redact_value` line |
| F-6 | The ledger path is live through every caller that supplies a policy: `RunLedgerStore.append_held` applies `redaction_policy or self._redaction_policy`, and `host_capability_registry.run_isolated_probe` / `evaluate_negative_probe` call `redaction_policy.redact(payload)`. The other in-tree redactors already fold case (`run_cli._redact_output` uppercases keys; `run_evidence._SENSITIVE_KEY_SUBSTRINGS` is uppercase), so `RedactionPolicy` was the outlier. | Review at `46d887d1e`: `default_redaction_policy().redact({'TOKEN':'s','Authorization':'b'})` returned both unmasked, `was_redacted` False. |
| F-7 | The defect reaches the durable ledger end to end. | Review probe: `RunLedgerStore(<tmp>, redaction_policy=default_redaction_policy())`, appending the seed record above plus `token: s3cr3t` wrote no `s3cr3t`; the same with `Authorization: Bearer s3cr3t` wrote `s3cr3t` to the ledger file. |
| F-5 | Existing test `test_security_hardening` uses lowercase `authorization`, which continues to match after folding. | `tests/test_security_hardening.py` PAYLOADS row "a bearer token under a SENSITIVE KEY" |

## Proposed changes (ordered, validatable)

1. Add failing outcome tests (E-01, V-01) and the end-to-end ledger test (E-05, V-05).
2. Case-fold the configured set and the compared key in `RedactionPolicy` (E-02, V-02).
3. Regression run (E-03, V-03).
4. CHANGELOG and docs/evidence.md note (E-04, V-04).

## Deferred / out of scope (with reason)

- Widening the default key list (e.g. adding `x-api-key`, `access_token`): a separate policy decision; folding addresses the reported defect. Not in backlog go20fk's ask.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Normalizing separators (`api-key` vs `api_key`): different defect class, not reported; would change matching semantics beyond case.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Free-text credential detection: tracked separately (backlog lfko0e per docs/security.md).
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Rewriting payload keys to lowercase: rejected; it would alter non-secret record structure for every ledger caller.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none.
- Under-scope: none; all ledger and worker-output callers share `RedactionPolicy` (F-4, conventions), so one change covers them.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_redaction_key_casefold.py` fails before E-02 and passes after (V-01, V-02).
- `python3 -m pytest -o addopts="" tests/test_security_hardening.py tests/test_host_runner_redaction.py tests/test_host_capability_registry.py` plus the `RunLedgerStore` test modules pass (V-03).
- Bare `python3 -m pytest` shows no new failure versus a same-session baseline (V-03).
- `aw ipd lint` conforming; `aw sanitize --agent` clean on changed files (V-04).

## Spec / documentation sync

- No spec governs `RedactionPolicy` key matching (search of `.aw/records/specs` for `RedactionPolicy`/`sensitive_keys` found none), so no spec amendment.
- docs/evidence.md `## Redaction` paragraph and CHANGELOG.md updated (E-04).

## Open questions

### OQ-01: Fold the key case, or widen the declared key list?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: Fold, on both the configured keys and the payload key at comparison time, without renaming payload keys. Backlog go20fk recommends folding as "the smaller change and the one that cannot be forgotten when a new key spelling appears"; F-4 shows no other reader of `sensitive_keys` depends on the original spelling.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted pytest output of `tests/test_redaction_key_casefold.py` run on unmodified `run_ledger_store.py` showing the mixed-case cases FAILED and the lowercase, non-sensitive and int-key controls passed.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" tests/test_redaction_key_casefold.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=2007411452
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 9 items

    tests/test_redaction_key_casefold.py F..FFFF.F                           [100%]

    =================================== FAILURES ===================================
    _ RedactionKeyCasefoldTests.test_default_policy_redacts_mixed_case_sensitive_keys _

    self = <tests.test_redaction_key_casefold.RedactionKeyCasefoldTests testMethod=test_default_policy_redacts_mixed_case_sensitive_keys>

        def test_default_policy_redacts_mixed_case_sensitive_keys(self) -> None:
            """Call security_hardening.default_redaction_policy().redact on payloads keyed TOKEN, Authorization, Api_Key."""
            policy = security_hardening.default_redaction_policy()
            payload = {
                "TOKEN": "tok123",
                "Authorization": "Bearer auth123",
                "Api_Key": "key123",
            }
            redacted, was_redacted = policy.redact(payload)
    >       self.assertTrue(was_redacted)
    E       AssertionError: False is not true

    tests/test_redaction_key_casefold.py:34: AssertionError
    _____ RedactionKeyCasefoldTests.test_list_nested_mixed_case_sensitive_keys _____

    self = <tests.test_redaction_key_casefold.RedactionKeyCasefoldTests testMethod=test_list_nested_mixed_case_sensitive_keys>

        def test_list_nested_mixed_case_sensitive_keys(self) -> None:
            """List with {'items': [{'Secret': ...}]} is redacted."""
            policy = security_hardening.default_redaction_policy()
            payload = {"items": [{"Secret": "sec123"}]}
            redacted, was_redacted = policy.redact(payload)
    >       self.assertTrue(was_redacted)
    E       AssertionError: False is not true

    tests/test_redaction_key_casefold.py:57: AssertionError
    _______ RedactionKeyCasefoldTests.test_nested_mixed_case_sensitive_keys ________

    self = <tests.test_redaction_key_casefold.RedactionKeyCasefoldTests testMethod=test_nested_mixed_case_sensitive_keys>

        def test_nested_mixed_case_sensitive_keys(self) -> None:
            """Nested dict with {'outer': {'PASSWORD': ...}} is redacted."""
            policy = security_hardening.default_redaction_policy()
            payload = {"outer": {"PASSWORD": "pwd123"}}
            redacted, was_redacted = policy.redact(payload)
    >       self.assertTrue(was_redacted)
    E       AssertionError: False is not true

    tests/test_redaction_key_casefold.py:48: AssertionError
    _ RedactionKeyCasefoldTests.test_end_to_end_ledger_redacts_mixed_case_authorization _

    self = <tests.test_redaction_key_casefold.RedactionKeyCasefoldTests testMethod=test_end_to_end_ledger_redacts_mixed_case_authorization>

        def test_end_to_end_ledger_redacts_mixed_case_authorization(self) -> None:
            """E-05: RunLedgerStore in tmp_path with default_redaction_policy masks mixed-case key."""
            with tempfile.TemporaryDirectory() as tmpdir:
                ledger_path = Path(tmpdir) / "ledger.jsonl"
                policy = security_hardening.default_redaction_policy()
                store = RunLedgerStore(ledger_path, redaction_policy=policy)

                seed = {
                    "schema_version": 2,
                    "kind": "run",
                    "run_id": "run-abc123ff",
                    "actor": "executor",
                    "parent": "",
                    "workflow_digest": "0" * 64,
                    "requirement_digest": "1" * 64,
                    "repo": "test-repo",
                    "head": "a" * 40,
                    "Authorization": "Bearer s3cr3t",
                }
                store.append(seed)

                # Assert the ledger file text does not contain s3cr3t
                ledger_text = ledger_path.read_text(encoding="utf-8")
    >           self.assertNotIn(
                    "s3cr3t",
                    ledger_text,
                    f"Ledger file leaked raw secret: {ledger_text}",
                )
    E           AssertionError: 's3cr3t' unexpectedly found in '{"Authorization":"Bearer s3cr3t","actor":"executor","head":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","kind":"run","parent":"","prev_hash":"0000000000000000000000000000000000000000000000000000000000000000","repo":"test-repo","requirement_digest":"1111111111111111111111111111111111111111111111111111111111111111","run_id":"run-abc123ff","schema_version":2,"seq":0,"timestamp":"2026-10-13T15:04:03Z","workflow_digest":"0000000000000000000000000000000000000000000000000000000000000000"}\n' : Ledger file leaked raw secret: {"Authorization":"Bearer s3cr3t","actor":"executor","head":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","kind":"run","parent":"","prev_hash":"0000000000000000000000000000000000000000000000000000000000000000","repo":"test-repo","requirement_digest":"1111111111111111111111111111111111111111111111111111111111111111","run_id":"run-abc123ff","schema_version":2,"seq":0,"timestamp":"2026-10-13T15:04:03Z","workflow_digest":"0000000000000000000000000000000000000000000000000000000000000000"}

    tests/test_redaction_key_casefold.py:127: AssertionError
    __ RedactionKeyCasefoldTests.test_mixed_case_key_with_list_value_masked_whole __

    self = <tests.test_redaction_key_casefold.RedactionKeyCasefoldTests testMethod=test_mixed_case_key_with_list_value_masked_whole>

        def test_mixed_case_key_with_list_value_masked_whole(self) -> None:
            """A list value under a mixed-case sensitive key ({'Token': ['a', 'b']}) is masked whole."""
            policy = security_hardening.default_redaction_policy()
            payload = {"Token": ["a", "b"]}
            redacted, was_redacted = policy.redact(payload)
    >       self.assertTrue(was_redacted)
    E       AssertionError: False is not true

    tests/test_redaction_key_casefold.py:66: AssertionError
    _ RedactionKeyCasefoldTests.test_uppercase_configured_key_masks_lowercase_payload_key _

    self = <tests.test_redaction_key_casefold.RedactionKeyCasefoldTests testMethod=test_uppercase_configured_key_masks_lowercase_payload_key>

        def test_uppercase_configured_key_masks_lowercase_payload_key(self) -> None:
            """A policy constructed with uppercase configured key masks lowercase payload key."""
            policy = RedactionPolicy(sensitive_keys=["X-Api-Key"])
            payload = {"x-api-key": "xkey123"}
            redacted, was_redacted = policy.redact(payload)
    >       self.assertTrue(was_redacted)
    E       AssertionError: False is not true

    tests/test_redaction_key_casefold.py:75: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_redaction_key_casefold.py::RedactionKeyCasefoldTests::test_default_policy_redacts_mixed_case_sensitive_keys
    FAILED tests/test_redaction_key_casefold.py::RedactionKeyCasefoldTests::test_list_nested_mixed_case_sensitive_keys
    FAILED tests/test_redaction_key_casefold.py::RedactionKeyCasefoldTests::test_nested_mixed_case_sensitive_keys
    FAILED tests/test_redaction_key_casefold.py::RedactionKeyCasefoldTests::test_end_to_end_ledger_redacts_mixed_case_authorization
    FAILED tests/test_redaction_key_casefold.py::RedactionKeyCasefoldTests::test_mixed_case_key_with_list_value_masked_whole
    FAILED tests/test_redaction_key_casefold.py::RedactionKeyCasefoldTests::test_uppercase_configured_key_masks_lowercase_payload_key
    ========================= 6 failed, 3 passed in 0.42s ==========================
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted pytest output of the E-05 ledger test FAILING on unmodified `run_ledger_store.py` (assertion showing `s3cr3t` present in the ledger file text), then passing after E-02. Runtime path: `RunLedgerStore.append` -> `append_held` -> `RedactionPolicy.redact` (shipped code), so the observation is reachable.
  - Observed evidence:
    Failing on unmodified code (from V-01 run above):
    ```
    FAILED tests/test_redaction_key_casefold.py::RedactionKeyCasefoldTests::test_end_to_end_ledger_redacts_mixed_case_authorization
    ...
    E AssertionError: 's3cr3t' unexpectedly found in '{"Authorization":"Bearer s3cr3t","actor":"executor","head":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","kind":"run","parent":"","prev_hash":"0000000000000000000000000000000000000000000000000000000000000000","repo":"test-repo","requirement_digest":"1111111111111111111111111111111111111111111111111111111111111111","run_id":"run-abc123ff","schema_version":2,"seq":0,"timestamp":"2026-10-13T15:04:03Z","workflow_digest":"0000000000000000000000000000000000000000000000000000000000000000"}\n' : Ledger file leaked raw secret: {"Authorization":"Bearer s3cr3t","actor":"executor","head":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","kind":"run","parent":"","prev_hash":"0000000000000000000000000000000000000000000000000000000000000000","repo":"test-repo","requirement_digest":"1111111111111111111111111111111111111111111111111111111111111111","run_id":"run-abc123ff","schema_version":2,"seq":0,"timestamp":"2026-10-13T15:04:03Z","workflow_digest":"0000000000000000000000000000000000000000000000000000000000000000"}
    ```
    Passing after E-02:
    ```
    $ python3 -m pytest -o addopts="" tests/test_redaction_key_casefold.py -k test_end_to_end_ledger_redacts_mixed_case_authorization
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collected 9 items / 8 deselected / 1 selected

    tests/test_redaction_key_casefold.py .                                   [100%]

    ======================= 1 passed, 8 deselected in 0.32s ========================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/run_ledger_store.py` pasted showing only the casefold changes in `__init__` and `_redact_value`, plus pasted pytest output showing every test in `tests/test_redaction_key_casefold.py` (E-01 and E-05 cases) passed.
  - Observed evidence:
    Pasted `git diff agent_workflows/run_ledger_store.py`:
    ```diff
    diff --git a/agent_workflows/run_ledger_store.py b/agent_workflows/run_ledger_store.py
    index 99fe23b83..ceb0eaeef 100644
    --- a/agent_workflows/run_ledger_store.py
    +++ b/agent_workflows/run_ledger_store.py
    @@ -241,14 +241,14 @@ class RedactionPolicy:
                 else:
                     compiled_patterns.append(p)
             self.patterns = tuple(compiled_patterns)
    -        self.sensitive_keys = frozenset(sensitive_keys)
    +        self.sensitive_keys = frozenset(k.casefold() for k in sensitive_keys)
             self.mask = mask
             self.custom_hook = custom_hook

         def _redact_value(
             self, val: Any, parent_key: Optional[str] = None
         ) -> Tuple[Any, bool]:
    -        if parent_key in self.sensitive_keys:
    +        if isinstance(parent_key, str) and parent_key.casefold() in self.sensitive_keys:
                 return self.mask, True

             if isinstance(val, str):
    ```
    Pasted pytest output:
    ```
    $ python3 -m pytest -o addopts="" tests/test_redaction_key_casefold.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=1112896620
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 9 items

    tests/test_redaction_key_casefold.py .........                           [100%]

    ============================== 9 passed in 0.42s ===============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted pytest summary lines for the named suites and the `RunLedgerStore` modules (with the `grep -ln` listing that found them), all passing; and the bare `python3 -m pytest` summary lines from the baseline and after E-02, with any failing test names listed side by side showing none is new.
  - Observed evidence:
    RunLedgerStore modules:
    ```
    $ grep -ln "RunLedgerStore" tests/*.py
    tests/test_capture_command_contract.py
    tests/test_run_cli_corruption_exit.py
    tests/test_run_cli_declarations.py
    tests/test_run_recovery_cli.py
    tests/test_runs_subdir_root.py
    ```
    Named suites + RunLedgerStore modules summary:
    ```
    $ python3 -m pytest -o addopts="" tests/test_security_hardening.py tests/test_host_runner_redaction.py tests/test_host_capability_registry.py tests/test_capture_command_contract.py tests/test_run_cli_corruption_exit.py tests/test_run_cli_declarations.py tests/test_run_recovery_cli.py tests/test_runs_subdir_root.py
    ============================= 127 passed in 26.67s =============================
    ```
    Bare `python3 -m pytest` baseline:
    ```
    8073 passed, 4 skipped, 18 xfailed, 3 warnings in 1131.20s (0:18:51)
    ```
    Bare `python3 -m pytest` after E-02:
    ```
    8082 passed, 4 skipped, 18 xfailed, 3 warnings in 472.24s (0:07:52)
    ```
    Failing tests comparison:
    Baseline: none (0 failed)
    After E-02: none (0 failed)
    Delta: 0 new failures; +9 new tests passed.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `git diff CHANGELOG.md docs/evidence.md` showing the case-insensitive sentence in each, and pasted `aw sanitize --agent` result record with no fail.
  - Observed evidence:
    Pasted `git diff CHANGELOG.md docs/evidence.md`:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 6fdfecceb..c35474681 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ The direction of the 2.x line (in progress, not all shipped in this entry):

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Fixed: `RedactionPolicy` sensitive-key matching is now case-insensitive (security fix, backlog go20fk).
     - Added: research document companion directory convention (`<doc-stem>.data/`) for non-Markdown companion files. `aw research index` lists companions in `INDEX.json` and flags orphaned companions via `check.research-companion-orphaned`, `aw research mv` and `set-assign` rename companion directories with collision refusal, `aw research promote` and `aw archive` carry companion directories to shards, all research walks skip companion contents, and `aw attention` excludes companion files from artifact status checks.
     - Fixed: the workflow history block bounding rule is now shared, so aw backlog set no longer suppresses a same-status record against an indented line it cannot preserve, and closing a decision item no longer duplicates wrapped history records.
     - Fixed: the color_depth pin now also governs general command styling (outcome words, paths, badges, severity labels), so none removes all color from those surfaces and 16 uses basic ANSI colors, and a terminal detected as 16-color (for example TERM=vt100 or TERM=linux) now gets basic ANSI colors there too instead of 256-color codes.
    diff --git a/docs/evidence.md b/docs/evidence.md
    index 28df8f2bb..d803d2948 100644
    --- a/docs/evidence.md
    +++ b/docs/evidence.md
    @@ -20,7 +20,7 @@ keys never land verbatim.

     ## Redaction

    -`RedactionPolicy` masks sensitive keys and patterns BEFORE a record is appended. If a required
    +`RedactionPolicy` masks sensitive keys and patterns BEFORE a record is appended. Sensitive keys are matched case-insensitively. If a required
     verification payload is redacted such that the check cannot be conclusively made, validation
     fails closed (`EV-REDACTION-CONFLICT`) rather than passing on masked data. See
     [security.md](security.md) for the evidence-redaction boundary.
    ```
    Pasted `aw sanitize --agent` result record:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":4939,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Open questions: OQ-01 resolved; none open. Begin with `aw ipd begin pbl020`. Scope fence: `- Scope-Paths:` is a declaration; an edit outside it is made and justified with `--scope-reason` at finalize, not a reason to stop. You MUST paste the actual runner output for every test claim; never claim a result you did not run. Commit only the paths you changed through `aw commit pbl020 -- <paths>`; never `git add -A`, never push. Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize and the executor MUST NOT run it; only in a manual run, after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize pbl020 ... --apply`; never a hand `git mv` or a hand `- Status: executed` edit.
