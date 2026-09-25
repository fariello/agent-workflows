# Review findings: plan hzdq8y

- Subject-Id: hzdq8y
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 01 of Set `followgen`: remove the never-built `--follow-generated` run flag. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE semantic review,
and `--phase review-finalize` conforms after the revisions. The plan file was committed and unchanged
at review start (`git status --porcelain` empty; last touched by `c41b69fb`), so no pre-review
snapshot was needed.

THE PLAN'S CASE FOR REMOVAL IS CORRECT AND WAS INDEPENDENTLY REPRODUCED, which is worth stating first
because the plan proposes deleting a public CLI surface and that deserves scrutiny rather than
agreement. Verified by running the code: `--action plan` is refused (`ACTION_IMPLEMENTED` is
`frozenset({'review'})` while `ACTION_CHOICES` carries `plan`), so no producer exists; `files_changed`
and `recommended_next_action` appear at exactly two places in the package, both inside the prompt text
SENT to the agent, and are never parsed back (zero `.get("files_changed"` hits); `--follow-generated`
is the ONLY `implemented=False` row of fifteen; and both host parsers accept it today while returning
`SystemExit(2)` for a genuinely unknown flag, so the post-removal assertion tests the right mechanism.
Findings 1 to 4 hold.

FIVE FINDINGS, ALL FIXED IN PLACE. One would have sent the executor into a finalize-gate refusal in
both directions (PR-001, a dead spec path). One is a deterministic `error` the plan carried twice, and
one half of it is a genuinely non-obvious rule (PR-002: a SPEC may not be a `Carrier:`). One corrects
a stale claim the plan inherited from an executed sibling and would have reproduced (PR-003). One is
the unreconciled consequence of leaving a maintainer ruling naming a removed flag (PR-004). One is the
usual thin gate, aggravated here because nothing in the test suite guards this surface any more
(PR-005).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G (executability) | MEASURED: `Path(".aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md").exists()` is `False`; the spec is at `20260826-25kzda-01-25kzda-...` (renamed to the id6 grammar); `ipd_lifecycle._scope_match(real, declared)` -> `False` | THE PLAN DECLARED A SPEC PATH THAT DOES NOT EXIST, in `- Scope-Paths:`, in E-04's instruction, and in V-04's verification command. Three consequences, each measured rather than inferred. (1) The finalize scope gate fails in BOTH directions: editing the real spec yields an out-of-scope path needing a `--scope-reason`, while the declared path sits unmodified needing a `--scope-ack`. (2) E-01's assertion (c) reads a missing file, so it either errors or, if the executor guards it with an existence check, passes VACUOUSLY while the spec still names the flag. (3) V-04's `rg` over a nonexistent path returns no output, which is exactly the "expected: no output" the item asks for, so the verification would PASS having measured nothing. `aw ipd lint` cannot catch this: `check_scope_paths` validates the Section 4.5 GRAMMAR only, never existence. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | `- Scope-Paths:` corrected to the real id6 path; E-04 names it and records that the old name does not exist; E-01 must resolve the spec by GLOBBING for `*-25kzda-*.spec.md` and fail loudly rather than hardcode a path; V-04 uses the real path and switched from `rg -n` to `rg -c` with the measured before-count (9) so a zero result is meaningful rather than ambiguous. Recorded as Finding 9, which also names the two sibling plans (`01reg8`, `1g4i1t`) carrying the same dead path as a finding against THEM. |
| PR-002 | HIGH | IN-SCOPE | G / repository rule | `check_engine.evaluate_durable_carrier` on this file -> `check.ipd-uncarried-obligation` at `error`, citing TWO obligations: "deferred row 1: carrier z7nbn1 resolves to no backlog item or plan" and OQ-02; `check_engine._CARRIER_TARGET_TYPES == ("backlog", "plans")` | TWO UNCARRIED OBLIGATIONS, and the first is a trap worth recording rather than just fixing. The plan wrote `- Carrier: z7nbn1`, which LOOKS correct (a real spec, genuinely owning the deferred work) and is REFUSED: the rule's target types are backlog and plans only, and its comment records that accepting a spec "was offered to the maintainer and REJECTED" because it delegates the judgement the rule exists to remove. So a well-intentioned, accurate citation in the wrong FIELD reads as a dangling carrier. OQ-02 separately carried nothing at all. Left unfixed the plan fails `aw check plans` at `error`, and on reaching `executed` it classes `done` in `aw attention` and both obligations vanish. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The deferred row now uses `- Carrier-Evidence:` naming the spec FILE (the resolvable-artifact form), with a note recording why `- Carrier:` is refused so the next author does not retry it. OQ-02 gained a `- Carrier-Declined:` stating that both answers are fully specified in-plan. Re-measured: 1 -> 0 findings. |
| PR-003 | MEDIUM | IN-SCOPE | D (anti-regression) / A | MEASURED: `tests/test_run_flag_surface.py` does not exist, deleted in `19313eed` "test: trim test suite from 9,136 to under 2,000 tests"; zero hits in `tests/` for the flag name, `NOT YET IMPLEMENTED`, or `RUN_POLICY_FLAGS` implemented-ness. Separately: `--with-dependencies` is `implemented=True` | TWO STALE FACTS THE PLAN WOULD HAVE CARRIED FORWARD. (a) Executed sibling `dhycim` recorded a shipped contract test pinning the unimplemented-flag set and requiring `x8diyb` in an unimplemented row's help; that file is GONE, and nothing replaced it. This LOWERS this plan's risk (no contract test to break) and simultaneously raises the stakes on E-01, because nothing would have caught the removal either. The plan stated neither half, so an executor could not know whether a test edit was owed. (b) E-02 told the executor to rewrite a docstring reading "the honest end state for `--follow-generated` and `--with-dependencies`, whose behavior nobody has built" - but `--with-dependencies` HAS been built, so a minimal one-name edit would preserve a false claim in the replacement. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added Finding 7 (the deleted contract test, stated in both directions) and Finding 8 (`--with-dependencies` is implemented, so the docstring is already stale independently of this plan). E-02 now forbids carrying the false claim forward, requires the replacement to name NO specific flag (which is also the only way its own zero-hit expected outcome is satisfiable, since the docstring is one of the three current hits), and records the simulated post-removal fact that the refusal loop iterates ZERO rows. The gate makes test-first non-negotiable on exactly this ground. |
| PR-004 | MEDIUM | IN-SCOPE | A (correctness) / F (honest documentation) | Spec `z7nbn1` OQ-01 Resolution: "When `--follow-generated` is implemented (owner backlog `x8diyb`), that flag becomes the opt-in mechanism for the same-run behavior"; `Blocking: yes`, `Owner: maintainer`, ruled 2026-09-16 | THE PLAN CORRECTLY REFUSED TO EDIT A MAINTAINER RULING AND THEN LEFT IT CONTRADICTING ITSELF. E-05 rewrites 3.4 (which names the flag) and explicitly does not touch OQ-01 (which also names it, as the future mechanism). That is the right call on authority, but it leaves one spec asserting the flag was removed and another paragraph of the SAME spec pointing a reader at it as the path forward, with nothing reconciling them. Nothing in the plan required the 3.4 replacement to carry a forward pointer, so the reconciliation depended on the executor noticing. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now REQUIRES the 3.4 replacement to carry a forward pointer saying the ruling's named mechanism was removed and why, states that leaving OQ-01 verbatim is deliberate (a dated ruling is not a reviewer's to rewrite), and records why the substance is unaffected: the ruling's operative decision is "NO FOLLOW FOR NOW ... the default stays report-only", and removal makes report-only the only behavior. V-05 now demands both the pointer sentence and a `git diff` showing the OQ-01 block UNCHANGED. OQ-02 was rewritten to put this reasoning in front of the maintainer explicitly. |
| PR-005 | MEDIUM | IN-SCOPE | G (executability) | The plan's `## Approval and execution gate` (two sentences before the fix); E-03's `/tmp/opencode/g2/probe-followgen/` absolute path | THE GATE CARRIED ALMOST NO EXECUTION CONTRACT and omitted the two things specific to this change: that it removes a PUBLIC CLI surface (after E-02 an existing operator command line fails with argparse exit 2 instead of the current `RunFlagRefusal`, which is the intended improvement and still a breaking surface change), and that TEST-FIRST is the only guard left (PR-003a). E-03 also named a machine-local absolute `/tmp` path, the kind of string the leak-sanitizer exists to keep out of shared output and which will not exist elsewhere, and probed only the harmless `False` polarity. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten with: OQ-01/OQ-02 dispositions plus an explicit do-not-re-decide instruction and the fully-specified alternative; the public-surface-removal disclosure; a do-not-reorder rule tied to the deleted contract test; a DECLARATION-style scope fence (make-then-justify, no stop-over-scope) naming the genuinely-unsafe cases; the two declared spec edits with the approved-spec status, the do-not-touch-OQ-01 limit and the `aw specs note` requirement; the honesty rule naming V-01's failing paste and V-03's both polarities; commit discipline with the no-dashes CHANGELOG rule; the conditional transition; and the backlog follow-up. E-03 now runs in-workspace with no absolute path and probes BOTH polarities (measured at review: a stale `True` and a stale `False` both return `False` without raising). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-004: the `z7nbn1` OQ-01 ruling will name a flag that no longer exists. Should the review edit the ruling, escalate removal as `Blocking: yes`, or reconcile from 3.4? | Reconcile from 3.4: require a forward pointer, leave the ruling verbatim, and put the reasoning to the maintainer in OQ-02 at `Blocking: no`. | (a) Editing the ruling text. Rejected: it is a dated maintainer ruling, and rewriting one to fit a plan is the forging failure AGENTS.md names. (b) Raising OQ-02 to `Blocking: yes`. Rejected: no behavior changes under either answer, so nothing is at risk while the human has not answered, and the plan is executable either way. | The ruling's operative decision ("NO FOLLOW FOR NOW ... default stays report-only") is STRENGTHENED by removal, since report-only becomes the only behavior; only its forward-looking mechanism name goes stale. The 2026-09-10 maintainer ruling makes a non-blocking question not-a-NO-GO, and the `- Blocking:` flag exists to mark what must stop work. | yes |
| D-2 | PR-002: `- Carrier: z7nbn1` is refused because the target is a spec. Fix the field, or file a backlog item to be the carrier? | Use `- Carrier-Evidence:` naming the spec file, and record why `- Carrier:` is refused. | Filing a new backlog item purely to satisfy the field. Rejected: it would mint an artifact to satisfy a checker rather than to track work, and the obligation genuinely IS owned by `z7nbn1`, which is a real in-tree artifact the evidence form resolves. | `check_engine._CARRIER_TARGET_TYPES == ("backlog","plans")` with a comment recording that a spec carrier was "offered to the maintainer and REJECTED"; `Carrier-Evidence` resolves through the same shared `resolve_evidence_artifact` the backlog `--evidence` route uses. Re-measured 0 findings after the change. | yes |
| D-3 | PR-001 also affects two OTHER pending plans (`01reg8`, `1g4i1t`) that declare the same dead spec path. Fix them here? | No. Fix this plan; name them in Finding 9 as a finding against them. | Correcting all three. Rejected: they are not in this review's ledger, and a reviewer editing plans it did not review leaves diffs with no findings record behind them. | `plan-review` Step 0.1 (the ledger is the named target plus documented additions; evidence-only files are out of scope). Consistent with the same decision taken in the `u8tabj` and `nomhl1` reviews of this sweep. | yes |
| D-4 | Should this review verify the removal's SAFETY by simulating it, given no test guards the surface? | Yes: simulate the row deletion in-process and check what `refuse_unimplemented_run_flags` would iterate. | Trusting the plan's reasoning. Rejected: PR-003 shows the plan's own inherited facts about this surface were stale, so its reasoning about the surface needed independent measurement. | Simulated: removing the row leaves 14 rows and ZERO `implemented=False`, so the refusal loop becomes a no-op and the function is correctly KEPT rather than deleted (which is what E-02 already said, now with evidence). Also measured both host parsers' exit-2 behavior for an unknown flag, which is what E-01(b) relies on. | yes |
| D-5 | E-02's expected outcome demands zero `follow.generated` hits in `agent_workflows`, but E-02 also REWRITES a docstring that currently contains the name. Is that a contradiction to flag, or a constraint to state? | A constraint to state: the rewrite must name no specific flag, which satisfies both halves. | Flagging it as a contradiction and relaxing the zero-hit expectation. Rejected: the zero-hit check is the useful one, and a docstring that still names a removed flag is itself a defect. | Measured 3 current hits, all in `runner_shared.py`: two in the row (deleted) and one in the docstring (rewritten). Also confirmed `rg` honors gitignore so the `__pycache__` `.pyc` that `grep -r` matches is correctly skipped, meaning V-02's command is sound as written. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author           --agent hzdq8y -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize  --agent hzdq8y -> {"outcome":"clean","exit":0,"findings":0}  (after revisions)
ipd_lint.lint_file(hzdq8y)  -> conforming, 0 diagnostics, 0 advisories
check_engine.evaluate_durable_carrier  BEFORE -> 1 finding, error, TWO obligations
                                                 (deferred row `Carrier: z7nbn1` + OQ-02)
                                        AFTER -> 0 findings

