# IPD: Bound the stranded-lane detail by construction with a reusable deterministic composer, not by a shortened sentence

- Date: 2026-10-01
- Kind: child
- Concern: Backlog `0livgf` residue 2. `attention.stranded_lane_drift` composes its `detail` as `"; ".join(bits)` plus the record's `why` plus `lane_remedy_hint`, and executed plan `mc6r92` bounded it by SHORTENING ONE SENTENCE to fit a 108-character budget derived from the worst prefix then observable. That budget is not a property of the assembly: the prefix embeds a `run_id`, a repository-relative worktree path, an `integration_signal` and a `commits_ahead` count, each of which can grow. Re-measured in this lane, the worst LIVE row is 297 of 300 (a margin of 3 characters) and the worst prefix REACHABLE from shapes already present in this tree composes to 370, which exceeds the bound by 70. `mc6r92` recorded this honestly and declined to close it, naming this item as carrier.
- Scope: Add ONE deterministic budget-spending composer to `attention_contract` and route `stranded_lane_drift` through it, so the lane detail is within the bound for EVERY input by arithmetic rather than for the shapes the corpus happens to exhibit. Convert the existing case (c) from a recorded observation into a real bound assertion. EXCLUDES validating `detail` inside `artifact_core.Drift` (Order 02 owns that), excludes changing `MAX_DESCRIPTIVE_LEN` or `is_safe_descriptive`, and excludes every other `Drift` producer.
- Scope-Paths: agent_workflows/attention_contract.py, agent_workflows/attention.py, tests/test_attention_lane_detail_bound.py, CHANGELOG.md
- Item-Dependencies: none
- Status: not-executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 0livgf
- Set: driftbound
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 9sbfea

## Workflow history
- 2026-10-07 not-executed (aw set): Maintainer ruling 2026-10-07: do not length-enforce tool-composed drift details; sibling 62pkkg already retired not-executed and backlog 0livgf closed. Retiring the rest of Set driftbound.
- 2026-10-07 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006. Reviewed at HEAD `fe2ee961c` in an isolated review lane; plan byte-identical to the lane input, so no pre-review snapshot. Re-measured (gitignored probe): 5 live lane rows, max 262, all safe; 387 run dirs, longest run_id 28; longest worktree name 41; same four signals; existing case (c) composes to 373 through the real producer; `7stpjm` done via executed `lxcexr`, over-bound population now 1 of 123. Prototyped the single-budget composer: sweep bound holds, but pass-through equals today's row only when each segment carries its own joiner. Fixed: composer segment/joiner contract and elided shapes specified so the byte-identical claim is achievable (PR-001); live figures re-measured and the 'live row byte-identical' bar made conditional on re-derivation (PR-002); 7stpjm carrier evidence cited (PR-003); revert route made shared-checkout-safe (PR-004); gate given paste-output rule, scope-fence declaration, conditional finalize ownership and Readiness ownership (PR-005); CHANGELOG ownership assigned to E-04 with V-04 evidence, suite bar compared by failure set, OQ owners recorded (PR-006).
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `0livgf`, which carries two deferred rows from executed plan `mc6r92`. This plan owns residue 2 (the lane prefix is not bounded by construction); Order 02 owns residue 1 (no producer-side refusal). THE ITEM'S DIAGNOSIS REPRODUCES AND TWO OF ITS FIGURES HAVE MOVED, which is recorded rather than inherited. The item says the live prefix runs 116 to 147 characters; measured here the worst composed row is 297 of 300 and the worst prefix REACHABLE from shapes in this tree composes to 370 (F-03, F-04), so the residual is live and the margin is 3 characters rather than the 65 to 93 `mc6r92` measured. THE ITEM'S CITATION IS WRONG AND IS CORRECTED: it says `agent_workflows.core.Drift`, but `agent_workflows/core.py` does not exist; the symbol is `artifact_core.Drift`, reached through the module alias `core` (F-01). AUTHORING ALSO REFUTED THE ITEM'S IMPLIED REMEDY. The item says closing this "means budgeting or eliding the prefix's variable segments", and measurement shows a PER-SEGMENT CAP SCHEME CANNOT WORK: the fixed skeleton costs 181 characters, leaving 119 for four variable segments that need 170 on a row live TODAY, so fixed caps would clip a currently-clean row (F-06). A single budget spent in priority order does work, and is prototyped at 297 worst case with today's rows byte-identical (F-07). OQ-01 is resolved from that measurement; OQ-02 records the one judgement a reviewer should attack, which is the priority order itself.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the composed stranded-lane `detail` satisfy the Section 8.8 descriptive bound for every reachable input, proven by arithmetic over a declared budget rather than by observation of the current corpus, while leaving every row the live tree produces today byte-identical.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the composer

