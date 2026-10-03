# Review findings: plan uh9jsk

- Subject-Id: uh9jsk
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-001 (BLOCKER, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file in `pending/` was committed and byte-identical to the
lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review, and
both `--phase author` and `--phase review-finalize` report `clean` with zero findings after revision. The
plan is `- Kind: child`, so the `IPD-S407` orchestrator child-row check does not apply.

THIS IS A WELL-EVIDENCED PLAN AND EVERY ONE OF F-1 THROUGH F-8 REPRODUCES. I re-ran all of them rather
than reading them:

- F-1 reproduces. Substituting `verified` for `pending` on a scaffolded V-item and linting at `author`
  yields exactly `error` with the single diagnostic `IPD-S402 V-01: unknown validation result 'verified'`.
  ONE CORRECTION, recorded as PR-005: the `pre-transition` run emits FIVE diagnostics, not the three the
  finding lists, because a fresh scaffold also reports `IPD-S404 E-01: not 'performed' at pre-transition`
  and the advisory `check.ipd-dependency-unresolved`.
- F-2 reproduces exactly. `ipd_lint.check_states` is the only consumer, at two call sites, and wraps the
  schema's string verbatim into `Diagnostic(..., C_VALID_STATE, f"{lf.ident}: {err}")`. No wording lives
  in `ipd_lint`, so the Scope-Paths decision to exclude it is right.
- F-3 reproduces. `execution_row_error` returns `"unknown execution state '{0}'".format(state)` with the
  identical shape, and in both predicates the membership guard precedes the dict lookup as the finding and
  the `bogus` rows claim.
- The E-01 PRECEDENT reproduces verbatim: `validate_metadata`'s `Readiness` branch is literally
  `"unrecognized readiness value (expected one of " + ", ".join(sorted(READINESS_VALUES)) + ")"`, so E-01
  is a copy of a shipped shape rather than a new convention.
- F-4 reproduces. `test_every_state_combination_gets_its_verdict` asserts only `got is None` versus
  not-None, so a message enumerating nothing satisfies both `bogus` rows. E-02 is genuinely new coverage.
- F-5 reproduces AND UNDERSTATED ITS OWN CASE, which PR-006 and PR-007 now repair. The tuple and its test
  are as described, and appending does keep the matcher matching. What the finding did not measure is that
  `IPD-S404` is NOT in `retryable_finalize_finding_codes()` (`{IPD-S401, IPD-S402, IPD-S403}`), so its
  prose is its ONLY matcher, and a REWORDED form measurably returns
  `finalize_refusal_is_retryable() == False`. The deferral is therefore better founded than it claimed.
- F-6 reproduces. `ipd_lint` contains exactly one `!= "pass"` comparison, and the three-edit cost of adding
  a vocabulary member was measured directly (see PR-003).
- F-7's PROPERTY reproduces and its COUNTS have already drifted in one day (4080/1438/6/2 against the
  recorded 3891/1178/6/2), which vindicates the finding's own "re-derive rather than trusting these
  figures" caveat. Zero out-of-vocabulary values in either census.
- F-8 reproduces, and the file already carries a comment making exactly this point about a different
  surviving sentence, so E-03's constraint follows an established in-file precedent.
- The MANIFEST claim reproduces to both hash prefixes: recorded `87df6b29...` versus
  `manifest.hash_content` at HEAD `6e0e9afe...`, confirming the manifest is not a gate a template edit must
  satisfy. Both precedent commits (`49d5e00f`, `9e3ed86e`) are real and neither touched
  `managed-sections.json`.
- E-03's regeneration arguments match `tests/test_ipd_templates.py` exactly (`<set-id>`, `tmp1d6`, the two
  titles, orders 1 and 0), and I simulated E-03 end to end: both kinds still lint `conforming` at `author`,
  both name every member of both vocabularies, and `authoring_placeholders_resolved` is unaffected.

