# Spec: Standalone post-hoc audit of an executed plan

- Date: 2026-09-20
- Status: draft
- Id: i4gpto
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: 7u9kbm
- Scope: An operator-invoked verb that buys one independent skeptical opinion on an already-executed plan, reusing the in-run verifier prompt and outcome schema, and never touching the finished plan document.
- Constrained-by: `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`
  (`25kzda`, `approved`), whose Section 1.3 "Audit only" row routes audit to `aw runs verify-ledger` or
  `aw <host> run resume`. This spec does NOT amend that row and does not contradict it: that row is
  about auditing a RUN LEDGER, and this verb audits a PLAN'S CLAIMS. Section 6 states the boundary.
- Implemented-by: `.aw/records/plans/pending/20260908-reverify-01-mp289j-run-the-existing-verifier-prompt-against-an-already-executed.ipd.md`
  (`mp289j`)

## Workflow history

- 2026-09-20 created (aw specs): An operator-invoked verb that buys one independent skeptical opinion on an already-executed plan, reusing the in-run verifier prompt and outcome schema, and never touching the finished plan document.
- 2026-09-20 drafted (opencode its_direct/pt3-claude-opus-5-1m-us): Written as the recorded DECISION deliverable of plan `mp289j`, whose Spec/documentation sync section requires it under either outcome ("THE DECISION IS THE PRIMARY DELIVERABLE UNDER EITHER OUTCOME"), so the four questions backlog `7u9kbm` reserved are not re-derived by the next person who wants this. Records the maintainer's two resolutions of 2026-09-10 (OQ-01 build it, findings need a carrier; OQ-05 the audit may fix code but never the plan record) and the three design answers the plan directed its executor to choose (the verification base, the verdict destination, the tree). Every number here was re-measured at HEAD `4b8f22b5` rather than quoted.

## 1. The gap, and why it could not be closed by configuration

The repository ships an INDEPENDENT SKEPTICAL VERIFIER: a second agent turn, in a fresh session, that
audits an execution it did not perform. It is composed by `runner_shared.build_verifier_prompt`, and
measured 2026-09-20 that function has exactly ONE production caller, inside
`runner_shared.execute_item_core`'s execute path, plus five callers in tests.

So the verifier could only ever run as TURN TWO OF AN EXECUTION. There was no route by which a human
could ask for it afterwards. Three consequences, each observed in this repository rather than imagined:

1. A run executed with verification OFF cannot be given an independent opinion later. On the OpenCode
   host that is the SHIPPED DEFAULT (`runner_profiles.RUNNER_REGISTRY["oc"].validate_default` is
   `False`, resolving as `provenance='shipped-default'`), so most executed plans here never got one.
2. An item that reached `substantially-complete` because finalize refused is exactly where a human
   wants a second opinion before deciding whether to trust the lane, and could not have one.
3. Lanes integrated BY HAND during recovery were validated by the full suite but never by an
   independent verifier, with no way to add that signal after the fact.

THE HOSTS DISAGREE ON THE DEFAULT, DELIBERATELY, and that asymmetry is why "just turn it on" is not the
fix. Measured: `RUNNER_REGISTRY["oc"].validate_default` is `False` and `RUNNER_REGISTRY["agy"]`'s is
`True`, resolved through `runner_shared.resolve_verification_decision`. So the in-run verifier is OFF by
default on OpenCode and ON by default on Antigravity. That is a measured maintainer ruling
(2026-08-31), owned by specs and plans `tm2cz8` / `ybkmzp`, and THIS SPEC DOES NOT TOUCH IT. Turning the
in-run verifier on would also not help at all with plans ALREADY executed, which is the whole case.

## 2. Is the verb wanted? (the question `7u9kbm` reserved as blocking)

YES. Resolved by the maintainer 2026-09-10.

The economics were genuinely open when the plan was authored: the maintainer's own measured finding was
that on a strong executor the verifier added only nits for roughly 33 percent extra cost, and a plan
review that concluded the historical base is unreachable for ~97 percent of executed plans argued the
feature was worth little.

THAT OBJECTION WAS WITHDRAWN ON ITS PREMISE, not on its arithmetic. The maintainer's words:

> I can ask an agent today "another agent claims to have fully completed abc123. Please verify all of
> its claims and the completeness of execution". It needs exactly no work to compare against.

and

