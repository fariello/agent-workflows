# Review findings: plan n7yaa6

- Subject-Id: n7yaa6
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-301 (HIGH, fixed), PR-302 (HIGH, fixed), PR-303 (HIGH, fixed), PR-304 (HIGH, fixed), PR-305 (LOW, fixed), PR-306 (LOW, fixed)

## Round 1

Reviewed at HEAD `1fbca3daa` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review; `--phase review-finalize`
reports `conforming` after revision. The plan is `- Kind: child`, so the `IPD-S407` orchestrator row check
does not apply. No production file and no test was modified by this review.

THE PLAN'S TECHNICAL CORE IS EXACT AND I RE-DROVE ALL OF IT RATHER THAN SPOT-CHECKING, because its entire
safety argument is an empirical no-op claim and such a claim is worth only as much as its reproduction.
F-03's randomized sweep reproduced with the IDENTICAL result: 2000 inputs over an alphabet mixing plain
ASCII, the VS pair `\u26a0\ufe0e`, the combining accent `e\u0301`, a zero-width space and the
ambiguous-width `\u25d5`, half ANSI-styled at a random color, widths 0 to 14, giving ZERO mismatches
against `_pad_visible`. F-02's byte-identity property reproduced with zero mismatches, and
`visible_width(styled) == visible_width(plain)` is True, which is the equality that makes E-03's
styled-text substitution sound rather than merely plausible. F-05 reproduced in BOTH of its independent
halves: `" " * -8 == ""` is True, so the guard is already implicit, AND `_abbrev_status` /
`_abbrev_readiness` produce ZERO results exceeding 8 and 9 columns across every lifecycle string, so
neither unguarded site can overflow in practice. F-08 reproduced exactly: 20 `ALL_STAGES` members, max
width 16 (`authority-queued`), 3 exceeding 12, 11 exceeding 8. F-07's MAY/MUST NOT sentence is verbatim in
approved spec `uonrjg` Section 9.4, so no amendment is owed.

F-04 DESERVES SPECIAL MENTION BECAUSE IT IS THE PLAN'S BEST REASONING AND IT HOLDS COMPLETELY. The backlog
item asked an open API question (an `align` parameter versus a right-aligning sibling function), and rather
than answering on taste the plan found the one real data-driven caller and let it decide.
`render_run_summary_table`'s `aligns` list measures at exactly 13 entries, 5 `"left"` and 8 `"right"`,
consumed by two `zip(..., aligns)` loops and branched on by two `if a == "right"` tests. A caller holding
alignment in a variable can forward it to a keyword parameter; it cannot dispatch between two
differently-named functions without keeping precisely the branch the helper exists to remove. That is a
decision grounded in shipped code, and choosing the parameter's values to match the strings that caller
already holds is the detail that makes adoption translation-free.

THEN I CHECKED WHAT A REFACTOR PLAN IS MOST EXPOSED TO, which is whether the tree moved under it. It did,
in three separate ways, and one of them is a latent runtime crash.

THE SHARPEST FINDING IS A CRASH THE PLAN'S OWN PROSE INVITES. Its conventions bullet describes `cli.py`'s
binding as "`_term_mod`/`term`", conflating the module with a `Term` instance. `cli.py` has exactly ONE
module import, `from . import term as _term_mod`. The bare name `term` at this plan's own second migration
site is an INSTANCE, and an instance carries neither `pad_visible` nor `visible_width`, both being
module-level functions (`hasattr(Term(), "visible_width")` -> False). What makes this a live trap rather
than a pedantic distinction is the shape of that exact site: `term.format_lifecycle_marker(...)` and
`term.style_lifecycle_text(...)` sit on the lines immediately above `_term_mod.visible_width(status_word)`,
so the two spellings are interleaved and both are correct in their place. An executor migrating by local
pattern-match would write `term.pad_visible(...)`, which raises `AttributeError` at runtime, and no
existing test exercises that code path, so neither E-06's suite run nor the three named width suites would
catch it. E-05's byte comparison would catch it only if the executor happened to drive that particular
inline attention row.

TWO MEASUREMENTS WENT STALE BECAUSE A SIBLING SHIPPED. F-06 asserts both siblings are unexecuted and
carries the plan's whole scope boundary on that. `it6tpj` is indeed still `pending/` and `approved`, but
`4taj2e` is `executed` (finalize `afb6635a7`), so `render_run_summary_table` exists today with FOUR inline
visible-width pads. The boundary SURVIVES on the half of the reason that is still true, and I want to be
precise about that because it would be easy to over-read this finding: `it6tpj` remains approved,
unexecuted, declares `render_stream.py`, and its E-02 does carry the quoted instruction not to reach for
the private helper, so editing that file here would still collide with an in-flight approved plan. What
does not survive is the arithmetic. "8 now, 43 after both siblings land" is superseded by measurement, and
`render_stream.py`'s share is now shipped debt a follow-up can take rather than a coordination hazard.

