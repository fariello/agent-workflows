# Review findings: plan m47znv

- Subject-Id: m47znv
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file in `pending/` was committed and byte-identical to the
lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review, and
reports `clean` again at `author` and `review-finalize` after revision. The plan is `- Kind: child`, so
the `IPD-S407` orchestrator child-row check does not apply.

THIS IS A SMALL PLAN WITH AN UNUSUALLY GOOD DESIGN ARGUMENT, AND ITS CENTRAL JUDGEMENT IS RIGHT. The
decision that distinguishes it from a careless version of the same work is F-3: the nudge must NOT reuse
Order 01's liveness predicate, because that predicate returns NOT HELD for a lane whose run has ended,
which is precisely the case the nudge serves. An implementation that took the obvious reuse would pass
every test a careless author would write and be silent exactly when wanted. The plan identifies that,
forbids the reuse in E-02, pins the distinction with a driven case in V-02, names it again in the gate,
and even anticipates that the tempting test ("assert the helper does not import the predicate") is a
forbidden structure pin and replaces it with the behavioral equivalent. That is the standard this
repository asks for. The never-a-refusal fence is equally well argued: D1's "NUDGE, never a refusal" is
quoted, the reason a lane's EXISTENCE is a proxy rather than the real condition is stated, and the gate
says plainly that a refusal here would be "the location rule Order 02 deleted, in a politer costume".

EVERY MEASURABLE FACT EXCEPT ONE REPRODUCES. F-1: the runner does finalize in the lane, and
`driver_finalize`'s comment does call that site "THE primary lane-shadowed site" with `cwd` kept there
deliberately "because finalize must resolve paths against the tree it is finalizing". F-2: all five lane
helpers exist (`WORKTREES_SUBDIR = ".aw/worktrees"`, `OWNERS_SUBDIR`, `lane_branch_name`,
`lane_id_from_branch`, `read_lane_owner`). F-5: `nested_aw_message` keeps both streams for the quoted
reason and strips exactly `_CHECKOUT_PIN_NOTICE_PREFIX = "aw: invoked in checkout "`. F-6: both handlers
branch on `ctx.is_agent or ctx.is_json`. F-7: `lane_branch_name`'s prohibition on hand-reconstruction and
`lane_id_from_branch` as the sanctioned inverse both read as quoted. F-8's reasoning is sound.

BUT THE PLAN'S OUTPUT FENCE DOES NOT COVER HALF THE SURFACE IT PROTECTS. That is PR-001 and it is the
one real defect. The plan's whole channel argument is that the advisory is safe because it goes to stderr
and is "suppressed entirely in `--agent` and `--json` modes", and OQ-02 leans on the stronger claim that
it is therefore "already silent in every non-interactive consumer". Measured, `runner_shared.driver_begin`
builds `["ipd", "begin", id6, "--actor", actor, "--dir", str(repo)]` and passes NEITHER flag, so
`result_types.select_output` resolves `OutputMode.HUMAN`; its docstring is explicit that a piped or
redirected invocation still emits human-readable text and that `--agent` is the only way to get
`aw.agent/v1`. `driver_begin` then captures `stderr=subprocess.PIPE` and returns
`nested_aw_message(result.stdout, result.stderr)`, which puts STDERR FIRST and strips exactly one prefix.
So a human-mode stderr line from `begin` is captured by the driver and prepended to the begin diagnostic.
`driver_finalize` is different and is genuinely fenced: it DOES request `--json`, recorded in
`runner_shared`'s own comment ("`driver_finalize` now requests `--json` (qo9khm E-01)"). The plan treated
the two verbs as symmetric and they are not.

