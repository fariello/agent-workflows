# IPD: Consume the verifier evidence the runner already asks for and surface it in the run report

- Date: 2026-09-08
- Kind: child
- Concern: The verifier outcome schema requests seven fields and the runner reads exactly ONE. `build_verifier_prompt` asks for `schema_version, id6, verdict, summary, evidence, tests_run, corrections_made`, the verifiers fill them in substantively, and the only consumption anywhere is `v_data.get("verdict")`. So `evidence`, `tests_run`, `corrections_made` and `summary` are written to disk, committed, and ignored by every gate, aggregate and report. `verified` is therefore a single opaque bit: nothing distinguishes a verifier that reproduced a phase gate and ran a mutation test from one that pasted nothing and asserted success, which makes a fleet-level "all VERIFIED" uninterpretable. The framework enforces "claims require pasted evidence" on human-facing IPD validation items but not on the machine-readable record that gates merging.
- Scope: Make the runner CONSUME what it asks for. Require real test evidence before `verify_disp` may be `verified`, using a bar calibrated against the recorded corpus rather than an invented one; surface `tests_run` and `corrections_made` in `execution-report.md` and in `aw runs` so a maintainer can audit a verification without opening JSON. Explicitly NOT included: the verdict-vocabulary fail-open (backlog `wyw936`, which must land first or together), and the session-log cross-check for fabricated evidence (scoped separately by the item's own instruction).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/run_viewer.py, tests/test_verifier_evidence.py
- Item-Dependencies: none
- Status: to-review
- Set: runverdict
- Order: 5
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: bxx9af
- From-Backlog: rbftpl
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `rbftpl`, inheriting its `Blocks-Release: next` gate. NOTHING IN THIS ITEM IS OBSOLETE, and every code claim re-located BY SYMBOL because the line numbers moved enormously: the item cites `oc_runipd.py:2171-2172` for the `v_data` read and it is now `:6421-6422` (a ~4250-line drift), `agy_runipd.py:2248-2249` is now `:3685-3686`, and the prompt schema the item cites at `oc_runipd.py:1610-1620` is now `:4915-4919`. Confirmed at HEAD `8b4e1570` that `v_data` is still read in exactly two places, one per host, and still only for `verdict`. THE ITEM'S ORDERING CONSTRAINT IS STILL BINDING AND ITS SIBLING IS STILL UNOWNED: `wyw936` (the verdict gate fails open) is `open` and has no plan, and I verified the fail-open directly - the gate downgrades only on `BLOCKED` or `NOT CONFORMING` (`oc_runipd.py:6423-6428`) and the schema's own `CORRECTION_REQUIRED` appears NOWHERE outside the prompt string (one occurrence per host, `oc_runipd.py:4915` / `agy_runipd.py:2575`), so a `CORRECTION_REQUIRED` verdict is recorded `verified` today. OQ-01 carries that dependency explicitly. ONE MEASUREMENT THAT MATERIALLY RESHAPES THE PLAN AND IS THE REASON THIS IS NOT A TRANSCRIPTION: the item's own PROPOSED BAR would fail closed on most real verifications. It asks to "require `tests_run` to be non-empty with at least one entry carrying a command AND an exit code", and demands as test (c) that "the 28 EXISTING recorded outcomes all still satisfy the new requirement". I evaluated exactly that predicate over the 34 verification outcomes now on this box: ALL 34 have non-empty `tests_run` and non-empty `evidence` (so the item's healthy-producer finding still holds, and has grown from 28 to 34), but only 10 of 34 satisfy the command-AND-exit-code shape. The cause is that `tests_run` is NOT uniformly typed: of 258 total entries, 132 are dicts and 126 are BARE STRINGS, and the bare strings carry the same facts in prose (measured example: `python -m unittest tests.test_release_gate_close -v -> Ran 25 tests in 0.102s OK (exit 0): ...`). So the item's test (c) and its fix sketch CONTRADICT each other against the real corpus, and implementing the sketch literally would reject 24 of 34 genuine verifications, including ones that pasted exit codes in prose. E-02 therefore calibrates the bar to the corpus and E-03 makes the corpus check a build-time gate rather than an afterthought.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Turn `verified` from an opaque bit into a claim backed by the evidence the verifier already produced. The point is auditability with fail-closed behavior: a verification that shows no test activity must not be recorded as verified, and a maintainer must be able to see what a verification actually did without reading JSON.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the bar against the real corpus BEFORE enforcing anything