- [ ] E-01 Re-derive the measurements in F-03, F-04 and F-06 at execution HEAD before writing any code, and record the numbers in this plan's `V-01` evidence. Specifically: the composed length of every live lane row, the longest `run_id` under the resolved runs root, the longest `.aw/worktrees` directory name, and the set of `integration_signal` values present.
  WHY THIS IS AN E-ITEM AND NOT A PREAMBLE. Every number in F-03 through F-07 is a LIVE CORPUS MEASUREMENT, not an acceptance bar, and `mc6r92` was burned by exactly this: it derived a 108-character sentence budget from the worst prefix then observable, and that prefix has since grown. If the re-derived worst case already exceeds 300 at execution time, that is a stronger motivation and not a reason to stop; if a `run_id` or worktree name longer than those recorded here has appeared, the E-02 budget arithmetic must be checked against the new value rather than the one in F-04.
  DO NOT TREAT ANY NUMBER IN THIS PLAN AS A THRESHOLD TO ASSERT. The only assertion this plan makes is `len(detail) <= MAX_DESCRIPTIVE_LEN`, which is a constant the contract owns. A test that pins 297, or 370, or any other measured value, pins a corpus and will rot exactly as `mc6r92`'s budget did.
  - Depends on: none
  - Expected outcome: a recorded table of the four measurements taken at execution HEAD, with the command or snippet that produced each, plus an explicit statement of whether the worst reachable composition exceeds `MAX_DESCRIPTIVE_LEN` at that HEAD.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/attention_contract.py`, add `compose_bounded_detail(segments, trailer, *, limit=MAX_DESCRIPTIVE_LEN)` beside `escape_detail` in the output-safety region: a pure function that spends ONE budget over the segments in the order given, keeping each whole segment that fits, clipping at most one with an explicit marker, dropping the remainder, and always preserving `trailer` intact.
  EACH SEGMENT MUST CARRY ITS OWN LEADING JOINER, because today's row is NOT a uniform join. `stranded_lane_drift` assembles `"{0}: {1}. {2}".format("; ".join(bits), why, lane_remedy_hint(...))`, so the `why` is introduced by `": "`, closed by `"."`, and the trailer by `" "`. A composer that joins every segment with `"; "` cannot reproduce that string, and E-04's byte-identical claim would be false on every live row. So the segment shape is `(joiner, text, min_keep)` (or an equivalent the executor documents), the first kept segment's joiner is omitted, and the trailer is passed with its own leading separator. Verified at review on 2026-10-07 by prototype (gitignored `.aw/state/` scratch): with per-segment joiners `("; ", bit)` for each bit and `(": ", why + ".")` for the sentence, and trailer `" " + hint`, the pass-through output equals today's `format(...)` byte for byte, while a uniform `"; "` join does not. ALSO SPECIFY THE ELIDED SHAPE: when the `why` segment is dropped entirely, the row ends `<last kept bit> <trailer>` with no dangling `": ."`; when it is clipped, it ends `<prefix>... <trailer>`. Both shapes must appear in E-03's cases.
  THE INVARIANT IS ARITHMETIC AND MUST BE STATED IN THE DOCSTRING AS SUCH: the return value is at most `limit` characters for EVERY input, because the budget is decremented by the real cost of each kept segment (including its separator) and the trailer plus joiners are reserved before the first segment is considered. This is the whole point of the change. A function that merely usually fits is what the repository already has.
  THE TRAILER IS RESERVED FIRST AND NEVER CLIPPED, because it is the REMEDY. `mc6r92` measured `lane_remedy_hint` at 41 characters and left it alone for the right reason: a row that reports a problem and loses its recovery command trains its own dismissal (the reasoning `attention.lane_remedy_hint` already records for why it probes a verb that exists). So the signature takes the trailer separately rather than as the last segment, and REFUSES when the trailer alone cannot fit the limit, which is a programming error rather than a data condition.
  CLIP AT MOST ONE SEGMENT, AND MARK IT. A scheme that clips several produces the garbage this plan's prototyping produced when it shrank largest-first: three mangled locators and an empty sentence. One clip plus a marker tells the reader that something was removed, following the same in-repo reasoning as `evaluate_durable_carrier`'s `(and N more)` tail and `term.truncate_visible`'s explicit `ellipsis`.
  DO NOT USE `term.truncate_visible` HERE. It truncates by VISIBLE COLUMNS and preserves ANSI, which is correct for a terminal cell and wrong for this bound: `is_safe_descriptive` counts CHARACTERS, so a column-based clip cannot discharge a character-based bound, and `attention_contract` must not acquire a dependency on the terminal module to compute a contract value.
  A SEGMENT MAY DECLARE A MINIMUM below which clipping is pointless, so a locator is DROPPED rather than reduced to `ru...`. Take it per segment rather than as a module constant; the useful floor for a run id is not the useful floor for a sentence.
  - Depends on: none
  - Expected outcome: `A.compose_bounded_detail` exists as a pure function with no I/O and no import of `attention`, `term` or `artifact_core`; for every input it returns a value of at most `limit` characters; a segment list that already fits is returned with every segment whole and byte-identical to the joiner-plus-text concatenation (and, for lane-shaped input, to today's `format(...)` assembly); and the function raises (rather than returning an over-bound value) when the trailer alone exceeds the limit.
  - Execution state: pending

- [ ] E-03 Add direct unit coverage for `compose_bounded_detail` in `tests/test_attention_lane_detail_bound.py`, including a PROPERTY-STYLE case that drives it over a deterministic sweep of adversarial segment lengths and asserts the bound holds on every one.
  THE SWEEP IS WHAT MAKES THIS A STRUCTURAL CLAIM RATHER THAN THREE MORE PER-SITE PINS. Iterate segment counts and lengths deterministically (no randomness, so a failure reproduces), including: a single segment longer than the whole limit, a trailer exactly at the limit minus one, every segment at its declared minimum, an empty segment list, and a segment list whose total is exactly `limit`. Assert `len(result) <= limit` and `A.is_safe_descriptive(result)` for every case.
  ASSERT THE PASS-THROUGH PROPERTY TOO, or the suite stays green for a function that clips everything. A segment list that fits must come back byte-identical to the concatenation of each segment's joiner and text (first joiner omitted) plus the trailer. ALSO assert, for at least one realistic lane-shaped input, equality with today's literal assembly `"{0}: {1}. {2}".format("; ".join(bits), why, hint)`, because that is the property that lets E-04 claim today's rows are unchanged; a pass-through against a uniform `"; "` join does NOT prove it.
  NO SOURCE INTROSPECTION. Per GUIDING_PRINCIPLES P16 and the repository's code-pinning prohibition, call the function and assert on returned strings; do not read `attention_contract`'s source, count callers, or assert on docstring text.
  - Depends on: E-02
  - Expected outcome: new test cases that FAIL if the budget arithmetic is wrong (demonstrate by temporarily perturbing the reserve by one character and pasting the failure) and pass against the real implementation.
  - Execution state: pending

### Task group 2: route the producer through it

- [ ] E-04 In `agent_workflows/attention.py`, rewrite `stranded_lane_drift`'s detail assembly to build its bits as PRIORITIZED segments and compose them through `A.compose_bounded_detail`, with `lane_remedy_hint(...)` passed as the trailer. Keep `A.escape_detail` applied LAST, and keep the bound satisfied after escaping.
  THE PRIORITY ORDER IS THE CONTRACT DECISION IN THIS PLAN and OQ-02 records it for attack. Proposed order, highest first: the lane state, the plan `id6`, the worktree display, the run identity, the `commits_ahead` count, the dirty marker, the `integration_signal`, and the `why` sentence LAST. The reasoning is that the row's JOB is to let an operator find the lane and act: state and `id6` name it, the worktree and run identity locate it, and the `why` is the one part the RULE ID already summarizes (`attention.lane-stranded` versus `attention.lane-superseded` versus `attention.lane-unknown`), so it is the cheapest thing to lose. An operator who needs the full sentence can run the verb the trailer names.
  ESCAPING AFTER COMPOSING IS A REAL HAZARD, NOT A STYLE NOTE, AND IT IS THE ONE THING MOST LIKELY TO BE GOT WRONG HERE. `A.escape_detail` LENGTHENS its input (measured: a 300-character all-backslash value escapes to 600), so composing to exactly 300 and then escaping can produce an over-bound value. Compose against a limit that reserves for escaping, or escape each segment BEFORE composing. Whichever route is taken, E-05 must assert the bound on the value that actually reaches the `Drift`, not on the pre-escape intermediate. This is precisely the trap `mc6r92` did not have to face, because it never claimed a general bound.
  THE LIVE ROWS MUST COME OUT BYTE-IDENTICAL, and that is checkable rather than hopeful: if every live row re-derived in E-01 is within the bound (297 at authoring, 262 at review on 2026-10-07), the pass-through property E-03 pins means no live row is clipped. Paste a before-and-after comparison over the real tree. If E-01 finds a live row already OVER the bound, that row is expected to change (it is the defect being fixed) and must be named as the one exception in the comparison.
  DO NOT CHANGE THE SENTENCES in `runner_shared.classify_lane_integration`. `mc6r92` already shortened the SUPERSEDED `why` to fit its budget; this plan makes the shortening unnecessary rather than compounding it, and re-editing that text would mix a wording change into a structural one. If a reviewer wants the fuller pre-`mc6r92` sentence restored now that the composer protects it, that is a separate change with its own operator-facing judgement.
  DO NOT CHANGE `lane_drift_severity`, the three rule ids, the `out.sort` key, or the `Drift` construction shape. The only change is how `detail` is built.
  - Depends on: E-02
  ALSO WRITE THE SET'S ONE `CHANGELOG.md` ENTRY HERE (the user-visible effect: an over-long lane row now elides with a marker instead of overflowing the bound), with no em or en dash.
  - Expected outcome: `attention.stranded_lane_drift` composes through `A.compose_bounded_detail`; every lane `Drift` it returns satisfies `A.is_safe_descriptive` AFTER escaping; the rows produced against the real tree are byte-identical to the pre-change rows; and `CHANGELOG.md` carries one entry describing the elision.
  - Execution state: pending

- [ ] E-05 Convert the existing case (c) in `tests/test_attention_lane_detail_bound.py` from a recorded observation into a real bound assertion, and add a case built from the WORST REACHABLE shapes E-01 re-derived (longest run id, longest worktree name, longest signal, a multi-run count, a dirty lane) asserting the bound holds.
  THIS IS THE DELIBERATE REVERSAL OF A DECISION `mc6r92` MADE, AND IT MUST BE RECORDED AS ONE RATHER THAN DONE QUIETLY. That file carries the comment `# of is_safe_descriptive; DO NOT assert len(drift.detail) <= MAX_DESCRIPTIVE_LEN` on case (c), and `mc6r92` E-03 explains why: asserting the bound there would have forced the `why` down to 36 to 74 characters, gutting the message. That reasoning was correct FOR THAT PLAN, whose only lever was the sentence length. It no longer holds once the composer can drop a segment, which is exactly what this plan adds. Replace the comment with one naming this plan and stating why the prohibition lifted.
  ADD A CASE THAT EXCEEDS THE BOUND BEFORE COMPOSING. Construct a lane record whose naive `"; ".join` composition is provably over 300 (the F-04 shape composes to 370) and assert that the real producer returns a conforming row for it. Without this case the suite cannot tell the composer from the old assembly, because every live row already fits.
  DRIVE THE REAL PRODUCER, NOT THE COMPOSER, in these cases. E-03 covers the composer directly; these cases exist to prove the PRODUCER is wired to it, which is a different claim and is the one that regressed in `mc6r92`'s F-02 finding (nothing applied the predicate at the producer).
  - Depends on: E-04
  - Expected outcome: case (c) asserts the bound; a new worst-reachable case asserts the bound on a shape whose naive composition exceeds it; both FAIL against the pre-E-04 producer (paste that run) and pass after; and the bare suite's failure set BY NAME equals a baseline re-derived at execution HEAD before any edit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE BOUND AND THE ESCAPE ARE DIFFERENT CONTRACTS AND THE DISTINCTION IS THE WHOLE BUG. `attention_contract.is_safe_descriptive` is the Section 8.8 predicate (bounded, single-line, control-char-free) and `attention_contract.escape_detail` escapes backslash, tab, newline and carriage return for the single-line agent record. Passing `escape_detail` proves NOTHING about the bound, and `escape_detail` can push a conforming value over it. `mc6r92` states this distinction explicitly in its conventions section; this plan is the first to have to act on it.
