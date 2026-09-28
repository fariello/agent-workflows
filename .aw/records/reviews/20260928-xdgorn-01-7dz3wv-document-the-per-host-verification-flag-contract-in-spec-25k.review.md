# Review: document the per-host verification flag contract in spec 25kzda and pin it with a test, child 7dz3wv (Set xdgorn)

- Subject-Id: 7dz3wv
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `c2815368`. `aw ipd lint --phase author --agent` reported `clean` (one advisory,
`IPD-Z602` on E-03's multi-part text) BEFORE semantic review, and `--phase review-finalize --agent`
after every revision. Every load-bearing claim was RE-MEASURED in this lane by driving the code, not
read off the plan, INCLUDING all three mutation results, each of which cost a full bare suite run.

THE PLAN IS UNUSUALLY GOOD AND ITS HARDEST CLAIMS ALL HOLD. The 24-cell dest table (F-01) reproduces
exactly, cell for cell, on both hosts and both subcommands. All three operator-visible consequences
(F-02) reproduce: `--verify`/`--audit` exit 2 on agy and are accepted on oc; the contradictory pair is
refused by `verification_flag_tristate` with `RunFlagRefusal` on agy in BOTH orders while oc parses it
silently and order-dependently (`--no-verify --validate` -> `validate=True`, reversed -> `False`); and
`agy resume --no-verify` exits 2 where `oc resume --no-verify` is accepted and yields `validate=False`.
F-03's falsification of the backlog item's safety-net premise is correct (the class greps to zero, both
files are deleted, in the commits named). F-04's quoted docstring is verbatim, including the
"must be RE-BASED and not deleted" instruction, so E-01 really is that instruction honored late. F-05 is
correct and the guard is non-vacuous: re-desting agy's `--no-verify` to `validate` makes `build_parser()`
raise `DriverError: internal: --no-verify resolves to dest 'validate', expected 'no_verify'`. F-13's
per-host defaults are right (`oc` False, `agy` True), which is what makes the resume asymmetry bite.

THE TWO MUTATION-GREEN RESULTS, WHICH ARE THE PLAN'S LOAD-BEARING EVIDENCE, BOTH REPRODUCE AT THIS HEAD.
F-06: adding a `--validate` `BooleanOptionalAction` to agy's `resume` parser leaves a full bare suite
fully green. F-07 reproduces with its asymmetry intact and is the sharper of the two: removing
`--verify`/`--audit` from oc's `start` fails exactly the one test the plan names
(`tests/test_oc_runipd.py::VerifierPromptTests::test_audit_flag_options`), while removing the SAME two
aliases from oc's `resume` leaves the suite fully green. So the plan's central claim, that this surface
is half-guarded and the unguarded half is invisible, is true as measured.

F-09'S PLACEMENT SIMULATION REPRODUCES TO THE NUMBER, and this is the finding I most expected to break.
Reconstructing the deleted test's `spec_grammar_flags` parser and running it against the live spec gives
exactly 17 declared flags, `owned - declared` EMPTY, `declared - owned` exactly `['--action']`, and none
of the six verification spellings present. Simulating the six inside the stanza grows `declared - owned`
to all six plus `--action`; simulating a new 2.1c subsection leaves both differences byte-identical. So
the placement decision is forced by the contract, as OQ-01 claims, and not merely preferred.

FOUR FINDINGS CHANGED THE PLAN. None touches the diagnosis; three are stale or incorrect evidence that
would have made a validation item unsatisfiable or a deferral rest on a false premise, and one is a
missed documentation defect measured while checking F-12.

FIRST, AND THE ONLY ONE THAT WOULD HAVE BLOCKED EXECUTION OUTRIGHT: EVERY BASELINE NUMBER IN THIS PLAN
IS STALE (PR-001). F-10 records the bare suite as `2937 passed, 2 skipped` at authoring HEAD `beb37773`.
At this HEAD it is `3149 passed, 2 skipped`, measured three times. 213 commits landed in between. This is
not cosmetic, because the plan makes that literal the comparison bar in four places, including
V-01(b)'s "state the delta against the F-10 baseline", which an executor cannot satisfy against a number
that was never true in their tree. The same staleness hits `aw check`: F-10 records "4 pre-existing
errors" naming three pending-plan frontmatter items plus `layout.json`; at this HEAD there are THREE, and
two of the three plan files named are different ones. The repair is to stop pinning a literal at all:
the plan now requires the executor to MEASURE the baseline at execution HEAD, record it, and compare
against their own measurement, with the authoring numbers kept as dated context. This is the plan's own
stated convention (its Step-0 bullet on dated snapshots, and the spec's own preamble warning that "a date
more than a few days old is probably wrong") applied to its own test counts, which is the one place it
did not apply it.

SECOND, A DEFERRAL RESTS ON A PREMISE THAT IS NO LONGER TRUE (PR-002). The `Carrier-Declined` on the
de-duplication row says the obligation "is already tracked as an OPEN MAINTAINER DECISION" and that
`s16omw`'s OQ-03 is "a live escalation whose answer is the maintainer's, not an agent's". It is NOT live:
`s16omw` OQ-03 reads `- Status: resolved`, `- Owner: maintainer`, and the maintainer ANSWERED it on
2026-09-16 with a directive to do the split ("at the end of the SET, there should be one code base shared
by the two runners that contains 100% of the otherwise redundant code"), explicitly ruling both stated
obstacles to be work rather than blockers. So the true state is worse than the plan describes and is
worth stating accurately: the de-duplication is DIRECTED work that was never performed (both hosts still
define their own `build_parser`; `runner_shared` defines none), the plan that was to do it is `executed`,
and the tests that pinned the contract it must preserve were deleted afterwards. That makes this plan MORE
valuable, not less, because it restores the guard a directed refactor will need. The deferral itself stays
correct on the Fix Bar; only its justification changes, and it now carries a carrier instead of declining
one, since no live artifact tracks the unperformed directive.

THIRD, `aw specs note` WORKS AND E-04'S HEDGE INVITES AN UNNECESSARY HAND-EDIT (PR-003). E-04 says to use
the tooled route but adds "if that verb cannot append to an `approved` spec without also moving its
status, do NOT force it, hand-append the line". Driven against this very spec: `aw specs note` appended
cleanly, `- Status: approved` was byte-identical afterwards, and the only diff was the one history line.
Its `--help` states it appends "WITHOUT changing its status", and the spec's own history shows the five
most recent amendments all logged by exactly this verb. Leaving the hedge in place invites an executor to
hand-edit a history block on a plausible-sounding pretext, which is the shape the untooled-status hook
exists to refuse. The conditional is now removed and the tooled route is mandatory, with the measurement
recorded.

FOURTH, A DOCUMENTATION DEFECT THE PLAN MEASURED PAST (PR-004). F-12 credits `docs/runner-profiles.md`
with documenting the start-subcommand difference "well" and faults it only for silence on resume. It also
contains an affirmatively FALSE host-unqualified claim: "Passing a contradictory pair such as
`--no-verify --validate` is refused before the run starts rather than resolved by precedence". Driven:
that is true on agy and false on oc, where the pair parses silently to `validate=False` and `oc_runipd`
has no `verification_flag_tristate` at all. So the doc tells an operator their contradictory pair will be
refused on a host where it will be silently honored, which is the same order-dependence F-08 measures and
is strictly worse than an omission. Recorded as F-14 and added to the existing `d8o2cv` carrier's scope
rather than fixed here, since the file is correctly out of `- Scope-Paths:`.

Smaller things I verified and did NOT raise, recorded so a later reader need not redo them. All four
existing test anchors E-01 and E-02 cite as idioms resolve in `tests/test_runner_shared.py`
(`AgyVerificationFlagSurfaceTests::test_tristate_parsing_options_and_distinct_flags` at `:2053`,
`VerificationPolarityTests` at `:1753`, `FollowGeneratedRemovedTests::test_host_parsers_reject_follow_generated_flag`
at `:4554`). F-11's blast-radius bound holds in substance: nine test files mention `25kzda` but only
`test_spec_25kzda_contains_no_follow_generated_token` reads THIS spec's bytes; the two files that read a
`.spec.md` read temp-dir fixtures or a different spec. All three declared carriers exist (`byazcp`,
`xvp5vx`, `d8o2cv`) and say what the plan claims. The insertion point is real: 2.1b ends at `:257` and
2.2 begins at `:271`. The `IPD-Z602` advisory on E-03 is a fair call on the (a)-(e) enumeration, but
splitting it would put one spec subsection across two E-items writing the same paragraph, which is worse;
left as an accepted advisory and noted in the plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing; G. Executability | plan F-10 and V-01(b)/V-03(f); measured `python3 -m pytest` bare x3 at HEAD `c2815368`; `git log --oneline beb37773..HEAD \| wc -l` = 213 | EVERY baseline literal in the plan is stale. F-10 pins `2937 passed, 2 skipped`; the actual bare suite here is `3149 passed, 2 skipped`. V-01(b) makes that literal the comparison bar, so an executor cannot satisfy it. The `aw check` baseline is stale too: F-10 says 4 pre-existing errors naming three specific pending plans plus `layout.json`; there are now 3, and two of the named plan files are different. A live-artifact count pinned as an acceptance bar is exactly what the plan-review rubric's re-derivation convention forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 rewritten to record its numbers as a DATED authoring snapshot and to require re-measurement at execution HEAD; V-01(b), V-03(f) and V-04(d) now require the executor to measure and record their own baseline and compare against it, naming the delta cause, rather than comparing to a literal. Requirement 2 in `## Required tests / validation` likewise de-pinned. |
| PR-002 | HIGH | IN-SCOPE | Step 1 evidence accuracy; C. Architecture | `.aw/records/plans/executed/20260915-rununify-10-s16omw-...ipd.md:293-330` (OQ-03: `- Status: resolved`, `- Owner: maintainer`, maintainer directive quoted); `grep -c "^def build_parser"` = 1 oc, 1 agy, 0 runner_shared | The de-duplication row's `Carrier-Declined` asserts the obligation is "already tracked as an OPEN MAINTAINER DECISION" and a "live escalation". `s16omw` OQ-03 is RESOLVED: the maintainer answered it on 2026-09-16 directing that the split be done and ruling both obstacles to be work, not blockers. So the deferral's stated reason is false, and the real state is that a DIRECTED refactor was never performed while the tests pinning the contract it must preserve were later deleted. Nothing live tracks it. | C:Low (the plan-level repair); U:Low; S:Low; F:Low; Overall:Low | FIXED | The row now states the accurate history (directed 2026-09-16, not performed, guard deleted afterwards), keeps the deferral on the Fix Bar, and REPLACES `Carrier-Declined` with `Carrier: xvp5vx` (whose scope already covers guards lost to the suite trim) plus the honest note that the unperformed directive has no live carrier of its own. The Goal and Under-scope now say the plan restores a guard a directed refactor will need. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness; F. KISS | `aw specs note --help` ("WITHOUT changing its status"); driven on this spec: history line appended, `- Status: approved` byte-identical, diff exactly one line; spec history shows the five most recent amendments all `note (aw specs)` | E-04 permits a hand-append to an approved spec's history block on the conditional "if `aw specs note` cannot append without also moving its status". Measured: it can, and does, and is the established route for this exact spec. Leaving the escape hatch invites the hand-edit the untooled-status pre-commit hook exists to refuse, on a pretext that is factually wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04's conditional removed; the tooled route is now mandatory with the driven measurement recorded inline, and the only permitted fallback is to STOP and report if the verb refuses. V-04(b) now requires pasting the verb's output rather than "state which route was taken". |
| PR-004 | MEDIUM | UNDER-SCOPE | Step 1 evidence accuracy; F. UX | `docs/runner-profiles.md:154-156`; driven: `oc start --validate --no-verify` -> `validate=False` silently, and `oc_runipd` has no `verification_flag_tristate` | F-12 credits `docs/runner-profiles.md` with documenting the start difference "well" and faults only its resume silence. The paragraph also makes a host-UNQUALIFIED claim that is FALSE for oc: "Passing a contradictory pair such as `--no-verify --validate` is refused before the run starts rather than resolved by precedence." On oc it is silently resolved by argparse last-wins. An affirmatively wrong statement is worse than an omission, and F-12 read the paragraph without testing its central claim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as new F-14; F-12's "well" softened to the measured truth; the `d8o2cv` deferral row now names BOTH defects (resume silence AND the false unqualified refusal claim) so the carrier's scope matches what was measured. Not fixed in-tree because the file is deliberately outside `- Scope-Paths:`. |

### Deferred and open

No finding is left `OPEN`, `DEFERRED`, or `REPLAN`, so `check.review-finding-unescalated` has nothing to
fire on and no `Blocking: yes` escalation is owed. The rows below record residues the PLAN defers (each
with a carrier in the plan's own Deferred section), not unfixed review findings.

| ID | Disposition | Reason | Remediation Risk | Axis | Required decision or evidence | Consequence if unresolved |
|----|-------------|--------|------------------|------|------------------------------|---------------------------|
| PR-002 (code residue, deferred BY THE PLAN) | DEFERRED | The directed `build_parser` de-duplication is a large refactor of two high-contention host runners whose oc-preferred reconciliation ruling provably cannot apply to this flag surface (F-05: the agy branch either raises at build time or silently steals a shipped spelling). Performing it inside a documentation plan would convert a zero-source-change plan into the largest behavior-risk change in the runner tree. | Medium-High | complexity; functionality | A mechanism that hands a shared core each host's own verification policy, which is what `s16omw` E-04 was to design and did not. | Both hosts keep their own `build_parser`, the 2026-09-16 directive stays unperformed, and no live artifact tracks it. Mitigated by this plan: after it, the contract a future split must preserve is declared in the spec AND pinned by a test, which is precisely what was missing when the guard tests were deleted. Carrier `xvp5vx`. |
| PR-004 (doc residue, deferred BY THE PLAN) | DEFERRED | `docs/runner-profiles.md` is deliberately outside `- Scope-Paths:`; operator-facing prose has a different audience and review standard than a spec section, and mixing it in would put user-facing text behind a spec-amendment gate. | Low | usability | One or two sentences correcting the unqualified refusal claim and adding the resume difference. | An operator reading the profiles doc is told a contradictory pair is refused when on opencode it is silently honored. Carrier `d8o2cv`, scope now naming both defects. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the stale `2937` baseline be UPDATED to `3149`, or de-pinned entirely? | De-pinned. The executor measures at execution HEAD, records it, and compares against their own measurement. | Updating the literal to 3149, rejected because it would be stale again within days (213 commits moved it in the plan's own lifetime) and would teach the next author to edit a number to match reality, which is the habit the deleted `test_run_flag_surface.py` docstring explicitly exists to break ("A literal count teaches the next author to edit the number to match the code"). | Measured `3149 passed, 2 skipped` three times at HEAD `c2815368` against the plan's `2937` at `beb37773`; the plan-review rubric's live-artifact re-derivation convention; the spec's own preamble requiring re-measurement of any dated claim. | yes |
| D-2 | Is the de-duplication deferral still valid now that its stated premise (a live maintainer escalation) is false? | Yes, the deferral stands; only its justification and carrier change. | (a) Withdrawing the deferral and folding the split into this plan, rejected on the Fix Bar (Medium-High complexity and functionality on two high-contention runners, in a plan whose whole guarantee is that no source file is in scope); (b) keeping `Carrier-Declined`, rejected because the premise that justified declining is measurably untrue and nothing live tracks the unperformed directive. | `s16omw` OQ-03 `- Status: resolved` with the maintainer's 2026-09-16 directive quoted in full; `build_parser` still defined once per host and zero times in `runner_shared`; no open backlog item names it (`baskrx` covers two different byte-identical symbols, not this one). | yes |
| D-3 | Should E-03 be split to clear the `IPD-Z602` density advisory? | No. Accept the advisory and note it in the plan. | Splitting (a)-(e) across two E-items, rejected because both halves would write the SAME spec subsection, so two items would contend on one paragraph and neither could be validated independently; the advisory is `info` severity and the linter reports `clean`. | `aw ipd lint --phase author --json` shows severity `info`, outcome `clean`, exit 0; the five parts are one subsection's contents, not five deliverables. | yes |
| D-4 | Does the false claim in `docs/runner-profiles.md` need fixing in this plan? | No. Record it as F-14 and extend the existing `d8o2cv` carrier's scope. | Adding the doc to `- Scope-Paths:`, rejected because it would break this plan's structural guarantee that it changes no shipped surface and would put operator prose behind a spec gate; filing a NEW carrier, rejected because `d8o2cv` already owns exactly this paragraph. | Driven: `oc start --validate --no-verify` -> `validate=False`, no `verification_flag_tristate` on `oc_runipd`; `docs/runner-profiles.md:154-156`; `d8o2cv`'s own text already quotes and scopes that paragraph. | yes |
