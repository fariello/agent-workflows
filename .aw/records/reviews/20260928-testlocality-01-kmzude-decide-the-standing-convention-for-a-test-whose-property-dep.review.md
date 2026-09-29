# Review findings: plan kmzude

- Subject-Id: kmzude
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `52d32b49` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and after revision `--phase
review-finalize` conforms with ZERO advisories and zero diagnostics. No pre-review snapshot was owed:
the plan was committed and unmodified. No production or test file was modified by this review. The
skip-visibility probe was created under the gitignored `.aw/state/`, never under `tests/`, and was
DELETED after measurement; `git status --porcelain` was empty before and after.

THE PLAN'S CENTRAL ARGUMENT IS CORRECT AND WAS REPRODUCED IN FULL. Every one of E-01's four authoring
baselines held independently (recorded as new F12). F1: a probe test skipping with a stated reason
under bare `python3 -m pytest` yields `1 passed, 1 skipped` with `grep -c` on the reason string
returning `0`, and that holds BOTH under the configured `-n auto` and with `-n0`, so the silence is
not an xdist artifact. Adding `-rs` prints
`SKIPPED [1] ...: UNIQUEPROBEREASON ...` under `short test summary info`, which localizes the cause to
the absent `reportchars` exactly as the plan says. F2: a bare run of a `livecorpus`-marked module
prints `NOTE: 1 tests were deselected by -m/-k and did not run (the default run skips 'slow' and
'livecorpus'); run everything with: make test-all`, and `release-review/08-final-ship-review.md`'s
`make test-all` / `-m ''` requirement is quoted accurately. CI's `-rfEs` is at
`.github/workflows/tests.yml:77`. F3 reproduced at per-test granularity: from a temp CWD,
`test_tracked_orchestrators_mostly_parse` SKIPPED while `test_every_refusal_states_a_reason` PASSED,
which is the vacuous pass. F4, F5, F6 and F7 all hold, and F6's carrier `3wofej` exists with the right
summary. F8's dead-citation catch is correct and is the best thing in the plan: the recommended file is
absent, `git log --diff-filter=D` names `19313eed`, and D78 does contain "had started passing
vacuously", so the live replacements are both real. P16's two `###` subsections and the
mutation-sensitivity bullet are quoted correctly, and `CONTRIBUTING.md`'s delegation pattern is as
described.

WHAT REVIEW FOUND IS THAT E-04's MECHANISM WOULD HAVE DEFEATED THE PLAN'S OWN PROHIBITION.

**"OPTION TWO GOVERNS" LOSES COVERAGE INSTEAD OF FIXING THE DEFECT (PR-A01, HIGH).** E-04 concluded
that the property "genuinely requires the live corpus, so option one (synthesize) does not apply and
option two governs", and left the mechanism to the executor. The only marker that fits this class is
`livecorpus`, and it is IN THE DEFAULT DESELECT SET (`addopts = ... -m 'not slow and not
livecorpus'`). CI's only full-suite step is `python -m pytest tests/ -n auto -rfEs` with no `-m ''`;
the sole `-m ''` invocation in the repository is `Makefile:31` (`make test-all`). So marking the class
removes both tests from every default local run AND from CI, leaving them at `make test-all` and
release-review only. Simulated by deselecting the class, the file drops from 36 to `34 passed`: both
corpus tests silently stop running. That is the outcome the plan's OWN second prohibition forbids ("do
NOT make both tests skip unconditionally to make the class quiet; that trades a vacuous pass for no
coverage"), reached by a different route, so E-04 as authored contradicted the gate as authored. FIXED
by redirecting E-04 at the ROOT CAUSE: the corpus is not genuinely absent, it is merely not where the
CWD-relative glob `.aw/records/plans/*/*.ipd.md` points, so anchoring the enumeration to the
repository root derived from the test module's own location removes the location dependence entirely,
which is what the rule's FIRST option prescribes and which deletes the skip and the vacuous pass
together. Verified nothing else is at stake: from the repository root both tests already pass
(`2 passed`), so anchoring changes only WHERE they look. Option three is retained as a documented
fallback with V-04 requiring the executor to say why anchoring failed; option two is explicitly
REFUSED for this class. Recorded as OQ-02 because it overrides an authored design choice, and E-02's
rule text now states option two's cost so the next author does not repeat the error.

