# Review: re-measure spec 25kzda's infrastructure paragraph and stop it going stale a third time, child wenmg4 (Set specfresh)

- Subject-Id: wenmg4
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `fc67605d`. Structural preflight `aw ipd lint --phase author` conformed (clean, 0 findings)
before semantic review, and `--phase review-finalize` conformed after the revisions. The plan carries no
`- Blocks-Release:`, correctly: backlog `sd2wz5` is `Work-Kind: chore` and carries no gate, and the plan
states that explicitly so a reader does not assume one was dropped.

DISCLOSURE: authored in the same repository and by the same model family as the plan, so treat this as a
near-self-review and worth less than an independent one.

I RE-MEASURED ALL FIVE ENUMERATED CLAIMS INDEPENDENTLY AND THE PLAN'S MEASUREMENTS ARE CORRECT. `From-Spec`
is recognized (`META_FROM_SPEC in META_RECOGNIZED` -> True); the trailers hold (0 across all refs); no
`Run contract` block in either driver; `HostSandboxCapabilities` carries 13 fields including all three
runner-safety ones with `mjx7ne` in `executed/`; `aw hooks install` does not resolve. Both cited shas
resolve. The plan's central judgement, that item 4 is MORE stale than the backlog item recorded, is right
and is the kind of correction-of-one's-own-source that this plan exists to make.

THE FINDING THAT MOST CHANGES THE PLAN IS THE ONE NOBODY LOOKED FOR: A SECOND PARAGRAPH IN THE SAME
PREAMBLE IS STALE THE SAME WAY. Four lines below the text the plan corrects, the Section 2.1 grammar
paragraph asserts that `run unverifiable`, `--allow-unverifiable` and `--unverifiable-ok` "all grep to
zero". All three exist: both flags are REGISTERED argparse options on `start` and `resume` on BOTH hosts,
declared `implemented=True` in `runner_shared.RunPolicyFlag`, and they landed in `08aab7ed` on 2026-09-05,
the SAME DAY that paragraph was measured. A plan whose entire purpose is de-staling this preamble would
have shipped having left a second false paragraph immediately adjacent, and would then have claimed the
spec de-staled. That is now E-05, inside the already-declared file and preamble, so it adds no scope path.

THAT ALSO RESHAPED THE PLAN'S REAL DELIVERABLE, E-03's DURABILITY DECISION. The preamble carries FOUR
point-in-time paragraphs of the same class, and TWO of them are now measured stale. A convention written
over one while three neighbors keep decaying is not a fix, it is a fourth thing to maintain. E-03 now
requires the decision be stated once in a form governing all four, which is the same sentence placed
better rather than more work.

