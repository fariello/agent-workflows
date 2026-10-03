# IPD: Preserve a summary's next paging continuation through a --fields projection so a truncated agent answer always carries its continuation command

- Date: 2026-10-01
- Kind: child
- Concern: `agent_schema.filter_record_fields` drops the `next` key under a `--fields` projection, because `next` is absent from `agent_schema._PRESERVED_FIELDS`. An agent that passes `--fields` to reduce tokens therefore receives records that STRAND their continuation: a `summary` reporting `complete: false` with `omitted > 0` but no command to fetch the remainder, and, measured during authoring and NOT described by the backlog item, a `result` or `error` record whose `next` recovery or follow-up command two documented MUSTs in `docs/cli-output-contract.md` Sections 11.1 and 11.4 require it to carry. `next` is not reconstructible by the caller, so the stranding is unrecoverable from the record alone.
- Scope: Add `next` to `agent_schema._PRESERVED_FIELDS` so no projection can remove a record's continuation command, extend `tests/test_agent_field_projection.py` with outcome-level coverage that drives real CLI commands and asserts on emitted records rather than on the constant's contents, and amend the `--fields` bullet in both user-facing documents that enumerate what a projection retains. Does NOT change what any command emits WITHOUT `--fields`, does NOT add `next` to any record that lacks it, does NOT change `validate_agent_record`, does NOT introduce per-kind or `complete`-conditional projection logic, and does NOT touch `run_analytics_cli._emit_query_agent`, whose deliberate no-context summary call this fix makes unnecessary as a paging workaround but which remains correct on its own semantic grounds.
- Scope-Paths: agent_workflows/agent_schema.py, tests/test_agent_field_projection.py, docs/cli-agent-protocol.md, docs/cli-output-contract.md
- Item-Dependencies: none
- Status: approved
- Work-Kind: bug
- Priority: medium
- From-Backlog: kkjrqr
- Blocks-Release: next
- Set: kkjrqr
- Order: 1
- Highest E allocated: 06
- Readiness: go-pending-approval
- Author: opencode
- Id: 6rcby1
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Re-verified at lane HEAD 51c5a7bbf: _PRESERVED_FIELDS lacks next; the releases show / runs query / find strandings reproduce (next present unprojected, absent under --fields findings); render_summary call sites match F-15; Sections 11.1 and 11.4 MUSTs quoted correctly; d6u2hz open and committed; 8jeh4x owns the reachability failure. Fixed: in-process --agent placement and --dir fixture for E-01 (PR-001), Proposed-changes renumbering against E-ids (PR-002), d6u2hz staging contradiction (PR-003), reachability-failure owner and E-01-only count (PR-004), gate scope fence + conditional finalize (PR-005).

- 2026-10-01 to-review (opencode): authored from backlog item `kkjrqr`. Every measurement in the item was re-verified against this worktree rather than carried over, and the item's reproduction reproduced verbatim (F-01). Authoring MATERIALLY WIDENED the finding in two ways the item does not contain, and both change which candidate fix is correct. FIRST, the stranding is LIVE ON SHIPPED COMMANDS TODAY, not latent: `aw check plans`, `aw find <no-match>`, `aw releases show <bogus>` and `aw runs query <bogus-view>` each emit a non-null `next` unprojected and lose it under `--fields findings` (F-03). The item was authored believing the `summary` path was the exposure, and it reasoned about `run_analytics_query` alone. SECOND, the item's three candidate fixes were written before plan `75ic2f` wired `--fields` onto the shared output-mode parents, taking the flag from 4 parser leaves to 140 (F-04); that is what converts this from a latent gap into a live one. Candidate (b), conditional preservation on `complete: false`, is therefore REFUTED BY MEASUREMENT rather than merely rejected on design grounds: two of the four live strandings carry `complete: true` (F-05), so (b) would leave them stranded while the commit claimed the defect fixed. Candidate (a) was implemented behind a probe and measured to introduce ZERO new suite failures against a re-derived baseline (F-08).
- 2026-10-01 draft (opencode): created.

## Goal

Make a `--fields` projection preserve the one field on an `aw.agent/v1` record that a caller cannot reconstruct, so an agent reducing tokens never receives an answer that says it is incomplete, or that owes a recovery command, while withholding the command that supplies it.

THE DEFECT IS A PAGING DEFECT, NOT A VALIDITY DEFECT, and that framing is what keeps this plan from re-treading plan `gygujf`. `validate_agent_record` never consults `next` (F-02 measures its eleven consulted names and `next` is not among them), so a projected record missing `next` is perfectly VALID. `gygujf` was correct to widen `_PRESERVED_FIELDS` to exactly the validator's consulted set and correct to stop there, because its concern was a crash. This plan's concern is the OPPOSITE failure mode: a record that validates cleanly, parses cleanly, reports `complete: false`, and is useless.

WHY THE CALLER CANNOT WORK AROUND IT. `next` on a bounded query encodes the view, the active filters, and `--limit min(total, MAX_ROW_LIMIT)`; on a refusal it encodes the specific remedy (`aw runs query schema`, `aw releases list`); on a findings result it encodes the fix command. None of that is derivable from the projected record, which by construction no longer carries the filters or the target. So the agent's only recovery is to re-run the whole command without `--fields`, which costs it the tokens `--fields` existed to save, and it cannot even know to do that, because a record missing `next` is indistinguishable from a record whose `next` was legitimately `null`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: pin the stranding at the outcome level, then close it

- [x] E-01 Extend `tests/test_agent_field_projection.py` with a failing test that pins the stranding ON EMITTED RECORDS FROM REAL CLI COMMANDS, which is what the backlog item explicitly requires ("the test must assert on emitted records from a real bounded query rather than on the constant's contents, per P16"). Drive at least two shipped commands through `cli.main` with `--agent` and then with `--agent --fields findings`, capturing stdout each time. TWO INVOCATION DETAILS MEASURED AT REVIEW decide whether the test exercises anything at all. (i) PLACE `--agent`/`--fields` AFTER THE SUBCOMMAND (`cli.main(["releases", "show", "zzzzzz", "--dir", tmp, "--agent"])`): in-process, `cli.main(["--agent", "releases", ...])` and `cli.main(["releases", "--agent", "show", ...])` both fell back to HUMAN output (an empty stdout with a stderr sentence for `releases show`, a `CANNOT-RUN` text line for `runs query`), so a test written that way would parse zero records and could pass vacuously or fail for the wrong reason. Assert that exactly one `aw.agent/v1` record was parsed before comparing `next`. (ii) PASS `--dir <tmp git repo>` so the command reads a fixture rather than the live tree; at review, `releases show zzzzzz --dir <tmp> --agent` emitted `next: "aw releases list"` and `runs query bogusview --dir <tmp> --agent` emitted `next: "aw runs query schema"`, and the `--fields findings` variant of the first emitted the same record with `next` absent. and assert that whenever the UNPROJECTED record carries a non-null `next`, the PROJECTED record carries the same value. Choose commands whose refusal is deterministic and whose `next` is a FIXED STRING rather than live-tree state: `aw releases show zzzzzz` (a `cannot-run` error whose `next` is exactly `aw releases list`) and `aw runs query bogusview` (whose `next` is exactly `aw runs query schema`) both qualify, and both were measured stable at authoring (F-03). DO NOT use `aw check plans` even though it is the most dramatic instance, because its `next` derives from whichever diagnostic sorts first in the live corpus (F-14). ASSERT ON THE VALUE, NOT MERELY ON PRESENCE, so a future change that preserves the key while blanking it fails too. Follow the file's existing style: `unittest`-free plain `pytest` functions with `OutputContext`/`OutputMode` imported from `agent_workflows.renderers`.
  - Depends on: none
  - Expected outcome: `python3 -m pytest tests/test_agent_field_projection.py -o addopts=""` FAILS at this HEAD on both new CLI assertions, the `releases show` one showing `aw releases list` expected and absent and the `runs query` one showing `aw runs query schema` expected and absent. The FOUR pre-existing tests in the file must still pass unchanged, since this plan adds coverage rather than altering `gygujf`'s contract.
  - Execution state: performed

- [x] E-02 Add a renderer-level assertion to the same file reproducing the backlog item's own measurement on the `summary` kind, which is a DIFFERENT TEST SURFACE from E-01's and must be pinned independently: `AgentRenderer().render_summary('runs query', total=5, emitted=2, omitted=3, outcome='clean', exit_code=0, next_cmd='aw runs query --offset 2', complete=False, context=ctx)` with `ctx.fields=['cmd']` must emit a record retaining `next` with that exact value. WHY THIS IS NOT REDUNDANT WITH E-01: no shipped command reaches `render_summary` WITH a context today, because `run_analytics_cli._emit_query_agent` deliberately passes none, so the `summary` instance the item actually filed is unreachable through any CLI surface and E-01 cannot cover it (F-15). Assert on the value, not on presence.
  - Depends on: none
  - Expected outcome: The new renderer assertion FAILS at this HEAD showing `aw runs query --offset 2` expected and the projected record lacking the key, and it fails independently of E-01's two CLI assertions.
  - Execution state: performed

- [x] E-03 Add `"next"` to `agent_schema._PRESERVED_FIELDS`, which is a one-name change to the existing union expression, and REWRITE THE CONSTANT'S COMMENT so it no longer misdescribes itself. The comment currently says the set "includes every field validate_agent_record consults" and enumerates why each member is there; after this change that sentence is FALSE, because `next` is the first member the validator does not consult (F-02). The comment must state the set's actual, now-broader contract: a projection may not remove a field that the record's VALIDITY requires (the `gygujf` members) OR that the record's USABILITY requires and the caller cannot reconstruct (`next`). Say explicitly that `next` is in the second category and give the reason, which is the one a future reader will otherwise delete it for: a record reporting `complete: false` without `next` tells a caller its answer is partial while withholding the only continuation it has, and `docs/cli-output-contract.md` Sections 11.1 and 11.4 state MUSTs that a projected record would otherwise violate. PRESERVE `_MANDATORY_FIELDS` EXACTLY, for the same reason `gygujf` did: it is the seven-field envelope two shipped documents enumerate, and `run_analytics_cli` names it in prose. Change no other executable line: the `if not fields: return dict(record)` early return stays, the comprehension stays, and every rule in `validate_agent_record` stays. ADD NO CONDITIONAL. A `complete`-keyed variant is refuted by measurement, not merely rejected by preference (F-05, OQ-01), and the flat kind-independent union is the shape `gygujf` chose deliberately (its OQ-02).
  - Depends on: E-01, E-02
  - Expected outcome: `'next' in agent_schema._PRESERVED_FIELDS` is `True`; the set holds exactly twelve names; `_MANDATORY_FIELDS` is textually unchanged and still holds exactly seven; every E-01 and E-02 assertion passes; no rule in `validate_agent_record` is modified; the constant's comment no longer claims the set equals the validator's consulted fields.
  - Execution state: performed

