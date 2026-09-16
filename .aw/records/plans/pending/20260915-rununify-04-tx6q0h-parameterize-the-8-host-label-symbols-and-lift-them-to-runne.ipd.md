# IPD: Parameterize the 8 host-label symbols and lift them to runner_shared

- Date: 2026-09-15
- Kind: child
- Concern: 8 symbols are duplicated across both runners and their difference is DOMINATED by a host-identifying string (`aw oc run` vs `aw agy run`, a report title, an argv token). They must not be left forked, because the shared logic around each string keeps drifting independently. CORRECTED AT REVIEW 2026-09-16: the word "ONLY" was false for 3 of the 8, and the plan's F-1 asserted it of all 8. Measured with docstrings stripped, 5 of 8 differ ONLY by a host token in executable code; `driver_actor` differs by a real CAPABILITY (oc emits variant+profile, agy emits neither and has no profile machinery at all), `write_report` by three things beyond the title, and `build_prompt`'s emitted PROMPT TEXT differs by 32 lines that carry no host token. See F-7 through F-13.
- Scope: Design ONE host-descriptor the shared library takes as a parameter, then lift the definitions that are genuinely host-string-only into `runner_shared.py` with the host string supplied by the caller rather than baked in. Logic comes from the `oc_runipd` version per the maintainer's 2026-09-14 ruling; only the string becomes a parameter. THE THREE NON-STRING SYMBOLS NEED A DIFFERENT ACT and are OQ-03, which is `Blocking: yes`: adopting oc's `build_prompt` rewrites the INSTRUCTIONS agy's agent receives, which is a behavior change the parent Set forbids a child to make unilaterally.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_rununify_host_descriptor.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_reporting_contract.py, tests/test_lane_prompt_purity.py, tests/test_run_viewer.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: rununify
- Order: 4
- Highest E allocated: 06
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: tx6q0h
- From-Backlog: alw22r