--- THE PLAN'S CASE FOR REMOVAL, REPRODUCED (Findings 1 to 4 all hold)
run_selection_policy.ACTION_PLAN            == "plan"
runner_shared.ACTION_CHOICES                == ("review", "plan", "execute")
runner_shared.ACTION_IMPLEMENTED            == frozenset({"review"})     -> "plan" NOT implemented
  and `--action plan` raises DriverError "is not implemented yet ... No run was started"
files_changed / recommended_next_action     2 occurrences in the whole package, both inside the
                                            prompt text SENT to the agent (runner_shared)
grep for .get("files_changed" / .get("recommended_next_action")  -> ZERO hits (never parsed back)
RUN_POLICY_FLAGS                            15 rows
rows with implemented=False                 EXACTLY ONE: ('--follow-generated',
                                              'backlog x8diyb (rundepflags-01)')
--with-dependencies implemented             True    <- Finding 8: the docstring is already stale
"--follow-generated" in RUN_POLICY_FLAGS_BY_FLAG   True   (E-01(a) is falsifiable)
"follow_generated" in RUN_POLICY_FLAGS_BY_DEST     True

--- E-01(b) MECHANISM CHECK (both hosts)
oc  parser: ACCEPTS --follow-generated today, follow_generated=True
agy parser: ACCEPTS --follow-generated today, follow_generated=True
oc  parser: unknown flag -> SystemExit code=2      (so the post-removal assertion is correct)
agy parser: unknown flag -> SystemExit code=2

--- SIMULATED REMOVAL (D-4)
rows after deleting the row      14
unimplemented rows after         []      -> refuse_unimplemented_run_flags iterates ZERO rows,
                                            so KEEPING the function (as E-02 says) is right

--- E-03 RESUME SAFETY, BOTH POLARITIES (the plan probed only False)
apply_run_policy_flags_on_resume({"options":{"follow_generated": False}}, Namespace()) -> False, no raise
apply_run_policy_flags_on_resume({"options":{"follow_generated": True }}, Namespace()) -> False, no raise

--- PR-001 THE DEAD SPEC PATH
declared .aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
   exists -> False
actual   .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
   exists -> True   (- Status: approved, - Blocks-Release: next, - Id: 25kzda)
ipd_lifecycle._scope_match(actual, declared) -> False
other pending plans declaring the SAME dead path: 01reg8, 1g4i1t   (a finding against them, not fixed here)
the plan declaring the CORRECT id6 path: 9x7otz
ipd_lint.check_scope_paths validates the GRAMMAR only, never existence -> no tool catches this

--- SPEC EDIT SURFACE (E-04's enumeration is complete)
rg -c "follow-generated" <real 25kzda path>  -> 9
the 9 sites: 2.1 synopsis | --full-auto "does not imply" list | the 2.1 bullet |
  the recorded-but-excluded endpoint | TWO dispatch-table cells (approved row, open row) |
  DAG rule 10 | consent-table "Generated child" row | the spec09 worked example
consent-table row reads: | Generated child | User may choose a new run, or original command may
  include --follow-generated | Requires original --follow-generated |   <- BOTH cells are the flag,
  so it needs a decision, not a reword (now stated in E-04)
z7nbn1: rg -n "x8diyb" -> 2 hits, line 139 (section 3.4, which E-05 rewrites) and line 228
  (the OQ-01 ruling, which E-05 must NOT touch)

--- PR-003 THE DELETED CONTRACT TEST
tests/test_run_flag_surface.py                 does NOT exist
deleted in                                     19313eed "test: trim test suite from 9,136 to under 2,000"
tests/ hits for "follow.generated"              ZERO
tests/ hits for "NOT YET IMPLEMENTED"           ZERO
tests/ references to RUN_POLICY_FLAGS           ONE, and it is about --allow-concurrent-driver
   => nothing guards this surface; E-01 is the only guard, hence test-first is load-bearing
rg honors gitignore, so agent_workflows/__pycache__/*.pyc is skipped -> V-02's command is sound
   (grep -r DOES match the .pyc, which is why the plan's `rg` spelling matters)

--- BACKLOG STATE
ceauac  graduated, Graduated-To: followgen, Work-Kind feature, Priority medium, NO Blocks-Release
        -> the follow-up close will not fail closed; HANDOFF in place via From-Backlog
x8diyb  done, Blocks-Release: next, and evaluate_blocking_close -> legitimate=True path=HANDOFF
        (handed to executed plan dhycim, which carries From-Backlog: x8diyb and the same gate).
        NOTE dhycim's own Scope says it "EXCLUDES --follow-generated ENTIRELY", so x8diyb closed
        with half its stated scope unbuilt. That is the pre-existing state this plan RESOLVES by
        removing the unbuilt half rather than leaving it advertised; recorded here because the
        closure looks anomalous until you see this plan.
CHANGELOG pending heading: "## 2.0.0 (pending) - AW project layout, storage backends, install
        wizard, and operational state"
```

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. PR-001 through PR-005 all FIXED, none deferred, none open. The plan's
central argument for removal was independently reproduced and is sound; the revisions repair a dead
path that would have defeated the scope gate and two of its own verifications, two carrier obligations,
two stale inherited facts, an unreconciled spec contradiction, and a thin gate.

Readiness `go-pending-approval`. Three things a human should know before approving. FIRST, this removes
a PUBLIC CLI flag: after execution an operator's existing `--follow-generated` command line fails with
argparse exit 2 rather than today's explicit refusal. That is the intended improvement and it is still
a breaking surface change, which is why the CHANGELOG bullet is mandatory. SECOND, OQ-02 asks the
maintainer to confirm that removal sits with their 2026-09-16 `z7nbn1` OQ-01 ruling, which names this
flag as the future opt-in mechanism; the default is to proceed (the ruling's operative "report-only"
decision is strengthened, not weakened), and the cheaper alternative is fully specified in-plan if they
would rather keep the reservation. THIRD, nothing in the test suite currently guards this flag surface,
because the contract test that did was deleted in the suite trim, so E-01's failing-first run is the
only evidence this change is what it claims to be.