> this had almost nothing to do with the specific case of something left unfinished because of a
> terminated `aw oc|agy run` and everything to do with my wondering if a plan or similar was actually
> executed faithfully and completely.

So the verb is not a run-recovery tool and must not be designed as one. It answers "was this plan really
done?" against material that is ALWAYS available: the plan's own claims, and the repository as it stands.
The measured cost of the alternative is the friction it removes: the one historical case that was
"recovered by hand" means a human went into the host and asked an agent manually.

A SECOND OBLIGATION CAME WITH THE YES. A finding must land in a backlog item or plan, not only in a
report, on the maintainer's standing rule that "no defect, gap, or issue may be found, raised, or noted
without a minimum of at least one IPD or one backlog item per issue". Report-only was declined
explicitly. Section 5 makes that a requirement of the verb rather than a convention of its users.

## 3. What it may write (the immutability question)

THE AUDIT MAY FIX CODE IN PLACE AND COMMIT; IT MAY NEVER EDIT THE FINISHED PLAN'S RECORD. Resolved by
the maintainer 2026-09-10.

The apparent collision that made this blocking: the prompt the verb is required to reuse instructs the
agent, in its requirement 4, to "fix them, re-run validation, and commit path-scoped ... Never push",
and `AGENTS.md` forbids adding commits to a plan already in `.aw/records/plans/executed/`.

THE CONSTRAINT IS NARROWER THAN BOTH THE PLAN AND ITS REVIEW ASSUMED, and re-reading the rule is what
dissolved it: the rule forbids adding commits TO A PLAN, and says to "close a post-execution gap with a
new corrective IPD, not an in-place edit". THE IMMUTABLE THING IS THE PLAN DOCUMENT, NOT THE REPOSITORY.
Fixing code behind a finished plan is therefore authorized; only the document is out of bounds.

R-1. The audit MAY modify code, tests and documentation within the audited plan's scope, and MUST commit
path-scoped. It MUST NOT push.

R-2. The audit MUST NOT edit, re-status, move, or add any commit to the audited plan document. It MUST
NOT append to its `## Workflow history`, tick its checkboxes, or fill in its `Observed evidence`
blocks. A gap it cannot close with an in-scope fix is closed by a NEW corrective IPD.

R-2 IS THE ONE RULE NO COST ARGUMENT MAY BUY. Making finished work look as though it was always complete
is precisely the dishonesty the immutability rule exists to prevent.

ON COST, since the maintainer asked for evidence and expected none to exist. Measured 2026-09-10 from
`.aw/records/runs/*/state.json`: 59 of 144 run records carried a numeric cost field, including 8 of the
12 most recent. Per-attempt medians were $11.10 for a `review` turn (n=185) and $18.50 for an `execute`
turn (n=94). So a small fix through a full corrective cycle costs about $29.60 against about $11.10 for
a fix riding inside the audit turn, roughly 2.7x. HONEST BOUNDS: those are per ATTEMPT, so a retried item
costs more; an audit turn may run longer than a plan review because it inspects finished work, making
$11.10 a floor; and 85 of 144 runs carried no cost field, so this is a sample and not a census.

## 4. What it verifies against

R-3. The audit's PRIMARY basis is the plan's OWN recorded claims versus the repository's present state.
This basis is always available, so the verb is never refused for want of history.

R-4. A historical diff basis is offered as CORROBORATION when one is reachable, in precedence order:
an operator-supplied revision (`--base`), then a surviving `aw ipd begin` receipt's `base_head`, then
none. The verdict RECORDS which basis it had, in a `diff_basis` field.

WHY THE RECORDED BASE CANNOT BE THE DESIGN. Re-measured across the whole tree at HEAD `4b8f22b5`: of 561
plans in `.aw/records/plans/executed/`, exactly 17 still have a readable begin receipt carrying
`base_head` and 544 do not. The mechanism is not a bug: `ipd_lifecycle.py:3989` unlinks the receipt under
the comment "Consume the begin receipt (the transaction is cleanly complete)". So the receipt survives
precisely when finalize did NOT cleanly complete, which makes the surviving population both small and
BIASED toward plans where something went wrong. Three plans worth naming measured receipt-ABSENT:
`nna8yz`, `tm2cz8`, and `ybkmzp`.

R-5. A verdict computed with `diff_basis: none` MEANS "the plan's claims are, or are not, borne out by the
code, tests and artifacts that exist now". It does NOT mean "the diff at the time was correct", and the
prompt must say so to the auditor rather than leaving the distinction to inference.