- [ ] E-01 Build a one-shot corpus survey over every recorded verification outcome (`.aw/records/runs/*/outcomes/*-verification.json`) reporting, per candidate predicate, how many outcomes PASS and how many FAIL, and dump a sample of each failing shape. THIS MUST COME FIRST because the item's own proposed predicate is measurably wrong against the corpus: measured at HEAD `8b4e1570` over 34 outcomes, all 34 have non-empty `tests_run` and `evidence`, but only 10 satisfy "at least one entry with a command AND an exit code", because 126 of 258 entries are BARE STRINGS rather than dicts. Do NOT skip to implementation on the assumption that the item's numbers hold; they described 28 outcomes and the shape distribution was never measured. The survey is throwaway tooling, not a deliverable, but its OUTPUT is the input to E-02 and must be pasted into V-01.
  - Depends on: none
  - Expected outcome: a pasted table of candidate-predicate pass/fail counts over the whole recorded corpus, plus one concrete sample of every distinct `tests_run` entry shape found.
  - Execution state: pending

- [ ] E-02 Choose and implement the evidence predicate, in `runner_shared.py` so both hosts share ONE definition, calibrated so that every outcome the corpus shows to be a GENUINE verification passes while an empty or contentless one fails. The predicate must accept BOTH shapes the corpus actually contains: a dict entry naming a command (`command`/`cmd`) and, where present, an exit code (`exit`/`exit_code`/`rc`); AND a bare string entry that names a command. It must REFUSE: an absent `tests_run`, an empty list, a list of empty or whitespace-only strings, and a list whose entries carry no command-like content. STATE THE RESIDUAL WEAKNESS HONESTLY IN THE CODE COMMENT: accepting prose means the predicate proves ACTIVITY, not correctness, and a determined verifier could write a plausible string having run nothing. That is the gap the item's own strongest option (cross-checking claimed commands against the session log) would close, and it is deliberately out of scope here; do not oversell the predicate as fabrication-proof.
  - Depends on: E-01
  - Expected outcome: one shared predicate, in one module, that passes every genuine outcome the E-01 survey identified and fails every contentless variant, with the prose-acceptance tradeoff recorded in a comment.
  - Execution state: pending

- [ ] E-03 Pin the corpus as a REGRESSION FENCE, which is the item's test (c) and the thing that stops the bar being set above what good verifiers already produce. Add a test that runs the E-02 predicate over a COMMITTED FIXTURE SET of outcome shapes derived from the real corpus (representative dicts with and without exit codes, and bare strings), NOT over `.aw/records/runs/` itself: that tree is gitignored box-local state with zero tracked files, so a test reading it would pass on this machine and fail in CI and in every lane worktree, which is the exact hazard `tests/test_run_viewer.py:1-30` documents for 23 existing tests. Copy the shapes into the fixture and cite their provenance in a comment so a future reader can tell they are real rather than invented.
  - Depends on: E-02
  - Expected outcome: a committed fixture corpus covering every shape E-01 found, asserted to pass the predicate, runnable in a bare checkout with no dependence on live run records.
  - Execution state: pending

### Task group 2: make the gate consume it, fail-closed

