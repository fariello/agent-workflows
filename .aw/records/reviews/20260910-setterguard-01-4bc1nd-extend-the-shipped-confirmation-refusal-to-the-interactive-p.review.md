# Review: extend the shipped confirmation refusal to the flagless path and refuse a backwards terminal transition, child 4bc1nd (Set setterguard)

- Subject-Id: 4bc1nd
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `6ffbac2a` (the pre-review snapshot of this plan). Structural preflight
`aw ipd lint --phase author` conformed (clean, 0 findings) before semantic review; `--phase
review-finalize` conformed after the revisions, having first correctly REFUSED with `IPD-Q501`
when this review briefly left a `Blocking: yes` question open, which is the gate working.

DISCLOSURE: authored in the same repository and by the same model family as the plan, so treat
this as a near-self-review and worth less than an independent one.

THE DIAGNOSIS IS RIGHT AND THE TWO FIXES ARE THE RIGHT TWO. The guard at `status_set.py:1333`
really is unreachable for a large class of callers, the forward-only `executed` gate at
`:1312-1328` really has no reverse counterpart, and the measured incident (seven plans reverted
out of `executed/` at exit 0) really did happen. The plan's restraint is also correct and worth
naming: it refuses to change what a bare setid means, citing `laykok` E-07, and it refuses to
make `--dry-run` the default, both of which would have been tempting over-corrections. Every
structural claim was re-verified rather than taken on trust, and the incident was reproduced from
scratch (two plans, one setid, one flagless command, both silently reverted and moved).

FOUR FINDINGS CHANGE THE WORK, and all four came from measuring what the plan PROPOSED rather
than what it diagnosed. The diagnosis survived verification in minutes; the proposed remedy did
not survive the same treatment, which is the same pattern this repository's review history keeps
recording.

FIRST, AND MOST IMPORTANT, THE CENTRAL SENTENCE IS FALSE (F-7). The plan says "a MACHINE caller
is protected and a HUMAN is not", and instructs E-01 to write that reasoning into a code comment
so nobody restores the condition. But `ctx` comes from `select_output`, whose docstring promises
"non-TTY stdout -> AGENT" (`result_types.py:75-76`) and whose BODY CONTAINS NO `isatty` CALL AT
ALL. Measured two ways: `grep -n isatty agent_workflows/result_types.py` returns only those two
docstring lines, and `select_output(Namespace(), stdout=StringIO())` returns `OutputMode.HUMAN`.
Confirmed end to end by running a PIPED, flagless `aw ipd set approved demo` in a scratch repo:
stdout was not a TTY, no flags were passed, and it still wrote and exited 0. So the guard keys on
the `--agent`/`--json` FLAGS alone, the unguarded set is "every caller passing neither flag", and
that is both WIDER than "humans" and the direct cause of the next finding. Left uncorrected, this
plan would have committed a false explanation into a comment written specifically to be durable.

SECOND, E-01 BREAKS TWO PRODUCTION CALLERS (F-8), which the plan asserted it would not. Its F-4
claimed the blast radius was small because the runner drivers already pass `--yes`. That
assessment was reached by grepping ARGV-BUILDING sites, a method that cannot see an IN-PROCESS
caller, and the plan then told the executor it was "confirming rather than exploring". Measured
instead by applying E-01 in an isolated worktree and running the suite bare: `5955 passed, 4
failed` against a `5959 passed` baseline on the same worktree. `work_cmd.run_finish` hands
`run_set_command` a hand-built `Namespace(dir=..., message=...)` with no `yes` attribute, so `aw
finish --to reviewed` returns exit 2 and writes nothing, and `aw finish` has no `--yes` to
forward. `oc_runipd.finalize_orchestrator` omits `--yes` where its sibling `set_plan_approved`
has it; that one is LATENT rather than broken today, saved only because the plan->executed
delegation returns at `:1326` above the guard at `:1333`, and the plan should say so plainly so a
later reader does not record it as an observed regression.

THIRD, THE TERMINAL GUARD AS SPECIFIED WOULD HAVE A HOLE IN THE MIDDLE OF THE CORPUS (F-9).
`rec.status` is the raw captured token (`status_set.py:240`, no normalization), and a census of
`.aw/records/plans/executed/` found 25 of 479 plans carrying uppercase `- Status: EXECUTED` or
`- Status: DONE` from the pre-vocabulary era. A guard comparing that token directly against
lowercase `plans.TERMINAL` misses exactly those 25. Verified live that `- Status: EXECUTED`
reverts to `approved` today with no complaint. Related, `superseded -> draft` also succeeds
silently at exit 0 (F-10), so guarding only `executed` leaves a second backwards route open.

