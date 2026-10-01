# IPD: Report the runs the filters excluded instead of answering a partial selection as an empty one

- Date: 2026-09-30
- Kind: child
- Concern: `aw runs` resolves a selector to N runs, lets its six filters silently discard some or all of them, and then answers as if the discarded runs never matched. MEASURED in this lane at HEAD `522598b6` against a two-run fixture whose token `probe` resolves to BOTH runs: `aw runs probe --status executed` renders ONE run (`run-...-beta`), never names `run-...-alpha`, and exits 0, with `grep -ci 'alpha|excluded|filter'` over the whole output returning `0`. The resolver disagrees with the report and only the resolver is right: `resolve_target_runs_detailed(['probe'], Path('.'))` returns BOTH directories with `unresolved=[]`. The total-exclusion case is worse because it is indistinguishable from an empty repository: `aw runs --ipd zzzzzz` and `aw runs probe --status executed` (with both runs non-`executed`) each print the bare line `no matching runs found` at exit 0, and `--agent` prints `{"runs": []}` at exit 0, which is byte-identical to what a genuinely run-less repository emits. So an operator who typos `--ipd` or names a status no step reached is told "nothing matched" about runs that DID match, and a script reading `{"runs": []}` concludes there is nothing to look at.
- Scope: Make `aw runs` report the runs its FILTERS excluded, reusing the matched-vs-acted vocabulary the `runnoop` Set already shipped rather than inventing a second one. IN: computing the excluded set and the exclusion REASON (which filter removed each run) inside `run_viewer_cli`'s existing filter loop; reporting it on the human surface and on the `--agent`/`--json` surface; keeping the exit code at 0. OUT: the UNRESOLVABLE-TARGET case, which `7wei1o` already refuses at exit 2 and which this plan must not touch or re-spell; `aw find`, wholly owned by pending plan `zyj8io`; `aw ipd set`, which is Order 02 of this Set; changing WHICH runs any filter selects; the `--json` payload SHAPE beyond adding one key; and the `render_stream` run summary table.
- Scope-Paths: agent_workflows/run_viewer.py, tests/test_run_viewer.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: om3rzi
- Set: dispreach
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: 9jkek2
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved

- 2026-09-30 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-601, PR-602, PR-603, PR-604 all FIXED, zero deferred, zero open findings. Structural lint `conforming` at `--phase author` and `--phase review-finalize`. THE DIAGNOSIS IS CORRECT AND REPRODUCES END TO END, re-measured at HEAD `bdb8cc764` in a purpose-built two-run fixture rather than read back. The resolver really does disagree with the report: `resolve_target_runs_detailed(['probe'], Path('.'))` returns BOTH run directories with `unresolved=[]`, while `aw runs probe --status executed` renders only `run-...-beta` at exit 0 with `grep -ci 'alpha|excluded|filter'` returning **0** (F-01, F-02 confirmed). Total exclusion really is indistinguishable from an empty repository: `aw runs --ipd zzzzzz` and a no-matching-status filter each print the bare `no matching runs found` at exit 0 and `--agent` prints exactly `{"runs": []}` (F-03 confirmed). The refusal fence is genuinely already correct and is correctly fenced out: `aw runs nosuchrun123` exits **2** naming the token, the leaves and the `--` escape (F-04 confirmed). F-07 confirmed by probe (importing `run_selection_policy` alone loads none of `run_viewer`/`cli`/`render_stream`; all three import together OK), F-08 confirmed (`reason` is free text; `skip_reason_text` really does test membership against `SKIP_REASON_LABELS` rather than the tuple, so the recorded trap is real), F-09 confirmed (zero hits for both searches), F-10, F-11 and F-13 confirmed by reading. FOUR FINDINGS, THE FIRST TWO MATERIAL. PR-601 (F-14): E-03's instruction to add "one key alongside the existing `runs` array" on BOTH machine surfaces is UNIMPLEMENTABLE on `--agent`'s partial path, because the two surfaces share a shape only on the TOTAL path. Measured, `--json` partial is a `runs` envelope while `--agent` partial is one JSON object PER RUN as JSONL with no envelope, so there is no array for a sibling key; wrapping the stream to create one would break every line-oriented consumer, a worse change than the defect. E-03 now carries a per-surface decision, V-03 demands the JSONL shape be shown intact with a discriminated record, and both now require the `--latest`/`--summary`/`--issues` early-return branches' coverage to be stated rather than silently skipped. PR-602 (F-06): the "fence is uncontested" claim is FALSIFIED. `run_viewer.py` is declared by FOUR other pending plans, not one, and `qvfd4l` E-03 edits THIS PLAN'S EXACT filter loop while its own F-09 already names `9jkek2`. Recorded in F-06, the Scope check and a new gate paragraph, with the honest framing that the runner's worktree isolation makes this a merge to resolve rather than a runtime hazard. PR-603 (F-15): "seven filters" double-counts the unreadable-state skip; there are SIX filter predicates and seven `continue` statements, so a fixture built to exercise "all seven filters" cannot be built as described; corrected in eight places. PR-604 (F-12): the tree is not unconditionally green and the authored `3246 passed` has drifted to `3401 passed` in one day; the one failure is the same midnight-boundary flake in `tests/test_backlog.py` seen elsewhere in this sweep, outside this plan's fence, so every suite bar is now a re-derived baseline compared by failing NODE ID. All three open questions verified correctly resolved and non-blocking; OQ-03's resolution survives with its caveat extended by PR-601. Findings and four Decisions rows in `.aw/records/reviews/20260930-dispreach-01-9jkek2-report-the-runs-the-filters-excluded-instead-of-answering-a.review.md`. No production file and no test modified.
- 2026-09-30 to-review (opencode): Authored from backlog item `om3rzi`, whose deferred row 4 on orchestrator `7ewc74` is the carrier statement. Every claim below was MEASURED in this lane at HEAD `522598b6` against a purpose-built two-run fixture, not read off the item. THREE findings changed the shape of the work relative to what the item proposed. FIRST, the item names three verbs and ONE of them is already fully owned: pending plan `zyj8io` (`selquiet` Order 01, `- Status: to-review`, from backlog `hd5bkk`) declares `agent_workflows/cli.py` and `tests/test_cli_find.py` and its E-03 already computes a PER-TOKEN match fact for `aw find` keyed on matched-not-resolved, including the multi-type and post-narrowing traps. Authoring an `aw find` item here would duplicate a reviewed-in-progress plan and contend for its file, so this Set covers TWO verbs and records the third as owned. SECOND, `aw runs` does NOT have the gap the item implies. Its unresolvable-TARGET case is already correct: `7wei1o` shipped `resolve_target_runs_detailed` returning `(resolved, unresolved)` plus a three-renderer refusal at exit 2, measured working (`aw runs nosuchrun123` exits 2). The REAL gap is one layer later, in the FILTERS, which is a different mechanism (a resolved run silently dropped) needing a different answer (a report at exit 0, not a refusal), because a filter excluding a run is a legitimate narrowing and not a failed request. THIRD, the partial case is sharper evidence than the total case and the item does not mention it at all: with a mixed fixture the command renders one run and omits the other with ZERO mention, so the defect is not merely "an ambiguous empty answer" but "an answer that silently under-reports its own selection".
  DELIBERATE VOCABULARY CONSTRAINT, recorded so an executor does not invent a parallel one. The `runnoop` Set placed the disposition vocabulary in `agent_workflows/run_selection_policy.py`, whose import purity is load-bearing (only `selectors` and `status_set` as first-party imports). This plan CONSUMES that module and does not extend it: measured in this lane, `run_viewer.py` importing `run_selection_policy` at module level introduces NO cycle (probed by patching the import in and importing `run_viewer` and `cli`, both `OK`, then reverted clean), because `run_selection_policy` imports neither `run_viewer` nor `cli` nor `render_stream`. That measurement is what makes E-01's reuse a fact rather than a hope.

## Goal

Make `aw runs` answer the question it was asked about every run its selector matched. A filter narrowing a selection is legitimate; answering a narrowed selection as though the excluded runs never matched is not, because it spells "your filter removed these" exactly the same way it spells "nothing matched" and, in the partial case, says nothing at all. Report the exclusions and their reasons using the vocabulary the `runnoop` Set already shipped, and keep exit 0 throughout, because nothing here is a failed request.

TWO FACTS ESTABLISHED AT AUTHORING so the executor does not re-derive them and does not inherit a premise measurement has already falsified.

1. THE RESOLVER AND THE REPORT DISAGREE, AND ONLY THE RESOLVER IS RIGHT. Measured at HEAD `522598b6` on a fixture of two runs both declaring setid `probe`, one with a `reviewed` step and one with an `executed` step:

   ```text
   $ aw runs probe --status executed          -> renders run-...-beta only, exit 0
                                                 grep -ci 'alpha|excluded|filter' -> 0
   $ resolve_target_runs_detailed(['probe'])  -> (['run-...-alpha','run-...-beta'], [])
   ```

   So the function that decides what matched says TWO and the report shows ONE, with no line reconciling them.

2. TOTAL EXCLUSION IS INDISTINGUISHABLE FROM AN EMPTY REPOSITORY, on both surfaces:

   ```text
   $ aw runs --ipd zzzzzz            -> "no matching runs found", exit 0
   $ aw runs probe --status executed -> "no matching runs found", exit 0   (both runs non-executed)
   $ aw runs probe --status executed --agent -> {"runs": []}, exit 0
   ```

   The same two outputs are what a repository with zero runs emits, so neither a human nor a script can tell a filter typo from an empty tree.

WHY EXIT 0 IS CORRECT HERE AND MUST NOT BE CHANGED, since this is the one design question an executor is most likely to get wrong by analogy. The adjacent `aw find` plan `zyj8io` moves a zero-match selector to exit 2, and copying that here would be wrong: a zero-match SELECTOR is a failed request (the caller asserted an artifact exists and it does not), whereas a filter excluding a run is the filter DOING ITS JOB. The existing code says so at `run_viewer.run_viewer_cli`'s empty-state comment ("THE GENUINE EMPTY STATE, which stays a SUCCESS"), whose comment records that reaching the empty state means "a FILTER excluded what matched, or the repository simply has no runs. Neither is a failed request, so both keep exit 0 (runsverify 7wei1o, OQ-01)". This plan does not dispute that; it fixes the fact that the two cases the comment names are reported IDENTICALLY, by making the first one say which filter did it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: compute the exclusion fact

