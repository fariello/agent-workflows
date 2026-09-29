# Review findings: plan 6mdtnu

- Subject-Id: 6mdtnu
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `c753ce61` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and after revision `--phase
review-finalize` conforms with ZERO advisories and zero diagnostics. No pre-review snapshot was owed:
the plan was committed and unmodified. No production or test file was modified by this review; every
measurement ran read-only or against `tempfile` trees, from probe scripts under the gitignored
`.aw/state/`, with the two pattern widenings applied IN MEMORY exactly as the plan's own validation
section instructs, and `git status --porcelain` empty throughout.

THIS PLAN IS UNUSUALLY WELL MEASURED AND ITS DIAGNOSIS IS CORRECT IN BOTH HALVES. Every load-bearing
claim reproduced. F-1: `len({new_run_id(), new_run_id(), new_run_id()})` is `1`. F-2's correction of
the backlog item is right and matters: `initialize_run_core` does carry
`if run_dir.exists(): raise DriverError(f"Run already exists: {run_id}")`, it is the only copy of
that string in the package, so the item's "silently overwrites" claim is indeed false for the queued
path. F-4's four-way grammar matrix reproduced cell for cell: `work_cmd` accepts the `-N` suffix
(with a comment naming it), both analytics patterns refuse it, and `run_ledger_schema` refuses both
driver shapes. F-5 reproduced end to end, including the verbatim detail text
`privacy refusal: key 'run_id' must be a driver run id or a pseudonym`, with the plain id deciding
`rebuild` and the suffixed one `skip` / `build-refused`. F-6 reproduced precisely: 7 of 7 correlation
fields kept for a plain id, 6 of 7 for a suffixed one with `run_id` the dropped field. F-7's
accept/refuse matrix for the three candidate remedies reproduced, so the choice of the mkdir loop
rests on measurement rather than preference. F-9 is accurate: the only spec mentioning the grammar is
the `draft` `i4gpto`, whose R-7 names the very mechanism being lifted. F-10's two timestamp parsers
behave identically for both shapes.

REVIEW ALSO PRE-VALIDATED THE DESIGN. The proposed widening was applied in memory to both patterns
and driven through the PUBLIC entry points over eight shapes: plain, `-2` and `-99` accepted;
`-good`, the shipped-assertion case `run-20260908T100000Z-good`, a microsecond stamp, a path-ish tail
`-1234-/etc`, and a triple suffix `-1234-2-3` all refused; all eight matched the plan's prediction at
BOTH boundaries, and `telemetry_safe_context` then kept 7 of 7 fields. So E-04/E-05 are known-good
before execution, and the privacy-boundary argument in E-04 holds: the added group admits only digits
and cannot express a path, a username or a session id (recorded as new F-15).

WHAT REVIEW FOUND IS ONE REAL CONTRADICTION BETWEEN TWO ITEMS, PLUS FOUR SMALLER ACCURACY GAPS.

**E-01 AND E-02 CONTRADICT EACH OTHER ABOUT A USER-VISIBLE ERROR (PR-901, HIGH).** E-01 instructs
the executor to "let the `FileExistsError` from `mkdir(exist_ok=False)` surface as the existing
refusal", while E-02 instructs "PRESERVE THAT REFUSAL MESSAGE VERBATIM ... an operator may be
matching on it". Those cannot both be satisfied, and the literal reading of E-01 is wrong on three
counts, each measured. The text becomes
`FileExistsError: [Errno 17] File exists: '/tmp/.../run-20260929T013453Z-1234'` where the shipped
refusal is `DriverError: Run already exists: run-20260929T013453Z-1234`. It LEAKS AN ABSOLUTE PATH
into a user-facing error, which is the class of string the leak-sanitizer exists to keep out of
shared output. And `DriverError` is the deliberately-shaped catchable class both hosts handle, with
`agy_runipd`'s own comments recording that a non-`DriverError` raised in this region "could NOT be
caught by `except DriverError`", so the bare OS error escapes the handler meant to render it.
Measured: the translating form reproduces the shipped string byte-for-byte
(`matches the shipped user-visible string: True`), the propagating form does not. FIXED: E-01 now
states the translation explicitly with all three reasons, E-02 cross-references it, V-01 requires the
class, the exact message and the ABSENCE of a path, and the decision is recorded as OQ-03 because it
settles a user-visible contract.

