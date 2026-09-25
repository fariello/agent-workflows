# Review: Pause for explicit acknowledgement before a run that declares spec edits

- Subject-Id: 1g4i1t
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `4e91bb1b`. The target plan was committed and unchanged, so the pre-review snapshot was
correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0) BEFORE review and again at `--phase review-finalize` after the revisions.

THE PLAN IS WELL RESEARCHED AND ITS CENTRAL DESIGN IS RIGHT. I verified every mechanism claim:
`announce_run_order` really does compute the impacts and print them inside an `except Exception` that
only prints a failure line, with a comment stating it "changes what the operator is TOLD, never what a
run is ALLOWED to do"; `enforce_orchestrator_probe_gate` really is the reusable shape, recording through
`record_refusal` + `save_state` + an `events.jsonl` event with its override stored in `state["options"]`;
both hosts really do reach `initialize_run_core`, so one call site covers both; `prompt_for_gate_phrase`
really never blocks and returns `None` unanswered; spec Sections 2.1 and 2.5b exist so 2.5c has a real
anchor; and `tests/test_run_flag_surface.py` really was deleted by `19313eed` (a 4863-line file). The
choice to reuse an accepted gate shape rather than invent a surface is correct, and the
justification-string-not-boolean reasoning is the repository's own, stated in two shipped rows.

PR-901 IS THE SAME BLOCKING DEFECT I FOUND IN TWO OTHER PLANS THIS SESSION, and it is worth naming as a
pattern. `- Scope-Paths:` declares
`.aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`. That file does
not exist; the spec is `20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`. I drove
`runner_shared.declared_spec_paths` over the plan and it returns the phantom path, which is exactly the
failure mode: the value ENDS in `.spec.md`, so it WOULD have been announced as a declared spec edit while
resolving to nothing, and E-01 would then have amended the real spec UNDECLARED. That is the
undeclared-spec-edit case both runners' end-of-run report exists to catch, and finalize would have
demanded a `--scope-reason` for the real path and a `--scope-ack` for the phantom one. Corrected in all
three places it appeared (front matter, E-01, the spec-sync section) and V-01 now requires the executor to
paste a `declared_spec_paths` resolution check.

PR-902 IS THE ONE THAT WOULD HAVE SHIPPED A CONSENT GATE WITH A SILENT BYPASS, and the plan's own
mitigation sentence pointed at the wrong failure mode. E-04 said "an exception computing impacts is NOT
swallowed here ... because a consent gate that cannot see the specs must fail closed". But the case that
matters raises NO exception. I read both helpers: `spec_impacts_for_queue` contains
`except OSError: continue`, and its docstring justifies the skip on the grounds that "this is an advisory
surface, and refusing to start a run because an announcement could not be built would be a worse failure"
— a justification that is TRUE for `announce_run_order` and FALSE for a consent gate. Its adapter
`queue_with_plan_paths` independently DROPS an item whose plan it cannot locate, and says so. So a queued
plan that declares a spec edit but whose file is unreadable or unlocatable yields an EMPTY impact list,
and the gate as specified returns `proceed=True` having prompted nobody. That is precisely the bypass the
plan exists to close, reachable without any exception anywhere. E-04 now refuses on a queue-length-versus-
resolved accounting, E-02 gains case (h) to pin it, and V-04 names (h) as the case that must not be
skipped because no other case covers it. Notably the fix belongs on the CALLER side: making the shared
helpers raise would convert an advisory surface into a run-stopper for `announce_run_order`, whose
catch-everything is deliberate and documented, so that is now an explicit Deferred entry.

PR-903 is a divergence presented as an inheritance. E-03 specifies `resume_rule=RESUME_REFUSE` and tells
the executor to put the row "directly after the `--allow-concurrent-driver` row". I checked both existing
`kind="str"` rows: `--allow-concurrent-driver` and `--allow-uncovered-orchestrator-work` BOTH carry
`resume_rule="none-default"`. So an executor copying the neighbouring row's shape would produce the
opposite behavior from the one specified, with nothing in the plan to catch it. The specified value is
nonetheless CORRECT, for a reason the plan never states and I had to establish: `RESUME_REFUSE` makes
`refuse_frozen_flags_on_resume` RAISE, and since neither host's `resume` branch calls
`initialize_run_core` (verified: they call `refuse_frozen_flags_on_resume`, load state, and apply policy
flags), a `--ack-spec-edits` accepted on resume would record consent that GATED NOTHING. Refusing loudly
is honest; freezing it would be theatre. E-03 now carries that reasoning and V-03 requires the executor to
paste the two siblings' values beside the new one so the divergence is visible in evidence.

