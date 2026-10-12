# IPD: Case-fold RedactionPolicy sensitive-key matching

- Date: 2026-10-12
- Kind: child
- Concern: `RedactionPolicy` sensitive-key matching is case-sensitive, so a secret under `TOKEN` or `Authorization` reaches the run ledger unmasked.
- Scope: Fold key case on both sides of the sensitive-key comparison in `run_ledger_store.RedactionPolicy`, add outcome tests for mixed-case keys, and record the behavior change in CHANGELOG and docs/evidence.md.
- Scope-Paths: agent_workflows/run_ledger_store.py, tests/test_redaction_key_casefold.py, CHANGELOG.md, docs/evidence.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: security
- Priority: medium
- From-Backlog: go20fk
- Set: go20fk
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: pbl020

## Workflow history

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog go20fk; review-ready.

## Goal

Make `RedactionPolicy` match sensitive keys case-insensitively, so that every spelling of a configured secret-bearing key (`token`, `TOKEN`, `Token`, `Authorization`) is masked before a record lands in the run ledger or in redacted worker output. Folding is chosen over widening the key list because it cannot be forgotten when a new spelling appears (backlog go20fk open question).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Reproduce, then fix

- [ ] E-01 Add `tests/test_redaction_key_casefold.py` with outcome tests that call `RedactionPolicy.redact` (and `security_hardening.default_redaction_policy().redact`) on payloads keyed `TOKEN`, `Authorization`, `Api_Key`, nested `{'outer': {'PASSWORD': ...}}`, and list `{'items': [{'Secret': ...}]}`, asserting the secret value is replaced by the mask, `was_redacted` is True, the ORIGINAL key spelling is preserved in the output, a non-sensitive key (`stdout`) is untouched, and a policy constructed with an uppercase configured key (`sensitive_keys=['X-Api-Key']`) masks a lowercase payload key `x-api-key`. Run it against unmodified code and record the failures.
  - Depends on: none
  - Expected outcome: new test file exists; the mixed-case cases fail on unmodified code (reproducing the defect) while the lowercase control passes.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/run_ledger_store.py`, change `RedactionPolicy.__init__` to store `self.sensitive_keys = frozenset(k.casefold() for k in sensitive_keys)` and change `RedactionPolicy._redact_value` so the check reads `isinstance(parent_key, str) and parent_key.casefold() in self.sensitive_keys`. Do not rename payload keys and do not alter pattern, list, dict, or custom-hook handling.
  - Depends on: E-01
  - Expected outcome: the E-01 tests pass; output dicts keep their original key spellings; non-string keys (e.g. int) no longer risk an AttributeError path and are simply not matched.
  - Execution state: pending

### Task group 2: Regression and documentation

- [ ] E-03 Run the existing redaction-adjacent suites (`tests/test_security_hardening.py`, `tests/test_host_runner_redaction.py`, `tests/test_host_capability_registry.py`) and then the full fast suite bare (`python3 -m pytest`).
  - Depends on: E-02
  - Expected outcome: all pass with no new failures attributable to this change.
  - Execution state: pending

- [ ] E-04 Document the behavior: add a CHANGELOG.md entry under the top `## 2.0.0 (pending)` section stating sensitive-key matching is now case-insensitive (security fix, backlog go20fk), and amend the `## Redaction` paragraph of `docs/evidence.md` to say sensitive keys are matched case-insensitively. No em or en dashes in this user-facing prose.
  - Depends on: E-02
  - Expected outcome: both files carry the new sentence; `aw sanitize --agent` reports no new leak finding.
  - Execution state: pending

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
| F-5 | Existing test `test_security_hardening` uses lowercase `authorization`, which continues to match after folding. | `tests/test_security_hardening.py` PAYLOADS row "a bearer token under a SENSITIVE KEY" |

## Proposed changes (ordered, validatable)

1. Add failing outcome tests (E-01, V-01).
2. Case-fold the configured set and the compared key in `RedactionPolicy` (E-02, V-02).
3. Regression run (E-03, V-03).
4. CHANGELOG and docs/evidence.md note (E-04, V-04).

## Deferred / out of scope (with reason)

- Widening the default key list (e.g. adding `x-api-key`, `access_token`): a separate policy decision; folding addresses the reported defect. Not in backlog go20fk's ask.
- Normalizing separators (`api-key` vs `api_key`): different defect class, not reported; would change matching semantics beyond case.
- Free-text credential detection: tracked separately (backlog lfko0e per docs/security.md).
- Rewriting payload keys to lowercase: rejected; it would alter non-secret record structure for every ledger caller.

## Scope check

- Over-scope: none.
- Under-scope: none; all ledger and worker-output callers share `RedactionPolicy` (F-4, conventions), so one change covers them.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_redaction_key_casefold.py` fails before E-02 and passes after (V-01, V-02).
- `python3 -m pytest -o addopts="" tests/test_security_hardening.py tests/test_host_runner_redaction.py tests/test_host_capability_registry.py` passes (V-03).
- Bare `python3 -m pytest` passes (V-03).
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

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output of `tests/test_redaction_key_casefold.py` run on unmodified `run_ledger_store.py` showing the mixed-case cases FAILED and the lowercase control passed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/run_ledger_store.py` pasted showing only the casefold changes in `__init__` and `_redact_value`, plus pasted pytest output showing every test in `tests/test_redaction_key_casefold.py` passed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `N passed` summary lines for the three named suites and for the bare `python3 -m pytest` run, with zero failures.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff CHANGELOG.md docs/evidence.md` showing the case-insensitive sentence in each, and pasted `aw sanitize --agent` result record with no fail.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit <this plan> -- <Scope-Paths>`; never push. After every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, transition the plan to `.aw/records/plans/executed/` with the tooled lifecycle (`aw ipd finalize`/`aw ipd set executed`), never by hand.
