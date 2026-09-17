# Review findings: plan tx6q0h

- Subject-Id: tx6q0h
- Subject-Type: ipd
- Reviewed-At: 2026-09-16
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `32625ffa`. Structural preflight `aw ipd lint --phase author` CONFORMED (exit 0) before
revision. No pre-review snapshot needed: the plan was committed and unmodified. This is the second
`rununify` child reviewed today and it repeats its sibling's pattern in a different key: structurally
clean, carefully argued, and resting on a central measured claim that does not survive checking.

THE CLAIM AND WHAT IT ACTUALLY MEASURES. F-1 asserts these 8 symbols are the ones whose "entire
behavioral difference is a host-identifying string" and that "every changed code line in each diff
carries a host token". I diffed all 8 with docstrings stripped, so only executable code was compared,
and then rendered the prompt/report output to compare emitted text. The claim holds for FIVE:
`_compute_scope_reconciliation` (4 changed lines, all host tokens, the cleanest symbol in the plan),
`_detect_driver_command`, `render_continuation_hint`, `build_verifier_prompt` and
`enforce_requested_action`. It fails for THREE, each in a different and consequential way.

`driver_actor` IS A CAPABILITY DIFFERENCE WEARING A STRING'S CLOTHES. oc builds its actor from
`options.model`, `options.variant` and `options.launch_profile.applied`; agy reads `options.model` and
nothing else. That is not a label, because `runner_profiles`, `resolve_launch_profile` and
`launch_profile` each grep to ZERO occurrences in `agy_runipd.py`: the host has no profile subsystem to
populate those keys. "Take the oc logic per the ruling" therefore hands agy two permanently-dead
branches. This matters beyond the one symbol, because it also invalidates the plan's F-2, which sells
agy's new `- Launch:` line as an improvement. I rendered it: for any agy-shaped state
`render_launch_identity` returns `model=(host default); profile=(none recorded)`. agy would gain a
permanent line announcing that no profile is recorded, on a host where none can ever be. agy's omission
of that line is CORRECT for a host without profiles, not the near-defect the plan calls it, so OQ-01's
resolution inverts.

`build_prompt` CHANGES WHAT AN AGENT IS TOLD TO DO. I rendered both hosts' non-isolated prompt from one
fixture: 34 lines differ and 32 carry no host token. The differences are instructions. Only oc's agent
receives the paragraph directing it to preserve partial work through "the repository-supported
nonterminal checkpoint mechanism or an attributable isolated branch/worktree", the clause "Leave every
checkout you did not own safe for subsequent turns", "Never claim executed unless the real terminal
state and acceptance criteria support it", and the instruction to say so explicitly when no material
question arose. So agy turns are structurally likelier to strand partial work and to over-claim
completion, which are failures this repository has repeatedly paid for. Adopting oc's text is probably
right, and it is unambiguously a behavior change to a live host, which the parent Set forbids a child to
make unilaterally. That is OQ-03, and it is the one thing I refused to decide.