## Workflow history
- 2026-09-16 reviewed (aw set): Reviewed 2026-09-16 by /plan-review: REVIEWED - OPEN QUESTIONS, NO-GO. 12 findings (PR-101..PR-112), 10 FIXED, PR-101/PR-104 OPEN and escalated as blocking OQ-03. F-1's claim that all 8 symbols differ only by a host string is false for 3: driver_actor is a host capability difference, write_report has four differences not two, and build_prompt's emitted instructions differ by 32 non-host-token lines. Also found a live run_viewer defect the lift repairs and a missing push prohibition in agy's verifier prompt. Dependency edge on i3d6ml removed as unfounded.
- 2026-09-16 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO; PR-101 through PR-112 (10 FIXED, PR-101 and PR-104 OPEN and escalated as the new blocking OQ-03). F-1's CENTRAL CLAIM IS FALSE FOR 3 OF THE 8. Measured with docstrings stripped, "every changed code line carries a host token" holds for five symbols (`_compute_scope_reconciliation`, `_detect_driver_command`, `render_continuation_hint`, `build_verifier_prompt`, `enforce_requested_action`) and fails for three, each differently: `driver_actor` is a host CAPABILITY difference (oc reads `options.variant`/`options.launch_profile` from a profile subsystem that greps to ZERO occurrences in `agy_runipd.py`, so the lift ships dead branches); `write_report` has FOUR differences where F-2 names two; and `build_prompt`'s EMITTED PROMPT differs by 34 rendered lines of which 32 carry no host token, including a preserve-partial-work paragraph and a "Never claim executed" clause present only on oc, so unifying it changes what agy's agent is INSTRUCTED to do. TWO DISCOVERIES THE PLAN MISSED, both improving its payoff: adopting oc's `write_report` REPAIRS A LIVE DEFECT (agy backticks the verify cell, `run_viewer.py:1008` does not strip backticks for that column and `:1370` compares to the bare string, so no agy run has ever rendered the `[verified]` badge), and agy's verifier prompt OMITS ANY PUSH PROHIBITION while instructing the agent to commit ("Never push" 1x in oc, 0x in agy). ALSO CORRECTED: OQ-01 INVERTED, because `render_launch_identity` renders `profile=(none recorded)` on any agy state, so the `- Launch:` line is noise rather than disclosure; two stale docstrings that would have been promoted to shared truth (agy claims `--full-auto` "DEFAULTS TO TRUE on this host", measured False on both; and cites `determine_action` where both hosts call `action_for`); and F-5's dependency premise, since `action_for` and `determine_action` are BOTH already in `runner_shared` as DIFFERENT functions, so the `executed:i3d6ml` edge was unfounded and is REMOVED, freeing this plan to run first. Re-scoped to the 6 sound symbols, E-02 split into single-concern items, the F-9 descriptor field added (agy's verifier names `run_command`, an agy-only tool), exclusions made a deliverable with proof-of-absence evidence, non-vacuity made bidirectional, five test files fenced, suite baseline named (7308 passed, one load-dependent flake). NOT DECIDED, deliberately: whether this child may change agy's agent instructions. Typed record at `.aw/records/reviews/20260916-rununify-04-tx6q0h-parameterize-the-8-host-label-symbols-and-lift-them-to-runne.review.md` with 12 findings and 6 decisions, 1 irreversible and escalated.
- 2026-09-15 to-review (aw set): Authored 2026-09-15 from a fresh measurement at HEAD; resolves part of the rununify parent's placeholder child rows per the maintainer's 2026-09-14 oc-preferred ruling.

- 2026-09-15 draft (opencode/its_direct-pt3-claude-opus-5): created.
- 2026-09-15 authored (opencode/its_direct-pt3-claude-opus-5): authored from a fresh per-symbol diff at HEAD; each of the 8 was inspected and its host-bearing lines counted.

## Goal

Remove the mechanically-duplicated symbols whose difference IS a host name by giving the shared library
a single host descriptor instead of two copies of the same function. One definition, one place to fix,
and the host string becomes data rather than code.

READ THIS BEFORE EXECUTING. The 2026-09-16 review measured all 8 and found the plan's central claim
(F-1: "every changed code line in each diff carries a host token") false for 3 of them. With docstrings
stripped, so that only executable code is compared:

| Symbol | Executable diff | Verdict |
|---|---|---|
| `_compute_scope_reconciliation` | 4 lines, all host tokens | HOST-STRING ONLY |
| `_detect_driver_command` | 4 lines, all host tokens | HOST-STRING ONLY (token LIST per F-3) |
| `build_verifier_prompt` | 2 lines, all host tokens | host-string only in CODE; see F-9 for its prompt text |
| `render_continuation_hint` | 4 lines, all host tokens | HOST-STRING ONLY |
| `enforce_requested_action` | 4 lines, all host tokens | host-string only in CODE; see F-10 for its stale docstring |
| `write_report` | 6 lines, 5 with no host token | NOT host-only (F-8) |
| `driver_actor` | 12 lines, 10 with no host token | NOT host-only: a real CAPABILITY difference (F-7) |
| `build_prompt` | emitted PROMPT TEXT differs by 34 rendered lines, 32 with NO host token | NOT host-only (F-11) |

THE THREE NON-STRING SYMBOLS ARE THE FINDING, and each fails differently. `driver_actor`: oc emits
`variant=` and `profile=` from a profile subsystem agy does not have at all (`runner_profiles`,
`resolve_launch_profile` and `launch_profile` grep to ZERO in `agy_runipd`), so "take the oc logic" gives
agy dead code, not a host string. `write_report`: adopting oc gives agy a `- Launch:` line that renders
`profile=(none recorded)` FOREVER on that host, which is misleading output rather than the improvement
the plan calls it. `build_prompt`: the two hosts send their agents MATERIALLY DIFFERENT INSTRUCTIONS
(oc's includes a preserve-partial-work paragraph and a "never claim executed" clause that agy's omits),
so unifying them changes what an agent is told to do, which is a behavior change, not a label swap.

WHAT THE REVIEW ALSO FOUND, and the plan did not: adopting oc's `write_report` REPAIRS A LIVE DEFECT
(F-12) and agy's verifier prompt is MISSING the "Never push" instruction entirely (F-13).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the descriptor

EXECUTOR: DO NOT START. OQ-03 is `Blocking: yes` and the lint gate refuses this plan at every
checkpoint until the maintainer answers it. E-05 names the three symbols whose disposition that answer
decides.

- [ ] E-01 Define ONE host descriptor in `runner_shared.py` carrying every host-varying string the LIFTED symbols need, measured from their actual diffs rather than guessed: the command prefix (`aw oc run` / `aw agy run`), the argv tokens `_detect_driver_command` matches (`oc`/`opencode` versus `agy`/`antigravity`, with agy additionally accepting `runagy`), the session-continuity and prompt/report titles (`OpenCode` / `Antigravity`), the report's verification column header (`Verify` / `Verification`), and the SHELL TOOL NAME the verifier prompt names (F-9: agy's prompt says `run_command`, which is an agy tool mapped at `agy_runipd.py:503` and does not exist on oc). Do NOT invent fields no symbol reads; every field must be justified by a named call site. Do NOT add a variant/profile field: that is F-7's capability difference, not a string.
  - Depends on: none
  - Expected outcome: one descriptor type with two instances (one per host), every field traceable to a symbol and line that consumes it, no unused field, and the F-9 tool-name field present with its call site cited.
  - Execution state: pending

- [ ] E-02 Lift the FIVE genuinely host-string-only symbols through the descriptor: `_compute_scope_reconciliation`, `_detect_driver_command`, `render_continuation_hint`, `build_verifier_prompt` and `enforce_requested_action`. Take the oc logic; only the string becomes a parameter. Three byte-identical constants must move with them because their bodies close over names `runner_shared` lacks: `SUCCESS_STATES` (`render_continuation_hint`), `ACTION_CHOICES` and `ACTION_IMPLEMENTED` (`enforce_requested_action`); all three are identical in both hosts, so this is a relocation and not a reconciliation. `_detect_driver_command` needs a token LIST per host, not a single token, or agy loses its `runagy` spelling (F-3). `_compute_scope_reconciliation`'s strings land in a plan's PERMANENT finalize record, so an empty host name here corrupts history (F-4).
  - Depends on: E-01
  - Expected outcome: five single definitions; three constants relocated; agy still resolves `runagy`; a finalize record still names the host that actually ran.
  - Execution state: pending