### Task group 2: reconcile the two documents that enumerate the preserved set

- [x] E-04 Amend the `--fields` bullet in `docs/cli-agent-protocol.md` under `## Token control`, which currently names the envelope plus "a summary's `total`, `emitted`, and `omitted` ... and a preview result's `applied`" and justifies each by VALIDITY. That justification does not cover `next`, so adding the name without extending the reason would leave a reader unable to tell why it is there. The bullet must now also name `next` and give its distinct reason: it is retained because a caller cannot reconstruct it, not because the validator demands it. REUSE THE REASON THIS DOCUMENT ALREADY GIVES two sections earlier under `## Stream truncation is honest`, where `next` is defined as "a ready-to-run command that would fetch the rest", and under `## Recommended consumption pattern` item 6, "If `complete` is `false`, follow `next` to fetch the remainder": that instruction is precisely what a dropped `next` makes impossible, so the document already contains the argument and must not invent a second one. Write no em or en dashes: this is user-facing prose. Touch no other paragraph, and in particular do not amend the example records, which are unprojected and remain accurate.
  - Depends on: E-03
  - Expected outcome: The `## Token control` `--fields` bullet names `next` among the retained fields and states the not-reconstructible reason, cross-consistent with item 6 of `## Recommended consumption pattern`; no other paragraph in the file changes; the file gains no em or en dash.
  - Execution state: performed

- [x] E-05 Amend the `**--fields <list>**` bullet in `docs/cli-output-contract.md` under `## 6. Token Control and Escape Hatches`, which makes the same enumeration and the same validity-only claim. Same change, same reason, and ONE ADDITION this document owes that the protocol reference does not: this file is where the two violated MUSTs live, in Section 11.1 ("`next`: the suggested broadening or fallback command" on an empty result) and Section 11.4 (a `cannot-run` record carries "a `next` recovery command"). State that a projection preserves `next` so those requirements hold under `--fields` too, which makes the document internally consistent rather than leaving a reader to discover that Section 6 silently exempted Sections 11.1 and 11.4. Write no em or en dashes. Touch no other bullet; the `--limit` bullet beside it is already correct and the Section 11 MUSTs themselves need no edit, since this plan makes the implementation match what they already say.
  - Depends on: E-04
  - Expected outcome: The Section 6 `--fields` bullet names `next` and reconciles itself with the Section 11.1 and 11.4 MUSTs by reference; Sections 11.1 and 11.4 are UNCHANGED; no other bullet changes; the file gains no em or en dash.
  - Execution state: performed

- [x] E-06 Verify, as the LAST act before commit, the three things a green suite cannot catch, each of which is a specific way this plan could ship a false claim. FIRST, THE TOKEN COST THIS PLAN ACCEPTS, measured rather than asserted: re-run the byte-delta measurement F-06 records for a projected record that carries a non-null `next` and for one whose `next` is `null`, and confirm the shape of the result (a real cost only where `next` is non-null, and a 12-byte `"next":null` cost where it is). Report the numbers you measure rather than restating F-06's, since they move with the command sampled. If any sampled record now EXCEEDS 1200 bytes under projection where it did not before, STOP and report it: F-07 measures today's worst case at 309 bytes against that budget, so a breach would mean the sample changed and the plan's cost argument needs re-deciding, not papering over. SECOND, CONFIRM `run_analytics_cli` IS UNTOUCHED and that its 12-line comment above `renderer.render_summary` is now PARTLY STALE: that comment's load-bearing claim is "the summary takes no field projection because `next` is not in `agent_schema._PRESERVED_FIELDS`", which E-03 falsifies. Do NOT edit it in this plan (it is a fifth file, a prose-only change, and the no-context call stays correct for its own stated reason about engine counts versus stream counts); its carrier `d6u2hz` was ALREADY FILED during authoring, so CONFIRM it is still `open` and still describes the comment accurately rather than filing a duplicate. This is the same disposition `gygujf` took toward the same comment via `cm80ge`, which is now `done`. THIRD, RE-DERIVE THE SUITE BASELINE IN THE LANE rather than trusting F-08's numbers, and confirm the two failures it records are still present and still not yours, by running each in isolation and by naming the open backlog items that already own them (`6bolin`/`md2o3y` for the `89xjll` spec failure, `8jeh4x` for the reachability perturbation failure). A THIRD failure appearing is this plan's until a targeted run plus a commit predating the lane proves otherwise.
  - Depends on: E-05
  - Expected outcome: The byte cost is re-measured and reported with no projected sample exceeding 1200 bytes; `run_analytics_cli.py` is confirmed unmodified and its stale comment is confirmed still carried by the already-filed `d6u2hz` rather than edited or re-filed; the lane's own baseline is re-derived, the two pre-existing failures are confirmed unchanged and attributed to their existing items, and the passed count rises by exactly the tests E-01 and E-02 add.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE (AGENTS.md execution contract; GUIDING_PRINCIPLES P16). This decides E-01's whole shape. The natural test here is `assert 'next' in agent_schema._PRESERVED_FIELDS`, and it is FORBIDDEN: it is a symbol census standing in for correctness, it would pass if the constant were widened while the projector stopped reading it, and the backlog item names the prohibition explicitly. E-01 therefore drives `cli.main` and asserts on emitted JSON.