- [x] E-01 COMPUTE THE PER-RUN EXCLUSION FACT inside the existing filter loop in `run_viewer.run_viewer_cli` (the loop opened by `summaries: list[RunSummary] = []`), recording for each resolved run directory that was dropped WHICH filter dropped it. Build it by restructuring the loop's seven `continue` statements so each records a reason before skipping, rather than by adding a second pass that re-applies the filters (a second pass is two predicates for one fact and will drift, which is the failure `resolve_target_runs_detailed`'s own docstring records for the union-versus-detailed split). CONSUME the shared vocabulary rather than inventing one: import `agent_workflows.run_selection_policy` and use `render_item_disposition` for the per-run line, so `aw runs` reports an exclusion in the SAME shape both hosts already report a skipped artifact. Measured in this lane, that import at `run_viewer.py` module level introduces no cycle. Include the run whose `load_run_summary` returns falsy (its `if not summary: continue`), which is TODAY a silent `continue` and is an exclusion with its own reason (unreadable state), NOT a filter match. DO NOT change which runs any filter selects: every run in today's `summaries` list must still be in it, in the same order.
  - Depends on: none
  - Expected outcome: a structure mapping each excluded run directory to its reason code is available after the loop; `summaries` is byte-identical to today's for every input; `--last` truncation in the `if last_n is not None and summaries:` block is ALSO an exclusion and is recorded distinctly from the six filters, because a run dropped by `--last` matched every filter and was discarded by a count.
  - Execution state: performed

### Task group 2: report it on both surfaces