- [ ] E-03 REPAIR the two STALE DOCSTRING CLAIMS before or as you lift, because lifting them copies a falsehood into the shared module where it becomes the single source of truth. (a) agy's `enforce_requested_action` says `--full-auto` "DEFAULTS TO TRUE on this host"; it does NOT, and has not since the 2026-09-04 maintainer ruling recorded at `agy_runipd.py:5358`. MEASURED at review: `build_parser().parse_args(['start','x']).full_auto` is `False` on BOTH hosts. (b) agy's version says the derived action comes from `determine_action`; both hosts' `initialize_run` actually call `action_for`, and BOTH functions already live in `runner_shared` as DIFFERENT functions (`action_for` wraps `determine_action` and adds orchestrator dispatch), so F-5's premise that these are two names for one job is wrong. The shared docstring must cite `action_for` and must not claim a default it does not have.
  - Depends on: none
  - Expected outcome: the shared docstring states the ACTUAL `--full-auto` default (False, both hosts) and cites `action_for`; the measurement that establishes each is pasted rather than asserted.
  - Execution state: pending

- [ ] E-04 Lift `write_report` and DISCLOSE what it actually changes, which is more than the plan originally claimed. Adopting oc's version does four things to agy's report: it renames the header, renames the `Verification` column to `Verify`, REMOVES the backticks agy wraps the verify cell in, and changes agy's empty-verify placeholder from `N/A` to an empty cell. THE BACKTICK REMOVAL IS A BUG FIX, not cosmetics (F-12): `run_viewer.py:1008` reads that column WITHOUT stripping backticks and `run_viewer.py:1370` compares it to the bare string `verified`, so agy's `` `verified` `` never matches and every agy run renders the wrong verification badge today. Do NOT also adopt the `- Launch:` line: see E-05.
  - Depends on: E-01
  - Expected outcome: one definition; the backtick removal recorded as REPAIRING the `run_viewer` badge for agy, with the before/after parse shown; the `N/A`-to-empty change stated.
  - Execution state: pending

- [ ] E-05 DO NOT LIFT `driver_actor` OR `build_prompt`, and do not give agy the `- Launch:` line. Record why, as a deliverable rather than a silent skip. `driver_actor`: oc's body reads `options.variant` and `options.launch_profile`, populated by a profile subsystem that does not exist on agy (`runner_profiles`, `resolve_launch_profile`, `launch_profile` all grep to ZERO in `agy_runipd.py`), so lifting it hands agy permanently-dead branches; this is the host-CAPABILITY case child 04 was never scoped for. `- Launch:` has the same cause: `render_launch_identity` renders `profile=(none recorded)` for any agy state, MEASURED at review, so the "improvement" is a permanently misleading line. `build_prompt`: the two hosts' emitted prompts differ by 34 rendered lines of which 32 carry NO host token, including a preserve-partial-work paragraph and a "Never claim executed" clause present only on oc, so unifying them CHANGES THE INSTRUCTIONS agy's agent receives. That is a behavior change and it is OQ-03's subject.
  - Depends on: E-01
  - Expected outcome: an execution-report paragraph naming all three exclusions with the measurement that justifies each, and the explicit statement that lifting them is a capability or behavior change rather than a completion of this plan.
  - Execution state: pending

### Task group 2: proof

- [ ] E-06 Add `tests/test_rununify_host_descriptor.py`: each LIFTED symbol resolves to the SAME OBJECT from both hosts; each host's descriptor produces its OWN strings (so the parameterization is real and not a hardcoded default); an AST scan proves neither runner still defines any lifted symbol; a NEGATIVE case proves a missing descriptor field fails loudly rather than emitting an empty host name into a permanent record; and the INVERSE assertions that `driver_actor` and `build_prompt` are STILL defined per host, so a later agent cannot "finish the job" by lifting a capability difference. Drive it from a named table, not from the literal 8.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: a suite that fails if a lifted symbol is re-forked, if a host's strings collapse to one host's, if a descriptor field goes silently empty, OR if an excluded symbol is lifted.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared.py` already uses NAME/VALUE INJECTION for exactly this problem rather than importing a
  host: `run_checked(..., env_builder=)`, `save_state(..., write_report=)`, and plan `b7xarm`'s
  `resume_via_launcher(launcher, ...)`, which was chosen specifically so no third launcher call site
  appears. A host descriptor is the same pattern applied to strings instead of callables.
- `integrate_lane_branch` is the precedent to copy: it already takes `host_label="aw oc run"` so the
  merge subject on main reads `integrate(aw oc run): ...`. That is a one-field descriptor in
  everything but name, and it proves the approach works in this codebase.
- `attention_contract.actor_refusal` refuses a parenthesized actor, so `driver_actor`'s output shape is
  constrained by a live gate, not merely by convention. VERIFIED at review: `attention_contract.py:590`
  refuses any `(` or `)`, and it refuses an EMPTY actor too, which is the second half worth knowing for
  a descriptor whose field could go blank.
- `tests/test_run_flag_surface.py` reads spec `25kzda` 2.1 as a FILE in both directions, so a flag
  surface must not be touched here; none of these 8 registers a flag except `_add_output_mode_flags`,
  which is child 03's and is display-only.
