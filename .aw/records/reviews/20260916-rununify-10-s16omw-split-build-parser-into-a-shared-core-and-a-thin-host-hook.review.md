# Review findings: plan s16omw

- Subject-Id: s16omw
- Subject-Type: ipd
- Reviewed-At: 2026-09-16
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `7936c13d`. Structural preflight `aw ipd lint --phase author` CONFORMED (exit 0) before
revision. No pre-review snapshot needed: the plan was committed and unmodified. This is the ninth
`rununify` child reviewed and the FIFTH split child. It is the mirror image of sibling `orziju`: there a
high similarity score concealed deep divergence, here a low one is being explained away as drift.

THE NUMBERS REPRODUCE AND THE INFERENCE INVERTS. Verified: 347 oc lines and 264 agy; 271/212 code lines;
47 differing lines under AST normalization with docstrings stripped; 22 bearing a host token (the plan says
23, the same measurement rounded). BUT 47 differing lines out of 46 oc and 47 agy TOTAL normalized lines
means the two functions share almost nothing, and SequenceMatcher confirms it: similarity 0.4946, the
LOWEST of the five large functions by a wide margin (`initialize_run` 0.9345, `execute_item` 0.851). The
Concern's boilerplate sentence, "most of the divergence is DRIFT in shared logic rather than genuine host
specificity", is FALSE for this symbol and CONTRADICTS the plan's own F-1, which says the opposite and is
correct.

I MEASURED THE FLAG SURFACE FLAG-BY-FLAG, which no prior review in this Set did, because for a parser the
unit of divergence is an option string and not a line. Across all four subparsers: 17 SHARED option
strings, 7 OC-ONLY (`--agent`, `--audit`, `--auto`, `--opencode`, `--variant`, `--verify`, `--verify-with`)
and 10 AGY-ONLY (`--agy`, `--agy-executable`, `--dangerous`, `--dangerously-skip-permissions`, `--effort`,
`--new-session`, `--no-audit`, `--no-dangerously-skip-permissions`, `--no-verify`, `--timeout`). So the
surface is 17 shared against 17 host-specific, and F-4's "oc has `--opencode`, agy has its own binary
override" describes two of seventeen.

THE SHARPEST FINDING IS THAT ONE DIFFERENCE IS AN INCOMPATIBLE CONTRACT, NOT A STRING, AND THE SET'S
OC-PREFERRED RULING CANNOT BE APPLIED TO IT. Measured live on built parsers: on oc, `--verify`, `--audit`
and `--no-verify` ALL resolve to dest `validate`; on agy, `--verify`/`--audit` do not exist at all, while
`--no-verify`/`--no-audit` resolve to dest `no_verify` and `--validate`/`--no-validate` resolve to
`validate`. agy DEFENDS this with a build-time guard oc does not have,
`assert_verification_flags_are_distinct` (`agy_runipd.py:1959`), called at the end of its `build_parser`.
That guard's docstring records the measured hazard verbatim: registering oc's alias list on agy makes
`BooleanOptionalAction` auto-generate `--no-verify`/`--no-audit`, which with the default handler raises at
build time and with `conflict_handler="resolve"` does something "far worse and SILENT: the new action STEALS
`--no-verify`/`--no-audit`, and the shipped spelling stops meaning what every existing invocation and every
piece of documentation says it means". "Resolve to oc unless a difference is a real capability" therefore
cannot govern here: adopting oc's version breaks agy's shipped CLI.

WHAT IS ACTUALLY SHARED IS ALREADY SHARED, and this is the finding that decides the plan's economics. F-3
is CORRECT and I verified it exactly: `runner_shared.RUN_POLICY_FLAGS` carries 12 rows and
`register_run_policy_flags` is called TWICE per host (`start` and `resume`). So twelve of the seventeen
shared option strings already have one implementation. The residual duplication a shared core would remove
is the four subparser skeletons plus the byte-identical `--repo`/`run_id`/`--json` registrations on
`status`/`report`. Against that, the cost is parameterizing 17 host-specific option strings and roughly
13,500 characters of help text: 8,376 of oc's 16,443 source characters and 5,051 of agy's 12,227 are string
literals, so 50 and 41 percent of each function IS prose, and it documents different capabilities (oc's
`as <profile>` positional clause and per-field precedence chain, against agy's clean-session skeptical
self-validation). F-5's "host names throughout; supplied by child 04's descriptor" understates this by an
order of magnitude and proposes a mechanism that cannot carry it.

