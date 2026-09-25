# Review: Make aw doctor report a found leak instead of a probe crash

- Subject-Id: rpqv4q
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `93a0e8a0`. The plan cites `0c2e7970`, an ancestor; both were checked and
the measurements agree. The target plan was committed and unchanged, so the pre-review snapshot was
correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0) BEFORE review and again at `--phase review-finalize` afterwards.

THE PLAN IS CORRECT AND UNUSUALLY WELL MEASURED FOR ITS SIZE. I REPRODUCED THE BUG rather than
reading it: a throwaway git repo with one committed file containing a real home path yields 2 real
`Finding`s while `probe_sanitizer(...).drift` carries exactly
`[('doctor.probe-failed', "'Finding' object has no attribute 'matched'")]`. F-1 and F-2 both hold.
`doctor.py:688` is the ONLY `.matched` site in the package, so the diagnosis is complete as well as
correct. The plan's parenthetical correction of its own source backlog item is also right, and I
checked it specifically because a plan correcting its item is where an over-claim would hide: the
human render does list both leaks (`- f.py:1: home-path (fail: ...)`), because `res.findings` is
assigned before the loop that raises. I found the same is true of a channel the plan does not mention:
`SanitizerProbeResult.to_dict()["findings"]` already reads `f.snippet` correctly, so the JSON findings
array is fine too. The defect is confined to the DRIFT channel, which the revised Concern now says
precisely instead of "agent/JSON consumers".

THE DOMINANT FINDING IS PR-801, AND IT RAISES THE STAKES OF THE FIX RATHER THAN CHANGING IT. The plan
frames the cost as a wrong rule name seen by automation. Measured, the cost is a LOST REMEDIATION:
`build_remediation` dispatches on the `doctor.leak-` prefix to return `aw sanitize --fix`, so in a
planted-leak repo today `build_remediation(probe-failed).command` is `None` and
`resolve_next_actions` returns an EMPTY list, while the same call on a `doctor.leak-home-path` drift
returns `aw sanitize --fix` as both the action and the primary. So that branch of `build_remediation`
is currently DEAD CODE, and a repository with a real leak is told nothing about how to fix it. I
confirmed the offered fix is genuine rather than decorative: `home-path` is one of the classes
`fix_working_tree` actually rewrites (`_HOME_ANY_RE.sub("~", line)`). E-02 now asserts the recovered
next action, which is what turns "the rule name is right" into "the consumer gets the repair".

THE SECOND MATERIAL FINDING IS PR-803, AND IT IS THE ONE MOST LIKELY TO HAVE BITTEN THE EXECUTOR.
E-02 said to commit "a file containing a home-directory path". The obvious implementation interpolates
`$HOME`, and that is machine-dependent: measured, a planted `/home/<real-user>/secret/x` fires TWO
rules, `home-path` AND `handle`, because the maintainer's username matches a second pattern
(`"handle": re.compile(re.escape(_H) + ...)`). So the test would see 2 findings on the maintainer's
machine and 1 in CI. Worse, a tracked test file containing a real home path is itself precisely what
`aw sanitize` exists to reject, so the regression test would plant the very leak class it tests for. A
neutral literal ``"/home/" + "someuser" + "/x"`` fires exactly `home-path` (measured), because that rule is generic
and excludes only the documented placeholders. E-02 now specifies the neutral literal and says why,
and V-02 requires a clean `aw sanitize --agent` on the worktree to prove the test did not introduce a
leak.

PR-802 IS A FIX-MECHANISM CORRECTION, and it matters because the plan's own wording admits the wrong
implementation. E-01 said to "narrow the `except` so it catches only errors from `scan_working_tree`
itself". The natural reading is a type filter, and a type filter is exactly wrong here: the bug IS an
`AttributeError`, and a genuine scan failure could raise one too, so `except AttributeError` or any
type-based narrowing would re-mask this class of defect. The correct change is structural, scoping the
`try` to the CALL and moving the Drift-building loop out of it, which is what "only errors from the
scan itself" actually requires. E-01 now states that and explicitly forbids the type-filter reading;
V-01 refuses a diff that narrows by type.

PR-804 IS AN HONESTY GAP IN THE VALIDATION, not a defect in the fix. E-03 runs `aw doctor --agent` on
THIS repository and expects no sanitizer `probe-failed`. But this repository is leak-clean
(`aw sanitize --agent` -> `findings:0` at review), so that run exercises the path where there are no
findings and the loop never executes. It proves the probe does not crash; it proves nothing about leak
reporting, which is the plan's entire goal. Presented without that caveat it reads as positive
evidence and is not. E-03 and V-03 now say which is which, and point at V-01/V-02 for the positive
evidence.