- `action_for` AND `determine_action` BOTH ALREADY LIVE IN `runner_shared` (`:4703`, `:4711`) and are
  DIFFERENT functions, not two names for one job: `action_for(kind, status)` adds orchestrator dispatch
  and delegates everything else to `determine_action(status)`. Both hosts import both and both call
  `action_for` from `initialize_run`. This is why F-5's stated dependency on child 03 was withdrawn
  (F-10) and why agy's docstring citing `determine_action` is a stale-prose bug rather than a real
  divergence.
- `run_viewer.load_run_summary` PARSES the execution report's markdown table (`run_viewer.py:1008`) and
  strips backticks for id6/setid/action/session but NOT for the verification column. That asymmetry is
  what makes agy's backticked verify cell a live defect (F-12), and it is the reason `write_report`'s
  unification has a user-visible payoff rather than being cosmetic. An executor changing that column
  must keep it BARE.
- THE PROMPT SURFACE IS GUARDED BY TWO PARAMETERIZED SUITES, both looping over BOTH hosts from one
  body, so a prompt change cannot land on one host only: `tests/test_reporting_contract.py:500` asserts
  the reporting contract and the required JSON keys in both hosts' execution and verifier prompts, and
  `tests/test_lane_prompt_purity.py` asserts lane-path purity plus a sha256 digest over the
  non-isolated path block. The digest covers a five-line block both hosts already share, so a prompt
  lift does not automatically break it, but it does mean any change to those five lines fails loudly.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | measured at HEAD | These 8 are the ONLY shared symbols whose entire behavioral difference is a host-identifying string. Every changed code line in each diff carries a host token. That is what makes a descriptor sufficient and a judgement call unnecessary. **FALSE FOR 3 OF THE 8, corrected at review 2026-09-16; see F-7, F-8, F-11 and the Goal table.** The claim holds for `_compute_scope_reconciliation`, `_detect_driver_command`, `render_continuation_hint`, `build_verifier_prompt` and `enforce_requested_action`. |
| F-2 | HIGH | `write_report` | The difference is NOT only the title. oc emits a `- Launch:` line via `render_launch_identity` and a `Verify` column; agy emits neither and spells the header `Verification`. So adopting oc GIVES agy the launch-identity line, an improvement, but it changes agy's report shape and must be disclosed. **PARTLY WRONG: the `- Launch:` line is NOT an improvement on agy (F-7), and the finding MISSES two further differences plus a live defect (F-8, F-12).** |
| F-3 | MED | `_detect_driver_command` | agy accepts a THIRD argv token (`runagy`) that oc has no analogue for. The descriptor must carry a LIST of accepted tokens per host, not a single token, or agy loses an invocation spelling. **VERIFIED at review: `agy_runipd.py:5089` matches `run`/`runipd`/`runagy` against `agy`/`antigravity`; oc matches `run`/`runipd` against `oc`/`opencode`.** |
| F-4 | MED | `_compute_scope_reconciliation` | Its two host strings are written into a plan's PERMANENT finalize record as the auto-reconciliation reason. A descriptor bug here would misattribute which host reconciled a scope, so this is the one symbol where an empty or defaulted host string is a history-corrupting defect rather than a cosmetic one. **VERIFIED at review, and this is the cleanest symbol in the plan: 4 changed executable lines, all host tokens.** |
| F-5 | MED | `enforce_requested_action` | Its diff is only the helper NAME quoted in its own explanatory message (`action_for` vs `determine_action`), which means the two hosts call differently-named functions for the same job. Child 03 lifts one of them; this plan must cite whichever name survives, so it is ordered AFTER child 03 by declared dependency. **THE PREMISE IS WRONG AND SO IS THE DEPENDENCY IT JUSTIFIES; see F-10. Both functions ALREADY live in `runner_shared` (`:4703`, `:4711`), they are DIFFERENT functions rather than two names for one job, and BOTH hosts' `initialize_run` call `action_for`. agy's docstring is simply stale.** |
| F-6 | LOW | `driver_actor` | Both hosts already agree on the parenthesis-free `model=` shape because a setter-side gate refuses the alternative. So the only real difference is the command prefix, which the descriptor supplies. **THE GATE CLAIM IS VERIFIED (`attention_contract.actor_refusal:590` refuses any parenthesis) BUT THE CONCLUSION IS FALSE: the command prefix is NOT the only difference. See F-7.** |

### Findings added by the 2026-09-16 plan review