FOURTH, THE DEFERRALS HAD NO CARRIER. Three findings were being deferred into this plan's prose,
and this plan is about to move to `executed/`, where no status view reads a deferral bullet. The
repository has an explicit rule about exactly this (`durablecapture` and the `From-Backlog`
machinery), so E-06 was added as a required execution item that files one backlog carrier per
deferred finding with pasted evidence in V-06. That is what let OQ-02 be DOWNGRADED from blocking
to non-blocking: with the carriers guaranteed by an E-item, what remains is a maintainer
preference about where the documentation edit lands, and stopping an executable plan over a
preference is over-escalation.

ALSO CORRECTED, smaller but load-bearing. E-01 was told to make the human renderer print the
per-artifact detail; it already does (`renderers.py:141-151`, a `Would change:` section), so that
instruction would have produced a duplicate rendering. The terminal set is now required to be
DERIVED from `plans.TERMINAL` rather than re-listed, following the comment `status_set.py:76-78`
leaves about a re-listed copy that desynced this very module once before. The new override flag
must be declared on all five routing surfaces, following the `--allow-open-questions` precedent
(`cli.py:3219-3230`) that exists because a gate declared on one spelling is bypassed by choosing
another. E-05 must now pin the SPEC case explicitly: `SPEC_TRANSITIONS` legitimately permits
`implemented -> deferred` and `superseded -> draft`, so E-02's plans-only keying is required
rather than incidental. `- Scope-Paths:` grew from two entries to seven, because the caller fixes
and the three test modules that must return to green were undeclared. And the measured baseline
is now written INTO the plan by node id, so the executor reproduces it instead of re-deriving it.