THE SUITE BASELINE WAS WRONG IN BOTH HALVES AND MISNAMED THE FAILING TEST, which matters more than usual
here because this plan's ENTIRE validation criterion is a suite delta. The plan expects `1 failed, 5648
passed` at `tests/test_orchestrator_retirement.py`; that file PASSES (`112 passed`), and the real failure
is `test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`,
caused by the gitignored `opencode-recovery/` tree of ANOTHER party's transcripts. An executor holding the
wrong baseline could read a co-worker's artifacts as their own regression and "clean up" files that are not
theirs. Corrected, with an explicit prohibition and a node-id comparison replacing the count comparison.

THREE OF FOUR BYTE-PINNED REGIONS WERE UNNAMED. The plan names Section 4.2 only; Section 4.1's abort-class
table, Section 2.1's fenced grammar block and Section 2.5a's character-for-character fenced blocks are
equally pinned by tests that read the spec AS A FILE. I verified the declared edit cannot reach any of
them (the preamble has no fenced block and no `RUN-` table row, and the three files pass), so this is a
completeness fix rather than a live hazard, but naming one of four invites the inference that the rest are
free.

I ALSO CHECKED THE ONE THING THE PLAN FORBIDS RE-DOING, and found its conclusion overstated in a way worth
recording rather than repeating. The audit half IS closed for its own question, but "confined to one spec,
no spec family inherited it" is no longer true: `kw5y2s` (`approved`) asserts `aw check reviews` fails with
`unknown artifact type 'reviews'`, and at HEAD that verb succeeds. I did NOT fix it, because `kw5y2s` is
not in `Scope-Paths` and amending an undeclared second approved spec is exactly the drift the declaration
requirement exists to catch. It goes to the maintainer as non-blocking OQ-04.

Seven findings, all FIXED in place, no deferrals. One new non-blocking open question. E-items go from four
to five, V-items likewise, bijection intact.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | UNDER-SCOPE | G. executability; D. anti-regression | parser walk -> `--allow-unverifiable`/`--unverifiable-ok` on `oc start`, `oc resume`, `agy start`, `agy resume`; `agent_workflows/runner_shared.py:1938-1960` (`implemented=True`); `git log -1 08aab7ed`; spec `:53-54` | **A SECOND PREAMBLE PARAGRAPH IN THE SAME FILE IS STALE THE SAME WAY, FOUR LINES FROM THE TEXT THE PLAN EDITS, and the plan never looked at it.** The Section 2.1 grammar paragraph says `run unverifiable`, `--allow-unverifiable` and `--unverifiable-ok` "all grep to zero". All three exist; the two flags are registered argparse options on `start`/`resume` on both hosts, and they landed in `08aab7ed` on 2026-09-05, the same day that paragraph was measured. The plan would have corrected one false paragraph, left its neighbor false, and recorded that it de-staled the spec | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New E-05 corrects it inside the already-declared file and preamble (no new scope path), requires PARSER-derived rather than grep evidence, requires the still-true clauses re-measured before being left alone, and forbids widening into Section 2.1's own byte-pinned grammar block. New V-05, new F-11; Concern, proposed-changes, spec-sync and scope-check all updated |
| PR-902 | HIGH | IN-SCOPE | Evidence accuracy; E. testing | bare `python3 -m pytest` at `fc67605d` -> `1 failed, 5958 passed, 3 skipped, 2 xfailed` at `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`; `tests/test_orchestrator_retirement.py` -> `112 passed`; `.gitignore:49` | **THE SUITE BASELINE IS WRONG IN BOTH HALVES AND NAMES A TEST THAT PASSES, and this plan's ONLY validation criterion is a suite delta.** The plan cites `1 failed, 5648 passed` blaming `test_orchestrator_retirement`. That file passes. The real failure is the reporting-contract parity test, caused by the gitignored `opencode-recovery/` tree of ANOTHER party's session transcripts. An executor holding the wrong baseline could attribute a co-worker's artifacts to their own edit, or "clean up" files that are not theirs, which the shared-checkout rule forbids | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 and required-tests carry the re-measured baseline with the real node id, the cause, an explicit do-not-fix prohibition citing the shared-checkout rule, and a NODE-ID comparison replacing the count comparison (counts drift as other agents land tests). V-04 requires both node-id lists and confirmation the pre-existing failure survived. New F-12 |
| PR-903 | MEDIUM | UNDER-SCOPE | A. correctness; F. KISS | spec `:21-56`: four point-in-time paragraphs; F-1, F-2 and PR-901 show two of them stale | **E-03's DURABILITY DECISION, THE PLAN'S ACTUAL DELIVERABLE, WOULD HAVE COVERED ONE PARAGRAPH OF FOUR.** The preamble carries four paragraphs of the same class, three already dated, two now measured stale. A convention stated over the infrastructure paragraph alone leaves three neighbors decaying and becomes a fourth thing to maintain, which is the burden the plan is trying to remove | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now requires the convention be stated ONCE in a form governing all four paragraphs with each carrying its own date, framed as the same sentence placed better rather than added scope; V-03 requires the governing sentence quoted and all four shown covered. New F-14 |
| PR-904 | MEDIUM | IN-SCOPE | D. anti-regression; E. testing | `tests/test_run_evidence_completion.py:1024-1075`; `tests/test_run_flag_surface.py:44-120`; `tests/test_run_selection_policy.py:806-817`; preamble scan -> no fenced block, no `RUN-` row; those three files -> `261 passed` | **THREE OF FOUR BYTE-PINNED SPEC REGIONS ARE UNNAMED, so the plan implies the others are free to edit.** Besides Section 4.2, tests read this spec AS A FILE and pin Section 4.1's abort-class table, Section 2.1's fenced grammar block, and Section 2.5a's fenced blocks asserted character for character. Not a live hazard for the declared edit (verified: the preamble contains no fence and no table row), but a completeness gap in a plan whose safety argument is "stay out of the pinned region" | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 enumerates all four regions with their test anchors and records the verification that the preamble cannot reach them; V-04 requires all THREE spec-reading test files pasted passing rather than only the `RUN_FINDING_CODES` case; conventions section rewritten. New F-13 |
| PR-905 | MEDIUM | IN-SCOPE | Evidence accuracy | `_iter_type_files("specs", include_retired=True)` -> 29; `aw check specs` -> 13; `aw check reviews` -> exit 0, `152 reviews checked`; `'reviews' in artifact_types.ARTIFACT_TYPES` -> True; `kw5y2s:123` | **THE PLAN REPEATS THE ITEM'S "CONFINED TO ONE SPEC" CONCLUSION AS STILL-TRUE, AND IT IS NOT.** `kw5y2s` (`approved`) asserts `aw check reviews` fails with `unknown artifact type 'reviews'`; at HEAD that verb succeeds. The corpus size is also wrong in a third way (item said 24, plan says 28, actual is 29 files, while `aw check specs`'s 13 is the non-retired subset). A plan about stale factual claims asserting a stale factual claim is the specific irony worth avoiding | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern records the re-measured corpus, distinguishes the 29-vs-13 question, and states plainly that the item's conclusion survives for the `detrun` defect class but not as "confined to one spec". F-9 rewritten, new F-15 records `kw5y2s`, Deferred explains why it is reported and not fixed, spec-sync updated, OQ-04 puts the follow-up to the maintainer |
| PR-906 | MEDIUM | UNDER-SCOPE | E. testing; B. security lens on evidence | `git log --all --format='%(trailers:key=Co-authored-by,valueonly)' -400` -> 20 vs the same command with `AW-Run` -> 0; `git rev-list --all --count` -> 2936 | **THREE OF THE FIVE VERDICTS REST ON A COUNT OF ZERO WITH NO PROOF THE COMMAND WORKS, and a zero is equally the signature of a broken command or a typo'd trailer key.** The plan also scopes the trailer scan to a 400-commit window, which cannot distinguish "never used" from "not used lately" and would let the claim read as holding while the mechanism was live | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 requires the whole-history scan (0 of 2936, not 0 of 400) and a NON-VACUITY control for every zero: the identical trailer command with a key that does exist, and per-file counts for each grep so an unqualified bare `0` is not accepted. V-01 requires the control pasted. Concern's item 2 records the stronger measurement |
| PR-907 | LOW | OVER-SCOPE (pre-empted) | C. architecture; scope discipline | E-03's brief ("stop it decaying a third time") against `Scope-Paths` declaring one spec file | **THE OBVIOUS "REAL" FIX FOR A CLAIM NOTHING ENFORCES IS TO ENFORCE IT, and nothing in the plan tells the executor not to.** A helpful executor reading "nothing enforces this paragraph" could add a test or an `aw check` rule verifying spec factual claims. That is a code change in a plan declaring one spec file, and a design decision (what a spec may assert, what a check may fail on) belonging to a maintainer | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 explicitly forbids inventing an enforcement mechanism and directs that conclusion be reported as a finding rather than taken as scope; a matching Deferred entry states the two independent reasons; V-03 requires confirmation no test or check rule was added |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | A second preamble paragraph in the same file is stale the same way (PR-901). Fix it inside this plan, or file it separately? | FIX IT HERE as new E-05. It is the same file, same preamble, same defect class and same declared `Scope-Paths` entry, so it costs no new scope, and E-03's durability decision is incoherent if applied to one of two known-stale paragraphs | File a separate plan (rejected: a second plan editing the same preamble of the same approved spec would collide with this one and doubles the lifecycle cost for a one-clause correction); leave it and mention it in the report (rejected: the plan would ship claiming it de-staled this preamble while a false paragraph sat four lines from its own edit) | Both flags registered on `start`/`resume` on both hosts; `runner_shared.py:1938-1960` `implemented=True`; landed `08aab7ed` 2026-09-05, the paragraph's own measurement date; spec `:53-54` | yes |
| D-2 | `kw5y2s` carries the same defect class (PR-905). Fix it too, since I am already correcting stale spec claims? | DO NOT FIX IT. Report it as F-15, explain the exclusion in Deferred, and put the follow-up to the maintainer as non-blocking OQ-04 | Amend `kw5y2s` in the same change (rejected: it is not in `Scope-Paths`; the runners announce declared spec edits at run start and the finalize gate reconciles them, so an undeclared second approved-spec edit is exactly the drift that machinery exists to catch); say nothing (rejected: concealing it would repeat the item's own error, which is what this plan exists to correct) | `kw5y2s:123` vs `aw check reviews` -> exit 0, `152 reviews checked`; `'reviews' in ARTIFACT_TYPES` -> True; plan `Scope-Paths` names one file | yes |
| D-3 | E-03 offers three durability options and defers the choice to the maintainer as open OQ-01. Should this review pick one? | LEAVE THE CHOICE OPEN, but require that WHICHEVER option is taken must govern all four point-in-time paragraphs. That converts a scope defect into a constraint without pre-empting the maintainer's preference | Pick option (c) in review (rejected: OQ-01 is explicitly the maintainer's call about their own review process, and the plan already defaults to (c) if nobody answers, so deciding adds nothing and removes their choice); leave E-03 as authored (rejected: a convention covering one of four paragraphs leaves the decay mechanism running) | OQ-01 owner is `maintainer`; spec `:21-56` carries four such paragraphs; two measured stale (F-1, F-2, F-11) | yes |
| D-4 | The plan forbids re-running the spec audit. Does verifying its conclusion violate that? | RE-CHECK THE CONCLUSION, not the audit. I re-grepped the 29-file corpus once to test the claim the plan asks the executor to TRUST, and did not redo the item's per-spec analysis | Trust the closed-audit instruction literally (rejected: the plan's own thesis is that an unverified point-in-time claim decays, and "the audit is closed" is itself such a claim, made when the corpus was 24 files); redo the full audit (rejected: genuinely wasteful, and the plan is right that its answer is recorded) | Corpus 24 (item) -> 28 (plan) -> 29 (measured); the one exception found is `kw5y2s`, recorded as F-15 | yes |