| # | Sev | Where | Finding |
|---|---|---|---|
| F-7 | BLOCKER | `driver_actor`; `oc_runipd.py:906`,`:909`; `agy_runipd.py:924` | **`driver_actor` IS A HOST-CAPABILITY DIFFERENCE, NOT A HOST STRING, so it is out of this plan's scope by the plan's own definition.** oc builds its actor from `options.model`, `options.variant` and `options.launch_profile.applied`; agy reads `options.model` ONLY. That is not a label: `runner_profiles`, `resolve_launch_profile` and `launch_profile` all grep to ZERO occurrences in `agy_runipd.py`, so agy has no profile subsystem to populate those keys. "Take the oc logic" therefore hands agy two permanently-dead branches. The same cause invalidates F-2's `- Launch:` improvement claim: MEASURED at review, `render_launch_identity({'options':{}})` returns `model=(host default); profile=(none recorded)`, so agy's report would carry a permanently misleading line rather than a useful one. |
| F-8 | HIGH | `write_report`; `oc_runipd.py:3679` vs `agy_runipd.py:2392` | **F-2 NAMES TWO OF FOUR DIFFERENCES.** Beyond the header title and the `Verify`/`Verification` column, agy also (a) wraps the verify cell in BACKTICKS where oc emits it bare, and (b) uses `N/A` as its empty-verify placeholder where oc uses an empty string. (a) is a live defect (F-12). Neither appears in the plan, so an executor adopting oc's version would ship two undisclosed observable changes to agy's report. |
| F-9 | MEDIUM | `build_verifier_prompt`; `agy_runipd.py:2785` | **THE VERIFIER PROMPTS DIFFER IN A HOST-SPECIFIC TOOL NAME, which a descriptor must carry or the lift breaks one host.** agy instructs the agent to run tests "using `run_command`"; `run_command` is an AGY TOOL NAME, mapped at `agy_runipd.py:503`. Telling an OpenCode agent to use `run_command` names a tool it does not have. So the descriptor needs a shell-tool-name field (or the clause must be dropped), which E-01's field list does not currently include. The plan's own rule that every field be justified by a named call site is what surfaces this. |
| F-10 | MEDIUM | `- Item-Dependencies: executed:i3d6ml`; `runner_shared.py:4703`,`:4711` | **THE DECLARED DEPENDENCY ON CHILD 03 IS UNFOUNDED, and F-5's reasoning for it is factually wrong.** `action_for` and `determine_action` are BOTH already defined in `runner_shared` and are DIFFERENT functions (`action_for` adds orchestrator dispatch and delegates the rest to `determine_action`), so neither is waiting on child 03 and there is no "whichever name survives". Both hosts import both and both call `action_for` from `initialize_run`. Closure-checked at review: of the 8, only `build_prompt` closes over anything child 03 owns (`build_isolation_notice`, `build_verify_and_continue_notice`), and `build_prompt` is now excluded by F-11. So the re-scoped plan needs NOTHING from child 03 and the edge is removed, which also frees it to run first. |
| F-11 | BLOCKER | `build_prompt`; rendered-output diff measured at review | **UNIFYING `build_prompt` CHANGES WHAT AGY'S AGENT IS TOLD TO DO, which is a behavior change the parent Set forbids a child to make.** Rendering both hosts' non-isolated prompt from one fixture: 34 lines differ and 32 carry NO host token. The differences are instructions, not labels. Present only on oc: an entire paragraph directing the agent to preserve partial work via "the repository-supported nonterminal checkpoint mechanism or an attributable isolated branch/worktree", the clause "Leave every checkout you did not own safe for subsequent turns", "Never claim executed unless the real terminal state and acceptance criteria support it", and "If no material question arose, say so in the summary". Present only on agy: an explicit `git commit -m msg -- <paths>` spelling. Adopting oc's text is arguably an improvement, but it is a DELIBERATE change to agent instructions and belongs to a decision, not to a string-parameterization child. |
| F-12 | HIGH | `run_viewer.py:1008`, `:1370`; agy's backticked verify cell | **AGY's BACKTICKED VERIFY CELL IS A LIVE DEFECT AND ADOPTING oc's FORM REPAIRS IT.** `run_viewer` parses the report table and strips backticks for id6, setid, action and session, but NOT for the verification column (`cols[5].strip()` at `:1008`); `:1370` then tests `verification_status == "verified"`. MEASURED at review: agy's row parses to `` '`verified`' ``, which never equals `verified`, so no agy run has ever rendered the `[verified]` badge. This is the plan's most valuable user-visible outcome and it is currently filed as an undisclosed side effect of a header rename. |
| F-13 | HIGH | `agy_runipd.py` `build_verifier_prompt` vs `oc_runipd.py` | **AGY's VERIFIER PROMPT OMITS "Never push" ENTIRELY.** Counted at review: the string appears once in oc's verifier prompt and ZERO times in agy's, in the in-scope-fixes clause that otherwise matches. Both hosts' EXECUTION prompts carry a push prohibition, so this is a gap in the verifier path only: agy's verifier is told to fix defects and commit, with no instruction not to push. Adopting oc's text closes it, which makes the `build_verifier_prompt` lift a SAFETY improvement worth stating rather than a title swap. |
| F-14 | MEDIUM | `- Scope-Paths:` as authored | **THE FENCE OMITS EVERY EXISTING TEST FILE THE CHANGE MUST EDIT.** Measured: `build_prompt` is referenced by 8 test files, `driver_actor`/`enforce_requested_action`/`_compute_scope_reconciliation` by `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py`, `build_verifier_prompt` by `tests/test_reporting_contract.py`, and F-12's repair changes what `tests/test_run_viewer.py` fixtures parse. The five that the re-scoped plan can actually touch are now fenced. |
| F-15 | LOW | Required tests item 4 | **A NAMED SUITE DOES NOT TEST WHAT THE PLAN THINKS.** `tests/test_run_summary_table.py` exercises `render_run_summary_table`, which is already shared and is not any of these 8; it does not read `write_report`'s output. Keeping it in the list is harmless but it is not evidence for this change. `tests/test_reporting_contract.py` IS relevant and its `DRIVERS` loop (`:500`) asserts both hosts' prompts carry the reporting contract and required JSON keys, so it is the real guard here. |
| F-16 | LOW | Required tests item 5 | **THE SUITE BASELINE IS UNSTATED AND ONE FAILURE IS PRE-EXISTING.** Measured at review, bare `python3 -m pytest`: `1 failed, 7308 passed, 3 skipped, 2 xfailed`. The failure is `tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`, a 30s subprocess timeout under parallel load that passes in isolation (`7 passed in 1.13s`). "No new failure against the baseline at execution time" is right in spirit but leaves the executor to rediscover this; it is now named. |