`write_report` HAS FOUR DIFFERENCES, THE PLAN NAMES TWO, AND ONE OF THE UNNAMED ONES IS A LIVE BUG.
Beyond the header title and the `Verify`/`Verification` column, agy wraps the verify cell in BACKTICKS
where oc emits it bare, and uses `N/A` where oc uses an empty string. The backticks are the finding.
`run_viewer.load_run_summary` parses this table and strips backticks for id6, setid, action and session,
but NOT for the verification column (`run_viewer.py:1008`); `:1370` then compares that value to the bare
string `verified`. Measured: agy's row parses to `` '`verified`' ``, which never matches, so no `aw agy
run` has ever rendered the `[verified]` badge in the run viewer. Adopting oc's form REPAIRS it. This is
the plan's most valuable user-visible outcome and it was invisible in the plan, filed as an undisclosed
side effect of a cosmetic rename.

I ALSO FOUND A SAFETY GAP NEITHER HOST'S PLAN MENTIONS. agy's verifier prompt contains NO push
prohibition: the string "Never push" appears once in oc's `build_verifier_prompt` and zero times in
agy's, in an in-scope-fixes clause that otherwise matches word for word and instructs the agent to fix
defects and commit. Both hosts' EXECUTION prompts carry a push prohibition, so this is a verifier-path
gap only. That converts the `build_verifier_prompt` lift from a title swap into a safety fix, and I have
recommended it be made regardless of how OQ-03 is answered.

TWO STALE DOCSTRINGS WOULD HAVE BEEN PROMOTED TO SHARED TRUTH. Lifting a docstring into
`runner_shared` makes it the single source of truth, so a false claim inside one gets worse, not
better. agy's `enforce_requested_action` states that `--full-auto` "DEFAULTS TO TRUE on this host". It
does not, and has not since the 2026-09-04 maintainer ruling recorded 3,500 lines below it at
`agy_runipd.py:5358`; measured, `parse_args(['start','x']).full_auto` is `False` on both hosts. The same
docstring cites `determine_action` as the action-deriving helper, and that is the second error, which
also collapses the plan's dependency argument: `action_for` and `determine_action` are BOTH already in
`runner_shared` (`:4703`, `:4711`), they are DIFFERENT functions rather than two names for one job
(`action_for` adds orchestrator dispatch and delegates the rest), and BOTH hosts' `initialize_run` call
`action_for`. So F-5's "cite whichever name survives child 03" describes a situation that does not
exist, and the `Item-Dependencies: executed:i3d6ml` edge it justified is unfounded. I closure-checked
all 8: only `build_prompt` needs anything child 03 owns, and `build_prompt` is now excluded. I removed
the edge, which frees this plan to run first, and that is a genuine improvement to the Set's shape
rather than a loosening.

WHAT I FIXED AND WHAT I LEFT. I re-scoped the plan to the 6 symbols that are sound, split the four-way
E-02 into single-concern items, added the F-9 descriptor field the plan's own "every field must be
justified" rule surfaced (agy's verifier prompt names `run_command`, an agy tool mapped at
`agy_runipd.py:503`, so an unparameterized lift would tell an OpenCode agent to use a tool it does not
have), made the exclusions a deliverable with proof-of-absence evidence, made non-vacuity bidirectional,
required F-13's new test to be shown FAILING first, fenced the five test files the change must edit, and
named the suite baseline with its one known flake. I did NOT decide OQ-03, because whether agy's agent
instructions change is the maintainer's call.

THE PLAN IS EXECUTABLE AS REVISED and its payoff is better than it originally claimed: 6 symbols
unified, one live run-viewer defect repaired, one verifier safety gap closed, two stale docstrings
corrected, and a dependency edge removed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-101 | BLOCKER | IN-SCOPE | A. correctness; G. executability | measured diffs of all 8 with docstrings stripped; rendered prompt/report output at HEAD `32625ffa` | **F-1's CENTRAL CLAIM IS FALSE FOR 3 OF THE 8.** "Every changed code line carries a host token" holds for five symbols and fails for `driver_actor` (10 of 12 changed lines carry no host token), `write_report` (5 of 6), and `build_prompt` (32 of 34 RENDERED lines). Each fails differently: a host capability, an undisclosed behavior change, and an agent-instruction change. A descriptor is sufficient for five of them and insufficient for three, so the plan's own premise does not license its scope. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | OPEN | Measurement recorded (Goal table, F-7/F-8/F-11). Five symbols re-scoped into E-02; `write_report` isolated into E-04 with full disclosure; the two genuinely out-of-scope symbols excluded in E-05. The `build_prompt` disposition is the maintainer's: escalated as OQ-03. |
| PR-102 | BLOCKER | IN-SCOPE | C. architecture; D. anti-regression | `oc_runipd.py:906`,`:909` vs `agy_runipd.py:924`; zero occurrences of `runner_profiles`/`resolve_launch_profile`/`launch_profile` in `agy_runipd.py` | **`driver_actor` IS A HOST-CAPABILITY DIFFERENCE, so it is out of scope by this plan's own definition.** oc reads `options.variant` and `options.launch_profile.applied`, populated by a profile subsystem agy does not have. Lifting it gives agy permanently-dead branches. Same cause invalidates the `- Launch:` improvement: measured, `render_launch_identity({'options':{}})` yields `model=(host default); profile=(none recorded)`, so agy gains a permanently misleading line. | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium | FIXED | Both excluded permanently in E-05 (not deferred: they do not belong to a host-descriptor child at all). V-05 requires the zero-occurrence grep and the rendered string as evidence; E-06 asserts `driver_actor` stays per-host so a later agent cannot unify it. OQ-01's resolution inverted with the measurement. |
| PR-103 | HIGH | IN-SCOPE | A. correctness; E. observable behavior | `run_viewer.py:1008`, `:1370`; agy's backticked cell vs oc's bare cell | **AGY's BACKTICKED VERIFY CELL IS A LIVE DEFECT AND THE PLAN NEVER NOTICED.** `run_viewer` strips backticks for four columns but not the verification column, then compares to the bare string `verified`. Measured: agy's row parses to `` '`verified`' ``, so no agy run has ever shown the `[verified]` badge. Adopting oc's form repairs it, making this the plan's best user-visible outcome, and F-2 filed it as an unnamed side effect of a header rename. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 records all four `write_report` differences and names the backtick removal as a bug fix; Required tests item 2 and V-04 require the repair proven END TO END through `run_viewer.load_run_summary`, not merely asserted. |
| PR-104 | HIGH | IN-SCOPE | D. anti-regression; B. security (agent instructions) | rendered non-isolated prompts, both hosts, one fixture: 34 differing lines, 32 with no host token | **UNIFYING `build_prompt` CHANGES THE INSTRUCTIONS AGY's AGENT RECEIVES, which the parent Set forbids a child to do unilaterally.** Only oc's agent is told to preserve partial work via the nonterminal checkpoint mechanism, to leave checkouts it did not own safe, and never to claim executed unless the terminal state supports it. Adopting oc's text is arguably right and is unambiguously a behavior change on a live host. | C:Medium; U:Low; S:Medium; F:Medium-High; Overall:Medium-High | OPEN | Cannot be decided from evidence: the repo establishes the diff, not the policy. Excluded provisionally in E-05 and escalated as OQ-03 with four options and a recommendation (option 2: give the prompt-text unification its own plan). |
| PR-105 | HIGH | UNDER-SCOPE | B. security; E. testing | `build_verifier_prompt`: "Never push" appears 1x in oc, 0x in agy | **AGY's VERIFIER PROMPT OMITS ANY PUSH PROHIBITION while instructing the agent to fix defects and commit.** Both hosts' execution prompts carry one, so the gap is verifier-path only and was invisible to the plan. This makes the `build_verifier_prompt` lift a safety fix rather than a title swap. | C:Low; U:Low; S:Medium; F:Medium; Overall:Low | FIXED | Recorded as F-13; Required tests item 3 adds a both-hosts push-prohibition assertion, and V-06(c) requires it shown FAILING before the change, since a test that was always green proves nothing about the gap it claims to close. Recommended to land regardless of OQ-03's answer. |
| PR-106 | MEDIUM | IN-SCOPE | A. correctness (a lifted docstring becomes shared truth) | `agy_runipd.py:1889` vs `:5358`; measured `parse_args(['start','x']).full_auto is False` on both hosts | **A STALE DOCSTRING CLAIM WOULD BE PROMOTED INTO THE SHARED MODULE.** agy's `enforce_requested_action` says `--full-auto` "DEFAULTS TO TRUE on this host"; the 2026-09-04 maintainer ruling normalized it to `False` and the module records that 3,500 lines below. Lifting the docstring unchanged makes a false statement the single source of truth for both hosts. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-03 repairs it before/as the lift, and V-03 requires the parsed default pasted for BOTH hosts rather than the docstring merely reworded. |
| PR-107 | MEDIUM | IN-SCOPE | G. dependencies and sequencing | `runner_shared.py:4703`,`:4711`; both hosts' `initialize_run` call `action_for` | **F-5's PREMISE IS WRONG AND THE DEPENDENCY IT JUSTIFIES IS UNFOUNDED.** `action_for` and `determine_action` are both already shared and are DIFFERENT functions, not two names for one job, so nothing is "waiting on child 03" and there is no name to pick. Closure-checked, only `build_prompt` needs anything child 03 owns, and it is now excluded. The `executed:i3d6ml` edge made this plan wait for no reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Edge removed (`Item-Dependencies: none`), which frees the plan to run first; agy's stale `determine_action` citation folded into E-03; the withdrawn premise recorded in Deferred so it is not re-proposed. |
| PR-108 | MEDIUM | UNDER-SCOPE | C. architecture (descriptor completeness) | `agy_runipd.py:2785` names `run_command`; the tool mapping at `agy_runipd.py:503` | **THE DESCRIPTOR FIELD LIST OMITS A HOST-SPECIFIC TOOL NAME the verifier prompt emits.** agy tells the agent to run tests "using `run_command`", an agy tool name. Lifting `build_verifier_prompt` without parameterizing it would instruct an OpenCode agent to use a tool it does not have. Surfaced by the plan's own rule that every field be justified by a named call site. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01's field list now includes the shell-tool-name field with its call site cited, and V-01 requires explicit confirmation it is present. |
| PR-109 | MEDIUM | UNDER-SCOPE | G. right-sizing and conceptual density | E-02 as authored: four producers spanning 313 oc lines including the 127-line `build_prompt` | **ONE ITEM BUNDLED TWO INDEPENDENT TEST-SURFACES.** Prompt text and report text need unrelated V-items, and the item mixed a 127-line prompt builder with a 71-line report writer plus two smaller symbols. A passing count lint does not clear this. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-02 (five string-only symbols), E-03 (docstring facts), E-04 (`write_report` alone with its behavior repair), E-05 (exclusions), E-06 (proof). Cohesion rationale now records the evaluation instead of asserting `standard`. |
| PR-110 | MEDIUM | UNDER-SCOPE | G. scope fence | `build_prompt` referenced by 8 test files; `driver_actor`/`enforce_requested_action`/`_compute_scope_reconciliation` by `test_oc_runipd.py` and `test_agy_runipd_cli.py`; `build_verifier_prompt` by `test_reporting_contract.py` | **THE FENCE NAMED ONE NEW TEST FILE AND NO EXISTING ONE,** though every lifted symbol has existing coverage that must move with it and F-12's repair changes what `test_run_viewer.py` fixtures parse. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Five existing test files added to `Scope-Paths`, each named in Project conventions or Required tests with the assertion that constrains the change. |
| PR-111 | LOW | IN-SCOPE | E. testing (a cited suite proves nothing) | `tests/test_run_summary_table.py` exercises `render_run_summary_table`, already shared | **A NAMED VALIDATION SUITE DOES NOT TEST THIS CHANGE.** It covers a already-shared renderer, not `write_report`'s output, so listing it as evidence is a false comfort. The real guards are `test_reporting_contract.py:500` (both hosts' prompts) and `test_lane_prompt_purity.py` (both hosts, digest-compared path block). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests item 5 rewritten to name the two suites that actually guard this surface and to say explicitly that `test_run_summary_table.py` is not relevant (F-15). |
| PR-112 | LOW | IN-SCOPE | E. achievable bar | measured bare `python3 -m pytest`: `1 failed, 7308 passed, 3 skipped, 2 xfailed`; the failure passes in isolation | **THE BASELINE WAS UNSTATED AND ONE FAILURE IS PRE-EXISTING.** "No new failure against the baseline at execution time" leaves the executor to rediscover that `ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130` is a load-dependent 30s subprocess timeout. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-16 records the measurement; Required tests item 6 and V-06(d) name the flake and require the isolation re-run as the disposing evidence. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | F-1 claims all 8 differ only by a host string. Trust it, or re-measure? | RE-MEASURE, comparing executable code with docstrings stripped AND rendering the emitted prompt/report text. | (a) Trust the plan, rejected: the same Set's sibling child was reviewed hours earlier and its analogous claim was also inverted, so the method (not the author) was the thing to check. (b) Diff raw source including docstrings, rejected as noisy: prose differences are real but do not decide liftability, and the plan would have been condemned for comment drift rather than for the three genuine cases. | measured diffs of all 8, docstrings stripped; rendered non-isolated prompts and report rows from one fixture at HEAD `32625ffa` | yes |
| D-2 | Does `driver_actor` belong in a host-descriptor plan? | NO. Exclude it permanently as a host-CAPABILITY difference. | (a) Lift it and let agy's variant/profile branches be inert, rejected: it ships dead code reading keys nothing populates, and a later reader cannot tell dead-by-design from broken. (b) Give agy profile support so the lift becomes honest, rejected as far out of scope and a question nobody has asked. (c) Defer it to a later child, rejected as misleading: it is not waiting on anything, it simply is not a string. | `oc_runipd.py:906`,`:909` vs `agy_runipd.py:924`; zero occurrences of `runner_profiles`/`resolve_launch_profile`/`launch_profile` in `agy_runipd.py` | no |
| D-3 | OQ-01 resolved that agy SHOULD gain the `- Launch:` line. Keep that, or invert it? | INVERT. Exclude the line. | (a) Keep it as additive disclosure, rejected on measurement: it renders `profile=(none recorded)` on every agy run forever, which is noise, not disclosure. (b) Add the line but suppress the profile clause for agy, rejected: that is a per-host conditional inside the shared renderer, which is the forking this Set exists to end. | `render_launch_identity({'options': {}})` returning `model=(host default); profile=(none recorded)`, measured at review | yes |
| D-4 | Should the `executed:i3d6ml` dependency edge stay? | REMOVE it. | (a) Keep it as harmless caution, rejected: an unfounded edge makes a runnable plan wait, and the runner re-checks edges at dispatch, so a false edge has a real cost. (b) Keep it because `build_prompt` needs child 03, rejected: `build_prompt` is now excluded, and it was the only one of the 8 that needed anything child 03 owns. | `runner_shared.py:4703`,`:4711`; both hosts calling `action_for` in `initialize_run`; closure check of all 8 against child 03's 48 | yes |
| D-5 | Is F-13's missing "Never push" in agy's verifier prompt this plan's business or a separate bug? | THIS PLAN's, and recommended to land regardless of OQ-03's answer. | (a) File it as a separate backlog item, rejected: the plan already lifts `build_verifier_prompt`, so the fix is one line of the work it is already doing, and splitting it would leave a known safety gap open while a scoping question waits. (b) Fold it into OQ-03's options, rejected as coupling a safety fix to a policy decision; it appears as option 4 there but is recommended independently. | "Never push" counted 1x in oc's verifier prompt and 0x in agy's, in an otherwise word-for-word clause instructing the agent to commit | yes |
| D-6 | `build_prompt`'s 32 non-host-token instruction differences: decide, or ask? | ASK. Raised as OQ-03, `Blocking: yes`, four options and a recommendation. | (a) Adopt oc's text myself since it is plainly safer, rejected: it changes what a live host's agent is instructed to do, and the parent Set explicitly forbids a child changing what a runner DOES; "obviously better" is exactly the reasoning a gate exists to interrupt. (b) Parameterize both prose variants to preserve behavior, rejected as duplication wearing a parameter (recorded as option 3 for the maintainer, not chosen by me). | rendered prompt diff, 34 lines differing with 32 carrying no host token; the parent orchestrator's no-behavior-change constraint on children | yes |

### Deferred and open

- `PR-101` - `OPEN`:
  - Reason: The measurement is settled and the five sound symbols are re-scoped, but the disposition of `build_prompt` (the third failing symbol) is a policy choice about agent instructions.
  - Remediation Risk: Medium-High
  - Axis: complexity, functionality
  - Required decision or evidence: the maintainer's answer to OQ-03.
  - Consequence if unresolved: the plan delivers 6 of 8 symbols and the two hosts keep sending materially different rulebooks to their agents, with agy's omitting the preserve-partial-work and never-over-claim instructions.
- `PR-104` - `OPEN`:
  - Reason: Adopting oc's prompt text is a behavior change on a live host; the parent Set forbids a child to make one unilaterally, and leaving it forked is also a defensible choice.
  - Remediation Risk: Medium-High
  - Axis: security, functionality
  - Required decision or evidence: same OQ-03 answer.
  - Consequence if unresolved: agy turns remain likelier to strand partial work and to claim executed without the terminal state supporting it, because its agent is never told otherwise.

### Escalation of the irreversible decision

D-2 is judged `Reversible: no`: it excludes a symbol on the ground that lifting it would ship dead code,
and the cost of being wrong is discovered as an inert branch nobody can distinguish from a broken one.
Escalated per the workflow rather than merely recorded: it is raised in the plan as F-7, cited by the
`Blocking: yes` OQ-03 whose `- Finding:` field names PR-101 and PR-104, made a deliverable in E-05 with
proof-of-absence evidence in V-05, and converted into a standing assertion by E-06's inverse table, so
the suite refuses the lift even if a future agent disagrees with me. The maintainer sees it at the
OQ-03 gate before anything executes. D-3 and D-4 are reversible (a plan edit undoes each) and are
recorded only.

### Honest limits of this review

- I DID NOT PERFORM THE LIFT, so "these five are host-string-only" rests on static diffing plus rendered
  output from ONE fixture, not on having moved the code. A host difference reachable only on a code path
  my fixture did not exercise would not appear. E-01/E-02 re-derive the field list at execution time.
- MY PROMPT COMPARISON USED A SINGLE NON-ISOLATED, NON-RECOVERY FIXTURE. The isolated and recovery
  branches interpolate more, so the 34-line figure is a floor, not a ceiling. That direction does not
  weaken PR-104; it strengthens it.
- I DID NOT JUDGE WHETHER oc's PROMPT TEXT IS THE RIGHT TEXT. I judged that the two differ materially and
  that choosing between them is a decision. Whether the preserve-partial-work paragraph is well written
  is a question for whoever answers OQ-03.
- F-12's REPAIR IS VERIFIED BY PARSE SIMULATION, not by running the viewer end to end: I reproduced
  `run_viewer`'s column logic on both hosts' row shapes and confirmed the mismatch. V-04 requires the
  executor to prove it through the real `load_run_summary`, which is the stronger evidence I did not
  produce.
- I READ THE SUITE BASELINE ONCE (7308 passed, one load-dependent flake). A second run under different
  load could surface a different flake.

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
| PR-101 | BLOCKER | IN-SCOPE | round 1 finding, discharged by directive | this plan's resolved `OQ-03`; the maintainer's 2026-09-16 directive | Unifying the agent-prompt builder would change the instructions one host gives its agent, which the Set forbids a child to do unilaterally. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The maintainer AUTHORIZED the instruction change on 2026-09-16, selecting option 4 (adopt the safer text for both hosts AND fix the verifier push omission in the same act). The direction is favorable: the 32 non-host-token lines only one host receives are the partial-work-preservation, leave-others-checkouts-safe and do-not-over-claim instructions. The plan must disclose the before/after in its evidence. See the resolved OQ-03. |
| PR-104 | HIGH | IN-SCOPE | round 1 finding, discharged by directive | this plan's resolved `OQ-03`; the maintainer's 2026-09-16 directive | The verifier prompt on one host tells its agent to commit but never tells it not to push. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Ruled fixed HERE regardless of the scoping answer. Re-verified at this HEAD: the verifier prompt omits any push prohibition while the other host ends the same sentence with "Never push." (`agent_workflows/oc_runipd.py:5729`); both hosts DO carry "5. Never push to remote." in the EXECUTOR prompt (`agy_runipd.py:2009`, `oc_runipd.py:3281`), so the gap is specific to the verifier path. |

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