**`OQ-01` ASSERTS AN ATTESTATION THE AUTHOR DID NOT HAVE (PR-A02, MEDIUM).** The question carried
`- Owner: maintainer` while its own rationale opens "RESOLVED AT AUTHORING FROM REPOSITORY EVIDENCE".
On a resolved question that field means the maintainer answered; a self-resolved question records the
reviewer or the plan author. This is precisely the case the workflow flags as passing every mechanical
check: measured, `ipd_lint` computes `has_owner` as `bool(oq.get("Owner","").strip()) and ... !=
"none"` and hands `ipd_schema.open_question_error` a bare boolean that never sees the value. FIXED to
`plan author` with the reasoning recorded in the rationale; the answer and its basis are untouched.

**THE SOURCE ITEM'S "NO TEST NEEDS THIS TODAY" PREMISE IS FALSE (PR-A03, LOW).** The item filed this
`low` on the reasoning that the question "becomes live the moment someone writes one". The plan's own
F3 found a test that both exists and is already producing the failure mode. That is a second
correction to the item beside F8's, and it strengthens the plan: E-04 is a real defect fix rather than
a demonstration. FIXED by recording it in the Proposed-changes review note; `Priority: low` and
`followup` are left unchanged on F7's reasoning, which review re-checked and upheld (the `Makefile`
and both CI pytest steps invoke from the repository root, so no gate runs the weakened form).