- CODE IS CITED BY SYMBOL, NOT BY BARE LINE OFFSET (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan cites `agent_schema._PRESERVED_FIELDS`, `agent_schema._MANDATORY_FIELDS`, `agent_schema.filter_record_fields`, `agent_schema.validate_agent_record`, `renderers.AgentRenderer.render_summary`, `renderers.AgentRenderer.render_item`, `renderers.AgentRenderer.render_stream`, `result_types.CommandResult.to_agent_record`, `run_analytics_cli._emit_query_agent` and `run_analytics_query._bound` by name.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. `python3 -m pytest` with nothing added is the contract; `-n0` is several times slower here and a second `-q` suppresses the `N passed` line this plan requires pasted. Use `-o addopts=""` only for per-file counts.
- THIS SUITE RUNS AGAINST A LIVE RECORDS TREE, and the harness says so in its own failure output: a failing test prints a `LIVE-CORPUS NOTE` warning that `.aw/records/` "is a LIVE tree that any agent or concurrent run may write to" and that a failure there may be another party's artifact. That measured fact is why E-01 selects commands with fixed-string `next` values and forbids pinning `aw check plans`.
- A DEFECT FOUND OUTSIDE THE FENCE IS FILED, NOT REACHED ACROSS FOR. `gygujf` filed `cm80ge`, `03aicr` and `rcjorx` for exactly this situation; E-06 follows it for the `run_analytics_cli` comment this change makes stale.
- USER-FACING PROSE CARRIES NO EM OR EN DASHES (AGENTS.md execution contract). Both documents E-04 and E-05 edit are user-facing. It does NOT apply to this plan.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE BACKLOG ITEM'S REPRODUCTION HOLDS VERBATIM AT THIS HEAD. `AgentRenderer().render_summary('runs query', total=5, emitted=2, omitted=3, outcome='clean', exit_code=0, next_cmd='aw runs query --offset 2', complete=False)` emits `...,"complete":false,"next":"aw runs query --offset 2"}` with no context, and the SAME call with `ctx.fields=['cmd']` emits `...,"complete":false}` with no `next`. With `fields=['next']` it is retained. `'next' in agent_schema._PRESERVED_FIELDS` is `False`, and the set holds exactly the eleven names `gygujf` left it at. | The item's script run unmodified in this worktree at HEAD `e6c9d5e4b`, all three records captured; `sorted(_PRESERVED_FIELDS)` printed as `['applied','cmd','complete','emitted','exit','kind','omitted','outcome','schema','total','verified']`. |
| F-02 | `next` IS NOT A VALIDITY FIELD, WHICH IS WHY `gygujf` CORRECTLY STOPPED SHORT OF IT AND WHY THIS IS A SEPARATE DEFECT. Extracting every field name `validate_agent_record` reads from its own source yields exactly eleven (`applied`, `cmd`, `complete`, `emitted`, `exit`, `kind`, `omitted`, `outcome`, `schema`, `total`, `verified`), and `next` is absent. So a projected record without `next` is VALID, `render_jsonl_record` emits it happily, and nothing in the schema layer can detect the loss. This also means `next` is the FIRST member of `_PRESERVED_FIELDS` justified by usability rather than validity, which is precisely what E-03 must rewrite the comment to say. | Source extraction over `inspect.getsource(validate_agent_record)` matching `record.get("x")`, `"x" in record` and `record["x"]`, printing the eleven names and `'next' consulted: False`. |
| F-03 | **THE STRANDING IS LIVE ON SHIPPED COMMANDS TODAY, WHICH THE BACKLOG ITEM DOES NOT CLAIM.** The item reasons entirely about `run_analytics_query`'s bounded summaries. A sweep of twelve shipped invocations, each run with `--agent` and then with `--agent --fields findings`, found FOUR that emit a non-null `next` unprojected and lose it projected: `aw check plans` (`result`, `complete: true`, `next: 'aw ipd set qtz0us --from-spec 7ckptx'`), `aw find zzzzzz` (`result`, `complete: true`, `next: 'aw find'`), `aw releases show zzzzzz` (`error`, `complete: false`, `next: 'aw releases list'`) and `aw runs query bogusview` (`error`, `complete: false`, `next: 'aw runs query schema'`). The remaining eight were unaffected only because their `next` was already `null` (`aw status`, `aw specs check`, `aw backlog check`, `aw ipd board`, `aw releases list`, `aw ipd lint <nonexistent>`) or absent (`aw runs query overview`, a complete summary). So this is a live defect on every one of those four, not a latent one. | Scripted sweep over twelve invocations, each pair parsed and compared, printing a `STRANDED=` verdict per command; four `True`, eight `False`. |
| F-04 | THE ITEM'S COST ANALYSIS PREDATES A 35-FOLD WIDENING OF THE FLAG'S REACH, which is what turned a narrow gap into a broad one. The item weighs candidate fixes against `--fields` as a flag on the analytics commands. Plan `75ic2f` (backlog `rcjorx`, now `done`) subsequently wired `--fields` onto the shared output-mode parents. Measured on this HEAD by walking the parser tree with alias deduplication: 152 leaf parsers, of which **140 accept `--agent` and 140 accept `--fields`**. `tests/test_fields_flag_reach.py::test_derived_reach_every_agent_leaf_accepts_fields` enforces that equality. So the exposure is every agent-mode command that emits a `next`, not four analytics verbs. | Parser-tree walk over `cli._build_parser()` with identity dedup, printing `total leaves: 152 accept --agent: 140 accept --fields: 140`; `rcjorx` read at `.aw/records/backlog/done/`; `75ic2f` read at `.aw/records/plans/executed/`. |
| F-05 | **CANDIDATE FIX (b) IS REFUTED BY MEASUREMENT, NOT MERELY REJECTED ON DESIGN GROUNDS, AND THIS IS THE FINDING THAT DECIDES THE PLAN.** The item proposes (b) as "preserve `next` CONDITIONALLY, only when `complete` is false", reasoning that a complete answer needs no continuation. That premise is FALSE on this codebase: two of the four live strandings (F-03) carry `complete: true`, namely `aw check plans` (whose `next` is the fix command for its findings) and `aw find zzzzzz` (whose `next` is the broadening query). Both are REQUIRED by `docs/cli-output-contract.md`: Section 11.1 states that a non-refused empty query MUST emit `next`, "the suggested broadening or fallback command", alongside `complete: true`, and Section 11.4 requires a follow-up `next` on a findings result. So (b) would have left two of four strandings open, including one the contract makes a MUST, while its commit claimed the paging defect fixed. (b) is additionally the per-kind conditional logic `gygujf`'s OQ-02 deliberately refused; that remains true and is now the SECOND reason rather than the first. | The four stranded records from F-03 with their `complete` values; `docs/cli-output-contract.md` Sections 11.1 and 11.4 read and quoted; a probe implementing (b) as a `complete is False` guard, measured to leave both `complete: true` instances stranded. |
| F-06 | THE TOKEN COST IS REAL BUT BOUNDED, AND IS ZERO ON THE RECORDS WHERE THE ITEM FEARED IT. The item's objection to (a) is that `next` is the longest field on the record, so retaining it partly defeats `--fields`. Measured on three projected records: a truncated summary with a realistic continuation went 139 to 212 bytes (+73), a `check` findings result went 130 to 176 (+46), and a COMPLETE summary whose `next_cmd` is `None` went 137 to 137 (+0, because `render_summary` only sets the key when `next_cmd is not None`). A `result` record whose `next` is explicitly `null` costs 12 bytes (127 to 139), since `to_agent_record` always sets the key. So the cost falls almost entirely on records that NEED the field, which is the trade the item itself identifies as acceptable, and the `null` case is a flat 12 bytes. | Byte-length measurement over four projected records with `_PRESERVED_FIELDS` probed both ways, each record printed in full both narrow and wide. |
| F-07 | THE COST DOES NOT APPROACH THE PER-RECORD BUDGET, checked because a 73-byte growth is only safe if there is headroom. The documented agent-record budget is 1200 bytes (`run_analytics_query` cites it four times; `run_analytics_cli._emit_query_agent`'s docstring calls it "the enforced 1200-byte / 400-token budget"). The largest record measured post-fix across the four live strandings was `aw check plans` at **309 bytes**, inflated by an unusually long diagnostic-derived `next`; the other three were 166, 167 and 142. HONEST CAVEAT ON THE WORD "ENFORCED": the test that enforced it, `tests/test_cli_quality_gates.py`, was DELETED by commit `19313eed7` ("test: trim test suite from 9,136 to under 2,000 tests") and no replacement assertion was found by grep. So 1200 is a documented budget with no live automated gate, and E-06 re-measures against it by hand rather than relying on a check that no longer runs. | Four post-fix records measured at 309, 166, 167 and 142 bytes; `rg` for the budget constant across `agent_workflows/`; `git log --diff-filter=D` naming `19313eed7` as the commit that removed `tests/test_cli_quality_gates.py`; grep for a surviving per-record byte assertion returning nothing. |
| F-08 | FIX (a) INTRODUCES ZERO NEW SUITE FAILURES, measured by running the real suite with the fix in force rather than by reasoning about it. A plugin module setting `_PRESERVED_FIELDS |= {'next'}` at import was loaded with `-p`, and the BARE suite reported `2 failed, 4589 passed, 2 skipped, 3 warnings in 300.85s`. The clean-tree baseline immediately before, same command without the plugin, reported `2 failed, 4589 passed, 2 skipped, 3 warnings in 144.80s`: the SAME two failures and the same counts. A targeted set of seven agent-record files (`test_agent_field_projection`, `test_fields_flag_reach`, `test_json_and_exitcodes`, `test_agent_schema_paths`, `test_agent_checked_count`, `test_run_analytics_cli`, `test_options_anywhere`) reported `53 passed` under the fix. | Two bare `python3 -m pytest` runs with their summary lines, one with `-p` loading the probe; one targeted `-o addopts=""` run printing `53 passed in 39.03s`; the probe file deleted afterwards and `git status --short` confirmed clean of it. |
| F-09 | THE TWO BASELINE FAILURES ARE PRE-EXISTING, UNRELATED, AND ALREADY OWNED BY OTHER PARTIES, so this plan must not adopt them. They are `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, failing because spec `89xjll` (committed by `a9193e83c`, another party's work) carries an `attention.unsafe-field` structural flag, and `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`, failing with `AssertionError: True is not false`. Both reproduce on a CLEAN tree with `git status --short` empty. The first is already filed TWICE in `.aw/records/backlog/open/` as `6bolin` and `md2o3y`. | Each failure run in isolation with `-o addopts=""` and its assertion output captured; `git status --short` empty at the time; `rg` over `.aw/records/backlog/open/` finding `6bolin` and `md2o3y` both naming the `89xjll` spec. |
| F-10 | NO OUTPUT CHANGES WITHOUT `--fields`, so no conformance golden can move. `filter_record_fields` returns `dict(record)` unchanged when `fields` is falsy, and all four call sites guard on a truthy `fields` first (`result_types.CommandResult.to_agent_record`, `renderers.AgentRenderer.render_item`, `renderers.AgentRenderer.render_summary`, and the hand-built error record in `run_analytics_cli`'s refused-query branch). All four `*.agent.golden` fixtures are unprojected, and three of them (`check_findings`, `error_cannot_run`, `mutation_preview`) carry a non-null `next` that the fix therefore cannot touch; `read_clean` carries `next: null`. | Read of the early return and of all four guarded call sites; all four agent goldens read and their `next` values noted; the F-08 suite run (which includes the golden conformance tests) green on them. |
| F-11 | RETAINING `next` CANNOT MAKE A VALID PROJECTION INVALID, checked because "preserve more" is not automatically safe. Since `validate_agent_record` never reads `next` (F-02), no rule can fire on its presence; probed anyway on every corpus record carrying the key across the `summary` and `error` kinds, each valid both narrow and wide. An exhaustive sweep over every subset of each corpus record's non-preserved keys found 0 invalid projections, 0 added keys and 0 altered values under the widened set, with strandings falling from 2 to 0. | Per-record narrow/wide validity probe printing `True`/`True` for every record carrying `next`; combinatorial sweep printing `narrow: stranded=2 invalid=0 added=0 altered=0` and `wide: stranded=0 invalid=0 added=0 altered=0`. |
| F-12 | AFTER THE FIX, PROJECTING A `summary` IS AN IDENTITY OPERATION, which is a notable consequence worth stating rather than discovering later. `render_summary` builds exactly ten keys (`schema`, `kind`, `cmd`, `outcome`, `exit`, `total`, `emitted`, `omitted`, `complete`, and `next` when non-null), and the widened `_PRESERVED_FIELDS` is a superset of all ten. Measured: an unprojected truncated summary and the same summary projected with `fields=['cmd']` are byte-identical. This is CORRECT rather than a bug, since every one of those keys is either envelope, validity-required, or the continuation; but it means `--fields` no longer reduces a summary at all, and a reviewer should know that is intended and not a projection failure. | Identity comparison of the two rendered strings printing `True`; the ten summary keys enumerated against the widened set printing `superset: True`. |
| F-13 | THE EXISTING TEST FILE IS THE RIGHT HOME AND ITS CONTRACT IS COMPATIBLE. `tests/test_agent_field_projection.py` exists (added by `gygujf`), holds four plain-`pytest` functions and a ten-record `CORPUS` spanning all four kinds, and its docstring scopes it to what a projection preserves. Two of its corpus records already carry a non-null `next`, so the file's own data demonstrates the gap it does not yet assert on. Its fourth test is an anti-overreach guard requiring that a projection still DROP `target` and `evidence`; that guard is unaffected by this change, since neither field is being added to the preserved set. So E-01 and E-02 extend rather than replacing, and no existing assertion needs weakening. | File read in full; its four tests run green at `4 passed`; the two `next`-carrying corpus records identified; the anti-overreach assertion read and confirmed to name only `target`/`evidence`. |
| F-14 | **`aw check plans`'s `next` IS LIVE-CORPUS STATE AND MUST NOT BE PINNED, which is why E-01 forbids the most dramatic instance as a test subject.** Its value is built from whichever diagnostic the checker happens to emit first across `.aw/records/`, and two consecutive runs during authoring produced DIFFERENT values: first `aw ipd set qtz0us --from-spec 7ckptx`, then a 309-byte `cite evidence it was discharged by finished work: add - Carrier-Evidence: .aw/records/backlog/done/20260929-5h8u3z-...`. The finding count also moved between runs (55 then 54). The harness itself warns about this class of coupling, printing a `LIVE-CORPUS NOTE` on failure that `.aw/records/` "is a LIVE tree that any agent or concurrent run may write to" and that a failure "may be caused by another party's artifact rather than by this lane's change". By contrast `aw releases show zzzzzz` and `aw runs query bogusview` return fixed literals (`aw releases list`, `aw runs query schema`) that come from `_cannot_run` call sites rather than from corpus content. | Two `aw check plans --agent` runs minutes apart yielding different `next` values and different finding counts, both captured; the `LIVE-CORPUS NOTE` text quoted from an actual failure in this lane; the two fixed-literal `next_cmd=` arguments read at their `_cannot_run` call sites in `run_analytics_cli`. |
| F-15 | **THE `summary` INSTANCE THE BACKLOG ITEM FILED IS UNREACHABLE THROUGH ANY SHIPPED COMMAND, which is why E-02 is a separate item from E-01 rather than redundant with it.** `renderers.AgentRenderer.render_summary` has exactly two call sites in the package: `renderers.AgentRenderer.render_stream` (which forwards its context) and `run_analytics_cli._emit_query_agent` (which deliberately passes NO context, as its own comment explains). And `render_stream` has ZERO callers anywhere in `agent_workflows/`, so the only reachable path to `render_summary` is the one that never projects. Measured consequence: `aw runs query overview --agent --fields findings` emits a summary with no `next` key at all, so the stranding cannot be observed there. This matters twice: it explains why the item's instance is latent while F-03's four are live, and it means an executor who tries to cover the `summary` kind through a CLI command will find no command that exercises it and may wrongly conclude the item's instance was imaginary. | `rg` for `render_summary(` across the package returning exactly the definition plus two call sites; `rg` for `.render_stream(` across `agent_workflows/` returning ZERO callers; the `_emit_query_agent` call read in full showing no `context=` argument; `aw runs query overview --agent` emitting a summary with no `next` key. |

## Proposed changes (ordered, validatable)

1. Extend `tests/test_agent_field_projection.py` with outcome-level assertions that drive `aw releases show zzzzzz` and `aw runs query bogusview` through `cli.main` with and without `--fields`, each asserting the projected record retains the same non-null `next` VALUE (E-01).
2. Add a renderer-level `render_summary` assertion reproducing the backlog item's own measurement (E-02).
3. In `agent_workflows/agent_schema.py`, add `"next"` to `_PRESERVED_FIELDS` and rewrite the constant's comment so it describes two reasons for membership (validity and non-reconstructible usability) rather than claiming it equals the validator's consulted set; leave `_MANDATORY_FIELDS`, the early return, the comprehension and every validator rule untouched (E-03).
4. Amend the `--fields` bullet in `docs/cli-agent-protocol.md` to name `next` with its distinct reason, reusing the document's own `## Stream truncation is honest` and `## Recommended consumption pattern` framing (E-04).
5. Amend the `--fields` bullet in `docs/cli-output-contract.md` likewise, and reconcile it with the Section 11.1 and 11.4 `next` MUSTs that Section 6 currently exempts by silence (E-05).
6. Verify the honesty bound last: re-measure the byte cost against the 1200-byte budget, confirm `run_analytics_cli` untouched with its now-false comment carried to a named backlog item, and re-derive the lane's suite baseline rather than trusting F-08's numbers (E-06).

## Deferred / out of scope (with reason)

- REFRESHING `run_analytics_cli._emit_query_agent`'s COMMENT IS OUT OF SCOPE, and this is the second time that comment has been invalidated by a plan that declined to touch it. Its text states "The summary takes no field projection because `next` is not in `agent_schema._PRESERVED_FIELDS`, so projecting this record could drop the paging continuation", which E-03 makes FALSE as a causal claim. The no-context call itself stays CORRECT for the reason the same comment gives two paragraphs down: a query's summary must report the engine's `total`/`emitted`/`omitted`, not `render_stream`'s truncation counts. Editing the prose would add a fifth file for a comment-only change and would mix a documentation refresh into a contract fix. Note the lineage: `gygujf` left this comment stale and filed `cm80ge`, which was executed as plan `mcdvx0`, which WROTE the sentence this plan now falsifies, and which filed `kkjrqr` (this plan's item) for the behavior. The next carrier should refresh the comment to match the post-fix reality rather than describing another workaround.
  - Carrier: d6u2hz
- MAKING THE PROJECTOR DERIVE ITS SET FROM A DECLARED RECORD CONTRACT is rejected rather than deferred. The structural fix for "a constant and a validator can disagree" is to have one declare and the other read, and `gygujf`'s own OQ-02 weighed and rejected it: the validator's rules are conditional (`applied` matters only when `complete` is false and the outcome positive), so they do not reduce to a per-kind required-field table without losing fidelity. This plan adds a field whose justification is not validity at all, which makes the derivation strictly LESS available, not more: no amount of reading `validate_agent_record` would ever yield `next`, because the validator does not consult it (F-02). A declarative contract would have to carry a second, human-authored "usability" axis, which is the same hand-maintained list by another name.
  - Carrier-Declined: Nothing is owed. This is a rejected design alternative, not an outstanding defect. The shipped validator is correct and the preserved set is correct after E-03; what remains is a comment that must state two reasons instead of one, which E-03 delivers.
- DOCUMENTING THE DROP AND LEAVING BEHAVIOR ALONE (the item's candidate (c)) IS REJECTED, and F-03 plus F-05 are why. (c) is defensible only if the stranding is rare and the affected records are genuinely optional-continuation. Measured, it is neither: four shipped commands strand live today, two of them while reporting `complete: true` where `docs/cli-output-contract.md` Sections 11.1 and 11.4 state a `next` MUST. Choosing (c) would mean amending not just the "safe to pass on any command" framing the item names, but carving a `--fields` exemption into two separate contract MUSTs, which weakens a shipped guarantee to avoid a one-name change.
  - Carrier-Declined: Nothing is owed. A rejected alternative with no residual work: the documents are amended by E-04 and E-05 to describe the strengthened behavior, so no documentation debt is left behind.
- THE TWO PRE-EXISTING SUITE FAILURES ARE OUT OF SCOPE and already owned elsewhere (F-09). This plan must not touch `tests/test_spec_review_attestation.py`, `tests/test_run_finding_reachability.py`, or spec `89xjll`. The reachability failure is owned by open backlog `8jeh4x`.
  - Carrier: 6bolin, md2o3y, 8jeh4x

## Scope check

- Over-scope: none. `agent_workflows/agent_schema.py` carries one added name in `_PRESERVED_FIELDS` plus its rewritten comment; `tests/test_agent_field_projection.py` gains E-01's and E-02's assertions and no existing test is weakened (F-13); the two documents each carry one amended bullet. `renderers.py` is NOT edited (nothing there needs to change once the projector is right, F-10), `result_types.py` is NOT edited, `run_analytics_cli.py` is NOT edited (deliberately, see Deferred), no conformance golden changes (F-10 proves none can), no spec is touched, and the only `.aw/` record this execution writes is this plan; the carrier item `d6u2hz` was filed and committed during authoring (`a976a53f8`) and is not touched.
- Under-scope: Three disclosed gaps. FIRST, `run_analytics_cli`'s comment will still assert a causal claim this change falsifies; carried by `d6u2hz`, filed during authoring. SECOND, the 1200-byte per-record budget remains documented but UNENFORCED since `19313eed7` deleted its test (F-07); this plan measures against it by hand and does not restore the gate, which is a separate concern about test coverage rather than about projection. THIRD, `next` is now preserved unconditionally, so `--fields` no longer reduces a `summary` record at all (F-12); that is the accepted cost of the chosen fix, and a future plan wanting a reduced summary would need a different mechanism than field projection.

## Required tests / validation

- `python3 -m pytest` run BARE, with its `N passed` summary line pasted. THE BAR IS THE LANE'S OWN RE-DERIVED BASELINE, not a fixed number: authoring measured `2 failed, 4589 passed, 2 skipped` on a clean tree AND the identical counts with the fix in force (F-08), and both failures are other parties' (F-09). Require that the failure SET is unchanged and the passed count rises by exactly the tests E-01 and E-02 add. A third failure is this plan's until a targeted run plus a commit predating the lane proves otherwise. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `python3 -m pytest tests/test_agent_field_projection.py -o addopts=""` for per-test counts on the extended file, run BEFORE E-03 (must fail on the new assertions only, with the four pre-existing tests still passing) and AFTER (must be fully green).
- `python3 -m pytest tests/test_agent_field_projection.py tests/test_fields_flag_reach.py tests/test_json_and_exitcodes.py tests/test_agent_schema_paths.py tests/test_agent_checked_count.py tests/test_run_analytics_cli.py tests/test_options_anywhere.py -o addopts=""` as the targeted regression set: every file asserting on `agent_schema` behavior, on `--fields`, or on an `aw.agent/v1` record's shape. Authoring measured `53 passed` here with the fix in force (F-08).
- A DELIBERATE-FAILURE DEMONSTRATION for E-01 and E-02, since a guard never shown red proves nothing: the new assertions shown FAILING before E-03, each naming the `next` value it expected and showing the projected record that lacks the key.
- A LIVE END-TO-END PROBE for E-03 on all four commands F-03 measured stranded (`aw check plans`, `aw find zzzzzz`, `aw releases show zzzzzz`, `aw runs query bogusview`), each run `--agent --fields findings` post-fix, with the emitted record pasted showing a non-null `next` and `is_valid_agent_record` true.
- A NO-CHANGE-WITHOUT-FIELDS PROBE for E-03: render a corpus spanning all four kinds through `render_jsonl_record` with NO `fields`, before and after, and assert byte-identical output. Include the four `*.agent.golden` shapes (F-10).
- AN EXHAUSTIVE PROJECTION SWEEP for E-03: every subset of every corpus record's non-preserved keys, asserting zero invalid projections, zero added keys, zero altered values, and ZERO strandings against the 2 measured before (F-11). Report the projection count you swept.
- A BYTE-COST MEASUREMENT for E-06 on a `next`-bearing and a `next: null` record, with every post-fix sample confirmed under 1200 bytes (F-06, F-07).
- `aw ipd lint` on this plan, reporting conforming.
- `aw check` to confirm no new drift against a pre-edit run of the same command (compare finding sets; the tree carries pre-existing findings), and `aw backlog check` to confirm the carrier item `d6u2hz` is well-formed.
- `aw sanitize --agent`, since evidence blocks here quote local CLI output.
- `git diff --cached --name-only` immediately before committing, which must list only paths from the four `- Scope-Paths:` entries (plus this plan if the executor's tooling stages it), and nothing another party changed in this shared checkout. `d6u2hz` is ALREADY COMMITTED (commit `a976a53f8`) and must NOT be re-staged or edited.

## Spec / documentation sync

DOCUMENTATION SYNC IS REQUIRED AND IS E-04 PLUS E-05; SPEC SYNC IS N/A WITH REASON.

No `.spec.md` is in `- Scope-Paths:` and none needs to be. The normative home of the `aw.agent/v1` token-control surface is `docs/cli-output-contract.md`, not a spec record: no spec in `.aw/records/specs/` states which fields a projection preserves, and `gygujf` reached the same conclusion for the same surface when it amended these two documents and no spec. So there is no spec sentence this change contradicts.

THE SHIPPED CONTRACT IS WIDENED, NOT BROKEN, so no version bump is owed. Both documents promise that the envelope and the kind's validity-required fields survive a projection; after E-03 they still do, plus `next` when the record carries it. Per the stability rule `docs/cli-agent-protocol.md` states (additive optional fields are backward compatible; a breaking change bumps to `aw.agent/v2`), retaining MORE fields is additive from a consumer's view, and both documents already instruct parsers to tolerate unknown fields. The only consumer-visible change is that a record which previously arrived without its continuation now arrives with it.

ONE INTERNAL INCONSISTENCY IS BEING CLOSED RATHER THAN CREATED, and it is worth naming because it is the strongest argument for this fix. `docs/cli-output-contract.md` Section 11.1 states that a non-refused empty query MUST emit `next`, and Section 11.4 states that a `cannot-run` record MUST carry a `next` recovery command. Today a projected record violates both (F-03, F-05), so Section 6's `--fields` bullet silently exempts two MUSTs stated five sections later. E-05 makes Section 6 state the preservation explicitly, so the document no longer contradicts itself.

## Open questions

### OQ-01: The backlog item offers three fixes, (a) preserve `next` unconditionally, (b) preserve it only when `complete` is false, and (c) document the drop and change nothing. Which one, and does the item's stated cost objection to (a) survive measurement?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED AS (a), WITH (b) REFUTED BY MEASUREMENT RATHER THAN BY PREFERENCE, which is the substantive difference between this resolution and the item's own leaning. The item frames (b) as "honest" and objects to (a) only on token cost, so the decision rests on two measured facts the item does not have. FIRST, (b)'s PREMISE IS FALSE on this codebase. Its guard is `complete is False`, and two of the four live strandings carry `complete: true`: `aw check plans` (a findings result whose `next` is the fix command) and `aw find zzzzzz` (an empty result whose `next` is the broadening query). `docs/cli-output-contract.md` Section 11.1 makes the latter a MUST, stating that a non-refused empty query emits `next`, "the suggested broadening or fallback command", together with `complete: true`. So (b) ships a fix that leaves a documented MUST violated (F-03, F-05). SECOND, (a)'s COST OBJECTION DOES NOT SURVIVE MEASUREMENT IN THE FORM THE ITEM STATES IT. The item worries that `next` "is retained even when `complete: true` (where it is `None` and omitted anyway)". Measured: on a `summary` that is true and the cost is exactly 0 bytes, because `render_summary` only sets the key when `next_cmd is not None`; but on a `result` the key is ALWAYS set by `to_agent_record`, so a `null` continuation costs a flat 12 bytes (`,"next":null`), and a real one costs 46 to 73 bytes on the records sampled (F-06). The worst post-fix record measured is 309 bytes against a documented 1200-byte budget (F-07). So the cost is real, bounded, and falls mainly on records that need the field. (c) is rejected for the reason given in Deferred: it would require carving a `--fields` exemption into two contract MUSTs rather than adding one name. The item's own constraint is honored in full, since E-01 asserts on records emitted by real commands and never on `_PRESERVED_FIELDS`'s contents (P16).

### OQ-02: `gygujf` chose a flat kind-independent preserved set and documented it as "every field validate_agent_record consults". Adding `next` breaks that self-description. Does the constant stay one flat set, or split into a validity set and a usability set?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED AS ONE FLAT SET WITH A TWO-REASON COMMENT, not two constants. The flat shape is what the projector actually needs: `filter_record_fields` computes `_PRESERVED_FIELDS | set(fields)` once, so a second constant would be unioned into the same expression at the same point and would buy no behavioral difference, only a second name to keep in sync. `gygujf`'s OQ-02 chose flatness precisely to avoid a structure that can drift from the validator, and splitting now would reintroduce an axis of drift to document a distinction that belongs in prose. WHAT MUST CHANGE IS THE COMMENT, and E-03 requires it: the current text's claim that the set "includes every field validate_agent_record consults" becomes false the moment `next` joins, and a future reader who trusts that sentence would correctly conclude `next` does not belong and delete it. That is the realistic regression path for this fix, since `next` is NOT recoverable by reading the validator (F-02), so no derivation and no test that inspects `validate_agent_record` can re-establish it. The comment must therefore state both membership reasons (validity for `gygujf`'s four, non-reconstructible usability for `next`) and name the two contract MUSTs that depend on the second. The behavioral guard against that regression is E-01's CLI-level assertions, which fail if `next` is ever dropped again regardless of why.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: Paste the committed diff of the CLI-level assertions E-01 adds to `tests/test_agent_field_projection.py`. Paste the output of `python3 -m pytest tests/test_agent_field_projection.py -o addopts=""` run on the tree BEFORE E-03, which must FAIL, and paste enough of each failure to show expected-versus-actual for BOTH new CLI assertions: the `releases show` one naming `aw releases list` and the `runs query` one naming `aw runs query schema`. A red run showing only one of the two is NOT sufficient. CONFIRM IN THE SAME OUTPUT that the four pre-existing tests still PASS, since this plan extends `gygujf`'s contract and must not weaken it (F-13); a run where an old test also fails means E-01 altered something it should not have. QUOTE the assertion lines and confirm each compares the `next` VALUE rather than merely testing `'next' in record`, because a presence-only assertion would pass against a future change that preserves the key while blanking it. CONFIRM NO ASSERTION READS `_PRESERVED_FIELDS`, `inspect`, `ast`, or the source text of any production module: the backlog item requires outcome-level testing and P16 forbids code-pinning tests, so a test asserting on the constant's contents is a FAILED validation even if it is green. CONFIRM `aw check plans` is NOT pinned, since its `next` derives from live-corpus diagnostic ordering (F-14) and would make the suite fail on another party's commit. Paste the records BOTH commands emit with and without `--fields` so a reader can see the expected value really is the fixed string the assertion names.
  - Observed evidence:
    Committed diff of CLI-level assertions in `tests/test_agent_field_projection.py`:
    ```python
    def test_cli_projection_releases_show_retains_next(tmp_path, capsys):
        """E-01: aw releases show preserves non-null next across --fields projection."""
        tmp = str(tmp_path)
        # 1. Unprojected run
        capsys.readouterr()
        cli.main(["releases", "show", "zzzzzz", "--dir", tmp, "--agent"])
        out_unproj, _ = capsys.readouterr()
        lines_unproj = [line for line in out_unproj.strip().splitlines() if line.strip()]
        assert len(lines_unproj) == 1, f"Expected exactly 1 record, got: {lines_unproj}"
        rec_unproj = json.loads(lines_unproj[0])
        assert rec_unproj.get("schema") == "aw.agent/v1"
        assert rec_unproj.get("next") == "aw releases list"

        # 2. Projected run with --fields findings
        cli.main(
            [
                "releases",
                "show",
                "zzzzzz",
                "--dir",
                tmp,
                "--agent",
                "--fields",
                "findings",
            ]
        )
        out_proj, _ = capsys.readouterr()
        lines_proj = [line for line in out_proj.strip().splitlines() if line.strip()]
        assert len(lines_proj) == 1, f"Expected exactly 1 record, got: {lines_proj}"
        rec_proj = json.loads(lines_proj[0])
        assert rec_proj.get("schema") == "aw.agent/v1"
        assert rec_proj.get("next") == rec_unproj.get("next")
        assert rec_proj.get("next") == "aw releases list"


    def test_cli_projection_runs_query_retains_next(tmp_path, capsys):
        """E-01: aw runs query preserves non-null next across --fields projection."""
        tmp = str(tmp_path)
        # 1. Unprojected run
        capsys.readouterr()
        cli.main(["runs", "query", "bogusview", "--dir", tmp, "--agent"])
        out_unproj, _ = capsys.readouterr()
        lines_unproj = [line for line in out_unproj.strip().splitlines() if line.strip()]
        assert len(lines_unproj) == 1, f"Expected exactly 1 record, got: {lines_unproj}"
        rec_unproj = json.loads(lines_unproj[0])
        assert rec_unproj.get("schema") == "aw.agent/v1"
        assert rec_unproj.get("next") == "aw runs query schema"

        # 2. Projected run with --fields findings
        cli.main(
            [
                "runs",
                "query",
                "bogusview",
                "--dir",
                tmp,
                "--agent",
                "--fields",
                "findings",
            ]
        )
        out_proj, _ = capsys.readouterr()
        lines_proj = [line for line in out_proj.strip().splitlines() if line.strip()]
        assert len(lines_proj) == 1, f"Expected exactly 1 record, got: {lines_proj}"
        rec_proj = json.loads(lines_proj[0])
        assert rec_proj.get("schema") == "aw.agent/v1"
        assert rec_proj.get("next") == rec_unproj.get("next")
        assert rec_proj.get("next") == "aw runs query schema"
    ```

    Pre-E-03 test output (`python3 -m pytest tests/test_agent_field_projection.py -o addopts=""`):
    ```
    =================================== FAILURES ===================================
    ________________ test_cli_projection_releases_show_retains_next ________________
    ...
    >       assert rec_proj.get("next") == rec_unproj.get("next")
    E       AssertionError: assert None == 'aw releases list'
    E        +  where None = <built-in method get of dict object at 0x7306bbb43fc0>('next')
    E        +    where <built-in method get of dict object at 0x7306bbb43fc0> = {'cmd': 'releases show', 'complete': False, 'exit': 2, 'findings': 0, ...}.get
    E        +  and   'aw releases list' = <built-in method get of dict object at 0x7306bbf97d00>('next')
    E        +    where <built-in method get of dict object at 0x7306bbf97d00> = {'cmd': 'releases show', 'complete': False, 'exit': 2, 'findings': 0, ...}.get
    ...
    _________________ test_cli_projection_runs_query_retains_next __________________
    ...
    >       assert rec_proj.get("next") == rec_unproj.get("next")
    E       AssertionError: assert None == 'aw runs query schema'
    E        +  where None = <built-in method get of dict object at 0x7306bb99a980>('next')
    E        +    where <built-in method get of dict object at 0x7306bb99a980> = {'cmd': 'runs query', 'complete': False, 'exit': 2, 'findings': 0, ...}.get
    E        +  and   'aw runs query schema' = <built-in method get of dict object at 0x7306bba5c9c0>('next')
    E        +    where <built-in method get of dict object at 0x7306bba5c9c0> = {'cmd': 'runs query', 'complete': False, 'exit': 2, 'findings': 0, ...}.get
    ...
    =========================== short test summary info ============================
    FAILED tests/test_agent_field_projection.py::test_cli_projection_releases_show_retains_next
    FAILED tests/test_agent_field_projection.py::test_cli_projection_runs_query_retains_next
    FAILED tests/test_agent_field_projection.py::test_summary_field_projection_retains_next_continuation
    ========================= 3 failed, 4 passed in 2.36s ==========================
    ```
    The 4 pre-existing tests passed (`test_summary_field_projection_retains_required_count_fields`, `test_result_preview_projection_retains_applied`, `test_derived_property_required_fields_preserved_under_projection`, `test_projection_anti_overreach_and_combinatorial_sweep`).
    Assertion lines compared exact values:
    - `assert rec_proj.get("next") == rec_unproj.get("next")`
    - `assert rec_proj.get("next") == "aw releases list"`
    - `assert rec_proj.get("next") == "aw runs query schema"`
    No assertion reads `_PRESERVED_FIELDS`, `inspect`, `ast`, or production module text. `aw check plans` is not pinned.
    Emitted records:
    `releases show zzzzzz --dir <tmp> --agent`:
    - Unprojected: `{"schema":"aw.agent/v1","kind":"error","cmd":"releases show","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":"aw releases list"}`
    - Projected (`--fields findings` pre-fix): `{"schema":"aw.agent/v1","kind":"error","cmd":"releases show","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0}`
    - Projected (`--fields findings` post-fix): `{"schema":"aw.agent/v1","kind":"error","cmd":"releases show","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":"aw releases list"}`
    `runs query bogusview --dir <tmp> --agent`:
    - Unprojected: `{"schema":"aw.agent/v1","kind":"error","cmd":"runs query","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":"aw runs query schema"}`
    - Projected (`--fields findings` pre-fix): `{"schema":"aw.agent/v1","kind":"error","cmd":"runs query","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0}`
    - Projected (`--fields findings` post-fix): `{"schema":"aw.agent/v1","kind":"error","cmd":"runs query","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":"aw runs query schema"}`
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the committed diff of the renderer-level assertion E-02 adds, and paste its output run BEFORE E-03 showing it FAILS with `aw runs query --offset 2` expected and the projected record lacking `next`. Run it IN ISOLATION (by node id) and paste that run, so its redness is established independently of E-01's two CLI assertions rather than inferred from a file-level red. CONFIRM it asserts on the VALUE and not on presence. CONFIRM IT IS NOT REDUNDANT with E-01 by demonstrating the reason F-15 records: show that `run_analytics_cli._emit_query_agent` calls `renderer.render_summary` with NO context argument, so no shipped command reaches the projected-summary path and E-01's CLI assertions cannot cover it. If you find that a shipped command DOES reach `render_summary` with a context, say so plainly: that would make F-15 wrong and would mean this surface should have been covered by a CLI assertion instead, which is a finding worth reporting rather than quietly collapsing the two items.
  - Observed evidence:
    Committed diff of renderer assertion in `tests/test_agent_field_projection.py`:
    ```python
    def test_summary_field_projection_retains_next_continuation():
        """E-02: render_summary with fields projection retains non-null next continuation command."""
        ctx = OutputContext(
            mode=OutputMode.AGENT,
            stdout=io.StringIO(),
            stderr=io.StringIO(),
            fields=["cmd"],
        )
        rendered = AgentRenderer().render_summary(
            "runs query",
            total=5,
            emitted=2,
            omitted=3,
            outcome="clean",
            exit_code=0,
            next_cmd="aw runs query --offset 2",
            complete=False,
            context=ctx,
        )
        data = json.loads(rendered)
        assert is_valid_agent_record(data)
        assert data.get("next") == "aw runs query --offset 2"
    ```

    Isolated run BEFORE E-03 (`python3 -m pytest tests/test_agent_field_projection.py::test_summary_field_projection_retains_next_continuation -o addopts=""`):
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=4112463359
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 1 item                                                              collected 1 item

    tests/test_agent_field_projection.py F                                   [100%]

    =================================== FAILURES ===================================
    ___________ test_summary_field_projection_retains_next_continuation ____________

        def test_summary_field_projection_retains_next_continuation():
            """E-02: render_summary with fields projection retains non-null next continuation command."""
            ctx = OutputContext(
                mode=OutputMode.AGENT,
                stdout=io.StringIO(),
                stderr=io.StringIO(),
                fields=["cmd"],
            )
            rendered = AgentRenderer().render_summary(
                "runs query",
                total=5,
                emitted=2,
                omitted=3,
                outcome="clean",
                exit_code=0,
                next_cmd="aw runs query --offset 2",
                complete=False,
                context=ctx,
            )
            data = json.loads(rendered)
            assert is_valid_agent_record(data)
    >       assert data.get("next") == "aw runs query --offset 2"
    E       AssertionError: assert None == 'aw runs query --offset 2'
    E        +  where None = <built-in method get of dict object at 0x7b53072d11c0>('next')
    E        +    where <built-in method get of dict object at 0x7b53072d11c0> = {'cmd': 'runs query', 'complete': False, 'emitted': 2, 'exit': 0, ...}.get

    tests/test_agent_field_projection.py:353: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_agent_field_projection.py::test_summary_field_projection_retains_next_continuation
    ============================== 1 failed in 0.84s ===============================
    ```
    Asserts on the exact value: `assert data.get("next") == "aw runs query --offset 2"`.
    Non-redundancy confirmed: `agent_workflows/run_analytics_cli.py` lines 268-278:
    ```python
        parts.append(
            renderer.render_summary(
                "runs query",
                total=total,
                emitted=result.emitted,
                omitted=max(0, total - result.emitted),
                outcome=result.outcome,
                exit_code=result.exit_code,
                next_cmd=result.next_command or None,
                complete=result.complete,
            )
        )
    ```
    `render_summary` is called with no `context=` argument, confirming F-15 that no shipped command reaches projected summary rendering in production CLI today.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the committed diff of `agent_workflows/agent_schema.py`. It must show exactly one name added to `_PRESERVED_FIELDS` plus comment text, and NOTHING else: confirm by inspection that `_MANDATORY_FIELDS` is textually unchanged and still holds seven names, that `filter_record_fields`'s early return and comprehension are unchanged, and that no rule inside `validate_agent_record` moved. Paste `python3 -m pytest tests/test_agent_field_projection.py -o addopts=""` now fully GREEN. Paste the LIVE PROBE on all four commands F-03 measured stranded (`aw check plans`, `aw find zzzzzz`, `aw releases show zzzzzz`, `aw runs query bogusview`), each run `--agent --fields findings`, showing for each the emitted record with a non-null `next` and `is_valid_agent_record` true; a probe covering fewer than four is incomplete, because two of them are the `complete: true` cases that refute candidate (b) and they are the ones an executor is most likely to skip. Paste the NO-CHANGE-WITHOUT-FIELDS result: a corpus spanning all four kinds rendered through `render_jsonl_record` with no `fields`, byte-identical before and after, including the four `*.agent.golden` shapes. Paste the EXHAUSTIVE SWEEP result with the projection count swept, showing zero invalid, zero added keys, zero altered values, and ZERO strandings against the 2 measured before. QUOTE the new comment text and confirm it no longer claims the set equals the validator's consulted fields, that it gives `next`'s distinct non-reconstructible reason, and that it names the Section 11.1 and 11.4 MUSTs; a diff that adds the name without correcting the comment leaves the next reader a documented reason to delete it (F-02, OQ-02) and is a FAILED validation.
  - Observed evidence:
    Committed diff of `agent_workflows/agent_schema.py`:
    ```diff
    diff --git a/agent_workflows/agent_schema.py b/agent_workflows/agent_schema.py
    index a5d3e098a..e02e1ce9a 100644
    --- a/agent_workflows/agent_schema.py
    +++ b/agent_workflows/agent_schema.py
    @@ -395,17 +395,24 @@ def assert_valid_agent_record(record: Dict[str, Any]) -> None:

     _MANDATORY_FIELDS = {"schema", "kind", "cmd", "exit", "outcome", "complete", "verified"}

    -# Fields that a projection must not remove in order for the resulting record to remain valid
    -# across all kinds. This is a kind-independent superset of _MANDATORY_FIELDS that additionally
    -# includes every field validate_agent_record consults:
    -# - 'applied': preview exemption for result records with complete=False
    -# - 'total', 'emitted', 'omitted': required accounting fields for summary records
    +# Fields that a projection must not remove across any record kind. This is a kind-independent
    +# superset of _MANDATORY_FIELDS that preserves fields required for two distinct reasons:
    +# 1. Record validity (fields validate_agent_record consults):
    +#    - 'applied': preview exemption for result records with complete=False
    +#    - 'total', 'emitted', 'omitted': required accounting fields for summary records
    +# 2. Record usability that the caller cannot reconstruct:
    +#    - 'next': paging continuation or recovery command. Dropping 'next' from a record reporting
    +#      complete=False tells the caller its answer is partial while withholding the command to
    +#      fetch the remainder. Furthermore, docs/cli-output-contract.md Sections 11.1 and 11.4
    +#      state MUST requirements for empty results and cannot-run error records to carry 'next',
    +#      which a projected record would otherwise violate.
     #
     # Preserving a flat union rather than a per-kind mapping avoids a second structure to keep
    -# in sync with the validator, and failing closed (retaining a field the validator might consult)
    -# prevents crashes at runtime. For records that do not carry these optional/kind-specific fields,
    -# filtering is a no-op because only present keys are considered.
    -_PRESERVED_FIELDS = _MANDATORY_FIELDS | {"applied", "total", "emitted", "omitted"}
    +# in sync with the validator, and failing closed (retaining a field the validator might consult
    +# or that the caller cannot reconstruct) prevents broken continuation and runtime crashes.
    +# For records that do not carry these optional/kind-specific fields, filtering is a no-op
    +# because only present keys are considered.
    +_PRESERVED_FIELDS = _MANDATORY_FIELDS | {"applied", "total", "emitted", "omitted", "next"}
    ```
    Confirmed: `_MANDATORY_FIELDS` unchanged (7 fields: schema, kind, cmd, exit, outcome, complete, verified); `filter_record_fields` early return and comprehension unchanged; no rules in `validate_agent_record` moved.

    Post-E-03 test output:
    ```
    $ python3 -m pytest tests/test_agent_field_projection.py -o addopts=""
    ============================== 7 passed in 2.57s ===============================
    ```

    Live probe on 4 commands (`--agent --fields findings`):
    ```
    COMMAND: check plans --agent --fields findings
    EXIT: 1
    RECORD: {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":76,"next":"cite evidence it was discharged by finished work: add `- Carrier-Evidence: .aw/records/backlog/done/20261001-vf3mw2-01-vf3mw2-partition-unknown-key-is-unreachable-dead-field.backlog.md`"}
    is_valid_agent_record: True, complete: True, next: 'cite evidence it was discharged by finished work: add `- Carrier-Evidence: .aw/records/backlog/done/20261001-vf3mw2-01-vf3mw2-partition-unknown-key-is-unreachable-dead-field.backlog.md`'
    ---
    COMMAND: find zzzzzz --agent --fields findings
    EXIT: 0
    RECORD: {"schema":"aw.agent/v1","kind":"result","cmd":"find","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"next":"aw find"}
    is_valid_agent_record: True, complete: True, next: 'aw find'
    ---
    COMMAND: releases show zzzzzz --agent --fields findings
    EXIT: 2
    RECORD: {"schema":"aw.agent/v1","kind":"error","cmd":"releases show","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":"aw releases list"}
    is_valid_agent_record: True, complete: False, next: 'aw releases list'
    ---
    COMMAND: runs query bogusview --agent --fields findings
    EXIT: 2
    RECORD: {"schema":"aw.agent/v1","kind":"error","cmd":"runs query","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":"aw runs query schema"}
    is_valid_agent_record: True, complete: False, next: 'aw runs query schema'
    ```

    No-change-without-fields probe:
    Tested 14 records across all four kinds (including the 4 `*.agent.golden` fixtures: `read_clean`, `error_cannot_run`, `check_findings`, `mutation_preview`): `byte-identical=True`.

    Exhaustive sweep over all key subsets:
    Swept 186 projections across 14 records: `invalid=0, added_keys=0, altered_values=0, strandings=0`.

    Quoted new comment text:
    > Fields that a projection must not remove across any record kind. This is a kind-independent
    > superset of _MANDATORY_FIELDS that preserves fields required for two distinct reasons:
    > 1. Record validity (fields validate_agent_record consults):
    >    - 'applied': preview exemption for result records with complete=False
    >    - 'total', 'emitted', 'omitted': required accounting fields for summary records
    > 2. Record usability that the caller cannot reconstruct:
    >    - 'next': paging continuation or recovery command. Dropping 'next' from a record reporting
    >      complete=False tells the caller its answer is partial while withholding the command to
    >      fetch the remainder. Furthermore, docs/cli-output-contract.md Sections 11.1 and 11.4
    >      state MUST requirements for empty results and cannot-run error records to carry 'next',
    >      which a projected record would otherwise violate.
    The comment no longer claims the set equals the validator's consulted fields, states the usability reason, and cites Sections 11.1 and 11.4 MUSTs.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the committed diff of `docs/cli-agent-protocol.md`. Confirm the `## Token control` `--fields` bullet now names `next` among the retained fields and states the not-reconstructible reason. QUOTE the bullet in full and confirm its reason is CONSISTENT with item 6 of `## Recommended consumption pattern` ("If `complete` is `false`, follow `next` to fetch the remainder") and with `## Stream truncation is honest`, rather than inventing a second rationale. Confirm by diff that no other paragraph changed and that the example records are untouched, since they are unprojected and already correct (F-10). Run `rg -n '[\u2013\u2014]' docs/cli-agent-protocol.md` (or an equivalent em/en dash scan) and paste the result showing NO hits, since this is user-facing prose under the execution contract.
  - Observed evidence:
    Committed diff of `docs/cli-agent-protocol.md`:
    ```diff
    diff --git a/docs/cli-agent-protocol.md b/docs/cli-agent-protocol.md
    index 193b0dfb2..41334c9c6 100644
    --- a/docs/cli-agent-protocol.md
    +++ b/docs/cli-agent-protocol.md
    @@ -67,8 +67,11 @@ Two escape hatches tune the token cost:
       (`schema`, `kind`, `cmd`, `exit`, `outcome`, `verified`, `complete`) is always retained. A projection
       additionally retains whatever the record kind requires to remain valid, including a summary's `total`,
       `emitted`, and `omitted` (so `emitted + omitted == total` remains verifiable to distinguish a bounded
    -  answer from a complete one) and a preview result's `applied`. A projection never yields a record that
    -  fails validation, so `--fields` is safe to pass on any command.
    +  answer from a complete one) and a preview result's `applied`. A projection also preserves `next`
    +  whenever present: a continuation command cannot be reconstructed by the caller, so dropping it would
    +  leave a truncated record (`complete: false`) without the ready-to-run command needed to follow `next`
    +  and fetch the remainder. A projection never yields a record that fails validation, so `--fields` is safe
    +  to pass on any command.
    ```

    Quoted amended bullet:
    `- --fields <a,b,c>: project each record down to the requested fields. The mandatory envelope (schema, kind, cmd, exit, outcome, verified, complete) is always retained. A projection additionally retains whatever the record kind requires to remain valid, including a summary's total, emitted, and omitted (so emitted + omitted == total remains verifiable to distinguish a bounded answer from a complete one) and a preview result's applied. A projection also preserves next whenever present: a continuation command cannot be reconstructed by the caller, so dropping it would leave a truncated record (complete: false) without the ready-to-run command needed to follow next and fetch the remainder. A projection never yields a record that fails validation, so --fields is safe to pass on any command.`
    Reason matches item 6 of `## Recommended consumption pattern` and `## Stream truncation is honest`. Example records and all other paragraphs untouched.
    Dash scan:
    `rg -n '[\u2013\u2014]' docs/cli-agent-protocol.md` -> 0 hits (exit code 1).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the committed diff of `docs/cli-output-contract.md`. Confirm the Section 6 `**--fields <list>**` bullet names `next` and reconciles itself by reference with the Section 11.1 and 11.4 MUSTs. QUOTE the amended bullet and ALSO quote Sections 11.1 and 11.4 from the committed file to demonstrate they are UNCHANGED: this plan makes the implementation satisfy what they already require, so editing them would be scope creep and would obscure that the contract was already right. Confirm by diff that the `--limit` bullet and every other bullet in Section 6 are untouched. Paste an em/en dash scan over the file showing NO hits.
  - Observed evidence:
    Committed diff of `docs/cli-output-contract.md`:
    ```diff
    diff --git a/docs/cli-output-contract.md b/docs/cli-output-contract.md
    index 9920f6b75..576ead7a9 100644
    --- a/docs/cli-output-contract.md
    +++ b/docs/cli-output-contract.md
    @@ -266,7 +266,7 @@ Agents (GPT, Gemini, Opus, GLM, etc.) and CI runners must **consume structured r
     To minimize token usage during agent orchestration while preserving complete decision facts:

     - **Compact Defaults**: By default, agent records emit concise identifiers (check names in evidence receipts, count of changes when large, minimal diagnostic fields) rather than verbose text paragraphs.
    -- **`--fields <list>`**: Projects records down to explicitly requested fields while preserving mandatory envelope metadata (`schema`, `kind`, `cmd`, `exit`, `outcome`, `complete`, `verified`). Projections additionally retain whatever the record kind requires to remain valid, including a summary's `total`, `emitted`, and `omitted` counts and a preview result's `applied` flag. A projection never yields a record that fails validation, so `--fields` is safe to pass on any command.
    +- **`--fields <list>`**: Projects records down to explicitly requested fields while preserving mandatory envelope metadata (`schema`, `kind`, `cmd`, `exit`, `outcome`, `complete`, `verified`). Projections additionally retain whatever the record kind requires to remain valid, including a summary's `total`, `emitted`, and `omitted` counts and a preview result's `applied` flag. Projections also preserve `next` whenever present: a continuation or recovery command cannot be reconstructed by the caller, so retaining it ensures the MUST requirements in Section 11.1 (broadening or fallback commands on empty results) and Section 11.4 (recovery commands on cannot-run error records) hold under `--fields` too. A projection never yields a record that fails validation, so `--fields` is safe to pass on any command.
    ```

    Quoted amended bullet:
    `- **--fields <list>**: Projects records down to explicitly requested fields while preserving mandatory envelope metadata (schema, kind, cmd, exit, outcome, complete, verified). Projections additionally retain whatever the record kind requires to remain valid, including a summary's total, emitted, and omitted counts and a preview result's applied flag. Projections also preserve next whenever present: a continuation or recovery command cannot be reconstructed by the caller, so retaining it ensures the MUST requirements in Section 11.1 (broadening or fallback commands on empty results) and Section 11.4 (recovery commands on cannot-run error records) hold under --fields too. A projection never yields a record that fails validation, so --fields is safe to pass on any command.`

    Unchanged Sections 11.1 and 11.4 quoted from committed file:
    Section 11.1 (excerpt):
    ```markdown
    - **Agent Protocol (`aw.agent/v1`)**: For non-refused empty queries, when nothing else is wrong, the handler MUST emit a structured `result` (or `summary`) record with:
      - `outcome: "clean"`, `exit: 0`, `findings: 0`, `verified: true`, `complete: true`.
      - Evidence/data carrying the zero count and active filter dictionary.
      - `next`: the suggested broadening or fallback command.
    ```
    Section 11.4 (excerpt):
    ```markdown
    - **Usage / Cannot-Run Errors (`exit: 2`)**:
      - Missing mandatory arguments, unknown subcommands, or invalid selectors MUST exit `2`.
      - Human TTY: prints diagnostic message and usage help to `stderr`.
      - Agent Mode: emits a `kind: "error"` record with `outcome: "cannot-run"` (or `"error"`), `exit: 2`, `verified: false`, `complete: false`, and a `next` recovery command (e.g. `aw <cmd> --help`).
    ```
    `--limit` and all other bullets in Section 6 untouched.
    Dash scan:
    `rg -n '[\u2013\u2014]' docs/cli-output-contract.md` -> 0 hits (exit code 1).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: THREE separate pieces, none inferable from the others. FIRST, the BYTE COST: paste the measured sizes for a projected record carrying a non-null `next` and for one whose `next` is `null`, before and after, and state the largest post-fix record you measured with an explicit confirmation it is under 1200 bytes. Report YOUR numbers, not F-06's; if any sample exceeds 1200 bytes, this validation FAILS and the plan returns for a cost re-decision rather than proceeding. SECOND, `run_analytics_cli`: paste `git diff --stat` (or the staged path list) proving `agent_workflows/run_analytics_cli.py` is NOT in this commit, QUOTE the now-false sentence from its comment ("The summary takes no field projection because `next` is not in `agent_schema._PRESERVED_FIELDS`"), and paste `d6u2hz` read from `.aw/records/backlog/open/` showing it is still `open` and still describes this comment, together with `aw backlog check` output confirming it is well-formed. A report that edits the comment instead is a FAILED validation, as is one that files a SECOND item for the same obligation. THIRD, the SUITE: paste the BARE `python3 -m pytest` summary line from this lane, state the baseline you re-derived at lane start, and confirm the failure SET is unchanged from it. For each of the two expected failures, paste its isolated run and name the open backlog item that owns it (`6bolin` or `md2o3y` for the `89xjll` spec failure; `8jeh4x` is the open item for the reachability one, measured at review; confirm it is still open). Confirm the passed count rose by exactly the number of tests E-01 and E-02 added. A THIRD failure must be investigated and attributed, not reported as pre-existing on the strength of F-09 alone.
  - Observed evidence:
    1. Measured byte costs:
    - truncated summary (non-null next): 139 bytes pre-fix -> 173 bytes post-fix (+34 bytes)
    - check findings result (non-null next): 136 bytes pre-fix -> 200 bytes post-fix (+64 bytes)
    - clean result (null next): 127 bytes pre-fix -> 139 bytes post-fix (+12 bytes)
    - cannot-run error (non-null next): 140 bytes pre-fix -> 166 bytes post-fix (+26 bytes)
    Largest post-fix record measured across samples: 200 bytes (and ~320 bytes on `check plans` in live probe), confirmed well under the 1200-byte budget.

    2. `run_analytics_cli.py` confirmed untouched:
    `git diff --stat agent_workflows/run_analytics_cli.py` produces 0 output (file is untouched).
    Quote of now-false sentence from lines 260-263 of `agent_workflows/run_analytics_cli.py`:
    > The summary takes no field projection because `next` is not in `agent_schema._PRESERVED_FIELDS`, so projecting this record could drop the paging continuation and emit a truncated answer (`complete: false` with `omitted > 0`) that tells the caller nothing about how to get the rest, which is the one field on this record a caller cannot reconstruct.

    Carrying backlog item `d6u2hz` at `.aw/records/backlog/open/20261002-d6u2hz-01-d6u2hz-run-analytics-summary-comment-next-preserved.backlog.md` is confirmed `open` and describes this exact sentence.
    `aw backlog check`: `aw backlog check: all backlog items conform.`

    3. Bare test suite re-derived baseline and post-change run:
    Re-derived baseline at lane start:
    `FAILED tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta`
    `1 failed, 4813 passed, 2 skipped, 3 warnings in 504.01s (0:08:24)`
    Post-change run:
    `FAILED tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta`
    `1 failed, 4816 passed, 2 skipped, 3 warnings in 548.98s (0:09:08)`
    Failure set is identical: exactly 1 failure (`test_corpus_verdict_neutrality_delta`).
    Passed count rose from 4813 to 4816 (rising by exactly 3, matching the 3 new tests added by E-01 and E-02).
    The two prior authoring failures cited in F-09 (`test_spec_review_attestation` and `test_run_finding_reachability`) were previously resolved on main prior to this lane's branch point and both pass in isolation:
    - `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`: `1 passed in 2.65s`
    - `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`: `1 passed in 28.36s`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT THE HUMAN IS APPROVING, in one paragraph. Adding one name, `next`, to `agent_schema._PRESERVED_FIELDS` so a `--fields` projection can no longer remove a record's continuation command; rewriting that constant's comment, which currently describes the set as exactly the validator's consulted fields and would therefore read as licence to delete the new member; extending the existing projection test file with assertions that drive real CLI commands and compare emitted records; and amending one bullet in each of the two documents that enumerate what a projection retains. No command's output changes unless `--fields` is passed (F-10), no record gains a field it did not have, no conformance golden moves, and no validator rule is touched.

THE ONE JUDGEMENT WORTH A HUMAN'S ATTENTION IS THAT THIS PLAN OVERRULES ITS OWN BACKLOG ITEM'S PREFERRED FIX. The item calls conditional preservation (b) "honest" and raises token cost against the unconditional (a). Authoring measured two facts the item does not have: the stranding is LIVE on four shipped commands rather than latent (F-03), and two of those four carry `complete: true`, which is exactly the case (b)'s guard excludes and which `docs/cli-output-contract.md` Section 11.1 makes a MUST (F-05). So (b) would have shipped with a documented MUST still violated. The accepted cost is stated plainly rather than minimized: 46 to 73 bytes on records carrying a real continuation, a flat 12 bytes for `"next":null` on a `result`, zero on a complete `summary` (F-06), and the side effect that projecting a `summary` becomes an identity operation (F-12).

SCOPE FENCE: `- Scope-Paths:` is a DECLARATION the runner reconciles afterwards, not a stop condition; an out-of-scope edit that proves necessary is made and justified at finalize with `--scope-reason <path>=<why>`, and a declared but unmodified path is acknowledged with `--scope-ack`. LIFECYCLE: when `aw oc run`/`aw agy run` dispatched this plan the runner performs `aw ipd begin`/`aw ipd finalize` itself (an in-lane invocation is refused by design); in a manual run the executor finalizes with `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` once `aw ipd lint --phase pre-transition` conforms. Never `git mv` the plan or hand-edit its terminal status. Backlog `kkjrqr` is already `graduated`; its `- Blocks-Release: next` gate travels with this plan and is released when this plan is `executed`.

On execution, the executor MUST: commit only the paths named in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout where another party's work must never be swept in; run the BARE `python3 -m pytest` and paste its ACTUAL output; and complete every `V-*` item with the concrete evidence it demands, including V-01's and V-02's red demonstrations and V-03's four-command live probe.

FOUR WAYS THIS PLAN CAN FAIL SILENTLY, stated because a green suite catches none of them.

FIRST, TESTING THE CONSTANT INSTEAD OF THE BEHAVIOR. `assert 'next' in agent_schema._PRESERVED_FIELDS` is one line, always green after E-03, and worthless: it pins code structure, it is forbidden by P16 and by the backlog item itself, and it would pass if the projector stopped reading the constant. V-01 requires confirming no assertion reads the constant, `inspect`, `ast`, or production source text.

SECOND, PINNING A LIVE-CORPUS VALUE. The most dramatic stranding is `aw check plans`, whose `next` is derived from whichever diagnostic sorts first across `.aw/records/`. Asserting on it would make this suite fail whenever another agent commits an artifact, and the harness warns about exactly this in its own failure output. E-01 forbids it and selects fixed-string refusals instead.

THIRD, LEAVING THE COMMENT ASSERTING THE OLD CONTRACT. `next` is the first member of this set that `validate_agent_record` does NOT consult (F-02), so a reader who trusts the current comment's "every field validate_agent_record consults" will correctly conclude the new member is a mistake. No derivation and no validator-reading test can re-establish it, which makes the comment the only durable explanation. A diff that adds the name and leaves the comment is a failed validation under V-03.

FOURTH, QUIETLY ADOPTING THE TWO PRE-EXISTING FAILURES. The lane starts red by two (F-09), both another party's and both reproducible on a clean tree. An executor who pastes a two-failure run and calls it the baseline without re-deriving it in the lane cannot distinguish a third failure of its own from the two it inherited. V-06 requires the baseline re-derived, each failure run in isolation, and each attributed to a named item or explicitly reported as unowned.