TWO FINDINGS IN THIS PLAN'S FAVOR THAT IT DOES NOT CLAIM, and they matter because they change what the
maintainer is deciding. FIRST, there are ZERO source-inspection pins on `build_parser`: no
`inspect.getsource`, no AST-lookup-by-name, no `split("def build_parser")` anywhere in `tests/`. All 31 test
files that touch it call `build_parser()` and assert on the parser OBJECT. That is unique among the five
(`execute_item` carries 14 such pins, `initialize_run` 11), so a relocation here breaks no pin. SECOND, the
closure is the cleanest in the Set: seven free module-level names, of which three are module handles already
single objects, two are equal constants (`ACTION_CHOICES` and `DEFAULT_STALL_TIMEOUT`, identical on both
hosts), and only TWO are still double-defined (`_add_output_mode_flags`, `_detect_driver_command`). Compare
`execute_item`'s eighteen. So this is the one split child where the obstacle is NOT mechanical.

WHICH MAKES THE QUESTION DIFFERENT IN KIND FROM ITS SIBLINGS. For `execute_item`, `run_queue` and
`initialize_run` the question is "can this be done from here"; the answer was no. Here the answer is "yes,
easily", and the question becomes "is it worth it", given that the shared half is already shared, the
unshared half is two hosts' public CLI contracts, and one difference cannot be reconciled in the ruled
direction at all.

ONE MORE CORRECTION: `_add_output_mode_flags` IS ORPHANED. Child 04 lifts `_detect_driver_command` and
explicitly assigns `_add_output_mode_flags` to child 03 ("which is child 03's and is display-only"), while
child 03 was re-scoped at its own review from 48 symbols to 9 and does not lift it. So this plan's declared
`executed:tx6q0h` prerequisite clears one of its two remaining double definitions and the other is owned by
nobody. `tx6q0h` is also itself `reviewed`/`no-go` with an open blocking question.

WHAT I FIXED AND WHAT I LEFT. I added the flag-surface table to the Goal; corrected the Concern; recorded
the verification-dest collision as F-7 with the guard docstring; measured and corrected F-4 (17 not 2) and
F-5 (13,500 characters, not host names); confirmed F-3 exactly and made its economics a deliverable (E-03);
recorded the zero-pin and clean-closure facts as F-9 and F-10 so the maintainer knows the obstacle is
worth-it rather than can-it; added gating E-01; rewrote E-02 to pin the per-host flag contract on the PARSER
OBJECT rather than by source inspection, preserving F-9; converted the split into E-04's analysis; added
E-05 with inverse assertions; made non-vacuity bidirectional; fenced
`tests/test_run_flag_surface.py`; and sharpened the spec section, since this is the most spec-coupled of the
five children. I did NOT decide the route.