- [ ] E-04 Wire the predicate into BOTH hosts' verification gates so a `VERIFIED` verdict with no test evidence is NOT recorded as verified. The single consumption site per host is `v_data = json.loads(...)` / `verify_verdict = str(v_data.get("verdict", "")).upper()` (`oc_runipd.py:6421-6422`, `agy_runipd.py:3685-3686`), inside an `if v_outcome_file.is_file():` block whose `else` and `except` branches both fall back to `verify_disp = "verified" if v_rc == 0 else "unverified"`. FAIL CLOSED, and mind those two fallbacks specifically: an unparseable outcome file currently yields `verified` on a zero exit code (`oc_runipd.py:6431-6432`), which is a second fail-open on the same surface and must not be left behind by a fix that only guards the parsed path. Introduce a distinct disposition for "verdict says verified but no evidence" rather than reusing `blocked`, so the run record can tell a rejecting verifier apart from an unevidenced one; if that requires a new status token, check it against whatever consumes `verification_status` before adding it.
  - Depends on: E-02, E-03
  - Expected outcome: in both hosts, a `VERIFIED` verdict with empty or contentless `tests_run` does not produce `verify_disp == "verified"`, and an unparseable outcome file no longer yields `verified`; both demonstrated per host.
  - Execution state: pending

- [ ] E-05 Verify the change does not silently alter the INTEGRATION decision beyond the intended fail-closed effect. `verify_disp` feeds `attempt["verification"]`, `item["verification_status"]` and the disposition, and there is a separate suite-based trust path immediately below the gate for the validation-off case (`oc_runipd.py`, the `suite_result` / `integration_gate_relevant` block after the disposition assignment) that exists precisely because `verify_disp` stays `None` when validation is off. Read that path and state explicitly whether a newly-unverified item now reaches integration differently. THIS IS A READ-AND-REPORT OBLIGATION with a code consequence only if a gap is found: the item's whole point is that tightening one gate while another fails open adds a second fail-open, so the interaction must be checked rather than assumed.
  - Depends on: E-04
  - Expected outcome: a written account of how the new refusal flows into the integration gate on BOTH the validation-on and validation-off paths, with any gap either fixed or recorded as a named follow-up.
  - Execution state: pending

### Task group 3: surface it where a maintainer will actually see it

- [ ] E-06 Render the evidence in `execution-report.md`, which is the report an operator actually reads. `write_report` (`oc_runipd.py:3175-3237`) builds a fixed metadata block and a per-item table with a `Verify` column, then appends a `## Dependency blocks (why)` section and a `## Review` section. Follow that established pattern exactly: add a NEW SECTION rather than new columns, because the file's own comments record twice that sections were chosen specifically so "the table's column contract is unchanged" (`:3206-3208`, `:3229-3231`). Render, per verified item, the commands from `tests_run` and any `corrections_made`. Handle both entry shapes from E-02, and truncate defensively: the corpus contains prose entries hundreds of characters long, and a report that becomes unreadable will not be read.
  - Depends on: E-02
  - Expected outcome: a new `execution-report.md` section listing each verified item's test commands and corrections, with the existing metadata block and table byte-identical; demonstrated on a fixture run.
  - Execution state: pending

- [ ] E-07 Surface the same facts in `aw runs`, in the human view AND in the `--json`/`--agent` payloads, since an automated consumer reads the machine path. Route it through ONE shared accessor rather than re-parsing the outcome JSON at each render site. IMPORTANT PRECEDENT AND POSSIBLE COLLISION: reviewed plan `r2i1b1` (Set `orchprobe`, Order 01) is already adding a per-item `refusal` record to run state and rendering it in BOTH these surfaces through one shared predicate, and its `Scope-Paths` include `agent_workflows/run_viewer.py`, `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py` and `agent_workflows/runner_shared.py` - the same four modules this plan touches. Before writing, check whether `r2i1b1` has landed; if it has, EXTEND its shared accessor rather than adding a parallel one, and if the two designs conflict, STOP and report rather than reverting a sibling's work.
  - Depends on: E-06
  - Expected outcome: `aw runs` shows a verified item's test evidence in all three renderers through one accessor, with a stated finding on whether `r2i1b1` had landed and how this composed with it.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The verifier prompt and the verifier CONSUMER are far apart and drifted: the schema is requested at `oc_runipd.py:4915-4919` and `agy_runipd.py:2575-2579`, and consumed at `oc_runipd.py:6421-6422` and `agy_runipd.py:3685-3686`. Nothing ties the request to the read, which is how five fields came to be ignored.
