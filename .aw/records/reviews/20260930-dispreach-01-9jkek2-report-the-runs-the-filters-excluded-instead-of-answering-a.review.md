# Review findings: plan 9jkek2

- Subject-Id: 9jkek2
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-601 (HIGH, fixed), PR-602 (HIGH, fixed), PR-603 (MEDIUM, fixed), PR-604 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `bdb8cc764`. The plan file is committed and unmodified
(`git status --short` empty before edits), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review. This plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator child-row
check does not apply.

All probe work was done in a purpose-built two-run fixture under the gitignored `tmp/` and removed
afterwards. No production file and no test was modified by this review.

THE DIAGNOSIS IS CORRECT AND REPRODUCES END TO END. I built my own fixture (two runs both declaring
setid `probe`, one with a `reviewed` step and one `executed`) and drove the real CLI rather than
reading the plan's findings back:

- F-01 and F-02 REPRODUCE, and together they are the plan's strongest evidence.
  `resolve_target_runs_detailed(['probe'], Path('.'))` returns BOTH run directories with
  `unresolved=[]`, while `aw runs probe --status executed` renders only `run-...-beta` at exit 0 and
  `grep -ci 'alpha|excluded|filter'` over the whole output returns **0**. The resolver says two, the
  report shows one, and nothing reconciles them.
- F-03 REPRODUCES on both surfaces: `aw runs --ipd zzzzzz` and a no-matching-status filter each print
  the bare `no matching runs found` at exit 0, and `--agent` prints exactly `{"runs": []}` at exit 0.
- F-04 REPRODUCES: `aw runs nosuchrun123` exits **2** naming the token, the nine leaves and the `--`
  escape. The plan's correction of the backlog item's framing is right, and fencing this out is right.
- F-05's substance holds: `zyj8io` declares `agent_workflows/cli.py` and `tests/test_cli_find.py` and
  owns the `aw find` half. (Its status has moved from `to-review` to `reviewed` since authoring;
  corrected in place, not filed as a finding.)
- F-07 REPRODUCES by probe: importing `run_selection_policy` alone loads none of `run_viewer`, `cli`
  or `render_stream`, and all three import together OK. The reuse really is cycle-free.
- F-08 REPRODUCES: `render_item_disposition`'s `reason` is free text, and `skip_reason_text` really
  does test membership against `SKIP_REASON_LABELS` rather than the `SKIP_REASONS` tuple, so the trap
  the plan warns about in its fourth failure mode is real and the warning is well placed.