**"BEHAVES IDENTICALLY" OVERSTATES THE PREDICATE SWAP (PR-902, MEDIUM).** E-02 claims the repoint
"behaves identically for the common case and for an explicit duplicate". Measured over four path
shapes, `exists()` and `mkdir(exist_ok=False)` agree for an existing directory, an existing plain
file, and a free path, but DISAGREE for a dangling symlink: `exists()` follows the link and returns
`False` (so the shipped code proceeds and fails later, deeper in the run) while `mkdir` raises
`FileExistsError` (so the new code refuses cleanly up front). That is an improvement, not a
regression, but it is a behavior change and an unqualified identity claim would have hidden it.
Related and also unstated: the shipped code never creates `run_dir` itself, only its three members
with `exist_ok=True`, so the run directory currently comes into being as a side effect; after the
change it is created explicitly, which is precisely the atomicity being bought. FIXED: recorded as
new F-12, stated in E-01 and E-02, and V-02 must now paste the symlink case.

**A SECOND CONVENTION CITATION IS STALE, FROM THE SAME DELETION AS F-3's (PR-903, LOW).** The Step-0
bullet cites `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
as the guard on `runner_shared`'s import graph. That file was deleted by `19313eed`, the same trim
commit F-3 already names for `tests/test_standalone_verify.py`, and no test in the tree matches the
name. The PROPERTY still holds (the module's module-level first-party imports are exactly
`runner_profiles` and `render_stream`), so E-01's "add no import" instruction stands, but it is now
unenforced. FIXED: the bullet records the measurement, the deletion, and that the suite will not
catch a violation; new F-13.

**THE BASELINE HAS DRIFTED AND ONE QUOTED `reason` IS PATH-DEPENDENT (PR-904, LOW).** The plan
records `3189 passed, 2 skipped`; review measured `3246 passed, 2 skipped, 3 warnings in 48.89s` one
day later. The plan already tells the executor to re-derive rather than trust that digit, which is
the right instruction, and this drift vindicates it. Separately, F-5 quotes the passing decision as
`rebuild / no-entry`, but `no-entry` arises only for a TERMINAL run; a non-terminal one yields
`rebuild / run-not-terminal`. Both are `rebuild`, and E-07 already says to assert on the decision
rather than the message, so the plan's test design is unaffected. FIXED: new F-14, and V-07 now says
explicitly to pin `verdict` and not `reason`. Neighbour set measured green at review (`194 passed`).

**THE GATE LACKED THE CONDITIONAL FINALIZE OWNERSHIP (PR-905, LOW).** The gate said to "move this
plan to `.aw/records/plans/executed/` via the tooled transition" without naming `aw ipd finalize`,
without the runner-versus-hand ownership split, and without forbidding a hand-rolled `git mv`. It
also carried no before-implementing re-reproduction instruction, which matters here because the plan
itself records that the backlog item's evidence had already gone stale once (F-3). FIXED: the gate now
carries the unconditional finalize obligation with conditional runner/executor ownership, the
`git mv` prohibition, and a re-run-F-1/F-5/F-6-first stop condition with the review's own
reproductions recorded as the baseline.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. OQ-01 and OQ-02 both survive review and are upheld; OQ-01's refusal of a format change is
independently confirmed by the F-7 matrix reproducing, and OQ-02's refusal to unify the patterns is
confirmed by `run_analytics_privacy` importing only stdlib and `work_cmd`'s comment recording the
duplication as deliberate. New OQ-03 records the refusal-translation decision. The five
Carrier-Declined rows were each checked and are honest; the `run_viewer` substring-matching row is
correctly characterized as pre-existing and arguably correct rather than as a defect.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | high | IN-SCOPE | A. Correctness / B. Privacy (path leak) / F. UX | E-01 "let the `FileExistsError` ... surface" vs E-02 "PRESERVE THAT REFUSAL MESSAGE VERBATIM"; measured propagating form `FileExistsError: [Errno 17] File exists: '/tmp/.../run-...'` vs translating form `DriverError: Run already exists: run-...` (`matches the shipped user-visible string: True`); `agy_runipd` comments on `except DriverError` not catching a foreign class | The two items give contradictory instructions for the explicit-duplicate refusal. E-01's literal reading changes the user-visible error string, leaks an absolute path into it, and raises a class the hosts' `except DriverError` handler does not catch. | C:Low; U:Medium; S:Medium; F:Medium; Overall:Medium | fixed | E-01 now requires translating to `DriverError(f"Run already exists: {run_id}")` inside `mint_run_dir`, with all three reasons; E-02 cross-references it; V-01 requires class, exact message and no path; recorded as OQ-03; new F-11. |
| PR-902 | medium | IN-SCOPE | A. Correctness and data integrity | four-path predicate comparison: dir/file/free agree, DANGLING SYMLINK disagrees (`exists()=False`, `mkdir` raises `FileExistsError`); shipped code mkdirs only the three members with `exist_ok=True` | E-02's "behaves identically" is not exact: the `exists()` -> `mkdir(exist_ok=False)` swap newly refuses a dangling symlink (an improvement, previously failing later in the run), and the run directory's creation moves from an implicit side effect to an explicit atomic act. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | New F-12; E-01 and E-02 state the one predicate change and the creation-point change; V-02 must paste the symlink case as an intentional improvement rather than claiming identity. |
| PR-903 | low | IN-SCOPE | Evidence accuracy | `ls tests/test_orchestrator_probe_cache.py` -> No such file; `git log --diff-filter=D --oneline -1` -> `19313eed` (the same commit F-3 names); `grep -rln "no_new_module_level_first_party_import" tests/` -> no matches; measured module-level first-party imports = `runner_profiles`, `render_stream` | A second convention citation names a test deleted by the same trim commit as F-3's, so the plan cites a guard that no longer runs; the underlying property still holds. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | The Step-0 bullet now records the measurement, the deletion, and that no test will catch a violation; new F-13. |
| PR-904 | low | IN-SCOPE | Evidence accuracy | bare suite `3246 passed, 2 skipped, 3 warnings in 48.89s` vs the plan's `3189 passed, 2 skipped`; `run_analytics_cache` returning `run-not-terminal` for a live run and `no-entry` for a terminal one; neighbour set `194 passed` | The recorded baseline has drifted, and F-5's quoted `no-entry` reason is path-dependent on whether the fixture's run is terminal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | New F-14; the Required-tests note records both figures and reiterates re-derivation; V-07 now says to assert `verdict` and not `reason`, and records the measured neighbour baseline. |
| PR-905 | low | UNDER-SCOPE | G. Plan executability (execution contract) | the gate's "move this plan to `.aw/records/plans/executed/` via the tooled transition" with no `aw ipd finalize`, no runner/hand ownership split, no `git mv` prohibition, and no before-implementing re-reproduction | The gate's execution contract was incomplete on the lifecycle transition, and carried no stop condition for a defect that has moved, which this plan's own F-3 shows can happen. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | The gate now carries the unconditional finalize obligation with conditional runner/executor ownership, the `git mv` prohibition, a re-run-F-1/F-5/F-6 stop condition with review's reproductions as the baseline, and a pointer to F-11. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-01 and E-02 disagree about the explicit-duplicate refusal. Translate to `DriverError` inside `mint_run_dir`, or let `FileExistsError` propagate as E-01 literally says? | Translate inside `mint_run_dir`, preserving the shipped `Run already exists: <id>` message exactly. | (a) Let it propagate (E-01's literal reading): rejected on three measurements, since it changes the user-visible string E-02 requires preserved, leaks an absolute path, and escapes the hosts' `except DriverError`. (b) Introduce a new `RunDirTaken(DriverError)` subclass: rejected as scope this bug does not need; the requirement is to preserve today's message, not to refine the taxonomy. (c) Raise it as a blocking question: rejected because the repository answers it decisively (the shipped message, the sanitizer convention, and the hosts' documented handler shape). | Measured propagating vs translating output; the single shipped copy of `Run already exists`; `agy_runipd`'s comments that a non-`DriverError` here is not caught by `except DriverError`. | yes |
| D-2 | The predicate swap changes behavior for a dangling symlink. Preserve `exists()` semantics exactly, or accept the change? | Accept it and record it as an intentional improvement that V-02 must evidence. | (a) Keep an explicit `exists()` pre-check to preserve the old semantics: rejected because it reintroduces the check-then-create race that `mkdir(exist_ok=False)` exists to remove, which is the plan's whole mechanism. (b) Leave it undocumented: rejected because an unstated behavior change is exactly what a reviewer should not let pass, even a beneficial one. | The four-path predicate comparison showing dir/file/free agreement and the single symlink divergence; `_fresh_audit_run_dir`'s own docstring arguing that mkdir is "atomic against a concurrent audit rather than a check-then-create race". | yes |
| D-3 | F-5 quotes `no-entry` but a live run yields `run-not-terminal`. Correct the finding, or the test instruction? | Record the distinction and sharpen V-07 to assert on `verdict`, leaving F-5's conclusion intact. | (a) Rewrite F-5's fixture description to guarantee terminality: unnecessary, since both reasons carry `verdict == "rebuild"`, which is what the fix is about. (b) Ignore it: rejected because an executor pinning `reason == "no-entry"` would write a test that depends on fixture construction rather than on the behavior under test. | Measured `rebuild / run-not-terminal` for a non-terminal fixture and the `no-entry` branch in `run_analytics_cache` for a terminal one; E-07's existing "assert on the DECISION, not the message" instruction. | yes |
