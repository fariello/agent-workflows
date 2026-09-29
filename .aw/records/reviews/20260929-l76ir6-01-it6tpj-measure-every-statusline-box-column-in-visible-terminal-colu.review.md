# Review findings: plan it6tpj

- Subject-Id: it6tpj
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `2aaf45e2` in a lane worktree. Structural preflight `aw ipd lint --phase author`
reported `conforming` with ZERO diagnostics, and `--phase review-finalize` after all revisions also
reports `conforming` with ZERO diagnostics. No pre-review snapshot was owed: the plan was committed and
unmodified, and the lane-input copy under `.aw/state/lane-inputs/rev-43/` is byte-identical (verified by
`diff`). NO PRODUCTION FILE, TEST, OR SPEC WAS MODIFIED by this review. Every fix-side measurement was
staged IN MEMORY exactly as the plan's own method rule requires (patched source re-exec'd as a synthetic
module registered in `sys.modules` before `exec`, the function rebound onto `render_stream` only inside
the probe process); probes were written under the gitignored `.aw/state/` and removed, and
`git status --short` showed only the plan file throughout. TWO BACKLOG ITEMS were created (`iuad9l`,
`45l00y`, see PR-605), which are records rather than code changes.

THIS PLAN IS EXCEPTIONALLY WELL MEASURED AND ALMOST EVERYTHING IN IT REPRODUCES EXACTLY. Confirmed at
review HEAD. The site classification over `inspect.getsource(format_statusline_lines)` returns precisely
the plan's figures: 27 non-comment `len(` occurrences, 8 `.ljust`/`.rjust` calls (3 and 5), and 12
alignment specs (10 `:>{` and 2 `:<{`), and I independently enumerated all thirteen width computations
and all twenty-two pads by content and they match F-02's listing line for line. F-01's defect reproduces
in all five cell paths at `{126, 127}` against an ASCII control of `{127}`, identically under
`Palette(False)` and `Palette(True)`, so it is not a styling artifact. F-04 reproduces exactly:
`format_action_label("abcdef\u26a0\ufe0egh")` returns `'Abcdef\u26a0'` with `'\ufe0e' in out` False,
`format_artifact_kind_label` does the same, and `term.truncate_visible(inp, 7)` returns
`'abcdef\u26a0\ufe0e'` with the grapheme intact; the secondary under-fill also reproduces (`'Ab\u26a0\ufe0ecde'`
is 7 code points and 6 columns). F-03 and F-08 reproduce: `tests/test_render_stream.py` is absent, commit
`19313eed` deleted 2,706 lines of it, and `grep -rln "format_statusline" tests/ agent_workflows/ tools/`
returns only two production files and zero tests. F-10 reproduces: all eight box-drawing characters plus
both bar blocks are East Asian Width `A`. F-09 reproduces verbatim in `oc_runipd`'s `Statusline(...)`
construction, all four fields straight from the queue item. Both Section 9.4 bullets are verbatim as
quoted, and the spec's PRIOR ART paragraph does indeed cite this module. `term._pad_visible` is private
and left-aligns only, exactly as F-05 says.

I DROVE THE PRESCRIBED FIX RATHER THAN REASONING ABOUT IT, independently of the plan's own staging. All
thirteen width computations converted and all twenty-two pads rewritten as guarded explicit
concatenation, plus the E-03 truncator swap. Results: every broken case collapses to a single width in
BOTH styling modes (`{126,127}` -> `{127}` for the five cell cases and the countdown case;
`{129,130}` -> `{130}` for a real activity case), the ASCII control and the neither-case stay `{127}`
unchanged, 800 randomized ASCII-input renders show ZERO byte differences, all nine `ACTION_DISPLAY_MAP`
keys return byte-identical labels, no post-fix label exceeds 7 visible columns, and the bare suite
reports `3246 passed, 2 skipped, 3 warnings` both clean (48.90s) and with the fix staged (49.87s). The
Step 0 `sys.modules` registration gotcha was necessary exactly as the plan records it. So the approach is
demonstrated, not merely argued, and the plan's central claims are sound.

PR-601 IS THE FINDING THAT MATTERS MOST, and it exists only because I tried to write E-04's cases rather
than read them. E-04 case (g) says to add "an `activity` variant, which selects the other `col4_w`
branch". `format_activity_cell` returns `("", 0)` for any activity value NOT in
`lifecycle_style.ALL_STAGES`, so the natural free-text choice an executor would reach for
(`"reading a file"`, which is what an activity sounds like) yields `activity_w == 0` and takes the
NO-ACTIVITY branch. Measured: with `activity="reading a file"` the box measures `{126, 127}`, identical
to cases (a) through (e), so the case would have passed while covering nothing new. With a real stage it
measures `{129, 130}` for `abandoned`, `{127, 128}` for `active`, `{128, 129}` for `blocked`. A test that
cannot distinguish the branch it claims to cover is the same class of defect as a guard that cannot
fail, which this repository has repeatedly ruled against. The remedy is cheap: use an `ALL_STAGES`
member and assert the branch is live.