THE PACKAGE CENSUS IS TWELVE, NOT EIGHT, AND THE GAP IS A GREP ARTEFACT WITH AN OPERATIONAL CONSEQUENCE. A
multiline-tolerant scan reports `attention.py` 3, `cli.py` 2, `ipd_lint.py` 1, `render_stream.py` 4,
`run_viewer.py` 1, `term.py` 1 = 12. F-01's eight is CORRECT for the five modules this plan migrates, so
the remedy needs no change. But two of the twelve are line-wrapped, including `cli.py`'s second site whose
`max(0, 12 - _term_mod.visible_width(status_word))` spans four physical lines, and V-03 asked for a
single-line grep as its proof of completeness. That grep returns 8 and would have reported success while a
wrapped site remained, which is the same class of defect as the plan's own concern.

THE SUITE BASELINE MOVED IN BOTH DIRECTIONS. F-09 records `1 failed, 3419 passed, 2 skipped` and diagnoses
the failure correctly as a midnight date-rollover flake in `tests/test_backlog.py`, then instructs E-06 and
V-06 to EXPECT that failure and to compute a passed-count delta against 3419. At review the bare suite is
`3789 passed, 2 skipped` with ZERO failures and that test passes in isolation, the rollover having moved on
exactly as the diagnosis predicted. The diagnosis was right and the instruction built on it is now
misleading: an executor would hunt a failure that does not exist and reconcile against a total that drifted
by 370 in a day. The three named width suites are green together at review (`113 passed`).