## Proposed changes (ordered, validatable)

1. Define the host descriptor with only the fields the lifted symbols provably consume, including F-9's
   shell-tool-name field (E-01).
2. Lift the five genuinely host-string-only symbols, relocating three byte-identical constants (E-02).
3. Repair the two stale docstring claims before they become the shared source of truth (E-03).
4. Lift `write_report`, disclosing all four changes and the `run_viewer` badge repair (E-04).
5. Record the `driver_actor` / `build_prompt` / `- Launch:` exclusions as a deliverable (E-05).
6. Add the descriptor suite with the negative empty-field case and the inverse exclusion assertions (E-06).

## Deferred / out of scope (with reason)

- The 48 no-disagreement symbols: child 03 (`i3d6ml`). NOTE the dependency edge on it was REMOVED at
  review (F-10): closure-checked, the re-scoped plan needs nothing child 03 owns, so it may run first.
- `extract_session_id`, `driver_begin`: child 05. Genuine behavior conflicts, not host strings.
- `PlanRecord`, `parse_plan_file`, `build_dynamic_manifest`: child 06.
- `execute_item`, `run_queue`, `initialize_run`, `build_parser`, `main`: children 07 through 11.
- Renaming `action_for`/`determine_action` to one name repo-wide. WITHDRAWN AS A PREMISE (F-10): they
  are two DIFFERENT shared functions, not two names for one job, so there is nothing to unify. What
  remains is only fixing agy's stale docstring, which E-03 does.

### Removed from scope by the 2026-09-16 review (F-7, F-11)

- `driver_actor`. NOT deferred pending a string decision: it is a host-CAPABILITY difference (oc reads
  a profile subsystem agy does not have), so it does not belong to a host-descriptor child at all.
  Whether agy should GAIN profile support is a separate question nobody has asked.
- The `- Launch:` line in `write_report`, for the same reason: on agy it renders
  `profile=(none recorded)` permanently.
- `build_prompt`. Its emitted instructions differ materially between hosts (32 non-host-token lines),
  so unifying it changes agent behavior. Subject of OQ-03.

## Scope check

- Over-scope: none, after the review removed the three capability/behavior symbols.
- Under-scope: this plan as re-scoped lifts 6 of the 8 it named. That is the honest size of the
  "host string only" slice. The descriptor will likely be useful to children 07 through 11 as well,
  since the big functions carry host strings too; this plan builds it for its own symbols and does not
  pre-fit it to theirs, because designing for unmeasured callers is how a parameter grows fields nobody
  reads.

## Required tests / validation

1. `tests/test_rununify_host_descriptor.py` (new): object identity across hosts for each LIFTED symbol;
   each host produces its OWN strings; AST scan showing no runner re-defines a lifted symbol; the
   NEGATIVE case proving a missing/empty descriptor field raises rather than writing an empty host name;
   and the INVERSE assertions that `driver_actor` and `build_prompt` are still defined per host.
2. A REPORT-SHAPE regression for F-8, asserting all FOUR changes explicitly so none lands silently: the
   header title, the `Verify` header, the REMOVED backticks, and the `N/A`-to-empty placeholder. Plus
   F-12's repair proven end to end: feed agy's NEW report row through `run_viewer.load_run_summary` and
   assert `verification_status == "verified"`, which fails on today's backticked output.
3. F-13's safety close: assert BOTH hosts' verifier prompts contain a push prohibition. Today agy's
   contains none, so this test fails before the change and passes after.
4. `tests/test_agy_runipd_cli.py` and `tests/test_oc_runipd.py` green (both render reports and prompts).
5. `tests/test_reporting_contract.py` green: its `DRIVERS` loop (`:500`) asserts both hosts' prompts
   carry the reporting contract and the required JSON keys, which is the real guard on a prompt lift.
   `tests/test_lane_prompt_purity.py` green too, since it parameterizes prompt assertions over BOTH
   hosts including a digest-compared path block. (`tests/test_run_summary_table.py` is NOT relevant
   here; see F-15.)
6. Bare `python3 -m pytest`, summary pasted, at or above the 7308-passed baseline MEASURED AT REVIEW
   2026-09-16, with NO NEW failure judged against the one known flake named in F-16; if that test fails,
   show it passing in isolation rather than treating it as a regression.
7. NON-VACUITY, in BOTH directions. (a) Force the descriptor to return oc's strings for BOTH hosts and
   show the suite FAILS naming agy, then restore; without this, "each host produces its own strings"
   can pass while both silently resolve to one host. (b) Lift one EXCLUDED symbol (`driver_actor`) into
   the shared module and show the suite names it, then restore; without this, a later agent can
   "complete" the plan by unifying a capability difference.