I ALSO ADDED A CASE THE PLAN DOES NOT HAVE, because it guards the one mistake F-11 predicts. The
`recovering` stage's glyph is `\u21a9` PLUS `\ufe0e`, so it puts a zero-width code point into the box
through the ONE path that is already correct (`format_activity_cell` returns its own width). Measured: it
is a SINGLE `{130}` before any fix, in both styling modes. That makes it a canary: if it ever goes
multi-width, `activity_w` was wrapped in `visible_width` or the cell was broken, which is exactly the
error F-11 names as "the single most likely place for an executor to convert something that is already
right".

PR-602 IS A SHAPE THE PLAN ASKS FOR THAT CANNOT EXIST. E-04's byte-identity guard says to compare
"against the CURRENT renderer's own output captured in the same process". Once E-01 through E-03 land
there is no pre-fix renderer in the process; that comparison is only available as one-off execution-time
evidence through the in-memory staging, which is what V-02 separately demands. Left as written, an
executor either fakes the comparison or reaches for the stored blob the same paragraph forbids. The
shipped test must assert the invariant the identity was evidence FOR. I verified E-03 does not perturb
that invariant: `truncate_visible(s, 7) == s[:7]` for every pure-ASCII length 1 through 12, so the
truncator swap is byte-identical on ASCII input.