- OVER-LENGTH IS A VIOLATION, NEVER A SILENT TRUNCATION. Spec Section 8.8: "Over-length values are a contract violation, not silently truncated." That governs an AUTHORED descriptive field, and it is why this plan ELIDES with an explicit marker in a TOOL-COMPOSED string rather than hard-clipping: the marker is what makes the elision visible to the reader instead of silent. A plan that quietly truncated here would be arguing against the spec rather than implementing it.
- ELISION WITH AN EXPLICIT MARKER IS AN ESTABLISHED IN-REPO PATTERN, not a new idea: `check_engine.evaluate_durable_carrier` enumerates five locators then appends `(and N more)`, `check_engine._IPD_LINT_SHOWN` does the same for lint diagnostics, and `term.truncate_visible` takes an explicit `ellipsis`. The constant beside `_IPD_LINT_SHOWN` also records WHY a bound exists ("a per-diagnostic Drift would let one badly-formed plan add dozens of lines"), which is the same reasoning class as this bound.
- THE PRODUCER MUST NOT PRINT AN ABSOLUTE PATH. `stranded_lane_drift`'s docstring records that `location` is a branch ref and the worktree is rendered repository-relative through `runner_shared.lane_worktree_display`, because `preserved_worktree` is an absolute home path. A composer that clips a path must not change which path is chosen, and the leak-sanitizer (`aw sanitize --agent`) is the check.
- A LANE ROW'S SEVERITY IS LOAD-BEARING: `attention.lane_drift_severity` returns `info` for SUPERSEDED (so it does not fail the gate) and `error` otherwise, and its docstring records the measured reason. Nothing in this plan may change that, because the worst-case row measured here IS a SUPERSEDED one.
- THE SUITE RUNS BARE: `python3 -m pytest`, with `addopts` already supplying `-q -n auto --dist=worksteal` and the marker deselection. Do not add `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md).

## Findings

Every finding below was driven in this lane at HEAD `f5bba04b`. Each names the command or snippet that produced it.

| Id | Finding | Evidence |
|---|---|---|
| F-01 | **THE BACKLOG ITEM'S CENTRAL CITATION IS WRONG AND IS CORRECTED HERE.** The item says `agent_workflows.core.Drift` twice. There is no `agent_workflows/core.py`. The symbol is `artifact_core.Drift`, which `attention` imports under the alias `core`, which is where the item's name came from. Every other claim in the item survived checking. | `ls agent_workflows/core.py` reports no such file. `agent_workflows/artifact_core.py` defines `class Drift(NamedTuple)` with fields `location`, `rule`, `detail` plus six optional metadata fields. `attention.py` imports it as `core`. |
| F-02 | The item's mechanism claim is CONFIRMED: `is_safe_descriptive` is applied to no composed drift detail anywhere. Its callers validate AUTHORED fields only (`specs`, `backlog`, `check_engine` evidence). The lane producer calls `escape_detail`, which does not bound length. | `rg` for `is_safe_descriptive` across `agent_workflows/` returns call sites in `attention_contract` (inside `validate_gate_ref`), `backlog` (summary, gate summary, close evidence, and a write-path refusal helper), `specs` (summary, gate summary, evidence, write-path helper) and `check_engine` (evidence citation). None takes a `Drift.detail`. |
| F-03 | **THE LIVE MARGIN IS 3 CHARACTERS, not the 65 to 93 `mc6r92` recorded.** Six live lane rows; the worst is a SUPERSEDED row at 297 of 300. All six pass `is_safe_descriptive` today, so the `mc6r92` fix holds, barely. RE-MEASURED AT REVIEW (HEAD `fe2ee961c`, 2026-10-07): five live rows, all `attention.lane-stranded`, lengths 262, 241, 241, 241, 241, all safe; no SUPERSEDED row is live. The margin moves with the corpus, which is the plan's thesis, not a counter to it. | `attention.stranded_lane_drift(Path('.'))` over this tree returns lengths 297, 221, 212, 212, 212, 212, all `is_safe_descriptive` True. The 297 row is `attention.lane-superseded` on `aw/lane/3brgb6`. |
| F-04 | **THE WORST REACHABLE COMPOSITION EXCEEDS THE BOUND BY 70 CHARACTERS, USING ONLY SHAPES PRESENT IN THIS TREE.** The prefix alone reaches 220 and the full detail 370. So residue 2 is live, not theoretical. | Composed from measured maxima: longest `run_id` is 28 characters over 353 run directories, longest `.aw/worktrees` directory name is 34 over 40 entries, `integration_signal` values are `driver-run-suite`, `suite-failed`, `verifier`, `verifier-declined` (max 17). With a multi-run count, a dirty lane and the SUPERSEDED `why` (105 characters) plus the 41-character trailer: prefix 220, total 370. RE-MEASURED AT REVIEW (2026-10-07): 387 run dirs (longest `run_id` still 28), 15 worktree entries (longest now 41), the same four signals; and the EXISTING case (c) fixture in `tests/test_attention_lane_detail_bound.py` already composes to 373 through the real producer (`-s` output: `composed length=373 ... 73 over bound`), so the over-bound shape is reproducible in-suite today. |
| F-05 | The trailer is NOT a long part and must not be touched. `lane_remedy_hint('abc123')` is 41 characters and returns the remedy an operator acts on. `mc6r92` F-03 reached the same conclusion against the item's framing. | `len(attention.lane_remedy_hint('abc123')) == 41`, value `Recover it with \`aw oc integrate abc123\`.` |
| F-06 | **A PER-SEGMENT CAP SCHEME CANNOT WORK, which refutes the remedy the backlog item implies ("budgeting or eliding the prefix's variable segments").** The fixed skeleton costs 181 characters, leaving 119 for four variable segments that need 170 on a row that exists TODAY. So any fixed cap set small enough to bound the worst case clips a currently-clean row. | Skeleton cost computed over the maximal bit set (state, plan, commits, dirty, signal label, worktree label, run label, joiners, trailer) = 181; `300 - 181 = 119`. The live 297-character row needs signal 17 + worktree 20 + run 28 + why 105 = 170. A prototype with caps 48/34/28/96 produced a 387-character worst case AND clipped the live row's `why`. |
| F-07 | **A SINGLE BUDGET SPENT IN PRIORITY ORDER DOES WORK, prototyped.** Worst case 297 (under the bound), and the live row comes out byte-identical to today's 297-character string. This is the design E-02 and E-04 implement. | Prototype `compose_bounded(head_segs, why, trailer)` reserving the trailer and the joiners first, then spending one budget in priority order with a single marked clip: on the F-04 worst shape it returns 297 characters; on the live `3brgb6` shape it returns the current string unchanged. |
| F-08 | **`escape_detail` CAN PUSH A CONFORMING VALUE OVER THE BOUND**, so compose-then-escape is unsafe and E-04 must handle the order. This hazard is new to this plan, because `mc6r92` never claimed a general bound. | `len(A.escape_detail('\\\\'*300)) == 600`. A 300-character value containing a tab and a newline escapes to 302 and fails `is_safe_descriptive`. |
| F-09 | Escaping is a NO-OP on every live lane row today, so the F-08 hazard is latent rather than active, and a test that only drives live shapes cannot see it. | Re-escaping each of the six live details changes its length by 0. |
| F-10 | The existing test file pins the bound for cases (a) and (b) and DELIBERATELY DOES NOT for case (c), with the prohibition written in a comment. This plan reverses that decision, which is why E-05 must replace the comment rather than delete it. | `tests/test_attention_lane_detail_bound.py` carries `# of is_safe_descriptive; DO NOT assert len(drift.detail) <= MAX_DESCRIPTIVE_LEN` on case (c) and asserts only single-line and control-char-free there. The file is 3 tests and passes today. |
| F-11 | The over-bound population on OTHER rules has GROWN from the 12 the item records to 25 of 71 findings, longest 974, split 15 `info` / 10 `error`, still exactly two rules. This matters here only as a BOUNDARY: this plan touches none of it, and Order 02 must re-derive it rather than inherit either number. RE-MEASURED AT REVIEW (2026-10-07): plan `lxcexr` (backlog `7stpjm`, now `done`) has executed, and `check all --json` now reports 1 over-bound finding of 123 (`check.ipd-carrier-finished-unverified`, 329 characters). | `python3 -m agent_workflows check all --json`, exit 1, 71 diagnostics; 25 exceed `MAX_DESCRIPTIVE_LEN`: `check.ipd-carrier-finished-unverified` (15, `info`) and `check.ipd-uncarried-obligation` (10, `error`); max length 974. |
| F-12 | `compose_bounded_detail` can live in `attention_contract` without an import cycle, which is what makes it reusable by Order 02 rather than private to `attention`. `attention_contract` imports only `re`, typing and `lifecycle_dirs`, and `lifecycle_dirs` imports no artifact module. | `python3 -c "from agent_workflows import attention_contract as A; from agent_workflows import artifact_core as C"` succeeds in either import order; importing `lifecycle_dirs` alone loads only `versioning`, `_compat` and the package root. |
| F-13 | **A LIVE PENDING PLAN IS EDITING `attention_contract.py` AND `attention.py` AND AMENDING THE SAME SPEC**, so the overlap is real and is addressed in OQ-03 rather than discovered at execution. | Pending plan `qpw45x` (Set `llnvwj`, Order 1, `- Status: to-review`) declares `- Scope-Paths: agent_workflows/attention_contract.py, agent_workflows/attention.py, tests/test_attention_output_safety.py, .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md, CHANGELOG.md`. It adds `neutralize_control_characters` and `escape_markdown_inline` to the same output-safety region and applies them to `detail_text` at three BOARD sites. |
| F-14 | A second live Set EXCLUDES the change Order 02 would otherwise be tempted to make, and this plan must not make it either. | Pending orchestrator `xhr0dj` (Set `qbz8i1`) excludes, "in every child without exception: minting a new rule id, changing `attention_contract.is_safe_descriptive` or `MAX_DESCRIPTIVE_LEN`". This plan changes neither; it ADDS a function beside them. |

