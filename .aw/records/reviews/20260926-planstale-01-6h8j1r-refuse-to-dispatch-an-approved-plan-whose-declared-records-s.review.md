# Review findings: plan 6h8j1r

- Subject-Id: 6h8j1r
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated lane worktree. Structural preflight `aw ipd lint --phase author --detail`
CONFORMED (exit 0, no advisory) before revision. No pre-review snapshot was needed: `git status
--short` was empty, so the plan was committed and unmodified.

THE GAP IS REAL AND I CONFIRMED IT FROM BOTH ENDS. Reading `execute_item_core` end to end, nothing
between `resolve_plan_path` and the agent spawn reads a `Scope-Paths` target, and `ipd_lifecycle.begin`
consults `_frozen_scope_paths` only to measure baseline dirtiness, never existence. The motivating
case reproduces exactly as written: `tgop8e`'s executed copy still declares
`.aw/records/plans/pending/20260910-rdyrecheck-01-qhy3i3-...ipd.md`, that path does not exist, and
`qhy3i3` now sits in `executed/`. The design constraint that shapes the whole plan is also right and
is the reason this is a good design rather than an obvious one: a generic existence check is
impossible because 30 missing literal NON-records entries exist across pending plans (new code and
test files that are legitimately absent), while 0 missing literal `.aw/records/` entries exist. I
widened that measurement past the plan's own: it holds across ALL 49 pending plans carrying
`Scope-Paths` (30 `to-review`, 11 `approved`, 8 `reviewed`), not merely the approved subset, so the
rule is safe on the whole pending lane.

I ALSO BUILT AND RAN A FAITHFUL PROTOTYPE of E-02's algorithm over the entire plans corpus, which is
what produced the substantive findings below. It reproduced the plan's classification result in shape
and disagreed in detail: 65 stale entries now (45 `moved-terminal`, 20 `moved`, 0 `vanished`) against
the authored 58/40/18/0, with 52 resolved via the id6 selector and 13 via the basename fallback, and
0 ambiguous multi-hit cases. Every one of the 65 sits in a plan under a terminal directory, so the
`pending`-only restriction is load-bearing exactly as the plan says. The choice of `is_retired` over
`run_selection_policy.is_in_terminal_directory` is correct and I verified it from the other side:
`_RETIRED_PATH_SEGMENTS` is `{archive, done, executed, not-executed, parked, shipped, superseded}`
and `_RETIRED_STATUSES` adds `implemented`, so it covers every records type and correctly excludes
`reusable`. OQ-01 through OQ-03 are all resolved from genuine evidence I checked rather than
asserted: Section 5.7 exists with the rows quoted, `fail-gate` is in `TERMINAL_STATES_CANONICAL`, and
the clean-base refusal arm matches the described shape symbol for symbol.