WHAT I DELIBERATELY DID NOT FLAG. The plan's mutation-discipline rule (stage in memory, never edit a
tracked file in a shared checkout) is correct, well justified, and I followed it myself. Its E-01
warnings not to touch `col1_w`/`col6_w`, the `max()` floors, or `activity_w` are each correct on
inspection, and the `activity_w` warning is the sharpest thing in the plan. Its insistence on converting
the seven safe static-literal pads is right for the stated reason (a mixed function is how this returns)
and its requirement that a skipped conversion be justified in V-02 rather than silently dropped is the
correct handling. The four `Carrier-Declined` rows are each sound: `format_event_prefix` genuinely has a
closed glyph set with no `Mn`/`Me`/`Cf` member, the ambiguous-width half is genuinely declined by the
spec's own text, and `render_run_summary_table` genuinely belongs to `4taj2e`. The `Spec / documentation
sync` section is unusually good: it correctly identifies that no spec is amended because the spec was
already right and the code was non-conforming.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | MEDIUM | IN-SCOPE | E (testing) / D (anti-regression) | plan E-04 case (g); `render_stream.format_activity_cell` (`if token not in _LS.ALL_STAGES: return "", 0`); measured `format_activity_cell("reading a file", Palette(False))` -> `('', 0)` and box widths `{126, 127}`, identical to cases (a)-(e) | E-04'S ACTIVITY CASE WOULD HAVE BEEN VACUOUS. `format_activity_cell` returns `("", 0)` for any value outside `ALL_STAGES`, so a natural free-text activity makes `activity_w == 0` and selects the NO-ACTIVITY `col4_w` branch: the case would pass while re-testing the same path as the others, leaving the branch it claims to cover untested. The plan's `{129, 130}` baseline is also stage-dependent (`abandoned` gives it, `active` gives `{127, 128}`), so the pasted numbers are not universal | C:Low; U:Low; S:Low; F:Medium (a case that cannot distinguish the branch it names is coverage in appearance only, and this is the branch `col4_w`'s second form lives in); Overall:Medium | FIXED | E-04 now requires an `ALL_STAGES` member, names the trap with its measurement, and requires the test to ASSERT the branch is live (nonzero `activity_w`, or a width differing from the no-activity box) so a vocabulary change cannot silently re-void it. A NEW case (h) was added: `activity="recovering"` with ASCII setid/id6, whose glyph `\u21a9\ufe0e` carries a VS through the already-correct path and measures a single `{130}` before any fix, making it the canary for the F-11 mistake. V-02 and V-04 both require the liveness proof. New F-13 |
| PR-602 | MEDIUM | IN-SCOPE | E (testing) / G (executability) | plan E-04's byte-identity paragraph ("comparing against the CURRENT renderer's own output captured in the same process") versus its own in-memory-staging method rule | THE SHIPPED BYTE-IDENTITY TEST CANNOT HAVE THE SHAPE THE PLAN PRESCRIBES. After E-01 through E-03 there is no pre-fix renderer in the process to compare against; that comparison exists only as one-off execution evidence via the staging V-02 separately demands. An executor following the text literally either fabricates the comparison or embeds the stored blob the same paragraph forbids | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now states plainly which shape is which: the SHIPPED test asserts the invariant the identity was evidence for (`visible_width(line) == len(line)` for every line of an unstyled ASCII-only box), while the pre-versus-post comparison is one-off execution evidence. V-04 requires the executor to state which was written and calls the wrong claim a fail. Review additionally verified E-03 does not perturb the invariant (`truncate_visible(s, 7) == s[:7]` for every pure-ASCII length 1..12; all 9 mapped labels unchanged). New F-14 |
| PR-603 | LOW | IN-SCOPE | F (honest documentation) / E | plan F-01, F-05, V-02 and Required-tests, each pasting absolute width figures as the bar | THE PASTED WIDTH BASELINES ARE FIXTURE- AND STAGE-DEPENDENT AND WERE STATED AS THE BAR. The activity figure varies by stage token (`{129,130}` vs `{127,128}`) and every absolute number depends on the probe's timestamps and counts, so an executor whose fixture differs would either open a spurious finding or, worse, adjust the fix to hit a number | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-01 now records the review re-measurement and states that the CARDINALITY is the bar and the numbers are context. V-02 restated to demand a multi-element set before and a single-element set after for all eight cases, with the review baselines offered as figures to reproduce or refute rather than as the criterion. This follows the live-artifact re-derivation convention |
| PR-604 | LOW | IN-SCOPE | F (honest documentation) | plan F-12 and its Deferred row versus `4taj2e`'s front matter re-read at review (`- Status: reviewed`, `- Readiness: go-pending-approval`) and its own Deferred row carrying "corrected at review, PR-503" | F-12'S ACCOUNT OF THE SIBLING PLAN IS STALE IN TWO WAYS. It says `4taj2e` "is pending review now" (it is reviewed and awaiting approval) and presents the falsified byte-pin premise as something `4taj2e` still "inherits" (its own review already corrected it, independently, reaching the identical conclusion). Neither error is consequential for the fix, but a reviewer reading both plans would be misled about which is waiting on what | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-12 rewritten with both corrections and the sibling's own correction quoted; the Deferred row updated and given a typed `- Carrier: 8xcsjr`. Also recorded that both plans declare `- Item-Dependencies: none` and edit verified-disjoint functions, so no ordering edge is owed |
| PR-605 | MEDIUM | UNDER-SCOPE | G / durable-carrier convention | plan's Deferred coverage row ("The executor should file a backlog item...") and OQ-01's `Carrier-Declined` ("The executor files it..."); `ipd_schema`'s durable-carrier rationale ("A note in an executed IPD is 100% guaranteed to be the same as not writing it anywhere") | TWO REAL OBLIGATIONS WERE LEFT AS INSTRUCTIONS TO AN EXECUTOR RATHER THAN CARRIED. Neither the statusline's total absence of coverage nor the `_pad_visible` API question had a typed `- Carrier:`; both depended on an executor remembering to file an item. Once this plan reaches `executed/` the attention view maps it to `done`, so anything it merely mentions becomes invisible, which is exactly the failure the durable-carrier convention was built to refuse | C:Low; U:Low; S:Low; F:Low (nothing breaks, but two tracked obligations silently evaporate); Overall:Low | FIXED | BOTH FILED AT REVIEW rather than deferred to execution: backlog `iuad9l` (`followup`, the statusline's zero coverage, recording the measurement, the trim commit, exactly which part this plan closes, and a behavioral-not-byte-pinning prescription) and `45l00y` (`followup`/`low`, the `_pad_visible` extraction question, recording both blocking properties, the two concurrent conversions that make the moment near, and the sub-decisions a maintainer faces). Typed `- Carrier:` added to OQ-01, to both Deferred rows that needed one, and to the `_pad_visible` row. The gate now instructs the executor NOT to file them again |
| PR-606 | LOW | UNDER-SCOPE | G (execution contract) | plan's POST-GATE LIFECYCLE paragraph as authored ("Do not claim done or move this plan to `.aw/records/plans/executed/` until...") | THE LIFECYCLE INSTRUCTION HAS NO CONDITIONAL OWNER and describes the executor moving the plan. Under a managed lane the runner owns begin/finalize and a worker-role process is refused with `AW-LIFECYCLE-ROLE-001` (enforced inside the finalize transaction, so `aw ipd set executed` is refused too), so an agent following this spends its terminal turn on an expected refusal | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten to separate the unconditional finalize obligation from the conditional owner, naming the enforcement site and the hand-execution invocation, and forbidding both a hand-rolled `git mv` and a hand-edited `- Status:`. Also corrected "six cases" to eight and added the under-fill repair to the required evidence list |
| PR-607 | LOW | UNDER-SCOPE | G (approval gate) | plan gate as authored: an execution contract and a scope fence, but no statement of what approval means | NO STATEMENT OF WHAT A HUMAN WOULD BE APPROVING. The gate is strong on constraints and silent on the decision: a reader cannot tell from it that the change is output-neutral for every input a user has today, that the direction is mandated by an approved spec rather than chosen, or what is deliberately left unfixed | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a "WHAT A HUMAN WOULD BE APPROVING" paragraph naming the scope, the measured output-neutrality (800 identical renders, 9 identical labels, identical suite counts), the spec mandate with its self-citing PRIOR ART, and all four carried exclusions with their carriers. Added a recorded right-sizing judgement noting the linter reports zero advisories and explaining why E-02's twenty-two sites are one concern |

No finding was DEFERRED and none was left OPEN, so no escalation to a `- Blocking: yes` question is
owed (`check.review-finding-unescalated` satisfied vacuously). No BLOCKER and no HIGH was found: the
defect is real, the diagnosis is accurate to the site, the prescribed fix was independently verified to
work and to be output-neutral on ASCII, and all three MEDIUMs are test-plan and carrier defects in items
nobody has executed.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-04's activity case is vacuous as written. Require a real stage token, or drop the case? | Require an `ALL_STAGES` token AND an assertion that the branch is live, plus a `recovering` canary case | Dropping it, rejected because `col4_w` has two forms and the activity form would then be the only unconverted-and-untested branch in a function this plan is converting wholesale. Requiring only the token without the liveness assertion, rejected because the same trap reappears the moment the stage vocabulary changes, and the assertion costs one line | measured `format_activity_cell("reading a file", Palette(False))` -> `('', 0)` with box widths identical to the no-activity cases; the guard clause `if token not in _LS.ALL_STAGES` in `format_activity_cell`; `ALL_STAGES` has 20 members; per-stage widths measured for four tokens | yes |
| D-2 | The plan asks the shipped test to compare against a renderer that will not exist. Restate the assertion, or keep the comparison and move it into the test via staging? | Restate: the shipped test asserts the invariant, the comparison stays one-off execution evidence | Keeping the comparison inside the shipped test by staging the old renderer permanently, rejected because it would ship a copy of the pre-fix code as a test fixture, which is a byte-pin in a worse form and rots on every unrelated column change. Dropping the property, rejected because it is the plan's main safety argument for a thirty-five-site rewrite | the plan's own in-memory-staging method rule; the impossibility of comparing to a replaced function in-process; review verification that `truncate_visible(s,7) == s[:7]` on ASCII so the invariant is not perturbed by E-03 | yes |
| D-3 | Two Deferred obligations instruct the executor to file backlog items. Leave them as instructions, or file them at review? | File both at review (`iuad9l`, `45l00y`) and wire typed carriers | Leaving them, rejected on the durable-carrier convention's own recorded rationale: a note in a plan that is about to become `executed` is equivalent to not writing it, because `attention_contract` maps `executed` to `done`. Filing only the coverage one, rejected because the `_pad_visible` question is the one whose moment is demonstrably near (two renderers being converted concurrently) and it is the cheaper of the two to lose track of | `ipd_schema`'s durable-carrier comment quoting the maintainer ("100% guaranteed to be the same as not writing it anywhere"); `CARRIER_FIELD` matching structurally and never by prose; both items verified filed with `open` status | yes |
| D-4 | Should this review also correct the stale byte-pin claim surviving in sibling `4taj2e`'s E-item prose? | No; record it and leave it to that plan | Editing `4taj2e`, rejected because it is a different plan already `reviewed` with its own `Readiness`, its Deferred section ALREADY carries the correction from its own review, and editing another plan's reviewed body from this review would touch an artifact outside this review's ledger. Opening a finding against it, rejected because its own review already found and fixed the same thing where it mattered | `4taj2e`'s Deferred row containing "corrected at review, PR-503" with the identical conclusion; its front matter `Status: reviewed` / `Readiness: go-pending-approval`; the workflow's scope rule that a file referenced only as evidence is not in scope | yes |
| D-5 | The plan requires converting seven pads that are pure ASCII today and cannot misalign. Accept that as necessary, or flag it as over-scope? | Accept it; do not flag | Flagging as over-scope, rejected on the plan's own stated reason, which I judge correct: converting them makes the rule "every pad in this function is visible-width" true and grep-checkable, whereas leaving them makes it "every pad except seven an editor must remember", and a mixed function is precisely how this defect class returns. The plan also already requires any skipped conversion to be justified in V-02 rather than silently dropped, which is the right handling | the plan's E-02 rationale; the measured fact that all 22 sites are in one function so the sweep is bounded; GUIDING_PRINCIPLES P8 on single source of truth applied to the padding rule | yes |

No `Reversible: no` decision was taken, so no escalation is owed under the irreversible-decision rule.