## Spec / documentation sync

No `.spec.md` change. These are internal producers, and the operator-visible surfaces they emit
(prompt text, execution report) are not spec-pinned in shape.

CHECKED AT REVIEW 2026-09-16 and the no-change conclusion HOLDS, with two corrections to what must be
disclosed. FIRST, the disclosure list was wrong: agy's report does NOT gain a `- Launch:` line (that is
now excluded, F-7 and OQ-01), and the renames are FOUR changes rather than one (F-8), of which the
backtick removal is a bug fix (F-12). SECOND, the spec adjacency worth naming: `enforce_requested_action`
implements spec `25kzda` 2.6 (`--action` "cannot force a status transition, execute an unapproved item,
or turn a non-runnable record into a runnable one") and 2.1, and its refusal messages are the enforcement
of that requirement. Lifting it must not weaken either refusal, which is why V-02 requires the `--action`
safety assertions green by name rather than merely a green suite. `tests/test_run_flag_surface.py` reads
that spec as a FILE in both directions, so no flag surface may be touched here; none of the lifted
symbols registers a flag.

## Open questions

### OQ-01: Does agy gaining oc's `- Launch:` report line count as a behavior change this Set forbids?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: SUPERSEDED AT REVIEW 2026-09-16, and the answer INVERTS. The
  original reasoning was sound in form (a report-content change is not a runner-behavior change) but
  rested on an unchecked premise: that the line would say something useful on agy. It does not.
  MEASURED at review, `render_launch_identity({'options': {}})` returns
  `model=(host default); profile=(none recorded)`, because the fields it renders
  (`options.variant`, `options.launch_profile`) are populated only by a profile subsystem that does not
  exist on this host: `runner_profiles`, `resolve_launch_profile` and `launch_profile` each grep to ZERO
  occurrences in `agy_runipd.py`. So agy would gain a permanent line asserting no profile is recorded,
  which is noise an operator must learn to ignore rather than "additive disclosure". agy's omission is
  therefore NOT closer to a defect than a feature; it is correct for a host with no profiles. The
  `- Launch:` line is now EXCLUDED (E-05) and the question is closed against adopting it. Whether agy
  should gain profile support is a real question, but a different one, and nobody has asked it.

### OQ-02: Should the descriptor be a dataclass, a NamedTuple, or a plain mapping?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: Whatever the executor picks, it must FAIL LOUDLY on a missing field,
  which is the property F-4 makes load-bearing (a silently empty host name would be written into a
  permanent finalize record). A plain mapping with `.get()` is therefore the one form to avoid. The
  choice between a frozen dataclass and a `NamedTuple` is left to the executor since both raise on a
  missing attribute; `runner_shared` already uses `NamedTuple` widely, so that is the path of least
  surprise.

### OQ-03: Unifying `build_prompt` changes the INSTRUCTIONS agy's agent receives. Which do you want?

- Blocking: yes
- Finding: PR-101, PR-104
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT RESOLVABLE FROM REPOSITORY EVIDENCE. The evidence settles what
  is TRUE; it does not settle what should be DONE, because the choice is about what a runner tells its
  agent to do, and the parent Set's own constraint is that a child may not change what a runner DOES.
  THE SYMPTOM, plainly: the two hosts hand their agents different rulebooks today. Rendering both
  non-isolated prompts from one fixture, 34 lines differ and 32 carry no host token. Only oc's agent is
  told to preserve partial work through "the repository-supported nonterminal checkpoint mechanism or an
  attributable isolated branch/worktree", to "Leave every checkout you did not own safe for subsequent
  turns", to "Never claim executed unless the real terminal state and acceptance criteria support it",
  and to say so explicitly when no material question arose. An agy agent is told none of that. So agy
  turns are likelier to strand partial work and likelier to over-claim completion, which are exactly the
  failures this repository has repeatedly paid for.
  WHY IT IS NOT MINE TO DECIDE: adopting oc's text is a deliberate change to agent instructions on a
  live host, with a real (if favorable) behavior consequence, and the Set forbids a child to make one
  unilaterally. Leaving it forked is also a choice, and a defensible one.
  The options:
  1. ADOPT oc's prompt text for both hosts here, treating it as the ruling's natural consequence, and
     disclose the instruction change as a behavior improvement. Fastest, and it closes a real safety gap;
     it also makes this child the plan that changed agy's agent instructions, which its title does not
     say.
  2. EXCLUDE `build_prompt` from this plan (what I have provisionally done) and give the prompt-text
     unification its own plan, where the instruction diff can be reviewed line by line and the safety
     rationale recorded. Slower, honest about what is being changed, keeps this child a string change.
  3. UNIFY ONLY THE HOST STRINGS in `build_prompt` and leave both hosts' instruction paragraphs exactly
     as they are, sharing the scaffolding and parameterizing the prose blocks. Preserves behavior
     exactly, but it means the shared function carries two prose variants, which is duplication wearing
     a parameter and will drift again.
  4. ADOPT oc's text AND fix agy's verifier "Never push" omission (F-13) in the same act, treating both
     as one prompt-safety correction rather than two.
  My recommendation is OPTION 2 for `build_prompt` and, separately, that F-13's missing "Never push" be
  fixed HERE regardless of the answer, because a verifier told to commit with no push prohibition is a
  safety gap that should not wait for a scoping decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the descriptor definition pasted, with each field annotated by the symbol and LINE that consumes it; a statement that no field is unconsumed; and explicit confirmation that the F-9 shell-tool-name field is present (with `agy_runipd.py:503`'s mapping cited) and that NO variant/profile field was added.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `oc_runipd.X is agy_runipd.X` -> `True` and `X.__module__` -> `agent_workflows.runner_shared` for all five lifted symbols. PLUS the three per-symbol proofs the findings make load-bearing: agy still resolves `runagy` (F-3, exercised not asserted); a finalize auto-reconciliation reason naming the correct host for EACH host (F-4); and a parenthesized actor still refused where `enforce_requested_action`'s neighbours touch actor output. PLUS confirmation that `SUCCESS_STATES`, `ACTION_CHOICES` and `ACTION_IMPLEMENTED` are now single definitions.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: BOTH corrections proven by measurement, not by reading. (a) Pasted output of `build_parser().parse_args(['start','x']).full_auto` for BOTH hosts showing `False`, and the shared docstring quoted to show it no longer claims otherwise. (b) Pasted evidence that both hosts' `initialize_run` call `action_for` (an AST or grep result), and the shared docstring quoted citing `action_for` rather than `determine_action`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted identity result for `write_report`; a BEFORE/AFTER of agy's rendered report row showing ALL FOUR changes (header title, `Verify` column, backticks removed, `N/A` placeholder gone); and F-12's repair proven END TO END by feeding the new row through `run_viewer.load_run_summary` and showing `verification_status == "verified"` where the old backticked row yielded `` '`verified`' ``. Explicit confirmation that the `- Launch:` line was NOT added.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the exclusion disclosure PLUS proof the exclusions still hold, since this item's deliverable is an absence. Paste: `driver_actor` and `build_prompt` each still defined in BOTH runners and absent from `runner_shared`; the grep showing `runner_profiles`/`resolve_launch_profile`/`launch_profile` at ZERO occurrences in `agy_runipd.py` (the measurement that justifies excluding them); and `render_launch_identity({'options': {}})` rendering `profile=(none recorded)`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: FOUR parts, all pasted. (a) `python3 -m pytest tests/test_rununify_host_descriptor.py -o addopts=""` green. (b) The NON-VACUITY control in BOTH directions: descriptor forced to oc's strings for both hosts produces a named failure, then restored; AND `driver_actor` lifted into the shared module produces a named failure, then restored. (c) F-13's safety test shown FAILING before the change and passing after, since a test that was always green proves nothing about a gap it claims to close. (d) Bare `python3 -m pytest` at or above 7308 passed with no new failure, judged against F-16's named flake, plus `tests/test_reporting_contract.py` and `tests/test_lane_prompt_purity.py` green by name.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. EVALUATED AT REVIEW 2026-09-16 rather than inherited, since a passing
  count lint does not clear conceptual density. As authored, E-02 bundled four prompt/report producers
  spanning 313 oc lines including the 127-line `build_prompt`, which is two distinct
  test-surfaces (prompt text and report text) and would have needed unrelated V-items; that is a
  right-sizing failure the count lint could not see. As revised each item is one concern: E-02 lifts the
  five string-only symbols, E-03 repairs two docstring facts, E-04 lifts one function with one disclosed
  behavior repair, E-05 records exclusions, E-06 proves it.

OQ-03 IS OPEN AND `Blocking: yes`. `aw ipd lint` refuses this plan at every checkpoint until the
maintainer answers it, including `aw ipd begin`, so it cannot be executed or auto-approved as it stands.
That is the intended gate: the question is whether this child may change the instructions agy's agent
receives, and the Set forbids a child to decide that alone.

EXECUTION CONTRACT. Commit ONLY the declared `Scope-Paths`, path-scoped; never `git add -A` and never
push. Paste the ACTUAL runner output for every `V-*`. Run the suite BARE as `python3 -m pytest`.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

REVIEWER'S HIGHEST-VALUE TARGETS, restated after the 2026-09-16 review:

1. F-7 and E-05's EXCLUSIONS. The most likely way to damage this repository from this plan is to read
   `driver_actor` as a host string and unify it, handing agy dead branches that read a profile subsystem
   it does not have. V-05 and V-06(b) exist to prove the exclusion held.
2. F-12's `run_viewer` REPAIR. Verify it independently rather than trusting the plan: confirm that
   `run_viewer.py:1008` really does skip backtick-stripping for column 5 and that agy's row therefore
   never matches `:1370`'s `verified` test. It is the plan's best user-visible outcome and it was
   originally invisible in the plan.
3. F-13's MISSING "Never push". agy's verifier prompt has no push prohibition at all while being told to
   commit. Check that the new test FAILS before the change (V-06(c)), or it proves nothing.
4. F-4 (an empty descriptor field corrupts a permanent finalize record, so E-06's negative test matters
   most) and F-3 (dropping agy's `runagy` token silently breaks an invocation spelling).