- The gate's shape is `if "BLOCKED" in verify_verdict or "NOT CONFORMING" in verify_verdict` -> `blocked`/`partial`, `else` -> `verified` (`oc_runipd.py:6423-6428`). It is a substring test against an uppercased string, and its `else` is unconditional, which is exactly `wyw936`'s fail-open.
- `CORRECTION_REQUIRED` is REQUESTED by the schema and handled NOWHERE: one occurrence per host, both inside the prompt string. So the schema's own middle verdict is silently treated as success today.
- There are TWO further fallbacks that both default to `verified`: the `except Exception` around the JSON parse, and the `else` when no outcome file exists (`oc_runipd.py:6430-6434`). Any fail-closed change must address them or it leaves the hole open one branch over.
- `tests_run` IS NOT UNIFORMLY TYPED in practice: 132 dict entries and 126 bare-string entries across 34 outcomes. Any predicate must handle both or it will reject real work.
- `write_report` deliberately appends SECTIONS rather than adding table columns, with the reason stated inline twice. Follow it.
- `.aw/records/runs/` is gitignored with zero tracked files, and `tests/test_run_viewer.py:1-30` documents that 23 tests reading it fail in a fresh checkout. New tests must use committed fixtures.
- Reviewed plan `r2i1b1` is concurrently adding per-item refusal reporting to the same four modules through one shared predicate. Compose with it; do not fork a second reporting path.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The runner still reads ONLY `verdict`. Two consumption sites, one per host, both `v_data.get("verdict", "")`. | `oc_runipd.py:6421-6422`, `agy_runipd.py:3685-3686`, measured at `8b4e1570` |
| F-2 | ALL THE ITEM'S LINE NUMBERS HAD DRIFTED and were re-located by symbol: `2171-2172` -> `6421-6422` (~4250 lines), `2248-2249` -> `3685-3686`, prompt `1610-1620` -> `4915-4919`. | read at `8b4e1570` |
| F-3 | The schema requests seven fields; four (`summary`, `evidence`, `tests_run`, `corrections_made`) are consumed by no gate, aggregate or report. | `oc_runipd.py:4911-4920` vs the only `v_data` read |
| F-4 | THE PRODUCING SIDE IS HEALTHY, and has grown: 34 of 34 recorded outcomes populate BOTH `tests_run` and `evidence`; 0 leave either empty. The item measured 28 of 28. | measured over `.aw/records/runs/*/outcomes/*-verification.json` at `8b4e1570` |
| F-5 | THE ITEM'S OWN PROPOSED BAR WOULD FAIL CLOSED ON 24 OF 34 GENUINE VERIFICATIONS. Only 10 of 34 have at least one `tests_run` entry carrying both a command and an exit code, so its fix sketch contradicts its own test (c). | measured at `8b4e1570` |
| F-6 | The cause is a non-uniform schema: of 258 `tests_run` entries, 132 are dicts and 126 are BARE STRINGS. The strings carry the same facts in prose, e.g. `python -m unittest tests.test_release_gate_close -v -> Ran 25 tests in 0.102s OK (exit 0): ...`. | measured at `8b4e1570` |
| F-7 | Even among dict entries the keys vary: 126 name a command but only 110 carry an exit code. | measured at `8b4e1570` |
| F-8 | `wyw936`'s fail-open is LIVE and UNOWNED (`open`, no plan), so the item's ordering constraint still binds: the gate downgrades only on `BLOCKED`/`NOT CONFORMING`. | backlog `wyw936` `- Status: open`; `oc_runipd.py:6423-6428` |
| F-9 | `CORRECTION_REQUIRED` is requested by the schema and handled nowhere in either host. | one occurrence per host, both in the prompt: `oc_runipd.py:4915`, `agy_runipd.py:2575` |
| F-10 | Two additional fallbacks default to `verified`: the JSON-parse `except` and the no-outcome-file `else`. | `oc_runipd.py:6430-6434` |
| F-11 | `write_report`'s own comments state twice that new facts go in SECTIONS to keep the table's column contract unchanged, which settles E-06's shape. | `oc_runipd.py:3206-3208`, `:3229-3231` |
| F-12 | New tests must not read `.aw/records/runs/`: it is gitignored with zero tracked files and 23 existing tests that read it fail in a fresh checkout. | `tests/test_run_viewer.py:1-30` |
| F-13 | A CONCURRENT REVIEWED PLAN touches the same four modules for the same two render surfaces through one shared predicate, so E-07 must compose rather than fork. | `r2i1b1` `- Status: reviewed`, its `Scope-Paths` |