## 5. Where a verdict goes

R-6. The machine verdict is written to a FRESH run directory per invocation, under the runs root. That
root is GITIGNORED (`.aw/.gitignore:14`, pattern `records/runs/`), so a verdict is local and is not
permanent repository history.

R-7. Each invocation MUST get its own directory, so a second opinion cannot erase the first. This is a
structural requirement and not a naming convention: `runner_shared.new_run_id` is
`run-<UTC seconds>-<pid>`, so two invocations within one second from one shell produce the SAME id
(measured 2026-09-20 while testing this verb). The implementation therefore suffixes until the path is
free, using `mkdir(exist_ok=False)` as an atomic test.

R-8. Every finding the audit reports MUST also be filed as a backlog item, so the finding reaches
TRACKED history a release gate can see. This is what makes R-6's gitignored destination acceptable: the
verdict prose is local, the findings are not.

WHAT IS NOT ACHIEVABLE, stated so nobody over-reads R-7. Nothing prevents an operator from re-running
the audit, and nothing can: the verb is invoked on demand, so it cannot force its own invocation and
cannot forbid a second. The achievable property is narrower and is the one specified: a later run cannot
HIDE an earlier one, and a finding the earlier run filed is a committed backlog item a later run cannot
unfile.

TWO DESTINATIONS WERE CONSIDERED AND REJECTED, with their costs, so the choice is not re-litigated:

* THE REVIEWS TREE (`.aw/records/reviews/`) would make the verdict tracked and citable, but
  `review_findings.SUBJECT_TYPES` is the CLOSED pair `('ipd', 'spec')` (verified live), an unrecognized
  value is a documented parse error (`REV-M101`/`REV-M102`), and the README states a new type is added by
  amending the vocabulary AND the checker's per-type resolution together. So filing there costs either an
  honesty compromise (recording a VERIFICATION verdict as an `ipd` REVIEW, a different judgement by a
  different actor at a different lifecycle point) or a vocabulary-plus-checker amendment.
* THE PLAN'S OWN `## Workflow history` is tracked and append-only and is where a workflow records that it
  touched an artifact, which makes it superficially attractive. It is ruled out by R-2: appending to an
  executed plan's file is exactly the in-place edit the immutability policy forbids.

## 6. Surface: which noun, and which host

R-9. The verb is `audit <id6>`, declared on the HOST RUNNER's own parser and reached as
`aw <host> run audit <id6>`, alongside the existing out-of-band verbs `stop` and `integrate`.

WHY NOT `aw runs audit`. `aw runs` self-describes as "the READING half of the run surface ...
Read-only, with FOUR exceptions, named rather than counted". A verb that launches a model turn and
writes a verdict is read-only under no reading of that sentence, and that description has already gone
stale twice by COUNTING its exceptions, so adding a fifth is the wrong direction.

WHY NOT `aw run audit`. `aw run` is "the WRITING half", whose ledger transactions (`start`, `record`,
`cancel`, `finalize`) are deterministic bookkeeping that spend no agent turn. An audit is an agent turn.

WHY THE HOST RUNNER NOUN IS RIGHT. The verb LAUNCHES A HOST, which is exactly what that noun owns, and
`stop` and `integrate` already establish that an out-of-band verb touching no queue belongs there.

BOUNDARY AGAINST `25kzda` SECTION 1.3. That spec's "Audit only" row routes audit to
`aw runs verify-ledger <run-id>` or `aw <host> run resume <run-id>`, on the reason "Verification is a
run-state operation, not another execution mode". Both of those audit A RUN: its ledger's hash chain, its
evidence validity, its resumable steps. This verb audits A PLAN'S CLAIMS, needs no run id, and works for
a plan whose run records are long gone (or which was executed by hand). So it does not duplicate that
row and does not amend it.