A SECOND, INDEPENDENT DEFECT IN THE SAME FUNCTION, recorded as PR-806 and deliberately NOT fixed here.
`SanitizerProbeResult.scanned_files` is declared, emitted in `to_dict()`, and published as agent
evidence, but is never assigned anywhere in the package, so every consumer reads a hardcoded 0.
Measured with one tracked file and two findings: `sanitizer evidence: {'scanned_files': 0,
'findings': 2}`. I did not absorb it: it is a different field, and `leak_sanitizer.scan_working_tree`
returns only a findings list, so there is no count to assign without an API change. Folding that into
a high-priority one-line bug fix would be the kind of scope creep that delays the fix. I filed it as
backlog item `c0ppo0` (`bug`, `Blocks-Release: next` per the live-bug gate policy) and recorded it in
Deferred with that carrier. NOTE on process: I first wrote a carrier id from `aw backlog new`'s DRY-RUN
output, which mints a different id than `--apply` does; I caught it by resolving the id and corrected
it to the applied `c0ppo0`. A dangling `Carrier` would have been a false handoff claim, and
`check.from-backlog-dangling` exists because that mistake is easy.

ON EXIT CODES, which I checked because a reporting change that also moves a gate would need the human
to know: it does not. `drift_exit_code` returns 1 for any non-`info` drift, and both the old
`probe-failed` and the new per-finding leak drifts are non-`info`, so `aw doctor` exits 1 either way.
What changes is the drift COUNT (one aggregate becomes one per finding) and therefore the summary
total. Stated in the gate so approval is informed.