## Proposed changes (ordered, validatable)

1. Survey the recorded corpus and report per-predicate pass/fail counts and every entry shape (E-01).
2. Implement one shared evidence predicate calibrated to that corpus, accepting both shapes (E-02).
3. Pin a committed fixture corpus as the regression fence (E-03).
4. Wire it into both hosts' gates, fail-closed, including the two `verified` fallbacks (E-04).
5. Read and report the interaction with the integration gate on both validation paths (E-05).
6. Add an `execution-report.md` section rendering commands and corrections (E-06).
7. Surface the same facts in `aw runs` in all three renderers, composing with `r2i1b1` (E-07).

## Deferred / out of scope (with reason)

- THE VERDICT-VOCABULARY FAIL-OPEN. That is backlog `wyw936`, still `open` and unowned, and the item is explicit that this work "should land AFTER or WITH" it because "tightening evidence requirements while the verdict gate still fails open would add a second fail-open path". This plan implements the EVIDENCE half only and OQ-01 carries the sequencing to the reviewer rather than silently absorbing a sibling item's scope.
- THE SESSION-LOG CROSS-CHECK for fabricated evidence (the item's strongest option, its test (e)). The item itself says to scope it separately "if it proves expensive", and it is: it requires parsing the session log's tool calls and matching them against claimed commands, which is a different subsystem and a different failure model. Recorded in E-02's comment as the acknowledged residual weakness.
- MODEL IDENTITY AND COST ATTRIBUTION on the verification record. That is the sibling item `vlf75p`, separately open.
- THE VERIFIER TURN THAT NEVER RAN AT ALL (40% of turns dying on a stale plan path after self-finalize). That is the sibling item `t74o5q`, separately open, and it is a PRODUCTION problem rather than a consumption one.
- NORMALIZING `tests_run` TO A SINGLE SHAPE, or changing the requested schema. Tempting given F-6, but it would invalidate the existing corpus as a regression fence and put this plan's fix behind a prompt change whose effect only appears in future runs. Accepting both shapes is the honest choice while the corpus is the evidence.

## Scope check

- Over-scope: `agent_workflows/run_viewer.py` is in `Scope-Paths` for E-07, which is a reporting improvement rather than the gate fix. It is included because the item names it explicitly ("Surface `tests_run`/`corrections_made` in the run's `execution-report.md` and in `aw runs`"), and because a fail-closed gate with no visible reason produces exactly the unactionable refusal this repository has repeatedly found trains bypasses. A reviewer may cut E-07 without affecting E-01 through E-06.
- Under-scope: the verdict fail-open, the session-log cross-check, model attribution, and the never-ran verifier turn are all left to their own items. No change to the requested schema or to the verifier prompt.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_verifier_evidence.py` plus whichever runner test modules the change touches.
- The E-01 corpus survey re-run after the change, showing the final predicate's pass rate over every recorded outcome (the item's test (c)).
- Per-host demonstrations for E-04: a `VERIFIED` verdict with empty `tests_run`, and a `tests_run` entry with no command, each shown NOT reaching `verified`, on BOTH `oc` and `agy`.
- Exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`).

## Spec / documentation sync

Spec `25kzda` (`aw run deterministic run and verify`, `- Status: approved`) governs the run-and-verify pipeline and states that agent prose and exit status are never completion authority, which this plan strengthens rather than contradicts. It may, however, DOCUMENT the verification disposition vocabulary: if E-04 introduces a new disposition token, that IS a contract change and the spec path MUST be added to `Scope-Paths` and the amendment justified here BEFORE editing, per the plan-may-amend-a-spec rule. The executor must check the spec's verification section for a disposition enum before choosing the token, and report what it found either way. The verifier prompt text is not changed, so the requested schema needs no doc update.