I checked how far the damage reaches before rating it, because two accidents limit it. `begin_msg` is
consumed ONLY on the `begin_rc != 0` branch (measured at `attempt["begin_refused"]`,
`item["begin_refusal"]`, the event `detail` and the printed line, all inside that branch), so on the
success path the string is discarded; and `driver_begin` runs with `cwd=str(repo)`, the MAIN tree, with
the lane allocated only AFTER begin returns, so on a FIRST attempt no lane exists and the nudge should
not fire. Neither is a fence this plan controls. A RECOVERY or second attempt re-runs `driver_begin` while
the prior attempt's lane is still on disk, which is exactly the nudge's firing condition, and if begin
then refuses for an unrelated reason the recorded refusal reason leads with the nudge. That is not a
hypothetical class of bug: it is the specific defect `nested_aw_message` exists to fix, measured on
run-20260925T174509Z-636951, where "the recorded refusal reason was the notice ... and the real refusal
was lost, so the run's remedy pointed at E/V bookkeeping that was already complete". A plan whose entire
promise is "this cannot affect an outcome" must not reintroduce it. Rated BLOCKER for that reason rather
than for breadth. The fix is cheap and uses the mechanism the plan already cites: give the nudge a fixed
prefix and add it to the set `nested_aw_message` strips, which keeps both verbs covered as D1 asks and
makes a stripping rule rather than a mode guess the thing that protects the driver. I required a recorded
choice among three shapes rather than mandating one, and I pulled `runner_shared.py` into
`- Scope-Paths:` because the preferred shape edits it.

PR-002 is a correction that matters more than it looks. F-4 claimed a new stdout line "could land inside
a parsed payload". Measured, `parse_finalize_payload` is a deliberately TOLERANT parser: it locates a
balanced top-level `{...}` rather than calling `json.loads` on the stream, explicitly because "the success
path prefixes stdout with `plans index --check: clean`", and it returns `None` and never raises on
unparseable input. So the stated hazard does not exist. The CONCLUSION (use stderr) is still right, on the
`--json` byte-identity requirement and the refusal contract, and I kept it. I fixed the reason because a
false reason is load-bearing in the wrong direction here: a future author who checks the claim, finds the
parser tolerant, and concludes the constraint was imaginary could move the line to stdout, where it WOULD
break the refusal contract. The plan also made this mutation "matter most" in its validation section, so
the priority was pointed at the weaker risk; the `driver_begin` mutation now holds that place.

PR-003: the scope check asserted that `runner_shared.py` needs no declaration because "the runner already
finalizes in the lane (F-1) and will therefore never see the nudge". F-1 is about where finalize RUNS and
says nothing about begin's output capture, so the inference is invalid and the conclusion is false for
begin. Corrected, and the path declared. Separately and in the plan's favour, I RESOLVED a question the
plan left for the executor: the `aw set executed` deferral row hoped the coverage would be free through
delegation, and it is. `status_set._delegate_plan_executed_to_finalize` routes a plan-to-`executed`
request into `ipd_lifecycle.finalize` and records that it "delegates transparently (OQ-03) rather than
refusing-and-redirecting", so a nudge emitted inside `finalize` covers both `aw set` spellings. V-03 still
requires the executor to confirm it, but the expected answer is now known rather than open.

BOTH OPEN QUESTIONS WERE ADDRESSED TO THE REVIEWER, SO I ANSWERED THEM, and both are recorded as
decisions below. OQ-01 (fire on a feature branch too) I RATIFIED as the plan had it, main-checkout only,
on the plan's own sound reasoning that a feature branch already has the reviewed-merge property plus D1's
wording. OQ-02 (a suppression flag) I also ratified as NO, but its reasoning had to be repaired first:
its premise that the line is "already silent in every non-interactive consumer" is exactly what PR-001
shows is false today, so the answer is correct only AFTER E-03's fix lands. I noted that, and rejected
the `AW_NONINTERACTIVE` alternative on the recorded 2026-09-10 maintainer retraction (ttyflags `yaxr4i`
OQ-01) that removed precisely this kind of interactivity-to-output-mode coupling.

