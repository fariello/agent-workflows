# Review findings: plan mzrr7x

- Subject-Id: mzrr7x
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `8a0c31093`. The plan file was committed and clean
(`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, ZERO findings) BEFORE semantic
review. This plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator
child-row check does not apply.

THE DIAGNOSIS IN THIS PLAN IS EXCELLENT AND I COULD NOT FAULT IT. I re-derived every load-bearing
measurement by driving the code rather than reading the prose, and the three-broken-links analysis is
correct link by link. What review found is a defect in the PRESCRIBED FIX, not in the problem
statement: the ASCII fill the plan specifies would ship a new user-visible wrong answer.

WHAT REPRODUCES EXACTLY:

- F-01 reproduces end to end. With `AW_ASCII_ONLY=1`, `term.should_unicode()` is False, and a
  `Statusline` built with a detector-fed `Palette(use_unicode=should_unicode())` still renders nine
  distinct non-ASCII code points: `0x2500 0x2502 0x252c 0x2534 0x256d 0x256e 0x256f 0x2570 0x2588`,
  with `'\u2502' in box` True. Built the way the runners ACTUALLY build it (`Palette(should_color(...))`
  with no `use_unicode`), the palette reports `use_unicode=True` despite the environment variable, and
  the same nine code points appear. Both halves of the claim hold.
- F-02 reproduces link by link. `format_progress_bar` signature is `(current, total, width=10)` with
  no `use_unicode` (link 7). `Statusline.__init__` has no `use_unicode` parameter (link 4).
  `Palette.__init__` is `(self, enabled, *, use_unicode=True)` so link 2 exists.
  `format_statusline_lines` does carry `use_unicode` (link 5). The only correction is the site COUNT,
  recorded as PR-003.
- F-03 reproduces precisely, and its consequence is real. Sweeping `current_idx` 0 through 10 with
  `total_items=10` at `use_unicode=False`: `0x2588` is present at every state 1 through 10 and the set
  is EMPTY at state 0, in BOTH styling modes. So a guard fixtured on `0/N` genuinely passes on the
  broken tree, exactly as the plan warns. The fractional branch leaks a different code point as
  claimed: `format_progress_bar(3, 80)` yields `0x258d`, and `79/80` yields `0x2588` plus `0x2589`.
- F-04 reproduces, and the plan's quoted rendering is accurate to the line. Writing the header through
  `cp1252` with `errors="replace"` gives
  `?Time     ? From start                ? set: s                   id6: i ?  Review ? Spend ? Tok ...`,
  matching the plan's quote; the box's top and bottom rules come back as solid `?` runs. An `ascii`
  stream raises `UnicodeEncodeError: 'ascii' codec can't encode characters in position 0-128`.
  `term.ensure_encodable_stdio` exists. The `bug` classification is earned on the repository's
  user-perceptible-impact test.
- F-05 reproduces in both halves, which is unusually good authoring evidence. Staging the proposed
  function out of tree: ASCII purity holds at all of `0/10`, `1/10`, `3/10`, `5/10`, `10/10`, `79/80`,
  `0/0` and `3/80`; width parity with the Unicode twin is EQUAL at every one (24 columns for the `/10`
  and `/80` cases, 22 for `0/0`, matching the plan's numbers); and the Unicode branch is byte-identical
  to the shipped function over 1105 `current`/`total` combinations with ZERO differences.
- F-06 reproduces. `grep -rln "format_statusline" tests/ agent_workflows/ tools/` returns only
  production files and no test; `tests/test_render_stream.py` does not exist; and a per-symbol census
  over `tests/` finds ZERO references for all thirteen statusline symbols I checked, including
  `Statusline` itself.
- F-07 reproduces. `it6tpj` is `- Status: approved` with `- Readiness: go-pending-approval`,
  `- Blocks-Release: next`, and `- Scope-Paths: agent_workflows/render_stream.py,
  tests/test_statusline_visible_width.py`. The same-function textual-conflict risk is real, and the
  plan's response (keep E-02 to one line) is the right one.
- F-09 reproduces. `render_run_summary_table(state, use_unicode=False)` emits `0x2502`, confirming the
  banner-separator half the plan defers, and the two `format_progress_bar(` call sites in
  `render_stream` confirm E-01 fixes the U+2588 half for both callers.
- F-10 and the spec/doc claims reproduce. Spec `uonrjg` really does carry
  "guaranteed single-byte alignment in ASCII mode" and names both variables in its Section 9.3
  sentence and criterion A12; `docs/cli-human-guide.md` really does promise the degradation. No spec
  edit is owed, as the plan says. I also checked A12's "use the exact fallbacks in section 5" clause
  against the fill-character question: Section 5 is the lifecycle-glyph table and says nothing about a
  progress bar, so the fill character is genuinely unconstrained and the plan is right to let the
  executor choose.

PR-001 IS THE FINDING THAT MATTERS, and it is a defect in the fix rather than in the diagnosis. The
plan prescribes `full = int(round(frac * width))` with a `"#"` fill, and measures purity and width
parity for it, both of which hold. What it does not measure is what the rounding does to the two
readings an operator actually takes from a progress bar. Driven:

    100% (80/80) -> [##########]
     99% (79/80) -> [##########]      <- IDENTICAL to 100%
      0% ( 0/80) -> [          ]
      1% ( 1/80) -> [          ]      <- IDENTICAL to 0%
      4% ( 3/80) -> [          ]      <- IDENTICAL to 0%

The shipped Unicode bar distinguishes every one of those (`[█████████▉]` vs `[██████████]`, and
`[▏         ]` / `[▍         ]` vs `[          ]`). So the plan's own fix would make a nearly-finished
run read as FINISHED and a started run read as NOT STARTED, in ASCII mode only. That is a NEW wrong
answer a user sees, introduced by a bug fix, judged on the same user-perceptible-impact test the plan
itself invokes to earn its `bug` classification and its release gate. It would also have passed every
piece of evidence the plan demanded, because purity and parity are both satisfied, which is what makes
this worth a HIGH rather than a note. Losing eighth-cell RESOLUTION is unavoidable in ASCII and is
fine; collapsing the BOUNDARIES is not. I measured a conforming alternative (floor plus boundary
clamp) that holds both boundaries and keeps every bar at exactly `width` cells:
`100%`->`[##########]`, `99%`->`[######### ]`, `4%`->`[#         ]`, `0%`->`[          ]`. Fixed by
rewriting E-01 to forbid bare `round()` and require the two boundary properties, adding them to E-05's
required assertions and to V-01's and Required-tests' evidence, and recording F-12.

PR-002 and PR-003 are census corrections that make E-04 smaller and safer. The plan says
`oc_runipd` has six `Palette(should_color(sys.stdout))` sites and `agy_runipd` five, and tells the
executor to sift them. Measured: `grep -c "Palette(should_color"` gives FIVE and FOUR, and far more
usefully there is exactly ONE `Statusline(` construction in each runner, each taking `pal` from a
single function-body assignment inside `run_opencode` and `run_agy_turn` respectively (AST-verified;
`pal` is a local in both, not a parameter). So E-04 edits one line per file. Separately, `run_opencode`
assigns `pal` TWICE, and the first is
`runner_shared.Palette(runner_shared.should_color(sys.stderr))` nested three `if`s deep in the
cross-tree-session refusal path. The later stdout assignment rebinds `pal` before the statusline is
built, so that stderr palette never reaches the box; but an executor following the plan's instruction
to "follow the `pal` variable" without noticing the rebinding could edit it, which would pair a stdout
glyph decision with a stderr color decision in one object, the exact defect E-04's own same-stream rule
forbids. Both recorded (F-13, F-14) and both added to E-04, V-04 and the scope fence.

PR-004 is a stale baseline, the same class of problem I have now seen in three plans from this period.
F-08 tells the executor to expect `1 failed, 3457 passed, 2 skipped` with
`test_release_exempt_setter_roundtrip_and_parity` failing. Re-measured on a clean tree:
`3674 passed, 2 skipped, 3 warnings in 339.13s`, fully green. That test is a local-versus-UTC clock
flake whose window was closed at review. The plan's surviving instruction (judge on the delta of
failing node ids) was always correct; the figures and the expectation of a known failure are not.

PR-005 is a small evidence note: the plan cites `tests/test_run_summary_visible_width.py` as the shape
to follow and as a focused-run target, and that file exists; but it also cites `it6tpj`'s
`tests/test_statusline_visible_width.py`, which does not exist yet because `it6tpj` has not executed.
That is correct as a forward reference and would be a confusing failure for an executor who tried to
run it, so I noted which is which.

ON RIGHT-SIZING. Five E-items in three groups, and the decomposition is genuinely per concern:
E-01 is one function, E-02 is one line, E-03 is one class, E-04 is one line per runner, E-05 is the
guard. E-01 grew slightly at review (it now carries a boundary constraint) but it is still one
function and one evidence pass. No split recommended. The plan's own insistence that each of the three
breaks gets its own E-item is correct and is what makes the partial-fix trap avoidable.

ON THE EXECUTION CONTRACT. Unusually thorough and I added little. It already carries the
declaration-style scope fence with no prohibited stop-on-scope clause, the paste-actual-output honesty
rule, path-scoped `aw commit` with never-push and an explicit shared-checkout warning naming the
`it6tpj` collision, a MUTATION DISCIPLINE paragraph forbidding tracked-file edits for the mutation
proof (which is the right call in a shared checkout and which I have not seen stated this well
elsewhere), and a correctly conditional finalize-ownership paragraph naming `AW-LIFECYCLE-ROLE-001`.
It also correctly states that `iuad9l` has two carriers in this Set and must stay `graduated` until
both execute. I added two fence prohibitions (the stderr palette, and the Unicode branch of
`format_progress_bar`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / F. Prevent silent failure | plan E-01 ("`full = int(round(frac * width))`"); `agent_workflows/render_stream.py:980` (`_FRACTIONAL_BLOCKS`), `:983` (`def format_progress_bar`) | The prescribed ASCII fill collapses two boundaries the Unicode bar preserves: `79/80` renders identically to `80/80` (a 99-percent run reads as FINISHED) and `1/80`, `3/80`, `4/80` render identically to `0/80` (a started run reads as UN-STARTED). It would have satisfied every piece of evidence the plan demanded, since purity and width parity both hold, so the plan's own validation could not catch it. A bug fix would ship a new user-visible wrong answer on the same perceptibility test that earns this plan its release gate. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now forbids bare `int(round(...))` and requires a boundary-preserving fill, naming a measured floor-plus-clamp shape; E-05 must assert `1/80 != 0/80` and `79/80 != 80/80`; V-01 and Required tests demand the boundary proof; Goal, Scope, Proposed changes, Scope check and the approval gate updated; recorded as F-12. |
| PR-002 | MEDIUM | IN-SCOPE | Evidence accuracy (Step 1) | `grep -n "Statusline("` -> one hit per runner (`oc_runipd.py:2959`, `agy_runipd.py:2475`); AST walk of `run_opencode` / `run_agy_turn` | The plan's "six candidate sites in `oc_runipd` and five in `agy_runipd`, not all of which feed a statusline" overstates E-04. There is exactly ONE `Statusline(` per runner and each takes `pal` from a single function-body assignment, so the item edits one line per file. The authored framing sends an executor sifting sites that cannot reach the box. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 rewritten to state the one-per-runner target; V-04 and the call-site reconciliation now expect one per file and treat more than two as over-scope; F-02's count corrected; recorded as F-13. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness | `agent_workflows/oc_runipd.py:2606` (`pal = runner_shared.Palette(runner_shared.should_color(sys.stderr))`) vs `:2787` (`pal = Palette(should_color(sys.stdout))`) | `run_opencode` assigns `pal` twice and the first targets `sys.stderr`, nested three `if`s deep. The later stdout assignment rebinds it before the statusline, so it is harmless today; but E-04's instruction to "follow the `pal` variable" could lead an executor to edit it, producing a palette whose glyph decision reads stdout while its color decision reads stderr, which is exactly the defect E-04's own same-stream rule forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now names the stderr assignment and forbids changing it, explaining the rebinding; V-04 requires pasting that line unchanged; the scope fence adds it; recorded as F-14. |
| PR-004 | MEDIUM | IN-SCOPE | G. Plan executability | plan F-08 ("`1 failed, 3457 passed, 2 skipped`") | The suite baseline is stale and tells the executor to expect a failure that no longer occurs. Re-measured clean: `3674 passed, 2 skipped, 3 warnings in 339.13s`, fully green. The named test is a local-versus-UTC clock flake whose window was closed at review. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-08 rewritten with both measurements and the mechanism; Required tests now says do not expect a known failure and to compare `date` with `date -u` first; recorded as F-15. |
| PR-005 | LOW | IN-SCOPE | Evidence accuracy (Step 1) | `ls tests/test_statusline_visible_width.py` -> No such file; `ls tests/test_run_summary_visible_width.py` -> exists | The plan cites `it6tpj`'s `tests/test_statusline_visible_width.py` as that plan's scope path (correct, a forward reference to an unexecuted plan) while also prescribing a focused run over `tests/test_run_summary_visible_width.py` (which exists). The two are one character apart in reading and an executor could try to run the nonexistent one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Verified which file exists and confirmed the focused-run list names only the existing one; no plan edit was needed beyond confirming the distinction in this record, since the plan's own focused-run line was already correct. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the ASCII fill handle the boundary collisions, given the plan's `round()` proposal fails? | Require the two boundary PROPERTIES (started distinguishable from un-started, incomplete from complete) and name a measured floor-plus-clamp shape as one conforming implementation, leaving the exact rule to the executor. | (a) Mandate one exact expression (rejected: over-prescribes an implementation when the property is what matters, and the plan's own convention is to state the constraint and let the executor choose the fill character); (b) accept the collisions as inherent to ASCII (rejected: measured false, since the clamp holds both boundaries at the same width); (c) widen scope to preserve fractional resolution via a multi-character ASCII ramp (rejected as gold-plating and as a width risk). | Driven comparison of `int(round(...))` against the shipped Unicode bar over `(0,80)`, `(1,80)`, `(3,80)`, `(4,80)`, `(79,80)`, `(80,80)`; the clamp alternative driven over the same cases with a cell-count check at every `current` from -2 to total+3. | yes |
| D-2 | Is the boundary collision in scope for this plan, or a separate finding to carry? | In scope for E-01. It is a property of the function this plan is already rewriting, in the mode this plan is already adding. | Filing it as a follow-up carrier (rejected: it would mean knowingly shipping the regression and then filing against it, when the correct fill costs two extra lines in the same edit). | The plan already owns `format_progress_bar` in `- Scope-Paths:`; the collision exists only on the new ASCII branch, which does not exist before this plan. | yes |
| D-3 | Should E-04's scope be widened now that review finds only one palette per runner feeds the statusline? | No. Narrow it to the measured one-per-runner target and leave OQ-01's broader question deferred. | Widening to all nine `Palette` constructions (rejected: OQ-01 defers that to the maintainer with a recorded reason, and F-09 measures that at least one other consumer has an independent leak a palette change would not fix, so widening would look done and not be). | The single `Statusline(` per runner; OQ-01's `Status: deferred` with `Owner: maintainer`; F-09's `render_run_summary_table` U+2502 measurement, reproduced at review. | yes |
| D-4 | Does OQ-01 being `deferred` with no carrier block readiness? | No. It carries `- Blocking: no`, the statusline fix is correct either way, and the plan records why filing a carrier would presuppose the maintainer's answer. | Treating a carrier-less deferral as a gate (rejected: the 2026-09-10 maintainer ruling narrowed `NO-GO` to an unresolved BLOCKING question, and the plan's deferral reasoning is explicit and measured). | `plan-review.md` "A NON-BLOCKING open question does NOT make a plan `NO-GO`"; the plan's OQ-01 `Carrier-Declined` rationale naming the blast-radius judgement as the maintainer's. | yes |