MY RECOMMENDATION IS ROUTE (C), grow the existing spec-governed table rather than relocate the function,
because the repository already contains the working precedent for exactly this problem and relocating adds a
second mechanism for one job. Route (D), do not share, is a stronger fallback here than for any sibling.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | BLOCKER | IN-SCOPE | A. correctness (public contract); B. security-adjacent | `agy_runipd.py:1959-1990`; live dest inspection of both built parsers | **ONE DIFFERENCE IS AN INCOMPATIBLE CLI CONTRACT AND THE OC-PREFERRED RULING CANNOT APPLY.** On oc, `--verify`/`--audit`/`--no-verify` all resolve to dest `validate`; on agy, `--verify`/`--audit` do not exist and `--no-verify`/`--no-audit` resolve to `no_verify`. agy carries a build-time guard whose docstring records that registering oc's aliases would make `BooleanOptionalAction` generate `--no-verify`/`--no-audit` and, under `conflict_handler="resolve"`, SILENTLY STEAL agy's shipped spellings. So adopting oc's version breaks a shipped CLI, and this is an A / NOT-A case the ruling reserves for a per-symbol maintainer decision. | C:Low; U:High; S:Low; F:High; Overall:High | OPEN | Added as F-7 with the docstring quoted; E-02 must assert all six dests per host; V-05(b) requires a control proving the suite catches the collision; E-04(b) must quote the guard. Folded into OQ-03. NOT fixed by a plan edit because the reconciliation direction is the maintainer's. |
| PR-002 | BLOCKER | IN-SCOPE | C. architecture; F. KISS | flag partition (17/7/10); `RUN_POLICY_FLAGS` = 12 rows registered twice per host; string-literal character counts | **THE SHARED HALF IS ALREADY SHARED, SO THE SPLIT'S PAYOFF IS FOUR SUBPARSER SKELETONS.** Twelve of the seventeen shared option strings already come from `runner_shared.register_run_policy_flags`. What remains duplicated is the four `add_parser` calls and a few byte-identical registrations. The cost is parameterizing 17 host-specific option strings plus ~13,500 characters of divergent help text (50 percent of oc's source, 41 percent of agy's). A shared core would be a template whose entire visible output is caller-supplied. | C:Medium; U:Medium; S:Low; F:Medium; Overall:Medium-High | OPEN | Flag table added to the Goal; F-3 confirmed and its economics made E-03's deliverable; F-4 and F-5 corrected with the measured counts; escalated as OQ-03 with four routes and a grow-the-table recommendation. |
| PR-003 | HIGH | IN-SCOPE | A. correctness (a conclusion contradicting its own finding) | similarity 0.4946; 47 of 46/47 normalized lines | **THE CONCERN'S "MOSTLY DRIFT" SENTENCE IS FALSE HERE AND CONTRADICTS F-1.** It is the boilerplate line shared with the other four split children, and for this symbol the measurement refutes it: the two functions share almost nothing, and F-1 (which calls this "the MOST host-specific of the five") is the correct reading. An executor trusting the Concern would look for drift to reconcile and find two intentionally different CLI contracts. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern corrected in place with the similarity figure and the flag partition; F-6 added stating the contradiction explicitly and siding with F-1. |
| PR-004 | HIGH | IN-SCOPE | A. correctness (an undercount) | flag-by-flag measurement | **F-4 DESCRIBES 2 OF 17 HOST-SPECIFIC FLAGS.** "oc has `--opencode`, agy has its own binary override" omits fifteen, several of which are capability-bound rather than name-bound: `--variant`/`--agent`/`--verify-with` belong to oc's runner-profile subsystem (zero `runner_profiles` references in agy), and `--effort`/`--timeout`/`--dangerously-skip-permissions` are agy CLI concepts with no oc analogue. The conclusion ("these stay host-side") is right; the scale is not, and the scale is what decides OQ-03. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-4 corrected with all 17 named and the capability-bound subset called out. |
| PR-005 | HIGH | IN-SCOPE | A. correctness; F. honest documentation | 8,376 / 16,443 oc chars; 5,051 / 12,227 agy chars | **F-5 UNDERSTATES THE HELP TEXT BY AN ORDER OF MAGNITUDE AND NOMINATES A MECHANISM THAT CANNOT CARRY IT.** Half of each function by character count is string literals, and they document DIFFERENT capabilities (oc's `as <profile>` clause, precedence chain and profile freezing; agy's clean-session validation), so a host-name descriptor substitution cannot turn one into the other. Either the whole text is parameterized or one host's help is imposed on the other, and the latter is an operator-visible change this plan forbids itself. | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | F-5 corrected with the character counts and the reason a descriptor is insufficient; folded into OQ-03's cost side. |
| PR-006 | HIGH | UNDER-SCOPE | G. dependencies and sequencing | child 04's line 115; child 03's re-scoped groups A/B | **`_add_output_mode_flags` IS ORPHANED BETWEEN TWO SIBLING PLANS.** Of this plan's only two remaining double definitions, child 04 lifts `_detect_driver_command` and explicitly assigns `_add_output_mode_flags` to child 03, which was re-scoped from 48 symbols to 9 and does not lift it. So the declared prerequisite clears one of two and the other has no owner. `tx6q0h` is additionally `reviewed`/`no-go` with an open blocking question, so the edge points at a plan that cannot currently execute. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-8 with both citations; E-04(c) must state an explicit disposition for the orphan; V-04 requires it. |
| PR-007 | HIGH | UNDER-SCOPE | E. testing (a property worth preserving) | repo-wide search of `tests/`; 31 behavioral callers | **A GOOD FACT THE PLAN DOES NOT CLAIM AND COULD ACCIDENTALLY DESTROY: `build_parser` HAS ZERO SOURCE-INSPECTION PINS.** All 31 test files that touch it assert on the parser OBJECT. That is unique among the five large functions and means a relocation breaks no pin. The risk is that a new suite written for this plan introduces the FIRST source pin, which would hand the next refactor the problem its siblings have. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-9 and to Project conventions; E-02 now requires parser-object assertions explicitly; V-02(b) requires confirmation that no `inspect.getsource` of `build_parser` was introduced. |
| PR-008 | MEDIUM | UNDER-SCOPE | C. architecture (favorable) | closure measured at HEAD | **THE CLOSURE IS THE CLEANEST IN THE SET AND THE PLAN DOES NOT SAY SO:** 7 free names, 3 module handles already shared, 2 equal constants, only 2 still double-defined, against `execute_item`'s 18. Recorded because it changes the DECISION: the obstacle here is not mechanical feasibility but whether the sharing is worth having, and a maintainer reading only the sibling reviews would assume otherwise. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-10 with the comparison; the gate's reviewer-targets paragraph now says explicitly not to hunt for mechanical blockers here. |
| PR-009 | MEDIUM | UNDER-SCOPE | E. testing (the hazard made executable) | `tests/test_run_flag_surface.py:43-48`; `89 passed` | F-2 correctly names the spec contract test as the hazard but never FENCES the file, never states its baseline, and never requires it green by name. It reads the spec as a FILE in both directions with an exclusion list where "silence is a failure", so it is the single most likely suite to catch a mistake here. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-12; the file fenced; Required tests item 3 requires it green with its 89-test baseline; item 4 additionally requires agy's build-time guard proven still invoked. |
| PR-010 | MEDIUM | UNDER-SCOPE | G. right-sizing | E-02 as authored | One E-item bundled the relocation, 17 flag-string decisions, 13,500 characters of help-text parameterization and the verification-dest collision into one pass, invisible to the count-based lint. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as F-11; restructured into five test-only items; `Highest E allocated` raised to 05. |
| PR-011 | MEDIUM | UNDER-SCOPE | E. non-vacuity | Required tests item 3 as authored | Non-vacuity was one-directional and aimed at "sabotage the shared core", which cannot exist while the split is ungated and would not have exercised the F-7 collision, the one failure mode that matters most. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Item 7 now demands both controls, the second specifically proving the suite would catch the verification-dest collision; V-05(b) requires both pasted. |
| PR-012 | LOW | UNDER-SCOPE | G. spec effects | `tests/test_run_flag_surface.py:43-48`; the per-host asymmetry | The spec section is the generic boilerplate, but this is the most spec-COUPLED of the five children: `build_parser` IS the surface spec `25kzda` 2.1 governs, and the contract test reads the spec file bidirectionally. It also raises a question the plan cannot see: the suite checks the surface against the SPEC rather than per host, so the spec may not acknowledge that `--no-verify` means different things on the two hosts. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec section rewritten with the file citation and the bidirectional rule; E-04 must report whether the spec acknowledges the per-host asymmetry, flagging a possible spec gap without taking on the fix. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | The plan reports 47 differing lines with 23 host tokens and concludes "mostly drift". Accept, or compute the ratio? | COMPUTE. 47 differing out of 46/47 TOTAL means similarity 0.4946, the lowest in the Set, so the conclusion inverts and F-1 is the correct reading. | (a) Accept the Concern, rejected: it is boilerplate repeated verbatim across five children, and a differing-line count is only interpretable against the total, which the sentence never supplies. (b) Trust F-1 without measuring, rejected: F-1 and the Concern CONTRADICT each other, so a measurement was the only way to say which stands. | AST-normalized diff at HEAD `7936c13d`; SequenceMatcher 0.4946 against 0.9345 for `initialize_run` and 0.851 for `execute_item` | yes |
| D-2 | For a parser, is the line diff the right unit? | NO. Measure the FLAG SURFACE: 17 shared option strings, 7 oc-only, 10 agy-only, plus the dest each verification spelling resolves to. | (a) Keep to the line diff as the sibling reviews did, rejected: a parser's contract is its option strings, and a single `add_argument` line can add or remove an operator-visible flag while a help-text line changes nothing. (b) Count only `start`, rejected: `resume` carries five oc-only flags including `--verify-with`, which the plan never mentions. | flag extraction across all four subparsers on both hosts; live dest inspection of the built parsers | yes |
| D-3 | `--no-verify` maps to different dests per host. Reconcile toward oc per the standing ruling, or escalate? | ESCALATE. The ruling cannot apply: adopting oc's aliases collides with agy's shipped `--no-verify`, which agy guards against at build time. | (a) Apply the oc-preferred ruling, rejected outright: `assert_verification_flags_are_distinct`'s docstring records that this exact change either raises at build time or silently steals agy's shipped spellings, so it would break a public CLI. (b) Reconcile toward agy, rejected: it would remove oc's `--verify`/`--audit` aliases, equally operator-visible, and the ruling does not authorize preferring agy. (c) Keep both by widening the shared core with a host conditional, rejected: OQ-01 already forbids an `if host == ...` branch in the core. | `agy_runipd.py:1959-1990` docstring; measured dests (`--no-verify` -> `validate` on oc, `no_verify` on agy); the maintainer's 2026-09-14 A/NOT-A carve-out | yes |
| D-4 | The shared half is already shared. Choose a route myself, or ask? | ASK. Raised as OQ-03, `Blocking: yes`, four routes with costs and a grow-the-table recommendation. | (a) Adopt share-the-skeleton myself, rejected: it redefines the child's deliverable from "split the function" to "share four `add_parser` calls", which changes what the Set delivers. (b) Declare the function host-owned myself, rejected for the same authority reason, though it is the strongest such position in the Set. (c) Recommend nothing and merely report, rejected: the repository contains a working precedent for this exact problem (`RUN_POLICY_FLAGS` plus its spec contract test), so withholding the recommendation would waste it. | `RUN_POLICY_FLAGS` = 12 rows registered twice per host; the residual duplication measured; the 13,500-character help-text volume | yes |
| D-5 | `build_parser` has zero source pins today. Should the new suite be allowed to add one? | NO. E-02 must assert on the PARSER OBJECT, following the 31 existing behavioral callers. | (a) Let the executor choose, rejected: three sibling reviews found source pins to be the single largest obstacle to a later split (14 on `execute_item`, 11 on `initialize_run`), so introducing the first one here would hand the next refactor a problem this function has never had. (b) Add a source pin deliberately to lock the current structure, rejected: it would lock a structure the maintainer may be about to change, and a parser's behavior is fully observable from the object. | zero `getsource`/AST/`split` matches for `build_parser` across `tests/`; 31 files calling `build_parser()`; the sibling measurements | yes |