WHAT I DID NOT CHANGE, deliberately. The plan's decision to keep setid fan-out, its refusal to
make `--dry-run` default, its preference for a dedicated override flag over overloading
`--force`, and its OQ-01 framing are all correct and were left alone; OQ-01 gained one note
because the `--allow-open-questions` precedent supports its recommendation more strongly than the
plan knew, including the history-attribution property (`status_set.py:604-610`) that makes an
override auditable in the FILE rather than only in a shell history.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | high | IN-SCOPE | A/G (correctness of the plan's own diagnosis) | `agent_workflows/result_types.py:75` and `:76` versus the function body; `agent_workflows/status_set.py:1333` | The plan's central claim, that the guard protects machine callers and not humans, is false. `select_output` implements no TTY rule (no `isatty` in the body; returns `HUMAN` for a `StringIO` stdout), so the condition keys on the `--agent`/`--json` flags alone and the unguarded set is every flagless caller. E-01 was instructed to write this false reasoning into a durable code comment. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern, Scope, E-01, conventions and F-7 rewritten to state what the condition actually did; E-01 now forbids the machine-versus-human wording and V-01 checks the comment for it. |
| PR-002 | high | UNDER-SCOPE | G/E (blast radius, validation) | `agent_workflows/work_cmd.py:562-573`; `agent_workflows/oc_runipd.py:841-855`; measured suite `5955 passed, 4 failed` versus `5959 passed` | E-01 breaks two production callers the authored survey could not see, because it grepped argv sites and missed in-process ones. `aw finish --to reviewed` returns exit 2 and writes nothing and has no `--yes` to forward; `finalize_orchestrator` omits `--yes` (latent, saved by the delegation returning above the guard). Four named tests fail. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 rewritten around the two measured fixes and a corrected survey method; the four failing node ids and the baseline written into Required tests; `work_cmd.py`, `oc_runipd.py` and the three test modules added to `Scope-Paths`. |
| PR-003 | high | UNDER-SCOPE | A/D (guard correctness) | `agent_workflows/status_set.py:240`; census of `.aw/records/plans/executed/` (18 `EXECUTED` + 7 `DONE` of 479); scratch run showing `EXECUTED -> approved` at exit 0 | E-02 as specified compares the raw `rec.status` token against a terminal set, so the 25 corpus plans carrying uppercase `EXECUTED`/`DONE` would remain unguarded: a hole in the middle of the very corpus the guard protects. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires case-folding plus the `done` alias via `normalize_target_status`, derives the set from `plans.TERMINAL`, and E-05/V-02/V-05 require an uppercase assertion. |
| PR-004 | medium | UNDER-SCOPE | A/D (second backwards route; over-refusal risk) | scratch run `superseded -> draft` at exit 0; `agent_workflows/attention_contract.py:367-395` | `superseded -> draft` also succeeds silently today, so guarding only `executed` leaves a second route out of a terminal state. Conversely specs legitimately permit `implemented -> deferred` and `superseded -> draft`, so E-02's plans-only keying is a requirement to pin, not an accident. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires the `superseded -> draft` refusal and an explicit spec-lifecycle must-still-work assertion; V-05 demands both. |
| PR-005 | medium | UNDER-SCOPE | G (durable capture of deferrals) | this plan's `## Deferred / out of scope`; `.aw/records/plans/README.md` lifecycle contract | Three findings were deferred into the prose of a plan that will move to `executed/`, where no status view reads them, so each would have been silently lost. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 added: file one backlog carrier per deferred finding and cite each id6 in its bullet, with V-06 requiring pasted `aw backlog new` output and an `aw attention` check. |
| PR-006 | medium | IN-SCOPE | F (self-documenting output) | `agent_workflows/renderers.py:141-151` | E-01 instructed the executor to make the human refusal print the per-artifact change detail, which the shared renderer already prints under a `Would change:` header, so following the instruction would add a duplicate rendering. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now points at the existing renderer and says the artifact COUNT (genuinely absent) belongs in `CommandResult.summary`, not in the renderer. |
| PR-007 | medium | IN-SCOPE | C (one mechanism, declared everywhere) | `agent_workflows/status_set.py:32`, `:76-78`; `agent_workflows/cli.py:3219-3230`, `:10927`, `:11029`, `:11106`, `:11233`, `:11274` | E-02 named no source for the terminal vocabulary (inviting a re-listed copy, the exact thing a comment in this module records as having desynced it before) and did not say the new override flag must exist on every routing surface, which is how `--allow-open-questions` avoided being bypassable by spelling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires deriving from `plans.TERMINAL` and declaring the flag on all five surfaces; V-02 requires the derivation line and the registrations as evidence. |
| PR-008 | medium | OVER-SCOPE (declaration gap) | G (scope fence) | this plan's `- Scope-Paths:` versus E-03's stated work | `Scope-Paths` declared only `status_set.py` and `tests/test_status_set.py` while E-03 was expected to add `--yes` to callers, so the fence did not cover the files the plan would actually change; `aw ipd finalize` would have required a `--scope-reason` for each. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `Scope-Paths` expanded to the seven paths the items name, and the Scope check section now maps each path to its item. |
| PR-009 | medium | IN-SCOPE | E (reproducible baseline) | measured `5959 passed, 3 skipped, 2 xfailed` at `c77f5b3c` in a clean worktree | The plan required a baseline but recorded none, and predicted an environmental `test_reporting_contract.py` failure that did NOT reproduce in a clean worktree. An executor would have re-derived the baseline and might have accepted the predicted failure as expected. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The measured baseline and the four post-patch failing node ids are written into Required tests, with the note that the predicted environmental failure did not reproduce. |
| PR-010 | medium | IN-SCOPE | F/G (honest documentation) | `.aw/records/plans/README.md:62-64`; `.aw/records/backlog/README.md:65`; `.aw/records/specs/README.md:25`; `README.md:53`; GUIDING_PRINCIPLES principle 2 | E-01 makes four documented setter examples refuse as written, and the plan raised this as a question for the reviewer rather than resolving the part that is not a judgement call: principle 2 forbids leaving them false, so only the LOCATION of the fix is optional. | C:Low; U:Medium; S:Low; F:Low; Overall:Medium | DEFERRED | The obligation is now stated and carried (E-06 files it; F-13 records it; OQ-02 asks only where it lands). The four README edits are NOT in this plan's scope: see Deferred and open below. |
| PR-011 | medium | IN-SCOPE | F (self-documenting output) | `agent_workflows/status_set.py:1343`; scratch runs printing `next: aw set approved demo --yes` | The refusal's suggested retry is rebuilt as `aw set <raw_args> --yes`, dropping `--actor`, `-m`, `--no-commit` and rewriting `aw ipd set` as `aw set`. E-01 promotes this from near-invisible to seen by every flagless caller, so a copy-pasted retry silently loses flags. | C:Medium-High; U:Low; S:Low; F:Medium-High; Overall:Medium-High | DEFERRED | Recorded as F-11 and carried by E-06. See Deferred and open below. |
| PR-012 | medium | OVER-SCOPE (adjacent defect) | C (shared authority correctness) | `agent_workflows/result_types.py:75-76` versus its body | `select_output`'s docstring documents a non-TTY rule its body does not implement. Distinct from PR-001 (which is about this plan believing it): this is the underlying defect in the CLI's single output-mode authority. | C:Low; U:Low; S:Low; F:High; Overall:High | DEFERRED | Recorded as F-12 and carried by E-06. See Deferred and open below. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is the plan's "machine protected, human not" framing a wording nit to leave, or a finding that changes the work? | A HIGH finding that changes E-01, because the plan instructs the executor to write that reasoning into a durable code comment and it is false. | Leaving it as prose imprecision (rejected: the comment is written specifically to outlast the change, so a false one misleads whoever next reads the guard). Rewriting silently without a finding row (rejected: it also widens the caller set, which is PR-002). | `agent_workflows/result_types.py:75-76` versus a body containing no `isatty`; `select_output(Namespace(), stdout=StringIO())` returning `OutputMode.HUMAN`; a piped flagless scratch run writing at exit 0 | yes |
| D-2 | Should the review trust the plan's own F-4 blast-radius survey, which tells the executor it is "confirming rather than exploring"? | No: re-run it by applying E-01 in an isolated worktree and running the suite bare. | Trusting it (rejected: the plan's method grepped argv-building sites, which structurally cannot see an in-process caller, and two of the four measured failures are exactly that case). | measured `5955 passed, 4 failed` versus a `5959 passed` baseline on the same detached worktree at `c77f5b3c`; `work_cmd.py:562-573`; `oc_runipd.py:841-855` | yes |
| D-3 | Is `finalize_orchestrator`'s missing `--yes` an observed break or a latent one? | Latent: report it as such and still fix it. | Calling it broken (rejected: verified in a scratch repo that the plan->executed delegation returns at `status_set.py:1326`, above the guard at `:1333`, so it never reaches the confirmation check today). Leaving it alone (rejected: the ordering that saves it is incidental, and its sibling `set_plan_approved` passes `--yes`). | `status_set.py:1319-1328`; scratch run refusing for the unrelated missing-receipt reason; `oc_runipd.py:762-772` versus `:841-855` | yes |
| D-4 | How should E-02 obtain the terminal-status vocabulary? | Derive it from `plans.TERMINAL`, already imported into this module. | Re-listing the three tokens inline (rejected: this module carries a comment recording that a re-listed status copy is what refused `aw backlog set graduated` after the vocabulary grew, and GUIDING_PRINCIPLES P8 forbids the second copy). | `agent_workflows/plans.py:26`; `agent_workflows/status_set.py:32`, `:76-78` | yes |
| D-5 | Does the uppercase-status corpus finding justify adding a requirement to E-02, or is it a test-only concern? | A requirement in E-02 plus an assertion in E-05, because a case-sensitive guard silently skips 25 real files. | Test-only (rejected: no test would exist to fail, since E-05 as authored used lowercase fixtures). Ignoring it as legacy data (rejected: those 25 sit in `executed/`, the exact disposition the guard protects, and a live scratch run confirmed `EXECUTED` reverts today). | `status_set.py:240`; the executed-dir census (18 `EXECUTED`, 7 `DONE`, 445 `executed`); scratch run `EXECUTED -> approved` at exit 0 | yes |
| D-6 | Should the four now-false documentation examples be fixed inside this plan? | No: obligate the fix, carry it in a backlog item, and ask the maintainer only where it lands. | Adding the four READMEs to this plan's scope (rejected: a four-tree documentation sweep has its own reviewable surface and widens a two-guard change). Saying nothing (rejected: principle 2 forbids knowingly leaving documentation false, so silence was not an available answer). | GUIDING_PRINCIPLES principle 2; the four cited README lines | yes |
| D-7 | Should OQ-02 (durable carriers for the deferrals) be `Blocking: yes`? | No, after adding E-06. It was briefly marked blocking and that was over-escalation. | Keeping it blocking (rejected: with E-06 making the carriers a required item with pasted evidence, the residual question is a maintainer PREFERENCE about placement and priority, and blocking an otherwise-executable plan on a preference is the failure mode the readiness vocabulary warns about). Dropping the question (rejected: the placement choice is genuinely the maintainer's). | `aw ipd lint --phase review-finalize` correctly refusing with `IPD-Q501` while it was open; the plan-review readiness rules on genuine not-ready conditions | yes |
| D-8 | Is the plan's claimed environmental `test_reporting_contract.py` failure real? | No, in a clean worktree: it did not reproduce (`5959 passed`, zero failures), consistent with the plan's own note that it is primary-checkout-only. Record the fact so the executor does not accept it as expected. | Repeating the plan's caveat unexamined (rejected: an executor told to expect a failure may accept a real one). | bare suite in the detached worktree at `c77f5b3c`: `5959 passed, 3 skipped, 2 xfailed` | yes |