PR-904 is the same value described with its meaning inverted. The Deferred entry reads "such runs predate
the gate and the flag is frozen (`RESUME_REFUSE`)". A `RESUME_REFUSE` row is the one flag that is NOT
frozen on resume: `refuse_frozen_flags_on_resume` raises for it and `apply_run_policy_flags_on_resume`
explicitly skips it. The conclusion survives and is better supported once corrected, but a reader
reasoning from the stated premise would draw the wrong inference about what happens on a resume.

PR-905 is a design decision that is right and reads as a mistake. E-05 places the gate BEFORE the
`--prepare-only` early return, which is the OPPOSITE of the model gate: the orchestrator gate sits AFTER
that return and prints a deliberate skip, because it spends a model call against a flag contracted to
"create and display the durable queue WITHOUT launching OpenCode". The plan gives its reason in a
parenthesis ("deterministic, no model call, and it closes the prepare-then-resume path") and does not put
it where the executor will be working. I verified the substance: this gate spends no model call, a y/N
prompt is not a launch, and because `resume` reaches no gate, a placement after the return would leave
`--prepare-only` ungated and let an operator prepare a queue and then execute its spec edits having
consented to nothing. So the inversion is load-bearing, and E-05 now says so in the text that becomes the
code comment. V-05 requires the `--prepare-only` half of the end-to-end probe as the evidence.

PR-906 is a trap the plan sets for itself. E-02 case (g) asserts that
`inspect.getsource(initialize_run_core)` contains exactly one `enforce_spec_edit_ack_gate(` occurrence.
E-05 simultaneously requires a substantial explanatory comment at that call site. The shipped orchestrator
gate records this exact hazard and dodges it (its comment describes the three pre-queue gates in prose
rather than spelling them, "so naming it in a comment would fail a correct test on a comment", and it
mentions its own symbol only without the paren; I confirmed the source contains the bare name while the
paren form appears exactly once). The test that constraint cites is DELETED, so it currently binds
nothing — and case (g) re-creates it, making the hazard live again with this plan. E-02 now carries the
warning, E-05's expected outcome requires the comment avoid the call form, and the gate names "edit the
comment, never the test" as the resolution. I also noticed case (g)'s "precedes every
`announce_run_order_fn(`" is the right form rather than a loose one: there are TWO such calls (one in the
prepare-only branch, one on the normal path), so a first-occurrence test would be weaker than it looks.

PR-907 is the gate: three sentences, no approval statement on a plan that adds a refusal path to shared
initialization and amends an approved spec, no scope fence, no stop conditions, and a transition
instruction naming a directory move.

I DECLINED A CARRIER FOR OQ-02 RATHER THAN FILING ONE, and recorded why: the question asks the maintainer
to confirm a default this plan already ships, and all three alternatives it names are changes to the one
function this plan creates, so nothing outlives the plan. What I DID add is the cost the question was
asking about without stating: shipping this makes every future unattended run whose queue declares a spec
edit FAIL unless the flag is passed, including under `--prepare-only`. That is a change to operator habit
rather than a purely additive feature, and it is the part a maintainer is most likely to want to shape.