## Open questions

### OQ-01: Must `wyw936` land before this plan executes, or may they land independently?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: BLOCKING, because the item states the constraint in its own words and the risk is concrete rather than stylistic: "tightening evidence requirements while the verdict gate still fails open would add a second fail-open path (an evidence check whose failure mode is also 'record verified'), so both must fail closed together to be worth anything." Verified that the hazard is live: `wyw936` is `open` with no plan, and `CORRECTION_REQUIRED` is handled nowhere. THREE OPTIONS. (a) Graduate and land `wyw936` first, then execute this: cleanest, but `wyw936` is not mine to graduate and is not yet designed. (b) Absorb the verdict fix into THIS plan: makes one coherent change, but silently takes over another open item's scope, which the graduation contract forbids. (c) Land this alone, accepting that an unevidenced `CORRECTION_REQUIRED` still records `verified` until `wyw936` lands: acceptable ONLY if the maintainer knows the residual hole remains. RECOMMENDED: (a). The decision is the maintainer's because it is a sequencing and ownership call, not a technical one.

### OQ-02: What should the disposition be for "verdict says VERIFIED but there is no evidence"?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE FROM THE CODE and recorded so the answer is deliberate. Reusing `blocked` would conflate a verifier that REJECTED the work with one that produced no evidence, and those need different operator responses (re-do the work versus re-run the verification). A distinct token is therefore preferred, but it must be checked against every consumer of `verification_status` and against spec `25kzda`'s disposition vocabulary before being added; if the spec pins an enum, the token needs a spec amendment (see Spec sync) and the cheaper answer may be to reuse `unverified`, which already means "we do not know that this was verified" and is arguably exactly right.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the survey's full output: the number of outcomes scanned, the pass/fail counts for at least the item's proposed predicate and the final chosen one, and one concrete sample of EVERY distinct `tests_run` entry shape found. The numbers must be re-measured at execution time, not copied from this plan, since the corpus grows with every run.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the predicate's source including the comment stating the prose-acceptance tradeoff, plus its verdict for each of these inputs shown individually: a dict entry with command and exit code; a dict entry with a command and no exit code; a bare string naming a command; an empty list; a list of whitespace-only strings; a missing `tests_run` key. Paste a grep proving there is ONE definition shared by both hosts.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the committed fixture file, its provenance comment, and the passing test result. Prove independence from live state by running the test from a clean temp checkout (or with `.aw/records/runs/` absent) and pasting that run.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: for EACH host separately (`oc` and `agy`), paste a demonstration that a `VERIFIED` verdict with empty `tests_run` does NOT yield `verify_disp == "verified"`, and that an UNPARSEABLE outcome file no longer yields `verified` on a zero exit code. Four demonstrations minimum. Paste the resulting `verification_status` value in each case.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the written account naming the integration-gate code path by symbol and line, and state explicitly what happens to a newly-unevidenced item on the validation-ON path and on the validation-OFF path. Where a gap was found, paste the fix or the named follow-up. A bare assertion that "integration is unaffected" does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the new `execution-report.md` section from a fixture run, AND a diff proving the metadata block and the item table are byte-identical to before. Paste the truncation behavior on one of the corpus's long prose entries.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the `aw runs` human output, the `--json` payload and the `--agent` record for a run with a verified item, each showing the test evidence. State whether `r2i1b1` had landed and paste the shared accessor showing this composed with it rather than duplicating it. Paste the bare `python3 -m pytest` summary line and compare it to the stated baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened. OQ-01 is BLOCKING and is a sequencing decision about a sibling item (`wyw936`) that a reviewer must settle before execution. A reviewer should also note F-5: the backlog item's own proposed bar would reject 24 of 34 real verifications, so E-01 exists to prevent this plan implementing the item literally and breaking the fleet.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE CONTENTION: `oc_runipd.py` and `agy_runipd.py` are the two most heavily edited files in the repository and reviewed plan `r2i1b1` declares the same four modules, so re-locate every citation BY SYMBOL at execution time and never by the line numbers written above. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