**REFUSING ON `moved` WOULD REFUSE PLANS THAT ARE PERFECTLY RUNNABLE, WHICH IS A WORSE FAILURE THAN
THE ONE BEING FIXED.** This is the finding that justifies the review. The authored E-04 refused on
ANY entry the predicate returned, and `moved` means the target resolves to exactly one NON-RETIRED
artifact. A non-retired artifact is fully editable, so the plan's work can still be done and the only
defect is a stale string. The mechanism that creates these is routine and unavoidable: a spec moves
`approved/` -> `implementing/` -> `implemented/` over its life, and NOTHING rewrites a citing plan's
`Scope-Paths` when it does. `aw rename` rewrites references ("rewriting references to it across the
repo"), but a status transition is not a rename, which is precisely how the motivating case happened
in the first place. Measured: 20 of the 65 corpus entries are this shape, 18 of them a spec that
advanced status. And the exposure is live rather than historical: SEVEN pending plans today cite a
spec by status directory, and one of them is THIS PLAN, which declares `25kzda` at `specs/approved/`.
Under the authored rule, the day `25kzda` moves to `implementing/` this plan and six others become
`fail-gate` on dispatch, for a path typo, having spent nothing and achieved nothing. So the refusal
is now narrowed to `moved-terminal` and `vanished`, while `aw check` keeps reporting all three. That
asymmetry is the design, not a compromise: one predicate owns the FACTS so the two surfaces cannot
disagree, and they act on different subsets because "this string is wrong" and "this work cannot be
done" are different questions.

**TWO OF THE THREE NAMED APIs WOULD NOT HAVE WORKED AS WRITTEN, AND BOTH FAIL SILENTLY.** I drove
each one. `artifact_naming.parse_clustered` returns a bare `re.Match` or `None`, so the id6 is
`m.group("id6")`; the authored phrasing ("`parse_clustered(...)`'s `id6` group") is defensible as
prose but an implementer reading it as attribute access gets `None` for every entry and routes ALL 65
through the basename fallback, taking that fallback's collision risk on every one instead of 13.
`selectors.Resolution` exposes `(paths, kind, rejected_kind, selector)` and has no `path`, `ok`, or
`matches` member; a reader written against the wrong member sees no hits and classifies everything
`vanished`, which in the authored design means REFUSE. Neither mistake raises: the predicate returns
a plausible list and the gate misbehaves quietly. I also found that `detect_artifact_type` returns
`other` for an unrecognized facet (a `.review.md`), which must skip the selector route rather than
call `resolve` with a bogus type. All three are now named in E-02 with their measurements.

**THE BASENAME FALLBACK CAN ANSWER CONFIDENTLY AND WRONGLY.** `rglob(basename)` under `.aw/records/`
is only safe for a basename unique by construction, and two corpus entries are not:
`.aw/records/research/INDEX.json` and `INDEX.md` both resolve to `.aw/records/plans/INDEX.*`, a
different type's generated index. The predicate would report `moved` with a `resolved` path that is
simply the wrong file, and the rule's recovery text would tell a human to repoint their scope at it.
A wrong answer is worse than no answer here, so the fallback is now bounded to basenames carrying a
records artifact facet, and anything else classifies `vanished` with empty `resolved`.

ON PLACEMENT, a smaller thing that would have left a visible artifact. E-04 said to insert
"immediately after `plan_path = resolve_plan_path(...)` and the `attempt` record is appended". Those
are two points about forty lines apart, and `build_prompt` then `write_prompt` run between them, the
latter WRITING a prompt file and recording a `prompt_sha256`. The later reading therefore leaves a
prompt artifact for a turn that never happens. I checked whether cost was the issue and it is not:
`build_prompt` contains no subprocess, no model call, and no git, so this is a correctness and
tidiness defect rather than a wasted-work one. E-04 now specifies before `build_prompt` with a
minimal attempt record, and requires a disclosure in V-04 if the fallback placement is taken.

ON RISK SIZING, recorded because the plan's own sizing is honest but its blast radius was not stated.
`execute_item_core` is the single function both hosts route every execute and review turn through, so
a defect in this refusal does not fail one item, it can refuse or break every item of every run. The
plan already specifies the two mitigations that matter (fail OPEN on a predicate exception, restrict
to `action == "execute"`), which is why this is a note rather than a finding; I added it to the scope
check and the gate so an approver weighs it as a hot-path change.

ON TEST DESIGN, the structural weakness behind F-8. Almost every case in E-06 asserts that something
IS refused, and the cheapest wrong implementation (refuse on any stale entry) satisfies all of them.
So the suite as authored would have passed the very design error this review corrected. The added
case 14 and the V-06 mutation are what make the suite defend the decision rather than merely exercise
the code.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | IN-SCOPE | A. correctness; D. anti-regression | review prototype: 20 of 65 stale entries are `moved` (non-retired), 18 of them specs that advanced status dir; 7 pending plans today cite a spec by status directory, including 6h8j1r itself (`specs/approved/25kzda`); `aw rename --help` rewrites references while the status setters do not | **THE AUTHORED REFUSAL WOULD REFUSE RUNNABLE PLANS.** `moved` means the target resolves to a NON-RETIRED artifact, which is still editable, so the plan can be executed and only its declared string is stale. A spec advancing `approved` -> `implementing` -> `implemented` creates this routinely and nothing rewrites the citing plan. Under the authored rule, 7 live pending plans become `fail-gate` the day their cited spec starts being implemented, for a path typo. That is a worse failure than the wasted turn the plan set out to prevent, because it converts a cosmetic staleness into a blocked queue. | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | Added as F-8. The REFUSAL now fires on `moved-terminal` and `vanished` only; `aw check` still reports all three; Concern, Scope, Goal, E-04, E-05's spec wording, E-06 case 14, the Deferred section, and the gate all state the asymmetry and why. A new V-06 mutation (refuse on any classification) must make case 14 fail, so the decision is defended by a test rather than by prose. |
| PR-302 | HIGH | IN-SCOPE | A. correctness; G. executability | driven in review: `parse_clustered(<name>)` -> `re.Match` (`.group("id6")` -> `'qhy3i3'`, no `.id6` attribute); `Resolution._fields` -> `('paths','kind','rejected_kind','selector')` (no `path`/`ok`/`matches`); `detect_artifact_type` on a nonexistent `.review.md` -> `'other'` | **TWO NAMED APIs WOULD NOT HAVE WORKED AS WRITTEN AND BOTH FAIL SILENTLY.** Reading `parse_clustered`'s result as an attribute yields `None` for every entry and routes all 65 through the basename fallback (compounding PR-303 from 13 entries to 65). Reading a nonexistent `Resolution.path` yields no hits and classifies everything `vanished`, which under the authored design means REFUSE EVERYTHING. Neither raises, so the predicate returns a plausible list and the gate silently misbehaves on the runner's hot path. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | Added as F-11. E-02 now specifies `m.group("id6")` after a None check, `r.paths` as a list with empty meaning no hit, and skipping the selector route when the type is `other`, each with the driven measurement. V-02 requires all three API shapes pasted. |
| PR-303 | MEDIUM | IN-SCOPE | A. correctness | review prototype: `.aw/records/research/INDEX.json` and `INDEX.md` both resolve via `rglob` to `.aw/records/plans/INDEX.*` | **THE BASENAME FALLBACK CAN RESOLVE TO A DIFFERENT ARTIFACT'S FILE AND REPORT IT CONFIDENTLY.** `rglob(basename)` is safe only for a basename unique by construction; a generated index name is not. The predicate reports `moved` with a `resolved` path that is the wrong file, and the rule's recovery text then advises repointing the plan's scope at it. A confidently wrong answer is worse than an honest unknown. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-10. The fallback is bounded to basenames carrying a records artifact facet (`.ipd.md`, `.spec.md`, `.backlog.md`, `.review.md`, `.release.md`, `.walkthrough.md`, `.prompt.md`, `.research.md`); anything else is `vanished` with empty `resolved`. E-06 case 15 asserts the EMPTY resolution specifically, and V-02 requires it pasted. |
| PR-304 | MEDIUM | IN-SCOPE | C. operability; G. executability | `execute_item_core` read in review: `resolve_plan_path`, then `build_prompt`/`write_prompt`, then the `attempt` dict carrying `prompt`/`prompt_sha256`, then the append; `build_prompt` measured to contain no subprocess, model call, or git | **THE INSERTION POINT NAMES TWO POINTS FORTY LINES APART AND THE LATER ONE LEAVES AN ORPHAN PROMPT FILE.** `write_prompt` writes to the run's `prompts/` directory between them, so a refusal after the attempt append records a prompt and its sha256 for a turn that never happens, polluting the run directory. Not a cost defect (the prompt build is cheap) but a correctness and legibility one on a shared hot path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-9. E-04 now specifies before `build_prompt` with a minimal attempt record, and requires that if the fallback placement is taken it be DISCLOSED in V-04 rather than leaving an unexplained artifact. E-06 case 16 asserts no prompt file exists for a refused attempt. |
| PR-305 | MEDIUM | UNDER-SCOPE | E. testing | authored E-06: 12 of 13 cases assert a refusal; the naive "refuse on any stale entry" implementation satisfies all of them | **THE SUITE AS AUTHORED WOULD HAVE PASSED THE DESIGN ERROR IN PR-301.** A gate is only as good as its negative cases, and this one had a single negative (case 13, the new-code file) that a wrong classification split would not catch. Nothing pinned that a runnable plan stays runnable. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 gains case 14 (a `moved` plan reaches its launcher AND `aw check` reports it), case 15 (PR-303), case 16 (PR-304); V-06 gains a MUTATION requirement: flip the refusal to fire on any classification and case 14 must fail. A test-design rule was added to Required tests recording why these are not optional padding. |
| PR-306 | LOW | IN-SCOPE | A. correctness (live-artifact counts cited as facts) | re-measured: corpus total 58 -> 65 (40/18/0 -> 45/20/0) in days; "13 of 24 approved plans" -> 11 approved plans with `Scope-Paths` and 30 missing non-records entries across all pending statuses | Every population number in the plan is a live count on a shared tree, and two of them had already drifted between authoring and review. The conclusions held both times, but E-01 and E-07 compare against these numbers, so a reader could treat expected drift as a failed check. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Findings preamble marks which rows were re-driven and gives both readings; F-4 widened to all pending statuses; F-5 and F-12 record the drift; E-01 and E-07 and their V-items require re-derivation and forbid comparing against the plan's integers; a RE-DERIVE rule added to the gate. |
| PR-307 | LOW | IN-SCOPE | B. security/operability (blast radius unstated) | `execute_item_core` is the single dispatch path for both hosts, every action | The plan edits the runner's hot path and said nothing about what a defect there costs. Its two mitigations (fail open on exception, `execute`-only) are already correct, so this is a disclosure gap rather than a design gap, but an approver sizing "one refusal in one function" should know it gates every item of every run. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A risk paragraph added to the Scope check and a "what this touches" paragraph to the gate, both naming the mitigations that make it acceptable. |
| PR-308 | LOW | UNDER-SCOPE | F. KISS/UX (a severity that fires on the innocent) | measured: 7 pending plans cite a spec by status directory, so a routine spec transition would create an `error` finding on each | The rule is registered `error` for all three classifications. That is right for `moved-terminal`/`vanished` (the plan is unexecutable) and questionable for `moved`, where a routine, correct spec transition creates an `error` on a plan whose only defect is a string. Not resolvable from the repository: it is a risk-appetite call about a published rule's severity. | C:Low; U:Low; S:Low; F:Low; Overall:Low | OPEN | Raised as OQ-04, `Blocking: no`, owner maintainer, with three shapes and a recommendation (`warning` for `moved`), and an explicit instruction to execute as authored if unanswered so a non-blocking question cannot hold the plan. Left OPEN rather than decided because changing a rule's severity, or teaching the status setters to rewrite citing scopes, is beyond this plan's fence. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the dispatch refusal fire on a plain `moved` (non-retired) target, as authored? | NO. Refuse on `moved-terminal` and `vanished` only; report all three in `aw check`. | (a) Refuse on all three as authored: rejected, it refuses plans that are runnable. A non-retired artifact is editable, so the work can be done; measured, 20 of 65 corpus entries and 7 live pending plans (including this one) are exposed, and the trigger is a routine spec status advance that rewrites nothing. (b) Drop `moved` from the predicate entirely: rejected, it is genuinely useful information and `aw check` should tell a human the path is wrong; deleting the classification would lose that. (c) Refuse on `moved` but only for plans-type targets: rejected as an unprincipled special case with no evidence behind it. | Drove the prototype over the whole corpus and listed all 20 `moved` entries with declared and resolved paths (18 specs that advanced status); confirmed `aw rename` rewrites references while `aw specs set`/`aw ipd set` do not; counted 7 pending plans citing a spec by status dir. | yes |
| D-2 | The predicate's basename fallback resolved two entries to the wrong file. Restrict the fallback, or drop it? | RESTRICT it to basenames carrying a records artifact facet; classify anything else `vanished` with empty `resolved`. | (a) Keep it unrestricted: rejected, a confidently wrong `resolved` path is worse than an unknown, and the rule's recovery text would actively advise repointing a scope at the wrong file. (b) Drop the fallback entirely: rejected, it is load-bearing for the 13 legacy-named entries with no id6 slot, which is exactly the population the id6 route cannot serve. (c) Disambiguate a multi-hit by preferring the same type directory: rejected as unnecessary complexity; measured 0 ambiguous multi-hit cases, and the facet restriction already removes the observed failures. | Prototype output naming both `INDEX.*` entries and their wrong resolutions; route histogram showing 13 fallback versus 52 id6 resolutions; 0 multi-hit. | yes |
| D-3 | Where exactly should the refusal sit in `execute_item_core`? | Before `build_prompt`, with a minimal attempt record; a fallback placement is allowed but must be disclosed in V-04. | (a) Leave the authored "immediately after ... the attempt is appended": rejected, it leaves a prompt file and a `prompt_sha256` for a turn that never runs. (b) Mandate before `build_prompt` with no fallback: rejected as over-specification; I cannot prove from reading alone that the minimal attempt record satisfies every downstream reader of `attempts`, so the executor needs a sanctioned alternative with a disclosure obligation rather than a rule they may have to silently break. | Read the function: `resolve_plan_path`, then `build_prompt`/`write_prompt`, then the attempt dict with `prompt`/`prompt_sha256`, then the append. Measured `build_prompt` has no subprocess, model call, or git, so the motive is tidiness rather than cost. | yes |
| D-4 | Is the `error` severity for a plain `moved` finding correct? | DO NOT DECIDE. Raise it as OQ-04 for the maintainer with a recommendation. | (a) Change it to `warning` myself: rejected, it is a risk-appetite call on a published rule's severity and the repo does not answer it; the same evidence supports either reading. (b) Say nothing: rejected, the measurement (7 innocent pending plans, one being this plan) is exactly the kind of consequence a human should see before approving, and it would otherwise be discovered from a red check after a routine spec transition. (c) Fix the cause by teaching the status setters to rewrite citing `Scope-Paths`: recorded as option (c) in the question but not chosen here; it touches every status setter and is far outside this fence. | Counted the 7 pending plans citing a spec by status directory; confirmed no reference rewriting on status transitions; the rule's own severity is declared in this plan's E-03. | yes |
| D-5 | The authored test suite would have passed the PR-301 design error. Add cases, or note the weakness? | ADD CASES AND A MUTATION, and record the structural reason. | (a) Note it in the review only: rejected, the review record is not a test and the next author would rebuild the same blind spot. (b) Add case 14 without the mutation: rejected, a negative case can itself be vacuous; the mutation is what proves it bites. | 12 of the authored 13 cases assert a refusal, so the naive implementation satisfies them all; the plan-review rubric's own anti-regression section requires mapping each invariant to a test. | yes |

### Deferred and open

- ONE FINDING IS LEFT OPEN: PR-308, raised as OQ-04 with `Blocking: no`. It is not deferred under the
  Fix Bar (its remediation risk is Low); it is a MAINTAINER DECISION about a published rule's severity
  that the repository cannot answer, and per this workflow I must not invent a human's judgement. The
  plan is executable as authored if it goes unanswered, and the gate says so explicitly, so the open
  question does not make the plan `NO-GO` (maintainer ruling of 2026-09-10: only an unresolved
  BLOCKING question does).
- The other seven findings are FIXED in place. None reached Medium-High or High Remediation Risk, so
  the Fix Bar permitted no deferral. PR-301 and PR-302 are the two Medium-overall ones, both on the
  functionality axis, and both were fixed by narrowing behavior rather than by adding machinery.
- No `Reversible: no` decision was made. All five decisions are plan-text choices on an unexecuted
  plan; D-4 deliberately declines to decide and hands the call to the human instead.

HONEST LIMITS, stated because they bound what this round proves. FIRST, I verified the predicate's
algorithm by PROTOTYPING it, not by reading the future implementation: my prototype agreed with the
plan's design and exposed F-10 and F-11, but the executor's code is what must be validated, and V-02
through V-04 are written to demand that. SECOND, I did not exercise the dispatch refusal, because it
does not exist yet; my claims about `execute_item_core` come from reading it and from driving
`build_prompt`'s contents, so the placement finding (F-9) is an argument about code structure rather
than an observed run. THIRD, my corpus scan covers `.aw/records/plans/**/*.ipd.md` only. The predicate
will be called on plan text, so that is the right population, but a stale `Scope-Paths` entry in a
plan stored outside that tree would be invisible to my measurement. FOURTH, the counts I report are
live-artifact counts and will have drifted again by execution, which is the whole point of PR-306.
FIFTH, on OQ-04 I measured the exposure (7 plans) but not the FREQUENCY of spec status transitions,
so I can say the trigger is routine and cannot say how often it would fire per month.