Two judgements I checked and concur with. The `- Work-Kind: followup` with no release gate is correct:
backlog `45l00y` carries no `- Blocks-Release:`, the gating set is `bug` alone, and this is an API decision
rather than a defect, so nothing is inherited and inventing a gate would be a false claim. And keeping
`_pad_visible` as a one-line alias is right for the reason given rather than as compatibility theatre:
`it6tpj` names that symbol in prose in an approved, unexecuted plan, so deleting it would leave a reviewer
unable to check that plan's claim against the tree, for the saving of one line.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | IN-SCOPE | E (evidence accuracy) | `4taj2e` is `- Status: executed` under `.aw/records/plans/executed/` (finalize `afb6635a7`); `it6tpj` still `pending/`+`approved`; `render_run_summary_table` exists with 4 inline pads | F-06 asserts BOTH siblings are unexecuted and the Concern derives "8 to 43" from that. One has shipped, so `render_stream.py` already holds 4 pads and the projection is superseded. The scope boundary survives on `it6tpj` alone | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-06 rewritten with both states and the surviving reason; new F-06a; Concern, F-01, the Deferred row and the Scope check corrected; V-03 now counts the excluded sites |
| PR-302 | HIGH | IN-SCOPE | E (validation method) | Multiline census: 12 pads across 6 modules; single-line grep returns 8 and misses `cli.py:12490`'s four-line wrapped site | The package census is 12, not 8 (F-01's 8 is right for its five modules), and V-03's single-line grep as proof of completeness would pass while leaving a wrapped site unmigrated | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-06a records the method and the artefact; V-03 and E-03's Expected outcome now require a MULTILINE-tolerant census; E-03 tells the executor to locate the wrapped site by fragment and expect the four lines to collapse |
| PR-303 | HIGH | IN-SCOPE | A (correctness), G (executability) | `cli.py` has one module import, `from . import term as _term_mod`; at the second migration site `term` is a `Term` instance; `hasattr(Term(), "visible_width")` -> False; the site interleaves `term.style_lifecycle_text(...)` with `_term_mod.visible_width(...)` | The conventions bullet says `cli.py`'s binding is "`_term_mod`/`term`", conflating module and instance and pointing at the one spelling that raises `AttributeError`. No existing test covers that branch, so the suite would not catch it | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | The conventions bullet corrected; E-03 carries an explicit paragraph naming the trap, the measurement, and the required `_term_mod.pad_visible(...)` spelling; E-03's Expected outcome and V-03 both require the binding confirmed, with the `hasattr` check or an exercised code path pasted |
| PR-304 | HIGH | IN-SCOPE | E (anti-regression), G (live-artifact criteria) | Bare suite at review: `3789 passed, 2 skipped`, zero failures; the named flake `1 passed in 0.89s` in isolation; authoring recorded `1 failed, 3419 passed` | F-09 instructs E-06/V-06 to expect the date-rollover failure and to delta against 3419. Both moved: the failure is gone and the total rose by 370 in a day, so the executor would hunt a nonexistent failure and reconcile against a stale figure | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-09a records the drift; F-09 carries both measurements; E-06, V-06 and Required-tests now demand the executor's OWN pre-change baseline compared by failing-node-id SET, with quoted figures labelled orientation-only and a pre-existing failure carried forward rather than fixed |
| PR-305 | LOW | IN-SCOPE | E (evidence precision) | Review re-run of F-02's property: 48 comparisons, 0 mismatches, where authoring recorded 38 | The comparison count differs from the authored figure, which a re-measuring executor would report as a divergence; the zero-mismatch result (the load-bearing half) is identical | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 records both counts and states that the probe shape differs while the zero-mismatch property is what matters |
| PR-306 | LOW | IN-SCOPE | F (attestation hygiene) | The gate asserts "It carries no `- Readiness:` field by design"; the review now writes one | The self-description becomes false the moment a review runs, and a reader finding both the field and the denial cannot tell which is authoritative | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate paragraph now records that the field was correctly ABSENT at authoring and is present as an attested `/plan-review` output, with human sign-off still required |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `4taj2e` has executed, so `render_stream.py` now holds 4 shipped inline pads. Widen this plan to migrate them, or keep the exclusion? | Keep the exclusion and correct the stated reason | (a) Add `render_stream.py` to `Scope-Paths` and migrate all four: REJECTED, because `it6tpj` is still `approved` and unexecuted, declares that same file, and its E-02 carries a reviewer-approved instruction not to reach for the private helper; editing it would collide with an in-flight approved plan and contradict an instruction a reviewer signed off. (b) File a new carrier for the four shipped sites: NOT taken, because the existing Deferred row with `- Carrier: 45l00y` already holds the migration follow-up and a second record would duplicate it | `it6tpj` measured `pending/`+`approved` with `render_stream.py` in its `Scope-Paths` and its E-02 quoted; `4taj2e` measured `executed`; the plan's own Deferred row already carrying `45l00y` | yes |
| D-2 | The `cli.py` instance-versus-module confusion could crash at runtime. Fix the prose, add a test, or widen scope to cover that path? | Fix the prose in three places and require the binding be confirmed in V-03 evidence | (a) Require a new test exercising that inline attention row: REJECTED as scope widening on a path this plan only refactors; E-05's byte comparison already drives these surfaces and the correct remedy is to make the executor aware, since the error is a one-token spelling choice. (b) Note it once in E-03 only: REJECTED, because the misleading claim lives in the conventions section where an executor reads it first, so the correction has to be where the error is | `cli.py`'s single module import measured; `hasattr(Term(), "visible_width")` -> False; the interleaved spellings read in context at the migration site | yes |
| D-3 | F-09's baseline is stale in both count and failure set. Substitute the review figures, or change what the bar is? | Change the bar to the executor's own same-session baseline compared by failing-node-id set | (a) Replace 3419/1-failed with 3789/0-failed: REJECTED, because mine will be stale too; the total moved 370 in one day and the execution turn is a third moment, so pinning a fresh number repeats the defect with a newer value. (b) Drop the baseline requirement: REJECTED, because this plan's safety claim is "no regression" and that needs a comparison; what it does not need is a comparison against a figure from another day | measured 3419 -> 3789 passed and 1 -> 0 failed between `0855db80` and `1fbca3daa`; the plan-review convention requiring live-artifact criteria to be re-derived rather than pinned | yes |
| D-4 | Is `- Work-Kind: followup` with no release gate correct for what is arguably a latent-defect-prevention change? | Concur; no gate, and none invented | (a) Reclassify as `bug` with `- Blocks-Release: next`: REJECTED. Nothing is currently wrong in any rendered output; the plan's own evidence is that all eight sites are byte-for-byte correct today, so there is no user-perceptible defect, and the repository's gating set is `bug` alone. (b) Ask the maintainer: NOT taken, because backlog `45l00y` frames this explicitly as an API DECISION rather than a defect report and carries no gate, so there is nothing to inherit | `45l00y` carries no `- Blocks-Release:` and `- Work-Kind: followup`; F-02/F-03/F-05 establishing that current output is correct; AGENTS.md gating set default | yes |

### Verdict

APPROVE WITH REVISIONS APPLIED. Six findings, all FIXED in place, none deferred, none left open. No unfixed
finding at or above the `HIGH` gate threshold remains, so no escalation to a `- Blocking: yes` question is
owed. The single pre-existing open question (OQ-01) stays `- Blocking: no`, `- Status: deferred`, with
`- Carrier: 45l00y`, and its deferral reasoning was verified rather than restated: a combined fit form would
change what an overflowing cell renders at eight sites at once, and overflow is reachable (3 of 20 stages
exceed 12 columns, 11 exceed 8), so deferring it is what preserves the no-op property this plan's safety
rests on. `- Readiness: go-pending-approval` written. Human approval is still required before execution.
