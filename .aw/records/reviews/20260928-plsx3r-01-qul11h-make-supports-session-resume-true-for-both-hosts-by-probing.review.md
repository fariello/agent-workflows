# Review findings: plan qul11h

- Subject-Id: qul11h
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `e63e9680` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` CONFORMS
after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: `git status --porcelain --`
on the plan path was empty.

THE PLAN'S DIAGNOSIS IS CORRECT AND ITS DESIGN IS RIGHT. Every premise reproduced. F-01 reproduces:
`aw host capabilities antigravity` prints `NO   supports_session_resume` while `opencode` prints
`yes`. F-03 reproduces exactly (`ACTION_CLASSES == ('read_only',)`,
`ACTION_CAPABILITY_REQUIREMENTS['read_only'].required == ()`). F-02's shipped proof exists and its
capture technique is reusable verbatim. F-04 reproduces (`oc_runipd` imports this module at module
level, so the function-local import really is mandatory). F-05 reproduces: the re-entry chain is
`detect_host_capabilities` -> probe -> `run_opencode` -> `_apply_execution_profile` ->
`detect_host_capabilities`, with exactly ONE such call per `run_opencode` as claimed. F-07 reproduces
and its reasoning for deferring rather than fixing is sound (that field IS consumed by
`run_discovery_then_execution`'s barrier decision). Most importantly, I BUILT the probe E-03
prescribes and it WORKS: `(True, "observed --session <sentinel> ...")` for opencode,
`(True, "observed --conversation <sentinel> ...")` for antigravity, and
`(False, "no resume argv builder is known ...")` for `scripted`. The sentinel requirement is
well judged, OQ-01's resolution against deletion is correctly evidenced, OQ-02's in-process default is
right for the reason it gives, and E-05 is exactly the load-bearing test the backlog item asked for.

WHAT REVIEW FOUND IS ONE FALSIFIED FINDING THAT THE PLAN'S ORDERING ANALYSIS RESTS ON, plus an
unstated side-effect profile, an unstated behavior change, and a wedge risk in the prescribed guard.

**F-08 IS FALSE IN BOTH HALVES, AND ITS CONCLUSION IS THE OPPOSITE OF THE TRUTH (PR-301, HIGH).**
F-08 states that pending plan `iot7hc` "does NOT name `host_sandbox_profile.py`" and that "its OQ-02
explicitly asks whether it may edit that file's docstring", concluding "NO path overlap, so the two can
run in either order". MEASURED: `iot7hc`'s `- Scope-Paths:` DOES include
`agent_workflows/host_sandbox_profile.py`; its OQ-02 is `resolved`, and its own review record says in
terms "OQ-02 RESOLVED by taking the plan's own default: `host_sandbox_profile.py` added to
`Scope-Paths` for one docstring paragraph". Worse for the ordering conclusion, `iot7hc` is
`- Status: approved` with `- Item-Dependencies: none`, i.e. runnable NOW, while this plan is not yet
reviewed - so the realistic order is `iot7hc` first. And both plans edit the SAME module docstring:
`iot7hc` E-06 rewrites the `HONEST LIMIT: nothing in the runners consults this preflight yet`
paragraph, this plan's E-06 edits the docstring's list of what is decided by attempt. The correct
disposition is still NOT to declare a dependency (they overlap as FILES, not as instructions, which is
what worktree isolation and the merge-and-revalidate gate handle), but the plan reached that right
answer from two false premises, and an executor trusting F-08 would neither expect the docstring
conflict nor know to preserve `iot7hc`'s paragraph.

**THE PROBE IS NOT SIDE-EFFECT FREE, AND IT WOULD RUN INSIDE A READ-ONLY VERB (PR-302, MEDIUM).**
E-03 frames the probe as building an argv and refusing to launch, and V-03 asks only for evidence that
"NO host process was launched". But the builders are not pure. MEASURED with `Popen` swapped and
`subprocess.run`/`check_output` counted: the OPENCODE path spawns THREE real subprocesses before the
seam (a python landlock-probe `boot.py`, a `bwrap` sandbox attempt, and `git ls-files -s --cached`) and
WRITES THREE ARTIFACTS into whatever run directory it is given
(`01-<id6>-a1-execute-*.jsonl`, `01-<id6>-attempt-1.jsonl`, `telemetry`); the ANTIGRAVITY path spawns
ONE and writes the same three. `aw host capabilities` is a shipped READ-ONLY verb, so a probe wired
into `detect_host_capabilities` inherits these on every invocation. The effects are containable and the
cost is fine (the sandbox probe is cached module-level: 41 ms first call, 0.002 ms after), but the plan
has to SAY so and confine them, because "refuses to launch" reads as "does nothing".

**THE FIX CHANGES A SHIPPED REPORTED VALUE ON TWO PLATFORMS (PR-303, MEDIUM).** The gate's central
reassurance is "NO RUN CHANGES BEHAVIOR", true about gating and over-read as a claim about the report.
MEASURED: the identity branch sits AFTER BOTH early returns, so today
`detect_host_capabilities("opencode","darwin").supports_session_resume` is **False**, and `win32` too.
E-04 deliberately places the verdict before the platform gate, making both **True** - which V-04(d)
explicitly requires as proof of correct placement. So it is intended and correct (an argv list is
platform-independent), but it is a change to a shipped value on two platforms that the approval
statement describes only as fixing the antigravity row, and V-04(d) as written would have the executor
paste the new `True` with no before-state to show it moved.

**THE PRESCRIBED RE-ENTRANCY GUARD CAN WEDGE THE VERDICT FOR THE PROCESS (PR-304, MEDIUM).** E-04
mandates a module-level flag and the conservative `False` while it is set, which is right. It does not
say the flag must be CLEARED in a `finally`. This module's own convention for process-global mutable
state is explicit (`_FORCED_RUNNER_SAFETY`: "a test that sets it MUST restore it"), and the plan itself
mandates a `finally` for the `Popen` swap for exactly this reason. If the probe raises while the guard
is set and the clear sits only on the success path, the flag stays set for the interpreter's life and
every later `detect_host_capabilities` silently returns the conservative `False` - the original defect,
inverted, and invisible because the fail-closed direction looks like correct behavior.

**A ONE-LINE ACCURACY FIX (PR-305, LOW).** The Scope check said the two plans "share no path", which
PR-301 falsifies; it now states the overlap, why no dependency is declared anyway, and what the
executor must therefore do.

Everything else checked and HELD. `tests/test_hostdedup_third_host.py::ThirdHostCapabilitiesTests`
already asserts `supports_session_resume` False for `scripted`, so E-02's case (3) agrees with a
shipped test rather than contradicting one; `CONTRACT_FIELDS` already contains the field, so the plan
correctly adds none; all four deferral carriers (`42da1n`, `b7tlsh`, `oq05nc`, and the declined
`iot7hc` row) resolve to real artifacts, with `42da1n` confirmed `open` / `bug` /
`Blocks-Release: next` exactly as E-07 will require; F-09's cost figures reproduce in the same range
(31 ms opencode, 20 ms antigravity warm, against 0.40 ms for a warm `detect_host_capabilities`); and
the `emits_structured_tool_events` deferral is correctly reasoned and correctly filed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-301 | HIGH | IN-SCOPE | A. Correctness / G. Executability | MEASURED at HEAD `e63e9680`: `iot7hc`'s `- Scope-Paths:` includes `agent_workflows/host_sandbox_profile.py`; its OQ-02 is `- Status: resolved` and its review history records "OQ-02 RESOLVED ... `host_sandbox_profile.py` added to `Scope-Paths` for one docstring paragraph"; it is `- Status: approved`, `- Item-Dependencies: none`. Its E-06 targets the docstring's `HONEST LIMIT: nothing in the runners consults this preflight yet` paragraph (present in the file); this plan's E-06 targets the same docstring | **F-08 IS FALSE IN BOTH HALVES.** The sibling plan DOES declare this file and its OQ-02 is NOT open, so "NO path overlap, so the two can run in either order" is wrong; and since `iot7hc` is already approved and dependency-free while this plan is unreviewed, it will realistically run FIRST. Both plans edit the same module docstring. The right disposition (no declared dependency) is unchanged, but it was reached from false premises, so an executor trusting F-08 would neither expect the conflict nor know to preserve the sibling's paragraph. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-08 rewritten as FALSIFIED with the measurements and the corrected consequence; E-06 gained a re-read-and-preserve instruction naming the sibling's paragraph; the Scope check's "shares no path" bullet replaced with the measured overlap plus why no dependency is declared; the approval gate names it. |
| PR-302 | MEDIUM | IN-SCOPE | C. Operability / B. Least surprise | MEASURED at HEAD `e63e9680` driving each real builder with `Popen` swapped and `subprocess.run`/`check_output` counted: OPENCODE spawned 3 subprocesses (`python .../boot.py`, `bwrap --unshare-user ...`, `git ls-files -s --cached`) and created `01-abc123-a1-execute-*.jsonl`, `01-abc123-attempt-1.jsonl`, `telemetry` under the run dir; ANTIGRAVITY spawned 1 and created the same three. `_probe_linux_sandbox` is cached (41 ms then 0.002 ms) | **"REFUSES TO LAUNCH" IS NOT "HAS NO EFFECTS", AND THIS RUNS IN A READ-ONLY VERB.** The builders do real work before the seam, including a sandbox attempt and journal/telemetry writes into whatever run directory they are handed. V-03's only side-effect requirement was that no HOST process launched, which is satisfiable while the probe still writes into an operator's tree on every `aw host capabilities`. | C:Low; U:Medium; S:Low; F:Low; Overall:Low | FIXED | E-03 gained the measured effect inventory and two requirements: the probe must own a THROWAWAY temp tree (the shape `HostResumeSpellingTests._argv` already uses), must never be handed a caller-supplied or real run dir, and must clean up; its note must not imply nothing executed. Its Expected outcome now demands confinement. New F-10. V-03 now requires the spawned-subprocess count and the temp-tree listing, and explicitly rejects a "no side effects" claim as measurably false. |
| PR-303 | MEDIUM | IN-SCOPE | A. Correctness / F. Honest documentation | MEASURED at HEAD `e63e9680`: `detect_host_capabilities("opencode","darwin").supports_session_resume` is **False** today (and `win32` False), because the identity branch sits after both early returns; E-04 moves the verdict before the platform gate and V-04(d) requires it to read `True` | **A SHIPPED REPORTED VALUE CHANGES ON TWO PLATFORMS, AND THE GATE DOES NOT SAY SO.** "NO RUN CHANGES BEHAVIOR" is true about gating and reads as a claim about the report. The change is intended and correct, but an approver is not told, and V-04(d) as written asks for the new `True` with no before-state, so it cannot distinguish "the placement moved it" from "it was always True". | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 states the measured off-platform before/after and requires a comment beside the placement; V-04(d) now requires BOTH the before and after for the darwin query; the approval gate's reassurance paragraph gained the change as the first of three review additions. New F-11. |
| PR-304 | MEDIUM | IN-SCOPE | A. Correctness / D. Anti-regression | The module's own convention for process-global state: `_FORCED_RUNNER_SAFETY`'s comment "a test that sets it MUST restore it (use `forced_runner_safety_verdicts`)"; the plan's own `finally` mandate for the `Popen` swap; the measured re-entry chain with one `detect_host_capabilities` call per `run_opencode`. Plan E-04 as authored: "GUARD RE-ENTRANCY WITH A MODULE-LEVEL FLAG" with no clearing discipline stated | **A GUARD SET WITHOUT A `finally` WEDGES THE VERDICT FOR THE WHOLE PROCESS.** If the probe raises while the flag is set and the clear is on the success path only, every later call returns the conservative `False`, including every `aw host capabilities` in that process - the original defect inverted, and invisible precisely because fail-closed looks correct. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now requires the guard set and cleared in a `try/finally`, citing the module's own `_FORCED_RUNNER_SAFETY` convention and the measured re-entry chain, and its Expected outcome names the clearing. V-04(e) now requires evidence the guard is CLEARED after a deliberately raising probe, not merely that it fired. New F-12. |
| PR-305 | LOW | IN-SCOPE | G. Executability (scope honesty) | PR-301's measurement against the Scope check bullet "The pending plan `iot7hc` shares no path with this one (F-08), so no ordering constraint is declared" | The scope fence asserted a non-overlap that does not hold, so a reader auditing the fence would conclude the two plans cannot conflict. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bullet now states the measured overlap, that no dependency is declared because the overlap is in FILES rather than instructions, and the three consequences the executor carries (re-read the docstring, preserve the sibling's paragraph, expect a confined merge conflict). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | PR-301: `iot7hc` overlaps this file and is already approved. Declare an `- Item-Dependencies:` edge, or keep them independent? | KEEP THEM INDEPENDENT and correct the reasoning. No dependency edge is added. | (a) Declare `executed:iot7hc`: rejected. The overlap is in FILES and one docstring, not in instructions - neither plan's correctness depends on the other's outcome - and the repository's own recorded position (restated in `AGENTS.md` and applied by three sibling reviews this sweep) is that file overlap is exactly what per-item worktree isolation plus the merge-and-revalidate gate handle, while a spurious edge can strand a runnable plan behind one that may never execute. (b) Ask this plan to drop its docstring edit to avoid the conflict: rejected, E-06 exists because the docstring is the module's published guarantee and leaving it stale would ship a guarantee this plan falsified. | `iot7hc`'s measured `- Scope-Paths:`, `- Status: approved` and `- Item-Dependencies: none`; the two plans' distinct E-06 targets within one docstring; the standing treatment of file overlap under worktree isolation. | yes |
| D-2 | PR-302: should the probe be forbidden from running inside `aw host capabilities`, or merely confined? | CONFINE IT. The probe stays wired into `detect_host_capabilities`, and E-03 must own a throwaway temp tree and touch no caller-supplied run directory. | (a) Forbid it in the read-only verb and compute the verdict only when a runner asks: rejected, the verb's whole purpose is to report capabilities, and a field that is `False` in the report because the report declines to probe it would reproduce the exact defect this plan fixes. (b) Cache the verdict module-level so the effects are paid once per process: TEMPTING and measurably cheap, but rejected as a reviewer-imposed design change - the sandbox probe's cache is a precedent for it, and the executor may add it, but mandating it here would conflate confinement (required) with optimization (optional) and the measured cost does not force the issue. | The measured subprocess and artifact inventory; `aw host capabilities` being a documented read-only verb; `HostResumeSpellingTests._argv`'s existing temp-tree shape as the available precedent; the measured module-level caching of `_probe_linux_sandbox` as the optional optimization. | yes |
| D-3 | PR-303: is the off-platform `False` -> `True` change acceptable, or should the verdict stay inside the platform gate? | ACCEPT IT as intended, and require it be DISCLOSED and pinned with a before/after. | Keeping the verdict inside the platform gate: rejected on the plan's own correct reasoning - the capability reads an argv list and is genuinely platform-independent, so gating it on the running platform would make the report claim on macOS that neither host can resume, which is the same class of lie the plan exists to remove. E-04 already forbids "restoring parity" for this reason; what was missing was the disclosure, not the decision. | The measured off-platform values today; E-04's own placement rationale; V-04(d)'s existing demand for the darwin `True`, which shows the author intended the change. | yes |

Every finding is `FIXED`; none is left `OPEN` or `DEFERRED`, so no escalation to a `- Blocking: yes`
question is owed and the repository's `HIGH` gate threshold is satisfied without one. PR-301 is `HIGH`
and was FIXED in place rather than escalated, which is correct under the Fix Bar: its overall
Remediation Risk is Low (a prose and instruction correction, with no code consequence beyond an
executor re-reading a docstring). No decision above is `Reversible: no`. OQ-01 and OQ-02 remain
`resolved` as authored and both were checked; no new open question is created.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- No pre-review snapshot was owed: `git status --porcelain -- <plan>` was EMPTY before editing.
- **F-01 REPRODUCED.** `python3 -m agent_workflows host capabilities antigravity` prints
  `NO   supports_session_resume` and `NO   emits_structured_tool_events`; the same verb for `opencode`
  prints `yes` for both.
- **F-03 REPRODUCED EXACTLY.** `ACTION_CLASSES == ('read_only',)` and
  `{'read_only': ()}` for the requirement map.
- **THE IDENTITY BRANCH READ IN PLACE.** `if host == "opencode":` assigns
  `caps.emits_structured_tool_events = True` and `caps.supports_session_resume = True`, under the
  comment the plan quotes, and it is the LAST thing before `return caps`.
- **F-04 REPRODUCED.** `oc_runipd` imports this module at module level, and
  `_apply_execution_profile`'s source contains `capabilities = detect_host_capabilities("opencode")`.
- **F-05 REPRODUCED.** Instrumenting `detect_host_capabilities` and driving one real `run_opencode`
  recorded exactly **1** call at max nesting depth 1, matching F-05's "exactly one such call per
  `run_opencode`"; the chain is `detect_host_capabilities` -> probe -> `run_opencode` ->
  `_apply_execution_profile` -> `detect_host_capabilities`.
- **E-03's PROBE BUILT AND EXERCISED.** Implementing it exactly as specified (function-local import,
  `Popen` swap in a `finally`, sentinel adjacency test) returned
  `(True, "observed --session ses-probe-sentinel in the host's own resume argv")` for opencode,
  `(True, "observed --conversation ses-probe-sentinel ...")` for antigravity, and
  `(False, "no resume argv builder is known for host 'scripted'")` for the third host. So the
  mechanism works as designed.
- **PR-302, THE SIDE-EFFECT INVENTORY.** OPENCODE: 3 subprocesses
  (`['<python>', '/tmp/aw-ll-probe-*/boot.py']`, `['bwrap', '--unshare-user', '--ro-bind', ...]`,
  `['git', 'ls-files', '-s', '--cached']`) and 3 created paths
  (`01-abc123-a1-execute-*.jsonl`, `01-abc123-attempt-1.jsonl`, `telemetry`). ANTIGRAVITY: 1
  subprocess (`git ls-files`) and the same 3 paths. `_probe_linux_sandbox` measured cached (41.26 ms
  then 0.002 ms).
- **PR-303, THE OFF-PLATFORM VALUES TODAY.** `opencode`/`linux` -> True; `opencode`/`darwin` -> False;
  `opencode`/`win32` -> False; `antigravity` -> False on all three.
- **F-09's COSTS REPRODUCE IN RANGE.** Warm `detect_host_capabilities` 0.40 ms; probe 31 ms
  (opencode) and 20 ms (antigravity) warm, against F-09's recorded 46 ms / 22 ms cold.
- **SHIPPED TESTS CHECKED FOR COLLISION.** `CONTRACT_FIELDS` in
  `tests/test_host_sandbox_profile.py` already lists `supports_session_resume`, so no field is added
  or removed. `tests/test_hostdedup_third_host.py::ThirdHostCapabilitiesTests` asserts
  `assertFalse(caps.supports_session_resume)` for `scripted`, which AGREES with E-02's case (3).
  `tests/test_defect_report.py::HostResumeSpellingTests` exists with the two argv tests F-02 names and
  the `_argv` capture helper E-03 reuses.
- **CARRIERS ALL RESOLVE.** `42da1n` at `.aw/records/backlog/open/` with `- Status: open`,
  `- Work-Kind: bug`, `- Blocks-Release: next` and a Summary naming the
  `emits_structured_tool_events` defect, exactly what E-07 will require; `b7tlsh` and `oq05nc` both
  exist under `.aw/records/backlog/open/`.
- **F-07 CONFIRMED CONSUMED.** `emits_structured_tool_events` is read at the
  `run_discovery_then_execution` barrier decision (`supports_read_only_phase and
  capabilities.emits_structured_tool_events`), so the plan is right that flipping it would change
  behavior and right to defer it.
- Post-revision suite re-check: `python3 -m pytest` -> `2970 passed, 2 skipped, 3 warnings in 58.37s`
  (plus the standard `201 tests were deselected` notice), confirming this review touched no code (it
  edited only the plan and this record). NOTE FOR THE EXECUTOR, since this plan's E-08 asks for a
  before/after comparison: the count at THIS HEAD is 2970, not the 2935 recorded by sibling plans
  earlier in the same sweep, because `main` advanced between them. Re-derive the baseline at the same
  commit as the after-state and judge on the delta of failing node ids, never on a carried number.
- `aw sanitize --agent` -> exit 0, no findings.

### Probe scripts

The two probe scripts backing these measurements were written under
`.aw/workflow-artifacts/plan-review-qul11h/` (gitignored, so not committed): `probe_resume.py` (E-03's
probe built and exercised on all three hosts, the F-05 re-entry instrumentation, the F-09 costs, and
the off-platform value table) and `probe_sideeffects.py` (the subprocess and artifact inventory each
builder produces before the launch seam).