ONE THING I DELIBERATELY DID NOT CHANGE, recorded so it is not mistaken for an oversight. The plan's six
Carrier-Declined deferral rows are all honest and I left them: each declines with a reason grounded in a
maintainer decision (D1), in another plan's ownership, or in a rejected design, and none parks work. The
row declining "make the preferred shape the default by moving the transition automatically" is
particularly well judged, since silently transitioning in a tree the operator did not invoke in would be
the surprising side effect P15 argues against.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | A (correctness) / C (operability) | `runner_shared.driver_begin`'s argv `["ipd", "begin", id6, "--actor", actor, "--dir", str(repo)]` (no `--agent`, no `--json`); `result_types.select_output` docstring ("a piped or redirected invocation still emits human-readable text, and `--agent` is the only way to get `aw.agent/v1` JSONL"); `driver_begin`'s `stderr=subprocess.PIPE` and `return result.returncode, nested_aw_message(result.stdout, result.stderr)`; `nested_aw_message` stripping only `_CHECKOUT_PIN_NOTICE_PREFIX = "aw: invoked in checkout "`; contrast `runner_shared`'s comment "`driver_finalize` now requests `--json` (qo9khm E-01)"; the measured precedent run-20260925T174509Z-636951 where "the real refusal was lost" | **THE `--agent`/`--json` SUPPRESSION DOES NOT FENCE `begin`, SO THE NUDGE CAN POLLUTE A BEGIN REFUSAL DIAGNOSTIC.** The plan's channel argument assumes both verbs are reached by machine consumers in structured mode; only finalize is. `driver_begin` runs in HUMAN mode and feeds stderr, stderr-first, into `nested_aw_message`. On a recovery attempt the prior lane exists (the nudge's firing condition) and an unrelated begin refusal is then recorded led by the nudge: the exact defect `nested_aw_message` was written to fix, in a plan whose whole promise is that it cannot affect an outcome. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now measures the asymmetry, states why the blast radius is limited but not fenced (`begin_msg` consumed only on refusal; the lane allocated after begin on a first attempt), and REQUIRES one of three recorded fixes, preferring a fixed prefix added to the set `nested_aw_message` strips. `agent_workflows/runner_shared.py` added to `- Scope-Paths:`, with a `--scope-ack` route stated if a shape that does not touch it is chosen. Fact 4 and the gate's STDERR paragraph swept. E-04 gains a diagnostic-integrity arm, V-03 the driven `driver_begin` evidence, and the validation section a fifth mutation that is now the one that "matters most". New F-9. |
| PR-002 | MEDIUM | IN-SCOPE | F (honest documentation) / D (anti-regression) | `runner_shared.parse_finalize_payload` docstring: "Tolerant parser (E-01): Locates a balanced top-level `{...}` object instead of calling `json.loads` on the whole stream, because the success path prefixes stdout with `plans index --check: clean` (F-05) ... Returns `None` (never raises) on unparseable, empty, or absent payloads" | **F-4'S STATED HAZARD DOES NOT EXIST, AND THE FALSE REASON POINTS A FUTURE AUTHOR THE WRONG WAY.** The plan justifies stderr partly by claiming a stdout line "could land inside a parsed payload"; the parser is deliberately tolerant of exactly such prose and never raises. The conclusion is right for other reasons, but an author who checks this claim, finds it false, and concludes the constraint was imaginary could move the line to stdout, where it would break the refusal contract. The plan also ranked the stdout mutation as the one that "matters most", pointing validation effort at the weaker risk. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-4 corrected in place with the measurement, explicitly keeping the stderr CONCLUSION while replacing its reason with the `--json` byte-identity requirement (F-6) and the refusal contract (F-5). Fact 4 carries the same correction, and the gate's STDERR paragraph now warns against letting the corrected reason tempt a move to stdout. The validation section's mutation priority is reassigned to the `driver_begin` arm. |
| PR-003 | LOW | IN-SCOPE | F / G (executability) | Plan scope check: "the runner already finalizes in the lane (F-1) and will therefore never see the nudge, so nothing changes there"; refuted by PR-001's measurement. Separately `status_set._delegate_plan_executed_to_finalize` docstring: "Route a plan -> `executed` `aw set`/`ipd set` request into the gated `aw ipd finalize` ... delegates transparently (OQ-03)" | **AN UNDER-SCOPE CLAIM RESTS ON AN INVALID INFERENCE, AND A QUESTION LEFT TO THE EXECUTOR IS ANSWERABLE FROM THE TREE.** F-1 concerns where finalize RUNS and cannot support a conclusion about begin's output capture; the claim is false for begin. Separately, the `aw set executed` deferral row asked the executor to confirm whether delegation makes the coverage free, which the tree already answers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The scope check now records the correction explicitly rather than silently dropping the claim, and declares `runner_shared.py` with the conditional `--scope-ack` route. The `aw set executed` deferral row now records the measured answer (the coverage IS free through the delegation), with V-03 still requiring confirmation. New F-10. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | `driver_begin` runs in HUMAN mode and captures stderr, so the nudge can pollute a begin refusal diagnostic. What fixes it? | Require a RECORDED choice among three shapes, preferring (a): give the nudge a fixed prefix and add it to the set `nested_aw_message` strips. | (b) Suppress in `begin` when not attached to a terminal: REJECTED as the primary shape because `select_output` deliberately does not consult `isatty` for mode and the maintainer RETRACTED that policy on 2026-09-10 (ttyflags `yaxr4i` OQ-01), so adding the coupling here would contradict a recorded decision. (c) Emit from `finalize` only: PERMITTED and defensible, since D1's wording is about finalizing and a first-attempt begin has no lane yet, but it drops half of what D1 asks for. (d) Leave it, since `begin_msg` is read only on the refusal branch: REJECTED, the refusal branch is exactly where a polluted reason does harm, and a recovery attempt reaches it with a lane present. | `driver_begin`'s argv and `nested_aw_message` call measured; `select_output`'s docstring and the recorded retraction; the run-20260925T174509Z-636951 precedent recorded in `nested_aw_message`'s own docstring; `driver_finalize`'s `--json` request as the contrast. | yes |
| D-2 | F-4's stated hazard is false. Correct the reason, or drop the fact? | Correct it in place, keeping the stderr conclusion and replacing the reason. | Dropping F-4 entirely: REJECTED, stdout IS a contract surface and the fact is doing real work; only its mechanism was wrong. Leaving it as written: REJECTED, a false justification is worse than none here because checking it suggests the constraint is imaginary, which licenses the one move that would actually break something. | `parse_finalize_payload`'s docstring stating tolerance and the `plans index --check: clean` prefix as its reason; F-6's `--json` byte-identity requirement, which is a real and sufficient reason. | yes |
| D-3 | OQ-01: should the nudge fire on a feature branch, not only in main? | Main checkout only, RATIFYING the plan's reading. | Fire anywhere outside the plan's own lane: REJECTED, though explicitly overrulable. On a feature branch the plan's move already travels with the code in one reviewed merge, so the property the nudge protects already holds; the residual case (a feature branch other than the lane's) would need a message naming two branches to be actionable, which is worse than silence for a one-line advisory. | The plan's own argument, ratified rather than replaced; backlog `dvonrn` D1's wording describing the nudge only for "begin/finalize runs in main and a lane or feature branch for the same plan exists". | yes |
| D-4 | OQ-02: should the advisory be suppressible? | NO, ratifying the answer, but after REPAIRING its premise. | A suppression flag: REJECTED, its only function would be hiding one line from its intended reader, a configuration surface for an unexpressed need (P6). Honoring `AW_NONINTERACTIVE` instead: REJECTED, it couples an advisory to an interactivity signal `select_output` deliberately does not consult for mode, which the 2026-09-10 retraction removed. NOTE the plan's premise that the line is "already silent in every non-interactive consumer" is FALSE today (PR-001) and the answer is correct only once E-03's fix lands; that is now stated in the question. | P6 on unexpressed needs; the ttyflags `yaxr4i` OQ-01 retraction; PR-001's measurement of `driver_begin`'s human mode. | yes |
| D-5 | Verdict and readiness, given one BLOCKER and two lesser findings all now fixed and no blocking open questions. | `APPROVE WITH REVISIONS APPLIED` / `go-pending-approval`. | `REJECT - NEEDS REPLAN`: REJECTED, the design is sound and its central judgement (not reusing the liveness predicate) is right; the BLOCKER was a missed asymmetry in one output path, repairable by one recorded choice plus one declared path, which is bounded editing. `REVIEWED - OPEN QUESTIONS`: REJECTED, both OQs are now `resolved`. Bare `NO-GO`: REJECTED, the workflow reserves it for genuine not-ready conditions and a reviewed clean plan awaiting sign-off is `GO - PENDING HUMAN APPROVAL`. | Workflow readiness vocabulary; zero findings left OPEN or DEFERRED at or above the default `HIGH` gate threshold, so no escalation to a `Blocking: yes` question is owed; `aw ipd lint` clean at `author` and `review-finalize`. | yes |
