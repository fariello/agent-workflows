# Review: Make aw doctor report how many files the leak sanitizer actually scanned

- Subject-Id: 3xdgg0
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Every material claim was re-measured at review HEAD `8b64b198` (the plan was authored at `61ef21d8`,
an ancestor; both were checked and the diagnosis agrees). The target plan was committed and unchanged,
so the pre-review snapshot was correctly skipped per Step 1. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE review, and
`--phase review-finalize` reported `conforming` again after the edits, including the added E-04/V-04
pair. `aw check plans --agent` reports 1 finding for the whole tree and NONE against this plan, and
`check_engine.evaluate_durable_carrier` on it returns `[]`.

THE DIAGNOSIS IS CORRECT AND THE FIX IS THE RIGHT SHAPE. I verified F-1 rather than reading it:
`scanned_files` exists at exactly three sites (the dataclass default, `to_dict`, the Evidence emitter)
and is assigned nowhere, in no module and no test. `aw doctor --json` on this repo returns
`evidence[sanitizer] == {"scanned_files": 0, "findings": 0}` with 2880 tracked files, so the field is
demonstrably a constant. The chosen mechanism is also the right one: a counted variant with the old
name delegating in one line keeps ONE implementation and leaves all three other callers
(`leak_sanitizer.run`, `security_hardening.scan_artifact_for_leaks`, the `local_leaks` re-export)
untouched, which is the KISS answer here. Plan structure, right-sizing (three then four one-concern
items), the E/V bijection, and the outcomes-only posture are all sound.

THE DOMINANT FINDING IS PR-901, AND IT CHANGES WHAT THIS PLAN CAN HONESTLY CLAIM RATHER THAN WHAT IT
SHOULD DO. The plan's Concern, E-02's expected outcome, and V-02's required evidence all named
`aw doctor --agent` as the surface that would start reporting a true count. IT CANNOT. The compact
`aw.agent/v1` record passes each `Evidence` through `agent_schema.sanitize_evidence_item`, which
returns the KEY ALONE for a dict-valued item (a scalar or safe string is inlined; a dict is not), and
the verbose branch that would emit the full object is selected by `OutputContext.verbose`, which
`select_output` reads off an `args.verbose` that `aw doctor` does not declare
(`aw doctor --verbose` -> `error: unrecognized arguments: --verbose`; the only `--verbose` in `cli.py`
belongs to `aw upgrade-test`). I confirmed this is a property of the SHAPE and not of the zero value
by driving both branches with a nonzero count: compact renders `["sanitizer"]`, verbose renders
`{"key": "sanitizer", "value": {"scanned_files": 2876, ...}}`. So V-02 as authored demanded evidence
the executor could never produce, and would have sent them hunting a nonexistent bug in their own
change. The reachable surfaces are `--json` and `data.report.sanitizer`. V-02 now demands the `--json`
object AND an `--agent` paste with a one-line statement that the absence there is F-3 and deliberate,
which is the pairing that stops a future reader re-opening this as a defect.

THE SECOND MATERIAL FINDING IS PR-902, AND IT IS THE ONE THAT MAKES THE FIELD MEAN ANYTHING. The plan
asserted only that a nonzero count appears. It did NOT pin that `0` still means "did not scan", which
is precisely the distinction its own Goal sells. Left as authored, a later refactor could set a partial
count on the failure path and no test would object, and the field would become actively misleading
rather than merely useless: a consumer would read coverage of N files from a probe that aborted after
N. I added E-04/V-04 (two assertions in the method E-03 already adds, no second fixture) pinning the
failure pair, and I was careful to record against myself that this assertion PASSES pre-change too,
measured on a non-git temp dir: `drift=[('doctor.probe-failed', "Command '['git', '-C', ...")]` with
`scanned_files: 0`. It is a characterization pin on an invariant, not evidence of the fix, and V-04
requires the executor to say so rather than counting it as proof.