Backlog item `muwwa5` carries `- Blocks-Release: next` and `- Work-Kind: bug`; the plan correctly
inherits both, so the release gate is preserved by the handoff, and the gate now says so explicitly.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | UNDER-SCOPE | C. Architecture / F. Prevent silent failure | Driven in a planted-leak repo: `build_remediation(probe-failed).command` -> `None` and `resolve_next_actions` -> `[]`; the same for a `doctor.leak-home-path` drift -> `'aw sanitize --fix'`, primary `aw sanitize --fix`; `doctor.build_remediation` dispatches on `rule.startswith("doctor.leak-")`; `leak_sanitizer._HOME_ANY_RE.sub("~", line)` | THE PLAN UNDERSTATES ITS OWN DEFECT: THE REAL COST IS A LOST REMEDIATION AND A DEAD CODE BRANCH. Framed as automation seeing a wrong rule name, the fix looks like tidier reporting. Measured, because the rule name never reaches `build_remediation`, a repository with a real leak is handed NO next action at all, and the branch that would return `aw sanitize --fix` is unreachable. That fix is real (`home-path` is auto-rewritten), so the user is being denied an actionable repair, not just a label. | C:Low; U:Low; S:Low; F:Low; Overall:Low (the fix E-01 already makes restores it; only the plan's framing and one assertion were missing) | FIXED | Concern and Goal rewritten around the lost remediation; F-3 added with the driven measurement; E-02 now asserts `build_remediation(...).command == "aw sanitize --fix"` and a non-empty `resolve_next_actions`, so the dead branch is proven live; a conventions bullet records that a drift rule name is a dispatch contract rather than a label. |
| PR-802 | MEDIUM | IN-SCOPE | A. Correctness (the fix mechanism) | The bug is an `AttributeError` raised inside the loop; `scan_working_tree` can itself raise `AttributeError`; original E-01: "narrow the `except` so it catches only errors from `leak_sanitizer.scan_working_tree` itself" | THE ITEM'S WORDING INVITES THE ONE NARROWING THAT RE-MASKS THIS BUG. The natural reading of "narrow the except" is a type filter, and a type filter is precisely wrong: the defect IS an `AttributeError`, so `except AttributeError` would catch the next occurrence of this same class of programming error and convert it back into a plausible probe failure. The correct change is structural (scope the `try` to the call, move the loop out), which is what the item meant but did not say. | C:Low; U:Low; S:Low; F:Medium (a type filter would silently preserve the defect class); Overall:Low | FIXED | E-01 now specifies the structural change (assign `findings` inside the `try`, build Drifts outside) and explicitly forbids narrowing by exception type, with the reason. V-01 refuses a diff that narrows by type instead. |
| PR-803 | MEDIUM | IN-SCOPE | E. Testing (a non-portable, self-defeating fixture) | Planted ``"/home/" + $(whoami) + "/secret/x"`` -> rules `['home-path', 'handle']`; planted ``"/home/" + "someuser" + "/secret/x"`` -> `['home-path']`; `"handle": re.compile(re.escape(_H) + r"(?!@fariel\.com)")`; `"home-path"` excludes only `u/`, `alice/`, `user/`, `USER/`, `<` | THE OBVIOUS IMPLEMENTATION OF E-02 IS MACHINE-DEPENDENT AND PLANTS THE LEAK IT TESTS FOR. "A file containing a home-directory path" naturally becomes an interpolated `$HOME`, which fires a SECOND rule (`handle`) on the maintainer's machine but not in CI, so any count-based assertion differs by host; and a tracked test file holding a real home path is exactly what `aw sanitize` rejects, so the regression test would introduce a leak into the tree it guards. | C:Low; U:Low; S:Medium (a committed real home path is the leak class itself); F:Low; Overall:Low | FIXED | E-02 now specifies the neutral literal ``"/home/" + "someuser" + "/x"`` with the measured rule sets behind the choice, and warns against interpolating `$HOME`. V-02 requires confirming the fixture is neutral AND pasting a clean `aw sanitize --agent` on the worktree. Added F-4 and a conventions bullet distinguishing the generic `home-path` rule from the maintainer-specific `handle` rule. A stop condition covers the fixture firing more than one rule. |
| PR-804 | MEDIUM | IN-SCOPE | E. Testing (evidence that does not support the claim) | `aw sanitize --agent` on this tree -> `findings:0`, exit 0; `probe_sanitizer` builds Drifts only inside `for f in findings`, so a clean tree never enters the loop | E-03'S EVIDENCE CANNOT DEMONSTRATE THE PLAN'S GOAL, AND READS AS IF IT DOES. A doctor run on THIS repository exercises the zero-findings path, where the failing loop never executes, so a clean result proves only that the probe does not crash. The plan's goal is that a FOUND leak is reported, and no item required evidence from a repository that has one until V-01/V-02 were strengthened. An executor could truthfully paste a green run and leave the actual fix unverified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and V-03 now state plainly what the clean run does and does not prove and point at V-01/V-02 for positive evidence; V-01 requires the observed before/after drift list from a planted-leak repo; V-03 adds the `tests/test_doctor.py` count against its measured `19 passed` baseline. |
| PR-805 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: two sentences, `Cohesion rationale: not required`, no scope fence, no approval paragraph, no stop conditions, an UNCONDITIONAL finalize instruction; V-01's entire evidence requirement was "paste the diff" | THE GATE AND V-01 WERE BOTH THINNER THAN THE CONTRACT REQUIRES. No scope fence (so finalize reconciliation had nothing to reconcile against), no statement of what approval means, no stop conditions, and finalize instructed unconditionally rather than with runner/executor ownership. V-01 asking only for a diff is the specific weakness: a diff shows the edit, not the behavior change, which for this plan is the whole point. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten: an approval paragraph (including that the exit code does NOT change but the drift count does), a per-path scope fence naming `build_remediation`/`resolve_next_actions` as expected-unmodified and `scanned_files` as deliberately untouched, the honesty rule naming the two easiest-to-fake claims, two genuine stop conditions, conditional runner/executor finalize ownership, and the `muwwa5` close with its inherited release gate stated. V-01 now demands observed before/after drift output beside the diff. Cohesion rationale left `not required` (correct at three items). |
| PR-806 | LOW | OVER-SCOPE (recorded, not absorbed) | A. Correctness (a second defect in the same function) | Driven with 1 tracked file and 2 findings: `sanitizer evidence: {'scanned_files': 0, 'findings': 2}`; `scanned_files` appears at its declaration, in `to_dict()`, and in the agent Evidence block, and is assigned NOWHERE in the package; `scan_working_tree` returns only `list[Finding]` | A SECOND, INDEPENDENT DEFECT SITS IN THE FUNCTION BEING EDITED: `scanned_files` is published as agent evidence but never assigned, so every consumer reads a hardcoded 0 even when files were scanned. Found while verifying the probe's agent payload. Recorded rather than fixed: it is a different field, and the sanitizer returns no count to assign, so the fix needs an API change that does not belong inside a one-line high-priority bug fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded and carried rather than repaired in place. Added F-5; recorded in Deferred with `- Carrier: c0ppo0`, a backlog item I filed at review (`bug`, `Blocks-Release: next` per the live-bug gate). The gate's scope fence names `scanned_files` as deliberately untouched so the omission is a declaration rather than an oversight. |

| PR-807 | MEDIUM | IN-SCOPE | E. Testing (a defect this review introduced, then measured) | `aw sanitize --agent` reported 5 `home-path` findings, all in this plan file, after the reviewer wrote the recommended fixture path as a full literal; `leak_sanitizer._ALLOWED_PATHS` contains only `tests/test_packaging.py`, `tests/test_local_leaks.py`, `tests/test_leak_sanitizer.py`, `agent_workflows/local_leaks.py`, `agent_workflows/leak_sanitizer.py`; a runtime-composed path plants `['home-path']` while the composing source line is unflagged; the rule excludes `user`/`USER`/`alice`/`u`/`<...>` | THE FIX FOR PR-803 REPRODUCED PR-803'S OWN FAILURE MODE, AND IT IS WORTH RECORDING BECAUSE THE PLAN TELLS AN EXECUTOR TO WRITE THIS EXACT STRING INTO A TRACKED TEST FILE. Prescribing a neutral account name is necessary but NOT sufficient: `tests/test_doctor.py` is not sanitizer-allowlisted, so any full `/home/<name>/...` literal in it fails `aw sanitize` and makes the regression test plant the leak class it guards. I discovered this by committing the mistake into the plan and running the gate. The remedy is mechanical (compose the path at runtime from pieces) and the rule's placeholder exclusions cannot substitute, since a placeholder is not flagged and so plants nothing. | C:Low; U:Low; S:Medium (the prescribed fixture would have failed the repository's own leak gate); F:Low; Overall:Low | FIXED | E-02 now requires composing the path at runtime, names the allowlist by contents, records that the placeholders do not work as fixtures, and cites the reviewer's own 5-finding measurement as the evidence. Added F-6. Re-verified: `aw sanitize --agent` -> `findings:0`, exit 0, and `aw ipd lint --phase review-finalize` conforming. V-02 already required a clean sanitizer run on the worktree, which is what would have caught this in execution. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the `except` be narrowed by exception TYPE, as E-01's wording suggests, or should the `try` block be scoped structurally? | Scope the `try` to the `scan_working_tree` call alone and move the Drift loop outside it; forbid a type filter. | (a) `except AttributeError` or any type-based narrowing - rejected on the defect's own nature: this bug IS an `AttributeError` and a genuine scan failure can raise one, so a type filter would re-mask exactly this class of error and the plan would half-fix itself. (b) Remove the `except` entirely - rejected: a real scan failure (unreadable tree, git absent) should still degrade to `doctor.probe-failed` rather than crash the whole doctor run. | the reproduced `AttributeError`; `scan_working_tree`'s body, which can raise beyond the call it wraps; the five other probes' `probe-failed` convention | yes |
| D-2 | What should the regression test plant: the running user's real home path, or a neutral one? | A neutral account name (`someuser`), COMPOSED at runtime rather than written as a full literal. | (a) Interpolate `$HOME` - rejected on measurement: it fires `home-path` AND `handle` on the maintainer's machine but only `home-path` in CI, so the assertion is host-dependent. (b) A neutral FULL LITERAL in the test source - rejected after measuring it (PR-807): `tests/test_doctor.py` is not sanitizer-allowlisted, so the literal fails `aw sanitize` and the test plants the leak class it guards. (c) Use the rule's placeholders (`user`, `alice`, `<name>`) - rejected: they are explicitly excluded by the pattern, so they plant nothing and the test would assert on zero findings. | planted real path -> `['home-path', 'handle']`; planted neutral path -> `['home-path']`; `_ALLOWED_PATHS` contents; the composed form planting `['home-path']` with its source line unflagged | yes |
| D-3 | Is a clean `aw doctor --agent` run on this repository adequate evidence for the plan's goal? | No; keep the run but label it as crash-only evidence and require planted-leak evidence in V-01/V-02. | (a) Accept it as the primary evidence - rejected: this tree is leak-clean, so the failing loop never executes and the run cannot speak to leak reporting at all. (b) Drop E-03 - rejected: a live run on the real repository is still worth having as a no-regression check, and it is cheap. | `aw sanitize --agent` -> `findings:0` on this tree; `probe_sanitizer` builds Drifts only inside `for f in findings` | yes |
| D-4 | The `scanned_files` defect found at review: fix it here, or carry it? | Carry it, as a filed backlog item, and declare it untouched in the scope fence. | (a) Fix it in this plan - rejected: `scan_working_tree` returns only findings, so assigning a real count requires an API change, and widening a high-priority one-line fix delays the fix that matters. (b) Mention it in prose only - rejected: `TODO`-style prose is not tracked, and the attention view would never see it, so the defect would be rediscovered rather than scheduled. | the driven `{'scanned_files': 0, 'findings': 2}`; `scan_working_tree`'s `-> list[Finding]` signature; item `c0ppo0` filed and resolvable | yes |