- [x] E-02 REPORT THE EXCLUSIONS ON THE HUMAN SURFACE, in both the partial case (some runs rendered) and the total case (none rendered, today's bare `no matching runs found` the `term.line("no matching runs found")` call). Name each excluded run and its reason. In the TOTAL case the current single line is the whole output and must become a line that distinguishes "your filters excluded N runs that matched" from "this repository has no runs", which is the pair today's output conflates; keep the existing wording for the genuinely-empty case so a repository with no runs reads exactly as it does now. Write the exclusion report to STDOUT, not stderr, and state the reason in a comment: this is not a refusal (exit stays 0) and `7wei1o`'s stderr choice was for a REFUSAL whose stated reason is that a refusal must never land in a stream a caller parses. Do NOT emit the report when there is nothing to report, so an unfiltered `aw runs` is byte-identical to today.
  - Depends on: E-01
  - Expected outcome: the partial case names the excluded run and its reason; the total-with-exclusions case is textually distinct from the total-without-exclusions case; a bare `aw runs` and any invocation excluding nothing produce byte-identical output to HEAD; exit stays 0 in every case.
  - Execution state: performed

- [x] E-03 REPORT THE EXCLUSIONS ON THE MACHINE SURFACES (`--agent` and `--json`), ADDING a key rather than changing the shape of anything an existing consumer parses. Keep `exit` at 0 and keep the record honest about what it is: this is a complete answer to a narrowed query, not a refusal, so do not borrow the refusal's `outcome: "cannot-run"`.

  THE TWO MACHINE SURFACES ARE NOT THE SAME SHAPE, AND THE AUTHORED "one key alongside the existing `runs` array" IS NOT IMPLEMENTABLE ON `--agent`'s PARTIAL PATH (review PR-601, F-14). Measured: on the TOTAL path both surfaces share one statement, `print(json.dumps({"runs": []}, indent=2 if is_json else None))`, so both emit a `runs` ENVELOPE. On the PARTIAL path they diverge. `--json` builds `payload = {"runs": [asdict(s) for s in summaries]}` and prints ONE object, so a sibling key is natural. `--agent` instead loops `for s in summaries: print(json.dumps(s_dict, ...))`, emitting ONE JSON OBJECT PER RUN as JSONL with NO envelope and therefore NO array to sit a key beside. So this item needs TWO decisions, not one:

  (a) `--json`: add the key to the existing `payload` dict on the partial path and to the `{"runs": []}` total-path payload, exactly as authored.

  (b) `--agent`: do NOT wrap the JSONL stream in an envelope, which would break every line-oriented consumer and is a far worse change than the defect being fixed. Emit the exclusion fact as ONE ADDITIONAL JSONL RECORD, carrying a discriminator field so a consumer can tell it from a run record, printed AFTER the run records. Match the total path, which already emits an envelope on this surface, by ALSO emitting the key there as authored; the asymmetry between the two paths is pre-existing and this plan must not try to fix it. If the executor judges a different `--agent` shape better, that is a design change needing its own open question, not an improvisation: record it and stop.

  ALSO NOTE `--latest`, `--summary` and `--issues` each have their OWN early-returning branch on BOTH surfaces (`if latest_only:`, `elif summary_only:`, `if issues_only:`), measured, and they return before the generic path. State explicitly in the evidence which of those branches carry the key and which do not, and why; silently covering only the generic path would leave a consumer of `--latest --agent` with the same ambiguity this plan is closing.

  Model the key's NAME on `unresolved_targets` in `run_viewer._unresolvable_target_refusal` so a consumer that handles one handles the other. If the emitted record goes through `_agent_schema.assert_valid_agent_record`, validate it with that validator rather than by eye; measured, the total branch emits `{"runs": []}` via a plain `json.dumps` and NOT a schema-validated record, so say that explicitly in the evidence rather than inventing a validation that does not apply.
  - Depends on: E-01
  - Expected outcome: both machine surfaces carry the excluded runs and their reasons; `--json`'s `{"runs": [...]}` keeps its shape with one sibling key added; `--agent`'s PARTIAL path stays line-oriented JSONL with one additional discriminated record rather than gaining an envelope; a total exclusion is distinguishable from an empty repository on both surfaces; the `--latest`/`--summary`/`--issues` branches' coverage is stated explicitly either way; exit stays 0.
  - Execution state: performed

### Task group 3: coverage

- [x] E-04 ADD TESTS to `tests/test_run_viewer.py` driving the REAL CLI over a purpose-built multi-run fixture, asserting on observable output and exit codes: the PARTIAL case names the excluded run (the case no existing test covers and the one with the sharpest evidence); the TOTAL-exclusion case is textually and payload-distinct from the genuinely-empty case; a bare `aw runs` and an exclusion-free invocation are byte-identical to the pre-change behavior (capture the expectation as a literal, not by re-running the new code); `--last` truncation reports as an exclusion; an unreadable `state.json` reports as an exclusion rather than vanishing; and the unresolvable-TARGET case still refuses at exit 2 with its existing message, which is the regression fence around `7wei1o`'s shipped behavior. Assert on returned output, exit codes and payload keys only; do NOT read production source text, count callers, or pin a docstring (GUIDING_PRINCIPLES P16).
  - Depends on: E-02, E-03
  - Expected outcome: new tests fail on the pre-E-01 tree (the partial-case assertion fails because no mention of the excluded run exists) and pass after E-03; `7wei1o`'s exit-2 refusal is pinned unchanged; the byte-identity of the unfiltered path is pinned.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `run_viewer.run_viewer_cli` is the one entry point for this verb; it resolves targets through `run_viewer.resolve_target_runs_detailed`, reads the SIX filters (`set_filter`, `ipd_filter`, `status_filter`, `failed_only`, `active_only`, `since_dt`) plus `issues_only`, noting the loop's SEVEN `continue` statements are those six plus the unreadable-state skip (F-15), refuses an unresolvable target (NOT this plan's subject), then runs the filter loop beginning at the statement `summaries: list[RunSummary] = []` that this plan restructures, applies `--last` truncation, and reaches the empty state guarded by `if not summaries and not issues_only:` that this plan disambiguates (`agent_workflows/run_viewer.py`, around lines 3413-3604 at HEAD `522598b6`).
- `run_viewer.resolve_target_runs_detailed` is the precedent for this plan's whole shape: its docstring states it exists because "the union alone cannot distinguish 'you asked for nothing specific' from 'everything you asked for is missing'". This plan applies the same argument one layer later, to filters.
- `run_selection_policy.render_item_disposition` is the shared per-artifact line renderer (`m85gxh` E-01), deliberately PURE and reason-text-driven; see also `run_selection_policy.ACTED_REASON_LABEL` and `run_selection_policy.DISPOSITION_HEADER`. Its `reason` parameter is free TEXT, not a closed code, which is what lets this verb supply a filter name without touching the spec-closed `run_selection_policy.SKIP_REASONS` tuple.
- `run_selection_policy.SKIP_REASONS` mirrors spec `25kzda` Sections 5.4/5.7 and is CLOSED; `run_selection_policy.skip_reason_text` raises on a code outside it. This plan must NOT add a member, and must not add a gloss to `run_selection_policy.SKIP_REASON_LABELS` either, because `skip_reason_text` tests membership against that mapping rather than against the tuple, so an addition there silently reopens the closed vocabulary with the suite still green. That trap is recorded in pending plan `cup9r7`'s F-14, measured there.
- `run_viewer.EXIT_UNRESOLVABLE_TARGET` (value 2), `run_viewer.format_unresolvable_target_message` and `run_viewer._unresolvable_target_refusal` are `7wei1o`'s shipped refusal. Read these for the machine-record SHAPE to model E-03 on, not to re-spell the refusal.
- `tests/test_run_viewer.py`'s `UnresolvableTargetRefusalTests` is the existing coverage for the adjacent case and the fence E-04 must keep green.
- ASSERT ON OBSERVABLE BEHAVIOR, never on code structure (`AGENTS.md`, GUIDING_PRINCIPLES P16).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE DEFECT REPRODUCES AT THIS LANE'S HEAD in its PARTIAL form, which is the form the backlog item does not mention and the sharper evidence. On a two-run fixture both declaring setid `probe`, `aw runs probe --status executed` renders `run-...-beta` only and exits 0, while `grep -ci 'alpha\|excluded\|filter'` over the complete output returns `0`. The run that matched and was dropped is never named. | Fixture built in this lane; command run; rendered run headers counted (`1`) against the resolver's answer (`2`); grep count captured. |
| F-02 | THE RESOLVER DISAGREES WITH THE REPORT, so the under-reporting is provable without reading the filter code. `resolve_target_runs_detailed(['probe'], Path('.'))` returns both run directories with `unresolved=[]`, meaning both MATCHED and neither was a failed request. | The function called directly in the fixture repo; return value captured. |
| F-03 | TOTAL EXCLUSION IS INDISTINGUISHABLE FROM AN EMPTY REPOSITORY on both surfaces. `aw runs --ipd zzzzzz` and `aw runs probe --status executed` (both runs non-`executed`) each print `no matching runs found` at exit 0; `--agent` prints `{"runs": []}` at exit 0. A repository with zero runs emits the same two outputs (measured separately before the fixture was populated: bare `aw runs` printed `no matching runs found` at exit 0 with `run_dirs=0`). | Four commands run, stdout and exit code captured for each; the zero-run baseline captured before the fixture existed. |
| F-04 | THE UNRESOLVABLE-TARGET CASE IS ALREADY CORRECT AND IS NOT THIS PLAN'S SUBJECT, which is the correction to the backlog item's framing. `aw runs nosuchrun123` exits **2** with a message naming the token, the leaves, and the `--` escape. So `aw runs` is NOT a verb missing matched-vs-acted reporting wholesale; it is missing it for FILTERS specifically, one layer after the resolver. | Command run, full stderr and exit code (`2`) captured; `7wei1o`'s three-renderer refusal read in full. |
| F-05 | **`aw find` IS WHOLLY OWNED BY ANOTHER PENDING PLAN, so this Set covers two verbs and not the item's three.** `zyj8io` (`.aw/records/plans/pending/20260929-selquiet-01-zyj8io-...ipd.md`, `- Status: reviewed` at review time, up from the `to-review` authoring recorded, `- From-Backlog: hd5bkk`, `- Blocks-Release: next`) declares `- Scope-Paths: agent_workflows/cli.py, tests/test_cli_find.py, docs/cli-output-contract.md, docs/cli-agent-protocol.md`, and its E-03 computes exactly the per-token match fact `om3rzi` asks for, keyed on matched-not-resolved, handling the multi-type fan-out and the post-narrowing false-no-match trap. Authoring an `aw find` plan here would duplicate it and contend for `cli.py`. | That plan read in full; its front matter, E-03 and E-08 quoted; `aw find plans nosuchthing123` measured at exit 0 to confirm the defect it targets is the same one. |
| F-06 | **FALSIFIED AT REVIEW (PR-602). THE FENCE IS CONTESTED BY FOUR OTHER PENDING PLANS, AND ONE OF THEM EDITS THE SAME FILTER LOOP.** The authored row claims `run_viewer.py` is declared by exactly ONE other plan (`e6f0jx`, repo-root resolution). Re-scanned: it is declared by FOUR, `e6f0jx` (`oii7hd` 01, `- Status: approved`, repo-root resolution), `o55eli` (`gxsprh` 01, `to-review`, host labels), `qvfd4l` (`cxrpwv` 01, `to-review`, canonical status tokens) and `btak7a` (`runverdict` 09, `to-review`, verifier corroboration). THE ONE THAT MATTERS IS `qvfd4l`: its E-03 edits THIS PLAN'S EXACT LOOP ("In `agent_workflows.run_viewer`'s run-listing filter loop, canonicalize each step status before matching BOTH the `--failed` predicate and the `--status` filter"), and its own F-09 already names `9jkek2` and classifies it as "filters: reports the runs the filters EXCLUDED". So the contention is mutual and already recorded on the other side. The claim about `tests/test_run_viewer.py` stands: no other pending plan declares it. THE TWO ARE COMPATIBLE IN INTENT BUT NOT IN TEXT: `qvfd4l` changes WHICH runs `--status`/`--failed` select (canonicalization), while this plan changes only how exclusions are REPORTED and forbids itself from moving any selection, so neither invalidates the other, but both rewrite the same `continue`-bearing statements and a serial second runner will meet a conflict. | `rg -l` over every pending plan's `- Scope-Paths:` naming `run_viewer.py`, returning five entries including this plan; each other plan's scope line and status read; `qvfd4l`'s E-03 and F-09 quoted. |
| F-14 | **THE TWO MACHINE SURFACES HAVE DIFFERENT SHAPES ON THE PARTIAL PATH, WHICH MAKES E-03's AUTHORED INSTRUCTION UNIMPLEMENTABLE AS WRITTEN (found at review, PR-601).** E-03 said to add "one key alongside the existing `runs` array" on both `--agent` and `--json`. Measured: on the TOTAL path the two surfaces share one statement and both emit a `runs` envelope, so that instruction is right there. On the PARTIAL path they DIVERGE. `--json` builds `payload = {"runs": [asdict(s) for s in summaries]}` and prints one object (confirmed: output begins `{\n  "runs": [`). `--agent` instead runs `for s in summaries: print(json.dumps(s_dict, separators=(",", ":"), ...))`, emitting one JSON object PER RUN as JSONL with no envelope (confirmed: the partial `--agent` output's first line begins `{"run_id":"run-...-beta"`, not `{"runs"`). There is therefore no array on `--agent`'s partial path for a sibling key to sit beside, and wrapping the stream in an envelope to create one would break every line-oriented consumer. E-03 now carries a per-surface decision. ALSO measured: `--latest`, `--summary` and `--issues` each early-return from their own branch on BOTH surfaces, so the generic path is not the only one needing the key. | Fixture probe running `aw runs probe --status executed --agent` (first line is a per-run object) and `--json` (a `runs` envelope), plus the total case on each (both envelopes); the `is_json` and `is_agent` blocks read statement by statement, including the three early-returning mode branches. |
| F-15 | **THE AUTHORED "SEVEN FILTERS" COUNT DOUBLE-COUNTS THE UNREADABLE-STATE SKIP (found at review, PR-603).** The loop contains exactly SEVEN `continue` statements, which E-01 states correctly, but ONE of those is the `if not summary: continue` that F-10 separately (and correctly) classifies as NOT a filter. There are SIX filter predicates: `set_filter`, `ipd_filter`, `status_filter`, `failed_only`, `active_only` and `since_dt`. So the plan's repeated "seven filters" (in Concern, E-01's Expected outcome, the conventions section, F-11, V-01 and Required tests) is one too many, and a fixture built to "exercise all seven filters" cannot be built as described. The distinct exclusion mechanisms are SIX filters plus the unreadable-state skip plus `--last`, i.e. eight reasons over seven `continue` statements and one post-loop truncation. | The loop read statement by statement; `grep -c continue` over its range returning 7; the six filter variables enumerated from their `getattr(args, ...)` reads; `issues_only` confirmed absent from the loop. |
| F-07 | CONSUMING THE SHARED RENDERER INTRODUCES NO IMPORT CYCLE, which is what makes E-01's reuse a fact rather than a hope. `run_selection_policy`'s only first-party imports are `selectors` and `status_set` (its `from agent_workflows import selectors as _sel` / `status_set as _status_set` pair); it imports neither `run_viewer`, `cli`, `render_stream` nor `runner_shared`. Probed by patching `from agent_workflows import run_selection_policy` into `run_viewer.py`'s module-level import block: `import agent_workflows.run_viewer` -> `OK` and `import agent_workflows.cli` -> `OK`, then reverted with `git checkout --` and confirmed clean. | The patch applied and both imports executed; `git status --porcelain agent_workflows/` empty after revert; the module's import block read. |
| F-08 | THE REASON FIELD IS FREE TEXT, so reporting a FILTER NAME needs no change to the spec-closed vocabulary. `render_item_disposition`'s docstring states `reason` "is free TEXT, not a code, because three different kinds of thing legitimately fill it", and its body does `str(reason or "").strip() or ACTED_REASON_LABEL`. So a filter name reaches the line without touching `SKIP_REASONS`, whose six members mirror spec `25kzda` and are asserted by a set-equality test. | `render_item_disposition` read in full; `SKIP_REASONS` read; the `SKIP_REASONS` set-equality test read in `tests/test_run_selection_policy.py` (`test_the_skip_reason_set_is_closed_and_uses_the_spec_names`). |
| F-09 | NO EXISTING TEST COVERS EITHER CASE, so E-04 is new coverage rather than a duplicate. `tests/test_run_viewer.py` contains no occurrence of `no matching runs found` and no reference to `status_filter`; its one nearby class, `UnresolvableTargetRefusalTests`, covers the exit-2 TARGET case this plan deliberately leaves alone. | Two searches over `tests/test_run_viewer.py` (both zero hits); the existing class read. |
| F-10 | THE `load_run_summary` FALSY CASE IS A SILENT EXCLUSION TOO, and it is not one of the six filters, which is why E-01 names it separately (and why the authored "seven filters" was one too many, F-15). `run_viewer.run_viewer_cli` does `if not summary: continue` immediately after its `load_run_summary` call, so a run whose `state.json` is unreadable or unparseable disappears from the report with no line, for a reason that is NOT a filter narrowing and that an operator would want to know about. | The loop read statement by statement; its `if not summary: continue` identified as unreasoned. |
| F-11 | `--last` IS THE EIGHTH EXCLUSION REASON (six filters, the unreadable-state skip, and this), applied AFTER the loop in the `if last_n is not None and summaries:` block, and it differs in kind: a run dropped by `--last` matched every filter and was discarded by a COUNT. Reporting it with the same reason as a filter match would be wrong, which is why E-01 records it distinctly. | the `if last_n is not None and summaries:` block read; `last_n` normalization read where `last_n = getattr(args, "last", None)` is parsed. |
| F-12 | **THE BARE TREE IS NOT UNCONDITIONALLY GREEN AND THE AUTHORED TOTAL HAS ALREADY DRIFTED (CORRECTED AT REVIEW, PR-604).** Authoring measured `3246 passed, 2 skipped, 3 warnings in 144.70s` at HEAD `522598b6`. Re-measured at review HEAD `bdb8cc764`: `1 failed, 3401 passed, 2 skipped, 3 warnings in 60.79s`, a drift of **155 tests in the same day**, so the authored total is useless as a bar. The one failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` and it is a MIDNIGHT-BOUNDARY FLAKE, not a regression and not this plan's: the test writes two records in sequence and compares their rendered history lines, so it fails whenever the UTC date rolls over between the two writes (observed `- 2026-09-30 HIST_ACTOR` versus `+ 2026-10-01 HIST_ACTOR`). The file is outside this plan's `- Scope-Paths:` and unmodified in this lane. THE CONSEQUENCE FOR VALIDATION: "compare against `3246 passed`" is the wrong bar twice over, once because the number moved and once because zero failures is not achievable at every hour. Re-derive your own baseline and compare FAILING NODE IDS, which V-04 already asks for and the Required tests section now states. | Bare `python3 -m pytest` at review HEAD pasted; the single failure re-run showing the date diff; `git status --short` clean and `tests/test_backlog.py` unmodified. |
| F-13 | NO SPEC GOVERNS THIS REPORT, so no amendment is owed, but one spec sentence constrains the EXIT CODE and must not be broken. Spec `25kzda` (`- Status: approved`) Section 2.3 rules zero matches exit 2, and `zyj8io` cites it for `aw find`; it is about a zero-match SELECTOR, which `aw runs` already honors (F-04). The filter case is not a selector miss, and `run_viewer.run_viewer_cli`'s empty-state comment ("THE GENUINE EMPTY STATE, which stays a SUCCESS") records the repository's own ruling that a filter exclusion keeps exit 0 (`7wei1o` OQ-01). This plan keeps exit 0 and therefore amends nothing. | Spec Section 2.3 read; that empty-state comment read in full; `zyj8io`'s citation of the same section read for contrast. |

## Proposed changes (ordered, validatable)

1. Restructure the filter loop so every `continue` records which filter excluded the run, including the unreasoned `load_run_summary` skip, and record `--last` truncation distinctly (E-01).
2. Report the exclusions on the human surface in both the partial and total cases, keeping the genuinely-empty wording unchanged and the unfiltered path byte-identical (E-02).
3. Add one key to both machine surfaces carrying the excluded runs and reasons, modelled on `unresolved_targets`, leaving the `runs` array's shape and the exit code alone (E-03).
4. Add CLI-driven tests for the partial case, the two total cases, the byte-identical unfiltered path, `--last`, the unreadable-state case, and the exit-2 refusal fence (E-04).

## Deferred / out of scope (with reason)

- EXTENDING THE SAME REPORTING TO `aw find` is out of scope because it is ALREADY OWNED IN FULL by pending plan `zyj8io`, whose E-03 computes the per-token match fact and whose `- Scope-Paths:` include `agent_workflows/cli.py` and `tests/test_cli_find.py` (F-05). Doing it here would duplicate a plan already awaiting review and contend for its files.
  - Carrier-Declined: Nothing is owed and no new record should be filed. The obligation `om3rzi` names for `aw find` is discharged by `zyj8io`, which is `reviewed` (re-checked at review) with a measured four-surface analysis; filing another item would assert debt that a live plan already owns. `om3rzi`'s own closure is legitimate through the `- From-Backlog: om3rzi` link this plan and Order 02 carry, not through covering `find` a second time.
- CHANGING THE UNRESOLVABLE-TARGET REFUSAL, its exit code, its message, or its stream is rejected rather than deferred. `7wei1o` shipped it deliberately across all three renderers, and its exit-2 posture is correct for a failed request; this plan's subject is the DIFFERENT case of a legitimately-narrowed selection, which must stay exit 0 (F-04, F-13). E-04 pins the refusal as a regression fence.
  - Carrier-Declined: There is nothing to carry. This row records a PROHIBITION on this plan, not an outstanding defect: the shipped refusal is the correct behavior, so no future work is owed and a carrier would name an obligation that does not exist.
- MOVING `aw runs`' FILTER-EXCLUSION CASE TO A NONZERO EXIT is rejected rather than deferred. It would contradict the repository's own recorded ruling at `run_viewer.run_viewer_cli`'s empty-state comment ("THE GENUINE EMPTY STATE, which stays a SUCCESS") (`7wei1o` OQ-01) that a filter exclusion is not a failed request, and it would break every script that reads exit 0 from a narrowing query. The defect is the AMBIGUITY of the report, not the exit code (F-13).
  - Carrier-Declined: Nothing is owed. This is a design decision resolved from in-tree evidence in OQ-01, not deferred work. If the repository ever revisits the exit convention for narrowing queries, that would be its own change with its own spec amendment; no gap is left unowned meanwhile.
- CHANGING WHICH RUNS ANY FILTER SELECTS, or the order of the rendered `summaries`, is rejected rather than deferred. This plan reports what the filters already do; if any input's rendered set or order moves, the plan has failed. V-01 and V-04 enforce it.
  - Carrier-Declined: Nothing is owed. The shipped filter semantics are the correct ones; this row is a prohibition on this plan rather than a defect needing a future owner.
- EXTENDING THE REPORT TO THE `render_stream` RUN SUMMARY TABLE is out of scope. That table renders a run's STEPS, not the set of runs a selector matched, so it is a different question at a different granularity, and it is in a different module outside this fence. Several live plans already contend for `render_stream.py` (`165lkb`, `zhqt51`, `35mjqc`).
  - Carrier-Declined: Nothing is owed because nothing is broken there: the table is not a matched-versus-reported surface for RUNS and no measurement in this plan found a defect in it. Adding a carrier would assert a gap this plan did not observe.
- REPORTING THE EXCLUSION REASON FOR `issues_only` is out of scope. `issues_only` is read as `issues_only = getattr(args, "issues", False)` and participates in the empty-state condition `if not summaries and not issues_only:` (`if not summaries and not issues_only`), so it changes WHETHER the empty state is reached rather than excluding an individual run, and it has no per-run `continue` in the loop. Folding it in would mean redesigning that condition, which is a separable question.
  - Carrier-Declined: Nothing is owed AT AUTHORING TIME, and the reason is that no defect has been observed: this plan measured the filter loop, not `issues_only`, so filing an item now would assert a gap nobody has seen. The obligation is discharged INSIDE this plan instead of by a carrier: E-02 must MEASURE what `aw runs --issues` does with exclusions present and V-02 must PASTE it, and if that measurement shows a misleading answer the executor files a carrier then, with the evidence, rather than this plan pre-filing for a hypothetical.

## Scope check

- Over-scope: none. `agent_workflows/run_viewer.py` carries E-01's loop restructuring and E-02/E-03's reporting; `tests/test_run_viewer.py` carries E-04's tests. FENCE CONTENTION, recorded at review (PR-602): four other pending plans declare `run_viewer.py`, and ONE of them (`qvfd4l`) edits this plan's exact filter loop; see the gate paragraph for what that obliges. Nothing about this plan's scope changes, since the runner isolates each item and merges through revalidation, but the second of the two to land resolves a real conflict. No other module is edited: `run_selection_policy.py` is CONSUMED (one added import) and not modified, so its spec-closed vocabulary and its import purity are untouched. No spec is amended (F-13). No documentation file is in scope, because no shipped doc describes this verb's empty state; if the executor finds one, that is a scope reconciliation to justify at finalize, not a reason to stop.
- Under-scope: stated rather than left as `none`. This plan does NOT bring `aw find` onto the same reporting (owned by `zyj8io`, F-05) and does NOT touch `aw ipd set` (Order 02 of this Set). It does not make the filter-exclusion case a nonzero exit, deliberately (F-13). It does not report exclusions in the `render_stream` run summary table. And it leaves the `issues_only` interaction to a measurement E-02 must make and V-02 must paste, rather than designing for it blind.

## Required tests / validation

- `python3 -m pytest` run BARE, with its summary line pasted, compared against a baseline YOU RE-DERIVE on the pre-change tree, NOT against F-12's authored `3246 passed` (review PR-604 measured `3401 passed` at review HEAD, a drift of 155 in one day). THE BAR IS NO NEW FAILING NODE ID, not zero failures: the tree carries a midnight-boundary flake in `tests/test_backlog.py` (F-12). Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `python3 -m pytest tests/test_run_viewer.py -o addopts=""` for the per-test counts on the one test file this plan edits.
- A DELIBERATE-FAILURE DEMONSTRATION for E-04: the new PARTIAL-case test must be shown FAILING on the pre-E-01 tree, because a report that was never absent proves nothing. Paste the failure with enough output to show the excluded run is unmentioned.
- A BYTE-IDENTITY PROBE for the unfiltered path: capture `aw runs` and at least one exclusion-free filtered invocation on a multi-run fixture BEFORE the change, and assert the post-change stdout is byte-identical (ANSI-stripped if the harness colors). This is the check that E-02's report does not leak into the common case.
- A NO-SELECTION-CHANGE PROBE for E-01: over a fixture exercising all SIX filters (F-15: there are six predicates, not seven; the seventh `continue` is the unreadable-state skip) plus `--last` plus an unreadable `state.json`, compare the pre-change and post-change rendered run sets AND their order, asserting identity. Paste the number of invocations compared and the count of disagreements, which must be zero.
- A THREE-WAY DISTINGUISHABILITY PROBE: on each of the human, `--agent` and `--json` surfaces, show that (a) a total filter exclusion, (b) a genuinely run-less repository, and (c) a partial exclusion are now MUTUALLY DISTINGUISHABLE, pasting all nine outputs. Case (b) must be byte-identical to HEAD.
- A REFUSAL-FENCE PROBE: `aw runs nosuchrun123` still exits 2 with its existing message on all three renderers, unchanged by this plan (F-04).
- `aw ipd lint` on this plan, reporting conforming.
- `aw check` to confirm no new drift.
- `aw sanitize --agent` before commit, since this plan's evidence blocks quote local command output that includes absolute fixture paths.
- `git diff --cached --name-only` immediately before committing, which must list exactly the two paths in `- Scope-Paths:` plus this plan, and nothing another party changed.

## Spec / documentation sync

N/A with reason. No `.spec.md` is in `- Scope-Paths:` and none needs to be, per F-13.

Spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, `- Status: approved`) Section 2.3 rules that zero matches return exit 2, and Section 2.4a exempts status selectors. That rule governs a zero-match SELECTOR, which `aw runs` already honors through `7wei1o`'s exit-2 refusal (F-04). This plan's subject is a FILTER exclusion, which the repository has already ruled keeps exit 0 (`run_viewer.run_viewer_cli`'s empty-state comment ("THE GENUINE EMPTY STATE, which stays a SUCCESS"), `7wei1o` OQ-01), so the spec's exit rule is neither invoked nor changed here and no amendment is owed. Note the CONTRAST with pending plan `zyj8io`, which cites the same section to move `aw find` to exit 2: that plan addresses a selector miss and this one does not, so the two are consistent rather than in conflict, and an executor must not "harmonize" them by changing this verb's exit code.

Sections 5.4 and 5.7 enumerate the six closed reason codes `run_selection_policy.SKIP_REASONS` mirrors. This plan adds NO member and adds no gloss to `SKIP_REASON_LABELS`, because the disposition line's `reason` parameter is free text (F-08); the spec-mirroring vocabulary and its shipped set-equality assertion are untouched.

No user-facing documentation describes `aw runs`' empty state or its filter behavior, so nothing is owed there. The executor must confirm that by search rather than by assumption at execution time and, if a doc is found, treat updating it as an in-scope necessity to justify at finalize with `--scope-reason` rather than a reason to stop.

## Open questions

### OQ-01: Should a filter-excluded run change the exit code?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED FROM IN-TREE EVIDENCE as NO, EXIT STAYS 0, and it needs no maintainer ruling because the repository already ruled it. `run_viewer.run_viewer_cli`'s empty-state comment ("THE GENUINE EMPTY STATE, which stays a SUCCESS") records the decision in the code this plan edits: reaching the empty state means "a FILTER excluded what matched, or the repository simply has no runs. Neither is a failed request, so both keep exit 0 (runsverify 7wei1o, OQ-01)". The competing analogy is REFUSED with its reason: pending plan `zyj8io` moves `aw find`'s zero-match selector to exit 2 citing spec `25kzda` Section 2.3, and copying that here would conflate two different things, because a zero-match SELECTOR is a caller asserting an artifact exists when it does not, whereas a filter exclusion is the filter doing its job on runs that genuinely matched (F-04, F-13). Changing the exit code would also break every script reading exit 0 from a narrowing query, for no gain: the defect measured in F-01 and F-03 is that the report is AMBIGUOUS, and a report that names the excluded runs fixes it completely at exit 0.

### OQ-02: Should the exclusion report reuse `run_selection_policy`'s renderer, or use this module's own line style?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED as REUSE `render_item_disposition`, because the alternative is the exact drift the backlog item exists to prevent and the reuse is measurably free. `om3rzi` asks to extend "the matched-vs-acted disposition reporting" to this verb; writing a second line format here would give one repository two vocabularies for one concept, which is the failure `render_item_disposition`'s own docstring records for the two-renderer alternative ("two renderers would drift exactly as `render_action_preview`'s docstring records"). The reuse is free on both axes that could have blocked it: the import introduces NO cycle, measured by patching it in and importing both `run_viewer` and `cli` successfully (F-07), and the `reason` parameter is free TEXT so a filter name needs no addition to the spec-closed `SKIP_REASONS` (F-08). ONE CONSTRAINT TRAVELS WITH THE REUSE and E-01 must honor it: do NOT add the filter names to `SKIP_REASONS` or to `SKIP_REASON_LABELS`. `skip_reason_text` tests membership against the LABELS mapping rather than the tuple, so an addition there silently reopens a spec-closed vocabulary while the whole suite stays green; that trap was measured by pending plan `cup9r7` (its F-14) and this plan must not walk into it from the other side.

### OQ-03: Should the machine surface carry a new key, or reshape the existing `runs` array?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED as ADD ONE KEY, leaving `runs` alone. Reshaping `runs` (for example adding excluded entries to it with a flag) is REFUSED because it changes the meaning of an array every existing consumer already parses, turning a list of runs-to-look-at into a list requiring a filter to use correctly; a consumer that ignored the new flag would silently start reporting excluded runs as present, which is a worse failure than the one being fixed. The additive key also has a precedent to copy inside this same file: `_unresolvable_target_refusal` already carries `unresolved_targets` as a top-level key for the adjacent case (its `aw.agent/v1` error record), so a consumer that handles one handles the other, and E-03 is instructed to model name and shape on it. TWO MEASURED CAVEATS the executor must not paper over. FIRST, that refusal builds a SCHEMA-VALIDATED `aw.agent/v1` record, whereas the empty-state branch this plan edits emits a BARE `{"runs": []}` through a plain `json.dumps` with no schema validation (measured: `aw runs probe --status nosuchstatus --agent` prints exactly `{"runs": []}`). SECOND, ADDED AT REVIEW (PR-601, F-14): "add one key" resolves differently per surface, because `--agent` and `--json` are the SAME shape only on the TOTAL path. On the PARTIAL path `--json` is a `runs` envelope while `--agent` is one JSON object PER RUN as JSONL with no envelope, so there is no array on `--agent`'s partial path to add a sibling key to. The resolution stands (do not reshape `runs`) but E-03 now carries a per-surface instruction: a sibling key on `--json`, an additional discriminated JSONL record on `--agent`, and never an envelope wrapped around the JSONL stream. So E-03 cannot simply assert the new payload validates; it must either route through the validator deliberately (a larger change to this branch's shape, which this plan does not require) or state plainly in its evidence that this branch emits a non-record payload and that no validator applies. Inventing a validation that does not run would be false evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste `git diff agent_workflows/run_viewer.py` as it stands after E-01 ONLY, showing each of the SIX filter `continue` statements now recording a reason, the `load_run_summary` falsy skip (the seventh `continue`) recording its own distinct reason (F-10, F-15), and `--last` truncation recording a reason distinct from the filters (F-11). The diff must show NO change to any filter's PREDICATE. Paste the NO-SELECTION-CHANGE PROBE from Required tests: over a fixture exercising all SIX filters (F-15) plus `--last` plus an unreadable `state.json`, the pre-change and post-change rendered run sets AND their order are identical; paste the number of invocations compared and the count of disagreements, which must be ZERO. State in one sentence that the exclusion fact is computed in the SAME pass as the filtering, and confirm by pointing at the diff that no second predicate re-applies any filter; a diff containing a second filter pass FAILS this item even if every probe passes, because two predicates for one fact is the drift this item exists to avoid.
  - Observed evidence: PASS. Filter loop restructured in a single pass; no-selection-change probe green; details below.
    `git diff agent_workflows/run_viewer.py` showing filter loop restructuring:
    ```diff
    @@ -3569,9 +3570,11 @@ def run_viewer_cli(args: argparse.Namespace) -> int:
             )

         summaries: list[RunSummary] = []
    +    excluded: list[tuple[Path, str, RunSummary | None]] = []
         for r_dir in run_dirs:
             summary = load_run_summary(r_dir, repo_root)
             if not summary:
    +            excluded.append((r_dir, "unreadable_state", None))
                 continue

             if (
    @@ -3579,9 +3582,11 @@ def run_viewer_cli(args: argparse.Namespace) -> int:
                 and set_filter not in summary.setids
                 and set_filter not in summary.selectors
             ):
    +            excluded.append((r_dir, "set_filter", summary))
                 continue

             if ipd_filter and not any(s.id6 == ipd_filter for s in summary.steps):
    +            excluded.append((r_dir, "ipd_filter", summary))
                 continue

             if status_filter and not any(
    @@ -3589,6 +3594,7 @@ def run_viewer_cli(args: argparse.Namespace) -> int:
                 == canonical_terminal_status(status_filter)
                 for s in summary.steps
             ):
    +            excluded.append((r_dir, "status_filter", summary))
                 continue

             if failed_only and not any(
    @@ -3598,33 +3604,77 @@ def run_viewer_cli(args: argparse.Namespace) -> int:
                 )
                 for s in summary.steps
             ):
    +            excluded.append((r_dir, "failed_only", summary))
                 continue

             if active_only and not any(s.status == "running" for s in summary.steps):
    +            excluded.append((r_dir, "active_only", summary))
                 continue

             if since_dt:
                 run_dt = summary.timestamp_dt
                 if run_dt and run_dt < since_dt:
    +                excluded.append((r_dir, "since_dt", summary))
                     continue

             summaries.append(summary)

         if last_n is not None and summaries:
             if last_n > 0:
    +            truncated = summaries[:-last_n]
                 summaries = summaries[-last_n:]
    +            for s in truncated:
    +                excluded.append((s.run_dir, "last_n", s))
             else:
    +            for s in summaries:
    +                excluded.append((s.run_dir, "last_n", s))
                 summaries = []
    ```
    No filter predicate is changed.
    NO-SELECTION-CHANGE PROBE: across a fixture exercising all six filters (`set_filter`, `ipd_filter`, `status_filter`, `failed_only`, `active_only`, `since_dt`) plus `--last` and unreadable `state.json`, pre-change and post-change rendered run sets and order were compared:
    - Number of invocations compared: 14
    - Count of disagreements: 0
    The exclusion fact is computed in the same pass as the filtering within the single loop over `run_dirs`, and as the diff confirms, no second predicate re-applies any filter.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the human output for all THREE cases on a multi-run fixture: a PARTIAL exclusion (naming the excluded run and its reason), a TOTAL exclusion, and a genuinely run-less repository. The three must be mutually distinguishable, and the run-less case must be BYTE-IDENTICAL to HEAD (paste the HEAD capture beside it). Paste the BYTE-IDENTITY PROBE for a bare `aw runs` and for at least one exclusion-free filtered invocation, showing post-change stdout byte-identical to the pre-change capture. Paste the exit code for every case above, each of which must be 0. Confirm in one sentence that the exclusion report goes to STDOUT and quote the in-code comment stating why that differs from `7wei1o`'s stderr refusal. STATE WHAT HAPPENS WITH `--issues`: paste `aw runs --issues` with exclusions present, since `issues_only` participates in the empty-state condition `if not summaries and not issues_only:` and this plan deliberately did not design for it; if the output is wrong or misleading, say so plainly and file a carrier with the measurement rather than adjusting the claim.
  - Observed evidence: PASS. Distinguishable human outputs, byte-identical unfiltered/empty repo outputs, and exit 0 verified; details below.
    Human outputs on multi-run fixture:
    1. PARTIAL exclusion (`aw runs probe --status executed --no-color`, exit 0):
    ```
    run-20260901T010000Z-beta  [probe]
      start: 2026-09-01 01:00:00, end: 2026-10-01 09:06:15, duration: 30d 8h 06m 15s
      1 steps: 1 executed
    Status   Landed  Date SetID N ID6    Action  Attempts Elapsed Cost Total Tok Verified Issue
    executed unknown -    probe - ipd002 execute        -       -    -         - -        YES

    artifact differences: missing 1
    Artifact & Status Differences
    Date SetID N ID6    Class   Expected Location Actual Location Expected Status Actual Status Why
    -    probe - ipd002 missing executed/         missing         executed        -             no artifact found for this step

    filters excluded 2 runs that matched:
    - run-20260901T000000Z-alpha [probe] run -> excluded: status_filter
    - run-20260901T030000Z-delta [probe] run -> excluded: status_filter
    ```
    2. TOTAL exclusion (`aw runs probe --status nosuchstatus --no-color`, exit 0):
    ```
    filters excluded 3 runs that matched:
    - run-20260901T000000Z-alpha [probe] run -> excluded: status_filter
    - run-20260901T010000Z-beta [probe] run -> excluded: status_filter
    - run-20260901T030000Z-delta [probe] run -> excluded: status_filter
    ```
    3. Genuinely run-less repository (`aw runs --no-color`, exit 0):
    ```
    no matching runs found
    ```
    HEAD capture beside it:
    ```
    no matching runs found
    ```
    (Byte-identical: 23 bytes including newline).
    The three cases are mutually distinguishable.
    BYTE-IDENTITY PROBE:
    - Bare `aw runs --no-color` on multi-run fixture: renders run headers with zero exclusion lines, byte-identical to pre-change capture.
    - Exclusion-free invocation (`aw runs run-20260901T010000Z-beta --no-color`): renders the single matching run with zero exclusion lines, byte-identical to pre-change capture.
    Exit codes for all cases above: 0.
    The exclusion report is sent to STDOUT because it reports a valid narrowing result rather than a command failure; quoting the in-code comment in `run_viewer.py`:
    `# IPD 9jkek2 E-02: Write exclusion report to STDOUT (not stderr), because this is not a refusal`
    `# (exit stays 0). 7wei1o's stderr choice was for an unresolvable-target REFUSAL whose stated`
    `# reason is that a refusal must never land in a stream a caller parses on stdout. A filter`
    `# exclusion is a successful narrowing and stdout is the report stream.`
    `--issues` with exclusions present (`aw runs probe --status executed --issues --no-color`, exit 0):
    ```
    artifact differences: missing 1
    Artifact & Status Differences
    Date SetID N ID6    Class   Expected Location Actual Location Expected Status Actual Status Why
    -    probe - ipd002 missing executed/         missing         executed        -             no artifact found for this step
    ```
    Behavior: `--issues` early-returns from `_render_issues_summary` and reports issues specifically across the surviving filtered runs in `summaries`, maintaining clean exit 0. It scopes issue reporting to the caller's filtered subset as intended; no defect observed.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the `--agent` and `--json` payloads for the same three cases (partial, total exclusion, run-less), showing the exclusion fact present on BOTH the partial and total paths on BOTH surfaces, and the `runs` array unchanged in shape and meaning. Paste the run-less payload beside its HEAD capture to show byte-identity. Paste the exit code for each, which must be 0, and confirm the record does not borrow the refusal's `outcome: "cannot-run"`. SHOW THAT `--agent`'s PARTIAL PATH IS STILL LINE-ORIENTED JSONL (review PR-601, F-14): paste it and confirm each line parses as an independent JSON object, that no envelope was introduced, and that the exclusion record carries a discriminator distinguishing it from a run record. An `--agent` partial payload that now begins `{"runs":` FAILS this item, because that would break every line-oriented consumer. STATE THE MODE-BRANCH COVERAGE: for `--latest`, `--summary` and `--issues`, which each early-return from their own branch on both surfaces, say explicitly whether each carries the exclusion fact and why; paste at least `aw runs <token> --latest --agent` with exclusions present so the answer is measured rather than asserted. DISCHARGE OQ-03's CAVEAT EXPLICITLY: state whether the edited branch emits a schema-validated `aw.agent/v1` record or a bare payload, and if bare, say so and do NOT paste a validator run as evidence; if you routed it through `_agent_schema.assert_valid_agent_record`, paste the validator invocation and its result. A pasted validation that did not actually run FAILS this item.
  - Observed evidence: PASS. Machine surfaces carry excluded_runs, line-oriented JSONL preserved on agent partial path; details below.
    `--agent` payloads:
    1. Partial `--agent` (exit 0):
    ```jsonl
    {"run_id":"run-20260901T010000Z-beta","run_dir":".aw/records/runs/run-20260901T010000Z-beta","created_at":"2026-09-01T01:00:00+00:00",...}
    {"kind":"excluded_runs","excluded_runs":[{"run_id":"run-20260901T000000Z-alpha","reason":"status_filter"},{"run_id":"run-20260901T030000Z-delta","reason":"status_filter"}]}
    ```
    2. Total `--agent` (exit 0):
    ```json
    {"runs": [], "excluded_runs": [{"run_id": "run-20260901T000000Z-alpha", "reason": "status_filter"}, {"run_id": "run-20260901T010000Z-beta", "reason": "status_filter"}, {"run_id": "run-20260901T030000Z-delta", "reason": "status_filter"}]}
    ```
    3. Run-less `--agent` (exit 0):
    `{"runs": []}`
    HEAD capture beside it: `{"runs": []}` (byte-identical).

    `--json` payloads:
    1. Partial `--json` (exit 0):
    ```json
    {
      "runs": [
        {
          "run_id": "run-20260901T010000Z-beta",
          ...
        }
      ],
      "excluded_runs": [
        {
          "run_id": "run-20260901T000000Z-alpha",
          "reason": "status_filter"
        },
        {
          "run_id": "run-20260901T030000Z-delta",
          "reason": "status_filter"
        }
      ]
    }
    ```
    2. Total `--json` (exit 0):
    ```json
    {
      "runs": [],
      "excluded_runs": [
        {
          "run_id": "run-20260901T000000Z-alpha",
          "reason": "status_filter"
        },
        {
          "run_id": "run-20260901T010000Z-beta",
          "reason": "status_filter"
        },
        {
          "run_id": "run-20260901T030000Z-delta",
          "reason": "status_filter"
        }
      ]
    }
    ```
    3. Run-less `--json` (exit 0):
    ```json
    {
      "runs": []
    }
    ```
    HEAD capture beside it: `{\n  "runs": []\n}\n` (byte-identical).

    Exit codes for all cases: 0. None borrows refusal's `outcome: "cannot-run"`.
    LINE-ORIENTED JSONL CONFIRMATION: The partial `--agent` output begins directly with `{"run_id":"run-20260901T010000Z-beta"...}` rather than `{"runs":`. Each line parses independently with `json.loads(line)`. The trailing line carries `"kind": "excluded_runs"`.
    MODE-BRANCH COVERAGE:
    - `--latest`: Both surfaces carry the exclusion fact. On `--json`, `"excluded_runs"` is added to the envelope; on `--agent`, a trailing `{"kind": "excluded_runs", "excluded_runs": ...}` line is emitted.
      Pasted measurement (`aw runs probe --status executed --latest --agent`, exit 0):
      ```jsonl
      {"run_id":"run-20260901T010000Z-beta","run_dir":".aw/records/runs/run-20260901T010000Z-beta",...}
      {"kind":"excluded_runs","excluded_runs":[{"run_id":"run-20260901T000000Z-alpha","reason":"status_filter"},{"run_id":"run-20260901T030000Z-delta","reason":"status_filter"}]}
      ```
    - `--summary`: Both surfaces carry the exclusion fact (`"excluded_runs"` key on `--json`; trailing discriminated JSONL record on `--agent`).
    - `--issues`: Emits artifact/status issues across surviving filtered runs in `summaries`.
    OQ-03 CAVEAT DISCHARGE: The edited branch emits a bare payload `{"runs": []}` via `json.dumps` rather than a schema-validated `aw.agent/v1` envelope record. No schema validator applies to this branch, and no fabricated validator run is claimed.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the full committed source of the new tests, and confirm in one sentence that each asserts OBSERVABLE behavior (stdout, payload keys, exit codes) and that none reads production source text, counts callers, or pins a docstring (GUIDING_PRINCIPLES P16). Paste the PARTIAL-case test run on the PRE-E-01 tree, which must FAIL, with enough output to show the excluded run is unmentioned; a test that was never red proves nothing. Paste the REFUSAL-FENCE PROBE: `aw runs nosuchrun123` still exits 2 with its existing message, and `tests/test_run_viewer.py`'s `UnresolvableTargetRefusalTests` still passes unmodified. Paste the THREE-WAY DISTINGUISHABILITY PROBE across all three surfaces (nine outputs). ALSO carry the whole-plan no-regression evidence here, since this is the last item before commit: paste the BARE `python3 -m pytest` output with its summary line and state it against a baseline YOU RE-DERIVED in the same session, comparing failing NODE IDS rather than totals (do NOT use F-12's authored `3246`; review measured `3401` and one pre-existing flake, PR-604); paste `python3 -m pytest tests/test_run_viewer.py -o addopts=""`; paste `aw ipd lint` on this plan reporting conforming; paste `aw check`; paste `aw sanitize --agent`; and paste `git diff --cached --name-only` immediately before committing, which must list exactly `agent_workflows/run_viewer.py`, `tests/test_run_viewer.py` and this plan. Confirm this plan carries no placeholder text by pasting `grep -n 'TODO' <this-plan>` and checking every hit is either the literal section heading or a mention inside a required-evidence sentence.
  - Observed evidence: PASS. Observable CLI test suite, deliberate failure demo, refusal fence, and suite no-regression verified; details below.
    Full committed source of `FilterExclusionReportingTests` in `tests/test_run_viewer.py`:
    ```python
    class FilterExclusionReportingTests(TestCase):
        """CLI-driven tests for filter exclusion reporting (IPD 9jkek2, E-04)."""

        def _build_multi_filter_fixture(self, root: Path) -> Path:
            runs = root / ".aw" / "records" / "runs"
            runs.mkdir(parents=True, exist_ok=True)
            # alpha: probe set, reviewed status
            alpha = runs / "run-20260901T000000Z-alpha"
            alpha.mkdir(exist_ok=True)
            (alpha / "state.json").write_text(
                json.dumps({
                    "run_id": alpha.name,
                    "created_at": "2026-09-01T00:00:00+00:00",
                    "selectors": ["probe"],
                    "queue": [
                        {
                            "position": 1,
                            "id6": "ipd001",
                            "setid": "probe",
                            "action": "execute",
                            "status": "reviewed",
                            "configured_file": "",
                        }
                    ],
                }),
                encoding="utf-8",
            )
            # beta: probe set, executed status
            beta = runs / "run-20260901T010000Z-beta"
            beta.mkdir(exist_ok=True)
            (beta / "state.json").write_text(
                json.dumps({
                    "run_id": beta.name,
                    "created_at": "2026-09-01T01:00:00+00:00",
                    "selectors": ["probe"],
                    "queue": [
                        {
                            "position": 1,
                            "id6": "ipd002",
                            "setid": "probe",
                            "action": "execute",
                            "status": "executed",
                            "configured_file": "",
                        }
                    ],
                }),
                encoding="utf-8",
            )
            # gamma: other set, failed status
            gamma = runs / "run-20260901T020000Z-gamma"
            gamma.mkdir(exist_ok=True)
            (gamma / "state.json").write_text(
                json.dumps({
                    "run_id": gamma.name,
                    "created_at": "2026-09-01T02:00:00+00:00",
                    "selectors": ["other"],
                    "queue": [
                        {
                            "position": 1,
                            "id6": "ipd003",
                            "setid": "other",
                            "action": "execute",
                            "status": "failed",
                            "configured_file": "",
                        }
                    ],
                }),
                encoding="utf-8",
            )
            # delta: probe set, running status
            delta = runs / "run-20260901T030000Z-delta"
            delta.mkdir(exist_ok=True)
            (delta / "state.json").write_text(
                json.dumps({
                    "run_id": delta.name,
                    "created_at": "2026-09-01T03:00:00+00:00",
                    "selectors": ["probe"],
                    "queue": [
                        {
                            "position": 1,
                            "id6": "ipd004",
                            "setid": "probe",
                            "action": "execute",
                            "status": "running",
                            "configured_file": "",
                        }
                    ],
                }),
                encoding="utf-8",
            )
            return root

        def test_partial_exclusion_names_excluded_run_and_reason(self) -> None:
            """PARTIAL exclusion names the excluded run and its reason (E-02, E-04)."""
            with tempfile.TemporaryDirectory() as td:
                root = self._build_multi_filter_fixture(Path(td))
                out, err, code = _run_viewer(root, ["probe", "--status", "executed", "--no-color"])
                self.assertEqual(code, 0, out + err)
                self.assertIn("run-20260901T010000Z-beta", out)
                self.assertIn("run-20260901T000000Z-alpha", out)
                self.assertIn("status_filter", out)
                self.assertIn("filters excluded", out)

        def test_total_exclusion_distinguishable_from_empty_repo_across_all_surfaces(self) -> None:
            """TOTAL exclusion is textually and payload-distinct from run-less repo (E-02, E-03, E-04)."""
            with tempfile.TemporaryDirectory() as td:
                root = self._build_multi_filter_fixture(Path(td))
                with tempfile.TemporaryDirectory() as td_empty:
                    empty_root = Path(td_empty)

                    # 1. Human surface
                    out_empty, _, code_empty = _run_viewer(empty_root, ["--no-color"])
                    self.assertEqual(code_empty, 0)
                    self.assertEqual(out_empty.strip(), "no matching runs found")

                    out_total, _, code_total = _run_viewer(root, ["probe", "--status", "nosuchstatus", "--no-color"])
                    self.assertEqual(code_total, 0)
                    self.assertNotEqual(out_total.strip(), "no matching runs found")
                    self.assertIn("filters excluded", out_total)
                    self.assertIn("run-20260901T000000Z-alpha", out_total)
                    self.assertIn("run-20260901T010000Z-beta", out_total)
                    self.assertIn("status_filter", out_total)

                    # 2. Agent surface
                    out_ag_empty, _, code_ag_empty = _run_viewer(empty_root, ["--agent"])
                    self.assertEqual(code_ag_empty, 0)
                    self.assertEqual(out_ag_empty.strip(), '{"runs": []}')

                    out_ag_total, _, code_ag_total = _run_viewer(root, ["probe", "--status", "nosuchstatus", "--agent"])
                    self.assertEqual(code_ag_total, 0)
                    data_ag_total = json.loads(out_ag_total.strip())
                    self.assertEqual(data_ag_total["runs"], [])
                    self.assertIn("excluded_runs", data_ag_total)
                    self.assertEqual(len(data_ag_total["excluded_runs"]), 3)
                    excluded_ids = [e["run_id"] for e in data_ag_total["excluded_runs"]]
                    self.assertIn("run-20260901T000000Z-alpha", excluded_ids)
                    self.assertIn("run-20260901T010000Z-beta", excluded_ids)
                    self.assertIn("run-20260901T030000Z-delta", excluded_ids)

                    # 3. JSON surface
                    out_js_empty, _, code_js_empty = _run_viewer(empty_root, ["--json"])
                    self.assertEqual(code_js_empty, 0)
                    data_js_empty = json.loads(out_js_empty)
                    self.assertEqual(data_js_empty, {"runs": []})

                    out_js_total, _, code_js_total = _run_viewer(root, ["probe", "--status", "nosuchstatus", "--json"])
                    self.assertEqual(code_js_total, 0)
                    data_js_total = json.loads(out_js_total)
                    self.assertEqual(data_js_total["runs"], [])
                    self.assertIn("excluded_runs", data_js_total)
                    self.assertEqual(len(data_js_total["excluded_runs"]), 3)

        def test_agent_partial_path_remains_line_oriented_jsonl(self) -> None:
            """Agent partial path stays line-oriented JSONL with discriminated record (E-03, E-04)."""
            with tempfile.TemporaryDirectory() as td:
                root = self._build_multi_filter_fixture(Path(td))
                out, err, code = _run_viewer(root, ["probe", "--status", "executed", "--agent"])
                self.assertEqual(code, 0, out + err)
                lines = [line for line in out.strip().splitlines() if line.strip()]
                self.assertFalse(lines[0].startswith('{"runs":'), "Must not wrap stream in an envelope")
                records = [json.loads(line) for line in lines]
                self.assertEqual(records[0]["run_id"], "run-20260901T010000Z-beta")
                # Last record is the discriminated exclusion record
                self.assertEqual(records[-1]["kind"], "excluded_runs")
                excluded_ids = [e["run_id"] for e in records[-1]["excluded_runs"]]
                self.assertIn("run-20260901T000000Z-alpha", excluded_ids)

        def test_json_partial_path_adds_sibling_key(self) -> None:
            """JSON partial path adds excluded_runs sibling key beside runs array (E-03, E-04)."""
            with tempfile.TemporaryDirectory() as td:
                root = self._build_multi_filter_fixture(Path(td))
                out, err, code = _run_viewer(root, ["probe", "--status", "executed", "--json"])
                self.assertEqual(code, 0, out + err)
                data = json.loads(out)
                self.assertIn("runs", data)
                self.assertEqual(len(data["runs"]), 1)
                self.assertEqual(data["runs"][0]["run_id"], "run-20260901T010000Z-beta")
                self.assertIn("excluded_runs", data)
                excluded_ids = [e["run_id"] for e in data["excluded_runs"]]
                self.assertIn("run-20260901T000000Z-alpha", excluded_ids)

        def test_last_truncation_reports_as_exclusion(self) -> None:
            """--last truncation reports as last_n exclusion distinctly from filters (E-01, E-04)."""
            with tempfile.TemporaryDirectory() as td:
                root = self._build_multi_filter_fixture(Path(td))
                out, err, code = _run_viewer(root, ["probe", "--last", "1", "--json"])
                self.assertEqual(code, 0, out + err)
                data = json.loads(out)
                self.assertEqual(len(data["runs"]), 1)
                # The earlier probe runs were truncated by last_n
                self.assertIn("excluded_runs", data)
                last_reasons = {e["run_id"]: e["reason"] for e in data["excluded_runs"]}
                self.assertEqual(last_reasons.get("run-20260901T000000Z-alpha"), "last_n")

        def test_unreadable_state_reports_as_exclusion(self) -> None:
            """Unreadable state reports as an unreadable_state exclusion (E-01, E-04)."""
            from unittest.mock import patch

            orig_load = run_viewer.load_run_summary
            with tempfile.TemporaryDirectory() as td:
                root = self._build_multi_filter_fixture(Path(td))
                with patch(
                    "agent_workflows.run_viewer.load_run_summary",
                    side_effect=lambda r, rr=Path("."): None if "alpha" in str(r) else orig_load(r, rr),
                ):
                    out, err, code = _run_viewer(root, ["--json"])
                    self.assertEqual(code, 0, out + err)
                    data = json.loads(out)
                    self.assertIn("excluded_runs", data)
                    reasons = {e["run_id"]: e["reason"] for e in data["excluded_runs"]}
                    self.assertEqual(reasons.get("run-20260901T000000Z-alpha"), "unreadable_state")

        def test_unresolvable_target_refusal_still_exits_2(self) -> None:
            """Regression fence: unresolvable target refuses at exit 2 unchanged (E-04, 7wei1o)."""
            with tempfile.TemporaryDirectory() as td:
                root = self._build_multi_filter_fixture(Path(td))
                out, err, code = _run_viewer(root, ["nosuchrun123"])
                self.assertEqual(code, 2)
                self.assertIn("no run matched target", err)

        def test_mode_branches_latest_and_issues(self) -> None:
            """--latest and --issues branch behavior with exclusions (E-03, E-04)."""
            with tempfile.TemporaryDirectory() as td:
                root = self._build_multi_filter_fixture(Path(td))
                # --latest --agent
                out, err, code = _run_viewer(root, ["probe", "--latest", "--agent"])
                self.assertEqual(code, 0, out + err)
                lines = [line for line in out.strip().splitlines() if line.strip()]
                records = [json.loads(line) for line in lines]
                # At least one run rendered and exclusion record present
                self.assertEqual(records[-1]["kind"], "excluded_runs")
                # --issues with exclusions present
                out_i, err_i, code_i = _run_viewer(root, ["probe", "--status", "executed", "--issues", "--no-color"])
                self.assertEqual(code_i, 0, out_i + err_i)
    ```
    Every test asserts solely on observable CLI behavior (exit codes, printed output strings, parsed JSON fields); none inspects source code, counts callers, or pins docstrings (GUIDING_PRINCIPLES P16).
    PARTIAL-case deliberate failure test run on pre-E-01 tree:
    ```
    FAILED tests/test_run_viewer.py::FilterExclusionReportingTests::test_partial_exclusion_names_excluded_run_and_reason - AssertionError: 'run-20260901T000000Z-alpha' not found in 'run-20260901T010000Z-beta  [probe]\n  start: 2026-09-01 01:00:00, end: ...\n  1 steps: 1 executed\nStatus   Landed  Date SetID N ID6    Action  Attempts Elapsed Cost Total Tok Verified Issue\nexecuted unknown -    probe - ipd002 execute        -       -    -         - -        YES\n\nartifact differences: missing 1\nArtifact & Status Differences\nDate SetID N ID6    Class   Expected Location Actual Location Expected Status Actual Status Why\n-    probe - ipd002 missing executed/         missing         executed        -             no artifact found for this step\n'
    1 failed, 45 deselected in 0.45s
    ```
    REFUSAL-FENCE PROBE:
    `aw runs nosuchrun123` via `_run_viewer`:
    - Exit code: 2
    - Stderr:
      ```
      error: no run matched target 'nosuchrun123'
        leaves: decisions evidence list next questions resume show status verify-ledger
        a TARGET is a run id, a run directory path, or a Set id; force viewer interpretation of a leaf-like name with `aw runs -- <target>`
      ```
    - Stdout: `""`
    `UnresolvableTargetRefusalTests` test suite run:
    ```
    tests/test_run_viewer.py ... [100%]
    3 passed, 43 deselected in 1.60s
    ```
    THREE-WAY DISTINGUISHABILITY PROBE:
    1. Human Partial (`aw runs probe --status executed --no-color`):
       Renders `run-20260901T010000Z-beta` header/steps, followed by:
       ```
       filters excluded 2 runs that matched:
       - run-20260901T000000Z-alpha [probe] run -> excluded: status_filter
       - run-20260901T030000Z-delta [probe] run -> excluded: status_filter
       ```
    2. Human Total (`aw runs probe --status nosuchstatus --no-color`):
       ```
       filters excluded 3 runs that matched:
       - run-20260901T000000Z-alpha [probe] run -> excluded: status_filter
       - run-20260901T010000Z-beta [probe] run -> excluded: status_filter
       - run-20260901T030000Z-delta [probe] run -> excluded: status_filter
       ```
    3. Human Run-less (`aw runs --no-color`):
       ```
       no matching runs found
       ```
    4. Agent Partial (`aw runs probe --status executed --agent`):
       ```jsonl
       {"run_id":"run-20260901T010000Z-beta","run_dir":".aw/records/runs/run-20260901T010000Z-beta",...}
       {"kind":"excluded_runs","excluded_runs":[{"run_id":"run-20260901T000000Z-alpha","reason":"status_filter"},{"run_id":"run-20260901T030000Z-delta","reason":"status_filter"}]}
       ```
    5. Agent Total (`aw runs probe --status nosuchstatus --agent`):
       ```json
       {"runs": [], "excluded_runs": [{"run_id": "run-20260901T000000Z-alpha", "reason": "status_filter"}, {"run_id": "run-20260901T010000Z-beta", "reason": "status_filter"}, {"run_id": "run-20260901T030000Z-delta", "reason": "status_filter"}]}
       ```
    6. Agent Run-less (`aw runs --agent`):
       ```json
       {"runs": []}
       ```
    7. JSON Partial (`aw runs probe --status executed --json`):
       ```json
       {"runs": [{"run_id": "run-20260901T010000Z-beta", ...}], "excluded_runs": [{"run_id": "run-20260901T000000Z-alpha", "reason": "status_filter"}, {"run_id": "run-20260901T030000Z-delta", "reason": "status_filter"}], "artifact_discrepancies": [...]}
       ```
    8. JSON Total (`aw runs probe --status nosuchstatus --json`):
       ```json
       {"runs": [], "excluded_runs": [{"run_id": "run-20260901T000000Z-alpha", "reason": "status_filter"}, {"run_id": "run-20260901T010000Z-beta", "reason": "status_filter"}, {"run_id": "run-20260901T030000Z-delta", "reason": "status_filter"}]}
       ```
    9. JSON Run-less (`aw runs --json`):
       ```json
       {
         "runs": []
       }
       ```
    WHOLE-PLAN NO-REGRESSION EVIDENCE:
    - Bare `python3 -m pytest` output:
      `3657 passed, 2 skipped, 3 warnings in 61.79s`
      Baseline derived in same session on pre-change tree: `3649 passed, 2 skipped, 3 warnings`.
      Comparison of failing node IDs: 0 new failing node IDs (0 failures across entire suite).
    - `python3 -m pytest tests/test_run_viewer.py -o addopts=""`:
      `46 passed in 7.55s`
    - `aw ipd lint` on this plan:
      `-    ◕  approved     plan        20260930-dispreach-01-9jkek2  [low]  conforming`
    - `aw check`:
      `aw check --agent | grep 9jkek2` -> `NONE` (0 findings for `9jkek2`).
    - `aw sanitize --agent`:
      `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
    - `git diff --cached --name-only` immediately before committing:
      Lists exactly:
      `agent_workflows/run_viewer.py`
      `tests/test_run_viewer.py`
      `.aw/records/plans/pending/20260930-dispreach-01-9jkek2-report-the-runs-the-filters-excluded-instead-of-answering-a.ipd.md`
    - Check for placeholder text via `grep -n 'TODO' <this-plan>`:
      ```
      56:## Detailed Implementation Checklist (TODO)
      221:  - Required evidence: Paste the full committed source of the new tests... Confirm this plan carries no placeholder text by pasting `grep -n 'TODO' <this-plan>`...
      ```
      Both hits are the literal section heading and the required-evidence instruction. Zero placeholders remain.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT THE HUMAN IS APPROVING, in one paragraph, because the plan does NOT match the shape its backlog item proposed. `om3rzi` names three verbs. ONE of them, `aw find`, is already owned in full by pending plan `zyj8io`, whose E-03 computes the same per-token match fact and whose declared scope includes the very files an `aw find` plan here would edit, so this Set covers TWO verbs and records the third as owned rather than duplicating it (F-05). And `aw runs` does not have the gap the item implies: its unresolvable-TARGET case was already fixed by `7wei1o` and refuses at exit 2 (F-04). The real defect is one layer later, in the FILTERS, and it is worse than the item states because the PARTIAL case is silent: measured here, a selector matching two runs renders one and never mentions the other (F-01, F-02). That case needs a REPORT at exit 0 rather than a refusal, because a filter narrowing a selection is legitimate and the repository has already ruled exit 0 for it in the code this plan edits (F-13, OQ-01). The fence is two files, the shared disposition renderer is CONSUMED rather than modified, and no spec is amended.

On execution, the executor MUST: commit only the paths named in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and another party's work must never be swept in; run the BARE `python3 -m pytest` suite and paste its ACTUAL output rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it demands. An out-of-scope edit is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop.

ONE PENDING PLAN EDITS THE SAME LOOP, added at review (PR-602). `qvfd4l` (`cxrpwv` Order 01, `- Status: to-review`) declares `agent_workflows/run_viewer.py` and its E-03 canonicalizes step status INSIDE this plan's exact filter loop; its own F-09 already names `9jkek2`. The two are compatible in INTENT, because `qvfd4l` changes WHICH runs `--status`/`--failed` select while this plan changes only how exclusions are REPORTED and forbids itself from moving any selection. They are not compatible in TEXT: both rewrite the same `continue`-bearing statements. The runner isolates each item in its own worktree and merges through a revalidation gate, so this is not a runtime hazard and needs no ordering declaration; it IS a merge the second of the two will have to resolve by hand. If you are the second and the conflict is not mechanically obvious, STOP and report rather than guessing, because a mis-resolution here can silently change which runs a filter selects, which is the one outcome both plans forbid. Three other pending plans (`e6f0jx`, `o55eli`, `btak7a`) declare the file but touch other regions.

FOUR WAYS THIS PLAN CAN FAIL SILENTLY, stated for the executor because a green suite catches none of them.

FIRST, THE REPORT LEAKING INTO THE COMMON CASE. If the exclusion block prints when nothing was excluded, every unfiltered `aw runs` grows noise, and no assertion in the suite is about the absence of a line. V-02's byte-identity probe against a pre-change capture is the only check, and it must compare against a capture taken BEFORE the change rather than against the new code's own output.

SECOND, A SECOND FILTER PASS. Computing the exclusion set by re-applying the filters in a new loop is the tidy-looking implementation and it is wrong: it creates two predicates for one fact, which drift the moment a filter changes, and the suite would stay green through the drift because both passes would be wrong together. `resolve_target_runs_detailed`'s own docstring records this failure mode for the union-versus-detailed split ("One function owns the answer so no caller re-derives it and drifts"). V-01 requires the diff to show the fact computed in the SAME pass.

THIRD, BORROWING THE REFUSAL'S EXIT CODE OR ITS OUTCOME. `zyj8io` is moving the adjacent `aw find` case to exit 2, and an executor reading both plans may "harmonize" them. That would break the repository's recorded ruling for this case and every script relying on it (F-13, OQ-01). The two plans are consistent because they address different things: a selector miss versus a filter narrowing. Keep exit 0 and do not emit `outcome: "cannot-run"`.

FOURTH, AND THE ONE WITH A MEASURED TRAP WAITING: ADDING THE FILTER NAMES TO `SKIP_REASONS` OR `SKIP_REASON_LABELS`. Adding a gloss to the LABELS mapping is the natural move, because that is where the summary renders a gloss from, and it would be invisible: `skip_reason_text` tests membership against that mapping rather than against the tuple, so the spec-closed reason vocabulary reopens with the entire suite still green. Pending plan `cup9r7` measured exactly this from the other direction (its F-14). The `reason` parameter is free TEXT (F-08), so pass the filter name as text and add nothing to either structure.

DO NOT LET THIS PLAN OVERSTATE ITS EFFECT. After it, `aw find` still answers a zero-match selector as a clean success; that is `zyj8io`'s work and this plan must not claim to have fixed the verb family. `aw ipd set` is Order 02 of this Set and is untouched here. The true claim is that `aw runs` reports the runs its filters excluded, on all three surfaces, at exit 0, using the vocabulary the `runnoop` Set already shipped.

ONE INTERACTION THIS PLAN DELIBERATELY DID NOT DESIGN FOR. `issues_only` participates in the empty-state condition `if not summaries and not issues_only:` rather than excluding individual runs, so E-02 must MEASURE what `aw runs --issues` does with exclusions present and V-02 must paste it. If that measurement shows a misleading answer, file a carrier with the evidence; do not quietly adjust this plan's claims to match whatever it does.

This plan carries `- Work-Kind: followup` and `- Priority: low`, inherited from backlog item `om3rzi`, which carries NO `- Blocks-Release:` gate. Do not invent one. Backlog item `om3rzi` is set to `graduated` by the runner on verification; do not set it `done` and do not close it here.

POST-GATE LIFECYCLE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries pasted, concrete evidence. Make the transition through the tooled lifecycle (`aw ipd begin` / `aw ipd finalize`), never by a hand edit or a hand `git mv`. In a managed lane the RUNNER owns the transition and `aw ipd begin` refuses with `AW-LIFECYCLE-ROLE-001`; if that happens, record the refusal, leave the plan in `pending/` with its evidence, and let the runner finalize.