THE THIRD FINDING IS THE KIND THAT COSTS AN EXECUTOR AN HOUR FOR NOTHING. E-01 told the executor not to
count "a path whose read and fallback both fail (`continue`)". That branch is NEARLY UNREACHABLE, and
believing otherwise invites the wrong increment placement. The fallback runs
`subprocess.run(..., check=False)`, so a git failure does not raise and never reaches the `continue`:
it returns nonzero with empty stdout and `scan_text` IS called with `""`. Measured with a binary file
staged but never committed: `git show HEAD:bin.dat` exits 128 with 0 bytes, no exception, findings
`[]`. E-01 now says to place the increment immediately before the `scan_text` call, which makes the
docstring true by construction, and it states the honest consequence (an unreadable file whose blob
fetch yields empty IS counted, because it was scanned, of empty text).

TWO SMALLER CORRECTIONS OF FACT, BOTH IN THE PLAN'S FAVOUR ONCE FIXED. E-03 justified a fresh fixture
because `DoctorTests.setUp` "tracks many files"; re-running that fixture's exact body shows it tracks
THREE (`.aw/system/VERSION`, `layout.json`, `layout.schema.json`). The instruction is still right for a
better reason, which E-03 now gives: `engine.emit_layout_artifacts` owns that count, so an exact-count
assertion against the shared fixture would break when the installer emits one more file. Separately the
plan called rpqv4q `approved`; it is `executed`, so the dependency is already satisfied and the gate's
stop condition is not expected to fire, which I verified in the code as well as the front matter
(`probe_sanitizer` already reads `f.snippet` with only the scan inside the `try`).

I ALSO STRENGTHENED THE ARGUMENT FOR DOING THIS AT ALL, because a `low`-priority cosmetic field
deserves a stated reason and the plan did not have one. The two states the count separates are real and
currently conflated in the value itself: a probe that raised reports `findings: 0, scanned_files: 0`,
and a clean repo reports `findings: 0, scanned_files: 0`. The `doctor.probe-failed` drift distinguishes
them TODAY, so I recorded the count as a second, positive signal rather than the only one; the Goal
would otherwise overstate the gap. The precedent is in the repository: `leak_sanitizer`'s own `--agent`
contract treats exactly this distinction as load-bearing, in the words of the test that pins it, so a
consuming agent can tell "scanned, nothing found" from "did not scan".

