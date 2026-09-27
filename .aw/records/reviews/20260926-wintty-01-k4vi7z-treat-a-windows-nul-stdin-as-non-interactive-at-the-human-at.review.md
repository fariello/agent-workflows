# Review findings: plan k4vi7z

- Subject-Id: k4vi7z
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `48e8c097` in a lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize` conforms after. No
pre-review snapshot was needed: the plan was committed and unmodified, and the lane-input copy at
`.aw/state/lane-inputs/rev-5/` is byte-identical to the tracked file (`diff` reported no difference).

THE APPROACH IS RIGHT AND I DID NOT SECOND-GUESS IT. One helper, reusing the probe that already exists
in `engine.is_interactive_session`, applied at exactly the sites where a false verdict grants authority,
with the prompt-only sites left alone. Every one of the plan's seven original findings re-verified:
`specs.run_set`'s floor (`agent_workflows/specs.py:636-652`), `status_set`'s fork of it
(`agent_workflows/status_set.py:644-661`), `git_commit_helper._is_interactive`
(`agent_workflows/git_commit_helper.py:302-315`), the probe to reuse
(`agent_workflows/engine.py:1940-1958`), and the `_NotATty` wrapper that masks the bug in the suite
(`tests/__init__.py:78-93`). The `cli.py` count had drifted 21 -> 22 between authoring and review, which
is why F-7 is now recorded as context rather than as a number anything asserts on.

WHAT I DID INSTEAD OF RE-READING THE PLAN'S PROSE: I drove the real commands, and that is where all six
findings came from.

FIRST, I measured how bad the `specs`/`status_set` half actually is, because the plan described the
mechanism without the consequence. Driving the real CLI with stdin on a `pty.openpty()` and stdout/stderr
PIPED (the driver shape, no human anywhere):

```text
rc= 0
STDOUT: aw specs set: .../specs/approved/20260926-aa1111-01-aa1111-probe.spec.md -> approved
LANDED IN: approved
['- Status: approved', '- 2026-09-26 approved (aw specs, --by-human): driver-spawned, no human involved']
```

So the auto-attestation does not merely skip a gate: it WRITES a `--by-human` provenance line attributing
an approval to a human who was never present, into the state that licenses execution. That is now F-10 and
it is carried into the CHANGELOG wording, because "was treated as an interactive session" undersells it.

SECOND, and the finding I consider the most valuable of this review, I found a LARGER hole of the same
class that this plan does not close and had not recorded. `git_commit_helper._is_interactive` keys on stdin
alone, and six of the seven in-repo `offer_commit` callers pass no `interactive=` override. Same pty-stdin,
piped-stdout shape, ON LINUX:

```text
stdin isatty: True stdout isatty: False
The following path-scoped changes are ready to commit:
  mine.txt