### Deferred and open

- `PR-001` - `OPEN`:
  - Reason: The two hosts' verification flags form an incompatible contract that the Set's oc-preferred ruling cannot resolve, and both candidate reconciliations change a shipped, documented CLI spelling. The maintainer gave A/NOT-A rulings for `extract_session_id` and `driver_begin` but was never asked about this one.
  - Remediation Risk: High
  - Axis: usability, functionality
  - Required decision or evidence: the maintainer's answer to OQ-03, including an explicit decision on whether the verification flags are reconciled at all and in which direction, or left permanently host-specific.
  - Consequence if unresolved: nothing breaks; the current state is correct and guarded. The risk being held open is an executor applying the standing ruling mechanically, which either raises at parser build (loud, recoverable) or, under `conflict_handler="resolve"`, silently repoints `--no-verify` on agy so every existing invocation and every piece of documentation becomes wrong.
- `PR-002` - `OPEN`:
  - Reason: Whether to share a function whose shared half is already shared and whose remaining content is two hosts' public CLI contracts is a design and priority question, and every route changes what this child of the Set delivers.
  - Remediation Risk: Medium-High
  - Axis: complexity, usability
  - Required decision or evidence: the maintainer's answer to OQ-03 (routes A through D).
  - Consequence if unresolved: `build_parser` stays duplicated, and this is the LOWEST-cost such outcome in the Set: the duplicated residue is four `add_parser` calls plus each host's own flags and help, while the spec-governed core is already single-implementation. The dangerous outcome is an executor producing a shared core parameterized by 17 option strings and 13,500 characters of help text, which would be harder to read than the two copies.