## Proposed changes (ordered, validatable)

1. Re-derive the four live measurements at execution HEAD and record them (E-01).
2. Add `compose_bounded_detail` to `attention_contract` as a pure, arithmetically-bounded composer (E-02).
3. Cover it directly, including a deterministic adversarial sweep and the pass-through property (E-03).
4. Route `stranded_lane_drift` through it with a declared priority order, handling the escape-growth hazard (E-04).
5. Turn case (c) into a real bound assertion and add a worst-reachable case (E-05).
6. Record the change in `CHANGELOG.md` (E-04).

## Deferred / out of scope (with reason)

- **Validating `detail` inside `artifact_core.Drift`.** That is residue 1 of the same backlog item and is a repository-wide contract change: F-11 measures 25 live over-bound findings on two other rules that a producer-side refusal would red at once. It is this Set's Order 02, which declares the dependency on this plan.
  - Carrier: 0livgf
- **The 25 over-bound `check.ipd-uncarried-obligation` and `check.ipd-carrier-finished-unverified` findings.** This plan touches neither rule. The population is backlog `7stpjm`'s, and Order 02 cannot refuse at the producer until it is clean. `7stpjm` is now `done`, discharged by executed plan `lxcexr`, which brought that population inside the bound (F-11 re-measurement).
  - Carrier: 7stpjm
  - Carrier-Evidence: .aw/records/plans/executed/20261001-7stpjm-01-lxcexr-bring-every-carrier-obligation-check-detail-inside-the-secti.ipd.md
