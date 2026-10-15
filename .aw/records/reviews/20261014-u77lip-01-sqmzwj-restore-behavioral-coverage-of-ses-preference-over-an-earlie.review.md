# Review findings: plan sqmzwj

- Subject-Id: sqmzwj
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review lane. The plan was already committed and unchanged at `8ab1fa6ca`, so no pre-review snapshot was needed. `aw ipd lint --phase author` reported conforming. `--phase pre-transition` reported `check.ipd-uncarried-obligation` on all three Deferred rows (PR-001).

Claims I verified at HEAD:
- `runner_shared._SESSION_ID_KEYS` holds all four keys, `conversation_id` among them.
- `_SESSION_ID_NESTS = ("result", "init")`.
- The body returns the first `ses_` value it finds, and otherwise the first unprefixed `fallback`.
- The docstring and the `agy_runipd` comment block both carry "no live guard currently asserts this conflict case".
- `tests/test_runner_shared.py` defines `BOTH` and `_MODULES`.
- The surviving oc test uses only `sessionID` keys (F-3 is accurate).
- `a.extract_session_id is r.extract_session_id` and `o.extract_session_id is r.extract_session_id` both print `True True`.
- Commit `19313eed7` exists, and `yuhl6o` and `9rthek` are in `executed/`.

Prototype run under the gitignored `.aw/state/` (removed afterwards):
- Cases (a), (b) and (c) passed on all three modules (`1 passed`).
- I patched a first-hit replacement over `runner_shared.extract_session_id` ONLY and re-ran. The test still failed on the `runner_shared` subtest with `'conv-EARLY' != 'ses_LATER'`. Each host module holds its own name binding, so a patch on `runner_shared` reaches only that subtest; hence E-02 must patch all three bindings.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Lifecycle gate | `aw ipd lint --phase pre-transition`: `check.ipd-uncarried-obligation: 3 obligation(s) name no durable carrier: deferred row 1, deferred row 2, deferred row 3` | The plan could not pass its own pre-transition gate, so it could not finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a reasoned `Carrier-Declined` to each Deferred row. Re-running lint shows the rule cleared. |
| PR-002 | MEDIUM | IN-SCOPE | E. Verification feasibility | E-02 said to "temporarily revert `runner_shared.extract_session_id` locally ... then restore", while E-03 edits the same file's docstring and V-02 hedged "if E-03 is already applied" | A source sabotage of a file that E-03 also edits risks the restore wiping E-03's edits, or a sabotaged body getting committed. Stash is forbidden. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now runs the sabotage in-process from a throwaway `.aw/state/` script and never touches source. V-02 demands the script and a `git status` check. |
| PR-003 | MEDIUM | IN-SCOPE | E. Non-vacuity across hosts | Each host module binds `extract_session_id` by name (`is` identity `True True`). Patching `runner_shared` alone does not reach `oc_runipd.extract_session_id` or `agy_runipd.extract_session_id`. | With the original wording, the host subtests would show no failure under sabotage, so non-vacuity was proven only for the `runner_shared` call path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now patches all three bindings and states why. It also requires case (c) to still pass under sabotage. |
| PR-004 | LOW | IN-SCOPE | G. Evidence / contract | V-01's `grep -nE "inspect\|ast\\."` over the new class (the file already imports `ast` and `inspect` and is allowlisted in `tests/test_no_code_structure_pins.py`); gate lacked scope fence, honesty rule, finalize ownership and never-tag; plan file missing from Scope-Paths | An ad hoc grep is weaker than the repo's own guard. The execution contract was incomplete. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now demands a passing `tests/test_no_code_structure_pins.py` and the pasted class body. Added the full gate contract and the plan path to Scope-Paths. |

`aw ipd lint --phase review-finalize` now returns `advisory`, a single `info` finding `IPD-Z602`. This density heuristic fires on E-02's longer text. The finding is accepted: E-02 remains one concern (a non-vacuity demonstration, done in-process) with one V-item, and the advisory does not affect disposition.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the sabotage be run? | In-process `mock.patch.object(...).start()` on all three module bindings, run from a `.aw/state/` script | Source edit plus `git checkout` (collides with E-03); patching `runner_shared` only (does not reach the hosts) | Review prototype output above | yes |
| D-2 | Should the IPD-Z602 advisory be accepted? | Yes | Splitting E-02, which would separate the sabotage from its own evidence | `ipd_lint.check_density` docstring: "Does NOT affect the conformance disposition" | yes |