### Escalation of the irreversible decision

None of this round's five decisions is judged `Reversible: no`. Each is undone by editing this plan or a
test, and none publishes an interface, migrates data, or deletes anything. Stated explicitly rather than
left blank: D-3 LOOKS like the irreversible one, because reconciling a shipped CLI flag genuinely cannot be
cleanly undone, but the decision I made was to ESCALATE rather than to reconcile, which is the fail-closed
direction. The irreversible act it guards against is escalated instead: PR-001 is raised in the plan as F-7
with the guard docstring quoted, E-02 must assert all six dests per host, V-05(b) requires a control proving
the suite catches the collision, and the `Blocking: yes` OQ-03 puts it in front of the maintainer before any
split executes. That is the workflow's prescribed handling for an irreversible consequence I declined to
authorize.

### Honest limits of this review

- I DID NOT ATTEMPT THE SPLIT. The 17/7/10 partition and the seven-name closure come from AST extraction
  plus live parser inspection, not from having built a shared core. E-01 re-derives both at execution HEAD.
- MY FLAG PARTITION COUNTS OPTION STRINGS, NOT SEMANTICS. `--audit` and `--no-audit` are counted separately
  per host, and a flag whose NAME matches across hosts could still differ in `action`, `default` or `help`;
  I checked that specifically only for the six verification spellings. E-02's per-host table should assert
  more than the name set if the executor wants a tighter contract.