RECORDED SO A LATER READER DOES NOT RE-DERIVE IT: a bare `--allow-concurrent-driver` exits 2 with
argparse's "expected one argument", confirming E-02 case (f)'s shape; `freeze_run_policy_flags(args)`
returns a plain dict and yields the string, confirming (f)'s second half; and backlog `10qxm7` carries no
`- Blocks-Release:`, so no release gate is owed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | IN-SCOPE | A. Correctness / G. Plan executability | `ls` on the declared path: no such file; the spec is `20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`; drove `runner_shared.declared_spec_paths` over the plan and it returns the phantom path | THE DECLARED SPEC PATH RESOLVES TO NOTHING, in `- Scope-Paths:`, in E-01, and in the spec-sync section. Because the value ends in `.spec.md` it WOULD be announced as a declared spec edit while pointing at no file, and E-01 would then amend the real spec UNDECLARED, which is the undeclared-spec-edit case both runners' end-of-run report exists to catch. Finalize would demand a `--scope-reason` for the real path and a `--scope-ack` for the phantom one, so the plan could not have finalized cleanly. Especially pointed on a plan whose whole subject is spec-edit consent. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Corrected in all three places. V-01 now additionally requires a pasted `declared_spec_paths` resolution check showing `True`. The spec-sync section states why the declaration is the mechanism that makes the amendment visible. |
| PR-902 | HIGH | UNDER-SCOPE | B. Security (fail-closed) / A. Correctness | `spec_impacts_for_queue` source contains `except OSError: continue`, docstring: "an unreadable plan is skipped ... this is an advisory surface"; `queue_with_plan_paths` docstring: "An item whose plan cannot be located is DROPPED"; neither raises | THE CONSENT GATE WOULD PROCEED SILENTLY ON AN UNVERIFIABLE QUEUE, and the plan's mitigation named the wrong failure mode. E-04 guarded only against an EXCEPTION, but the reachable case raises nothing: a queued plan declaring a spec edit whose file is unreadable or unlocatable yields an EMPTY impact list, so the gate returns proceed having prompted nobody. That is the exact bypass this plan exists to close. The helpers' skip is CORRECT for their advisory caller and wrong as a consent input, which is why the fix belongs to the gate's own accounting rather than to the helpers. | C:Medium (requires caller-side accounting rather than a one-line guard); U:Low; S:Medium (a consent gate that can be silently skipped); F:Medium; Overall:Medium | FIXED | E-04 now requires comparing queue length against what the helpers resolved and REFUSING when any declaring item was dropped or unread, explicitly without changing either shared helper. Added E-02 case (h) and named it in V-04 as the case no other covers. Added a Findings bullet with both docstring quotes and a Deferred entry declining to make the helpers raise. |
| PR-903 | MEDIUM | IN-SCOPE | C. Architecture / D. Anti-regression | `RUN_POLICY_FLAGS_BY_FLAG['--allow-concurrent-driver'].resume_rule` and `['--allow-uncovered-orchestrator-work'].resume_rule` both print `none-default`; `RESUME_REFUSE == "refuse"`; `refuse_frozen_flags_on_resume` raises for such a row; neither host's `resume` branch calls `initialize_run_core` | A DELIBERATE DIVERGENCE WAS PRESENTED AS AN INHERITANCE. E-03 specifies `RESUME_REFUSE` while telling the executor to site the row beside `--allow-concurrent-driver`, and BOTH existing `kind="str"` rows use `none-default`, so copying the neighbour's shape produces the opposite behavior with nothing in the plan to catch it. The specified value is right, for a reason the plan never gave: the gate lives only in `initialize_run_core`, which `resume` does not call, so consent accepted on resume would gate nothing. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now carries the measurement and the reason, and instructs that the comment state it so a later reader does not "restore consistency". V-03 requires the two siblings' values pasted beside the new row's. Added a Findings bullet and a conventions bullet on what `RESUME_REFUSE` actually does. |
| PR-904 | MEDIUM | IN-SCOPE | F. Honest documentation | Deferred entry says "the flag is frozen (`RESUME_REFUSE`)"; measured, `refuse_frozen_flags_on_resume` RAISES for such a row and `apply_run_policy_flags_on_resume` skips it precisely so it is never frozen | THE DEFERRAL'S PREMISE INVERTS WHAT ITS OWN CITED VALUE DOES. A `RESUME_REFUSE` flag is the one that is NOT frozen on resume. The conclusion (no re-gating needed) survives and is better supported once corrected, but a reader reasoning from the stated premise would draw the wrong inference about resume behavior, and this plan's whole subject is what a run is allowed to do. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the Deferred entry with the correct semantics and the stronger reason (resume reaches no gate, so there is nothing on that path to protect). |
| PR-905 | MEDIUM | UNDER-SCOPE | C. Architecture / F. Honest documentation | Orchestrator gate sits AFTER the `--prepare-only` return and prints a deliberate skip, its call site citing the model-call cost against that flag's "WITHOUT launching OpenCode" contract; this gate spends no model call; `resume` reaches no gate | THE CORRECT DESIGN READS AS A MISTAKE AND ITS REASON WAS IN A PARENTHESIS. E-05 inverts the model gate's placement, which is load-bearing (it is the only placement closing the prepare-then-resume bypass, since a prepared queue is executed by `resume`, which never re-gates) and is safe for a reason that does not transfer from the model (no model call, and a y/N prompt is not a launch). Left as a parenthetical, the next reader comparing the two gates would most likely "fix" it into the model's placement and silently reopen the bypass. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now states the inversion, why the model's reason does not transfer, and that the placement is what closes the bypass, in the text that becomes the code comment. V-05 requires the `--prepare-only` half of the end-to-end probe as the evidence, and the gate lists a moved early return as a stop condition. |
| PR-906 | LOW | IN-SCOPE | E. Testing / G. Plan executability | Orchestrator gate's call-site comment records the hazard verbatim ("naming it in a comment would fail a correct test on a comment") and avoids the paren form; measured, `initialize_run_core`'s source holds the bare symbol but the paren form exactly once, and TWO `announce_run_order_fn(` calls; the cited `test_run_flag_surface.py` was deleted by `19313eed` | THE PLAN SETS A TRAP FOR ITSELF. E-02 case (g) counts occurrences of the literal `enforce_spec_edit_ack_gate(` in the function's source while E-05 requires a substantial comment at that call site, so a comment written in the natural call form fails a correct test. The shipped gate documents this exact hazard, but the test enforcing it is deleted, so the constraint currently binds nothing and case (g) revives it. The plan gave the executor no warning. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 carries the warning with the model gate's own precedent, and notes that the deleted test is why the hazard becomes live again. E-05's expected outcome requires the comment avoid the call form. The gate names "the fix is always the comment, never the test" as a stop condition. Also recorded that case (g)'s "precedes every" form is correct because there are two announce calls. |
| PR-907 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: three sentences (approve-first, commit path, "Move to `executed/`"); `- Cohesion rationale: not required` | THE GATE WAS MISSING MOST OF ITS REQUIRED ELEMENTS on a plan that adds a REFUSAL PATH to shared initialization and amends an approved spec. No statement of what a human is approving (and the headline consequence is that queues which run clean today start refusing); no scope fence, notably none forbidding edits to the two shared helpers whose posture PR-902 depends on; no stop conditions; and a transition instruction naming a directory move rather than the runner's ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate: a what-a-human-is-approving paragraph naming the habit change, the spec amendment, the deliberate `--prepare-only` behavior and OQ-02; a per-path scope fence stated as a DECLARATION with an explicit not-in-scope list including the two helpers and both host files, plus the finalize-justifies-afterwards rule; the hard-MUST honesty rule naming three temptations; three genuine stop conditions; and the transition with conditional runner/executor ownership. Filled in the cohesion rationale. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The unreadable-plan fail-open could be closed in the shared helpers or in the gate. Which? | In the GATE, via caller-side accounting; declare the helpers explicitly out of scope. | (a) Make `spec_impacts_for_queue` raise on `OSError` - rejected: its only current caller is `announce_run_order`, which is advisory by design and catches everything so "a broken announcement must never stop a run from starting"; raising would turn an advisory surface into a run-stopper for every caller, a behavior change outside this plan's fence. (b) Leave it as authored and rely on the exception clause - rejected: the reachable case raises nothing, so the clause guards a path that does not occur while the one that does proceeds silently. | `spec_impacts_for_queue`'s `except OSError: continue` plus its "advisory surface" docstring; `queue_with_plan_paths`' documented drop; `announce_run_order`'s deliberate catch-all | yes |
| D-2 | `RESUME_REFUSE` diverges from both `str` precedents. Keep it, or match the siblings' `none-default`? | Keep `RESUME_REFUSE`, and require the row's comment to justify the divergence. | (a) Match `none-default` for consistency - rejected: it would ACCEPT and freeze a consent value on a path where the gate never runs, recording consent that gated nothing, which is worse than refusing. (b) Keep it silently as authored - rejected: an executor told to site the row beside a `none-default` neighbour will most plausibly copy that neighbour, producing the opposite behavior with no test to catch it. | Both `str` rows measured at `none-default`; `refuse_frozen_flags_on_resume` raises for a `RESUME_REFUSE` row; neither host's `resume` branch calls `initialize_run_core` | yes |
| D-3 | E-05 inverts the model gate's `--prepare-only` placement. Accept, or align with the model? | Accept the inversion and promote its reason from a parenthesis into the item text. | (a) Align with the orchestrator gate (gate after the early return, announce a skip) - rejected: it reopens the prepare-then-resume bypass, because a prepared queue is executed by `resume` and `resume` reaches no gate; and the model's reason (it spends a model call against a launch-nothing contract) does not transfer to a gate that spends none. (b) Also gate on `resume` - rejected as out of scope: `resume` deliberately does not re-run initialization, and adding a gate there is a change to a shipped path this plan did not fence. | The orchestrator gate's call-site comment on the model-call cost; verified that neither host's `resume` calls `initialize_run_core`; a y/N prompt launches no host | yes |
| D-4 | OQ-02 asks the maintainer to confirm the default and names three alternatives. File a carrier, or decline one? | Decline the carrier with a reason; add the operator-habit cost the question was implicitly about. | (a) File a backlog carrier - rejected: every alternative is a change to the one function this plan creates, so nothing outlives the plan; a carrier would track a decision that may never need making and name no startable work. (b) Resolve it myself - rejected: the y/N-versus-typed-phrase shape and whether a repository-policy pre-acknowledgement key should exist are contract choices about how operators are interrupted, which is the maintainer's call. | The three named alternatives all target `enforce_spec_edit_ack_gate`; the default IS OQ-01's fully specified resolution, so nothing is blocked | yes |