R-10. The verb is DECLARED on both hosts through one shared declarator, so an operator meets the same
command line on either, and it is IMPLEMENTED on the OpenCode host only. The Antigravity binding REFUSES
with a message naming the OpenCode spelling, exiting 2 ("cannot run") rather than 1 ("refused after
checking"). Wiring a second launch path doubles the review burden while the two drivers are still being
unified (`5e4sb6`), and one independent opinion is the whole product.

R-11. The verb MUST appear in each driver's implicit-start shim subcommand set. An unregistered first
token is rewritten into `start <token>`, so a bare `audit <id6>` would LAUNCH A RUN with `audit` as a
selector, i.e. an operator asking for a cheap opinion on finished work would pay for an execution
attempt.

## 7. The one-composer rule

R-12. The audit MUST reuse `runner_shared.build_verifier_prompt` and the existing verification outcome
schema. A second verifier prompt or a second outcome schema is FORBIDDEN.

The reason is stated in backlog `7u9kbm` and is the same argument `wlxkoz` makes against a second
completion checker: two verifiers drift, and then neither can be trusted. Note the drift had ALREADY
happened once and has since been repaired: the two hosts once carried separate 68-line copies of this
prompt differing in 26 lines, and the Antigravity copy had NO push prohibition at all while instructing
the agent to commit. `rununify` collapsed them to one definition with host labels.

R-13. The audit rendering is a MODE of that one composer, and the IN-RUN rendering MUST be byte-identical
before and after. The mode parameter therefore defaults to the in-run behavior.

R-14. Exactly three things differ in the audit rendering, and requirement 4's fix-and-commit authority is
deliberately NOT one of them (R-1 authorizes it):

1. Requirement 1's working-tree-diff instruction is replaced by the claims-versus-present-state
   instruction of R-3, because a finished plan has no such tree.
2. Two requirements are ADDED: the R-2 prohibition, and the R-8 carrier obligation.
3. The execution-outcome path is omitted, because for a historical plan no such file exists and naming
   one invites the auditor to report its absence as a defect.

## 8. Tree isolation

R-15. The audit turn MUST NOT run in the shared primary checkout by default. It allocates its own git
worktree through the existing `worktree_lease` machinery, which is also the default for execute turns on
both hosts, with an explicit opt-out for an operator who accepts the contention.

R-16. The lane is NEVER torn down by the verb, even on failure. `teardown_isolation_worktree` is
destructive and safe only on a lane holding no work, and an audit that fixed code in scope holds exactly
that work. The lane and its branch are reported so an operator can inspect and then integrate or discard.

R-17. The audit does NOT integrate its own lane. A fix behind a finished plan must be reviewed on its own
merits rather than auto-merged by the verb that requested it.

NOTE WHICH GUARD IS PRIMARY. Under R-13's chosen route the immutability guarantee is carried by R-2 (the
prompt's explicit prohibition), and tree isolation is a SECONDARY guard plus a contention control. A
read-only tree was considered as the primary guard and rejected: it would silently refuse the very
in-scope fix R-1 authorizes, which is an instruction-versus-reality gap.

## 9. What this spec deliberately does not decide

* THE PER-HOST VERIFICATION DEFAULTS. Opposite by design (Section 1), owned by `tm2cz8` / `ybkmzp`, and a
  measured maintainer ruling. Untouched.
* THE MISSING `--validate` FLAG ON THE ANTIGRAVITY HOST as it stood in 2026-09. Reclassified from
  evidence to a defect with its own carrier (backlog `kyb0v5`); registering a flag on the other host is
  not re-verification and may not be absorbed here.
* PER-ROLE MODEL SELECTION for the auditor. The audit reuses whatever VERIFIER launch profile is
  configured, so it inherits that decision rather than making a new one (`kgpptv`, `w15vzb`).
* RE-AUDITING HISTORICAL PLANS. A use of the verb, and a maintainer's call about spending money on
  history, not part of specifying it.

## 10. Acceptance criteria

1. `aw oc run audit <id6>` runs one fresh-session turn against an executed plan and records a verdict.
2. A plan that is not in `executed/` is REFUSED with its own code, and an unknown id6 likewise; both
   refusals are returned as messages, never raised as tracebacks.
3. The verdict records `diff_basis` as one of `receipt`, `operator`, or `none`, and `none` is accepted as
   a normal outcome rather than an error.
4. The audited plan document is byte-identical after an audit, asserted by test.
5. Two audits within one second produce two run directories.
6. The audit prompt carries the R-2 prohibition and the R-8 carrier obligation.
7. The in-run verifier prompt is byte-identical to its pre-change text.
8. Exactly one `build_verifier_prompt` body exists in `agent_workflows/`, with the two host functions as
   delegations.
9. Both hosts declare the verb with an identical command line; the Antigravity binding exits 2 naming the
   OpenCode spelling.
10. `audit` is present in both drivers' implicit-start shim sets, and a bare refused `audit` creates no
    run directory.