- I DID NOT RUN THE FULL SUITE. I ran `tests/test_run_flag_surface.py` (`89 passed`). The plan's overall
  suite bar is unverified by me, and the flake I warn about is inherited from a sibling review's measurement.
- MY ZERO-PIN CLAIM RESTS ON A KEYWORD SEARCH for `getsource(...build_parser)`, `n.name == "build_parser"`
  and `split("def build_parser")` across `tests/test_*.py`. A pin reaching the source by another route (a
  fixture reading the module file, a helper that takes a function and inspects it) would not have appeared,
  so E-01(d) is asked to confirm it independently rather than inherit my result.
- I DID NOT VERIFY THAT THE SPEC IS SILENT ON THE PER-HOST ASYMMETRY. I established that
  `test_run_flag_surface.py` checks the surface against the spec rather than per host, and inferred that the
  spec may not distinguish the two hosts' `--no-verify`; I did not read the spec's grammar block to confirm
  it. E-04 is asked to report it, and my PR-012 wording is deliberately conditional.
- I DID NOT DECIDE THE ROUTE (D-4), and my grow-the-table recommendation is a recommendation. I also did not
  evaluate whether spec `25kzda` 2.1 SHOULD govern per-host flags, which is the question route (C) would
  eventually raise and which is broader than this plan.

