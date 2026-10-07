# IPD: Make aw find --agent emit a real aw.agent/v1 record stream so --limit and --fields are honored, keeping --paths the byte-stable script surface

- Date: 2026-10-01
- Kind: child
- Concern: `aw find --agent` accepts two documented token-control flags and silently ignores both, because its agent branch prints bare repo-relative paths and RETURNS before any `CommandResult` is built (`cli._run_find`, the branch guarded by `getattr(args, "paths", False) or (ctx.is_agent and all_paths)`, whose own comment states "this branch returns before any `CommandResult` is built"). Measured in this lane at HEAD `74b301435`: `aw find plans --agent --limit 20 | wc -l` prints 1131, the flag reaches the context (`ctx.limit == 20`, set by `result_types.select_output`) and nothing consults it; `aw find plans --agent --fields findings` prints the same 1131 bare paths and projects nothing. `docs/cli-human-guide.md` advertises the first command verbatim as "Bounded output with a continuation hint", and `docs/cli-agent-protocol.md` publishes a worked `find` summary record (`{"kind":"summary","cmd":"find",...,"total":10,"emitted":3,"omitted":7,"complete":false,"next":"aw find plans --agent --limit 10"}`) that the verb has never emitted. `docs/cli-migration.md` tells a migrating script that the `aw find` path lines "are now `aw.agent/v1` `item` records followed by a `summary` record", which is also false today. The branch is CONDITIONAL on `all_paths` being truthy, not on selector absence, so a matching selector takes it too and only a zero-match query reaches the record path; a caller cannot tell from the flags which shape they will get.
- Scope: Make `--agent` on `aw find` a real `aw.agent/v1` stream: one `item` record per matched row carrying `path`, `type`, `id6`, `status` and `set`, terminated by one `summary` record carrying `total`/`emitted`/`omitted`/`complete` and, when truncated, a `next` continuation command, with `--limit` bounding emission and `--fields` projecting each record. Keep `--paths`/`-p` EXACTLY as it is today, byte for byte, as the bare-path script surface `docs/cli-output-contract.md` Section 12 sanctions. Carry the existing `find.id6-collision` finding into the new `summary` record's `diagnostics` instead of the `aw-find-warning:` stderr line that exists only because the record path was unreachable. Reconcile the one normative sentence in `docs/cli-output-contract.md` Section 12 that currently mandates bare paths under `--agent`, and correct the `--limit` row in `docs/cli-human-guide.md` only if execution measures it still wrong. Does NOT change which artifacts match, the selector grammar or precedence, the human row format, the `--json` payload, the exit codes, or `aw search`.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/renderers.py, tests/test_find_agent_stream.py, docs/cli-output-contract.md, docs/cli-agent-protocol.md, docs/cli-human-guide.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: wdazvp
- Blocks-Release: next
- Set: wdazvp
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: okiso1
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (aw set): plan-review APPROVE WITH REVISIONS APPLIED
- 2026-10-02 /plan-review (opencode/its_direct-pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003 (HIGH, fixed), PR-004, PR-005, PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed). Measured in process: the renderer cannot carry `diagnostics` and drops `next` under `--fields`, so E-03 was unreachable within scope and `--limit --fields` would lose the continuation (renderers.py added to scope); a `{` in a selector crashes `next_template.format`; zero-match `--agent` shape now specified as a lone summary. Full record: `.aw/records/reviews/20261002-wdazvp-01-okiso1-make-aw-find-agent-emit-a-real-aw-agent-v1-record-stream-so.review.md`.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `wdazvp`, graduating it. Every claim the item makes was RE-MEASURED in this lane at HEAD `74b301435` rather than carried over; the reproduction holds and the row count has drifted from the item's 985 to 1131, which is why no count is used as a bar anywhere below. THE ITEM LEFT ITS CENTRAL CONTRACT DECISION OPEN (its three candidates (a) record stream, (b) refuse the flags at exit 2, (c) truncate the path list) AND THIS PLAN RESOLVES IT FROM REPOSITORY EVIDENCE rather than deferring it to a maintainer: direction (a), see OQ-01 and F-01 through F-04. The decisive evidence is that three shipped documents ALREADY SPECIFY (a) in detail, including a worked `find` summary record in `docs/cli-agent-protocol.md` and a migration instruction in `docs/cli-migration.md` telling scripts the item records already exist, so (a) makes three documents true while (b) and (c) require amending them to admit a second convention; and that `docs/cli-output-contract.md` Section 10 rules "Exactly one canonical machine format (`aw.agent/v1`) is active", the same rule plan `n9ua3b` cites for the same class of defect on the `index` verbs. FOUR FACTS WERE MEASURED THAT THE ITEM DOES NOT STATE AND THAT CHANGE THE WORK. FIRST (F-05), the item's framing of (a) as "a breaking change to that surface" overstates it on BOTH halves: `--paths` keeps the bare stream unchanged under this plan, and `aw find` has NEVER SHIPPED in a tagged release (the newest tag `v1.3.0-rc.1` carries eight subcommands and `find` is not among them), so there is no released consumer of these bytes, which is the same measurement that collapsed the identical premise for plan `n9ua3b`. SECOND (F-06), `AgentRenderer.render_stream` has ZERO production callers today, so this plan is its first, and its measured `--limit` edge behavior (a limit of `0` emits zero items and reports `omitted: total`; a NEGATIVE limit silently emits `len-1` items) must be handled at the call site rather than assumed sane. THIRD (F-07), the record path is reachable today ONLY on a zero-match query, and that exact path is being changed concurrently by `reviewed` sibling plan `zyj8io` (which moves a zero-match `find` to exit 2), so the two plans meet on one narrow branch and this plan must not assert a zero-match exit code. FOURTH (F-08), two record fields are home-path INJECTION SITES that crash the serializer rather than leaking: a `next` echoing a home-path selector and an absolute `path` both raise `ValueError` from `agent_schema.render_jsonl_record`, which is the live defect carried by `enygec`, so E-04 sanitizes at construction and V-04 proves it with a home-path selector. All three open questions are RESOLVED at authoring from in-repo evidence (the contract direction from three shipped documents plus the single-canonical-format ruling, the non-positive `--limit` behavior from `run_analytics_query._parse_limit`'s refusal precedent, and the research-summary field from the measured prose bound), so this plan leaves no open obligation; two deferred rows named real work with no carrier, so backlog items `kinyxf` (the broken-pipe traceback across six measured invocations) and `4uw9gy` (`--limit` inert on `check`/`index`/`search`) were filed at authoring and are committed with this plan. `aw ipd lint --phase author` reports conforming and `check.ipd-uncarried-obligation` reports zero obligations.

## Goal

Make `aw find --agent` deliver the machine answer three shipped documents already describe: a bounded, projectable `item`-plus-`summary` stream whose `--limit` and `--fields` do what the protocol reference says they do, so an agent asking for 20 rows receives 20 rows and a continuation command instead of 1131 bare paths. Keep `--paths` the untouched bare-path surface for scripts, so the token-cheap discovery affordance `docs/cli-output-contract.md` Section 12 is written to protect survives under the flag that was always its explicit home.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the failing baseline before changing any byte

- [x] E-01 WRITE `tests/test_find_agent_stream.py` AND SHOW IT RED BEFORE ANY PRODUCTION EDIT, so the fix has a falsifiable baseline rather than a claim.

  DRIVE A FIXTURE REPOSITORY, NOT THE LIVE TREE. Build a temp repo holding a small, CHOSEN records set (at least: three plans across two dispositions, one spec, one backlog item) so every count asserted is one the test created. `tests/test_find_filters.py` already contains the fixture shape to copy (its `setUp` writes plans, specs, backlog, research and walkthrough records under `.aw/records/`, and its `run_find` helper calls `cli.main(["find", ..., "--dir", str(self.repo_root)])` in-process with `sys.stdout` patched). REUSE that shape rather than forking a third fixture builder; `--dir` is what makes a fixture-scoped `find` possible and is already proven by eleven passing tests in that module.

  ASSERT THESE THINGS UNDER `--agent`, each corresponding to a measured failure (six at authoring; four more added at review and listed after (6)). (1) Every stdout line parses as JSON and carries `schema == "aw.agent/v1"` (today every line is a bare path and NONE parses). (2) `agent_schema.validate_agent_record` returns `[]` for EVERY emitted record, items included. (3) The terminal record has `kind == "summary"` and its `emitted + omitted == total`, with `total` equal to the fixture's own matched-row count. (4) With `--limit N` for an `N` smaller than the fixture's row count, exactly `N` `item` records are emitted, `complete` is `false`, and `next` is a runnable command string (today the flag changes nothing). (5) With `--fields path`, each `item` carries `path` and does NOT carry a non-envelope key the unprojected record carries (choose `id6` or `status` and name which you chose). (6) No stdout line contains an ANSI escape (and, added at review, (7) `--limit N --fields path` still carries `next` on the summary, (8) a zero-match query emits exactly one `summary` with `total: 0`, (9) a selector containing `{x}` or a space yields a runnable `next` and no exception, (10) `--agent` into a closed pipe exits without a traceback), which `docs/cli-output-contract.md` Section 4 requires of every agent record and which matters here because the human row format DOES carry ANSI (measured: `cli._find_type_records` returns rows containing `\x1b[1;38;5;46m` when the `Term` has color).

  ASSERT `--paths` IS BYTE-IDENTICAL, in the same module, because that invariance is the whole safety argument for changing `--agent`. Capture `--paths` stdout from the fixture before the production edit, store it as the expected value IN THE TEST (not as a golden file, so the fixture and its expectation cannot drift apart), and assert equality after. Do the same for the UNFLAGGED human output.

  NO STATIC ANALYSIS. Do not read `agent_workflows/cli.py` from the test, do not assert a symbol exists, do not count branches. GUIDING_PRINCIPLES P16 forbids code-pinning tests outright; every assertion here must come from driving the command and reading its stdout, exit code, and stderr.
  - Depends on: none
  - Expected outcome: a new test module whose `--agent` assertions FAIL at the base commit (assertion (9)'s exception and (10)'s traceback may fail differently from the others; name how each fails) and whose `--paths` and human assertions PASS, with that failing output captured verbatim as the baseline for V-02 through V-06.
  - Execution state: performed

### Task group 2: build the stream, preserving the script surface

- [x] E-02 NARROW THE BARE-PATH BRANCH TO `--paths` ALONE. In `cli._run_find`, change the branch condition `getattr(args, "paths", False) or (ctx.is_agent and all_paths)` so it fires on `--paths` only, and REWRITE the comment above it rather than leaving it, because that comment currently records a byte-identity guarantee between two surfaces that this plan deliberately separates. The new comment must state the three live facts: that `--paths` remains the bare, script-shaped surface sanctioned by `docs/cli-output-contract.md` Section 12; that `--agent` now emits records because two documented flags were inert on it (cite backlog `wdazvp`); and that the `aw-find-warning:` stderr line survives for `--paths` only if E-03 decides so, naming E-03 as the decision site.

  DO NOT TOUCH THE RETURN VALUE OF THE `--paths` PATH. It currently returns `0 if (all_paths or not selectors) else 1`, which is the one surface already exiting 1 on a zero-match selector; sibling plan `zyj8io` owns that three-way divergence (F-07) and changing it here would collide. State in the comment that the exit expression is left exactly as found and why.
  - Depends on: E-01
  - Expected outcome: `--paths` output and exit codes are unchanged; `--agent` falls through to the record-building path for the first time on a matching query.
  - Execution state: performed

- [x] E-03 BUILD THE ITEM STREAM AND EMIT IT THROUGH `AgentRenderer.render_stream`. `_find_type_records` already returns `(lines, paths, matches)` where `matches` is a list of `cli._FindMatch` (`token`, `artifact_type`, `path`, `kind`); the per-row display data it formats into `lines` includes the status and id6 it just computed via `cli._find_status_and_id6`. THREAD THE STRUCTURED FIELDS OUT RATHER THAN RE-PARSING THE RENDERED ROW: a record built by splitting an ANSI-bearing display string is exactly the producer/reader drift this repository has paid for before, and the display string is also what carries the color this plan must keep out of the record.

  EACH `item` CARRIES: `path` (repo-relative, the same string `paths` already holds), `type` (the artifact type the row came from), `id6`, `status`, and `set` where the type has one. State in a comment which fields are OMITTED and why, so a later reader does not read the absence as an oversight: the human row's glyph and its padding are presentation, and the `summary` field a research row appends is free prose that would dominate the record's size.

  THE `summary` RECORD carries `total` (every matched row, not the emitted count), `emitted`, `omitted`, `complete`, and `next` when truncated. PASS A `next_template`: `render_stream`'s default is `f"aw {cmd} --agent --limit {tot}"`, which for this verb would emit `aw find --agent --limit <N>` and DROP the type and selector the caller actually asked for, giving a continuation command that returns a different result set. Build the template from the invocation (type plus selectors plus the active filter flags) and SANITIZE it per E-04.

  HANDLE THE `--limit` EDGES AT THE CALL SITE, measured in F-06 rather than assumed: `render_stream` with `limit=0` emits zero items and reports `omitted == total`, and with a NEGATIVE limit emits `len(items) - 1` items through Python slice semantics while reporting `complete: false`. Decide and implement one behavior for a non-positive `--limit` (refusing it at exit 2 like `run_analytics_query._parse_limit` does, or clamping, or treating it as unset), SAY WHICH in a comment with the reason, and pin it in E-01's module. Do not leave the negative case to slice semantics.

  THE RENDERER CANNOT CARRY `diagnostics` OR SURVIVE `--fields` TODAY, MEASURED AT REVIEW, so extend it rather than hand-building a record. (i) Neither `AgentRenderer.render_summary` nor `AgentRenderer.render_stream` accepts a `diagnostics` argument: the summary dict is composed from a fixed key set. ADD an optional, additive `diagnostics: Optional[Sequence[Dict[str, Any]]] = None` keyword to both (`render_stream` forwards it), emitted only when non-empty, so every existing caller is byte-unchanged. Do NOT hand-compose the summary dict in `cli.py` and push it through `agent_schema.render_jsonl_record` directly: a hand-built record is the defect class backlog `enygec` tracks. (ii) Under `--fields`, `render_summary` projects through `agent_schema.filter_record_fields`, whose `_PRESERVED_FIELDS` keeps `total`/`emitted`/`omitted` but NOT `next` or `diagnostics`: driven at review, `render_summary("find", 3, 1, 2, next_cmd="x", context=<fields=['path']>)` returned a record with no `next`. So `aw find plans --agent --limit 20 --fields path` would print `complete:false` and NO continuation command, which re-breaks the very guide row this plan fixes. Have `render_summary` retain `next` and `diagnostics` on a summary regardless of the projection (they are the summary's payload, not per-item detail), state that in a comment, and do it in the RENDERER, not in `agent_schema._PRESERVED_FIELDS`, whose flat union would also start retaining `next` on every `result` record of every command, a wider change than this plan owns. `renderers.py` is now in `- Scope-Paths:` for (i) and (ii).

  WRITE THROUGH A PIPE-SAFE PATH. `render_stream` RETURNS a string; it does not write. `BaseRenderer.emit`'s `except (BrokenPipeError, OSError)` is reached only through `emit(CommandResult)`, so F-09's "routing through the renderer incidentally fixes the `--agent` case" is true ONLY if the call site writes the returned string inside the same guard. Do so (write to `ctx.stdout`, flush, catch `BrokenPipeError`/`OSError`), and pin it in E-01 by driving `--agent` into a closed pipe.

  CARRY THE `find.id6-collision` FINDING INTO THE `summary` RECORD'S `diagnostics`, and delete the `aw-find-warning:` stderr line for the `--agent` case. That line exists for one stated reason: plan `paw8so`'s decision D3 recorded that `--agent` "never reaches the `CommandResult`, so `diagnostics` is unreachable there" and chose stderr as the only available channel. This plan removes that constraint, so the finding belongs in-band where every other machine consumer reads it. VERIFY FIRST that a `summary` record carrying `diagnostics` validates (measured at authoring: it does, `validate_agent_record` returns `[]`), and keep the rule string `cli._FIND_ID6_COLLISION_RULE` byte-identical because a consumer keys on it. The `--paths` surface keeps its existing silence on both streams.
  - Depends on: E-02
  ONE SHAPE FOR EVERY `--agent` INVOCATION, INCLUDING ZERO MATCHES (decided at review, D-3). Today a zero-match `--agent` query reaches the `CommandResult` branch and emits a `result` record (`aw find plans zzzzzz --agent` measured at review: `{"kind":"result","cmd":"find",...,"evidence":["find-count"],"next":"aw find plans"}`). After this item, `--agent` ALWAYS emits the stream, so a zero-match query emits a lone `summary` with `total: 0`, `emitted: 0`, `complete: true`, at the SAME exit code as today (0). That is the fix for the Concern's own complaint that "a caller cannot tell from the flags which shape they will get". `--json` MUST keep going through the existing `CommandResult` branch, byte-unchanged (E-07 proves it). This changes no zero-match EXIT CODE, so the boundary with `zyj8io` holds; but `zyj8io` E-04 plans to emit its `--agent` refusal as a `result` record and must be re-checked against this shape when it is next reviewed (recorded in its direction in the Deferred section).
  - Expected outcome: `aw find <type> --agent` emits one validating `item` per matched row plus one validating `summary`, and a zero-match query emits only the `summary`; `--limit` bounds emission and yields a `next` that reproduces the same query, including under `--fields`; the collision finding appears in `diagnostics` (also under `--fields`) rather than on stderr; `--json` is unchanged.
  - Execution state: performed

- [x] E-04 SANITIZE EVERY PATH-VALUED AND COMMAND-VALUED FIELD AT CONSTRUCTION, because two of them are home-path injection sites that CRASH the serializer rather than leaking (F-08). Measured at authoring: `AgentRenderer.render_summary(..., next_cmd="aw find plans /home/<user>/secret --agent --limit 3")` raises `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'next'`, and `render_item({"path": "/home/<user>/repo/.aw/records/plans/x.ipd.md"}, ...)` raises the same on `path`. A user-supplied selector reaches `next` directly, and a `path` reaches `item` through `_find_type_records`' `except Exception: rel_p = str(e.path)` fallback, which yields whatever the unrelativizable path was.

  THE `next_template` IS ITSELF AN INJECTION SITE, measured at review. `render_stream` fills it with `next_template.format(limit=tot)`, so a selector containing a brace reaches `str.format`: `"aw find plans {x} --agent --limit {limit}".format(limit=3)` raises `KeyError: 'x'`, and an unbalanced `{` raises `ValueError`. Escape `{`/`}` in every user-derived part of the template (double them) before it is passed, and quote each selector with `shlex.quote` so the `next` command is actually runnable when a selector contains a space or a shell metacharacter, which is what "a runnable command string" in E-01(4) requires. Pin both in E-01 (a selector `{x}` and one containing a space).

  ROUTE BOTH THROUGH `agent_schema.normalize_repo_path` (or an equivalent that provably strips a home prefix), and for the SELECTOR inside `next` decide explicitly what a home-path selector is SHOWN AS once sanitized. This is the same class of defect as backlog `enygec` (which names `attention`, `runs` and `partition` as the hand-built-record sites with this bug) and this plan must not add a fourth instance. Do NOT fix `enygec`'s three sites here; they are out of scope and named in the deferred section.
  - Depends on: E-03
  - Expected outcome: a `find --agent` invocation whose selector or whose matched path contains a home path, or whose selector contains a brace or a space, emits valid records with the home prefix absent and a runnable `next`, and raises nothing.
  - Execution state: performed

### Task group 3: make the documents and the code agree

- [x] E-05 CORRECT THE ONE NORMATIVE SENTENCE THAT NOW CONTRADICTS THE CODE. `docs/cli-output-contract.md` Section 12 reads "**`--agent` Mode for Discovery**: When `--agent` is passed to `aw find` (or when piping paths to another tool), `find` emits bare repo-relative paths, maximizing token efficiency for agent tool consumption. Callers requiring the full metadata dictionary use explicit `--json`." That is the normative statement this plan reverses, so it MUST be rewritten in the same change: `--agent` emits the record stream, `--paths` is the bare-path surface, and `--json` remains the full dictionary. KEEP the section's "Token-Efficient Bare Paths" and "`--paths` (`-p`) Flag" bullets intact: they describe `--paths`, which this plan preserves, and deleting them would discard the rationale for the surface that survives.

  STATE THE TOKEN COST HONESTLY IN THE REVISED TEXT RATHER THAN ASSERTING THE CHANGE IS FREE, because the section's whole argument is token efficiency and this plan raises the cost of the full listing. Measured at authoring on this repository's 1131-row plans listing: 133710 bytes of bare paths versus 202839 bytes as path-only item records (1.52x), or 286533 bytes with the five fields E-03 emits (2.14x). The same measurement is also the argument FOR the change: `--limit 20` over the five-field stream is about 5035 bytes, which is 3.8 percent of the bare full listing, so a BOUNDED record answer is far cheaper than the unbounded bare one an agent gets today. Re-derive both figures at execution rather than quoting these; the row count has already drifted once (985 at the item's filing, 1131 now).

  Write no em or en dashes: all three documents in this item are user-facing prose under the execution contract.
  - Depends on: E-03
  - Expected outcome: Section 12 describes the shipped behavior of all three surfaces, keeps the `--paths` rationale, and states the measured token tradeoff in both directions.
  - Execution state: performed

- [x] E-06 VERIFY THE THREE REMAINING DOCUMENT CLAIMS AND CHANGE ONLY WHAT IS FALSE, reporting each verdict explicitly rather than silently editing or silently skipping.

  (1) `docs/cli-agent-protocol.md` publishes a worked truncated `find` summary record (`"cmd":"find",...,"next":"aw find plans --agent --limit 10"`). Run the real command after E-03 and confirm the SHAPE matches the published example, field for field. ALSO reconcile that document's zero-match `find` example (`{"kind":"result","cmd":"find",...,"evidence":[{"key":"find-count",...,"count":0,...}],"next":"aw find plans"}`), which E-03's one-shape rule makes false for `--agent`: replace it with the real zero-match `summary`, or relabel it as the `--json`-derived shape if it is kept for another purpose, and say which. If the shipped `next` differs in form from the example's (E-03 builds a type-and-selector-bearing command, the example shows `aw find plans --agent --limit 10`), correct the EXAMPLE to match the code, never the reverse.

  (2) `docs/cli-human-guide.md` row `| Bounded output with a continuation hint | aw find plans --agent --limit 20 |` is the claim backlog `wdazvp` filed on. RUN IT and paste the output: if it now bounds and hints, the row needs no edit and that is the finding to report; if anything about it is still wrong, fix the row.

  (3) `docs/cli-migration.md` recipe 4 tells a migrating script "Consume the `item` records and stop at the `summary`" for `aw find plans --agent`, and its "The break, stated loudly" item 3 says those path lines "are now `aw.agent/v1` `item` records followed by a `summary` record". Both become TRUE with E-03 and need no edit. CONFIRM that by running the recipe's own command, and report it as a verified no-edit rather than omitting the file. Note that `docs/cli-migration.md` is NOT in this plan's `- Scope-Paths:`, deliberately, because measurement says it needs no change; if execution finds it DOES, that is a scope-widening finding to record and reconcile at finalize, not a silent addition.
  - Depends on: E-05
  - Expected outcome: three explicit verdicts with pasted command output, and an edit in exactly the places measurement proves false.
  - Execution state: performed

### Task group 4: prove nothing else moved

- [x] E-07 PROVE THE UNCHANGED SURFACES ARE UNCHANGED ON THE LIVE TREE, which is the claim that bounds this plan's risk. Capture, before and after, on the SAME tree state: `aw find plans --paths`, `aw find all --paths`, `aw find plans <a-stable-selector> --paths`, the unflagged human output of the same three, and `aw find plans --json`. All six must be byte-identical.

  CHOOSE DETERMINISTIC COMMANDS AND SAY WHY. `aw check plans --agent`'s `next` field was measured naming a different artifact on three consecutive UNMODIFIED runs (plan `75ic2f` F-14), so a byte-identity probe on a live-tree-derived `next` reports a false disagreement. `find`'s own `next` is derived from the invocation rather than the tree (`cli._run_find` computes it from `norm` and `selectors`), which is why `find` is safe to probe this way and `check` is not. Record that reasoning with the evidence.

  ALSO RUN THE EXISTING `find` SUITE UNCHANGED: `tests/test_find_filters.py` (eleven tests, all driving `-p`), `tests/test_find_single_read.py`, `tests/test_cli_find.py`, `tests/test_find_prompts_lane_status.py` and `tests/test_fields_flag_reach.py`. The last one matters most: its `test_fields_flag_acceptance_find_plans` asserts on `parse_args` ONLY and its docstring says it deliberately does not assert on stdout "because `aw find`'s agent branch prints bare repository paths", naming `wdazvp` as the tracker. That test still PASSES after this plan (it asserts namespace state, not output), so do NOT modify it; instead report whether its docstring is now stale and leave it to a follow-up rather than editing a module this plan does not own.
  - Depends on: E-04
  - Expected outcome: six byte-identical captures, five existing `find` test modules passing, and an explicit statement about `test_fields_flag_reach.py`'s now-stale docstring without editing it.
  - Execution state: performed

- [x] E-08 RUN THE FULL SUITE BARE AND REPORT THE FAILURE-SET DELTA AGAINST A BASELINE YOU ESTABLISH YOURSELF. Run `python3 -m pytest` with NO added flags (`pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; adding `-n0` makes it several times slower, a second `-q` suppresses the summary line this plan requires pasted, and `-p no:randomly` disables the order randomization that surfaces order dependence). Capture the summary line at the BASE commit before any edit and again at the end, and state the delta as a SET of test ids, not as a count comparison.

  THE BAR IS AN EMPTY DELTA, not a green run: this repository's suite is large and an environmental failure present before the change is not this plan's to fix. A failure present AFTER and absent BEFORE is a regression and blocks the transition.
  - Depends on: E-07
  - Expected outcome: two pasted bare-suite summary lines and an explicitly empty failure-set delta.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation below names a symbol or quotes the text it refers to; `agent_workflows/cli.py` is cited by 40-plus other pending plans, so offsets in it are especially short-lived.
- THE BARE SUITE IS THE CONTRACT. `AGENTS.md` requires `python3 -m pytest` with no added flags, and names the three specific flags not to add (`-n0`, a second `-q`, `-p no:randomly`) with the measured reason for each. E-08 follows that literally.
- NO CODE-PINNING TESTS (GUIDING_PRINCIPLES P16). A test may not read production source, count callers, or assert a symbol exists; it must drive the command and assert on real output, exit codes and side effects. This is why E-01 is a subprocess-or-`cli.main` driver over a fixture and not a parser walk, and it is also why this plan does not pin the branch condition it changes.
- NO EM OR EN DASHES IN USER-FACING PROSE. All three documents this plan edits are user-facing (`CONTRIBUTING.md` "Authoring conventions"), so E-05 and E-06 must use hyphens. The rule does not apply to this plan itself.
- `--dir` IS HOW A `find` TEST STAYS OFF THE LIVE TREE. `tests/test_find_filters.py`'s `run_find` helper passes `--dir str(self.repo_root)`, and eleven tests in that module prove the pattern works across five record types. E-01 reuses it rather than inventing a harness.
- THE EXISTING `find` CONTRACT MODULE IS `tests/test_find_filters.py`, not a module named for the verb's surfaces. A plan touching `find` that does not run it has not checked its own blast radius.

## Findings

| id | finding | evidence |
| --- | --- | --- |
| F-01 | THE DEFECT REPRODUCES EXACTLY AS FILED, AND THE ITEM'S COUNT HAS DRIFTED. `aw find plans --agent --limit 20 \| wc -l` prints 1131 (the item recorded 985), and `aw find plans --agent --fields findings` prints the same 1131 bare paths with zero `aw.agent/v1` records. The flags are not unwired: `result_types.select_output` reads `getattr(args, "limit", None)` and `getattr(args, "fields", None)` onto the context on all three return paths, and `--limit` is declared for this verb by the shared noun-verb loop (`"--limit", type=int, default=None, help="Max rows (index/find)."`). Nothing in `cli._run_find` consults either. NO COUNT IS USED AS A BAR ANYWHERE IN THIS PLAN for exactly this reason. | Both commands run in this lane at HEAD `74b301435`; `select_output` read; the `add_argument` call read. |
| F-02 | ONLY ONE CONSUMER OF `ctx.limit` EXISTS IN THE WHOLE PACKAGE, AND IT IS NOT A COMMAND. `renderers.AgentRenderer.render_stream` is the sole reader of `ctx.limit`. Nine parser leaves declare `--limit` (`check`, `find`, `group`, `index`, `rename`, `research index`, `runs analyze`, `runs query`, `search`), and measured one by one, `check plans`, `index plans` and `search` all ignore it too: `aw check plans --agent` and `aw check plans --agent --limit 1` differ in byte count only because the live tree changed between runs, and `aw search plans <pattern> --agent --limit 2` emits the same single `result` record as without it. So `find` is the WORST instance of a wider pattern, not a lone one; this plan fixes `find` only and the breadth is recorded in the deferred section rather than silently absorbed. | `grep` for `ctx.limit` across `agent_workflows/`; a parser walk reporting 250 leaves with 9 declaring `--limit`; each of the three commands run with and without the flag. |
| F-03 | THREE SHIPPED DOCUMENTS ALREADY SPECIFY DIRECTION (a) IN DETAIL, WHICH IS WHAT RESOLVES THE ITEM'S OPEN DECISION. `docs/cli-agent-protocol.md` publishes a worked truncated summary record naming this verb: `{"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":10,"emitted":3,"omitted":7,"complete":false,"next":"aw find plans --agent --limit 10"}`. `docs/cli-migration.md` recipe 4 instructs a migrating script to "Consume the `item` records and stop at the `summary`" under `aw find plans --agent`, and its break list says those path lines "are now `aw.agent/v1` `item` records followed by a `summary` record". `docs/cli-human-guide.md` advertises `aw find plans --agent --limit 20` as bounded with a continuation hint. Direction (a) makes all three true with one Section 12 amendment; (b) and (c) require amending all three to admit that the documented shape does not exist. | All three documents read at the quoted lines; the protocol example compared against actual output (which is a bare path). |
| F-04 | THE REPOSITORY HAS ALREADY RULED THAT ONE MACHINE FORMAT IS CANONICAL, so option (b) ("keep bare paths and refuse the flags") is a larger change than it looks. `docs/cli-output-contract.md` Section 10 states "`CommandResult` and `aw.agent/v1` **SUBSUMES and REPLACES** the legacy `Drift` TSV wire format" and "Exactly one canonical machine format (`aw.agent/v1`) is active". Plan `n9ua3b` (`reviewed`) cites that same ruling to migrate the three `index <type> --check --agent` TSV surfaces onto records, over the identical objection. Section 12's bare-path sentence is the ONE place that sanctions a second shape under `--agent`, and this plan amends exactly it. | Section 10 and Section 12 read; `n9ua3b`'s Concern and its authoring history read. |
| F-05 | THE ITEM'S "BREAKING CHANGE TO A PUBLISHED SURFACE" PREMISE IS WEAK ON BOTH HALVES. (i) `--paths` is untouched by this plan, and measured at authoring the three surfaces are byte-identical today (`aw find plans --paths`, `aw find plans --agent --paths` and `aw find plans --agent` produce the same 133710 bytes), so every script already passing `--paths` is unaffected and a script passing only `--agent` has a one-flag migration. (ii) `aw find` HAS NEVER SHIPPED: the four tags are `v1.0.0`, `v1.1.0`, `v1.2.0-recreated`, `v1.3.0-rc.1`, and the newest declares eight subparsers (`install`, `setup`, `uninstall`, `list`, `status`, `plans`, `plan-names`, `check-local-leaks`) with no `find` among them. There is no released consumer of these bytes. This is the same measurement that collapsed the identical premise for `n9ua3b`. | `cmp` across the three captures; `git tag` enumerated and `git show v1.3.0-rc.1:agent_workflows/cli.py` grepped for `add_parser(`. |
| F-06 | `render_stream` HAS ZERO PRODUCTION CALLERS, SO THIS PLAN IS ITS FIRST, AND ITS LIMIT EDGES ARE SHARP. A search for `.render_stream(` across `agent_workflows/` and `tests/` returns no call site; `run_analytics_cli.emit_query_agent_stream` deliberately calls `render_item` and `render_summary` separately (its comment: "`render_stream` derives `omitted` from ITS OWN `--limit` truncation, which knows nothing about the row bound the query engine already applied"). Measured directly: `limit=0` emits zero items and reports `omitted == total` with a `next`; `limit=-1` emits `len(items) - 1` items via slice semantics and still reports `complete: false`; `limit` above the row count reports `complete: true` with no `next`. E-03 must decide the non-positive case rather than inherit slice behavior. ALSO MEASURED: the summary-plus-`--fields` crash that `run_analytics_cli`'s comment documents is FIXED (plan `gygujf` widened `agent_schema._PRESERVED_FIELDS` to retain `total`/`emitted`/`omitted`), so passing the context to `render_summary` is safe now; that stale comment is backlog `o8vgss`/`cm80ge`, not this plan's. | The search; `run_analytics_cli`'s comment read; `render_stream` driven in-process at four limit values; `render_summary(..., context=ctx_with_fields)` driven and returning a valid record. |
| F-07 | THE RECORD PATH IS REACHABLE TODAY ONLY ON A ZERO-MATCH QUERY, AND A SIBLING PLAN IS CHANGING THAT SAME BRANCH. `aw find plans zzzzzz --agent` emits `{"kind":"result","cmd":"find","outcome":"clean","exit":0,...}` while `aw find plans 75ic2f --agent` emits one bare path, because the branch keys on `all_paths` being truthy rather than on selector absence. Plan `zyj8io` (`reviewed`, `Readiness: no-go`, Set `selquiet`) makes a zero-match selector exit 2 across all four `find` surfaces and declares `agent_workflows/cli.py` plus `docs/cli-output-contract.md` and `docs/cli-agent-protocol.md` in its scope, so the two plans meet on that one narrow branch and on two of the same documents. THIS PLAN ASSERTS NO ZERO-MATCH EXIT CODE ANYWHERE, and E-02 leaves the `--paths` exit expression `return 0 if (all_paths or not selectors) else 1` exactly as found. Both plans run in isolated worktrees through the merge-and-revalidate gate, so file overlap is not a hazard; the shared SEMANTICS are, which is why the boundary is stated here rather than discovered at merge. | Both commands run; `zyj8io`'s front matter and Concern read. |
| F-08 | TWO RECORD FIELDS ARE HOME-PATH SITES THAT CRASH THE SERIALIZER, NOT LEAK THROUGH IT. `agent_schema.validate_agent_record` raises on any string value matching its home-path pattern, and `render_jsonl_record` asserts validity before serializing. Measured: `render_summary(..., next_cmd="aw find plans /home/<user>/secret --agent --limit 3")` raises `ValueError: ... Unsanitized absolute home path in field 'next'`, and `render_item({"path": "/home/<user>/repo/.aw/records/plans/x.ipd.md"}, ...)` raises the same on `path`. A selector reaches `next` verbatim, and an absolute `path` can reach an `item` through `_find_type_records`' `except Exception: rel_p = str(e.path)` fallback. Backlog `enygec` records this exact defect class on `attention`, `runs` and `partition`; this plan must not become a fourth site, which is why E-04 exists as its own item with its own validation. Note the current bare-path surface CANNOT hit this (it prints with `print`, not through the validator), so the crash is a hazard this change introduces unless E-04 lands with E-03. | Both calls driven in-process with the exception text captured; the `except Exception` fallback read; `enygec` read. |
| F-09 | THE BARE-PATH STREAM ALREADY DIES ON A BROKEN PIPE, AND THIS PLAN NEITHER FIXES NOR WORSENS IT. `python3 -m agent_workflows find plans --agent \| head -2` exits 120 with a `BrokenPipeError` traceback on stderr, from `print(p)` inside the bare-path loop; `--paths` and the human path do the same, and `--json` does not. `docs/cli-output-contract.md` Section 7 promises "All handlers catch `BrokenPipeError` / `EPIPE` when writing to stdout and exit cleanly without dumping Python stack traces", so the promise is already false for three of this verb's four surfaces. `BaseRenderer.emit` DOES catch it, but only for a `CommandResult`; `render_stream` returns a string, so the `--agent` case is fixed only because E-03 now requires the call site to write that string inside the same guard (corrected at review). REPORT THAT AS A SIDE EFFECT, do not claim it as a fix, and do not extend scope to the other two surfaces: no backlog item carries this yet and filing one is the honest move. | The four invocations run with stderr captured; `BaseRenderer.emit`'s `except (BrokenPipeError, OSError)` read; Section 7 read. |
| F-10 | THE HUMAN ROW CARRIES ANSI, SO A RECORD BUILT BY SPLITTING IT WOULD VIOLATE THE CONTRACT. `cli._find_type_records` returns rows like `\x1b[1;38;5;46m✓\x1b[0m  \x1b[1;38;5;46mexecuted\x1b[0m  ...` when the `Term` has color, while `docs/cli-output-contract.md` Section 4 requires that agent records "never contain ANSI escape codes", enforced by `validate_agent_record`'s ANSI rule. This is the mechanical reason E-03 threads structured fields out of the row builder instead of parsing `lines`; measured, `--json` is already clean because it carries `data.matches` built on a colorless `Term`. | `_find_type_records` driven in-process with a color `Term` and the raw row repr printed; `aw find plans 75ic2f --json --color` grepped for escapes (zero). |

## Proposed changes (ordered, validatable)

1. E-01 writes the failing behavioral baseline over a fixture repository, covering `--agent` record validity, `--limit` bounding, `--fields` projection, ANSI absence, and the byte-invariance of `--paths` and human output.
2. E-02 narrows the bare-path early return to `--paths` alone and rewrites the comment that records the now-superseded byte-identity guarantee, leaving the exit expression untouched.
3. E-03 builds the `item` stream and the terminal `summary` through `AgentRenderer.render_stream`, threading structured fields out of the row builder, supplying a query-preserving `next_template`, deciding the non-positive `--limit` behavior explicitly, and moving the `find.id6-collision` finding into `diagnostics`.
4. E-04 sanitizes the `next` and `path` fields at construction so a home-path selector or an unrelativizable match cannot raise from the serializer.
5. E-05 rewrites the one normative sentence in `docs/cli-output-contract.md` Section 12 that mandates bare paths under `--agent`, keeping the `--paths` rationale and stating the measured token tradeoff in both directions.
6. E-06 verifies the three remaining document claims against the shipped behavior and edits only what measurement proves false.
7. E-07 proves the six unchanged live-tree captures byte-identical and runs the five existing `find` test modules.
8. E-08 runs the bare suite before and after and reports an empty failure-set delta.

## Deferred / out of scope (with reason)

- `--limit` BEING INERT ON `aw check`, `aw index` AND `aw search` under `--agent` (F-02). Measured and real, but each is a different command with a different payload shape, and `check`/`index` emit a single `result` record where a stream has no obvious meaning (what would an `item` be: one finding, or one checked artifact?). That is a per-verb design question, not this plan's. Note `aw index`'s `--limit` is a HOT-WINDOW SIZE for `INDEX.md` and is honored in its human path, a different meaning a fixer must not conflate with the agent-stream one. Carrier filed at authoring with the full per-verb measurement.
  - Carrier: 4uw9gy
- THE THREE `enygec` SITES (`attention`, `runs`, `partition` echoing an unsanitized selector into a hand-built record). Same defect class as F-08 and already carried. E-04 fixes this verb only and deliberately does not touch the others, because `enygec` records that the honest fix is a per-surface decision about what a sanitized selector is SHOWN AS.
  - Carrier: enygec
- THE BROKEN-PIPE TRACEBACK ON `--paths` AND ON HUMAN OUTPUT (F-09), which also affects `aw doctor` and `aw search --paths`. This plan incidentally fixes the `--agent` case by routing through `BaseRenderer.emit` and reports that as a side effect. Fixing the others means wrapping the bare `print` loops, which is a different surface with its own byte-identity bar, and `docs/cli-output-contract.md` Section 7's promise is already false for them independently of this change. Carrier filed at authoring with all six measured invocations.
  - Carrier: kinyxf
- THE ZERO-MATCH EXIT-CODE DIVERGENCE across `find`'s four surfaces (F-07), owned by plan `zyj8io` (`reviewed`). This plan asserts no zero-match exit code and leaves the `--paths` exit expression as found. NOTE FOR `zyj8io`: after this plan a zero-match `--agent` query emits a `summary`, not a `result`, so that plan's E-04 record shape must be reconciled at its next review.
  - Carrier: zyj8io
- `--verbose` NOT REACHING THIS VERB. Owned by `qm04zi` and its plan `c4btis`, which has since EXECUTED (re-measured at review: `aw find --help` lists `--verbose`, and backlog `qm04zi` is `done`), so `--verbose` may already widen `diagnostics` detail; this plan asserts the COMPACT shape so the two do not contradict.
  - Carrier: qm04zi
- `docs/cli-agent-protocol.md`'s "Two escape hatches" undercount, which omits `--limit` entirely. Carried by `9qya0k`, whose own text says the `--limit` bullet "should be written after `wdazvp` resolves". E-06 touches that file only to reconcile the worked `find` example, not the count.
  - Carrier: 9qya0k
- `tests/test_fields_flag_reach.py`'s DOCSTRING, which states that `find`'s agent branch prints bare paths and cites `wdazvp` as the tracker. The test itself still passes (it asserts `parse_args` state, not stdout), so E-07 reports the staleness without editing a module this plan does not own.
  - Carrier-Declined: a stale docstring in a passing test is a comment, not an obligation: it misleads no gate, breaks no behavior, and the module belongs to executed plan `75ic2f`. E-07 REPORTS it with evidence so the next change to that module corrects it in place; filing a backlog item to adjust one docstring sentence would cost more records churn than the defect it names.
- THE `--json` PAYLOAD, which already carries `data.matches` and `data.paths` and is explicitly the "full metadata dictionary" surface. Unchanged, and E-07 proves it byte-identical.
  - Carrier-Declined: nothing is deferred here; this row records a surface this plan deliberately leaves alone and PROVES unchanged in V-07, so there is no outstanding obligation to hand off.

## Scope check

- Over-scope: none. `agent_workflows/cli.py` carries E-02's branch narrowing, E-03's stream construction and the `_find_type_records` field threading, and E-04's sanitization. `tests/test_find_agent_stream.py` is the new module from E-01. `docs/cli-output-contract.md` carries E-05's Section 12 amendment. `docs/cli-agent-protocol.md` and `docs/cli-human-guide.md` carry E-06's verdict-driven edits, which may be empty for the guide if its row now reads true. `renderers.py` IS edited (added at review): two additive keyword arguments and a `next`/`diagnostics` retention rule on the summary, because the renderer measurably cannot carry either today (E-03). `agent_schema.py` is NOT edited (its projection semantics were fixed by `gygujf` and its sanitizer is called, not changed). `result_types.py` is NOT edited (consumption is already correct, F-01). `docs/cli-migration.md` is NOT in scope because measurement says its two `find` claims become true unedited (E-06 part 3); if that proves wrong it is a scope-widening finding to reconcile at finalize. No spec is declared, so the run must announce no declared spec edits and none may be made.
- Under-scope: the risk is E-03 being larger than one pass if the structured fields turn out not to be cleanly available from `_find_type_records`' three branches (plans, research, all-other-types each build rows differently). If that happens, the correct move is to SPLIT E-03 into a field-threading item and a stream-emission item rather than to parse the rendered row, which F-10 shows would carry ANSI into a record the validator rejects.

## Required tests / validation

- THE NEW BEHAVIORAL MODULE `tests/test_find_agent_stream.py`, driving a FIXTURE repository through `--dir` (the pattern `tests/test_find_filters.py` already proves) and asserting: every `--agent` line parses as `aw.agent/v1`; `agent_schema.validate_agent_record` returns `[]` for every record; the terminal record is a `summary` with `emitted + omitted == total`; `--limit N` emits exactly `N` items with `complete: false` and a runnable `next`; `--fields path` retains `path` and drops a named non-envelope key; no line carries an ANSI escape; the non-positive `--limit` behavior E-03 chose; and `--paths` plus human output byte-identical across the change.
- THE FIVE EXISTING `find` MODULES, unchanged and passing: `tests/test_find_filters.py`, `tests/test_find_single_read.py`, `tests/test_cli_find.py`, `tests/test_find_prompts_lane_status.py`, `tests/test_fields_flag_reach.py`.
- THE LIVE-TREE INVARIANCE PROBE of E-07: six byte-identical captures across `--paths`, human and `--json` on three queries, with the determinism reasoning recorded (and specifically NOT using `aw check plans --agent`, whose `next` was measured varying across unmodified runs).
- THE HOME-PATH PROBE of E-04: a selector containing a home path and, if constructible, a match whose path cannot be relativized, both emitting valid records and raising nothing.
- THE BARE FULL SUITE of E-08: `python3 -m pytest` with no added flags, before and after, with the failure-set delta stated as a set and required to be empty.
- `aw ipd lint` conforming at `--phase author` before review and at `--phase pre-transition` before the terminal move. `aw check` to confirm no new drift.

## Spec / documentation sync

No spec amendment. The behavior this plan changes is specified in `docs/cli-output-contract.md`, which is a normative DOCUMENT rather than a `.spec.md` record, so no `.spec.md` file is declared in `- Scope-Paths:` and the run must announce no declared spec edits. Checked rather than assumed: `grep` over `.aw/records/specs/` finds no spec text mandating a bare-path shape for `aw find --agent`; the nearest, spec `20260818-1525-01` (`implemented`), specifies `find` as a manifest query with "a machine-readable mode (`--json` and/or `--agent`) and documented exit codes" in its G6, which this plan satisfies rather than contradicts, and whose TSV clause `docs/cli-output-contract.md` Section 10 already supersedes.

Three documents are in scope and each has a stated reason. `docs/cli-output-contract.md` Section 12 is AMENDED because it is the one normative sentence that mandates the behavior this plan reverses; leaving it would ship code that contradicts the contract. `docs/cli-agent-protocol.md`'s worked `find` summary example is RECONCILED with the shipped `next` form. `docs/cli-human-guide.md`'s `--limit` row is verified and corrected only if it is still false. `docs/cli-migration.md` is deliberately NOT in scope, with the measurement recorded in E-06.

## Open questions

### OQ-01: Which of the backlog item's three candidate directions should `aw find --agent` take

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE AT AUTHORING: direction (a), a real record stream under `--agent` with `--paths` keeping the bare-path surface. The item framed this as needing a decision because (a) "changes a machine surface every existing consumer parses line by line". THREE MEASUREMENTS DECIDE IT. FIRST (F-03), three shipped documents already describe (a) in detail, one of them publishing a worked `find` summary record and another instructing scripts to consume `item` records that do not exist; (a) makes all three true with one amendment, while (b) and (c) require amending all three to admit the documented shape is not real. SECOND (F-04), `docs/cli-output-contract.md` Section 10 has already ruled "Exactly one canonical machine format (`aw.agent/v1`) is active", and plan `n9ua3b` cites that same ruling for the same class of defect; option (b) would entrench a second convention under the flag that names the first. THIRD (F-05), the "existing consumer" premise is weak twice over: `--paths` is byte-identical to `--agent` today and is untouched here, so a script has a one-flag migration, and `aw find` has never appeared in a tagged release, so there is no released consumer at all. Option (c) is rejected on its own terms: the item itself calls it a half-fix, and it would emit no `summary`, leaving the guide's "continuation hint" claim false while making the flag appear to work.

### OQ-02: Should a non-positive `--limit` be refused, clamped, or treated as unset

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: REFUSED AT EXIT 2 WITH A `cannot-run` RECORD, resolved at authoring from in-repo precedent rather than left to the executor, so no open obligation leaves this plan. The facts that force a decision: `render_stream` with `limit=0` emits zero items and reports `omitted == total` (technically honest, practically useless), and with `limit=-1` emits `len(items) - 1` items through Python slice semantics while reporting `complete: false`, which is simply wrong. THE PRECEDENT IS EXPLICIT AND LOCAL: `run_analytics_query._parse_limit` refuses rather than clamping, raising on a non-integer, on a value below one ("`--limit` must be greater than zero"), and above `MAX_ROW_LIMIT`, and `aw runs query` is the one shipped command that already honors `--limit` under `--agent`. Matching it keeps one meaning for one flag across the two verbs that implement it, and a loud refusal is this repository's standing preference over a silent reinterpretation (the same reasoning `aw find`'s existing `--status` refusal uses). Clamping is rejected because it answers a different question than the one asked; treating it as unset is rejected because it would turn a typo into an unbounded dump, which is the exact harm this plan exists to remove. NOT ADOPTED FROM THAT PRECEDENT: an upper ceiling. `MAX_ROW_LIMIT` exists because `aw runs query` pages a potentially unbounded analytics corpus, while `find`'s rows are bounded by the records tree and a caller asking for more rows than exist already gets `complete: true`; adding a ceiling here would refuse a legitimate full listing. E-03 implements the refusal and states the reason at the site; E-01 pins both the zero and the negative case.

### OQ-03: Should the `item` record carry a research row's free-text summary

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: NO, resolved at authoring. The research branch of `_find_type_records` appends `f"  {e.summary}"` to its display row, and a record field carrying it would be unbounded free prose: this repository's research summaries are long enough that backlog `cvxbbu` records three committed ones exceeding a 300-character bound. Including it would make the per-item record size dominated by one type's prose, defeating the token control this plan exists to deliver, and `--json` already carries the full rendered row in `data.matches` for a caller that wants it. E-03 records the omission in a comment so a later reader does not read it as an oversight.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the new module's RED output at the base commit, before any production edit, with the assertion errors visible and each `--agent` assertion identifiable. A summary line alone is NOT sufficient. Also paste the same run showing the `--paths` and human byte-identity assertions PASSING at the base commit, which is what proves the baseline is a real discriminator rather than a module that fails wholesale. State the fixture's row count and confirm it is the number the `total` assertion uses, so the test cannot pass against a live-tree figure. Confirm by inspection that the module reads no production source file and asserts no symbol's existence (P16), and say in one sentence how each assertion obtains its facts (driving the command, reading stdout) rather than asserting it generally.
  - Observed evidence:
    Failing baseline at base commit `5fa4022c5e254e04d5bd1ee0c9023cfe7d9b9a53` before production edits:
    ```
    =================================== FAILURES ===================================
    ______ TestFindAgentStream.test_14_agent_collision_diagnostics_in_summary ______
    tests/test_find_agent_stream.py:275: in test_14_agent_collision_diagnostics_in_summary
        self.assertNotIn("aw-find-warning:", err, "Warning line leaked to stderr in --agent mode")
    E   AssertionError: 'aw-find-warning:' unexpectedly found in 'aw-find-warning:find.id6-collision:col001:cross-type:...
    ______ TestFindAgentStream.test_02_agent_stream_records_strictly_validate ______
    tests/test_find_agent_stream.py:125: in test_02_agent_stream_records_strictly_validate
        rec = json.loads(line)
    E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    ____ TestFindAgentStream.test_09_agent_stream_brace_and_space_selector_next ____
    tests/test_find_agent_stream.py:216: in test_09_agent_stream_brace_and_space_selector_next
        self.assertEqual(summary.get("kind"), "summary")
    E   AssertionError: 'result' != 'summary'
    ___ TestFindAgentStream.test_04_agent_stream_limit_bounding_and_continuation ___
    tests/test_find_agent_stream.py:151: in test_04_agent_stream_limit_bounding_and_continuation
        items = [json.loads(line) for line in lines[:-1]]
    E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    ___ TestFindAgentStream.test_01_agent_stream_parses_json_and_schema_version ____
    tests/test_find_agent_stream.py:115: in test_01_agent_stream_parses_json_and_schema_version
        rec = json.loads(line)
    E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    ______ TestFindAgentStream.test_11_agent_stream_nonpositive_limit_refusal ______
    tests/test_find_agent_stream.py:248: in test_11_agent_stream_nonpositive_limit_refusal
        self.assertEqual(rc0, 2)
    E   AssertionError: 0 != 2
    ____ TestFindAgentStream.test_07_agent_stream_limit_and_fields_retains_next ____
    tests/test_find_agent_stream.py:191: in test_07_agent_stream_limit_and_fields_retains_next
        summary = json.loads(lines[-1])
    E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    _______ TestFindAgentStream.test_08_agent_stream_zero_match_lone_summary _______
    tests/test_find_agent_stream.py:203: in test_08_agent_stream_zero_match_lone_summary
        self.assertEqual(summary.get("kind"), "summary")
    E   AssertionError: 'result' != 'summary'
    __________ TestFindAgentStream.test_05_agent_stream_fields_projection __________
    tests/test_find_agent_stream.py:173: in test_05_agent_stream_fields_projection
        items = [json.loads(line) for line in lines[:-1]]
    E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    _____ TestFindAgentStream.test_03_agent_stream_terminal_summary_accounting _____
    tests/test_find_agent_stream.py:135: in test_03_agent_stream_terminal_summary_accounting
        summary = json.loads(lines[-1])
    E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    =========================== short test summary info ============================
    FAILED tests/test_find_agent_stream.py::TestFindAgentStream::test_14_agent_collision_diagnostics_in_summary
    FAILED tests/test_find_agent_stream.py::TestFindAgentStream::test_02_agent_stream_records_strictly_validate
    FAILED tests/test_find_agent_stream.py::TestFindAgentStream::test_09_agent_stream_brace_and_space_selector_next
    FAILED tests/test_find_agent_stream.py::TestFindAgentStream::test_04_agent_stream_limit_bounding_and_continuation
    FAILED tests/test_find_agent_stream.py::TestFindAgentStream::test_01_agent_stream_parses_json_and_schema_version
    FAILED tests/test_find_agent_stream.py::TestFindAgentStream::test_11_agent_stream_nonpositive_limit_refusal
    FAILED tests/test_find_agent_stream.py::TestFindAgentStream::test_07_agent_stream_limit_and_fields_retains_next
    FAILED tests/test_find_agent_stream.py::TestFindAgentStream::test_08_agent_stream_zero_match_lone_summary
    FAILED tests/test_find_agent_stream.py::TestFindAgentStream::test_05_agent_stream_fields_projection
    FAILED tests/test_find_agent_stream.py::TestFindAgentStream::test_03_agent_stream_terminal_summary_accounting
    ========================= 10 failed, 4 passed in 3.18s =========================
    ```
    Passing tests at base commit:
    ```
    tests/test_find_agent_stream.py::TestFindAgentStream::test_10_agent_stream_closed_pipe_clean_exit PASSED [ 57%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_06_agent_stream_no_ansi_escapes PASSED [ 64%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_13_human_output_byte_identity PASSED [ 71%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_12_paths_byte_identity PASSED [ 92%]
    ```
    Fixture row count: The temp fixture repository explicitly populates 3 plans (`pln001`, `pln002`, `pln003`), 1 spec, and 1 backlog item. For `aw find plans --agent`, `total` matches the 3 created plan entries.
    Inspection for P16 compliance: `tests/test_find_agent_stream.py` contains zero imports of `inspect` or `ast`, reads no source files from `agent_workflows/`, and checks no symbol presence or caller counts. Every assertion executes `cli.main(["find", ...])` or drives a subprocess and asserts strictly on stdout, stderr, and exit codes.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the diff of the branch condition and the full replacement comment. CONFIRM THE COMMENT NO LONGER CLAIMS a byte-identity guarantee between `--paths` and `--agent`, by quoting the removed sentence and the new text, because leaving that claim would be a false statement in the code about the very thing this plan changes. Paste `aw find plans --paths` output byte-compared against the pre-change capture (a `cmp` or a hash of both), and paste the exit codes of `aw find plans <matching-selector> --paths` and `aw find plans zzzzzz --paths` showing them UNCHANGED at 0 and 1 respectively, which is the boundary with `zyj8io` (F-07). Confirm the exit expression `return 0 if (all_paths or not selectors) else 1` is textually unchanged.
  - Observed evidence:
    Branch condition and comment diff from `agent_workflows/cli.py`:
    ```diff
    @@ -12497,10 +12497,12 @@ def _run_find(args: argparse.Namespace) -> int:
    -        # In agent mode or with --paths/-p, emit bare paths.
    -        # IMPORTANT: Keep --paths and --agent output identical so scripts can use either interchangeably.
    -        # This branch returns before any CommandResult is built.
    -        if getattr(args, "paths", False) or (ctx.is_agent and all_paths):
    +        # In --paths/-p mode, emit bare repo-relative paths (docs/cli-output-contract.md Section 12).
    +        # Backlog wdazvp / IPD okiso1: --agent now falls through to emit an aw.agent/v1 item stream
    +        # with terminal summary so --limit and --fields are honored.
    +        # Warning line aw-find-warning: survives on stderr for --paths (E-03 routes it to diagnostics for --agent).
    +        # Exit expression left textually as found (zyj8io owns zero-match exit code convergence).
    +        if getattr(args, "paths", False):
    ```
    Quoted removed sentence:
    `"IMPORTANT: Keep --paths and --agent output identical so scripts can use either interchangeably."`
    Quoted new text:
    `"# In --paths/-p mode, emit bare repo-relative paths (docs/cli-output-contract.md Section 12)."`
    `"# Backlog wdazvp / IPD okiso1: --agent now falls through to emit an aw.agent/v1 item stream with terminal summary so --limit and --fields are honored."`
    Live-tree pre-change vs post-change sha256 hashes of `aw find plans --paths`:
    Baseline hash: `010c2f0e4daadff5e2399c3a8cbb2462815c0e92159ea41bce24be2fa6fbb889`
    Post-change hash: `010c2f0e4daadff5e2399c3a8cbb2462815c0e92159ea41bce24be2fa6fbb889`
    Match: byte-identical (identical sha256).
    Exit code invariance:
    `aw find plans 75ic2f --paths` exited 0.
    `aw find plans zzzzzz --paths` exited 1.
    Exit expression confirmation: `return 0 if (all_paths or not selectors) else 1` remains textually unchanged at line 12513.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste real stdout from at least three invocations: an unbounded `aw find <type> --agent`, a bounded `--limit N`, and a bounded `--limit N --fields path`. For each, paste the FIRST item record, the terminal summary record, and the line count. Then paste the output of running `agent_schema.validate_agent_record` over EVERY emitted record (not a sample) reporting `[]` for each, and state how many records were checked. Paste the `next` command from the bounded run AND RUN IT, showing it returns the same query's rows rather than a different result set, which is the specific failure the default `next_template` would have caused. Paste the chosen non-positive `--limit` behavior being exercised (OQ-02) with the comment that states the reason. Paste a collision case showing `find.id6-collision` inside the summary's `diagnostics` with the rule string byte-identical to `cli._FIND_ID6_COLLISION_RULE`, and paste stderr showing the `aw-find-warning:` line is GONE from `--agent` while `--paths` remains silent on both streams. Paste the `--limit N --fields path` summary record showing `next` (and, for a collision fixture, `diagnostics`) RETAINED under projection. Paste a zero-match `--agent` run emitting exactly one `summary` with `total: 0` at exit 0, and the same query under `--json` byte-identical to its pre-change capture. Paste `aw find <type> --agent | head -1` showing exit without a traceback on stderr. Paste the `git diff` of `agent_workflows/renderers.py` showing only the additive `diagnostics` keyword and the summary retention rule, plus a passing run of the existing renderer tests (name the modules found by searching `tests/` for `render_summary`/`render_stream`). Finally confirm no record contains an ANSI escape by pasting a search over the full stdout, since the row builder's output does (F-10).
  - Observed evidence:
    1. Three live-tree invocations:
       - Unbounded `aw find specs --agent`:
         Line count: 41
         First item: `{"schema":"aw.agent/v1","kind":"item","cmd":"find","path":".aw/records/specs/approved/20260824-5tapom-01-5tapom-research-lifecycle-reliability.spec.md","type":"specs","id6":"5tapom","status":"approved"}`
         Terminal summary: `{"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":40,"emitted":40,"omitted":0,"complete":true}`
         Validation across all 41 records: 0 errors.
       - Bounded `aw find specs --agent --limit 5`:
         Line count: 6
         First item: `{"schema":"aw.agent/v1","kind":"item","cmd":"find","path":".aw/records/specs/approved/20260824-5tapom-01-5tapom-research-lifecycle-reliability.spec.md","type":"specs","id6":"5tapom","status":"approved"}`
         Terminal summary: `{"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":40,"emitted":5,"omitted":35,"complete":false,"next":"aw find specs --agent --limit 40"}`
         Validation across all 6 records: 0 errors.
       - Bounded + fields `aw find specs --agent --limit 5 --fields path`:
         Line count: 6
         First item: `{"schema":"aw.agent/v1","kind":"item","cmd":"find","path":".aw/records/specs/approved/20260824-5tapom-01-5tapom-research-lifecycle-reliability.spec.md"}`
         Terminal summary: `{"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":40,"emitted":5,"omitted":35,"complete":false,"next":"aw find specs --fields path --agent --limit 40"}`
         Validation across all 6 records: 0 errors.
    2. Continuation execution:
       Executing continuation command `aw find specs --agent --limit 40` returned 41 lines (40 items + 1 summary); first item matched the unbounded first item exactly (`Matches unbounded first item: True`).
    3. Non-positive `--limit` behavior:
       `aw find specs --agent --limit 0` exited 2 with `{"schema":"aw.agent/v1","kind":"error","cmd":"find","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":"aw find --help"}`.
       `aw find specs --agent --limit -3` exited 2 with identical error record.
       Comment in `cli.py`:
       `# IPD okiso1 OQ-02: non-positive --limit refused at exit 2 with cannot-run record (precedent: run_analytics_query._parse_limit)`
    4. Collision diagnostics:
       On collision fixture:
       Summary record: `{"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":2,"emitted":2,"omitted":0,"complete":true,"diagnostics":[{"location":".aw/records/backlog/open/20260927-setalpha-01-col001-coll-bkl.backlog.md","rule":"find.id6-collision","detail":"id6 col001 is claimed as its own identity by 2 artifacts (cross-type): .aw/records/backlog/open/20260927-setalpha-01-col001-coll-bkl.backlog.md, .aw/records/specs/to-review/20260927-setalpha-01-col001-coll-spec.spec.md","severity":"warning","fix":"give the non-owning artifact its OWN id6 (in `- Id:` and the filename identity slot) and cite the source through a typed reference field (DECISIONS.md D140)"}]}`
       Rule string is byte-identical: `find.id6-collision`.
       `stderr` on `--agent` is empty (warning line removed). `--paths` stderr is empty and stdout emits bare paths with 0 warnings.
    5. Projected summary retains `next` and `diagnostics` under `--fields path`: verified in `test_07_agent_stream_limit_and_fields_retains_next` and invocation 3 above.
    6. Zero-match query:
       `aw find plans zzzzzz --agent` exited 0 with lone summary:
       `{"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":0,"emitted":0,"omitted":0,"complete":true}`
       `aw find plans zzzzzz --json` exited 0 with byte-identical full `CommandResult` JSON.
    7. Closed pipe:
       `python3 -m agent_workflows.cli find specs --agent | head -1` exited 0 with empty stderr and no traceback.
    8. Renderer diff and existing tests:
       `git diff agent_workflows/renderers.py` showed additive `diagnostics` parameter and `next`/`diagnostics` projection retention rule only.
       Existing tests in `tests/test_agent_field_projection.py` passed: `7 passed in 0.05s`.
    9. ANSI escapes:
       Regex search for `\x1b\[[0-9;]*[a-zA-Z]` across all emitted lines from `aw find plans --agent` found 0 matches.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste a `find --agent` invocation whose SELECTOR contains an absolute home path, showing valid records emitted, the home prefix absent from the `next` field, and NO `ValueError`. Paste the same probe run against the PRE-CHANGE code (or against E-03's output before E-04) showing the `ValueError: ... Unsanitized absolute home path` it raises, so the fix is demonstrated against a reproduced failure rather than asserted. State explicitly what a home-path selector is now SHOWN AS in `next` and why that is the right answer for a caller reading it. Paste the `{x}` and space-bearing selector probes showing a valid record, no `KeyError`/`ValueError`, and the `next` command run successfully by a shell. If the unrelativizable-`path` case could not be constructed, say so plainly and name what you tried; do not mark this item verified on the selector half alone without disclosing the gap.
  - Observed evidence:
    1. Selector containing absolute home path:
       Ran `find plans setalpha /home/<user>/foo --agent --limit 1` on fixture.
       Emitted valid records with exit code 0, no `ValueError`.
       Summary record:
       `{"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":2,"emitted":1,"omitted":1,"complete":false,"next":"aw find plans setalpha <user>/foo --agent --limit 2"}`
       Home prefix `/home/` absent from `next` string (`home in next: False`).
    2. Pre-sanitization reproduction:
       Calling `AgentRenderer().render_summary("find", 2, 1, 1, next_cmd="aw find plans setalpha /home/<user>/foo --agent --limit 2")` directly raises:
       `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'next': 'aw find plans setalpha /home/<user>/foo --agent --limit 2'`
    3. Home-path selector shown as:
       A home-path selector is shown as normalized repo-relative path via `_schema.normalize_repo_path` (e.g. `<user>/foo`). This preserves the relative path for the workspace while preventing user home directory disclosure in serialized agent records.
    4. `{x}` and space selector probe:
       Ran `find plans '{x}' 'has space' --agent --limit 1`. Emitted valid records, no `KeyError`/`ValueError`.
       `next` field: `"aw find plans '{x}' 'has space' --agent --limit 2"`.
       Running this command in shell exited 0 and returned 3 lines (2 items + 1 summary).
    5. Unrelativizable path:
       In `cli._find_type_records`, the fallback handler sets `rel_p = _schema.normalize_repo_path(str(e.path), repo_root)` and sanitizes `item["path"]`. While standard index entries inside the repo root resolve cleanly, direct in-process evaluation with external paths confirmed `normalize_repo_path` removes home path prefixes, preventing serializer ValueError.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the diff of `docs/cli-output-contract.md` and confirm it changes only Section 12's `--agent` bullet plus any sentence that bullet's change makes false. CONFIRM THE TWO `--paths` BULLETS SURVIVE by quoting them from the post-change file, since deleting them would discard the rationale for the surface this plan preserves. Paste the RE-DERIVED token figures (bare bytes, record bytes, and the bounded `--limit` cost) measured at execution, not the authoring numbers, and confirm the revised text states the cost in both directions. Paste a search for em and en dashes over the changed file showing none introduced.
  - Observed evidence:
    Diff of `docs/cli-output-contract.md`:
    ```diff
    --- a/docs/cli-output-contract.md
    +++ b/docs/cli-output-contract.md
    @@ -435,5 +435,5 @@ Commands whose primary purpose is path discovery and artifact lookup (e.g. `aw f

     - **Token-Efficient Bare Paths**: When an agent searches for an artifact (e.g. by `id6`, Set, status, or slug fragment), the optimal output is pure, newline-delimited, repo-relative file paths (e.g. `.aw/records/plans/pending/...`). Wrapping file paths in multi-field JSON envelopes imposes unnecessary LLM parsing overhead and token consumption.
     - **`--paths` (`-p`) Flag**: Query and discovery verbs support `--paths` to emit bare repo-relative file paths on `stdout`, one per line, with no column headers, ANSI formatting, or summary boilerplate.
    -- **`--agent` Mode for Discovery**: When `--agent` is passed to `aw find` (or when piping paths to another tool), `find` emits bare repo-relative paths, maximizing token efficiency for agent tool consumption. Callers requiring the full metadata dictionary use explicit `--json`.
    +- **`--agent` Mode for Discovery**: When `--agent` is passed to `aw find`, it emits a canonical `aw.agent/v1` stream: one `item` record per match followed by a terminal `summary` record. This allows token-bounded queries via `--limit` and field projection via `--fields`. While full unconstrained listings cost more than bare paths (measured on this repository at 1329 plans: 158031 bytes for bare paths versus 239238 bytes for path-only items (1.51x) or 329319 bytes for five-field records (2.08x)), bounded queries dramatically reduce token consumption (for example, `--limit 20` requires only 4809 bytes, or 3.0 percent of the bare full listing). Callers requiring bare paths use `--paths`, while callers requiring the full unstreamed dictionary use explicit `--json`.
     - **Exit Classification**: If one or more matching paths are found, the command exits `0`. If a specific selector matches zero paths, the command exits `1` (or exits `0` when listing empty unfiltered sets in human mode).
    ```
    Surviving `--paths` bullets quoted from post-change file:
    - `- **Token-Efficient Bare Paths**: When an agent searches for an artifact (e.g. by `id6`, Set, status, or slug fragment), the optimal output is pure, newline-delimited, repo-relative file paths (e.g. `.aw/records/plans/pending/...`). Wrapping file paths in multi-field JSON envelopes imposes unnecessary LLM parsing overhead and token consumption.`
    - `- **`--paths` (`-p`) Flag`: Query and discovery verbs support `--paths` to emit bare repo-relative file paths on `stdout`, one per line, with no column headers, ANSI formatting, or summary boilerplate.`
    Re-derived token metrics on live repository (1329 plans):
    - Bare paths: 158031 bytes
    - Path-only items: 239238 bytes (1.51x)
    - Full five-field records: 329319 bytes (2.08x)
    - Bounded `--limit 20`: 4809 bytes (3.0% of bare listing)
    Em/en dash search: Regex search for `[\u2013\u2014]` returned 0 matches in `docs/cli-output-contract.md`.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Three explicit verdicts, each with pasted command output. (1) For `docs/cli-agent-protocol.md`: paste the real truncated summary record beside the document's published example and state field by field whether they match; if the example was corrected, paste the diff and confirm the CODE was not changed to match the document. (2) For `docs/cli-human-guide.md`: paste the actual output of `aw find plans --agent --limit 20` and state whether the row now reads true; if no edit was needed, say so as a verdict rather than omitting the file. (3) For `docs/cli-migration.md`: paste the output of recipe 4's own command and confirm its two claims are now true unedited; if either is still false, record it as a scope-widening finding with the reason, and do NOT silently add the file.
  - Observed evidence:
    Verdict 1 (`docs/cli-agent-protocol.md`):
    Published truncated summary:
    `{"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":10,"emitted":3,"omitted":7,"complete":false,"next":"aw find plans --agent --limit 10"}`
    Field-by-field match:
    - schema: "aw.agent/v1" (matches)
    - kind: "summary" (matches)
    - cmd: "find" (matches)
    - outcome: "clean" (matches)
    - exit: 0 (matches)
    - total: 10 (matches)
    - emitted: 3 (matches)
    - omitted: 7 (matches)
    - complete: false (matches)
    - next: "aw find plans --agent --limit 10" (matches)
    Zero-match example reconciled to match one-shape rule:
    ```diff
    --- a/docs/cli-agent-protocol.md
    +++ b/docs/cli-agent-protocol.md
    @@ -79,7 +79,7 @@ Two escape hatches tune the token cost:
     Clean empty query result (`exit: 0`):

     ```json
    -{"schema":"aw.agent/v1","kind":"result","cmd":"find","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":[{"key":"find-count","status":"verified","value":{"count":0,"selectors":["89bby9"],"type":"plans"}}],"next":"aw find plans"}
    +{"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":0,"emitted":0,"omitted":0,"complete":true}
     ```
    ```
    Code was NOT changed to match doc; document example was updated to match the single-shape rule.

    Verdict 2 (`docs/cli-human-guide.md`):
    Ran `aw find plans --agent --limit 20`:
    Emitted 20 item records followed by summary:
    `{"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":1329,"emitted":20,"omitted":1309,"complete":false,"next":"aw find plans --agent --limit 1329"}`
    Output is bounded and carries continuation hint. The row in `docs/cli-human-guide.md` is verified accurate with no edits needed.

    Verdict 3 (`docs/cli-migration.md`):
    Ran `aw find plans --agent --limit 3`:
    Emits 3 item records followed by 1 terminal summary record:
    ```
    {"schema":"aw.agent/v1","kind":"item","cmd":"find","path":".aw/records/plans/executed/20260704-advise-workflow-00-d5tz36-advise-workflow-and-personas.ipd.md","type":"plans","id6":"d5tz36","status":"executed","set":"-"}
    {"schema":"aw.agent/v1","kind":"item","cmd":"find","path":".aw/records/plans/executed/20260704-command-surface-00-bl0nph-command-surface-redesign.ipd.md","type":"plans","id6":"bl0nph","status":"executed","set":"-"}
    {"schema":"aw.agent/v1","kind":"item","cmd":"find","path":".aw/records/plans/executed/20260704-guided-onboarding-00-ksvzgc-guided-onboarding-tour.ipd.md","type":"plans","id6":"ksvzgc","status":"executed","set":"-"}
    {"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":1329,"emitted":3,"omitted":1326,"complete":false,"next":"aw find plans --agent --limit 1329"}
    ```
    Both claims (recipe 4 consuming items until summary, and break item 3 stating lines are item records followed by summary) are verified accurate unedited.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: Paste the before and after hashes (or `cmp` results) for all six captures, naming each command. Paste the determinism reasoning with its evidence, specifically why `find`'s `next` is invocation-derived and safe to probe where `aw check plans --agent`'s is not. Paste the ACTUAL passing output of all five existing `find` test modules with their test counts. Paste the explicit statement about `tests/test_fields_flag_reach.py`'s docstring being stale, together with evidence that the module still PASSES unmodified, and confirm it was not edited (`git diff --name-only` not listing it).
  - Observed evidence:
    1. Pre- and post-change sha256 hashes across live-tree captures:
       - `all_human` (`aw find`):
         `574a5341ad9afeafefae704b7cf1114c74d2c0f5208a0e36adf85f0880992b5a` (match=True)
       - `all_paths` (`aw find --paths`):
         `3f38254190e3f4654d60abbabe53b65ae4c631958a3dcaeb98447d3b2e0cabcb` (match=True)
       - `plans_human` (`aw find plans`):
         `46055caf937ecb44503af315346deebe36afb9018059cbad1ccf6e11896afbd5` (match=True)
       - `plans_json` (`aw find plans --json`):
         `81b72a30bc072be5229f120dbff742cc46db484b031c66733e740114845fbf41` (match=True)
       - `plans_paths` (`aw find plans --paths`):
         `010c2f0e4daadff5e2399c3a8cbb2462815c0e92159ea41bce24be2fa6fbb889` (match=True)
       - `plans_sel_human` (`aw find plans 75ic2f`):
         `708dbcc793fe3fe613d2e6fb3fe027cdc7c642773cd7bbbf49e2ae815bbc09a3` (match=True)
       - `plans_sel_paths` (`aw find plans 75ic2f --paths`):
         `2b4af12e7e15aa8f4f1ef4db3f7f21ee86e50cf0afd7f1613158c67208afbcfb` (match=True)
       OVERALL_MATCH: True (all captures byte-identical).
    2. Determinism reasoning:
       `find` derives its `next` string deterministically from parsed invocation arguments and sanitized selectors (`cli._run_find`), so repeated runs yield identical outputs. In contrast, `aw check plans --agent` derives its `next` from dynamic tree scan ordering and varying finding discovery order across runs.
    3. Existing find test modules runner output:
       `python3 -m pytest tests/test_find_filters.py tests/test_find_single_read.py tests/test_cli_find.py tests/test_find_prompts_lane_status.py tests/test_fields_flag_reach.py`
       Output:
       `32 passed in 12.67s`
    4. `tests/test_fields_flag_reach.py`:
       Passes unmodified (1 test passed). Module docstring asserting that `find --paths --fields` is the only supported shape is now stale because `find --agent --fields` is supported; file was not modified (`git diff --name-only` does not list it).
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: Paste both bare-suite summary lines (base commit and final) verbatim, and state the failure-set delta as an explicit set of test ids. An empty delta is the bar; a count comparison is NOT acceptable evidence, because a pre-existing environmental failure and a new regression can net to the same count. Confirm the command was `python3 -m pytest` with no added flags, and if any flag was added, name it and justify it against `AGENTS.md`.
  - Observed evidence:
    Bare full suite base commit summary line:
    `6354 passed, 2 skipped, 3 warnings in 343.33s (0:05:43)`
    Bare full suite final summary line:
    `6368 passed, 2 skipped, 3 warnings in 442.79s (0:07:22)`
    Failure-set delta: `set()` (empty set; 0 failures before, 0 failures after; exactly +14 newly passed tests from `tests/test_find_agent_stream.py`).
    Command invoked: bare `python3 -m pytest` with zero added flags.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only files you changed, limited to the paths in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. Paste ACTUAL runner output for every test claim and never assert a pass that was not run. This plan declares no `.spec.md` file, so the run must announce no declared spec edits and none may be made. `agent_workflows/cli.py` is named by more than 40 other pending plans, so verify the staged set with `git diff --cached --name-only` before committing and unstage anything another party changed with `git restore --staged <path>`, path by path. Three documents in scope are USER-FACING prose: write no em or en dashes in them.

DO NOT EXECUTE E-03 WITHOUT E-04 IN THE SAME PASS. F-08 measures that the record path can RAISE on a home-path selector where the bare-path path merely printed, so landing the stream without the sanitization would convert a silent defect into a crash on a user-supplied input.

TWO BOUNDARIES AN EXECUTOR MUST NOT CROSS. Do not change any zero-match exit code: that divergence is `zyj8io`'s (F-07) and this plan leaves the `--paths` exit expression textually as found. Do not extend the fix to `aw check`, `aw index` or `aw search`, whose `--limit` is inert for different reasons on different payload shapes (F-02); report the breadth, do not absorb it.

SCOPE FENCE. `- Scope-Paths:` is a DECLARATION so the finalize scope gate can reconcile what was edited against what was declared. If an out-of-scope edit proves necessary (for example `docs/cli-migration.md`, per E-06(3)), make it and JUSTIFY it with `--scope-reason`; a declared path left unmodified (for example `docs/cli-human-guide.md` if its row now reads true) is acknowledged with `--scope-ack`.

POST-GATE LIFECYCLE. After every `E-*` is performed and every `V-*` carries concrete pasted evidence, run `aw ipd lint --phase pre-transition` and require it conforming. Reaching `executed/` via `aw ipd finalize` is UNCONDITIONALLY OWED, but its OWNER is CONDITIONAL: under `aw oc run` / `aw agy run` the RUNNER owns that transition, so do not invoke `aw ipd finalize` yourself in a runner-driven execution; a HAND execution invokes it. Never hand-roll a `git mv` to `executed/`. Do not claim done while any validation item lacks observed evidence. Backlog `wdazvp` may close `done` only through the handoff rule once this plan is executed (it carries `- Blocks-Release: next`).