Commit these path-scoped changes? [Y/n]
TIMED OUT (blocked on input()) after 20s
```

That is the exact predicate error `ipd_lifecycle.run_finalize`'s ttywedge note records as a measured 1h49m
wedge, and this repository already has the correct fence in three places
(`artifact_adopt.leak_gate_is_interactive`, `runner_stop.interrupt_menu_is_safe`, and the finalize site
itself), all requiring the OUTPUT stream to be a TTY too and honoring `AW_NONINTERACTIVE`/`CI`. Fixing it
here would turn a Windows-only bugfix into a cross-platform interactivity change at six call sites, which
is outside the maintainer-approved scope, so the plan now FILES it (E-09) as a `bug` carrying
`Blocks-Release: next` and records the reproduction. The helper's docstring must also state the honest
limit and name the stronger predicate, so the new helper does not read as canonical and invite a future
caller to weaken one of those three fences down to it.

THIRD, V-02 was vacuous twice over and it was E-02's only coverage. `pytest tests/test_installer.py -k
interactive` deselects all 120 tests and exits 0 having run nothing:

```text
NOTE: 120 tests were deselected by -m/-k and did not run
120 deselected in 0.14s
```

and `tests/test_installer.py:59` is `pytestmark = pytest.mark.slow`, which `pyproject.toml`'s `addopts`
`-m 'not slow'` excludes from the bare suite E-08 uses as its gate. That module is the ONLY one exercising
`engine.is_interactive_session` (it patches it at `tests/test_installer.py:1432`), so as written E-02 had
no validation at all. The covering test is
`OverwritePromptTests::test_every_prompt_answer_has_the_right_effect_and_exit_code`, which passes when the
marker is cleared (`1 passed, 119 deselected in 2.71s`). V-02 and E-08 now say so.

FOURTH, I checked the plan's spec-sync claim rather than accepting it, and it survives for a better reason
than the plan gave. The governing spec `20260815-0151-01-honest-human-approval-attestation` is
`implemented` and its G1 REQUIRES removing the `isatty()` requirement from the human-only path, so a
careless reading makes this plan look like a partial revert. It is not: the auto-attestation branch this
plan narrows was added LATER, by commit `cf7dceea` (2026-09-04, "auto-attest human approval on interactive
TTY without prompt"), and the spec does not describe it at all. The spec-sync section now records that
provenance, which is what makes "no `.spec.md` is amended" a checkable claim instead of an assertion.

FIFTH, I verified the two prescribed-but-unproven mechanisms so the executor does not spend a cycle
discovering they work. The `mock.patch.object(ctypes, "windll", ..., create=True)` shape produces
False/True/True across the three platform cases against a scratch copy of the proposed helper body, and
`script -q -c ... /dev/null` does yield a real tty here (`True`) while `< /dev/null` yields `False`. I also
confirmed `term.py` is a legal import target for `git_commit_helper`: its only internal import is
`lifecycle_style`, itself stdlib-only, so the leaf discipline that module's docstring insists on is intact.

SIXTH, on the deferral I did NOT overturn. The ~20 prompt-only `cli.py` sites stay out of scope, and I
spot-checked the premise rather than trusting it: `cli._confirm` guards `input()` with `except EOFError`,
`cli.main` carries a top-level `except EOFError` returning 130, and of the twelve `input()` call sites in
`cli.py` the three without a local guard are covered (one is a docstring, one is guarded four lines later,
one carries an inline comment deferring to `main()`). So an EOF at a prompt-only site declines or exits,
it does not hang. That evidence is now in the Deferred section, which converts a maintainer-authority
claim into a checkable one.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | C. Architecture and operability / B. Security | `agent_workflows/git_commit_helper.py:302-315` (`_is_interactive`, stdin only); `offer_commit` callers `cli.py:6448`, `plans_archive.py:295`, `research_archive.py:554`, `specs.py:888`, `status_set.py:1565`, `work_cmd.py:684` all `interactive=None`; measured on LINUX with pty stdin + piped stdout: prompt printed into the pipe, blocked on `input()` until a 20s timeout; the stronger fence exists at `artifact_adopt.leak_gate_is_interactive`, `runner_stop.interrupt_menu_is_safe`, `ipd_lifecycle.run_finalize` (ttywedge g40w37, a measured 1h49m wedge) | **THE SAME CLASS OF BUG IS LIVE ON EVERY PLATFORM AND THE PLAN WOULD HAVE SHIPPED WITHOUT RECORDING IT.** E-05 makes `_is_interactive` require a console on win32, which reads as "the commit-prompt hazard is handled". It is not: with stdin inherited and stdout piped, a shape the runners deliberately defend against elsewhere, the prompt still goes into a pipe and blocks. Three sites in this repository already use the correct both-streams-plus-`AW_NONINTERACTIVE` fence, so the knowledge exists and this site simply does not consume it. Left unrecorded, a reader of the executed plan would reasonably conclude the prompt gate was fixed, and the next person to hit the hang would have to re-measure it from scratch. | C:Low; U:Low; S:Low; F:Low for the CHOSEN fix (file a carrier + state the limit). Fixing it in this plan would be Medium-High: a cross-platform behavior change at six call sites, turning a Windows-only bugfix into an interactivity redesign, and outside the maintainer-approved scope. | FIXED | Added E-09: file ONE backlog item (`--work-kind bug --priority medium --blocks-release next`) with the measured reproduction pasted in, and write its minted id6 into the new F-8 row. Added V-09 demanding the item's path and front matter as evidence. Added a `Carrier-Declined` explaining why `- Carrier:` cannot name it (the id6 is minted at execution). E-01's docstring requirement now includes the honest limit naming `artifact_adopt.leak_gate_is_interactive`, and the gate carries a "WHAT THIS DOES NOT FIX" paragraph. |
| PR-002 | HIGH | IN-SCOPE | E. Testing and verification | Measured: `python3 -m pytest tests/test_installer.py -o addopts="" -q -k interactive` -> `120 deselected in 0.14s`, exit 0, nothing run; `tests/test_installer.py:59` `pytestmark = pytest.mark.slow`; `pyproject.toml` `addopts` `-m 'not slow'`; `tests/test_installer.py:1432` patches `agent_workflows.engine.is_interactive_session`; the real covering test is `OverwritePromptTests::test_every_prompt_answer_has_the_right_effect_and_exit_code` (`1 passed, 119 deselected`) | **E-02'S ONLY VALIDATION RAN ZERO TESTS AND EXITED 0.** `-k interactive` matches no test id in that module, so V-02 would have been marked satisfied by a green exit code covering nothing. The module is additionally slow-marked, so E-08's bare suite never runs it either: E-02 (replacing the inline win32 probe in the one function the installer's overwrite prompt depends on) had NO coverage in either validation path. This is the vacuous-evidence shape the honesty rule exists to prevent, and it would have passed every structural check. | C:Low; U:Low; S:Low; F:Medium (an unvalidated edit to the installer's interactivity gate); the FIX is Low | FIXED | V-02 now forbids `-k interactive` with the measured reason, prescribes `python3 -m pytest tests/test_installer.py -o addopts="" -q`, and names the specific covering test that must appear in the pasted output. E-08 additionally requires that slow-marked module to be run beside the bare suite, with the exclusion explained. Recorded as F-9 in the plan and in "Project conventions discovered". |
| PR-003 | MEDIUM | UNDER-SCOPE | D. Anti-regression / E. Testing | Plan's own F-6; `tests/test_specs_verbs.py::test_approved_requires_human_and_is_refused_non_tty` third block (`stdin.isatty.return_value = True`, asserts rc 0); `tests/test_status_set.py::test_spec_approved_interactive_confirmation` (`patch("sys.stdin.isatty", return_value=True)`, asserts rc 0); neither file was in `- Scope-Paths:` | **A KNOWN BREAKAGE WAS DEFERRED TO A POST-PUSH DISCOVERY.** F-6 correctly identified that both tests would start failing on `windows-latest` (they force `isatty()` True and then reach the real `GetConsoleMode`, which fails on a runner), but assigned the repair to E-08 as a contingency and left both files undeclared. That inverts the order: the executor finishes, the maintainer pushes, CI goes red, and the fix arrives as an unplanned hotfix to files the plan never declared, with the scope reconciliation done after the fact. The repair is known NOW and is three lines. | C:Low; U:Low; S:Low; F:Low | FIXED | Added E-11 owning the change explicitly (patch `agent_workflows.term.stdin_is_interactive` alongside the existing `isatty` patch, preserving every assertion), added V-11 requiring both diffs plus a passing run, declared both test files in `- Scope-Paths:`, rewrote F-6 to record that it is now planned rather than contingent, and noted the `--scope-ack` case if only one file needs the edit. |
| PR-004 | MEDIUM | IN-SCOPE | G. Plan executability (a gate blocking on a forbidden act) | V-08 as written: "an explicit statement that Windows CI has not yet run because the branch is unpushed, in which case this V-item stays `pending` and the plan is not finalized"; the plan's own gate and the repository execution contract: the executor "never pushes", and in a managed lane the runner owns the terminal transition | **FINALIZATION WAS CONDITIONED ON AN ACT THE EXECUTOR IS FORBIDDEN TO PERFORM.** Windows CI needs a push; the executor may not push; therefore a fully completed, fully validated plan would sit in `pending/` indefinitely waiting for the maintainer, with all its work unintegrated. That is precisely the stranding failure the corrected element-5 lifecycle contract exists to prevent, and it is worse than the hole it was guarding: an unrun CI job is a KNOWN, recorded gap, while a stranded plan is invisible work. | C:Low; U:Low; S:Low; F:Medium (stranded completed work); the FIX is Low | FIXED | Added OQ-02 resolving it from the repository's own contract (non-blocking, resolved, with a `Carrier-Declined` recording that nothing is left outstanding). V-08 now requires the local evidence plus an explicit statement of the Windows CI position in one of exactly two forms, names the win32 `GetConsoleMode` call as the KNOWN HOLE, and states that the unpushed form is a legitimate pass that must not be dressed up as green. E-08 and the gate's "WHAT A HUMAN IS APPROVING" paragraph match. The gate's lifecycle sentence also now states the CONDITIONAL runner/executor ownership instead of instructing the executor unconditionally. |
| PR-005 | MEDIUM | IN-SCOPE | G. Plan executability (right-sizing and conceptual density) | E-06 as written bundled five tests across three surfaces: the helper's own verdict, `specs.run_set`'s refusal, and `git_commit_helper`'s prompt suppression, plus (via F-6) an unowned edit to two existing test files; V-06 demanded "5 passed" as one evidence blob | **ONE E-ITEM CARRIED THREE INDEPENDENT TEST-SURFACES AND FOUR DISTINCT DELIVERABLES.** The count-based size lint passes, which is exactly why the right-sizing rubric is a separate semantic judgement: the helper-level cases need only E-01, the site-level cases need E-03 and E-05 and a red-run against the base commit to be non-vacuous, and the existing-test repair needs E-03/E-04 and touches two other files. Bundled, a partial execution is invisible, and the single V-item cannot distinguish "the helper's arithmetic is right" from "the security gate actually refuses". | C:Low; U:Low; S:Low; F:Low | FIXED | Split into E-06 (three helper-level tests), E-10 (the two site-level tests that prove the fix, with the `input`-raises patch called out as the load-bearing half) and E-11 (PR-003's repair), each with its own V-item. V-10 additionally prescribes the base-commit RED RUN in a throwaway detached worktree, names the gitignored paths that are safe for it (`.gitignore:73`, `.gitignore:42`), requires (d)/(e) to fail on the OUTCOME rather than on an import error, and forbids both an in-place revert and `git stash` with the shared-checkout reason. Cohesion rationale records the split. |
| PR-006 | LOW | IN-SCOPE | E. Testing / F. Honest documentation | V-04 as written presented a `< /dev/null` refusal as evidence for E-04; measured at review against UNMODIFIED code: that command already exits 1 with `aw specs set: reviewed -> approved is a human-only transition; pass --by-human ...` and leaves the file byte-identical. Separately, V-07's `grep -P '[\x{2013}\x{2014}]'` exits 1 on the passing (no-match) case | **A REGRESSION GUARD WAS PRESENTED AS PROOF OF THE FIX, AND ONE EVIDENCE COMMAND'S PASSING EXIT CODE LOOKS LIKE A FAILURE.** V-04's command cannot distinguish fixed from unfixed code on POSIX (it passes on both), so pasting it without saying so overstates what the evidence proves; the plan's honesty rule makes that a defect rather than a nicety. V-07's `grep` exiting 1 on success invites an executor to "fix" a passing check or to report it as failed. | C:Low; U:Low; S:Low; F:Low | FIXED | V-04 now states explicitly that it is a POSIX REGRESSION GUARD, records the measured pre-fix output proving it already passes, and requires that caveat beside the paste. V-07 records that `rc=1` from `grep` is the PASSING case, verified at review. V-01 additionally requires the helper's docstring to be pasted so the three required statements are checkable, and offers a `pty.openpty()` substitute if the sandbox refuses `script`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The `git_commit_helper` prompt hazard (PR-001) is real on every platform, not just Windows. Widen this plan to fix it, file a carrier, or say nothing? | FILE A CARRIER (E-09: one `bug` backlog item carrying `Blocks-Release: next`, with the measured reproduction), and state the limit in the helper docstring and the gate. | (a) Widen the plan to fix it: rejected. It changes behavior at six `offer_commit` call sites on all platforms, none of which is in `- Scope-Paths:`, converting a maintainer-approved narrow Windows fix into a cross-platform interactivity redesign; the blast radius is the whole self-commit path. (b) Say nothing: rejected outright. The plan touches this exact function, so a reader of the executed plan would conclude the prompt gate was fixed, and the AGENTS.md rule that a live user-perceptible defect must carry a release gate would be silently unmet. (c) Fix only the `AW_NONINTERACTIVE` half as a cheap partial: rejected, a half-fence is harder to reason about than none and would make the remaining stdout hole look addressed. | Measured reproduction (pty stdin + piped stdout, prompt into pipe, blocked until a 20s timeout); `artifact_adopt.leak_gate_is_interactive` and `runner_stop.interrupt_menu_is_safe` docstrings both stating stdin alone is not consent; `ipd_lifecycle.run_finalize`'s ttywedge note recording a measured 1h49m wedge; six of seven `offer_commit` callers passing `interactive=None`; AGENTS.md "every live bug gates the next release" plus the user-perceptible-impact test | yes |
| D-2 | `- Carrier:` requires a bare id6, but E-09 MINTS the carrier during execution, so no id6 exists at authoring time. How is the obligation recorded without either a dangling reference or a silent drop? | `- Carrier-Declined:` whose text states that the carrier is minted by this plan, names the verb and flags that mint it, and points at V-09 (evidence) and the F-8 row (where the id6 lands). | (a) Write `- Carrier:` with prose: ATTEMPTED and REFUSED by the checker, which reported `expected a bare 6-char id6` and raised `check.ipd-uncarried-obligation` at `error`; that is what surfaced this question. (b) Mint the backlog item now, during the review: rejected. A review must not create durable work items on its own authority, and the plan-review contract limits this workflow to planning documents. (c) Leave the deferral with no carrier field: rejected, `error`-severity finding and the obligation vanishes from `aw attention` once the plan reaches `executed`. | `check_engine.evaluate_durable_carrier` driven directly before and after the edit (1 finding -> `[]`); the rule's own recovery text; plan-review memory kernel item 1 ("Review plans only") | yes |
| D-3 | Does narrowing the auto-attestation branch contradict implemented spec `20260815-0151-01-honest-human-approval-attestation`, whose G1 removed the `isatty()` requirement from the human-only path? | NO, and record WHY in the spec-sync section: the branch being narrowed was added later by commit `cf7dceea` and the spec does not describe it. | (a) Amend the spec: rejected, nothing in it becomes false; G1 is about `--by-human` working WITHOUT a TTY, which is untouched, and G2's "succeeds iff the flag is passed" shape is if anything better honored after this change. (b) Leave the plan's original bare assertion that no spec is amended: rejected, it was true but uncheckable, and a future reader comparing G1 against this diff would reasonably suspect a partial revert. | Spec G1 ("honored regardless of TTY ... Remove the `sys.stdin.isatty()` requirement") and G2; `git log -L` on the authority floor showing `cf7dceea` (2026-09-04) introduced the auto-attest branch and `73452a6e` (2026-08-28) the prompt before it; spec Date 2026-08-15 | yes |
| D-4 | Should the ~20 prompt-only `cli.py` sites stay deferred on the maintainer's narrow-scope ruling alone? | YES, but VERIFY the premise and record the evidence rather than resting on authority. | (a) Widen scope to include them: rejected, explicitly maintainer-approved as out of scope and the sites grant no authority. (b) Accept the deferral as written: rejected as insufficient. The stated reason ("a prompt reads EOF and falls back") is a behavioral CLAIM about 20 sites, and the plan had not checked it; if any site lacked an EOF guard it would hang, which is exactly PR-001's failure mode. | Spot-checked at review: `cli._confirm` (`cli.py:6393-6403`) `except EOFError: return False`; `cli.main` top-level `except EOFError` -> 130 (`cli.py:14860-14862`); nine of twelve `input()` sites carry a local guard and the three without are covered (docstring / guarded four lines later / inline comment deferring to `main()`) | yes |
| D-5 | V-08 as written blocked finalization on an unpushed Windows CI job. Resolve it, or ask the maintainer whether to hold the plan? | RESOLVE IT from the repository's own contract: non-blocking, recorded as a known hole. | (a) Ask the maintainer: rejected, "do not ask the human what the repository already answers"; the execution contract states the executor never pushes and the corrected element-5 contract exists precisely to stop completed work being stranded. (b) Keep the block: rejected, it guarantees the stranding failure. (c) Drop the Windows CI requirement entirely: rejected, it is the ONLY real proof of the win32 `GetConsoleMode` call, so it must be recorded as an outstanding hole, not deleted. | AGENTS.md execution contract ("never push"); the CHANGELOG entry on the corrected element-5 contract describing an agent that completed all work being rejected and stranding its changes; `.github/workflows/tests.yml` matrix including `windows-latest` | yes |

### Deferred and open

- (none DEFERRED). All six findings were FIXED in place. No finding was left `OPEN` or `DEFERRED`, so
  nothing is owed an escalated `- Blocking: yes` question under the gate threshold rule (the repository
  sets no `review_findings_gate` in `.aw/config/project.json`, so the default `HIGH` applies; PR-001 and
  PR-002 are `HIGH` and both are FIXED).
- No `Reversible: no` decision was taken, so no escalation to the maintainer is owed. D-1 comes closest,
  since it leaves a live release-gating bug unfixed, but it is reversible in the sense that matters: the
  obligation is durably recorded as a backlog item rather than discarded, and a maintainer who wants it
  fixed sooner can simply prioritize that item.
- The plan's two open questions are both `resolved` and both `Blocking: no`.

HONEST LIMITS, stated because they bound what this round proves. Every measurement above was made ON
LINUX. I did NOT run anything on Windows, so the claim that `NUL` reports `isatty()` True there rests on
the backlog item's field report, on the `tests/__init__.py:79-83` comment recording it as observed on the
Windows CI runner, and on the pre-existing win32 branch in `engine.is_interactive_session` that was
written for it, NOT on a measurement of mine. The win32 half of the new helper will be proven only by the
`windows-latest` job, which is exactly why V-08 records that as a known hole instead of claiming coverage.
I verified the three `mock.patch.object(ctypes, "windll", ...)` shapes against a SCRATCH COPY of the
proposed helper body, not against the shipped helper, which does not exist yet; that proves the patch
mechanism, not the final code. I did not write any test, apply any product edit, or run the bare suite for
this plan: E-01 through E-11 and V-01 through V-11 remain the executor's work and their evidence. My
`git_commit_helper` reproduction used a 20s timeout and a `pty`, which is the driver shape but not a real
driver; the finding is that the prompt is PRINTED and BLOCKS, and that is what the paste shows. Finally,
the F-8 row deliberately ships with the placeholder `<id6 pending E-09>`: I could not mint the item without
exceeding this workflow's authority, so if a future reader finds that placeholder on an EXECUTED plan,
E-09 was skipped and that is the defect to chase.