**THE GATE LACKED CONDITIONAL FINALIZE OWNERSHIP AND A RE-REPRODUCTION STOP (PR-A04, LOW).** The gate
said to "move this plan to `.aw/records/plans/executed/` via `aw ipd finalize`" unconditionally, with
no runner-versus-hand ownership split and no `git mv` prohibition, and carried no instruction to
re-verify the defect still reproduces. The latter matters here because this plan's own F8 shows the
source item's evidence had already gone stale once. FIXED: the gate now carries the unconditional
finalize obligation with conditional ownership, the `git mv` prohibition, a re-run-F1/F3-first stop
condition with review's reproductions as the baseline, and a pointer to F9.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. OQ-01's ANSWER survives review and is upheld: its premise-refuting measurement reproduced
exactly, and the ordering it records is unchanged. New OQ-02 records the E-04 mechanism reversal,
which vindicates the ordering rather than disturbing it by showing option one reaches further than the
author assumed. The four Deferred rows were each checked; three Carrier-Declined rows are honest
(notably the P6 argument against a speculative marker, which review independently agrees with given
that `livecorpus`'s rationale is blast radius and not location), and `3wofej` carries F6 correctly.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-A01 | high | IN-SCOPE | D. Anti-regression / E. Testing | `pyproject.toml` `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`; `.github/workflows/tests.yml:77` `run: python -m pytest tests/ -n auto -rfEs` (no `-m ''`); only `-m ''` is `Makefile:31`; measured `34 passed` with the class deselected versus 36 with it | E-04's "option two governs" would remove both `TestCorpusNoRegression` tests from the default local suite AND from CI, losing coverage instead of fixing the vacuous pass, which the plan's own second prohibition forbids by another route. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | E-04 redirected at the CWD-relative glob so option ONE applies (anchor to the repository root), with option three as a documented fallback and option two explicitly refused for this class; E-02's rule text now states option two's cost; new F9; recorded as OQ-02; the gate's second prohibition now names the marker route. |
| PR-A02 | medium | IN-SCOPE | G. Plan executability (attestation integrity) | `OQ-01` `- Owner: maintainer` against its own rationale "RESOLVED AT AUTHORING FROM REPOSITORY EVIDENCE"; `ipd_lint`'s `has_owner` computed as non-empty-and-not-`none` and passed to `ipd_schema.open_question_error` as a bare boolean | A resolved question claims the maintainer answered when the author resolved it, which is an attestation of another role, and no mechanical check inspects the value. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | `- Owner:` corrected to `plan author` with the reasoning and the linter measurement recorded in the rationale; the answer and its basis unchanged; new F10. |
| PR-A03 | low | IN-SCOPE | Evidence accuracy | backlog `5mc38x` ("no test in the tree needs the answer today ... It becomes live the moment someone writes one") against the plan's own F3, reproduced at review as `1 passed, 1 skipped` with the PASS being `test_every_refusal_states_a_reason` | The source item's premise is refuted by the plan's own measurement, a second correction beside F8's dead citation, and it changes how E-04 should be read. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Recorded in the Proposed-changes review note; `Priority: low` and `followup` left unchanged on F7's reasoning, re-checked and upheld; new F11. |
| PR-A04 | low | UNDER-SCOPE | G. Plan executability (execution contract) | the gate's unconditional `aw ipd finalize` instruction with no runner/hand split, no `git mv` prohibition, and no before-implementing re-reproduction | The execution contract was incomplete on the lifecycle transition, and carried no stop condition for a defect that has moved, which this plan's own F8 shows can happen. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Gate now carries the unconditional finalize obligation with conditional runner/executor ownership, the `git mv` prohibition, an F1/F3 re-reproduction stop with review's baselines, and a pointer to F9. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-04 chose the marker route for `TestCorpusNoRegression`, which loses coverage. Redirect it, or let the executor choose? | Redirect E-04 at the CWD-relative glob so the location dependence is REMOVED and the rule's option one applies; refuse option two for this class; keep option three as a documented fallback. | (a) Mark the class `livecorpus`: rejected on the measurement that it removes both tests from the default suite and from CI (36 -> `34 passed`). (b) Make the zero-corpus condition a hard FAILURE for both tests: rejected because it turns a red suite into the signal for an environmental condition and would fire for anyone running pytest from a subdirectory, and is unnecessary once the dependence is gone. (c) Leave E-04 as authored: rejected because the plan gave the executor no way to know that one of its two offered options loses coverage. | `addopts`' deselect set; CI's `-rfEs` step carrying no `-m ''`; `Makefile:31` as the sole `-m ''`; the deselect simulation; and the measurement that from the repository root both tests already pass, so anchoring changes only where they look. | yes |
| D-2 | `OQ-01` carries `Owner: maintainer` on an author-resolved question. Correct the owner, or reopen the question? | Correct the owner to `plan author`, leaving the question resolved and its answer intact. | (a) Reopen it as `- Status: open` with `Owner: maintainer`: rejected because the plan's reasoning is sound and evidence-backed, and reopening would assert an outstanding obligation that then needs a durable carrier, which the rationale already argues against. (b) Leave it: rejected because a false attestation passes every mechanical check and is exactly the forgery the workflow names. | The rationale's own "RESOLVED AT AUTHORING FROM REPOSITORY EVIDENCE"; `ipd_lint`'s value-blind `has_owner`. | yes |
| D-3 | Should the E-01 probe measurements be re-run at review, or accepted from the plan? | Re-run all four independently, and record them as pre-validated so a contradiction at execution reads as a real change in the tree. | (a) Accept them: rejected because the entire rule rests on one measurement (the reason-string count of zero), and a review that does not check the load-bearing digit is not checking the argument. (b) Re-run only (a): rejected because (c)'s asymmetry is the other half of the rule's justification. | Reproduced: reason count `0` parallel and serial; `-rs` printing the SKIPPED line; the `NOTE:` deselect line; `tests.yml:77`'s `-rfEs`. Probe created under `.aw/state/` and deleted. | yes |