## Round 2

DISCHARGE ONLY. NO NEW REVIEW WAS PERFORMED. This round records that round 1's gating findings were
resolved by the maintainer's own directive, given on 2026-09-16 in an interactive session. Nothing in the
plan was re-reviewed here and no new finding was sought; appending a round is the mechanism
`plan-review.md` prescribes for this, since the gate reads only the current round. Round 1 is left exactly
as written, and its measurements remain the specification the execution must reproduce at execution HEAD.

THE DIRECTIVE, quoted: "at the end of the SET, there should be one code base shared by the two runners
that contains 100% of the otherwise redundant code that currently is duplicated between the two runners."

TWO SUPPORTING RULINGS the maintainer gave in the same session, because round 1's findings rested on
premises both of them contradict. FIRST, TESTS ARE NOT IMMOVABLE: asked directly whether the
source-reading guards prevent this work, the answer was no, and the maintainer pointed at this
repository's own precedent where such a guard was already re-based for shared code
(`tests/test_nested_tty_noninteractive.py:190-203`, whose docstring records the reasoning; all 41 tests in
that file and `tests/test_lane_tool_identity.py` pass at this HEAD, verified 2026-09-16). SECOND,
COORDINATED DE-DUPLICATION IS PERMITTED: many functions may be de-duplicated together before testing, so
a dependency that is still double-defined because a sibling has not landed is an ordering matter, not a
blocker. What remains forbidden is weakening a guard silently.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | round 1 finding, discharged by directive | this plan's resolved `OQ-03`; the maintainer's 2026-09-16 directive | Body difference was measured but liftability was not: the function closes over names that are still defined twice, so a shared core would need many injected parameters. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The maintainer ruled 2026-09-16 that the objective is 100% de-duplication and that the injected-parameter form IS the sanctioned mechanism, not a violation of it: the 2026-09-03 `818uru` OQ-02 ruling established "shared file owns the real function taking explicit parameters, each runner keeps a one-line wrapper at the original name and signature", and what it rejected was threading a parameter through ~86 CALL SITES, which the wrapper form avoids. The maintainer also confirmed many functions may be de-duplicated together before testing, so a still-double-defined dependency is handled by working in dependency order, not by refusing. See the resolved OQ-03. |
| PR-002 | BLOCKER | IN-SCOPE | round 1 finding, discharged by directive | this plan's resolved `OQ-03`; the maintainer's 2026-09-16 directive | Tests read this function's source text or patch names it resolves, and a thin caller satisfies none of them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The maintainer ruled 2026-09-16 that these pins are work, not vetoes, citing the existing precedent where such a guard was already re-based onto shared code successfully (`tests/test_nested_tty_noninteractive.py:190-203`, all 41 related tests passing at this HEAD). A pin is to be re-based on the new location with its property preserved and its injected-regression proof kept; silently weakening one (lowering a threshold, deleting an assertion) remains forbidden. Where a behavioral assertion can replace a source-text one without losing coverage, prefer it and say so. See the resolved OQ-03. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the maintainer's directive discharge round 1's gating findings, or do they need a fresh review pass? | It discharges them; record the discharge and leave round 1 untouched. | A further full review round on this plan, rejected on cost and on relevance: round 1 already measured the mechanics correctly and its findings were escalations of a SCOPE decision, which is the maintainer's to make and which they have now made. | The findings' own recorded remedy was a maintainer decision, and that decision is now recorded in this plan's resolved OQ-03 with its reasoning and its two supporting rulings. | yes |

HONEST LIMIT, stated because it bounds what this round proves: the discharge rests on the maintainer's
directive, NOT on an independent reviewer's re-examination of the plan's content. Round 1 is where that
assurance lives. Specifically NOT re-verified here: the closure and pin measurements round 1 recorded
(each plan's E-01 re-measures them at execution HEAD and is required to refuse on a stale list), and
whether the re-based guards preserve their properties (each plan's V-items require that evidence). This
round changes the DECISION column and nothing else.