- **Restoring the fuller pre-`mc6r92` SUPERSEDED `why` sentence now that the composer would protect it.** `mc6r92` E-02 shortened that sentence to fit a budget this plan makes unnecessary, so the shortening is now arguably over-cautious. Deliberately NOT done here: it is an operator-facing wording decision about what every superseded row reads, it would mix a content change into a structural one, and this plan's byte-identical-output claim depends on not touching it.
  - Carrier-Declined: nothing is owed, because no defect remains. The current sentence is correct and in bound; a longer one would be a readability improvement with no contract behind it, and `runner_shared.classify_lane_integration` is where a future author who wants it will look. Filing a record would leave an open item whose only content is a preference.
- **Markdown-escaping or control-character-neutralizing the lane detail at the board.** That is pending plan `qpw45x`'s declared work on the same two files (F-13), and it concerns a DIFFERENT Section 8.8 bullet (deterministic escaping per surface) from this plan's (bounded, single-line). Doing it here would race a live plan.
  - Carrier: llnvwj
- **Bounding any other `Drift` producer's detail.** 171 construction sites exist across 10 modules; this plan changes one. Each other site is either already short or is Order 02's census problem.
  - Carrier: 0livgf

## Scope check

- Over-scope: none. Every declared path is written by at least one E-item: `attention_contract.py` by E-02, `attention.py` by E-04, `tests/test_attention_lane_detail_bound.py` by E-03 and E-05, and `CHANGELOG.md` by E-04 (the Set's one user-facing note).
- Under-scope: residue 2 of backlog `0livgf` is fully covered (the prefix becomes bounded by construction, and the test that recorded the residual now asserts it). NOT covered, each with a reason recorded in Deferred above: residue 1 (Order 02), the 25-finding population (`7stpjm`), the board's escaping bullet (`qpw45x`), and every other producer.

## Required tests / validation

- `python3 -m pytest tests/test_attention_lane_detail_bound.py` must pass, and the new cases must FAIL against the pre-change producer with both runs pasted.
- `tests/test_attention.py` and `tests/test_attention_contract.py` must stay green: both drive the surfaces this plan changes.
- The full suite, run BARE as `python3 -m pytest`, with the `N passed` summary line pasted; re-derive the baseline at execution HEAD before any edit and compare FAILURE SETS BY NAME, not counts.
- A byte-comparison of every live lane row before and after (the set re-derived in E-01; six at authoring, five at review), proving no in-bound live row changed.
- `python3 -m agent_workflows attention --check --json` over this tree: exit code and lane-row count unchanged from the pre-change run, and every row's `detail` within the bound.
- `aw sanitize --agent` clean, because the composer touches a string that carries a worktree path.
- `aw check` and `aw ipd lint` on this plan.

## Spec / documentation sync

NO SPEC AMENDMENT IS REQUIRED BY THIS PLAN, and the reason is worth stating because the sibling Order 02 reaches the OPPOSITE conclusion on the same spec. Section 8.8 already requires that a descriptive field be bounded; this plan makes one composed value comply with the bound as the contract already states it, which needs no new contract text. What Order 02 does is EXTEND 8.8's subject from authored artifact metadata to a tool-composed `Drift.detail`, and that is a contract change which must be declared. Keeping the amendment in exactly one plan also avoids two plans in one Set editing the same `.spec.md`.

`CHANGELOG.md` carries one entry for the Set, written here because this is the plan with the user-visible effect (a very long lane row now elides rather than overflowing).

## Open questions

### OQ-01: Per-segment caps, or one budget spent in priority order?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED as ONE BUDGET, on measurement rather than preference, and this contradicts the remedy the backlog item implies. The item says closing residue 2 means "budgeting or eliding the prefix's variable segments", which reads as a per-segment cap. F-06 measures that this cannot work: the fixed skeleton costs 181 characters, leaving 119 for four variable segments that need 170 on a row present in the tree today, so any cap set tight enough to bound the F-04 worst case (370) necessarily clips a clean row. A prototype with generous caps still produced a 387-character worst case while mangling the live row. A single budget spent in priority order is bounded by construction AND leaves every live row byte-identical (F-07), so it dominates on both criteria.

### OQ-02: Is `why` the right thing to lose first?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED as YES, and this is the judgement a reviewer should attack first, because it decides what an operator reads on a pathological row. The argument: the row exists so an operator can FIND and ACT on a lane, the rule id already carries the classification the sentence elaborates (`attention.lane-stranded` says work is at risk, `attention.lane-superseded` says prune a husk, `attention.lane-unknown` says the question is unresolved), and the trailer names the verb that recovers it. The locators (`id6`, worktree, run id) cannot be reconstructed from anything else on the line, so losing one costs more than losing the sentence. The honest cost: on a row long enough to trigger elision, the operator sees a marked, truncated explanation and must run the named verb for the full story. The alternative order (keep the sentence, drop a locator) was rejected because a row that explains a lane you cannot locate is not actionable. Note this only ever engages past 300 characters; F-03 measures that no live row reaches it (at authoring and again at review).

### OQ-03: How does this plan avoid racing pending plan `qpw45x`, which declares the same two files?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED, and no `- Item-Dependencies:` edge is declared, deliberately. F-13 measures the overlap as FILE-LEVEL but not SEMANTIC: `qpw45x` adds `neutralize_control_characters` and `escape_markdown_inline` to `attention_contract` and applies them at three BOARD rendering sites (`_render_item_row` twice, `_render_table_row`); this plan adds `compose_bounded_detail` to the same region and changes one PRODUCER (`stranded_lane_drift`). The functions are disjoint, the call sites are disjoint, and neither changes `is_safe_descriptive`, `MAX_DESCRIPTIVE_LEN` or `_CONTROL_CHAR_RE`. The runner isolates each execute item in its own worktree and merges through a revalidation gate, so a textual overlap in the same file is not a hazard (AGENTS.md, "The runners own ordering, isolation, and orchestrators"); declaring a dependency would serialize two independent changes for no reason and could stall this plan behind one that is not approved. The one real interaction is the SPEC FILE, and it does not arise: `qpw45x` amends Section 8.8's escaping bullet and this plan amends nothing (see Spec sync), so only Order 02 and `qpw45x` touch that file, in different bullets.

### OQ-04: Should the composer be reused by Order 02 to fix the 25 over-bound findings?

- Blocking: no
- Status: deferred
- Owner: Order 02 of this Set (`62pkkg`); triggered when that plan decides how to bring `check_engine.evaluate_durable_carrier` into bound
- Resolution or deferral rationale: DEFERRED to Order 02 because it is that plan's decision and it has a genuine alternative. `compose_bounded_detail` is placed in `attention_contract` rather than inside `attention` precisely so it CAN be reused (F-12 confirms no import cycle blocks it), and the `evaluate_durable_carrier` detail has the same shape this composer handles (a count, a joined enumeration, and an elision marker it already writes by hand as `(and N more)`). But the alternative for that site is to reduce the enumeration cap from five, which backlog `7stpjm` names as a route and which needs no composer at all. Choosing between them requires measuring what an operator loses from each, which is work this plan does not do and must not pre-empt.
- Carrier: 0livgf

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the four re-derived measurements with the command or snippet that produced each: (a) the composed length and rule of every live lane row from `attention.stranded_lane_drift` over the execution tree; (b) the longest `run_id` under the resolved runs root with the directory count; (c) the longest `.aw/worktrees` entry name with the count; (d) the distinct `integration_signal` values. Then state explicitly whether the worst reachable composition at that HEAD exceeds `MAX_DESCRIPTIVE_LEN`, with the arithmetic shown. If any figure differs from F-03/F-04/F-06, say so and say whether E-02's budget arithmetic needed adjusting.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a `python3 -c` session showing `A.compose_bounded_detail` returning a value of at most `A.MAX_DESCRIPTIVE_LEN` characters for: a segment list that already fits (and showing it is byte-identical to the joiner-plus-text concatenation plus trailer, and for a lane-shaped input to today's `"{0}: {1}. {2}".format(...)` string), the F-04 worst-reachable segment list, a single segment longer than the whole limit, and an empty segment list. Paste the refusal when the trailer alone exceeds the limit. Paste `git diff` for `attention_contract.py` showing the function is pure (no I/O, no import of `attention`, `term` or `artifact_core`) and that `is_safe_descriptive`, `MAX_DESCRIPTIVE_LEN`, `_CONTROL_CHAR_RE` and `escape_detail` are byte-for-byte unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new test cases' run. Demonstrate they are load-bearing by perturbing the budget reserve by one character, pasting the resulting FAILURE, then restoring and pasting the PASS; paste `git diff agent_workflows/attention_contract.py` after restoring to show the perturbation is gone and is not committed. Confirm by inspection and state explicitly that the sweep is deterministic (no randomness) and that no case reads production source via `inspect`, `ast`, regex over source, a symbol census or a line count (GUIDING_PRINCIPLES P16). Confirm the pass-through case is present.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a `python3 -c` session running `attention.stranded_lane_drift` over the execution tree and printing, per row, the length, `is_safe_descriptive`, rule and location; paste the SAME output captured before the change; and show they are byte-identical. Separately, paste a session that drives the producer against a constructed worst-reachable lane record whose naive `"; ".join` composition exceeds 300 (show that number) and show the real row is within the bound. State which route was taken for the F-08 escape-growth hazard (compose against a reserved limit, or escape per segment) and paste evidence that the bound holds on the POST-escape value that reaches the `Drift`. Paste `git diff` showing `lane_drift_severity`, the three rule ids, the `out.sort` key, the `Drift` construction shape, and `runner_shared.classify_lane_integration`'s sentences are all unchanged. Quote the `CHANGELOG.md` entry in full and state it contains no em or en dash.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the FAILING run of `python3 -m pytest tests/test_attention_lane_detail_bound.py -o addopts=""` against the pre-E-04 producer, produced by writing the E-05 cases BEFORE E-04 is applied (or by importing `git show HEAD:agent_workflows/attention.py` from a gitignored scratch location); do NOT `git stash` or revert the working tree, which a shared checkout forbids, then the PASSING run after restoring. Paste the diff of case (c) showing the `DO NOT assert` comment REPLACED by one naming this plan and the reason the prohibition lifted, not merely deleted. Paste the BARE full-suite `python3 -m pytest` with its `N passed` summary line. Paste `python3 -m agent_workflows attention --check --json` exit code and lane-row count before and after, showing both unchanged. Paste `aw sanitize --agent` output showing no finding on the changed files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is ONE cohesive change: a bounded composer, the coverage that proves its arithmetic, the single producer routed through it, and the per-site test upgraded from recording the residual to asserting it is gone. Splitting the composer from its one caller would land dead code; splitting the test upgrade from the fix would leave a plan claiming a bound nothing checks, which is the exact gap this Set exists to close.