- F-09, F-10, F-11 and F-13 confirmed by reading (zero hits for both searches; the unreasoned
  `if not summary: continue`; the post-loop `if last_n is not None and summaries:` block; the
  empty-state comment's recorded exit-0 ruling, quoted accurately).

The design judgement is sound throughout: exit 0 is correct here and the plan's refusal to copy
`zyj8io`'s exit 2 is well argued from the in-tree ruling; consuming `render_item_disposition` rather
than inventing a second vocabulary is right; and the four named silent-failure modes are each real.

TWO HIGH FINDINGS CAME FROM MEASURING THE SURFACES AND THE FENCE RATHER THAN THE DEFECT.

PR-601 (HIGH), the one that would have stalled execution. E-03 instructs the executor to add "one key
alongside the existing `runs` array" on BOTH `--agent` and `--json`. That is unimplementable on
`--agent`'s partial path. Measured: on the TOTAL path the two surfaces share one statement
(`print(json.dumps({"runs": []}, indent=2 if is_json else None))`) and both emit an envelope, so the
instruction is correct there. On the PARTIAL path they diverge. `--json` builds
`payload = {"runs": [asdict(s) for s in summaries]}` and prints one object (output begins `{\n
"runs": [`). `--agent` instead loops `for s in summaries: print(json.dumps(s_dict, ...))`, emitting
one JSON object PER RUN as JSONL with no envelope (first line begins `{"run_id":"run-...-beta"`).
There is no array for a sibling key to sit beside, and wrapping the stream to create one would break
every line-oriented consumer, a worse regression than the defect being fixed. Separately, `--latest`,
`--summary` and `--issues` each early-return from their own branch on BOTH surfaces, so the generic
path is not the only one needing the fact. FIXED: new finding F-14; E-03 now carries an explicit
per-surface decision (sibling key on `--json`, an additional discriminated JSONL record on `--agent`,
never an envelope) plus an instruction to state the mode-branch coverage either way; V-03 now demands
the JSONL shape be shown intact and fails the item if the partial `--agent` payload begins `{"runs":`;
OQ-03's caveat extended.

PR-602 (HIGH). F-06 claims "no other pending plan declares either of this plan's files" and that
`run_viewer.py` is declared by exactly ONE other plan. Re-scanned: FOUR other pending plans declare
it, and the one that matters is `qvfd4l` (`cxrpwv` Order 01, `to-review`), whose E-03 edits THIS
PLAN'S EXACT filter loop ("canonicalize each step status before matching BOTH the `--failed`
predicate and the `--status` filter") and whose own F-09 already names `9jkek2` and classifies it
correctly. So the contention is mutual and was already recorded on the other side while this plan
asserted there was none. The two are compatible in INTENT (`qvfd4l` changes which runs are selected;
this plan changes only how exclusions are reported and forbids moving any selection) but not in TEXT.
FIXED: F-06 rewritten; the Scope check records it; a new gate paragraph states what it obliges, with
the honest framing that the runner's worktree isolation makes this a merge to resolve rather than a
runtime hazard, and that a mis-resolution could silently change which runs a filter selects, the one
outcome both plans forbid. The `tests/test_run_viewer.py` half of the claim stands.

PR-603 (MEDIUM). "Seven filters" double-counts. The loop has exactly SEVEN `continue` statements,
which E-01 states correctly, but one of them is the `if not summary: continue` that F-10 separately
and correctly classifies as NOT a filter. There are SIX filter predicates (`set_filter`, `ipd_filter`,
`status_filter`, `failed_only`, `active_only`, `since_dt`). The error matters because two items
instruct the executor to build "a fixture exercising all seven filters", which cannot be built as
described. FIXED: new finding F-15; corrected in eight places; the distinct mechanisms are now stated
as six filters plus the unreadable-state skip plus `--last`.

PR-604 (MEDIUM). F-12 asserts the suite is green and makes `3246 passed` the comparison bar. Both
halves fail at review: the total is now `3401 passed` (a drift of 155 in one day), and there is one
failure, the same midnight-boundary flake in
`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`
seen elsewhere in this sweep (it writes two records and compares their rendered dates, so it fails
across a UTC date rollover). The file is outside this plan's fence and unmodified here. FIXED: F-12
rewritten; the Required tests bullet and V-04 now require a re-derived baseline compared by failing
NODE ID rather than by total, which V-04 already half-asked for.

NOTHING WAS DEFERRED and no finding is left OPEN, so no escalation to a `- Blocking: yes` question is
required by Step 4's gate threshold (`review_findings_gate.block_at`, default `HIGH`).

All three open questions verified correctly `resolved` and genuinely non-blocking. OQ-01's exit-0
resolution is backed by the in-tree comment it quotes and I confirmed that comment reads as quoted.
OQ-02's reuse resolution is backed by F-07 and F-08, both independently reproduced, and its
`SKIP_REASON_LABELS` warning is measured-correct. OQ-03's "add a key, do not reshape `runs`" survives
PR-601 unchanged in substance; only its per-surface mechanics needed correcting, which is why it stays
`resolved` with an extended caveat rather than being reopened.

`aw ipd lint --phase review-finalize --agent` reports `conforming` after the revisions.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `--agent`'s partial path is JSONL with no envelope, so "add one key beside the `runs` array" cannot apply. What shape should the exclusion fact take there? | An additional JSONL record carrying a discriminator, printed after the run records; never an envelope around the stream. | (a) Wrap the `--agent` partial stream in a `{"runs": [...], "excluded": [...]}` envelope, rejected because it breaks every line-oriented consumer, a worse regression than the ambiguity being fixed; (b) add the key only to the total path where an envelope already exists, rejected because the plan's own E-03 correctly argues a consumer must not have to know the key exists only when the list is empty; (c) leave `--agent` alone entirely, rejected because the machine surface is where the `{"runs": []}` ambiguity bites hardest (a script cannot read prose). | Measured: partial `--agent` first line is `{"run_id":"run-...-beta"` (per-run JSONL) while partial `--json` is a `runs` envelope; the `is_agent` block's `for s in summaries: print(json.dumps(...))` loop read. Recorded as F-14. | yes |
| D-2 | `qvfd4l` edits the same filter loop. Does that make this plan unsafe to approve or require an ordering declaration? | Neither: record the contention in the plan and name what the second-to-land executor must do. | (a) Add an `- Item-Dependencies:` edge on `qvfd4l`, rejected because the two plans are in different Sets with no logical dependency and the edge would wrongly block one on the other's execution; (b) warn the maintainer the queue is unsafe, rejected because the runner isolates each item in its own worktree and merges through a revalidation gate, so file overlap is not a runtime hazard (AGENTS.md states this explicitly); (c) leave F-06's "uncontested" claim, rejected because it is false and an executor trusting it would be surprised by a conflict. | Four pending plans' `- Scope-Paths:` naming `run_viewer.py`; `qvfd4l` E-03 quoted editing the same loop; its F-09 already naming `9jkek2`; AGENTS.md on runner worktree isolation. | yes |
| D-3 | Should OQ-03 be reopened given PR-601 changed how its answer is implemented? | No: keep it `resolved` and extend its caveat. | Reopening as `open`, rejected because the DECISION (add a key, never reshape `runs`) is unchanged and correct; only the per-surface mechanics were wrong, which is an E-item detail rather than an unresolved design question, and a blocking-free open question would add noise without a pending decision. | The resolution text's own reasoning (reshaping `runs` would silently make consumers report excluded runs as present) holds on both surfaces; F-14 affects only the mechanism. | yes |
| D-4 | The plan's baseline bar cites a total that has drifted 155 tests in one day, and the tree has a time-dependent failure. Fix the number or change the bar? | Change the BAR to a re-derived baseline compared by failing node id, and record why the number is unusable. | (a) Update `3246` to `3401`, rejected because it would drift again before execution and repeats the mistake the plan's own conventions section warns against ("A LIVE COUNT IS NEVER AN ACCEPTANCE BAR"); (b) exempt the flaky test by name, rejected because a hard-coded exemption would mask a genuine future regression in it. | Bare run at review HEAD `1 failed, 3401 passed` versus authored `3246 passed`; the failure re-run showing `- 2026-09-30` versus `+ 2026-10-01`; `tests/test_backlog.py` unmodified in this lane. | yes |