THE ONE BLOCKER IS A TEST THAT CANNOT PASS, and it is the kind that wastes a whole execution pass. E-04
instructed `assertNotIn("verified", scaffold)` as its negative direction. But the scaffold ALREADY contains
that substring at HEAD, before any change this plan makes: the `## Required tests / validation` placeholder
is the literal `TODO: how the executed plan is verified.`, and `verified` is a substring of `verified.`.
Measured: `"verified" in build_skeleton(kind="child", ...)` is True at HEAD, and the same for
`kind="orchestrator"`. So an executor writing the instructed assertion gets a test that is RED on arrival
and that no correct implementation of E-03 can turn green. The worse branch is that an executor "fixes" it
by deleting an unrelated placeholder. E-04 now scopes the negative to the two intro lines and expresses it
token-wise against the frozenset, which is both satisfiable and strictly stronger than pinning one word.

TWO HIGH FINDINGS ARE BOTH ABOUT PROOFS THAT WOULD NOT PROVE WHAT THEY CLAIM. V-02's second red proof
("temporarily add a member to `VALIDATION_RESULTS`") fails `test_the_state_tables_cover_their_closed_vocabularies`
FIRST, not the new content assertion, so it attributes a pass to the wrong guard. Measured both stages: with
only the frozenset member and its `_VALIDATION_RULES` entry, `pytest -x` exits 1 on the coverage test with
`Items in the second set but not the first: 'zzprobe'`; adding the legal and illegal `STATES` rows returns
`26 passed`, which is the state in which a missing enumeration is the only remaining cause of failure. And
the scope fence instructed "stop and report rather than broadening", which the 2026-09-01 maintainer ruling
specifically names as the wording to flag: a fence is a declaration the runner reconciles afterwards, not a
stop condition. Replaced with make-and-justify, plus ONE genuine stop condition (an absent prerequisite,
which is a different case the ruling preserves).

ON OQ-01 I DID NOT ANSWER, AND I WITHDREW THE CLAUSE THAT WOULD HAVE ANSWERED IT BY DEFAULT. The question
("should `IPD-S404` also name the vocabulary, accepting an edit to the send-back's prose trigger") is
genuinely the maintainer's: it is a risk-appetite call on a run-control mechanism, its `- Owner:` is
`maintainer`, and this run was non-interactive (`AW_EXECUTION_ROLE=worker`, neither stream a TTY), so there
was no channel on which to ask. Its closing clause read "silence is taken as accepting the narrower scope",
which would let the absence of a reply count AS the reply; that is struck (PR-008). What I did add is the
missing half of the evidence, so the maintainer can now decide from the record: the feasibility half was
already settled, and the RISK half is now measured, namely that the safe (append) and unsafe (reword) forms
differ by one editing choice with no author-time test signal between them.