Execution requires explicit human approval first (`Status: approved`). The `- Readiness:` field is `/plan-review`'s output and no author or executor writes or changes it. Open questions: OQ-01 to OQ-03 are resolved and OQ-04 is deferred to Order 02 with a carrier; none blocks execution.

Commit through `aw commit 9sbfea -- <paths>` with only this plan's declared paths; verify `git diff --cached --name-only` before committing; never `git add -A`, never `-a`, never `--no-verify`, and never a push. Paste the ACTUAL runner output for every test, check and lint claimed; a green suite claimed without its pasted output does not satisfy the execution contract.

SCOPE FENCE (a declaration the finalize scope gate reconciles, not a stop directive): this plan edits only its `Scope-Paths`. It does not change `is_safe_descriptive`, `MAX_DESCRIPTIVE_LEN`, `_CONTROL_CHAR_RE` or `escape_detail`, `artifact_core.Drift`, any other `Drift` producer, `runner_shared.classify_lane_integration`'s sentences, or `qpw45x`'s board-escaping work. An out-of-scope edit that nonetheless proves necessary must be justified with a `--scope-reason` at finalize; a declared path left unmodified needs a `--scope-ack`.

Lifecycle transition: `aw ipd lint --phase pre-transition` must conform and every `V-*` item must carry pasted, concrete evidence before the plan reaches `executed/`. The transition is tooled and its owner is conditional: under `aw oc run` / `aw agy run` the RUNNER finalizes after its merge-and-revalidate gate and the executor must NOT run `aw ipd finalize`; in a hand execution with no runner, the executor runs `aw ipd finalize 9sbfea`. Never `git mv` the plan. Backlog `0livgf` stays open until Order 02 (`62pkkg`, `- Item-Dependencies: executed:9sbfea`) also executes.