WHAT I DID NOT CHANGE. The mechanism (counted variant plus one-line delegation), OQ-01's resolution
(count files READ, which I confirmed is a live distinction on this tree: 2880 tracked versus 2876 read,
because four of the five `_ALLOWED_PATHS` entries are tracked here), the decision to leave `scan_staged`
and `scan_history` uncounted, the `low` priority, and the outcomes-only test posture. I did NOT add a
`local_leaks` re-export of the new name (D-2) and I did NOT widen the compact-record contract to expose
the count (PR-901's fix, deliberately declined with the reason recorded).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | MEDIUM | IN-SCOPE (claim); OUT (contract fix) | A. Correctness / E. Testing (evidence that cannot be produced) | `agent_workflows/agent_schema.py`, `sanitize_evidence_item` (a dict `value` returns `key` alone); `result_types.CommandResult.to_agent_record` (`is_verbose = context.verbose if context is not None else False`); `select_output` reading `getattr(args, "verbose", False)`; `aw doctor --verbose` -> `error: unrecognized arguments: --verbose`. Driven with a NONZERO 2876: compact `["sanitizer"]`, verbose the full dict. On this repo `aw doctor --agent` first record is `"evidence":["git","env","attention","sanitizer","artifacts"]` and `'scanned_files' in json.dumps(record)` is `False`, while `--json` gives `{"scanned_files": 0, "findings": 0}` | **THE PLAN NAMED `--agent` AS THE SURFACE IT FIXES, AND THE COUNT CANNOT APPEAR THERE.** The compact record reduces a dict-valued `Evidence` to its key for every verb, and doctor declares no `--verbose` to select the branch that would carry the value. So E-02's expected outcome and V-02's required evidence were both unproducible: an executor following V-02 would paste `--agent` output with no `scanned_files` in it and conclude their own change was broken. `--json` and `data.report.sanitizer` are the reachable surfaces. The contract FIX is out of scope (it is shared by every verb, `docs/cli-output-contract.md` Section 2). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern, Scope, E-02's expected outcome and V-02 all renamed to `--json`; V-02 additionally requires the `--agent` paste plus a one-line statement that the absence is F-3 and deliberate, so a later reader does not re-file it. Added F-3 with both measurements, a Carrier-Declined deferral stating that exposing it is a NEW contract request rather than unfinished work here, and a "WHAT IT DOES NOT DELIVER" paragraph in the approval gate. |
| PR-902 | MEDIUM | UNDER-SCOPE | D. Anti-regression / E. Testing (the invariant the Goal claims was unpinned) | `doctor.probe_sanitizer`'s `except` branch returns `res` before any assignment, so `scanned_files` stays 0; measured on a non-git temp dir at HEAD: `drift=[('doctor.probe-failed', "Command '['git', '-C', ...")]`, `scanned_files: 0`. No test in `tests/test_doctor.py` references `scanned_files` at all | **ONLY THE NONZERO HALF OF THE INVARIANT WAS TESTED.** The plan's Goal is that a reader can tell a clean scan of N files from a scan that read nothing, but nothing pinned that `0` still means "did not scan". A later change setting a partial count on the failure path would pass the whole suite, and the field would then assert coverage a crashed probe never had, which is worse than the constant 0 it replaces. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added E-04 (two assertions inside the method E-03 already adds: `scanned_files == 0` and a `doctor.probe-failed` drift on a non-git path) and V-04. E-02 gained an explicit instruction to leave the failure path at the default 0 and not set a partial count. `Highest E allocated` 03 -> 04. V-04 requires the executor to state that this assertion passes pre-change and is a characterization pin, so it is never mistaken for proof of the fix. |
| PR-903 | LOW | IN-SCOPE | A. Correctness (an instruction resting on a branch that does not behave as described) | `scan_working_tree`'s fallback is `subprocess.run(..., check=False)` inside its own `try`, so a git failure returns nonzero rather than raising; measured with a binary file staged but never committed: `git show HEAD:bin.dat` exits 128, 0 bytes, `scan_text` called with `''`, no `continue`, findings `[]` | **E-01's EXCLUSION NAMES A NEARLY UNREACHABLE BRANCH, WHICH INVITES THE WRONG INCREMENT PLACEMENT.** "A path whose read and fallback both fail (`continue`) is NOT counted" reads as the binary/unreadable case, but that case reaches `scan_text` with empty text. The `continue` is taken only if `subprocess.run` itself raises (missing `git` binary, spawn failure). An executor reasoning from the wrong model could place the counter in the `try` and produce a count that disagrees with its own docstring. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now states the measured behavior, instructs placing the increment immediately before `findings.extend(scan_text(...))` so the docstring is true by construction, and records the honest consequence that an unreadable file whose blob fetch yields empty IS counted. Added F-5. |
| PR-904 | LOW | IN-SCOPE | A. Correctness (a false justification and a stale status) | Re-ran `DoctorTests.setUp`'s exact body: tracked `['.aw/system/VERSION', '.aw/system/layout.json', '.aw/system/layout.schema.json']` (three files). `.aw/records/plans/executed/20260925-doctorleak-01-rpqv4q-...ipd.md` carries `- Status: executed` | **TWO FACTUAL ERRORS IN THE PLAN'S OWN PROSE.** E-03 justified a fresh fixture because `DoctorTests.setUp` "tracks many files" (it tracks three), and the conventions section called rpqv4q `approved` (it is `executed`). Neither changes what to do, but an executor who checks the first claim and finds it false loses confidence in the rest, and the second misrepresents whether the gate's stop condition is live. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now gives the correct and stronger reason (the count is owned by `engine.emit_layout_artifacts` and would drift, so an exact-count assertion must not depend on it) and states the measured three. The conventions bullet and the stop condition both record that rpqv4q is executed and that the dependency is satisfied, verified in the code as well as the front matter. Added F-6. |
| PR-905 | LOW | UNDER-SCOPE | F. UX (the human surface keeps the ambiguity) | `grep -rn "Clean (0 maintainer" --include=*.py .` -> one site in `agent_workflows/doctor.py`, zero test references; the clean branch prints the fixed string `"  Sanitizer:   Clean (0 maintainer/local leak findings)"` | **THE HUMAN READER GAINS NOTHING FROM THIS PLAN.** `render_human_report`'s sanitizer section prints a constant on the clean path, so the exact ambiguity the Goal describes survives for the human audience both before and after. Not fixed: it is a copy change on an unpinned rendered line, outside the declared paths, and unnecessary for the machine-readable fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded rather than absorbed. Added F-4 with the measurement; recorded in Deferred with a Carrier-Declined; named in the gate's not-touched list and in the "WHAT IT DOES NOT DELIVER" paragraph so the approving human sees which audiences benefit. |
| PR-906 | LOW | IN-SCOPE | E. Testing (a validation command that selects nothing) | `python3 -m pytest -o addopts="" tests/test_doctor.py -v -k scanned` -> `collected 27 items / 27 deselected / 0 selected` | **THE PLAN'S OWN VALIDATION COMMAND MATCHES NO TEST.** `-k scanned` depends on a method name the plan never specifies, and a green-looking run that selected zero tests is exactly the shape of false evidence the honesty rule exists to prevent: exit 0 with nothing executed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The validation section now says to use the method name actually added and records the measured 27-deselected result so the trap is documented; V-03 requires naming the `-k` selector used. |
| PR-907 | LOW | IN-SCOPE | G. Plan executability (execution contract) | Gate as authored: a scope fence naming only the Scope-Paths list, an UNCONDITIONAL "perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane)", and a one-line gate handoff assertion with no evidence | **THE GATE WAS THINNER THAN THE CONTRACT REQUIRES IN THREE PLACES.** The fence restated the path list without saying which surfaces inside those files are in scope or which adjacent ones must stay untouched, so finalize reconciliation had little to reconcile against; the finalize instruction did not carry conditional runner/executor ownership or forbid a raw `git mv`; and the `c0ppo0` close asserted the gate is preserved without the predicate that proves it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fence now names the in-scope surface per file, declares `local_leaks.py` expected-unmodified with the reason (D-2), and lists `sanitize_evidence_item`, `to_agent_record`, `render_human_report` and `CHANGELOG.md` as deliberately untouched. Finalize instruction now carries conditional ownership and forbids a raw `git mv`. The handoff cites `check_engine.evaluate_blocking_close` on `c0ppo0` returning `legitimate=True, path='HANDOFF'` (driven at review). The honesty rule now names the two claims easiest to fake. |
| PR-908 | LOW | IN-SCOPE | F. KISS / G (an unstated why, and an unstated not-doing) | `tests/test_leak_sanitizer.py`, the CLEAN ROW of `STATES` in `test_the_agent_envelope_is_identical_in_shape_for_both_tree_states`: "so a consuming agent can tell 'scanned, nothing found' from 'did not scan'". Measured: a raised probe and a clean repo both report `findings: 0, scanned_files: 0`, distinguished today only by the `doctor.probe-failed` drift | **THE PLAN NEVER SAID WHY A `low`-PRIORITY COSMETIC FIELD IS WORTH A CHANGE, AND ITS SPEC-SYNC LINE WAS AN UNEVIDENCED "N/A".** Without the why, a reviewer cannot tell a real gap from polish; and the bare `N/A` did not say WHICH specs were checked, which is the claim a reader would need to trust. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Goal gained a paragraph stating the two conflated states, honestly noting the drift entry already distinguishes them (so the count is a second signal, not the only one), and citing the in-repo precedent that treats this distinction as load-bearing. Spec sync now names the specs checked (`kw5y2s` 6.2, `2lcqno`) and `docs/cli-output-contract.md` Section 2, and states that the Evidence SHAPE is unchanged. A conventions bullet records why no CHANGELOG line is owed, contrasting with sibling `wd6npl` which does declare one. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-901 shows the count cannot reach `--agent`. Widen the compact-record contract here, or restate the plan's claim? | RESTATE THE CLAIM to `--json` and record the `--agent` limitation as a measured finding with a declined carrier. | (a) Widen `sanitize_evidence_item` or add `--verbose` to doctor: rejected, it changes a contract shared by every verb (`docs/cli-output-contract.md` Section 2) inside a `low`-priority three-item bug fix, and the compact reduction is deliberate token control rather than an oversight. (b) Leave the plan saying `--agent`: rejected outright, V-02 would demand evidence that cannot exist and the executor would hunt a bug in their own correct change. (c) File a backlog item as carrier: rejected, it would record a decision the maintainer has not taken; whether the count belongs in `--agent` is a contract question for them, and the finding plus its measurement is now in the plan for whoever asks it. | `sanitize_evidence_item` read in full; `to_agent_record`'s `is_verbose`; `select_output`'s `getattr(args, "verbose", False)`; `aw doctor --verbose` refused; both branches driven with a nonzero value | yes |
| D-2 | Should `local_leaks` re-export `scan_working_tree_counted`, as the Scope line briefly said during revision? | NO. The shim keeps the HISTORICAL surface; the new name is not added. | (a) Add it for symmetry: rejected, the module's own docstring says it exists so historical importers keep working with ONE code path, and `__all__` is a curated historical list, not a mirror. No consumer imports the new name (the only callers of the counted function will be `scan_working_tree` and `doctor.probe_sanitizer`), so adding it would create a second public spelling with no user and a second thing to keep in sync. | `agent_workflows/local_leaks.py` module docstring and `__all__`; the three measured callers of `scan_working_tree`; `tests/test_leak_sanitizer.py::test_e04_local_leaks_reexports_resolver` asserts identity of what IS re-exported, not completeness | yes |
| D-3 | PR-902's failure-pair assertion passes against the pre-change code. Add it anyway, or drop it as vacuous? | ADD IT, and require the executor to state that it passes pre-change. | (a) Drop it: rejected, it is the only thing pinning that `0` means "did not scan", which is the half of the Goal that makes the field trustworthy rather than merely populated; unpinned, a partial count on the failure path would pass the suite and the field would become misleading. (b) Add it silently: rejected, an assertion that passes pre-change is easily mis-presented as evidence of the fix, so V-04 makes the executor say otherwise in writing. | `probe_sanitizer`'s `except` branch returning before assignment; the non-git measurement; no existing test references `scanned_files` | yes |
| D-4 | Was E-04 over-scope, given the plan is `low` priority and had three items? | NO, it is in scope: same method, two assertions, no new fixture. | (a) File it as a follow-up item: rejected, the invariant belongs with the change that gives the field meaning, and a separate item would leave a window where the field is populated but its zero is unpinned. (b) Split into a fourth E-item with its own fixture: rejected as genuine over-scope; the non-git probe needs only a second `TemporaryDirectory` in the method E-03 already writes. | The plan's own right-sizing rule; `aw ipd lint --phase review-finalize` conforming at four E-items; the size thresholds (>18 E-leaves, >5 groups) are nowhere near | yes |

### Deferred and open

- (none). All eight findings are FIXED in place. Two of them (PR-901's contract change, PR-905's human
  render line) have their FIXES deliberately outside this plan, recorded as F-3 and F-4 with
  Carrier-Declined reasons and surfaced in the approval gate. Under the Fix Bar that is correct scoping
  rather than deferral: nothing this plan is responsible for was left unfixed. No finding sits at or
  above the repository gate threshold (`HIGH`), so no escalation to a `- Blocking: yes` question is
  owed. OQ-01 was already resolved by the author and I confirmed its reasoning with numbers rather than
  re-opening it; it gained a Carrier-Declined. No question required the human: every judgement above
  was answerable from the repository, and the one contract question I refused to pre-empt (D-1) is
  recorded for the maintainer rather than decided.