READINESS IS `go-pending-approval` DESPITE THE `REVIEWED - OPEN QUESTIONS` VERDICT, and that required
resolving a genuine conflict in the controlling instructions rather than picking one. The workflow's
readiness table lists a `REVIEWED - OPEN QUESTIONS` verdict as a `NO-GO` condition, while the paragraph
immediately below it records the 2026-09-10 maintainer ruling that a NON-BLOCKING open question does not
make a plan `NO-GO`. I resolved it on repository precedent, which is decisive and one-directional: of 77
review records carrying this verdict, 66 of the corresponding plans carry `go-pending-approval` and 11
carry `no-go`, and the discriminator is exactly the blocking flag. Every `no-go` case I sampled
(`xtklpd`, `yku4ga`, `g1w58u`, `a6i03f`) carries a `Blocking: yes` question that is still `open`; every
`go-pending-approval` sample (`qhy3i3` (the ruling's own plan), `wlxkoz`, `r2i1b1`) carries zero. `uh9jsk`
carries zero blocking questions, so it falls on the `go-pending-approval` side. Recorded as decision D-5.

TWO MECHANICAL NOTES FOR FUTURE REVIEWS, because together they cost two round trips here and the second
one is a trap worth naming precisely.

FIRST, a `REVIEWED - OPEN QUESTIONS` verdict does not by itself attest a `- Readiness:` field.
`ipd_lint._REVIEW_EVIDENCE_RE` accepts `/plan-review`, `APPROVE`, `NO-GO` or `REJECT`, and
`REVIEWED - OPEN QUESTIONS` contains none of those tokens, so writing the field after
`aw ipd set reviewed ... -m "REVIEWED - OPEN QUESTIONS; ..."` yields `IPD-M107`. It is the ONLY
in-vocabulary verdict the attestation regex does not recognize on its own.

SECOND, AND THIS IS THE TRAP: the obvious fix (relabelling the history line to
`- <date> /plan-review (<actor>): <verdict>`, which is the shape the workflow's own template shows) CLEARS
`IPD-M107` and then TRIPS A DIFFERENT GATE. The `aw untooled-status` pre-commit gate refused the commit,
because `check_engine._has_matching_history_line` requires a history line whose LABEL TOKEN equals the new
`- Status:` value, i.e. literally `reviewed`, which is what `aw ipd set` writes and what a `/plan-review`
label replaces. So the two gates read the SAME line for different things: one reads the label, the other
reads the whole line for review evidence.

BOTH ARE SATISFIABLE AT ONCE, and the resolution is to keep the TOOL-WRITTEN label and put the verdict
token in the MESSAGE: `- <date> reviewed (<actor>): /plan-review verdict REVIEWED - OPEN QUESTIONS; ...`.
Measured against the real file: `_has_matching_history_line(text, "reviewed")` is True and
`_REVIEW_EVIDENCE_RE` matches, and both `--phase author` and `--phase review-finalize` report `clean` with
zero findings. Neither gate was weakened or bypassed and no `--no-verify` was used. Both are correct
fail-closed controls rather than defects; they are recorded so the next reviewer writes the line in a shape
that satisfies both on the first attempt, and so nobody "fixes" the untooled-status refusal by relabelling
away the attribution it exists to require.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | E (testing) / G (executability) | `agent_workflows/ipd_authoring.py` `_SECTION_BODY[S.H_REQUIRED_TESTS]` = `TODO: how the executed plan is verified.`; E-04 as authored | E-04 INSTRUCTED AN UNSATISFIABLE ASSERTION. Its negative direction said the scaffolded text "must NOT contain ... the specific word `verified`", but the scaffold already contains that substring at HEAD, inside the `## Required tests / validation` placeholder, before any change this plan makes. Measured: `"verified" in build_skeleton(kind="child", ...)` returns True at HEAD with no E-03 edit, and likewise for `kind="orchestrator"`. An executor following E-04 literally writes a test that is red on arrival and that no correct implementation can green, and the tempting "fix" is to delete an unrelated placeholder. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now scopes the negative to `_EXEC_INTRO`/`_VALID_INTRO` only and expresses it GENERALLY ("no token in the intro's rendered value list is outside the frozenset") rather than by naming one word, which is satisfiable and strictly stronger. A measured DO-NOT note records the trap, the exact placeholder string, and the measurement. V-04 updated to match and to additionally require proof that the negative assertion is GREEN against an unmodified scaffold. |
| PR-002 | HIGH | IN-SCOPE | E | `tests/test_ipd_schema.py::ExecutionAndValidationStateTests.test_the_state_tables_cover_their_closed_vocabularies`; V-02 as authored | V-02's SECOND RED PROOF WOULD HAVE ATTRIBUTED A FAILURE TO THE WRONG TEST. It said to add a member to `VALIDATION_RESULTS` "(with the `_VALIDATION_RULES` entry it needs to import)" and observe the new content assertion fail. Measured: with exactly those two edits, `pytest tests/test_ipd_schema.py -o addopts="" -x` exits 1 on the COVERAGE test with `Items in the second set but not the first: 'zzprobe'`, and the new assertion is never reached. The proof needs a third edit (a legal and an illegal `STATES` row); with it the suite returns `26 passed`, which is the only state in which a missing enumeration is the remaining cause of failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 now states the three required edits explicitly, names the coverage test that otherwise fails first, pastes both measured stages as the bar, and requires the executor to paste BOTH stages so the proof is attributable to the new assertion. |
| PR-003 | HIGH | IN-SCOPE | G (execution contract) | Plan `## Scope check` under-scope bullet and the `## Approval and execution gate`, both reading "stop and report rather than broadening" | THE SCOPE FENCE WAS WORDED AS A STOP CONDITION, which the 2026-09-01 maintainer ruling names specifically as the wording to flag. A fence is a DECLARATION so the runner can reconcile afterwards; instructing an executor to halt over a scope question is the wording that propagated into 224 executed plans and contradicts the work done to stop runs stranding unfinished turns. The correct requirement is that an out-of-scope edit be MADE and then JUSTIFIED, which `aw ipd finalize` already enforces via `--scope-reason`/`--scope-ack`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both sites now say make-and-justify with `--scope-reason`, citing the ruling and recording that the plan originally said otherwise. A genuine stop condition is stated SEPARATELY and correctly (if the `Readiness` enum-rendering precedent or the `ipd_lint`-interpolates-schema layering has moved, the design premise is void), which the ruling explicitly preserves as a different case. |
| PR-004 | MEDIUM | UNDER-SCOPE | D (anti-regression) | `tests/fixtures/conforming-orchestrator.md`; `tests/support.CONFORMING_ORCHESTRATOR`; the plan's under-scope note | THE "LEAVE THE NEIGHBOURING INTRO STRINGS ALONE" NOTE WAS ASSERTED, NOT MEASURED, AND IT NAMED THE WRONG FILES. It claimed `tests/test_ipd_lint.py` and `tests/test_oc_runipd.py` carry the string `Validation-state rule: inspect evidence separately.`; measured, only `test_ipd_lint.py` carries that sentence, while `test_oc_runipd.py` carries a TRUNCATED variant of the generator's own sentence. More importantly it omitted `tests/fixtures/conforming-orchestrator.md`, which is the ONLY file outside the module carrying the FULL `_VALID_INTRO` verbatim and therefore the one a reader would most reasonably suspect E-03 could break. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The note is replaced with a measured inventory of all three files, stating for each whether it contains the full `_VALID_INTRO`/`_EXEC_INTRO`, and recording that the fixture is NOT byte-compared to `build_skeleton` anywhere (it is consumed through `tests/support.CONFORMING_ORCHESTRATOR`), so E-03 cannot break it. The conclusion is unchanged; it is now evidenced. |
| PR-005 | MEDIUM | IN-SCOPE | A (correctness of the record) | `ipd_lint.lint_text(..., checkpoint="pre-transition")` over a scaffold with `- Result: verified` | F-1'S DIAGNOSTIC INVENTORY IS INCOMPLETE, which matters because V-04 asks the executor to reproduce it end to end. The finding lists three `pre-transition` diagnostics; the actual run emits FIVE, adding `IPD-S404 E-01: not 'performed' at pre-transition` and the advisory `check.ipd-dependency-unresolved`. An executor comparing counts would read a correct reproduction as a failed one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-1 now records the re-measurement, names both extra diagnostics, explains that both are properties of a fresh scaffold rather than of the substituted value, and directs V-04's end-to-end check to assert on the `IPD-S402` LINE rather than on a diagnostic count. |
| PR-006 | MEDIUM | UNDER-SCOPE | B/C (operability) / D | `runner_shared.finalize_refusal_is_retryable` Arm 1; `retryable_finalize_finding_codes()`; `ipd_lint.C_VALID_STATE`/`C_CHECKPOINT` | THE PLAN NEVER ESTABLISHED THAT E-01 ITSELF IS SAFE, which is the first question an executor will ask given F-5's warning: `IPD-S402` IS one of the codes the finalize retry path classifies, so rewording it looks like exactly the hazard F-5 describes. Unaddressed, a cautious executor could refuse E-01 by analogy, or an incautious one could proceed without knowing why it is safe. Measured: Arm 1 tests the leading CODE TOKEN against `retryable_finalize_finding_codes()` BEFORE the prose fallback, that set is `{IPD-S401, IPD-S402, IPD-S403}`, and a reworded `IPD-S402` line still returns `finalize_refusal_is_retryable() == True`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-9 recording the code-before-prose ordering, the measured code set, and the reworded-probe result; added a note under E-01 telling the executor not to apply F-5's caution by analogy, with the structural reason. This also sharpens WHY the `IPD-S404` deferral is correct rather than merely cautious. |
| PR-007 | LOW | IN-SCOPE | A | F-5 and F-7 as authored | TWO FINDINGS WERE WEAKER THAN THE EVIDENCE ALLOWS. F-5 asserted the `IPD-S404` risk without measuring the failure mode, so its deferral read as caution; measured, a REWORDED message returns `finalize_refusal_is_retryable() == False`, converting a bounded correction turn into a terminal failure, and `IPD-S404` has no code-keyed fallback. F-7's counts (3891/1178/6/2) are already stale one day later (4080/1438/6/2), which its own caveat predicted but which a reader might otherwise treat as a bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-5 now records the measured reword-returns-False result and the absent code fallback, turning the deferral from caution into evidence. F-7 records the re-measurement, confirms the PROPERTY is unchanged (including a clean `- Execution state:` census), reports the drifted counts, and states explicitly that the numbers are context and must not be used as an acceptance bar. F-6's count is likewise reframed as a ratio. |
| PR-008 | LOW | IN-SCOPE | G (honesty) / F | OQ-01's closing clause "silence is taken as accepting the narrower scope" | AN UNANSWERED QUESTION WAS MADE SELF-CLOSING. The clause let the absence of a maintainer reply count as the maintainer's reply, which defeats the purpose of recording the question: a question whose own `- Owner:` is `maintainer` cannot be answered by the reviewer's inability to ask it. This run was non-interactive, which is precisely the case in which the clause would have fired wrongly. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The clause is WITHDRAWN in a dated review-disposition note that states why, records that the run was non-interactive (`AW_EXECUTION_ROLE=worker`, no TTY), confirms the question stays `open` and `Blocking: no` (so it does not hold the plan, per the 2026-09-10 ruling), and adds the measured risk half of the evidence so the maintainer can decide from the record. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-04's negative assertion is unsatisfiable as written. Scope it to the intro lines, or drop the negative direction? | SCOPE it to the two intro lines and express it token-wise against the frozenset. | (a) Drop the negative direction: REJECTED, it is the assertion that stops a future edit satisfying the positive check by pasting an illustrative list containing a rejected value, which is a real way to make the scaffold actively misleading. (b) Keep it document-wide and delete the offending placeholder: REJECTED outright, that mutates an unrelated scaffold section to satisfy a test, which is the tail wagging the dog and is out of this plan's scope. (c) Keep it document-wide but exclude the one known line: REJECTED as brittle, it would re-break the moment any other scaffold prose used the word. | Measured `"verified" in build_skeleton(...)` is True at HEAD for both kinds; the source is `_SECTION_BODY[S.H_REQUIRED_TESTS]` = `TODO: how the executed plan is verified.`; the intro-scoped token check was measured to pass on a correct intro and fail on one advertising `verified`. | yes |
| D-2 | Should the review answer OQ-01 on the maintainer's behalf, given the run cannot ask? | NO. Leave it `open`, `Blocking: no`, `Owner: maintainer`, and add the missing evidence instead. | (a) Resolve it "no, the narrower scope is final" per the plan's own silence clause: REJECTED, that is the self-closing defect PR-008 fixes, and a reviewer's inability to ask is not the maintainer's consent. (b) Resolve it "yes" and widen scope: REJECTED, it is a risk-appetite call on a run-control mechanism and not the reviewer's to make. (c) Escalate it to `Blocking: yes` to force an answer: REJECTED, the plan's value genuinely does not depend on it and E-01..E-04 are complete without it, so blocking would hold a ready plan for a question its author correctly judged non-stopping. | The run is non-interactive: `AW_EXECUTION_ROLE=worker`, neither stdin nor stdout a TTY. The question's own `- Owner:` is `maintainer`. The workflow's Step 3.3 non-interactive exception says to leave questions explicitly OPEN. The 2026-09-10 maintainer ruling (plan `qhy3i3` OQ-01) establishes that a non-blocking open question does not gate a plan. | yes |
| D-3 | F-5 deferred the `IPD-S404` fix on an asserted risk. Accept the deferral, or require the fix? | ACCEPT the deferral, and strengthen its basis by measuring the risk. | Require the fix in this plan: REJECTED on the measurement. `IPD-S404` is absent from `retryable_finalize_finding_codes()`, so its prose is its only matcher, and a reworded message measurably returns `finalize_refusal_is_retryable() == False`, which converts a bounded correction turn into a terminal failure. The safe and unsafe forms differ by one editing choice with no author-time signal between them, so bundling it into a discoverability chore would put a run-control mechanism at risk for a nicety. | `retryable_finalize_finding_codes()` measured `['IPD-S401','IPD-S402','IPD-S403']`; `ipd_lint.C_CHECKPOINT == 'IPD-S404'`; the appended probe returned True and the reworded probe returned False; `tests/test_finalize_sendback.py::TheRetryTriggerIsAPositiveAllowlist` read as the pin. | yes |
| D-4 | The spec's Section 14 fenced example quotes the two intro sentences E-03 extends. Require a spec amendment? | NO amendment required; the plan's reasoning is correct and needs no change. | Require adding the spec to `Scope-Paths` and refreshing the example: REJECTED. The example is illustrative prose in a fenced block with no test comparing it to the generator (unlike the two templates, which `TemplateParityTests` byte-compares), and it is ALREADY stale at HEAD independently of this plan: it omits the shipped right-sizing clause of `_EXEC_INTRO` and is hand-wrapped. So it is not a contract this plan breaks. Amending an `implemented` spec as a side effect of a discoverability fix is also the wrong trigger, as the plan itself argues. | Spec Section 5.3 enumerates the four results and Section 9.2 demands `Result: pass`, so the vocabulary is already specified and E-01/E-03 only surface it; Section 10's diagnostic guidance is a SHOULD about stable codes and locations, which this plan preserves; Section 14's example read at HEAD and confirmed already divergent from `_EXEC_INTRO`; both precedent commits amended the spec because they changed the CONTRACT (new required fields), which this plan does not. | yes |
| D-5 | The workflow's readiness table lists a `REVIEWED - OPEN QUESTIONS` verdict as a `NO-GO` condition, while the paragraph below it says a NON-BLOCKING open question does not make a plan `NO-GO`. Which governs? | `go-pending-approval`. The blocking-flag ruling governs; the verdict alone does not force `no-go`. | (a) Follow the verdict literally and write `no-go`: REJECTED, it would contradict the 2026-09-10 maintainer ruling recorded in the same section, whose stated reasoning is that treating blocking and non-blocking questions alike discards the distinction the field exists to carry, and it would hold a plan whose author correctly judged its one question non-stopping. (b) Omit the field: REJECTED, the workflow states automation fails closed on an absent field, so omission would silently strand a reviewed plan. | Repository precedent is decisive and one-directional: of 77 review records with this verdict, 66 plans carry `go-pending-approval` and 11 carry `no-go`, and the discriminator is the blocking flag. Sampled `no-go` plans (`xtklpd`, `yku4ga`, `g1w58u`, `a6i03f`) each carry a `Blocking: yes` question still `open`; sampled `go-pending-approval` plans (`qhy3i3`, the ruling's own subject, plus `wlxkoz`, `r2i1b1`) carry zero. `uh9jsk` carries zero `Blocking: yes` questions. | yes |
